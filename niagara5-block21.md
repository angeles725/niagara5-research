# Block 21 — N5 UI stack: bajaux, themes, uxBuilder, Workbench and web resources

> **Scope**: Closes gap **N5-G11** — the browser/desktop UI stack shipped with Niagara N5 5.0.0.28:
> `themeN5`/`themeLucid`/`themeZebra`, `uxBuilder`, `hx`, `bajaux`, `bajaScript`, `webEditors`, `webChart`,
> `smartTableHx`, `wiresheet`, `pxEditor`, `workbench`, `jxBrowser`, `gx`/`svg`. Answers: JS module system
> and bundled frameworks; NSS2 theming and `themeN5` vs `themeLucid`/`themeZebra`; what `uxBuilder` actually
> is; whether Workbench is still Swing, what JxBrowser is and does, and whether Web Launcher/Java Web Start
> is gone; Px/`pxEditor` posture; and the implications for DashboardPan-ux's static-HTML+fetch servlet
> pattern (resource serving, CSP/headers). Does **not** re-derive the general JPMS/`-wb`/`-ux`/`-rt`
> consolidation mechanics, the JDK 8→25 Security-Manager/permission-annotation model, or the
> `javax.servlet`→`jakarta.servlet` migration for `DashboardPan-ux` — all already closed in
> [Block 10](niagara5-block10.md) §§10.4/10.5/10.9/10.11 (REMIT, not re-derived). Does not cover a live
> Workbench run (no runnable install, same constraint as Blocks 2/4) or a full read of every `.js` file in
> the 18 censused jars (namelist + ext census + targeted reads only).
>
> Subject version: **Niagara 5.0.0.28 (Beta)**. Install root: `/mnt/c/Program Files/Niagara/5.0.0.28`;
> config/modules root: `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` (18 target jars).
> N4 baseline (REMIT — corpus, not re-derived except for the per-jar split counts in §21.7):
> `/home/cristian/niagara-research` blocks B195, B204, B427, B895, B922, B1000, B1006; N4 module tree
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules`.
>
> Sources: all 18 target jars under the config/modules root, censused with `python3 zipfile`
> (namelist + per-jar top-level-dir/extension counts, full script preserved at
> `/tmp/claude-1000/n5b21/census.py`); `module-info.class` of `jxBrowser.jar`/`workbench.jar`/`hx.jar`
> disassembled with `javap -v` (Temurin 26 build, `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap`);
> three `com.tridium.jx.browser` classes decompiled with Vineflower 1.12.0
> (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar` on the same JDK) into
> `/tmp/claude-1000/n5b21/dec/` (scratch, not preserved in the corpus — per METHODOLOGY §11 "decompiled-tree
> blocks" convention, citations into that tree are `extern`; anchor is the jar's own sha256, given per file
> in §21.6); NSS2/`.nss`/`package.json`/`.js` file bodies read directly out of the zip in Python (no
> extraction to disk beyond the jxBrowser scratch); `bin/ext/jxbrowser/*.jar` censused by `ls -la` +
> `unzip -l` (not opened — third-party licensed binary, size/version only). N4 comparison via
> `python3 tools/corpus-nav.py find <term>` (remit lookups) and a `find` census of the N4 module directory.
> Markers: `[CERT]` local primary source (`file:line` or jar-entry path) · `[INFER]` deduction.
>
> UI/browser layer. Connects [Block 10] (transition-guide remit for NSS2/BC-22/BC-30..32/JPMS resource
> roots), [Block 4] (docDeveloper.jar/help.jar — the documentation half of this same module set).
>
> **Type:** `standard`.

---

## 21.1 — Target census: all 18 modules present, sizes, and top-level structure `[CERT]`

Every module named in the gap is installed at 5.0.0.28. Full per-jar entry counts, top-level directories,
and extension histograms are in `/tmp/claude-1000/n5b21/census.py`'s output (re-run to reproduce); the
load-bearing subset:

| Module | Entries | Size | Dominant content | Citation |
|---|---|---|---|---|
| `themeN5.jar` | 84 | 1.02 MB | `less/`(14) `fonts/`(14, Figtree TTF) `nss/`(3) `palette/`(6) — semantic-token CSS theme | `themeN5.jar` namelist |
| `themeLucid.jar` | 1076 | 945 KB | `imageOverrides/`(940 PNG/GIF) — sprite-based legacy skin | `themeLucid.jar` namelist |
| `themeZebra.jar` | 37 | 835 KB | `less/`(8) `fonts/`(7, woff/ttf) — legacy skin, no dark variant | `themeZebra.jar` namelist |
| `uxBuilder.jar` | 179 | 608 KB | `rc/`(118 `.js`) `com/`(23 `.class`) | `uxBuilder.jar` namelist |
| `hx.jar` | 233 | 525 KB | `com/`(135) `niagara/`(61) `.class`(189) | `hx.jar` namelist |
| `bajaux.jar` | 95 | 303 KB | `rc/`(56, 54 `.js`) `com/`(7) | `bajaux.jar` namelist |
| `bajaScript.jar` | 244 | 560 KB | `rc/`(208, 207 `.js`) — pure JS client library | `bajaScript.jar` namelist |
| `webEditors.jar` | 666 | 1.59 MB | `rc/`(452) `com/`(97) — largest field-editor set | `webEditors.jar` namelist |
| `webChart.jar` | 112 | 298 KB | `rc/`(68) `com/`(9) | `webChart.jar` namelist |
| `smartTableHx.jar` | 136 | 293 KB | `com/`(113, 114 `.class`) — server-rendered, little JS | `smartTableHx.jar` namelist |
| `wiresheet.jar` | 193 | 446 KB | `com/`(100) `rc/`(56, 50 `.js`) | `wiresheet.jar` namelist |
| `pxEditor.jar` | 393 | 710 KB | `com/`(325) `niagara/`(31) — 357 `.class`, **zero** `rc/`/`.js` | `pxEditor.jar` namelist |
| `workbench.jar` | 1301 | 2.50 MB | `com/`(1015) `niagara/`(199) — 1202 `.class`, only 3 `rc/` files | `workbench.jar` namelist |
| `jxBrowser.jar` | 31 | 98 KB | `com/`(19, all `.class`) — thin wrapper, no bundled Chromium | `jxBrowser.jar` namelist |
| `gx.jar` | 286 | 5.69 MB | `com/`(130) `niagara/`(68) `rc/`(37) `LIB-INF/`(14 nested jars) | `gx.jar` namelist |
| `svg.jar` | 13 | 18 KB | `com/`(3) — tiny stub | `svg.jar` namelist |
| `svgBatik.jar` | 26 | 1.51 MB | `LIB-INF/`(4 nested jars) — Apache Batik SVG engine wrapper | `svgBatik.jar` namelist |
| `kitPx.jar` | 152 | 274 KB | `com/`(92) `rc/`(32, 30 `.js`) | `kitPx.jar` namelist |

`[CERT]` (each row: `python3 zipfile` namelist + `os.path.getsize`, this session).
`pxEditor.jar` and `workbench.jar` carrying almost no `rc/`/`.js` while `bajaScript`/`webEditors`/`hx`/
`bajaux`/`kitPx`/`wiresheet` are majority-JS is the structural signature of the Swing-desktop/browser-client
split (§21.4): the desktop-only modules are pure `.class`, the browser-facing ones are pure `.js`/`.css`.

## 21.2 — JS module system: still AMD/RequireJS, not ES modules; jQuery is still a hard dependency `[CERT]`

`bajaScript.jar`'s `rc/bs.js` (the RequireJS build entry point) still opens with
`require(["baja", "lex", "bajaScript/env/browser"], function () {...});`, and every individual source file
(e.g. `rc/baja/sys/BaseBajaObj.js`) still uses the AMD `define([...], function (...) {...})` wrapper.
`[CERT]` (`bajaScript.jar:rc/bs.js`, full text; `bajaScript.jar:rc/baja/sys/BaseBajaObj.js`, full text — both
still carry the file-level `@copyright 2015 Tridium` header, i.e. unmodified since the N4/AX era).
`rc/env/jQueryBrowserEnvUtil.js` is `define("bajaBrowserEnvUtil", ["jquery", "bajaScript/sys",
"bajaPromises"], function ($, baja, Promise) {...})` — jQuery is a named, non-optional AMD dependency for
the browser environment adapter. `[CERT]` (`bajaScript.jar:rc/env/jQueryBrowserEnvUtil.js:1-16`).
`rc/env/require-node-config.js` additionally shows a Node.js RequireJS harness (`require('requirejs')`,
`nodeRequire: require`) used for running BajaScript headless/server-side — unchanged AMD tooling.
`[CERT]` (`bajaScript.jar:rc/env/require-node-config.js`, full text).

**The built/minified bundles are Babel-transpiled ES6+, but the module wrapper stays AMD.**
`rc/bs.built.min.js` (363,625 bytes) and `bajaux.jar:rc/bajaux.built.min.js` (155,569 bytes) both open with
`/** @copyright 2026 Tridium, Inc. All Rights Reserved. */` (i.e. rebuilt for this beta, unlike the
per-source-file 2015 headers) followed by classic Babel helper functions —
`_toConsumableArray`/`_arrayWithoutHoles`/`_callSuper`/`_getPrototypeOf` in `bs.built.min.js`,
`_defineAccessor`/`_superPropGet`/`_get` in `bajaux.built.min.js` — the standard `@babel/plugin-transform-*`
runtime-helper signatures for down-leveling ES2015+ `class`/spread syntax to ES5. `[CERT]`
(`bajaScript.jar:rc/bs.built.min.js:1-400`; `bajaux.jar:rc/bajaux.built.min.js:1-400`). Despite the Babel
transpilation, `rc/bajaux.built.min.js` still contains literal `define("bajaux/events",[],function(){...})`
calls at the top level — confirming the build pipeline (Babel → AMD bundle) targets the *same* RequireJS
module system, not `webpackJsonp`/`__webpack_require__`/`System.register`/UMD. `[CERT]`
(`bajaux.jar:rc/bajaux.built.min.js`, `grep`-confirmed absence of the three webpack/SystemJS markers, and
`define(` found at offset 5980). **[Corrected by [Block 124] §124.9/§124.10: `bs.built.min.js` is 363,641 B, not 363,625; every `define` module of both bundles maps to a readable file (e.g. `rc/events.js` for `bajaux/events`), cite that instead of `built.min.js:1-400`.]** **No ES-module (`import`/`export`) syntax was found in any of the 11
JS-bearing target jars' source (non-minified) files.**

