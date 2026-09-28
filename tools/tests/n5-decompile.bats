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
  # Orchestrator note (2026-09-28): reading ~440 jars from /mnt/c (WSL 9p) is
  # the main slowdown for decompile/grade runs. A sha256-verified local
  # mirror (spot-checked against known recon.json sha256s this session)
  # exists at $mirror — prefer it when present, falling back to the original
  # read-only Windows-side mount otherwise. Byte-identical, so every test
  # assertion is unaffected; only wall-clock time changes.
  local mirror="/home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28"
  if [[ -d "$mirror/modules" ]]; then
    N5_MODULES_DIR="${N5_MODULES_DIR:-$mirror/modules}"
    N5_BIN_EXT_DIR="${N5_BIN_EXT_DIR:-$mirror/bin-ext}"
  else
    N5_MODULES_DIR="${N5_MODULES_DIR:-/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules}"
    N5_BIN_EXT_DIR="${N5_BIN_EXT_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext}"
  fi
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

  export N5_MODULES_DIR N5_BIN_EXT_DIR N5_OUT_DIR="$BATS_FILE_TMPDIR/organized"
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

  # One shared --variant cons run (T22, niagara5-block118.md §118.1's
  # conservative + line-mapped view), reused by every cons-flag-assertion test
  # below, same sharing rationale as v2's above.
  N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}" \
    "$REPO_ROOT/tools/n5-decompile.sh" --variant cons "$MODULE" > "$BATS_FILE_TMPDIR/cons_run.log" 2>&1
  echo "$?" > "$BATS_FILE_TMPDIR/cons_run_status"
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

# Like make_fake_jar, but with caller-controlled marker CONTENT (not just the
# destination path) so a test can produce two jars at the SAME path with
# deliberately DIFFERENT bytes/sha256 (T19-hardening fix 1: a source jar
# changed at the same manifest path must be re-hashed, not trusted from cache).
make_versioned_jar() {
  local dest="$1" vendor="${2:-Tridium}" content="$3"
  python3 - "$dest" "$vendor" "$content" <<'PY'
import sys, zipfile
dest, vendor, content = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", f'<module vendor="{vendor}"/>')
    z.writestr("marker.txt", content)
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

# --- --variant cons (B118 §118.1's conservative + line-mapped view, T22) ---
# Reuses v2's entire library-context machinery; only the flag set, output
# dirs (vineflower-cons/+fallback-cons/), and recon.json's "cons" key differ.

@test "--variant cons exits 0 and produces vineflower-cons/ output" {
  status="$(cat "$BATS_FILE_TMPDIR/cons_run_status")"
  [ "$status" -eq 0 ]
  count=$(find "$N5_OUT_DIR/$MODULE/vineflower-cons" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -ge 1 ]
}

@test "--variant cons passes the B118 conservative flags, all false/resugaring-off except bytecode-source-mapping, before -e" {
  cmd_line="$(grep '^CMD:' "$N5_OUT_DIR/_logs/$MODULE.cons.log" | head -1)"
  [[ -n "$cmd_line" ]]
  for flag in '--pattern-matching=false' '--decompile-switch-expressions=false' '--ternary-in-if=false' \
      '--prettify-ifs=false' '--inline-simple-lambdas=false' '--bytecode-source-mapping=true' \
      '--__dump_original_lines__=true'; do
    [[ "$cmd_line" == *"$flag"* ]]
  done
  # every Additional option must precede -e (the same undocumented Vineflower
  # ordering requirement v2 already guards against)
  before_e="${cmd_line%%-e=*}"
  [[ "$before_e" == *"--bytecode-source-mapping=true"* ]]
  [[ "$before_e" == *"--__dump_original_lines__=true"* ]]
}

@test "--variant cons command line has no Vineflower 'missing ... ignored' parse-order warnings" {
  run grep -c 'warn: missing' "$N5_OUT_DIR/_logs/$MODULE.cons.log"
  [ "$status" -ne 0 ]
  [ "$output" -eq 0 ]
}

@test "--variant cons does not touch v1's vineflower/ or v2's vineflower2/ output" {
  find "$N5_OUT_DIR/$MODULE/vineflower" -name '*.java' | sort | xargs -r sha256sum \
    > "$BATS_TEST_TMPDIR/v1_hashes_after_cons.txt"
  diff "$BATS_FILE_TMPDIR/v1_vineflower_hashes_before.txt" "$BATS_TEST_TMPDIR/v1_hashes_after_cons.txt"
  count=$(find "$N5_OUT_DIR/$MODULE/vineflower2" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -ge 1 ]
}

@test "recon.json keeps its v1 AND v2 fields and gains a separate cons sub-object" {
  v2_status=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['status'])")
  [ "$v2_status" = "ok" ]

  cons_variant=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['cons']['variant'])")
  [ "$cons_variant" = "cons" ]

  cons_sha=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['cons']['jar_sha256'])")
  expected_sha=$(sha256sum "$N5_MODULES_DIR/$MODULE.jar" | awk '{print $1}')
  [ "$cons_sha" = "$expected_sha" ]

  cons_status=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['cons']['status'])")
  [ "$cons_status" = "ok" ]

  # v2 and cons idempotency keys must differ (different flags -> different key)
  v2_key=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['v2']['idempotency_key'])")
  cons_key=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['cons']['idempotency_key'])")
  [ "$v2_key" != "$cons_key" ]

  cons_flags_pm=$(python3 -c "import json;print(json.load(open('$N5_OUT_DIR/$MODULE/recon.json'))['cons']['flags']['pattern_matching'])")
  [ "$cons_flags_pm" = "False" ]
}

@test "--variant cons is idempotent (rerunning without --force skips)" {
  before=$(stat -c %Y "$N5_OUT_DIR/$MODULE/recon.json")
  sleep 1
  run "$REPO_ROOT/tools/n5-decompile.sh" --variant cons "$MODULE"
  [ "$status" -eq 0 ]
  after=$(stat -c %Y "$N5_OUT_DIR/$MODULE/recon.json")
  [ "$before" -eq "$after" ]
}

# --- --extra-tridium (T22): the 10 out-of-pipeline Tridium jars (B117 §117.4)
# and the Tridium-owned nested LIB-INF jars (B117 §117.2) ---

@test "run_extra_tridium classifies mechanically via the existing >50% Tridium-namespace rule and routes etc-m2 vs lib into separate output roots (synthetic fixtures)" {
  local_dir="$BATS_TEST_TMPDIR/extra1"
  mkdir -p "$local_dir/modules" "$local_dir/etc-m2/com/tridium/tools/foo/1.0" "$local_dir/lib" "$local_dir/out"
  # T23: --prepare-libcache refuses a zero-jar scan, so every fixture needs one module jar.
  make_fake_jar "$local_dir/modules/modA.jar" Tridium ""
  # a real >50%-Tridium jar (classify only inspects the zip namelist, not bytecode)
  python3 - "$local_dir/etc-m2/com/tridium/tools/foo/1.0/foo-1.0.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("com/tridium/foo/A.class", b"stub")
    z.writestr("com/tridium/foo/B.class", b"stub")
PY
  python3 - "$local_dir/lib/bar-1.0.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("com/tridium/bar/A.class", b"stub")
PY
  # a third-party (non-Tridium) jar that must be SKIPPED
  python3 - "$local_dir/etc-m2/com/tridium/tools/foo/1.0/thirdparty-1.0.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("org/apache/Thing.class", b"stub")
PY
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_ETC_M2_DIR="$local_dir/etc-m2" N5_LIB_DIR="$local_dir/lib" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --extra-tridium
  [ -d "$local_dir/out/_etc-m2/foo-1.0" ]
  [ -d "$local_dir/out/_lib/bar-1.0" ]
  [ ! -d "$local_dir/out/_etc-m2/thirdparty-1.0" ]
  [ -f "$local_dir/out/_etc-m2/foo-1.0/recon.json" ]
  language=$(python3 -c "import json;print(json.load(open('$local_dir/out/_etc-m2/foo-1.0/recon.json'))['language'])")
  [ "$language" = "java" ]
}

@test "run_extra_tridium_libinf routes a Tridium-owned nested LIB-INF jar into organized/<mod>/lib-inf/<stem>/" {
  local_dir="$BATS_TEST_TMPDIR/extra2"
  mkdir -p "$local_dir/modules" "$local_dir/out/somemod/extracted/LIB-INF"
  # T23: --prepare-libcache refuses a zero-jar scan, so every fixture needs one module jar.
  make_fake_jar "$local_dir/modules/modA.jar" Tridium ""
  python3 - "$local_dir/out/somemod/extracted/LIB-INF/tridiumlib-1.0.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("com/tridium/x/A.class", b"stub")
PY
  python3 - "$local_dir/out/somemod/extracted/LIB-INF/thirdparty-2.0.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("org/apache/Thing.class", b"stub")
PY
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_ETC_M2_DIR=/nonexistent N5_LIB_DIR=/nonexistent \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --extra-tridium
  [ -d "$local_dir/out/somemod/lib-inf/tridiumlib-1.0" ]
  [ ! -d "$local_dir/out/somemod/lib-inf/thirdparty-2.0" ]
}

