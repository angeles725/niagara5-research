#!/usr/bin/env bash
# n5-decompile.sh — decompile Niagara N5 modules into organized/<module>/
#
# Usage:
#   tools/n5-decompile.sh                 # decompile every jar in $N5_MODULES_DIR
#   tools/n5-decompile.sh <name>.jar      # decompile one module (name with or without .jar)
#   tools/n5-decompile.sh --docsource     # only extract docSource.jar (original .java sources)
#   tools/n5-decompile.sh --bin-ext       # decompile the Tridium-owned jars under bin/ext/
#   tools/n5-decompile.sh --force <name>  # ignore the sha256 cache, redo it
#   tools/n5-decompile.sh --variant v2 <name>   # v2: same module, WITH library context
#   tools/n5-decompile.sh --variant v2 --all    # v2 over every module jar (see below)
#   tools/n5-decompile.sh --variant v2 --bin-ext [<name>]  # v2 over included bin/ext jar(s)
#
# --variant v2: a second decompile, alongside (not instead of) the plain v1 run in
# vineflower/+fallback/, writing organized/<mod>/vineflower2/ (+fallback2/). v1 runs
# Vineflower with NO library context at all — no --add-external for the other N5 jars,
# no --include-runtime — so the decompiler has to *guess* every generic type argument,
# cast target, and overload resolution from bytecode alone (this bake-off's own earlier
# "Vineflower +lib ctx" timing experiment used only the 247 module jars, no bin/ext, no
# LIB-INF, and was measured for time only, not fidelity — see docs/decompiler-bakeoff.md).
# v2 gives Vineflower the full picture instead: every OTHER N5 module jar, every jar
# under bin/ext/, every already-extracted LIB-INF jar (embedded third-party libs some
# modules ship inside their own jar, e.g. jodaTime's joda-time-2.14.3.jar), and the real
# JDK 25 runtime — so a type like `List<BComponent>` or an overload target resolves to
# what it actually is instead of an inferred guess. v2 never writes into or deletes
# vineflower/ or fallback/ (v1's trees); v1 and v2 are meant to be diffed, not swapped.
# --variant v2 requires an explicit <name> or --all — unlike the v1 default (no args =
# full run), a bare `--variant v2` is a usage error, so an omitted argument can never
# silently trigger the full ~250-module library-context run by accident.
#
# Undocumented Vineflower 1.12.0 CLI ordering requirement (verified empirically
# 2026-09-28, not documented anywhere in --help): an "Additional option" such as
# --include-runtime or --use-lvt-names placed AFTER a "General option" such as
# -e/--add-external is silently dropped — Vineflower logs `warn: missing
# '--include-runtime=...', ignored` and treats the flag text as a bogus positional
# source file, with exit code 0 and no other indication anything was wrong. Every
# Additional option must precede -e/--add-external on the command line for it to take
# effect; decompile_module_v2 below relies on this order and the v2 bats tests assert
# the log carries zero "warn: missing" lines as a regression guard.
#
# Environment overrides (all optional):
#   N5_MODULES_DIR   default: /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules
#   N5_BIN_EXT_DIR   default: /mnt/c/Program Files/Niagara/5.0.0.28/bin/ext
#   N5_OUT_DIR       default: <repo>/organized
#   N5_JAVA          default: /home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java
#   N5_VINEFLOWER    default: <repo>/tools/decompilers/vineflower-1.12.0.jar
#   N5_CFR           default: <repo>/tools/decompilers/cfr-0.152.jar
#   N5_PRIMARY_TIMEOUT   default: 240 (seconds, whole-jar primary decompile budget)
#   N5_PARALLELISM   default: 6 (used only as documentation for callers driving xargs -P)
#   N5_JDK25_HOME    default: /home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec
#                    (--variant v2 only) passed to Vineflower's --include-runtime. Must be
#                    a real JDK home containing lib/modules (the jrt image), NOT just a
#                    `java` binary's directory — Homebrew's keg-only openjdk@25 formula
#                    symlinks bin/include/etc under opt/openjdk@25 itself but the actual
#                    JDK home (with lib/modules) is one level down, at opt/openjdk@25/libexec.
#                    Passing opt/openjdk@25 itself crashes Vineflower with a NullPointerException
#                    in JrtFinder.addRuntime (verified empirically 2026-09-28).
# --bin-ext: the 247 module jars are not the whole N5 install — bin/ext/ carries
# ~109 more jars the daemon/tools load at runtime, most of them third-party
# libraries (Jetty, BouncyCastle under bcfips/bcstd, Kotlin stdlib, ASM, JNA/JNR,
# OkHttp, ...). Only the Tridium-owned ones are worth decompiling here; the skip
# rule is in tools/n5-classify-binext.py (>50% of a jar's classes under
# com/tridium/, niagara/, or javax/baja/ => include). On the real bin/ext/ tree
# that rule is not a close call: every jar came back ~0% or >=67% Tridium, so the
# threshold has wide margin. Included jars land in organized/_bin-ext/<jar-stem>/
# with the same extracted/resources/vineflower/fallback/recon.json layout as a
# module (write_recon's docSource-coverage lookup is a no-op for these — they are
# not modules docSource.jar indexes by name).
#
# Primary decompiler: Vineflower (best Java 17-25 SYNTAX fidelity: records, sealed
# classes, switch pattern matching resugar correctly — see docs/decompiler-bakeoff.md).
# This is syntax fidelity, not semantic fidelity: B116 (niagara5-block116.md) found 11
# confirmed semantic defects in 36,977 recompiled methods (0.030%) — dropped casts/
# boxing that rebind an overload, varargs array-length loss, float/double ternary
# widening, and instanceof-pattern resugaring that turns a local into a field
# reference. Any corpus claim about behavior that depends on overload binding,
# boxing, numeric conversion, `finally` control flow, or local-vs-field identity MUST
# be confirmed with javap or a docSource original, not read off the decompiled text —
# see niagara5-block116.md and docs/decompiler-bakeoff.md's "Semantic defects (B116)".
# Fallback: CFR, used for a whole module when Vineflower times out or exits non-zero
# (observed on this corpus: Vineflower 1.12.0 hangs indefinitely on bajaui.jar's
# com.tridium.ui.* subtree; CFR decompiles the same jar in ~11s), and per-class when
# Vineflower completes but leaves an explicit decompiler-failure marker in a handful of
# files. CFR is not a semantic oracle either (B116: it drops `(Object)null` casts).
#
# Idempotent: skips a module whose jar sha256 matches organized/<module>/recon.json's
# recorded sha256, unless --force is given. Parallel-safe: every module writes only
# to its own organized/<module>/ subtree and its own organized/_logs/<module>.log;
# safe to drive with `find ... | xargs -P N tools/n5-decompile.sh`.
#
# Vendor filter (modules/ only, not bin/ext/): every jar processed from
# $N5_MODULES_DIR — whether named explicitly or picked up by the bulk run — is
# skipped unless its own META-INF/module.xml declares vendor="Tridium". This
# excludes non-Tridium jars that don't belong in a real N5 install (found in this
# corpus: n5Hello.jar vendor="poc", ColdRoomPan-rt.jar vendor="Angeles" — both
# locally-built PoC/N4 jars, not part of the 247 real Tridium-shipped modules).
# Every exclusion is logged. bin/ext/ jars have no module.xml and are filtered by
# tools/n5-classify-binext.py instead (package-namespace based, see --bin-ext).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

