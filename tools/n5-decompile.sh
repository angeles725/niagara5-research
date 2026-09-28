#!/usr/bin/env bash
# n5-decompile.sh — decompile Niagara N5 modules into organized/<module>/
#
# Usage:
#   tools/n5-decompile.sh                 # decompile every jar in $N5_MODULES_DIR
#   tools/n5-decompile.sh <name>.jar      # decompile one module (name with or without .jar)
#   tools/n5-decompile.sh --docsource     # only extract docSource.jar (original .java sources)
#   tools/n5-decompile.sh --bin-ext       # decompile the Tridium-owned jars under bin/ext/
#   tools/n5-decompile.sh --force <name>  # ignore the sha256 cache, redo it
#   tools/n5-decompile.sh --prepare-libcache    # v2/cons: build organized/_v2-libcache/ (see below)
#   tools/n5-decompile.sh --variant v2 <name>   # v2: same module, WITH library context
#   tools/n5-decompile.sh --variant v2 --all    # v2 over every module jar (see below)
#   tools/n5-decompile.sh --variant v2 --bin-ext [<name>]  # v2 over included bin/ext jar(s)
#   tools/n5-decompile.sh --variant cons <name> # cons: B118 §118.1's conservative + line-mapped
#                                                # view (same lib context as v2, see below)
#   tools/n5-decompile.sh --variant cons --all  # cons over every module jar
#   tools/n5-decompile.sh --extra-tridium       # v2+cons over the 10 out-of-pipeline Tridium
#                                                # etc/m2+lib jars AND the Tridium-owned nested
#                                                # LIB-INF jars (see below; T22)
#   tools/n5-decompile.sh --third-party-libinf  # v2 over EVERY non-Tridium nested LIB-INF jar,
#                                                # deduplicated by sha256 (see below; T26b)
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
# --variant cons (T22, niagara5-block118.md §118.1): a THIRD decompile, alongside v1 and v2,
# writing organized/<mod>/vineflower-cons/ (+fallback-cons/). Reuses v2's entire
# library-context machinery UNCHANGED (immutable libcache, --add-external, --include-runtime,
# idempotency key, failure semantics) — only the Vineflower flag set differs: resugaring OFF
# (--pattern-matching=false --decompile-switch-expressions=false --ternary-in-if=false
# --prettify-ifs=false --inline-simple-lambdas=false, so instanceof-pattern/switch-expression/
# collapsed-if syntax never renders — B90/B98's resugaring caveat, closed mechanically) and
# ORIGINAL-source line mapping ON (--bytecode-source-mapping=true plus the HIDDEN
# --__dump_original_lines__=true, found only in IFernflowerPreferences.class's constant pool,
# not --help). B118 measured 669/669 mapped lines correct against docSource originals. cons is a
# second, syntax-neutral, line-cited view for corroboration, not a replacement for v1/v2 — a real
# pattern switch (e.g. BNumericWritable) renders more faithfully in v1/v2; cons shows the
# desugared bytecode-shaped state machine instead, still line-mapped.
#
# --extra-tridium (T22, niagara5-block117.md §117.2 + §117.4): the pipeline above only ever
# scans $N5_MODULES_DIR and $N5_BIN_EXT_DIR. Two further Tridium-owned code populations exist:
#  - 10 out-of-pipeline jars under $N5_ETC_M2_DIR (com/tridium/tools/*, com/tridium/xelem/*) and
#    $N5_LIB_DIR (tridium-niagara-baja-doclet). Classified with tools/n5-classify-binext.py's
#    EXISTING >50%-Tridium-namespace rule, unchanged — mechanical, not a hand-picked list
#    (verified this session: exactly the 10 names niagara5-block117.md §117.4 lists). Each gets
#    v2 AND cons, into organized/_etc-m2/<jar-stem>/ or organized/_lib/<jar-stem>/. 4 of the 10
#    (n-plugin, n-conv-plugin, settings, utils) carry Lkotlin/Metadata; in their bytecode — this
#    is recorded per-jar as "language": "kotlin" in recon.json (write_recon_language), and
#    Vineflower 1.12.0's bundled Kotlin plugin (--kt-enable, default true) applies to them.
#  - Tridium-owned nested LIB-INF jars (niagara5-block117.md §117.2: 98 LIB-INF jars exist, only
#    2 — devkit's n-templates and tridium-niagara-slotomatic-library — are Tridium's own code by
#    the same >50% rule). Found by scanning every ALREADY-EXTRACTED
#    organized/<mod>/extracted/LIB-INF/*.jar (not the deduplicated-by-sha256 libcache, so
#    per-module identity is kept), decompiled (v2+cons) into
#    organized/<mod>/lib-inf/<jar-stem>/{extracted,vineflower2,vineflower-cons,...}.
#
# --third-party-libinf (T26b, odd/tasks/decompiler-fidelity-audit.md): the complement of
# --extra-tridium's LIB-INF handling. tools/n5-best-source.py found that 11,719 classes
# corpus-wide have NO representation anywhere — almost entirely non-Tridium (third-party) jars
# nested under module/bin-ext jars' LIB-INF/, which the pipeline above never decompiles at all
# (--extra-tridium only ever picks up the Tridium-OWNED ones, verdict "include*"). This mode
# decompiles every OTHER nested LIB-INF jar — verdict "skip" from the same
# tools/n5-classify-binext.py >50%-rule, unchanged — with v2 settings, ONCE per distinct jar
# sha256 regardless of how many modules bundle a byte-identical copy.
#  - Source jars are scanned directly: every Tridium-vendor jar in $N5_MODULES_DIR (docSource.jar
#    excluded) and every jar under $N5_BIN_EXT_DIR, reading each one's own LIB-INF/*.jar entries
#    straight from the zip (never from organized/*/extracted/, which this mode does not require to
#    exist first).
#  - Dedup key is the nested jar's own sha256. The FIRST module/entry seen for a given sha256 names
#    the output directory's <jar-stem>; every occurrence (including the first) is recorded in
#    recon.json's "found_in" as "<module>!LIB-INF/<entry-path>".
#  - Output: organized/_lib-inf-3p/<jar-stem>-<sha256[:12]>/{extracted,vineflower2,fallback2,
#    recon.json} — exactly decompile_module_v2's own out_dir_name/fallback_dir_name convention (no
#    copy of the decompile core; this mode calls decompile_module_v2 directly), so
#    extracted/.jar_sha256 is written the same way every other population's is and
#    tools/n5-best-source.py's sha256 identity index links every module's raw copy to it. recon.json
#    additionally carries "population": "lib-inf-3p", "jar_sha256", and "found_in" — written by
#    write_recon_lib_inf_3p, layered on top of decompile_module_v2's own "v2" sub-object, never
#    replacing it.
#  - Idempotent for free: decompile_module_v2's own idempotency key is purely content-based (jar
#    sha256 + library set + flags + tool jar sha256s, see compute_v2_idempotency_key) and the output
#    directory name is deterministic from the same sha256, so a rerun without --force naturally
#    skips an already-"ok" distinct jar — no separate idempotency bookkeeping needed here.
#  - Prints one summary line: "lib-inf-3p: decompiled=N skipped-up-to-date=N failed=N
#    distinct_jars=N" (distinct_jars counts only non-Tridium jars; a Tridium-owned nested LIB-INF
#    jar found during the scan is classified out before it is counted at all — it belongs to
#    --extra-tridium instead).
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
#   N5_ISOLATE_TIMEOUT   default: 90 (seconds, T24: per-package/per-class budget used ONLY
#                    after a whole-jar Vineflower run times out, to bisect down to the exact
#                    top-level class(es) responsible — see "Whole-jar timeout isolation" below)
#   N5_ISOLATE_TOTAL_BUDGET  default: 1800 (seconds, decompile-pipeline review fix,
#                    R4-isolation-unbounded-total-budget: a HARD CAP on the WHOLE T24
#                    bisection (every package probe + every per-class dive combined) for one
#                    hung module. N5_ISOLATE_TIMEOUT alone bounds each individual probe, but a
#                    module with many packages/classes had no bound on how many of those
#                    per-probe budgets could stack up — a worst-case module could burn hours in
#                    vf_isolate_hung_classes alone. Exceeding this total stops isolation
#                    immediately (isolation_status=total_budget_exhausted, no partial hung-class
#                    list kept — see vf_isolate_hung_classes' doc comment) and falls back to
#                    today's original whole-module CFR behavior, exactly as if no hung class
#                    could be isolated at all.
#   N5_PARALLELISM   default: 6 (used only as documentation for callers driving xargs -P)
#   N5_JDK25_HOME    default: /home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec
#                    (--variant v2 only) passed to Vineflower's --include-runtime. Must be
#                    a real JDK home containing lib/modules (the jrt image), NOT just a
#                    `java` binary's directory — Homebrew's keg-only openjdk@25 formula
#                    symlinks bin/include/etc under opt/openjdk@25 itself but the actual
#                    JDK home (with lib/modules) is one level down, at opt/openjdk@25/libexec.
#                    Passing opt/openjdk@25 itself crashes Vineflower with a NullPointerException
#                    in JrtFinder.addRuntime (verified empirically 2026-09-28).
#   N5_ETC_M2_DIR    default: /mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository
#                    (--extra-tridium only) scanned for *.jar recursively.
#   N5_LIB_DIR       default: /mnt/c/Program Files/Niagara/5.0.0.28/lib
#                    (--extra-tridium only) scanned for *.jar, -maxdepth 1.
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
# and T24's isolation below could not do better (observed on this corpus: Vineflower
# 1.12.0 hangs indefinitely on ONE class in bajaui.jar,
# com/tridium/ui/theme/custom/nss/query/NSS2SelectionResult — its method-local record
# NSS2SelectionResult$1ValueAndAdvice makes a Vineflower thread spin forever in
# ClassWriter.writeClass; CFR decompiles the same jar in ~11s), and per-class when
# Vineflower completes but leaves an explicit decompiler-failure marker in a handful of
# files. CFR is not a semantic oracle either (B116: it drops `(Object)null` casts).
#
# Whole-jar timeout isolation (T24, odd/tasks/decompiler-fidelity-audit.md): a single
# hanging class used to cost a whole module ALL of its Vineflower fidelity — 832 classes
# (566 top-level) in bajaui, all three variants, over ONE hang. When the primary
# whole-jar run times out, decompile_module/decompile_module_variant now call the shared
# vf_handle_primary_timeout (see its own doc comment, right before decompile_module
# below) before falling back to whole-module CFR:
#   1. vf_isolate_hung_classes bisects — first by PACKAGE (every .class file directly in
#      one directory, run together as a throwaway subset jar, same Vineflower
#      command/options/library context as the real run, but its own N5_ISOLATE_TIMEOUT
#      budget), then, for any package that times out, by TOP-LEVEL CLASS (that class plus
#      its own Name$* nested classes, alone). Deterministic (sorted iteration/output);
#      parallelism is not attempted.
#   2. If one or more top-level classes are found hung, the whole jar is re-run ONCE more
#      with Vineflower's --excluded-classes=<regex> excluding exactly those classes (see
#      vf_build_excluded_classes_regex's doc comment for the empirically-verified regex
#      semantics: a FULL match against the '/'-separated internal name).
#   3. If THAT re-run succeeds: the excluded-run tree becomes the primary tree
#      (recon.json primary_status="ok_with_excluded", fallback_reason=
#      "primary_hang_isolated"); each hung class gets CFR output in the fallback dir the
#      variant already uses (same per-class-fallback convention as a decompiler-failure
#      marker); and a best-effort Vineflower --decompile-inner=false rendering of just the
#      hung class group is attempted (own N5_ISOLATE_TIMEOUT budget) into a "-noinner"
#      sibling of the primary tree, as a secondary view — useful even when the class still
#      doesn't fully round-trip, since a local/anon/method-scoped class is what actually
#      tends to hang Vineflower's inner-class handling.
#   4. If isolation finds NO hung class, or the excluded re-run ALSO times out or errors,
#      today's original whole-module CFR fallback is kept EXACTLY (primary_status stays
#      "timeout", fallback_reason stays "primary_timeout_whole_module") — recon.json just
#      gains an "isolation_status" field explaining why isolation didn't help
#      ("no_hung_class_found", "excluded_rerun_timeout", "excluded_rerun_error"). Isolation
#      never claims success it did not observe.
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
N5_ISOLATE_TIMEOUT="${N5_ISOLATE_TIMEOUT:-90}"
N5_ISOLATE_TOTAL_BUDGET="${N5_ISOLATE_TOTAL_BUDGET:-1800}"
N5_JDK25_HOME="${N5_JDK25_HOME:-/home/linuxbrew/.linuxbrew/opt/openjdk@25/libexec}"
N5_ETC_M2_DIR="${N5_ETC_M2_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository}"
N5_LIB_DIR="${N5_LIB_DIR:-/mnt/c/Program Files/Niagara/5.0.0.28/lib}"

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
  # T24 (optional, all default to "isolation never ran"): $9=excluded_classes as a
  # JSON array string, $10=isolate_time_seconds, $11=isolation_status (only ever
  # non-empty when the whole-jar run originally timed out), $12=
  # primary_timeout_attempt_seconds (the ORIGINAL timed-out attempt's elapsed time,
  # kept even after primary_time above is overwritten with the excluded re-run's own
  # time on success). See vf_handle_primary_timeout's doc comment.
  local excluded_classes_json="${9:-[]}" isolate_time="${10:-0}" \
        isolation_status="${11:-}" timeout_attempt_time="${12:-}"
  # Multi-Release JAR (JEP 238) version overrides (odd/tasks/decompiler-fidelity-audit.md):
  # $13=mrjar_versions as a JSON object string ("N": {classes,decompiled,fallback}),
  # $14=mrjar_unrepresented as a JSON array string ("N:<internal-name>" entries). Both
  # default to "empty" so a caller that never ran vf_handle_mrjar_versions (none do —
  # decompile_module always calls it — but a future/test caller might) still writes a
  # valid, if trivial, recon.json. See vf_handle_mrjar_versions's doc comment.
  # (a literal "{}" default inside a "${n:-...}" expansion is a known bash brace-
  # matching trap — it silently APPENDS a stray extra "}" onto a non-empty $13 instead
  # of only supplying the default for a missing one; verified empirically 2026-09-28 —
  # so the object default is applied in a separate step instead.)
  local mrjar_versions_json="${13:-}" mrjar_unrepresented_json="${14:-[]}"
  [[ -z "$mrjar_versions_json" ]] && mrjar_versions_json="{}"
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
    --excluded-classes "$excluded_classes_json" \
    --isolate-time "$isolate_time" \
    --isolation-status "$isolation_status" \
    --timeout-attempt-time "$timeout_attempt_time" \
    --out "$moddir/recon.json"

  # Multi-Release JAR (JEP 238) version overrides: merged onto recon.json's TOP level
  # (a fact about the source jar, independent of which decompiler variant read it — same
  # placement as write_recon_language's "language" field) as a step AFTER
  # n5-recon-helper.py's own write above, rather than as one more of that script's own
  # CLI flags, so tools/n5-recon-helper.py (owned by a different writer in this
  # checkout) never needs to change for this fix. See vf_handle_mrjar_versions's doc
  # comment.
  RECON_PATH="$moddir/recon.json" \
  RECON_MRJAR_VERSIONS="$mrjar_versions_json" \
  RECON_MRJAR_UNREPRESENTED="$mrjar_unrepresented_json" \
  python3 <<'PYEOF'
