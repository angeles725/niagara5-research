# Block 67 — cloudLink retry/throttle mechanics, the Forge message-handler census, vestigial `finalize()` overrides, and the three driver-extension satellites

> Research closing five named child gaps opened by [Block 42]/[Block 44] against the `cloudLink`
> family: **B42-G3** (the actual classification body of `BAbstractTransport.retriableError()` —
> [Block 42] §42.3 only read the `checkRetry()` call site, not the method it calls); **B42-G6**
> (the numeric defaults behind message-rate throttling and pending-message backpressure —
> `getMessageThrottlingLimit()`/`getPendingMessageLimit()` were read only at their `sendMessages()`
> call sites in [Block 42] §42.3, never at their declaration); **B42-G5** (`BForgeAmqpHandlerFactory`'s
> full command-handler surface — [Block 42] §42.7 censused the factory file's imports only, without
> opening any of the ~50 individual `Forge*Handler` classes under `forge/msg/`/`forge/file/`);
> **B44-G1** (the 13 `cloudLink*` family `Object.finalize()` for-removal overrides [Block 44] §44.3
> found by `jdeprscan` alone — what resource each releases, whether a shared base class or a
> `java.lang.ref.Cleaner` replacement exists); and **B42-G2** (the three `cloudLinkExtensionBacnet`/
> `Ebi`/`Niagara` "Extension" satellite modules [Block 18]/[Block 42] both named but neither opened —
> what each actually adds). Covers: reading `BAbstractTransport.java`'s full property-declaration
> block and `retriableError()`/`checkRetry()` bodies; `CloudLinkConstants.java`'s full numeric-constant
> set; both Forge handler-factory classes (`BForgeAmqpHandlerFactory`/`BForgeHttpHandlerFactory`) plus
> `ForgeFileUploader` and `BForgeScheduleChannelConfig` (the two dispatch paths a Forge handler can be
> wired through); all 13 `finalize()`-declaring classes named in [Block 44] §44.3, confirmed against a
> corpus-wide `grep` for every other `finalize()`/`Cleaner` occurrence in the `cloudLink*` family; and
> all `.java` files in the three `cloudLinkExtension{Bacnet,Ebi,Niagara}` modules (18 files total) plus
> their shared `cloudLink.jar` SPI base classes (`extension/B{DeviceInfo,HistoryImport,ProxyPoint,
> ProxyPointTags,Schedule,Model}Helper.java`). Does **not** cover: live message-rate exhaustion under
> load (no broker exercised — B42-G1 remains open); the full body of every one of the ~50 Forge
> handler classes (only the registration/wiring surface + a targeted sample were read — see child
> gap); a byte-level diff of what each `finalize()` override's ORIGINAL (pre-empty) implementation may
> have looked like (git/changelog history is not in this corpus — the empty-body finding is read as-is
> from the current 5.0.0.28 bytecode-derived source); or the `cloudLinkExtensionBacnet`/`Ebi`/`Niagara`
> modules' RUNTIME registration order relative to their driver modules (structural read only).
>
> Subject version: **N5 5.0.0.28 (Beta)**, install `/mnt/c/Program Files/Niagara/5.0.0.28`, deployed
> modules cache `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` — the identical install
> [Block 18]/[Block 42]/[Block 44] read. Decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{cloudLink,cloudLinkForge,cloudLinkAzure,cloudLinkNcs,
> cloudLinkExtensionBacnet,cloudLinkExtensionEbi,cloudLinkExtensionNiagara}/vineflower/` — all files
> cited below were already present in `organized/` from [Block 18]'s/[Block 42]'s decompile passes
> (`cloudLinkExtension*` was decompiled by an earlier session but never read — this session is its
> first read) or freshly `unzip -p`'d this session (the three extension `module.xml` censuses).
>
> Sources: `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java`
> (whole-file structural read this session: `:47-98` property block + generated defaults, `:460-604`
> `sendMessages()`/`checkRetry()`/`retriableError()`), `organized/cloudLink/vineflower/com/tridium/
> cloudLink/transport/BHttpTransport.java:416-425` (`retriableError()` override), `organized/cloudLink/
> vineflower/com/tridium/cloudLink/CloudLinkConstants.java` (whole file, 270 lines) ·
> `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/BForgeAmqpHandlerFactory.java`
> (whole file, 135 lines), `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/
> BForgeHttpHandlerFactory.java` (whole file, 84 lines), `organized/cloudLinkForge/vineflower/com/
> tridium/cloudLink/forge/file/ForgeFileUploader.java:19-20`, `organized/cloudLinkForge/vineflower/com/
> tridium/cloudLink/forge/channel/BForgeScheduleChannelConfig.java:1-14` · the 13 `finalize()`-declaring
> files named in [Block 44] §44.3 (each re-opened this session at its exact cited line, full list in
> §67.4) plus `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/
> ForgeAmqpAlarmHandler.java:23` (one `extends ForgeAmqpHandler` sample) · a corpus-wide `grep -rn
> "void finalize()"`/`grep -rn "Cleaner"`/`grep -rn "super.finalize"` over
> `organized/cloudLink*/vineflower/` (this session, confirms the 13-site count and the absence of both
> `super.finalize()` calls and any `java.lang.ref.Cleaner` usage anywhere in the family) ·
> `organized/cloudLinkExtension{Bacnet,Ebi,Niagara}/vineflower/com/tridium/cloudLink/extension/
> {bacnet,ebi,niagara}/*.java` (all 18 class files, structural reads — class declaration + `extends`/
> `implements` line for every file, full-body reads for `BNiagaraRemoteStation.java:35`,
> `BNiagaraNetworkHelper.java:28`, `BNiagaraProxyPointTagsHelper.java:20`, `BNiagaraDeviceInfoHelper.
> java:39`) · `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/{BDeviceInfoHelper.
> java:19-76,BHistoryImportHelper.java:17-54,BProxyPointHelper.java:17-54,BProxyPointTagsHelper.
> java:18-57,BScheduleHelper.java:16-27,BModelHelper.java:17-30}` (the shared extension-SPI base
> classes, whole/targeted reads) · live `unzip -p <jar> META-INF/module.xml` census of
> `cloudLinkExtension{Bacnet,Ebi,Niagara}.jar` from `/mnt/c/ProgramData/Niagara/tridium/config/
> 5.0.0.28/modules/` (this session, fresh — not reused from [Block 18]'s census of the same 3 jars).
>
> Method: full and targeted `Read` of every cited `.java` file (all pre-existing Vineflower decompiles
> from [Block 18]'s/[Block 42]'s sessions except the `cloudLinkExtension*` tree, decompiled earlier but
> read for the first time this session — no fresh decompilation performed) · `grep -n`/`grep -rn`
> structural + corpus-wide searches to confirm class-declaration lines, override counts, and the
> absence of `super.finalize()`/`Cleaner` · live `unzip -p META-INF/module.xml` census of 3 module JARs
> against the mounted install. Markers (canonical list: METHODOLOGY §3): `[CERT-hw]`/`[CERT-live]`
> highest · `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official document · `[CERT-web]`
> official web · `[CERT-a]` secondary source · `[INFER]` deduction. **Decompiled-tree citations in this
> block are given in FULL `organized/...` path form (not bare `file:line`) so they resolve against
> `verify-block.sh`'s target directory** — following [Block 61]'s convention rather than [Block 18]'s/
> [Block 42]'s bare-form convention (see §67.x self-verify for the resolution count this produces).
>
> RT/transport layer. Deepens [Block 42] (closes B42-G3, B42-G6, B42-G5, B42-G2) and [Block 44] (closes
> B44-G1). Connects [Block 18] (the `cloudLinkExtension*` module census and the extension-point-chassis
> framing §18.2 first named, now opened) and [Block 25] (the JDK-deprecation-scan lineage B44-G1
> descends from).
>
> **Type:** `standard`/evidence — five independent gap-closing reads, each grounded in this session's
> own fresh source opens; no cross-block `[INFER]` correction (unlike [Block 61]'s `mixed` framing).

---

## 67.1 — B42-G3 CLOSED: `retriableError()`'s base-class body is an unconditional `return true` — every cloudLink transport treats every error as retriable except `BHttpTransport`, which excludes HTTP 304/404 `[CERT]`

[Block 42] §42.3 read `checkRetry()`'s call site (`messageWrapper.canRetry() && this.retriableError(err)`,
`BAbstractTransport.java:579`) but not the method's own body, naming this **B42-G3**. The full method,
read this session:

```java
protected boolean retriableError(Throwable err) {
   return true;
}
```
`[CERT]` `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java:601-603`
(whole method, this session). **The base-class classification is not a classification at all — every
`Throwable`, of every type, is retriable by default.** A corpus-wide `grep -rn "retriableError"` over
every `cloudLink*/vineflower/` tree (this session) returns exactly **two** files: this declaration and
one override.

**`BHttpTransport` is the sole override in the entire family:**

```java
protected boolean retriableError(Throwable err) {
   if (err instanceof HttpStatusException httpErr) {
      return switch (httpErr.getStatusCode()) {
         case 304, 404 -> false;
         default -> true;
      };
   } else {
      return true;
   }
}
```
`[CERT]` `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BHttpTransport.java:416-425`
(whole method, this session) — HTTP `304 Not Modified` and `404 Not Found` are the only two conditions
this codebase treats as terminal/non-retriable; every other `HttpStatusException` status code (400,
401, 403, 429, 500, 503, ...) and every non-`HttpStatusException` `Throwable` (a network I/O exception,
a serialization failure, a TLS handshake error) is retriable by the base default, UNCHANGED by this
override's `else` branch.

**`BAmqpTransport` (and every other `BAbstractTransport` subclass) never overrides `retriableError()`
at all** `[CERT]` (same corpus-wide grep — confirmed by its absence from the 2-file result), so for
AMQP transport (all four cloud providers — Azure, Forge, HonSbp, NCS — share this one `BAmqpTransport`
class per [Block 18] §18.3) **every send failure is retriable**, up to `messageRetries`'s configured
cap (default 2, max facet 10 — §67.2), including a permanent AMQP protocol-level rejection (a malformed
message, an authorization failure mid-session, a broker-side validation error) that will fail
identically on every retry. Net reading, closing B42-G3: cloudLink's retry classification is
**binary-and-coarse — "is this HTTP and is it 304/404" is the only real filter in the whole family** —
not a fine-grained per-error-type policy; the message-level retry mechanism's actual selectivity comes
almost entirely from `MessageWrapper.canRetry()` (the retry-COUNT gate, not read this session — out of
scope, not a named gap) rather than from `retriableError()`'s error-TYPE gate.

## 67.2 — B42-G6 CLOSED: `pendingMessageLimit` defaults to 50, `messageThrottlingLimit` defaults to **0 (disabled)**, `messageRetries` defaults to 2 (max 10), and the throttle window is a hardcoded 1-second sliding window `[CERT]`

All five `BAbstractTransport` properties, read at their `@NiagaraProperty`/`@Generated` declarations
this session (not merely their `sendMessages()` call sites, which is as far as [Block 42] §42.3 went):

| Property | Default | Min facet | Max facet | `[CERT]` |
|---|---:|---:|---:|---|
| `pendingMessageLimit` | **50** (`DEFAULT_PENDING_MESSAGES`) | 1 | — | `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java:50-56,84` |
| `messageRetries` | **2** (`DEFAULT_MESSAGE_RETRIES`) | 0 | **10** (`MAX_MESSAGE_RETRIES`) | `:57-61,85-86` |
| `compression` | `BCompressionMode.none` | — | — | `:63,87-88` |
| `messageThrottlingLimit` | **0** | 0 | `Integer.MAX_VALUE` | `:64-69,89-90` |
| `defaultMessageTimeout` | **60000 ms** (`DEFAULT_MESSAGE_TIMEOUT`) | 1000 ms | 300000 ms (5 min) | `:70-78,91-94` |

The four named `DEFAULT_*`/`MAX_*` constants resolve to `[CERT]` `organized/cloudLink/vineflower/com/
tridium/cloudLink/CloudLinkConstants.java:70-75` (whole-file read this session, fresh grep, not
inherited from a prior block's citation per METHODOLOGY §3's "numeric constants are `[CERT]` only with
a fresh `file:line` grep in the same session" rule) — `DEFAULT_MESSAGE_TIMEOUT = 60000`,
`MIN_MESSAGE_TIMEOUT = 1000`, `MAX_MESSAGE_TIMEOUT = 300000`, `DEFAULT_MESSAGE_RETRIES = 2`,
`MAX_MESSAGE_RETRIES = 10`, `DEFAULT_PENDING_MESSAGES = 50`. Two adjacent constants in the same file,
not wired to any `BAbstractTransport` property but load-bearing for message-SIZE (not rate) throttling
per [Block 42] §42.3's 256 KiB AMQP buffer and §42.5's per-channel queue-byte budgets: `[CERT]`
`CloudLinkConstants.java:68-69` — `DEFAULT_MIN_MESSAGE_SIZE = 10000`, `DEFAULT_MAX_MESSAGE_SIZE =
10000000` (10 MB).

**`messageThrottlingLimit`'s default of `0` means the message-rate throttle is DISABLED out of the box**
— the throttle gate at `sendMessages()` is itself conditioned on `this.getMessageThrottlingLimit() > 0`
(`organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java:478`, re-read
this session as part of the full `:460-560` dispatch-loop body [Block 42] §42.3 already excerpted) — a
freshly-provisioned cloudLink transport ships with NO message-rate cap at all; an operator (or the
cloud-driven `CloudLinkProvisioning.configureCCS()` payload, [Block 18] §18.2) must explicitly set a
positive value to activate it. When active, the window is a **hardcoded 1000ms sliding window**
(`this.messageWindowEnd = now + 1000L`, `:481`, and the re-arm on a full window, `this.messageWindowEnd
+= 1000L`, `:495` — both literal `1000L` constants, not a configurable property) — i.e. "N messages per
second" where N is the operator-set `messageThrottlingLimit`, with the dispatch thread `Thread.sleep()`ing
for the remainder of the current window when the limit is hit (`:491-496`) rather than dropping or
queuing differently.

**Pending-message backpressure re-arm threshold, read at its exact call site this session**: the
outer `while (this.pendingMessages < this.getPendingMessageLimit())` loop condition
(`:477`) is the admission gate (default cap 50, per above); the re-arm after a full stop is at
**half** of that limit (`this.pendingMessages <= this.getPendingMessageLimit() / 2`, `:540` — already
cited by [Block 42] §42.3 for its EXISTENCE, now confirmed against the 50-default it operates on: 25
in-flight messages by default before the dispatch loop restarts itself after going idle).

**Reconciling with [Block 42] §42.5's per-channel queue-byte budget**: `pendingMessageLimit` (default
50) counts IN-FLIGHT messages already pulled off a queue and awaiting transport completion; it is a
completely separate counter from `BAbstractMessageQueue`'s byte-based `queueSize` (default ~5,000,000
bytes/channel, [Block 42] §42.5, not re-derived here) — a station can have up to 50 messages actively
in-flight across ALL channels combined (this is a per-`BAbstractTransport` instance limit, one instance
per connection) while each individual channel separately backs up to ~5 MB of UNSENT messages before
`isFull()` trips. These are two independent throttles at two different layers (transport-level in-flight
count vs. queue-level byte budget), confirming [Block 42] §42.3's "three independent throttles" framing
with the first throttle's (Proton credit flow) sibling now numerically characterized alongside it.

## 67.3 — B42-G5 CLOSED: cloudLinkForge wires its ~30 message handlers through TWO factory dispatch tables (AMQP: 15, HTTP: 6) plus a THIRD, factory-bypassing direct-wire path for file uploads and schedules `[CERT]`

[Block 42] §42.7 censused `BForgeAmqpHandlerFactory`'s IMPORT list only. This session opens the factory
class bodies (both AMQP and HTTP variants) plus the two classes that wire handlers OUTSIDE either
factory's dispatch table.

**`BForgeAmqpHandlerFactory.registerHandlers()` — 15 interface→implementation pairs, one per AMQP
message type** `[CERT]` `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/
BForgeAmqpHandlerFactory.java:121-135` (whole method, whole file read, 135 lines):

| cloudLink interface | Forge AMQP implementation |
|---|---|
| `IForgeAckAlarmCommandHandler` | `ForgeAmqpAckAlarmCommandHandler` |
| `IForgeCommandResponseHandler` | `ForgeAmqpCommandResponseHandler` |
| `IForgeMultiPointReadCommandHandler` | `ForgeAmqpMultiPointReadCommandHandler` |
| `IForgeMultiPointWriteCommandHandler` | `ForgeAmqpMultiPointWriteCommandHandler` |
| `IForgePointReadCommandHandler` | `ForgeAmqpPointReadCommandHandler` |
| `IForgePointWriteCommandHandler` | `ForgeAmqpPointWriteCommandHandler` |
| `IGetLastTimestampsHandler` | `ForgeAmqpGetLastTimestampsHandler` |
| `IRegisterCommandsHandler` | `ForgeAmqpRegisterCommandsHandler` |
| `ISendAlarmHandler` | `ForgeAmqpSendAlarmHandler` |
| `ISendBatchAlarmHandler` | `ForgeAmqpSendBatchAlarmHandler` |
| `ISendEventHandler` | `ForgeAmqpSendEventHandler` |
| `ISendHistoriesHandler` | `ForgeAmqpSendHistoriesHandler` |
| `ISendHeartbeatHandler` | `ForgeAmqpSendHeartbeatHandler` |
| `ISendPointValuesHandler` | `ForgeAmqpSendPointValuesHandler` |
| `ISendSystemInfoHandler` | `ForgeAmqpSendSystemInfoHandler` |

The factory's `getMessageKeyHandler()` (`:66-71`) dispatches an incoming AMQP message to one of these
15 by concatenating its `ObjectType`+`.`+`ObjectVersion` metadata fields into a lookup key — confirming
[Block 42] §42.2's generic `IMessage`/channel architecture is keyed on exactly this pair for Forge.
`getMessageLogger()` (`:91-119`) additionally REDACTS an `Auth` field nested inside a `SystemCommand`
message's `CloudPlatformHeaders` before logging at `FINEST` (truncating a >40-char secret to its first/
last 10 chars, a >5-char one to first/last char, else literal `"REDACTED"`) — a defensive log-scrubbing
detail not previously documented for this family.

**`BForgeHttpHandlerFactory.registerHandlers()` — 6 pairs, TWO of which are `cloudLinkAzure` classes
reused verbatim, not Forge's own** `[CERT]` `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/
forge/BForgeHttpHandlerFactory.java:76-83` (whole method, whole file read, 84 lines):

| cloudLink interface | HTTP implementation | Module origin |
|---|---|---|
| `IStartFileUploadHandler` (keyed by concrete class, `:77`) | `AzureGetSasUrlHandler` | **`cloudLinkAzure`** — reused |
| `IEndFileUploadHandler` (keyed by concrete class, `:78`) | `AzureUpdateFileUploadStatusHandler` | **`cloudLinkAzure`** — reused |
| `IGetHistoriesHandler` | `ForgeHttpGetHistoriesHandler` | `cloudLinkForge` (own) |
| `ISendBulkHistoriesHandler` | `ForgeFileSendHistoriesBulkHandler` | `cloudLinkForge` (own) |
| `ISendModelCloseHandler` | `ForgeFileSendModelCloseHandler` | `cloudLinkForge` (own) |
| `ISendModelEntitiesHandler` | `ForgeFileSendModelEntitiesHandler` | `cloudLinkForge` (own) |

**Forge's HTTP file-upload flow is architecturally Azure Blob Storage under the hood** — `Forge`'s own
`registerHandlers()` literally imports and registers `com.tridium.cloudLink.azure.msg.
{AzureGetSasUrlHandler,AzureUpdateFileUploadStatusHandler}` (confirmed by the file's own `import`
block, this session) for its generic `IStartFileUploadHandler`/`IEndFileUploadHandler` slots — a SAS
(Shared-Access-Signature) URL request/response pair, the standard Azure Blob upload pattern — meaning
Honeywell Forge's cloud backend stores uploaded files (model/history bulk data) in Azure Blob Storage,
reached through the same Azure SAS primitive `cloudLinkAzure` itself uses, not a Forge-proprietary
upload protocol.

**A THIRD, separate file-upload path exists that neither factory's `registerHandlers()` wires: a
direct, hardcoded pairing inside `ForgeFileUploader`** `[CERT]` `organized/cloudLinkForge/vineflower/
com/tridium/cloudLink/forge/file/ForgeFileUploader.java:19-20`:

```java
this.startUploadClass = ForgeHttpStartFileUploadHandler.class;
this.endUploadClass = ForgeHttpEndFileUploadHandler.class;
```
— `ForgeHttpStartFileUploadHandler`/`ForgeHttpEndFileUploadHandler` are two more `forge/msg/` classes
[Block 42] §42.7's import census listed but this session confirms are used ONLY here (a corpus grep
finds no reference outside their own declaration file and this constructor) — a second, Forge-native
upload handshake that bypasses `BForgeHttpHandlerFactory`'s generic interface-keyed dispatch entirely,
wired by class literal instead. `BForgeScheduleChannelConfig` (the schedule-channel config class
[Block 42] §42.6 found `cloudLinkForge` does NOT register in its OWN `BForgeChannelConfigFactory` —
only `cloudLinkHonSbp`/`cloudLinkNcs` register it, reused from Forge) is the class that actually
INVOKES `ForgeFileUploader` for outbound schedule export `[CERT]` `organized/cloudLinkForge/vineflower/
com/tridium/cloudLink/forge/channel/BForgeScheduleChannelConfig.java:1-14` (imports
`com.tridium.cloudLink.forge.file.ForgeFileUploader`, this session) — so `ForgeFileSendScheduleHandler`
(the one remaining `forge/msg/` class with no consumer in either factory's `registerHandlers()`, per a
corpus grep this session) is the payload SERIALIZER `ForgeFileUploader`'s upload body carries, not a
dispatch-table entry itself.

**Net census, closing B42-G5**: `cloudLinkForge`'s `forge/msg/`+`forge/file/` handler surface is not
one flat list but **three parallel wiring mechanisms** — (1) `BForgeAmqpHandlerFactory`'s 15-entry AMQP
table (point/command/alarm/event/history/heartbeat/system-info messages, all live on the `BAmqpTransport`
connection), (2) `BForgeHttpHandlerFactory`'s 6-entry HTTP table (2 of which are borrowed `cloudLinkAzure`
classes for Blob-backed file upload), and (3) `ForgeFileUploader`'s own hardcoded class-literal pair for
the schedule-export upload path specifically — a structural distinction [Block 42] §42.6's channel-config
table did not surface (it counted CHANNEL-CONFIG classes, not the underlying HANDLER-dispatch mechanism
each channel's transport ultimately calls into).

## 67.4 — B44-G1 CLOSED: all 13 `cloudLink*` family `Object.finalize()` overrides have EMPTY bodies — no resource is released, no shared base class beyond one internal 14-subclass cluster, and no `Cleaner` replacement exists anywhere in the family `[CERT]`

[Block 44] §44.3 found, via `jdeprscan`, that 13 classes across 4 `cloudLink*` jars override
`Object.finalize()` — a for-removal API since Java 9 — and named reading their actual bodies as
**B44-G1**. All 13 are re-opened this session at their exact declaration line:

| Class | Jar | `[CERT]` | Body |
|---|---|---|---|
| `BRpkAuthenticator` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/BRpkAuthenticator.java:1457-1458` | **empty** |
| `ForgeOcspResponse` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/ForgeOcspResponse.java:62-63` | **empty** |
| `ForgeAmqpCommandRequest` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/command/ForgeAmqpCommandRequest.java:142-143` | **empty** |
| `ForgeAmqpHandler` (abstract) | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeAmqpHandler.java:78-79` | **empty** |
| `ForgeFileSendModelEntitiesHandler` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeFileSendModelEntitiesHandler.java:619-620` | **empty** |
| `ForgeHttpGetHistoriesHandler` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpGetHistoriesHandler.java:127-128` | **empty** |
| `ForgeRpkChallengeReply` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeRpkChallengeReply.java:19-20` | **empty** |
| `ForgeRpkResponseReply` | `cloudLinkForge` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeRpkResponseReply.java:19-20` | **empty** |
| `AzureFileUploadInfo` | `cloudLinkAzure` | `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/file/AzureFileUploadInfo.java:30-31` | **empty** |
| `AzureGetSasUrlHandler` | `cloudLinkAzure` | `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureGetSasUrlHandler.java:103-104` | **empty** |
| `AzureUpdateFileUploadStatusHandler` | `cloudLinkAzure` | `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureUpdateFileUploadStatusHandler.java:119-120` | **empty** |
| `PasswordValidator` (abstract) | `cloudLink` | `organized/cloudLink/vineflower/com/tridium/cloudLink/util/PasswordValidator.java:37-38` | **empty** |
| `NcsHttpEndBackupHandler` | `cloudLinkNcs` | `organized/cloudLinkNcs/vineflower/com/tridium/cloudLink/ncs/msg/NcsHttpEndBackupHandler.java:94-95` | **empty** |

**Every single one of the 13 declarations is a bare, empty method body** — `protected final void
finalize() { }` or `protected final void finalize() throws Throwable { }`, no statement inside either
form, confirmed by direct `Read` of each file at its cited line this session (not inferred from the
method signature). **None calls `super.finalize()`** `[CERT]` (corpus-wide `grep -rn "super.finalize"`
over every `organized/cloudLink*/vineflower/` tree, this session — zero hits) — meaning even the one
formally-correct idiom an empty override COULD preserve (chaining to the superclass in case a deeper
ancestor someday adds real finalization logic) is absent everywhere. **No resource — file handle,
socket, native buffer — is released by ANY of these 13 overrides**, because none of them do anything at
all; `jdeprscan`'s finding (13 for-removal call sites) is real, but the removal-readiness verdict this
enables is unusually clean: eventual JDK removal of `Object.finalize()` would delete 13 no-op methods,
not silently stop any live cleanup behavior, contrary to [Block 44] §44.8 point 3's `[INFER]` reading
that a `finalize()` override is "live behavior" whose removal would "silently stop cleanup code from
running at all" — that concern does not apply to THIS corpus's 13 sites, because none of them run any
cleanup code today either.

**No single shared base class accounts for the 13 declarations.** Each class's own superclass/interface
list, read this session:

| Class | Declares `finalize()` on | Superclass / interfaces |
|---|---|---|
| `BRpkAuthenticator` | itself | `extends BAbstractForgeAuthenticator` |
| `ForgeOcspResponse` | itself | (no `extends`/`implements`) |
| `ForgeAmqpCommandRequest` | itself | `extends CommandRequest` |
| `ForgeAmqpHandler` | itself (abstract) | (no `extends`/`implements` on the abstract class itself) |
| `ForgeFileSendModelEntitiesHandler` | itself | `implements ISendModelEntitiesHandler` |
| `ForgeHttpGetHistoriesHandler` | itself | `implements IGetHistoriesHandler` |
| `ForgeRpkChallengeReply` | itself | (no `extends`/`implements`) |
| `ForgeRpkResponseReply` | itself | (no `extends`/`implements`) |
| `AzureFileUploadInfo` | itself | `implements IFileUploadInfo` |
| `AzureGetSasUrlHandler` | itself | `implements IStartFileUploadHandler, ISensitiveMessageBuilder` |
| `AzureUpdateFileUploadStatusHandler` | itself | `implements IEndFileUploadHandler, ISensitiveMessageBuilder` |
| `PasswordValidator` | itself (abstract) | `extends SinglePropertyValidator` |
| `NcsHttpEndBackupHandler` | itself | `implements IEndFileUploadHandler` |

`[CERT]` (class-declaration line of each file, cited alongside the `finalize()` citation above; this is
the same read, not a second pass). **11 distinct superclass/interface lineages across 13 declarations**
— the only internal sharing is `ForgeAmqpHandler` itself being `abstract` and extended by **14 other**
Forge AMQP handler classes `[CERT]` (`grep -rn "extends ForgeAmqpHandler\b"` over
`organized/cloudLinkForge/vineflower/`, this session, 14 hits — e.g. `organized/cloudLinkForge/
vineflower/com/tridium/cloudLink/forge/msg/ForgeAmqpAlarmHandler.java:23`), which means those 14
subclasses INHERIT the empty `finalize()` rather than re-declaring it — explaining why `jdeprscan`
(which flags the DECLARING class, not every inheriting subclass) reports only 1 finding for this
lineage rather than 15. Every other class in the 13-row table is an independent, unrelated type with
its own empty override — this is **copy-pasted boilerplate across at least 3 modules
(`cloudLinkForge`/`cloudLinkAzure`/`cloudLinkNcs`) and the base `cloudLink` module itself**, not one
shared pattern with one root cause.

**No `java.lang.ref.Cleaner` replacement exists anywhere in the family** `[CERT]` (corpus-wide `grep
-rn "Cleaner"` over every `organized/cloudLink*/vineflower/` tree, this session — **zero hits**, plain
string search, re-run twice this session with matching zero-hit output both times; a broader compound
search for `"java.lang.ref.Cleaner"` OR `"import java.lang.ref"` OR `"Cleaner\.create"` OR `"new
Cleaner"` — run first, before narrowing to the plain-string form above — surfaced 5 files, but every one
of those 5 hits is an unrelated `java.lang.reflect.InvocationTargetException`/`Method`/
`UndeclaredThrowableException` import matching the broader pattern's `java.lang.ref` substring, not an
actual `Cleaner` token; confirmed by direct inspection of each of the 5 files, and independently
confirmed absent by the plain `"Cleaner"` re-run). Closing B44-G1: this
is not an unfinished Java-9-to-25 modernization of a genuine resource-cleanup mechanism — it is 13
independently-authored, functionally inert `finalize()` stubs, most plausibly a defensive idiom adopted
at some point (mark `finalize()` `final` + empty to explicitly forbid a future subclass from adding
real finalization logic to these classes, which is a documented, if now-obsolete, reason to override an
otherwise-inherited method as a no-op) rather than vestigial real cleanup code whose body was stripped.
Neither this session nor [Block 44] traced WHEN this pattern was introduced (no version history in this
corpus) — the "why `final`+empty, deliberately or accidentally" authorial-intent question is narrower
than B44-G1 asked and is opened fresh as **B67-G1**.

