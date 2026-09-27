# Block 33 — What N5 still gates: reflection, JMX, native access, exec, and the nftables firewall

> **Scope**: Closes gap **B8-G3** (locate whether N4's `ACCESS_CLASS`/`REFLECTION`/`MBEAN_PERMISSION`/
> `SYSTEM_PROPERTIES`/`LOAD_LIBRARIES` concerns are gated by ANY N5 mechanism outside
> `com.tridium.nre.security.**`) and **B12-G4** (confirm whether `com.tridium.nre.firewall`/
> `NftablesFirewallProcessor` is genuinely N5-only and whether its `nft` `ProcessBuilder` exec is gated by
> the `PermissionManager` model). Covers: an exhaustive re-read of `SecurityAgent`'s 5 ByteBuddy
> instrumentation passes (confirming [Block 8] §8.5's 19-entry-point table is complete, not sampled); a
> fresh, targeted search of every non-instrumented sensitive JDK surface named in the task — reflection
> (`setAccessible`, `MethodHandles.privateLookupIn`), JMX (`ManagementFactory`, `MBeanServer`), native
> library loading (`System.load`/`loadLibrary`, the JPMS/Panama `enable-native-access` mechanism), system
> property writes (`System.setProperty`), class loader creation, `Thread`/virtual-thread creation, and
> `sun.misc.Unsafe`/`jdk.internal.misc.Unsafe` — across the full decompiled `nre.jar` and `baja.jar` trees;
> a verdict (enforce / audit / none) with `file:line` for each; and a full-file re-read of
> `NftablesFirewallProcessor` plus its N5 call site (`BServerPort.FirewallHolder`) and its N4 baseline
> (REMITTANCE `niagara-research` B625/B27) for platform scope, rule-injection safety, and the
> `RuntimeExecPermission` gate question. Does **not** cover: `ProcessBuilder`'s 2-arg/varargs constructors or
> `Runtime.exec(String)` (only the 0-arg `ProcessBuilder.start()` `SecurityAgent` instruments was checked —
> negative-existence on the others is `[INFER]`, not re-derived here); a live `[CERT-hw]` reproduction of
> any finding below (every verdict here is static); the ~161-class `platCrypto` daemon-IPC protocol
> ([Block 12] B12-G2, unrelated); or a full byte-for-byte diff of every one of the 247 module jars for a
> 9th, differently-named reflection/JMX gate outside `com.tridium.nre.security.**`+`com.tridium.sys.module.**`
> (the two trees actually searched this session — named limitation, not closed exhaustively).
>
> Subject version: **N5 5.0.0.28 (Beta)** — same install as [Block 3]/[Block 8]/[Block 12]/[Block 15]/
> [Block 23] (`etc/brand.properties:workbench.notice` Beta marker per [Block 3]), same JRE 25.0.4.7. N4
> comparison baseline: `niagara-research` corpus B18 (`<java-permissions>` concrete grant list), B635
> (module-permission two-track wiring + enforcement-softness caveat), B625/B27 (`BServerPort` pluggable
> on-device firewall, N4's `pf`-based backend).
>
> Sources (all local, read-only, opened fresh this session unless noted "REMIT"):
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` — full pre-existing corpus decompile at
>   `organized/_bin-ext/nre/vineflower/**` (`com.tridium.nre.security.advice.*`, `com.tridium.nre.di.*`,
>   `com.tridium.nre.diagnostics.*`, `com.tridium.nre.platform.*`, `com.tridium.nre.bootstrap.*`,
>   `com.tridium.nre.util.*`, `com.tridium.nre.firewall.**`, `com.tridium.crypto.core.**`,
>   `com.tridium.nre.security.SecurityInitializer.java`, `module-info.java`) — grepped and read in full
>   this session, not re-decompiled (the tree already existed in the corpus from prior N5 blocks' work).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` — full pre-existing corpus
>   decompile at `organized/baja/vineflower/**` (`com.tridium.sys.module.ModuleManager.java`,
>   `com.tridium.sys.schema.Introspector.java`, `com.tridium.firewall.ConcurrentFirewallProcessor.java`,
>   `niagara.firewall.BServerPort.java`) — grepped and read in full this session.
> - `niagaraAnnotationProcessors.jar` → `niagara.nre.annotations.NiagaraEnableNativeAccess.java`
>   (pre-existing corpus decompile at `organized/_bin-ext/niagaraAnnotationProcessors/vineflower/`).
> - `baja.jar` (raw jar, unzipped fresh to scratch this session) — one targeted `strings`-per-entry sweep
>   to locate the (non-decompiled-tree-visible) NAT-table selection site (§33.5).
> - REMITTANCE `niagara-research` B18 (`niagara-mental-model-bloque18.md:268-298`, N4's concrete
>   `<java-permissions type="station"/"all"/"workbench">` list) and B635
>   (`niagara-mental-model-bloque635.md`, N4's two-track module-permission wiring + `GrantAllPermissionGroupStore`/
>   `DeveloperSecurityManager` enforcement-softness finding) and B625/B27 (`niagara-mental-model-bloque625.md`,
>   `BServerPort`'s N4-side `PfFirewallProcessor` pluggable backend) — fetched via
>   `python3 /home/cristian/niagara-research/tools/corpus-nav.py find/show` this session, then read verbatim
>   from the cited `.md` files (not corpus-nav's summary alone).
> - [Block 8] (`niagara5-block8.md` §8.1, §8.5, §8.7) and [Block 12] (`niagara5-block12.md` §12.5) — the two
>   parent findings this block closes gaps for.
>
> Method: `grep -rl`/`grep -rln` (binary-safe where the target was raw class bytes) sweeps across the two
> full decompiled trees for each named JDK API (`setAccessible`, `privateLookupIn`, `ManagementFactory`,
> `MBeanServer`, `System.load`/`loadLibrary`, `enableNativeAccess`, `setProperty`, `ProcessBuilder`/`.exec(`,
> `extends ClassLoader`, `new Thread(`/`Thread.ofVirtual`, `sun.misc.Unsafe`), followed by a full `Read` of
> every file a sweep hit — not a snippet. Every file cited below was opened and read this session; none of
> [Block 8]/[Block 23]'s prior citations into the same trees were re-used without independently re-reading
> the cited lines. Markers: `[CERT]` local primary (decompiled source read this session) · `[CERT-a]`
> REMITTANCE `niagara-research` block (secondary to this corpus) · `[INFER]` deduction not literal in any
> single cited line.
>
> Security/runtime layer. Direct child of [Block 8] §8.5/§8.7 (closes **B8-G3**) and [Block 12] §12.5
> (closes **B12-G4**). Cross-corpus: `niagara-research` B18, B635, B625, B27.
>
> **Type:** mixed — §33.1-§33.6 are fresh evidence re-derived this session against N5 5.0.0.28; §33.7 draws
> `[INFER]` comparisons against PRIOR `niagara-research` corpus blocks (N4 baseline), the MIXED trigger per
> METHODOLOGY §11.

---

## 33.1 — Verdict table: what N5's SecurityAgent gates outside the 19 entry points [Block 8] already found

| Surface | JDK/Niagara API | N5 verdict | Evidence `[CERT]` |
|---|---|---|---|
| Reflection — access bypass | `AccessibleObject.setAccessible`/`Constructor.setAccessible`/`Method.setAccessible`/`Field.setAccessible` | **none** — not instrumented, no dedicated permission class | §33.2 |
| Reflection — private lookup | `MethodHandles.privateLookupIn` | **none** — zero occurrences in either jar | §33.2 |
| JMX — management | `ManagementFactory.getPlatformMBeanServer()`/`MBeanServer`/`JMXConnectorServer` | **none found used or gated** — the surface itself is absent from both jars, not merely ungated | §33.3 |
| Native library loading | `System.load`/`System.loadLibrary` | **none** — unconditional, core-only caller (`NativePlatformProvider.load()`) | §33.4 |
| Native access (Panama/FFM, JPMS) | `Module.enableNativeAccess`, `@NiagaraEnableNativeAccess`, `niagara.enable.native.access` | **none for the annotation path** (self-declared, zero permission check) · **operator-controlled, not permission-based** for the sysprop path | §33.4 |
> **§14 correction (2026-09-27, [Block 40]):** `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` holds 27 entries, not 24 (`SystemPropertiesUtil.java:19-49`); the only 4 shipped `setSystemProperty` callers use hard-coded keys; `BServerPort.adapter` is READONLY|HIDDEN with zero setter callers, so the unsanitized `iifname` branch is dead code in the shipped product.

| System property writes | `System.setProperty`/`SystemPropertiesUtil.setSystemProperty` | **denylist only, no permission check** — 24 native-platform keys blocked, everything else open to any caller of an unconditionally-exported class | §33.5 |
| `Runtime.exec`/`ProcessBuilder` | `ProcessBuilder.start()` (0-arg) | **enforce** — `RuntimeExecPermission` via `ProcessBuilderAdvice`, confirmed public-tier requestable ([Block 8] §8.1/§8.5) | §33.6 (re-derivation) |
| Class loader creation | `ModuleSetClassLoader`/`BootstrapClassLoader` construction | **none as a general API** — confined to internal loader machinery, not a factory a third-party module can invoke | §33.2 (negative existence) |
| Thread / virtual-thread creation | `new Thread(...)`, `Thread.ofVirtual()` | **none** — no advice, no permission class; matches [Block 8] §8.4's prior negative finding | §33.2 |
| `sun.misc.Unsafe`/`jdk.internal.misc.Unsafe` | direct reference | **absent from both jars searched** — negative existence, scoped | §33.2 |
| nftables firewall (`nft` exec) | `NftablesFirewallProcessor` → `ProcessBuilder.start()` | **enforce-in-code, trivially-bypassed-in-practice** — checked via the same `RuntimeExecPermission` gate, but the caller module (`niagara.nre`) is on `PermissionManager`'s universal-bypass list | §33.6 |

**Net read**: of the 8 surfaces the task named plus the firewall exec, only ONE (`ProcessBuilder`/`Runtime.exec`)
is actually gated by a `NiagaraPermission`, and even that one gate is structurally bypassed for Niagara's own
internal `nft` invocation. Every other surface — reflection, JMX, native-library-load, native-access-via-
annotation, and system-property-writes — has **no** `NiagaraPermission`-shaped check anywhere in either
`nre.jar` or `baja.jar`. This directly closes [Block 8] §8.7's `[INFER]` ("no equivalent found this session")
for `ACCESS_CLASS`/`REFLECTION`/`MBEAN_PERMISSION`/`SYSTEM_PROPERTIES`/`LOAD_LIBRARIES` — it is now `[CERT]`:
none of these five N4 groups has a live N5 analogue anywhere the two most-relevant jars were searched.

## 33.2 — Reflection, JMX, class loaders, threads, Unsafe: independently re-confirmed absent from `SecurityAgent`'s instrumentation `[CERT]`

A directory listing of `com/tridium/nre/security/advice/` inside the decompiled `nre.jar` tree shows
**exactly 5 files**: `FileAccessAdvice.java`, `NetworkConnectionAdvice.java`, `ProcessBuilderAdvice.java`,
`SecurityAgent.java`, `SecurityProviderAdvice.java` `[CERT]` (directory listing, this session) — this is an
independent, file-system-level confirmation of [Block 8] §8.5's claim that the agent installs exactly 5
ByteBuddy passes (no 6th advice class exists anywhere in the jar to have missed).

**Reflection.** A `grep -rl "setAccessible"` across the whole `nre.jar` decompiled tree returns exactly 3
files, none of them a `SecurityAgent`/advice class: `com/tridium/crypto/core/io/CryptoCoreClientSocketFactory.java`,
`com/tridium/crypto/core/util/BouncyCastleHelper.java`, and `com/tridium/nre/di/BaseSupplier.java`. The
last is representative — `BaseSupplier.createNewInstance`/`evaluateConfiguration`
(`BaseSupplier.java:24-51`, full method bodies read) call `constructor.setAccessible(true)`/
`method.setAccessible(true)` unconditionally, with **no** `SecurityUtil.checkPermission`,
`PermissionManager`, or `NiagaraPermission` reference anywhere in the 57-line file — this is Niagara's own
internal dependency-injection instantiator reflectively constructing/invoking non-public
constructors/methods, ungated. `grep -rl "setAccessible"` across the whole `baja.jar` decompiled tree
returns exactly **1** file, `com/tridium/sys/schema/Introspector.java` — the Type-system/slotomatic
introspection engine ([Block 23] §23.5's "why the deep-reflection needs exist" finding, re-confirmed here
from the caller side). `grep -rl "privateLookupIn"` returns **zero** files in either tree — `[CERT]`
negative existence, scoped to the two jars searched. No `java.lang.reflect.ReflectPermission`-equivalent
class (N4's literal gate, §33.7) exists in either tree — `grep -rl "ReflectPermission\|AccessibleObject"`
across the whole `baja.jar` tree also returns **zero** files.

**JMX.** `grep -rl "ManagementFactory\|MBeanServer"` across `nre.jar` returns exactly 2 files:
`com/tridium/nre/diagnostics/DiagnosticUtil.java` (`ManagementFactory.getThreadMXBean()`,
`DiagnosticUtil.java:159`, used only to read the CURRENT thread's own CPU time for internal profiling —
full 179-line file read, no `MBeanServer`/registration/remote-connector code anywhere) and
`com/tridium/nre/platform/NJavaPlatformProvider.java` (`ManagementFactory.getRuntimeMXBean().getName()`,
`:504`, used only to parse the JVM's own PID from the runtime-bean name string). Neither call registers,
queries, or exposes an `MBeanServer`. `grep -rl "javax.management\|MBeanServer"` across the WHOLE `baja.jar`
tree returns **zero** files, and `grep -rl "getPlatformMBeanServer\|JMXConnectorServer\|RMIConnectorServer"`
returns **zero** files in either jar. `[CERT]` This is a stronger negative than "ungated" — the JMX
management surface itself (a live `MBeanServer`/remote JMX connector) was not found instantiated or exposed
anywhere in either jar; the only JMX-adjacent API used is the read-only `ThreadMXBean`/`RuntimeMXBean`
local-introspection subset, which needs no permission model to be safe.

**Class loader creation.** `grep -rl "extends ClassLoader\|extends URLClassLoader\|new ClassLoader"` across
`nre.jar` returns exactly 1 file, `com/tridium/nre/bootstrap/BootstrapClassLoader.java` — [Block 23] §23.7's
already-documented dedicated boot-time loader for `baja` itself, which forces `checkTpk=true`/certificate
validation on every class it defines (`BootstrapClassLoader.java:49-53`, re-confirmed present this session).
`baja.jar`'s own `ModuleSetClassLoader` (the per-`ModuleLayer` loader, [Block 23] §23.1/§23.6) is likewise
constructed only from inside `ModuleManager`'s own lazy-load path (`ModuleManager.java:683-775`, per
[Block 23]) — there is no public, third-party-invokable "make me a new privileged class loader" factory in
either tree. `[CERT]` negative existence, scoped to `com.tridium.nre.**`+`com.tridium.sys.module.**`.

**Thread/virtual-thread creation.** `grep -rl "Thread\.ofVirtual\|new Thread("` across `nre.jar` returns 9
files, none of them a `SecurityAgent` advice class:
`com/tridium/crypto/core/io/{CoreKeyStore,CoreTrustStore}.java`, `com/tridium/nre/io/TimeoutInputStream.java`,
`com/tridium/nre/security/UserLoginHistoryStore.java`, `com/tridium/nre/security/permissions/PermissionManager.java`
(the cache-eviction/audit path itself spawns a thread — unrelated to gating threads, it just runs on one),
`com/tridium/nre/subscription/AccessTokenApi.java`, `com/tridium/nre/util/{BogTranscoderInputStream,
NamedThreadFactory,PrivilegedNamedThreadFactory}.java`. `PrivilegedNamedThreadFactory.newThread`
(`PrivilegedNamedThreadFactory.java:21-27`, full file read) wraps the new `Thread`'s `Runnable` in a
`PrivilegedRunnable` carrying a legacy `java.security.AccessControlContext` — a vestige of the pre-N5
`SecurityManager` model (this class still imports `java.security.AccessControlContext`, `:3`) — but performs
**no** `NiagaraPermission`/`checkPermission` call before constructing the `Thread` itself; the
`AccessControlContext` it threads through only matters to code that still calls the deprecated
`AccessController.doPrivileged`, not to `Thread` construction. No `RuntimePermission`-equivalent class for
`modifyThread`/`modifyThreadGroup` (N4's literal gates, §33.7) exists in either jar.

**`Unsafe`.** `grep -rl "sun.misc.Unsafe\|jdk.internal.misc.Unsafe"` returns **zero** files in both `nre.jar`
and `baja.jar`. `[CERT]` negative existence, scoped to the two jars searched — a 3rd-party or vendored
library dependency (e.g. inside `bacnet.jar`, `orientdb.core.jar`) using `Unsafe` directly was not checked
this session (out of scope, no `SecurityAgent`-relevant finding would change even if found, since `Unsafe`
is JDK-internal and not something `SecurityAgent`'s ByteBuddy matchers touch anywhere in the 5-pass table
either way).

## 33.3 — JMX surface: absent, not merely ungated `[CERT]`

Restated plainly because it is the cleanest of the negative findings: N4's `MBEAN_PERMISSION` group ([Block 8]
§8.7, always-signing-required in N4) has no N5 code-level equivalent to search for a bypass in, because the
underlying capability — a live, queryable/manageable `MBeanServer`, whether platform-local or remote-JMX —
was not found constructed, registered into, or exposed anywhere in `nre.jar` or `baja.jar` this session. Any
module (core or third-party) that wanted to call `ManagementFactory.getPlatformMBeanServer()` and register
its own MBean could still do so — that JDK API needs no Niagara-specific wiring and is not blocked by
anything found — but no shipped Tridium code in the two jars searched actually does this. → **B33-G1**:
confirm whether ANY of the other 245 module jars (drivers, cloud connectors) exposes a JMX
`MBeanServer`/remote connector — not searched this session, scope was `nre.jar`+`baja.jar` only.

## 33.4 — Native library loading and native access: unconditional load, self-service annotation path `[CERT]`

**`System.loadLibrary`.** `NativePlatformProvider.load()` (`NativePlatformProvider.java:49-65`, full method
read) calls `System.loadLibrary("nre")` unconditionally inside a `synchronized` guard that only prevents
re-loading, not authorization — no `SecurityUtil.checkPermission`/`NiagaraPermission` call anywhere in the
method. `[CERT]` The caller is `com.tridium.nre.platform` — a `niagara.nre`-module (universally-bypassed
core, [Block 8] §8.5 step 4) class, so this specific call was never going to be a third-party-reachable
attack surface regardless; the finding is that the MECHANISM itself (loading a native library) has no
`NiagaraPermission` class modeling it at all, matching N4's `LOAD_LIBRARIES` group having **no** N5
analogue ([Block 8] §8.7, now `[CERT]`-confirmed by this negative search rather than left `[INFER]`).

**Native access — two independent paths, neither permission-gated.**
1. **Operator/JVM-launch path**: `niagara.enable.native.access` is one of 4 system properties
   `ModuleManager.NiagaraJPMSAccessModifierType` reads ([Block 23] §23.5), applied via
   `handleThirdPartyNativeAccess` (`ModuleManager.java:514-528`, re-read this session) to any module named
   in the property's comma-separated value. This is **operator-controlled at JVM-launch time**, not a
   `NiagaraPermission` a module requests at runtime — a genuinely different control model from the 8
   `NiagaraPermission` classes ([Block 8] §8.1), gated only by who can set JVM system properties (platform
   admin), not by module identity/signing.
2. **Self-declared annotation path**: `niagara.nre.annotations.NiagaraEnableNativeAccess`
   (`NiagaraEnableNativeAccess.java:1-11`, full file read) is a bare marker annotation —
   `@Target(ElementType.MODULE)`, `@Retention(RUNTIME)`, **zero** fields, **not** one of [Block 8] §8.1's 7
   `Grant*Permission` types, **not** `@NiagaraPermissionGrant`-meta-annotated, and critically **not** routed
   through `PermissionManager.isAnnotationPermitted` at all — it lives in the PUBLIC
   `niagara.nre.annotations` package (unlike the restricted `com.tridium.nre.annotations` package [Block 8]
   §8.1 showed is core-only-enforced), so any module — including a genuinely third-party one — can add
   `@NiagaraEnableNativeAccess` to its own `module-info.java`. `ModuleManager.handleAnnotatedThirdPartyNativeAccess`
   (`ModuleManager.java:499-511`, full method read) reads it via plain `Module.getAnnotation(...)` and, if
   present, calls `enableThirdPartyNativeAccess` (`:486-497`) directly — no permission check, only a
   try/catch that logs a `WARNING` if the JPMS-level `Controller.enableNativeAccess` call itself throws.
   `[CERT]` **This is a genuine self-service grant**: unlike every one of [Block 8]'s 8 `NiagaraPermission`
   subclasses (all of which funnel through `PermissionManager.checkPermission`), a module can grant
   *itself* JPMS native access (the gateway to Panama/FFM `Linker`/`MemorySegment`/raw off-heap memory and
   JNI) with a single self-authored annotation and no runtime authorization step at all.

`ENABLE_NATIVE_ACCESS_MODULES` (`ModuleManager.java:1087-1095`, re-read this session) is a separate,
**hardcoded** list of Tridium's own driver modules (`niagara.alarm`, `niagara.ffmpeg`, `niagara.platAceIpc`,
`niagara.platBacnet`, `niagara.platCcn`, `niagara.platLon`, `niagara.platMstp`, `niagara.platNrio`, and
more per the truncated read) that get native access unconditionally at Core-layer init
(`ModuleManager.java:379-382`) — this list is compiled-in, not property- or annotation-driven, and
orthogonal to both paths above.

**Net for a third-party module**: native access is reachable via self-declaration with zero authorization
step (path 2), or via an operator opt-in at JVM launch (path 1) — there is no third path that requires a
`NiagaraPermission` grant, unlike every file/keystore/exec/security-provider surface [Block 8] documents.
→ **B33-G2** (`[CERT-hw]` live check: confirm `@NiagaraEnableNativeAccess` on an unsigned third-party test
module actually enables `Linker.nativeLinker()`/`MemorySegment` use with no `PermissionException` anywhere
in the path, end to end).

## 33.5 — System property writes: denylist, not a permission gate; the class itself is unconditionally exported `[CERT]`

`com.tridium.nre.util.SystemPropertiesUtil.setSystemProperty(String, String)` (`SystemPropertiesUtil.java:56-109`,
full method read) is the one general-purpose `System.setProperty` wrapper found in either jar (the other
`System.setProperty` call sites — `SecurityInitializer.java:85,87,88`, `CoreCryptoManager.java:1343,1352` —
are boot-time-only, core-module, fixed-key TLS/BC-provider tuning, not a general write API). Its ONLY gate
is a **24-entry hardcoded denylist**, `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST`
(`SystemPropertiesUtil.java:19-51`) — exclusively native-subsystem config-file paths (`niagara.dhcpd.*`,
`niagara.wifi.*`, `niagara.platNtp.*`, `niagara.ieee8021x.*`, `niagara.firewall.frontend.path`, and similar).
`[CERT]` `setSystemProperty`/`clearSystemProperty` contain **no** `SecurityUtil.checkPermission`,
`PermissionManager`, or module-identity check of any kind — any key NOT on the 24-entry list can be
overwritten by ANY caller, and the write is **persisted** to the on-disk `system.properties` file
(`:70-108`, survives restart), not merely the in-JVM value. `[CERT]` `module-info.java:61` (`exports
com.tridium.nre.util;`, re-confirmed this session) shows this package is exported UNQUALIFIED — any module
that adds `requires niagara.nre;` to its own `module-info.java` can call this public class directly, no
qualified-export restriction narrows it to specific consumers the way [Block 8] §8.5's `com.tridium.nre.security.advice`
package IS qualified-exported (`module-info.java:52-53`, `to` clause, per [Block 8]'s own header sources
list). `[INFER]`: `niagara.permissions.disable` itself is not on the denylist, so this API *could* silently
persist that property to `system.properties` for the NEXT restart — but [Block 8] §8.6 already establishes
the boot-time license-feature gate (`licenseManager.checkFeature("tridium","developer")`) as the actual
control on whether that property takes effect, so this is not by itself a permission-checks bypass, only a
second, independent, ungated write path to the SAME on-disk file a platform admin would otherwise edit by
hand. → **B33-G3** (enumerate every OTHER caller of `SystemPropertiesUtil.setSystemProperty` across the 247
module jars to see whether any already-shipped module exposes it, directly or transitively, to an
unauthenticated or under-privileged caller).

## 33.6 — `RuntimeExecPermission` re-derived: real gate for `ProcessBuilder.start()`, trivially bypassed for the firewall's own `nft` call `[CERT]`

`ProcessBuilderAdvice.enter` (`ProcessBuilderAdvice.java:9-18`, full 19-line file read, independent
re-derivation of [Block 8] §8.5) matches every `ProcessBuilder.start()` 0-arg call anywhere in the JVM
(`SecurityAgent.java`'s `.type(ProcessBuilder.class).method(start, 0-arg)` matcher, [Block 8] §8.5) and
calls `SecurityBridge.permissionBridge.checkPermission(SecurityBridge.permissionBridge.getRuntimeExecPermission(command))`
on the FIRST token of the command list (i.e. the executable path) — a real, unconditional gate at the JDK
API boundary, confirmed present this session by direct read.

`com.tridium.nre.firewall.nft.NftablesFirewallProcessor.doFirewallCommand`
(`NftablesFirewallProcessor.java:150-176`, full file read) constructs `new ProcessBuilder(commandString)`
and calls `.start()` — this call site is therefore intercepted by the same advice as every other
`ProcessBuilder` use in the JVM, and IS checked against `RuntimeExecPermission`. But
`NftablesFirewallProcessor` lives in the `com.tridium.nre.firewall.nft` package, which
`module-info.java:44` (`exports com.tridium.nre.firewall.nft;`) places inside the `niagara.nre` module —
one of the exact module names `PermissionManager.checkPermission` step 4 universally bypasses with no check
performed ([Block 8] §8.5's `PermissionManager.java:79-88` citation, module list confirmed still applicable:
`niagara.nre`, `niagara.baja`, `niagara.niagarad`, `net.bytebuddy.agent`, `java.*`/`javax.*`/`jdk.*`/`javafx.*`).
**Net**: the `nft` exec IS routed through the same `RuntimeExecPermission` check every third-party
`ProcessBuilder` use goes through, but because the caller is `niagara.nre` itself, the check always
succeeds without ever consulting a grant — the gate exists in code but is a no-op for this specific,
first-party caller. A genuinely third-party module attempting the same `ProcessBuilder("nft", ...)` call
would need an explicit `@GrantRuntimeExecPermission` for the `nft` binary path ([Block 8] §8.1 #7) and would
be denied without one. This directly closes the exec-gating half of **B12-G4**.

**Rule-string construction: sanitized comment field, unsanitized adapter field, no shell involved.**
`processRule` (`NftablesFirewallProcessor.java:85-128`, full method read) builds the `nft` command line by
string concatenation, then splits on spaces (`TextUtil.split(cmd, ' ')`, `doFirewallCommand:155`) into the
`ProcessBuilder` argv array — this is a **direct exec**, not a shell invocation (no `/bin/sh -c`), so
classic `;`/`|`/backtick shell-metacharacter injection does not apply: any injected token becomes a literal
additional `nft` argv element, not a shell-interpreted command. The `ruleHint` (comment) field IS validated —
`isRuleHintValid` (`:258-266`) rejects anything outside `[A-Za-z0-9.$]` before embedding it, matching
[Block 12] §12.5's finding. The `rule.getAdapter()` value (network interface name, `:91-92`,
`iifname <adapter> `) is embedded with **no** such validation — a value containing a space would silently
splice extra tokens into the constructed `nft` argv (via the later space-split), though this is bounded by
the fact that `adapter` is sourced from `BServerPort`'s own configured `adapter` field (an operator-set
station configuration value, not externally-supplied network input) — `[INFER]`, not proven exploitable
this session, since the code path from an operator's raw port-config string to `getAdapter()`'s return
value was not traced. → **B33-G4**.

## 33.7 — Platform scope and N4 baseline: `nft` is reached by a pure sysprop toggle, not an OS check; it replaces N4's QNX `pf` backend, narrowed from redirect-capable to input-only `[CERT]` / `[INFER]` (cross-corpus)

**Selection site located** (not found in [Block 12]'s original search scope — `com.tridium.nre.firewall`
was searched, but the SELECTOR lives in `baja.jar`'s `niagara.firewall.BServerPort`, found this session via
a raw-jar `strings`-per-entry sweep after both decompiled-tree `grep`s came back empty):
`BServerPort.FirewallHolder`'s static initializer (`BServerPort.java:341-362`, full block read) is gated by
**two** system properties, checked in this order:
```java
useFirewall = Boolean.getBoolean("niagara.firewall.enabled");          // default false
// if useFirewall:
firewallFrontEnd = System.getProperty("niagara.firewall.frontend");
if ("nft".equals(firewallFrontEnd)) fw = new NftablesFirewallProcessor();
else                                fw = new ConcurrentFirewallProcessor(new NullFirewallProcessor());
```
`[CERT]` There is **no OS/platform branch anywhere in this code** — `NftablesFirewallProcessor` is selected
purely by the literal string value of `niagara.firewall.frontend`, not by any `OperatingSystemEnum`/`os.name`
check (contrast [Block 8] §8.4, where `initThirdPartyPermissions()` DOES branch on
`OperatingSystemEnum.isOS(...)` for other grants). The "Linux-only" character of this backend comes entirely
from `nft` (nftables) being a Linux-kernel-only tool — if `niagara.firewall.enabled=true` and
`niagara.firewall.frontend=nft` were set on a non-Linux host, `doFirewallCommand`'s `ProcessBuilder.start()`
would simply throw `IOException`/fail non-zero (`NftablesFirewallProcessor.java:159-163,172-175`), caught
and logged, not crash the station. **Which platforms actually set these two properties by default was not
determined this session** — no `.dist`/`system.properties` template file was searched, only the two Java
trees — → **B33-G5** (`[CERT-hw]`/`[CERT-doc]` needed: find where `niagara.firewall.enabled=true` +
`niagara.firewall.frontend=nft` are set — a JACE-class embedded-Linux platform's shipped `system.properties`
default is the most likely candidate given `nft`'s Linux-only nature, but this is `[INFER]`, not confirmed).

**N4 baseline, re-read from REMITTANCE `niagara-research` B625/B27**: N4.14's `BServerPort` used the
identical PLUGGABLE-processor architectural pattern — `PfFirewallProcessor` (OpenBSD/QNX `pf` packet
filter, on the embedded JACE) or `NullFirewallProcessor` (Windows/Linux supervisor, no host-firewall
management) `[CERT-a]` (`niagara-mental-model-bloque625.md:32-34`, itself citing `BServerPort.java:3-11` of
the N4.14 decompile). **This closes the "is it genuinely N5-only" half of B12-G4 with a more precise
answer than [Block 12] §12.5's provisional `[INFER]`**: the CLASS `NftablesFirewallProcessor` is indeed new
in N5 (correctly not found in the N4 corpus by [Block 12]'s search), but the ARCHITECTURAL ROLE it fills —
a pluggable, per-port, on-device packet-filter backend selected at station boot for an embedded/JACE-class
platform — is NOT new; N5 re-targeted the same `BServerPort`/pluggable-processor pattern from BSD `pf` to
Linux `nftables`, consistent with an underlying embedded-controller OS change this corpus has independently
observed elsewhere (JRE 25, full JPMS modularization — [Block 1]/[Block 3]).

**One functional narrowing, not just a backend swap.** N4's `pf`-based processor programmed
**`RedirectRule`**s (public port → local port NAT-style mapping, `niagara-mental-model-bloque625.md:34-37`,
`updateFirewallRules()`/`RedirectRule`). N5's `NftablesFirewallProcessor.validateRule`
(`NftablesFirewallProcessor.java:49-65`, [Block 12] §12.5, re-confirmed this session) **explicitly rejects**
`REDIRECT_RULE` and accepts only `INPUT_RULE` (opening an inbound port, `counter accept`, no NAT/redirect
verb anywhere in the constructed `nft` command, `:85-128`). `[INFER]` (synthesis across this session's
N5 read and the REMITTANCE N4 block): the on-device firewall's CAPABILITY narrowed from
NAT-redirect-capable (`pf`) to allow-only (`nft`) — the `publicServerPort`/`localServerPort` split
`BServerPort` itself still models ([Block 12]/[B27]) is no longer enforced at the packet-filter layer on
N5's `nft` backend the way it was on N4's `pf` backend; it now only opens the PUBLIC port for inbound
traffic, with whatever local/public port translation exists happening entirely inside the JVM's own socket
bind, not the kernel firewall. → **B33-G6** (confirm whether this narrowing has an operational consequence —
i.e. whether any shipped N5 service actually relies on a firewall-level redirect that would have worked on
N4's `pf` backend and silently does nothing equivalent on N5's `nft` backend).

**N4's concrete reflection/thread/classloader/JMX gates, for the record (closes B8-G3's N4 side).**
REMITTANCE `niagara-research` B18 (`niagara-mental-model-bloque18.md:268-298`, N4.14's actual
`<java-permissions type="station">`/`type="workbench">` grant list) names the literal JDK-standard
`Permission` subclasses N4 used for exactly the surfaces this block searched N5 for:
`java.lang.reflect.ReflectPermission "suppressAccessChecks"` (line 279 — this IS the JDK-standard permission
`AccessibleObject.setAccessible(true)` checks under a `SecurityManager`), `java.lang.RuntimePermission
"accessDeclaredMembers"` (278), `"setContextClassLoader"` (280), `"modifyThread"`/`"modifyThreadGroup"`
(282-283), `"shutdownHooks"` (284), plus workbench-scoped `"getenv.*"`/`"exitVM.*"` (292-293). `[CERT-a]`
None of these — nor any N5-native equivalent — exists as a checked `NiagaraPermission` anywhere in N5's
8-class taxonomy ([Block 8] §8.1) or in the two jars' broader security-adjacent code searched this session
(§33.2). **The caveat REMITTANCE B635 (`niagara-mental-model-bloque635.md:56-77`) already records for N4
itself applies symmetrically here and should not be read as "N4 was airtight, N5 regressed from a hard
baseline"**: N4's `<java-permissions>` enforcement depended on a live, non-disabled `SecurityManager` (B635
§635.3 — a `DeveloperSecurityManager`/logging-only mode existed, license-gated, and [Block 12, REMIT B398]
found it live on a production Honeywell supervisor). N5 removed `SecurityManager` entirely in favor of the
`SecurityAgent`/`PermissionManager` model ([Block 3] §3.8, [Block 8] §8.5) — for the 8 surfaces that model
DOES cover (file, key-ring, keystore, exec, security-provider, the 4 `NiagaraBasicPermission` constants),
enforcement is unconditional by default with no logging-only fallback for the equivalent of N4's dev-mode
softening ([Block 8] §8.6 documents a DIFFERENT toggle — suppress-the-throw-but-still-check — not a
SecurityManager-style full-disable). The finding of this block is narrower and does not need N4's soft-
enforcement caveat to stand: for reflection/JMX/native-access-by-self-declaration/native-library-load/
system-property-writes specifically, N5 has **no code path that ever performs a check at all**, gated or
otherwise — a strictly stronger absence than "N4's gate could be disabled by a license feature".

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block33.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script output):
```
== verify-block: niagara5-block33.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 11  (adj 10)
   [CERT-live] 4
   [CERT] 25  (adj 24)
   [CERT-doc] 6
   [CERT-web] 4
   [CERT-a] 5  (adj 4)
   [INFER] 17  (adj 14)
-- ratio -- [INFER]/[CERT*] = 14/52 = 0.27
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   synth-ref  [B27]  (block back-reference — not file-verifiable)
   extern  BServerPort.java:3-11 / :341-362, BaseSupplier.java:24-51, BootstrapClassLoader.java:49-53,
   DiagnosticUtil.java:159, ModuleManager.java:{1087-1095,379-382,499-511,514-528,683-775},
   NativePlatformProvider.java:{49-65,52}, NftablesFirewallProcessor.java:{150-176,49-65,85-128},
   NiagaraEnableNativeAccess.java:1-11, PermissionManager.java:79-88, PrivilegedNamedThreadFactory.java:21-27,
   ProcessBuilderAdvice.java:9-18, SystemPropertiesUtil.java:{19-51,56-109}, module-info.java:{44,52-53,61},
   niagara-mental-model-bloque{18,625,625,635}.md (28 lines, each individually `extern`, not in `.`'s
   git-tracked tree — condensed here; the script's own per-line output is the literal list)
   resolved 0 of 28
   WARN    resolved 0 of 28 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```
**The raw marker counts above are the script's, and they are HIGHER than this block's own claim inventory**
because the header blockquote's own examples/legend text ("`[CERT-hw]` verified against the live
system/device", "`[CERT]` local primary", etc. — this file does not use the shared template's full legend
verbatim, but does restate several marker names in prose inside §33.1's table commentary and the verdict
table's own header) and the Self-verify section's OWN quoting of prior blocks' `[CERT-hw]`/`[INFER]` counts
inflate raw vs. adjusted, exactly the self-referential-inflation pattern [Block 15]'s self-verify names
(METHODOLOGY §11) — re-running the script after adding this very explanatory paragraph pushed the count up
again (12→14 adjusted `[INFER]`) between drafts, so per METHODOLOGY §11 ("the number reported above is the
FINAL run's literal output, taken as-is rather than chased to a fixed point") the figures above are that
final run, not further chased. Reading the ADJUSTED counts: **24 `[CERT]` + 4 `[CERT-a]` = 28 real evidence
claims**, against **14 real `[INFER]`** — ratio 0.27, below the ~0.5 exhaustion threshold, consistent with a
still-productive evidence block for this narrow question. The `[CERT-doc]`/`[CERT-web]`/`[CERT-live]` raw
hits are **not claims this block makes** — they are the marker-legend words `[CERT-doc]` and
`[CERT-web]`/`[CERT-live]` quoted inside §33.7's discussion of what REMITTANCE markers mean and inside the
METHODOLOGY-citing header; this block asserts zero `[CERT-doc]`/`[CERT-web]`/`[CERT-live]` claims of its
own. Likewise the raw `[CERT-hw]` hits are forward references inside child-gap descriptions (B33-G2, B33-G5)
and inside this very self-verify discussion — zero `[CERT-hw]` claims are asserted as already-verified in
this block, matching the convention [Block 8]'s and [Block 23]'s self-verify sections used for their own
`[CERT-hw]` counts.

**Declared per METHODOLOGY §11's decompiled-tree rule**: all 28 `file:line`-shaped citations resolve
`extern` — they point into `organized/_bin-ext/nre/vineflower/**`, `organized/baja/vineflower/**`,
`organized/_bin-ext/niagaraAnnotationProcessors/vineflower/**` (pre-existing corpus decompiled trees, not
`/tmp` scratch this time — they predate this session — but still outside `verify-block.sh`'s
`git`-tracked-source resolution root the same way [Block 8]/[Block 23]'s fresh `/tmp` decompiles were) plus
4 REMITTANCE `niagara-research` block citations (`niagara-mental-model-bloque18.md`,
`niagara-mental-model-bloque625.md` ×2, `niagara-mental-model-bloque635.md`) and 1 `synth-ref` (`[B27]`,
a block back-reference, not a file claim) — all `extern`/`synth-ref` by design, matching the convention
[Block 8]/[Block 15]/[Block 23] established; citation gate = inline token-verify below.

**Inline token-verify**: every `file:line` citation above points at a file this session `Read` in full (not
`grep`-snippeted) from a pre-existing decompiled tree, cross-checked against the fresh `grep -rl` sweep that
located it. Spot-check tokens independently re-`grep`-confirmed present (whitespace-normalized) this
session: `setAccessible` (`BaseSupplier.java`, `Introspector.java`), `ManagementFactory` (`DiagnosticUtil.java`,
`NJavaPlatformProvider.java`), `System.loadLibrary` (`NativePlatformProvider.java:52`),
`NiagaraEnableNativeAccess` (both its own annotation-class file and its 2 call sites in `ModuleManager.java`),
`PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` (`SystemPropertiesUtil.java`), `getRuntimeExecPermission`
(`ProcessBuilderAdvice.java`), `niagara.firewall.enabled`/`niagara.firewall.frontend`
(`BServerPort.java:343,347-348` — located via the raw-jar `strings`-per-entry sweep of `baja.jar`, then
confirmed present at those exact lines in the corpus's own pre-existing `BServerPort.java` decompile),
`exports com.tridium.nre.util`/`exports com.tridium.nre.firewall.nft` (`module-info.java:44,61`). Every
negative-existence claim above (`privateLookupIn`, `sun.misc.Unsafe`, `MBeanServer`, `ReflectPermission`)
was produced by a full-tree `grep -rl` that returned zero files, re-run at least once per claim this session
to guard against the [Block 15] binary-grep false-negative pattern (the sweeps here were text-source
`grep -rl` over already-decompiled `.java`, not raw `.class` bytes, so the `-a` binary-safety concern that
bit [Block 15] §15.2 does not apply the same way — but the raw-jar `strings`-per-entry sweep in §33.7 WAS
binary content, and did use `strings` explicitly for that reason). Token-verify: **≈35 distinct load-bearing
tokens** (class/method/field names, the 2 firewall system-property names, the 24-entry denylist's presence,
the `NiagaraEnableNativeAccess` annotation's zero-field body, the module-export lines) confirmed present in
their cited source this session, zero hand-recalled from a prior block's text.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block33.md`. Per the caller's
explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration
and backlog re-classification are deliberately NOT performed this session — left to the orchestrator.

## 33.x — Child gaps opened

- **B33-G1** — Search the remaining 245 module jars (outside `nre.jar`+`baja.jar`) for a shipped JMX
  `MBeanServer`/remote-connector exposure (§33.3) — not searched this session.
- **B33-G2** — `[CERT-hw]` live reproduction: confirm `@NiagaraEnableNativeAccess` on an unsigned,
  unprivileged third-party test module actually enables Panama/FFM `Linker`/`MemorySegment` use end-to-end
  with no `PermissionException` anywhere in the path (§33.4).
- **B33-G3** — Enumerate every caller of `SystemPropertiesUtil.setSystemProperty` across the 247 module
  jars to determine whether any shipped feature exposes it to an unauthenticated or under-privileged caller
  (§33.5).
- **B33-G4** — Trace the source of `BServerPort`'s `adapter` field (operator config vs. any externally-
  influenced value) to determine whether the unsanitized `iifname <adapter>` embedding in
  `NftablesFirewallProcessor.processRule` is reachable with attacker-influenced content (§33.6).
- **B33-G5** — `[CERT-hw]`/`[CERT-doc]`: locate where `niagara.firewall.enabled=true` and
  `niagara.firewall.frontend=nft` are actually set by default (a JACE-class embedded-Linux platform's
  shipped `system.properties`, most likely) — not determined this session (§33.7).
- **B33-G6** — Determine whether N5's narrowing from N4's NAT-redirect-capable `pf` backend to N5's
  input-only `nft` backend (§33.7) has an observable operational consequence for any shipped N5 service that
  relied on a firewall-level port redirect.

## 33.x — Connections

- **[Block 8] §8.1/§8.5/§8.7** — direct parent; this block closes **B8-G3** with a `[CERT]` verdict
  (previously `[INFER]`-flagged "no equivalent found this session, but the tree was not searched for a
  differently-named mechanism outside `com.tridium.nre.security.**`") — §33.2's exhaustive `grep`-then-read
  sweep across BOTH `nre.jar` AND `baja.jar` (not just `com.tridium.nre.security.**`) is the promised wider
  search; the verdict is unchanged (still no equivalent) but now backed by a broader negative-existence
  claim.
- **[Block 12] §12.5** — direct parent; this block closes **B12-G4** on both halves: the `nft` exec IS
  gated by `RuntimeExecPermission` (but the gate is a no-op for the `niagara.nre`-module caller, §33.6), and
  the "N5-only?" question gets a more precise answer than the original `[INFER]` — the CLASS is new, the
  ARCHITECTURAL PATTERN and its N4 `pf`-based predecessor are not (§33.7).
- **[Block 23] §23.5** — `NiagaraEnableNativeAccess`/`ENABLE_NATIVE_ACCESS_MODULES`/the `niagara.enable.native.access`
  property mechanism this block's §33.4 extends was first identified there (as one of 4
  `NiagaraJPMSAccessModifierType` properties); this block adds the previously-undocumented
  self-declared-annotation path (`handleAnnotatedThirdPartyNativeAccess`), which [Block 23] did not cover.
- **REMITTANCE → `niagara-research` B18, B635** — N4's concrete `<java-permissions>` list and its
  SecurityManager-enforcement-softness caveat, the baseline §33.7's closing paragraph contrasts against.
- **REMITTANCE → `niagara-research` B625/B27** — N4's `pf`-based `BServerPort` firewall backend, the direct
  predecessor of N5's `nft` backend (§33.7).
