# Block 119 — Source-map census and minified-JS audit: 86 JSON source maps ship, only 42 carry originals (all Babel-transpiled driver/workbench code that already ships readable), none of the 234 minified JS files has a map, and the 42 originals are now recovered

> Research task for gap **B117-G3** ([Block 117] §117.3 and its child-gap list: "Tag corpus claims that rest on the
> 234 minified JS files, and check whether the 86 `.map` files carry `sourcesContent`"). Answers five questions:
> (1) which modules/files ship source maps and what each unique map contains; (2) where the originals of the maps
> WITHOUT `sourcesContent` live; (3) which shipped JS is minified with no map at all; (4) which earlier blocks read
> claims from minified JS; (5) a durable, tested tool that materialises the recovered originals. Does **not**
> cover: decompiling or reverse-engineering any minified bundle's logic; third-party library identity of the
> minified vendor files (child gap B119-G2); behavioural equivalence of the Babel output and the recovered ES2015
> source; the 18 `jakarta.mail` `META-INF/*.map` files (charset/address lookup tables, not source maps, §119.1).
>
> Type: evidence. **Subject version:** Niagara N5 5.0.0.28 (Beta), extracted module trees
> `/home/cristian/niagara5-research/organized/<module>/extracted/` (byte-exact jar contents, [Block 117] §117.1);
> N4 cross-check `organized/uxBuilder/uxBuilder-ux/uxBuilder-ux.jar` (N4, sha256 `cfce7add6a06e75404e90fa6c154a50f04135676ccfc082dfcdbaf7f2830e6f0`).
> Every measurement is a stdlib python3 script kept in `evidence/b119/` (see its `README.md`); each takes the
> organized dir as its argument. Markers: `[CERT-hw]` = executed this session with the cited script/output;
> `[CERT]` = read at a `file:line`; `[INFER]` = derived.
>
> **ALREADY-COVERED check (literal queries, 2026-09-29):** `rg -il "sourceMappingURL|\.js\.map|source map|sourcemap"
> niagara5-block*.md` → [Block 117] (the gap itself) and [Block 75] (one sentence, §119.6); `rg -il sourcesContent
> niagara5-block*.md tools/` → [Block 117] only; `python3 tools/check-coverage.py sourcemap sourcesContent` → prior
> coverage found only in B117 (the census that opened this gap), no answer. `.map` files had no reader in the
> corpus tooling before this block.

---

## 119.1 — Census of the 88 unique maps: 86 are JSON source maps, 42 carry `sourcesContent`, 44 do not; the orchestrator's pre-census is reproduced exactly `[CERT-hw]`

`evidence/b119/census_maps.py <organized>` walks `organized/` excluding `_best/` (which only re-links) and hashes
every `*.map`: **448 paths → 88 unique sha256**. Every one of the 86 JSON maps appears in exactly 5 trees
(`extracted`, `resources`, `vineflower`, `vineflower-cons`, `vineflower2`: 86 × 5 = 430), and the 2 non-JSON files
account for the other 18 paths (`_lib-inf-3p/jakarta.mail-2.0.5-…/extracted/META-INF/jakarta.charset.map` 6 paths,
`jakarta.address.map` 12 paths). Those 2 are `charset=`/`a=b` lookup tables, not source maps
(`evidence/b119/census-maps.out`).

Of the 86 JSON maps: **42 have non-empty `sourcesContent`, 44 have none**; `sources` entries total **269** (42 + 160 +
67). Classified by what the map maps (`sources[0]` extension, `evidence/b119/census-maps.json`):

| Class | Unique maps | `sourcesContent` | Modules |
|---|---|---|---|
| JS with embedded original | 42 | yes (42 of 42 non-empty, 1 source each) | `driver` 40, `workbench` 2 (`findCommands.js`, `BroadcastChannel.js`) |
| JS without embedded original | 1 | no | `js`: `rc/underscore/underscore-umd.js.map`, 160 sources |
| LESS→CSS | 42 (31 `maps/<module>.map`, 8 theme `less/maps/*.map`, 3 `sprite/**/maps/*.map`) | no | 34 modules, incl. `themeN5` 6, `themeLucid` 2, `themeZebra` 2, `icons` 1 (sources are `.less`, 67 entries, 53 unique paths) |
| Empty map | 1 | no | `platform/maps/platform.map` = `{"version":3,"sources":[],"names":[],"mappings":""}` |

So the popular reading of B117 ("86 source maps ship alongside minified JS") is wrong in kind: **only 43 of the 86
maps map JavaScript at all, and 42 of the remaining 43 maps map LESS** `[CERT-hw]`.

**The 42 recovered originals versus the shipped JS** (`evidence/b119/analyze_sc.py`, `es_features.py`, outputs
`sc-analysis.json`, `es-features.out`):

- The generated file named by `file` exists next to the map for **42/42** and ends with a `sourceMappingURL` comment
  for 42/42.
- The shipped JS is **not minified**: 0/42 meet B117's rule (longest line ≥ 1,000 B or mean ≥ 250 B); the longest
  line anywhere is 816 B and the largest mean line length is 82.0 B. Comments (`/** … */`, `//`) survive in 42/42
  generated files and 42/42 originals.
- The shipped file is **Babel-transpiled ES5** from ES2015+ source: **33 of 42** originals use ES2015+ constructs
  (arrow functions 24 files, `const`/`let` 27, `class … {` 20, spread/rest 7; comments stripped before counting,
  so this is a lower bound) and **0 of 42** shipped files do. Example: `ExtMgrColumn.js` is `return class
  ExtMgrColumn extends PropertyMgrColumn {…}` in the original (1,002 B) and gains the `_typeof`,
  `_classCallCheck`, `_createClass` … helpers in the shipped file (4,191 B). Total 156,824 B original versus
  242,978 B shipped (1.55×).
- 5 originals are ES5-only and **code-identical** to the shipped file after stripping comments and whitespace;
  4 are ES5-only but differ (Babel re-print, e.g. `var XYPoint = function (params)` → `var XYPoint = function
  XYPoint(params)` in `XYPoint.js`; not itemised further) `[INFER]`.
- 40 of 42 originals are AMD (`define(`); the 2 `workbench` ones are IIFEs; **0/42 contain `import`/`export`**,
  which independently corroborates [Block 21]'s "no ES-module syntax" finding for these files.
- The originals live at build-tree paths outside the jar (`../../../../src/rc/wb/mgr/PointMgr.js`, 4 to 8 leading
  `../`), i.e. the vendor's Gradle/Grunt `src/` layout; `sourceRoot` is absent in all 86 maps.

**Verdict for question 1.** The recovered originals add no missing logic: the shipped JS was already readable
(comments intact) for every map that has an original. Their value is the ES2015 syntax and original formatting;
they change no behavioural claim in the corpus (§119.4).

---

## 119.2 — Originals of the 44 maps without `sourcesContent`: 43 of 44 need none (LESS sources ship verbatim; the empty map has no source); the 160 underscore modules are absent (two-term census), but their bundle ships `[CERT-hw]`

**LESS maps (42 maps, 67 source entries, 53 unique paths).** Every `/module/<m>/<path>.less` source resolves to
`organized/<m>/extracted/<path>.less` (67/67 found, `evidence/b119/verify-less.out`), and for every one the
highest source line named by the map's `mappings` (VLQ-decoded in `evidence/b119/verify_less.py`) is smaller than the
shipped file's line count (67/67 fit, 0 exceed). The shipped tree holds 71 `.less` files in `extracted/`
(`find organized -path '*/extracted/*' -iname '*.less'`), 15 in `analytics` alone. Two independent terms were used
per METHODOLOGY's absence rule: (a) path-derived name lookup (67/67), (b) content consistency of the mapping ranges
against the found file (67/67). A content sha256 lookup is impossible here because the map does not contain the
source bytes; the range check is the substitute, and it is a consistency test, not proof of byte identity `[INFER]`.

**`platform.map`** has 0 sources: nothing to recover.

**`underscore-umd.js.map` (160 sources).** The sources are the 160 ES modules of upstream `underscore`
(`modules/_setup.js` … `modules/index-default.js`). Census (`evidence/b119/underscore_search.py`,
`underscore-search.out`): term 1, exact basenames under all of `organized/` (excluding `_best/`): only 2 of the 160
names occur (`underscore.js`, which is the bundle itself, and an unrelated `xprotect/**/js/template.js`), so 158 are
not shipped as files; term 2, content tokens: `function restArguments` and `VERSION = '1.13` occur in the shipped
bundle `js/extracted/rc/underscore/underscore.js` (5 tree copies), and `modules/_setup` occurs in 0 files. The
generated file `underscore-umd.js` named by the map is **not shipped** (the rc directory holds `LICENSE.txt`,
`underscore-min.js`, `underscore-umd.js.map`, `underscore.js`); `underscore.js` (2,064 lines, `VERSION = '1.13.8'`
at `js/extracted/rc/underscore/underscore.js:16`) is the UMD build and still ends with `//#
sourceMappingURL=underscore-umd.js.map` (line 2064), i.e. it was renamed after the map was written `[CERT-hw]`.
The originals are open-source upstream files; hash-verification against the npm package is child gap B119-G2.

---

## 119.3 — Minified JS with no map: all of B117's 234 files have none, but only 132 are truly minified; 102 are readable Babel output caught by the long-line half of the rule `[CERT-hw]`

`evidence/b119/minified_nomap.py <organized>` re-applies B117's rule (`tools/n5-extract-census.py:66`
`is_minified_js`: longest line ≥ 1,000 B **or** mean line ≥ 250 B) to every `*.js` under
`organized/*/extracted` (+ the `_bin-ext`/`_lib-inf-3p` sub-extractions): 2,572 JS files, **237 minified**; excluding
the `_`-prefixed pseudo-modules the count is **234 of 2,560**, B117's figure, so the census reproduces (the 3 extra are
`_bin-ext` 2 and `_lib-inf-3p` 1, e.g. `forge.min.js`).

