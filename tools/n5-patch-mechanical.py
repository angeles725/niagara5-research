#!/usr/bin/env python3
"""n5-patch-mechanical.py -- javac-error-driven mechanical source patches for decompiled
N5 classes that stay bytecode-only because the source does not compile (C3b/C3c/C3a-G2).

The F8/C3a patcher (n5-patch-doprivileged.py) fixes one defect from bytecode evidence. This
stage generalises the pattern to the other Vineflower defects that have exactly one
deterministic source-level fix. Every patch is a `fixer`:

  * it recognises ONE javac error shape (message + the source line javac points at),
  * it rewrites only that construct (no guessing between alternatives: when the shape is
    not unambiguous the site is left alone and reported as residual),
  * javac re-verifies after every round: a round that does not reduce the error count is
    reverted and the fixer is blacklisted for that class.

The grader (tools/n5-fidelity.py --regrade-nonclean --patch-tree <tree>) decides whether a
patched class is faithful; this tool never claims fidelity. Input is the vineflower2p
tree when it has the class (the C3a output), else vineflower2. Output tree
(default vineflower2m) holds every vineflower2p file (carried unchanged, so the regrade of
the patched rung keeps the C3a results) plus the mechanically patched classes, and a
PATCHES.json manifest recording each patch (fixer kind, line, javac evidence) and each
unresolved class with its residual javac errors.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

MAX_ROUNDS = 8

_ERR_RE = re.compile(r"^(?:.*\.java):(\d+): error: (.*)$")


def parse_javac_errors(stderr: str) -> list[dict]:
    """[{line, col, message, detail}] for every javac error. `col` is the caret column
    (0-based) within the source line, `detail` the indented lines after the caret."""
    lines = stderr.splitlines()
    out: list[dict] = []
    i = 0
    while i < len(lines):
        m = _ERR_RE.match(lines[i])
        if not m:
            i += 1
            continue
        err = {"line": int(m.group(1)), "message": m.group(2), "col": None, "detail": []}
        j = i + 1
        # source line, caret line, then detail lines up to the next diagnostic
        if j < len(lines):
            j += 1
        if j < len(lines) and lines[j].rstrip().endswith("^") and set(lines[j].rstrip()[:-1]) <= {" ", "\t"}:
            err["col"] = len(lines[j].rstrip()) - 1
            j += 1
        while j < len(lines) and not re.match(r"^.*\.java:\d+: (error|warning)|^Note: |^\d+ errors?$", lines[j]):
            err["detail"].append(lines[j])
            j += 1
        out.append(err)
        i = j
    return out


def _error_count(stderr: str) -> int:
    return len(parse_javac_errors(stderr))


# ---------------------------------------------------------------------------
# fixers: fn(lines, errors) -> Optional[(new_lines, [patch records])]
# ---------------------------------------------------------------------------

def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


_BINDING_RE = re.compile(
    r"^(?P<ind>\s*)if \(!\((?P<expr>[\w.]+) instanceof (?P<type>[\w.<>?, \[\]]+?) (?P<var>\w+)\)\) \{\s*$")


def fix_pattern_binding_scope(lines: list[str], errors: list[dict]):
    """`if (!(E instanceof T v)) { ...v = X; }` then `v` used after the if: javac puts a
    negated-instanceof binding in scope after the statement only when the block cannot
    complete normally. Vineflower folds `else v = (T)E;` into the binding. Restore the
    bytecode shape: declare `T v;`, test `!(E instanceof T)`, add `else { v = (T)E; }`."""
    missing = {}
    for e in errors:
        if e["message"] == "cannot find symbol":
            m = re.search(r"symbol:\s+variable (\w+)", "\n".join(e["detail"]))
            if m:
                missing.setdefault(m.group(1), e["line"])
    if not missing:
        return None
    new = list(lines)
    patches = []
    # bottom-up so earlier line numbers stay valid
    sites = []
    for var, err_line in missing.items():
        for k in range(min(err_line, len(lines)) - 1, -1, -1):
            m = _BINDING_RE.match(lines[k])
            if m and m.group("var") == var:
                sites.append((k, m))
                break
    for k, m in sorted(sites, key=lambda s: -s[0]):
        ind = m.group("ind")
        end = next((j for j in range(k + 1, len(new)) if _indent(new[j]) == ind and new[j].strip() == "}"), None)
        if end is None:
            continue
        typ, var, expr = m.group("type"), m.group("var"), m.group("expr")
        new[end:end + 1] = [f"{ind}}} else {{", f"{ind}   {var} = ({typ}){expr};", f"{ind}}}"]
        new[k] = f"{ind}if (!({expr} instanceof {typ})) {{"
        new.insert(k, f"{ind}{typ} {var};")
        patches.append({"kind": "pattern-binding-scope", "line": k + 1, "variable": var,
                        "evidence": f"javac: cannot find symbol variable {var} (negated instanceof binding not in scope)"})
    if not patches:
        return None
    return new, patches


_BOXED = {"int": "Integer", "long": "Long", "short": "Short", "byte": "Byte", "char": "Character",
          "boolean": "Boolean", "float": "Float", "double": "Double"}
_RAW_ITERABLES = ("List", "Set", "Collection", "Iterable", "ArrayList", "LinkedList", "HashSet", "LinkedHashSet",
                  "TreeSet", "SortedSet", "Vector", "Queue", "Deque", "ArrayDeque")
_FOREACH_RAW_RE = re.compile(
    r"(for \((?:final )?(?P<type>[\w.<>?\[\]]+) \w+ : )\((?P<raw>(?:[\w.]+\.)?(?:%s))\)" % "|".join(_RAW_ITERABLES))


def fix_foreach_raw_cast(lines: list[str], errors: list[dict]):
    """`for (T v : (List)expr)` -- javac: `Object cannot be converted to T`. The decompiler
    dropped the type argument of the raw cast; the loop variable's type is the element
    type the bytecode checkcasts to, so the cast becomes `(List<T>)` (boxed for a primitive)."""
    new = list(lines)
    patches = []
    for e in errors:
        if not re.match(r"incompatible types: (?:java\.lang\.)?Object cannot be converted to ", e["message"]):
            continue
        k = e["line"] - 1
        m = _FOREACH_RAW_RE.search(new[k]) if 0 <= k < len(new) else None
        if not m:
            continue
        typ = m.group("type")
        arg = _BOXED.get(typ, typ)
        new[k] = new[k][:m.start()] + f"{m.group(1)}({m.group('raw')}<{arg}>)" + new[k][m.end():]
        patches.append({"kind": "foreach-raw-cast", "line": e["line"], "element_type": arg,
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_BOOL_AS_INT_RE = re.compile(r"^(?P<ind>\s*)int (?P<var>\w+) = (?P<lit>true|false);\s*$")


def fix_boolean_declared_int(lines: list[str], errors: list[dict]):
    """`int v = false;` -- javac: `boolean cannot be converted to int`. Vineflower typed the
    local by the JVM's int slot; the source only compiles with the literal's type."""
    new = list(lines)
    patches = []
    for e in errors:
        if e["message"] != "incompatible types: boolean cannot be converted to int":
            continue
        k = e["line"] - 1
        m = _BOOL_AS_INT_RE.match(new[k]) if 0 <= k < len(new) else None
        if not m:
            continue
        new[k] = f"{m.group('ind')}boolean {m.group('var')} = {m.group('lit')};"
        patches.append({"kind": "boolean-declared-int", "line": e["line"], "variable": m.group("var"),
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_INSTANCEOF_GENERIC_RE = re.compile(r"instanceof (?P<raw>[\w.]+)<[^<>()]*(?:<[^<>()]*>[^<>()]*)*> (?P<var>\w+)")


def fix_instanceof_generic_raw(lines: list[str], errors: list[dict]):
    """`x instanceof Comparable<T> v` -- javac: `Object cannot be safely cast to Comparable<T>`.
    instanceof is erased in the class file, so the type arguments carry no bytecode
    evidence; the raw type is the only spelling that is always legal."""
    new = list(lines)
    patches = []
    for e in errors:
        if not re.search(r"cannot be safely cast to ", e["message"]):
            continue
        k = e["line"] - 1
        m = _INSTANCEOF_GENERIC_RE.search(new[k]) if 0 <= k < len(new) else None
        if not m:
            continue
        new[k] = new[k][:m.start()] + f"instanceof {m.group('raw')} {m.group('var')}" + new[k][m.end():]
        patches.append({"kind": "instanceof-generic-raw", "line": e["line"], "variable": m.group("var"),
                        "evidence": "javac: " + e["message"]})
    return (new, patches) if patches else None


_LABEL_RE = re.compile(r"^\s*(?:case .*|default)\s*:\s*$")
_REDEF_RE = re.compile(r"variable (\w+) is already defined in ")


def _case_group(lines: list[str], k: int, ind: int):
    """(first_label, last_label, last_stmt) of the switch group holding line k whose
    statements sit at column `ind` (labels at ind-3), or None."""
    lab = None
    for j in range(k - 1, -1, -1):
        s = lines[j]
        if not s.strip():
            continue
        i = len(s) - len(s.lstrip())
        if i < ind - 3:
            return None
        if i == ind - 3:
            if _LABEL_RE.match(s):
                lab = j
                break
            return None
    if lab is None:
        return None
    first = lab
    while first > 0 and _LABEL_RE.match(lines[first - 1]) and _indent(lines[first - 1]) == _indent(lines[lab]):
        first -= 1
    end = None
    for j in range(lab + 1, len(lines)):
        s = lines[j]
        if not s.strip():
            continue
        i = len(s) - len(s.lstrip())
        if i < ind:
            break
        end = j
    return None if end is None else (first, lab, end)


def fix_switch_group_scope(lines: list[str], errors: list[dict]):
    """`variable v is already defined` where the duplicate sits in a switch group: switch
    groups share one scope, so the original source had braces around each group (javac
    reuses the slot). Brace every group of the switch that declares `v`."""
    groups: dict[int, tuple] = {}
    for e in errors:
        m = _REDEF_RE.match(e["message"])
        k = e["line"] - 1
        if not m or not 0 <= k < len(lines):
            continue
        var = m.group(1)
        ind = len(lines[k]) - len(lines[k].lstrip())
        g = _case_group(lines, k, ind)
        if g is None:
            continue
        groups[g[1]] = g
        decl = re.compile(r"^\s{%d}(?:final )?[\w.<>\[\]?, ]+ %s\b\s*(?:=|;)" % (ind, re.escape(var)))
        # earlier groups of the same switch that declare the variable
        j = g[0] - 1
        while j >= 0:
            if lines[j].strip() and _indent(lines[j]) and len(_indent(lines[j])) < ind - 3:
                break
            if _LABEL_RE.match(lines[j]) and len(_indent(lines[j])) == ind - 3:
                eg = _case_group(lines, j + 1, ind)
                if eg and eg[1] == j and any(decl.match(lines[t]) for t in range(eg[1] + 1, eg[2] + 1)):
                    groups[eg[1]] = eg
                    j = eg[0]
            j -= 1
    if not groups:
        return None
    new = list(lines)
    patches = []
    for lab, first, end in sorted(((g[1], g[0], g[2]) for g in groups.values()), reverse=True):
        ind = _indent(new[lab])
        new.insert(end + 1, f"{ind}}}")
        new[lab] = new[lab].rstrip() + " {"
        patches.append({"kind": "switch-group-scope", "line": lab + 1,
                        "evidence": "javac: variable already defined across switch groups"})
    return new, patches


FIXERS: list[tuple[str, Callable]] = [
    ("pattern-binding-scope", fix_pattern_binding_scope),
    ("foreach-raw-cast", fix_foreach_raw_cast),
    ("boolean-declared-int", fix_boolean_declared_int),
    ("instanceof-generic-raw", fix_instanceof_generic_raw),
    ("switch-group-scope", fix_switch_group_scope),
]


def patch_source(original: str, compile_fn: Callable[[str], str], fixers=None, max_rounds: int = MAX_ROUNDS) -> dict:
    """Apply fixers driven by javac feedback. `compile_fn(text) -> ''` on success, else stderr.
    Returns {text, patches, compiles, residual_errors, rounds}."""
    fixers = list(FIXERS if fixers is None else fixers)
    text = original
    err = compile_fn(text)
    patches: list[dict] = []
    banned: set[str] = set()
    rounds = 0
    while err and rounds < max_rounds:
        errors = parse_javac_errors(err)
        applied = False
        for name, fn in fixers:
            if name in banned:
                continue
            lines = text.split("\n")
            got = fn(lines, errors)
            if got is None:
                continue
            new_text = "\n".join(got[0])
            new_err = compile_fn(new_text)
            if new_err and _error_count(new_err) >= len(errors):
                banned.add(name)
                continue
            text, err = new_text, new_err
            patches.extend(got[1])
            applied = True
            break
        rounds += 1
        if not applied:
            break
    residual = parse_javac_errors(err) if err else []
    return {"text": text, "patches": patches, "compiles": not err, "rounds": rounds,
            "residual_errors": [{"line": e["line"], "message": e["message"]} for e in residual],
            "residual_error_count": len(residual)}


# ---------------------------------------------------------------------------
# population + module driver
# ---------------------------------------------------------------------------

import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
MANIFEST_NAME = "PATCHES.json"
MANIFEST_SCHEMA = 1
# ladder order, lowest first; a later rung wins a rank tie (see n5-fidelity.py _GRADE_RANK)
RUNGS = ("vineflower", "vineflower2", "vineflower2.canon", "vineflower2.patched", "vineflower2.spliced")
GRADE_RANK = {"no-compile": 0, "timeout": 0, "harness-error": 0, "compiles-mismatch": 1, "bytecode-only": 1,
              "roundtrip-canonical-t2": 2, "roundtrip-canonical": 3, "roundtrip-equivalent": 4, "roundtrip-exact": 5}
SOURCE_TREES = ("vineflower2p", "vineflower2")  # preferred first


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity_for_mech", TOOLS_DIR / "n5-fidelity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def module_population(mod_dir: Path) -> dict[str, dict]:
    """{fqcn: {best_grade, tree, source_grade}} for the module's best-of-ladder
    `bytecode-only` classes; `tree` is the source tree that is graded no-compile on the most
    advanced rung that recorded it (vineflower2p when it has the class, else vineflower2)
    and `source_grade` that attempt's grade. Uses the grader JSON only."""
    recs: dict[str, dict] = {}
    for r in RUNGS:
        p = mod_dir / f"fidelity.{r}.json"
        if p.is_file():
            try:
                recs[r] = json.loads(p.read_text())["classes"]
            except (json.JSONDecodeError, OSError, KeyError):
                pass
    names = set()
    for c in recs.values():
        names |= set(c)
    out = {}
    for f in names:
        best_grade, rung_recs = -1, {}
        for r in RUNGS:
            rec = recs.get(r, {}).get(f)
            if rec is None:
                continue
            rung_recs[r] = rec
            best_grade = max(best_grade, GRADE_RANK.get(rec["grade"], -1))
        # the class's best grade is the best over the rungs; only bytecode-only classes are targets
        best_names = [rec["grade"] for rec in rung_recs.values() if GRADE_RANK.get(rec["grade"], -1) == best_grade]
        if "bytecode-only" not in best_names or best_grade != GRADE_RANK["bytecode-only"]:
            continue
        tree = next((t for t in SOURCE_TREES if (mod_dir / t / f"{f}.java").is_file()), None)
        if tree is None:
            continue
        source_grade = None
        for r in reversed(RUNGS):
            if r in rung_recs:
                source_grade = next((g for n, g in rung_recs[r].get("attempted", []) if n == tree), None)
                if source_grade:
                    break
        out[f] = {"tree": tree, "source_grade": source_grade}
    return out


