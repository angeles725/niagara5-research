# N5 decompile fidelity completion (after T21)

## Objective
Close every fidelity gap left open by T21 (odd/tasks/n5-full-grading.md) so the N5 5.0.0.28 decompile is measured
and proven across ALL class files, not only top-level Tridium classes. Only after this is done does the toolchain
move to Niagara N4 (user decision 2026-09-29).

## Problem / why
T21 proved 95.79% of 14,307 top-level classes. Still unmeasured or unproven:
- 6,186 nested/inner/anonymous class files (`Outer$Inner.class`) are compiled but never compared.
- Third-party LIB-INF jars without proven upstream source, and bin/ext jars, are not graded.
- 602 top-level classes are bytecode-only (no decompile reproduces the shipped bytecode).
- 3,375 classes are proven only up to canonical normalization, not byte-exact.

## Scope (authorized, user 2026-09-29: "mejorarlo todo lo que nos falta ... fiel y exacto")
tools/ (n5-fidelity.py, n5_canon.py, n5-splice-methods.py, n5-patch-doprivileged.py, new helpers) + tests;
generated organized/<mod>/fidelity.*.json; docs/decompile-fidelity-report.md; this document.
Decompiled/reconstructed vendor source stays under gitignored paths (organized/<mod>/vineflower*/, organized/_evidence/).

## Constraints
- User authorization 2026-09-29 (research-sdd launch): ODD + RDD (granted, accept Gentle-AI review consent) + commit + push + PR + pr view +
  issues + merge without asking; answer own questions by recommendation; run uninterrupted. After this feature: frontier
  research chain (heavy + auto + chained) on niagara5-research.
- TDD: strict, source = user CLAUDE.md ("Strict TDD Mode: enabled"); runner `cd tools/tests && python3 -m unittest <module>`
  and full `make test` (pytest not installed).
- Classpath = sha256-verified jar mirror /home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28.
- Grade with `--tool-server --class-jobs 4 --jobs 3`. Never `pkill -f` a pattern present in your own command line.
- RDD: on (global). Commits for review stay small (< ~250 lines per slice; lens budget).
- Delivery: feature branch feat/n5-fidelity-completion + PR (standing authorization from the T21 session).
- Grading semantics: a new grade never weakens an existing one; schema bumps retract older grades explicitly.

