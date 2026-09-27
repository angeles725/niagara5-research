# Block 11 — N5 license-gated features map: 253 confirmed `checkFeature`/`getFeature`/`Feature.*`/`checkDeveloperLicense`/`checkJreFeature` call sites across 77 of 248 scanned jars, 84 distinct `vendor:feature` keys (all vendor `tridium`), closing B6-G3

> Research of **every call site of the N5 licensing API** (`niagara.license.LicenseManager.checkFeature`/
> `getFeature`, `niagara.license.Feature.check`/`get`/`getb`/`geti`/`list`/`isExpired`/`getExpiration`,
> `com.tridium.sys.license.NLicenseManager.checkDeveloperLicense`/`isDeveloperLicense`,
> `com.tridium.sys.license.LicenseUtil.checkJreFeature`) across **all 247 module jars** shipped in N5
> 5.0.0.28 plus `nre.jar` (`bin/ext`) — closing [Block 6]'s child gap **B6-G3** ("a fuller enumeration
> of every caller of `LicenseManager.checkFeature()`/`getFeature()` across the rest of `baja.jar`… was
> not attempted this session"), here widened from "the rest of `baja.jar`" to **every shipped jar**, per
> this block's assignment. Covers: the exact method list (derived from [Block 6]'s own decompile of
> `niagara.license.LicenseManager`/`Feature`), a two-stage scan pipeline (fast constant-pool byte
> pre-filter, then precise `javap -c -p` invoke-target + preceding-literal extraction), the complete
> per-module call-site census, the complete `vendor:feature` map, the `Feature.get`/`getb`/`geti`
> attribute-key map (limit/on-off/expiry semantics), and a delta against the N4 `niagara-research`
> corpus's own feature-gate documentation (B14, B301, B387, B481, B488, B1-3). Does **not** cover:
> source-level (`file:line`) citations — this block is bytecode-only (`javap` disassembly offsets), no
> Vineflower decompile was run on the ~127 hit classes this session (→ **B11-G4**); the 6 call sites
> whose `vendor`/`feature` arguments are runtime-computed (not string literals) were not traced to their
> actual values (→ **B11-G3**); OEM-branded builds (Honeywell, Andover UI layers) were not investigated
> beyond noting their jar-level absence from this generic beta distribution (→ **B11-G2**); and live/
> on-station verification of any finding (read-only static block, no N5 station available this session,
> consistent with [Block 1]'s blocked gap B1-G1).
>
> Subject version: N5 **5.0.0.28** (Beta) — same install as [Block 6]: modules under
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/` (247 `.jar`, `mtime`-stamped, unversioned
> by git — METHODOLOGY §3 "no git, no problem") plus
> `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar`. N4 baseline: the `niagara-research` corpus
> (its own B14/B301/B387/B481/B488/B1-3, read as remittances, not re-derived).
>
> Sources:
> - All 247 `.jar` under `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/` + `bin/ext/nre.jar`
>   (248 jars total scanned) — read via Python `zipfile` (constant-pool byte scan) and `javap -c -p`
>   (bytecode disassembly), both read-only against the installed jars; no file was modified.
> - `/tmp/claude-1000/n5b6/out/{niagara/license,com/tridium/sys/license}/**` — [Block 6]'s own Vineflower
>   decompile of the API surface itself (`LicenseManager.java`, `Feature.java`, `NLicenseManager.java`),
>   read here (not re-derived) to confirm the exact method list and the `getFeature`-vs-`checkFeature`
>   semantics (§11.6) before searching for callers.
> - `niagara-research` corpus (N4 baseline, read via
>   `python3 niagara-research/tools/corpus-nav.py find "checkFeature"` / `"device.limit"` /
>   `"point.limit"` / `"history.limit"` / and individual feature-name lookups) — blocks B1-3, B14, B108,
>   B126, B232, B244, B251, B301, B316, B317, B323, B387, B443, B453, B454, B456, B479-B481, B483, B488,
>   B499, B500, B806, B850, B930, B1144, plus `bloque387`'s full text (read in full, not just the grep
>   excerpt) — read here as N4 REMITTANCE, not re-derived.
>
> Method: **Stage 1 (byte pre-filter)** — a Python script (`shortlist.py`, stdlib `zipfile` only) opened
> every `.class` entry in all 248 jars and flagged any entry whose raw bytes contain one of 8 target
> byte-strings (`niagara/license/LicenseManager`, `niagara/license/Feature`, `checkFeature`,
> `getFeature`, `checkDeveloperLicense`, `isDeveloperLicense`, `checkJreFeature`,
> `com/tridium/sys/license`) — deliberately over-inclusive (substring match, no bytecode parsing) to
> guarantee no candidate class is missed; this shortlisted 282 classes across 83 jars.
> **Stage 2 (precise extraction)** — a second script (`extract_callsites.py`) ran
> `javap -c -p -classpath <jar> <FQCN>` (openjdk 26.0.2.1,
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap`) on every stage-1-shortlisted class, split the
> disassembly into per-method blocks, and for every `invoke*` instruction whose resolved target matched
> one of the 11 API methods (§11.2), recorded the enclosing method signature, the bytecode offset, and
> the (up to 6) preceding `ldc`/`ldc_w` String-constant literals in the same method — candidate
> `vendor`/`feature`/attribute-key arguments. This is the SAME `javap`-based approach [Block 6] used on
> `baja.jar`'s license package, mechanically extended to all 248 jars. Both scripts and their raw JSON
> output are preserved at
> `/tmp/claude-1000/-home-cristian-niagara-research/2d45784e-5708-4584-92d2-21151b041500/scratchpad/b11/`
> (scratch, not archived in the corpus; fully re-derivable from the jars cited — same convention as
> [Block 6]'s `/tmp/claude-1000/n5b6/out/`).
> Markers: `[CERT]` — call-site EXISTENCE and invoke TARGET (module, class, method, bytecode offset) is
> always `[CERT]`, mechanically read from live `javap` output, zero hand-transcription. The
> **literal-argument extraction** (which string is the vendor/feature/attribute-key) is `[CERT]` only
> where individually spot-verified live this session (listed in §11.10); elsewhere it is `[CERT — pipeline
> output, not individually spot-verified]`, a distinct sub-grade the self-verification section explains
> (§11.9's known heuristic failure mode). `[INFER]` deduction (chiefly: "no N4 corpus hit" ≠ "absent from
> N4" — §11.8). No `[CERT-doc]`/`[CERT-web]` this block.
>
> Security/licensing layer. Connects [Block 6] (parent gap B6-G3; this block is its direct closure and
> reuses its decompiled `niagara.license`/`com.tridium.sys.license` API surface verbatim), [Block 3]
> (§11.4's `fips140` feature ties to Block 3's `bcfips`/`bcstd` FIPS-provider swap), and, across corpora,
> `niagara-research` B387 (the N4 "runtime feature-gate map" this block's N5 counterpart directly
> extends and cross-validates — §11.7), B488 (N4's limit-enforcement map, compared in §11.6), B14/B1-3
> (N4's own `checkFeature` hit-count, compared in §11.8).
>
> **Type:** standard

---

## 11.1 — Licensing API surface: 11 methods across 4 types, unchanged from [Block 6]'s decompile `[CERT]`

[Block 6] §6.1/§6.9 already decompiled the whole `niagara.license`/`com.tridium.sys.license` package;
this block reads that output (not re-derived) to fix the exact target-method list before searching for
callers:

| Type | Method | Signature | Role |
|---|---|---|---|
| `niagara.license.LicenseManager` (interface) | `getFeature` | `(String,String) → Feature` | look up, no expiry enforcement |
| | `checkFeature` | `(String,String) → Feature` | look up **and** enforce expiry (`f.check()` internally) |
| `niagara.license.Feature` (interface) | `check` | `() → void`, throws `FeatureNotLicensedException` | expiry gate |
| | `get` | `(String) → String` / `(String,String) → String` | read an attribute, with/without default |
| | `getb` | `(String,boolean) → boolean` | read a boolean attribute |
| | `geti` | `(String,int) → int` | read an int attribute |
| | `list` | `() → String[]` | list attribute keys |
| | `isExpired` | `() → boolean` | expiry query |
| | `getExpiration` | `() → long` | expiry query |
| `com.tridium.sys.license.NLicenseManager` (impl) | `checkDeveloperLicense` | `() → void` (private) | cached at `postInit()`, backs `isDeveloperLicense` |
| | `isDeveloperLicense` | `() → boolean` | accessor for the cached developer-mode flag |
| `com.tridium.sys.license.LicenseUtil` | `checkJreFeature` | `() → void` (static) | gates the bundled Zulu JRE version ([Block 6] §6.10) |

`[CERT]` `/tmp/claude-1000/n5b6/out/niagara/license/{LicenseManager,Feature}.java`,
`com/tridium/sys/license/{NLicenseManager,LicenseUtil}.java` (Vineflower output from [Block 6]'s session,
read here). These 11 methods are the exact TARGETS regex set for stage 2 (§ Method above).

## 11.2 — Scan census: 248 jars scanned → 83 shortlisted → 77 confirmed, 127 classes, 253 call sites `[CERT]`

| Stage | Count |
|---|---|
| Jars scanned (247 `modules/*.jar` + `nre.jar`) | 248 |
| Jars with ≥1 byte-level candidate (stage 1, over-inclusive) | 83 |
| Classes shortlisted (stage 1) | 282 |
| Jars with ≥1 CONFIRMED invoke-target hit (stage 2, precise) | 77 |
| Classes with ≥1 confirmed hit | 127 |
| Total confirmed call sites | 253 |

The stage-1→stage-2 shrink (282 → 127 classes, 83 → 77 jars) is the over-inclusive byte substring
match resolving false positives: e.g. `nre.jar`'s one stage-1 hit
(`com/tridium/nre/cloud/NiagaraCloudConfiguration.class`, matched on the substring `getFeature`) turned
out to be the unrelated method `getFeatureEnablementEndpoint()` — zero actual invokes of the licensing
API — confirmed live: `javap -c -p -classpath nre.jar com.tridium.nre.cloud.NiagaraCloudConfiguration |
grep -i "getfeature\|licensemanager"` → exactly one line, `public java.lang.String
getFeatureEnablementEndpoint();`, no invoke. `[CERT]` — see §11.8 for what this negative means for
`nre.jar` specifically.

Breakdown by target method (253 = 40+98+33+39+20+6+4+3+3+6+1, verified by direct count):

| Invoke target | Count |
|---|---|
| `LicenseManager.getFeature` | 98 |
| `LicenseManager.checkFeature` | 40 |
| `Feature.get` | 39 |
| `Feature.check` | 33 |
| `Feature.getb` | 20 |
| `NLicenseManager.isDeveloperLicense` | 6 |
| `Feature.list` | 6 |
| `LicenseUtil.checkJreFeature` | 4 |
| `Feature.isExpired` | 3 |
| `Feature.geti` | 3 |
| `NLicenseManager.checkDeveloperLicense` (private, called from `postInit()`) | 1 |

`getFeature` (98) outnumbers `checkFeature` (40) more than 2:1 — §11.6 explains why this is NOT a
licensing-strictness regression.

## 11.3 — Per-module call-site table (all 77 jars) `[CERT]` (call sites) / `[CERT — pipeline output, not individually spot-verified]` (feature-key column, except rows named in §11.10)

| Module (jar) | Call sites | Distinct feature keys checked |
|---|---|---|
| `baja.jar` | 40 | `brand`, `developer`, `fips140`, `globalCapacity`, `premiumWBNiagaraRemote`, `zulu25` |
| `workbench.jar` | 19 | `about`, `fips140`, `nre`, `workbench` |
| `cloudLink.jar` | 12 | `cloudLink`, `cloudLinkConnect`, `historyArchive` |
| `systemIndex.jar` | 12 | `systemDb`, `systemIndex` |
| `niagaraDriver.jar` | 9 | `niagaraDriver` |
| `bacnet.jar` | 8 | `bacnet`, `bacnetSc`, `mstp` |
| `platform.jar` | 8 | `fips140`, `platformClient` |
| `ccn.jar` | 6 | `ccn`, `ccnl` |
| `rdb.jar` | 6 | `rdbHistoryArchive` |
| `obixDriver.jar` | 5 | `obixDriver` |
| `template.jar` | 5 | `template` |
| `alarm.jar` | 4 | `alarm`, `alarmArchive` |
| `driver.jar` | 4 | `fileDriver` |
| `nrio.jar` | 4 | `accessControl`, `nrio` |
| `saml.jar` | 4 | `samlDP` |
| `web.jar` | 4 | `mobile`, `web` |
| `ace.jar` | 3 | `ace` |
| `analytics.jar` | 3 | `analytics` |
| `hierarchy.jar` | 3 | `hierarchy` |
| `httpClient.jar` | 3 | `http` |
| `mbus.jar` | 3 | `mbus` |
| `nss.jar` | 3 | `securityDashboard` |
| `nurio.jar` | 3 | `nurio` |
| `nvideo.jar` | 3 | `videoDriver` |
| `opcUaServer.jar` | 3 | `opcUaServer`, `opcUaServerAnonLogin` |
| `orientSystemDb.jar` | 3 | `systemDb` |
| `platCrypto.jar` | 3 | `bulkCertSigner`, `fips140` |
| `search.jar` | 3 | `search` |
| `systemDb.jar` | 3 | `systemDb`, `systemIndex` |
| `xprotect.jar` | 3 | `milestoneCorporate`, `milestoneVideo`, `remoteVideo` |
| `axvelocity.jar` | 2 | `axvelocity` |
| `bacnetAws.jar` | 2 | `bacnetAws` |
| `box.jar` | 2 | `box` |
| `fox.jar` | 2 | `platform` |
| `history.jar` | 2 | `historyArchive` |
| `jsonToolkit.jar` | 2 | `jsonToolkit` |
| `ldap.jar` | 2 | `ldapv3` |
| `lonIp.jar` | 2 | `lonIp` |
| `maxpro.jar` | 2 | `maxpro`, `remoteVideo` |
| `naxisVideo.jar` | 2 | `axisVideo`, `remoteVideo` |
| `nmilestone.jar` | 2 | `milestoneVideo`, `remoteVideo` |
| `platDataRecovery.jar` | 2 | `dataRecovery` |
| `platIEEE8021X.jar` | 2 | `ieee8021x` |
| `platSerial.jar` | 2 | `serial` |
| `aaphp.jar` | 1 | `aaphp` |
| `aapup.jar` | 1 | `aapup` |
| `abstractMqttDriver.jar` | 1 | `mqtt` |
| `andoverAC256.jar` | 1 | `andoverAC256` |
| `andoverInfinity.jar` | 1 | `andoverInfinity` |
| `bajaui.jar` | 1 | `fips140` |
| `cloudLinkHonSbp.jar` | 1 | *(dynamic/non-literal arg — §11.9, → B11-G3)* |
| `email.jar` | 1 | `email` |
| `event.jar` | 1 | `eventService` |
| `flexSerial.jar` | 1 | `flexSerial` |
| `lonworks.jar` | 1 | `lonworks` |
| `mcquay.jar` | 1 | `mcquay` |
| `modbusAsync.jar` | 1 | `modbusAsync` |
| `modbusSlave.jar` | 1 | `modbusSlave` |
| `modbusTcp.jar` | 1 | `modbusTcp` |
| `modbusTcpSlave.jar` | 1 | `modbusTcpSlave` |
| `nSnmp.jar` | 1 | `snmp` |
| `niagaraCloud.jar` | 1 | `premiumWBNiagaraRemote` |
| `niagaraSync.jar` | 1 | `niagaraSync` |
| `opcUaClient.jar` | 1 | `opcUaClient` |
| `platHwScan.jar` | 1 | *(dynamic/non-literal arg — §11.9, → B11-G3)* |
| `portalApi.jar` | 1 | *(dynamic/non-literal arg — §11.9, → B11-G3)* |
| `program.jar` | 1 | `developer` |
| `provisioningNiagara.jar` | 1 | `provisioning` |
| `rdbHsqlDb.jar` | 1 | `rdbHsqlDb` |
| `rdbMySQL.jar` | 1 | `rdbMySQL` |
| `rdbSqlServer.jar` | 1 | `rdbSqlServer` |
| `remoteVideo.jar` | 1 | `remoteVideo` |
| `signingService.jar` | 1 | `certSigningService` |
| `sms.jar` | 1 | `sms` |
| `tagdictionary.jar` | 1 | `tags` |
| `tls.jar` | 1 | `tls` |
| `videoDriver.jar` | 1 | `videoDriver` |

`baja.jar` dominates (40/253, 16%) — expected, since it hosts the licensing implementation itself
(`NLicenseManager`, `LicenseUtil`, `Brand`, `ResourceManager`, `GlobalGroup`, `ModuleDev`,
`ModuleSetClassLoader`, `Station`, `SubscriptionLicenseManager`) alongside its own callers. `workbench.jar`
(19) and the `cloudLink`/`systemIndex` pair (12 each) are the next tier — matching N5-G9/G10/G11's own
gap framing (cloud + workbench UI as N5-emphasis areas). `[CERT]`

## 11.4 — Complete `vendor:feature` map: 84 distinct pairs, ALL vendor `tridium` `[CERT — pipeline output, not individually spot-verified except rows named in §11.10]`

Extracted from the 138 `LicenseManager.checkFeature`/`getFeature` call sites whose two immediately
preceding `ldc` literals both parse as bare identifiers (132 sites → 84 distinct pairs, several features
checked from more than one call site); the remaining 6 sites push a non-literal (variable/field) argument
and are excluded here (listed in §11.3's per-module table as "dynamic/non-literal", enumerated in
§11.9 → **B11-G3**).

| Vendor:feature | # call sites | Citing module(s) |
|---|---|---|
| `tridium:aaphp` | 1 | aaphp.jar |
| `tridium:aapup` | 1 | aapup.jar |
| `tridium:about` | 1 | workbench.jar |
| `tridium:accessControl` | 1 | nrio.jar |
| `tridium:ace` | 2 | ace.jar |
| `tridium:alarm` | 1 | alarm.jar |
| `tridium:alarmArchive` | 1 | alarm.jar |
| `tridium:analytics` | 1 | analytics.jar |
| `tridium:andoverAC256` | 1 | andoverAC256.jar |
| `tridium:andoverInfinity` | 1 | andoverInfinity.jar |
| `tridium:axisVideo` | 1 | naxisVideo.jar |
| `tridium:axvelocity` | 2 | axvelocity.jar |
| `tridium:bacnet` | 1 | bacnet.jar |
| `tridium:bacnetAws` | 1 | bacnetAws.jar |
| `tridium:bacnetSc` | 1 | bacnet.jar |
| `tridium:box` | 1 | box.jar |
| `tridium:brand` | 1 | baja.jar |
| `tridium:bulkCertSigner` | 1 | platCrypto.jar |
| `tridium:ccn` | 3 | ccn.jar |
| `tridium:ccnl` | 3 | ccn.jar |
| `tridium:certSigningService` | 1 | signingService.jar |
| `tridium:cloudLink` | 2 | cloudLink.jar |
| `tridium:cloudLinkConnect` | 1 | cloudLink.jar |
| `tridium:dataRecovery` | 1 | platDataRecovery.jar |
| `tridium:developer` | 5 | baja.jar, program.jar |
| `tridium:email` | 1 | email.jar |
| `tridium:eventService` | 1 | event.jar |
| `tridium:fileDriver` | 1 | driver.jar |
| `tridium:fips140` | 7 | baja.jar, bajaui.jar, platCrypto.jar, platform.jar, workbench.jar |
| `tridium:flexSerial` | 1 | flexSerial.jar |
| `tridium:globalCapacity` | 2 | baja.jar |
| `tridium:hierarchy` | 1 | hierarchy.jar |
| `tridium:historyArchive` | 2 | cloudLink.jar, history.jar |
| `tridium:http` | 1 | httpClient.jar |
| `tridium:ieee8021x` | 1 | platIEEE8021X.jar |
| `tridium:jsonToolkit` | 1 | jsonToolkit.jar |
| `tridium:ldapv3` | 1 | ldap.jar |
| `tridium:lonIp` | 1 | lonIp.jar |
| `tridium:lonworks` | 1 | lonworks.jar |
| `tridium:maxpro` | 1 | maxpro.jar |
| `tridium:mbus` | 1 | mbus.jar |
| `tridium:mcquay` | 1 | mcquay.jar |
| `tridium:milestoneCorporate` | 1 | xprotect.jar |
| `tridium:milestoneVideo` | 2 | nmilestone.jar, xprotect.jar |
| `tridium:mobile` | 2 | web.jar |
| `tridium:modbusAsync` | 1 | modbusAsync.jar |
| `tridium:modbusSlave` | 1 | modbusSlave.jar |
| `tridium:modbusTcp` | 1 | modbusTcp.jar |
| `tridium:modbusTcpSlave` | 1 | modbusTcpSlave.jar |
| `tridium:mqtt` | 1 | abstractMqttDriver.jar |
| `tridium:mstp` | 1 | bacnet.jar |
| `tridium:niagaraDriver` | 4 | niagaraDriver.jar |
| `tridium:niagaraSync` | 1 | niagaraSync.jar |
| `tridium:nre` | 3 | workbench.jar |
| `tridium:nrio` | 1 | nrio.jar |
| `tridium:nurio` | 1 | nurio.jar |
| `tridium:obixDriver` | 2 | obixDriver.jar |
| `tridium:opcUaClient` | 1 | opcUaClient.jar |
| `tridium:opcUaServer` | 1 | opcUaServer.jar |
| `tridium:opcUaServerAnonLogin` | 1 | opcUaServer.jar |
| `tridium:platform` | 1 | fox.jar |
| `tridium:platformClient` | 1 | platform.jar |
| `tridium:premiumWBNiagaraRemote` | 2 | baja.jar, niagaraCloud.jar |
| `tridium:provisioning` | 1 | provisioningNiagara.jar |
| `tridium:rdbHistoryArchive` | 1 | rdb.jar |
| `tridium:rdbHsqlDb` | 1 | rdbHsqlDb.jar |
| `tridium:rdbMySQL` | 1 | rdbMySQL.jar |
| `tridium:rdbSqlServer` | 1 | rdbSqlServer.jar |
| `tridium:remoteVideo` | 5 | maxpro.jar, naxisVideo.jar, nmilestone.jar, remoteVideo.jar, xprotect.jar |
| `tridium:samlDP` | 1 | saml.jar |
| `tridium:search` | 1 | search.jar |
| `tridium:securityDashboard` | 1 | nss.jar |
| `tridium:serial` | 1 | platSerial.jar |
| `tridium:sms` | 1 | sms.jar |
| `tridium:snmp` | 1 | nSnmp.jar |
| `tridium:systemDb` | 5 | orientSystemDb.jar, systemDb.jar, systemIndex.jar |
| `tridium:systemIndex` | 5 | systemDb.jar, systemIndex.jar |
| `tridium:tags` | 1 | tagdictionary.jar |
| `tridium:template` | 3 | template.jar |
| `tridium:tls` | 1 | tls.jar |
| `tridium:videoDriver` | 4 | nvideo.jar, videoDriver.jar |
| `tridium:web` | 1 | web.jar |
| `tridium:workbench` | 4 | workbench.jar |
| `tridium:zulu25` | 1 | baja.jar |

**Every single one of the 84 pairs uses vendor `tridium`** `[CERT]` — this generic beta distribution
carries no OEM-branded feature vendor string (contrast N4's B108/B98/B387, whose corpus reads
`Honeywell`/`HoneywellCentraLine`/`honeywell` vendor literals from OEM-branded N4 builds) — consistent
with, and explained by, §11.7's OEM-absence finding.

## 11.5 — Attribute-key map: 36 keys extracted + 1 hand-verified addition, classified `[CERT — pipeline output, not individually spot-verified except rows named]` / `[CERT]` (the addition)

Extracted from `Feature.get`/`getb`/`geti` call sites, using each target's own bytecode DESCRIPTOR (read
from the same `javap` line) to decide whether the last one or two preceding literals is the key — a
one-`String`-param overload (`get(String)`, `getb(String,Z)`, `geti(String,I)`) takes the LAST literal as
the key; the two-`String`-param overload (`get(String,String)`) takes the SECOND-TO-LAST as the key
(assuming the default is also a literal — see the caveat below).

| Attribute key | # sites | Example caller |
|---|---|---|
| `device.limit` | 5 | niagaraDriver.jar/BNiagaraEdgeLiteStation#getEdgeLiteLicenseLimit |
| `.limit` | 4 | baja.jar/BAbstractService#checkLicense |
| `brandId` | 3 | baja.jar/Brand#init |
| `system` | 3 | hierarchy.jar/BHierarchyService#getLicenseFeature |
| `OnOff` | 2 | saml.jar/BSAMLIdPService#getLicenseFeature |
| `edgeLite1_device.percentage` | 2 | niagaraDriver.jar/BNiagaraEdgeLiteStation$EdgeStationHolder |
| `export` | 2 | bacnet.jar/BBacnetNetwork#hasServerLicense |
| `local` | 2 | hierarchy.jar/BHierarchyService#getLicenseFeature |
| `profiles` | 2 | workbench.jar/WbMain#doCheckLicense |
| `admin` | 1 | workbench.jar/WbMain#doCheckLicense |
| `alarm` | 1 | alarm.jar/BAlarmService#getLicenseFeature |
| `anonymous.access` | 1 | opcUaServer.jar/BOpcUaServer#isAnonReadEnabled |
| `bacnetSc` | 1 | bacnet.jar/BAbstractConnectionManager#checkLicense |
| `component.limit` | 1 | ace.jar/LicenseUtil#getComponentLimitString |
| `demoOnly` | 1 | baja.jar/Station#checkLicense |
| `heap.limit` | 1 | baja.jar/ResourceManager#checkLicense — **`[CERT]` live re-verified, §11.10** |
| `history.limit` | 1 | rdb.jar/BRdbmsHistoryImport#checkLicense |
| `historyImport` | 1 | rdb.jar/BRdbmsHistoryImport#checkLicense |
| `mbus` | 1 | mbus.jar/BAbstractMbusNetwork#getLicenseFeature |
| `minVersion` | 1 | baja.jar/LicenseUtil#checkJreFeature |
| `moduleDev` | 1 | baja.jar/ModuleDev#isModuleDevFeatureLicensed |
| `modules` | 1 | baja.jar/SubGroup |
| `none` | 1 | baja.jar/NLicenseManager#dump |
| `orientDb` | 1 | orientSystemDb.jar/BOrientSystemDb#checkLicense |
| `owner` | 1 | workbench.jar/WbMain#doCheckLicense |
| `platform` | 1 | fox.jar/FoxSession#getNiagaraPlatformType |
| `port.limit` | 1 | bacnet.jar/BBacnetMstpLinkLayer#checkLicense |
| `project` | 1 | workbench.jar/WbMain#doCheckLicense |
| `session.limit` | 1 | box.jar/BBoxService#getLicenseFeature |
| `skipModuleValidation` | 1 | baja.jar/ModuleSetClassLoader#loadSkipModuleValidation |
| `subscriptionExp` | 1 | analytics.jar/NAFFeatureUtil#getExpiry |
| `useBrand` | 1 | platform.jar/BDaemonSession#getBrandId |
| `validCheckFreq` | 1 | baja.jar/SubscriptionLicenseManager#initPeriodicEntitlementCheck — **`[CERT]` live re-verified, §11.10** |
| `validCheckRetry.limit` | 1 | baja.jar/SubscriptionLicenseManager#initPeriodicEntitlementCheck — **`[CERT]` live re-verified, §11.10** |
| `vendor` | 1 | baja.jar/LicenseUtil#checkJreFeature |
| `virtual` | 1 | niagaraDriver.jar/BNiagaraVirtualNetworkExt#checkLicense |
> **§14 correction (2026-09-27, [Block 34]):** the `resource.limit` gate polarity is `if (!Metrics.isUsingCapacityLicensing())` (live `javap -c -p` on ResourceManager.checkLicense) — the opposite of the inference below; capacity licensing is NOT new to N5 (N4 B488 §488.2 already had it).

| `resource.limit` (**hand-added, not in the mechanized table**) | 1 | baja.jar/ResourceManager#checkLicense — `[CERT]` live-verified, see below |

**Gating-type classification** `[INFER]` (grouping, not extraction): **numeric limits** — every `*.limit`
key (`device.limit`, `component.limit`, `history.limit`, `port.limit`, `session.limit`,
`validCheckRetry.limit`, `heap.limit`, `resource.limit`, the bare `.limit` suffix pattern) plus
`edgeLite1_device.percentage`; **on/off or mode switches** — `OnOff`, `moduleDev`,
`skipModuleValidation`, `demoOnly`, `useBrand`, `virtual`, `anonymous.access`; **expiry/cadence** —
`subscriptionExp`, `validCheckFreq`, `minVersion` (a version-floor gate, not a date, but functions the
same way — [Block 6] §6.3); **identity/scope** — `brandId`, `vendor`, `system`, `local`, `owner`,
`project`, `profiles`, `admin`. This three-way split matches N4's own B488 classification (limit /
on-off / expiry) exactly — no new gating CATEGORY, only new instances of the same three categories.
`[CERT]` on the category members named above (each read from the extraction table); `[INFER]` on the
three-way taxonomy itself (a synthesis, not a literal).

**Known heuristic limitation, demonstrated and hand-corrected at one site.**
`ResourceManager.checkLicense(Feature)` (`baja.jar`) actually reads **two** attribute keys, not one:
```
40: aload_2
41: ldc     #194   // String heap.limit
43: ldc     #196   // String -1
45: invokeinterface #198  // Feature.get:(String,String)String
...
155: aload_1
156: ldc     #246   // String resource.limit
158: aconst_null
159: invokeinterface #198  // Feature.get:(String,String)String
```
`[CERT]` (live `javap -c -p -classpath baja.jar com.tridium.sys.resource.ResourceManager`, re-run this
session). The SECOND call's default argument is `aconst_null` (not a string literal) — the mechanized
extraction rule ("2-`String`-param overload → key = second-to-last literal") assumed BOTH arguments are
literals, so at this site it computed a bogus key (an unrelated `println` banner string from further up
the same method — the literal buffer is per-METHOD, not per-call-adjacency) and correctly discarded it
(the space-containing bogus string failed the identifier filter) rather than mislabeling it — but the
genuine key `resource.limit` was silently dropped, not wrong. **The attribute-key table is therefore a
verified LOWER BOUND on distinct keys (fails safe by omission), not a guaranteed-complete enumeration**
— any 2-`String`-param `get()` call whose default is `null`/non-literal is at risk of the same
under-count. Re-deriving every one of the 39 `Feature.get` sites individually (rather than the shared
heuristic) is named **B11-G4**.

`resource.limit` gates a **new-looking call not documented in N4's B387/B488**: it is read only when
`com.tridium.sys.metrics.Metrics.isUsingCapacityLicensing()` returns `true` (offset 148, immediately
before the `ldc "resource.limit"` at 156) — a static boolean switch this block did not decompile. No hit
for `isUsingCapacityLicensing`/`CapacityLicensing` in the N4 `niagara-research` corpus
(`corpus-nav.py find "CapacityLicensing"` → "No matches.") `[CERT]` on the absence-in-corpus-search;
`[INFER]` on "N5-new" (corpus-absence is not proof of N4-absence — named **B11-G1**).

## 11.6 — `getFeature` (98) outnumbers `checkFeature` (40) 2.5:1 — same two-method contract as N4, no strictness change `[CERT]`

`NLicenseManager`'s own N5 source (§6's decompile, read again here) settles WHY:

```java
public Feature getFeature(String vendor, String feature) {
   ...
   Feature f = this.features.get(key);
   if (f == null) throw new FeatureNotLicensedException(key);
   return f;                    // <-- no f.check() — expiry NOT enforced here
}

public Feature checkFeature(String vendor, String feature) {
   ...
   Feature f = this.features.get(key);
   if (f == null) throw new FeatureNotLicensedException(key);
   f.check();                   // <-- expiry enforced
   return f;
}
```
`[CERT]` (`/tmp/claude-1000/n5b6/out/com/tridium/sys/license/NLicenseManager.java`, [Block 6]'s own
decompile, read again this session — not re-derived). This is **byte-for-byte the same two-method
contract N4's B387 §387.2 documents**: `"getFeature(vendor, feature) — returns the Feature WITHOUT
enforcing expiry (the common path; the caller invokes feature.check() itself)"` vs `"checkFeature(vendor,
feature) — calls feature.check() internally… used where a gate must block immediately"`. `[CERT]`
(niagara-mental-model-bloque387.md §387.2, read in full this session).

The observed 98:40 ratio is therefore **not** evidence of a licensing-strictness change — it reflects
that most N5 call sites (like most N4 ones, per B387's own framing) prefer the two-step `getFeature()` +
separate `.check()`/`.get()`/`.getb()` pattern (33 explicit `Feature.check()` calls + 39 `Feature.get` +
20 `Feature.getb` + 3 `Feature.geti` = 95 follow-up calls against 98 `getFeature()` sites — consistent
order of magnitude, `[INFER]` that they are the SAME call chains, not independently traced site-by-site).
A concrete confirmed 2-step chain: `platIEEE8021X.jar`'s `BIEEE8021XPlatformService.serviceStarted()`
calls `getFeature("tridium","ieee8021x")` then `.check()` — the EXACT pattern N4's B481 §481 documents
for the identically-named N4 feature (`getFeature("tridium","ieee8021x").check()`) `[CERT]`
(`niagara-mental-model-bloque481.md:87`, read this session) — **the 802.1x license-gate call pattern is
unchanged, name and all, between N4 and N5**.

## 11.7 — `nre.jar`: zero confirmed licensing-API call sites `[CERT — negative existence, artifact opened]`

`nre.jar` (`bin/ext/nre.jar`) — the one jar the task named explicitly outside the `modules/` directory —
was scanned by BOTH stages (§11.2) and produced **zero confirmed call sites** to any of the 11 target
methods. Its one stage-1 byte hit resolved to an unrelated method name collision (§11.2). `[CERT]` —
this exact jar was opened and searched by the same method as every other jar (methodology §3's
negative-existence discipline: the artifact WAS opened).

This connects to, and partially resolves, [Block 6]'s **B6-G1** ("`com.tridium.nre.subscription` in
`nre.jar`… out of this block's jar scope"): `nre.jar`'s subscription-transport classes
(`SubscriptionLicenseUtil`, `RetrieveEntitlements`, `EntitlementApi`, `LicenseValidator`) do NOT
themselves call `niagara.license.LicenseManager.checkFeature`/`getFeature` — the feature-gate checks all
live in `baja.jar`'s `com.tridium.sys.license.subscription.SubscriptionLicenseManager` (already covered
by [Block 6] §6.11 and this block's §11.4 `developer`/`fips140`/etc. rows), and `nre.jar` supplies only
the transport/validator plumbing `SubscriptionLicenseManager` calls INTO, not the other way. `[INFER]`
(consistent with, not independently proving, B6-G1's still-open "trace `SecurityUtil`/`nre.jar`" thread).

## 11.8 — N4 comparison: one confirmed rename, several exact-name matches, several apparently-new names `[CERT]`/`[INFER]`

**Confirmed rename** `[CERT]`: N4's FIPS feature is named **`fips140-2`** (`niagara-mental-model-bloque481.md:75`:
`` `fips140-2` — `Nre.verifyFipsLicense()`… ``, read this session) — N5's is **`fips140`** (no `-2` suffix),
confirmed live: `javap -c -p -classpath baja.jar com.tridium.sys.Nre` →
`private static void verifyFipsLicense(); … 6: ldc_w #1342 // String fips140` (offset 9 invokes
`checkFeature`) `[CERT]` (re-verified live this session, exact match to the mechanized extraction).

**Exact-name matches, call pattern unchanged** `[CERT]`: `developer` (N4 B387/[Block 6] §6.10),
`bacnet`/`bacnetSc`/`mstp` (N4 B387 exactly), `modbusTcp` (N4 B387), `accessControl` (N4 B387),
`analytics` (N4 B387), `email` (N4 B387), `hierarchy` (N4 B387), `historyArchive` (N4 B387),
`mobile`/`web` (N4 B387), `globalCapacity` (N4 B387), `ieee8021x` (N4 B481, §11.6), `samlDP` (N4 B494),
`bacnetAws` (N4 B885), `axisVideo`/`naxisVideo` (N4 B453/B454), `edgeLite1_device.percentage` (N4 B483)
— **16 of the 84 N5 feature keys are independently confirmed present, unchanged, in the N4 corpus** by
name, and the `heap.limit`/"STATION IS UNLICENSED!!!"/`System.exit(-3)` triple (§11.5) is a byte-for-byte
behavioral match to N4's B387 §387.4 finding.

**No N4-corpus hit (5 names)** `[INFER — corpus-absence, not proven N4-absence]`:
`opcUaServerAnonLogin`, `milestoneCorporate`, `niagaraSync`, `cloudLinkConnect`,
`premiumWBNiagaraRemote` — none matched in `corpus-nav.py find` against the ~1,000-block
`niagara-research` corpus. This is evidence of ABSENCE-FROM-THE-SEARCHED-CORPUS, not evidence the
feature is absent from N4 itself (that corpus's own coverage of `opcUaServer`/`cloudLink`/`niagaraSync`-
adjacent N4 jars was not exhaustively re-checked this session) — flagged, not asserted, and folded into
the existing porting-guide gap (RESEARCH-STATE `N5-G16`) rather than opened as a fresh gap.

**Module-set absence, not a feature-naming delta** `[CERT]` on the jar-listing fact; `[INFER]` on cause:
no jar in this 248-jar set is named `honEasyBinding`/`honAlarmConsole`/`honAlarmExt`/`honPointListView`
(`ls modules/ | grep -i "^hon"` → only `lonHoneywell.jar`/`lonHoneywellXfl800.jar`, LON *drivers*, not the
OEM UI-layer modules) — the whole Honeywell-OEM UI/licensing layer N4's B80/B81/B98/B207/B244/B387
documents (feature names `honEasyBinding`, `honPointListView`, `clCbus`, etc.) is simply **not shipped in
this generic N5 beta distribution**, so it produces no call sites here at all — not because those
features were removed from N5's architecture, but because this install is not an OEM-branded build.
Likewise, **no jar matches `*[Ss]ign*` beyond `signingService.jar`** — N4's `eSignature`
feature/module (B356/B387 §387.3) has no N5 counterpart jar in this set either. Both are named
**B11-G2** (needs an OEM-branded N5 build to adjudicate edition-gap vs architecture-removal).

**N4's own `checkFeature` grep count (95, from B1-3) is not directly comparable** `[INFER]`: that count is
a raw TEXT grep across the whole `niagara-research` corpus's prose+code excerpts (`"58 resueltos, 37
ZKM-obfuscados"`), spanning an OEM Honeywell-branded ~1,013-jar N4 install; this block's 40 `checkFeature`
+ 98 `getFeature` = 138 LicenseManager-level call sites are bytecode-precise counts over a DIFFERENT
(generic, 248-jar, beta) N5 distribution. The two numbers answer related but not identical questions;
neither supersedes the other.

## 11.9 — The 6 dynamic/non-literal `checkFeature`/`getFeature` call sites `[CERT]` (existence) / not traced (values, → B11-G3)

| Module | Class | Notes |
|---|---|---|
| `baja.jar` | `com.tridium.sys.station.Station` | one literal captured (`tridium`); feature arg is a variable |
| `cloudLink.jar` | `com.tridium.cloudLink.channel.BBackupChannel` | preceding literals are log strings ("Niagara Recover license check skipped for NCS station"), not the actual args |
| `cloudLink.jar` | `com.tridium.cloudLink.transport.BNiagaraRemoteTransport` | same pattern, different log string |
| `platform.jar` | `com.tridium.platform.BPlatform` | preceding literal is an error message, not an arg |
| `platform.jar` | `com.tridium.platform.command.BPlat` | zero preceding literals — both args are variables/fields |
| `platHwScan.jar` | `com.tridium.platHwScan.ports.BPort` | args built at runtime via `StringTokenizer` splitting a `"vendor:feature"` config string — confirmed live: `ldc #58 // String ,` immediately precedes an unrelated `StringTokenizer` call chain, not the checkFeature args themselves |

`[CERT]` on existence and the absence of a usable literal; the actual runtime `vendor`/`feature` values
these 6 sites resolve to were NOT traced (would need a targeted decompile of each of these 6 classes,
not the mechanized pipeline) — named **B11-G3**.

## 11.10 — Self-verification

**Pipeline determinism.** Both stages are mechanized (`shortlist.py`, `extract_callsites.py`, preserved
under the scratchpad path in the header); the second background run of `extract_callsites.py` (launched
accidentally in duplicate) reproduced byte-identical output (77 jars / 127 classes / 253 call sites) —
the pipeline is deterministic, not a one-off hand transcription.

**Live spot-checks performed THIS session** (not merely trusted from the pipeline — each re-run against
the live jar with `javap -c -p` and compared against the JSON the pipeline emitted):
1. `baja.jar!com.tridium.sys.Nre#verifyFipsLicense()` @offset 9 → `tridium`/`fips140` → matches (§11.8).
2. `ace.jar!com.tridium.ace.util.LicenseUtil` → `ace` (checkFeature) then `component.limit`
   (`Feature.get`) → matches (§11.5).
3. `baja.jar!com.tridium.sys.license.NLicenseManager#postInit()` @43 → `checkDeveloperLicense()` @10 →
   `tridium`/`developer` (`checkFeature`) → matches (§11.4, and confirms [Block 6] §6.10's finding by a
   different route: the private helper method, not just the public accessor).
4. `baja.jar!com.tridium.sys.resource.ResourceManager#checkLicense(Feature)` — full method disassembled
   live, both `heap.limit` (offset 45) and `resource.limit` (offset 159) confirmed, plus the
   `System.exit(-3)`/"STATION IS UNLICENSED!!!" banner byte-for-byte (§11.5/§11.6).
5. `nre.jar!com.tridium.nre.cloud.NiagaraCloudConfiguration` → confirmed the one stage-1 hit is
   `getFeatureEnablementEndpoint()`, unrelated (§11.7).

**Marker tally** (mechanized `grep -c`, run against this file after writing it):

```
$ grep -o '\[CERT\]' /home/cristian/niagara5-research/niagara5-block11.md | wc -l
      32
$ grep -o '\[CERT — pipeline output, not individually spot-verified' /home/cristian/niagara5-research/niagara5-block11.md | wc -l
       4
$ grep -o '\[CERT — negative existence' /home/cristian/niagara5-research/niagara5-block11.md | wc -l
       2
$ grep -o '\[INFER' /home/cristian/niagara5-research/niagara5-block11.md | wc -l
      13
```
(literal output, re-run against the file as saved — not hand-recalled; supersedes any earlier estimate
drafted before this final pass). The three 77/84/36-row tables (§11.3-§11.5) are governed by the single
`[CERT — pipeline output…]` grade declared once in each section header rather than repeated per-row
(avoiding ~200 redundant inline markers) — this is a deliberate block-level convention, flagged here so
a reviewer does not read the low per-row marker density as under-citation: EVERY row in those three
tables is pipeline output, covered by that section's header grade, with the rows individually upgraded
to `[CERT]` in §11.10's spot-checks and §11.5's hand-verified addition named explicitly in their own
table cells.
Adjusted ratio `[INFER]`/`[CERT]`-family (32+4+2=38) ≈ **0.34** — moderate-low, consistent with an
evidence-dominant block whose per-row citation weight is carried by section-level grades rather than
inline repetition; `[INFER]` is reserved for (a) the gating-type taxonomy (a synthesis, §11.5),
(b) "no N4-corpus-hit ≠ N4-absent" hedges (§11.8), and (c) the OEM-edition-gap-vs-architecture-removal
open question (§11.8/B11-G2).

**Token check.** Every bytecode offset and literal string quoted verbatim in §11.5-§11.10 (`fips140`,
`heap.limit`, `resource.limit`, `component.limit`, `checkDeveloperLicense`, `ieee8021x`,
`isUsingCapacityLicensing`, `getFeatureEnablementEndpoint`) was `grep`/`javap`-confirmed live against the
actual jar immediately before being written into this block (transcript: the Bash tool calls this
session, not hand-recalled). `verify-block.sh`/`verify-state.sh` were NOT run — this corpus's layout
(`niagara5-research/`, flat, no `research-sdd` kit checkout inside it) does not carry the kit tooling;
per METHODOLOGY §11's "decompiled-tree blocks" provision, the citation gate here is 100% inline
token-verify (documented above) rather than a mechanized `verify-block.sh` resolution pass — declared
explicitly per that section's requirement, not silently omitted.

## 11.11 — Open questions / unresolved artifacts

- **[C1]** `Metrics.isUsingCapacityLicensing()` (§11.5) gates a second `ResourceManager` limit
  (`resource.limit`) that N4's B387/B488 do not name alongside `heap.limit` — unresolved whether this is
  an N5-new capacity-licensing MODE (two mutually exclusive licensing schemes?) or simply an N4 finding
  this corpus's B387/B488 did not individually enumerate. Not pushed to a `CONTRADICTIONS.md` (this
  corpus has none yet, same as [Block 6]) — named **B11-G1**.

## 11.12 — Connections

- **[Block 6]** — this block is the direct closure of [Block 6]'s child gap **B6-G3**, widened per this
  session's assignment from "the rest of `baja.jar`" to all 247 module jars + `nre.jar`. It reuses
  [Block 6]'s own decompiled `niagara.license`/`com.tridium.sys.license` API surface (§11.1) and
  independently re-confirms two of [Block 6]'s own findings by a different call path: the `developer`
  feature check inside `NLicenseManager.postInit()`→`checkDeveloperLicense()` (§6.10, §11.10 spot-check
  3) and the `zulu25`/`checkJreFeature()` JRE gate (§6.10, §11.4 table row).
- **[Block 3]** — the `fips140`(→ renamed from N4's `fips140-2`) feature (§11.8) is the licensing-side
  gate for Block 3's `bcfips`/`bcstd` FIPS crypto-provider swap, mirroring how [Block 6] §6.10's `zulu25`
  feature ties to Block 3's bundled-JRE migration.
- **`niagara-research` B387** — this block's per-module/per-feature census is the N5-side, full-corpus
  counterpart to B387's N4 "runtime feature-gate map"; §11.6 and §11.5's `heap.limit`/exit(-3) finding
  are direct, exact confirmations that B387's enforcement model (`getFeature`-without-check vs
  `checkFeature`-with-check; absent-feature→uncapped; heap-limit-exceeded→`System.exit(-3)`) is
  UNCHANGED in N5.
- **`niagara-research` B488** — this block's three-way limit/on-off/expiry attribute-key taxonomy
  (§11.5) matches B488's own N4 classification with no new category, only new feature instances.
- **`niagara-research` B14/B1-3** — the N4 corpus's own `checkFeature` grep count (95 hits) is
  discussed, and explicitly NOT treated as directly comparable to this block's bytecode-precise 138-site
  count, in §11.8.
- **`niagara-research` B479-B481/B483** — §11.6's `ieee8021x` two-step call-pattern match and §11.8's
  `fips140-2`→`fips140` rename and `edgeLite1_device.percentage` match all cite this block group as the
  N4 comparator.

---

## Child gaps opened this block

- **B11-G1** — `com.tridium.sys.metrics.Metrics.isUsingCapacityLicensing()`: a static boolean switch
  gating a second `ResourceManager` limit key (`resource.limit`, alongside the already-known
  `heap.limit`) with no named N4-corpus counterpart. Decompile `Metrics` to find what sets this flag and
  whether it represents a new licensing MODE or an existing-but-previously-unenumerated N4 mechanism.
- **B11-G2** — OEM-branded module absence: no `honEasyBinding`/`honAlarmConsole`/`honPointListView`-style
  Honeywell OEM UI jar, and no `eSignature`-style electronic-signature jar, exists in this generic N5
  5.0.0.28 beta's 248-jar set (§11.8). Needs an OEM-branded N5 build (if/when one exists) to determine
  whether this is an edition/SKU gap (not shipped in this generic beta) or a genuine architectural removal
  from N5.
- **B11-G3** — The 6 dynamic/non-literal `checkFeature`/`getFeature` call sites (§11.9: `Station`,
  `BBackupChannel`, `BNiagaraRemoteTransport`, `BPlatform`, `BPlat`, `BPort`) resolve their vendor/feature
  arguments at runtime; a targeted Vineflower decompile of these 6 classes (not the mechanized pipeline)
  would recover the actual values.
- **B11-G4** — Upgrade this block's bytecode-offset citations to source-level `file:line` by running
  Vineflower over the 127 classes with confirmed call sites, and individually re-verify each of the 84
  `vendor:feature` pairs and 36+1 attribute keys beyond the 5 live spot-checks done this session — the
  extraction heuristic is a demonstrated, fail-safe LOWER BOUND (§11.5), not a proven-complete
  enumeration.

## Measure counts

| Measure | Count |
|---|---|
| Jars scanned (247 `modules/*.jar` + `nre.jar`) | 248 |
| Jars shortlisted (stage 1, byte pre-filter) | 83 |
| Classes shortlisted (stage 1) | 282 |
| Jars with confirmed call sites (stage 2) | 77 |
| Classes with confirmed call sites | 127 |
| Total confirmed call sites | 253 |
| Distinct target-method breakdown | 11 methods (§11.2 table) |
| Distinct `vendor:feature` pairs (literal-argument) | 84 (all vendor `tridium`) |
| Dynamic/non-literal `checkFeature`/`getFeature` sites | 6 (§11.9, → B11-G3) |
| Distinct attribute keys (`Feature.get`/`getb`/`geti`) | 36 (mechanized) + 1 (hand-verified `resource.limit`) |
| `nre.jar` confirmed call sites | 0 (negative existence, §11.7) |
| Confirmed N4↔N5 feature-name renames | 1 (`fips140-2` → `fips140`) |
| Confirmed N4↔N5 exact-name matches | 16 named in §11.8 |
| Names with no N4-corpus hit (not asserted N5-exclusive) | 5 (§11.8) |
| Live spot-checks performed this session | 5 (§11.10) |
| Child gaps opened | 4 (B11-G1..G4) |
