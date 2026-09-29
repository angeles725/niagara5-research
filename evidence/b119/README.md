# evidence/b119 — source-map census (B117-G3)

Run against `/home/cristian/niagara5-research/organized` (outside git, read-only), 2026-09-28.
All scripts are stdlib-only python3; each takes the organized dir as its argument.

| Script | Output | Answers |
|---|---|---|
| `census_maps.py` | `census-maps.json`, `census-maps.out` | every `*.map` outside `_best/`: 448 paths, 88 unique sha256, 2 non-JSON, per-map file/sources/sourcesContent |
| `analyze_sc.py` | `sc-analysis.json` | the 42 maps with sourcesContent vs their shipped generated JS |
| `es_features.py` | `es-features.json`, `es-features.out` | ES2015+ constructs in recovered original vs shipped JS (comments stripped; lower bound) |
| `verify_less.py` | `less-locate.json`, `verify-less.out` | the 44 maps without sourcesContent: is each source shipped, do mapped lines fit (VLQ decode) |
| `minified_nomap.py` | `minified-nomap.json`, `minified-nomap.out` | B117 minified rule over all `extracted/**/*.js`; which have a map |
| `minified_split.py` | `minified-split.json`, `minified-split.out` | truly minified (mean line >= 250 B) vs long-line-only |
| `block_js_cites.py` | `block-js-cites.json`, `block-js-cites.out` | every `niagara5-block*.md` `.js` citation resolved and classified |
| (tool) `tools/n5-sourcemap-recover.py` | `recover-real-run.txt`, `sourcemaps-manifest.json` | materialisation of the 42 originals; manifest sha256 `fca3f1eceb968dc209a3bb7f7fe342c4a7489c6bd6c5980292482ef20aa67bad` |
| TDD | `tdd-red.txt`, `tdd-green.txt`, `tdd-mutant-innerdotdot.txt`, `make-test.txt` | RED (10 failures + 5 errors, tool absent), GREEN 16/16, mutant killed (2 failures), `make test` 486 OK |
| N4 cross-check | `n4-uxbuilder-map.txt` | N4 `uxBuilder-ux.jar` map/bundle sizes (jar sha256 inside) |

Recovered originals themselves (156,824 B of Tridium JS) stay under `organized/_sourcemaps/` (gitignored, regenerable).
