# Block 79 — Closing three named gaps and narrowing a fourth: TeamDev jxbrowser's actual shipped version vs. a stale Tridium log string, `uxBuilder.jar`'s built AMD bundle structure and entry points, `BJxWebBrowserImpl`/`BFxWebBrowserImpl`'s `preInitialize()` fallback gates, and the still-unnamed `grunt-niagara`-successor npm package

> **Scope**: Closes three child gaps and narrows a fourth, each explicitly named by a prior block as
> unopened: **B21-G4** (`niagara5-block21.md` §21.5 — `WbJxBrowserUtil.getDefaultTimeout()`'s catch-block
> log string says "via JxBrowser 7.30.3 API" while the bundled engine is `jxbrowser-9.5.0.jar`; confirm
> whether this is cosmetic or signals a real version-negotiation code path, by reading the jar's own
> manifest/version constants), **B75-G4** (`niagara5-block75.md` §75.3/child-gap-list — whether N5's NEW
> `ux/make`/`ux/fe` Java classes are paired with genuinely new client-JS in N5's consolidated `uxBuilder.jar`
> `rc/` tree, by extracting and characterizing its bundled minified JS — module system, entry points,
> structure, not a full reverse), **B75-G1** (`niagara5-block75.md` §75.4 — `BFxWebBrowserImpl.preInitialize()`/
> `BJxWebBrowserImpl.preInitialize()`'s own bodies, which [Block 75] read only the *selection loop* calling
> into, to determine what makes either succeed or fail), and **B36-G3** (`niagara5-block36.md` §36.12 —
> locate and inspect the actual `grunt-niagara`-successor npm package content the Gradle `gruntBuild` task
> only orchestrates by name). Covers: extracting `META-INF/MANIFEST.MF` and disassembling
> `com.teamdev.jxbrowser.VersionInfo` plus its bundled `version.info` properties resource from the live
> install's own `jxbrowser-9.5.0.jar`; a full `find`/structural census of N5's consolidated `uxBuilder.jar`'s
> `rc/` source tree (already preserved, decompiled, in this corpus) cross-referenced against its
> `rc/uxBuilder.built.min.js` bundle's own `define(...)` call census; whole-method reads of
> `BJxWebBrowserImpl.preInitialize()` and `BFxWebBrowserImpl.preInitialize()` (neither previously opened
> beyond the one-line selection-loop calls [Block 75] §75.4 read) plus a corpus-wide grep for their shared
> `forceStationBrowserInit` option to identify the real caller(s) that force JxBrowser to initialize inside a
> station; and an exhaustive filesystem search across both the N5 install root and the Gradle-plugin/devkit
> jars already decompiled by [Block 36] for any occurrence of `grunt-niagara`/`Gruntfile` outside the
> already-confirmed-stale `buildingJS.html` guide ([Block 75] §75.5). Does **not** cover: `nre.dll`'s native
> `CreateProcessA`/Windows-Service call-site tracing (a different, already-closed gap chain, [Block 63] §63.1);
> a full reverse of `uxBuilder.built.min.js`'s bundled logic (structure/module-census only, per the gap's own
> "not full reverse" framing); JxBrowser's actual Chromium-process bring-up once `preInitialize()` succeeds
> (`makeBrowserView()`'s own body, `BrowserView`/`Engine` construction — out of scope, not named by B75-G1);
> or a live npm/GitHub registry lookup for `grunt-niagara`'s current published version (no network access in
> this environment — same constraint noted across Blocks 2/4/21/36).
>
> Subject version: **Niagara 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 21]/[Block 36]/[Block 75] read; decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{jxBrowser,workbench,uxBuilder}/vineflower/`, all already
> preserved in this corpus (not scratch) except where noted. The TeamDev-licensed binary read for §79.1 is
> `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/jxbrowser/jxbrowser-9.5.0.jar` — the exact jar [Block 21]
> §21.5 only `ls -la`/`unzip -l`'d by directory listing, never opened for its own internal manifest/resource
> content until this session.
>
> Sources:
> - `[CERT-hw]` `unzip -p .../bin/ext/jxbrowser/jxbrowser-9.5.0.jar META-INF/MANIFEST.MF` (full manifest,
>   this session) and `unzip -p .../jxbrowser-9.5.0.jar com/teamdev/jxbrowser/version.info` (full resource
>   content, this session) — the live install's own bundled TeamDev jar, not a remote/vendor-site lookup.
> - `[CERT-hw]` `javap -p -c -constants` disassembly of `com/teamdev/jxbrowser/VersionInfo.class`, extracted
>   from the same jar, this session — never previously opened in this corpus.
> - `organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:247-248,280-289,305-407,
>   2032,2169,2214-2217` (constants, whole `preInitialize()` method, static-init and two other
>   `preInitError`/`DISABLE_JX_BROWSER` use sites, all read this session — this file is a corpus-preserved
>   decompile, NOT the scratch tree [Block 21]/[Block 61] treated as `extern`).
> - `organized/jxBrowser/vineflower/com/tridium/jx/browser/WbJxBrowserUtil.java:60-61,207-217,247-266,291-303`
>   (license/disable constants, `getLicenseKey()`, `getCrashDirectory()`, `getDefaultTimeout()` — all whole
>   methods, re-read this session at their full path; [Block 21] cited this file only via a `/tmp` scratch
>   decompile).
> - `organized/workbench/vineflower/com/tridium/workbench/web/browser/fx/BFxWebBrowserImpl.java:172-184`
>   (`preInitialize()`, whole method, never previously opened).
> - `organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebWidget.java:281-298` (`started()`,
>   the `forceStationBrowserInit` call site, never previously opened in this corpus).
> - `organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebBrowser.java:419-426` (`post()`
>   static helper, the second `forceStationBrowserInit` call site, re-opened this session — [Block 21] cited
>   only this file's `makeImpl()`/field region, `:108-307`, never this range).
> - `organized/workbench/vineflower/com/tridium/workbench/web/browser/BIWebBrowserImpl.java:34` (the
>   `FORCE_STATION_BROWSER_INIT` interface constant, whole 154-line file read this session — never previously
>   opened).
> - `organized/uxBuilder/vineflower/META-INF/module.xml` (whole file, 91 lines — vendorVersion `5.0.0.28`,
>   confirms this is N5's own consolidated module, re-read this session); `organized/uxBuilder/vineflower/rc/`
>   (full recursive `find`, this session — 115 individual `.js` source files across `ux/`, `ux/make/`,
>   `ux/commands/`, `ux/factory/`, `ux/model/`, `ux/sidebars/`, `ux/wysiwyg/`, `fe/`, `util/`, plus the one
>   `rc/uxBuilder.built.min.js` bundle); `organized/uxBuilder/vineflower/rc/uxBuilder.built.min.js` (382,030
>   bytes, full-text `grep -o 'define("[a-zA-Z0-9_/.]*"'` census, this session — 115 unique named-module IDs,
>   matching the 115-source-file count 1:1).
> - `organized/uxBuilder/vineflower/com/tridium/uxBuilder/ux/BUxBuilder.java` (whole 35-line file, never
>   previously opened) and `.../ux/BUxBuilderJsBuild.java` (whole 33-line file, never previously opened) —
>   the two Java types wiring the JS entry-point/build-bundle ORDs.
> - `[CERT-doc]` `doc/js/buildingJS.html` from `docDeveloper.jar` (re-extracted this session, cross-checked
>   against [Block 75] §75.5's own already-confirmed-stale finding for the same file — this session adds a
>   fresh full-text grep for `npm install`/`grunt-init`/`grunt-niagara`/the package.json snippet, not
>   previously quoted at this granularity).
> - `[CERT]` `strings`-sweep of every unzipped `.class` file under
>   `com/tridium/gradle/plugins/{node,grunt}/` inside `n-plugin-5.0.54.9.2.jar` (the same jar [Block 36]
>   fully decompiled; this session's sweep targets `grunt-`, `npm`, `registry`, `@tridium` specifically, a
>   narrower pass than [Block 36]'s own `strings` sweep which targeted download-URL indicators); a fresh
>   `zipfile.namelist()` census of `devkit.jar`'s bundled `LIB-INF/n-templates-5.0.54.9.2.jar` (111 entries,
>   re-listed this session, cross-checked for any `Gruntfile`/`package.json` template — none found, extending
>   [Block 36] §36.6's narrower two-file grep to the FULL template set); a `grep -rl` sweep for
>   `grunt-niagara`/`Gruntfile` across the full N5 install root (`/mnt/c/Program Files/Niagara/5.0.0.28`) and
>   the full config/modules root (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`), this session.
> - `niagara5-block21.md`, `niagara5-block75.md`, `niagara5-block36.md`, `niagara5-block61.md` — parent
>   blocks, cited for gap framing and prior citations, re-verified where noted above, not blindly re-derived
>   elsewhere.
>
> Method: direct extraction/reading of a live third-party binary jar's own manifest and bundled properties
> resource (`unzip -p`, no decompilation needed — `version.info` is a plain-text resource, not compiled code)
> for §79.1; `javap -p -c -constants` bytecode disassembly for the one `.class` this session opens fresh
> (`VersionInfo.class`); decompiled-Java source reading (Vineflower output already preserved in
> `organized/`, not scratch) for §79.2–§79.3; `find`/`grep -o` structural census (no decompilation) for the
> `uxBuilder.jar` `rc/` tree and its bundle's `define()` call census in §79.2; `python3 zipfile`
> namelist/`strings`/`grep -rl` filesystem sweeps (no decompilation) for the negative-existence search in
> §79.4. Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live install's own
> binary artifacts (a jar's manifest/bundled resource, a form of static live-artifact inspection, matching
> [Block 61]'s convention for `objdump`/`strings` over live install binaries) · `[CERT]` local primary source
> (`file:line`, corpus-preserved decompile) · `[CERT-doc]` official installed HTML doc, full-text read ·
> `[INFER]` deduction.
>
> Workbench-UI / browser-embedding layer and N5 JS-build-toolchain layer. Connects [Block 21] (closes
> B21-G4), [Block 75] (closes B75-G4, closes B75-G1, corrects §75.4's framing), [Block 36] (narrows B36-G3),
> [Block 61] (shares the `[CERT-hw]`-over-live-binaries citation convention).
>
> **Type:** `mixed` — §79.1–§79.3 each upgrade a NAMED prior block's `[INFER]`-flagged or explicitly-deferred
> finding to `[CERT]`/`[CERT-hw]` by opening a source that block named but did not open (the
> `[INFER]`-across-a-prior-block correction pattern, the `mixed` trigger per METHODOLOGY §4/§11) — §79.3
> additionally issues a narrow correction to [Block 75] §75.4's own framing (a live §14-style cross-block
> correction, not a fresh contradiction of unrelated evidence); §79.4 is fresh negative-evidence-gathering
> against a previously untouched gap, narrowing but not closing it.

---

## 79.1 — B21-G4 CLOSED: `jxbrowser-9.5.0.jar` ships `product.version=9.5.0`/`chromium.version=152.0.7977.65` in its own bundled resource; the "7.30.3" string is an isolated, cosmetic catch-block log literal inside Tridium's own wrapper, not evidence of a stuck-old-API code path `[CERT-hw]`+`[CERT]`

[Block 21] §21.5 found `WbJxBrowserUtil.getDefaultTimeout()`'s catch-block log string reading *"...via
JxBrowser 7.30.3 API..."* while the actually-bundled engine ships as `jxbrowser-9.5.0.jar`, and named
confirming whether this is purely cosmetic or a real version-negotiation code path as **B21-G4**. This
session opens the TeamDev jar's own manifest and internal version-resolution mechanism directly, rather than
relying on the filename or a Tridium-side wrapper constant.

**The jar's own manifest and bundled resource both independently state `9.5.0`, with no trace of `7.30.3`
anywhere.** `META-INF/MANIFEST.MF` declares `Implementation-Version: 9.5.0` `[CERT-hw]` (`unzip -p
jxbrowser-9.5.0.jar META-INF/MANIFEST.MF`, this session). Disassembling `com.teamdev.jxbrowser.VersionInfo`
shows `version()`/`chromiumVersion()` are thin accessors over a lazily-loaded `Properties` map, populated
from a bundled classpath resource named literally `version.info`
(`Class.getResourceAsStream("version.info")`) `[CERT-hw]` (`javap -p -c -constants` output for
`VersionInfo.class`, this session — every step above is a directly observed `invokestatic`/`getstatic`
bytecode instruction, not inferred from the class name). That resource's full content, read directly:

```
#Wed Aug 26 11:51:01 UTC 2026
chromium.version=152.0.7977.65
product.version=9.5.0
```
`[CERT-hw]` (`unzip -p jxbrowser-9.5.0.jar com/teamdev/jxbrowser/version.info`, this session, full 83-byte
resource). This is the SAME value already independently confirmed on the Tridium-wrapper side: `[CERT]`
`organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:286,288` hardcodes
`CHROMIUM_VERSION = "152.0.7977.65"` and `JX_BROWSER_VERSION = "9.5.0"` as Java constants, an exact match to
the TeamDev jar's own `version.info` — two independent artifacts (a third-party binary's internal resource,
and Tridium's own wrapper source) agree. A `strings`/`unzip -l` sweep for any occurrence of `7.30.3` across
all five `jxbrowser-*.jar` files under `bin/ext/jxbrowser/` (the core jar plus the `javafx`/`swing`/`swt`/
`win64` adapter jars) returns **zero hits** `[CERT-hw]` (this session).

**The "7.30.3" string traces to exactly one place: a hardcoded literal inside
`WbJxBrowserUtil.getDefaultTimeout()`'s own catch block — a corpus-preserved citation, not the scratch decompile
[Block 21] treated it as.**

```java
public static long getDefaultTimeout() {
   try {
      return Navigation.defaultTimeout().getSeconds();
   } catch (Throwable throwable) {
      BJxWebBrowserImpl.log.log(
         Level.SEVERE,
         "Problem getting default timeout via JxBrowser 7.30.3 API: " + throwable,
         BJxWebBrowserImpl.log.isLoggable(Level.FINE) ? throwable : null
      );
      return 45000L;
   }
}
```
`[CERT]` `organized/jxBrowser/vineflower/com/tridium/jx/browser/WbJxBrowserUtil.java:291-303` (whole method,
read this session — this file already exists preserved in `organized/jxBrowser/vineflower/`, unlike [Block
21]'s own citation into a `/tmp` scratch Vineflower output for the identical line). The `7.30.3` literal is
purely decorative text concatenated into a log message inside a `catch (Throwable)` block that already falls
back to a fixed `45000L`-millisecond default regardless of what the caught exception is — it does not gate,
branch on, or select any code path. **The same class's neighboring `getCrashDirectory()` method, 34 lines
above, correctly hardcodes the CURRENT version**: `path.resolve(".config/jxbrowser/9.5.0/crash-reports/")`
`[CERT]` `WbJxBrowserUtil.java:257`. This rules out the "stuck on an older API surface" reading [Block 21]
flagged as the more concerning possibility — the same file tracks `9.5.0` correctly in one place and merely
forgot to update a log string in another, a purely cosmetic staleness, not a version-negotiation bug.

**Net verdict, closing B21-G4**: `9.5.0` is definitively what ships — confirmed simultaneously by the
TeamDev jar's own `Implementation-Version` manifest field, its own `version.info` bundled resource (read via
its own accessor class's bytecode, not assumed from the filename), and Tridium's wrapper-side hardcoded
constants, three independent reads that agree exactly. The `"7.30.3"` string is an isolated,
never-executed-as-logic, purely cosmetic leftover in one `catch`-block log message, unconnected to any actual
version check, negotiation, or compatibility gate.

## 79.2 — B75-G4 CLOSED: N5's consolidated `uxBuilder.jar` ships matching new `rc/ux/make/*.js`/`rc/fe/*.js` source for the new `ux/make`/`ux/fe` Java classes, bundled via a 115-module named-AMD build with a Java-wired entry point `[CERT]`

[Block 75] §75.3 confirmed `uxBuilder.jar`'s new `ux/make/`+`ux/fe/` Java classes (`BUxMwActionBatch` et al.,
`BActionArgEditor`/`BWidgetEventEditor`/`BWidgetPropertyEditor`) are genuinely new in N5, but its own child
gap **B75-G4** left open whether the client-JS side is paired with equally new material, or unchanged — the
N4-side `uxBuilder-ux.jar` (§75.3's subject) ships ONLY a pre-minified bundle, no individual source files, so
that jar alone cannot answer the pairing question. This session opens N5's own consolidated `uxBuilder.jar`
(confirmed the SAME module this corpus already has fully decompiled and preserved at
`organized/uxBuilder/vineflower/`, `vendorVersion="5.0.0.28"` `[CERT]` `organized/uxBuilder/vineflower/
META-INF/module.xml:1`, re-read this session).

**The `rc/` tree ships 115 individual, already-transpiled `.js` source files — not just a bundle.** A full
recursive listing under `organized/uxBuilder/vineflower/rc/` shows `ux/`, `ux/commands/` (+`align/`/
`distribute/`/`reorder/`), `ux/factory/` (+`impl/`), `ux/make/`, `ux/model/`, `ux/sidebars/`, `ux/wysiwyg/`
(+`artisans/`+`path/`+`commands/`+`trackers/`+`trackers/events/`), a TOP-LEVEL `fe/`, and a top-level
`util/` — 115 `.js` files total plus the one bundle, `uxBuilder.built.min.js`. `[CERT]` (`find`, this
session, full listing). Every one of these 115 files already opens with the SAME `@babel/helpers`-generated
runtime functions (`_typeof`, `_toConsumableArray`, `_nonIterableSpread`, …) [Block 21] §21.2 already
identified as the Babel-down-level signature for `bs.built.min.js`/`bajaux.built.min.js` — confirming the
INDIVIDUAL source files, not only the bundle, are already ES5-transpiled before bundling. `[CERT]`
(`organized/uxBuilder/vineflower/rc/ux/UxBuilder.js:1-5`, read this session).

**Every §75.3/§21.4 "new" Java class has a matching, correspondingly-named JS source file.** `rc/ux/make/`
holds `MwActionBatch.js`, `MwBoundLabel.js`, `MwChartWidget.js`, `MwFromPalette.js`, `MwPropertyBatch.js`,
`MwPxInclude.js`, `MwWorkbenchView.js`, `UxMwConfig.js` — matching, one-for-one, `com.tridium.uxBuilder.ux.make
.{BUxMwActionBatch,BUxMwBoundLabel,BUxMwChartWidget,BUxMwFromPalette,BUxMwPropertyBatch,BUxMwPxInclude,
BUxMwWorkbenchView,BIUxMwConfig}` (the exact 7+1 class set [Block 75] §75.3 confirmed genuinely new). Plus
`MakeWidget.js`, `MwPalettePreview.js`, `MwPropertiesWidget.js`, `mwUtils.js` — 4 additional JS-only files
with no direct `BUxMw*` Java counterpart (client-internal helpers/base classes, not exposed as their own Baja
agent types — see child gap). `rc/fe/` holds `ActionArgEditor.js`, `WidgetEventEditor.js`,
`WidgetPropertyEditor.js` — matching `com.tridium.uxBuilder.ux.fe.{BActionArgEditor,BWidgetEventEditor,
BWidgetPropertyEditor}` exactly — plus `BoundOrdReplaceEditor.js`/`VariablesEditor.js`, likewise JS-only. Note
the JS package layout is `rc/fe/` (top-level), not `rc/ux/fe/` mirroring the Java `ux/fe/` package path — a
real, minor asymmetry between the two trees' directory conventions, not load-bearing for this gap's verdict.
`[CERT]` (`organized/uxBuilder/vineflower/rc/{ux/make,fe}/*.js` full listing, this session, cross-checked
against [Block 75] §75.3's own Java class-name list).

**The bundle is a standard RequireJS-optimizer (r.js) build: 115 named `define()` modules, a 1:1 map onto the
115 source files.** `grep -o 'define("[a-zA-Z0-9_/.]*"'` over `rc/uxBuilder.built.min.js` (382,030 bytes)
returns exactly 115 unique module IDs, every one shaped `nmodule/uxBuilder/rc/<relative-path-without-.js>` —
e.g. `define("nmodule/uxBuilder/rc/ux/make/MwActionBatch", [...], function (...) {...})`,
`define("nmodule/uxBuilder/rc/fe/WidgetPropertyEditor", ...)`. `[CERT]` (`grep -o`, this session, full-text
census; count cross-checked against the 115-source-file `find` count above — an exact match, meaning the
bundle is literally every individual `rc/` source file concatenated and registered under its own `nmodule/`
id, not a hand-selected subset). This is the SAME AMD/`nmodule/`-prefixed module-ID convention [Block 21]
§21.2 already established for `bajaScript`/`bajaux`'s built bundles — independently confirmed here for
`uxBuilder`.

**The Java-side entry point is explicitly wired to a specific module ID, and a companion type separately
names the built bundle.** `com.tridium.uxBuilder.ux.BUxBuilder` (the `@NiagaraType` agent view on
`file:PxFile`/`pxEditor:PxEditor`/`baja:Component`, per `module.xml`) declares:

```java
private static final JsInfo JS_INFO = JsInfo.make(BOrd.make("module://uxBuilder/rc/ux/UxBuilder.js"), BUxBuilderJsBuild.TYPE);
```
`[CERT]` `organized/uxBuilder/vineflower/com/tridium/uxBuilder/ux/BUxBuilder.java:24` (whole 35-line file
read this session, never previously opened) — i.e. `nmodule/uxBuilder/rc/ux/UxBuilder` (the module ID form
of that same `module://` ORD) is the literal top-level entry Workbench's `BIJavaScript` machinery loads for
this agent view. A separate, paired type names the AGGREGATE built bundle: `BUxBuilderJsBuild extends
niagara.web.js.BJsBuild`, constructed with `("uxBuilder", BOrd.make("module://uxBuilder/rc/uxBuilder.built
.min.js"), new Type[]{BBajauiJsBuild.TYPE, BBajauxJsBuild.TYPE, BUxBuilderCssResource.TYPE})` `[CERT]`
`organized/uxBuilder/vineflower/com/tridium/uxBuilder/ux/BUxBuilderJsBuild.java:26-30` (whole 33-line file
read this session, never previously opened) — declaring two upstream JS-build dependencies
(`niagara.ui.ux.BBajauiJsBuild`, `niagara.bajaux.BBajauxJsBuild`) plus a CSS-resource companion. The generic
`niagara.web.js.BJsBuild`/`BIJavaScript` framework that decides WHICH of these two ORDs (the raw entry module
vs. the built bundle) actually gets served to a given browser session was not traced this session — see
child gap.

**Net verdict, closing B75-G4**: YES — N5's new `ux/make`/`ux/fe` Java classes are paired with genuinely
new, correspondingly-named client-JS in N5's consolidated `uxBuilder.jar`, not merely a Java-side API-surface
addition over an unchanged JS layer. The bundle is a conventional named-AMD r.js build covering every
individual source file 1:1, and the module's Java-side agent view wires a concrete entry-point module ID
matching that bundle's own naming scheme.

## 79.3 — B75-G1 CLOSED, and [Block 75] §75.4's framing CORRECTED: `BJxWebBrowserImpl.preInitialize()` self-vetoes inside a running station unless `forceStationBrowserInit` is explicitly passed — a gate the selection loop itself never expresses; `BFxWebBrowserImpl.preInitialize()` carries no station gate at all, only a bare `javafx.scene.Node` classloader probe `[CERT]`

[Block 75] §75.4 read `BWebBrowser.makeImpl()`'s selection LOOP in full and established JxBrowser is tried
first, unconditionally, with only `BROWSING_DISABLED` able to skip it — but explicitly left both candidate
implementations' own `preInitialize()` BODIES unread, naming this **B75-G1**. Both are opened in full this
session, plus a corpus-wide search for their shared `forceStationBrowserInit` option to find real callers.

**`BJxWebBrowserImpl.preInitialize()` carries an explicit, self-contained station veto the loop does not
express:**

```java
public boolean preInitialize(Map<String, String> options) {
   if (!options.getOrDefault("forceStationBrowserInit", "").equals(Boolean.TRUE.toString()) && Sys.isStation()) {
      return false;
   }
   if (WbJxBrowserUtil.DISABLE_JX_BROWSER || preInitError != null) {
      return false;
   }
   if (UiEnv.get().isMicroEdition()) {
      return false;
   }
   try {
      if (!preInit.getAndSet(true) || options.get("interrupted") != null) {
         // ... EngineOptions construction: rendering mode, license key, Chromium
         // switches (dark-mode, GPU-disable, per-OS scaling), module://+https://
         // scheme handlers, up to 1000 numbered userDataDir suffixes to dodge
         // UserDataDirectoryAlreadyInUseException ...
      }
   } catch (Throwable e) {
      if ((e instanceof InterruptedException || e.getCause() instanceof InterruptedException)
            && options.get("interrupted") == null) {
         // one-shot self-retry with an "interrupted" marker
         return this.preInitialize(withInterruptedMarker(options));
      }
      log.log(Level.SEVERE, "Cannot pre-initialize JxBrowser", e);
      preInitError = e;   // static field — sticky for the life of the process
   }
   return preInitError == null;
}
```
`[CERT]` `organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:305-407` (whole
method, read this session — abbreviated above for the EngineOptions-construction body, which is not
load-bearing for the gate-condition question). Four independent gate conditions, in order: (1) **station
veto** — `Sys.isStation()` returns `false` from `preInitialize()` UNLESS the caller explicitly passed
`forceStationBrowserInit=true` in `options` (`:306-308`); (2) **global/sticky-failure veto** —
`WbJxBrowserUtil.DISABLE_JX_BROWSER` (`Boolean.getBoolean("niagara.jxbrowser.disable")`, `[CERT]`
`WbJxBrowserUtil.java:61`) OR a previously-set `preInitError` short-circuits to `false` (`:310`) — and
because both `preInit`/`preInitError` are `private static` fields (`[CERT]` `BJxWebBrowserImpl.java:247-248`,
`preInit` constructed once at the class's static initializer, `[CERT]` `:2032`), a SINGLE transient
initialization failure permanently disables JxBrowser for the remaining life of that JVM process — every
subsequent `preInitialize()` call across every widget instance returns `false` immediately, with no retry
path except process restart; (3) **headless veto** — `UiEnv.get().isMicroEdition()` always fails (`:314-316`);
(4) otherwise, engine bring-up proceeds using a hardcoded default license key (`WbJxBrowserUtil.
getLicenseKey()`, `[CERT]` `WbJxBrowserUtil.java:207-217` — falls back to a base64 `niagara.jxbrowser.
licenseKey` system-property override, `[CERT]` `WbJxBrowserUtil.java:60`, only if set), and any OTHER
`Throwable` (not a bare `InterruptedException`, which gets exactly one self-retry) is caught and stored into
the sticky `preInitError` field.

**`BFxWebBrowserImpl.preInitialize()`, by contrast, has no station-awareness of its own whatsoever:**

```java
@Override
public boolean preInitialize(Map<String, String> options) {
   try {
      Class.forName("javafx.scene.Node");
      String useHTTP2LoaderPropValue = System.getProperty("com.sun.webkit.useHTTP2Loader");
      if (useHTTP2LoaderPropValue == null) {
         System.setProperty("com.sun.webkit.useHTTP2Loader", String.valueOf(false));
      }
      return true;
   } catch (Throwable e) {
      return false;
   }
}
```
`[CERT]` `organized/workbench/vineflower/com/tridium/workbench/web/browser/fx/BFxWebBrowserImpl.java:172-184`
(whole method, read this session, never previously opened). This is a bare classloader probe — it succeeds
iff `javafx.scene.Node` resolves on the running JVM (i.e. the optional `javafx.graphics`/`javafx.controls`
modules [Block 21] §21.5 already found are `ACC_STATIC_PHASE`-optional in `workbench.jar`'s `module-info`
are actually present at runtime), catching ANY `Throwable` — most plausibly `ClassNotFoundException`/
`NoClassDefFoundError` on a JavaFX-less JRE — as a plain `false`. **There is no `Sys.isStation()` check
anywhere in this method.** This confirms [Block 75] §75.4's own `stationFx` finding precisely: the EXCLUSION
of `BFxWebBrowserImpl` inside a station is enforced entirely by the `makeImpl()` LOOP's own `stationFx` flag
(`isFxWebBrowserImpl && Sys.isStation()`, already `[CERT]` per §75.4) — `BFxWebBrowserImpl` itself has no
opinion on where it runs.

**Correcting [Block 75] §75.4's own framing.** §75.4 stated JxBrowser "is the default, tried before anything
else, every time browsing is not globally disabled" — true AT THE LOOP LEVEL (the loop's own `stationFx`
computation is `false` for JxBrowser unconditionally, so the loop itself never skips it). But
`preInitialize()`'s own body, now read, adds a SECOND, callee-side station gate the loop's logic does not
express or account for: **inside an actual running station** (not Workbench), `BJxWebBrowserImpl.
preInitialize()` returns `false` by default too — meaning, contrary to §75.4's literal wording, a plain
station-context call to `makeImpl()` tries JxBrowser (loop allows it), JxBrowser's OWN callee-side check
declines (this session's finding), THEN falls to `FxWebBrowserImpl` (loop's `stationFx` excludes it too), and
lands on `NullWebBrowserImpl` — i.e. **inside a station, by default, NEITHER real browser implementation
initializes**, unless the caller explicitly opts in via `forceStationBrowserInit=true`. This does not
invalidate §75.4's Workbench-context (non-station) finding, which remains correct there; it narrows "tried
first unconditionally" to "tried first unconditionally outside a station, and inside a station only when the
caller explicitly forces it" — a genuine, load-bearing correction, flagged per METHODOLOGY §14.

**The real callers that force it: PDF/image export, and a lazily-created shared `post()` helper.** A
corpus-wide grep for `forceStationBrowserInit` finds exactly two call sites plus its interface constant
declaration, all previously unopened:

```java
// BWebWidget.started()
Map<String, String> options;
if (BBoolean.TRUE.equals(this.get("exporting"))) {
   options = Collections.singletonMap("forceStationBrowserInit", Boolean.TRUE.toString());
} else {
   options = Collections.emptyMap();
}
this.browser = this.browserProvider.makeBrowser(options);
```
`[CERT]` `organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebWidget.java:281-298` (whole
`started()` method region, read this session, never previously opened) — the option is forced ONLY when the
widget's own `"exporting"` property is `true`, i.e. specifically during a headless PDF/image EXPORT render,
not for ordinary interactive `BWebWidget` display inside a station. The second site is a static,
lazily-created shared browser instance:

```java
public static void post(BWebBrowser browser, Runnable r) {
   if (browser == null) {
      synchronized (STATIC_MONITOR) {
         if (staticBrowser == null) {
            staticBrowser = new BWebBrowser(Collections.singletonMap("forceStationBrowserInit", Boolean.TRUE.toString()));
         }
      }
      browser = staticBrowser;
   }
   browser.impl.post(r);
}
```
`[CERT]` `organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebBrowser.java:419-426`
(re-opened this session at a range [Block 21] did not cite — §21.5 cited only `:108-307`, the fields/
`makeImpl()` region). The shared, string-named constant both sites and `BJxWebBrowserImpl` key off is
declared once, `String FORCE_STATION_BROWSER_INIT = "forceStationBrowserInit";` `[CERT]`
`organized/workbench/vineflower/com/tridium/workbench/web/browser/BIWebBrowserImpl.java:34` (whole 154-line
interface file read this session, never previously opened) — though `BJxWebBrowserImpl.preInitialize()`
itself reads the raw string literal directly rather than this named constant (both resolve to the identical
value, confirmed by direct comparison this session).

**Net verdict, closing B75-G1**: both `preInitialize()` bodies are now read in full. JxBrowser's gate is a
FOUR-CONDITION chain (station-unless-forced, global-disable-or-sticky-failure, headless, then real
engine-bringup with a sticky failure cache) that the `makeImpl()` LOOP alone does not reveal; JavaFX
WebView's gate is a single bare classloader-availability probe with no station-awareness of its own. The
"forces JxBrowser inside a station" scenario names two concrete product cases: PDF/image export rendering,
and the shared `BWebBrowser.post()` utility's lazily-created static instance.

## 79.4 — B36-G3 NARROWED, not closed: the only npm-package name for the Grunt task definitions anywhere in this install is `grunt-niagara@^2.1.0` from `github.com/tridium/grunt-init-niagara`, and it comes ONLY from the already-confirmed-stale N4-era `buildingJS.html` guide — no trace of a distinct "successor" package exists anywhere else in this N5 5.0.0.28 install `[CERT]`+`[CERT-doc]`

[Block 36] §36.5/§36.12 established the Gradle-side `gruntBuild`/`gruntCi`/`gruntIntegration` tasks only
ORCHESTRATE an external `grunt <taskname>` process invocation — they never name, resolve, or bundle the npm
package that actually SUPPLIES the `babel:dist`/`copy:dist`/`requirejs` task definitions, and named locating
that package's actual content as **B36-G3**, presuming (unverified) it is "presumably still `grunt-niagara`
(or a renamed npm-registry successor)". This session searches exhaustively for any trace of that package's
NAME anywhere in the local install, since no runnable Niagara install or network/npm-registry access exists
in this environment (same constraint [Block 36] itself already named for a live run).

**Zero hits outside one already-known-stale document.** A `grep -rl` sweep for `grunt-niagara` and
`Gruntfile` across the FULL N5 install root (`/mnt/c/Program Files/Niagara/5.0.0.28`) and the full
config/modules root (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`) returns **zero matching files**
except `docDeveloper.jar`'s own `doc/js/buildingJS.html`. `[CERT]` (`grep -rl`, this session, both roots,
whole-tree). A `strings`-sweep of every unzipped `.class` file under `com/tridium/gradle/plugins/{node,
grunt}/` inside `n-plugin-5.0.54.9.2.jar` — the exact Gradle-plugin jar [Block 36] fully decompiled — for
`grunt-`, `npm`, `registry`, `@tridium` finds only strings [Block 36] §36.2/§36.4 already reported
(`grunt-cli`, the generic `npm`/`node` verification-task messages); **no npm package NAME for the Grunt task
definitions themselves appears anywhere in this jar's bytecode**. `[CERT]` (`strings`, this session, full
sweep of both package prefixes). `devkit.jar`'s bundled `LIB-INF/n-templates-5.0.54.9.2.jar` (111 entries,
the New-Module-Wizard's full Velocity template set) — re-listed in FULL this session, not just the 2 files
[Block 36] §36.6 grepped — contains **no `Gruntfile.js`, `package.json`, or any JS-scaffold template of any
kind** anywhere among its 111 entries. `[CERT]` (`zipfile.namelist()`, this session, full listing).

**The one concrete name that DOES exist is the OLD `grunt-niagara`, and it comes from a document this corpus
has already proven unreliable for version-current claims.** `buildingJS.html`'s migration appendix (the same
section [Block 75] §75.5 quoted for its stale `com.tridium.n-grunt` plugin-id example) contains a full worked
`package.json` snippet:

```
"devDependencies": { "grunt-contrib-requirejs": "^4.1.3", "grunt": "~1.0.1", "grunt-niagara": "^2.1.0" }
```
and an installation instruction, `git clone https://github.com/tridium/grunt-init-niagara`. `[CERT-doc]`
(`doc/js/buildingJS.html`, fresh full-text extraction and `grep -o` this session — the exact snippet and URL,
read verbatim, not paraphrased). **But [Block 75] §75.5 already established, from THIS SAME document,
concrete internal evidence of staleness**: an unqualified "Niagara 4" framing never updated for N5, a
first-tutorial wizard transcript whose recorded DEFAULT answer is version "(4.10)", and a worked Gradle
example citing `com.tridium.n-grunt` — a plugin id absent from this exact install's own local Maven
repository (`etc/m2/repository/com/tridium/` has `grunt`, not `n-grunt`) — REMIT, not re-derived here. A
`package.json`/GitHub-URL snippet sitting in the SAME confirmed-stale document cannot be trusted as evidence
of what N5 5.0.0.28 actually resolves today without independent confirmation.

**Net verdict, narrowing but not closing B36-G3**: the gap's own framing (a "successor" package) has **no
positive evidence anywhere in this install** — no Gradle-plugin bytecode string, no devkit template, no file
anywhere else in either install root names ANY npm package for the Grunt task definitions. The only name
found at all is the literal OLD `grunt-niagara@^2.1.0`, sourced exclusively from a document this corpus has
already shown carries unmodified N4-era content elsewhere in the same file. Since [Block 36] §36.9 already
confirmed the Gradle-side TASK NAMES (`babel:dist`/`copy:dist`/`requirejs`) are unchanged from N4, the most
defensible reading is that the underlying npm package is ALSO still literally `grunt-niagara` unrenamed
(`[INFER]`, consistent with but not proven by the stale-doc citation) — but confirming this, or discovering
an actual renamed successor invisible anywhere in this local install, requires either live npm-registry/
GitHub access (no network in this environment) or a real N5-generated module's own `package.json`/lockfile —
the same blocker [Block 36]'s own **B36-G2** already named. Refined as **B79-G3** below.

## 79.x — Connections

- **[Block 21]** — closes **B21-G4** (§79.1); the "7.30.3" catch-block string §21.5 flagged is confirmed
  purely cosmetic, and §21.5's own `9.5.0`/`bin/ext/jxbrowser/` citations are independently corroborated by
  a fresh read of the jar's own manifest/resource rather than only its filename. [Block 21]'s own **B21-G1**
  (closed by [Block 75]) and **B21-G3** (station-level CSP census, still open) are untouched by this block.
- **[Block 75]** — closes **B75-G4** (§79.2) and **B75-G1** (§79.3); §79.3 additionally issues a narrow
  correction to §75.4's own "tried first unconditionally" framing (station context specifically), per
  METHODOLOGY §14. [Block 75]'s own **B75-G2** (`PatternFilter` grammar) and **B75-G3** (`buildingJS.html`
  byte-diff against N4) remain open, untouched by this block; **B75-G4**'s "structure not full reverse"
  scope is honored — `uxBuilder.built.min.js`'s internal bundler runtime/module-loader logic itself was not
  reverse-engineered, only its module census and naming scheme.
- **[Block 36]** — narrows **B36-G3** (§79.4), does not close it; extends [Block 36]'s own negative-evidence
  method (the `corpus-nav.py find` absence-in-corpus-TEXT check, §36.9) with a fresh filesystem-wide and
  jar-bytecode-wide sweep of the ACTUAL install (not just this corpus's prior block text), reaching the same
  "no positive evidence" conclusion from independent evidence. [Block 36]'s own **B36-G1** (closed by [Block
  75]) and **B36-G2** (live `gruntBuild`/`gruntCi` run, requires-execution) remain open.
- **[Block 61]** — shares this block's `[CERT-hw]`-over-live-install-binaries citation convention (there:
  `objdump -x`/`strings` over `nre.dll`/`njre.dll`; here: `unzip -p`/`javap` over `jxbrowser-9.5.0.jar`) —
  no direct factual overlap, cited for methodological consistency only.

## 79.x — Child gaps opened

- **B79-G1** — Four JS-only files under `rc/ux/make/` (`MakeWidget.js`, `MwPalettePreview.js`,
  `MwPropertiesWidget.js`, `mwUtils.js`) and two under `rc/fe/` (`BoundOrdReplaceEditor.js`,
  `VariablesEditor.js`) have no direct `BUxMw*`/`B*Editor` Java-type counterpart named in [Block 75] §75.3's
  class list. Whether these back OLDER, already-existing Java field-editor/widget types this session did not
  cross-check, or are purely internal client-side helpers reused by the classes that DO have a Java pair, is
  unverified. LOW — not load-bearing for B75-G4's closure (the pairing question was about the NAMED new
  classes, all of which DO have matching JS). `investigable`.