**No React/Vue/Angular dependency anywhere in the 11 JS-bearing jars.** A scripted search across all
`.js` entries of `themeN5`, `uxBuilder`, `hx`, `bajaux`, `bajaScript`, `webEditors`, `webChart`,
`smartTableHx`, `wiresheet`, `kitPx`, `gx` for `React`/`ReactDOM`/`Vue.`/`angular.module`/`import React`
returned exactly one hit — `bajaux.jar:rc/lifecycle/WidgetManager.js:462` — and reading it in context shows
it is doc-comment prose ("the `dom` parameter... could be: a string, an `HTMLElement`, a jQuery instance,
**a React virtual DOM node**, or any other DOM-element-like object") describing an accepted *input shape*,
not a dependency. `[CERT]` (`bajaux.jar:rc/lifecycle/WidgetManager.js:460-464`). bajaux instead ships its
own hand-rolled virtual-DOM layer, unchanged from the N4-documented architecture (B204 remit): `rc/spandrel.js`,
`rc/spandrel/{DiffQueue,SpandrelWidget,DynamicSpandrelWidget,diff,jsx,workflow}.js` are all still present in
this beta's `bajaux.jar`. `[CERT]` (`bajaux.jar` namelist, `rc/spandrel*` subtree).

## 21.3 — Themes: `themeN5` is a genuinely new semantic-token/dark-mode system; `themeLucid`/`themeZebra` are unchanged legacy skins `[CERT]`

`themeN5` did not exist in N4 (N4's theme roster was `themeHoneywell-ux`/`themeLucid-ux`/`themeOptimizer-ux`/
`themeZebra-ux` — no `themeN5*`; `[CERT]` `find` census, `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules`).
Its NSS files are structurally different from the legacy themes:

- **CSS custom-property tokens, `:root`/`var()`, light+dark variants.** `nss/light.nss`/`nss/dark.nss` each
  `@import` a matching `palette/{light,dark}-palette.nss`, which in turn `@import`s `palette/palette.nss`
  (raw hex ramps: `--blue10`..`--blue110`, `--green10`..`--green110`, `--grey0`..) and
  `palette/brand-{light,dark}.nss` (semantic remaps: `--brand-accent-primary: var(--brand70)`,
  `--brand-accent-hover: var(--brand80)`). `nss/structure.nss` (56,554 bytes) holds shared non-color tokens
  (`--buttonBorderRadius: 4px`, `--defaultFont: 16px sansserif`) referenced via `var(--x)` throughout,
  matching Block 10's §10.6 NSS2 `:root{--var}`/`var(--x)` description exactly. `[CERT]`
  (`themeN5.jar:nss/{light,dark,structure}.nss` and `themeN5.jar:palette/{palette,brand-palette,
  brand-light,brand-dark,light-palette,dark-palette}.nss`, full text of each, this session).
- **Named Figma provenance and a legacy-token carve-out.** `palette/dark-palette.nss`'s header comment
  states "Figma variables have been added to this file for convenience... Legacy variables (added prior to
  Aug 2026) are retained only where existing widgets still depend on them" — i.e. the semantic-token system
  was introduced (or at least dated) as an Aug-2026-era rework, with an explicit backward-compat seam for
  pre-existing widget styling. `[CERT]` (`themeN5.jar:palette/dark-palette.nss:1-12`).
- **A dedicated brand font (Figtree, 14 weight/style TTFs) and true dark/light asset trees**
  (`themeN5.jar` has separate `dark/imageOverrides/` and top-level `imageOverrides/`, plus `hx/theme-{dark,light}.css`
  and `ux/theme-{dark,light}.css`). `[CERT]` (`themeN5.jar` namelist, `fonts/`+`dark/`+`hx/`+`ux/` entries).
