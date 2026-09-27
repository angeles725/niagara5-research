<!-- review-status: pending -->
<!-- Marker lifecycle: the maintainer flips 'pending' above to 'applied <date> · kit <sha>' once this retro's proposed deltas are reviewed and applied (or 'dismissed') in the kit; sweep-retros.sh reads this marker to report which retros are still open (METHODOLOGY §18). -->
# Retro — niagara5-research · N5 frontier bootstrap · 2026-09-27 · Research-SDD self-retrospective

> Run reviewed: N5 frontier bootstrap — corpus scaffold, tool porting (10 commits), 11 blocks
> (B1-B10, B14), one PoC build, one partial decompiler bake-off. Trigger: session close
> (`odd/tasks/n5-research-bootstrap.md` T8) — first-ever run of this target, no prior retro exists.
> Method: a FRESH-CONTEXT agent read the current kit (`METHODOLOGY.md §18`, then `templates/retro.template.md`)
> FIRST, then the run's evidence (`RESEARCH-STATE.md`, `INDEX.md`, `git log`, `odd/tasks/n5-research-bootstrap.md`,
> `tools/README.md`, `docs/decompiler-bakeoff.md`), then proposes kit deltas. READ-ONLY on the kit — this
> report only PROPOSES; kit changes are human-reviewed and human-committed (METHODOLOGY §18).

## Proposed kit deltas

> Only genuinely NEW items — anything the kit already encodes is listed under "Already covered", not here.