- **Map coverage of the 237: 0 have a sibling `<file>.js.map` and 0 have an existing `sourceMappingURL` target.** 7
  carry a dangling `sourceMappingURL` comment (`forge.min.js` ×2, `babel.min.js`, `jquery.contextMenu.min.js`,
  `moment.min.js`, `media-stream-library.min.js`, `hls.min.js`) whose maps were not shipped. The 43 shipped JS
  maps (§119.1) map only non-minified files. So no minified claim can be re-derived from a map.
- **Rule precision** (`minified_split.py`): of the 234, **132** meet the mean-line half (truly minified; 111 have
  ≤ 10 lines) and **102** meet only the longest-line half (median 530 lines, median mean line 41.5 B, i.e.
  readable Babel-transpiled Tridium code with a few very long helper lines, e.g. `alarm/rc/views/AlarmExtUxManager.js`,
  733 lines). Claims about those 102 rest on readable code.
- **Composition of the 132:** 71 are per-module bundles `rc/<module>.built.min.js` (banner `@copyright 2026 Tridium`),
  the rest are third-party vendor libraries (`jquery`, `d3`, `moment`, `handlebars`, `bluebird`, `ace`, `babel`,
  `prettify`, …; module `js` 32, `docDeveloper` 20). Every one of the 71 bundle modules also ships readable
  per-file JS under its `rc/` (e.g. `webEditors` 399 files, `bajaScript` 206); that these are the bundle's
  constituents is `[INFER]` (bundle membership not proved, child gap B119-G1). **[Measured by [Block 124] §124.1, §124.10: 72 `*.built.min.js` files, 57 with the 2026 banner (not 71); membership is now measured for all 2,315 `define` modules.]**