N5_MODULES_DIR="${N5_MODULES_DIR:-/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules}"
N5_BIN_EXT_DIR="${N5_BIN_EXT_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext}"
N5_OUT_DIR="${N5_OUT_DIR:-$REPO_ROOT/organized}"
N5_JAVA="${N5_JAVA:-/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java}"
N5_VINEFLOWER="${N5_VINEFLOWER:-$REPO_ROOT/tools/decompilers/vineflower-1.12.0.jar}"
N5_CFR="${N5_CFR:-$REPO_ROOT/tools/decompilers/cfr-0.152.jar}"
N5_PRIMARY_TIMEOUT="${N5_PRIMARY_TIMEOUT:-240}"
N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}"

LOG_DIR="$N5_OUT_DIR/_logs"
mkdir -p "$LOG_DIR"

log() {
  # $1 = module name, rest = message
  local mod="$1"; shift
  printf '[%s] %s %s\n' "$(date -u +%FT%TZ)" "$mod" "$*" | tee -a "$LOG_DIR/$mod.log" >/dev/null
}

sha256_of() {
  sha256sum "$1" | awk '{print $1}'
}

# A module jar is in scope only if its own META-INF/module.xml declares
# vendor="Tridium". The N5 modules dir is meant to hold only Tridium-shipped
# modules, but two locally-built PoC jars (n5Hello.jar, vendor="poc";
# ColdRoomPan-rt.jar, vendor="Angeles" — this repo's own prior N4 work,
# accidentally installed into the N5 runtime by a local build) were found
# sitting alongside the real 247 during this run. Every one of the other 247
# jars declares vendor="Tridium" with no exceptions, so this is a clean,
# unambiguous filter, not a guess.
module_vendor() {
  unzip -p "$1" META-INF/module.xml 2>/dev/null | grep -io 'vendor="[^"]*"' | head -1 \
    | sed -E 's/^vendor="//; s/"$//'
}

