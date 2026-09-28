#!/usr/bin/env bash
# n5-decompile.sh — decompile Niagara N5 modules into organized/<module>/
#
# Usage:
#   tools/n5-decompile.sh                 # decompile every jar in $N5_MODULES_DIR
#   tools/n5-decompile.sh <name>.jar      # decompile one module (name with or without .jar)
#   tools/n5-decompile.sh --docsource     # only extract docSource.jar (original .java sources)
#   tools/n5-decompile.sh --bin-ext       # decompile the Tridium-owned jars under bin/ext/
#   tools/n5-decompile.sh --force <name>  # ignore the sha256 cache, redo it
#   tools/n5-decompile.sh --prepare-libcache    # v2 only: build organized/_v2-libcache/ (see below)
#   tools/n5-decompile.sh --variant v2 <name>   # v2: same module, WITH library context
#   tools/n5-decompile.sh --variant v2 --all    # v2 over every module jar (see below)
#   tools/n5-decompile.sh --variant v2 --bin-ext [<name>]  # v2 over included bin/ext jar(s)
#
# --prepare-libcache (T19 fix, odd/tasks/decompiler-fidelity-audit.md): a required, explicit,
# ONE-TIME, serial step before any --variant v2 decompile. It extracts every module/bin-ext
# jar's LIB-INF/*.jar directly from the read-only source jars and copies each one into
# organized/_v2-libcache/<its own sha256>.jar. --variant v2 <name>/--bin-ext <name> FAILS LOUDLY
# if organized/_v2-libcache/ does not exist yet — run --prepare-libcache first, then drive
# per-module v2 work in parallel (e.g. `xargs -P 6`), same as the v1 campaign. `--variant v2
# --all` (and `--variant v2 --bin-ext` with no <name>) run it automatically, serially, before
# looping. Idempotent (skips an already-cached entry unless --force). The original race this
# closes: the first v2 campaign (2026-09-28 07:20-07:32Z) built the LIB-INF part of the library
# set by scanning organized/*/extracted/LIB-INF/*.jar LIVE, while OTHER parallel workers were
# concurrently rm -rf+unzip-ing their own organized/<mod>/extracted/ — a worker's `find` could
# observe another module's extracted/ mid-rewrite and silently miss its LIB-INF jars. Sourcing
# from the immutable cache instead removes that dependency entirely — see the "v2 library-context
# run" section of docs/decompiler-bakeoff.md for the affected-module list and the fix writeup.
#
# --variant v2's --force redoes the DECOMPILE (Vineflower/CFR) but no longer forces
# RE-EXTRACTION: extracted/ is reused as-is whenever its recorded provenance (the
# extracted/.jar_sha256 marker, written right after every real extraction) matches the current
# jar's sha256 — --force cannot reopen the race above by itself, because it no longer performs an
# unconditional rm -rf on a tree another worker might be reading.
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
  # Tolerant of a missing/unreadable file (empty string, not a crash): under
  # `set -o pipefail`, `sha256sum <missing> | awk ...` would otherwise
  # propagate sha256sum's failure through the pipe and, via `set -e`, abort
  # the whole script from inside a plain assignment (`x="$(sha256_of ...)"`)
  # — including decompile_module_v2's own N5_VINEFLOWER/N5_CFR hashing, which
  # must survive a genuinely missing/misconfigured tool jar so the rest of the
  # pipeline can run its course and record the resulting decompile failure
  # properly (T19 fix, requirement 4) instead of crashing opaquely before it.
  sha256sum "$1" 2>/dev/null | awk '{print $1}' || true
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
  # Provenance marker (T19 fix): records which jar sha256 the CURRENT extracted/
  # tree reflects, so --variant v2's ensure_extracted_for_v2 can trust-and-reuse
  # this extraction (requirements 3+6) instead of blindly re-extracting.
  printf '%s' "$sha" > "$moddir/extracted/.jar_sha256"

  # resources/ = a copy of every non-.class file (module.xml, lexicons, .properties,
  # .xml, images, etc.) so a reader doesn't have to wade through the class tree.
  rm -rf "${moddir:?}/resources"
  mkdir -p "$moddir/resources"
  ( cd "$moddir/extracted" && find . -type f ! -name '*.class' ! -name '.jar_sha256' -print0 ) \
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

