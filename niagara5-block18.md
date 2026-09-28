# Block 18 — N5 cloud surface: cloudLink family, niagaraCloud and niagaraSync

> **§14 refinement (2026-09-27, [Block 37]):** failover promotion requires BOTH heartbeat channels (Fox RPC and the mTLS raw socket on port 5911) to be lost — an AND-gate, not a secondary-only check; every Fox reconnect re-runs a full initSync (no incremental catch-up); planned handoffs re-correct tick offsets but heartbeat-loss failover uses the last periodic correction.


> Research of the **N5 cloud-connectivity surface**: 10 modules —
> `cloudLink`, `cloudLinkAzure`, `cloudLinkExtensionBacnet`, `cloudLinkExtensionEbi`,
> `cloudLinkExtensionNiagara`, `cloudLinkForge`, `cloudLinkHonSbp`, `cloudLinkNcs`, `niagaraCloud`,
> `niagaraSync` — plus the `niagara.niagaraSync` marker-interface package inside `baja.jar` (the
> `BINiagaraSyncCapableComplex` sighting from [Block 5] §5.3/B5-G3) and the standalone `NCS-Agent`
> native binary shipped alongside the JVM install. Covers: architecture (components/services per
> module), protocols (AMQP 1.0, HTTPS/REST, Fox), identity/registration/provisioning flow (structure
> only, no secrets), the data model exported to the cloud, what `niagaraSync` actually syncs and its
> conflict-resolution model, the `NCS-Agent` process, licensing gates, and the N4 baseline for
> comparison. Does NOT cover: live registration against a real NCS/Forge/Azure/HonSbp tenant
> (B18-G1), full method-body tracing of every AMQP link handler in `transport/internal/` (B18-G2), or
> exhaustive per-provider (`cloudLinkForge`/`cloudLinkHonSbp`) channel-config classes beyond the
> pattern already established for `cloudLinkNcs` (B18-G3).
>
> Subject version: Niagara **5.0.0.28**, install `/mnt/c/Program Files/Niagara/5.0.0.28`, deployed
> modules cache `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules`. Per [Block 1] §1.4, the
> entire `cloudLink*` family (8 modules) carries `vendorVersion="5.0.0.26"` in `module.xml` and in its
> JPMS `module-info.class` — i.e. these 8 modules were NOT rebuilt for the 5.0.0.28 point release and
> are older code than `niagaraCloud`/`niagaraSync` (both `5.0.0.28`). N4 comparison baseline:
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules` (992 JARs) + the `niagara-research` N4
> corpus (`corpus-nav.py`), cited by block number below.
>
> Sources: `.../5.0.0.28/modules/{cloudLink,cloudLinkAzure,cloudLinkExtensionBacnet,cloudLinkExtensionEbi,
> cloudLinkExtensionNiagara,cloudLinkForge,cloudLinkHonSbp,cloudLinkNcs,niagaraCloud,niagaraSync}.jar`
> (censused with `unzip -l`; selected classes extracted+decompiled) ·
> `.../5.0.0.28/modules/baja.jar!niagara/niagaraSync/*.class` +
> `!com/tridium/util/niagaraSync/NiagaraSyncContextUtil.class` (5 classes, full decompile) ·
> `"/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe"` +
> `.sig` + `META-INF/{MANIFEST.MF,BOARDUPD.SF,BOARDUPD.RSA}` (PE header + `strings`, no decompiler —
> Go binary) · N4 corpus via `python3 /home/cristian/niagara-research/tools/corpus-nav.py find <term>`
> (blocks B39, B83, B84, B1076, B1082, B1083, B388, B1147 cited) · `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/`
> (directory listing only, to confirm absence of the 3 N5-only module JARs).
>
> Method: `unzip -l` census of all 10 module JARs (package/class inventory, dependency counts from
> `META-INF/module.xml`) · selective extraction of 34 classes from `cloudLink.jar` into
> `/tmp/claude-1000/n5b18/extract/cloudLink/`, decompiled with Vineflower 1.12.0
> (`java -jar vineflower-1.12.0.jar -e=baja.jar -e=cloudLink.jar extract/cloudLink out/cloudLink`,
> this session) into `/tmp/claude-1000/n5b18/out/cloudLink/` · full-jar Vineflower decompile of
> `niagaraSync.jar` (21 files), `niagaraCloud.jar` (10 files), `cloudLinkNcs.jar` (23 files),
> `cloudLinkAzure.jar` (12 files) into `/tmp/claude-1000/n5b18/out/{niagaraSync,niagaraCloud,
> cloudLinkNcs,cloudLinkAzure}/` · 5 classes extracted from `baja.jar`'s `niagara.niagaraSync` +
> `com.tridium.util.niagaraSync` packages, decompiled into `/tmp/claude-1000/n5b18/out/baja_ns/` ·
> `strings`/`file` on the `NCS-Agent` PE binary (no decompiler used — compiled Go, not JVM bytecode) ·
> `corpus-nav.py find` against the existing N4 `niagara-research` corpus for the N4 baseline.
> Markers (canonical list: METHODOLOGY §3): `[CERT-hw]`/`[CERT-live]` highest · `[CERT]` local primary
> source (`file:line`) · `[CERT-doc]` official document · `[CERT-web]` official web · `[CERT-a]`
> secondary source · `[INFER]` deduction. **Decompiled-tree citations in this block resolve to
> `extern`** per METHODOLOGY §11's decompiled-tree rule — see §18.9 self-verify.
>
> RT/security layer. Connects [Block 1] (module packaging — the `cloudLink*` stale-version finding),
> [Block 5] §5.3/B5-G3 (the `BINiagaraSyncCapableComplex` sighting this block resolves), [Block 15]
> (outbound-network-gate finding — `NiagaraCloudHttpTransport`/`com.tridium.nre.cloud.*` cited there is
> the SAME class this block's `niagaraCloud` discovery client calls into).

---

## 18.1 — Ten modules, two unrelated subsystems wearing the word "cloud" `[CERT]`

The `5.0.0.28` modules directory holds 10 cloud-surface JARs; census (`unzip -l`, this session):

| Module | `vendorVersion` | Top-level classes | `module.xml` deps | `module.xml description` |
|---|---|---|---|---|
| `cloudLink` | 5.0.0.26 | 447 | 24 | "Core Cloud Connectivity" |
| `cloudLinkAzure` | 5.0.0.26 | 11 | 26 | "Azure Cloud Connectivity" |
| `cloudLinkExtensionBacnet` | 5.0.0.26 | 6 | 26 | "CloudLink Station Utils for Bacnet Driver" |
| `cloudLinkExtensionEbi` | 5.0.0.26 | 4 | 26 | "CloudLink Station Utils for EBI Connector Driver" |
| `cloudLinkExtensionNiagara` | 5.0.0.26 | 8 | 26 | "CloudLink Station Utils for Niagara Driver" |
| `cloudLinkForge` | 5.0.0.26 | 154 | 28 | "Honeywell Forge Cloud Connectivity" |
| `cloudLinkHonSbp` | 5.0.0.26 | 33 | 29 | "CloudLink module for Honeywell Smart Buildings Platform" |
| `cloudLinkNcs` | 5.0.0.26 | 22 | 29 | "CloudLink module for **Niagara Cloud Suite**" |
| `niagaraCloud` | 5.0.0.28 | 9 | 29 | "Niagara Cloud module" |
| `niagaraSync` | 5.0.0.28 | 20 | 35 | "Niagara sync service" |

`[CERT]` (`unzip -p <jar> META-INF/module.xml`, this session, all 10; `unzip -l <jar> | grep '\.class$' | grep -v '\$'`
counted per jar). `cloudLinkNcs`'s own `module.xml description` literally spells out **NCS = Niagara
Cloud Suite** `[CERT]` (`cloudLinkNcs.jar!META-INF/module.xml`), settling the acronym without
inference. Total top-level classes across the 10 modules: **714** (994 including inner/lambda classes
and `module-info.class`, `unzip -l` count, this session).

**These are two structurally unrelated subsystems**, established by reading their code (§18.2-§18.7):

1. **`cloudLink` + its 7 satellites** — a device→cloud **telemetry/command connector framework**:
   one station streams its own point/history/alarm/schedule/model data OUT to a cloud tenant
   (Azure IoT Hub, Honeywell Forge, Honeywell Smart Buildings Platform, or Tridium's own Niagara
   Cloud Suite) and receives commands back.
2. **`niagaraSync`** — a **station-to-station high-availability replication** service (primary/
   secondary warm-standby over the Fox protocol). It has nothing to do with any cloud tenant; "sync"
   here means station↔station, not station↔cloud.
3. **`niagaraCloud`** — a **Workbench-side** (premium-licensed) sidebar that discovers an
   organization's registered devices from the Niagara Cloud REST API and opens direct Fox-over-WSS
   sessions to them — a remote-access client, not a data pipeline.

## 18.2 — `cloudLink` core: the extension-point chassis `[CERT]`

`cloudLink.jar` (`com.tridium.cloudLink.*`, 34 packages) is a **provider-agnostic connector chassis**
orchestrated by `BCloudConnectionService` (`com/tridium/cloudLink/BCloudConnectionService.class`,
top-level singleton service), which owns four child folders — `BClientAuthenticatorsFolder`,
`BTransportsFolder`, `BClientChannelsFolder`, plus per-provider config components — each holding
pluggable implementations `[CERT]` (package census, this session):

| Layer | Folder / abstract base | Concrete implementations found |
|---|---|---|
| Authentication | `auth/BAbstractClientAuthenticator` | `BPasswordAuthenticator`, `BTokenAuthenticator`, `BFederatedIdentityAuthenticator`, `BNullClientAuthenticator` |
| Transport | `transport/BAbstractTransport` → `BAbstractConnectedTransport` / `BAbstractConnectionlessTransport` | `BHttpTransport`, `BAmqpTransport`, `BNiagaraRemoteTransport`, `BNullTransport` |
| Channel | `channel/BAbstractClientChannel` | `BAlarmChannel`, `BBackupChannel`, `BCommandChannel`, `BEventChannel`, `BHeartbeatChannel`, `BHistoryChannel`, `BModelChannel`, `BPointChannel`, `BScheduleChannel`, `BMessageChannel` |
| Model export | `model/BModelExportPolicy` (abstract) | `BComponentExportPolicy`, `BCloudIdExportPolicy` |
| Object identity | `objectIdentity/BAbstractIdentityWorker` | `BComponentIdentityWorker`, orchestrated by `BCloudIdManager` |

`BCloudLinkProvisioning.configureCCS()` (`provisioning/BCloudLinkProvisioning.java:65-109`, this
session's decompile) is the mechanism that turns a cloud-delivered `CloudLinkConfiguration` payload
into live authenticator/transport/channel `BComponent`s under the running `BCloudConnectionService` —
i.e. the cloud can push NEW component configuration into the station at runtime (§18.4). This path has
an explicit type guard: `isLegalType()` rejects any type whose module name is `"program"`
(`BCloudLinkProvisioning.java:236-238`) — a deliberate block against the provisioning channel being
used to inject Niagara Program-object logic.

`BCloudConnectionService.getLicenseFeature()` gates on two Tridium license features depending on
context — `"cloudLink"` and `"cloudLinkConnect"` `[CERT]` (`BCloudConnectionService.java:212,217`, grep-confirmed).

## 18.3 — Transports: AMQP 1.0 (WebSocket) and HTTP, no protocol lock-in `[CERT]`

`BAmqpTransport` (`transport/BAmqpTransport.java:1-303`, this session's decompile) wraps a custom
`com.tridium.cloudLink.transport.internal.AmqpClient` built on **Apache Qpid Proton-J**
(`org.apache.qpid.proton.amqp.*` imports, `:24-26`) with **AMQP-over-WebSocket as the default
connection type** (`BAmqpConnectionType.amqpWs`, `:29,32`) and a SASL handshake
(`transport/internal/AmqpSaslListener.class`, package census). `BHttpTransport` is the sibling for
plain REST calls. Both transports are driven generically through `IMessage`/`MessageWrapper` and a
pluggable `IAmqpLinkResolver` (sender/receiver AMQP link-name pair) — `NcsAmqpLinkResolverFactory` /
`NcsRabbitMqLinkResolver` (`transport/NcsRabbitMqLinkResolver.java:1-21`) is the resolver `cloudLinkNcs`
registers, and its class name is the direct evidence that **NCS's AMQP broker is a RabbitMQ
deployment** `[CERT]` — no other resolver implementation was found for the other 3 providers in the
classes read this session (`[INFER]` that Forge/HonSbp/Azure use their own resolver implementations,
not read this session — B18-G3).

`AmqpClient` message decompression is content-type-driven (`BAmqpTransport.java:218-229`): incoming
AMQP messages carry a `MessageContentType` metadata key, and a `decompressorTypeMap` matches its
suffix to unpack the payload before delivery — the channel/message layer above is decompression-agnostic.

## 18.4 — Identity, registration and provisioning flow (structure only) `[CERT]`

`BFederatedIdentityAuthenticator` (`auth/BFederatedIdentityAuthenticator.java:1-490`, this session's
decompile) is the outbound identity flow used by NCS (and, per its `AUTH_PLATFORM_TYPE_FEDERATED`
default `authenticatorId`, designed as the shared federated-identity path):

1. **Device identity** comes from `com.tridium.nre.cloud.NiagaraCloudIdentity` (singleton,
   `SecurityUtil.doPrivileged(NiagaraCloudIdentity::getInstance)`, `:204`) — a per-device UUID
   (`getDeviceUuid()`) plus a `KeyManager` used to sign outbound requests. Registration state is a
   frozen enum, `BFedIdRegistrationState` (`registered`/`unregistered`, `:212-218`).
2. **Device provisioning** (`deviceProvisioning()`, `:362-400`): once registered, the authenticator
   sends a signed HTTP request (`FederatedIdentityDeviceProvisioningInfoRequest`, carrying the
   `IdAndKeyManager` and a cached `configurationIdentifier` used as an **ETag** for conditional
   retrieval — a `304` response means "unchanged", `:373-375`) to `registrationHost`. A `200` response
   (`FederatedIdentityDeviceProvisioningInfoResponse`) carries a `CloudLinkConfiguration` payload that
   is applied via `BCloudLinkProvisioning.configureCCS()` (§18.2) and a server-set retry interval
   (`response.getRetry()`, default 900s, `:391-398`) — this is a cloud-driven, poll-based remote
   configuration channel, not push.
3. **Broker token exchange** (`getBrokerToken()`, `:471-489`): a second signed HTTP request
   (`FederatedIdentityBrokerTokenRequest`) fetches a bearer token for the AMQP broker, cached until
   `getExpiration()` (`:296-306`).
4. **Default AMQP wiring for NCS** (`makeAmqpConfiguration()`, `:450-454`): provider id `"NcsRmq"`,
   D2C exchange `""` (default exchange), C2D queue path template `/queues/%s.station`, WebSocket path
   `/api/v1/amqp`, protocol `"amqp"`, auth type `BAmqpAuthenticationType.jwt` — confirming JWT-bearer
   auth over the AMQP-WebSocket transport for NCS specifically.
5. **JWKS validation route**: `NcsConstants.JWKS_ROUTE = "/api/v1/accesstoken"` +
   `JWKS_KEY = "/publicKey"` (`ncs/NcsConstants.java:8-9`) — the public-key/JWKS side of the same
   JWT scheme.

**Inbound direction is symmetric and JWT-based too.** `CloudLoginModule` (`security/CloudLoginModule.java:28-243`,
this session's decompile) is a JAAS `LoginModule` that authenticates INCOMING connections carrying a
cloud-issued JWT: it validates signature (RS256/ES256 via `org.jose4j`, `:121-129`), issuer/audience/
expiry, extracts `deviceid`/`stationrole`/`cloudroles`/`custom_attributes.cloudroles`/`principal`
claims, and maps them to an **ephemeral, cached `BUser`** (`LruLinkedHashMap<String,BComponent>` sized
100, `:35`) whose Niagara roles come from `BCloudRoleMappings.mapCloudRoles()` — except appId
`"NCS-FoxC"`, which is hardcoded to map straight to Niagara role `"FoxC"` (`:147-149`). This is the
authentication backing the Fox-over-WSS remote-access sessions `niagaraCloud`'s Workbench sidebar opens
(§18.6) — the cloud vouches for the identity, the station never sees a local password.

## 18.5 — Data model exported: full component tree, not just points `[CERT]`

The channel taxonomy (§18.2 table) plus the `msg/` package's ~35 handler interfaces (package census,
this session) show the exported data model spans **7 categories**, each with its own channel and
message-handler contract: **model** (device/point topology — `ISendModelHandler`/`Open`/`Close`/
`Entities`, gated by `BModelExportPolicy`/`BComponentExportPolicy`, §18.2), **points**
(`IPointReadCommandHandler`/`Write`, `IMultiPointReadCommandHandler`/`Write`, `ISendPointValuesHandler`),
**histories** (`ISendHistoriesHandler`/`Bulk`, `IGetHistoriesHandler` with a `GetHistoriesFilter`),
**alarms** (`ISendAlarmHandler`/`Batch`, `IAckAlarmCommandHandler`), **schedules**
(`ISendScheduleHandler`), **backup** (`BBackupChannel`, `StartBackupResult` — `cloudLinkNcs`'s
`NcsBackupUploader`/`BNcsFileUploadManager` implement this over HTTP, not AMQP — `ncs/file/*.java`),
and **health/heartbeat** (`ISendHealthStatusHandler`, `ISendHeartbeatHandler`, `BHeartbeatPolicy`).
Object identity is decoupled from Niagara slot paths: `BCloudIdManager` (`objectIdentity/BCloudIdManager.java:1-320`)
assigns a stable `cloudId` per device/history via a pluggable `ICloudIdProvider` (default
`UUID_PROVIDER`, `:61`) and persists the mapping in a `BVector` tree keyed by escaped device/history
name, saved with the station (`Station.saveSync()`, `:295`) — so a Niagara point rename does not orphan
its cloud telemetry id.

## 18.6 — `niagaraCloud`: Workbench sidebar, not a data pipeline `[CERT]`

`BNiagaraCloudSideBar` (`sidebar/BNiagaraCloudSideBar.java:59-546`, this session's decompile) is a
`BWbSideBar` gated by license feature `"tridium:premiumWBNiagaraRemote"` (`:159`, `checkFeature`) — if
absent, the sidebar shows only an upsell label (`:164-171`). When licensed and authenticated
(`NiagaraCloudAuthenticationClient`), it calls `NiagaraCloudDiscoveryClient.discover()`
(`discovery/NiagaraCloudDiscoveryClient.java:9-11`), which issues a **bearer-token-authenticated HTTPS
GET** through the SAME `com.tridium.nre.cloud.transport.NiagaraCloudHttpTransport` [Block 15] already
documented as outbound-network-ungated, against a HAL/JSON `_embedded`/`_links.self.href` REST API
(`NiagaraCloudDiscoveryUtil.java:9-70`, `?size=1000` pagination). The response builds a drill-down tree
of `NiagaraCloudEntity` (org → site → ... → `"Device"` leaf, `parseItem()`, `:31-43`); for each
discovered `Device`, the sidebar mounts a `com.tridium.cloud.BNiagaraRemoteHost` and opens a Fox
session **over WSS on port 443** (`BFoxSession.make(null, host, 443, FoxConnectionTypeEnum.FOXWSS, 443)`,
`BNiagaraCloudSideBar.java:325-327`) plus a `BDaemonSecureSession` — i.e. Workbench connects directly
to the remote station's Fox-over-WSS endpoint once the cloud API has told it which host to dial; the
cloud is a directory/broker for the connection, not an intermediary for the Fox traffic itself. The
`CloudLoginModule` inbound JWT auth (§18.4) is what authenticates that resulting session.

## 18.7 — `niagaraSync`: primary/secondary station replication over Fox, not cloud sync `[CERT]`

`BNiagaraSyncService` (`com/tridium/niagaraSync/BNiagaraSyncService.java:1-1049`, this session's full
decompile) is a `BAbstractService` with a frozen `role` property (`BNiagaraSyncRoleEnum`:
**primary**/**secondary**, `:14-47` of that file) and a frozen `state` property
(`BNiagaraSyncStateEnum`: **initializing**/**active**/**standby**/**disabled**/**fault**, `:12-59`).
License feature: `Sys.getLicenseManager().getFeature("tridium", "niagaraSync")`
(`BNiagaraSyncService.java:296`).

