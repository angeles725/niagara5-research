# Block 102 — Workbench/web UI stack: closing the B21/B36/B79 JS-build-toolchain gaps, correcting Block 75's "unmodified" `buildingJS.html` verdict, the exact `buildN5.html` VideoDriver tree fix, and two mechanical B93 closures

> **Covers**: (1) ALREADY-COVERED verification for B21-G1, B21-G2, B36-G1 (all closed by [Block 75]); (2)
> B79-G3/B36-G3 — live npm-registry/GitHub confirmation of `grunt-niagara`'s real current package identity;
> (3) B79-G1 — call-graph census of uxBuilder's 6 Java-pairless JS files, plus a newly-traced N4 `pxEditor`
> naming lineage for `MakeWidget`; (4) B79-G2 — the full `WebDev`/`BJsBuild`/`JsInfo` raw-vs-built JS serving
> mechanism, traced to `BUxBuilderJsBuild`'s own concrete toggle name; (5) B75-G3 — a real line-by-line diff
> of N4's vs N5's `buildingJS.txt`/`requirejs.txt`; (6) B97-G4 — the exact corrected VideoDriver example-tree
> fix for `buildN5.html`; (7) B93-G1 — direct N5 `baja.jar` bytecode check for `BCertificateStatusHealth`;
> (8) B93-G2 — a one-line clarification of which `niagara-help/source/` directory [Block 4] §4.7 meant.
> **Does not cover**: re-deriving anything [Block 75]/[Block 79]/[Block 89]/[Block 97]/[Block 93] already
> settled with a `[CERT]`-class citation (reused by pointer, not re-verified from scratch) — see each
> section's own "reused from" note.
> **Subject version**: N5 5.0.0.28 (this corpus's baseline); N4 4.14 decompiled baseline (sibling corpus
> `/home/cristian/niagara-research`) used only for cross-version diffs, explicitly marked.
> **Method**: (a) `grep -rl <GAP-ID>` ALREADY-COVERED checks against the full `niagara5-block*.md` set; (b)
> direct `zipfile`/`unzip -l` structural census over shipped jars (`baja.jar`, `n-templates-*.jar`); (c) fresh
> Vineflower decompilation of two classes ([Block 89]/[Block 97] had read but not preserved as `.java`
> anywhere in `organized/`) — `VideoDriverModuleGenerator.class`, `NDriverModuleGenerator.class`,
> `NiagaraTypeInfo.class`, all from `n-templates-5.0.54.9.2.jar`; (d) full-corpus call-graph `grep` (who
> `require()`s a given RequireJS module ID) over `organized/uxBuilder`; (e) cross-corpus `diff -u` of the
> `devguide-clean`/`guides-clean` plain-text doc extractions, blank-line-normalized; (f) `WebSearch`/`WebFetch`
> against `github.com/tridium/grunt-niagara` and `registry.npmjs.org` (network tools available and working
> this session — confirmed live, not assumed).

## 102.1 — B21-G1 ALREADY-COVERED: closed by [Block 75] §75.3

Parent text ([Block 21] §21.4, quoted in its own child-gap list): *"Is `uxBuilder.jar`'s `ux/make/`+
`ux/fe/` sub-package (`BUxMwActionBatch`, ...) genuinely new in N5, or simply un-enumerated N4 material
B895/B922 didn't flag?"* [Block 75] §75.3 ran a direct `zipfile.namelist()` census of BOTH N4 `uxBuilder`
jars and found `uxBuilder-ux.jar` holds **zero** `.class` files of any kind and `uxBuilder-wb.jar` holds
exactly 8, none under `ux/make`/`ux/fe` — settling **CLOSED**: the N5 classes are genuinely new, not
missed N4 material. No re-derivation performed this session; verified only that no later block reopened it.

## 102.2 — B21-G2 ALREADY-COVERED: closed by [Block 75] §75.4

Parent text ([Block 21] §21.5): *"Which embedded-browser implementation (`BJxWebBrowserImpl`/JxBrowser-
Chromium vs `BFxWebBrowserImpl`/JavaFX WebView) is the DEFAULT for `BWebBrowser`/`BWebWidget`, and under
what condition does N5 fall back to the other?"* [Block 75] §75.4 answered: **JxBrowser/Chromium is the
default**, tried first; JavaFX WebView is the fallback, unconditionally excluded inside a station;
`NullWebBrowserImpl` is the final no-op. [Block 79] §79.3 later added one narrow correction to §75.4's
"tried first unconditionally" framing (station-context specifically) but did not reopen the CLOSED verdict.
No re-derivation performed.

## 102.3 — B36-G1 ALREADY-COVERED (closure sharpened, not reversed, by §102.7 below): closed by [Block 75] §75.5

Parent text ([Block 36] §36.12): *"`doc/js/buildingJS.html`/`doc/requirejs.html` were confirmed present and
on-topic by grep but not read line-by-line this session; a full read would either confirm or refute the
`[INFER]` 'near-identical to the N4 guide' claim."* [Block 75] §75.5 read both files and declared them
"CONFIRMED-STALE, unmodified-for-N5 N4-era content." **This session's own §102.7 (below) performs the actual
line-by-line diff B75-G3 asked for and finds the "unmodified" half of that verdict is overstated** — the
doc was genuinely, substantially edited for N5 (see §102.7 and the Corrections section). B36-G1's own literal
ask (confirm/refute "near-identical") is answered precisely by that diff: **neither** "near-identical" nor
"unmodified" is accurate — the correct characterization is "substantively edited, with a handful of
unedited residuals." B36-G1 itself stays CLOSED (the full read WAS performed, by [Block 75] and confirmed
again this session); the correction targets [Block 75] §75.5's own summary framing, not B36-G1's closure.

## 102.4 — B79-G3 (refines B36-G3) CLOSED: `grunt-niagara` is still the literal, unrenamed package name — confirmed live on the public npm registry and GitHub, version 2.3.0 (2025-10-17), with zero name-rename or N5-split history anywhere in its changelog `[CERT-web]`

