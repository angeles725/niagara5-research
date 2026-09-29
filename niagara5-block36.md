# Block 36 — The N5 JavaScript build pipeline (node, grunt, RequireJS) for module web resources

> Closes child gap **B2-G5**: what the `com.tridium.node`/`rpno`/`yarn-ws`/`yarn-ws-agg`/`grunt` Gradle
> plugins actually DO for a Niagara 5 module that ships JS web resources (`-ux`-style). Covers: whether a
> `node` binary is bundled or auto-downloaded, how `node`/`npm`/`yarn`/`grunt` commands are actually
> invoked by the Gradle tasks, the Node/Yarn-Workspace root-vs-module split, the `gruntBuild`/`gruntCi`/
> `gruntIntegration` task set and what each runs, what the devkit New-Module-Wizard templates actually
> scaffold for a `$javascriptModule`, and the official `docDeveloper.jar` doc coverage of the same
> pipeline. Also answers the practical question for **DashboardPan-ux** (plain static `rc/` HTML/JS, no
> `package.json`/`Gruntfile.js`): is this whole pipeline optional. Does **not** cover `com.tridium.npsdk-
> native`/`native`/`native-agg` (confirmed unrelated — a C/C++ NPSDK build, only co-located in the same
> jar's package tree, §36.8) or a live `gradle gruntBuild`/`gruntCi` run against a real Node/npm install
> (no runnable Niagara install in this environment — same constraint as Blocks 2/4/21).
>
> Subject version: **Niagara 5.0.0.28 (Beta)**, Gradle plugin artifacts at version `5.0.54.9.2`. Install
> root: `/mnt/c/Program Files/Niagara/5.0.0.28`; config/modules root:
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`.
>
> Sources:
> - `/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/{grunt,node,yarn-ws,yarn-ws-agg,
>   rpno,npsdk-native}/**` — the 6 plugin-marker POMs (each a thin `packaging=pom` pointing at
>   `com.tridium.tools:n-plugin:5.0.54.9.2` — confirmed by direct read, §36.1).
> - `.../etc/m2/repository/com/tridium/tools/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar` (`sha256
>   eb9831b6…d93356`) — the one fat Kotlin jar implementing all of the above; decompiled whole-jar with
>   Vineflower 1.12.0 into `/tmp/claude-1000/n5b36/vf-out/` (scratch, not preserved — per METHODOLOGY §11
>   "decompiled-tree blocks" convention, citations into that tree are `extern`; this jar's sha256 is the
>   anchor). `javap -c -p -constants` (same JDK) used directly on individual `.class` files, unzipped to
>   `/tmp/claude-1000/n5b36/classes2/`, wherever Vineflower emitted `<unrepresentable>`/`$VF: Couldn't be
>   decompiled` for a lambda body (the interpreter-selection and error-message logic in §36.2/§36.3).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/devkit.jar` (`sha256 a0fef522…9d3624`) —
>   `rc/gradle.properties.vm` and its bundled `LIB-INF/n-templates-5.0.54.9.2.jar` (`sha256
>   285e6463…2bb2405`): `gradle/module/module.gradle.kts.vm`, `gradle/includes/niagara/modulePlugins.vm`,
>   `gradle/settings.gradle.kts.vm`, and the `NiagaraModuleProjectGenerator.class`/
>   `GradleProjectGenerator.class` wizard-generator classes (decompiled the same way, into
>   `/tmp/claude-1000/n5b36/templates-vf/`).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` — full `doc/` tree
>   unzipped and grepped for `grunt`/`npm`/`yarn`/`node.js`/`jsdoc`/`bajaux build` (§36.7).
> - N4 remittances (READ, not re-derived — cited `REMIT`): `niagara-research` B1132, B1119, B957, B1028,
>   B1016, B960, and a `corpus-nav.py find` census confirming NO N4 corpus hit for `com.tridium.node`,
>   `yarn-ws`, or `npmLocalInstall` (an absence-in-corpus-text finding, not a claim about N4's actual
>   source — flagged `[INFER]`).
>
> Method: `unzip`/`python3 zipfile` POM/jar inventory; Vineflower 1.12.0
> (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar` on
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`) whole-jar decompilation; `javap -c -p -constants`
> (same JDK) for bytecode-level confirmation of lambdas Vineflower could not reconstruct as Kotlin source;
> `strings` sweep of the unzipped `node`/`grunt`/`niagara/service` class files for download-URL evidence
> (none found, §36.2); direct `Read`/`grep` on extracted devkit templates and the HTML-stripped
> `docDeveloper` tree; `python3 tools/corpus-nav.py find <term>` against the N4 corpus for remittance/
> delta lookups. Markers (METHODOLOGY §3): `[CERT]` local primary source (`file:line`/zip-entry path) ·
> `[CERT-doc]` official installed doc, full basename · `[INFER]` deduction · `REMIT` = cited from a prior
> corpus block, not re-opened this session.
>
> N5 build-toolchain layer. Connects [Block 2] (parent block — plugin inventory, this block is its named
> child gap B2-G5), [Block 21] (N5 UI stack — bajaux/bajaScript/AMD confirmed still RequireJS in N5, this
> block is the build-time producer of that `rc/` output).
>
> **Type:** mixed — §§36.1–36.8 are direct evidence (`[CERT]`/`[CERT-doc]`) from this session's own
> decompilation and template reads; §§36.9–36.10 are synthesis comparisons against `[Block]`-external N4
> corpus material, cited `REMIT`.
>
> **Breakthrough:** the plugin's own first-party error string, read directly out of
> `CheckNodePackageGloballyInstalled.findPackage()`'s bytecode, settles the gap's central question in the
> vendor's own words: *"Could not start 'npm'. Ensure 'node' and 'npm' are available on your PATH, or set
> the Gradle property 'nodeHome' to the absolute path of a valid installation of node.js"* — N5 ships
> **zero** bundled or auto-downloaded Node; every JS-build task (`node`, `npm`, `yarn`, `grunt`) is
> resolved through `/usr/bin/env`/`cmd` against a Node install the developer supplies via PATH, `nodeHome`,
> or `NODE_HOME` (§36.2/§36.3), with a `<projectRoot>/node` convention-fallback if none is set.

---

## 36.1 — Confirmed: all 6 gap-named plugin ids live in ONE fat jar, `npsdk-native` included `[CERT]`

Every plugin marker POM under `etc/m2/repository/com/tridium/{grunt,node,yarn-ws,yarn-ws-agg,rpno,
npsdk-native}/` is a thin `packaging=pom` artifact whose sole dependency is
`com.tridium.tools:n-plugin:5.0.54.9.2` — identical structure to the 27-plugin inventory already
established in [Block 2] §2.1. `[CERT]` (direct read of all 6 POMs, this session). The implementation
classes for all of them live inside `n-plugin-5.0.54.9.2.jar` under three sibling packages:
`com.tridium.gradle.plugins.node.*` (Node/Yarn, 40 top-level classes + nested), `com.tridium.gradle.
plugins.grunt.*` (Grunt, 26 top-level classes + nested), `com.tridium.gradle.plugins.natives.*` (native/
NPSDK C build — confirmed OUT OF SCOPE for this gap, §36.8). `[CERT]` (`python3 zipfile` namelist filter
on the three package prefixes, 252 `.class` entries total, this session; jar has 724 `.class` entries
overall).

## 36.2 — Node is never bundled or downloaded: PATH / `nodeHome` / `NODE_HOME` only `[CERT]`

`NiagaraEnvironmentSpec.wireFromProviders()` resolves `nodeHome` in this exact precedence: the `nodeHome`
Gradle property → the `nodeHome` JVM system property → the `NODE_HOME` environment variable — with **no**
download step anywhere in the chain. `[CERT]`
(`com/tridium/gradle/plugins/niagara/service/NiagaraEnvironmentSpec.kt:28-32`, decompiled). If none of the
three is set, `NiagaraEnvironmentService`'s `configurationConvention()` helper falls back to a
project-relative default directory named literally `"node"` (i.e. `<projectRoot>/node`) — the same
pattern used for `niagaraHome`/`niagaraUserHome`/`niagaraConfigHome` falling back to
`niagara/niagara_home` etc. `[CERT]` (`NiagaraEnvironmentService.kt:64-70`, decompiled).

A `strings` sweep of every `.class` file under the `node`/`grunt`/`niagara/service` package prefixes for
download-URL indicators (`nodejs.org`, `.tar.gz`/`.zip` install-archive patterns, `download`, `registry`,
`mirror`) returned **zero hits** beyond the literal strings `"node_modules"`/`"lib/node_modules"`. `[CERT]`
(`strings` over the unzipped class tree, this session) — unlike the well-known third-party
`com.github.node-gradle.node` Gradle plugin (which downloads a pinned Node distribution from
nodejs.org/dist), Tridium's `com.tridium.node` plugin has **no download code path at all**.

`CheckNodeInstalled` (the `com.tridium.node` plugin's verification task) confirms this operationally: its
`check()` task action either does a "quick check" (just checks a file exists under `nodeHomeDirectory`) or
calls `findNodeVersion()`, which execs the resolved `node` executable with `--version` and throws
`InvalidUserDataException("No valid node version was found, please install one")` if it can't run it —
there is no fallback to fetch one. `[CERT]` (`CheckNodeInstalled.kt:60-105`, decompiled;
`findNodeVersion()` body confirmed via `javap -c` bytecode read since Vineflower could not reconstruct the
anonymous-class lambda, §36 header).

The single clearest first-party confirmation is `CheckNodePackageGloballyInstalled.findPackage()`'s own
exception message (this class checks that a **globally npm-installed** package like `grunt-cli` or `yarn`
is present — §36.4), read verbatim out of its `makeConcatWithConstants` bootstrap args via `javap`:

> *"Could not start 'npm'. Ensure 'node' and 'npm' are available on your PATH, or set the Gradle property
> 'nodeHome' to the absolute path of a valid installation of node.js. You can set the 'nodeHome' property:
> In your global gradle.properties file / In the project-specific gradle.properties file / By passing
> "-PnodeHome=…" when invoking Gradle"* `[CERT]`
> (`com/tridium/gradle/plugins/node/task/CheckNodePackageGloballyInstalled.class`, `findPackage()`
> catch-block string constant, `javap -c -p -constants` output, this session).

This is the tagged **Breakthrough** for this block: it is the vendor's own error text, not an inference —
Node is a **bring-your-own** dependency in N5, exactly as it already was documented for N4 (`nodeHome` in
`gradle.properties` — REMIT `niagara-research` B1016 §25/29, B960 §63/109, B817 §154 — all pre-existing N4
client scaffolds pin `nodeHome=C:\Program Files\nodejs`). N5 changes nothing about this contract; it adds
Gradle-level plumbing (`CheckNodeInstalled`/`CheckNodePackageGloballyInstalled` verification tasks,
§36.4) around the SAME bring-your-own-Node model.

## 36.3 — How `node`/`grunt`/`npm`/`yarn` are actually invoked: `cmd /c` / `/usr/bin/env --` `[CERT]`

Every JS-build task (`NodeExec`, `GruntExecTask` and its subclasses, `NpmExecTask`, `YarnInstall`) extends
`JavaScriptTask` → `NiagaraEnvironmentAwareExec` → `InterpreterExecTask`. `InterpreterExecTask.
getExecutable()`/`getArgs()` build the process invocation as **`interpreter` + `interpreterArgs` +
`command` + `commandArgs`** whenever `interpreter` is set. `[CERT]`
(`com/tridium/gradle/plugins/task/InterpreterExecTask.kt:25-54`, decompiled).
`NiagaraEnvironmentAwareExec`'s constructor wires the `interpreter`/`interpreterArgs` conventions to two
platform-selecting `Transformer`s, read via `javap -c` since Vineflower could not reconstruct the anonymous
Kotlin lambda classes:

| Property | Windows value | POSIX/Linux value | Citation |
|---|---|---|---|
| `interpreter` | `"cmd"` | `"/usr/bin/env"` | `NiagaraEnvironmentAwareExec$1.transform()`, `javap -c` |
| `interpreterArgs` | `["/c"]` | `["--"]` | `NiagaraEnvironmentAwareExec$2.transform()`, `javap -c` |

`[CERT]` (both read via `NiagaraPlatform.selectForPlatform("interpreter command"/"interpreter args", …)`
bytecode, this session). So `GruntExecTask` setting `command = "grunt"` resolves, at exec time, to
`cmd /c grunt <args>` on Windows or `/usr/bin/env -- grunt <args>` on POSIX — i.e. the actual `node`/
`grunt`/`npm`/`yarn` binary is looked up through the **process environment's `PATH`**, not a hardcoded
absolute path baked into the plugin. `getEnvironment()` (`NiagaraEnvironmentAwareExec.kt:19-23`) delegates
to `NiagaraEnvironmentService.addNiagaraEnvironment()`, which — when `nodeHome` is present — **prepends**
`nodeHome`'s (Windows) or `nodeHome/bin`'s (POSIX) absolute path to `PATH` before the process launches.
`[CERT]` (`NiagaraEnvironmentService.kt:103-123`, decompiled). This is the mechanism that makes the
`nodeHome` property actually take effect: it does not point the plugin AT a binary, it front-loads `PATH`
for the child process.

**`-Pskipjs=true` is a real escape hatch.** Every `IJavaScriptTask` (the common interface for all node/
grunt tasks) carries a `skipjs` property wired via `JavaScriptTaskKt.wireSkipJsConvention()` to the
`skipjs` Gradle property; when its lower-cased value is `"true"`, `onlyIf { !jsDisabled() }` skips the
task entirely. `[CERT]` (`com/tridium/gradle/plugins/node/task/JavaScriptTaskKt.class`, `jsDisabled()`
body read directly since Vineflower decompiled that one cleanly — `JavaScriptTaskKt.kt:42-60` — the
`wireSkipJsConvention` gradleProperty wiring confirmed via `javap -c` for the one `<unrepresentable>`
segment). A module or a whole build can therefore disable every Node/Grunt task with one property, without
removing the plugin from `plugins{}`.

## 36.4 — Root-vs-module split: Yarn Workspaces, not per-module `node_modules` `[CERT]`

`com.tridium.node`'s `NodePlugin` (per-module) just wires 3 legacy-cleanup/local-install task names
(`npmLocalInstall`, `cleanLegacyJs`, `cleanNodeModules` — constants only, `NodePlugin.kt:19-22`) and
applies the root project's `RootProjectNodePlugin`. `RootProjectNodePlugin` (root-only) registers, for
each of a fixed 3-entry `GlobalNodeModules` enum, a global-npm-install task and a globally-installed
check task:

| `GlobalNodeModules` entry | npm package | Purpose (inferred from name/co-located Karma code) |
|---|---|---|
| `YARN` | `yarn` | drives the workspace install (`yarnInstall` task, §36.1 `YarnInstall : NpmExecTask`) |
| `GRUNT_CLI` | `grunt-cli` | the `grunt` command every `GruntExecTask` shells out to (§36.3) |
| `PUPPETEER` | `puppeteer` | headless-Chrome driver for `gruntCi`'s Karma browser tests (§36.5 — `KarmaBrowser`/`chromeFlags`/`browsers` options exist in `GruntCiOptions`) |

`[CERT]` (`com/tridium/gradle/plugins/node/GlobalNodeModules.kt:6-19`, decompiled — task-name pattern
derived mechanically via `GradleExtensionsKt.camelCase(...)`, e.g. `yarnGlobalInstall`/
`checkYarnGloballyInstalled`). `YarnWorkspacePlugin` (per-module) explicitly **refuses to apply to the
root project** (`throw IllegalArgumentException("This plugin must not be applied to the root project of a
build")`, `javap -c` on its `apply()`), and publishes a `yarnWorkspaceElements` outgoing configuration.
`[CERT]` (`YarnWorkspacePlugin.kt`, bytecode dump, this session). `YarnWorkspaceAggregationPlugin` (root-
only — self-applies `com.tridium.node`) resolves the union of every module's `yarnWorkspaceElements` into
one `yarnWorkspace` configuration, registers a `writeWorkspacePackageJson` task, and wires the root-level
`npmLocalInstall`/`YarnInstall` task to depend on that resolved set. `[CERT]`
(`YarnWorkspaceAggregationPlugin.kt`, bytecode dump, this session). Net architecture: **one Yarn
Workspaces install at the multi-project build root**, not `npm install`/`node_modules` per module — every
JS-bearing module contributes its `package.json`'s dependency surface into a synthesized root workspace
`package.json`, and `yarn install` runs once for the whole build.

## 36.5 — Grunt: `gruntBuild`/`gruntCi`/`gruntIntegration`, wired to `com.tridium.n-module` `[CERT]`

`GruntPlugin.apply()` registers exactly 3 tasks (bytecode-confirmed, since Vineflower could not
reconstruct this lambda-heavy method):

| Task | Class | Registration point |
|---|---|---|
| `gruntBuild` | `GruntBuildTask` | unconditional, in `apply()` |
| `gruntCi` | `GruntCiTask` | unconditional, in `apply()` |
| `gruntIntegration` | `GruntCiTask` (same class, separate task instance) | unconditional, in `apply()` |

`[CERT]` (`GruntPlugin.class apply()`, `javap -c` bytecode: `TaskContainer.register("gruntBuild", …)`,
`.register("gruntCi", …)`, `.register("gruntIntegration", …)` calls, this session). All three are wired
through `project.getPluginManager().withPlugin("com.tridium.n-module", …)` — i.e. Grunt task
configuration only fires once the module plugin (§2.1) has also been applied, confirming `com.tridium.
grunt` is meant to sit ALONGSIDE `com.tridium.n-module` on a JS-bearing module, never standalone.
`GruntExecTask` (the `gruntBuild` base class) hardcodes `command = "grunt"`, `workingDir =
projectDirectory`, and captures stdout at INFO. `[CERT]` (`GruntExecTask.kt:14-19`, decompiled cleanly).
`gruntBuild.tasks(vararg)` appends to `commandArgs` — this is the method the devkit wizard template calls
with `tasks("babel:dist", "copy:dist", "requirejs")` (§36.6, confirmed already in [Block 2] §2.11).

`gruntCi`/`gruntIntegration` are both `GruntCiTask` (extends `GruntExecTask`), configured by a shared
private `configureTask()` extension that sets `group = "grunt"`, `description = "Run grunt ci"`, and
**`enabled = false` by default** — both are opt-in, not part of a default `gradle build`. `[CERT]`
(`GruntPlugin.configureTask()` body, `javap -c` bytecode, this session). `GruntCiOptions` (a
`CommandLineArgumentProvider` passed to `options(...)`) exposes ~30 properties that get serialized to
`--key=value` CLI args for the underlying `grunt` process: `niagaraHome`/`niagaraUserHome`/
`niagaraConfigHome`/`stationCwd`/`stationsDir` paths, `jUnitReportDir`/`jshintReportDir`/`jsdocDir`/
`complexityReportsDir`/`coverageReportsDir` output dirs, a `configFile` (a serialized Karma config, backed
by `KarmaConfig`/`KarmaBrowser`/`KarmaOptions` — all `JsonSerializable` DTOs with a `Gson` round-trip,
`JsonSerializable.kt`), a spun-up test station's `stationName`/`stationHost`/`stationHttpPort`(default
**9088**)/`stationHttpsPort`(default **9089**)/`stationFoxPort`(default **9911**)/`stationFoxsPort`/debug
port/suspend flag, `browsers`/`chromeFlags` (feeding the `puppeteer`-driven headless-Chrome Karma runner,
§36.4), and `testOnly`/`testNever`/`testOnlyTags`/`testNeverTags` filters. `[CERT]`
(`GruntCiOptions.kt:18-130`, decompiled cleanly — the full property list and `asArguments()` body). This
confirms `gruntCi`/`gruntIntegration` run a real **spun-up Niagara test station + Karma/JUnit/jshint/
jsdoc/complexity/coverage report pipeline**, not just a lint pass — matching the `srcTest/rc/stations/…`
test-station pattern already documented for N4's `grunt-niagara` (REMIT `niagara-research` B957 §957.5-6).

> **Correction (added by [Block 121], §121.7, §14 cross-block).** The three default ports (9088 / 9089 / 9911) are right but are not in `GruntCiOptions.kt`: that class only declares
> `Property<Int>`. The defaults are `private const val DEFAULT_STATION_*_PORT` in `GruntPlugin.Companion` (`GruntPlugin.kt:235-237`), inlined into the lambda class
> `GruntPlugin$configureTask$2` (`javap -c`: `getStationHttpPort` / `sipush 9088` / `Property.convention`); cite that bytecode, not the options class.
`configureTask()` also sets `NODE_PATH` on the task's environment to
`NodePluginKt.getGlobalNodeModulesDirectory(niagaraEnvironmentService)` — the platform-specific global
npm-modules dir (`<nodeHome>/lib/node_modules` on Linux, `<nodeHome>/node_modules` elsewhere) — so `grunt`
can resolve the globally-installed `grunt-cli`/`yarn`/`puppeteer` packages from §36.4 without a local
`node_modules`. `[CERT]` (`GruntPlugin.configureTask()` bytecode + `NodePluginKt.kt:17-35`, both this
session).

## 36.6 — What the devkit wizard actually scaffolds: a task hookup, not a JS project `[CERT]` + `[INFER]`

`NiagaraModuleProjectGenerator`'s constructor takes an `includeBajaux` boolean and, when true, sets
`context.put("javascriptModule", true)` for the Velocity template context — i.e. the New Module Wizard's
"include a `-ux` module part" checkbox is the literal trigger for `$javascriptModule`. `[CERT]`
(`NiagaraModuleProjectGenerator.java:12-23`, decompiled cleanly). Grepping every `.vm`/`.txt` template in
`n-templates-5.0.54.9.2.jar` for `grunt`/`node`/`yarn`/`javascript` returns exactly **2 files**:
`gradle/includes/niagara/modulePlugins.vm` (adds `id("com.tridium.grunt")` inside a `#if
($javascriptModule)` block — no version, no `com.tridium.node`/`yarn-ws` alongside it) and
`gradle/module/module.gradle.kts.vm` (imports `GruntBuildTask` and configures `tasks.named<GruntBuildTask>
("gruntBuild") { tasks("babel:dist", "copy:dist", "requirejs") }`, also gated on `$javascriptModule`).
`[CERT]` (`python3 zipfile` read of every `.vm`/`.txt` entry, this session — confirms and extends [Block
2] §2.11's citation of the same two snippets). **No template scaffolds `package.json`, `Gruntfile.js`, a
`karma.conf`, an `.eslintrc`, `src/rc/` JS boilerplate, or ANY JS source file** — the wizard's entire
JS-module contribution is: apply one Gradle plugin id, and pre-wire the `gruntBuild` task's argument list.
Everything downstream of that (writing `Gruftfile.js`, installing `grunt-niagara`'s task definitions,
authoring `rc/*.js`) is left entirely to the developer, matching N4's `grunt-init-niagara` CLI scaffolder
having no N5-devkit equivalent (REMIT `niagara-research` B1132 §19 — `grunt-init-niagara` is an **npm-side**
generator invoked by hand, not part of either N4's or N5's Gradle-wizard tooling).

**A concrete devkit-template gap, worth flagging as its own finding.** `gradle/settings.gradle.kts.vm`'s
`pluginManagement { plugins { … } }` block explicitly version-pins every OTHER plugin id the module-level
template can apply (`com.tridium.n-module`, `.sign`, `.bajadoc`, `.jacoco`, `.nap`, `.conv.n-repo`,
`.niagara`, `.vendor`, the `set.*` family) — but it does **not** list `com.tridium.grunt` (nor `.node`/
`.yarn-ws`/`.rpno`). `[CERT]` (full-text read of `gradle/settings.gradle.kts.vm`, this session — no `#if`
block or plugin-id string for grunt/node/yarn anywhere in the file). Since `id("com.tridium.grunt")` in
the generated `module.gradle.kts` carries no inline `version(...)` either (§36.5's `modulePlugins.vm`
excerpt), a project generated by the wizard with the `-ux`/JS checkbox checked would need the developer to
manually add a version pin for `com.tridium.grunt` to `settings.gradle.kts` before the generated build
would resolve — this is `[INFER]` (Gradle's actual plugin-resolution failure mode was not reproduced live,
no runnable install in this environment, same constraint noted in the block header) but the missing pin is
itself a directly-observed `[CERT]` fact about the template text.

## 36.7 — Official docs: `docDeveloper.jar` documents the JS pipeline in detail `[CERT-doc]`

The doc/ tree ships a dedicated `doc/js/buildingJS.html` guide plus `doc/requirejs.html` — both hit by a
grep for `grunt`/`npm`/`yarn`/`node.js`/`jsdoc`/`bajaux build` across the full unzipped tree, alongside
`doc/buildN5.html` (already the primary source for [Block 2]) and the full `doc/jsdoc/*` API-reference
tree generated FROM the shipped `-rc`/`-ux` JS source of `bajaScript`, `bajaux`, `webEditors`,
`driver`, `export`, `converters`, `batchJob`, and the `js` module itself (hundreds of per-file `jsdoc`
pages — i.e. `jsdoc` generation is a real, populated part of the N5 doc build, not a stub). `[CERT-doc]`
(`docDeveloper.jar` doc/ tree listing, this session — `doc/js/buildingJS.html` and `doc/requirejs.html`
basenames confirmed present by direct grep-hit path, full content not read line-by-line this session —
flagged as a shallower pass than [Block 2]'s `buildN5.html` read). This is the SAME guide family N4's
corpus already extracted extensively (REMIT `niagara-research` B1132/B1119, which cite `buildingJS.txt`
and `requirejs.txt` by line number for the grunt-niagara/RequireJS/Babel toolchain) — `[INFER]`: given N5's
`com.tridium.grunt` plugin is a direct id-rename of N4's `com.tridium.niagara-grunt` (confirmed alias in
[Block 2] §2.1 line 155: `com.tridium.niagara-grunt → com.tridium.grunt`), the N5 `buildingJS.html`/
`requirejs.html` content is very likely a near-identical revision of the N4 guides already excerpted in
B1132/B1119 — not independently re-read this session, named as child gap B36-G1.

## 36.8 — `npsdk-native`: confirmed unrelated (native C/C++ build, not JS) `[CERT]`

`com.tridium.npsdk-native`'s `NpsdkNativePlugin.apply()` configures a `NiagaraNativeExtension`'s
`platforms` container — entirely native-toolchain (gcc/Win32) machinery, sharing no code path with `node`/
`grunt`/`yarn`. `[CERT]` (`NpsdkNativePlugin.kt:9-21`, decompiled — confirms it only touches
`com.tridium.gradle.plugins.natives.*` types). It was named in the gap's directory list only because it
lives in the same `n-plugin` jar's sibling package tree (§36.1) — this block does not investigate it
further, matching the gap's own scope note ("native … module builds" explicitly out of scope, carried
over from [Block 2]'s header).

## 36.9 — N4 → N5 delta: `grunt-niagara` (npm package) survives as `com.tridium.grunt` (Gradle plugin id
rename); Node/Yarn-Workspace Gradle orchestration reads as N5-new `[CERT]` + `[INFER]` (synthesis)

The N4 corpus already documents, in depth, an npm-published `grunt-niagara` task set (lint/test/dist),
`grunt-cli` (`npm install -g grunt-cli`), and `grunt-init-niagara` (a scaffolding CLI for a fresh `-ux`
module) — all wired through a Gradle plugin id `com.tridium.niagara-grunt` whose `gruntBuild` task runs
`babel:dist → copy:dist → requirejs`, IDENTICAL task-name sequence to what this block found in N5's
`module.gradle.kts.vm` (§36.6). `REMIT` (`niagara-research` B1132 §§1-2, B1119 §§21-42, B957 §957.6). This
is the SAME toolchain lineage — [Block 2] §2.1 already confirmed `com.tridium.niagara-grunt` is a legacy
plugin-id alias resolving to N5's `com.tridium.grunt` — so the Grunt HALF of this pipeline (§36.5-36.6) is
continuity, not a rewrite.

The Node/Yarn-Workspace Gradle-level orchestration found in this block (§36.2-36.4: `CheckNodeInstalled`/
`CheckNodePackageGloballyInstalled` verification tasks, the `GlobalNodeModules` global-install/check-task
factory, `YarnWorkspacePlugin`/`YarnWorkspaceAggregationPlugin`'s root-aggregated Yarn Workspaces model)
has **no hit** in a `corpus-nav.py find` census of the N4 corpus for `com.tridium.node`, `yarn-ws`, or
`npmLocalInstall`. `[CERT]` (three `corpus-nav.py find` runs, this session, each returning "No matches" —
an absence-in-corpus-TEXT finding). This does **not** prove N4 lacked equivalent machinery (the exact N4
`n-plugin`/`settings` jars were not opened this session to check for a same-named class — the
negative-existence discipline in METHODOLOGY §3 applies), but combined with N4's corpus already treating
`nodeHome`/Node-on-PATH as a manually-maintained `gradle.properties` convention with NO Gradle-plugin-level
"is Node installed" check task ever mentioned across B1016/B960/B817/B815 (4 independent N4 build-scaffold
blocks), the more likely read is: **N5 formalizes Node/Yarn discovery and Workspace aggregation as
first-party Gradle plugins where N4 left it to `grunt-niagara`'s own npm-side tooling and a hand-set
`nodeHome` property.** `[INFER]`.

## 36.10 — Relevance for DashboardPan-ux: the entire pipeline is opt-in, and DashboardPan-ux opts out
`[CERT]` (synthesis, `REMIT`)

DashboardPan-ux is confirmed, by direct source inspection in the N4 corpus, to ship **zero** `package.json`,
`Gruntfile.js`, or Jasmine/Karma spec tree — a single pure-JUnit test for the Baja-free dispatcher, and
hand-authored raw `rc/` HTML/JS with no transpile/bundle step. `REMIT` (`niagara-research` B1028
§1028.3, B1119 §38/48). Nothing in this block's N5 findings changes that posture's viability:

- **No plugin is required to ship a `-ux` module with plain static `rc/` resources.** `com.tridium.grunt`/
  `.node`/`.yarn-ws` are only applied when the wizard's `$javascriptModule` flag is set (§36.6) or a
  developer adds them by hand (§36.1) — a module that never declares them never runs any Node/npm/Yarn/
  Grunt task, and `-Pskipjs=true` (§36.3) is available as a build-wide kill switch even on a build that
  DOES declare them elsewhere in a multi-module Yarn-Workspace root.
- **The cost of opting IN is real, not cosmetic.** Opting in means: a developer-supplied Node install
  (§36.2 — nothing is bundled), a root-level Yarn Workspaces aggregation touching every other JS-bearing
  module in the same multi-project build (§36.4 — NOT a module-local `node_modules`), and (for `gruntCi`/
  `gruntIntegration`, if enabled) a spun-up live Niagara test station on fixed default ports 9088/9089/9911
  (§36.5). None of that exists today for a hand-authored raw-`rc/` module.
- **The ES5-only consequence already known from N4 still holds by the same mechanism.** A module without
  the Grunt `babel:dist` step gets no transpile — whatever ES-level JS is authored is what ships verbatim.
  `REMIT` (`niagara-research` B1119 §§21-23/38, which already states this exact rule for N4's
  `grunt-niagara`/no-grunt-niagara split and names DashboardPan-ux/B1064/chihuahua as the no-grunt,
  ES5-mandatory case). Nothing decompiled in this block contradicts or changes that rule for N5 — the
  `babel:dist` task name is identical (§36.6), so the same decision rule applies unchanged.

**Conclusion for DashboardPan-ux specifically: the JS build pipeline is confirmed optional in N5, exactly
as it already was in N4, and DashboardPan-ux's existing no-Grunt/no-Node posture requires no N5-migration
change on this axis** — the only N5-relevant delta is that ADDING the pipeline later (e.g. to close the
Jasmine/Karma gap already logged against DashboardPan-ux in `niagara-research` B1028's client punch-list)
would, in N5, mean adopting `com.tridium.grunt`/`.node`/`.yarn-ws` (§36.5/§36.6) rather than N4's
`com.tridium.niagara-grunt`, with the added root-level Yarn Workspaces commitment from §36.4 as a new
consideration not present in the N4 punch-list's original scoping.

## 36.11 — Self-verification

`verify-block.sh niagara5-block36.md` was run against this file (literal output pasted, not hand-recalled).
Exit 0. Per the METHODOLOGY §11 "decompiled-tree blocks" convention, every `[CERT]` `file:line` citation
into `vf-out/`, `classes2/`, or `templates-vf/` (the Vineflower/`javap` scratch trees under
`/tmp/claude-1000/n5b36/`) classifies `extern` — the tool cannot follow paths outside the target
directory — so `resolved 0 of 14`. This is the EXPECTED signature, not a failure: `verify-block: 0
resolved (all extern — decompiled trees); citation gate = inline token-verify` for those 14 anchors,
each backed by the literal `Read`/`grep`/`javap -c -p -constants` output already quoted in §36.1-§36.8
above (no hand-recalled numbers).

```
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0   [CERT-live] 0   [CERT] 40 (adj 38)   [CERT-doc] 5 (adj 3)
   [CERT-web] 0   [CERT-a] 0   [INFER] 10 (adj 8)
-- ratio -- [INFER]/[CERT*] = 8/41 = 0.20
-- [CERT] file:line citation resolution -- resolved 0 of 14 (all extern — decompiled-tree, see above)
-- OCR-provenance flag -- (none)
== exit 0 ==
```

Ratio 0.20 is low for an evidence-dominant block — the gap was fully investigable with the local jars/
templates already on hand; no requires-execution blocker existed for the core "is Node bundled/
downloaded" question (§36.2's Breakthrough), only for the live-run confirmations named in §36.12's child
gaps.

Artifacts: this file exists at `/home/cristian/niagara5-research/niagara5-block36.md`. `CATALOG.md`,
`INDEX.md`, and `RESEARCH-STATE.md` updates and the backlog re-classification are left to the orchestrator
per this task's read-only/single-file mandate (no other file was touched this session).

## 36.12 — Child gaps

- **B36-G1** — `doc/js/buildingJS.html`/`doc/requirejs.html` were confirmed present and on-topic by grep
  but not read line-by-line this session (§36.7); a full read would either confirm or refute the
  `[INFER]` "near-identical to the N4 guide" claim and could surface any N5-specific wording (e.g. Yarn
  Workspaces, the new `com.tridium.node`/`yarn-ws` plugin ids) the N4 guide text would not mention. LOW-MED.
- **B36-G2** — requires-execution: actually run `gradlew gruntBuild`/`gruntCi` against a real Node install
  on a wizard-generated `$javascriptModule` project, to (a) confirm or refute the §36.6 plugin-version-pin
  gap actually blocks resolution as written, and (b) capture a live `gruntCi` Karma/JUnit report to ground
  the `GruntCiOptions` property list (§36.5) against real output. Blocked on a runnable N5 install +
  network/local npm registry access — same constraint noted across Blocks 2/4/21. MED.
- **B36-G3** — the actual `grunt-niagara`-successor npm package content (whatever provides the `babel:dist`/
  `copy:dist`/`requirejs` Grunt task definitions the Gradle plugin only ORCHESTRATES, §36.5) was not
  located or inspected this session — it is presumably still `grunt-niagara` (or a renamed npm-registry
  successor) since the Gradle-side task names are unchanged, but this is unverified; would need either a
  live `npm view` against Tridium's private registry or a shipped `package.json`/lockfile snapshot from a
  real N5 project. LOW (the Gradle-side orchestration this block covers is likely sufficient for the
  DashboardPan-ux decision in §36.10 regardless).

## 36.x — Connections

- **[Block 2]** — this block closes B2-G5, the child gap [Block 2] §2.11 explicitly deferred; §36.1
  extends [Block 2] §2.1's plugin-id inventory/alias table (`com.tridium.niagara-grunt → com.tridium.
  grunt`) with the 6 gap-named ids' shared-jar structure.
- **[Block 21]** — [Block 21] confirmed N5's `bajaScript`/`bajaux`/`webEditors`/`kitPx`/`wiresheet`
  runtime JS is still AMD/RequireJS, Babel-transpiled, no webpack (§21.2 and onward); this block is the
  BUILD-TIME producer of that same `rc/` output — the `requirejs`/`babel:dist` `gruntBuild` tasks (§36.5/
  §36.6) are literally what generates the artifacts [Block 21] censused as already-built jar contents.
- **REMIT `niagara-research` B1132/B1119** — the N4 baseline for the Grunt/RequireJS/Babel toolchain this
  block confirms survives (id-renamed) into N5; B957 — the SDK's `typeExtensionDemo` example already
  documents the full `package.json`+`Gruntfile.js`+`grunt-niagara` scaffold this block's devkit-wizard
  read (§36.6) confirms N5's wizard does NOT auto-generate.
- **REMIT `niagara-research` B1028** — the DashboardPan-ux conformance audit this block's §36.10
  conclusion is built on (no Jasmine/Karma harness, no `package.json`, hand-authored `rc/`).