| # | Proposed change | Target (file · §/section) | Evidence (block / commit / § / transcript ref) | Type | Priority |
|---|---|---|---|---|---|
| 1 | Add a rule: a machine-generated state-file header/legend comment must never contain the literal text of a real section heading it precedes (e.g. `## Blocked gaps`) — a naive `s.index('## Blocked gaps')` in a scripted state editor matches the COMMENT occurrence first and mangles the file. Use a paraphrase in header prose, or require heading-anchor scripts to match only a line starting with `^## `. | `METHODOLOGY.md` (research-state.v1 envelope section) / `research-sdd-init.sh` scaffold template | `RESEARCH-STATE.md` header comment: `blocked_open (## Blocked gaps entries)` appears verbatim before the real `## Blocked gaps` heading later in the same file (orchestrator-reported: this footgun bit a scripted edit this run) | new | MEDIUM |
| 2 | Add an explicit engram rule: use ONE `topic_key` per finding — never reuse a `topic_key` across two distinct findings in the same session, because `mem_save` upserts on that key and the second write silently overwrites the first with no conflict signal. | `METHODOLOGY.md` (engram mirroring convention) | orchestrator-reported: two distinct findings this session shared one `topic_key`; the second silently overwrote the first | new | HIGH |
| 3 | Document that `gentle-ai review` preflight (RDD) can refuse when the checkout has OTHER concurrent agents' untracked files present (parallel block delegation leaves many uncommitted per-agent files mid-run) — recommend reviewing from a clean detached worktree, or declaring/stashing the untracked inventory before START, rather than treating the refusal as a kit-side bug. | `METHODOLOGY.md` §18 Review Execution Contract (RDD section) | orchestrator-reported: RDD START refused while other agents' untracked files existed in this checkout; workaround used = clean detached worktree | new | MEDIUM |
| 4 | Add default guidance to pre-split large tooling-bootstrap changes into one commit per ported/created tool BEFORE attempting RDD review, rather than committing one large blob and hitting `lens_context_budget_exceeded`. This run's own tool-bootstrap history (10 separate `feat(tools):` commits, one per tool) is the pattern that should be the DEFAULT, not a post-refusal recovery. | `PROMPT-LOOP.md` (tool-acquisition / tool-porting step) | orchestrator-reported: a single ~7,182-line tooling commit hit `lens_context_budget_exceeded` and had to be split into 9 chained commits; `git log` in this corpus shows exactly this granularity (`99f8adb…7a4fc5a`, 10 tool-port commits) | new | MEDIUM |
| 5 | Add a directory-ownership convention for concurrent per-block/per-tool agents: each parallel agent writes only inside a path it exclusively owns for the run; a shared path (e.g. a common `tools/decompilers/` download directory) needs ONE designated owner agent, and any other agent needing a file placed there hands off to the owner instead of writing directly — avoids a runtime permission denial ("Modify Shared Resources"). | `PROMPT-LOOP.md` (concurrent block-writer delegation section) | `tools/README.md` japicmp row, "OPEN ITEM": this session's own attempt to place `japicmp-0.26.2-jar-with-dependencies.jar` under `tools/decompilers/` was denied because that directory was concurrently owned by the decompiler-bakeoff agent | new | MEDIUM |
| 6 | Codify the "placeholder marker" resumability pattern for a long single-writer artifact at risk of a forced mid-run handback: seed the doc with named HTML-comment placeholders (e.g. `<!-- RECOMPILE_TABLE -->`) for sections not yet filled, so a resumed session has an unambiguous fill-in point instead of re-deriving scope from scratch. | `METHODOLOGY.md` (near §18's "improvised technique" intake, or a new tool-authoring note) | `docs/decompiler-bakeoff.md`: `<!-- RECOMPILE_TABLE -->`, `<!-- RECOMPILE_NOTES -->`, `<!-- FEATURE_TABLE -->`, `<!-- FIDELITY_NOTES -->`, `<!-- RECOMMENDATION -->` remain unfilled after the bake-off agent was cut off mid-run by a forced handback (orchestrator-reported) and resumed | new | LOW |
| 7 | Add a WSL operating-environment note: running `javac`/decompile tool invocations directly against a Windows-mounted install tree (`/mnt/c/...`, 9p filesystem) is far slower per invocation than against a local copy (orchestrator-reported: ~30s vs ~1.8s) — recommend copying the target module set locally before any tight-loop verification pass (per-class recompile checks). | `METHODOLOGY.md` / `PROMPT-LOOP.md` (WSL operating-environment notes) | orchestrator-reported (session fact); `docs/decompiler-bakeoff.md`'s reproduction commands run directly against `MODDIR=/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` | new | LOW |
| 8 | Record, as a validated data point, the concurrency ceiling actually exercised safely for parallel block-writer delegation this run: up to ~8 concurrent sonnet agents, each writing exactly one block file, zero write collisions across 11 blocks in one session. | `METHODOLOGY.md` (block-delegation / concurrency guidance) | orchestrator-reported; `RESEARCH-STATE.md` iteration history rows 1-11, all same-day, one block file per row, no collision noted | new | LOW |
| 9 | Document that the kit repo's (`sdd-investigacion`) PR checks require an approved issue + type label, and that `gh pr edit --add-label` fails there under the GitHub Projects-classic deprecation — use `gh api repos/<owner>/<repo>/issues/<n>/labels` (REST) instead. | `toolbelt/stage-retro-issues.sh` docstring / `METHODOLOGY.md` §18 backlog-first section | orchestrator-reported | new | MEDIUM |

For each delta above, one line of rationale (WHY it matters, what it costs, expected impact):

- **#1** — a scripted state edit that silently corrupts `RESEARCH-STATE.md` is worse than a crash; cheap fix (anchor on `^## `), high blast radius if left unfixed across every future target's state-edit scripts.
- **#2** — silent data loss in memory is the worst failure mode for a persistence layer; the fix is a one-line discipline rule, the cost of NOT having it is an undetected lost finding.
- **#3** — without this note, a future parallel-block session hits the same RDD refusal and burns time diagnosing it as a bug instead of applying the known workaround.
- **#4** — turns a reactive recovery (split after refusal) into the default authoring pattern, saving a round-trip through RDD every time a tooling bootstrap is large.
- **#5** — a permission denial mid-run on a shared directory stalls a parallel agent; a named-owner convention prevents it deterministically instead of by luck of scheduling.
- **#6** — cheap technique (a handful of HTML comments) that converts an interrupted long-running writer task from "re-derive scope" to "read the next empty marker."
- **#7** — a 15-17x per-invocation slowdown compounds badly across a 247-module, multi-decompiler bake-off; flagging it early saves the next WSL-based target from repeating the same slow loop.
- **#8** — an unquantified "delegate in parallel" instruction is harder to trust than a concrete, evidence-backed ceiling; this gives the next campaign a number to plan against.
- **#9** — the backlog-first mechanism depends on labeling working; a silent `gh pr edit` failure would otherwise look like a kit bug rather than a known GitHub API deprecation with a known REST workaround.

## Already covered (dedupe — proof the retro read the kit first)

- Refuting an unproven premise via one scoped, evidence-backed correction ("subscription licensing is new in N5" → refuted; it existed in N4 per B6) → already covered by the ODD/METHODOLOGY assumption-challenge convention and the kit's own §14 cross-block-correction mechanism; this run used it exactly as designed (`RESEARCH-STATE.md` N5-G8 row).
- Tagging a gap as blocked with an explicit "needs: … · tried: …" annotation when it depends on infrastructure that does not exist yet (a live N5 station) → already covered by the kit's own `## Blocked gaps` template convention; this run populated it correctly for 3 gaps (B9-G1, B8-G5, B1-G1).
- Promoting child gaps straight into the backlog as soon as a block surfaces them, without a separate triage pass → already covered by the target's heavy/frontier-mode convention (per the user's explicit instruction and prior established practice across other targets); this run followed it consistently (every block row in the iteration history lists "N new — B*-G1..Gn in block").

## Anti-patterns observed (optional)

- A single oversized tooling commit was attempted before splitting, triggering an avoidable RDD refusal → the delta above that would prevent it: #4.
- A scripted state-file edit matched the wrong text due to a header comment echoing a real heading → the delta above that would prevent it: #1.
- Two distinct engram findings landed under one `topic_key`, losing the first silently → the delta above that would prevent it: #2.

## Tools built, adapted, or outgrown