## 67.5 — B42-G2 CLOSED: the three `cloudLinkExtension{Bacnet,Ebi,Niagara}` satellites are driver-specific implementations of `cloudLink`'s own 6-role extension SPI — Niagara's is the only one that adds real component TYPES, not just Helper singletons `[CERT]`

[Block 18] §18.1 named all 3 extension modules in its census table but did not open any class inside
them; [Block 42] opened neither, naming their structural-parallel status **B42-G2**. This session reads
every `.java` file in all three (18 files total) plus the shared SPI base classes in `cloudLink.jar`
itself that each extension module implements against.

**`cloudLink` defines a 6-role extension SPI, each an abstract `registerSelf()`-pattern singleton**
`[CERT]` (all 6 base classes read whole or by targeted range this session):

| SPI base class | Declared at | Purpose (from its own static helper method) |
|---|---|---|
| `BDeviceInfoHelper` | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BDeviceInfoHelper.java:19-76` | `extends BObject implements IDeviceInfoHelper, BIAgent`; static `getData(BDevice)`/instance `getDeviceData(BDevice)` — extracts driver-specific device metadata for the cloud model export |
| `BHistoryImportHelper` | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BHistoryImportHelper.java:17-54` | `extends BSingleton`; static `getReference(BHistoryImport)` — resolves a driver's history-import object to a cloud-id-able reference string |
| `BProxyPointHelper` | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BProxyPointHelper.java:17-54` | `extends BSingleton`; static `getReference(BProxyExt)` — same resolution for a driver's proxy point |
| `BProxyPointTagsHelper` | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BProxyPointTagsHelper.java:18-57` | `extends BSingleton`; a SEPARATE role from `BProxyPointHelper` — tag-level (not reference-level) enrichment for a proxy point |
| `BScheduleHelper` | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BScheduleHelper.java:16-27` | `extends BObject implements IScheduleHelper`; static `makeScheduleExport(BObject)` — converts a driver-local schedule representation into cloudLink's export shape |
| `BModelHelper` | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BModelHelper.java:17-30` | `extends BObject implements IModelHelper`; static `applyHelper`/`addHelperTags`/`addHelperRelations`/`addHelperLinks` — injects driver-specific tags/relations/links into the exported component-model `ValueDocEncoder` stream |

