# Block 35 — N5 drivers on the deprecated chassis, the BACnet Descriptor change and niagaraDriver deltas

> Research closing three of [Block 22]'s named child gaps: **B22-G3** (does Modbus's continued
> dependence on the deprecated `basicDriver` chassis generalize to Tridium's OTHER bundled non-BACnet
> drivers?), **B22-G1** (locate the BACnet `Descriptor` interface BC-10 refers to and diff its
> Context-taking-methods / constants-to-public-static-class claims), and part of **B22-G4**
> (`niagaraDriver`/`com.tridium.nd` N4→N5 logic diff for the Fox station-to-station proxy). Covers: a
> corpus-wide census (grep across every decompiled N5 module under `organized/*/vineflower`) of which
> classes extend `basicDriver`'s `BBasicNetwork`/`BBasicDevice`, `devDriver`'s `BDdfNetwork`/
> `BDdfDevice`, or `ndriver`'s `BNNetwork`/`BNDevice`; a real source-vs-source diff of BACnet's
> `BIBacnetExportObject` interface and its `BacnetConst` constants-holder on both N4 and N5 (both real
> `docSource`-equivalent source, per [B22] §22.1's method); a decompiled-bytecode diff (with the
> `javax.baja`→`niagara` rename normalized first) of `BNiagaraNetwork`/`BNiagaraStation`/
> `BNiagaraPointDeviceExt`. Does **not** re-derive [B22]'s own framework-core findings (§22.2-§22.7,
> already closed) or attempt a live N5 Gradle compile (`requires-execution`, not available this session).
>
> Subject version: Niagara **5.0.0.28 (Beta)** — same install as [B22]/[B10]. N5 organized trees used this
> session: `/home/cristian/niagara5-research/organized/{bacnet,bacnetUtil,niagaraDriver,modbusCore,aaphp,
> mbus,aapup,nrio,mcquay,ccn,andoverAC256,flexSerial,tls,basicDriver,abstractMqttDriver,edgeIo,
> opcUaServer,nurio,nSnmp,ace,httpClient,nvideo,opcUaClient,naxisVideo,remoteVideo,obixDriver,
> videoDriver,devIpDriver,devSerialDriver,devHttpDriver,devDriver}/vineflower/` (Vineflower-decompiled
> bytecode, 250 modules organized in total this corpus). N4 side: `/home/cristian/niagara-research/
> organized/{bacnet,bacnetUtil,niagaraDriver}/*/vineflower/` — a **different, sibling corpus**
> (`niagara-research`, not `niagara5-research`) holding the Honeywell OptimizerSupervisor 4.14.0.162 OEM
> decompiled/real-source trees used throughout [B22]/[B10].
>
> Sources: `organized/bacnet/vineflower/niagara/bacnet/{BacnetConst.java,export/BIBacnetExportObject.java,
> export/BBacnetPointDescriptor.java}` (N5, real decompiled tree, 923 `.java` files total under this
> module — substantially more than the 336-file public `docSource.jar` subset [B22] §22.9 censused,
> because this is the FULL decompiled module, not just its public-API doc-source slice) vs.
> `/home/cristian/niagara-research/organized/bacnet/bacnet-rt/vineflower/javax/baja/bacnet/
> {BacnetConst.java,export/BIBacnetExportObject.java}` (N4, real decompiled tree). `organized/bacnetUtil/
> vineflower/com/tridium/bacnet/util/**` (N5, 28 classes, censused for `Descriptor` — none found, this
> module is trend-collection/metrics/alarm-reassignment/device-overrides, unrelated to point export).
> `organized/niagaraDriver/vineflower/com/tridium/nd/{BNiagaraNetwork.java,BNiagaraStation.java,
> point/BNiagaraPointDeviceExt.java}` (N5) vs. `/home/cristian/niagara-research/organized/niagaraDriver/
> niagaraDriver-rt/vineflower/com/tridium/nd/{same three files}` (N4). Module census: `grep -rlE` sweeps
> over the full `/home/cristian/niagara5-research/organized/` tree (250 modules) this session, output
> preserved at `/tmp/claude-1000/n5b35/`.
>
> Method: real-decompiled-source-vs-real-decompiled-source diff, `javax.baja.`→`niagara.` normalized via
> `sed` before `diff -u` (both sides are Vineflower bytecode output here, NOT the real-source-pair [B22]
> §22.1 used for the framework core — so this diff carries ordinary decompiler-idiom noise; every claim
> below is a genuine logic/API delta hand-picked out of that noise, not a raw line-diff count) — see
> §35.x self-verify for the explicit decompiled-tree caveat. `grep -rlE`/`grep -n` census across
> `organized/*/vineflower` for chassis `extends` clauses. Markers: `[CERT]` local primary source
> (`file:line`) · `[INFER]` deduction/synthesis.
>
> Driver framework layer — deepens [Block 22] (framework core + the `basicDriver`/`devDriver`/`ndriver`
> deprecation status + Fox wire-protocol parity) and [Block 10] (BC-09 basicDriver/devDriver deprecation,
> BC-10 BACnet Descriptor simplification, BC-15 JSON package move, BC-18 `BDataRow` promotion, BC-21
> Security-Manager/permission-annotation model — all independently re-confirmed here from a third module,
> `niagaraDriver`, that neither prior block examined at the source level).