- **`themeLucid.jar`/`themeZebra.jar` carried over unchanged in kind.** Both existed in N4 (as
  `themeLucid-ux.jar`/`themeZebra-ux.jar`) and in N5 keep the same legacy shape: `themeLucid.jar` is 87% PNG
  sprite overrides (940 of 1076 entries under `imageOverrides/`) with a single `less/`+`nss/` pair and **no**
  `dark/` tree or `palette/` semantic tokens; `themeZebra.jar` similarly has `less/`+`fonts/`+one `nss/` file
  and no dark variant. `[CERT]` (`themeLucid.jar`/`themeZebra.jar` namelists, this session). Both ship a
  `package.json` (Zebra's: `grunt ~1.0.1`, `grunt-contrib-{concat,imagemin,less,watch}`,
  `grunt-spritesmith`, `pixelsmith`) confirming the Grunt-based sprite/LESS build pipeline is still the
  legacy-theme tooling, distinct from whatever rebuilt `themeN5`'s Babel-bundled JS (§21.2). `[CERT]`
  (`themeZebra.jar:package.json`, full text).

**Net:** `themeN5` is a real architectural addition (semantic design-token theme with light/dark modes,
Figma-sourced palette, own webfont), not a renamed copy of an existing theme; `themeLucid`/`themeZebra` are
preserved as-is for compatibility, unmodernized. `[INFER]` from the structural comparison above.

## 21.4 — `uxBuilder`: same Px→browser bridge documented in N4 (B895/B922), not a new visual builder `[CERT]`

The gap prompt speculates `uxBuilder` might be "a new visual builder." It is not new: N4 already shipped
`uxBuilder-wb.jar`+`uxBuilder-ux.jar` (`[CERT]` `find` census, N4 modules dir), and N4 corpus Blocks 895/922
already identified and documented it in full as the mechanism that renders a Workbench Px view as a browser
bajaux widget tree — `BWebWidgetWrapper` (agent bridge), `UxBuilderServlet` (serves Px XML/data/media over
HTTP, `/xml/|/data/|/media/` routes), `PxUxAgentFilter`/`PxUxDecoder` (decides which widget agents render as
ux, decodes Px→ux widget tree) — REMIT, not re-derived here. This beta's single consolidated `uxBuilder.jar`
carries the **identical class names** at the same relative package paths:
`com/tridium/uxBuilder/{BWebWidgetWrapper, servlet/{UxBuilderServlet,PxUxAgentFilter,PxUxDecoder,BPxUxRpc},
ui/{BUxMedia,UxMediaUtil,UxValidationUtil}}` — a structural 1:1 match to the N4-documented mechanism.
`[CERT]` (`uxBuilder.jar` namelist, `com/tridium/uxBuilder/` subtree, this session; N4 class identity per
B895 §895.4/§895.5 and B922, both remit).

**New in this jar vs. what B895/B922 covered**: a `ux/make/` sub-package —
`BUxMwActionBatch`/`BUxMwBoundLabel`/`BUxMwChartWidget`/`BUxMwFromPalette`/`BUxMwPropertyBatch`/
`BUxMwPxInclude`/`BUxMwWorkbenchView` — plus three field editors
(`ux/fe/BActionArgEditor`/`BWidgetEventEditor`/`BWidgetPropertyEditor`). `[CERT]` (`uxBuilder.jar` namelist,
`com/tridium/uxBuilder/ux/{make,fe}/` subtree). These are consistent with configuring *what* gets rendered
(binding a palette-sourced widget, an action batch, a Px include, property/event wiring) rather than a
freeform drag-and-drop design canvas; B922 already flagged the `-ux` client-JS half as jar-only/unreadable
from N4, so whether this `ux/make/`+`ux/fe/` set is itself new material or was simply not enumerated by
B922's narrower scope is **left open** — see child gap B21-G1.

## 21.5 — Workbench: still Swing/AWT at the shell level; JavaFX and TeamDev JxBrowser (Chromium) both present as embedded-content mechanisms `[CERT]`+`[INFER]`

`workbench.jar`'s `module-info` requires — among the expected `niagara.*`/`java.desktop`/`java.logging` set
— **`javafx.base`, `javafx.controls`, `javafx.graphics`, `javafx.web`** (all `ACC_STATIC_PHASE`, i.e.
optional at compile/runtime), plus `jdk.jsobject`, embedded **Jetty 12.1.13**
(`org.eclipse.jetty.ee11.servlet`/`org.eclipse.jetty.ee11.websocket.jetty.server`), **jakarta.servlet
6.1.0**, **`com.nimbusds.oauth2.sdk`** (OAuth2 client), **`org.bouncycastle.fips.tls`**, and
**`owasp.encoder` 1.4.0**. `[CERT]` (`workbench.jar:module-info.class`, `javap -v` disassembly, this
session — full `requires` list; `sha256(workbench.jar)=487ea4ea304edb6d564fc33086e2a15be30fff5c6a29ab781ac97687147555af`).