is_tridium_module() {
  local vendor
  vendor="$(module_vendor "$1")"
  [[ "$vendor" == "Tridium" ]]
}

# ---------------------------------------------------------------------------
# docSource.jar — original Tridium sources, highest fidelity reference
# ---------------------------------------------------------------------------
extract_docsource() {
  local jar="$N5_MODULES_DIR/docSource.jar"
  local out="$N5_OUT_DIR/docSource"
  if [[ ! -f "$jar" ]]; then
    echo "docSource.jar not found at $jar" >&2
    return 1
  fi
  local sha; sha="$(sha256_of "$jar")"
  local marker="$out/.sha256"
  if [[ -f "$marker" ]] && [[ "$(cat "$marker")" == "$sha" ]]; then
    log docSource "up to date (sha256 $sha), skipping"
    return 0
  fi
  rm -rf "$out"
  mkdir -p "$out"
  unzip -o -q "$jar" -d "$out"
  echo "$sha" > "$marker"
  log docSource "extracted $(find "$out" -name '*.java' | wc -l) .java files"
}

# ---------------------------------------------------------------------------
# recon.json — lightweight structural facts about one module jar
# ---------------------------------------------------------------------------
write_recon() {
  local module="$1" jar="$2" moddir="$3" primary_status="$4" primary_time="$5" \
        fallback_used="$6" fallback_reason="$7" class_count="$8"
  local sha; sha="$(sha256_of "$jar")"

  local signed="false" sig_name="null"
  local sf_file
  sf_file="$(find "$moddir/extracted/META-INF" -maxdepth 1 -name '*.SF' 2>/dev/null | head -1 || true)"
  if [[ -n "$sf_file" ]]; then
    signed="true"
    sig_name="\"$(basename "$sf_file")\""
  fi

  # major-version histogram + obfuscation heuristic + docSource coverage, via python3
  # (small, precise binary parsing beats a bash/awk reimplementation here)
  python3 "$SCRIPT_DIR/n5-recon-helper.py" \
    --module "$module" \
    --jar "$jar" \
    --sha256 "$sha" \
    --extracted "$moddir/extracted" \
    --docsource "$N5_OUT_DIR/docSource/$module" \
    --signed "$signed" \
    --sig-name "$sig_name" \
    --primary-status "$primary_status" \
    --primary-time "$primary_time" \
    --fallback-used "$fallback_used" \
    --fallback-reason "$fallback_reason" \
    --out "$moddir/recon.json"
}

