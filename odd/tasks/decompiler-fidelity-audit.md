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
- [x] T4 (ce7b266) Write B115 (fidelity matrix + audit results) and §14 pointers in affected blocks. Route: delegated writer
      if 2+ non-trivial blocks change, else inline.
- [ ] T5 Add the fidelity rule to docs/decompiler-bakeoff.md, docs/n4-to-n5-porting-guide.md, tools/README.md,
      tools/n5-decompile.sh header, and the writer prompt. Route: inline (mechanical once T1-T3 known).
- [x] T6 Retro retros/2026-09-28-n5-method-errors-retro.md (fresh opus agent; verify-retro OK): 14 kit deltas (6 high) → sdd-investigacion issues #1204-#1217 (stage-retro-issues --apply, created=14 failed=0).
- [ ] T7 Commit, RDD assess, PR, merge.

## Prevention (user requirement 2026-09-28: "these same errors must not happen again")
Prose rules already failed once (B84 was written after B90 established the resugaring rule). Prevention must be
MECHANICAL and fail closed:
- [x] T8 (d458bc1 + fix aaa369d; RDD review-ff9661ae41472f13 approved on d458bc1; fix under review) tools/lint-block.py (TDD, fixtures): rules R1 syntax-adoption/N4-N5 syntax-delta claim without bytecode/docSource
      evidence token; R2 absence claim without class-level census token; R3 [CERT-hw]/[CERT-live] evidence only under /tmp;
      R4 child-gap bullet without coverage-check + measured-by clauses; R5 null-argument/fail-open permission claim without a
      resolved dispatch target; R6 comparison against another block without citing its raw artifact. Enforced (FAIL) for
      blocks >= 115; older blocks in --audit mode (report only) to drive T4 fixes. Explicit per-line waiver token with reason.
      Route: delegated writer (2+ non-trivial files).
- [x] T9 (d458bc1, aaa369d: hook lints staged blobs, integration-tested) Wiring: tools/githooks/pre-commit (lint staged blocks + check-gap-drift + verify-block), `make install-hooks`
      (core.hooksPath), SessionStart hook warns if hooks not installed, GitHub Actions CI (make test + lint). No branch
      protection on this private plan, so the orchestrator merge step MUST wait for green checks (gh pr checks --watch).
- [x] T10 (evidence/b115, README LVT fact corrected in aaa369d) Durable evidence: evidence/b<N>/ in repo for small [CERT-hw] artifacts (size cap), writer prompt updated.
- [x] T11 (d458bc1) Versioned writer prompt docs/writer-prompt.md (replaces the session-scratch common.txt) with the checklist.
- [ ] T12 Orchestrator-side memory: feedback memory + engram; retro kit deltas (T6) mirror R1-R6 into METHODOLOGY proposals.

