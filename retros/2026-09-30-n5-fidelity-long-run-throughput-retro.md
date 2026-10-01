<!-- review-status: pending -->
<!-- Marker lifecycle: the maintainer flips 'pending' above to 'applied <date> · kit <sha>' once this retro's proposed deltas are reviewed and applied (or 'dismissed') in the kit; sweep-retros.sh reads this marker to report which retros are still open (METHODOLOGY §18). -->
# Retro — niagara5-research · n5 decompile-fidelity long runs (C2d / C2a-G1 / C1c design) · 2026-09-30 · Research-SDD self-retrospective

> Run reviewed: the Niagara 5 decompile-fidelity grading runs in `niagara5-research` (feature doc
> `odd/tasks/n5-fidelity-completion.md`, tasks C2d, C2a-G1 and the C1c design, commits 3bb6d9c..00c818c).
> Trigger: operator question ("¿esto nos puede servir como retro/delta?") after the C1c scope extension.
> Method: the coordinator read the current kit first (METHODOLOGY §11a, §18; PROMPT-LOOP parallel/concurrency
> rules; `toolbelt/WINDOWS-SSH-PROBES.md` checkpoint section) and then the run evidence. READ-ONLY on the kit —
> this report only PROPOSES (METHODOLOGY §18).

## What happened
Grading 3,997 third-party classes (C2d) took 10.6 h. The machine ran 25 JVMs on 16 hardware threads / 31 GB
(load 23-30) because the C2d grader, the C4 splice writer and the C2a-G1 stages ran at the same time. jxbrowser
alone took ~8 h, dominated by one fresh JVM per class for the CFR/Procyon fallback decompilers. The operator asked
twice how to make it faster "without sacrificing quality", and then how never to restart from zero.
Reading `tools/n5-fidelity.py` showed three different levels of reuse in the same pipeline:
the decompile step is content-addressed per jar (`n5-decompile.sh`, sha256 marker + idempotency key), the
canonical regrade is checkpointed every 10 classes (`REGRADE_CHECKPOINT_EVERY`, `n5-fidelity.py:2273`), but the
main grade is all-or-nothing PER MODULE (`is_module_up_to_date`, `n5-fidelity.py:2237`: jar sha256 + schema).
So one changed class, a schema bump, or an interrupted run regrades the whole module. The fix was designed as
C1c: a per-class key (decompiled source + shipped class bytes + nested bytes + toolchain identity) whose store is
written durably per class, so it is at the same time a cache and a resume checkpoint. NOT yet implemented; the
speedups below are measured costs plus a design, not measured gains.

## Proposed kit deltas