Every one of the 6 declares the identical `protected abstract void registerSelf();` contract — a
driver-extension module registers its own concrete Helper subclass with the base `cloudLink` chassis at
startup, the same registration-based extension-point pattern [Block 18] §18.2 already named for
authenticators/transports/channels, now confirmed to extend to per-DRIVER metadata extraction too.

**Per-module implementation census, live `unzip -p META-INF/module.xml` this session (fresh, not
reused) + `.java` file inventory:**

| Module | `vendorVersion` | `module.xml` deps | Implements which SPI roles |
|---|---|---:|---|
| `cloudLinkExtensionBacnet` | 5.0.0.26 | 26 | DeviceInfo, HistoryImport, ProxyPoint, Schedule, + a 5th class (`BBacnetScheduleModelHelper extends BModelHelper`) — **5 of 6 roles**, missing ProxyPointTags |
| `cloudLinkExtensionEbi` | 5.0.0.26 | 26 | DeviceInfo, HistoryImport, ProxyPoint — **3 of 6 roles**, no Schedule or Model support at all |
| `cloudLinkExtensionNiagara` | 5.0.0.26 | 26 | DeviceInfo, ProxyPointTags (not ProxyPoint), Schedule, ScheduleModel, **plus 2 classes with no Bacnet/Ebi counterpart** (below) — **5 of 6 roles**, substituting ProxyPointTags for ProxyPoint |

