#!/usr/bin/env python3
"""n5-vineflower-variants.py -- per-flag Vineflower decompile variants of chosen classes (C3d).

The primary decompile (vineflower2) fixes one flag set. A method that only matches the shipped
bytecode under another Vineflower behaviour (`--incorporate-returns=false`, `--pattern-matching=false`,
`--remove-getclass=false`, ...) is recovered by decompiling the class again with that one flag changed
and letting tools/n5-splice-methods.py take the method from that tree (`--donor-trees vf2v-<variant>`).
Nothing here judges fidelity: the splice recompiles and compares.

Writes organized/<module>/vf2v-<variant>/<package>/<Class>.java for the classes of the targets file
(`[[module, fqcn], ...]`; nested `Outer$X.class` files are staged with the outer so Vineflower resolves
them). The flag set is the v2 one of tools/n5-decompile.sh plus the variant's single change; the
library context is the jar mirror + the v2 libcache, `-e=` last (Vineflower drops later flags).

Usage:
  python3 tools/n5-vineflower-variants.py --targets t.json --variants ir0,pm0,rg0 --jobs 4
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import glob
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORGANIZED_DIR = REPO_ROOT / "organized"
DEFAULT_VINEFLOWER = REPO_ROOT / "tools" / "decompilers" / "vineflower-1.12.0.jar"
DEFAULT_JAVA = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/java"
DEFAULT_JDK_HOME = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec"
DEFAULT_MIRROR = Path("/home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28")
TIMEOUT_SECONDS = 420

# the v2 flag set of tools/n5-decompile.sh (V2_FLAG_NAMES/V2_FLAG_VALUES)
BASE_FLAGS = [
    "--log-level=error", "--thread-count=4", "--use-lvt-names=true", "--use-method-parameters=true",
    "--decompile-generics=true", "--decompile-assert=true", "--rename-members=false",
    "--decompile-complex-constant-dynamic=false", "--ignore-invalid-bytecode=false",
    "--dump-bytecode-on-error=true", "--decompiler-comments=true"]

# variant name -> the one flag it changes
VARIANTS = {
    "base": [],
    "ss0": ["--simplify-stack=false"],
    "ir0": ["--incorporate-returns=false"],
    "vm": ["--verify-merges=true"],
    "tif0": ["--ternary-in-if=false"],
    "pi0": ["--prettify-ifs=false"],
    "tcs": ["--ternary-constant-simplification=true"],
    "bai0": ["--boolean-as-int=false"],
    "pm0": ["--pattern-matching=false"],
    "se0": ["--decompile-switch-expressions=false"],
    "isl0": ["--inline-simple-lambdas=false"],
    "tlf0": ["--try-loop-fix=false"],
    "df0": ["--decompile-finally=false"],
    "ens0": ["--ensure-synchronized-monitors=false"],
    "rg0": ["--remove-getclass=false"],
}


def build_command(variant: str, in_dir: Path, out_dir: Path, libs: list, *, java: str = DEFAULT_JAVA,
                  vineflower: str = str(DEFAULT_VINEFLOWER), jdk_home: str = DEFAULT_JDK_HOME) -> list:
    """The Vineflower command line of one variant; KeyError for an unknown variant."""
    flags = VARIANTS[variant]
    return [java, "-Xmx4g", "-jar", str(vineflower), *BASE_FLAGS, f"--include-runtime={jdk_home}", *flags,
            "-e=" + ",".join(libs), str(in_dir), str(out_dir)]


def load_targets(path: Path) -> dict:
    by_module: dict = collections.defaultdict(list)
    for module, fqcn in json.loads(Path(path).read_text()):
        by_module[module].append(fqcn)
    return {m: sorted(v) for m, v in sorted(by_module.items())}


def stage_classes(mod_dir: Path, fqcns: list, stage: Path) -> None:
    """Copy each class and its `Outer$*.class` files from organized/<mod>/extracted into `stage`."""
    for fqcn in fqcns:
        src = Path(mod_dir) / "extracted" / f"{fqcn}.class"
        dst = stage / f"{fqcn}.class"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        for nested in sorted(src.parent.glob(src.stem + "$*.class")):
            shutil.copy(nested, dst.parent / nested.name)


def library_jars(mirror: Path, organized: Path) -> list:
    return sorted(glob.glob(str(mirror / "modules" / "*.jar"))
                  + glob.glob(str(mirror / "bin-ext" / "**" / "*.jar"), recursive=True)
                  + glob.glob(str(organized / "_v2-libcache" / "*.jar")))


def run_variant(variant: str, module: str, fqcns: list, organized: Path, libs: list, *, java: str, vineflower: str,
                jdk_home: str) -> tuple:
    """(variant, module, returncode or "timeout", .java files written)."""
    mod_dir = organized / module
    tree = mod_dir / f"vf2v-{variant}"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix=f"n5vv-{module}-") as td:
        stage = Path(td) / "in"
        stage_classes(mod_dir, fqcns, stage)
        cmd = build_command(variant, stage, tree, libs, java=java, vineflower=vineflower, jdk_home=jdk_home)
        try:
            rc: object = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS).returncode
        except subprocess.TimeoutExpired:
            rc = "timeout"
    return variant, module, rc, sum(1 for _ in tree.rglob("*.java"))


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--targets", required=True, help="JSON file: [[module, fqcn], ...]")
    ap.add_argument("--variants", required=True, help=f"comma-separated, of: {', '.join(VARIANTS)}")
    ap.add_argument("--organized-dir", default=str(DEFAULT_ORGANIZED_DIR))
    ap.add_argument("--mirror-dir", default=str(DEFAULT_MIRROR), help="sha256-verified jar mirror (modules/, bin-ext/)")
    ap.add_argument("--java", default=DEFAULT_JAVA)
    ap.add_argument("--vineflower", default=str(DEFAULT_VINEFLOWER))
    ap.add_argument("--jdk-home", default=DEFAULT_JDK_HOME)
    ap.add_argument("--jobs", type=int, default=4)
    args = ap.parse_args(argv)
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    unknown = [v for v in variants if v not in VARIANTS]
    if unknown:
        ap.error(f"unknown variant {unknown}; known: {sorted(VARIANTS)}")
    organized = Path(args.organized_dir)
    libs = library_jars(Path(args.mirror_dir), organized)
    targets = load_targets(Path(args.targets))
    jobs = [(v, m) for v in variants for m in targets]
    failed = 0

    def one(job):
        v, m = job
        return run_variant(v, m, targets[m], organized, libs, java=args.java, vineflower=args.vineflower,
                           jdk_home=args.jdk_home)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        for variant, module, rc, n in pool.map(one, jobs):
            print(f"[{module}] {variant}: rc={rc} files={n}", file=sys.stderr, flush=True)
            failed += rc not in (0,)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
