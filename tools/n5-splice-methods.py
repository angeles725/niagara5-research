#!/usr/bin/env python3
"""n5-splice-methods.py -- per-method source splice (meta-decompilation) of a
decompiled N5 class (T21/F9).

A class whose primary decompile (vineflower2, or F8's vineflower2p when it
exists) COMPILES but has methods whose recompiled bytecode differs from the
shipped class is re-decompiled with CFR and Procyon. Each donor is recompiled
and compared with the shipped class method by method, with the grader's own
normalizer, width allowlist and sound canonical comparison (tools/n5-fidelity.py,
tools/n5_canon.py). A method m is spliced only from a donor whose own m matches
the shipped m (exact preferred, then allowlist/canonical; CFR before Procyon on
a tie), and only m is replaced: the declaration from the end of the primary's
modifiers (annotations and modifiers stay the primary's) to the end of the body,
or the whole declaration when the primary's flags/throws differ. Nothing else
of the primary changes except added single-type or static imports the donor
span needs.

Methods are located by name + JVM descriptor computed by javac itself: the
helper tools/n5-splice-methods/MethodSpans.java attributes each source against
the grading classpath (erasure, varargs, enum constructor prefix are javac's).
A splice is refused (never guessed) when:
  clinit / synthetic-method   the mismatched method is <clinit> or a
                              synthetic (lambda$, access$...) method
  structural-mismatch         fields/class attributes differ, or a non-synthetic
                              method is missing/extra (no body splice fixes it)
  no-donor                    some mismatched method has no faithful donor
  method-not-located          the method has no source declaration to replace
  local-class                 the donor span declares a local/anonymous class
  synthetic-member / missing-member
                              the donor span references a member of the class
                              nest the primary source does not declare
  import-conflict             a donor type's simple name is bound to another
                              type in the primary
  attribution-error           javac could not attribute a source
  splice-no-compile / splice-not-clean
                              the spliced class does not recompile, or does not
                              grade clean as a whole (every method, fields,
                              attributes) against the shipped class
Only classes whose spliced source grades clean are written.

Output: organized/<mod>/<out-tree>/<package>/<Class>.java plus
organized/<mod>/<out-tree>/SPLICES.json (per class: primary tree, original and
spliced sha256, per method donor engine / donor source sha256 / reason, added
imports, self grade; per refused class the reason). Grade it with
  n5-fidelity.py --regrade-nonclean --tree vineflower2 --patch-tree vineflower2s
(-> fidelity.vineflower2.spliced.json).

Usage:
  python3 tools/n5-splice-methods.py --targets remaining.json --tool-server --jobs 2 --class-jobs 4
    (remaining.json: [[module, fqcn], ...])
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

TOOLS_DIR = Path(__file__).resolve().parent
HELPER_SRC = TOOLS_DIR / "n5-splice-methods" / "MethodSpans.java"
MANIFEST_NAME = "SPLICES.json"
MANIFEST_SCHEMA = 1


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity_for_splice", TOOLS_DIR / "n5-fidelity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


FID = _load_fidelity()


class Refusal(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}")
        self.reason = reason
        self.detail = detail


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_synthetic_name(name: str) -> bool:
    return "$" in name


# ---------------------------------------------------------------------------
# attributed spans (MethodSpans.java)
# ---------------------------------------------------------------------------

def compile_helper(cache_dir: Path, javac_bin: str) -> Path:
    stamp = hashlib.sha256(HELPER_SRC.read_bytes()).hexdigest()[:16]
    out = Path(cache_dir) / f"spans-{stamp}"
    if not (out / "MethodSpans.class").is_file():
        out.mkdir(parents=True, exist_ok=True)
        subprocess.run([javac_bin, "-d", str(out), str(HELPER_SRC)], check=True, capture_output=True, text=True)
    return out


def scan_spans(files: list, helper_dir: Path, java_bin: str, classpath: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".cp", delete=False) as cpf:
        cpf.write(classpath)
    try:
        proc = subprocess.run([java_bin, "-Xmx2g", "-cp", str(helper_dir), "MethodSpans", cpf.name,
                               *map(str, files)], capture_output=True, text=True, timeout=900)
    finally:
        Path(cpf.name).unlink()
    if proc.returncode != 0:
        raise Refusal("attribution-error", proc.stderr.strip()[:300])
    out = {}
    for line in proc.stdout.splitlines():
        if line.strip():
            d = json.loads(line)
            out[d["file"]] = d
    return out


def _find_method(scan: dict, name: str, desc: str, class_short: str) -> Optional[dict]:
    src_name = "<init>" if name == class_short else name
    hits = [m for m in scan["methods"] if m["name"] == src_name and m["desc"] == desc]
    return hits[0] if len(hits) == 1 else None


def plan_type_import(primary: dict, ref: dict) -> Optional[str]:
    """The single-type import the primary needs for a donor type reference by
    simple name, None when it already resolves there; Refusal when the simple
    name is bound to a different type in the primary."""
    simple, qname, binary = ref["simple"], ref["qname"], ref["binary"]
    if ref.get("nest"):
        return None
    pkg = binary.rsplit("/", 1)[0].replace("/", ".") if "/" in binary else ""
    for imp in primary["imports"]:
        if imp["static"]:
            continue
        name = imp["name"]
        if name == qname:
            return None
        if name.rsplit(".", 1)[-1] == simple and not name.endswith(".*"):
            raise Refusal("import-conflict", f"{simple}: primary imports {name}, donor uses {qname}")
    for member in primary.get("members", []):
        if member.startswith("type|") and member.rsplit("$", 1)[-1].rsplit("/", 1)[-1] == simple \
                and member[5:] != binary:
            raise Refusal("import-conflict", f"{simple}: primary declares {member[5:]}, donor uses {qname}")
    if qname in (f"java.lang.{simple}", f"{primary['package']}.{simple}" if primary["package"] else simple):
        return None
    for imp in primary["imports"]:
        if not imp["static"] and imp["name"].endswith(".*") and qname == imp["name"][:-1] + simple:
            return None
    if pkg == "" or "." not in qname:
        return None
    return qname


def render_splice(text: str, replacements: list, imports: list, primary: dict) -> str:
    """Apply (start, end, new_text) replacements (non-overlapping) and insert
    `import X;` lines (X may start with "static ") after the last import, else
    after the package declaration."""
    out = text
    for start, end, new in sorted(replacements, reverse=True):
        out = out[:start] + new + out[end:]
    if imports:
        # every replacement lies inside the class body, after the import block
        block = "".join(f"\nimport {i};" for i in imports)
        if primary["imports"]:
            at = max(i["end"] for i in primary["imports"])
        elif primary.get("package_end", -1) >= 0:
            at = primary["package_end"]
        else:
            at, block = 0, block.lstrip("\n") + "\n"
        out = out[:at] + block + out[at:]
    return out


def plan_splice(primary_text: str, primary: dict, donors: dict, assignment: dict, full_decl: dict,
                class_short: str) -> tuple[str, list]:
    """Spliced source for `assignment` {method key: donor engine}; donors =
    {engine: (text, scan)}. Returns (text, added imports); raises Refusal."""
    if primary["errors"]:
        raise Refusal("attribution-error", f"primary: {primary['errors'][0]}")
    primary_members = set(primary["members"])
    replacements, imports = [], []
    for key, eng in sorted(assignment.items()):
        name, desc = key
        dtext, dscan = donors[eng]
        if dscan["errors"]:
            raise Refusal("attribution-error", f"{eng}: {dscan['errors'][0]}")
        pm = _find_method(primary, name, desc, class_short)
        dm = _find_method(dscan, name, desc, class_short)
        if pm is None or dm is None:
            raise Refusal("method-not-located", f"{name}{desc} in {'primary' if pm is None else eng}")
        mode = "start" if full_decl.get(key) else "after_mods"
        d0, d1 = dm[mode], dm["end"]
        for ref in dscan["refs"]:
            if not d0 <= ref["pos"] < d1:
                continue
            kind = ref["kind"]
            if kind == "local_class":
                raise Refusal("local-class", f"{name}{desc} from {eng}")
            if kind == "member" and not ref["local"] and ref["key"] not in primary_members:
                member = ref["key"].split("|")[1]
                raise Refusal("synthetic-member" if _is_synthetic_name(member) else "missing-member",
                              f"{name}{desc} from {eng} uses {ref['key']}")
            if kind == "type":
                if ref["nest"] and f"type|{ref['binary']}" not in primary_members and "$" in ref["binary"]:
                    raise Refusal("missing-member", f"{name}{desc} from {eng} uses type {ref['binary']}")
                need = plan_type_import(primary, ref)
                if need and need not in imports:
                    imports.append(need)
            if kind == "static":
                have = {i["name"] for i in primary["imports"] if i["static"]}
                if f"{ref['owner']}.{ref['name']}" in have or f"{ref['owner']}.*" in have:
                    continue
                donor_static = {i["name"] for i in dscan["imports"] if i["static"]}
                for cand in (f"{ref['owner']}.{ref['name']}", f"{ref['owner']}.*"):
                    if cand in donor_static and f"static {cand}" not in imports:
                        imports.append(f"static {cand}")
                        break
        replacements.append((pm[mode], pm["end"], dtext[d0:d1]))
    return render_splice(primary_text, replacements, imports, primary), imports
