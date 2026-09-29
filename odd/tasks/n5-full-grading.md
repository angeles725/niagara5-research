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
- Strict TDD (user CLAUDE.md) for tools/ changes; runner `python3 -m pytest tools/tests/test_n5_fidelity.py` and full `make test`.
- RDD granted by the user for this session.
- Classpath = sha256-verified local jar mirror /home/cristian/niagara5-research-localcache/jar-mirror-5.0.0.28
  (re-verified 2026-09-28: modules.sha256 and bin-ext.sha256 rc=0).
- Delivery strategy: ask-on-risk answered by the user's standing authorization → feature branch + PR.

## Tasks
- [ ] F1 Forecast: time one full module (alarm, 195 classes) on vineflower2. Route: inline (evidence below).
- [ ] F2 Intra-module class-level parallelism (`--class-jobs N`): per-class grading is independent (own temp dirs);
      results must be identical to the serial path and ordered deterministically. Route: delegated writer (TDD).
- [ ] F3 Full run, vineflower2 then vineflower, all modules; failures recorded as module_error, never dropped.
      Route: inline background run.
- [ ] F4 Report: regenerate docs/decompile-fidelity-report.md + `--compare vineflower,vineflower2`; verify numbers
      independently (recount grade_counts from the JSON files). Route: inline.
- [ ] F5 Update parent ODD T21, commit, RDD, PR, merge.

## Progress / evidence
- 2026-09-28 branch feat/n5-t21-full-grading off main b57cabf.
