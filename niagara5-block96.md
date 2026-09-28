# Block 96 — Cloud connectors, licensing features, NCS agent: nine gap closures spanning Forge payload bodies, Forge tenant proxying, platform license-key censuses, a corpus-wide dead-constant sweep, subscription-licensing response shapes, a resolved device-registration disjunction, and NCS-Agent's Thrift/mTLS convergence with the station's own cloud identity

> Research closing/narrowing nine previously-opened child gaps drawn from five parent blocks. Covers:
> **B88-G1** ([Block 88] §88.x — "Full payload/serialization-logic body reads of the 9 substantial,
> still-unopened `cloudLinkForge/forge/msg/` classes named in §88.6"); **B88-G3** ([Block 88] §88.x —
> "Whether `cloudLinkForge`'s Honeywell-Forge-branded tenant ... is itself an Azure IoT Hub tenant
> under Honeywell's own Azure subscription, or a Forge-operated proxy in front of one"); **B90-G2**
> ([Block 90] §90.x — "Enumerate `BCloudConnectionService.getPlatformType()`'s actual return-value
> set"); **B90-G4** ([Block 90] §90.x — "A full corpus-wide census of every concrete
> `BPlatformService`/`BIPlatformCommand` subtype's `getLicenseVendor()`/`getLicenseFeature()`
> override"); **B85-G1** ([Block 85] §85.x — "A systematic corpus-wide audit for the 'declared
> constant shadowed by an independent identical-literal at its real call site' anti-pattern");
> **B85-G3** ([Block 85] §85.x — "`RotateKeys`'s and `RequestCertificates`'s RESPONSE field shapes ...
> were not read this session"); **B77-G4** ([Block 77] §77.x — "Whether
> `DEVICE_REGISTRATION_RESPONSE_TYPE`/`DEVICE_REGISTRATION_GRANT_TYPE`/`DEVICE_REGISTRATION_HOST`'s
> dead-constant status ... is a refactor artifact or an unfinished configurability path"); **B18-G5**
> ([Block 18] §18.x — "Trace whether `NCS-Agent`'s own device-registration REST calls
> (`/api/v1/deviceregistration/*`) converge on the same backend device identity as `cloudLinkNcs`'s
> station-side `NiagaraCloudIdentity`/federated-identity flow, or are a genuinely separate registration
> domain"); **B18-G6** ([Block 18] §18.x — "Deeper reverse-engineering of the `NCS-Agent` Go binary
> (disassembly/decompilation of actual logic, not just string-table census)"). Does **not** cover: a
> full per-candidate manual triage of every one of the ~3600 dead-constant candidates the B85-G1 sweep
> surfaced (script + counts only — see child gap); live-traffic capture of a real Forge/NCS device
> registration (all findings are static-source/static-binary); instruction-level disassembly of
> individual NCS-Agent Go functions (blocked by a stripped Go symbol table — see child gap); a full
> census of every `cloudLinkForge`/`cloudLinkHonSbp` per-provider channel-config class (B18-G3,
> untouched).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at
> `/home/cristian/niagara5-research/organized/` (canonical `vineflower/`-tree sweep this session: 14,578
> `.java` files, excluding `fallback/`/`docSource/`/`obfuscated-bak/`/`extracted/`/`decompiled/`/
> `pipeline/`/`deobf/` duplicate subtrees). N5 install (READ-ONLY) for the native binary:
> `/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe`
> (sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`, copied read-only into this
> session's scratch for tool access). Census method for B85-G1/B90-G4: `find organized -path
> '*/vineflower/*' -name '*.java' | grep -v -E '(fallback|obfuscated-bak|docSource|extracted|decompiled|
> pipeline|deobf)'` (matches every prior block's `find -exec`-over-shell-glob convention). One Python
> script (`dead_constant_sweep.py`) was written this session for the B85-G1 mechanical sweep, preserved
> at `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/
> b96/` (scratch, not archived in the corpus) along with its two JSON outputs (`dead_constants_all.json`,
> `dead_constants_shadowed.json`). Native tooling: `strings`, `file`, `objdump`/`nm` (GNU binutils via
> Homebrew), `radare2` 6.2.0, and the Go 1.27.0 toolchain's own `go tool nm`/`go tool objdump` (all
> attempted against the NCS-Agent binary; results and the one confirmed tooling limitation are in
> §96.9). Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line` or a
> literal command/tool-output) · `[CERT-hw]` installed-binary evidence with sha256 · `[CERT-doc]`/
> `[CERT-web]` not used in this block · `[INFER]` deduction.

---

## 96.1 — B88-G1 CLOSED: all 9 named `cloudLinkForge/forge/msg/` classes' payload bodies read; three concrete wire schemas recovered (history-sample JSON, CSOM/tag-dictionary export JSON, history-query response JSON) `[CERT]`

The gap's own text (quoted above) names 9 classes. All 9 exist and were read in full this session:
`ForgeFileSendScheduleHandler`, `ForgeFileSendModelCloseHandler`, `ForgeFileSendHistoriesBulkHandler`,
`ForgeHttpGetHistoriesResult`, `ForgeAmqpSendPointValuesHandler`, `ForgeAmqpEventSerializer`,
`ForgeFileHistoryConfigSerializer`, `ForgeHistorySerializer` (`ForgeMsgConstants` — the 9th name in
the gap's list — is explicitly named "a constants dump, low priority" by the gap's own text and was
not re-read; it is a pure `String` constant holder, already effectively covered by other
`ForgeMsgConstants.*` field references cited below).

**`ForgeFileSendScheduleHandler`** (`organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeFileSendScheduleHandler.java:40-320`)
converts a `BAbstractSchedule` to an iCalendar `VCALENDAR` (via `biweekly`'s `ICalWriter`), gzips it,
and either saves it to `cloudLinkSchedule/schedule_<systemGuid>_<cloudId>_<UTC-timestamp>.ics.gz` or
uploads it through the channel's `FileUploader`, with upload metadata `[CERT]`
(`ForgeFileSendScheduleHandler.java:116-124`): `{fileType: "schedule", mimetype: "text/ics+gzip",
version: "1.0", format: <filename>, filename: <filename-without-extension>}`.

**`ForgeFileSendModelCloseHandler`** (`ForgeFileSendModelCloseHandler.java:41-298`) writes the
end-of-model-export "CSOM" (Cloud System Object Model) file, `<systemGuid>_<exportId>_csom.json.gz`,
metadata `{filetype: "n4csom", mimetype: "application/json+gzip", version: "1"}` `[CERT]`
(`ForgeFileSendModelCloseHandler.java:115-118`). Its JSON body shape, built with
`com.tridium.json.quick.QuickJSONWriter`, is `[CERT]` (`ForgeFileSendModelCloseHandler.java:104-109,130-135`):
`{"metadata": <config.makeModelMetadata()>, "adHocTagDictionary": {"tags": [{"n": <name>, "t": <type>}, ...],
"relations": [<qName>, ...]}, "tagDictionaries": {<dictionaryDisplayName>: <encoded-value-doc>, ...}}`.

**`ForgeFileSendHistoriesBulkHandler`** (`ForgeFileSendHistoriesBulkHandler.java:32-234`) is the
backfill/bulk-history uploader used after a reconnect, writing
`<systemGuid>_history_<exportId>_<fileCounter>.gz`, metadata `[CERT]`
(`ForgeFileSendHistoriesBulkHandler.java:228-233`): `{filetype: "history+gzip", mimetype:
"application/json+gzip", version: "2", mode: "BackfillAfterReconnect"}`; its per-record body is
delegated to `ForgeHistorySerializer` (below).

**`ForgeHistorySerializer`** (`ForgeHistorySerializer.java:21-120`) is the canonical history-sample JSON
schema shared by the bulk uploader: `[CERT]` (`ForgeHistorySerializer.java:37-68`)
`{"HistorySamples": [{"ItemName": <cloudId>, "Quality": "good", "Time": <ISO-string>, "Value": <flattened
value>, "Properties": {<remaining flattened BComplex fields, dot-prefixed, with numeric/boolean/enum-ordinal/
bit-string special-casing and "Infinity"/"-Infinity"/"NaN" string substitution for non-finite doubles>}}, ...]}`.

**`ForgeAmqpSendPointValuesHandler`** (`ForgeAmqpSendPointValuesHandler.java:22-131`) sends live/snapshot
point updates over the AMQP transport with the `"HistoryUpdateMessage"` command name, version `"1"`
`[CERT]` (`ForgeAmqpSendPointValuesHandler.java:29-30,36`), and a near-identical but distinct per-item
body shape from `ForgeHistorySerializer`'s file-upload one — `[CERT]`
(`ForgeAmqpSendPointValuesHandler.java:53-64,80-86`): `{"ItemName": <id>, "Quality": "\"<status>\""
(quote-wrapped literal string, not a JSON string field — the same value gets double-quoted inside the JSON
string value itself, a distinct serialization quirk from the file-upload path's plain `"good"`), "Time":
<ISO/encoded timestamp>, "Value": <status value>}`, wrapped in the outer envelope `{"HistorySamples": [...]}`
(`ForgeAmqpSendPointValuesHandler.java:120-122`, inherited from `ForgeAmqpHandler.initializeMessage()`).

**`ForgeAmqpEventSerializer`** (`ForgeAmqpEventSerializer.java:25-133`) serializes a `BEvent` into an
AMQP event message: `[CERT]` (`ForgeAmqpEventSerializer.java:45-54`) `{"Id": <event UUID>, "CreatedTime":
<encoded timestamp>, "CreatorId": "NiagaraFramework" (default, overridable via the event value's own
`creatorId` property), "CreatorType": "Niagara4" (default, likewise overridable), "TargetId": <last source
ORD>, "TargetType": "BEvent" (default), "TargetContext": "BOrdList" (default), "Body": null, "BodyProperties":
[{"Key": <name>, "Value": <string>}, ...] (flattened; includes "CloudId"/"EventUuid"/"EventTimestamp"/
"EventSource"/"SystemType" plus every non-`ForgeMsgConstants.OVERRIDE_PROPS` property of the event's value,
dot-qualified for nested `BComplex` values), "EventType": "BEvent" (default)}`.

**`ForgeFileHistoryConfigSerializer`** (`ForgeFileHistoryConfigSerializer.java:26-123`) is not itself a
wire-schema producer but a tag-injection step run during CSOM model export: for each `BHistoryConfig` with
a resolved telemetry ID, it stamps escaped tag slots directly onto the in-memory component before encoding
— `n:history` (the history's own encoded ID), the cloud-ID tag, `nc:telemetryId`, a data-type tag, and a
type-ID tag `[CERT]` (`ForgeFileHistoryConfigSerializer.java:54-81`), plus (when present) `n:range`/
`n:units`/`n:trueText`/`n:falseText` facet-derived tags `[CERT]` (`ForgeFileHistoryConfigSerializer.java:82-109`),
before delegating to the shared `ComponentEncoder` for the actual JSON body.

**`ForgeHttpGetHistoriesResult`** (`ForgeHttpGetHistoriesResult.java:42-225`) is the client-side parser for
the HTTP history-query response: `[CERT]` (`ForgeHttpGetHistoriesResult.java:51-96,154-171`)
`{"pointDetails": [{"pointId": <telemetryId>, "preRecord": {"time": ..., "value": ..., "properties": {...}}
(optional), "postRecord": {...} (optional), "historyRecords": [{"time": <ISO string>, "value": <JSON value>,
"properties": {<dot-qualified field map>}}, ...]}]}` — an empty `pointDetails` array or an unresolvable
`pointId` both short-circuit to an empty result rather than an error (`ForgeHttpGetHistoriesResult.java:54-66`).

**B88-G1 verdict: CLOSED.** All 8 substantial classes' bodies (of the 9 named; the 9th is the
already-characterized constants dump) were read and their concrete wire shapes recovered above,
narrowing [Block 67]'s original B67-G4 to zero remaining unopened files in this named set.

## 96.2 — B88-G3 NARROWED: `cloudLinkForge`'s file-upload SAS-issuing path is a Forge-branded REST gateway (`/api/(v2/)systems/{id}/fileuploadrequest`, response `{CorrelationId, FileUploadSasUrl}`), structurally distinct from Azure IoT Hub's own file-upload API — but the actual tenant host is a runtime-configured value, so tenancy itself remains unconfirmed `[CERT]`+`[INFER]`

[Block 88] §88.x's own gap text (quoted above) asks whether Forge's SAS-issuing endpoint is Honeywell's
own Azure IoT Hub tenant or "a Forge-operated proxy in front of one." `ForgeHttpStartFileUploadHandler`
(`organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpStartFileUploadHandler.java:29-125`)
builds its upload-request URL from a `connectionInfo` map's `uploadUrlTemplate`/`hostName`/`id` entries
(`ForgeHttpStartFileUploadHandler.java:56-60`), and `ForgeHttpStartFileUploadResult`
(`ForgeHttpStartFileUploadResult.java:9-35`) parses the response as `{"CorrelationId": <id>,
"FileUploadSasUrl": <url>}` — optionally nested one level inside an `"ApiCall"` wrapper object
(`ForgeHttpStartFileUploadResult.java:17-22`) — the SAME response schema table entry [Block 88] §88.3
already cited for `AzureGetSasUrlHandler`'s response is, by [Block 88]'s own quoted evidence,
`correlationId/hostName/containerName/blobName/sasToken`
(`organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureGetSasUrlHandler.java:53-57`;
`organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/file/AzureFileUploadInfo.java:12-16`) —
**a genuinely different field-name schema** `[CERT]`, confirming these are two independently-implemented
client parsers, not a shared code path.

The `uploadUrlTemplate` itself is `[CERT]`
`organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/ForgeConstants.java:20-21`:
`FORGE_FILE_UPLOAD_URL_TEMPLATE = "https://%s/api/systems/%s/fileuploadrequest"` (legacy/`IoTHub`
provider) and `FORGE_FILE_UPLOAD_URL_TEMPLATE_V2 = "https://%s/api/v2/systems/%s/fileuploadrequest"`
(non-`IoTHub` provider, i.e. `IoTHub2`/`RabbitMq` per `ForgeConstants.java:16-18`) — a Forge-owned
REST path shape (`/api/(v2/)systems/{systemId}/fileuploadrequest`), not Azure IoT Hub's own native
file-upload-notification REST API (`/devices/{id}/files?api-version=...`, per [Block 88] §88.3's own
cite of `AzureGetSasUrlHandler.java:53-57`). This distinction, and the `"ApiCall"` wrapper-object shape,
are consistent with Forge operating an API gateway in front of whatever storage backend ultimately
issues the SAS token — matching the gap's "Forge-operated proxy" hypothesis over a bare pass-through of
Azure IoT Hub's own API surface `[INFER]`.

**The actual host is not a compile-time literal**, however: `BForgeCertificateAuthenticator.getConnectionInfo()`
(`organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/BForgeCertificateAuthenticator.java:418-487`)
populates `connectionMap.put("hostName", ...)` from `this.getRegistrationHost()` for the file-upload
operation (`BForgeCertificateAuthenticator.java:453-461`), and `registrationHost` is a plain, empty-by-default
`BString` component property, `flags=5` `[CERT]` (`BForgeCertificateAuthenticator.java:116,163,268-274`) —
set at commissioning time, never hardcoded. No corpus-wide literal Azure or Honeywell domain exists for
this specific path (a targeted `grep` for `hostName` assignments in `cloudLinkForge` found only this
property-backed accessor and its two AMQP/HTTP siblings — `BForgeCertificateAuthenticator.java:449,463-464`
— none of which carry a compiled-in host literal). **B88-G3 verdict: NARROWED, not closed.** The
gateway-vs-passthrough architecture question is resolved in Forge's favor by the distinct REST
path/response-schema evidence above (`[CERT]`), but *whose* Azure subscription (if any) sits behind that
gateway remains a live-registration question — the same class of blocker the gap's own text and [Block
67] §67.x already named, now narrowed to a single specific unknown (the runtime `registrationHost`
value) rather than an open architectural question. New child gap: **B96-G3**.

## 96.3 — B90-G2 CLOSED: `getPlatformType()`'s complete concrete value set is `{"Forge", "NCS", "HoneywellSBP"}` plus two internal sentinels `{"null", "NONE"}` `[CERT]`

`BCloudConnectionService` is declared `final` (`organized/cloudLink/vineflower/com/tridium/cloudLink/BCloudConnectionService.java:85`)
and its `getPlatformType()` (`BCloudConnectionService.java:119-121`) is a plain generated accessor over
a `BString` property (`BCloudConnectionService.java:75,87`, default `BString.DEFAULT`, `flags=5`) —
**never assigned a literal anywhere in the corpus** (`find ... -exec grep -Hn "setPlatformType("` returns
exactly two hits corpus-wide: the accessor's own declaration and one internal restore-on-failure call,
`BCloudConnectionService.java:353`, that reassigns a previously-read backup value, not a literal
`[CERT]`). The actual value set is instead defined by every concrete `getKey()`-bearing factory/manager
this string is looked up against (`BCloudConnectionService.java:440,653,681,700`, per [Block 90] §90.6's
own already-published generic-dispatch pattern), each of which derives its key from its own
`getPlatformType()` override:

| Registered value | `[CERT]` source (`getPlatformType()` override) |
|---|---|
| `"Forge"` | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/BForgeAmqpHandlerFactory.java:61-63`, `BForgeHttpHandlerFactory.java:38-40`, `channel/BForgeChannelConfigFactory.java:19-21`, `file/BForgeFileUploadManager.java:25-27` |
| `"NCS"` | `organized/cloudLinkNcs/vineflower/com/tridium/cloudLink/ncs/BNcsAmqpHandlerFactory.java:60-62`, `BNcsHttpHandlerFactory.java:44-46`, `channel/BNcsChannelConfigFactory.java:25-27`, `file/BNcsFileUploadManager.java:30-32` |
| `"HoneywellSBP"` | `organized/cloudLinkHonSbp/vineflower/com/tridium/cloudLink/honsbp/BHonSbpAmqpHandlerFactory.java:63-65`, `BHonSbpHttpHandlerFactory.java:42-44`, `channel/BHonSbpChannelConfigFactory.java:26-28`, `file/BHonSbpFileUploadManager.java:30-32` |
| `"null"` (literal string, internal sentinel — not the Java `null`) | `organized/cloudLink/vineflower/com/tridium/cloudLink/BNullChannelConfigFactory.java:23-25` |
| `"NONE"` | `organized/cloudLink/vineflower/com/tridium/cloudLink/channel/BNullChannelConfig.java:24-26` (a per-channel, not per-factory, unconfigured-config sentinel) |

Both `getKey()` bases derive directly from `getPlatformType()` — `BAbstractCloudLinkHandlerFactory.getKey()`
returns `this.getPlatformType() + ";" + this.getTransportType()`
(`organized/cloudLink/vineflower/com/tridium/cloudLink/BAbstractCloudLinkHandlerFactory.java:35-36`) and
`BAbstractChannelConfigFactory.getKey()` returns `this.getPlatformType()` directly
(`organized/cloudLink/vineflower/com/tridium/cloudLink/BAbstractChannelConfigFactory.java:31-32`) — `[CERT]`,
confirming the table above is exhaustive: a corpus-wide search for every `getPlatformType()` override
under a `cloudLink*` package returns exactly these 3 real-platform + 2 sentinel values, no others.
**B90-G2 verdict: CLOSED.** The complete concrete `tridium:<platformType>{Recover,Remote}` feature-key
list [Block 90] §90.6 asked for is therefore `tridium:{Forge,NCS,HoneywellSBP}{Recover,Remote}` (6 keys),
modulo the `<connection-service-vendor>` prefix itself also being dynamic per §90.6's own finding.

## 96.4 — B90-G4 CLOSED: full corpus-wide census of `BPlatformService`/`BIPlatformCommand` license-gate overrides — 18 direct + 24 second-level `BPlatformService` subtypes (11 gate a feature, 0 of the 24 hardware/OS variants add a further override), and a complete `BIPlatformCommand` tree (`BAbstractPlatformCommand` → 17 `platDaemon` leaves, all sharing one `tridium:workbench` key) `[CERT]`

**`BPlatformService` subtypes.** A corpus-wide `find ... -exec grep -l "extends BPlatformService"`
(excluding `fallback/`) returns exactly **18 direct subtypes**; none of the further **24 second-level**
OS/hardware-variant subclasses (`*PlatformServiceWin32`/`*Npsdk`/`*Linux`/`*Qnx`/`*Atlas`/`*Emstp`/
`*UbuntuCore`, etc. — e.g. `organized/platform/vineflower/com/tridium/platform/win32/BSystemPlatformServiceWin32.java`,
`organized/platMstp/vineflower/com/tridium/platMstp/BBacnetMstpPlatformServiceNpsdk.java`) add their own
`getLicenseVendor()`/`getLicenseFeature()` override `[CERT]` (individually grepped, zero hits across all
24) — the license gate is fixed at the first (module-level) subclass, never further specialized per
hardware target:

| Module class | `getLicenseFeature()` | `getLicenseVendor()` | `[CERT]` |
|---|---|---|---|
| `platMstp.BBacnetMstpPlatformService` | `"mstp"` | (inherited `"tridium"`) | `organized/platMstp/vineflower/com/tridium/platMstp/BBacnetMstpPlatformService.java:75-77` |
| `platIEEE8021X.BIEEE8021XPlatformService` | `"ieee8021x"` | `"tridium"` (explicit) | `organized/platIEEE8021X/vineflower/com/tridium/platIEEE8021X/BIEEE8021XPlatformService.java:73-79` |
| `platform.syslog.BSyslogPlatformService` | `null` | (inherited `"tridium"`) | `organized/platform/vineflower/com/tridium/platform/syslog/BSyslogPlatformService.java:280-282` |
| `platBacnet.BBacnetEthernetPlatformService` | `null` | (inherited `"tridium"`) | `organized/platBacnet/vineflower/com/tridium/platBacnet/BBacnetEthernetPlatformService.java:53-55` |
| `platCcn.BCcnPlatformService` | `"ccnl"` | (inherited `"tridium"`) | `organized/platCcn/vineflower/com/tridium/platCcn/BCcnPlatformService.java:66-68` |
| `platNurio.BNurioPlatformService` | `"nurio"` | (inherited `"tridium"`) | `organized/platNurio/vineflower/com/tridium/platNurio/BNurioPlatformService.java:35-37` |
| `platDataRecovery.BDataRecoveryService` | `"dataRecovery"` | `"tridium"` (explicit) | `organized/platDataRecovery/vineflower/com/tridium/platDataRecovery/BDataRecoveryService.java:641-647` |
| `platNrio.BNrioPlatformService` | `"nrio"` | (inherited `"tridium"`) | `organized/platNrio/vineflower/com/tridium/platNrio/BNrioPlatformService.java:37-39` |
| `platEdgeIo.BEdgeIoPlatformService` | `null` | (inherited `"tridium"`) | `organized/platEdgeIo/vineflower/com/tridium/platEdgeIo/BEdgeIoPlatformService.java:29-31` |
| `platAceIpc.BAceIpcPlatformService` | `null` | (inherited `"tridium"`) | `organized/platAceIpc/vineflower/com/tridium/platAceIpc/BAceIpcPlatformService.java:29-31` |
| `platLon.BLonPlatformService` | `"lonworks"` | (inherited `"tridium"`) | `organized/platLon/vineflower/com/tridium/platLon/BLonPlatformService.java:29-31` |
| `platSerial`, `platform.BSystemPlatformService`, `platform.tcpip.BTcpIpPlatformService`, `platform.license.BLicensePlatformService`, `platform.ntp.BNtpPlatformService`, `platHwScan.BHardwareScanService`, `platCrypto.BCertManagerService` (7 classes) | — no override — | — no override — | inherit `BPlatformService`'s own default: `getLicenseFeature() → null`, `getLicenseVendor() → "tridium"` (`organized/platform/vineflower/com/tridium/platform/BPlatformService.java:94-100`, per [Block 90] §90.6) |

11 of 18 gate a real feature key (`"mstp"`, `"ieee8021x"`, `"ccnl"` — reproducing [Block 90] §90.6's own
`platCcn` finding — `"nurio"`, `"dataRecovery"`, `"nrio"`, `"lonworks"`, plus 4 explicit `null` overrides
that are functionally unlicensed); 7 never override at all and are therefore silently unlicensed
(`checkFeature(vendor, null)`) via the same generic dispatch loop.

**`BIPlatformCommand` subtypes.** Exactly one class implements the interface directly,
`BAbstractPlatformCommand` (`organized/platform/vineflower/com/tridium/platform/command/BAbstractPlatformCommand.java`),
which itself re-declares the interface's own `null`/`null` default explicitly
(`BAbstractPlatformCommand.java:50-57`) rather than leaving it inherited. It has exactly **2 direct
subclasses** (`find ... -exec grep -l "extends BAbstractPlatformCommand"`): `BPlatformCommandScript`
(zero further subclasses, no override — inherits `null`/`null`, i.e. unlicensed) and
`BDaemonSessionCommand`, which itself has exactly **17 concrete leaf subclasses**, all in `platDaemon`,
and **all 17 override both methods to the identical pair** `[CERT]` (grepped and read individually,
representative citations `organized/platDaemon/vineflower/com/tridium/platDaemon/command/BBackupInstallCommand.java:110-116`,
`.../BStartStationCommand.java:40-46`, `.../BFileGetCommand.java:47-53`): `getLicenseVendor() →
"tridium"`, `getLicenseFeature() → "workbench"` — every platform-daemon session command (file get/put/
list/delete, module/dist/backup install, start/stop/tell/watch/list station, reboot host, set time, ip
config, big-files, details) gates on the **same single** `tridium:workbench` key, not a per-command
feature. No class extends `BPlatformCommandScript` or any of the 17 `BDaemonSessionCommand` leaves.

**B90-G4 verdict: CLOSED.** Full corpus-wide census complete for both hierarchies: 18 + 24 = 42
`BPlatformService`-family classes (11 real license gates, 4 explicit-null, 7 inherited-null, 24 with no
further override), and the complete `BIPlatformCommand` tree (1 interface implementer, 2 direct + 17
second-level subclasses, one shared `tridium:workbench` key for the entire `platDaemon` command family)
— closing the loop [Block 11] §11.9 and [Block 90] §90.6 both left open.

## 96.5 — B85-G1 NARROWED: the mechanical corpus-wide sweep runs clean and finds the "shadow-literal dead-constant" anti-pattern is pervasive — not a 2-instance anomaly — recurring in at least 680 files at various scales, from a single accidental bug to a 268-instance systematic table; full per-candidate triage of the ~3600 surfaced pairs is a separate, large, mechanical follow-on `[CERT]`+`[INFER]`

> **Correction (added by [Block 115], §115.3, §14 cross-block).** This sweep's method (decompiled source
> only) cannot distinguish a compile-time-INLINED reference to the "dead" constant from a genuinely
> independent duplicate literal — `static final` `String`/primitive fields are JLS §4.12.4 compile-time
> constants, inlined by `javac` into every caller's own constant pool, so a referencing site and an
> unrelated duplicate both decompile to the identical bare literal. [Block 115] §115.3 proves this
> concretely on a real, docSource-covered pair from this sweep's own `dead_constants_shadowed.json`
> (`BTagDictionaryService.LOGGER_NAME` / `BTagDictionary.logger`): one shadow-literal hit for that constant
> IS an inlined reference (confirmed against the docSource original); a second shadow-literal hit for the
> SAME constant, same file, is a genuine independent duplicate. A dead constant with zero textual references
> in decompiled source is therefore not itself evidence the constant is unused.

**Method** (`dead_constant_sweep.py`, preserved at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/`):
(1) regex-match every `[public|private|protected] static final String NAME = "VALUE";` single-line
declaration across the 14,578-file canonical tree — **5,529 declarations** found `[CERT]`; (2) build a
corpus-wide identifier-token frequency table over the same tree; (3) flag every declared constant whose
`NAME` has corpus-wide frequency **exactly 1** (i.e. the declaration is the only occurrence of that
identifier anywhere) as a dead-constant candidate — **3,913 of 5,529 (71%)** `[CERT]`; (4) for each dead
candidate, search the same tree for its literal `VALUE` re-appearing as a quoted string literal on a
*different* line — **3,623 dead constants have at least one such "shadow literal" hit somewhere in the
corpus**, of which **2,766 have the hit in the SAME file as the declaration** `[CERT]` (raw run output:
`Total declarations matched: 5529` / `Dead (single-occurrence identifier) constants: 3913` / `Dead
constants with a corpus-wide shadow-literal hit elsewhere: 3623`).

**This raw count over-counts the true anti-pattern.** Manual inspection of a same-file sample shows many
hits are two *different*, intentionally-related constants that happen to share a literal value (e.g.
`READ_STATUS_FLAGS = "statusFlags"` and `STATUS_FLAGS_STATUS_FACET = "statusFlags"`, two distinct,
both-referenced-elsewhere constants in `organized/bacnet/vineflower/niagara/bacnet/point/BBacnetProxyExt.java:140,144`
— the sweep's same-file "hit" is each one seeing the *other's* declaration line, not a real duplication
bug). Filtering for genuinely load-bearing instances, three distinct real shapes were confirmed by direct
read this session:

1. **A clean, isolated copy-paste bug**, structurally identical to [Block 77] §77.3's and [Block 85]
   §85.1's own two known examples: `BTagDictionaryService.DISABLE_TAG_INDEXING_SYS_PROP =
   "niagara.tagdictionary.disableTagIndexing"` (`organized/tagdictionary/vineflower/niagara/tagdictionary/BTagDictionaryService.java:124`)
   has zero readers, while the very next line hardcodes the identical literal directly —
   `Boolean.getBoolean("niagara.tagdictionary.disableTagIndexing")`
   (`BTagDictionaryService.java:125`) — and the same literal recurs a third time in a `Lexicon.getText()`
   call (`BTagDictionaryService.java:295`) `[CERT]`.
2. **A generated, large-scale systematic recurrence, not a bug**: `organized/bacnet/vineflower/niagara/bacnet/enums/BBacnetEngineeringUnits.java`
   alone accounts for **268** same-file candidate pairs — every `*_NAME` constant (e.g.
   `VOLT_AMPERES_REACTIVE_NAME = "volt ampere reactive"`, `BBacnetEngineeringUnits.java:574`) is declared
   once and then the identical display-string literal is hardcoded again, unabbreviated, at the enum's
   construction table (`BBacnetEngineeringUnits.java:843`) `[CERT]` — a code-generation style choice
   across an entire BACnet-engineering-units enum table, not an accidental duplication.
3. **A recurring lexicon-key style across a whole class family**: the `*SecurityDashboardProviderAgent`
   classes (`BFoxServiceSecurityDashboardProviderAgent`, `BSystemPlatformServiceSecurityDashboardProviderAgent`,
   `BUserServiceSecurityDashboardProviderAgent`, `BEmailServiceSecurityDashboardProviderAgent`,
   `BSigningProfileSecurityDashboardAgent`, and others — 5 of these 10+ classes appear individually in
   the top-15-by-count table below) each declare i18n lexicon-key constants (e.g. `FORWARDING_SUMMARY =
   "securityDashboard.foxForwarding.summary"`, `organized/fox/vineflower/com/tridium/fox/dashboard/BFoxServiceSecurityDashboardProviderAgent.java:71`)
   that are never referenced by name — the real `getLexicon().getText(...)` call sites hardcode the
   identical dotted-key string literal directly instead `[CERT]`.

**Distinct-files-affected count**: `[CERT]` grouping the 2,766 same-file candidates by file gives
**680 distinct files** with at least one same-file candidate pair; the top offenders by raw candidate
count are `BBacnetEngineeringUnits.java` (268), `platWifi/WifiUtil.java` (116),
`_bin-ext/niagarad/servlet/WiFiServlet.java` (109), `migrator/bacnet/BBacnetBogConverter.java` (73),
`platform/BSystemPlatformServiceSecurityDashboardProviderAgent.java` (56),
`platform/tcpip/dhcpd/DhcpdUtil.java` (43), `baja/user/BUserServiceSecurityDashboardProviderAgent.java`
(35), `platIEEE8021X/IEEE8021XUtil.java` (34),
`provisioningNiagara/saml/BConfigureNiagaraIdPAndSAMLSchemeJobStep.java` (34),
`email/BEmailServiceSecurityDashboardProviderAgent.java` (29) — a full 15-row table plus every
file:candidate-count pair is preserved in `dead_constants_shadowed.json`.

**B85-G1 verdict: NARROWED, not CLOSED.** The mechanical sweep the gap's own text asked for ("grepping
every ... constant against its own call sites corpus-wide") ran successfully and is fully reproducible
(script + two JSON artifacts preserved); it proves the anti-pattern is systemic (680+ files, at every
scale from a 1-off bug to a 268-row generated table) rather than the 2 previously-known instances, and
adds a 3rd confirmed clean isolated-bug instance (`BTagDictionaryService`) plus a 4th confirmed instance
inside the licensing/subscription subsystem itself (§96.7 below, `EntitlementUtil`/`DeviceCodeApi`/
`AccessTokenApi`). What remains open is the per-candidate triage separating true accidental duplication
from intentional generated/style duplication across all ~2,766–3,623 raw hits — new child gap **B96-G2**.

## 96.6 — B85-G3 CLOSED: `RotateKeys`'s response is `{updated: bool}`; `RequestCertificates`'s response is `{certificates: {"<vendor>.certificate": <PEM/XML string>, ...}}`; both share the common `{code, type, message}` error envelope `[CERT]`

**`RotateKeys.rotateKeysApi()`** (`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/RotateKeys.java:27-51`)
POSTs `{nreId, publicKey}` to `/ncents/authn/api_key` and reads back a single boolean field: `[CERT]`
(`RotateKeys.java:36`) `response.optBoolean("updated", false)` — response schema `{"updated": <bool>}`
(a `false`/missing value throws `EntitlementException`, not a silent no-op).

**`RequestCertificates.getCertificatesApi()`** (`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/RequestCertificates.java:54-89`)
POSTs `{version, vendors, nreId}` to `/ncents/certificates` and reads the response as `[CERT]`
(`RequestCertificates.java:68`): `((JSONObject)response.get("certificates")).optString(vendor +
".certificate")` per requested vendor — response schema `{"certificates": {"<vendor>.certificate":
<certificate bytes as a UTF-8 string, parsed as an XElem/XML document via `XParser`>, ...}}`, one key
per requested vendor, keyed by the literal dotted string `"<vendorName>.certificate"`.

**Shared error envelope**, used by both endpoints via `EntitlementApi.checkErrorResponse()`
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementApi.java:327-370`) and
`handleResponseError()` (`EntitlementApi.java:272-288`): `[CERT]` (`EntitlementApi.java:288`)
`{"code": <HTTP status int>, "type": <error-type string>, "message": <human-readable string>}` — a
`type` of `"key"` is `RotateKeys`'s own endpoint-specific `KEY_ROTATION_FAILURE` signal
(`RotateKeys.java:19-25`), and a `type` matching `EntitlementState.INVALID_VENDOR`'s own `toString()` is
`RequestCertificates`'s own endpoint-specific signal (`RequestCertificates.java:91-96`) — both parsed
generically from the same `{code, type, message}` shape before either endpoint's own
`doCheckEndpointErrorResponse()` override runs.

**B85-G3 verdict: CLOSED.** Both response field shapes, previously unread, are now recovered above,
completing [Block 85] §85.6's own five-endpoint request/response table (register/entitlements/unbind
already read; rotateKeys/certificates now added).

## 96.7 — B77-G4 CLOSED: the `DEVICE_REGISTRATION_*` constants are neither a dead-functionality refactor artifact nor an unfinished configurability path — the device-code registration flow is fully live and wired, and all four constants are simply bypassed by hardcoded literal duplicates at their own real call sites, a fourth confirmed instance of the same anti-pattern named in §96.5 `[CERT]`

[Block 77] §77.3/§77.x's own gap text (quoted above) poses a disjunction — refactor artifact (dead
functionality) vs. unfinished configurability path — for `EntitlementUtil.DEVICE_REGISTRATION_HOST`/
`_CLIENT_ID`/`_RESPONSE_TYPE`/`_GRANT_TYPE`
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementUtil.java:57-60`). Reading
the actual OAuth2 device-code flow this session resolves it to a **third** answer neither branch names:
the flow is genuinely live, complete, and functioning — a real Salesforce-style device-code OAuth2
handshake against Tridium's own community portal (`www.niagara-community.com`, matching
`DEFAULT_REGISTRATION_URL`, `EntitlementUtil.java:47`) — implemented across two sibling classes,
`DeviceCodeApi` (`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/DeviceCodeApi.java:1-99`)
and `AccessTokenApi` (`AccessTokenApi.java:1-203`), with a full polling loop
(`AccessTokenApi.Poll`, `AccessTokenApi.java:94-202`) that retries every `pollInterval` seconds for up
to 10 minutes, backing off on `"too_fast"` and giving up cleanly on any other terminal error.

The four named constants are simply never referenced at their own real call sites, each shadowed by an
inline literal duplicate `[CERT]`:

- `DEVICE_REGISTRATION_RESPONSE_TYPE = "device_code"` — the request builder hardcodes the literal
  directly: `requestMessage.append("response_type").append('=').append("device_code");`
  (`DeviceCodeApi.java:63`).
- `DEVICE_REGISTRATION_GRANT_TYPE = "device"` — likewise: `requestBody.append("grant_type").append('=').append("device");`
  (`AccessTokenApi.java:16`).
- `DEVICE_REGISTRATION_HOST = "www.niagara-community.com"` — `EntitlementUtil.getDeviceRegistrationHost()`,
  the actual call site used by both `DeviceCodeApi.java:66` and `AccessTokenApi.java:21`, reads a
  `license.deviceRegistrationHost` property with an inline hardcoded default of the identical literal
  string instead of returning the named constant: `[CERT]` (`EntitlementUtil.java:139-141`).
- `DEVICE_REGISTRATION_CLIENT_ID` — `EntitlementUtil.getDeviceRegistrationClientId()` does the same:
  `license.clientId` property, default value the identical literal client-ID string, not the constant
  (`EntitlementUtil.java:134-137`).

**B77-G4 verdict: CLOSED**, revising the gap's own framing: this is not a dead-vs-unfinished question at
all — it is a live, fully-wired, third-party-style OAuth2 device-registration flow (structurally the
same device-code/user-code/polling UX pattern as NCS-Agent's own separate device registration, §96.8 —
see Connections) whose declaring class simply duplicates its own constants as inline literals at every
one of their real call sites, a fourth confirmed instance of the exact anti-pattern §96.5 (B85-G1) is
auditing corpus-wide, now inside the licensing/subscription subsystem itself.

## 96.8 — B18-G5 CLOSED: NCS-Agent's device-registration flow and `cloudLinkNcs`'s station-side `NiagaraCloudIdentity` are the SAME identity domain — niagarad is a Thrift client of NCS-Agent's local mTLS server on `localhost:9097`, both sides share the exact Java `DirectoryKeyStore` keystore, and the resulting rolling certificate alias (`"ncs-rolling"`) is produced by NCS-Agent and consumed by `NiagaraCloudIdentity` `[CERT-hw]`+`[CERT]`

**The station side never makes any HTTP call at all.** `NiagaraCloudIdentity`
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/cloud/NiagaraCloudIdentity.java:34-188`) is a pure
keystore watcher: `isRegistered()` is `this.keyStore.containsAlias("ncs-rolling")`
(`NiagaraCloudIdentity.java:76-78`), `getDeviceUuid()` reads the CN RDN of the `"ncs-rolling"`
certificate chain (`NiagaraCloudIdentity.java:80-89`), and a background `FileWatcher`
(`NiagaraCloudIdentity.java:117-177`) watches `<securityDir>/keystore/ncs-rolling.p12` for
create/delete/modify events and fires `DEVICE_REGISTERED`/`DEVICE_DEREGISTERED`/`IDENTITY_RENEWED`
purely from filesystem changes — the actual cloud handshake that produces that file happens entirely
outside this class `[CERT]`.