# ---------------------------------------------------------------------------
# decompile one module jar
# ---------------------------------------------------------------------------
decompile_module() {
  local jar="$1"
  local module; module="$(basename "$jar" .jar)"
  local force="${2:-false}"
  local moddir="${3:-$N5_OUT_DIR/$module}"

  local sha; sha="$(sha256_of "$jar")"
  if [[ "$force" != "true" ]] && [[ -f "$moddir/recon.json" ]]; then
    local prev_sha
    prev_sha="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('jar_sha256',''))" "$moddir/recon.json" 2>/dev/null || true)"
    if [[ "$prev_sha" == "$sha" ]]; then
      log "$module" "up to date (sha256 $sha), skipping"
      return 0
    fi
  fi

  mkdir -p "$moddir/extracted" "$moddir/resources" "$moddir/vineflower"
  log "$module" "extracting $jar"
  rm -rf "${moddir:?}/extracted"
  mkdir -p "$moddir/extracted"
  unzip -o -q "$jar" -d "$moddir/extracted"

  # resources/ = a copy of every non-.class file (module.xml, lexicons, .properties,
  # .xml, images, etc.) so a reader doesn't have to wade through the class tree.
  rm -rf "${moddir:?}/resources"
  mkdir -p "$moddir/resources"
  ( cd "$moddir/extracted" && find . -type f ! -name '*.class' -print0 ) \
    | while IFS= read -r -d '' f; do
        mkdir -p "$moddir/resources/$(dirname "$f")"
        cp "$moddir/extracted/$f" "$moddir/resources/$f"
      done

  local class_count
  class_count="$(find "$moddir/extracted" -name '*.class' | wc -l)"

  # --- primary: Vineflower, whole jar, bounded timeout ---
  rm -rf "${moddir:?}/vineflower"
  mkdir -p "$moddir/vineflower"
  log "$module" "primary(vineflower) starting on $class_count classes"
  local t0 t1 primary_time primary_status
  t0="$(date +%s)"
  if timeout "$N5_PRIMARY_TIMEOUT" "$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error \
      "$jar" "$moddir/vineflower" >> "$LOG_DIR/$module.log" 2>&1; then
    primary_status="ok"
  else
    local rc=$?
    if [[ $rc -eq 124 ]]; then
      primary_status="timeout"
    else
      primary_status="error"
    fi
  fi
  t1="$(date +%s)"
  primary_time=$(( t1 - t0 ))
  log "$module" "primary(vineflower) status=$primary_status time=${primary_time}s"

  local fallback_used="false" fallback_reason="none"
  local produced
  produced="$(find "$moddir/vineflower" -name '*.java' | wc -l)"

  if [[ "$primary_status" != "ok" ]] || [[ "$produced" -eq 0 && "$class_count" -gt 0 ]]; then
    # whole-jar fallback to CFR — primary either failed outright or hung with zero output
    fallback_used="true"
    fallback_reason="primary_${primary_status}_whole_module"
    log "$module" "fallback(cfr) whole-module reason=$fallback_reason"
    mkdir -p "$moddir/fallback"
    "$N5_JAVA" -jar "$N5_CFR" "$jar" --outputdir "$moddir/fallback" --silent true \
      >> "$LOG_DIR/$module.log" 2>&1 || log "$module" "fallback(cfr) also failed"
  else
    # primary produced output for the whole jar; scan for the decompiler's own
    # failure markers (not application log strings) and re-run just those classes
    # through CFR into fallback/.
    local marker_files
    marker_files="$(scan_marker_files "$moddir/vineflower")"
    if [[ -n "$marker_files" ]]; then
      fallback_used="true"
      fallback_reason="per_class_decompiler_marker"
      mkdir -p "$moddir/fallback"
      local n=0
      while IFS= read -r javafile; do
        [[ -z "$javafile" ]] && continue
        local rel="${javafile#"$moddir"/vineflower/}"
        local classrel="${rel%.java}.class"
        local classfile="$moddir/extracted/$classrel"
        if [[ -f "$classfile" ]]; then
          "$N5_JAVA" -jar "$N5_CFR" "$classfile" --outputdir "$moddir/fallback" --silent true \
            >> "$LOG_DIR/$module.log" 2>&1 || true
          n=$((n+1))
        fi
      done <<< "$marker_files"
      log "$module" "fallback(cfr) per-class reran $n classes flagged by primary"
    fi
  fi

  write_recon "$module" "$jar" "$moddir" "$primary_status" "$primary_time" \
    "$fallback_used" "$fallback_reason" "$class_count"
  log "$module" "done"
}

# ---------------------------------------------------------------------------
# bin/ext/ — Tridium-owned jars that ship outside modules/ (see usage header)
# ---------------------------------------------------------------------------
decompile_binext() {
  local force="${1:-false}"
  local out_root="$N5_OUT_DIR/_bin-ext"
  mkdir -p "$out_root"

  local jar module verdict included=0 skipped=0
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_bin-ext.log" || true)"
    if [[ "$verdict" == include* ]]; then
      log "_bin-ext" "including $module ($verdict)"
      decompile_module "$jar" "$force" "$out_root/$module"
      included=$((included + 1))
    else
      log "_bin-ext" "skipping $module ($verdict)"
      skipped=$((skipped + 1))
    fi
  done < <(find "$N5_BIN_EXT_DIR" -name '*.jar' -print0)

  log "_bin-ext" "done: included=$included skipped=$skipped"
}

# ---------------------------------------------------------------------------
# --variant v2 — same modules, WITH library context (see header comment)
# ---------------------------------------------------------------------------

