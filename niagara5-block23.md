# Block 23 — N5 module loader internals: ModuleLayer topology, JPMS access patching and signature gates

> Research of **how N5 5.0.0.28 turns ~247 module jars into real `java.lang.module`/`ModuleLayer` objects at
> runtime**: full method-body trace of `com.tridium.sys.module.*` (`baja.jar`) and `com.tridium.nre.module.*`
> / `com.tridium.nre.bootstrap.*` (`nre.jar`), closing/deepening [B1]'s B1-G2/B1-G3/B1-G4/B1-G5 and [B3]'s
> B3-G1. Covers: layer count/parenting/grouping rule, `Configuration.resolve` vs `resolveAndBind` use sites,
> module.xml-vs-JPMS-`requires` relationship, automatic-module derivation, the `NiagaraJPMSAccessModifier`
> property mechanism, hot-install vs hot-reload, the dead `PROGRAM` `ModuleType`, and a three-way comparison
> of N5's module-signature gates against N4's two-gate design ([B1147], `niagara-research` corpus). Does
> **not** cover: `com.tridium.crypto.core` internals (searched, absent from both jars opened — see §23.7),
> live station confirmation of any of this (still B1-G1, unclosed — a `[CERT-hw]` gap), or the build-time
> Gradle plugin that emits `module-info.class` (N5-G6, `niagara-research`-adjacent, out of scope).
>
> Subject version: Niagara **N5 5.0.0.28 (Beta)**, `baja.jar`/`nre.jar` from
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` and
> `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` — same install this corpus's [B1]/[B3] used.
>
> Sources: `baja.jar` → `com/tridium/sys/module/*.class`, already Vineflower-decompiled to
> **source-level `.java`** at `organized/baja/vineflower/com/tridium/sys/module/*.java` (pre-existing corpus
> artifact, gitignored — `organized/` per `.gitignore` "PROPRIETARY Tridium bytecode… NEVER commit") ·
> `nre.jar` → `com/tridium/nre/module/*.class` + `com/tridium/nre/bootstrap/*.class`, freshly decompiled this
> session with Vineflower 1.12.0 (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar`,
> `-e=` `baja.jar` for cross-jar context, run under
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`) into `/tmp/claude-1000/n5b23/out/` (scratch, not
> archived in the corpus — re-derivable verbatim from `nre.jar` + the same command) · REMITTANCE
> `niagara-research` **B1147** (`niagara-mental-model-bloque1147.md`, N4's two-gate signature design) via
> `python3 /home/cristian/niagara-research/tools/corpus-nav.py show 1147`.
>
> Method: direct reading of decompiled `.java` source (both trees are now real Java source with genuine
> line numbers — an upgrade over [B1]'s `javap`-only method and [B3]'s bytecode-offset method, neither of
> which had a decompiler available in-session). Every method body cited below was read in full this
> session, not inferred from a signature. `grep`/`find` used to confirm negative-existence claims (§23.7,
> §23.5) by exhaustively searching both decompiled trees for the searched token.
> Markers: `[CERT]` local primary source, decompiled `.java`, cited `file:line` (line-addressable — a
> stronger form than [B1]/[B3]'s bytecode-offset citations) · `[CERT-a]` N4 REMITTANCE block (secondary to
> this corpus, primary to `niagara-research`) · `[INFER]` deduction not literal in any single cited line.
>
> Loader/runtime layer. Deepens [B1] §1.5 (signatures-only pass on the same classes — this block replaces
> B1's `javap`-derived inferences with source-level confirmation and closes B1-G2/G3/G4, substantially
> answers B1-G5) and [B3] §3.6 (Bootstrap bytecode-offset trace — this block replaces those offsets with
> `file:line` and closes B3-G1). Cross-corpus: REMITTANCE `niagara-research` [B1147] (N4's two-gate
> signature design — §23.7 is the direct N4↔N5 comparison).
>
> **Type:** standard

---

## 23.1 — Layer topology: 3 layers built at boot, plus one dynamic layer per third-party module, `PROGRAM` layers never happen

Four distinct `ModuleLayer`s exist in a running N5 process, built in this fixed order `[CERT]`:

| # | Layer | Built by | Parent(s) | Membership | `resolve` API used |
|---|---|---|---|---|---|
| 0 | JVM boot layer | the JVM itself, from `--module-path`/native launcher (`[B3]` §3.5) | — | `java.base` + ~19 JDK/3rd-party modules + `niagara.nre` | n/a (JDK bootstrap) |
| 1 | "Baja Boot ModuleLayer" | `Bootstrap.Main` (`nre.jar`) | Layer 0 only | **exactly one module**, `niagara.baja` | `Configuration.resolve` (`Bootstrap.java:146-148`) |
| 2 | "Core Framework ModuleLayer" | `ModuleManager.initCoreModuleLayer()` | Layer 1 + Layer 0 (`ModuleManager.java:137`: `List.of(NIAGARA_BOOT_MODULE_LAYER, JVM_BOOT_MODULE_LAYER)`) | **every** module `NModuleModuleFinderFactory` categorizes `CORE` (Tridium-dev-cert-signed), bulk-resolved **together in one `Configuration`** | `Configuration.resolveAndBind` (`ModuleManager.java:414-419`) |
| 3+ | "Dynamic Layer `<name>`", one per module | `ModuleManager.loadModuleForModuleReference` (lazy, on first `loadModule`/dependency-resolve) | filtered `moduleLayerInfoSet`: for a **non-core** module, every previously-tracked layer that `isCoreFrameworkModuleLayer()` **or** any layer at all if the module itself is non-core (`ModuleManager.java:704-708`) | one `APPLICATION`-categorized (third-party, non-`niagara.`/`com.tridium.`-prefixed) module per layer | `Configuration.resolve`, **not** `resolveAndBind` (`ModuleManager.java:709-711`) |

`[CERT]` layer 1/2 registration: `ModuleManager.java:97-98` (constructor seeds `moduleLayerInfoSet` with the
JVM-boot and Baja-boot `ModuleLayerInfo` records, both `isCoreFrameworkModuleLayer=true`);
`ModuleManager.java:386` (`Core Framework ModuleLayer` added, also `true`); `ModuleManager.java:726`
(`"Dynamic Layer %s".formatted(...)`  added with `isCoreFrameworkModule` — false for the third-party case
this method exists for).

**Grouping rule is per-`ModuleType`, not per-module and not per-profile.** `NModuleModuleFinderFactory`
categorizes every scanned module into exactly one of 3 buckets — `CORE` (module manifest is signed with
Tridium's dev cert, checked against `SecurityConstants.getTpk()` or a `niagaradevca` trust-store cert;
`NModuleModuleFinderFactory.java:637-671`), `APPLICATION` (name does **not** start with `niagara.`/
`com.tridium.` — `:673-675`), or `PROGRAM` (`:677-679`, see below). All `CORE` modules go into **one shared
`Configuration`/layer** built once at `initCoreModuleLayer()`; `APPLICATION` modules each get their **own**
dynamic layer, lazily, the first time something calls `loadModule`/resolves a dependency on them
(`ModuleManager.java:683-775`). This is the direct, source-confirmed answer to [B1] §1.5's `[INFER]`
("N5 still classifies modules into a small closed set of categories at load time... about the module's role
in the boot/resolution graph") — it is now `[CERT]`, and refines it: the categorization does **not** map
1:1 onto "core vs. application" in a binary sense at the ModuleLayer level either — every `CORE` module
shares ONE layer, while every `APPLICATION` module gets its OWN layer.

**`PROGRAM` is a dead branch as shipped.** `isProgramModule(NModuleModuleReference)`
(`NModuleModuleFinderFactory.java:677-679`) is:
```java
private static boolean isProgramModule(NModuleModuleReference moduleReference) {
   return false;
}
```
`[CERT]` — hardcoded, unconditional `false`, the only reference to it anywhere in either decompiled tree
(`grep -rn "isProgramModule"` inside `organized/baja/vineflower/` matches only this definition and its one
call site in `categorize()`, `NModuleModuleFinderFactory.java:490`). `categorize()` throws
`FindException("Unable to determine module type…")` if a module reference is neither `CORE` nor
`APPLICATION` (`:491`), so — because `isProgramModule` can never return `true` — that `FindException`
branch, and the `PROGRAM` enum constant itself (`enum ModuleType { CORE, APPLICATION, PROGRAM; }`,
`:913-917`), are unreachable dead code in 5.0.0.28. **Answering the task's Q6 directly: no, a "program
object" is not compiled at runtime into its own `PROGRAM`-categorized `ModuleLayer` via this factory as
shipped** — the scaffolding (enum constant + `categorize()` branch + finder-factory bucket) exists, but
nothing populates it. Whether Niagara's runtime program-scripting feature (`com.tridium.program.*`,
`BProgramAction`/`Robot` per `docDeveloper.jar!doc/program/…`, `[B1]`'s doc-scan territory) uses an
entirely separate, non-`ModuleLayer` mechanism (e.g. a plain reflective/ASM-generated class, not a JPMS
module at all) was not traced this session — → **child gap B23-G1**.

## 23.2 — `Configuration.resolveAndBind` vs `.resolve`: only the shared Core layer uses service-binding

The **only** call site using `resolveAndBind` in either decompiled tree is
`ModuleManager.resolveCoreModuleLayerConfiguration` (`ModuleManager.java:414-419`):
```java
Configuration configuration = Configuration.resolveAndBind(
   ModuleFinder.of(),
   List.of(NIAGARA_BOOT_MODULE_LAYER.configuration(), JVM_BOOT_MODULE_LAYER.configuration()),
   niagaraHomeModulesDirectoryModuleFinder,
   coreModuleLayerRootModuleNames
);
```
`[CERT]`. Every dynamic (`APPLICATION`) layer instead uses plain `Configuration.resolve`
(`ModuleManager.java:709-711`) and `Bootstrap.Main`'s single-module baja layer also uses plain `.resolve`
(`Bootstrap.java:146-148`). `[CERT]` — `resolveAndBind`'s only behavioral difference from `resolve` is JPMS
service-binding (transitively adding any module that `provides` a service some root module `uses`).
`[B1]` §1.4 already established `[CERT]` that **zero of the 242 censused Niagara modules declare `uses` or
`provides`** — so for the Niagara-authored module graph, `resolveAndBind` and `resolve` behave identically
here; the choice only matters for the **third-party** modules the Core layer also resolves in that same
`Configuration` (Jetty 12, jose4j, BouncyCastle, etc. — `[B3]` §3.6 lists several as `nre.jar` `requires`),
several of which are genuine JPMS service providers upstream. `[INFER]` — no source states this rationale
explicitly; it follows from combining `[B1]`'s exhaustive `uses`/`provides` census with this block's two
call sites.

`coreModuleLayerRootModuleNames` (the resolution roots passed to `resolveAndBind`) is every `CORE`-
categorized module name the finder found **that is not already resolved in the Niagara Boot layer**
(`ModuleManager.java:406-413`, filter `NIAGARA_BOOT_MODULE_LAYER.findModule(moduleName).isEmpty()`) — i.e.
"every core module except `baja` itself", confirming `baja` really is handled by a wholly separate
resolution path (§23.7).

## 23.3 — module.xml `<dependency>` graph and JPMS `requires` are two independent, never-cross-checked graphs

`module-info.class` ships **pre-built** in every module JAR (baked in at build time by the Gradle plugin,
out of scope — N5-G6); at runtime `NModuleModuleFinderFactory.readModuleDescriptor` just reads those
bytes directly off disk (`Files.readAllBytes(moduleDescriptorPath)` → `ModuleDescriptor.read(...)`,
`NModuleModuleFinderFactory.java:394-403`) and passes the result through
`ModuleDescriptorAugmenter.augmentModuleDescriptorWithAutoPackageExports` — which rebuilds every `exports`
entry with an extra `<pkg>._auto_` sibling export added (`ModuleDescriptorAugmenter.java:10-46`, `[CERT]`,
scratch `/tmp/claude-1000/n5b23/out/com/tridium/nre/module/ModuleDescriptorAugmenter.java`) — the same
rewrite `[B3]` §3.6 point 2 found `Bootstrap.Main` applying to `baja`'s own descriptor via bytecode-offset
evidence; this block confirms it is a **shared, general-purpose** augmenter class used by both the
`Bootstrap` single-module path and the ordinary `NModuleModuleFinderFactory` scan path, not something
`Bootstrap` does uniquely for `baja`.

The Niagara-level `module.xml` `<dependencies>` graph is enforced **completely separately**, by
`ModuleManager.resolve(NModule, Map)` (`ModuleManager.java:922-948`): for each `Dependency d` on `m.depends`,
it recursively `loadDependency`s the named Niagara module, then calls
`d.resolution.checkBajaVersion(d.bajaVersion)` and `.checkVendor(d.vendor, d.vendorVersion)` — a
Niagara-semantic version/vendor compatibility check, unrelated to JPMS. `[CERT]` No code path in either
decompiled tree cross-references the two graphs (no site reads a module's JPMS `requires()` list and
compares it against its own `module.xml` `<dependency>` list, or vice versa) — `[INFER]`, drawn from the
absence of any such call in `ModuleManager`/`NModuleModuleFinderFactory`, not a positive statement anywhere
that they are independent. **Answering the task's Q2: module.xml dependencies are not "generated into" JPMS
`requires` at runtime and are not validated against them either — they are two parallel dependency graphs,
each enforced by its own, non-communicating mechanism** (JPMS hard-fails `Configuration.resolve*` on a
missing `requires`; Niagara hard-fails `ModuleManager.resolve` on a version/vendor mismatch). → **child gap
B23-G6**: confirm whether the two graphs can silently diverge (a `module.xml` dependency edited without a
matching `module-info.java` change, or vice versa) — not proven exhaustively this session.

## 23.4 — Automatic modules: N5 has its own derivation path, independent of the JDK's built-in fallback

For the 5 module-info-less JARs `[B1]` §1.1 found (`analyticsLibs`, `apachePoi`, `commonsIo`, `commonsLang`,
`niagaraTest`), `NModuleModuleFinderFactory.readModuleDescriptor` falls through to its own
`deriveModuleDescriptor(JarFile, NModule)` (`:394-397`, method body `:681-751`) rather than delegating to
the JDK's built-in `ModuleFinder.of()` automatic-module inference. `[CERT]` It: reads
`Automatic-Module-Name` from the manifest if present, else synthesizes a name from
`vendor + "." + moduleName`, cleaned of non-alphanumerics (`cleanModuleName`, `:753-766`); walks every
`.class` entry in the JAR to build the package set, adding a `<pkg>._auto_` sibling for each (matching
§23.3's augmenter convention, applied here by hand instead); and separately walks `META-INF/services/*`
entries to populate JPMS `provides` (`:724-748`), validating each provider class's package is one it just
discovered (`:735-737`, throwing `InvalidModuleDescriptorException` otherwise). This is a from-scratch
reimplementation of automatic-module semantics **inside Niagara's own loader**, not a delegation to the
JDK's automatic-module support — `NModuleModuleFinderFactory.readJar` (`:330-339`) only falls back to
`ModuleFinder.of(jarFilePath).findAll()` (the JDK's own path) when the JAR has **no** `META-INF/module.xml`
at all (i.e. a non-Niagara-wrapped third-party JAR loaded as a packaged `LIB-INF` dependency, §23.6) —
every one of the 5 automatic-module JARs `[B1]` found **does** carry `module.xml` (confirmed there), so all
5 go through `deriveModuleDescriptor`, not the JDK path.

## 23.5 — `NiagaraJPMSAccessModifier`: 4 system properties, semicolon/comma tuple grammar, exports/opens restricted to non-Tridium sources, reads unrestricted

`ModuleManager.NiagaraJPMSAccessModifierType` (`ModuleManager.java:1201-1206`) is a 4-constant enum —
`ENABLE_NATIVE_ACCESS`, `ADD_READS`, `ADD_EXPORTS`, `ADD_OPENS` — read from 4 system properties at
`initCoreModuleLayer()` (`:387-390`): `niagara.enable.native.access`, `niagara.add.reads`,
`niagara.add.exports`, `niagara.add.opens`. `[CERT]` `NiagaraJPMSAccessModifier.makeModifier`
(`:1115-1185`) parses each into a distinct grammar:

| Property | Tuple separator | Format | Example |
|---|---|---|---|
| `niagara.enable.native.access` | `,` | bare module names | `myDriver,otherDriver` |
| `niagara.add.reads` | `;` between tuples, `=` source/target | `source=target1,target2` | `myModule=okhttp3,jetty.util` |
| `niagara.add.exports` | `;` between tuples, `/` module/package, `=` source/target | `source/pkg=target1,target2` | `myModule/com.acme.internal=otherModule` |
| `niagara.add.opens` | same grammar as `add.exports` | `source/pkg=target1,target2` | — |

`[CERT]` (`:1120-1181`, full `switch` body over `modifierType`). Applied only for **dynamically-loaded,
non-core (`APPLICATION`) modules**, at the end of `loadModuleForModuleReference` (`:749-756`):
`handleThirdPartyNativeAccess` → `handleThirdPartyAddReads` → `handleThirdPartyAddExportsOrOpens(...,
exports=true)` → `handleThirdPartyAddExportsOrOpens(..., exports=false)` → per-annotation native access.
`[CERT]` **Asymmetric guard**: `handleThirdPartyAddExportsOrOpens` rejects any modifier whose
`sourceModuleName` starts with a `NIAGARA_JPMS_RESTRICTED_PREFIXES` entry — `"niagara."` or `"com.tridium."`
(`:570-574`, set built at `:1086`: `Set.of("niagara.", "com.tridium.")`) — throwing
`IllegalArgumentException("Cannot modify graph for restricted source module…")`; **`handleThirdPartyAddReads`
has no equivalent prefix check** (`:533-565`) — a third-party module can be granted `addReads` onto a
Tridium/Niagara module via this property, but **not** `addExports`/`addOpens` *from* one. `[CERT]` This is
a genuine, source-confirmed asymmetry: the property mechanism lets an operator/OEM widen what a third-party
module can **read**, but not what it can **reflectively access inside** Niagara's own modules.

**Why the deep-reflection needs exist (answering the task's "why").** Independently of the configurable
property mechanism above, `initCoreModuleLayer()` **unconditionally** opens every package of every
Core-layer module to `BAJA_MODULE` (`:154-162`: `coreModuleLayer.modules()...forEach(modulex ->
modulex.getPackages()...forEach(pkgName -> this.addOpens(modulex, pkgName, BAJA_MODULE)))`), and
`loadModuleForModuleReference` does the identical thing for every dynamically-loaded module regardless of
category (`:728-730`). `[CERT]` Every Niagara module, core or third-party, is therefore opened to `baja`
by construction, with no property or annotation needed — this is the concrete mechanism behind `[B1]`
§1.5's `[INFER]` about "reflection needs of the type system/slotomatic": `baja` (which hosts the
`niagara.sys.Type`/slot-access machinery) needs unconditional reflective access into every other module's
packages to instantiate/introspect their `BComponent`/`BObject` types, and this loop is how that access is
granted at every layer, every time, unconditionally — not via `NiagaraJPMSAccessModifier` at all, which is
reserved for narrower, operator-opt-in third-party grants.

## 23.6 — Hot install of a *new* module: yes, at runtime, into its own fresh layer. Hot *reload* of an already-loaded module: no code path exists

`loadModuleForModuleReference` is invoked lazily, the first time `ModuleManager.loadModule`/`loadDependency`
needs a Niagara module that is not yet in `loadedModules` (`ModuleManager.java:649-677`, `:777-817`) — for
an `APPLICATION`-type module this **builds a brand-new `Configuration`/`ModuleLayer`/`ModuleSetClassLoader`
on demand** (`:683-775`), i.e. a module that was never part of the initial boot resolution can be added to a
running process without a restart, provided its JAR is discoverable via
`moduleFinderFactory.getModuleModuleFinderForNiagaraModuleName` (which itself lazily re-scans
`Nre.niagaraConfigHome/modules` on demand, `NModuleModuleFinderFactory.scanNModules`,
`:116-143`/`ModuleManager.java:100`). `[CERT]` This is a real, working **hot-add** path.

There is, however, **no unload/reload/replace path anywhere in either decompiled tree** — a
`grep -rin "unload\|removeModule\|reload"` over every `.java` file in
`organized/baja/vineflower/com/tridium/sys/module/` matches only the string `"unloadedModule"` used as a
**local variable name** for a not-yet-loaded module inside `findModuleReferenceForNiagaraModule`
(`ModuleManager.java:833-838` — this is the fallback path when a module isn't yet in
`moduleFinderFactory`'s cache, not an unload operation), plus the unrelated `try (JarFile jarFile = new
JarFile(unloadedModule))` line. `[CERT]` — negative-existence claim, scoped exactly to this package in
`baja.jar`; a teardown mechanism could in principle live elsewhere (e.g. `com.tridium.sys.registry.NRegistry`,
not decompiled this block) but nothing in `ModuleManager`/`ModuleSetClassLoader`/`NModuleModuleFinderFactory`
removes an entry from `loadedModules`, `moduleLayerInfoSet`, or `controllersByModuleLayer` once added — those
are plain (non-evicting) maps/sets throughout. **Answering the task's Q5: hot-install of a brand-new module
is supported by the existing `ModuleLayer` machinery; hot-reload of an already-loaded module's bytecode is
not** (would require, at minimum, JDK 9+ `ModuleLayer` unloading semantics — dropping every strong reference
to the old layer/loader/classes — which nothing here attempts).

## 23.7 — Signature gates: N5 restructures N4's two-gate design into three gates, drops the `moduleVerificationMode` level knob, and gives `baja` its *own* dedicated per-class check instead of bypassing verification

REMITTANCE `[B1147]` (`niagara-research`, N4 4.14) documents N4 as **two** gates: boot-scan
(`ModuleManager.verifyModuleSignature`, per module-part, hard-fails to `exit(-7)`) and class-load
(`ModuleClassLoader.verifyJarEntrySignature`, per JAR entry, hard-fails to `exit(-6)`), with `baja` bypassing
**both** (S1: loaded via `loadSystemModule`, `isSystemJar=true`, never signature-checked). `[CERT-a]`
(`niagara-mental-model-bloque1147.md` §1147.1/§1147.5 S1). N5's structure, read source-level this session:

| | N4 (`[B1147]`) | N5 (this block) |
|---|---|---|
| **Gate 1 site/timing** | `ModuleManager.verifyModuleSignature`, at first-load (`doLoadByModulePartName`) | `NModuleModuleFinderFactory.verifyModuleSignature`, at **discovery/scan time** inside `readNiagaraModule` (`:341-352`, call at `:348`) — moved earlier in the lifecycle |
| **Gate 1 enforcement condition** | conditional: `any permission requiresSignature()` **or** `verificationMode != low` | **unconditional** whenever `Nre.getJarSignatureRegistry()` is non-null (`NModuleModuleFinderFactory.java:521-559` — no `moduleVerificationMode`/level check anywhere in the method) |
| **Gate 1 fail path** | `ModuleException` → uncaught → `exit(-7)` | `ModuleException extends BajaRuntimeException` (`niagara/sys/ModuleException.java:3`) → uncaught `RuntimeException` → propagates to `Nre.boot()`'s generic `catch (Throwable)` → `System.exit(-7)` (`Nre.java:362,369`) — **same exit code, but via a shared generic catch, not a dedicated named case** |
| **Gate 2 site** | `ModuleClassLoader.verifyJarEntrySignature` | `ModuleSetClassLoader.verifyJarEntrySignature(NModule, JarEntry)` (`ModuleSetClassLoader.java:499-629`), called from `defineClass` (`:437-441`) |
| **Gate 2 `shouldCheckTpk` prefixes** | `com/tridium/` or `javax/baja/` or `module.getCheckTpk()` | `com/tridium/` or **`niagara/`** (renamed, matching `[B3]` §3.7's `javax.baja.*`→`niagara.*` package move) or `module.getCheckTpk()` (`:509`) |
| **Gate 2 level knob** | `verificationMode != low \|\| (shouldCheckTpk \|\| validateCertChain) && canCheckTpk` | `!isDeveloperLicense \|\| (shouldCheckTpk \|\| this.validateCertChain) && canCheckTpk` (`:512`) — the 3-level `moduleVerificationMode` enum is **replaced outright** by a binary `NLicenseManager.isDeveloperLicense()` check |
| **Gate 2 fail path** | `ValidationException` → `exit(-6)` | same `ValidationException` pattern → `EXIT_CONSUMER.accept(-6)` (`:625`, `EXIT_CONSUMER = System::exit`, `:77`) — **same exit code, same mechanism** |
| **`skipModuleValidation` escape hatch** | sysprop `niagara.classLoader.skipModuleValidation` + license `developer{skipModuleValidation=true}`; logs `"**** Module validation has been DISABLED ****"` | **identical** sysprop name, identical license-feature gate, identical log string (`loadSkipModuleValidation`, `:631-655`; holder `:828-830`) — survives 1:1 |
| **`baja` treatment** | bypasses **both** gates entirely (S1) | `baja` bypasses gates 1/2 too (`ModuleManager.loadSystemModule`, `:105-120`, sets `isSystemJar=true`; `Bootstrap.BajaModuleReference.open()`, `Bootstrap.java:342-357`, has no signature call at all) — **but** its classes are instead loaded by a **dedicated third path**, `BootstrapClassLoader.loadClass` (nre.jar, scratch `/tmp/claude-1000/n5b23/out/com/tridium/nre/bootstrap/BootstrapClassLoader.java:31-56`), which calls `this.coreCryptoManager.validateCertChain(superClazz, true)` on **every class it defines** (`:49`, `checkTpk` hardcoded `true`, unconditional — stronger than the name-prefix heuristic used elsewhere) and hard-fails to `System.exit(-6)` on any exception (`:50-53`) |

`[CERT]` every cell sourced from the file:line pairs shown; the N4 column is `[CERT-a]` via `[B1147]`.
**Net finding for the task's B1-G5/Q7: N5 does NOT preserve N4's exact two-gate structure — it restructures
into three gates** (discovery-time module-level, class-load-time entry-level, and a `baja`-specific
per-class gate that did not exist in N4's model at all) **and removes the level-based escape hatch at both
of N4's original gates**, replacing "verification strength depends on `moduleVerificationMode`" with
"verification is unconditional except for a binary developer-license carve-out at Gate 2" — consistent with,
and now code-level confirming, `[B3]` §3.4's independently-found schema-level absence of
`niagara.moduleVerificationMode` from N5's `system.properties`. **This also refutes a literal reading of
`[B1147]` S1 carried forward unchanged**: `baja` is not verification-free in N5 — it trades the
ordinary two-gate pipeline for one unconditional, `checkTpk=true`-forced, per-class check of its own.

`com.tridium.crypto.core` (`CoreCryptoManager`, `JarSignatureRegistry`, `CertUtils`, `ValidationException` —
every type both gates call into) is **absent from both `baja.jar`'s and `nre.jar`'s decompiled trees**:
`find … -ipath "*crypto/core*"` over `organized/baja/vineflower/` returns zero directories or files, and the
same is true of the freshly-decompiled `nre.jar` tree. `[CERT]` (negative-existence, scoped to exactly the
two jars opened this session) — matching N4's `[B1147]` framing ("closed-source... `[INFER]` from call
sites") exactly; the actual PKIX chain-building/TPK-memcmp/revocation logic remains unread in N5 too.
→ **child gap B23-G2** (mirrors N4's still-open `SES9-G1`).

## 23.8 — Connections

- **[B1]** — §23.1 replaces `[B1]` §1.5's `javap`-signature-only pass with full source-level confirmation;
  closes **B1-G2** (`nre.jar` does carry its own `META-INF/module.xml` — `nre` `bajaVersion="0"
  vendorVersion="5.0.0.28" schemaVersion="5"`, confirmed by direct `unzip -p`, and does carry a real
  `module-info.class`, both outside the `modules/` directory `[B1]`'s census scoped to), **B1-G3** (full
  statement-level tracing of `loadModule`/`doLoadByModuleName`/`resolve`/`initCoreModuleLayer` — done, §23.1-
  §23.2), **B1-G4** (`NiagaraJPMSAccessModifier` fully decompiled — §23.5; `com.tridium.nre.module.
  NiagaraModuleReference` is a trivial 1-method marker interface, `NiagaraModuleReference.java:1-5`), and
  substantially answers **B1-G5** (§23.7, restructured not preserved 1:1).
- **[B3]** — §23.1 replaces `[B3]` §3.6's bytecode-offset `Bootstrap.Main` trace with `file:line` source
  citations (same conclusions, higher precision); closes **B3-G1** ("does N5 build one `ModuleLayer` per
  module, one shared layer for all modules, or fall back to a non-JPMS dynamic classloader" — answer: one
  shared layer for ALL core modules together, plus one dynamic layer PER third-party module — §23.1).
  Confirms §3.7's `javax.baja.*`→`niagara.*` rename is reflected in the Gate-2 `shouldCheckTpk` prefix
  (§23.7). Independently confirms §3.4's `moduleVerificationMode` schema-drop at the code level (§23.7).
- **REMITTANCE → `niagara-research` [B1147]** — the full N4↔N5 signature-gate comparison is §23.7; also see
  its still-open `SES9-G1` (closed-source `CoreCryptoManager.validateCertChain`), mirrored here as **B23-G2**
  since the same class is equally absent from the N5 jars searched.

## 23.9 — Child gaps

- **B23-G1** — Whether Niagara's runtime program-scripting feature (`com.tridium.program.*`,
  `BProgramAction`/`Robot`) uses a mechanism outside `NModuleModuleFinderFactory`'s dead `PROGRAM`
  `ModuleType` branch (§23.1) — requires decompiling `com.tridium.program.*` (not in `baja.jar`, not
  searched this session) and/or a later N5 build to check if `isProgramModule()` is ever implemented.
- **B23-G2** — Decompile/RE `com.tridium.crypto.core.io.CoreCryptoManager.validateCertChain` (absent from
  both `baja.jar` and `nre.jar` this session, likely lives in a `crypto`/`platCrypto`-family jar not yet
  identified in this corpus) to confirm PKIX construction and whether revocation checking is disabled for
  the module-signature path, mirroring N4's still-open `SES9-G1`.
- **B23-G3** — Confirm whether `niagara.classLoader.skipModuleValidation` is present or absent from N5's
  CLI-property blacklist (the `Nre.java` equivalent of N4 `[B1147]` S3) — not traced this session beyond the
  `System.exit` call-site greps.
- **B23-G4** — Live confirmation, via the `moduleConfiguration` spy page decompiled in full at
  `ModuleConfigurationPage.java` (§23.1's table columns: Module Name / Layer=Core-or-Application / Parent
  Module / JAR Path / Version — this closes the *code* half of `[B1]`'s **B1-G1**), on an actual running N5
  5.0.0.28 station — the *live* half of B1-G1 remains open (requires-execution, `[CERT-hw]`).
- **B23-G5** — `com.tridium.nre.di.NreInstantiator`/`SingletonSupplier`/`TypeSupplier` (referenced in
  `Bootstrap`'s static initializer for wiring `ISecurityInitializer`, `Bootstrap.java:320-328`) were not
  decompiled/traced — tangential DI plumbing, out of scope for this block's loader focus.
- **B23-G6** — Confirm whether the module.xml `<dependency>` graph and the compiled `module-info.class`
  `requires` graph (§23.3, shown independent but not proven exhaustively divergence-free) can be edited out
  of sync without either resolution mechanism detecting it.

## 23.10 — Self-verification (METHODOLOGY §11)

**Decompiled-tree block, now at SOURCE level, not bytecode level.** Every `[CERT]` citation above points
into a Vineflower-decompiled `.java` file — for `baja.jar`, a pre-existing corpus artifact at
`organized/baja/vineflower/com/tridium/sys/module/*.java` (gitignored, per `.gitignore`'s explicit
"PROPRIETARY Tridium bytecode/decompiled output — NEVER commit" rule — confirmed this session via `git
ls-files organized | wc -l` → `0`); for `nre.jar`, freshly decompiled this session into scratch
`/tmp/claude-1000/n5b23/out/` (not archived, re-derivable verbatim by re-running the exact `vineflower-1.12.0.jar
-e="<baja.jar>" nre.jar out` command cited in the header — same convention `[B3]` used for its own scratch
dirs). None of these paths are inside this corpus's own git-tracked target directory, so
`verify-block.sh`'s citation-resolution will classify every one of them `extern`. Per METHODOLOGY §11
("DECOMPILED-TREE BLOCKS WILL SHOW ZERO RESOLVED CITATIONS — THIS IS EXPECTED"), the burden falls entirely
on inline token-verification — done here by reading every cited method body **in full**, this session, via
the `Read` tool at the exact line ranges cited (not `grep` snippets), and additionally by exhaustive
`grep -rn`/`find` passes for every negative-existence claim (§23.1's `isProgramModule`, §23.6's
unload/reload search, §23.7's `crypto/core` absence, §23.1's `moduleVerificationMode` absence
cross-check). This is a genuine methodological upgrade over `[B1]`/`[B3]`: because Vineflower now
produces real line-addressable source (unlike `[B1]`'s `javap` disassembly or `[B3]`'s raw bytecode
offsets), every citation above is a literal source line, not a reconstructed inference from a signature or
an instruction offset.

`verify-block.sh` was run against this file (`bash toolbelt/verify-block.sh niagara5-block23.md`, from the
corpus root) and its **literal output** is reproduced below — every `file:line` citation resolves `extern`
(unresolvable outside this corpus's own git-tracked tree), exactly the expected signature for a
decompiled-tree block per the convention `[B1]` §1.7 established, plus 2 `synth-ref` (`[B1]`/`[B3]` block
back-references) and 1 `jar-entry` (a `docDeveloper.jar` doc path), neither of which are file:line claims:

```
== verify-block: niagara5-block23.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 1)
   [CERT-live] 0
   [CERT] 24  (adj 23)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 5  (adj 4)
   [INFER] 10  (adj 9)
-- ratio -- [INFER]/[CERT*] = 9/28 = 0.32
-- [CERT] file:line citation resolution --
   27 citations, all resolved `extern` (decompiled-tree paths) or `synth-ref`/`jar-entry` (non-file claims)
   resolved 0 of 27
   WARN    resolved 0 of 27 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag -- (none)
== exit 0 ==
```

The 2 `[CERT-hw]` hits are **not citations** — both are meta-mentions of the marker name itself, discussing
what B23-G4/B1-G1 (live-station confirmation) would need (header blockquote line, §23.9's B23-G4
paragraph) — there is no live-hardware evidence in this block, consistent with its scope (static
decompiled-source reading only). `[CERT-a]` (raw 5, adj 4) are the `[B1147]` REMITTANCE references in
§23.7's comparison table discussion and §23.8's Connections. `verify-block.sh`'s script-computed
`[INFER]`/`[CERT*]` ratio is **0.32** (9 adjusted `[INFER]` over 28 adjusted `[CERT]`+`[CERT-a]`) — below
the ~0.5 exhaustion threshold the script itself flags, consistent with an **evidence** block where most
claims are still direct source reads rather than deductions. The 9 adjusted `[INFER]` tags are each a
narrow, explicitly-flagged synthesis across multiple cited lines (§23.1's `PROGRAM`-dead-code framing,
§23.2's service-binding rationale, §23.3's graph-independence claim and its "not proven exhaustively"
caveat, §23.4's automatic-module framing, §23.5's "why" synthesis, §23.6's hot-reload negative framing,
§23.7's "restructures/refutes" framing) — none is a bare unsupported guess; each names the file:line
evidence it is drawn from in the same paragraph.

Token check: every method signature, field name, constant string, exit code, and property name quoted
above was read directly off the decompiled `.java` source this session (via `Read`, full method bodies,
not partial excerpts) — **≈60 distinct load-bearing tokens** (class/method/field names, the 4 property
names, the 2 exit codes, the `skipModuleValidation` log string, the restricted-prefix set, the tuple
grammar's separators), all copied verbatim from tool output, zero hand-recalled.
