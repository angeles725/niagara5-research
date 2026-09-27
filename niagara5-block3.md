# Block 3 — N5 boot and runtime on JRE 25: classpath-to-JPMS migration, a bespoke `ModuleLayer` bootstrap, and a ByteBuddy-agent replacement for `SecurityManager`

> **Scope**: Closes gap **N5-G7** (Boot/runtime: NRE on JRE 25, bin layout, `nre.properties`/`system.properties`,
> JPMS module loading). Covers the native launchers in `bin/`, the bundled JRE, the two property files that
> configure NRE at launch, the classpath→module-path transition, the `com.tridium.nre.bootstrap.Bootstrap`
> class that builds a second `ModuleLayer` for `baja.jar`, and the concrete mechanism that replaces the
> JDK `SecurityManager` (removed upstream) — a `-javaagent` (`SecurityAgent`) that uses ByteBuddy to weave
> "advice" around JDK file/network/process/security-provider APIs and route them through Niagara's own
> `PermissionManager`. Does **not** cover: the full module inventory delta (→ N5-G2), module-signing/ZKM
> profile (→ N5-G3), the `javax.baja.*`→`niagara.*` core-API rename in full (→ N5-G5, touched here only
> where it is the boot-facing `Sys` class), or the build toolchain (→ N5-G6).
>
> Subject version: **N5 5.0.0.28 (Beta)** — confirmed by `etc/brand.properties:workbench.notice` ("This is
> a Beta version...") — vs. baseline **N4 4.14.0.162** (Honeywell OptimizerSupervisor OEM distribution;
> see caveat in §3.4). JRE: N5 bundles **Azul JRE 25.0.4.7 / `JAVA_VERSION="25.0.4"`**; N4 bundles Azul
> JRE **1.8.0.412.20** (Java 8).
>
> Sources (all local, read-only):
> - `/mnt/c/Program Files/Niagara/5.0.0.28/` — `bin/` (launchers, DLLs, `bin/policy/`, `bin/ext/*.jar`+`.sig`),
>   `jre/` (`release`, `jreVersion.xml`), `defaults/` (`nre.properties`, `system.properties`, `platform.bog`,
>   `workbench/`), `etc/` (`brand.properties`, `extensions.properties`), `*.lnk` shortcuts.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/` — top-level dirs (`cleanDist`, `etc`, `eula`,
>   `jar-cache`, `modules/` [247 jars], `registry`, `security`, `sw`) and `modules/baja.jar`, `modules/bacnet.jar`,
>   `modules/web.jar`.
> - `/mnt/c/ProgramData/Niagara/tridium/daemon/5.0/`, `/mnt/c/Users/equipo/Niagara/tridium/5.0/` — `.lnk` targets.
> - `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/` — same layout, N4.14 baseline (`bin/`, `jre/`,
>   `defaults/`, `modules/baja.jar`).
> - Decompiled/disassembled locally with `javap` (`/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap`,
>   version 26.0.2.1) against extracted `.class` files (scratch dirs `/tmp/n5extract`, `/tmp/n4extract` —
>   not part of the corpus; re-derivable from the jars cited).
> - REMITTANCE baseline: `niagara-research` corpus (target #1, N4-only) via
>   `python3 /home/cristian/niagara-research/tools/corpus-nav.py find nre.properties` and `find SecurityManager`.
>
> Method: direct file reads (`cat`/`sed`), `strings` on native `.exe`/`.dll` for embedded JVM-arg templates,
> `diff`/`grep` for property-file deltas, `unzip -p`/`unzip -l` + `javap -p` / `javap -verbose` / `javap -c -p`
> for jar manifests, `module-info.class` descriptors, and one method's bytecode disassembly
> (`Bootstrap.Main`). No decompiler (CFR/Vineflower) was available in this session; conclusions about
> `Bootstrap.Main`'s control flow are read directly off the `javap -c` instruction stream (offsets cited as
> `Bootstrap.class:offset <n>` — there are no source line numbers for a class file with no shipped source).
> Markers: `[CERT]` local primary (file/binary/bytecode opened) · `[CERT-doc]` n/a this block ·
> `[INFER]` deduction. Every `[CERT]` below was read this session; none is carried from memory.
>
> Runtime/boot layer. Connects [Block 1] / [Block 2] (N5 module inventory and packaging, if written —
> this block's §3.7 and §3.11 supply the packaging evidence a module-inventory block would consume) and,
> across corpora, `niagara-research` B17 (N4 filesystem forensics + JRE), B26 (NRE launcher + native DLLs),
> B31 (`nre.properties` + thread pools), B1021 (shipped-default vs installed `nre.properties`), B533
> (`station.java.options` as the javaagent persistence vector), B635/B18/B1‑3/B29/B541/B330/B572/B800/B806
> (N4's `SecurityManager` + `java.policy` sandbox — the mechanism N5 replaces).
>
> **Type:** standard

---

## 3.1 — Identity: two installs, two JREs, one launcher family `[CERT]`

| | N5 5.0.0.28 (Beta) | N4 4.14.0.162 (Honeywell OEM) |
|---|---|---|
| `bin/nreVersion.xml` | `name="nre-core-win-x64" version="5.0.0.28"` | `name="nre-core-win-x64" version="4.14.0.162"` |
| `jre/jreVersion.xml` | `name="azul-jre-win-x64" vendor="Tridium" version="25.0.4.7" description="Azul ZRE"` | `name="azul-jre-win-x64" vendor="Azul Systems, Inc" version="1.8.0.412.20"` |
| `jre/release` | `JAVA_VERSION="25.0.4"`, 40+ listed `MODULES` incl. `javafx.*`, `jdk.incubator.vector`, `jdk.attach` | absent (Java 8 JRE ships no `release` file) `[CERT]` (`cat` exit 1) |
| Class file major version | **69** (Java 25) | not applicable (Java 8, no module classes) |
| Beta marker | `etc/brand.properties:workbench.notice=This is a Beta version. It is provided solely for testing and evaluation purposes...` | none |

`[CERT]` all four rows read verbatim from the cited files. The JRE vendor string changed from
`"Azul Systems, Inc"` to `"Tridium"` between N4 and N5 — Tridium now brands the bundled JRE build itself,
not just the wrapping NRE. `[CERT]` (`jreVersion.xml` both installs)

## 3.2 — `bin/` layout: same launcher set, one policy file dropped, `bin/ext/` triples in size

| File | N5 | N4 | Note |
|---|---|---|---|
| `nre.exe`, `station.exe`, `wb.exe`, `wb_w.exe`, `test.exe`, `plat.exe`, `niagarad.exe`, `console.exe`, `n5mig.exe`/`n4mig.exe`, `nre.dll`, `njre.dll`, `common.dll`, `alarmDialog.dll`, `trayIcon.dll`, `lon.dll`, `pcapBacEther.dll`, `cppunit.dll` | present | present | launcher family unchanged `[CERT]` |
| `n5mig.exe` / `n4mig.exe` | `n5mig.exe` | `n4mig.exe` | migrator renamed to match version, same role `[INFER]` |
| `dsfspi.dll`, `honImport.dll`, `hdbt.exe`, `nverify.exe`, `opc*.dll`, `uninstall.exe` | **absent** | present | Honeywell-OEM tooling (Optimizer import, uninstaller, OPC) not carried into this stock N5 beta — expected: N5 install here is stock Tridium, not yet OEM-repackaged `[INFER]` |
| `bin/policy/` | `java.security`, `signing.properties` (**2 files**) | `java.policy` (271 lines), `java.security`, `signing.properties` (**3 files**) | **`java.policy` is not shipped in N5** `[CERT]` (`ls` both dirs) |
| `bin/ext/*.jar` | **73** jars | **27** jars | +46 jars; new: full Jetty 12 EE11 stack (`jetty-ee11-*`), `jose4j`, `okhttp`/`okio` (jvm split), `resilience4j-core/-retry`, `byte-buddy`, `asm`/`asm-commons`/`asm-tree`, `niagara-remote-client`, `kotlin-stdlib` (+`jdk7`/`jdk8` shims), `angus-activation`, `httpclient5`/`httpcore5`(+`h2`), `jakarta.*` (servlet 6.1, cdi 4.1, el 6.0, enterprise, interceptor, inject) `[CERT]` (`ls` diff both `ext/` dirs) |
| `bin/x86/` | `ldvProxy.exe` + 2 DLLs | present (not itemized this pass) | new/renamed native helper `[INFER]` — not traced further (out of scope) |

The removal of `bin/policy/java.policy` is the single strongest **structural** signal that the classic
`SecurityManager`+`Policy` sandbox is gone in N5 — a codebase that still used `Policy.getPolicy()` would
need a policy file to grant anything. §3.8 confirms this with the replacement mechanism.

## 3.3 — `nre.properties`: same 4-profile schema, N5 ships all four **empty**

Both installs define the identical four-key schema (`station.java.options`, `wb.java.options`,
`test.java.options`, `nre.java.options`) with an identical header comment block. `[CERT]`
(`defaults/nre.properties`, both installs, header text diff only in copy-edits — N5 fixed "initialze"→
"initialize" and "specfied"→"specified", `excutables`→`executables`)

| Key | N5 `defaults/nre.properties` | N4 `defaults/nre.properties` |
|---|---|---|
| `station.java.options` | *(empty)* | `-Dfile.encoding=UTF-8 -Xss512K -Xmx1024M` |
| `wb.java.options` | *(empty)* | `-Dfile.encoding=UTF-8 -Xss512K -Xmx1024M` |
| `test.java.options` | *(empty)* | *(undefined — not even a key; matches REMITTANCE B1021 "test.java.options and nre.java.options... neither key" finding for N4.14 too)* |
| `nre.java.options` | *(empty)* | *(undefined)* |
| `softjace` | *(absent)* | `false` |

`[CERT]` both files read verbatim. N5 ships **no default heap/stack tuning at all** — every launcher gets
whatever the Azul JRE 25 heuristics pick. This is a meaningful behavioural delta from N4, where
REMITTANCE `niagara-research` B31/B1021 document `-Xmx1024M`/`-Xss512K` as the load-bearing station default
(B31: "Heap 1 GB default... explains Bloque 13.1.7 Supervisor bottleneck") and B533 documents
`station.java.options` as *the* persistence point for a `-javaagent` at station boot. On N5 that same key
exists and is still the mechanism (§3.6 confirms N5's own agent, `SecurityAgent`, is wired via
`-javaagent`-equivalent instrumentation at native-launcher level, not via this property — see §3.8), but
the property itself starts blank, so any heap/agent tuning on N5 must be added by the installer/OEM rather
than inherited from Tridium's shipped default. `softjace` (Windows host-ID prefixing toggle) is present in
N4, absent from N5's file entirely — `[CERT]` (grep, no match) — `[INFER]` dropped or now hardcoded/detected
rather than configured.

## 3.4 — `system.properties`: schema shrinks from 759/589 lines to a smaller active surface

Both files share the same header/purpose comment ("loaded into `System.getProperties()` during NRE boot").
`[CERT]` N5's file is longer overall (**759 lines** vs N4's **589**) because it documents many more knobs
in comments (jetty/thrift/cloud-related), but far fewer are **active** (uncommented) by default:
N5 has **3** active non-comment keys, N4 (this OEM build) has **17**. `[CERT]` (`wc -l` + non-comment
`grep` count, both files)

**Caveat before reading the table**: `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162` is a
Honeywell-branded OEM distribution, not a stock Tridium N4.14 install — 6 of its 17 active keys carry
non-default *values* (see below), meaning this specific installer activates settings Tridium ships
commented-out. The **absence** of a key from N5's file entirely (not even as a commented default) is
still solid `[CERT]` evidence the key left N5's *documented* schema — but "N4 had it active, N5 doesn't"
partly reflects this OEM's customization on top of the N4 core, not a pure core-vs-core delta. Framed
this way:

| Key | N4 (OEM) value | N5 status | Read as |
|---|---|---|---|
| `niagara.steadystate` | `10000` (active) | `#niagara.steadystate=10000` (commented, same default) | schema kept, this OEM activated it |
| `hx.poll.freq` | `5000` (active) | `#hx.poll.freq=5000` (commented, same default) | schema kept |
| `niagara.fox.circuitMaxReceiveBuffer` | `10240000` (active) | `#niagara.fox.circuitMaxReceiveBuffer=102400` (commented, **100× smaller** default) | schema kept, default shrunk 100× |
| `niagara.license.subscriptionLicenseAllowed` | `true` (active) | `#niagara.license.subscriptionLicenseAllowed=false` (commented, **opposite** default) | schema kept, default flipped |
| `niagara.ui.px.maxImageModuleFileSize` | `2047` (active) | `#niagara.ui.px.maxImageModuleFileSize=65535` (commented, **32× larger** default) | schema kept, default raised |
| `niagara.ui.pxCache.max` | `10` (active) | `#niagara.ui.pxCache.max=10` (commented, same default) | schema kept |
| `bajaui.hasKeyboard` | `true` (active) | **absent, no trace** | schema-level drop `[CERT]`/`[INFER]` |
| `ie.activex.activation` | `true` (active) | **absent, no trace** | schema-level drop — matches ActiveX/IE removal expectation on a modern stack `[INFER]` |
| `niagara.fox.broker.unsubscribeDelay` | `5000` (active) | **absent, no trace** | schema-level drop |
| `niagara.fox.transport.ip` | `fox:com.tridium.fox.sys.BFoxAddress$IpTransportHandler` (active) | **absent, no trace** | schema-level drop |
| `niagara.ipv6Enabled` | `false` (active) | **absent, no trace** | schema-level drop |
| `niagara.moduleVerificationMode` | `low` (active) | **absent, no trace** | schema-level drop |
| `sun.java2d.noddraw` | `true` (active) | **absent, no trace** | schema-level drop |

`[CERT]` every cell above is a direct `grep -n "^#*<key>="` read of both files this session; the 7
"absent, no trace" rows were re-confirmed with a case-insensitive whole-file grep (`grep -in`, exit 1 —
zero matches, not even inside a comment). Present unchanged in both, active in both:
`jdk.lang.Process.allowAmbiguousCommands=true`, `jdk.tls.rejectClientInitiatedRenegotiation=true`,
`niagara.fox.exceptionTranslator=com.tridium.fox.sys.LocalizableExceptionTranslator`. `[CERT]`

## 3.5 — Boot mechanism: N4 is classpath, N5 is JPMS module-path — confirmed inside the native launcher

`strings` on the native launcher DLLs shows the actual JVM invocation templates baked into the binaries
that build the `JNI_CreateJavaVM` argument vector. `[CERT]` (`strings` output, both `nre.dll`s, this session)

**N4 `nre.dll` / `njre.dll`** — classic classpath boot:
```
FATAL: Failed to append all items in extPath to classpath, insufficient buffer size
nre>   classPath                = %s
java>   classPath                = %s
```
No `--module-path`, no `--add-opens`, no `--add-exports` strings anywhere in either N4 DLL.

**N5 `nre.dll`** — JPMS module-path boot, **26** distinct `--add-opens=` templates and **4**
`--add-reads=` templates baked in, plus:
```
--add-modules=ALL-MODULE-PATH,ALL-DEFAULT
--module-path=%s
-Xbootclasspath/a:%s\bin\ext\securityBridge\securityBridge.jar
```
The opened targets are all `...=niagara.nre` (the module the native launcher itself resolves) and span
`java.base` (`java.io`, `java.lang`, `java.net`, `java.security`, `java.util`, `sun.security.provider`),
`java.desktop/java.awt`, `java.xml.crypto/org.jcp.xml.dsig.internal.dom`, `javafx.web` (2 packages), and
**11** third-party module packages: 6× BouncyCastle FIPS/provider/TLS internals, 5× Eclipse Jetty 12 EE11
internals (`client`, `ee11.servlet`, `ee11.websocket.jetty.server`, `security.authentication`,
`server`/`server.handler`, `session`, `util.ssl`, `websocket.api`). The 4 `--add-reads=` grant `niagara.nre`
and `okhttp3` read access to the BouncyCastle FIPS/non-FIPS module pairs. `njre.dll` additionally carries
`--add-exports=niagara.nre/com.tridium.nre.security.permissions.restricted=niagara.niagarad` — a
package-level export scoped specifically to the daemon module. `[CERT]` (full `strings` capture, this session)

**Reading this**: N5's native launcher constructs the JVM boot module layer with `niagara.nre` (`nre.jar`)
resolved via `--module-path`, and grants it deep-reflection access to a hand-picked set of JDK-internal and
third-party-module internals it needs for TLS/crypto (BouncyCastle FIPS), the embedded web server (Jetty
12), and JavaFX WebView (JxBrowser host). None of this exists in N4 because N4 has no module system at
all — everything, including `bin/ext/*.jar`, is a flat classpath entry.

## 3.6 — `com.tridium.nre.bootstrap.Bootstrap`: a second, hand-built `ModuleLayer` on top of the JVM boot layer

`nre.jar`'s manifest carries `Automatic-Module-Name: com.tridium.nre` **and** a real `module-info.class`
declaring the module `niagara.nre@5.0.0.28` (requires `java.base`, `java.logging`, `java.management`,
`java.xml`, `niagara.niagaraAnnotationProcessors`, `kotlin.stdlib`, 4 BouncyCastle-FIPS modules, `org.json`,
`jakarta.servlet`, `okhttp3`, `org.apache.thrift`, `jakarta.annotation`, 8 Jetty-12 modules, `org.jose4j`,
`java.instrument`, `net.bytebuddy`). `[CERT]` (`javap -verbose module-info.class`) **When a real
`module-info.class` is present, the manifest's `Automatic-Module-Name` is inert** — the actual module name
is the one in the descriptor. This is directly demonstrated: `baja.jar`'s manifest says
`Automatic-Module-Name: com.tridium.baja`, but its `module-info.class` names the module
**`niagara.baja@5.0.0.28`**. `[CERT]` (`javap -verbose` on both `module-info.class` files)

`nre.jar` ships a `Premain-Class: com.tridium.nre.security.advice.SecurityAgent` (§3.8) and the actual boot
driver, `com.tridium.nre.bootstrap.Bootstrap`, whose `public static void Main(String[])` is the real entry
point the native launcher calls after JVM creation (fields: `BOOT_TIME`, `isStation`, `isTest`,
`niagaraBootModuleLayerController : ModuleLayer.Controller`, `loader : BootstrapClassLoader`,
`BAJA_JPMS_MODULE_NAME`, `BAJA_NMODULE_NAME`). `[CERT]` (`javap -p Bootstrap.class`)

**Traced from the `javap -c` disassembly of `Bootstrap.Main`** (bytecode offsets, no source shipped):

1. Resolve `<niagara.home>/bin/ext/baja.jar`... no — resolve the module's on-disk jar via
   `Path.of(URI)`/`.resolve("baja.jar")`, open it as a `java.util.jar.JarFile` (offset 238–250).
2. Read its `module-info.class` bytes and pass them through
   `com.tridium.nre.module.ModuleDescriptorAugmenter.augmentModuleDescriptorWithAutoPackageExports(ModuleDescriptor)`
   before use (constant-pool entries `#218`/`#219`) — **the shipped descriptor is rewritten at boot time to
   auto-export additional packages**, not used as-authored. `[CERT]` (constant pool + call site, offsets
   around 214–228)
3. Build a `Bootstrap$BajaModuleReference` from the augmented descriptor + jar URI, wrap it in a custom
   `Bootstrap$BajaModuleFinder` (a `ModuleFinder` implementation with exactly one entry), and resolve a
   **child `Configuration`** against it: `Configuration.resolve(bajaFinder, List.of(JVM_BOOT_MODULE_LAYER
   .configuration()), ModuleFinder.of(), Set.of("niagara.baja"))` (offsets 417–460). `[CERT]`
4. Define a **new child `ModuleLayer`** from that configuration, parented on the JVM boot layer:
   `ModuleLayer.defineModules(configuration, List.of(JVM_BOOT_MODULE_LAYER), classLoaderFn)` →
   `ModuleLayer.Controller`, stored in the static field `niagaraBootModuleLayerController` (offset 548–559).
   `classLoaderFn` supplies the custom `BootstrapClassLoader` (constructed earlier). `[CERT]`
5. Programmatically wire the new `niagara.baja` module into the boot layer's `niagara.nre` module and
   several JDK/Jetty/BouncyCastle modules via **runtime** `Module.addOpens(String, Module)` calls (offsets
   562–920+: `java.xml.crypto`, `org.eclipse.jetty.client`/`.security`/`.ee11.servlet`/`.server`/`.session`/
   `.util`/`.websocket.api`/`.ee11.websocket.jetty.server`, `org.bouncycastle.tls`,
   `org.bouncycastle.provider`, …) — the SAME target set the native launcher's `--add-opens` already grants
   to `niagara.nre`, now extended in-process to `niagara.baja` because that module did not exist yet when
   the JVM started and so could not be named on the command line. `[CERT]`
6. Call `ModuleLayer.Controller.enableNativeAccess(Module)` on the relevant module — the JDK 22+/24+
   "restricted native access" opt-in — confirming N5's boot path is written against a genuinely current
   JDK integrity model, not merely compiled for one. `[CERT]` (`enableNativeAccess` call site, offset ~634)
7. Conditionally, **only when `isTest` is true**, look up `niagara.niagarad` and wire it too (offset
   712–750: `getstatic isTest; ifeq 1155` gates this whole block) — matching the `test:niagara.test.TestRunner`
   entry-class mapping also present in the constant pool. `[CERT]`
8. FIPS handling: `overrideFipsModeOnStart(String)` accepts literal `-fips=false`/`-fips=true` flags,
   backed by a workbench-user config fragment default `<p n="startWorkbenchInFipsMode" v="false"/>`
   (`FIPS_OPTIONS_FRAGMENT_PATH`). `[CERT]` (constant-pool strings `#34`, `#40`, `#511`)
9. `com.tridium.sys.station.Station` is still the literal station main class name referenced from
   `Bootstrap` (constant `#45`) — **the station's entry class did not change name** even though everything
   around how it gets classloaded did. `[CERT]` — corroborates REMITTANCE `niagara-research` B1236
   ("`station.exe` ... Equivale a `nre com.tridium.sys.station.Station <stationName>`").

**Net finding for "how modules become a `ModuleLayer`" (partial answer, rest is a named child gap)**: N5
boots in two stages. Stage 1 is the native launcher creating the JVM with `niagara.nre` (`nre.jar`) as a
named module in the **JVM's own boot layer**, resolved via `--module-path` and pre-opened to ~19 JDK/3rd
-party module targets via baked-in `--add-opens`/`--add-reads`. Stage 2 is `Bootstrap.Main`, running inside
that module, hand-building a **second, child `ModuleLayer`** containing exactly one module — `niagara.baja`
— via a bespoke single-entry `ModuleFinder`/`ModuleReference`/`ClassLoader`, then patching its cross-module
`addOpens` wiring programmatically because the command-line flags could not have named a module that did
not exist at process-start. Every one of N5's ordinary content modules also ships a `module-info.class`
(confirmed for `baja.jar`, `bacnet.jar`, `web.jar` — all three carry both `META-INF/module.xml` **and** a
root `module-info.class`, §3.7), but **how the other ~245 modules get resolved into layers at station/
workbench runtime was not traced this session** — `Bootstrap.Main` only handles `baja.jar` by name; the
rest is almost certainly driven by `com.tridium.nre.module.*` (`NModuleModuleReader`,
`NiagaraModuleReference`, `SafeCloseModuleReader` — all present in `nre.jar`, none decompiled this pass)
and/or `NRegistry` (`com/tridium/sys/registry/NRegistry.class`, present in `baja.jar`, not decompiled).
→ **child gap B3-G1**.

## 3.7 — Every N5 module is a real JPMS module now; `module.xml` keeps `schemaVersion="5"` and drops `runtimeProfile`

`baja.jar`, `bacnet.jar`, and `web.jar` (spot-checked; a representative core/driver/web module) each carry
**both** `META-INF/module.xml` **and** a root `module-info.class`. `[CERT]` (`unzip -l`, 3 jars)
`baja.jar`'s N5 `module.xml` root element: `<module name="baja" ... moduleName="baja" schemaVersion="5"
releaseDate="2026-03-11">` with `<nre name="nre-core-*" version="5.0.0.28".../>` inside
`<installation><dependencies>` — the module declares its NRE dependency by the same `nre-core-*` name
pattern the launcher's own `nreVersion.xml` publishes (`nre-core-win-x64`). `[CERT]` N4's `module.xml` root
element for the same module: `<module name="baja" ... moduleName="baja" runtimeProfile="rt"
releaseDate="2024-05-28">` — **no `schemaVersion` attribute at all**, and carries `runtimeProfile="rt"`
(the `-rt`/`-ux` split), which N5's `module.xml` does not have. `[CERT]` (both `module.xml`, root-tag diff)
This is consistent with, and adds file-level evidence for, gap **N5-G1**'s framing (rt/ux split replaced by
`schemaVersion`) — full inventory left to that gap.

**The core API package prefix moved from `javax.baja.*` to `niagara.*`** — directly relevant here because
the task's own boot-facing reference class, `Sys`, is the example: N4 `javax.baja.sys.Sys` →
N5 `niagara.sys.Sys`. `[CERT]` (`find` + `javap -p` on both, this session) A method-by-method `javap -p`
comparison shows the surface is preserved almost 1:1 (`getStation`, `isStation`, `isStationStarted`,
`atSteadyState`, `getRegistry`, `getLicenseManager`, `getHostId`, `getBajaModule`, `getType`/`getTypes`,
`loadType`, `getAuditor`/`setAuditor`, `getSecurityAuditor`, …) with a handful of concrete deltas:
`getLanguage`/`setLanguage` renamed `getLanguageCode`/`setLanguageCode`; the no-arg `getLocalHost()`
overload dropped (only `getLocalHost(InetAddress)` remains); `getHsmManager()` removed outright; `newInstance`
now also declares `NoSuchMethodException`/`InvocationTargetException`. `[CERT]` Full API-delta cataloging
is N5-G5's job; recorded here only because it is the exact class the task named. → **child gap B3-G2**
(full `Sys`/`javax.baja.*`→`niagara.*` rename census belongs to N5-G5, seed it from this finding).

## 3.8 — What replaced `SecurityManager`: a `-javaagent` + ByteBuddy "advice" routed through a home-grown `PermissionManager`

**The removal is structural, not just an unused file.** N5 ships **no `bin/policy/java.policy`** (§3.2) —
N4's equivalent file is 271 lines of classic `grant codeBase {...}` `SecurityManager`/`Policy` permission
grants (`permission java.io.FilePermission`, `RuntimePermission`, `com.tridium.nre.di.NreSupplierPermission`,
etc.), scoped per-jar `codeBase` (`nre.jar`, `niagarad.jar`, …). `[CERT]` (`cat bin/policy/java.policy`, N4)
REMITTANCE `niagara-research` confirms this was N4's real, enforcing sandbox: B635 §1-3 ("N4 installs a
SecurityManager by default"), B17 ("sandbox... via `SecurityManager` + `java.policy`... NOT via JPMS module
boundaries"), B18 (`SecurityManager.checkPermission()` evaluates `<java-permissions>` ∩ policy), B26 (`java
.policy` = "Java 2 SecurityManager grants"), B330/B800/B806 (concrete `checkPermission` call sites and
denials observed live), B541/B572 (the `program`-module sandbox specifically).

**N5's replacement, found in `nre.jar`:**

| Component | Class | Role `[CERT]` |
|---|---|---|
| Java agent entry point | `com.tridium.nre.security.advice.SecurityAgent` | `Premain-Class` in `nre.jar` MANIFEST; `public static void premain(String, Instrumentation)` — installed at JVM start like a classic `-javaagent`, confirmed by the module requiring `java.instrument` and `net.bytebuddy` |
| Bytecode weaving | same class, private methods `isInstalledProvider()`, `isFileSystemProvider()`, 14× `lambda$premain$N` builders | uses `net.bytebuddy.dynamic.DynamicType$Builder` to instrument matched JDK classes at class-load time — this is ByteBuddy's standard "type-matcher + advice" agent pattern |
| Advice classes (the actual interception logic) | `advice.FileAccessAdvice` (+10 nested variants: `ForCopy`, `ForCreateTempFile`, `ForFileRead`/`Write`, `ForFileSystemProviderNewChannel`, `ForMismatch`, `ForMove`, `ForRandomAccessFile`, `ForReadWithFileArgument`/`PathArgument`/`StringArgument`, `ForWriteWithFileArgument`/`PathArgument`), `advice.NetworkConnectionAdvice` (+3: `ForDatagramSocket`, `ForSocket`, `ForSocketChannel`), `advice.ProcessBuilderAdvice`, `advice.SecurityProviderAdvice` | woven into the matched JDK method bodies; `ProcessBuilderAdvice` exposes a single `public static void enter(Object)` — the advice-method shape ByteBuddy calls on entry to the instrumented JDK method |
| Permission model | `permissions.NiagaraPermission`, `NiagaraBasicPermission`, `PermissionFactory`, `PermissionBridge`, `permissions.PermissionManager` | `PermissionManager.checkPermission(NiagaraPermission, Module)` — permission checks are now keyed **by `java.lang.Module`**, not by `CodeSource`/`ProtectionDomain` as under the old `SecurityManager`; a static `modulePermissions : Map<String moduleName, Map<Class<? extends NiagaraPermission>, Set<NiagaraPermission>>>` holds the grant table in memory, built by `initThirdPartyPermissions()`/`addPermissions(String, NiagaraPermission...)` rather than parsed from a `.policy` grant file |
| Restricted cross-module bridge | `permissions.restricted.PermissionUtil` | package `com.tridium.nre.security.permissions.restricted`, the exact package the native launcher `--add-exports`'s to `niagara.niagarad` (§3.5) |
| Bootclasspath shim | `com.tridium.securityBridge.SecurityBridge` + `IPermissionBridge` (2 tiny classes, `bin/ext/securityBridge/securityBridge.jar`, own `module-info.class`) | loaded via `-Xbootclasspath/a:` (§3.5) — `[INFER]` exists so JDK-bootstrap-loaded / unnamed-module code the woven advice touches can call back into the named-module `PermissionManager` without an illegal-access edge; not decompiled this pass (2 classes, ~500 bytes each) |

`[CERT]` every class/method name above is read from `javap -p`/`-verbose` output produced this session
against the extracted `nre.jar`; token-verified by direct disassembly, not inferred from names alone (e.g.
`PermissionManager.checkPermission`'s signature `(NiagaraPermission, Module)` was read off its `javap -p`
listing, not guessed).

**Reading the mechanism as a whole**: N5 does not restore anything resembling `SecurityManager`/`Policy`
(consistent with upstream JDK 25 having fully removed that subsystem — `[INFER]`, general JDK-evolution
knowledge, not sourced from a local file this session). Instead it re-implements *sandboxing* at the
bytecode level: a premain agent instruments the specific JDK entry points that used to trigger
`SecurityManager.checkPermission()` calls (file access — 11 advice variants covering every `java.nio.file`/
`java.io` entry shape; network connect — sockets/datagram/channels; process spawn; security-provider
installation), and each woven call site now calls into `PermissionManager.checkPermission(...)`, which
grants/denies based on the calling `Module`'s entry in an in-memory table instead of a `CodeSource`'s
`.policy` grant. This preserves the *shape* of N4's model (per-codebase/module permission checks on
file/network/process/reflection operations — REMITTANCE B18's "intersection, NO union" semantics) while
moving the enforcement point from a JDK-native hook (now deleted upstream) to an agent-injected one. The
concrete **grant table** N5 ships by default (equivalent to N4's 271-line `java.policy`) was not
decompiled this pass (`initThirdPartyPermissions()`/`addPermissions()` bodies) → **child gap B3-G3**.
Whether N4's 19 textual permission groups (REMITTANCE B635/B18) have a 1:1 `NiagaraPermission` subclass
mapping in N5, or a different taxonomy, is likewise unresolved → **child gap B3-G4**.

## 3.9 — Cryptography provider order: BouncyCastle-FIPS first, by default, on both

`bin/policy/java.security` (N5): `security.provider.1=org.bouncycastle.jcajce.bcfkswrapprovider
.BouncyCastleBCFKSWrapProvider`, `.2=org.bouncycastle.jcajce.provider.BouncyCastleFipsProvider`, then
`SUN`, `SunRsaSign`, `SunEC`, `SunJCE`, `SunJGSS`, `SunSASL`, `XMLDSig`, `SunPCSC`, `JdkLDAP`, `JdkSASL`,
`SunMSCAPI` (13 providers). `[CERT]` `securerandom.source=file:/dev/random`;
`securerandom.strongAlgorithms=Windows-PRNG:SunMSCAPI,DRBG:SUN`. `[CERT]` `bin/ext/bcfips` and
`bin/ext/bcstd` (both BouncyCastle variants, FIPS and standard) ship side-by-side in both N4 and N5's
`ext/` — the FIPS-first provider order plus the `-fips=true/false`/`startWorkbenchInFipsMode` toggle in
`Bootstrap` (§3.6.8) confirms N5 kept N4's FIPS-mode capability rather than dropping it. `[INFER]` (not
diffed line-by-line against N4's `java.security` this pass — out of scope for G7; flagged for whoever
picks up a crypto-focused gap).

## 3.10 — Virtual threads: not found in the boot/web/workbench core this session (scoped negative finding)

Searched the decompressed contents of `nre.jar`, `baja.jar`, `platform.jar`, `web.jar`, `workbench.jar`, and
`niagaraDriver.jar` for the literal method-name/API strings `ofVirtual`, `newVirtualThreadPerTaskExecutor`,
`VirtualThreadPerTask` (these appear as plain UTF-8 constant-pool strings inside any `.class` file that
calls them, so a `strings`/`grep` pass over the decompressed `.class` bytes is a valid presence check).
`[CERT]` — zero matches in all six jars, each of which was actually opened (`unzip -p '*.class' | strings |
grep`) this session. Per the negative-existence rule, this is `[CERT]` **scoped to the six jars opened**,
not a corpus-wide claim — the other ~240 module jars were not checked. `Thread.ofVirtual()`/
`Executors.newVirtualThreadPerTaskExecutor()` are available in the bundled JRE 25 (`java.base`, always
present), so absence here is a Tridium-code choice, not a platform limitation; REMITTANCE B800/B806 record
N4's `SecurityManager` denying `RuntimePermission "modifyThread"` for JDK-executor-style threading inside
station components, and a house doctrine of using `Clock`, not `java.util.concurrent`, for scheduling — if
that doctrine survives into N5, it would explain non-adoption of virtual threads in the core regardless of
JDK support. Not confirmed this session (`PermissionManager`'s live grant table was not decompiled, §3.8) →
folds into **child gap B3-G3**.

## 3.11 — Config/user-home layout: same three shortcuts, same `ProgramData` root, `daemon` split by major version only

The 3 `.lnk` shortcuts in the N5 install root resolve to (`strings -e l`, this session, `[CERT]`):

| Shortcut | Target |
|---|---|
| `Configuration Home.lnk` | `..\..\..\ProgramData\Niagara\tridium\config\5.0.0.28` (exactly the path given in the task) |
| `Daemon User Home.lnk` | `..\..\..\ProgramData\Niagara\tridium\daemon\5.0` (note: **`5.0`**, not `5.0.0.28` — daemon home is keyed by major.minor, not the full build) |
| `Workbench User Home.lnk` | `..\..\..\Users\equipo\Niagara\tridium\5.0` (same major.minor-only keying) |

`ProgramData\Niagara\tridium\config\5.0.0.28\` top-level dirs: `cleanDist`, `etc`, `eula`, `jar-cache`,
`modules` (247 `.jar`), `registry` (`registry.chk`/`registry.db`), `security` (`certificates`, `licenses`
— not opened), `sw`. `[CERT]` `jar-cache/` holds lazily-fetched third-party integration bundles —
`cloudLink`, `oauth2`, `saml`, `totpAuth`, `abstractMqttDriver`, `opcUaCore`, `rdb`/`rdbHsqlDb`/
`rdbSqlServer`, `svgBatik`, `snmpLibs`, `xprotect`, `devkit`, `test`, `email`, `gx`, `jodaTime`,
`jsonSmart`/`jsonToolkit`, `apachePoi`, `axvelocity`, `commonsCompress`/`commonsIo` — directly relevant to
N5-G9/N5-G10 (out of scope here, noted for those gaps). `ProgramData\Niagara\tridium\daemon\5.0\` holds
`daemon`, `logging`, `security`, `stations`. `Users\equipo\Niagara\tridium\5.0\` holds `etc`, `logging`,
`security`, `shared`. `[CERT]` No secret values were opened or printed from any `security`/`certificates`/
`licenses` directory — only top-level directory listings, per the read-only mandate.

## 3.x — Child gaps opened

- **B3-G1** — Decompile `com.tridium.nre.module.{NModuleModuleReader,NiagaraModuleReference,
  SafeCloseModuleReader,ModuleDescriptorAugmenter}` and `com.tridium.sys.registry.NRegistry` to trace how
  the ~245 non-`baja` Niagara modules (each carrying its own `module-info.class`, §3.7) get resolved into
  `ModuleLayer`(s) at station/workbench runtime, beyond the single hand-built `niagara.baja` child layer
  `Bootstrap.Main` constructs. Does N5 build one `ModuleLayer` per module, one shared layer for all
  modules, or fall back to a non-JPMS dynamic classloader for the module catalog proper?
- **B3-G2** — Full `javax.baja.*` → `niagara.*` package rename census (seeds N5-G5): `Sys` is a 1:1
  method-level match with a handful of signature deltas (§3.7); is this true fleet-wide, or are there
  packages that split, merged, or dropped entirely?
- **B3-G3** — Decompile `PermissionManager.initThirdPartyPermissions()`/`addPermissions()` to recover N5's
  actual default grant table (the `NiagaraPermission` equivalent of N4's 271-line `java.policy`), and check
  whether it denies `RuntimePermission "modifyThread"`/JDK-executor use the way N4's `SecurityManager` did
  (REMITTANCE B800/B806) — this also resolves whether virtual-thread avoidance (§3.10) is policy-enforced
  or merely not-yet-adopted.
- **B3-G4** — Map N4's 19 textual `<java-permissions>` groups (REMITTANCE B635 §635) onto N5's
  `NiagaraPermission` subclass taxonomy (`FilePermission`, `KeyRingPermission`,
  `ModifyProtectedPropertiesPermission`, `NiagaraBasicPermission`, `KeyStorePermission`,
  `RuntimeExecPermission`, `SigningPasswordPermission`, … — only partially enumerated this session from
  directory listing, not fully decompiled).
- **B3-G5** — Decompile the 2-class `securityBridge.jar` (`SecurityBridge`, `IPermissionBridge`) to confirm
  the bootclasspath-shim hypothesis in §3.8's table (`[INFER]` there, not yet `[CERT]`).

## 3.x — Connections

- **REMITTANCE → `niagara-research` B635, B17, B18, B26, B1-3, B29, B541, B330, B572, B800, B806** — N4's
  `SecurityManager` + `java.policy` + 19-permission-group sandbox; every claim in §3.8 about what N5
  replaces is anchored against these.
- **REMITTANCE → `niagara-research` B31, B17, B1021, B533** — N4's `nre.properties`/native-launcher/
  thread-pool baseline; anchors §3.3 and §3.5.
- **REMITTANCE → `niagara-research` B1236 (BTI)** — N4 launcher-to-entry-class table
  (`nre.exe`/`station.exe`/`wb.exe`/`test.exe`/`plat.exe`/`niagarad.exe` ↔ `nre.properties` profiles);
  §3.6 point 9 confirms `com.tridium.sys.station.Station` is unchanged in N5.
- **[N5-G1]** (module packaging / `schemaVersion`) — §3.7 supplies the `module.xml` root-tag evidence
  (`schemaVersion="5"`, `runtimeProfile` dropped) that gap should consume and expand.
- **[N5-G5]** (core API delta) — §3.7's `Sys` method comparison and child gap B3-G2.
- **[N5-G9]/[N5-G10]** (security/authn surface, cloud surface) — §3.11's `jar-cache/` inventory
  (`totpAuth`, `oauth2`, `saml`, `cloudLink`, `xprotect`) is a ready-made seed list for those gaps.