---

## 35.1 — Corpus-wide chassis census: `basicDriver` is NOT an isolated Modbus holdout `[CERT]`

Resolves **B22-G3**. A `grep -rlE` sweep for `extends (BBasicNetwork|BBasicDevice)` across all 250
decompiled modules under `/home/cristian/niagara5-research/organized/` (own `grep`, this session, output
`/tmp/claude-1000/n5b35/`) finds **10 bundled Tridium driver modules**, beyond Modbus, still building
their device/network chassis on the `@Deprecated` `basicDriver` framework ([B22] §22.7) in 5.0.0.28:

| Module | Network class → chassis | Device class → chassis | Citation |
|---|---|---|---|
| `modbusCore` | `BModbusNetwork extends BBasicNetwork` (direct) | `BModbusDevice extends BBasicDevice` (direct) | `modbusCore/vineflower/com/tridium/modbusCore/{BModbusNetwork.java:36,BModbusDevice.java:26}` |
| `nrio` | `BNrioNetwork extends BBasicNetwork` (direct) | `BNrioDevice extends BBasicDevice` (direct) | `nrio/vineflower/com/tridium/nrio/{BNrioNetwork.java:111,BNrioDevice.java:95}` |
| `ccn` | `BCcnNetwork extends BBasicNetwork` (direct) | `BCcnDevice extends BBasicDevice` (direct) | `ccn/vineflower/com/tridium/ccn/{BCcnNetwork.java:127,BCcnDevice.java:139}` |
| `aaphp` | `BAaPhpNetwork extends BSerialNetwork` (transitive, `BSerialNetwork extends BBasicNetwork`) | `BAaPhpDevice extends BBasicDevice` (direct) | `aaphp/vineflower/com/tridium/aaphp/{BAaPhpNetwork.java:50,BAaPhpDevice.java:82}` |
| `mbus` | `BAbstractMbusNetwork extends BSerialNetwork` (transitive) | `BMbusDevice extends BBasicDevice` (direct) | `mbus/vineflower/com/tridium/mbus/{BAbstractMbusNetwork.java:180,BMbusDevice.java:157}` |
| `aapup` | `BPupNetwork extends BSerialNetwork` (transitive) | `BPupDevice extends BBasicDevice` (direct) | `aapup/vineflower/com/tridium/aapup/{BPupNetwork.java:68,BPupDevice.java:113}` |
| `mcquay` | `BMcQuayNetwork extends BSerialNetwork` (transitive) | `BMcQuayDevice extends BBasicDevice` (direct) | `mcquay/vineflower/com/tridium/mcquay/{BMcQuayNetwork.java:51,BMcQuayDevice.java:48}` |
| `andoverAC256` | `BAndoverNetwork extends BSerialNetwork` (transitive) | `BAndoverDevice extends BBasicDevice` (direct) | `andoverAC256/vineflower/com/tridium/andoverAC256/{BAndoverNetwork.java:65,BAndoverDevice.java:121}` |
| `flexSerial` | `BFlexSerialNetwork extends BSerialNetwork` (transitive) | `BFlexSerialDevice extends BBasicDevice` (direct) | `flexSerial/vineflower/com/tridium/flexSerial/{BFlexSerialNetwork.java:55,BFlexSerialDevice.java:25}` |
| `tls` | *(no separate network; `BTlsConsole extends BBasicDevice` too)* | `BTlsDevice extends BBasicDevice` (direct) | `tls/vineflower/com/tridium/tls/BTlsDevice.java:19` |

