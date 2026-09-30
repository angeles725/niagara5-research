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

C3d: --donor-trees adds already-decompiled trees (vineflower-cons, the v1 tree, flag-variant trees) as
donors named `tree:<name>`; --primary-trees starts from the m/p patch stage; --keep-existing extends an
earlier splice stage instead of replacing it (a re-run without it rebuilds the out tree).

Usage:
  python3 tools/n5-splice-methods.py --targets remaining.json --tool-server --jobs 2 --class-jobs 4
    (remaining.json: [[module, fqcn], ...])
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.util
import itertools
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

TOOLS_DIR = Path(__file__).resolve().parent
HELPER_SRC = TOOLS_DIR / "n5-splice-methods" / "MethodSpans.java"
MANIFEST_NAME = "SPLICES.json"
MANIFEST_SCHEMA = 1
DONOR_ENGINES = ("cfr", "procyon")
MAX_COMBOS = 8
_VERDICT_RANK = {"exact": 0, "allowlist": 1, "canonical": 2}


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity_for_splice", TOOLS_DIR / "n5-fidelity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


FID = _load_fidelity()


def _load_clinit():
    spec = importlib.util.spec_from_file_location("n5_clinit_order_for_splice", TOOLS_DIR / "n5_clinit_order.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CLINIT = _load_clinit()


def _load_hypotheses():
    spec = importlib.util.spec_from_file_location("n5_source_hypotheses_for_splice",
                                                  TOOLS_DIR / "n5_source_hypotheses.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


HYP = _load_hypotheses()


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
# per-method verdicts (the grader's own comparison, one method at a time)
# ---------------------------------------------------------------------------

def per_method_verdicts(shipped: dict, recompiled: dict) -> tuple[dict, dict]:
    """({method key: {"verdict", "rules"}} for every shipped method, structure).
    verdict: exact | allowlist | canonical (n5_canon, rules listed) | mismatch |
    missing (not in the recompiled class)."""
    diff = FID.diff_normalized_classes(shipped, recompiled)
    out = {}
    for key in shipped["methods"]:
        if key not in recompiled["methods"]:
            out[key] = {"verdict": "missing", "rules": []}
        elif key not in diff["mismatched_methods"]:
            out[key] = {"verdict": "exact", "rules": []}
        else:
            bodies = diff["method_bodies"][key]
            hit = next((e for e in FID.ALLOWLIST if e.predicate(bodies["a"], bodies["b"])), None)
            if hit is not None:
                out[key] = {"verdict": "allowlist", "rules": [hit.name]}
                continue
            rules = FID._canonical_resolution(bodies)
            if rules is not None:
                out[key] = {"verdict": "canonical", "rules": sorted(rules)}
            else:
                out[key] = {"verdict": "mismatch", "rules": [], "body_only": bodies["body_only"]}
    structure = {"fields_match": diff["fields_match"], "attrs_match": diff["attrs_match"],
                 "missing": diff["missing_methods"], "extra": diff["extra_methods"]}
    return out, structure


TREE_DONOR_PREFIX = "tree:"
HYP_DONOR_PREFIX = "hyp:"


def numbering_only(shipped_code: list, ours_code: list) -> bool:
    """True when two normalized codes are equal once anonymous-class numbers (`Foo$1`) are ignored:
    javac numbers anonymous classes in source order, so a reordered source differs only by them."""
    strip = lambda code: [re.sub(r"\$\d+\b", "$N", line) for line in code]  # noqa: E731
    return len(shipped_code) == len(ours_code) and strip(shipped_code) == strip(ours_code) \
        and shipped_code != ours_code


def donor_candidates(key, donor_verdicts: dict, engines: tuple = DONOR_ENGINES) -> list:
    """[(engine, verdict)] of the donors whose `key` matches the shipped method,
    best evidence first (exact, allowlist, canonical), `engines` order on a tie."""
    found = []
    for i, eng in enumerate(engines):
        v = (donor_verdicts.get(eng) or {}).get(key)
        if v and v["verdict"] in _VERDICT_RANK:
            found.append((_VERDICT_RANK[v["verdict"]], i, eng, v))
    return [(eng, v) for _r, _i, eng, v in sorted(found)]


def _reason(v: dict) -> str:
    return v["verdict"] if not v["rules"] else f"{v['verdict']}:{','.join(v['rules'])}"


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


# ---------------------------------------------------------------------------
# compile + grade helpers (same javac flags as n5-fidelity.recompile_and_grade)
# ---------------------------------------------------------------------------

def compile_parse(java_file: Path, class_short: str, classpath: str, javac_bin: str, javap_bin: str,
                  tool_server: bool, raw: bool = False):
    """The parsed javap of the recompiled class (None when it does not compile);
    (parsed, javap text) with raw=True."""
    with tempfile.TemporaryDirectory(prefix=f"n5sp-{class_short}-") as td:
        args = ["--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn", "-d", td]
        if classpath:
            args += ["-cp", classpath]
        args.append(str(java_file))
        rc, _o, _e = FID._run_jdk_tool("javac", javac_bin, args, FID.DEFAULT_JAVAC_TIMEOUT_SECONDS, tool_server)
        found = list(Path(td).rglob(f"{class_short}.class"))
        if rc != 0 or not found:
            return None
        text = FID.run_javap_verbose(str(found[0]), javap_bin=javap_bin, tool_server=tool_server)
        return (FID.parse_javap_verbose(text), text) if raw else FID.parse_javap_verbose(text)


def grade_text(text: str, class_short: str, shipped_class: Path, classpath: str, javac_bin: str,
               javap_bin: str, tool_server: bool) -> dict:
    """The grader's own single-rung grade of a source text (fresh temp dirs)."""
    with tempfile.TemporaryDirectory(prefix=f"n5sg-{class_short}-") as td:
        src = Path(td) / "src" / f"{class_short}.java"
        src.parent.mkdir()
        src.write_text(text, encoding="utf-8")
        return FID.recompile_and_grade(str(src), class_short, classpath, str(shipped_class), str(Path(td) / "out"),
                                       javac_bin, javap_bin, tool_server=tool_server)


# ---------------------------------------------------------------------------
# one class, one module
# ---------------------------------------------------------------------------

def splice_class(fqcn: str, mod_dir: Path, tree: str, **kw) -> dict:
    """{"status": "spliced", ...record, "_text": spliced} or
    {"status": "refused"|"not-candidate", "reason", "detail"} (see _splice_class)."""
    with tempfile.TemporaryDirectory(prefix=f"n5sd-{fqcn.rsplit('/', 1)[-1]}-") as td:
        return _splice_class(fqcn, mod_dir, tree, td, **kw)


def _splice_class(fqcn: str, mod_dir: Path, tree: str, td: str, *, classpath: str, helper_dir: Path, javac_bin: str,
                  javap_bin: str, java_bin: str, tool_server: bool, donor_trees: tuple = (),
                  primary_trees: tuple = (), hypotheses: tuple = (), decompilers: tuple = DONOR_ENGINES) -> dict:
    """{"status": "spliced", ...record, "_text": spliced} or
    {"status": "refused"|"not-candidate", "reason", "detail"}."""
    site_hyps = tuple(h for h in hypotheses if h in HYP.SITE_HYPOTHESES)
    hypotheses = tuple(h for h in hypotheses if h in HYP.HYPOTHESES)
    class_short = fqcn.rsplit("/", 1)[-1]
    shipped_class = mod_dir / "extracted" / f"{fqcn}.class"
    # the primary is the first existing tree of primary_trees (e.g. the m/p patch stage), then
    # <tree>p (F8), then <tree>
    candidates = [t for t in (*primary_trees, f"{tree}p", tree) if (mod_dir / t / f"{fqcn}.java").is_file()]
    if not candidates or not shipped_class.is_file():
        return {"status": "not-candidate", "reason": "no-source", "detail": str(mod_dir / tree / f"{fqcn}.java")}
    primary_tree = primary_path = primary_text = compiled = None
    for t in candidates:
        # the first tree that compiles is the primary (a patch stage, else a donor tree when the
        # baseline does not compile at all)
        path = mod_dir / t / f"{fqcn}.java"
        text = path.read_text(encoding="utf-8")
        compiled = compile_parse(path, class_short, classpath, javac_bin, javap_bin, tool_server, raw=True)
        if compiled is not None:
            primary_tree, primary_path, primary_text = t, path, text
            break
    if compiled is None:
        return {"status": "not-candidate", "reason": "primary-no-compile", "detail": candidates[0]}
    if any(ord(ch) > 0xFFFF for ch in primary_text):
        return {"status": "refused", "reason": "non-bmp", "detail": "javac offsets are UTF-16"}
    shipped_javap = FID.run_javap_verbose(str(shipped_class), javap_bin=javap_bin, tool_server=tool_server)
    shipped = FID.parse_javap_verbose(shipped_javap)
    primary_parsed, primary_javap = compiled
    verdicts, structure = per_method_verdicts(shipped, primary_parsed)
    base = {"primary_tree": primary_tree}
    original_text = primary_text
    # a primary that is not the baseline tree (nor its F8 patch) and is clean as it stands is a
    # result in itself; the baseline being clean is not (the class is then not a target)
    pre_transforms: list = ([{"kind": "primary-tree", "tree": primary_tree, "sha256": sha256_text(primary_text)}]
                            if primary_tree not in (tree, f"{tree}p") else [])

    def hyp_variant(name: str) -> str:
        """The hypothesis applied to the current primary; context hypotheses (needs_context) get the
        attributed spans and the shipped/recompiled code of every method."""
        fn = HYP.HYPOTHESES[name]
        if not getattr(fn, "needs_context", False):
            return fn(primary_text)
        try:
            scan = scan_spans([primary_path], helper_dir, java_bin, classpath)[str(primary_path)]
        except Refusal:
            return primary_text
        if scan["errors"]:
            return primary_text
        return fn(primary_text, {
            "methods": scan["methods"],
            "shipped": {k: m["code"] for k, m in shipped["methods"].items()},
            "ours": {k: m["code"] for k, m in primary_parsed["methods"].items()},
            "static": {k: "ACC_STATIC" in m["flags"] for k, m in shipped["methods"].items()},
            "lvt": HYP.lvt_types(shipped_javap),
            "mismatched": {k for k, x in verdicts.items() if x["verdict"] == "mismatch"}})

    def structure_ok(st: dict) -> bool:
        return st["fields_match"] and st["attrs_match"] and not st["missing"] and not st["extra"]

    def score(v: dict, st: dict) -> tuple:
        bad_structure = len(st["missing"]) + len(st["extra"]) + (not st["fields_match"]) + (not st["attrs_match"])
        return bad_structure, sum(1 for x in v.values() if x["verdict"] == "mismatch")

    def repair_structure_by_sites(max_rounds: int = 8, max_sites: int = 40) -> bool:
        """Greedy site repair: apply the single site whose swap lowers (structure differences,
        mismatching methods); repeat. Kept only when the class structure ends up matching."""
        nonlocal primary_text, primary_path, primary_parsed, verdicts, structure
        text, parsed, v, st = primary_text, primary_parsed, verdicts, structure
        applied: list = []
        for _round in range(max_rounds):
            improved = False
            for name in site_hyps:
                hyp = HYP.SITE_HYPOTHESES[name]
                for n, site in enumerate(hyp.sites(text)[:max_sites]):
                    cand = hyp.apply(text, site)
                    path = Path(td) / "site" / f"{len(applied)}-{n}" / f"{class_short}.java"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(cand, encoding="utf-8")
                    cp = compile_parse(path, class_short, classpath, javac_bin, javap_bin, tool_server)
                    if cp is None:
                        continue
                    cv, cs = per_method_verdicts(shipped, cp)
                    if score(cv, cs) < score(v, st):
                        text, parsed, v, st, primary_path_ = cand, cp, cv, cs, path
                        applied.append(name)
                        improved = True
                        break
                if improved:
                    break
            if not improved or (structure_ok(st) and score(v, st)[1] == 0):
                break
        if not applied or not structure_ok(st) or not score(v, st) < score(verdicts, structure):
            return False
        primary_text, primary_parsed, verdicts, structure = text, parsed, v, st
        primary_path = primary_path_
        pre_transforms.append({"kind": "site:" + applied[0] if len(set(applied)) == 1 else "site:mixed",
                               "sites": len(applied), "sha256": sha256_text(text)})
        return True

    def numbering_mismatch() -> bool:
        return any(v["verdict"] == "mismatch" and k in primary_parsed["methods"] and k in shipped["methods"]
                   and numbering_only(shipped["methods"][k]["code"], primary_parsed["methods"][k]["code"])
                   for k, v in verdicts.items())

    if structure_ok(structure) and site_hyps and numbering_mismatch():
        repair_structure_by_sites()

    if not structure_ok(structure):
        # C3d: lambda numbering, accessors, nest attributes... cannot be spliced method by method;
        # the first alternative source (donor tree, source hypothesis) that restores the class
        # structure with the fewest mismatching methods becomes the primary
        alts = []
        sources = [(f"tree:{t}", (mod_dir / t / f"{fqcn}.java").read_text(encoding="utf-8"))
                   for t in donor_trees if t != primary_tree and (mod_dir / t / f"{fqcn}.java").is_file()]
        sources += [(HYP_DONOR_PREFIX + h, hyp_variant(h)) for h in hypotheses]
        for n, (kind, text) in enumerate(sources):
            if text == primary_text:
                continue
            path = Path(td) / "alt" / str(n) / f"{class_short}.java"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            parsed = compile_parse(path, class_short, classpath, javac_bin, javap_bin, tool_server)
            if parsed is None:
                continue
            alt_verdicts, alt_structure = per_method_verdicts(shipped, parsed)
            if structure_ok(alt_structure):
                bad = sum(1 for x in alt_verdicts.values() if x["verdict"] == "mismatch")
                alts.append((bad, n, kind, text, path, parsed, alt_verdicts, alt_structure))
        if alts:
            _bad, _n, kind, primary_text, primary_path, primary_parsed, verdicts, structure = min(alts, key=lambda a: a[:2])
            if kind.startswith("tree:"):
                primary_tree = kind[len("tree:"):]
                pre_transforms.append({"kind": "primary-tree", "tree": primary_tree, "sha256": sha256_text(primary_text)})
            else:
                pre_transforms.append({"kind": kind, "sha256": sha256_text(primary_text)})
            base = {"primary_tree": primary_tree}
        elif site_hyps:
            repaired = repair_structure_by_sites()
            if repaired:
                base = {"primary_tree": primary_tree}
    non_synth = [k for k in structure["missing"] + structure["extra"] if not _is_synthetic_name(k[0])]
    if not structure["fields_match"] or not structure["attrs_match"] or non_synth:
        return {**base, "status": "refused", "reason": "structural-mismatch",
                "detail": f"fields={structure['fields_match']} attrs={structure['attrs_match']} "
                          f"members={[list(k) for k in non_synth][:4]}"}
    clinit_key = ("<clinit>", "()V")

    def adopt(text: str, kind: str, must_fix_clinit: bool) -> bool:
        """Make `text` the primary when it compiles and leaves no method worse (its mismatching
        methods are a subset of the current ones, and <clinit> is fixed when it must be)."""
        nonlocal primary_text, primary_path, primary_parsed, verdicts, structure
        path = Path(td) / "pre" / f"{len(pre_transforms)}" / f"{class_short}.java"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        parsed = compile_parse(path, class_short, classpath, javac_bin, javap_bin, tool_server)
        if parsed is None:
            return False
        new_verdicts, new_structure = per_method_verdicts(shipped, parsed)
        bad = lambda v: {k for k, x in v.items() if x["verdict"] == "mismatch"}  # noqa: E731
        if not bad(new_verdicts) <= bad(verdicts) or (must_fix_clinit and clinit_key in bad(new_verdicts)):
            return False
        if new_structure["missing"] or new_structure["extra"] or not new_structure["fields_match"] \
                or not new_structure["attrs_match"]:
            return False
        primary_text, primary_path, primary_parsed = text, path, parsed
        verdicts, structure = new_verdicts, new_structure
        pre_transforms.append({"kind": kind, "sha256": sha256_text(text)})
        return True

    if verdicts.get(clinit_key, {}).get("verdict") == "mismatch":
        # C3d: a source hypothesis that repairs the static initializer, then its recoverable order
        for h in hypotheses:
            variant = hyp_variant(h)
            if variant != primary_text and adopt(variant, HYP_DONOR_PREFIX + h, True):
                break
    if verdicts.get(clinit_key, {}).get("verdict") == "mismatch":
        try:
            scan = scan_spans([primary_path], helper_dir, java_bin, classpath)[str(primary_path)]
            if scan["errors"]:
                raise CLINIT.Unsupported(f"attribution: {scan['errors'][0]}")
            primary_javap = compile_parse(primary_path, class_short, classpath, javac_bin, javap_bin, tool_server,
                                          raw=True)[1]
            reordered = CLINIT.reorder_clinit(primary_text, scan["inits"], shipped["methods"][clinit_key]["code"],
                                              primary_javap, primary_parsed["methods"][clinit_key]["code"])
        except (CLINIT.Unsupported, Refusal):
            reordered = None
        if reordered is not None:
            adopt(reordered, "clinit-order", False)
    todo = sorted(k for k, v in verdicts.items() if v["verdict"] == "mismatch")
    if not todo and not structure["missing"] and not structure["extra"]:
        if not pre_transforms:
            return {**base, "status": "not-candidate", "reason": "already-clean", "detail": ""}
        grade = grade_text(primary_text, class_short, shipped_class, classpath, javac_bin, javap_bin, tool_server)
        if not FID._is_clean(grade["grade"]):
            return {**base, "status": "refused", "reason": "splice-not-clean", "detail": "clinit-order only"}
        return {**base, "status": "spliced", "original_sha256": sha256_text(original_text),
                "spliced_sha256": sha256_text(primary_text), "methods": [], "imports_added": [],
                "pre_transforms": pre_transforms, "self_grade": grade["grade"],
                "canonical_rules": grade.get("canonical_rules", []), "_text": primary_text}
    for k in todo:
        if k[0] == "<clinit>":
            return {**base, "status": "refused", "reason": "clinit", "detail": f"{k[0]}{k[1]}"}
        if _is_synthetic_name(k[0]):
            return {**base, "status": "refused", "reason": "synthetic-method", "detail": f"{k[0]}{k[1]}"}
    if not todo:
        return {**base, "status": "refused", "reason": "structural-mismatch", "detail": "synthetic members only"}

    donor_texts, donor_files, donor_verdicts = {}, {}, {}
    engines = (*decompilers, *(TREE_DONOR_PREFIX + t for t in donor_trees),
               *(HYP_DONOR_PREFIX + h for h in hypotheses))
    for eng in engines:
        if eng.startswith(HYP_DONOR_PREFIX):
            # a source hypothesis applied to the (possibly reordered) primary; identical text is no donor
            variant = hyp_variant(eng[len(HYP_DONOR_PREFIX):])
            if variant == primary_text:
                continue
            src = Path(td) / "hyp" / eng[len(HYP_DONOR_PREFIX):] / f"{class_short}.java"
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text(variant, encoding="utf-8")
        elif eng.startswith(TREE_DONOR_PREFIX):
            # an already-decompiled tree is a donor as-is (never the primary itself)
            name = eng[len(TREE_DONOR_PREFIX):]
            src = mod_dir / name / f"{fqcn}.java"
            if name == primary_tree or not src.is_file():
                continue
        else:
            jar = FID.DEFAULT_CFR_JAR if eng == "cfr" else FID.DEFAULT_PROCYON_JAR
            src, _reason_ = FID._decompile_one_class_with(java_bin, eng, jar, shipped_class, Path(td) / eng)
            if src is None:
                continue
        parsed = compile_parse(Path(src), class_short, classpath, javac_bin, javap_bin, tool_server)
        if parsed is None:
            continue
        donor_texts[eng] = Path(src).read_text(encoding="utf-8")
        donor_files[eng] = Path(src)
        donor_verdicts[eng] = per_method_verdicts(shipped, parsed)[0]
    options = {k: donor_candidates(k, donor_verdicts, engines) for k in todo}
    lacking = [k for k, v in options.items() if not v]
    if lacking:
        return {**base, "status": "refused", "reason": "no-donor", "donors_compiled": sorted(donor_verdicts),
                "detail": ", ".join(f"{k[0]}{k[1]}" for k in lacking[:4])}
    used = sorted({eng for v in options.values() for eng, _ in v})
    try:
        scans = scan_spans([primary_path] + [donor_files[e] for e in used], helper_dir, java_bin, classpath)
    except Refusal as r:
        return {**base, "status": "refused", "reason": r.reason, "detail": r.detail}
    primary_scan = scans[str(primary_path)]
    donors = {e: (donor_texts[e], scans[str(donor_files[e])]) for e in used}
    full_decl = {k: not verdicts[k].get("body_only", True) for k in todo}
    last = None
    for combo in itertools.islice(itertools.product(*(options[k] for k in todo)), MAX_COMBOS):
        assignment = {k: eng for k, (eng, _v) in zip(todo, combo)}
        try:
            text, imports = plan_splice(primary_text, primary_scan, donors, assignment, full_decl, class_short)
        except Refusal as r:
            last = (r.reason, r.detail)
            continue
        grade = grade_text(text, class_short, shipped_class, classpath, javac_bin, javap_bin, tool_server)
        if grade["grade"] == "no-compile":
            last = ("splice-no-compile", grade.get("first_error") or "")
            continue
        if not FID._is_clean(grade["grade"]):
            last = ("splice-not-clean", ", ".join(f"{m[0]}{m[1]}" for m in grade["mismatched_methods"][:4]))
            continue
        return {**base, "status": "spliced",
                "original_sha256": sha256_text(original_text), "spliced_sha256": sha256_text(text),
                    **({"pre_transforms": pre_transforms} if pre_transforms else {}),
                "methods": [{"name": k[0], "descriptor": k[1], "donor": eng, "reason": _reason(v),
                             "donor_sha256": sha256_text(donor_texts[eng]),
                             "span": "declaration" if full_decl[k] else "after-modifiers"}
                            for k, (eng, v) in zip(todo, combo)],
                "imports_added": imports, "self_grade": grade["grade"],
                "canonical_rules": grade.get("canonical_rules", []), "_text": text}
    return {**base, "status": "refused", "reason": last[0], "detail": last[1][:300]}


def splice_module(module: str, organized_dir: Path, tree: str, out_tree: str, targets: list, *, classpath: str,
                  helper_dir: Path, javac_bin: str, javap_bin: str, java_bin: str, tool_server: bool,
                  class_jobs: int = 1, donor_trees: tuple = (), primary_trees: tuple = (),
                  keep_existing: bool = False, hypotheses: tuple = (), decompilers: tuple = DONOR_ENGINES) -> dict:
    mod_dir = Path(organized_dir) / module
    out_dir = mod_dir / out_tree

    def one(fqcn: str):
        try:
            return fqcn, splice_class(fqcn, mod_dir, tree, classpath=classpath, helper_dir=helper_dir,
                                      javac_bin=javac_bin, javap_bin=javap_bin, java_bin=java_bin,
                                      tool_server=tool_server, donor_trees=tuple(donor_trees),
                                      primary_trees=tuple(primary_trees), hypotheses=tuple(hypotheses),
                                      decompilers=tuple(decompilers))
        except Exception as exc:  # noqa: BLE001 -- one class must not abort the module
            return fqcn, {"status": "refused", "reason": "tool-error", "detail": repr(exc)[:300]}

    # every class runs on this module's own pool (even a single one), so the
    # long-lived --jobs threads never own a tool-server JVM; the pool's JVMs are
    # closed once its threads have exited: at most jobs x class_jobs JVMs live
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, class_jobs)) as pool:
        results = list(pool.map(one, targets))
    FID.reap_dead_thread_tool_servers()
    old_classes = {}
    manifest_path = out_dir / MANIFEST_NAME
    if keep_existing and manifest_path.is_file():
        # a later stage extends an earlier one: its splices survive unless re-targeted here
        old_classes = {f: r for f, r in json.loads(manifest_path.read_text()).get("classes", {}).items()
                       if f not in set(targets) and (out_dir / f"{f}.java").is_file()}
    if out_dir.is_dir():
        for old in out_dir.rglob("*.java"):
            if not (keep_existing and old.relative_to(out_dir).with_suffix("").as_posix() in old_classes):
                old.unlink()
    classes, refused, skipped = dict(old_classes), {}, {}
    for fqcn, rec in sorted(results):
        status = rec.pop("status")
        if status == "spliced":
            text = rec.pop("_text")
            dest = out_dir / f"{fqcn}.java"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
            classes[fqcn] = rec
        elif status == "refused":
            refused[fqcn] = rec
        else:
            skipped[fqcn] = rec
    manifest = {"schema": MANIFEST_SCHEMA, "module": module, "source_tree": tree,
                "tool": "tools/n5-splice-methods.py",
                "helper_sha256": hashlib.sha256(HELPER_SRC.read_bytes()).hexdigest(),
                "donor_engines": [*decompilers, *(TREE_DONOR_PREFIX + t for t in donor_trees),
                                  *(HYP_DONOR_PREFIX + h for h in hypotheses if h in HYP.HYPOTHESES),
                                  *("site:" + h for h in hypotheses if h in HYP.SITE_HYPOTHESES)], "classes": classes, "refused": refused,
                "not_candidates": skipped}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--targets", required=True, help="JSON file: [[module, fqcn], ...]")
    ap.add_argument("--modules", default=None, help="restrict --targets to these modules")
    ap.add_argument("--organized-dir", default=str(FID.DEFAULT_ORGANIZED_DIR))
    ap.add_argument("--tree", default="vineflower2")
    ap.add_argument("--out-tree", default=None, help="default: <tree>s")
    ap.add_argument("--modules-dir", default=str(FID.DEFAULT_MODULES_DIR))
    ap.add_argument("--bin-ext-dir", default=str(FID.DEFAULT_BIN_EXT_DIR))
    ap.add_argument("--jre-dir", default=str(FID.DEFAULT_JRE_DIR))
    ap.add_argument("--bc-variant", choices=FID.BC_VARIANTS, default=FID.DEFAULT_BC_VARIANT)
    ap.add_argument("--classpath-cache-dir", default=None)
    ap.add_argument("--helper-cache-dir", default=None)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--class-jobs", type=int, default=1)
    ap.add_argument("--tool-server", action="store_true")
    ap.add_argument("--donor-trees", default="",
                    help="comma-separated on-disk trees (organized/<mod>/<tree>/) used as extra donors after "
                         "CFR/Procyon, e.g. vineflower-cons,vineflower")
    ap.add_argument("--primary-trees", default="",
                    help="comma-separated trees tried first as the primary source, e.g. vineflower2m "
                         "(then <tree>p, then <tree>)")
    ap.add_argument("--decompilers", default=",".join(DONOR_ENGINES),
                    help="comma-separated re-decompile donors (cfr, procyon); empty = none, use when only "
                         "on-disk trees and hypotheses should be tried")
    ap.add_argument("--hypotheses", default="",
                    help="comma-separated source hypotheses of tools/n5_source_hypotheses.py used as donors "
                         "(\"all\" = every one)")
    ap.add_argument("--keep-existing", action="store_true",
                    help="keep the out tree's earlier splices that are not re-targeted (extend a stage)")
    args = ap.parse_args(argv)
    split = lambda v: tuple(x.strip() for x in v.split(",") if x.strip())  # noqa: E731
    known = (*HYP.HYPOTHESES, *HYP.SITE_HYPOTHESES)
    hypotheses = known if args.hypotheses.strip() == "all" else split(args.hypotheses)
    unknown = [h for h in hypotheses if h not in known]
    if unknown:
        ap.error(f"unknown hypothesis {unknown}; known: {sorted(known)}")
    by_module: dict = {}
    for module, fqcn in json.loads(Path(args.targets).read_text()):
        by_module.setdefault(module, []).append(fqcn)
    if args.modules:
        keep = {m.strip() for m in args.modules.split(",")}
        by_module = {m: v for m, v in by_module.items() if m in keep}
    tmp = Path(tempfile.gettempdir())
    cache = Path(args.classpath_cache_dir) if args.classpath_cache_dir else tmp / "n5-fidelity-classpath-cache"
    classpath = FID.build_classpath(cache, Path(args.modules_dir), Path(args.bin_ext_dir), bc_variant=args.bc_variant,
                                    jre_dir=Path(args.jre_dir) if args.jre_dir else None)
    helper = compile_helper(Path(args.helper_cache_dir) if args.helper_cache_dir else tmp / "n5-splice-methods",
                            FID.DEFAULT_JAVAC)
    out_tree = args.out_tree or args.tree + "s"
    failed = []

    def run(module: str):
        try:
            man = splice_module(module, Path(args.organized_dir), args.tree, out_tree, sorted(by_module[module]),
                                classpath=classpath, helper_dir=helper, javac_bin=FID.DEFAULT_JAVAC,
                                javap_bin=FID.DEFAULT_JAVAP, java_bin=FID.DEFAULT_JAVA,
                                tool_server=args.tool_server, class_jobs=args.class_jobs,
                                donor_trees=split(args.donor_trees), primary_trees=split(args.primary_trees),
                                keep_existing=args.keep_existing, hypotheses=hypotheses,
                                decompilers=split(args.decompilers))
            reasons: dict = {}
            for r in man["refused"].values():
                reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
            print(f"[{module}] spliced {len(man['classes'])} refused {reasons} "
                  f"not-candidates {len(man['not_candidates'])}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 -- one module must not abort the batch
            print(f"[{module}] FAILED: {exc!r}", file=sys.stderr, flush=True)
            failed.append(module)

    if args.jobs > 1 and len(by_module) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(run, sorted(by_module)))
    else:
        for m in sorted(by_module):
            run(m)
    FID.shutdown_tool_servers()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