| # | CREATED (path · purpose) | ADAPTED (kit tool · what the kit version could not express) | OUTGREW (kit tool · why stopped) | ORACLE (tool · what it SEEs, not recomputes) | VERDICT (decision · evidence) |
|---|---|---|---|---|---|
| T1 | `tools/n5-decompile.sh` · Java-25-aware decompile pipeline: Vineflower primary under a bounded per-jar timeout, CFR whole-module fallback on timeout/error, per-class CFR fallback when Vineflower flags specific classes | — | — | — | `promote` · not N5-specific — any modern-bytecode (Java 17+) decompile job needs a timeout+fallback pattern; evidence: `docs/decompiler-bakeoff.md` — Vineflower 1.12.0 hangs indefinitely (zero output at 600s) on `bajaui.jar`'s `com.tridium.ui.*` subtree while CFR decompiles the same jar cleanly in ~11s |
| T2 | `tools/lib/moduleinfo.py` · pure-Python JPMS `module-info.class` parser (constant pool + `Module` attribute, JVMS §4.4/§4.7.25) | — | — | — | `promote` · not N5-specific — any JPMS-module research target needs this without shelling out to `javap`/a JVM; `searched` clause recorded (nothing off-the-shelf found) and cross-checked byte-for-byte against `javap -p` on a real N5 module (`tools/README.md`, `tools/tests/test_moduleinfo.py`) |
| T3 | — | — | — | — | `absorb` · Vineflower 1.12.0 (`tools/decompilers/vineflower-1.12.0.jar`) into `toolbelt/tool-registry.md` as the default primary decompiler for major-version-69+ (Java 17-25) bytecode — best language-feature fidelity (records, pattern-matching switch) per `docs/decompiler-bakeoff.md` |
| T4 | — | — | — | — | `absorb` · CFR 0.152 (`tools/decompilers/cfr-0.152.jar`) into `toolbelt/tool-registry.md` as the required fallback decompiler paired with T3 — robust on the one jar (`bajaui.jar`) where Vineflower hangs |
| T5 | — | — | — | — | `absorb` · Procyon 0.6.0 (`tools/decompilers/procyon-decompiler-0.6.0.jar`) into `toolbelt/tool-registry.md` as a third-opinion decompiler (works on major-69 bytecode, unmaintained since 2021, does not resugar records/sealed classes) |
| T6 | — | — | — | — | `absorb` · JADX 1.5.6 (`tools/decompilers/jadx-1.5.6.zip`) into `toolbelt/tool-registry.md` as a second fallback candidate — fastest/most robust of the four tools tested in this bake-off, no crashes, full class coverage |
| T7 | — | — | — | — | `absorb` · Krakatau v2 (`krak2`, via cargo) into `toolbelt/tool-registry.md` as the absolute-last-resort disassembler (lossless `.j` bytecode-assembly text) for a class every source decompiler fails on |
| T8 | — | — | — | — | `absorb` · japicmp 0.26.2 (`tools/decompilers/japicmp-0.26.2-jar-with-dependencies.jar`) into `toolbelt/tool-registry.md` as the bytecode-level Java API-compatibility checker for cross-major-version diffs; verified working against Java 25 classfiles (1595 classes, N4 vs N5 `baja.jar`, exit 0) |
| T9 | — | — | — | — | `absorb` · `openjdk@25` (brew) into `toolbelt/tool-registry.md` as the minimum JDK needed to `javap`/`jdeps`/`jdeprscan` class major version 69 bytecode without external tooling |

## Metrics

- **Blocks reviewed**: 11 (B1-B10, B14)  ·  **§14 cross-block corrections in this run**: 1 (B6 licensing premise refuted)  ·  **Rules skipped in practice**: 0 known; T2 (decompiler bake-off, `docs/decompiler-bakeoff.md`) was left partially filled (RECOMPILE_TABLE / FEATURE_TABLE / FIDELITY_NOTES / RECOMMENDATION still empty placeholders) after a forced mid-run handback — resumed, not skipped, and still open at session close.
- **Deltas proposed (new)**: 9  ·  **Already-covered lessons**: 3

## Honest verdict

This run genuinely surfaced new lessons the kit does not yet encode — it is the FIRST-EVER run of this
target, executed under real concurrency (parallel block delegation, a concurrent decompiler-bakeoff agent,
tool porting) and real RDD/engram/GitHub integration friction that a single-agent, single-focus run would
not have hit. The state-file header-comment footgun (#1), the engram `topic_key` upsert overwrite (#2), the
RDD untracked-inventory preflight refusal (#3), the pre-split tooling-commit guidance (#4), the shared-directory
permission denial under concurrency (#5), and the `gh pr edit` label-API deprecation (#9) are all concrete,
evidence-backed operational footguns not previously documented in `METHODOLOGY.md` or `PROMPT-LOOP.md`. The
placeholder-marker resumability technique (#6) and the WSL 9p performance note (#7) are smaller but real
improvised wins worth codifying. Three lessons (premise refutation, blocked-gap tagging, child-gap promotion)
ARE already covered by existing kit conventions and are listed above, not re-proposed.
