#!/usr/bin/env bats
# Smoke test for tools/n5-decompile.sh, run against the smallest real N5 module
# jar in the corpus (lontunnel.jar: 2 classes) so it completes in seconds.
#
# Run with: bats tools/tests/n5-decompile.bats
#
# Skips (does not fail) if the N5 modules directory isn't mounted, since this
# repo's source jars live on a read-only Windows-side path that isn't present
# on every machine that might check out the repo.

# All @test cases share one decompile run (done once in setup_file) and one
# N5_OUT_DIR (BATS_FILE_TMPDIR, which bats keeps alive for the whole file) —
# per-test setup() would get a fresh BATS_TEST_TMPDIR and re-run everything.

setup_file() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  N5_MODULES_DIR="${N5_MODULES_DIR:-/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules}"
  MODULE="lontunnel"

  echo "$REPO_ROOT" > "$BATS_FILE_TMPDIR/repo_root"
  echo "$N5_MODULES_DIR" > "$BATS_FILE_TMPDIR/modules_dir"
  echo "$MODULE" > "$BATS_FILE_TMPDIR/module"

  if [[ ! -f "$N5_MODULES_DIR/$MODULE.jar" ]] \
      || [[ ! -f "$REPO_ROOT/tools/decompilers/vineflower-1.12.0.jar" ]] \
      || [[ ! -f "$REPO_ROOT/tools/decompilers/cfr-0.152.jar" ]]; then
    touch "$BATS_FILE_TMPDIR/skip_all"
    return 0
  fi

  export N5_MODULES_DIR N5_OUT_DIR="$BATS_FILE_TMPDIR/organized"
  "$REPO_ROOT/tools/n5-decompile.sh" "$MODULE" > "$BATS_FILE_TMPDIR/first_run.log" 2>&1
  echo "$?" > "$BATS_FILE_TMPDIR/first_run_status"

  # Snapshot of v1's vineflower/ output, taken right after the v1 run above and
  # before any --variant v2 run touches the same organized/$MODULE/ tree — used
  # by the "v1 unchanged" test below.
  find "$N5_OUT_DIR/$MODULE/vineflower" -name '*.java' 2>/dev/null | sort \
    | xargs -r sha256sum > "$BATS_FILE_TMPDIR/v1_vineflower_hashes_before.txt"

  # T19 fix (odd/tasks/decompiler-fidelity-audit.md): the v2 library context for
  # LIB-INF-embedded jars must come from an immutable cache built serially,
  # never from a live organized/*/extracted/ tree — --prepare-libcache is now a
  # required, explicit, one-time step before any --variant v2 decompile.
  N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}" \
    "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache > "$BATS_FILE_TMPDIR/libcache_prep.log" 2>&1
  echo "$?" > "$BATS_FILE_TMPDIR/libcache_prep_status"

  # One shared --variant v2 run, reused by every v2-flag-assertion test below
  # (mirrors the v1 sharing pattern above: one real decompile per file, not
  # per test, since library-context resolution over ~450 jars is real work).
  N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}" \
    "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE" > "$BATS_FILE_TMPDIR/v2_run.log" 2>&1
  echo "$?" > "$BATS_FILE_TMPDIR/v2_run_status"
}

# Build a tiny synthetic module jar (module.xml + optional LIB-INF/<name>.jar nested inside) for
# the fast, isolated T19-fix unit tests below, which must not depend on the ~450-jar real corpus
# for speed or determinism. `zipfile` (stdlib) is used instead of `jar`/`zip` so no extra tool is
# required beyond python3, already a hard dependency of this pipeline.
make_fake_jar() {
  local dest="$1" vendor="${2:-Tridium}" libinf_name="${3:-}"
  python3 - "$dest" "$vendor" "$libinf_name" <<'PY'
import sys, zipfile, io
dest, vendor, libinf_name = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", f'<module vendor="{vendor}"/>')
    z.writestr("marker.txt", dest)
    if libinf_name:
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as iz:
            iz.writestr("lib-marker.txt", libinf_name)
        z.writestr(f"LIB-INF/{libinf_name}", inner.getvalue())
PY
}

