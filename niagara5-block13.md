# Block 13 — N4.14 → N5 module inventory delta: removed, merged, OEM-only and new modules

> Research of **the module SET delta between the Honeywell OptimizerSupervisor-N4.14.0.162 OEM build and
> the stock Tridium Niagara 5.0.0.28 beta**: every N4-only ("removed") module classified into
> Honeywell/OEM/third-party vendor vs Tridium-removed vs Tridium-merged/renamed vs no-evidence; the 18
> N5-only modules' purpose; vendorVersion/dependency/size deltas for the 229 modules common to both; and
> whether our own N4 modules' declared dependencies survive in N5. Does NOT cover: method-body tracing of
> any individual module's runtime behaviour (that is B1-G2/B3-G1 territory), a live N5 station build of any
> replacement module (B2-G7/B10-G1, `requires-execution`), or the full official N5.0 Breaking-Changes list
> beyond what B10 already extracted (B10-G2, still pending).
>
> Subject version: N4 side — Honeywell OptimizerSupervisor **4.14.0.162** OEM build,
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules` (992 jars on disk at analysis time). N5 side —
> Niagara **5.0.0.28** beta, `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` (248 jars on disk
> at analysis time, one of which — `n5Hello.jar`, `vendor="poc"` — is a local build-artifact from a
> concurrent gradle-plugin PoC, not a shipped module; excluded throughout, leaving 247 real N5 modules —
> see §13.1). Both trees are read-only, unversioned by git; jar `buildMillis`/`releaseDate` and file `mtime`
> serve as the version stamp (METHODOLOGY §3 "no git, no problem").
>
> Sources: `tools/n5-modules.py diff-n4 --json` (this target's own tool, read-only, pure stdlib) over the
> two module directories above · every `META-INF/module.xml` in every N4 jar named by the diff (`vendor`,
> `vendorVersion`, `description`, `<dependency>` list) · every `META-INF/module.xml` + full zip-entry
> namelist (`.class` files and resource paths) in all 247 real N5 jars · `docDeveloper.jar` →
> `doc/modules.html`, `doc/upgrade/upgradingToN5.html` (already read for B10; re-searched here for
> module-name-specific removal text) · `lonDevices.jar` full zip namelist (proof of LON-device-library
> consolidation, §13.4.2) · Cliente checkout `build.gradle.kts` files under
> `/home/cristian/modulos_niagara_n4/Cliente/{Leon-Guanjuato,Honeywell,Juarez,LLM,panccadia-leon,_salvage}`
> (excluding `*-worktrees/` duplicates) for our own modules' declared Niagara dependencies (§13.7).
>
> Method: `tools/n5-modules.py diff-n4 --json` produced the base three-way split (698 N4 collapsed base
> names / 247 N5 / 18 added / 469 removed / 229 common); one-off `python3 zipfile`/`xml.etree.ElementTree`
> scripts (not preserved in the corpus — scratch only, per the block1 §1 convention) then (1) read `vendor`
> for every one of the 469 removed base names' constituent part-jars, (2) built a package-prefix index of
> all 247 real N5 jars' `.class` zip entries, (3) for each Tridium-vendor removed module extracted its own
> `.class` package set and probed the N5 index for overlap, (4) for the two resource-only families (LON
> device profiles, per-module doc bundles) compared zip-entry **directory names** instead (no `.class`
> exists in either side), (5) diffed `vendorVersion`/`dependencies`/jar-size for the 229 common base names,
> (6) grepped Cliente `build.gradle.kts` files for `api(":x")`/`nre(":x")`-style dependency declarations and
> checked each target's survival in N5. Every count below is the literal output of one of these scripts run
> in this session — no count is hand-estimated. Scripts and raw JSON were kept under this session's scratch
> directory (`/tmp/claude-1000/.../scratchpad/*.json`) — not archived in the corpus, mirroring B1's own
> "census scripts kept in scratch" convention.
> Markers: `[CERT]` local primary source (module.xml attribute, jar zip-entry path, or a script's literal
> output computed in this session) · `[CERT-doc]` shipped Tridium doc inside `docDeveloper.jar`, cited by
> HTML zip-entry path · `[INFER]` deduction / naming-convention or role inference not literal in any source.
>
> Packaging/inventory layer. Connects [B1] (N5 module packaging — the collapse this block diffs against),
> [B4] (`docDeveloper.jar` census — §13.4.3's merge target), [B10] (breaking-changes table BC-02 `app`
> module removed — §13.4.1's sole doc-confirmed case), [B2] (build toolchain — §13.6's dependency-list
> shrinkage), [B6] (licensing — §13.5's Honeywell-branded-under-Tridium-vendor finding).
>
> **Type:** mixed (evidence classification + one synthesis cross-reference to B1/B4/B10's already-covered
> gaps in §13.4.1/§13.4.3; the vendor/merge/no-evidence classification itself is fresh `[CERT]` evidence
> read in this session, not deduction across prior blocks).

---

## 13.1 — Snapshot integrity and excluded non-module artifacts `[CERT]`

Three data-quality findings, measured before any classification, that change the denominator:

1. **Three non-module tool jars sit inside the N4 `modules/` directory.** `cfr.jar`, `procyon.jar`,
   `deobfuscator.jar` are decompiler tools (used by this research's own prior sessions, e.g. B1's method),
   not Niagara modules — `cfr.jar`'s zip contains `META-INF/MANIFEST.MF` (a generic Java manifest, dated
   2021-12-11) and **no** `META-INF/module.xml`; reading `module.xml` from all three raised
   `There is no item named 'META-INF/module.xml' in the archive` `[CERT]`. Their `mtime` (2026-03-11 to
   2026-04-03) is later than the genuine OEM release build (`alarm-rt.jar`/`baja.jar` both `mtime`
   2025-03-14, matching the shipped `releaseDate="2024-05-28"` inside their `module.xml` `[CERT]`) —
   confirming they were copied into this directory by prior tooling, not shipped by Honeywell. The
   `collapse_n4_modules()` helper in `tools/n5-modules.py` has no module.xml awareness (it only strips
   filename suffixes), so it counts these 3 as "removed base modules." Excluded from every classification
   below. This drops the real "N4-only module" population from **469 → 466**.
2. **`n5Hello.jar` appeared in the N5 `modules/` directory mid-session.** `module.xml` reads
   `vendor="poc"`, `vendorVersion="1.0.0"` `[CERT]`; file `mtime` 2026-09-27 05:27:13, i.e. *after* an
   earlier `diff-n4` run in this same session had already reported 247/18/469/229 without it — consistent
   with a concurrent gradle-plugin proof-of-concept (the pending `B2-G7`/`B7-G1` "build a trivial N5 module"
   gap) depositing its build output into the shared deployed-modules cache while this block was being
   written. It is a locally-built PoC artifact, not a Tridium-shipped module; excluded throughout, so "N5
   module count" in this block is **247**, matching the frozen `diff-n4.json` snapshot (18 added + 229
   common) rather than the live directory's current 248 jars.
3. **One N5 jar-count discrepancy vs B1.** B1 §1.1 reports 247 N5 jars at its write time; this block
   independently also lands on 247 real (non-PoC) N5 modules — consistent, not a contradiction; the
   momentary 248 in finding 2 is explained by `n5Hello.jar`'s later arrival, not a change to the shipped set.

All counts from §13.2 onward use the **frozen snapshot**: 466 genuine N4-only modules, 247 real N5
modules, 18 added, 229 common (18+229 = 247 `[CERT]` — measured via `tools/n5-modules.py diff-n4 --json`).

## 13.2 — Top-level counts `[CERT]`

| Metric | Value | Method |
|---|---|---|
| N4 jars on disk (`modules/`) | 992 | `ls *.jar \| wc -l` |
| N4 base modules after suffix-collapse (`-rt/-ux/-wb/-se/-doc`) | 698 | `diff-n4 --json` → `n4_module_count` |
| N5 jars on disk at snapshot time | 247 (248 after `n5Hello.jar` appeared — §13.1) | `diff-n4 --json` → `n5_module_count` |
| N4-only ("removed") base modules | 469 raw → **466 real** (§13.1 excludes 3 tool jars) | `diff-n4 --json` → `removed_from_n4` |
| N5-only ("added") modules | 18 | `diff-n4 --json` → `added_in_n5` |
| Common base modules (present both sides) | 229 | `diff-n4 --json` → `common` |

## 13.3 — Vendor classification of the 466 N4-only modules `[CERT]`

Every removed base module's constituent N4 part-jar(s) were opened and `module.xml`'s `vendor` attribute
read (union across parts — no removed module showed a vendor split across its own parts). Two vendor
strings turned out **not** to be Honeywell OEM content at all: `Angeles` (this researcher's own PANCCADIA
family of custom N4 modules, coincidentally vendor-stamped and baked into this same shared
OptimizerSupervisor-N4.14.0.162 install used across multiple client engagements) and `SEJOFA`/`Sejofa` (a
different client's custom modules, same install). Folding those into "Honeywell OEM" would overstate the
true OEM package; they are broken out separately.

| Class | Vendor string(s) | Count | Total bytes | Examples |
|---|---|---|---|---|
| **(a) Honeywell OEM** | `Honeywell` (91) + `Honeywell.Galileo` (8) + `honeywell` (5) + `Honeywell.SBC` (1) | **105** | 217,231,160 | `BACnetFFTN4`, `airFlowBalancer`, `ascBacnet`, `SylkActuatorAnalytics`, `galileoSupervisor`, `easyTemplating`, `sbcIconGallery` |
| **(a) Centraline (Honeywell European brand)** | `Centraline UK` (2) + `centraline` (1) + `CentraLine` (1) | **4** | 682,684 | `CentralineAhuPx`, `CentralineHtgPx`, `clExtensions`, `clLexiconDe` |
| **(a) Third-party free-community modules** | `NiagaraMods` | **3** | 10,572,455 | `nmodsomnipal`, `nmodsreflow.77`, `nmxdomo` |
| **(a) Client-custom, non-OEM** | `SEJOFA` (17) + `Sejofa` (1) | **18** | 36,747,117 | `dashboardups`, `sukarne`, `datacenter`, `banbajio`, `DashboardNotifier` |
| **own-dev, non-OEM (not a vendor-delta finding)** | `Angeles` (10) + `ANGELES` (3) + `Angeles4657` (1) | **14** | 36,999,909 | `ColdRoomPan`, `CompPan`, `DashboardPan`, `MinimalPan`, `UmbrellaDashboard` |
| **(b)/(c)/(d) Tridium-vendor** (§13.4) | `Tridium` (313) + `Tridium Europe` (6) + `TridiumPS` (3) | **322** | — (see §13.4) | `app`, `lonAaon`…, `docKitControl`, `electronicSignature` |
| **excluded — not a module** | (n/a — decompiler tool jars) | 3 | — | `cfr`, `procyon`, `deobfuscator` |
| **Total** | | 469 raw (466 real) | | |

**Reading this table for the gap's actual question.** 105 + 4 + 3 + 18 = **130 genuinely non-Tridium
modules** removed from the N4→N5 delta — this is the true "Honeywell OEM / third-party layer that has no
platform counterpart because it was never Tridium's to carry forward" bucket, class (a). The 14 `Angeles`
modules are excluded from that bucket (own dev-account artifacts of this install, not OEM content) but are
*also* not part of the Tridium platform delta — they are simply absent from N5 because nobody has ported
them yet (tracked separately by `N5-G14`/`B10-G1`, not a platform removal). The 322 `Tridium`-vendor
modules are the ones that answer "what did Tridium itself drop, merge, or omit" — classified next.

## 13.4 — Tridium-vendor removed modules (322): removed / merged / no-evidence `[CERT]`

### 13.4.1 — (b) Documented removed: 1 module `[CERT-doc]`

Only **one** of the 322 Tridium-vendor removed modules is named explicitly, by module name, in the shipped
upgrade documentation: **`app`** (`vendor="Tridium"`, `vendorVersion="4.14.0.162"`, `description="Niagara
Applications"`, parts `rt`+`wb` `[CERT]`). `docDeveloper.jar` → `doc/upgrade/upgradingToN5.html` states
verbatim: *"app module removed — The app module has been removed. Most of its contents were deprecated or
removed in Niagara 4.15 since the Niagara Mobile apps have long been superseded by the standard web
interface"* `[CERT-doc]` — this is B10's own BC-02 row, cross-referenced here as the only removed-module
name this session could re-find via full-text search of the same document (`326` occurrences of the word
"module" in that HTML were scanned for a "removed"/"deleted"/"discontinued"/"no longer" pattern within 100
characters; every other hit named a **class or method**, not a **module**, as removed `[CERT]`).

### 13.4.2 — (c) Merged: 200 LON device-profile modules → `lonDevices` `[CERT]`

200 of the 322 Tridium-vendor removed modules are per-vendor LON device-profile libraries named
`lon<Vendor>` (`lonAaon`, `lonAbb`, `lonAct`, … `lonCpc`, 200 total base names, each shipped as a single
`-rt`-only jar holding `.lnml` device-profile XML resources — **zero `.class` files** in any of them
`[CERT]`, so the package-overlap method used for code modules cannot see them). N5's new `lonDevices.jar`
(one of the 18 added modules, description `"LON Devices"`, `vendorVersion="5.0.0.28"`, 4,261,024 bytes,
1,951 zip entries) contains one top-level directory per vendor — `lonAaon/`, `lonAbb/`, … `lonCpc/` — each
holding the same `.lnml` files `[CERT]`. A direct set comparison of the 200 removed N4 module base names
against `lonDevices.jar`'s top-level directory names found **200 of 201** exact matches (the 201st N4-side
`lon*` name, `lonhoneywellAXWizards`, is `vendor="Honeywell"` — a UI wizard helper, not a device-profile
library, correctly excluded from this Tridium-family count and from the merge, §13.3). `lonDevices.jar`
additionally carries a `lonMcquay/` directory with **no** N4-side `lon*` module counterpart — a genuinely
new device-profile addition in N5, not a rename `[CERT — INFER for "new" since no N4 vendor library for
McQuay was ever removed to compare against]`.

**Verdict: 200/200 Tridium-vendor `lon*` modules are a clean, measured, directory-name-identical merge**
into the single new `lonDevices` module — the strongest evidence-backed merge case in this block.

### 13.4.3 — (c) Merged: 13 per-module doc-guide jars → `docDeveloper.jar` `[CERT]`

75 of the 322 Tridium-vendor removed modules are standalone `doc<Name>-doc.jar` guide bundles (already
covered as an N4 packaging pattern by [B1]; their N5-side consolidation into one `docDeveloper.jar` is
[B4]'s finding, re-applied here per-module). Matching each `doc<Name>` base name against
`docDeveloper.jar`'s zip namelist for an *exact* `doc/<name>/module-index.bajadoc` or `doc/<name>.html`
entry (case-variants tried: as-given, first-letter-lowered, first-letter-uppered) found **13 exact hits**:

| N4 doc module | N5 `docDeveloper.jar` match |
|---|---|
| `docAapup` | `doc/aapup/module-index.bajadoc` |
| `docAce` | `doc/ace/module-index.bajadoc` |
| `docBacnet` | `doc/bacnet/module-index.bajadoc` |
| `docCcn` | `doc/ccn/module-index.bajadoc` |
| `docHttpClient` | `doc/httpClient/module-index.bajadoc` |
| `docJsonToolkit` | `doc/jsonToolkit/module-index.bajadoc` |
| `docKitControl` | `doc/kitControl/module-index.bajadoc` |
| `docLonworks` | `doc/lonworks/module-index.bajadoc` |
| `docNrio` | `doc/nrio/module-index.bajadoc` |
| `docNsnmp` | `doc/nSnmp/module-index.bajadoc` |
| `docPlatform` | `doc/platform/module-index.bajadoc` |
| `docSeriesTransform` | `doc/seriesTransform/module-index.bajadoc` |
| `docWeather` | `doc/weather/module-index.bajadoc` |

These 13 are the module-API-javadoc counterpart of a real, still-shipped N5 module (e.g. `docKitControl`'s
javadoc is now inside `docDeveloper.jar` because `kitControl` itself is a common module — its bajadoc moved
with B4's per-module consolidation, not a code merge in the §13.4.2 sense).

### 13.4.4 — (d) No merge/removal evidence found: 108 modules `[CERT]` / `[INFER]` for the absence conclusion

The remaining 322 − 1 − 200 − 13 = **108** Tridium-vendor removed modules produced **zero** evidence of
either documented removal or consolidation, split into two measured groups:

**(d-1) 59 doc-guide jars with no matching artifact anywhere in `docDeveloper.jar`** (same exact-match
method as §13.4.3, zero hits under any case variant) — includes `docUser` (independently flagged absent by
the still-open, DEFERRED gap `B4-G6`, corroborating this method), `docAnalyticsAPI`, `docAnalyticsGuide`,
`docBackupRestore`, `docDrivers`, `docModbus`, `docObix`, `docProvisioning`, `docSnmp`, and 50 more feature
*guide* PDFs. A looser substring search (not just the exact-path check) does find per-class bajadoc for
several of the underlying *code* modules under a different key (e.g. `doc/modbusAsync/`, `doc/nSnmp/`,
`doc/rdb/`, `doc/obixDriver/`, `doc/provisioningNiagara/`) — meaning the API reference for that subsystem
still exists, but the standalone feature **guide** these doc-jars held does not appear to. `[CERT]` for the
absence within `docDeveloper.jar`; `[INFER]` for "not shipped in the beta at all" — the web-hosted Tridium
doc portal was not checked (out of scope here; ties into the still-open `B4-G6`/`B10-G2` gaps).

**(d-2) 49 real code modules with zero N5 package overlap** — every one of their `.class` package prefixes
was probed against the full 247-module N5 package index and found in **none** of them:

| Module | N4 `.class` count | Notes |
|---|---|---|
| `electronicSignature` / `electronicSignatureRemote` | 836 / 216 | vendor `TridiumPS` |
| `cloudIotHubDep` / `cloudIotHubConnector` / `nCloudDriver` / `cloudBackup` / `cloudConnector` / `cloudConfig` / `cloudSentienceConnector` | 589/6/158/30/18/1/14 | old cloud stack — packages `com.tridium.cloud.client.*`, `com.tridium.nc.*` `[CERT]`; **no package-name continuity** with the new `cloudLink*`/`niagaraCloud` family (§13.5), which uses `com.tridium.cloudLink.*`/`com.tridium.niagaraCloud.*` — role plausibly superseded but this is a rewrite, not a code merge `[CERT for the package names; INFER for "superseded"]` |
| `knxnetIp` / `knxStationConverter` | 388 / 4 | vendor `Tridium Europe` |
| `gauth` | 310 | |
| `snmp` | 195 | **already coexisted** in N4 alongside a separate `nSnmp` module (both present in the N4.14.0.162 tree, `nSnmp` is `common` in N5 too) — its removal looks like N4-side legacy cleanup already under way before N5, not an N5-specific drop `[CERT for coexistence; INFER for the "already legacy" reading]` |
| `micros`, `opc`, `openAdr`, `ndio`, `mobile`, `mobileThemeZebra` | 113/88/85/72/49/1 | |
| `fcModelSync` / `fcModelSyncBacnet` / `fcModelSyncNiagara` / `fcEasyOnboard` / `fcTagDict` | 29/2/2/16/15 | "fc" = Forge Connect-adjacent naming; no `fc*` N5 module exists to check against |
| `platPower`, `platNdio`, `platSerialQnx` | 20/6/4 | |
| `bacnetAlarmRouter` (`Tridium Europe`), `bacnetOws`, `bacnetMigrator` | 17/17/4 | |
| `boxAnalyzer`, `rdbOracle` | 11/13 | |
| `kitPxBuilding` (`Tridium Europe`) | 15 | packages `com.tridiumemea.extras.*` — EMEA-regional kit, no N5 trace |
| `platHwScanJ603`/`J645`/`Jvln`/`Npm`/`Sec`/`Titan`/`Xpr` | 1 each | package pattern `com.tridium.platHwScan<Model>.B<Model>Board` — **structurally identical naming convention** to the new `platHwScanAtlas` module's `com.tridium.platHwScanAtlas.BAtlasBoard` `[CERT]`; read as role-superseded by a new unified "Atlas" hardware target, not a code merge `[INFER]` |
| `nrioConversion`, `hdk8000`, `videoMigrator`, `modbusTcpSlaveMigrator`, `obixMigrator`, `snmpMigrator`, `weatherUnderground` | 5/2/2/1/1/1/1 | one-off migrator utilities |
| `DINsymbol` (`Tridium Europe`, `wb`-only, 0 classes), `analytics-lib` (0 classes) | — | resource/palette-only, no code to compare |

No claim of certainty about *why* these 108 are gone — the measured fact is the absence of any evidence
(doc text or package overlap) for removal-reason or merge-target; §13.9 opens a child gap rather than
guessing.

## 13.5 — The 18 N5-only modules `[CERT]`

> **Correction (added by [Block 115], §115.4, §14 cross-block).** "N5-only" here means "absent from the
> specific N4.14.0.162 OEM install consulted" — this section never checked against the closer N4-**4.15.3.28**
> release. Re-run this session against all of `/mnt/c/PowerB/PowerB-4.15.3.28/modules`: **7 of these 18
> already ship in N4-4.15.3.28** — the `cloudLink` family (`cloudLink`, `cloudLinkAzure`, `cloudLinkForge`,
> `cloudLinkHonSbp`, `cloudLinkNcs`), `jodaTime`, and (not previously known) `platHwScanAtlas`
> (`module.xml` `vendorVersion="4.15.3.28"`, same `BAtlasBoard` class), per a class-level census of all 721
> jars in that install. The remaining 11 (the 3
> `cloudLinkExtension*` modules, `niagaraCloud`, `niagaraSync`, `nurio`, `platNurio`, `totpAuth`, `themeN5`,
> `analyticsLibs`, `lonDevices`) are genuinely absent from this 4.15.3.28 install too. See [Block 115] §115.4
> for the full corrected table and downstream sites this affected (including [Block 18] §18.9's `cloudLinkNcs`
> row).

| Module | Vendor · vendorVersion | Size | Description (module.xml) | Notable |
|---|---|---|---|---|
| `cloudLink` | Tridium · **5.0.0.26** | 2,442,163 | Core Cloud Connectivity | 474 classes, top package `com.tridium.cloudLink.msg` |
| `cloudLinkAzure` | Tridium · 5.0.0.26 | 73,835 | Azure Cloud Connectivity | depends on `cloudLink` |
| `cloudLinkForge` | Tridium · 5.0.0.26 | 448,273 | **"Honeywell Forge Cloud Connectivity"** | vendor is `Tridium`, not `Honeywell` — see below |
| `cloudLinkHonSbp` | Tridium · 5.0.0.26 | 136,574 | **"CloudLink module for Honeywell Smart Buildings Platform"** | same finding |
| `cloudLinkNcs` | Tridium · 5.0.0.26 | 65,734 | CloudLink module for Niagara Cloud Suite | |
| `cloudLinkExtensionBacnet` / `…Ebi` / `…Niagara` | Tridium · 5.0.0.26 | 28,658 / 18,746 / 41,675 | per-driver CloudLink station-utility shims | |
| `niagaraCloud` | Tridium · **5.0.0.28** | 40,911 | Niagara Cloud module | discovery client, 16 classes |
| `niagaraSync` | Tridium · 5.0.0.28 | 102,956 | Niagara sync service | 28 classes — feeds `B5-G3` |
| `nurio` | Tridium · 5.0.0.28 | 404,209 | Niagara Remote IO Driver | 162 classes |
| `platNurio` | Tridium · 5.0.0.28 | 98,065 | Niagara Universal Remote IO Platform Service | 61 classes, dependency of `nurio` |
| `platHwScanAtlas` | Tridium · 5.0.0.28 | 120,520 | Niagara Hardware Scan Service for Atlas | 1 class (`BAtlasBoard`) — see §13.4.4 naming-convention note |
| `totpAuth` | Tridium · 5.0.0.28 | 804,942 | Time-based One-Time Password (TOTP) Authenticator | 19 classes — feeds `N5-G9` |
| `themeN5` | Tridium · 5.0.0.28 | 1,020,168 | "The latest and the greatest Niagara theme" | 0 classes (resources only) |
| `analyticsLibs` | Tridium · 5.0.0.28 | 45,495 | Niagara Analytics Library | 0 classes — resource/lib bundle |
| `jodaTime` | Tridium · 5.0.0.28 | 549,958 | Joda Time | third-party library repackaged as a Niagara module, dep = `baja` only |
| `lonDevices` | Tridium · 5.0.0.28 | 4,261,024 | LON Devices | the §13.4.2 merge target |

**Two findings beyond bare inventory:**

1. **Honeywell-branded product content now ships under `vendor="Tridium"`.** `cloudLinkForge` and
   `cloudLinkHonSbp` name Honeywell products (Forge, Smart Buildings Platform) directly in their
   `description`, yet their `module.xml` `vendor` attribute is `Tridium`, not `Honeywell` `[CERT]` — a
   platform-level convergence: in N4 this kind of Honeywell-specific integration lived in the separate OEM
   overlay (vendor `Honeywell`, §13.3); in N5 it ships as stock Tridium product. This is qualitatively
   different from every merge/removal case in §13.4 — it is new Honeywell content entering the *platform*
   layer, not old platform content leaving it.
2. **The `cloudLink*` family (7 of the 18 modules) is stamped `vendorVersion="5.0.0.26"`**, two iterations
   behind every other module in this snapshot (all of which read `5.0.0.28`, matching the release
   `vendorVersion` seen across all 229 common modules in §13.6) `[CERT]`. Whether this is a stale build
   artifact of this specific beta drop or an intentionally independent CloudLink release train is not
   determinable from static inspection alone — opened as `B13-G2`.

## 13.6 — The 229 common modules: vendorVersion, dependency and size delta `[CERT]`

**vendorVersion.** 228 of 229 common N4-side modules read exactly `vendorVersion="4.14.0.162"`; the lone
exception, `niagaraLexiconDe` (German lexicon pack), reads `vendorVersion="4.13.2.18"` — one platform
release behind the rest of the OEM baseline, i.e. it was not rebuilt when Honeywell bumped the rest of the
tree to 4.14.0.162 `[CERT]`. All 229 N5-side counterparts read exactly `vendorVersion="5.0.0.28"` — no
exceptions.

**Size.** Total jar bytes for the 229 common modules: N4 side 193,050,119 bytes → N5 side 223,839,317 bytes
(+15.9%, `[CERT]`, single-jar-per-module N5 sizes vs the summed rt+ux+wb+se+doc N4 parts). 134 grew, 95
shrank, 0 stayed byte-identical. Largest growth: `docDeveloper` +12,943,924 (already explained by B4's
consolidation influx), `xprotect` +12,777,380, `ffmpeg` +3,112,811, `gx` +2,544,738. Largest shrink:
`apachePoi` −2,793,149, `abstractMqttDriver` −2,228,211, `samlEncryption` −1,202,712, `commonsLang`
−696,817.

> **Correction (added by [Block 122], §122.8, §14 cross-block).** The `xprotect` and `ffmpeg` growth figures are measured against the N4.14 parts only. Against the N4-4.15.3.28 OEM install (`xprotect-ux` 181,730 + `xprotect-wb` 2,903,882 B; `ffmpeg-rt` 46,063 + `ffmpeg-wb` 23,488,672 B) the growth is +11,571,737 and +1,648,861 B (`evidence/b122/claim-audit.tsv`); of the quoted growth 1,205,643 B (xprotect) and 1,463,950 B (ffmpeg) is 4.14→4.15, not N5; the 14 .NET files and the 26-export ffmpeg wrapper already ship in 4.15.


**Dependency-list churn.** Comparing each common module's declared `<dependency>` name set (N4 side: union
across its rt/ux/wb/se parts, suffix-stripped; N5 side: its single module.xml) found 155/229 modules with at
least one *added* declared dependency and 130/229 with at least one *removed* one. The most frequently
**added** names across modules: `svgBatik` (149), `oauth2` (136), `jsonSmart` (135), `smartTableHx` (61),
`hx` (52), `webEditors` (51), `bajaux` (39). The most frequently **removed** names: `uxBuilder` (94),
`template` (93), `search` (92), `tagdictionary` (91), `neql` (87), `converters` (73), `wbutil` (58) `[CERT —
measured counts]`. **Read this carefully**: every one of those "removed" dependency names (`search`,
`tagdictionary`, `alarm`, `history`, `chart`, `platform`, `driver`…) is itself a module that is still
`common` in N5 (verified directly, §13.7's method) — this is **declaration-list churn, not a target-module
disappearance**. The likely explanation is that N5's Gradle-based module build declares fewer *explicit*
dependencies than N4's per-profile manual `module.xml` union did (JPMS `requires` transitivity, or the new
`n-module`/`niagara` plugin computing a narrower explicit set — [B2] territory) `[INFER]`; confirming the
mechanism is out of scope here and opened as `B13-G4`.

## 13.7 — Our own N4 modules' dependencies vs the N5 delta `[CERT]`

Every `api(":x")`/`implementation(":x")`/`nre(":x")`-style Niagara-module dependency declared in this
project's own `build.gradle.kts` files (Cliente checkouts, worktree duplicates excluded) was extracted and
checked against the frozen `diff-n4` classification:

| Declared dependency (suffix-stripped) | N5 status |
|---|---|
| `alarm`, `baja`, `bajaScript`, `bajaui`, `bajaux`, `bql`, `control`, `gx`, `history`, `schedule`, `search`, `web`, `workbench` | **common** — all 13 |
| `nre` | special NRE boot dependency type (not a `<dependency>` module entry); `nre.jar` exists in N5 per [B3] |

**Zero** of our own declared module dependencies fall into the removed-from-N4 list. Example citation:
`DashboardPan-rt.gradle.kts:47-51` (`Leon-Guanjuato/Dashboard/DashboardPan/DashboardPan-rt/`) declares
`api(":baja")`, `api(":alarm-rt")`, `api(":control-rt")` `[CERT]`; all three base names (`baja`, `alarm`,
`control`) are `common` per §13.2's frozen snapshot.

## 13.8 — Self-verification `[CERT]`

- **Token check.** Every load-bearing named count in §13.1-§13.7 was re-derived from a script run in this
  session (not recalled) and cross-checked at least once by a second, independent method where a surprising
  result appeared (e.g. the 274-of-321 "zero-class" anomaly in §13.4 was traced to LON/doc resource-only
  jars by direct `unzip -l`, not assumed). Spot-checked primary facts: `app` module.xml attributes (direct
  JSON read, §13.4.1), `docDeveloper.jar`'s `doc/kitControl/module-index.bajadoc` entry (direct
  `zipfile.namelist()`, §13.4.3), `lonDevices.jar`'s 200/201 directory-name match (direct set diff,
  §13.4.2), `cloudLinkForge` vendor=`Tridium` (direct `module.xml` read, §13.5), `DashboardPan-rt.gradle.kts`
  dependency lines (direct file read, §13.7). 12 distinct facts spot-checked this way, 12/12 confirmed on
  first read (no false-negative rechecks needed).
- **verify-block.sh.** Not run as a literal invocation in this session — this block's citations are
  overwhelmingly jar zip-entry paths, `module.xml` XML attributes, and script-computed aggregate counts over
  files **outside** this git-tracked corpus (`/mnt/c/Honeywell/...`, `/mnt/c/ProgramData/...`), which
  `verify-block.sh`'s `file:line` resolver cannot reach — every citation would classify `extern`, exactly the
  documented "decompiled-tree blocks show zero resolved citations" signature (METHODOLOGY §11), here for jar
  entries rather than decompiled trees. Declaring explicitly per that rule: **verify-block: 0 resolved of 0
  file:line attempted (all citations are jar-zip-entry / module.xml-attribute / script-output form, not
  `file:line` — see B1 §1.8's identical convention); citation gate = inline token-verify, 12/12 tokens
  confirmed above.**
- **Marker tally — computed by grep, ADJUSTED (header legend region stripped, per METHODOLOGY §11):**
  `[CERT]` 29 · `[CERT-doc]` 3 · `[INFER]` 6 (RAW/unadjusted, whole file: `[CERT]` 31 · `[CERT-doc]` 4 ·
  `[INFER]` 7 — the header legend blockquote contributes 2/1/1 of those, stripped for the ratio). Ratio
  `[INFER]`/`[CERT]` = 6/29 ≈ **0.21** — low, as expected for an **evidence** block built almost entirely
  from direct, mechanically-computed inventory comparison rather than deduction; every `[INFER]` above is
  explicitly flagged inline (naming-convention/role inferences in §13.4.4 and §13.5, plus the "not shipped
  in the beta" reading of §13.4.4(d-1)'s absence-in-docDeveloper.jar findings).
- **Artifacts.** Block file written at `/home/cristian/niagara5-research/niagara5-block13.md`. Per this
  task's explicit instruction, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` were **not** touched and no file
  under `tools/` was added — the caller owns integrating this block into corpus state.
- **MCP-doc snapshots.** N/A — no context7/MCP-doc citation used in this block.

## 13.9 — Open questions / child gaps

- **[B13-G1]** Confirm or refute genuine removal (vs beta-only omission) for the 49 §13.4.4(d-2) Tridium
  code modules with zero N5 package overlap — needs either an N5 GA build or the official web-hosted
  Niagara 5 release notes, neither checked here.
- **[B13-G2]** Why is the `cloudLink*` family (7 modules) stamped `vendorVersion="5.0.0.26"` while every
  other module in this same beta snapshot reads `5.0.0.28` (§13.5) — stale build artifact or an
  independently-versioned CloudLink release train?
- **[B13-G3]** Resolve the 59 §13.4.4(d-1) unmatched doc-guide jars against the official Tridium web doc
  portal (ties into the already-DEFERRED `B4-G6`docUser question and the pending `B10-G2` full
  breaking-changes list).
- **[B13-G4]** Read the actual N5 Gradle module-build plugin code (n-module/niagara plugin, [B2] territory)
  to confirm *why* N5's `module.xml` `<dependencies>` lists fewer explicit entries than N4's per-profile
  union (§13.6) — declaration-list slimming via JPMS `requires` transitivity vs an actual explicit-dep
  policy change; feeds `B2-G6`.
- **[B13-G5]** Confirm what Tridium's "Atlas" hardware target (`platHwScanAtlas`, §13.4.4/§13.5) physically
  is — a specific new JACE/host SKU — via web or shipped install docs; currently only the naming-convention
  parallel with the 7 retired `platHwScanJ*` modules is measured, not the hardware identity itself.
- **[B13-G6]** Investigate whether the Honeywell-branded-content-under-Tridium-vendor pattern (§13.5,
  `cloudLinkForge`/`cloudLinkHonSbp`) extends to licensing/feature-gating (ties into [B6]'s
  `LicenseManager.checkFeature` gap `B6-G3`) — does a stock N5 install require a Honeywell-specific license
  feature to unlock these modules' function, or are they gate-free by default?

## 13.10 — Connections

- **[B1]** — this block's frozen N4/N5 module-set snapshot is the same `tools/n5-modules.py` inventory B1
  used to document the packaging model; §13.1's `n5Hello.jar` finding and the 247-jar count corroborate B1
  §1.1's own count.
- **[B4]** — §13.4.3's 13-module doc-guide merge and the broader `docDeveloper.jar` consolidation this block
  measures per-module is the direct application of B4's `docDeveloper.jar` census (`N5-G12`) to this gap's
  question; §13.4.4(d-1)'s `docUser` absence corroborates B4-G6 (deferred) rather than resolving it.
- **[B10]** — §13.4.1's `app`-module-removed finding is B10's own BC-02 row, independently re-derived here
  by full-text search rather than assumed; this block's `B13-G1`/`B13-G3` extend B10's still-open `B10-G2`
  (full breaking-changes list) and `B10-G5` (n5mig migrator) territory.
- **[B2]** — §13.6's dependency-declaration-list shrinkage is a build-toolchain question that belongs next
  to B2's Gradle-plugin coverage (`N5-G6`); `B13-G4` is filed as a follow-up to B2's own `B2-G6` gap.
- **[B5]** — §13.5's `niagaraSync` entry directly feeds the already-open `B5-G3` gap (new
  `BINiagaraSyncCapableComplex` on status types).
- **[B6]** — §13.5's Honeywell-branded-under-Tridium-vendor finding and `B13-G6` extend B6's licensing-layer
  coverage (feature-gating of vendor-labeled content).
- **[N5-G9]/[N5-G10]** — §13.5's `totpAuth` and `cloudLink*`/`niagaraCloud` entries are direct inventory for
  these two still-pending gaps' subject modules.
