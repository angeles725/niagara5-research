# Block 65 — Opening `SecurityAgent`/`SecurityProviderAdvice` directly: the full ByteBuddy interception map, the `Module`-keyed enforcement chain (never `AccessControlContext`/`Subject`), and a new finding — the platform daemon runs with the whole advice layer permanently inert via `PermissionUtil.isTrustedDomain`

> Research closing **B54-G3**: read `niagara.nre.security.advice.SecurityAgent` and
> `SecurityProviderAdvice` directly — the two classes [Block 3] §3.8 named (by class name and `javap`
> signature only, via REMIT) as N5's ByteBuddy-agent replacement for the removed JDK `SecurityManager`, and
> [Block 54] §54.5 relied on (also by REMIT, "[Block 3]'s independently-established... finding, not
> re-derived") to declare 25 `AccessController`-family call sites "architecturally inert" — without either
> block having opened the agent/advice source itself. This session opens all five `advice.*` classes
> (`SecurityAgent`, `SecurityProviderAdvice`, `FileAccessAdvice`, `NetworkConnectionAdvice`,
> `ProcessBuilderAdvice`) plus their full runtime dependency chain (`securityBridge.jar`'s 2-class shim,
> `PermissionBridge`, `SecurityUtil.checkPermission`, `PermissionManager.checkPermission`,
> `NiagaraPermission`) to answer B54-G3's exact two questions: (1) **what does the agent actually
> intercept** — the full JDK type/method interception map, not merely the four category names [Block 3]
> §3.8's table gave; (2) **does the advice layer itself ever consult an `AccessControlContext`/`Subject` for
> a real decision** — a possibility [Block 54] §54.5 explicitly left unruled-out ("the advice classes
> intercept calls *before* they reach `AccessController`, a different mechanism than what this block
> traced"). Both are answered directly from source this session. A third, unplanned finding surfaced while
> tracing the enforcement chain to its root: `com.tridium.niagarad.NiagaraDaemon.Main()` sets
> `PermissionUtil.isTrustedDomain = true` **unconditionally**, as literally its first security-relevant
> statement — and this flag is the ONE gate that decides whether `SecurityBridge.permissionBridge` (the
> field every advice class's `if (SecurityBridge.isInitialized())` guard tests) is ever wired up at all.
>
> Does **not** cover: `FilePermission`/`RuntimeExecPermission`'s own `doIsGrantedTo()` decision logic
> (path-prefix matching against `modulePermissions`'s per-module grant table) — the classes were opened for
> their `NiagaraPermission` shape and construction sites, not their full grant-matching algorithm bodies;
> the 18-entry `isInstalledProvider()`/4-entry `isFileSystemProvider()` matcher lists' own rationale beyond
> what they visibly match; a live/dynamic confirmation that an intercepted call in a running station actually
> throws `PermissionException` (no runnable N5 station this session, same blocker as [Block 41]'s
> **B41-G4**/[Block 49]'s **B49-G1**/[Block 54]'s **B54-G2**); whether `securityBridge.jar` is empirically
> loaded via `-Xbootclasspath/a:` as [Block 3] §3.8 `[INFER]`'d (this session decompiles and reads its 2
> classes' CONTENT, confirming the shape [Block 3] predicted, but does not test the loading mechanism
> itself); and whether `niagarad`'s own JVM invocation is actually launched with `-javaagent:nre.jar` (a
> native launch-flag fact outside decompiled-source scope, the same limitation class as [Block 54]'s
> **B54-G1** and [Block 61]'s **B61-G1** — flagged in §65.3, not silently assumed).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as every predecessor block
> (`etc/brand.properties:workbench.notice`). No fresh decompilation — every file cited was already present
> in this corpus's `organized/` tree from prior sessions ([Block 1]'s corpus-wide extraction for `nre.jar`
> and `niagarad.jar`; [Block 25]/[Block 44]'s `bin/ext` extraction established the `_bin-ext/nre` and
> `_bin-ext/niagarad` locations); `organized/_bin-ext/securityBridge/` (the `securityBridge.jar` shim) was
> also already present in-corpus, extracted but never opened before this session ([Block 3] §3.8 named it
> `[INFER]` and explicitly deferred decompiling it — **B3-G5**).
>
> Sources: `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/advice/{SecurityAgent,
> SecurityProviderAdvice,FileAccessAdvice,NetworkConnectionAdvice,ProcessBuilderAdvice}.java` (all 5 whole
> files, the task's literal target plus the 3 sibling advice classes `SecurityAgent.premain()` wires up,
> read for completeness of the interception map); `organized/_bin-ext/securityBridge/vineflower/com/tridium/
> securityBridge/{SecurityBridge,IPermissionBridge}.java` (both whole files, 9 and 13 lines — first read of
> this jar in the corpus, closing the content half of **B3-G5**); `organized/_bin-ext/nre/vineflower/com/
> tridium/nre/security/permissions/{PermissionBridge,PermissionManager}.java` (whole files, `PermissionBridge`
> re-read from [Block 54]'s citation list, `PermissionManager` re-read whole — [Block 54] cited only
> `:95-140`, this session reads all 428 lines including `initThirdPartyPermissions()` and the module-identity
> short-circuit list); `organized/_bin-ext/nre/vineflower/niagara/nre/util/SecurityUtil.java:230-238,
> 322-333` (`checkPermission`/`consumePrivilegedModules`, re-opened from [Block 54]'s whole-file citation,
> new targeted range this session); `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/
> NiagaraPermission.java` (whole 40-line file); `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/
> permissions/restricted/PermissionUtil.java` (whole 11-line file); `organized/_bin-ext/nre/vineflower/com/
> tridium/nre/bootstrap/Bootstrap.java:228-238` (the `SecurityBridge.permissionBridge = new PermissionBridge()`
> assignment site, targeted read); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/
> NiagaraDaemon.java:195-198` (`Main()` head, targeted read); `organized/_bin-ext/nre/vineflower/META-INF/
> MANIFEST.MF:1-8` (`Premain-Class` line, re-confirmed this session); `organized/_bin-ext/niagarad/
> vineflower/META-INF/MANIFEST.MF` (confirms no `Premain-Class` of its own); `organized/_bin-ext/niagarad/
> vineflower/module-info.java` (whole file — `requires transitive niagara.nre`); `organized/_bin-ext/nre/
> vineflower/module-info.java:1` (`module niagara.nre` declaration, cross-check); `organized/_bin-ext/
> securityBridge/vineflower/module-info.java` (whole 3-line file); `organized/_bin-ext/nre/vineflower/com/
> tridium/nre/security/permissions/FilePermission.java:1-60` (class header + field block only, partial read
> — named but not fully traced, see scope note above). Whole-tree `grep -rn` this session for
> `SecurityBridge.permissionBridge\s*=` and `isTrustedDomain\s*=` across all of `organized/` (both single-hit
> searches, reported verbatim in §65.3).
>
> Method: direct reading of pre-existing in-corpus Vineflower decompiles (nothing re-decompiled this
> session, `securityBridge.jar`'s 2 classes are the one jar never PREVIOUSLY OPENED, though already
> extracted); corpus-wide `grep -rn` for two exact assignment-statement patterns to establish each as a
> single, exhaustive hit (not a sample). Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified
> against the live system/device — highest · `[CERT]` local primary source (`file:line`) · `[CERT-a]`
> secondary/forum · `[INFER]` deduction. `file:line` citations point into `organized/<module>/vineflower/...`
> inside **this** corpus (`/home/cristian/niagara5-research/`).
>
> ByteBuddy-agent / permission-enforcement layer, closing the loop [Block 3] opened via `javap` disassembly
> and [Block 54] relied on via REMIT. Connects [Block 3] (upgrades its `[INFER]` `securityBridge.jar`
> bootclasspath-shim shape to a direct read — advances **B3-G5**; confirms its `advice.*` class/method table
> at the source level, not just `javap` signatures), [Block 54] (closes **B54-G3**; the `isTrustedDomain`
> finding in §65.3 is new evidence bearing on [Block 54] §54.5's per-site "inert" verdict — see Connections),
> [Block 44] (the `AccessController` census this block's §65.2 independently corroborates from a completely
> different code path), [Block 61] (the `niagarad`/`nre.dll` process-identity question §61.2 left open gets
> a new, unrelated data point in §65.3 — a second reason the two binaries' behavior diverges).
>
> **Type:** `mixed` — §65.1–§65.2 upgrade [Block 3]'s REMIT-level (`javap`-signature) characterization of
> `SecurityAgent`/`SecurityProviderAdvice` to a direct source read, and directly answer [Block 54] §54.5's
> named open possibility ("does the advice layer consult `AccessControlContext`/`Subject`") — the
> `[INFER]`-across-a-prior-block correction trigger per METHODOLOGY §4/§11; §65.3 is fresh evidence-gathering
> (the `isTrustedDomain` chain was not hypothesized by any prior block).

---

## 65.1 — `SecurityAgent.premain()`: the full JDK interception map — every matched type, method, and advice class `[CERT]`

`SecurityAgent.premain(String, Instrumentation)` is `nre.jar`'s declared `Premain-Class`
(`Premain-Class: com.tridium.nre.security.advice.SecurityAgent`, `Can-Redefine-Classes: true`,
`Can-Retransform-Classes: true`) `[CERT]` `organized/_bin-ext/nre/vineflower/META-INF/MANIFEST.MF:1-8`
(re-confirmed this session, first cited by [Block 3] §3.8). The method body is five sequential ByteBuddy
`AgentBuilder.Default` pipelines, each `RedefinitionStrategy.RETRANSFORMATION` + `TypeStrategy.REDEFINE`,
each `.ignore(nameStartsWith("net.bytebuddy."))` (so the agent's own classes are never re-instrumented), each
ending `.installOn(instrumentation)` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/
advice/SecurityAgent.java:12-161` (whole method, this session). The exact matched-type → matched-method(s) →
advice-class map, read directly off the `.type(...)...on(...)` chains (not summarized from names):

| Matched JDK type(s) | Matched method(s) | Advice class | Advice trigger |
|---|---|---|---|
| `java.nio.channels.SocketChannel` | `open` | `NetworkConnectionAdvice.ForSocketChannel` | `@OnMethodExit` |
| `java.net.Socket` | `connect` (declared by `Socket` itself) | `NetworkConnectionAdvice.ForSocket` | `@OnMethodExit` |
| `java.net.DatagramSocket` | `connect` OR `send` | `NetworkConnectionAdvice.ForDatagramSocket` | `@OnMethodExit` |
| `java.lang.ProcessBuilder` | `start` (0-arg overload) | `ProcessBuilderAdvice` | `@OnMethodEnter` |
| 18 named security-provider classes (`isInstalledProvider()`, below) | `clear`/`load`/`remove`/`merge`/`removeService`/`put*`/`replace*`/`compute*` | `SecurityProviderAdvice` | `.intercept(Advice.to(...))` (full method replacement wrapper, not `.visit`) |
| `java.security.Security` | `addProvider` OR `insertProviderAt` OR `removeProvider` | `SecurityProviderAdvice` | `@OnMethodEnter` |
| `java.io.File` | `createNewFile`/`mkdir`/`mkdirs`/`renameTo`/`set*`/`delete`/`deleteOnExit` | `FileAccessAdvice.ForFileWrite` | `@OnMethodEnter` (`this`) |
| `java.io.File` | `createTempFile` (3-arg overload) | `FileAccessAdvice.ForCreateTempFile` | `@OnMethodEnter` (arg 2 = directory) |
| `java.io.FileInputStream` | constructor, 1-arg `File` | `FileAccessAdvice.ForReadWithFileArgument` | `@OnMethodEnter` |
| `java.io.FileOutputStream` | constructor, 2-arg starting with `File` | `FileAccessAdvice.ForWriteWithFileArgument` | `@OnMethodEnter` |
| `java.io.RandomAccessFile` | constructor, 2-arg `(File, String mode)` | `FileAccessAdvice.ForRandomAccessFile` | `@OnMethodEnter` |
| `java.util.zip.ZipFile` | constructor, 3-arg starting with `File` | `FileAccessAdvice.ForReadWithFileArgument` | `@OnMethodEnter` (same advice class as `FileInputStream`) |
| 4 named `FileSystemProvider` classes (`isFileSystemProvider()`, below) | `newByteChannel` OR `newFileChannel` | `FileAccessAdvice.ForFileSystemProviderNewChannel` | `@OnMethodEnter` |
| same 4 providers | `newDirectoryStream` | `FileAccessAdvice.ForReadWithPathArgument` | `@OnMethodEnter` |
| same 4 providers | `createDirectory` OR `implDelete` | `FileAccessAdvice.ForWriteWithPathArgument` | `@OnMethodEnter` |
| same 4 providers | `copy` | `FileAccessAdvice.ForCopy` | `@OnMethodEnter` |
| same 4 providers | `move` | `FileAccessAdvice.ForMove` | `@OnMethodEnter` |
| `java.nio.file.Files` | `mismatch` | `FileAccessAdvice.ForMismatch` | `@OnMethodEnter` |
| `sun.awt.SunToolkit` | `createImage` OR `getImage`, first arg `String` | `FileAccessAdvice.ForReadWithStringArgument` | `@OnMethodEnter` |

`[CERT]` every row read directly off `SecurityAgent.java:16-160`'s `ElementMatchers` chain, this session —
not paraphrased from [Block 3] §3.8's 4-row category table (file/network/process/provider), which named the
CATEGORIES but not this method-level matcher detail. **This is materially finer-grained than [Block 3]'s
table**: e.g. [Block 3] said "11 advice variants covering every `java.nio.file`/`java.io` entry shape" —
this session's direct read confirms the exact count (11 nested `FileAccessAdvice` inner classes:
`ForCopy`/`ForCreateTempFile`/`ForFileRead`/`ForFileSystemProviderNewChannel`/`ForFileWrite`/`ForMismatch`/
`ForMove`/`ForRandomAccessFile`/`ForReadWithFileArgument`/`ForReadWithPathArgument`/
`ForReadWithStringArgument`/`ForWriteWithFileArgument`/`ForWriteWithPathArgument` — **13** nested classes
counted this session in the whole 242-line file `[CERT]` `FileAccessAdvice.java:18-241`, two more than
[Block 3]'s "11" because `ForFileRead`(`:54`) and `ForReadWithPathArgument`(`:179`)/`ForWriteWithPathArgument`
(`:226`) exist as distinct classes not all individually named in [Block 3]'s prose — a minor count
refinement, not a contradiction, since [Block 3] never claimed to enumerate them exhaustively).

**The two matcher-predicate methods, read whole:**

```java
private static Junction<NamedElement> isInstalledProvider() {
   return named("org.bouncycastle.jce.provider.BouncyCastleProvider")
      .or(named("sun.security.provider.Sun")).or(named("sun.security.rsa.SunRsaSign"))
      .or(named("sun.security.ec.SunEC")).or(named("com.sun.crypto.provider.SunJCE"))
      .or(named("sun.security.jgss.SunProvider")).or(named("com.sun.security.sasl.Provider"))
      .or(named("org.jcp.xml.dsig.internal.dom.XMLDSigRI")).or(named("sun.security.smartcardio.SunPCSC"))
      .or(named("sun.security.provider.certpath.ldap.JdkLDAP"))
      .or(named("com.sun.security.sasl.gsskerb.JdkSASL")).or(named("sun.security.mscapi.SunMSCAPI"))
      .or(named("sun.security.pkcs11.SunPKCS11"))
      .or(named("org.bouncycastle.jsse.provider.BouncyCastleJsseProvider"))
      .or(named("com.tridium.nre.security.NiagaraKeystoreProvider"))
      .or(named("org.bouncycastle.jcajce.bcfkswrapprovider.BouncyCastleBCFKSWrapProvider"))
      .or(named("org.bouncycastle.jcajce.provider.BouncyCastleFipsProvider"))
      .or(named("com.tridium.nre.security.provider.XMLDSigRI"));   // 18 named classes total
}
private static Junction<NamedElement> isFileSystemProvider() {
   return named("sun.nio.fs.WindowsFileSystemProvider").or(named("sun.nio.fs.UnixFileSystemProvider"))
      .or(named("jdk.nio.zipfs.ZipFileSystemProvider")).or(named("jdk.internal.jrtfs.JrtFileSystemProvider"));
}
```
`[CERT]` `SecurityAgent.java:163-189`, whole both methods, literal counted (18 and 4 respectively). All 18
`isInstalledProvider()` entries are JCE/JSSE/PKCS11/SASL/XMLDSig `java.security.Provider` subclasses (both
JDK-bundled and BouncyCastle/Tridium-authored — `NiagaraKeystoreProvider`, `com.tridium.nre.security.
provider.XMLDSigRI`, the same class §61.3's SAML block never needed to open) — matching a `Provider`
instrumented on its **mutation** methods (`clear`/`load`/`remove`/`merge`/`removeService`/`put*`/`replace*`/
`compute*`, i.e. `java.util.Properties`/`Map`-inherited methods `Provider` extends), not on construction or
lookup. `[INFER]`: this shape (guarding MUTATION of an already-installed provider's own service table, plus
`Security.addProvider`/`insertProviderAt`/`removeProvider` for the provider LIST itself) targets exactly the
two ways N5's crypto trust configuration could be tampered with at runtime — altering what a provider already
on the list SERVES, or altering WHICH providers are on the list — a narrower and more surgical target than a
blanket "any `java.security.*` call" match.

## 65.2 — `SecurityProviderAdvice` and the full enforcement chain down to the grant table: `Module`-keyed throughout, `AccessControlContext`/`Subject` never touched — closing B54-G3 `[CERT]`

**`SecurityProviderAdvice` itself is a 2-line enforcement point, not a decision-maker:**

```java
public class SecurityProviderAdvice {
   @OnMethodEnter
   public static void enter() {
      if (SecurityBridge.isInitialized()) {
         SecurityBridge.permissionBridge.checkPermission(SecurityBridge.permissionBridge.getManageSecurityProvidersPermission());
      }
   }
}
```
`[CERT]` `SecurityProviderAdvice.java:6-13`, whole file (13 lines). Every one of the other four advice
classes follows the SAME shape — a null/initialized guard on the static `SecurityBridge.permissionBridge`
field, then a `checkPermission(...)` call built from a permission-object factory method on the SAME
`IPermissionBridge` interface: `ProcessBuilderAdvice.enter()` reads the target `ProcessBuilder`'s own
`command().getFirst()` and calls `getRuntimeExecPermission(command)` `[CERT]`
`ProcessBuilderAdvice.java:8-18`; `FileAccessAdvice`'s 13 nested classes each resolve a path (from `@This`,
`@Argument`, or a cast) and call `getFilePermission(path, "read"|"write"|"read, write")` `[CERT]`
`FileAccessAdvice.java:18-241` (every one of the 13 nested classes individually confirmed this session to
follow this identical guard→resolve-path→`checkPermission(getFilePermission(...))` shape — no exceptions
found); `NetworkConnectionAdvice`'s 3 nested classes call `auditNetworkConnection(type, address)` instead of
`checkPermission` — **the only advice family that AUDITS rather than GATES**, and only for a NON-loopback
connected address, `@OnMethodExit` (after the connection already succeeded) `[CERT]`
`NetworkConnectionAdvice.java:14-64`, whole file.

**`securityBridge.jar` — the 2-class shim [Block 3] §3.8 named `[INFER]` and explicitly deferred
(`B3-G5`), opened and read whole this session, closing the content half of that gap:**

```java
// com.tridium.securityBridge.SecurityBridge
public class SecurityBridge {
   public static IPermissionBridge permissionBridge = null;
   public static boolean isInitialized() { return permissionBridge != null; }
}
// com.tridium.securityBridge.IPermissionBridge
public interface IPermissionBridge {
   void checkPermission(Object var1);
   void auditNetworkConnection(String var1, String var2);
   Object getManageSecurityProvidersPermission();
   Object getRuntimeExecPermission(String var1);
   Object getFilePermission(String var1, String var2);
}
```
`[CERT]` both whole files, `SecurityBridge.java:1-9` (9 lines), `IPermissionBridge.java:1-13` (13 lines) —
confirms [Block 3] §3.8's prediction almost exactly: a tiny (9+13 line) static-holder + interface pair, own
`module-info.class` (`module niagara.securityBridge { exports com.tridium.securityBridge; }` `[CERT]`
`organized/_bin-ext/securityBridge/vineflower/module-info.java`, whole 3-line file — no `requires` clause at
all, confirming it depends on nothing beyond `java.base`). **What this session does NOT confirm**: [Block 3]
§3.8's `-Xbootclasspath/a:` loading-mechanism claim — that remains `[INFER]`, unchanged, since this session
read the jar's CONTENT, not its classloader placement; the interface's `checkPermission(Object)` /
`getFilePermission(String,String)` signatures using raw `Object`/`String` rather than the concrete
`NiagaraPermission`/`FilePermission` types IS, however, independent supporting evidence for [Block 3]'s
"illegal-access-avoidance" rationale — a type-erased interface is exactly the shape needed for
`securityBridge`'s module (or an unnamed/bootstrap classloader context) to call into `PermissionBridge`
(a `niagara.nre`-module class implementing concrete `NiagaraPermission` subtypes) without either side needing
a compile-time dependency on the other's permission class hierarchy. `[INFER]` for the rationale; `[CERT]`
for the observed type-erased shape itself.

**The concrete implementer, and the full call chain from advice down to the grant-table decision — read
whole this session, extending [Block 54]'s partial `:95-140`/`:236-238` citations to full methods:**

```
FileAccessAdvice.ForFileWrite.onEnter()                              [advice.*]
  → SecurityBridge.permissionBridge.checkPermission(getFilePermission(path, "write"))
      SecurityBridge.permissionBridge is a PermissionBridge instance  [permissions.PermissionBridge]
  → PermissionBridge.checkPermission(Object niagaraPermission)
      → SecurityUtil.checkPermission((NiagaraPermission) niagaraPermission)     [nre.util.SecurityUtil]
          if (!PermissionUtil.isTrustedDomain) consumePrivilegedModules(permission::isGrantedTo);
          → consumePrivilegedModules(consumer):
              StackWalker.walk() over the calling thread's frames, takeWhile "privileged"
              (isPrivileged(frame, counter) — a frame-classification helper, not opened further this
              session, but its OUTPUT is unambiguous from the surrounding code: a Set<Module> of the
              distinct java.lang.Module owners of the "privileged" prefix of the call stack)
              → for each such Module: consumer.accept(module)  i.e. permission.isGrantedTo(module)
  → NiagaraPermission.isGrantedTo(Module module)          [permissions.NiagaraPermission, final method]
      → PermissionManager.checkPermission(this, module)   [package-private, the actual decision point]
          if (PermissionUtil.isTrustedDomain) return;                          // ← §65.3
          if (Bootstrap.isTest()) { ...skip for test/mock modules... }
          if (moduleName is niagara.nre/niagara.baja/niagara.niagarad/net.bytebuddy.agent/java.*/
              javax.*/jdk.*/javafx.*) return;                                  // trusted-by-name allowlist
          check permissionCheckCache[(module, permission)] — memoized allow/deny
          else: permission.doIsGrantedTo(module)   [NOT opened this session — see scope note]
              throws PermissionException on deny → caught, audited (SecurityAuditEvent("Permission
              Check", ...), [Block 54] §54.2's own emitter table), logged, RE-THROWN unless
              PermissionUtil.permissionChecksDisabled
```
`[CERT]` for every arrow (`PermissionBridge.java:18-25`, `SecurityUtil.java:230-238,322-333`,
`NiagaraPermission.java:20-22`, `PermissionManager.java:51-139`, all read whole or in the cited targeted
range this session); `[INFER]` only for `isPrivileged()`'s own internal frame-classification RULE (the
method itself was not opened this session — its call site and the Set<Module> it produces from
`takeWhile(...).map(frame -> frame.getDeclaringClass().getModule())` IS directly read, `[CERT]`
`SecurityUtil.java:322-333`).