setup() {
  REPO_ROOT="$(cat "$BATS_FILE_TMPDIR/repo_root")"
  N5_MODULES_DIR="$(cat "$BATS_FILE_TMPDIR/modules_dir")"
  MODULE="$(cat "$BATS_FILE_TMPDIR/module")"
  N5_OUT_DIR="$BATS_FILE_TMPDIR/organized"
  export REPO_ROOT N5_MODULES_DIR MODULE N5_OUT_DIR

  if [[ -f "$BATS_FILE_TMPDIR/skip_all" ]]; then
    skip "N5 modules dir or decompiler jars not available (see tools/decompilers/README.md)"
  fi
}

@test "first run exits 0 and writes recon.json" {
  status="$(cat "$BATS_FILE_TMPDIR/first_run_status")"
  [ "$status" -eq 0 ]
  [ -f "$N5_OUT_DIR/$MODULE/recon.json" ]
}

@test "extracted/ contains the module's class files" {
  [ -d "$N5_OUT_DIR/$MODULE/extracted" ]
  count=$(find "$N5_OUT_DIR/$MODULE/extracted" -name '*.class' | wc -l)
  [ "$count" -ge 2 ]
}

@test "resources/ contains module.xml but no .class files" {
  [ -f "$N5_OUT_DIR/$MODULE/resources/META-INF/module.xml" ]
  count=$(find "$N5_OUT_DIR/$MODULE/resources" -name '*.class' | wc -l)
  [ "$count" -eq 0 ]
}

@test "primary decompiler (vineflower) produced at least one .java file" {
  count=$(find "$N5_OUT_DIR/$MODULE/vineflower" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -ge 1 ]
}

@test "recon.json has the expected fields and a sha256 matching the source jar" {
  expected_sha=$(sha256sum "$N5_MODULES_DIR/$MODULE.jar" | awk '{print $1}')
  actual_sha=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['jar_sha256'])")
  [ "$actual_sha" = "$expected_sha" ]

  module_name=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['module'])")
  [ "$module_name" = "$MODULE" ]

  class_count=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['class_count'])")
  [ "$class_count" -ge 2 ]
}

# --- --variant v2 (library-context decompile: --add-external + --include-runtime) ---
# The shared v2 run above (setup_file) decompiles $MODULE (lontunnel) with a
# real -e list built from every other N5 module jar, every bin/ext jar, and
# every already-extracted LIB-INF jar under organized/ — the same real corpus
# used by the plain v1 run, not a stub/mock. Its exact invocation is logged as
# a "CMD: ..." line in organized/_logs/$MODULE.v2.log (see decompile_module_v2
# in n5-decompile.sh), which these tests inspect instead of re-parsing live
# process argv.
#
# This block MUST run before the "--force redoes the module" v1 test below:
# v1's write_recon (tools/n5-recon-helper.py) fully overwrites recon.json —
# pre-existing behavior, unchanged by this feature — so a v1 --force rerun
# silently drops any "v2" sub-object a prior --variant v2 run had merged in.
# That is a real, documented interaction (see docs/decompiler-bakeoff.md and
# the write_recon_v2 comment in n5-decompile.sh), not a v2 bug; ordering these
# tests before the v1 --force test keeps this file's assertions accurate
# without changing v1's untouched behavior.

@test "--variant v2 exits 0 and produces vineflower2/ output" {
  status="$(cat "$BATS_FILE_TMPDIR/v2_run_status")"
  [ "$status" -eq 0 ]
  count=$(find "$N5_OUT_DIR/$MODULE/vineflower2" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -ge 1 ]
}

