# Block 101 — N5 install-layout capstone: the `jar-cache/<module>/` extraction mechanism traced to its source, two `com.tridium.json` writer classes' real call-site census, the firewall IP-protocol conversion boundary pinned to one method, `security/licenses/conf/` confirmed genuinely N5-new, Atlas hardware identified as an ARM64 snap-packaged platform, Honeywell-under-Tridium licensing shown feature-name-generic, and `systemDb`/`javac` embedded-tier gaps narrowed against their scope limits

> Research closing/narrowing nine child gaps opened by six earlier blocks, all under this wave's theme
> (N5 install layout, jar-cache, platform/hardware and licensing packaging). Covers: **B95-G2**
> ([Block 95] §95.11 — "Census and trace the newly-discovered `jar-cache/<module>/` deployment-directory
> family… what build-side Gradle mechanism populates it, whether it is `unterjar`'s actual deployment
> target… and whether it resolves other blocks' unlocated-third-party-jar gaps"); **B95-G3** ([Block 95]
> §95.11 — "Trace real call sites of `com.tridium.json`'s other two classes, `pretty.PrettyJSONStringer`
> and `quick.QuickJSONWriter`"); **B95-G5** ([Block 95] §95.11 — "Trace whether `BServerPort`'s
> wire-level socket setup actually converts `niagara.firewall.BIpProtocolEnum`… into
> `niagara.nre.security.IpProtocol`… at a single well-defined boundary, or whether the two enums'…
> domains are kept in sync by convention only"); **B34-G6** ([Block 34] §34.x Child gaps — "Confirm
> whether `security/licenses/conf/` is genuinely N5-only or simply an N4-corpus documentation gap (the
> `niagara-research` corpus's own `nre.jar`/native decompile scope for this exact class was not checked
> this session)"); **B5-G1** ([Block 5] — "Confirm whether `HsmManager`/HSM support is dropped from N5
> proper or only from this stock Beta vs. the OEM N4 baseline; requires either a non-OEM N4 baseline or a
> later/OEM N5 build to compare against"); **B13-G5** ([Block 13] §13.9 — "Confirm what Tridium's
> 'Atlas' hardware target (`platHwScanAtlas`, §13.4.4/§13.5) physically is — a specific new JACE/host
> SKU — via web or shipped install docs; currently only the naming-convention parallel with the 7 retired
> `platHwScanJ*` modules is measured, not the hardware identity itself"); **B13-G6** ([Block 13] §13.9 —
> "Investigate whether the Honeywell-branded-content-under-Tridium-vendor pattern (§13.5,
> `cloudLinkForge`/`cloudLinkHonSbp`) extends to licensing/feature-gating… does a stock N5 install
> require a Honeywell-specific license feature to unlock these modules' function, or are they gate-free
> by default?"); **B58-G3** ([Block 58] §58.x Child gaps — "Whether `systemDb`/`orientSystemDb` is
> absent from this Niagara4.14 OEM profile because it is unlicensed/unused, or because this specific OEM
> distribution never provisions it at all, is unresolved… Requires either a `[CERT]` decompile-level
> check of a license-feature flag against this specific install, or a `[CERT-hw]` Workbench-UI check of
> whether an `orientSystemDb` service component is even offered for addition on this station"); **B32-G3**
> ([Block 32] §32.9 Child gaps — "Confirm `bin/javac` is physically present in the distributed image of
> an *embedded*-tier N5 device (JACE), not just declared 'JDK 25 Standard Edition' by the doc (§32.1) —
> static census only, no device image inspected this session"). Does **not** cover: a client-specific
> determination of B58-G3 for the PANCCADIA station itself — this wave's own SOURCES instruction forbids
> reading client station files, so this block answers only the *general* license-gate mechanism, not
> which branch applies to that particular OEM install; an embedded/JACE-tier device-image inspection for
> B32-G3 (none was available/in-scope this session — see §101.9's explicit note on a locally-present but
> client-associated SD-card image that was deliberately **not** opened); a commercial SKU/marketing name
> for the Atlas hardware target (B13-G5's physical/architectural identity is closed, its public product
> name is not, per §101.6's `[CERT-web]` negative search).
>
> Subject version: **N5 5.0.0.28 (Beta)**. Decompiled tree at `/home/cristian/niagara5-research/organized/`
> (`vineflower/` primary, `fallback/` excluded from all census greps below). Live N5 install (read-only):
> `/mnt/c/Program Files/Niagara/5.0.0.28` (engineering binaries/JRE) and its sibling config-home tree
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/` (`jar-cache/`, `modules/`, `security/` —
> the actual runtime-populated directories referenced throughout this block; [Block 95] already
> established this config-home split). N4 comparators: `/home/cristian/niagara-research/organized`
> (4.14 decompiled corpus) and its `sources/decompiled/nre-ext/` tree (Block 477's full Vineflower
> decompile of a Honeywell-OEM 4.14 `bin/ext/nre.jar`, sha256
> `33aaaac5186e851d6d0773fb8df1ebe4970e18c34312b8e73ea697d15e560415`, 437 `.java` files); and
> `/mnt/c/PowerB/PowerB-4.15.3.28` (read-only, a **second, independent** OEM install — vendor PowerB, not
> Honeywell — used in §101.5 purely as a cross-check jar, never decompiled or read past `unzip -l`/manifest
> level). Census method throughout: `find organized -iname '*.java' -exec grep …' {} +` (never a shell
> glob), per METHODOLOGY's documented under-match trap; every negative-existence claim below states the
> exact completed sweep it rests on. One WebSearch call was made (§101.6, no other web/MCP-doc lookups
> this session). No client station file (PANCCADIA or otherwise) was opened at any point this session —
> confirmed by this session's own command history, not merely asserted.
> **Secrets discipline**: `security/`, `licenses/`, and `LicenseAccessKey`/`checkLicense` code paths are
> cited by structure (class names, method names, file paths, feature/vendor STRING LITERALS that are
> themselves feature *names*, not secret values) only — no license key, HostId value, or credential
> byte is reproduced anywhere in this block.
> Markers (canonical list, METHODOLOGY §3): `[CERT]` decompiled-source `file:line` · `[CERT-hw]` live/
> installed-file evidence this session (`ls`/`unzip`/`sha256sum`/`stat` against the read-only install
> paths above — corpus convention per [Block 34]/[Block 58]/[Block 6], not limited to disassembly) ·
> `[CERT-web]` one search this session · `[CERT-doc]` not used this block · `[INFER]` deduction.

---

## 101.1 — B95-G2 CLOSED: `jar-cache/<module>/` is the runtime extraction cache for exactly the 22 module jars that embed third-party libraries under `LIB-INF/` — populated by `NModuleModuleFinderFactory`, byte-identical to its `LIB-INF` source, on-demand at module-path resolution `[CERT-hw]`/`[CERT]`

**Full re-census confirms [Block 95]'s 22 subdirectories, unchanged**: `ls
/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/jar-cache/` this session lists exactly the same 22
names [Block 95] §95.11 recorded (`oauth2`, `saml`, `totpAuth`, `apachePoi`, `commonsIo`, `email`, `gx`,
`jodaTime`, `jsonSmart`, `jsonToolkit`, `rdb`, `rdbHsqlDb`, `rdbSqlServer`, `abstractMqttDriver`,
`axvelocity`, `cloudLink`, `commonsCompress`, `devkit`, `opcUaCore`, `snmpLibs`, `svgBatik`, `test`,
`xprotect`) `[CERT-hw]`.

**Exact source-side match, closing "which modules use it".** Counting `LIB-INF/*.jar` entries inside
every one of the 247 module jars under `.../config/5.0.0.28/modules/` (`unzip -l "$f" | grep -c
"LIB-INF/.*\.jar$"` per jar) finds **exactly 22 module jars with a non-zero count — the identical 22
names as the jar-cache directory listing, one-to-one, with matching per-module jar counts** (e.g.
`xprotect.jar` has 26 `LIB-INF/*.jar` entries and `jar-cache/xprotect/` holds 26 files;
`oauth2.jar` has 5 and `jar-cache/oauth2/` holds 5) `[CERT-hw]`. This is a completed, closed population
comparison (247 jars, all counted, not a sample) — the family is fully explained: `jar-cache/<module>/`
exists for a module if and only if that module's own jar ships third-party dependencies under `LIB-INF/`.

**Byte-identity proof that jar-cache is a copy of LIB-INF, not an independent deployment target.**
`unzip -p modules/oauth2.jar LIB-INF/nimbus-jose-jwt-10.0.2.jar | sha256sum` →
`960b978a6cd6cbc3319648adc73959789f6742a2bf1e8dd0c843dbc91624218a`, identical to `sha256sum
jar-cache/oauth2/nimbus-jose-jwt-10.0.2.jar` `[CERT-hw]`. This directly answers the gap's "as
opposed to/in addition to `LIB-INF`" question: `LIB-INF` is the packaged SOURCE (inside the Niagara
module jar); `jar-cache/<module>/` is the runtime-EXTRACTED cache of it — not an alternative.

**The populating mechanism, traced to a single method.**
`organized/baja/vineflower/com/tridium/sys/module/NModuleModuleFinderFactory.java:297-328`
(`readModule`) detects, per module-path entry, whether the `.jar` filename is reached through a
non-default `FileSystem` (`module.getFileSystem().provider().getScheme()` ≠ `"file"` — i.e. the entry
is itself a nested-zip path *inside* another jar's own zip filesystem, exactly what a `LIB-INF/*.jar`
entry is when the module jar is opened as a `ZipFileSystem`). Java's own module system cannot build a
`ModuleFinder` directly over such a nested-zip path, so `readModule` calls
`getCachedJar(module, fileName, cacheDir, attrs)` (`:612-635`), which: resolves `parentModuleName` from
the containing filesystem's own filename (`oauth2.jar` → `"oauth2"`), creates
`jar-cache/<parentModuleName>/` if absent, and — under a lock, with an mtime-based staleness check
(`targetModified >= sourceModified` skips the copy) — does `Files.copy(module, cachedJar,
StandardCopyOption.REPLACE_EXISTING)` before finally opening the now-real on-disk file as a module
`[CERT]`. This resolves "how it is resolved at boot": lazily, on the first module-path scan that needs
to read one of these third-party jars as a module (station/Workbench startup, or on-demand module load),
not by an eager boot-time sweep.

**"Build-side Gradle mechanism" question resolved by elimination, not directly observed**: no Gradle
build script is present in this decompiled/live-install corpus (`etc/gradle`/`etc/m2` under the N5 home
hold only wrapper/repo config, not this module's own build), so the actual build-time step that PACKS
third-party jars into `LIB-INF/` (presumably an `unterjar`-family Gradle task, per the gap's own
phrasing) was not directly read this session — but the RUNTIME side (this section) is now fully
`[CERT]`-closed, and it is the runtime side, not the build side, that the gap's "how is it resolved at
boot" sub-question actually needed.

**Feeds [Block 12]'s B12-G5.** `jar-cache/totpAuth/core-3.5.4.jar`'s manifest declares
`Automatic-Module-Name: com.google.zxing`, `Bundle-SymbolicName: com.google.zxing.core`,
`Bundle-Version: 3.5.4` `[CERT-hw]` (`unzip -p … META-INF/MANIFEST.MF`) — the third-party library behind
`totpAuth` is **ZXing 3.5.4** (Apache-2.0 barcode/QR encode-decode library), which directly explains what
a TOTP-enrollment UI (B12-G5's "`BTotpAuthAuthenticatorFE`… enrollment UI wiring") would need it for:
rendering the enrollment QR code. `jar-cache/saml/` holds `java-saml-core-2.9.0.jar` + `xmlsec-4.0.4.jar`
(OneLogin's `java-saml` + Apache Santuario XML-Security, both by top-level-package inspection of their
own manifests) — the SAML IdP library named in B12-G6, not independently traced end-to-end into a
servlet flow this session (that remains B12-G6's own open scope, only its underlying library is now
named).

## 101.2 — B95-G3 CLOSED: `QuickJSONWriter` is the corpus's dominant fast-JSON writer (35 files, 110 occurrences); `PrettyJSONStringer` has exactly one real caller, `tagdictionary`'s pretty-printed export `[CERT]`

Whole-corpus census (`find organized -iname '*.java' -exec grep …`, `fallback/` excluded):
`import com.tridium.json.quick.QuickJSONWriter` resolves in **35 distinct files** across `cloudLink`,
`cloudLinkForge`, `cloudLinkHonSbp`, `cloudLinkNcs`, `cloudLinkAzure`, `box`, `history`, `webChart`,
`seriesTransform`, `bacnet`, `analytics`, `tagdictionary`, `smartTableHx`, `niagaraDriver`, `web`,
`uxBuilder`, `workbench` — **110 total token occurrences** (import + construction + subclassing)
`[CERT]`. Two representative resolutions: `organized/history/vineflower/com/tridium/history/util/HistoryUtil.java:7,135`
(`JSONWriter jsonWriter = QuickJSONWriter.make(out);`) and
`organized/box/vineflower/com/tridium/box/json/BoxWriter.java:3,10`
(`public class BoxWriter extends QuickJSONWriter implements JSONString`) `[CERT]`.

`import com.tridium.json.pretty.PrettyJSONStringer` resolves in exactly **one file** — **4 total token
occurrences** (all within that one file) `[CERT]`:
`organized/tagdictionary/vineflower/com/tridium/tagdictionary/util/ExportUtil.java:3,73` —
`JSONStringer jsonStringer = new PrettyJSONStringer(2);` inside `exportToJson(BTagDictionary dictionary,
BJsonFile file, …)`, a human-readable (2-space-indent) tag-dictionary export-to-file feature `[CERT]`.

**Answer to the gap**: `QuickJSONWriter` is the corpus's default/near-universal JSON output path for
HTTP responses, RPC payloads, and cloud message bodies; `PrettyJSONStringer` is a narrow, single-purpose
pretty-printer used only for one human-facing file-export feature. No third call-site category exists
for either class in this corpus — this is a closed population (110 + 4 = 114 total occurrences, all
individually attributable to one of the two classes' own defining files plus the 36 caller files named
above).

## 101.3 — B95-G5 CLOSED: the `BIpProtocolEnum` ↔ `IpProtocol` conversion is one package-private switch method, called from exactly one place — firewall-rule construction, not socket bind — refuting "convention only" `[CERT]`

`organized/baja/vineflower/niagara/firewall/BIpProtocolEnum.java:54-65` defines the single conversion
point: a package-private `static IpProtocol make(BIpProtocolEnum protocol)` that explicit-switches on
`protocol.getOrdinal()` (`0→TCP`, `1→UDP`, `2`/`default→TCP_AND_UDP`) `[CERT]`. This is a genuine,
single, well-defined shared-source-of-truth boundary — not "kept in sync by convention only" as the gap
speculated.

**Its only two call sites, both in `BServerPort.updateFirewallRules()`**:
`organized/baja/vineflower/niagara/firewall/BServerPort.java:281,286` — constructing an `InputRule` (or
`NoOpRule` when the firewall is disabled) that is handed to the platform's native firewall processor
(`com.tridium.nre.firewall.nft.NftablesFirewallProcessor`, seen importing the same `IpProtocol` type)
`[CERT]`. A corpus-wide census of every `getIpProtocol()` call site (`find organized -iname '*.java'
-exec grep -l 'getIpProtocol()'`) resolves to exactly **5 files, all firewall-package classes**
(`FirewallRule.java`, `NullFirewallProcessor.java`, `NftablesFirewallProcessor.java`, `BServerPort.java`,
`FirewallRulesPage.java`) `[CERT]` — zero hits in any socket/listener-setup class (`BFoxService`,
`BWebService`, jetty package, etc.). This is a completed, closed sweep: the conversion exists **only**
to build native OS firewall rules (which port/protocol combination to open), never to select a socket
type at bind time.

**Correction to the gap's own framing (not an earlier block's claim — the gap's phrasing itself).**
"`BServerPort`'s wire-level socket setup" does not describe what was found: `BServerPort` never binds a
socket itself; its subclasses (`BWebService`, `BFoxService`) construct default port values directly with
the plain `IpProtocol` enum literal (`new BServerPort(80, IpProtocol.TCP)` —
`organized/web/vineflower/niagara/web/BWebService.java:84,86,170,174`; `new BServerPort(1911,
IpProtocol.TCP)` — `organized/fox/vineflower/com/tridium/fox/sys/BFoxService.java:99,101,189,193`
`[CERT]`), which the `BServerPort(int, IpProtocol)` constructor converts the OTHER direction —
ordinal-based, not switch-based — via `this.setIpProtocol(BIpProtocolEnum.make(protocol.ordinal()))`
(`BServerPort.java:150-158`) `[CERT]`. So there are two directions, two different implementation
strategies (an explicit, reorder-safe switch one way; a fragile ordinal-index assumption the other way,
though both enums' declared orders happen to agree today), and the actual conversion USE is
firewall-rule bookkeeping, not wire-level socket setup.

## 101.4 — B34-G6 CLOSED: `security/licenses/conf/` (and its `AuthenticatedLicenseRetrievalUtil`/`LicenseAccessKey` mechanism) is genuinely N5-new — N4's own fully-decompiled `nre.jar` has no `license` sub-package at all `[CERT]`

N5's `com.tridium.nre.license.AuthenticatedLicenseRetrievalUtil` (`organized/_bin-ext/nre/vineflower/com/tridium/nre/license/AuthenticatedLicenseRetrievalUtil.java`)
manages a `KEY_RING_ALIAS = "com.tridium.licensing.LicenseAccessKey"` XML file
(`getLicenseAccessKeyFile`/`readLicenseAccessKey`/`createLicenseAccessKeyFile`) `[CERT]` — this is the
class [Block 34] named as the likely populator of the live install's `security/licenses/conf/<hostid>/`
directory ([Block 6] §6.7/§6.8).

**N4's own `nre.jar` was already fully decompiled by [Block 477]**, independently of this session
(`niagara-mental-model-bloque477.md:11-12`: "full Vineflower decompile of `bin/ext/nre.jar`… 437 `.java`
files", sha256 `33aaaac5186e851d6d0773fb8df1ebe4970e18c34312b8e73ea697d15e560415`) — the exact corpus
scope [Block 34]'s own gap text said "was not checked this session". Listing that decompile's
`com/tridium/nre/*` package directories this session
(`find sources/decompiled/nre-ext -type d -ipath '*com/tridium/nre*'`) finds `platform`, `subscription`,
`bootstrap`, `security` (+ `io`/`policy`/`km`/`provider`), `protocol` (+`program`), `auth`, `di`,
`diagnostics`, `syslog`, `jetty` (+`log`/`rc`/`rc/auth`/…), `firewall` (+`pf`), `util` (+`tuple`) — **no
`license` package anywhere in this list**, and a direct file search
(`find sources/decompiled/nre-ext -iname '*license*'`) returns zero matches under `com/tridium/nre/`
`[CERT]`. Whole-N4-corpus search (`find organized -iname '*.java' -exec grep -l
'com.tridium.nre.license\|licenses.conf\|licenses/conf'`) also returns zero hits `[CERT]`, reproducing
[Block 6] §6.7's own `grep -rn "security/licenses/conf"` zero-hit result independently.

**Answer to the gap**: this is not an N4-corpus decompile-scope gap (the exact class's containing
library WAS fully decompiled, by a named prior block, sha256-verified) — the `com.tridium.nre.license`
package and the `security/licenses/conf/` storage tier it backs are **genuinely absent from N4**, i.e.
**N5-new**, closing [Block 6]'s own still-open **B6-G2** ("`conf/` is left as an open, unexplained
on-disk artifact") at the same time: `conf/` is the physical target of `AuthenticatedLicenseRetrievalUtil`'s
`getLicenseAccessKeyFile()`, a class that simply did not exist before N5.

## 101.5 — B5-G1 NARROWED (not fully closeable within this session's sources): `HsmManager`/HSM is present, identically, in TWO independent OEM N4 builds and absent from a whole-corpus N5 sweep — strong evidence of a real N5 drop, but no non-OEM Tridium-stock N4 build was available to fully rule out an OEM-only artifact `[CERT]`

Whole-N5-corpus case-insensitive search (`find organized -iname '*.java' -exec grep -li 'hsm'`) returns
**three files**, all confirmed false positives on inspection: `BTagDictionaryService.java` (`searchSmart
Dictionaries…` — substring, not "hsm" as a word), `DaemonFileUtil.java` (`pathsMatch` — substring), and
an unrelated LON Helvar lighting-device resource file (`Ahsm1.lnml`, a fixture model name) `[CERT]`. Zero
genuine `hsm`/`Hsm`/`HSM` hits anywhere in the N5 5.0.0.28 decompiled corpus — a completed whole-corpus
sweep, not an unchecked absence.

**N4 comparator #1 (Honeywell OEM, 4.14, [Block 477]'s decompile)**:
`sources/decompiled/nre-ext/javax/baja/nre/security/HsmManager.java` (interface: `DEFAULT_HSM_TYPE =
"none"`, `hasHsmEngine()`, `getHsmEngineClassName()`, default `hasHsm() { return
!"none".equals(getHsmType()); }`) and `sources/decompiled/nre-ext/com/tridium/nre/security/HsmManagerImpl.java`
(implementation) both exist as real, fully-decompiled classes `[CERT]`.

**N4 comparator #2 (PowerB OEM, 4.15.3.28, a DIFFERENT vendor and a different minor version, never
decompiled by any prior block — checked at the jar-listing level only this session)**:
`unzip -l "/mnt/c/PowerB/PowerB-4.15.3.28/bin/ext/nre.jar" | grep -i hsm` →
`javax/baja/nre/security/HsmManager.class` and `com/tridium/nre/security/HsmManagerImpl.class`, both
present `[CERT-hw]`.

**Answer to the gap**: the fact that two INDEPENDENT OEM vendors (Honeywell and PowerB), on two
different N4 minor versions (4.14 and 4.15.3.28), both ship the identical `HsmManager`/`HsmManagerImpl`
class pair, is strong cross-corroborating evidence that this is standard Tridium `nre.jar` code, not an
artifact either OEM independently injected — which shifts the balance decisively toward "N5 genuinely
dropped HSM support" rather than "the N4 baseline used for comparison happened to be OEM-augmented".
This NARROWS rather than fully CLOSES the gap only because the gap's own stated closure condition
("requires either a non-OEM N4 baseline or a later/OEM N5 build") is literally unmet — neither a
vanilla Tridium-branded N4 install nor a later N5 beta was available this session; both comparators used
here are still OEM builds, just from two different, mutually-corroborating vendors.

## 101.6 — B13-G5 CLOSED (architecture/identity) / open (commercial name): Atlas is a real Tridium platform target — ARM64, its Niagara core shipped as an installable Linux **snap** package, contrasted with Titan's AM335x/ARMv7 + traditional OS/JRE/NRE split `[CERT]`/`[CERT-web]`

`organized/docSource/backup/niagara/backup/BBackupService.java:3169-3170` declares
`ATLAS_PART_NAME = "ATLAS"` and `TITAN_PART_NAME = "TITAN"` — literal platform **model part names**,
compared against `op.platform().getModelPart().getPartName()` (i.e. the same field Workbench's Platform
Administration view shows as the connected device's "Model") at `:1873-1875` `[CERT]`.

**Physical/architectural identity, from the same file's backup-manifest special-casing logic
(`:1890-1990`)**:
- `TITAN_OS_NAME_SUFFIX = "-n4-titan-am335x-hs"` (`:3155`) — Titan's OS part name is suffixed for the TI
  **Sitara AM335x** SoC family (ARMv7-A), in its **`-hs`** (hardware-security-fused) silicon variant
  `[CERT]`.
- `ATLAS_SNAP_TRIDIUM_NIAGARA_NAME = "snap-tridium-niagara-arm64"` (`:3159`) — Atlas's Niagara core ships
  as an installable Linux **snap** package named for **ARM64** `[CERT]` — a different CPU architecture
  and a different OS-packaging model from Titan.
- For Atlas specifically (not Titan): the backup manifest captures the OS dependency as version-less
  ("OS version created as an amalgam of snap parts", `:1896-1908`), skips capturing a separate VM/JRE
  dependency entirely ("captured implicitly in nre-core part", `:1940-1945`), and marks NRE/installable
  snap-part dependencies with a `COMMISSIONING_SOLVER` filter so they "cannot be upgraded without
  nre-config" / "can't be upgraded by DistFileInstaller" (`:1931-1936,1977-1981`) `[CERT]` — i.e. Atlas's
  OS/JRE/NRE stack is a single commissioning-tool-managed snap bundle, not the ordinary
  OS-part+VM-part+NRE-part trio a ProgramData-style N5/N4 distribution installs on other platforms.
- Corroborating bajadoc hits (`niagara_help.py find "Atlas"`): `com/tridium/platHwScan/ports/BWifiPort.txt`
  — "BWifi port represents the Wi-Fi adapter on the TITAN / ATLAS"; `com/tridium/platHwScan/optionCards/BOptionModule.txt`
  — "TITAN/ATLAS Hardware Scan so the property sheet says 'Option Module' instead"; a dedicated
  `com/tridium/platHwScanAtlas/BAtlasBoard.txt` class exists `[CERT-doc]` (bajadoc, ground-truth-adjacent
  per this wave's SOURCES tiering) — confirming Atlas, like Titan, is a physical controller board with
  its own Wi-Fi adapter and hardware-scan/option-card model, not a virtual or cloud-only target.

**Commercial name still unconfirmed — `[CERT-web]` negative result.** One `WebSearch` this session for
`Tridium Niagara "ATLAS" hardware platform snap-tridium-niagara-arm64 JACE` returned no page naming
"Atlas" as a Tridium hardware product (only generic JACE-8000/Niagara-4 marketing pages) `[CERT-web]` —
consistent with Atlas being an unreleased/unannounced platform as of this N5 5.0.0.28 Beta, but not
itself proof of that; the search is a negative result, not a confirmation of non-existence in the
market.

**Answer to the gap**: the "hardware identity itself" the gap asked for — beyond the
`platHwScanJ*`-retirement naming parallel — is now established at `[CERT]` level: Atlas is a real
ARM64-based Tridium controller board, packaged and serviced as Linux snaps rather than the traditional
OS/VM/NRE split, with integrated Wi-Fi, positioned alongside (successor to, on this architecture
evidence) the AM335x/ARMv7-based Titan. Its public marketing/SKU name is not established this session.

## 101.7 — B13-G6 CLOSED: Honeywell-branded `cloudLinkForge`/`cloudLinkHonSbp` carry NO Honeywell-specific license feature — they gate on the same generic `tridium:cloudLink`/`tridium:cloudLinkConnect` features as their non-Honeywell siblings `[CERT]`

Both modules' own `module.xml` declare `vendor="Tridium"` while their `description` names Honeywell
products (`cloudLinkForge`: `description="Honeywell Forge Cloud Connectivity"`; `cloudLinkHonSbp`:
`description="CloudLink module for Honeywell Smart Buildings Platform"`) `[CERT-hw]` (`unzip -p` against
the live install's `modules/cloudLinkForge.jar`/`cloudLinkHonSbp.jar`, cross-checked against
`organized/cloudLinkForge/vineflower/META-INF/module.xml`/`organized/cloudLinkHonSbp/vineflower/META-INF/module.xml`
`[CERT]`) — reproducing [Block 13] §13.5's vendor-vs-description pattern exactly.

**A complete search of BOTH modules' own decompiled source trees** (`grep -rniE
'checkFeature|getFeature\(|LicenseNotFoundException|FeatureNotLicensedException|honeywell'` over
`organized/cloudLinkForge` and `organized/cloudLinkHonSbp` in full) finds **zero Honeywell-named license
feature or checkFeature/getFeature call anywhere in either module** `[CERT]` — the only "Honeywell"
string hits are platform-type/URL/hostname string LITERALS used for cloud registration (e.g.
`"HoneywellSBP"`, `sc.honeywellforge.com`), not license-gate code.

**The actual license gates live one level up, in the shared parent `cloudLink` module, and are
generically named**: `organized/cloudLink/vineflower/com/tridium/cloudLink/BCloudConnectionService.java:209,214`
— `Sys.getLicenseManager().getFeature("tridium", "cloudLink")` /
`Sys.getLicenseManager().getFeature("tridium", "cloudLinkConnect")`; `organized/cloudLink/vineflower/com/tridium/cloudLink/util/LicenseLimit.java:58`
— the same `"tridium","cloudLink"` feature, checked for attribute limits (e.g. SMA-expiration,
`organized/cloudLink/vineflower/com/tridium/cloudLink/util/LicenseLimit.java:89`); `organized/cloudLink/vineflower/com/tridium/cloudLink/channel/BHistoryChannel.java:315`
— `Sys.getLicenseManager().getFeature("tridium", "historyArchive").check()` `[CERT]`. All three feature
names (`cloudLink`, `cloudLinkConnect`, `historyArchive`) are **vendor-generic Tridium features shared by
every `cloudLink*` sibling module** (Forge, HonSbp, Ncs, Azure alike) — none is Honeywell-scoped.

**The one Honeywell-adjacent runtime read found is a brand-identity attribute, not a gate**:
`organized/cloudLinkHonSbp/vineflower/com/tridium/cloudLink/honsbp/msg/ForgeHttpNameplateInfoHandler.java:330`
— `Nre.getLicenseManager().getFeature("Tridium", "brand").get("brandId")`, sent as a
`"tridium-brand-id"` property in the device's cloud nameplate/registration payload `[CERT]` — this reads
the SAME generic `"tridium:brand"` feature's `brandId` attribute every N5/N4 install's license already
carries (per the corpus's own prior OEM-branding findings), used here only to tell the Honeywell Forge
cloud what brand it is talking to, not as an access-control gate on the module's own function.

**Answer to the gap**: a stock N5 install does **not** need a Honeywell-specific license feature to use
`cloudLinkForge`/`cloudLinkHonSbp` — any install already licensed for the generic `tridium:cloudLink`/
`cloudLinkConnect` features (the same license any `cloudLink*` sibling needs) can use them; they are
**gate-free with respect to Honeywell branding specifically**, extending [Block 6]'s `LicenseManager
.checkFeature` gap (`B6-G3`) with a concrete negative result for this module family.

## 101.8 — B58-G3 NARROWED to its general mechanism (client-specific determination remains explicitly out of scope this wave): `systemDb`/`orientSystemDb` IS license-feature-gated by design — `BOrientSystemDb.checkLicense()` requires `tridium:systemDb` with its `orientDb` attribute set — identically in N4-4.14 and N5 `[CERT]`

**Scope note, stated up front**: [Block 58]'s own gap text frames this around "this Niagara4.14 OEM
profile" — the PANCCADIA station Block 58 examined. This wave's own SOURCES instruction explicitly
forbids reading client station files (`config.bog` etc. of PANCCADIA or other clients) this session, so
**the client-specific half of this gap (which branch applies to that particular install) is not, and
cannot be, answered here** — only the general architecture question ("is this a real license gate at
all, or would the module simply never provision the feature structurally") is investigable from the
decompiled software alone, and is answered below.

Both N4-4.14's and N5's `com.tridium.systemDb.BSystemDb` (the base `systemDb` runtime type) declare a
`checkLicense()` HOOK that is an empty no-op in the base class itself —
`organized/systemDb/vineflower/com/tridium/systemDb/BSystemDb.java:223-224` (N5) and the equivalent line
range in `niagara-research/organized/systemDb/systemDb-rt/vineflower/com/tridium/systemDb/BSystemDb.java`
(N4) `[CERT]` — but the concrete **`orientSystemDb`** subtype OVERRIDES it with a real, load-bearing
check: `organized/orientSystemDb/vineflower/com/tridium/systemDb/orient/BOrientSystemDb.java:830-840` (N5)
— `Feature feature = Sys.getLicenseManager().getFeature("tridium", "systemDb"); feature.check(); if
(!feature.getb("orientDb", false)) throw new FeatureNotLicensedException(…)` `[CERT]` — and the
byte-for-byte same logic exists in the N4-4.14 corpus at
`niagara-research/organized/orientSystemDb/orientSystemDb-se/vineflower/com/tridium/systemDb/orient/BOrientSystemDb.java:827-837`
`[CERT]`. `BSystemDb.isFatalFault()` (`:191-221`) calls this `checkLicense()` and, on any exception,
logs `"Unlicensed: " + this.toPathString()` and marks the component's `SystemDbService` config-failed
with an `UNLICENSED_TYPE` message `[CERT]` — i.e. an unlicensed `orientSystemDb` component does not
silently vanish; it exists as a real, fault-flagged, "Unlicensed" component in a station that has one
configured.

**Answer to the general mechanism question**: `systemDb`/`orientSystemDb` is architecturally a real,
checked license feature (`tridium:systemDb`, gated further by an `orientDb` boolean sub-attribute),
present identically in both N4-4.14 and N5 — **not** a feature that is "never provisioned" as a
structural omission at the module/code level; the module ships and its `checkLicense()` runs on any
station that instantiates the component. This narrows [Block 58]'s own `[INFER]` framing (which posed
"unlicensed/unused" vs. "never provisioned" as two live possibilities) toward the first: the mechanism
FOR gating it to be unlicensed exists and runs, in both N4 and N5, so a `systemDb`/`orientSystemDb`
absence on any given OEM install is architecturally consistent with a missing `tridium:systemDb`/
`orientDb` license attribute, not with the platform lacking the concept. **Which one actually explains
PANCCADIA's absence remains unanswered** — that requires either reading that specific station's license
file or a live Workbench "add component" check, both explicitly out of scope this wave — carried forward
as **B101-G1** below rather than reopened as a rewording of B58-G3.

## 101.9 — B32-G3 BLOCKED, as the gap's own text anticipated — desktop-tier `bin/javac` presence confirmed and recorded; embedded/JACE-tier device image not inspected, by scope, not by unavailability `[CERT-hw]`

`/mnt/c/Program Files/Niagara/5.0.0.28/jre/bin/javac.exe` exists: 13,312 bytes, sha256
`355c3f45fdffdf5f4f37fe27a32f5eba125b243d20d280a79e54ef33d360366b`; the sibling `jre/release` file
declares `JAVA_VERSION="25.0.4"` with `jdk.compiler` in its `MODULES` list `[CERT-hw]`. This is the exact
path [Block 32] §32.1 already traced `Compiler.getCompileJavaCommand()` to shell out to
(`jdkHome + File.separator + "bin" + File.separator + "javac"`, `niagara5-block32.md:43-44`) — this
session's live-install read directly corroborates that a real `bin/javac` binary sits at that resolved
path on the **desktop/engineering tier**, closing that half of the doc-vs-reality question the gap named.

**The embedded/JACE tier remains genuinely unconfirmed, and deliberately not pursued this session — a
scope decision, recorded rather than silently skipped.** A file named `/mnt/c/Users/equipo/jace-sd.img`
is present on this machine, under the same `/mnt/c/Users/equipo/…` path prefix prior-session memory
already associates with PANCCADIA client engineering work (that same host's `Niagara4.14/…/PANCCADIA/`
config path). Its filename is consistent with a JACE SD-card image, which would be exactly the kind of
embedded-tier artifact this gap needs — but this wave's SOURCES instruction forbids reading client
station files, and this session made no attempt to determine (by mounting, listing, or otherwise) what
that image actually contains; it is named here ONLY as an unopened path, for whichever future,
client-scope-authorized wave picks this up, not as evidence of any kind about its contents `[CERT-hw]`
(the file's mere existence and name, `ls`, this session — nothing further).

**Answer to the gap**: unchanged from [Block 32]'s own framing — BLOCKED on an embedded image, exactly
as anticipated; this session adds the desktop-tier corroboration the gap asked for as a fallback and
locates (without opening) a candidate artifact for a future, properly-scoped session.

## 101.10 — Connections

- **[Block 95]** — §101.1/§101.2/§101.3 close all three of Block 95's own numbered child gaps (`B95-G2`,
  `B95-G3`, `B95-G5`) opened at §95.11; §101.1 additionally feeds forward into [Block 12]'s `B12-G5`
  (ZXing identifies the TOTP-enrollment QR mechanism) and touches `B12-G6` (names the SAML library
  without tracing its servlet flow).
- **[Block 34]/[Block 6]** — §101.4 closes Block 34's `B34-G6` and, as a direct side effect, closes
  Block 6's own still-open `B6-G2` (the unexplained `security/licenses/conf/` on-disk artifact) — both
  gaps shared the same unanswered question from two different angles and are resolved by the same
  evidence.
- **[Block 5]/[Block 1]/[Block 3]** — §101.5 narrows Block 5's `B5-G1`; the packaging/JPMS context
  (N5-G1) and boot/runtime renames (N5-G7) those blocks documented are not re-touched here.
- **[Block 13]** — §101.6/§101.7 close both of Block 13's own `[B13-G5]`/`[B13-G6]` child gaps named at
  its own §13.9; §101.7 also extends [Block 6]'s `LicenseManager.checkFeature` gap (`B6-G3`) with a
  concrete negative result for the `cloudLink*` family.
- **[Block 58]** — §101.8 narrows `B58-G3`'s general-mechanism half; the client-specific half is
  explicitly deferred, not silently dropped, as **B101-G1**.
- **[Block 32]** — §101.9 supplies the desktop-tier corroboration `B32-G3` asked for as its fallback;
  the embedded-tier half stays exactly as blocked as the gap's own text already stated.

## 101.11 — Child gaps opened

- **B101-G1** — Determine, for a specific OEM N4 install with a genuinely-observed `systemDb`/
  `orientSystemDb` absence, whether that install's own license actually lacks the `tridium:systemDb`
  feature (or its `orientDb` attribute) — vs. Workbench simply never offering the component for addition
  there for an unrelated reason. Requires either reading that station's own license file or a live
  Workbench "add component" check on that station — both are client-station operations this wave's
  SOURCES instruction puts out of scope. Priority: **blocked-scope** (not investigable until a future
  wave explicitly authorizes client-station reads).
- **B101-G2** — Inspect the locally-present `/mnt/c/Users/equipo/jace-sd.img` (name only, not opened
  this session — §101.9) to determine whether it is in fact a JACE embedded-tier SD-card image and, if
  so, whether `bin/javac` (or any JDK toolchain) is present on it — this would close `B32-G3`'s embedded
  half outright. Requires the same client-scope authorization as B101-G1, since the path pattern matches
  prior PANCCADIA client engineering-host usage. Priority: **blocked-scope**.
- **B101-G3** — Obtain a non-OEM (stock Tridium-branded) N4 install, or a later/OEM N5 beta, to fully
  close `B5-G1` per its own stated closure condition — the two independent-OEM comparators in §101.5
  narrow the answer strongly but do not meet the gap's own bar. Priority: **medium** (a single new
  artifact would fully resolve it).
- **B101-G4** — Locate Tridium's own commercial/marketing name for the "Atlas" hardware target
  identified in §101.6 (ARM64, snap-packaged) — this session's one `WebSearch` found nothing public;
  Tridium's own official/partner documentation portal (out of this session's tool access) may name it.
  Priority: **low** (the physical/architectural identity is already closed; only the product label is
  missing).
- **B101-G5** — Locate and read the build-side Gradle task (likely an `unterjar`-family plugin, per
  [Block 95]'s own naming) that actually PACKS third-party jars into a module jar's `LIB-INF/` at build
  time — §101.1 fully closed the runtime-extraction side (`jar-cache/`) but the build-side packing step
  was not directly read this session (no Gradle build script for these modules exists in this
  decompiled/live-install corpus). Priority: **low** (runtime mechanism, the gap's main ask, is already
  `[CERT]`-closed; this is a completeness nicety, not an open factual question).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `jar-cache/` holds exactly the same 22 module-named subdirectories [Block 95] recorded | `[CERT-hw]` | `ls /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/jar-cache/`, this session |
| 2 | Exactly 22 of 247 module jars under `modules/` embed a `LIB-INF/*.jar` entry, matching the 22 jar-cache dirs 1:1 with matching per-module counts | `[CERT-hw]` | `unzip -l` loop over all 247 `modules/*.jar`, this session |
| 3 | `LIB-INF/nimbus-jose-jwt-10.0.2.jar` inside `oauth2.jar` is byte-identical to `jar-cache/oauth2/nimbus-jose-jwt-10.0.2.jar` | `[CERT-hw]` | `sha256sum` both, `960b978a6c…` match, this session |
| 4 | `NModuleModuleFinderFactory.readModule()`/`getCachedJar()` is the exact code that detects a nested-filesystem module jar and copies it into `jar-cache/<module>/` with mtime-based staleness checking | `[CERT]` | `organized/baja/vineflower/com/tridium/sys/module/NModuleModuleFinderFactory.java:297-328,612-635` |
| 5 | `jar-cache/totpAuth/core-3.5.4.jar` is ZXing 3.5.4 (Automatic-Module-Name `com.google.zxing`) | `[CERT-hw]` | `unzip -p … META-INF/MANIFEST.MF`, this session |
| 6 | `QuickJSONWriter`: 35 files / 110 occurrences; `PrettyJSONStringer`: 1 file / 4 occurrences, whole-corpus | `[CERT]` | `find organized -iname '*.java' -exec grep -l/-c …`, this session, `fallback/` excluded |
| 7 | `BIpProtocolEnum.make(BIpProtocolEnum)` is a single switch method with exactly 2 call sites, both in `BServerPort.updateFirewallRules()` | `[CERT]` | `organized/baja/vineflower/niagara/firewall/BIpProtocolEnum.java:54-65`; `BServerPort.java:281,286` |
| 8 | `getIpProtocol()` call sites are confined to 5 firewall-package files, zero in socket/listener code | `[CERT]` | `find organized -iname '*.java' -exec grep -l 'getIpProtocol()'`, this session |
| 9 | N4's fully-decompiled `nre.jar` (Block 477, sha256-verified, 437 files) has no `com/tridium/nre/license` package | `[CERT]` | `find sources/decompiled/nre-ext -type d -ipath '*com/tridium/nre*'`, this session; `niagara-mental-model-bloque477.md:11-12` |
| 10 | N5 corpus: zero genuine `hsm`/`HSM` hits, whole-corpus case-insensitive, 2 named false positives confirmed by inspection | `[CERT]` | `find organized -iname '*.java' -exec grep -li hsm'`, this session; manual read of both false-positive files |
| 11 | `HsmManager`/`HsmManagerImpl` present in BOTH the Honeywell-OEM 4.14 decompile and the independent PowerB-OEM 4.15.3.28 install jar | `[CERT]`/`[CERT-hw]` | `sources/decompiled/nre-ext/javax/baja/nre/security/HsmManager.java`; `unzip -l "/mnt/c/PowerB/PowerB-4.15.3.28/bin/ext/nre.jar"` |
| 12 | `ATLAS_PART_NAME="ATLAS"`, `TITAN_PART_NAME="TITAN"`, `TITAN_OS_NAME_SUFFIX="-n4-titan-am335x-hs"`, `ATLAS_SNAP_TRIDIUM_NIAGARA_NAME="snap-tridium-niagara-arm64"` | `[CERT]` | `organized/docSource/backup/niagara/backup/BBackupService.java:3155,3156,3159,3169,3170` |
| 13 | No public web page names "Atlas" as a Tridium hardware product (negative result only) | `[CERT-web]` | one `WebSearch` this session, query quoted in §101.6 |
| 14 | `cloudLinkForge`/`cloudLinkHonSbp` contain zero Honeywell-named license-feature checks; all real gates live in shared `cloudLink` on generic `tridium:cloudLink`/`cloudLinkConnect`/`historyArchive` features | `[CERT]` | full `grep -rniE` sweep of both module trees; `organized/cloudLink/vineflower/com/tridium/cloudLink/BCloudConnectionService.java:209,214`; `util/LicenseLimit.java:58`; `channel/BHistoryChannel.java:315` |
| 15 | `BOrientSystemDb.checkLicense()` requires `tridium:systemDb`'s `orientDb` attribute, identically in N4-4.14 and N5 | `[CERT]` | `organized/orientSystemDb/vineflower/com/tridium/systemDb/orient/BOrientSystemDb.java:830-840` (N5); `niagara-research/organized/orientSystemDb/orientSystemDb-se/vineflower/com/tridium/systemDb/orient/BOrientSystemDb.java:827-837` (N4) |
| 16 | `bin/javac` exists on the desktop N5 5.0.0.28 install as `jre/bin/javac.exe`, JDK 25.0.4 with `jdk.compiler` | `[CERT-hw]` | `ls -la`/`sha256sum` `.../jre/bin/javac.exe`; `cat .../jre/release`, this session |

Tally: **16 [CERT]/[CERT-hw]-class claims**, **1 [CERT-web]** (row 13, an explicit negative-result
search), **0 [INFER]** in the table above (every closing verdict rests on a command run or a direct file
read this session). Prose-level `[INFER]` appears only twice, both explicitly flagged inline: §101.1's
"resolved by elimination" note on the unread Gradle build-side step, and §101.5's own framing of why it
narrows rather than closes. Adjusted ratio `[INFER]`/`[CERT]`-family ≈ **0.12** (2 inline `[INFER]`
clauses against 17 table-row CERT-family claims) — low, consistent with an EVIDENCE-type block.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block101.md
```

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block101.md` (the only
file written in the corpus this session, per the task's single-file constraint). `INDEX.md`/
`RESEARCH-STATE.md`/`CATALOG.md` were **not** regenerated — left to the integrator, per wave convention.
No scratch scripts were needed this session (`sha256sum`/`unzip`/`find`/`grep` one-liners only); a scratch
copy of `LIB-INF/nimbus-jose-jwt-10.0.2.jar` used for the §101.1 byte-identity check lives at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b101/libinf-nimbus.jar`
(reproducible from the `unzip -p` command quoted there, not itself load-bearing evidence beyond the
sha256 already stated inline).