- **Transport**: a dedicated Fox channel named `"niagaraSync"` registered in
  `BFoxChannelRegistry` (`serviceStarted()`, `:217-222`), carrying request/response ops `heartbeat`,
  `status`, `takeControl`, `relinquishControl`, `clockSync`, `keyExchange`, `rotateKeys`,
  `maintenance`, `stateSubscribe`/`Unsubscribe`, `updateState` (`BNiagaraSyncChannel.process()`,
  `fox/BNiagaraSyncChannel.java:75-102`), plus two long-lived FoxCircuits (`initSync`, `startSync`) for
  bulk transfer.
- **What is synced**: the FULL running `BComponent` tree under every `BINiagaraSyncFolder` — not just
  values. `initSync()` (`BNiagaraSyncChannel.java:319-472`) walks the folder with a
  `ComponentTreeCursor`, serializes every component (`ValueDocEncoder`, transients included) plus every
  outgoing `BLink`/`BRelation` (knob) whose target sits OUTSIDE the sync folder (cross-tree links are
  re-pointed via `NiagaraSyncUtil.toSlotPathOrd`), and the receiving side reconstructs adds/sets/removes
  under `NiagaraSyncContextUtil.SYNC` context. After the initial snapshot, `startSync()`
  (`ComponentSyncRunnable.java:28-108`) streams a live event log with **20 distinct event ids**
  covering property set/add/remove/rename/reorder/flags/facets changes — i.e. this is a live
  component-tree replication protocol, not a periodic re-sync.