## Tasks
Task IDs are C<n> (completion). "N4"/"N5" always mean Niagara 4 / Niagara 5, never a task.
- [x] C0 Bookkeeping: T21 F5 is done (parent T21 line checked at odd/tasks/decompiler-fidelity-audit.md:242, PR #23/#24 merged).
- [x] C1 (a4002c0; 19 new tests RED->GREEN, make test 658 OK; smoke backup+axvelocity) Grade nested/inner/anonymous class files. Each `Outer$X.class` produced by recompiling the outer source is
      compared against the shipped `Outer$X.class` with the same normalizer/canonical ladder; a top-level class is
      "fully proven" only when it and all its nested files are proven. Missing/extra synthetic nested files are
      reported, never dropped. Forecast: 6,186 nested files; they are already produced by the existing compile step,
      so the added cost is javap+compare only. Route: delegated writer (TDD; writer trigger: tool + tests).
- [ ] C1c Incremental regrade cache (user 2026-09-30: "agregala y hazla antes de C1b"). Per-class cache key = sha256 of
  the decompiled source file(s) + shipped class bytes + nested bytes + toolchain identity (javac/javap version, grader
  schema/NESTED_SCHEMA_VERSION, rung, --release/legacy flags, classpath digest); a hit reuses the stored record, a miss
  regrades; `--force` still bypasses; cache stats (hits/misses) printed per module + periodic progress line (C2d process
  note). Strict TDD (hit, miss on each key component, force bypass, schema bump invalidates). Route: delegated writer
  after C4 + C2a-G1 merge (both touch tools/n5-fidelity.py). Then run C1b ALONE (no concurrent heavy agents,
  jobs = cores): the machine showed 25 JVMs on 16 threads / 31 GB during C2d+C4 (load ~30). Optional follow-up
  C1c-G1: persistent CFR/Procyon fallback server (per-class JVM spawn dominated jxbrowser's 8 h).
  Scope extension (user 2026-09-30: "no volver a empezar de cero"): the per-class cache file doubles as a CHECKPOINT —
  every graded class is appended durably (atomic write / fsync per batch) as soon as it is graded, so an interrupted
  run (crash, reboot, compaction teardown) resumes at the next ungraded class instead of restarting the module.
  Today: decompile is sha256-cached per jar (n5-decompile.sh), regrade-canon is checkpointed every 10 classes, but the
  main grade is all-or-nothing PER MODULE (is_module_up_to_date: jar sha256 + schema) with no per-class resume.
  Extra TDD case: kill mid-module -> rerun regrades only the missing classes and yields the same JSON as an
  uninterrupted run.
  Research 2026-09-30 (read-only agent; parent re-checked l.2237-2265, l.1577-1587, l.1815-1830, l.1066), folded into C1c:
  (a) key ALSO covers decompiler jar sha256s, rung list + ORDER, patch label, nested bytes, classpath digest — the module
  check today covers only schema, jar sha, tree, limits, so a re-decompile or toolchain change is skipped as up to date;
  (b) cache the shipped-class javap parse by sha256, reused across rungs/nested/docsource (up to 6x `javap -v` today);
  (c) NEVER cache or checkpoint a `timeout` record (wall-clock, load-dependent) and print timeouts per module;
  (d) per-stage time accumulators (javac / javap / parse / spawn) on the progress line — no stage timings exist yet;
  (e) hard assert jobs x class-jobs <= cores (each tool server -Xmx1g); (f) schedule modules longest-first from the
  previous run's durations (no lone long tail). Each with an equivalence test (cache on/off -> identical JSON).
  C1c-G1 refined: CFR via CfrDriver library API in one JVM per worker, engines serial inside it (CFR issue #250
  StackOverflow in parallel), recycle by request count; differential test on 200 sampled classes vs `java -jar` output
  (byte-identical .java). jxbrowser measured: CFR tried ~1,130 / rescued 232; Procyon tried ~906 / rescued 11.
  Run the primary rung for all classes first, fallbacks as a warm second pass.
  New optional C1c-G2: in-server javac reusing one StandardJavaFileManager per classpath digest + AppCDS (JEP 350) +
  TieredStopAtLevel=1, and batched primary-rung compiles with per-class fallback on any error — benchmark on an IDLE
  machine first; differential test on 100 classes incl. no-compile (same .class bytes and first_error); resolve output
  .class by package path, not rglob simple name, before batching.
  Design rule (user 2026-09-30: "que nos sirva para cualquier cosa"): build the C1c cache/checkpoint/scheduler/timers as a
  DOMAIN-FREE module (no Niagara/javac names inside; the grader plugs in key + work functions), plus a strategy ranker that
  orders rungs/hypotheses by historical success (ordering only, never skipping; the verifier stays the judge). Promote to
  the research-sdd kit after its equivalence tests pass (kit issue #1262, throughput retro row 5).
  C3e input: Vineflower option-sweep rung on the bytecode-only residual (additive, option set in the cache key).
- [ ] C1d (after C1c, user 2026-09-30) Grade identical classes once: dedup by the C1c per-class key (shipped bytes +
  decompiled source + classpath digest), e.g. jxbrowser javafx/swing/swt variants; every duplicate gets the canonical
  record copied with a `dedup_of` pointer. Test: deduped run vs full run -> identical grades per class.
- [ ] C3h (after C1c) Residual triage table: every non-exact class with the rule/mismatch family that failed, ranked by
  family size, so the largest families (e.g. C3d-G2 LVT) are attacked first. Generated from the JSON, no regrade.
- [ ] C3f (after C1c) Vineflower option-sweep rung on the bytecode-only residual (options from vineflower.org/usage:
  pattern-matching, try-loop-fix, ensure-synchronized-monitors, use-lvt-names, decompile-generics...). Additive rung
  (best-of cannot regress); option set in the cache key.
- [ ] C3g (after C1c; method for C3e) AI-proposed reconstruction of the residual (352 Tridium + 44 bin/ext): the model
  proposes source edits, the compiler + bytecode comparison is the only judge; accepted only when the grade improves,
  recorded as its own rung with the proposal kept as evidence.
- [x] P0 Leak fix (process study 2026-09-30): 3 decompiled Tridium classes (BDevice, BQudtUnitTag, BSimpleSigningProfile,
  ~878 lines) were tracked in evidence/b118 since b8eebcd while the repo is PUBLIC. Untracked + gitignored + block 118
  note, PR #25 (merged; post-merge review review-0daa96c7e791466b approved — the review ran AFTER the merge, a process
  slip). Local copies in organized/_evidence/b118/. Still in git HISTORY: user decided 2026-09-30 NOT to purge ("lo dejamos así"); no history rewrite.
- [ ] P1 (before C1c) Leak guard: tools/githooks/pre-commit + CI reject staged *.class/*.jar, decompiled-vendor patterns
  (*.cons-linemapped.java, packages com.tridium/javax.baja/niagara.* outside a reviewed allowlist) and files over a size
  limit; fixture tests (blocked vendor file, allowed own probe).
- [ ] P2 (before C1c) Test fast lane: `make test-changed` (tools/X.py -> tools/tests/test_X*.py map + a test that every
  tool has a mapped test) and `--durations` profiling; full serial suite stays the closing gate. Measured: 755 tests in
  1,298.8 s serial (maketest.log); now 841 + 99 bats.
- [ ] P3 (before C1c) Review tooling: rdd.py abspath fix; `slice-plan` (cut points <= 250 changed lines at commit
  boundaries using real parents); `--all-due` walking from a tracked boundary file odd/review-boundary.txt. Evidence: a
  3,378-line slice refused (rdd-c2d.log); two relative-path failures today. Operating rule: review slice N while the next
  writer runs (reviews take ~40-90 s per slice and are read-only on immutable commits); never merge before review.
- [ ] P4 (with C1c) Generated facts: status.py recounts the headline numbers from the fidelity JSON into a marked doc
  block (test: block == script output); `make test-record` writes Ran/OK/seconds/HEAD/dirty to evidence; runs.tsv
  start/end/load/cores/JVMs for every heavy run; env.json toolchain identity (reused as C1c key part); `odd-close` script
  ticks a task from git + review output (17 of 46 commits since 09-29 were bookkeeping docs).
- [ ] P5 (before C1c) Defect-class lint: ban first-`$` splits of class names (recurred in 4 files; fix commits d1623a7,
  4d6369e) + property test over `$`-prefixed names; fixes C2d-G5 survivors n5-extract-census.py:127, n5-recon-helper.py:72.
- [ ] P6 Machine-readable handoff state.json (in-flight workers, worktrees, branch, review boundary, next task) derived
  from git/worktree state; handoff prose generated from it.
- [ ] P7 No-garbage rule (user 2026-09-30: "no se puede dejar tanta basura"). Inventory 2026-09-30: organized/_evidence
  232 MB (rollback backups c3a 19M, c3b 16M, c3d 43M, c4 20M; b122 82M), organized/_logs 56M, 4 stray assess-*.json from
  09-27 in niagara5-research-worktrees/ (deleted), /tmp/tmp.* dirs left by test runs. Rules: (a) every run writes only
  under organized/_evidence/<task>/ or the session scratchpad, never loose in repo/worktree roots or /tmp; (b) rollback
  backups carry a `RETENTION` note (delete when the task's results are merged + C1b regraded) and are deleted at C5;
  (c) tests clean their temp dirs (trap/tearDown) with a test that asserts no leftover; (d) `make clean-check` lists
  untracked/ignored leftovers, worktrees, merged branches, stale tmp, and runs at every task close and at C5;
  (e) each task close removes its worktree + local/remote branch. C5 close gate: clean-check prints nothing.
- [ ] C1b Full regrade with nested files on the best-of trees; report "fully proven (outer + nested)" per module.
- [x] C2a (code 03df7d1 reviewed: lineage review-e1d0c2509715fd09 approved+acknowledged; 174 tests OK; run 2026-09-29: 501/587 = 85.35% proven) Grade the 6 Tridium bin/ext jars (nre 704, niagarad 255, niagaraAnnotationProcessors 51, niagara-remote-client 8,
      securityBridge 2, splash 2 classes; trees already in organized/_bin-ext/*/vineflower2, no fidelity JSON yet). ~600 top-level.
- [x] C2b (c84b22a review-c7952c9610dddba9, 32d7c3e review-fb240cea1c278fe9, 80ee769 passive; make test 702 OK; run 8h16m) Grade third-party classes without proven upstream source (~14.6k: 38 identified artifacts incl. woodstox 735,
      nimbus-jose 203, mssql-jdbc 166, paho 109 vendor-modified; unidentified jxbrowser 5,914, prosys-opc-ua 4,591, swt 959)
      on organized/_lib-inf-3p trees; per-jar --release; Kotlin (~3.6k) uses javap as the verified representation (B125).
- [x] C2c (15aa01f review-4909f06f0c2e2261; report f02c89b: 63,538/79,241 = 80.2%) Fix upstream coverage loader for etc/m2 + regenerate docs/upstream-sources-report.md (C2b-G1).
- [x] C2d Decompile + grade the 3,997 uncovered third-party classes without a tree (C2b-G2; audit C2b-G4).
  Done (delegated writer; strict TDD bats g-j RED->GREEN): 3bb6d9c `n5-decompile.sh --third-party-uncovered`
  (RDD approved, lineage review-03eada57d4d2f0b9), 0402e78 report regenerated (assess passive). 3,997 classes:
  exact 1,970 / eq 36 / canon 39 / bytecode-only 1,418 / kotlin-javap-reference 534 -> 2,045 proven = 59.0% of 3,463
  gradable. Third-party overall 5,407/9,294 = 58.2% (64.9% of decompile-gradable); no no-decompiled-tree gaps left.
  C2b-G4 audit 0/30 false --release failures (vineflower2 rung only). Grading 10.6h (jxbrowser 8h, load ~23-30).
  Child gaps: C2d-G1 kotlin-reflect 412 metadata-less Kotlin classes counted bytecode-only (parent decision: typed
  state via artifact/kotlin marker detection, fold into C1b); C2d-G2 `$`-prefixed top-level names collapse in the
  population (nimbus $Gson$Types; 9,294 vs 9,295) -> fix n5-upstream-sources.py with a test; C2d-G3 1,418 bytecode-only
  -> C3 patch/splice candidates (optional, C3e); C2d-G4 silent skipped-other for artifacts outside bin/ext/etc-m2;
  process: grader should print a periodic per-class progress line.
- [x] C2e (9f8c367 review-42c252c99b42b763; 59/62 proven with JDK 8 javac, --legacy-jdk8-javac) Grade the 62 release-unsupported classes with JDK 8 javac (C2b-G3).
- [x] C3a (e248220, 624f772; review-54c9da1651ae379a approved; merged da9797a; 23 patcher tests + make test 666 OK) Extend the F8 doPrivileged patch tree to the 109 bytecode-only `reference to doPrivileged is ambiguous` classes.
- [x] C3b (11 commits cf50de5..1e39ba0, tools/n5-patch-mechanical.py, tree vineflower2m; 24 tests, make test 737 OK) Mechanical patches: anonymous-class-with-arguments (12), generic Object->String casts (12), `no suitable method` overload casts (22).
- [x] C3c (same stage as C3b) Split `cannot find symbol` (67) by missing symbol kind and patch the mechanical sub-classes.
- [x] C3d (23 commits ff7012c..6bf863b, 12 reviewed slices; make test 803 OK) Per-method splice with more donors / hand edits for the 103 one-method and 18 two-to-three-method mismatches
      (`<clinit>` is the top mismatched method: 166 of 602).
- [x] C2a-G1 bin/ext on the best-of ladder (base + doPrivileged + mechanical + splice rungs): 543/587 = 92.50% proven
  (was 501, 85.35%). Commits d1623a7, 3c46358, 4d6369e, 3c156e0, ba6b830; reviewed in 3 slices: 6f53a9c..3c46358
  review-a4d08a71f2ef7afc, 3c46358..036ca14 review-74d18ef1015a3e1d, 036ca14..ba6b830 review-6bf66779a39df0b8 (all
  approved, 0 corrections); make test 841 OK (writer), parent spot check 7 new tests OK.
- [x] C3d-G1 `--patch-label LABEL` (3c46358): non-default patch trees write their own rung file; `vineflower2.mech` added to BEST_OF_RUNGS.
- [x] C2d-G2 `$`-prefixed top-level names (d1623a7 upstream population, 4d6369e grader discovery): nimbus 84 classes,
  third-party 5,408/9,296 = 58.2%.
- [ ] C3e Hand reconstruction of the long tail (~220 compile errors + 4 many-method mismatches), prioritised by module use.
- [x] C4 Canonical-only -> byte-exact (worktree c4, 29 commits ee89ae9..3610d70, 2,418 changed lines; merged 69d0532).
  Exact 10,345 -> 11,827 (+1,482), canonical 3,513 -> 2,057, t2 72 -> 46, proven 13,955 unchanged, fully proven
  594 -> 1,503; 0 regressions, 0 missing (parent re-ran `n5-exact-regrade.py --organized-dir organized recount`).
  Writer: 30 random new exacts recompiled against the official classpath = 30/30; make test 888 OK (skipped=4).
  Review: 10 slices all approved, 0 corrections: review-50b5d4e9686963fb, -0fee76f491cc1e3a, -4909499e048f0cf5,
  -5369da65fabe2417, -9119193f3a75c2ca, -f65795ac81c92f5a, -0eb591f996a8354a, -99df7f00f3791317, -7a6d1cff57a05b85,
  -df0f6ac4ef3b9afa. Compiler verdict: shipped = javac 25 (major 69); residual non-exactness is SOURCE SHAPE, not
  compiler (pair fixtures per rule). The old premise "layout rules stay canonical" is DISPROVED: tail 872/1,407,
  min 358/693, web 110/416 solved. Residual 2,128 non-exact proven (1,019 no-donor, 916 >=4 methods not attempted,
  124 CFR/Procyon-best, 35 synthetic, 21 clinit, ...).
  Child gaps: C4-G1 JDK 25.0.3 check; C4-G2 (MUST before C1b) grader `--regrade-nonclean --patch-tree` skips
  baseline-clean classes, so C1b would NOT reproduce +1,482 — target non-exact classes with a patched source;
  C4-G3 LVT slot/scope solver for `web` (718); C4-G4 combo donors; C4-G5 string/enum switch reorder; C4-G6 refused map
  overwritten per run; C4-G7 ldc_w equivalent (25); C4-G8 span-scanner cost; C4-G9 (parent) recount without
  --organized-dir silently reports missing=14307 rc=0 -> fail loudly; C4b optional: 916 >=4-method + 124 CFR-best.
  Retention: /tmp/n5-jars-local (437 MB local jar copy, javac ~6x faster than /mnt/c, identical results) +
  /tmp/n5-jars-cache-local kept for C1b, delete at C5; organized/_evidence/c4-backup delete at C5.
- [ ] C5 Report + PR + merge; then open the N4 port as a separate ODD project.

## Route log
- C0: inline (state check only).
- C1: delegated writer (trigger: tool + tests, 2 non-trivial files); parent spot check re-ran the 19 nested tests: OK.
- C2/C3/C4 map: delegated read-only Explore (trigger: 4+ files).
- C2a: delegated writer (tool + tests); interrupted by a network error and a session teardown after commit 03df7d1;
  parent re-launched the real run inline in background (log organized/_evidence/c2a/run.log).
- C3a: delegated writer in worktree c3a (feat/n5-c3a-doprivileged); first writer left e248220 + 624f772, resumed by a fresh writer.
- C1 review: lineage review-fb22cee6e85fed40 approved + acknowledged (4 lenses).

## Progress / evidence
- 2026-09-29: branch feat/n5-fidelity-completion from main 3d1bc79. RDD status: on (global).
  Class-file census (organized/*/extracted, excluding _*): 14,683 top-level, 6,186 nested.

- 2026-09-29 C2/C3/C4 map (read-only Explore, script scratchpad/a.py): best-of recount reproduces T21 exactly
  (14,307 / 10,306 / 24 / 3,305 / 70 / 602). 602 bytecode-only = 477 no-compile + 103 one-method + 18 two-three + 4 many.
  Top modules: baja 49, bacnet 38, provisioningNiagara 27, lonworks 25. bin/ext: 109 jars, 6 Tridium (1,022 classes incl. nested),
  103 third-party (42,936). _lib-inf-3p: 94 artifact trees, 23,683 .java, ungraded. Canonical winners: base 2,980, patched 297, spliced 79.
  Open reconcile: upstream coverage recount 14,638 uncovered of 76,129 vs report 16,228 of 77,719 (1,590 via classdiff fallback) -> C2b checks.

- C1 result: per-class `nested` {files, missing, extra, drift_suspected} + `fully_proven` (outer clean AND all shipped nested
  clean AND no missing/extra); SCHEMA_VERSION stays 2, separate NESTED_SCHEMA_VERSION=1 makes legacy JSON not up-to-date.
  Smoke: axvelocity 12 nested (9 exact, 1 mismatch, 2 not-graded), 20/22 fully proven; backup 20 nested (3 exact, 17 not-graded
  under 2 bytecode-only outers), 5/8 fully proven.
  Child gaps: C1-G1 nested taken from the outer's winning rung only (score outer+nested jointly); C1-G2 anonymous numbering
  drift reported, not re-paired; C1-G3 nested of never-compiled outers are not-graded (regrade after C3); C1-G4 regrade-nonclean
  cannot backfill nested for clean classes -> C1b needs a full --force run first.

- C2a result (vineflower2 base tree only, organized/_bin-ext/<jar>/fidelity.vineflower2.json): 587 top-level classes —
  exact 401, canonical 99, canonical-t2 1, bytecode-only 86 -> 501 proven (85.35%). Per jar: nre 304/49/1/64, niagarad 48/46/0/21,
  niagaraAnnotationProcessors 43/3/0/1, niagara-remote-client 3/1, securityBridge 2, splash 1. Nested: 435 files, 273 not-graded
  (under bytecode-only outers), fully proven 497.
  Child gap C2a-G1: bin/ext got only the base rung — apply F8 doPrivileged patch, F9 splice, and the v1 tree to _bin-ext
  (fold into C3a/C3d once those land) so it is graded on the same best-of ladder as modules.

- C3a result (grader JSON fidelity.vineflower2.patched.json, 46 modules regraded, backup organized/_evidence/c3a-backup/):
  ambiguity resolved in all 109; proven 0 -> 5 (1 exact, 4 canonical); compiles-mismatch 81 -> 83; no-compile 25 -> 21;
  missing vineflower2p rung 3 -> 0. The "doPrivileged ambiguous" label was stale for 104 (81 already compiled on the patched rung).
  Child gaps: C3a-G1 83 compile-but-mismatch (26 with 0 mismatched methods -> class-level attribute difference; <clinit> 14, doRun 8);
  C3a-G2 21 unrelated javac errors (cannot find symbol 6, bad operand 3, inference 3, already-defined 2, unreachable 2, ...);
  C3a-G3 decision (parent, by recommendation): on a rank tie the best-of record must carry the first_error/mismatch of the
  most-advanced ladder rung (spliced > patched > canon > base), with every rung's error kept, so labels are not stale.
  Implement in n5-fidelity.py after C2b lands (same file).

- C3b/C3c/C3a-G2 result (grader best-of over 14,307 top-level, 56 modules regraded with --patch-tree vineflower2m, backup
  organized/_evidence/c3b-backup/): before exact 10,307 / equiv 24 / canon 3,309 / t2 70 / bo 597 = 13,710 (95.83%);
  after 10,319 / 24 / 3,349 / 70 / 545 = 13,762 (96.19%). +52 proven (12 exact, 40 canonical), 0 regressions.
  170 no-compile targets: 90 compile after patching (52 proven, 38 mismatch), 79 still fail. Top fixers by proven:
  inner-ctor-outer-arg 20, pattern-binding-scope 19, protected-member-import 14. Map labels for anonymous-with-arguments (12)
  and `no suitable` (22) were stale (record-level first_error from CFR/Procyon rungs): recomputed 0 and 3.
  Child gaps: C3b-G1 38 compile-but-mismatch (overlaps C3a-G1; try rename vs brace for switch-group); C3b-G2 declare
  condition-assigned varN from the shipped LocalVariableTable; C3b-G3 six bacnet export descriptors + inherited raw fields;
  C3b-G4 patcher should read a baseline population automatically.
  Parent decisions (by recommendation): the 190 modules without an m-patched class are not regraded now (their patched
  JSON is unchanged; C1b final run covers everything); run the vineflower2p + vineflower2m stages over _bin-ext in C2a-G1;
  C3a-G3 + C3b-G4 are one tooling task after C2b releases n5-fidelity.py.

- 2026-09-30 user decision: close the session once C2, C3, C4 and C5 are done (C1b final regrade runs before C5), leaving
  everything clean for a new session (no worktrees/processes left, branches merged/deleted, memory + resume point saved).
  The frontier research chain moves to the NEW session.

- C2b result: reconciliation = the 1,590 gap is exactly 4 etc/m2 artifacts the jar mirror lacks (report fell back to classdiff
  top-level totals with 0 covered). Authoritative population (`n5-upstream-sources.py uncovered-population`): 79,241 third-party
  classes, 63,538 covered, 15,703 uncovered in 50 jars (9,295 top-level, 959 Kotlin). Graded 27 trees / 5,297 top-level:
  exact 3,087, equivalent 12, canonical 201, t2 3, bytecode-only 1,507, kotlin-javap-reference 425, release-unsupported 62
  -> proven 3,303 (62.4%; 68.7% of decompile-gradable), fully proven 3,232. prosys 1,891/48/1,178; swt 429/68/155;
  woodstox 384/57/45 (+52 release-unsupported); xml-apis-ext 185/-/7; mssql 58/5/49; paho 49/6/41; nimbus 42/13/23.
  Child gaps and parent decisions (by recommendation):
  C2b-G1 docs/upstream-sources-report.md headline undercounts (mirror loader lacks etc/m2) -> FIX (install-dir fallback + regenerate),
    correcting a published number is required; task C2c.
  C2b-G2 3,997 uncovered top-level classes have no decompiled tree (jxbrowser 2,691 + javafx/swing/swt variants, kotlin-stdlib
    2.4.10 430, kotlin-reflect 453, okhttp/okio, bc*, byte-buddy, jackson etc/m2) -> decompile + grade; task C2d.
  C2b-G3 62 release-unsupported (major <= 51) -> grade with the installed JDK 8 javac (/usr/lib/jvm/java-8-openjdk-amd64); task C2e.
  C2b-G4 --release N API restriction may cause false bytecode-only; audit sample in C2d. C2b-G5 C3-style patches on the 1,507
  third-party bytecode-only after Tridium work. C2b-G6 reproducibility note (run uncovered-population first) -> report text.

- C3a-G3 done (b885808, review-3ab6acefdaf7e654): per-record detail_rung + rung_errors; merge_best_of_records() for cross-JSON
  consumers (C3a-G3-G1: existing JSON keeps old first_error until the C1b regrade).
- C3d result (best-of recount, 0 rank regressions over 14,307): exact 10,345 / eq 25 / canon 3,513 / t2 72 / bytecode-only 352
  -> 13,955 proven (97.54%, +193 all via spliced rung vineflower2s; 182 fully proven). Mechanisms: vineflower-cons donor 60,
  clinit order 29, vf2v-ir0 16, source hypotheses (compound-assign, unfold arrays, lift increments, iinc), LVT local types 5,
  structure repair + climb ~24, pattern-matching-off primary 12 (no-compile -> proven). Brace-all won C3b-G1 (5 clean vs 4/3).
  Residual 352 = 63 no-compile + 289 mismatch (191 single-method), organized/_evidence/c3d/residual.tsv.
  Child gaps: C3d-G1 generalize patch_output_label (--patch-label) in n5-fidelity.py; C3d-G2 LVT slot/scope AST reconstruction
  (largest family); C3d-G3 lambda/anonymous/access$ numbering via declaration reordering; C3d-G4 checkcast on intersection
  casts/varargs; C3d-G5 iinc inside expressions; vineflower2m tree not regenerated with brace-all.

- C2a-G1 result (evidence organized/_evidence/c2a-g1/): exact 401 -> 412, canonical 99 -> 130, fully proven 539/587 (91.8%).
  Bytecode-only nre 64 -> 28, niagarad 21 -> 15, niagaraAnnotationProcessors 1. Stages: 2p nre 45 classes/135 sites +
  niagarad 7/9; 2m nre 2 + niagarad 2 compile (regraded with --patch-label mech, m re-run after the p regrade); 2s 53 targets,
  9 spliced, refused no-donor 25 / clinit 2 / structural 1 / synthetic 2.
  Child gaps (parent decisions by recommendation): C2a-G2 44 residual bytecode-only bin/ext classes, mostly no-donor -> fold
  into C3e or keep as residual; C2a-G3 n5-patch-mechanical.py reads only fidelity.vineflower2.patched.json (fixed RUNGS) ->
  read BEST_OF_LABELS files, also closes C3b-G4; C2a-G4 4 nre clinit/synthetic mismatches -> C3d-G2/G3 families;
  C1b MUST regrade module m-stage results with `--patch-label mech` (C3b m results still sit in .patched.json);
  C2d-G5 n5-extract-census.py:127 and n5-recon-helper.py:72 still split at the first `$`.
  Process note: rdd.py needs an ABSOLUTE worktree path (a relative one is re-resolved inside the worktree and fails with
  KeyError next_transition).

## Handoff / resume point (rewritten before the 3rd context compaction, 2026-10-01 ~01:10 CST)
Numbers: Tridium top-level proven 13,955/14,307 = 97.54% (exact 11,827 after C4); bin/ext 543/587 = 92.50% (C2a-G1 done,
reviewed); third-party 5,408/9,296 = 58.2%. Last REVIEWED boundary on this branch: 69d0532 (C4 merge; 10 slices approved;
later docs-only commits are passive).
IN FLIGHT: none (C4 merged 69d0532; worktree c4 and branch feat/n5-c4-exact removed).
REMAINING ORDER: P1 leak guard, P2 test fast lane, P3 review tooling, P5 `$` lint -> C4-G2 grader fix -> C1c (domain-free
cache=checkpoint engine, +P4 generated facts) -> C1d dedup -> C3h triage -> C3f Vineflower sweep -> C3g AI-proposed
reconstruction -> C1b ALONE (jobs=cores, --patch-label mech for module m results) -> C5 report + PR + merge (clean-check
must print nothing; delete rollback backups c3a/c3b/c3d/c4-backup) -> clean close.
RULES: never merge before an RDD review that assess says is due (PR #25 slip); no garbage (P7); possibility-first
(no bare "can't"); speed without sacrificing quality; strict TDD; Conventional Commits without AI attribution;
vendor source/JSON never tracked (repo PUBLIC; b118 history purge declined by the user 2026-09-30).
Related work outside this repo (see Engram + memory files): kit PR angeles725/sdd-investigacion#1278 (possibility-first
#1263-#1267, RDD approved review-a4daa3f9f6bf9b71, waiting toolbelt-tests CI, then merge + remove worktree
~/investigacion/sdd-investigacion-worktrees/possibility-first + delete branch; follow-up PR for #1268-#1270); N4 agent
MCP research focus n4-agent-mcp in niagara-research (B1168+).

## Next step
Next: P1/P2/P3/P5, C4-G2 grader fix, C1c (+P4), C1d, C3h, C3f, C3g, C1b alone, C5.
