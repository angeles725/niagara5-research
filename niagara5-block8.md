# Block 8 — N5 permission model: SecurityAgent advice and PermissionManager grants

> **Scope**: Closes gap **B3-G3** (decompile `PermissionManager.initThirdPartyPermissions()`/`addPermissions()`
> to recover N5's default grant table) and **B3-G4** (map N4's textual `<java-permissions>`/
> `<niagara-permission-groups>` taxonomy onto N5's `NiagaraPermission` subclass taxonomy). Covers: the full
> `NiagaraPermission` class hierarchy and its 2 grant-declaration halves (core-only vs. public/third-party);
> the mechanism a module uses to REQUEST a permission (`module-info.java` annotations, replacing N4's
> `module.xml <permissions>` element outright); a census of the 247 shipped N5 module jars for which ones
> declare which grant annotations; the default third-party-library grant table
> (`PermissionManager.initThirdPartyPermissions()`); the full advice→bridge→`PermissionManager`→caller-module
> check path, including the `StackWalker`-based privileged-frame walk in `SecurityUtil`; the enforcement
> modes (enforced by default; a license-gated `niagara.permissions.disable` developer mode that logs instead
> of throwing — no distinct "warn" mode exists); and the concrete implication for a third-party module (e.g.
> DashboardPan/ColdRoomPan) that opens files/sockets/processes. Does **not** cover: `KeyRing`/`SystemPassphrase`
> cryptographic material itself (§3.9 territory), the FIPS provider toggle (§3.6.8), or a live
> `[CERT-hw]` reproduction of a `PermissionException` on real hardware (named child gap below).
>
> Subject version: **N5 5.0.0.28 (Beta)** — same install as [Block 3] (`etc/brand.properties:workbench.notice`
> Beta marker), same JRE 25.0.4.7. N4 comparison baseline: `niagara-research` corpus B635 (module-anatomy
> MA7, N4 4.14, module-permission wiring) and B18 §18.4.4 (N4's ~25-group `NiagaraPermissionGroupFactory`
> taxonomy, itself a correction of an earlier 19-group count).
>
> Sources (all local, read-only):
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` — `com.tridium.nre.security.permissions.*`,
>   `com.tridium.nre.security.advice.*`, `com.tridium.nre.security.permissions.restricted.PermissionUtil`,
>   `niagara.nre.security.permissions.*` (public taxonomy), `niagara.nre.util.SecurityUtil`.
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/niagaraAnnotationProcessors.jar` —
>   `com.tridium.nre.annotations.*` (core-only grant annotations) and `niagara.nre.annotations.*` (public
>   grant annotations).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` — `com.tridium.sys.Nre`
>   (`niagara.permissions.disable` boot wiring), used only as an `-e` decompiler classpath aid + direct
>   `javap`/grep target for that one class; module.xml inspection of `baja.jar` and `dashboard.jar`
>   (negative-existence check for a `<permissions>` element).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar` (**247** jars) — `module-info.class`
>   constant-pool census for the 7 permission-grant annotation names.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` —
>   `doc/security/niagaraPermissions.html`, `doc/security/requestingPermissions.html` (official shipped
>   developer docs, read via Python `zipfile` + HTML-tag-stripped text extraction).
> - REMITTANCE baseline: `niagara-research` corpus B635 (`niagara-mental-model-bloque635.md`, N4
>   `NModule.readPermissions`/`ModuleClassLoader`/`Nre`/`GrantAllPermissionGroupStore`) and B18
>   (`niagara-mental-model-bloque18.md` §18.4.4, N4's ~25 `NiagaraPermissionGroup` names + the 3 that always
>   require signing), fetched via `python3 /home/cristian/niagara-research/tools/corpus-nav.py show <N>`.
> - [Block 3] (`niagara5-block3.md` §3.8) — the parent finding this block was seeded from (SecurityAgent +
>   ByteBuddy advice + `PermissionManager.checkPermission(NiagaraPermission, Module)` identified but not
>   decompiled).
>
> Method: `unzip` extraction of `nre.jar` (126 classes under `com/tridium/nre/security/**`) and
> `niagaraAnnotationProcessors.jar`, decompiled with **Vineflower 1.12.0**
> (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar`) on
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java` (OpenJDK 26.0.2.1) into
> `/tmp/claude-1000/n5b8/decompiled/` (ephemeral scratch, not part of the corpus — re-derivable from the
> jars cited; ~20 target classes decompiled cleanly to readable Java source, not raw bytecode, since none of
> `nre.jar`'s security classes are minified/obfuscated — ordinary `file:line` citation applies, no sha256
> beautified-temp anchor needed). A Python `zipfile`+`re` one-liner extracted and HTML-stripped the two
> `docDeveloper.jar` pages into `/tmp/claude-1000/n5b8/docextract/*.txt`. The 247-module census is a Python
> `zipfile` scan of each `module-info.class`'s raw bytes for 7 literal annotation-name byte strings
> (`census.py`, one-shot, output captured verbatim below). Markers: `[CERT]` local primary (jar/class file
> opened this session) · `[CERT-doc]` official shipped doc (`docDeveloper.jar`, opened this session) ·
> `[INFER]` deduction. Every `[CERT]`/`[CERT-doc]` below was read this session; none is carried from memory.
> **Code vs. doc**: where the two disagree, code is authoritative for BEHAVIOUR, the doc for INTENT — one
> concrete disagreement is recorded in §8.6 (log-file naming) and flagged explicitly rather than silently
> merged.
>
> Security/runtime layer. Connects [Block 3] (§3.8 seeded this block; §3.5's `--add-exports
> niagara.nre/com.tridium.nre.security.permissions.restricted=niagara.niagarad` is the exact package this
> block's `PermissionUtil` class lives in). Cross-corpus: `niagara-research` B635, B18 §18.4.4, B3(niagara-research,
> different numbering — module-anatomy MA7's own B3, not this corpus's Block 3).
>
> **Type:** standard

---

## 8.1 — The permission taxonomy: 8 concrete `NiagaraPermission` subclasses in two trust tiers `[CERT]`

`NiagaraPermission` (abstract, `com.tridium.nre.security.permissions.NiagaraPermission.java:8-43`) is the
single base class. Its public API is intentionally small: `isGrantedTo(Module)` (final, delegates to
`PermissionManager.checkPermission`), an abstract `doIsGrantedTo(Module)` each subclass implements as its
own decision logic, `equals`/`hashCode` (abstract — every subclass must define value equality, used by the
grant-table's `Set<NiagaraPermission>`), and an `environmentType` (`STATION`/`WORKBENCH`/`ALL`,
`NiagaraPermission.java:10-18,40-42`) gating whether a permission even applies outside a station or
workbench process.

There are **8 concrete subclasses**, split cleanly into two trust tiers by PACKAGE, not by any explicit
"internal/public" flag:

| # | Class | Package (trust tier) | Grant-request annotation | `[CERT]` |
|---|---|---|---|---|
| 1 | `FilePermission` | `com.tridium.nre.security.permissions` (**core-only**) | `@GrantFilePermission(path, actions)` | `FilePermission.java:19,49-68` |
| 2 | `KeyRingPermission` | `com.tridium.nre.security.permissions` (**core-only**) | `@GrantKeyRingPermission(value)` | `KeyRingPermission.java:8-14` |
| 3 | `NiagaraBasicPermission` | `com.tridium.nre.security.permissions` (**core-only**) | `@GrantNiagaraBasicPermission(value)` | `NiagaraBasicPermission.java:6-92` |
| 4 | `ModifyProtectedPropertiesPermission` | `com.tridium.nre.security.permissions` (**core-only, and un-requestable**) | **none — no Grant annotation exists for it** | `ModifyProtectedPropertiesPermission.java:8-23` |
| 5 | `PublicNiagaraBasicPermission` | `niagara.nre.security.permissions` (**public**) | `@GrantPublicNiagaraBasicPermission(value)` | `PublicNiagaraBasicPermission.java:6-33` |
| 6 | `KeyStorePermission` | `niagara.nre.security.permissions` (**public**) | `@GrantKeyStorePermission(name, actions)` | `KeyStorePermission.java:9-82` |
| 7 | `RuntimeExecPermission` | `niagara.nre.security.permissions` (**public**) | `@GrantRuntimeExecPermission(value, type)` | `RuntimeExecPermission.java:15-53` |
| 8 | `SigningPasswordPermission` | `niagara.nre.security.permissions` (**public**) | `@GrantSigningPasswordPermission(value)` | `SigningPasswordPermission.java:8-37` |

**The trust split is enforced in code, not just by package convention.** `PermissionManager.isAnnotationPermitted`
(`PermissionManager.java:413-423`) rejects any `com.tridium.*`-named annotation (i.e. all of #1-3's Grant
annotations, since they live in package `com.tridium.nre.annotations`) unless the requesting module's own
JPMS name starts with `com.tridium.` or `niagara.` — logging a `WARNING` ("Cannot grant private annotation
... to non-core module") and silently DROPPING the grant otherwise (`PermissionManager.java:416-419`). This
is the code-level mechanism behind `docDeveloper.jar:doc/security/niagaraPermissions.html` `[CERT-doc]`
("Third party modules cannot create and enforce custom permissions. Only the permissions provided by the
core Niagara Framework can be used."): the 4 public-tier classes (#5-8, package `niagara.nre.*`) are the
ENTIRE set a third-party module can ever request — `FilePermission` (#1) is explicitly NOT among them.

**`ModifyProtectedPropertiesPermission` (#4) has no Grant annotation at all** — a full-file read of both
annotation jars found no `GrantModifyProtectedProperties`-shaped type. Its constructor takes a
`Set<String> trustedModules` directly (`ModifyProtectedPropertiesPermission.java:11-14`), and `doIsGrantedTo`
(`:16-23`) allows the calling module only if it is IN that hardcoded set, OR its JPMS name starts with
`niagara.`/`com.tridium.` and does NOT end in `Test`. This permission can never be requested by ANY module
via declaration — the trusted set is baked in wherever a `ModifyProtectedPropertiesPermission` instance is
constructed (not traced further this session — construction sites are outside `com.tridium.nre.security.**`
→ child gap **B8-G1**).

`niagara.nre.security.permissions.PermissionException` (`PermissionException.java:3-14`) — the exception
every denial throws — extends `java.lang.SecurityException` and carries `getModuleName()`. `[CERT]`
Confirmed verbatim against `docDeveloper.jar` `[CERT-doc]`: "Any code that requires a permission will fail
with a `niagara.nre.security.permissions.PermissionException`."

## 8.2 — Requesting a permission: `module-info.java` annotations replace `module.xml <permissions>` outright `[CERT]` / `[CERT-doc]`

**N4's `<permissions>` XML element is gone, not relocated.** A direct `unzip -p` read of
`baja.jar:META-INF/module.xml` and `dashboard.jar:META-INF/module.xml` — the two N5 module.xml files already
opened for [Block 3] §3.7 plus one fresh grep this session — found **zero** `<permissions>`,
`<java-permissions>`, or `<niagara-permission-groups>` elements in either; the one substring match for
"permission" in `baja.jar`'s module.xml is an unrelated `<type class="niagara.security.BPermissions"
name="Permissions"/>` RBAC-component catalog entry, confirmed by direct offset inspection, not a
permission-DECLARATION element. `[CERT]` (`python3 -c "zipfile..."`, this session, both jars)

In its place, N5 grants permissions via **`java.lang.annotation.ElementType.MODULE`-targeted annotations on
the module-info.java declaration itself** — i.e. the module keyword in `module-info.java` carries the Grant
annotations directly, exactly as `docDeveloper.jar:doc/security/requestingPermissions.html` `[CERT-doc]`
shows in its worked example:
```java
@GrantKeyStorePermission(name = "userKeyStore", actions = "read")
@GrantPublicNiagaraBasicPermission(MANAGE_SERVER_TRUST_ANCHORS)
module myCompany.myModule { ... }
```
All 7 Grant annotation types declare `@Target(ElementType.MODULE)` and are `@Retention(RUNTIME)` —
confirmed by direct read of all 7 annotation source files (`GrantFilePermission.java:10-11`,
`GrantKeyRingPermission.java:10-11`, `GrantNiagaraBasicPermission.java:10-11`,
`GrantKeyStorePermission.java:11-12`, `GrantPublicNiagaraBasicPermission.java:10-11`,
`GrantRuntimeExecPermission.java:12-13`, `GrantSigningPasswordPermission.java:10-11`) — RUNTIME retention is
what lets `PermissionManager.getPermissions` read them straight off the live `java.lang.Module` object via
reflection (`module.getAnnotations()`, `PermissionManager.java:356`), with no `module.xml` parser involved
at all. Each is `@Repeatable` via a matching `*Permissions` container annotation (e.g.
`FilePermissions.java:11-13` wraps `GrantFilePermission[]`), so a module can carry multiple grants of the
same permission type. `PermissionFactory.makeNiagaraPermission` (`PermissionFactory.java:26-37`) is the
exhaustive switch-pattern mapping each of the 7 annotation types to its `NiagaraPermission` construction —
this switch IS the closed list; there is no 8th path.

**`NiagaraPermissionGrant`/`NiagaraPermissionGroup`** (`NiagaraPermissionGrant.java:8-16`,
`NiagaraPermissionGroup.java:8-11`) are meta-annotations: every concrete `Grant*` annotation is itself
`@NiagaraPermissionGrant`-annotated (so `PermissionManager.getPermissions` can recognize it generically via
`annotation.annotationType().isAnnotationPresent(NiagaraPermissionGrant.class)`,
`PermissionManager.java:357`), and every `*Permissions` repeatable-container annotation is
`@NiagaraPermissionGroup`-annotated (`PermissionManager.java:369`, handling the repeated-annotation
unwrapping case). `NiagaraPermissionGrant.Type` (`STATION`/`WORKBENCH`/`ALL`) is the SAME enum
`NiagaraPermission.environmentType` uses (§8.1) — a module can scope a grant to station-only or
workbench-only via e.g. `@GrantRuntimeExecPermission(value=..., type=STATION)`.

## 8.3 — Module census: 89 of 247 shipped N5 modules declare at least one permission grant `[CERT]`

A Python scan (`census.py`, this session) opened every `module-info.class` inside all 247 jars under
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/` and searched the raw class-file bytes for the
7 annotation-name UTF-8 constant-pool strings (a valid presence check — an annotation reference in a
`RuntimeVisibleAnnotations` attribute always carries its type name as a `CONSTANT_Utf8` entry). `[CERT]`
verbatim script output:

```
total jars: 247
jars with module-info.class: 242
jars with >=1 grant annotation: 89

GrantFilePermission: 60
GrantKeyRingPermission: 22
GrantNiagaraBasicPermission: 52
GrantRuntimeExecPermission: 13
GrantKeyStorePermission: 38
GrantPublicNiagaraBasicPermission: 9
GrantSigningPasswordPermission: 2
```

5 jars have no `module-info.class` at all (not decompiled/identified this session — likely resource-only or
legacy-shim jars → not pursued, out of scope). `GrantFilePermission` is the single most-requested annotation
(60 modules — expected, since file access is the broadest-denied-by-default surface per §8.4/§8.5), followed
by `GrantNiagaraBasicPermission` (52) and `GrantKeyStorePermission` (38, expected given N5's TLS/crypto
surface — fox, jetty, rdb\*, saml\*, platCrypto, clientCertAuth all appear in the per-jar hit list).
`GrantSigningPasswordPermission` is the rarest (2 jars: `platCrypto.jar`, `signingService.jar` — both exactly
the modules that plausibly own other modules' signing passwords).

**Caveat on "third-party" framing.** All 89 hits are modules Tridium itself SHIPS in this stock N5 beta
distribution (drivers like `bacnet.jar`/`abstractMqttDriver.jar`/`opcUaClient.jar`, cloud connectors like
`cloudLink*.jar`, DB drivers like `rdbMySQL.jar`) — every one of them is `com.tridium.`/`niagara.`-namespaced
internally and therefore ELIGIBLE for the core-only Grant annotations (§8.1's `isAnnotationPermitted` gate).
This census does **not** contain a genuinely third-party (non-Tridium) module, since none ships in this
directory — it answers "how does Tridium's OWN driver/integration catalog use the annotation mechanism",
not "what does a real third-party vendor module request". The 5 core-only annotations (`GrantFilePermission`,
`GrantKeyRingPermission`, `GrantNiagaraBasicPermission`) dominate the census (60/22/52 hits) precisely
because these are core modules that qualify for them; a real third-party module restricted to the 4 public
annotations (§8.1) would show a very different, narrower profile — this is the direct, mechanized
confirmation of §8.1's `isAnnotationPermitted` code-reading, not a separate independent measurement.

## 8.4 — Default third-party-LIBRARY grant table: `initThirdPartyPermissions()`, 28 grants across 20 module names `[CERT]`

This is the gap B3-G3 asked for directly: N5's equivalent of N4's 271-line `bin/policy/java.policy`. It is
**not** a file — it is a Java static method, `PermissionManager.initThirdPartyPermissions()`
(`PermissionManager.java:156-230`), run once from the class's static initializer
(`PermissionManager.java:425-427`, `static { initThirdPartyPermissions(); }` — i.e. it runs the first time
any code touches the `PermissionManager` class, unconditionally, no config file gating it). It calls the
private helper `addPermissions(String moduleName, NiagaraPermission...)` (`PermissionManager.java:232-242`)
**28 times**, covering **20 distinct hardcoded module names** (`grep -c`/`grep -oP` this session, cross-checked
against a full manual read of the method body):

| Module name granted-to | Permissions | `[CERT]` line |
|---|---|---|
| `org.bouncycastle.provider`, `.tls`, `.fips.core`, `.fips.tls` (×4) | `MANAGE_SECURITY_PROVIDERS` + `KeyStorePermission("*","all")` | `:157-160` |
| `org.eclipse.jetty` | `KeyStorePermission("*","all")` | `:161` |
| `org.eclipse.jetty.ee11.webapp` | read `jre/conf/jaxp.properties` | `:162` |
| `org.eclipse.jetty.io` | `KeyStorePermission("*","all")` + read `jre/conf/net.properties` | `:163-165` |
| `org.eclipse.jetty.server` | read `net.properties` + `jaxp.properties` | `:166-170` |
| `org.eclipse.jetty.util` | read `net.properties`/`jaxp.properties`/`jre/lib/jfr`, read+write `default.jfc`/`profile.jfc` | `:171-178` |
| `org.eclipse.jetty.websocket.common` | `MANAGE_MAX_PRO` | `:179` |
| `org.eclipse.jetty.xml` | read `jaxp.properties` | `:180` |
| `jxbrowser` | exec + rw its own install dir + rw crash-dump dir + `KeyStorePermission("*","all")`, **+OS-conditional**: Windows adds rw `%LOCALAPPDATA%\JxBrowser`; Linux adds exec `/usr/bin/ldd` + rw `~/.config/jxbrowser` | `:181-203` |
| `org.hsqldb` | rw `${protected.station.home}/hsqldb/-` | `:205` |
| `orientdb.core`, `orientdb.server` (×2) | rw `${protected.station.home}/orientSystemDb/-`, **+Linux-only**: read `/proc/self/cgroup` + exec `/usr/bin/id` | `:206-212` |
| `org.jnrproject.posix` | **Linux-only**: exec `/usr/bin/id` | `:213` |
| `jakarta.mail` | read `jre/conf/*` | `:216` |
| `org.apache.commons.compress` | rw `*` (**all files**) | `:217` |
| `org.apache.poi.poi`, `.ooxml` (×2) | rw 3 template dirs under `niagara.user.home` | `:218-229` |

`[CERT]` every row read verbatim from `PermissionManager.java:156-230` this session. Two entries are
notable outliers: `org.apache.commons.compress` gets an unrestricted `FilePermission("*", "read,write")` —
the single broadest file grant in the whole table — and the OS-conditional blocks (`:188-203`,
`:208-213`) show the grant table itself branches on `OperatingSystemEnum.isOS(...)`, something no static
`.policy` file could express. This table answers B3-G3's exact question ("does it deny
`RuntimePermission "modifyThread"`/JDK-executor use") only NEGATIVELY-BY-ABSENCE: no thread/executor-related
permission appears anywhere in `initThirdPartyPermissions()`, and no `NiagaraPermission` subclass in §8.1
models JDK thread/executor access at all — the N5 permission model has **no equivalent surface** for that
N4 `SecurityManager` check ([Block 3] §3.10's virtual-thread negative finding is therefore `[INFER]`
UNCHANGED by this block: absence of a matching permission class is consistent with, but does not prove,
policy-driven avoidance — it may simply never have been modeled because virtual threads/executors were
never a target of the new agent's instrumentation scope, §8.5). This narrows but does not close
[Block 3]'s child gap B3-G3 on that specific sub-question; the general grant-table half of B3-G3 is now
CLOSED.

## 8.5 — Check path: ByteBuddy advice → `SecurityBridge`/`PermissionBridge` → `PermissionManager` → `StackWalker` caller resolution `[CERT]`

**Agent install.** `nre.jar` manifest `Premain-Class: com.tridium.nre.security.advice.SecurityAgent`
([Block 3] §3.8, re-confirmed this session). `SecurityAgent.premain(String, Instrumentation)`
(`SecurityAgent.java:12-190`) builds **5** separate ByteBuddy `AgentBuilder.Default` instrumentation passes,
each `RedefinitionStrategy.RETRANSFORMATION` + `TypeStrategy.REDEFINE`, each excluding `net.bytebuddy.*`
itself from matching:

| Target JDK type(s) | Matched method(s) | Advice class | `[CERT]` line |
|---|---|---|---|
| `java.nio.channels.SocketChannel` | `open` | `NetworkConnectionAdvice.ForSocketChannel` (exit) | `:17-21` |
| `java.net.Socket` | `connect` (declared by `Socket`) | `NetworkConnectionAdvice.ForSocket` (exit) | `:26-32` |
| `java.net.DatagramSocket` | `connect` or `send` | `NetworkConnectionAdvice.ForDatagramSocket` (exit) | `:33-38` |
| `java.lang.ProcessBuilder` | `start()` (0-arg) | `ProcessBuilderAdvice` (enter) | `:39-44` |
| 17 named crypto-provider classes (`isInstalledProvider()`) | `clear/load/remove/merge/removeService/put*/replace*/compute*` | `SecurityProviderAdvice` (enter) | `:46-64,163-181` |
| `java.security.Security` | `addProvider`/`insertProviderAt`/`removeProvider` | `SecurityProviderAdvice` (enter) | `:65-76` |
| `java.io.File` | `createNewFile/mkdir/mkdirs/renameTo/set*/delete/deleteOnExit` | `FileAccessAdvice.ForFileWrite` (enter) | `:81-94` |
| `java.io.File` | `createTempFile` (3-arg) | `FileAccessAdvice.ForCreateTempFile` (enter) | `:95` |
| `java.io.FileInputStream` | ctor(File) | `FileAccessAdvice.ForReadWithFileArgument` (enter) | `:97-106` |
| `java.io.FileOutputStream` | ctor(File, ..) | `FileAccessAdvice.ForWriteWithFileArgument` (enter) | `:107-116` |
| `java.io.RandomAccessFile` | ctor(File, ..) | `FileAccessAdvice.ForRandomAccessFile` (enter) | `:117-126` |
| `java.util.zip.ZipFile` | ctor(File, .., ..) | `FileAccessAdvice.ForReadWithFileArgument` (enter) | `:127-136` |
| 4 named `FileSystemProvider` impls (`isFileSystemProvider()`) — Windows/Unix/Zip/Jrt | `newByteChannel/newFileChannel` | `FileAccessAdvice.ForFileSystemProviderNewChannel` (enter) | `:137-143,184-189` |
| (same 4) | `newDirectoryStream` | `FileAccessAdvice.ForReadWithPathArgument` (enter) | `:143` |
| (same 4) | `createDirectory`/`implDelete` | `FileAccessAdvice.ForWriteWithPathArgument` (enter) | `:145-147` |
| (same 4) | `copy` | `FileAccessAdvice.ForCopy` (enter) | `:148` |
| (same 4) | `move` | `FileAccessAdvice.ForMove` (enter) | `:149` |
| `java.nio.file.Files` | `mismatch` | `FileAccessAdvice.ForMismatch` (enter) | `:151-152` |
| `sun.awt.SunToolkit` | `createImage`/`getImage` (String arg) | `FileAccessAdvice.ForReadWithStringArgument` (enter) | `:153-159` |

`[CERT]` every row read verbatim from `SecurityAgent.java` this session, matcher-by-matcher — this is the
COMPLETE instrumentation surface (the whole 190-line `premain` body was read, not sampled).

**Advice bodies are thin — all delegate through `SecurityBridge`/`PermissionBridge`.** Every `FileAccessAdvice`
nested class (13 of them, full file read: `ForCopy`, `ForCreateTempFile`, `ForFileRead`,
`ForFileSystemProviderNewChannel`, `ForFileWrite`, `ForMismatch`, `ForMove`, `ForRandomAccessFile`,
`ForReadWithFileArgument`, `ForReadWithPathArgument`, `ForReadWithStringArgument`, `ForWriteWithFileArgument`,
`ForWriteWithPathArgument` — `FileAccessAdvice.java:18-241`) follows the identical shape: check
`SecurityBridge.isInitialized()` (short-circuit if the bridge isn't up yet, e.g. very early boot), extract a
path string from the advised method's argument(s)/receiver, call
`SecurityBridge.permissionBridge.checkPermission(SecurityBridge.permissionBridge.getFilePermission(path,
"read"|"write"))`. `ProcessBuilderAdvice.enter` (`:9-18`) and `SecurityProviderAdvice.enter` (`:6-13`) follow
the same pattern for `RuntimeExecPermission`/`NiagaraBasicPermission.MANAGE_SECURITY_PROVIDERS_PERMISSION`
respectively. `PermissionBridge implements IPermissionBridge`
(`PermissionBridge.java:15-72`) is the concrete bridge singleton, and its `checkPermission(Object)`
(`:18-25`) is a 1-line delegate to `SecurityUtil.checkPermission((NiagaraPermission)niagaraPermission)`.

**`SecurityUtil.checkPermission` resolves a SET of caller modules via `StackWalker`, not a single caller** —
directly answering B3-G4's "caller Module resolution" sub-question: `SecurityUtil.java:230-234` is a 1-line
gate (`if (!PermissionUtil.isTrustedDomain) consumePrivilegedModules(permission::isGrantedTo)`);
`consumePrivilegedModules` (`:322-333`) walks the live call stack with
`StackWalker.getInstance(Option.RETAIN_CLASS_REFERENCE)`, `takeWhile`-ing frames through `isPrivileged`
(`:335-355`) — a hand-rolled "privileged frame" boundary detector that stops the walk 2 frames after it sees
either `niagara.nre.util.SecurityUtil.doPrivileged` or `java.security.AccessController.doPrivileged` on the
stack, and skips `Class.forName` frames outright — then `.map(frame ->
frame.getDeclaringClass().getModule())` `.collect(Collectors.toSet())` to build the module SET, and finally
calls `permission.isGrantedTo(module)` (→ `PermissionManager.checkPermission`) for **every** module in that
set. This is a direct structural echo of the OLD `AccessControlContext`/`ProtectionDomain` intersection
semantics REMITTANCE `niagara-research` B18 documents for N4's `SecurityManager` — the "walk privileged
frames, collect every distinct code source involved, and deny if ANY of them lacks the permission" shape
survives the SecurityManager→agent migration essentially intact, just re-keyed from `CodeSource` to
`java.lang.Module`.

**`PermissionManager.checkPermission(NiagaraPermission, Module)`** (`PermissionManager.java:51-139`) is the
actual decision point, in order:
1. `PermissionUtil.isTrustedDomain` short-circuit-allow (`:53-55`).
2. Test-mode bypasses for `niagara.test`/`niagara.tridiumTest`/`org.testng`/`privilegedaccessor`/
   `org.mockito`/`mock.client`/any module ending `Test` (`:57-72`, only when `Bootstrap.isTest()`).
3. Unnamed-module hard-deny: `throw new PermissionException("unnamedModule", ...)` (`:75-77`).
4. **Universal bypass for platform/core modules**: `niagara.nre`, `niagara.baja`, `niagara.niagarad`,
   `net.bytebuddy.agent`, and any module name prefixed `java.`/`javax.`/`jdk.`/`javafx.` are ALWAYS granted,
   no check performed (`:79-88`) — this is the module-identity list a caller must be IN to skip the whole
   mechanism.
5. A `Map<Pair<Module,NiagaraPermission>, Boolean>` LRU-style cache (`CacheMap<>(2048)`,
   `PermissionManager.java:41`) short-circuits repeat checks (`:90-99`).
6. On a cache miss: `permission.doIsGrantedTo(module)` — the subclass-specific logic from §8.1's table; a
   caught `PermissionException` is cached as `false` (only if `permission.isInitialized()`, `:110-115`) and
   rethrown; success is cached as `true` (`:101-106`).
7. **Denial handling** (`:119-137`, outer catch): audits via `SecurityUtil.getSecurityAuditor().audit(new
   SecurityAuditEvent("Permission Check", moduleName, permission.toString()))`, conditionally logs to
   console (`niagara.permissions` logger at `FINE`) and/or to a per-run debug FILE (§8.6), then **rethrows the
   `PermissionException` UNLESS `PermissionUtil.permissionChecksDisabled`** (`:134-136`) — the exact fork
   point for §8.6's developer mode.

`getPermissions(Module, Class<? extends NiagaraPermission>)` (`PermissionManager.java:349-398`) is where the
annotation-reading happens: `module.getAnnotations()` under `SecurityUtil.doPrivileged` (`:356`), filtered
by `NiagaraPermissionGrant`/`NiagaraPermissionGroup` meta-annotation presence (§8.2), each converted via
`PermissionFactory.makeNiagaraPermission` and cached per-module in the `modulePermissions` map — this is a
lazy, per-module, computed-once cache (`ConcurrentHashMap.computeIfAbsent`, `:351-395`), distinct from the
static `initThirdPartyPermissions()` table (§8.4), which is seeded once at class-init for a FIXED list of
library module names rather than read from any module's own annotations.

## 8.6 — Modes: enforced by default; one license-gated "developer" bypass; no separate "warn" mode `[CERT]` / `[CERT-doc]`

There are exactly **two** runtime postures, not three — no dedicated "warn" mode exists as a first-class
concept; the doc's own vocabulary ("Disabling Permission Checks") confirms this is framed as an
enable/disable toggle, not a 3-way enforce/warn/off switch:

1. **Enforced (default).** `PermissionUtil.permissionChecksDisabled = false` (`PermissionUtil.java:6`,
   its declared default) — every denial throws `PermissionException` synchronously at the call site
   (§8.5 step 7).
2. **Developer mode (opt-in, license-gated).** Wired at boot in `com.tridium.sys.Nre`
   (`baja.jar`, decompiled this session): `Nre.java:938-948` reads
   `Boolean.getBoolean("niagara.permissions.disable")`, and if true, calls
   `licenseManager.checkFeature("tridium", "developer")` — **failing that check logs a WARNING and does
   NOT disable checks** (`Nre.java:948`, "not licensed for it") — then, only on success, calls
   `PermissionManager.disablePermissionChecks()` (`PermissionManager.java:141-145`), which itself requires
   the caller already hold `NiagaraBasicPermission.DISABLE_PERMISSION_CHECKS_PERMISSION` (a
   circularity that is only satisfiable because this call happens from `Nre`/`niagara.baja`, one of the
   universally-bypassed core modules in §8.5 step 4) and starts the debug log file
   (`initDebugLogFile()`, `:285-317`). `[CERT-doc]` exactly matches:
   `docDeveloper.jar:doc/security/niagaraPermissions.html` — "The first requirement to disable permission
   checks is to have the developer license feature... set the `niagara.permissions.disable` system
   property... present at boot" — `[CERT]` code confirms the property name, the license feature string
   `("tridium","developer")`, and the boot-only timing (it is read once in `Nre`'s startup path, not
   polled) all match the doc's claims exactly.

**In developer mode, checks still RUN — only the throw is suppressed.** `PermissionManager.java:119-137`
shows the exception is still constructed, audited, and (conditionally) logged EVERY time; only the final
`throw var20` is skipped when `permissionChecksDisabled` is true. This is precisely
`docDeveloper.jar:doc/security/niagaraPermissions.html`'s own framing: "doesn't actually disable permission
checks completely. The checks still happen, but instead of throwing... the exception is logged to a file."
`[CERT-doc]` = `[CERT]` here — a clean cross-check, no contradiction.

**One concrete code/doc disagreement, flagged per instruction.** The doc states the developer debug log is
named `developerNiagaraPermissionLog-<STATION|WORKBENCH|DAEMON>-<DATE>-<TIME>.txt` (e.g.
`developerNiagaraPermissionLog-STATION-20260827-085850.txt`). The actual code
(`PermissionManager.java:285-288`) builds the filename as `"developerNiagaraPermissionLog-" +
LocalDateTime.now().format("yyyyMMdd-HHmmss")` — **no `STATION`/`WORKBENCH`/`DAEMON` process-type token
appears anywhere in the format string this session's decompile produced.** Per the code-wins-for-behaviour
rule: the actual on-disk filename this build produces is `developerNiagaraPermissionLog-<yyyyMMdd-HHmmss>.txt`
without a process-type segment; the doc's example filename does not match what 5.0.0.28's `PermissionManager`
class will write. This could be a doc that describes a different/later build, or a process-type prefix
applied by a caller not traced this session (`initDebugLogFile()`'s only caller found this pass is
`disablePermissionChecks()` itself, with no process-type parameter threaded through) — recorded as an open
discrepancy, not resolved. → informs child gap **B8-G2**.

**No config-file "policy" exists to hand-tune individual grants** — the only external control surface for
the WHOLE mechanism is the single boolean `niagara.permissions.disable` system property (all-or-nothing);
per-module grants are fixed at compile time (annotations, §8.2) or hardcoded (`initThirdPartyPermissions`,
§8.4) — there is no N5 equivalent of editing `bin/policy/java.policy` by hand.

## 8.7 — B3-G4: N4's ~25-group taxonomy has NO clean 1:1 mapping onto N5's 8-class taxonomy `[CERT]` / synthesis

REMITTANCE `niagara-research` B18 §18.4.4 corrects B3(niagara-research)'s original 19-group count to **~25**
distinct `NiagaraPermissionGroup` names in N4.14, of which exactly 3 (`ACCESS_CLASS`, `REFLECTION`,
`MBEAN_PERMISSION`) always require code-signing regardless of `verificationMode`. Mapping that list against
this block's §8.1 8-class N5 taxonomy:

| N4 group (B18 §18.4.4) | N5 equivalent | Fit |
|---|---|---|
| `NETWORK_COMMUNICATION` (hosts, ports, type, SSLSockets) | **none** — `NetworkConnectionAdvice` audits only, no `NiagaraPermission` gates a connection at all (§8.8) | **NO equivalent — a genuine coverage GAP, not a rename** |
| `SYSTEM_PROPERTIES` (properties, actions) | **none found** — no `SystemPropertyPermission`-shaped class exists among the 8 | **NO equivalent found this session** |
| `LOAD_LIBRARIES` (libraries) | **none found** — no native-library-load gate class identified | **NO equivalent found this session** |
| `RUNTIME_EXECUTION` (files) | `RuntimeExecPermission` | **Close match** (public-tier, §8.1 #7) |
| `KEY_STORE` | `KeyStorePermission` | **Close match** (public-tier, §8.1 #6) |
| `MANAGE_SERVER_TRUST_ANCHORS` | `PublicNiagaraBasicPermission("MANAGE_SERVER_TRUST_ANCHORS")` | **Direct 1:1 rename** — confirmed both by decompile (`PublicNiagaraBasicPermission.java:12-13`) and by `docDeveloper.jar` doc text |
| `SET_SYSTEM_TIME` | `PublicNiagaraBasicPermission("SET_TIME")` | **Direct 1:1, renamed** `SET_SYSTEM_TIME`→`SET_TIME` |
| `BACKUPS` (actions) | `PublicNiagaraBasicPermission("RESTORE_BACKUP")` | **Close match, narrowed to restore-only** (N4's had `actions`, i.e. multiple backup verbs; N5's public constant list has no separate BACKUP-create verb) |
| `CLOUD_BEARER_TOKEN` | `NiagaraBasicPermission.CLOUD_TOKEN`/`CLOUD_IDENTITY` (core-only, `NiagaraBasicPermission.java:84-87`) | **Renamed + moved to core-only tier** — no longer public-requestable at all |
| `ACCESS_CLASS` / `REFLECTION` / `MBEAN_PERMISSION` (the 3 always-signed N4 groups) | **none found** — no reflection/classloading/JMX gate class exists among the 8 | **NO equivalent found this session — the always-signed tier has no visible N5 analogue** |
| `THIRD_PARTY_PERMISSION` (class, name, actions — N4's generic escape hatch for a module to define ITS OWN custom permission) | **structurally impossible in N5** — §8.1 confirms third-party modules cannot create custom permissions at all | **Removed as a category, not renamed** |
| `MODIFY_IO_STREAMS`, `SHUTDOWN_HOOKS`, `GET_ENVIRONMENT_VARIABLES`, `AUTHENTICATION`, `UI`, `SIGNING`, `DIAGNOSTICS`, `MANAGE_EXECUTION`, `LOGGING`, `PROTECTION_DOMAIN` | **none found among the 8 N5 classes** | **NO equivalent found this session** |

**Reading this table honestly**: this is an `[INFER]`-heavy SYNTHESIS section built by comparing two
independently-`[CERT]`-sourced enumerations (N4's from B18, N5's from §8.1 of this block) — a name NOT
appearing on the N5 side is a genuine absence FROM THE 8 CLASSES DECOMPILED THIS SESSION, not proof no
N5 mechanism exists anywhere for that concern (e.g. reflection/JMX access could be gated by a completely
different, non-`NiagaraPermission` mechanism not yet located — negative-existence discipline applies:
`com.tridium.nre.security.**`, the ONLY package tree searched, is where all 8 classes live, and no 9th
subclass was found in a full 126-class listing of that tree, §8.0 sources — but the tree was not searched
for a DIFFERENTLY-NAMED gating mechanism outside it). **Net verdict**: N4's ~25-group taxonomy does NOT map
1:1 onto N5's 8-class taxonomy. Roughly a third renames/relocates cleanly (network-trust-anchors, time,
runtime-exec, keystore); the rest either has no visible N5 equivalent at all (network connections,
system properties, native-library loading, reflection/JMX/class-access — precisely N4's 3 always-signed
groups) or is structurally removed as a category (`THIRD_PARTY_PERMISSION`, since custom permissions no
longer exist). → child gap **B8-G3** (locate whether reflection/JMX/native-library/system-property access is
gated by SOME other N5 mechanism, or is now genuinely unguarded).

## 8.8 — Impact for a third-party module (DashboardPan/ColdRoomPan-style) opening files/sockets/HTTP `[CERT]` / `[INFER]`

Putting §8.1, §8.5, §8.7 together, for a module like DashboardPan (servlet + file I/O) or ColdRoomPan
(control logic, no direct I/O) built as a genuinely third-party N5 module (JPMS name NOT prefixed
`com.tridium.`/`niagara.`):

- **File access is GATED and requires an explicit, per-path `@GrantFilePermission`.** §8.1's
  `isAnnotationPermitted` check applies to `GrantFilePermission` too (it lives in the restricted
  `com.tridium.nre.annotations` package) — **meaning a genuinely third-party module cannot request
  `FilePermission` at all**, the same restriction as `FilePermission` itself (§8.1's table, row 1). A
  third-party module's ONLY sanctioned file I/O is therefore the always-granted shared-directory set
  `FilePermission.getPermissionsGrantedToAllModules()` builds for every module regardless of its own grants
  (`FilePermission.java:210-236`): `${niagara.user.home}/shared/-` and `${protected.station.home}/shared/-`
  (read/write/all), `logging/-`, the JVM temp dir, and READ-only access to `modules/-`, `lexicon/-`, `etc/-`,
  `jar-cache/-`, `jre/bin/-`, `jre/conf/-`, `bin/ext/-`, `cacerts`. This is EXACTLY the "shared directories"
  doctrine `docDeveloper.jar:doc/security/niagaraPermissions.html` `[CERT-doc]` documents
  (`Sys.getStationHome()`/`Sys.getNiagaraSharedUserHome()`) — confirmed by direct code cross-check, not
  doc-only. Any file DashboardPan wants to read/write OUTSIDE those shared roots is structurally unreachable
  for a third-party module — there is no annotation path to request it.
- **Network sockets are effectively UNGATED — a finding, not a doc restatement.** §8.5's table and §8.7's
  synthesis both land on the same negative: `NetworkConnectionAdvice` (`NetworkConnectionAdvice.java:1-65`,
  full file read) instruments `Socket.connect`, `DatagramSocket.connect`/`.send`, and
  `SocketChannel.open` — and EVERY advice body calls only `SecurityBridge.permissionBridge
  .auditNetworkConnection(...)` (an AUDIT LOG call, `PermissionBridge.java:39-46`), never
  `checkPermission(...)`. A `grep`-equivalent full-file read of `NetworkConnectionAdvice.java` found **zero**
  `checkPermission` call sites (contrast with `FileAccessAdvice`'s 13 advice classes, EVERY one of which
  calls `checkPermission`). This means a third-party module opening an outbound HTTP/HTTPS connection (e.g.
  DashboardPan calling a cloud API) faces **no `PermissionException` at the socket layer at all** — only a
  post-hoc audit-log entry naming the first non-core module in the call stack
  (`PermissionBridge.getFirstRelevantModuleInStack`, `:48-60`). This is a genuinely SURPRISING finding
  relative to N4's `NETWORK_COMMUNICATION` group (§8.7, which DID enforce host/port/SSL constraints under an
  enforcing `SecurityManager`) — N5's network-access model DOWNGRADES from enforcement to observability-only
  for the exact same surface. `[CERT]` for the code fact; `[INFER]` for "this is a real regression in
  practice" — it is possible N5 gates outbound HTTP at a different, higher layer (e.g. `okhttp3`'s own
  interceptor chain, or a Jetty client wrapper never touched this session) not covered by this block's
  `com.tridium.nre.security.**` search scope → child gap **B8-G4**.
- **`Runtime.exec()`/`ProcessBuilder` IS gated and requestable.** `RuntimeExecPermission` is public-tier
  (§8.1 #7) — a third-party module CAN request `@GrantRuntimeExecPermission` for a specific executable path,
  scoped `STATION`/`WORKBENCH`/`ALL`. Unlike file access, this is a genuinely open door for a third-party
  module with a legitimate need (e.g. shelling out to a codec/CLI tool), gated per-path via
  `RuntimeExecPermission.impliedBy` (`RuntimeExecPermission.java:85-105`, supports exact-path,
  trailing-`*`-sibling, and trailing-`-`-recursive grant shapes, mirroring `FilePermission`'s own three
  shapes).
- **Managing security providers, reading/writing keystores, restoring backups, RDB connections, renaming the
  station**: all public-tier (`PublicNiagaraBasicPermission`'s 5 named constants, `KeyStorePermission`) and
  requestable by any module — the doc's worked example (§8.2) is literally a third-party module requesting
  `MANAGE_SERVER_TRUST_ANCHORS` + a keystore read grant.

**Net for DashboardPan/ColdRoomPan specifically**: a servlet-style module doing file I/O must scope its
writes to `${protected.station.home}/shared/` or explicitly declare `@GrantFilePermission` — but since that
annotation is core-only (§8.1), a genuinely third-party DashboardPan **cannot** request arbitrary file paths
at all under this model; it is confined to the shared-directory allowlist by construction, not by choice.
Any outbound HTTP call it makes (cloud sync, webhook) passes uninspected except for an audit-trail entry.
ColdRoomPan-style pure control logic (no file/socket/process I/O) is essentially unaffected by this whole
mechanism — it never trips any of the 19 instrumented JDK entry points in §8.5's table.

## Self-verify

`toolbelt/verify-block.sh niagara5-block8.md` (this session, verbatim):
```
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 3  (adj 2)
   [CERT-live] 0
   [CERT] 22  (adj 20)
   [CERT-doc] 10  (adj 8)
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 5  (adj 4)
-- ratio -- [INFER]/[CERT*] = 4/30 = 0.13
-- [CERT] file:line citation resolution --
   resolved 0 of 48
   WARN    resolved 0 of 48 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```
**Declared per METHODOLOGY §11's decompiled-tree rule**: `verify-block: 0 resolved (all extern — decompiled
trees under /tmp/claude-1000/n5b8/decompiled/, ephemeral scratch, re-derivable from the jars cited in the
header); citation gate = inline token-verify`. The two `[CERT-hw]` raw hits are NOT claims made by this
block — both are forward references naming the marker inside child-gap descriptions (B8-G4, B8-G5) for
FUTURE live-hardware work; zero `[CERT-hw]` claims are asserted as already-verified here.

**Inline token-verify**: every one of the 48 `file:line` citations above points at a class this session
itself decompiled (§8.0 Method) and then directly `Read` with line numbers before citing it — not a single
citation was written from memory or inferred from a class/method NAME without opening the body. Spot-check
tokens independently re-`grep`-confirmed against the decompiled source this session (whitespace-normalized):
`niagara.permissions.disable` (`Nre.java`, §8.6), `DISABLE_PERMISSIONS_CHECKS`/`MANAGE_SECURITY_PROVIDERS`
(`NiagaraBasicPermission.java`, §8.1/§8.4), `auditNetworkConnection` (`PermissionBridge.java`/
`NetworkConnectionAdvice.java`, §8.8 — confirmed present in the bridge, confirmed ABSENT from a full-file
read of the 3 network advice classes alongside zero `checkPermission` hits, §8.8's central negative
finding). Token-verify: **48/48** citations token-checked present in their cited decompiled source this
session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block. The 2 `[CERT-doc]` sources
(`niagaraPermissions.html`, `requestingPermissions.html`) are LOCAL files already shipped inside
`docDeveloper.jar` (opened via `zipfile`, not fetched from the web) — no snapshot-registration step applies;
they are cited by their exact in-jar path, which is itself the permanent, re-derivable locator.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block8.md`. `INDEX.md`/
`RESEARCH-STATE.md`/`CATALOG.md` regeneration and backlog re-classification are left to the orchestrator (out
of this read-only research task's scope — this task was scoped to produce ONE block file only, per the
caller's instruction to touch no other file).

## 8.x — Child gaps opened

- **B8-G1** — Trace where `ModifyProtectedPropertiesPermission` instances are actually CONSTRUCTED (its
  `trustedModules` set is a constructor argument, not a static list) — outside `com.tridium.nre.security.**`,
  not searched this session. Answers which modules are hardcoded-trusted to modify "protected"/readonly
  properties.
- **B8-G2** — Resolve the `developerNiagaraPermissionLog` filename code/doc discrepancy (§8.6): does a
  process-type token (`STATION`/`WORKBENCH`/`DAEMON`) get threaded into `initDebugLogFile()` from a caller
  not traced this session, or does the doc describe a different/later build than 5.0.0.28?
- **B8-G3** — Locate whether N4's `ACCESS_CLASS`/`REFLECTION`/`MBEAN_PERMISSION`/`SYSTEM_PROPERTIES`/
  `LOAD_LIBRARIES` concerns (the always-signed tier + 2 others) are gated by ANY N5 mechanism outside
  `com.tridium.nre.security.**`, or are now genuinely unguarded in N5's boot module layer.
- **B8-G4** — Confirm (or refute) that outbound HTTP/HTTPS from a third-party module is truly ungated in
  N5 by checking whether `okhttp3`'s own interceptor chain, or a Jetty HTTP client wrapper, applies a
  `NiagaraPermission` check `NetworkConnectionAdvice` itself does not (§8.8) — ideally cross-checked
  `[CERT-hw]` against a live N5 station with a deliberately unprivileged third-party module attempting an
  outbound call.
- **B8-G5** — `[CERT-hw]` reproduction: install a minimal third-party test module with NO grants, attempt a
  file write outside the shared directories, and confirm the exact `PermissionException` message/stack shape
  §8.5 predicts, live against the 5.0.0.28 station.

## 8.x — Connections

- **[Block 3] §3.8** — this block's direct parent; closes the "concrete grant table" half of child gap
  **B3-G3** (§8.4) and the "network-access avoidance" half of B3-G3 stays open (§8.4's closing paragraph).
  §3.5's `--add-exports niagara.nre/com.tridium.nre.security.permissions.restricted=niagara.niagarad` names
  the exact package §8.5/§8.6's `PermissionUtil` class lives in.
- **REMITTANCE → `niagara-research` B635** (N4 module-anatomy MA7, `readPermissions`/`ModuleClassLoader`/
  `GrantAllPermissionGroupStore`) — the N4-side mechanism this whole block replaces; §8.2's "annotations
  replace `<permissions>` XML outright" finding is the direct structural successor to B635's Track-1/Track-2
  XML-element model.
- **REMITTANCE → `niagara-research` B18 §18.4.4** — the corrected ~25-group N4 taxonomy §8.7 maps against;
  also the 3-always-signed-groups finding that has no visible N5 analogue.
- **[N5-G1]** (module packaging) — §8.3's census (89/247 modules, `module-info.class` annotation presence)
  is a ready-made data point for that gap's fuller module-inventory work.
- **[N5-G9]** (security/authn surface, per [Block 3] §3.11) — §8.4's `initThirdPartyPermissions()` table
  names several of that gap's candidate integrations directly (`cloudLink`, `saml`, TLS/keystore surface).
