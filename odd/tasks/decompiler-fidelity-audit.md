# Decompiler-fidelity and method blind-spot audit

## Objective
Make the corpus immune to decompiler-artifact and method errors: verify which Java-language features are
distinguishable at the bytecode level on Tridium's actual class files, audit every corpus claim that depends
on that distinction, and audit the other recurring method failures observed in waves 10-12.

## Problem / why
Vineflower resugars classic idioms into modern syntax (B90 §90.2, B98 §98.8), which inflated B70's
`instanceof`-pattern adoption census. The caveat lives only in blocks, not in the decompiler docs, the tool
header, the porting guide, or the writer prompt, so new writers can repeat the mistake. The orchestrator's own
first restatement of the rule ("confirm with javap") was incomplete, and the second ("enhanced for is
indistinguishable") was wrong — both caught only by running the experiment. Other recurring failures in the
same family: absence claims from the wrong location/name (B102 pxEditor, B98 saml.jar), comparing against a
block's prose instead of its raw artifact (B106-G2), and evidence cited only in ephemeral /tmp scratch.

## Scope (authorized)
Read-only research over organized/, installs, and the corpus; edits to corpus blocks (§14 pointers),
docs/, tools/ header comments, RESEARCH-STATE; one new block (B115); retro kit-delta proposals only
(kit is propose-never-apply).

## Constraints
- TDD mode: Strict TDD enabled (user CLAUDE.md). Applies to tools/ code changes; this feature changes docs and
  comments only unless a tool check is added (then RED first).
- RDD: user-granted. Docs/blocks commits assess passive; tools/ code would be reviewed natively.
- Shared checkout with wave-13 writers (B112-B114) on feat/n5-wave14: add own paths only.

## Tasks
- [x] T1 Fidelity experiment: javac 25 old-vs-new idiom pairs, javap diff with and without -g; check whether
      Tridium class files carry LocalVariableTable. Route: inline (1 scratch dir). Evidence: scratchpad/fidelity/.
- [x] T2 Audit all feature-adoption claims (SAFE / SUSPECT / ALREADY-CORRECTED). Route: delegated (4+ files, mapping trigger).
      Result: 2 already-corrected (B25 §25.6, B70 §70.4), 9 SUSPECT quote sites (B27 §27.5, B37, B41 §41.1, B67, B82 §82.1,
      B84 §84.2/§84.3, B86, B103), none tracked as gaps. Orchestrator verified: B84 §84.2 EntitlementApi pattern switch REAL
      (2 invokedynamic typeSwitch call sites — orchestrator first reported 12, a grep -c artifact over javap -v that also counts BootstrapMethods entries; corrected by B115 §115.5); RetrieveEntitlements has no switch (claim over-attributed); B84 §84.3 BQudtUnitTag FALSE (N4-4.15 major 52
      and N5 major 69 bytecode identical; Vineflower resugars only the v69 class).
- [x] T3 Audit other method blind spots. Route: delegated (mapping trigger). Result (orchestrator-verified items marked *):
      * C13 baseline attribution: B13 §13.5 "18 N5-only modules" computed vs N4.14 only; PowerB 4.15.3.28 ships cloudLink(-rt/ux/wb),
        cloudLinkAzure, cloudLinkForge(-rt/ux), cloudLinkHonSbp, cloudLinkNcs, jodaTime (ls verified).
      * C14 compile-time constant inlining: B96/B105/B111 dead-constant/shadow-literal census never considers JLS constant inlining
        (grep: no inlining discussion); javac 25 proof: K.HOST → ldc literal, Vineflower renders literal (scratchpad/fidelity/constinline).
      - 7 of 9 T2 quote sites harmless behavior quotes; B84 §84.2/§84.3 are the 2 defects.
      - Absence: B98/B102 already self-corrected; B42.8/B3/B81 used robust methods.
      - Ephemeral: 151 /tmp paths near CERT-hw/live, 13 already gone.
      - Beta-vs-GA: sample clean.
      - Not done: full prose-vs-raw sweep (only the known B106 instance).
- [ ] T4 (delegated writer running) Write B115 (fidelity matrix + audit results) and §14 pointers in affected blocks. Route: delegated writer
      if 2+ non-trivial blocks change, else inline.
- [ ] T5 Add the fidelity rule to docs/decompiler-bakeoff.md, docs/n4-to-n5-porting-guide.md, tools/README.md,
      tools/n5-decompile.sh header, and the writer prompt. Route: inline (mechanical once T1-T3 known).
- [x] T6 Retro retros/2026-09-28-n5-method-errors-retro.md (fresh opus agent; verify-retro OK): 14 kit deltas (6 high) → sdd-investigacion issues #1204-#1217 (stage-retro-issues --apply, created=14 failed=0).
- [ ] T7 Commit, RDD assess, PR, merge.

## Prevention (user requirement 2026-09-28: "these same errors must not happen again")
Prose rules already failed once (B84 was written after B90 established the resugaring rule). Prevention must be
MECHANICAL and fail closed:
- [ ] T8 (delegated writer running; R7 constant-inlining + R8 baseline-attribution added) tools/lint-block.py (TDD, fixtures): rules R1 syntax-adoption/N4-N5 syntax-delta claim without bytecode/docSource
      evidence token; R2 absence claim without class-level census token; R3 [CERT-hw]/[CERT-live] evidence only under /tmp;
      R4 child-gap bullet without coverage-check + measured-by clauses; R5 null-argument/fail-open permission claim without a
      resolved dispatch target; R6 comparison against another block without citing its raw artifact. Enforced (FAIL) for
      blocks >= 115; older blocks in --audit mode (report only) to drive T4 fixes. Explicit per-line waiver token with reason.
      Route: delegated writer (2+ non-trivial files).
- [ ] T9 Wiring: tools/githooks/pre-commit (lint staged blocks + check-gap-drift + verify-block), `make install-hooks`
      (core.hooksPath), SessionStart hook warns if hooks not installed, GitHub Actions CI (make test + lint). No branch
      protection on this private plan, so the orchestrator merge step MUST wait for green checks (gh pr checks --watch).
- [ ] T10 Durable evidence: evidence/b<N>/ in repo for small [CERT-hw] artifacts (size cap), writer prompt updated.
- [ ] T11 Versioned writer prompt docs/writer-prompt.md (replaces the session-scratch common.txt) with the checklist.
- [ ] T12 Orchestrator-side memory: feedback memory + engram; retro kit deltas (T6) mirror R1-R6 into METHODOLOGY proposals.

## Maximum decompile fidelity (user requirement 2026-09-28: "the decompile must be right, no inventions, not tainted; try everything possible")
- [x] T13 Integrity + completeness census [CERT-hw]: 252 recon.json (247 modules + bin/ext) — 0 jar sha256 mismatches vs the
      installed jars, 0 missing jars; 14,894 top-level classes, 0 without a .java (vineflower or fallback); CFR fallback used in
      6 modules (andoverAC256, backup, bajaui, ccn, ffmpeg, opcUaClient); obfuscation heuristic > 0.2 in none.
      docSource originals cover 2,776 of 7,284 top-level classes in docSource-eligible modules. Route: inline.
- [ ] T14 Lossy-aspects catalog (answers "what else is not faithful"): synthetic javac-25 experiments for every candidate loss
      class + EMPIRICAL differential of Vineflower output vs the 2,776 docSource originals (normalized), taxonomy with counts.
      Output: B116. Route: delegated researcher.
- [ ] T15 Semantic fidelity grader tools/n5-fidelity.py (TDD): recompile each decompiled class against the original jars and
      compare normalized bytecode per method with the shipped class; on mismatch try CFR/Procyon/JADX and keep the first that
      round-trips; grade per class (docsource-original / roundtrip-exact / roundtrip-normalized / compiles-mismatch / no-compile);
      write organized/<mod>/fidelity.json + committed docs/decompile-fidelity-report.md. Route: delegated writer.
- [ ] T17 Extraction + native fidelity (B117): nested/multi-release jars, extracted/ byte-exactness vs jar entries, resources,
      skipped bin/ext jars, N5 obfuscation re-check, jarsigner verification of all module jars, native inventory + every native
      claim classified single-tool vs >= 2 anchored instruments with corroboration run now. Route: delegated researcher.
- Redundancy ladder added to T15 (user: "use everything, no limits"): kit corroborate-java.sh (java-corroboration.v1), krak2
  disassembly cross-check of the normalizer, a 4th independent decompiler (JD-Core/Fernflower, official source + sha256, else
  typed blocked-on-tool), bajadoc member-set cross-check via niagara-help, per-class consensus + `bytecode-only` grade.
- [ ] T18 Logic-recovery method ladder (B118; user: "try a thousand ways"): M1 Vineflower conservative + line-mapped variant,
      M2 bytecode-level analysis (Joern jimple2cpg / SootUp / OPAL call graphs, dispatch resolution), M3 differential execution of
      pure station-independent classes (original vs recompiled), M4 runtime tracing of license-free Tridium CLIs, M5 dataflow
      (CodeQL buildless / Joern), M6 krak2 round-trip, M7 others. Hard limits: no live station, no license bypass. Route: delegated.
- [ ] T16 Make the grade visible where claims are made: lint rule R9 — a [CERT] citation into organized/<mod>/vineflower/<cls>
      whose class grade is compiles-mismatch/no-compile needs a bytecode (javap) or docSource co-citation. Route: after T15.

## Additional failure classes observed during this feature (fold into T3/T6)
- C9 Gap opened without an ALREADY-COVERED check at open time: B109-G3 was already answered by B4 §4.2 + B109 §109.3 (B114).
- C10 A figure carried forward from one tool/method into a gap text without its method: "4,209 types" (Ghidra count) vs
  2,418 typelinks entries (B113) — gaps must state how a number was measured.
- C12 Call-site argument read without resolving the dynamic-dispatch target: B107 §107.3 called three
  `getPermissions(null)` sites fail-open, but they dispatch to BRootHistoryFolder's override which ignores cx and
  fetches real session permissions (B112 §112.1, orchestrator verified BRootHistoryFolder.java:42-49).
- C11 Writers keep evidence only in session scratch (/tmp) — my own writer prompt instructs it; durable preservation needed.

## Acceptance criteria
- Every feature-adoption claim classified with a resolving check; every SUSPECT either fixed or tracked as a named gap.
- The rule appears in every place a future writer reads before decompiling.
- Each T3 failure class has a count, examples, and either fixes or named gaps.

## Progress / evidence
- T1 [CERT-hw] javac 25.0.x `--release 25`, scratchpad/fidelity/{old,new}/F.java, javap -c -p (and -c -l -p with -g):
  - IDENTICAL bytecode (with and without -g): `instanceof` pattern vs instanceof+cast, `var`, text block vs
    concatenated literals, `a + b` string concat (indy StringConcatFactory either way — a compile-target
    signal, not a source feature).
  - DISTINGUISHABLE: array for-each (javac copies the array ref + caches length into synthetic locals);
    Iterable for-each with -g (no named iterator in LocalVariableTable); arrow switch / switch expression
    (value-on-stack + single store/goto shape — heuristic, weaker); lambda (invokedynamic LambdaMetafactory,
    no F$1 inner class) vs anonymous class; pattern switch (typeSwitch indy); records/sealed (class attributes).
  - Tridium N5 classes ship WITH debug info: control.jar niagara/control/BNumericWritable.class has
    62 LocalVariableTable + 63 LineNumberTable entries, major 69.
  - Correction to the orchestrator's chat statement: enhanced for IS bytecode-distinguishable.

## Next step
Wait for T2/T3 reports, then T4-T7.