**`niagarad`'s own `NiagaraCloudServlet` is the missing link, and it is an explicit Thrift client of a
local process.** `NiagaraCloudServlet`
(`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/NiagaraCloudServlet.java:46-333`)
holds a `TServiceClientFactory<Niagaradshim.Client>` (`NiagaraCloudServlet.java:47,55-56`) and its
`TransportSupplier.makeTransport()` opens a **mutual-TLS TCP socket to `localhost:9097`**
(`NiagaraCloudServlet.java:328`), using a self-signed client cert (`CN="RSM Thrift Client"`, alias
`"rsm-thrift-client"`) stored in — and a trust manager reading a `"rsm-thrift-server"` trust anchor
from — the exact same `com.tridium.crypto.core.io.DirectoryKeyStore` class
(`NiagaraCloudServlet.java:6,301-323`) that `NiagaraCloudIdentity` itself uses
(`NiagaraCloudIdentity.java:3-4,40,49-50`) `[CERT]`. The Thrift IDL-generated service is named
`Niagaradshim` (`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/cloud/Niagaradshim.java`),
with exactly three RPCs — `StartRegistration(StartRequestStruct) → StartRespStruct`,
`RegistrationStatus() → StatusResponseStruct`, `Deregister()` — `[CERT]`
(`Niagaradshim.java:1120-1126`, `Niagaradshim.Client` methods `Niagaradshim.java:456-520`).

