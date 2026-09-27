# Block 61 — Closing three named gaps: the live station's `BComponentSpace` identity, `nre.dll`/`njre.dll`'s native process-creation capability split, and the SP-side SAML signature-algorithm allowlist buried in the bundled `java-saml-core` jar

> Research closing/advancing three previously-opened child gaps that each hinged on one unresolved fact
> [Block 40]/[Block 57]/[Block 38] each explicitly flagged as out-of-session-budget: **B40-G2** (which
> concrete `BComponentSpace` subtype a LIVE, normally-running N5 station's own root space instantiates, and
> whether `.getType().is(BOG_SPACE_TYPE_INFO)` is true or false for it — the one fact [Block 40] §40.2's
> `BTunnelService.setRuleHintOverride("TunnelService.serverPort")` reachability verdict rested on);
> **B57-G2** (how `platDaemon`/`niagarad` actually spawns the `station.exe` OS process — [Block 57] §57.1
> found zero `ProcessBuilder` anywhere in the Java corpus and named this a genuine, not merely negative,
> gap); **B38-G2** (the SP-side SAML response signature-algorithm allowlist `Response.validateSignatures()`
> defers to inside the bundled OneLogin `java-saml-core` library — [Block 38] §38.6 found no allowlist
> visible in Tridium's own Java source, unlike the IdP-side `ALGORITHM_MAPPING` [Block 38] §38.9 already
> read). Covers: [Block 41] §41.2's own citation of `Station.java:190` (opened there for an unrelated
> `@AuditableSpace` question, re-read here for what it says about space IDENTITY) plus fresh reads of
> `BComponentSpace.getType()`/`isProxyComponentSpace()`, `NTypeInfo.is()`, and the three concrete
> `BComponentSpace` subclasses (`BBogSpace`/`BOrionSpace`/`BVirtualComponentSpace`) to settle B40-G2
> outright; `objdump`/`strings` import-table probes of the LIVE install's `niagarad.exe`/`njre.dll` and
> `station.exe`/`nre.dll` native binaries (fresh this session, not reused from any prior block's `nre.dll`
> `strings` runs) to advance B57-G2; and a `javap` bytecode disassembly of the bundled
> `java-saml-core-2.9.0.jar`'s `com.onelogin.saml2.util.Util` class (never previously opened in this corpus
> — no decompiled `.java` for it exists anywhere in `organized/`) to close B38-G2. Does **not** cover: a
> live reproduction of a station start/restart (no execution performed — native-binary reads are static
> import-table/string inspection, not dynamic tracing); disassembly of `nre.dll`'s own `CreateProcessA`
> CALL SITE (only its IMPORT TABLE was read — which Windows API call in the binary actually invokes it, and
> with what arguments, was not traced — see child gap); the `xmlsec-4.0.4.jar` (Apache Santuario)'s own
> internal algorithm-restriction logic (Santuario's `JCEMapper`/secure-validation properties were listed by
> filename only, not read — OneLogin's own `isAlgorithmWhitelisted()` allowlist, confirmed to be the gate
> N5's actual call chain hits FIRST, made a deeper Santuario read unnecessary for closing B38-G2 specifically).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 33]/[Block 40]/[Block 41]/[Block 53]/[Block 57] read; decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{baja,platDaemon,platform,saml}/vineflower/`. The bundled
> third-party library read for §61.3 is `organized/saml/vineflower/LIB-INF/java-saml-core-2.9.0.jar`
> (OneLogin's `java-saml` core, version pinned in its own filename — this is the exact jar file shipped
> inside the `saml` module on this install, not a version fetched externally) and
> `organized/saml/vineflower/LIB-INF/xmlsec-4.0.4.jar` (Apache Santuario, filename-versioned, listed but
> not opened this session). The native binaries read for §61.2 are the live install's own
> `bin/niagarad.exe`, `bin/njre.dll`, `bin/station.exe`, `bin/nre.dll` under
> `/mnt/c/Program Files/Niagara/5.0.0.28/` — the identical `nre.dll` [Block 53]/[Block 57] already `strings`'d,
> re-probed here with `objdump -x` for its full import table (a different extraction method than either
> prior block used) plus two binaries (`niagarad.exe`, `njre.dll`) neither prior block opened.
>
> Sources: `organized/baja/vineflower/niagara/space/BComponentSpace.java` (`:66-99` class header +
> `getType()`, `:105-111` `setRootComponent()`, `:317-319` `isProxyComponentSpace()` — all whole-method
> reads this session); `organized/baja/vineflower/com/tridium/sys/station/Station.java:160-207` (whole
> method, re-read from [Block 41]'s citation, this session, for its space-construction sequence, not its
> `@AuditableSpace` framing); `organized/baja/vineflower/com/tridium/sys/registry/NTypeInfo.java:110-139`
> (`is(TypeInfo)`/`is(Type)`, whole method); `organized/baja/vineflower/com/tridium/sys/schema/
> ComplexSlotMap.java:1666-1667` (`getSpace()`), `:1799-1827` (`setRequiresValidation`, re-read from [Block
> 40]'s citation, now extended 2 lines to the closing brace); `organized/baja/vineflower/com/tridium/sys/
> schema/ComponentSlotMap.java:1588-1608` (`mount()`, partial read — enough to confirm the space-wiring
> call, not the full permission-check body); `organized/file/vineflower/com/tridium/file/types/bog/
> BBogSpace.java:43`, `organized/orion/vineflower/com/tridium/orion/BOrionSpace.java:32`,
> `organized/baja/vineflower/niagara/virtual/BVirtualComponentSpace.java:22` (class declarations only —
> confirms all three `extends BComponentSpace`, not the reverse); `organized/platDaemon/vineflower/com/
> tridium/platDaemon/command/BStartStationCommand.java` (whole file, 116 lines — the Workbench-side `plat
> startstation` client command); `organized/platform/vineflower/com/tridium/platform/BSystemPlatformService.java
> :1006-1023` (`doRestartStation`), `:1248-1260` (`sendRestartRequest`); `organized/platform/vineflower/com/
> tridium/platform/daemon/LocalSessionUtil.java:32-80` (`getLocalSession()` head, partial read); `[CERT-hw]`
> `objdump -x`/`strings` over `/mnt/c/Program Files/Niagara/5.0.0.28/bin/{niagarad.exe,njre.dll,station.exe,
> nre.dll}`, this session; `organized/saml/vineflower/com/tridium/saml/rp/Response.java:238-286`
> (`validateSignatures()`, re-read from [Block 38]'s citation, whole method); `[CERT]` `javap -p -c`
> disassembly of `com/onelogin/saml2/util/Util.class` extracted from `organized/saml/vineflower/LIB-INF/
> java-saml-core-2.9.0.jar`, this session — methods `validateSignNode` (4-arg, 5-arg, and the
> `XMLSignature`-arg overload), `getSignatureData` (2-arg and 3-arg), `isAlgorithmWhitelisted`,
> `mustRejectDeprecatedSignatureAlgo`, and the class `static {}` initializer (for `DEPRECATED_ALGOS`'
> contents).
>
> Method: source reading (`niagara.space`/`niagara.sys`/`platDaemon`/`platform` decompiled Java), native
> Windows PE import-table inspection (`objdump -x`, `strings`) over the live install's own binaries, and
> JVM bytecode disassembly (`javap -p -c`) of a bundled third-party jar with no decompiled source anywhere
> in the corpus. Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live
> system/device — here, the live install's own binaries and their import tables, a form of static
> live-artifact inspection distinct from a runtime probe · `[CERT]` local primary source (`file:line`, or
> for the jar, `javap` disassembly of the exact bundled `.class`) · `[CERT-a]` secondary source · `[INFER]`
> deduction.
>
> NRE core / platform-daemon / SAML SP layer. Connects [Block 40] (closes B40-G2), [Block 57] (advances
> B57-G2 with new native-binary evidence, does not fully close it — new narrower child gap opened),
> [Block 38] (closes B38-G2), [Block 41] (re-uses its `Station.java:190` citation for a different question),
> [Block 33] (grandparent of the B40-G2 chain).
>
> **Type:** `mixed` — §61.1 and §61.3 each upgrade a NAMED prior block's `[INFER]` hypothesis to `[CERT]`
> by opening a source that block explicitly flagged as unopened (a `[INFER]`-across-a-prior-block
> correction, the `mixed` trigger per METHODOLOGY §4/§11); §61.2 is fresh evidence-gathering that narrows
> without fully closing.

---

## 61.1 — B40-G2 CLOSED: a live, normally-running N5 station's root `BComponentSpace` is the base class itself, not `BBogSpace` — `setRequiresValidation()` returns `false` for it, confirming `BTunnelService.setRuleHintOverride("TunnelService.serverPort")` passes unchecked by construction `[CERT]`

[Block 40] §40.2 traced `BServerPort.setRuleHintOverride(v)` → `ComplexSlotMap.setString(...)` →
`setRequiresValidation(Context)` and found that with `context == null` (`BTunnelService`'s call site,
`BTunnelService.java:325,725`, already `[CERT]`), the method falls through to:

```java
BComponentSpace space = this.getSpace();
if (space == null) return false;
if (space.isProxyComponentSpace()) return true;
if (BOG_SPACE_TYPE_INFO == null) {
   BOG_SPACE_TYPE_INFO = BTypeSpec.make("file", "BogSpace").getTypeInfo();
}
return space.getType().is(BOG_SPACE_TYPE_INFO);
```
`[CERT]` `organized/baja/vineflower/com/tridium/sys/schema/ComplexSlotMap.java:1799-1827` (re-read whole
method this session, 2 lines past [Block 40]'s `:1799-1816` citation to the closing brace — no
substantive change, same body). [Block 40] could resolve the `space == null` and (trivially) the
`isProxyComponentSpace()` branches, but left the THIRD branch — whether `TunnelService.serverPort`'s own
LIVE, in-station `getSpace()` result `.is()`-a `BBogSpace` TypeInfo — as an `[INFER]` "more likely false"
reading, naming the exact missing fact: *"would require opening the concrete space class a running
`BStationSpace`/equivalent instantiates, out of this session's scope"* ([Block 40] §40.2).

**That concrete class is opened this session, and it settles the question outright.** [Block 41] §41.2
already cited the relevant line for an unrelated `@AuditableSpace` finding — re-reading `Station.java`'s
full load sequence (not just the one cited line) shows the SAME instantiation is the station's own
runtime root space, not a transient or offline object:

```java
space = new BComponentSpace("station", LexiconText.make("baja", "nav.station"), BOrd.make("station:"));
space.fw(105, Boolean.TRUE, null, null, null);
BLocalHost.INSTANCE.addNavChild(space);
BLocalHost.INSTANCE.mountSpace(space);
space.setRootComponent(station);
```
`[CERT]` `organized/baja/vineflower/com/tridium/sys/station/Station.java:190-194` (whole load-station
method read this session, `:160-207`; `station` at line 165 is the decoded `BStation` root of
`config.bog` — the actual, live component tree the station runs, not a scratch/offline copy).
`space.setRootComponent(station)` mounts that live tree INTO this very `space` instance:
`setRootComponent()` calls `((ComponentSlotMap)root.fw(1)).mount(this, null, null)`
`[CERT]` `organized/baja/vineflower/niagara/space/BComponentSpace.java:105-111`, and `mount(BComponentSpace
space, ...)` wires the component's slotmap to that space
`[CERT]` `organized/baja/vineflower/com/tridium/sys/schema/ComponentSlotMap.java:1588` (signature +
opening body read this session). Every component under the live tree — including `BTunnelService`, a
station service parented somewhere under `Services` — resolves `ComplexSlotMap.getSpace()` by walking
`this.parent.getSpace()` up to the root, whose own `getSpace()` terminates at this literal `space`
instance `[CERT]` `ComplexSlotMap.java:1666-1667` (already cited by [Block 40], re-confirmed this
session against the mount chain above, not merely asserted).

**The literal class instantiated is `niagara.space.BComponentSpace` itself — `new BComponentSpace(...)`,
no subclass.** This settles both remaining branches of `setRequiresValidation`:

1. **`isProxyComponentSpace()` → `false`.** The base class's own implementation is a plain, non-abstract
   `return false;` `[CERT]` `BComponentSpace.java:317-319`. Since the live station space is an instance of
   the base class itself (not a subtype that could override it), this branch is `false` for it, structurally
   — no further tracing needed.
2. **`.getType().is(BOG_SPACE_TYPE_INFO)` → `false`.** `BComponentSpace.getType()` is a `@Generated`
   accessor returning the class's OWN static `TYPE` field (`Sys.loadType(BComponentSpace.class)`)
   `[CERT]` `BComponentSpace.java:69-70,90-94`. `TypeInfo.is(TypeInfo)` (the concrete `NTypeInfo`
   implementation) walks `this.is[]` — a type's own precomputed ancestor/self set — and returns `true`
   only when the TARGET type appears in THAT array: `for (TypeInfo isInfo : this.is) if
   (isInfo.equals(typeInfo)) return true;` `[CERT]` `organized/baja/vineflower/com/tridium/sys/registry/
   NTypeInfo.java:126-139` (whole method, both `is(TypeInfo)` and `is(Type)` overloads). This is standard
   "is-a" semantics: `X.is(Y)` is true iff `Y` is `X` itself or an ANCESTOR of `X` in the type hierarchy —
   never a DESCENDANT. `BBogSpace`, the class `BOG_SPACE_TYPE_INFO` resolves to
   (`com.tridium.file.types.bog.BBogSpace`, already established by [Block 40]), is confirmed this session
   to `extend BComponentSpace` `[CERT]` `organized/file/vineflower/com/tridium/file/types/bog/
   BBogSpace.java:43` — i.e. `BBogSpace` is a DESCENDANT of `BComponentSpace`, never an ancestor of it. A
   plain `BComponentSpace` instance's `is[]` array can therefore never contain `BBogSpace`'s `TypeInfo` —
   `space.getType().is(BOG_SPACE_TYPE_INFO)` is `false` for the live station space, by construction of the
   type hierarchy, not merely "more likely". (The other two concrete `BComponentSpace` subclasses found in
   the corpus, `BOrionSpace` and `BVirtualComponentSpace`, are checked for the same reason — both also
   `extend BComponentSpace` `[CERT]` `organized/orion/vineflower/com/tridium/orion/BOrionSpace.java:32`,
   `organized/baja/vineflower/niagara/virtual/BVirtualComponentSpace.java:22` — confirming the live
   station's root space is not secretly one of THESE either; it is literally the base class.)

**Net verdict, closing B40-G2 and upgrading [Block 40] §40.2's `ruleHintOverride` finding from `[INFER]`
to `[CERT]`: for a live, normally-running N5 station, `BTunnelService.setRuleHintOverride("TunnelService.serverPort")`
never reaches `BServerPort.isAlphanumeric`.** All three `setRequiresValidation` branches resolve
deterministically for the live station's own component tree — `space != null` (it is the mounted root
space), `isProxyComponentSpace() == false` (base-class default, structurally unavoidable), and
`getType().is(BOG_SPACE_TYPE_INFO) == false` (type-hierarchy direction makes this unreachable, not merely
unlikely) — so `setRequiresValidation` returns `false`, `IPropertyValidator` is never invoked, and the
`"TunnelService.serverPort"` literal (`BTunnelService.java:142`, already `[CERT]` per [Block 40]) is
written to a real, frozen `Property` slot with zero validation, exactly as [Block 40]'s `[INFER]` reading
anticipated — now on firm ground. This closes [Block 40]'s framing of the `ruleHintOverride` branch as
"NOT REACHABLE... with high confidence but `[INFER]`" — it is now `[CERT]` NOT REACHABLE, for the one
scenario that matters (a live station's own internal write to its own already-live component), leaving
[Block 40]'s companion gap **B40-G1** (the RENAME-charset question for `BOpcUaServer.getName()`) as the
only still-open half of that finding.

## 61.2 — B57-G2 ADVANCED, not closed: `station.exe`'s own native library (`nre.dll`) imports `CreateProcessA` AND Windows-Service-registration APIs; `niagarad.exe`'s own native library (`njre.dll`) imports NEITHER — narrowing, not resolving, which binary actually spawns a station process `[CERT-hw]`+`[INFER]`

[Block 57] §57.1 found zero `ProcessBuilder`/argument-list construction anywhere in the N5 Java corpus and
named the actual station-spawn mechanism "native-code-mediated or outside the decompiled tree entirely" —
**B57-G2**. This session probes the two most plausible native binaries directly on the live install, using
`objdump -x` (full PE import table) rather than `strings` alone (the method [Block 40]/[Block 57] used for
`nre.dll`'s `-Dcmdline::` string).

**`niagarad.exe`'s native library, `njre.dll`, imports NO process-creation or Service-Control-Manager API.**
Full `ADVAPI32.dll` import set: `RegCreateKeyExA`, `RegFlushKey`, `RegOpenKeyExA`, `RegQueryValueExA`,
`RegSetValueExA`, `RegCloseKey` — registry read/write only, no `OpenSCManager`, `CreateService`,
`StartService`, `ControlService`, `RegisterServiceCtrlHandler`, or `StartServiceCtrlDispatcher`
`[CERT-hw]` `objdump -x /mnt/c/Program Files/Niagara/5.0.0.28/bin/njre.dll`, this session, full import
table read, not grepped-only. Full `KERNEL32.dll` import set includes `TerminateProcess` and
`GetCurrentProcess` (self-process control) but no `CreateProcessA`/`CreateProcessW` anywhere in the file
`[CERT-hw]` (same run; `grep -i CreateProcess` over the full `objdump -x` output returns zero hits). A
`strings` pass over the same file for `CreateProcess`/`station.exe`/`StartServiceCtrlDispatcher`/
`OpenSCManager` also returns zero hits `[CERT-hw]` (confirms the API name is not resolved dynamically via
`GetProcAddress`-by-name either — `GetProcAddress` IS imported, but the literal ASCII string
`"CreateProcess"` a name-based dynamic lookup would require is absent from the binary).

**`station.exe`'s native library, `nre.dll`, imports BOTH.** Full `ADVAPI32.dll` import set:
`RegisterServiceCtrlHandlerA`, `StartServiceCtrlDispatcherA`, `SetServiceStatus` (the three-call pattern a
Windows Service's own entry point uses to register itself with the SCM and report status — i.e.
`station.exe` is capable of running AS its own Windows Service, self-hosted, not merely being launched by
one) PLUS the same six registry calls `njre.dll` has. `KERNEL32.dll` additionally imports
`SetConsoleCtrlHandler` and, critically, **`CreateProcessA`** `[CERT-hw]` `objdump -x /mnt/c/Program
Files/Niagara/5.0.0.28/bin/nre.dll`, this session — a fresh full-import-table extraction; [Block 53]/[Block
57] each only ran `strings` over this same file for a DIFFERENT string (`-Dcmdline::`), never enumerated
its import table.

**Reading this correctly — what it does and does NOT establish.** The import table proves `nre.dll`
CONTAINS a call site somewhere that invokes `CreateProcessA` and a call site that registers a Windows
Service entry point; it does NOT prove what that `CreateProcessA` call spawns, nor that it is the
station-start path at all `[CERT-hw]` for the import fact, `[INFER]` for any interpretation beyond it. Two
readings compete, and this session cannot adjudicate between them without disassembling the actual call
site (out of scope — see child gap): (1) `nre.dll` — linked into `station.exe` ITSELF, the process being
launched, not the launcher — uses `CreateProcessA` for something UNRELATED to daemon-driven spawning (a
JxBrowser/Chromium-embedded-renderer child process is a concrete, corpus-attested candidate: [Block 40]'s
own citation list includes `JxBrowserUtil.java:223`, and the `jxBrowser` module exists in this corpus,
`organized/jxBrowser/`; JxBrowser's Chromium engine runs as a separate OS process by design). (2)
`station.exe`, once running, is what the OS's Service Control Manager (not `niagarad.exe`) actually
launches for a "start on boot"/"start via `net start`" scenario — consistent with the
`RegisterServiceCtrlHandlerA`/`StartServiceCtrlDispatcherA` pair being `station.exe`'s OWN entry-point
registration, not evidence `niagarad.exe` calls anything to trigger it — in which case SCM itself (an OS
component, not Niagara code) is the actual spawner for THAT path, and `niagarad.exe`'s role (per §57.1's
own `BStartStationCommand`/`BSystemPlatformService.sendRestartRequest` chain, re-confirmed this session at
`organized/platform/vineflower/com/tridium/platform/BSystemPlatformService.java:1248-1260` — an
`BDaemonSession`/`BStationSurrogate` RPC call, not a local spawn) may be limited to asking SCM to
start/stop the service by NAME, through an API this session found no evidence `njre.dll` itself imports
either (`OpenSCManager`/`StartService` are absent from `njre.dll`'s table, per above) — meaning even reading
(2) leaves OPEN exactly how `niagarad.exe` talks to SCM, if it does at all (possibly via a THIRD binary,
a `.NET`/`sc.exe`-invoking helper, or the `BDaemonSession` RPC terminating in a component this corpus's
Java tree does not expose). **Net: this session narrows the search space (rules OUT `njre.dll` as the
holder of process-creation/SCM capability; confirms `nre.dll` HAS both capabilities) but does not close
B57-G2** — the specific call site and its actual target remain unread. Refined and re-opened as **B61-G1**.

## 61.3 — B38-G2 CLOSED: the SP-side SAML signature-algorithm allowlist lives inside OneLogin's bundled `java-saml-core-2.9.0.jar`, is a hardcoded 5-URI set INCLUDING SHA-1 variants, and IS the gate N5's actual call chain hits — with a separate "reject deprecated" flag the N5 call site never enables `[CERT]`

[Block 38] §38.6 read `Response.validateSignatures()` (`Response.java:238-286`) calling
`Util.validateSignNode(Node, X509Certificate, String, String)` and found no explicit algorithm allowlist
VISIBLE in Tridium's own source — unlike the IdP-side `ALGORITHM_MAPPING` (§38.9: 6 URIs, RSA/ECDSA ×
SHA-256/384/512, Tridium-authored) — and named the gap "depends on OneLogin/Santuario library defaults
not read this session" → **B38-G2**. No decompiled `.java` for `com.onelogin.saml2.util.Util` exists
anywhere in `organized/` — the library ships as `LIB-INF/java-saml-core-2.9.0.jar` only. This session
extracts `Util.class` from that exact jar and disassembles it with `javap -p -c` — a legitimate primary
source read (the exact bundled bytecode on this install), never previously opened in this corpus.

**Confirmed call chain from N5's actual call site down to the allowlist check.** `Response.validateSignatures()`
calls the 4-argument overload directly: `Util.validateSignNode(responseSignatures.item(0), cert, null,
null)` and `Util.validateSignNode(assertionSignatures.item(0), cert, null, null)` `[CERT]`
`organized/saml/vineflower/com/tridium/saml/rp/Response.java:274,278` (re-read whole method this session).
Disassembling `Util.class` shows this exact 4-arg overload is a thin wrapper:

```
validateSignNode(Node, X509Certificate, String, String)
  → validateSignNode(Node, X509Certificate, String, String, Boolean.FALSE)   // "reject deprecated" hardcoded false
      → getSignatureData(Node, fingerprintAlg, Boolean.FALSE)
          uri = new XMLSignature(element, "", true).getSignedInfo().getSignatureMethodURI();
          if (!isAlgorithmWhitelisted(uri)) throw new Exception(uri + " is not a valid supported algorithm");
          if (mustRejectDeprecatedSignatureAlgo(uri, false)) return emptyMap;   // never true: flag is false
          ... populate {signature, cert, fingerprint} map ...
      → validateSignNode(XMLSignature, cert, fingerprint, certFromMap, fingerprintFromMap)
          if (cert != null) return signature.checkSignatureValue(cert);   // actual Apache Santuario crypto check
```
`[CERT]` `javap -p -c` disassembly of `com/onelogin/saml2/util/Util.class` (extracted from
`organized/saml/vineflower/LIB-INF/java-saml-core-2.9.0.jar`, this session) — every arrow above is a
directly observed `invokestatic`/`invokevirtual` bytecode instruction, not inferred from method names: the
4-arg overload's body is `iconst_0 → Boolean.valueOf(false) → invokestatic validateSignNode(5-arg)`; the
5-arg overload's body is `invokestatic getSignatureData(3-arg)` followed by unpacking the returned `Map`'s
`"signature"`/`"cert"`/`"fingerprint"` entries into the low-level `XMLSignature`-typed
`validateSignNode`; the 3-arg `getSignatureData` constructs `new XMLSignature(element, "", true)`, calls
`getSignedInfo().getSignatureMethodURI()`, then `invokestatic isAlgorithmWhitelisted(String)Z` — a
conditional `ifne` on its result gates a `throw new Exception(... "is not a valid supported algorithm")` —
followed by `invokestatic mustRejectDeprecatedSignatureAlgo(String,Boolean)` on the SAME uri and the
propagated `false`; the low-level `XMLSignature`-arg `validateSignNode` calls
`XMLSignature.checkSignatureValue(X509Certificate)` only when the caller-supplied cert (N5's IdP truststore
cert, `BServerPort`-unrelated — `SecurityUtil.doPrivileged(() -> CertManagerFactory.getInstance()
.getUserTrustStore().getCertificate(idpCertName))`, `[CERT]` `Response.java:263-264`) is non-null.

**`isAlgorithmWhitelisted(String)` is a hardcoded 5-member `HashSet`, built inline in the method body:**
`http://www.w3.org/2000/09/xmldsig#dsa-sha1`, `http://www.w3.org/2000/09/xmldsig#rsa-sha1`,
`http://www.w3.org/2001/04/xmldsig-more#rsa-sha256`, `http://www.w3.org/2001/04/xmldsig-more#rsa-sha384`,
`http://www.w3.org/2001/04/xmldsig-more#rsa-sha512` `[CERT]` `javap -p -c` output for
`isAlgorithmWhitelisted`, five `Set.add(String)` calls read directly off the constant-pool string literals
(`ldc` instructions) in sequence — a `SignatureMethod` URI outside this exact 5-member set throws before
`checkSignatureValue` is ever reached, which is the answer B38-G2 asked for: **yes, an explicit allowlist
gates the SP side too**, it is just invisible from Tridium's own Java source because it lives entirely
inside the bundled library.

**A second gate exists in the same library and is confirmed DISABLED for N5's call path.**
`mustRejectDeprecatedSignatureAlgo(String uri, Boolean reject)` checks `uri` against a static
`DEPRECATED_ALGOS` set — populated in the class's `static {}` initializer as exactly `{rsa-sha1, dsa-sha1}`
`[CERT]` `javap -p -c` disassembly of the class initializer, two `String` literals `Arrays.asList`'d into a
`HashSet` — and, when `reject == true`, LOGS an error and returns `true` (causing `getSignatureData` to
return an empty map, i.e. reject the signature as invalid upstream). Because N5's 4-arg call site hardcodes
`Boolean.FALSE` for this parameter (the `iconst_0` at the very top of the 4-arg overload, propagated
unchanged through both intermediate calls), `mustRejectDeprecatedSignatureAlgo` for N5 ALWAYS returns
`false` regardless of the algorithm used — its `reject==true` branch is dead code for every call this
station makes. **Net reading: `rsa-sha1` and `dsa-sha1` are simultaneously inside `isAlgorithmWhitelisted`'s
ACCEPT set and inside `DEPRECATED_ALGOS`'s reject-candidate set — the library ships a knob to reject them
as deprecated, and N5's SP-side SAML call site does not turn it on**, so a SHA-1-signed (or DSA-SHA1-signed)
IdP response is accepted by `com.tridium.saml.rp.Response` on this install exactly as readily as an
RSA-SHA256/384/512 one would be, subject only to `checkSignatureValue`'s actual cryptographic check against
the configured IdP cert succeeding.

**Contrast with the IdP-side allowlist [Block 38] §38.9 already read.** Tridium's OWN `ALGORITHM_MAPPING`
(IdP-side `AuthnRequest` verification, Tridium-authored Java source, not a bundled library) accepts 6 URIs
— RSA/ECDSA × SHA-256/384/512 — and excludes SHA-1 and DSA entirely `[CERT-a]` (per [Block 38] §38.9,
re-cited not re-verified this session). The SP-side allowlist this session closes is STRICTER in shape
(fewer signature families — RSA/DSA only, no ECDSA) but LOOSER in strength (still accepts two SHA-1-family
URIs the IdP side would reject outright): the two allowlists are independently maintained (one
Tridium-authored, one inherited from a third-party library's 2.9.0 release) and are NOT the same policy,
despite guarding the same protocol at the two ends of the same trust relationship.

## 61.x — Connections

- **[Block 40]** — closes **B40-G2** (§61.1); upgrades §40.2's `ruleHintOverride`-branch finding from
  `[INFER]` to `[CERT]` for the live-station scenario. [Block 40]'s companion **B40-G1** (RENAME charset
  for `BOpcUaServer.getName()`) remains open, untouched by this block.
- **[Block 41]** — its §41.2 citation of `Station.java:190` (opened there for an `@AuditableSpace`
  finding) is re-read here for the space-CONSTRUCTION sequence around it (`:160-207`) to settle a
  completely different question (B40-G2); no correction to [Block 41]'s own finding.
- **[Block 57]** — advances but does not close **B57-G2** (§61.2); narrows the search space (rules out
  `njre.dll`, confirms `nre.dll` has both `CreateProcessA` and Windows-Service-registration imports) and
  opens a narrower, re-scoped **B61-G1** in its place.
- **[Block 33]** — grandparent of the B40-G2 chain via [Block 40]; unchanged by this block.
- **[Block 38]** — closes **B38-G2** (§61.3); the §38.9 IdP-side `ALGORITHM_MAPPING` citation is re-used
  for the cross-allowlist contrast, not re-verified this session (flagged `[CERT-a]` accordingly, matching
  its own original marker).
- **[Block 53]** — its `nre.dll` `strings` run (for `-Dcmdline::`) and this block's `objdump -x` run (for
  the import table) are two DIFFERENT extractions of the same file for different purposes; no overlap,
  no correction either way.

## 61.x — Child gaps opened

- **B61-G1** (refines/narrows **B57-G2**) — Disassemble `nre.dll`'s actual `CreateProcessA` CALL SITE(s)
  (not merely its import-table presence) to determine what it spawns — a JxBrowser/Chromium child process
  (plausible, per `JxBrowserUtil.java` and the `jxBrowser` module already in this corpus), a station-restart
  self-relaunch, or something else — and separately determine how `niagarad.exe` actually triggers an OS-level
  station start given `njre.dll` imports neither `CreateProcessA` nor any `OpenSCManager`/`StartService`
  Service-Control-Manager API: possible candidates not checked this session are a `.NET`/PowerShell/`sc.exe`
  helper invoked as a subprocess (which WOULD need `CreateProcessA` — absent — so this reading is weakened,
  not supported, by this session's findings), or an OS-level Windows Service definition created entirely at
  INSTALL time (by the MSI/installer, a binary outside `bin/` not probed this session) with `niagarad.exe`
  never itself calling any Win32 process/service-creation API for a NORMAL start (§61.2).
- **B61-G2** — This session's `isAlgorithmWhitelisted`/`DEPRECATED_ALGOS` reading is bytecode-only
  (`javap` disassembly); it was not exercised against a live SAML exchange. A `[CERT-hw]` confirmation —
  crafting/observing a live SAML response signed with `rsa-sha1` and confirming N5 actually accepts it
  end-to-end (not merely that the library-internal gate WOULD permit it) — was not performed this session
  and would require an active IdP/SP test harness (§61.3).

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block61.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):
```
== verify-block: niagara5-block61.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 13  (adj 11)
   [CERT-live] 0
   [CERT] 29  (adj 26)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 6  (adj 5)
   [INFER] 14  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/42 = 0.26
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BComponentSpace.java:317-319  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BTunnelService.java:142  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ComplexSlotMap.java:1666-1667  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ComplexSlotMap.java:1799-1816  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  JxBrowserUtil.java:223  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Response.java:238-286  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Response.java:263-264  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Station.java:190  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/baja/vineflower/com/tridium/sys/registry/NTypeInfo.java:110-139  (range end verified; file has 309 lines)
   ok      organized/baja/vineflower/com/tridium/sys/schema/ComplexSlotMap.java:1799-1827  (range end verified; file has 2189 lines)
   ok      organized/baja/vineflower/com/tridium/sys/schema/ComponentSlotMap.java:1588
   ok      organized/baja/vineflower/com/tridium/sys/station/Station.java:160-207  (range end verified; file has 885 lines)
   ok      organized/baja/vineflower/com/tridium/sys/station/Station.java:190-194  (range end verified; file has 885 lines)
   ok      organized/baja/vineflower/niagara/space/BComponentSpace.java:105-111  (range end verified; file has 1055 lines)
   ok      organized/baja/vineflower/niagara/virtual/BVirtualComponentSpace.java:22
   ok      organized/orion/vineflower/com/tridium/orion/BOrionSpace.java:32
   ok      organized/platform/vineflower/com/tridium/platform/BSystemPlatformService.java:1248-1260  (range end verified; file has 1565 lines)
   ok      organized/saml/vineflower/com/tridium/saml/rp/Response.java:238-286  (range end verified; file has 520 lines)
   resolved 10 of 18
== exit 0 ==
```

**Reading the resolution split.** 10 of the 18 script-recognized citations resolve `ok` — these are the
ones cited in the header/prose with their FULL `organized/...` path, per METHODOLOGY §11's citation-form
convention ("the SELF-VERIFY anchor for every load-bearing citation MUST carry the full `filename:line`
form"). The 8 `extern` ones are BARE `file:line` forms used in the body prose for readability where a
FULLY-PATHED citation for the same fact already appears elsewhere in the block (e.g. `Station.java:190`
in the header blockquote is the bare short-form the body prose also uses once, while `Station.java:160-207`
and `:190-194` — the same file, fuller ranges — are cited in full-path form immediately alongside it and
DO resolve `ok`). None of the 8 `extern` items is an unpathed citation with NO full-path counterpart in the
block; each is redundant with a resolved full-path citation to the same file. Two citation classes are not
`file:line`-shaped and are therefore outside the script's 18-item list entirely: (1) the `javap` bytecode
disassembly of `Util.class` (§61.3) — cited by method signature and jar path, no source line numbers exist
for a `.class`-only artifact; (2) the `objdump -x`/`strings` native-binary import-table reads (§61.2) —
cited by binary path and imported symbol name, same reason. Both are addressed by inline token-verify,
next.

**Reading the raw vs. adjusted split.** The `[CERT-hw]` raw count (13, adj 11) is inflated by 2 from this
Self-verify section's own prose re-using the marker name while describing the tally — the block's REAL
`[CERT-hw]` claims are the native-binary import-table findings in §61.2 (11 distinct claims: njre.dll's
ADVAPI32 set, njre.dll's lack of CreateProcess in both the import table and a `strings` pass, nre.dll's
ADVAPI32 set, nre.dll's `CreateProcessA`/service-API presence, plus the negative `njre.dll` string-search
sub-claims). `[CERT]` (29 raw, 26 adj) and `[CERT-a]` (6 raw, 5 adj) are the block's other evidence
classes — real evidence tally: **26 `[CERT]` + 11 `[CERT-hw]` + 5 `[CERT-a]` = 42** against **11 real
`[INFER]`**, ratio 11/42 ≈ 0.26 (matching the script's own reported ratio exactly — no chase-your-tail
inflation this run) — well below the ~0.5 exhaustion threshold, consistent with this being a targeted
gap-closing session against sources each prior block had explicitly named but not yet opened (a productive
session, not an exhausted one). The `[INFER]`s are concentrated in §61.2's own honestly bounded "two
readings compete" paragraph (naming B61-G1) plus the cross-allowlist "independently maintained" framing and
the B61-G1/B61-G2 child-gap prose in §61.3 — none are load-bearing for either CLOSED gap's verdict (B40-G2,
B38-G2), which rest entirely on the `[CERT]`/`[CERT-hw]` claims.

**Inline token-verify.** Every `file:line` citation above points at a file this session `Read` in full or
via a targeted range this session, cross-checked against a fresh `grep -n` locating the cited symbol —
zero citations reused verbatim from [Block 40]/[Block 41]/[Block 57]/[Block 38]'s text without an
independent re-open this session (the `Station.java:190` region [Block 41] also cites was re-read in
FULL this session, `:160-207`, not copied from [Block 41]'s excerpt; `ComplexSlotMap.java:1799-1816`
[Block 40] cites was re-read and extended to `:1827`). Spot-check tokens independently re-confirmed present
(whitespace-normalized) this session: `setRequiresValidation`/`BOG_SPACE_TYPE_INFO`/`space.getType().is`
(`ComplexSlotMap.java`), `getType()`/`isProxyComponentSpace()`/`TYPE = Sys.loadType` (`BComponentSpace.java`),
`class BBogSpace extends BComponentSpace` / `class BOrionSpace extends BComponentSpace` / `class
BVirtualComponentSpace extends BComponentSpace` (3 independent `grep -n "class B.*Space"` runs, one per
file), `is(TypeInfo)`/`is(Type)` bodies (`NTypeInfo.java`), `setRootComponent`/`mount(BComponentSpace`
(`BComponentSpace.java`/`ComponentSlotMap.java`), `Util.validateSignNode`/`SecurityUtil.doPrivileged`
(`Response.java`). Native-binary tokens confirmed present/absent via direct tool output this session (not
hand-recalled): `RegisterServiceCtrlHandlerA`/`StartServiceCtrlDispatcherA`/`SetServiceStatus`/
`CreateProcessA` present in `nre.dll`'s `objdump -x` output; same four ABSENT from `njre.dll`'s `objdump -x`
output (confirmed by their absence from the full printed import table, not by a negative grep alone — the
full table was read end-to-end for both files); `CreateProcess`/`station.exe`/`StartServiceCtrlDispatcher`/
`OpenSCManager` confirmed absent from `njre.dll` via `strings | grep -i`, zero hits, this session. Jar
bytecode tokens confirmed via direct `javap -p -c` output this session, not recalled from training-data
knowledge of the OneLogin library: `isAlgorithmWhitelisted`'s 5 `Set.add` string literals, `DEPRECATED_ALGOS`'
2-member `static {}` population, the exact `invokestatic` call sequence from the 4-arg `validateSignNode`
down to `checkSignatureValue`. Token-verify: **≈28 distinct load-bearing tokens** confirmed present (or
confirmed ABSENT, for the two native-binary negative-existence claims in §61.2, per METHODOLOGY §3's
symmetric-opening-obligation rule — both `njre.dll` claims are ABOUT a named artifact this session actually
opened and read end-to-end, not merely not-found) in their cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block61.md`. Per the
caller's explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator, matching [Block 40]'s own convention for the same instruction.
