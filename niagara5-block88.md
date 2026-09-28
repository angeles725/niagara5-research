# Block 88 — `MessageWrapper` retry-count gate, the Forge/Azure Blob upload backend, the cloudLink version-lag explained, and the nCloudDriver→cloudLink lineage statement

> Research closing six named child gaps against the `cloudLink` family and its N4 module-inventory
> siblings: **B67-G2** (`MessageWrapper.canRetry()` — [Block 67] §67.1 named this the family's REAL
> retry-selectivity mechanism but did not read it, since `retriableError()` turned out to be nearly a
> no-op); **B67-G3** (whether Honeywell Forge's reuse of `cloudLinkAzure`'s SAS-URL file-upload handlers
> implies an Azure-OWNED backend or merely a coincidentally-shared client-side primitive); **B67-G4**
> (the ~30 remaining unread `cloudLinkForge` `forge/msg/` classes — [Block 67] §67.3 traced only the two
> factories' dispatch wiring, not the handler/serializer bodies); **B67-G5** (which file declares
> `BINiagaraNetworkHelper` — the interface `BNiagaraNetworkHelper` implements, named but not traced in
> [Block 67] §67.5); **B13-G2** (why the 7-module `cloudLink*` family is stamped `vendorVersion="5.0.0.26"`
> while all 240 other N5 5.0.0.28 modules read `5.0.0.28`); and **B42-G4** (an authoritative statement on
> N4 `nCloudDriver`'s retirement/successor relationship to `cloudLink` — [Block 42] §42.8 reached only an
> `[INFER]` verdict from a local migrator-catalog absence check). Covers: `MessageWrapper.java`'s whole
> body plus every corpus-wide `new MessageWrapper(...)` call site (28, all channels/commands/file-upload);
> `BINiagaraNetworkHelper.java`'s declaring file and its one implementation's full body;
> `AzureGetSasUrlHandler`/`AzureUpdateFileUploadStatusHandler`/`AzureFileUploadInfo`/
> `AzureBlobFileUploader`/`AzureBlobOutputStream` (the whole Azure file-upload chain) plus
> `ForgeHttpStartFileUploadHandler`/`ForgeHttpStartFileUploadResult`/`ForgeHttpEndFileUploadHandler` (the
> parallel Forge-native chain feeding the SAME writer); a structural (class/interface-declaration-line)
> census of all 47 previously-unopened `cloudLinkForge/forge/msg/` files; a live `unzip -p`+`stat`
> forensic read of `buildMillis`/`buildHost`/`releaseDate` across the 7 `cloudLink*` jars vs. 11 other
> 5.0.0.28-stamped modules; and one authorized external source — a genuine, dated Tridium "Niagara Cloud
> Service Guide" PDF (N4-era, publicly mirrored) fetched and full-text-extracted this session. Does
> **not** cover: full method-body reads of the ~9 largest still-unopened Forge `msg/` classes (200+ lines
> each — see child gap); a live capture of an actual Azure Blob/IoT-Hub hostname from a real Forge tenant
> (still requires a live registration, per [Block 67] §67.x's own residual scope); or a second external
> source explicitly stating "`nCloudDriver` is removed/unsupported in N5" by name (the one external
> document found states a design-lineage relationship, not an N5-specific removal notice — see verdict
> in §88.5).
>
> Subject version: **N5 5.0.0.28 (Beta)**, deployed modules cache
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules`, decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{cloudLink,cloudLinkAzure,cloudLinkForge,
> cloudLinkExtensionNiagara}/vineflower/` — the same install and decompile trees [Block 18]/[Block 42]/
> [Block 67] read. One external source used this session, outside the local corpus, per the caller's
> explicit authorization for **B42-G4** only: a Tridium "Niagara Cloud Service Guide" PDF, dated
> **January 8, 2025**, "niagara4"-branded on its cover, fetched from
> `https://downloads.onesight.solutions/Tridium/Niagara%204%20Documents/docNcs.pdf` (a third-party
> Niagara-integrator public downloads mirror — **not** `tridium.com` itself; the PDF's own "Legal Notice"
> page marks its contents "confidential information of Tridium, Inc." for "Tridium employees, licensees,
> and system owners," yet it is reachable at this public URL without authentication — a provenance
> caveat recorded here, not silently smoothed over) — accessed this session via `WebFetch`, saved to
> local disk, and full-text-extracted with `pdftotext -layout` (`/home/linuxbrew/.linuxbrew/bin/pdftotext`)
> for exact-quote grepping, since `WebFetch`'s own HTML-conversion path could not render the binary PDF.
>
> Sources: `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/MessageWrapper.java` (whole
> file, 63 lines) · a corpus-wide `grep -rn "new MessageWrapper"` over every `organized/cloudLink*/
> vineflower/` tree (28 call sites, this session) · `organized/cloudLink/vineflower/com/tridium/
> cloudLink/extension/BINiagaraNetworkHelper.java` (whole file) and `organized/cloudLinkExtensionNiagara/
> vineflower/com/tridium/cloudLink/extension/niagara/BNiagaraNetworkHelper.java` (whole file, 110 lines)
> · `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/{AzureGetSasUrlHandler,
> AzureUpdateFileUploadStatusHandler}.java` (whole files) · `organized/cloudLinkAzure/vineflower/com/
> tridium/cloudLink/azure/file/{AzureFileUploadInfo,AzureIotUploader,AzureBlobFileUploader,
> AzureBlobOutputStream}.java` (whole files) · `organized/cloudLinkForge/vineflower/com/tridium/
> cloudLink/forge/msg/{ForgeHttpStartFileUploadHandler,ForgeHttpStartFileUploadResult,
> ForgeHttpEndFileUploadHandler}.java` (whole files) · a structural (`grep -m1` class/interface-
> declaration-line + `wc -l`) census of the remaining 47 `organized/cloudLinkForge/vineflower/com/
> tridium/cloudLink/forge/msg/*.java` files not opened by [Block 67] · live `unzip -p <jar>
> META-INF/module.xml` + `unzip -p <jar> META-INF/MANIFEST.MF` + `stat` of all 7 `cloudLink*.jar` plus
> `baja.jar`/`alarm.jar`/`bacnet.jar`/`kitControl.jar`/`niagaraDriver.jar`/`history.jar`/`platform.jar`/
> `gx.jar`/`workbench.jar`/`schedule.jar`/`webChart.jar` from
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/` (this session, fresh) · a `python3`
> `buildMillis`→UTC-timestamp conversion script (this session, scratch, not archived) · `WebSearch` (3
> queries, this session) and `WebFetch` (2 URLs, this session) for **B42-G4** only · the Tridium "Niagara
> Cloud Service Guide" PDF, `pdftotext -layout`'d in full (5,533 lines), grepped for
> `ncloud|sentience|iot hub|azure|aws|google` and read at the matched line ranges.
>
> Method: full `Read` of every cited `.java` file · corpus-wide `grep -rn` for call-site census
> (`new MessageWrapper`, confirmed 28/28 pass an explicit retry count) · live `unzip -p`/`stat` forensic
> comparison of jar build metadata (not reused from any prior block — [Block 13] §13.5 named the
> `vendorVersion` anomaly but did not open `buildMillis`/`buildHost`) · one authorized external fetch
> chain (`WebSearch` → `WebFetch` → local-disk PDF → `pdftotext` → `grep`) for the one gap (B42-G4)
> explicitly scoped to allow it. Markers (canonical list, METHODOLOGY §3): `[CERT-hw]`/`[CERT-live]`
> highest · `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official shipped document ·
> `[CERT-web]` official/authoritative web source, fetched and quoted this session, URL+date given ·
> `[CERT-a]` secondary source · `[INFER]` deduction. Decompiled-tree citations are given in full
> `organized/...` path form, following [Block 61]'s/[Block 67]'s/[Block 80]'s convention for
> `verify-block.sh` resolvability.
>
> RT/transport + cloud-history layer. Deepens [Block 67] (closes B67-G2, B67-G3, B67-G5; advances
> B67-G4), [Block 13] (closes B13-G2), and [Block 42] (advances B42-G4). Connects [Block 18] (the
> extension-point-chassis framing) and [Block 44] (the `finalize()`/`ForgeAmqpHandler` lineage,
> re-confirmed by this block's structural census).
>
> **Type:** `mixed` — five sections are direct fresh primary-source evidence (§88.1–§88.4, §88.6); §88.5
> draws a moderate-strength `[INFER]` conclusion from one directly-fetched-and-quoted `[CERT-web]`
> external document rather than from this session's own decompiled-source reads alone.

---

## 88.1 — B67-G2 CLOSED: `canRetry()` is a plain atomic decrement-and-check gate — and the class's own hardcoded `DEFAULT_RETRY_COUNT = 3` is dead code, because every one of the 28 production call sites overrides it with the operator-configurable `messageRetries` property instead `[CERT]`

The full method, read this session:

```java
private static final int DEFAULT_RETRY_COUNT = 3;
...
public boolean canRetry() {
   boolean retry = this.retryCounter.decrementAndGet() >= 0;
   if (retry) {
      this.transportFuture = new CompletableFuture<>();
   }
   return retry;
}
```
`[CERT]` `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/MessageWrapper.java:13,55-62`
(whole file, this session). `retryCounter` is an `AtomicInteger` seeded once, at construction, from
whichever `numRetries` value the caller passes (`:12,32`) — `canRetry()` decrements it and returns `true`
iff the **post-decrement** value is `>= 0`. For a seed of N, this permits exactly N+1 total send attempts
(1 original send + N retries): e.g. seed 2 → attempts at retryCounter 2→1 (retry allowed), 1→0 (retry
allowed), 0→-1 (final failure, no more retries) — 3 total sends. On every allowed retry, `canRetry()`
also **replaces `transportFuture` with a fresh `CompletableFuture`** (`:58`) — decoupling the retried
send's own completion signal from the original (now presumably failed/timed-out) transport-level future;
`messageFuture` (the higher-level, channel-consumer-visible future returned to callers) is left untouched
by this reset, so a caller awaiting the message's overall outcome sees one logical future across all
retry attempts, while the transport layer gets a fresh per-attempt one.

**The class's own `DEFAULT_RETRY_COUNT = 3` constant is never actually reached by production code.**
`MessageWrapper` has four constructors: two convenience overloads that hardcode `numRetries` to the
literal `3` (`:15-17,19-21`), and two explicit-count overloads that take `numRetries` as a caller-supplied
parameter (`:23-25,27-33`). A corpus-wide `grep -rn "new MessageWrapper"` over every `organized/cloudLink*/
vineflower/` tree (this session) returns **28 instantiation sites**, spanning every channel type
(`BPointChannel`, `BAlarmChannel`×3, `BHeartbeatChannel`, `BCommandChannel`, `BModelChannel`,
`BHistoryChannel`×3, `BEventChannel`, `BScheduleChannel`, `BMessageChannel`, `BAbstractModelChannelConfig`
×2), the generic `FileUploader`×2, the Azure block-upload writer (`AzureBlobOutputStream`×2), and every
Forge command class (`BForgeReadPointCommand`, `BForgeWritePointCommand`,
`BForgeReadMultiPointCommand`, `BForgeWriteMultiPointCommand`, `BForgeAckAlarmCommand`,
`BForgeCommandContainer`×3) `[CERT]`. **Every single one of the 28 passes `transport.getMessageRetries()`
explicitly as the third constructor argument** `[CERT]` (confirmed by direct inspection of each matched
line and its surrounding 1-2 lines this session — zero call sites use the 1-arg or 2-arg convenience
constructors that would fall back to the hardcoded `3`). Since `getMessageRetries()` resolves to the
`messageRetries` `@NiagaraProperty` [Block 67] §67.2 already characterized (default **2**, max facet
**10**, `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BAbstractTransport.java:57-61,
85-86`), **the real, operative retry count for every cloudLink message in this corpus is the
operator-configurable `messageRetries` property (2 by default), never the class-internal literal `3`** —
closing B67-G2: `canRetry()`'s "logic" is intentionally trivial (a bare countdown), and its
selectivity comes entirely from what value the CALLER seeds it with, which in 100% of this corpus's
wiring is the transport's own configured retry-count property, confirming and sharpening [Block 67]
§67.1's framing that "the message-level retry mechanism's actual selectivity comes almost entirely from
`MessageWrapper.canRetry()` (the retry-COUNT gate)... rather than from `retriableError()`'s error-TYPE
gate" — the count gate is not merely simple, its own class-level default is provably unreachable.

## 88.2 — B67-G5 CLOSED: `BINiagaraNetworkHelper` is declared inside `cloudLink` itself, not `cloudLinkExtensionNiagara` — a base-chassis interface with exactly one implementation, and that implementation provisions real N5 station-to-station Fox-over-websocket connections `[CERT]`

`BINiagaraNetworkHelper` is declared at `[CERT]`
`organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BINiagaraNetworkHelper.java:12` — inside
the **base `cloudLink` module**, package
`com.tridium.cloudLink.extension`, alongside the 6-role Helper SPI [Block 67] §67.5 already documented
(`BDeviceInfoHelper`, `BHistoryImportHelper`, etc.). It is a **7th, narrower extension-point interface**,
not one of those 6, and not declared inside `cloudLinkExtensionNiagara` as [Block 67] §67.5 left open:

```java
public interface BINiagaraNetworkHelper extends BInterface {
   void configureNiagaraNetwork(Map<String, NiagaraRemoteConnectionState> var1, String var2,
                                  BICertificateCredentials var3, IAuditLog var4);
}
```
`[CERT]` (whole file, 17 lines). Its **sole implementation**, `cloudLinkExtensionNiagara`'s
`BNiagaraNetworkHelper` (`organized/cloudLinkExtensionNiagara/vineflower/com/tridium/cloudLink/extension/
niagara/BNiagaraNetworkHelper.java:28`), is a real, non-trivial method body (read in full this session,
110 lines) that provisions/updates/removes `BNiagaraRemoteStation` devices under the station's
`niagaraNetwork` service in response to a cloud-driven `ENABLE`/`DISABLE`/`DELETE` command per remote
device ID `[CERT]`. For `ENABLE`, it constructs a `BFoxClientConnection` hardcoded to **port 4911**,
`useFoxs(true)`, `FoxOverWebsocket = useWebsocketOnly`, websocket port **443**, and a path prefix of
`"/api/v1/proxy/" + deviceId` — i.e. this is the concrete mechanism behind [Block 67] §67.5's "Niagara's
device concept needs component-tree-level integration": the cloud platform can remotely command a
station to open (or tear down) a Fox-over-websocket connection to another Niagara station, reachable
through a `/api/v1/proxy/<deviceId>` path, with the credentials and audit-log hook supplied by the
caller `[CERT]`. This closes B67-G5: the interface lives in the base chassis (making it a formally
declared, if narrow, 7th SPI role cloudLink defines for itself), and its one implementation is a genuine
network-provisioning operation, not a stub.

## 88.3 — B67-G3 CLOSED: Forge's file-upload backend genuinely speaks Azure Blob Storage's proprietary REST wire protocol — this is not a coincidentally-shared client primitive, and the generic upload path additionally matches Azure IoT Hub's own File-Upload API response schema field-for-field `[CERT]`

[Block 67] §67.3 found that `BForgeHttpHandlerFactory` registers `cloudLinkAzure`'s own
`AzureGetSasUrlHandler`/`AzureUpdateFileUploadStatusHandler` for its generic `IStartFileUploadHandler`/
`IEndFileUploadHandler` slots, and asked whether this proves an Azure-owned backend or is merely a
convenient shared client-side pattern. Reading the full chain this session settles it, with two
independent lines of evidence:

**(a) The generic upload path's response schema is Azure IoT Hub's own, field-for-field.**
`AzureGetSasUrlHandler.toMessage()` POSTs to
`https://{connectionInfo.hostName}/devices/{connectionInfo.id}/files?api-version=2020-03-13` `[CERT]`
`organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureGetSasUrlHandler.java:53-57` —
this is Azure IoT Hub's documented device File-Upload REST path shape (`/devices/{deviceId}/files`), and
`connectionInfo.hostName`/`.id` are populated from the device's own IoT Hub connection info (hostName +
deviceId, the standard Azure IoT Hub device-identity pair). The response is parsed by
`AzureFileUploadInfo`, whose constructor reads **exactly five** JSON fields — `correlationId`, `hostName`,
`containerName`, `blobName`, `sasToken` — `[CERT]`
`organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/file/AzureFileUploadInfo.java:12-16` —
which is Azure IoT Hub's own
"Create File Upload SAS URI" response schema (the same five field names), not a Forge- or
Tridium-invented shape. `getUrl()` then builds `https://{hostName}/{containerName}/{blobName}{sasToken}`
(`:18`) — note this response `hostName` is a **different** value from the REQUEST hostname (the IoT Hub
host): it is the Blob Storage account host IoT Hub hands back, confirming the actual object store is a
separate, linked Azure Storage Account, reached via a SAS URL IoT Hub itself issues.

**(b) The actual byte-upload writer speaks Azure Blob Storage's proprietary REST protocol, not a generic
HTTP PUT.** `AzureBlobOutputStream` (used by BOTH the generic `AzureGetSasUrlHandler` path AND, via
`ForgeFileUploader extends AzureBlobFileUploader`, Forge's OWN native schedule-export handshake) issues
`PUT ...?comp=block&blockid=<id>` requests carrying header **`x-ms-version: 2021-08-06`** and
**`x-ms-content-crc64`**, then finalizes with `PUT ...?comp=blocklist` carrying an
`<?xml version="1.0"?><BlockList><Latest>...</Latest></BlockList>` body `[CERT]`
`organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/file/AzureBlobOutputStream.java:
157-179,207-231` (whole file read, 231 lines) — the `x-ms-*` header family and the `comp=block`/
`comp=blocklist`/`<BlockList>` XML commit body are Azure Storage's own proprietary "Put Block"/"Put Block
List" REST operations, a wire protocol that is not a generic S3-style or vendor-neutral upload API.
**Whatever endpoint answers this PUT sequence must itself implement Azure's proprietary Blob Storage REST
protocol** — an operationally implausible thing for a third party to reimplement wholesale rather than
simply using genuine Azure Blob Storage.

**Forge's schedule-export path (the THIRD, factory-bypassing path [Block 67] §67.3 found) reuses this
SAME writer with its OWN, differently-shaped handshake** — `ForgeHttpStartFileUploadHandler` POSTs to a
Forge-supplied `uploadUrlTemplate` host (not an `azure-devices.net`-shaped IoT-Hub host) and
`ForgeHttpStartFileUploadResult` parses a Forge-specific `{"CorrelationId":..., "ApiCall":
{"FileUploadSasUrl":...}}` (or flat `{"CorrelationId":...,"FileUploadSasUrl":...}`) schema `[CERT]`
`organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpStartFileUploadResult.java:
16-21` — an opaque, Forge-owned SAS-issuing handshake, distinct from IoT Hub's own schema in (a) — but
whatever URL it returns is STILL fed into the same `AzureBlobOutputStream`, so it too must resolve to a
genuine Azure-Blob-protocol-speaking endpoint, regardless of which service issued the SAS token.

**Net verdict, closing B67-G3**: this is **not** a merely-coincidental shared client-side primitive —
the wire protocol itself (`x-ms-version`, block/blocklist commit) is Azure-Storage-specific, and the
generic upload path's response schema is provably Azure IoT Hub's own (not reinvented by Forge). One
externally-sourced corroboration, read this session for a different gap (§88.5) but directly relevant
here: the Tridium "Niagara Cloud Service Guide" states **"Niagara Cloud Suite is a collection of
user-facing (and some non-user-facing) web applications, running within the **Tridium-provided Azure
cloud space**"** `[CERT-web]` (`docNcs.pdf`, Glossary, p.125 — see §88.5's citation for the full
provenance/URL/date) — confirming the product family's cloud backend is genuinely hosted on Azure, not
merely protocol-compatible with it. Forge's own tenant (Honeywell-operated rather than
Tridium-Niagara-Cloud-Suite-operated) is not directly confirmed by this same sentence, but the wire-level
evidence in (a)/(b) applies identically to Forge's reused Azure handlers.

