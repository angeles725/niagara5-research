# Block 9004 — synthetic fixture for R4 child-gap hygiene

## 9004.x — Child gaps opened

- **B9004-G1** — Positive: no coverage-check clause at all, just a plain gap description.
- **B9004-G2** — Positive: has coverage-check but cites 3623 candidates with no measured-by.
  coverage-check: rg -il "foo|bar" over niagara5-block*.md, zero hits.
- **B9004-G3** — Negative: fully compliant. coverage-check: rg -il "baz|qux" over
  niagara5-block*.md, zero hits. measured-by: `wc -l` over the sweep output, this session.
- **B9004-G4** — Negative: no big numbers, has coverage-check. coverage-check: rg -il "quux" over
  niagara5-block*.md, zero hits.