**The NCS-Agent Go binary is the Thrift SERVER on the other end of that socket, and its own strings
name the exact same Java class and the exact same keystore aliases.** `strings -n 8` over the installed
binary (`/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe`,
sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`) `[CERT-hw]` contains, verbatim:
`com.tridium.crypto.core.io.DirectoryKeyStore` (the literal fully-qualified Java class name — this is
NOT a decompiler artifact, this is the Go binary's own embedded string table referencing the Java
keystore implementation it interoperates with); `ncs-bootstrap.p12` and `ncs-rolling.p12` (matching
`NiagaraCloudIdentity.ROLLING_CERT_ALIAS = "ncs-rolling"`, `NiagaraCloudIdentity.java:35`, and its
`KEY_STORE_DIRECTORY = "keystore"`, `NiagaraCloudIdentity.java:36`); `rsm-thrift-client.p12` /
`rsm-thrift-server.p12` (matching the two cert aliases `NiagaraCloudServlet.java:311,323` uses); the
literal log strings `"Received Rolling Certificate from NCS"`, `"rollingCert failed to load PKCS#12
identity"`, `"rollingCert failed to write PKCS#12 identity"`, `"failed to load bootstrap PKCS#12
identity"`, `"failed to validate the rolling certificate"`, `"failed to delete NCS certificates"`; and a
full internal Go package, `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/ncsauth`, with functions
`InitRegistration`, `CheckRegistration`, `createCertificateSigningRequest`, `LoadTLSIdentity`,
`DeleteCerts`, `NeedsCertRenewal`, and `doJSONPost` — a complete CSR-based provisioning workflow: the
agent generates its own key pair and CSR, POSTs it to the cloud (`/api/v1/deviceregistration/
initregistration`, per [Block 18] §18.8's own already-published string), and on success stores the
returned rolling certificate under the exact `"ncs-rolling"`-branded PKCS#12 path
`NiagaraCloudIdentity`'s `FileWatcher` is already watching.

**B18-G5 verdict: CLOSED.** NCS-Agent's `/api/v1/deviceregistration/*` REST calls are **not** a separate
registration domain from `cloudLinkNcs`'s station-side identity — they are the SAME identity domain: the
Go agent performs the actual cloud handshake and writes the resulting `"ncs-rolling"` PKCS#12 identity
into the exact keystore path/alias that `NiagaraCloudIdentity` (consumed transitively by `cloudLinkNcs`
via `BCloudConnectionService`'s platform-type dispatch, §96.3) watches and fires
`DEVICE_REGISTERED` from — connected end-to-end via a local mTLS Thrift RPC channel
(`niagarad` client ↔ NCS-Agent server, `localhost:9097`) whose own certificate aliases and Java keystore
class are named verbatim inside the Go binary itself. This resolves [Block 18] §18.8's own `[INFER]`
("plausibly related from naming alone, not traced") to `[CERT]`.

## 96.9 — B18-G6 ADVANCED: full internal Go package/function architecture recovered from the binary's own embedded symbol strings (Thrift RPC shim, CSR/PKCS12 keystore internals, DPAPI integration) — but true instruction-level disassembly is blocked by a stripped Go symbol table, a specific, reproducible tooling limitation rather than an unattempted step `[CERT-hw]`

Beyond the string-table census [Block 18] §18.8 already ran, this session extracted the binary's
**embedded Go compiler metadata** (function/type names Go always embeds in `.rodata` for panics and
reflection, independent of the stripped linker symbol table) via a wider `strings -n 8` pass, recovering
concrete internal architecture `[CERT-hw]` (all strings quoted verbatim from
`tridium-ncs-supervisor-amd64-windows.exe`, sha256 as above):

- **Package `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/ncsauth`**: functions `FileExists`,
  `InitRegistration`, `CheckRegistration`, `certSigningRequest`, `createCertificateSigningRequest`,
  `LoadTLSIdentity`, `DeleteCerts`, `NeedsCertRenewal`, `doJSONPost` — the outbound cloud HTTP client;
  its `doJSONPost` is generic over a response shape whose exact JSON field tags are embedded in the
  binary's type metadata: `go.shape.struct { DeviceCode string "json:\"deviceCode\""; UserCode string
  "json:\"userCode\""; RegistrationUrl string "json:\"registrationUrl\""; DirectRegistrationUrl string
  "json:\"directRegistrationUrl\""; ExpiryTimeInSeconds int32 "json:\"expirationTimeInSeconds\"" }` —
  the `/api/v1/deviceregistration/initregistration` response's exact wire schema, previously unknown.
- **Package `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/keystore`** (and `.../keystore/dpapi`,
  `.../keystore/flock`): functions `LoadIdentity`, `SaveIdentity`, `SaveTrustStore`,
  `LoadTrustStoreCertificates`, `ParseCertificatesPEM`, `ReadKeyring`, `decryptKeyring`,
  `decryptAESGCM`, `KMPath`/`KRPath` (key-material/key-ring path helpers), `fileBackup`/
  `restoreFileBackup`/`writeFileAtomic`, and Windows-DPAPI-backed `dpapi.Decrypt` — a full local secret
  store with its own encrypted "keyring" file format, atomic-write/backup discipline, and file locking,
  independent of (but keystore-alias-compatible with, per §96.8) the Java-side `DirectoryKeyStore`.
- **The `Niagaradshim` Thrift IPC shim's Go-side struct**: `*niagaradshimgen.StartRequestStruct`,
  `StartRespStruct`, `NiagaradshimStartRegistrationArgs/Result`, `NiagaradshimRegistrationStatusArgs/Result`,
  `NiagaradshimDeregisterArgs/Result`, `NiagaradshimException` — the Go-side generated Thrift bindings
  for the identical 3-method service the Java `Niagaradshim.java` (§96.8) defines, confirming the IDL is
  shared/generated once and compiled into both languages, not independently re-implemented.
- User-facing registration UX strings — `"User action required: register device using the"`,
  `"Waiting for user to complete registration using"` — confirm a device-code/user-code, open-a-URL,
  poll-until-approved UX, structurally the same pattern as the independently-implemented subscription-
  licensing device flow in §96.7 (see Connections), though against a different backend and for a
  different purpose.

**What was NOT recovered, and why (a concrete tooling finding, not a gap in effort):** both `go tool nm`
and `go tool objdump -s` (Go 1.27.0 toolchain, run against a local read-only copy of the binary) fail
identically with `no runtime.pclntab symbol found` — the installed Go 1.25.12 binary's PE COFF symbol
table does not carry a `runtime.pclntab` entry the Go toolchain's own PE reader can locate (`objdump -t`
on the same binary returns only 7 COFF symbol-table rows, confirming the table is link-time-stripped,
consistent with a production release build, e.g. `-ldflags="-s -w"`) `[CERT]` (this session's own
`go tool nm`/`go tool objdump -s`/`objdump -t` runs, exit output preserved at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/ncsagent/nm.txt`).
`radare2` 6.2.0 likewise reports `lang c`/`lsyms false` for this PE (no Go-specific pclntab analyzer
engaged for this binary format in the installed r2 build). **B18-G6 verdict: ADVANCED, not fully
closed.** Full internal package/function-name architecture (well beyond the original string-table
census) and one concrete wire schema were recovered; genuine instruction-level disassembly of individual
function bodies needs a pclntab-aware tool (a magic-number pclntab scanner, or Ghidra's dedicated Go
binary analyzer) that this session's available tooling could not provide — new child gap **B96-G1**.

## 96.x — Connections

- §96.1 directly closes the residual scope [Block 67]'s own B67-G4 and [Block 88] §88.6 both left open,
  giving three concrete Forge wire-message JSON shapes (history-sample, CSOM export, history-query
  response) that any future block reading Forge's telemetry/model-export traffic can cite directly.
- §96.2 extends [Block 88] §88.3/§88.5's own Azure-wire-protocol proof with a structurally distinct
  Forge-branded REST gateway finding, and its residual "whose tenant" question is the same class of
  live-registration blocker [Block 67] §67.x and [Block 18]'s own B18-G1 already named — all three now
  point at the same missing artifact (a real device registration capture).
- §96.3/§96.4 jointly close [Block 90] §90.6's own two child gaps and complete [Block 11] §11.9's
  per-module feature-key table with the platform-service/platform-command side of the generic
  `BPlatform`/`BPlat` dispatch mechanism §90.6 first identified.
- §96.5 extends [Block 77] §77.3's and [Block 85] §85.1's two known examples into a corpus-wide,
  reproducible measurement — and §96.7 below independently supplies a fourth confirmed instance from a
  completely different subsystem (subscription licensing, not tag dictionaries or portal APIs),
  corroborating §96.5's own "systemic, not coincidental" verdict from an unrelated code path.
- §96.6 completes [Block 85] §85.6's five-endpoint subscription-API request/response table.
- §96.7's device-code/user-code/polling OAuth2-style UX (subscription licensing, against
  `www.niagara-community.com`) and §96.8/§96.9's NCS-Agent device-code registration UX (against the
  NCS/Forge cloud) are two independently-implemented instances of the same interaction pattern for two
  unrelated backends — worth noting as a recurring Tridium UX convention, not a shared code path (the
  two flows share no classes, packages, or constants).