## 88.4 — B13-G2 CLOSED: the `cloudLink*` family's `vendorVersion="5.0.0.26"` is neither a stale leftover jar nor an unexplained build anomaly — it is a 4-year-old, independently-versioned N4 add-on module family (documented "Niagara Cloud Service," formerly "CloudLink," initial release **May 11, 2021**) that is compiled fresh for every platform beta in its OWN CI job, on its OWN version-numbering track `[CERT]`+`[CERT-web]`

Two independent lines of evidence converge on the same answer.

**(a) Forensic: the jars are freshly compiled, same day as the rest of 5.0.0.28, in a separate build job.**
Live `unzip -p`+`stat` this session (not reused from [Block 13]'s vendor/dependency census, which read
`vendorVersion` but not `buildMillis`/`buildHost`) of all 7 `cloudLink*.jar` plus 11 other 5.0.0.28-stamped
modules from `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`:

| Module | `vendorVersion` | `buildHost` | `buildMillis` → UTC | `releaseDate` |
|---|---|---|---|---|
| `baja` | 5.0.0.28 | `aceb72ec905d` | 2026-09-11 21:08:13 | 2026-03-11 |
| `alarm` | 5.0.0.28 | `aceb72ec905d` | 2026-09-11 21:12:59 | 2026-03-11 |
| `bacnet`/`kitControl`/`niagaraDriver`/`history`/`platform`/`gx`/`workbench`/`schedule`/`webChart` | 5.0.0.28 | `aceb72ec905d` (all 9) | 2026-09-11 21:11–22:34 | 2026-03-11 |
| `cloudLink` | **5.0.0.26** | **`81d038d602c5`** | 2026-09-11 **22:21:13** | 2026-03-11 |
| `cloudLinkAzure`/`Forge`/`HonSbp`/`Ncs`/`ExtensionBacnet`/`ExtensionEbi`/`ExtensionNiagara` | **5.0.0.26** (all 7) | **`81d038d602c5`** (all 7) | 2026-09-11 22:21:29–22:21:43 | 2026-03-11 |