- **Direction**: strictly **active → standby**, one-way, never bidirectional merge. `activate()`
  starts the sync folders locally and tells any `BINiagaraSyncCapableDeviceNetwork` driver it is now
  active (`:480-508`); `standby()` stops local folders, opens `initSync`+`startSync` circuits AGAINST
  the peer, and applies everything it receives (`:510-549`). The peer's role/state is learned via the
  `status` RPC (`BNiagaraSyncStatus`, `:936-964`).
- **Conflict resolution is exclusion, not merge.** `handleStatus()` (`:632-704`) faults immediately if
  the peer reports the SAME role as local (`"niagaraSync.fault.peerStationDuplicateRole"`, `:636-638`)
  — there is no dual-primary/split-brain reconciliation path, only a hard fault. Module-version skew
  between the two stations is checked (`checkModules()`, `:706-757`) and normally faults the service
  (`FAULT_CAUSE_MODULE_MISMATCH`); a `maintenanceMode` flag relaxes this to allow deliberate,
  directional software upgrades (newer wins on the side maintenance was set for, `:716-731`) without
  full fault.
- **Two independent heartbeats and mTLS-rotated keys.** A 500ms Fox RPC heartbeat (`sendPrimaryHeartbeat()`,
  `:851-874`) detects Fox-level disconnection (auto-reconnect with 15s backoff, `:782-800`); a SEPARATE
  raw-socket `HeartbeatClient`/`BSecondaryHeartbeat` pair, authenticated by mutually exchanged X.509
  certs (`keyExchange` RPC, `:684-702`) rotated every **30 days** (`KEY_ROTATION_INTERVAL`, `:122`, via
  `rotateKeys()`), is the actual failover trigger: `heartbeatLost()` (`:551-555`) promotes a standby to
  active only off this second channel, decoupling "is Fox still connected" from "is the peer process
  actually alive". **Clock skew between the two stations is measured (`clockSync` RPC, NTP-style
  three-timestamp offset, `:812-820`) and applied to every synced `BNiagaraSyncTicks` value** so a
  scheduled deferred action (`BNiagaraSyncTicket`, `niagara/niagaraSync/BNiagaraSyncTicket.java:1-168`,
  the class [Block 5] §5.3 flagged as B5-G3) fires at the correct WALL time on the peer despite clock
  drift, not at the same tick count.