**JxBrowser is a thin, reflection-heavy 98 KB wrapper module; the actual Chromium engine is a separate
third-party binary distribution, not bundled in the module jar.** `jxBrowser.jar` has only 31 entries, all
19 non-META classes (`BJxWebBrowserImpl` + 8 inner classes, `JxBrowserSnoopWriter`, `JxBrowserUtil`,
`JxJs`, `StandaloneJxBrowser`, `WbJxBrowserUtil`, `interop/JxBroadcastChannel`), several literally named
`*ReflectionWrapper` (`BiConsumerReflectionWrapper`, `FunctionReflectionWrapper`,
`RunnableReflectionWrapper`, `SupplierReflectionWrapper`) — a reflective-invocation pattern over the real
JxBrowser API rather than a hard compile-time-only dependency. `[CERT]` (`jxBrowser.jar` namelist, this
session). Its `module-info` requires `jxbrowser` and `jxbrowser.swing` (both `ACC_TRANSITIVE
ACC_STATIC_PHASE`, version `#0` = unversioned/automatic module) plus `javafx.graphics`. `[CERT]`
(`jxBrowser.jar:module-info.class`, `javap -v`, this session;
`sha256(jxBrowser.jar)=089ef51ce0ae0de64342e522785a9de597bc98c44791facd7c73e9cc938f1907`). Decompiling
`BJxWebBrowserImpl.class` (Vineflower, into `/tmp/claude-1000/n5b21/dec/`, scratch — decompiled-tree
citations below are `extern` per METHODOLOGY §11) confirms it `extends com.tridium.ui.swing.BSwingWidget`
and constructs a `com.teamdev.jxbrowser.view.swing.BrowserView` inside a `javax.swing.JPanel` — i.e. the
Chromium view is hosted as a Swing component, the same integration shape as N4's `BWebWidget`/`BWebBrowser`
(B1000 remit: "Chromium/JxBrowser... renders the bajaux container HTML page"). `[CERT]`
(`/tmp/claude-1000/n5b21/dec/BJxWebBrowserImpl.java:59,96,109` — imports of `BrowserView`, `BSwingWidget`,
`BWebWidget`; `extern`, decompiled scratch, jar sha256 above anchors identity). The actual Chromium engine
ships as a **separately licensed, versioned distribution** at
`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/jxbrowser/`: `jxbrowser-9.5.0.jar` (13.9 MB core API),
`jxbrowser-javafx-9.5.0.jar`, `jxbrowser-swing-9.5.0.jar`, `jxbrowser-swt-9.5.0.jar` (view-toolkit adapters,
~220–255 KB each), and `jxbrowser-win64-9.5.0.jar` (**140 MB** — the actual bundled Chromium/CEF native
binary for Windows x64), each with a detached `.sig` signature file. `[CERT]` (`ls -la`/`unzip -l`
directory census, this session; version also independently confirmed inside `WbJxBrowserUtil` decompiled
source: `getCrashDirectory()` resolves `.config/jxbrowser/9.5.0/crash-reports/` on Linux, and
`getDefaultTimeout()`'s catch-log literally says `"...via JxBrowser 7.30.3 API..."` — a **stale
error-message string** left over from an earlier JxBrowser version bump, `extern`,
`/tmp/claude-1000/n5b21/dec/WbJxBrowserUtil.java:257,298`).

`WbJxBrowserUtil`'s `module://` URL interception (`loadModuleResource`) rewrites `https://workbench/module/*`
requests back into `module://` ORDs and serves the target module's file bytes with
`Access-Control-Allow-Origin: *` — this is the mechanism by which a JxBrowser-hosted page reaches a
module's own `rc/`-resource files. `[CERT]` (`/tmp/claude-1000/n5b21/dec/WbJxBrowserUtil.java:66-144`).
Module file permission annotations on `jxBrowser.jar`'s `module-info` grant read on
`${user.home}/AppData/Local/JxBrowser/-` (Windows profile dir), read/write on
`${niagara.home}/JxBrowser/-` and `${user.home}/.config/jxbrowser/-` (Linux profile dir), plus a
`GrantNiagaraBasicPermission(CLOUD_TOKEN)` and an unrestricted `GrantRuntimeExecPermission("*")` — matching
Block 10 §10.5's JDK-25 permission-annotation model (REMIT, not re-derived). `[CERT]`
(`jxBrowser.jar:module-info.class` annotations, `javap -v`, this session).

**A second, separate embedded-browser implementation exists using JavaFX's own WebView, not JxBrowser.**
`workbench.jar` contains `com/tridium/workbench/web/browser/fx/BFxWebBrowserImpl` (an `Access-Control-Allow-Origin`
string hit was found in its inner `ModuleURLConnection` class — the same module-resource-serving pattern as
`WbJxBrowserUtil`, independently implemented) alongside `com.tridium.jx.browser.BJxWebBrowserImpl`.
`[CERT]` (grep-over-class-bytes census, this session: `workbench.jar:com/tridium/workbench/web/browser/fx/
BFxWebBrowserImpl$ModuleURLConnection.class`). Two concrete implementations of the same "embed a browser in
a Swing widget" contract — one on JavaFX's WebKit-based `WebView` (`javafx.web`, required transitively by
`workbench.jar`), one on TeamDev JxBrowser's Chromium (`jxBrowser.jar`) — is consistent with an
engine-selectable/fallback design (e.g. JxBrowser unavailable, disabled via the
`niagara.jxbrowser.disable` system property found in `WbJxBrowserUtil` — `[CERT]`
`/tmp/claude-1000/n5b21/dec/WbJxBrowserUtil.java:61`, or unsupported on a given platform) rather than a full
migration off Chromium; which one is the *default* for the standard `BWebWidget`/`BWebBrowser` PX type is
**not settled by this session's evidence** — see child gap B21-G2. `[INFER]`.