@test "--extra-tridium on the real corpus: a small out-of-pipeline etc/m2 jar decompiles (v2+cons) and n-conv-plugin is flagged Kotlin" {
  real_etc_m2="/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository"
  [[ -d "$real_etc_m2" ]] || skip "etc/m2 not available at $real_etc_m2"
  filetypes_jar="$(find "$real_etc_m2/com/tridium/tools/filetypes" -name '*.jar' -print -quit 2>/dev/null)"
  [[ -n "$filetypes_jar" ]] || skip "filetypes jar not found under $real_etc_m2"
  ncp_jar="$(find "$real_etc_m2/com/tridium/tools/n-conv-plugin" -name '*.jar' -print -quit 2>/dev/null)"
  [[ -n "$ncp_jar" ]] || skip "n-conv-plugin jar not found under $real_etc_m2"

  out="$BATS_TEST_TMPDIR/organized_extra_real"
  mkdir -p "$out"
  ln -s "$N5_OUT_DIR/_v2-libcache" "$out/_v2-libcache"
  local_etc="$BATS_TEST_TMPDIR/etc-m2-subset"
  mkdir -p "$local_etc/filetypes" "$local_etc/n-conv-plugin"
  cp "$filetypes_jar" "$local_etc/filetypes/"
  cp "$ncp_jar" "$local_etc/n-conv-plugin/"

  N5_OUT_DIR="$out" N5_ETC_M2_DIR="$local_etc" N5_LIB_DIR=/nonexistent \
    "$REPO_ROOT/tools/n5-decompile.sh" --extra-tridium
  status=$?
  [ "$status" -eq 0 ]

  ft_stem="$(basename "$filetypes_jar" .jar)"
  [ -f "$out/_etc-m2/$ft_stem/recon.json" ]
  ft_v2_status=$(python3 -c "import json;print(json.load(open('$out/_etc-m2/$ft_stem/recon.json'))['v2']['status'])")
  [ "$ft_v2_status" = "ok" ]
  ft_cons_status=$(python3 -c "import json;print(json.load(open('$out/_etc-m2/$ft_stem/recon.json'))['cons']['status'])")
  [ "$ft_cons_status" = "ok" ]

  ncp_stem="$(basename "$ncp_jar" .jar)"
  ncp_lang=$(python3 -c "import json;print(json.load(open('$out/_etc-m2/$ncp_stem/recon.json'))['language'])")
  [ "$ncp_lang" = "kotlin" ]
}

@test "--extra-tridium on the real corpus: devkit's LIB-INF n-templates (Tridium-owned, non-Kotlin) decompiles into organized/devkit/lib-inf/" {
  [[ -f "$N5_OUT_DIR/devkit/extracted/LIB-INF/n-templates-5.0.54.9.2.jar" ]] \
    || skip "devkit not yet decompiled in this shared organized/ tree"
  out="$N5_OUT_DIR"
  N5_ETC_M2_DIR=/nonexistent N5_LIB_DIR=/nonexistent \
    "$REPO_ROOT/tools/n5-decompile.sh" --extra-tridium
  status=$?
  [ "$status" -eq 0 ]
  [ -f "$out/devkit/lib-inf/n-templates-5.0.54.9.2/recon.json" ]
  lang=$(python3 -c "import json;print(json.load(open('$out/devkit/lib-inf/n-templates-5.0.54.9.2/recon.json'))['language'])")
  [ "$lang" = "java" ]
  v2_status=$(python3 -c "import json;print(json.load(open('$out/devkit/lib-inf/n-templates-5.0.54.9.2/recon.json'))['v2']['status'])")
  [ "$v2_status" = "ok" ]
}

# --- --third-party-libinf (T26b, odd/tasks/decompiler-fidelity-audit.md): the complement of
# --extra-tridium's LIB-INF handling -- EVERY non-Tridium (n5-classify-binext.py verdict "skip")
# nested LIB-INF jar found directly in the SOURCE module/bin-ext jars (never organized/*/extracted/,
# which may not exist yet), decompiled ONCE per distinct jar sha256 with v2 settings into
# organized/_lib-inf-3p/<jar-stem>-<sha256[:12]>/{extracted,vineflower2,fallback2,recon.json}.
# T25's `missing_by_jar` (odd/tasks/decompiler-fidelity-audit.md) found this is almost the entire
# 11,719-class corpus-wide gap: prosys-opc-ua-sdk-client-server, poi-ooxml-lite, xmlbeans,
# kotlin-stdlib, ... none of them Tridium's own code.

# Compiles one trivial REAL class (javac, not a zipfile.writestr placeholder) into a standalone
# jar at $1 -- needed only by the idempotency test below: a garbage-bytes fixture (like every other
# fixture in this section) always fails BOTH decompilers, and T19 fix requirement 4 ("a module
# recorded status=failed is NEVER treated as up to date") means a failing decompile can never reach
# the idempotency skip branch this test wants to observe.
build_real_standalone_jar() {
  local dest="$1" class_name="$2" pkg="$3"
  local javac_bin="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}/bin/javac"
  [[ -x "$javac_bin" ]] || javac_bin="$(command -v javac)"
  local srcdir compiled_dir
  srcdir="$(mktemp -d)"
  compiled_dir="$(mktemp -d)"
  mkdir -p "$srcdir/$pkg"
  {
    [[ -n "$pkg" ]] && printf 'package %s;\n' "${pkg//\//.}"
    printf 'public class %s { public void m() { int x = 1; } }\n' "$class_name"
  } > "$srcdir/$pkg/$class_name.java"
  "$javac_bin" -d "$compiled_dir" "$srcdir/$pkg/$class_name.java"
  python3 - "$dest" "$compiled_dir" <<'PY'
import os, sys, zipfile
dest, compiled_dir = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(dest, "w") as z:
    for dirpath, _dirs, files in os.walk(compiled_dir):
        for f in files:
            if f.endswith(".class"):
                full = os.path.join(dirpath, f)
                z.write(full, os.path.relpath(full, compiled_dir))
PY
  rm -rf "$srcdir" "$compiled_dir"
}

@test "(a) run_third_party_libinf decompiles a non-Tridium LIB-INF jar into _lib-inf-3p/<stem>-<sha12>/ with recon.json population+found_in" {
  local_dir="$BATS_TEST_TMPDIR/libinf3p_a"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/base.jar" Tridium ""
  # 0 .class entries -> ratio 0.0, not > 0.5 -> n5-classify-binext.py verdict "skip" (third-party)
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "thirdparty-1.0.jar"

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --third-party-libinf

  sha=$(unzip -p "$local_dir/modules/modA.jar" "LIB-INF/thirdparty-1.0.jar" | sha256sum | awk '{print $1}')
  sha12="${sha:0:12}"
  moddir="$local_dir/out/_lib-inf-3p/thirdparty-1.0-$sha12"
  [ -d "$moddir" ]
  [ -f "$moddir/recon.json" ]
  pop=$(python3 -c "import json;print(json.load(open('$moddir/recon.json'))['population'])")
  [ "$pop" = "lib-inf-3p" ]
  jarsha=$(python3 -c "import json;print(json.load(open('$moddir/recon.json'))['jar_sha256'])")
  [ "$jarsha" = "$sha" ]
  found_in=$(python3 -c "import json;print(json.load(open('$moddir/recon.json'))['found_in'])")
  [[ "$found_in" == *"modA!LIB-INF/thirdparty-1.0.jar"* ]]
}

@test "(c) run_third_party_libinf does NOT handle a Tridium-owned nested LIB-INF jar (belongs to --extra-tridium)" {
  local_dir="$BATS_TEST_TMPDIR/libinf3p_c"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/base.jar" Tridium ""
  python3 - "$local_dir/modules/modA.jar" <<'PY'
import sys, zipfile, io
inner = io.BytesIO()
with zipfile.ZipFile(inner, "w") as iz:
    iz.writestr("com/tridium/x/A.class", b"stub")
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="Tridium"/>')
    z.writestr("LIB-INF/tridiumlib-1.0.jar", inner.getvalue())
PY

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --third-party-libinf
  # decompile-pipeline review fix (R3-004): this run's own exit status was
  # never asserted -- a regression where --third-party-libinf crashed
  # outright (before creating ANY output) would still leave the directory
  # below absent and make this test falsely pass.
  [ "$status" -eq 0 ]

  sha=$(unzip -p "$local_dir/modules/modA.jar" "LIB-INF/tridiumlib-1.0.jar" | sha256sum | awk '{print $1}')
  sha12="${sha:0:12}"
  [ ! -d "$local_dir/out/_lib-inf-3p/tridiumlib-1.0-$sha12" ]
}