@test "--variant v2 passes --add-external with other module jars, excluding the module's own jar" {
  cmd_line="$(grep '^CMD:' "$N5_OUT_DIR/_logs/$MODULE.v2.log" | head -1)"
  [[ -n "$cmd_line" ]]
  [[ "$cmd_line" == *"-e="* ]]
  # a real other-module jar (baja.jar) must be in the external list
  [[ "$cmd_line" == *"/baja.jar"* ]]
  # the module's OWN jar must appear exactly once on the command line (as the
  # source positional arg), never a second time inside the -e= value
  own_count=$(grep -o "/$MODULE\.jar" <<< "$cmd_line" | wc -l)
  [ "$own_count" -eq 1 ]
}

@test "--variant v2 passes --include-runtime pointing at the JDK 25 home" {
  cmd_line="$(grep '^CMD:' "$N5_OUT_DIR/_logs/$MODULE.v2.log" | head -1)"
  runtime="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}"
  [[ "$cmd_line" == *"--include-runtime=$runtime"* ]]
}

@test "--variant v2 command line has no Vineflower 'missing ... ignored' parse-order warnings" {
  # Regression for an undocumented Vineflower CLI ordering bug found while
  # building this feature: an Additional option (--include-runtime, ...) placed
  # AFTER -e/--add-external is silently dropped rather than applied. Every
  # Additional option must precede -e on the command line.
  run grep -c 'warn: missing' "$N5_OUT_DIR/_logs/$MODULE.v2.log"
  [ "$status" -ne 0 ]
  [ "$output" -eq 0 ]
}

@test "--variant v2 does not touch the existing v1 vineflower/ output" {
  find "$N5_OUT_DIR/$MODULE/vineflower" -name '*.java' | sort | xargs -r sha256sum \
    > "$BATS_TEST_TMPDIR/v1_vineflower_hashes_after.txt"
  diff "$BATS_FILE_TMPDIR/v1_vineflower_hashes_before.txt" "$BATS_TEST_TMPDIR/v1_vineflower_hashes_after.txt"
}

@test "recon.json keeps its v1 fields and gains a v2 sub-object after a v2 run" {
  primary_decompiler=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['primary_decompiler'])")
  [ "$primary_decompiler" = "vineflower-1.12.0" ]

  v2_variant=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['variant'])")
  [ "$v2_variant" = "v2" ]

  v2_sha=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['jar_sha256'])")
  expected_sha=$(sha256sum "$N5_MODULES_DIR/$MODULE.jar" | awk '{print $1}')
  [ "$v2_sha" = "$expected_sha" ]

  lib_count=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['add_external_count'])")
  [ "$lib_count" -gt 300 ]

  idem_key=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['idempotency_key'])")
  [ -n "$idem_key" ]
  [ "${#idem_key}" -eq 64 ]

  status_field=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['status'])")
  [ "$status_field" = "ok" ]
}

# --- T19 fix: v2 library-context race + hardening (odd/tasks/decompiler-fidelity-audit.md) ---
# The first --variant v2 campaign (2026-09-28 07:20-07:32Z) re-extracted 5 modules' extracted/
# (rm -rf + unzip) WHILE other parallel workers built their -e list by scanning
# organized/*/extracted/LIB-INF/*.jar live — a race that could silently drop LIB-INF jars from
# some modules' library context. These tests cover the fix's 9 requirements.

@test "sourcing n5-decompile.sh does not execute main() (needed so the unit tests below can source it safely)" {
  run bash -c "cd '$REPO_ROOT' && N5_MODULES_DIR=/nonexistent N5_OUT_DIR='$BATS_TEST_TMPDIR/sourceguard' source tools/n5-decompile.sh && echo SOURCED_OK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"SOURCED_OK"* ]]
}