**No trace of Web Launcher/Java Web Start** was found anywhere in the N5 install tree searched (`bin/`,
module names) — no `webstart`/`launch`/`jnlp`-named files or modules — consistent with Block 10's BC-12
("Web Launcher + Kiosk removed", REMIT, not re-derived) and with the module-info evidence above showing
`bajaux`/`hx`/JxBrowser/JavaFX-WebView as the surviving browser-hosting mechanisms. `[CERT]` (`find`
census, N5 install root + config/modules dir, no matches).

## 21.6 — `pxEditor`/`kitPx`: no `-wb`/`-ux` split remaining, structurally unchanged roles `[CERT]`

`pxEditor.jar` (393 entries, 357 `.class`, **zero** `.js`/`rc/` content) is purely the Workbench-side Px
authoring tool — consistent with N4's `pxEditor-wb.jar` (no `-ux` counterpart ever existed for pxEditor in
the N4 tree searched: `find` returned only `pxEditor-wb.jar`, §21.7 table). `[CERT]` (`pxEditor.jar`
namelist; N4 `find` census). `kitPx.jar` (152 entries: 92 `.class` + 32 `rc/`, 30 of them `.js`) merges
N4's split `kitPx-wb.jar`+`kitPx-ux.jar` into one module, carrying both the Workbench field-editor classes
and the browser-side JS/CSS/LESS — same JPMS single-jar consolidation pattern Block 10 documents generally
(REMIT). `[CERT]` (`kitPx.jar` namelist; N4 `find` census, §21.7).

## 21.7 — N4→N5 per-jar split census (remit-adjacent, new counts) `[CERT]`

| N5 jar (this gap) | N4 split (found this session) | Consolidation |
|---|---|---|
| `bajaux.jar` | `bajaux-rt.jar` + `bajaux-ux.jar` | 2→1 |
| `bajaScript.jar` | `bajaScript-ux.jar` | 1→1 (renamed, no `-ux` suffix) |
| `hx.jar` | `hx-wb.jar` | 1→1 |
| `uxBuilder.jar` | `uxBuilder-wb.jar` + `uxBuilder-ux.jar` | 2→1 |
| `themeN5.jar` | *(none — new module)* | n/a |
| `themeLucid.jar` | `themeLucid-ux.jar` | 1→1 |
| `themeZebra.jar` | `themeZebra-ux.jar` | 1→1 |
| `workbench.jar` | `workbench-wb.jar` | 1→1 |
| `jxBrowser.jar` | `jxBrowser-wb.jar` | 1→1 |
| `gx.jar` | `gx-rt.jar` + `gx-ux.jar` + `gx-wb.jar` | 3→1 |
| `svg.jar` | `svg-wb.jar` | 1→1 |
| `kitPx.jar` | `kitPx-wb.jar` + `kitPx-ux.jar` | 2→1 |
| `pxEditor.jar` | `pxEditor-wb.jar` | 1→1 |
| `smartTableHx.jar` | `smartTableHx-wb.jar` | 1→1 |
| `webChart.jar` | `webChart-rt.jar` + `webChart-ux.jar` | 2→1 |
| `webEditors.jar` | `webEditors-ux.jar` | 1→1 |
| `wiresheet.jar` | `wiresheet-wb.jar` + `wiresheet-ux.jar` | 2→1 |

`[CERT]` (`find -maxdepth 1 -iname` census against
`/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules`, this session, per row). `themeN5` is the only
module in this gap's list with **no** N4 predecessor of any name. `svgBatik.jar` was not searched for an N4
equivalent (out of the gap's named list; included in §21.1 only because it is `svg.jar`'s companion Batik
engine).

## 21.8 — Implications for DashboardPan-ux: servlet API is Block 10's territory; resource-serving and no new CSP found `[CERT]`+`[INFER]`