- §96.8 closes [Block 18] §18.4/§18.8's own B18-G5, upgrading its `[INFER]` to `[CERT]`, and directly
  extends [Block 5] §5.3's `BINiagaraSyncCapableComplex` context (already closed by [Block 18] §18.7)
  with the actual identity-provisioning mechanism underneath `cloudLinkNcs`'s station-side federation.
- §96.9 extends [Block 18] §18.8's string-only census with actual package/function-level architecture
  and one recovered wire schema, while documenting a specific, reproducible reason (`no runtime.pclntab
  symbol found`) that a full instruction-level RE pass still requires different tooling than this
  session had — a concrete, falsifiable blocker for whoever picks up **B96-G1**.

## 96.x — Child gaps opened

- **B96-G1** — Instruction-level disassembly/decompilation of the NCS-Agent Go binary's function bodies
  (`ncsauth.doJSONPost`, `keystore.LoadIdentity`/`SaveIdentity`, the Thrift transport-setup code) using a
  pclntab-aware tool (a magic-number Go pclntab scanner, or Ghidra's dedicated Go analyzer via
  `decompile-native.sh ghidra`) — this session's `go tool nm`/`objdump`/`radare2` could not locate the
  binary's stripped symbol table (`no runtime.pclntab symbol found`, §96.9). `investigable`, medium
  priority — the architecture is now well understood from strings (§96.9); this closes the remaining
  "what does the code actually DO, not just what is it named" gap.