import json, os

path = os.environ["RECON_PATH"]
with open(path) as fh:
    recon = json.load(fh)
recon["mrjar_versions"] = json.loads(os.environ["RECON_MRJAR_VERSIONS"])
recon["mrjar_unrepresented"] = json.loads(os.environ["RECON_MRJAR_UNREPRESENTED"])
with open(path, "w") as fh:
    json.dump(recon, fh, indent=2)
    fh.write("\n")
PYEOF
}

# ---------------------------------------------------------------------------
# T24 (odd/tasks/decompiler-fidelity-audit.md): isolate the top-level class(es)
# that hang a whole-jar Vineflower run, instead of losing the WHOLE module to
# CFR over one hanging class. Shared by v1 (decompile_module) and v2/cons
# (decompile_module_variant, via decompile_module_v2/decompile_module_cons) —
# every function in this block is called from both places; see the header
# comment's "Whole-jar timeout isolation" section for the algorithm summary.
# ---------------------------------------------------------------------------

# Every TOP-LEVEL class's internal name (its path under $1, '/'-separated,
# WITHOUT the .class extension), sorted. A class is "top-level" when its
# .class file's basename has no '$' — nested/inner/local/anonymous classes are
# always compiled as Outer$Something.class (verified against this whole
# corpus already, T13/T19: no exception found).
vf_list_top_level_classes() {
  local extracted_dir="$1" f
  find "$extracted_dir" -name '*.class' ! -name '*$*' ! -path '*/META-INF/*' \
    | while IFS= read -r f; do
        f="${f#"$extracted_dir"/}"
        printf '%s\n' "${f%.class}"
      done \
    | sort
}