def make_compile_fn(fid, classpath: str, javac_bin: str, tool_server: bool, class_short: str):
    def compile_fn(text: str) -> str:
        with tempfile.TemporaryDirectory(prefix=f"n5mech-{class_short}-") as td:
            src = Path(td) / "src" / f"{class_short}.java"
            src.parent.mkdir()
            src.write_text(text, encoding="utf-8")
            args = ["--release", "25", "-g", "-implicit:none", "-proc:none", "-nowarn", "-Xmaxerrs", "100000",
                    "-d", str(Path(td) / "out")]
            if classpath:
                args += ["-cp", classpath]
            args.append(str(src))
            rc, _o, e = fid._run_jdk_tool("javac", javac_bin, args, 300, tool_server)
            return "" if rc == 0 else (e or "javac failed")
    return compile_fn


def patch_module(module: str, organized: Path, out_tree: str, *, fid, classpath: str, javac_bin: str,
                 tool_server: bool, only: Optional[set] = None, class_jobs: int = 1) -> dict:
    mod_dir = organized / module
    pop = module_population(mod_dir)
    targets = {f: v for f, v in pop.items() if v["source_grade"] == "no-compile" and (only is None or f in only)}
    out_dir = mod_dir / out_tree
    records: dict[str, dict] = {}

    def one(f: str):
        v = targets[f]
        src = mod_dir / v["tree"] / f"{f}.java"
        original = src.read_text(encoding="utf-8")
        res = patch_source(original, make_compile_fn(fid, classpath, javac_bin, tool_server, src.stem))
        rec = {"source_tree": v["tree"], "original_sha256": sha256_text(original),
               "patched_sha256": sha256_text(res["text"]), "patches": res["patches"], "compiles": res["compiles"],
               "residual_error_count": res["residual_error_count"], "residual_errors": res["residual_errors"][:20],
               "rounds": res["rounds"]}
        return f, rec, res["text"]

    results = []
    if class_jobs > 1 and len(targets) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=class_jobs) as pool:
            results = list(pool.map(one, sorted(targets)))
    else:
        results = [one(f) for f in sorted(targets)]

    if out_dir.is_dir():
        shutil.rmtree(out_dir)
    carried = 0
    p_dir = mod_dir / "vineflower2p"
    if p_dir.is_dir():
        for p in p_dir.rglob("*.java"):
            dest = out_dir / p.relative_to(p_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dest)
            carried += 1
    for f, rec, text in results:
        records[f] = rec
        if rec["patches"] and rec["compiles"]:
            dest = out_dir / f"{f}.java"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")
    manifest = {"schema": MANIFEST_SCHEMA, "module": module, "tool": "tools/n5-patch-mechanical.py",
                "carried_from": "vineflower2p", "carried_files": carried, "classes": records}
    if records or carried:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv: Optional[list[str]] = None) -> int:
    fid = _load_fidelity()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modules")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--organized-dir", default=str(fid.DEFAULT_ORGANIZED_DIR))
    ap.add_argument("--out-tree", default="vineflower2m")
    ap.add_argument("--modules-dir", default=str(fid.DEFAULT_MODULES_DIR))
    ap.add_argument("--bin-ext-dir", default=str(fid.DEFAULT_BIN_EXT_DIR))
    ap.add_argument("--jre-dir", default=str(fid.DEFAULT_JRE_DIR))
    ap.add_argument("--bc-variant", choices=fid.BC_VARIANTS, default=fid.DEFAULT_BC_VARIANT)
    ap.add_argument("--classpath-cache-dir", default=None)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--class-jobs", type=int, default=1)
    ap.add_argument("--tool-server", action="store_true")
    args = ap.parse_args(argv)
    organized = Path(args.organized_dir)
    if args.all:
        modules = [p.name for p in sorted(organized.iterdir())
                   if p.is_dir() and not p.name.startswith("_") and (p / "vineflower2").is_dir()]
    elif args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    else:
        ap.error("pass --modules a,b or --all")
    cache = Path(args.classpath_cache_dir) if args.classpath_cache_dir \
        else Path(tempfile.gettempdir()) / "n5-fidelity-classpath-cache"
    classpath = fid.build_classpath(cache, Path(args.modules_dir), Path(args.bin_ext_dir), bc_variant=args.bc_variant,
                                    jre_dir=Path(args.jre_dir) if args.jre_dir else None)
    failed = []

    def run(module: str):
        try:
            man = patch_module(module, organized, args.out_tree, fid=fid, classpath=classpath,
                               javac_bin=fid.DEFAULT_JAVAC, tool_server=args.tool_server, class_jobs=args.class_jobs)
            n_t = len(man["classes"])
            n_p = sum(1 for r in man["classes"].values() if r["patches"])
            n_c = sum(1 for r in man["classes"].values() if r["compiles"])
            print(f"[{module}] targets {n_t} patched {n_p} now-compiling {n_c}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 -- one module must not abort the batch
            print(f"[{module}] FAILED: {exc!r}", file=sys.stderr, flush=True)
            failed.append(module)

    if args.jobs > 1 and len(modules) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(run, modules))
    else:
        for m in modules:
            run(m)
    fid.shutdown_tool_servers()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