**Answering B54-G3's exact question — the enforcement chain is `java.lang.Module`-identity-keyed, from the
very first advice call to the final grant-table lookup, and never once constructs, inspects, or delegates to
an `AccessControlContext` or a `Subject`.** Every class opened this session for this trace
(`SecurityAgent`/`SecurityProviderAdvice`/`FileAccessAdvice`/`NetworkConnectionAdvice`/`ProcessBuilderAdvice`/
`SecurityBridge`/`IPermissionBridge`/`PermissionBridge`/`SecurityUtil`/`NiagaraPermission`/`PermissionManager`/
`PermissionUtil`) contains zero references to `java.security.AccessControlContext`,
`java.security.AccessController`, or `javax.security.auth.Subject` — confirmed by the same whole-tree
`grep -rn` discipline [Block 54] §54.5 already ran corpus-wide (0/0/1/2 hits for the four `Subject.*` call
shapes, none inside any file this session opened) plus a direct read of every method in the actual decision
path. **This directly closes [Block 54] §54.5's own named uncertainty** ("the advice classes intercept calls
*before* they reach `AccessController`, a different mechanism than what this block traced... a possibility
this block did not rule out"): the mechanism this session traced end-to-end IS that different mechanism, and
it is now traced, and it does not touch `AccessControlContext`/`Subject` either — the two independent
enforcement families (`AccessController`-family sites, [Block 54] §65.5; ByteBuddy-advice sites, this block)
are BOTH confirmed `Module`-identity-based (or, for the `AccessController` family, provably inert), by two
separate direct reads rather than one extrapolated from the other.