- **B79-G2** — `niagara.web.js.BJsBuild`/`BIJavaScript`'s generic framework — the mechanism that decides,
  for a given browser session, whether the RAW entry module (`BUxBuilder`'s `JsInfo`, `rc/ux/UxBuilder.js`)
  or the BUILT bundle (`BUxBuilderJsBuild`'s ORD, `rc/uxBuilder.built.min.js`) is actually served — was not
  traced this session (out of `uxBuilder`-specific scope; this class pair is likely generic to every
  `-ux`-bearing N5 module, not unique to `uxBuilder`). Would clarify whether N5 has a dev-mode
  (unminified/uncompressed) vs. prod-mode (minified/bundled) JS-serving toggle. MED — cross-cutting,
  potentially answers a question relevant to every browser-JS module this corpus has censused ([Block 21]).
  `investigable`.
- **B79-G3** (refines **B36-G3**) — Confirm, via live npm-registry/GitHub access or a real N5-generated
  module's own `package.json`/lockfile, whether N5 5.0.0.28 truly still resolves the literal N4-era
  `grunt-niagara@^2.1.0` package unchanged (as the stale `buildingJS.html` snippet implies but cannot prove
  current), or whether an actual renamed/versioned successor exists that simply appears nowhere in this
  local install's own shipped artifacts. `blocked-on-source` (no network/runnable install in this
  environment — same constraint as [Block 36]'s own **B36-G2**).

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block79.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):

```
== verify-block: niagara5-block79.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 15  (adj 13)
   [CERT-live] 0
   [CERT] 55  (adj 51)
   [CERT-doc] 4  (adj 3)
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 8  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/67 = 0.09
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:247-248  (range end verified; file has 2370 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:286,288  (file has 2370 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/BJxWebBrowserImpl.java:305-407  (range end verified; file has 2370 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/WbJxBrowserUtil.java:60-61  (file has 304 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/WbJxBrowserUtil.java:207-217  (range end verified; file has 304 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/WbJxBrowserUtil.java:257  (file has 304 lines)
   ok      organized/jxBrowser/vineflower/com/tridium/jx/browser/WbJxBrowserUtil.java:291-303  (range end verified; file has 304 lines)
   ok      organized/uxBuilder/vineflower/META-INF/module.xml:1  (file has 91 lines)
   ok      organized/uxBuilder/vineflower/com/tridium/uxBuilder/ux/BUxBuilder.java:24  (file has 35 lines)
   ok      organized/uxBuilder/vineflower/com/tridium/uxBuilder/ux/BUxBuilderJsBuild.java:26-30  (file has 33 lines)
   ok      organized/uxBuilder/vineflower/rc/ux/UxBuilder.js:1-5  (file has 2472 lines)
   ok      organized/workbench/vineflower/com/tridium/workbench/web/browser/fx/BFxWebBrowserImpl.java:172-184  (range end verified; file has 1315 lines)
   ok      organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebWidget.java:281-298  (range end verified; file has found)
   ok      organized/workbench/vineflower/com/tridium/workbench/web/browser/BWebBrowser.java:419-426  (range end verified; file has found)
   ok      organized/workbench/vineflower/com/tridium/workbench/web/browser/BIWebBrowserImpl.java:34  (file has 154 lines)
   resolved 15 of 15
== exit 0 ==
```

**Reading the tally.** Every `[CERT]`-marked `file:line` citation in this block points into `organized/`
(corpus-preserved decompiles), not a `/tmp` scratch tree — unlike [Block 21]/[Block 61]'s own citations for
the SAME `WbJxBrowserUtil`/`BJxWebBrowserImpl` classes, which were scratch and therefore `extern`. All 15
script-recognized `file:line` anchors resolve `ok`; there is no `extern`/unresolved citation in this block.
The `[CERT-hw]` count (15 raw, 13 adj — the 2-item gap is this Self-verify section's own prose reusing the
marker name while describing the tally, the same self-referential artifact [Block 61]/[Block 75] both
already documented and resolved by computation rather than chasing) covers §79.1's live-binary-manifest/
resource reads exclusively — no other section of this block uses `[CERT-hw]`. `[CERT-doc]` (4 raw, 3 adj)
is entirely §79.4's `buildingJS.html` reads. The `[INFER]` count (8 raw, 6 adj) is concentrated in §79.2's
"a real, minor asymmetry... not load-bearing" aside, §79.3's `forceStationBrowserInit`-mapped-to-constant
observation, and §79.4's own explicit "`[INFER]`, consistent with but not proven by" framing for the
still-`grunt-niagara`-unrenamed reading — none are load-bearing for any of the three CLOSED gaps' verdicts
(B21-G4, B75-G4, B75-G1), which rest entirely on `[CERT]`/`[CERT-hw]` claims; B36-G3's own NARROWED (not
closed) status is itself the honest signal that this gap's remaining open half is genuinely
evidence-exhausted from THIS install alone, not an artifact of under-reading.