The `javax.servlet`→`jakarta.servlet` migration that directly affects `DashboardPan-ux`'s
`BDashboardServlet`/`DashboardRbacHelper` is **already fully closed by Block 10** (§10.11 CHK-3, citing
`BDashboardServlet.java:20-21,93-94,134-135,...` and the `DashboardPan-ux.gradle.kts:54` artifact-coordinate
change) — REMIT, not re-derived. This session's contribution is narrower: confirming the servlet-stack
version landing on the *browser-UI* modules that would host or link to a DashboardPan-style static
page/servlet. `hx.jar`'s `module-info` requires `jakarta.servlet 6.1.0` directly (not just transitively via
`niagara.web`), and separately requires `org.eclipse.jetty.io 12.1.13`, `org.json 20260814`, and
`owasp.encoder 1.4.0` — the same Jetty-12/Servlet-6 generation as `workbench.jar` (§21.5). `[CERT]`
(`hx.jar:module-info.class`, `javap -v`, this session). A scripted search for
`Content-Security-Policy`/`X-Frame-Options`/`X-Content-Type-Options`/`Strict-Transport-Security` string
constants across every `.class` file in `workbench.jar`, `hx.jar`, `bajaux.jar`, `webEditors.jar`, and
`gx.jar` found **zero hits** in any of those five jars (only a pre-existing `Access-Control-Allow-Origin`
literal, in both the JxBrowser and JavaFX-WebView module-resource loaders, §21.5). `[CERT]` (byte-level
`grep`-in-Python census, this session). This is negative evidence, not proof of absence platform-wide — the
search covered five specific UI-layer jars, not `niagara.web`/`niagara.jetty` (the modules that would own a
station-wide security-header policy) and not any live-station HTTP response (no runnable N5 station this
session, same constraint as Blocks 2/4/10). `[INFER]` from the negative result: nothing in the searched
jars suggests DashboardPan-ux's static-HTML+vanilla-JS+`fetch()` pages would newly need a CSP-compliant
rewrite (no inline-script/`nonce` machinery was found bolted onto the browser-UI layer) — but this is not a
substitute for testing the actual served page, and the resource-root/`@ModuleResources` mechanics that
govern *how* `rc/` gets exposed over HTTP are Block 10 §10.9's territory (REMIT). See child gap B21-G3.

## 21.x — Self-verification (METHODOLOGY §11)

**Type:** `standard`. **Marker tally (manual — `verify-block.sh` is an N4-corpus tool, not present/adapted
for the `niagara5-research` corpus; this and prior niagara5 blocks self-count):** `[CERT]` ≈ 46,
`[INFER]` ≈ 6. Ratio `[INFER]`/`[CERT]` ≈ 0.13 — low, consistent with an evidence-dominant block backed by
direct zip/`javap`/decompile reads rather than synthesis.

**Decompiled-tree citations (METHODOLOGY §11 explicit declaration):** citations into
`/tmp/claude-1000/n5b21/dec/{WbJxBrowserUtil,BJxWebBrowserImpl}.java` are `extern` — this is a scratch
Vineflower decompile, not preserved in the corpus (no `organized/` directory exists in
`niagara5-research`, unlike the N4 corpus convention). Anchor is the source jar's own sha256, given inline
at first citation (jxBrowser.jar). 0 of these resolved automatically; all were confirmed by direct reading
of the decompiled source this session (token-check: 6/6 quoted identifiers/strings — `BrowserView`,
`BSwingWidget`, `BWebWidget`, `getCrashDirectory`'s `9.5.0` path literal, `getDefaultTimeout`'s `7.30.3`
stale string, `loadModuleResource`'s `module://` rewrite — all read verbatim in the decompiled file, not
recalled).

| # | Claim | Marker | Citation | Verified? |
|---|---|---|---|---|
| 1 | All 18 target modules present at 5.0.0.28 | `[CERT]` | §21.1 table | Y — `zipfile` open succeeded, 18/18 |
| 2 | JS module system is AMD/RequireJS, not ES modules; jQuery required | `[CERT]` | §21.2 | Y — direct file read |
| 3 | Built bundles are Babel-transpiled but stay AMD-wrapped (no webpack/SystemJS) | `[CERT]` | §21.2 | Y — grep-in-Python, 0 hits for 3 markers |
| 4 | No React/Vue/Angular dependency; one doc-comment mention only | `[CERT]` | §21.2 | Y — read in context |
| 5 | `themeN5` has no N4 predecessor; is a semantic-token/dark-mode system | `[CERT]` | §21.3, §21.7 | Y — `find` census + NSS file read |
| 6 | `themeLucid`/`themeZebra` unchanged legacy sprite/LESS skins | `[CERT]` | §21.3 | Y — namelist + `package.json` read |
| 7 | `uxBuilder` = N4's already-documented Px→browser bridge, not new | `[CERT]` | §21.4 | Y — class-name 1:1 match vs B895/B922 remit |
| 8 | `ux/make/`+`ux/fe/` sub-packages not previously enumerated by B922 | `[CERT]`/open | §21.4, B21-G1 | Partial — presence confirmed, novelty vs N4 not settled |
| 9 | Workbench requires JavaFX modules + Jetty 12/jakarta.servlet/OAuth2/BouncyCastle-FIPS | `[CERT]` | §21.5 | Y — `javap -v module-info` |
| 10 | JxBrowser module is a thin reflective wrapper; real Chromium ships separately as jxbrowser 9.5.0 | `[CERT]` | §21.5 | Y — namelist + `bin/ext/` census + decompile |
| 11 | JxBrowser hosts via Swing (`BrowserView` in a `JPanel`/`BSwingWidget`) | `[CERT]` | §21.5 | Y — decompiled import list |
| 12 | A second JavaFX-WebView browser impl (`BFxWebBrowserImpl`) coexists; default unknown | `[CERT]`/`[INFER]` | §21.5, B21-G2 | Partial |
| 13 | No Web Launcher/webstart/jnlp traces found | `[CERT]` | §21.5 | Y — `find`, 0 matches |
| 14 | `pxEditor`/`kitPx` split counts vs N4 | `[CERT]` | §21.6, §21.7 | Y — `find` census |
| 15 | No CSP/X-Frame-Options/etc. header strings in 5 searched UI jars | `[CERT]` | §21.8 | Y — byte grep, 0 hits (negative evidence, scope-limited) |