- Minified files are physically 4-5 lines: `bs.built.min.js` (363,641 B), `bajaux.built.min.js` (155,569 B),
  `uxBuilder.built.min.js` (382,030 B) each have 4 newline characters (`awk 'END{print NR}'` = 5). A `file:line` citation
  into them is therefore meaningless beyond line 5; use a byte offset or a string.

---

## 119.4 — Earlier blocks that read claims from minified JS: 106 `.js` citations in 15 blocks, no claim is contradicted by the recovered originals `[CERT-hw]`

`evidence/b119/block_js_cites.py <repo> <organized>` extracts every `*.js` token from `niagara5-block*.md`, resolves it
to files under the extracted trees (exact path suffix, else unique basename) and classifies the file by §119.3:
106 tokens: 64 readable, 13 long-line-only (readable Babel output), **15 minified**, 14 unresolved (not files:
`javax.baja.web.js`, `niagara.web.js`, `.min.js` as a suffix, typos, Javadoc index names). The 15 minified citations
sit in 5 blocks. Grading (SUSPECT = the claim needs logic read from minified code; SAFE = the claim is a string
literal, an inventory or a structure count that survives minification):

| Block | Minified file cited | What the claim needs | Verdict |
|---|---|---|---|
| [Block 21] §21.x (lines 90-101 of `niagara5-block21.md`) | `bs.built.min.js`, `bajaux.built.min.js` | Babel helper names (`_toConsumableArray`/`_callSuper`, `_defineAccessor`/`_superPropGet`), literal `define("bajaux/events"`, absence of webpack markers | **SAFE** on substance (helper identifiers and `define("…")` literals survive minification; re-`grep`ed present this session: 1 hit line each, `define("bajaux/events"` present). **Cite form SUSPECT:** `…built.min.js:1-400` names lines in a 5-line file (§119.3). |
| [Block 75] §75.3 (line 205-210 of `niagara5-block75.md`) | N4 `uxBuilder-ux.jar` `rc/uxBuilder.built.min.js`, `maps/uxBuilder.map` | "a single pre-minified JS bundle and its sourcemap" | **CORRECTED** (§119.6): the N4 bundle is a 64-byte banner stub and the map is an empty map; N5's `uxBuilder.map` maps LESS. |
| [Block 79] | `uxBuilder.built.min.js` | `define("…")` id census only ("structure/module-census only" by its own scope) | **SAFE** (string-literal census) |
| [Block 102] | `uxBuilder.built.min.js` ORD | Java-side ORD string of `BUxBuilderJsBuild` | **SAFE** (decompiled Java, not the JS) |
| [Block 4] | `JsPlayground.built.min.js`, `babel.min.js` | existence and purpose in the module inventory | **SAFE** (inventory) |

