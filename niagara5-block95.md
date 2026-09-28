# Block 95 — Closing eight standing child gaps across five prior blocks: the 5 automatic-module jars' real packaging shape, `NiagaraRpc`'s defining module, `com.tridium.crypto.core`'s actual location (correcting Block 23), the NRE's hand-rolled DI container, module.xml-vs-`module-info` cross-validation, the `com.tridium.json`/`org.json` relationship, `IpProtocol`'s package placement, and the Nimbus OAuth2 SDK jar location

> Research closing eight previously-opened child gaps drawn from five different blocks, each re-read
> verbatim from its parent file before investigation (gap-ID discipline, task instructions): **B1-G6**
> ([Block 1] §1.9 — quoted in full below, the 5 module-info-less automatic-module jars); **B7-G2**
> ([Block 7] §7.9/§7.7 — `niagara.rpc.NiagaraRpc`'s defining module); **B23-G2**, **B23-G5**, **B23-G6**
> ([Block 23] §23.9 — `com.tridium.crypto.core` location, the `NreInstantiator` DI plumbing, and
> module.xml-vs-`module-info` divergence-detection); **B84-G1**, **B84-G2** ([Block 84] §84.x —
> `com.tridium.json`/`org.json` coexistence, and `IpProtocol`'s package placement); **B12-G1** ([Block 12]
> §12.17 — the Nimbus OAuth2 SDK jar location). All eight gap texts were opened from their parent block
> files this session and are quoted verbatim in each closing section below; none required a "backlog
> wording drifted" flag — every text matches the task assignment's paraphrase closely enough that no
> correction was needed. Covers: a full-corpus + live-install re-investigation of each named gap using
> file/jar census, targeted decompiled-source reads (all of it already present in this pre-existing
> corpus — no fresh decompilation was needed this session), and one N4-vs-N5 install cross-check. Does
> **not** cover: live-station confirmation of anything (`[CERT-hw]`/`[CERT-live]` gaps remain untouched);
> a full re-derivation of [Block 84]'s N4 4.15.3.28 corpus beyond the two jars opened for this session's
> own cross-check; tracing `com.tridium.oauth2`'s actual runtime use of the located Nimbus jars beyond
> confirming their existence and identity.
>
> Subject version: **N5 5.0.0.28 (Beta)**, same deployed-modules tree as every other N5 block
> (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`, 247 jars) plus, newly opened this
> session, its sibling **`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/jar-cache/`** directory (22
> module-named subdirectories holding per-module third-party JPMS-automatic-module jars — not censused by
> any prior block) and the live install's `bin/ext/` (`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/`).
> N4 cross-check baseline: `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/` (the same N4
> baseline [Block 1] used). Every source file read for this block already existed in the corpus's
> pre-existing decompiled tree at `organized/` (`_bin-ext/nre/vineflower/**`, `baja/vineflower/**`) — zero
> fresh Vineflower invocations were needed.
>
> Sources: `organized/_bin-ext/nre/vineflower/{com/tridium/crypto/core,com/tridium/nre/di,com/tridium/nre/firewall,com/tridium/json,niagara/nre/security}/**`
> · `organized/baja/vineflower/{niagara/rpc,niagara/firewall,com/tridium/sys/module,com/tridium/sys/Nre.java}/**`
> · `organized/_bin-ext/niagaraAnnotationProcessors/vineflower/niagara/nre/annotations/processors/NullProcessor.java`
> · live jars: `.../modules/{analyticsLibs,apachePoi,commonsIo,commonsLang,niagaraTest,baja}.jar`,
> `.../jar-cache/oauth2/*.jar`, `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/{nre,json-20260814}.jar` ·
> N4 baseline: `.../OptimizerSupervisor-N4.14.0.162/modules/{commonsLang-rt,niagaraTest-se}.jar` ·
> `docDeveloper.jar` → `doc/modules.html` ("uberjar and unterjar" / resource-root-directory sections,
> already quoted by [Block 1] §1.6, re-read here for the `LIB-EXT` vs `LIB-INF` naming question) ·
> parent blocks `niagara5-block{1,7,12,23,84}.md` (exact gap text and citing sections, quoted below).
>
> Method: `unzip -l`/`unzip -p` census of jar entries and manifests for the 5 automatic-module jars and
> the newly-found `jar-cache/` tree; `find`/`grep -rl` whole-corpus census (module attribution via path
> component after `organized/`) for `com.tridium.json`/`org.json`/`IpProtocol`/`nre.firewall`/
> `niagara.nre.security`, all `fallback/` directories excluded per task instructions; direct `Read` of
> already-decompiled `.java` files for every code-level claim (no `grep` snippets substituted for method
> bodies); one N4-vs-N5 jar-content diff (`commonsLang-rt.jar`/`niagaraTest-se.jar` vs their N5
> counterparts) for the B1-G6 "build omission" question. `sha256sum` on every jar cited by path. Markers
> (METHODOLOGY §3): `[CERT]` local primary source (jar-entry + `sha256`, or `file:line` into the
> pre-existing decompiled tree) · `[CERT-doc]` shipped doc · `[INFER]` deduction.
>
> **Type:** `evidence` — every section closes a named prior-block gap with a fresh primary-source
> citation; one section (§95.3) additionally **corrects** [Block 23] §23.7's own negative-existence claim.

---

## 95.1 — B1-G6 CLOSED: 2 of the 5 automatic-module jars are genuine `unterjar` third-party bundles; the other 3 ship zero library code, and one of those three is a real N5-beta build omission `[CERT]`

**Parent text** ([Block 1] §1.9, quoted verbatim): *"**B1-G6** — The 5 automatic-module JARs
(`analyticsLibs`, `apachePoi`, `commonsIo`, `commonsLang`, `niagaraTest`, §1.1/§1.6): confirm they are
`unterjar`-packaged third-party/test libraries (per §1.6's `unterjar` mechanism) rather than a build
omission, by inspecting their `LIB-EXT` directory contents."*

Full jar-entry listing this session (`unzip -l`, all 5, live `modules/` tree):

| Jar | LIB-INF nested jars | Own `.class` files | Verdict |
|---|---|---|---|
| `apachePoi.jar` | 8 unexploded jars (`poi-5.5.1`, `poi-ooxml-5.5.1`, `poi-ooxml-lite-5.5.1`, `xmlbeans-5.3.0`, `curvesapi-1.08`, `log4j-api-2.24.3`, `commons-collections4-4.5.0`, `commons-math3-3.6.1`) | 0 | **genuine `unterjar` bundle** |
| `commonsIo.jar` | 1 (`commons-io-2.22.0.jar`) | 0 | **genuine `unterjar` bundle** |
| `commonsLang.jar` | **0** | **0** | **empty — no LIB-INF, no classes at all** |
| `niagaraTest.jar` | 0 | 0 | empty (same shape in N4, see below — not a regression) |
| `analyticsLibs.jar` | 0 | 0 | not a library wrapper at all — a 54-dependency Niagara feature module shipping only a `module.palette` |

`[CERT]` (`unzip -l` output, this session, against `sha256` `4077124e0334375b3d82e6b18433e22f5ad37e4b0fcc50332cd986372834a6d4`
(`apachePoi.jar`), `708c3d054f2c7986ad1261cf30237c8e659efdf0524ddbb55980beb00dd8318c` (`commonsIo.jar`),
`4a0adcf954ed523c5d9223863306f38eabc3d15c3259261c2f26e8d128f53737` (`commonsLang.jar`),
`2d5c137bda93f900a3d5d927a6cdb5aac9397d03e443407e292f15e8fd232187` (`niagaraTest.jar`),
`eb08730dffece6cecd0593cf8491fb684957fd319090945487c75a5768f12a39` (`analyticsLibs.jar`)). Every one of
the 5 declares `Automatic-Module-Name: com.tridium.<name>` in `META-INF/MANIFEST.MF` (`[CERT]`, e.g.
`apachePoi`'s manifest: `Automatic-Module-Name: com.tridium.apachePoi`) — this manifest attribute, not
the presence/absence of library content, is the actual JPMS mechanism making all 5 "automatic modules"
(confirming [Block 1] §1.6's general claim at the manifest level for the first time).

**The doc-terminology question is resolved too**: `doc/modules.html`'s own "uberjar and unterjar"
paragraph says `unterjar` "includes the entire .jar in your module's **`LIB-EXT`** directory," but its
separate "resource roots" paragraph lists **`LIB-INF`** (not `LIB-EXT`) as the recognized top-level
directory name, and the actual packaged jars use `LIB-INF` (confirmed above) — matching the runtime
loader code too: `NModuleModuleFinderFactory.processPackagedDependencies` hard-codes
`moduleFileSystem.getPath("/LIB-INF")` (`organized/baja/vineflower/com/tridium/sys/module/NModuleModuleFinderFactory.java:437`)
`[CERT]`. So `LIB-EXT` is the doc's own (apparently stale/inconsistent) name for the *build-side* Gradle
`unterjar` DSL target; the *packaged and runtime-resolved* directory is unambiguously `LIB-INF` — this is
a doc-internal inconsistency, not a corpus contradiction (the gap's own "`LIB-EXT` directory contents"
phrasing, quoted verbatim above, comes from the doc's usage, not from [Block 1] itself).

**A cheap, on-topic bonus finding** (directly answers the gap's own "rather than a build omission"
clause): N4's parallel modules were opened for comparison. N4's `commonsLang-rt.jar`
(`OptimizerSupervisor-N4.14.0.162/modules/commonsLang-rt.jar`, `sha256`
`7f0bc12c6185479acb036b972c4660c9c08f18018f5a486b76144cf038d6aafb`) contains **403 real
`org/apache/commons/lang3/*.class` files** (`unzip -l | grep -c`, this session) — a genuinely populated
Commons Lang3 library. N5's `commonsLang.jar` has **zero**. N4's `niagaraTest-se.jar` (`sha256`
`48e2e8f193a72876691dd696eee4edf86d8dd918ee36472ad43d1fe9e28b7c3d`), by contrast, is **already** just a
6-entry manifest+module.xml+lexicon shell in N4 too — the same empty shape N5 has. `[CERT]` (both `unzip
-l` outputs, this session). **Net finding**: `niagaraTest`'s emptiness is normal, consistent
placeholder behavior across both major versions (its real test classes are presumably supplied at
project-build time via the doc's own `testUnterJar` dependency type, not shipped in the base
distribution) — **not** the gap's feared "build omission." `commonsLang`'s emptiness, however, **is** a
genuine content loss specific to this N5 5.0.0.28 beta build: the module shell, dependency graph, and
"Apache Commons Lang" description all survive, but the library payload that N4 shipped (and that
`apachePoi`/`commonsIo` correctly ship via `unterjar` in this very same beta) is missing.

**GAP CLOSED.** Answer: heterogeneous, not uniform — 2/5 (`apachePoi`, `commonsIo`) are genuine
`unterjar`-packaged third-party bundles exactly as documented; `niagaraTest` is intentionally empty in
both N4 and N5 (not a defect); `analyticsLibs` isn't a library wrapper at all (a palette-only feature
module); and `commonsLang` is a real N5-5.0.0.28-beta packaging omission — the wrapper module exists but
its `unterjar`'d payload does not, confirmed by a direct N4 content diff.

## 95.2 — B7-G2 CLOSED: `niagara.rpc.NiagaraRpc` is defined in `baja.jar` itself — the same corpus [Block 7] was already reading — while `NullProcessor` lives in the separate `bin/ext/niagaraAnnotationProcessors.jar` `[CERT]`

**Parent text** ([Block 7] §7.9, quoted verbatim): *"**[TO ANNOTATE — child gap B7-G2]** —
`niagara.rpc.NiagaraRpc`, claimed by `NullProcessor` (§7.7) but its defining module/package was not
located in this session's 2 opened jars; likely lives in an RPC-specific Niagara module not yet
identified in this corpus."*

`niagara.rpc.NiagaraRpc` is a plain `@Target(ElementType.METHOD)`/`@Retention(RUNTIME)` annotation:

```java
package niagara.rpc;
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface NiagaraRpc {
   Transport[] transports();
   String permissions() default "I";
   Protected[] protectedTargets() default {};
   boolean isSecure() default false;
}
```
`[CERT]` (`organized/baja/vineflower/niagara/rpc/NiagaraRpc.java`, whole file — decompiled from
`baja.jar`'s own `niagara/rpc/NiagaraRpc.class`, confirmed present via `find` this session; `baja.jar`
`sha256` `0a7fcbfcbd1a609ed0eba0c1abfbf7e3de372b6a51f551dcea497649d4e3fd9c`). It lives in `baja.jar`
alongside sibling `niagara.rpc.{Transport,Protected,TransportType}` — the same package [Block 7]'s own
`NiagaraSlotProcessor`/`ModuleInclude` investigation was already reading `baja.jar` for, just a different
package within it — **not** a separate "RPC-specific module" as the gap speculated.

`NullProcessor` itself, which claims the annotation via `@SupportedAnnotationTypes` without processing
it (§7.7), lives in a **different** jar: `bin/ext/niagaraAnnotationProcessors.jar`
(`organized/_bin-ext/niagaraAnnotationProcessors/vineflower/niagara/nre/annotations/processors/NullProcessor.java`)
`[CERT]` — a `bin/ext/` bootstrap-classpath jar, not one of the 247 `modules/` jars — confirming why
[Block 7]'s own search of "`niagaraAnnotationProcessors.jar`" for `niagara/rpc` came up empty: the
annotation and its claiming processor are simply in two different jars on two different classpaths
(compile-time annotation-processor path vs. runtime `baja.jar`), which is ordinary for a
compile-time-only marker annotation.

**GAP CLOSED.** Answer: `niagara.rpc.NiagaraRpc` is defined in `baja.jar` (`niagara.rpc` package,
alongside `Transport`/`Protected`/`TransportType`) — the exact opposite of "a different, RPC-specific
module."

## 95.3 — B23-G2 CLOSED (and corrects [Block 23] §23.7): `com.tridium.crypto.core` is present in `nre.jar` — 152 zip entries, already decompiled in this corpus — and its module-signature path explicitly disables PKIX revocation checking `[CERT]`

**Parent text** ([Block 23] §23.9, quoted verbatim): *"**B23-G2** — Decompile/RE
`com.tridium.crypto.core.io.CoreCryptoManager.validateCertChain` (absent from both `baja.jar` and
`nre.jar` this session, likely lives in a `crypto`/`platCrypto`-family jar not yet identified in this
corpus) to confirm PKIX construction and whether revocation checking is disabled for the
module-signature path, mirroring N4's still-open `SES9-G1`."*

`com.tridium.crypto.core.**` is **present** in the exact same `nre.jar` [Block 23] opened
(`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar`, `sha256`
`d563a334e02ef739d53bb67ddf48de96582b787dff89a8ab1c5140cdf381f9f7` — matches [Block 84]'s independently
recorded N5-side hash for the same file verbatim) — `unzip -l | grep -c "crypto/core/"` → **152** entries
this session `[CERT]`. It is also **already decompiled** in this corpus's own pre-existing tree at
`organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/**` (419 total `.java` files under
`organized/_bin-ext/nre/vineflower/`, including `io/CoreCryptoManager.java`, `cert/CertificateChainValidator.java`,
`provider/{IProvider,NProvider}.java`, etc.) — no fresh decompilation was needed this session.

`CoreCryptoManager.validateCertChain(CodeSigner, boolean)` (line 1136) delegates to a private
`CertificateChainValidator certValidator` field (line 149, instantiated at line 925) whose own
`validateCertChain(CertPath, Timestamp, PKIXCertPathChecker)` does the real PKIX work:

```java
CertPathValidator validator = CertPathValidator.getInstance("PKIX");
PKIXParameters params = new PKIXParameters(this.trustAnchors);
params.addCertPathChecker(checker);
params.setRevocationEnabled(false);
```
`[CERT]` (`organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/CertificateChainValidator.java:148-151`).
**Revocation checking is explicitly and unconditionally disabled** (`setRevocationEnabled(false)`, no
CRL/OCSP consultation anywhere in this path) for the exact module/JAR-signature-validation call chain
[Block 23] §23.7 traced (`NModuleModuleFinderFactory.verifyModuleSignature` → `CoreCryptoManager.validateCertChain`
→ `CertificateChainValidator.validateCertChain`) — **this is the same finding N4's `SES9-G1` left open**,
now confirmed at the N5 source level: module/JAR signature chains are validated for trust-anchor
membership and expiry only, never for revocation, mirroring N4's design exactly.

**Correction to [Block 23]** (§95.x below has the formal entry): §23.7's own text calls
`com.tridium.crypto.core` "absent from both `baja.jar`'s and `nre.jar`'s decompiled trees" and cites a
`find … -ipath "*crypto/core*"` returning zero over its own **freshly re-decompiled scratch copy**
(`/tmp/claude-1000/n5b23/out/`, not preserved — task instructions forbid archiving decompile scratch).
This session's `find` over the corpus's **pre-existing** `organized/_bin-ext/nre/vineflower/` tree — the
same `nre.jar`, same `sha256` — returns the package in full. The most likely explanation (`[INFER]`,
not verified further this session) is that [Block 23]'s own scratch Vineflower invocation into `/tmp`
was incomplete for this specific package (a large decompile silently dropping one subtree), not that
the package is genuinely absent — flagged as a new child gap, B95-G4, rather than resolved definitively
here.

**GAP CLOSED.** Answer: present, 152 entries, already in-corpus; revocation checking is disabled
(`setRevocationEnabled(false)`) for the module-signature path, confirming the N4 `SES9-G1` parallel.

## 95.4 — B23-G5 CLOSED: `NreInstantiator` is a minimal, permission-gated, reflection-based singleton-supplier registry — three independent boot paths each wire it with exactly one supplier, for `ISecurityInitializer` `[CERT]`

**Parent text** ([Block 23] §23.9, quoted verbatim): *"**B23-G5** —
`com.tridium.nre.di.NreInstantiator`/`SingletonSupplier`/`TypeSupplier` (referenced in `Bootstrap`'s
static initializer for wiring `ISecurityInitializer`, `Bootstrap.java:320-328`) were not
decompiled/traced — tangential DI plumbing, out of scope for this block's loader focus."*

The whole `com.tridium.nre.di` package is 7 small classes, all read in full this session
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/di/*.java`): `NreInstantiator` holds a
`Map<Class<?>, TypeSupplier<?>>` (`ConcurrentHashMap`), guarded on every `addSupplier`/`getSupplier`/
`removeSupplier`/effectively-`instance` call by `SecurityUtil.checkPermission(NiagaraBasicPermission.NRE_SUPPLIER_PERMISSION)`
(`NreInstantiator.java:12,21,30,38` region) `[CERT]`. `instance(Class<T>)` looks up the registered
`TypeSupplier`, type-checks it, and delegates to `supplier.get(this)`. `SingletonSupplier<T> extends
BaseSupplier<T>` lazily constructs-once (guards re-entrancy with a `recursive` counter that throws on
recursive creation) and caches the instance. `BaseSupplier.createNewInstance` uses reflection: a
`@RequiresInstantiator`-annotated target class gets its `(NreInstantiator)`-arg constructor invoked
(constructor injection of the instantiator itself); otherwise the no-arg constructor is used. A
`@RequiresConfiguration`-annotated target additionally gets a named setter-style method invoked
post-construction with the supplier's stashed `config` object (`BaseSupplier.java:24-51`) — i.e. this is
a small hand-rolled reflection-based DI container (annotation-driven constructor/config injection,
type-keyed singleton cache), not a general framework.

`Bootstrap`'s static initializer (`Bootstrap.java:320-327`, matching the gap's own cited line range)
registers **exactly one** supplier:
```java
static {
   TypeSupplier<ISecurityInitializer> secIntSupplier =
      new SingletonSupplier<>(ISecurityInitializer.class, SecurityInitializer.class, new DefaultSecurityInitializerConfig());
   SecurityUtil.doPrivileged(() -> { INSTANTIATOR.addSupplier(secIntSupplier); return null; });
}
```
`[CERT]`. Two **other** boot paths do the identical wiring independently, each with its **own**
`NreInstantiator` instance (not a shared singleton across the JVM): `com.tridium.sys.Nre`
(`organized/baja/vineflower/com/tridium/sys/Nre.java:1186,1198`, `baja.jar`) and
`com.tridium.niagarad.NiagaraDaemon`
(`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/NiagaraDaemon.java:128,1461`, the niagarad
daemon) `[CERT]` (both files, exact lines, grepped and read this session). In all three, the only
registered supplier type is `ISecurityInitializer`.

**GAP CLOSED.** Answer: a tiny permission-gated reflection-based DI container, independently
instantiated per boot entry point (`Bootstrap`, `Nre`, `NiagaraDaemon`), wired in every case with exactly
one supplier (`ISecurityInitializer` → `SecurityInitializer`) — not general-purpose DI plumbing, a
narrowly-scoped bootstrap indirection for one security interface.

## 95.5 — B23-G6 CLOSED: the module.xml `<dependency>` graph and the JPMS `module-info` `requires` graph are read by two textually disjoint code paths with zero cross-reference — yes, they can be edited out of sync undetected `[CERT]`

**Parent text** ([Block 23] §23.9, quoted verbatim): *"**B23-G6** — Confirm whether the module.xml
`<dependency>` graph and the compiled `module-info.class` `requires` graph (§23.3, shown independent but
not proven exhaustively divergence-free) can be edited out of sync without either resolution mechanism
detecting it."*

The module.xml graph is read exclusively through `com.tridium.sys.module.Dependency`
(`organized/baja/vineflower/com/tridium/sys/module/Dependency.java` — a plain 4-field holder:
`moduleName`, `bajaVersion`, `vendor`, `vendorVersion`) and consumed only by `NModule` (which parses it
via `readXml`) and `ModuleManager.resolve`:
```java
private void resolve(NModule m, Map<String, NModule> pendingAdd) throws ModuleException {
   if (m.depends != null) {
      for (int i = 0; i < m.depends.length; i++) {
         Dependency d = m.depends[i];
         ...
         d.resolution = this.loadDependency(d.moduleName, pendingAdd);
         d.resolution.checkBajaVersion(d.bajaVersion);
         d.resolution.checkVendor(d.vendor, d.vendorVersion);
```
`[CERT]` (`organized/baja/vineflower/com/tridium/sys/module/ModuleManager.java:920-937`). This is
Niagara's own load-ordering/version-compatibility check — it only ever validates `bajaVersion`/`vendor`/
`vendorVersion` against the loaded target module's own metadata, never against that module's
`module-info.class`.

`NModuleModuleFinderFactory` — the class that builds the actual JPMS `ModuleFinder`/`Configuration` (the
class [Block 23] §23.1-23.4 already traced) — **never references `Dependency` or `.depends` anywhere**
(`grep -n "\.depends\b\|class Dependency\b"` over every `.java` in
`organized/baja/vineflower/com/tridium/sys/module/` returns hits only in `Dependency.java`, `NModule.java`,
`ModuleManager.java` — zero in `NModuleModuleFinderFactory.java`) `[CERT]`. Its own uses of the word
"dependency" (`scanDependency`, `processPackagedDependencies`, `dependencyPath`) refer exclusively to
`unterjar`-packaged **`LIB-INF` nested jars** (§95.1) — an unrelated concept — each of which becomes its
own JPMS `ModuleReference` (`NModuleDependencyModuleReference`,
`NModuleModuleFinderFactory.java:436-467,500-518`) via `Configuration.resolve`'s ordinary JPMS
module-graph resolution, driven purely by `module-info.class` `requires` edges.

**GAP CLOSED.** Answer: yes — these are two textually disjoint graphs read by two disjoint code paths
(`ModuleManager`/`Dependency` for module.xml; `NModuleModuleFinderFactory`/JPMS `Configuration` for
`module-info`), with no call site in either class referencing the other's data structure. Nothing in the
loader code this corpus has decompiled would notice if a `module.xml <dependency>` entry and a
`module-info requires` clause for the same module pair disagreed — each graph independently drives its
own resolution mechanism (Niagara load-ordering vs. JPMS `Configuration`), and a module could in
principle load successfully under one graph while silently carrying a stale/incorrect entry in the
other. (Scope note: this confirms the absence of cross-validation in the ~2,300 lines of loader code this
corpus has read across [Block 1]/[Block 23]; it does not rule out a check living in code neither block
has opened.)

## 95.6 — B84-G1 CLOSED: `com.tridium.json` is not a competing legacy library "coexisting" with `org.json` — it is a 3-class NRE convenience wrapper *built on* `org.json`, and every one of its 121 call sites already imports `org.json` in the same file `[CERT]`

**Parent text** ([Block 84] §84.x, quoted verbatim): *"**B84-G1** — `com.tridium.json` (N4's vendored
JSON library) and `org.json` (the real third-party library) **coexist** in the N5 5.0.0.28 corpus — 121
files still reference `com.tridium.json`, 398 reference `org.json` (`grep -rl`, this session,
whole-corpus, `fallback/` excluded). Whether this is a completed per-module swap (some modules fully on
`org.json`, others never touched) or an in-progress migration needs a per-module breakdown, not
performed this session."*

Per-module breakdown (`grep -rl`, whole corpus, `fallback/` excluded, this session): the **entire**
`com.tridium.json` package is exactly 3 classes — `JSONUtil.java`, `pretty/PrettyJSONStringer.java`,
`quick/QuickJSONWriter.java` — all three living in `nre.jar`
(`organized/_bin-ext/nre/vineflower/com/tridium/json/**`) `[CERT]`. `JSONUtil.java` itself:
```java
package com.tridium.json;
...
import org.json.JSONArray;
import org.json.JSONObject;
public final class JSONUtil { ... }
```
`[CERT]` (`organized/_bin-ext/nre/vineflower/com/tridium/json/JSONUtil.java:1-13`) — it is a thin
adapter/utility layer (unmodifiable-view wrappers for `JSONArray`/`JSONObject`) written *on top of*
`org.json`, not an alternative to it. Confirming the pattern corpus-wide: **all 121 of 121** files that
import `com.tridium.json` also import `org.json` in the **same file** (`grep -rl com.tridium.json | xargs
grep -l org.json | wc -l` → 121, matching the total exactly) `[CERT]` — there is not a single file that
uses `com.tridium.json` without `org.json` alongside it. The per-module split requested by the gap
(34 modules import both packages somewhere in their tree; 0 modules import `com.tridium.json` only; 22
modules import `org.json` only) reflects this same layering: modules using the convenience wrapper
necessarily also use the base library it wraps.

**GAP CLOSED.** Answer: not a migration, in progress or otherwise — `com.tridium.json` is a permanent,
tiny (3-class) Tridium convenience layer over `org.json`, which is why every one of its use sites also
imports `org.json` directly. There is no module still "fully on" a separate legacy JSON library to
migrate away from.

## 95.7 — B84-G2 CLOSED: `IpProtocol`'s presence in `niagara.nre.security` reflects genuine broad reuse (firewall + ~15 other driver/service modules + `baja.jar`'s own `BIpProtocolEnum` slot wrapper), not a firewall→security package merge and not coincidence `[CERT]`

**Parent text** ([Block 84] §84.x, quoted verbatim): *"**B84-G2** — `IpProtocol`'s package move,
`com.tridium.nre.firewall` (N4) → `niagara.nre.security` (N5, `organized/_bin-ext/nre/vineflower/niagara/nre/security/IpProtocol.java`),
sits inside a much larger `niagara.nre.security` package (593 files corpus-wide) versus a small residual
`nre.firewall` (14 files still present, `grep -rl`, this session). Whether `nre.security` is a genuine
`firewall`-package consolidation/rename or a coincidentally-large unrelated package needs its own
census."*

Both file counts reproduce exactly this session: `grep -rl "niagara\.nre\.security"` (fallback excluded)
→ **593**; `grep -rl "nre\.firewall"` → **14** `[CERT]`. `IpProtocol` itself is a 3-value enum (`TCP`,
`UDP`, `TCP_AND_UDP`, `organized/_bin-ext/nre/vineflower/niagara/nre/security/IpProtocol.java`). Its
corpus-wide callers (`grep -rl "IpProtocol"`, fallback excluded) span **every** `com.tridium.nre.firewall`
class (`FirewallRule`, `NoOpRule`, `RedirectRule`, `InputRule`, `NftablesFirewallProcessor` — all import
it directly, e.g. `FirewallRule.java:3` `protected IpProtocol ipProtocol;`) **plus** at least 15
unrelated driver/service modules that have nothing to do with the firewall: `bacnet`
(`BBacnetIpServerPort`/`BBacnetIpLinkLayer`), `modbusTcpSlave`, `net.BFirewallPortHelper`,
`fox.BFoxService`, `tunnel.BTunnelService`, `niagaraSync.BSecondaryHeartbeat`, `opcUaServer.BOpcUaServer`,
`lonIp` (2 classes), `web.BWebService`, `nSnmp.BSnmpNetwork`, `migrator.BProgramConverter` `[CERT]` (full
`grep -rl` file list, this session).

Most tellingly: `baja.jar`'s own **`niagara.firewall.BIpProtocolEnum`** — the Niagara-slot-visible
`BFrozenEnum` used by `BServerPort`'s UX-exposed `ipProtocol` property, in a **different** package from
`IpProtocol` — itself imports `niagara.nre.security.IpProtocol` directly:
```java
package niagara.firewall;
import niagara.nre.security.IpProtocol;
...
@NiagaraEnum(range = {@Range("tcp"), @Range("udp"), @Range("tcpAndUdp")})
public final class BIpProtocolEnum extends BFrozenEnum { ... }
```
`[CERT]` (`organized/baja/vineflower/niagara/firewall/BIpProtocolEnum.java:1-15`) — the same
TCP/UDP/TCP_AND_UDP domain, mirrored as a Niagara slot enum. So `com.tridium.nre.firewall` (small, 14
files, still a standalone package in N5 — **not merged into `nre.security`**) and `niagara.firewall`
(baja.jar's own separate package, holding `BIpProtocolEnum`/`BServerPort`) are two **different**,
still-independent firewall-adjacent packages, and both depend on `niagara.nre.security.IpProtocol` as a
shared low-level primitive — the same relationship `niagara.nre.security`'s other ~590 files have with
their own general cross-cutting consumers (TLS parameters, crypto, secrets, permissions — [Block 12]
already catalogued this package's crypto/TLS content in detail).

**GAP CLOSED.** Answer: neither. `nre.security` is not a firewall-package rename/consolidation (the
firewall packages still exist standalone, unmerged, in both `com.tridium.nre.firewall` and
`niagara.firewall`) and it is not coincidental (`IpProtocol` is a genuinely general, widely-reused
protocol-tag primitive — consumed directly by firewall rule classes, a dozen unrelated driver/service
modules, and `baja.jar`'s own Niagara-slot-facing enum wrapper). Its placement in the general
`niagara.nre.security` package reflects real cross-module reuse, the same pattern the package's other
content follows.

## 95.8 — B12-G1 CLOSED: the Nimbus OAuth2 SDK jars live in a previously-uncensused `jar-cache/<module>/` directory tree, sibling to `modules/` and `bin/ext/` `[CERT]`

**Parent text** ([Block 12] §12.17, quoted verbatim): *"**B12-G1** — Locate the JPMS automatic-module
jar(s) backing `oauth2`'s `com.nimbusds.jose.jwt` / `com.nimbusds.oauth2.sdk` / `org.json` `requires`
(§12.12, §12.16 [C1])."*

`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/jar-cache/` — a directory neither [Block 1] nor
[Block 12] searched (both stopped at `modules/` and `bin/ext/`) — holds **22 module-named
subdirectories** (`oauth2`, `saml`, `totpAuth`, `apachePoi`, `commonsIo`, `email`, `gx`, `jodaTime`,
`jsonSmart`, `jsonToolkit`, `rdb`, `svgBatik`, `xprotect`, etc. — `ls`, this session), each holding the
unexploded third-party jars that module's `unterjar` dependencies resolve to at deployment time.
`jar-cache/oauth2/` contains exactly 5 jars:

| Jar | `Automatic-Module-Name` | Role |
|---|---|---|
| `nimbus-jose-jwt-10.0.2.jar` | `com.nimbusds.jose.jwt` | the `requires com.nimbusds.jose.jwt` target `[CERT]` |
| `oauth2-oidc-sdk-11.26-jdk11.jar` | `com.nimbusds.oauth2.sdk` | the `requires transitive com.nimbusds.oauth2.sdk` target `[CERT]` |
| `content-type-2.3.jar`, `jcip-annotations-1.0-1.jar`, `lang-tag-1.7.jar` | (transitive deps) | Nimbus OAuth2 SDK's own dependency closure |

`[CERT]` (`unzip -p <jar> META-INF/MANIFEST.MF` for both named jars, this session — `nimbus-jose-jwt`:
`Implementation-Title: Nimbus JOSE+JWT`, `Automatic-Module-Name: com.nimbusds.jose.jwt`;
`oauth2-oidc-sdk`: `Implementation-Title: OAuth 2.0 SDK with OpenID Connect extensions`,
`Automatic-Module-Name: com.nimbusds.oauth2.sdk`; `sha256` of `nimbus-jose-jwt-10.0.2.jar`
`960b978a6cd6cbc3319648adc73959789f6742a2bf1e8dd0c843dbc91624218a`). The third `requires`,
`org.json`, resolves separately and **not** from `jar-cache/`: it ships as a plain `bin/ext/` jar,
`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/json-20260814.jar` (`sha256`
`a04b6178f7fc0df38e1e93afe048baf1b56155ef8fd2a70b45e313bc23a8d754`) `[CERT]` — the same `bin/ext/`
location as `nre.jar` itself, i.e. a corpus-wide shared dependency rather than an `oauth2`-specific one.

**GAP CLOSED.** Answer: `jar-cache/oauth2/nimbus-jose-jwt-10.0.2.jar` and
`jar-cache/oauth2/oauth2-oidc-sdk-11.26-jdk11.jar` (both confirmed via `Automatic-Module-Name`); `org.json`
itself is a separate, corpus-wide `bin/ext/json-20260814.jar`. The broader discovery — a whole
`jar-cache/<module>/` deployment-directory family this corpus has never censused — is opened as its own
child gap (B95-G2) below, since it plausibly resolves several *other* blocks' "couldn't locate the
vendored third-party jar" open questions (e.g. [Block 12]'s own `totpAuth`/SAML gaps) beyond just oauth2.

## 95.9 — Corrections to earlier blocks

- **[Block 23] §23.7** (`niagara5-block23.md:276`) — **old claim**: *"`com.tridium.crypto.core`
  (`CoreCryptoManager`, `JarSignatureRegistry`, `CertUtils`, `ValidationException` — every type both
  gates call into) is **absent from both `baja.jar`'s and `nre.jar`'s decompiled trees**: `find …
  -ipath "*crypto/core*"` over `organized/baja/vineflower/` returns zero directories or files, and the
  same is true of the freshly-decompiled `nre.jar` tree."* — **new claim** (this session, §95.3 above):
  `com.tridium.crypto.core.**` is present in the same `nre.jar` (identical `sha256`
  `d563a334e02ef739d53bb67ddf48de96582b787dff89a8ab1c5140cdf381f9f7`), 152 zip entries, and is already
  fully decompiled in this corpus's own pre-existing `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/**`
  tree (419 `.java` files total under `organized/_bin-ext/nre/vineflower/`). **Evidence**: `find
  organized -ipath "*crypto/core*"` this session returns 30+ hits under exactly that path; `unzip -l
  <nre.jar> | grep -c "crypto/core/"` → 152. [Block 23]'s absence claim was correct only for its own
  scratch re-decompile at `/tmp/claude-1000/n5b23/out/` (never preserved, per task instructions) — it did
  not check the corpus's own pre-existing `organized/_bin-ext/nre/vineflower/` tree for the same jar.
  Root cause of the scratch-decompile gap is not established this session (flagged as B95-G4).

## 95.10 — Connections

- **[Block 1]** — §95.1's `apachePoi`/`commonsIo` unterjar finding, and the `LIB-INF` runtime-resolution
  confirmation via `NModuleModuleFinderFactory.processPackagedDependencies`, deepen [Block 1] §1.6's
  documentary-only `unterjar` citation into a source-level one; the `commonsLang` empty-payload finding
  is a genuine new N5-5.0.0.28-beta defect candidate not previously recorded anywhere in this corpus.
- **[Block 7]** — §95.2 confirms `niagara.rpc.NiagaraRpc` sits in the exact `baja.jar` [Block 7] already
  read for `NiagaraSlotProcessor`/`ModuleInclude`; no new jar needed to be opened.
- **[Block 8]** — `NiagaraBasicPermission.NRE_SUPPLIER_PERMISSION` (§95.4's `NreInstantiator` gate) is
  another concrete instance of [Block 8]'s permission-annotation model gating a specific NRE-internal
  operation, alongside the firewall/session/crypto examples [Block 12] §12.18 already catalogued.
- **[Block 12]** — §95.8 directly closes [Block 12]'s own B12-G1 and opens a broader `jar-cache/`
  child gap (B95-G2) that plausibly also resolves [Block 12]'s still-open B12-G5 (`totpAuth` enrollment
  UI wiring) and B12-G6 (SAML IdP flow) third-party-jar questions, since `jar-cache/totpAuth/` and
  `jar-cache/saml/` both exist and were not opened this session.
- **[Block 23]** — §95.3, §95.4, §95.5, and §95.9 all close or correct [Block 23] gaps directly; §95.5's
  finding (no cross-validation between module.xml deps and `module-info` requires) is a direct
  structural sibling of §23.3's already-documented "two independent, never-cross-checked graphs" framing
  — this session supplies the "and neither notices divergence" half that §23.3 left as future work.
  `SES9-G1`'s N4-side revocation-disabled finding (referenced by §95.3) is `niagara-research`-corpus
  territory, not re-verified here — cited by name only, per [Block 23]'s own convention.
- **[Block 84]** — §95.6 and §95.7 close both of [Block 84]'s own child gaps; the N4-vs-N5 jar diff
  technique (unzip + direct content compare, no decompile needed) reuses [Block 84]'s own
  already-established N4-4.15.3.28-cross-check method, applied here instead to N4-4.14.0.162 (the
  original [Block 1] baseline) for the narrower `commonsLang`/`niagaraTest` question.

## 95.11 — Child gaps opened

- **B95-G1** (requires external artifact) — Confirm whether N5's `commonsLang.jar` empty-payload defect
  (§95.1) is present in a later N5 5.0.0.28 build or fixed in a subsequent beta/release — this corpus has
  only the one 5.0.0.28 snapshot; needs either a newer build or an official Tridium release-note/issue
  reference. Priority: **low** (cosmetic/packaging defect, not a behavior-affecting finding).
- **B95-G2** — Census and trace the newly-discovered `jar-cache/<module>/` deployment-directory family
  (22 module subdirectories found this session: `oauth2`, `saml`, `totpAuth`, `apachePoi`, `commonsIo`,
  `email`, `gx`, `jodaTime`, `jsonSmart`, `jsonToolkit`, `rdb`, `rdbHsqlDb`, `rdbSqlServer`,
  `abstractMqttDriver`, `axvelocity`, `cloudLink`, `commonsCompress`, `devkit`, `opcUaCore`, `snmpLibs`,
  `svgBatik`, `test`, `xprotect`) — what build-side Gradle mechanism populates it, whether it is
  `unterjar`'s actual deployment target (as opposed to/in addition to `LIB-INF`), and whether it resolves
  other blocks' unlocated-third-party-jar gaps (candidates: [Block 12]'s B12-G5/B12-G6). Priority:
  **medium** — directly useful to multiple other open gaps.
- **B95-G3** — Trace real call sites of `com.tridium.json`'s other two classes,
  `pretty.PrettyJSONStringer` and `quick.QuickJSONWriter` (only `JSONUtil`'s self-contained
  `org.json`-wrapping was read in full this session, §95.6). Priority: **low**.
- **B95-G4** — Root-cause why [Block 23]'s own freshly-decompiled `nre.jar` scratch copy
  (`/tmp/claude-1000/n5b23/out/`, not preserved) omitted `com/tridium/crypto/core/**` entirely, when this
  session's `find` over the corpus's pre-existing `organized/_bin-ext/nre/vineflower/` tree — same jar,
  same `sha256` — finds it in full (§95.3, §95.9). Needs re-running [Block 23]'s exact documented
  Vineflower invocation to see if the omission reproduces (decompiler flakiness) or was a `find`-path
  transcription error in that session. Priority: **low** (methodology-hygiene gap, not a corpus-fact
  gap — the fact itself is now settled).
- **B95-G5** — Trace whether `BServerPort`'s wire-level socket setup actually converts
  `niagara.firewall.BIpProtocolEnum` (the Niagara-slot enum, §95.7) into `niagara.nre.security.IpProtocol`
  (the plain enum) at a single well-defined boundary, or whether the two enums' TCP/UDP/TCP_AND_UDP
  domains are kept in sync by convention only (no shared source of truth found this session). Priority:
  **low**.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 5 automatic-module jars: 2 genuine `unterjar` bundles, 3 empty of library content | `[CERT]` | `unzip -l` all 5 jars, this session, `sha256` per jar in §95.1 |
| 2 | All 5 declare `Automatic-Module-Name: com.tridium.<name>` in `MANIFEST.MF` | `[CERT]` | `unzip -p … MANIFEST.MF`, this session |
| 3 | `LIB-INF` (not `LIB-EXT`) is the runtime-resolved packaged-dependency directory name | `[CERT]` | `NModuleModuleFinderFactory.java:437`, `unzip -l` entries |
| 4 | N4's `commonsLang-rt.jar` ships 403 real Commons Lang3 classes; N5's `commonsLang.jar` ships zero | `[CERT]` | `unzip -l | grep -c`, both jars, `sha256` in §95.1 |
| 5 | N4's `niagaraTest-se.jar` is already a 6-entry empty shell, same as N5's | `[CERT]` | `unzip -l`, this session |
| 6 | `niagara.rpc.NiagaraRpc` is defined in `baja.jar`'s `niagara.rpc` package | `[CERT]` | `organized/baja/vineflower/niagara/rpc/NiagaraRpc.java`, whole file |
| 7 | `NullProcessor` lives in `bin/ext/niagaraAnnotationProcessors.jar`, a different jar | `[CERT]` | `organized/_bin-ext/niagaraAnnotationProcessors/vineflower/…/NullProcessor.java` |
| 8 | `com.tridium.crypto.core` present in `nre.jar`, 152 entries, already decompiled in-corpus | `[CERT]` | `unzip -l | grep -c`; `find organized -ipath "*crypto/core*"` |
| 9 | Module-signature-path PKIX validation sets `setRevocationEnabled(false)` | `[CERT]` | `CertificateChainValidator.java:151` |
| 10 | `NreInstantiator`/`SingletonSupplier`/`BaseSupplier` mechanics (permission gate, reflection injection) | `[CERT]` | `organized/_bin-ext/nre/vineflower/com/tridium/nre/di/*.java`, whole files |
| 11 | 3 independent boot paths (`Bootstrap`, `Nre`, `NiagaraDaemon`) each wire one `ISecurityInitializer` supplier | `[CERT]` | `Bootstrap.java:320-327`, `Nre.java:1186-1198`, `NiagaraDaemon.java:128,1461` |
| 12 | `NModuleModuleFinderFactory` never references `Dependency`/`.depends`; `ModuleManager` never references JPMS `requires` | `[CERT]` | `grep -n` over `com/tridium/sys/module/*.java`, this session |
| 13 | `com.tridium.json` is exactly 3 classes, all importing `org.json`, all in `nre.jar` | `[CERT]` | `organized/_bin-ext/nre/vineflower/com/tridium/json/**`, `JSONUtil.java:1-13` |
| 14 | 121/121 `com.tridium.json`-importing files also import `org.json` in the same file | `[CERT]` | `grep -rl … | xargs grep -l …`, this session |
| 15 | `nre.security` = 593 files, `nre.firewall` = 14 files, corpus-wide (fallback excluded) | `[CERT]` | `grep -rl`, this session, reproduces [Block 84]'s own counts exactly |
| 16 | `IpProtocol` used directly by every `nre.firewall` class plus 15+ unrelated driver/service modules plus `baja.jar`'s own `BIpProtocolEnum` | `[CERT]` | `grep -rl "IpProtocol"` file list; `BIpProtocolEnum.java:1-15` |
| 17 | Nimbus jars located at `jar-cache/oauth2/{nimbus-jose-jwt-10.0.2,oauth2-oidc-sdk-11.26-jdk11}.jar`; `org.json` at `bin/ext/json-20260814.jar` | `[CERT]` | `ls`, `unzip -p … MANIFEST.MF`, `sha256sum`, this session |
| 18 | `jar-cache/` holds 22 module-named subdirectories, not censused by any prior block | `[CERT]` | `ls jar-cache/`, this session |
| 19 | [Block 23] §23.7's negative-existence claim for `crypto.core` is contradicted by this session's evidence | `[CERT]` | §95.9, citing `niagara5-block23.md:276` verbatim plus items 8-9 above |

**Tally** (mechanical `grep -o` count over the finished file, RAW = whole file; ADJUSTED = RAW minus the
1 header-legend occurrence of each marker per METHODOLOGY §11): `[CERT]` raw 62 / adjusted 61 ·
`[CERT-doc]` raw 1 / adjusted 0 · `[INFER]` raw 3 / adjusted 2. `[INFER]`/`[CERT]` ratio ≈ **0.03** — low,
evidence-dominant, consistent with an **evidence** block: every one of the 8 assigned gaps closed on a
direct `[CERT]`-class citation (jar entry + `sha256`, or `file:line` into the pre-existing decompiled
tree), with the 2 real `[INFER]`s confined to (a) speculating why [Block 23]'s own scratch decompile
missed `crypto/core` (§95.3/§95.9, left open as B95-G4 rather than asserted) and (b) reading `LIB-EXT`
as the doc's build-side/Gradle-DSL name for the packaged `LIB-INF` directory (§95.1).

**Self-verification note** (decompiled/bytecode-and-jar-evidence block, per METHODOLOGY §11): every
`[CERT]` citation above points to a jar zip-entry (`unzip -l`/`unzip -p`, resolved by `sha256`) or a
`file:line` into the corpus's **pre-existing** `organized/` decompiled tree (gitignored, `git ls-files
organized | wc -l` → 0, same convention every other N5 block uses) — none of these are addressable by
`verify-block.sh`'s git-based citation resolver, so it will report 100% `extern`, exactly as expected and
documented for this block type. The burden falls on inline verification: every jar entry, `sha256`,
manifest attribute, and file-count figure quoted above was produced by a command run and read in this
session (not from memory), and every quoted source-file excerpt was read via `Read` at the cited line
range, not reconstructed from a `grep` snippet.

Artifacts: no scratch decompilation was performed this session (all cited `.java` files were
already present in the corpus's pre-existing `organized/` tree); working notes kept at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b95/`
(the `docDeveloper.jar`→`doc/modules.html` HTML-stripped scratch copy used for the `LIB-EXT`/`LIB-INF`
doc-text quote in §95.1 — scratch only, not archived in either repo).