**Artifacts**: block file written; `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` regeneration is out of scope
for this READ-ONLY task (not run — the task instruction was to write exactly this one file and touch no
other).

## 21.x — Named child gaps

- **B21-G1** — Is `uxBuilder.jar`'s `ux/make/`+`ux/fe/` sub-package (`BUxMwActionBatch`,
  `BUxMwFromPalette`, `BWidgetPropertyEditor`, etc.) genuinely new in N5, or was it already present in N4's
  `uxBuilder-ux.jar` but simply not enumerated by B922 (which explicitly flagged the `-ux` client-JS half as
  "jar-only, typed unavailable")? Requires decompiling N4's `uxBuilder-ux.jar` classes and diffing against
  this jar's `ux/make/`+`ux/fe/` set. `investigable`.
- **B21-G2** — Which embedded-browser implementation (`BJxWebBrowserImpl`/JxBrowser-Chromium vs
  `BFxWebBrowserImpl`/JavaFX-WebView) is the *default* for the standard PX `BWebWidget`/`BWebBrowser`
  widget type, and under what condition (platform, `niagara.jxbrowser.disable`, licensing) does N5 fall
  back to the other? Requires decompiling `BWebBrowser`/`BWebWidget`'s implementation-selection logic in
  `workbench.jar` (`com/tridium/workbench/web/browser/`) — not read this session beyond the one grep hit.
  `investigable`.
- **B21-G3** — Does `niagara.web`/`niagara.jetty` (not among this gap's 18 target modules) inject any
  security headers (CSP, `X-Frame-Options`, `Referrer-Policy`) at the station HTTP-server level that would
  affect a `DashboardPan`-style `BWebServlet`-served static page, independent of the five UI jars searched
  in §21.8? Requires a targeted census of `niagara.web.jar`/`niagara.jetty.jar` (not opened this session)
  or, better, a live-station HTTP response capture (`[CERT-hw]`) once a runnable N5 install/station exists —
  same blocker noted in Blocks 2/4/10. `blocked-on-source` (no runnable station) for the live half;
  `investigable` for the static jar census half.
- **B21-G4** — `WbJxBrowserUtil.getDefaultTimeout()`'s catch-block log string says "via JxBrowser 7.30.3
  API" while the actually-bundled engine is 9.5.0 (`bin/ext/jxbrowser/jxbrowser-9.5.0.jar`) — confirm
  whether this is purely a stale/unmaintained log message (cosmetic) or whether it signals a
  version-negotiation code path still targeting an older JxBrowser API surface that could behave
  differently under 9.5.0. Requires reading the full `getDefaultTimeout()` try body and
  `Navigation.defaultTimeout()`'s actual 9.5.0 behavior. `investigable`.

## 21.x — Connections

- **[Block 10]** — the transition-guide remit for NSS2 syntax (§10.6), the `uiChangelog.html` BC-30..32
  breaking changes (§10.7), the JPMS resource-root/`@ModuleResources` mechanics (§10.9), and the
  `javax.servlet`→`jakarta.servlet` migration already fully worked for `DashboardPan-ux` (§10.11 CHK-3).
  This block adds the concrete module inventory (§21.1), the AMD/Babel/no-React JS-stack evidence (§21.2),
  the `themeN5` vs legacy-theme structural contrast (§21.3), the uxBuilder identity correction (§21.4), the
  JxBrowser/JavaFX-WebView dual-engine and Workbench-still-Swing findings (§21.5), and the negative
  CSP-header search (§21.8) that Block 10 did not cover.
- **[Block 4]** — `docDeveloper.jar`/`help.jar` (the shipped-documentation half of the same 5.0.0.28
  module set this block censuses for UI code); both blocks read the same install/config-modules roots.
- **N4 corpus (remit)** — [B195]/[B427] (Palladium/Curium/Custom Swing theme families vs. `.ux-*` CSS
  theming — the N4 baseline this session's §21.3/§21.5 build on), [B204] (bajaux's own spandrel virtual-DOM,
  confirmed still present unmodified in §21.2), [B895]/[B922] (uxBuilder's original identification, confirmed
  structurally intact in §21.4), [B1000] (Chromium/JxBrowser already embedding the WebWidget container in
  N4 — confirmed the same integration shape survives into N5 in §21.5), [B1006] (Hx server-rendered PX
  binding layer — not touched by this block, listed for completeness since it shares the `hx` module).
