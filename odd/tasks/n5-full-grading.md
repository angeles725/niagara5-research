# N5 full-corpus decompile fidelity grading (T21 of decompiler-fidelity-audit)

## Objective
Grade every top-level class of the N5 5.0.0.28 corpus (14,548 classes, 246 modules with extracted/) on both
decompiled trees (vineflower, vineflower2) with tools/n5-fidelity.py, and publish the measured round-trip rates.
Closes B116-G1 and T21 of odd/tasks/decompiler-fidelity-audit.md.

## Problem / why
Only 192 classes were graded (v1 124 exact, v2 125, 0 worse). The "vineflower2 is the recommended tree" decision
and every fidelity number rest on a 1.3% sample. The user asked for the most faithful decompile possible; that
needs the full measurement, and then the per-class best tree follows from data, not from a sample.

## Scope (authorized)
tools/n5-fidelity.py + tests (performance only, grading semantics unchanged); organized/<mod>/fidelity.<tree>.json
(generated); docs/decompile-fidelity-report.md; this document; the parent ODD doc T21 line.

## Constraints
- Strict TDD (user CLAUDE.md) for tools/ changes; runner `cd tools/tests && python3 -m unittest test_n5_fidelity` (pytest not installed) and full `make test`.
- RDD granted by the user for this session.
- Classpath = sha256-verified local jar mirror /home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28
  (re-verified 2026-09-28: modules.sha256 and bin-ext.sha256 rc=0).
- Delivery strategy: ask-on-risk answered by the user's standing authorization → feature branch + PR.

## Tasks
- [x] F1 Forecast (inline): haystack 36 classes serial 282 s = 7.8 s/class (ladder CFR+Procyon runs for every non-clean class);
      14,548 classes ≈ 31.5 h serial per tree → ≈ 5 h per tree at 9 concurrent compiles (--jobs 3 --class-jobs 3).
      v1/v2 source identical for 5,955 of 14,550 .java (41%).
- [x] F2 (8350885, RDD review-f08d8c2ebebe6b46 approved+acknowledged) Intra-module class-level parallelism (`--class-jobs N`): per-class grading is independent (own temp dirs);
      results must be identical to the serial path and ordered deterministically. Route: delegated writer (TDD).
- [x] F2b Opt-in persistent tool server (`--tool-server`, default off): tools/n5-toolserver/ToolServer.java runs javac/javap in-process via ToolProvider
      (one JVM per worker thread, length-prefixed binary protocol, per-request timeout = kill+restart, fallback to subprocess on any server failure).
      Grades identical to the subprocess path; SCHEMA_VERSION and cache key untouched. Route: delegated writer (TDD). Commits: 5efbc27, 156c533, 50ef661.
- [ ] F3 Full run, vineflower2 then vineflower, all modules; failures recorded as module_error, never dropped.
      Route: inline background run.
- [ ] F4 Report: regenerate docs/decompile-fidelity-report.md + `--compare vineflower,vineflower2`; verify numbers
      independently (recount grade_counts from the JSON files). Route: inline.
- [ ] F5 Update parent ODD T21, commit, RDD, PR, merge.

## Follow-ups
- first_error embeds the random javac temp dir path (/tmp/tmpXXXX/...), so fidelity JSON is not byte-reproducible
  between runs (pre-existing; serial runs differ too). Normalize to the package-relative path.

## Progress / evidence
- 2026-09-28 branch feat/n5-t21-full-grading off main b57cabf.
- F2 real check: haystack --class-jobs 1 vs 8 → identical grades and key order for all 36 classes; only first_error temp paths differ; 282 s → 85 s.
- F2b real check (class-jobs 4, machine saturated by the F3 run): wall --tool-server vs subprocess: haystack 116 s vs 324 s, abstractMqttDriver 145 s vs 483 s,
  alarmOrion 128 s vs 489 s (~2.8-3.8x); all 129 classes identical (grade/best_decompiler/attempted/mismatched_methods/consensus/docsource_roundtrip) vs the F3 JSON; only first_error temp paths differ.
  Bug found and fixed by verification: unbuffered pipe reads truncated >64 KB javap replies (regression test added).
- F3 launched: scratchpad run-t21.sh (vineflower2 then vineflower), log t21.log.
- F2b RDD: 5efbc27 under budget (medium); 156c533 review-4db7520f8f538813 raised R4-jvm-leak-per-module-pool (CRITICAL, real: per-module class pools left one JVM per finished thread) → fixed abf1b56 (TDD: RED 2 tests, GREEN 114/114), targeted validation passed, approved + acknowledged; 50ef661 review-60ae58ae9c55861b approved. make test 481 OK before the fix.
- F3 restarted 2026-09-29T05:48Z with --jobs 3 --class-jobs 4 --tool-server (run 1 stopped after 39 modules; finished modules skipped as up to date).
