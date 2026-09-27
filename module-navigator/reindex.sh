#!/usr/bin/env bash
#
# reindex.sh — Rebuild all module-navigator indexes safely.
#
# Why this exists: the 12 build_*.py builders have a dependency order and a
# shared-path footgun. build_method/field/xref/annotations read the corpus
# `source` from module-inventory.json; if that inventory is stale (e.g. a
# Windows path after moving the corpus) those builders fail and overwrite their
# index with an EMPTY file. This script enforces the correct order
# (class -> inventory -> rest), validates every output, and can roll back.
#
# Usage:
#   ./reindex.sh                 full rebuild (with backup + validation)
#   ./reindex.sh --check         preflight only: validate setup + print plan, run nothing
#   ./reindex.sh --no-backup     skip the index backup (faster, no rollback safety)
#   ./reindex.sh --only NAME     rebuild a single builder (e.g. --only build_string_index.py)
#
set -uo pipefail

NAV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS="$NAV_DIR/tools"
IDX="$NAV_DIR/indexes"
BAK="$IDX/.reindex-bak"

# Dependency order: class-index first (catalog), module-inventory second
# (carries the corpus `source` path the rest depend on), then everything else.
ORDER=(
  "build_class_index.py:class-index.json"
  "build_module_inventory.py:module-inventory.json"
  "build_string_index.py:string-index.db"
  "build_token_index.py:token-index.db"
  "build_method_index.py:method-index.json"
  "build_field_index.py:field-index.json"
  "build_callgraph_index.py:callgraph-index.json"
  "build_exceptions_index.py:exceptions-index.json"
  "build_swing_index.py:swing-index.json"
  "build_inheritance.py:inheritance.json"
  "build_xref.py:xref-index.json"
  "build_annotations_index.py:annotations-index.json"
)

MODE="run"
NO_BACKUP=0
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --check) MODE="check" ;;
    --no-backup) NO_BACKUP=1 ;;
    --only) shift; ONLY="${1:-}" ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
  shift
done

red()   { printf '\033[31m%s\033[0m\n' "$1"; }
green() { printf '\033[32m%s\033[0m\n' "$1"; }
yellow(){ printf '\033[33m%s\033[0m\n' "$1"; }

size_of() { stat -c%s "$1" 2>/dev/null || echo 0; }

# --- Preflight ----------------------------------------------------------------
[ -d "$TOOLS" ]   || { red "tools/ not found at $TOOLS"; exit 1; }
[ -d "$IDX" ]     || { red "indexes/ not found at $IDX"; exit 1; }
command -v python3 >/dev/null || { red "python3 not found"; exit 1; }

# The corpus path is hardcoded inside build_class_index.py / build_module_inventory.py.
# Extract it and verify it exists — this is the root-cause guard for the empty-index bug.
ORGANIZED="$(grep -oE '/[^"'"'"']*organized' "$TOOLS/build_class_index.py" 2>/dev/null | head -1)"
if [ -z "$ORGANIZED" ] || [ ! -d "$ORGANIZED" ]; then
  red "Corpus dir not found or unreadable: '${ORGANIZED:-<none>}'"
  red "Fix ORGANIZED_DIR in tools/build_class_index.py and build_module_inventory.py first."
  exit 1
fi
green "Corpus: $ORGANIZED"

# Validate every builder exists before doing anything.
for entry in "${ORDER[@]}"; do
  b="${entry%%:*}"
  [ -f "$TOOLS/$b" ] || { red "Missing builder: tools/$b"; exit 1; }
done

if [ "$MODE" = "check" ]; then
  echo "Plan (dependency order):"
  i=0
  for entry in "${ORDER[@]}"; do
    i=$((i+1)); b="${entry%%:*}"; o="${entry##*:}"
    cur=$(size_of "$IDX/$o")
    printf "  %2d. %-28s -> %-22s (current: %s)\n" "$i" "$b" "$o" "$(numfmt --to=iec $cur 2>/dev/null || echo ${cur}B)"
  done
  green "Preflight OK. Run without --check to rebuild."
  exit 0
fi

# --- Backup -------------------------------------------------------------------
if [ "$NO_BACKUP" -eq 0 ]; then
  rm -rf "$BAK"; mkdir -p "$BAK"
  yellow "Backing up current indexes to $BAK ..."
  for entry in "${ORDER[@]}"; do
    o="${entry##*:}"
    [ -f "$IDX/$o" ] && cp -p "$IDX/$o" "$BAK/$o"
  done
fi

# --- Build --------------------------------------------------------------------
fail=0
run_one() {
  local b="$1" o="$2"
  local prev; prev=$(size_of "$BAK/$o"); [ "$prev" -eq 0 ] && prev=$(size_of "$IDX/$o")
  local start end rc; start=$(date +%s)
  ( cd "$TOOLS" && python3 "$b" ) >"/tmp/reidx-$b.log" 2>&1; rc=$?
  end=$(date +%s)
  local now; now=$(size_of "$IDX/$o")
  # Validation: builder must exit 0, output must exist, and must not collapse to
  # an empty/tiny file (<50% of previous size when we had a meaningful previous).
  local bad=""
  [ $rc -ne 0 ] && bad="exit=$rc"
  [ "$now" -lt 10240 ] && bad="${bad:+$bad, }tiny ($(numfmt --to=iec $now 2>/dev/null || echo ${now}B))"
  if [ "$prev" -gt 102400 ] && [ "$now" -lt $((prev/2)) ]; then
    bad="${bad:+$bad, }shrank ${prev}B->${now}B"
  fi
  if [ -n "$bad" ]; then
    red "  ✗ $b ($((end-start))s) — $bad [log: /tmp/reidx-$b.log]"
    if [ "$NO_BACKUP" -eq 0 ] && [ -f "$BAK/$o" ]; then
      cp -p "$BAK/$o" "$IDX/$o"; yellow "    rolled back $o from backup"
    fi
    fail=1
  else
    green "  ✓ $b ($((end-start))s) -> $o $(numfmt --to=iec $now 2>/dev/null || echo ${now}B)"
  fi
}

echo "Rebuilding indexes..."
for entry in "${ORDER[@]}"; do
  b="${entry%%:*}"; o="${entry##*:}"
  [ -n "$ONLY" ] && [ "$b" != "$ONLY" ] && continue
  run_one "$b" "$o"
  # Root-cause guard: right after inventory, verify its `source` points at a real dir.
  if [ "$b" = "build_module_inventory.py" ] && [ -z "$ONLY" ]; then
    src=$(python3 - "$IDX/module-inventory.json" <<'PY' 2>/dev/null
import json,sys
try:
    d=json.load(open(sys.argv[1],encoding='utf-8-sig'))
    print(d.get('_meta',{}).get('source',''))
except Exception: print('')
PY
)
    if [ -z "$src" ] || [ ! -d "$src" ]; then
      red "ABORT: module-inventory source invalid ('$src'). Dependent builders would write empty indexes."
      red "Fix the corpus path in the builders and re-run."
      exit 1
    fi
    green "  inventory source OK: $src"
  fi
done

echo
if [ "$fail" -eq 0 ]; then
  green "Re-index complete — all indexes rebuilt and validated."
else
  red "Re-index finished WITH ERRORS — see logs above. Broken indexes rolled back where possible."
  exit 1
fi
