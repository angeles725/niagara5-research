#!/usr/bin/env python3
"""T25: per-class "best available representation" index for the niagara5-research corpus, so a
reader never has to know the source-precedence rule by heart -- see docs/writer-prompt.md
"Source precedence for code claims" (T20) for the prose version this tool makes mechanical.

Precedence, most faithful first:
  1. organized/docSource/<module>/<pkg>/<Class>.java     -- Tridium original source (byte-identical
                                                              recompile; B116).
  2. organized/_upstream-sources/.../<artifact>-sources.jar -- fetched upstream Maven Central source,
                                                              trusted as ground truth ONLY for classes
                                                              the manifest's own per-artifact identity
                                                              verdict (manifest.json's content_identity
                                                              / identification_method fields -- see
                                                              classify_upstream_identity) proves
                                                              byte-identical to the shipped binary jar:
                                                              a whole-jar SHA-1 match (identified-by-
                                                              sha1), resigned-identical (Niagara
                                                              re-signature only), or -- for a
                                                              partially-modified jar -- a class actually
                                                              in that jar's own identical set. An
                                                              unproven, vendor-modified, or
                                                              partially-modified-but-this-class-differs
                                                              artifact is demoted to `alternates` (kind
                                                              upstream-unproven / upstream-different-
                                                              build) and never used as `best` (fixed
                                                              2026-09-28, orchestrator-found defect:
                                                              org.eclipse.paho.client.mqttv3 1.2.5 is
                                                              vendor-rebuilt -- 0/110 classes byte-
                                                              identical to Central -- yet 96 of its
                                                              classes were being trusted as `upstream`
                                                              ground truth). Linked to a population by
                                                              jar sha256 first (population's own
                                                              extracted/.jar_sha256, or a raw jar's
                                                              direct hash, against the manifest
                                                              artifact's own binary_sha256 -- same hash
                                                              space, same physical jar) when both sides
                                                              have one; falls back to matching by class
                                                              name alone (the pre-existing, weaker
                                                              signal) when no sha256 link is available,
                                                              and the `reason` records which one applied.
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
  6. a BYTE-IDENTICAL jar decompiled as a DIFFERENT population (fixed 2026-09-28, orchestrator-
                                          found defect): when a population has none of the above
                                          for a class, but some other population's jar has the
                                          exact same sha256 (organized/<pop>/extracted/.jar_sha256,
                                          written at decompile time; a raw nested jar is hashed
                                          directly) and DOES decompile that class, use it -- never
                                          linked by filename/artifact-name alone, only by sha256.
                                          Real example: devkit bundles a raw, undecompiled LIB-INF
                                          copy of n-templates-5.0.54.9.2.jar AND separately
                                          decompiled that exact jar at organized/devkit/lib-inf/
                                          n-templates-5.0.54.9.2/ (also duplicated at organized/
                                          _etc-m2/n-templates-5.0.54.9.2/) -- the raw copy's classes
                                          are not actually undecompiled corpus-wide, just locally.
  7. missing -- no representation anywhere; still listed (never silently dropped).

Also recorded per class (not a precedence rung, purely informational):
  - line_mapped_view: organized/<pop>/vineflower-cons/... when it exists -- conservative,
    original-line-numbered / non-resugared decompile, useful for line-number or classic-syntax
    citations regardless of which rung was chosen as `best` (see B118 sec 118.1).

Corpus facts this tool encodes (verified 2026-09-28 against the real, read-only
/home/cristian/niagara5-research/organized; --organized always points there for the real run,
never the git-tracked worktree, which does not carry the gitignored corpus):
  - A "population" is any directory with a sibling extracted/ dir: every module
    (organized/<mod>/), every organized/_bin-ext/<jar>/, organized/_etc-m2/<jar>/,
    organized/_lib/<jar>/, organized/_lib-inf-3p/<jar-stem>-<sha256[:12]>/ (T26b:
    tools/n5-decompile.sh --third-party-libinf's dedup-by-sha256 decompile of every non-Tridium
    nested LIB-INF jar), and -- confirmed by inspection, ONE module only (devkit) --
    organized/<mod>/lib-inf/<jar>/, a genuine decompiled subtree (duplicates of etc/m2 build-tool
    jars devkit also bundles).
  - Every OTHER module's LIB-INF-nested third-party jars are raw, undecompiled files at
    organized/<mod>/extracted/LIB-INF/<jar>.jar (and duplicated raw under vineflower/,
    vineflower2/, etc.) -- there is usually no per-class decompile of that SPECIFIC copy in the
    corpus. This tool treats each such raw jar as its own population ("module-lib-inf-raw"),
    enumerating its classes straight from the jar's zip entries. Before falling through to
    upstream-sources coverage or `missing`, it first checks whether a byte-identical copy of the
    same jar (matched by sha256, never filename) was decompiled as some OTHER population -- see
    precedence rung 6 above; this really happens (devkit).
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
import hashlib
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
            "jar_name": stem,
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
                         "docsource_name": module_name, "jar_name": module_name})
        pops.extend(_raw_lib_inf_populations(entry, module_name))
        lib_inf_dir = entry / "lib-inf"
        if lib_inf_dir.is_dir():
            for sub in sorted(lib_inf_dir.iterdir()):
                if sub.is_dir() and _is_population_root(sub):
                    pops.append({"kind": "module-lib-inf", "name": f"{module_name}/lib-inf/{sub.name}",
                                 "root": sub, "docsource_name": None, "jar_name": sub.name})

    for base_name, kind in (("_bin-ext", "bin-ext"), ("_etc-m2", "etc-m2"), ("_lib", "lib"),
                            ("_lib-inf-3p", "lib-inf-3p")):
        base = organized_root / base_name
        if not base.is_dir():
            continue
        for sub in sorted(base.iterdir()):
            if sub.is_dir() and _is_population_root(sub):
                pops.append({"kind": kind, "name": f"{base_name}/{sub.name}", "root": sub,
                             "docsource_name": sub.name, "jar_name": sub.name})
                pops.extend(_raw_lib_inf_populations(sub, f"{base_name}/{sub.name}"))

    return pops


# ---------------------------------------------------------------------------
# Jar identity (sha256-only cross-population linking; never by filename).
# ---------------------------------------------------------------------------

def compute_jar_sha256(pop: dict) -> Optional[str]:
    """The identity of the jar this population's classes came from.

    Decompiled populations already have this written at decompile time
    (<root>/extracted/.jar_sha256); a raw (undecompiled) nested jar is hashed directly. Never
    derived from a filename/artifact name -- two same-named jars can differ in bytes (a different
    build or version), and two differently-named ones can be byte-identical."""
    if pop["kind"] == "module-lib-inf-raw":
        try:
            return hashlib.sha256(pop["jar_path"].read_bytes()).hexdigest()
        except OSError:
            return None
    root = pop.get("root")
    if root is None:
        return None
    sha_file = root / "extracted" / ".jar_sha256"
    if not sha_file.is_file():
        return None
    content = sha_file.read_text().strip()
    return content or None


def build_jar_identity_index(populations: list[dict]) -> dict[str, list[dict]]:
    """sha256 -> every DECOMPILED population whose jar has that sha256 (module-lib-inf-raw
    populations are never sources here -- they have no decompile of their own to offer)."""
    idx: dict[str, list[dict]] = {}
    for pop in populations:
        if pop["kind"] == "module-lib-inf-raw":
            continue
        sha256 = pop.get("jar_sha256")
        if not sha256:
            continue
        idx.setdefault(sha256, []).append(pop)
    return idx


def find_identical_jar_candidate(jar_identity_index: dict[str, list[dict]],
                                  own_sha256: Optional[str], own_pop_name: str, class_key: str):
    """Last-resort rung (6): this population has nothing of its own for class_key, but some OTHER
    population decompiled the exact same jar (by sha256) and DOES have it. Returns a
    (kind, path, grade, reason) candidate tuple, or None."""
    if not own_sha256:
        return None
    for other_pop in jar_identity_index.get(own_sha256, []):
        if other_pop["name"] == own_pop_name:
            continue
        other_root = other_pop.get("root")
        grade_v2 = other_pop.get("fidelity_v2", {}).get(class_key, {}).get("grade")
        grade_v1 = other_pop.get("fidelity_v1", {}).get(class_key, {}).get("grade")
        kind, path, grade, _reason = choose_decompile_rung(other_root, class_key, grade_v2, grade_v1)
        if kind is None:
            fb2 = find_rung_file(other_root, "fallback2", class_key)
            if fb2 is not None:
                kind, path, grade = "fallback2", fb2, None
            else:
                fb = find_rung_file(other_root, "fallback", class_key)
                if fb is not None:
                    kind, path, grade = "fallback", fb, None
        if kind is not None:
            reason = (f"identical jar {own_sha256[:12]} decompiled at {other_pop['name']} "
                      f"({kind})")
            return kind, path, grade, reason
    return None


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


def classify_upstream_identity(art: dict) -> dict:
    """Whether one manifest.json artifact record proves its fetched Maven SOURCES are byte-
    identical to the SHIPPED BINARY jar it was matched against -- i.e. whether it can be trusted
    as ground truth for any/all of its classes (2026-09-28 fix, orchestrator-found defect: this
    tool used to trust every "status": "fetched" artifact unconditionally, so a vendor-rebuilt jar
    like org.eclipse.paho.client.mqttv3 1.2.5 -- 0/110 classes byte-identical to Central -- was
    marked `best_kind: upstream` for 96 of its classes).

    tools/n5-upstream-sources.py writes one of these identity signals per artifact, most reliable
    first:
      - art["content_identity"]["status"] == "resigned-identical": every .class entry matched
        Central byte-for-byte (only non-class entries, e.g. Niagara's added signature, differ) --
        proven for the WHOLE jar.
      - art["content_identity"]["status"] == "partially-modified": only SOME classes matched;
        content_identity["different_classes"] / ["local_only_classes"] list the ones that did NOT
        -- everything else in the jar is proven, per class (see _class_trusted).
      - art["content_identity"]["status"] in {"vendor-modified", "no-classes", "unverifiable"}:
        not proven for any class.
      - art["identification_method"] set with NO "content_identity" key at all: T26a's
        identify_unidentified_entry returned "identified-by-sha1" -- the ONLY T26a outcome that
        skips writing content_identity -- meaning the whole local BINARY jar's SHA-1 matched
        Central's directly (the strongest possible proof: a whole-jar SHA-1 match).
      - neither field present (the original ~154 pom.properties-identified artifacts that were
        never rechecked -- either because evidence/b117 already recorded a whole-jar SHA-1 "exact"
        match, which manifest.json does not carry forward as an explicit field, or because no
        matching evidence record was found at all): the manifest itself carries NO identity
        verdict for this artifact, so it is treated as NOT proven (`verdict` "no-verdict") --
        conservative by design, and visible in the index summary's `upstream_unproven_artifacts`
        rather than silently assumed correct.

    Returns {"trust": "whole" | "partial" | "none", "verdict": <short label>, "reason": <human
    text>, "different_classes": set[str] (partial only), "local_only_classes": set[str] (partial
    only)} -- entries are full in-jar paths with .class extension (matching content_identity's own
    lists), e.g. "com/foo/Bar.class" or "com/foo/Bar$Inner.class"."""
    ci = art.get("content_identity")
    if ci is not None:
        status = ci.get("status")
        if status == "resigned-identical":
            return {"trust": "whole", "verdict": status,
                    "reason": "content_identity=resigned-identical (every class byte-identical to "
                              "Central; only non-class entries, e.g. Niagara's added signature, "
                              "differ)"}
        if status == "partially-modified":
            return {"trust": "partial", "verdict": status,
                    "different_classes": set(ci.get("different_classes") or []),
                    "local_only_classes": set(ci.get("local_only_classes") or []),
                    "reason": "content_identity=partially-modified (only this jar's own per-class "
                              "byte-identical matches are trusted)"}
        return {"trust": "none", "verdict": status or "unknown",
                "reason": f"content_identity={status} (not proven byte-identical to the shipped jar)"}
    if art.get("identification_method") and art.get("status") == "fetched":
        return {"trust": "whole", "verdict": "identified-by-sha1",
                "reason": f"identification_method={art['identification_method']} "
                          "(whole shipped binary jar's SHA-1 matched Central directly)"}
    return {"trust": "none", "verdict": "no-verdict",
            "reason": "no identity verdict recorded in manifest.json for this artifact (no "
                      "content_identity, no identification_method) -- not proven byte-identical "
                      "to the shipped jar"}


def _class_trusted(verdict: dict, class_key: str) -> bool:
    """Per-class trust decision given one classify_upstream_identity() verdict."""
    if verdict["trust"] == "whole":
        return True
    if verdict["trust"] == "partial":
        entry = class_key + ".class"
        return (entry not in verdict["different_classes"]
                and entry not in verdict["local_only_classes"])
    return False


def build_upstream_index(organized_root: Path):
    """Returns (name_index, sha_index, artifact_verdict_counts):
      - name_index: class_key -> candidate dict, for every class name a fetched upstream sources
        jar actually covers (per its own recorded classdiff); first match wins on a name collision
        across artifacts (pre-existing, weaker signal -- a name match alone never proves THIS
        population's own jar is the identity-verified one).
      - sha_index: manifest artifact binary_sha256 -> {class_key: candidate dict}, for artifacts
        that recorded one (set by n5-upstream-sources.py's classdiff step). A population whose own
        jar_sha256 (extracted/.jar_sha256, or a raw jar hashed directly) equals an artifact's
        binary_sha256 is DEFINITELY that artifact's own shipped jar -- both sides are SHA-256 of
        the same physical jar bytes, so this is a real, filename-independent join key (see
        find_upstream_candidate), preferred over the name-only index when available.
      - artifact_verdict_counts: classify_upstream_identity()["verdict"] -> count of "fetched"
        artifacts, e.g. {"no-verdict": 81, "resigned-identical": 95, ...} -- feeds the index
        summary's `upstream_unproven_artifacts` (the "no-verdict" count).

    Each candidate dict: {groupId, artifactId, version, jar_path, entry, trusted (bool),
    verdict (str), reason (str)}."""
    manifest_path = organized_root / "_upstream-sources" / "manifest.json"
    if not manifest_path.is_file():
        return {}, {}, {}
    try:
        manifest = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}, {}, {}

    name_index: dict[str, dict] = {}
    sha_index: dict[str, dict[str, dict]] = {}
    verdict_counts: dict[str, int] = {}
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
        verdict = classify_upstream_identity(art)
        verdict_counts[verdict["verdict"]] = verdict_counts.get(verdict["verdict"], 0) + 1
        binary_sha256 = art.get("binary_sha256")
        by_class_for_this_artifact: dict[str, dict] = {}
        for name in covered:
            if not _is_portable_class_name(name):
                continue
            candidate = {
                "groupId": art["groupId"], "artifactId": art["artifactId"],
                "version": art["version"], "jar_path": jar_path, "entry": name + ".java",
                "trusted": _class_trusted(verdict, name), "verdict": verdict["verdict"],
                "reason": verdict["reason"],
            }
            by_class_for_this_artifact[name] = candidate
            if name not in name_index:
                name_index[name] = candidate
        if binary_sha256:
            sha_index.setdefault(binary_sha256, {}).update(by_class_for_this_artifact)
    return name_index, sha_index, verdict_counts


def find_upstream_candidate(pop: dict, class_key: str, name_index: dict, sha_index: dict):
    """The upstream candidate (if any) for one population's class, plus how it was linked.

    Prefers a jar-sha256 link (this population's own jar IS the exact jar the manifest artifact's
    identity verdict was computed against -- never a name coincidence) over the weaker class-name-
    only index. Returns None if neither index covers this class."""
    jar_sha256 = pop.get("jar_sha256")
    if jar_sha256 and jar_sha256 in sha_index and class_key in sha_index[jar_sha256]:
        cand = dict(sha_index[jar_sha256][class_key])
        cand["link"] = (f"population jar sha256 {jar_sha256[:12]} matches manifest artifact "
                         f"{cand['groupId']}:{cand['artifactId']}:{cand['version']}'s own "
                         "binary_sha256 (same physical jar)")
        return cand
    if class_key in name_index:
        cand = dict(name_index[class_key])
        cand["link"] = ("matched by class name only (no jar-sha256 link between this population's "
                         "jar and a manifest artifact)")
        return cand
    return None


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
                        upstream_index, extract_dir: Path,
                        jar_identity_index: Optional[dict] = None) -> dict:
    """`upstream_index` is the (name_index, sha_index) tuple build_upstream_index() returns."""
    pop_root = pop.get("root")
    fidelity_v2 = pop.get("fidelity_v2") or {}
    fidelity_v1 = pop.get("fidelity_v1") or {}
    grade_v2 = fidelity_v2.get(class_key, {}).get("grade")
    grade_v1 = fidelity_v1.get(class_key, {}).get("grade")

    name_index, sha_index = upstream_index

    ds_file = find_docsource_file(organized_root, pop.get("docsource_name"), class_key)
    up_candidate = find_upstream_candidate(pop, class_key, name_index, sha_index)
    decompile_kind, decompile_file, decompile_grade, decompile_reason = choose_decompile_rung(
        pop_root, class_key, grade_v2, grade_v1)
    fb2_file = find_rung_file(pop_root, "fallback2", class_key)
    fb_file = find_rung_file(pop_root, "fallback", class_key)
    cons_file = find_rung_file(pop_root, "vineflower-cons", class_key)

    candidates = []
    if ds_file is not None:
        candidates.append(("docSource", ds_file, None, "Tridium original source (docSource)"))
    if up_candidate is not None and up_candidate["trusted"]:
        candidates.append(("upstream", None, None,
                           f"upstream Maven sources jar match, proven byte-identical -- "
                           f"{up_candidate['reason']} [{up_candidate['link']}]"))
    if decompile_kind is not None:
        candidates.append((decompile_kind, decompile_file, decompile_grade, decompile_reason))
    if fb2_file is not None:
        candidates.append(("fallback2", fb2_file, None,
                           "CFR fallback2 (vineflower/vineflower2 produced no output for this class)"))
    if fb_file is not None:
        candidates.append(("fallback", fb_file, None,
                           "legacy CFR fallback (vineflower/vineflower2/fallback2 produced no output)"))

    if not candidates and jar_identity_index:
        identical = find_identical_jar_candidate(
            jar_identity_index, pop.get("jar_sha256"), pop["name"], class_key)
        if identical is not None:
            candidates.append(identical)

    alternates = []
    if not candidates:
        best_kind, best_path, grade, reason = "missing", None, None, (
            "no docSource, proven-identical upstream, vineflower2, vineflower, fallback2, "
            "fallback or identical-jar-elsewhere representation found for this class"
        )
    else:
        best_kind, best_path_raw, grade, reason = candidates[0]
        if best_kind == "upstream":
            best_path = extract_upstream_file(up_candidate, extract_dir, class_key)
        else:
            best_path = best_path_raw
        for kind, path, alt_grade, _reason in candidates[1:]:
            if kind == "upstream":
                gav = f"{up_candidate['groupId']}:{up_candidate['artifactId']}:{up_candidate['version']}"
                alternates.append({"kind": kind, "path": f"upstream:{gav}:{class_key}.java",
                                   "grade": alt_grade})
            else:
                alternates.append({"kind": kind, "path": _rel(organized_root, path),
                                   "grade": alt_grade})

    # Not proven byte-identical (vendor-modified / unverifiable / no-classes / this class differs
    # in a partially-modified jar / no identity verdict recorded at all): never used as `best`
    # (see classify_upstream_identity), but still recorded, never silently dropped -- a reader
    # investigating this class should see the upstream file existed and why it wasn't trusted.
    if up_candidate is not None and not up_candidate["trusted"]:
        gav = f"{up_candidate['groupId']}:{up_candidate['artifactId']}:{up_candidate['version']}"
        alt_kind = ("upstream-unproven" if up_candidate["verdict"] == "no-verdict"
                    else "upstream-different-build")
        alternates.append({
            "kind": alt_kind, "path": f"upstream:{gav}:{class_key}.java", "grade": None,
            "reason": f"{up_candidate['reason']} [{up_candidate['link']}]",
        })

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
    name_index, sha_index, upstream_verdict_counts = build_upstream_index(organized_root)
    upstream_index = (name_index, sha_index)

    # Enrich every population BEFORE building any class record: the jar-identity index (rung 6)
    # needs every population's fidelity grades and jar_sha256 available up front, since a class
    # missing from population A may be resolved by looking at population B's own data.
    enriched: list[dict] = []
    for pop in populations:
        pop = dict(pop)
        pop["fidelity_v2"] = load_fidelity(pop.get("root"), "vineflower2")
        pop["fidelity_v1"] = load_fidelity(pop.get("root"), "vineflower")
        pop["jar_sha256"] = compute_jar_sha256(pop)
        enriched.append(pop)
    jar_identity_index = build_jar_identity_index(enriched)
    jar_name_by_pop_name = {p["name"]: p.get("jar_name", p["name"]) for p in enriched}

    records = []
    for pop in enriched:
        for class_key in enumerate_classes(pop):
            records.append(build_class_record(organized_root, pop, class_key, upstream_index,
                                               extract_dir, jar_identity_index))

    by_best_kind: dict[str, int] = {}
    by_population: dict[str, int] = {}
    missing_by_jar_counts: dict[str, int] = {}
    for rec in records:
        by_best_kind[rec["best_kind"]] = by_best_kind.get(rec["best_kind"], 0) + 1
        by_population[rec["module"]] = by_population.get(rec["module"], 0) + 1
        if rec["best_kind"] == "missing":
            jar_name = jar_name_by_pop_name.get(rec["module"], rec["module"])
            missing_by_jar_counts[jar_name] = missing_by_jar_counts.get(jar_name, 0) + 1

    missing_by_jar = sorted(
        ({"jar": jar, "count": count} for jar, count in missing_by_jar_counts.items()),
        key=lambda e: (-e["count"], e["jar"]),
    )

    summary = {
        "total_classes": len(records),
        "total_populations": len(populations),
        "by_best_kind": by_best_kind,
        "by_population": by_population,
        "missing_count": by_best_kind.get("missing", 0),
        "missing_by_jar": missing_by_jar,
        # "no-verdict" fetched upstream artifacts (organized/_upstream-sources/manifest.json has
        # neither content_identity nor identification_method for them) -- treated as NOT proven,
        # never used as `best`, per classify_upstream_identity(). Visible here rather than silently
        # assumed correct (2026-09-28 fix).
        "upstream_unproven_artifacts": upstream_verdict_counts.get("no-verdict", 0),
        "upstream_artifact_verdicts": upstream_verdict_counts,
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
    print(f"upstream_unproven_artifacts: {s.get('upstream_unproven_artifacts', 0)}")


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
