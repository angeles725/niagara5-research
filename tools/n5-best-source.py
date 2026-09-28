#!/usr/bin/env python3
"""T25: per-class "best available representation" index for the niagara5-research corpus, so a
reader never has to know the source-precedence rule by heart -- see docs/writer-prompt.md
"Source precedence for code claims" (T20) for the prose version this tool makes mechanical.

Precedence, most faithful first:
  1. organized/docSource/<module>/<pkg>/<Class>.java     -- Tridium original source (byte-identical
                                                              recompile; B116).
  2. organized/_upstream-sources/.../<artifact>-sources.jar -- fetched upstream Maven Central source
                                                              for a byte-identical/vendor-resigned
                                                              third-party jar (B117/T22), for classes
                                                              its classdiff actually covers.
  3. organized/<pop>/vineflower2/...  -- v2 decompile (recommended tree; docs/decompile-fidelity-
                                          report.md).
  4. organized/<pop>/vineflower/...   -- v1 decompile. Preferred over v2 only when BOTH are graded
                                          (organized/<pop>/fidelity.vineflower2.json /
                                          fidelity.vineflower.json) and v1's grade outranks v2's,
                                          per the same ordering tools/n5-fidelity.py's _GRADE_RANK
                                          uses (no-compile/timeout/harness-error < compiles-mismatch/
                                          bytecode-only < roundtrip-equivalent < roundtrip-exact).
  5. organized/<pop>/fallback2/... then fallback/...  -- CFR fallback (only ever populated for the
                                          specific classes vineflower/vineflower2 failed to produce).
  6. missing -- no representation anywhere; still listed (never silently dropped).

Also recorded per class (not a precedence rung, purely informational):
  - line_mapped_view: organized/<pop>/vineflower-cons/... when it exists -- conservative,
    original-line-numbered / non-resugared decompile, useful for line-number or classic-syntax
    citations regardless of which rung was chosen as `best` (see B118 sec 118.1).

Corpus facts this tool encodes (verified 2026-09-28 against the real, read-only
/home/cristian/niagara5-research/organized; --organized always points there for the real run,
never the git-tracked worktree, which does not carry the gitignored corpus):
  - A "population" is any directory with a sibling extracted/ dir: every module
    (organized/<mod>/), every organized/_bin-ext/<jar>/, organized/_etc-m2/<jar>/,
    organized/_lib/<jar>/, and -- confirmed by inspection, ONE module only (devkit) --
    organized/<mod>/lib-inf/<jar>/, a genuine decompiled subtree (duplicates of etc/m2 build-tool
    jars devkit also bundles).
  - Every OTHER module's LIB-INF-nested third-party jars are raw, undecompiled files at
    organized/<mod>/extracted/LIB-INF/<jar>.jar (and duplicated raw under vineflower/,
    vineflower2/, etc.) -- there is no per-class decompile of them in the corpus at all. This
    tool treats each such raw jar as its own population ("module-lib-inf-raw"), enumerating its
    classes straight from the jar's zip entries; without upstream-sources coverage, those classes
    are correctly `missing`, not silently absent from the index.
  - Nested classes (Outer$Inner.class) are excluded from population enumeration; their source
    lives in Outer's own file.
  - Some _etc-m2 populations' decompilers wrote `.kt` instead of `.java` (Kotlin sources); every
    rung lookup tries both extensions.
  - fidelity.vineflower2.json / fidelity.vineflower.json exist only for a minority of modules
    (46 of 247+ populations as of 2026-09-28) -- grading is opt-in, `grade` is null elsewhere.

Design note on `--materialize`: an "upstream" pick lives inside a zipped `-sources.jar`, which
cannot be symlinked to directly. This tool extracts the matched .java entry once into
`<out>/_upstream-extracted/<groupId>/<artifactId>/<version>/<class>.java` (idempotent, cached) and
treats *that* real file as the `best` path -- so materialize's own job stays exactly what the task
asked for: symlink-only, no copies, at materialize time.

Subcommand-free CLI: this always runs the full index build (see main()).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ORGANIZED = REPO_ROOT / "organized"
DEFAULT_OUT = None  # resolved relative to --organized at call time (organized/_best)

# Same ordering as tools/n5-fidelity.py's _GRADE_RANK (kept independent/inline: this tool only
# READS already-graded JSON, it never grades anything itself, so it does not import that module).
GRADE_RANK = {
    "no-compile": 0,
    "timeout": 0,
    "harness-error": 0,
    "compiles-mismatch": 1,
    "bytecode-only": 1,
    "roundtrip-equivalent": 2,
    "roundtrip-exact": 3,
}

RUNG_EXTENSIONS = (".java", ".kt")

# Per-compilation-unit descriptor files: every module/artifact has its OWN module-info.java /
# package-info.java, with completely different content, yet they all share this exact filename.
# Matching them by name across artifacts (like any other class) would silently swap in an
# unrelated artifact's descriptor -- observed for real on the first full-corpus run (2026-09-28):
# aaphp's module-info was matched to org.eclipse.angus:jakarta.mail's module-info.java, which is
# jakarta.mail's own module declaration, not aaphp's. These names are excluded from the upstream
# cross-artifact index entirely; classes with these names always fall through to the decompile
# rungs (correct: they are genuinely no-representation-in-source-form-elsewhere classes).
_NON_PORTABLE_CLASS_NAMES = {"module-info", "package-info"}


def _is_portable_class_name(class_key: str) -> bool:
    simple = class_key.rsplit("/", 1)[-1]
    return simple not in _NON_PORTABLE_CLASS_NAMES


# ---------------------------------------------------------------------------
# Population discovery.
# ---------------------------------------------------------------------------

def _is_population_root(d: Path) -> bool:
    return (d / "extracted").is_dir()


def _raw_lib_inf_populations(module_dir: Path, module_name: str) -> list[dict]:
    """Raw (undecompiled) nested LIB-INF jars living at <module>/extracted/LIB-INF/*.jar."""
    out = []
    lib_inf_dir = module_dir / "extracted" / "LIB-INF"
    if not lib_inf_dir.is_dir():
        return out
    for jar in sorted(lib_inf_dir.glob("*.jar")):
        stem = jar.name[:-4] if jar.name.endswith(".jar") else jar.name
        out.append({
            "kind": "module-lib-inf-raw",
            "name": f"{module_name}/lib-inf-raw/{stem}",
            "root": None,
            "jar_path": jar,
            "docsource_name": None,
        })
    return out


def discover_populations(organized_root: Path) -> list[dict]:
    """Every population in the corpus: modules, _bin-ext/_etc-m2/_lib jars, module/lib-inf/<jar>
    decompiled subtrees, and raw (undecompiled) module/extracted/LIB-INF/<jar>.jar nested jars."""
    pops: list[dict] = []
    if not organized_root.is_dir():
        return pops

    for entry in sorted(organized_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_") or entry.name == "docSource":
            continue
        module_name = entry.name
        if _is_population_root(entry):
            pops.append({"kind": "module", "name": module_name, "root": entry,
                         "docsource_name": module_name})
        pops.extend(_raw_lib_inf_populations(entry, module_name))
        lib_inf_dir = entry / "lib-inf"
        if lib_inf_dir.is_dir():
            for sub in sorted(lib_inf_dir.iterdir()):
                if sub.is_dir() and _is_population_root(sub):
                    pops.append({"kind": "module-lib-inf", "name": f"{module_name}/lib-inf/{sub.name}",
                                 "root": sub, "docsource_name": None})

    for base_name, kind in (("_bin-ext", "bin-ext"), ("_etc-m2", "etc-m2"), ("_lib", "lib")):
        base = organized_root / base_name
        if not base.is_dir():
            continue
        for sub in sorted(base.iterdir()):
            if sub.is_dir() and _is_population_root(sub):
                pops.append({"kind": kind, "name": f"{base_name}/{sub.name}", "root": sub,
                             "docsource_name": sub.name})
                pops.extend(_raw_lib_inf_populations(sub, f"{base_name}/{sub.name}"))

    return pops


# ---------------------------------------------------------------------------
# Class enumeration.
# ---------------------------------------------------------------------------

def _is_nested(simple_name: str) -> bool:
    return "$" in simple_name


def enumerate_classes(pop: dict) -> list[str]:
    """Top-level class keys (slash form, no extension) for one population."""
    if pop["kind"] == "module-lib-inf-raw":
        jar_path: Path = pop["jar_path"]
        names = []
        try:
            with zipfile.ZipFile(jar_path) as zf:
                for n in zf.namelist():
                    if not n.endswith(".class"):
                        continue
                    base = n[: -len(".class")]
                    simple = base.rsplit("/", 1)[-1]
                    if _is_nested(simple):
                        continue
                    names.append(base)
        except (zipfile.BadZipFile, OSError):
            return []
        return sorted(set(names))

    root = pop["root"]
    extracted = root / "extracted"
    if not extracted.is_dir():
        return []
    names = []
    for class_file in extracted.rglob("*.class"):
        rel = class_file.relative_to(extracted)
        simple = rel.name[: -len(".class")]
        if _is_nested(simple):
            continue
        key = rel.with_suffix("").as_posix()
        names.append(key)
    return sorted(set(names))


# ---------------------------------------------------------------------------
# Rung file lookups.
# ---------------------------------------------------------------------------

def find_rung_file(pop_root: Optional[Path], rung_dir: str, class_key: str) -> Optional[Path]:
    if pop_root is None:
        return None
    for ext in RUNG_EXTENSIONS:
        p = pop_root / rung_dir / (class_key + ext)
        if p.is_file():
            return p
    return None


def find_docsource_file(organized_root: Path, docsource_name: Optional[str],
                         class_key: str) -> Optional[Path]:
    if not docsource_name:
        return None
    for ext in RUNG_EXTENSIONS:
        p = organized_root / "docSource" / docsource_name / (class_key + ext)
        if p.is_file():
            return p
    return None


def load_fidelity(pop_root: Optional[Path], variant: str) -> dict:
    """Returns fidelity.<variant>.json's "classes" dict, or {} if absent/unreadable."""
    if pop_root is None:
        return {}
    path = pop_root / f"fidelity.{variant}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}
    return data.get("classes", {})


def choose_decompile_rung(pop_root: Optional[Path], class_key: str,
                           grade_v2: Optional[str], grade_v1: Optional[str]):
    """Returns (kind, path, grade, reason) for the best of vineflower2/vineflower, or
    (None, None, None, None) if neither has a file for this class."""
    v2_file = find_rung_file(pop_root, "vineflower2", class_key)
    v1_file = find_rung_file(pop_root, "vineflower", class_key)
    if v2_file and v1_file and grade_v2 is not None and grade_v1 is not None:
        rank_v2 = GRADE_RANK.get(grade_v2, -1)
        rank_v1 = GRADE_RANK.get(grade_v1, -1)
        if rank_v1 > rank_v2:
            reason = (f"vineflower (v1) graded {grade_v1} outranks vineflower2 (v2) graded "
                      f"{grade_v2} (grader ordering); v1 preferred for this class")
            return "vineflower", v1_file, grade_v1, reason
    if v2_file:
        return "vineflower2", v2_file, grade_v2, "vineflower2 available (default precedence)"
    if v1_file:
        return "vineflower", v1_file, grade_v1, "vineflower2 missing; vineflower (v1) available"
    return None, None, None, None


# ---------------------------------------------------------------------------
# Upstream (third-party original source) index.
# ---------------------------------------------------------------------------

def _resolve_repo_relative(organized_root: Path, stored_path: str) -> Path:
    """manifest.json paths are stored relative to the REPO ROOT of whatever checkout produced
    them (e.g. "organized/_upstream-sources/..."). Resolve them against the *given* --organized
    root, not a hardcoded REPO_ROOT, so this tool works against any corpus checkout."""
    norm = stored_path.replace("\\", "/")
    if norm.startswith("organized/"):
        return organized_root / norm[len("organized/"):]
    return organized_root.parent / norm


def build_upstream_index(organized_root: Path) -> dict[str, dict]:
    """class_key -> {groupId, artifactId, version, jar_path, entry} for every class name a
    fetched upstream sources jar actually covers (per its own recorded classdiff), first match
    wins on a name collision across artifacts."""
    manifest_path = organized_root / "_upstream-sources" / "manifest.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

    index: dict[str, dict] = {}
    for art in manifest.get("artifacts", []):
        if art.get("status") != "fetched":
            continue
        sources_jar_path = art.get("sources_jar_path")
        if not sources_jar_path:
            continue
        jar_path = _resolve_repo_relative(organized_root, sources_jar_path)
        if not jar_path.is_file():
            continue
        sources_only = set(art.get("classdiff", {}).get("sources_only", []))
        try:
            with zipfile.ZipFile(jar_path) as zf:
                java_names = {n[: -len(".java")] for n in zf.namelist() if n.endswith(".java")}
        except (zipfile.BadZipFile, OSError):
            continue
        covered = java_names - sources_only
        for name in covered:
            if not _is_portable_class_name(name):
                continue
            if name in index:
                continue
            index[name] = {
                "groupId": art["groupId"], "artifactId": art["artifactId"],
                "version": art["version"], "jar_path": jar_path, "entry": name + ".java",
            }
    return index


def extract_upstream_file(info: dict, extract_dir: Path, class_key: str) -> Optional[Path]:
    dest = extract_dir / info["groupId"] / info["artifactId"] / info["version"] / (class_key + ".java")
    if dest.is_file():
        return dest
    try:
        with zipfile.ZipFile(info["jar_path"]) as zf:
            data = zf.read(info["entry"])
    except (zipfile.BadZipFile, KeyError, OSError):
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


# ---------------------------------------------------------------------------
# Per-class record assembly.
# ---------------------------------------------------------------------------

def _rel(organized_root: Path, path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    try:
        return "organized/" + path.relative_to(organized_root).as_posix()
    except ValueError:
        return path.as_posix()


def build_class_record(organized_root: Path, pop: dict, class_key: str,
                        upstream_index: dict, extract_dir: Path) -> dict:
    pop_root = pop.get("root")
    fidelity_v2 = pop.get("fidelity_v2") or {}
    fidelity_v1 = pop.get("fidelity_v1") or {}
    grade_v2 = fidelity_v2.get(class_key, {}).get("grade")
    grade_v1 = fidelity_v1.get(class_key, {}).get("grade")

    ds_file = find_docsource_file(organized_root, pop.get("docsource_name"), class_key)
    up_info = upstream_index.get(class_key)
    decompile_kind, decompile_file, decompile_grade, decompile_reason = choose_decompile_rung(
        pop_root, class_key, grade_v2, grade_v1)
    fb2_file = find_rung_file(pop_root, "fallback2", class_key)
    fb_file = find_rung_file(pop_root, "fallback", class_key)
    cons_file = find_rung_file(pop_root, "vineflower-cons", class_key)

    candidates = []
    if ds_file is not None:
        candidates.append(("docSource", ds_file, None, "Tridium original source (docSource)"))
    if up_info is not None:
        candidates.append(("upstream", None, None, "upstream Maven sources jar match"))
    if decompile_kind is not None:
        candidates.append((decompile_kind, decompile_file, decompile_grade, decompile_reason))
    if fb2_file is not None:
        candidates.append(("fallback2", fb2_file, None,
                           "CFR fallback2 (vineflower/vineflower2 produced no output for this class)"))
    if fb_file is not None:
        candidates.append(("fallback", fb_file, None,
                           "legacy CFR fallback (vineflower/vineflower2/fallback2 produced no output)"))

    alternates = []
    if not candidates:
        best_kind, best_path, grade, reason = "missing", None, None, (
            "no docSource, upstream, vineflower2, vineflower, fallback2 or fallback "
            "representation found for this class"
        )
    else:
        best_kind, best_path_raw, grade, reason = candidates[0]
        if best_kind == "upstream":
            best_path = extract_upstream_file(up_info, extract_dir, class_key)
        else:
            best_path = best_path_raw
        for kind, path, alt_grade, _reason in candidates[1:]:
            if kind == "upstream":
                gav = f"{up_info['groupId']}:{up_info['artifactId']}:{up_info['version']}"
                alternates.append({"kind": kind, "path": f"upstream:{gav}:{class_key}.java",
                                   "grade": alt_grade})
            else:
                alternates.append({"kind": kind, "path": _rel(organized_root, path),
                                   "grade": alt_grade})

    return {
        "module": pop["name"],
        "class": class_key,
        "best": _rel(organized_root, best_path),
        "best_kind": best_kind,
        "reason": reason,
        "line_mapped_view": _rel(organized_root, cons_file),
        "alternates": alternates,
        "grade": grade,
    }


# ---------------------------------------------------------------------------
# Index build + summary + materialize.
# ---------------------------------------------------------------------------

def build_index(organized_root: Path, extract_dir: Path) -> dict:
    populations = discover_populations(organized_root)
    upstream_index = build_upstream_index(organized_root)

    records = []
    for pop in populations:
        pop = dict(pop)
        pop["fidelity_v2"] = load_fidelity(pop.get("root"), "vineflower2")
        pop["fidelity_v1"] = load_fidelity(pop.get("root"), "vineflower")
        for class_key in enumerate_classes(pop):
            records.append(build_class_record(organized_root, pop, class_key, upstream_index,
                                               extract_dir))

    by_best_kind: dict[str, int] = {}
    by_population: dict[str, int] = {}
    for rec in records:
        by_best_kind[rec["best_kind"]] = by_best_kind.get(rec["best_kind"], 0) + 1
        by_population[rec["module"]] = by_population.get(rec["module"], 0) + 1

    summary = {
        "total_classes": len(records),
        "total_populations": len(populations),
        "by_best_kind": by_best_kind,
        "by_population": by_population,
        "missing_count": by_best_kind.get("missing", 0),
    }
    return {"schema_version": 1, "summary": summary, "classes": records}


def materialize(organized_root: Path, materialize_dir: Path, records: list[dict]) -> int:
    """Idempotent RELATIVE symlink tree DIR/<module>/<pkg>/<Class>.<ext> -> the chosen `best`
    file. Extension matches the actual source file (.java or .kt), not forced to .java, since a
    .java symlink pointing at Kotlin content would misrepresent the file for any reader/editor."""
    linked = 0
    for rec in records:
        if rec["best_kind"] == "missing" or not rec["best"]:
            continue
        best_rel = rec["best"]
        assert best_rel.startswith("organized/")
        target_abs = organized_root / best_rel[len("organized/"):]
        ext = target_abs.suffix
        link_path = materialize_dir / rec["module"] / (rec["class"] + ext)
        link_path.parent.mkdir(parents=True, exist_ok=True)
        rel_target = os.path.relpath(target_abs, start=link_path.parent)
        if link_path.is_symlink() or link_path.exists():
            try:
                if link_path.is_symlink() and os.readlink(link_path) == rel_target:
                    linked += 1
                    continue
            except OSError:
                pass
            link_path.unlink()
        os.symlink(rel_target, link_path)
        linked += 1
    return linked


def print_human_summary(index: dict) -> None:
    s = index["summary"]
    print(f"populations: {s['total_populations']}")
    print(f"classes: {s['total_classes']}")
    print(f"missing: {s['missing_count']}")
    print("by best_kind:")
    for kind in sorted(s["by_best_kind"]):
        print(f"  {kind}: {s['by_best_kind'][kind]}")


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--organized", default=str(DEFAULT_ORGANIZED),
                   help="corpus organized/ root (default: repo_root/organized)")
    p.add_argument("--out", default=None,
                   help="output dir for best-source.json (default: <organized>/_best)")
    p.add_argument("--materialize", default=None,
                   help="optional dir to create a browsable relative-symlink tree in")
    args = p.parse_args(argv)

    organized_root = Path(args.organized).resolve()
    out_dir = Path(args.out).resolve() if args.out else organized_root / "_best"
    out_dir.mkdir(parents=True, exist_ok=True)
    extract_dir = out_dir / "_upstream-extracted"

    index = build_index(organized_root, extract_dir)
    index_path = out_dir / "best-source.json"
    index_path.write_text(json.dumps(index, indent=1))

    if args.materialize:
        materialize_dir = Path(args.materialize).resolve()
        materialize_dir.mkdir(parents=True, exist_ok=True)
        materialize(organized_root, materialize_dir, index["classes"])

    print_human_summary(index)
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