`[CERT]` (`unzip -p`, this session, from the live mounted install; `buildMillis`→UTC conversion via a
`python3` one-liner this session). **All 18 modules — cloudLink family included — carry the identical
`releaseDate="2026-03-11"`** (a fixed release-branch stamp shared platform-wide, not a per-module signal)
and were **all built on the same calendar day, 2026-09-11**, with the cloudLink family's 7 builds landing
in a tight **30-second window** (22:21:13–22:21:43), roughly **69–73 minutes after** the `baja`/`alarm`
builds (21:08–21:13) — i.e. these are NOT stale jars carried over from an old beta; they were freshly
compiled as part of this exact 5.0.0.28 beta's build pipeline. What IS distinct: every one of the 9
sampled non-cloudLink modules (including `baja`/`alarm`) shares `buildHost="aceb72ec905d"`, while **all 7
cloudLink-family modules share a different `buildHost="81d038d602c5"`** — a separate CI worker/container
from the rest of the platform build `[CERT]`. This is the direct forensic signature of "cloudLink family
built in its own separate build job, packaged into the same day's beta assembly" — not "an old artifact
nobody rebuilt."

**(b) Documentary: cloudLink is a real, independently-released N4 add-on with its own multi-year release
history, predating N5 by over 4 years.** The Tridium "Niagara Cloud Service Guide" (see §88.5 for full
citation) — a genuine, dated document, "niagara4"-branded — states in its own "Document change log"
`[CERT-web]`:

> "May 11, 2021 — Initial release document." ... "August 26, 2024 — Update - Renaming: The product name
> 'Niagara Cloud Service' is replacing 'CloudLink'." ... "October 23, 2023 — Added 'Niagara Remote' topic
> and 'cloudLink-NiagaraRemoteTransport' component (**available with Niagara 4.10u7 and Niagara 4.13**)."

— and its "Requirements" chapter states plainly: **"All systems must be running Niagara 4.10 or later"**
`[CERT-web]` (`docNcs.pdf`, p.9). This confirms `cloudLink`/"Niagara Cloud Service" has shipped as a
distinct, independently-versioned Tridium add-on module across MULTIPLE N4 minor releases
(4.10u7 through at least 4.13, and by extension whatever N4 baseline preceded this N5 beta) since **May
2021** — nearly 4 years before this January 2025 documentation snapshot, and well over 5 years before
this September 2026 N5 5.0.0.28 beta. A module family with its own multi-year release cadence, developed
and versioned independently of the core platform's `bajaVersion`/`vendorVersion` counter, is exactly what
would produce a 2-patch-level version lag when bundled into a platform beta whose OWN version counter has
moved on — **closing B13-G2**: this is not a stale-build artifact (the buildMillis timestamps rule that
out) and not an unexplainable anomaly — it is the expected fingerprint of `cloudLink` being an
independently-released, independently-versioned product line (its own separate CI job, confirmed in (a);
its own multi-year release history under a different original product name, confirmed in (b)) that
Tridium packages into each platform beta rather than folding into the platform's own version-bump
cadence.

