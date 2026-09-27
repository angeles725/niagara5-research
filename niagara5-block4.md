# Block 4 — N5 shipped documentation: `docDeveloper.jar`'s bajadoc-XML architecture, the JavaHelp TOC, and a niagara-help-N5 rebuild recipe

> **Scope**: Closes gap **N5-G12** (the documentation Tridium ships with Niagara N5 5.0.0.28 and how to
> turn it into a searchable help index, the N5 equivalent of the N4 `niagara-help` repo at
> `/home/cristian/niagara-research/niagara-help`). Covers: the full directory/file-type census of
> `docDeveloper.jar` (222 MB uncompressed, 8,817 entries), `docDeveloperAnalytics.jar`, `docSource.jar`,
> `help.jar`, and `niagaraJavadoc.jar`; the `doc/toc.xml` JavaHelp table of contents (the Developer Guide's
> real structure); the `.bajadoc` XML format (replacing N4's static HTML bajadoc) and the `help.jar`
> classes that parse/render/search it; a census of all 247 installed module jars for module-carried
> `doc/` content; a comparison against N4's per-subsystem `docX-doc.jar` architecture
> (`/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules`); and a concrete jar→directory rebuild
> recipe for a `niagara-help-N5` corpus. Does **not** cover: the full content of every individual guide
> page (spot-read only), the `niagaraLexiconXX.jar` translation files (out of scope — not documentation),
> or building/running `HtmlCompilerMain`/`BajadocFinder` live against a real N5 station (no runnable
> `gradlew`/station in this beta install — same constraint noted in `niagara5-block2.md`).
>
> Subject version: **Niagara 5.0.0.28 (Beta)**. Install root: `/mnt/c/Program Files/Niagara/5.0.0.28`;
> config/modules root: `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28` (247 module jars). N4 baseline:
> **Honeywell OptimizerSupervisor 4.14.0.162** at `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules`
> (1,013 module jars). N4 corpus baseline (REMIT, not re-derived): `niagara-research/niagara-help` — see
> its `README.md`/`ROADMAP.md` heads, read this session for the N4 layout only.
>
> Sources (all local, read-only, censused with `python3 zipfile` — no full extraction to disk):
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` — full namelist +
>   per-entry `file_size` census; `doc/toc.xml`, `doc/bajadoc.index`, `doc/control/module-index.bajadoc`,
>   `doc/control/niagara/control/BBooleanPoint.bajadoc`, `doc/upgrade/upgradingToN5.html` read in full/large
>   excerpt (HTML-tag-stripped with a local regex script, not a library).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloperAnalytics.jar`,
>   `docSource.jar`, `help.jar` — full namelist census; `help.jar`'s full class list read (no
>   decompilation — class names/packages only, from the zip directory).
> - `/mnt/c/Program Files/Niagara/5.0.0.28/javadoc/niagaraJavadoc.jar` — full namelist census +
>   `doc/element-list` content read.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar` — **all 247 jars** censused
>   (`doc/` prefix, `.html`, `.bajadoc` entry counts per jar) to answer whether individual modules carry
>   their own doc content.
> - `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/` — directory listing (1,013 jars, doc-named
>   subset) + census of `docDeveloper-doc.jar`, `docAXtoN4Migration-doc.jar`, `docUser-doc.jar`.
> - `/home/cristian/niagara-research/niagara-help/README.md`, `ROADMAP.md` (heads only) — N4 corpus layout
>   REMIT, not re-derived.
>
> Method: `python3 zipfile` census scripts (directory-tree tallies, extension tallies, per-jar doc-content
> scan across all 247 N5 module jars), direct `ZipFile.read()` of individual entries for content
> verification (XML/HTML/plain-text — no binary format needed decoding), a local regex HTML-tag-stripper
> for readable-text excerpts of guide pages. No decompiler used this session (all read artifacts are
> plain XML/HTML/text, not bytecode). Markers (METHODOLOGY §3): `[CERT]` local primary source (file/zip
> entry opened and read this session) · `[CERT-doc]` official installed HTML/XML doc, full basename ·
> `[INFER]` deduction · REMIT = cited from `niagara-help`'s own README/ROADMAP, not re-derived.
>
> N5 documentation/tooling layer. Connects [niagara5-block2.md] (build toolchain — shares the
> `tridium-niagara-baja-doclet-5.0.4.jar` doclet that PRODUCES the `.bajadoc` files censused here) and,
> across corpora, the N4 `niagara-help` repo (`/home/cristian/niagara-research/niagara-help`) whose
> `README.md`/`ROADMAP.md`/`tools/*.py` this block explicitly targets for an N5 port.
>
> **Type:** mixed — §4.1–§4.9 are direct evidence (`[CERT]`) from this session's own zip/file reads;
> §4.10–§4.13 draw `[INFER]` comparisons against the N4 `niagara-help` REMIT baseline and against the N4
> `docX-doc.jar` architecture (itself independently censused this session, so those specific counts are
> `[CERT]`, but the cross-version comparison judgment is `[INFER]`); §4.14 (rebuild recipe) is a synthesis.
>
> **Breakthrough:** N5's per-class API documentation is no longer pre-rendered static HTML (N4's
> `bajadoc/*.html`) — it ships as **plain, directly-parseable XML** (`doc/<module>/**/*.bajadoc`,
> `<?xml version="1.0"?><bajadoc version="5.0" ...>`), with a separate `help.jar` class
> (`com.tridium.help.bajadoc.html.HtmlCompiler`) that renders it to HTML only at Workbench-view-time. For
> an offline `niagara-help-N5` corpus this means the entire HTML-stripping step N4's
> `bajadoc_parser.py` needs can be **skipped outright** — the XML is already the clean, structured
> intermediate form N4 had to reverse-engineer out of HTML.

---

## 4.1 — `docDeveloper.jar` full census: 8,817 entries, 222 MB uncompressed, 6 top-level dirs `[CERT]`

| Metric | Value |
|---|---|
| Jar file size on disk | 42.07 MB (compressed) |
| Total zip entries | **8,817** |
| Uncompressed total | **222.03 MB** |
| Compressed total | 38.39 MB |

`[CERT]` (`ZipFile.namelist()` + `ZipInfo.file_size`/`compress_size` summed over all entries, this
session). This matches the gap's own stated figures ("222 MB, 8,817 entries") exactly — those are the
**uncompressed** size and the raw entry count, not the on-disk jar size (42 MB).

Top-level directories (entry counts include subdirectory-marker entries):

| Top dir | Entries | Content |
|---|---|---|
| `doc/` | 8,726 | everything documented below (§4.2–§4.6) |
| `examples/` | 45 | `bajaScript/*.js` runnable code samples (referenced from the Developer Guide's BajaScript tutorials) |
| `rc/` | 20 | JS Playground widget resources (`JsPlayground.built.min.js`, `.hbs` template) + Sunlight.js syntax-highlighter assets used to render `<pre>` code blocks in the guide HTML |
| `com/` | 13 | `.class` files for `com.tridium.docdeveloper.*` — a Workbench-viewable `BJsPlayground`/`BBajaScriptTestComp` demo component, plus dashboard-widget example classes (`BExampleLinearGauge`, `BDashboardWidget`) referenced by the guide |
| `META-INF/` | 5 | manifest + signature (`NIAGARA4.SF`/`.RSA`) + `module.xml` |
| `ext/` | 5 | a bundled `@babel/standalone` (babel.min.js + LICENSE) — used by the JS Playground to transpile pasted examples in-browser |
| `module-info.class`, `module.palette`, `docDeveloper.lexicon` | 1 each | standard N5 module artifacts (JPMS descriptor — REMIT `niagara5-block2.md` §2.7) |

`[CERT]` (top-level split of `namelist()`, this session).

File-type breakdown across all 8,817 entries (non-directory entries only, `(none)` extension after
excluding directory markers resolves to **1 file** — a bundled `LICENSE` text file, not 1,183 as a naive
directory-inclusive count would suggest):

| Extension | Count | Role |
|---|---|---|
| `.bajadoc` | 6,584 | per-class/module/package API-doc XML (§4.2) |
| `.html` | 683 | Developer Guide pages, `doc/jsdoc/` JSDoc pages (§4.3–§4.4) |
| `.js` | 114 | JSDoc/BajaScript source + rc/examples JS |
| `.eot`/`.ttf`/`.woff`/`.woff2` | 36 each | one web-font family bundled 4x for the guide's own CSS |
| `.css` | 26 | guide + jsdoc + bajadoc stylesheets |
| `.png`/`.svg`/`.jpg` | 24/18/1 | guide diagrams/icons |
| `.class` | 9 | JS Playground demo component classes |
| `.dat` | 4 | the search-index binary payload (§4.5) |
| `.xml` | 2 | `doc/toc.xml` (§4.3) + 1 other |

`[CERT]` (extension tally over `namelist()` with directory entries excluded, this session).

## 4.2 — `doc/<module>/` = per-module bajadoc, now plain XML instead of static HTML `[CERT]`

**120 distinct `doc/<name>/` subdirectories** exist; **109 of them are indexed as documented modules** in
`doc/bajadoc.index` (a flat newline-separated list — `aapup`, `abstractMqttDriver`, `ace`, `alarm`, ...,
`workbench`, one module name per line, read in full this session). The remaining 11 are
non-module guide-content subdirectories (`security/`, `servlets/`, `themes/`, `upgrade/`, `ui/`, `js/`,
`velocity/`, `seriesTransforms/`, `jsdoc/`, plus the root-guide co-located `doc/` itself and one more not
separately enumerated). `[CERT]` (`doc/bajadoc.index` full read; `120 - 109 = 11` arithmetic over the
subdirectory-name set, this session).

Every `doc/<module>/` directory (checked directly for 33 of the 109 — every one sampled, from `doc/baja/`
652 entries down to `doc/chart/` 53 — the same pattern in all of them) contains:

- `module-index.bajadoc` — one per module, lists every package + every top-level class with a one-line
  description.
- `<packagePath>/<ClassName>.bajadoc` — one file per class/interface, mirroring the Java package path
  (`doc/control/niagara/control/BBooleanPoint.bajadoc`).
- occasional `package-index.bajadoc` (seen in `doc/lonworks/com/tridium/lonworks/`).

**The `.bajadoc` files are plain, well-formed XML — not HTML, not a binary format.** Full read of
`doc/control/niagara/control/BBooleanPoint.bajadoc` (5,520 bytes):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bajadoc version="5.0" createdBy="tridium-niagara-baja-doclet-5.0.4" createdAt="11-Sep-2026" createdOn="aceb72ec905d">
<class module="control" qualifiedName="niagara.control.BBooleanPoint" name="BBooleanPoint" packageName="niagara.control" public="true">
<description>
BBooleanPoint defines a read only boolean control point.
</description>
<tag name="@author">Dan Giorgis</tag>
...
<extends><type class="niagara.control.BDiscretePoint"/></extends>
<implements><type class="niagara.sys.BIBoolean"/></implements>
<property name="out" flags="orts">
<type class="niagara.status.BStatusBoolean"/>
<description>Slot for the &lt;code&gt;out&lt;/code&gt; property....</description>
</property>
<constructor name="BBooleanPoint" public="true"><description/></constructor>
<method name="getOut" public="true">...</method>
...
```
`[CERT]` (`doc/control/niagara/control/BBooleanPoint.bajadoc`, whole file read).

`createdBy="tridium-niagara-baja-doclet-5.0.4"` ties this file directly to the doclet jar
(`tridium-niagara-baja-doclet-5.0.4.jar`) already identified in `niagara5-block2.md` §2.10 as a real
`jdk.javadoc.doclet.Doclet` — this block confirms its **output format** is this XML dialect, which is a
new, custom "bajadoc" XML schema (`<bajadoc version="5.0">` root), distinct from both N4's rendered-HTML
bajadoc and from standard `javadoc`'s HTML output (§4.8).

The `module-index.bajadoc` for a module has the same root but a `<module>` element instead of `<class>`,
listing every package (with description) and every top-level public class (name + one-line description)
— e.g. `doc/control/module-index.bajadoc`:

```xml
<module name="control" bajaVersion="0" vendor="Tridium" vendorVersion="5.0.0.28">
<description>Niagara Control Module</description>
<package name="niagara.control"><description>This package provides classes for modeling control points.</description></package>
...
<class packageName="niagara.control" name="BBooleanPoint"><description>BBooleanPoint defines a read only boolean control point.</description></class>
```
`[CERT]` (`doc/control/module-index.bajadoc`, first ~1,500 bytes read).

## 4.3 — `doc/toc.xml`: the real "Developer Guide" table of contents (JavaHelp format) `[CERT]`

`doc/toc.xml` (9,711 bytes, read in full) is a **JavaHelp 1.0 TOC** document
(`DOCTYPE toc PUBLIC "-//Sun Microsystems Inc.//DTD JavaHelp TOC Version 1.0//EN"`) rooted at
`index.html`. It is the authoritative, complete list of Developer Guide topics — grouped exactly as
Workbench's own Help sidebar would render it (this tree is consumed by `help.jar`'s
`com.tridium.help.ui.TocTreeModel`/`TocRootNode`/`TocNode`, §4.6):

| Section | Sub-topics (leaf titles, verbatim from `toc.xml`) |
|---|---|
| **Framework** | Overview, Architecture, Directory Structure, API Information, Modules, Object Model, Component Model, Entity Model, Building Simples/Enums/Complexes, Registry, What Should I Subclass?, Collections, Naming, Links, Execution, Station, Remote Programming, Files, Localization, Spy, Licensing, XML, Bog Format, Distributions, Test, Virtual Components, Utilities |
| **User Interface → Open Web Technologies** | Introduction to Niagara UI, User Interfaces from AX to N4, UI Changelog, Serving HTML from the Station's File System, RequireJS, BajaScript, bajaux, webEditors, UxMedia, managers, driver, lexicon, log, dialogs, dashboards, export |
| **User Interface → Niagara - bajaui** | Gx, Bajaui, Workbench, Web, Px |
| **User Interface → Niagara Theme Modules** | Theming Custom Widgets, Using Custom Fonts |
| **User Interface (misc)** | Niagara Login Screen Customization, Auto Logoff (Web / Workbench) |
| **Web Server** | Web Modules - Java Servlets, Servlet Views, Web Servlets Components, Exporter Servlet, Apache Velocity, Px Velocity |
| **Niagara RPC** | Niagara RPC Overview |
| **Horizontal Applications** | Control, History, Alarm, Schedule, Report, Hierarchy, Series Transforms (5 sub-pages) |
| **Queries (BQL, NEQL, Search)** | BQL Overview/Expressions/Examples, NEQL Overview and Examples, Search |
| **Drivers** | Driver Framework (+ Quick Start, PointDeviceExt, HistoryDeviceExt, AlarmDeviceExt, ScheduleDeviceExt), BACnet, Lonworks, Lon Markup Language |
| **Development Tools** | Building Niagara Modules (`buildN5.html`), Building JavaScript Applications, Deploying Help, Slot-o-matic |
| **Upgrading to Niagara 5** | Upgrading to Niagara 5, Upgrading UI to Niagara 5, Upgrading JDKs, Using BFoxProxySession between stations at different major versions |
| **Architecture Diagrams** | Software Stack, Communication, Remote Programming, Driver Hierarchy, ProxyExt, Driver Learn |
| **Security** | General Overview, Niagara Permissions (+ Requesting Permissions), Authentication Service, Role Based Permissions, HTTP Header Authentication Mechanism, Client Authentication Example, Protecting against CSRF, Code Signing |

`[CERT-doc]` (`doc/toc.xml`, whole file, structure and every `tocitem text=` label quoted verbatim).

Independently, the **76 root-level `doc/*.html` files** (guide pages living directly under `doc/`, not in
a per-module subdirectory) plus the 9 non-module subfolders (`security/` 19, `servlets/` 5, `themes/` 5,
`upgrade/` 4, `ui/` 6, `js/` 2, `velocity/` 3, `seriesTransforms/` 7 — 51 files total) together **are** the
Developer Guide content this TOC indexes: 76 + 51 = 127 HTML files, closely tracking the `toc.xml` leaf
count. `[CERT]` (root-level `.html` count via `namelist()` filter `n.startswith('doc/') and n.count('/')==1`,
this session).

## 4.4 — `doc/jsdoc/`: JSDoc-generated static HTML for the BajaScript/UI JS APIs `[CERT]`

895 entries, of which 570 are `.html` — a standard **JSDoc**-tool output (recognizable file-name pattern:
`baja.Component.html`, `baja_comp_Component.js.html`, `tutorial-networkCalls.html`) plus its own bundled
web fonts (36×4), 18 `.svg` icons, 18 `.css`, 72 `.js` (JSDoc's own search-index/template scripts), 9
`.txt`. Subdirectories seen: `bajaScript/`, `bajaux/`, `webEditors/`, `driver/`, `export/`, `js/` (the last
holding `module-lex.html`, `module-log.html`, `module-dialogs.html`) — each referenced individually from
`toc.xml`'s "Open Web Technologies" section (§4.3). This is a **pre-rendered, ready-to-serve static HTML
tree**, already directly usable for a `niagara-help-N5/jsdoc/` mirror with no conversion step. `[CERT]`
(`doc/jsdoc/` full namelist + extension tally, this session).

## 4.5 — A homegrown full-text search index ships inside `docDeveloper.jar` `[CERT]`

Four small binary/text data files sit at `doc/` root: `doc/words.dat`, `doc/postings.dat`,
`doc/documents.dat`, `doc/worddocs.dat` — an inverted-index layout (word list, posting list, document
list, word→document map), matching the class names found in `help.jar` (§4.6): `Searcher`,
`Searcher$Module`, `Searcher$ModuleWordMap`, `Searcher$WordResult`, `SearchBuilder`, `SearchLoader`,
`SearchResult`. This is Workbench's built-in Help full-text search engine's pre-built index shipped
alongside the doc content it indexes — a custom format, not Lucene. `[CERT]` (file listing +
`help.jar` class-name cross-reference, this session; internal binary layout of the `.dat` files not
decoded — named as child gap B4-G1, low priority since the doc content itself is directly greppable).

## 4.6 — `help.jar`: the runtime consumer — bajadoc XML→HTML compiler + TOC-driven Help UI + search `[CERT]`

`help.jar` (117 entries, 0.21 MB) is a small, dedicated module whose **full class list was read this
session** (108 `.class` files under `com/tridium/help/`, plus `help.lexicon` and `rc/bajadoc.css`). Three
functional groups, by package:

| Package | Role |
|---|---|
| `com.tridium.help.bajadoc.*` (parser/model: `BajadocParser`, `ClassDoc`, `ModuleDoc`, `PackageDoc`, `MethodDoc`, `FieldDoc`, `PropertyDoc`, `TopicDoc`, ...) | reads the `.bajadoc` XML files (§4.2) into an in-memory doc model |
| `com.tridium.help.bajadoc.html.HtmlCompiler` / `HtmlCompilerMain` | **renders the XML model to HTML** — `HtmlCompilerMain` is a standalone entry point, i.e. an offline/batch HTML-generation path exists in addition to any live in-Workbench rendering |
| `com.tridium.help.bajadoc.ui.BBajadocViewer` / `BajadocCommands` / `Flattener` | the Workbench-embedded bajadoc viewer (renders on demand when a class is opened in Help) |
| `com.tridium.help.ui.*` (`BHelpProfile`, `BHelpSideBar`, `TocTreeModel`, `TocRootNode`, `TocNode`, `DocModuleNode`, `DocPackageNode`, `DocClassNode`, `SearchNode`, `SearchTreeModel`) | the Help view itself — `TocTreeModel`/`TocRootNode` is the direct consumer of `doc/toc.xml` (§4.3) |
| `com.tridium.help.{Searcher,SearchBuilder,SearchLoader,SearchResult}` | the full-text search engine over the `.dat` index (§4.5) |
| `com.tridium.help.{HelpSystem,HelpVerifier,Hierarchy,HierarchyBuilder,HtmlChecker}` | orchestration + a class-hierarchy builder (drives a "subclass tree" view, same feature N4's `niagara_help.py hierarchy` command replicates) + an HTML-well-formedness checker |
| `com.tridium.help.web.BBajadocServletView` | a web (browser, not just Workbench) view of bajadoc |

`[CERT]` (`help.jar` full `namelist()`, class names read directly, no decompilation needed for this
architectural mapping). `rc/bajadoc.css` is the stylesheet `HtmlCompiler` output references.

**This directly confirms the Breakthrough**: the XML→HTML step is a real, separately-invokable compiler
(`HtmlCompilerMain`), not an inline private routine — so an offline rebuild has two valid paths: (a) parse
the `.bajadoc` XML directly (no Niagara runtime needed — plain XML, any parser), or (b) run
`HtmlCompilerMain` against the jar (needs a JVM + this module's classpath, unverified runnable this
session — child gap B4-G2, requires-execution). Path (a) is recommended (§4.14).

## 4.7 — `docDeveloperAnalytics.jar` and `docSource.jar`: a small Analytics guide + N5's public source `[CERT]`

`docDeveloperAnalytics.jar` — 204 entries, 0.33 MB, a self-contained mini developer-guide for the
Analytics module: `doc/overview.html`, `doc/componentModel.html`, `doc/ordSchemes.html`,
`doc/webApis.html`, `doc/buildingAlgorithmBlocks.html`, plus `doc/algo_flow.jpg` and its own 197 `doc/`
entries (mostly `.bajadoc` — 158). `[CERT]` (full namelist).

`docSource.jar` — 3,239 entries, 11.80 MB compressed, **2,868 `.java` files** (30.5 MB uncompressed) —
N5's public Java source, organized identically to `doc/<module>/` (one top folder per module, e.g.
`alarm/niagara/alarm/AlarmDbConnection.java`), confirming the package-path rename from N4's `javax.baja.*`
to N5's `niagara.*` is reflected directly in the source folder layout, not just in class names. Also
carries `doc/index.html` and `doc/packageIndex.html` (a source-browsing index, 8 `doc/`-prefixed entries
total — not guide content). `[CERT]` (full namelist, `.java` count via extension filter).

For comparison: N4's equivalent `docSource-doc.jar` was **not opened this session** (out of the gap's
named source list) — `niagara-help`'s own `source/` dir (REMIT) holds 2,603 Java files / 679K lines from
N4 4.14, so N5's 2,868-file `docSource.jar` is in the same order of magnitude. `[INFER]` (file-count
comparison only; no line-count comparison performed this session — child gap B4-G3).

## 4.8 — `niagaraJavadoc.jar`: a standard `javadoc`-tool artifact — genuinely new in N5 `[CERT]`

`/mnt/c/Program Files/Niagara/5.0.0.28/javadoc/niagaraJavadoc.jar` — 4,115 entries, 25.94 MB, **not**
bajadoc: its file set (`allclasses-index.html`, `allpackages-index.html`, `member-search-index.js`,
`module-search-index.js`, `package-search-index.js`, `type-search-index.js`, `element-list`,
`overview-tree.html`, `serialized-form.html`) is the exact, unmistakable output signature of the standard
JDK `javadoc` tool (the same file set the Java 25 `javadoc` doclet produces for any JDK module). `[CERT]`
(full namelist + `doc/element-list` content read).

`doc/element-list` lists ~100+ `niagara.*` packages (`niagara.agent`, `niagara.alarm`, `niagara.bacnet.*`,
`niagara.bajascript`, `niagara.control.*`, `niagara.driver.*`, ...) — confirming this jar documents the
**same public `niagara.*` API surface** as the per-module bajadoc (§4.2), rendered a second time through
the standard-Java pipeline instead of the custom bajadoc doclet+`HtmlCompiler` pipeline. `[CERT]`
(`doc/element-list`, first 2,000 bytes read, package names enumerated).

**No N4 counterpart was found for this artifact.** `niagara-help`'s own README (REMIT) lists no javadoc
jar or javadoc-tool output among its sources (only `bajadoc/`, `devguide/`, `source/`, `jdk/`, `guides/`,
`docs-text/`) — this is consistent with N4 never having shipped a standard-`javadoc` rendering of its API
at all. `[INFER]` (absence claim based on the README's stated source list, not an independent scan of all
1,013 N4 module jars for a javadoc-shaped artifact — child gap B4-G4).

## 4.9 — Census of all 247 N5 module jars: only 2 jars carry real API-doc content; no per-module doc bundling `[CERT]`

Every one of the 247 jars under `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/` was scanned
for entries under `doc/` or ending `.html`/`.bajadoc`. **Only 8 jars have any such entries**:

| Jar | `doc/` entries | `.html` | `.bajadoc` | Verdict |
|---|---|---|---|---|
| `docDeveloper.jar` | 8,726 | 683 | 6,584 | the documentation module (§4.1) |
| `docDeveloperAnalytics.jar` | 197 | 6 | 158 | Analytics mini-guide (§4.7) |
| `docSource.jar` | 8 | 2 | 0 | source-browsing index only (§4.7) |
| `ffmpeg.jar` | 8 | 0 | 0 | bundled LGPL/license texts (`lgpl-2.1.txt`, `readme.txt`) + `doc/toc.xml` for its own third-party doc, not Niagara API doc |
| `bajaui.jar` | 2 | 0 | 0 | just `doc/style.css` |
| `web.jar` | 0 | 1 | 0 | `rc/theme/test.html` (a theme test fixture) |
| `workbench.jar` | 0 | 3 | 0 | `com/tridium/workbench/media/{about,contents,error}.html` (Workbench's own About/Help-error screens) |
| `xprotect.jar` | 0 | 1 | 0 | one vendor-SDK `index.html` inside a bundled third-party SDK |

The other **239 of 247 module jars carry zero doc-shaped content.** `[CERT]` (full 247-jar zip scan, this
session — script and per-jar counts reproducible). This directly answers the gap's question: **module
jars do NOT carry their own API-documentation directories in N5** — all bajadoc for all 109 documented
modules is centralized inside `docDeveloper.jar`/`docDeveloperAnalytics.jar`, exactly mirroring N4's
model where bajadoc for a module X lived in a *separate* `docX-doc.jar`, not inside `X.jar` itself (§4.10).

## 4.10 — What's NEW vs N4: architecture comparison `[CERT]` + `[INFER]`

N4 side (censused this session): `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/` ships **~98
separate per-subsystem `docX-doc.jar` files** (one doc jar per guide topic — `docAlarms-doc.jar`,
`docBacnet-doc.jar`, `docCcn-doc.jar`, `docKitControl-doc.jar`, ... — this is the literal source of
`niagara-help`'s 98 `guides/` folders, REMIT), plus `docDeveloper-doc.jar` (8,803 entries, 94.67 MB
uncompressed — the Developer Guide + bajadoc core), `docSource-doc.jar`, `docUser-doc.jar` (1,249
entries, 21.28 MB — a **User Guide**, end-user not developer docs), and `docAXtoN4Migration-doc.jar` (210
entries — the historical **AX→N4** migration guide, e.g. `doc/AXtoN4overview.html`,
`doc/pAXtoN4_MigrationTasks.html`). `[CERT]` (directory listing + census of the three named jars, this
session).

| Dimension | N4 4.14.0.162 | N5 5.0.0.28 (this beta) |
|---|---|---|
| Doc-jar count | ~98 per-subsystem `docX-doc.jar` + `docDeveloper-doc.jar` + `docUser-doc.jar` + `docSource-doc.jar` + `docAXtoN4Migration-doc.jar` (~102 doc jars total, of 1,013) | **4 jars total**: `docDeveloper.jar`, `docDeveloperAnalytics.jar`, `docSource.jar`, `help.jar` (of 247) — a **~25x consolidation** in jar count |
| Per-class API doc format | static pre-rendered HTML (`bajadoc/*.html`, REMIT) | plain XML (`.bajadoc`, §4.2), rendered to HTML on demand by `HtmlCompiler` |
| Guide-topic organization | one `docX-doc.jar` module per subsystem, each with its own `doc/` HTML tree (98 folders in `niagara-help/guides/`) | one consolidated `docDeveloper.jar`, guide pages as flat `doc/*.html` + a handful of subfolders, indexed by one `doc/toc.xml` |
| User Guide (end-user docs) | separate `docUser-doc.jar` (1,249 entries) | **no `docUser`-named jar present** in this beta's 247-module set (§4.13) |
| Migration guide | `docAXtoN4Migration-doc.jar` (AX→N4, 210 entries, separate module) | `doc/upgrade/upgradingToN5.html` + 3 sibling pages, bundled **inside** `docDeveloper.jar` itself (§4.11–4.12) — no separate migration module |
| Standard-`javadoc` rendering | not found (REMIT — absent from `niagara-help` README's source list) | new: `niagaraJavadoc.jar` (§4.8) |
| JDK-class bajadoc stand-ins | `jdk/` — 4,120 `.bajadoc` files for referenced JDK types (REMIT) | **no `jdk`-named top dir found** in `docDeveloper.jar`'s census (§4.1) — flagged absence, child gap B4-G5 |
| Full-text search index | not documented in `niagara-help` README as shipped (the repo BUILDS its own indexes, `tools/*.py`) | ships a **pre-built** search index (`doc/{words,postings,documents,worddocs}.dat`, §4.5) consumed by `help.jar`'s own `Searcher` |
| API namespace | `javax.baja.*` | `niagara.*` (confirmed both in `docSource.jar` folder layout §4.7 and in `niagaraJavadoc.jar`'s `element-list` §4.8) |

`[CERT]` for every row's raw counts (independently censused this session on both sides); `[INFER]` for the
"~25x consolidation" characterization and the overall architecture-shift narrative.

## 4.11 — Migration/upgrade documentation: keyword census across all `docDeveloper.jar` HTML `[CERT]`

A full-text keyword scan (all 683 `.html` files under `doc/`) for `N4`, `migrat`, `upgrad`, `Java 25`,
`module-info`, `JPMS`, `deprecat` found the following as the **load-bearing hits** (non-jsdoc,
non-incidental):

| File | Hit keywords |
|---|---|
| `doc/upgrade/upgradingToN5.html` | N4, migrat, upgrad, Java 25, module-info, JPMS |
| `doc/upgrade/upgradingUItoN5.html` | migrat, upgrad |
| `doc/upgradingJDK.html` | migrat, upgrad, Java 25 |
| `doc/upgrade/usingFoxProxySession.html` | N4, migrat, upgrad |
| `doc/uiFromAxToN4.html` | N4 (title: "User Interfaces from AX to N4" — a **retained legacy AX→N4** doc, still shipped in N5) |
| `doc/ui/uiChangelog.html` | N4, migrat, upgrad |
| `doc/security/niagaraPermissions.html` | migrat, module-info |
| `doc/security/requestingPermissions.html` | module-info |
| `doc/modules.html` | migrat, module-info, JPMS |
| `doc/buildN5.html` | migrat, upgrad, Java 25, module-info, JPMS (already covered in `niagara5-block2.md`) |

`[CERT]` (script scanned all 683 `.html` files' decoded text + filename + `<title>`, this session; results
above are the full non-jsdoc hit list, not a sample).

## 4.12 — `doc/upgrade/upgradingToN5.html`: the "Niagara 5 Module Transition Guide" — the single highest-value port doc `[CERT-doc]`

92,940 bytes raw (64,102 bytes of stripped text). This is a **dedicated, step-by-step module-porting
guide**, titled "Niagara 5 Module Transition Guide," structured as: Intro → Niagara 4 Environment (upgrade
to 4.15 first, fix compiler warnings) → **Module Part Combination** → Niagara 5 Environment (directories,
Gradle env, Java 25, plugin renames — cross-checked against `niagara5-block2.md` §2.2/2.8, consistent) →
Java 25 API Changes (Security Manager, namespace moves) → **Niagara 5 Breaking Changes** → Compiling and
Testing → **Modularity** (Java Module Directives, `uberjar`) → Third Party Libraries → Tips & Tricks. Full
read of the two highest-value sections:

**Module Part Combination (verbatim procedure, quoted/summarized):** "Niagara 5 removes the concept of
module parts. ... all of our code will be placed in a single directory and separated based on package
names instead of being split among different module part directories." A `-doc` module part must be
extracted into its own new `doc<YourModuleName>` module first (via `gradlew addModule --module-name
doc<YourModuleName> --runtime-profiles doc ...`); remaining module parts (`rt`/`ux`/`wb`/`se`, given a
documented "level" precedence 4→3→2→1 rt>ux>wb>se) get merged into the **highest-level** part, folding
`.gradle.kts` plugin/dependency blocks, `module.lexicon`, `module.palette`, `module-permissions.xml`, and
(if hand-maintained) `module-include.xml`/`moduleTest-include.xml` (auto-generated ones can simply be
deleted and regenerated — direct continuity with the annotation-processor finding in `niagara5-block2.md`
§2.6). `[CERT-doc]` (`doc/upgrade/upgradingToN5.html`, "Module Part Combination"/"-doc Module Part"/"Other
Module Parts" subsections, ~4,600 words read in full this session).

**This is a direct, load-bearing hit against the `build-n4-module` skill's own module structure** — every
N4 module the skill scaffolds (rt/ux/wb parts, e.g. ColdRoomPan-rt/ColdRoomPan-ux/ColdRoomPan-wb per the
user's own module memories) is exactly the module-part pattern this guide says N5 **eliminates entirely**.

**Niagara 5 Breaking Changes (list, verbatim topic headers):** Removed classes/methods (most N4-deprecated
APIs removed outright; `javax.baja.log.Log` → `java.util.logging.Logger`); **`app` module removed**
(Niagara Mobile app support, config.bog `AppContainer` needs manual/migrator-tool removal); non-TLS Fox
connections slated for future removal; `isUnoperational()`→`isNonOperational()` rename;
`Sys.getLanguage()`/`Context.getLanguage()` removed in favor of `getLanguageCode()`;
`RuntimeProfile`/`BModule.getRuntimeProfile(FilePath)` removed; `javax.baja.chart.*` →
`niagara.chart.data.*` package move; `javax.baja.query.*` → `niagara.collection.*` package move;
**`basicDriver`/`devDriver` frameworks deprecated** (not removed, unsupported); BACnet public API changes
(Descriptor interface simplification, `Context`-taking methods, constants moved to public static classes);
**Web Launcher and Kiosk Mode removed** (all browser UI must go through bajaux/hx/axvelocity/custom
servlets, not bajaui); `BKioskProfile` fully removed. `[CERT-doc]` (same file, "Niagara 5 Breaking Changes"
section, ~1,900 words read in full this session).

## 4.13 — Doc-silent gap: no `docUser`/AX-migration analog installed in this beta `[CERT]` (absence, beta-scoped)

The 247-jar census (§4.9) found **no jar named `docUser*` or `*Migration*`** among this beta's installed
modules — unlike N4, which ships `docUser-doc.jar` (end-user guide) and `docAXtoN4Migration-doc.jar`
(migration guide) as separate, always-installed modules (§4.10). `[CERT]` (247-jar namelist scan, no
match for either pattern, this session). This is recorded as an **absence specific to this beta's minimal
`modules/` directory** (the same caveat `niagara5-block2.md` §2.6 raised for the missing
`niagaraAnnotationProcessors` module) — not a confirmed statement that N5 GA drops the User Guide. Closing
this needs either a fuller N5 install/distribution kit or the Tridium product-download page for a full
N5 module list. Named as child gap **B4-G6**.

## 4.14 — Rebuild recipe: `niagara-help-N5` jar→directory mapping `[INFER]` (synthesis)

Concrete mapping from N5 source jars to a `niagara-help`-style corpus, one row per N4 folder this session
confirmed an N5 source for:

| N4 folder (existing) | N4 source | N5 source | N5 rebuild approach |
|---|---|---|---|
| `bajadoc/` (3,586 HTML) | ~98 `docX-doc.jar` | `docDeveloper.jar` `doc/<module>/**/*.bajadoc` (6,584 files, 109 modules) + `docDeveloperAnalytics.jar` | **Skip HTML entirely.** Parse the XML directly with `xml.etree`/`lxml` — simpler than N4's HTML-strip (`bajadoc_parser.py`); the XML already carries `qualifiedName`, `extends`, `implements`, `<property>`/`<method>`/`<field>` structured, no regex-scraping needed. |
| `bajadoc-clean/` (2,759 .txt) | derived from `bajadoc/` | same XML source | generate the clean-text summary directly from the parsed XML tree — one new script, no HTML step. |
| `devguide/` (472 HTML) | `docDeveloper-doc.jar` `doc/*.html` | `docDeveloper.jar` `doc/*.html` (76 root) + `doc/{security,servlets,themes,upgrade,ui,js,velocity,seriesTransforms}/*.html` (51) + `doc/toc.xml` for structure (§4.3) | reuse the existing HTML-strip approach (`devguide_parser.py`) largely as-is; **new**: parse `toc.xml` (JavaHelp XML, trivial) instead of `devguide/index.html` for the section/guide index — arguably an upgrade, since `toc.xml` is already structured data, not HTML to scrape. |
| — (JSDoc, previously folded into `devguide/`) | `docDeveloper-doc.jar` | `docDeveloper.jar` `doc/jsdoc/**` (895 entries, 570 HTML) | copy as-is — already static, pre-rendered HTML; no conversion needed (§4.4). |
| `source/` (2,603 .java) | `docSource-doc.jar` | `docSource.jar` (2,868 `.java`) | copy as-is; note the `javax.baja.*`→`niagara.*` package-path rename affects every file's location (§4.7). |
| `jdk/` (4,120 .bajadoc, JDK class metadata) | (N4-only artifact) | **no direct source found** (§4.10) | either derive equivalent JDK cross-references from `niagaraJavadoc.jar`'s standard-javadoc rendering (§4.8, different format, needs a new adapter) or drop this folder for N5 — child gap B4-G5. |
| `guides/` (8,971 HTML, 98 folders) | ~98 `docX-doc.jar` | **folded into `devguide/`'s new source above** — N5 has no separate per-subsystem guide-jar structure (§4.10) | no separate step; the consolidation means N5's `niagara-help` needs **no** `guides/`-equivalent top folder at all — everything lands under one `devguide/` tree. |
| `docs-text/` (364 .txt, from PDFs) | PDF manuals (`pdf_extractor.py`) | not covered this session — no PDF census performed (gap did not list PDF sources for N5) | out of scope; would need a fresh PDF inventory of the N5 distribution if one exists (child gap, not opened this session, B4-G7). |
| — (new) | (none) | `niagaraJavadoc.jar` (4,115 entries, standard `javadoc` output, §4.8) | copy `doc/*.html` as-is into a new `javadoc/` top folder — a second, alternate API-reference rendering, genuinely new in N5, worth keeping alongside `bajadoc/` rather than merging (different rendering, same underlying `niagara.*` API surface). |
| **indexes** (`class-index.json`, `devguide-toc.json`, `guides-index.json`) | derived by `tools/*.py` from `allclasses-noframe.html` + `devguide/index.html` + folder census | `doc/bajadoc.index` (109-module flat list, §4.2) + `doc/<module>/module-index.bajadoc` (class list per module, already has descriptions) + `doc/toc.xml` (§4.3) | building the N5 `class-index.json` needs no HTML parsing at all — `doc/bajadoc.index` + 109 `module-index.bajadoc` files are already the exact structured data N4 had to scrape out of `allclasses-noframe.html`. This is a strict simplification over the N4 tool. |

`[INFER]` — this is a synthesis recipe built from the `[CERT]` facts in §4.1–§4.9 and the REMIT N4 layout;
no N5 rebuild script was written or run this session (would be new-file creation, out of scope for a
READ-ONLY research block).

## 4.x — Self-verify tally

Literal `verify-block.sh` output (methodology §11: reported as the script's own output, not
hand-recalculated):

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    /home/cristian/niagara5-research/niagara5-block4.md
== verify-block: niagara5-block4.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 37  (adj 34)
   [CERT-doc] 6  (adj 5)
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 11  (adj 8)
-- ratio -- [INFER]/[CERT*] = 8/39 = 0.21
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   WARN    [CERT] markers present (39) but ZERO file:line citations resolved — the citation gate checked
   nothing and exits 0 silently. Expected for synthesis / REMITTANCE / [CERT-live]-only or
   [CERT-doc]-only blocks (check your block-type declaration); otherwise add file:line citations or
   re-check the citation format.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

Adjusted `[INFER]`/`[CERT*]` ratio = 8/(34+5) = **0.21** — low, consistent with an evidence-heavy `mixed`
block whose only real synthesis load is the comparison table (§4.10) and the rebuild recipe (§4.14).

**The WARN is EXPECTED and explained by METHODOLOGY §11's decompiled/archival-tree citation note**, not a
defect: every `[CERT]` citation in this block points to a **zip-entry path inside a jar**
(`doc/toc.xml`, `doc/bajadoc.index`, individual `.bajadoc`/`.html` files) rather than a `file:line` inside
an extracted tree under this corpus directory — `verify-block.sh` can only resolve paths that exist on
disk under `/home/cristian/niagara5-research`, so every jar-internal citation classifies as `extern` and
the literal-citation-resolution gate finds none to check. Self-verify declaration per §11:
**`verify-block: 0 resolved (all extern — zip-entry citations into installed jars); citation gate =
inline read-verify, every cited zip entry was opened with `ZipFile.read()` and its content quoted/read in
full or in the shown byte range this session, not carried from memory.`**

## 4.x — Named child gaps

- **B4-G1** — decode the internal binary layout of `doc/{words,postings,documents,worddocs}.dat` (§4.5);
  low priority since the doc content itself is directly parseable without the index.
- **B4-G2** — requires-execution: run `com.tridium.help.bajadoc.html.HtmlCompilerMain` against a sample
  `.bajadoc` file to confirm the XML→HTML rendering path works standalone (no live station in this beta
  install — same constraint as `niagara5-block2.md`).
- **B4-G3** — line-count comparison of N5's 2,868 `docSource.jar` `.java` files vs. N4's 2,603/679K-line
  `source/` REMIT baseline (only file counts compared this session, §4.7).
- **B4-G4** — confirm the absence of any standard-`javadoc`-shaped artifact across all 1,013 N4 module
  jars (only the `niagara-help` README's stated source list was checked, §4.8).
- **B4-G5** — locate an N5 equivalent (if any) of N4's `jdk/` JDK-class-bajadoc stand-ins (§4.1/§4.10);
  candidate: adapt `niagaraJavadoc.jar`'s standard-javadoc rendering, but that covers `niagara.*` packages
  only, not `java.*`/`javax.*` JDK types.
- **B4-G6** — confirm whether N5 GA (vs. this beta) ships a `docUser`-equivalent and/or an
  AX/N4-migration-equivalent module (§4.13) — needs a fuller distribution or the vendor download page.
- **B4-G7** — census whether N5 ships any PDF manuals (N4's `docs-text/` source), not checked this session
  (not in the gap's named source list).
- **B4-G8** — deep-read `doc/upgrade/upgradingUItoN5.html` (UI-specific transition guide, only
  keyword-hit-confirmed in §4.11, not read in full) — high value for any module with a `-ux`/`-wb` part.

## 4.x — Connections

- **[niagara5-block2.md]** — shares the `tridium-niagara-baja-doclet-5.0.4.jar` doclet (that block's §2.10
  identified it as a `jdk.javadoc.doclet.Doclet`; this block confirms its output IS the `.bajadoc` XML
  format censused in §4.2) and the annotation-processor/`module-include.xml` mechanism (§2.6, directly
  referenced by the Module Part Combination procedure in §4.12).
- **REMIT `niagara-research/niagara-help`** (README.md/ROADMAP.md heads) — the N4 corpus layout this block
  targets for a port; §4.14 is the concrete jar→folder mapping.
- **[TO ANNOTATE — child gap B4-G6]** — a fuller N5 distribution (beyond this beta's 247-module install)
  would let a future session confirm or refute the `docUser`/migration-module absence as GA-permanent
  rather than beta-minimal.
