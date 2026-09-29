# evidence/b124 — bundle-to-readable-source proof for the `*.built.min.js` bundles (B119-G1)

Scripts (Node, no vendor code is committed; inputs are read from `organized/<module>/extracted/`):

| Script | Step | Output (committed) |
|---|---|---|
| `bundle_census.js` | acorn parse of every `organized/*/extracted/rc/**/*.built.min.js`: path, size, sha256, banner, `define()` ids, hoisted prelude statements, other segments | `bundles.tsv` (derived) |
| `bundle_equiv.js` | id to readable path, then tiered equivalence per module (uses `b124_lib.js`) | `modules.tsv` |
| `bundle_hbs.js` | re-run the shipped Handlebars compiler (`organized/js/extracted/rc/handlebars/handlebars.js`, v4.7.9) on each `.hbs` and compare with the template spec in the bundle | `hbs.tsv` |
| `bundle_segments.js` | prove the non-`define` bytes: hoisted prelude statements and vendor/other segments | `segments.tsv` |
| `bundle_controls.js` | oracle validity: baseline, negative (wrong pair), string and operator mutations | `controls.json` |
| `minifier_fingerprint.js` | which terser/uglify-js release reproduces the bundle output | `fingerprint.json` |
| `helper_pattern.js` | one probe per minifier release: does it collapse the Babel `_typeof` helper the way the bundles show | `helper-pattern.txt` |
| `bundle_tally.py` | combines the JSON into the TSV tables and `summary.txt` | `bundles.tsv`, `modules.tsv`, `summary.txt` |

Tools (installed 2026-09-29 into a scratch dir with `npm install`, registry.npmjs.org, Node v24.19.0):
`acorn@8.18.0`, `terser@5.51.2`, `uglify-js@3.19.3`, `handlebars@4.7.9` (only to cross-check; the corpus copy of
handlebars v4.7.9 is what `bundle_hbs.js` runs), and older terser releases as npm aliases
(`t505@npm:terser@5.5.1`, `t514@npm:terser@5.14.2`, `t519@npm:terser@5.19.4`, `t526@npm:terser@5.26.0`,
`t531@npm:terser@5.31.6`, `t536@npm:terser@5.36.0`, `t539@npm:terser@5.39.2`, `t543@npm:terser@5.43.1`,
`t481@npm:terser@4.8.1`, `t561@npm:terser@5.6.1`, `t572@npm:terser@5.7.2`, `t590@npm:terser@5.9.0`,
`t5100@npm:terser@5.10.0`, `t5121@npm:terser@5.12.1`).

Reproduce (`S` = the directory holding `node_modules`, `O` = `organized/`):

    NODE_PATH=$S/node_modules node bundle_census.js $O census.json      # scratch (550 KB, over the evidence cap; kept in organized/_evidence/b124/)
    NODE_PATH=$S/node_modules node bundle_equiv.js $O census.json equiv.json   # ~7 min
    NODE_PATH=$S/node_modules node bundle_hbs.js $O census.json hbs.json
    NODE_PATH=$S/node_modules node bundle_segments.js $O census.json seg.json
    NODE_PATH=$S/node_modules node bundle_controls.js $O census.json equiv.json controls.json 120
    NODE_PATH=$S/node_modules node minifier_fingerprint.js $O census.json equiv.json fingerprint.json 100
    python3 bundle_tally.py census.json equiv.json hbs.json seg.json .

Method note (a bug found and fixed while building this): `terser.minify("(function(){...});")` returns an EMPTY
string with compress on, because a bare function expression is side-effect free; a first version that wrapped
code in parentheses therefore reported 2,147 of 2,153 modules as "equal" (both sides empty). The negative
control (`bundle_controls.js`) exposed it; `b124_lib.js` now wraps the code in a call, `__n(...)`, and the
controls are part of the committed evidence.
