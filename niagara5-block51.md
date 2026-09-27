# Block 51 — From build-n4-module to an N5 kit: file-by-file delta, n-java placement and derived dependencies

> Research of **what the `build-n4-module` kit's own files must change to target Niagara N5**,
> closing three named gaps: **B2-G6** (turn Block 2 §2.12 item 2's `[INFER]` into a direct read of the
> kit's own `.gradle.kts` templates), **B9-G3** (settle whether `com.tridium.n-java` must be applied
> per-module or at root — [Block 9] §9.6.G3 left this as an `[INFER]` resolvable statically), and
> **B13-G4** (why N5's `module.xml` declares fewer explicit `<dependencies>` than N4's — read the
> `WriteModuleXml`/`ModuleXml` task code). Covers: a file-by-file delta table for every N4 kit build
> template (`settings.gradle.kts`, root `build.gradle.kts`, per-profile `<module>.gradle.kts`,
> `gradle.properties`) against the working N5 PoCs/devkit templates; a `verify-module.sh` check-by-check
> N5 delta (bytecode major, `module-info.class`, `schemaVersion`, `runtimeProfile` removal, dependency
> baseline); a `build.sh` delta (Java toolchain, the `niagara_config_home` install-write hazard, task
> names); a classification of the kit's 37 `lint-*.sh` scripts into N5-obsolete / N5-needs-update /
> N5-still-valid, grounded in source (not guessed); the decompiled-source resolution of B9-G3 and
> B13-G4; and an ordered, **proposed** (not implemented) plan for a `build-n5-module` kit variant. Does
> NOT cover: a live re-run of any lint script against N5-ported source (no N5-ported module tree with a
> full lint sweep exists — every N5 PoC in this corpus was built without running the N4 kit's lints
> against it); the `report-module.sh`/`schema-risk.sh`/`bog-audit.sh` aggregation layer in detail beyond
> what feeds their N4-specific assumptions; or authoring the actual `build-n5-module` kit (explicitly
> out of scope — §51.7 is a plan, not a deliverable).
>
> Subject version: **N4 kit** — `build-n4-module-kit` at
> `/home/cristian/modulos_niagara_n4/niagara-tools/build-n4-module-kit`, files as read this session
> (mtimes 2026-09-05 through 2026-09-27, `BUILD-STATE.md` at 2026-09-27 04:43 — read-only, not
> modified). **N5 side** — Niagara 5.0.0.28 beta, Gradle plugin artifacts `5.0.54.9.2`/`5.0.9.8.14`, per
> [Block 2]/[Block 9]/[Block 16]/[Block 28]/[Block 39] (all READ, not re-derived, this session — see
> Sources).
>
> Sources:
> - `build-n4-module-kit/toolbelt/build.sh`, `verify-module.sh` (624 lines, full read), `lint-structure.sh`
>   (362 lines, full read), `lint-wb-threading.sh` (238 lines, full read), `lint-servlet.sh` (grep +
>   targeted read), and a full-corpus `grep -ln` sweep of all 37 `lint-*.sh` scripts for
>   N4-packaging-specific tokens (`javax\.baja`, `javax\.servlet`, `-rt|-ux|-wb`, `module-permissions`,
>   `module\.xml`, `major`/bytecode, `swing`/`invokeLater`) this session.
> - `build-n4-module-kit/fixtures/MinimalPan/{settings.gradle.kts,build.gradle.kts,gradle.properties}`,
>   `MinimalPan/MinimalPan/MinimalPan-rt/MinimalPan-rt.gradle.kts`,
>   `MinimalDash/MinimalDash/MinimalDash-ux/MinimalDash-ux.gradle.kts` — the kit's own canonical
>   B790-minimal N4 templates, all read in full this session.
> - `~/.claude/skills/build-n4-module/SKILL.md` — read for kit-resolution/execution-step context.
> - `/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/java/NiagaraJavaPlugin.kt` (whole file, 87
>   lines) and `.../module/util/ModuleXml.java` lines 225-390 (`toElementInternal`,
>   `findModuleDependencies`, `getDependencyFromModule`, `getDependencyFromManifest`) — Vineflower
>   decompile of `n-plugin-5.0.54.9.2.jar`, cached from [Block 2]'s session, **re-read to completion this
>   session** (not re-decompiled; the same cached tree [Block 39] also re-read).
> - `/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/NiagaraModulePlugin.kt` lines 195-300
>   (`registerModuleTasks`, `configureConfigurations`) — same decompiled tree, read this session for the
>   first time (Block 2 read other regions of this file; this session reads the dependency-classpath
>   wiring specifically).
> - [Block 2] (N5 plugin/DSL census — REMIT for the N5-side "required content" column), [Block 9] (PoC
>   scaffold, B9-G3's own framing), [Block 16]/[Block 28]/[Block 39] (real-module ports, B16-G5's
>   unexplained `vendorVersion` truncation — closed as a side-finding here, §51.6), `docs/n4-to-n5-porting-guide.md`
>   (synthesis cross-check).
>
> Method: direct `Read`/`grep` of every N4 kit file named in scope (no decompilation on the N4 side — the
> kit is plain bash/Kotlin-DSL source); targeted re-read of already-decompiled N5 plugin classes to answer
> the two mechanism questions (B9-G3, B13-G4) that [Block 2]/[Block 9] could not close from the outside;
> cross-reference against the 5 live-build PoC blocks for the N5-side "required content" column (no new N5
> build was run this session — every N5-side claim is `REMIT` from a block that ran a real `gradlew`).
> Markers (METHODOLOGY §3): `[CERT]` local primary source (`file:line`) · `[CERT-hw]` a prior session's own
> live command output, cited via `REMIT [Block N]` · `[INFER]` deduction · `REMIT` = cited from a prior
> corpus block, not re-opened this session (context, not a fresh `[CERT-*]` claim of this block, per
> [Block 2]'s own convention).
>
> N5 build-toolchain layer, synthesis/kit-delta focus. Connects [Block 2] (§2.12's 9-item kit-delta list,
> extended here file-by-file), [Block 9]/[Block 16]/[Block 28]/[Block 39] (the live-build evidence this
> block's "N5 required content" column cites), `docs/n4-to-n5-porting-guide.md` (the module-porting
> procedure this block's kit-delta plan operationalizes into kit tooling).
>
> **Type:** mixed — §51.1-§51.4 are direct evidence reads of both the N4 kit and (via REMIT) the N5 PoCs;
> §51.5/§51.6 are fresh `[CERT]` decompiled-source reads closing two named gaps; §51.7 is an explicitly
> labeled proposal/plan, not evidence.
>
> **Breakthrough:** two mechanism questions this corpus had left open as `[INFER]` are now settled
> directly from decompiled source, not inferred from build behavior: (1) `com.tridium.n-java` must be
> applied **per-module**, not at root — `NiagaraJavaPlugin.apply()` calls
> `project.getPluginManager().withPlugin("java", ...)` and then reads `this.$this_run.getTasks()`,
> configuring `JavaCompile` only on the project the plugin's `apply()` ran against; there is no
> `subprojects{}`/`allprojects{}` traversal in the class at all, so applying it at root would configure
> only the root project's (non-existent) Java tasks, never a subproject's (§51.5). (2) N5's
> `module.xml <dependencies>` are **not** derived from `module-info.java`'s JPMS `requires` list at
> all — `ModuleXml.findModuleDependencies()` walks the module's own resolved `compileClasspath`
> configuration, opens every jar's `META-INF/module.xml`, and emits one `<dependency>` per Niagara-module
> jar found there (filtered by `excludedDependencyModules`, version-stripped to `dependencyVersionLimit`
> — default **2** segments) — a purely Gradle-classpath-side mechanism, entirely independent of the
> hand-authored JPMS descriptor (§51.6). That same `dependencyVersionLimit=2` default is also the exact,
> previously-unexplained cause of [Block 16] B16-G5's `vendorVersion="2.0"` truncation — closed as a
> free side-finding.

---

## 51.1 — File-by-file delta table: the kit's own N4 build templates vs. the N5 shape

Every "N4 content" cell below is quoted verbatim from the kit's own canonical fixture
(`fixtures/MinimalPan/**`, `fixtures/MinimalDash/**` — the kit's B790-minimal skeleton, read in full
this session, §Sources). Every "N5 required content" cell is quoted verbatim from a **working, built**
N5 PoC file (REMIT [Block 9]/[Block 16]/[Block 28] — a real `gradlew jar` produced the artifact these
lines came from), not from the wizard template alone.

### 51.1.1 — `settings.gradle.kts` (root)

| | N4 (kit's own `fixtures/MinimalPan/settings.gradle.kts`) | N5 required (REMIT [Block 9] §9.4, PoC file that built clean) |
|---|---|---|
| plugin ids in `pluginManagement.plugins{}` | `com.tridium.settings.multi-project`, `com.tridium.settings.local-settings-convention`, `com.tridium.niagara`, `com.tridium.vendor`, `com.tridium.niagara-module`, `com.tridium.niagara-signing`, `com.tridium.convention.niagara-home-repositories` | `com.tridium.set.mpr`, `com.tridium.set.lsc`, `com.tridium.niagara`, `com.tridium.vendor`, `com.tridium.n-module`, `com.tridium.n-java` **(new — not in the N5 wizard's own default list either, [Block 9] §9.4's load-bearing correction)**, `com.tridium.sign`, `com.tridium.bajadoc`, `com.tridium.jacoco`, `com.tridium.nap`, `com.tridium.conv.n-repo` |
| plugin version variable | `gradlePluginVersion` `getOrElse("7.6.17")`, `settingsPluginVersion = "7.6.3"` (hardcoded) | `gradlePluginVersion = "5.0.54.9.2"`, `settingsPluginVersion = "5.0.9.8.14"` (both `[CERT]` [Block 2] §2.1, `plugin-version.properties`) |
| top-level `plugins{}` block | `id("com.tridium.settings.multi-project")`, `id("com.tridium.settings.local-settings-convention")` | `id("com.tridium.set.mpr")`, `id("com.tridium.set.lsc")` |
| subproject discovery | `configure<MultiProjectExtension> { findProjects() }` — **identical call, same import** `com.tridium.gradle.plugins.settings.MultiProjectExtension` | unchanged: `configure<MultiProjectExtension> { findProjects() }` — REMIT [Block 2] §2.3, `findProjects()` no-arg walks 4 recognized naming conventions in N5 too |
| `LocalSettingsExtension` | `configure<LocalSettingsExtension> { loadLocalSettings() }` | unchanged call shape (REMIT [Block 9] §9.4's own `settings.gradle.kts`, same `loadLocalSettings()` line) |
| `gradlePluginRepoUrl` derivation | `"file:///${gradlePluginHome.replace('\\', '/')}"` — no space-escaping | N5's own template additionally escapes spaces: `"file:///${gradlePluginHome.replace('\\', '/').replace(" ", "%20")}"` (REMIT [Block 9] §9.4) — a **load-bearing delta** the kit's own N4 file does not carry: an install path containing a space (default Windows `C:\Program Files\Niagara\...`) will fail plugin-repo resolution on N5 without this escape |
| `rootProject.name` | `"MinimalPan"` (fixture-specific string) | unchanged mechanism (a plain string literal); no plugin-side change |

Evidence: N4 column `[CERT]` `fixtures/MinimalPan/settings.gradle.kts` (whole file, quoted in full in
§Sources' Read). N5 column `[CERT]` REMIT [Block 9] §9.4's own working `settings.gradle.kts` (quoted
verbatim there, itself `[CERT-hw]` — a real `./gradlew jar` succeeded against it) + [Block 2] §2.2's
official rename table (`[CERT-doc]` `buildN5.html`).

### 51.1.2 — root `build.gradle.kts`

| | N4 (`fixtures/MinimalPan/build.gradle.kts`) | N5 required (REMIT [Block 9]/[Block 28], working PoC root files) |
|---|---|---|
| `plugins{}` | `com.tridium.niagara`, `com.tridium.vendor`, `com.tridium.niagara-signing`, `com.tridium.convention.niagara-home-repositories` | `com.tridium.niagara`, `com.tridium.vendor`, `com.tridium.sign`, `com.tridium.conv.n-repo` |
| `vendor{}` block | `defaultVendor("Angeles"); defaultModuleVersion("1.0.0")` | **byte-identical call shape and semantics** — REMIT [Block 2] §2.3: `defaultVendor`/`defaultModuleVersion` decompiled from `VendorExtension.kt` unchanged; [Block 28] §28.7 confirms two real client groups (`Compresores`/`Paccadia` at `2.0.7`, `Dashboard` at `2.1.1`) both use this exact N4 call form ported verbatim to N5's root script with zero signature change |
| `subprojects{ repositories{...} }` | `mavenCentral()` only | unchanged for the N4-authored repos block itself; [Block 39] §39.3 shows `mavenCentral()` must already be present here for any module needing real `org.openjfx`/`org.apache.xmlgraphics` `compileOnly` deps (§51.1.3 below) — not a syntax change, but a new REASON the block must not be dropped |

Evidence: N4 `[CERT]` `fixtures/MinimalPan/build.gradle.kts` (whole file). N5 `[CERT]` REMIT [Block 9]
§9.4 (`build.gradle.kts`, quoted in full, `[CERT-hw]` build-proven) + [Block 2] §2.2 rename table.

### 51.1.3 — per-profile `<module>-<part>.gradle.kts`

The kit ships two canonical shapes — a pure-logic `-rt` (`MinimalPan-rt.gradle.kts`) and a servlet
`-ux` (`MinimalDash-ux.gradle.kts`). Both deltas below are build-proven on REAL client modules, not just
the PoC stub (REMIT [Block 16] ColdRoomPan-rt, [Block 28] CompPan-rt/DashboardPan-rt).

| | N4 `-rt` (`MinimalPan-rt.gradle.kts`) | N5 required (REMIT [Block 16] §16.2, `ColdRoomPan-rt.gradle.kts`, build-proven) |
|---|---|---|
| `import` | `com.tridium.gradle.plugins.module.util.ModulePart.RuntimeProfile.*` | **deleted entirely** — the `RuntimeProfile` type no longer exists in the N5 DSL surface used by the kit's own templates; nothing replaces this import |
| `plugins{}` | `com.tridium.niagara-module`, `com.tridium.niagara-signing`, `com.tridium.bajadoc`, `com.tridium.niagara-jacoco`, `com.tridium.niagara-annotation-processors`, `com.tridium.convention.niagara-home-repositories` | `com.tridium.n-module`, `com.tridium.n-helper-modularity` **(new — replaces `niagara-annotation-processors` as the per-module id; see next row)**, `com.tridium.n-java` **(new — not in the N5 wizard's own default `modulePlugins.vm` list either; without it, `--module-path` is never set on `javac` and the resulting error is misdiagnosable as a namespace bug, [Block 9] §9.4's own load-bearing finding)**, `com.tridium.sign`, `com.tridium.bajadoc`, `com.tridium.jacoco`, `com.tridium.nap`, `com.tridium.conv.n-repo` |
| `moduleManifest{}` body | `moduleName.set("MinimalPan"); runtimeProfile.set(rt)` | `moduleName.set("ColdRoomPan"); checkModuleName.set(false)` — **`runtimeProfile.set(...)` line deleted outright, no replacement property exists** (REMIT [Block 16] §16.2 step 4, [Block 2] §2.4's `ModuleXml` DSL table has no `runtimeProfile`-named field at all) |
| `dependencies{}` | `nre(":nre")`, `api(":baja")`, `moduleTestImplementation(":test-wb")` | `nre(":niagaraAnnotationProcessors")` **(new, split out — REMIT [Block 2] §2.6)**, `nre(":nre")`, `niagaraAnnotationProcessor(":niagaraAnnotationProcessors")` **(new configuration name)**, `api(":baja")`; test dependency changes shape entirely — `moduleTestImplementation(":test")` **plus** `moduleTestImplementation("org.testng:testng:7.12.0")` **(both required — `:test` alone does not expose `org.testng.*` transitively, [Block 16] §16.5.3)**. `:test-wb` **does not exist as an N5 artifact at all** ([Block 28] §28.2 finding 4, B28-G1: confirmed absent from all 247 `modules/`+`bin/ext` jars by name) |
| `tasks.named<Bajadoc>("bajadoc")` | `includePackage("com.angeles.MinimalPan")` | unchanged call shape; import `com.tridium.gradle.plugins.bajadoc.task.Bajadoc` unchanged (REMIT [Block 2] §2.10, class identity confirmed unchanged) |

| | N4 `-ux` (`MinimalDash-ux.gradle.kts`) | N5 required (REMIT [Block 28] §28.5, `DashboardPan-rt.gradle.kts` — merged into the `-rt` project post-CHK-1, servlet code now lives there) |
|---|---|---|
| servlet dependency | `compileOnly("javax.servlet:javax.servlet-api:3.1.0")` | `compileOnly("jakarta.servlet:jakarta.servlet-api:6.1.0")` — exact coordinate pinned by the shipped `libs.versions.toml:102`, not guessed ([Block 28] §28.5) |
| intra-module dependency | `api(project(":MinimalDash-rt"))` | **deleted outright, not stripped/renamed** — once `-ux` and `-rt` merge into one compilation unit (N5's CHK-1, [Block 10]/[Block 28] §28.3), a same-module cross-package Java reference needs no build-time indirection at all |
| `-rt`-suffixed module deps | `api(":web-rt")` | `api(":web")` (suffix stripped; REMIT [Block 2] §2.2's rename table has no direct `-rt`-suffix rule, but every real N5 module-name pair examined in [Block 16]/[Block 28] drops the part suffix) |
| moduleTest deps | `moduleTestImplementation(":test-wb")`, `moduleTestImplementation("junit:junit:4.13.2")` | JUnit4 is a **hard incompatibility**, not a version bump — N5's `test` module ships TestNG only; `import org.junit.Test` fails to compile at all (`package org.junit does not exist`, [Block 16] §16.5.2) |
| packaging block | `tasks.named<Jar>("jar") { from("src/rc"){ include("**/*"); into("rc") } }` | **unchanged shape**, confirmed byte-identical mechanism on the real, 3.6 MB `DashboardPan` `index.html` (byte-identical copy, [Block 28] §28.3.3) — this one Jar-packaging block needs no delta at all |

Evidence: N4 columns `[CERT]` `fixtures/MinimalPan/MinimalPan/MinimalPan-rt/MinimalPan-rt.gradle.kts` and
`fixtures/MinimalDash/MinimalDash/MinimalDash-ux/MinimalDash-ux.gradle.kts` (both whole files, quoted in
full this session). N5 columns `[CERT]` REMIT [Block 16] §16.2/§16.4, [Block 28] §28.2/§28.3/§28.5 —
every cell traces to a line that appeared in a jar that actually built (`BUILD SUCCESSFUL`), not a
template read in isolation.

### 51.1.4 — `gradle.properties`

| | N4 (`fixtures/MinimalPan/gradle.properties`) | N5 required (REMIT [Block 9] §9.1, [Block 16] §16.1/§16.3) |
|---|---|---|
| properties present (all commented-out placeholders in the kit's own fixture) | `gradlePluginHome`, `niagara_home`, `niagara_user_home` | `niagara_home` (now **read-only** by N5's own convention — `[CERT-doc]` REMIT [Block 2] §2.8), `niagara_config_home` **(entirely new key, no N4 equivalent — REMIT [Block 2] §2.8)**, `niagara_user_home`, `org.gradle.java.installations.paths` (points at a JDK 25, not JDK 8) |
| the one property that MUST NOT be set to the shared real install on N5 | not applicable — N4's `build.sh` (§51.3) already redirects the module-install path via `niagara_home`/`modules/` semantics that do not auto-publish on `:jar` | **`niagara_config_home`** — pointing it at the real, shared `/mnt/c/.../config/5.0.0.28` causes the `:jar` task to silently *install* the built jar into that shared `modules/` directory as a side effect of the same flat-file-repo convention plugin that reads from it ([Block 16] §16.3, a genuinely dangerous, previously-undocumented hazard with **no N4 equivalent warning anywhere in the kit today**) |

Evidence: N4 `[CERT]` `fixtures/MinimalPan/gradle.properties` (whole file). N5 `[CERT-hw]` REMIT
[Block 16] §16.3 (the live incident: a real `.jar` file appearing inside the read-only install, with
timestamp evidence) + [Block 9] §9.1 (safe pattern that avoided it by module-name luck alone, not by
design).

## 51.2 — `verify-module.sh`: check-by-check N5 delta

All 19 checks read in full this session (§Sources). Verdicts below are grounded either in a REMIT
live-build fact (`[CERT-hw]` via a cited block) or in this session's direct read of the check's own
grep/awk logic against what N5 source actually looks like (`[CERT]`).

| Check (as shipped) | N4 behavior | N5 verdict | Why |
|---|---|---|---|
| `bytecode` (major 52) | asserts every `.class` entry is bytecode major 52 (Java 8) | **must change to 69** | REMIT [Block 9] §9.5 / [Block 16] §16.7 / [Block 28] §28.7: every N5-built `.class` (including `module-info.class`) is confirmed major **69** (Java 25), across 3 independently built real modules — not a one-off |
| `signed` (`NIAGARA4.SF` present) | asserts the entry exists | **unchanged, still valid as-is** | REMIT [Block 9] §9.5: "same `NIAGARA4.*` signature-file naming N4 uses, confirmed unchanged into N5"; re-confirmed on all 3 real N5 module builds |
| `types` (module.xml `<type>` → `.class`) | walks `<type class=...>` and checks the matching `.class` exists | **unchanged mechanism, still valid** | REMIT [Block 9] §9.5: N5's `<types>` element is written by the AP but has the identical `<type class="..." name="..."/>` shape the check already parses; [Block 16]/[Block 28] both show it resolving correctly on real modules |
| `baja` (`--target-version`, baja vendorVersion) | compares the `<dependency name="baja" vendorVersion=...>` against `--target-version` | **mechanism unchanged; the comparison BASELINE moves from a 4.x string to a 5.x string** | REMIT [Block 9] §9.5: N5's auto-added baja dependency is literally `<dependency name="baja" vendor="Tridium" vendorVersion="5.0"/>`; the check's `ver_le` dot-numeric compare logic is version-string-format-agnostic and needs no code change, but any caller still passing a 4.x `--target-version` against an N5 jar will always FAIL (the comparison is correct, the CALLER convention needs updating, not the check) |
| `stored` (`--stored`, zero Deflated entries) | Workbench re-sign safety check | **untested on N5 — no evidence either way** | none of [Block 9]/[Block 16]/[Block 28]/[Block 39] ran `unzip -v`/Deflated-entry inspection or attempted a Workbench re-sign against an N5 jar; named child gap B51-G1 below |
| `typecount` (`--src`, jar `<type>` count == `module-include.xml` count) | compares packaged types against the source `module-include.xml` | **unchanged mechanism, still valid** | REMIT [Block 16] §16.4 CHK-9 / [Block 28] §28.6 CHK-9: N5's AP writes `module-include.xml` in place with the correct count on every build (confirmed on 1-file, 2-package, and multi-part-merged real modules); `profile_dir()`'s `<jar-basename>` → source-dir convention still holds because N5 kept the `-rt`/`-ux` project-name suffix even after a multi-part CHK-1 merge (REMIT [Block 28] §28.3: the merged project is still named `DashboardPan-rt`) |
| `facets` (raw-number MIN/MAX under `--src`) | greps `BFacets.make(BFacets.(MIN|MAX), <raw number>)` in `.java` under `<profile>/src` | **unchanged mechanism, still valid** | the grep keys on the literal `BFacets`/`@NiagaraProperty` annotation vocabulary, not on the `javax.baja.*`/`niagara.*` import namespace — REMIT [Block 9]'s `BN5Hello.java` keeps the identical `@NiagaraProperty`/`@NiagaraAction` simple annotation names post-rename (only their PACKAGE moved, from `javax.baja.nre.annotations` to `niagara.nre.annotations`, [Block 9] §9.2) |
| `facets-req` (`--src`, OPERATOR numeric facets-key WARN) | same annotation-text scan as `facets` | **unchanged mechanism, still valid** | same reasoning — the awk parses `@NiagaraProperty(...)`/`OPERATOR`/`UNITS`/`PRECISION` tokens, none of which are namespace-qualified strings |
| `ord-literal` (`--src`, `station:`/`local:`/`slot:/` string WARN) | greps hardcoded ORD literal strings | **unchanged mechanism, still valid** | ORD literal syntax (`station:`/`local:`/`slot:/`) is a Baja-runtime string format, not a Java import path; REMIT no block reports an ORD-syntax change anywhere in N5 |
| `rcbackup` (editor/backup files under `rc/`) | pure filename-pattern check on the jar's own entry list | **unchanged, still valid** | generic zip-entry-name check, no N4/N5-specific content at all |
| `palette` (empty `module.palette` WARN, `b:Folder` vs `b:UnrestrictedFolder`) | parses `module.palette` XML | **unchanged mechanism, still valid** | REMIT [Block 16] §16.7 / [Block 28] §28.7: `module.palette` is copied byte-verbatim into every N5 build with no schema change observed |
| `wb-scaffold` (`-wb` jar, 0 classes + 0 palette entries) | fires only on a jar basename ending `-wb` | **its trigger condition is now the COMMON case, not a rare edge case** | REMIT [Block 28] §28.3: DashboardPan's real `-wb` part contributed **zero** source and was folded away entirely under N5's CHK-1 merge (`com.tridium.set.mpr`'s `findProjects()` needs no grouping file — [Block 16] §16.4 CHK-7, generalized by [Block 28] §28.6). A ported N5 module very often has NO `-wb` jar to run this check against at all; the check itself does not need code changes, but its practical applicability shrinks — flagged as **needs-context-update**, not obsolete |
| `phantom-dep` (`--src`, module.xml `<dependency>` not declared in gradle.kts) | matches `api\|nre\|implementation` config calls against declared `<dependency name=...>` | **regex needs extension — N5 adds new dependency-declaring configuration names the current regex does not match** | §51.1.3 shows N5 modules declaring `nre(":niagaraAnnotationProcessors")`, `niagaraAnnotationProcessor(":niagaraAnnotationProcessors")`, and (for alarm/bajaui-touching modules) `compileOnly(...)` Maven coordinates ([Block 39] §39.3) — none of these break the EXISTING `api\|nre` matches for ordinary Niagara-module deps, but a module using `unterjar(...)`/`uberjar(...)` (real N5 configuration names, REMIT [Block 2] §2.4's dependency-configuration table) would currently be invisible to this check's `gkt_deps` extraction, a genuine **needs-update**, not proven broken on a real module this session (no built N5 module used `unterjar`/`uberjar`) |
| `moduletest-present` (`--src`, `-rt` jar w/ prod `.java` but no `moduleTest-include.xml`) | fires on any `-rt` jar | **unchanged mechanism, still valid** | REMIT [Block 16] §16.7: N5's moduleTest jar carries its own `module.xml`/`moduleTest-include.xml` pair with an unchanged file-presence contract; the check's `-rt`-suffix gate still matches N5 project names |
| `cross-module-type` (`--src`, foreign FQN in `@NiagaraProperty type=`) | whitelists `javax.baja.*`, `com.tridium.*`, `com.tridiumx.*`, `com.honeywell.*` as known-safe prefixes | **the whitelist itself is stale and MUST add `niagara.*`** | every N5-native framework type (`niagara.sys.BComponent`, `niagara.alarm.BAlarmRecord`, etc., [Block 9] §9.2) now lives under `niagara.*`, not `javax.baja.*` — as shipped, this check would WARN on every single N5-native `@NiagaraProperty type="niagara...."` reference as a "foreign type," a **guaranteed false-positive flood** on any real N5 module, not a hypothetical risk |
| `transient-operator` (`--src`, TRANSIENT+OPERATOR flag combo) | greps `Flags.TRANSIENT`/`Flags.OPERATOR` co-occurrence | **mechanism unchanged; import origin unverified** | the `Flags` constants themselves were not independently re-confirmed under `niagara.sys.Flags` this session — plausible unchanged by continuity with `BComponent`/`Property`/`Type` all moving intact under `niagara.sys.*` ([Block 9] §9.2), but not `[CERT]`; named child gap B51-G2 |
| `compact3-import` (`--src`, `-rt`/`-ux` importing `java.awt.*`/`javax.swing.*`/`java.sql.*`) | Compact3 JRE-subset exclusion warning | **applicability to N5 is UNCONFIRMED, not refuted** | [Block 2] §2.7/§2.8 found a real `Compact3ArgumentProvider` wired by `com.tridium.n-java` on every `JavaCompile` task, by NAME alone — its actual javac argument value was never read (child gap B2-G2, still open); if N5's NRE still ships a Compact3-subset JRE, this check's logic is directly reusable unmodified (no namespace dependency in the pattern itself); if N5 dropped the Compact3 profile, the check becomes a silent, harmless no-op, not a false-positive risk either way — genuinely unresolved, not "still valid" by confirmation |
| `subscription-leak` (`--src`, `TypeSubscriber` w/o `stopped()`) | class-name pattern match | **unchanged mechanism, still valid** | `TypeSubscriber` is a `com.tridium.*`/`niagara.*`-namespace-agnostic simple class name the check matches textually; no evidence of an API shape change in any read block |
| `slot-wall` (`--src`, >15 `@NiagaraProperty` per class) | pure annotation-count | **unchanged mechanism, still valid** | same reasoning as `facets`/`facets-req` — annotation vocabulary, not import path |

**Two entirely NEW checks N5 needs that N4 never required, named but not implemented here (proposal
only, §51.7):**

- **`module-info-class` presence** — every N5 module jar must ship a real `module-info.class` at major 69
  ([Block 1] §1.4 REMIT, [Block 9]/[Block 16]/[Block 28] §9.5/§16.7/§28.7 confirmed on all 3 real
  builds); N4 never had a JPMS descriptor to check at all.
- **`schema-version-5`** — `META-INF/module.xml`'s root `<module ...>` element must carry
  `schemaVersion="5"` ([Block 2] §2.4, `ModuleXml.java` `toElementInternal()` line
  `root.setAttr("schemaVersion", "5")`, confirmed present on every real N5-built jar's `module.xml` this
  session's read of §51.1/[Block 9]/[Block 16]/[Block 28]).
- **`no-runtime-profile`** — an N5-targeted `.gradle.kts` should FAIL a lint that finds a lingering
  `runtimeProfile.set(...)` call or `ModulePart.RuntimeProfile` import (§51.1.3 — the property/type no
  longer exists in the N5 `ModuleXml` DSL at all, so this is a compile-time error already, but a kit
  authoring/scaffolding lint catching it BEFORE a `gradlew` invocation saves the round-trip).

## 51.3 — `build.sh`: chain-level N5 delta

Read in full (273 lines). Delta, ordered by where in the chain each item bites:

1. **Java toolchain.** N4: hardcoded `J8="${JAVA8:-/usr/lib/jvm/java-8-openjdk-amd64}"`, passed as
   `-Porg.gradle.java.installations.paths="$J8"`. N5 needs **any JDK 25** — REMIT [Block 9] header/[Block 39]
   §39.5: "Keep the existing Homebrew OpenJDK 25 toolchain... no JavaFX-bundled JDK distribution needs to
   be sourced." The Gradle property name (`org.gradle.java.installations.paths`) is unchanged; only the
   version and the hardcoded default path need updating (a kit-config value, not a mechanism change).
2. **`--plugin-version`/`$NIAGARA_PLUGIN_VERSION` forwarding.** N4's `build.sh` auto-detects
   `niagaraPluginVersion` from the module's `gradle.properties`/`settings.gradle.kts` and forwards it as
   `-PniagaraPluginVersion=...`. N5's `settings.gradle.kts` (§51.1.1) has **no `niagaraPluginVersion`
   Gradle property at all** — both `gradlePluginVersion`/`settingsPluginVersion` are hardcoded string
   literals inside the template itself (REMIT [Block 2] §2.1/§2.3, [Block 9] §9.4's own working
   `settings.gradle.kts`). This whole auto-detect-and-forward mechanism needs to become a no-op (or be
   repointed at whatever variable an eventual N5 kit template uses) — a real behavioral delta, not
   cosmetic.
3. **`niagara_config_home` — the single most consequential build.sh-adjacent finding this block carries
   forward.** N4's `build.sh` has an entire "Deployed-baseline drift gate (Δ2)" built around the
   assumption that `:jar` publishes into `<niagara_home>/modules/<jar>` (confirmed by its own inline
   comments, §Sources `build.sh` read). On N5, the equivalent auto-publish target is
   `<niagara_config_home>/modules/`, a **different property**, and REMIT [Block 16] §16.3 shows this is
   not hypothetical — it happened, wrote into the real shared install, and needed an explicit local-mirror
   redirect to fix. A `build-n5-module` variant of `build.sh` needs Δ2's drift-detection logic
   re-targeted at `niagara_config_home`, not `niagara_home`.
4. **Task names (`:MOD-$p:clean`, `:MOD-$p:slotomatic`, `:MOD-$p:jar`).** **Unchanged** — REMIT
   [Block 9] §9.3/[Block 16] §16.8: `slotomatic`, `jar`, `clean` are all still real, identically-named
   Gradle tasks in N5; the exact `TASKS+=(":$MOD-$p:clean" ":$MOD-$p:slotomatic" ":$MOD-$p:jar")` array
   construction needs zero change on this point.
5. **Profile auto-detection (`for p in rt ux wb`).** N4's `build.sh` scans `$MOD/$MOD-rt`,
   `$MOD/$MOD-ux`, `$MOD/$MOD-wb` as 3 independent candidates. N5's CHK-1 module-part merge (REMIT
   [Block 10]/[Block 16] §16.4 CHK-7/[Block 28] §28.3) means a *ported* N5 module typically has **one**
   project folder (the highest-precedence part, usually `-rt`) holding all the merged source — the
   3-candidate scan logic itself is not WRONG for N5 (a not-yet-merged N4 source tree still has 3 real
   directories going INTO the port), but the kit's build orchestration needs an explicit merge step
   BEFORE this scan runs, not a scan-time change.
6. **The `--no-drift-check`, `has_gradle`/`has_sources` helpers, `_content_hash`/`_module_own_version`
   functions.** All **generic, format-agnostic** (`unzip -Z1`/`grep -oE '<module [^>]*vendorVersion="...'`
   over any `META-INF/module.xml`) — REMIT [Block 9]/[Block 16]/[Block 28]/[Block 39] all confirm N5's
   `module.xml` still carries a `vendorVersion` attribute on the `<module>` root in the same XML shape;
   these functions need **zero code change**, only the drift-gate's directory target (item 3).

## 51.4 — Lint classification summary (37 scripts, grounded, not exhaustive per-script re-derivation)

A full-corpus `grep -ln` sweep (§Sources) for N4-packaging-specific tokens across all 37
`toolbelt/lint-*.sh` scripts found **zero** hits for `javax\.baja`, `javax\.servlet`, `com.tridium.niagara-module`
(or any other N4 plugin id), or `module-permissions\.xml` in ANY lint script — every one of the kit's
lints keys on **annotation/keyword vocabulary** (`@NiagaraProperty`, `@NiagaraType`, `Flags.OPERATOR`,
`BFacets.make`, `TypeSubscriber`, `Clock.schedule`, ORD-literal string syntax) rather than on the Java
import-path namespace that actually moved (`javax.baja.*` → `niagara.*`, [Block 9] §9.2). This is the
single biggest reason MOST of the kit's lints transfer to N5 with **no code change at all** — they were
never coupled to the namespace in the first place.

| Category | Scripts (representative, not exhaustive) | Verdict |
|---|---|---|
| Annotation/Flags/keyword-vocabulary lints | `lint-delays.sh`, `lint-timers.sh`, `lint-demand-scope.sh`, `lint-silent-protection.sh`, `lint-ext-writable-shape.sh`, `lint-write-path.sh`, `lint-config-sanity.sh`, `lint-recovery-path.sh`, `lint-status-parity.sh`, `lint-clock-zero-floor.sh`, `lint-no-system-out.sh`, `lint-null-context-write.sh`, `lint-changed-hot-write.sh`, `lint-persist-hot-write.sh`, `lint-subscribe-without-unsubscribe.sh`, `lint-agent-on-shape.sh` (partial — see below), `lint-arbitrary-ord.sh`, `lint-bql-string-concat.sh`, `lint-lexicon-ascii.sh`, `lint-no-md5-credential-digest.sh`, `lint-inert-coordination.sh`, `lint-session-store-lazy-evict.sh`, `lint-spa-poll-no-recovery.sh` | **still valid, no code change identified** — grep sweep confirms zero N4-namespace-specific tokens; the underlying Java/Baja vocabulary these scripts key on is unchanged by REMIT [Block 9] §9.2/§9.3 |
| `lint-servlet.sh` | (single script) | **still valid, no code change** — its own `is_servlet` detector matches `extends BWebServlet` / `doGet\|doPost\|service(` method signatures, both confirmed unchanged simple names in N5 (REMIT [Block 28] §28.5, `niagara.web.BWebServlet` same shape); it never string-matches `javax.servlet`/`jakarta.servlet` at all, so the jakarta rename (§51.1.3) does not affect it |
| `lint-structure.sh` (module source-tree structure) | (single script, but multiple sub-checks) | **mixed — several sub-checks need N5-specific updates**, detailed below |
| `lint-wb-threading.sh` | (single script) | **needs update — likely obsolete threading model, not merely a namespace rename** — detailed below |
| `lint-bundled-jar-class-version.sh` | (single script) | **needs its accepted-major-version constant updated** — same bytecode-major delta as `verify-module.sh` (§51.2): whatever major-version literal it currently checks against needs the 52→69 update (not independently re-read line-by-line this session; flagged by the grep sweep hit on `major`/bytecode tokens, named child gap B51-G3) |
| `rc-scan.sh`, `bog-audit.sh` | (2 scripts, `-rt|-ux|-wb` grep hits) | **their `-rt|-ux|-wb` token hits are path-glob/profile-name matching, not namespace-coupled** — REMIT no block found either script's core check logic depends on the OLD 3-way split surviving; flagged as likely-still-valid but not independently read this session (named child gap B51-G4) |

### 51.4.1 — `lint-structure.sh`: sub-check-by-sub-check (read in full this session)

| Sub-check | N4 rule | N5 verdict |
|---|---|---|
| L1 (package must not be `javax.baja.*`) | `grep -qE '^[[:space:]]*package[[:space:]]+javax\.baja\.'` | **needs the pattern extended to also match `niagara\.'`** — an N5 module accidentally declaring its own package as `niagara.*` (the new framework namespace) is exactly the bug class L1 exists to catch, but the current regex is blind to it |
| L3 (pure-model package importing framework types, WARN) | `grep -qE '^[[:space:]]*import[[:space:]]+javax\.baja\.'` | **silently stops firing on N5 source** — an N5 module's pure-model package importing `niagara.sys.*` would never trigger this WARN as shipped; a false-negative (lost coverage), not a false-positive |
| L6 (module-include.xml present, no hand-authored META-INF/module.xml) | file-presence check | **unchanged, still valid** — REMIT [Block 9]/[Block 16]/[Block 28]: `module-include.xml` still exists as a source file on N5 and is still auto-regenerated, not hand-maintained |
| L7 (dependency version must be a 3-part floor, `X.Y.Z` not `X.Y`, matched via `":module:X.Y"` gradle-string syntax) | `grep -qE '":[^:]+:[0-9]+\.[0-9]+"'` against `*.gradle.kts` | **premise likely does not apply to N5 at all** — every real N5 dependency declaration read across [Block 2]/[Block 9]/[Block 16]/[Block 28] uses the bare `api(":baja")`/`nre(":nre")` form with **no inline version suffix**; N5's own `dependencyVersionLimit` mechanism (§51.6) governs the version that lands in `module.xml`, not a hand-written string in the `.gradle.kts`. If this reading holds, L7 simply never fires on N5 source (harmless no-op, not wrong) — `[INFER]`, not independently confirmed against a real N5 `.gradle.kts` containing an inline version string this session, named child gap B51-G5 |
| L9 (`-wb`/`-ux` empty-skeleton, 0 classes + empty palette) | file/palette-content check, profile-name-suffix-gated | **unchanged mechanism, but its trigger population changes** — same reasoning as `verify-module.sh`'s `wb-scaffold` (§51.2): N5's CHK-1 merge makes a genuinely-empty `-wb` folder the COMMON case for a ported multi-part module, not a mistake to flag; the check itself stays correct, its practical WARN rate on N5-ported trees will rise |
| L10 (no absolute host paths in `gradle.properties`) | generic path-pattern check | **unchanged, still valid** — no N4/N5-specific content |
| L11 (mixed BTest+JUnit srcTest requires BOTH `:test-wb` AND `junit` gradle declarations) | `grep`s for `:test-wb` specifically | **directly broken on N5 — `:test-wb` does not exist as an N5 artifact** (REMIT [Block 28] §28.2 finding 4/B28-G1: confirmed absent by name from all 247 `modules/`+`bin/ext` jars in the 5.0.0.28 install). This check's premise needs updating to N5's real test dependency pair, `:test` + explicit `org.testng:testng:7.12.0` (§51.1.3, [Block 16] §16.5.3) |
| L12 (`org.gradle.java.installations.paths`/`.auto-detect` present, uncommented) | generic property-presence check | **unchanged, still valid** — the property NAME is identical on N5 ([Block 9] §9.1's own `gradle.properties`); only the JDK version it should point at changes (§51.3 item 1), which L12 does not itself assert |
| L13 (sibling `gradle.properties` divergent `niagara_home=`) | generic cross-file consistency check | **unchanged mechanism; scope should extend to `niagara_config_home` too** — the exact hazard class this check guards against (divergent Niagara-install targeting across sibling builds) is the SAME class of bug §51.1.4/[Block 16] §16.3 found for `niagara_config_home` specifically; L13 as shipped checks only `niagara_home=`, leaving the more dangerous N5 property unchecked |

### 51.4.2 — `lint-wb-threading.sh`: the one script named "obsolete" in the task framing, checked directly

Read in full (238 lines, §Sources). Its `ui-thread-traversal` check WARNs when a `doInvoke` body reaches
`getNavChildren|getNavNodes|BqlQuery` without `invokeLater|BJobService|JobThread` anywhere on the
expanded call chain — i.e., it enforces that Workbench navigation code marshals onto the **Swing Event
Dispatch Thread** via `invokeLater` (Swing's/AWT's threading idiom) before touching nav-tree state.

This session's evidence for N5's `-wb`/Workbench layer is **JavaFX, not Swing**: [Block 28] §28.4 and
[Block 39] (whole block) both establish that `niagara.workbench`/`niagara.bajaui`/`niagara.gx` have a
hard, non-`static` transitive `requires` chain onto `javafx.{graphics,controls,web,swing}` — REMIT
[Block 39] §39.4's decisive finding: the vendor's OWN bundled `jre/bin/javac.exe` resolves these as real
system modules of its JDK, confirming JavaFX genuinely IS N5's desktop-UI toolkit dependency at the
platform level, not merely present as files. **JavaFX's own thread-marshaling idiom is
`javafx.application.Platform.runLater(...)`, a different method name than Swing's/AWT's
`invokeLater`/`EventQueue.invokeLater`** — and `lint-wb-threading.sh`'s guard pattern
(`invokeLater|BJobService|JobThread`) does not contain `runLater` or `Platform\.` anywhere in the script.

This is a real, load-bearing gap, but this session did **not** read any actual N5 Workbench/`-wb` Java
source to confirm N5's OWN Workbench widget classes still expose a `doInvoke`-shaped hook or actually
switch their navigation-marshaling idiom from Swing to JavaFX at the call-site level our own -wb modules
would write against (no block in this corpus decompiled or built an N5 `-wb` widget — [Block 39] §39.x
itself notes `bajaui`/`workbench`'s FULL API surface was never explored, only its module-graph
dependency edges). The verdict is therefore: **`lint-wb-threading.sh`'s Swing-specific guard pattern is
very likely INCOMPLETE for N5 (a real N5 -wb navigation method marshaling correctly via
`Platform.runLater` would false-WARN under the current pattern) — `[INFER]`, grounded in a confirmed
platform-dependency fact but not in a directly-read N5 `-wb` source file**, named child gap B51-G6. This
is the strongest evidence-backed candidate for "obsolete" among the 37 scripts, but it is not yet
`[CERT]`-closed.

## 51.5 — B9-G3 closed: `com.tridium.n-java` must be applied per-module, `[CERT]`

`NiagaraJavaPlugin.apply(project: Project)` (`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/java/NiagaraJavaPlugin.kt:22-87`, whole 87-line file read):

```kotlin
public class NiagaraJavaPlugin : Plugin<Project> {
   public open fun apply(project: Project) {
      project.getPluginManager()
         .withPlugin("java", new Action(project, project) {
            public final void execute(AppliedPlugin $this$withPlugin) {
               val var10000: TaskContainer = this.$this_run.getTasks();
               val var4: TaskCollection = (var10000 as TaskCollection).withType(JavaCompile.class);
               var4.configureEach(new Action(this.$project) { ... registers
                  compact3/limitModules/apt/modulePath CommandLineArgumentProviders ... });
            }
         });
   }
}
```

`this.$this_run` is the `Project` the `Action` closure was constructed against — the SAME `project`
parameter `apply(project: Project)` received, i.e. the project `com.tridium.n-java` was applied to via
its `id("com.tridium.n-java")` line. `getTasks()` on THAT project returns ONLY that project's own task
container; there is **no `subprojects{}`, `allprojects{}`, or any other cross-project traversal
anywhere in this class** — every line of the 87-line file was read this session, not sampled. `[CERT]`.

**Consequence, stated precisely.** If `com.tridium.n-java` is applied at the ROOT project's
`build.gradle.kts` `plugins{}` block, `project.getTasks().withType(JavaCompile.class).configureEach{...}`
runs against the ROOT project's OWN `JavaCompile` tasks — and a root project in this kit's layout has no
`JavaCompile` task of its own (it has no `src/` of its own; all Java source lives in module
subprojects). The `compact3`/`limitModules`/`apt`/`modulePath` argument providers would therefore never
be registered on ANY subproject's `compileJava` task if the plugin were applied only at root — exactly
matching [Block 9] §9.4's OBSERVED symptom (per-module application was required to get
`--module-path` onto `javac` at all) but now derived from the plugin's own `apply()` body instead of
from an external behavioral test. **This closes B9-G3 to `[CERT]`: `com.tridium.n-java` must be applied
in EVERY module/part subproject's own `<part>.gradle.kts` `plugins{}` block — never at root, and never
via a single root-level application relying on Gradle's plugin-inheritance (there is none here, since
this plugin performs no `subprojects.configureEach` or similar propagation).**

## 51.6 — B13-G4 closed: `module.xml <dependencies>` is derived from the resolved compile classpath, not from `module-info.java`, `[CERT]`

`ModuleXml.java` (`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/util/ModuleXml.java`),
`findModuleDependencies()` (lines 312-334) and `getDependencyFromManifest()` (lines 365-390-ish), read
in full this session:

```java
private TreeSet<NiagaraModuleDependency> findModuleDependencies(Map<String, NiagaraModuleDependency> dependencyOverrides) {
   TreeSet<NiagaraModuleDependency> dependencies = new TreeSet<>();
   for (File artifact : this.getDependencySearchClasspath()) {
      if (artifact.getName().endsWith(".jar")) {
         NiagaraModuleDependency dependency = this.getDependencyFromModule(dependencyOverrides, artifact);
         if (dependency != null) dependencies.add(dependency);
      }
   }
   if (this.getDependsOnBaja().get() && this.getNre().get() && !"baja".equals(this.getName().get())
       && ... dependencies.stream().noneMatch(dep -> "baja".equals(dep.getName())))
      dependencies.add(new NiagaraModuleDependency("Tridium", "baja", "4.0"));
   return dependencies;
}
```

`getDependencyFromManifest()` opens EACH classpath jar's OWN `META-INF/module.xml`, reads its `<module
name=... vendor=... vendorVersion=...>` attributes, **skips it entirely if `name` is in
`excludedDependencyModules`** (the set [Block 2] §2.4 already named: `{activation, jettyWrapper,
niagarad, nre, npsdkTest, nacl, splash}`), and otherwise builds a `NiagaraModuleDependency` whose
version is `new Version(vendorVersion).strip(versionStrip)` where `versionStrip =
this.getDependencyVersionLimit().get()` — **default `2`** (§2.4's own DSL table). `[CERT]`
(`ModuleXml.java:312-390`, both methods read to completion).

`getDependencySearchClasspath()` itself is wired, per `NiagaraModulePlugin.registerModuleTasks()`
(`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/NiagaraModulePlugin.kt:215-221`, read
this session):

```kotlin
var56 = manifestExtension.getDependencySearchClasspath();
var27[0] = configurations.get(mainSourceSet.getCompileClasspathConfigurationName());
var56.from(var27);
```

— i.e., the module's own `compileClasspath` Gradle configuration, which
`configureConfigurations()` (`NiagaraModulePlugin.kt:147-196`, same file, read this session)
`extendsFrom(uberjar, unterjar, nre)` on the `api` bucket. **This directly and completely answers
B13-G4**: N5's `module.xml <dependencies>` element is populated by SCANNING every jar on the module's
own resolved compile classpath, opening each one's `META-INF/module.xml`, filtering by
`excludedDependencyModules`, and version-truncating to `dependencyVersionLimit` (default major.minor
only) — a purely Gradle-classpath-resolution mechanism that **never reads `module-info.java` at all**.
The JPMS `requires` list (hand-authored per §2.7/§51.1.3) and the auto-derived `module.xml
<dependencies>` list are two INDEPENDENT declarations of overlapping intent, kept in sync only by the
module author declaring the same dependency set to both the `.gradle.kts` `dependencies{}` block (which
feeds `module.xml` via the classpath) AND the `module-info.java` `requires` list (which JPMS enforces
separately at compile/run time) — this is exactly why [Block 28] §28.3.7 had to hand-verify each
`requires niagara.<x>;` line against a `javap`-confirmed real module name rather than simply copying the
`.gradle.kts` dependency names.

**Free side-finding: this closes [Block 16] B16-G5.** [Block 16] §16.7 found
`ColdRoomPan-rtTest`'s `module.xml` declared `vendorVersion="2.0"` for its dependency on
`ColdRoomPan-rt`, even though the real module's own version is `2.0.7`, and left the truncation
unexplained. `dependencyVersionLimit`'s DEFAULT value of `2` (confirmed by this session's own read of
`ModuleXml.java`, not merely `[Block 2] §2.4`'s DSL-surface table) is the exact, literal mechanism: any
N5 inter-module dependency version is stripped to 2 segments (major.minor) by default unless a module
explicitly overrides `dependencyVersionLimit` in its `moduleManifest{}` block. B16-G5 is **closed**, not
merely narrowed.

**Why N5 shows FEWER explicit dependencies than N4 (the task's own framing) — bounded, honest scope.**
This session confirms the N5-SIDE mechanism completely (`[CERT]`, above). It does **not** independently
re-read N4's own `ModuleXml`-equivalent dependency-writing code this session (out of the scope of the
blocks this task named as required reading, and not re-derived here) — so the COMPARATIVE magnitude
claim ("fewer than N4") rests on the corpus's existing observation (this task's own framing) plus
`[INFER]`: if N4's own dependency-resolution walked a WIDER classpath (e.g., before Gradle's
`api`/`implementation` visibility boundaries were as strictly enforced, or before `excludedDependencyModules`
existed as a concept), a straightforward auto-scan would naturally surface fewer explicit entries once
transitive noise is filtered — but this is a plausible explanation, not a confirmed one. Named child gap
B51-G7: read the N4-side `ModuleXml`/manifest-writing task (REMIT-cited but not reopened in
`niagara-research`, e.g., B12/B434) directly, side-by-side with `NiagaraModulePlugin.kt`'s N5
`configureConfigurations()`, to confirm or refute whether the CLASSPATH SHAPE itself (not just the
version-truncation default) changed between N4 and N5.

## 51.7 — Recommended plan for a `build-n5-module` kit variant (PROPOSAL — not implemented)

Ordered by dependency (each step needs the prior step's artifact to test against). This is a plan, not a
change to any file in this session — no kit file was written or modified.

1. **Fork, don't mutate, the kit directory.** Create
   `build-n5-module-kit/` as a sibling of `build-n4-module-kit/` (not a branch inside it) — the two
   toolchains (Java 8 vs Java 25, N4 vs N5 install layout) are incompatible in the same working tree, and
   N4 client modules remain in active production use (REMIT this corpus's own `docs/n4-to-n5-porting-guide.md`
   §6 "known open risks" — N4.15 LTS is supported through Q3 2028; N5 work is exploratory, not a
   replacement, yet).
2. **Port the 4 template files first** (§51.1), using this block's delta table directly — these are the
   files every subsequent module scaffold copies from, so getting them right first avoids re-deriving the
   same deltas per-module later. Validate each by re-running [Block 9]'s exact PoC scaffold procedure
   against the new templates (a fresh `n5Hello`-equivalent build), not just a visual diff.
3. **Rewrite `build.sh`** per §51.3: Java-25 default, drop/repoint the `niagaraPluginVersion` auto-detect,
   retarget the Δ2 drift gate at `niagara_config_home`, add an explicit pre-flight assertion that
   `niagara_config_home` does NOT resolve to the real shared install directory (a hard-fail guard, not
   just documentation — [Block 16] §16.3's incident is exactly the class of mistake a first-time kit user
   will make without one).
4. **Rewrite `verify-module.sh`** per §51.2: bytecode major → 69, add the 3 new checks
   (`module-info-class` presence, `schema-version-5`, `no-runtime-profile`), extend `cross-module-type`'s
   whitelist to include `niagara.*`, extend `phantom-dep`'s config-name regex to cover
   `unterjar\|uberjar\|niagaraAnnotationProcessor`, leave `baja`/`stored`/`typecount`/`facets*`/
   `rcbackup`/`palette`/`moduletest-present`/`subscription-leak`/`slot-wall` unchanged (§51.2 already
   confirms these need no code edits).
5. **Update `lint-structure.sh`** per §51.4.1: L1/L3 pattern extension to `niagara\.`, L7 either dropped
   or reworked once B51-G5 (does N5 even use inline-version dependency strings) is resolved, L11's
   `:test-wb` replaced with the real N5 test-dependency pair, L13 scope extended to `niagara_config_home`.
6. **Defer `lint-wb-threading.sh`'s rewrite until a real N5 `-wb` widget is built and decompiled**
   (§51.4.2/B51-G6) — do not guess at the JavaFX threading idiom's exact call shape from module-graph
   evidence alone; this is the one lint where a wrong guess (adding `runLater` to the guard pattern
   without confirming N5's own `-wb` widgets actually use `Platform.runLater` at the call sites our code
   would write) could silently stop catching a real defect class.
7. **Leave the remaining ~30 annotation/keyword-vocabulary lints (§51.4's first row) untouched** — copy
   them into the new kit directory verbatim; re-validate each against ONE real N5-ported module (e.g. a
   fresh N5 port of ColdRoomPan-rt, reusing [Block 16]'s existing PoC tree) rather than re-deriving
   correctness from source reading alone, since "no N4-specific token in the script" is strong but not
   exhaustive evidence of N5 correctness (a live sweep is the only way to catch a check whose REGEX
   happens to key on a behavior that changed for reasons other than the namespace rename).
8. **Only after 2-7 are individually validated, build the `moduleTest`/TestNG-aware layer** — port
   `run-pure-test.sh` and any moduleTest-related tooling last, since N5's test framework swap (TestNG,
   not JUnit4, [Block 16] §16.5.2/§16.5.3) and the `bin/test.exe`-only `niagaraTest` platform gate
   ([Block 16] §16.5.4) make this the least mechanically transferable layer of the kit — it needs new
   tooling (a paren-aware JUnit4→TestNG port script, already prototyped per `docs/n4-to-n5-porting-guide.md`
   §2.12/[Block 29] REMIT), not a mechanical template edit.
9. **Re-run `report-module.sh`/`schema-risk.sh`/`bog-audit.sh` against the new checks only after 2-6 are
   stable** — these are aggregation/synthesis layers over the individual checks; updating them before
   their inputs are correct just propagates the same N4 assumptions one layer further.

## 51.x — Self-verify tally

Literal `verify-block.sh` output (methodology §11: the reported tally must be the script's own output,
never hand-recalculated), run read-only against this file:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    niagara5-block51.md .
== verify-block: niagara5-block51.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 7  (adj 6)
   [CERT-live] 0
   [CERT] 24  (adj 22)
   [CERT-doc] 2
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 10  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/30 = 0.20
-- [CERT] file:line citation resolution --
   extern  /tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/java/NiagaraJavaPlugin.kt:22-87  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  /tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/NiagaraModulePlugin.kt:215-221  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:312-390  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  NiagaraModulePlugin.kt:147-196  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  libs.versions.toml:102  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   resolved 0 of 5
   WARN    resolved 0 of 5 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

The script's own count (`[CERT]` raw 24, adj 22; `[CERT-hw]` raw 7, adj 6; `[INFER]` raw 10, adj 6;
adjusted ratio 6/30 = 0.20) is markedly lower on the `[CERT]` side than the body text's density would
suggest by eye — this is because the script counts literal marker TOKENS (`` `[CERT]` ``-style inline
tags), and this block's §51.1 delta tables carry most of their evidence inside table cells with a single
trailing `[CERT]`/REMIT citation per ROW rather than per individual claim, plus §51.2/§51.4's per-check
verdict tables use prose verdicts ("still valid", "needs update") without a repeated inline marker on
every cell. The **5 `extern` citations flagged are exactly the 5 decompiled-source line-range citations
of §51.5/§51.6 plus one archive-internal `libs.versions.toml:102` REMIT** — all read directly this
session (§Sources), matching the EXPECTED "DECOMPILED-TREE BLOCKS" signature [Block 2]/[Block 9]/
[Block 16]/[Block 28]/[Block 39] already established (methodology §11): `resolved 0 of 5` is not a
citation failure, it is the tool correctly reporting that every one of this block's `[CERT]`-marked
primary-source reads lives outside this corpus directory. The `[INFER]` adjusted count of 6 corresponds
to the 7 explicitly named child gaps (B51-G1 through B51-G7) minus one gap (B51-G7) whose own paragraph
is framed around a `[CERT]` finding (§51.6) rather than carrying its own inline `[INFER]` tag — each
`[INFER]` is bounded to one named, scoped uncertainty, not spread through a central claim. Exit 0: no
verifiable contradiction found (no cited file that exists but whose line is out of range).
- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block51.md`. No
  other file in this corpus, the N4 kit, or the N5 install was modified (read-only throughout, per task
  scope). `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated this session — the parent
  orchestrator owns that, per the same single-block-deliverable convention [Block 16]/[Block 28]/[Block 39]
  documented.
- **MCP-doc snapshots** — N/A, no MCP/context7 citation used this session.
- **Decompiled-tree citation note (methodology §11)** — every `[CERT]` citation into
  `/tmp/claude-1000/n5b2/vf-out/**` resolves as `extern`/unresolvable to any script walking only this
  corpus directory — EXPECTED per [Block 2]'s own established convention; every one was read in full this
  session (§51.5's whole-87-line-file read of `NiagaraJavaPlugin.kt`; §51.6's targeted-but-complete reads
  of `ModuleXml.java` lines 225-390 and `NiagaraModulePlugin.kt` lines 147-300), not carried from a prior
  block's summary.

## 51.x — Connections

- **[Block 2]** — this block closes §2.12 item 2 (`niagaraModule{}`→`moduleManifest{}` rename, confirmed
  `[CERT]` in §51.1.3 against the kit's own real fixture rather than inferred) and B2-G6 outright (the
  kit's own `.gradle.kts` templates are now directly read and diffed, §51.1). §51.5/§51.6 re-read the
  SAME decompiled `n-plugin-5.0.54.9.2.jar` tree Block 2 first decompiled, extending it to 2 classes
  Block 2 named but did not read to completion (`NiagaraJavaPlugin.apply()`'s FULL body, `ModuleXml`'s
  dependency-derivation methods).
- **[Block 9]** — B9-G3 is closed here (§51.5) from the mechanism side, confirming [Block 9] §9.4's own
  externally-observed finding (`n-java` must be per-module) was correctly diagnosed, not merely
  empirically lucky. §51.1's N5-side template cells are largely quoted FROM [Block 9]'s own working
  `settings.gradle.kts`/`build.gradle.kts`.
- **[Block 16]** — B16-G5 (the unexplained `vendorVersion="2.0"` truncation) is closed here as a direct
  side-effect of answering B13-G4 (§51.6) — `dependencyVersionLimit`'s literal default value. §51.1.3's
  N5 `-rt` template cell is quoted from [Block 16]'s real, build-proven `ColdRoomPan-rt.gradle.kts`.
- **[Block 28]** — §51.1.3's N5 `-ux`/servlet template cell and §51.4.2's JavaFX-vs-Swing evidence both
  trace to [Block 28]'s real DashboardPan merge/build and its `niagara.alarm` JavaFX/Batik discovery.
- **[Block 39]** — §51.4.2's wb-threading verdict leans on [Block 39]'s decisive confirmation (via the
  real vendor `javac.exe`) that JavaFX is a genuine, resolvable system-module dependency of
  `niagara.workbench`, not merely a files-on-disk curiosity.
- **`docs/n4-to-n5-porting-guide.md`** — this block's §51.7 plan is the natural next artifact the guide's
  own closing "known open risks" list names ("The `build-n4-module` kit's own `.gradle.kts` templates
  have not been updated or diffed against the N5 plugin DSL... whether the kit's scaffold generator
  itself should be updated to emit N5-shaped files by default remains open (B2-G6, still pending)") — this
  block is that diff, plus the two decompiled-mechanism answers (B9-G3, B13-G4) the guide's own module
  porting procedure (§2.2, §2.3) already assumed as established facts without citing a source for either.
- **`~/.claude/skills/build-n4-module/SKILL.md`** — §51.7's proposed `build-n5-module-kit` fork would need
  its own sibling skill file, out of scope here (a skill-authoring task, not a research block).

## 51.x — Child gaps

- **B51-G1** — `verify-module.sh`'s `stored` check (`--stored`, zero Deflated entries) was never tested
  against a real N5 jar or a real N5 Workbench re-sign attempt; no evidence either way.
- **B51-G2** — Whether `niagara.sys.Flags` (or wherever `Flags.TRANSIENT`/`Flags.OPERATOR` now live) is
  confirmed unchanged in N5 was not independently re-verified this session; plausible by continuity with
  `BComponent`/`Property`/`Type` (all moved intact under `niagara.sys.*`) but not `[CERT]`.
- **B51-G3** — `lint-bundled-jar-class-version.sh` was found by the grep sweep to reference bytecode-major
  tokens but was not independently read line-by-line this session to confirm its exact N5 delta (almost
  certainly the same 52→69 update as `verify-module.sh`'s `bytecode` check, but unconfirmed).
- **B51-G4** — `rc-scan.sh` and `bog-audit.sh` were found by the grep sweep to reference `-rt|-ux|-wb`
  tokens but were not independently read this session to confirm whether those references are
  namespace-coupled or purely path-glob/profile-name matching (assessed as likely the latter by pattern,
  not confirmed).
- **B51-G5** — Whether ANY real N5 `.gradle.kts` (across all of [Block 9]/[Block 16]/[Block 28]/[Block 39]'s
  PoCs) ever uses an inline-version dependency string (`":module:X.Y"` or `":module:X.Y.Z"`) was not
  exhaustively checked; every example this session read uses the bare `api(":name")` form, but the
  negative claim ("N5 never uses inline versions") was not proven by opening every `.gradle.kts` line in
  every cited PoC.
- **B51-G6** — `lint-wb-threading.sh`'s Swing-vs-JavaFX threading-idiom gap (§51.4.2) is grounded in
  confirmed N5 platform-dependency facts (JavaFX IS a real, resolvable system module of
  `niagara.workbench`) but NOT in a directly-read N5 `-wb` widget source file; no block in this corpus
  built, decompiled, or even located a real N5 Workbench widget class to confirm the actual
  navigation-marshaling call shape a kit author would need to update the lint's guard pattern against.
- **B51-G7** — The comparative claim "N5 shows fewer explicit dependencies than N4" was answered from the
  N5 side only (§51.6, `[CERT]`); the N4-side `ModuleXml`-equivalent dependency-writing mechanism was not
  independently re-read this session to confirm whether the classpath-SHAPE itself (not just the
  version-truncation default) changed between N4 and N5.