@test "--prepare-libcache populates organized/_v2-libcache keyed by the nested LIB-INF jar's own sha256" {
  local_dir="$BATS_TEST_TMPDIR/v2fix1"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "commons-x-1.0.jar"
  make_fake_jar "$local_dir/modules/modB.jar" Tridium ""
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  count=$(find "$local_dir/out/_v2-libcache" -maxdepth 1 -name '*.jar' 2>/dev/null | wc -l)
  [ "$count" -eq 1 ]
  f=$(find "$local_dir/out/_v2-libcache" -maxdepth 1 -name '*.jar')
  base="$(basename "$f" .jar)"
  actual="$(sha256sum "$f" | awk '{print $1}')"
  [ "$base" = "$actual" ]
}

@test "--prepare-libcache scans bin/ext recursively (nested subdirectories), matching compute_v2_library_jars' own bin/ext scan" {
  local_dir="$BATS_TEST_TMPDIR/v2fix1b"
  mkdir -p "$local_dir/modules" "$local_dir/binext/nested" "$local_dir/out"
  make_fake_jar "$local_dir/binext/nested/deep.jar" Tridium "nested-lib-1.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR="$local_dir/binext" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  count=$(find "$local_dir/out/_v2-libcache" -maxdepth 1 -name '*.jar' 2>/dev/null | wc -l)
  [ "$count" -eq 1 ]
  grep -q "binext/nested/deep.jar" "$local_dir/out/_v2-libcache/_source_shas.tsv"
}

@test "compute_v2_library_jars reads LIB-INF context from the libcache, never from a live organized/*/extracted/ tree" {
  local_dir="$BATS_TEST_TMPDIR/v2fix2"
  mkdir -p "$local_dir/modules" "$local_dir/binext" "$local_dir/out/_v2-libcache" \
    "$local_dir/out/staleMod/extracted/LIB-INF"
  echo fake > "$local_dir/out/_v2-libcache/cafef00dcafef00dcafef00dcafef00dcafef00dcafef00dcafef00dcafef00.jar"
  echo stale > "$local_dir/out/staleMod/extracted/LIB-INF/stale-lib.jar"
  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_BIN_EXT_DIR='$local_dir/binext' N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_BIN_EXT_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    compute_v2_library_jars
    printf '%s\n' \"\${V2_ALL_LIB_JARS[@]}\"
  "
  [ "$status" -eq 0 ]
  [[ "$output" == *"_v2-libcache/cafef00d"* ]]
  [[ "$output" != *"stale-lib.jar"* ]]
}

@test "changing N5_JDK25_HOME changes the recorded idempotency key and forces a redo, jar sha256 unchanged" {
  key_before=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['idempotency_key'])")
  cmd_count_before=$(grep -c '^CMD:' "$N5_OUT_DIR/_logs/$MODULE.v2.log")
  sleep 1
  N5_JDK25_HOME="$BATS_TEST_TMPDIR/alt-jdk-home" "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE" || true
  cmd_count_after=$(grep -c '^CMD:' "$N5_OUT_DIR/_logs/$MODULE.v2.log")
  [ "$cmd_count_after" -gt "$cmd_count_before" ]
  key_after=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['idempotency_key'])")
  [ "$key_before" != "$key_after" ]
  sha_after=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['jar_sha256'])")
  expected_sha=$(sha256sum "$N5_MODULES_DIR/$MODULE.jar" | awk '{print $1}')
  [ "$sha_after" = "$expected_sha" ]
  # restore canonical (default-JDK-home) v2 state so later steady-state-idempotency tests are
  # unaffected by this test's deliberate mutation
  "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE"
}