The 13 long-line-only citations (B79 `UxBuilder.js`/`MwPalettePreview.js`/`MwPropertyBatch.js`, B102 five uxBuilder
files, B103 `PropertySheetRow.js`) are readable Babel output: **SAFE**. The 10 blocks citing only readable files
(B10, B20, B26, B27, B36, B38, B49, B52, B72, B103) are **SAFE**. **Limitation:** the method finds `.js` tokens; a
block that reads a minified bundle without naming a `.js` file would be missed, and none of the 42 recovered-original
basenames is cited by any block (0 hits over `niagara5-block*.md`), so there is nothing the originals could
contradict.

---

## 119.5 — Recovered originals materialised: `tools/n5-sourcemap-recover.py` (RED→GREEN, 16 tests) extracted 42 originals, 0 rejected, 227 source entries left as `no-sourcesContent` `[CERT-hw]`

`tools/n5-sourcemap-recover.py --organized-dir <organized> [--out-dir DIR]` scans `<module>/extracted/**/*.map` only
(never the four decompiler copies, never `_`-prefixed dirs) and writes each embedded original to
`organized/_sourcemaps/<module>/<normalized source path>` plus a deterministic `manifest.json` (per map: sha256,
`file`, `has_sourcesContent`, per source: original string, normalized `path`, `content_sha256`, `status`). Safety
rules, each pinned by a test: `webpack:///` and `webpack://<ns>/` prefixes and a leading `./` removed; absolute
paths, drive letters, NUL, empty results and any `..` after the leading run rejected (`rejected-unsafe-path`); a
**leading** `../` run is stripped and counted (`parent_dirs_stripped`) because all 42 real sources begin with 4-8
`../` (rejecting every `..` would recover nothing) — the stripped path is contained by construction and a final
realpath check guards each write; a second source landing on an existing path with different bytes is a `collision`
and never overwrites.

