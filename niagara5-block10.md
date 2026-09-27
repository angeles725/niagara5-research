# Block 10 — Official N4→N5 transition guides: breaking changes and a porting checklist for our modules

> Research of **Niagara 5's official module-porting documentation** (`doc/upgrade/*.html` +
> `doc/upgradingJDK.html` + `doc/modules.html` + `doc/ui/uiChangelog.html` inside `docDeveloper.jar`)
> cross-applied against our three live N4 modules (ColdRoomPan, CompPan, DashboardPan). Scope: full-text
> read of every file named in the gap, a structured breaking-changes table, the step-by-step module
> transition procedure, JDK 8→25 and Fox-interop notes, and a module-by-module porting checklist backed by
> `grep`/`cat` evidence from the actual module sources. Does **not** cover: BACnet driver internals beyond
> the doc's own summary, a live N5 build/compile attempt (no N5 Gradle environment run this session), or
> the `docSource.jar` Java source itself (only the doc prose citing it).
>
> Subject version (doc side): Niagara **5.0.0.28 (Beta)**, `docDeveloper.jar` at
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` — same install [B1]–[B4]
> read. Subject version (module side): git worktree
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`, commit
> `a109249d98b795c934c71b2165af976dbc39716e` (2026-09-05), branch `main` — per user memory this is the
> non-stale worktree for client reads (the plain `Leon-Guanjuato` checkout is stale at `4f5f1c7`).
>
> Sources: `docDeveloper.jar` zip entries `doc/upgrade/upgradingToN5.html`, `doc/upgrade/upgradingUItoN5.html`,
> `doc/upgrade/usingFoxProxySession.html` (the complete `doc/upgrade/` directory — censused, no other file
> exists there), `doc/upgradingJDK.html`, `doc/modules.html`, `doc/ui/uiChangelog.html`; all extracted to
> plain text under `/tmp/claude-1000/n5b10/` this session via `python3 zipfile` + a custom HTML-stripper
> (no external tool). Module sources: `niagara-module.xml`, `<part>.gradle.kts`, `module-include.xml`,
> `module-permissions.xml`, and all `.java`/`.html` files under `Compresores/CompPan/`,
> `Dashboard/DashboardPan/`, `Paccadia/ColdRoomPan/` in the worktree above, read via `cat`/`grep -rn`.
>
> Method: full HTML→text extraction and read-through (not keyword sampling) for every doc file named in
> the gap; `grep -rn`/`cat` census of the three module trees. Markers: `[CERT]` local primary source
> (`file:line`) · `[CERT-doc]` the shipped Niagara 5 doc, cited by zip-entry path + `<title>`/section
> (extern to this corpus per [B4] §4.x convention — no `file:line` resolves under
> `/home/cristian/niagara5-research`) · `[INFER]` deduction/synthesis.
>
> Build/porting layer. Connects [B1] (module.xml schema, runtime profiles gone), [B2] (Gradle plugin
> renames, JPMS `module-info.java`, annotation-processor split), [B3] (directory layout, Security
> Manager replacement), [B4] (doc corpus census, §4.11/§4.12 keyword census of this same guide, §4.13
> `docUser` absence, child gap B4-G8 which this block closes).
>
> **Type:** `mixed` — §10.1–§10.9 are evidence blocks reading the shipped doc; §10.10–§10.12 draw
> `[INFER]` conclusions by cross-applying that evidence against three prior-session module trees (not this
> block's own `[CERT]` sources alone), which is the declared trigger for `mixed` per METHODOLOGY §4.

---

## 10.1 — `doc/upgrade/` census: exactly three files, all read in full `[CERT]`

A `zipfile.namelist()` filter for `doc/upgrade/` inside `docDeveloper.jar` returns exactly three HTML
files (plus the directory entry) — there is no fourth file to "read all others" of:

| Zip entry | Raw bytes | Stripped text bytes |
|---|---|---|
| `doc/upgrade/upgradingToN5.html` | 93,112 | 67,828 |
| `doc/upgrade/upgradingUItoN5.html` | 68,971 | 51,608 |
| `doc/upgrade/usingFoxProxySession.html` | 3,745 | 1,785 |

`[CERT]` (`zipfile.ZipFile.namelist()` filtered on prefix `doc/upgrade/`, this session; all three files
opened and their full text read below — not keyword-sampled, unlike [B4] §4.11 which only keyword-hit
these same three paths). This closes named child gap **B4-G8** ("deep-read
`doc/upgrade/upgradingUItoN5.html` ... high value for any module with a `-ux`/`-wb` part").

The three additional files named in the gap (`doc/upgradingJDK.html`, `doc/modules.html`,
`doc/ui/uiChangelog.html`) live outside `doc/upgrade/` but were also censused and read in full (§10.5,
§10.9, §10.7).

## 10.2 — `upgradingToN5.html`: "Niagara 5 Module Transition Guide" — full structure `[CERT-doc]`

Titled **"Niagara 5 Module Transition Guide"**. Top-level structure (confirmed by its own TOC, read in
full): Intro → **Niagara 4 Environment** (upgrade to 4.15, fix compiler warnings, **Module Part
Combination**, Niagara 4 Wrap-up) → **Niagara 5 Environment** (directories, Gradle build environment,
Java 25 changes, `javax.baja`→`niagara` namespace, private-API-to-public-API moves, Servlets, New Core
APIs, **Niagara 5 Breaking Changes**, Compiling and Testing, **Modularity**, Third Party Libraries,
Niagara 5 Wrap-up) → **Tips & Tricks** (Common Issues, Code Signing, Multi-Module Projects, Modularity
errors). `[CERT-doc]` (`doc/upgrade/upgradingToN5.html`, TOC + full body, 67,828 chars read this session).

This single document is confirmed as the intended **one-stop porting guide**: its Intro states "This guide
serves to help developers take their existing Niagara 4 modules and make the changes required so that
they will run in a Niagara 5 environment," and every subsequent guide in this block (`upgradingUItoN5.html`,
`upgradingJDK.html`, `usingFoxProxySession.html`) is a referenced sub-guide branching off one of its
sections. `[CERT-doc]` (same file, "Intro" section).

## 10.3 — Step-by-step Module Transition procedure `[CERT-doc]`

**Phase A — stay in Niagara 4.15** (do this first, before touching N5 at all):
1. Upgrade build scripts to 4.15; update module dependencies to 4.15.
2. Enable `-Xlint:deprecation -Xlint:overrides -Xlint:unchecked -Werror` on `JavaCompile`; fix every
   warning; confirm `gradlew moduleTestJar` + tests pass.
3. **Module Part Combination** (skip entirely if the module has only one part):
   - **`-doc` part** (if present): extract into a brand-new module `doc<YourModuleName>` via
     `gradlew addModule --module-name doc<YourModuleName> --runtime-profiles doc --base-package none
     --copyright none --vendor none`; move `src/`, the `.gradle.kts` contents (renaming its
     `moduleName.set(...)` line), delete the old `-doc` folder, strip `doc` from the old module's
     `runtimeProfiles`, sync `preferredSymbol`, retarget any `help.guide.base` lexicon key, rebuild and
     re-check Workbench Help.
   - **Remaining parts** (rt/ux/wb/se): pick the **highest-level** part as destination using the fixed
     precedence `rt(4) > ux(3) > wb(2) > se(1)`; merge `.gradle.kts` plugins/dependencies/resource-copy
     blocks, cut-paste `src`/`srcTest`, merge `module.lexicon`/`module.palette`/`module-permissions.xml`,
     delete-and-let-regenerate any auto-generated `module-include.xml`/`moduleTest-include.xml` (hand-
     maintained ones must be merged), delete `node_modules` for a source `-ux` part, delete empty source
     folders, collapse `niagara-module.xml`'s `runtimeProfiles` to just the destination part, fix any
     sibling-module dependency on the now-gone part id, `gradlew moduleTestJar`, `nre -buildreg`, full
     functional retest. **This is the last N4-only checkpoint.**
4. Niagara 4 Wrap-up: module compiles as a single part, zero warnings, in N4.15.

**Phase B — target Niagara 5** (install the N5 SDK, then, per module):
5. Update dev-environment directories (`niagara_home`, new `niagara_config_home`, `niagara_user_home`) —
   see §10.9-adjacent table in §10.3 below and cross-ref [B3].
6. Point `JAVA_HOME`/`org.gradle.java.installations.paths` at a Java 25 JDK+JavaFX (the bundled
   `<niagara5_home>/jre` works unless the `n-helper-modularity` plugin needs a full JDK toolchain).
7. `gradlew.bat wrapper --gradle-version 9.2.1`; add `niagara_config_home=...` to `gradle.properties`;
   update `niagara_home`/`niagara_user_home` there too.
8. Global search/replace every Gradle plugin id per the rename table (§10.4 BC-25); fix
   `settings.gradle.kts` (`toLowerCase()`→`lowercase()`, the plugin-repo URL escape, and the two version
   constants `gradlePluginVersion="5.0.54.9.2"` / `settingsPluginVersion="5.0.9.8.14"`).
9. Rename `<module>-<part>.gradle.kts`/its directory to drop the part suffix; remove the
   `niagara-annotation-processors` plugin, add `com.tridium.n-helper-modularity`; simplify
   `moduleManifest{}` to just `moduleName.set(...)` (delete the `runtimeProfile.set(...)` line and its
   `RuntimeProfile` import); strip every dependency's module-part suffix and de-duplicate; add
   `annotationProcessor(":niagaraAnnotationProcessors")` + `nre(":niagaraAnnotationProcessors")`.
10. Strip `runtimeProfiles` entirely from `niagara-module.xml`.
11. Fix Security-Manager fallout (§10.5), rename `javax.baja.*`→`niagara.*` and the listed
    private-API packages (§10.4 BC-14..BC-19), migrate servlets to `jakarta.servlet` (§10.4 BC-22).
12. `gradlew slotomatic`, then `gradlew jar`; iterate on remaining Java-25/JPMS errors.
13. Add `module-info.java` (and a test one) per §10.9; resolve `Package found in more than one module`
    split-package errors and `requires-automatic` warnings as they surface.
14. Full functional retest; Niagara 5 Wrap-up.

`[CERT-doc]` (`doc/upgrade/upgradingToN5.html`, sections "Niagara 4 Environment" through "Niagara 5
Wrap-up", full text read and condensed this session — not paraphrased from a summary).

## 10.4 — Niagara 5 Breaking Changes: full table `[CERT-doc]`

The doc's own **"Niagara 5 Breaking Changes"** heading (`upgrade/upgradingToN5.html`) enumerates **13**
items under three subheads (Core: 8, Drivers: 2, UI: 3) and explicitly says "A full list of breaking
changes in 5.0 can be found at Niagara 5.0 Breaking Changes [external cross-reference doc, not shipped in
this jar] — some important ones you may be likely to run into are detailed below." This block's table
below is **broader**: it adds the private-API-relocation items (documented earlier in the same file under
"Private API moved to Public API") and the build/tooling items (Servlets, Modularity, Security Manager)
because they are equally source-breaking even though the doc files them under a different heading. Rows
tagged **[§BC]** are inside the doc's own "Breaking Changes" heading; untagged rows are breaking changes
documented elsewhere in the same guide.

| ID | Area | Change | N4 thing affected | N5 replacement / action | Doc path + section |
|---|---|---|---|---|---|
| BC-01 §BC | Core/logging | AX `Log` removed | `javax.baja.log.Log` | `java.util.logging.Logger` | `upgrade/upgradingToN5.html` §Removed Classes and Methods |
| BC-02 §BC | Core/app | `app` module removed | Mobile-app `AppContainer` in `config.bog` | manual removal, or automatic via `n5mig` station migrator | same §app module removed |
| BC-03 §BC | Core/fox | non-TLS Fox slated for future removal | plaintext Fox connections | plan TLS-only Fox; see BFoxProxySession notes (§10.8) | same §Non-TLS fox Connections + `upgrade/usingFoxProxySession.html` |
| BC-04 §BC | Core/naming | `isUnoperational()` renamed | any override/call of `isUnoperational()` | `isNonOperational()` (+ `isOperational()` now always paired) | same §isOperational |
| BC-05 §BC | Core/i18n | `getLanguage()` removed | `Sys.getLanguage()`, `Context.getLanguage()` | `getLanguageCode()` (lang_variant form) | same §Sys.getLanguage |
| BC-06 §BC | Core/runtime | `RuntimeProfile` on `BModule` removed | `BModule.getRuntimeProfile(FilePath)`, `getRuntimeProfiles()`, `getVendorVersion(RuntimeProfile)` | overloads without the parameter | same §RuntimeProfile and BModule; cross-ref [B1] §1.3 |
| BC-07 §BC | Core/chart | package move | `javax.baja.chart.*` (`BAxisDimension`, `BAxisLocation`, `TrendFlags`, `BAxisBound`, `BColumnIdentifier`) | `niagara.chart.data.*` | same §javax.baja.chart |
| BC-08 §BC | Core/query | package move | `javax.baja.query.*` (`BIQueryHandler`, `BQueryResult`, `BQueryScheme`) | `niagara.collection.*` | same §javax.baja.query |
| BC-09 §BC | Drivers | frameworks deprecated (not removed) | `basicDriver` / `devDriver` | unsupported; suppress `-Xlint:deprecation` or `@SuppressWarnings` if kept | same §basicDriver & devDriver |
| BC-10 §BC | Drivers/BACnet | public API simplified | BACnet `Descriptor` interface, static constants on interfaces | simplified `Descriptor`, `Context`-taking methods, constants moved to public static classes | same §BACnet |
| BC-11 §BC | UI/bajaui | paint/layout signatures | custom `BWidget` overrides of `paint()`, `doLayout()`, `computePreferredSize()` | `doPaint(Graphics,IRenderContext)`, `doLayout(IRenderContext)`, `doComputePreferredSize(...)` via `IRenderContextAware` | `upgrade/upgradingUItoN5.html` (whole doc); summarized in `upgradingToN5.html` §Module Transition Guide for UI Developers |
| BC-12 §BC | UI/browser | Web Launcher + Kiosk removed | `bajaui`-based browser UI, `BKioskProfile` | `bajaux`/hx/axvelocity/custom servlets only | `upgrade/upgradingToN5.html` §Web Launcher and Kiosk Mode removed |
| BC-13 §BC | UI/BajaScript | build-tool + JS API changes | `niagara-moduledev`<0.2.1, `grunt-niagara`<2.3.0, `Complex.js#getFacets`, manual batching, `Callback` API | bump tool versions; `getSlotFacets`; automatic batching; `Promise`s | same §BajaUx/BajaScript |
| BC-14 | Core/namespace | public-API namespace-wide rename | any `javax.baja.*` import | `niagara.*` (mechanical search/replace) | `upgrade/upgradingToN5.html` §javax.baja Namespace |
| BC-15 | Core/JSON | package move + new dep | `com.tridium.json.*` (JSON-Java) | `org.json.*` + `api("org.json:json:20251224")` | same §JSON-Java |
| BC-16 | Drivers/nDriver | package move | `com.tridium.ndriver.*` | `niagara.ndriver.*` | same §nDriver Public API |
| BC-17 | Core/nre | 9 classes promoted private→public | `com.tridium.nre.*` (`IElement`, `EncryptionKeySource`, `SecretChars`/`SecretBytes`/`ISecretBytesSupplier`, `Single`/`Pair`/`Triple`, `CertificateHealth`, `CertificateStatusEnum`, `IpProtocol`, `PasswordStrength`) | `niagara.nre.*` (same method signatures) | same §nre module |
| BC-18 | Core/baja | 4 classes promoted + 1 renamed | `com.tridium.util.ArrayUtil` (+ removed `sort`/`remove`/`testAny`/`testAll`/`binarySearch`), `BServerCertificateHealth`, `BCertificateStatusEnum`, `BDataTable`/`BDataRow`, `LoginFailureCause` | `niagara.util.ArrayUtil` (use `java.util.Arrays`/`removeOne()`/streams), `niagara.security.BCertificateHealth` (renamed), `niagara.data.*`, `niagara.authn.LoginFailureCause` | same §baja module |
| BC-19 | Drivers/bacnet | package move | `com.tridium.bacnet.asn.{AsnUtil,AsnInputStream,AsnOutputStream}` | `niagara.bacnet.asn.*` | same §bacnet module |
| BC-20 | Build/structure | module parts eliminated | any multi-part module (`-rt`/`-ux`/`-wb`/`-se`/`-doc`) | single directory, packages separate concerns; `-doc` becomes its own `doc<Module>` module | same §Module Part Combination |
| BC-21 | Build/security | Security Manager removed (Java 25) | `AccessController`/`PrivilegedAction`/`PrivilegedActionException` imports, `module-permissions.xml` | `niagara.nre.util.SecurityUtil` + `niagara.nre.security.privileged.*`; permissions become `module-info.java` annotations (9-row mapping table, §10.5) | same §Security Manager; `doc/upgradingJDK.html` |
| BC-22 | Build/web | Jetty 12 / Servlet 6 | `javax.servlet-api:4.0.1`, `javax.servlet.*` imports, `jetty-web.xml` `Configure` class | `jakarta.servlet-api:6.1.0`, `jakarta.servlet.*`, `org.eclipse.jetty.ee11.webapp.WebAppContext` | same §Servlets |
| BC-23 | Build/packaging | uberjar breaks modularity | `uberjar(...)` dependency type | `unterjar(...)` (same syntax; ships whole jar into `LIB-EXT` instead of exploding it) | same §uberjar |
| BC-24 | Build/JPMS | explicit module descriptor now expected | modules with no `module-info.java` (silently become "automatic modules") | `module-info.java` + `module-info.java` (test) with `requires`/`exports`/`opens`/`uses`/`provides` | same §Modularity; `doc/modules.html` |
| BC-25 | Build/gradle | 9 plugin-id renames | `com.tridium.niagara-module`, `-signing`, `-jacoco`, `-grunt`, `settings.multi-project`, `settings.local-settings-convention`, `convention.niagara-home-repositories` | `com.tridium.n-module`, `sign`, `jacoco`, `grunt`, `set.mpr`, `set.lsc`, `conv.n-repo` (full table §Plugin Names) | same §Plugin Names; cross-ref [B2] §2.2 |
| BC-26 | Build/gradle | annotation-processor module split out of `nre` | `id("com.tridium.niagara-annotation-processors")`, implicit `@NiagaraType` resolution via `nre` | `id("com.tridium.n-helper-modularity")` + explicit `annotationProcessor(":niagaraAnnotationProcessors")` + `nre(":niagaraAnnotationProcessors")` | same §plugins / §dependencies (`<module>.gradle.kts`); cross-ref [B2] §2.6 |
| BC-27 | Build/gradle | wrapper + plugin versions bumped | Gradle 4.15-era wrapper | Gradle **9.2.1**; `gradlePluginVersion=5.0.54.9.2`; `settingsPluginVersion=5.0.9.8.14` | same §Gradle Wrapper / §settings.gradle.kts; cross-ref [B2] |
| BC-28 | Env/dirs | new Configuration Home; other dirs moved | `C:\Niagara\...`, `C:\ProgramData\Niagara4.x\...`, no config home | `C:\Program Files\Niagara\5.x...` (Home, read-only), `C:\ProgramData\Niagara\<brand>\config\5.x...` (new Config Home), daemon/user homes reshuffled | same §Updated Niagara Directories; cross-ref [B3] |
| BC-29 | Runtime/security | program-object signing now mandatory by default | unsigned `BProgramObject`s in `config.bog` | valid code-signing cert configured under Workbench→Tools→Options→Code Signing before `n5mig` | same §New Requirement for Program Objects in Niagara 5 |
| BC-30 | UI/BajaScript | method rename | `baja.Complex#getFacets` | `baja.Complex#getSlotFacets` | `doc/ui/uiChangelog.html` §Niagara 5.0 › Breaking changes |
| BC-31 | UI/bajaui | classes deleted | `nmodule/bajaui/rc/model/UxModel`, `.../BindingList` (deprecated in 4.15, moved to `bajaux`) | fully deleted in 5.0; must already be on the `bajaux/model/...` import path | same §Niagara 5.0 › UxModel and BindingList deleted from bajaui |
| BC-32 | UI/BajaScript | non-standard method removed | `Array#contains` (BajaScript polyfill) | standard `Array#includes` | same §Niagara 5.0 › BajaScript no longer adds Array#contains |

`[CERT-doc]` (every row traced to the cited section this session — `upgrade/upgradingToN5.html` §§ listed
above, `upgrade/upgradingUItoN5.html` full read, `ui/uiChangelog.html` §Niagara 5.0 full read).

## 10.5 — JDK 8→25 migration: Security Manager and the permission-annotation model `[CERT-doc]`

`doc/upgradingJDK.html` (7,153 raw bytes) is a short pointer document: it does **not** enumerate JDK
breaking changes itself, instead directing to external Oracle resources (JDK Migration Guide, Java
Almanac API-diff tool, JEP history, Java Version History on Wikipedia) and flags the Security Manager
removal as "the most significant change you might encounter." It also states the JDK 8 Compact3-vs-SE
split (embedded vs. Supervisor) is gone in N5 — **all** devices, including embedded, now run full JDK 25
Standard Edition (embedded stays headless). `[CERT-doc]` (`doc/upgradingJDK.html`, full text).

The concrete migration mechanics live back in `upgradingToN5.html` §Security Manager:

| Niagara 4 API | Niagara 5 replacement |
|---|---|
| `import java.security.AccessController` | `import niagara.nre.util.SecurityUtil` |
| `import java.security.PrivilegedAction(Exception)?` | `import niagara.nre.security.privileged.PrivilegedAction(Exception)?` |
| `AccessController.doPrivileged(...)` | `SecurityUtil.doPrivileged(...)` |
| a module's `module-permissions.xml` | **deleted**; permissions become `@Grant*` annotations on `module-info.java` |

Permission-annotation mapping (9 rows, `upgradingToN5.html` table):

| N4 permission group | N5 annotation |
|---|---|
| `KEY_STORE` | `@GrantKeyStorePermission(keyStoreName, action)` |
| `SET_SYSTEM_TIME` | `@GrantPublicNiagaraPermission(PublicNiagaraPermission.SET_TIME)` |
| `BACKUPS` | `@GrantPublicNiagaraPermission(PublicNiagaraPermission.RESTORE_BACKUP)` |
| `MANAGE_SERVER_TRUST_ANCHORS` | `@GrantPublicNiagaraPermission(PublicNiagaraPermission.MANAGE_SERVER_TRUST_ANCHORS)` |
| `RDB` | `@GrantPublicNiagaraPermission(PublicNiagaraPermission.RDB_CONNECTION)` |
| `RENAME_AND_RESTART_STATION` | `@GrantPublicNiagaraPermission(PublicNiagaraPermission.RENAME_AND_RESTART)` |
| `RUNTIME_EXECUTION` | `@GrantRuntimeExecPermission(filePath)` |
| `SIGNING` | `@GrantSigningPasswordPermission(String value)` |
| *(none — new)* | `@NiagaraEnableNativeAccess` |

`[CERT-doc]` (`upgrade/upgradingToN5.html` §Security Manager, table read verbatim; cross-ref [B3] §3.8
which found the N5 permission enforcement path is a `-javaagent` + ByteBuddy `PermissionManager`, not a
`SecurityManager` subclass — consistent with this doc's "Security Manager was removed" claim).

## 10.6 — UI transition guide (`upgradingUItoN5.html`): scope gate + NSS2 `[CERT-doc]`

**Applies only to custom `bajaui` (Java-based) Widgets.** The doc opens with an explicit scope gate: "If
you only have bajaux user interface code, you can skip this guide," then a decision tree — Px-only authors
stop reading; a `BWidget` subclass with no overridden paint/layout needs no changes; a subclass that
**does** override `paint`/`doLayout`/`computePreferredSize` must migrate to `IRenderContextAware`; a custom
Workbench theme must be fully rewritten in **NSS2**. `[CERT-doc]` (`upgrade/upgradingUItoN5.html`, "Make it
easy for me, please" section).

Core new API surface: `IStylable`/`IConfigurableStylable`/`IHasLayout`/`IPaintable` (styling contract),
`IStyle` (typed style constants — `COLOR`, `BORDER`, `PADDING`, `BACKGROUND_COLOR`, `MARGIN`,
`BORDER_RADIUS`, `FONT`), `IRenderContext` (the injected dependency — `cx.select(stylable, style)`),
`IRenderContextAware` (opt-in interface whose `doPaint`/`doLayout`/`doComputePreferredSize` replace the
old signatures), `BoxModel` (CSS-box-model-style margin/border/padding/background layout helper), and
`StylableAdapter`/`HasLayoutAdapter`/`PaintableImageAdapter` (style child "virtual" elements that aren't
real `BWidget`s). NSS2 replaces NSS1 (used N4/N3.7 era) with CSS-like selectors (tag `module|Type`, class
`.foo`, ID `#foo`, attribute `[attr=val]`, pseudoclass `:hover`), combinators (descendant, direct-child
`>`, nesting `&`), specificity rules (`!important` > self-style > non-inherited > ID > class > tag, with
declaration order as tiebreak), and directives (`:root { --var: ...}` / `var(--x)`, `.mixin()`, `@import`).
`[CERT-doc]` (`upgrade/upgradingUItoN5.html`, full body, ~51.6 KB text read this session).

**The private `com.tridium.ui.theme.Theme` class (`Theme.label().getTextFont()` etc.) is explicitly "Not
Supported"** in N5 — any code still using it must migrate to `IRenderContextAware` + `IRenderContext`
selects. `[CERT-doc]` (same file, §com.tridium.ui.theme.Theme: Not Supported).

## 10.7 — UI Changelog (`uiChangelog.html`): only the "Niagara 5.0" heading is N5-new `[CERT-doc]`

`doc/ui/uiChangelog.html` is a **cumulative** changelog going back to Niagara 4.10 (52,707 raw bytes, read
in full). Only the top `## Niagara 5.0` section is genuinely new in this release; everything under `##
Niagara 4.15` and older already shipped in N4 and is carried-over history, not a porting item. The N5.0
section's full content: (a) `baja.comm.Batch` removed from public API — explicit batching calls become
silent no-ops, **not** flagged breaking; (b) **breaking:** `baja.Complex#getFacets`→`getSlotFacets`
(BC-30); (c) **breaking:** `UxModel`/`BindingList` fully deleted from `bajaui` (BC-31, was deprecated-only
since 4.15); (d) **breaking:** `Array#contains` no longer polyfilled by BajaScript, use
`Array#includes` (BC-32). `[CERT-doc]` (`doc/ui/uiChangelog.html`, `## Niagara 5.0` heading, full text).

A reader who only skims the "4.15" heading immediately above risks misattributing an already-shipped N4
change (e.g. `BDefaultMobileWebProfile` removal, filed under `## Niagara 4.15 › Breaking changes`) as an
N5 item — this block deliberately separated the two headings to avoid that.

## 10.8 — Fox N4↔N5 interop: `BFoxProxySession` is USE-AT-YOUR-OWN-RISK across major versions `[CERT-doc]`

`doc/upgrade/usingFoxProxySession.html` (short, 3,745 raw bytes, read in full) is a single-topic warning:
Workbench itself is blocked from cross-major-version Fox connections (N5 Workbench cannot open an N4
station), but a module **programmatically** engaging `BFoxProxySession` (the public Fox API) between
stations of different major versions is not blocked by the framework and is officially
"**USE-AT-YOUR-OWN-RISK**" — it "could encounter unrecoverable problems or inconsistencies," and Tridium
recommends thorough integration testing if attempted. A new `getRemoteNiagaraVersion()` method on
`BFoxProxySession` lets a module programmatically check the remote station's Niagara (baja module)
version after connecting, so it can pre-emptively disengage if the versions are incompatible.
`[CERT-doc]` (`doc/upgrade/usingFoxProxySession.html`, full text).

None of our three modules (§10.10) construct a `BFoxProxySession` — this section is a forward-looking note
for any future PANCCADIA↔station bridging work, not a current porting item.

## 10.9 — `modules.html`: JPMS module descriptor, resource-root list, and permission annotations `[CERT-doc]`

`doc/modules.html` (23,540 raw bytes, read in full) is the general architecture doc for "Modules" (not
upgrade-specific), but its **Modularity** section is the fullest single treatment of the N5
`module-info.java` mechanics — it repeats and extends the `upgradingToN5.html` §Modularity content:

- **Module descriptor example** and the 9-directive table (`requires`, `requires transitive`,
  `requires static`, `exports`, `exports...to`, `opens`, `opens...to`, `uses`, `provides`) — identical to
  `upgradingToN5.html`'s copy.
- **Naming rules**: dots allowed, dashes not; project-style (`my.module`) or reverse-DNS; `niagara.*`/
  `com.tridium.*` prefixes reserved for the framework; avoid trailing numbers, uppercase, or embedded
  version numbers.
- **`@SuppressWarnings`** for incremental migration: `requires-automatic`, `requires-transitive-automatic`,
  `opens` (targets an empty/non-existent package) — new in this doc, **not** present in
  `upgradingToN5.html`.
- **Resource-root directories** — JPMS treats every directory as a potential package, so Niagara
  designates these top-level names as non-package resource roots regardless of module:
  `rc`, `WEB-INF`, `META-INF`, `LIB-INF`, `resources`, `res`, `maps`, `icons`, `images`, `stations`, `px`,
  `lib`, `doc`. Anything else holding only resources needs `@ModuleResources({...globs...})` (partial) or
  `@ModuleResourcesAll` (whole-module, used by theme/icon/doc modules with no `.java` at all) on the module
  descriptor, kept in sync with the jar's `CopySpec`.
- **`uberjar`/`unterjar`** — same content as BC-23.
- **`moduleConfiguration` spy** — a live Workbench view of loaded modules, their `ModuleLayer`, jar path
  (trimmed to `niagara_config_home`), and vendor/third-party version info — new diagnostic surface, not
  mentioned in `upgradingToN5.html`.

`[CERT-doc]` (`doc/modules.html`, full text, §§Modularity/Module Descriptor/Module Naming/Java Module
Directives/Annotations/Inspecting Loaded Modules).

## 10.10 — Our three N4 modules: structural census against the transition guide `[CERT]`

Read from `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249` (worktree at
commit `a109249`), `git log -1` this session.

| Module | `niagara-module.xml` `runtimeProfiles` | Module parts on disk | Part-combination needed? |
|---|---|---|---|
| CompPan | `"rt"` | `CompPan-rt/` only | **No** — single-part, §Module Part Combination is explicitly skippable |
| ColdRoomPan | `"rt"` | `ColdRoomPan-rt/` only | **No** — single-part |
| DashboardPan | `"rt,ux,wb"` | `DashboardPan-rt/`, `DashboardPan-ux/`, `DashboardPan-wb/` | **Yes** — 3 parts, levels rt(4)/ux(3)/wb(2) |

`[CERT]` (`niagara-module.xml` read verbatim for all three:
`Compresores/CompPan/niagara-module.xml`, `Dashboard/DashboardPan/niagara-module.xml`,
`Paccadia/ColdRoomPan/niagara-module.xml`, this session; directory listing under each module root).

DashboardPan is a **direct, load-bearing hit** against BC-20 (§10.4) and the exact procedure in §10.3
step 3 — it is the only one of the three that needs the merge; per the doc's own "If your module only has
one module part, you can skip this section," CompPan and ColdRoomPan skip Module Part Combination
entirely. This confirms and narrows the general observation [B4] §4.12 already made against the
`build-n4-module` skill's rt/ux/wb scaffold pattern — here it is a concrete, named module.

## 10.11 — Porting checklist: ColdRoomPan / CompPan / DashboardPan `[CERT]` + `[INFER]`

Each item cites the doc rule (§10.4 `BC-ID` or a doc section) and the exact file/line in our module it
hits. Items are ordered roughly per the §10.3 procedure.

**CHK-1 — Module Part Combination (DashboardPan only).** `Dashboard/DashboardPan/niagara-module.xml`
declares `runtimeProfiles="rt,ux,wb"` `[CERT]`. Per BC-20, merge `-ux`(3) and `-wb`(2) into `-rt`(4).
Concretely: fold `DashboardPan-ux/DashboardPan-ux.gradle.kts` and `DashboardPan-wb/DashboardPan-wb.gradle.kts`
dependency/plugin blocks into `DashboardPan-rt/DashboardPan-rt.gradle.kts`; move
`DashboardPan-ux/src/com/angeles/DashboardPan/ux/*.java` and `DashboardPan-wb/src/...` into
`DashboardPan-rt/src/...`; delete the two source folders; collapse `runtimeProfiles` to none.
`[CERT]` (`Dashboard/DashboardPan/niagara-module.xml:2`).

**CHK-2 — Intra-module dependency disappears.** `DashboardPan-ux/DashboardPan-ux.gradle.kts:53` has
`api(project(":DashboardPan-rt"))  // BDashboardService.appendAudit (audit-on-write)`. After CHK-1 this
line is deleted outright (not suffix-stripped) — per §10.3 step 3, "you don't need to copy over ... any
dependencies on this module's other module parts." `[CERT]`
(`Dashboard/DashboardPan/DashboardPan-ux/DashboardPan-ux.gradle.kts:53`).

**CHK-3 — Servlet API migration (DashboardPan-ux only).** Two files import raw `javax.servlet.http.*`
directly (not through a Niagara wrapper): `BDashboardServlet.java:20-21` (`HttpServletRequest`,
`HttpServletResponse`, used in `doGet`/`doPost`/`handleEquipment`/`handleSetpointWrite`/`handleAlarms`/
`serveStaticResource`/`send404`/`send405` — dozens of `HttpServletResponse.SC_*` call sites) and
`DashboardRbacHelper.java:6-7` (`checkCanWrite`, `SC_UNAUTHORIZED`/`SC_FORBIDDEN`). The gradle dependency
is `DashboardPan-ux.gradle.kts:54`: `compileOnly("javax.servlet:javax.servlet-api:3.1.0")`. Per BC-22,
both the import namespace and the gradle dependency artifact must move to `jakarta.servlet`/
`jakarta.servlet-api:6.1.0`; the guide states the API shape (constants, method names) is unchanged — this
is a namespace-only rename for these two files, no logic rewrite. No `jetty-web.xml` exists in this module
(`find` returned none), so the `Configure` class `ee11` fix is not applicable unless one is added later.
`[CERT]` (`BDashboardServlet.java:20-21,93-94,134-135,...`; `DashboardRbacHelper.java:6-7,33,41,56`;
`DashboardPan-ux.gradle.kts:54`).

**CHK-4 — Module-part-suffixed dependencies need stripping (regardless of CHK-1).** Even after the merge,
BC-20's §dependencies rule applies to *cross-module* dependencies, not just intra-module ones:
`DashboardPan-rt.gradle.kts:51-52` — `api(":alarm-rt")`, `api(":control-rt")` → `api(":alarm")`,
`api(":control")`; `DashboardPan-ux.gradle.kts:51-52` — `api(":alarm-rt")`, `api(":web-rt")` →
`api(":alarm")`, `api(":web")` (the `-ux`→`-rt` merge means the two `api(":alarm-rt")` lines also
de-duplicate into one). `[CERT]` (`DashboardPan-rt.gradle.kts:51-52`; `DashboardPan-ux.gradle.kts:51-52`).

**CHK-5 — Gradle plugin id renames (all 5 module-part gradle.kts files).** Every one of the 5 files read
this session (`CompPan-rt`, `DashboardPan-rt`, `DashboardPan-ux`, `DashboardPan-wb`, `ColdRoomPan-rt`)
declares the identical plugin block: `id("com.tridium.niagara-module")`, `id("com.tridium.niagara-signing")`,
`id("com.tridium.bajadoc")`, `id("com.tridium.niagara-jacoco")`,
`id("com.tridium.niagara-annotation-processors")`, `id("com.tridium.convention.niagara-home-repositories")`.
Per BC-25/BC-26, rename the first, second, fourth, and sixth per the mapping table (`n-module`, `sign`,
`jacoco`, `conv.n-repo`); `bajadoc` id is unchanged per [B4] §4.x/[B2]; remove
`niagara-annotation-processors` and add `n-helper-modularity`. `[CERT]` (all 5 `*.gradle.kts` files,
identical `plugins {}` block, lines 8-30 in each, this session).

**CHK-6 — `moduleManifest{}` simplification (all 5 files).** Every file has
`moduleManifest { moduleName.set("X"); runtimeProfile.set(rt|ux|wb) }` plus the top-of-file
`import com.tridium.gradle.plugins.module.util.ModulePart.RuntimeProfile.*`. Per §Module Transition Guide
§moduleManifest, delete the `runtimeProfile.set(...)` line and the `RuntimeProfile` import in all 5.
`[CERT]` (e.g. `DashboardPan-ux.gradle.kts:6,40`; `DashboardPan-rt.gradle.kts:6,40`).

**CHK-7 — `niagara-module.xml` `runtimeProfiles` attribute drop (all 3 modules).** Even CompPan and
ColdRoomPan — which skip Module Part Combination because they're already single-part — still carry
`runtimeProfiles="rt"` `[CERT]` and must drop the attribute entirely per §niagara-module.xml (N5's
manifest has no `runtimeProfiles` concept at all, confirmed independently by [B1] §1.3). `[CERT]`
(`Compresores/CompPan/niagara-module.xml:2`, `Paccadia/ColdRoomPan/niagara-module.xml:2`).

**CHK-8 — `module-permissions.xml` deletable, zero migration needed (all 3 modules).** CompPan-rt and
ColdRoomPan-rt ship the New-Module-Wizard scaffold with every `<req-permission>` commented out; DashboardPan-ux
carries an explicit `<permissions/>` (empty) with a comment stating the module needs none. None of the
three has a live permission request to translate into `@Grant*` annotations — per BC-21's "Delete your
module's `module-permissions.xml` file, if present," all three files can simply be deleted with no
annotation work. `[CERT]` (`CompPan-rt/module-permissions.xml`, `DashboardPan-ux/module-permissions.xml`,
`ColdRoomPan-rt/module-permissions.xml`, full contents read this session).

**CHK-9 — `module-include.xml` is auto-generated, delete-and-regenerate (all 3 modules).** 11
`@NiagaraType`-annotated classes exist across the three modules (`BCompressorControl`, `BDashboardService`,
`BRoomPanel`, `BDashboardServlet`, `BColdRoom`, `BEvaporatorUnit`, `BDefrostController`, `BStagingMode`,
`BDefrostMode`, `BFanMode`, and one more) `[CERT]`, and every `module-include.xml` carries the
Slot-o-matic/annotation-processor `<!--com.angeles.X-->` marker comment matching them 1:1. Per §Other
Module Parts, these can be deleted and will regenerate on next build — no hand-merge required even for
the DashboardPan CHK-1 merge. `[CERT]` (`grep -rc "@NiagaraType"` across all three trees, 11 files, 1 hit
each, this session; `module-include.xml` contents for `CompPan-rt`, `ColdRoomPan-rt`, `DashboardPan-ux`
read verbatim).

**CHK-10 — `javax.baja.*`→`niagara.*` rename scope (all 3 modules).** Import counts:
CompPan 1 file, DashboardPan 4 files, ColdRoomPan 6 files import `javax.baja.*` — a combined ~60 distinct
import lines spanning `javax.baja.sys`, `.nre.annotations`, `.status`, `.alarm`, `.collection`, `.web`,
`.naming`, `.units`. **None import `javax.baja.log`** — a `grep -rl "javax.baja.log"` across all three
trees returned zero files, and `BDashboardServlet.java` already uses `java.util.logging.{Level,Logger}`
directly — so BC-01 (Log→Logger) is **confirmed not applicable**, a genuine simplification versus the
general guide. `[CERT]` (`grep -rhn "^import javax.baja"` across the three trees, this session; zero-hit
`javax.baja.log` grep).

**CHK-11 — Several breaking-change rows confirmed absent from all three modules.** `grep`s this session
for BACnet (`bacnet`, case-insensitive), JSON-Java (`org.json`, `com.tridium.json`), Security-Manager
privileged calls (`AccessController`, `PrivilegedAction`), `new URL(String)`, `new Array()` (the nre
class), `equals()`-without-`hashCode()`, `isUnoperational`, and `getSubjectDN`/`getIssuerDN` all returned
**zero matches** across CompPan, DashboardPan, and ColdRoomPan. This means BC-10 (BACnet), BC-15 (JSON),
BC-21's privileged-action sub-item, and several of the doc's "Tips & Tricks" warning patterns are not
porting work for these three modules. `[CERT]` (absence, `grep -rl`/`grep -rln` over all three module
trees this session — not a compiler-verified guarantee, since a dynamically-constructed string or
reflection call would not show up in a text grep).

**CHK-12 — The entire bajaui/bajaux/NSS2 UI migration guide is not applicable (DashboardPan-ux).**
`DashboardPan-ux/src/rc/index.html` is the module's whole browser frontend — a standalone static HTML page
with vanilla JavaScript and `fetch()` calls (per its own routing doc-comment in
`DashboardDispatch.java:13`, "REST-POLL only... there is no BajaScript subscription or watchdog"), not a
`bajaux` Widget, not a Px view, and not a custom `BWidget` subclass. `grep`s for `getFacets(`,
`baja.comm.Batch`, `batchSaveMixin`/`batchLoadMixin`, and `require([` all returned zero hits in
`src/rc/`; the file's single `.contains(` hit at `index.html:1484` is DOM `classList.contains(...)`, not
the BajaScript `Array#contains` (BC-32). **Conclusion:** §10.6 (`upgradingUItoN5.html`, all 51.6 KB) and
§10.7's BC-30/BC-31/BC-32 rows are **not applicable to any of our three modules** — none has a custom
`bajaui` `BWidget`, a `bajaux` Widget, or a themed Px page. `[CERT]` (`find`/`grep` over
`DashboardPan-ux/src/rc`, this session — one file, `index.html`, plus `preview-mock.json`/
`preview-server.py` which are local dev-preview tooling outside the shipped jar).

**CHK-13 — Program-object signing (BC-29) not applicable.** `grep -rl "BProgram\|ProgramObject"` across
all three trees returned zero hits, and `module.palette` for ColdRoomPan (representative) declares only
plain `BComponent` types (`ColdRoom`, `EvaporatorUnit`, `DefrostController`) — none of the three modules
instantiates a `BProgramObject`/BajaScript Program, so the mandatory-signing requirement (§10.4 BC-29) has
no target in this codebase. `[CERT]` (`grep -rl` zero-hit, this session;
`Paccadia/ColdRoomPan/ColdRoomPan-rt/module.palette` read in full).

**CHK-14 — Fox interop (§10.8) is forward-looking, not current.** None of the three modules constructs a
`BFoxProxySession` — no import, no reference — so §10.8's USE-AT-YOUR-OWN-RISK warning is not a current
porting item for these modules, only a caution for any future station-to-station bridging work.
`[INFER]` (absence inferred from the same import-grep sweep as CHK-10/CHK-11, which would have surfaced a
`javax.baja.fox`/`niagara.fox` import had one existed; not separately re-grepped for `fox` specifically
this session — recorded as `[INFER]` rather than `[CERT]` per METHODOLOGY §3's negative-existence rule,
since the exact string `fox` was not independently grepped).

**CHK-15 — Priority ordering `[INFER]` (synthesis).** Given the checklist above, the practical N5-port
order for these three modules is: (1) CHK-5/CHK-6/CHK-7 (mechanical, all 5 files, no logic risk) →
(2) CHK-1/CHK-2/CHK-4 (DashboardPan's part-merge — the only structural risk) → (3) CHK-3 (servlet
namespace rename — mechanical but 2 files with many call sites) → (4) CHK-10 (`javax.baja`→`niagara`
global rename, all files) → (5) CHK-8/CHK-9 (delete-and-regenerate, near-zero risk) → skip CHK-11/CHK-12/
CHK-13/CHK-14 entirely (confirmed not applicable). `[INFER]` (synthesis from CHK-1..CHK-14, no independent
source states this ordering).

## 10.12 — Doc-vs-code conflicts: none found this session

No conflict surfaced between the shipped N5 doc's claims and the live N4 module code — every doc claim in
§10.4–§10.9 was corroborated (not contradicted) by the module census in §10.10–§10.11, and no prior
sibling block ([B1]–[B4]) statement about the module system was contradicted by this session's reading.
Per METHODOLOGY's "code wins for behaviour" rule, this section is empty-by-absence rather than
empty-by-omission: the checklist in §10.11 already privileges the *actual* module structure (e.g.
`niagara-module.xml`'s ground-truth `runtimeProfiles` value) over the doc's generic examples wherever the
two could have diverged.

## 10.x — Self-verification (METHODOLOGY §11)

**Token check.** Every `[CERT-doc]` citation in §10.2–§10.9 points to a zip-entry path inside
`docDeveloper.jar` (`doc/upgrade/upgradingToN5.html`, `doc/upgrade/upgradingUItoN5.html`,
`doc/upgrade/usingFoxProxySession.html`, `doc/upgradingJDK.html`, `doc/modules.html`,
`doc/ui/uiChangelog.html`) rather than a `file:line` inside this corpus — each was opened with
`ZipFile.read()` this session and its **full** text extracted and read (not sampled), matching the
convention [B4] §4.x established for jar-internal citations. All 6 files' full text is quoted or closely
paraphrased somewhere in §10.2–§10.9 above — spot-checked by re-`grep`ping 6 verbatim phrases
("Module Part Combination", "USE-AT-YOUR-OWN-RISK", "getSlotFacets", "unterjar",
"@GrantKeyStorePermission", "@ModuleResourcesAll") back against the extracted `/tmp/claude-1000/n5b10/*.txt`
files: all 6 resolved. Every `[CERT]` citation in §10.10–§10.11 is a `file:line` (or whole-file) reference
into the `main-a109249` worktree, each opened directly with `cat`/`grep -n`/`find` this session — 32
distinct file references, all target-resolvable in principle (external to this corpus's own directory, so
`verify-block.sh` will also report these as `extern`, same pattern as the doc citations).

**Marker tally — literal `toolbelt/verify-block.sh niagara5-block10.md .` output, run this session from
`/home/cristian/niagara5-research`:**

```
== verify-block: niagara5-block10.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1
   [CERT-live] 1
   [CERT] 27  (adj 25)
   [CERT-doc] 23  (adj 22)
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 9  (adj 7)
-- ratio -- [INFER]/[CERT*] = 7/51 = 0.14
-- [CERT] file:line citation resolution --
   synth-ref  [B1] [B2] [B3] [B4]  (block back-references — not file-verifiable)
   extern  (10 file:line citations — not in default target)
   resolved 0 of 12
   WARN    resolved 0 of 12 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```

The `[CERT-hw]`/`[CERT-live]`/`[CERT-web]`/`[CERT-a]` counts of 1 each are the script matching the **marker
legend line** in this block's own header blockquote (which names all 7 marker tokens for the reader), not
a real claim carrying that marker — this block makes zero `[CERT-hw]`/`[CERT-live]`/`[CERT-web]`/`[CERT-a]`
claims; the adjusted counts (25 `[CERT]`, 22 `[CERT-doc]`, 7 `[INFER]`) are the real per-claim tally.
Adjusted `[INFER]`/`[CERT*]` ratio = 7/(25+22) = **0.15** — low, consistent with a `mixed` block whose
evidence load is almost entirely direct reads (doc side, `[CERT-doc]`) or direct file/grep reads (code
side, `[CERT]`), with only §10.11 CHK-14/CHK-15 and the `Type: mixed` declaration reasoning crossing into
synthesis.

Re-running with `SOURCE_ROOT=/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`
(the module worktree, outside this corpus) resolves the 3 citations written in full relative-path form —
`ok Compresores/CompPan/niagara-module.xml:2`, `ok Dashboard/DashboardPan/DashboardPan-ux/DashboardPan-ux.gradle.kts:53`,
`ok Dashboard/DashboardPan/niagara-module.xml:2`, `ok Paccadia/ColdRoomPan/niagara-module.xml:2` (4 of 12,
one path cited twice) — while the remaining 8, cited by bare basename in the checklist prose
(`BDashboardServlet.java:20-21` etc.) stay `extern`, per METHODOLOGY §11's citation-form convention (a
bare-basename body citation is fine, but only a full `filename:line`/path self-verify anchor resolves).
**Declared per §11:** `verify-block: 4 of 12 file:line citations resolve with SOURCE_ROOT set to the
module worktree (0 of 12 without it, since that worktree sits outside this corpus); the doc-side
[CERT-doc] citations are zip-entry paths into an installed jar and are extern to the script by design,
same convention as [B4] §4.x; citation gate = inline read-verify — every cited doc file was opened in
full with ZipFile.read() and every cited module file was opened with cat/grep -n this session, not
recalled from memory or an earlier block.`

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block10.md`.
Per the task instruction, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated or edited
this session (read-only task scope, single-file deliverable).

**MCP-doc snapshots.** N/A — no MCP/context7 web citation was used this session; every doc citation is a
local jar zip-entry.

## 10.x — Named child gaps

- **B10-G1** — no live N5 Gradle build was actually run against any of our three modules this session
  (no N5 SDK/Gradle environment invoked); every checklist item in §10.11 is a **static, doc-derived**
  prediction, not a compiler-verified fact. Running `gradlew jar` against a post-migration ColdRoomPan (the
  smallest, single-part, dependency-light module) would validate or falsify CHK-5/CHK-6/CHK-7/CHK-10 cheaply.
- **B10-G2** — the "Niagara 5.0 Breaking Changes" doc that `upgradingToN5.html` itself cross-references
  ("A full list of breaking changes in 5.0 can be found at Niagara 5.0 Breaking Changes") was not located
  as a separate file in this `docDeveloper.jar` census — it may be an external web page rather than a
  shipped doc; confirm whether it exists inside the jar under a different path, or is genuinely
  web-only, and if the latter, whether §10.4's 32-row table is a strict subset of that fuller list.
- **B10-G3** — `usingFoxProxySession.html`'s new `getRemoteNiagaraVersion()` method on `BFoxProxySession`
  was not cross-checked against the `docSource.jar`/`niagaraJavadoc.jar` API surface [B4] §4.7/§4.8 to
  confirm its exact signature and package (`niagara.fox.BFoxProxySession` vs. a moved location per BC-14).
- **B10-G4** — CHK-14 (Fox interop not applicable) was inferred from the same general import-grep sweep as
  CHK-10/CHK-11, not from an independently re-run `grep -rli "fox"` across the three module trees —
  promote to `[CERT]` by running that grep.
- **B10-G5** — the `n5mig` station migration application (mentioned in `upgradingToN5.html` §n5mig and
  §New Requirement for Program Objects in Niagara 5) was not located or read as a separate artifact in
  this jar census — confirm whether it ships inside `docDeveloper.jar` at all, or only as a runtime tool
  in the N5 install's `bin/`.
- **B10-G6** — the DashboardPan-ux `preview-server.py`/`preview-mock.json` local dev-preview tooling
  (found alongside `src/rc/index.html`, §10.11 CHK-12) was not read — confirm it has no N5-relevant
  Python/JSON breaking-change surface of its own (unlikely, since it's local dev tooling outside the
  shipped jar, but unverified this session).

## 10.x — Connections

- **[B1]** — this block's BC-06 (`RuntimeProfile`/`BModule` methods removed) and CHK-7
  (`niagara-module.xml` `runtimeProfiles` attribute drop) directly confirm and operationalize [B1] §1.3's
  finding that N5's shipped `module.xml` schema has no `runtimeProfile` attribute at all.
- **[B2]** — BC-25 (plugin-id renames), BC-26 (annotation-processor split), BC-27 (Gradle/plugin version
  bump) are the same facts [B2] §2.2/§2.6/§2.8 already established from the Gradle plugin jar itself; this
  block corroborates them from the independent doc source and applies them to named files in our modules
  (CHK-5, CHK-6) rather than describing the plugin in the abstract.
- **[B3]** — BC-28 (directory layout) and BC-21 (Security Manager → `-javaagent`/ByteBuddy
  `PermissionManager`) directly corroborate [B3] §3.11 (directory layout) and §3.8 (what replaced
  `SecurityManager`) from the doc side; no conflict found (§10.12).
- **[B4]** — closes named child gap **B4-G8** (deep-read `upgradingUItoN5.html`, done in §10.6/§10.11
  CHK-12); corroborates [B4] §4.12's Module Part Combination summary with the full procedure (§10.3) and
  the full Breaking Changes list (§10.4, vs. [B4]'s topic-header-only keyword census in its §4.11); confirms
  [B4] §4.12's prediction that the `build-n4-module` skill's rt/ux/wb scaffold is a direct hit — here named
  concretely as DashboardPan (§10.10, CHK-1).
- **REMIT `build-n4-module` skill** (`.claude/skills/build-n4-module/`, referenced by user's global
  CLAUDE.md and [B2] §2.12/[B4] §4.12) — §10.11's checklist is the first session to apply the guide against
  real client modules built with that skill's scaffold; a future skill update for N5 targeting should
  encode CHK-1 through CHK-10 as its own default checklist rather than re-deriving them per module.
