# Block 2 — N5 module build toolchain: Kotlin Gradle plugins (`n-plugin`), JPMS `module-info.java`, an annotation-processor that now writes `module-include.xml`, and what the N4 build kit must change

> Research of **how a Niagara N5 (5.0.0.28 beta) module is built**, contrasted with the N4 toolchain
> (Java 8 + Gradle + Slotomatic — see §2.10 remittances). Covers: the Gradle plugin inventory shipped
> in the local Maven repo, the `build.gradle.kts`/`settings.gradle.kts`/`<module>.gradle.kts` DSL,
> `module.xml`/`module-include.xml` generation, the fate of Slotomatic, `module-info.java` (JPMS),
> the Java 25 toolchain requirement, signing, and the test framework. Does NOT cover: `@NiagaraType`
> runtime semantics beyond what the build docs state, native (`native`/`native-agg`/`npsdk-native`)
> module builds, or the node/yarn/grunt JS toolchain internals (flagged as a child gap, §2.11).
>
> Subject version: **Niagara 5.0.0.28 beta**, Gradle plugin artifacts at version `5.0.54.9.2`
> (settings-plugin family at `5.0.9.8.14`), bundled JRE `25.0.4`. Install root:
> `/mnt/c/Program Files/Niagara/5.0.0.28`; config/modules root:
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`.
>
> Sources:
> - `/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/**` — local Maven repo: every
>   `com.tridium.*` Gradle-plugin marker POM + the 4 implementation jars
>   (`n-plugin-5.0.54.9.2.jar`, `n-conv-plugin-5.0.54.9.2.jar`, `settings-5.0.9.8.14.jar`,
>   `java-utils-7.6.2.jar`) and `tridium-niagara-slotomatic-library-5.0.2.jar`.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/devkit.jar` — developer-kit templates
>   (`rc/gradle.properties.vm`, and its bundled `LIB-INF/n-templates-5.0.54.9.2.jar` — the New
>   Module/Driver Wizard's Velocity templates: `gradle/build.gradle.kts.vm`,
>   `gradle/settings.gradle.kts.vm`, `gradle/module/module.gradle.kts.vm`,
>   `gradle/module/module-info.java.vm`, `gradle/includes/niagara/modulePlugins.vm`,
>   `gradle/includes/niagara/moduleDependencies.vm`, `plugin-version.properties`).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` —
>   `doc/buildN5.html` (the official "Building Niagara" guide) and `doc/security/codeSigning.html`.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` — checked for
>   `module-info.class` presence and `@NiagaraType`-family annotation classes.
> - `/mnt/c/Program Files/Niagara/5.0.0.28/jre/release` — bundled JRE identity.
> - `/mnt/c/Program Files/Niagara/5.0.0.28/lib/tridium-niagara-baja-doclet-5.0.4.jar` — the Bajadoc
>   doclet.
> - N4 remittances (READ, not re-derived — cited `REMIT`): `niagara-research` B12, B631, B434, B711,
>   B637, BTI.
>
> Method: `unzip`/`python3 zipfile` inventory of every jar; `javap` (JDK 26 from
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26`) on individual `.class` files for byte-level confirmation;
> Vineflower (`vineflower.jar`, same JDK) full-jar decompilation of `n-plugin-5.0.54.9.2.jar` into
> `/tmp/claude-1000/n5b2/vf-out/` for the Kotlin-plugin source reconstruction. Direct `Read`/`grep` on
> the extracted devkit templates and the HTML-stripped `docDeveloper` guide. Markers (METHODOLOGY §3):
> `[CERT]` local primary source (`file:line` or `zip-entry:path`) · `[CERT-doc]` official installed
> HTML doc, full basename · `[INFER]` deduction · `REMIT` = cited from a prior corpus block, not
> re-opened this session (methodology has no dedicated marker for this; treated as context, not a
> `[CERT-*]` claim of this block).
>
> N5 build-toolchain layer. First block in this corpus's public numbering (no Block 1 exists in this
> tree yet — the corpus was bootstrapped but empty; this document is `niagara5-block2.md` per explicit
> task numbering).
>
> **Type:** mixed — most sections are direct evidence (`[CERT]`/`[CERT-doc]`) from this session's own
> reads; §2.10 is a synthesis comparison against `[Block]`-external N4 corpus material, cited `REMIT`.
>
> **Breakthrough:** the official `buildN5.html` guide states, in its own words, that in N5 "the type
> elements [of `module-include.xml`] are generated and updated automatically by the annotation
> processor during compilation" — this is the single mechanism-level answer the gap asked for: N4's
> Slotomatic-reads-module-include.xml-as-input model (REMIT B631) is joined in N5 by a real JSR-269
> annotation processor that WRITES it, while Slotomatic itself survives unchanged as a separate task
> for the in-class slot code (see §2.6/§2.7 for the exact division of labor and its residual `[INFER]`).

---

## 2.1 — Plugin inventory: one fat Kotlin jar behind ~30 plugin ids `[CERT]`

The local Maven repo (`etc/m2/repository`) holds **27 `com.tridium.*` Gradle-plugin marker
artifacts** at version `5.0.54.9.2` (2 more — `jcw`, `pmd` — and the `set.*` family sit at
`5.0.9.8.14`), plus `com.tridium.tools:xelem:4.0.3` (a plain library, not a plugin marker).
`[CERT]` (directory listing, `etc/m2/repository/com/tridium/**`)

Every plugin-marker POM (`com.tridium.<id>.gradle.plugin-5.0.54.9.2.pom`) is a thin `packaging=pom`
artifact whose sole dependency is one of 4 real implementation jars — confirmed by reading the POMs
directly, e.g.:

```xml
<groupId>com.tridium.n-module</groupId>
<artifactId>com.tridium.n-module.gradle.plugin</artifactId>
<dependencies><dependency>
  <groupId>com.tridium.tools</groupId><artifactId>n-plugin</artifactId><version>5.0.54.9.2</version>
</dependency></dependencies>
```
`[CERT]` (`com/tridium/n-module/com.tridium.n-module.gradle.plugin/5.0.54.9.2/….pom`)

`n-plugin-5.0.54.9.2.jar` (sha256 `eb9831b6…d93356`) alone implements **27 of the 30 plugin ids**
via `META-INF/gradle-plugins/*.properties` — one file per id, each an
`implementation-class=com.tridium.gradle.plugins.….<Name>Plugin` line:

| Plugin id | Implementation class | Role (from name/decompiled `apply()`) |
|---|---|---|
| `com.tridium.n-module` | `module.NiagaraModulePlugin` | the module plugin: `moduleManifest{}`, `jar`/`moduleTestJar`, slotomatic tasks |
| `com.tridium.n-helper-module` | `module.NiagaraModuleWithExtLibsPlugin` | helper variant for modules bundling external libs |
| `com.tridium.n-helper-modularity` | `module.NiagaraModularityPlugin` | resolves transitive deps for modules with embedded jars |
| `com.tridium.nap` | `module.NiagaraAnnotationProcessorsPlugin` | wires `niagaraAnnotationProcessor` config + `-A` compiler args |
| `com.tridium.n-java` | `java.NiagaraJavaPlugin` | registers `compact3`/`limitModules`/`apt`/`modulePath` `CommandLineArgumentProvider`s on every `JavaCompile` |
| `com.tridium.niagara` | `niagara.NiagaraPlugin` | root-project base plugin |
| `com.tridium.rpni` | `niagara.RootProjectNiagaraPlugin` | root-only Niagara environment service |
| `com.tridium.set.niagara` | `niagara.SettingsNiagaraPlugin` | settings-time Niagara wiring |
| `com.tridium.vendor` | `vendor.VendorPlugin` | `vendor{}` extension: `defaultGroup/defaultVendor/defaultModuleVersion/defaultDistVersion` |
| `com.tridium.sign` | `signing.SigningPlugin` | per-module `niagaraSigning{}` |
| `com.tridium.rps` | `signing.RootProjectSigningPlugin` | root-only signing-profile factory |
| `com.tridium.signed-jar` | `signing.SignedJarPlugin` | generic signed-jar archive task |
| `com.tridium.bajadoc` | `bajadoc.BajadocPlugin` | per-module `bajadoc` task (`includePackage(...)`) |
| `com.tridium.bajadoc-module` | `doc.BajadocModulePlugin` | aggregates bajadoc across a doc module's dependents |
| `com.tridium.niagara-doc` | `doc.NiagaraDocPlugin` | doc-module `docCopy`/index tasks |
| `com.tridium.base-doc` | `doc.BaseDocPlugin` | shared doc-module base config |
| `com.tridium.jacoco` | `jacoco.NiagaraJacocoPlugin` | JaCoCo coverage on the `niagaraTest` task |
| `com.tridium.native` | `natives.NiagaraNativePlugin` | per-module native-code build |
| `com.tridium.native-agg` | `natives.NativeAggregationPlugin` | aggregates native artifacts |
| `com.tridium.rpna` | `natives.RootProjectNiagaraNativePlugin` | root-only native env |
| `com.tridium.npsdk-native` | `natives.NpsdkNativePlugin` | NPSDK native build |
| `com.tridium.node` | `node.NodePlugin` | per-module Node.js toolchain |
| `com.tridium.rpno` | `node.RootProjectNodePlugin` | root-only Node env |
| `com.tridium.yarn-ws` | `node.YarnWorkspacePlugin` | Yarn workspace member |
| `com.tridium.yarn-ws-agg` | `node.YarnWorkspaceAggregationPlugin` | Yarn workspace aggregator |
| `com.tridium.grunt` | `grunt.GruntPlugin` | Grunt JS build tasks (`gruntBuild`) |
| `com.tridium.uat` | `artifacts.UnpackingArtifactTransformPlugin` | Gradle artifact-transform helper |

`[CERT]` (`META-INF/gradle-plugins/*.properties` inside `n-plugin-5.0.54.9.2.jar`, all 27 files read)

The remaining 3 plugin families live in **2 sibling jars**:

- `n-conv-plugin-5.0.54.9.2.jar` → `com.tridium.conv.{n-module, n-build, n-repo, set.niagara}`, all
  under package `com.tridium.gradle.plugins.niagara.convention.*` — **these are Gradle "convention
  plugins" in the ordinary Gradle sense** (`NiagaraModuleConventionPlugin`,
  `NiagaraGradleProjectConventionPlugin`, `NiagaraHomeRepositoriesPlugin`,
  `SettingsConventionPlugin`) — NOT an AX→N4-style migration/conversion tool despite the `conv`
  abbreviation reading that way at a glance. `[CERT]`
  (`META-INF/gradle-plugins/com.tridium.conv.*.properties` inside `n-conv-plugin-5.0.54.9.2.jar`)
- `settings-5.0.9.8.14.jar` → `com.tridium.{set.mpr, set.lsc, jcw, pmd}` under
  `com.tridium.gradle.plugins.settings.*` — `MultiProjectPlugin` (subproject auto-discovery, §2.3),
  `LocalSettingsConventionPlugin`, `JavaCompilerWarningsPlugin`, `ProjectMetadataPlugin`. `[CERT]`
  (`META-INF/gradle-plugins/*.properties` inside `settings-5.0.9.8.14.jar`)

`tridium-niagara-slotomatic-library-5.0.2.jar` ships as its own Maven artifact (separate from
`n-plugin`) — Slotomatic is a **library dependency of `n-plugin`**, not baked into it. `[CERT]`
(artifact listing, `com/tridium/tools/tridium-niagara-slotomatic-library/5.0.2/`)

**Decompiled-tree citation note (methodology §11):** all `[CERT]` citations into
`/tmp/claude-1000/n5b2/vf-out/**` (Vineflower output of `n-plugin-5.0.54.9.2.jar`, sha256
`eb9831b6…d93356`) resolve to `extern` under any mechanical citation checker — the tree lives outside
this corpus. Every such citation was inline-token-verified by reading the named `.java`/`.kt` file
directly in this session (all files quoted in §2.2–§2.9 were read in full or in the shown range).

## 2.2 — Official old→new plugin-id renames `[CERT-doc]`

`buildN5.html` gives an explicit rename table for anyone porting an N4 build (quoted verbatim,
3 groups):

| Old id (N4) | New id (N5) |
|---|---|
| `com.tridium.settings.multi-project` | `com.tridium.set.mpr` |
| `com.tridium.settings.local-settings-convention` | `com.tridium.set.lsc` |
| `com.tridium.settings.niagara` | `com.tridium.set.niagara` |
| `com.tridium.niagara-module` | `com.tridium.n-module` |
| `com.tridium.niagara-signing` | `com.tridium.sign` |
| `com.tridium.niagara-grunt` | `com.tridium.grunt` |
| `com.tridium.niagara-native` | `com.tridium.native` |
| `com.tridium.niagara-jacoco` | `com.tridium.jacoco` |
| `com.tridium.niagara-annotation-processors` | `com.tridium.nap` |
| `com.tridium.niagara-java` | `com.tridium.n-java` |
| `com.tridium.convention.niagara-home-repositories` | `com.tridium.conv.n-repo` |
| `com.tridium.convention.settings.niagara` | `com.tridium.conv.set.niagara` |
| `com.tridium.convention.niagara-module` | `com.tridium.conv.n-module` |
| `com.tridium.convention.niagara-build` | `com.tridium.conv.n-build` |
| `com.tridium.yarn-workspace` | `com.tridium.yarn-ws` |
| `com.tridium.yarn-workspace-aggregation` | `com.tridium.yarn-ws-agg` |

`[CERT-doc]` `doc/buildN5.html` ("Niagara 5 Plugin ID Updates" section, 4 sub-tables) — every id in
this table was cross-checked against §2.1's own live inventory of `META-INF/gradle-plugins/*` and
matches exactly (both a doc claim and an independently-read artifact fact).

## 2.3 — Root project DSL: `vendor{}` survives near-verbatim; module discovery is now automatic `[CERT]`

Root `build.gradle.kts` (wizard template, `gradle/build.gradle.kts.vm` inside devkit's
`n-templates` jar):

```kotlin
plugins {
  id("com.tridium.niagara")
  id("com.tridium.vendor")
  id("com.tridium.sign")
  id("com.tridium.conv.n-repo")
}

vendor {
  defaultVendor("$vendor")
  defaultModuleVersion("$version")
}

subprojects { repositories { mavenCentral(); mavenLocal() } }
```

`defaultModuleVersion(version: String)` — decompiled from `VendorExtension.kt` — is implemented as:
for every subproject that applies `com.tridium.n-module`, configure its `moduleManifest` extension
(`ModuleXml`) and call `.getVendorVersion().set(version)`; `defaultVendor` likewise sets
`ModuleXml.getVendor().convention(vendor)` (and the parallel `DistXml` for `com.tridium.dist`).
`[CERT]` (`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/vendor/VendorExtension.kt`, whole
file, `defaultVendor`/`defaultModuleVersion` methods) — **this is the exact root-level call already
in the client's N4 `build.gradle.kts` files** (REMIT `client-module-version-key-location` memory:
`defaultModuleVersion("X.Y.Z")` in each GROUP `build.gradle.kts`) — the N5 signature and semantics are
unchanged; only the surrounding `plugins{}` ids move (§2.2).

`settings.gradle.kts` (wizard template) replaces N4's manual `include(":moduleA", ":moduleB", …)`
with automatic subproject discovery:

```kotlin
configure<MultiProjectExtension> { findProjects() }
```

`findProjects()` (no-arg) walks the root directory for any of 4 recognized build-script naming
conventions (`<name>/<name>.gradle.kts`, `<name>/<name>.gradle`, `<name>/build.gradle.kts`,
`<name>/build.gradle`) and includes every match; `findProjects("folder1", …)` scopes the walk to
named subfolders. `[CERT-doc]` `doc/buildN5.html` ("Note: If you have specific subfolder(s)…") +
`[CERT]` `gradle/settings.gradle.kts.vm` (`MultiProjectExtension`/`LocalSettingsExtension` imports
and calls, whole file read). `pluginManagement{}` in the same file pins every plugin version from
2 properties (`gradlePluginVersion=5.0.54.9.2`, `settingsPluginVersion=5.0.9.8.14` —
`[CERT]` `plugin-version.properties`), resolved from `file:///<gradlePluginHome>` (defaulting to
`<niagara_home>/etc/m2/repository`) plus `gradlePluginPortal()`. `[CERT]` `gradle/includes/niagara/settingsRepoUrl.txt` + `settingsRepos.txt` (whole files read).

## 2.4 — Per-module DSL: `moduleManifest{}` is the renamed extension; `schemaVersion="5"` in the manifest `[CERT]`

Per-module `<moduleName>.gradle.kts` (wizard template, abridged):

```kotlin
plugins {
  id("com.tridium.n-module")
  id("com.tridium.n-helper-modularity")
  id("com.tridium.sign")
  id("com.tridium.bajadoc")
  id("com.tridium.jacoco")
  id("com.tridium.nap")
  id("com.tridium.conv.n-repo")
}

moduleManifest {
  moduleName.set("$moduleName")
  ignoreRuntimeProfileCheck.set("true")   // present verbatim in the wizard's own conversion template
  checkModuleName.set(false)
}
```
`[CERT]` `gradle/module/module.gradle.kts.vm` + `gradle/includes/niagara/modulePlugins.vm` (whole
files read).

`moduleManifest` is a Gradle extension of type `ModuleXml` (`com.tridium.gradle.plugins.module.util.ModuleXml`),
registered by `NiagaraModulePlugin.registerModuleTasks()` via
`extensions.create("moduleManifest", ModuleXml::class, …)`. `[CERT]`
(`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/NiagaraModulePlugin.kt`, `registerModuleTasks`,
the `var60 = var59.register("writeModuleXml", WriteModuleXml::class, …)` block and the preceding
`extensions.create("moduleManifest", ModuleXml::class, …)` call — both read directly in this session).
The task `writeModuleXml` serializes it to `build/manifest/writeModuleXml/module.xml`, later copied
into the jar's `META-INF/module.xml`.

Full `ModuleXml` DSL surface (constructor defaults + `@Input` getters, `ModuleXml.java` decompiled
whole-class read):

| Attribute/property | Default | Notes |
|---|---|---|
| `name` | Gradle project name | |
| `moduleName` | project name (convention) | written as both `moduleName` and legacy `name` XML attrs |
| `bajaVersion` | `"0"` | |
| `vendor` | `project.group` | overridable by `vendor{}` root DSL |
| `vendorVersion` | `project.version` | overridable by `vendor{}` root DSL |
| `description` | project description or `""` | |
| `preferredSymbol` | `name` (convention) | written to `module.xml` as `preferredSymbol` attr |
| `nre` | `true` | |
| `autoload` | `true` | |
| `installable` | `true` | |
| `dependsOnBaja` | `true` | auto-adds a `Tridium:baja:4.0` dependency unless the module IS baja |
| `isTestModule` | `false` | |
| `ignoreRuntimeProfileCheck` | from `-PignoreRuntimeProfileCheck` gradle property | bypasses an (unlocated in this session) rt/ux/wb naming-suffix check — see §2.10 open item |
| `forceBackwardsDependency` | from gradle property | allows an out-of-order dependency version override |
| `strictValidation` | `false` | throw vs. warn on manifest problems |
| `checkModuleName` | `true` | |
| `excludedDependencyModules` | `{activation, jettyWrapper, niagarad, nre, npsdkTest, nacl, splash}` | modules never auto-added as manifest deps |
| `dependencyVersionLimit` | `2` | version-segment strip depth for computed dependency versions |
| `dependencies{}` / `installation{}` / `defines{}` / `lexicons{}` | — | nested blocks, each maps to a `module.xml` child element |

The generated root XML element is literally `root.setAttr("schemaVersion", "5")` — **N5 module
manifests carry a `schemaVersion="5"` attribute that N4 manifests did not have** (REMIT B12/B434
describe N4 `module.xml` without this attribute). `[CERT]`
(`ModuleXml.java`, `toElementInternal()`, whole method read: `root.setAttr("schemaVersion", "5")`
literal at the line building the `<module>` root element, alongside `name`, `bajaVersion`, `vendor`,
`vendorVersion`, `description`, `preferredSymbol`, `nre`, `autoload`, `installable`, `buildMillis`,
`buildHost`, `moduleName`).

Dependency configurations (official table, `buildN5.html`, cross-checked against `moduleDependencies.vm`):

| Configuration | Use |
|---|---|
| `api(":x")` / `api(project(":x"))` | Niagara-module dependency (own build or installed) |
| `nre("group:artifact")` | compile against a jar already under `!bin/ext`, not bundled |
| `niagaraAnnotationProcessor(":niagaraAnnotationProcessors")` | the JSR-269 processor (§2.6), now a separate dependency from `nre` |
| `unterjar("group:artifact:version")` | embed a third-party jar whole under `LIB-INF/`, preserving its JPMS module identity for `module-info.java requires` |
| `uberjar("group:artifact:version")` | explode a third-party jar's classes into the module jar (private, non-exported) |
| `compileOnly` | compile-time-only stub |
| `moduleTestImplementation` / `testNre` / `testUberjar` / `testUnterjar` | test-scope mirrors of the above |

`[CERT-doc]` `doc/buildN5.html` ("Dependency Configurations" table) + `[CERT]`
`gradle/includes/niagara/moduleDependencies.vm` (same configuration names in the Velocity template,
whole file read).

## 2.5 — Slotomatic: same tool, same package, now exposed as a Kotlin `Slotomatic` task type `[CERT]`

> **Correction (added by [Block 121], §121.7, §14 cross-block).** The heading is wrong about the language of the task type: `Slotomatic`, `SlotomaticTask` and
> `MigrateSlotomaticTask` are **Java** classes (no `kotlin/Metadata` on any of the three, `evidence/b121/claim-audit.tsv`); only the registering plugin
> `NiagaraModulePlugin` is Kotlin. The body's own citation (`Slotomatic.java`) and [Block 74] §74.1 already say so. The delegation to `com.tridium.slottool.Slotomatic` below is unaffected.

The Gradle task class `com.tridium.gradle.plugins.module.task.Slotomatic` (registered by
`NiagaraModulePlugin.registerSlotomaticTasks()`, task name `slotomatic`, invoked as
`gradlew :<moduleName>:slotomatic`) delegates to **`com.tridium.slottool.Slotomatic`** — the identical
fully-qualified class name REMIT-identified in N4 (`niagara-research` B434 §434, decompiled
`slottool/Slotomatic.java`; B12 §12.1.8; B637 §637.2). `[CERT]`
(`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/task/Slotomatic.java`, whole file:

```java
com.tridium.slottool.Slotomatic.builder()
   .withModulePath(...).withPaths(includedFiles).withInputCharset(...)
   .withJavaLanguageLevel(...).withGeneratedAnnotationClass(...)
   .force(...).strictAnnotationMode(...).failOnInvalidFile(...)
   .sortImports(...).preserveDate(...).migrate(...)
   .compile().runSlotomatic();
```
) — the invocation is now a fluent builder (`Slotomatic.builder()…compile().runSlotomatic()`) rather
than N4's constructor/method-call shape (REMIT B12 §12.1.8's `gradlew slotomatic` CLI description),
but the underlying class and its role (writing generated code) are the same tool, confirmed present
as its own Maven artifact `tridium-niagara-slotomatic-library-5.0.2.jar` (§2.1). A companion
`MigrateSlotomaticTask` and a `--migrate` CLI option on the `Slotomatic` task
(`@Option(option = "migrate", description = "Migrate before reslotting")`) directly continue N4's
`gradlew slotomatic -Dslotomatic.migrateBeforeRecompile` AX-slot-XML migration path (REMIT B12
line 169). `[CERT]` (`Slotomatic.java`, `getMigrate()`/`@Option` annotation, same file).

## 2.6 — `module-include.xml`/`moduleTest-include.xml`: now WRITTEN by a JSR-269 annotation processor, not just read `[CERT-doc]`

This is the central mechanism change from N4. `buildN5.html`, verbatim:

> "The type elements are generated and updated automatically by the annotation processor during
> compilation - any type annotated with `@NiagaraType` will be written to `module-include.xml`
> automatically."

and, for the test-side twin:

> "As with the main `module-include.xml`, elements for any correctly annotated test type will be
> added automatically. This file is auto-generated and maintained during the `gradlew jar` build
> process; and it is no longer necessary to maintain manually."

`[CERT-doc]` `doc/buildN5.html` ("module-include.xml" and "moduleTest-include.xml" subsections).

This directly supersedes the N4 finding (REMIT B12 §12.1.8, corrected by B631 §631.1-2): in N4, no
`javax.annotation.processing.Processor` existed in the decompiled corpus, and `module-include.xml`
was read as INPUT by Slotomatic, with `<type>` entries populated by the wizard or by hand. N5 keeps
that read-as-input path for Slotomatic's OWN in-class code generation (§2.5) but adds a genuine
annotation processor that owns the type-list file. The processor is wired through the
`com.tridium.nap` plugin (`NiagaraAnnotationProcessorsPlugin`), which:

- creates a `niagaraAnnotationProcessor` Gradle configuration that the standard `annotationProcessor`
  and `moduleTestAnnotationProcessor` configurations `extendsFrom` — confirmed both in the decompiled
  plugin (`ConfigurationContainerScope`/`niagaraAnnotationProcessor` configuration wiring, class dump
  `NiagaraAnnotationProcessorsPlugin$apply$1$1$1$niagaraAnnotationProcessor$2$1`) and in the official
  doc's own comment on the plugin: "The Annotation processors plugin adds default dependencies on
  `:nre` for the `annotationProcessor` and `moduleTestAnnotationProcessor` configurations by creating
  a single `niagaraAnnotationProcessor` configuration they extend from." `[CERT]`
  (`NiagaraAnnotationProcessorsPlugin.kt`, `apply()`, whole file read) + `[CERT-doc]`
  (`gradle/includes/niagara/modulePlugins.vm` inline comment, and `doc/buildN5.html` "Niagara
  annotation processors" section).
- registers 2 `-A` processor arguments on every `JavaCompile` task —
  `-Aniagara.module.root=<project dir>` and `-Aniagara.test.roots=src/moduleTest/java=java` (Maven
  layout) or `srcTest=java` (legacy layout) — via a `CommandLineArgumentProvider`
  (`AnnotationProcessorArgumentProvider`). `[CERT]` (`NiagaraAnnotationProcessorsPlugin.kt`,
  `execute$lambda$0`, whole method read).
- the actual processor DEPENDENCY is `:niagaraAnnotationProcessors` — the doc's own migration
  instructions state it plainly: "the `niagaraAnnotationProcessors` has now been split from the `nre`
  module, so we need to add a dependency on it in addition to `nre`":
  ```kotlin
  dependencies {
    nre(":niagaraAnnotationProcessors")
    nre(":nre")
    niagaraAnnotationProcessor(":niagaraAnnotationProcessors")
  }
  ```
  `[CERT-doc]` `doc/buildN5.html` ("Niagara annotation processors" section, code block read verbatim).

**Residual `[INFER]`, named as child gap B2-G1**: this session could not locate the processor's own
class (no `META-INF/services/javax.annotation.processing.Processor`, no `NiagaraProperty`/`NiagaraType`
-named class, found inside `baja.jar` by name search — §2.9) because the `niagaraAnnotationProcessors`
Niagara module itself was not present in this beta's minimal `modules/` config directory (only 247
modules installed, none named `niagaraAnnotationProcessors` — `[CERT]`, directory listing of
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules`). The doc's own claim about WHAT the
processor does is `[CERT-doc]`; the processor's own implementation is unread. Division of labor
between Slotomatic (in-class getter/setter/slot-constant code — REMIT B12/B434 for the N4 mechanic,
not re-verified against an N5-built `.java` in this session) and the new AP (module-include.xml only)
is stated by the doc for the AP half and inferred by continuity for the Slotomatic half — `[INFER]`.
Closing this needs either the `niagaraAnnotationProcessors` module jar or a live N5 station/build.

## 2.7 — `module-info.java`: real JPMS, one per module subproject, wizard-generated `[CERT-doc]` + `[CERT]`

> "Niagara 5 modules are Java Platform Module System (JPMS) modules. Each module subproject must have
> a `src/module-info.java` declaring the module name and the Niagara modules it requires. The New
> Module Wizard generates this file for you based on the dependencies you select."

`[CERT-doc]` `doc/buildN5.html` ("module-info.java" subsection). Minimal shape (doc's own example):

```java
module yourCompany.myModule {
  requires niagara.nre;
  requires transitive niagara.baja;
  requires niagara.niagaraAnnotationProcessors;
  requires niagara.driver;
  // exports yourCompany.myModule;
}
```

Module-naming rule stated by the doc: name is `<vendor>.<moduleName>` lower-cased; every Niagara
dependency declared in `<moduleName>.gradle.kts` (`api(":x")`, `nre(":x")`,
`niagaraAnnotationProcessor(":x")`) needs a matching `requires niagara.x;`, auto-generated by the
wizard; no package is exported by default (`exports` must be added explicitly). The wizard's own
Velocity template for this file:

```
module ${vendor}.${projectName} {
  #foreach ( $require in $requires )
    #if ($require == "baja")
  requires transitive niagara.${require};
    #else
  requires niagara.${require};
    #end
  #end
}
```
`[CERT]` `gradle/module/module-info.java.vm` (whole file read) — confirms the `requires transitive
niagara.baja` special-case is baked into the generator, not just doc prose.

**Build-side plumbing that only makes sense for real JPMS**, found independently in the decompiled
plugin (not doc-stated, so kept as a separate `[CERT]`):
- `JavaCompile.options.javaModuleVersion` is set to the module's `vendorVersion` on every
  `JavaCompile` task, inside `NiagaraModulePlugin.registerModuleTasks()`. `[CERT]`
  (`NiagaraModulePlugin.kt`, the `var73.configureEach { … getJavaModuleVersion().set(manifestExtension.getVendorVersion()…) }` block, read directly).
- `com.tridium.n-java` (`NiagaraJavaPlugin`) registers 4 `CommandLineArgumentProvider`s on every
  `JavaCompile`: `compact3` (`Compact3ArgumentProvider`), `limitModules`
  (`LimitModulesArgumentProvider`), `apt` (`AnnotationProcessorArgumentProvider`, §2.6), and
  `modulePath` (`ModulePathArgumentProvider`, seeded from the Niagara-home/niagara-config-home
  environment service). `[CERT]` (`NiagaraJavaPlugin.kt`, whole `apply()` method read). The
  `Compact3ArgumentProvider` name is a direct callback to the old JRE "compact3" profile concept —
  `[INFER]` that this exists to keep module classfiles usable on constrained embedded JVMs (e.g. a
  JACE), unconfirmed against an actual javac argument value in this session (child gap B2-G2).
- `unterjar` vs `uberjar` is explicitly a JPMS accommodation: `unterjar` preserves a third-party jar's
  own JPMS module name intact under `LIB-INF/` so a dependent module's `module-info.java` can
  `requires` it directly; `uberjar` explodes classes into a private, non-exportable classloader.
  `[CERT-doc]` `doc/buildN5.html` ("External Dependencies"/"When to Use uberjar Instead" sections).

`baja.jar` itself ships a real `module-info.class` (confirmed by zip-entry listing) — `[CERT]`
(`python3 zipfile` listing of `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar`,
entry `module-info.class` present) — so the JPMS-ification is not limited to third-party/vendor
modules; Tridium's own `baja` module is a named JPMS module too.

## 2.8 — Java toolchain: bundled JRE 25.0.4, Java 25 mandatory `[CERT]` + `[CERT-doc]`

The installed JRE's own `release` file: `JAVA_VERSION="25.0.4"`. `[CERT]`
(`/mnt/c/Program Files/Niagara/5.0.0.28/jre/release`, line read verbatim). The devkit's own
`gradle.properties.vm` template states the requirement in prose: "This example _requires_ a full JDK
… If that list includes a valid Java 25 JDK, you can leave the following three properties commented
out … If it does not, you can set … the full path to a Java 25 JDK." `[CERT]`
(`devkit.jar!rc/gradle.properties.vm`, whole file read). `buildN5.html` repeats this as the very
first line of "Getting started": "In order to build Niagara modules, you need a valid Java 25 JDK
with JavaFx." `[CERT-doc]` `doc/buildN5.html`. IDE integration changed too: `gradlew idea` and
`gradlew eclipse` are explicitly REMOVED in N5 ("these are now removed and will not work" —
`[CERT-doc]`, same doc); IDE import is now via opening `build.gradle.kts` directly in IntelliJ/Eclipse.

Toolchain resolution is standard Gradle auto-detection
(`gradlew -q javaToolchains -Porg.gradle.java.installations.auto-detect=true`) with 3 override
properties (`org.gradle.java.installations.{auto-detect,auto-download,paths}`) settable in
`gradle.properties`. `[CERT-doc]` `doc/buildN5.html` ("Configuring Gradle's JDK").

3 new/changed Gradle path properties are required in every project's `gradle.properties`
(`niagara_home`, `niagara_user_home`, `niagara_config_home`) — `niagara_config_home` is **new in N5**
and `niagara_home` is now explicitly **read-only** in N5 (both facts stated directly by the doc, not
inferred): "niagara_config_home … Introduced in Niagara 5 with niagara_home being read-only."
`[CERT-doc]` `doc/buildN5.html` ("Gradle Properties for Niagara Paths" table).

## 2.9 — Signing and testing: both carried over from N4 with light renaming `[CERT-doc]`

**Signing.** `com.tridium.sign` (`SigningPlugin`) provides a per-module `niagaraSigning{}` extension
(`aliases`, `signingProfileFile`); `com.tridium.rps` (`RootProjectSigningPlugin`) is the root-only
signing-profile factory (`signingServices { signingProfileFactory { allowDefaultProfile.set(false) } }`).
Default behavior — auto-generated self-signed certificate stored in
`USER_HOME/.tridium/security/niagara.signing.{jks,xml}`, `JCEKS` keystore, `createProfile` and
`generateCertificate` Gradle tasks to mint a real org-specific profile — is stated by
`codeSigning.html` to date from N4 4.6, i.e. **unchanged mechanism, carried forward into N5**.
`[CERT-doc]` `doc/security/codeSigning.html` (whole doc read; the doc itself is written against the
shared N4/N5 signing subsystem, not N5-specific prose — flagged so the low novelty here is not
mistaken for missing coverage).

**Testing.** The doc points at a separate "TestNG Support in Niagara 5" guide (not opened this
session — child gap B2-G3) and lists `gradlew :<moduleName>:niagaraTest` ("Run tests with code
coverage on a single `<moduleName>`") and `com.tridium.jacoco` ("Enable JaCoCo test coverage report
for the `niagaraTest` task") as the N5 task/plugin pair. `[CERT-doc]` `doc/buildN5.html`. This is the
same TestNG + `BTestNg` + JaCoCo combination REMIT-identified as N4's official framework (BTI §TI.3,
§469, §473: "El framework oficial de tests Niagara es TestNG + BTestNg (NOT JUnit 4)"), and the same
`niagaraTest` task name N4 used (REMIT BTI, `gradlew :chihuahua-rt:niagaraTest`). Whether N5's
`niagaraTest` still suffers N4's plugin-7.6.17 zero-tests-discovered defect (REMIT BTI §TI.3, "the
`moduleTestAnnotationProcessor` never produces the metadata XML that `writeTestModuleXml` requires")
is unverified — plausible that it is FIXED given §2.6's new AP now demonstrably writes
`moduleTest-include.xml` — but this is `[INFER]`, not confirmed against a live N5 `niagaraTest` run
(child gap B2-G4, requires-execution).

The `moduleTest` source set (`srcTest/`) and `moduleTestJar`/`moduleTestImplementation` naming are
unchanged from N4 (REMIT B711/BTI use identical names). `[CERT]`
(`NiagaraModulePlugin.kt`, `createNiagaraModuleTestSourceSet()`: `sourceSets.create("moduleTest")`).

## 2.10 — Bajadoc: a real `jdk.javadoc.doclet.Doclet`, unchanged tool identity `[CERT]`

`com.tridium.bajadoc` (`BajadocPlugin`) drives a `Bajadoc` task
(`com.tridium.gradle.plugins.bajadoc.task.Bajadoc`, `includePackage(...)` DSL, seen invoked in
`module.gradle.kts.vm`) that runs the doclet packaged separately at
`/mnt/c/Program Files/Niagara/5.0.0.28/lib/tridium-niagara-baja-doclet-5.0.4.jar` — class
`com.tridium.bajadoclet.Bajadoclet` plus a `SlotDeclarationParser`/`SlotDoc` pair for parsing
`@NiagaraProperty`-shaped slot declarations out of source for the generated API docs. `[CERT]`
(zip-entry listing + `META-INF/MANIFEST.MF`: `Implementation-Vendor: Tridium`,
`Implementation-Version: 5.0.4`, of `tridium-niagara-baja-doclet-5.0.4.jar`).

## 2.11 — Node/Yarn/Grunt: a real JS build surface exists in the plugin set, largely unexplored `[CERT]` + `[INFER]`

`com.tridium.node`/`rpno`, `com.tridium.yarn-ws`/`yarn-ws-agg`, and `com.tridium.grunt` are live
plugin ids in `n-plugin` (§2.1), and the devkit's `gradle.properties.vm` template has a commented
`nodeHome` property ("the path to your node install if it is not available on your PATH"). `[CERT]`
(properties file + plugin-id inventory, both already cited). The wizard template conditionally wires
a `gruntBuild` task (`tasks("babel:dist", "copy:dist", "requirejs")`) when `$javascriptModule` is set.
`[CERT]` `module.gradle.kts.vm`. Beyond this existence proof, the JS/UX build pipeline internals are
**not investigated** in this block — named as child gap B2-G5 (requires-execution or a deeper
decompile of the `node`/`grunt` packages, both out of scope for the "build toolchain vs. N4" gap as
literally asked).

## 2.12 — What the N4 build kit (`build-n4-module` skill) must change for N5 targeting `[INFER]` (synthesis)

Concrete delta list, each item backed by a section above:

1. **Plugin ids** — apply the full §2.2 rename table; `com.tridium.niagara-module` →
   `com.tridium.n-module` is the load-bearing one for the kit's own gradle-plugin references.
2. **`niagaraModule{}` → `moduleManifest{}`** (if the kit's templates used the old extension name —
   unresolved against the kit's actual `.gradle.kts` templates, not opened this session; the N4
   remittances cite `defaultModuleVersion` at ROOT level, which is unchanged, but do not name the
   per-module extension block, so this specific rename is `[INFER]`, not confirmed against the kit's
   own files — child gap B2-G6).
3. **Add `src/module-info.java` to every module/part folder** — entirely new requirement (§2.7); the
   kit's module-scaffolding step needs a JPMS descriptor generator mirroring
   `module-info.java.vm`, keyed off the same dependency list already declared in `<part>.gradle.kts`.
4. **Split `niagaraAnnotationProcessors` out of `nre`** — any kit template that assumed the AP shipped
   bundled with `nre` needs an explicit `niagaraAnnotationProcessor(":niagaraAnnotationProcessors")`
   line (§2.6).
5. **Stop hand-maintaining `module-include.xml`/`moduleTest-include.xml`** — §2.6 makes this
   generated-and-updated (never removed) by the AP; the kit's "did you forget to add the `<type>`
   entry" checklist step becomes obsolete for additions (still needed for deletions/renames per the
   doc's own caveat).
6. **Java 8 → Java 25 toolchain** — the kit's `gradle.properties`/CI images need a Java 25 JDK with
   JavaFX (§2.8), not Java 8; `gradlew idea`/`gradlew eclipse` tasks the kit may invoke for IDE setup
   no longer exist.
7. **Add `niagara_config_home`** to every kit-generated `gradle.properties`; treat `niagara_home` as
   read-only in any kit script that currently writes under it (§2.8).
8. **`settings.gradle.kts` auto-discovery** — a kit that generates explicit `include(":a", ":b")`
   lines can be simplified to rely on `com.tridium.set.mpr`'s `findProjects()` (§2.3), though this is
   optional, not required.
9. **Re-evaluate the plugin-7.6.17 `niagaraTest` dead-test workaround** (REMIT BTI) against N5 once a
   real N5 station is available — §2.6's new AP may have fixed the root cause, but this is unverified
   (B2-G4).

None of these 9 items were tested end-to-end against a real N5 build in this session — this beta
install ships only the Maven-repo plugin jars and devkit/docDeveloper doc jars, no runnable
`gradlew`/station. All 9 are therefore build-time-static conclusions; a requires-execution child gap
(B2-G7) is opened to run an actual `gradlew jar` against a trivial generated module and observe the
real task graph, `module-include.xml` write, and any `niagaraTest` outcome.

## 2.x — Self-verify tally

Literal `verify-block.sh` output (methodology §11: the reported tally must be the script's own
output, never hand-recalculated) — run read-only against this file, no other file touched:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    /home/cristian/niagara5-research/niagara5-block2.md
== verify-block: niagara5-block2.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1
   [CERT-live] 1
   [CERT] 45  (adj 43)
   [CERT-doc] 24  (adj 22)
   [CERT-web] 0
   [CERT-a] 1
   [INFER] 13  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/68 = 0.16
-- [CERT] file:line citation resolution --
   jar-entry  devkit.jar!rc/gradle.properties.vm  (jar archive path — not file-verifiable)
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

The `[CERT-hw]`/`[CERT-live]`/`[CERT-a]` raw=1 each are the header-legend LEGEND lines (marker
definitions in the blockquote), not fresh claims — adjusted count for those 3 is 0; this block makes
no `[CERT-hw]`/`[CERT-live]`/`[CERT-a]`/`[CERT-web]` claims (no secondary/forum source, no live
station, no downloaded-manual PDF). Adjusted `[INFER]`/`[CERT*]` ratio = 11/(43+22) = **0.17** — low,
consistent with a `mixed` evidence-heavy block whose synthesis load is §2.12's kit-delta list (item 2
declared `[INFER]`) plus the residual mechanism gaps B2-G1/B2-G2/B2-G4. `[CERT]` citations into
`/tmp/claude-1000/n5b2/vf-out/**` (Vineflower decompile of `n-plugin-5.0.54.9.2.jar`,
sha256 `eb9831b6…d93356`) resolve as `extern`/unresolvable to a script that only walks this corpus
directory — EXPECTED per methodology §11's decompiled-tree note; every one was read in full or in the
quoted range this session, not carried from memory. The one `jar-entry` line the script DOES flag
(`devkit.jar!rc/gradle.properties.vm`) is correctly reported as non-file-verifiable (a zip-internal
path); its content was inline-quoted verbatim in §2.8 for the same reason.

## 2.x — Connections

- **REMIT `niagara-research` B12** (§12.1.8) and **B631** (§631.1-2) — the N4 baseline this block
  contrasts against for Slotomatic mechanics and the "no JSR-269 processor in N4" finding that §2.6
  directly supersedes for N5.
- **REMIT `niagara-research` B434** — same `com.tridium.slottool.Slotomatic` class identity confirmed
  independently in N5 (§2.5).
- **REMIT `niagara-research` B711/B637** — N4's real operator build workflow (Clean+Slotomatic+Build
  variant rule); §2.12 item 9 is the open question of whether N5's AP changes that workflow's
  necessity.
- **REMIT `niagara-research` BTI** — N4's TestNG/JaCoCo framework and the plugin-7.6.17 dead-test
  defect; §2.9/§2.12 item 9 carry the open question into N5.
- **[TO ANNOTATE — child gap B2-G6]** — direct read of the `build-n4-module` skill's own
  `.gradle.kts` templates (not opened this session) to turn item 2 of §2.12 from `[INFER]` into
  `[CERT]`.