- **RED:** the test file was written first (fixtures under `tools/tests/fixtures/sourcemap/corpus/`, the directory is
  named `corpus` because the repo `.gitignore` ignores `organized/`); with no tool: `Ran 16 tests … FAILED
  (failures=10, errors=5)` (`evidence/b119/tdd-red.txt`).
- **GREEN:** `python3 -m unittest discover -s tools/tests -p test_n5_sourcemap_recover.py` → `Ran 16 tests OK`
  (`tdd-green.txt`); a mutant removing the inner-`..` rejection is killed (`FAILED (failures=2)`,
  `tdd-mutant-innerdotdot.txt`); `make test` → `Ran 486 tests … OK (skipped=4)` (`make-test.txt`).
  `pytest` is not installed on this machine (`No module named pytest`, both interpreters), so the unittest runner
  the repo's `make test` already uses was run instead.
- **Real run** (`recover-real-run.txt`): `maps 86 (with sourcesContent 42, not a source map 0) | sources 269 |
  recovered 42, duplicate 0, no-sourcesContent 227, no-content 0, collision 0, rejected 0` → 43 files (42 sources +
  manifest), 392 KB under `organized/_sourcemaps/{driver,workbench}/`; the manifest is copied to
  `evidence/b119/sourcemaps-manifest.json` (sha256 `fca3f1eceb968dc209a3bb7f7fe342c4a7489c6bd6c5980292482ef20aa67bad`).
  The jakarta maps are excluded by design (`_lib-inf-3p`); the 227 = 269 − 42 covers 67 LESS entries, 160 underscore
  modules, and 0 others.

---

## 119.6 — Corrections to earlier blocks

- **[Block 75] §75.3** (`niagara5-block75.md:208-210`): "`rc/uxBuilder.built.min.js`, `maps/uxBuilder.map` — CSS/LESS/a
  single pre-minified JS bundle and its sourcemap". N4 `uxBuilder-ux.jar` (sha256 above): the bundle is **64 bytes**
  (the copyright banner only), `rc/uxBuilder.less` is 0 bytes, and `maps/uxBuilder.map` is the 51-byte empty map
  `{"version":3,"sources":[],"names":[],"mappings":""}` (`evidence/b119/n4-uxbuilder-map.txt`). In N5 the
  `maps/uxBuilder.map` maps `/module/uxBuilder/rc/uxBuilder.less`, not the JS bundle (§119.1). No shipped source map
  belongs to any `*.built.min.js` (§119.3). `[CERT-hw]`
- **[Block 21]** (`niagara5-block21.md:96,98`): the citations `bs.built.min.js:1-400` / `bajaux.built.min.js:1-400` name
  line numbers in 5-line files (§119.3); read them as "first 400 bytes". The findings stand (§119.4).
- **[Block 117] §117.3**: "86 `.map` source maps ship alongside" minified JS — the 86 maps cover 0 minified files;
  42 map readable transpiled JS, 42 map LESS, 1 maps underscore's ES modules, 1 is empty (§119.1). The "234 minified"
  figure over-counts by 102 readable files (§119.3). The orchestrator adds the pointer lines.

---

## 119.7 — Connections

- [Block 117] §117.3 counted the 234 minified and 86 map files; this block classifies both and closes B117-G3.
- [Block 21] §21 (Babel/AMD finding) is corroborated for the 42 recovered originals (0 `import`/`export`, all AMD or IIFE).
- [Block 75], [Block 79], [Block 102]: the uxBuilder bundle is a 382,030-byte, 5-line file whose module ids are the
  only safely readable content; its readable per-file sources ship beside it.
- [Block 118] §118.10's ladder covers Java; this block is the JS analogue: for JS, cite the readable sibling or the
  recovered original (`organized/_sourcemaps/`), never a `file:line` into a minified bundle.
- [Block 115]/[Block 116] (decompiler fidelity) do not apply to JS: none of these files is decompiled; the recovered
  originals are the vendor's own bytes from `sourcesContent`.

## 119.8 — Child gaps opened