# The package (directory) internal class name $1 lives in — "" for one
# sitting directly under the extraction root (no package).
vf_package_of() {
  local internal="$1"
  case "$internal" in
    */*) printf '%s\n' "${internal%/*}" ;;
    *) printf '%s\n' "" ;;
  esac
}

# Every .class file (top-level AND nested/local/anon — anything compiled into
# the SAME directory) that is a DIRECT child of $1/$2 (one package directory,
# NON-recursive: a sub-package is a different group), as internal names,
# sorted. $2="" means the extraction root itself.
vf_classes_in_package() {
  local extracted_dir="$1" package="$2" f dir
  if [[ -n "$package" ]]; then dir="$extracted_dir/$package"; else dir="$extracted_dir"; fi
  [[ -d "$dir" ]] || return 0
  find "$dir" -maxdepth 1 -name '*.class' \
    | while IFS= read -r f; do
        f="${f#"$extracted_dir"/}"
        printf '%s\n' "${f%.class}"
      done \
    | sort
}

# Every .class file for top-level class $2 ALONE — itself plus its own
# Name$*.class nested/local/anon classes, never a sibling top-level class that
# happens to share a name prefix — as internal names, sorted.
vf_classes_for_top_level() {
  local extracted_dir="$1" internal="$2" dir base f
  dir="$(dirname "$extracted_dir/$internal.class")"
  base="$(basename "$internal")"
  [[ -d "$dir" ]] || return 0
  find "$dir" -maxdepth 1 \( -name "$base.class" -o -name "${base}\$*.class" \) \
    | while IFS= read -r f; do
        f="${f#"$extracted_dir"/}"
        printf '%s\n' "${f%.class}"
      done \
    | sort
}

# Builds a throwaway jar at $2, containing exactly the .class entries named
# (one internal name per line) on stdin, read from under $1, preserving their
# directory structure — so Vineflower resolves them the same way it would
# inside the real module jar. python3's zipfile (already a hard dependency of
# this pipeline) is used instead of `zip`/`jar` so no extra tool is required.
vf_build_subset_jar() {
  local extracted_dir="$1" dest="$2"
  # -c, not a `python3 - ... <<'PY'` heredoc: a heredoc would itself become
  # this command's stdin, discarding the piped class-name list callers rely
  # on (`vf_classes_in_package ... | vf_build_subset_jar ...`).
  python3 -c '
import sys, zipfile
extracted_dir, dest = sys.argv[1], sys.argv[2]
names = [l.rstrip("\n") for l in sys.stdin if l.strip()]
with zipfile.ZipFile(dest, "w") as z:
    for internal in names:
        rel = internal + ".class"
        z.write(extracted_dir + "/" + rel, rel)
' "$extracted_dir" "$dest"
}

# Runs "$5 $6 ... <jar> <outdir>" (the whole prefix command, "$@" from $5
# onward) under `timeout $3`, logging it (CMD line + all output) into $4.
# Prints "ok"/"timeout"/"error" (the same vocabulary decompile_module's own
# primary-run check already uses) on stdout — nothing else.
vf_run_timed() {
  local jar="$1" outdir="$2" budget="$3" logfile="$4"; shift 4
  local -a cmd=("$@" "$jar" "$outdir")
  mkdir -p "$outdir"
  { printf 'CMD(T24):'; printf ' %q' "${cmd[@]}"; printf '\n'; } >> "$logfile"
  if timeout "$budget" "${cmd[@]}" >> "$logfile" 2>&1; then
    echo ok
  else
    local rc=$?
    if [[ $rc -eq 124 ]]; then echo timeout; else echo error; fi
  fi
}

# Bisects $2 (the module's ALREADY-extracted class tree, e.g. "$moddir/extracted"
# — NOT a path this function appends "/extracted" to itself) for the top-level
# class(es) that hang a Vineflower run on their own, given the exact
# command/options/library-context prefix a caller's real whole-jar run used
# ("$@" from $5 onward — e.g. v1: "$N5_JAVA -jar $N5_VINEFLOWER
# --log-level=error"; v2/cons: that plus --include-runtime=... plus the
# variant's own fidelity flags plus -e=<lib CSV>), each subset run given its
# own $3-second budget instead of $N5_PRIMARY_TIMEOUT. First by PACKAGE
# (cheap: most packages are innocent and a package-sized subset completes
# fast); only a package that itself times out is bisected further, by
# TOP-LEVEL CLASS (that class + its own Name$* nested classes, alone).
# Deterministic: packages and classes are iterated in sorted order, and the
# result is sorted+deduped. Parallelism is not attempted (T24 doesn't require
# it; a real corpus run drives whole MODULES in parallel already, via xargs
# -P, same as every other mode this script has). The WHOLE bisection (every
# package probe + every per-class dive combined) is capped at
# $N5_ISOLATE_TOTAL_BUDGET seconds total (decompile-pipeline review fix,
# R4-isolation-unbounded-total-budget) — exceeding it abandons isolation
# entirely (no partial hung-class list is trusted) rather than let a
# many-package module stack up an unbounded number of per-probe budgets.
#
# Sets (globals, read by the caller immediately after calling):
#   VF_ISOLATE_HUNG_CLASSES=()  sorted internal names of classes that hang ALONE
#                                (always empty when VF_ISOLATE_STATUS != "isolated")
#   VF_ISOLATE_STATUS           "isolated" (>=1 found) | "no_hung_class_found" |
#                                "total_budget_exhausted" (N5_ISOLATE_TOTAL_BUDGET
#                                hit before every package/class could be tried)
#   VF_ISOLATE_TIME             wall-clock seconds this whole bisection took
vf_isolate_hung_classes() {
  local module="$1" extracted_dir="$2" budget="$3" logfile="$4"; shift 4
  local -a prefix=("$@")

  local t0 t1; t0="$(date +%s)"
  VF_ISOLATE_HUNG_CLASSES=()
  local budget_exhausted=false

  local -a top_level=()
  local c
  while IFS= read -r c; do [[ -n "$c" ]] && top_level+=("$c"); done \
    < <(vf_list_top_level_classes "$extracted_dir")

  # NOT an associative array keyed by package name: bash 5.2 treats an EMPTY
  # STRING subscript ("${arr[$x]}" with x="") as a "bad array subscript"
  # error — and a class with no package at all (e.g. bajaui's real
  # module-info.class, sitting directly at the extraction root) legitimately
  # has package "". `sort -u` dedups just as well without that trap.
  local -a packages=()
  readarray -t packages < <(
    local top_c
    for top_c in "${top_level[@]}"; do vf_package_of "$top_c"; done | sort -u
  )

  local tmpdir; tmpdir="$(mktemp -d)"
  local pkg pkg_status
  for pkg in "${packages[@]}"; do
    # R4-isolation-unbounded-total-budget: checked at the top of EVERY
    # package iteration (not just once) so a module with many packages can't
    # stack up an unbounded number of per-probe budgets.
    if [[ $(( $(date +%s) - t0 )) -ge "$N5_ISOLATE_TOTAL_BUDGET" ]]; then
      log "$module" "T24 isolate: total isolation budget (${N5_ISOLATE_TOTAL_BUDGET}s) exhausted before every package could be tried, abandoning isolation"
      budget_exhausted=true
      break
    fi
    rm -f "$tmpdir/pkg.jar"; rm -rf "$tmpdir/pkg-out"
    vf_classes_in_package "$extracted_dir" "$pkg" | vf_build_subset_jar "$extracted_dir" "$tmpdir/pkg.jar"
    log "$module" "T24 isolate: testing package '${pkg:-<default>}'"
    pkg_status="$(vf_run_timed "$tmpdir/pkg.jar" "$tmpdir/pkg-out" "$budget" "$logfile" "${prefix[@]}")"
    if [[ "$pkg_status" == "timeout" ]]; then
      log "$module" "T24 isolate: package '${pkg:-<default>}' timed out, bisecting its top-level classes"
      local top_c cls_status
      for top_c in "${top_level[@]}"; do
        [[ "$(vf_package_of "$top_c")" == "$pkg" ]] || continue
        if [[ $(( $(date +%s) - t0 )) -ge "$N5_ISOLATE_TOTAL_BUDGET" ]]; then
          log "$module" "T24 isolate: total isolation budget (${N5_ISOLATE_TOTAL_BUDGET}s) exhausted mid-bisection of package '${pkg:-<default>}', abandoning isolation"
          budget_exhausted=true
          break
        fi
        rm -f "$tmpdir/cls.jar"; rm -rf "$tmpdir/cls-out"
        vf_classes_for_top_level "$extracted_dir" "$top_c" | vf_build_subset_jar "$extracted_dir" "$tmpdir/cls.jar"
        cls_status="$(vf_run_timed "$tmpdir/cls.jar" "$tmpdir/cls-out" "$budget" "$logfile" "${prefix[@]}")"
        if [[ "$cls_status" == "timeout" ]]; then
          log "$module" "T24 isolate: class '$top_c' hangs alone"
          VF_ISOLATE_HUNG_CLASSES+=("$top_c")
        fi
      done
      [[ "$budget_exhausted" == true ]] && break
    fi
  done
  rm -rf "$tmpdir"

  if [[ "$budget_exhausted" == true ]]; then
    # No partial hung-class list is trusted once the total budget is blown —
    # the caller must fall all the way back to today's whole-module CFR
    # behavior, exactly as if isolation had found nothing at all.
    VF_ISOLATE_HUNG_CLASSES=()
    VF_ISOLATE_STATUS="total_budget_exhausted"
  elif [[ "${#VF_ISOLATE_HUNG_CLASSES[@]}" -gt 0 ]]; then
    local -a sorted_hung=()
    readarray -t sorted_hung < <(printf '%s\n' "${VF_ISOLATE_HUNG_CLASSES[@]}" | sort -u)
    VF_ISOLATE_HUNG_CLASSES=("${sorted_hung[@]}")
    VF_ISOLATE_STATUS="isolated"
  else
    VF_ISOLATE_STATUS="no_hung_class_found"
  fi
  t1="$(date +%s)"
  VF_ISOLATE_TIME=$(( t1 - t0 ))
}

# Vineflower 1.12.0's --excluded-classes=<regex> semantics, verified
# EMPIRICALLY 2026-09-28 (not documented in --help; see docs/decompiler-bakeoff.md's
# "Resolved (T24)" bullet under its "### Campaign run" section (itself under
# "## `--variant cons` and `--extra-tridium`") for the experiment this comment
# summarizes) against the real vineflower-1.12.0.jar with a synthetic jar
# reproducing bajaui's actual shape (a top-level class with a method-local
# class, NSS2SelectionResult(\$1ValueAndAdvice), plus an unrelated sibling
# whose name shares the same prefix, NSS2SelectionResultFooBar):
#   - the value is matched with a FULL match (java.util.regex
#     Matcher#matches(), i.e. the ENTIRE string must match — not a substring
#     search) against each class's INTERNAL name: '/'-separated package path,
#     no leading/trailing slash, no ".class" suffix — e.g.
#     "com/tridium/ui/theme/custom/nss/query/NSS2SelectionResult" for the
#     top-level class, "...NSS2SelectionResult$1ValueAndAdvice" for its nested
#     one. '/' is NOT specially re-encoded — a literal '.' in the pattern
#     means "any character", exactly like anywhere else in Java regex.
#   - a bare "<name>.*" pattern therefore OVER-MATCHES: it also excludes an
#     UNRELATED sibling class whose name simply starts with the same
#     characters (confirmed: "...NSS2SelectionResult.*" also swallowed
#     "...NSS2SelectionResultFooBar" — a distinct top-level class — because
#     Matcher#matches() still succeeds when ".*" just consumes "FooBar" too).
#   - the correct per-class pattern anchors the nested-class boundary
#     EXPLICITLY: "<escaped-internal-name>(\$.*)?" — matches the class itself
#     (the optional group empty) and any of its own nested classes (which
#     start with a literal '$'), but nothing that merely shares a prefix.
#     Verified: this pattern excluded NSS2SelectionResult (and would exclude
#     its nested class if Vineflower ever rendered one as a separate file —
#     it doesn't, by default, for a method-local class) while leaving
#     NSS2SelectionResultFooBar alone.
#   - multiple classes combine with Java regex alternation ('|'); '|' has the
#     lowest precedence, so "A(\$.*)?|B(\$.*)?" parses as the two intended
#     independent full-match alternatives, not something narrower.
# re.escape (not a hand-rolled sed character class) escapes each class's own
# internal name before this suffix is appended, so a name containing a regex
# metacharacter (none exist in this corpus, but this must never silently
# under-exclude one that did) can't corrupt the pattern.
vf_build_excluded_classes_regex() {
  python3 -c '
import re, sys
parts = [re.escape(n) + r"(\$.*)?" for n in sys.argv[1:]]
print("|".join(parts), end="")
' "$@"
}

# Best-effort secondary view (T24 step 3): re-decompiles just the hung class
# group (each hung top-level class plus its own Name$* nested classes) with
# --decompile-inner=false, so a local/anonymous/method-scoped class — the kind
# that actually tends to hang Vineflower's inner-class handling — renders on
# its own instead of being desugared invisibly inside its enclosing method.
# Useful even when it still doesn't fully round-trip. NEVER fails the caller:
# on timeout/error it just logs and leaves no output directory behind (a
# reader must never mistake a half-written or stale noinner/ for a real one).
#
# $1=module $2=extracted_dir $3=dest_dir $4=budget $5=logfile, then a
# Vineflower prefix command (N5_JAVA -jar N5_VINEFLOWER --log-level=error
# [own flags incl. --decompile-inner=false] [-e=<lib CSV>]) up to a literal
# "--" separator, then the hung top-level classes' internal names.
vf_render_noinner_view() {
  local module="$1" extracted_dir="$2" dest_dir="$3" budget="$4" logfile="$5"; shift 5
  local -a cmd=()
  while [[ "$#" -gt 0 && "$1" != "--" ]]; do
    cmd+=("$1"); shift
  done
  [[ "$#" -gt 0 ]] && shift # drop the "--" separator
  local -a hung=("$@")
  [[ "${#hung[@]}" -gt 0 ]] || return 0

  local tmpdir; tmpdir="$(mktemp -d)"
  local c
  {
    for c in "${hung[@]}"; do
      vf_classes_for_top_level "$extracted_dir" "$c"
    done
  } | sort -u | vf_build_subset_jar "$extracted_dir" "$tmpdir/hung.jar"

  rm -rf "${dest_dir:?}"
  local status
  status="$(vf_run_timed "$tmpdir/hung.jar" "$dest_dir" "$budget" "$logfile" "${cmd[@]}")"
  rm -rf "$tmpdir"
  if [[ "$status" != "ok" ]]; then
    log "$module" "T24 noinner view: $status, skipping (best-effort secondary view, never blocks the module)"
    rm -rf "${dest_dir:?}"
    return 1
  fi
  log "$module" "T24 noinner view: rendered $(find "$dest_dir" -name '*.java' 2>/dev/null | wc -l) file(s) for ${#hung[@]} hung class(es)"
  return 0
}

# Orchestrates T24's whole response to a timed-out whole-jar primary run,
# shared by decompile_module (v1) and decompile_module_variant (v2/cons).
# Returns 0 and sets VFH_PRIMARY_STATUS/VFH_PRIMARY_TIME/VFH_FALLBACK_USED/
# VFH_FALLBACK_REASON when isolation resolved it (primary_status=
# "ok_with_excluded"); returns 1 (the caller must keep ITS OWN original
# whole-module-CFR-fallback behavior exactly) when it did not. Either way,
# always sets VFH_ISOLATION_STATUS, VFH_ISOLATE_TIME and VFH_EXCLUDED_CLASSES
# (an array, possibly empty) — the caller records these in recon.json
# regardless of outcome (forensics: WHY isolation didn't help matters as much
# as when it did).
#
# $1=module $2=moddir $3=jar (the REAL module jar) $4=out_dir_name (the
# primary tree, e.g. "vineflower") $5=fallback_dir_name (e.g. "fallback")
# $6=noinner_dir_name (e.g. "vineflower-noinner"; pass "" to skip the
# secondary view entirely — no caller does, but keeps this function usable
# without it) $7=logfile $8=dash_e ("-e=<lib CSV>", or "" for v1's no library
# context) $9=cfr_extraclasspath (the SAME lib CSV colon-joined for CFR's
# --extraclasspath, or "" for v1), then "$@" (from $10) = the variant's own
# "Additional option" flags, in order, EXCLUDING --log-level=error (always
# added) and EXCLUDING -e/--add-external (dash_e is appended separately, last,
# per the header's "Undocumented Vineflower 1.12.0 CLI ordering requirement" —
# every Additional option, including --excluded-classes/--decompile-inner,
# MUST precede -e for Vineflower to actually apply it).
vf_handle_primary_timeout() {
  local module="$1" moddir="$2" jar="$3" out_dir_name="$4" fallback_dir_name="$5" \
        noinner_dir_name="$6" logfile="$7" dash_e="$8" cfr_extraclasspath="$9"
  shift 9
  local -a own_flags=("$@")
  local extracted_dir="$moddir/extracted"

  local -a isolate_prefix=("$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error)
  [[ "${#own_flags[@]}" -gt 0 ]] && isolate_prefix+=("${own_flags[@]}")
  [[ -n "$dash_e" ]] && isolate_prefix+=("$dash_e")

  vf_isolate_hung_classes "$module" "$extracted_dir" "$N5_ISOLATE_TIMEOUT" "$logfile" "${isolate_prefix[@]}"
  VFH_ISOLATE_TIME="$VF_ISOLATE_TIME"
  VFH_EXCLUDED_CLASSES=("${VF_ISOLATE_HUNG_CLASSES[@]}")

  if [[ "$VF_ISOLATE_STATUS" != "isolated" ]]; then
    # R4-isolation-unbounded-total-budget: propagate the REAL status
    # ("no_hung_class_found" or "total_budget_exhausted") instead of
    # hardcoding "no_hung_class_found" — recon.json's isolation_status field
    # must be able to tell "isolation genuinely tried every package/class and
    # found nothing" apart from "isolation gave up early on the total budget".
    VFH_ISOLATION_STATUS="$VF_ISOLATE_STATUS"
    log "$module" "T24: no single hung class found in ${VFH_ISOLATE_TIME}s (isolation_status=$VF_ISOLATE_STATUS), keeping whole-module CFR fallback"
    return 1
  fi
  log "$module" "T24: found ${#VFH_EXCLUDED_CLASSES[@]} hung class(es) in ${VFH_ISOLATE_TIME}s: ${VFH_EXCLUDED_CLASSES[*]}"

  local regex; regex="$(vf_build_excluded_classes_regex "${VFH_EXCLUDED_CLASSES[@]}")"
  local -a rerun_cmd=("$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error)
  [[ "${#own_flags[@]}" -gt 0 ]] && rerun_cmd+=("${own_flags[@]}")
  rerun_cmd+=("--excluded-classes=$regex")
  [[ -n "$dash_e" ]] && rerun_cmd+=("$dash_e")

  rm -rf "${moddir:?}/$out_dir_name"
  mkdir -p "$moddir/$out_dir_name"
  local t0 t1 rerun_time rerun_status
  t0="$(date +%s)"
  rerun_status="$(vf_run_timed "$jar" "$moddir/$out_dir_name" "$N5_PRIMARY_TIMEOUT" "$logfile" "${rerun_cmd[@]}")"
  t1="$(date +%s)"
  rerun_time=$(( t1 - t0 ))

  if [[ "$rerun_status" != "ok" ]]; then
    VFH_ISOLATION_STATUS="excluded_rerun_${rerun_status}"
    log "$module" "T24: excluded re-run $rerun_status after ${rerun_time}s, keeping whole-module CFR fallback"
    return 1
  fi
  log "$module" "T24: excluded re-run ok in ${rerun_time}s, $(find "$moddir/$out_dir_name" -name '*.java' | wc -l) file(s)"

  # per-hung-class CFR fallback: same convention as the existing
  # per-class "decompiler-failure marker" branch below — feed CFR the
  # top-level .class file alone; it resolves nested classes from the
  # same directory on its own.
  mkdir -p "$moddir/$fallback_dir_name"
  local hung classfile
  for hung in "${VFH_EXCLUDED_CLASSES[@]}"; do
    classfile="$extracted_dir/$hung.class"
    [[ -f "$classfile" ]] || continue
    local -a cfr_cmd=("$N5_JAVA" -jar "$N5_CFR" "$classfile" --outputdir "$moddir/$fallback_dir_name" --silent true)
    [[ -n "$cfr_extraclasspath" ]] && cfr_cmd+=(--extraclasspath "$cfr_extraclasspath")
    { printf 'CMD:'; printf ' %q' "${cfr_cmd[@]}"; printf '\n'; } >> "$logfile"
    "${cfr_cmd[@]}" >> "$logfile" 2>&1 || log "$module" "T24 fallback(cfr) for hung class $hung also failed"
  done

  if [[ -n "$noinner_dir_name" ]]; then
    local -a noinner_cmd=("$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error)
    [[ "${#own_flags[@]}" -gt 0 ]] && noinner_cmd+=("${own_flags[@]}")
    noinner_cmd+=(--decompile-inner=false)
    [[ -n "$dash_e" ]] && noinner_cmd+=("$dash_e")
    # decompile-pipeline review fix (orchestrator, 2026-09-28,
    # R2-noinner-never-fails-contract): this call was an unguarded statement.
    # vf_render_noinner_view's own doc comment and log message both promise a
    # "best-effort secondary view, never blocks the module" contract, but its
    # `return 1` on a non-"ok" status, left unguarded here under this script's
    # `set -euo pipefail`, actually ABORTED THE WHOLE SCRIPT instead — the
    # exact opposite of "never blocks". `|| true` makes the call really honor
    # its documented contract.
    vf_render_noinner_view "$module" "$extracted_dir" "$moddir/$noinner_dir_name" "$N5_ISOLATE_TIMEOUT" "$logfile" \
      "${noinner_cmd[@]}" -- "${VFH_EXCLUDED_CLASSES[@]}" || true
  fi

  VFH_PRIMARY_STATUS="ok_with_excluded"
  VFH_PRIMARY_TIME="$rerun_time"
  VFH_FALLBACK_USED="true"
  VFH_FALLBACK_REASON="primary_hang_isolated"
  VFH_ISOLATION_STATUS="isolated"
  return 0
}

# ---------------------------------------------------------------------------
# Multi-Release JAR (JEP 238) version overrides (odd/tasks/decompiler-fidelity-audit.md,
# fix for the T26b "residual 27 classes" note in docs/decompiler-bakeoff.md): a class
# nested under META-INF/versions/<N>/... inside the jar being decompiled is a real,
# ordinary, compilable class — just packaged at a special path the multi-release-jar
# mechanism (not Vineflower) understands. Vineflower 1.12.0 creates the package
# directory tree for these entries during the WHOLE-JAR primary run above but writes
# NO .java at the leaf, silently — no decompiler-failure marker, so scan_marker_files
# never sees anything wrong and the per-class CFR fallback above never triggers either.
# Verified corpus-wide 2026-09-28: 27 classes in 16 third-party jars (found via
# --third-party-libinf; see docs/decompiler-bakeoff.md's T26b section).
#
# Fix: re-decompile every META-INF/versions/<N>/ class on its own, RE-ROOTED into its
# real package path (the "META-INF/versions/<N>/" prefix stripped, so it lands at the
# same internal name Vineflower would resolve for an ordinary class), in one subset jar
# per version N, with the SAME variant command/options/library context as the real run
# — "$@" is that variant's own Additional-option flags array (v1: empty; v2/cons:
# --include-runtime=... plus the variant's fidelity flags, same convention
# vf_handle_primary_timeout's callers already build) and $6/$7 are dash_e/
# cfr_extraclasspath, same meaning as vf_handle_primary_timeout's own. A subset run
# that itself times out reuses vf_isolate_hung_classes/vf_build_excluded_classes_regex
# — the EXACT SAME T24 machinery a whole-jar hang uses — just pointed at the temporary
# re-rooted extraction directory instead of $moddir/extracted, since every T24 helper
# already takes extracted_dir as a plain parameter and needs no changes to be reused
# here.
#
# Shared by decompile_module (v1) and decompile_module_variant (v2/cons) — called
# unconditionally, right after the whole-jar primary decompile (and any T24 hang
# handling) settles, for EVERY jar, so every population this script has
# (--bin-ext/--extra-tridium/--third-party-libinf/plain modules, which all funnel
# through one of these two functions) gets this fix for free with no separate call
# site. A no-op (both outputs empty/default) when the jar has no META-INF/versions/ at
# all — the overwhelming majority of this corpus.
#
# $1=module $2=moddir $3=out_dir_name (the variant's primary tree, e.g. "vineflower")
# $4=fallback_dir_name (e.g. "fallback") $5=logfile $6=dash_e ("-e=<lib CSV>", or "" for
# v1) $7=cfr_extraclasspath (the same lib CSV colon-joined, or "" for v1), then "$@"
# (from $8) = the variant's own Additional-option flags, in the exact order to pass —
# EXCLUDING --log-level=error (always added) and EXCLUDING -e/--add-external (dash_e is
# appended separately, last, per the header's "Undocumented Vineflower 1.12.0 CLI
# ordering requirement").
#
# Writes <moddir>/$3/META-INF/versions/<N>/<pkg>/<Class>.java for every class Vineflower
# decompiled, <moddir>/$4/META-INF/versions/<N>/<pkg>/<Class>.java (CFR) for every class
# it did not, and sets (globals, read by the caller immediately after calling):
#   VFM_VERSIONS_JSON     JSON object "N": {"classes": n, "decompiled": n, "fallback": n}
#                          (VFM_VERSIONS_JSON="{}" when no versions/ entries exist)
#   VFM_UNREPRESENTED     bash array of "N:<internal-name>", one entry per class NEITHER
#                          decompiler produced a file for — silent zero is forbidden:
#                          the caller records this in recon.json so a class Vineflower
#                          silently skipped can never again go unnoticed the way the 27
#                          corpus classes above did.
vf_handle_mrjar_versions() {
  local module="$1" moddir="$2" out_dir_name="$3" fallback_dir_name="$4" logfile="$5" \
        dash_e="$6" cfr_extraclasspath="$7"
  shift 7
  local -a own_flags=("$@")
  local extracted_dir="$moddir/extracted"
  local versions_root="$extracted_dir/META-INF/versions"

  VFM_VERSIONS_JSON="{}"
  VFM_UNREPRESENTED=()

  [[ -d "$versions_root" ]] || return 0

  local -a versions=()
  readarray -t versions < <(
    find "$versions_root" -mindepth 1 -maxdepth 1 -type d -print \
      | while IFS= read -r d; do basename "$d"; done \
      | sort -n
  )
  [[ "${#versions[@]}" -gt 0 ]] || return 0

  local -a isolate_prefix=("$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error)
  [[ "${#own_flags[@]}" -gt 0 ]] && isolate_prefix+=("${own_flags[@]}")
  [[ -n "$dash_e" ]] && isolate_prefix+=("$dash_e")

  local versions_json="{" first_v=true n
  for n in "${versions[@]}"; do
    # a real MRJAR release directory name is always numeric (JEP 238); ignore
    # anything else under versions/ rather than mis-decompiling it as one.
    [[ "$n" =~ ^[0-9]+$ ]] || continue
    local ver_dir="$versions_root/$n"

    local -a internal_names=()
    local f rel
    while IFS= read -r f; do
      rel="${f#"$ver_dir"/}"
      internal_names+=("${rel%.class}")
    done < <(find "$ver_dir" -name '*.class' | sort)
    local total="${#internal_names[@]}"
    [[ "$total" -gt 0 ]] || continue

    log "$module" "mrjar: version $n has $total override class(es), re-decompiling re-rooted"

    local reroot_dir; reroot_dir="$(mktemp -d)"
    local internal
    for internal in "${internal_names[@]}"; do
      mkdir -p "$reroot_dir/$(dirname "$internal")"
      cp "$ver_dir/$internal.class" "$reroot_dir/$internal.class"
    done

    local subset_jar="$reroot_dir.jar"
    printf '%s\n' "${internal_names[@]}" | vf_build_subset_jar "$reroot_dir" "$subset_jar"

    local target_dir="$moddir/$out_dir_name/META-INF/versions/$n"
    local fb_dir="$moddir/$fallback_dir_name/META-INF/versions/$n"
    rm -rf "$target_dir"; mkdir -p "$target_dir"
    local status
    status="$(vf_run_timed "$subset_jar" "$target_dir" "$N5_PRIMARY_TIMEOUT" "$logfile" "${isolate_prefix[@]}")"

    if [[ "$status" == "timeout" ]]; then
      log "$module" "mrjar: version $n whole-subset run timed out, isolating hung class(es) (T24, shared path)"
      vf_isolate_hung_classes "$module" "$reroot_dir" "$N5_ISOLATE_TIMEOUT" "$logfile" "${isolate_prefix[@]}"
      if [[ "$VF_ISOLATE_STATUS" == "isolated" ]]; then
        local regex; regex="$(vf_build_excluded_classes_regex "${VF_ISOLATE_HUNG_CLASSES[@]}")"
        local -a rerun_cmd=("$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error)
        [[ "${#own_flags[@]}" -gt 0 ]] && rerun_cmd+=("${own_flags[@]}")
        rerun_cmd+=("--excluded-classes=$regex")
        [[ -n "$dash_e" ]] && rerun_cmd+=("$dash_e")
        rm -rf "$target_dir"; mkdir -p "$target_dir"
        status="$(vf_run_timed "$subset_jar" "$target_dir" "$N5_PRIMARY_TIMEOUT" "$logfile" "${rerun_cmd[@]}")"
        if [[ "$status" == "ok" ]]; then
          mkdir -p "$fb_dir"
          local hung classfile
          for hung in "${VF_ISOLATE_HUNG_CLASSES[@]}"; do
            classfile="$reroot_dir/$hung.class"
            [[ -f "$classfile" ]] || continue
            local -a cfr_cmd=("$N5_JAVA" -jar "$N5_CFR" "$classfile" --outputdir "$fb_dir" --silent true)
            [[ -n "$cfr_extraclasspath" ]] && cfr_cmd+=(--extraclasspath "$cfr_extraclasspath")
            "${cfr_cmd[@]}" >> "$logfile" 2>&1 \
              || log "$module" "mrjar: version $n CFR fallback for hung class $hung also failed"
          done
        fi
      fi
    fi

    if [[ "$status" != "ok" ]]; then
      log "$module" "mrjar: version $n whole-subset run status=$status, falling back to CFR for all $total class(es)"
      mkdir -p "$fb_dir"
      local -a cfr_cmd=("$N5_JAVA" -jar "$N5_CFR" "$subset_jar" --outputdir "$fb_dir" --silent true)
      [[ -n "$cfr_extraclasspath" ]] && cfr_cmd+=(--extraclasspath "$cfr_extraclasspath")
      "${cfr_cmd[@]}" >> "$logfile" 2>&1 \
        || log "$module" "mrjar: version $n whole-subset CFR fallback also failed"
    fi

    # per-class marker scan (same pattern as the whole-module one in
    # decompile_module/decompile_module_variant): a class Vineflower DID emit
    # a .java for but flagged internally still needs a CFR retry.
    #
    # decompile-pipeline review fix (orchestrator, 2026-09-28,
    # R3-mrjar-tally-marker-miscount / R2-mrjar-decompiled-count-hides-cfr-retry):
    # remember which internal names were marker-flagged here (is_marker_flagged),
    # so the tally below can tell "primary genuinely succeeded cleanly" apart
    # from "primary left a decompiler-failure marker and CFR replaced it" — the
    # marker-flagged .java stays in target_dir (Vineflower writes it even for a
    # class it flags as failed), so without this the tally counted every
    # marker-flagged-and-CFR-retried class as a clean "decompiled" success and
    # never revealed the retry happened at all.
    local -A is_marker_flagged=()
    local marker_files; marker_files="$(scan_marker_files "$target_dir")"
    if [[ -n "$marker_files" ]]; then
      mkdir -p "$fb_dir"
      local javafile relj classrel
      while IFS= read -r javafile; do
        [[ -z "$javafile" ]] && continue
        relj="${javafile#"$target_dir"/}"
        is_marker_flagged["${relj%.java}"]=1
        classrel="${relj%.java}.class"
        [[ -f "$reroot_dir/$classrel" ]] || continue
        local -a cfr_cmd=("$N5_JAVA" -jar "$N5_CFR" "$reroot_dir/$classrel" --outputdir "$fb_dir" --silent true)
        [[ -n "$cfr_extraclasspath" ]] && cfr_cmd+=(--extraclasspath "$cfr_extraclasspath")
        "${cfr_cmd[@]}" >> "$logfile" 2>&1 || true
      done <<< "$marker_files"
    fi

    # R2-mrjar-inner-class-count: tally in TOP-LEVEL classes only — the SAME
    # unit vf_list_top_level_classes/vf_classes_for_top_level use everywhere
    # else in this file. A nested/local/anon class (Name$N) never gets its own
    # .java file; it is folded into its enclosing top-level class's source.
    # Tallying raw .class files here (the old $internal_names, still used
    # above to build the reroot/subset jar with every class Vineflower needs)
    # produced FALSE "unrepresented" entries for every override that happened
    # to carry an inner class, even though it was fully represented inside its
    # parent's .java (confirmed empirically: a synthetic override with one
    # anonymous Runnable reported its Name$1 as unrepresented every time).
    local -a top_level_names=()
    for internal in "${internal_names[@]}"; do
      case "$(basename "$internal")" in
        *'$'*) continue ;;
        *) top_level_names+=("$internal") ;;
      esac
    done
    total="${#top_level_names[@]}"

    # tally: for each TOP-LEVEL class, fallback iff it was marker-flagged AND
    # CFR actually produced a replacement in fb_dir; decompiled iff a .java
    # exists in target_dir at its exact relative path (and it wasn't a marker
    # CFR successfully replaced); fallback iff not decompiled but a .java
    # exists in fb_dir; unrepresented (silent zero — must never go unrecorded)
    # iff neither.
    local decompiled=0 fallback=0
    for internal in "${top_level_names[@]}"; do
      if [[ -n "${is_marker_flagged[$internal]:-}" && -f "$fb_dir/$internal.java" ]]; then
        fallback=$((fallback + 1))
      elif [[ -f "$target_dir/$internal.java" ]]; then
        decompiled=$((decompiled + 1))
      elif [[ -f "$fb_dir/$internal.java" ]]; then
        fallback=$((fallback + 1))
      else
        VFM_UNREPRESENTED+=("$n:$internal")
      fi
    done
    log "$module" "mrjar: version $n top-level classes=$total decompiled=$decompiled fallback=$fallback unrepresented=$((total - decompiled - fallback))"

    $first_v || versions_json+=","
    first_v=false
    versions_json+="\"$n\": {\"classes\": $total, \"decompiled\": $decompiled, \"fallback\": $fallback}"

    rm -rf "$reroot_dir" "$subset_jar"
  done
  versions_json+="}"
  VFM_VERSIONS_JSON="$versions_json"
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
  # T27: fallback/ belongs to THIS run only (v2/cons already clear theirs); a
  # stale CFR file from an earlier attempt would otherwise pose as current.
  rm -rf "${moddir:?}/fallback"
  # decompile-pipeline review fix (orchestrator, 2026-09-28): vineflower-noinner/
  # (T24's best-effort --decompile-inner=false secondary view) is written ONLY
  # inside vf_render_noinner_view, which runs ONLY when THIS run's primary hangs
  # and isolation finds a hung class. A rerun where nothing hangs never touches
  # vineflower-noinner/ at all — without this, a noinner/ view from an EARLIER
  # run that used to hang would silently survive and a reader could mistake it
  # for current output, exactly the "stale fallback/" failure mode T27 already
  # fixed for fallback/ above; clear it unconditionally here too.
  rm -rf "${moddir:?}/vineflower-noinner"
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
  local excluded_classes_json="[]" isolate_time="0" isolation_status="" timeout_attempt_time=""
  local produced
  produced="$(find "$moddir/vineflower" -name '*.java' | wc -l)"

  # T24: a hung whole-jar run gets ONE isolation attempt before falling back
  # to whole-module CFR — see vf_handle_primary_timeout's doc comment. v1 has
  # no library context at all (no -e, no --extraclasspath).
  if [[ "$primary_status" == "timeout" ]]; then
    timeout_attempt_time="$primary_time"
    local -a v1_own_flags=()
    if vf_handle_primary_timeout "$module" "$moddir" "$jar" "vineflower" "fallback" \
        "vineflower-noinner" "$LOG_DIR/$module.log" "" "" "${v1_own_flags[@]}"; then
      primary_status="$VFH_PRIMARY_STATUS"
      primary_time="$VFH_PRIMARY_TIME"
      fallback_used="$VFH_FALLBACK_USED"
      fallback_reason="$VFH_FALLBACK_REASON"
    fi
    isolation_status="$VFH_ISOLATION_STATUS"
    isolate_time="$VFH_ISOLATE_TIME"
    excluded_classes_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${VFH_EXCLUDED_CLASSES[@]}")"
    produced="$(find "$moddir/vineflower" -name '*.java' | wc -l)"
  fi

  if [[ "$primary_status" == "ok" || "$primary_status" == "ok_with_excluded" ]] \
      && [[ "$produced" -gt 0 || "$class_count" -eq 0 ]]; then
    # primary produced output for the whole jar (either the plain run, or
    # T24's excluded re-run); scan for the decompiler's own failure markers
    # (not application log strings) left in ANY class it did decompile — a
    # hung class isn't the only way one can fail — and re-run just those
    # through CFR into fallback/, on top of whatever T24 already put there
    # for the hung class(es) themselves.
    local marker_files
    marker_files="$(scan_marker_files "$moddir/vineflower")"
    if [[ -n "$marker_files" ]]; then
      fallback_used="true"
      [[ "$fallback_reason" == "none" ]] && fallback_reason="per_class_decompiler_marker"
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
  else
    # whole-jar fallback to CFR — primary either failed outright, or hung and
    # T24's isolation+excluded-rerun did not resolve it either.
    fallback_used="true"
    fallback_reason="primary_${primary_status}_whole_module"
    log "$module" "fallback(cfr) whole-module reason=$fallback_reason"
    mkdir -p "$moddir/fallback"
    "$N5_JAVA" -jar "$N5_CFR" "$jar" --outputdir "$moddir/fallback" --silent true \
      >> "$LOG_DIR/$module.log" 2>&1 || log "$module" "fallback(cfr) also failed"
  fi

  # Multi-Release JAR (JEP 238) version overrides — see vf_handle_mrjar_versions's doc
  # comment. Runs unconditionally, independent of the whole-jar primary_status above (a
  # META-INF/versions/ entry is a separate namespace this jar may carry regardless of
  # how the base classes decompiled). v1 has no library context at all (no -e, no
  # --extraclasspath), same as the T24 call above.
  local -a v1_mrjar_own_flags=()
  vf_handle_mrjar_versions "$module" "$moddir" "vineflower" "fallback" "$LOG_DIR/$module.log" \
    "" "" "${v1_mrjar_own_flags[@]}"
  local mrjar_unrepresented_json
  mrjar_unrepresented_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${VFM_UNREPRESENTED[@]}")"

  write_recon "$module" "$jar" "$moddir" "$primary_status" "$primary_time" \
    "$fallback_used" "$fallback_reason" "$class_count" \
    "$excluded_classes_json" "$isolate_time" "$isolation_status" "$timeout_attempt_time" \
    "$VFM_VERSIONS_JSON" "$mrjar_unrepresented_json"
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
# Shared by both the modules/ and bin/ext/ scans below (T19-hardening fix 5,
# RDD review-56f32a364d16cec0: the two scans used to be near-identical
# duplicated while-loop bodies). Extracts $1's own LIB-INF/*.jar entries,
# copies each into $2 keyed by ITS OWN sha256 (content-addressed — naturally
# dedups identical embedded libs shipped by multiple modules; a changed lib
# gets a different key, never collides with or overwrites an old one), and
# appends every resulting sha256 to the caller's PREP_CURRENT_LIBINF_SHAS
# array (T19-hardening fix 3's pruning list — see compute_v2_library_jars).
# Updates the caller's PREP_ADDED_COUNT.
cache_source_jar_libinf() {
  local jar="$1" cache_dir="$2" force="$3"
  local tmpdir libjar libsha dest
  tmpdir="$(mktemp -d)"
  # decompile-pipeline review fix (orchestrator, 2026-09-28,
  # R3-002/R4-002): exit 11 ("no matching files") is the ordinary case for
  # the overwhelming majority of jars, which carry no LIB-INF/*.jar at all —
  # but unzip ALSO returns nonzero (and still writes whatever bytes it
  # managed, e.g. a CRC-mismatched entry) on a genuinely corrupt/truncated
  # LIB-INF entry, which this used to swallow identically and silently via a
  # blanket `2>/dev/null || true`. A corrupted entry would then be hashed and
  # cached under ITS OWN (wrong) sha256 as if it were a legitimate distinct
  # lib jar, with no trace anywhere that the extraction itself had failed.
  # Any OTHER nonzero exit is now surfaced as a warning (unzip's own message,
  # captured instead of discarded) so a reader can tell "no LIB-INF here"
  # apart from "LIB-INF extraction actually failed".
  local unzip_out unzip_rc=0
  unzip_out="$(unzip -o -q "$jar" 'LIB-INF/*.jar' -d "$tmpdir" 2>&1)" || unzip_rc=$?
  if [[ "$unzip_rc" -ne 0 && "$unzip_rc" -ne 11 ]]; then
    log "_prepare-libcache" "WARNING: unzip exited $unzip_rc extracting LIB-INF/*.jar from $jar — a partially/incorrectly extracted entry may be cached under a misleading sha256; unzip output: $unzip_out"
  fi
  while IFS= read -r -d '' libjar; do
    libsha="$(sha256_of "$libjar")"
    [[ -z "$libsha" ]] && continue
    PREP_CURRENT_LIBINF_SHAS+=("$libsha")
    dest="$cache_dir/$libsha.jar"
    if [[ "$force" == "true" || ! -f "$dest" ]]; then
      cp "$libjar" "$dest.tmp.$$"
      mv "$dest.tmp.$$" "$dest"
      PREP_ADDED_COUNT=$((PREP_ADDED_COUNT + 1))
    fi
  done < <(find "$tmpdir" -name '*.jar' -print0 2>/dev/null)
  rm -rf "$tmpdir"
}

# T19-hardening (RDD review-56f32a364d16cec0) additions folded into this
# function, on top of the original T19 fix:
#  - completion sentinel (.complete, recording the expected *.jar count),
#    written LAST and atomically (write-to-temp then rename) — a reader
#    (v2_libcache_ready) can then tell a COMPLETE cache from one an
#    interrupted run left half-built, instead of trusting the directory's
#    mere existence (fix 2).
#  - _source_shas.tsv now also records each source jar's own size+mtime, so a
#    jar replaced at the SAME PATH after this manifest was written gets
#    re-hashed live by compute_v2_idempotency_key instead of silently keeping
#    a now-wrong cached hash forever (fix 1; see load_v2_source_shas below).
#  - _current_entries.tsv records the sha256 of every LIB-INF jar CURRENTLY
#    referenced by a source jar, THIS run. compute_v2_library_jars only offers
#    a cache entry listed here — the cache dir itself stays content-addressed
#    and is never pruned (an old recon.json's idempotency key may still name a
#    superseded entry), but a stale/orphaned version drops out of every
#    FUTURE decompile's -e= list instead of accumulating forever (fix 3).
prepare_v2_libcache() {
  local force="${1:-false}"
  local cache_dir="$N5_OUT_DIR/_v2-libcache"
  # T23 (RDD advisory R4): a zero-jar scan (mistyped or unmounted
  # $N5_MODULES_DIR) must fail loudly BEFORE touching the cache. Otherwise it
  # would publish a "complete" cache with an empty _current_entries.tsv, and
  # every later v2/cons decompile would silently lose all LIB-INF context.
  if ! find -L "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' ! -name docSource.jar -print -quit 2>/dev/null | grep -q . \
      && ! find -L "$N5_BIN_EXT_DIR" -name '*.jar' -print -quit 2>/dev/null | grep -q .; then
    echo "FATAL: --prepare-libcache found no source jars under N5_MODULES_DIR=$N5_MODULES_DIR or N5_BIN_EXT_DIR=$N5_BIN_EXT_DIR; refusing to rebuild $cache_dir (an existing cache is left untouched)." >&2
    exit 2
  fi
  mkdir -p "$cache_dir"
  # An in-progress rebuild must never look complete to a concurrent reader.
  rm -f "$cache_dir/.complete"

  PREP_ADDED_COUNT=0
  PREP_CURRENT_LIBINF_SHAS=()
  local -a all_source_jars=()
  local jar scanned=0

  # $N5_MODULES_DIR is flat (-maxdepth 1); $N5_BIN_EXT_DIR is scanned
  # recursively, matching compute_v2_library_jars' own bin/ext scan (and
  # decompile_binext's), which is NOT -maxdepth 1 — bin/ext ships several
  # jars nested under subdirectories (bcfips/, bcstd/, jxbrowser/, system/,
  # securityBridge/). A --maxdepth 1 scan here would silently miss those
  # jars' own LIB-INF content.
  while IFS= read -r -d '' jar; do
    [[ "$(basename "$jar" .jar)" == "docSource" ]] && continue
    all_source_jars+=("$jar")
    scanned=$((scanned + 1))
    cache_source_jar_libinf "$jar" "$cache_dir" "$force"
  done < <(find -L "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0 2>/dev/null)
  if [[ -d "$N5_BIN_EXT_DIR" ]]; then
    while IFS= read -r -d '' jar; do
      all_source_jars+=("$jar")
      scanned=$((scanned + 1))
      cache_source_jar_libinf "$jar" "$cache_dir" "$force"
    done < <(find -L "$N5_BIN_EXT_DIR" -name '*.jar' -print0 2>/dev/null)
  fi

  # Performance (not a correctness requirement): also pre-hash every scanned
  # module/bin-ext jar ITSELF (not just its LIB-INF content), plus its size and
  # mtime, into one manifest, _source_shas.tsv (tab-separated:
  # sha256<TAB>size<TAB>mtime<TAB>path). compute_v2_idempotency_key needs every
  # library jar's sha256 on every single-module v2/cons invocation; without
  # this, each of ~250 module invocations would separately re-hash the same
  # ~360 jars — expensive when $N5_MODULES_DIR/$N5_BIN_EXT_DIR live on a slow
  # mount (e.g. /mnt/c under WSL). size+mtime let a later run detect a jar that
  # changed at the SAME path without rebuilding the whole manifest (fix 1).
  # Rebuilt fresh each --prepare-libcache run (jars rarely change; --force is
  # not required to refresh it).
  if [[ "${#all_source_jars[@]}" -gt 0 ]]; then
    : > "$cache_dir/_source_shas.tsv.tmp.$$"
    local p sha size mtime
    for p in "${all_source_jars[@]}"; do
      sha="$(sha256_of "$p")"
      size="$(stat -c '%s' "$p" 2>/dev/null || echo 0)"
      mtime="$(stat -c '%Y' "$p" 2>/dev/null || echo 0)"
      printf '%s\t%s\t%s\t%s\n' "$sha" "$size" "$mtime" "$p" >> "$cache_dir/_source_shas.tsv.tmp.$$"
    done
    mv "$cache_dir/_source_shas.tsv.tmp.$$" "$cache_dir/_source_shas.tsv"
  fi

  if [[ "${#PREP_CURRENT_LIBINF_SHAS[@]}" -gt 0 ]]; then
    printf '%s\n' "${PREP_CURRENT_LIBINF_SHAS[@]}" | sort -u > "$cache_dir/_current_entries.tsv.tmp.$$"
    mv "$cache_dir/_current_entries.tsv.tmp.$$" "$cache_dir/_current_entries.tsv"
  else
    : > "$cache_dir/_current_entries.tsv"
  fi

  local actual_count
  actual_count="$(find -L "$cache_dir" -maxdepth 1 -name '*.jar' | wc -l)"
  printf 'count=%s\n' "$actual_count" > "$cache_dir/.complete.tmp.$$"
  mv "$cache_dir/.complete.tmp.$$" "$cache_dir/.complete"

  log "_prepare-libcache" "scanned $scanned module/bin-ext jar(s), added/updated $PREP_ADDED_COUNT lib jar(s), cache now has $actual_count entry/entries in $cache_dir"
}

# T19-hardening fix 2: the completion sentinel. Both --variant v2 and
# --variant cons call this instead of a bare `[[ -d ... ]]` before trusting
# the libcache — an interrupted or in-progress --prepare-libcache must never
# be treated as ready.
#
# BUGFIX (found via a bats test that symlinks organized/_v2-libcache/,
# 2026-09-28): every `find` in this file that scans `$cache_dir` or
# `$N5_OUT_DIR/_v2-libcache` now passes `-L`. GNU find's default (`-P`) mode
# does NOT descend into a directory given as ITS OWN starting argument when
# that argument is a symlink (confirmed empirically: `find symlink-to-dir
# -maxdepth 1 -name '*.jar'` silently returns 0 results, while `[[ -d
# symlink-to-dir ]]` and `[[ -f symlink-to-dir/x ]]` both correctly follow it)
# — a real correctness gap, not just a test artifact, if `_v2-libcache` (or
# $N5_OUT_DIR itself) is ever reached via a symlink. Without `-L`,
# `v2_libcache_ready` would see `.complete`'s recorded count via `-f` (which
# DOES follow the symlink) but `actual=0` via `find` (which did NOT) — a
# spurious mismatch that then made `prepare_v2_libcache` rebuild into the
# SAME (symlinked, so really the shared) cache dir with a genuinely-empty
# source-jar scan, overwriting `.complete` with `count=0` while the physical
# jar files were left untouched — corrupting a shared cache for every later
# reader. `-L` makes every one of these `find` calls behave the same whether
# the path is a real directory or a symlink to one.
v2_libcache_ready() {
  local cache_dir="$N5_OUT_DIR/_v2-libcache"
  [[ -d "$cache_dir" ]] || return 1
  [[ -f "$cache_dir/.complete" ]] || return 1
  local recorded actual
  recorded="$(grep -o 'count=[0-9]*' "$cache_dir/.complete" 2>/dev/null | cut -d= -f2)"
  [[ -n "$recorded" ]] || return 1
  actual="$(find -L "$cache_dir" -maxdepth 1 -name '*.jar' | wc -l)"
  [[ "$recorded" == "$actual" ]]
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
  done < <(find -L "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0)
  while IFS= read -r -d '' jar; do
    V2_ALL_LIB_JARS+=("$jar")
  done < <(find -L "$N5_BIN_EXT_DIR" -name '*.jar' -print0 2>/dev/null)

  # T19-hardening fix 3: only offer a libcache entry CURRENTLY referenced by
  # some source jar's LIB-INF, per prepare_v2_libcache's _current_entries.tsv
  # (rebuilt fresh every --prepare-libcache run). The cache dir itself is
  # content-addressed and never pruned (an old recon.json's idempotency key
  # may still name a superseded entry), but a stale/orphaned version must not
  # silently re-enter a NEW decompile's -e= list forever. A cache built before
  # this fix existed (no _current_entries.tsv yet) falls back to the old
  # "offer everything in the cache dir" behavior rather than excluding
  # everything.
  local current_manifest="$N5_OUT_DIR/_v2-libcache/_current_entries.tsv"
  local -A current_shas=()
  if [[ -f "$current_manifest" ]]; then
    local sha
    while IFS= read -r sha; do
      [[ -n "$sha" ]] && current_shas["$sha"]=1
    done < "$current_manifest"
  fi
  while IFS= read -r -d '' jar; do
    local base; base="$(basename "$jar" .jar)"
    if [[ -f "$current_manifest" ]] && [[ -z "${current_shas[$base]:-}" ]]; then
      continue
    fi
    V2_ALL_LIB_JARS+=("$jar")
  done < <(find -L "$N5_OUT_DIR/_v2-libcache" -maxdepth 1 -name '*.jar' -print0 2>/dev/null)
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

# Lazily loads $N5_OUT_DIR/_v2-libcache/_source_shas.tsv (prepare_v2_libcache's
# performance manifest: sha256<TAB>size<TAB>mtime<TAB>path, one line per
# scanned module/bin-ext jar) into V2_SOURCE_SHA_BY_PATH/_SIZE_BY_PATH/
# _MTIME_BY_PATH, once per process. A path with no manifest entry (the
# manifest is missing entirely, or a jar was added after --prepare-libcache
# last ran) is simply absent from the maps — compute_v2_idempotency_key falls
# back to hashing it directly, so a stale/missing manifest only costs
# performance, never correctness. (T19-hardening fix 5 note: this doc comment
# used to sit above load_v2_source_shas but actually documented BOTH this
# function and compute_v2_idempotency_key's key formula below it — split so
# each function's comment sits directly above it.)
declare -A V2_SOURCE_SHA_BY_PATH=()
declare -A V2_SOURCE_SIZE_BY_PATH=()
declare -A V2_SOURCE_MTIME_BY_PATH=()
V2_SOURCE_SHA_LOADED="false"
load_v2_source_shas() {
  [[ "$V2_SOURCE_SHA_LOADED" == "true" ]] && return 0
  V2_SOURCE_SHA_LOADED="true"
  local manifest="$N5_OUT_DIR/_v2-libcache/_source_shas.tsv"
  [[ -f "$manifest" ]] || return 0
  local hash size mtime path
  while IFS=$'\t' read -r hash size mtime path; do
    [[ -z "$hash" ]] && continue
    V2_SOURCE_SHA_BY_PATH["$path"]="$hash"
    V2_SOURCE_SIZE_BY_PATH["$path"]="$size"
    V2_SOURCE_MTIME_BY_PATH["$path"]="$mtime"
  done < "$manifest"
}

# T19-hardening fix 1: a manifest entry is trusted only when the jar's CURRENT
# size+mtime still match what was recorded when the manifest was written — a
# jar replaced at the same path (e.g. a module upgrade) after
# --prepare-libcache last ran is re-hashed live here instead of silently
# keeping a now-wrong cached sha256 forever. Prints the trustworthy cached
# hash and returns 0, or returns 1 (nothing printed) when the entry is
# missing or stale, leaving the caller to hash $1 itself.
v2_source_sha_current() {
  local p="$1"
  load_v2_source_shas
  local cached="${V2_SOURCE_SHA_BY_PATH[$p]:-}"
  [[ -z "$cached" ]] && return 1
  local cur_size cur_mtime
  cur_size="$(stat -c '%s' "$p" 2>/dev/null || true)"
  cur_mtime="$(stat -c '%Y' "$p" 2>/dev/null || true)"
  if [[ -n "$cur_size" ]] && [[ "$cur_size" == "${V2_SOURCE_SIZE_BY_PATH[$p]:-}" ]] \
      && [[ "$cur_mtime" == "${V2_SOURCE_MTIME_BY_PATH[$p]:-}" ]]; then
    printf '%s' "$cached"
    return 0
  fi
  return 1
}

# T19 fix, requirement 2: idempotency key = sha256 of (module jar sha256 +
# sorted library-set sha256 list + JDK home + flag list + tool jar sha256s). A
# change in ANY of these must trigger a re-decompile, not just a changed module
# jar. Library jars already living in $N5_OUT_DIR/_v2-libcache/ are keyed by
# their own sha256 already (their filename IS the hash), so those are reused
# directly; every other jar in the set (every $N5_MODULES_DIR / $N5_BIN_EXT_DIR
# jar) is looked up via v2_source_sha_current (T19-hardening fix 1's staleness
# check) and only actually re-hashed (one batched `sha256sum` call, not one
# process per jar — the full set, V2_LIB_ARRAY, can be ~450 entries) when the
# manifest entry is missing or stale.
#
# BUGFIX (found running --variant cons for real, 2026-09-28): this function
# used to read the global $V2_FLAGS_JSON directly instead of taking the
# caller's flags as a parameter — under `set -u` that crashed a cons-only
# invocation outright (build_v2_flags is never called on the cons path, so
# V2_FLAGS_JSON was unbound), and even when V2_FLAGS_JSON happened to be set
# (e.g. a v2 run earlier in the same process), it silently used v2's flags for
# a cons idempotency key too, so v2 and cons could never actually be told
# apart by their key. flags_json is now an explicit 4th argument.
compute_v2_idempotency_key() {
  local jar_sha="$1"
  local vf_sha="$2" cfr_sha="$3" flags_json="$4"
  local -a lib_hashes=()
  local -a to_hash=()
  local p cached
  for p in "${V2_LIB_ARRAY[@]}"; do
    if [[ "$p" == "$N5_OUT_DIR/_v2-libcache/"* ]]; then
      lib_hashes+=("$(basename "$p" .jar)")
      continue
    fi
    if cached="$(v2_source_sha_current "$p")"; then
      lib_hashes+=("$cached")
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
    printf 'flags=%s\n' "$flags_json"
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
# T19-hardening fix 4: unzip's exit status is now checked explicitly, and the
# extraction-provenance marker is written only after VERIFYING the extracted
# .class count matches the jar's own listing. This function is reached from
# inside `if decompile_module_v2 ...`/`if "$decompile_fn" ...` in the run_*
# drivers below, where bash disables errexit for the ENTIRE call chain (a
# well-known bash gotcha: `if cmd; then` suppresses -e for every command cmd
# runs, transitively) — so an unchecked unzip failure here would otherwise
# fall through silently and this marker would get written even for a
# failed/partial extraction. Returns 1 (marker withheld) on either failure.
ensure_extracted_for_v2() {
  local jar="$1" moddir="$2" _force_unused="$3" module="$4" variant_label="${5:-v2}"
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
    log "$module" "$variant_label reusing existing extracted/+resources/ (jar sha256 $sha matches extracted/.jar_sha256)"
    return 0
  fi

  mkdir -p "$moddir/extracted" "$moddir/resources"
  log "$module" "$variant_label extracting $jar (extracted/ missing, empty, or stale vs the current jar sha256)"
  rm -rf "${moddir:?}/extracted"
  mkdir -p "$moddir/extracted"

  local unzip_rc=0
  unzip -o -q "$jar" -d "$moddir/extracted" || unzip_rc=$?
  if [[ "$unzip_rc" -ne 0 ]]; then
    log "$module" "$variant_label FATAL: unzip exited $unzip_rc extracting $jar — not writing the extraction-provenance marker"
    return 1
  fi
  local jar_class_count extracted_class_count
  jar_class_count="$(unzip -l "$jar" 2>/dev/null | grep -c '\.class$' || true)"
  extracted_class_count="$(find "$moddir/extracted" -name '*.class' | wc -l)"
  if [[ "$jar_class_count" != "$extracted_class_count" ]]; then
    log "$module" "$variant_label FATAL: extraction verification failed for $jar (jar lists $jar_class_count .class entries, extracted/ has $extracted_class_count) — not writing the extraction-provenance marker"
    return 1
  fi
  printf '%s' "$sha" > "$moddir/extracted/.jar_sha256"

  rm -rf "${moddir:?}/resources"
  mkdir -p "$moddir/resources"
  ( cd "$moddir/extracted" && find . -type f ! -name '*.class' ! -name '.jar_sha256' -print0 ) \
    | while IFS= read -r -d '' f; do
        mkdir -p "$moddir/resources/$(dirname "$f")"
        cp "$moddir/extracted/$f" "$moddir/resources/$f"
      done
}

# B118 §118.1's conservative + line-mapped view (niagara5-block118.md): the
# resugaring toggles OFF, ORIGINAL-source line mapping ON. Every flag name is
# confirmed to exist in vineflower-1.12.0.jar's own --help (verified this
# session), except DUMP_ORIGINAL_LINES, which --help does NOT print — it is
# read from the constant pool of
# org/jetbrains/java/decompiler/main/extern/IFernflowerPreferences.class
# (`javap -constants`: DUMP_ORIGINAL_LINES = "__dump_original_lines__"), per
# B118 §118.1. It is passed separately as CONS_HIDDEN_FLAG rather than folded
# into CONS_FLAG_NAMES/VALUES, because build_cons_flags' name//-/_  ->  JSON-key
# transform (borrowed from build_v2_flags) would turn its leading double
# underscore into a confusing JSON key; it is still recorded, verbatim, in
# recon.json's "cons".flags.
CONS_FLAG_NAMES=(pattern-matching decompile-switch-expressions ternary-in-if prettify-ifs
  inline-simple-lambdas bytecode-source-mapping)
CONS_FLAG_VALUES=(false false false false false true)
CONS_HIDDEN_FLAG="--__dump_original_lines__=true"

build_cons_flags() {
  CONS_FLAG_ARGS=()
  local flags_json="{" first=true i
  for i in "${!CONS_FLAG_NAMES[@]}"; do
    CONS_FLAG_ARGS+=("--${CONS_FLAG_NAMES[$i]}=${CONS_FLAG_VALUES[$i]}")
    local key="${CONS_FLAG_NAMES[$i]//-/_}"
    $first || flags_json+=","
    first=false
    flags_json+="\"$key\": ${CONS_FLAG_VALUES[$i]}"
  done
  CONS_FLAG_ARGS+=("$CONS_HIDDEN_FLAG")
  flags_json+=',"__dump_original_lines__": true}'
  CONS_FLAGS_JSON="$flags_json"
}

# Merges a "$1" (recon_key: "v2" or "cons") sub-object into
# organized/<mod>/recon.json, leaving every other top-level field (v1's, and
# the other variant's) untouched (recon.json may not exist yet if this is the
# first library-context variant run on a module that never went through v1 —
# in that case a minimal file is created).
#
# Interaction with v1 (fixed in T27): v1's write_recon
# (tools/n5-recon-helper.py) now carries the "v2"/"cons" sub-objects over when
# they describe the same jar sha256, and drops (and names, under
# "dropped_stale_variants") any that describe an older jar — rerun that
# --variant to refresh it.
#
# T19 fix, requirement 7: every value that could conceivably contain a
# double-quote, backslash, or other Python-string-literal metacharacter
# (module name, JDK home path, fallback reason, ...) is passed through the
# ENVIRONMENT, never interpolated into the heredoc's text — the heredoc itself
# is quoted (<<'PYEOF'), so bash performs no expansion on it at all and the
# Python source is fixed, literal code regardless of what these values contain.
write_recon_variant() {
  local recon_key="$1" module="$2" moddir="$3" jar="$4" sha="$5" primary_status="$6" \
        primary_time="$7" fallback_used="$8" fallback_reason="$9"
  shift 9
  local status="$1" idempotency_key="$2" out_dir_name="$3"
  # T24 (optional, all default to "isolation never ran"): $4=excluded_classes as
  # a JSON array string, $5=isolate_time_seconds, $6=isolation_status (only
  # ever non-empty when the whole-jar run originally timed out), $7=
  # primary_timeout_attempt_seconds. See vf_handle_primary_timeout's doc comment.
  local excluded_classes_json="${4:-[]}" isolate_time="${5:-0}" \
        isolation_status="${6:-}" timeout_attempt_time="${7:-}"
  # Multi-Release JAR (JEP 238) version overrides (odd/tasks/decompiler-fidelity-audit.md):
  # $8=mrjar_versions as a JSON object string, $9=mrjar_unrepresented as a JSON array
  # string. See vf_handle_mrjar_versions's doc comment.
  # (a literal "{}" default inside a "${n:-...}" expansion is a known bash brace-
  # matching trap — see write_recon's identical comment above.)
  local mrjar_versions_json="${8:-}" mrjar_unrepresented_json="${9:-[]}"
  [[ -z "$mrjar_versions_json" ]] && mrjar_versions_json="{}"
  local vf_sha cfr_sha vf_version cfr_version flags_json
  vf_sha="$(sha256_of "$N5_VINEFLOWER")"
  cfr_sha="$(sha256_of "$N5_CFR")"
  vf_version="$(basename "$N5_VINEFLOWER" .jar)"
  cfr_version="$(basename "$N5_CFR" .jar)"
  if [[ "$recon_key" == "cons" ]]; then flags_json="$CONS_FLAGS_JSON"; else flags_json="$V2_FLAGS_JSON"; fi
  local markers
  markers="$(scan_marker_files "$moddir/$out_dir_name" | wc -l | tr -d ' ')"

  RECON_PATH="$moddir/recon.json" \
  RECON_KEY="$recon_key" \
  RECON_MODULE="$module" \
  RECON_JAR_PATH="$jar" \
  RECON_JAR_SHA256="$sha" \
  RECON_VF_VERSION="$vf_version" \
  RECON_VF_SHA256="$vf_sha" \
  RECON_CFR_VERSION="$cfr_version" \
  RECON_CFR_SHA256="$cfr_sha" \
  RECON_LIB_COUNT="$V2_LIB_COUNT" \
  RECON_INCLUDE_RUNTIME="$N5_JDK25_HOME" \
  RECON_FLAGS_JSON="$flags_json" \
  RECON_PRIMARY_STATUS="$primary_status" \
  RECON_PRIMARY_TIME="$primary_time" \
  RECON_FALLBACK_USED="$fallback_used" \
  RECON_FALLBACK_REASON="$fallback_reason" \
  RECON_MARKERS="$markers" \
  RECON_STATUS="$status" \
  RECON_IDEMPOTENCY_KEY="$idempotency_key" \
  RECON_EXCLUDED_CLASSES_JSON="$excluded_classes_json" \
  RECON_ISOLATE_TIME="$isolate_time" \
  RECON_ISOLATION_STATUS="$isolation_status" \
  RECON_TIMEOUT_ATTEMPT_TIME="$timeout_attempt_time" \
  RECON_MRJAR_VERSIONS="$mrjar_versions_json" \
  RECON_MRJAR_UNREPRESENTED="$mrjar_unrepresented_json" \
  python3 <<'PYEOF'
import json, os

path = os.environ["RECON_PATH"]
key = os.environ["RECON_KEY"]
try:
    with open(path) as fh:
        recon = json.load(fh)
except (OSError, json.JSONDecodeError):
    recon = {"module": os.environ["RECON_MODULE"]}

recon[key] = {
    "variant": key,
    # provenance (orchestrator note, 2026-09-28): the exact jar path actually
    # decompiled — lets a reader tell whether a run used the read-only N5
    # install or the sha256-verified local mirror
    # (niagara5-research-localcache/jar-mirror-5.0.0.28/), which are
    # byte-identical but live at different paths.
    "jar_path": os.environ["RECON_JAR_PATH"],
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
    "excluded_classes": json.loads(os.environ["RECON_EXCLUDED_CLASSES_JSON"]),
    "isolate_time_seconds": int(os.environ["RECON_ISOLATE_TIME"]),
    "mrjar_versions": json.loads(os.environ["RECON_MRJAR_VERSIONS"]),
    "mrjar_unrepresented": json.loads(os.environ["RECON_MRJAR_UNREPRESENTED"]),
}
_isolation_status = os.environ.get("RECON_ISOLATION_STATUS", "")
if _isolation_status:
    recon[key]["isolation_status"] = _isolation_status
_timeout_attempt = os.environ.get("RECON_TIMEOUT_ATTEMPT_TIME", "")
if _timeout_attempt:
    recon[key]["primary_timeout_attempt_seconds"] = int(_timeout_attempt)

with open(path, "w") as fh:
    json.dump(recon, fh, indent=2)
    fh.write("\n")
PYEOF
}

# Shared by decompile_module_v2 and decompile_module_cons (T19-hardening fix
#5's "don't duplicate" principle applied to the v2/cons split too): the
# machinery is identical between them — immutable libcache, --add-external
# library context, whole-jar timeout + CFR fallback with the same
# --extraclasspath, per-class fallback for output the primary flagged, and the
# "status=failed only when NEITHER decompiler produced anything" rule. Only
# what differs — fidelity flags, output/fallback directory names, and which
# recon.json sub-key to write — is passed in. Every internal failure this
# function must not silently swallow is checked explicitly (not left to
# errexit), because callers invoke it as `if decompile_module_v2 ...; then`,
# where bash disables errexit for this whole call chain (T19-hardening fix 4).
decompile_module_variant() {
  local variant_label="$1" out_dir_name="$2" fallback_dir_name="$3" recon_key="$4"
  local jar="$5" force="$6" moddir="$7"
  shift 7
  # "$@" = this variant's Vineflower flag args, in the order to record.

  # T19 fix, requirement 1 + T19-hardening fix 2: the library context MUST
  # come from a COMPLETE immutable cache (v2_libcache_ready, not a bare
  # directory-exists check) — fail loudly rather than silently decompiling
  # with a weaker, or an interrupted/partial, library set.
  if ! v2_libcache_ready; then
    echo "FATAL: $N5_OUT_DIR/_v2-libcache is missing or incomplete — run 'tools/n5-decompile.sh --prepare-libcache' once, serially, before any --variant $variant_label decompile (the v2/cons library context must never be built from a live organized/*/extracted/ tree, nor trusted mid-build; T19 fix + T19-hardening fix 2)." >&2
    exit 1
  fi

  local module; module="$(basename "$jar" .jar)"
  local sha; sha="$(sha256_of "$jar")"
  mkdir -p "$moddir"
  if ! ensure_extracted_for_v2 "$jar" "$moddir" "$force" "$module" "$variant_label"; then
    log "$module" "$variant_label FAILED: extraction verification failed, aborting this module's $variant_label decompile"
    return 1
  fi

  local class_count
  class_count="$(find "$moddir/extracted" -name '*.class' | wc -l)"

  compute_v2_library_jars
  build_v2_external_lists "$jar"

  local vf_sha cfr_sha
  vf_sha="$(sha256_of "$N5_VINEFLOWER")"
  cfr_sha="$(sha256_of "$N5_CFR")"

  # This variant's own flags_json (same lookup write_recon_variant uses below)
  # — NOT a hardcoded global — so v2 and cons compute genuinely different keys
  # for the same jar (bugfix found running --variant cons for real: this used
  # to read $V2_FLAGS_JSON unconditionally, which crashed a cons-only process
  # under `set -u` and would have silently collided the two variants' keys
  # even when it happened not to crash).
  local variant_flags_json
  if [[ "$recon_key" == "cons" ]]; then variant_flags_json="$CONS_FLAGS_JSON"; else variant_flags_json="$V2_FLAGS_JSON"; fi

  # T19 fix, requirement 2: idempotency key covers the module jar, the full
  # resolved library set, the JDK runtime home, the fidelity flags (so v2 and
  # cons never collide despite decompiling the same jar), and the decompiler
  # tool jars themselves.
  local idempotency_key
  idempotency_key="$(compute_v2_idempotency_key "$sha" "$vf_sha" "$cfr_sha" "$variant_flags_json")"

  if [[ "$force" != "true" ]] && [[ -f "$moddir/recon.json" ]]; then
    local prev_key prev_status
    prev_key="$(RECON_KEY="$recon_key" python3 -c "