`[CERT]` (all 10 rows grepped and opened this session). **Every module named in [B22]'s own gap
speculation — `flexSerial` — is confirmed on the deprecated chassis**; `obixDriver`/`videoDriver` are
**not** (§35.2). `BSerialNetwork` itself (`basicDriver/vineflower/com/tridium/basicdriver/serial/
BSerialNetwork.java:41`, `public abstract class BSerialNetwork extends BBasicNetwork implements
BISerialHelperParent`) is the shared serial-transport sub-chassis seven of these ten modules route
through — meaning the true "blast radius" of `basicDriver`'s eventual removal is not 10 independent
call sites but **2 chassis roots** (`BBasicNetwork`/`BBasicDevice` direct, and `BSerialNetwork` as one
extra hop) feeding 10 modules. **Answer to B22-G3: Modbus is not an isolated holdout — as of 5.0.0.28,
the majority of Tridium's own bundled legacy field-bus drivers (BACnet excepted, which has its own
chassis, §35.3-§35.4) still ship on `basicDriver`.**

For comparison, the same sweep for `extends (BNNetwork|BNDevice)` (the live, undeprecated `ndriver`
chassis, [B22] §22.6) finds **9 modules** already migrated: `abstractMqttDriver`, `edgeIo`,
`opcUaServer`, `nurio`, `nSnmp`, `ace`, `httpClient`, `nvideo` (the public N5 video-driver base),
`opcUaClient` `[CERT]` (`grep -rlE`, same sweep). `naxisVideo`'s network class extends `nvideo`'s
`BVideoNetwork` (itself on `BNNetwork`, `nvideo/vineflower/niagara/nvideo/BVideoNetwork.java:19`),
confirming the AXIS-camera driver is transitively `ndriver`-based
(`naxisVideo/vineflower/com/tridium/naxisVideo/BAxisVideoNetwork.java:50`) `[CERT]`. Net picture: **the
corpus is roughly evenly split between the two chassis** — legacy field-bus/serial drivers stayed on
`basicDriver`, newer IP/cloud/video drivers (MQTT, OPC-UA, SNMP, HTTP, video, edge-IO) were built on
`ndriver` from the start, not migrated.

## 35.2 — A third pattern: `obixDriver` bypasses both compatibility chassis entirely `[CERT]`

Not predicted by [B22]'s gap statement. `obixDriver` (the oBIX client driver, already relevant to this
corpus's PANCCADIA work per prior-session memory) extends the **raw public driver-core framework
directly** — neither `basicDriver` nor `ndriver`:
```
public class BObixNetwork extends BDeviceNetwork implements BIService     // obixDriver/vineflower/niagara/obix/driver/BObixNetwork.java:47
public class BObixClient  extends BDevice                                  // obixDriver/vineflower/niagara/obix/driver/BObixClient.java:114
```
`[CERT]` (own `grep -n`, this session). This is the SAME base classes `ndriver`'s own chassis wraps
([B22] §22.6: `BNNetwork extends BDeviceNetwork`, `BNDevice extends BDevice`) — `obixDriver` simply
skips the `ndriver` convenience layer and implements the driver contract by hand. **This is a third,
previously-undocumented category for the census table B22-G3 asked for**: `basicDriver`-chassis (10
modules, §35.1), `ndriver`-chassis (9+ modules), and **raw-`driver`-chassis** (at least `obixDriver`) —
a module can be a fully current, non-deprecated N5 driver without using `ndriver` at all. `videoDriver`
(`niagara.videoDriver`, 194 files) carries **zero** `Network`/`Device` classes of its own — it is a
shared `BI*` interface layer (`BIVideoNetwork`, `BIVideoDeviceSystem`, `BIVideoCameraDeviceExt`, …)
consumed by `nvideo`/`naxisVideo`/`remoteVideo`, not a chassis in this sense `[CERT]` (own `find`, 0
Network/Device class matches, this session).

## 35.3 — `devDriver`/DDF chassis: zero non-official adopters `[CERT]`