@test "(b) run_third_party_libinf dedups a byte-identical LIB-INF jar embedded in two modules and lists both in found_in" {
  local_dir="$BATS_TEST_TMPDIR/libinf3p_b"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/base.jar" Tridium ""
  python3 - "$local_dir/inner.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("org/apache/Shared.class", b"stub")
PY
  for m in modA modB; do
    python3 - "$local_dir/modules/$m.jar" "$local_dir/inner.jar" <<'PY'
import sys, zipfile
dest, inner = sys.argv[1], sys.argv[2]
data = open(inner, "rb").read()
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="Tridium"/>')
    z.writestr("LIB-INF/shared-1.0.jar", data)
PY
  done

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --third-party-libinf

  sha=$(sha256sum "$local_dir/inner.jar" | awk '{print $1}')
  sha12="${sha:0:12}"
  dircount=$(find "$local_dir/out/_lib-inf-3p" -maxdepth 1 -name "shared-1.0-*" -type d | wc -l)
  [ "$dircount" -eq 1 ]
  moddir="$local_dir/out/_lib-inf-3p/shared-1.0-$sha12"
  [ -d "$moddir" ]
  found_in=$(python3 -c "import json;print(json.load(open('$moddir/recon.json'))['found_in'])")
  [[ "$found_in" == *"modA!LIB-INF/shared-1.0.jar"* ]]
  [[ "$found_in" == *"modB!LIB-INF/shared-1.0.jar"* ]]
}

@test "(d) run_third_party_libinf is idempotent: a rerun without --force skips the already-decompiled distinct jar" {
  local_dir="$BATS_TEST_TMPDIR/libinf3p_d"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/base.jar" Tridium ""
  build_real_standalone_jar "$local_dir/real-lib.jar" Widget org/example
  python3 - "$local_dir/modules/modA.jar" "$local_dir/real-lib.jar" <<'PY'
import sys, zipfile
dest, inner = sys.argv[1], sys.argv[2]
data = open(inner, "rb").read()
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="Tridium"/>')
    z.writestr("LIB-INF/example-lib-1.0.jar", data)
PY

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --third-party-libinf
  [ "$status" -eq 0 ]
  [[ "$output" == *"lib-inf-3p: decompiled=1 skipped-up-to-date=0 failed=0 distinct_jars=1"* ]]

  sha=$(sha256sum "$local_dir/real-lib.jar" | awk '{print $1}')
  sha12="${sha:0:12}"
  moddir="$local_dir/out/_lib-inf-3p/example-lib-1.0-$sha12"
  v2status=$(python3 -c "import json;print(json.load(open('$moddir/recon.json'))['v2']['status'])")
  [ "$v2status" = "ok" ]

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --third-party-libinf
  [ "$status" -eq 0 ]
  [[ "$output" == *"lib-inf-3p: decompiled=0 skipped-up-to-date=1 failed=0 distinct_jars=1"* ]]
}

@test "(e) run_third_party_libinf surfaces a genuinely corrupt LIB-INF entry instead of silently swallowing unzip's error (decompile-pipeline review: R3-002/R4-002)" {
  local_dir="$BATS_TEST_TMPDIR/libinf3p_e"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/base.jar" Tridium ""
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "thirdparty-1.0.jar"

  # Flip ONE byte inside the (ZIP_STORED, so length-preserving) nested
  # LIB-INF/thirdparty-1.0.jar entry's raw data -- the CENTRAL DIRECTORY and
  # every other entry (META-INF/module.xml, marker.txt) stay byte-identical
  # and readable; only this one entry now fails its own CRC-32 check. `unzip`
  # still WRITES it (with the bad bytes) and exits 2, not the ordinary
  # exit-11 "no matching files" every OTHER jar in this suite produces.
  python3 - "$local_dir/modules/modA.jar" <<'PY'
import sys, zipfile, struct
dest = sys.argv[1]
zf = zipfile.ZipFile(dest)
info = zf.getinfo("LIB-INF/thirdparty-1.0.jar")
zf.close()
header_offset = info.header_offset
with open(dest, "rb") as f:
    f.seek(header_offset)
    header = f.read(30)
fname_len, extra_len = struct.unpack("<HH", header[26:30])
data_offset = header_offset + 30 + fname_len + extra_len
with open(dest, "r+b") as f:
    f.seek(data_offset + 5)
    b = f.read(1)
    f.seek(data_offset + 5)
    f.write(bytes([b[0] ^ 0xFF]))
PY

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --third-party-libinf
  [ "$status" -eq 0 ]

  grep -q "WARNING: unzip exited 2 extracting LIB-INF" "$local_dir/out/_logs/_lib-inf-3p.log"
  grep -q "from modA " "$local_dir/out/_logs/_lib-inf-3p.log"
}

@test "(f) cache_source_jar_libinf (--prepare-libcache) surfaces a genuinely corrupt LIB-INF entry too, same as run_third_party_libinf's (e) -- both share ONE helper now (decompile-pipeline review: R2-duplicated-unzip-libinf-error-handling / R3-003)" {
  local_dir="$BATS_TEST_TMPDIR/libinf3p_f"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "thirdparty-1.0.jar"

  # Same byte-flip technique as (e) -- length-preserving, so only this one
  # nested LIB-INF entry's own CRC-32 check fails; unzip still WRITES it (bad
  # bytes) and exits 2, not the ordinary exit-11 every OTHER jar produces.
  python3 - "$local_dir/modules/modA.jar" <<'PY'
import sys, zipfile, struct
dest = sys.argv[1]
zf = zipfile.ZipFile(dest)
info = zf.getinfo("LIB-INF/thirdparty-1.0.jar")
zf.close()
header_offset = info.header_offset
with open(dest, "rb") as f:
    f.seek(header_offset)
    header = f.read(30)
fname_len, extra_len = struct.unpack("<HH", header[26:30])
data_offset = header_offset + 30 + fname_len + extra_len
with open(dest, "r+b") as f:
    f.seek(data_offset + 5)
    b = f.read(1)
    f.seek(data_offset + 5)
    f.write(bytes([b[0] ^ 0xFF]))
PY

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]

  grep -q "WARNING: unzip exited 2 extracting LIB-INF" "$local_dir/out/_logs/_prepare-libcache.log"
  grep -q "may be cached under a misleading sha256" "$local_dir/out/_logs/_prepare-libcache.log"
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

# --- T19-hardening (RDD review-56f32a364d16cec0, folded in under T22): 5 reproducibility
# holes in the v2 library-context machinery that --variant cons also reuses. ---

@test "T19h1: compute_v2_idempotency_key re-hashes a source jar whose content changed at the same manifest path, instead of trusting a stale cached sha256" {
  local_dir="$BATS_TEST_TMPDIR/t19h1"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_versioned_jar "$local_dir/modules/modA.jar" Tridium "a"
  make_versioned_jar "$local_dir/modules/modB.jar" Tridium "v1"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  key_before="$(bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_BIN_EXT_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    compute_v2_library_jars
    build_v2_external_lists '$local_dir/modules/modA.jar'
    build_v2_flags
    compute_v2_idempotency_key deadbeef vfsha cfrsha testflags
  ")"
  sleep 1
  # modB's content changes AT THE SAME PATH, WITHOUT re-running --prepare-libcache
  # (simulates a module jar upgraded between a manifest build and the next v2 run).
  make_versioned_jar "$local_dir/modules/modB.jar" Tridium "v2-different-content"
  key_after="$(bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_BIN_EXT_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    compute_v2_library_jars
    build_v2_external_lists '$local_dir/modules/modA.jar'
    build_v2_flags
    compute_v2_idempotency_key deadbeef vfsha cfrsha testflags
  ")"
  [ "$key_before" != "$key_after" ]
}

@test "T19h2a: an interrupted --prepare-libcache (missing completion marker) is never treated as ready by --variant v2" {
  local_dir="$BATS_TEST_TMPDIR/t19h2a"
  mkdir -p "$local_dir/modules" "$local_dir/out/_v2-libcache"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium ""
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 modA
  [ "$status" -ne 0 ]
  [[ "$output" == *"--prepare-libcache"* ]]
}

@test "T19h2b: --prepare-libcache writes a completion marker whose recorded count matches the cache's actual jar count" {
  local_dir="$BATS_TEST_TMPDIR/t19h2b"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "libx-1.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  [ -f "$local_dir/out/_v2-libcache/.complete" ]
  recorded=$(grep -o 'count=[0-9]*' "$local_dir/out/_v2-libcache/.complete" | cut -d= -f2)
  actual=$(find "$local_dir/out/_v2-libcache" -maxdepth 1 -name '*.jar' | wc -l)
  [ "$recorded" -eq "$actual" ]
}

@test "T23a: --prepare-libcache refuses an empty source-jar scan and leaves an existing ready cache untouched" {
  local_dir="$BATS_TEST_TMPDIR/t23a"
  mkdir -p "$local_dir/modules" "$local_dir/empty" "$local_dir/out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "libx-1.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  before=$(cat "$local_dir/out/_v2-libcache/.complete" "$local_dir/out/_v2-libcache/_current_entries.tsv" | sha256sum)
  # A mistyped / unmounted modules dir scans zero jars: that must be a typed
  # failure, never a "complete" cache that strips every LIB-INF jar from the
  # later decompiles' -e= context.
  N5_MODULES_DIR="$local_dir/empty" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -ne 0 ]
  [[ "$output" == *"no source jars"* ]]
  after=$(cat "$local_dir/out/_v2-libcache/.complete" "$local_dir/out/_v2-libcache/_current_entries.tsv" | sha256sum)
  [ "$before" = "$after" ]
}