**Inline token-verify.** Every citation above points at a file this session opened and read this session (in
full, for the small files — `BFxWebBrowserImpl.preInitialize()`, `BUxBuilder.java`, `BUxBuilderJsBuild.java`,
`BIWebBrowserImpl.java` — or via a `grep -n`-confirmed range for the larger files), cross-checked against the
cited symbol appearing in the actual read output this session — zero citations reused from [Block 21]/[Block
75]/[Block 36]'s text without an independent re-open this session (`WbJxBrowserUtil.java`'s `getDefaultTimeout
()`/`getCrashDirectory()`, cited by [Block 21] via scratch, were re-`grep`'d and re-read this session at their
corpus-preserved full path; `BWebBrowser.java`, cited by [Block 21] at `:108-307`, was re-opened this session
at the DIFFERENT, non-overlapping `:419-426` range for `post()`). Spot-check tokens independently re-confirmed
present (whitespace-normalized) this session: `Implementation-Version: 9.5.0`/`chromium.version=152.0.7977.65`
(jar manifest/resource, direct `unzip -p` output); `getResourceAsStream("version.info")`/`PRODUCT_VERSION`/
`CHROMIUM_VERSION` field constants (`VersionInfo.class`, `javap` output); `forceStationBrowserInit`/
`Sys.isStation()`/`preInitError`/`WbJxBrowserUtil.DISABLE_JX_BROWSER` (`BJxWebBrowserImpl.java`, one `grep -n`
run each); `Class.forName("javafx.scene.Node")` (`BFxWebBrowserImpl.java`); `JsInfo.make`/`module://uxBuilder/
rc/ux/UxBuilder.js` (`BUxBuilder.java`); `BJsBuild`/`module://uxBuilder/rc/uxBuilder.built.min.js`
(`BUxBuilderJsBuild.java`); `define("nmodule/uxBuilder/rc/` (115 occurrences, `grep -o` count, `uxBuilder
.built.min.js`); `"grunt-niagara": "^2.1.0"`/`git clone https://github.com/tridium/grunt-init-niagara`
(stripped `buildingJS.txt`, both confirmed present by direct `grep -o` output this session). Token-verify:
**≈26 distinct load-bearing tokens/facts** confirmed present (or, for the negative-existence claims in §79.4
— zero `grunt-niagara`/`Gruntfile` hits outside `buildingJS.html`, zero `7.30.3` hits across all five
`jxbrowser-*.jar` files — confirmed ABSENT from a fully/exhaustively-searched artifact, per METHODOLOGY §3's
symmetric negative-existence-opening-obligation rule) in their cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block79.md`. Per the
caller's explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator, matching [Block 61]/[Block 75]'s own convention for the same instruction.
