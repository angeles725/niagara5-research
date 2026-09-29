# Block 124 — Tracing the 72 `*.built.min.js` bundles to readable source: every one of 2,315 `define()` modules has a shipped readable counterpart, 975 are proven equal by an AST or compiler oracle, 1,315 match by names and literals only

> Research task for gap **B119-G1** ([Block 119] §119.8: "prove which readable files each of the `<module>.built.min.js` bundles is built from"). Goal: fidelity of the JS layer, meaning whether a claim about a bundle can cite a readable shipped file instead of minified code.
>
> Type: evidence (measurement with committed scripts, no tool code under `tools/`, so no TDD ledger; the oracle is validated by controls instead, §124.3). **Subject version:** Niagara N5 5.0.0.28 (Beta). **Scope:** the 72 files named `*.built.min.js` under `organized/<module>/extracted/` (the `vineflower*` trees hold byte copies, [Block 119] §119.3). Not covered: third-party minified vendor JS that is not a `*.built.min.js` (B119-G2), the `.map` files ([Block 119] §119.1), the runtime behaviour of any module.
>
> **Repo hygiene:** public repository, no vendor or decompiled code committed. `evidence/b124/` holds scripts, TSV tables, one JSON of controls and one of the minifier probe; the 550 KB census JSON stays in `organized/_evidence/b124/` (over the evidence cap, gitignored). Commits are listed in §124.13.
>
> **ALREADY-COVERED check (literal queries, 2026-09-29):** `rg -il "built\.min" niagara5-block*.md` → [Block 4], [Block 21], [Block 75], [Block 79], [Block 102], [Block 119], [Block 122]; none matches `define()` ids to readable files except [Block 79] §79.2's `grep -o 'define("'` census of `uxBuilder` (115 ids = 115 files, a count, not a per-file proof). `rg -il "terser|uglify|r\.js" niagara5-block*.md` → only [Block 79]'s `grunt-niagara` mention; no block identifies the minifier.

---

## 124.1 — B119-G1 step 1 ADVANCED: there are 72 bundle files (not 71), 2,315 `define()` modules, 9,305,969 bytes; 57 carry the 2026 banner, none a source-map comment `[CERT-hw]`

`evidence/b124/bundle_census.js` (acorn 8.18.0) parses every `organized/*/extracted/rc/**/*.built.min.js` and walks each top-level statement, because terser joins statements with commas and hides some `define(` calls inside `if(...)` tests and UMD wrappers (2 of the 2,315 sit inside such statements). Result (`evidence/b124/bundles.tsv`, one row per file with sha256):

- **72 files, 9,305,969 bytes, 2,315 named `define("id",[deps],function(){...})` modules.** Every registration is named; the only anonymous `define(` calls (1 in `maxpro`, 17 in `docDeveloper`, regex `define\(` not followed by a quote) are the UMD branches inside bundled vendor libraries. [Block 119] §119.3 counted 71 per-module bundles; the 72nd is the vendor Handlebars plugin `js/rc/require-handlebars-plugin/hbs.built.min.js` (license banner "Handlebars hbs 2.0.0"), and 5 of the 72 are not named `<module>.built.min.js` (`bs`, `JsPlayground`, `hxContainer`, `hbs`, `findCommands`).
- **Banner:** 57 of 72 start with `/** @copyright 2026 Tridium, Inc. ... */`; 15 do not (13 open directly with a Babel helper or a `define`, the hbs plugin with its own license, `smartTableHx` with a 2005 comment). §124.10 corrects the "71 with the 2026 banner" wording.
- **No source map:** 0 of 72 ends in a `sourceMappingURL` comment; the single text hit is a regex inside the bundled Babel standalone (`JsPlayground.built.min.js`). This is the [Block 119] §119.3 result restated for the full set.
- **Layout of a bundle** (e.g. `bajaux.built.min.js`, sha256 `e6f2950746d14dcbbe54d0a1e61ee37a8719d491968d089ad32b3c3049276785`, 155,569 B): a banner comment, then hoisted Babel helper functions (`_defineAccessor`, `_superPropGet`, `_get`, ... 32 of them), then one comma-joined statement of 54 `define()` calls starting at byte 5980. 1,273 top-level helper/script statements (288,711 B) precede or sit between the defines in the 72 files.

## 124.2 — B119-G1 step 2 ADVANCED: all 2,315 `define()` ids resolve to a readable shipped file; none is bundle-only `[CERT-hw]`

`evidence/b124/bundle_equiv.js` maps each id to a path (`nmodule/<m>/rc/X` → `organized/<m>/extracted/rc/X.js`; `hbs!nmodule/<m>/rc/X` → `X.hbs`; `bajaux/X`, `bajaScript/X` → the module's `rc/X.js`; `nmodule/<m>/ext/X` → `ext/X.js`). Four ids are r.js aliases resolved by the file that declares them (`bajaPromises` → `bajaScript/rc/env/Promises.js`, `bajaBrowserEnvUtil` → `env/jQueryBrowserEnvUtil.js`, `dialogs` → `js/rc/dialogs/dialogs.js`, `hbs` → `js/rc/require-handlebars-plugin/hbs.js`; `modules.tsv` column `alias`).

- **Result: 2,315 of 2,315 ids resolve; 0 are "NO-READABLE-SOURCE".** Class-level census over all 72 bundles, literal counts in `evidence/b124/summary.txt`. Every bundle module is therefore traceable to a readable file, so no claim about a bundle has to rest on minified code alone; what varies is how strongly the two texts are proven equal (§124.4).
- **`uxBuilder` reproduces [Block 79] §79.2 exactly and now with the mapping:** 115 ids map to 115 distinct readable files (`modules.tsv`, module `uxBuilder`), the 115 source files [Block 79] counted.
- The dependency arrays are equal after normalisation for 2,152 of the 2,154 modules compared (`deps_equal` column); the 2 exceptions are the empty alias stubs `bajaScript/env/Promises` and `bajaScript/env/jQueryBrowserEnvUtil`, whose path-mapped readable file declares a different id (`bajaPromises`, `bajaBrowserEnvUtil`), themselves matched under the alias.

## 124.3 — The equivalence oracle, its tiers, and a bug the controls caught `[CERT-hw]`

The readable files are Babel output (per-file helpers, `define([deps], function (a, b) {...})`), the bundle modules are minified. The oracle in `evidence/b124/b124_lib.js` compares the factory function of both, after normalising each with a minifier, in this order (strongest first):

1. **`mangle` tier — IDENTICAL-AFTER-MINIFY:** terser with compress off and names mangled equals on both sides, so only formatting, comments and identifier names differ. 2 modules.
2. **`compress` / `uglify-expr` tiers — SEMANTIC-MATCH:** equal after the same terser 5.51.2 compress+mangle pass (262 modules) or the same uglify-js 3.19.3 pass (569 modules). This is AST equality up to the rewrites a minifier applies to both sides, so it is an equivalence proof modulo that minifier's correctness. 831 modules.
3. **`skeleton` tier — SKELETON-MATCH (not a proof):** the sets of property names and words of string literals are equal, Babel-machinery names (`key`, `value`, `prototype`, ...) removed, numeric literals ignored, and the compressed code sizes are within 0.4 to 3 times each other. 1,315 modules. It cannot see control-flow or operator changes (measured below).

**Bug found and fixed while building it (a method blind spot, recorded for future writers).** The first version compared `(function(){...});` after `terser.minify(..., {compress: true})`. A bare function expression is side-effect free, so compress deletes it and both sides became the empty string: the run reported 2,147 of 2,153 modules "equal". The negative control (pair a bundle module with a different module's readable factory) matched 300 of 300 pairs, which exposed it. `b124_lib.js` now wraps the code in a call (`__n(...)`), and the same controls are part of the committed evidence. Any earlier minified-JS comparison in this corpus that relied on a parenthesised minify would need the same check; none was found by `rg -n "terser|minify" niagara5-block*.md` (no hit outside this block).

**Controls (`evidence/b124/controls.json`, 120 random true pairs per pool, fixed seed):**

| Pool | Baseline (true pair keeps its tier) | Wrong-pair matches | String-literal mutation detected | Operator-flip mutation detected |
|---|---|---|---|---|
| AST tiers (821 modules) | 120 of 120 | 0 | 103 of 103 | 63 of 63 |
| Skeleton tier (1,315 modules) | 120 of 120 | 0 | 113 of 119 | 0 of 83 |

So the two AST tiers discriminate; the skeleton tier detects renamed/changed strings and property names but is blind to a flipped operator by construction, which is why it is reported as a separate, weaker class and never added to the proven count.

## 124.4 — B119-G1 step 2 result per class `[CERT-hw]`

`evidence/b124/modules.tsv` (2,315 rows: module, id, bytes, class, readable path, tier):

| Class | Modules | Bytes of module code | Meaning |
|---|---|---|---|
| IDENTICAL-AFTER-MINIFY | 2 | 14,286 | formatting and names only |
| SEMANTIC-MATCH | 831 | 1,227,941 | AST-equal after the same minifier pass |
| HBS-RECOMPILE-MATCH | 142 | 306,031 | compiled template equals a re-run of the shipped Handlebars compiler (§124.5) |
| SKELETON-MATCH | 1,315 | 3,629,455 | same names and literals; AST differs (§124.4a) |
| EMPTY-STUB | 4 | 1,649 | `define("id",function(){})` or a deps-only aggregator |
| STUB-OR-VENDOR-WRAPPER | 19 | 1,292 | readable file has no `define` (doc-only typedefs, global scripts hoisted into the prelude) or the bundle module is a vendor UMD wrapper `define("id",t)` (§124.6) |
| DIFFERS | 2 | 26,000 | see below |
| **Total** | **2,315** | | |

**124.4a Why 1,315 modules are only skeleton matches.** Sampled diffs show the readable file and the bundle module are two different Babel transpilations of the same source, not one output minified: the readable class form is an arrow-function IIFE (`return (() => { function t(e) { ... _classCallCheck(this, t) ...`), the bundle form is `_inherits(c, e), _createClass(c, [{key: "merge", value: ...}])`; the readable form keeps `var i = this;` aliases the bundle inlines. Mangled parameter order also differs. Comparing them after any minifier therefore cannot converge for class-heavy modules, and both terser and uglify-js were tried (§124.7). 813 of the 1,315 also have the same first-occurrence order of names (`ordered` flag in `modules.tsv`); the median compressed-size ratio readable:bundle is 1.49 (range 1.08 to 2.30).

**The 2 DIFFERS** are `nmodule/webChart/rc/ChartWidget` (23,219 B; readable literal `js-tab-samplingCommand` where the bundle has `js-tab-` plus a variable) and `nmodule/webEditors/rc/fe/baja/OverrideRelTimeEditor` (2,781 B; `js-durationSelect`, `js-relTime` present only in the readable text). Both are consistent with a constant string being propagated in one build and not the other, but that is `[INFER]`: no per-function proof was made (child gap B124-G3).

**Per-bundle numbers** are in `evidence/b124/bundles.tsv` (columns `proven_js_modules`, `skeleton_modules`, `hbs_proven`, `pct_bytes_proven`, `pct_bytes_proven_or_skeleton`). The biggest ones:

| Bundle | Bytes | Modules | AST-proven | Skeleton | Templates recompiled | % bytes proven | % proven or skeleton |
|---|---|---|---|---|---|---|---|
| `docDeveloper/JsPlayground` | 2,946,323 | 3 | 0 | 1 | 0 | 0.12 | 0.21 |
| `webEditors` | 959,642 | 432 | 169 | 227 | 33 | 35.32 | 99.50 |
| `maxpro` | 594,634 | 6 | 0 | 1 | 0 | 0.37 | 1.82 |
| `analytics` | 527,895 | 179 | 79 | 58 | 41 | 51.00 | 99.94 |
| `uxBuilder` | 382,030 | 115 | 5 | 110 | 0 | 2.72 | 99.95 |
| `bajaScript` (`bs`) | 363,641 | 203 | 146 | 55 | 0 | 49.17 | 99.89 |
| `totpAuth` | 313,623 | 7 | 0 | 1 | 4 | 1.84 | 3.33 |

Three bundles (`docDeveloper`, `maxpro`, `totpAuth`) are dominated by bundled vendor libraries (§124.6). 22 of the 72 bundles have 0 AST-proven JS modules (small ones whose modules are class-heavy, plus those three); 64 of 72 have at least 95% of their bytes either proven or skeleton-matched.

## 124.5 — Compiled Handlebars templates: 142 of 142 `hbs!` modules recompile to the bundle's template spec `[CERT-hw]`

`evidence/b124/bundle_hbs.js` loads the Handlebars build Tridium ships (`organized/js/extracted/rc/handlebars/handlebars.js`, header `handlebars v4.7.9`, sha256 `b942e021f95685bc22345b93929849f28e2f95e2e6d0aba63c4651fefc26e185`), runs `Handlebars.precompile` over each `.hbs` file, and compares the object with the argument of `e.template(...)` inside the bundle's `hbs!` module after the same normalisation as §124.3. **142 of 142 are equal** (`evidence/b124/hbs.tsv`; includes `hbs!bajaux/container/error` shared by the `bajaui` and `hx` bundles). Because the spec embeds `loc:{start:{line,column}}` for every expression, a match also ties the bundle to the template's exact text and layout. The 142 modules total 306,031 B (3.29% of all bundle bytes).

## 124.6 — B119-G1 step 4 (bytes outside `define` modules): 243,528 of 288,711 prelude bytes proven; 3,761,256 vendor bytes are not `[CERT-hw]`

`evidence/b124/bundle_segments.js` accounts for the other bundle bytes (`evidence/b124/segments.tsv`):

- **Hoisted prelude (1,273 statements, 288,711 B):** each Babel helper or hoisted script statement is matched to a same-named top-level statement of a readable file of the same module (terser first, uglify-js as a second oracle). **1,260 statements (243,528 B) proven** (1,258 in the same module, 2 in another). **13 statements (45,183 B) not proven:** 8 renamed Babel helpers in `maxpro` (`_classCallCheck2` ... `_setPrototypeOf2`, no readable file carries those names), `maxpro` `protocolFormater` and `MJPEG`, `smartTableHx` `Save` (24-char shingle overlap 0.868) and `SmartTable` (0.985), `totpAuth` `qrcode` (0.707). For `Save` the first divergence is `return a=e.which,!!save.isControlKey(a)||(save.modified(),!0)` in the bundle against `save.isControlKey(a)||save.modified(),!0` in the readable file, which both return `true`; this is a boolean re-expression, not a behaviour change, but it is `[INFER]` (hand-read of one divergence).
- **Vendor UMD segments (3,761,256 B, 40.42% of all bytes): not proven.** `docDeveloper` 2,897,029 B (Babel standalone), `maxpro` 564,111 + 10,340 + 2,380 B (video.js and two small scripts), `totpAuth` 282,994 + 229 B (forge, qrcode), `js` UMD 1,410 B, `cloudLink` 843 + 59 B, `workbench` `findCommands` IIFE 1,861 B. A shipped readable counterpart exists for the large ones (`ext/@babel/standalone/babel.min.js` 3,073,951 B, `video-js.min.js` 560,398 B, `forge.min.js` 283,280 B) but the texts differ: the bundle wraps `typeof exports` as `("undefined"==typeof exports?"undefined":_typeof(exports))`, the shipped file has `"object"==typeof exports` (`grep -c "_typeof(exports)"` = 0 in all three shipped files, 1 or more in the bundle head), i.e. the build ran Babel over the vendor file and re-minified it. Raw 128-byte chunk coverage against the best counterpart is 54% (Babel), 29% (video.js), 9% (forge). `[INFER]` for "bundle segment = transformed copy of the shipped vendor file"; `[CERT-hw]` for "not byte- or AST-equal under the oracles used".
- **19 wrapper/stub modules:** the readable file has no `define` (3 doc-only `typedefs.js`, 5 `smartTableHx` global scripts whose code is in the hoisted prelude, `naxisVideoRequireJsConfig`, `MissingDataConfigEditor`, `BroadcastChannel`, the two `maxpro` scripts `protocolFormater` and `mjpegvideo`) or the bundle module is a one-line `define("id",t)` whose body is the vendor UMD function above (`babel.min`, `video-js`, `videojsfmp4`, `std.video.player`, `forge.min`, `qrcode`).

## 124.7 — B119-G1 step 3 NARROWED: the minifier is terser-family, consistent with terser 5.7.2 or earlier or uglify-js 3.x; no release and no build configuration is identifiable `[CERT-hw]`

There is no banner naming a tool and no source-map comment. Fingerprint evidence, all reproducible (`evidence/b124/helper_pattern.js`, `evidence/b124/minifier_fingerprint.js`, outputs `helper-pattern.txt`, `fingerprint.json`):

- **Output shape.** The bundles minify the Babel `_typeof` helper to `return(_typeof=<fn>)(e)`. Probe over 15 installed releases: terser 4.8.1, 5.5.1, 5.6.1, 5.7.2 and uglify-js 3.19.3 produce that shape; terser 5.9.0 and every later release tested (5.10.0, 5.12.1, 5.14.2, 5.19.4, 5.26.0, 5.31.6, 5.36.0, 5.39.2, 5.43.1, 5.51.2) emit `return _typeof=<fn>,_typeof(e)` instead. The 5.8.0 release was not tested, so the flip is between 5.7.2 and 5.9.0.
- **Name mangling** in the bundles follows a whole-file character-frequency order (`e,t,n,r,i,...`); a single module alone gets different names (`E` first in terser 5.51.2 for `bajaux/events`), so an exact byte reproduction needs the whole concatenated input, which the readable tree does not give.
- **Whole-module reproduction rate** (100 random modules, names canonicalised by one neutral pass): terser 14 to 15 for every release from 5.5.1 to 5.51.2, uglify-js 0. The releases are not discriminated by it (the residual differences are the two-Babel-passes effect of §124.4a).
- **Build structure:** named `define("nmodule/<module>/rc/<path>",[deps],function(){...})` modules, `hbs!` templates precompiled by the Handlebars plugin, `require.config`/`requirejs.config` snippets kept as plain statements, all inside one file per module: an r.js-style AMD optimizer. The optimizer config (`grunt-niagara` successor) is not in the install: [Block 79] §79.4's narrowing still stands (`blocked-on-source`).

## 124.8 — B119-G1 step 5: tally, overall and by module

Byte ledger over the 72 files (9,305,969 B; `evidence/b124/summary.txt`, `bundles.tsv`):

| Part | Bytes | Share |
|---|---|---|
| AST-proven JS modules (IDENTICAL + SEMANTIC) | 1,242,227 | 13.35% |
| Templates recompiled from readable `.hbs` | 306,031 | 3.29% |
| Prelude statements proven (helpers, hoisted scripts) | 243,528 | 2.62% |
| Other segments proven (`require.config`, shims) | 779 | 0.01% |
| **Proven readable source, total** | **1,792,565** | **19.26%** |
| Skeleton-matched modules (names and literals only) | 3,629,455 | 39.00% |
| Vendor UMD segments, not proven | 3,761,256 | 40.42% |
| Prelude statements not proven | 45,183 | 0.49% |
| Stubs and wrappers | 2,941 | 0.03% |
| DIFFERS | 26,000 | 0.28% |
| Glue (banner, commas, separators) | 49,861 | 0.54% |

By module count: 975 of 2,315 (42.1%) proven (833 JS + 142 templates), 1,315 (56.8%) skeleton, 23 stubs or wrappers, 2 DIFFERS; **2,290 of 2,315 (98.9%) have a readable counterpart whose names and literals match or which is proven equal.** Excluding the vendor segments, the Tridium-authored bundle bytes are 5,544,713 and the proven share is 32.3%, proven or skeleton 97.8%. `[INFER]` for reading the skeleton class as "same code": it is a weaker statement and the controls show it misses operator changes.

## 124.9 — B119-G1 step 6: audit of the corpus blocks that cite `*.built.min.js`

Each claim re-read against `modules.tsv` and the bundle files:

| Block | Claim | Result |
|---|---|---|
| [Block 21] §21.2 | Babel helper names in `bs.built.min.js` (`_toConsumableArray`, `_arrayWithoutHoles`, `_callSuper`, `_getPrototypeOf`) and in `bajaux.built.min.js` (`_defineAccessor`, `_superPropGet`, `_get`); literal `define("bajaux/events"`; `define(` at offset 5980 | **Confirmed**: all seven helper names are prelude statements of the two bundles (`bundles.tsv` census, `grep -bo 'define('` → first hit 5980), `bajaux/events` is the first module. **Size wrong by 16 bytes:** `bs.built.min.js` is 363,641 B, not 363,625; better citation: `rc/events.js` is SEMANTIC-MATCH to the module (`modules.tsv`, `bajaux/events`, tier `compress`). Pointer added to [Block 21] |
| [Block 4] | `JsPlayground.built.min.js` = "JS Playground widget resources" | **Refined**: 2,897,029 of its 2,946,323 B (98.3%) are the bundled Babel standalone; the Tridium content is 2 modules (`JsPlaygroundWidget` 2,609 B, one template 1,987 B). Pointer added to [Block 4] |
| [Block 75] §75.3 | N4 vs N5 `uxBuilder` bundle | Already corrected by [Block 119] §119.6; unchanged |
| [Block 79] §79.2 | 115 named `define` ids = 115 source files, "every `rc/` source file concatenated" | **Confirmed and strengthened**: the 115 ids map to 115 distinct readable files, 5 AST-equal and 110 skeleton-matched. Not literally "concatenated": the two are separate Babel builds (§124.4a). No edit needed |
| [Block 102] | ORD string of `BUxBuilderJsBuild` | Java-side string, no JS claim; unchanged |
| [Block 119] §119.3 | bundle banner and count | **Corrected**, §124.10 |
| [Block 122] B122-G4 | browser-side path through `xprotect.built.min.js` | **Better citation exists**: the 5 modules resolve to `xprotect/rc/xprotect/{XProtectSession,xprotectUtils}.js` (AST-equal) and `{XProtectCameraSession,XProtectCamera,XProtectVideoStream}.js` (skeleton); read those instead of the bundle. Pointer added to [Block 122] |

## 124.10 — Corrections to earlier blocks

- **[Block 119] §119.3** says 71 per-module bundles carry the banner `@copyright 2026 Tridium`. Measured: **72 `*.built.min.js` files** (71 Tridium bundles + the vendor hbs plugin), of which **57** start with that banner (§124.1). Scope clarification for the count (the 71 is right for Tridium-built files) and a correction for the banner. It also says bundle membership is `[INFER]`: now measured for all 2,315 modules, with the strength per class in §124.4.
- **[Block 21] §21.2** gives 363,625 bytes for `bs.built.min.js`; the file is 363,641 B (`wc -c`; [Block 119] already used 363,641).
- No claim in [Block 79] or [Block 102] is contradicted. Pointers are added in [Block 4], [Block 21], [Block 119] and [Block 122] (§14: original text kept).

## 124.11 — Connections

- Closes [Block 119] B119-G1 (§119.8) and resolves its `[INFER]` (bundle membership). Uses [Block 119]'s minified census (72 of its 132 truly minified files) and its source-map finding (0 maps for any bundle): the mapping here replaces what a source map would have given.
- [Block 79] §79.2 (uxBuilder 115 = 115) is confirmed per file; §79.4 (`grunt-niagara` config unavailable) is why the minifier identity stays open.
- Related method note: [Block 115]/[Block 116] concern Java decompilation; nothing here is decompiled, every bundle byte is the vendor's own.
- The `_typeof` probe and the vacuous-compare bug are candidates for the kit's method notes (a test whose two sides can both be empty proves nothing): recorded, not filed.

## 124.12 — Child gaps opened

- **B124-G1** (medium) — Upgrade the 1,315 skeleton modules to an AST proof by reproducing the second Babel build. Needs `@babel/core` with the preset targets and helper options that produce `_inherits(c,e),_createClass(...)`, then the bundle minifier; the configuration is not shipped, so it is inferred by trial. **requires-execution** (npm fetch, runs Babel). coverage-check: `rg -il "babel" niagara5-block*.md` → [Block 21], [Block 79], [Block 119], this block; none reproduces a build. measured-by: number of the 1,315 that become AST-equal (baseline 831 + 2 of 2,315).
- **B124-G2** (low) — Prove the vendor segments (Babel standalone 2,897,029 B, video.js, forge, qrcode) are the shipped `ext/` files run through Babel's `typeof` transform and the minifier; would move up to 3,761,256 B (40.42%) from unproven. **requires-execution**. coverage-check: `rg -il "standalone|video-js|forge" niagara5-block*.md` → [Block 4], [Block 119] mention them, none compares bytes. measured-by: raw chunk coverage or AST equality of each segment against its transformed counterpart (baseline 54%, 29%, 9%).
- **B124-G3** (low) — Hand-verify the 2 DIFFERS (`ChartWidget`, `OverrideRelTimeEditor`) and the 13 unproven prelude statements (§124.6): decide equal, constant-propagation or a real difference per function. **Investigable read-only.** coverage-check: `modules.tsv` and `segments.tsv` rows with class `DIFFERS` and proof `UNPROVEN`; no block cites them. measured-by: number of the 15 resolved.
- **B124-G4** (low) — Identify the minifier release and options: bisect terser 5.7.2 to 5.9.0 (5.8.0 untested) and uglify-js 3.x, and try the mangle and compress flags against whole-bundle reproduction (needs the readable inputs concatenated in bundle order with the hoisted helpers de-duplicated). **requires-execution**; the build configuration itself stays **blocked-on-source** ([Block 79] §79.4). coverage-check: `rg -il "terser|uglify|r\.js" niagara5-block*.md` → only [Block 79]. measured-by: byte-equal bundles out of 72 (baseline 0).
- **B124-G5** (low) — Readable-to-bundle direction: which readable `rc/**/*.js` files of the 71 modules are not registered in any `define` (dead or separately loaded files), so a claim about a module can say whether the bundle even contains it. **Investigable read-only.** coverage-check: `rg -il "not bundled|unbundled" niagara5-block*.md` → no hit. measured-by: readable files without a `modules.tsv` row, per module.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 72 `*.built.min.js` files, 9,305,969 B, 2,315 named `define` modules; anonymous `define(` only in 2 vendor bundles | [CERT-hw] | `evidence/b124/bundles.tsv`, `evidence/b124/summary.txt`, `evidence/b124/bundle_census.js` |
| 2 | 57 of 72 start with the 2026 banner; 0 have a `sourceMappingURL` comment | [CERT-hw] | `organized/*/extracted/rc/*.built.min.js` (`head -c`, `grep sourceMappingURL`), `evidence/b124/bundles.tsv` column `sourceMappingURL` |
| 3 | All 2,315 ids resolve to a readable file; 4 via r.js alias | [CERT-hw] | `evidence/b124/modules.tsv` (columns `readable`, `alias`), `evidence/b124/bundle_equiv.js` |
| 4 | Class counts 2 / 831 / 142 / 1,315 / 4 / 19 / 2 | [CERT-hw] | `evidence/b124/modules.tsv`, `evidence/b124/summary.txt` |
| 5 | The AST tiers reject wrong pairs (0 of 120) and detect 103 of 103 string and 63 of 63 operator mutations | [CERT-hw] | `evidence/b124/controls.json`, `evidence/b124/bundle_controls.js` |
| 6 | The skeleton tier is blind to operator flips (0 of 83) and misses 6 of 119 string mutations | [CERT-hw] | `evidence/b124/controls.json` |
| 7 | The first oracle was vacuous (empty output both sides) and the negative control exposed it | [CERT-hw] | `evidence/b124/README.md` (method note), `evidence/b124/b124_lib.js` (`__n(` wrapper comment) |
| 8 | 142 of 142 `hbs!` modules equal `Handlebars.precompile` of the shipped `.hbs` with the shipped 4.7.9 compiler | [CERT-hw] | `evidence/b124/hbs.tsv`, `evidence/b124/bundle_hbs.js`, `organized/js/extracted/rc/handlebars/handlebars.js` (sha256 `b942e021f95685bc22345b93929849f28e2f95e2e6d0aba63c4651fefc26e185`) |
| 9 | Prelude: 1,260 of 1,273 statements proven (243,528 of 288,711 B) | [CERT-hw] | `evidence/b124/segments.tsv`, `evidence/b124/bundle_segments.js` |
| 10 | Vendor segments 3,761,256 B are not equal to the shipped vendor files; shipped files have no `_typeof(exports)` | [CERT-hw] | `evidence/b124/segments.tsv`, `grep -c "_typeof(exports)"` on `organized/docDeveloper/extracted/ext/@babel/standalone/babel.min.js`, `organized/totpAuth/extracted/ext/forge/forge.min.js`, `organized/maxpro/extracted/ext/std-video-player/dependency/video-js.min.js` |
| 11 | The bundle segment is a Babel-transformed, re-minified copy of the shipped vendor file | [INFER] | §124.6: `typeof` wrapper difference plus size closeness (2,897,029 vs 3,073,951 B), not proven |
| 12 | Minifier output shape matches terser 4.8.1 to 5.7.2 and uglify-js 3.19.3, not terser 5.9.0 and later | [CERT-hw] | `evidence/b124/helper-pattern.txt`, `evidence/b124/helper_pattern.js` |
| 13 | No release is discriminated by whole-module reproduction (terser 14 to 15 of 100, uglify-js 0) | [CERT-hw] | `evidence/b124/fingerprint.json`, `evidence/b124/minifier_fingerprint.js` |
| 14 | The two Babel outputs differ in class form (arrow IIFE vs `_inherits/_createClass`) | [CERT-hw] | `evidence/b124/modules.tsv` (skeleton rows), e.g. `organized/webEditors/extracted/rc/wb/commands/RelationMarkCommand.js` vs the same id in `organized/webEditors/extracted/rc/webEditors.built.min.js` |
| 15 | Byte ledger: 19.26% proven, 39.00% skeleton, 40.42% vendor unproven | [CERT-hw] | `evidence/b124/summary.txt`, `evidence/b124/bundles.tsv` |
| 16 | [Block 79]'s 115 = 115 holds per file; [Block 21]'s size is off by 16 B | [CERT-hw] | `evidence/b124/modules.tsv` (`uxBuilder` rows), `wc -c organized/bajaScript/extracted/rc/bs.built.min.js` = 363641 |
| 17 | 2 DIFFERS are constant-propagation differences | [INFER] | §124.4 (literal sets only), not hand-verified per function |
| 18 | `Save` divergence is a behaviour-preserving boolean re-expression | [INFER] | one hand-read divergence, `evidence/b124/segments.tsv` row `Save` |
| 19 | The optimizer is r.js-style AMD; its config is not shipped | [CERT] | `organized/bajaux/extracted/rc/bajaux.built.min.js` (named `define` calls), `niagara5-block79.md` §79.4 |

**Tally:** `[CERT-hw]` 16 rows · `[CERT]` 1 row · `[INFER]` 3 rows · `[INFER]`/`[CERT*]` = 3/17 = 0.18. Block type: **evidence** (measurement plus a validated oracle).

**Artifacts:** `evidence/b124/` (`bundle_census.js`, `b124_lib.js`, `bundle_equiv.js`, `bundle_hbs.js`, `bundle_segments.js`, `bundle_controls.js`, `minifier_fingerprint.js`, `helper_pattern.js`, `bundle_tally.py`, `README.md`, `bundles.tsv`, `modules.tsv`, `hbs.tsv`, `segments.tsv`, `summary.txt`, `controls.json`, `fingerprint.json`, `helper-pattern.txt`); scratch JSON in `organized/_evidence/b124/`.

## 124.13 — Reproduction and commits

Commands are in `evidence/b124/README.md` (about 7 minutes for `bundle_equiv.js`). Tools installed 2026-09-29 from the npm registry: acorn 8.18.0, terser 5.51.2 and 14 older terser releases as aliases, uglify-js 3.19.3, Node v24.19.0. Commits on `feat/n5-wave20`: `f31c89a` (census, library, equivalence scripts), `dfca025` (template and segment scripts), `3e64ef7` (controls, fingerprint probes, tally, README), `62f3ee1` (data tables), then the block, state and pointer commits.