@test "T19h2c: a stale completion marker (count mismatch against actual cache contents) is treated as not-ready" {
  local_dir="$BATS_TEST_TMPDIR/t19h2c"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "libx-1.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  f=$(find "$local_dir/out/_v2-libcache" -maxdepth 1 -name '*.jar' | head -1)
  rm -f "$f"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_JDK25_HOME="$BATS_TEST_TMPDIR/fake-jdk" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 modA
  [ "$status" -ne 0 ]
  [[ "$output" == *"--prepare-libcache"* ]]
}

@test "T19h3: compute_v2_library_jars excludes libcache entries no longer referenced by any current source jar (pruned from the active set, not physically deleted)" {
  local_dir="$BATS_TEST_TMPDIR/t19h3"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "libx-1.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  old_entry=$(find "$local_dir/out/_v2-libcache" -maxdepth 1 -name '*.jar')
  [ -n "$old_entry" ]
  # modA's embedded lib is superseded by a different-content one (a version bump)
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "libx-2.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  [ -f "$old_entry" ]
  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_BIN_EXT_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    compute_v2_library_jars
    printf '%s\n' \"\${V2_ALL_LIB_JARS[@]}\"
  "
  [ "$status" -eq 0 ]
  [[ "$output" != *"$(basename "$old_entry")"* ]]
}

@test "T19h4a: ensure_extracted_for_v2 does not write the extraction-provenance marker when unzip fails" {
  local_dir="$BATS_TEST_TMPDIR/t19h4a"
  mkdir -p "$local_dir/moddir"
  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR=/nonexistent N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    ensure_extracted_for_v2 '$local_dir/does-not-exist.jar' '$local_dir/moddir' false fakemod v2
  "
  [ "$status" -ne 0 ]
  [ ! -f "$local_dir/moddir/extracted/.jar_sha256" ]
}

@test "T19h4b: ensure_extracted_for_v2 writes the marker on a real, complete extraction" {
  local_dir="$BATS_TEST_TMPDIR/t19h4b"
  mkdir -p "$local_dir/moddir"
  make_fake_jar "$local_dir/modA.jar" Tridium ""
  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR=/nonexistent N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    ensure_extracted_for_v2 '$local_dir/modA.jar' '$local_dir/moddir' false modA v2
  "
  [ "$status" -eq 0 ]
  [ -f "$local_dir/moddir/extracted/.jar_sha256" ]
}

@test "T19h4c: ensure_extracted_for_v2 fails and withholds the marker when extracted/ ends up with fewer .class files than the jar lists (partial extraction, unzip still exits 0)" {
  local_dir="$BATS_TEST_TMPDIR/t19h4c"
  mkdir -p "$local_dir/moddir" "$local_dir/fakebin"
  python3 - "$local_dir/modA.jar" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1], "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="Tridium"/>')
    z.writestr("a/A.class", b"stub")
    z.writestr("a/B.class", b"stub")
PY
  cat > "$local_dir/fakebin/unzip" <<'SH'
#!/usr/bin/env bash
if [[ "$1" == "-l" ]]; then
  echo "  Length      Date    Time    Name"
  echo "a/A.class"
  echo "a/B.class"
  exit 0
fi
dest=""
prev=""
for a in "$@"; do
  if [[ "$prev" == "-d" ]]; then dest="$a"; fi
  prev="$a"
done
mkdir -p "$dest/META-INF"
echo stub > "$dest/META-INF/module.xml"
exit 0
SH
  chmod +x "$local_dir/fakebin/unzip"
  run bash -c "
    set -euo pipefail
    PATH='$local_dir/fakebin:'\$PATH
    N5_MODULES_DIR=/nonexistent N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_OUT_DIR PATH
    source '$REPO_ROOT/tools/n5-decompile.sh'
    ensure_extracted_for_v2 '$local_dir/modA.jar' '$local_dir/moddir' false modA v2
  "
  [ "$status" -ne 0 ]
  [ ! -f "$local_dir/moddir/extracted/.jar_sha256" ]
}

@test "T19h5: prepare_v2_libcache uses one shared LIB-INF caching helper for modules/ and bin/ext/ (no duplicated scan loop)" {
  count=$(grep -c "unzip -o -q \"\$jar\" 'LIB-INF/\*\.jar'" "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$count" -le 1 ]
}

@test "T19h6: v2_libcache_ready/compute_v2_library_jars/prepare_v2_libcache tolerate a symlinked _v2-libcache/ (GNU find -P silently returns 0 on a symlinked starting arg without -L)" {
  local_dir="$BATS_TEST_TMPDIR/t19h6"
  mkdir -p "$local_dir/modules" "$local_dir/real-out"
  make_fake_jar "$local_dir/modules/modA.jar" Tridium "libx-1.0.jar"
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/real-out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  real_count=$(find "$local_dir/real-out/_v2-libcache" -maxdepth 1 -name '*.jar' | wc -l)
  [ "$real_count" -ge 1 ]

  # a SECOND N5_OUT_DIR whose _v2-libcache is a SYMLINK to the first — this is
  # exactly the shape tools/tests/n5-decompile.bats' own "real corpus" tests
  # use (ln -s "$N5_OUT_DIR/_v2-libcache" "$out/_v2-libcache") to share one
  # prepared cache across an isolated per-test output dir.
  mkdir -p "$local_dir/symlinked-out"
  ln -s "$local_dir/real-out/_v2-libcache" "$local_dir/symlinked-out/_v2-libcache"

  run bash -c "
    set -euo pipefail
    N5_OUT_DIR='$local_dir/symlinked-out'
    export N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'
    v2_libcache_ready && echo READY || echo NOT_READY
  "
  [ "$status" -eq 0 ]
  [[ "$output" == *"READY"* ]]
  [[ "$output" != *"NOT_READY"* ]]

  # rerunning --prepare-libcache through the symlink must not corrupt the
  # shared real cache's .complete count (the bug this test guards: it used to
  # silently rebuild with a "scanned 0" view of the same jars and overwrite
  # .complete with count=0 while leaving the physical jar files untouched).
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/symlinked-out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  recorded=$(grep -o 'count=[0-9]*' "$local_dir/real-out/_v2-libcache/.complete" | cut -d= -f2)
  [ "$recorded" -eq "$real_count" ]
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

# --- T24 (odd/tasks/decompiler-fidelity-audit.md): isolate the class(es) that
# hang a whole-jar Vineflower run instead of losing the WHOLE module to CFR
# (bajaui: 832 classes, all 566 top-level sources CFR because ONE local-record
# class, com/tridium/ui/theme/custom/nss/query/NSS2SelectionResult, hangs
# Vineflower's ClassWriter forever). Uses a FAKE Vineflower (N5_JAVA overridden
# to fake-vineflower-java.sh, which wraps fake-vineflower.py — see both files'
# headers for the exact double-dispatch: only a -jar target equal to
# $FAKE_VINEFLOWER_JAR is faked; every real CFR invocation the script makes
# still runs the REAL tools/decompilers/cfr-0.152.jar against real compiled
# .class bytes) because a real Vineflower hang cannot be reproduced quickly or
# deterministically in a unit test. Real bajaui numbers are the orchestrator's
# separate real-corpus run (not part of this bats file — bajaui is not
# lontunnel-sized, decompiling it for real is a multi-minute campaign).

# Resolves the REAL java binary these tests' fake $N5_JAVA wrapper falls back
# to for every non-Vineflower invocation (i.e. every real CFR call). Uses the
# script's own hardcoded default first (same brew keg every other real-corpus
# test in this file already depends on) and falls back to whatever `java` is
# on PATH so this doesn't hard-fail on a machine without that exact keg.
t24_real_java() {
  local default="/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java"
  if [[ -x "$default" ]]; then
    printf '%s' "$default"
  else
    command -v java
  fi
}

# Points N5_JAVA/N5_VINEFLOWER at the T24 fake Vineflower double for the rest
# of the calling test. $FAKE_VINEFLOWER_JAR itself is never read as a jar (the
# wrapper only compares the -jar argument by path) — an empty placeholder file
# is enough, and its sha256 (n5-decompile.sh hashes N5_VINEFLOWER for
# recon.json/idempotency purposes) is stable and harmless.
t24_use_fake_vineflower() {
  FAKE_VINEFLOWER_JAR="$BATS_TEST_TMPDIR/fake-vineflower-marker.jar"
  : > "$FAKE_VINEFLOWER_JAR"
  FAKE_VINEFLOWER_PY="$REPO_ROOT/tools/tests/fixtures/fake-vineflower.py"
  REAL_JAVA="$(t24_real_java)"
  export FAKE_VINEFLOWER_JAR FAKE_VINEFLOWER_PY REAL_JAVA
  N5_JAVA="$REPO_ROOT/tools/tests/fixtures/fake-vineflower-java.sh"
  N5_VINEFLOWER="$FAKE_VINEFLOWER_JAR"
  export N5_JAVA N5_VINEFLOWER
}

# Builds a REAL module jar (real javac-compiled .class bytes, not
# zipfile.writestr placeholders) at $N5_MODULES_DIR/$1.jar, one trivial public
# top-level class per remaining "pkg/ClassName" argument. Real bytes are
# needed because T24's CFR fallback for a hung/excluded class is the REAL
# tools/decompilers/cfr-0.152.jar (see t24_use_fake_vineflower above) — it has
# to actually decompile something for the "hung class ends up in fallback/"
# assertions to mean anything. Uses N5_JDK25_HOME's javac (the JDK already a
# hard dependency of the --variant v2/cons real-corpus tests in this file) so
# no extra tool/install is required.
t24_build_module_jar() {
  local dest_name="$1" vendor="$2"; shift 2
  local javac_bin="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}/bin/javac"
  [[ -x "$javac_bin" ]] || javac_bin="$(command -v javac)"

  local srcdir compiled_dir
  srcdir="$(mktemp -d)"
  compiled_dir="$(mktemp -d)"
  local name pkg simple
  for name in "$@"; do
    pkg="$(dirname "$name")"
    [[ "$pkg" == "." ]] && pkg=""
    simple="$(basename "$name")"
    mkdir -p "$srcdir/$pkg"
    {
      [[ -n "$pkg" ]] && printf 'package %s;\n' "${pkg//\//.}"
      # A no-op method body (not just a field) so a class is a closer analog
      # of a real Tridium class than an empty marker type would be; nothing
      # about T24's isolation logic depends on WHAT a class does, only on
      # its internal name and whether Vineflower/CFR can round-trip it.
      printf 'public class %s { public void m() { int x = 1; } }\n' "$simple"
    } > "$srcdir/$pkg/$simple.java"
  done
  find "$srcdir" -name '*.java' -print0 | xargs -0 "$javac_bin" -d "$compiled_dir"

  mkdir -p "$N5_MODULES_DIR"
  python3 - "$N5_MODULES_DIR/$dest_name.jar" "$vendor" "$compiled_dir" <<'PY'
import os, sys, zipfile
dest, vendor, compiled_dir = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="%s"/>' % vendor)
    for dirpath, _dirs, files in os.walk(compiled_dir):
        for f in files:
            if f.endswith(".class"):
                full = os.path.join(dirpath, f)
                z.write(full, os.path.relpath(full, compiled_dir))
PY
  rm -rf "$srcdir" "$compiled_dir"
}

@test "T24a: one hung class -> ok_with_excluded, excluded_classes exact, primary tree keeps the rest, hung class in fallback (+ noinner secondary view)" {
  local_dir="$BATS_TEST_TMPDIR/t24a"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24a_mod Tridium pkgA/Alpha pkgA/Beta pkgB/Gamma pkgB/HangClass

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkgB/HangClass" \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24a_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24a_mod/recon.json"
  [ -f "$recon" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "ok_with_excluded" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_used'])")" = "True" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_reason'])")" = "primary_hang_isolated" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['excluded_classes'])")" = "['pkgB/HangClass']" ]
  attempt="$(python3 -c "import json;print(json.load(open('$recon'))['primary_timeout_attempt_seconds'])")"
  [ "$attempt" -ge 3 ]
  isolate_t="$(python3 -c "import json;print(json.load(open('$recon'))['isolate_time_seconds'])")"
  [ "$isolate_t" -ge 0 ]

  [ -f "$local_dir/out/t24a_mod/vineflower/pkgA/Alpha.java" ]
  [ -f "$local_dir/out/t24a_mod/vineflower/pkgA/Beta.java" ]
  [ -f "$local_dir/out/t24a_mod/vineflower/pkgB/Gamma.java" ]
  [ ! -f "$local_dir/out/t24a_mod/vineflower/pkgB/HangClass.java" ]

  [ -f "$local_dir/out/t24a_mod/fallback/pkgB/HangClass.java" ]

  # best-effort secondary view (T24 step 3): --decompile-inner=false never
  # hangs in the fake (see fake-vineflower.py), so this genuinely succeeds.
  [ -f "$local_dir/out/t24a_mod/vineflower-noinner/pkgB/HangClass.java" ]
}