| # | Proposed change | Target (file · §/section) | Evidence (block / commit / § / transcript ref) | Type | Priority |
|---|---|---|---|---|---|
| 1 | LONG BATCH RUNS ARE CONTENT-ADDRESSED PER UNIT. Any run over a population (classes, files, records) that takes more than ~30 min keys each unit's result on the sha256 of ALL its inputs plus the toolchain identity (tool versions, schema version, flags), and reuses a stored result only on an exact key match; a forced bypass flag stays available. A per-container key (per module/jar) is not enough: one changed unit regrades the whole container | `METHODOLOGY.md §11a` (new heuristic) | `n5-fidelity.py:2237` module-level up-to-date vs `n5-decompile.sh` per-jar sha256; C1c design in feature doc (036ca14, 00c818c) | new | HIGH |
| 2 | THE CACHE IS THE CHECKPOINT, AND ITS PROOF IS EQUIVALENCE. Write each unit's result durably as soon as it is produced (append + atomic rename/fsync per batch) so an interrupted run resumes at the next missing unit. Gate it with an equivalence test: interrupt mid-container, rerun, and require output byte-identical to an uninterrupted run; plus one test per key component (changing it must force recomputation). Never claim a speedup for the run that fills the cache | `METHODOLOGY.md §11a` (same entry as #1) + `§11b` test-lane note | C1c TDD list in feature doc (00c818c); `WINDOWS-SSH-PROBES.md:74` already does partial checkpoints for one probe type only | new | HIGH |
| 3 | CPU BUDGET BEFORE LAUNCH. Before starting a heavy run, read load/cores/RAM; jobs ≤ physical threads across ALL concurrent heavy runs (agents included), and never launch a second heavy run while one is active — queue it. Record the load in the run log so a slow run can be attributed | `PROMPT-LOOP.md` DELEGATION + MODEL TIER / parallel-sweep rules | C2d 10.6 h at load 23-30, 25 JVMs on 16 threads (feature doc C2d entry); operator rule memory `speed-without-sacrificing-quality` | new | MEDIUM |
| 4 | PER-UNIT PROCESS SPAWN OF A HEAVY RUNTIME IS A SMELL. When a pipeline starts a JVM/interpreter per unit, measure the spawn share; if it dominates, keep a persistent server (the grader's `--tool-server` for javac/javap already does this; CFR/Procyon fallback does not) | `METHODOLOGY.md §11a` or `toolbelt/tool-registry.md` notes | jxbrowser ~8 h of the 10.6 h C2d run; child task C1c-G1 | new | LOW |
| 5 | GENERIC RUN ENGINE + VERIFIED SEARCH ORDERING. Promote one reusable toolbelt module for any per-unit batch run (decompile grading, bog/XML parse caches, research sweeps, data pipelines): content-addressed per-unit cache that is also the checkpoint (#1/#2), cores/RAM-capped workers (#3), longest-first scheduling from the previous run's durations, per-stage time accumulators, and a strategy ranker that ORDERS (never skips) candidate strategies by their historical success rate (multi-armed-bandit style) so the first verified-exact result ends the search early. Quality invariant: the verifier (compiler, bytecode compare, test) stays the only judge; ordering changes time, never the result | `toolbelt/` (new module + tests) · `METHODOLOGY.md §11a` pointer | niagara5-research C1c/C1c-G1 design (1ff27f5); HARBOR retro row 1 (bog-nav reparse, same cache need); jxbrowser fallbacks: CFR rescued 232/~1,130, Procyon 11/~906 (order by success rate) | new | MEDIUM |

- **#1** — the most expensive lesson of the run; module-level caching looked like "we already cache" while every real change still cost hours. Cost: one key function + store per pipeline.
- **#2** — makes a cache trustworthy (a stale hit is a silent wrong grade, the worst failure for a fidelity tool) and turns crashes/compactions into a resume instead of a restart. The honesty clause prevents claiming gains the first run cannot have.
- **#3** — oversubscription made every concurrent run slower and hid which one was slow; queueing is free.
- **#5** — the operator asked for an algorithm usable "para cualquier cosa"; every pipeline in this fleet re-invents caching/checkpoint/scheduling. Build it first inside niagara5-research C1c as a domain-free module, prove it with the equivalence tests, then promote.
- **#4** — narrow but recurring for JVM toolchains; LOW until C1c-G1 measures it.

## Already covered (dedupe — proof the retro read the kit first)

- Do not run parallel sweeps that write shared state → already covered by PROMPT-LOOP concurrent-scout rules (~l.406) and OPERATOR-INJECTED GAP (MID-LOOP PARALLEL) (~l.455); they address correctness of shared writes, not CPU budget (hence #3).
- Partial checkpoint every N iterations so a cut session keeps results → already covered for Windows SSH probe sweeps only (`toolbelt/WINDOWS-SSH-PROBES.md:74-82`); #2 generalises it with an equivalence proof.
- Idempotent provisioning (`install-tool.sh` never re-installs) → METHODOLOGY §10 ~l.1393; tool installs, not data pipelines.
- Print the population count with the mutation / population-floor gate → §11a; complements #2 (a resumed run must still report the full population).

## Anti-patterns observed (optional)

- C2d, C4 and C2a-G1 heavy stages launched concurrently on one 16-thread machine → #3.
- A per-module up-to-date check treated as "the cache" → #1.
- (Coordinator, non-kit) the review driver was given a relative worktree path and failed twice before the cause was found; recorded in the feature doc, not a kit delta.

## Tools built, adapted, or outgrown

| # | CREATED (path · purpose) | ADAPTED (kit tool · what the kit version could not express) | OUTGREW (kit tool · why stopped) | ORACLE (tool · what it SEEs, not recomputes) | VERDICT (decision · evidence) |
|---|---|---|---|---|---|
| T1 | `niagara5-research/tools/n5-fidelity.py` `--patch-label` + best-of over bin/ext rungs (3c46358, 3c156e0) | — | — | the grader itself is an oracle: it recompiles the decompiled source and compares bytecode with the shipped class, it does not trust the decompiler | `keep-local` · Niagara-specific |
| T2 | C1c per-class cache/checkpoint (designed, not built) | — | — | — | `promote` candidate once built and its equivalence test passes (pattern for #1/#2, not the code) |

## Metrics

- **Blocks reviewed**: 0 (tooling run, no corpus blocks)  ·  **§14 cross-block corrections in this run**: 0  ·  **Rules skipped in practice**: 0
- **Deltas proposed (new)**: 5  ·  **Already-covered lessons**: 4

## Honest verdict

Yes, this run surfaced something new for the kit: §11a has many data-correctness heuristics but nothing about
throughput of long batch runs, reuse keyed on content, resume after interruption, or CPU budget. Deltas #1 and #2
are the valuable ones and generalise beyond Niagara. Caveat: the C1c implementation does not exist yet, so the
evidence is the measured cost and the code reading, not a measured speedup; the maintainer may prefer to apply
#1/#2 after C1c's equivalence test passes.
