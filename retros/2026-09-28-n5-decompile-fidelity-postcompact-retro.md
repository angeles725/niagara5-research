<!-- review-status: pending -->
<!-- Marker lifecycle: the maintainer flips 'pending' above to 'applied <date> · kit <sha>' once this retro's proposed deltas are reviewed and applied (or 'dismissed') in the kit; sweep-retros.sh reads this marker to report which retros are still open (METHODOLOGY §18). -->
# Retro — niagara5-research · decompile-fidelity (post-compact) · 2026-09-28 · Research-SDD self-retrospective

> Run reviewed: decompile-fidelity work after the context compact — commits 8cd9467 (T23), 2a08063 (bakeoff
> campaign numbers), the T24 bajaui investigation (bisect, option trials), RDD lineage
> review-83022868fd33530e, and three delegated writers (T24, T18b, T25). Trigger: Stop hook (retro-gate) plus
> the §18 "run is not over until the retro exists" rule.
> Method: the orchestrator read the kit's PROMPT-LOOP.md and METHODOLOGY.md sections on delegation, pkill,
> worktrees and Engram topic keys FIRST (grep-located: PROMPT-LOOP.md:1520, METHODOLOGY.md:2902, :3283), then this
> run's commits and transcript. READ-ONLY on the kit — this report only PROPOSES (METHODOLOGY §18).

## Proposed kit deltas

| # | Proposed change | Target (file · §/section) | Evidence (block / commit / § / transcript ref) | Type | Priority |
|---|---|---|---|---|---|
| 1 | When the research target repo differs from the session's working directory, never rely on the harness `isolation: worktree` option for delegated writers: it creates the worktree from the session cwd's repo. Create the worktree explicitly with `git -C <target> worktree add <target>-worktrees/<name> <branch>` and pass that path to the writer. | `PROMPT-LOOP.md` DELEGATION + MODEL TIER · `METHODOLOGY.md` concurrent-lane rule (~line 2902) | T18b/T25 writers launched with `isolation: worktree` from cwd `niagara-research`; the worktrees appeared under `niagara-research/.claude/worktrees/agent-*` (a checkout of the wrong repo) while the target was `niagara5-research`; the orchestrator had to send corrective messages mid-run | new | HIGH |
| 2 | `retro-gate.sh` / `lib/block-files.sh` should exclude `.claude/worktrees/**` (and other nested git worktrees) from the "changed research file" scan. | `toolbelt/retro-gate.sh` · `toolbelt/lib/block-files.sh` | `find . -newer retros/<newest> -name '*.md'` in niagara-research listed only `.claude/worktrees/agent-a79beab48b55eface/niagara-mental-model-bloque*.md` copies; the Stop hook blocked on them although no niagara-research block changed | refinement | MEDIUM |
| 3 | A tool pipeline with a whole-artifact budget (decompile, parse, extract) must, on timeout, isolate the offending unit (bisect by package, then by class) and degrade only that unit. A whole-artifact fallback must never report a top-level `status: ok`. The summary must carry the degraded primary status. | `METHODOLOGY.md §6` research tools (Java decompile row) · `toolbelt/tool-registry.md` | bajaui (832 classes): Vineflower 1.12.0 timed out in v1/v2/cons, so 566/566 top-level sources were CFR while `recon.json` v2/cons said `status: ok`. The cause was ONE class (`NSS2SelectionResult`, the only method-local record in the corpus). With `--excluded-classes`: 14 s, 565/566 Vineflower. Found only by accident during a line-mapping spot check | new | HIGH |

For each delta above, one line of rationale (WHY it matters, what it costs, expected impact):

- **#1** — A writer in the wrong repo either fails confusingly or, worse, falls back to editing the shared main checkout and collides with a concurrent writer. The fix costs one explicit `git -C` call and prevents cross-writer corruption.
- **#2** — False Stop-hook blocks train operators to ignore the gate. The fix is a one-line path exclusion.
- **#3** — A single pathological input silently downgraded a whole core module across every tree for the entire session. Isolation is cheap: 60 package runs plus 11 class runs took under 5 minutes. Without it, the "0 failures" headline hid a 100%-CFR module.

## Already covered (dedupe — proof the retro read the kit first)

- `pkill -f` matched the wrapper shell and killed my own command twice (exit 144) → already covered by `PROMPT-LOOP.md:1520` "PKILL -F WRAPPER-SHELL MATCH". This is a rule skipped in practice, not a missing rule.
- Engram `mem_save` with a reused `topic_key` replaced the previous observation (same id 10219), losing content until I re-saved a merged version → already covered by `METHODOLOGY.md:3283` (topic_key is an UPSERT). Also a rule skipped in practice.
- I proposed "reconstruct @NiagaraProperty annotations" as an improvement without checking. Vineflower already recovers them (18/18 in BNumericWritable; they are in RuntimeVisible/InvisibleAnnotations) → already covered by the verify-before-claim rule (METHODOLOGY §1/§11 SOURCE-BEFORE-AGENT). I retracted it to the user with the evidence.
- Vineflower silently ignores options placed after `-e` → already encoded in the target's own tool header and B118. Not a kit concern.

## Anti-patterns observed (optional)

- Treating a typed per-variant field (`primary_status: timeout`) as sufficient while the top-level `status: ok` summarized it away → #3.
- Delegating with a harness isolation primitive whose repo binding was not checked → #1.
- In the zsh-wrapped Bash tool, `eval "arr=(...)"` plus `arr[$((n-1))]` indexed the wrong element because zsh arrays are 1-based. Caught by printing the element before use; fixed by running the array logic under `bash -c`. This is target-environment trivia, so it gets no delta.

## Tools built, adapted, or outgrown

| # | CREATED (path · purpose) | ADAPTED (kit tool · what the kit version could not express) | OUTGREW (kit tool · why stopped) | ORACLE (tool · what it SEEs, not recomputes) | VERDICT (decision · evidence) |
|---|---|---|---|---|---|
| T1 | scratchpad `bisect-pkg.sh` / `bisect-cls.sh` · per-package then per-class Vineflower runs under a budget, to find the unit that hangs | — | — | — | `absorb` into `tools/n5-decompile.sh` (T24 writer is automating it); generic idea proposed as delta #3 |
| T2 | scratchpad `tryopt.sh` · runs one Vineflower option per trial on the hung class | — | — | — | `no` · throwaway; its findings are recorded in the ODD doc and Engram |
| T3 | `/tmp/linecheck-t22.py` (adapted from `evidence/b118/linecheck.py`) · compares `// N` line markers with docSource original lines | — | — | `linecheck` · SEES whether the decompiled statement sits on the original source line by reading the original file (624/624) | `keep-local` · already versioned as evidence/b118/linecheck.py |

## Metrics

- **Blocks reviewed**: 0 new blocks (tool/pipeline work; B116-B118 unchanged) · **§14 cross-block corrections in this run**: 0 · **Rules skipped in practice**: 3 (pkill, topic_key upsert, verify-before-claim)
- **Deltas proposed (new)**: 3 · **Already-covered lessons**: 4

## Honest verdict

This run surfaced two genuinely new kit gaps:
- Worktree isolation is bound to the session cwd repo in cross-repo runs (#1).
- A whole-artifact tool fallback can mask a single-unit failure behind an `ok` summary (#3).

It also surfaced one retro-gate false positive (#2). The other three mistakes were already-encoded rules that I skipped. They show discipline slips, not missing kit rules.