@test "T24b: the excluded-classes regex does not over-match a sibling class (Foo hangs, FooBar and Baz must survive in the primary tree)" {
  local_dir="$BATS_TEST_TMPDIR/t24b"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24b_mod Tridium pkg/Foo pkg/FooBar pkg/Baz

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkg/Foo" \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24b_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24b_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "ok_with_excluded" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['excluded_classes'])")" = "['pkg/Foo']" ]

  [ -f "$local_dir/out/t24b_mod/vineflower/pkg/FooBar.java" ]
  [ -f "$local_dir/out/t24b_mod/vineflower/pkg/Baz.java" ]
  [ ! -f "$local_dir/out/t24b_mod/vineflower/pkg/Foo.java" ]
  [ -f "$local_dir/out/t24b_mod/fallback/pkg/Foo.java" ]
}

@test "T24c: nothing hangs individually but the whole jar times out -> old whole-module-CFR behavior kept, isolation_status explains why" {
  local_dir="$BATS_TEST_TMPDIR/t24c"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24c_mod Tridium pkgA/A1 pkgA/A2 pkgB/B1 pkgB/B2 pkgC/C1 pkgC/C2

  # 6 classes total; every package/class isolation subset this run can ever
  # build has at most 2 classes (well under the threshold) — only the whole
  # 6-class jar ever reaches it, so isolation MUST find zero hung classes.
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_MIN_CLASSES=5 \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24c_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24c_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "timeout" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_used'])")" = "True" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_reason'])")" = "primary_timeout_whole_module" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['isolation_status'])")" = "no_hung_class_found" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['excluded_classes'])")" = "[]" ]

  # old behavior: whole-module CFR, primary tree left empty
  count=$(find "$local_dir/out/t24c_mod/vineflower" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -eq 0 ]
  for c in pkgA/A1 pkgA/A2 pkgB/B1 pkgB/B2 pkgC/C1 pkgC/C2; do
    [ -f "$local_dir/out/t24c_mod/fallback/$c.java" ]
  done
}

@test "T24e: a top-level class with NO package (module-info-style, package '') doesn't crash isolation (regression: bash 5.2 'bad array subscript' on an empty associative-array key, found running this on the real bajaui corpus)" {
  local_dir="$BATS_TEST_TMPDIR/t24e"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  # "RootClass" has no '/' in its name -> package "" (t24_build_module_jar
  # compiles it with no package declaration, placing it at the jar root,
  # exactly like a real module-info.class).
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24e_mod Tridium RootClass pkg/Hang pkg/Other

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkg/Hang" \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24e_mod
  [ "$status" -eq 0 ]
  [[ "$output" != *"bad array subscript"* ]]

  recon="$local_dir/out/t24e_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "ok_with_excluded" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['excluded_classes'])")" = "['pkg/Hang']" ]
  [ -f "$local_dir/out/t24e_mod/vineflower/RootClass.java" ]
  [ -f "$local_dir/out/t24e_mod/vineflower/pkg/Other.java" ]
  [ -f "$local_dir/out/t24e_mod/fallback/pkg/Hang.java" ]
}

@test "T24f: a vineflower-noinner/ secondary view from an EARLIER hung run does not survive a rerun where nothing hangs (decompile-pipeline review: R3-stale-noinner-view-survives-rerun)" {
  local_dir="$BATS_TEST_TMPDIR/t24f"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24f_mod Tridium pkgA/Alpha pkgB/HangClass

  # run 1: HangClass hangs -> isolated -> vineflower-noinner/pkgB/HangClass.java
  # is genuinely produced, exactly like T24a.
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkgB/HangClass" \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24f_mod
  [ "$status" -eq 0 ]
  [ -f "$local_dir/out/t24f_mod/vineflower-noinner/pkgB/HangClass.java" ]

  # run 2 (--force, same module, no hang this time): the whole-jar primary
  # never times out, so vf_handle_primary_timeout/vf_render_noinner_view are
  # never called at all this run -- the fix must proactively clear the STALE
  # vineflower-noinner/ from run 1 instead of leaving it in place looking like
  # current output.
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --force t24f_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24f_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "ok" ]
  [ -f "$local_dir/out/t24f_mod/vineflower/pkgB/HangClass.java" ]
  [ ! -e "$local_dir/out/t24f_mod/vineflower-noinner/pkgB/HangClass.java" ]
  [ ! -d "$local_dir/out/t24f_mod/vineflower-noinner" ]
}