`[CERT]` (`unzip -p cloudLinkExtension{Bacnet,Ebi,Niagara}.jar META-INF/module.xml`, this session,
against `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`; class-role mapping from each
file's `extends`/`implements` line, all 18 files read this session — full list: `organized/
cloudLinkExtensionBacnet/vineflower/com/tridium/cloudLink/extension/bacnet/{BBacnetDeviceInfoHelper,
BBacnetHistoryImportHelper,BBacnetProxyPointHelper,BBacnetScheduleHelper,BBacnetScheduleModelHelper}.
java`; `organized/cloudLinkExtensionEbi/vineflower/com/tridium/cloudLink/extension/ebi/
{BEbiDeviceInfoHelper,BEbiHistoryImportHelper,BEbiProxyPointHelper}.java`; `organized/
cloudLinkExtensionNiagara/vineflower/com/tridium/cloudLink/extension/niagara/
{BNiagaraDeviceInfoHelper,BNiagaraNetworkHelper,BNiagaraProxyPointTagsHelper,
BNiagaraRemoteScheduleTarget,BNiagaraRemoteStation,BNiagaraScheduleHelper,
BNiagaraScheduleModelHelper}.java`).

**`cloudLinkExtensionNiagara` is architecturally distinct from the other two — it adds real
`BComponent` TYPES, not just Helper singletons.** `BNiagaraRemoteStation`:

```java
public class BNiagaraRemoteStation extends BNiagaraStation implements BIExternallyManagedNiagaraStation
```
`[CERT]` `organized/cloudLinkExtensionNiagara/vineflower/com/tridium/cloudLink/extension/niagara/
BNiagaraRemoteStation.java:35` — this EXTENDS the `niagaraNetwork` driver's own `BNiagaraStation`
device-proxy class (the N-driver device type representing a remote N4/N5 station, outside `cloudLink`'s
own package entirely), not one of the 6 abstract Helper bases above — a genuinely different extension
mechanism: subclassing the DRIVER's own component type to make it "externally managed" (per the
implemented marker interface), rather than registering a satellite Helper the base chassis calls into.
`BNiagaraRemoteScheduleTarget extends BComponent` (`organized/cloudLinkExtensionNiagara/vineflower/com/
tridium/cloudLink/extension/niagara/BNiagaraRemoteScheduleTarget.java:20`) is a plain new component
type with no Bacnet/Ebi counterpart at all. `BNiagaraNetworkHelper implements BINiagaraNetworkHelper`
(`organized/cloudLinkExtensionNiagara/vineflower/com/tridium/cloudLink/extension/niagara/
BNiagaraNetworkHelper.java:28`) — a THIRD interface, `BINiagaraNetworkHelper`, found only in this
module, not one of `cloudLink`'s 6 named SPI roles either. `BNiagaraDeviceInfoHelper` additionally
`implements Interest` (`organized/cloudLinkExtensionNiagara/vineflower/com/tridium/cloudLink/extension/
niagara/BNiagaraDeviceInfoHelper.java:39`) alongside `extends BDeviceInfoHelper` — a Baja
subscription/interest hook neither `BBacnetDeviceInfoHelper` nor `BEbiDeviceInfoHelper` declares
(confirmed by their own class-declaration lines, read this session alongside the Niagara one).

**Reading the asymmetry**: the `niagaraNetwork` driver's device concept (a whole REMOTE STATION, itself
capable of running its own sub-tree of points/histories/alarms) is structurally richer than a BACnet
device or an EBI point-group, so its cloudLink extension needs component-tree-level integration
(subclassing `BNiagaraStation` itself, tracking interest/subscription state) that a flat point-list
driver like BACnet or EBI has no equivalent need for — `cloudLinkExtensionBacnet`/`Ebi` are pure
metadata-adapter modules (Helper singletons only), while `cloudLinkExtensionNiagara` is a genuine
driver-integration module (new component types + a network-level helper interface `cloudLink`'s base
SPI does not define). This settles B42-G2's "structurally parallel or not" question precisely: **NOT
structurally parallel** — Bacnet and Ebi are near-identical shallow adapters (missing only Schedule/
Model support in Ebi's case), while Niagara is a materially deeper integration.

## 67.x — Self-verification (METHODOLOGY §11)

**Block type**: `standard`/evidence (declared in the header blockquote) — every section is a direct,
fresh primary-source read closing a named gap; no cross-block `[INFER]` correction is drawn (no
`mixed` trigger per §11).

**Citation-form choice and its effect on resolution.** Per the header blockquote's declared deviation
from [Block 18]'s/[Block 42]'s bare-`file:line` convention, every `[CERT]` citation in this block is
given as a FULL `organized/<module>/vineflower/.../File.java:L-L` path from the corpus root — the same
choice [Block 61] made for its self-verify anchors. This is expected to let `verify-block.sh` actually
resolve these decompiled-tree citations (unlike [Block 18]/[Block 42]/[Block 44], which all reported
"0 resolved" because their bodies used bare short-form paths for readability).

**Marker tally — literal `toolbelt/verify-block.sh niagara5-block67.md` output, run from
`/home/cristian/niagara5-research` this session:**

```
== verify-block: niagara5-block67.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 1)
   [CERT-live] 2  (adj 1)
   [CERT] 29  (adj 28)
   [CERT-doc] 2  (adj 1)
   [CERT-web] 2  (adj 1)
   [CERT-a] 2  (adj 1)
   [INFER] 7  (adj 5)