# Populates global array V2_ALL_LIB_JARS with every jar to offer Vineflower as
# external library context: every jar in $N5_MODULES_DIR except docSource.jar
# (a sources-only jar, not compiled classes — useless and potentially confusing
# as a class-resolution source), every jar under $N5_BIN_EXT_DIR (all of it, not
# just the six classified "Tridium-owned" by n5-classify-binext.py — that rule
# picks which jars are worth *decompiling*, a different question from which
# jars help *resolve types* while decompiling something else; third-party libs
# like Jetty/Jackson under bin/ext are exactly the kind of thing a module's
# generics/casts may reference), and every already-extracted LIB-INF/*.jar
# found under $N5_OUT_DIR (embedded third-party libs some modules ship inside
# their own jar's LIB-INF/, e.g. jodaTime's joda-time-2.14.3.jar). No caching
# beyond one process invocation: this is a `find`-only scan (no unzip/vendor
# inspection), verified fast (a few hundred ms for ~450 entries).
compute_v2_library_jars() {
  V2_ALL_LIB_JARS=()
  local jar
  while IFS= read -r -d '' jar; do
    [[ "$(basename "$jar" .jar)" == "docSource" ]] && continue
    V2_ALL_LIB_JARS+=("$jar")
  done < <(find "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0)
  while IFS= read -r -d '' jar; do
    V2_ALL_LIB_JARS+=("$jar")
  done < <(find "$N5_BIN_EXT_DIR" -name '*.jar' -print0 2>/dev/null)
  while IFS= read -r -d '' jar; do
    V2_ALL_LIB_JARS+=("$jar")
  done < <(find "$N5_OUT_DIR" -path '*/extracted/LIB-INF/*.jar' -print0 2>/dev/null)
}

# Builds V2_LIB_CSV (comma-joined, for Vineflower -e=) and V2_LIB_COLON
# (colon-joined, for CFR --extraclasspath) from V2_ALL_LIB_JARS, excluding the
# one jar given (the module currently being decompiled — it must never appear
# in its own library-context list). Also sets V2_LIB_COUNT.
build_v2_external_lists() {
  local exclude="$1"
  local csv="" colon="" count=0
  local p
  for p in "${V2_ALL_LIB_JARS[@]}"; do
    [[ "$p" == "$exclude" ]] && continue
    csv="${csv:+$csv,}$p"
    colon="${colon:+$colon:}$p"
    count=$((count + 1))
  done
  V2_LIB_CSV="$csv"
  V2_LIB_COLON="$colon"
  V2_LIB_COUNT="$count"
}

# v1's decompile_module always re-extracts unconditionally (safe there: it's
# only reached after an sha256 mismatch already proved the extraction is
# stale). v2 shares the same organized/<mod>/extracted/ and resources/ trees
# as v1 rather than keeping a second copy, so it must NOT blindly wipe them —
# reuse them if a prior run (v1 or v2) already populated them, extract only if
# missing/empty or --force.
ensure_extracted_for_v2() {
  local jar="$1" moddir="$2" force="$3" module="$4"
  local need_extract="false"
  if [[ "$force" == "true" ]]; then
    need_extract="true"
  elif [[ ! -d "$moddir/extracted" ]]; then
    need_extract="true"
  elif [[ -z "$(find "$moddir/extracted" -name '*.class' -print -quit 2>/dev/null)" ]]; then
    need_extract="true"
  fi

  if [[ "$need_extract" != "true" ]]; then
    log "$module" "v2 reusing existing extracted/+resources/ (from a prior run)"
    return 0
  fi

  mkdir -p "$moddir/extracted" "$moddir/resources"
  log "$module" "v2 extracting $jar (no existing extracted/ found, or --force)"
  rm -rf "${moddir:?}/extracted"
  mkdir -p "$moddir/extracted"
  unzip -o -q "$jar" -d "$moddir/extracted"

  rm -rf "${moddir:?}/resources"
  mkdir -p "$moddir/resources"
  ( cd "$moddir/extracted" && find . -type f ! -name '*.class' -print0 ) \
    | while IFS= read -r -d '' f; do
        mkdir -p "$moddir/resources/$(dirname "$f")"
        cp "$moddir/extracted/$f" "$moddir/resources/$f"
      done
}

# Merges a "v2" sub-object into organized/<mod>/recon.json, leaving every v1
# top-level field untouched (recon.json may not exist yet if v2 is run on a
# module that never went through v1 — in that case a minimal file is created).
#
# KNOWN INTERACTION (pre-existing, not introduced by v2): v1's write_recon
# (tools/n5-recon-helper.py) always fully overwrites recon.json — it has no
# concept of a "v2" key to preserve. So `tools/n5-decompile.sh --force <mod>`
# (v1) run AFTER a --variant v2 run silently drops that module's "v2"
# sub-object. If both v1 --force and v2 data are needed for the same module,
# rerun --variant v2 again afterward to re-merge it.
write_recon_v2() {
  local module="$1" moddir="$2" sha="$3" primary_status="$4" primary_time="$5" \
        fallback_used="$6" fallback_reason="$7"
  local vf_sha cfr_sha
  vf_sha="$(sha256_of "$N5_VINEFLOWER")"
  cfr_sha="$(sha256_of "$N5_CFR")"
  local markers
  markers="$(scan_marker_files "$moddir/vineflower2" | wc -l | tr -d ' ')"
  local fallback_used_py="False"
  [[ "$fallback_used" == "true" ]] && fallback_used_py="True"

  python3 - "$moddir/recon.json" <<PYEOF
import json, sys

path = sys.argv[1]
try:
    with open(path) as fh:
        recon = json.load(fh)
except (OSError, json.JSONDecodeError):
    recon = {"module": "$module"}

recon["v2"] = {
    "variant": "v2",
    "jar_sha256": "$sha",
    "vineflower_version": "vineflower-1.12.0",
    "vineflower_sha256": "$vf_sha",
    "cfr_version": "cfr-0.152",
    "cfr_sha256": "$cfr_sha",
    "add_external_count": $V2_LIB_COUNT,
    "include_runtime": "$N5_JDK25_HOME",
    "flags": {
        "use_lvt_names": True,
        "use_method_parameters": True,
        "decompile_generics": True,
        "decompile_assert": True,
        "rename_members": False,
        "decompile_complex_constant_dynamic": False,
        "ignore_invalid_bytecode": False,
        "dump_bytecode_on_error": True,
        "decompiler_comments": True,
    },
    "primary_status": "$primary_status",
    "primary_time_seconds": int("$primary_time"),
    "fallback_used": $fallback_used_py,
    "fallback_reason": "$fallback_reason",
    "decompile_failure_markers": $markers,
}

with open(path, "w") as fh:
    json.dump(recon, fh, indent=2)
    fh.write("\n")
PYEOF
}

decompile_module_v2() {
  local jar="$1"
  local module; module="$(basename "$jar" .jar)"
  local force="${2:-false}"
  local moddir="${3:-$N5_OUT_DIR/$module}"

  local sha; sha="$(sha256_of "$jar")"
  if [[ "$force" != "true" ]] && [[ -f "$moddir/recon.json" ]]; then
    local prev_sha
    prev_sha="$(python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
print(d.get('v2', {}).get('jar_sha256', ''))
" "$moddir/recon.json" 2>/dev/null || true)"
    if [[ "$prev_sha" == "$sha" ]]; then
      log "$module" "v2 up to date (sha256 $sha), skipping"
      return 0
    fi
  fi

  mkdir -p "$moddir"
  ensure_extracted_for_v2 "$jar" "$moddir" "$force" "$module"

  local class_count
  class_count="$(find "$moddir/extracted" -name '*.class' | wc -l)"

  compute_v2_library_jars
  build_v2_external_lists "$jar"

  rm -rf "${moddir:?}/vineflower2"
  mkdir -p "$moddir/vineflower2"
  log "$module" "v2 primary(vineflower) starting on $class_count classes (lib_count=$V2_LIB_COUNT, runtime=$N5_JDK25_HOME)"

  # Additional options MUST precede -e/--add-external — see the header comment's
  # "Undocumented Vineflower 1.12.0 CLI ordering requirement".
  local vf2_cmd=(
    "$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error
    --include-runtime="$N5_JDK25_HOME"
    --use-lvt-names=true
    --use-method-parameters=true
    --decompile-generics=true
    --decompile-assert=true
    --rename-members=false
    --decompile-complex-constant-dynamic=false
    --ignore-invalid-bytecode=false
    --dump-bytecode-on-error=true
    --decompiler-comments=true
    -e="$V2_LIB_CSV"
    "$jar" "$moddir/vineflower2"
  )
  { printf 'CMD:'; printf ' %q' "${vf2_cmd[@]}"; printf '\n'; } >> "$LOG_DIR/$module.v2.log"

  local t0 t1 primary_time primary_status
  t0="$(date +%s)"
  if timeout "$N5_PRIMARY_TIMEOUT" "${vf2_cmd[@]}" >> "$LOG_DIR/$module.v2.log" 2>&1; then
    primary_status="ok"
  else
    local rc=$?
    if [[ $rc -eq 124 ]]; then
      primary_status="timeout"
    else
      primary_status="error"
    fi
  fi
  t1="$(date +%s)"
  primary_time=$(( t1 - t0 ))
  log "$module" "v2 primary(vineflower) status=$primary_status time=${primary_time}s"

  local fallback_used="false" fallback_reason="none"
  local produced
  produced="$(find "$moddir/vineflower2" -name '*.java' | wc -l)"

  if [[ "$primary_status" != "ok" ]] || [[ "$produced" -eq 0 && "$class_count" -gt 0 ]]; then
    fallback_used="true"
    fallback_reason="primary_${primary_status}_whole_module"
    log "$module" "v2 fallback(cfr) whole-module reason=$fallback_reason"
    mkdir -p "$moddir/fallback2"
    local cfr2_cmd=("$N5_JAVA" -jar "$N5_CFR" "$jar" --outputdir "$moddir/fallback2" --silent true --extraclasspath "$V2_LIB_COLON")
    { printf 'CMD:'; printf ' %q' "${cfr2_cmd[@]}"; printf '\n'; } >> "$LOG_DIR/$module.v2.log"
    "${cfr2_cmd[@]}" >> "$LOG_DIR/$module.v2.log" 2>&1 || log "$module" "v2 fallback(cfr) also failed"
  else
    local marker_files
    marker_files="$(scan_marker_files "$moddir/vineflower2")"
    if [[ -n "$marker_files" ]]; then
      fallback_used="true"
      fallback_reason="per_class_decompiler_marker"
      mkdir -p "$moddir/fallback2"
      local n=0
      while IFS= read -r javafile; do
        [[ -z "$javafile" ]] && continue
        local rel="${javafile#"$moddir"/vineflower2/}"
        local classrel="${rel%.java}.class"
        local classfile="$moddir/extracted/$classrel"
        if [[ -f "$classfile" ]]; then
          local cfr2c_cmd=("$N5_JAVA" -jar "$N5_CFR" "$classfile" --outputdir "$moddir/fallback2" --silent true --extraclasspath "$V2_LIB_COLON")
          { printf 'CMD:'; printf ' %q' "${cfr2c_cmd[@]}"; printf '\n'; } >> "$LOG_DIR/$module.v2.log"
          "${cfr2c_cmd[@]}" >> "$LOG_DIR/$module.v2.log" 2>&1 || true
          n=$((n+1))
        fi
      done <<< "$marker_files"
      log "$module" "v2 fallback(cfr) per-class reran $n classes flagged by primary"
    fi
  fi

  write_recon_v2 "$module" "$moddir" "$sha" "$primary_status" "$primary_time" \
    "$fallback_used" "$fallback_reason"
  log "$module" "v2 done"
}

run_v2_all_modules() {
  local force="$1"
  local excluded=0 jar module
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    if [[ "$module" == "docSource" ]]; then
      continue
    fi
    if ! is_tridium_module "$jar"; then
      log "$module" "v2 EXCLUDED: module.xml vendor=\"$(module_vendor "$jar")\" (not \"Tridium\"), skipping"
      excluded=$((excluded + 1))
      continue
    fi
    decompile_module_v2 "$jar" "$force"
  done < <(find "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0)
  log "_full-run" "v2 vendor filter: excluded $excluded non-Tridium jar(s) from $N5_MODULES_DIR"
}

run_v2_binext() {
  local force="$1" only="$2"
  local out_root="$N5_OUT_DIR/_bin-ext"
  mkdir -p "$out_root"

  if [[ -n "$only" && "$only" != "--all" ]]; then
    only="${only%.jar}"
    local jar
    jar="$(find "$N5_BIN_EXT_DIR" -name "$only.jar" -print -quit 2>/dev/null)"
    if [[ -z "$jar" ]]; then
      echo "no such bin/ext jar: $only.jar under $N5_BIN_EXT_DIR" >&2
      return 1
    fi
    local verdict
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_bin-ext.log" || true)"
    if [[ "$verdict" != include* ]]; then
      log "_bin-ext" "v2 skipping $only ($verdict)"
      return 0
    fi
    decompile_module_v2 "$jar" "$force" "$out_root/$only"
    return 0
  fi

  local jar module verdict included=0 skipped=0
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_bin-ext.log" || true)"
    if [[ "$verdict" == include* ]]; then
      log "_bin-ext" "v2 including $module ($verdict)"
      decompile_module_v2 "$jar" "$force" "$out_root/$module"
      included=$((included + 1))
    else
      log "_bin-ext" "v2 skipping $module ($verdict)"
      skipped=$((skipped + 1))
    fi
  done < <(find "$N5_BIN_EXT_DIR" -name '*.jar' -print0)
  log "_bin-ext" "v2 done: included=$included skipped=$skipped"
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
# Print the .java files under $1 that carry a decompiler failure marker.
# Vineflower writes "// $VF: Couldn't be decompiled" INDENTED inside the method
# body, so the pattern must allow leading whitespace (an anchored '^// ' missed
# andoverAC256/backup — niagara5-block30.md B30-G2).
scan_marker_files() {
  # shellcheck disable=SC2016  # '$VF:' is a literal Vineflower marker, not an expansion
  grep -rlE '^[[:space:]]*// \$VF: |Unable to fully decompile class|COULD NOT DECOMPILE|<unknown>' \
    "$1" 2>/dev/null || true
}

main() {
  local force="false"
  local only=""
  local mode="modules"
  local variant=""

  # Parse every flag before acting, so order (--force --bin-ext vs --bin-ext
  # --force) never changes behavior.
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --scan-markers)
        scan_marker_files "${2:?--scan-markers needs a directory}"
        exit 0
        ;;
      --docsource)
        mode="docsource"
        shift
        ;;
      --bin-ext)
        mode="bin-ext"
        shift
        ;;
      --force)
        force="true"
        shift
        ;;
      --variant)
        variant="${2:?--variant needs a value (only v2 is implemented)}"
        shift 2
        ;;
      --all)
        only="--all"
        shift
        ;;
      *)
        only="$1"
        shift
        ;;
    esac
  done

  mkdir -p "$N5_OUT_DIR"

  if [[ -n "$variant" ]]; then
    if [[ "$variant" != "v2" ]]; then
      echo "unsupported --variant '$variant' (only 'v2' is implemented)" >&2
      exit 1
    fi
    if [[ "$mode" == "docsource" ]]; then
      echo "--variant v2 does not apply to --docsource (docSource.jar is original sources, not decompiled)" >&2
      exit 1
    fi
    if [[ "$mode" == "bin-ext" ]]; then
      run_v2_binext "$force" "$only"
      exit $?
    fi
    if [[ -z "$only" ]]; then
      echo "--variant v2 needs an explicit <module> or --all: tools/n5-decompile.sh --variant v2 [<module>|--all]" >&2
      exit 1
    fi
    if [[ "$only" == "--all" ]]; then
      run_v2_all_modules "$force"
      exit 0
    fi
    only="${only%.jar}"
    local v2_jar="$N5_MODULES_DIR/$only.jar"
    if [[ ! -f "$v2_jar" ]]; then
      echo "no such module jar: $v2_jar" >&2
      exit 1
    fi
    if ! is_tridium_module "$v2_jar"; then
      log "$only" "v2 EXCLUDED: module.xml vendor=\"$(module_vendor "$v2_jar")\" (not \"Tridium\") — not a real N5-shipped module, skipping"
      exit 0
    fi
    decompile_module_v2 "$v2_jar" "$force"
    exit 0
  fi

  if [[ "$mode" == "docsource" ]]; then
    extract_docsource
    exit 0
  fi

  if [[ "$mode" == "bin-ext" ]]; then
    decompile_binext "$force"
    exit 0
  fi

  if [[ -n "$only" ]]; then
    only="${only%.jar}"
    if [[ "$only" == "docSource" ]]; then
      extract_docsource
      exit 0
    fi
    local jar="$N5_MODULES_DIR/$only.jar"
    if [[ ! -f "$jar" ]]; then
      echo "no such module jar: $jar" >&2
      exit 1
    fi
    if ! is_tridium_module "$jar"; then
      log "$only" "EXCLUDED: module.xml vendor=\"$(module_vendor "$jar")\" (not \"Tridium\") — not a real N5-shipped module, skipping"
      exit 0
    fi
    decompile_module "$jar" "$force"
    exit 0
  fi

  extract_docsource
  local excluded=0 jar module
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    # docSource.jar is handled entirely by extract_docsource above (it is the
    # original-.java-sources reference tree, not a module to decompile) — running
    # it through decompile_module too would write a redundant extracted/,
    # resources/, vineflower/ copy of the same 2868 .java files directly inside
    # organized/docSource/, colliding with extract_docsource's own layout there.
    if [[ "$module" == "docSource" ]]; then
      continue
    fi
    if ! is_tridium_module "$jar"; then
      log "$module" "EXCLUDED: module.xml vendor=\"$(module_vendor "$jar")\" (not \"Tridium\") — not a real N5-shipped module, skipping"
      excluded=$((excluded + 1))
      continue
    fi
    decompile_module "$jar" "$force"
  done < <(find "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0)
  log "_full-run" "vendor filter: excluded $excluded non-Tridium jar(s) from $N5_MODULES_DIR"
}

main "$@"
