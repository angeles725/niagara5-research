# Block 78 — The `box` "Building Object eXchange Protocol" is an N4-carryover modernized onto Jetty-ee11 WebSocket + Fox dual transport, plus the on-disk `alarm.adb` header format and niagaraSync's license feature

> Research closing/narrowing four child gaps. Covers: the **`box` protocol** [Block 72] surfaced (its
> jetty-web.xml made it one of three modules carrying one) — what it is, its transport, and the **actual
> N4→N5 delta** (correcting the wave-8 dispatch assumption that box was N5-new); **B72-G3** (box's WebSocket
> upgrade path + isWar status); **B58-G1** and its sub-gap **B58-G4** (the on-disk `alarm.adb` header/word
> layout, which prior N4-side memory recorded as undecoded); **B37-G4** (the `niagaraSync` license-feature
> identity and fault wiring). Does **not** cover: the full `box` frame wire-format / message opcodes (only
> the transport envelope and framing MODE are read — see child gap); the alarm record-body layout beyond the
> store header; a live box session capture.
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree `/home/cristian/niagara5-research/organized/`
> (`box`, `alarm`, `niagaraSync` `vineflower/`). N4 baseline: `/home/cristian/niagara-research/organized`
> (4.14). This block was authored directly by the orchestrator (Opus) because the wave-8 delegated writer
> for this cluster was terminated by a weekly rate-limit before writing; all reads were run in-session.

## 78.1 — `box` = "Building Object eXchange Protocol", NOT new in N5: it exists in N4 4.14 with the identical module description; the real delta is transport modernization `[CERT]`

The wave-8 dispatch premise ("box is N5's new protocol") is **refuted**. The N5 `box` module.xml declares
`description="Building Object eXchange Protocol"` `vendorVersion="5.0.0.28"` `schemaVersion="5"`
(`organized/box/.../module.xml`) `[CERT]`, and the **N4 4.14 corpus carries a `box` module with the
byte-identical description** `[CERT]` (`/home/cristian/niagara-research/organized/box/box-rt/.../module.xml`
`description="Building Object eXchange Protocol"`). So `box` is an N4 carryover, not a new N5 subsystem. Its
N4 form was split (`box-rt`); its N5 form is a single jar (no `-rt` suffix), consistent with [Block 1]'s
one-jar-per-module packaging `[CERT]`.

`box` is a **session/channel protocol over a dual transport** `[CERT]`. Its `module.xml` registers ~24
component types, most of them channels: `BAlarmChannel`, `BHistoryChannel`, `BOrdChannel`, `BSysChannel`,
`BTimeZoneChannel`, `BUnitChannel`, `BRegistryChannel`, `BComponentSpaceSessionHandler`, `BNavNodeSessionHandler`,
`BServerSession`/`BServerSessionChannel`/`BServerSessionHandler`, `BTransferChannel`, `BWrapperBoxChannel`
`[CERT]`. Two acceptors give the two transports:

- **WebSocket**: `BoxWebSocketServlet extends org.eclipse.jetty.ee11.websocket.server.JettyWebSocketServlet`
  (`organized/box/.../BoxWebSocketServlet.java:13`) — Jetty-12 **ee11 / jakarta** WebSocket API `[CERT]`,
  the N5 servlet-stack modernization ([Block 27] context). Its `createWebSocket` gates on the box service +
  acceptor being operational and the web service's HTTPS policy (`if (!httpsEnabled || !httpsOnly ||
  req.isSecure())`) `[CERT]` (`:34-42`).
- **Fox**: `BFoxBoxChannel`/`BFoxBoxAcceptor` import `com.tridium.fox.session.*` and run box over a
  `BFoxServerConnection`/`FoxHttpsSocket` (`organized/box/.../BFoxBoxChannel.java:2-6`) `[CERT]`.

**Framing mode**: `BoxWebSocketServlet.isBinary()` returns `!WebDev.get("bajaScript").isEnabled()`
(`:31`) — i.e. box speaks **binary WebSocket frames by default**, switching to text only when the
`bajaScript` web-dev flag is on `[CERT]`. Tunables are `box.ws.*` system properties: `idleTimeout`=60000 ms,
`maxTextMessageSize`=262144, `maxBinaryMessageSize`=131072, `maxFrameSize`=131072, in/out buffers 8192
(`:14-19`) `[CERT]`. The `BBajaScriptClientEnv` type (`module.xml`) confirms box is the station↔BajaScript
bridge (the N4 lineage: "box" historically = the BajaScript object-exchange channel) `[CERT]`.

**N4→N5 quantitative delta**: N4's `box-rt` had 15 files referencing WebSocket; N5's consolidated `box` has
6 `[CERT]` (`find ... -exec grep -l -i websocket`) — fewer, consistent with the ee11 API removing boilerplate
and the `-rt` merge, not a feature reduction (both retain `BoxWebSocketServlet`/`BBoxWebSocketAcceptor`/
`BFoxBoxAcceptor`/`QueryServlet`/`BBoxServlet`) `[INFER]`.

## 78.2 — B72-G3 CLOSED: box ships `WEB-INF/jetty-web.xml`, and its WebSocket route is a Jetty upgrade servlet gated on the box service — not a WAR bypass `[CERT]`

Box carries `WEB-INF/jetty-web.xml` (`organized/box/.../WEB-INF/jetty-web.xml`, also in `extracted/` and
`resources/`) `[CERT]`, which is exactly why [Block 72] found `box` among the three jetty-web.xml-bearing
modules (with `web` and `fox`). Under [Block 68]'s B27-G4 rule (`NModuleInfo.isWar` = jar contains
`WEB-INF/web.xml`), box's file is `jetty-web.xml` (a context-config override, per [Block 72]), so the
WEB-INF presence alone declares a context path, and the actual WebSocket entry is the Jetty **upgrade
servlet** `BoxWebSocketServlet`, whose creator refuses the upgrade unless `BBoxService` and its
`getWebSocketAcceptor()` are operational and the HTTPS policy is satisfied `[CERT]`
(`BoxWebSocketServlet.java:34-42`). There is no separate unauthenticated route: the upgrade rides the
normal web-service HTTPS gate. The exact `jetty-web.xml` contents (contextPath value) and the
WebSocket-upgrade-filter ordering vs. the auth filter are child gap **B78-G1**.

## 78.3 — B58-G1 + B58-G4 CLOSED: the `alarm.adb` store header is a fixed little-work `ByteBuffer` record — MAGIC `1611526157`, version 1, 512-byte pages, 8 pages/block, 1024-byte header `[CERT]`

The N5 `alarm` module writes its on-disk alarm database as `alarm.adb`
(`organized/alarm/.../db/file/BFileAlarmDatabase.java:125` `new File(this.dbDir, "alarm.adb")`), renaming a
corrupt store to `alarm_error[.N].adb` on recovery (`:188,191`) `[CERT]`. The header is defined by
`com.tridium.alarm.db.file.AlarmStoreHeader`, and its `write(DataOutput)` fixes the exact word order
(`AlarmStoreHeader.java:36-41`) `[CERT]`:

| Offset (bytes) | Field | Type | Value / default |
|---|---|---|---|
| 0 | MAGIC | int32 | **1611526157** (`0x60112E4D`) `[CERT]` (`:7`, `:36`) |
| 4 | version | int32 | 1 (`LATEST_VERSION`=1) `[CERT]` (`:8`,`:26`) |
| 8 | recordVersion | int32 | constructor arg (schema of the row bodies) `[CERT]` |
| 12 | creationTime | int64 | `System.currentTimeMillis()` `[CERT]` (`:25`) |
| 20 | pageSize | int32 | 512 (`DEFAULT_PAGE_SIZE`) `[CERT]` (`:10`,`:27`) |
| 24 | pagesPerBlock | int32 | 8 (`DEFAULT_PAGES_PER_BLOCK`) `[CERT]` (`:11`,`:28`) |

Total serialized header words = 28 bytes, padded to a `DEFAULT_HEADER_SIZE` of **1024** bytes (`:9`); the
buffer is a `niagara.nre.util.ByteBuffer` writing big-endian `writeInt`/`writeLong` `[CERT]`. This closes
[Block 58]'s B58-G1 ("no N5 alarm.jar decompile yet") and the sub-question B58-G4 ("decode the header words
0x0C-0x20"): words at 0x0C (creationTime) and 0x14/0x18 (pageSize/pagesPerBlock) are now named. Whether an
N4 `alarm.adb` uses the SAME magic/version (format compatibility across the upgrade) is child gap
**B78-G2** — it needs the N4 `AlarmStoreHeader` for a magic/version compare.

## 78.4 — B37-G4 NARROWED: `niagaraSync`'s license feature is `tridium:niagaraSync`; its fault surface is lexicon-driven cause strings, but the license-fault severity path is not the primary one `[CERT]`+`[INFER]`

`BNiagaraSyncService.getLicenseFeature()` returns
`Sys.getLicenseManager().getFeature("tridium", "niagaraSync")`
(`organized/niagaraSync/.../BNiagaraSyncService.java:286-287`) `[CERT]` — confirming [Block 71]'s B56-G2
finding that `tridium:niagaraSync` is the gating feature (independent of `premiumWBNiagaraRemote`). The
service's fault causes are lexicon strings for **operational** conditions —
`niagaraNetworkNotFound`, `peerStationNotFound`, `peerStationDisabled`, `peerStationServiceNotFound`,
`peerStationChannelNotFound`, `moduleMismatch`, `maintenanceMode` (`:122-127,276`) `[CERT]` — set via
`this.down(<cause>)` when `isFault()`. A distinct **license-absent** fault severity (fault vs. down vs.
disabled when `getLicenseFeature()` is unlicensed) is referenced but its exact branch/severity was not read
in this pass `[INFER]` — child gap **B78-G3** (trace where `getLicenseFeature()` is consumed and what state
it forces).

## 78.x — Connections

- Extends [Block 72] (which found box's jetty-web.xml) and corrects the wave-8 "box is N5-new" premise with
  the N4 4.14 module.xml evidence (§14-style correction of a dispatch assumption, not of a prior block).
- §78.1's ee11/jakarta WebSocket ties to [Block 27]'s N5 servlet-stack modernization.
- §78.4 corroborates [Block 71] §B56-G2 (`tridium:niagaraSync` feature).
- §78.3's `alarm.adb` header answers [Block 58]'s deferred B58-G1/B58-G4.

## 78.x — Child gaps opened

- **B78-G1** — box `jetty-web.xml` contextPath contents + WebSocket-upgrade-filter vs auth-filter ordering.
- **B78-G2** — N4 `AlarmStoreHeader` magic/version compare (alarm.adb format compatibility across upgrade).
- **B78-G3** — niagaraSync `getLicenseFeature()` consumer: unlicensed → fault/down/disabled severity branch.
- **B78-G4** — box wire-format message opcodes / frame body layout (only the transport envelope read here).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | box = "Building Object eXchange Protocol", present in N4 4.14 with identical description | [CERT] | N5 `box/module.xml`; N4 `box/box-rt/module.xml` |
| 2 | box runs over Jetty ee11 WebSocket AND Fox (dual transport) | [CERT] | `BoxWebSocketServlet.java:13`; `BFoxBoxChannel.java:2-6` |
| 3 | box frames are binary by default (`isBinary = !bajaScript dev`) | [CERT] | `BoxWebSocketServlet.java:31` |
| 4 | box WebSocket tunables via `box.ws.*` sys props (idle 60000, maxFrame 131072, …) | [CERT] | `BoxWebSocketServlet.java:14-19` |
| 5 | N4 box-rt = 15 WebSocket files; N5 box = 6 | [CERT] | `find -exec grep -l -i websocket` both corpora |
| 6 | box ships WEB-INF/jetty-web.xml; upgrade gated on box service + HTTPS policy | [CERT] | `box/.../WEB-INF/jetty-web.xml`; `BoxWebSocketServlet.java:34-42` |
| 7 | alarm store file is `alarm.adb`, corrupt→`alarm_error.adb` | [CERT] | `BFileAlarmDatabase.java:125,188,191` |
| 8 | alarm.adb header: MAGIC 1611526157, version 1, pageSize 512, pagesPerBlock 8, header 1024 | [CERT] | `AlarmStoreHeader.java:7-11,26-28,36-41` |
| 9 | niagaraSync license feature = `tridium:niagaraSync` | [CERT] | `BNiagaraSyncService.java:286-287` |
| 10 | niagaraSync unlicensed-fault severity branch not traced this pass | [INFER] | `BNiagaraSyncService.java` fault-cause list `:122-127` (license branch unread) |

Tally: 9 [CERT], 1 [INFER] (ratio 0.10). Load-bearing tokens confirmed present this session via direct
`grep`/`sed` output: the two `box/module.xml` descriptions; `JettyWebSocketServlet` import + `isBinary`;
`box.ws.*` property names; the `WEB-INF/jetty-web.xml` paths; `alarm.adb`/`alarm_error.adb` literals; the
`AlarmStoreHeader` MAGIC `1611526157` and field defaults; `getFeature("tridium", "niagaraSync")`. The N4
comparison rests on a whole-corpus `find -exec grep` over both trees that ran to completion.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block78.md`; INDEX/RESEARCH-STATE/CATALOG regeneration is the integrator step.
