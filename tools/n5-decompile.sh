#!/usr/bin/env bash
# n5-decompile.sh — decompile Niagara N5 modules into organized/<module>/
#
# Usage:
#   tools/n5-decompile.sh                 # decompile every jar in $N5_MODULES_DIR
#   tools/n5-decompile.sh <name>.jar      # decompile one module (name with or without .jar)
#   tools/n5-decompile.sh --docsource     # only extract docSource.jar (original .java sources)
#   tools/n5-decompile.sh --bin-ext       # decompile the Tridium-owned jars under bin/ext/
#   tools/n5-decompile.sh --force <name>  # ignore the sha256 cache, redo it
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
#
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
# Primary decompiler: Vineflower (best Java 17-25 feature fidelity: records, sealed
# classes, switch pattern matching — see docs/decompiler-bakeoff.md). Fallback: CFR,
# used for a whole module when Vineflower times out or exits non-zero (observed on
# this corpus: Vineflower 1.12.0 hangs indefinitely on bajaui.jar's com.tridium.ui.*
# subtree; CFR decompiles the same jar in ~11s), and per-class when Vineflower
# completes but leaves an explicit decompiler-failure marker in a handful of files.
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
    # shellcheck disable=SC2016  # '$VF:' is a literal Vineflower marker, not an expansion
    marker_files="$(grep -rlE '^// \$VF: |Unable to fully decompile class|COULD NOT DECOMPILE|<unknown>' \
      "$moddir/vineflower" 2>/dev/null || true)"
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
# main
# ---------------------------------------------------------------------------
main() {
  local force="false"
  local only=""
  local mode="modules"

  # Parse every flag before acting, so order (--force --bin-ext vs --bin-ext
  # --force) never changes behavior.
  while [[ $# -gt 0 ]]; do
    case "$1" in
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
      *)
        only="$1"
        shift
        ;;
    esac
  done

  mkdir -p "$N5_OUT_DIR"

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