# ---------------------------------------------------------------------------
# --prepare-libcache (T19 fix, requirement 1) — build the LIB-INF part of the
# v2 library set from an IMMUTABLE cache, never from a live organized/<mod>/
# extracted/ tree.
#
# The first --variant v2 campaign (2026-09-28 07:20-07:32Z) re-extracted 5
# modules' extracted/ (rm -rf + unzip, via ensure_extracted_for_v2) WHILE other
# parallel workers were building their own -e list by scanning
# organized/*/extracted/LIB-INF/*.jar live — a filesystem race: a concurrent
# `find` could observe a module's extracted/ mid rm-rf-then-unzip and miss its
# LIB-INF jars entirely, non-deterministically weakening that OTHER module's
# library context. Sourcing LIB-INF jars from an immutable, pre-built cache
# instead removes the dependency on any other worker's live extracted/ state.
#
# Every module jar's LIB-INF/*.jar is extracted directly from the read-only
# source jar under $N5_MODULES_DIR (never from organized/), and each nested lib
# jar is copied into $N5_OUT_DIR/_v2-libcache/<its own sha256>.jar — "keyed by
# source jar sha256" per the fix spec: the key is the sha256 of the cached
# jar's own bytes, which (a) naturally deduplicates identical embedded libs
# shipped by multiple modules and (b) makes staleness moot — a changed LIB-INF
# jar gets a different key, never collides with or overwrites an old one.
# Idempotent: an existing cache entry is left alone unless --force.
prepare_v2_libcache() {
  local force="${1:-false}"
  local cache_dir="$N5_OUT_DIR/_v2-libcache"
  mkdir -p "$cache_dir"
  local jar tmpdir added=0 scanned=0
  local -a all_source_jars=()
  # $N5_MODULES_DIR is flat (-maxdepth 1); $N5_BIN_EXT_DIR is scanned
  # recursively, matching compute_v2_library_jars' own bin/ext scan (and
  # decompile_binext's), which is NOT -maxdepth 1 — bin/ext ships several
  # jars nested under subdirectories (bcfips/, bcstd/, jxbrowser/, system/,
  # securityBridge/). A --maxdepth 1 scan here would silently miss those
  # jars' own LIB-INF content and leave them out of the _source_shas.tsv
  # performance manifest (compute_v2_idempotency_key would still hash them
  # correctly via its per-jar fallback — just slower, not incorrect — but the
  # LIB-INF omission would be a real, if unlikely, fidelity gap).
  while IFS= read -r -d '' jar; do
    [[ "$(basename "$jar" .jar)" == "docSource" ]] && continue
    all_source_jars+=("$jar")
    scanned=$((scanned + 1))
    tmpdir="$(mktemp -d)"
    unzip -o -q "$jar" 'LIB-INF/*.jar' -d "$tmpdir" 2>/dev/null || true
    local libjar
    while IFS= read -r -d '' libjar; do
      local libsha; libsha="$(sha256_of "$libjar")"
      local dest="$cache_dir/$libsha.jar"
      if [[ "$force" == "true" || ! -f "$dest" ]]; then
        cp "$libjar" "$dest.tmp.$$"
        mv "$dest.tmp.$$" "$dest"
        added=$((added + 1))
      fi
    done < <(find "$tmpdir" -name '*.jar' -print0 2>/dev/null)
    rm -rf "$tmpdir"
  done < <(find "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0 2>/dev/null)
  if [[ -d "$N5_BIN_EXT_DIR" ]]; then
    while IFS= read -r -d '' jar; do
      all_source_jars+=("$jar")
      scanned=$((scanned + 1))
      tmpdir="$(mktemp -d)"
      unzip -o -q "$jar" 'LIB-INF/*.jar' -d "$tmpdir" 2>/dev/null || true
      local libjar
      while IFS= read -r -d '' libjar; do
        local libsha; libsha="$(sha256_of "$libjar")"
        local dest="$cache_dir/$libsha.jar"
        if [[ "$force" == "true" || ! -f "$dest" ]]; then
          cp "$libjar" "$dest.tmp.$$"
          mv "$dest.tmp.$$" "$dest"
          added=$((added + 1))
        fi
      done < <(find "$tmpdir" -name '*.jar' -print0 2>/dev/null)
      rm -rf "$tmpdir"
    done < <(find "$N5_BIN_EXT_DIR" -name '*.jar' -print0 2>/dev/null)
  fi

  # Performance (not a correctness requirement): also pre-hash every scanned
  # module/bin-ext jar ITSELF (not just its LIB-INF content) into one manifest,
  # _source_shas.tsv (sha256sum's own "<hash>  <path>" format, one batched
  # invocation). compute_v2_idempotency_key needs every library jar's sha256 on
  # every single-module v2 invocation (T19 fix, requirement 2); without this,
  # each of ~250 module invocations would separately re-hash the same ~360
  # jars — expensive when $N5_MODULES_DIR/$N5_BIN_EXT_DIR live on a slow mount
  # (e.g. /mnt/c under WSL). Rebuilt fresh each --prepare-libcache run (jars
  # rarely change; --force is not required to refresh it).
  if [[ "${#all_source_jars[@]}" -gt 0 ]]; then
    sha256sum "${all_source_jars[@]}" > "$cache_dir/_source_shas.tsv.tmp.$$" 2>/dev/null || true
    mv "$cache_dir/_source_shas.tsv.tmp.$$" "$cache_dir/_source_shas.tsv"
  fi

  log "_prepare-libcache" "scanned $scanned module/bin-ext jar(s), added/updated $added lib jar(s) into $cache_dir"
}

# Populates global array V2_ALL_LIB_JARS with every jar to offer Vineflower as
# external library context: every jar in $N5_MODULES_DIR except docSource.jar
# (a sources-only jar, not compiled classes — useless and potentially confusing
# as a class-resolution source), every jar under $N5_BIN_EXT_DIR (all of it, not
# just the six classified "Tridium-owned" by n5-classify-binext.py — that rule
# picks which jars are worth *decompiling*, a different question from which
# jars help *resolve types* while decompiling something else; third-party libs
# like Jetty/Jackson under bin/ext are exactly the kind of thing a module's
# generics/casts may reference), and every jar cached under
# $N5_OUT_DIR/_v2-libcache/ by --prepare-libcache (T19 fix: embedded
# third-party libs some modules ship inside their own jar's LIB-INF/, e.g.
# jodaTime's joda-time-2.14.3.jar — sourced from the immutable cache, never
# from a live organized/*/extracted/ tree; see prepare_v2_libcache above).
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
  done < <(find "$N5_OUT_DIR/_v2-libcache" -maxdepth 1 -name '*.jar' -print0 2>/dev/null)
}