## 65.3 — New finding: `NiagaraDaemon.Main()` sets `PermissionUtil.isTrustedDomain = true` unconditionally — the platform daemon process is architecturally exempt from every advice-driven permission check `[CERT]`+`[INFER]`

Tracing §65.2's chain to its root surfaces a fact no prior block in this corpus named. `PermissionUtil` is a
4-field static-holder class with no logic of its own:

```java
public final class PermissionUtil {
   public static boolean permissionChecksDisabled = false;
   public static boolean isTrustedDomain = false;
   public static Path moduleDevPath = null;
}
```
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/restricted/
PermissionUtil.java:1-11`, whole file. A corpus-wide `grep -rn "isTrustedDomain\s*="` (this session, over
the whole `organized/` tree) finds exactly **two** assignment sites — the field's own declaration-line
default (`= false`, above) and exactly ONE runtime mutation, anywhere in the corpus:

```java
// com.tridium.niagarad.NiagaraDaemon
public static void Main(String[] args) {
   ticksAtMainStart = ticks();
   PermissionUtil.isTrustedDomain = true;          // ← the literal second statement of Main()
   try {
      instantiator.instance(ISecurityInitializer.class);
   } ...
```
`[CERT]` `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/NiagaraDaemon.java:195-199`
(`Main()` head, this session) — **unconditional**: no feature flag, no config check, no environment-variable
gate precedes it; it is the first security-relevant line the platform daemon's own entry point executes,
before even the security-initializer instantiation that follows it.

**Why this flag is load-bearing for the ENTIRE advice layer, not just `PermissionManager`'s own checks.**
Two independent consumers of `isTrustedDomain` were read this session:

1. `PermissionManager.checkPermission(NiagaraPermission, Module)` — the decision method at the bottom of
   §65.2's chain — opens with `if (PermissionUtil.isTrustedDomain) { return; }`, its literal first statement
   `[CERT]` `PermissionManager.java:53-55`. A permission check that reaches this method with the flag set
   returns silently — grant, no audit, no cache entry.
2. `com.tridium.nre.bootstrap.Bootstrap`'s own bootstrap sequence — the class whose `bootstrap(...)`-adjacent
   startup logic wires the ENTIRE advice layer's dependency — gates the ONE place in the whole corpus that
   ever assigns `SecurityBridge.permissionBridge` a non-null value:
   ```java
   if (!PermissionUtil.isTrustedDomain) {
      SecurityBridge.permissionBridge = new PermissionBridge();
   }
   ```
   `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/bootstrap/Bootstrap.java:232-234`, immediately
   before `Bootstrap` hands off to `com.tridium.sys.Nre.bootstrap(args)` (`:236-238`). A corpus-wide
   `grep -rn "SecurityBridge\.permissionBridge\s*="` (this session) confirms this is the field's **only**
   assignment site anywhere in `organized/` — `SecurityBridge.permissionBridge` therefore stays at its
   declared default, `null`, for the lifetime of any JVM process for which this line is skipped.

**The consequence for every advice class in §65.1/§65.2: `SecurityBridge.isInitialized()` (`permissionBridge
!= null`) is the FIRST guard every one of them checks, before `checkPermission`/`auditNetworkConnection` is
ever called** — `FileAccessAdvice`'s 13 nested classes, `NetworkConnectionAdvice`'s 3, `ProcessBuilderAdvice`,
and `SecurityProviderAdvice` all open with `if (SecurityBridge.isInitialized())` (or the `try { if
(!SecurityBridge.isInitialized()) return; } catch (NoClassDefFoundError...)` variant `FileAccessAdvice` uses
— §65.2). **If `permissionBridge` is never assigned, EVERY advice class's body becomes a silent no-op for
the process's entire lifetime** — the ByteBuddy weaving still happens (§65.1's interception map is installed
regardless, since `SecurityAgent.premain()` itself has no `isTrustedDomain` check), but every intercepted
call falls straight through with zero permission check and zero audit event.

**Reading the two facts together (the load-bearing `[INFER]`).** `PermissionUtil.isTrustedDomain = true`
being set unconditionally at `NiagaraDaemon.Main()`'s very start, combined with `Bootstrap.java:232-234`'s
`!isTrustedDomain` guard on the ONLY `permissionBridge` assignment in the corpus, means: **for any JVM
process where `NiagaraDaemon.Main()` runs before (or instead of) `Bootstrap`'s `permissionBridge` assignment,
`SecurityBridge.permissionBridge` never becomes non-null, and the entire ByteBuddy advice-driven permission
layer traced in §65.1/§65.2 — file access, process spawn, network-connection audit, security-provider
mutation — is permanently inert for that process.** This is `[INFER]`, not `[CERT]`, for one specific
residual reason honestly named: this session did not find (or look for) the exact call site that invokes
`NiagaraDaemon.Main()` itself, so whether it runs in the SAME JVM process/call stack as `Bootstrap`'s
sequence — rather than, say, a wrapper `main()` that calls `NiagaraDaemon.Main()` directly and never touches
`Bootstrap` at all — is not directly observed. Three independent pieces of `[CERT]` evidence support the
same-process reading without fully closing it: (a) `niagarad`'s own `module-info.java` declares `requires
transitive niagara.nre` `[CERT]` (whole file, above) — the `niagara.niagarad` module has a hard compile-time
dependency on `niagara.nre` (the module `PermissionUtil`/`Bootstrap`/`SecurityBridge`'s classes all live in),
confirming they share a module layer, not merely that they COULD; (b) [Block 3] §3.8's own `javap`-verified
table (re-cited, not re-verified this session) already named `permissions.restricted.PermissionUtil`'s
package as "the exact package the native launcher `--add-exports`'s to `niagara.niagarad`" — meaning N5's
OWN native launcher strings (read `[CERT]` by [Block 3], `strings` output over `nre.dll`) explicitly wire a
JPMS export of this exact restricted package TO the `niagara.niagarad` module, independent evidence that
`niagarad` is expected to reach into `PermissionUtil` at runtime, matching what `NiagaraDaemon.Main()`'s own
source does; (c) `niagarad.jar`'s own `MANIFEST.MF` has NO `Premain-Class` of its own `[CERT]`
(`organized/_bin-ext/niagarad/vineflower/META-INF/MANIFEST.MF`, this session) — if the SecurityAgent
instrumentation is active in the `niagarad` process at all, it can only be `nre.jar`'s agent, reinforcing
that `niagarad` and the agent share `nre.jar`'s classes. What remains genuinely unconfirmed — the residual
gap, **B65-G1** — is the native JVM launch command for `niagarad.exe` itself: whether it passes
`-javaagent:nre.jar` at all, and the exact call sequence between `Bootstrap`'s entry point and
`NiagaraDaemon.Main()`. This is the same class of gap as [Block 54]'s **B54-G1** and [Block 61]'s
**B61-G1** — a native-launch-flag fact outside decompiled-`.class`/`.java` scope.

**What this does NOT change.** [Block 54] §54.5's own "inert" verdict was about the `AccessController`-family
sites (a DIFFERENT, already-provably-dead mechanism — no `SecurityManager` installed, §54.5) and is
untouched by this finding. This block's §65.3 finding is about a DIFFERENT layer (the ByteBuddy advice) being
conditionally (not universally) inert — specifically for whichever process path sets `isTrustedDomain` before
`Bootstrap` would otherwise wire `permissionBridge`. For a normal STATION process (`station.exe`/`nre.dll`,
per [Block 61] §61.2's native-binary identification), nothing in this session's reads suggests
`isTrustedDomain` is ever set true — the ONE mutation site found corpus-wide is `NiagaraDaemon.Main()`
specifically, and `Bootstrap.java`'s own default path (the `!isTrustedDomain` branch) assigns
`permissionBridge` normally, consistent with [Block 3]/[Block 44]/[Block 54]'s shared premise that a running
station DOES enforce this permission model (`PermissionManager`'s allowlist explicitly excludes only
`niagara.nre`/`niagara.baja`/`niagara.niagarad`/`net.bytebuddy.agent`/JDK-prefixed modules by NAME, §65.2 —
implying ordinary third-party/driver modules ARE checked in that process). The finding is specifically that
`niagarad` — the platform daemon, a SEPARATE process per [Block 57]/[Block 61] — is architecturally exempted
from this specific layer, by design (`isTrustedDomain` is not a bug-shaped accidental true; it is the literal
first line of that process's own `Main()`), not that station-side enforcement is broken.

## 65.4 — Self-verification

**Token check.** Every load-bearing `[CERT]` `file:line`/whole-file citation above was read directly this
session (not hand-recalled): `SecurityAgent.java` (whole 191-line file), `SecurityProviderAdvice.java`
(whole 14-line file), `FileAccessAdvice.java` (whole 242-line file, all 13 nested classes individually
confirmed), `NetworkConnectionAdvice.java` (whole 65-line file, all 3 nested classes), `ProcessBuilderAdvice.
java` (whole 20-line file), `SecurityBridge.java`/`IPermissionBridge.java` (both whole, first opening of this
jar in the corpus), `PermissionBridge.java` (whole 73-line file), `PermissionManager.java` (whole 429-line
file, `checkPermission`/`initThirdPartyPermissions`/allowlist all read, not excerpted), `SecurityUtil.java`
(`:230-238` `checkPermission`, `:322-333` `consumePrivilegedModules`, targeted re-read past [Block 54]'s
citation), `NiagaraPermission.java` (whole 41-line file), `PermissionUtil.java` (whole 11-line file),
`Bootstrap.java:228-238` (targeted), `NiagaraDaemon.java:195-199` (targeted), `nre.jar`'s `MANIFEST.MF:1-8`
and `niagarad.jar`'s `MANIFEST.MF` head (both read), `niagarad`'s and `nre`'s and `securityBridge`'s
`module-info.java` (all 3 whole files). Two corpus-wide `grep -rn` runs (`isTrustedDomain\s*=`,
`SecurityBridge\.permissionBridge\s*=`) each returned exactly 1 assignment site beyond a declaration —
reported verbatim, not summarized, in §65.3. Spot-check tokens independently re-confirmed present this
session (not reused from any prior block's excerpt): `Premain-Class: com.tridium.nre.security.advice.
SecurityAgent` (MANIFEST), `isInstalledProvider()`/`isFileSystemProvider()` (both matcher methods, full
`.or(...)` chains counted: 18 and 4 respectively), `IPermissionBridge` interface's 5 method signatures,
`if (PermissionUtil.isTrustedDomain) { return; }` (`PermissionManager.java`), `PermissionUtil.isTrustedDomain
= true;` (`NiagaraDaemon.java`), `requires transitive niagara.nre;` (`niagarad` module-info).

**Marker tally — mechanized, literal `verify-block.sh` output** (run this session from
`/home/cristian/niagara5-research`):

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block65.md .
== verify-block: niagara5-block65.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 1)
   [CERT-live] 1
   [CERT] 32  (adj 31)
   [CERT-doc] 1
   [CERT-web] 2
   [CERT-a] 2  (adj 1)
   [INFER] 19  (adj 14)
-- ratio -- [INFER]/[CERT*] = 14/37 = 0.38
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  Bootstrap.java:228-238 / :232-234, FileAccessAdvice.java:18-241, IPermissionBridge.java:1-13,
           MANIFEST.MF:1-8, NetworkConnectionAdvice.java:14-64, NiagaraDaemon.java:195-199,
           NiagaraPermission.java:20-22, PermissionBridge.java:18-25, PermissionManager.java:51-139 / :53-55,
           ProcessBuilderAdvice.java:8-18, SecurityAgent.java:16-160 / :163-189, SecurityBridge.java:1-9,
           SecurityProviderAdvice.java:6-13, SecurityUtil.java:322-333 (17 short-form citations — bare
           `file:line` body forms with a fully-pathed counterpart cited elsewhere in the block; see below)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/NiagaraDaemon.java:195-199
           (range end verified; file has 1641 lines)
   ok      organized/_bin-ext/nre/vineflower/META-INF/MANIFEST.MF:1-8  (range end verified; file has 2343 lines)
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/bootstrap/Bootstrap.java:232-234
           (range end verified; file has 366 lines)
   resolved 3 of 20
== exit 0 ==
```

**Reading the raw vs. adjusted split — the same self-referential inflation [Block 54] §54.6/[Block 61]'s
Self-verify sections both document.** The raw `[CERT-hw]`(2)/`[CERT-live]`(1)/`[CERT-doc]`(1)/`[CERT-web]`(2)/
`[CERT-a]`(2) counts are **entirely accounted for** by this block's own header-blockquote marker LEGEND
(`` `[CERT-hw]` ``/`` `[CERT-a]` ``, §65 header) plus this very Self-verification section's own prose using
those marker tokens by name while describing the tally categories (verified this session: every one of those
6 raw hits traces to line 74/75 of the header legend or this section's own tally/prose, zero to a body
claim) — this block makes **zero** actual `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]`
claims; every load-bearing citation in §65.1–§65.3 is `[CERT]` (local primary source, decompiled `.java`) or
`[INFER]`. The real evidence tally is therefore **31 `[CERT]` against 14 `[INFER]`, ratio 0.38** — the
script's own reported adjusted ratio — moderate, below the ~0.5 exhaustion threshold, and consistent with a
`mixed` block whose one extended inferential chain (§65.3's same-process reasoning, explicitly hedged, its
residual gap named **B65-G1**) is built directly from this session's own dense `[CERT]` reads, not
free-standing speculation.

**Citation resolution.** `resolved 3 of 20` — 3 full-path (`organized/...`) citations resolve `ok` (all
range-verified against actual on-disk file lengths: `NiagaraDaemon.java` 1641 lines, `MANIFEST.MF` 2343
lines, `Bootstrap.java` 366 lines — the cited ranges all fall inside). The 17 `extern` rows are the SAME
citations in bare `file:line` short-form, used in body prose for readability where a fully-pathed citation to
the SAME file already appears in the header-blockquote Sources list (METHODOLOGY §11's named "bare `:line`
body + full `filename:line` self-verify anchor" pair) — e.g. `SecurityAgent.java:16-160` in §65.1's body
prose is the same file the header Sources list cites in full as `organized/_bin-ext/nre/vineflower/com/
tridium/nre/security/advice/SecurityAgent.java`. This is the expected decompiled-tree signature (METHODOLOGY
§11: "DECOMPILED-TREE BLOCKS WILL SHOW ZERO OR PARTIAL RESOLVED CITATIONS — THIS IS EXPECTED"), matching
[Block 41]/[Block 44]/[Block 49]/[Block 54]/[Block 61]'s identical pattern on this corpus; the burden falls
on the Token check above, which independently confirms every cited file was opened and read this session.

**Artifacts.** This file (`/home/cristian/niagara5-research/niagara5-block65.md`) is the only artifact
written this session, per the caller's explicit single-file/read-only-elsewhere constraint —
`CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated or hand-edited, matching every
predecessor block's identical disclosure on this corpus.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 65.5 — Child gaps

- **B65-G1** — Confirm whether `niagarad.exe`'s own JVM invocation actually loads `nre.jar`'s `-javaagent`
  instrumentation, and trace the exact call sequence between `com.tridium.nre.bootstrap.Bootstrap`'s startup
  path and `com.tridium.niagarad.NiagaraDaemon.Main()` — specifically, whether `Main()` runs in the SAME
  process/call stack `Bootstrap.java:232-234`'s `permissionBridge` assignment does, or via a separate
  entry-point that never reaches `Bootstrap` at all (in which case `permissionBridge` stays `null` by simple
  omission, independent of the `isTrustedDomain` flag `NiagaraDaemon.Main()` also sets). A native
  launch-flag/process-tracing fact, same limitation class as [Block 54]'s **B54-G1**/[Block 61]'s **B61-G1**.
  `blocked-on-source` for a decompiled-only session; `investigable` live if a running N5 install with process
  inspection (`jcmd`/`ManagementFactory` on the actual `niagarad` PID) becomes available.
- **B65-G2** — Read `PermissionUtil.isPrivileged(StackFrame, int[])` (the frame-classification predicate
  `SecurityUtil.consumePrivilegedModules` calls, `SecurityUtil.java` — the exact line range was not opened
  this session, only its call site and consumer) to confirm precisely which stack frames count as
  "privileged" for the purpose of collecting the `Set<Module>` `PermissionManager.checkPermission` is called
  against — i.e., whether a deeply-nested call chain can cause an INTERMEDIATE module (not just the immediate
  caller) to be silently checked/granted instead of the actual originating third-party module. `investigable`
  — file already present in-corpus.
- **B65-G3** — Read `FilePermission`/`RuntimeExecPermission`/`NiagaraBasicPermission`'s own
  `doIsGrantedTo(Module)` bodies (only `FilePermission`'s class header/fields were read this session, §65
  header scope note) to confirm the actual per-module grant-matching algorithm — path-prefix matching against
  `PermissionManager.getPermissions(module, cls)`'s per-module annotation-derived set (§65.2's chain
  identifies WHERE this call happens but not HOW the match itself is computed). `investigable`.
- **B65-G4** (closes the loading-mechanism half of **B3-G5**) — Empirically confirm (or find further static
  evidence for) `securityBridge.jar`'s `-Xbootclasspath/a:` loading claim [Block 3] §3.8 originated as
  `[INFER]` — e.g. a launcher-script/`nre.properties` grep for `-Xbootclasspath`, or a live
  `jcmd <pid> VM.system_properties`/`ManagementFactory.getRuntimeMXBean().getInputArguments()` probe (same
  live-station blocker as **B54-G1**/**B54-G2**/**B61-G1**/**B65-G1** — these five gaps share one blocker and
  could close together in a single live-station session). `blocked-on-source`.

## 65.x — Connections

- **[Block 3]** — advances **B3-G5** (the `securityBridge.jar` 2-class shim's CONTENT is now directly read
  and confirmed to match [Block 3] §3.8's `[INFER]` prediction; the LOADING-mechanism half remains open, now
  refined as **B65-G4**); §65.1's interception-map table is a direct-source-read refinement of §3.8's
  4-category `javap`-signature table (finer method-level granularity, not a contradiction); §65.3's
  `--add-exports`-to-`niagara.niagarad` citation (§3.5, re-cited not re-verified) is independent corroborating
  evidence for the same-process reading in §65.3's `[INFER]`.
- **[Block 54]** — closes **B54-G3**: §65.2 opens `SecurityAgent`/`SecurityProviderAdvice` directly (not via
  REMIT) and answers §54.5's explicitly-left-open question — the advice layer never consults
  `AccessControlContext`/`Subject`, confirmed by direct chain-trace rather than the corpus-wide negative
  `grep` §54.5 already had. §65.3's `isTrustedDomain`/`niagarad` finding is NEW evidence adjacent to, but
  distinct from, §54.5's "inert `AccessController`-family sites" verdict — a different enforcement layer,
  same station-vs-daemon process-identity axis [Block 54] did not examine.
- **[Block 44]** — §65.2's `Module`-keyed, `AccessControlContext`/`Subject`-free enforcement chain
  independently corroborates [Block 44]'s original `AccessController`-census framing and [Block 54] §54.5's
  per-site "inert" verdict, from a completely separate code path (the ByteBuddy advice layer, not the
  `AccessController` call sites [Block 44] originally censused).
- **[Block 61]** — §65.3's `niagarad`-vs-`station` process-identity distinction is a second, independent axis
  of the same "these two N5 processes behave differently" theme §61.2's `njre.dll`/`nre.dll` native
  import-table split established — one at the NATIVE-binary-capability layer (§61.2, `CreateProcessA`/SCM
  imports), one at the JVM-permission-layer (§65.3, `isTrustedDomain`); **B65-G1** and **B61-G1** are
  companion gaps (both ask "what does `niagarad`'s own process actually do at launch") and named as
  candidates to close together in §65.5.