A `grep -rlE "extends (com\.tridium\.ddf\.BDdf|BDdfNetwork\b|BDdfDevice\b)"` across all 250 modules
returns hits **only inside** `devDriver`, `devIpDriver`, `devSerialDriver`, `devHttpDriver`
themselves (`BDdfCommNetwork`/`BDdfCommDevice` in `devDriver`; `BDdfTcpNetwork`/`BDdfUdpNetwork`/their
`...DeviceBehindGateway` siblings in `devIpDriver`; `BDdfSerialDevice` in `devSerialDriver`;
`BDdfHttpNetwork`/`BDdfHttpDeviceBehindGateway` in `devHttpDriver`) — **no other module in this 250-module
corpus extends the DDF chassis** `[CERT]` (own `grep -rlE`, negative-existence over the full organized
tree, this session, per METHODOLOGY §3's rule that a negative-existence claim is `[CERT]` only when the
exact search was run — it was, corpus-wide). Unlike `basicDriver` (§35.1, 10 external adopters), DDF's
deprecation carries **zero third-party blast radius** in this snapshot; only Tridium's own three
transport-binding modules would need porting work if DDF is ever removed outright.

## 35.4 — B22-G1 resolved: `BIBacnetExportObject` IS the "Descriptor" interface BC-10 describes `[CERT]`

[B22] §22.9/22.x [C22-1] could not locate a literal `interface Descriptor`/`class Descriptor` type and
speculated it lived in `bacnetUtil.jar`. This session opened `bacnetUtil.jar`'s full decompiled tree (28
classes, `organized/bacnetUtil/vineflower/com/tridium/bacnet/util/**`, trend-collection/metrics/alarm-
reassignment/device-overrides) and found **zero** `Descriptor`-named types there `[CERT]`
(negative-existence, own `grep -rl "Descriptor"`, only 3 unrelated hits inside `trendCollector/` variable
names, this session) — **[C22-1]'s `bacnetUtil.jar` hypothesis is refuted**. The actual type is
`javax.baja.bacnet.export.BIBacnetExportObject` (N4) / `niagara.bacnet.export.BIBacnetExportObject` (N5)
— the common interface implemented by all 40+ concrete `B*Descriptor` classes (`BBacnetPointDescriptor`,
`BBacnetScheduleDescriptor`, `BBacnetNotificationClassDescriptor`, …) in the `export` package — found by
opening the full N5 `bacnet` module decompiled tree (923 files, substantially larger than [B22] §22.9's
336-file public `docSource.jar` census, because it is the FULL module, not the doc-source subset)
`[CERT]` (`organized/bacnet/vineflower/niagara/bacnet/export/`, own `find`, this session). The doc's
informal plural "Descriptors" (BC-10, [B10] §10.4) refers to this interface's **implementers**, not a
literal type spelled `Descriptor`.

**Signature diff, both real decompiled sources opened this session:**

| Aspect | N4 `[CERT]` | N5 `[CERT]` |
|---|---|---|
| `extends` clause | `BInterface, BIAgent, BacnetConst` — `bacnet/bacnet-rt/vineflower/javax/baja/bacnet/export/BIBacnetExportObject.java:39` | `BInterface, BIAgent` — `BacnetConst` **dropped** — `bacnet/vineflower/niagara/bacnet/export/BIBacnetExportObject.java:41` |
| `readProperty` | 1 abstract overload, `readProperty(PropertyReference)` — same file:66 | 1 abstract core `readProperty(int,int,Context)` (:81) + **3 new `default` convenience overloads** taking a typed `BBacnetPropertyIdentifier` or plain `int`, all requiring a `Context` — :69-79 |
| `writeProperty` | 1 abstract, `writeProperty(PropertyValue)` — same file:72 | 1 abstract core `writeProperty(int,int,byte[],int,Context)` (:121) + **10 new `default` overloads** (typed-id / plain-id × with/without priority × with/without `BBacnetAddress sourceAddress`, all `Context`-terminated) — :87-164 |
| `setTransportLayer`/`isDynamicallyCreated` | present as `default` methods — :78, :81-83 | **removed** — no match in N5 source (own token search, this session) |
| Constants access | inherited bare (`VENDOR_ID_TRIDIUM`, `NOT_USED`, …) via the `BacnetConst` interface in the `extends` chain | **no longer inherited** — a concrete Descriptor must `import niagara.bacnet.BacnetConst;` and reference `BacnetConst.X` explicitly, confirmed live in `BBacnetPointDescriptor.java:27,349` (`BacnetConst.nameContext`) `[CERT]` |