# Builds V2_LIB_CSV (comma-joined, for Vineflower -e=), V2_LIB_COLON
# (colon-joined, for CFR --extraclasspath) and V2_LIB_ARRAY (the surviving
# paths, for the idempotency key) from V2_ALL_LIB_JARS, excluding the one jar
# given (the module currently being decompiled — it must never appear in its
# own library-context list). Also sets V2_LIB_COUNT.
#
# T19 fix, requirement 9: self-exclusion compares realpath, not the literal
# string, so the module's own jar is still excluded even if it is also
# reachable via a different path spelling (symlink, relative component, a
# bin/ext alias, ...). Every candidate path is also checked for ',' (breaks
# Vineflower's -e CSV separator) and ':' (breaks CFR's --extraclasspath
# separator) and the script fails loudly rather than silently building a
# corrupted external-library argument.
build_v2_external_lists() {
  local exclude="$1"
  local exclude_real
  exclude_real="$(realpath -m -- "$exclude" 2>/dev/null || printf '%s' "$exclude")"
  local csv="" colon="" count=0
  V2_LIB_ARRAY=()
  local p p_real
  for p in "${V2_ALL_LIB_JARS[@]}"; do
    p_real="$(realpath -m -- "$p" 2>/dev/null || printf '%s' "$p")"
    [[ "$p_real" == "$exclude_real" ]] && continue
    if [[ "$p" == *,* ]]; then
      echo "FATAL: library jar path contains ',' (breaks Vineflower's -e CSV separator): $p" >&2
      exit 1
    fi
    if [[ "$p" == *:* ]]; then
      echo "FATAL: library jar path contains ':' (breaks CFR's --extraclasspath separator): $p" >&2
      exit 1
    fi
    csv="${csv:+$csv,}$p"
    colon="${colon:+$colon:}$p"
    V2_LIB_ARRAY+=("$p")
    count=$((count + 1))
  done
  V2_LIB_CSV="$csv"
  V2_LIB_COLON="$colon"
  V2_LIB_COUNT="$count"
}