- **B119-G1** (medium) — Prove bundle membership: for each of the 71 `rc/<module>.built.min.js` bundles, extract the
  `define("…")` ids and match them to the module's shipped readable `rc/**/*.js` files, so any claim about a
  bundle can be re-read from its readable constituents (and list ids present only in the bundle).
  Investigable read-only. coverage-check: `rg -il "built\.min" niagara5-block*.md` → [Block 4], [Block 21], [Block 75],
  [Block 79], [Block 102], all structure-level; none matches ids to siblings. measured-by: number of bundle
  `define` ids with a same-path shipped sibling, per module (baseline: 71 bundles, 132 truly-minified files).
- **B119-G2** (low) — Third-party identity of the minified vendor JS and of underscore 1.13.8: hash the 160 upstream
  ES modules / `underscore-umd.js` and the 7 files with dangling `sourceMappingURL` (`forge.min.js`, `babel.min.js`,
  `moment.min.js`, …) against the npm artifacts of the matching versions. Requires external fetch (not run here;
  no web tool used this session). coverage-check: `rg -il "underscore" niagara5-block*.md` → only [Block 21]/[Block 75]
  inventory mentions, no hash comparison; [Block 117] §117.x covers Maven jars only. measured-by: files matching
  upstream by sha256 of 160 modules + 7 vendor files.
- **B119-G3** (medium) — Fix the rule: split `is_minified_js` into `minified` (mean ≥ 250 B) and `long-line`
  (longest ≥ 1,000 B only) in `tools/n5-extract-census.py` with tests, and re-run the sweep so
  `census-modules.json` reports 132/102 instead of 234. Investigable read-only, needs a code change
  (requires-execution for the sweep). coverage-check: `rg -n "is_minified_js" tools/ niagara5-block*.md` → the tool
  and [Block 117] only. measured-by: `evidence/b119/minified-split.out` (132 mean-line, 102 longest-only).
