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
- [ ] F7 Classpath completion for missing-lib no-compiles (javafx, bouncycastle): locate the exact jars N5 links at runtime.
- [ ] F8 Mechanical doPrivileged disambiguation patch tree (vineflower2p), verified by recompile + canonical grade.
- [ ] F3 Full run, vineflower2 then vineflower, all modules; failures recorded as module_error, never dropped.
      Route: inline background run.
- [ ] F4 Report: regenerate docs/decompile-fidelity-report.md + `--compare vineflower,vineflower2`; verify numbers
      independently (recount grade_counts from the JSON files). Route: inline.
- [ ] F5 Update parent ODD T21, commit, RDD, PR, merge.
- [x] F6 Sound canonical comparison as SEPARATE labelled grades (`roundtrip-canonical` tier 1, `roundtrip-canonical-t2`
      tier 2 = boolean 0/1 JLS invariant): port the taxonomy prototype (organized/_evidence/taxonomy/canon.py) into
      tools/n5_canon.py with per-rule switches + tests (hand javap fixtures AND real javac-25 pairs), ordered exception
      coverage (catch priority, never sorted), per-class `canonical_rules`, `--regrade-nonclean` writing
      fidelity.<tree>.canon.json, fail-closed mutation soundness suite, blind-spot fixes (iinc_w/wide slots,
      mismatched_methods minus allowlist-only). TDD on (user CLAUDE.md, runner `cd tools/tests && python3 -m unittest
      test_n5_fidelity test_n5_canon` + `make test`). Route: delegated writer (writer trigger: 2+ non-trivial files).
      Commits: ca164f8, aefb8b0, 29ed173, 1d0bc5c, 8d6f513, 9a70f44, e2ae091, 6c4f15f, cf8b487 (evidence below).

## Follow-ups
- F6 schema bump: SCHEMA_VERSION 2 makes every schema-1 fidelity.<tree>.json a stale cache for a plain re-run.
  Cheapest path after F3: `--regrade-nonclean --all` per tree (non-clean classes only), then decide whether the
  schema-1 exact grades need a re-check under the tightened normalizer (0 of 359 flipped on 5 modules, see F6).
- Pre-existing normalizer gap (not fixed in F6): strip_cp_indices also drops `#<digits>` INSIDE a string constant's
  symbolic comment (`ldc // String a#1` == `// String a#2`); needs a CP-index strip that stops at the `//` comment.
- `boolmat` on an `instanceof` producer is sound at tier 1 (JVMS: instanceof pushes 0/1) but is labelled tier 2
  with the Z-typed producers; splitting it would move BOffnormalAlgorithm-like classes to roundtrip-canonical.
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
- F6 (2026-09-29, worktree t21-compile-server, TDD on): RED then GREEN per step --
  exact-normalizer soundness 9 tests RED (5 fail + 4 error; real javac `a - b` vs `b - a` graded equal = false exact),
  n5_canon baseline 14 RED (module absent), control-flow rules 10 RED, data-flow rules 11 RED (the `cov` and `cmp1`
  tests were written after their code landed with the CFG commit and passed on first run), canonical grades 8 RED,
  --regrade-nonclean 6 RED, invokedynamic bootstrap args 2 RED (real javac `"a" + x` vs `"b" + x` graded equal =
  false exact), --force 1 RED, ladder preference 4 RED. GREEN: `make test` 558 tests OK (skipped=4).
- F6 soundness: mutation suite kill rate 929/929 on 49 shipped methods (7 modules) + 45/45 on the recompiled side of 9
  javac pairs, 0 unsupported; sabotaged canonicalizers (polarity-blind, order-blind, catch-type-blind) leave survivors
  (suite can fail). Scratch run on the recompiled side of 40 real canonical classes: 2290/2290 mutants killed (139 methods).
- F6 real verification: `--regrade-nonclean --tool-server` on haystack/box/batchJob/bql/alarm (vineflower2):
  non-clean 162 -> 34 (canonical 125, canonical-t2 3); exact/equivalent unchanged (359/1). A forced full re-grade of
  all 555 classes of those modules with the new code in a scratch organized dir gives identical per-class grades
  (0 disagreements) and 0 exact->non-exact flips: the tightened normalizer found no false exact there.
  Prototype (t3_normalizer_class_results.tsv, vf2 rung): 119 resolved / 28 residual on both sides, tier split equal,
  0 disagreements. Bug found by verification: the ladder stopped at a canonical first rung and cost 57 classes their
  CFR/Procyon roundtrip-exact -> fixed cf8b487 (ladder stops only at exact/equivalent).
- F6 hand checks (shipped vs recompiled, n5_canon form): BRefTag.getParentOfType `goto` to a shared `areturn` (tail);
  BServerSession.<clinit> `aconst_null; checkcast BFacets` overload pick (r1); BFoxBqlResolver.resolve locals shifted
  by one slot (web); BHisStatusTag.getTag swapped if/else arms (baseline polarity); BBqlInterval `aload_0; aload_0` vs
  `aload_0; dup`, `istore; iload; ireturn` temp (peep, dse) and BOffnormalAlgorithm.isParentLegal
  `instanceof ? true : false` (boolmat, tier 2).
- Next: F3 continues on the schema-1 code in the main checkout; after merge run `--regrade-nonclean` for both trees.
- F6 RDD: 9 per-commit reviews approved + acknowledged (review-803946ab6daf4636 … review-112d902cf672b79e). Orchestrator reproduced both false-exact cases with the OLD normalizer (b57cabf): `a-b` vs `b-a` and `"a"+x` vs `"b"+x` compared equal. All schema-1 exact grades (incl. the 192-class sample and runs 1-2) are therefore not trustworthy.
- F3 restarted 2026-09-29T08:02Z on schema 2 (run 2 schema-1 stopped at ~200 modules; log kept as t21-run2-schema1.log).
