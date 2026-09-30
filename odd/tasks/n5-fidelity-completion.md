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
- [ ] C1b Full regrade with nested files on the best-of trees; report "fully proven (outer + nested)" per module.
- [x] C2a (code 03df7d1 reviewed: lineage review-e1d0c2509715fd09 approved+acknowledged; 174 tests OK; run 2026-09-29: 501/587 = 85.35% proven) Grade the 6 Tridium bin/ext jars (nre 704, niagarad 255, niagaraAnnotationProcessors 51, niagara-remote-client 8,
      securityBridge 2, splash 2 classes; trees already in organized/_bin-ext/*/vineflower2, no fidelity JSON yet). ~600 top-level.
- [x] C2b (c84b22a review-c7952c9610dddba9, 32d7c3e review-fb240cea1c278fe9, 80ee769 passive; make test 702 OK; run 8h16m) Grade third-party classes without proven upstream source (~14.6k: 38 identified artifacts incl. woodstox 735,
      nimbus-jose 203, mssql-jdbc 166, paho 109 vendor-modified; unidentified jxbrowser 5,914, prosys-opc-ua 4,591, swt 959)
      on organized/_lib-inf-3p trees; per-jar --release; Kotlin (~3.6k) uses javap as the verified representation (B125).
- [ ] C2c Fix upstream coverage loader for etc/m2 + regenerate docs/upstream-sources-report.md (C2b-G1).
- [ ] C2d Decompile + grade the 3,997 uncovered third-party classes without a tree (C2b-G2; audit C2b-G4).
- [ ] C2e Grade the 62 release-unsupported classes with JDK 8 javac (C2b-G3).
- [x] C3a (e248220, 624f772; review-54c9da1651ae379a approved; merged da9797a; 23 patcher tests + make test 666 OK) Extend the F8 doPrivileged patch tree to the 109 bytecode-only `reference to doPrivileged is ambiguous` classes.
- [x] C3b (11 commits cf50de5..1e39ba0, tools/n5-patch-mechanical.py, tree vineflower2m; 24 tests, make test 737 OK) Mechanical patches: anonymous-class-with-arguments (12), generic Object->String casts (12), `no suitable method` overload casts (22).
- [x] C3c (same stage as C3b) Split `cannot find symbol` (67) by missing symbol kind and patch the mechanical sub-classes.
- [ ] C3d Per-method splice with more donors / hand edits for the 103 one-method and 18 two-to-three-method mismatches
      (`<clinit>` is the top mismatched method: 166 of 602).
- [ ] C3e Hand reconstruction of the long tail (~220 compile errors + 4 many-method mismatches), prioritised by module use.
- [ ] C4 Push canonical-only classes toward byte-exact where source-controllable: expression-level rules (r1 503, iinc 21,
      cmp1 18, const 1, boolmat 53 ~ 700 classes) first; inspect the 210 canonical classes with no rule fired;
      layout rules (tail 2,101, min 1,192, web, inl, merge, dse, thread, peep) are javac codegen shape and stay canonical.
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

## Next step
C3b slice reviews -> merge; C2b result -> review; then C3a-G3/C3b-G4 tooling, C3d (C3a-G1 + C3b-G1 + one-method splice), C2a-G1, C4, C1b, C5.
C1b (full --force regrade) is deferred until the C2/C3 tool changes land, so it runs once.
