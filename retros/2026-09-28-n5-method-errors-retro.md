<!-- review-status: pending -->
<!-- Marker lifecycle: the maintainer flips 'pending' above to 'applied <date> · kit <sha>' once this retro's proposed deltas are reviewed and applied (or 'dismissed') in the kit; sweep-retros.sh reads this marker to report which retros are still open (METHODOLOGY §18). -->
# Retro — niagara5-research · decompiler-fidelity and method-error audit · 2026-09-28 · Research-SDD self-retrospective

> Run reviewed: the decompiler-fidelity audit (`odd/tasks/decompiler-fidelity-audit.md`, failure classes
> C1–C14, prevention plan R1–R8), blocks B107–B114 and their Corrections sections, and the §14 corrections
> they carry back to B13, B84, B98, B102, B106, B107, and B109. Commits up to `35d9841`.
> Trigger: every-N-blocks, plus a user mandate. The user's words were: "No pueden volver a pasar estos
> mismos errores" and "se tiene que aprender de esto".
> Method: a FRESH-CONTEXT agent read the current kit FIRST (`METHODOLOGY.md` §1, §3, §5, §6, §9, §11, §11b,
> §14, §18, §21; `PROMPT-LOOP.md`; `templates/retro.template.md`). It then read the run's blocks, commits,
> and corrections, and grep-deduped every lesson against METHODOLOGY, PROMPT-LOOP, `toolbelt/*.sh`, and
> `toolbelt/*.md`. This retro is READ-ONLY on the kit: it only PROPOSES changes (METHODOLOGY §18).
> It also cross-checked the two pending retros (`2026-09-28-n5-wave10-11-retro.md`,
> `2026-09-28-n5-wave8-9-retro.md`) so it does not re-propose their deltas.
> Engram journal query: project `niagara5-research` is not in the Engram store, so there were no journal
> entries to consolidate. That result means the project was never registered. It does not show that the
> run produced no insights.