Parent text ([Block 79] §79.5, refining [Block 36] §36.12's own **B36-G3**): *"Confirm, via live
npm-registry/GitHub access or a real N5-generated module's own `package.json`/lockfile, whether N5 5.0.0.28
truly still resolves the literal N4-era `grunt-niagara@^2.1.0` package unchanged... or whether an actual
renamed/versioned successor exists that simply appears nowhere in this local install's own shipped
artifacts."* [Block 36]/[Block 79] both marked this `blocked-on-source` for lack of network access.

**This session has live `WebSearch`/`WebFetch` access, confirmed working.** Direct queries settle it:

- `github.com/tridium/grunt-niagara` exists, is actively maintained by Tridium (author `Logan Byam
  <lbyam@tridium.com>`), and its own `package.json` (raw, fetched this session) names the package literally
  `grunt-niagara`, version **2.3.0**, license "Tridium Open Source License," main entry `Gruntfile.js`.
  `[CERT-web]` (`https://raw.githubusercontent.com/tridium/grunt-niagara/master/package.json`, fetched
  2026-09-27).
- The project's own `CHANGELOG.md` (fetched in full this session) runs from v0.1.19 (2014) to **v2.3.0
  (2025-10-17)** — a release newer than this corpus's own N5 5.0.0.28 subject build — with **zero** entries
  mentioning a rename, a fork, or an N5-specific split. The most recent entries are mechanical (2.3.0 adds
  `--niagara-config-home`; 2.2.2 adds a default Chrome-flag; 2.1.0 drops PhantomJS). `[CERT-web]`
  (`https://raw.githubusercontent.com/tridium/grunt-niagara/master/CHANGELOG.md`, fetched 2026-09-27).
- `registry.npmjs.org/grunt-niagara` (the actual PUBLIC npm registry, fetched directly this session) confirms
  the package is public (not a private Tridium-only registry, contrary to [Block 36]'s own unverified
  assumption), with `dist-tags.latest = 2.3.0`, matching GitHub exactly. `[CERT-web]`
  (`https://registry.npmjs.org/grunt-niagara`, fetched 2026-09-27).

**Net verdict, closing B79-G3/B36-G3**: N5 5.0.0.28 (whose own `buildingJS.html`, per §102.7 below, still
cites the old `grunt-niagara@^2.1.0` pin) resolves against a package that is **still literally named
`grunt-niagara`**, publicly published, with 8+ releases and zero renames between the doc's cited `2.1.0` and
the current `2.3.0`. [Block 36]'s own `[INFER]` "presumably still `grunt-niagara` unrenamed" is now
`[CERT-web]`-confirmed correct, and the "no successor exists" half of [Block 79]'s narrowing is also
confirmed: there is no renamed/versioned successor — the SAME package simply kept shipping new minor
versions past the doc's stale version pin.

## 102.5 — B79-G1 NARROWED, largely CLOSED: uxBuilder's 6 Java-pairless JS files are, by direct call-graph census, internal helpers consumed exclusively by the JS modules that DO pair with a named `BUxMw*` class — plus a newly-traced N4 `pxEditor` naming lineage for `MakeWidget` itself `[CERT]`

Parent text ([Block 79] §79.6): *"Four JS-only files under `rc/ux/make/` (`MakeWidget.js`,
`MwPalettePreview.js`, `MwPropertiesWidget.js`, `mwUtils.js`) and two under `rc/fe/`
(`BoundOrdReplaceEditor.js`, `VariablesEditor.js`) have no direct `BUxMw*`/`B*Editor` Java-type counterpart
named in [Block 75] §75.3's class list. Whether these back OLDER, already-existing Java field-
editor/widget types this session did not cross-check, or are purely internal client-side helpers reused
by the classes that DO have a Java pair, is unverified."*

**Full-corpus Java grep, zero hits.** `grep -rl -E "MakeWidget|MwPropertiesWidget|MwPalettePreview|mwUtils|
BoundOrdReplaceEditor|VariablesEditor" --include='*.java'` over the ENTIRE `organized/` tree returns nothing
— no Java class anywhere (in uxBuilder or any other module) references any of these six JS names. `[CERT]`
(full-corpus grep, this session, zero matches).

**Direct call-graph census confirms the "internal helper" branch for 5 of 6 files.** Grepping for each
file's own RequireJS module path (`rc/ux/make/<Name>'`/`rc/fe/<Name>'`) as a `require()`d dependency string
inside every OTHER uxBuilder JS file:

| File | Required (called) by |
|---|---|
| `mwUtils.js` | `MwWorkbenchView.js`, `MwPropertyBatch.js`, `MwPxInclude.js`, `MwChartWidget.js`, `MwBoundLabel.js`, `MakeWidget.js`, `MwPropertiesWidget.js`, `uxBuilderUtils.js`, `MwFromPalette.js` |
| `MwPropertiesWidget.js` | `MwChartWidget.js`, `MwWorkbenchView.js`, `MwPxInclude.js`, `MwFromPalette.js`, `MwBoundLabel.js` |
| `MwPalettePreview.js` | `MwPropertyBatch.js`, `MwFromPalette.js` |
| `BoundOrdReplaceEditor.js` | `BoundOrdsEditor.js` (sidebars) |
| `VariablesEditor.js` | `uxBuilderUtils.js` |

Every `mwUtils.js`/`MwPropertiesWidget.js`/`MwPalettePreview.js` caller listed
(`MwWorkbenchView`/`MwPropertyBatch`/`MwPxInclude`/`MwChartWidget`/`MwBoundLabel`/`MwFromPalette`) is the JS
half of the SAME 6 already-paired classes [Block 75] §75.3 named (`BUxMwWorkbenchView`/`BUxMwPropertyBatch`/
`BUxMwPxInclude`/`BUxMwChartWidget`/`BUxMwBoundLabel`/`BUxMwFromPalette`). `BoundOrdReplaceEditor.js`'s and
`VariablesEditor.js`'s own callers (`BoundOrdsEditor.js`, `uxBuilderUtils.js`) are themselves confirmed
Java-pairless: `BoundOrdsEditor.js` has its own `keyName: 'BoundOrdsEditor'` with **no** matching Java class
anywhere in the corpus (a second `grep -rl "BoundOrdsEditor" --include='*.java'` sweep, zero hits,
`[CERT]`), and `uxBuilderUtils.js` is a broad, ~35-file-deep shared utility library used across the WHOLE
`ux/` tree (widget tree, property sheet, wysiwyg trackers, context-menu commands — a `grep -rl "rc/util/
uxBuilderUtils'"` sweep this session returns 35 distinct callers), not a feeder of any one paired class in
particular. **Checked directly and ruled out**: `BActionArgEditor` itself resolves (via its own
`getJsInfo()`) to `module://uxBuilder/rc/fe/ActionArgEditor.js` — a DIFFERENT file that does NOT
`require()` either `BoundOrdReplaceEditor.js` or `VariablesEditor.js` (`[CERT]`,
`BActionArgEditor.java:24`, `ActionArgEditor.js`'s own `define([...])` head, both read this session) — so
neither orphan `fe/` file feeds any of the three named, Java-paired `fe/` editor classes; they are
independent uxBuilder-internal UI plumbing, exactly the same "purely internal client-side helper" category
as the `ux/make/` trio, just consumed by OTHER Java-pairless sidebar/utility JS rather than by a
Java-paired one. `[CERT]` (`grep -rl` per-module-path census, this session, `organized/uxBuilder/vineflower`,
table above each independently reproducible).

**`MakeWidget.js` is the one exception — it is a standalone dialog controller, not a shared widget helper,
called only by `NavNodesToUxModelFactory.js`'s `MakeWidget.showFor(navNodes, params)`** — a Workbench-tree
"convert these selected nodes into a widget" wizard entry point, invoked programmatically, never registered
as an agent-bound `BWidget`. `[CERT]` (`NavNodesToUxModelFactory.js:15,52`, this session).

**New finding, not asked for by the gap but directly relevant: `MakeWidget`'s naming is not
uxBuilder-original — it mirrors an OLDER, N4-baseline Workbench-Swing feature with the identical name,
`com.tridium.px.editor.make.BMakeWidget`, in the separate `pxEditor` module.** A full-corpus grep for
"MakeWidget" across the SIBLING N4 corpus (`/home/cristian/niagara-research/organized`) turns up
`com/tridium/px/editor/make/BMakeWidget.java` plus a whole parallel class family — `BMwActionBatch`,
`BMwBatch`, `BMwBoundLabel`, `BMwChart`, `BMwConfig`, `BMwFromPalette`, `BMwPropertyBatch`, `BMwPxInclude`,
`BMwTimePlot`, `BMwWorkbenchView`, `MakeWidgetContext`, `PropertyNode(Factory)`, `BCellPane`,
`WidgetCopier` — already present in N4 4.14's decompiled `pxEditor-wb` jar (a Workbench-only Swing module,
predating uxBuilder entirely). `[CERT]` (`/home/cristian/niagara-research/organized/pxEditor/pxEditor-wb/
decompiled/com/tridium/px/editor/make/BMakeWidget.java`, sha256
`98dd4146d298bda81009441720f0fa690039e7c9b098c7a99e265126f7b05780`, this session). **This is a
naming-lineage connection, not a code-reuse one**: `pxEditor` was never decompiled/organized anywhere in
THIS (N5) corpus, and this session's own mounted N5 install path (`/mnt/c/Program Files/Niagara/5.0.0.28`)
ships **no Niagara module jars at all** (only third-party libs — confirmed by a full `find -iname '*.jar'`,
128 hits, zero named `pxEditor`/`uxBuilder`/any Niagara module), so whether `pxEditor`'s own Swing
"Make Widget" wizard still ships in N5 5.0.0.28 is unknown from this environment — flagged as new child gap
**B102-G1** below, not asserted either way.