@test "--variant v2 --force redoes the decompile but does not re-extract when extracted/ already matches the jar" {
  before_marker=$(cat "$N5_OUT_DIR/$MODULE/extracted/.jar_sha256" 2>/dev/null || true)
  [ -n "$before_marker" ]
  before_extract_mtime=$(stat -c %Y "$N5_OUT_DIR/$MODULE/extracted/.jar_sha256")
  lines_before=$(wc -l < "$N5_OUT_DIR/_logs/$MODULE.log")
  sleep 1
  run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 --force "$MODULE"
  [ "$status" -eq 0 ]
  after_extract_mtime=$(stat -c %Y "$N5_OUT_DIR/$MODULE/extracted/.jar_sha256")
  [ "$before_extract_mtime" -eq "$after_extract_mtime" ]
  new_lines=$(tail -n +"$((lines_before + 1))" "$N5_OUT_DIR/_logs/$MODULE.log")
  [[ "$new_lines" == *"v2 reusing existing extracted"* ]]
  [[ "$new_lines" != *"v2 extracting"* ]]
}

@test "fallback2/ is cleared at the start of each v2 run" {
  mkdir -p "$N5_OUT_DIR/$MODULE/fallback2"
  touch "$N5_OUT_DIR/$MODULE/fallback2/STALE_MARKER.java"
  run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 --force "$MODULE"
  [ "$status" -eq 0 ]
  [ ! -e "$N5_OUT_DIR/$MODULE/fallback2/STALE_MARKER.java" ]
}

@test "--variant v2 records status=failed and exits non-zero when both Vineflower and CFR fail, and never caches it as done" {
  out="$BATS_TEST_TMPDIR/organized_bothfail"
  mkdir -p "$out"
  ln -s "$N5_OUT_DIR/_v2-libcache" "$out/_v2-libcache"
  N5_OUT_DIR="$out" N5_VINEFLOWER="$BATS_TEST_TMPDIR/no-such-vineflower.jar" \
    N5_CFR="$BATS_TEST_TMPDIR/no-such-cfr.jar" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE"
  [ "$status" -ne 0 ]
  status_field=$(python3 -c "import json;print(json.load(open('$out/$MODULE/recon.json'))['v2']['status'])")
  [ "$status_field" = "failed" ]

  cmd_count_before=$(grep -c '^CMD:' "$out/_logs/$MODULE.v2.log")
  N5_OUT_DIR="$out" N5_VINEFLOWER="$BATS_TEST_TMPDIR/no-such-vineflower.jar" \
    N5_CFR="$BATS_TEST_TMPDIR/no-such-cfr.jar" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE"
  [ "$status" -ne 0 ]
  cmd_count_after=$(grep -c '^CMD:' "$out/_logs/$MODULE.v2.log")
  [ "$cmd_count_after" -gt "$cmd_count_before" ]
}

@test "write_recon_v2 is safe against Python string-literal injection via N5_JDK25_HOME" {
  out="$BATS_TEST_TMPDIR/organized_inject"
  mkdir -p "$out"
  ln -s "$N5_OUT_DIR/_v2-libcache" "$out/_v2-libcache"
  malicious="/tmp/pwn\"; import os; os.system('touch $BATS_TEST_TMPDIR/PWNED'); x=\""
  N5_OUT_DIR="$out" N5_JDK25_HOME="$malicious" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE"
  [ ! -f "$BATS_TEST_TMPDIR/PWNED" ]
  runtime=$(python3 -c "import json;print(json.load(open('$out/$MODULE/recon.json'))['v2']['include_runtime'])")
  [ "$runtime" = "$malicious" ]
}

@test "a library jar path containing ',' fails loudly instead of corrupting Vineflower's -e CSV list" {
  local_dir="$BATS_TEST_TMPDIR/v2fix3"
  mkdir -p "$local_dir/modules" "$local_dir/binext,with,commas" "$local_dir/out"
  make_fake_jar "$local_dir/modules/goodmod.jar" Tridium ""
  make_fake_jar "$local_dir/binext,with,commas/evil.jar" Tridium ""
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR="$local_dir/binext,with,commas" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR="$local_dir/binext,with,commas" N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 goodmod
  [ "$status" -ne 0 ]
  [[ "$output" == *"','"* ]]
}

