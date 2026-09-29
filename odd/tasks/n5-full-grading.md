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
- [x] F7 Classpath completion for missing-lib no-compiles (javafx, bouncycastle): locate the exact jars N5 links at runtime.
      Route: delegated writer (worktree t21-f7f8, TDD on). Commit 4eeaafb. Evidence under "F7 evidence" below.
- [x] F8 Mechanical doPrivileged disambiguation patch tree (vineflower2p), verified by recompile + canonical grade.
      Route: delegated writer (worktree t21-f7f8, TDD on). Commits 7d9cb2d, 9ba04f9, 11136c8. Evidence under "F8 evidence" below.
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

## F7 evidence (2026-09-29, worktree t21-f7f8)
- Cause: `build_classpath` globbed only `bin/ext/*.jar` (non-recursive) and the grader JDK has no JavaFX. nre.dll's
  launcher strings (`strings -a bin/nre.dll`, initPaths()) are `%s\bin\ext`, `%s\bin\ext\%s` (bcfips|bcstd, chosen by
  initFips()), `%s\bin\ext\jxbrowser`, `%s\bin\ext\system`, separate `%s\bin\ext\securityBridge`; the JVM is
  `<niagaraHome>\jre` whose `release` MODULES list javafx.base/controls/fxml/graphics/media/swing/web + jfx.incubator.*.
- Search method (package content, not names): zip index of every .jar/.zip (recursively into nested jars) under the
  jar mirror, `/mnt/c/Program Files/Niagara/5.0.0.28` and the config home; plus `jimage list jre/lib/modules`.
  | missing package (vf2 no-compile) | N5 artifact (mirror path, sha256 from bin-ext.sha256, re-verified `sha256sum -c` rc=0) |
  |---|---|
  | org.bouncycastle.{asn1,cert,openssl,pkcs,tls,util} | bin-ext/bcstd/bcprov-jdk18on-1.85.2.jar 5b16c2ba…, bcpkix-jdk18on-1.85.jar e3f24cfc…, bctls-jdk18on-1.85.jar d5174c51…, bcutil-jdk18on-1.85.jar c05bdcc1… (FIPS twin bin-ext/bcfips/*, `--bc-variant bcfips`) |
  | com.teamdev.jxbrowser.* | bin-ext/jxbrowser/jxbrowser-9.5.0.jar e20a7f71… (+ -javafx 9267055b…, -swing 3ed7d5ff…, -swt 64f8e52f…, -win64 43ee02e4…) |
  | com.orientechnologies.* | bin-ext/system/orientdb-core-3.2.55.jar 8caa1c60…, -client 11fe880c…, -server f3295116…, -tools 8a87fd85… |
  | javafx.* | N5 JRE `jre/lib/modules` (JAVA_VERSION 25.0.4) sha256 2eaeb1d398f53c5d3c14e4b36f3dd224c611cf81e608f927ba04bb751c98281e, extracted with `jimage extract --include regex:/(javafx|jfx)\..*` (5,863 classes) |
  Nothing needed is absent from N5, so no --extra-classpath / foreign jar was introduced.
- TDD: tools/tests/test_n5_fidelity_classpath.py RED 8/8 (TypeError: unexpected keyword 'jre_dir'), GREEN 8/8;
  `test_n5_fidelity` + classpath 153 OK.
- Real check: the 74 vf2 no-compile classes whose first error or source references those packages, graded with the
  new classpath (tool server, 4 class jobs, read-only on organized/): 0 remain missing-lib; grade 18 roundtrip-exact +
  24 roundtrip-canonical + 32 bytecode-only; the 27 vf2 rungs still no-compile all fail on `doPrivileged is ambiguous` (F8).

## F8 evidence (2026-09-29, worktree t21-f7f8)
- Tool: tools/n5-patch-doprivileged.py + tools/n5-patch-doprivileged/DoPrivilegedSites.java (javac Tree API, parse
  only). Cast = shipped `invokestatic SecurityUtil.doPrivileged:(L<iface>;)` + LambdaMetafactory instantiated return
  (T) + same-class lambda `throws` (E); source/bytecode sites matched in order per method, lambda pools only with
  uniform evidence; javac feedback (<= 4 compiles + 1 verification) only for thrown types and type variables.
  Grading: `n5-fidelity.py --regrade-nonclean --patch-tree vineflower2p` -> fidelity.<tree>.patched.json, rung label
  `vineflower2p`, `patched: true` + `patch: {tree, manifest, patched_sha256}` only when that rung is the class grade.
- TDD: test_n5_patch_doprivileged RED 10 errors (module absent) -> GREEN 13; test_n5_fidelity_patch_rung RED 8/8 ->
  GREEN 8; regressions found by the real run, each RED first: javap offsets >= 100 dropped (1 FAIL), no-arg
  constructor vs overloads (1 FAIL), thrown-type/type-variable feedback (2 FAIL). The CLI guard test was written with
  its code. `make test` 590 OK (skipped=4) at 9ba04f9 and again at 948e141 (after the feedback fix).
- Real run (all 259 organized dirs, vineflower2 tree, classpath of F7): 522 files contain `doPrivileged(`; 504 classes
  patched, 1,469 sites (PrivilegedAction 894, PrivilegedExceptionAction 489, SingleException 83, DoubleException 3),
  1,452 sites on the first (pure-evidence) cast, 17 needed javac feedback; 467 patched classes compile, 37 still fail on
  other decompiler defects (unreachable statement, variable scoping, generics). Refused 10 sites in 5 classes:
  lambda-pool-mixed-evidence 4 (BForgeCertificateAuthenticator), instance-initializer 3 (AwtSeEnv, BSnmpDevice,
  NiagaraLocalPlatform), overload-unresolved 2 (LocalInstallableRegistry), count-mismatch 1 (BSnmpDevice); 1 extra
  ambiguous site is `AccessController.doPrivileged` (OrdTargetFilter), out of scope.
- Soundness: all 467 compiling patched classes, recompiled: per class file and method, the sequence of
  (doPrivileged descriptor interface, instantiated return) equals the shipped bytecode in 467/467.
- Grades (scratch organized dir of symlinks + SNAPSHOT copies of fidelity.vineflower2.json, 91 modules; web/workbench
  have no fidelity file yet and were graded class by class with the same rung): baseline compile of the unpatched
  source: 476 of the 504 fail ONLY on `doPrivileged is ambiguous` (full-corpus counterpart of the taxonomy's 88).
  Of those 476: 88 roundtrip-exact, 291 roundtrip-canonical, 3 roundtrip-canonical-t2 (all via vineflower2p),
  91 still bytecode-only (vineflower2p rung 82 compiles-mismatch, 9 no-compile), 3 already clean in the snapshot.
  The 28 classes with other errors too stay bytecode-only.
- Evidence copies: organized/_evidence/t21-f7f8/ (gitignored): f7.list, f7-results.json, baseline-errs.json,
  f8-final-grades.json, descr-diffs.json, patch/regrade logs, scratch-patched/*.fidelity.vineflower2.patched.json, scripts.
- Next: after F3, run the patcher over the final tree and `--regrade-nonclean --patch-tree vineflower2p --all` for the
  published numbers; the vineflower2p rung counts as a separate, labelled source in the report.
