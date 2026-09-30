#!/usr/bin/env python3
"""n5-exact-regrade.py -- C4: make the proven-but-not-exact Tridium classes exact.

Population = the best-of grade of every top-level Tridium class over the fidelity.<rung>.json ladder
files (tools/n5-fidelity.py merge_best_of_records). The C4 targets are the classes proven only
by the sound canonicalizer (roundtrip-canonical / -canonical-t2 / -equivalent): their shipped
bytecode is reproduced up to a semantics-preserving rewrite, and the goal is the shipped instruction
stream itself.

  targets   write the target list ([[module, fqcn], ...]) for tools/n5-splice-methods.py --exact
  census    class counts per canonical rule / rule set over the targets
  regrade   grade the C4 splice trees (organized/<mod>/vineflower2s) through the official ladder,
            including classes whose baseline grade is already clean. tools/n5-fidelity.py's
            --regrade-nonclean only revisits classes that are NOT clean at baseline, so the
            regrade runs on a scratch farm whose baseline JSON marks the targets non-clean, and
            the resulting records are merged into the real fidelity.vineflower2.spliced.json
            (a record is replaced only by one that ranks at least as high)
  recount   best-of grade counts before/after, per-class improvements and rank regressions

Usage:
  python3 tools/n5-exact-regrade.py --organized-dir <organized> targets --out targets.json
  python3 tools/n5-exact-regrade.py --organized-dir <organized> census
  python3 tools/n5-exact-regrade.py --organized-dir <organized> regrade --targets t.json --tool-server
  python3 tools/n5-exact-regrade.py --organized-dir <organized> recount --before best-before.json
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import importlib.util
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional

TOOLS_DIR = Path(__file__).resolve().parent


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity_for_exact", TOOLS_DIR / "n5-fidelity.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


FID = _load_fidelity()

PROVEN_NOT_EXACT = ("roundtrip-canonical", "roundtrip-canonical-t2", "roundtrip-equivalent")
SPLICE_TREE = "vineflower2s"
SPLICED_RUNG = "vineflower2.spliced"


def rank(grade: str) -> int:
    return FID._GRADE_RANK.get(grade, -1)


def modules_of(organized: Path) -> list[str]:
    return sorted(p.name for p in Path(organized).iterdir()
                  if p.is_dir() and not p.name.startswith("_") and any(p.glob("fidelity.*.json")))


def load_best(organized: Path, modules: Optional[list] = None) -> dict:
    """{(module, fqcn): best-of record} over every module's fidelity.<rung>.json ladder files."""
    best: dict = {}
    for mod in modules or modules_of(organized):
        rungs: dict = {}
        for rung in FID.BEST_OF_RUNGS:
            path = Path(organized) / mod / f"fidelity.{rung}.json"
            if not path.is_file():
                continue
            for fqcn, record in json.loads(path.read_text()).get("classes", {}).items():
                rungs.setdefault(fqcn, {})[rung] = record
        for fqcn, by_rung in rungs.items():
            best[(mod, fqcn)] = FID.merge_best_of_records(by_rung)
    return best


def exact_targets(best: dict) -> list:
    return sorted(k for k, v in best.items() if v["grade"] in PROVEN_NOT_EXACT)


def rule_census(best: dict) -> dict:
    """Classes per canonical rule, per irreducible rule set, and with no rule (baseline layout only)."""
    rules: collections.Counter = collections.Counter()
    sets: collections.Counter = collections.Counter()
    none = 0
    for key in exact_targets(best):
        used = tuple(sorted(best[key].get("canonical_rules") or []))
        if not used:
            none += 1
            continue
        sets[used] += 1
        rules.update(used)
    return {"rules": dict(rules), "sets": dict(sets), "no_rules": none}


def grade_counts(best: dict) -> dict:
    return dict(collections.Counter(v["grade"] for v in best.values()))


def recount(before: dict, after: dict) -> dict:
    improved = sorted(k for k in after if k in before and rank(after[k]["grade"]) > rank(before[k]["grade"]))
    regressed = sorted(k for k in after if k in before and rank(after[k]["grade"]) < rank(before[k]["grade"]))
    return {"before": grade_counts(before), "after": grade_counts(after), "improved": improved,
            "regressed": regressed, "missing": sorted(set(before) - set(after))}


def build_farm(organized: Path, farm: Path, module: str, fqcns: list) -> Path:
    """A scratch copy of one module's directory whose baseline JSON marks `fqcns` non-clean (every
    other class clean), so the official regrade grades exactly those with a splice-tree source."""
    real, mod_dir = Path(organized) / module, Path(farm) / module
    mod_dir.mkdir(parents=True)
    skip = {"fidelity.vineflower2.json", "fidelity.vineflower2.spliced.json"}
    for entry in os.listdir(real):
        if entry not in skip:
            os.symlink(real / entry, mod_dir / entry)
    base = json.loads((real / "fidelity.vineflower2.json").read_text())
    for fqcn, record in base["classes"].items():
        base["classes"][fqcn] = dict(record, grade="compiles-mismatch" if fqcn in fqcns else "roundtrip-exact")
    (mod_dir / "fidelity.vineflower2.json").write_text(json.dumps(base))
    return mod_dir