> **Correction (orchestrator addendum, same session, §14).** The premise above is wrong. N5 module jars live in
> the config home, not under `Program Files`: `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`
> holds 247 jars including `pxEditor.jar`, and this corpus already has it decompiled at
> `organized/pxEditor/vineflower/com/tridium/px/editor/make/`. That package holds 16 files, the same 16 file
> names as N4 4.14's `pxEditor-wb` (`diff` of the two listings is empty), including
> `BMakeWidget.java:54` (`public class BMakeWidget extends BEdgePane`) and the whole `BMw*` family `[CERT]`.
> So N5 5.0.0.28 ships BOTH the Workbench-Swing `BMakeWidget` wizard (pxEditor) and the web `MakeWidget.js`
> dialog (uxBuilder). **B102-G1 is CLOSED by this addendum**; `MakeWidget.js` is a web-side sibling of a
> still-shipped Swing wizard, not a replacement of a removed one.

**Net verdict, NARROWING B79-G1 (not further closable without B102-G1)**: 5 of 6 files
(`MwPropertiesWidget`/`MwPalettePreview`/`mwUtils`/`BoundOrdReplaceEditor`/`VariablesEditor`) are
`[CERT]`-confirmed pure internal helpers, exactly the branch [Block 79]'s own gap text anticipated as most
likely ("not load-bearing for B75-G4's closure"). `MakeWidget.js` alone is architecturally distinct (a
standalone wizard dialog, role-equivalent — not code-equivalent — to N4 `pxEditor`'s older `BMakeWidget`
Swing wizard), and whether N5 still ships that OLDER `pxEditor` Java counterpart at all remains open
(**B102-G1**, `blocked-on-source`: no full N5 module set reachable from this environment).

## 102.6 — B79-G2 CLOSED: N5's dev-mode/prod-mode JS toggle is `niagara.web.WebDev` + `webdev.properties`, gating `BJsBuild.isWebDevEnabled()`, which `JsInfo`/`BIWebResource.DependencyGraph`/`RequireJsUtil` all check to decide RAW-per-file vs. BUILT-bundle serving — traced end-to-end to uxBuilder's own concrete toggle name, `"uxBuilder"` `[CERT]`

Parent text ([Block 79] §79.6): *"`niagara.web.js.BJsBuild`/`BIJavaScript`'s generic framework — the
mechanism that decides, for a given browser session, whether the RAW entry module (`BUxBuilder`'s `JsInfo`,
`rc/ux/UxBuilder.js`) or the BUILT bundle (`BUxBuilderJsBuild`'s ORD, `rc/uxBuilder.built.min.js`) is
actually served — was not traced this session... Would clarify whether N5 has a dev-mode (unminified/
uncompressed) vs. prod-mode (minified/bundled) JS-serving toggle."*

**The mechanism, traced end-to-end this session, is real and exactly matches the gap's own guess:**

1. **`niagara.web.WebDev`** (a per-named-build boolean flag, backed by `$niagara.user.home/etc/
   webdev.properties`, toggled live via the Workbench Spy tree at `spy:/webDevSetup/enable-<name>` /
   `disable-<name>`) provides `WebDev.get(name).isEnabled()`. `[CERT]` (`WebDev.java`, sha256
   `265b0b3562ef6df61cdcd8ebe17bdbdb6dda3463e5aad0a24e58c1ba942fec85`, full file read this session).
2. **`BJsBuild.isWebDevEnabled()`** (`BJsBuild.java:143`) returns `WebDev.get(this.getId()).isEnabled()` —
   every `BJsBuild` singleton (one per `-ux`-bearing module, e.g. `BUxBuilderJsBuild`) is itself a named
   WebDev toggle. `[CERT]` (`BJsBuild.java:143`, sha256
   `c0aed4c8df3b60afc8a211094dc5637371a365a4bd090bde00ac12b13d9b6abf`, this session).
3. **`JsInfo.addBuilds()`** (`JsInfo.java:94-95`): `if (!build.isWebDevEnabled()) { list.add(build); }` —
   a build is only added to the resolved dependency list (and therefore only gets its BUILT bundle ORD
   served) when its own WebDev flag is OFF. When ON, the build is dropped from the list entirely, and
   RequireJS instead resolves the module by its raw per-file AMD `define()` graph. `[CERT]` (`JsInfo.java:
   94-95`, sha256 `52d2098aeb196584d406af4de56fe2c37f1da64ac9bcd8e986914f47e4731343`, this session).
4. **`BIWebResource.DependencyGraph.STANDARD_WEBDEV_FILTER`** (`BIWebResource.java:47-48`) applies the
   identical `!isWebDevEnabled()` predicate when serializing the graph to the page's `require([...], ...)`
   JSON — the SAME toggle governs both the internal `getBuilds()` recursion and the actual served-to-browser
   JSON manifest. `[CERT]` (`BIWebResource.java:47-48`, sha256
   `a422a8494ece17614a7d4746b35677f041481a691a1ff09ae4db6f50f02bc5a6`, this session).
5. **`RequireJsUtil` (`com.tridium.web.RequireJsUtil.java:169-172`)** is the actual page-render-time
   consumer: for every registered `BIRequireJsConfig`, it looks up that config's own `JsInfo.getBuildId()`,
   resolves the matching `BJsBuild`, and reads `.isWebDevEnabled()` to compute a `webdev` boolean that
   is then passed into `config.write(...)` — i.e. this is the literal fork point deciding what gets written
   into the page's RequireJS bootstrap script. `[CERT]` (`RequireJsUtil.java:169-172`, sha256
   `f84b26c70d9b9765d726faeb59837a86bb3cd6bdb5b4d09482e309c9adb433d1`, this session).

