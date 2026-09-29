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
- [ ] F3 Full run, vineflower2 then vineflower, all modules; failures recorded as module_error, never dropped.
      Route: inline background run.
- [ ] F4 Report: regenerate docs/decompile-fidelity-report.md + `--compare vineflower,vineflower2`; verify numbers
      independently (recount grade_counts from the JSON files). Route: inline.
- [ ] F5 Update parent ODD T21, commit, RDD, PR, merge.

## Follow-ups
- first_error embeds the random javac temp dir path (/tmp/tmpXXXX/...), so fidelity JSON is not byte-reproducible
  between runs (pre-existing; serial runs differ too). Normalize to the package-relative path.

## Progress / evidence
- 2026-09-28 branch feat/n5-t21-full-grading off main b57cabf.
- F2 real check: haystack --class-jobs 1 vs 8 → identical grades and key order for all 36 classes; only first_error temp paths differ; 282 s → 85 s.
- F3 launched: scratchpad run-t21.sh (vineflower2 then vineflower), log t21.log.