@test "T24g: the post-isolation excluded re-run itself failing keeps the old whole-module-CFR fallback exactly, isolation_status explains why (decompile-pipeline review: R3-excluded-rerun-failure-untested)" {
  local_dir="$BATS_TEST_TMPDIR/t24g"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24g_mod Tridium pkgA/Alpha pkgB/Hang

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkgB/Hang" FAKE_EXCLUDED_RERUN_FAIL=1 \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24g_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24g_mod/recon.json"
  # isolation DID find the hung class -- excluded_classes is not empty --
  # but the excluded re-run itself errored, so T24's fix must fall all the
  # way back to today's original whole-module CFR behavior, unchanged.
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['excluded_classes'])")" = "['pkgB/Hang']" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['isolation_status'])")" = "excluded_rerun_error" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "timeout" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_used'])")" = "True" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_reason'])")" = "primary_timeout_whole_module" ]

  count=$(find "$local_dir/out/t24g_mod/vineflower" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -eq 0 ]
  [ -f "$local_dir/out/t24g_mod/fallback/pkgA/Alpha.java" ]
  [ -f "$local_dir/out/t24g_mod/fallback/pkgB/Hang.java" ]
}

@test "T24h: the best-effort noinner secondary view failing must never abort the whole decompile under 'set -e' (decompile-pipeline review: R2-noinner-never-fails-contract)" {
  local_dir="$BATS_TEST_TMPDIR/t24h"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24h_mod Tridium pkgA/Alpha pkgB/HangClass

  # HangClass hangs, gets isolated, and the excluded re-run succeeds (like
  # T24a) -- but this time the best-effort --decompile-inner=false secondary
  # view itself fails (FAKE_NOINNER_FAIL=1). Under this script's own
  # `set -euo pipefail`, vf_render_noinner_view's call site was an unguarded
  # statement: a non-zero return there aborted the ENTIRE script instead of
  # being swallowed as the documented "best-effort ... never blocks the
  # module" behavior. The whole run must still exit 0 and still record
  # ok_with_excluded, exactly as if the noinner view had never been attempted.
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkgB/HangClass" FAKE_NOINNER_FAIL=1 \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24h_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24h_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "ok_with_excluded" ]
  [ -f "$local_dir/out/t24h_mod/vineflower/pkgA/Alpha.java" ]
  [ -f "$local_dir/out/t24h_mod/fallback/pkgB/HangClass.java" ]
  [ ! -f "$local_dir/out/t24h_mod/vineflower-noinner/pkgB/HangClass.java" ]
}

@test "T24i: N5_ISOLATE_TOTAL_BUDGET caps the WHOLE bisection and falls back to whole-module CFR when exhausted, with no partial hung-class list trusted (decompile-pipeline review: R4-isolation-unbounded-total-budget)" {
  local_dir="$BATS_TEST_TMPDIR/t24i"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24i_mod Tridium pkgA/Alpha pkgB/HangClass

  # N5_ISOLATE_TOTAL_BUDGET=0: the total-budget check at the top of the very
  # FIRST package iteration is already "elapsed(0) >= 0", so isolation gives
  # up before running even one package-subset probe -- deterministic and
  # fast, no real per-probe hang/timeout needs to elapse to prove the cap.
  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=1 N5_ISOLATE_TIMEOUT=2 N5_ISOLATE_TOTAL_BUDGET=0 \
    FAKE_HANG_CLASS="pkgB/HangClass" \
    run "$REPO_ROOT/tools/n5-decompile.sh" t24i_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24i_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['isolation_status'])")" = "total_budget_exhausted" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['excluded_classes'])")" = "[]" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['primary_status'])")" = "timeout" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_used'])")" = "True" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['fallback_reason'])")" = "primary_timeout_whole_module" ]

  # old whole-module-CFR behavior kept exactly, same as T24c/T24g.
  count=$(find "$local_dir/out/t24i_mod/vineflower" -name '*.java' 2>/dev/null | wc -l)
  [ "$count" -eq 0 ]
  [ -f "$local_dir/out/t24i_mod/fallback/pkgA/Alpha.java" ]
  [ -f "$local_dir/out/t24i_mod/fallback/pkgB/HangClass.java" ]
}

@test "T24j: --variant v2's own library context (-e=<lib CSV>, own flags) reaches T24's isolation path too, not just v1's context-free one (decompile-pipeline review: R3-variant-isolation-path-unexercised)" {
  local_dir="$BATS_TEST_TMPDIR/t24j"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24j_mod Tridium pkgA/Alpha pkgB/HangClass

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkgB/HangClass" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 t24j_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24j_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['primary_status'])")" = "ok_with_excluded" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['excluded_classes'])")" = "['pkgB/HangClass']" ]
  [ -f "$local_dir/out/t24j_mod/vineflower2/pkgA/Alpha.java" ]
  [ ! -f "$local_dir/out/t24j_mod/vineflower2/pkgB/HangClass.java" ]
  [ -f "$local_dir/out/t24j_mod/fallback2/pkgB/HangClass.java" ]

  # proves v2's OWN library context (not v1's context-free prefix) is what
  # actually reached the isolation/excluded-rerun path: its CMD line carries
  # -e=<lib CSV>.
  grep -q -- '-e=' "$local_dir/out/_logs/t24j_mod.v2.log"
}

@test "T24k: --variant v2's own vineflower2-noinner/ secondary view from an EARLIER hung run does not survive a rerun where nothing hangs, same as v1's T24f (decompile-pipeline review: R3-004)" {
  local_dir="$BATS_TEST_TMPDIR/t24k"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  t24_use_fake_vineflower
  N5_MODULES_DIR="$local_dir/modules" \
    t24_build_module_jar t24k_mod Tridium pkgA/Alpha pkgB/HangClass

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]

  # run 1: HangClass hangs -> isolated -> vineflower2-noinner/pkgB/HangClass.java
  # is genuinely produced, exactly like T24j.
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="pkgB/HangClass" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 t24k_mod
  [ "$status" -eq 0 ]
  [ -f "$local_dir/out/t24k_mod/vineflower2-noinner/pkgB/HangClass.java" ]

  # run 2 (--force, same module, no hang this time): the whole-jar primary
  # never times out, so vf_handle_primary_timeout/vf_render_noinner_view are
  # never called at all this run -- the fix at line ~1977 must proactively
  # clear the STALE vineflower2-noinner/ from run 1, same as v1's T24f.
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    N5_CFR="$REPO_ROOT/tools/decompilers/cfr-0.152.jar" \
    N5_PRIMARY_TIMEOUT=3 N5_ISOLATE_TIMEOUT=2 \
    FAKE_HANG_CLASS="" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 --force t24k_mod
  [ "$status" -eq 0 ]

  recon="$local_dir/out/t24k_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['primary_status'])")" = "ok" ]
  [ -f "$local_dir/out/t24k_mod/vineflower2/pkgB/HangClass.java" ]
  [ ! -e "$local_dir/out/t24k_mod/vineflower2-noinner/pkgB/HangClass.java" ]
  [ ! -d "$local_dir/out/t24k_mod/vineflower2-noinner" ]
}

@test "T24d: v1 and --variant v2/cons share ONE Vineflower-hang isolation helper (no copy-paste)" {
  def_count=$(grep -c '^vf_isolate_hung_classes()' "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$def_count" -eq 1 ]
  regex_def_count=$(grep -c '^vf_build_excluded_classes_regex()' "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$regex_def_count" -eq 1 ]
  orchestrator_def_count=$(grep -c '^vf_handle_primary_timeout()' "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$orchestrator_def_count" -eq 1 ]

  # both decompile_module (v1) and decompile_module_variant (v2/cons, shared
  # by decompile_module_v2/decompile_module_cons) call it — 'vf_handle_primary_timeout "'
  # (quote after the space) matches only an actual call, not the header/doc
  # comments that also mention the function by name.
  call_count=$(grep -c 'vf_handle_primary_timeout "' "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$call_count" -ge 2 ]
}

@test "T27: v1 --force keeps same-jar v2/cons recon sub-objects, drops stale ones, and clears a stale fallback/" {
  local_out="$BATS_TEST_TMPDIR/t27-out"
  N5_OUT_DIR="$local_out" run "$REPO_ROOT/tools/n5-decompile.sh" "$MODULE"
  [ "$status" -eq 0 ]
  recon="$local_out/$MODULE/recon.json"
  sha=$(python3 -c "import json;print(json.load(open('$recon'))['jar_sha256'])")
  # Simulate earlier --variant v2 (same jar) and --variant cons (a different, older jar) runs.
  python3 - "$recon" "$sha" <<'PY'
import json, sys
p, sha = sys.argv[1], sys.argv[2]
d = json.load(open(p))
d["v2"] = {"variant": "v2", "jar_sha256": sha, "status": "ok"}
d["cons"] = {"variant": "cons", "jar_sha256": "0" * 64, "status": "ok"}
json.dump(d, open(p, "w"))
PY
  mkdir -p "$local_out/$MODULE/fallback"
  echo "stale" > "$local_out/$MODULE/fallback/Stale.java"
  N5_OUT_DIR="$local_out" run "$REPO_ROOT/tools/n5-decompile.sh" --force "$MODULE"
  [ "$status" -eq 0 ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['status'])")" = "ok" ]
  [ "$(python3 -c "import json;print('cons' in json.load(open('$recon')))")" = "False" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['dropped_stale_variants'])")" = "['cons']" ]
  [ ! -e "$local_out/$MODULE/fallback/Stale.java" ]
}