@test "a library jar path containing ':' fails loudly instead of corrupting CFR's --extraclasspath list" {
  local_dir="$BATS_TEST_TMPDIR/v2fix4"
  mkdir -p "$local_dir/modules" "$local_dir/binext:colon" "$local_dir/out"
  make_fake_jar "$local_dir/modules/goodmod.jar" Tridium ""
  make_fake_jar "$local_dir/binext:colon/evil.jar" Tridium ""
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR="$local_dir/binext:colon" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR="$local_dir/binext:colon" N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 goodmod
  [ "$status" -ne 0 ]
  [[ "$output" == *"':'"* ]]
}

@test "the module's own jar is excluded from -e even when reachable via a different (symlinked) path" {
  local_dir="$BATS_TEST_TMPDIR/v2fix5"
  mkdir -p "$local_dir/modules" "$local_dir/binext" "$local_dir/out"
  make_fake_jar "$local_dir/modules/selfmod.jar" Tridium ""
  ln -s "$local_dir/modules/selfmod.jar" "$local_dir/binext/selfmod-alias.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR="$local_dir/binext" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_BIN_EXT_DIR='$local_dir/binext' N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_BIN_EXT_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    compute_v2_library_jars
    build_v2_external_lists '$local_dir/modules/selfmod.jar'
    echo \"COUNT=\$V2_LIB_COUNT\"
    printf '%s\n' \"\${V2_LIB_ARRAY[@]}\"
  "
  [ "$status" -eq 0 ]
  [[ "$output" == *"COUNT=0"* ]]
  [[ "$output" != *"selfmod.jar"* ]]
}

@test "--variant v2 <module> fails loudly with a clear message when the libcache was never prepared" {
  local_dir="$BATS_TEST_TMPDIR/v2fix6"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/nolibcache.jar" Tridium ""
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 nolibcache
  [ "$status" -ne 0 ]
  [[ "$output" == *"--prepare-libcache"* ]]
}

@test "--variant v2 is idempotent (rerunning without --force skips)" {
  before=$(stat -c %Y "$N5_OUT_DIR/$MODULE/recon.json")
  sleep 1
  run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE"
  [ "$status" -eq 0 ]
  after=$(stat -c %Y "$N5_OUT_DIR/$MODULE/recon.json")
  [ "$before" -eq "$after" ]
}

@test "--variant v2 with no module and no --all is a usage error, not a silent bulk run" {
  run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2
  [ "$status" -ne 0 ]
}

@test "--variant v3 (unimplemented) is rejected, not silently ignored" {
  run "$REPO_ROOT/tools/n5-decompile.sh" --variant v3 "$MODULE"
  [ "$status" -ne 0 ]
}

@test "--variant v2 CFR fallback receives --extraclasspath of the same library set (forced primary failure)" {
  out="$BATS_TEST_TMPDIR/organized"
  mkdir -p "$out"
  ln -s "$N5_OUT_DIR/_v2-libcache" "$out/_v2-libcache"
  N5_OUT_DIR="$out" N5_VINEFLOWER="$BATS_TEST_TMPDIR/no-such-vineflower.jar" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 "$MODULE"
  [ -d "$out/$MODULE/fallback2" ]
  cfr_cmd_line="$(grep '^CMD:' "$out/_logs/$MODULE.v2.log" | grep 'cfr' | head -1)"
  [[ -n "$cfr_cmd_line" ]]
  [[ "$cfr_cmd_line" == *"--extraclasspath"* ]]
}

@test "rerunning without --force is idempotent (skips, does not re-extract)" {
  before=$(stat -c %Y "$N5_OUT_DIR/$MODULE/recon.json")
  sleep 1
  run "$REPO_ROOT/tools/n5-decompile.sh" "$MODULE"
  [ "$status" -eq 0 ]
  after=$(stat -c %Y "$N5_OUT_DIR/$MODULE/recon.json")
  [ "$before" -eq "$after" ]
}