- **B119-G4** (low) — Cite-form audit: find every corpus citation of the form `<file>.js:<n>[-<m>]` whose target has
  fewer lines than `<n>` (B21's `built.min.js:1-400` is the known case) across all blocks and the writer prompt.
  Investigable read-only. coverage-check: §119.4 extracted `.js` tokens but not their `:line` suffixes; no earlier
  block checks line-range validity. measured-by: count of `file.js:line` citations whose file has fewer lines
  than the cited line (baseline: 2 in [Block 21]).
- **B119-G5** (low) — Compile the 42 LESS sources' shipped `.less` with a LESS compiler and compare the output to the
  shipped `.css` through the maps, upgrading §119.2's range-consistency test to byte-level proof. Requires-execution
  (needs a LESS toolchain). coverage-check: `rg -il "\.less" niagara5-block*.md` → theme/inventory mentions only;
  none compiles them. measured-by: CSS files reproduced byte-identical of 42 maps.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 448 `.map` paths, 88 unique sha256, 2 non-JSON, 86 JSON, 42 with / 44 without `sourcesContent`, 269 `sources` entries | [CERT-hw] | `evidence/b119/census_maps.py`, `evidence/b119/census-maps.out` |
| 2 | Class split 42 JS-with-original, 1 underscore, 42 LESS (31/8/3), 1 empty; each of 86 in exactly 5 trees | [CERT-hw] | `evidence/b119/census-maps.json` |
| 3 | 42/42 generated files exist, 42/42 end with `sourceMappingURL`, 0/42 minified (max line 816 B, max mean 82.0 B) | [CERT-hw] | `evidence/b119/analyze_sc.py`, `evidence/b119/sc-analysis.json` |
| 4 | 33/42 originals use ES2015+ (arrow 24, const/let 27, class 20, spread 7), 0/42 shipped; 156,824 B vs 242,978 B | [CERT-hw] | `evidence/b119/es_features.py`, `evidence/b119/es-features.out`, `evidence/b119/sc-analysis.json` |
| 5 | 5 ES5-only originals code-identical after comment/ws strip, 4 differ; 0/42 `import`/`export`; 40 AMD | [CERT-hw] | `evidence/b119/sc-analysis.json` (`code_identical_after_comment_ws_strip`, `src_es_import_export`, `src_amd_define`) |
| 6 | 67/67 LESS sources ship at `extracted/<path>`; 67/67 mapped lines fit shipped line counts; 71 `.less` in extracted trees | [CERT-hw] | `evidence/b119/verify_less.py`, `evidence/b119/verify-less.out`, `evidence/b119/less-locate.json` |
| 7 | Census: 158 of 160 underscore module names not shipped; bundle `underscore.js` 1.13.8 ships; `underscore-umd.js` absent; dangling `sourceMappingURL` at line 2064 | [CERT-hw] | `evidence/b119/underscore_search.py`, `evidence/b119/underscore-search.out`; `organized/js/extracted/rc/underscore/underscore.js:2064` |
| 8 | 2,572 JS / 237 minified (234 of 2,560 excluding `_` dirs); 0 sibling maps, 0 existing map targets; 7 dangling refs | [CERT-hw] | `evidence/b119/minified_nomap.py`, `evidence/b119/minified-nomap.out`, `evidence/b119/minified-nomap.json` |
| 9 | 234 = 132 mean-line minified + 102 long-line-only; 71 `*.built.min.js` bundles | [CERT-hw] | `evidence/b119/minified_split.py`, `evidence/b119/minified-split.out`, `evidence/b119/minified-split.json` |
| 10 | Bundles have 4 newline chars (`bs.built.min.js` 363,641 B; `bajaux` 155,569 B; `uxBuilder` 382,030 B) | [CERT-hw] | `awk 'END{print NR}'` and `wc -lc` on `organized/{bajaScript,bajaux,uxBuilder}/extracted/rc/*.built.min.js` (5 lines each) |
| 11 | 106 `.js` citations in 15 blocks: 64 readable, 13 long-line-only, 15 minified, 14 unresolved | [CERT-hw] | `evidence/b119/block_js_cites.py`, `evidence/b119/block-js-cites.out`, `evidence/b119/block-js-cites.json` |
| 12 | B21 helper tokens and `define("bajaux/events"` present in the minified bundles | [CERT-hw] | `grep -c` and `grep -o` on `organized/bajaScript/extracted/rc/bs.built.min.js`, `organized/bajaux/extracted/rc/bajaux.built.min.js` (this session) |
| 13 | N4 `uxBuilder-ux.jar`: bundle 64 B banner-only, `.less` 0 B, map 51 B with 0 sources; N5 map's source is `uxBuilder.less` | [CERT-hw] | `evidence/b119/n4-uxbuilder-map.txt` |
| 14 | Tool RED (10 failures + 5 errors) → GREEN 16/16; inner-`..` mutant killed; `make test` 486 OK | [CERT-hw] | `evidence/b119/tdd-red.txt`, `evidence/b119/tdd-green.txt`, `evidence/b119/tdd-mutant-innerdotdot.txt`, `evidence/b119/make-test.txt`, `tools/tests/test_n5_sourcemap_recover.py` |
| 15 | Real run recovered 42/269, 0 rejected, 0 collisions; manifest sha256 `fca3f1ec…` | [CERT-hw] | `evidence/b119/recover-real-run.txt`, `evidence/b119/sourcemaps-manifest.json`, `tools/n5-sourcemap-recover.py` |
| 16 | Bundle constituents = the module's readable `rc/` JS files | [INFER] | Babel banner + sibling counts (`minified-split.json`); membership unproved, B119-G1 |
| 17 | Babel re-print explains the 4 ES5-only differing originals | [INFER] | one diff read (`XYPoint.js`), not itemised |
| 18 | Range-fit of mapped LESS lines implies the shipped `.less` is the mapped source | [INFER] | consistency test only, B119-G5 |

**Tally:** 15 `[CERT-hw]` · 0 `[CERT]` · 3 `[INFER]`; `[INFER]`/`[CERT]`-family ratio 0.2 (evidence block; the
INFERs are the three explicitly gapped ones).

**Artifacts:** `evidence/b119/` (scripts, JSON/outputs, README; total < 400 KB, no binaries or proprietary jars, the
N4 jar cited by sha256 only); `tools/n5-sourcemap-recover.py`, `tools/tests/test_n5_sourcemap_recover.py`,
`tools/tests/fixtures/sourcemap/corpus/`; recovered originals `organized/_sourcemaps/` (gitignored, regenerable with
the tool).