# ---------------------------------------------------------------------------
# Multi-Release JAR (JEP 238) version overrides — META-INF/versions/<N>/...
# (odd/tasks/decompiler-fidelity-audit.md: Vineflower 1.12.0 creates the
# package directories for these entries during the whole-jar primary run but
# writes no .java for them, silently, with no failure marker, so the
# per-class CFR fallback never triggers either — see docs/decompiler-bakeoff.md's
# T26b "residual 27 classes" note for the corpus-wide shape of this bug.)
# ---------------------------------------------------------------------------

# Builds a REAL Multi-Release module jar at $1: a base com/example/Base.class
# (real javac bytes) at the normal package path, PLUS a byte-DIFFERENT
# override — compiled from a distinct source returning a distinguishing
# marker string — nested at META-INF/versions/$3/com/example/Base.class (real
# MRJAR layout, JEP 238; $2 = module.xml vendor, $3 = version, default 11).
mrjar_build_module_jar() {
  local dest="$1" vendor="$2" version="${3:-11}"
  local javac_bin="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}/bin/javac"
  [[ -x "$javac_bin" ]] || javac_bin="$(command -v javac)"

  local base_src base_out override_src override_out
  base_src="$(mktemp -d)"; base_out="$(mktemp -d)"
  override_src="$(mktemp -d)"; override_out="$(mktemp -d)"
  mkdir -p "$base_src/com/example" "$override_src/com/example"
  cat > "$base_src/com/example/Base.java" <<'JAVA'
package com.example;
public class Base {
  public String marker() { return "BASE_ORIGINAL"; }
}
JAVA
  cat > "$override_src/com/example/Base.java" <<'JAVA'
package com.example;
public class Base {
  public String marker() { return "MRJAR_OVERRIDE_MARKER"; }
}
JAVA
  "$javac_bin" -d "$base_out" "$base_src/com/example/Base.java"
  "$javac_bin" -d "$override_out" "$override_src/com/example/Base.java"

  python3 - "$dest" "$vendor" "$version" "$base_out" "$override_out" <<'PY'
import sys, zipfile, os
dest, vendor, version, base_out, override_out = sys.argv[1:]
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="%s"/>' % vendor)
    z.writestr("com/example/Base.class",
               open(os.path.join(base_out, "com/example/Base.class"), "rb").read())
    z.writestr("META-INF/versions/%s/com/example/Base.class" % version,
               open(os.path.join(override_out, "com/example/Base.class"), "rb").read())
PY
  rm -rf "$base_src" "$base_out" "$override_src" "$override_out"
}

@test "MRJAR: a META-INF/versions/<N> override class is decompiled into vineflower/META-INF/versions/<N>/... and recorded top-level in recon.json's mrjar_versions (v1, real javac/Vineflower/CFR)" {
  local_dir="$BATS_TEST_TMPDIR/mrjar"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  mrjar_build_module_jar "$local_dir/modules/mrjar_mod.jar" Tridium 11

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" mrjar_mod
  [ "$status" -eq 0 ]

  base_java="$local_dir/out/mrjar_mod/vineflower/com/example/Base.java"
  [ -f "$base_java" ]
  grep -q "BASE_ORIGINAL" "$base_java"

  override_java="$local_dir/out/mrjar_mod/vineflower/META-INF/versions/11/com/example/Base.java"
  [ -f "$override_java" ]
  grep -q "MRJAR_OVERRIDE_MARKER" "$override_java"

  recon="$local_dir/out/mrjar_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['classes'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['decompiled'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['fallback'])")" = "0" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_unrepresented'])")" = "[]" ]
}

@test "MRJAR: a META-INF/versions/<N> override class is ALSO handled under --variant v2, recorded in recon.json's v2 sub-object, not just v1's (decompile-pipeline review: R3-mrjar-variant-untested)" {
  local_dir="$BATS_TEST_TMPDIR/mrjar-v2"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  mrjar_build_module_jar "$local_dir/modules/mrjar_v2_mod.jar" Tridium 11
  # A second module jar so --variant v2's -e=<lib CSV> is non-empty (real
  # corpus usage always has hundreds of other module jars in the list): an
  # empty "-e=" is a separate, pre-existing Vineflower 1.12.0 CLI quirk
  # (confirmed unrelated to MRJAR handling -- it identically errors the
  # WHOLE-MODULE base decompile too, not just the override), irrelevant to
  # what this test is checking.
  make_fake_jar "$local_dir/modules/other_mod.jar" Tridium ""

  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --prepare-libcache
  [ "$status" -eq 0 ]
  N5_MODULES_DIR="$local_dir/modules" N5_BIN_EXT_DIR=/nonexistent N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" --variant v2 mrjar_v2_mod
  [ "$status" -eq 0 ]

  override_java="$local_dir/out/mrjar_v2_mod/vineflower2/META-INF/versions/11/com/example/Base.java"
  [ -f "$override_java" ]
  grep -q "MRJAR_OVERRIDE_MARKER" "$override_java"

  recon="$local_dir/out/mrjar_v2_mod/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['mrjar_versions']['11']['classes'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['mrjar_versions']['11']['decompiled'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['v2']['mrjar_unrepresented'])")" = "[]" ]
  # v1's tree must stay untouched -- this run only ever asked for --variant v2.
  [ ! -d "$local_dir/out/mrjar_v2_mod/vineflower" ]
}

@test "MRJAR: a class neither Vineflower nor CFR can produce a file for is listed in mrjar_unrepresented, never silently dropped" {
  local_dir="$BATS_TEST_TMPDIR/mrjar-bad"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  mrjar_build_module_jar "$local_dir/modules/mrjar_bad.jar" Tridium 11
  # Corrupt the override .class bytes IN the jar so neither decompiler can
  # produce any output for it — the exact "silent zero" the fix must always
  # surface instead of dropping quietly.
  python3 - "$local_dir/modules/mrjar_bad.jar" <<'PY'
import sys, zipfile, os
path = sys.argv[1]
tmp = path + ".tmp"
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w") as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "META-INF/versions/11/com/example/Base.class":
            data = b"not a class file"
        zout.writestr(item, data)
os.replace(tmp, path)
PY

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" mrjar_bad
  [ "$status" -eq 0 ]

  [ ! -f "$local_dir/out/mrjar_bad/vineflower/META-INF/versions/11/com/example/Base.java" ]
  recon="$local_dir/out/mrjar_bad/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['classes'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['decompiled'])")" = "0" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_unrepresented'])")" = "['11:com/example/Base']" ]
}

@test "MRJAR: an anonymous inner class (Name\$1) inside an override is NOT listed as unrepresented — it is folded into its enclosing top-level class's .java, same as everywhere else in this file (decompile-pipeline review: R2-mrjar-inner-class-count)" {
  local_dir="$BATS_TEST_TMPDIR/mrjar-inner"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  local javac_bin="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}/bin/javac"
  [[ -x "$javac_bin" ]] || javac_bin="$(command -v javac)"

  local base_src base_out override_src override_out
  base_src="$(mktemp -d)"; base_out="$(mktemp -d)"
  override_src="$(mktemp -d)"; override_out="$(mktemp -d)"
  mkdir -p "$base_src/com/example" "$override_src/com/example"
  cat > "$base_src/com/example/Base.java" <<'JAVA'
package com.example;
public class Base {
  public String marker() { return "BASE_ORIGINAL"; }
}
JAVA
  # the override has an anonymous Runnable -> javac emits a SEPARATE
  # com/example/Base$1.class alongside com/example/Base.class.
  cat > "$override_src/com/example/Base.java" <<'JAVA'
package com.example;
public class Base {
  public String marker() {
    Runnable r = new Runnable() {
      public void run() { System.out.println("MRJAR_OVERRIDE_INNER"); }
    };
    r.run();
    return "MRJAR_OVERRIDE_MARKER";
  }
}
JAVA
  "$javac_bin" -d "$base_out" "$base_src/com/example/Base.java"
  "$javac_bin" -d "$override_out" "$override_src/com/example/Base.java"
  [ -f "$override_out/com/example/Base\$1.class" ]

  python3 - "$local_dir/modules/mrjar_inner.jar" "$base_out" "$override_out" <<'PY'
import sys, zipfile, os
dest, base_out, override_out = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="Tridium"/>')
    z.write(os.path.join(base_out, "com/example/Base.class"), "com/example/Base.class")
    for f in os.listdir(os.path.join(override_out, "com/example")):
        z.write(os.path.join(override_out, "com/example", f), f"META-INF/versions/11/com/example/{f}")
PY
  rm -rf "$base_src" "$base_out" "$override_src" "$override_out"

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" mrjar_inner
  [ "$status" -eq 0 ]

  recon="$local_dir/out/mrjar_inner/recon.json"
  # top-level-class UNIT: 1 override class (Base), not 2 raw .class files.
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['classes'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['decompiled'])")" = "1" ]
  # the exact regression: Base\$1 must never appear as unrepresented -- it is
  # folded into Base.java, which IS present.
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_unrepresented'])")" = "[]" ]
  override_java="$local_dir/out/mrjar_inner/vineflower/META-INF/versions/11/com/example/Base.java"
  [ -f "$override_java" ]
  grep -q "MRJAR_OVERRIDE_MARKER" "$override_java"
}