@test "--force redoes the module even though the sha256 is unchanged" {
  run "$REPO_ROOT/tools/n5-decompile.sh" --force "$MODULE"
  [ "$status" -eq 0 ]
  [ -f "$N5_OUT_DIR/$MODULE/recon.json" ]
}

# --- bin/ext classification + decompile (separate from the module fixture above) ---

@test "n5-classify-binext.py: a known Tridium bin/ext jar is included" {
  N5_BIN_EXT_DIR="${N5_BIN_EXT_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext}"
  jar="$N5_BIN_EXT_DIR/nre.jar"
  [[ -f "$jar" ]] || skip "bin/ext not available at $N5_BIN_EXT_DIR"
  run python3 "$REPO_ROOT/tools/n5-classify-binext.py" "$jar"
  [ "$status" -eq 0 ]
  [[ "$output" == include* ]]
}

@test "n5-classify-binext.py: a known third-party bin/ext jar is skipped" {
  N5_BIN_EXT_DIR="${N5_BIN_EXT_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext}"
  jar="$N5_BIN_EXT_DIR/kotlin-stdlib-2.4.10.jar"
  [[ -f "$jar" ]] || skip "bin/ext not available at $N5_BIN_EXT_DIR"
  run python3 "$REPO_ROOT/tools/n5-classify-binext.py" "$jar"
  [ "$status" -eq 1 ]
  [[ "$output" == skip* ]]
}

@test "--bin-ext decompiles only Tridium-owned jars into organized/_bin-ext/" {
  N5_BIN_EXT_DIR="${N5_BIN_EXT_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext}"
  [[ -d "$N5_BIN_EXT_DIR" ]] || skip "bin/ext not available at $N5_BIN_EXT_DIR"
  export N5_BIN_EXT_DIR
  out="$BATS_TEST_TMPDIR/organized"
  N5_OUT_DIR="$out" "$REPO_ROOT/tools/n5-decompile.sh" --bin-ext
  [ -f "$out/_bin-ext/nre/recon.json" ]
  # third-party jars must never appear as decompiled output dirs
  [ ! -d "$out/_bin-ext/kotlin-stdlib-2.4.10" ]
}

# --- vendor filter (modules/ only): non-Tridium jars must never be decompiled ---

@test "a non-Tridium-vendor jar in modules/ is excluded, not decompiled" {
  jar="$N5_MODULES_DIR/n5Hello.jar"
  [[ -f "$jar" ]] || skip "n5Hello.jar not present in $N5_MODULES_DIR (already cleaned up)"
  out="$BATS_TEST_TMPDIR/organized"
  N5_OUT_DIR="$out" "$REPO_ROOT/tools/n5-decompile.sh" n5Hello
  [ ! -d "$out/n5Hello" ]
}

@test "a Tridium-vendor jar in modules/ is not excluded" {
  run python3 -c "
import subprocess
print(subprocess.run(['unzip','-p','$N5_MODULES_DIR/$MODULE.jar','META-INF/module.xml'],
      capture_output=True, text=True).stdout)
"
  [[ "$output" == *'vendor="Tridium"'* ]]
}

@test "--scan-markers finds an INDENTED Vineflower failure marker (regression: andoverAC256/backup)" {
  local d="$BATS_TEST_TMPDIR/vf"
  mkdir -p "$d/pkg"
  printf 'class A {\n  Object getValueAt(int r) {\n         // $VF: Couldn'"'"'t be decompiled\n  }\n}\n' > "$d/pkg/A.java"
  printf 'class B { String s = "ok"; }\n' > "$d/pkg/B.java"
  run "$REPO_ROOT/tools/n5-decompile.sh" --scan-markers "$d"
  [ "$status" -eq 0 ]
  [[ "$output" == *"pkg/A.java"* ]]
  [[ "$output" != *"pkg/B.java"* ]]
}