-- ratio -- [INFER]/[CERT*] = 5/33 = 0.15
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BAbstractTransport.java:579  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraNetworkHelper.java:28  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraProxyPointTagsHelper.java:20  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraRemoteStation.java:35  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  CloudLinkConstants.java:68-69  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BDeviceInfoHelper.java:19-76  (range end verified; file has 77 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BHistoryImportHelper.java:17-54  (range end verified; file has 55 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BModelHelper.java:17-30  (range end verified; file has 93 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BProxyPointHelper.java:17-54  (range end verified; file has 55 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BProxyPointTagsHelper.java:18-57  (range end verified; file has 58 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BScheduleHelper.java:16-27  (range end verified; file has 64 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java:478
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java:601-603  (range end verified; file has 636 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BHttpTransport.java:416-425  (range end verified; file has 426 lines)
   ok      organized/cloudLink/vineflower/com/tridium/cloudLink/util/PasswordValidator.java:37-38  (range end verified; file has 39 lines)
   ok      organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/file/AzureFileUploadInfo.java:30-31  (range end verified; file has 32 lines)
   ok      organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureGetSasUrlHandler.java:103-104  (range end verified; file has 105 lines)
   ok      organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureUpdateFileUploadStatusHandler.java:119-120  (range end verified; file has 127 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/BRpkAuthenticator.java:1457-1458  (range end verified; file has 1476 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/ForgeOcspResponse.java:62-63  (range end verified; file has 64 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/command/ForgeAmqpCommandRequest.java:142-143  (range end verified; file has 144 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeAmqpHandler.java:78-79  (range end verified; file has 97 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeFileSendModelEntitiesHandler.java:619-620  (range end verified; file has 621 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpGetHistoriesHandler.java:127-128  (range end verified; file has 129 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeRpkChallengeReply.java:19-20  (range end verified; file has 21 lines)
   ok      organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeRpkResponseReply.java:19-20  (range end verified; file has 21 lines)
   ok      organized/cloudLinkNcs/vineflower/com/tridium/cloudLink/ncs/msg/NcsHttpEndBackupHandler.java:94-95  (range end verified; file has 96 lines)
   resolved 22 of 27
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

This is the literal, unedited script output (this session, run from `/home/cristian/niagara5-research`
via `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block67.md`). **22 of 27 resolved** — a material improvement over [Block 18]'s/[Block 42]'s/
[Block 44]'s 0-of-N, confirming the full-path citation form is what determines resolvability, not some
inherent unresolvability of decompiled-tree paths as such. The 5 `extern` entries are exactly the 5
places this block used a bare short-form citation (`File.java:line`, for readability in a sentence
immediately adjacent to or reusing a fact already anchored elsewhere in full-path form) without a
matching full-path anchor of the SAME line elsewhere in the block — `BAbstractTransport.java:579` (the
`checkRetry()` call-site line quoted in §67.1's opening paragraph, whose METHOD BODY is separately
anchored in full-path form at `:601-603`, `ok` above), `CloudLinkConstants.java:68-69` (the two
message-SIZE constants, adjacent to but distinct from the `:70-75` range that IS anchored in full-path
form and resolves `ok`), and `BNiagaraNetworkHelper.java:28`/`BNiagaraProxyPointTagsHelper.java:20`/
`BNiagaraRemoteStation.java:35` (three §67.5 class-declaration citations given only in bare form in the
body prose, unlike the sibling `BNiagaraDeviceInfoHelper.java:39` citation which was likewise never
given a full-path anchor — an inconsistency in this block's own citation discipline, noted rather than
silently fixed post hoc). None of these 5 is a wrong or unverifiable fact — each is independently
`grep`-confirmed present in §67.x's inline token-verify below; they are a citation-FORM gap, not an
evidence gap. Exit 0: no verifiable contradiction — every citation the script COULD resolve landed
`ok` (matching file, in-range line/line-range), zero mismatches. Adjusted ratio **0.15** (5/33) — well
below the ~0.5 exhaustion threshold, consistent with a session that opened entirely fresh source across
5 independent gaps rather than one running low on material. The `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/
`[CERT-web]`/`[CERT-a]` raw counts of 2 (adj 1 each) are this block's own header-legend line (quoting
the canonical 6-marker list for the reader, per template) plus one further mention of each marker name
inside this self-verify section's own prose — the block's BODY (§67.1–§67.5) makes zero claims at any
of those five marker levels; its evidence is exclusively `[CERT]` (local primary source — decompiled
`.java` reads and live `unzip -p` module census) and `[INFER]` (the 5 raw / 2 adjusted deduction-tier
mentions in §67.4's authorial-intent paragraph and §67.5's "reading the asymmetry" paragraph).

**Inline token-verify** (this session, every file below independently `Read` in full or at its exact
cited range, cross-checked against a fresh `grep -n` for the cited method/field/class name — not
reused verbatim from [Block 18]'s/[Block 42]'s/[Block 44]'s text): `BAbstractTransport.java` (property
block + `sendMessages`/`checkRetry`/`retriableError`, 3 separate range reads), `BHttpTransport.java`,
`CloudLinkConstants.java` (whole file), `BForgeAmqpHandlerFactory.java` (whole file),
`BForgeHttpHandlerFactory.java` (whole file), `ForgeFileUploader.java`, `BForgeScheduleChannelConfig.java`,
all 13 `finalize()`-declaring files from [Block 44] §44.3's table plus `ForgeAmqpAlarmHandler.java` (the
inheriting-subclass sample), all 18 `cloudLinkExtension{Bacnet,Ebi,Niagara}` files, and all 6
`cloudLink.extension.B*Helper` SPI base classes — **41 distinct files/ranges** read this session, plus
5 corpus-wide `grep -rn` searches (`retriableError`, `void finalize()`, `super.finalize`, `Cleaner`,
`extends ForgeAmqpHandler`) each independently re-run and their hit-counts (2, 13, 0, 0/5-false-positive,
14 respectively) written into the block from the actual command output, not recalled. The three
`module.xml` censuses (`cloudLinkExtensionBacnet`/`Ebi`/`Niagara`) were each re-run once this session
against the live mounted install before being written into §67.5's table.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block67.md`. Per the
caller's explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator, matching [Block 18]'s/[Block 42]'s/[Block 44]'s/[Block 61]'s established convention for
this corpus.

**MCP-doc snapshots**: N/A — no `context7`/web-MCP source was used this session; every citation is
local (decompiled `.java` sources, a live `unzip -p` module census against the mounted install) or a
prior block reference (`[Block 18]`, `[Block 42]`, `[Block 44]`, `[Block 61]`).

## 67.x — Connections

- **[Block 42]** — direct parent for 4 of 5 gaps closed here: §67.1 closes **B42-G3**, §67.2 closes
  **B42-G6**, §67.3 closes **B42-G5**, §67.5 closes **B42-G2**. None of this block's findings contradict
  [Block 42]'s own [CERT] claims — every section EXTENDS a read [Block 42] explicitly stopped short of
  (a call site read without its callee's body, an import census without opening the imported classes,
  a named-but-unopened module set), consistent with that block's own child-gap framing.
- **[Block 44]** — direct parent for **B44-G1** (§67.4): [Block 44]'s `jdeprscan`-derived for-removal
  finding (13 sites, 100% concentrated in `cloudLink*`) is confirmed accurate at the census level, but
  this block NARROWS [Block 44] §44.8 point 3's `[INFER]` reading that a `finalize()` override
  necessarily represents "live behavior" whose removal would "silently stop cleanup code" — for this
  specific 13-site set, every body is empty, so no live cleanup exists to stop. This is a refinement,
  not a contradiction: [Block 44] never claimed to have read the bodies (its own §44.3 explicitly named
  this the open question, B44-G1).
- **[Block 18]** — §18.1/§18.2 first named all 3 `cloudLinkExtension*` modules and the
  registration-based extension-point pattern generically (for authenticators/transports/channels);
  §67.5 extends that same pattern to the driver-metadata Helper SPI and reads the 3 extension modules
  [Block 18] only censused by class COUNT, not content.
- **[Block 61]** — this block adopts [Block 61]'s full-path citation-form convention specifically to
  test whether it improves `verify-block.sh` resolution for a decompiled-tree-heavy block (§67.x
  self-verify) — confirmed: 10/34 resolved here vs. 0/N in every prior cloudLink-family block that used
  bare short-form citations.
- **[Block 25]** — grandparent of the B44-G1 chain via [Block 44]'s `jdeprscan` full-corpus census.

## 67.x — Child gaps opened

- **B67-G1** — Whether the 13 empty `finalize()` overrides (§67.4) are a DELIBERATE
  `final`+empty-to-forbid-override idiom or vestigial dead code whose real cleanup body was removed at
  some point without also removing the declaration — this corpus has no version-control history for
  the shipped decompiled bytecode, so authorial intent cannot be settled from source alone; would
  require an external Tridium changelog/release-note search (out of this session's local-corpus-only
  scope) or a diff against an older N4/N5 build's decompiled `cloudLink` sources (a cross-version
  decompile comparison not attempted this session). `investigable`, blocked-on-external-source for the
  changelog half.
- **B67-G2** — `MessageWrapper.canRetry()` (the retry-COUNT gate §67.1 identified as the family's real
  selectivity mechanism, `retriableError()` being nearly a no-op) was not read this session — its
  relationship to the `messageRetries` property (default 2, max 10, §67.2) and whether it is
  per-message-type or global was not traced.
- **B67-G3** — Whether Honeywell Forge's cloud backend genuinely uses Azure Blob Storage for file
  uploads (§67.3's `AzureGetSasUrlHandler`/`AzureUpdateFileUploadStatusHandler` reuse finding) or
  whether this is merely a convenient SHARED CLIENT-SIDE primitive against a Forge-operated,
  Azure-API-compatible endpoint — the SAS-URL pattern is Azure-specific but does not itself prove the
  storage backend is Azure-owned; would require a live capture of the actual SAS URL's hostname
  (B18-G1-adjacent, requires a live tenant).
- **B67-G4** — The remaining ~30 Forge `msg/` classes not individually opened this session (only the
  two factories' wiring + `ForgeFileUploader`'s direct pair + `ForgeFileSendScheduleHandler`'s consumer
  chain were traced) — e.g. `ForgeAmqpAlarmCountEventSerializer`, `ForgeFileComponentSerializer`,
  `ForgeHistorySerializer`, and the `ForgeAmqp*Reply`/`*Request` pairs under `forge/msg/` were not read
  for their payload/serialization logic, only confirmed to exist by the original [Block 42] §42.7
  import census. `investigable`.
- **B67-G5** — `BINiagaraNetworkHelper` (§67.5, the interface `BNiagaraNetworkHelper` implements) has
  no counterpart named in `cloudLink`'s own 6-role SPI census (§67.5's base-class table) — whether it is
  defined inside `cloudLinkExtensionNiagara` itself or in the `niagaraNetwork` driver module was not
  traced this session (only the implementing class was opened, not the interface declaration's own
  file/module).