## RESUME HERE (written 2026-09-28 before a context compact)
State: branch feat/n5-wave14 pushed; draft PR #15 open (CI was green at d9a6f9b; re-check after bb58475).
Commits after PR#14 (all tools commits RDD-approved+acknowledged unless noted): 9523a9e B116 · f4e49f8 census ·
7bc188c B117 · 16fc6a8 grader · 1791db1 v2 · 1ad56eb xref · b8eebcd B118 · 9592b82 porting-guide fix · f591074
upstream-sources · 1e44e71 v2 hardening · 0aaae58/d9a6f9b javap fixes · 6fb316d tests · 80c5f90 T20 (range RDD
review-6f1c46518f56b786 approved) · 97a5d23 compare-skips (NOT yet RDD-reviewed) · bb58475 cons + extra-tridium (NOT yet
RDD-reviewed).
Running at compact time: `bash /tmp/run-cons-campaign.sh` (log /tmp/cons-campaign.log; phases: cons over 247 modules
-P 6 → cons --bin-ext → --extra-tridium; prints ALL_DONE). Also a bats run: scratchpad/bats-t22.log (ends EXIT=<rc>).
Next steps, in order:
1. Wait for ALL_DONE in /tmp/cons-campaign.log (if the process died: re-run the same script; it is idempotent).
   Verify: count organized/*/vineflower-cons (expect 247 minus class-less modules), organized/_etc-m2/* + _lib/* (10 jars),
   organized/*/lib-inf/*; recon.json cons.status all ok.
2. Run the line-mapping spot check /tmp/linecheck-t22.py (adapted from evidence/b118/linecheck.py; classes
   BNumericWritable, StyleUtils, ValueDocDecoder, Column) — mapped `// N` must match docSource lines; record result.
3. Fill the "Campaign run" numbers in docs/decompiler-bakeoff.md (T22 section), commit.
4. Confirm bats-t22.log EXIT=0.
5. RDD range review 80c5f90..HEAD (covers 97a5d23, bb58475, docs) in a clean worktree under
   /home/cristian/niagara5-research-worktrees/rdd-<sha>; read advisories, verify, fix real ones (TDD).
6. Push, mark PR #15 ready, wait for green CI (`gh pr checks 15`), merge via REST if GraphQL fails:
   `gh api -X PUT repos/angeles725/niagara5-research/pulls/15/merge -f merge_method=merge`.
7. Final single notice to the user with verified numbers (user asked for ONE notice when pipeline + verification done).
Deferred to next session (user decision): all research child gaps (B115-B118 G*), T16 lint R9, T16b docs lint,
T18b xref hardening, T21 full-corpus grading, grader report follow-ups, upstream-sources integration test.
Key verified numbers: B116 11/36,977 Vineflower semantic defects (D1-D11); v2 fixes D4/D5; grader sample 192 classes:
v1 124 exact, v2 125, 0 worse; docSource 3,707 classes byte-identical; B117 21,751 classes byte-exact, 356 jars signed,
Authenticode 20/20; upstream sources 154/154, 92.4% third-party classes; krak2 -r byte-identical; jar mirror
niagara5-research-localcache/jar-mirror-5.0.0.28 (sha256-verified, ~4.3x faster grading).

## Session focus change (user, 2026-09-28)
Research child gaps (B115-B118 G*) are deferred to the next session. Remaining work in THIS session: verify v1 vs v2,
make the decompile complete and as faithful as possible.
- [x] T18 (B118, b8eebcd; tool 1ad56eb RDD review-afef2ecdf952d3f2 approved) Logic-recovery method ladder.
- [x] T18b (TDD; single commit on branch t18b-xref-hardening, worktree niagara5-research-worktrees/t18b-xref-hardening) Hardened
      n5-bytecode-xref per its review-afef2ecdf952d3f2:
      overriders now matches name+descriptor, with `--desc` to disambiguate overloads (R2-001); duplicate class names across
      modules are kept and reported via `idx["duplicates"]`/`duplicate_classes` in every subcommand's output (R2-002); `--cha`
      now also accepts subtype receivers that inherit the method (invokevirtual/invokeinterface on a subclass that does not
      redeclare it), stopping descent at any subtype that redeclares it (R3-001); every subcommand's JSON and text output now
      carries `parse_errors`/`parse error(s)` (R4). Evidence: 11 new/updated unit tests (RED confirmed for each fix, then
      GREEN), full `make test` green (298 tests, 4 pre-existing skips), real-corpus sanity check on organized/{baja,control}
      -- `callers niagara.sys.BComponent started --cha` went from 5 sites (old code) to 10 sites (new code), the 5 new ones
      correctly tagged `subtype-owner`. Caller lists under `--cha` are now complete modulo reflection/invokedynamic (see
      tools/README.md).
- [~] T22 Completeness (code bb58475; Tridium-half campaign RUNNING at compact time) (third-party half DONE f591074: 154/154 upstream -sources.jar, 92.4% class coverage; Tridium half + conservative tree delegated): decompile (v2 + conservative line-mapped view) the 10 out-of-pipeline Tridium jars (etc/m2, lib doclet)
      and the Tridium-owned nested LIB-INF jars; for identified third-party jars fetch the upstream -sources.jar by exact
      Maven coordinates (original source beats any decompile); record per-class best representation. Route: delegated,
      after T19b lands (same script).
- [x] T22-rdd Range review 80c5f90..HEAD (tool base 7f6ba50; covers 97a5d23, bb58475, docs): lineage
      review-83022868fd33530e APPROVED + acknowledged (authority burned), 4 lenses, 10 non-blocking advisories.
      Orchestrator verified the WARNINGs: R4-libcache-empty-scan-strips-context REAL → T23; R3 .complete removal under
      concurrent readers = by design (readers fail loudly with "run --prepare-libcache"; prepare runs serially first);
      R3 source-sha cache reload per jar = performance only; R2 readability items deferred.
- [x] T23 (8cd9467; follow-up in the T27 commit: two synthetic --extra-tridium bats fixtures had an empty modules dir, which the new guard correctly refuses — the orchestrator had run only the 13 libcache tests, not the full file, before committing T23; fixtures now carry one module jar) (TDD, bats T23a RED observed: exit 0 on an empty scan) `--prepare-libcache` refuses a zero-jar scan of
      N5_MODULES_DIR + N5_BIN_EXT_DIR with exit 2 BEFORE touching the cache, so a mistyped/unmounted path can never
      publish a "complete" cache that strips all LIB-INF context. GREEN: 13/13 libcache tests, shellcheck clean.
      Route: inline (one script + one test).
- [x] T24 (1875258) bajaui whole-module Vineflower timeout (found during the T22 line-mapping spot check; TDD, bats,
      strict-TDD writer): root cause isolated by per-package then per-class bisection to exactly ONE class,
      `com/tridium/ui/theme/custom/nss/query/NSS2SelectionResult` (its method-local record
      `NSS2SelectionResult$1ValueAndAdvice` hangs Vineflower's ClassWriter.writeClass forever). Fix (shared by v1/v2/
      cons, no copy-paste — `vf_handle_primary_timeout`/`vf_isolate_hung_classes`/`vf_build_excluded_classes_regex`/
      `vf_render_noinner_view` in tools/n5-decompile.sh): on a whole-jar timeout, bisect by package then by top-level
      class (own N5_ISOLATE_TIMEOUT budget, default 90s), re-run the whole jar ONCE with Vineflower's
      `--excluded-classes=<regex>` excluding exactly the hung class(es) (regex semantics — FULL match against the
      `/`-separated internal name — verified empirically against the real vineflower-1.12.0.jar, not guessed), CFR
      for the hung class(es), plus a best-effort `--decompile-inner=false` secondary view
      (`vineflower*-noinner/`). New env var N5_ISOLATE_TIMEOUT (default 90s), new recon.json fields
      (`primary_status: ok_with_excluded`, `fallback_reason: primary_hang_isolated`, `excluded_classes`,
      `isolate_time_seconds`, `primary_timeout_attempt_seconds`, `isolation_status`); a hang that can't be isolated
      keeps today's original whole-module-CFR behavior exactly, with `isolation_status` explaining why. Real bajaui
      re-run on the local mirror, all three variants: `primary_status=ok_with_excluded`,
      `excluded_classes=[NSS2SelectionResult]`, 565/566 top-level `.java` in the primary tree (v1/v2/cons), 1 file in
      fallback, 2 files in the noinner secondary view. Found and fixed one real bug along the way (not just a test
      artifact): bash 5.2 raises "bad array subscript" on an empty-string associative-array key, which real
      bajaui's `module-info.class` (no package) hits — covered by a dedicated regression test (T24e) and fixed by
      not using an associative array for package dedup. Evidence: docs/decompiler-bakeoff.md's "Resolved (T24)"
      bullet; tools/tests/n5-decompile.bats T24a-T24e. Route: delegated writer (TDD, bats).
- [x] T27 (TDD, bats T27 RED observed: `KeyError: 'v2'` after v1 --force) v1 `write_recon` replaced recon.json
      wholesale and dropped the "v2"/"cons" sub-objects; v1 also never cleared a stale `fallback/`. Fix:
      tools/n5-recon-helper.py carries "v2"/"cons" over only when their `jar_sha256` equals the jar v1 just rebuilt,
      else drops them and lists them in `dropped_stale_variants`; v1 clears `fallback/` before its primary run.
      GREEN: full `bats tools/tests/n5-decompile.bats` 63/63 (EXIT=0), `make test` OK, shellcheck clean.
      Route: inline (script + helper + test).

## Maximum decompile fidelity (user requirement 2026-09-28: "the decompile must be right, no inventions, not tainted; try everything possible")
- [x] T13 Integrity + completeness census [CERT-hw]: 252 recon.json (247 modules + bin/ext) — 0 jar sha256 mismatches vs the
      installed jars, 0 missing jars; 14,894 top-level classes, 0 without a .java (CORRECTED by B117: this counted only top-level classes of the module jars — 24,896 classes in 98 nested LIB-INF jars and 958 classes in 10 out-of-pipeline Tridium jars were never decompiled; orchestrator verified 0 .java under any LIB-INF) (vineflower or fallback); CFR fallback used in
      6 modules (andoverAC256, backup, bajaui, ccn, ffmpeg, opcUaClient); obfuscation heuristic > 0.2 in none.
      docSource originals cover 2,776 of 7,284 top-level classes in docSource-eligible modules. Route: inline.
- [x] T14 (B116, 9523a9e) Lossy-aspects catalog (answers "what else is not faithful"): synthetic javac-25 experiments for every candidate loss
      class + EMPIRICAL differential of Vineflower output vs the 2,776 docSource originals (normalized), taxonomy with counts.
      Output: B116. Route: delegated researcher.
- [x] T15 (16fc6a8; orchestrator re-ran svg+lonWattStopper: 6/6 roundtrip-exact, matches report) Semantic fidelity grader tools/n5-fidelity.py (TDD): recompile each decompiled class against the original jars and
      compare normalized bytecode per method with the shipped class; on mismatch try CFR/Procyon/JADX and keep the first that
      round-trips; grade per class (docsource-original / roundtrip-exact / roundtrip-normalized / compiles-mismatch / no-compile);
      write organized/<mod>/fidelity.json + committed docs/decompile-fidelity-report.md. Route: delegated writer.
- [x] T17 Extraction + native fidelity (B117; Authenticode 20/20 verified by orchestrator; nested-jar count cross-checked independently: 97 jars / 34,507 entries / 24,831 top-level vs B117's 98 / 34,605 / 24,896 — same units, 1-jar scope difference; tool f4e49f8 RDD review-49636f53e9119721 approved, hardening folded into B117-G7): nested/multi-release jars, extracted/ byte-exactness vs jar entries, resources,
      skipped bin/ext jars, N5 obfuscation re-check, jarsigner verification of all module jars, native inventory + every native
      claim classified single-tool vs >= 2 anchored instruments with corroboration run now. Route: delegated researcher.
- Redundancy ladder added to T15 (user: "use everything, no limits"): kit corroborate-java.sh (java-corroboration.v1), krak2
  disassembly cross-check of the normalizer, a 4th independent decompiler (JD-Core/Fernflower, official source + sha256, else
  typed blocked-on-tool), bajadoc member-set cross-check via niagara-help, per-class consensus + `bytecode-only` grade.
- [ ] T18 Logic-recovery method ladder (B118; user: "try a thousand ways"): M1 Vineflower conservative + line-mapped variant,
      M2 bytecode-level analysis (Joern jimple2cpg / SootUp / OPAL call graphs, dispatch resolution), M3 differential execution of
      pure station-independent classes (original vs recompiled), M4 runtime tracing of license-free Tridium CLIs, M5 dataflow
      (CodeQL buildless / Joern), M6 krak2 round-trip, M7 others. Hard limits: no live station, no license bypass. Route: delegated.
- [x] T19 (1791db1; orchestrator verified the Vineflower option-order quirk and the D4 fix `map.remove(Integer.valueOf(this.index))`) Pipeline v2 (from reviewing the user-supplied external niagara_decomp.py + a decompilation survey, 2026-09-28):
      verified defect tools/n5-decompile.sh:199 — Vineflower ran with NO library context (no --add-external for other N5 jars,
      no JDK runtime) and CFR fallback without --extraclasspath. v2 variant → organized/<mod>/vineflower2/ with library context +
      explicit fidelity flags (condy conversion off, rename off, LVT/MethodParameters names); v1 kept for comparison; the grader
      grades both trees. Route: delegated writer (TDD, bats).
      Adopted from the external review: exclude own jar from classpath; argfiles; reference-not-replace fallback; forensic
      Vineflower flags; CFR git-master pinned; meta-decompilation per method (Harrand et al. 2019/2020); japicmp; jqwik; ASM>=9.8;
      JEP 513/456, condy, preview 65535, Kotlin metadata, Maven SHA-1 lookup. REJECTED from it: difflib similarity >= 0.90 as a
      verdict and branch-target erasure ("L") in its normalizer (hides control-flow changes); -parameters (Tridium classes have no
      MethodParameters, verified); re-signing/redistribution steps (out of scope: research is read-only).
- [x] T19b (1e44e71; orchestrator verified 252/252 v2 ok with idempotency_key; RDD pending) Harden v2 after RDD review-4091d4df000d0cae: orchestrator verified a real library-context race —
      5 modules (analyticsLibs, apachePoi, commonsIo, commonsLang, niagaraTest) were rm -rf/unzip-ed 07:20-07:31Z while parallel
      workers scanned */extracted/LIB-INF/*.jar. Fix: immutable libcache prepared serially, idempotency key over the full
      library set, failed runs never cached as success, fallback2/ cleared, stale-extract check, no shell→Python interpolation.
      The first v2 tree is superseded until the clean rerun lands.
- [x] T15b (done in T20) Grader normalizer holes from RDD review-a849ade48da9b9ae, orchestrator-verified with javac 25:
      switch-case regex drops negative keys (javap `-5: 40`) → possible FALSE roundtrip-exact; iinc `2, 3` comma form not
      canonicalized (conservative). Plus: masked module failures, truncated runs cached as complete, no subprocess timeouts,
      harness failures graded as no-compile, tautological test. The 120/186 exact figure is provisional until re-graded.
- [x] T20 (grader fixes T15b included; 46-module/192-class sample on the local mirror: v1 124/192 exact, v2 125/192, 0 worse, 1 better; ldc/ldc_w allowlist moved 1 class; orchestrator diffed v1 before/after: 191/192 unchanged, 0 exact→non-exact, so no false exacts from the negative-switch bug in this sample; decision: vineflower2 = recommended tree, precedence recorded in docs/writer-prompt.md) Per-tree fidelity files (fidelity.<tree>.json) and grade vineflower2 vs vineflower on the identical 43-module sample;
      choose the primary tree by measured round-trip rate, not by text diff. Note: v2's +139% @Override is decompiler inference
      (B116: @Override never survives compilation), not recovered information. Route: delegated writer (TDD).
- [ ] T21 Full-corpus grading run (all ~15k top-level classes, both trees) — closes B116-G1; long run, forecast first. Route: delegated.
- [x] T25 (4745a3e, worktree t25-best-source off feat/n5-wave14@2a08063) Per-class "best available representation"
      index tools/n5-best-source.py (TDD, 17/17 tests GREEN) + `--materialize` browsable relative-symlink tree, so a
      reader never has to re-derive the docs/writer-prompt.md precedence rule by hand. Structural discovery found one
      undocumented split: devkit is the ONLY module with a genuine decompiled `<mod>/lib-inf/<jar>/` subtree; every
      other module's LIB-INF-nested third-party jars are raw, undecompiled files at `extracted/LIB-INF/<jar>.jar`
      (no per-class decompile anywhere in the corpus for those). Real run: 361 populations, 40678 classes — docSource
      2809, upstream 13023, vineflower2 12708, fallback2 273, missing 11865 (28.2%, almost entirely LIB-INF-nested
      third-party classes with no upstream-sources match); 0 vineflower(v1)-preferred picks (matches T20: v1 never
      beats v2 on the 192 classes graded on both trees), 0 bare-fallback picks (fallback2 always already covers
      whatever bare fallback would). Caught and fixed one real bug before reporting numbers: `module-info`/
      `package-info` were being matched across UNRELATED upstream artifacts by filename alone (aaphp's module-info
      matched to org.eclipse.angus:jakarta.mail's) — excluded from the upstream cross-artifact index, regression
      test added. 3 spot-checks by hand (docSource: alarm/AlarmDbConnection; upstream: abstractMqttDriver's
      jackson-annotations JacksonAnnotation, extracted+symlinked correctly; vineflower2: aaphp/BAaPhpDevice) all
      resolved to the right file. Route: delegated writer (TDD).
      **T25 follow-up fix (this commit, TDD, 20/20 tests GREEN)**: orchestrator verification found 146 `devkit`
      classes (131 tridium-niagara-slotomatic-library-5.0.2 + 15 n-templates-5.0.54.9.2) wrongly reported `missing`
      — devkit bundles a raw, undecompiled LIB-INF copy of each jar AND a genuine decompile of the byte-identical
      jar at `organized/devkit/lib-inf/<jar>/`, never cross-linked. Fixed by keying every population's jar by
      sha256 (`extracted/.jar_sha256` where present, else hashing the raw jar directly) and adding a rung-6
      identical-jar fallback, linked by sha256 ONLY, never filename (regression test: same-named/different-bytes
      jars stay unlinked). Added `missing_by_jar` to the summary. Rerun: docSource 2809, upstream 13023,
      vineflower2 12854 (+146), fallback2 273, missing 11719 (-146, 28.8%). `missing_by_jar` top 10, all
      genuinely-undecompiled third-party LIB-INF jars with no upstream match: prosys-opc-ua-sdk-client-server-
      5.7.0-248 (3117), poi-ooxml-lite-5.5.1 (2325), poi-5.5.1 (1226), xmlbeans-5.3.0 (697), kotlin-stdlib-2.3.0
      (687), poi-ooxml-5.5.1 (654), org.eclipse.swt.win32.win32.x86_64-3.134.0 (652), woodstox-core-7.2.0 (539),
      hsqldb-2.7.4 (465), testng-7.12.0 (402). Spot-checked devkit/lib-inf-raw/n-templates-5.0.54.9.2's `Generator`
      class: `best` and materialized symlink both resolve to `organized/devkit/lib-inf/n-templates-5.0.54.9.2/
      vineflower2/.../Generator.java`, real content confirmed.
- [x] T5 (9592b82) Porting guide: the only N5-only claim (`NiagaraSlotProcessor`) was false vs BOTH N4.14 and N4.15 — it is a
      relocation (javax.baja.nre... in bin/ext/nre.jar → niagara.nre... in module niagaraAnnotationProcessors); fixed.
- [ ] T16b Extend lint-block R1/R2/R8 to docs/*.md (the porting guide carried an R8 error the linter could not see). TDD.
- [ ] T16 Make the grade visible where claims are made: lint rule R9 — a [CERT] citation into organized/<mod>/vineflower/<cls>
      whose class grade is compiles-mismatch/no-compile needs a bytecode (javap) or docSource co-citation. Route: after T15.

## Grader report follow-ups (next session, from review-6f1c46518f56b786)
- Render the new grades (timeout, harness-error) in the aggregate report table (0 occurrences in the current sample).
- Reconcile the report's allowlist prose and sample-size note with the current run; restore the krak2 cross-check line.

## Performance (2026-09-28)
- Grading/decompiling read ~440 jars from /mnt/c (WSL 9p) per javac call — the dominant cost. Local mirror created and
  sha256-verified: niagara5-research-localcache/jar-mirror-5.0.0.28/{modules,bin-ext} (+ modules.sha256, bin-ext.sha256).
- Next session: n5-upstream-sources run_recompile_check integration test for the javap-error → None path (review
  review-8361cb6c548924c1 R3-recompile-integration-unproved).

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