- **`BINiagaraSyncCapableComplex` resolved (closes B5-G3)**: it is a bare marker interface
  (`niagara/niagaraSync/BINiagaraSyncCapableComplex.java:10-13`, no methods) whose only consumer found
  this session is `BNiagaraSyncTicket.isParentLegal()` (`:106-116`), which requires the parent
  component's type to declare this interface. `BStatusBoolean`/`BStatusNumeric` implementing it (per
  [Block 5] §5.3) means those two status types are legal HOSTS for a `BNiagaraSyncTicket` child — a
  deferred, clock-corrected action scheduled to fire on the component once a timer expires — used
  inside the sync/HA machinery for things like a delayed fail-back action; no evidence found this
  session of any OTHER framework use of the interface (`[INFER]`, narrow search — B18-G4).
- **Station pairing lives in the `niagaraNetwork` (BACnet-style N-driver) namespace**, not in the
  service itself: `BNiagaraSyncStationPair` (`niagaraNetwork/BNiagaraSyncStationPair.java:34-192`) is
  restricted to exactly 2 `BNiagaraStation` children under a `BNiagaraNetwork` (`isChildLegal`,
  `checkParentForRestrictedComponent`, `:122-146`) and tracks which of the two currently reports
  `active` (`activeStation` property, updated by the `updateState` Fox op, `:173-180`) — this is the
  station-discovery/pairing UI surface, separate from `BNiagaraSyncService`'s runtime state machine.