import json, os, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
print(d.get(os.environ['RECON_KEY'], {}).get('idempotency_key', ''))
" "$moddir/recon.json" 2>/dev/null || true)"
    prev_status="$(RECON_KEY="$recon_key" python3 -c "
import json, os, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    d = {}
print(d.get(os.environ['RECON_KEY'], {}).get('status', ''))
" "$moddir/recon.json" 2>/dev/null || true)"
    # T19 fix, requirement 4: a module recorded status=failed is NEVER treated
    # as up to date, regardless of the idempotency key.
    if [[ "$prev_key" == "$idempotency_key" ]] && [[ "$prev_status" == "ok" ]]; then
      log "$module" "$variant_label up to date (idempotency key $idempotency_key), skipping"
      return 0
    fi
  fi

  # T19 fix, requirement 5: the fallback dir is cleared unconditionally at the
  # start of each run so a class that used to need the CFR fallback but no
  # longer does can never leave a stale *.java behind that a reader might
  # mistake for current output. Recreated (empty) immediately, not only inside
  # the fallback branches below: under `set -o pipefail`, `find
  # "$moddir/$fallback_dir_name" ... | wc -l` later in this function would
  # otherwise fail (find exits nonzero on a missing path, pipefail propagates
  # that through `| wc -l`), aborting via errexit whenever primary succeeds
  # and no fallback is needed.
  rm -rf "${moddir:?}/$fallback_dir_name"
  mkdir -p "$moddir/$fallback_dir_name"

  # decompile-pipeline review fix (orchestrator, 2026-09-28): same "stale
  # secondary view" hazard as v1's vineflower-noinner/ clear above — this
  # variant's own "$out_dir_name-noinner" dir is written only inside
  # vf_render_noinner_view, called only when THIS run's primary hangs, so a
  # rerun where nothing hangs would otherwise leave an earlier run's noinner
  # view sitting there posing as current.
  rm -rf "${moddir:?}/${out_dir_name}-noinner"

  rm -rf "${moddir:?}/$out_dir_name"
  mkdir -p "$moddir/$out_dir_name"
  log "$module" "$variant_label primary(vineflower) starting on $class_count classes (lib_count=$V2_LIB_COUNT, runtime=$N5_JDK25_HOME)"

  # Additional options MUST precede -e/--add-external — see the header
  # comment's "Undocumented Vineflower 1.12.0 CLI ordering requirement". "$@"
  # supplies every Additional option here, in the same order recorded in
  # recon.json.
  local vf_cmd=(
    "$N5_JAVA" -jar "$N5_VINEFLOWER" --log-level=error
    --include-runtime="$N5_JDK25_HOME"
    "$@"
    -e="$V2_LIB_CSV"
    "$jar" "$moddir/$out_dir_name"
  )
  { printf 'CMD:'; printf ' %q' "${vf_cmd[@]}"; printf '\n'; } >> "$LOG_DIR/$module.$variant_label.log"

  local t0 t1 primary_time primary_status
  t0="$(date +%s)"
  if timeout "$N5_PRIMARY_TIMEOUT" "${vf_cmd[@]}" >> "$LOG_DIR/$module.$variant_label.log" 2>&1; then
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
  log "$module" "$variant_label primary(vineflower) status=$primary_status time=${primary_time}s"

  local fallback_used="false" fallback_reason="none"
  local excluded_classes_json="[]" isolate_time="0" isolation_status="" timeout_attempt_time=""
  local produced
  produced="$(find "$moddir/$out_dir_name" -name '*.java' | wc -l)"

  # T24: a hung whole-jar run gets ONE isolation attempt before falling back
  # to whole-module CFR — see vf_handle_primary_timeout's doc comment. v2/cons
  # share this variant's own flag set ("$@") + --include-runtime, and the
  # SAME -e=<lib CSV>/--extraclasspath library context the plain run used.
  if [[ "$primary_status" == "timeout" ]]; then
    timeout_attempt_time="$primary_time"
    local -a variant_own_flags=("--include-runtime=$N5_JDK25_HOME" "$@")
    if vf_handle_primary_timeout "$module" "$moddir" "$jar" "$out_dir_name" "$fallback_dir_name" \
        "${out_dir_name}-noinner" "$LOG_DIR/$module.$variant_label.log" "-e=$V2_LIB_CSV" "$V2_LIB_COLON" \
        "${variant_own_flags[@]}"; then
      primary_status="$VFH_PRIMARY_STATUS"
      primary_time="$VFH_PRIMARY_TIME"
      fallback_used="$VFH_FALLBACK_USED"
      fallback_reason="$VFH_FALLBACK_REASON"
    fi
    isolation_status="$VFH_ISOLATION_STATUS"
    isolate_time="$VFH_ISOLATE_TIME"
    excluded_classes_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${VFH_EXCLUDED_CLASSES[@]}")"
    produced="$(find "$moddir/$out_dir_name" -name '*.java' | wc -l)"
  fi

  if [[ "$primary_status" == "ok" || "$primary_status" == "ok_with_excluded" ]] \
      && [[ "$produced" -gt 0 || "$class_count" -eq 0 ]]; then
    local marker_files
    marker_files="$(scan_marker_files "$moddir/$out_dir_name")"
    if [[ -n "$marker_files" ]]; then
      fallback_used="true"
      [[ "$fallback_reason" == "none" ]] && fallback_reason="per_class_decompiler_marker"
      mkdir -p "$moddir/$fallback_dir_name"
      local n=0
      while IFS= read -r javafile; do
        [[ -z "$javafile" ]] && continue
        local rel="${javafile#"$moddir"/"$out_dir_name"/}"
        local classrel="${rel%.java}.class"
        local classfile="$moddir/extracted/$classrel"
        if [[ -f "$classfile" ]]; then
          local cfrc_cmd=("$N5_JAVA" -jar "$N5_CFR" "$classfile" --outputdir "$moddir/$fallback_dir_name" --silent true --extraclasspath "$V2_LIB_COLON")
          { printf 'CMD:'; printf ' %q' "${cfrc_cmd[@]}"; printf '\n'; } >> "$LOG_DIR/$module.$variant_label.log"
          "${cfrc_cmd[@]}" >> "$LOG_DIR/$module.$variant_label.log" 2>&1 || true
          n=$((n+1))
        fi
      done <<< "$marker_files"
      log "$module" "$variant_label fallback(cfr) per-class reran $n classes flagged by primary"
    fi
  else
    # whole-jar fallback to CFR — primary either failed outright, or hung and
    # T24's isolation+excluded-rerun did not resolve it either.
    fallback_used="true"
    fallback_reason="primary_${primary_status}_whole_module"
    log "$module" "$variant_label fallback(cfr) whole-module reason=$fallback_reason"
    mkdir -p "$moddir/$fallback_dir_name"
    local cfr_cmd=("$N5_JAVA" -jar "$N5_CFR" "$jar" --outputdir "$moddir/$fallback_dir_name" --silent true --extraclasspath "$V2_LIB_COLON")
    { printf 'CMD:'; printf ' %q' "${cfr_cmd[@]}"; printf '\n'; } >> "$LOG_DIR/$module.$variant_label.log"
    "${cfr_cmd[@]}" >> "$LOG_DIR/$module.$variant_label.log" 2>&1 || log "$module" "$variant_label fallback(cfr) also failed"
  fi

  # T19 fix, requirement 4: a module where BOTH decompilers produced nothing
  # (jar has classes, but neither output dir has a .java) is NOT a success.
  local total_produced status="ok"
  total_produced=$(( \
    $(find "$moddir/$out_dir_name" -name '*.java' 2>/dev/null | wc -l) \
    + $(find "$moddir/$fallback_dir_name" -name '*.java' 2>/dev/null | wc -l) \
  ))
  if [[ "$class_count" -gt 0 && "$total_produced" -eq 0 ]]; then
    status="failed"
  fi

  # Multi-Release JAR (JEP 238) version overrides — see vf_handle_mrjar_versions's doc
  # comment. Runs unconditionally, independent of primary_status/status above, with the
  # SAME library context and variant flags ("$@", plus --include-runtime, same
  # convention the T24 timeout handling above already uses for variant_own_flags) the
  # real run used.
  local -a variant_mrjar_own_flags=("--include-runtime=$N5_JDK25_HOME" "$@")
  vf_handle_mrjar_versions "$module" "$moddir" "$out_dir_name" "$fallback_dir_name" \
    "$LOG_DIR/$module.$variant_label.log" "-e=$V2_LIB_CSV" "$V2_LIB_COLON" "${variant_mrjar_own_flags[@]}"
  local mrjar_unrepresented_json
  mrjar_unrepresented_json="$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${VFM_UNREPRESENTED[@]}")"

  write_recon_variant "$recon_key" "$module" "$moddir" "$jar" "$sha" "$primary_status" "$primary_time" \
    "$fallback_used" "$fallback_reason" "$status" "$idempotency_key" "$out_dir_name" \
    "$excluded_classes_json" "$isolate_time" "$isolation_status" "$timeout_attempt_time" \
    "$VFM_VERSIONS_JSON" "$mrjar_unrepresented_json"

  if [[ "$status" == "failed" ]]; then
    log "$module" "$variant_label FAILED: both Vineflower and CFR produced zero output for $class_count classes"
    return 1
  fi
  log "$module" "$variant_label done"
}