# T19 fix, requirement 8: the SAME array (V2_FLAG_NAMES/V2_FLAG_VALUES) drives
# both Vineflower's command-line flags (V2_FLAG_ARGS) and the JSON recorded in
# recon.json (V2_FLAGS_JSON) — a single source of truth, so recon.json can
# never silently drift from what was actually passed to the decompiler.
V2_FLAG_NAMES=(use-lvt-names use-method-parameters decompile-generics decompile-assert
  rename-members decompile-complex-constant-dynamic ignore-invalid-bytecode
  dump-bytecode-on-error decompiler-comments)
V2_FLAG_VALUES=(true true true true false false false true true)

build_v2_flags() {
  V2_FLAG_ARGS=()
  local flags_json="{" first=true i
  for i in "${!V2_FLAG_NAMES[@]}"; do
    V2_FLAG_ARGS+=("--${V2_FLAG_NAMES[$i]}=${V2_FLAG_VALUES[$i]}")
    local key="${V2_FLAG_NAMES[$i]//-/_}"
    $first || flags_json+=","
    first=false
    flags_json+="\"$key\": ${V2_FLAG_VALUES[$i]}"
  done
  flags_json+="}"
  V2_FLAGS_JSON="$flags_json"
}

# T19 fix, requirement 2: idempotency key = sha256 of (module jar sha256 +
# sorted library-set sha256 list + JDK home + flag list + tool jar sha256s). A
# change in ANY of these must trigger a re-decompile, not just a changed module
# jar. Library jars already living in $N5_OUT_DIR/_v2-libcache/ are keyed by
# their own sha256 already (their filename IS the hash), so those are reused
# directly; every other jar in the set (every $N5_MODULES_DIR / $N5_BIN_EXT_DIR
# jar) is hashed with one batched `sha256sum` call rather than one process per
# jar, since the full set (V2_LIB_ARRAY) can be ~450 entries.
# Lazily loads $N5_OUT_DIR/_v2-libcache/_source_shas.tsv (prepare_v2_libcache's
# performance manifest, sha256sum's own "<hash>  <path>" format) into
# V2_SOURCE_SHA_BY_PATH, once per process. A path with no manifest entry (the
# manifest is missing entirely, or a jar was added after --prepare-libcache
# last ran) is simply absent from the map — compute_v2_idempotency_key falls
# back to hashing it directly, so a stale/missing manifest only costs
# performance, never correctness.
declare -A V2_SOURCE_SHA_BY_PATH=()
V2_SOURCE_SHA_LOADED="false"
load_v2_source_shas() {
  [[ "$V2_SOURCE_SHA_LOADED" == "true" ]] && return 0
  V2_SOURCE_SHA_LOADED="true"
  local manifest="$N5_OUT_DIR/_v2-libcache/_source_shas.tsv"
  [[ -f "$manifest" ]] || return 0
  local line hash rest
  while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    hash="${line%%  *}"
    rest="${line#*  }"
    V2_SOURCE_SHA_BY_PATH["$rest"]="$hash"
  done < "$manifest"
}

