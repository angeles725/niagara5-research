# Block 104 — `BNiagaraStation`'s base connection-handshake bodies, the `findReachableStations` wire protocol (both hops), `BComponent`'s unconditional `isChildLegal` default, BACnet's `BLoadableNetwork`/`BLoadableDevice` chassis lineage, a full `BWrapperBoxChannel` subclass census, what actually re-arms `niagaraSync`'s license check, `BFoxProxySession.getRemoteNiagaraVersion`'s exact signature, and `BOrionDatabase`'s pluggable-RDBMS storage internals

> Research closing eight previously-opened, narrowly-scoped child gaps across the niagaraDriver/station-link,
> niagaraSync, box-channel, and Orion clusters. All eight gap texts were re-read from their own parent block
> files this session (per the ALREADY-COVERED-CHECK / GAP-ID-DISCIPLINE instructions); no gap-ID drift was
> found between the task's paraphrase and each parent block's own wording — verbatim quotes are given inline
> below and in the RETURN. Covers: **B73-G1** ([Block 73] §73.x: *"`BNiagaraStation`'s own base-class
> `clientOpened()`/`stopped()` method bodies (§73.1) were not opened this session — only their existence and
> `BNiagaraEdgeLiteStation`'s `@Override`+`super`-call relationship to them was confirmed."*) — whole-method
> reads of both bodies; **B73-G2** ([Block 73] §73.x: *"`BNiagaraVirtualChannel.findReachableStations`
> (§73.2), the actual Fox RPC `BReachableStations.doUpdateReachableStations` invokes to perform per-hop
> station discovery, was named but not opened this session — the wire-level discovery protocol itself (what
> fields a `findReachableStations` request/response actually carries) remains unread."*) — whole-method reads
> of the client-side RPC, the server-side per-hop dispatcher, and the async multi-hop worker that recurses
> through it; **B73-G3** ([Block 73] §73.x: *"`BComponent`'s own default `isChildLegal` behavior (§73.3's
> terminal, unopened boundary) was not opened this session."*) — direct read of the framework root default;
> **B73-G4** ([Block 73] §73.x: *"BACnet's own network-class chassis lineage (`BBacnetNetwork`'s `extends`
> chain) was not classified against [Block 35] §35.1's `basicDriver`/`ndriver` split this session."*) — full
> `extends`-chain trace for both `BBacnetNetwork`/`BBacnetDevice`, cross-classified against [Block 35] §35.1's
> `basicDriver` census and §35.2's `ndriver`/raw-`driver`-chassis distinction; **B92-G2** ([Block 92] §92.x:
> *"whether any OTHER `box` module type besides these two [`HistoryChannel`/`AlarmChannel`] now uses the same
> wrapper (a corpus-wide census of `BWrapperBoxChannel` subclasses/instantiations was not run this session) is
> open."*) — full corpus `grep -rl` census; **B92-G3** ([Block 92] §92.x: *"this session did not trace what
> actually TRIGGERS a fresh start cycle in practice ... whether toggling the `enabled` property alone re-runs
> `fwServiceStarted()`/`checkLicense()`, or only a full component restart does, was not verified against
> `BComponent`'s own start/stop lifecycle."*) — traced the sole `fw(15)` call site corpus-wide and its two
> callers; **B10-G3** ([Block 10] §10.x, "Named child gaps": *"`usingFoxProxySession.html`'s new
> `getRemoteNiagaraVersion()` method on `BFoxProxySession` was not cross-checked against the
> `docSource.jar`/`niagaraJavadoc.jar` API surface [B4] §4.7/§4.8 to confirm its exact signature and package
> (`niagara.fox.BFoxProxySession` vs. a moved location per BC-14)."*) — source + bajadoc + the concrete
> `fw(404)` implementation all read; **B69-G3** ([Block 69] §69.6: *"`BOrionDatabase`'s own physical storage
> implementation (only its consumer interface, `OrionSession`, was read this session) — table DDL for
> `BOrionSecurityAudit` rows, retention/purge policy, and whether it shares the station's `db/` history
> storage or a genuinely separate RDBMS file/schema."*) — whole-file reads of `BOrionDatabase`/
> `BLocalOrionDatabase` plus a corpus-wide negative-existence census for any retention/purge mechanism.
>
> Does **not** cover: `BNiagaraVirtualChannel`'s `ValueDocDecoder`/`BOG` on-wire byte encoding itself (the
> `findReachableStations` response's `size`/exception envelope fields are read, but the binary doc-encoding
> `ValueDocDecoder.decode()` uses to materialize each `BReachableStationInfo` off the wire was not opened);
> `BIloadable`'s `BUploadParameters`/`BDownloadParameters` payload classes (read only the 4-method interface
> contract, not the parameter classes' own fields); `TableBuilder`'s Property-type→SQL-column-type mapping
> (opened only far enough to confirm DDL is dynamically generated, not the exact type table); a live-station
> reproduction of any finding (all evidence below is static source reading, same constraint as every
> predecessor block in this series).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (same corpus every prior block in this series cites). No fresh decompilation — every file cited was already
> present in this corpus's `organized/` tree from prior sessions' extraction ([Block 1]'s corpus-wide
> extraction covers `niagaraDriver`/`bacnet`/`box`/`orion`/`fox`/`baja`/`driver`/`obixDriver`/`ndriver`).
>
> Sources: `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraStation.java:473-490,655-668` (whole
> `clientOpened()`/`stopped()` methods, own reads this session — file confirmed 778 lines via `wc -l`);
> `organized/niagaraDriver/vineflower/com/tridium/nd/virtual/BNiagaraVirtualChannel.java:365-449` (whole
> public `findReachableStations(BNiagaraStation,Set<String>)`, client-side RPC), `:451-552` (whole private
> `findReachableStations(FoxCircuit)`, server-side per-hop dispatcher/merge), `:957-1025` (whole
> `FindReachableStations` inner `Runnable`/`Executor` class through its `run()` body — file confirmed 1059
> lines via `wc -l`), all own reads this session; `organized/baja/vineflower/niagara/sys/BComponent.java:614-
> 620` (`isParentLegal`/`isChildLegal` defaults, own read — file confirmed 1169 lines); `organized/bacnet/
> vineflower/niagara/bacnet/BBacnetNetwork.java:122`, `organized/bacnet/vineflower/niagara/bacnet/
> BBacnetDevice.java:120` (class-declaration lines, own `grep -n` this session);
> `organized/driver/vineflower/niagara/driver/loadable/{BLoadableNetwork.java:24,BLoadableDevice.java:23,
> BILoadable.java}` (whole 22-line `BILoadable.java` read, other two class-declaration lines, own reads this
> session); `organized/driver/vineflower/niagara/driver/BDeviceNetwork.java:65` (class-declaration line, own
> `grep -n`); `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraNetwork.java:101-108` (class
> declaration, re-`grep`'d this session — already `[CERT]`'d whole-class by [Block 73] §73.2 for a different
> fact); `organized/ndriver/vineflower/niagara/ndriver/BNNetwork.java:33` (class-declaration line, own
> `grep -n`); `organized/obixDriver/vineflower/niagara/obix/driver/BObixNetwork.java:47` (class-declaration
> line, re-`grep`'d this session — the SAME citation [Block 35] §35.2 already made, re-confirmed not
> re-derived); own corpus-wide `grep -rl "extends BWrapperBoxChannel" organized/*/vineflower --include="*.java"`
> (2 hits); `organized/baja/vineflower/niagara/sys/BAbstractService.java:100-127,164-202,245-288` (whole
> `updateStatus()`/`checkLicense()`/`fw()`+`fwServiceStarted()`+`fwChanged()`, re-read past [Block 92] §92.5's
> prior citation of the same file); `organized/baja/vineflower/com/tridium/sys/service/ServiceManager.java:91-
> 140,182-223,270-323` (whole `register()`/`startAllServices()`/`startService()` methods, first open of this
> file in this corpus — file confirmed 541 lines); own corpus-wide `grep -rn "\.fw(15" organized/*/vineflower
> --include="*.java"` (exactly 1 hit); `organized/baja/vineflower/com/tridium/sys/schema/
> ComponentSlotMap.java:1615-1623` (the `mount()` call site that invokes `ServiceManager.register()`, own
> targeted read this session); `organized/fox/vineflower/niagara/fox/BFoxProxySession.java:1-22,89-91` (package
> + imports + whole `getRemoteNiagaraVersion()` method, own read this session);
> `organized/docDeveloper/vineflower/doc/fox/niagara/fox/BFoxProxySession.bajadoc:343-352` (the
> `getRemoteNiagaraVersion` `<method>` element, own read this session); `organized/fox/vineflower/com/tridium/
> fox/sys/BFoxSession.java:1134-1165` (whole `fw()` `case 404` branch, own read this session — first open of
> this specific case in this corpus); `organized/orion/vineflower/com/tridium/orion/BOrionDatabase.java`
> (whole 120-line file, own read this session — first whole-file open of this specific file in this corpus,
> [Block 69] having read only `OrionSession.java`); `organized/orion/vineflower/com/tridium/orion/
> BLocalOrionDatabase.java` (whole 544-line file, own read this session); `organized/orion/vineflower/com/
> tridium/orion/sql/TableBuilder.java:26`, `organized/orion/vineflower/com/tridium/orion/priv/db/
> TableDefinition.java` (class-declaration line + `wc -l`, own reads); `organized/rdb/vineflower/niagara/rdb/
> BRdbms.java:81,346,365,399` (class declaration + 3 abstract method signatures, own `grep -n`); own
> corpus-wide `grep -rln "purge|retention|maxRecords|maxAge" organized/orion/vineflower --include="*.java"`
> (zero hits).
>
> Method: whole-method/whole-file source reading of decompiled Vineflower output; class-declaration/`extends`-
> chain tracing; four corpus-wide `grep` censuses (one exhaustive-file-count for `BWrapperBoxChannel`
> subclasses, one exhaustive-call-site-count for `.fw(15`, one bajadoc-XML open, one negative-existence census
> for Orion retention/purge — each reported as an exhaustive result, not a sample, per METHODOLOGY §3).
> Markers: `[CERT]` local primary source (`file:line`) · `[INFER]` deduction/synthesis across this block's own
> `[CERT]` findings.
>
> **Type:** `evidence` — every section closes a named parent-block gap with a fresh, this-session file-read,
> chain trace, or exhaustive `grep` census; the few `[INFER]` claims are explicitly-flagged syntheses drawn
> directly across this block's own dense `[CERT]` reads, not free-standing speculation.
>
> niagaraDriver/station-link, niagaraSync, box-channel, and Orion cluster. Connects [Block 73] (closes
> B73-G1, B73-G2, B73-G3, B73-G4), [Block 35] (refines/corroborates §35.1/§35.2's `basicDriver`/`ndriver`/
> raw-`driver`-chassis taxonomy with BACnet now classified), [Block 92] (closes B92-G2, B92-G3), [Block 10]
> (closes B10-G3), [Block 69] (closes B69-G3).

---

## 104.1 — B73-G1 CLOSED: base `BNiagaraStation.clientOpened()`/`stopped()` do NEITHER of EdgeLite's two identity checks — no `niagaraPlatformType` literal match, no `hostId` dedup singleton — confirming the "EdgeLite adds gating" contrast by direct observation, not by absence `[CERT]`

**`clientOpened()`, whole method, read this session:**
```java
public void clientOpened() {
   try {
      FoxMessage hello = this.getClientConnection().session().getRemoteHello();
      this.setVersion(hello.getString("version", ""));
      this.setHostModel(hello.getString("hostModel", ""));
      this.setHostModelVersion(hello.getString("hostModelVersion", ""));
   } catch (Exception e) {
      this.getLogger().log(Level.WARNING, "Failed to open client connection: " + e, ...);
   }

   for (BINiagaraDeviceExt devicelet : this.getNiagaraDeviceExts()) {
      try {
         devicelet.clientOpened();
      } catch (Exception e) {
         this.getLogger().log(Level.SEVERE, "Exception occurred while opening client: " + e, ...);
      }
   }
}
```
`[CERT]` `BNiagaraStation.java:473-490`. The base method reads exactly three plain string fields off the
incoming Fox hello (`version`/`hostModel`/`hostModelVersion`) into ordinary Properties, then fans out to each
mounted `BINiagaraDeviceExt`'s own `clientOpened()`. **It never inspects a `niagaraPlatformType` field at
all**, and never consults any static registry keyed by host identity — both absent by direct read, not by a
partial-read inference. This is the exact literal-match gate [Block 73] §73.1 already found
`BNiagaraEdgeLiteStation.clientOpened()` layers on top (`niagaraPlatformType == "edgeLite1"` or throw), now
confirmed to be a pure ADDITION with nothing analogous in the base to contrast against.

**`stopped()`, whole method, read this session:**
```java
public void stopped() throws Exception {
   super.stopped();
   if (Sys.getStation() != null && Sys.getStation().isRunning()) {
      BFoxServerConnection serverConn = this.serverConnection;
      if (serverConn != null) {
         serverConn.setPersistent(false);
         if (!serverConn.isConnected() && serverConn.getParent() != null) {
            serverConn.getParent().asComponent().remove(serverConn.getPropertyInParent());
         } else {
            serverConn.removeConnectionTarget(this);
         }
      }
   }
}
```
`[CERT]` `BNiagaraStation.java:655-668`. The base body's entire concern is the OUTGOING `BFoxServerConnection`
this station instance owns (making it non-persistent, then either removing the connection component outright
if it's already disconnected, or just detaching this station as a connection target) — it never touches a
`hostIdsInUse`-style registry either. This is the exact counterpart [Block 73] §73.1 flagged: EdgeLite's own
`stopped()` deregisters itself from the static `hostIdsInUse` map BEFORE calling this exact `super.stopped()`
body — now directly confirmed, not inferred, that the base body does nothing equivalent.

**B73-G1 verdict: CLOSED.** Reading both base bodies directly upgrades [Block 73] §73.1's own framing from
`[INFER]`-by-absence ("neither check exists in `BNiagaraStation`'s own `clientOpened()`/`stopped()`... this
block did not open those base-class method bodies to confirm their content by contrast") to a directly-observed
`[CERT]` contrast: a NORMAL station connection handshake does no hello-literal validation and no per-host
singleton bookkeeping whatsoever — both of EdgeLite's two gating mechanisms are genuinely net-new additions
layered via `@Override`+`super`-call, not a stricter version of something the base already partially did.

## 104.2 — B73-G2 CLOSED: the `findReachableStations` Fox RPC carries a semicolon-batched exclusion-name request and a count-prefixed, `ValueDocDecoder`-encoded response list; the recursive per-hop worker re-issues the SAME client RPC one hop further, not a separate protocol `[CERT]`

**Client-side request/response, whole method read this session** (`BNiagaraVirtualChannel.findReachableStations
(BNiagaraStation station, Set<String> stationsToExclude)`, `:365-449`): the request is a single `FoxMessage`
opened on a `"findReachable"` `FoxCircuit`, carrying the exclusion set as one or more `"x"` fields, each holding
UP TO 10 station names joined by `;` (`StringJoiner(";")`, batched every 10th name into a fresh field) `[CERT]`
`:372-387`. The response is read back off the SAME circuit as: an optional `"exception"` string field (if
present, translated via `Fox.exceptionTranslator.messageToException(resp)` and thrown) `[CERT]` `:395-397`;
otherwise an `"size"` int field giving the row count `[CERT]` `:399`; then, for `size` rows, a
`ValueDocDecoder` (obtained via `this.makeDefaultDecoder(inputStream, null)`) is walked `size` times, each
`decoder.next()`+`decoder.decode()` call materializing one `BReachableStationInfo` off the circuit's raw
`InputStream` `[CERT]` `:404-427` — the standard Niagara value-doc binary encoding, not a bespoke JSON/text
shape (its own byte-level grammar is out of this session's scope, named as child gap **B104-G1**). Each
decoded `info`'s `virtualSpaceOrd` is then locally re-mapped from the REMOTE station's virtual-space ORD space
into the CALLER's own relative session ORD space via `NiagaraVirtualUtil.fromServerOrdToClientVirtual` before
being added to the result list `[CERT]` `:410-424`.

**Server-side dispatcher, whole method read this session** (private `findReachableStations(FoxCircuit
circuit)`, `:451-552`): reads the request's `"x"` field(s), re-splits every batch on `;` back into a flat
`Set<String> stationsToExclude`, adds the LOCAL station's own name to that set (so a station never reports
itself back to a caller already walking through it), then iterates the local `BNiagaraNetwork`'s
`getBDeviceList()`, filtering to exactly those `BNiagaraStation` devices that are simultaneously
not-disabled/not-fault/not-down, not already in the exclusion set, and pass
`station.getPermissions(this.getSessionContext()).hasOperatorRead()` `[CERT]` `:462-481`. For each surviving
station, it builds a fresh `BReachableStationInfo` seeded with `stationName`/`stationVersion`/
`routeToStation=localName+";"+stationName`/`minVersionAlongRoute=Sys.getBajaVersion()` — i.e. this immediate
1-hop entry is populated LOCALLY, without any further RPC — then spawns ONE
`BNiagaraVirtualChannel.FindReachableStations` async worker PER station, run via `CompletableFuture.runAsync`
against a per-station work queue (`this.station.getNiagaraNetwork().getWorkers()`), and blocks on
`CompletableFuture.allOf(...).get(FIND_REACHABLE_STATIONS_TIMEOUT, TimeUnit.MILLISECONDS)`
(`FIND_REACHABLE_STATIONS_TIMEOUT` defaults to 120,000 ms, overridable via the system property
`niagara.findReachableStations.timeoutMillis`) `[CERT]` `:117,483-526`. After the timeout/completion, every
worker's own `reachableStationInfos` list is merged into the response map via `Map.compute`, preferring
whichever entry has FEWER hops (parsed via `NiagaraDriverUtil.parseRouteToStation`), or on a hop-count tie,
the LOWER `timeToReach` `[CERT]` `:528-552` — this is the exact merge policy [Block 73] §73.2's
`mergeReachableStations` finding already described for the OUTER (`findAllReachableStations`) walk, now
confirmed to be implemented identically at THIS inner, per-request-server-side layer too, not a separate
algorithm.

**The recursive worker re-issues the SAME client RPC, confirmed by direct read (`FindReachableStations.run()`,
`:957-1025`):** each worker `engageNoRetry`s a Fox client connection to its own target `this.station`, fetches
that connection's own `"niagaraVirtual"` channel instance, and calls
`channel.findReachableStations(this.station, this.stationsToExclude)` `[CERT]` `:1004,1009-1010` — the
IDENTICAL client-side method this section's first paragraph already fully documents, one hop further out, then
adds the elapsed `duration` to every returned `info`'s own `timeToReach` `[CERT]` `:1011-1015`. **This settles
B73-G2's own framing precisely**: there is exactly ONE `findReachableStations` wire protocol in this corpus,
used recursively at every hop, not a distinct "deeper" protocol for multi-hop chains — the recursion is
achieved entirely by the server-side dispatcher fanning out N async copies of the SAME client call, each one
hop further from the original caller, with loop-prevention carried purely in the growing `stationsToExclude`
set passed down at each level (the exact mechanism [Block 73] §73.2 already named for the OUTER walk,
confirmed here to be the SAME set object threaded through the per-hop RPC layer too).

**B73-G2 verdict: CLOSED.** The wire-level discovery protocol carries: request = batched (`;`-joined,
10-per-field) excluded station names under repeated `"x"` fields; response = an optional `"exception"` string,
else an `"size"` int followed by that many value-doc-encoded `BReachableStationInfo` rows. The per-hop
recursion mechanism is the SAME client RPC re-issued by an async worker per locally-known station, not a
separate protocol — closing the gap's exact question ("what fields a `findReachableStations` request/response
actually carries").

## 104.3 — B73-G3 CLOSED: `BComponent.isChildLegal()`'s framework-wide default is an UNCONDITIONAL `true` — no component-tree-level restriction governs `niagaraSync` point-folder membership by default; the mechanism (if any) is entirely import/discovery-side `[CERT]`

`BComponent`'s own defaults, read directly this session:
```java
public boolean isParentLegal(BComponent parent) {
   return true;
}

public boolean isChildLegal(BComponent child) {
   return true;
}
```
`[CERT]` `organized/baja/vineflower/niagara/sys/BComponent.java:614-620` — both one-line, unconditional
`true` returns, with no field reads, no type checks, no facet/flag inspection of any kind. This is the
terminal, framework-root boundary [Block 73] §73.3 traced five subclasses down to
(`BBacnetNiagaraSyncPointFolder`/`BModbusClientNiagaraSyncPointFolder`/`BNiagaraSyncPointFolder` → their three
`PointFolder` bases collapsed with `BPointFolder` → `BFolder`) without finding an override anywhere along the
chain; this session confirms the chain's own destination is itself a no-op.

**B73-G3 verdict: CLOSED.** `BComponent.isChildLegal()`'s generic framework default places NO restriction on
what `BComponent` may be added as a child of anything, anywhere in this corpus, absent an explicit override —
directly settling the gap's own question: whatever governs which components may legally populate a
`niagaraSync` point folder is NOT enforced anywhere in the `isChildLegal` override pattern (six classes now
confirmed, root to leaf, all either silent or explicitly returning the unconditional default) — it must be
enforced entirely by import/discovery-side logic (e.g. a driver's own point-discovery/import wizard choosing
what it offers to create) outside the component-tree legality-check mechanism `BComponent` itself provides.
`[INFER]` for the "therefore import/discovery-side" conclusion specifically — a genuine, if narrow,
elimination-argument synthesis across this and [Block 73] §73.3's own six `[CERT]` reads, not a directly
observed import-wizard mechanism (out of this gap's own scope to trace further).

## 104.4 — B73-G4 CLOSED: BACnet's network/device chassis is `BLoadableNetwork`/`BLoadableDevice` → `BDeviceNetwork`/`BDevice` — the SAME raw-`driver`-chassis root [Block 35] §35.2 already found for `obixDriver`, reached via one extra "bulk upload/download" hop neither `ndriver`'s own `BNNetwork`/`BNDevice` nor `obixDriver` provide `[CERT]`

**The full chain, both sides, traced this session:**
```
public class BBacnetNetwork extends BLoadableNetwork implements BIService, BINiagaraSyncCapableDeviceNetwork
```
`[CERT]` `organized/bacnet/vineflower/niagara/bacnet/BBacnetNetwork.java:122`;
```
public abstract class BLoadableNetwork extends BDeviceNetwork implements BILoadable
```
`[CERT]` `organized/driver/vineflower/niagara/driver/loadable/BLoadableNetwork.java:24`;
```
public abstract class BDeviceNetwork extends BComponent implements BIDeviceFolder, BIStatus, BIPingable, BILicensed
```
`[CERT]` `organized/driver/vineflower/niagara/driver/BDeviceNetwork.java:65`. Device side, identical shape:
`public class BBacnetDevice extends BLoadableDevice implements BIBacnetObjectContainer, ...` `[CERT]`
`organized/bacnet/vineflower/niagara/bacnet/BBacnetDevice.java:120`; `public abstract class BLoadableDevice
extends BDevice implements BILoadable` `[CERT]` `organized/driver/vineflower/niagara/driver/loadable/
BLoadableDevice.java:23`. **Full chains**: `BBacnetNetwork` → `BLoadableNetwork` → `BDeviceNetwork` →
`BComponent`; `BBacnetDevice` → `BLoadableDevice` → `BDevice`.

**Cross-classified against [Block 35] §35.1/§35.2's own taxonomy: this is neither `basicDriver` nor
`ndriver` — it is the SAME "raw-`driver`-chassis" category §35.2 already named for `obixDriver`.**
[Block 35] §35.1 established `basicDriver`'s chassis roots are `BBasicNetwork`/`BBasicDevice` (`basicDriver`
module) — BACnet shares NEITHER class anywhere in its chain, `[CERT]` by the full chain traced above containing
zero `basicDriver`-package types. [Block 35] §35.2 separately established a THIRD category, re-quoted and
re-confirmed this session: `public class BObixNetwork extends BDeviceNetwork implements BIService` `[CERT]`
`organized/obixDriver/vineflower/niagara/obix/driver/BObixNetwork.java:47` (the exact citation [Block 35]
§35.2 already made, re-`grep`'d not re-derived) — described there as "the SAME base classes `ndriver`'s own
chassis wraps... `obixDriver` simply skips the `ndriver` convenience layer and implements the driver contract
by hand," naming it "raw-`driver`-chassis." **`ndriver`'s own chassis root is confirmed, this session, to
ALSO be `BDeviceNetwork` directly**: `public abstract class BNNetwork extends BDeviceNetwork implements
BIService` `[CERT]` `organized/ndriver/vineflower/niagara/ndriver/BNNetwork.java:33` — and niagaraDriver's OWN
network class extends the identical root a third, independent way: `public final class BNiagaraNetwork extends
BDeviceNetwork implements BIService, NiagaraNetwork, BINiagaraNetwork, ...` `[CERT]`
`organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraNetwork.java:101-102` (re-`grep`'d this session;
already `[CERT]`'d whole-class by [Block 73] §73.2 for its Fox-connection behavior, not previously classified
against [Block 35]'s chassis taxonomy). **`BDeviceNetwork` is therefore the single, shared modern chassis root
that `ndriver` (via `BNNetwork`), `obixDriver` (directly), `niagaraDriver` itself (directly), and now BACnet
(via one extra `BLoadableNetwork` hop) all independently sit on** — four different "how you get there" shapes
converging on the same non-deprecated base, none of them `basicDriver`.

**The one extra hop is not incidental — `BILoadable` is a real, distinct bulk upload/download contract
neither `ndriver`'s bare `BNNetwork`/`BNDevice` nor `obixDriver`'s direct `BDeviceNetwork` use provides:**
```java
public interface BILoadable extends BInterface {
   void upload(BUploadParameters var1);
   void doUpload(BUploadParameters var1, Context var2) throws Exception;
   void download(BDownloadParameters var1);
   void doDownload(BDownloadParameters var1, Context var2) throws Exception;
}
```
`[CERT]` `organized/driver/vineflower/niagara/driver/loadable/BILoadable.java` (whole 22-line file, this
session's own read) — a paired bulk-transfer action contract (`upload`/`download`, each with a synchronous
public entry point and an internal `doUpload`/`doDownload` worker taking an explicit `Context`), the classic
"learn device points into the station" / "push station config out to the device" bulk operation shape a
field-bus driver like BACnet's device-object scanning needs and neither `ndriver`'s nor `obixDriver`'s bare
chassis expose. `BUploadParameters`/`BDownloadParameters`'s own field contents were not opened this session
(child gap **B104-G2**).

**B73-G4 verdict: CLOSED.** BACnet's network/device chassis lineage is `BDeviceNetwork`/`BDevice`-rooted — the
SAME modern, non-deprecated root [Block 35] §35.2 already classified as "raw-`driver`-chassis" for
`obixDriver`, and the SAME root `ndriver`'s own `BNNetwork`/`BNDevice` wrap — reached via one extra
`BLoadableNetwork`/`BLoadableDevice` hop that adds the `BILoadable` bulk-transfer contract. This directly
answers the gap's own framing ("whether that chassis is `ndriver`-rooted or a third, fully independent
lineage"): it is **neither** in the strict sense — not literally routed through `BNNetwork`/`BNDevice` — but
it IS rooted in the exact same underlying `BDeviceNetwork`/`BDevice` base `ndriver` itself merely wraps, making
it a sibling of `ndriver` (and of `obixDriver` and `niagaraDriver` itself) rather than a fourth, independent
chassis family. [Block 35] §35.1's "2 roots" framing (`basicDriver`'s `BBasicNetwork`/`BBasicDevice` plus the
`BSerialNetwork` sub-chassis) is UNCHANGED by this finding — BACnet was never counted toward that root and
remains outside it; this section instead completes the corpus's chassis map by classifying the one major
driver family [Block 35] §35.3-§35.4 had already flagged as chassis-unclassified.

## 104.5 — B92-G2 CLOSED: exactly two classes in the entire corpus extend `BWrapperBoxChannel` — `BAlarmChannel` and `BHistoryChannel`, both already known; no other `box` module type uses the wrapper `[CERT]`

`grep -rl "extends BWrapperBoxChannel" organized/*/vineflower --include="*.java"` (own run, this session,
corpus-wide across all module directories, `docSource/*` duplicates excluded — the exact command the gap's own
text names): **exactly 2 files**, `organized/box/vineflower/com/tridium/box/BAlarmChannel.java` and
`organized/box/vineflower/com/tridium/box/BHistoryChannel.java` `[CERT]` — the SAME two classes [Block 92]
§92.3 already fully characterized (`super("alarm:AlarmBoxChannel")`/`super("history:HistoryBoxChannel")`).

**B92-G2 verdict: CLOSED.** Zero additional `box` module type has adopted the lazy-resolving,
graceful-degradation `BWrapperBoxChannel` decorator pattern beyond the two [Block 92] §92.3 already documented
— the N4→N5 dependency-inversion refactor (`box` core dropping its `alarm`/`history` compile-time dependency)
was applied to exactly the two channel types that needed it, not adopted more broadly across `box`'s own
channel roster (e.g. no `BChartChannel`/`BControlChannel` wrapper exists, consistent with [Block 92] §92.3's
own observation that `chart`/`control`/`bql`/`gx` were ALSO dropped from `box`'s dependency list — but this
session's own corpus-wide grep confirms none of those four modules ships a `box`-side wrapper channel of its
own at all, at least not one using this specific `BWrapperBoxChannel` mechanism).

## 104.6 — B92-G3 CLOSED: `checkLicense()` re-runs ONLY when a service component is (re-)mounted into the station's component tree — at station boot, or a fresh add/re-add of the service component — NEVER merely by toggling its `enabled` property, which reaches only `updateStatus()` `[CERT]`

**The sole call site, corpus-wide, confirmed by exhaustive `grep`:** `grep -rn "\.fw(15" organized/*/vineflower
--include="*.java"` (own run, this session) returns **exactly one hit**,
`organized/baja/vineflower/com/tridium/sys/service/ServiceManager.java:296`:
`service.fw(15, null, null, null, null);` `[CERT]`, inside `startService(S service)` (whole method,
`ServiceManager.java:270-323`, first open of this file in this corpus). `BAbstractService.fw()`'s own `case
15` dispatch (already `[CERT]`'d by [Block 92] §92.5) routes `fw(15,...)` to `fwServiceStarted()`, which is
the ONLY caller of the private `checkLicense()` method anywhere in `BAbstractService.java` (re-confirmed by
this session's own re-read, `:245-272`) — there is exactly one path into the license check in this entire
corpus, and it is `ServiceManager.startService()`.

**`startService()` itself has exactly two callers, both traced this session:** `register(S service)`
(`ServiceManager.java:91-140`) calls `this.startService(service)` at `:135`, but ONLY `if (this.servicesRunning
&& (!this.migratingServiceContainer || Station.stationStarted))` — i.e. only when a `BIService` component is
being freshly REGISTERED into the `ServiceManager` while services are already running station-wide; and
`startAllServices()` (`ServiceManager.java:182-223`) calls `startService` on every currently-known service in
a loop at `:219` (and once more for a to-be-migrated `ServiceContainer` at `:204`) — this is the STATION BOOT
path, invoked once per service at station startup. **`register()`'s own trigger, traced one level further**:
`ComponentSlotMap`'s `mount(BComponentSpace space, Context context, ...)` calls
`Nre.getServiceManager().register((BComponent & BIService)this.instance)` immediately after binding the
component to its space, whenever `this.instance instanceof BIService` `[CERT]`
`organized/baja/vineflower/com/tridium/sys/schema/ComponentSlotMap.java:1619-1623` — i.e. `register()` (and
therefore, downstream, `checkLicense()`) fires exactly when a `BIService`-typed `BComponent` is MOUNTED into a
running component space: at whole-station load (mounting the whole tree), or when such a component is freshly
added (e.g. deleted-and-re-pasted, or programmatically `add()`-ed) to an ALREADY-RUNNING station.

**Toggling `enabled` alone does NOT retrigger any of this — confirmed by direct contrast with
`fwChanged()`'s own dispatch, already `[CERT]`'d by [Block 92] §92.5 and re-read this session:**
```java
private void fwChanged(Property prop) {
   if (this.isRunning()) {
      if (prop.equals(enabled)) {
         this.updateStatus();
      }
      ...
```
`[CERT]` `BAbstractService.java:278-288` — a live `enabled`-property write reaches ONLY `updateStatus()` (which
recomputes the visible `BStatus` bits purely from the ALREADY-SET `fatalFault`/`configFault`/`enabled` flags,
`:100-127`), never `checkLicense()`. Since a licensing-caused `fatalFault=true` is never reset to `false`
anywhere in this class (re-confirmed [Block 92] §92.5 finding), toggling `enabled` off then back on while
unlicensed will run `updateStatus()` twice but leave `fatalFault` untouched — the service stays visibly faulted
throughout, because the ONLY thing that can clear or re-evaluate `fatalFault` is a fresh `fwServiceStarted()`
call, which only fires via the mount/register path above, never via a property change on an already-mounted
component.

**B92-G3 verdict: CLOSED.** What actually re-arms `niagaraSync`'s (or any `BAbstractService` subclass's)
license check is: (1) a full station restart (`startAllServices()` walks every service on boot), or (2) the
service component being freshly (re-)mounted into an already-running station's component tree (delete+re-add,
or a programmatic `add()`) — NOT a full "component restart" in any more general sense (no `stop()`/`start()`
lifecycle action independent of tree mount/unmount was found to call `startService()`), and specifically NOT
merely flipping `getEnabled()`/`setEnabled()`, which is wired to `updateStatus()` alone and structurally cannot
clear or re-evaluate a `fatalFault` a prior `checkLicense()` call set.

## 104.7 — B10-G3 CLOSED: `BFoxProxySession.getRemoteNiagaraVersion()` is `public Version getRemoteNiagaraVersion()` in `niagara.fox.BFoxProxySession`, returning `niagara.util.Version`, implemented via a generic `fw(404, moduleName, modulePart, ...)` framework hook whose `null`-moduleName case returns the ALREADY-CACHED remote Fox handshake version, not a fresh RPC `[CERT]`

**Exact package, signature, and return type, read directly this session:**
```java
package niagara.fox;
...
import niagara.util.Version;

public abstract class BFoxProxySession extends BSession implements AuthenticationRealm {
   ...
   public Version getRemoteNiagaraVersion() {
      return (Version)this.fw(404, null, null, null, null);
   }
```
`[CERT]` `organized/fox/vineflower/niagara/fox/BFoxProxySession.java:1,18,89-91` — confirming the gap's own
named question directly: the class already lives at `niagara.fox.BFoxProxySession` (the POST-BC-14
`niagara.*`-namespace location, not `javax.baja.fox`), and the method returns `niagara.util.Version` (the
generic Niagara version-comparison type used corpus-wide, not a Fox-specific type).

**The bajadoc entry independently confirms the same signature and dates the method as genuinely N5-new:**
```
<!-- niagara.fox.BFoxProxySession.getRemoteNiagaraVersion() -->
<method name="getRemoteNiagaraVersion"  public="true">
...
<tag name="@since">Niagara 5.0</tag>
<return>
<type class="niagara.util.Version"/>
</return>
</method>
```
`[CERT]` `organized/docDeveloper/vineflower/doc/fox/niagara/fox/BFoxProxySession.bajadoc:343-352` — the
`@since Niagara 5.0` tag confirms [Block 10] §10.8's own reading (this is a genuinely new N5 method, not a
renamed N4 carryover), and Tridium's own auto-generated API doc independently reproduces the exact same
package/return-type pair this session's source read already established.

**The `fw(404)` implementation, traced to its concrete handler this session (`BFoxSession.java:1134-1165`,
first open of this specific `case` in this corpus):**
```java
case 404:
   String moduleName = (String)a;
   ...
   if (moduleName != null && !"baja".equalsIgnoreCase(moduleName)) {
      // ... live sysChannel.stationCall("module.version", key.getBytes()) round-trip for a NAMED module
   } else {
      remoteModuleVersion = this.getConnection().getRemoteVersion();
   }
   return remoteModuleVersion;
```
`[CERT]` — `getRemoteNiagaraVersion()` calls `fw(404, null, null, null, null)` with `moduleName == null`, which
takes the `else` branch: it returns `this.getConnection().getRemoteVersion()` — the remote host's overall
Niagara version ALREADY RECORDED at Fox connection handshake time, not a fresh network round-trip. The SAME
`case 404` hook is more general-purpose than `BFoxProxySession`'s own public method exposes: passing a
non-null, non-`"baja"` `moduleName` instead triggers a live `sysChannel.stationCall("module.version", ...)`
RPC to fetch a SPECIFIC OTHER module's remote version (keyed `module:part` for an N4 peer, bare `module` for
an N5-or-newer peer, per the remote host's own detected version) — an unopened, more general sibling mechanism
not exercised by `getRemoteNiagaraVersion()` itself, named as a minor residual for completeness rather than a
tracked child gap (it does not bear on B10-G3's own narrower question).

**B10-G3 verdict: CLOSED.** Exact signature: `public niagara.util.Version getRemoteNiagaraVersion()` on
`niagara.fox.BFoxProxySession`, `@since Niagara 5.0` per its own bajadoc, implemented as a thin wrapper over a
generic `fw(404,...)` "get remote module version" framework hook whose `null`-moduleName invocation returns the
Fox connection's own already-cached handshake-time remote version.

## 104.8 — B69-G3 CLOSED: `BOrionDatabase` is a genuinely separate, PLUGGABLE-RDBMS-backed schema (HSQLDB/Db2/MySQL/etc. via `niagara.rdb.BRdbms`), NOT the station's file-based `db/` history/alarm store; table DDL is dynamically generated per registered type via `TableBuilder`, schema versioning is per-app via a persisted `BOrionAppVersion` row, and NO retention/purge mechanism exists anywhere in the `orion` module `[CERT]`

**Storage backend: a real, pluggable SQL RDBMS connection, not a Niagara-proprietary file format.**
`BOrionDatabase` (abstract, `extends BComponent implements BIOrionDatabaseObject`, whole 120-line file read
this session) declares `public abstract BRdbms getRdbms();` `[CERT]`
`organized/orion/vineflower/com/tridium/orion/BOrionDatabase.java:19,33` — `niagara.rdb.BRdbms` (`abstract
class BRdbms extends BDevice implements BILicensed`, `organized/rdb/vineflower/niagara/rdb/BRdbms.java:81`,
own `grep -n` this session) is the generic Niagara RDBMS-connection device type, itself abstract over the
ACTUAL installed RDBMS driver module (concrete `getConnection`/`getRdbmsContext` abstract methods,
`BRdbms.java:365,399`). The concrete implementation, `BLocalOrionDatabase` (whole 544-line file read this
session), is initialized with `void init(BOrionService service, BRdbms rdb)` `[CERT]`
`BLocalOrionDatabase.java:42,53,63-66` and its `doesTableExist()` method explicitly branches on the LIVE
`BRdbms` instance's own type spec — `BTypeSpec.make("rdbHsqlDb:HsqlDatabase")`,
`BTypeSpec.make("rdbDb2:Db2Database")` (uppercases table names for both), `BTypeSpec.make("rdbMySQL:MySQLDatabase")`
(reads a `databaseName` schema-name property) `[CERT]` `BLocalOrionDatabase.java:427-467` — i.e. WHICH
concrete RDBMS backs a given Orion database is a station-operator-configurable choice (whichever `rdb*` driver
module's `BRdbms` device is wired into `BOrionService`), not a fixed proprietary format at all. This directly
answers the gap's own "genuinely separate RDBMS file/schema" framing: yes, genuinely separate — Orion's tables
live in whatever external/embedded SQL database the station's own `BRdbms` device connects to, structurally
unrelated to `niagara.history`'s own binary `db/` record-store files ([Block 78]/[Block 84]/[Block 92]'s
`alarm.adb` format).

**Table DDL is dynamically generated per registered `OrionType`, not fixed/hand-written SQL.** `createTables()`/
`createTable(OrionType)` build `DdlCommand[]` arrays via `new TableBuilder(this, tableDef.getOrionType())`
`[CERT]` `BLocalOrionDatabase.java:361-398` (`class TableBuilder`, `organized/orion/vineflower/com/tridium/
orion/sql/TableBuilder.java:26`, 238-line file, own `grep -n`/`wc -l` this session — its own
Property-type→SQL-column-type mapping was not opened in detail, named as child gap **B104-G3**). `boot()`
registers every `BIOrionApp`'s declared `OrionType`s PLUS three always-present built-in types —
`BOrionAppVersion.ORION_TYPE`, `BOrionAudit.ORION_TYPE`, and `BOrionSecurityAudit.ORION_TYPE` (the exact type
[Block 69] §69.4/§69.6 traced the `session.insert(secRec)` write path for, its own TABLE now identified as one
of these three always-registered built-ins) `[CERT]` `BLocalOrionDatabase.java:78-98`. `open()`'s
`ensureTableExists()` checks each of the three built-ins' tables via a LIVE JDBC `DatabaseMetaData.getTables()`
call against a real `java.sql.Connection` obtained through `SecurityUtil.doPrivileged(() ->
this.rdb.getNonPrivilegedConnection(null))`, creating the table via generated DDL only if it does not already
exist `[CERT]` `BLocalOrionDatabase.java:100-131,416-467`.

**Schema versioning is per-app, not per-database, via a persisted row in the always-present
`BOrionAppVersion` table.** `createOrUpgradeApp(OrionSession, BIOrionApp app)` reads a persisted
`BOrionAppVersion` row keyed by the app's own type spec; if none exists, it inserts a fresh row recording the
app's current `getSchemaVersion()`; if the persisted version is OLDER, it calls
`app.performSchemaUpgrade(this, persisted.getSchemaVersion())` (an app-supplied migration hook) then updates
the persisted row; if the persisted version is NEWER than the running app's own declared version, it throws
an `OrionException("Application version mismatch: ...")` rather than silently downgrading `[CERT]`
`BLocalOrionDatabase.java:469-508`. `testMode` (a `BBoolean` service property) triggers `dropAllTables()` at
boot instead of the normal upgrade path — a diagnostic/development wipe, not a production retention mechanism
`[CERT]` `BLocalOrionDatabase.java:100,106-109,400-414`.

**No retention/purge mechanism exists anywhere in the `orion` module — a genuine, exhaustively-searched
negative-existence finding, not an unread body.** `grep -rln "purge|retention|maxRecords|maxAge"
organized/orion/vineflower --include="*.java"` (own run, this session, whole-module case-sensitive-pattern
sweep as named): **zero hits** `[CERT]`. Neither `BOrionDatabase` nor `BLocalOrionDatabase` (both whole-file
read this session) contains any row-count cap, age-based expiry, or scheduled cleanup logic of any kind —
`BOrionSecurityAudit` rows (and every other Orion-backed table) accumulate without bound absent an
application-level or operator-level cleanup outside this module's own code, structurally unlike
`niagara.history`'s own capacity-/age-based record-store rollover [Block 78]/[Block 84] already documented for
the file-based history/alarm stores.

**B69-G3 verdict: CLOSED for the questions the gap itself named (table DDL, backing-store identity), NARROWED
for retention specifically.** Table DDL: dynamically generated per `OrionType` via `TableBuilder`, against
whichever concrete `BRdbms`-typed RDBMS the station operator has configured. Backing store: a genuinely
separate, pluggable SQL RDBMS schema — NOT the station's own `db/` history/alarm binary file format, sharing
only the generic `niagara.rdb` connection-device abstraction, not any storage bytes. Retention/purge:
confirmed ABSENT from the `orion` module's own code by exhaustive corpus-wide grep — whether some retention
policy exists OUTSIDE this module entirely (e.g. a station-wide scheduled job, or is simply left to the
operator's own DBA-level table maintenance on the external RDBMS) was not checked this session, tracked as
child gap **B104-G4**.

## 104.x — Connections

- **[Block 73]** — closes **B73-G1** (§104.1), **B73-G2** (§104.2), **B73-G3** (§104.3), and **B73-G4**
  (§104.4). §104.1 upgrades §73.1's own `[INFER]`-by-absence framing to a directly-observed `[CERT]`
  contrast. §104.2 completes §73.2's "transitive per-hop" discovery-mechanism finding down to the exact wire
  fields and confirms the recursion is homogeneous (the same client RPC re-issued, not a distinct protocol).
  §104.3 confirms §73.3's own negative-existence finding terminates, correctly, at a genuine framework no-op.
  §104.4 classifies BACnet's chassis for the first time against [Block 35]'s taxonomy, the one item §73.4
  explicitly left BACnet out of scope for.
- **[Block 35]** — §104.4 reuses and extends §35.1's `basicDriver`-census and §35.2's "raw-`driver`-chassis"
  finding (re-confirming, not re-deriving, the `BObixNetwork.java:47` citation), adding BACnet and
  `niagaraDriver`'s own `BNiagaraNetwork` as two more `BDeviceNetwork`-direct/near-direct sitters alongside
  `obixDriver` and `ndriver`'s own `BNNetwork` — strengthening §35.2's "a module can be a fully current,
  non-deprecated N5 driver without using `ndriver` at all" verdict with two more confirmed instances, one of
  them (BACnet) a major bundled driver family, not a minor one.
- **[Block 92]** — closes **B92-G2** (§104.5) and **B92-G3** (§104.6), the two residual gaps that block's own
  §92.x opened. §104.6 directly extends §92.5's `BAbstractService` licensing-fault trace one further layer
  outward (from "what severity does an unlicensed feature produce" to "what actually re-triggers the check
  that could clear or re-raise it"), tracing the mechanism to `ServiceManager`/`ComponentSlotMap`, files
  neither [Block 92] nor any prior predecessor block had opened.
- **[Block 10]** — closes **B10-G3** (§104.7), confirming §10.8's own doc-only reading of
  `getRemoteNiagaraVersion()` against the actual shipped source AND its bajadoc, finding perfect agreement (no
  doc-vs-code conflict, consistent with §10.12's own "none found" verdict) and additionally tracing the
  concrete `fw(404)` implementation neither [Block 10] nor any prior block had opened.
- **[Block 69]** — closes **B69-G3** (§104.8), completing that block's own `OrionSession`-interface-only read
  into a full `BOrionDatabase`/`BLocalOrionDatabase` implementation trace; corroborates §69.4's own finding
  that Orion is a first-party, RDBMS-backed subsystem by showing the CONCRETE plumbing (`BRdbms`,
  `getNonPrivilegedConnection`, live `DatabaseMetaData` checks) behind that block's `OrionSession`-level
  reading.
- **[Block 78]/[Block 84]** — §104.8's finding that Orion tables are unbounded (no retention/purge) is a
  direct structural CONTRAST with those blocks' own capacity-/age-based history/alarm file-store rollover
  mechanisms — named explicitly rather than left implicit, since a reader could otherwise assume Orion follows
  the same pattern.

## 104.x — Child gaps opened

- **B104-G1** — `BNiagaraVirtualChannel.findReachableStations`'s response is decoded via a generic
  `ValueDocDecoder` (`this.makeDefaultDecoder(inputStream, null)`, §104.2) — this session read WHAT is decoded
  (a count-prefixed sequence of `BReachableStationInfo` objects) but not the decoder's own binary doc-encoding
  grammar itself. `investigable`, mechanical (open `ValueDocDecoder.java`, likely in `baja`), low priority
  given the request/response FIELD-level question B73-G2 actually asked is already fully answered.
- **B104-G2** — `BILoadable`'s `BUploadParameters`/`BDownloadParameters` parameter classes (§104.4) were named
  but not opened — confirming their own field contents would show exactly what a bulk device-object
  upload/download operation configures (e.g. a device filter, a progress/cancel handle). `investigable`,
  mechanical, low priority (the interface CONTRACT itself, which is what B73-G4's own text asked about, is
  already fully read).
- **B104-G3** — `TableBuilder`'s own Property-type→SQL-column-type mapping (§104.8, file present and
  `wc -l`'d but not read past its class-declaration line) was not traced this session — would give the exact
  DDL column types (`VARCHAR`/`INTEGER`/`TIMESTAMP`/etc.) Orion generates for each Niagara `BSimple` property
  type. `investigable`, mechanical (whole-file read of a 238-line class already located).
- **B104-G4** — whether ANY retention/purge policy for Orion-backed tables exists OUTSIDE the `orion` module
  itself (e.g. a scheduled housekeeping job in a different module, or `BOrionService`'s own un-opened
  properties/actions beyond `auditMode`/`securityAuditMode`) was not checked this session — §104.8's own
  negative census was scoped to `organized/orion/vineflower` only, per the gap's own "retention/purge policy"
  framing being about `BOrionDatabase` specifically. `investigable`, would need a corpus-wide (not
  `orion`-scoped) census for any Orion-table-targeting cleanup logic.
- **B104-G5 (requires-execution, carries forward every prior block's own live-station caveat)** — every
  finding in this block is static source reading; none of §104.1's connection-handshake contrast, §104.2's
  wire-protocol read, §104.6's service-restart tracing, or §104.8's RDBMS-schema finding was exercised against
  a live station, a live Fox connection, or a live Orion-backed RDBMS this session.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | Base `BNiagaraStation.clientOpened()` reads only `version`/`hostModel`/`hostModelVersion` off the hello, fans out to `BINiagaraDeviceExt`s; no `niagaraPlatformType` check, no host-identity registry | [CERT] | `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraStation.java:473-490` |
| 2 | Base `BNiagaraStation.stopped()` only manages the outgoing `BFoxServerConnection` (persistent flag, remove/detach); no `hostIdsInUse`-style deregistration | [CERT] | `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraStation.java:655-668` |
| 3 | Client-side `findReachableStations` request: `;`-joined, 10-per-field `"x"` exclusion batches; response: optional `"exception"`, else `"size"` int + that many `ValueDocDecoder`-decoded `BReachableStationInfo` rows | [CERT] | `organized/niagaraDriver/vineflower/com/tridium/nd/virtual/BNiagaraVirtualChannel.java:365-449` |
| 4 | Server-side dispatcher re-splits `"x"` batches, self-excludes, filters candidate stations by status+permission, spawns one async worker per station, merges by fewer-hops/lower-time-to-reach | [CERT] | `organized/niagaraDriver/vineflower/com/tridium/nd/virtual/BNiagaraVirtualChannel.java:451-552` |
| 5 | The async `FindReachableStations` worker re-issues the SAME client-side `findReachableStations` method one hop further | [CERT] | `organized/niagaraDriver/vineflower/com/tridium/nd/virtual/BNiagaraVirtualChannel.java:957-1025` |
| 6 | `BComponent.isParentLegal`/`isChildLegal` both unconditionally return `true` | [CERT] | `organized/baja/vineflower/niagara/sys/BComponent.java:614-620` |
| 7 | `BBacnetNetwork extends BLoadableNetwork extends BDeviceNetwork`; `BBacnetDevice extends BLoadableDevice extends BDevice` | [CERT] | `organized/bacnet/vineflower/niagara/bacnet/BBacnetNetwork.java:122`; `organized/driver/vineflower/niagara/driver/loadable/BLoadableNetwork.java:24`; `organized/driver/vineflower/niagara/driver/BDeviceNetwork.java:65`; `organized/bacnet/vineflower/niagara/bacnet/BBacnetDevice.java:120`; `organized/driver/vineflower/niagara/driver/loadable/BLoadableDevice.java:23` |
| 8 | `ndriver`'s own `BNNetwork` and niagaraDriver's own `BNiagaraNetwork` both extend `BDeviceNetwork` directly; `obixDriver`'s `BObixNetwork` too (re-confirmed) | [CERT] | `organized/ndriver/vineflower/niagara/ndriver/BNNetwork.java:33`; `organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraNetwork.java:101-102`; `organized/obixDriver/vineflower/niagara/obix/driver/BObixNetwork.java:47` |
| 9 | `BILoadable` is a 4-method bulk upload/download contract (`upload`/`doUpload`/`download`/`doDownload`) | [CERT] | `organized/driver/vineflower/niagara/driver/loadable/BILoadable.java` (whole 22-line file) |
| 10 | Exactly 2 corpus-wide `extends BWrapperBoxChannel` sites: `BAlarmChannel`, `BHistoryChannel` | [CERT] | `grep -rl "extends BWrapperBoxChannel" organized/*/vineflower --include="*.java"`, this session |
| 11 | Exactly 1 corpus-wide `.fw(15` call site: `ServiceManager.startService()` | [CERT] | `grep -rn "\.fw(15" organized/*/vineflower --include="*.java"`, this session → `organized/baja/vineflower/com/tridium/sys/service/ServiceManager.java:296` |
| 12 | `checkLicense()`'s only caller is `fwServiceStarted()`; `fwChanged()`'s `enabled`-branch calls only `updateStatus()`, never `checkLicense()` | [CERT] | `organized/baja/vineflower/niagara/sys/BAbstractService.java:245-288` |
| 13 | `startService()` is called only from `register()` (gated on `servicesRunning`) and `startAllServices()` (station boot) | [CERT] | `organized/baja/vineflower/com/tridium/sys/service/ServiceManager.java:91-140,182-223,270-323` |
| 14 | `ComponentSlotMap.mount()` calls `ServiceManager.register()` for every `BIService`-typed component it mounts | [CERT] | `organized/baja/vineflower/com/tridium/sys/schema/ComponentSlotMap.java:1619-1623` |
| 15 | `BFoxProxySession.getRemoteNiagaraVersion()`: `public Version getRemoteNiagaraVersion()`, package `niagara.fox`, returns `niagara.util.Version`, implemented via `fw(404,...)` | [CERT] | `organized/fox/vineflower/niagara/fox/BFoxProxySession.java:1,18,89-91` |
| 16 | Bajadoc independently confirms the same signature, `@since Niagara 5.0` | [CERT] | `organized/docDeveloper/vineflower/doc/fox/niagara/fox/BFoxProxySession.bajadoc:343-352` |
| 17 | `fw(404)`'s `null`-moduleName branch returns the cached `getConnection().getRemoteVersion()`; a named moduleName instead triggers a live `stationCall("module.version",...)` | [CERT] | `organized/fox/vineflower/com/tridium/fox/sys/BFoxSession.java:1134-1165` |
| 18 | `BOrionDatabase` is abstract with `abstract BRdbms getRdbms()`; `BRdbms extends BDevice implements BILicensed` | [CERT] | `organized/orion/vineflower/com/tridium/orion/BOrionDatabase.java:19,33`; `organized/rdb/vineflower/niagara/rdb/BRdbms.java:81` |
| 19 | `BLocalOrionDatabase.doesTableExist()` branches on the live `BRdbms`'s own type spec (HSQLDB/Db2/MySQL) | [CERT] | `organized/orion/vineflower/com/tridium/orion/BLocalOrionDatabase.java:427-467` |
| 20 | Table DDL generated dynamically via `TableBuilder`; 3 always-registered built-in types incl. `BOrionSecurityAudit.ORION_TYPE` | [CERT] | `organized/orion/vineflower/com/tridium/orion/BLocalOrionDatabase.java:78-98,361-398` |
| 21 | Per-app schema versioning via persisted `BOrionAppVersion` row; version-mismatch throws, older triggers `performSchemaUpgrade` | [CERT] | `organized/orion/vineflower/com/tridium/orion/BLocalOrionDatabase.java:469-508` |
| 22 | Zero corpus-wide (`orion` module) hits for `purge`/`retention`/`maxRecords`/`maxAge` | [CERT] | `grep -rln "purge|retention|maxRecords|maxAge" organized/orion/vineflower --include="*.java"`, this session |

Tally: 22 [CERT], 0 [INFER] in the table above (the two inline `[INFER]` clauses — §104.3's
elimination-argument synthesis for "therefore import/discovery-side," and §104.4's "sibling, not fourth
independent lineage" characterization — are stated inline per METHODOLOGY's own convention for a synthesis
clause, not as separate table rows). Adjusted ratio `[INFER]`/`[CERT]` ≈ **0.09** (2 inline `[INFER]` clauses
against 22 `[CERT]` claims) — low, consistent with an EVIDENCE-type block whose every closing verdict rests on
a direct file read, chain trace, or exhaustive `grep` census run this session, not recalled from memory or
extrapolated from a partial sample.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block104.md
```
(run until exit 0; literal output reported in the handback to the caller, per the task's own instruction — the
tool's own tally brackets are not pasted into this block body, per the same instruction).

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; no web tool was used.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block104.md` (the only file
written in this corpus this session, per the task's single-file constraint). `INDEX.md`/`RESEARCH-STATE.md`/
`CATALOG.md` were **not** regenerated or hand-edited — left to the orchestrator's integration step, per the
established wave convention every predecessor block in this series follows.