decompile_module_v2() {
  local jar="$1" force="${2:-false}"
  local moddir="${3:-$N5_OUT_DIR/$(basename "$jar" .jar)}"
  build_v2_flags
  decompile_module_variant "v2" "vineflower2" "fallback2" "v2" "$jar" "$force" "$moddir" "${V2_FLAG_ARGS[@]}"
}

# --variant cons — B118 §118.1's conservative + line-mapped Vineflower view:
# resugaring off (no instanceof-pattern/switch-expression/ternary-in-if/
# prettify-ifs/inline-simple-lambdas rendering), ORIGINAL source line numbers
# mapped onto the output (bytecode-source-mapping +
# __dump_original_lines__). Reuses v2's entire library-context machinery
# (immutable libcache, --add-external, --include-runtime, idempotency,
# failure semantics) unchanged — only the flag set, the output directories
# (vineflower-cons/ + fallback-cons/), and the recon.json sub-key ("cons")
# differ. See CONS_FLAG_NAMES/CONS_FLAG_VALUES/CONS_HIDDEN_FLAG above.
decompile_module_cons() {
  local jar="$1" force="${2:-false}"
  local moddir="${3:-$N5_OUT_DIR/$(basename "$jar" .jar)}"
  build_cons_flags
  decompile_module_variant "cons" "vineflower-cons" "fallback-cons" "cons" "$jar" "$force" "$moddir" "${CONS_FLAG_ARGS[@]}"
}