## 18.8 — `NCS-Agent`: a standalone Go service, not a JVM component `[CERT]`

`"/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe"` is a
**PE32+ Windows console executable** (`file`, this session) — NOT a `.jar`, and not run inside the
Niagara JVM. `strings` (this session) identify it as a **Go 1.25.12** binary whose embedded build path
is `/__w/tridium-ncs-rsm-agent/tridium-ncs-rsm-agent/internal/platform/supervisor_windows.go` — the
source repository is literally named `tridium-ncs-rsm-agent` `[CERT]` (string present verbatim in the
binary). It registers itself as a **Windows Service** (imports `StartServiceW`/`DeleteService`/
`SetServiceStatus`/`QueryServiceStatus` from `advapi32`, plus a companion string "Running RSM agent").
Distinct capabilities visible in the string table (`[CERT]`, all strings quoted verbatim from the
binary this session):

- **Bootstrap + rolling mTLS identity**, independent of the station's own `NiagaraCloudIdentity`
  (§18.4): strings `"ncs-bootstrap.p12"`, `"Failed to get Bootstrap certificate"`,
  `"failed to renew rolling certificate"`, `"Could not load rolling client certificate. Registration
  succeeded but client may not be set correctly."`, `"Cloud registration timeout expired."` — PKCS#12
  keystore/truststore handling (`"read PKCS#12 truststore %s: %w"`, `"decode PKCS#12 identity %s: %w"`).