## 88.5 — B42-G4 ADVANCED (not fully closed): a genuine, dated Tridium document states `cloudLink`/"Niagara Cloud Service" was designed as a successor informed by "lessons learned from" the N4 Honeywell Sentience driver (`nCloudDriver`'s underlying product) — but no source found this session states outright that `nCloudDriver` itself is removed/unsupported in N5 `[CERT-web]`/`[INFER]`

[Block 42] §42.8 reached an `[INFER]` verdict — "N4's `nCloudDriver` was retired without a migration path"
— purely from a LOCAL absence check (no matching module, no matching migrator-converter class). This
session was explicitly authorized to use `WebSearch`/`WebFetch` for this one gap; both tools connected
successfully (confirmed: `WebSearch` returned live, dated results; `WebFetch` retrieved a live PDF).

**Two `WebSearch` queries surfaced no Tridium/Honeywell document that names N5 and `nCloudDriver`'s
removal in the same breath** `[CERT-web — negative result, both queries executed and returned unrelated
hits]`: `"nCloudDriver" Niagara` and `Niagara nCloudDriver removed N5 migration Tridium` returned only
general N5-breaking-changes commentary (Java 21 migration, module resignation requirements) and one
Honeywell-hosted document snippet describing `nCloudDriver`'s N4 role ("provides device registration and
a secure connection to the Honeywell Sentience cloud platform... intended for use with Niagara Cloud
Honeywell Sentience Driver and Cloud-BackupService") — this is a search-engine-generated summary of a
Honeywell release-notes PDF, not independently fetched and quoted this session, so it is recorded here as
corroboration only, not elevated to `[CERT-web]`.

