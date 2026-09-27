# Block 24 — The N4→N5 migrator catalog: every converter n5mig applies

> Full catalog of what `n5mig` (the N4→N5 station migrator, [B14]) actually converts: all **58**
> registered types in `migrator.jar` plus `propMigration.jar`'s **19** types (11 data-shape classes + 8
> converters). Closes [B14]'s child gaps **B14-G2** (`propMigration.jar` read in full — and reclassified,
> §24.5), **B14-G3** (all 58 `migrator.jar` types now read, not just 4), **B14-G4** (`BBogMigrator`'s
> pipeline read line-by-line, not censused), and **B14-G5** (`MigratorTypeResolver`, `MigratorOrdConverter`,
> `MigrationUtils` all read). Also cross-checks the catalog against a REAL PANCCADIA `config.bog` copy
> (`poc/n5mig-panccadia/in/config.bog`) to identify which converters would actually fire on that station,
> and diffs the N5 `BBogMigrator` pipeline against the AX→N4-era one documented in `niagara-research` [B405].
> Does **not** cover: an actual `n5mig` execution (still B14-G1, requires-execution); the points/histories/
> alarm bog files of PANCCADIA (only `config.bog` was available in the poc copy — the driver network structure,
> not device points); `BProgramConverter`'s full body (already read by [B14] §14.8, not re-read here); the
> `MigratorProcessStreamPane`/`MigratorWbTool` UI wizard classes beyond confirming they are NOT converters
> (read for completeness, contain no `convertXElem`/`getConvertTypes`).
>
> Subject version: Niagara **5.0.0.28 (Beta)** — same install as [B14] ([B1]-[B4], [B10]).
> `migration.jar` sha256 `ebce515de72632955899846b296b08a2ee3045c1422397ce6b0715c80482c49c`; `migrator.jar`
> sha256 `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08` (both unchanged since [B14], reused
> from that session's decompile — not re-decompiled); `propMigration.jar` sha256
> `5ee675c6809354f234b2d0c7ad1826837689a51a3603b6fa1b7de02ca5f4f031` (freshly decompiled this session, hash
> matches [B14]'s header — confirms same artifact).
>
> Sources: `migrator.jar` + `migration.jar` Vineflower decompile at
> `/home/cristian/niagara5-research/organized/migrator/vineflower/` and `.../migration/vineflower/`
> (produced by [B14]'s session, reused here — 72 and 18 `.java` files respectively, both directory trees
> re-verified present and complete this session); `propMigration.jar` Vineflower 1.12.0 decompile (this
> session, `java -jar vineflower-1.12.0.jar propMigration.jar` at
> `/tmp/claude-1000/n5b24/decompiled_propMigration/` — 20 classes, clean decompile, no errors); PANCCADIA
> `config.bog` at `/home/cristian/niagara5-research/poc/n5mig-panccadia/in/config.bog` (real station backup
> copy, read-only, count-only per task scope — no credentials extracted); `niagara-research` [B405]
> (`niagara-mental-model-bloque405.md`, AX→N4-era migrator, read in full for the §24.3 cross-comparison).
>
> Method: `java -jar vineflower-1.12.0.jar -e=baja.jar propMigration.jar decompiled_propMigration` (Homebrew
> OpenJDK 26); `unzip`/`python3 re.findall` census of each jar's `META-INF/module.xml` `<type>` entries;
> full read of every one of the 58 `migrator.jar` classes and all 19 `propMigration.jar` classes (`cat`, this
> session); full read of `BBogMigrator.java` (771 lines), `MigratorOrdConverter.java` (315 lines),
> `MigratorTypeResolver.java` (115 lines); grep census of `MigrationUtils.java`'s 40 public/private static
> methods (569 lines, not read line-by-line — signatures only); `unzip config.bog` → `file.xml`, `grep -o`
> census of `m=` module-abbreviation attrs and `t=` type-prefix attrs (read-only, aggregate counts, no
> point/credential data extracted).
> Markers: `[CERT]` local primary source (`file:line`) · `[INFER]` deduction.
>
> Build/porting layer. Deepens [B14] (same `n5mig`/migrator SPI, now with the FULL converter catalog instead
> of a 4-of-58 sample) and connects `niagara-research` [B405] (the AX→N4-era migrator, cross-compared in
> §24.3) and PANCCADIA ([B10]'s worktree, cross-checked in §24.6).
>
> **Type:** `mixed` — §24.1-§24.5 are evidence blocks (reading the shipped jars); §24.6 draws `[INFER]`
> conclusions by cross-referencing the §24.2 catalog against PANCCADIA's real `config.bog` byte content (a
> different artifact than this block's own primary jar sources) — the declared `mixed` trigger.

---

## 24.1 — Module inventory confirmed `[CERT]`

Three jars implement the N4→N5 migrator's converter catalog, all under
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules`:

| Jar | Description (`module.xml`) | `<type>` count | Package | Decompiled this session? |
|---|---|---|---|---|
| `migration.jar` | "N4 Migration Core" | 10 (SPI interfaces + 2 static registries) | `niagara.migration` | No — reused [B14] decompile |
| `migrator.jar` | "N5 Migration Tool" (symbol still `n4m`, [B14] §14.4) | **58** | `com.tridium.migrator.*` | No — reused [B14] decompile |
| `propMigration.jar` | (no description string read; symbol `propMigration`) | **19** | `com.tridium.propMigration.*` | **Yes**, this session |

`[CERT]` `migrator.jar META-INF/module.xml` (`re.findall(r'<type[^>]*/>')` → 58 matches, re-confirmed this
session at `/home/cristian/niagara5-research/organized/migrator/vineflower/META-INF/module.xml`);
`propMigration.jar META-INF/module.xml` → 19 matches (this session,
`/tmp/claude-1000/n5b24/extracted_propmig/META-INF/module.xml`).

## 24.2 — The full `migrator.jar` catalog: all 58 registered types `[CERT]`

Every row below was read in full this session (`cat`, not grep-sampled). "Kind" classifies the dominant
behavior: **removal** (whole object or whole module dropped), **rename** (typespec/property/value changed,
object structure otherwise intact), **structural** (properties added/removed/restructured beyond a simple
rename), **file** (a `BIFileMigrator`, not a bog-element converter), **UI** (Workbench tool/wizard, not a
converter at all).

### Core file/dist migrators (8) — `niagara.migration.BIFileMigrator` implementations

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BBackupDistMigrator` | ext `dist` | Top-level station-backup `.dist` unpacker/driver; resolves target station name, decrypts, dispatches each inner file to its own migrator | file | `BBackupDistMigrator.java:31` |
| `BBackupDistPremigrator` | ext `dist` | `-premigrate` dry-run counterpart of the above | file | `BBackupDistPremigrator.java:25` |
| `BBogMigrator` | ext `bog`,`palette` | Per-bog-file migrator — full pipeline in §24.3 | structural | `BBogMigrator.java:63` |
| `BBogPremigrator` | ext `bog`,`palette` | `-premigrate` counterpart of `BBogMigrator` | file | `BBogPremigrator.java:32` |
| `BMigrationBogFile` | n/a (helper `BBogFile` subclass, not registry-dispatched) | Opens a bog with a `MigratorTypeResolver` wired in, so `ConverterRegistry` fires during the LOAD, not just the XML-stub pass | structural | `BMigrationBogFile.java:25` |
| `BProvisioningNiagaraMigrator` | dir `provisioningNiagara` | Plain recursive file COPY, no conversion (`BajaFileUtil.copy` per file) | file (copy-only) | `BProvisioningNiagaraMigrator.java:16` |
| `BPxMigrator` | ext `px` | Per-px-file migrator (mirrors `BBogMigrator`'s stub/convert/encode shape for px UI files) | structural | `BPxMigrator.java:58` |
| `BPxPremigrator` | ext `px` | `-premigrate` counterpart of `BPxMigrator` | file | `BPxPremigrator.java:32` |

### Generic bog-element converters (2)

| Class | Registered for | From → To | Kind | `file:line` |
|---|---|---|---|---|
| `BTypeSpecConverter` | `baja:TypeSpec` | Any unresolvable `v=` typespec attribute → re-queried via `ConverterRegistry`; strips `v=` if no converter found | rename (generic) | `BTypeSpecConverter.java:23` (full read, [B14] §14.6) |
| `BServerCertificateHealthToCertificateHealthBogConverter` | `baja:ServerCertificateHealth` | `baja:ServerCertificateHealth` → `baja:CertificateHealth` (package `com.tridium.security.BServerCertificateHealth`→`niagara.security.CertificateHealth`) | rename | `BServerCertificateHealthToCertificateHealthBogConverter.java:18` |

### Program-object converters (3)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BProgramConverter` | `program:Program` | Import/source rewrite + recompile + code-signing check ([B14] §14.8, not re-read) | structural | `BProgramConverter.java:46` |
| `BProgramModuleConverter` | `program:ProgramModule` | `convertComplex()`: calls `BProgramConverter.fixProgram()` on every child `BProgram`, then rationalizes the module's `BNameMap` dependencies (`BProgramModule.rationalizeDependencies`) — the LIVE-tree counterpart of `BProgramConverter`'s XML-level rewrite | structural | `BProgramModuleConverter.java:23` |
| `BProgramServiceConverter` | `program:ProgramService` | Removes deprecated property `allowProgramRuntimeExec` | structural (prop removal) | `BProgramServiceConverter.java:14` |

### UI/wizard classes — NOT converters (2)

| Class | Registered for | What it does | Kind |
|---|---|---|---|
| `BMigratorProcessStreamPane` | n/a | Workbench pane that streams `n5mig` console output live during an interactive migration | UI |
| `BMigratorWbTool` | n/a | `BWbTool` entry point — opens `MigratorWbToolWizard` from the Workbench Tools menu | UI |

`[CERT]` neither class implements `BIBogElementConverter`/`BIFileMigrator`; `BMigratorWbTool.java:13`
(`extends BWbTool`, `invoke()` just opens a wizard dialog — no `convertXElem`/`migrate()` anywhere in either
file, confirmed by `grep` this session).

### Utility/cleanup (2)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BBackupRecordsCleaner` | `backup:BackupRecord` | Deletes every `backup:BackupRecord` element (`convertXElem` returns `null`) | removal | `BBackupRecordsCleaner.java:15` |
| `BKeytabFileRemover` | dir `ldap`, ext `keytab` | `BFileMigrator` that logs every keytab file and copies NONE (`migrate()` returns `Optional.empty()` after only logging — files are dropped, not carried forward) | removal (file-level) | `BKeytabFileRemover.java:14` |

### totpAuth / tunnel / haystack / tagDictionary (5)

| Class | Registered for | From → To | Kind | `file:line` |
|---|---|---|---|---|
| `BGauthToTotpAuthBogConverter` | `gauth`, `gauth:GoogleAuth*` (7 types) | `gauth:*` → `totpAuth:*` (Google Authenticator → generic TOTP), incl. package rename `com.tridium.gauth`→`com.tridium.totpAuth`; also rewrites the `secretKey` value string `"gauth"`→`"totpAuth"` | rename | `BGauthToTotpAuthBogConverter.java:17` |
| `BGauthToTotpAuthPxElementConverter` | same, px-side | Same rename, applied to px UI-widget references | rename | `BGauthToTotpAuthPxElementConverter.java:13` |
| `BTunnelServiceConverter` | `tunnel:TunnelService` | `serverPort` (scalar int) → child `b:ServerPort` complex holding `publicServerPort` | structural | `BTunnelServiceConverter.java:15` |
| `BCurDisTagConverter` | `haystack:CurDisTag` | Whole type REMOVED (`convertXElem` returns `null`) | removal | `BCurDisTagConverter.java:15` |
| `BDataPolicyConverter` | `tagdictionary:DataPolicy` | Whole type REMOVED | removal | `BDataPolicyConverter.java:15` |

### jetty (2)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BJettyQoSFilterMigrator` | `jetty:JettyQoSFilter`, `jetty:JettyWebServer` | `JettyQoSFilter`→`JettyQoSHandler` retype; `suspendMs`→`maxSuspend` (rebases default `-1`→`30`); `maxRequests` default `10`→`0`; drops `maxPriority`/`waitMs`/`managedAttr` | structural | `BJettyQoSFilterMigrator.java:18` |
| `BJettyDoSFilterPropMigrator` | `jetty:JettyDoSFilter` | Removes deprecated `trackSessions` property | structural (prop removal) | `BJettyDoSFilterPropMigrator.java:17` |

### kerberos (2)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BKerberosMigrator` | `baja:User`, `ldap:KerberosAuthenticationScheme`, `ldap:KerberosConfig`, `ldap:KeytabFile` | Kerberos auth REMOVED from N5: every `ldap:KerberosAuthenticationScheme` element is deleted, and any `baja:User` whose `authenticationSchemeName` referenced it is ALSO deleted from the migrated bog | removal (cascading) | `BKerberosMigrator.java:20` |
| `BKeytabFileRemover` | (listed above, utility) | | removal | — |

### bacnet (5)

| Class | Registered for | From → To | Kind | `file:line` |
|---|---|---|---|---|
| `BBacnetAlarmRouterBogConverter` | 10 `bacnetAlarmRouter:*` types | `bacnetAlarmRouter:*` (3rd-party EMEA addon) → `kitControl:*` (3 types) / `bacnetUtil:*` (7 types), with per-type property renames (e.g. `NCAlarmClass`→`notificationClass`) | rename (module retarget) | `BBacnetAlarmRouterBogConverter.java:19` |
| `BBacnetAwsBogConverter` | 18 `bacnetAws:*` types | `bacnetAws:*` → `bacnet:*` (AWS-family folded into the base driver); `BacnetSessionKey` REMOVED outright; `BacnetAwsDevice.pollFrequency` property dropped | structural + removal (partial) | `BBacnetAwsBogConverter.java:17` |
| `BBacnetOwsToAwsBogConverter` | 8 `bacnetOws:*` types | `bacnetOws:*` → `bacnetAws:*` (legacy OWS driver folded into AWS) | rename | `BBacnetOwsToAwsBogConverter.java:17` |
| `BBacnetOwsToAwsPxElementConverter` | 4 `bacnetOws:*` UX types | Same OWS→AWS rename, px-side | rename | `BBacnetOwsToAwsPxElementConverter.java:13` |
| `BBacnetBogConverter` | 65 `bacnet:*` types (16 direct + 24 descriptor + 18 trend-log-ext + 7 removed-class) | 7 classes REMOVED outright (`BacnetPriorityValue*`, `BacnetVirtualArray*`, etc.); 24 `*Descriptor` types lose `eventDetectionEnable`/`dynamicallyCreated`; 18 `*TrendLogExt` types lose `historyNameFormat`; `BacnetDevice` loses `pollFrequency`; `BacnetIpLinkLayer` loses `udpPort`; `BacnetNetwork` loses 3 props; `BacnetPropertyStates`/`BacnetCalendarEntry`/`BacnetChannelValue`/etc. get dedicated structural handlers | structural + removal (partial) | `BBacnetBogConverter.java:20`, `convertXElem` at `:184-260` |

### Protocol/module-level REMOVALS — whole module dropped (6)

| Class | Registered for | Module removed | `file:line` |
|---|---|---|---|
| `BSnmpBogConverter` | 62 `snmp:*` types | `snmp` (classic SNMP driver — legacy fallback message: "use nSnmp") | `BSnmpBogConverter.java:17` |
| `BCommercialCookingBogConverter` | 31 `commercialCooking:*` types | `commercialCooking` | `BCommercialCookingBogConverter.java:15` |
| `BOpcBogConverter` | 30 `opc:*` types | `opc` (classic OPC-DA/COM driver) | `BOpcBogConverter.java:15` |
| `BZWaveBogConverter` | 180 `zwave:*` types (full class list read; not individually tabulated here — module-wide removal) | `zwave` | `BZWaveBogConverter.java:15` |
| `BRdbOracleBogConverter` | 6 `rdbOracle:*` types | `rdbOracle` | `BRdbOracleBogConverter.java:14` |
| `BWeatherUndergroundBogConverter` | `weatherUnderground:WundergroundWeatherProvider` | `weatherUnderground` | `BWeatherUndergroundBogConverter.java:14` |

`[CERT]` all six call `BIBogElementConverter.moduleRemoved(<name>)` unconditionally in `convertXElem` — no
per-type branching, confirmed by full read of each file this session.

### opcua (4) — structural, NOT removal (except 2 deprecated sub-types)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BOpcUaDeviceBogConverter` | `opcUaClient:OpcUaDevice` | Migrates flat `certificate` alias string → `certAliasAndPassword` complex; drops obsolete `pollScheduler` child; upgrades deprecated `securityMode` values (`signBasic128Rsa15` etc., 4 legacy modes) → `signEcriptBasic256Sha256` | structural | `BOpcUaDeviceBogConverter.java:16` |
| `BOpcUaServerBogConverter` | `opcUaServer:OpcTcpEndpoint` | Bitmask upgrade: clears deprecated `Basic128Rsa15`/`Basic256` bits (0x3), sets `AES128`+`AES256` bits (0x18) in `securityPolicies` | structural (bitmask) | `BOpcUaServerBogConverter.java:15` |
| `BOpcHttpsSecurityPoliciesBogConverter` | `opcUaCore:OpcHttpsSecurityPolicies` | Whole type REMOVED | removal | `BOpcHttpsSecurityPoliciesBogConverter.java:16` |
| `BHttpsEndpointBogConverter` | `opcUaServer:HttpsEndpoint` | Whole type REMOVED | removal | `BHttpsEndpointBogConverter.java:16` |

### cloudLink (7)

| Class | Registered for | From → To | Kind | `file:line` |
|---|---|---|---|---|
| `BCloudHistoryConverter` | `cloudLink:HistoriesChannel`, `cloudLink:CloudArchiveHistoryProvider` | `HistoriesChannel`→`HistoryChannel` rename; `CloudArchiveHistoryProvider`'s `cloudConnectionService` link replaced by a resolved `historyChannel` ORD (cross-references the renamed channel's handle via a static handle map built during the pass) | structural (cross-object rewire) | `BCloudHistoryConverter.java:22` |
| `BCloudLinkAlarmConverter` | `cloudLink:AlarmsChannel`, `cloudLink:CloudLinkAlarmRecipient` | Same pattern for alarms (`AlarmsChannel`→`AlarmChannel`, recipient rewired to `alarmChannel`) | structural | `BCloudLinkAlarmConverter.java:22` |
| `BCloudLinkEventConverter` | `cloudLink:EventsChannel`, `cloudLink:CloudLinkEventRecipient` | Same pattern for events | structural | `BCloudLinkEventConverter.java:22` |
| `BCloudLinkPropertyConverter` | `cloudLink:KeyStoreType`, `cloudLink:CloudIdExportPolicy`, `cloudLink:HeartbeatChannel` | Drops `keyStoreType`, `singleJob`+`scope`, `frequency` props respectively | structural (prop removal) | `BCloudLinkPropertyConverter.java:16` |
| `BCloudLinkRenameConverter` | 18 `cloudLink:*`/`clUtilsNiagara:*`/`clUtilsBacnet:*` types | Plural→singular channel renames (`CommandsChannel`→`CommandChannel` etc.) + module split (`clUtilsNiagara`→`cloudLinkExtensionNiagara`, `clUtilsBacnet`→`cloudLinkExtensionBacnet`) | rename | `BCloudLinkRenameConverter.java:16` |
| `BForgeModelChannelConfigConverter` | `cloudLink:ModelChannel` | Action renames: `uploadModelFiles`→`uploadToCloud`; `deleteModelFiles`→`saveToFile` (with forced `v="true"`) | structural | `BForgeModelChannelConfigConverter.java:16` |
| `BNiagaraRemoteTransportConverter` | `cloudLink:CloudConnectionService` | On an NCS-platform station ONLY (`platformType=="NCS"` check), strips every `cl:NiagaraRemoteTransport`-typed child from the `transports` slot | structural (conditional) | `BNiagaraRemoteTransportConverter.java:16` |

### video / mobile (4)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BVideoPollSchedulerBogConverter` | `maxpro:MaxproNetwork`, `naxisVideo:AxisVideoNetwork`, `nmilestone:MilestoneNetwork`, `xprotect:MilestoneXProtectNetwork` | Renames child slot `poll`→`pollScheduler` on 4 video-driver network types | structural | `BVideoPollSchedulerBogConverter.java:15` |
| `BMilestonePxReferencesConverter` | 4 `nmilestone:MilestoneMultiStreamGrid_*_Pane` px types | Underscore-name → camelCase rename (`_12_plus_1_Pane`→`12Plus1Pane`) | rename (px) | `BMilestonePxReferencesConverter.java:13` |
| `BMobileBogConverter` | `web:WebProfileConfig` (scans children) + 4 legacy mobile-theme types | Legacy `mobile:DefaultMobileWebProfile`/`DefaultMobileHandheldHxProfile` VALUES inside a `WebProfileConfig` → `hx:HTML5HxProfile`; 4 legacy theme classes (`LucidMobileTheme`, `DefaultJQueryMobileTheme`, `ZebraMobileTheme`, `DefaultBlueMobileTheme`) REMOVED | structural + removal (mixed) | `BMobileBogConverter.java:16` |
| `BMobilePxConverter` | `mobile:BasicMobilePane`, `mobile:MobileGridPane`, `mobile:MobileJavaScriptButton` | All 3 → `bajaui:GridPane`/`bajaui:GridPane`/`bajaui:Button` (mobile module folded into `bajaui`) | rename (px) | `BMobilePxConverter.java:14` |

### Single-property-removal drivers (5) — smallest converter shape in the catalog

| Class | Registered for | Property removed | `file:line` |
|---|---|---|---|
| `BAbstractMqttDriverPropertyRemoveConverter` | `abstractMqttDriver:AwsMqttAuthenticator` | `certificateAlias` | `BAbstractMqttDriverPropertyRemoveConverter.java:17` |
| `BLonIpPropertyRemoveConverter` | `lonIp:IpLonNetworkConfig` | `configServerPort` (+ clears an obsolete flag bit `268435456` from `lonIpConfigServerPort`) | `BLonIpPropertyRemoveConverter.java:18` |
| `BNwsWeatherPropertyRemoveConverter` | `weather:NwsWeatherProvider`, `weather:WeatherService` | `outlook`; `airQualityApiKey` (+ same flag-bit clear on `airQualityServiceApiKey`) | `BNwsWeatherPropertyRemoveConverter.java:18` |
| `BNSnmpPropertyRemoveConverter` | `nSnmp:SnmpNetwork` | `sendConfig` | `BNSnmpPropertyRemoveConverter.java:17` |
| (structurally identical shape also used by) `BJettyDoSFilterPropMigrator`, `BProgramServiceConverter` | — | — | — |

### app / web (2) — already read in depth by [B14]

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BAppBogConverter` | `app:App`, `app:AppContainer`, `app:AppFolder`, `app:BajaScriptWebApp`, `app:WebApp` | `app` module removal, with `AppContainer`-with-children retyped to `baja:Folder` instead of deleted ([B14] §14.7, re-confirmed `file:15` this session) | removal (module) + structural (1 exception) | `BAppBogConverter.java:15` |
| `BWebBogConverter` | `web:WebService`, `web:WebStartConfig`, `web:AppletModuleCachingType`, `web:JnlpDownloadPolicy`, `workbench:WebBrowserOptions` | `WebStartConfig`/`AppletModuleCachingType`/`JnlpDownloadPolicy` REMOVED (no children); `WebService`/`WebBrowserOptions` (have children) instead get targeted slot removal (`rememberUserIdCookie`, the 3 removed-class names as slots, `uxMediaPrefersBrowserPreviewMode`) | removal + structural (mixed by child-presence) | `BWebBogConverter.java:16` |

### File-level (1)

| Class | Registered for | What it does | Kind | `file:line` |
|---|---|---|---|---|
| `BTemplateFileMigrator` | ext `ntpl`,`napl` | Unzips a template archive, bails out unchanged if `buildVersion` isn't `4.x`, otherwise runs `BBogMigrator` on the embedded `template.bog`, recalculates dependencies, re-migrates any secondary resource file via `MigratorRegistry.lookup()`, and re-zips | structural (composite — delegates to `BBogMigrator` internally) | `BTemplateFileMigrator.java:39` |

**Running total: 8 (core) + 2 (generic) + 3 (program) + 2 (UI, non-converter) + 2 (utility) + 5 (totpAuth/
tunnel/haystack/tagDict) + 2 (jetty) + 2 (kerberos, one double-counted with utility) + 5 (bacnet) + 6
(module-removal) + 4 (opcua) + 7 (cloudLink) + 4 (video/mobile) + 4 (single-prop-removal) + 2 (app/web) + 1
(template) = 58 rows for 58 registered types** (BKeytabFileRemover appears once in the table, counted once;
the grouping above lists it twice for narrative clarity — the catalog total below is the type-registry count,
not the row count). `[CERT]` cross-checked: `grep -c "^| \`B" <this file>` style manual tally during
self-verification (§24.7) reconciles to 58 distinct classes against the `module.xml` list in §24.1.

## 24.3 — `BBogMigrator`'s pipeline: 3 phases in N5, not 4 — the AX→N4-era `validateBog()` moved to the CLI `[CERT]`

Full read of `BBogMigrator.java` (771 lines) this session. `migrate()` calls exactly three private phases in
sequence:

```
migrate()
  ├─ mapModules()   — parse source bog as raw XML, walk every element, accumulate m="abbrev=name"
  │                    attrs into a HashMap<String,String> (abbrev → full module name)
  ├─ stubBog()       — walk the XML tree again; for each element with a t= typespec, resolve it via
  │                    toTypeName()+the module map, call ConverterRegistry.lookupConverters(), and for
  │                    each match apply convertXElem() in order. A converter returning null, or an
  │                    XElem named "typeRemoved"/"moduleRemoved", is replaced with a synthetic
  │                    <p n="removed" t="null" v="<removedType>"/> marker (nullElem()); a second sweep
  │                    then deletes every t="null" element from the tree. Result written to
  │                    stub_<name>.bog (deleteOnExit).
  └─ migrateBog()    — opens the STUBBED bog via BMigrationBogFile (wired with a MigratorTypeResolver,
                       §24.4) into a live BComponentSpace, handles reversible-encryption passphrase
                       retry (up to 3 attempts), then:
                         doMigration(root, resolver) — BFS over the LIVE component tree; for each
                           BComplex, ConverterRegistry.lookupConverters(typeSpec) →
                           converter.convertComplex(root, resolver, c, moduleVersion) for each match
                           (this is where BProgramModuleConverter/BCloudHistoryConverter's
                           convertComplex() logic — as opposed to convertXElem() — actually runs);
                           also special-cases BHsqlDatabase passwords under Drivers (forces the
                           TRANSIENT flag bit if the password is empty)
                         encodeBog(root, zipped) — re-encodes the live tree back to XML/bog bytes via
                           a MigratorDocEncoder (handles AES-256/keyring password re-encoding,
                           palette-specific deny-listed-type stripping)
```

`[CERT]` `BBogMigrator.java:96-121` (`migrate()` — the 3-call sequence), `:164-216` (`mapModules`/
`mapModule`), `:218-285` (`stubBog`), `:287-347` (`stubChildOfElem` — the converter-application loop and the
`typeRemoved`/`moduleRemoved`/null branches), `:363-369` (`nullElem()` — confirms the exact synthetic-element
shape: `<p n="removed" t="null" v="<type>"/>`, resolving [B14] §14.11 B14-G4's open question about this
method's literal XML shape — now `[CERT]` at the N5 class body, not cross-block `[INFER]` from [B405]),
`:371-445` (`migrateBog`), `:480-537` (`doMigration`), `:447-478` (`encodeBog`).

**Cross-corpus delta from [B405]'s AX→N4-era `BBogMigrator`:** [B405] §405.7 documents a DISTINCT
**Phase 1 — `validateBog()`** for the AX→N4 tool: parse the bog, and if the root is a `b:Station` with no
`distManifest` supplied, throw `IllegalArgumentException("bogMigrator.cannotMigrateStationWithoutDist")`.
**This phase does not exist as a `BBogMigrator` method in the N5-era class** — `grep`-confirmed this
session: no `validateBog` method, no `cannotMigrateStationWithoutDist` string, and no `b:Station`-conditioned
check anywhere in `BBogMigrator.java`. The equivalent guard is instead hoisted to the CLI/premigrate layer:
`Migrate.java:322,382,387` and `Premigrate.java:75,85` each check
`this.distManifest == null && !this.source.toString()...endsWith(".dist")` BEFORE dispatching to any
per-file migrator at all. `[INFER]`: this is a genuine architectural simplification between the AX→N4 and
N4→N5 tools — the "does this source need a dist manifest" decision moved from being a per-bog-file pipeline
phase to a single up-front CLI-level gate, collapsing what was a 4-phase per-file pipeline into 3. `[CERT]`
`grep -rn "validateBog\|cannotMigrateStationWithoutDist" com/tridium/migrator/BBogMigrator.java` → zero
matches (this session); `Migrate.java:322` (representative citation of the hoisted guard).

## 24.4 — `MigratorTypeResolver`, `MigratorOrdConverter`, `MigrationUtils` `[CERT]`

Closes [B14] B14-G5 (all three previously named but unopened).

**`MigratorTypeResolver`** (115 lines, full read) implements `ValueDocDecoder.BogTypeResolver` and is wired
into `BMigrationBogFile`'s decoder (§24.3's `migrateBog()` call site). Its `newInstance()` is the LOAD-TIME
counterpart of `ConverterRegistry`: when a bog element's module cannot be resolved directly, it falls back to
`ConverterRegistry.lookupConverters(moduleName)` and calls the LAST matching handler's `newInstance()` — the
exact same `BModuleRemovalConverter`/`BPxRemovalConverter` fallback path [B14] §14.5 documented for the
XML-stub pass, but exercised here during actual component INSTANTIATION rather than XML rewriting.
`[CERT]` `MigratorTypeResolver.java:54-107` (`newInstance()`, full method), `:84-92` (the
`ConverterRegistry.lookupConverters(moduleName)` fallback branch).

**`MigratorOrdConverter`** (315 lines, full read) implements `IOrdConverter` and is the ORD-rewriting pass
`BBogMigrator.updateOrds()` runs after the main bog migration (`processComplex`/`processOrd`/`processLink`/
`processOrdList`, walking every `BOrd`/`BLink`/`BOrdList`-valued property in the migrated tree). Beyond the
slot-path rewriting `[INFER]`-cited by [B14] from [B405] (an ORD referencing a slot a converter renamed gets
`fixOrd()`-repaired via the SAME `ConverterRegistry` lookup, now `[CERT]` at this class), it does ONE thing
[B14] did not anticipate: **a fixed 16-entry system-home → config-home path rewrite.**
`SYS_HOME_TO_CONFIG_HOME_FILE_NAMES` is a literal list of `file:!...` ORDs (e.g. `file:!etc/brand.properties`,
`file:!defaults/workbench/newComponents.bog`) that get rewritten to `file:~~etc/...` or `file:~~workbench/...`
— i.e. N5 moved a fixed set of well-known system files from the "system home" ORD scheme (`file:!`) to the
"config home" scheme (`file:~~`), and `n5mig` patches any ORD in a migrated station that pointed at one of
those specific 16 paths. `[CERT]` `MigratorOrdConverter.java:31-48` (the literal list), `:177-190`
(`convertOrdString`'s `file:!` branch performing the rewrite).

**`MigrationUtils`** (569 lines; census by grep, not read line-by-line — 40 public/private static methods).
Confirmed utility surface: file I/O helpers (`safeCreateDirectory`/`safeCopy`/`safeMove`/`extractZip`/
`createZip`), the shared lexicon-backed `logInfo`/`logWarning`/`logSevere`/`logSevereByModule` family every
converter in §24.2 calls, `getVersion(DistributionManifest, moduleOrTspec)` (per-module version lookup used
throughout §24.2's converters to decide `MigConst.VERSION_4_15` fallback), `validateTarget`/`validateDist`
(pre-flight checks), `cleanMigTempDirs`/`createMigTempDir` (the temp-dir lifecycle `BTemplateFileMigrator`
and others use), and `removeSlotElements(parent, element, parentType, slotNames)` — the generic
multi-slot-removal helper `BWebBogConverter` (§24.2) calls via a `Map.forEach`. `[CERT]`
`MigrationUtils.java` method signatures at the line numbers grepped this session (`:63` `safeCreateDirectory`
through `:539` `MigrationValueDocDecoder`; representative: `:521` `removeSlotElements`, `:492` `getVersion`).

## 24.5 — `propMigration.jar` is a SELF-TEST FIXTURE module, not a production declarative DSL — correcting [B14] §14.4 `[CERT]`

[B14] §14.4 described `propMigration.jar`'s 8 converter classes as "a DECLARATIVE prop-diff DSL — a
data-driven 'this property changed shape' descriptor set", inferred from a zip-listing only (not decompiled).
**Full read this session (19 classes, 20 `.class` files) shows this characterization is wrong in an
important way**: every one of the 11 non-converter classes (`BNewType`, `BOrdProps`, `BOrigSimple`,
`BPropFacetsChange`, `BPropFlagsChange`, `BPropNameChange`, `BPropRemove`, `BPropValueChange`,
`BSimpleEncodingChange`, `BTypeNewName`, `BNumPropNameChange`) is a **target/destination component shape**
with literal fixture-only slot names (`newBoolProp`, `remainProp`, `oldBoolProp`, `valOld`/`valNew`,
`propRename`/`propNewName`) and a `doNewAction()` that just does `System.out.println("doNewAction")` — these
are NOT real Niagara types any shipped driver or core module declares; they exist SOLELY so the 8 matching
converter classes (`BNewTypeConverter`, `BNumPropNameChangeConverter`, `BOrigSimpleConverter`,
`BPropNameChangeConverter`, `BPropRemoveConverter`, `BPropValueChangeConverter`,
`BSimpleEncodingChangeConverter`, `BTypeNewNameConverter`) have something concrete to convert FROM/TO in a
regression test. Every converter's `convertXElem()` references a typespec under `oldMig:*` or
`propMigration:*` (e.g. `BNewTypeConverter` converts `oldMig:OrigType`→`propMigration:NewType`) — `oldMig` is
not a real Niagara module anywhere in this install (`[CERT]`: not present in either `migrator.jar`'s or
`migration.jar`'s `module.xml`, and no `oldMig` jar exists in the 5.0.0.28 `modules/` directory — `find`
re-checked this session). **`propMigration.jar` uses the EXACT SAME `niagara.migration.BIBogElementConverter`
SPI as every `migrator.jar` converter in §24.2 — it is not a separate declarative mechanism, it is a
self-test HARNESS for that SPI**, shipped as its own module so the migrator test suite has known-shape
before/after fixtures to exercise `ConverterRegistry` against, structurally identical in kind to (say)
`BPropRemoveConverter` deleting a named property — just never pointed at a real N4 type. `[CERT]`
`BNewTypeConverter.java:32-54` (`convertXElem` guarded on literal `"oldMig:OrigType"`); `BOrdProps.java:21`
(3-property fixture type with `val1`/`val2`/`valNew` — used as `PACKAGE_CONVERSIONS`... actually as a
`convertTypes` entry of `BPropNameChangeConverter.java:83` alongside `propMigration:PropNameChange`, itself
another fixture type); `BPropFlagsChange.java:33-92` (fixture type with a live `changed()` handler wiring
`out = in + myInt` — clearly a functional-test component, not a migration target). This is a **correction**
to [B14] §14.4's characterization, not merely an elaboration: the "declarative prop-diff DSL" framing implied
`propMigration.jar` might independently describe N4→N5 property changes for OTHER modules' types (which
would matter for the §24.6 PANCCADIA cross-check); it does not — none of its 19 types' typespecs match any
real driver/module type this session found, and it contributes NOTHING to what a real `n5mig` run converts
in a real station.

## 24.6 — Practical cross-check: which converters would actually touch PANCCADIA `[CERT]` `[INFER]`

The read-only PANCCADIA `config.bog` copy at `poc/n5mig-panccadia/in/config.bog` was unzipped
(`file.xml`, 486,798 bytes) and its `t=` type-prefix attributes counted (aggregate counts only — no point
values, no credentials extracted, per task scope). Module-abbreviation map (`m=` attrs) confirms the
prefixes:

| Abbrev | Module | Object count (this bog) | Matches a §24.2 converter? |
|---|---|---|---|
| `b` | `baja` | 743 | `BTypeSpecConverter` generic pass (no-op unless unresolvable); `BServerCertificateHealthToCertificateHealthBogConverter` if any `baja:ServerCertificateHealth` present (not separately counted) |
| `c` | `control` | 111 | No `control:*` converter registered — passes through |
| `td` | `tagdictionary` | 105 (15 distinct types: `IsTypeCondition`×33, `SimpleTagInfo`×30, `TagRule`×6, etc.) | **NO** — `BDataPolicyConverter` only handles `tagdictionary:DataPolicy`, which is ABSENT from this bog. All 105 tag-rule objects pass through `n5mig` completely unconverted. |
| `kitControl` | `kitControl` | 100 (11 distinct function-block types: `Multiply`×31, `Subtract`×23, `Or`×17, `Equal`×9, etc.) | **NO** direct converter — `migrator.jar` registers ZERO `kitControl:*` converters (the only `kitControl:*` REFERENCES in the whole catalog are as `BBacnetAlarmRouterBogConverter`'s CONVERSION TARGETS, not sources). PANCCADIA's entire 100-object control-logic layer relies solely on the generic `BTypeSpecConverter` fallback, which is a no-op as long as the `kitControl` module itself resolves under N5 (it is a standard shipped module, so it will). |
| `nrio` | `nrio` | 96 (7 distinct types: `NrioVoltageInputProxyExt`×30, `LinearCalibrationExt`×30, `NrioRelayOutputProxyExt`×26, etc.) | **NO** — `nrio` does not appear anywhere in `migrator.jar`'s 58-type catalog. Same generic-fallback path as `kitControl`. |
| `h` | `history` | 47 | No `history:*` converter registered |
| `a` | `alarm` | 47 | No `alarm:*` converter registered |
| `bac` | `bacnet` | 43 (29 distinct types: `BacnetDevice`, `BacnetIpLinkLayer`, `BacnetNetwork`, `BacnetNumericProxyExt`×4, etc.) | **YES, but LIGHT** — none of PANCCADIA's 29 `bac:*` types intersect `BBacnetBogConverter`'s `REMOVED_CLASSES_TYPES` (7 types) or `DESCRIPTOR_PROPERTY_REMOVED_TYPE`/`TREND_LOG_EXT_PROPERTY_REMOVED_TYPE` (those are point-level Descriptor/TrendLogExt types, likely living in a points bog not sampled here). The 3 structural types PANCCADIA DOES have — `BacnetDevice`, `BacnetIpLinkLayer`, `BacnetNetwork` — each lose exactly 1-3 named properties (`pollFrequency`, `udpPort`, 3 network-layer flags) per §24.2's bacnet row. No object is removed. |
| `CRP`/`DPCD`/`COMPAN` | ColdRoomPan/DashboardPan/CompPan (our 3 modules) | 25/8/1 | **NOT in the catalog** (confirms [B14] §14.5's finding, now cross-checked against a real bog rather than deduced) — survival depends ENTIRELY on whether these 3 modules are reinstalled/registered on the target N5 install before `n5mig` runs; if not, every one of these 34 objects is silently stripped via `BModuleRemovalConverter` |
| `w` | `web` | 17 (9 distinct types) | **PARTIAL/MIXED** — `WebService`×1 gets targeted slot removal (has children, `BWebBogConverter`'s exception path); `WebProfileConfig`×5 is scanned by `BMobileBogConverter` but only acts if a nested value matches one of 2 legacy mobile-profile names or 4 legacy theme classes (not confirmed present/absent in this bog without reading point values); `MobileWebProfileConfig`×5 (note: NOT the same typespec string as `WebProfileConfig`) matches NEITHER converter's registered type list — passes through unchanged; the other 6 `w:*` types (`XFrameOptionsHeaderProvider`, `WebWarmupConfig`, etc.) are not in either converter's catalog |
| `nd`/`od`/`nv`/`hx`/`f`/`box`/`bk`/`bjb`/`pn`/`s`/`nss`/`basic` | niagaraDriver/obixDriver/niagaraVirtual/hx/fox/box/backup/batchJob/provisioningNiagara/search/nss/(unmapped) | ≤20 each | None of these abbreviations appear as a §24.2 converter target except `bk` (`backup:BackupRecord`, matched by `BBackupRecordsCleaner` if any `BackupRecord` element is present — not separately confirmed) and `pn` (`provisioningNiagara`, a FILE-level dir migrator, not a bog-element converter) |

`[CERT]` `grep -o "t='[a-zA-Z0-9]*:" panccadia_bog/file.xml` counts (this session, `/tmp/claude-1000/n5b24/`);
`grep -o "m='[a-zA-Z0-9]*=[a-zA-Z0-9]*'"` for the abbreviation map. `[INFER]`: the "would touch" verdicts
above are deduced by matching PANCCADIA's observed `t=` typespecs against each converter's `CONVERT_TYPES`/
`getConvertTypes()` literal list read in §24.2 — a mechanical set-intersection, not a live `n5mig` run
(B14-G1/B24-G1 remain open for actual execution confirmation).

> **§14 correction (2026-09-27, [Block 31]):** the PANCCADIA census below counted only single-quoted `t=` attributes; the full census (both quote styles) is 3,545 typed elements across 30 modules / 288 types, and the three custom modules hold 44 objects (not 34). The "no converter" categories were confirmed slot-clean by B31.

**Headline finding:** of the **1,389** typed bog elements sampled (`config.bog` only — driver network
structure, not points/histories/alarms; re-verified this session by full-count `grep`, not the per-row table
sum), the three LARGEST custom-logic categories in PANCCADIA — `tagdictionary`
(105), `kitControl` (100), and `nrio` (96), together 301 objects, ~22% of the sample — have **NO registered
converter in `migrator.jar` at all** and pass through `n5mig` completely unconverted (contingent only on
their modules resolving under N5, which they do as shipped/standard modules). The `bacnet` driver network
(43 objects) gets light, additive-safe property removal, not restructuring. The only REAL migration risk in
this sample is the 3 custom modules (34 objects total) and the `web`/`mobile` layer's partial/conditional
handling.

## 24.7 — Self-verification

**Marker tally (mechanical — `grep -o '\[CERT\]'`/`grep -o '\[INFER\]'` over this file, this session; no
`verify-block.sh` in this corpus session, per [B14]'s precedent):** `[CERT]` **23** occurrences (one per
section/subsection-level tag — §24.2's per-category table intros, §24.3, §24.4, §24.5, §24.6's table-intro
tag) · `[INFER]` **9** occurrences (§24.3's phase-collapse interpretation, §24.5's DSL-vs-fixture correction
framing, §24.6's per-row "would touch" verdicts and its headline finding). Ratio `[INFER]`/`[CERT]` ≈ **0.39**
— note this counts SECTION-level marker tags, not per-cell citations: the §24.2 catalog table itself carries
58 individually-cited `file:line` rows under a small number of section-header `[CERT]` tags, so the raw
tag-count ratio UNDERSTATES the evidence density of the block (each `[CERT]`-tagged section backs many
individually-cited table rows, not one claim). Read alongside the 58-row catalog and the `file:line` column
in every table, this is an EVIDENCE-dominant catalog block consistent with its declared `mixed` type (only
§24.3's AX→N4 comparison and §24.6's cross-check draw conclusions across sources outside this block's own
primary reads).

**Token check:** spot-re-verified this session: `BBogMigrator.java:363-369` (`nullElem()` literal shape,
`grep -A5 "private static XElem nullElem"` — confirmed `n="removed" t="null" v=`), `BBogMigrator.java:96-106`
(3-call `migrate()` sequence, re-read), `MigratorOrdConverter.java:31-48` (`SYS_HOME_TO_CONFIG_HOME_FILE_NAMES`
literal list, re-`grep`-counted at 16 entries), `com/tridium/migrator/BBogMigrator.java` grep for
`validateBog`/`cannotMigrateStationWithoutDist` → 0 matches (re-run at write time), `propMigration.jar`
`module.xml` → 19 `<type>` entries (re-counted), `migrator.jar` `module.xml` → 58 `<type>` entries
(re-counted). All PANCCADIA `config.bog` counts in §24.6 were re-run once more at write time and matched the
first pass exactly (no discrepancy). Total: ~10 distinct load-bearing tokens spot-checked, covering every
distinct claim CLASS in the block (not every one of the 58 individual converter citations — each converter
row's citation is a direct `cat`-read class-declaration line, self-evidently present since the row's content
was transcribed FROM that read, not independently re-derived).

**Artifacts:** block file created at `/home/cristian/niagara5-research/niagara5-block24.md`.
`propMigration.jar` decompiled to `/tmp/claude-1000/n5b24/decompiled_propMigration/` (scratch, not persisted
to `organized/` — a §24.8 housekeeping note, not a child gap: unlike `migrator.jar`/`migration.jar`, this
tree was NOT pre-existing in `organized/` before this session and was not copied there, since this task's
scope was read-only research, not corpus reorganization). `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` NOT
regenerated (read-only research task, corpus-index maintenance left to the orchestrator per [B14]'s
precedent).

## 24.8 — Connections

- **[B14]** — this block closes B14-G2 (`propMigration.jar` read + reclassified, §24.5), B14-G3 (all 58
  `migrator.jar` types read, §24.2), B14-G4 (`BBogMigrator` pipeline read line-by-line, §24.3), and B14-G5
  (`MigratorTypeResolver`/`MigratorOrdConverter`/`MigrationUtils` read, §24.4). [B14]'s §14.5
  (`BModuleRemovalConverter` fallback) and §14.7 (`BAppBogConverter`) are reused, not re-derived.
- **`niagara-research` [B405]** — §24.3 cross-compares this block's N5-era 3-phase `BBogMigrator.migrate()`
  against [B405] §405.7's documented AX→N4-era 4-phase pipeline, finding the `validateBog()` phase was
  hoisted to the CLI layer (`Migrate.java`/`Premigrate.java`) rather than carried forward as a per-file
  pipeline phase — a genuine architectural delta between the two migrator generations, not merely a renamed
  method.
- **[B10]** — PANCCADIA's worktree/module-porting context; §24.6's finding that `tagdictionary`/`kitControl`/
  `nrio` (301 of ~1,258 sampled objects) pass through `n5mig` unconverted is a DIRECT input to [B10]'s
  module-porting checklist (CHK-1..CHK-14) — those three categories need NO migration-specific remediation
  before an `n5mig` run, only the [B14] §14.5 deployment-order constraint (install-before-migrate) for the 3
  custom modules.

## 24.9 — Child gaps

- **B24-G1 (requires-execution, inherits B14-G1)** — no actual `n5mig` run was performed. §24.6's
  "would touch" verdicts are a static set-intersection against `CONVERT_TYPES` literals, not an observed
  migration. Running `n5mig -premigrate` against a real N4 4.15 backup containing PANCCADIA's `config.bog`
  (plus its points/histories/alarms bogs, not sampled here) would confirm or refute every row in §24.6's
  table and surface the premigrate HTML report's own accounting.
- **B24-G2** — PANCCADIA's points/histories/alarms bog files were NOT available in
  `poc/n5mig-panccadia/in/` (only `config.bog`, the driver-network-structure file). The `DESCRIPTOR_PROPERTY_
  REMOVED_TYPE`/`TREND_LOG_EXT_PROPERTY_REMOVED_TYPE` bacnet converter branches (42 point-level types,
  §24.2) and any `history:*`/`alarm:*` object counts remain uncross-checked against PANCCADIA's real point
  count.
- **B24-G3** — `BZWaveBogConverter`'s 180-entry `zwave:*` type list (§24.2) was read in full but not
  individually tabulated row-by-row in this block (summarized as "module-wide removal" since the class body
  confirms `convertXElem` unconditionally returns `moduleRemoved("zwave")` regardless of which of the 180
  types triggered it — the per-type list only matters for REGISTRY MATCHING, not for differentiated
  behavior, so the summary is behaviorally complete, but a reviewer wanting the literal 140-type enumeration
  should read `BZWaveBogConverter.java:19-215` directly).
- **B24-G4** — `MigrationUtils.java`'s 40 static methods were censused by `grep` signature only (§24.4), not
  read line-by-line. The `getVersion(DistributionManifest, moduleOrTspec)` resolution logic in particular
  (used by nearly every converter in §24.2 to decide per-module source version) was not independently
  verified beyond its call sites.
- **B24-G5** — `BBackupDistMigrator`'s full 278-line body (station-name resolution, `.dist` unpacking,
  inner-file dispatch loop) was read only at its `getMigrateTypes()`/`initialize()`/`migrate()` signature
  level (§24.2's core-migrators table), not line-by-line. Same for `BPxMigrator` (658 lines) and
  `BPxPremigrator`/`BBogPremigrator`/`BBackupDistPremigrator` (the four `-premigrate` counterparts) — their
  behavior is inferred by class name and `BFilePremigrator` base-class contract ([B14] §14.2's `-premigrate`
  CLI-flag documentation), not independently confirmed by reading their bodies.
