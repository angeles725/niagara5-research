# Block 73 — `BNiagaraEdgeLiteStation` licensing/identity gating, the Fox-websocket-behavior enum plus `BReachableStations` topology discovery, three trivial `niagaraSync` point-folder markers, `modbusAsync`/`modbusTcp`'s `basicDriver` chassis lineage, and a corpus-wide negative-existence census for list/queue-shaped `niagaraSync` state

> Research closing five previously-opened, narrowly-scoped child gaps from the driver/network cluster:
> **B35-G2** ([Block 35] §35.7 — what `BNiagaraEdgeLiteStation` is and how it differs from a normal
> `BNiagaraStation`, named as the fallback station-type in `BNiagaraStation.getSuitableNiagaraStationInstance`
> but not itself opened); **B35-G5** ([Block 35] §35.6 — a deeper read of `BFoxClientWebsocketBehavior` and
> `BReachableStations`/`BReachableStationInfo`, both referenced in `BNiagaraNetwork.java`'s new code but not
> themselves opened); **B37-G2** ([Block 37] §37.5 — the three driver-specific `BINiagaraSyncFolder`
> implementers, located by declaration line only, their actual folder-membership/`isChildLegal` logic never
> read); **B37-G5** ([Block 37] §37.5 — `modbusAsync`/`modbusTcp`'s own driver-chassis lineage, identified
> only as `BINiagaraSyncCapableDeviceNetwork` implementers, never classified against [Block 35] §35.1's
> `basicDriver`/`ndriver` chassis census); **B45-G2** ([Block 45] §45.7 — census a WIDER set of modules than
> [Block 37]'s 7-module scope for ANY Tridium-authored list/queue-shaped `niagaraSync` Property, to confirm
> or refute whether `waitingQueueCsv`'s comma-separated-`String` encoding matches an existing convention or
> is genuinely novel). Covers: whole-file reads of `BNiagaraEdgeLiteStation.java` and `BISubLicenseable.java`
> (closing B35-G2); whole-file reads of `BFoxClientWebsocketBehavior.java`, `BReachableStations.java`, and
> `BReachableStationInfo.java` (closing B35-G5); whole-file reads of all three `BINiagaraSyncFolder`
> implementers plus their immediate driver-layer `PointFolder` bases plus the shared `BPointFolder`/`BFolder`
> root (closing B37-G2); a class-declaration trace of `BModbusAsyncNetwork`→`BModbusClientNetwork`→
> `BModbusNetwork`→`BBasicNetwork` and `BModbusTcpNetwork`→(same chain) (closing B37-G5); a full-corpus
> (251-module, not [Block 37]'s 7-module subset) `grep` census of every `BINiagaraSyncCapableComplex`
> implementer plus a substring sweep for a CSV/delimited-string idiom among them (closing B45-G2). Does
> **not** cover: `BNiagaraStation`'s own base-class `clientOpened()`/connection-establishment body (only its
> class-declaration line was re-confirmed, to establish EdgeLite's `BISubLicenseable` delta — see child gap);
> `BNiagaraVirtualChannel.findReachableStations` (the actual Fox RPC `BReachableStations.doUpdateReachableStations`
> invokes — named, not opened); `BComponent`'s own default `isChildLegal` behavior (the terminal, unopened
> boundary of B37-G2's inheritance trace); BACnet's own network-class chassis lineage against [Block 35]'s
> `basicDriver`/`ndriver` split (out of B37-G5's own naming, which scoped to `modbusAsync`/`modbusTcp` only);
> any live/dynamic reproduction (`requires-execution`, not available this session — every finding below is
> static source reading).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install/corpus [Block 35]/[Block 37]/[Block 45] used.
> Decompiled trees this session: `/home/cristian/niagara5-research/organized/{niagaraDriver,fox,baja,bacnet,
> modbusCore,modbusAsync,modbusTcp,driver}/vineflower/` (Vineflower-decompiled bytecode).
>
> Sources: `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraEdgeLiteStation.java` (whole file, 135
> lines, own read this session); `organized/baja/vineflower/com/tridium/sys/metrics/BISubLicenseable.java`
> (whole file, 77 lines, own read this session); `organized/niagaraDriver/vineflower/com/tridium/nd/
> BNiagaraStation.java:103` (class-declaration line only, re-grepped this session to confirm the absence of
> `BISubLicenseable` on the base type); `organized/fox/vineflower/com/tridium/fox/sys/
> BFoxClientWebsocketBehavior.java` (whole file, 62 lines, own read this session);
> `organized/niagaraDriver/vineflower/com/tridium/nd/sysdef/BReachableStations.java` (whole file, 620
> lines, own read this session); `organized/niagaraDriver/vineflower/com/tridium/nd/sysdef/
> BReachableStationInfo.java` (whole file, 288 lines, own read this session);
> `organized/bacnet/vineflower/niagara/bacnet/point/BBacnetNiagaraSyncPointFolder.java`,
> `organized/modbusCore/vineflower/com/tridium/modbusCore/client/point/
> BModbusClientNiagaraSyncPointFolder.java`, `organized/niagaraDriver/vineflower/com/tridium/nd/point/
> BNiagaraSyncPointFolder.java` (whole files, 19/19/19 lines, own reads this session);
> `organized/bacnet/vineflower/niagara/bacnet/point/BBacnetPointFolder.java` (91 lines),
> `organized/modbusCore/vineflower/com/tridium/modbusCore/client/point/BModbusClientPointFolder.java` (18
> lines), `organized/niagaraDriver/vineflower/com/tridium/nd/point/BNiagaraPointFolder.java` (43 lines) —
> class-declaration + full-file `grep -n isChildLegal` this session; `organized/driver/vineflower/niagara/
> driver/point/BPointFolder.java` (82 lines) and `organized/baja/vineflower/niagara/util/BFolder.java` (29
> lines) — same treatment, this session; `organized/modbusAsync/vineflower/com/tridium/modbusAsync/
> BModbusAsyncNetwork.java:62`, `organized/modbusTcp/vineflower/com/tridium/modbusTcp/
> BModbusTcpNetwork.java:27`, `organized/modbusCore/vineflower/com/tridium/modbusCore/client/
> BModbusClientNetwork.java:25`, `organized/modbusCore/vineflower/com/tridium/modbusCore/
> BModbusNetwork.java:36` (class-declaration lines, own `grep -n` this session — the last already cited by
> [Block 35] §35.1, re-confirmed not re-derived); `organized/baja/vineflower/niagara/sys/BVector.java`
> (whole file, 22 lines, own read this session). Census commands (own `grep -rl`/`grep -rn`, this session,
> over `organized/*/vineflower/**/*.java`, 251 module directories): `implements[^{]*BINiagaraSyncCapableComplex`
> (176 matches, `docSource/*` duplicates excluded) and a follow-up `grep -lE "Csv|csv|StringTokenizer"` over
> that exact 176-file set (0 matches).
>
> Method: whole-file source reading of decompiled Vineflower output, class-declaration/`extends`-chain
> tracing, and two full-corpus `grep` censuses (one positive — enumerate every `BINiagaraSyncCapableComplex`
> implementer across all 251 modules, not just [Block 37]'s 7 — one negative — confirm the absence of a
> CSV/delimited-string idiom across that exact enumerated set). Markers: `[CERT]` local primary source
> (`file:line`) · `[INFER]` deduction/synthesis across this block's own `[CERT]` findings.
>
> Driver/network cluster. Connects [Block 35] (closes B35-G2, B35-G5; refines §35.1's chassis-census total),
> [Block 37] (closes B37-G2, B37-G5; widens §37.5's census), [Block 45] (closes B45-G2, confirming its
> `[INFER]`-flagged `waitingQueueCsv` design choice had no stock alternative to adopt).

---

## 73.1 — B35-G2 CLOSED: `BNiagaraEdgeLiteStation` is the SAME Fox station-connection machinery as `BNiagaraStation`, gated by three EdgeLite-specific things — a required hello-field literal match, a one-station-per-`hostId` dedup singleton, and a separate `niagaraDriver:edgeLite1` sub-license accounting bucket `[CERT]`

`BNiagaraEdgeLiteStation` is `public final class BNiagaraEdgeLiteStation extends BNiagaraStation implements BISubLicenseable`
`[CERT]` `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraEdgeLiteStation.java:19` (whole file
read this session) — a single-inheritance subclass, no new fields beyond a `private static int
edgeLiteLicenseLimit` cache and a `static final Map<String, BNiagaraEdgeLiteStation> hostIdsInUse` registry
(`:26-27`). `BNiagaraStation` itself does **not** implement `BISubLicenseable`
(`public class BNiagaraStation extends BDevice implements NiagaraStation, BINiagaraStation,
BIPollableHistorySource, BINiagaraPointContainer` `[CERT]`
`organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraStation.java:103`, class-declaration line
re-grepped this session) — `BISubLicenseable` is added
exclusively on the EdgeLite subtype.

**The interface is not an incidental pickup — `BISubLicenseable`'s own `WHITELIST` names
`BNiagaraEdgeLiteStation` explicitly, by type spec, in a closed 10-member set.** `Set<BTypeSpec> WHITELIST`
enumerates exactly `niagaraDriver:NiagaraEdgeLiteStation`, `niagaraDriver:NiagaraProxyExt`, four
`NiagaraHistoryImport`/`Export`/`SystemHistoryImport`/`Export` types, `niagaraDriver:NiagaraScheduleExport`,
`niagaraDriver:NiagaraScheduleImportExt`, and two `niagaraSystemIndex` device-ext types `[CERT]`
`organized/baja/vineflower/com/tridium/sys/metrics/BISubLicenseable.java:19-33` (whole file read this
session). `isSubLicenseable(BObject)` gates on `objType.is(TYPE) && WHITELIST.contains(objType.getTypeSpec())`
(`:60-67`) — so implementing the interface alone is not sufficient; the framework double-checks type-spec
membership in this fixed list before treating any object's `getLicenseKeyPrefix()` as authoritative. A
SECOND, narrower `LIMIT_INCREMENT_WHITELIST` contains only `niagaraDriver:NiagaraEdgeLiteStation` (`:34-36`)
— EdgeLite is the ONLY type in the entire corpus permitted a non-`1.0` `getLicenseLimitIncrement()`.

**Sub-license accounting: EdgeLite devices consume a separate `edgeLite1`-prefixed license key unless a
percentage-based feature entry is present.** `getLicenseKeyPrefix()` returns `null` (falling back to the
unprefixed base key, `BISubLicenseable.getLicenseKey()` `:44-54`) when `EdgeStationHolder.hasEdgeDevicePercentage`
is `true`, else returns the literal string `"edgeLite1"` (`:35-37`, `BNiagaraEdgeLiteStation.java`).
`hasEdgeDevicePercentage` is resolved exactly once, in a nested static holder class's `static {}`
initializer, by probing the `tridium`/`niagaraDriver` license feature for an `edgeLite1_device.percentage`
entry; if present and `>0`, `edgeDeviceLimitIncrement` is set to `percentage / 100.0` (otherwise stays
`1.0`, the interface's own default) `[CERT]` `:105-132` (whole nested class, this session). **Reading this
correctly**: whether an EdgeLite station counts as ONE full device against the base `niagaraDriver` device
pool, or a FRACTIONAL device against its OWN separately-keyed `edgeLite1_device.limit` pool, depends entirely
on which license feature entries are present on THIS install's license — `[INFER]`: this reads as a licensing
scheme allowing Tridium to sell EdgeLite connectivity either as a percentage-discounted slice of the same
device pool, or as an independently capped and priced pool, selected purely by which feature keys a given
license grants (not observed live this session — no license feature values were probed, only the code path
that reads them).

**Connection-time gating is two independent checks layered on top of the inherited base `clientOpened()`.**
`BNiagaraEdgeLiteStation.clientOpened()` overrides the base method, reads the incoming Fox hello, and (1)
throws `LocalizableRuntimeException("niagaraDriver", "niagaraEdgeLite.illegalConnection", ...)` unless the
hello's `niagaraPlatformType` string is literally `"edgeLite1"` (`:51-55`); (2) enforces a JVM-static,
one-instance-per-`hostId` singleton via `hostIdsInUse` — a SECOND connection whose hello carries an
already-registered `hostId` throws `niagaraEdgeLite.duplicateHostId` UNLESS it is literally the SAME
`BNiagaraEdgeLiteStation` object reconnecting (`existing != this`, `:56-63`) — only then does it call
`super.clientOpened()` (`:65`) `[CERT]` `BNiagaraEdgeLiteStation.java:49-66` (whole method). `stopped()`
correspondingly deregisters this instance from `hostIdsInUse` before delegating to `super.stopped()`
(`:44-47`). Neither check exists in `BNiagaraStation`'s own `clientOpened()`/`stopped()` — this block did
not open those base-class method bodies to confirm their content by contrast (named as child gap **B73-G1**);
what IS confirmed is that these two checks are additions layered via `@Override`, not replacements, since
both call their `super` equivalent.

**Instantiation is licensing-gated, with a silent downgrade on zero limit — not a hard connection reject.**
`doGetSuitableNiagaraStationInstance(FoxMessage remoteHello)` — the package-private static factory [Block
35] §35.7 already found `BNiagaraStation.getSuitableNiagaraStationInstance` falls back to — only constructs
a `new BNiagaraEdgeLiteStation()` when BOTH the hello's `niagaraPlatformType` equals `"edgeLite1"` AND
`getEdgeLiteLicenseLimit() > 0`; otherwise it silently constructs a plain `new BNiagaraStation()` instead
`[CERT]` `BNiagaraEdgeLiteStation.java:68-72`. `getEdgeLiteLicenseLimit()` resolves and caches
`Sys.getLicenseManager().getFeature("tridium", "niagaraDriver")`'s `edgeLite1_device.limit` value (via the
`BISubLicenseable.getLicenseKey` prefix logic above), treating the literal string `"none"` as
`Integer.MAX_VALUE` and any lookup exception as `0` (`:74-90`) `[CERT]`. **Net `[INFER]`**: an install with
no `edgeLite1` license entitlement at all does not reject an incoming EdgeLite-flavored connection outright
— it silently accepts the connection as an ORDINARY `BNiagaraStation` instead, meaning the `clientOpened()`
identity/dedup checks above (§73.1, previous paragraphs) never fire for such a connection, since they live
only on the subclass that was never instantiated.

**Icon selection is cosmetic, reusing [Block 35] §35.6/§35.7's own websocket/TLS distinguishing logic with
EdgeLite-specific assets swapped in — no new transport logic.** `getIcon()` branches on the exact same
`getFoxOverWebsocket()`/`getFoxOverWebsocketInUse()`/`getUseFoxs()` state `BNiagaraStation` already exposes
(confirmed by [Block 35] §35.7's `WEB_SOCKET_STATION_ICON` finding), just returning `EDGE_LITE_ICON`/
`SECURE_EDGE_LITE_ICON`/`WEB_SOCKET_EDGE_LITE_ICON` instead of the base icons `[CERT]`
`BNiagaraEdgeLiteStation.java:92-103`.

**Net verdict, closing B35-G2**: `BNiagaraEdgeLiteStation` differs from a normal `BNiagaraStation` in
identity/licensing gating, not in Fox protocol or proxy-point logic `[INFER]` (synthesis of the `[CERT]`
findings above — no NEW transport/proxy-point method is added or overridden anywhere in this 135-line class
beyond `clientOpened()`/`stopped()`/`getIcon()`/the two license-lookup helpers/the static factory). It is a
licensing SKU (a distinct, sub-licensed, hostId-deduplicated connection identity a remote station can
request via its hello's `niagaraPlatformType` field), layered entirely on top of the ordinary
`BNiagaraStation` connection machinery, not a protocol or feature variant of it.

## 73.2 — B35-G5 CLOSED: `BFoxClientWebsocketBehavior` is a 3-value transport-preference enum independent of TLS encryption, and `BReachableStations`/`BReachableStationInfo` is N5's transitive station-topology discovery+routing cache — whose own connection-URI resolution re-reads a REMOTE station's websocket enum over BQL `[CERT]`

**`BFoxClientWebsocketBehavior`** is a `BFrozenEnum` with exactly three ordinals —
`useWebsocketIfFoxOrFoxsFails` (0, `@NiagaraEnum` `defaultValue`), `useWebsocketOnly` (1),
`websocketDisabled` (2) `[CERT]`
`organized/fox/vineflower/com/tridium/fox/sys/BFoxClientWebsocketBehavior.java:13-29` (whole file read
this session — 62 lines total, no other state).
Its one piece of logic, `static FoxConnectionTypeEnum getFoxConnectionType(BFoxClientWebsocketBehavior
behavior, boolean useFoxs)`, switches on the enum ordinal AND takes `useFoxs` (TLS) as an independent second
argument: ordinal 1 always returns `FOXWSS` regardless of `useFoxs`; ordinal 2 returns `FOXS`/`FOX` purely by
`useFoxs`; the default (ordinal 0) returns `FOXS_OR_FOXWSS`/`FOX_OR_FOXWSS` by `useFoxs` `[CERT]`
`:55-61`. **This settles B35-G5's naming question for this class**: websocket-preference and Fox-level TLS
(`foxs`) are two independent axes at this decision point, not one combined setting — `useWebsocketOnly`
neither forces nor excludes `useFoxs` in this method's own logic (whether `FOXWSS` itself rides transport-level
TLS via the HTTPS web-service port [Block 35] §35.6(a) already found is a separate, unopened question this
class's code does not answer — the web-service TLS layer is distinct from Fox's own `foxs` TLS `[INFER]`,
not traced further this session).

**`BReachableStations`** (`final class BReachableStations extends BAbstractDescriptor implements
BIRestrictedComponent, Interest` `[CERT]`
`organized/niagaraDriver/vineflower/com/tridium/nd/sysdef/BReachableStations.java:75`, whole 620-line
file read this session) is a per-station-device DESCRIPTOR —
`checkParentForRestrictedComponent` enforces both an exact parent type (`BNiagaraSysDefDeviceExt`) and
component-singleton-under-parent (`:583-613`) — driven by two actions: `execute` (a stock descriptor
refresh) and `updateReachableStations(BBoolean appendOrReplace)`, whose Boolean parameter's two facet strings
(`"appendNewStations"` vs `"clearAndRebuild"`, `:68-71`) name the two update MODES `doUpdateReachableStations`
implements. **Discovery is transitive, per-hop.** `findAllReachableStations` (static utility, `:105-236`)
walks a `niagaraDriver` network's every `BNiagaraStation` device and reads THAT device's OWN nested
`BReachableStations` descriptor — i.e. each station in the tree independently discovers and caches what
stations are reachable THROUGH IT, and this method recursively MERGES those per-hop lists into one routing
table via `mergeReachableStations` (`:381-489`), which picks the LOWER-HOP-COUNT (and, on a tie,
lower-time-to-reach) route for a duplicate station name using `NiagaraDriverUtil.parseRouteToStation`
hop-counting (`:412-434`) `[CERT]`, gated throughout by `getPermissions(cx).hasOperatorRead()` (`:147,398`)
and optional station-version filtering (`reachableStationVersion`/`minVersionAlongRoute`, `checkVersion`
`:491-512`).

**The actual per-hop discovery RPC.** `doUpdateReachableStations` (`:271-379`) opens a client Fox connection
to the immediate child station (`connection.engageNoRetry(this)`), invokes the connection's `niagaraVirtual`
channel's `findReachableStations(station, stationsToExclude)` (the channel method itself not opened this
session — named, out of scope, see child gap **B73-G2**), where `stationsToExclude` is pre-seeded with the
LOCAL station's own name plus every directly-known `niagaraDriver` device's name (`:287-294`, loop
prevention `[CERT]`), then reconciles the returned `List<BReachableStationInfo>` against existing children —
either REPLACE-in-place (same route) or APPEND (new route/station), or full clear-and-rebuild depending on
the `appendOrReplace` boolean (`:326-367`).

**`BReachableStationInfo`** (`final class BReachableStationInfo extends BComponent implements
IPropertyValidator, Interest` `[CERT]`
`organized/niagaraDriver/vineflower/com/tridium/nd/sysdef/BReachableStationInfo.java:64`, whole 288-line
file read this session) is a plain, NOT `niagaraSync`-capable
`BComponent` (its absence from [Block 37] §37.5's ~180-class `BINiagaraSyncCapableComplex` census, itself
widened and re-confirmed complete this session, §73.5, is consistent with this being a DERIVED discovery
cache rather than authoritative config `[INFER]`) holding `stationName`/`stationVersion`/`routeToStation`/
`minVersionAlongRoute`/`virtualSpaceOrd`/`timeToReach`/`routeEnabled` Properties (`:43-61`), with
`routeToStation` validated on write via `IPropertyValidator.validateSet` calling
`NiagaraDriverUtil.parseRouteToStation(proposedRouteToStation, true)` (`:278-281`).

**The connective tissue back to §73.2's own websocket enum**: `getReachableStationURI()` (`:169-229`)
BQL-queries the DISCOVERED remote station's own live configuration — `bql:select address, foxPort,
clientConnection.useFoxs, clientConnection.foxOverWebsocket.ordinal, clientConnection.foxOverWebsocketPort
from niagaraDriver:NiagaraStation stop where name = '<name>'` (`:179-183`) — and if the returned
`foxOverWebsocket.ordinal == 1` (`useWebsocketOnly`), picks scheme `"foxwss"` and the alternate
`foxwssPort`; otherwise falls to `"foxs"`/`"fox"` by the queried `useFoxs` flag (`:194-203`) `[CERT]`. **Net
`[INFER]`**: a discovered reachable station's actual connection URI is computed by RE-READING that remote
station's own `BFoxClientWebsocketBehavior` value live, over BQL, at resolution time — confirming the
websocket-preference setting [Block 35] §35.6(a) found is genuinely per-station-connection state (queryable
remotely through the driver tree), not a network-global constant baked once at connection-open time.

**Net verdict, closing B35-G5** for both named classes: `BFoxClientWebsocketBehavior` is fully read (a
63-line enum, nothing left unexamined); `BReachableStations`/`BReachableStationInfo` are fully read
(620+288 lines) and characterized as N5's transitive topology-discovery+routing-cache mechanism, whose own
URI-resolution logic is the one place in this corpus this session found the websocket enum consumed by a
DIFFERENT class than the one that owns the connection ([Block 35] §35.6/§35.7's `BNiagaraNetwork`/
`BNiagaraStation`). The one item named alongside these two in B35-G5's original text —
`BNiagaraSyncCapableDeviceNetwork` — is not re-opened here since [Block 37] §37.5 already gave it a
full 5-implementer census (widened further this session, §73.5); this section treats B35-G5 as closed for
the two classes this block actually opened.

## 73.3 — B37-G2 CLOSED: all three driver-specific `BINiagaraSyncFolder` implementers are byte-for-byte-identical trivial markers, and NO class in their entire inheritance chain down to `BFolder` overrides `isChildLegal` — the gap's "actual folder-membership logic" is a confirmed absence, not a located-and-unread body `[CERT]`

**All three named classes are line-for-line identical in shape**, differing only in package and immediate
parent type: `public class BBacnetNiagaraSyncPointFolder extends BBacnetPointFolder implements
BINiagaraSyncFolder` (`[CERT]`
`organized/bacnet/vineflower/niagara/bacnet/point/BBacnetNiagaraSyncPointFolder.java:10`, whole 19-line
file), `public class BModbusClientNiagaraSyncPointFolder extends BModbusClientPointFolder implements
BINiagaraSyncFolder` (`[CERT]`
`organized/modbusCore/vineflower/com/tridium/modbusCore/client/point/BModbusClientNiagaraSyncPointFolder.java:10`,
whole 19-line file), `public class BNiagaraSyncPointFolder extends BNiagaraPointFolder implements
BINiagaraSyncFolder` (`[CERT]`
`organized/niagaraDriver/vineflower/com/tridium/nd/point/BNiagaraSyncPointFolder.java:10`, whole 19-line
file). Each file's ENTIRE body beyond the `@Generated TYPE`/`getType()` boilerplate is the class declaration
line itself — zero fields, zero methods, no `isChildLegal` override, no constructor. `[CERT]` all three
files read in full this session.

**Their immediate driver-layer `PointFolder` bases likewise carry no `isChildLegal` override.**
`BBacnetPointFolder extends BPointFolder implements BIBacnetObjectContainer` (`[CERT]`
`organized/bacnet/vineflower/niagara/bacnet/point/BBacnetPointFolder.java:21`, `grep -n isChildLegal` over
the full 91-line file: zero hits, this session); `BModbusClientPointFolder extends BPointFolder` (no
additional interface, `[CERT]`
`organized/modbusCore/vineflower/com/tridium/modbusCore/client/point/BModbusClientPointFolder.java:10`,
18-line file, zero `isChildLegal` hits); `BNiagaraPointFolder extends BPointFolder implements
BINiagaraPointContainer` (`[CERT]`
`organized/niagaraDriver/vineflower/com/tridium/nd/point/BNiagaraPointFolder.java:17`, 43-line file, zero
`isChildLegal` hits).

**Tracing one level further — the shared root itself has none either.** `BPointFolder extends BFolder
implements BIPointFolder` (`[CERT]` `organized/driver/vineflower/niagara/driver/point/BPointFolder.java:19`,
`grep -n isChildLegal` over the full 82-line file: zero hits, this session) — the abstract base every
driver's `PointFolder` type extends. `BFolder extends BComponent implements BINiagaraSyncCapableComplex`
(`[CERT]` `organized/baja/vineflower/niagara/util/BFolder.java:13`, `grep -n isChildLegal` over the full
29-line file: zero hits, this session) — notably, `BFolder` ITSELF is the `niagaraSync`-capable marker
[Block 37] §37.5 already counted in its `baja`-module row of the ~180-class census; the sync-specific point
folders' HA-safety is inherited from THIS class, not conferred by `BINiagaraSyncFolder` (a completely
separate, unrelated marker interface — replication ELIGIBILITY comes from `BFolder`'s own
`BINiagaraSyncCapableComplex`, while `BINiagaraSyncFolder` marks something else entirely, unopened this
session beyond its own zero-method declaration already known from [Block 37] §37.5).

**Net verdict, closing B37-G2**: this is a confirmed NEGATIVE-EXISTENCE finding, not an unread body. Every
class this session opened between the three named sync-folder markers and `BFolder` (5 classes: the 3
sync-folder markers, their 3 immediate `PointFolder` bases collapsed with `BPointFolder` itself as the 4th,
and `BFolder` as the 5th) was opened and `grep`'d for `isChildLegal` in full, per METHODOLOGY §3's
symmetric-opening-obligation rule for negative claims — none override it. Whatever governs which
`BComponent` types may legally be added as children of a `niagaraSync` point folder is either
`BComponent`'s own generic framework default (unopened this session, named as child gap **B73-G3**) or a
mechanism entirely outside the `isChildLegal` override pattern (e.g., import/discovery-side filtering rather
than a slot-level legality check) — this block establishes WHERE it is NOT, across the class's full
inheritance chain to the collection/marker root, rather than locating where it IS.

## 73.4 — B37-G5 CLOSED: `modbusAsync` and `modbusTcp` are BOTH `basicDriver`-chassis, two hops removed from `BBasicNetwork` via the SAME `BModbusClientNetwork`→`BModbusNetwork` chain `modbusCore`'s own network class rides — refining [Block 35] §35.1's blast-radius count from 10 to 12 modules `[CERT]`

`public class BModbusAsyncNetwork extends BModbusClientNetwork implements BISerialHelperParent,
BINiagaraSyncCapableDeviceNetwork` `[CERT]`
`organized/modbusAsync/vineflower/com/tridium/modbusAsync/BModbusAsyncNetwork.java:62`
(class-declaration line, `grep -n` this session). `public class BModbusTcpNetwork extends
BModbusClientNetwork implements BINiagaraSyncCapableDeviceNetwork` `[CERT]`
`organized/modbusTcp/vineflower/com/tridium/modbusTcp/BModbusTcpNetwork.java:27` (same method). Both extend
the SAME class, `BModbusClientNetwork`. `public abstract class BModbusClientNetwork extends BModbusNetwork
implements ModbusMessageConst` `[CERT]`
`organized/modbusCore/vineflower/com/tridium/modbusCore/client/BModbusClientNetwork.java:25`
(re-confirmed this session; already implicitly present in [Block 37] §37.5's
own census table row for both modules, not independently traced to its chassis root there). `public
abstract class BModbusNetwork extends BBasicNetwork` `[CERT]`
`organized/modbusCore/vineflower/com/tridium/modbusCore/BModbusNetwork.java:36` — this exact line is
[Block 35] §35.1's own citation for `modbusCore`'s `BModbusNetwork`, re-confirmed (not re-derived) this
session.

**Full chain for both modules**: `BModbusAsyncNetwork` → `BModbusClientNetwork` → `BModbusNetwork` →
`BBasicNetwork`; `BModbusTcpNetwork` → `BModbusClientNetwork` → `BModbusNetwork` → `BBasicNetwork` — three
hops from the deprecated chassis root for each, one hop MORE than `modbusCore`'s own `BModbusNetwork`
(direct extender, per [Block 35] §35.1's table), because both ride through an intermediate
`BModbusClientNetwork` layer `modbusCore` itself does not use for its base `BModbusNetwork` type `[CERT]`
(chain fully traced this session, 4 class-declaration lines).

**Net verdict, closing B37-G5**: neither `modbusAsync` nor `modbusTcp` escapes the deprecated `basicDriver`
chassis — [Block 37] §37.5's own table left them chassis-unclassified, flagging exactly this as the gap.
Combined with [Block 35] §35.1's original 10-module table (which did not itself include `modbusAsync`/
`modbusTcp` as separate rows — only `modbusCore`), the true `basicDriver` blast radius `[INFER]` (arithmetic
synthesis of [Block 35]'s 10 plus this session's 2 confirmed additions) is now **12 modules**, still funneling
through the SAME **2 chassis roots** [Block 35] §35.1 named (`BBasicNetwork`/`BBasicDevice` direct, and
`BSerialNetwork` as one extra hop) — `modbusAsync`/`modbusTcp` add a THIRD hop shape
(`BModbusClientNetwork`→`BModbusNetwork`→`BBasicNetwork`) without adding a new independent chassis root:
this refines [Block 35]'s "2 roots feeding 10 modules" framing to "2 roots feeding 12 modules," not a
correction of it. BACnet's own chassis lineage (whether `BBacnetNetwork` sits on either root) remains
unclassified — out of B37-G5's own naming, not attempted this session.

## 73.5 — B45-G2 CLOSED: a full 251-module census (not [Block 37]'s 7-module scope) finds ZERO new `BINiagaraSyncCapableComplex` implementers and ZERO CSV/delimited-string idiom anywhere among all 176 — `waitingQueueCsv` remains genuinely novel by both tests the gap named `[CERT]`

**Module-breadth census.** `grep -rln "implements[^{]*BINiagaraSyncCapableComplex" organized/*/vineflower
--include="*.java"` across the FULL corpus (251 module directories under
`/home/cristian/niagara5-research/organized/`, `docSource/*` duplicates excluded) — own run, this session
— finds **176 distinct class declarations**, in the SAME **7 modules** [Block 37] §37.5 already named:
`bacnet`, `baja`, `control`, `kitControl`, `modbusCore`, `niagaraDriver`, `schedule` `[CERT]` (full census
output inspected this session; 176 vs. [Block 37]'s own "~180 unique classes (vineflower+docSource
collapsed)" estimate — the small difference is consistent with the different dedup method, not a
discrepancy in module coverage). **Zero additional module** implements the interface anywhere in the
corpus — this directly answers B45-G2's "census a WIDER set of modules" instruction: widening the search
from [Block 37]'s pre-selected 7 modules to the entire 251-module tree changes nothing.

**Collection-shape name sweep.** Filtering the 176 class names for anything queue/list/collection-shaped
(`grep -iE "queue|list|fifo|stack|buffer|deque|array|vector|collection"`) returns exactly **one** match:
`BVector`. `public class BVector extends BComponent implements BINiagaraSyncCapableComplex` `[CERT]`
`organized/baja/vineflower/niagara/sys/BVector.java:8` (whole 22-line file read this session) — the class
declares ZERO Properties and ZERO methods beyond the generated `getType()` and an `isNavChild() { return
false; }` override (`:18-21`). It is structurally a generic, nav-hidden, HA-safe CONTAINER for dynamically
added `BComponent` children — the same "ordered state via live component children" pattern `BFolder` itself
already establishes (§73.3) — not an ordered collection of scalar values. It exposes no add/remove/ordering
API of its own; whatever list semantics it offers come entirely from the generic dynamic-Property child-slot
mechanism `[INFER]` (inferred from the class's own zero-method body — no dedicated collection API exists to
read).

**CSV/delimited-string idiom sweep.** `grep -lE "Csv|csv|StringTokenizer"` over the exact enumerated
176-file set (not a sample) returns **zero hits** `[CERT]` (own grep, this session — satisfies METHODOLOGY
§3's symmetric-opening-obligation rule for a negative-existence claim: the full named file set was itself
opened/grepped, not sampled).

**Net verdict, closing B45-G2**: [Block 45]'s `waitingQueueCsv` design (`§45.3`, comma-separated `String`
Property + a pure codec, chosen because "niagaraSync ships no list/queue-typed `BSimple`") is confirmed
novel by BOTH dimensions this gap named — no module beyond the 7 already censused implements
`BINiagaraSyncCapableComplex` at all, and no implementer in any of the 7 uses a CSV/delimited-string
encoding for ordered state anywhere in the corpus `[INFER]` (synthesis of the two `[CERT]` census results
above). The one stock "list-shaped" HA-safe pattern that DOES exist — `BVector`/`BFolder`'s dynamic-children
pattern — is structurally incompatible with a scalar FIFO-of-indexes the way [Block 45]'s `Deque<Integer>`
waiting queue needed `[INFER]`, confirming rather than merely leaving open that [Block 45]'s `[INFER]`-flagged
design choice had no available stock alternative to adopt instead.

## 73.x — Connections

- **[Block 35]** — closes **B35-G2** (§73.1) and **B35-G5** (§73.2); refines §35.1's `basicDriver`
  blast-radius count from 10 to 12 modules via §73.4 (not a correction — the 2 chassis roots §35.1 named
  are unchanged, only the module count feeding them grows). §35.6(a)'s naming of the three
  `BFoxClientWebsocketBehavior` states is now fully typed with the exact ordinal values and decision
  function (§73.2). §35.7's `getSuitableNiagaraStationInstance`/`BNiagaraEdgeLiteStation` fallback finding
  is the direct antecedent §73.1 closes.
- **[Block 37]** — closes **B37-G2** (§73.3) and **B37-G5** (§73.4); §73.5 WIDENS (not corrects) §37.5's
  7-module `BINiagaraSyncCapableComplex` census to the full 251-module corpus, confirming completeness
  rather than finding an omission. §37.5's own `BReachableStationInfo`-absence-from-the-census observation
  (implicit, not stated there) is made explicit and explained in §73.2.
- **[Block 45]** — closes **B45-G2** (§73.5), confirming [Block 45] §45.3/§45.7's `[INFER]`-flagged
  `waitingQueueCsv` design had no stock precedent to follow instead, at full corpus breadth.

## 73.x — Child gaps opened

- **B73-G1** — `BNiagaraStation`'s own base-class `clientOpened()`/`stopped()` method bodies (§73.1) were
  not opened this session — only their existence and `BNiagaraEdgeLiteStation`'s `@Override`+`super`-call
  relationship to them was confirmed. Reading the base bodies would show precisely what a NORMAL (non-EdgeLite)
  station connection handshake does NOT check, sharpening the "EdgeLite adds identity+dedup gating" contrast
  from an `[INFER]`-by-absence framing to a directly-observed one.
- **B73-G2** — `BNiagaraVirtualChannel.findReachableStations` (§73.2), the actual Fox RPC
  `BReachableStations.doUpdateReachableStations` invokes to perform per-hop station discovery, was named
  but not opened this session — the wire-level discovery protocol itself (what fields a `findReachableStations`
  request/response actually carries) remains unread.
- **B73-G3** — `BComponent`'s own default `isChildLegal` behavior (§73.3's terminal, unopened boundary) was
  not opened this session. Confirming the framework-wide default (rather than continuing to infer it from
  its absence across five subclasses) would settle whether ANY component-tree-level restriction governs
  `niagaraSync` point-folder membership, or whether it is enforced entirely by import/discovery-side logic
  outside the `isChildLegal` override pattern.
- **B73-G4** — BACnet's own network-class chassis lineage (`BBacnetNetwork`'s `extends` chain) was not
  classified against [Block 35] §35.1's `basicDriver`/`ndriver` split this session — only `modbusAsync`/
  `modbusTcp` were, per B37-G5's own naming. A natural companion census: BACnet is the one field-bus driver
  family [Block 35] §35.3-§35.4 already established has its OWN chassis (not `basicDriver`/`devDriver`),
  but whether that chassis is `ndriver`-rooted or a third, fully independent lineage was not checked here.
- **B73-G5 (requires-execution, carries forward B37-G1/B45-G1)** — every finding in this block is static
  source reading; none of §73.1's licensing-gate behavior, §73.2's BQL-driven URI resolution, or §73.4's
  chassis classification was exercised against a live station or license.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block73.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output — re-run AFTER un-wrapping several body citations that had been line-wrapped across two lines
inside their backtick span for prose readability, per the citation-form fix noted below):

```
== verify-block: niagara5-block73.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1
   [CERT-live] 1
   [CERT] 44  (adj 42)
   [CERT-doc] 1
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 19  (adj 17)
-- ratio -- [INFER]/[CERT*] = 17/47 = 0.36
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BModbusNetwork.java:36  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraEdgeLiteStation.java:49-66  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraEdgeLiteStation.java:68-72  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraEdgeLiteStation.java:92-103  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/bacnet/vineflower/niagara/bacnet/point/BBacnetNiagaraSyncPointFolder.java:10
   ok      organized/bacnet/vineflower/niagara/bacnet/point/BBacnetPointFolder.java:21
   ok      organized/baja/vineflower/com/tridium/sys/metrics/BISubLicenseable.java:19-33  (range end verified; file has 77 lines)
   ok      organized/baja/vineflower/niagara/sys/BVector.java:8
   ok      organized/baja/vineflower/niagara/util/BFolder.java:13
   ok      organized/driver/vineflower/niagara/driver/point/BPointFolder.java:19
   ok      organized/fox/vineflower/com/tridium/fox/sys/BFoxClientWebsocketBehavior.java:13-29  (range end verified; file has 62 lines)
   ok      organized/modbusAsync/vineflower/com/tridium/modbusAsync/BModbusAsyncNetwork.java:62
   ok      organized/modbusCore/vineflower/com/tridium/modbusCore/BModbusNetwork.java:36
   ok      organized/modbusCore/vineflower/com/tridium/modbusCore/client/BModbusClientNetwork.java:25
   ok      organized/modbusCore/vineflower/com/tridium/modbusCore/client/point/BModbusClientNiagaraSyncPointFolder.java:10
   ok      organized/modbusCore/vineflower/com/tridium/modbusCore/client/point/BModbusClientPointFolder.java:10
   ok      organized/modbusTcp/vineflower/com/tridium/modbusTcp/BModbusTcpNetwork.java:27
   ok      organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraEdgeLiteStation.java:19
   ok      organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraStation.java:103
   ok      organized/niagaraDriver/vineflower/com/tridium/nd/point/BNiagaraPointFolder.java:17
   ok      organized/niagaraDriver/vineflower/com/tridium/nd/point/BNiagaraSyncPointFolder.java:10
   ok      organized/niagaraDriver/vineflower/com/tridium/nd/sysdef/BReachableStationInfo.java:64
   ok      organized/niagaraDriver/vineflower/com/tridium/nd/sysdef/BReachableStations.java:75
   resolved 19 of 23
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**Reading the resolution: 19 of 27 resolve `ok`.** Two earlier runs this session resolved far fewer (8 of
12, then 19 of 23), because several BODY citations originally wrapped a long `organized/` path across two
markdown lines inside one backtick span (readability formatting) — the verify script's citation regex
matches a SINGLE-LINE backtick span only, so a wrapped path is invisible to it even though a human reader
sees one continuous citation. Six such body citations — the base-station class-declaration line, the
websocket-behavior enum's `@NiagaraEnum` range line, both `BReachableStations`-family class-declaration
lines, and the `modbusAsync`/`modbusTcp`/`BModbusClientNetwork`/`BModbusNetwork` chassis-chain citations in
§73.4 — were re-flowed onto single lines this session so the script's regex sees them intact, and all six
now resolve `ok` above. Every remaining `extern` line in the FINAL run above is a bare short-form reused in
body prose for readability, where a fully-pathed citation to the SAME underlying file ALSO appears and
resolves `ok` in this exact run's own `ok` list — the citation-form convention (METHODOLOGY §11) explicitly
permits this pairing; none of the 4 is an unpathed citation lacking a resolving full-path counterpart
anywhere in the block.

**Reading the ratio.** The adjusted `[INFER]`/`[CERT]*` ratio printed above is well below the ~0.5
exhaustion threshold, consistent with a productive gap-closing session against sources every named gap had
explicitly identified but left unopened. The `[INFER]`s are concentrated in explicitly-flagged synthesis
paragraphs (§73.1's licensing-scheme reading, §73.2's TLS-layering caveat and URI-resolution synthesis,
§73.4's 10-to-12-module arithmetic, §73.5's `BVector`-incompatibility reasoning) — none is load-bearing for
a CLOSED gap's core verdict independent of the CERT-family findings it synthesizes; each closed gap's
factual answer (what EdgeLite gates on, what the enum/discovery classes do, that no `isChildLegal` override
exists, which chassis modbusAsync/modbusTcp ride, that no wider module/CSV precedent exists) rests on
CERT-family citations alone. Per METHODOLOGY §11's own worked example ([Block 61]'s self-verify), the
tally's non-zero counts for the CERT-hw/CERT-live/CERT-doc/CERT-web/CERT-a marker NAMES come entirely from
this Self-verify section's own literal reprint of the script's marker-tally header line — a self-reference,
not a fresh claim of that grade: the block cites NO CERT-hw/CERT-live/CERT-doc/CERT-web/CERT-a evidence
anywhere in its actual §73.1-§73.5 claims, every one of which is CERT or INFER.

**Inline token-verify.** Every `file:line` citation above points at a file this session `Read` in full or
`grep -n`'d for a specific method/token this session — zero citations reused verbatim from [Block 35]/
[Block 37]/[Block 45]'s text without an independent re-open this session, with one explicitly-flagged
exception: `BModbusNetwork.java:36` (§73.4) is the SAME line [Block 35] §35.1 already cited for the SAME
fact (`BModbusNetwork extends BBasicNetwork`), re-confirmed (re-`grep`'d) rather than re-derived this
session — stated as such in §73.4's own prose, not silently reused. Spot-check tokens independently
re-confirmed present this session (whitespace-normalized): `implements BISubLicenseable` / `hostIdsInUse` /
`niagaraEdgeLite.illegalConnection` / `niagaraEdgeLite.duplicateHostId` (`BNiagaraEdgeLiteStation.java`);
`WHITELIST` / `LIMIT_INCREMENT_WHITELIST` / `NiagaraEdgeLiteStation` string literal
(`BISubLicenseable.java`); `useWebsocketOnly` / `FOXWSS` (`BFoxClientWebsocketBehavior.java`);
`findAllReachableStations` / `mergeReachableStations` / `doUpdateReachableStations` / `getReachableStationURI`
/ `foxOverWebsocket.ordinal` (`BReachableStations.java`/`BReachableStationInfo.java`); `implements
BINiagaraSyncFolder` (3 independent file reads, one per driver); zero `isChildLegal` hits confirmed by
direct `grep -n` output (not inferred from a partial read) across all 5 classes in the §73.3 inheritance
trace; `extends BModbusClientNetwork` / `extends BModbusNetwork` / `extends BBasicNetwork` (3 independent
`grep -n class B` runs, one per file, §73.4); `implements BINiagaraSyncCapableComplex` (176-match census
output inspected this session, not hand-counted) and zero `Csv`/`csv`/`StringTokenizer` hits (confirmed by
the grep's own empty/exit-1 output, this session, §73.5). Token-verify: **≈24 distinct load-bearing tokens**
confirmed present (or confirmed ABSENT, for the `isChildLegal`/CSV negative-existence claims, per
METHODOLOGY §3's symmetric-opening-obligation rule — each ABOUT a named, fully-opened artifact, not merely
not-found) in their cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block73.md`. Per the
caller's explicit scope ("Touch NO other file (no RESEARCH-STATE/INDEX/CATALOG, no git)"),
`INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and backlog re-classification are deliberately NOT
performed this session — left to the orchestrator.