compute_v2_idempotency_key() {
  local jar_sha="$1"
  local vf_sha="$2" cfr_sha="$3"
  local -a lib_hashes=()
  local -a to_hash=()
  local p
  for p in "${V2_LIB_ARRAY[@]}"; do
    if [[ "$p" == "$N5_OUT_DIR/_v2-libcache/"* ]]; then
      lib_hashes+=("$(basename "$p" .jar)")
      continue
    fi
    load_v2_source_shas
    if [[ -n "${V2_SOURCE_SHA_BY_PATH[$p]:-}" ]]; then
      lib_hashes+=("${V2_SOURCE_SHA_BY_PATH[$p]}")
    else
      to_hash+=("$p")
    fi
  done
  if [[ "${#to_hash[@]}" -gt 0 ]]; then
    while IFS= read -r h; do
      lib_hashes+=("$h")
    done < <(sha256sum "${to_hash[@]}" 2>/dev/null | awk '{print $1}')
  fi
  local sorted_libs
  sorted_libs="$(printf '%s\n' "${lib_hashes[@]}" | sort)"
  {
    printf 'jar_sha256=%s\n' "$jar_sha"
    printf 'jdk_home=%s\n' "$N5_JDK25_HOME"
    printf 'flags=%s\n' "$V2_FLAGS_JSON"
    printf 'vineflower_sha256=%s\n' "$vf_sha"
    printf 'cfr_sha256=%s\n' "$cfr_sha"
    printf 'libs=%s\n' "$sorted_libs"
  } | sha256sum | awk '{print $1}'
}

