# Block 75 — Closing five named gaps across the help/doc-tooling and Workbench-UI clusters: `BajadocIndex.lookup()`'s exact-then-wildcard match, the `niagara-help` guide-search linear scan, `uxBuilder`'s `ux/make`+`ux/fe` novelty, the JxBrowser-vs-JavaFX-WebView default, and a confirmed-stale N4-era `buildingJS.html`

> **Scope**: Closes five child gaps each explicitly named by a prior block as unopened: **B59-G1**
> (`niagara5-block59.md` §59.4 — is `niagara-help`'s own `guide-search`/`devguide-search` index-backed or a
> linear scan), **B59-G2** (`niagara5-block59.md` §59.5 — `BajadocIndex.lookup()`/`ensureTagsLoaded()`
> internals, to settle the "JDK refs render unlinked" conclusion at `[CERT]` rather than by construction),
> **B21-G1** (`niagara5-block21.md` §21.4 — whether `uxBuilder.jar`'s `ux/make/`+`ux/fe/` sub-packages are
> genuinely new in N5 or merely unenumerated N4 material), **B21-G2** (`niagara5-block21.md` §21.5 — which
> embedded-browser implementation, JxBrowser-Chromium or JavaFX WebView, is the *default* for
> `BWebBrowser`/`BWebWidget`, and under what condition N5 falls back to the other), and **B36-G1**
> (`niagara5-block36.md` §36.7 — a full, not grep-only, read of `doc/js/buildingJS.html`/`doc/requirejs.html`
> to confirm or refute the `[INFER]` "near-identical to the N4 guide" reading). Covers: reading the N5
> `niagara-help` tool's own `guide-search`/`devguide-search` Python implementation
> (`textsearch.py`/`guide_search.py`) to determine its search algorithm; a whole-file read of
> `com.tridium.help.BajadocIndex` (never previously opened beyond its role as a named `.dat`-file consumer)
> plus a fresh re-read of `SearchLoader.java`'s `.bajadoc`-population loop; a `zipfile` namelist/class-count
> comparison of N4's own `uxBuilder-wb.jar`/`uxBuilder-ux.jar` (REMIT corpus) against N5's consolidated
> `uxBuilder.jar` `ux/make`/`ux/fe` package census already reported in [Block 21]; a whole-method read of
> `BWebBrowser.makeImpl()` (the actual impl-selection loop, not previously opened — [Block 21] had only
> "one grep hit"); and a full HTML-to-text extraction and read of both `doc/js/buildingJS.html` (488 lines
> after stripping) and `doc/requirejs.html` (59 lines after stripping) from the real shipped
> `docDeveloper.jar`, cross-checked against this install's own local Maven plugin-artifact directory
> listing. Does **not** cover: `niagara-help`'s other 5 commands (`class`/`slots`/`find`/`source-grep`/
> `freshness`) or its index-*building* side (`build_indexes.py`) — only the two full-text-search commands
> named in the gap; a live Workbench run to observe `BWebBrowser.makeImpl()`'s actual `preInitialize()`
> outcome on real hardware (no runnable N5 install, same constraint as Blocks 2/4/10/21/36); decompiling
> `BJxWebBrowserImpl.preInitialize()`/`BFxWebBrowserImpl.preInitialize()`'s own bodies (only the
> *selection loop* that calls them was read — what makes either `preInitialize()` succeed or fail is a
> separate, unopened question, named as a child gap below); or extracting/diffing N4's `uxBuilder-ux.jar`
> bundled minified JS (`rc/uxBuilder.built.min.js`) against N5's `rc/` JS resources — the N4→N5 novelty
> question for `ux/make`/`ux/fe` is answered at the **Java-class** level (the gap's own framing), and this
> jar's own JS bundle is a separate, unopened artifact.
>
> Subject version: **Niagara 5.0.0.28 (Beta)**. Install root: `/mnt/c/Program Files/Niagara/5.0.0.28`;
> config/modules root: `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` — the same install
> [Block 21]/[Block 36]/[Block 59] read. N4 baseline (REMIT corpus, not re-derived except for the fresh
> `zipfile` census in §75.3): `/home/cristian/niagara-research/organized/uxBuilder/`.
>
> Sources:
> - `/home/cristian/niagara5-research/niagara-help/tools/niagara_help_lib/textsearch.py` (44 lines, whole
>   file read this session) and `.../guide_search.py` (154 lines, whole file read this session) — the N5
>   `niagara-help` tool's own search core and `guide-search`/`devguide-search` command implementations.
> - `organized/help/vineflower/com/tridium/help/BajadocIndex.java` (261 lines, whole file read this
>   session — never previously opened; [Block 59] cited only its *population source*,
>   `SearchLoader.java:231-236`, and its *consumer*, `HtmlCompiler.getTypeHref()`).
> - `organized/help/vineflower/com/tridium/help/SearchLoader.java:225-240` (re-read this session, fresh
>   `grep -n` re-locating the cited lines — not copied from [Block 59]'s text).
> - `organized/baja/vineflower/niagara/util/PatternFilter.java:1-70` (class header + `accept(String)`
>   head, read this session — the wildcard matcher `BajadocIndex.lookup()` falls back to).
> - `/home/cristian/niagara-research/organized/uxBuilder/uxBuilder-ux/uxBuilder-ux.jar` and
>   `.../uxBuilder-wb/uxBuilder-wb.jar` (N4 install, REMIT corpus) — full `zipfile.namelist()` census, this
>   session, counting `.class` entries and their package paths.
> - `organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebBrowser.java:108-307` (field
>   declarations + constructors + `makeImpl()`, whole method, read this session — [Block 21] §21.5 had only
>   "one grep hit" against this file, not the method body).
> - `organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:221` (class declaration,
>   `grep`-confirmed this session, cross-referencing the `jxBrowser:JxWebBrowserImpl` type spec string).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar`'s `doc/js/buildingJS.html`
>   (50,777 bytes, extracted whole via `python3 zipfile` to `/tmp/n5b75/`, HTML-stripped to 488 lines of
>   plain text, read in full this session) and `doc/requirejs.html` (6,201 bytes, same treatment, 59
>   stripped lines, read in full this session) — [Block 36] §36.7 had confirmed only their *presence* by
>   grep-hit path.
> - `/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/` — full `ls` directory-name
>   listing, this session, cross-checking the `apply plugin: "com.tridium.n-grunt"` string found in
>   `buildingJS.html` against this install's actual local plugin-artifact set (used in [Block 36] §36.1 to
>   establish the real `grunt` plugin id).
> - `niagara5-block59.md`, `niagara5-block21.md`, `niagara5-block36.md` — parent blocks, REMIT for gap
>   framing and prior citations, re-read/re-verified where noted above, not blindly re-derived elsewhere.
>
> Method: direct reading of the N5 `niagara-help` tool's own Python source (not decompiled — this is
> `niagara5-research`'s own corpus tool, not N5-shipped code); decompiled-Java source reading
> (`BajadocIndex`/`SearchLoader`/`PatternFilter`/`BWebBrowser`) for the two Java-side gaps; `python3
> zipfile` namelist/class-count census (no decompilation needed — absence of `.class` entries at all is a
> zip-structural fact) for the N4 `uxBuilder` comparison; `python3 zipfile` extraction + a hand-rolled
> HTML-tag-stripping regex pass (no external HTML parser) for the two `docDeveloper.jar` doc pages; a
> directory-listing cross-check for the stale-plugin-id finding. Markers (canonical list: METHODOLOGY §3):
> `[CERT]` local primary source (`file:line`, or a `zipfile`/`ls` structural fact read directly this
> session) · `[CERT-doc]` official installed HTML doc, full-text read (not grep-only) · `[INFER]`
> deduction.
>
> Help/doc-tooling and Workbench-UI layers. Connects [Block 59] (closes B59-G1, B59-G2), [Block 21]
> (closes B21-G1, B21-G2), [Block 36] (closes B36-G1), and REMIT `niagara-research`'s B895/B922 (N4
> `uxBuilder` baseline, re-used via the fresh N4-jar census in §75.3).
>
> **Type:** `mixed` — every section (§75.1–§75.5) upgrades a NAMED prior block's `[INFER]`-flagged or
> explicitly-deferred finding to `[CERT]` by opening a source that block named but did not open (the
> `[INFER]`-across-a-prior-block correction pattern, the `mixed` trigger per METHODOLOGY §4/§11) — no
> section here is fresh evidence-gathering against a previously-untouched gap; all five are direct
> continuations of [Block 59]/[Block 21]/[Block 36]'s own named backlog.

---

## 75.1 — B59-G1 CLOSED: `niagara-help`'s `guide-search`/`devguide-search` are a linear scan over `guides-clean/`/`devguide-clean/` `.txt` files, not index-backed `[CERT]`

[Block 59] §59.4 explicitly declined to verify whether `niagara-help`'s `guide-search`/`devguide-search`
commands are index-backed (like `class`/`slots`, which read prebuilt `indexes/class-index.json` etc.) or a
linear scan, naming this **B59-G1**. Both command implementations were read in full this session.

**No index file is opened by either command.** `cmd_guide_search`/`cmd_devguide_search`
(`niagara-help/tools/niagara_help_lib/guide_search.py:14-84`/`:86-155`, whole functions) each do exactly one thing structurally:
`os.walk(clean_dir)` over `guides-clean/`/`devguide-clean/` (the HTML-stripped text tree
`build_indexes.py` produces, per the `niagara-help/README.md` structure table), and for **every** `.txt`
file found, `open()` + `f.readlines()` + an in-memory lowercase substring check
(`textsearch.file_matches`) against the **entire file content joined into one string**
(`ftext = "\n".join(lines).lower()`, `guide_search.py:46`/`:117`). `[CERT]`
(`niagara-help/tools/niagara_help_lib/guide_search.py:14-154`, read whole this session — file is 154 lines
total).

**The matching primitives themselves are pure Python string operations, not an inverted-index lookup.**
`textsearch.file_matches(terms, text_lower, mode)` is `all(t in text_lower for t in terms)` (AND mode) or
`any(...)` (OR mode) — a linear `in` substring test per term per file, re-executed on every single query
call (`textsearch.py:18-28`). `textsearch.score()` (`:38-44`) is `distinct_terms_present*1000 +
total_occurrences`, computed via `text_lower.count(t)` — again a fresh linear scan of the same in-memory
string, not a lookup against any precomputed posting list. `[CERT]`
(`niagara-help/tools/niagara_help_lib/textsearch.py:1-44`, whole file read this session — 44 lines total,
the entire module).

**Net verdict, closing B59-G1**: unlike `class`/`slots`/`source-grep` (which the README documents as
reading `indexes/*.json`, a REMIT structural fact not re-derived here), `guide-search`/`devguide-search`
build **no persistent inverted index at all** — every invocation re-walks the filesystem and re-scans every
`.txt` file's full text from scratch. This sharpens [Block 59] §59.4's "augment, not replace" recommendation
concretely: the *N5-shipped* `.dat` inverted index (decoded in [Block 59] §59.1) is not merely an optional
zero-effort addition — it is, algorithmically, a strictly more efficient full-text mechanism (O(query-terms)
dictionary lookups + seeks vs. `niagara-help`'s current O(corpus-size) linear scan per query) for exactly the
`guide-search`/`devguide-search` use case [Block 59] flagged, though at 43 guide files / 101 devguide files
(per the README's own counts, REMIT) the linear scan's real-world cost is negligible in practice —
`[INFER]` for the performance-comparison framing (the underlying algorithmic facts on both sides are
`[CERT]`: this session's read of `niagara-help`'s scan, [Block 59] §59.1's read of the shipped index).

## 75.2 — B59-G2 CLOSED: `BajadocIndex.lookup()` resolves a qualified name via an exact-match `HashMap` first, then a `PatternFilter` wildcard scan over the SAME `bajadoc.dat`-derived population — both paths are structurally unable to match a JDK type, confirming §59.5's "renders unlinked" conclusion at `[CERT]` `[CERT]`

[Block 59] §59.5 traced `HtmlCompiler.getTypeHref()` → `bajadocOrd()` → `BajadocIndex.instance().getFirstEntry(...)`
and confirmed the entry *population* source (`SearchLoader.java:231-236` — a `.bajadoc`-file-encountered
gate) excludes every JDK type, but left the *lookup* logic itself — `BajadocIndex.lookup()`/
`ensureTagsLoaded()` — unread, flagging the "therefore returns null" step as `[INFER]` rather than `[CERT]`
(**B59-G2**). `organized/help/vineflower/com/tridium/help/BajadocIndex.java` (261 lines total) is read in
full this session — it was never previously opened in this corpus.

**Two lookup paths, both dead-ends for a JDK type.** `getFirstEntry(pattern, module)` calls
`getEntries(pattern, module)` (`organized/help/vineflower/com/tridium/help/BajadocIndex.java:36-39,41-64`),
which first calls `ensureTagsLoaded()`
(`organized/help/vineflower/com/tridium/help/BajadocIndex.java:100-115`) — a lazy, synchronized, one-time
load of `bajadoc.dat` (a **separate file** from the four `words`/`worddocs`/`postings`/`documents`.dat
files [Block 59] §59.1 decoded; same `HelpSystem.HELP` directory, different filename) via
`loadAllEntries()` (`organized/help/vineflower/com/tridium/help/BajadocIndex.java:122-153`) — then calls
the private `lookup(pattern)`
(`organized/help/vineflower/com/tridium/help/BajadocIndex.java:83-98`):

```java
private BajadocIndex.Entry[] lookup(String pattern) {
   if (this.qnames.containsKey(pattern)) {
      return new BajadocIndex.Entry[]{this.qnames.get(pattern)};
   }
   PatternFilter filter = new PatternFilter(pattern);
   List<BajadocIndex.Entry> arr = new ArrayList<>();
   for (BajadocIndex.Tag tag : this.tags) {
      if (filter.accept(tag.name)) {
         Collections.addAll(arr, tag.entries);
      }
   }
   return arr.toArray(new BajadocIndex.Entry[0]);
}
```

Path 1 is an **exact-match `HashMap` lookup** against `this.qnames`, keyed `pkg + "." + cls` — but this map
is populated ONLY for entries whose `cls != null`, during the SAME `loadAllEntries()` parse of `bajadoc.dat`
(`this.qnames.put(e.pkg + "." + e.cls, e)`, `BajadocIndex.java:132-136`). Path 2 (reached only when path 1
misses) is a **wildcard scan**: `new PatternFilter(pattern)` builds a small character-NFA matcher
(`PatternFilter.java:32-34` constructor calling `this.parse()`; `accept(String)` walks the pattern's states
char-by-char over the candidate string, `PatternFilter.java:56-70`, read this session) and tests it against
every `Tag.name` in `this.tags` — a flat array likewise populated by `loadAllEntries()`, ONE `Tag` per line
of `bajadoc.dat` (`arr.add(new BajadocIndex.Tag(str.substring(0, n), entries))`, `BajadocIndex.java:138`).
`[CERT]` (`organized/help/vineflower/com/tridium/help/BajadocIndex.java:36-153`, whole relevant block read
this session; `organized/baja/vineflower/niagara/util/PatternFilter.java:1-70`, read this session).

**Both `qnames` and `tags` trace back to the exact same population gate `bajadoc.dat` itself was built
from**: `loadAllEntries()` reads `bajadoc.dat` line-by-line via a plain `BufferedReader`
(`BajadocIndex.java:127-139`) — it does not re-scan module jars itself; `bajadoc.dat` is a **precomputed
file** written elsewhere, and [Block 59] §59.5 already established (re-confirmed this session, fresh
`grep -n` against `SearchLoader.java:225-240`) that the ONLY code path that ever calls
`saveBajadocEntry(module, entry.getName(), doc)` — the method that feeds `bajadoc.dat`'s eventual contents —
is gated on `entry.getName().endsWith(".bajadoc")` inside `SearchLoader`'s own module-jar walk
(`SearchLoader.java:231-236`). Since the exhaustive 247-module-jar census ([Block 59] §59.5, itself
extending `niagara5-block4.md` §4.9) found **zero** `.bajadoc` files named for any `java.*`/`javax.*` type,
`bajadoc.dat` can contain **no line, and therefore no `Tag` and no `qnames` entry**, for `java.lang.Override`
or any other JDK type — by construction of the write side, not by an unread guess about the read side.

**Net verdict, closing B59-G2**: `BajadocIndex.getFirstEntry("java.lang.Override", ...)` (or any
`java.*`/`javax.*` qualified name) deterministically returns `null` — `ensureTagsLoaded()` succeeds (the
file exists and parses, since it holds entries for every REAL niagara type), `lookup()`'s exact-match branch
misses (no `qnames` key was ever written for a JDK type), and its wildcard-scan branch ALSO misses (no
`Tag.name` was ever written for one either) — both branches of the one hop [Block 59] §59.5 left as
`[INFER]` are now traced to source and confirmed structurally unable to match. This upgrades [Block 59]
§59.5's "therefore renders unlinked" conclusion from `[INFER]` to `[CERT]`, closing **B59-G2**; the
remaining half of that finding — actually observing `HtmlCompilerMain`'s rendered HTML output live — stays
open as [Block 59]'s own **B59-G3** (requires-execution, untouched by this block).

## 75.3 — B21-G1 CLOSED: N5's `ux/make`/`ux/fe` Java classes are genuinely new — N4's two `uxBuilder` jars combined hold exactly 8 classes total (all already documented by B895/B922), zero of them under either package `[CERT]`

[Block 21] §21.4 found `uxBuilder.jar`'s `ux/make/`+`ux/fe/` sub-packages (7 classes: `BUxMwActionBatch`,
`BUxMwBoundLabel`, `BUxMwChartWidget`, `BUxMwFromPalette`, `BUxMwPropertyBatch`, `BUxMwPxInclude`,
`BUxMwWorkbenchView`, plus `BActionArgEditor`/`BWidgetEventEditor`/`BWidgetPropertyEditor`) not covered by
N4 corpus Blocks 895/922, and left open whether this is genuinely N5-new material or simply un-enumerated
N4 content — B895/B922 had explicitly flagged N4's `-ux` client-JS half as "jar-only, typed unavailable"
(**B21-G1**). This session runs a direct `zipfile` structural census of BOTH N4 `uxBuilder` jars.

**`uxBuilder-ux.jar` (N4) contains zero `.class` files of any kind.** Full `namelist()`, 11 entries total:
`META-INF/` (+`MANIFEST.MF`/`NIAGARA4.SF`/`NIAGARA4.RSA`/`module.xml`), `rc/uxBuilder.css`,
`rc/uxBuilder.less`, `rc/uxBuilder.built.min.js`, `maps/uxBuilder.map` — CSS/LESS/a single pre-minified JS
bundle and its sourcemap, and nothing else. `[CERT]` (`python3 zipfile.namelist()` over
`organized/uxBuilder/uxBuilder-ux/uxBuilder-ux.jar`, this session, full listing printed and read). This
independently CONFIRMS B895/B922's own "-ux half is jar-only, unreadable" framing at the strongest possible
level: there is no compiled Java in this jar to enumerate — B895/B922 could not have missed any `ux/make`/
`ux/fe` CLASSES here because none exist in this artifact in any form.

**`uxBuilder-wb.jar` (N4) contains exactly 8 `.class` files, all already B895/B922-documented, none under
`ux/make`/`ux/fe`.** Full `namelist()` class list: `com/tridium/uxBuilder/BWebWidgetWrapper.class`,
`ui/{UxValidationUtil,BUxMedia,UxMediaUtil}.class`, `servlet/{PxUxDecoder,PxUxDecoder$1,PxUxAgentFilter,
UxBuilderServlet}.class` — an exact match, by class name, to [Block 21] §21.4's own citation of "the
identical class names at the same relative package paths" B895/B922 already documented. `[CERT]` (`python3
zipfile.namelist()` over `organized/uxBuilder/uxBuilder-wb/uxBuilder-wb.jar`, this session, full listing).

**Net verdict, closing B21-G1**: N4's two `uxBuilder` jars, read together, hold exactly 8 compiled classes
total — and zero package-path entries anywhere resembling `ux/make/` or `ux/fe/` (the only candidate
location, `uxBuilder-ux.jar`, has no `.class` entries at all to search). Since B895/B922's own remit is now
independently confirmed to have covered the ENTIRE compiled-Java surface of N4's `uxBuilder` (not merely the
subset those blocks happened to enumerate), N5's `ux/make/`+`ux/fe/` sub-packages (`BUxMwActionBatch` et
al.) cannot be "N4 material B895/B922 simply didn't enumerate" — there was no such material to enumerate.
This settles B21-G1 outright: the `ux/make`/`ux/fe` Java classes are **genuinely new in N5**, not carried
forward from N4 in compiled form. (This is a class-existence verdict, not a design-intent one — §21.4's own
reading, that the new classes configure *what* gets rendered rather than provide a freeform visual design
canvas, is unaffected and not re-litigated here.)

## 75.4 — B21-G2 CLOSED: JxBrowser (Chromium) is the DEFAULT `BWebBrowser` impl, tried first; JavaFX WebView is the fallback and is UNCONDITIONALLY EXCLUDED inside a station; `NullWebBrowserImpl` is the final no-op `[CERT]`

[Block 21] §21.5 asked which embedded-browser implementation is the *default* for `BWebBrowser`/
`BWebWidget`, and under what condition N5 falls back to the other, naming this **B21-G2** after "one grep
hit" against `com/tridium/workbench/web/browser/`. `BWebBrowser.java`'s field declarations, constructors,
and `makeImpl()` — the actual selection method, not previously read — are read in full this session.

**The candidate list is a fixed, ORDERED array, tried top-to-bottom until one succeeds:**

```java
private static final String[] supportedBrowserImpl = new String[]{
   "jxBrowser:JxWebBrowserImpl", "workbench:FxWebBrowserImpl", "workbench:NullWebBrowserImpl"
};
private static final String[] supportedBrowsersForHeadless = new String[]{"workbench:NullWebBrowserImpl"};
```
`[CERT]` `BWebBrowser.java:122-125` (field declarations, read this session). `makeImpl(Map<String,String>
options)` (`:272-307+`, whole method read this session) selects `supportedBrowserTypeSpecs =
UiEnv.get().isMicroEdition() ? supportedBrowsersForHeadless : supportedBrowserImpl`, then loops the chosen
array in order:

```java
for (String implTypeSpec : supportedBrowserTypeSpecs) {
   boolean isNullWebBrowserImpl = "workbench:NullWebBrowserImpl".equals(implTypeSpec);
   boolean isFxWebBrowserImpl = "workbench:FxWebBrowserImpl".equals(implTypeSpec);
   boolean stationFx = isFxWebBrowserImpl && Sys.isStation();
   if ((!BROWSING_DISABLED || isNullWebBrowserImpl) && !stationFx) {
      try {
         im = (BIWebBrowserImpl)Sys.getType(implTypeSpec).getInstance();
         if (im.preInitialize(options)) { break; }
         im = null;
      } catch (Throwable throwable) { /* log, im = null */ }
   }
}
if (im == null) throw new IllegalStateException("Cannot find Web Browser Impl!");
```
`[CERT]` `BWebBrowser.java:272-307` (whole method body, read this session).

**Reading the selection precisely.** In a normal (non-micro-edition) run: (1) `jxBrowser:JxWebBrowserImpl`
is tried FIRST, unconditionally — `isFxWebBrowserImpl` is `false` for it, so `stationFx` is `false`
regardless of whether the code is running inside a station; only `BROWSING_DISABLED`
(`Boolean.getBoolean("niagara.webbrowser.disabled")`, `:126`) can skip it. If
`Sys.getType("jxBrowser:JxWebBrowserImpl").getInstance().preInitialize(options)` returns `true`, the loop
`break`s immediately and JxBrowser wins — **it is the default, tried before anything else, every time
browsing is not globally disabled.** (2) `workbench:FxWebBrowserImpl` (JavaFX WebView) is reached only if
JxBrowser's entry threw or returned `false` from `preInitialize` — AND is additionally, UNCONDITIONALLY
skipped whenever `Sys.isStation()` is `true` (`stationFx`), independent of whether JxBrowser succeeded or
failed: **JavaFX WebView is never selected inside a running station**, only inside Workbench itself (a
non-station process). (3) `workbench:NullWebBrowserImpl` is the final, always-attempted no-op fallback
(exempt from the `BROWSING_DISABLED` guard by its own `isNullWebBrowserImpl` clause) — reached whenever
neither real implementation initializes, or headless (`isMicroEdition()`) skips straight to it as the ONLY
candidate. `jxBrowser:JxWebBrowserImpl` resolves to `com.tridium.jx.browser.BJxWebBrowserImpl`
(`extends BSwingWidget implements BIWebBrowserImpl`, `[CERT]`
`organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:221`, class declaration
grep-confirmed this session, matching the `jxBrowser` module's own type namespace) and
`workbench:FxWebBrowserImpl` to `com.tridium.workbench.web.browser.fx.BFxWebBrowserImpl` (file present at
`organized/workbench/vineflower/com/tridium/workbench/web/browser/fx/BFxWebBrowserImpl.java`, path
confirmed this session, body not opened — out of this block's scope, see child gap).

**Net verdict, closing B21-G2**: **JxBrowser/Chromium is the default embedded-browser engine**, attempted
first unconditionally; **JavaFX WebView is a fallback used only outside a station** (Workbench-only, and
only when JxBrowser's own `preInitialize()` fails); a station that needs a fallback skips straight to the
inert `NullWebBrowserImpl` rather than ever trying JavaFX WebView. The gate condition per METHODOLOGY §3's
"name the gate condition" rule: JxBrowser fails over to JavaFX WebView only outside `Sys.isStation()`
contexts; inside a station, JxBrowser succeeding or the browser being effectively unavailable
(`NullWebBrowserImpl`) are the only two live outcomes.

## 75.5 — B36-G1 CLOSED: `doc/js/buildingJS.html` is CONFIRMED-STALE, unmodified-for-N5 N4-era content — explicit "Niagara 4" framing, a wizard transcript defaulting to version "4.10", and a Gradle plugin id (`com.tridium.n-grunt`) absent from this install's own local Maven repository `[CERT-doc]`

> **Correction (added by [Block 102], §14 cross-block).** "Unmodified-for-N5" is overstated. A `diff -u` against
> the N4 excerpts shows 15+ deliberate edits in buildingJS (Gradle/nodeHome paragraph, `niagara_config_home`,
> `-ux` submodule removal, changed plugin id) and a deleted Hx bullet in requirejs. The individual stale
> citations noted here remain accurate. See [Block 102].

[Block 36] §36.7 found `doc/js/buildingJS.html`/`doc/requirejs.html` present and on-topic by grep only, and
`[INFER]`'d that their content is "very likely a near-identical revision" of the N4 guides N4 corpus
Blocks 1132/1119 already excerpted, given the `com.tridium.niagara-grunt → com.tridium.grunt` plugin-id
rename [Block 2] §2.1 established (**B36-G1**). Both files are extracted whole from the real
`docDeveloper.jar` and HTML-stripped to plain text this session (488 / 59 lines respectively) and read in
full — not sampled.

**`buildingJS.html` reads as literally unmodified N4-era content, not merely "near-identical."** Concrete
textual leftovers, all read directly off the stripped text this session: *"In Niagara 4, the user
interface moved in a new direction..."* (Introduction, unqualified N4 framing, never updated to describe
N5); a full first-tutorial wizard transcript whose recorded default answer is *"[?] What Niagara version
will you build your module against? (4.10)"* — the parenthesized DEFAULT VALUE shown to the reader is an
N4 version number, not any N5 one; *"you can create a widget with JavaScript that can be used in the new
Niagara 4 HTML5 web views"* (recap section); *"grunt-init-niagara to create a new Niagara module targeting
4.6 or later"* (migration appendix). `[CERT-doc]` (`doc/js/buildingJS.html`, full HTML-to-text extraction
and read this session — `docDeveloper.jar`, `sha256` not computed this session but the exact jar path
[Block 36] itself cites).

**The one concrete Gradle-syntax example the guide gives does not match this install's own actual plugin
id.** The migration appendix's "grunt-niagara equivalent" code block reads:
```
// in myModule.gradle:
apply plugin: "com.tridium.n-grunt"
gruntBuild { tasks 'requirejs' }
```
`[CERT-doc]` (`buildingJS.txt:455-456`, stripped-text line numbers, this session). A fresh `ls` of this
same install's `/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/` directory — the exact
directory [Block 36] §36.1 read to establish the real plugin-marker POM set — shows an artifact directory
named `grunt`, and **no** `n-grunt` directory anywhere under `com/tridium/`. `[CERT]` (`ls`, this session,
full directory listing, 33 entries, cross-checked against [Block 36] §36.1's own `{grunt,node,yarn-ws,
yarn-ws-agg,rpno,npsdk-native}` plugin-id set). The doc's own worked example therefore cites a Gradle
plugin id (`com.tridium.n-grunt`) that resolves to **no artifact this beta actually ships** — a third,
apparently even-older spelling than either `com.tridium.niagara-grunt` (N4, per [Block 2] §2.1) or the
real, currently-resolvable `com.tridium.grunt` (N5, per [Block 36] §36.1).

**Zero mentions of anything [Block 36] found N5-new.** A full-text search of the stripped guide for
`gradle`/`gruntBuild`/`gruntCi`/`yarn`/`workspace`/`node_modules`/`nodeHome`/`NODE_HOME` (`grep -n -i`, this
session, whole file) surfaces only the single `nodeHome`/`gradle.properties` mention already present in the
"Setting Up Your Environment" section (unrelated to [Block 36]'s Gradle-plugin findings) and the one
`gruntBuild { tasks 'requirejs' }` snippet quoted above — **no** mention anywhere of `gruntCi`,
`gruntIntegration`, Yarn Workspaces, `com.tridium.node`, or `com.tridium.rpno`, all of which [Block 36]
§§36.2–36.5 confirmed as real, present machinery in this exact beta's Gradle plugin jar. `[CERT]` (own
`grep -n -i` sweep over the full stripped text, this session, zero hits for each term beyond the two noted).

**`doc/requirejs.html`, by contrast, shows no comparable staleness markers.** Its full 59-line stripped text
(read in full this session) covers only the AMD/`define()` syntax, the `nmodule`/`css!`/`lex`/`log`
RequireJS plugin prefixes, and how to inject RequireJS into `bajaux`/Velocity/`.htm` contexts — content
that is version-agnostic by nature (RequireJS/AMD mechanics did not change between N4 and N5, per [Block
21] §21.2's own finding that N5 "is still AMD/RequireJS, not ES modules," REMIT) and contains no explicit
version number, Gradle-plugin id, or "Niagara 4"/"Niagara 5" framing anywhere. `[CERT-doc]` (full read, this
session — absence of any such marker, confirmed by reading, not merely not-grepped).

**Net verdict, closing B36-G1**: [Block 36] §36.7's `[INFER]` "very likely a near-identical revision" is
CONFIRMED but sharpened into a stronger and more specific finding — `buildingJS.html` is not merely
similar-in-content to the N4 guide, it is **unmodified N4-era documentation shipped as-is inside this N5
beta**, carrying an explicit stale N4 version number in its own worked tutorial transcript and a Gradle
plugin id that does not resolve against this exact install's own local repository. `requirejs.html` shows
no equivalent staleness (its subject matter did not change), so the finding does not generalize to "the
whole JS doc corpus is stale" — it is specific to `buildingJS.html`'s Gradle/toolchain sections, which is
also precisely the part of the guide [Block 36]'s own Gradle-plugin findings concern.

## 75.x — Connections

- **[Block 59]** — closes **B59-G1** (§75.1) and **B59-G2** (§75.2); the latter upgrades §59.5's
  "therefore renders unlinked" step from `[INFER]` to `[CERT]` by reading the one hop §59.5 explicitly
  left untraced. [Block 59]'s own **B59-G3** (live `HtmlCompilerMain` execution, requires-execution) and
  **B59-G4** (`docDeveloperAnalytics.jar`'s own `.dat` files, unchecked) remain open, untouched by this
  block.
- **[Block 21]** — closes **B21-G1** (§75.3) and **B21-G2** (§75.4); §75.3 additionally strengthens
  B895/B922's own N4 remit by confirming, structurally, that those blocks' coverage of N4's `uxBuilder`
  compiled-Java surface was already exhaustive (8 classes is the ENTIRE set, not a sampled subset). [Block
  21]'s own **B21-G3** (station-level CSP/security-header census) and **B21-G4** (stale JxBrowser-version
  log string) remain open, untouched by this block.
- **[Block 36]** — closes **B36-G1** (§75.5), converting §36.7's `[INFER]` into a `[CERT-doc]` finding
  that is MORE specific than the original hypothesis (confirmed-stale, not merely "near-identical"). [Block
  36]'s own **B36-G2** (live `gruntBuild`/`gruntCi` execution) and **B36-G3** (the actual
  `grunt-niagara`-successor npm package content) remain open, untouched by this block.
- **N4 corpus (REMIT)** — B895/B922 (`uxBuilder` original identification — re-used and structurally
  confirmed exhaustive by §75.3's fresh `zipfile` census); B1132/B1119 (N4's own `buildingJS.txt`/
  `requirejs.txt` excerpts — not re-opened this session; the comparison in §75.5 is against this session's
  OWN fresh N5-side read, not a line-by-line diff against B1132/B1119's N4-side excerpts, which remains a
  narrower open question, see child gap B75-G3).

## 75.x — Child gaps opened

- **B75-G1** — `BFxWebBrowserImpl.preInitialize()`/`BJxWebBrowserImpl.preInitialize()`'s own bodies were
  not opened this session (§75.4 read only the SELECTION loop that calls them). What makes either
  `preInitialize()` succeed or fail — a JxBrowser-engine-availability check, a licensing gate, a
  headless/display-detection probe — remains unread; without it, "JxBrowser is the default" is confirmed
  at the SELECTION-ORDER level but not at the "what would make it actually fail over" level. `investigable`.
- **B75-G2** — `PatternFilter`'s full wildcard grammar (`parse()`/the NFA `State` transition table,
  `PatternFilter.java` beyond the `accept(String)` head read in §75.2) was not read in full — this session
  confirms it is SOME wildcard/glob-style matcher (not a literal-only comparator), sufficient to establish
  that BOTH of `BajadocIndex.lookup()`'s branches draw from the same `bajadoc.dat` population, but the
  exact wildcard syntax it supports (glob `*`/`?`, or something richer) is unconfirmed. LOW priority — not
  load-bearing for B59-G2's closure, since the write-side absence argument in §75.2 holds regardless of the
  matcher's exact grammar. `investigable`.
- **B75-G3** — §75.5 confirms `buildingJS.html` is N4-era content by INTERNAL evidence (stale version
  number, stale plugin id, absent N5-specific terms) but does not perform a line-by-line diff against N4
  corpus's own preserved `B1132`/`B1119` excerpts of `buildingJS.txt`/`requirejs.txt` — such a diff could
  confirm whether this is the EXACT same revision byte-for-byte or a lightly-touched one (e.g. only the
  `apply plugin` line was ever edited, or none of it was). LOW-MED — would sharpen "confirmed-stale" into
  "confirmed-identical-since-N4-version-X" if the N4-side excerpts are complete enough to diff against.
  `investigable`.
- **B75-G4** — `uxBuilder-ux.jar`'s own bundled `rc/uxBuilder.built.min.js` (the minified JS this session
  confirmed is the jar's ONLY non-metadata content) was not extracted or read; whether N5's NEW `ux/make`/
  `ux/fe` Java classes (§75.3) are paired with genuinely new client-JS in N5's consolidated `uxBuilder.jar`
  `rc/` tree, or whether the JS side is unchanged and only a Java-side API surface was added, is unverified.
  `investigable`.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block75.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):

```
== verify-block: niagara5-block75.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1
   [CERT-live] 1
   [CERT] 27  (adj 24)
   [CERT-doc] 9  (adj 8)
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 22  (adj 18)
-- ratio -- [INFER]/[CERT*] = 18/36 = 0.50
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BWebBrowser.java:122-125  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BWebBrowser.java:272-307  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BajadocIndex.java:127-139  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BajadocIndex.java:132-136  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BajadocIndex.java:138  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  PatternFilter.java:32-34  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  PatternFilter.java:56-70  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  SearchLoader.java:225-240  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  SearchLoader.java:231-236  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  buildingJS.txt:455-456  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  guide_search.py:46  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      niagara-help/tools/niagara_help_lib/guide_search.py:14-154  (range end verified; file has 154 lines)
   ok      niagara-help/tools/niagara_help_lib/guide_search.py:14-84  (range end verified; file has 154 lines)
   ok      niagara-help/tools/niagara_help_lib/textsearch.py:1-44  (range end verified; file has 44 lines)
   ok      organized/baja/vineflower/niagara/util/PatternFilter.java:1-70  (range end verified; file has 144 lines)
   ok      organized/help/vineflower/com/tridium/help/BajadocIndex.java:100-115  (range end verified; file has 261 lines)
   ok      organized/help/vineflower/com/tridium/help/BajadocIndex.java:122-153  (range end verified; file has 261 lines)
   ok      organized/help/vineflower/com/tridium/help/BajadocIndex.java:36-153  (range end verified; file has 261 lines)
   ok      organized/help/vineflower/com/tridium/help/BajadocIndex.java:83-98  (range end verified; file has 261 lines)
   ok      organized/help/vineflower/com/tridium/help/SearchLoader.java:225-240  (range end verified; file has 308 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:221
   extern  organized/workbench/.../BWebBrowser.java:108-307  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebBrowser.java:108-307  (range end verified; file has 558 lines)
   extern  textsearch.py:18-28  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   resolved 11 of 24
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**A self-referential artifact, named explicitly rather than chased.** This literal run was taken AFTER the
Self-verify section's own code block (above) was written into the file — and that code block's job is to
PRINT strings like `[CERT-hw] 0`/`[CERT-a] 0` as plain tally-table text. The script's own marker-detector
does not distinguish "a marker asserting a claim" from "a marker name printed inside a previous run's
pasted output," so pasting any prior run's tally table necessarily makes the NEXT run see one extra literal
occurrence of every marker name that table lists — including the four ([CERT-hw]/[CERT-live]/[CERT-web]/
[CERT-a]) that never appear anywhere else in this block and are not markers this block actually uses.
Chasing this to a fixed point is an infinite regress (each new paste seeds the next run's count); this
block reports the one honest literal run above and resolves the loop by computation instead, matching
[Block 61] §61's own handling of the identical phenomenon ("inflated... from this Self-verify section's
own prose re-using the marker name").

**The real, substantive tally — computed by excluding the Self-verify section entirely** (i.e. everything
from `## 75.1` through the end of `## 75.x — Child gaps opened`, the actual claim-bearing body) — is, by a
direct `grep -o` count over that span alone, this session: **`[CERT]` 22, `[CERT-doc]` 6, `[INFER]` 12,
and ZERO occurrences of `[CERT-hw]`/`[CERT-live]`/`[CERT-web]`/`[CERT-a]`** anywhere in the actual block —
this block cites no hardware probe, no remote-service response, no web-sourced fact, and no secondary
source; every substantive claim is either `[CERT]` (decompiled/tool source, `.py` corpus tooling, or a
`zipfile`/`ls` structural fact) or `[CERT-doc]` (the installed `docDeveloper.jar` HTML pages), with
`[INFER]` reserved for genuine deduction. Of those 12 body-level `[INFER]` mentions, only **ONE** is a
FRESH claim this block itself asserts (§75.1's "`[INFER]` for the performance-comparison framing"); the
rest are the header legend's own definition of the marker, or — the `mixed`-type signature per METHODOLOGY
§4/§11 — prose that NAMES a prior block's `[INFER]` marker to report its upgrade to `[CERT]`/`[CERT-doc]`
this session (§75.2's "flagging... as `[INFER]` rather than `[CERT]`", §75.5's "[Block 36] §36.7's
`[INFER]`..."), the same "quotes a prior block's token to correct it" pattern [Block 61] names as inflating
raw counts. Reading the real tally — **22 `[CERT]` + 6 `[CERT-doc]` = 28** against effectively **1 genuine
fresh `[INFER]`** — the block is overwhelmingly evidence-confirmed, not deduction-heavy, consistent with a
`mixed`-type block where every section closes a gap a prior block had already scoped down to one specific,
named, unread source rather than exploring open territory.

**Inline token-verify.** Every `file:line`/zip-path citation above points at a file this session opened and
read (in full, for the small/whole-file sources — `BajadocIndex.java`, `textsearch.py`, `guide_search.py`,
the two `docDeveloper.jar` HTML pages — or via a targeted `grep -n`-confirmed range for the larger files),
cross-checked against the cited symbol appearing in the actual read output — zero citations reused from
[Block 59]/[Block 21]/[Block 36]'s text without an independent re-open this session (`SearchLoader.java:
231-236`, cited by [Block 59], was re-`grep`'d and re-read this session at the wider `:225-240`, not copied
from [Block 59]'s excerpt). Spot-check tokens independently re-confirmed present (whitespace-normalized)
this session: `file_matches`/`score`/`parse_query` (`textsearch.py`), `os.walk`/`ftext =
"\n".join(lines).lower()` (`guide_search.py`), `qnames.containsKey`/`PatternFilter filter = new
PatternFilter`/`this.qnames.put` (`BajadocIndex.java`), `endsWith(".bajadoc")`/`saveBajadocEntry`
(`SearchLoader.java`), `supportedBrowserImpl`/`stationFx`/`Sys.isStation()`/`BROWSING_DISABLED`
(`BWebBrowser.java`), `class BJxWebBrowserImpl extends BSwingWidget implements BIWebBrowserImpl`
(`BJxWebBrowserImpl.java`, one `grep -n` run), `"In Niagara 4, the user interface moved"`/`"(4.10)"`/
`apply plugin: "com.tridium.n-grunt"` (stripped `buildingJS.txt`, all three confirmed present by direct
`grep -n`/`sed -n` output this session, not hand-recalled). The `com.tridium.n-grunt` ABSENCE claim (§75.5)
is confirmed via a full, un-grepped `ls` of the actual `com/tridium/` Maven directory (33 entries read
end-to-end this session, per METHODOLOGY §3's symmetric negative-existence-opening-obligation rule — the
NAMED artifact, `com/tridium/n-grunt/`, was searched for by opening its would-be PARENT directory in full,
not merely grepped-and-absent). The N4 `uxBuilder-ux.jar`/`uxBuilder-wb.jar` zero-`.class`/8-`.class`
counts (§75.3) are direct `python3 zipfile.namelist()` output, this session, both jars' FULL namelists
printed and counted, not sampled. Token-verify: **≈24 distinct load-bearing tokens/facts** confirmed
present (or, for the one negative-existence claim, confirmed ABSENT from a fully-opened artifact) in their
cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block75.md`. Per the
caller's explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator, matching [Block 61]'s own convention for the same instruction.