# Shared by run_v2_all_modules/run_cons_all_modules (T19 fix: --all always
# prepares the libcache first, serially, exactly once, before decompiling any
# module — this is what makes it safe to then drive per-module work in
# parallel, e.g. external `xargs -P`: every worker reads the SAME
# already-complete, immutable cache instead of racing to build it).
run_variant_all_modules() {
  local decompile_fn="$1" variant_label="$2" force="$3"
  prepare_v2_libcache "$force"
  local excluded=0 failed=0 ok=0 jar module
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    if [[ "$module" == "docSource" ]]; then
      continue
    fi
    if ! is_tridium_module "$jar"; then
      log "$module" "$variant_label EXCLUDED: module.xml vendor=\"$(module_vendor "$jar")\" (not \"Tridium\"), skipping"
      excluded=$((excluded + 1))
      continue
    fi
    if "$decompile_fn" "$jar" "$force"; then
      ok=$((ok + 1))
    else
      failed=$((failed + 1))
    fi
  done < <(find -L "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0)
  log "_full-run" "$variant_label vendor filter: excluded $excluded non-Tridium jar(s) from $N5_MODULES_DIR"
  log "_full-run" "$variant_label done: ok=$ok failed=$failed excluded=$excluded"
  [[ "$failed" -eq 0 ]]
}
run_v2_all_modules() { run_variant_all_modules decompile_module_v2 "v2" "$1"; }
run_cons_all_modules() { run_variant_all_modules decompile_module_cons "cons" "$1"; }

run_variant_binext() {
  local decompile_fn="$1" variant_label="$2" force="$3" only="$4"
  local out_root="$N5_OUT_DIR/_bin-ext"
  mkdir -p "$out_root"
  prepare_v2_libcache "$force"

  if [[ -n "$only" && "$only" != "--all" ]]; then
    only="${only%.jar}"
    local jar
    jar="$(find -L "$N5_BIN_EXT_DIR" -name "$only.jar" -print -quit 2>/dev/null)"
    if [[ -z "$jar" ]]; then
      echo "no such bin/ext jar: $only.jar under $N5_BIN_EXT_DIR" >&2
      return 1
    fi
    local verdict
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_bin-ext.log" || true)"
    if [[ "$verdict" != include* ]]; then
      log "_bin-ext" "$variant_label skipping $only ($verdict)"
      return 0
    fi
    "$decompile_fn" "$jar" "$force" "$out_root/$only"
    return $?
  fi

  local jar module verdict included=0 skipped=0 failed=0
  while IFS= read -r -d '' jar; do
    module="$(basename "$jar" .jar)"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_bin-ext.log" || true)"
    if [[ "$verdict" == include* ]]; then
      log "_bin-ext" "$variant_label including $module ($verdict)"
      if "$decompile_fn" "$jar" "$force" "$out_root/$module"; then
        included=$((included + 1))
      else
        failed=$((failed + 1))
      fi
    else
      log "_bin-ext" "$variant_label skipping $module ($verdict)"
      skipped=$((skipped + 1))
    fi
  done < <(find -L "$N5_BIN_EXT_DIR" -name '*.jar' -print0)
  log "_bin-ext" "$variant_label done: included=$included skipped=$skipped failed=$failed"
  [[ "$failed" -eq 0 ]]
}
run_v2_binext() { run_variant_binext decompile_module_v2 "v2" "$1" "$2"; }
run_cons_binext() { run_variant_binext decompile_module_cons "cons" "$1" "$2"; }

# ---------------------------------------------------------------------------
# --extra-tridium — the 10 out-of-pipeline Tridium jars (B117 §117.4: 9 under
# etc/m2/repository/com/tridium/**, 1 under lib/) and the Tridium-owned nested
# LIB-INF jars (B117 §117.2: devkit's n-templates + slotomatic, 160 classes,
# plus any other LIB-INF jar passing the same rule). Neither is a "module"
# (no module.xml / not reachable from organized/<mod>/extracted/ the normal
# way), so each gets its own decompile_module_v2 + decompile_module_cons pair
# into a purpose-built moddir. The Tridium/non-Tridium split reuses
# n5-classify-binext.py's existing >50%-of-classes-under-com/tridium|niagara|
# javax/baja rule UNCHANGED — this is what makes the 10-jar list mechanical
# (verified this session: exactly the 10 B117 §117.4 names) rather than
# hand-picked.
# ---------------------------------------------------------------------------

# Records language (Kotlin vs Java) on a jar-level (not per-variant) basis:
# fraction of .class entries carrying Lkotlin/Metadata; in their constant
# pool, same rule as B117 §117.4's "constant-pool byte scan". Written directly
# onto recon.json's top level (not under "v2"/"cons" — this is a fact about
# the SOURCE jar, independent of which decompiler variant read it).
# Vineflower 1.12.0 ships a Kotlin plugin (--kt-enable, default true, verified
# via --help this session) — vineflower_kotlin_plugin_used records whether
# that plugin was relevant for this jar.
write_recon_language() {
  local jar="$1" moddir="$2"
  RECON_PATH="$moddir/recon.json" \
  RECON_JAR="$jar" \
  python3 <<'PYEOF'
import json, os, zipfile

path = os.environ["RECON_PATH"]
jar = os.environ["RECON_JAR"]
try:
    with open(path) as fh:
        recon = json.load(fh)
except (OSError, json.JSONDecodeError):
    recon = {}

kotlin = 0
total = 0
with zipfile.ZipFile(jar) as zf:
    for name in zf.namelist():
        if not name.endswith(".class"):
            continue
        total += 1
        try:
            data = zf.read(name)
        except Exception:
            continue
        if b"Lkotlin/Metadata;" in data:
            kotlin += 1

recon["language"] = "kotlin" if kotlin > 0 else "java"
recon["kotlin_classes"] = kotlin
recon["kotlin_total_classes"] = total
recon["kotlin_ratio"] = round(kotlin / total, 4) if total else 0.0
recon["vineflower_kotlin_plugin_used"] = kotlin > 0

with open(path, "w") as fh:
    json.dump(recon, fh, indent=2)
    fh.write("\n")
PYEOF
}

# Decompiles ($jar, both v2 and cons) into $moddir, then records language.
# Returns 1 if either variant failed.
decompile_extra_tridium_jar() {
  local jar="$1" force="$2" moddir="$3"
  local ok=0
  decompile_module_v2 "$jar" "$force" "$moddir" || ok=1
  decompile_module_cons "$jar" "$force" "$moddir" || ok=1
  write_recon_language "$jar" "$moddir"
  return "$ok"
}

# The 9 etc/m2 jars + 1 lib/ jar (B117 §117.4). Classified mechanically with
# n5-classify-binext.py's existing >50% rule — no hand-picked jar list.
run_extra_tridium() {
  local force="$1"
  v2_libcache_ready || prepare_v2_libcache "$force"
  local etc_root="$N5_OUT_DIR/_etc-m2"
  local lib_root="$N5_OUT_DIR/_lib"
  mkdir -p "$etc_root" "$lib_root"

  local -a candidates=()
  local jar
  while IFS= read -r -d '' jar; do
    candidates+=("$jar|etc-m2")
  done < <(find -L "$N5_ETC_M2_DIR" -name '*.jar' -print0 2>/dev/null)
  while IFS= read -r -d '' jar; do
    candidates+=("$jar|lib")
  done < <(find -L "$N5_LIB_DIR" -maxdepth 1 -name '*.jar' -print0 2>/dev/null)

  local entry loc stem out_root verdict included=0 skipped=0 failed=0
  for entry in "${candidates[@]}"; do
    jar="${entry%|*}"
    loc="${entry##*|}"
    stem="$(basename "$jar" .jar)"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_extra-tridium.log" || true)"
    if [[ "$verdict" != include* ]]; then
      log "_extra-tridium" "skipping $stem ($verdict)"
      skipped=$((skipped + 1))
      continue
    fi
    if [[ "$loc" == "etc-m2" ]]; then out_root="$etc_root"; else out_root="$lib_root"; fi
    log "_extra-tridium" "including $stem ($verdict) -> $out_root/$stem"
    if decompile_extra_tridium_jar "$jar" "$force" "$out_root/$stem"; then
      included=$((included + 1))
    else
      failed=$((failed + 1))
    fi
  done
  log "_extra-tridium" "etc-m2+lib done: included=$included skipped=$skipped failed=$failed"
  [[ "$failed" -eq 0 ]]
}

# Tridium-owned nested LIB-INF jars (B117 §117.2), found by scanning every
# ALREADY-EXTRACTED organized/<mod>/extracted/LIB-INF/*.jar (real corpus, not
# the deduplicated-by-sha256 libcache, so per-module identity is preserved for
# the organized/<mod>/lib-inf/<stem>/ destination the task calls for) and
# classifying each with the same >50% rule.
run_extra_tridium_libinf() {
  local force="$1"
  v2_libcache_ready || prepare_v2_libcache "$force"
  local jar mod stem verdict moddir included=0 skipped=0 failed=0
  while IFS= read -r -d '' jar; do
    # $jar = $N5_OUT_DIR/<mod>/extracted/LIB-INF/<stem>.jar: strip 3 path
    # components (LIB-INF/<stem>.jar, extracted, <mod>) to land on <mod> —
    # verified 2026-09-28: an earlier version of this line was one dirname
    # short and returned "extracted" instead of the module name (caught by
    # tools/tests/n5-decompile.bats' run_extra_tridium_libinf test).
    mod="$(basename "$(dirname "$(dirname "$(dirname "$jar")")")")"
    stem="$(basename "$jar" .jar)"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$jar" 2>>"$LOG_DIR/_extra-tridium.log" || true)"
    if [[ "$verdict" != include* ]]; then
      skipped=$((skipped + 1))
      continue
    fi
    moddir="$N5_OUT_DIR/$mod/lib-inf/$stem"
    log "_extra-tridium" "including LIB-INF $mod/$stem ($verdict) -> $moddir"
    if decompile_extra_tridium_jar "$jar" "$force" "$moddir"; then
      included=$((included + 1))
    else
      failed=$((failed + 1))
    fi
  done < <(find -L "$N5_OUT_DIR" -mindepth 4 -maxdepth 4 -path '*/extracted/LIB-INF/*.jar' -print0 2>/dev/null)
  log "_extra-tridium" "LIB-INF done: included=$included skipped=$skipped failed=$failed"
  [[ "$failed" -eq 0 ]]
}

# ---------------------------------------------------------------------------
# --third-party-libinf (T26b, odd/tasks/decompiler-fidelity-audit.md) — see the header comment's
# own "--third-party-libinf" section for the full rationale/behavior; this is the mechanical part.
# ---------------------------------------------------------------------------

# Merges "population": "lib-inf-3p", "jar_sha256" and "found_in" onto
# $1/recon.json's TOP level (like write_recon_language, never touching the
# "v2" sub-object decompile_module_v2 already wrote/skipped). Called
# unconditionally after every decompile_module_v2 call in
# run_third_party_libinf — including a call that hit the idempotency skip
# branch — so found_in always reflects the current scan's occurrences even
# when the decompile itself was skipped as up to date.
write_recon_lib_inf_3p() {
  local moddir="$1" sha="$2" found_in_json="$3"
  RECON_PATH="$moddir/recon.json" \
  RECON_SHA="$sha" \
  RECON_FOUND_IN_JSON="$found_in_json" \
  python3 <<'PYEOF'
import json, os

path = os.environ["RECON_PATH"]
try:
    with open(path) as fh:
        recon = json.load(fh)
except (OSError, json.JSONDecodeError):
    recon = {}

recon["population"] = "lib-inf-3p"
recon["jar_sha256"] = os.environ["RECON_SHA"]
recon["found_in"] = json.loads(os.environ["RECON_FOUND_IN_JSON"])

with open(path, "w") as fh:
    json.dump(recon, fh, indent=2)
    fh.write("\n")
PYEOF
}

# Every non-Tridium (n5-classify-binext.py verdict "skip") nested LIB-INF jar
# found directly in $N5_MODULES_DIR's Tridium-vendor jars (docSource.jar
# excluded) and every $N5_BIN_EXT_DIR jar, decompiled ONCE per distinct
# sha256 with decompile_module_v2 (unchanged — same out_dir_name/
# fallback_dir_name, same immutable libcache, same T24 hang-isolation path)
# into organized/_lib-inf-3p/<jar-stem>-<sha256[:12]>/. A Tridium-owned nested
# LIB-INF jar (verdict "include*") is classified out and never counted —
# --extra-tridium already owns that population.
run_third_party_libinf() {
  local force="$1"
  v2_libcache_ready || prepare_v2_libcache "$force"
  local out_root="$N5_OUT_DIR/_lib-inf-3p"
  mkdir -p "$out_root"

  # Pass 1: scan every source jar's LIB-INF/*.jar entries straight from the
  # zip (never organized/*/extracted/), recording every occurrence and, per
  # distinct sha256, one probe copy (first module/entry seen names the
  # output directory's jar-stem).
  local -a source_jars=()
  local jar modname
  while IFS= read -r -d '' jar; do
    modname="$(basename "$jar" .jar)"
    [[ "$modname" == "docSource" ]] && continue
    is_tridium_module "$jar" || continue
    source_jars+=("$jar")
  done < <(find -L "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' -print0 2>/dev/null)
  if [[ -d "$N5_BIN_EXT_DIR" ]]; then
    while IFS= read -r -d '' jar; do
      source_jars+=("$jar")
    done < <(find -L "$N5_BIN_EXT_DIR" -name '*.jar' -print0 2>/dev/null)
  fi

  local scratch; scratch="$(mktemp -d)"
  mkdir -p "$scratch/probes"
  local occurrences="$scratch/occurrences.tsv"
  : > "$occurrences"
  local -A STEM_BY_SHA=()

  local src tmpdir entry rel stem sha
  for src in "${source_jars[@]}"; do
    modname="$(basename "$src" .jar)"
    tmpdir="$(mktemp -d)"
    # decompile-pipeline review fix (orchestrator, 2026-09-28, R3-002/R4-002):
    # see cache_source_jar_libinf's identical fix above for the full
    # rationale — exit 11 ("no matching files") is the ordinary case, any
    # OTHER nonzero exit means a genuinely corrupt/truncated LIB-INF entry
    # was extracted anyway (with bad bytes) and used to be swallowed
    # identically and silently.
    local unzip_out unzip_rc=0
    unzip_out="$(unzip -o -q "$src" 'LIB-INF/*.jar' -d "$tmpdir" 2>&1)" || unzip_rc=$?
    if [[ "$unzip_rc" -ne 0 && "$unzip_rc" -ne 11 ]]; then
      log "_lib-inf-3p" "WARNING: unzip exited $unzip_rc extracting LIB-INF/*.jar from $modname — a partially/incorrectly extracted entry may be recorded under a misleading sha256; unzip output: $unzip_out"
    fi
    while IFS= read -r -d '' entry; do
      rel="${entry#"$tmpdir"/}"
      stem="$(basename "$entry" .jar)"
      sha="$(sha256_of "$entry")"
      [[ -z "$sha" ]] && continue
      printf '%s\t%s!%s\n' "$sha" "$modname" "$rel" >> "$occurrences"
      if [[ -z "${STEM_BY_SHA[$sha]:-}" ]]; then
        STEM_BY_SHA[$sha]="$stem"
        cp "$entry" "$scratch/probes/$sha.jar"
      fi
    done < <(find "$tmpdir" -name '*.jar' -print0 2>/dev/null)
    rm -rf "$tmpdir"
  done

  # Pass 2: classify + decompile each distinct sha256 once.
  local -a shas=()
  if [[ "${#STEM_BY_SHA[@]}" -gt 0 ]]; then
    mapfile -t shas < <(printf '%s\n' "${!STEM_BY_SHA[@]}" | sort)
  fi

  local distinct=0 decompiled=0 skipped=0 failed=0
  local moddir probe verdict logfile before_lines new_log found_in_json rc
  for sha in "${shas[@]}"; do
    probe="$scratch/probes/$sha.jar"
    verdict="$(python3 "$SCRIPT_DIR/n5-classify-binext.py" "$probe" 2>>"$LOG_DIR/_lib-inf-3p.log" || true)"
    if [[ "$verdict" == include* ]]; then
      log "_lib-inf-3p" "skipping Tridium-owned LIB-INF jar ${STEM_BY_SHA[$sha]} ($sha) — handled by --extra-tridium, not --third-party-libinf ($verdict)"
      continue
    fi
    distinct=$((distinct + 1))
    stem="${STEM_BY_SHA[$sha]}"
    moddir="$out_root/${stem}-${sha:0:12}"
    mkdir -p "$moddir"
    # A stem-named copy (not the raw sha256) so log filenames and recon.json's
    # "module" field read like every other population's.
    cp "$probe" "$scratch/${stem}.jar"

    # $LOG_DIR/$stem.log (log()'s own target — NOT $stem.v2.log, which only
    # ever gets the raw Vineflower/CFR CMD+output, never the "up to date"
    # skip message decompile_module_variant logs via log()).
    logfile="$LOG_DIR/$stem.log"
    before_lines=0
    [[ -f "$logfile" ]] && before_lines="$(wc -l < "$logfile")"

    rc=0
    decompile_module_v2 "$scratch/${stem}.jar" "$force" "$moddir" || rc=$?

    new_log=""
    [[ -f "$logfile" ]] && new_log="$(tail -n +"$((before_lines + 1))" "$logfile")"

    found_in_json="$(awk -F'\t' -v sha="$sha" '$1==sha{print $2}' "$occurrences" \
      | python3 -c 'import json, sys; print(json.dumps([l.rstrip("\n") for l in sys.stdin if l.strip()]))')"
    write_recon_lib_inf_3p "$moddir" "$sha" "$found_in_json"

    if [[ "$rc" -ne 0 ]]; then
      failed=$((failed + 1))
      log "_lib-inf-3p" "FAILED ${stem}-${sha:0:12} ($sha)"
    elif [[ "$new_log" == *"up to date"* ]]; then
      skipped=$((skipped + 1))
    else
      decompiled=$((decompiled + 1))
    fi
    rm -f "$scratch/${stem}.jar"
  done

  rm -rf "$scratch"
  local summary="lib-inf-3p: decompiled=$decompiled skipped-up-to-date=$skipped failed=$failed distinct_jars=$distinct"
  log "_lib-inf-3p" "$summary"
  echo "$summary"
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
      --extra-tridium)
        mode="extra-tridium"
        shift
        ;;
      --third-party-libinf)
        mode="third-party-libinf"
        shift
        ;;
      --force)
        force="true"
        shift
        ;;
      --variant)
        variant="${2:?--variant needs a value (v2 or cons)}"
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

  if [[ "$mode" == "extra-tridium" ]]; then
    local rc1=0 rc2=0
    run_extra_tridium "$force" || rc1=$?
    run_extra_tridium_libinf "$force" || rc2=$?
    [[ "$rc1" -eq 0 && "$rc2" -eq 0 ]]
    exit $?
  fi

  if [[ "$mode" == "third-party-libinf" ]]; then
    run_third_party_libinf "$force"
    exit $?
  fi

  if [[ -n "$variant" ]]; then
    if [[ "$variant" != "v2" && "$variant" != "cons" ]]; then
      echo "unsupported --variant '$variant' (only 'v2' and 'cons' are implemented)" >&2
      exit 1
    fi
    local decompile_fn="decompile_module_v2"
    [[ "$variant" == "cons" ]] && decompile_fn="decompile_module_cons"
    if [[ "$mode" == "docsource" ]]; then
      echo "--variant $variant does not apply to --docsource (docSource.jar is original sources, not decompiled)" >&2
      exit 1
    fi
    if [[ "$mode" == "bin-ext" ]]; then
      if [[ "$variant" == "cons" ]]; then run_cons_binext "$force" "$only"; else run_v2_binext "$force" "$only"; fi
      exit $?
    fi
    if [[ -z "$only" ]]; then
      echo "--variant $variant needs an explicit <module> or --all: tools/n5-decompile.sh --variant $variant [<module>|--all]" >&2
      exit 1
    fi
    if [[ "$only" == "--all" ]]; then
      if [[ "$variant" == "cons" ]]; then run_cons_all_modules "$force"; else run_v2_all_modules "$force"; fi
      exit $?
    fi
    only="${only%.jar}"
    local v2_jar="$N5_MODULES_DIR/$only.jar"
    if [[ ! -f "$v2_jar" ]]; then
      echo "no such module jar: $v2_jar" >&2
      exit 1
    fi
    if ! is_tridium_module "$v2_jar"; then
      log "$only" "$variant EXCLUDED: module.xml vendor=\"$(module_vendor "$v2_jar")\" (not \"Tridium\") — not a real N5-shipped module, skipping"
      exit 0
    fi
    "$decompile_fn" "$v2_jar" "$force"
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