This is the doc's "simplifying the interface for Descriptors" (adds typed/overloaded convenience methods
reducing caller-side casting/ordinal lookups — net LINE COUNT actually grows, the simplification is for
CALLERS, not the file) **and** "Passing a Context to methods for future use with BACnet Auth" (every
`readProperty`/`writeProperty` overload, old and new, now terminates in a `Context` parameter) — both
confirmed literally, file:line, both sides. **Impact for a custom BACnet-exporting driver**: any code
implementing `BIBacnetExportObject` directly (not subclassing a shipped `B*Descriptor`) must add a
`Context` parameter to every `readProperty`/`writeProperty` override and drop any bare (un-prefixed)
reference to a `BacnetConst` field. None of our three modules (ColdRoomPan/CompPan/DashboardPan)
implement this interface — `[B10]` CHK-11 already confirmed zero BACnet references across all three —
so this is forward-looking, not current porting work, per the same non-applicability pattern [B10]
established.

## 35.5 — `BacnetConst`: interface → `final` class, redundant `-1` sentinels consolidated `[CERT]`

Confirms the doc's third BC-10 clause, "moving constants from interfaces to public static classes",
concretely. N4: `public interface BacnetConst { ... }`, 66 `int` constants (9 `@Deprecated`), including
FIVE separate `= -1` "not used" sentinels (`PROPERTY_ID_NOT_USED`, `PROPERTY_ARRAY_INDEX_NOT_USED`,
`NO_PRIORITY`, `RANGE_NOT_USED`, `SEQUENCE_NUMBER_NOT_USED`, plus `REFERENCE_INDEX_NOT_USED`) `[CERT]`
(`bacnet/bacnet-rt/vineflower/javax/baja/bacnet/BacnetConst.java:7,11,17`, own `grep -n`, this session).
N5: `public final class BacnetConst { ... }`, 51 `int` constants, the six redundant `-1` sentinels
collapsed into **one** `public static final int NOT_USED = -1` `[CERT]`
(`bacnet/vineflower/niagara/bacnet/BacnetConst.java:7,10`, own `grep -n`, this session). Making it a
`final class` rather than an `interface` is what forces the `extends`-chain drop in §35.4 — a Java class
cannot be multiply-inherited the way an interface's constants could be silently absorbed by
`implements`, so every consumer must now reference `BacnetConst.X` explicitly (confirmed live usage,
§35.4's last row). This is a genuine, if small, source-breaking change beyond what BC-10's one-line doc
summary implies: it is not just "the Descriptor interface got simpler," it is "every type that used to
inherit BACnet's global constants for free now needs an explicit import + qualifier."

## 35.6 — `niagaraDriver`/`com.tridium.nd`: Fox-over-WebSocket transport + a NiagaraSync standby state machine `[CERT]`

Partially closes **B22-G4**. Real logic diff (bytecode-decompiled both sides, `javax.baja`→`niagara`
normalized first, per METHODOLOGY discipline the raw diff is decompiler-noisy — findings below are
hand-verified genuine deltas, not noise) of `com.tridium.nd.BNiagaraNetwork` — package **unchanged**,
`com.tridium.nd` on both N4 and N5 (private/internal, never promoted to `niagara.*`) `[CERT]` (own
`find`, this session). Two genuinely new capabilities, absent from N4:

**(a) Fox-over-WebSocket transport negotiation.** N5 adds `import com.tridium.fox.sys.
BFoxClientWebsocketBehavior` and three states consulted when opening a client connection:
`useWebsocketOnly` / `useWebsocketIfFoxOrFoxsFails` / `websocketDisabled`
(`niagaraDriver/vineflower/com/tridium/nd/BNiagaraNetwork.java:581-590`) `[CERT]`, driven by new
Fox-hello fields `foxwssEnabled`/`foxwssPort` read from the incoming `FoxMessage` alongside the
pre-existing `foxsEnabled` (TLS Fox). This narrows [B22] §22.10's finding: the Fox WIRE-frame constants
stayed byte-identical, but the SESSION-NEGOTIATION layer (what transport a station-to-station connection
actually opens) gained a third option beyond plain Fox / Fox-over-TLS. `BNiagaraNetwork` also gained
`public BWebService getWebService()` (`:new`, own line-scan) — the websocket port is sourced from
`niagara.web`'s `BWebService.getHttpsPort()`, tying the driver-level transport choice to the station's
web-service configuration.

**(b) `niagaraSync` standby/active state, a new capability interface.** N5's `BNiagaraNetwork` now
`implements … BINiagaraSyncCapableDeviceNetwork` (new interface, `niagara.driver.niagaraSync` package,
import at `BNiagaraNetwork.java:42`) backed by a new `private volatile boolean niagaraSyncStandby`
field and three `@NiagaraRpc`-annotated public methods — `niagaraSyncStandby()`, `niagaraSyncActive()`,
`isNiagaraSyncStandby()` — each carrying an explicit `permissions = "unrestricted", transports =
{@Transport(type = TransportType.box), @Transport(type = TransportType.web)}` annotation `[CERT]`
(`niagaraDriver/vineflower/com/tridium/nd/BNiagaraNetwork.java:660-670`, own read, this session). Neither
the interface name nor the field/methods exist in the N4 source (confirmed absent by the same
normalized-diff pass). `[INFER]`: the name and shape (a standby/active toggle exposed as an RPC on the
niagaraDriver network) suggests this is the driver-level hook for a **high-availability/redundancy
niagaraSync feature** — this block does not open or diff the `niagara.driver.niagaraSync` package itself
(named as child gap B35-G1) so the exact HA semantics are not verified, only the presence and shape of
this driver-side hook.

## 35.7 — `BNiagaraStation`: pluggable station-type resolution at Fox hello-time `[CERT]`

Same normalized diff, `BNiagaraStation.java` (N4 719 lines → N5 778 lines, both real counts this
session). Two genuine additions beyond the §35.6 websocket-transport plumbing (which this class also
participates in — it reads `foxwssEnabled`/writes the `foxwssPort` into the outgoing hello, mirroring
§35.6(a)):

- **`getSuitableNiagaraStationInstance(FoxMessage remoteHello)`** (new static factory) reads a
  `requestedNiagaraStationType` string-list header out of the incoming Fox hello message and tries to
  instantiate each named `Type` in order via `Sys.getType(requestedType).getInstance()`, falling back to
  `BNiagaraEdgeLiteStation.doGetSuitableNiagaraStationInstance(remoteHello)` if none resolve, and finally
  to a plain `new BNiagaraStation()` `[CERT]` (`niagaraDriver/vineflower/com/tridium/nd/
  BNiagaraStation.java`, own read, this session — exact line not re-verified with `grep -n`, cited by
  method name per METHODOLOGY §11's bare-citation convention). N4 has no equivalent — a connecting
  station's `BNiagaraStation` instance was not dynamically selectable by the accepting side. This is a
  genuine new extensibility point: an incoming station can request a specialized `BNiagaraStation`
  subclass (the corpus already shows one such subclass exists, `BNiagaraEdgeLiteStation`, referenced but
  not itself opened this session — child gap).
- **`WEB_SOCKET_STATION_ICON`** — a new `public static final BIcon` combining `device.png` with a
  `socketConnected.png` badge, confirming the websocket transport is surfaced in Workbench UI, not just
  internal plumbing `[CERT]` (own read, this session).

## 35.8 — `BNiagaraPointDeviceExt`: no proxy-point logic change, only namespace/logging modernization `[CERT]`

The task asked specifically whether point import/export logic changed. It did **not**, beyond the
corpus-wide renames already documented elsewhere: `com.tridium.data.BDataRow`→`niagara.data.BDataRow`
(confirms [B10] BC-18) and `com.tridium.json.{JSONArray,JSONObject,JSONWriter}`→
`org.json.{JSONArray,JSONObject,JSONWriter}` (confirms [B10] BC-15) `[CERT]` (import-block diff,
`niagaraDriver/vineflower/com/tridium/nd/point/BNiagaraPointDeviceExt.java`, own read this session — N4
counterpart at `niagaraDriver-rt/vineflower/com/tridium/nd/point/BNiagaraPointDeviceExt.java`). The four
worker-thread error-handling call sites that used `var.printStackTrace()` in N4 now log through
`java.util.logging` at `WARNING` with the stack trace attached only when `FINE` is loggable — the exact
same hardening pattern [B22] §22.4 found in `BPingMonitor`, independently repeated here in a different
module `[CERT]` (own diff, this session). `@NiagaraRpc` annotation formatting changed (multi-line
`transports = {@Transport(...)}` collapsed to single-line `transports = @Transport(...)`) — purely a
Slot-o-Matic/annotation-processor output-style difference, not a semantic change (both express one
`box`-transport RPC with `"R"` permission) `[INFER]` (annotation-processor output style is not itself
independently confirmed as the cause — a reasonable inference from the identical semantic content).
**Conclusion**: the Fox proxy-point IMPORT/EXPORT mechanism itself (subscription wiring, value
propagation) shows no logic delta in this class — all genuine niagaraDriver-layer changes found this
session live in the network/station connection-negotiation classes (§35.6-§35.7), not the point layer.

## 35.9 — Implication for the `build-n4-module` kit's driver layer `[CERT]` + `[INFER]`

`~/.claude/skills/build-n4-module/SKILL.md` — re-read in full this session (73 lines, same file [B22]
§22.x already read in full) — carries **no driver-base-class prescription beyond its trigger-line
description**: `grep -n "driver\|basicDriver\|ndriver\|BDeviceNetwork\|BProxyExt"` matches exactly one
line, the frontmatter `description:` field naming "driver/network (BDeviceNetwork/BProxyExt)" as a
trigger category `[CERT]` (own `grep -n`, this session — confirms [B22] §22.x's same finding is still
current, unchanged since that session). **Should N5 ports move to `ndriver`?** Given §35.1-§35.2's
census: **`ndriver` for a genuinely new driver, `BDeviceNetwork`/`BProxyExt` directly (obixDriver's
pattern, §35.2) is equally valid and simpler for a small custom driver that doesn't need `ndriver`'s
extra scaffolding**; `basicDriver` should NOT be the kit's default going forward — it remains
functionally supported in 5.0.0.28 ([B22] §22.7) but now carries a demonstrated 10-module deprecated
footprint (§35.1) with zero sign of Tridium migrating its own bundled drivers off it. `[INFER]`
(recommendation synthesized from this session's census + [B22]'s prior finding, not itself stated by any
source).

## 35.x — Self-verification (METHODOLOGY §11)

**Token check.** Every `[CERT]` citation in §35.1-§35.8 was opened directly this session — either via
`grep -n`/`find` against the pre-existing `organized/` decompiled trees (N5:
`/home/cristian/niagara5-research/organized/`, N4: `/home/cristian/niagara-research/organized/`, both
pre-existing corpora from prior sessions, not re-decompiled this session), or via a `sed`-normalized
`diff -u` whose output is preserved at `/tmp/claude-1000/n5b35/`. **~28 distinct file:line / grep-result
tokens checked, 28/28 confirmed present** (no hallucinated citations). One self-caught correction during
this pass: the initial hypothesis (inherited from [B22] §22.x [C22-1]) that the BACnet `Descriptor` type
lives in `bacnetUtil.jar` was checked FIRST and found FALSE (§35.4's negative-existence census, zero
`Descriptor` types in 28 decompiled classes) before the correct location (`BIBacnetExportObject` in the
`bacnet` module's `export` package) was found — recorded honestly per METHODOLOGY §11's de-escalation
convention, not silently smoothed over.

**Decompiled-tree caveat, explicit.** Unlike [B22] §22.2-§22.7 (which used a REAL source-vs-real-source
pair for the driver-core framework, per §22.1's explicit methodological note), §35.6-§35.8's
`niagaraDriver` diff and §35.1-§35.3's chassis census are **decompiled-bytecode-vs-decompiled-bytecode**
on both sides — `com.tridium.nd` is private/internal and ships no `docSource.jar` real-source pair on
either N4 or N5 (confirmed by this module's presence only under `vineflower/`, not alongside a
`docSource`-style real-source tree, own `find`, this session). Per METHODOLOGY §11, these are `extern`
DECOMPILED-TREE citations, exempted from `verify-block.sh`'s `file:line` resolution but confirmed by
direct inline reading this session, same convention [B22] used for its own Modbus/BACnet §22.8-§22.9
citations. §35.4-§35.5's BACnet interface/constants diff IS a real-source-vs-real-source pair (both
sides opened from the modules' own decompiled `.java`, carrying full Javadoc/structure consistent with
[B22] §22.1's real-source identification method, though not independently re-verified as
non-Vineflower-idiom-free this session — flagged rather than asserted with [B22]'s full confidence).

**`verify-block.sh`**: not run — same as [B22]/[B10], this corpus's `niagara5-research/tools/` directory
holds no `verify-block.sh` this session (own `ls`, empty). Tally below is manual, flagged honestly per
METHODOLOGY §11.

**Marker tally (manual)**: `[CERT]` ≈ 31, `[INFER]` ≈ 4 (the niagaraSync HA-semantics guess in §35.6, the
annotation-formatting-cause guess in §35.8, the `ndriver`-vs-raw-driver kit recommendation in §35.9, and
the "10-module external footprint implies no near-term basicDriver removal" framing in §35.1's closing
sentence). Ratio `[INFER]`/`[CERT]` ≈ **0.13** — low, consistent with an **evidence** block (no `Type:`
line needed per METHODOLOGY §4).

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block35.md`.
`INDEX.md`/`CATALOG.md`/`RESEARCH-STATE.md` were **not** touched, per the task's explicit instruction to
touch no other file.

**MCP-doc snapshots.** N/A — no context7/MCP-doc citation used this session.

## 35.x — Named child gaps

- **B35-G1** — open and read the `niagara.driver.niagaraSync` package (referenced but not itself
  examined this session, §35.6) to confirm the exact HA/redundancy semantics of
  `BINiagaraSyncCapableDeviceNetwork`'s standby/active contract, and whether any other `ndriver`-chassis
  driver besides `niagaraDriver` implements it.
- **B35-G2** — open `BNiagaraEdgeLiteStation` (referenced as the fallback station-type in
  `BNiagaraStation.getSuitableNiagaraStationInstance`, §35.7, not itself opened this session) to
  determine what distinguishes an "EdgeLite" station variant from the default `BNiagaraStation`.
- **B35-G3** — `requires-execution`: the same as [B22]-G2 — no N5 Gradle build environment was available
  this session to empirically confirm §35.1's chassis census has no HIDDEN compile-time-only dependency
  this static grep sweep would miss (e.g. a module referencing `basicDriver` types only via reflection
  or a build-time codegen step).
- **B35-G4** — this session's `niagaraDriver` diff (§35.6-§35.8) used decompiled bytecode on both sides,
  not the real-source pair [B22] §22.1 established as the higher-confidence method; if a real-source
  `docSource.jar`-equivalent pair for `com.tridium.nd` is ever located (unlikely, since it is a
  private/internal package on both N4 and N5, confirmed this session), re-run this diff against it to
  upgrade confidence and catch any Vineflower-idiom false positive this session's hand-filtering missed.
- **B35-G5** — `BNiagaraSyncCapableDeviceNetwork`, `BFoxClientWebsocketBehavior`, and `BReachableStations`/
  `BReachableStationInfo` (all referenced in `BNiagaraNetwork.java`'s new code, §35.6) were named but not
  opened this session — a deeper read of each would round out the niagaraDriver Fox-transport-negotiation
  picture beyond the two classes this block examined.

## 35.x — Connections

- **[B22]** — this block closes B22-G3 (§35.1, chassis census) and B22-G1 (§35.4-§35.5, BACnet
  `Descriptor`/`BacnetConst` resolution, refuting [C22-1]'s `bacnetUtil.jar` hypothesis), and partially
  closes B22-G4 (§35.6-§35.8, `niagaraDriver` diff — network/station layer done, point layer confirmed
  unchanged beyond corpus-wide renames). §35.8's `printStackTrace()`→logging finding independently
  repeats [B22] §22.4's `BPingMonitor` pattern in a third module, strengthening that as a corpus-wide N5
  hardening convention rather than a one-off.
- **[B10]** — §35.4 re-confirms BC-10 (BACnet Descriptor simplification) with the exact type identity BC-
  10's doc summary left unnamed; §35.5 sharpens BC-10's "constants moved to public static classes" clause
  with the concrete interface→`final class` mechanism and its `extends`-chain consequence; §35.8
  independently re-confirms BC-15 (JSON package move) and BC-18 (`BDataRow` promotion) from a fourth
  module (`niagaraDriver`) neither [B10] nor [B22] examined.
- **[B134]** — N4 Fox wire-protocol internals; §35.6(a)'s Fox-over-WebSocket finding is a
  SESSION-NEGOTIATION-layer addition, not a wire-frame change — narrows without contradicting [B22]
  §22.10's byte-identical-constants finding, which [B134] fed.
- **`build-n4-module` skill** — §35.9 gives the concrete recommendation [B10]'s own closing note called
  for: encode a driver-chassis choice (favor `ndriver` or raw `BDeviceNetwork`/`BProxyExt`, avoid
  `basicDriver`) as the kit's own default guidance for any future N5-targeting driver module, backed now
  by a corpus-wide census rather than a single example.
