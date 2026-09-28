# Niagara N5 (5.0.0.28 beta, Java 25) — Research State

MODE: frontier (METHODOLOGY §8) — breadth-first coverage map; high [INFER]/[CERT] ratio expected, deep-dive passes later.
focus-distinctness: OK — no prior N5 coverage; niagara-research (target #1) covers N4 only and is used as REMITTANCE baseline for N4↔N5 deltas.
ANGLE: decompiled-Java + packaged resources + shipped docs (docSource.jar originals, docDeveloper.jar guides) of the N5 module set; N4→N5 delta is the organizing axis.

> Operational state consumed by the loop (Research-SDD). Mirrored in engram
> (`research/<target>/gaps`, `research/<target>/progress`). Visible and versionable source.

<!-- State envelope (research-state.v1) — ported from gentle-ai's verify-result/v1. The prose sections below
     are the human-readable MIRROR. Seed/refresh it MECHANICALLY — never hand-edit the ints — with:
       research-sdd-status.sh <corpus> --sync-state
     GATED vs DECLARED — be honest about which is machine-validated:
       • FAIL-gated against ground truth by verify-state.sh (a stale value BLOCKS the loop): covered_blocks
         (block files on disk) · investigable_open (pending non-blocked backlog rows = the STOP-critical
         count) · blocked_open (## Blocked gaps entries). These cannot drift without a hard FAIL.
       • BACKLOG-ANCHORED WHEN MARKED — requires_execution_open (the §19 build-loop STOP counter): mark each
         OPEN build/PoC gap as a backlog row whose Status column carries `requires-execution` (see the example
         row below); verify-state then derives the open count from those rows and FAILs ONLY the premature
         build-STOP hazard (requires_execution_open: 0 while marked-open rows remain — the exact analog of the
         investigable gate). Other divergence is a WARN. A corpus that tracks its build gaps in prose only is
         still valid, but that count is NOT machine-gated — mark the rows to get the gate.
       • DECLARED-only — read from the prose and carried forward, NOT disk-validated: gaps_closed · known_gaps.
         verify-state only cross-checks the coverage ratio for the all-closed-while-pending desync (CHECK D),
         not these absolute values — keep them truthful by hand.
       • MANUALLY-MAINTAINED — undocumented_findings: the researcher increments this when saving a project/
         decision finding to memory (engram) WITHOUT a corresponding block; decrements it when the block is
         written. Nothing in the kit observes memory saves — this is discipline, not automation. Gate behaviour:
         verify-state.sh WARNs when > 3; FAILs when > 6; research-sdd-archive.sh refuses to close when > 0.
         Memory is a MIRROR, not the record. A finding that exists only in memory is undocumented.
       • ADVISORY — blocks_since_retro: cumulative blocks written since the last retro was run. Increment it
         manually each time a block is written; reset to 0 when you run a retro. research-sdd-status.sh WARNs
         (never FAILs) when this exceeds 10, surfacing the §18 cadence reminder. Omitting the field is legal;
         CHECK P18 is silent when the field is absent. Seed it at 0 for a new research state.
       • OPTIONAL — block_scope: controls how verify-state counts on-disk block files for CHECK A.
         Omit for the common case (§16 per-focus prefix layout — each focus has its own block prefix).
         Set to 'shared-global' when ALL focuses share ONE corpus-wide block-file prefix (e.g. niagara-
         mental-model-bloque). Under shared-global, covered_blocks = blocks ATTRIBUTED to this focus
         (from a '## Covered blocks' list, else distinct B<n> ids in '## Iteration history' Block column);
         the corpus-wide total is printed as INFO only. When no attributed ids are found, CHECK A reports
         'unverifiable' as INFO — never FAIL against the corpus total (§7 three-state rule). Legal values:
         'per-focus' | 'shared-global'. Present but empty, or any other value, is a hard FAIL — absent
         (omitted) is always legal.
     Field names use UNDERSCORES on purpose: they must never collide with the prose greps below. -->
<!-- research-state.v1 -->
schema: research-state.v1
covered_blocks: 106
gaps_closed: 355
known_gaps: 466
investigable_open: 20
requires_execution_open: 16
blocked_open: 63
deferred_open: 12
undocumented_findings: 0
blocks_since_retro: 16
last_iteration_ts: 2026-09-28T05:30:00Z
<!-- /research-state.v1 -->
<!-- last_iteration_ts is always present — write the ISO-8601 UTC timestamp on every block commit;
     applies to every corpus (single-focus and campaign alike); the stall-detection instrument reads it
     from this envelope; do not pre-fill with a placeholder, update it when committing a block. -->

## Coverage

- **Covered blocks**: 106 (B1..B106)
- **Coverage metric**: 355 / 466 closed
- **Last iteration**: 2026-09-28 — wave 11: B99–B106 (8 delegated sonnet writers), 68 gaps closed/narrowed (7 already-covered confirmed), 5 moved to blocked

## Gap-backlog

| Priority | Gap | Artifact type / source | Status |
|---|---|---|---|
| high | N5-G1 Module packaging: one jar per module + JPMS module-info.class + module.xml schemaVersion 5 — how rt/ux/wb runtime profiles are expressed without the -rt/-ux split | Java bytecode + module.xml | ✅ covered — B1 |
| high | N5-G2 Module inventory delta N4.14 (OptimizerSupervisor) vs N5 5.0.0.28: added / removed / merged / renamed modules | jar listing + module.xml | ✅ covered — B13 |
| high | N5-G3 Bytecode, signing and obfuscation profile: class major 69, NIAGARA4.SF signing, ZKM vs N4, decompiler bake-off | Java bytecode + META-INF | ✅ covered — B30 |
| high | N5-G4 Java 17-25 language feature adoption in Tridium code (records, sealed, switch patterns, virtual threads, text blocks) | Java bytecode (javap attributes) | ✅ covered — B25 |
| high | N5-G5 Core API delta javax.baja.* N4 docSource vs N5 docSource (removed / deprecated / new types) | docSource originals | ✅ covered — B5 |
| high | N5-G6 N5 module build toolchain: etc/m2 gradle plugins (n-module, n-java, niagara, nap) and devkit vs N4 Java 8 + slotomatic | gradle plugin jars/poms + devkit | ✅ covered — B2 |
| high | N5-G7 Boot/runtime: NRE on JRE 25, bin layout, nre.properties / system.properties, JPMS module loading | install bin/defaults + baja sys | ✅ covered — B3 |
| high | N5-G8 Licensing layer delta (premise corrected: subscription package is NOT new — exists in N4 per B6) | baja license packages | ✅ covered — B6 |
| medium | N5-G9 Security/authn surface: totpAuth (new), oauth2, saml, clientCertAuth, firewall, authn (premise corrected: tls.jar is the Veeder-Root tank driver, not TLS crypto) | module bytecode | ✅ covered — B12 |
| medium | N5-G10 Cloud surface new in N5: cloudLink*, niagaraCloud, niagaraSync | module bytecode | ✅ covered — B18 |
| medium | N5-G11 UI stack: themeN5 (new), uxBuilder, hx, bajaux, webEditors, JxBrowser in workbench | module bytecode + js resources | ✅ covered — B21 |
| medium | N5-G12 Shipped documentation: docDeveloper.jar (8,817 files: guides, jsdoc, bajadoc) and rebuild of an N5 niagara-help index | doc jar | ✅ covered — B4 |
| medium | N5-G13 Station persistence/index: orientSystemDb, systemDb, systemIndex, niagaraSystemIndex, search | module bytecode | ✅ covered — B19 |
| medium | N5-G14 Control/alarm/history/schedule/kitControl delta — portability of our N4 modules (ColdRoomPan, CompPan, DashboardPan) | docSource + bytecode | ✅ covered — B20 |
| medium | N5-G15 Driver framework delta (driver, ndriver, basicDriver, bacnet, modbus*, niagaraDriver, fox) | module bytecode | ✅ covered — B22 |
| low | N5-G16 N4→N5 porting guide synthesis for own modules (what breaks: Java 8 APIs, removed modules, packaging) | synthesis of G1-G15 | ✅ covered — B50 |
| high | B2-G1 Slotomatic vs nap annotation processor division of labor (who generates slot code vs module-include.xml) | n-plugin jar + niagaraAnnotationProcessors | ✅ covered — B7 |
| high | B3-G3 PermissionManager default grant table (initThirdPartyPermissions/addPermissions) — N5 permission model that replaced java.policy | nre.jar bytecode | ✅ covered — B8 |
| high | B2-G7 Build a trivial N5 module end-to-end with the shipped gradle plugins (gradlew jar) and observe module.xml/module-info output | prototype build | ✅ covered — B9 |
| medium | B1-G2 N5 module loader method-body trace (ModuleManager / ModuleLayerInfo / NModuleModuleFinderFactory) | baja.jar com.tridium.sys.module | ✅ covered — B23 |
| medium | B3-G1 nre.module internals: NModuleModuleReader, NiagaraModuleReference, NiagaraJPMSAccessModifier (merges B1-G3/B1-G4) | nre.jar bytecode | ✅ covered — B23 |
| medium | B1-G5 Signature-verification gate parity N4 ModuleClassLoader vs N5 ModuleSetClassLoader | baja.jar bytecode | ✅ covered — B23 |
| medium | B3-G4 Map N4 19 java-permissions groups onto N5 NiagaraPermission taxonomy | nre.jar + N4 B635 | ✅ covered — B8 |
| medium | B2-G5 N5 JS build pipeline (node/yarn/grunt plugins) for -ux style web resources | m2 plugins | ✅ covered — B36 |
| medium | B2-G6 Delta list for our build-n4-module kit templates (.gradle.kts) against N5 plugin DSL | kit templates + B2 | ✅ covered — B51 |
| low | B1-G6 The 5 automatic-module jars (unterjar packaging) — why not explicit modules | jar manifests | ✅ covered — B95 |
| low | B2-G2 Meaning of the Compact3 javac argument in N5 plugins | n-plugin bytecode | ✅ covered — B89 |
| low | B2-G3 Read the TestNG Support in Niagara 5 doc | docDeveloper.jar | ✅ covered — B89 |
| low | B3-G5 securityBridge.jar 2-class bootclasspath shim | securityBridge.jar | ✅ covered — B65 |
| low | B2-G4 Does N5 niagaraTest still hit the N4 plugin zero-tests bug | prototype build | requires-execution → §19 (run niagaraTest on a sample module) |
| high | B4-G8 Deep-read official upgrade guides (upgradingToN5, upgradingUItoN5, upgradingJDK) + porting checklist for our modules | docDeveloper.jar doc/upgrade | ✅ covered — B10 |
| medium | B4-G1 Decode the help search index binary format doc/{words,postings,documents,worddocs}.dat | help.jar Searcher + dat files | ✅ covered — B59 |
| medium | B4-G5 N5 equivalent of N4 niagara-help jdk/ JDK-class bajadoc stand-ins | docDeveloper.jar | ✅ covered — B59 |
| low | B4-G3 Line-count N5 vs N4 shipped source (docSource) | docSource jars | ✅ covered — B93 |
| low | B4-G4 Confirm no javadoc-shaped artifact across all 1,013 N4 jars | N4 jars | ✅ covered — B103 |
| low | B4-G7 Census of N5 PDF manuals | install + doc jars | ✅ covered — B93 |
| low | B4-G2 Render bajadoc via HtmlCompilerMain | help.jar | requires-execution → §19 (run HtmlCompilerMain on a bajadoc file) |
| medium | B6-G1 com.tridium.nre.subscription in nre.jar (subscription bootstrap outside baja.jar) | nre.jar bytecode | ✅ covered — B34 |
| medium | B6-G3 Full caller enumeration of LicenseManager.checkFeature across all N5 jars (license-gated features map) | all module bytecode | ✅ covered — B11 |
| low | B6-G2 Code path of the security/licenses/conf directory | baja.jar license | ✅ covered — B34 |
| medium | B7-G1 Exact Gradle task-graph edge slotomatic ↔ compileJava ↔ nap processor | prototype build | ✅ covered — B9 |
| low | B7-G2 Defining module of niagara.rpc.NiagaraRpc (claimed by NullProcessor) | module bytecode | ✅ covered — B95 |
| high | B8-G4 Confirm or refute that outbound HTTP/sockets from third-party modules are ungated in N5 (okhttp3/Jetty client layer) | nre.jar + bin/ext + module bytecode | ✅ covered — B15 |
| medium | B8-G3 Are reflection / JMX / native-library / system-property accesses gated elsewhere in N5 | nre.jar + baja.jar | ✅ covered — B33 |
| low | B8-G1 ModifyProtectedPropertiesPermission construction sites | module bytecode | ✅ covered — B86 |
| low | B8-G2 Permission-denial log filename: code vs doc discrepancy | nre.jar | ✅ covered — B86 |
| medium | B10-G1 Compile-verify the 15-item porting checklist by building DashboardPan/CompPan/ColdRoomPan against N5 | prototype build | ✅ covered — B16 |
| high | B10-G5 The n5mig station migration application: where it ships, what it transforms (N4 station → N5) | install bin + migration/migrator modules | ✅ covered — B14 |
| low | B10-G3 BFoxProxySession.getRemoteNiagaraVersion signature/package | docSource + javadoc | ✅ covered — B104 |
| low | B10-G4 Re-run fox grep across our three modules to certify CHK-14 | our module sources | ✅ covered — B97 |
| low | B10-G6 DashboardPan-ux preview tooling has no N5-relevant surface | our module sources | ✅ covered — B97 |
| medium | B5-G3 niagaraSync subsystem (new BINiagaraSyncCapableComplex on status types) — feeds N5-G10 | niagaraSync.jar + baja | ✅ covered — B18 |
| medium | B5-G2 Does any Tridium or our own B* type rely on the removed BObject.equals override | baja + our sources | ✅ covered — B52 |
| medium | B5-G4 The javax.baja.web import sites in our modules vs the jakarta.servlet break | our module sources | ✅ covered — B52 |
| low | B5-G1 HsmManager: real N5 drop or N4 OEM-baseline artifact | N4 stock vs OEM jars | ✅ narrowed — B101 (residue → B101-G3) |
| high | B9-G2 Real niagaraTest run with a TestNG test in the PoC (settles B2-G4) | prototype build | ✅ covered — B16 (build+sign OK; niagaraTest platform-gated: test.exe Windows-only) |
| medium | B9-G3 Is com.tridium.n-java required per module or at root (wizard template omits it) | devkit templates + PoC | ✅ covered — B51 |
| low | B9-G4 NDriver / device-driver module scaffold on N5 | devkit templates | requires-execution → §19 (generator manifests traced in B97; run the NDriver/VideoDriver wizard) |
| high | B14-G1 Run n5mig -premigrate (dry-run report) on a copy of a real N4.15 station backup/bog (e.g. PANCCADIA) with and without our modules installed | n5mig.exe + station copy | ✅ covered — B17 (partial: run blocked by license tridium:nre; static census substituted) |
| medium | B14-G3 Open the ~26 unread migrator.jar converter types (driver/protocol bog converters) | migrator.jar | ✅ covered — B24 |
| medium | B14-G4 BBogMigrator 4-phase pipeline full read | migrator.jar | ✅ covered — B24 |
| low | B14-G2 propMigration.jar 8 declarative converter classes | propMigration.jar | ✅ covered — B24 |
| low | B14-G5 MigratorTypeResolver / MigratorOrdConverter / MigrationUtils | migrator.jar | ✅ covered — B24 |
| medium | B15-G2 Independent egress gate inside okhttp / jetty-client / jetty library internals | bin/ext third-party jars | ✅ covered — B55 |
| low | B15-G3 OS/platform-level egress control outside NiagaraPermission (daemon, platform firewall) | platform modules | ✅ covered — B81 |
| low | B15-G4 Full niagara.security.dashboard module: any provider surfacing network grants | security dashboard module | ✅ covered — B99 |
| medium | B12-G4 nftables firewall backend: N5-only? and is it PermissionManager-gated | nre.jar firewall | ✅ covered — B33 |
| medium | B12-G5 totpAuth enrollment UI flow and secret storage path | totpAuth.jar | ✅ covered — B38 |
| medium | B12-G6 SAML IdP servlet flow in N5 | saml.jar | ✅ covered — B38 |
| low | B12-G1 Location of the Nimbus OAuth SDK jar required by oauth2 | bin/ext + modules | ✅ covered — B95 |
| low | B12-G2 platCrypto daemon protocol | platCrypto.jar | ✅ covered — B94 |
| low | B12-G3 signingService Fox CSR protocol | signingService.jar | ✅ covered — B94 |
| low | B12-G7 LDAP v2/v3 bind details | ldap.jar | ✅ covered — B38 |
| low | B12-G8 SRP6 key exchange: new in N5 or carried over | baja/nre | ✅ covered — B38 |
| medium | B11-G1 Capacity licensing mode: Metrics.isUsingCapacityLicensing() and resource.limit | baja metrics + license | ✅ covered — B34 |
| low | B11-G3 Six dynamic (non-literal) checkFeature/getFeature call sites | module bytecode | ✅ covered — B90 |
| low | B11-G4 Upgrade B11 bytecode-offset citations to source file:line via full decompile | organized/ decompile | ✅ narrowed — B105 (residue → B105-G1) |
| deferred | B11-G2 OEM-branded module absence (Honeywell UI, eSignature): edition gap vs removal | OEM N5 build | pending (parked; needs an OEM N5 build) |
| medium | B13-G4 Why N5 module.xml declares fewer explicit dependencies (declaration slimming) | module.xml + build plugin | ✅ covered — B51 |
| low | B13-G2 cloudLink family stuck at vendorVersion 5.0.0.26 | module.xml | ✅ covered — B88 |
| low | B13-G5 What the Atlas hardware (platHwScanAtlas) is | platHwScanAtlas.jar | ✅ covered — B101 |
| low | B13-G6 Licensing of Honeywell-branded modules shipped under vendor Tridium | cloudLinkForge/HonSbp | ✅ covered — B101 |
| medium | B18-G2 cloudLink AMQP link-handler method-body trace | cloudLink.jar | ✅ covered — B42 |
| medium | B18-G7 Fate of N4 nCloudDriver (Azure IoT / Forge) in N5 | N4 vs N5 modules | ✅ covered — B42 |
| low | B18-G3 Per-provider channel config classes (Forge / HonSbp) | cloudLink satellites | ✅ covered — B42 |
| low | B18-G4 Other BINiagaraSyncCapableComplex consumers (full-tree search) | organized/ decompile | ✅ covered — B37 |
| low | B18-G5 NCS-Agent registration vs cloudLinkNcs station identity convergence | NCS-Agent + cloudLinkNcs | ✅ covered — B96 |
| low | B18-G6 Deeper NCS-Agent Go binary RE beyond strings | NCS-Agent Go binary | ✅ narrowed — B96 (residue → B96-G1) |
| medium | B19-G1 BOrientSystemDb at-rest AES encryption toggle: new in N5 or pre-existing | orientSystemDb.jar vs N4 | ✅ covered — B57 |
| low | B19-G2 EncryptionKeySource enum in N4 (never decompiled there) vs N5 five members | N4 baja decompile | ✅ covered — B57 |
| low | B19-G4 KeyRing/SecurityInitializer proprietary blocker unchanged in N5 | nre/baja | ✅ covered — B43 |
| medium | B19-G5 OrientDB 3.2.23 → 3.2.55 on-disk compatibility for migrated stations | prototype run | requires-execution → §19 (open an N4 systemDb store with the N5 OrientDB libs) |
| medium | B17-G2 Why wb.exe boots on the unlicensed beta while n5mig/station do not (tridium:nre gate path) | nre.jar + launchers | ✅ covered — B53 |
| low | B17-G3 Reconstruct the native launcher VM/module-path args to run n5mig via java | bin launchers + nre.dll | ✅ covered — B87 |
| medium | B20-G2 niagaraSync ticks integration in kitControl BLoopPoint (BNiagaraSyncTicks) semantics | kitControl + niagaraSync | ✅ covered — B37 |
| medium | B20-G3 BIActionAuditProvider old-value audit path end-to-end | baja security + control | ✅ covered — B41 |
| medium | B20-G4 History rollover mechanism after BCapacity storage-size mode removal (migration hazard) | history.jar | ✅ covered — B26 |
| low | B20-G5 Decompile control/alarm/kitControl/schedule to source for file:line citations | organized/ decompile | ✅ covered — B70 |
| low | B21-G1 uxBuilder ux/make + ux/fe sub-packages: new vs N4 | uxBuilder.jar | ✅ covered — B75 (already-covered; confirmed in wave 11) |
| low | B21-G2 JxBrowser vs JavaFX WebView default selection in Workbench | workbench.jar | ✅ covered — B75 (already-covered; confirmed in wave 11) |
| medium | B21-G3 CSP / security headers served by niagara.web / jetty (static half) | web.jar + jetty | ✅ covered — B27 (static half) |
| low | B21-G4 Stale JxBrowser 7.30.3 log string vs 9.5.0 engine | jxBrowser.jar | ✅ covered — B79 |
| high | B16-G1 Run niagaraTest on the ColdRoomPan TestNG test via the Windows test.exe (WSL interop) — may hit the tridium:nre license gate | prototype run | ✅ covered — B29 (test.exe blocked by license tridium:nre; plain TestNG 51/51) |
| high | B16-G6 Port the 5 N4 JUnit4 ColdRoomPan tests to TestNG and write a JUnit4→TestNG recipe | our module tests | ✅ covered — B29 |
| high | B16-G7 Port CompPan and DashboardPan (multi-part rt/ux/wb, jakarta servlet) with the B16 recipe | prototype build | ✅ covered — B28 |
| medium | B16-G2 Does a multi-module group like DashboardPan still need a parent grouping file | devkit templates + build | ✅ covered — B28 |
| low | B16-G3 Locate the TestNG Support in Niagara 5 doc | docDeveloper.jar | ✅ covered — B89 |
| low | B16-G5 moduleTest dependency vendorVersion truncated 2.0.7 → 2.0 | n-plugin | ✅ covered — B51 |
| medium | B22-G1 Decompile bacnetUtil to resolve the Descriptor interface behind BC-10 | bacnetUtil.jar | ✅ covered — B35 |
| medium | B22-G3 Which other bundled drivers still extend the deprecated basicDriver chassis | driver modules | ✅ covered — B35 |
| low | B22-G4 niagaraDriver logic diff N4→N5 | niagaraDriver.jar | ✅ covered — B35 |
| low | B22-G2 Compile a basicDriver-based module on N5 | prototype build | requires-execution → §19 (build a minimal basicDriver module against the local mirror) |
| medium | B23-G1 PROGRAM ModuleType is dead code: where program objects actually load (com.tridium.program) | program.jar | ✅ covered — B32 |
| medium | B23-G3 Is skipModuleValidation blacklisted on the N5 command line | nre + launchers | ✅ covered — B53 |
| low | B23-G2 Locate com.tridium.crypto.core (absent from nre/baja) | bin/ext + modules | ✅ covered — B95 |
| low | B23-G5 NreInstantiator DI plumbing | nre.jar | ✅ covered — B95 |
| low | B23-G6 Prove or refute module.xml vs module-info dependency divergence | module census | ✅ covered — B95 |
| high | B24-G6 No converter exists for tagdictionary (105), kitControl (100), nrio (96) PANCCADIA objects — confirm they load unchanged in N5 (type names, slot compatibility) | migrator + module registry | ✅ covered — B31 |
| medium | B24-G2 Census the PANCCADIA points/histories/alarm stores beyond config.bog | PANCCADIA station copy | ✅ covered — B58 (narrowed: this Windows Workbench path holds only config.bog + empty alarm.adb; real runtime data is elsewhere) |
| low | B24-G3 Tabulate the 180-entry zwave removal type list | migrator.jar | ✅ covered — B66 |
| low | B24-G4 MigrationUtils (40 static methods) line-by-line read | migrator.jar | ✅ covered — B66 |
| low | B24-G5 BBackupDistMigrator / BPxMigrator / premigrate classes full bodies | migrator.jar | ✅ covered — B66 |
| medium | B27-G3 NiagaraConstraintSecurityHandler / NiagaraAuthenticator: web authn/authz proper | jetty.jar + web.jar | ✅ covered — B41 |
| medium | B27-G6 Adopt the real x-niagara-csrfToken in DashboardPan-ux on N5 instead of the hand-rolled X-Requested-With guard (design note) | web.jar CsrfUtil + our module | ✅ covered — B52 |
| low | B27-G2 Per-module jetty-web.xml census | all modules | ✅ covered — B72 |
| low | B27-G4 NModuleInfo.isWar() definition | baja/jetty | ✅ covered — B68 |
| low | B27-G5 hx.jar WebAppContext registration path | hx.jar | ✅ covered — B68 |
| low | B26-G2 Can a raw property-sheet string edit construct a restrictBy=2 capacity on N5 | history + workbench | ✅ covered — B72 |
| low | B26-G3 BHistoryDbTable subclasses: alternate capacity enforcement | history.jar | ✅ covered — B72 |
| low | B26-G4 BTypeSpecConverter generic simple-value handling | migrator.jar | ✅ covered — B72 |
| low | B29-G5 compileModuleTestJava "cannot determine module name" message root cause | n-plugin | ✅ covered — B89 |
| low | B29-G3 assertArrayEquals mapping in the port script | tools/port-junit4-to-testng.py | ✅ covered — B97 + tools/port-junit4-to-testng.py fix (assertArrayEquals → Assert.assertEquals, TDD) |
| low | B25-G1 instanceof-pattern adoption (bytecode-invisible) via decompiled sources | organized/ + docSource | ✅ covered — B90 |
| low | B25-G2 Classify the 34 ambiguous Deque-family SequencedCollection call sites | bytecode census | ✅ covered — B80 |
| medium | B25-G3 Full 253-jar jdeprscan --for-removal pass | all jars | ✅ covered — B44 |
| low | B25-G4 Read the switch logic of control.jar B*Writable pattern switches | control.jar | ✅ covered — B70 |
| medium | B32-G2 Compile a program object that depends on a non-default module (readability end-to-end) | prototype run | requires-execution → §19 (needs a running station; blocked with the license gate) |
| low | B32-G4 Any station/platform flag relaxing mandatory program signing beyond dev-license test mode | program.jar + nre | ✅ covered — B99 |
| low | B30-G1 Format and verifier of the bin/ext <jar>.jar.sig sidecars | bin/ext + nre | ✅ covered — B76 |
| medium | B30-G3 N5 embedded trust anchor that accepts the Honeywell code-signing chain | nre/baja crypto | ✅ covered — B53 |
| low | B30-G4 Full N4 obfuscation census (beyond the 53-module ZKM sample) | N4 organized/ | ✅ covered — B90 (already-covered; confirmed in wave 11) |
| low | B31-G1 Slot diff for 5 types in the 4.14→4.15 version gap (needs an N4 4.15 decompile) | N4 4.15 jars | ✅ covered — B84 |
| low | B31-G3 Re-read BWebBogConverter / BJettyQoSFilterMigrator property lists | migrator.jar | ✅ covered — B82 |
| low | B31-G5 box HistoryChannel/AlarmChannel parent swap BBoxChannel → BWrapperBoxChannel | box.jar | ✅ covered — B92 |
| medium | B35-G1 niagaraSync package semantics (standby/active RPC state machine in niagaraDriver) | niagaraSync + niagaraDriver | ✅ covered — B37 |
| low | B35-G2 BNiagaraEdgeLiteStation | niagaraDriver | ✅ covered — B73 |
| low | B35-G5 BFoxClientWebsocketBehavior / BReachableStations deeper read | niagaraDriver + fox | ✅ covered — B73 |
| medium | B33-G3 All callers of SystemPropertiesUtil.setSystemProperty (ungated except a 24-key denylist) | all modules | ✅ covered — B40 |
| medium | B33-G4 BServerPort.adapter → nft rule-hint injection reachability | nre + baja | ✅ covered — B40 |
| medium | B33-G5 Where niagara.firewall.enabled / frontend=nft are set by default (platform template?) | install + platform | ✅ covered — B40 |
| low | B33-G1 JMX usage across the remaining modules | all modules | ✅ covered — B80 |
| low | B33-G6 Operational impact of the firewall losing port-redirect (N4 pf) in N5 nft | platform docs + code | ✅ covered — B94 |
| high | B28-G7 niagara.alarm transitive dependency on javafx/batik platform modules forces stub module-info jars when compiling third-party modules on Linux — find the supported way (Windows javac.exe? SDK module path?) | n-plugin + alarm/gx/bajaui module-info | ✅ covered — B39 |
| medium | B28-G2 Batik (org.apache.xmlgraphics) provider: JavaFX confirmed in the bundled JRE release MODULES (7 javafx.* modules); batik not a JRE module and svgBatik.jar holds no org/apache classes | jre + bin/ext + modules | ✅ covered — B39 |
| low | B28-G1 Fate of the N4 test-wb module in N5 | modules | ✅ covered — B64 |
| medium | B28-G3 Does the Windows jre/bin/javac.exe resolve niagara.alarm without stubs | prototype build | ✅ covered — B39 |
| medium | B34-G3 Caller of AuthenticatedLicenseRetrievalUtil (perpetual LicenseAccessKey flow) | nre + workbench | ✅ covered — B53 |
| low | B34-G1 Backup-restoration write site for the subscription cache | nre | ✅ covered — B71 |
| low | B34-G4 Workbench UI consumer of the LicenseAccessKey flow | workbench | ✅ covered — B71 |
| low | B34-G5 N4 nre.jar client-package comparator for subscription | N4 nre | ✅ covered — B71 |
| low | B34-G6 Is security/licenses/conf N5-only | N4 vs N5 | ✅ covered — B101 |
| low | B36-G1 Read doc/js/buildingJS.html and doc/requirejs.html fully | docDeveloper.jar | ✅ covered — B75 (already-covered; confirmed in wave 11) |
| medium | B36-G2 Live gradlew gruntBuild / gruntCi run on a JS module | prototype build | requires-execution → §19 (needs node/npm on PATH + a JS module scaffold) |
| low | B36-G3 Locate the grunt-niagara successor npm package contents | m2 + npm | ✅ covered — B102 |
| low | B38-G1 Account-lockout defaults: N4 vs N5 provenance | baja security | ✅ covered — B62 |
| medium | B38-G2 SP-side SAML signature algorithm allowlist | saml.jar | ✅ covered — B61 |
| low | B38-G3 LDAP Kerberos/GSSAPI location | ldap + kerberos | ✅ covered — B81 |
| low | B38-G4 SRP6 group size cross-check | nre/fox | ✅ covered — B98 |
| high | B37-G6 HA-ready design for our modules under niagaraSync: replace raw Clock.schedule timers with BNiagaraSyncTicket, state as Properties, BNiagaraSyncTicks, implement BINiagaraSyncCapableComplex (design note + PoC) | our modules + niagaraSync API | ✅ covered — B45 |
| low | B37-G2 Three driver-specific sync-folder classes | bacnet/modbus/niagaraDriver | ✅ covered — B73 |
| low | B37-G4 niagaraSync license-fault severity wiring | niagaraSync | ✅ covered — B92 |
| low | B37-G5 modbusAsync/modbusTcp chassis lineage | modbus modules | ✅ covered — B73 |
| high | B41-G6 DashboardPan N5 write path: pass the servlet request niagara.context (authenticated user) into set()/invoke so writes land in AuditHistory with user and old→new value (design + PoC in the ported copy) | our module + web/baja | ✅ covered — B46 |
| medium | B41-G1 SecurityAuditEvent / SecurityAuditor full mapping | baja security | ✅ covered — B54 |
| low | B41-G2 JAAS Subject / AddSubjectFilter contents | web.jar | ✅ covered — B68 |
| low | B41-G3 Jetty LoginService / UserIdentity resolution | jetty.jar | ✅ covered — B68 |
| low | B41-G5 Do first-party N5 servlets thread niagara.context through to writes | web modules | ✅ covered — B68 |
| low | B42-G2 Three cloudLinkExtension satellite modules | cloudLinkExtension* | ✅ covered — B67 |
| low | B42-G3 retriableError() classification body | cloudLink | ✅ covered — B67 |
| low | B42-G4 Authoritative statement on nCloudDriver retirement (newer releases / web) | web | ✅ narrowed — B88 (residue → B88-G2) |
| low | B42-G5 Forge message-handler classes | cloudLinkForge | ✅ covered — B67 |
| low | B42-G6 Throttle / backpressure numeric defaults | cloudLink | ✅ covered — B67 |
| high | B43-G1 KeyRing alias rename javax.baja.security.BAes256PasswordEncoder.key → niagara.security.BAes256PasswordEncoder.key: does N5 (or n5mig) remap it, or do migrated stations lose reversible passwords? | nre KeyRing + migrator | ✅ covered — B47 (MITIGATED by n5mig force-clear/passphrase path; PANCCADIA uses external encoding (3 pbkdf2-aes-256 secrets)) |
| low | B43-G2 N4 orientSystemDb default-encryption parity (narrows B19-G1) | N4 orientSystemDb | ✅ covered — B57 |
| low | B43-G3 N4 EncryptionKeySource member count | N4 baja decompile | ✅ covered — B57 |
| low | B39-G2 Does the batik-awt-util version matter beyond 1.19 | prototype build | ✅ covered — B106 |
| medium | B39-G3 Why 3 other absent gx.jar requires (batik.transcoder, swt win32, owasp.encoder) never fail compilation | javac module resolution | ✅ covered — B55 |
| low | B39-G4 Runtime behaviour of a module that really calls JavaFX/Batik APIs with these artifacts | prototype build | requires-execution → §19 (needs a licensed station to run) |
| low | B40-G1 OPC UA component-name charset vs ruleHintOverride validation | opcUaServer + baja | ✅ covered — B94 |
| medium | B40-G2 Which BComponentSpace subtype a live station instantiates (decides whether BTunnelService ruleHintOverride is validated) | baja + station | ✅ covered — B61 |
| low | B40-G4 N4 netsh / CAP_NET_ADMIN host-firewall mechanism | N4 platform | ✅ covered — B94 |
| medium | B46-G1 Slotomatic-generated setters pass null Context (setXxx → setString(prop, v, null)): framework-wide audit implication and recommended pattern | slotomatic + baja | ✅ covered — B49 |
| medium | B46-G2 Implement the x-niagara-csrfToken check in the DashboardPan-ux port | our module + web.jar | ✅ covered — B52 |
| low | B46-G3 Should the 3 read-side BOrd.get(this, null) resolutions use the request Context | our module | ✅ covered — B91 |
| deferred | B46-G5 Port the audited-write fix back into the live N4 DashboardPan source (same N4 gate B829/B830) — product change in the client repo, needs operator decision | client repo | pending (parked; recommendation only — outside research scope) |
| low | B47-G1 Confirm the vestigial source-.kr extraction code has no live call site (Premigrate + bytecode xref) | migrator.jar | ✅ covered — B66 |
| low | B47-G2 Purpose of the source-.kr extraction machinery (dist-container encryption?) | migrator.jar | ✅ covered — B98 |
| low | B47-G3 AxPasswordUtil.usesPasswordEncodings definition | migrator/baja | ✅ covered — B82 |
| medium | B48-G1 Resolve the public Java 21 vs Java 25 contradiction (first-party says 25; code confirms JRE 25.0.4) | web + install | ✅ covered — B56 (narrowed: Java 25 authoritative (first-party + local jre/release); HA name = Niagara Sync) |
| medium | B48-G5 N5 HA/niagaraSync 'limited availability first' signal — scope of niagaraSync at GA | web + niagaraSync | ✅ covered — B56 (narrowed: Java 25 authoritative (first-party + local jre/release); HA name = Niagara Sync) |
| deferred | B48-G2 Read the login-gated docs.niagara-community.com N5 breaking-changes page | Developer Program credentials | pending (parked; needs Developer Program login) |
| deferred | B48-G3 Re-run the 49 absent-module check on the N5 GA build (target Dec 2026) | N5 GA install | pending (parked; needs a GA build) |
| deferred | B48-G4 Watch for a post-GA nCloudDriver statement | web after GA | pending (parked; revisit after GA) |
| medium | B49-G2 Trace N5 NiagaraRpc servlet/BOX dispatch for Context injection into @NiagaraRpc methods | web/box modules | ✅ covered — B54 |
| low | B49-G3 Feasibility of a Context-taking overload in Slotomatic output | slotomatic | ✅ covered — B74 |
| low | B49-G4 Whole-corpus census of generated action invoke wrappers | organized/ | ✅ covered — B74 |
| low | B44-G1 The 13 cloudLink* finalize() overrides: resource, shared base class, Cleaner replacement | cloudLink family | ✅ covered — B67 |
| medium | B44-G2 AccessController-family call sites in jetty/platform/hx: inert after SecurityManager removal or live authorization | jetty/platform/hx | ✅ covered — B54 |
| low | B44-G4 svgBatik ThreadDeath usage | svgBatik | ✅ covered — B106 |
| deferred | B44-G3 Re-run jdeprscan on the 29 classpath-incomplete jars with vendor SDKs (Prosys OPC UA etc.) | vendor SDKs | pending (parked; needs licensed vendor SDKs) |
| low | B45-G2 Census other modules for list/queue state under niagaraSync (no stock BSimple list; CSV String precedent) | organized/ | ✅ covered — B73 |
| medium | B50-G1 Driver-module N5 build PoC (ndriver or BDeviceNetwork chassis) | prototype build | requires-execution → §19 (scaffold + build a minimal ndriver module) |
| low | B50-G2 Native-module (npsdk) build on N5 | m2 native plugins | ✅ covered — B74 (already-covered; confirmed in wave 11) |
| low | B50-G6 Re-verify the §2.13 @NiagaraRpc Context-injection mechanism on the N5-side NiagaraRpcServlet (text corrected from block50) | devkit.jar | ✅ covered — B97 |
| low | B54-G1 Is -Djava.security.manager set by the N5 launcher (moot: vulnerable Subject API never called) | launchers | ✅ covered — B63 |
| low | B54-G3 Open SecurityAgent / SecurityProviderAdvice directly | nre.jar | ✅ covered — B65 |
| low | B54-G4 BUserService.auditLoginAttempt appears dead code | baja | ✅ covered — B69 |
| low | B54-G5 BOrionSecurityAudit parallel audit DB | orion | ✅ covered — B69 |
| medium | B51-G2 Where Flags.TRANSIENT/OPERATOR live in N5 (niagara.sys.Flags?) — lints keyed on Flags vocabulary | baja | ✅ covered — B60 |
| medium | B51-G5 Does any real N5 gradle.kts need per-profile splitting at all (single-jar world) | PoC build files | ✅ covered — B60 |
| low | B51-G1 verify-module.sh stored check on N5 jars | prototype build | ✅ narrowed — B97 (residue → B97-G2) |
| low | B51-G3 lint-bundled-jar-class-version.sh major-version constants | kit lints | ✅ covered — B60 |
| low | B51-G4 rc-scan.sh and bog-audit.sh part-suffix (rt/ux/wb) assumptions | kit lints | ✅ covered — B97 |
| low | B51-G6 lint-wb-threading: Swing invokeLater vs JavaFX Platform.runLater on real N5 wb code | prototype build | ✅ covered — B97 |
| low | B51-G7 Measured N4 vs N5 explicit dependency counts | module.xml census | ✅ covered — B60 |
| deferred | B51-G8 Implement the build-n5-module kit fork in niagara-tools (9-step plan in B51 §51.7) | niagara-tools repo | pending (parked; separate kit campaign in niagara-tools with its own gates) |
| medium | B53-G3 niagara.commandLinePropertyDenyList is itself read via System.getProperty — can a -D override neuter the denylist (static hypothesis, measure) | nre/baja Nre | ✅ covered — B57 |
| low | B53-G2 portalApi LicenseDownload flow | portalApi | ✅ covered — B71 |
| low | B53-G4 Runtime cacerts contents (structure only) | install jre | ✅ covered — B94 |
| low | B53-G5 TPK pin vs Honeywell leaf key identity | nre + signed jars | ✅ covered — B77 |
| low | B53-G6 TRIDIUM_DEV_CA_CERT usage | nre | ✅ covered — B77 |
| low | B52-G1 CsrfUtil token compare is String.equals (not constant-time) — platform code, low practical severity | web.jar | ✅ covered — B91 |
| low | B52-G2 Frontend should refetch the CSRF token after a 403 | our module | ✅ covered — B91 |
| deferred | B52-G5 Port the CSRF + audited-write hardening back to the live N4 DashboardPan (product change, operator decision) | client repo | pending (parked; recommendation only) |
| low | B56-G2 Niagara Sync vs Cloud Suite licensing coupling | web + license features | ✅ covered — B71 |
| deferred | B56-G3 Supervisor Linux support at N5 GA | N5 GA docs | pending (parked; revisit at GA) |
| low | B56-G4 Survey the rest of the 2023 Loyalty Program Q&A transcript | web | ✅ covered — B93 |
| low | B57-G1 Are nre.properties-sourced JVM args also cmdline::-tagged (nre.dll disassembly) | nre.dll | ✅ covered — B63 |
| medium | B57-G2 How platDaemon spawns station.exe (no ProcessBuilder in the Java corpus) — remote reachability of JVM-arg injection | platDaemon + native | ✅ covered — B63 |
| low | B57-G4 N4 BogPasswordObjectEncoder semantics for shared/undefined | N4 baja | ✅ covered — B98 |
| low | B55-G1 Cross-check the transitive-vs-plain javac rule with the Windows javac.exe | prototype run | ✅ covered — B106 |
| low | B55-G2 Decompile okio-jvm for any egress hook | bin/ext okio | ✅ covered — B106 |
| low | B55-G4 Does any N5 module hit the okhttp-5.5.0 empty placeholder jar trap | bin/ext + builds | ✅ covered — B74 |
| low | B58-G1 alarm.adb N5-side format compatibility (no N5 alarm.jar decompile yet) | alarm.jar | ✅ covered — B78 |
| low | B58-G3 systemDb absent: unlicensed vs never-provisioned on this OEM build | install | ✅ narrowed — B101 (residue → B101-G1) |
| low | B58-G4 Decode alarm.adb header words 0x0C-0x20 | alarm.adb + tool | ✅ covered — B78 |
| low | B59-G1 Is niagara-help guide-search/devguide-search index-backed or linear scan | niagara-help tool | ✅ covered — B75 (already-covered; confirmed in wave 11) |
| low | B59-G2 BajadocIndex.lookup/ensureTagsLoaded internals (rendering of java.* refs) | help.jar | ✅ covered — B75 (already-covered; confirmed in wave 11) |
| low | B59-G4 docDeveloperAnalytics.jar own .dat index presence | docDeveloperAnalytics.jar | ✅ covered — B103 |
| low | B60-G1 ignoreRuntimeProfileCheck consuming logic/effect in N5 ModuleXml | n-plugin | ✅ covered — B89 |
| low | B60-G2 Version.strip(2) exact truncation algorithm | baja Version | ✅ covered — B89 |
| low | B60-G3 plat* cluster +17..+19 dependency gain N4→N5 cause | module.xml census | ✅ covered — B105 |
| low | B60-G4 html/file/fox/export cluster outsized N4→N5 dependency drop | module.xml census | ✅ covered — B105 |
| high | B61-G3 N5's consumer-side SAML (java-saml Util) accepts SHA-1/DSA-SHA1-signed IdP responses — the DEPRECATED_ALGOS reject flag is hardcoded false; weaker than Tridium's own IdP-side policy (security note for SAML SSO deployments) | saml java-saml-core | ✅ covered — B62 |
| medium | B61-G1 nre.dll CreateProcessA target + how niagarad triggers OS-level station start (B57-G2 refined) | native launchers | ✅ covered — B63 |
| medium | B65-G1 niagarad runs with the ByteBuddy permission layer inert (isTrustedDomain=true in NiagaraDaemon.Main); Java half confirmed — NiagaraDaemon has no nreMain so Nre.runClass path is unreachable | nre + platDaemon bytecode | ✅ covered — B69 |
| low | B62-G1 Did N4's bare JDK javax.xml.crypto.dsig provider independently restrict SHA-1 (N4 used older com.onelogin.saml.Utils with no allowlist) | N4 saml + JDK | ✅ covered — B98 |
| low | B62-G2 N4 runtime-crypto jar decompile for SRP6 KeyExchange (re-scoped B38-G4) | N4 nre-equivalent | ✅ covered — B98 |
| low | B63-G2 nre.dll module-path / java.library.path / niagara.* %s runtime-value origin trace | nre.dll disasm | ✅ covered — B87 |
| low | B63-G4 Disassemble nre.dll's shared snprintf-style command-line helper | nre.dll disasm | ✅ covered — B87 |
| low | B64-G3 Independently open the third-party CloudConnector_Sentience doc (WebSearch-summary confidence only) | web | ✅ covered — B106 |
| low | B64-G4 Full page-by-page pass of the Summit-2026 128-slide Module Transition deck | web PDF | ✅ covered — B93 |
| low | B64-G5 Same deck: enumerate any further module-level breaking-change rows beyond BACnet | web PDF | ✅ covered — B93 |
| low | B65-G2 PermissionUtil.isPrivileged frame-classification rule | nre bytecode | ✅ covered — B69 |
| low | B65-G4 securityBridge.jar -Xbootclasspath/a: loading mechanism (residual half of B3-G5) | securityBridge.jar + launcher | ✅ covered — B87 |
| low | B66-G1 backup.jar design-intent: can BBackupService produce a KeyRing-protected .dist the dead migrator code consumed (residual B47-G2) | backup.jar | ✅ covered — B98 |
| low | B66-G2 BPxMigrator.processFormat ReflectCall.eval semantics | migrator.jar | ✅ covered — B82 |
| low | B67-G1 Deliberate-vs-vestigial intent of the empty finalize() idiom (needs external changelog) | cloudLink + web | ✅ covered — B106 |
| low | B67-G2 MessageWrapper.canRetry() logic — the real retry-count gate | cloudLink | ✅ covered — B88 |
| low | B67-G3 Whether Forge's Azure-Blob file-upload reuse implies an Azure-owned backend or a shared client primitive | cloudLinkForge + cloudLinkAzure | ✅ covered — B88 |
| low | B67-G4 The ~30 remaining unread Forge msg/ classes | cloudLinkForge | ✅ narrowed — B88 (residue → B88-G1) |
| low | B67-G5 BINiagaraNetworkHelper declaring file | cloudLinkExtensionNiagara | ✅ covered — B88 |
| low | B68-G1 Remaining uncensused first-party servlets (Context threading) | web modules | ✅ covered — B83 |
| low | B68-G2 @NiagaraRpc method bodies past injection point | niagaraDriver + rpc | ✅ covered — B91 |
| low | B68-G3 BOrdScheme.resolve null-user read-permission enforcement | baja ord | ✅ covered — B86 |
| low | B68-G4 JAAS LoginModule chain internals | baja auth | ✅ covered — B86 |
| low | B68-G5 SuperSessionPrincipal branch-on-identity check | baja auth | ✅ covered — B86 |
| low | B65-G3 doIsGrantedTo grant-matching body for FilePermission/RuntimeExecPermission | nre bytecode | ✅ covered — B81 |
| low | B69-G1 Native-launcher-binary confirmation that niagarad never runs the Nre.runClass/Bootstrap path | native launchers | ✅ covered — B76 |
| low | B69-G3 BOrionDatabase storage/retention internals | orion | ✅ narrowed — B104 (residue → B104-G4) |
| low | B70-G1 Extend AMBIG SequencedCollection classification to the ~33 sites in undecompiled jars | organized/ | ✅ covered — B105 |
| low | B70-G2 Cross-check instanceof census against docSource.jar originals | docSource | ✅ covered — B90 |
| low | B70-G4 Confirm kitControl zero-modernization (records/sealed/pattern-switch counts) | kitControl | ✅ covered — B90 |
| low | B71-G1 PortalLicenseUtil.getPortalUpdates HTTP body | portalApi | ✅ covered — B77 |
| low | B71-G2 LicenseProcedure wizard full flow | portalApi | ✅ covered — B85 |
| low | B71-G3 EntitlementApi/RetrieveEntitlements request/response schema | nre.subscription | ✅ covered — B77 |
| low | B71-G4 N4 nre.jar physical location (which jar holds com.tridium.nre.subscription) | N4 install | ✅ covered — B84 |
| low | B71-G5 N4 vs N5 nre.subscription byte-diff | N4 vs N5 nre | ✅ covered — B84 |
| low | B71-G6 DEVICE_REGISTRATION_CLIENT_ID OAuth flow (structure only) | nre.subscription | ✅ covered — B77 |
| low | B72-G1 Exact FE-selection UI command that sets fieldEditor facet | workbench | ✅ narrowed — B103 (residue → B103-G1) |
| low | B72-G2 AgentList.getDefault() specificity algorithm | baja agent | ✅ covered — B103 |
| low | B72-G3 fox/box isWar() status + WebSocket-upgrade-filter interaction | fox/box | ✅ covered — B78 |
| low | B72-G4 Px-side converter registry | px | ✅ covered — B103 |
| low | B73-G1 BNiagaraEdgeLiteStation license-downgrade edge cases | niagaraDriver | ✅ covered — B104 |
| low | B73-G2 BNiagaraVirtualChannel.findReachableStations wire-level discovery request/response fields (text corrected from block73) | niagaraDriver | ✅ covered — B104 |
| low | B73-G3 BComponent default isChildLegal behavior: does any tree-level restriction govern niagaraSync point-folder membership (text corrected from block73) | fox | ✅ covered — B104 |
| low | B73-G4 basicDriver chassis full blast-radius (12 modules) slot census | modbus + basicDriver | ✅ covered — B104 |
| low | B73-G5 niagaraSync waitingQueueCsv live behavior (requires-execution) | niagaraSync station | requires-execution → §19 (run niagaraSync on a station and observe waitingQueueCsv) |
| low | B74-G1 Build a driver module end-to-end via NDriverModuleGenerator templates (refines B50-G1) | devkit | requires-execution → §19 (static template reconstruction done in B89; run the wizard + build) |
| low | B74-G2 Recover devkit*.properties native-build compiler/linker command shapes | n-plugin natives | ✅ narrowed — B89 (residue → B89-G3) |
| low | B74-G3 npsdk-native linux_npsdk/Gcc preset platform definition | n-plugin natives | ✅ covered — B89 |
| low | B75-G1 JxBrowser/JavaFX preInitialize() bodies | workbench | ✅ covered — B79 |
| low | B75-G2 BajadocIndex PatternFilter full wildcard grammar | help | ✅ covered — B103 |
| low | B75-G3 Line-diff N5 buildingJS.html vs N4 B1132/B1119 excerpts | doc jars | ✅ covered — B102 |
| low | B75-G4 uxBuilder-ux.jar minified JS bundle extraction | uxBuilder | ✅ covered — B79 |
| low | B77-G1 PortalApi.getOnlineLicenseRequestPortalAddress endpoint host resolution | portalApi | ✅ covered — B85 |
| low | B77-G2 Two structural inconsistencies in PortalApi.getLicenseUpdates | portalApi | ✅ narrowed — B85 (residue → B85-G2) |
| low | B77-G3 Whether EntitlementStatus.getScope()/the scope OAuth field is consumed anywhere (text corrected from block77 — prior row drifted) | nre.subscription | ✅ covered — B85 |
| low | B77-G4 Whether DEVICE_REGISTRATION_RESPONSE_TYPE/GRANT_TYPE sibling constants are dead or a not-yet-wired path (text corrected from block77; live token exchange is not this gap) | nre.subscription | ✅ covered — B96 |
| low | B77-G5 Whether SecurityConstants.canCheckTpk() is a deliberate single dev/prod-build flag or incidental reuse (text corrected from block77) | nre.subscription | ✅ covered — B85 |
| low | B79-G1 Six JS-only rc/ux/make + rc/fe files with no Java-type counterpart: back older types or JS-only (text corrected from block79) | jxBrowser | ✅ covered — B102 |
| low | B79-G2 uxBuilder AMD bundle module-loader entry graph | uxBuilder | ✅ covered — B102 |
| low | B79-G3 grunt-niagara successor npm package name/contents (still unnamed) | m2 + npm | ✅ covered — B102 |
| low | B81-G1 securityBridge.jar exact boot-classpath loading mechanism (refines B65-G4) | nre launcher | ✅ covered — B87 |
| low | B81-G2 doIsGrantedTo wildcard/implies edge cases for other permission types | nre | ✅ covered — B86 |
| low | B81-G3 BServerPort nftables firewall rule-set generation + activation path | platform | ✅ narrowed — B94 (residue → B94-G5) |
| low | B82-G1 backup.jar bytecode-exhaustive (javap) cross-reference to migrator (text corrected from block82) | backup | ✅ covered — B98 |
| low | B82-G2 SimpleKeyRing.exportKeyData [IV][AES] format vs AESStreamEncryption.isEncrypted header detection (text corrected from block82) | baja | ✅ covered — B91 |
| low | B82-G3 BFormat.reflect body: exception handling, method-cache invalidation, gates (text corrected from block82) | migrator/baja | ✅ covered — B98 |
| low | B78-G1 box jetty-web.xml contextPath + WebSocket-upgrade-filter vs auth-filter ordering | box | ✅ covered — B83 |
| low | B78-G2 N4 AlarmStoreHeader magic/version compare (alarm.adb upgrade compatibility) | N4 alarm | ✅ covered — B84 |
| low | B78-G3 niagaraSync getLicenseFeature consumer: unlicensed fault/down/disabled severity | niagaraSync | ✅ covered — B92 |
| low | B78-G4 box wire-format message opcodes / frame body layout | box | ✅ covered — B83 |
| low | B80-G1 Full new-vs-old classification of all 110 getFirst/getLast call sites by receiver type | organized/ | ✅ covered — B90 |
| low | B80-G2 What Jetty MBeanContainer publishes + platform MBean server remote reachability | jetty | ✅ covered — B83 |
| low | B80-G3 Decompile the 5 B31 types from on-host N4-4.15 jars and slot-diff vs 4.14 | N4 4.15 jars | ✅ covered — B84 |
| low | B76-G1 Boot-time routine (njre.dll/nre) that verifies the 256-byte .jar.sig sidecars + its key | nre boot | ✅ covered — B87 |
| low | B76-G2 Watermark-specific N4 ZKM census (clinit decrypt idiom), replacing base64-polluted grep | N4 organized/ | ✅ covered — B90 |
| deferred | B4-G6 Is the absence of docUser/migration doc jars permanent in N5 GA or beta-only | N5 GA install | pending (parked; needs a GA build) |
| medium | B83-G2 Does the manual non-ComponentSlotMap alarm-attribution pattern (BNaServlet UpdateAlarms) generalize to the alarm module's own ack path | alarm + analytics | ✅ covered — B92 |
| medium | B83-G3 Plain-JSON box frame path: internal message-type/method-dispatch structure beyond p/v/id | box | ✅ covered — B92 |
| low | B84-G1 com.tridium.json (121 files) vs org.json (398 files) coexistence: per-module migration state | organized/ census | ✅ covered — B95 |
| low | B84-G2 IpProtocol move nre.firewall → nre.security: genuine consolidation or coincidence | nre | ✅ covered — B95 |
| low | B84-G3 alarm.adb record/row body format (recordVersion) N4-4.15 vs N5 compare | alarm + PowerB 4.15 | ✅ covered — B92 |
| low | B85-G1 Corpus-wide audit for the shadow-literal dead-constant anti-pattern (seen twice in portalApi) | organized/ | ✅ narrowed — B96 (residue → B96-G2) |
| low | B85-G3 RotateKeys / RequestCertificates response field shapes | nre.subscription | ✅ covered — B96 |
| medium | B86-G1 Any first-party chain combining null-Context ORD resolve with canRead() as an exposure gate | web + baja | ✅ narrowed — B91 (residue → B91-G1) |
| low | B86-G2 BLegacyBasicAuthenticationScheme (null LoginConfiguration) live reachability vs vestigial | web/authn | ✅ narrowed — B91 (residue → B91-G5) |
| low | B87-G2 NreLauncherWin32 FIPS-mode byte (this+0x1002c) setter/origin | nre.dll disasm | ✅ covered — B94 |
| low | B87-G3 njre.dll --add-exports niagara.nre/...=niagara.niagarad call site | njre.dll disasm | ✅ covered — B94 |
| low | B88-G1 Payload body reads of the 9 large unread Forge msg/ classes | cloudLinkForge | ✅ covered — B96 |
| low | B88-G3 cloudLinkForge Honeywell-Forge tenant ownership vs Tridium Azure proxy | cloudLinkForge | ✅ narrowed — B96 (residue → B96-G3) |
| low | B89-G1 Why compileModuleTestJava's invalid Automatic-Module-Name error does not fail the Gradle task | n-plugin + javac | ✅ narrowed — B97 (residue → B97-G1) |
| low | B89-G4 Remaining ~45 ndriver/videodriver .vm templates: other unnoted interface requirements | devkit | ✅ covered — B97 |
| low | B90-G1 Extend docSource instanceof cross-check to the 19 remaining bound sites | docSource | ✅ covered — B98 |
| low | B90-G2 BCloudConnectionService.getPlatformType() value set | cloudLink/platform | ✅ covered — B96 |
| low | B90-G3 Explicit Zelix deobfuscator log for the 2 remaining N4 ZKM modules | N4 organized/ | ✅ narrowed — B98 (residue → B98-G3) |
| low | B90-G4 Full census of BPlatformService/BIPlatformCommand getLicenseVendor/Feature overrides | organized/ | ✅ covered — B96 |
| deferred | B88-G2 N5-specific Tridium statement that nCloudDriver is removed/unsupported (successor-by-redesign quote found) | web after GA | pending (parked; revisit after GA) |
| low | B91-G1 Extend the null-Context ORD census beyond the literal `null` keyword (indirect nulls, cross-method chains) | organized/ | ✅ narrowed — B99 (residue → B99-G4) |
| medium | B91-G3 Census the remaining ~53 permissions="unrestricted" @NiagaraRpc methods for the fail-open write shape | organized/ | ✅ narrowed — B99 (residue → B91-G2) |
| low | B91-G4 Does Niagara rate-limit or lock out repeated CSRF failures | web | ✅ covered — B99 |
| low | B92-G1 AlarmStore page-packing logic N4-4.15 vs N5 | alarm | ✅ covered — B105 |
| low | B92-G2 Census of other BWrapperBoxChannel subclasses besides Alarm/History | organized/ | ✅ covered — B104 |
| low | B92-G3 What re-triggers fwServiceStarted()/checkLicense() short of a station restart | baja | ✅ covered — B104 |
| low | B93-G1 Does BCertificateStatusHealth exist in N5 bytecode or is Summit slide p.70 a typo | organized/ | ✅ covered — B102 |
| low | B93-G2 Clarify which niagara-help/source directory Block 4's REMIT baseline refers to | docs | ✅ covered — B102 |
| medium | B94-G1 Identify the actual caller of BPlatCryptoManager.make(BDaemonPlatform) (daemon crypto path entry) | platform | ✅ covered — B99 |
| low | B94-G6 Trace getCertHealth/getPasswordStrength's actual caller | platCrypto | ✅ covered — B99 |
| low | B94-G7 BSigningService.processCsr CA-signing internals (CSR → certificate) | signingService | ✅ narrowed — B99 (residue → B99-G1) |
| low | B94-G3 External caller of defaultToNonFIPS outside nre.dll | native bins | ✅ covered — B100 |
| low | B94-G4 Locate NullFirewallProcessor/PfFirewallProcessor class definitions missing from the N4 corpus | N4 jars | ✅ covered — B100 |
| medium | B95-G2 Trace the jar-cache/<module>/ deployment family (22 subdirs) | N5 install | ✅ covered — B101 |
| low | B95-G3 PrettyJSONStringer/QuickJSONWriter call sites | organized/ | ✅ covered — B101 |
| low | B95-G4 Root-cause Block 23's scratch-decompile omission of crypto/core | methodology | ✅ covered — B100 |
| low | B95-G5 BIpProtocolEnum ↔ IpProtocol conversion boundary | baja + nre | ✅ covered — B101 |
| medium | B96-G1 pclntab-aware (Ghidra Go analyzer) disassembly of NCS-Agent Go functions | NCS-Agent binary | ✅ covered — B100 |
| low | B96-G2 Per-candidate triage of the dead-constant shadow-literal sweep | organized/ | ✅ narrowed — B105 (residue → B105-G2) |
| low | B97-G1 Gradle resolution-engine tolerance of the moduleTest self-dependency error | Gradle | ✅ narrowed — B106 (residue → B106-G1) |
| low | B97-G3 Full body read of the 56 ndriver/videodriver templates | devkit | ✅ narrowed — B106 (residue → B106-G3) |
| low | B97-G4 buildN5.html VideoDriver example tree is inaccurate vs the real generator (doc note) | docDeveloper | ✅ covered — B102 |
| low | B98-G1 Do N4 stations run with a SecurityManager installed (reachability of JSR-105 secure validation) | N4 nre | ✅ covered — B100 |
| low | B98-G2 Re-check B98 N4 findings on the exact 4.14.0.162 build | N4-4.14 | ✅ covered — B100 |
| low | B98-G3 Raw deobfuscator detect log for honeywellBacnetSpyder/honeywellLonSpyder | N4 organized/ | ✅ covered — B105 |
| low | B98-G4 saml.jar absent from the PowerB 4.15 OEM package | PowerB install | pending |
| low | B97-G2 Workbench GUI re-sign vs verify-module.sh stored check | Workbench | requires-execution → §19 (re-sign a module in Workbench, rerun --stored) |
| deferred | B95-G1 commonsLang.jar empty in 5.0.0.28 beta: fixed in a later build? | N5 GA install | pending (parked; needs a later build) |
| medium | B99-G1 Do downstream consumers of signingService-issued certs perform CA-chain/BasicConstraints validation (exploitability of the CA:TRUE copy-through) | crypto consumers | pending |
| low | B99-G3 Workbench reachability of the ungated BPlatCryptoManager.generateSelfSignedCert/resetUserKeyStore | workbench + platCrypto | pending |
| low | B99-G4 Remaining B91-G1 null-Context sub-shapes (caller/callee split, non-standard wrapper names) | organized/ | pending |
| low | B99-G5 Does BLonworksRpc's read-gates-write pattern recur elsewhere | organized/ | pending |
| medium | B100-G1 Census the full 8005-function / 4209-type NCS-Agent symbol table | NCS-Agent binary | pending |
| low | B101-G4 Commercial name of the Atlas (ARM64 snap) hardware target | web | pending |
| low | B101-G5 Build-side Gradle step that packs LIB-INF third-party jars | m2 plugins | pending |
| medium | B103-G1 Any GUI path reaching BComplex.setFacets() frozen-slot branch | workbench + web | pending |
| low | B103-G2 Do other doc jars share docDeveloperAnalytics' dual-indexing | doc jars | pending |
| medium | B103-G3 Is docDeveloperAnalytics.jar's own index read at runtime by BajadocIndex | help | pending |
| low | B104-G1 ValueDocDecoder binary grammar | baja | pending |
| low | B104-G2 BUploadParameters/BDownloadParameters field contents | driver | pending |
| low | B104-G3 TableBuilder Property → SQL type mapping | orion | pending |
| low | B104-G4 Station-wide search for an Orion-table retention/purge job | organized/ | pending |
| medium | B105-G1 Receiver-type-aware census of Feature .get()/.getb() calls to finish B11-G4 | organized/ | pending |
| low | B105-G2 Continue dead-constant shadow-literal triage beyond the 40-candidate sample | organized/ | pending |
| low | B105-G3 Extend the module.xml consolidation explanation to the rest of the plat*/html/file/fox/export cluster | module.xml census | pending |
| low | B106-G2 Windows javac.exe NiagaraPermissionGrant$Type.WORKBENCH enum warning: toolchain-specific or unreported | javac | pending |
| low | B106-G3 Exhaustive prose read of all 5,161 ndriver/videodriver template lines | devkit | pending |
| low | B99-G2 Live repro of the Sys.isStation()/getStation() permission-helper edges | station | requires-execution → §19 (offline Workbench vs station run) |
| low | B102-G2 Flip the uxBuilder WebDev toggle on a live station and observe raw vs built serving | station | requires-execution → §19 |
| low | B104-G5 Live-station confirmation of B104's static driver/sync findings | station | requires-execution → §19 |
| low | B106-G1 Gradle --info/dependencyInsight trace of which wiring puts the moduleTest jar on compileModuleTestJava | Gradle run | requires-execution → §19 |

## Iteration history

| # | Date | Gap closed | Block | Delegated? · model tier | New gaps uncovered |
|---|---|---|---|---|---|
| 1 | 2026-09-27 | N5-G1 packaging / JPMS | B1 | yes · sonnet | 6 new — B1-G1..G6 in block |
| 2 | 2026-09-27 | N5-G6 build toolchain | B2 | yes · sonnet | 7 new — B2-G1..G7 in block |
| 3 | 2026-09-27 | N5-G7 boot/runtime JRE 25 | B3 | yes · sonnet | 5 new — B3-G1..G5 in block |
| 4 | 2026-09-27 | N5-G12 shipped docs | B4 | yes · sonnet | 8 new — B4-G1..G8 in block |
| 5 | 2026-09-27 | N5-G8 licensing (premise refuted: subscription not new) | B6 | yes · sonnet | 3 new — B6-G1..G3 in block |
| 6 | 2026-09-27 | B2-G1 Slotomatic vs nap processor | B7 | yes · sonnet | 2 new — B7-G1, B7-G2 |
| 7 | 2026-09-27 | B3-G3+B3-G4 permission model | B8 | yes · sonnet | 5 new — B8-G1..G5 |
| 8 | 2026-09-27 | B4-G8 upgrade guides + porting checklist | B10 | yes · sonnet | 6 new — B10-G1..G6 in block |
| 9 | 2026-09-27 | N5-G5 core API delta (javax.baja→niagara 1:1, no shim) | B5 | yes · sonnet | 4 new — B5-G1..G4 |
| 10 | 2026-09-27 | B2-G7 + B7-G1 build PoC (built, signed, JPMS) | B9 | yes · sonnet | 4 new — B9-G1..G4 |
| 11 | 2026-09-27 | B10-G5 n5mig station migration + migrator SPI | B14 | yes · sonnet | 5 new — B14-G1..G5 |
| 12 | 2026-09-27 | B8-G4 outbound network gating — CONFIRMED audit-only | B15 | yes · sonnet | 4 new — B15-G1..G4 |
| 13 | 2026-09-27 | N5-G9 authn/security surface | B12 | yes · sonnet | 8 new — B12-G1..G8 |
| 14 | 2026-09-27 | B6-G3 license-gated features map (253 call sites, 84 features) | B11 | yes · sonnet | 4 new — B11-G1..G4 |
| 15 | 2026-09-27 | N5-G2 module inventory delta | B13 | yes · sonnet | 6 new — B13-G1..G6 |
| 16 | 2026-09-27 | N5-G10 + B5-G3 cloud surface and niagaraSync | B18 | yes · sonnet | 7 new — B18-G1..G7 |
| 17 | 2026-09-27 | N5-G13 persistence: bog v5 grammar unchanged, .hdb MAGIC unchanged, OrientDB 3.2.55 | B19 | yes · sonnet | 5 new — B19-G1..G5; §14 fix of N4 B33 hex (niagara-research PR #3) |
| 18 | 2026-09-27 | N5-G14 behavioural delta control/alarm/history/kitControl | B20 | yes · sonnet | 5 new — B20-G1..G5 |
| 19 | 2026-09-27 | N5-G11 UI stack | B21 | yes · sonnet | 4 new — B21-G1..G4 |
| 20 | 2026-09-27 | B14-G1 n5mig on PANCCADIA copy (license-blocked; static census) | B17 | yes · sonnet | 4 new — B17-G1..G4 |
| 21 | 2026-09-27 | B10-G1 + B9-G2 ColdRoomPan ported and built on N5 (8/15 CHK confirmed, 4 unpredicted breaks) | B16 | yes · sonnet | 6 new — B16-G1..G7 |
| 22 | 2026-09-27 | N5-G15 driver framework delta (javax.baja.log deleted; isNonOperational) | B22 | yes · sonnet | 4 new — B22-G1..G4 |
| 23 | 2026-09-27 | B1-G2 + B3-G1 + B1-G5 module loader internals (4 layers, PROGRAM dead code) | B23 | yes · sonnet | 6 new — B23-G1..G6 |
| 24 | 2026-09-27 | B14-G2..G5 migrator catalog (58 types; §14 correction of B14 propMigration) | B24 | yes · sonnet | 5 new — B24-G2..G6 |
| 25 | 2026-09-27 | B21-G3 web security headers (default CSP allows unsafe-inline; CSRF token only on 4 URL patterns) | B27 | yes · sonnet | 5 new — B27-G1..G6 |
| 26 | 2026-09-27 | B20-G4 BCapacity hazard — CONFIRMED narrower; PANCCADIA zero exposure (§14 refinement of B20) | B26 | yes · sonnet | 3 new — B26-G2..G4 |
| 27 | 2026-09-27 | B16-G6 + B16-G1 JUnit4→TestNG (117 asserts, 51/51 pass; test.exe license-gated) | B29 | yes · sonnet | 3 new — B29-G3..G5 |
| 28 | 2026-09-27 | N5-G4 Java 17-25 feature census (recompiled, not modernized: 45 records, 3 sealed, 33 pattern switches, 0 virtual threads) | B25 | yes · sonnet | 4 new — B25-G1..G4 |
| 29 | 2026-09-27 | B23-G1 program objects: javac shell-out, per-program ModuleLayer, mandatory signing for v69 | B32 | yes · sonnet | 4 new — B32-G1..G4 |
| 30 | 2026-09-27 | N5-G3 bytecode/signing/obfuscation (same Honeywell cert as N4, zero obfuscation; found pipeline marker bug) | B30 | yes · sonnet | 4 new — B30-G1..G4 |
| 31 | 2026-09-27 | B24-G6 PANCCADIA types load in N5 (0/283 missing; 1 real orphan slot resurrected as dynamic) | B31 | yes · sonnet | 5 new — B31-G1..G5 |
| 32 | 2026-09-27 | B22-G1/G3/G4 drivers on basicDriver (10), BACnet export API change, niagaraDriver deltas | B35 | yes · sonnet | 5 new — B35-G1..G5 |
| 33 | 2026-09-27 | B8-G3 + B12-G4 residual gating (only exec enforced; self-declared native access ungated) + nftables firewall | B33 | yes · sonnet | 6 new — B33-G1..G6 |
| 34 | 2026-09-27 | B16-G7 CompPan + DashboardPan ported and built (rt+ux+wb merge, jakarta servlet; alarm needs javafx/batik stubs) | B28 | yes · sonnet | 7 new — B28-G1..G7 |
| 35 | 2026-09-27 | B6-G1/G2 + B11-G1 subscription client, license conf dir, capacity licensing (§14 correction of B11) | B34 | yes · sonnet | 6 new — B34-G1..G6 |
| 36 | 2026-09-27 | B2-G5 N5 JS pipeline (node never bundled; grunt/yarn-workspace plugins; optional for DashboardPan) | B36 | yes · sonnet | 3 new — B36-G1..G3 |
| 37 | 2026-09-27 | B12-G5..G8 TOTP enrollment (2 paths, AES-256 reversible at rest, no gauth migration), SAML SP/IdP, LDAP bind, SRP6 (§14 correction of B12) | B38 | yes · sonnet | 4 new — B38-G1..G4 |
| 38 | 2026-09-27 | B35-G1 + B18-G4 + B20-G2 niagaraSync internals (AND-gate failover, ~180 sync-capable types; ColdRoomPan timers not HA-safe) (§14 refinement of B18) | B37 | yes · sonnet | 6 new — B37-G1..G6 |
| 39 | 2026-09-27 | B20-G3 + B27-G3 N5 action audit (old value now recorded for 4 writables; null-Context servlet writes still unaudited) + web authn chain | B41 | yes · sonnet | 6 new — B41-G1..G6 |
| 40 | 2026-09-27 | B18-G2/G3/G7 cloudLink AMQP (in-memory-only offline queue, Azure fingerprint in generic chassis), provider channels, nCloudDriver retired without migrator | B42 | yes · sonnet | 6 new — B42-G1..G6 |
| 41 | 2026-09-27 | B19-G1/G2/G4 data-at-rest crypto: KeyRing format identical to N4, DPAPI on Windows, EncryptionKeySource semantics, systemDb encrypted by default, alias-string rename | B43 | yes · sonnet | 4 new — B43-G1..G4 |
| 42 | 2026-09-27 | B28-G7/G2/G3 alarm graph needs javafx (bundled in JRE) + batik (absent from the whole install); fix = 6 compileOnly Maven deps, no stubs; Windows javac.exe hits the same batik gap | B39 | yes · sonnet | 4 new — B39-G1..G4 |
| 43 | 2026-09-27 | B33-G3/G4/G5 system-property writers (4, hard-coded keys; boot re-applies etc/system.properties), nft adapter dead code, firewall sysprops absent from Supervisor install (§14 correction of B33: 27 keys) | B40 | yes · sonnet | 4 new — B40-G1..G4 |
| 44 | 2026-09-27 | B41-G6 DashboardPan write path passes the request niagara.context (1 HTTP write site; bytecode-verified) | B46 | yes · sonnet | 5 new — B46-G1..G5 |
| 45 | 2026-09-27 | B43-G1 reversible secrets across N4→N5: keyring-mode cleared with SEVERE log, external-mode kept with passphrase; PANCCADIA = external, 3 secrets (§14 correction of B24) | B47 | yes · sonnet | 3 new — B47-G1..G3 |
| 46 | 2026-09-27 | Public evidence: Tridium FAQ (GA target Dec 2026, JACE-9000 only, JACE-8000 not upgradable, Java 25), subscription licensing pre-dates N5; B10-G2/B13-G1/B42-G4 narrowed not closed | B48 | yes · sonnet | 5 new — B48-G1..G5 |
| 47 | 2026-09-27 | B46-G1 which N5 writes are audited: generated setters always null Context (3,589 sites); Fox/BOX/OrdServlet thread real Context via SetOp.commit; 3-tier pattern for our modules | B49 | yes · sonnet | 4 new — B49-G1..G4 |
| 48 | 2026-09-27 | B25-G3 full jdeprscan: 85 deprecated call sites (39 for-removal) in 16/253 jars; 3 root causes (AccessController family, cloudLink finalize, ThreadDeath); our 3 ported modules clean | B44 | yes · sonnet | 4 new — B44-G1..G4 |
| 49 | 2026-09-27 | B37-G6 ColdRoomPan HA-ready PoC: 8 Clock.Ticket → BNiagaraSyncTicket, 9 fields → Properties, 3 classes sync-capable; builds; 55/55 tests; validator walk passes statically | B45 | yes · sonnet | 2 new — B45-G2, B45-G4 (B45-G1 merges into blocked B37-G1) |
| 50 | 2026-09-27 | N5-G16 porting synthesis + docs/n4-to-n5-porting-guide.md (180 citations across 27 blocks; troubleshooting table; PANCCADIA migration runbook) | B50 | yes · sonnet | 3 new — B50-G1..G6 (G3-G5/G7 fold into existing blocked/deferred gaps) |
| 51 | 2026-09-27 | B41-G1 + B49-G2 + B44-G2 security audit routing (SecurityHistory vs AuditHistory, 19 emitters, niagarad relay), NiagaraRpc Context = SecurableContext + permission check, AccessController sites inert; no Subject.getSubject | B54 | yes · sonnet | 5 new — B54-G1..G5 |
| 52 | 2026-09-27 | B2-G6 + B9-G3 + B13-G4 N5 kit delta (file-by-file), n-java per module, module.xml deps derived from compileClasspath (explains 2.0.7→2.0) | B51 | yes · sonnet | 8 new — B51-G1..G8 |
| 53 | 2026-09-27 | B17-G2/B23-G3/B30-G3/B34-G3 launch gates: tridium:nre allowlist (WbMain, LicenseDownload), skipModuleValidation not denylisted, trust anchor = runtime cacerts + TPK pin, LicenseAccessKey via niagarad | B53 | yes · sonnet | 6 new — B53-G1..G6 |
| 54 | 2026-09-27 | B46-G2/B27-G6/B5-G4/B5-G2 DashboardPan CSRF via CsrfUtil + /api/csrfToken; zero javax/servlet residue in 4 built jars; BObject.equals removal is not a risk | B52 | yes · sonnet | 4 new — B52-G1..G5 |
| 55 | 2026-09-27 | B48-G1/G5 public Java version (all first-party say 25; Java 21 only in 3 third-party pages) and HA naming (Niagara Sync = tridium:niagaraSync) | B56 | yes · sonnet | 4 new — B56-G1..G4 |
| 56 | 2026-09-27 | B53-G3 denylist self-override CONFIRMED but bounded to host-admin; nre.properties is a 2nd JVM-arg surface; B43-G2/G3 N4 parity: systemDb encrypted-by-default and EncryptionKeySource unchanged since N4 | B57 | yes · sonnet | 4 new — B57-G1..G4 |
| 57 | 2026-09-27 | B39-G3 javac forces only transitive requires of non-root modules (4 controlled compiles); B15-G2 no egress gate inside okhttp 5.5 / Jetty 12.1.13 — audit-only verdict holds at library layer | B55 | yes · sonnet | 4 new — B55-G1..G4 |
| 58 | 2026-09-27 | B24-G2/B31-G4 PANCCADIA station census: only config.bog + empty alarm.adb on the Windows path; histories/schedules/px/systemDb/.dist structurally absent | B58 | yes · sonnet | 4 new — B58-G1..G4 |
| 59 | 2026-09-27 | B4-G1/B4-G5 help full-text index format decoded (words/worddocs/postings/documents.dat, 7,270 docs, verified reader); no JDK-class bajadoc stand-ins in N5 (javadoc links to Oracle only) | B59 | yes · sonnet | 3 new — B59-G1..G4 (G3 folds into B4-G2) |
| 60 | 2026-09-27 | B51-G2..G7 kit lint facts: Flags byte-identical (only 2 lints need niagara.* added), no real per-profile split, class-version 52→69 inverts, dependency slimming is mostly the N4 part-split artifact | B60 | yes · sonnet | 4 new — B60-G1..G4 |
| 61 | 2026-09-27 | B40-G2 live station root space is base BComponentSpace (ruleHintOverride never validated) [CERT]; B38-G2 consumer SAML allowlist includes SHA-1 (deprecated-reject is dead code) | B61 | yes · sonnet | 4 new — B61-G1..G3 (B57-G2 refined) |
| 62 | 2026-09-27 | B61-G3 SAML SHA-1 accept CLOSED (no config flips OneLogin rejectDeprecatedAlg; Santuario secureValidation gates ref-count only) + B38-G1 lockout N4=N5 | B62 | yes · sonnet | 2 new — B62-G1..G2 |
| 63 | 2026-09-27 | B61-G1/B57-G2 CLOSED: sole nre.dll CreateProcessA xref = restartPlatformDaemon0 building plat.exe restartdaemon (refutes B61 JxBrowser reading, §14) + B57-G1 + B54-G1 (neg) | B63 | yes · sonnet | 4 new — B63-G1..G4 |
| 64 | 2026-09-27 | B28-G1 CLOSED (test-wb→test, Summit-2026 deck) + B10-G2/B13-G1 narrowed (bacnetOws removed, bacnetAlarmRouter→bacnetUtil) | B64 | yes · sonnet | 5 new — B64-G1..G5 |
| 65 | 2026-09-27 | B54-G3 CLOSED (full ByteBuddy interception map) + B3-G5 content half; niagarad runs permission layer inert (isTrustedDomain=true) | B65 | yes · sonnet | 4 new — B65-G1..G4 |
| 66 | 2026-09-27 | B24-G3/G4/G5 + B47-G1 CLOSED (MigrationUtils 47 sigs, migrators/premigrators, zwave 180-list, .kr decrypt is dead code via bytecode xref) | B66 | yes · sonnet | 3 new — B66-G1..G3 |
| 67 | 2026-09-27 | B42-G2/G3/G5/G6 + B44-G1 CLOSED (retriableError=true default, throttle defaults, Forge handlers, 13 empty finalize() no Cleaner) | B67 | yes · sonnet | 5 new — B67-G1..G5 |
| 68 | 2026-09-27 | B41-G2/G3/G5 + B27-G4/G5 CLOSED (JAAS 2-principal Subject, Jetty isUserInRole dead, first-party servlets drop Context via 2-arg set overload) | B68 | yes · sonnet | 6 new — B68-G1..G6 |
| 69 | 2026-09-27 | B65-G1 niagarad permission-layer inert (Java half: NiagaraDaemon has no nreMain, Nre.runClass path unreachable) + B65-G2 (via B8) + B54-G4/G5 | B69 | yes · sonnet | 3 new — B69-G1..G3 |
| 70 | 2026-09-27 | B25-G4 control B*Writable pattern-switch (dispatch on non-sealed Action) + B20-G5 source-cite upgrade (4 control modules) | B70 | yes · sonnet | 4 new — B70-G1..G4 |
| 71 | 2026-09-27 | B53-G2 portalApi LicenseDownload is dead target (no nreMain) + B34-G1/G4/G5 subscription + B56-G2 Sync vs Remote feature decouple | B71 | yes · sonnet | 6 new — B71-G1..G6 |
| 72 | 2026-09-27 | B26-G2/G3/G4 capacity (BHistoryDbTable is shared ancestor, §14 corrects B26) + B27-G2 jetty-web census (web/fox/box) | B72 | yes · sonnet | 4 new — B72-G1..G4 |
| 73 | 2026-09-27 | B35-G2 EdgeLite license-gated station + B35-G5 reachable-stations + B37-G2/G5 sync-folder/modbus chassis + B45-G2 no CSV precedent | B73 | yes · sonnet | 5 new — B73-G1..G5 |
| 74 | 2026-09-27 | B49-G3 Slotomatic Context-overload feasible + B49-G4 369 invoke sites + B55-G4 no okhttp placeholder trap (advances B50-G2/G7) | B74 | yes · sonnet | 3 new — B74-G1..G3 |
| 75 | 2026-09-27 | B59-G1/G2 help linear-scan + bajadoc JDK-null + B21-G1/G2 uxBuilder new/JxBrowser default + B36-G1 buildingJS stale | B75 | yes · sonnet | 4 new — B75-G1..G4 |
| 77 | 2026-09-27 | B71-G1/G3/G6 entitlement+portal (getPortalUpdates XML-over-HTTPS to legacy host; device-flow OAuth) + B53-G5 (TPK=Honeywell leaf pubkey) + B53-G6 (dev CA dead) | B77 | delegated (rate-limited post-write) | 5 new — B77-G1..G5 |
| 79 | 2026-09-27 | B21-G4 jxBrowser real version + B75-G4 uxBuilder AMD bundle + B75-G1 preInitialize fallback gates; B36-G3 narrowed | B79 | delegated | 3 new — B79-G1..G3 |
| 78 | 2026-09-27 | box = Building Object eXchange (N4 carryover, not new) on Jetty-ee11 WS + Fox; B72-G3 + B58-G1/G4 alarm.adb header (MAGIC 1611526157) | B78 | orchestrator-direct (rate-limit fallback) | 4 new — B78-G1..G4 |
| 80 | 2026-09-27 | B25-G2 SequencedCollection types only in bajaui NSS2; B33-G1 JMX = MXBean introspection + jetty MBeanContainer only, no first-party MBeans | B80 | orchestrator-direct | 3 new — B80-G1..G3 |
| 76 | 2026-09-27 | B69-G1 CLOSED niagarad.exe = 24KB njre.dll-hosted service, no CreateProcess/SCM; B30-G1 .jar.sig = 73×256-byte detached RSA-2048; B30-G4 N5 zero-ZKM reaffirmed (base64 FP); B43-G4 blocked (no native npsdk) | B76 | orchestrator-direct (r2/objdump) | 3 new — B76-G1..G3 |
| 81 | 2026-09-27 | B65-G3 permission grant-matching bodies + B38-G3 LDAP Kerberos/GSSAPI REMOVED in N5 + B15-G3 BServerPort opt-in inbound-only nftables firewall; B65-G4 narrowed | B81 | delegated | 3 new — B81-G1..G3 |
| 82 | 2026-09-27 | B66-G2 ReflectCall.eval permission-gated + B47-G3 AxPasswordUtil recursive walk + B31-G3 BWebBogConverter/QoS property lists; B66-G1 narrowed | B82 | delegated | 4 new — B82-G1..G4 |
| 83 | 2026-09-28 | B78-G1 box /wsbox behind injected auth filter chain + B78-G4 single 'F' fragment opcode + B80-G2 MBeanContainer opt-in, no remote connector + B68-G1 servlet census; B82-G4 blocked-on-authorization | B83 | yes · sonnet | 4 new — B83-G1..G4 |
| 84 | 2026-09-28 | N4-4.15.3.28 (PowerB OEM) found on-host: B80-G3/B31-G1 5 types slot-identical, B71-G4/G5 nre.subscription (injected LicenseValidator), B78-G2 alarm header byte-identical | B84 | yes · sonnet | 4 new — B84-G1..G4 |
| 85 | 2026-09-28 | B77-G1/G3/G5 + B71-G2 LicenseProcedure full flow; B77-G2 narrowed; state-row drift for B77-G3/G4/G5 corrected | B85 | yes · sonnet | 3 new — B85-G1..G3 |
| 86 | 2026-09-28 | B68-G3/G4/G5 ORD schemes + single REQUIRED LoginModule + super-session reader; B81-G2, B8-G1, B8-G2 doc/code mismatch | B86 | yes · sonnet | 3 new — B86-G1..G3 |
| 87 | 2026-09-28 | B76-G1 SignatureUtil::checkFileSignature (CNG, exit 249/250) + B63-G2/G4 + B81-G1/B65-G4 live -Xbootclasspath/a + B17-G3 | B87 | yes · sonnet | 3 new — B87-G1..G3 |
| 88 | 2026-09-28 | B67-G2/G3/G5 cloudLink retry/Azure/network helper + B13-G2 independent CI versioning; B42-G4/B67-G4 narrowed | B88 | yes · sonnet | 3 new — B88-G1..G3 |
| 89 | 2026-09-28 | B2-G2 compact3 inert, B2-G3/B16-G3 doc/test.html, B29-G5 invalid Automatic-Module-Name (§14 corrects B29), B60-G1/G2, B74-G3; B74-G1/G2 advanced | B89 | yes · sonnet | 4 new — B89-G1..G4 |
| 90 | 2026-09-28 | B80-G1 211-site classification, B70-G2 instanceof = Vineflower resugaring (§14 corrects B70/B25), B70-G4, B25-G1, B76-G2 N4 ZKM 16 modules, B11-G3 | B90 | yes · sonnet | 4 new — B90-G1..G4 |
| 91 | 2026-09-28 | B82-G2 (real text) .kr export not AESStream-detectable + B68-G2 setCategoryMask fail-open on null ambient user (MEDIUM, conditional) + B46-G3/B52-G1/B52-G2; B86-G1/G2 narrowed | B91 | yes · sonnet | 5 new — B91-G1..G5 |
| 92 | 2026-09-28 | B83-G2/G3 alarm ack attribution + box JSON dispatch; B31-G5 BWrapperBoxChannel dependency inversion; B84-G3 alarm.adb row body identical; B78-G3/B37-G4 license fatalFault | B92 | yes · sonnet | 3 new — B92-G1..G3 |
| 93 | 2026-09-28 | B4-G3/G7 docSource +17% lines, 0 PDFs; B64-G4/G5 Summit deck full read; B56-G4; B10-G2/B13-G1/G3 → blocked (login portal) | B93 | yes · sonnet | 2 new — B93-G1..G2 |
| 94 | 2026-09-28 | B33-G6/B40-G1/B40-G4 firewall (underscore drops accept rule; N4 netsh refuted) + B12-G3 signingService CSR flow + B53-G4 cacerts + B87-G2/G3 (§14 corrects B87 FIPS) + B12-G2 platCrypto = HTTP over BDaemonSession, 19 actions, host-admin gate | B94 | yes · sonnet | 7 new — B94-G1..G7 |
| 95 | 2026-09-28 | B1-G6 commonsLang empty build omission, B7-G2, B23-G2 crypto.core in nre.jar revocation disabled (§14 corrects B23), B23-G5/G6, B84-G1/G2, B12-G1 | B95 | yes · sonnet | 5 new — B95-G1..G5 |
| 96 | 2026-09-28 | B88-G1 Forge wire schemas, B90-G2/G4, B85-G3, B77-G4, B18-G5 NCS-Agent↔cloudLinkNcs converge; B85-G1/B88-G3/B18-G6 narrowed | B96 | yes · sonnet | 3 new — B96-G1..G3 |
| 97 | 2026-09-28 | B89-G4 templates census, B50-G6 N5 RPC Context injection, B51-G4/G6, B10-G4/G6; B29-G3 fix applied to port script (TDD) | B97 | yes · sonnet | 4 new — B97-G1..G4 |
| 98 | 2026-09-28 | N4-4.15 closes B62-G1/G2, B38-G4 SRP6 identical, B66-G1/B47-G2 live .kr backup, B82-G1/G3, B57-G4, B90-G1 CFR corroboration | B98 | yes · sonnet | 4 new — B98-G1..G4 |
| 99 | 2026-09-28 | B91-G4, B94-G1/G6, B32-G4, B15-G4; B94-G7 → signingService copies CA:TRUE into non-CA certs (MEDIUM-HIGH conditional, orchestrator-verified); B91-G3 root = getPermissions(null) → all | B99 | yes · sonnet | 5 new — B99-G1..G5 |
| 100 | 2026-09-28 | B96-G1 NCS-Agent pclntab recovered (Go 1.25.12, private HON-HCE module); B94-G3/G4, B95-G4, B98-G1 N4 stations run with a SecurityManager, B98-G2 | B100 | yes · sonnet | 3 new — B100-G1..G3 (G3 closed in-session) |
| 101 | 2026-09-28 | B95-G2 jar-cache = LIB-INF extraction, B95-G3/G5, B34-G6, B13-G5 Atlas = ARM64 snap, B13-G6; B5-G1/B58-G3 narrowed; B32-G3 blocked | B101 | yes · sonnet | 5 new — B101-G1..G5 |
| 102 | 2026-09-28 | grunt-niagara unrenamed v2.3.0, WebDev toggle chain, buildingJS diff (§14 corrects B75), corrected VideoDriver tree (§14 B89/B97), B93-G1/G2; B102-G1 closed by orchestrator (pxEditor ships in N5) | B102 | yes · sonnet | 2 new — B102-G1..G2 |
| 103 | 2026-09-28 | B59-G4 dual doc index, B75-G2 PatternFilter grammar, B72-G2/G4 agent specificity + px converters, B4-G4; B72-G1 narrowed | B103 | yes · sonnet | 3 new — B103-G1..G3 |
| 104 | 2026-09-28 | B73-G1..G4 station/discovery/isChildLegal/BACnet chassis, B92-G2/G3 license fault needs remount, B10-G3; B69-G3 Orion = separate RDBMS | B104 | yes · sonnet | 5 new — B104-G1..G5 |
| 105 | 2026-09-28 | B98-G3 ZKM detect logs, B70-G1 bajaui fallback (§14 corrects B80/B90 totals), B60-G3/G4 module.xml consolidation, B92-G1; B11-G4/B96-G2 narrowed | B105 | yes · sonnet | 3 new — B105-G1..G3 |
| 106 | 2026-09-28 | B55-G1 real javac.exe, B55-G2 okio, B39-G2 batik ≥1.18 (§14 corrects B50), B44-G4, B64-G3, B67-G1 MET12-J-EX1; B97-G1/G3 narrowed | B106 | yes · sonnet | 3 new — B106-G1..G3 |

## Blocked gaps (each tagged with what it needs)

- B32-G3 bin/javac on embedded-tier N5 images — needs: a JACE/embedded N5 image · tried: desktop install (javac.exe present, JDK 25.0.4, B101)
- B45-G4 Live operator-driven link-wiring validation — needs: licensed running station (same wall as B45-G1) · tried: validator traced as dynamic ORD + ancestor walk (B106)
- B58-G2 Where PANCCADIA's runtime histories/schedules/px live — needs: operator authorization to read the client station host · tried: not attempted (client data out of scope)
- B17-G4 DefrostMode zero instances in the PANCCADIA bog — needs: operator authorization to read the client bog · tried: not attempted (client data out of scope)
- B66-G3 BBogPremigrator program-object dependency check vs a real station — needs: a real station copy with authorization · tried: static only
- B100-G2 defaultToNonFIPS caller sweep on JACE/embedded binaries — needs: embedded image · tried: all 20 N5 desktop bin/ binaries (B100)
- B101-G1 systemDb branch that applies to PANCCADIA — needs: operator authorization to read the client station · tried: generic license-gate mechanism traced (B101)
- B101-G2 Inspect jace-sd.img (found on the client host) — needs: explicit operator authorization; file deliberately not opened (B101)
- B101-G3 HsmManager genuine N5 drop — needs: a non-OEM N4 build or a later N5 build · tried: N5 corpus (0) + two OEM N4 builds (present) (B101)
- B10-G2 Full N5.0 Breaking Changes list — needs: login-gated niagara-community.com article · tried: WebSearch x2, Summit-2026 deck full read (13/32 rows corroborated, B93). Same wall as B48-G2
- B13-G1 47/49 absent modules: genuine removal vs beta omission — needs: login-gated portal or GA release · tried: full 128-page Summit deck sweep (zero hits, B93)
- B13-G3 59 N4 doc-guides absent from docDeveloper.jar — needs: login-gated doc portal · tried: Summit deck (B93)
- B91-G2 Does box-transport RPC dispatch run under a bound JAAS Subject (fail-open precondition for setCategoryMask) — needs: running station · tried: static trace (B91)
- B91-G5 Is any JAAS default Configuration installed on an N5 station JVM (BLegacyBasic login outcome) — needs: running station · tried: static (B91)
- B94-G2 Live nft base-chain default policy (deny vs accept) — needs: Linux/JACE N5 install · tried: static (B94)
- B94-G5 Linux/JACE packaging defaults for firewall system properties (carries B33-G5/B40-G3/B81-G3 part 2) — needs: JACE-class install image · tried: full Windows defaults/system.properties read (B94)
- B96-G3 Forge registrationHost tenant ownership — needs: live Forge registration · tried: static endpoint shape (B96)
- B82-G4 SLOTS_TO_REMOVE vs PANCCADIA config.bog cross-check (text corrected; prior row drifted to a QoS-migrator wording) — needs: operator authorization to read client config.bog in this sandbox · tried: B83 located the bog; classifier denied extraction (not retried). Alias: B83-G4
- B69-G2 BUserService.auditLoginAttempt third-party caller — needs: third-party/OEM modules · tried: N5 + N4.14 corpora (zero first-party callers in both, B86)
- B29-G4 niagaraTest hard-requires BTestNg — needs: licensed niagaraTest run · tried: doc/test.html (every example extends BTestNg, B89)
- B83-G1 MBeanContainer listener propagation to per-module WebAppContexts — needs: live JMX enumeration on a running station · tried: static read (B83)
- B84-G4 NiagaraDaemon system property truth during niagarad execution — needs: running niagarad · tried: static trace (B84)
- B85-G2 Portal handling of the growing multi-host getLicenseUpdates payload — needs: live traffic capture · tried: static reachability (B85)
- B86-G3 BSpyScheme null-user bypass reachability from a live web session — needs: running station · tried: static (B86)
- B87-G1 Live JPMS readability edge for securityBridge on the boot classpath — needs: running JVM (jcmd) · tried: launcher disasm + ModuleManager read (B87)
- B89-G2 ignoreRuntimeProfileCheck consumer in closed native binaries — needs: native RE of the remaining binaries · tried: n-plugin, slotomatic, baja, devkit jars (zero consumers, B89)
- B89-G3 Real devkit*.properties to confirm interpolation syntax — needs: an external devkit properties artifact · tried: whole install (absent, B89)
- B61-G2 Live confirmation that N5 accepts an rsa-sha1-signed SAML response — needs: a running station + IdP · tried: bytecode gate reading only
- B55-G3 Live egress reproduction — needs: a running station · tried: static decompile
- B57-G3 Live reproduction of the denylist -D override — needs: a running station with controllable launch args · tried: static trace only
- B56-G1 Wayback Machine crawl of Tridium pages for the Java 21 → 25 change — needs: a fetch tool allowed on web.archive.org · tried: WebFetch (refused for that domain), live pages
- B52-G4 Live CSRF round trip on a station — needs: a running licensed N5 station · tried: build + javap only
- B53-G1 Live wb.exe license dialog path — needs: GUI session on the Windows host · tried: -help only (short-circuits before the check)
- B54-G2 Live capture of the audit routing table — needs: a running N5 station · tried: static only
- B49-G1 Live AuditHistory readback for Fox/BOX writes — needs: a running licensed N5 station · tried: static trace only
- B46-G4 Live $/AuditHistory readback of a DashboardPan write — needs: a running licensed N5 station · tried: build + javap only
- B40-G3 Firewall defaults on a JACE/embedded-Linux N5 platform — needs: a JACE-class N5 install image · tried: whole Windows Supervisor install tree + 247-module corpus (absent)
- B39-G1 Live deploy of the rebuilt DashboardPan-rt jar — needs: a running licensed N5 station · tried: build only
- B42-G1 Live AMQP capture against a cloud tenant — needs: tenant + running station · tried: static only
- B41-G4 Live confirmation of audited servlet writes — needs: a running N5 station · tried: static only
- B37-G1 / B37-G3 Live niagaraSync pair probe incl. ColdRoomPan mid-defrost failover — needs: two licensed N5 stations · tried: static only
- B17-G1 / B29-G2 Real n5mig run and niagaraTest/test.exe run on the PANCCADIA copy — needs: a licensed N5 install (tridium:nre feature) · tried: n5mig -premigrate and -o via WSL interop (FeatureNotLicensedException tridium:nre, exit 253), java Bootstrap fallback (missing JavaFX runtime)
- B28-G4 Deploy the three ported modules to a live N5 station — needs: a running (licensed) N5 station · tried: build + sign only
- B34-G2 Dev-build TLS trust-bypass reachability live — needs: a dev-license build · tried: static (unreachable in this build: TPK populated)
- B33-G2 Live check of self-declared @NiagaraEnableNativeAccess — needs: a running N5 station · tried: static decompile only
- B32-G1 Unsigned-program behaviour on real hardware — needs: a running N5 station/device · tried: static decompile only
- B27-G1 Live HTTP header capture from an N5 station — needs: a running N5 station · tried: static jar census only
- B23-G4 Live module-layer confirmation via the moduleConfiguration spy — needs: a running N5 station · tried: static decompile only
- B20-G1 / B26-G1 Dynamic confirmation of BCapacity reinterpretation — needs: a running N5 station · tried: static decompile + bytecode (static half closed by B26: the JS contradiction predates N5)
- B19-G3 Live save/load of an N5 station bog and history — needs: a running N5 station · tried: no station configured
- B18-G1 Live registration against NCS/Forge/HonSbp/Azure tenants — needs: cloud tenant credentials and a running station · tried: none available (no tenant, no station)
- B15-G1 Live reproduction of ungated outbound connection — needs: a running N5 station · tried: no station configured (measured: no stations/ dir under config/5.0.0.28)
- B9-G1 Load the built n5Hello.jar in a live N5 station — needs: a running N5 station · tried: no station configured (measured: no stations/ dir under config/5.0.0.28)
- B8-G5 Live PermissionException reproduction — needs: a running N5 station · tried: no N5 station configured (measured: no stations/ dir under config/5.0.0.28)
- B1-G1 Live confirmation of module layers via the moduleConfiguration spy — needs: a running N5 station · tried: WSL has no N5 station; beta install has no configured station (measured: no stations/ dir yet)
- B63-G1 station.exe's own OS-start path via Service Control Manager — needs: a live Windows N5 station + SCM probe · tried: static import-table read only (nre.dll CreateProcessA xref is the plat.exe path, not station.exe)
- B63-G3 Live HTTP reproduction of the refreshSoftware daemon-restart path — needs: a running N5 platform daemon · tried: static disassembly + Java-chain trace only
- B64-G1 The 47 remaining Tridium modules absent from N5 with no removal/merge evidence — needs: authorized niagara-community.com developer-portal credentials · tried: WebSearch + Wayback (portal 302-redirects to Salesforce login)
- B64-G2 The 59 N4 doc-guides absent from docDeveloper.jar — needs: same portal credentials · tried: confirmed uniform login gate on /s/article/<slug>
- B68-G6 Live station confirmation of the servlet Context-threading audit gap — needs: a running N5 station · tried: static bytecode census only
- B70-G3 Live-station probe for BIActionAuditProvider UI consumption — needs: a running N5 station · tried: static read only
- B43-G4 NativePlatformProviderNpsdk getKeyMaterial0/setKeyMaterial0 native RE — needs: a platform/embedded image bundling the compiled npsdk lib · tried: this desktop install ships only the com.tridium.npsdk-native Gradle plugin, no native artifact
- B76-G3 Same npsdk native reverse on an embedded image — needs: a device/embedded build · tried: absent from this Beta desktop install

## Stop control (primary = read-only-investigable exhaustion, METHODOLOGY §8)

- **Open gaps — read-only investigable**: 20
- **Open gaps — requires-execution**: 16
- **Open gaps — blocked**: 63
- Consecutive iterations with empty backlog (secondary): 0/2
- Budget cap (default safety net): none

## Dismissed file types

<!-- Populated during BOOTSTRAP after census-target.sh (METHODOLOGY §6 step a2). Every file type starred
     by the census (>= 5 files OR >= 1 MB aggregate) must be either CLAIMED by a backlog gap or listed here
     with a stated reason. A starred type in neither is an unclosed audit hole.
     Format (one line per dismissed type):
       - .<ext> — <N> files · <M> MB — dismissed: <reason>
     Example:
       - .lnk — 312 files · 0.1 MB — dismissed: Windows shell shortcuts, no application data
       - .mdb — 681 files · 450 MB — dismissed: Access databases, out of scope for this focus
     If no types are dismissed (all starred types are covered by gaps), write: none -->

- none

<!--
## Campaign queue

BOOTSTRAP: this section does not exist until the first focus-STOP audit enqueues an entry (§8c).
The loop creates this section on the first focus STOP that finds enqueued > 0; it never exists
at BOOTSTRAP. Do NOT pre-create it; omit the heading and table entirely for single-focus corpora.

Before the queue section is created, campaign_bounds: lives in Stop control (see above; optional;
absent = no bounds). Once the queue section is created, all campaign scalars move into it:
  the last_audit field: written after each focus-STOP coverage audit; ISO timestamp followed by
    enqueued count; absent ≠ enqueued=0. Grammar: see METHODOLOGY §8c.
  the campaign_started field: written at queue creation (first focus-STOP audit that creates the
    queue); anchors wall-clock bound check. Grammar: see METHODOLOGY §8c.
  the campaign_iterations field (example value 0): incremented on every block commit across all
    entries; anchors iteration-count bound check. Root-focus blocks count from BOOTSTRAP.
    Grammar: see METHODOLOGY §8c.
  the campaign_stop field: written only when a bound fires; grammar: see METHODOLOGY §8c.

The loop pops the next `pending` entry at each focus STOP; campaign STOP fires when no entry
is `pending` or `active` (all rows carry terminal state `done` or `bound-stopped`) AND the most
recent `last_audit:` shows enqueued=0.

depth is the length of the parent chain from root (root entry depth 0; a child of root has
depth 1); every kind (focus, tier, sub-topic) counts toward max-depth.

Column grammar (closed — parsers read leading tokens):
  State: pending | active | done | bound-stopped | rejected
  Kind:  focus | tier | sub-topic

One row per campaign entry. Do not add free-text columns; put notes in the Seed/Convergence cells.

Example entries (the live section has no rows at creation — the loop fills them in):
| Name | Parent | Kind | Seed | Convergence | State |
|---|---|---|---|---|---|
| <slug> | root | focus | <brief description of what to investigate> | <done condition> | pending |
| <slug-child> | <parent-slug> | tier | <description> | <done condition> | pending |
-->