- **Device registration REST calls**: `"/api/v1/deviceregistration/initregistration"`,
  `"/api/v1/deviceregistration/uuid"` — a separate registration surface from `cloudLinkNcs`'s station-side
  federated-identity flow (§18.4); whether these two registration flows converge on the same backend
  identity was not traced this session (`[INFER]` — B18-G5).
- **Software distribution / OTA**: `"/software/part/{repositoryId}/{vendorId}/{partType}/{partName}/
  {partVersion}/download"`, `"building manifest"`, `"DONE: Agent successfully sent a manifest/sync and
  downloaded"`, `"DownloadParts() out"` — a manifest-driven part-download mechanism, consistent with an
  RSM ("Remote Software Manager"/"Remote Software Management", name not spelled out anywhere in the
  binary — the expansion of the acronym is `[INFER]`) agent that lets NCS push software/module updates
  to the JACE/platform independently of Workbench's own provisioning tooling.
- **Local IPC to the station**: strings `"niagaradshim"`, `"*niagaradshimgen.StartRequestStruct"`,
  `"HostID: *niagaradshim..."`, `"Unsupported Niagaradshim IPC request"`, plus an embedded **Apache
  Thrift** client/server (`"RSM Thrift Client"`, `"RSM Thrift Server"`, `"Failed to create mTLS thrift
  server"`) — the agent talks to the local `niagarad` (platform daemon) over a Thrift-based mTLS IPC
  shim rather than through the JVM's own module/service layer. `NIAGARA_USER_HOME`/`NIAGARA_CONFIG_HOME`
  environment variables are read, confirming it locates the local install the same way the JVM side does.
- **FIPS-140 crypto posture**: numerous `"... is not allowed in FIPS 140-only mode"` guard strings
  (RSA key size, AES mode, HKDF/HMAC key length, hash algorithm) — the Go crypto stack enforces FIPS
  boundaries when that mode is active, mirroring the JVM side's own FIPS material directory noted in
  the N4 corpus (`niagara.home/fips`, B39 §39 permissions table).