@test "MRJAR: a marker-flagged override class CFR successfully retries is tallied as fallback, not decompiled -- the count must reveal the retry happened (decompile-pipeline review: R3-mrjar-tally-marker-miscount / R2-mrjar-decompiled-count-hides-cfr-retry)" {
  local_dir="$BATS_TEST_TMPDIR/mrjar-marker"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  mrjar_build_module_jar "$local_dir/modules/mrjar_marker.jar" Tridium 11

  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'

    # Stub vf_run_timed (used for the whole-subset primary run) to skip the
    # real Vineflower entirely and instead write the EXACT decompiler-failure
    # marker Vineflower itself would leave (see scan_marker_files's doc
    # comment) into the override's .java -- deterministic, no real Vineflower
    # bug needs to be reproduced to exercise this path. The REAL CFR retry
    # that follows (triggered by the real, unmodified scan_marker_files) still
    # runs for real against the real compiled Base.class this test built via
    # mrjar_build_module_jar, so the 'fallback' count reflects a genuine CFR
    # success, not a mock.
    vf_run_timed() {
      local outdir=\"\$2\"
      mkdir -p \"\$outdir/com/example\"
      {
        echo 'package com.example;'
        echo 'public class Base {'
        echo '  // \$VF: Couldn'\''t be decompiled'
        echo '  public String marker() { return \"MRJAR_OVERRIDE_MARKER\"; }'
        echo '}'
      } > \"\$outdir/com/example/Base.java\"
      echo ok
    }

    decompile_module \"$local_dir/modules/mrjar_marker.jar\" false \"$local_dir/out/mrjar_marker\"
  "
  [ "$status" -eq 0 ]

  recon="$local_dir/out/mrjar_marker/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['classes'])")" = "1" ]
  # the exact regression: a marker-flagged class CFR successfully replaced
  # must count as fallback, NEVER as a clean "decompiled" success.
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['decompiled'])")" = "0" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['fallback'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_unrepresented'])")" = "[]" ]
  # the marker-flagged primary .java is still on disk (untouched) AND the
  # real CFR retry produced its own replacement in fallback/.
  [ -f "$local_dir/out/mrjar_marker/vineflower/META-INF/versions/11/com/example/Base.java" ]
  [ -f "$local_dir/out/mrjar_marker/fallback/META-INF/versions/11/com/example/Base.java" ]
}

@test "MRJAR: a marker-flagged override class whose CFR retry produces NO file is tallied as unrepresented, never miscounted as decompiled (decompile-pipeline review: R2-mrjar-marker-cfr-miss-counted-decompiled / R3-002)" {
  local_dir="$BATS_TEST_TMPDIR/mrjar-marker-miss"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  mrjar_build_module_jar "$local_dir/modules/mrjar_marker_miss.jar" Tridium 11

  # Corrupt the override .class bytes so the REAL CFR retry (triggered by the
  # real, unmodified scan_marker_files below) cannot produce any output for
  # it. The primary run is stubbed to "succeed" and leave its marker-flagged
  # .java behind, exactly as real Vineflower does for a real marker-flagged
  # class -- but this time nothing ever replaces it in fallback/.
  python3 - "$local_dir/modules/mrjar_marker_miss.jar" <<'PY'
import sys, zipfile, os
path = sys.argv[1]
tmp = path + ".tmp"
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w") as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "META-INF/versions/11/com/example/Base.class":
            data = b"not a class file"
        zout.writestr(item, data)
os.replace(tmp, path)
PY

  run bash -c "
    set -euo pipefail
    N5_MODULES_DIR='$local_dir/modules' N5_OUT_DIR='$local_dir/out'
    export N5_MODULES_DIR N5_OUT_DIR
    source '$REPO_ROOT/tools/n5-decompile.sh'

    vf_run_timed() {
      local outdir=\"\$2\"
      mkdir -p \"\$outdir/com/example\"
      {
        echo 'package com.example;'
        echo 'public class Base {'
        echo '  // \$VF: Couldn'\''t be decompiled'
        echo '  public String marker() { return \"MRJAR_OVERRIDE_MARKER\"; }'
        echo '}'
      } > \"\$outdir/com/example/Base.java\"
      echo ok
    }

    decompile_module \"$local_dir/modules/mrjar_marker_miss.jar\" false \"$local_dir/out/mrjar_marker_miss\"
  "
  [ "$status" -eq 0 ]

  recon="$local_dir/out/mrjar_marker_miss/recon.json"
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['classes'])")" = "1" ]
  # the exact regression: a marker-flagged class whose CFR retry produced NO
  # file must be unrepresented, never a clean "decompiled" success.
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['decompiled'])")" = "0" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['fallback'])")" = "0" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_unrepresented'])")" = "['11:com/example/Base']" ]
  # the marker-flagged primary .java is still on disk (Vineflower's own
  # contract), but no fallback/ replacement exists -- CFR could not parse the
  # corrupted classfile.
  [ -f "$local_dir/out/mrjar_marker_miss/vineflower/META-INF/versions/11/com/example/Base.java" ]
  [ ! -f "$local_dir/out/mrjar_marker_miss/fallback/META-INF/versions/11/com/example/Base.java" ]
}

@test "MRJAR: a versions/<N> override shipping ONLY a nested class (no top-level Outer.class in that version) is still tallied, never silently dropped (decompile-pipeline review: R4-mrjar-toplevel-filter-drops-nested-only-overrides)" {
  local_dir="$BATS_TEST_TMPDIR/mrjar-nested-only"
  mkdir -p "$local_dir/modules" "$local_dir/out"
  local javac_bin="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}/bin/javac"
  [[ -x "$javac_bin" ]] || javac_bin="$(command -v javac)"

  local base_src base_out override_src override_out
  base_src="$(mktemp -d)"; base_out="$(mktemp -d)"
  override_src="$(mktemp -d)"; override_out="$(mktemp -d)"
  mkdir -p "$base_src/com/example" "$override_src/com/example"
  cat > "$base_src/com/example/Base.java" <<'JAVA'
package com.example;
public class Base {
  public String marker() { return "BASE_ORIGINAL"; }
}
JAVA
  # the override ships a new anonymous Runnable but its own top-level
  # Base.class is deliberately EXCLUDED from versions/11/ below -- an
  # unusual but real MRJAR shape (only the synthetic/anonymous class differs
  # for this release; javac still emits Base.class too, this test just
  # never copies it into the versions/ dir).
  cat > "$override_src/com/example/Base.java" <<'JAVA'
package com.example;
public class Base {
  public String marker() {
    Runnable r = new Runnable() {
      public void run() { System.out.println("NESTED_ONLY_OVERRIDE"); }
    };
    r.run();
    return "BASE_ORIGINAL";
  }
}
JAVA
  "$javac_bin" -d "$base_out" "$base_src/com/example/Base.java"
  "$javac_bin" -d "$override_out" "$override_src/com/example/Base.java"
  [ -f "$override_out/com/example/Base\$1.class" ]

  python3 - "$local_dir/modules/mrjar_nested_only.jar" "$base_out" "$override_out" <<'PY'
import sys, zipfile, os
dest, base_out, override_out = sys.argv[1], sys.argv[2], sys.argv[3]
with zipfile.ZipFile(dest, "w") as z:
    z.writestr("META-INF/module.xml", '<module vendor="Tridium"/>')
    z.write(os.path.join(base_out, "com/example/Base.class"), "com/example/Base.class")
    z.write(os.path.join(override_out, "com/example/Base$1.class"),
            "META-INF/versions/11/com/example/Base$1.class")
PY
  rm -rf "$base_src" "$base_out" "$override_src" "$override_out"

  N5_MODULES_DIR="$local_dir/modules" N5_OUT_DIR="$local_dir/out" \
    run "$REPO_ROOT/tools/n5-decompile.sh" mrjar_nested_only
  [ "$status" -eq 0 ]

  recon="$local_dir/out/mrjar_nested_only/recon.json"
  # the exact regression: this override class must be TALLIED (classes=1),
  # never silently swallowed out of total/decompiled/fallback/unrepresented
  # the way the old basename-only '$'-filter did.
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['classes'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_versions']['11']['decompiled'])")" = "1" ]
  [ "$(python3 -c "import json;print(json.load(open('$recon'))['mrjar_unrepresented'])")" = "[]" ]
  override_java="$local_dir/out/mrjar_nested_only/vineflower/META-INF/versions/11/com/example/Base\$1.java"
  [ -f "$override_java" ]
}

@test "MRJAR: v1 and --variant v2/cons share ONE MRJAR-version-override helper (no copy-paste)" {
  def_count=$(grep -c '^vf_handle_mrjar_versions()' "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$def_count" -eq 1 ]
  # both decompile_module (v1) and decompile_module_variant (v2/cons, shared
  # by decompile_module_v2/decompile_module_cons) call it.
  call_count=$(grep -c 'vf_handle_mrjar_versions "' "$REPO_ROOT/tools/n5-decompile.sh")
  [ "$call_count" -ge 2 ]
}