**A third search led to a genuine, directly-fetched, dated Tridium document that DOES state a
lineage/successor relationship.** `WebFetch` retrieved
`https://downloads.onesight.solutions/Tridium/Niagara%204%20Documents/docNcs.pdf` — the "Niagara Cloud
Service Guide," dated **January 8, 2025**, "niagara4"-branded, marked internally "confidential
information of Tridium, Inc." on its own Legal Notice page (found at this public third-party mirror
without authentication — provenance caveat as stated in the header). `WebFetch`'s own text-extraction
could not render the binary PDF stream, so this session downloaded it to local disk (via the tool's own
save-path) and ran `pdftotext -layout` to get a clean, greppable 5,533-line text export — the "Chapter 6.
Tuning" section's opening paragraph reads, verbatim:

> **"Niagara Cloud Service was designed with lessons learned from Niagara Cloud Honeywell Sentience
> Driver, and with greater knowledge of the capabilities and limitations of the cloud platforms to which
> it might connect."**

`[CERT-web]` (`docNcs.pdf`, Chapter 6 "Tuning," "Tuning Considerations," p.114 — accessed and
`pdftotext`-extracted this session, 2026-09-27). "Niagara Cloud Honeywell Sentience Driver" is the
document's own name for the product `nCloudDriver` implements (matching this corpus's own `com.tridium.
nc.*` package naming and `BCloudSentienceDevice` type, per [Block 42] §42.8's citation of `niagara-research`
B83 §83.5) — this is a first-party Tridium statement that its cloud-connectivity module (what this N5
beta ships as `cloudLink`) is a **deliberate redesign informed by** the older Sentience-driver product,
not a renamed/ported continuation of it. The same document's network-allowlist chapter additionally lists
`*.azure-devices.net` (Azure IoT Hub's own DNS suffix) among the domains a cloudLink-using station must
reach `[CERT-web]` (p.14) and states elsewhere that a station becomes "connected to the IoT Hub (the
cloud)" upon registration (`[CERT-web]`, p.19) — both directly corroborating §88.3's independent
source-code finding that the backend is genuinely Azure IoT Hub, not merely IoT-Hub-protocol-shaped.

**Verdict: ADVANCED, not CLOSED.** This raises [Block 42] §42.8's conclusion from a purely local,
absence-based `[INFER]` to one partially grounded in a genuine, dated, first-party Tridium statement —
but that statement describes a DESIGN lineage ("lessons learned from"), not an explicit N5-specific
removal/retirement notice ("`nCloudDriver` is not available/supported in Niagara 5"). No source found
this session states the latter outright. **B42-G4 stays open, narrowed**: an explicit N5 release note or
migration-guide sentence naming `nCloudDriver`'s N5 status was not located (would require either a
newer, N5-specific Tridium migration document not yet public/indexed as of this session, or a direct
Tridium support-portal search this session's tools cannot reach).

## 88.6 — B67-G4 ADVANCED: a full structural census (class/interface declaration line) of all 47 previously-unopened `cloudLinkForge/forge/msg/` files — confirms the 3-tier `ForgeAmqpHandler` subclass lineage extends one level deeper than [Block 67] measured, and narrows the remaining gap to ~9 substantial handler/serializer bodies `[CERT]`

[Block 67] §67.3/§67.4 traced the two factories' dispatch wiring and the 13 `finalize()` sites, but left
~30 `forge/msg/` classes unread beyond the import census — named **B67-G4**. This session reads every
remaining file's class/interface declaration line (`grep -m1` + `wc -l`, all 47 files, this session):

**Every AMQP command/query handler extends `ForgeAmqpHandler` directly** — `ForgeAmqpAckAlarmCommandHandler`,
`ForgeAmqpCommandResponseHandler`, `ForgeAmqpGetLastTimestampsHandler`, `ForgeAmqpMultiPointReadCommandHandler`,
`ForgeAmqpMultiPointWriteCommandHandler`, `ForgeAmqpPointReadCommandHandler`, `ForgeAmqpPointWriteCommandHandler`,
`ForgeAmqpRegisterCommandsHandler`, `ForgeAmqpSendEventHandler`, `ForgeAmqpSendHeartbeatHandler`,
`ForgeAmqpSendHistoriesHandler`, `ForgeAmqpSendPointValuesHandler`, `ForgeAmqpSendSystemInfoHandler` (13
classes) `[CERT]` — consistent with [Block 67] §67.4's corpus-wide `extends ForgeAmqpHandler` count of 14
(the 14th being `ForgeAmqpAlarmHandler` itself, one tier up — see next finding).

**A previously-unnoted 3rd tier**: `ForgeAmqpSendAlarmHandler` and `ForgeAmqpSendBatchAlarmHandler`
extend **`ForgeAmqpAlarmHandler`** (not `ForgeAmqpHandler` directly) `[CERT]` — and `ForgeAmqpAlarmHandler`
itself extends `ForgeAmqpHandler` (confirmed already read as [Block 67] §67.4's inheriting-subclass
sample, `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeAmqpAlarmHandler.java:23`).
This makes the empty-`finalize()` lineage from [Block 67] §67.4
three levels deep for these 2 classes (`ForgeAmqpHandler` → `ForgeAmqpAlarmHandler` → `{SendAlarmHandler,
SendBatchAlarmHandler}`), not the flat one-level "abstract base + 14 direct subclasses" picture §67.4
described — a refinement, not a contradiction (§67.4's 14-count is unaffected, since these 2 classes
still transitively inherit the empty override).