def merge_spliced(organized: Path, module: str, farm_result: dict, fqcns: list) -> dict:
    """Merge the farm's regraded records into the real fidelity.vineflower2.spliced.json. A record is
    replaced only when the new grade ranks at least as high; returns {"replaced": n, "kept": n}."""
    mod_dir = Path(organized) / module
    path = mod_dir / f"fidelity.{SPLICED_RUNG}.json"
    base_path = mod_dir / "fidelity.vineflower2.json"
    base = json.loads(base_path.read_text())
    if path.is_file():
        merged = json.loads(path.read_text())
    else:
        merged = {k: v for k, v in farm_result.items() if k not in ("classes", "grade_counts")}
        merged["classes"] = {fqcn: dict(rec) for fqcn, rec in base["classes"].items()}
        merged["regraded_classes"] = []
    replaced = kept = 0
    for fqcn in fqcns:
        new = farm_result["classes"].get(fqcn)
        if new is None:
            continue
        old = merged["classes"].get(fqcn)
        if old is not None and rank(new["grade"]) < rank(old["grade"]):
            kept += 1
            continue
        new = dict(new, previous_grade=(old or base["classes"].get(fqcn) or {}).get("grade"))
        merged["classes"][fqcn] = new
        replaced += 1
        if fqcn not in merged["regraded_classes"]:
            merged["regraded_classes"].append(fqcn)
    merged["grade_counts"] = dict(collections.Counter(r["grade"] for r in merged["classes"].values()))
    merged["source_sha256"] = FID.sha256_of(base_path)
    manifest = mod_dir / SPLICE_TREE / FID.patch_manifest_name("vineflower2", SPLICE_TREE)
    merged["patch_manifest_sha256"] = FID.sha256_of(manifest) if manifest.is_file() else None
    merged["patch_tree"] = SPLICE_TREE
    merged["complete"] = True
    FID._write_json_atomic(path, merged)
    return {"replaced": replaced, "kept": kept}


def regrade_module(organized: Path, module: str, fqcns: list, *, class_jobs: int = 1,
                   grade_fn: Optional[Callable] = None, **grade_kwargs) -> dict:
    """Grade `fqcns` of one module on the ladder with the C4 splice tree as the patch rung and merge
    the records into the real spliced JSON."""
    with tempfile.TemporaryDirectory(prefix=f"n5-exact-{module}-") as td:
        build_farm(organized, Path(td), module, set(fqcns))
        result = FID.regrade_nonclean_module(module, organized_dir=Path(td), tree="vineflower2",
                                             class_jobs=class_jobs, patch_tree=SPLICE_TREE, force=True,
                                             grade_fn=grade_fn, **grade_kwargs)
    return merge_spliced(organized, module, result, fqcns)


def by_module(targets: list) -> dict:
    out: dict = {}
    for module, fqcn in targets:
        out.setdefault(module, []).append(fqcn)
    return out


def _dump_best(best: dict) -> dict:
    return {f"{m}::{c}": v for (m, c), v in best.items()}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--organized-dir", default=str(FID.DEFAULT_ORGANIZED_DIR))
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("targets")
    p.add_argument("--out", required=True)
    sub.add_parser("census")
    p = sub.add_parser("snapshot", help="write the best-of records to a JSON file (the `before` of a recount)")
    p.add_argument("--out", required=True)
    p = sub.add_parser("regrade")
    p.add_argument("--targets", required=True)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--class-jobs", type=int, default=1)
    p.add_argument("--tool-server", action="store_true")
    p.add_argument("--classpath-cache-dir", default=None)
    p = sub.add_parser("recount")
    p.add_argument("--before", required=True)
    args = ap.parse_args(argv)
    organized = Path(args.organized_dir)

    if args.cmd == "targets":
        Path(args.out).write_text(json.dumps([list(k) for k in exact_targets(load_best(organized))]))
        return 0
    if args.cmd == "census":
        best = load_best(organized)
        print(json.dumps({"population": len(best), "grades": grade_counts(best),
                          "targets": len(exact_targets(best)),
                          **{k: (v if k != "sets" else {",".join(s): n for s, n in sorted(v.items(), key=lambda x: -x[1])})
                             for k, v in rule_census(best).items()}}, indent=1))
        return 0
    if args.cmd == "snapshot":
        Path(args.out).write_text(json.dumps(_dump_best(load_best(organized))))
        return 0
    if args.cmd == "recount":
        before = {tuple(k.split("::", 1)): v for k, v in json.loads(Path(args.before).read_text()).items()}
        out = recount(before, load_best(organized))
        print(json.dumps({**out, "improved": len(out["improved"]), "regressed": out["regressed"]}, indent=1))
        return 1 if out["regressed"] or out["missing"] else 0
    cache = Path(args.classpath_cache_dir) if args.classpath_cache_dir else Path(tempfile.gettempdir()) / "n5-fidelity-classpath-cache"
    classpath = FID.build_classpath(cache, Path(FID.DEFAULT_MODULES_DIR), Path(FID.DEFAULT_BIN_EXT_DIR),
                                    jre_dir=Path(FID.DEFAULT_JRE_DIR))
    targets = by_module(json.loads(Path(args.targets).read_text()))
    failed = []

    def one(module: str) -> None:
        try:
            out = regrade_module(organized, module, targets[module], class_jobs=args.class_jobs,
                                 classpath=classpath, javac_bin=FID.DEFAULT_JAVAC, javap_bin=FID.DEFAULT_JAVAP,
                                 java_bin=FID.DEFAULT_JAVA, cfr_jar=FID.DEFAULT_CFR_JAR,
                                 procyon_jar=FID.DEFAULT_PROCYON_JAR, jd_cli_jar=None, tool_server=args.tool_server)
            print(f"[{module}] {out}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 -- one module must not abort the batch
            print(f"[{module}] FAILED: {exc!r}", file=sys.stderr, flush=True)
            failed.append(module)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        list(pool.map(one, sorted(targets)))
    FID.shutdown_tool_servers()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