# v1's decompile_module always re-extracts unconditionally (safe there: it's
# only reached after an sha256 mismatch already proved the extraction is
# stale). v2 shares the same organized/<mod>/extracted/ and resources/ trees
# as v1 rather than keeping a second copy, so it must NOT blindly wipe them.
#
# T19 fix, requirements 3+6: "force re-decompile" (redo Vineflower/CFR) is now
# separate from "force re-extract" (rm -rf + unzip extracted/). --force alone
# must NOT force re-extraction — only a verifiably stale or missing
# extracted/ does. Staleness is decided by comparing the CURRENT jar's sha256
# against extracted/.jar_sha256, a provenance marker both v1's decompile_module
# and this function write right after a real extraction. No marker (an
# extracted/ tree that predates this fix, or was produced some other way) is
# treated as stale — there is nothing trustworthy to reuse — so it is
# re-extracted once; after that it always carries the marker. This also means
# --force can never reopen the T19 race: it no longer performs an unconditional
# rm -rf on a tree other workers might read.
ensure_extracted_for_v2() {
  local jar="$1" moddir="$2" _force_unused="$3" module="$4"
  local sha; sha="$(sha256_of "$jar")"
  local need_extract="false"
  local marker="$moddir/extracted/.jar_sha256"
  local recorded=""
  [[ -f "$marker" ]] && recorded="$(cat "$marker" 2>/dev/null || true)"

  if [[ ! -d "$moddir/extracted" ]]; then
    need_extract="true"
  elif [[ -z "$(find "$moddir/extracted" -name '*.class' -print -quit 2>/dev/null)" ]]; then
    need_extract="true"
  elif [[ -z "$recorded" ]]; then
    need_extract="true"
  elif [[ "$recorded" != "$sha" ]]; then
    need_extract="true"
  fi

  if [[ "$need_extract" != "true" ]]; then
    log "$module" "v2 reusing existing extracted/+resources/ (jar sha256 $sha matches extracted/.jar_sha256)"
    return 0
  fi

  mkdir -p "$moddir/extracted" "$moddir/resources"
  log "$module" "v2 extracting $jar (extracted/ missing, empty, or stale vs the current jar sha256)"
  rm -rf "${moddir:?}/extracted"
  mkdir -p "$moddir/extracted"
  unzip -o -q "$jar" -d "$moddir/extracted"
  printf '%s' "$sha" > "$moddir/extracted/.jar_sha256"

  rm -rf "${moddir:?}/resources"
  mkdir -p "$moddir/resources"
  ( cd "$moddir/extracted" && find . -type f ! -name '*.class' ! -name '.jar_sha256' -print0 ) \
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
#
# T19 fix, requirement 7: every value that could conceivably contain a
# double-quote, backslash, or other Python-string-literal metacharacter
# (module name, JDK home path, fallback reason, ...) is passed through the
# ENVIRONMENT, never interpolated into the heredoc's text — the heredoc itself
# is quoted (<<'PYEOF'), so bash performs no expansion on it at all and the
# Python source is fixed, literal code regardless of what these values contain.
write_recon_v2() {
  local module="$1" moddir="$2" sha="$3" primary_status="$4" primary_time="$5" \
        fallback_used="$6" fallback_reason="$7" status="$8" idempotency_key="$9"
  local vf_sha cfr_sha vf_version cfr_version
  vf_sha="$(sha256_of "$N5_VINEFLOWER")"
  cfr_sha="$(sha256_of "$N5_CFR")"
  vf_version="$(basename "$N5_VINEFLOWER" .jar)"
  cfr_version="$(basename "$N5_CFR" .jar)"
  local markers
  markers="$(scan_marker_files "$moddir/vineflower2" | wc -l | tr -d ' ')"

  RECON_PATH="$moddir/recon.json" \
  RECON_MODULE="$module" \
  RECON_JAR_SHA256="$sha" \
  RECON_VF_VERSION="$vf_version" \
  RECON_VF_SHA256="$vf_sha" \
  RECON_CFR_VERSION="$cfr_version" \
  RECON_CFR_SHA256="$cfr_sha" \
  RECON_LIB_COUNT="$V2_LIB_COUNT" \
  RECON_INCLUDE_RUNTIME="$N5_JDK25_HOME" \
  RECON_FLAGS_JSON="$V2_FLAGS_JSON" \
  RECON_PRIMARY_STATUS="$primary_status" \
  RECON_PRIMARY_TIME="$primary_time" \
  RECON_FALLBACK_USED="$fallback_used" \
  RECON_FALLBACK_REASON="$fallback_reason" \
  RECON_MARKERS="$markers" \
  RECON_STATUS="$status" \
  RECON_IDEMPOTENCY_KEY="$idempotency_key" \
  python3 <<'PYEOF'
import json, os

path = os.environ["RECON_PATH"]
try:
    with open(path) as fh:
        recon = json.load(fh)
except (OSError, json.JSONDecodeError):
    recon = {"module": os.environ["RECON_MODULE"]}

recon["v2"] = {
    "variant": "v2",
    "jar_sha256": os.environ["RECON_JAR_SHA256"],
    "vineflower_version": os.environ["RECON_VF_VERSION"],
    "vineflower_sha256": os.environ["RECON_VF_SHA256"],
    "cfr_version": os.environ["RECON_CFR_VERSION"],
    "cfr_sha256": os.environ["RECON_CFR_SHA256"],
    "add_external_count": int(os.environ["RECON_LIB_COUNT"]),
    "include_runtime": os.environ["RECON_INCLUDE_RUNTIME"],
    "flags": json.loads(os.environ["RECON_FLAGS_JSON"]),
    "primary_status": os.environ["RECON_PRIMARY_STATUS"],
    "primary_time_seconds": int(os.environ["RECON_PRIMARY_TIME"]),
    "fallback_used": os.environ["RECON_FALLBACK_USED"] == "true",
    "fallback_reason": os.environ["RECON_FALLBACK_REASON"],
    "decompile_failure_markers": int(os.environ["RECON_MARKERS"]),
    "status": os.environ["RECON_STATUS"],
    "idempotency_key": os.environ["RECON_IDEMPOTENCY_KEY"],
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

  # T19 fix, requirement 1: the library context MUST come from the immutable
  # cache, never a live organized/*/extracted/ scan — fail loudly rather than
  # silently decompiling with a weaker (or, worse, non-deterministic) library
  # set if the cache was never built.
  if [[ ! -d "$N5_OUT_DIR/_v2-libcache" ]]; then
    echo "FATAL: $N5_OUT_DIR/_v2-libcache does not exist — run 'tools/n5-decompile.sh --prepare-libcache' once, serially, before any --variant v2 decompile (T19 fix: the v2 library context must never be built from a live organized/*/extracted/ tree, which a concurrent worker may be mid rm-rf+unzip on)." >&2
    exit 1
  fi

  local sha; sha="$(sha256_of "$jar")"
  mkdir -p "$moddir"
  ensure_extracted_for_v2 "$jar" "$moddir" "$force" "$module"

  local class_count
  class_count="$(find "$moddir/extracted" -name '*.class' | wc -l)"

  compute_v2_library_jars
  build_v2_external_lists "$jar"
  build_v2_flags

  local vf_sha cfr_sha
  vf_sha="$(sha256_of "$N5_VINEFLOWER")"
  cfr_sha="$(sha256_of "$N5_CFR")"

  # T19 fix, requirement 2: idempotency key covers the module jar, the full
  # resolved library set, the JDK runtime home, the fidelity flags, and the
  # decompiler tool jars themselves — not just the module jar's sha256 like the
  # first v2 campaign checked. Any change in any of these forces a redo, even
  # under an unchanged module jar and without --force.
  local idempotency_key
  idempotency_key="$(compute_v2_idempotency_key "$sha" "$vf_sha" "$cfr_sha")"

  if [[ "$force" != "true" ]] && [[ -f "$moddir/recon.json" ]]; then
    local prev_key prev_status
    prev_key="$(python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
print(d.get('v2', {}).get('idempotency_key', ''))
" "$moddir/recon.json" 2>/dev/null || true)"
    prev_status="$(python3 -c "
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
print(d.get('v2', {}).get('status', ''))
" "$moddir/recon.json" 2>/dev/null || true)"
    # T19 fix, requirement 4: a module recorded status=failed is NEVER treated
    # as up to date, regardless of the idempotency key — a failed module must
    # always be retried until it actually succeeds or is explicitly forced.
    if [[ "$prev_key" == "$idempotency_key" ]] && [[ "$prev_status" == "ok" ]]; then
      log "$module" "v2 up to date (idempotency key $idempotency_key), skipping"
      return 0
    fi
  fi

  # T19 fix, requirement 5: fallback2/ is cleared unconditionally at the start
  # of each run (mirroring vineflower2/ below) so a class that used to need the
  # CFR fallback but no longer does can never leave a stale fallback2/*.java
  # behind that a reader might mistake for current output.
  rm -rf "${moddir:?}/fallback2"
  # Recreated (empty) immediately, not only inside the fallback branches below:
  # under `set -o pipefail`, `find "$moddir/fallback2" ... | wc -l` later in
  # this function would otherwise fail (find exits nonzero on a missing path,
  # pipefail propagates that through `| wc -l`) whenever primary succeeds and
  # no fallback is needed, aborting the whole script via errexit.
  mkdir -p "$moddir/fallback2"

  rm -rf "${moddir:?}/vineflower2"
  mkdir -p "$moddir/vineflower2"
  log "$module" "v2 primary(vineflower) starting on $class_count classes (lib_count=$V2_LIB_COUNT, runtime=$N5_JDK25_HOME)"

  # Additional options MUST precede -e/--add-external — see the header comment's
  # "Undocumented Vineflower 1.12.0 CLI ordering requirement". V2_FLAG_ARGS
  # (built by build_v2_flags, requirement 8's single source of truth) supplies
  # every Additional option here, in the same order recorded in recon.json.
  local vf2_cmd=(
    "$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error
    --include-runtime="$N5_JDK25_HOME"
    "${V2_FLAG_ARGS[@]}"
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

  # T19 fix, requirement 4: a module where BOTH decompilers produced nothing
  # (jar has classes, but neither vineflower2/ nor fallback2/ has a .java) is
  # NOT a success — record status=failed, exit non-zero, and (per the
  # idempotency check above) never treat it as cached/done on a later run.
  local total_produced status="ok"
  total_produced=$(( \
    $(find "$moddir/vineflower2" -name '*.java' 2>/dev/null | wc -l) \
    + $(find "$moddir/fallback2" -name '*.java' 2>/dev/null | wc -l) \
  ))
  if [[ "$class_count" -gt 0 && "$total_produced" -eq 0 ]]; then
    status="failed"
  fi

  write_recon_v2 "$module" "$moddir" "$sha" "$primary_status" "$primary_time" \
    "$fallback_used" "$fallback_reason" "$status" "$idempotency_key"

  if [[ "$status" == "failed" ]]; then
    log "$module" "v2 FAILED: both Vineflower and CFR produced zero output for $class_count classes"
    return 1
  fi
  log "$module" "v2 done"
}

# T19 fix: --all always prepares the libcache first, serially, exactly once,
# before decompiling any module — this is what makes it safe to then drive
# per-module v2 work in parallel (external `xargs -P`, or a future internal
# parallelism): every worker reads the SAME already-complete, immutable cache
# instead of racing to build it from live extracted/ trees.
run_v2_all_modules() {
  local force="$1"
  prepare_v2_libcache "$force"
  local excluded=0 failed=0 ok=0 jar module
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
    if decompile_module_v2 "$jar" "$force"; then
      ok=$((ok + 1))
    else
      failed=$((failed + 1))
    fi
  done < <(find "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0)
  log "_full-run" "v2 vendor filter: excluded $excluded non-Tridium jar(s) from $N5_MODULES_DIR"
  log "_full-run" "v2 done: ok=$ok failed=$failed excluded=$excluded"
  [[ "$failed" -eq 0 ]]
}

run_v2_binext() {
  local force="$1" only="$2"
  local out_root="$N5_OUT_DIR/_bin-ext"
  mkdir -p "$out_root"
  prepare_v2_libcache "$force"

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
    return $?
  fi

  local jar module verdict included=0 skipped=0 failed=0
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_bin-ext.log" || true)"
    if [[ "$verdict" == include* ]]; then
      log "_bin-ext" "v2 including $module ($verdict)"
      if decompile_module_v2 "$jar" "$force" "$out_root/$module"; then
        included=$((included + 1))
      else
        failed=$((failed + 1))
      fi
    else
      log "_bin-ext" "v2 skipping $module ($verdict)"
      skipped=$((skipped + 1))
    fi
  done < <(find "$N5_BIN_EXT_DIR" -name '*.jar' -print0)
  log "_bin-ext" "v2 done: included=$included skipped=$skipped failed=$failed"
  [[ "$failed" -eq 0 ]]
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
      --prepare-libcache)
        prepare_v2_libcache "false"
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
      exit $?
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
    exit $?
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

# Only run main() when executed directly, not when sourced (e.g. by the T19-fix
# unit tests in tools/tests/n5-decompile.bats, which source this file to call
# its internal functions — compute_v2_library_jars, build_v2_external_lists,
# ... — directly against synthetic fixtures without a real decompile).
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