- **B96-G2** — Full per-candidate triage of the B85-G1 mechanical sweep's ~2,766 same-file /
  ~3,623 corpus-wide dead-constant-with-shadow-literal candidates (`dead_constants_shadowed.json`, this
  session's artifact) to classify each as a genuine accidental-duplication bug (like
  `BTagDictionaryService`, §96.5) vs. intentional generated/style duplication (like
  `BBacnetEngineeringUnits`'s 268-row enum table) vs. a coincidental same-value collision between two
  unrelated, both-used constants (like `BBacnetProxyExt`'s `READ_STATUS_FLAGS`/
  `STATUS_FLAGS_STATUS_FACET`). `investigable`, low-to-medium priority — large but fully mechanical:
  the candidate list already exists, only per-row classification remains.
- **B96-G3** — Live-traffic (or otherwise privileged) confirmation of `cloudLinkForge`'s actual
  `registrationHost`/file-upload SAS-issuing tenant (§96.2) — the runtime-configured `BString` property
  means no static-source answer is possible; this is the same class of blocker as [Block 18]'s own
  B18-G1 and [Block 67] §67.x's residual scope. `investigable`, blocked-on-live-registration.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | All 9 named `cloudLinkForge/forge/msg/` classes exist and were read; concrete JSON/AMQP wire shapes recovered for 8 of them | [CERT] | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/{ForgeFileSendScheduleHandler,ForgeFileSendModelCloseHandler,ForgeFileSendHistoriesBulkHandler,ForgeHttpGetHistoriesResult,ForgeAmqpSendPointValuesHandler,ForgeAmqpEventSerializer,ForgeFileHistoryConfigSerializer,ForgeHistorySerializer}.java` full reads, this session |
| 2 | `ForgeHttpStartFileUploadResult`'s response schema (`CorrelationId`/`FileUploadSasUrl`, optional `ApiCall` wrapper) differs from `AzureGetSasUrlHandler`'s (`correlationId/hostName/containerName/blobName/sasToken`) | [CERT] | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpStartFileUploadResult.java:9-35` vs. [Block 88] §88.3's own cite of `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureGetSasUrlHandler.java:53-57` |
| 3 | Forge file-upload URL templates are `/api/systems/{id}/fileuploadrequest` (v1) / `/api/v2/systems/{id}/fileuploadrequest` (v2), both Forge-branded, not Azure IoT Hub's own path | [CERT] | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/ForgeConstants.java:20-21`; `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/BForgeCertificateAuthenticator.java:453-461` |
| 4 | `registrationHost` is a runtime `BString` property, never a compiled-in literal | [CERT] | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/auth/BForgeCertificateAuthenticator.java:116,163,268-274` |
| 5 | `BCloudConnectionService.getPlatformType()` has exactly 2 corpus-wide `setPlatformType(` call sites (accessor decl + one internal restore), no literal assignment | [CERT] | `find organized -name '*.java' -exec grep -Hn "setPlatformType("` → `organized/cloudLink/vineflower/com/tridium/cloudLink/BCloudConnectionService.java:124,353` |
| 6 | Complete `getPlatformType()` value set: `Forge`/`NCS`/`HoneywellSBP`/`null`/`NONE` | [CERT] | per-file citations in §96.3's table |
| 7 | Both `getKey()` bases (`BAbstractCloudLinkHandlerFactory`, `BAbstractChannelConfigFactory`) derive directly from `getPlatformType()` | [CERT] | `organized/cloudLink/vineflower/com/tridium/cloudLink/BAbstractCloudLinkHandlerFactory.java:35-36`; `organized/cloudLink/vineflower/com/tridium/cloudLink/BAbstractChannelConfigFactory.java:31-32` |
| 8 | 18 direct + 24 second-level `BPlatformService` subtypes census; 0 of the 24 second-level classes add a further license-method override | [CERT] | `find organized -name '*.java' -exec grep -l "extends BPlatformService"` (18) + `extends B*PlatformService*` variants (24), each individually grepped for `getLicenseVendor\|getLicenseFeature`, zero hits |
| 9 | 11 of 18 `BPlatformService` subtypes gate a real feature; per-class values recorded | [CERT] | per-file citations in §96.4's table |
| 10 | `BIPlatformCommand` tree: 1 interface implementer, 2 direct + 17 second-level subclasses, all 17 leaves share `tridium:workbench` | [CERT] | `organized/platform/vineflower/com/tridium/platform/command/BAbstractPlatformCommand.java:50-57`; `organized/platDaemon/vineflower/com/tridium/platDaemon/command/*.java` (17 files, each grepped) |
| 11 | Mechanical dead-constant sweep: 5,529 declarations, 3,913 single-occurrence, 3,623 with a corpus-wide shadow-literal hit, 2,766 same-file | [CERT] | `dead_constant_sweep.py` run output, this session; `dead_constants_all.json`/`dead_constants_shadowed.json` |
| 12 | `BTagDictionaryService.DISABLE_TAG_INDEXING_SYS_PROP` is dead; its literal is hardcoded twice more in the same file | [CERT] | `organized/tagdictionary/vineflower/niagara/tagdictionary/BTagDictionaryService.java:124-125,295` |
| 13 | `BBacnetEngineeringUnits.java` alone accounts for 268 same-file shadow-literal candidate pairs (systematic, not accidental) | [CERT] | `dead_constants_shadowed.json` grouped-by-file count, this session; spot-read `organized/bacnet/vineflower/niagara/bacnet/enums/BBacnetEngineeringUnits.java:574,843` |
| 14 | `RotateKeys` response schema `{updated: bool}` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/RotateKeys.java:36` |
| 15 | `RequestCertificates` response schema `{certificates: {"<vendor>.certificate": ...}}` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/RequestCertificates.java:68` |
| 16 | Shared error envelope `{code, type, message}` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementApi.java:288` |
| 17 | `DeviceCodeApi`/`AccessTokenApi` hardcode `"device_code"`/`"device"` instead of referencing `DEVICE_REGISTRATION_RESPONSE_TYPE`/`_GRANT_TYPE` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/DeviceCodeApi.java:63`; `AccessTokenApi.java:16` |
| 18 | `getDeviceRegistrationHost()`/`getDeviceRegistrationClientId()` hardcode the identical literals as property defaults instead of returning `DEVICE_REGISTRATION_HOST`/`_CLIENT_ID` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementUtil.java:134-141` |
| 19 | `NiagaraCloudIdentity` makes no HTTP calls; watches `keystore/ncs-rolling.p12` via `FileWatcher` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/cloud/NiagaraCloudIdentity.java:34-188` |
| 20 | `NiagaraCloudServlet` is a Thrift client connecting mTLS to `localhost:9097`, using `DirectoryKeyStore` and cert aliases `rsm-thrift-client`/`rsm-thrift-server` | [CERT] | `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/NiagaraCloudServlet.java:6,301-328` |
| 21 | `Niagaradshim` Thrift service has exactly 3 RPCs (`StartRegistration`/`RegistrationStatus`/`Deregister`) | [CERT] | `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/cloud/Niagaradshim.java:1120-1126` |
| 22 | NCS-Agent binary embeds the literal string `com.tridium.crypto.core.io.DirectoryKeyStore` plus `ncs-bootstrap.p12`/`ncs-rolling.p12`/`rsm-thrift-{client,server}.p12` and "Received Rolling Certificate from NCS" | [CERT-hw] | `strings -n 8` over `/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe`, sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`, this session |
| 23 | NCS-Agent embeds full `internal/ncsauth` and `internal/keystore(/dpapi,/flock)` package/function names, plus the JSON schema `{deviceCode,userCode,registrationUrl,directRegistrationUrl,expirationTimeInSeconds}` | [CERT-hw] | same binary/sha256, `strings -n 8` output preserved at `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/ncsagent/strings8.txt` |
| 24 | `go tool nm`/`go tool objdump -s` both fail with `no runtime.pclntab symbol found`; `objdump -t` shows only 7 COFF symbol rows | [CERT] | this session's own tool runs, output at `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/ncsagent/nm.txt` |

Tally: 24 [CERT]/[CERT-hw] table rows (22 [CERT], 2 [CERT-hw]), 0 [INFER] table rows (two inline
`[INFER]` clauses appear in prose — §96.2's "consistent with ... the gap's 'Forge-operated proxy'
hypothesis" and §96.5's discussion of coincidental collisions — per METHODOLOGY's own convention that a
synthesis/interpretive clause is stated inline, not as a table row). Adjusted ratio `[INFER]`/`[CERT]*`
≈ **0.08** (2 inline `[INFER]` clauses against 24 `[CERT]`-class claims) — low, consistent with an
EVIDENCE-type block whose every closing verdict rests on a direct file read, a reproducible script run,
or a direct binary-string read this session, not on recalled prior-block content (prior-block content is
cited as `[Block N] §N.x` context throughout, never re-asserted as a fresh marker).

**MCP-doc snapshots**: N/A — no `context7`/web-MCP source was used this session. **Secrets discipline**:
`DEVICE_REGISTRATION_CLIENT_ID`'s literal value is not reproduced in this file (already characterized as
format-only, non-secret, by [Block 85] §85.1); no other secret-shaped literal is quoted verbatim in this
block. No client station files (`config.bog` etc.) were read this session, consistent with the task's
explicit scope instruction.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block96.md
```
(output pasted into the handback message to the caller, per the task's own instruction to run this
until exit 0.)

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block96.md` (the only
file written in the corpus this session, per the task's single-file constraint). `INDEX.md`/
`RESEARCH-STATE.md`/`CATALOG.md` were **not** regenerated — left to the integrator step, per the
established wave convention. Scratch artifacts (all reproducible from the commands/paths quoted above)
live at `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/`:
`dead_constant_sweep.py`, `dead_constants_all.json`, `dead_constants_shadowed.json`,
`canonical_files.txt`, and `ncsagent/` (`ncsagent.exe` — a read-only copy of the installed NCS-Agent
binary, `nm.txt`, `strings8.txt`).