**Interface layering confirmed for the remaining `IForge*` types**: every `IForge<Verb>CommandHandler`
extends BOTH a generic cloudLink interface (`I<Verb>CommandHandler`, [Block 67] §67.3's dispatch-table
column) AND the empty marker `IForgeCommandHandler` `[CERT]` (`IForgeAckAlarmCommandHandler`,
`IForgeCommandResponseHandler`, `IForgeMultiPointReadCommandHandler`, `IForgeMultiPointWriteCommandHandler`,
`IForgePointReadCommandHandler`, `IForgePointWriteCommandHandler` — all 6 read, 6-7 lines each) — a clean
Forge-specific tagging pattern layered onto §67.3's generic dispatch interfaces, not a parallel type
hierarchy.

**Remaining unread material narrows to ~9 substantial bodies** (200+ decompiled lines each, none opened
this session beyond their declaration line): `ForgeFileSendScheduleHandler` (320 ln, `implements
ISendScheduleHandler`), `ForgeFileSendModelCloseHandler` (298 ln, `implements ISendModelCloseHandler`),
`ForgeFileSendHistoriesBulkHandler` (234 ln, `implements ISendBulkHistoriesHandler`),
`ForgeHttpGetHistoriesResult` (225 ln), `ForgeMsgConstants` (188 ln, a constants-only class — low
investigative value), `ForgeAmqpSendPointValuesHandler` (130 ln), `ForgeAmqpEventSerializer` (132 ln,
`implements IEventSerializer<BEvent>`), `ForgeFileHistoryConfigSerializer` (122 ln), `ForgeHistorySerializer`
(120 ln, no interface — a plain utility class). The remaining ~36 files are small (6-105 lines) result/
request/serializer classes whose declaration lines are now fully censused `[CERT]` (full table in
self-verify below). This **advances but does not close** B67-G4 — a payload/serialization-logic read of
the 9 substantial classes above is opened fresh as **B88-G1**.

## 88.x — Connections

- **[Block 67]** — direct parent for 4 of 6 gaps: §88.1 closes **B67-G2**, §88.2 closes **B67-G5**, §88.3
  closes **B67-G3**, §88.6 advances **B67-G4**. None of this block's findings contradict [Block 67]'s own
  `[CERT]` claims; every section extends a read [Block 67] explicitly stopped short of.
- **[Block 13]** — §88.4 closes **B13-G2**, [Block 13] §13.5's named-but-unexplained `vendorVersion`
  anomaly, using a forensic method (`buildMillis`/`buildHost`) [Block 13] itself did not apply.
- **[Block 42]** — §88.5 advances (narrows, does not close) **B42-G4**, upgrading [Block 42] §42.8's
  purely-local `[INFER]` with one directly-fetched, dated, first-party Tridium document.