**Framing.** Most lessons in this run are ones the kit ALREADY states as prose. The run broke them anyway:
- Negative-absence discipline (#732) was in the kit, and B98 and B102 still claimed absences they had not proven.
- Golden rule 4 ("preserve external evidence") was in the kit, and 151 paths near `[CERT-hw]`/`[CERT-live]`
  claims still point into `/tmp`.
- GAP NUMBERS ARE ALSO HYPOTHESES was in the kit, and B113 still carried the "4,209 types" figure.
- The resugaring caveat was in B90's own prose, and B84 still repeated the error later.

Under the task's rule, each of these is a NEW delta: **convert the prose rule into a mechanical check.** So
most deltas below are checks, tools, or recorded integration steps, not new doctrine.

## Proposed kit deltas

| # | Proposed change | Target (file · §/section) | Evidence (block / commit / § / transcript ref) | Type | Priority |
|---|---|---|---|---|---|
| 1 | **Java decompilation fidelity matrix.** Add a kit doc with a rule in METHODOLOGY. A claim about source syntax (instanceof pattern, `var`, text block, enhanced for, switch expression, lambda, record/sealed, string concat) that rests on decompiled `.java` is INADMISSIBLE as `[CERT]`. It must cite the bytecode shape the matrix names as distinguishing. Vineflower resugars depending on the class-file major version: the same bytecode renders as classic code at major 52 and as modern syntax at major 69. Agreement between decompilers (for example `corroborate-java.sh` pairwise agreement) is NOT evidence of fidelity. | new `toolbelt/java-decompile-fidelity.v1.md` + `METHODOLOGY.md §5` (next to "Decompiler-string-scrubbed Java") | B90 §90.2 (the rule, stated in prose) → B84 §84.3 `BQudtUnitTag` (a false claim written AFTER B90: N4-4.15 major 52 and N5 major 69 have identical bytecode); feature doc T1/T2 | new | HIGH |
| 2 | **Class-file facts machine-visible in the Java wrappers.** `corroborate-java.sh` would record per-class `major_version`, `has_LocalVariableTable`, and a `resugar_risk` flag in `java-corroboration.v1.json`. `decompile-java.sh` would print a header with the major version and a warning that syntax-level claims need bytecode. Today neither tool records the class version: `corroborate_java.py` contains no `major` or `LocalVariableTable` token. | `toolbelt/corroborate-java.sh`, `corroborate_java.py`, `java-corroboration.v1.md`, `decompile-java.sh` | feature doc T1 (Tridium N5 classes ship with an LVT, major 69; `BNumericWritable` has 62 LVT entries); B84 §84.3 | new (mechanical) | HIGH |
| 3 | **Block linter promoted to the toolbelt.** Add `toolbelt/lint-block.sh`. It would have a generic rule core plus per-target rule packs, with an explicit per-line waiver token that carries a reason. It is enforced (FAIL) on new blocks and report-only (`--audit`) on the legacy corpus. Generic rules: absence claim without a census token; `[CERT-hw]`/`[CERT-live]` evidence only under `/tmp` or a scratchpad; child-gap bullet without `coverage-check:` and `measured-by:` clauses; a cross-block comparison that does not cite the other block's raw artifact. JVM pack: syntax claims, constant inlining, dispatch. Multi-version pack: baseline attribution. It would be wired into `verify-block.sh`, or run next to it inside the self-verify step. | `toolbelt/` (new) + `METHODOLOGY.md §11` (self-verify list) + `PROMPT-LOOP.md` step 5 | target `tools/lint-block.py` R1–R8 (TDD; in progress) derived from C1–C14 | new (mechanical) | HIGH |
| 4 | **Ephemeral evidence fails closed.** `verify-block.sh` would classify a `[CERT*]` citation whose path is under `/tmp`, `/var/tmp`, or a session scratchpad as **FAIL**, not `extern`. The one exception is a beautified-temp view anchored with a `sha256`, per the existing §5 rule. Add a convention `sources/probes/b<N>/` (or the target's `evidence/b<N>/`) with a size cap. The delegated-writer prompt template must require preservation there and must never say "scratch only". | `toolbelt/verify-block.sh` (classification at line ~295) + `METHODOLOGY.md §5` beautified-temp paragraph (narrow its scope) + `PROMPT-LOOP.md` delegation prompt | C11: 151 cited `/tmp` paths, 13 already gone; the driver's own writer prompt told writers to keep evidence in scratch only; this feature's own T1 `[CERT-hw]` evidence sits in `scratchpad/fidelity/` | refinement (mechanical) | HIGH |
| 5 | **Make the orchestrator's central-claim check a recorded integration step.** Before a delegated block is integrated, the driver opens the primary source behind the block's HEADLINE claim and reads its semantics, not just whether the token exists. The driver records one line: `central-claim-check: <claim> → <file:line> → OK \| CORRECTED`. `lint-block.sh` or `verify-state.sh` can check that the line is present. This narrows §11's "trust the self-report; spot-check only when it smells off". That rule's evidence was a gate that re-grepped star tokens and caught nothing. This run's semantic re-read caught every one of the 4 central-claim errors. | `METHODOLOGY.md §11` (trust paragraph) + `PROMPT-LOOP.md` ORCHESTRATED-AUTO driver steps (1)–(3) | B84 §84.3, B98 §98.1 (→ B109 §109.4), B106 §106.8 (→ B108 §108.3), B107 §107.3 (→ B112 §112.1): all 4 were caught by the orchestrator spot-check, and none by any writer self-report | refinement | HIGH |
| 6 | **Multi-version baseline attribution.** A delta claim ("X-only", "new in", "removed in", "N5 replaces N4's …") must name its baseline version. It must be computed against the NEWEST available predecessor, or against every available one, with the version stated. Using an older install when a newer one is on disk is a defect. Lint token: `vs <product> <version>`. | `METHODOLOGY.md §3` usage rules (or §14) + lint multi-version pack | B13 §13.5 said "18 N5-only modules" against N4.14 while N4.15.3.28 was installed; at least 6 of them (cloudLink*, jodaTime) ship in 4.15 (`ls` verified, feature doc C13) | new | HIGH |
| 7 | **Compile-time constant inlining caps dead-constant censuses.** javac inlines `static final` compile-time constants at every use site (JLS §13.1, §13.4.9). A census over bytecode or decompiled code for dead constants, unused fields, or shadow literals therefore cannot tell an inlined reference from a duplicated literal. It stays `[INFER]` unless the author's source (for example `docSource`) is read. The same ceiling applies to .NET `const` and to C/C++ macros. | `METHODOLOGY.md §5` decompiler hazards + fidelity doc (#1) | C14: the B96, B105, and B111 censuses never considered inlining; javac 25 proof: `K.HOST` → an `ldc` literal, which Vineflower renders as a literal (`scratchpad/fidelity/constinline`) | new | MEDIUM |
| 8 | **Resolve dynamic dispatch before you read a call-site argument.** A behavior claim that depends on a call-site argument (null Context, fail-open, a default) must enumerate the overrides of the target method across the static receiver type's subtypes and name the runtime target. Only then can it be `[CERT]`. | `METHODOLOGY.md §9` (next to golden rule 9) + lint JVM pack (R5) | B107 §107.3 read three `getPermissions(null)` sites as fail-open; B112 §112.1 found `BRootHistoryFolder` overrides the method, ignores `cx`, and fetches the real session permissions (`BRootHistoryFolder.java:42-49`) | new | MEDIUM |
| 9 | **Absence claims need a content-based census token, not a filename test.** A negative claim must cite a search by CONTENT (class, package, or resource name inside archives) across ALL declared artifact roots. A test for one guessed jar name, or a look in one directory, does not count. This is the mechanical half of the existing #732 prose rule. It complements pending wave10-11 #2 (the per-target "artifact roots" line), which supplies the root list. | `PROMPT-LOOP.md` NEGATIVE-ABSENCE CLAIM DISCIPLINE + lint generic rule | B98 → B109 §109.4 (`saml.jar` was absent, but `saml-rt/ux/wb.jar` ship); B102 (looked only in Program Files, not the config home) | refinement (mechanical) | MEDIUM |
| 10 | **Cross-block comparisons cite the raw artifact, not the prose.** A §14 comparison or correction against block N must open the raw preserved artifact block N cited (the probe output, a dump), not block N's prose quote of it. | `METHODOLOGY.md §14` + lint generic rule | B106 §106.8 compared against B55 §55.2's prose; B55's own raw probe file already held the warning (B108 §108.3) | new | MEDIUM |
| 11 | **Child-gap bullet grammar at OPEN time.** Every `B<n>-G<m>` bullet carries `coverage-check: <grep/INDEX query → result>`, plus `measured-by: <tool/method>` for any number in the bullet. `check-gap-drift` or `verify-state.sh` flags a missing clause. This is the open-time twin of pending wave10-11 #3, which checks at dispatch time. It also mechanizes GAP NUMBERS ARE ALSO HYPOTHESES. | `METHODOLOGY.md §8b` gap grammar + `PROMPT-LOOP.md` "Child gaps opened" + lint generic rule | C9: B109-G3 was already answered by B4 §4.2 (B114 header); C10: "4,209 types" (a Ghidra count) vs 2,418 typelinks (B113) | refinement (mechanical) | MEDIUM |
| 12 | **Run an experiment before restating a tool-behavior rule.** Any rule about what a compiler, decompiler, or packer preserves must link a reproducible minimal experiment. Ship one as `toolbelt/java-fidelity-experiment.sh`: it compiles idiom pairs (old vs new) with the installed javac, with and without `-g`, diffs `javap -c -p -l`, and regenerates the #1 matrix for each JDK version. | `METHODOLOGY.md §1` (sibling of "Mechanism before observation") + `toolbelt/` (new) + `toolbelt/tests/` | The orchestrator twice restated the rule wrongly in chat ("confirm with javap" was incomplete; "enhanced for is indistinguishable" was wrong) until the javac experiment settled it (feature doc T1) | new | MEDIUM |
| 13 | **A §18 rule: a lesson that recurs after being written as prose must come back as a mechanical delta.** When a retro lesson is "already covered" as prose AND the run violated it, the retro must propose a check, tool, or recorded step, not more prose. The maintainer's review marks such rows `mechanical`. | `METHODOLOGY.md §18` (dedupe clause, "already covered") | B90 → B84 (resugaring); #732 → B98/B102 (absence); golden rule 4 → C11 (`/tmp`); the rows above | new | MEDIUM |
| 14 | **Delivery without branch protection.** When the target repo cannot enforce required checks (for example a private repo on a free plan), the driver's merge step MUST wait for green CI (`gh pr checks <n> --watch`) and record the result. The in-repo pre-commit hook is the local backstop. | `PROMPT-LOOP.md` delivery/integration step | Feature doc T9: no branch protection is available on this plan | new | LOW |

Rationale, one line per delta:

- **#1** — This is kit-general for any JVM decompile target. The prose rule already failed once inside this corpus. A kit doc that every writer is pointed to costs one page and closes the whole C1 class.
- **#2** — This makes #1 checkable. A writer who sees `major=69 resugar_risk=true` in the wrapper output cannot claim N5 adopted a syntax feature without seeing the warning. It adds a few lines to an existing adapter.
- **#3** — This is the core of the user's "must not happen again". It turns six prose rules into one fail-closed check. The target is already building it test-first, so the kit can absorb it rather than write it from scratch.
- **#4** — Evidence has already decayed: 13 of 151 paths are gone. The kit's own §5 beautified-temp paragraph sanctions scratchpad citations, and writers generalized that to probe outputs. This change narrows the rule and makes the gate fail closed.
- **#5** — This is the only detection mechanism that worked in this run. §11's trust doctrine rests on one run where a token re-grep caught nothing. This run's semantic re-read caught 4 of 4. Recording the check costs one line per block.
- **#6** — This is kit-general for any target with more than one installed predecessor version. The baseline was wrong for 6 or more of the 18 "N5-only" modules, and that headline number was wrong in a foundation block.
- **#7** — This is a quiet ceiling on a whole census family (three blocks). No kit text mentions constant inlining. It costs one paragraph plus a lint trigger on words like "dead constant" and "shadow literal".
- **#8** — This is kit-general for OO targets, and it touches a security verdict: a false fail-open went into a permission census. Enumerating overrides is cheap with CodeGraph or grep.
- **#9** — The prose rule exists and was broken twice. The fix is a mechanical token, plus the root list from wave10-11 #2. The two should land as one issue.
- **#10** — This is a small rule, and it caught a real error: a correction was made against a block's prose while that block's raw file already held the answer.
- **#11** — It costs two clauses per bullet. It prevents opening an already-answered gap (C9) and a number with no method behind it (C10) at the moment the gap is created, which is earlier than wave10-11 #3 can catch them.
- **#12** — Recalled rules were wrong twice in one session, and the experiment took minutes. A regenerating script also keeps #1's matrix honest across JDK versions.
- **#13** — This is a meta-fix for the pattern that produced this retro. Without it, the next retro will again list these lessons as "already covered" and propose nothing.
- **#14** — This is a narrow operational rule. It matters only where the platform cannot enforce checks, but it is exactly this target's situation.

## Already covered (dedupe — proof the retro read the kit first)

- String-literal scrubbing by the decompiler, where `javap`/bytecode is authoritative → `METHODOLOGY.md §5` "Decompiler-string-scrubbed Java". This covers STRINGS only, not syntax resugaring, which is why #1 is new.
- Negative-existence claims need the exact artifact opened → `METHODOLOGY.md §3` usage rules; `PROMPT-LOOP.md` NEGATIVE-ABSENCE CLAIM DISCIPLINE (#732); overlay-vs-base absence (§8); a sub-agent's absence inherits its search scope. These are prose, and they were violated (B98, B102) → #9.
- Preserve external evidence → golden rule 4 (§9); block-evidence artifacts are gate-enforced (§11). That gate covers only `B<N>-*` artifact NAMES; absolute `/tmp` paths still classify as `extern` → #4.
- Numbers in gap text are hypotheses → `PROMPT-LOOP.md` GAP NUMBERS ARE ALSO HYPOTHESES and SWEEP NUMERIC LABELING. These are prose, and they were violated (B113) → #11.
- PRIOR COVERAGE CHECK per gap, and a focus-distinctness check at focus open → `PROMPT-LOOP.md` NORMAL CYCLE step 3 and BOOTSTRAP. These fire at investigation time, not at gap-open time → #11 (and pending wave10-11 #3 at dispatch).
- VERIFY BEFORE ACTING on a sub-agent's report (resolve the key citations) → `PROMPT-LOOP.md` step 3. It is prose, unrecorded, and in tension with §11's trust rule → #5.
- Numeric constants are `[CERT]` only with a fresh grep → `METHODOLOGY.md §3`. This is related to #7 but does not address inlining.
- "A name is not a kind" (golden rule 9) → it covers declarations, not dispatch targets → #8 is new.
- Already proposed in pending retros, not re-proposed here: install-root list per target (wave10-11 #2, referenced by #9); already-covered pre-check at dispatch (wave10-11 #3, referenced by #11); backlog row-drift checker (wave10-11 #1 / wave8-9 #1; the target's `check-gap-drift.py` is its local form); census tree-shape scope (wave10-11 #4).

## Anti-patterns observed

- A rule stated in prose inside a block (B90) was treated as learned; a later block (B84) repeated the error → #1, #2, #13.
- The driver's own writer prompt told writers to keep evidence in scratch only, and this audit's own T1 `[CERT-hw]` evidence also lives in `scratchpad/fidelity/` → #4.
- The orchestrator restated a tool-behavior rule from memory, and got it wrong twice → #12.
- A headline census used an older baseline while a newer install was on disk (B13) → #6.
- A call-site `null` was read as fail-open without looking at the override (B107) → #8.
- A comparison was made against another block's prose instead of its raw file (B106) → #10.
- A gap was opened that was already answered (B109-G3), and a figure was copied without its method (B113) → #11.

## Tools built, adapted, or outgrown

| # | CREATED (path · purpose) | ADAPTED (kit tool · what the kit version could not express) | OUTGREW (kit tool · why stopped) | ORACLE (tool · what it SEEs, not recomputes) | VERDICT (decision · evidence) |
|---|---|---|---|---|---|
| T1 | `niagara5-research/tools/lint-block.py` · rules R1–R8 over block prose (syntax claims, absence census, `/tmp` evidence, child-gap clauses, dispatch, raw-vs-prose, constant inlining, baseline), TDD fixtures, waivers | `toolbelt/verify-block.sh` · it counts markers and resolves citations, but it cannot express claim-shape rules (what KIND of evidence a claim type requires) | — | — | `promote` · generic core + JVM/multi-version packs as `toolbelt/lint-block.sh` (#3); in progress in the target, so absorb once its fixtures are green |
| T2 | fidelity experiment (javac 25 idiom pairs, `javap -c -p [-l]` diff, `-g` on/off) · decides which source features survive into bytecode | `toolbelt/decompile-java.sh --javap` · it gives one class's bytecode, with no paired old-vs-new comparison | — | fidelity experiment · it SEEs what the compiler actually emits for each idiom rather than recalling a rule; it refuted two orchestrator statements | `promote` as `toolbelt/java-fidelity-experiment.sh` + fixtures (#12); currently scratch-only, which is itself a C11 instance |
| T3 | `niagara5-research/tools/githooks/pre-commit` + CI workflow (planned T9) · runs lint + gap-drift + verify-block on staged blocks | `toolbelt/sweep-*-hook.sh` · those run on the kit, not on target corpora | — | — | `keep-local` for now · the wiring is target-repo policy; the kit could ship a template later under `templates/` |
| T4 | `niagara5-research/tools/check-gap-drift.py` (pre-existing) · compares backlog rows against the block bullets | — | — | — | already proposed for promotion by wave10-11 #1; not re-counted here |

## Metrics

- **Blocks reviewed**: 8 (B107–B114), plus the corrected sites in B13, B84, B90, B96, B98, B102, B105, B106, B111 · **§14 cross-block corrections in this run**: 5 central-claim corrections (B84 §84.3, B98 §98.1, B106 §106.8, B107 §107.3, B13 §13.5) and 2 method ceilings (C9, C14) · **Rules skipped in practice**: 4 prose rules (resugaring caveat, #732 absence, golden rule 4, GAP NUMBERS)
- **Deltas proposed (new)**: 14 (HIGH 6 · MEDIUM 7 · LOW 1) · **Already-covered lessons**: 8, plus 4 pending-retro references

## Honest verdict

This run surfaced real kit deltas. They are not mainly new doctrine: the kit already stated four of the
violated rules as prose. What the run showed is that **prose in a block or in METHODOLOGY does not stop a
fresh writer**, and that the one mechanism that caught errors was the orchestrator re-reading the primary
source for each block's headline claim. The highest-value deltas are therefore mechanical: #2, #3, #4, and
#5 (the recorded central-claim check).

The genuinely new doctrine covers:
- Syntax resugaring as a fidelity ceiling (#1).
- Compile-time constant inlining (#7).
- Dynamic-dispatch resolution (#8).
- Multi-version baseline attribution (#6).
- Raw-vs-prose comparison (#10).

Portability:
- **Kit-general for any JVM target:** #1, #2, #7 (with .NET and C analogs), and #12.
- **Kit-general for any OO target:** #8.
- **Kit-general for any target with more than one installed predecessor version:** #6.
- **Fully general:** #3–#5, #9–#11, #13, and #14.
- **Niagara-specific:** only the evidence (Tridium class versions, install layout). None of the rules depends on Niagara.
