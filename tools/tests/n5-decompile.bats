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