- **[Block 44]**/**[Block 67] §67.4** — §88.6's 3-tier `ForgeAmqpHandler` lineage finding refines (does
  not contradict) the empty-`finalize()`-inheritance picture both blocks already established.
- **[Block 18]** — §88.2's `BNiagaraNetworkHelper` full read is the concrete Fox-over-websocket mechanism
  behind [Block 18] §18.2's/[Block 67] §67.5's generic "extension-point chassis" framing.

## 88.x — Child gaps opened

- **B88-G1** — Full payload/serialization-logic body reads of the 9 substantial, still-unopened
  `cloudLinkForge/forge/msg/` classes named in §88.6 (`ForgeFileSendScheduleHandler`,
  `ForgeFileSendModelCloseHandler`, `ForgeFileSendHistoriesBulkHandler`, `ForgeHttpGetHistoriesResult`,
  `ForgeAmqpSendPointValuesHandler`, `ForgeAmqpEventSerializer`, `ForgeFileHistoryConfigSerializer`,
  `ForgeHistorySerializer`; `ForgeMsgConstants` is a constants dump, low priority). `investigable`,
  medium priority — narrows [Block 67]'s original B67-G4 to a bounded, small file set.
- **B88-G2** — Whether an N5-specific Tridium migration guide or release note exists (not yet public or
  not indexed by this session's `WebSearch`) that states `nCloudDriver`'s status in Niagara 5 explicitly,
  rather than the design-lineage statement found in §88.5's N4-era document. `investigable`,
  blocked-on-external-source (would need either a later Tridium N5 GA migration doc or direct portal
  access this session's tools cannot reach) — the direct residue of B42-G4 staying open.
- **B88-G3** — Whether `cloudLinkForge`'s Honeywell-Forge-branded tenant (as opposed to Tridium's own
  Niagara Cloud Suite tenant, confirmed Azure-hosted by §88.3/§88.5) is itself an Azure IoT Hub tenant
  under Honeywell's own Azure subscription, or a Forge-operated proxy in front of one — the wire-protocol
  evidence in §88.3 proves the STORAGE side is genuine Azure Blob, but Forge's own
  `ForgeHttpStartFileUploadHandler`/`Result` handshake (distinct schema from IoT Hub's) leaves the
  SAS-issuing side's tenancy unconfirmed. `investigable`, would require a live Forge tenant capture
  (same live-registration blocker as [Block 67] §67.x's residual scope).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `canRetry()` is `retryCounter.decrementAndGet() >= 0`, resets `transportFuture` on retry | [CERT] | `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/MessageWrapper.java:55-62` |
| 2 | `DEFAULT_RETRY_COUNT = 3` exists but is unreachable — all 28 call sites pass `transport.getMessageRetries()` | [CERT] | `grep -rn "new MessageWrapper"` → 28 hits, each inspected |
| 3 | `BINiagaraNetworkHelper` declared in `cloudLink`, not `cloudLinkExtensionNiagara` | [CERT] | `organized/cloudLink/vineflower/com/tridium/cloudLink/extension/BINiagaraNetworkHelper.java:12` |
| 4 | `BNiagaraNetworkHelper.configureNiagaraNetwork` provisions `BFoxClientConnection` port 4911/websocket 443, path `/api/v1/proxy/<id>` | [CERT] | `organized/cloudLinkExtensionNiagara/vineflower/com/tridium/cloudLink/extension/niagara/BNiagaraNetworkHelper.java:73-79` |
| 5 | `AzureGetSasUrlHandler` POSTs to IoT-Hub-shaped `/devices/{id}/files?api-version=2020-03-13`; response schema = `correlationId/hostName/containerName/blobName/sasToken` | [CERT] | `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/msg/AzureGetSasUrlHandler.java:53-57`; `organized/cloudLinkAzure/vineflower/com/tridium/cloudLink/azure/file/AzureFileUploadInfo.java:12-16` |
| 6 | `AzureBlobOutputStream` uses `x-ms-version: 2021-08-06`, `comp=block`/`comp=blocklist`, `<BlockList>` XML commit | [CERT] | `AzureBlobOutputStream.java:157-179,207-231` |
| 7 | Forge's native `ForgeHttpStartFileUploadHandler`/`Result` uses a different, Forge-owned schema (`CorrelationId`/`FileUploadSasUrl`) but feeds the same `AzureBlobOutputStream` writer | [CERT] | `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpStartFileUploadHandler.java`; `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeHttpStartFileUploadResult.java:16-21`; `organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/file/ForgeFileUploader.java` (`extends AzureBlobFileUploader`) |
| 8 | cloudLink family: 7/7 jars `vendorVersion=5.0.0.26`, `buildHost=81d038d602c5`, built 2026-09-11 22:21:13-43 | [CERT] | live `unzip -p module.xml`, this session |
| 9 | 11 sampled non-cloudLink 5.0.0.28 modules (incl. `baja`/`alarm`): `buildHost=aceb72ec905d`, built 2026-09-11 21:08-22:34 | [CERT] | live `unzip -p module.xml`, this session |
| 10 | Tridium "Niagara Cloud Service Guide": initial release 2021-05-11; product renamed from "CloudLink" 2024-08-26; `NiagaraRemoteTransport` "available with Niagara 4.10u7 and Niagara 4.13" (2023-10-23) | [CERT-web] | `docNcs.pdf` Document change log, p.7-8, fetched+`pdftotext`'d this session |
| 11 | "Niagara Cloud Service was designed with lessons learned from Niagara Cloud Honeywell Sentience Driver" | [CERT-web] | `docNcs.pdf` Ch.6 "Tuning Considerations," p.114 |
| 12 | `*.azure-devices.net` in the required domain allowlist; "connected to the IoT Hub (the cloud)" on registration; "Tridium-provided Azure cloud space" | [CERT-web] | `docNcs.pdf` p.14, p.19, p.125 (Glossary) |
| 13 | No source found this session states `nCloudDriver`'s N5-specific removal/status explicitly | [INFER] | 3 `WebSearch` queries + `docNcs.pdf` full-text — none found |
| 14 | 13 `ForgeAmqp*Handler` classes extend `ForgeAmqpHandler` directly; 2 (`SendAlarmHandler`/`SendBatchAlarmHandler`) extend `ForgeAmqpAlarmHandler` instead | [CERT] | `grep -m1` declaration lines, all 15 files, this session |
| 15 | 6 `IForge*CommandHandler` interfaces extend both a generic cloudLink interface and marker `IForgeCommandHandler` | [CERT] | declaration lines, 6 files, this session |

Tally: 13 [CERT]/[CERT-web], 1 [INFER] (raw claim count above, header-legend mentions excluded per
[Block 67]/[Block 80]'s adjusted-ratio convention) — ratio **[INFER]/[CERT\*] ≈ 0.08**, well under the
~0.5 exhaustion threshold, consistent with a session that opened entirely fresh source/forensic/external
evidence across 6 independent gaps. The one `[INFER]` is a **negative-result** claim (row 13 — nothing
found despite a genuine search), the correct marker for "searched, not located" per METHODOLOGY's
evidence-gap discipline, not a downgrade of an otherwise-positive finding. `[CERT-web]` rows (10-12) are
each backed by a directly fetched, `pdftotext`-extracted, dated document — not a search-snippet summary
(the one search-snippet-only Honeywell-doc mention in §88.5 is explicitly NOT promoted to `[CERT-web]`,
per the marker-discipline note in that section). No secrets, keys, tokens, or connection strings were
copied from any source — the Azure/Forge material above is header names, JSON field names, and URL path
shapes only, per this task's SECRETS constraint.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block88.md`. Per this
session's explicit read-only scope, `RESEARCH-STATE.md`/`INDEX.md`/`CATALOG.md` and no other block file
were touched, and no `git commit` was made. The fetched `docNcs.pdf` was saved by the `WebFetch` tool to
this session's own tool-results cache (not copied into the corpus); its `pdftotext` export was written to
this session's scratchpad directory only (not archived in the corpus), matching [Block 13]'s "scratch
scripts not preserved in the corpus" convention.