- The `.sig` file alongside the `.exe` is a **detached signature** (raw bytes, not a JAR-style
  `.RSA`/`.SF` pair) — the `META-INF/BOARDUPD.{RSA,SF}` in the SAME `NCS-Agent` directory is a
  SEPARATE, JAR-style code-signing artifact for the exe when it is delivered as a
  `niagara_user_home/npsdkUpdates/` update package (`MANIFEST.MF` lists exactly
  `tridium-ncs-supervisor-amd64-windows.{exe,sig}` under that path, cert subject "Open Board Update /
  For Development Purposes Only - Do Not Distribute / Tridium, Inc"), i.e. the agent binary is itself
  one of the OTA-updatable "parts" the agent's own download API can fetch — a self-updating agent.
  No decompiler was used (Go binary, not JVM bytecode); all of the above is `strings`+`file`-level
  structural evidence, not a traced call graph — deeper analysis is out of scope for this block
  (B18-G6).

## 18.9 — N4 baseline comparison `[CERT]`/`[INFER]`

| N5 module | N4 equivalent | Relationship |
|---|---|---|
| `cloudLink` + `cloudLinkAzure`/`Forge`/`HonSbp` + 3 `Extension*` | **Already exists in N4**, same `com.tridium.cloudLink.*` namespace, documented in `niagara-research` B1082/B1083/B1147/B388 | Carried forward unchanged into N5 — consistent with [Block 1]'s finding that these 8 modules stayed at `vendorVersion 5.0.0.26` (not rebuilt for N5) |
| `cloudLinkNcs` | **Not found** in the N4 modules directory or corpus (`corpus-nav.py find cloudLinkNcs` → no matches; `ls .../N4.14.0.162/modules | grep -i cloudLinkNcs` → empty) | N5-only provider extension; NCS itself may be a newer Tridium cloud offering than the N4-era Azure/Forge/HonSbp integrations |
| `niagaraCloud`, `niagaraSync` | **Not found** as module JARs in the N4.14.0.162 tree (`ls` empty for both names) | Genuinely new in this N5 line (or at least not yet shipped as of N4.14.0.162) — see next row for the closest N4 functional analogue |
| (functional gap `niagaraSync` fills) | N4 has **no automatic HA/failover module at all**: `niagara-research` B39 documents `BBackupService` (manual backup/restore) and `provisioningNiagara` (`BNiagaraNetworkJob`/`BForEachStationStage`, cold, admin-triggered bulk config push to N subordinates) as the ONLY N4 replication mechanisms — no primary/secondary heartbeat, no automatic promotion | `niagaraSync`'s active/standby Fox-heartbeat failover (§18.7) is a materially NEW capability class relative to N4, not a rename of an existing one |
| N4's own separate cloud driver, `nCloudDriver` | `nCloudDriver` (`BNiagaraCloudNetwork extends BNNetwork`, `com.tridium.nc.*`, license `tridium/nCloudDriver`) bridges to Honeywell Sentience/Forge via **Azure IoT Hub AMQP**, discovered via BQL `select * from cloudConnector:CloudConnector` — documented in B83/B84/B1076 | A THIRD, N4-only cloud stack, architecturally distinct from both `cloudLink` (extension-based) and N5's module set — no `nCloudDriver` JAR was checked for in the N5 5.0.0.28 tree this session (`[INFER]` that it was retired/folded into `cloudLinkAzure`+`cloudLinkForge` — not confirmed, B18-G7) |

> **Correction (added by [Block 115], §14 cross-block).** `cloudLinkNcs` is NOT N5-only: `cloudLinkNcs-rt.jar` ships in the
> N4-4.15.3.28 OEM install (`/mnt/c/PowerB/PowerB-4.15.3.28/modules/`); the "not found" check above used only the N4.14.0.162 baseline.
> See [Block 115] §115.4 (7 of B13's 18 "N5-only" modules already ship in 4.15).

The corpus-nav absence checks are `[CERT]` for "not present in the specific N4.14.0.162 install /
niagara-research corpus consulted" — they are not proof the modules never existed in ANY N4 release;
a narrower or newer N4 build was not checked (scope caveat, folded into B18-G7).

## 18.x — Self-verification (METHODOLOGY §11)

**Block type**: `standard`/evidence (default — omitted per template). **DECOMPILED-TREE BLOCK — ZERO
RESOLVED CITATIONS ARE EXPECTED** per METHODOLOGY §11's explicit rule: every `[CERT]` citation in this
block points into a Vineflower-decompiled `.java` file under `/tmp/claude-1000/n5b18/out/...`
(scratch, not archived in the corpus) or into a `strings`/`unzip -l` census of a binary artifact
(`.jar`/`.exe`) — none of these paths resolve under the corpus's own `verify-block.sh` target
directory, so a mechanical run would report `resolved 0 of N — no file paths resolved`. Declared
explicitly per the convention: **`verify-block: 0 resolved (all extern — decompiled trees + binary
census); citation gate = inline token-verify below`.**

**Marker tally — literal `toolbelt/verify-block.sh niagara5-block18.md /home/cristian/niagara5-research`
output, this session:**

```
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 1)
   [CERT-live] 2  (adj 1)
   [CERT] 25  (adj 24)
   [CERT-doc] 1  (adj 0)
   [CERT-web] 1  (adj 0)
   [CERT-a] 1  (adj 0)
   [INFER] 9  (adj 8)
-- ratio -- [INFER]/[CERT*] = 8/26 = 0.31
-- [CERT] file:line citation resolution --
   resolved 0 of 21
   WARN    resolved 0 of 21 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```

Adjusted ratio **0.31** — well under the ~0.5 exhaustion threshold, consistent with an evidence block
that opened fresh source rather than one running out of investigable material. Exit 0: no verifiable
contradiction (no cited line resolved as out-of-range, no cited block-evidence artifact missing).
The `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` counts are the LEGEND lines in this
block's own header blockquote (the canonical marker list, quoted for the reader), not fresh claims —
this block makes no `[CERT-hw]`, `[CERT-live]`, `[CERT-doc]`, `[CERT-web]`, or `[CERT-a]` claims itself
(adjusted count 0 for each of the latter three, 1 each for `-hw`/`-live` only because the header
blockquote's own legend line is counted once by the script's positional strip; this block's BODY
contains zero of those four marker types as actual claims).

**Inline token-verify** (this session, all classes independently re-opened after the initial decompile
pass to confirm the cited line numbers, since the mechanical tool cannot): `BCloudConnectionService.java`,
`BCloudLinkProvisioning.java`, `BAmqpTransport.java`, `NcsRabbitMqLinkResolver.java`,
`BFederatedIdentityAuthenticator.java`, `NcsConstants.java`, `CloudLoginModule.java`,
`BModelExportPolicy.java`, `BCloudIdManager.java`, `BNiagaraCloudSideBar.java`,
`NiagaraCloudDiscoveryClient.java`, `NiagaraCloudDiscoveryUtil.java`, `BNiagaraSyncService.java`,
`BNiagaraSyncChannel.java`, `ComponentSyncRunnable.java`, `BNiagaraSyncStationPair.java`,
`BNiagaraSyncTicket.java`, `BNiagaraSyncTicks.java`, `BINiagaraSyncCapableComplex.java`,
`BINiagaraSyncFolder.java`, `NiagaraSyncContextUtil.java`, `BNiagaraSyncRoleEnum.java`,
`BNiagaraSyncStateEnum.java` — **23 files, read in full with line numbers this session**, every cited
line range checked against the actual `Read` output above (not inferred from a class/method name).
License-feature string tokens (`"cloudLink"`, `"cloudLinkConnect"`, `"niagaraSync"`,
`"premiumWBNiagaraRemote"`) independently re-`grep -rn`-confirmed against the decompiled sources
(`getFeature(`/`checkFeature(` call sites, §18.2/§18.6/§18.7). `NCS-Agent` string citations
(§18.8) are direct `strings` output on the binary, quoted verbatim — not a decompiled-source citation,
so no `file:line` applies; each quoted string was independently re-`strings | grep -F`-confirmed present.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block18.md`. Per the
caller's explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator.

**MCP-doc snapshots**: N/A — no `context7`/web-MCP source was used this session; all `[CERT]` evidence
is local (JARs, an .exe) or from the existing local N4 corpus via `corpus-nav.py`.

## 18.x — Child gaps opened

- **B18-G1** — `[CERT-hw]`/`[CERT-live]` live registration: register a real (test-tenant) device
  against NCS/Forge/HonSbp/Azure and observe the actual provisioning payload, broker token, and AMQP
  traffic — everything in §18.4/§18.5 is derived from static code, never exercised against a live
  endpoint this session.
- **B18-G2** — Full method-body trace of `transport/internal/{AmqpClient,AmqpDeviceSessionHandler,
  AmqpAuthReceiverLinkHandler,AmqpAuthSenderLinkHandler,AmqpTelemetryReceiverLinkHandler,
  AmqpTelemetrySenderLinkHandler,ProxyHandler}` — only `AmqpConstants`/`AmqpSaslListener`/
  `AmqpDeviceSessionHandler` were extracted+decompiled this session; the link-handler classes were
  identified by name in the package census (§18.1 method) but not opened.
- **B18-G3** — Per-provider channel-config classes for `cloudLinkForge` (154 top-level classes) and
  `cloudLinkHonSbp` (33 top-level classes, though B1082 already covers much of this from the N4 side)
  beyond the pattern established for `cloudLinkNcs`'s `channel/BNcs*ChannelConfig` set (§18.5) — not
  individually opened this session; assumed structurally parallel but not verified class-by-class.
- **B18-G4** — Confirm whether any component type OTHER than `BStatusBoolean`/`BStatusNumeric` (found
  by [Block 5], not re-searched this session) implements `BINiagaraSyncCapableComplex`, and find every
  OTHER caller of `BNiagaraSyncTicket.make()` beyond the one class read this session — the scope this
  session was the `niagaraSync` module + the 5 `baja.jar` classes; a full-tree grep for
  `BINiagaraSyncCapableComplex` usage across ALL modules was not run.
- **B18-G5** — Trace whether `NCS-Agent`'s own device-registration REST calls
  (`/api/v1/deviceregistration/*`) converge on the same backend device identity as `cloudLinkNcs`'s
  station-side `NiagaraCloudIdentity`/federated-identity flow, or are a genuinely separate registration
  domain (e.g. platform-level vs. station-level identity) — inferred as plausibly related from naming
  alone, not traced.
- **B18-G6** — Deeper reverse-engineering of the `NCS-Agent` Go binary (disassembly/decompilation of
  actual logic, not just string-table census) — this session used only `file`+`strings`, no Go
  decompiler (e.g. no attempt to recover function bodies).
- **B18-G7** — Confirm whether N4's `nCloudDriver` (`com.tridium.nc.*`, B83/B84/B1076) has a direct N5
  successor module, was retired, or was folded into `cloudLinkAzure`+`cloudLinkForge` — the N5
  5.0.0.28 modules directory was not searched for an `nCloudDriver`-equivalent JAR this session (search
  was scoped to the 10 named cloud-surface modules in the task).

## 18.x — Connections

- **[Block 1] §1.4** — direct parent for the `cloudLink*` stale-`5.0.0.26`-version finding this block
  extends into a full architecture read; also the source of the 247-module census this block's 10
  modules are drawn from.
- **[Block 5] §5.3 / B5-G3** — this block closes B5-G3: `BINiagaraSyncCapableComplex` is a bare marker
  interface consumed by `BNiagaraSyncTicket.isParentLegal()` (§18.7), gating which component types may
  host a clock-corrected deferred-action ticket inside the `niagaraSync` HA machinery.
- **[Block 15] §15.2** — `com.tridium.nre.cloud.transport.NiagaraCloudHttpTransport`, documented there
  as having no permission check at the transport layer, is the EXACT class `niagaraCloud`'s discovery
  client (§18.6) and `cloudLinkForge`-family provisioning calls route through — this block identifies
  a concrete, licensed, in-product CALLER of that ungated transport.
- **REMITTANCE → `niagara-research` B39** (provisioning/backup/HA baseline), **B1082/B1083**
  (`cloudLinkHonSbp` RT architecture, already documented from the N4 side — cite only, not
  re-derived), **B388/B1147** (`cloudLink*` presence + signature-gate handling in N4), **B83/B84/B1076**
  (`nCloudDriver` Azure IoT Hub stack) — the N4 baseline for §18.9, retrieved via `corpus-nav.py find`
  this session and read at the cited block/line locations before being characterized above.
