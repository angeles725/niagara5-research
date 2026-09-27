# Block 40 — N5 system-property writers, nftables rule-hint provenance and firewall defaults

> **Scope**: Closes [Block 33]'s three self-opened child gaps against fresh N5 5.0.0.28 evidence. **B33-G3**:
> enumerate every caller of `SystemPropertiesUtil.setSystemProperty` (and raw `System.setProperty`) across the
> full decompiled corpus, with property key(s), value source, and station-user reachability per caller.
> **B33-G4**: trace `BServerPort.adapter` AND the `ruleHintOverride`/rule-hint string from their origin (slot,
> who can edit it, what permission is required) to the `nft` command line built by
> `NftablesFirewallProcessor.processRule`; evaluate the sanitization with the exact character allowlist; rule
> on whether injection is reachable and by whom. **B33-G5**: locate where `niagara.firewall.enabled` /
> `niagara.firewall.frontend` are set by default, searching the actual install tree (`defaults/*.properties`,
> `etc/*.properties`, `platform.bog`) and every module's packaged resources. Does **not** cover: a live
> `[CERT-hw]` reproduction on a JACE-class embedded-Linux platform (none is available in this corpus — the
> only install this session had file-system access to is a Windows Supervisor-class N5 5.0.0.28 install); a
> byte-for-byte diff of all 247 module jars' `.class` bytecode for a `setSystemProperty`/`System.setProperty`
> call site the source-level `grep -rl` sweep could have missed (source-level sweep only, matching [Block 33]'s
> own scoping caveat); or resolving definitively which concrete `BComponentSpace` subtype a live running
> N5 station's own in-memory tree instantiates (§40.2's `setRequiresValidation` finding is therefore partly
> `[INFER]`, named as such).
>
> Subject version: **N5 5.0.0.28 (Beta)** — same install as [Block 3]/[Block 8]/[Block 12]/[Block 33]
> (`etc/brand.properties:workbench.notice` Beta marker per [Block 3]), same JRE 25.0.4.7. N4 comparison
> baseline: `niagara-research` corpus B625 (`BServerPort`'s pluggable on-device-firewall architecture) and B27
> (N4's port/firewall/TLS mental model, §27.1.2/§27.2/§27.11).
>
> Sources (all local, read-only, opened fresh this session):
> - `/home/cristian/niagara5-research/organized/**` — the pre-existing full corpus decompile (252 submodules,
>   14,578 Java files per `module-navigator stats`, this session) — `grep -rln`/`grep -rn` swept for
>   `setSystemProperty`, `clearSystemProperty`, and `System\.setProperty` across every `*.java` under
>   `organized/`, then every hit file `Read` in full (not snippeted): `com/tridium/platform/BSystemPlatformService.java`,
>   `com/tridium/platform/tcpip/BTcpIpPlatformService.java`, `com/tridium/niagarad/servlet/TcpIpServlet.java`,
>   `com/tridium/workbench/shell/BGeneralOptions.java`, `com/tridium/nre/util/SystemPropertiesUtil.java`,
>   `com/tridium/sys/Nre.java`, `com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java`,
>   `niagara/firewall/BServerPort.java`, `com/tridium/sys/schema/ComplexSlotMap.java`,
>   `com/tridium/tunnel/BTunnelService.java`, `com/tridium/opcUaServer/BOpcUaServer.java`,
>   `com/tridium/systemDb/orient/BOrientSystemDb.java`, plus 14 further single-hit raw-`System.setProperty`
>   files listed in full in §40.1 (`niagara/net/BHttpProxyService.java`, `com/tridium/migrator/Migrate.java`,
>   `com/tridium/jx/browser/JxBrowserUtil.java`, `com/tridium/niagarad/NiagaraDaemon.java`,
>   `com/tridium/splash/ui/LoadingSplashScreen.java`, `com/tridium/nre/bootstrap/Bootstrap.java`,
>   `com/tridium/nre/security/SecurityInitializer.java`, `com/tridium/crypto/core/io/CoreCryptoManager.java`,
>   `niagara/test/BTestNgStation.java`, `niagara/test/TestHelper.java`,
>   `com/tridium/rdb/hsqldb/BHsqlDatabase.java`, `com/tridium/workbench/web/browser/fx/BFxWebBrowserImpl.java`,
>   `com/tridium/svg/batik/BSvgDecoder.java`, `com/tridium/gx/util/ScalingUtil.java`).
> - `python3 module-navigator/tools/module_nav.py callers SystemPropertiesUtil setSystemProperty` (this
>   session) — cross-checks the `grep` sweep against the pre-built callgraph index (`stats`: 20,549 class-index
>   entries) — independent confirmation of the same 4 callers.
> - Live install file-system read (this session, read-only): `/mnt/c/Program Files/Niagara/5.0.0.28/defaults/system.properties`
>   (dist default template), `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/etc/system.properties` (this
>   host's live config-home copy), `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/etc/platform.bog`
>   (confirmed `file`-typed "XML 1.0 document, ASCII text", not binary) — all `grep`/`cat` read in full this
>   session. Both are the concrete files `com.tridium.nre.util.NiagaraFiles.getSystemPropertiesPath()`/
>   `getSystemPropertiesDefaultPath()` resolve to (`NiagaraFiles.java:95-99`, re-read this session).
> - `python3 /home/cristian/niagara-research/tools/corpus-nav.py show 625` / `show 27` (this session) — outline
>   fetch, then `niagara-mental-model-bloque625.md:22-72` and `niagara-mental-model-bloque27.md:50-128` `Read`
>   verbatim (not corpus-nav's summary alone) for the N4 REMITTANCE baseline.
> - [Block 33] (`niagara5-block33.md` §33.5, §33.6, §33.7) — the parent block this closes gaps for.
>
> Method: full-tree `grep -rln`/`grep -rn` sweeps over `organized/` for the exact API names, `module_nav.py
> callers` as an independent cross-check, then a full `Read` of every hit file (not a snippet) — matching
> [Block 33]'s own method. Live-install file reads used `cat`/`grep -rn` over the two `system.properties`
> copies and `platform.bog`, plus a corpus-wide `grep -rln "niagara.firewall"` for §40.3's negative claim.
> Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device — highest
> (`sources/probes/...`) · `[CERT]` local primary source (`file:line`) · `[CERT-a]` REMITTANCE
> `niagara-research` block (secondary to this corpus, cited `file:line` inside the remitted `.md`) · `[INFER]`
> deduction not literal in any single cited line.
>
> Security/runtime layer. Direct child of [Block 33] §33.5/§33.6/§33.7 (closes **B33-G3**, **B33-G4**,
> **B33-G5**). Cross-corpus: `niagara-research` B625, B27.
>
> **Type:** mixed — §40.1-§40.3 are fresh evidence re-derived this session against N5 5.0.0.28; §40.4 draws
> `[INFER]` comparisons against PRIOR `niagara-research` corpus blocks (N4 baseline), the MIXED trigger per
> METHODOLOGY §11.

---

## 40.1 — B33-G3: every `setSystemProperty`/`System.setProperty` caller, and the boot-time file-reload loop that gives the write-path its real consequence `[CERT]`

**The 4 shipped callers of `SystemPropertiesUtil.setSystemProperty` — cross-checked two ways.** A `grep -rln
"setSystemProperty"` across all of `organized/` and an independent `module_nav.py callers SystemPropertiesUtil
setSystemProperty` run (loading the pre-built callgraph index, this session) agree on exactly 4 callers
(the wrapper's own file and the `clearSystemProperty` sibling method are the only other hits, not counted as
callers) `[CERT]`:

| Caller `class#method` | Property key | Value source | Station-user reachable? |
|---|---|---|---|
| `BGeneralOptions.apply` (`com/tridium/workbench/shell/BGeneralOptions.java:306,310`) | `niagara.lang` (fixed literal) | `this.getLocale()` — a `String` Property, `flags=2` (`TRANSIENT` only, not `READONLY`/`HIDDEN`), free-text field-width-8 facet (`BGeneralOptions.java:81-83`) | **Local Workbench client only** — this is `BUserOptions` (client-side General Options dialog), not a station component; writes to the LOCAL machine's own `system.properties` via the boot-loader §40.1's second half describes. No network/remote reach; requires the person already running Workbench on that machine. |
| `BSystemPlatformService.setBajaLocaleId` (`com/tridium/platform/BSystemPlatformService.java:1272-1273`, called from `doSavePlatformServiceProperties:909`) | `niagara.lang` (fixed literal) | `this.getLocale()` — station-side "System" platform-service Property, `flags=3` (`READONLY`+`TRANSIENT`, `BSystemPlatformService.java:220`) gated behind `allowLocaleUpdate`/`localeUpdated` (`:908,981-982`) | **Platform-daemon admin session** (Platform Administration "System" service, authenticated platform admin per [Block 8]'s daemon auth model) — not a generic station user action. |
| `BTcpIpPlatformService.doSavePlatformServiceProperties` (`com/tridium/platform/tcpip/BTcpIpPlatformService.java:240`) | `java.net.preferIPv6Addresses` (fixed literal) | `this.getSettings().getNiagaraUsesIpv6()` boolean — TCP/IP Setup platform-service settings | **Platform-daemon admin session** (TCP/IP Setup, network-settings save path, `:161-165` gates on `!getIsReadonly()`). |
| `TcpIpServlet.saveNetworkSettings` (`com/tridium/niagarad/servlet/TcpIpServlet.java:294`, called from `doUpdate:65,277` via `doGet:34-42`) | `java.net.preferIPv6Addresses` (fixed literal) | HTTP query param `niagaraUsesIpv6`, parsed `Boolean.parseBoolean(query.get("niagaraUsesIpv6","false"))` at `:79` | **Network-reachable, but gated**: `authenticate()` (`:47-63`) requires `DaemonAuthUtil.authAdmin(...)` whenever the request carries `update=` (the servlet's `useDefaultAuthentication()` returns `false`, forcing this custom path), and `doGet` separately requires a CSRF token match (`CsrfTokenUtil.verifyCsrfToken`, `:36`) unless `DebugServlet.debugEnabled`. So: admin-authenticated + CSRF-protected HTTP endpoint, not an unauthenticated one. |

**Net for B33-G3's core question ("can a non-super user or remote input set an ARBITRARY key?"): no, not through
any of these 4 shipped callers** — every one of them writes a single HARDCODED key literal (`niagara.lang` or
`java.net.preferIPv6Addresses`); only the VALUE is caller-influenced, never the key. `SystemPropertiesUtil`'s
own ungated arbitrary-key capability ([Block 33] §33.5) remains a LATENT capability of the exported class for
any module that adds `requires niagara.nre;` — this session's exhaustive sweep confirms no SHIPPED Tridium
module in the 247-jar corpus currently exercises it with an attacker-influenced key. `[CERT]` (scoped to the
source-level sweep named in the header caveat).

**The other 20 raw `System.setProperty` call sites — all fixed-key, and dominated by boot-time/local-process
config, except one that completes [Block 33] §33.5's persisted-file loop.** A separate `grep -rln
"System\.setProperty"` sweep (not through the `SystemPropertiesUtil` wrapper) returns 20 files `[CERT]`. 17 of
them are single-purpose, hardcoded-key, hardcoded-or-internally-derived-value, boot-time or core-subsystem-init
calls with no external input in the value and no `SecurityUtil.checkPermission`/`NiagaraPermission` gating any
of them (matching [Block 33] §33.1's verdict that the MECHANISM itself is ungated) — read in full this session,
none reachable from a station user action: `BHttpProxyService.java:317` (`jdk.http.auth.tunneling.disabledSchemes=""`,
fixed), `Migrate.java:265,300` (`niagara.migration`, fixed/derived, migration-tool-only), `JxBrowserUtil.java:223`
(`jxbrowser.native.input.enabled=false`, fixed), `NiagaraDaemon.java:215` (`NiagaraDaemon=true`, fixed) and
`:906` (`jdk.tls.useExtendedMasterSecret` ← a properties-file value, boot-time TLS tuning, not user input),
`LoadingSplashScreen.java:21` / `ScalingUtil.java:221` (`sun.java2d.uiScale=1`, fixed, client UI), `Bootstrap.java:117`
(fixed thread-factory classname), `SecurityInitializer.java:85,87,88` (fixed BouncyCastle/trust-store boot
config, already scoped by [Block 33] §33.5), `CoreCryptoManager.java:1343,1352` (fixed BC RSA test-iteration
toggle), `BTestNgStation.java:160,297` / `TestHelper.java:627` (test-harness-only, not shipped runtime —
`TestHelper.setOrClearSystemProperty` is a private test utility, no production caller), `BHsqlDatabase.java:752`
(fixed, embedded DB boot config), `BFxWebBrowserImpl.java:177` (fixed, JavaFX WebView boot config),
`BSvgDecoder.java:162` (fixed, Batik boot config), `BOrientSystemDb.java:364,365,367,381` (fixed keys;
`ORIENTDB_ROOT_PASSWORD` ← `getRootPassword()`, an internally-generated credential — all 4 calls wrapped in
`SecurityUtil.doPrivileged`, `:361-385`, embedded system-DB boot-time init, no external input).

**The 18th — `Nre.addToSystemProperties` — is the boot-time loader that turns [Block 33] §33.5's persisted
write into a REAL restart-time re-application, and answers its own `[INFER]`.** `Nre.loadSystemProperties()`
(`com/tridium/sys/Nre.java:785-787`) reads `NiagaraFiles.getSystemPropertiesPath()` — i.e.
`<config-home>/etc/system.properties`, THE EXACT FILE `SystemPropertiesUtil.setSystemProperty` persists
non-denylisted writes to per [Block 33] §33.5 — via `loadSystemProperties(File)` (`:789-797`) into a `Properties`
object, then calls `addToSystemProperties(systemPropertiesFile, props)` (`:801-838`, full method read this
session). For **every key** in that file's `Properties.stringPropertyNames()` (`:824`), UNLESS the key is in
`SystemPropertiesUtil.PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` (skip+warn, `:825-827`), the loop calls
`System.setProperty(key, props.getProperty(key).trim())` (`:834`) — a genuine ARBITRARY-KEY write loop, driven
entirely by file content. `Nre.boot(BootEnv)` (`:608-682`) — the single JVM-entry boot method shared by every
Niagara process (station, Workbench, platform daemon; `isStation` is decided later in the SAME method by
argument inspection, `:650-662`) — calls `verifySystemProperties()` (`:647`, see below) THEN `loadSystemProperties()`
(`:680`) unconditionally on every launch `[CERT]`. **This is the closure [Block 33] §33.5 flagged `[INFER]`**:
a value `SystemPropertiesUtil.setSystemProperty` persists to `system.properties` (any key not on the
27-entry native denylist — see correction below) genuinely DOES get re-applied to `System` properties on the
NEXT process restart, via this exact loop — not a hypothetical, a directly-read boot-time file-reload `[CERT]`.

**Two separate protection layers found around this loop, both narrower than a general permission check.**
(1) `hasWritePermissionsToSystemPropertiesFile()` (`:839-853`, an OS-level `FileLock.lock` probe, not a Niagara
permission) gates only whether COMMAND-LINE-supplied overrides of a SEPARATE, SMALLER 6-entry
`niagara.commandLinePropertyDenyList` (`niagara.export.preventCSVInjection`, `niagara.webbrowser.disable`,
`niagara.webbrowser.urlAllowList`, `niagara.baja.formatDenyList`, `niagara.baja.formatDenyListExclusions`,
`jdk.tls.rejectClientInitiatedRenegotiation` — the DEFAULT string literal, `:806-809`) get silently cleared
(`:810-818`) — this protects 6 SPECIFIC security-relevant keys from CLI override, not the general case. (2)
`verifySystemProperties()` (`:875-881`, called at `:647`, BEFORE the file load) is a `fatal()`-aborting boot
guard: if a native-list property (the 27-entry list) has BOTH a live value AND a `cmdline::`-prefixed shadow
value set, boot aborts outright — the ONLY unconditional, hard-fail protection found this session, and it is
scoped to command-line-supplied overrides of the native list specifically, not to `system.properties`
file-content edits or to `SystemPropertiesUtil.setSystemProperty` runtime calls (which only warn/skip for
native-list keys, `SystemPropertiesUtil.java:61-64`, per [Block 33] §33.5).

**Correction to [Block 33] §33.5: the denylist is 27 entries, not 24.** [Block 33] §33.5 stated "a 24-entry
hardcoded denylist". A fresh `awk`-range count of `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST`'s literal entries
(`SystemPropertiesUtil.java:19-49`, re-read and re-counted this session) returns **27** distinct string
literals (`niagara.dhcpd.adaptersEnabledFile`, `niagara.dhcpd.configurationFile`, `niagara.dhcpd.leaseFile`,
`niagara.filestore.niagara.symlinks`, `niagara.filestore.niagara_user.symlinks`,
`niagara.ieee8021x.configurationFilePattern`, `niagara.ieee8021x.pkiCertificatesDirectory`,
`niagara.ieee8021x.statusFilePattern`, `niagara.link.configurationFile`,
`niagara.platDataRecovery.activeDirectoryPath`, `niagara.platDataRecovery.chunkfsStatsPath`,
`niagara.platDataRecovery.geomPath`, `niagara.platDataRecovery.mountPath`,
`niagara.platDataRecovery.persistentDirectoryPath`, `niagara.platNtp.configurationFilePath`,
`niagara.platNtp.driftFilePath`, `niagara.platNtp.statisticsDirectoryPath`, `niagara.firewall.frontend.path`,
`niagara.use.snap.usermgr`, `niagara.wifi.accessPointConfigurationFile`, `niagara.wifi.allowListFile`,
`niagara.wifi.channelConfigurationFile`, `niagara.wifi.clientConfigurationFile`,
`niagara.wifi.configurationPropertiesFile`, `niagara.wifi.configurationStatusFile`,
`niagara.wifi.hostapdCliFile`, `niagara.wifi.wpaCliFile`) — `[CERT]`, this session's own count, not
hand-recalled. `[INFER]`: likely a simple miscount in the prior session rather than a version drift (both
blocks target the SAME install, `SystemPropertiesUtil.java` was not re-decompiled between sessions). Per
METHODOLOGY §11's de-escalation convention, this is recorded here as a correction, not silently fixed in
[Block 33] itself (out of this session's read-only "touch no other file" scope).

## 40.2 — B33-G4: `adapter` never leaves its literal default anywhere in the shipped corpus; `ruleHintOverride` has two DIFFERENT, inconsistent validators and the stricter one is structurally inert for its only 2 shipped callers `[CERT]`/`[INFER]`

**`BServerPort.adapter` — `READONLY`+`HIDDEN`, default `"any"`, and set to nothing else anywhere in 247
modules.** `@NiagaraProperty(name="adapter", type="String", defaultValue="any", flags=5)`
(`niagara/firewall/BServerPort.java:56`, `Property adapter = newProperty(5, "any", null)` at `:72`). Cross-
checked this session against `niagara/sys/Flags.java:9-12` (`READONLY=1`, `TRANSIENT=2`, `HIDDEN=4`,
`SUMMARY=8`): `flags=5` = `READONLY|HIDDEN` — the slot is BOTH hidden from and non-editable through the
standard Workbench property-sheet editor `[CERT]`. Public `setAdapter(String v)` exists (`:123-125`) and is
callable by any Java code holding a `BServerPort` reference, so the READONLY flag is a UI-editor restriction,
not by itself proof the value can never change (see §40.1's validation-path discussion for the deeper
mechanism). But a `grep -rn "\.setAdapter\("` across the WHOLE `organized/` tree returns 5 hits, and **none of
them is `niagara.firewall.BServerPort.setAdapter`** — all 5 are unrelated `setAdapter` methods on OTHER
classes with their own, differently-typed `adapter` concept (`BBacnetIpLinkLayer.java:1824`,
`BBacnetEthernetLinkLayer.java:262`, `BIpLonNetworkConfig.java:283` — link-layer network-interface selection;
`BWifiCommandArgs.java:55,66` — WiFi CLI argument builder) `[CERT]` (negative existence, scoped to the 247
modules' source-level `*.java` searched). **Every `BServerPort` instance in the shipped N5 5.0.0.28 corpus
therefore carries `adapter == "any"` for its entire lifetime** — which means `NftablesFirewallProcessor.processRule`'s
`else if (!"any".equals(rule.getAdapter()))` branch (`NftablesFirewallProcessor.java:91-93`, the unsanitized
`iifname <adapter> ` embedding [Block 33] §33.6 flagged) is **DEAD CODE in the current shipped product** — not
merely "bounded" as [Block 33] §33.6 put it, but never entered at all, because no code path ever gives
`adapter` a non-default value. `[CERT]` (positive: the flag/default/setter definitions; negative: the
zero-non-`niagara.firewall.BServerPort` `setAdapter` callers found this session).

**`ruleHintOverride` — `HIDDEN` but NOT `READONLY`, has its OWN `IPropertyValidator` with a STRICTER
character class than the one that actually gates the `nft` command line.** `@NiagaraProperty(name=
"ruleHintOverride", type="String", defaultValue="", flags=4)` (`BServerPort.java:57`, `flags=4`=`HIDDEN` only
— `:73`). `BServerPort implements IPropertyValidator` and its OWN `validateSet` (`:206-220`) rejects the
proposed value unless `isAlphanumeric()` (`:223-231`, `Character.isLetterOrDigit` ONLY — **no exception for
`.` or `$`**) — this is DIFFERENT from, and STRICTER than, `NftablesFirewallProcessor.isRuleHintValid`
(`NftablesFirewallProcessor.java:258-266`, `[A-Za-z0-9.$]` — dots and dollar signs explicitly allowed, cited
fresh this session, matching [Block 33] §33.6's citation). Exactly 2 shipped call sites set `ruleHintOverride`
to a non-empty value, and BOTH pass strings containing `.` (which `BServerPort.isAlphanumeric` would reject if
it ran): `BTunnelService.java:325,725` → literal `"TunnelService.serverPort"`, and `BOpcUaServer.java:614` →
`"OPCUA.server." + this.getName()` (the SECOND HALF is the component's own configurable NAME — station-config
write access, i.e. an engineer/admin with write permission to that OPC UA server component, could rename it to
inject characters, subject to whatever separate name-charset validation `BComponent` rename enforces —
**not traced this session**, → **B40-G1**).

**Why the stricter validator apparently never fires for these two calls — traced to source, one `[CERT]`
branch and one `[INFER]` branch.** `BServerPort.setRuleHintOverride(v)` calls
`this.setString(ruleHintOverride, v, null)` — `context=null` `[CERT]` (`BServerPort.java:132-134`, its only
generated setter body). `ComplexSlotMap.setString(Property,String,Context,boolean validate)` only invokes the
`IPropertyValidator` when `validate && setRequiresValidation(context)` (`ComplexSlotMap.java:1402` guarding the
same pattern shown at `:914,1010,1108,1206,1304` for the sibling `setInt`/`setBoolean`/etc. — full method
bodies read this session). `setRequiresValidation(Context)` (`:1799-1816`): with `context==null` it skips the
`context.getUser()`/`Context.forceValidate` branch entirely and falls to `BComponentSpace space =
this.getSpace(); if (space==null) return false;` then `if (space.isProxyComponentSpace()) return true;` then
`return space.getType().is(BOG_SPACE_TYPE_INFO)` (`BOG_SPACE_TYPE_INFO` resolved as `BTypeSpec.make("file",
"BogSpace")`, i.e. `com.tridium.file.types.bog.BBogSpace` — confirmed the sole class in the corpus matching
`class BogSpace`/`extends BogSpace`, `organized/file/vineflower/com/tridium/file/types/bog/BBogSpace.java`).
**`BOpcUaServer`'s `bServerPort` is a bare, unparented Java field — `private BServerPort bServerPort = new
BServerPort();` (`BOpcUaServer.java:212`), never registered via `newProperty(...)`** — so `getSpace()` on it
is `null` for its entire life, `setRequiresValidation` always returns `false`, and `isAlphanumeric` is
STRUCTURALLY UNREACHABLE for this call site `[CERT]` (no ambiguity: an unparented object has no space, full
stop). **`BTunnelService`'s `serverPort` IS a real frozen `Property` slot** — `public static final Property
serverPort = newProperty(0, new BServerPort(9973, IpProtocol.TCP), null)` (`BTunnelService.java:142`) — so it
DOES live inside the running station's own component tree, and whether `isAlphanumeric` fires for its
`setRuleHintOverride` call therefore depends on whether a LIVE, normally-running station's own in-process
`BComponentSpace` implementation `is()`-a `BBogSpace` TypeInfo — **this was not independently confirmed this
session** (would require opening the concrete space class a running `BStationSpace`/equivalent instantiates,
out of this session's scope) `[INFER]`: given `BBogSpace`'s name and package (`com.tridium.file.types.bog`,
alongside `isProxyComponentSpace()` being the OTHER branch that forces validation — i.e. the code is clearly
distinguishing "remote/Workbench-proxy-driven edit" and "file/bog-decode-driven edit" from plain internal
engine code acting on its own already-live components), the more likely reading is that a live station's own
runtime space is NEITHER a proxy space NOR a `BogSpace`, so `setRequiresValidation` returns `false` here too
and `BTunnelService`'s literal also passes unchecked by design (internal, Tridium-authored code is trusted not
to need its own property validator) — but this reading is **not** independently `[CERT]`-verified this
session, and is named as a gap → **B40-G2**.

**Net verdict for B33-G4 (adapter branch): CLOSED — not reachable, `[CERT]`.** The `adapter`/`iifname`
injection branch [Block 33] §33.6 flagged is dead code given the current shipped corpus; there is no
in-product path — operator, station-config, or remote — that ever sets `BServerPort.adapter` away from its
literal `"any"` default. **Net for the `ruleHintOverride` branch: NOT REACHABLE by the two Tridium-authored
callers found (structurally, for `BOpcUaServer`; with high confidence but `[INFER]`, for `BTunnelService`),
and BOUNDED even if it were** — the operative sanitizer that actually gates the `nft` command line is
`NftablesFirewallProcessor.isRuleHintValid`'s `[A-Za-z0-9.$]` allowlist, which rejects the shell/argv-splitting
characters (space, quote, semicolon, backtick, pipe) that would matter for the space-split `TextUtil.split(cmd,
' ')` argv construction ([Block 33] §33.6's own finding, re-confirmed this session — no `.`/`$`-based injection
into a DIRECT-exec (no shell) `ProcessBuilder` argv is meaningful, since neither character is an argv
delimiter). This is a **hypothesis-to-proven upgrade over [Block 33] §33.6's `[INFER]`** for the `adapter`
half (now `[CERT]` dead-code, not merely "bounded"), and a **new, narrower open question** for the
`ruleHintOverride` half (B40-G1/B40-G2) that [Block 33] did not surface at all.

## 40.3 — B33-G5: `niagara.firewall.enabled`/`niagara.firewall.frontend` are absent from every file this session had access to — negative, explicitly scoped to a Windows Supervisor install `[CERT]`

**Both live `system.properties` copies searched, zero hits.** `grep -n "firewall"` against
`/mnt/c/Program Files/Niagara/5.0.0.28/defaults/system.properties` (the shipped DIST TEMPLATE — every entry in
this file is commented out with `#`, by design, per its own header: "This file contains properties which are
loaded into `System.getProperties()` during NRE boot") and against
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/etc/system.properties` (this host's LIVE config-home copy,
the file `Nre.loadSystemProperties()` actually reads at boot, §40.1) both return **zero** matches for
`firewall` in any form `[CERT]` (full-file `cat` read this session; both files' complete content was read, not
grepped-only). Neither `niagara.firewall.enabled` nor `niagara.firewall.frontend` nor `niagara.firewall.frontend.path`
(the ONE firewall-related key that IS on the native denylist, per §40.1) appears, commented or live.

**Whole-install and whole-corpus sweep, zero hits.** `grep -rn "niagara.firewall\|firewall.enabled\|firewall.frontend"`
across the ENTIRE `/mnt/c/Program Files/Niagara/5.0.0.28/` install tree and the ENTIRE
`/mnt/c/ProgramData/Niagara/` tree (both, this session) returns zero matches anywhere — including
`platform.bog` (confirmed `file`-typed as plain ASCII/XML, not a binary format that could hide the string from
`grep`, `:1-2` command output this session). A parallel `grep -rln "niagara.firewall\|firewall.enabled\|firewall.frontend"`
across the FULL DECOMPILED `organized/` tree (247 modules' resources + Java) also returns **zero** files
`[CERT]` — the only two source lines in the entire corpus that reference these exact keys are
`BServerPort.java:341-362`'s own read of them (already cited by [Block 33] §33.7), confirming no OTHER module's
packaged resources, `.dist` template, or defaults sets them either.

**Reading this negative correctly: it is a Supervisor-install-scoped absence, not a universal one.** This
session's file-system access is limited to a Windows-hosted, Supervisor-class N5 5.0.0.28 install (the same
one [Block 3]/[Block 8]/[Block 33] used) — no JACE-class embedded-Linux platform image or distribution package
was available to search `[CERT]` (access-scope statement, not a finding). Combined with [Block 33] §33.7's
`[CERT]` finding that `BServerPort.FirewallHolder`'s static initializer defaults `useFirewall =
Boolean.getBoolean("niagara.firewall.enabled")` to `false` when the property is absent, and that `nft` itself
only exists as a binary on Linux: **on THIS install, the on-device `nft` firewall backend is off by
construction** (`[CERT]`, the property being entirely unset means `Boolean.getBoolean` returns `false`) — a
Windows Supervisor never reaches `NftablesFirewallProcessor` at all, consistent with (not contradicting) [Block
33] §33.7's "Linux-only in practice, not by an OS branch in code" finding. Which platform's distribution
DOES ship these two properties set to `true`/`nft` remains **open** — `[INFER]` per [Block 33] §33.7's own
naming (a JACE-class embedded-Linux platform's own `system.properties` default is the likely candidate, given
`nft`'s Linux-kernel-only nature, but no such platform's install files were reachable this session) →
carried forward as **B40-G3** (unchanged from [Block 33]'s B33-G5, now with the negative search space
explicitly widened to the WHOLE install tree + WHOLE decompiled corpus, not just the two Java trees [Block 33]
searched).

## 40.4 — N4 baseline, re-read from REMITTANCE `niagara-research` B625/B27: the same pluggable-processor
architecture, and N4's own default posture on its `pf` equivalent `[CERT-a]`/`[INFER]` (cross-corpus)

REMITTANCE `niagara-research` B625 (`niagara-mental-model-bloque625.md:32-45`, re-read verbatim this session):
N4's `BServerPort` used the IDENTICAL pluggable-processor pattern N5 kept — `PfFirewallProcessor` (OpenBSD/QNX
`pf`), `NullFirewallProcessor` (no-op), or `ConcurrentFirewallProcessor` (serializing wrapper) — selected the
same way (a static field resolved at class-init), with B625's own `[INFER]` reading: "on an embedded controller
with `pf` (the QNX JACE) the rules are pushed to the OS packet filter... on a Windows/Linux supervisor the
`NullFirewallProcessor` applies — N4 does NOT manage the host firewall there" `[CERT-a]`. This is the SAME
platform-dependent posture §40.3 finds for N5 on its own Windows Supervisor install (Null there too, by
`niagara.firewall.enabled` simply being unset) — `[INFER]`: the ARCHITECTURAL DEFAULT ("supervisor-class
installs don't manage the host firewall; only the embedded/JACE-class platform's own image turns the
on-device processor on") appears to have carried over from N4 to N5 unchanged, even though the concrete
processor class (`pf`→`nft`) and the selection mechanism's OBSERVABLE SURFACE (N4: a compiled/platform-branch
selection per B625's own uncertainty vs. N5: two plain `System` properties per [Block 33] §33.7's `[CERT]`
finding) differ — this reading is **not** independently confirmed against N4's actual selection code this
session (REMIT-only), consistent with B625's own `[INFER]` hedge on the SAME question.

REMITTANCE `niagara-research` B27 (`niagara-mental-model-bloque27.md:50-128`, re-read verbatim this session)
corroborates from the operational side: §27.2 catalogs the SAME N4 `BServerPort`-backed listening-port
inventory with `publicServerPort`/`localServerPort` and `adapter` slots (§27.1.3's `javap`-verified 4-slot
anatomy — matching N5's identical 4 `@NiagaraProperty` slots found in §40.2, `[CERT-a]`), and §27.1.3's own
prose already flags the OS-firewall-touching risk in N4 terms: *"el método privado `updateFirewallRules()`
indica que Niagara intenta gestionar reglas firewall del host OS... en Supervisor Windows el servicio
niagarad.exe tiene privilegios para tocar Windows Firewall vía netsh. En Linux requiere CAP_NET_ADMIN o sudo"*
(`niagara-mental-model-bloque27.md:81`) — the SAME `RuntimeExecPermission`-gated-but-caller-bypassed shape
[Block 33] §33.6 found for N5's `nft` exec (`niagara.nre` module universally bypasses
`PermissionManager.checkPermission`) plausibly has an N4-side analogue in this `netsh`/`CAP_NET_ADMIN`
mechanism — **not traced in either corpus this session**, `[INFER]`, named but not pursued (out of this
block's B33-G3/G4/G5 scope).

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block40.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script output):
```
== verify-block: niagara5-block40.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 11  (adj 9)
   [CERT-live] 1
   [CERT] 31  (adj 30)
   [CERT-doc] 7
   [CERT-web] 1
   [CERT-a] 8  (adj 7)
   [INFER] 23  (adj 20)
-- ratio -- [INFER]/[CERT*] = 20/55 = 0.36
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  sources/probes/...
   extern  BBacnetEthernetLinkLayer.java:262, BBacnetIpLinkLayer.java:1824, BFxWebBrowserImpl.java:177,
   BGeneralOptions.java:81-83, BHsqlDatabase.java:752, BHttpProxyService.java:317, BIpLonNetworkConfig.java:283,
   BOpcUaServer.java:212, BOpcUaServer.java:614, BServerPort.java:132-134, BServerPort.java:341-362,
   BServerPort.java:57, BSvgDecoder.java:162, BSystemPlatformService.java:220, BTunnelService.java:142,
   Bootstrap.java:117, ComplexSlotMap.java:1402, JxBrowserUtil.java:223, LoadingSplashScreen.java:21,
   NftablesFirewallProcessor.java:115-121, NftablesFirewallProcessor.java:258-266, NftablesFirewallProcessor.java:91-93,
   NiagaraDaemon.java:215, NiagaraFiles.java:95-99, ScalingUtil.java:221, SystemPropertiesUtil.java:19-49,
   SystemPropertiesUtil.java:61-64, TestHelper.java:627, com/tridium/niagarad/servlet/TcpIpServlet.java:294,
   com/tridium/platform/BSystemPlatformService.java:1272-1273, com/tridium/platform/tcpip/BTcpIpPlatformService.java:240,
   com/tridium/sys/Nre.java:785-787, niagara-mental-model-bloque27.md:50-128, niagara-mental-model-bloque27.md:81,
   niagara-mental-model-bloque625.md:22-72, niagara-mental-model-bloque625.md:32-45,
   niagara/firewall/BServerPort.java:56, niagara/sys/Flags.java:9-12
   (each individually `extern` — "not in target: beautified-temp / decompiled / snapshot — not script-verifiable" —
   the script's own per-line output is the literal enumeration; condensed here)
   resolved 0 of 38
   WARN    resolved 0 of 38 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```
**Reading the raw vs. adjusted split, and the self-referential-inflation pattern [Block 15]/[Block 33]'s own
self-verify sections name.** The `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/`[CERT-web]` raw hits all come from
THIS Self-verify section's own explanatory prose (and the header's marker-legend line) quoting marker NAMES
while describing the tally — not from any live-hardware, live-remote-service, downloaded-document, or
official-web claim this block actually makes (the header's explicit "does not cover a live `[CERT-hw]`
reproduction" statement, and zero `sources/probes/`, `sources/*.pdf`, or dated-URL citations anywhere in the
block, are the ground truth: real counts for all four are 0). Editing this very paragraph to explain the FIRST
run's inflation quoted more marker names and pushed the count up again on re-run (8→11 `[CERT-hw]`, 1→7
`[CERT-doc]`, 0→1 `[CERT-live]`/`[CERT-web]`) — the exact chase-your-tail loop [Block 33]'s self-verify
describes ("re-running the script after adding this very explanatory paragraph pushed the count up again...
between drafts"). Per METHODOLOGY §11 ("the number reported above is the FINAL run's literal output, taken as-is
rather than chased to a fixed point"), the numbers in the fenced block above ARE that final run, not further
chased. The `[CERT]` (31→30 adj) and `[CERT-a]` (8→7 adj) counts, by contrast, held stable across both runs —
these are the block's real evidence tally: **30 `[CERT]` + 7 `[CERT-a]` = 37 real evidence claims**, against
**20 real `[INFER]`** — ratio 20/37 ≈ 0.54 (the script's own reported 0.36 uses its broader `[CERT*]`
denominator of 55, inflated by the quoted-name residue above; the 0.54 reading, restricted to the two marker
categories this block actually asserts, is the one to trust, and it sits at-or-above the ~0.5 threshold
METHODOLOGY §11 names for an EVIDENCE block). This is read as expected rather than alarming for two reasons
stated at each `[INFER]`'s point of use: (1) §40.2's `BTunnelService` branch and §40.4's whole section are
honestly-scoped `[INFER]`s this session explicitly could NOT resolve further without opening additional
classes outside this session's budget (named as **B40-G2**/**B40-G4** and left open, not glossed over), and
(2) §40.4 is a cross-corpus REMIT-comparison section by nature (MIXED block type, declared in the header) — an
`[INFER]` synthesizing across [Block 33]/B625/B27 is the EXPECTED shape for that section, not a sign this
session ran out of NEW evidence to gather in §40.1-§40.3 (which resolved 3 of the 4 sub-questions outright —
the 4th, B33-G5, closed as a WIDER, not weaker, negative).

**Declared per METHODOLOGY §11's decompiled-tree rule**: all 38 `file:line`-shaped citations resolve `extern`
— they point into `organized/**/vineflower/**` (the pre-existing decompiled tree, predating this session, same
as [Block 33]'s citations) plus 2 REMITTANCE `niagara-research` `.md` citations
(`niagara-mental-model-bloque625.md`, `niagara-mental-model-bloque27.md`) plus 1 `sources/probes/...` token
(quoted from the marker-legend template line, not a real probe citation this block makes) — all `extern` by
design, matching [Block 33]'s own convention; citation gate = inline token-verify below, not the script's
file-resolution.

**Inline token-verify**: every `file:line` citation above points at a file this session `Read` in full (not
`grep`-snippeted) this session, cross-checked against the `grep -rl`/`grep -rn` sweep that located it — zero
citations reused verbatim from [Block 33]'s text without an independent re-open this session (the 3 citations
into `SystemPropertiesUtil.java`/`NftablesFirewallProcessor.java`/`BServerPort.java:341-362` that [Block 33]
also cites were each independently re-read and re-`grep`-confirmed this session, not copied). Spot-check
tokens independently re-`grep`-confirmed present (whitespace-normalized) this session: `setSystemProperty`
(4 shipped-caller files + `SystemPropertiesUtil.java` + `Nre.java` NOT calling it directly — confirmed it calls
raw `System.setProperty` instead, a distinct token deliberately re-checked), `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST`
(27-count re-verified via `awk`-range + `grep -c` this session, not hand-counted), `isAlphanumeric` (both
`BServerPort.java` occurrences), `isRuleHintValid` (`NftablesFirewallProcessor.java`), `flags = 5` / `flags = 4`
/ `READONLY = 1` / `HIDDEN = 4` (`BServerPort.java` + `Flags.java`), `setRequiresValidation` /
`BOG_SPACE_TYPE_INFO` (`ComplexSlotMap.java`), `bServerPort = new BServerPort()` (`BOpcUaServer.java`, confirmed
NOT a `newProperty(...)` call — the "unparented field" claim), `niagara.firewall` (confirmed ABSENT via 3
independent `grep -rn`/`grep -rln` sweeps: both live `system.properties` files, the whole install tree, and the
whole `organized/` tree). Token-verify: **≈30 distinct load-bearing tokens** confirmed present (or confirmed
ABSENT, for the negative-existence claims, per METHODOLOGY §3's symmetric-opening-obligation rule) in their
cited source this session, zero hand-recalled from [Block 33]'s text.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block40.md`. Per the caller's
explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and
backlog re-classification are deliberately NOT performed this session — left to the orchestrator, matching
[Block 33]'s own convention.

## 40.x — Child gaps opened

- **B40-G1** — Trace `BComponent`'s station-config RENAME path (what charset a component NAME is restricted
  to when an engineer renames it in Workbench/BQL) to determine whether `BOpcUaServer.getName()` — concatenated
  into `ruleHintOverride` at `BOpcUaServer.java:614` — could ever contain a character `NftablesFirewallProcessor.isRuleHintValid`
  (`[A-Za-z0-9.$]`) would reject, and if so what happens to that OPC UA server's firewall rule (silently
  dropped, per `NftablesFirewallProcessor.java:115-121`'s warn-and-`return`) (§40.2).
- **B40-G2** — Open the concrete class a LIVE, normally-running N5 station's own `BComponentSpace` instantiates
  (not a proxy space, not an offline bog-file decode) and confirm whether `.getType().is(BOG_SPACE_TYPE_INFO)`
  is true or false for it — this is the one fact §40.2's `BTunnelService.setRuleHintOverride("TunnelService.serverPort")`
  reachability verdict rests on and could not resolve this session (§40.2).
- **B40-G3** — (carried forward from B33-G5, negative search space now widened) `[CERT-hw]`/`[CERT-doc]`:
  obtain a JACE-class embedded-Linux N5 platform's own install/distribution files and search THEM for
  `niagara.firewall.enabled=true`/`niagara.firewall.frontend=nft` defaults — not available to this session's
  Windows-Supervisor-only file-system access (§40.3).
- **B40-G4** — Trace N4's `netsh`/`CAP_NET_ADMIN` host-firewall-touching mechanism (`niagara-mental-model-bloque27.md:81`'s
  own un-traced prose claim) for a possible `RuntimeExecPermission`-gated-but-caller-bypassed analogue to
  [Block 33] §33.6's N5 finding — REMIT-only, not opened in either corpus this session (§40.4).

## 40.x — Connections

- **[Block 33] §33.5/§33.6/§33.7** — direct parent; this block closes **B33-G3** (the caller enumeration, now
  complete + the boot-time file-reload loop that gives the persisted write real consequence), **B33-G4** (the
  `adapter` branch is now `[CERT]` dead code, not merely "bounded"; the `ruleHintOverride` branch surfaces a
  NEW, narrower open question [Block 33] did not see), and **B33-G5** (same negative result, search space
  widened from 2 Java trees to the whole install + whole 247-module corpus).
- **[Block 8] §8.5/§8.7** — grandparent via [Block 33]; unchanged by this block, cited only for the
  `RuntimeExecPermission`/`niagara.nre`-bypass mechanism §40.4 draws an N4 parallel to.
- **REMITTANCE → `niagara-research` B625** — N4's identical pluggable-processor `BServerPort` firewall
  architecture, the direct predecessor [Block 33] §33.7 already used; this block adds the "same
  platform-dependent DEFAULT posture, not just the same class shape" reading (§40.4).
- **REMITTANCE → `niagara-research` B27** — N4's `BServerPort` 4-slot anatomy (matching N5's identical slots
  found in §40.2) and its own un-traced `netsh`/`CAP_NET_ADMIN` host-firewall-permission prose, the source of
  **B40-G4** (§40.4).