**Traced to uxBuilder's own concrete toggle name, closing the loop the gap's own text asked about
explicitly:** `BUxBuilderJsBuild` (`com.tridium.uxBuilder.ux.BUxBuilderJsBuild`, `extends BJsBuild` directly,
no override) passes `"uxBuilder"` as its own `id` to the `BJsBuild` superclass constructor, alongside the
`module://uxBuilder/rc/uxBuilder.built.min.js` ORD ([Block 75] §75.3's own already-censused minified bundle)
and 3 dependent-build types (`BBajauiJsBuild`, `BBajauxJsBuild`, `BUxBuilderCssResource`). `[CERT]`
(`BUxBuilderJsBuild.java`, sha256 `52515d749729688ed5b3d2ef23ac3e8c6c27b3e9613975a1697594b5db0563bb`,
content quoted verbatim above). Meaning: toggling `spy:/webDevSetup/enable-uxBuilder` in a running station's
Spy tree is, `[CERT]`, the literal live switch between uxBuilder's minified bundle and its raw per-module
JS tree.

**Net verdict, closing B79-G2**: N5 DOES have exactly the dev-mode/prod-mode toggle the gap predicted, it is
NOT `uxBuilder`-specific (confirmed generic — the SAME `WebDev`/`BJsBuild`/`JsInfo` machinery is reused,
`[CERT]`, by `bacnetAws`/`maxpro`/`kitControl`/`tagdictionary`/`naxisVideo`/`bacnet`/`totpAuth`/
`modbusTcpSlave`/`modbusCore`/`platform`'s own `B*JsBuild` subclasses — a 10-module-deep grep hit list,
this session), and its concrete uxBuilder-side toggle name is `"uxBuilder"`.

## 102.7 — B75-G3 CLOSED: line-by-line diff of N4's vs N5's `buildingJS.txt`/`requirejs.txt` shows SUBSTANTIAL, deliberate N5-specific editing — not a byte-identical or near-identical carryover `[CERT-doc]`

Parent text ([Block 75] §75.6, its own child-gap list): *"§75.5 confirms `buildingJS.html` is N4-era
content by INTERNAL evidence (stale version number, stale plugin id, absent N5-specific terms) but does not
perform a line-by-line diff against N4 corpus's own preserved `B1132`/`B1119` excerpts of
`buildingJS.txt`/`requirejs.txt` — such a diff could confirm whether this is the EXACT same revision
byte-for-byte or a lightly-touched one."*

[Block 1132]/[Block 1119] (the sibling N4 corpus's own blocks) only ever quoted short excerpts of N4's
devguide text, not full files — but the FULL source files they excerpted from are independently preserved,
untouched, in both corpora at parallel paths:
`/home/cristian/niagara-research/niagara-help/devguide-clean/js/buildingJS.txt` (N4, 644 raw / 379
non-blank lines) and `/home/cristian/niagara5-research/niagara-help/guides-clean/js/buildingJS.txt` (N5,
657 raw / 386 non-blank lines); same pair for `requirejs.txt` (N4 47 / N5 46 lines, same directory name in
both corpora). `diff -u` after blank-line normalization on both pairs, this session:

**`buildingJS.txt`: at least 15 distinct content edits, not zero.** Concrete examples (all `[CERT-doc]`,
direct `diff -u` output, this session):
- "In Niagara 4, the user interface **is moving**..." (N4) → "...**moved**..." (N5) — a deliberate
  present→past tense edit, the ONE "Niagara 4" mention [Block 75] cited as "never updated" was, in fact,
  edited (just not de-branded).
- "for Niagara **4**" (N4, toolchain-scope sentence) → "for Niagara" (N5) — genericized.
- An entirely NEW paragraph added: a "Gradle" subsection (`gradle.properties`/`nodeHome`) absent from N4.
- `niagara_home` example path: N4 `c:\Niagara\Niagara-{versionNumber}` → N5 `C:\Program Files\Niagara\
  {version}` — updated to N5's real install-path convention.
- A wholly NEW environment variable documented: **`niagara_config_home`** (`C:\ProgramData\Niagara\
  {brandId}\config\{version}`) — does not exist in the N4 doc at all.
- `niagara_user_home` example: N4 `%USERPROFILE%\Niagara4.x\{companyName}` → N5 `%USERPROFILE%\Niagara\
  {brandId}\{version}`.
- "Niagara **4** stations" → "Niagara stations"; "Niagara **4** includes a moduledev mode" → "Niagara
  includes a moduledev mode."
- Every code/CLI example dropped the N4 `-ux` submodule convention: `myWebModule-ux` → `myWebModule`,
  `gradlew :myWebModule-ux:jar` → `gradlew :myWebModule:jar`, `"yourModuleName-ux"` → `"yourModuleName"`,
  `myModule-ux.gradle` → `myModule.gradle`, `projectResource('js-ux', ...)` → `projectResource('js', ...)`
  — consistent, throughout, with this corpus's own established N5 module-restructuring finding (no more
  `-ux` submodule split).
- `moduledev.properties` location: N4 `niagara_home/etc/` → N5 `niagara_config_home/etc/` (tracks the new
  env var above).
- BIJavaScript's hosting package citation changed: N4 `javax.baja.web.js.BIJavaScript` → N5 doc text
  `niagara.js.web.BIJavaScript` (this exact string is itself a doc-side inaccuracy — the REAL N5 package,
  independently confirmed in §102.6 above by decompiling the class directly, is `niagara.web.js.BIJavaScript`,
  package segments transposed; a small residual error, but proof the sentence was actively rewritten, not
  copy-pasted).
- The Gradle-plugin-id citation itself changed: N4 doc showed `apply plugin: "com.tridium.niagara-grunt"`;
  N5 doc shows `apply plugin: "com.tridium.n-grunt"` — [Block 75] §75.5 treated the N5 wording
  (`com.tridium.n-grunt`) as evidence the doc is "N4-era, unmodified" because that id is absent from this
  install's own local Maven repo; the diff proves the OPPOSITE causal direction — this is a genuine EDIT
  made specifically for N5's doc revision, one that happens to reference a plugin id this particular
  minimal install's `etc/m2/repository` doesn't carry (a packaging-completeness question, not a
  staleness one).

**`requirejs.txt`: smaller file, same pattern.** Title line "RequireJS: how to load JavaScript code in
Niagara **4**" (N4) → "...in Niagara" (N5, de-branded); every `myModule-ux/src/rc/...` path example →
`myModule/src/rc/...` (same `-ux`-removal pattern); and, most tellingly, **the entire "`Hx` : Call
`HxOp#requireJs()` from your Hx View." bullet is DELETED outright in N5** — consistent with Hx's own
deprecation/removal, a genuinely meaningful content edit, not a copy-paste artifact.

**What DID survive unedited** (validating [Block 75]'s specific citations, even though its overall framing
was too strong): the wizard-transcript default "`[?] What Niagara version will you build your module
against? (4.10)`" is byte-identical in both files (`buildingJS.txt:119` N4 / `:126` N5) — this ONE residual
is real and unedited. 3 of the doc's original 7 "Niagara 4" mentions also survive (down from 7 in N4 to 4
in N5): one substantive-but-historical (BajaScript 4.2 offline-editing feature note, correctly still `4.2`
since it's a historical fact), one intentional ("the new annotation-based method available **since**
Niagara 4" — also correctly historical, note the ADDED word "since"), and one genuine leftover
("...the new Niagara 4 HTML5 web views..." in the tutorial's closing summary, never de-branded like its
sibling sentence at the top of the doc was).

**Net verdict, closing B75-G3**: the requested diff is done. Result: **this is neither a byte-identical
carryover NOR a "near-identical" one** — it is a **substantively, deliberately edited N5 revision with a
small number of specific unedited/mis-edited residuals** (the version-default wizard answer, one leftover
brand mention, and a doc-side package-name transposition). This directly issues a correction to [Block 75]
§75.5's own "unmodified-for-N5" framing — see Corrections section below.

## 102.8 — B97-G4 CLOSED: the exact corrected `buildN5.html` "Example File Tree for a VideoDriver" section, verified against a fresh full decompile of `VideoDriverModuleGenerator.class` `[CERT]`

Parent text ([Block 97] §97.11, its own child-gap list): *"file a documentation-accuracy note against
`buildN5.html`'s own 'Example File Tree for a VideoDriver' section: it names 5 files
(`myDriverTcpCommConfig.java`, `myDriverHttpListener.java`, `myDriverTcpListener.java`,
`myDriverCameraConnectReq.java`, `myDriverZoomReq.java`) that `VideoDriverModuleGenerator.generate()` never
queues under any conditional, while omitting 4 files it DOES queue
(`NfooPanTiltReq`/`NfooFocusControlReq`/`NfooHttpUtil`/`NfooVideoStreamUtil`) — worth confirming whether
this is a stale doc... or a hand-written illustrative tree that was never generated from the real templates
at all."*

**This session decompiled `VideoDriverModuleGenerator.class` fresh** (Vineflower, `n-templates-
5.0.54.9.2.jar`, sha256 `285e6463e99ae0c4e1ed303792150773c344c8593cc1af29aac1dfb132bb2405`; the class had
been READ but never preserved as `.java` anywhere in `organized/` by [Block 89]/[Block 97]) — plus
`NDriverModuleGenerator.class` and `NiagaraTypeInfo.class` from the same jar, to nail down the exact output
filename convention. Whole `generate()` method read (`VideoDriverModuleGenerator.java:56-173`, `[CERT]`).

**Correction to the call-count, first**: the method contains **32** total `addTemplateWrite()` calls (18
unconditional + 14 gated by `dvrSupport`/`dvrDiscovery`/`dvrDisplay`(×4)/`getCommInfo().isHttp()`(×2)/
`camera.isPanTiltSupport()`/`camera.isFocusSupport()`), not "24" — see Corrections section.
[Block 97] §97.3's own DESCRIPTIVE manifest (its prose enumeration of every package/file), independently
re-verified this session, is fully accurate; only the headline NUMBER (inherited from [Block 89] §89.7) was
wrong.

**Filename-mapping rule, confirmed `[CERT]` this session** (`NiagaraTypeInfo.getCls()` returns literally
`"B" + this.type`, e.g. `network.getCls()` → `"BMyDriverNetwork"`; a bare `this.basePrefix` concatenation,
e.g. for `NfooHttpUtil.java.vm`, produces `"MyDriverHttpUtil"` with no leading letter at all) — this matches
the doc's own established "drop the leading `B`, lowercase the first letter" illustrative-name convention
(already validated for NDriver by [Block 97] §97.2), applied here to VideoDriver for the first time.

**Full package-by-package reconciliation, doc vs. real generator output** (✓ = doc name matches the real
write-target string exactly; ✗ = doc name is fictional or wrong; **+** = real file the doc omits entirely):

| Package | Doc says | Real generator produces | Verdict |
|---|---|---|---|
| (top-level) | `myDriverNetwork.java` | `BMyDriverNetwork.java` (unconditional) | ✓ correct |
| (top-level) | `myDriverDeviceFolder.java` | **— no such file; VideoDriver has no DeviceFolder concept at all** | ✗ fictional |
| `dvr/` (cond. `dvrSupport`) | Dvr/DvrFolder/DvrId/MultistreamPreferences | same 4, same names | ✓ all 4 correct |
| `camera/` | Camera/CameraDeviceExt/CameraDeviceId/CameraDiscoveryLeaf/CameraDiscoveryPreferences/CameraFolder | same 6, same names (Discovery pair cond. `dvrDiscovery`) | ✓ all 6 correct |
| `comm/` | TcpCommConfig/HttpListener/TcpListener | **— no `comm/` package exists for VideoDriver at all** | ✗ entire section fictional |
| `datatypes/` | IpAddress/TimeSyncParams | same 2, same names | ✓ both correct |
| `display/` (cond. `dvrDisplay`) | `myDriverVideoDisplay.java`, `myDriverVideoDisplayMultistream.java`, `myDriverDisplayController.java` | `BMyDriverDisplay.java`, `BMyDriverDisplayMultistream.java`, `MyDriverDisplayController.java` | ✗ spurious "Video" infix on 2 of 3 (template file is named `BNfooVideoDisplay.java.vm` but its OWN write-target string drops "Video"); 3rd is correct |
| `event/` | all 7 (CameraExt/DiscoveryLeaf/DiscoveryList/DiscoveryPreferences/Folder/ProxyExt/VideoEventRecall) | same 7, same names (here "Video" IS baked into the real write-target for `VideoEventRecall`) | ✓ all 7 correct |
| `enums/` | EventTypesEnum, DisplayLayoutTypesEnum (cond. `dvrDisplay`) | same 2, same names | ✓ both correct |
| `util/` (cond. `isHttp()`) | `myDriverHttpUtil.java`, `myDriverVideoStreamUtil.java` | same 2, same names | ✓ both correct |
| `messages/` | CameraConnectReq, **PanTiltReq**, ZoomReq, MessageFactory, TcpLinkMessage | ONLY `PanTiltReq.java` (cond. `camera.isPanTiltSupport()`) and `FocusControlReq.java` (cond. `camera.isFocusSupport()`) | ✗ 4 of 5 doc entries fictional; PanTiltReq is the one true positive; **+ FocusControlReq missing entirely** |
| `ui/` | VideoAgent, `myDriverMjpegVideoDecoder.java`, `myDriverFfmpegDecoder.java` | `BMyDriverVideoAgent.java` + ONE generic `MyDriverVideoDecoder.java` (unconditional) | ✗ both "decoder" names fictional (no Mjpeg/Ffmpeg split exists); VideoAgent correct; **+ generic VideoDecoder.java missing entirely** |

**The exact corrected tree** (same drawing style as the doc's own, `myDriver` prefix convention preserved;
`†` marks a conditionally-generated file, matching the doc's existing convention of showing conditional
NDriver `learn/` files unconditionally as one illustrative configuration):

```
    │       ├── camera/             # Camera device classes
    │       │   ├── myDriverCamera.java
    │       │   ├── myDriverCameraDeviceExt.java
    │       │   ├── myDriverCameraDeviceId.java
    │       │   ├── myDriverCameraDiscoveryLeaf.java          †dvrDiscovery
    │       │   ├── myDriverCameraDiscoveryPreferences.java   †dvrDiscovery
    │       │   └── myDriverCameraFolder.java
    │       │
    │       ├── datatypes/          # Protocol-specific data types
    │       │   ├── myDriverIpAddress.java
    │       │   └── myDriverTimeSyncParams.java
    │       │
    │       ├── display/            # Video display components           †dvrDisplay (whole package)
    │       │   ├── myDriverDisplay.java
    │       │   ├── myDriverDisplayMultistream.java
    │       │   └── myDriverDisplayController.java
    │       │
    │       ├── dvr/                # DVR/Recording device classes       †dvrSupport (whole package)
    │       │   ├── myDriverDvr.java
    │       │   ├── myDriverDvrFolder.java
    │       │   ├── myDriverDvrId.java
    │       │   └── myDriverMultistreamPreferences.java
    │       │
    │       ├── enums/              # Enumerations
    │       │   ├── myDriverDisplayLayoutTypesEnum.java        †dvrDisplay
    │       │   └── myDriverEventTypesEnum.java
    │       │
    │       ├── event/              # Video event handling
    │       │   ├── myDriverEventCameraExt.java
    │       │   ├── myDriverEventDiscoveryLeaf.java
    │       │   ├── myDriverEventDiscoveryList.java
    │       │   ├── myDriverEventDiscoveryPreferences.java
    │       │   ├── myDriverEventFolder.java
    │       │   ├── myDriverEventProxyExt.java
    │       │   └── myDriverVideoEventRecall.java
    │       │
    │       ├── messages/           # Protocol message classes           †both files conditional
    │       │   ├── myDriverPanTiltReq.java        †camera.isPanTiltSupport()
    │       │   └── myDriverFocusControlReq.java   †camera.isFocusSupport()
    │       │
    │       ├── ui/                 # UI classes
    │       │   ├── myDriverVideoAgent.java
    │       │   └── myDriverVideoDecoder.java
    │       │
    │       ├── util/               # Utility classes                   †getCommInfo().isHttp() (whole package)
    │       │   ├── myDriverHttpUtil.java
    │       │   └── myDriverVideoStreamUtil.java
    │       │
    │       └── myDriverNetwork.java      # Top-level network component
```

(No `comm/` package; no `myDriverDeviceFolder.java`; the `ui/` package has exactly 2 files, not 3; the
`messages/` package has exactly 2 files, both conditional, not 5.)

**Net verdict, closing B97-G4**: the corrected tree above is written and cross-checked field-by-field
against `VideoDriverModuleGenerator.java`'s own complete, freshly re-decompiled `generate()` body. The
doc's error is broader than [Block 97] flagged (that session caught `comm/`+`messages/`; this session
additionally catches the fictional `myDriverDeviceFolder.java`, the spurious "Video" infix in 2 of 3
`display/` names, and the fictional Mjpeg/Ffmpeg decoder split in `ui/` in place of the one real generic
decoder file) — consistent with a genuinely stale, hand-maintained illustrative tree that was never
re-generated from the real templates, not a doc simplification of one conditional branch (the NDriver
`learn/` case remains the only clean simplification example in this doc).

## 102.9 — B93-G1 CLOSED: `BCertificateStatusHealth` does not exist anywhere in this session's shipped N5 5.0.0.28 `baja.jar` — confirmed by direct namelist grep, zero matches `[CERT]`

Parent text ([Block 93] §93.8, its own child-gap list): *"Confirm, directly against the shipped N5
`baja.jar`/`niagara.security` bytecode, whether a class actually named `BCertificateStatusHealth` exists
anywhere in the real N5 API surface, or whether S2 p.70's naming is confirmed as a pure slide-authoring
typo for `BCertificateHealth`."*

This session located a genuine, version-matched N5 `baja.jar` (`vendorVersion="5.0.0.28"`,
`Implementation-Version: 5.0.0.28`, confirmed via its own `META-INF/module.xml`/`MANIFEST.MF`, this
session — `poc/dashboardpan-n5/.n5config/modules/baja.jar`, sha256
`0a7fcbfcbd1a609ed0eba0c1abfbf7e3de372b6a51f551dcea497649d4e3fd9c`) not previously used by [Block 93]. A
full `unzip -l` namelist grep for `CertificateStatusHealth` (case-insensitive) returns **zero matches**
(exit code 1 = no match, confirmed). The complete `niagara/security/*Certificate*` class list in this jar
is: `BCertificateAliasAndPassword`, `BCertificateAliasCredential`, **`BCertificateHealth`**,
**`BCertificateStatusEnum`**, `BICertificateAliasAndPasswordContainer`, `BICertificateCredentials`,
`BX509Certificate`, `BX509CertificateCredential`, `crypto/X509CertificateFactory`. `[CERT]` (`unzip -l`
against `baja.jar`, this session, full output above).

**Refinement beyond a pure typo**: the two real, adjacent class names present — `BCertificateHealth` and
`BCertificateStatusEnum` — read together as a plausible source for the slide's fabricated
"BCertificateStatusHealth": it is consistent with either a straight typo for `BCertificateHealth` (as the
gap's own text hypothesized) OR a name-blend of these two genuinely-adjacent real API elements. Both
readings agree on the load-bearing fact: `[CERT]`, the name as printed on the slide does not exist.
`[INFER]` for which specific authoring mistake produced it (unresolvable without the slide author's own
notes — out of scope, not pursued further).

**Net verdict, closing B93-G1**: confirmed `[CERT]` — no class named `BCertificateStatusHealth` exists in
this exact-version-matched, shipped N5 5.0.0.28 `baja.jar`. The slide's naming is not a real, still-shipping
N5 API surface.

## 102.10 — B93-G2 CLOSED: [Block 4] §4.7's "niagara-help's own `source/` dir" phrase refers to the N4-baseline sibling corpus's git-tracked directory, not this N5 corpus's own untracked one — confirmed by exact file-count match `[CERT]`

Parent text ([Block 93] §93.9, its own child-gap list): *"Documentation-only: clarify... which of the two
`niagara-help/source/` directories (this corpus's untracked, N5-content-holding `niagara5-research/
niagara-help/raw/source/`, vs. the actual N4-baseline, `git`-tracked `niagara-research/niagara-help/
source/` in the sibling corpus) [Block 4] §4.7's own 'niagara-help's own source/ dir (REMIT)' phrase refers
to — this session resolved it correctly by line-count cross-check against [Block 4]'s own cited figure, but
a future reader taking the phrase literally inside this corpus would silently compare N5 against N5."*

Direct `find -iname '*.java' | wc -l` this session on both candidate directories: `/home/cristian/
niagara-research/niagara-help/source/` (the N4-baseline, git-tracked, SIBLING corpus directory) = **2,603**
files, an EXACT match to [Block 4] §4.7's own cited figure ("2,603 Java files / 679K lines"). The N5
corpus's OWN directory at the naively-identical-looking relative path, `/home/cristian/niagara5-research/
niagara-help/raw/source/`, = **2,868** files — matching [Block 4]'s own SEPARATE table row for
`docSource.jar`'s N5-side extraction ("2,868 `.java`"), i.e. the thing [Block 4] was COMPARING AGAINST, not
the REMIT baseline itself. `[CERT]` (direct `find | wc -l`, both paths, this session, exact counts above).

**Clarifying statement for any future reader of this corpus** (satisfying the gap's own request, recorded
here rather than in a separate corpus-conventions file per this block's own scope restriction against
editing other files): whenever a `niagara5-research`-corpus block says "niagara-help's own `source/` dir"
as an N4 REMIT baseline (as [Block 4] §4.7 does), it means the SIBLING corpus's path
`/home/cristian/niagara-research/niagara-help/source/` (2,603 `.java`, git-tracked) — NOT this corpus's own
`/home/cristian/niagara5-research/niagara-help/raw/source/` (2,868 `.java`, untracked), which is itself
already this corpus's own N5-side comparison target, not a baseline.

**Net verdict, closing B93-G2**: confirmed `[CERT]` by exact figure match; clarification recorded above.

## 102.x — Corrections to earlier blocks

- **[Block 75] §75.5, claim**: *"`doc/js/buildingJS.html` is CONFIRMED-STALE, unmodified-for-N5 N4-era
  content — explicit 'Niagara 4' framing, a wizard transcript defaulting to version '4.10', and a Gradle
  plugin id (`com.tridium.n-grunt`) absent from this install's own local Maven repository."*
  **New evidence (§102.7, this session)**: a full line-by-line `diff -u` of the actual preserved N4 vs N5
  plain-text doc extractions shows **at least 15 distinct, deliberate content edits** in `buildingJS.txt`
  alone (tense changes, a wholly new Gradle/`nodeHome` paragraph, a new `niagara_config_home` env var,
  updated install-path examples, systematic removal of the `-ux` submodule naming convention from every
  code sample, a changed BIJavaScript package citation, a changed Gradle plugin-id citation) plus a deleted
  bullet in the sibling `requirejs.html` (the Hx `requireJs()` line, consistent with Hx's own removal).
  **Corrected claim**: the doc is **NOT** an unmodified N4-era carryover — it is a genuinely,
  substantively-edited N5 revision with a small number of specific unedited residuals (the "(4.10)" wizard
  default, one leftover un-de-branded "Niagara 4" mention in the tutorial's closing summary, and a
  transposed-package doc typo). [Block 75]'s SPECIFIC three citations (the "(4.10)" default, one "Niagara
  4" mention, the `n-grunt` plugin-id string) remain individually accurate as quoted strings — only the
  broader "unmodified-for-N5" summary inference was wrong; the `com.tridium.n-grunt` citation in particular
  is itself proof of an N5-specific EDIT (N4's own doc said `com.tridium.niagara-grunt`), not evidence of
  staleness. Evidence: `diff -u` of `niagara-research/niagara-help/devguide-clean/js/buildingJS.txt`
  (sha256 `927a09900062e3884add8771431fee5b359bc883804452371de0e6fbb84189c9`) vs `niagara5-research/
  niagara-help/guides-clean/js/buildingJS.txt` (sha256
  `735e37b7adb0a13f224967239591410df90225a461cfa383f6e9976d80612856`), and the same-named `requirejs.txt`
  pair (N4 sha256 `0231d95811ff94a902159ae884bda1c20d32666c0efddd01548dcf1b69ba4ae5`, N5 sha256
  `51fc473f4a641446dc464e054dc100fb797b5d1b2d7e7fd2bd436ec675c8b111`), this session.

- **[Block 89] §89.7 / [Block 97] §97.3, claim**: *"`VideoDriverModuleGenerator`'s own `generate()`
  override... queue[s] up to 24 conditional `addTemplateWrite()` calls"* (repeated by [Block 97] §97.3 as
  "matching [Block 89] §89.7's own 'up to 24 conditional `addTemplateWrite()` calls' count exactly").
  **New evidence (§102.8, this session)**: a fresh, complete Vineflower decompile of
  `VideoDriverModuleGenerator.class` (`n-templates-5.0.54.9.2.jar`, sha256
  `285e6463e99ae0c4e1ed303792150773c344c8593cc1af29aac1dfb132bb2405`) shows the `generate()` method
  contains **32** total `addTemplateWrite()` calls (18 unconditional + 14 conditional across
  `dvrSupport`/`dvrDiscovery`/`dvrDisplay`(×4)/`isHttp()`(×2)/`isPanTiltSupport()`/`isFocusSupport()`).
  **Corrected claim**: 32, not 24. This is a pure arithmetic slip, NOT a contradiction of either block's
  own DESCRIPTIVE package-by-package manifest — [Block 97] §97.3's own prose enumeration (independently
  re-verified line-by-line against this session's fresh decompile) correctly names every one of the 32
  calls; only the summary headline number, inherited unchecked from [Block 89] §89.7, was wrong. Does not
  affect either block's own closing verdicts (B74-G1's mechanism-mirroring finding, B9-G4's
  doc-mismatch finding) since neither depended on the exact count.

## 102.x — Connections

- **[Block 21]** — this session's ALREADY-COVERED checks (§102.1-102.2) confirm B21-G1/B21-G2 remain
  closed by [Block 75]; untouched otherwise.
- **[Block 36]** — B36-G1's own closure (by [Block 75] §75.5) is reused, then sharpened by this session's
  own §102.7 diff (§102.3); B36-G3 is now fully CLOSED via [Block 79]'s own refinement B79-G3 (§102.4) —
  this session supplies the live-network evidence both [Block 36] and [Block 79] were blocked on.
- **[Block 75]** — §102.3/§102.7 reuse and then correct §75.5's own summary framing (see Corrections);
  §75.3/§75.4 (B21-G1/B21-G2) and §75.3's own class list (reused as the ground truth for B79-G1's
  call-graph census, §102.5) are otherwise unaffected and not re-litigated.
- **[Block 79]** — closes its own B79-G1 (mostly, §102.5), B79-G2 (fully, §102.6), and B79-G3 (fully,
  §102.4); its own §79.3/§79.4 findings (JxBrowser fallback correction, `grunt-niagara` local-install
  negative-evidence sweep) are reused as-is, not re-derived.
- **[Block 89]/[Block 97]** — §102.8 reuses [Block 97] §97.3's own DESCRIPTIVE manifest as ground truth
  (independently re-verified `[CERT]` against a fresh decompile) while correcting the "24" headline number
  both blocks share (see Corrections); B97-G4 itself is now CLOSED with the exact corrected tree, going
  beyond [Block 97]'s own comm/+messages/-only finding to also catch the `myDriverDeviceFolder.java`,
  `display/`'s spurious "Video" infix, and `ui/`'s fictional decoder-split errors.
- **[Block 93]** — closes both of its own remaining child gaps, B93-G1 (§102.9) and B93-G2 (§102.10), with
  no external dependency, consistent with HEAVY mode's instruction to pursue cheaply-investigable gaps
  alongside the harder source-gated ones.
- **[Block 4]** — §102.10's exact file-count cross-check (2,603 vs 2,868) directly reuses and confirms
  [Block 4] §4.7's own cited figures without re-deriving them.

## 102.x — Child gaps opened

- **B102-G1** (opened by §102.5's own naming-lineage finding) — Confirm whether N4's Workbench-Swing
  `pxEditor` module (`com.tridium.px.editor.make.BMakeWidget` and its whole `BMw*` family) still ships in a
  full N5 5.0.0.28 install at all; this session's own mounted N5 install path carries no Niagara module
  jars whatsoever (only third-party libs, confirmed by a full `find`), so the question is unanswerable from
  this environment. If it does still ship, a follow-up could determine whether uxBuilder's `ux/make`
  subsystem was consciously modeled on `pxEditor`'s older wizard (shared design lineage, confirmed by
  identical naming) or is coincidental. `investigable`, low-priority, `blocked-on-source` (needs a full N5
  module-set install, not this corpus's current minimal mount).
- **B102-G2** (opened by §102.6's own toggle-name trace) — This session confirmed `BUxBuilderJsBuild`'s own
  WebDev toggle name (`"uxBuilder"`) and traced the FULL code-side mechanism deciding raw-vs-built JS
  serving, but did NOT actually flip the toggle against a live station to empirically observe the served
  HTML/RequireJS-config difference; a `requires-execution` follow-up (a live N5 Workbench/station session,
  toggling `spy:/webDevSetup/enable-uxBuilder`/`disable-uxBuilder` and diffing the served page source)
  would be the strongest possible confirmation, beyond the static code trace already `[CERT]`-complete
  here. `investigable`, low-priority (the static trace is already conclusive for the mechanism question the
  parent gap actually asked).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | B21-G1/B21-G2/B36-G1 remain closed by [Block 75]; no later block reopened them | [CERT] | `grep -rl <gap-id> niagara5-block*.md` full sweep, this session |
| 2 | `grunt-niagara` is a live, public npm package, v2.3.0 (2025-10-17), zero rename history | [CERT-web] | `github.com/tridium/grunt-niagara` `package.json`+`CHANGELOG.md` (raw, fetched), `registry.npmjs.org/grunt-niagara`, this session |
| 3 | Zero Java references anywhere in `organized/` to `MakeWidget`/`MwPropertiesWidget`/`MwPalettePreview`/`mwUtils`/`BoundOrdReplaceEditor`/`VariablesEditor` | [CERT] | full-corpus `grep -rl`, this session, zero matches |
| 4 | 5 of 6 orphan JS files are `require()`d exclusively by the JS half of already-Java-paired `BUxMw*` classes | [CERT] | per-module-path `grep -rl`, `organized/uxBuilder/vineflower`, this session, table in §102.5 |
| 5 | `com.tridium.px.editor.make.BMakeWidget` (+ full `BMw*` family) exists in the N4 4.14 baseline `pxEditor-wb` decompile; absent from N5 corpus and from this session's minimal N5 install mount | [CERT] | `pxEditor-wb/decompiled/.../BMakeWidget.java` sha256 `98dd4146d298bda81009441720f0fa690039e7c9b098c7a99e265126f7b05780`; `find -iname '*.jar'` over `/mnt/c/Program Files/Niagara/5.0.0.28`, 128 hits, zero Niagara modules |
| 6 | `WebDev`→`BJsBuild.isWebDevEnabled()`→`JsInfo.addBuilds()`/`BIWebResource.STANDARD_WEBDEV_FILTER`→`RequireJsUtil` is the real raw-vs-built JS serving toggle chain | [CERT] | `BJsBuild.java:143`, `JsInfo.java:94-95`, `BIWebResource.java:47-48`, `RequireJsUtil.java:169-172`, this session, sha256s in §102.6 |
| 7 | `BUxBuilderJsBuild`'s own WebDev id is literally `"uxBuilder"`, pointed at `module://uxBuilder/rc/uxBuilder.built.min.js` | [CERT] | `BUxBuilderJsBuild.java`, decompiled in full, this session, quoted verbatim in §102.6 |
| 8 | N4 vs N5 `buildingJS.txt`/`requirejs.txt` differ by 15+ deliberate content edits, not zero | [CERT-doc] | `diff -u`, both file pairs, sha256s in §102.7/Corrections, this session |
| 9 | `VideoDriverModuleGenerator.generate()` contains exactly 32 `addTemplateWrite()` calls (18 unconditional + 14 conditional) | [CERT] | fresh Vineflower decompile, `VideoDriverModuleGenerator.java:56-173`, sha256 `285e6463e99ae0c4e1ed303792150773c344c8593cc1af29aac1dfb132bb2405`, this session |
| 10 | `buildN5.html`'s VideoDriver tree is wrong in `comm/` (fictional), top-level `myDriverDeviceFolder.java` (fictional), `display/` (2 of 3 names have a spurious "Video" infix), and `ui/` (fictional Mjpeg/Ffmpeg decoder split, missing the one real generic decoder) | [CERT] | `buildN5.html` sha256 `ffa1acff911679c68e3865a94e994a8a0595590e1c3486db9dab004c62fb5c70` vs `VideoDriverModuleGenerator.java`'s complete `generate()` body, this session, table in §102.8 |
| 11 | `BCertificateStatusHealth` does not exist in a version-matched (`5.0.0.28`) N5 `baja.jar`; only `BCertificateHealth`/`BCertificateStatusEnum` exist among candidates | [CERT] | `unzip -l` full namelist grep, `baja.jar` sha256 `0a7fcbfcbd1a609ed0eba0c1abfbf7e3de372b6a51f551dcea497649d4e3fd9c`, this session |
| 12 | [Block 4] §4.7's "niagara-help's own `source/`" REMIT baseline = the N4-baseline sibling corpus's `niagara-help/source/` (2,603 `.java`), not this corpus's own `niagara-help/raw/source/` (2,868 `.java`) | [CERT] | `find -iname '*.java' \| wc -l`, both paths, this session, exact counts in §102.10 |

**Tally**: 10 `[CERT]`-class claims (rows 1, 3, 4, 5, 6, 7, 9, 10, 11, 12), 1 `[CERT-web]` (row 2), 1
`[CERT-doc]` (row 8), 0 `[INFER]` load-bearing claims (one `[INFER]` sub-note in §102.9 is explicitly
non-load-bearing, flagged as unresolvable and out of scope). [INFER]/[CERT*] ratio: 0/12 = 0.00 — this is
an EVIDENCE block (direct bytecode/source/live-network verification throughout), a 0.00 ratio is expected
and healthy for this block TYPE, not a sign of exhausted investigation.

**Artifacts**: no new artifact dumps preserved outside this file — all decompiled sources this session were
read in full from a scratch working copy (`/tmp/claude-1000/.../scratchpad/b102/extract/`, per this
session's own instructions, never committed to either repo) and cited above by their SOURCE jar path +
sha256 + decompiled-filename:line, matching this corpus's existing convention for reading-without-
preserving a fresh decompile (e.g. [Block 89] §89.7's own `VideoDriverModuleGenerator.java` citation
style). Every `[CERT]`/`[CERT-doc]` citation above resolves to a file already present in `organized/`
(both corpora) except the two freshly-decompiled `.java` files (`VideoDriverModuleGenerator.java`,
`NDriverModuleGenerator.java`, `NiagaraTypeInfo.java`), which are the same source jar Block 89/97 already
read from (`n-templates-5.0.54.9.2.jar`, present at `organized/devkit/extracted/LIB-INF/`,
sha256-verified unchanged).
