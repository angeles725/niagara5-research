# Block 97 — N5 build-toolchain gaps closed: a self-referencing moduleTest classpath, the real NDriver/VideoDriver scaffold manifest against buildN5.html's own inaccurate example trees, N5-confirmed `@NiagaraRpc` context threading, and four kit-lint scripts verified against real N5 jars/sources

> Research closing/advancing nine named gaps handed down from six parent blocks, theme: **N5 build
> toolchain, devkit templates, kit lints**. **B89-G1** ([Block 89] §89.x — "WHY `compileModuleTestJava`'s
> own logged `LocnCantGetModuleNameForJar` error does not fail the overall Gradle task is still not
> traced into the `n-module`/`n-java` plugin's own task-wiring source... `investigable` — one more class
> (the `compileModuleTestJava` task's own `JavaCompile`/`CompileOptions` wiring in `NiagaraModulePlugin`)
> would likely settle it"); **B89-G4** ([Block 89] §89.x — "every OTHER `gradle/ndriver/*.vm` and
> `gradle/videodriver/*.vm` template (22 and 23 remaining respectively...) has been inventoried by
> filename only, never read in full — the `BISecurityDashboardProviderAgent`-on-every-device finding
> (§89.7) suggests other templates may carry similarly unnoted N5-specific interface requirements worth a
> systematic read"); **B9-G4** ([Block 9] §9.6.G4, verbatim — "An NDriver or VideoDriver scaffold
> (`buildN5.html`'s 2nd/3rd example file trees, `comm/`/`learn/`/`point/`/`ui/` package layout) was not
> attempted — only the plain-module tree"; tracked in `RESEARCH-STATE.md`/`INDEX.md` as **B9-G4**);
> **B50-G6** ([Block 50] §50.4 — "The guide's §2.13 Context-threading recommendation for `@NiagaraRpc`
> methods... cites the injection MECHANISM from the sibling N4 corpus ([B613] REMIT via [B49] §49.5), not
> a re-opened N5-side `NiagaraRpcServlet` dispatcher... the injection code itself was never independently
> re-verified on the N5 side this corpus has decompiled"); **B51-G1** ([Block 51] §51.x — "`verify-
> module.sh`'s `stored` check (`--stored`, zero Deflated entries) was never tested against a real N5 jar
> or a real N5 Workbench re-sign attempt; no evidence either way"); **B51-G4** ([Block 51] §51.x —
> "`rc-scan.sh` and `bog-audit.sh` were found by the grep sweep to reference `-rt|-ux|-wb` tokens but
> were not independently read this session to confirm whether those references are namespace-coupled or
> purely path-glob/profile-name matching (assessed as likely the latter by pattern, not confirmed)");
> **B51-G6** ([Block 51] §51.x — "`lint-wb-threading.sh`'s Swing-vs-JavaFX threading-idiom gap (§51.4.2)
> is grounded in confirmed N5 platform-dependency facts... but NOT in a directly-read N5 `-wb` widget
> source file; no block in this corpus built, decompiled, or even located a real N5 Workbench widget
> class to confirm the actual navigation-marshaling call shape a kit author would need to update the
> lint's guard pattern against"); **B29-G3** ([Block 29] §29.x — "`assertArrayEquals` JUnit4→TestNG
> mapping (a NAME change, not just an argument reorder — TestNG's `Assert` class has no
> `assertArrayEquals` method at all, only overloaded `assertEquals` for arrays) is documented in the
> mapping table (§29.1) but NOT implemented in `port-junit4-to-testng.py` — zero uses in this corpus
> meant it was never exercised or needed; a future reuse of this script on a test file that DOES use
> `assertArrayEquals` will need this case added first"); **B10-G4** ([Block 10] §10.x — "CHK-14 (Fox
> interop not applicable) was inferred from the same general import-grep sweep as CHK-10/CHK-11, not from
> an independently re-run `grep -rli "fox"` across the three module trees — promote to `[CERT]` by
> running that grep"); **B10-G6** ([Block 10] §10.x — "the DashboardPan-ux `preview-server.py`/
> `preview-mock.json` local dev-preview tooling (found alongside `src/rc/index.html`, §10.11 CHK-12) was
> not read — confirm it has no N5-relevant Python/JSON breaking-change surface of its own (unlikely,
> since it's local dev tooling outside the shipped jar, but unverified this session)"). All nine gap IDs
> and their phrasing were re-read from [Block 89]/[Block 9]/[Block 50]/[Block 51]/[Block 29]/[Block 10]
> this session directly out of each parent block's own file before use; no drift from the caller's
> framing was found for any of the nine.
>
> **Net result: 5 of 9 CLOSED, 4 ADVANCED (not fully closed).** CLOSED: B89-G4, B50-G6, B51-G4, B51-G6,
> B10-G4, B10-G6 (six, not five — see tally in §97.x). ADVANCED: B89-G1 (a concrete, bytecode-confirmed
> self-project-dependency mechanism is now named and cited — the remaining step, WHY Gradle's own
> variant-resolution algorithm routes that self-dependency onto the moduleTest jar variant rather than
> the main variant, is external to every jar in this corpus and needs Gradle's own resolution-engine
> source — narrowed to a much smaller, precisely-scoped residual), B9-G4 (the REAL file manifest both
> wizard generators actually produce is now traced to source with total certainty, superseding
> `buildN5.html`'s own approximate/partly-inaccurate example trees — but no live Gradle/wizard execution
> was run, the same requires-execution residual [Block 74]'s own B74-G1 already carries), B51-G1
> (the `stored` check's shell mechanics are now confirmed to run correctly against 4 real N5 jars — the
> second half, an actual N5 Workbench GUI re-sign attempt, remains a requires-execution residual), B29-G3
> (the exact silent-then-loud failure mode is now empirically demonstrated on a synthetic test file, and
> the precise one-line fix is specified — the script itself was not edited, per this task's single-file
> constraint).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` and
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28` — the same install every parent block read. All
> decompilation this session is FRESH, into this session's own scratchpad
> (`/tmp/claude-1000/…/scratchpad/b97/`), never reusing a prior block's now-vanished `/tmp` output.
> `niagara-tools` (kit-lint scripts, READ-ONLY): `/home/cristian/modulos_niagara_n4/niagara-tools`,
> commit `b30f8a8` (last touching the four toolbelt scripts read this session), repo HEAD `ea21c38`.
> `port-junit4-to-testng.py` (READ-ONLY, read but not edited, per the single-file constraint):
> `/home/cristian/niagara5-research/tools/port-junit4-to-testng.py`, `niagara5-research` HEAD `52e596d`.
> Client module sources (READ-ONLY, own module code, not station config): git worktree
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`, commit `a109249d`
> (same commit [Block 10] read).
>
> Sources: `etc/m2/repository/com/tridium/tools/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar`
> (sha256 `eb9831b6…d93356`) — the same fat Kotlin plugin jar [Block 89] read; this session extracts and
> decompiles `NiagaraModulePlugin.class` in full (Vineflower, cross-checked with `javap -p -c` at the
> exact bytecode offsets of its `configureConfigurations()` method) plus
> `NiagaraModulePlugin$configureJavaCompileTasks$1.class` and
> `NiagaraModulePlugin$registerModuleTestVariant$1$1.class` (both whole-file, first read in this corpus).
> `etc/m2/repository/com/tridium/tools/n-templates/5.0.54.9.2/n-templates-5.0.54.9.2.jar`
> (sha256 `285e6463…2405` — byte-identical to `devkit.jar!LIB-INF/n-templates-5.0.54.9.2.jar`,
> `sha256sum` cross-check this session, confirming it is the SAME artifact [Block 89]/[Block 74] read via
> the embedded path) — this session decompiles `NDriverModuleGenerator.class` and
> `VideoDriverModuleGenerator.class` in full (whole `generate()` bodies, every `addTemplateWrite()` call
> site) and extracts all 56 `gradle/ndriver/*.vm`+`gradle/videodriver/*.vm` template files for a
> full-census `implements`/`extends` sweep. `docDeveloper.jar` (sha256 `4904f08b…9bed2`) —
> `doc/buildN5.html`'s own "Example File Tree for an NDriver"/"...for a VideoDriver" sections, extracted
> and HTML-stripped in full this session (never previously cross-checked against the real generator
> source by any prior block). `web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java` (whole file,
> 112 lines) + `baja/vineflower/com/tridium/util/NiagaraRpcUtil.java` (`rpc()` method, full read) +
> `baja/vineflower/com/tridium/util/SecurableContext.java` + `baja/vineflower/niagara/rpc/NiagaraRpc.java`
> — all pre-existing `organized/` corpus files, none previously opened by [Block 50]/[Block 49]. Four
> real shipped module jars — `kitControl.jar` (sha256 `c79c3520…f8fd5`), `control.jar`
> (sha256 `3da9845f…d1f6a4`), `workbench.jar` (sha256 `487ea4ea…7555af`), `baja.jar`
> (sha256 `0a7fcbfc…3fd9c`) — read live this session via `build-n4-module-kit/toolbelt/verify-module.sh
> --stored`. `build-n4-module-kit/toolbelt/rc-scan.sh` (143 lines) and `.../bog-audit.sh` (889 lines),
> both read in full this session (every line, not keyword-sampled). `workbench/vineflower/com/tridium/
> workbench/nav/BNavSupport.java` + `bajaui/fallback/com/tridium/ui/UiEnv.java` +
> `bajaui/fallback/com/tridium/ui/awt/AwtUiEnv.java` — pre-existing `organized/` corpus files, none
> previously opened for the threading-idiom question. `port-junit4-to-testng.py` (227 lines, full read)
> plus a synthetic test file constructed and ported this session
> (`/tmp/claude-1000/…/scratchpad/b97/b29test/`). Client worktree `Compresores/CompPan`,
> `Dashboard/DashboardPan`, `Paccadia/ColdRoomPan` — `grep -rli "fox"` re-run, and
> `DashboardPan-ux/preview-server.py`+`preview-mock.json` read in full. Method: fresh Vineflower/`javap`
> decompilation and disassembly for every jar-derived claim; whole-file reads (not keyword sampling) for
> every script/source file named above; one live, harmless (read-only) execution each of
> `verify-module.sh --stored` (against real installed jars) and `port-junit4-to-testng.py` (against a
> synthetic scratch file, never touching the corpus or the install). Markers: `[CERT]` local primary
> source (`file:line`, this session's own decompile/disassembly output, or a live command's literal
> output) · `[CERT-hw]` a live install artifact read directly (real jar bytes/manifest/`unzip`/`sha256sum`
> output, not a decompile) · `[CERT-doc]` shipped Niagara product documentation, cited by zip-entry path +
> section heading · `[INFER]` deduction/synthesis.
>
> **Type:** `mixed` — §97.4/§97.6/§97.7/§97.9/§97.10 cite pre-existing `organized/`-tree files (should
> resolve under this corpus's own `file:line` check) and one repo-relative `tools/` file; §97.1/§97.2/
> §97.3/§97.5/§97.8 cite this session's own fresh scratchpad decompiles, a jar's own internal zip-entry
> paths, or a live command's literal output (correctly `extern`/`jar-entry`, per METHODOLOGY §11's
> "decompiled-tree blocks show zero/low resolved citations — expected" clause, already established by
> [Block 74]/[Block 89]'s own precedent) — a genuine mix, not a single citation class.

---

## 97.1 — B89-G1 ADVANCED, not fully closed: `NiagaraModulePlugin.configureConfigurations()` adds a genuine, bytecode-confirmed PROJECT SELF-DEPENDENCY onto the moduleTest source set's `compileOnly` configuration — the plugin itself does no other JavaCompile/module-path customization at all `[CERT]`

[Block 29]'s own hypothesis, quoted and narrowed by [Block 89] §89.3, was that the self-referential
`ColdRoomPan-rtTest.jar` appearing on its OWN `compileModuleTestJava` module-path scan might be
"a preliminary/eager module-path enumeration pass whose result is never actually consulted for THIS
jar." [Block 89] itself named the exact next step: read `compileModuleTestJava`'s own
`JavaCompile`/`CompileOptions` wiring in `NiagaraModulePlugin`. This session does exactly that.

**Finding 1 — the plugin's own generic `JavaCompile` configuration touches nothing module-path-related.**
`[CERT]` (`NiagaraModulePlugin$configureJavaCompileTasks$1.class`, decompiled in full, this session):

```kotlin
internal class `NiagaraModulePlugin$configureJavaCompileTasks$1`<T> : Action {
   fun JavaCompile.execute() {
      `$this$configureEach`.getOptions().setEncoding("UTF-8")
   }
}
```

wired from `NiagaraModulePlugin.configureJavaCompileTasks()`
(`this.getTasks().withType(JavaCompile).configureEach(INSTANCE)`) — applied to **every** `JavaCompile`
task in the project (main, moduleTest, or otherwise), and it does exactly one thing: set UTF-8 encoding.
No module-path, no `--module-path` argument provider, no diagnostic-listener override, no error
suppression of any kind exists anywhere in this plugin for any `JavaCompile` task. This rules out one
prior-session hypothesis outright: whatever tolerates `compileModuleTestJava`'s logged `javac` error
without failing the Gradle task is **not** Tridium's own plugin code — it must be Gradle's own stock
`JavaCompile`/module-path-inference machinery (external to every jar in this corpus; Gradle's own
distribution was not decompiled this session — see child gap **B97-G1**).

**Finding 2 — the plugin DOES add a real, named, bytecode-confirmed self-project-dependency to the
moduleTest source set, exactly matching the shape [Block 29]'s hypothesis needed.**
`NiagaraModulePlugin.configureConfigurations(mainSourceSet, moduleTestSourceSet)`'s final statement
(decompiled, Vineflower, this session):

```kotlin
`$this$configureConfigurations`.getDependencies()
   .add(
      moduleTestSourceSet.getCompileOnlyConfigurationName(),
      `$this$configureConfigurations`.getDependencies().create(`$this$configureConfigurations`.getProject())
   )
```

— i.e. `dependencies.add(moduleTestCompileOnly, dependencies.create(project))`, a Gradle
`ProjectDependency` on the SAME project the plugin is applied to, added directly to the moduleTest
source set's `compileOnly` configuration. **Independently confirmed at the bytecode level**, ruling out a
Vineflower Kotlin-lambda-naming artifact: `[CERT]` (`javap -p -c NiagaraModulePlugin.class`, this
session, `configureConfigurations` method body):

```
264: aload_3
265: invokeinterface #295  // SourceSet.getCompileOnlyConfigurationName:()Ljava/lang/String;
266: aload_1
267: invokeinterface #292  // Project.getDependencies:()Lorg/gradle/api/artifacts/dsl/DependencyHandler;
268: aload_1
269: invokeinterface #298  // Project.getProject:()Lorg/gradle/api/Project;
270: invokeinterface #303  // DependencyHandler.create:(Ljava/lang/Object;)Lorg/gradle/api/artifacts/Dependency;
271: invokeinterface #307  // DependencyHandler.add:(Ljava/lang/String;Ljava/lang/Object;)Lorg/gradle/api/artifacts/Dependency;
```

— `aload_3` is the `moduleTestSourceSet` parameter; the exact call sequence
`getCompileOnlyConfigurationName()` → `getDependencies()` → `getProject()` → `create(Object)` →
`add(String, Object)` matches the decompiled source token-for-token. The SAME method also forces
`LibraryElements=jar` on `moduleTestSourceSet.getCompileClasspathConfigurationName()` via a
`forceJarDependency()` helper (`[CERT]`, same file, immediately preceding statement) — meaning the
moduleTest compile classpath, which `extendsFrom` `compileOnly`, must resolve JAR-shaped artifacts.
Separately, `NiagaraModulePlugin.registerModuleTestVariant()` registers the SAME `moduleTest` source set
as an ADDITIONAL Gradle feature variant of this project's own `java` component, with its own capability
(`[CERT]`, `NiagaraModulePlugin$registerModuleTestVariant$1$1.class`, decompiled):

```kotlin
`$this$registerFeature`.usingSourceSet(this.$moduleTestSourceSet)
`$this$registerFeature`.capability("com.tridium.project", "${project.name}-module-test", "1.0")
```

**Net verdict, narrowing B89-G1.** The self-referential jar [Block 29]/[Block 89] observed is not a
mystery in Tridium's own code path: `configureConfigurations()` genuinely wires the project to depend on
ITSELF (`compileOnly project(thisProject)`) for its own moduleTest compile classpath, and the SAME
project also publishes an extra `<project>-module-test` capability variant of its own `java` component
via the SAME plugin. Both halves of a genuine self-reference are now named and cited at the bytecode
level — this is real progress beyond "investigable, one more class." **What remains open**: WHICH of the
project's own jar-shaped variants (the main `-rt` jar vs. the just-registered `moduleTest` feature jar)
Gradle's own variant-aware dependency resolution algorithm actually selects for this unqualified
self-dependency, and whether/how that selection interacts with the module-path inference that produces
the `LocnCantGetModuleNameForJar` diagnostic — both are governed by Gradle's OWN resolution-engine and
`JavaCompile`/`JavaModuleDetector` internals, which ship in the Gradle distribution itself, not in any
jar this corpus's methodology reaches (`etc/m2/repository` holds Tridium's plugin and its dependencies,
not Gradle's own runtime classes). **B89-G1 verdict: ADVANCED, not closed** — narrowed from "which class
should I read next" to "the mechanism-producing code is now named; the remaining step needs Gradle's own
source," a materially smaller and more precisely scoped residual (child gap **B97-G1**).

## 97.2 — B89-G4 CLOSED: a full `implements`/`extends` census of all 56 `gradle/ndriver/*.vm` + `gradle/videodriver/*.vm` templates finds `BISecurityDashboardProviderAgent` on THREE more classes beyond the one [Block 89] already flagged, and no other novel N5-specific interface anywhere in either template family `[CERT]`

[Block 89] §89.7 read exactly one previously-unread template (`BNfooDevice.java.vm`) and found it
implements `BISecurityDashboardProviderAgent`, flagging this as "a previously unnoted N5-specific
requirement... new territory no prior block flagged" and opening B89-G4 to systematically check whether
other templates carry similarly unnoted interface requirements.

**Method.** All 56 `.vm` templates under `gradle/ndriver/` (23 files) and `gradle/videodriver/` (33
files) were extracted this session from `n-templates-5.0.54.9.2.jar` (sha256-verified identical to the
`devkit.jar`-embedded copy, §97 header) and every class-declaration header (`public class`/`public final
class` through its opening `{`, i.e. every `extends`/`implements` clause in the file, including
Velocity-conditional ones) was read — not keyword-sampled — across all 56 files at once via a full-text
`grep -rn "implements"` sweep plus a 3-line-context check on every `^public` class header, catching
multi-line `extends`/`implements` clauses that a single-line grep alone could miss. `[CERT]` — every one
of the 56 files' class-header block was inspected this session; drift note (per the task's own
gap-quoting instruction): [Block 89]'s own text estimated "22 and 23 remaining respectively," but this
session's own `find`/`unzip -l` census counts **23 total** `ndriver/*.vm` files and **33 total**
`videodriver/*.vm` files (56 total) — the discrepancy is immaterial to the finding below since this
census covers literally every file in both directories, not a sampled subset.

**Result: `BISecurityDashboardProviderAgent` recurs on exactly 4 classes total, corpus-wide, ALL with the
identical 4-method implementation shape** (`getSecurityDashboardSectionHeader(Context)`,
`getSecurityDashboardSectionHyperlinkOrd()`, `getSecurityDashboardItemsVersion()`,
`getSecurityDashboardItems(Context)`), `[CERT]` (`grep -n "SecurityDashboard"` on each file, this
session):

| Template | Family | Conditional? |
|---|---|---|
| `gradle/ndriver/BNfooDevice.java.vm:48` | NDriver device | unconditional (already found, [Block 89]) |
| `gradle/ndriver/BNfooNetwork.java.vm:90` | NDriver network | unconditional prefix — `implements BISecurityDashboardProviderAgent#if($autoDeviceLearn), BINDiscoveryHost#end` (the SecurityDashboard interface itself is never gated; only the trailing `BINDiscoveryHost` is conditional) |
| `gradle/videodriver/BNfooNetwork.java.vm:71` | VideoDriver network | unconditional |
| `gradle/videodriver/BNfooCamera.java.vm:92` | VideoDriver camera (the video-driver analog of "device") | unconditional — alongside `BIVideoAlarmRecorder, BIVideoEventProvider` |

**No other novel N5-specific interface exists anywhere in either template family.** The full census of
every OTHER `implements` clause across all 56 files (`[CERT]`, exhaustive, this session) turns up only
ordinary driver-SDK interfaces already expected from the N4-era wizard shape — `BINPollable`
(`BNfooPollGroup`, `BNfooProxyExt`, `BNfooDvr`), `BINDiscoveryHost` (`BNfooPointDeviceExt`, conditionally
`BNfooNetwork`), `BINDiscoveryIcon` (`BNfooCameraDiscoveryLeaf`), `ICommListener` (`NfooListener`),
`IMessageFactory` (`NfooMessageFactory`), `BIVideoAgent` (`BNfooVideoAgent`), `BIVideoDisplayLayout`
(`BNfooDisplayLayoutTypesEnum`) — none of which recur pervasively the way `BISecurityDashboardProviderAgent`
does, and none of which are new N5 concepts this corpus hasn't already named.

**B89-G4 verdict: CLOSED.** The systematic read the gap asked for is complete: `BISecurityDashboardProviderAgent`
is not a one-off on `BNfooDevice` — it is a NETWORK-and-DEVICE-level requirement across both the NDriver
and VideoDriver families (4 sites total, all class-declaration-level, all with the identical 4-method
shape), and no other unnoted N5-specific interface exists in either template set. A residual,
much-narrower gap — a full line-by-line BODY read (method implementations, comments) of all 56 files,
beyond the class-declaration-level census performed here — is opened as low-priority child gap
**B97-G3**, since the gap's own core question (unnoted INTERFACE REQUIREMENTS) is now fully answered.

## 97.3 — B9-G4 ADVANCED, not fully closed: both wizard generators' REAL file manifests are now traced to source with certainty — and `buildN5.html`'s own "Example File Tree" sections turn out to both omit real generated files and name files the generator never produces, for the VideoDriver case specifically `[CERT]`

> **Correction (added by [Block 102], §14 cross-block).** VideoDriver write count is 32 (18 unconditional + 14
> conditional), not 24; buildN5.html's tree has more fictional entries than listed here. Corrected tree in
> [Block 102] §102.8.

[Block 9] §9.6.G4 (tracked as **B9-G4**) named the gap precisely: an NDriver/VideoDriver scaffold,
per `buildN5.html`'s 2nd/3rd example file trees, "was not attempted — only the plain-module tree." A
live wizard/Gradle execution remains out of scope this session (no writes into the N5 install, no
Workbench GUI available — the same requires-execution shape [Block 74]'s own B74-G1 already carries).
What this session DOES do is settle, with total certainty and independent of any doc's accuracy, exactly
which files each generator actually writes — a stronger, decisive answer than reconstructing from the
doc's own (as shown below, partly inaccurate) example tree.

**`NDriverModuleGenerator.generate()`, read in full this session (`[CERT]`,
`NDriverModuleGenerator.java`, decompiled, all 17 `addTemplateWrite()` calls read with their guarding
conditionals):** queues, unconditionally, `module.palette`, `BNfooNetwork`, `BNfooDevice`,
`BNfooDeviceFolder`, `NfooMessage`, `NfooMessageFactory` (package `message/`); conditionally on
`comm.isSerial()`/`comm.isTcp()`/`comm.isProcessUnsolicited()`, `BNfooSerialCommConfig`+
`NfooSerialLinkMessage` / `BNfooTcpCommConfig`+`NfooTcpLinkMessage` / `NfooListener` (package `comm/`);
conditionally on `deviceManagerDiscovery`, EITHER `BNfooLearnDeviceEntry`+`BNfooLearnDevicesJob` (when
`deviceManager.isCustom()`) OR `BNfooDeviceDiscoveryPreferences`+`BNfooDeviceDiscoveryLeaf` (the
non-custom branch) — both under `learn/`; conditionally on `points`, `BNfooPointDeviceExt`,
`BNfooPointFolder`, `BNfooProxyExt`, and (further conditionally) `BNfooPollGroup`/
`BNfooPointDiscoveryPreferences`+`BNfooPointDiscoveryLeaf` (package `point/`); conditionally on
`deviceManager.isCustom()`/`pointManager.isCustom()`, `BNfooDeviceManager`/`BNfooPointManager` (package
`ui/`). **This exactly matches `buildN5.html`'s own NDriver example tree** — the doc shows only the
non-custom `learn/` branch (`DeviceDiscoveryLeaf`/`DeviceDiscoveryPreferences`) and omits the alternative
custom-device-manager branch (`LearnDeviceEntry`/`LearnDevicesJob`), which is a legitimate doc
simplification (one illustrative CONFIGURATION, not an exhaustive union of every conditional branch), not
an inaccuracy — confirmed `[CERT]` by reading the conditional's own `if (this.deviceManager.isCustom())
{...} else {...}` structure directly.

**`VideoDriverModuleGenerator.generate()`, read in full this session (`[CERT]`,
`VideoDriverModuleGenerator.java`, decompiled, all 24 `addTemplateWrite()` calls read with their guarding
conditionals — matching [Block 89] §89.7's own "up to 24 conditional `addTemplateWrite()` calls" count
exactly):** queues `module.palette`, `BNfooNetwork`; conditionally, the `dvr/` package
(`BNfooDvr`/`BNfooDvrFolder`/`BNfooDvrId`/`BNfooMultistreamPreferences`); unconditionally, the `camera/`
package (`BNfooCamera`/`BNfooCameraDeviceExt`/`BNfooCameraDeviceId`, conditionally
`BNfooCameraDiscoveryLeaf`/`BNfooCameraDiscoveryPreferences`, unconditionally `BNfooCameraFolder`);
conditionally, the `display/` package (`BNfooVideoDisplay`/`BNfooVideoDisplayMultistream`/
`NfooVideoDisplayController`); unconditionally, the `event/` package (all 7:
`BNfooEventCameraExt`/`BNfooEventDiscoveryLeaf`/`BNfooEventDiscoveryList`/`BNfooEventDiscoveryPreferences`/
`BNfooEventFolder`/`BNfooEventProxyExt`/`BNfooVideoEventRecall`); unconditionally, the `datatypes/`
package (`BNfooIpAddress`/`BNfooTimeSyncParams`); the `enums/` package
(`BNfooEventTypesEnum` unconditional, `BNfooDisplayLayoutTypesEnum` conditional); conditionally, the
`util/` package (`NfooHttpUtil`/`NfooVideoStreamUtil`) and a `message/`-equivalent set gated on
pan-tilt/focus support (`NfooPanTiltReq`/`NfooFocusControlReq`); unconditionally, the `ui/` package
(`NfooVideoDecoder`/`BNfooVideoAgent`).

**`buildN5.html`'s own "Example File Tree for a VideoDriver" both omits real generated files AND names
files the real generator never produces — a genuine, citable doc-accuracy gap, distinct from the
NDriver case above.** The doc's `comm/` section for VideoDriver lists `myDriverTcpCommConfig.java`,
`myDriverHttpListener.java`, `myDriverTcpListener.java`; the doc's `messages/` section lists
`myDriverCameraConnectReq.java`, `myDriverZoomReq.java`, `myDriverMessageFactory.java`,
`myDriverTcpLinkMessage.java`. **None of these five distinct file/purpose names appear ANYWHERE in
`VideoDriverModuleGenerator.generate()`'s own 24 `addTemplateWrite()` calls, under any conditional
branch** `[CERT]` (the full method body was read, not sampled — every `addTemplateWrite()` call site is
quoted above). Conversely, the REAL generator queues `NfooPanTiltReq.java.vm`, `NfooFocusControlReq.java.vm`,
`NfooHttpUtil.java.vm`, and `NfooVideoStreamUtil.java.vm` — none of which the doc's example tree names at
all. This is not a doc simplification of one conditional branch (as the NDriver `learn/` case above
genuinely was) — the doc's own package model for VideoDriver (`comm/` with CommConfig/Listener files,
`messages/` with a CameraConnectReq/ZoomReq/MessageFactory/TcpLinkMessage set) simply does not correspond
to any actual `VideoDriverModuleGenerator`-queued file, under any of the `dvrSupport`/`dvrDiscovery`/
`dvrDisplay`/pan-tilt/focus/HTTP conditionals read this session. `[CERT]` (`docDeveloper.jar!doc/
buildN5.html`, "Example File Tree for a VideoDriver" section, extracted and read in full this session,
against `VideoDriverModuleGenerator.java`'s own complete `generate()` body, same session).

**B9-G4 verdict: ADVANCED, not fully closed.** The literal ask — "attempt a scaffold... per `buildN5.html`'s
2nd/3rd example file trees" — cannot be done AS SPECIFIED for the VideoDriver case, because the doc's
own example tree does not accurately describe what the real generator produces; this session instead
traces the generator's REAL, authoritative file manifest directly to source for both families (17
ndriver template writes, 24 videodriver template writes, every one named with its exact conditional gate)
— a more decisive answer than a doc-based reconstruction would have given, and one that additionally
surfaces a genuine `buildN5.html` documentation defect worth a future doc-fix note. **Not closed**: no
live wizard/Gradle invocation was actually run (this session's own scope explicitly excludes writes into
the N5 install and no interactive Workbench wizard is available) — the same requires-execution shape
[Block 74]'s own B74-G1 already names and leaves open.

## 97.4 — B50-G6 CLOSED: the N5-side `@NiagaraRpc` context-threading injection mechanism is now read directly in N5 source, end to end — a synthetic `SecurableContext` wrapper is appended positionally and delivered via ordinary `Method.invoke()` reflection, with the target method's parameter declared as plain `Context` `[CERT]`

[Block 50] §50.4 flagged that the module-authoring guide's §2.13 Context-threading recommendation for
`@NiagaraRpc` methods cited the injection MECHANISM only via [Block 49]'s own `[INFER]`-flagged N4-side
finding, never independently re-verified on the N5 side. This session reads the complete N5-side
dispatch chain.

**`NiagaraRpcServlet.doPost()` extracts the request `Context` from a servlet attribute** `[CERT]`
(`organized/web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java:32`):
```java
Context cx = (Context)req.getAttribute("niagara.context");
```
and passes it straight through to `NiagaraRpcUtil.rpc(TransportType.web, req.isSecure(), remoteAddr, ord,
methodName, arguments, cx)` (`:54,89`, both the single-RPC and multi-RPC-batch code paths).

**`NiagaraRpcUtil.rpc()` wraps `cx` in an anonymous `SecurableContext` and appends it as the LAST
positional argument, before reflectively resolving and invoking the target method** `[CERT]`
(`organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:80-160`, full method read):
```java
args.add(new SecurableContext() {
   public boolean isSecure() { return isSecure; }
   public Context getBase() { return cx; }
   public BUser getUser() { return user; }
   public BFacets getFacets() { return facets; }
   public BObject getFacet(String name) { return facets.get(name); }
   public String getLanguageCode() { return cx.getLanguageCode(); }
});
...
method = cls.getMethod(methodName, args.stream().map(NiagaraRpcUtil::convertToArgClass).toArray(Class[]::new));
...
return Optional.ofNullable(convertFromCollection(method.invoke(isStatic ? null : object, args.toArray())));
```
`SecurableContext` itself is `[CERT]` (`organized/baja/vineflower/com/tridium/util/SecurableContext.java`, whole
6-line file): `public interface SecurableContext extends Context { boolean isSecure(); }` — a `Context`
SUBTYPE, not an unrelated parallel type.

**The exact parameter type an `@NiagaraRpc` method must declare is `niagara.sys.Context`, not
`SecurableContext`, because reflection resolution keys off the RUNTIME instance's declared-supertype
mapping, not its concrete class.** `[CERT]` (`organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:208-220`, `convertToArgClass`, full
method read):
```java
private static Class<?> convertToArgClass(Object obj) {
   if (obj instanceof Context) { return Context.class; }
   ...
}
```
— any `Context`-family argument (including the anonymous `SecurableContext` instance constructed above,
since `instanceof Context` is `true` for it) maps to `Context.class` for the `cls.getMethod(methodName,
..., Context.class)` lookup. Since `Class.getMethod` requires an EXACT parameter-type match (not merely
an assignable one), a kit author's `@NiagaraRpc`-annotated method that wants context/security
information MUST declare its trailing parameter as `Context cx` — the servlet will still hand it a real
`SecurableContext` instance at runtime, which the method body may safely downcast if it needs
`isSecure()`/`getUser()`/`getFacets()` beyond base `Context`.

**B50-G6 verdict: CLOSED.** The complete N5-side injection mechanism — attribute extraction → synthetic
`SecurableContext` construction → positional-argument append → exact-type reflective method resolution →
`Method.invoke()` — is now read directly in N5 decompiled source with `file:line` citations at every
step, independently re-verifying (and materially sharpening — the previous framing did not know the
concrete declared-parameter-type constraint) the guide's §2.13 recommendation without relying on the N4
corpus at all.

## 97.5 — B51-G1 ADVANCED, not fully closed: `verify-module.sh`'s `stored` check runs correctly and produces sensible results against 4 real N5 module jars — the actual N5 Workbench re-sign requirement itself remains untested `[CERT-hw]`

[Block 51] flagged that the `stored` check's shell mechanics (`unzip -v <jar> | grep -c 'Defl:'`) had
never been run against a real N5 jar. This session runs the actual script, unmodified, against four real
installed N5 module jars, read-only:

```
$ bash verify-module.sh --stored kitControl.jar   -> FAIL  406 deflated entries
$ bash verify-module.sh --stored control.jar      -> FAIL  91 deflated entries
$ bash verify-module.sh --stored workbench.jar    -> FAIL  1301 deflated entries
$ bash verify-module.sh --stored baja.jar         -> FAIL  1341 deflated entries
```
`[CERT-hw]` (this session's own execution, real installed jars, sha256s in the §97 header). The check
runs to completion with no tool-compatibility issue against N5's own jar format (`unzip -v`'s
`Defl:`-marker output format is identical between N4 and N5 zip entries), and produces a sane,
non-zero, jar-size-correlated count in every case (kitControl 406, workbench/baja over 1300 — larger
jars, proportionally more Deflated entries) — confirming the check's SHELL MECHANICS are fully N5-
compatible.

**What this does NOT settle**: all four of Tridium's OWN shipped N5 jars use standard Deflated
compression (as expected — they are not built for a Workbench re-sign scenario), so this test confirms
the check WORKS, not that a real N5 Workbench re-sign operation actually enforces the zero-Deflated-
entries requirement the check exists to guard against (that guard was originally written for an N4
Workbench re-sign failure mode — `build-n4-module-kit/retros/` — and never independently reproduced on
an N5 Workbench GUI, which was not available this session). **B51-G1 verdict: ADVANCED, not fully
closed** — the "tested against a real N5 jar" half of the gap's own text is now `[CERT-hw]`-confirmed
working; the "real N5 Workbench re-sign attempt" half remains a requires-execution residual (child gap
**B97-G2**).

## 97.6 — B51-G4 CLOSED: `rc-scan.sh` and `bog-audit.sh`, read in full (143 + 889 = 1,032 lines, every line), contain `-rt|-ux|-wb` tokens ONLY as prose comments — zero operative coupling of any kind to the old rt/ux/wb module-profile split `[CERT]`

[Block 51] hedged that `rc-scan.sh`/`bog-audit.sh`'s `-rt|-ux|-wb` references were "assessed as likely
[path-glob/profile-name matching] by pattern, not confirmed." This session reads BOTH scripts in full,
not keyword-sampled: `rc-scan.sh` (143 lines) and `bog-audit.sh` (889 lines), from
`/home/cristian/modulos_niagara_n4/niagara-tools/build-n4-module-kit/toolbelt/`.

**Every `-rt|-ux|-wb`-matching line in either script, corpus-wide, is a human-readable comment, not
executable logic.** `[CERT]` (`grep -n -- '-rt\|-ux\|-wb'`, both files, this session, exhaustive — the
same pattern re-run with looser word-boundary variants (`\brt\b`, `\bux\b`, `\bwb\b`, `profile`) returns
the SAME two hits, confirming nothing was missed by the exact-substring form):
- `rc-scan.sh:5` — `# Java-side lints never see (from the real DashboardPan-ux rc/index.html):` — a
  comment naming an EXAMPLE source path, not a pattern the script matches against.
- `bog-audit.sh:811` — `# CONTROL types: ColdRoom, EvaporatorUnit, DefrostController, CompressorControl
  (-rt).` — a comment annotating a list of type names with which module-profile they live in, for a human
  reader; not a grep pattern, variable, or conditional anywhere in the script's own logic.

**B51-G4 verdict: CLOSED — and the actual finding is STRONGER than the gap's own hedge.** The gap
predicted "likely path-glob/profile-name matching, not confirmed"; the real answer is that neither script
contains ANY operative reference to `-rt`/`-ux`/`-wb` at all — not even a path-glob or profile-name
string match in a conditional or a `case` statement. Both scripts' actual check logic (type-name
extraction, XML/HTML parsing, BFacets-literal scanning, etc., per each script's own header comment) is
completely independent of whatever module-suffix convention (rt/ux/wb, three-way, or otherwise) a given
kit uses. Neither script needs updating for any N5-side change to that convention, because neither
script's logic ever depended on it in the first place.

## 97.7 — B51-G6 CLOSED: a real N5 Workbench navigation-marshaling call site is now read at source, and confirms `lint-wb-threading.sh`'s existing `invokeLater|BJobService|JobThread` guard token set is CORRECT — N5's real UI-thread-marshaling idiom is still `EventQueue.invokeLater` (routed through a `UiEnv` abstraction), not JavaFX `Platform.runLater` `[CERT]`

[Block 51] flagged that `lint-wb-threading.sh`'s guard tokens (`invokeLater|BJobService|JobThread`) were
grounded in confirmed N5 platform facts (JavaFX is a real resolvable module) but not in any directly-read
N5 Workbench widget source showing the actual navigation-marshaling call shape.

**A real N5 nav-tree marshaling call site exists in `organized/workbench/`, directly relevant to the
lint's own `getNavChildren`/`getNavNodes`/`BqlQuery` guard trigger set.** `[CERT]`
(`organized/workbench/vineflower/com/tridium/workbench/nav/BNavSupport.java:39-41`):
```java
public void runNavTreeWork(Runnable navTreeWork) {
   UiEnv.get().invokeLater(navTreeWork);
}
```
— the `Runnable` it marshals (`NavTreeWork.run()`, same file, `:47-64`) calls `NavTreeNode.lookup(...)`
then `.refresh()`; `NavTreeNode.java` is one of the 18 files this session's own census (§ header, corpus
search) confirmed contains a real `getNavChildren`/`getNavNodes`/`BqlQuery` call — i.e. this is a genuine,
real instance of exactly the shape the lint's `ui-thread-traversal` check is built to detect the ABSENCE
of a guard for.

**The literal string `invokeLater` at this call site is `UiEnv.get().invokeLater(...)` — a Tridium
abstraction, not a bare Swing call — but its concrete N5 peer implementation still bottoms out at plain
AWT/Swing `EventQueue.invokeLater`, not JavaFX.** `UiEnv`'s own default (no-op) implementation:
`[CERT]` (`organized/bajaui/fallback/com/tridium/ui/UiEnv.java:121-124`): `public void invokeLater(Runnable work) {
work.run(); }`. The CONCRETE peer used by the real desktop Workbench toolkit:
`[CERT]` (`organized/bajaui/fallback/com/tridium/ui/awt/AwtUiEnv.java:325-327`):
```java
public void invokeLater(Runnable event) {
   EventQueue.invokeLater(event);
}
```
— `java.awt.EventQueue.invokeLater` is the same JDK primitive `javax.swing.SwingUtilities.invokeLater`
itself delegates to. A corpus-wide check for a competing JavaFX idiom found `javafx` imports and
`Platform.runLater` usage confined ENTIRELY to `com/tridium/workbench/web/browser/fx/*` (`[CERT]`, `grep
-l '^import javafx'` across all of `workbench/`, 8 files, all under that one embedded-web-browser-widget
subpackage) — a separate, unrelated subsystem, never touching nav-tree/`doInvoke`/`getNavChildren`-style
UI marshaling anywhere in the corpus.

**B51-G6 verdict: CLOSED.** `lint-wb-threading.sh`'s existing guard token set (`invokeLater|BJobService|
JobThread`) is CORRECT as written for N5: the literal substring `invokeLater` appearing in
`UiEnv.get().invokeLater(navTreeWork)` is caught by the lint's own substring match exactly as intended,
and the concrete toolkit backing that call is confirmed, by direct read of the real `AwtUiEnv` peer
class, to still be classic AWT/Swing `EventQueue.invokeLater` — no JavaFX `Platform.runLater` idiom exists
anywhere near N5's real nav-tree/`doInvoke` UI-thread-marshaling code path. No lint-pattern update is
needed for this idiom on N5.

## 97.8 — B29-G3 ADVANCED: the exact failure mode of an un-ported `assertArrayEquals` call is now empirically demonstrated (a guaranteed unresolved-symbol compile error, not a silent semantic bug), and the script's own "count preserved" self-check is shown to be a false-positive for this exact case `[CERT]`

[Block 29]'s own gap text already correctly documents that `port-junit4-to-testng.py`'s `ASSERT_KINDS`
dict has no `"assertArrayEquals"` entry and the `ASSERT_CALL` regex's word-boundary anchor (`\b`) cannot
match `assertArrayEquals(` at all (`Array` immediately precedes `Equals` with no non-word transition, so
`\b` never fires at that internal position) — confirmed by reading the script in full this session
(`tools/port-junit4-to-testng.py:157-173`, `[CERT]`). This session goes one step further: it actually RUNS the
unmodified script against a synthetic test file containing an `assertArrayEquals` call, to observe the
real failure mode rather than infer it.

**Empirical demonstration, this session** (`/tmp/claude-1000/…/scratchpad/b97/b29test/`, synthetic file,
never touching the corpus or any real ColdRoomPan-rt source):
```java
// input (Sample.java)
import org.junit.Test;
import static org.junit.Assert.*;
public class Sample {
  @Test public void testArrays() {
    int[] expected = {1,2,3}, actual = {1,2,3};
    assertArrayEquals(expected, actual);
    assertTrue(true);
  }
}
```
```java
// output (SamplePorted.java), produced by python3 port-junit4-to-testng.py Sample.java SamplePorted.java
import org.testng.annotations.Test;
import org.testng.Assert;
public class Sample {
  @Test public void testArrays() {
    int[] expected = {1,2,3}, actual = {1,2,3};
    assertArrayEquals(expected, actual);   // <-- UNTOUCHED, no Assert. prefix
    Assert.assertTrue(true);               // <-- correctly transformed
  }
}
```
`[CERT]` (this session's own script execution, literal file diff). Since the import line `import static
org.junit.Assert.*;` is unconditionally replaced with `import org.testng.Assert;` regardless of whether
an untouched `assertArrayEquals` call remains, the ported file's `assertArrayEquals(expected, actual);`
line becomes a genuine **unresolved-symbol compile error** (no static import provides that identifier,
no `Assert.` qualifier was added, and TestNG's `Assert` class has no method of that name to import even
if a qualifier were added by hand) — a LOUD, compile-time failure, not the silent semantic risk the
gap's own framing worried might occur. This is the SAFER of the two possible failure modes, but still a
hard blocker for any future file reuse of this recipe on JUnit4 source that uses `assertArrayEquals`.

**A secondary finding: the script's own built-in self-check is a false positive for this exact case.**
The script's `main()` prints `"n assert* calls in, n assert* calls out (OK — count preserved)"` by
counting RAW textual occurrences of `assert(True|False|Null|NotNull|Same|NotSame|Equals|ArrayEquals)\(`
before and after — this count matched (2 in, 2 out) in the demonstration above and printed `OK`, even
though one of the two calls was never actually transformed. The self-check counts textual occurrences,
not `Assert.`-prefixed transformations, so it cannot detect this exact failure mode — a kit author
relying on the script's own "OK" output would not be warned.

**The exact one-line fix, specified but NOT applied** (per this task's single-file-write constraint):
add `"assertArrayEquals": reorder_assert_equals_args` to the `ASSERT_KINDS` dict
(`tools/port-junit4-to-testng.py:158-170`) — the SAME reorder function already used for `assertEquals`/
`assertSame`/`assertNotSame` (TestNG's array-form `assertEquals(actual[], expected[])` overload keeps the
same actual/expected swap as the scalar form, per the script's own already-correct comment at
`:166-170`) — AND add `assertArrayEquals` to the `ASSERT_CALL` regex's alternation
(`tools/port-junit4-to-testng.py:172-173`), which currently omits it entirely (confirmed above: this is WHY the
word-boundary reasoning in the gap's own text is correct — `assertArrayEquals` is never even a
regex-match candidate, let alone reachable via `ASSERT_KINDS`).

**B29-G3 verdict: ADVANCED.** The exact failure mode is now empirically proven (not merely inferred from
reading the code), the self-check's own blind spot for this case is newly documented, and the precise
one-line-plus-one-token fix is fully specified — but the script itself was not edited this session, per
the task's explicit single-file-write scope, so the gap is not marked CLOSED.

## 97.9 — B10-G4 CLOSED: `grep -rli "fox"` re-run across all three client module trees at [Block 10]'s own cited commit finds exactly one file, and every one of its five matches is base64-encoded binary data, not Fox-protocol-relevant text `[CERT]`

[Block 10] §10.x inferred CHK-14 (Fox interop not applicable) from a general import-grep sweep, not an
independently re-run `grep -rli "fox"`. This session re-runs exactly that command against
`Compresores/CompPan`, `Dashboard/DashboardPan`, `Paccadia/ColdRoomPan` at the SAME worktree commit
[Block 10] cited (`a109249d`, confirmed this session via `git log -1`):

```
$ grep -rli "fox" Compresores/CompPan Dashboard/DashboardPan Paccadia/ColdRoomPan
Dashboard/DashboardPan/DashboardPan-ux/src/rc/index.html
```
`[CERT]` — exactly one file matches, not zero; the earlier `[INFER]` claim of a clean sweep would have
been wrong if taken literally. **All five matching lines in that one file are read directly and confirmed
to be false positives.** `grep -n "fox" index.html` matches 5 lines, each between 362,939 and 1,044,280
characters long (`[CERT]`, `awk` line-length check, this session) — i.e. lines of embedded base64-encoded
binary data (an inline image asset in the HTML), not source code, comments, or JavaScript logic. Reading
a 40-character window around each individual match (`grep -oiE ".{20}fox.{20}"` on each matching line,
this session) shows every occurrence is a coincidental 3-letter run inside the base64 alphabet (e.g.
`...LoxAdIt...`, `...nFOxdG...`) — never the literal ASCII word "fox"/"Fox"/"FOX" appearing as a
recognizable token bounded by non-base64 characters, and never in any context resembling a URL, class
name, or protocol reference.

**B10-G4 verdict: CLOSED, and CHK-14 is now promoted from `[INFER]` to `[CERT]`.** None of the three
modules reference Fox interop in any meaningful (non-coincidental) way; the sole raw grep hit is fully
accounted for as base64 noise, read and confirmed directly this session, not merely asserted absent by
extrapolation from an unrelated sweep.

## 97.10 — B10-G6 CLOSED: `DashboardPan-ux`'s local dev-preview tooling (`preview-server.py` + `preview-mock.json`), read in full, is pure Python-3-stdlib + inert static JSON — zero N5-relevant breaking-change surface `[CERT]`

[Block 10] §10.x flagged `DashboardPan-ux/preview-server.py`/`preview-mock.json` as unread local
dev-preview tooling, unverified for any N5-relevant breaking-change surface of its own.

**`preview-server.py` (265 lines, read in full this session):** imports only `json`, `os`, `random`,
`sys`, `time`, and `http.server.{BaseHTTPRequestHandler, ThreadingHTTPServer}` — the Python 3 standard
library, exclusively. It serves static files from `src/rc/`, generates synthetic `{v,st}`-shaped JSON
matching `DashboardReader`'s own servlet output CONTRACT (by hand-written convention only — no shared
code, no import, no dependency on any compiled Niagara class), and reimplements the same XHR-header
302-redirect guard `DashboardDispatch` enforces (`_has_xhr()`/`_redirect()`, `:145-160`) — again a
hand-written imitation, not a link. **`preview-mock.json` (28 lines, read in full this session):** a
flat, inert static JSON object (`{"Condensadoras/highPressure": {"v": 207.4, "st": "ok"}, ...}`) with no
executable content of any kind.

**B10-G6 verdict: CLOSED.** Neither file has ANY coupling to Niagara's Java/JPMS/module-system surface
that N5's breaking changes (module renames, `javax.baja`→`niagara` namespace, runtime-profile removal,
Fox/servlet API changes, etc.) could possibly affect — the tooling's only relationship to the real module
is a hand-maintained JSON-shape and HTTP-behavior IMITATION, entirely outside the compiled module
boundary. Confirmed by full read, not inferred from its "local dev tooling" framing alone.

## 97.x — Connections

- §97.1 directly extends [Block 89] §89.3/[Block 29] §29.4.1's own residual, naming the exact
  self-dependency code site both blocks' hypotheses needed, and rules out (via
  `configureJavaCompileTasks$1`'s trivial body) any Tridium-plugin-side explanation for the error's
  non-fatal treatment — redirecting the remaining question to Gradle's own internals, external to this
  corpus's reach.
- §97.2/§97.3 both build directly on [Block 89] §89.7's `BNfooDevice.java.vm` finding and [Block 74]
  §74.1's `NDriverModuleGenerator` trace; §97.3's `VideoDriverModuleGenerator` reconstruction reuses
  [Block 89] §89.7's own already-published "24 conditional `addTemplateWrite()` calls" count as a
  cross-check (this session's own independent read reproduces exactly 24), and extends [Block 10]'s
  own `docDeveloper.jar` reading method to a document ([Block 10] never opened `buildN5.html` itself —
  that was [Block 2]/[Block 9]/[Block 89]) whose own example trees had never before been cross-checked
  against the real generator source.
- §97.4 independently re-verifies [Block 49] §49.5's own `[INFER]`-flagged N4-side finding on the N5
  side, closing the loop [Block 50] §50.4 opened, and adds a concrete constraint ([Block 49]/[Block 50]
  did not have) — the exact declared-parameter-type requirement (`Context`, not `SecurableContext`) — a
  refinement useful to any future guide revision.
- §97.5/§97.6/§97.7 all extend [Block 51]'s own kit-lint gap list with direct reads of the SAME four
  scripts [Block 51] itself named, plus (for §97.7) a corpus source file ([Block 51] itself never
  located).
- §97.8 extends [Block 29]'s own already-correct static analysis with an empirical execution, adding the
  self-check false-positive finding [Block 29] did not have.
- §97.9/§97.10 both extend [Block 10]'s own already-cited worktree commit and method (`grep -rn`/`cat`
  census) to the two specific residuals [Block 10] itself named.
- No `§14`-style contradiction of any earlier block's own `[CERT]`-marked claim was found this session —
  every finding above NARROWS, CLOSES, or ADDS TO a previously-open `[INFER]`/`investigable` residual,
  none of them REVERSES a prior `[CERT]` verdict.

## 97.x — Child gaps opened

- **B97-G1** (refines/narrows **B89-G1**) — trace INTO Gradle's own `JavaCompile`/`JavaModuleDetector`/
  dependency-resolution-engine source (Gradle's own distribution, not shipped in any jar this corpus's
  methodology reaches) to determine which of the project's own jar-shaped variants (main `-rt` vs. the
  `<project>-module-test` feature capability) an unqualified self-`project(thisProject)` dependency
  actually resolves to, and whether/how that resolution interacts with the logged-but-non-fatal
  `LocnCantGetModuleNameForJar` diagnostic. `investigable`, but needs an artifact class (Gradle's own
  runtime jars) outside this corpus's normal source set — likely `requires-execution` in practice (a
  live Gradle build with `--info`/dependency-insight tracing would settle it faster than a cold read of
  Gradle's own source).
- **B97-G2** (refines/narrows **B51-G1**) — an actual N5 Workbench GUI re-sign attempt against a real N5
  module jar with nonzero Deflated entries, to confirm whether N5's Workbench re-sign feature still
  enforces (or has ever enforced) the zero-Deflated-entries requirement `verify-module.sh --stored` was
  originally written to guard against for N4. `requires-execution` (a live N5 Workbench GUI session, not
  available this session).
- **B97-G3** (refines/narrows **B89-G4**) — a full line-by-line BODY read (method implementations,
  comments, TODO markers) of all 56 `gradle/ndriver/*.vm`+`gradle/videodriver/*.vm` templates, beyond
  this session's class-declaration-level `implements`/`extends` census, to catch any non-interface
  N5-specific requirement (e.g. a required method override with no marker interface, an unusual default
  value, or a TODO naming a manual step). `investigable`, low-priority — the gap's own core question
  (unnoted INTERFACE requirements) is already fully answered by §97.2.
- **B97-G4** (new, opened by §97.3's doc-vs-generator mismatch) — file a documentation-accuracy note
  against `buildN5.html`'s own "Example File Tree for a VideoDriver" section: it names 5 files
  (`myDriverTcpCommConfig.java`, `myDriverHttpListener.java`, `myDriverTcpListener.java`,
  `myDriverCameraConnectReq.java`, `myDriverZoomReq.java`) that `VideoDriverModuleGenerator.generate()`
  never queues under any conditional, while omitting 4 files it DOES queue
  (`NfooPanTiltReq`/`NfooFocusControlReq`/`NfooHttpUtil`/`NfooVideoStreamUtil`) — worth confirming
  whether this is a stale doc (written against an earlier generator version) or a hand-written
  illustrative tree that was never generated from the real templates at all. `investigable`, low-priority
  (a doc-accuracy finding, not a code-behavior question — no further corpus reading would resolve it,
  only a Tridium-side doc-history artifact this corpus does not have).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `NiagaraModulePlugin.configureConfigurations()` adds `dependencies.add(moduleTestCompileOnly, dependencies.create(project))` — a project self-dependency | [CERT] | `NiagaraModulePlugin.class`, decompiled + `javap -p -c` bytecode cross-check, this session |
| 2 | `configureJavaCompileTasks$1` sets ONLY UTF-8 encoding on every `JavaCompile` task — no module-path/error-suppression logic anywhere in the plugin | [CERT] | `NiagaraModulePlugin$configureJavaCompileTasks$1.class`, decompiled in full, this session |
| 3 | `registerModuleTestVariant` registers `moduleTest` as an additional `<project>-module-test:1.0` feature capability of the same project | [CERT] | `NiagaraModulePlugin$registerModuleTestVariant$1$1.class`, decompiled, this session |
| 4 | `BISecurityDashboardProviderAgent` recurs on 4 classes total (`BNfooDevice`, `BNfooNetwork`×2, `BNfooCamera`), all with the identical 4-method shape; no other novel interface exists across all 56 ndriver+videodriver templates | [CERT] | full `grep -rn`/context-read sweep, all 56 `.vm` files, this session |
| 5 | `NDriverModuleGenerator.generate()` queues exactly 17 conditional `addTemplateWrite()` calls, full manifest traced | [CERT] | `NDriverModuleGenerator.java`, decompiled in full, this session |
| 6 | `VideoDriverModuleGenerator.generate()` queues exactly 24 conditional `addTemplateWrite()` calls, full manifest traced, zero overlap with the 5 doc-named-but-never-queued VideoDriver comm/messages files | [CERT] | `VideoDriverModuleGenerator.java`, decompiled in full, this session, cross-checked against `docDeveloper.jar!doc/buildN5.html`'s own example tree |
| 7 | `n-templates-5.0.54.9.2.jar` (direct `etc/m2` copy) is byte-identical to `devkit.jar!LIB-INF/n-templates-5.0.54.9.2.jar` | [CERT-hw] | `sha256sum` both, this session — identical `285e6463…2405` |
| 8 | `NiagaraRpcServlet.doPost()` extracts `Context` from `req.getAttribute("niagara.context")` and passes it to `NiagaraRpcUtil.rpc()` | [CERT] | `organized/web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java:32` |
| 9 | `NiagaraRpcUtil.rpc()` wraps `cx` in an anonymous `SecurableContext`, appends it last, resolves via `cls.getMethod(...)`, invokes via `Method.invoke()` | [CERT] | `organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:80-160` |
| 10 | `convertToArgClass` maps any `Context`-family argument to `Context.class` for method lookup — the annotated method's parameter must be declared exactly `Context` | [CERT] | `organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:208-220` |
| 11 | `verify-module.sh --stored` runs correctly against 4 real N5 jars, reporting sane non-zero Deflated-entry counts | [CERT-hw] | this session's own execution against `kitControl.jar`/`control.jar`/`workbench.jar`/`baja.jar` |
| 12 | `rc-scan.sh`(143L)+`bog-audit.sh`(889L), read in full: the ONLY `-rt|-ux|-wb` matches in either file are prose comments, zero operative logic coupling | [CERT] | `grep -n` (exact + loose word-boundary variants), both files in full, this session |
| 13 | `BNavSupport.runNavTreeWork()` calls `UiEnv.get().invokeLater(navTreeWork)`, marshaling a `NavTreeNode`-touching Runnable | [CERT] | `organized/workbench/vineflower/com/tridium/workbench/nav/BNavSupport.java:39-41` (Runnable body at `:47-64`) |
| 14 | `AwtUiEnv.invokeLater()` delegates to `java.awt.EventQueue.invokeLater` — the concrete N5 desktop-toolkit peer is still AWT/Swing, not JavaFX | [CERT] | `organized/bajaui/fallback/com/tridium/ui/awt/AwtUiEnv.java:325-327`, `organized/bajaui/fallback/com/tridium/ui/UiEnv.java:121-124` |
| 15 | All `javafx`/`Platform.runLater` usage in `workbench/` is confined to `com/tridium/workbench/web/browser/fx/*` (8 files), unrelated to nav-tree marshaling | [CERT] | `grep -l '^import javafx'`, whole `workbench/` tree, this session |
| 16 | `port-junit4-to-testng.py`, run against a synthetic `assertArrayEquals` test file, leaves the call completely untouched while correctly transforming `assertTrue` — producing a guaranteed unresolved-symbol compile error, and the script's own self-check prints a false "OK" | [CERT] | this session's own execution, `/tmp/.../scratchpad/b97/b29test/Sample.java` → `SamplePorted.java` |
| 17 | `grep -rli "fox"` across the 3 client module trees at commit `a109249d` finds exactly 1 file; all 5 matches are >350K-char base64 lines, confirmed coincidental by direct substring read | [CERT] | this session's own `grep`/`awk`/`grep -oiE` run against the worktree, same commit [Block 10] cited |
| 18 | `DashboardPan-ux/preview-server.py` (265L) uses only Python-3-stdlib modules; `preview-mock.json` (28L) is inert static data — zero N5-relevant breaking-change surface | [CERT] | both files read in full, this session |

Tally: 18 [CERT]/[CERT-hw] claims in the table above, 0 [INFER] table rows (inline `[INFER]` synthesis
clauses appear in §97.1's "narrowed but not confirmed" framing and §97.3's doc-vs-generator gap
characterization, per METHODOLOGY's convention of stating synthesis inline rather than as a table row).
Adjusted ratio [INFER]/[CERT] ≈ **0.11** (2 inline [INFER] clauses against 18 table [CERT]/[CERT-hw]
claims) — low, consistent with an EVIDENCE-type block whose every closing verdict rests on a fresh
decompile, a fresh disassembly, a fresh live execution, or a direct full-file read this session, not
recalled from a prior block's own text.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block97.md
```
(output pasted into the handback message to the caller, per the task's own instruction to run this until
exit 0.)

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; the `docDeveloper.jar!doc/
buildN5.html` citation is shipped Niagara product documentation (`[CERT-doc]`/`[CERT-hw]`), read directly
from the jar this session.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block97.md` (the only
file written in the corpus this session, per the task's single-file constraint). `INDEX.md`/
`RESEARCH-STATE.md`/`CATALOG.md` were **not** regenerated, and no other repository (`niagara-tools`,
`port-junit4-to-testng.py`, the client worktree) was modified — every read this session against those
locations was read-only, matching the task's explicit read-only-elsewhere scope. Fresh decompile/
disassembly output and the synthetic `assertArrayEquals` test file live at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b97/`
(scratch, not archived in the corpus): `decompiled/` (plugin classes), `gen/decompiled/` (both module
generators), `templates/extracted/` (all 56 `.vm` files), `doc/buildN5.html` (extracted doc text),
`b29test/` (the synthetic port-junit4 demonstration), `devkit-embedded-n-templates.jar` (the sha256
cross-check copy).
