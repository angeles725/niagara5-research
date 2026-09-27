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
covered_blocks: 57
gaps_closed: 101
known_gaps: 279
investigable_open: 132
requires_execution_open: 8
blocked_open: 27
deferred_open: 10
undocumented_findings: 0
blocks_since_retro: 7
last_iteration_ts: 2026-09-27T11:10:00Z
<!-- /research-state.v1 -->
<!-- last_iteration_ts is always present — write the ISO-8601 UTC timestamp on every block commit;
     applies to every corpus (single-focus and campaign alike); the stall-detection instrument reads it
     from this envelope; do not pre-fill with a placeholder, update it when committing a block. -->

## Coverage

- **Covered blocks**: 57 (B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, B11, B12, B13, B14, B15, B16, B17, B18, B19, B20, B21, B22, B23, B24, B25, B26, B27, B28, B29, B30, B31, B32, B33, B34, B35, B36, B37, B38, B39, B40, B41, B42, B43, B44, B45, B46, B47, B48, B49, B50, B51, B52, B53, B54, B55, B56, B57)
- **Coverage metric**: 101 / 279 closed
- **Last iteration**: 2026-09-27 — N5-G5 core API delta (B5)

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
| low | B1-G6 The 5 automatic-module jars (unterjar packaging) — why not explicit modules | jar manifests | pending |
| low | B2-G2 Meaning of the Compact3 javac argument in N5 plugins | n-plugin bytecode | pending |
| low | B2-G3 Read the TestNG Support in Niagara 5 doc | docDeveloper.jar | pending |
| low | B3-G5 securityBridge.jar 2-class bootclasspath shim | securityBridge.jar | pending |
| low | B2-G4 Does N5 niagaraTest still hit the N4 plugin zero-tests bug | prototype build | requires-execution → §19 (run niagaraTest on a sample module) |
| high | B4-G8 Deep-read official upgrade guides (upgradingToN5, upgradingUItoN5, upgradingJDK) + porting checklist for our modules | docDeveloper.jar doc/upgrade | ✅ covered — B10 |
| medium | B4-G1 Decode the help search index binary format doc/{words,postings,documents,worddocs}.dat | help.jar Searcher + dat files | pending |
| medium | B4-G5 N5 equivalent of N4 niagara-help jdk/ JDK-class bajadoc stand-ins | docDeveloper.jar | pending |
| low | B4-G3 Line-count N5 vs N4 shipped source (docSource) | docSource jars | pending |
| low | B4-G4 Confirm no javadoc-shaped artifact across all 1,013 N4 jars | N4 jars | pending |
| low | B4-G7 Census of N5 PDF manuals | install + doc jars | pending |
| low | B4-G2 Render bajadoc via HtmlCompilerMain | help.jar | requires-execution → §19 (run HtmlCompilerMain on a bajadoc file) |
| medium | B6-G1 com.tridium.nre.subscription in nre.jar (subscription bootstrap outside baja.jar) | nre.jar bytecode | ✅ covered — B34 |
| medium | B6-G3 Full caller enumeration of LicenseManager.checkFeature across all N5 jars (license-gated features map) | all module bytecode | ✅ covered — B11 |
| low | B6-G2 Code path of the security/licenses/conf directory | baja.jar license | ✅ covered — B34 |
| medium | B7-G1 Exact Gradle task-graph edge slotomatic ↔ compileJava ↔ nap processor | prototype build | ✅ covered — B9 |
| low | B7-G2 Defining module of niagara.rpc.NiagaraRpc (claimed by NullProcessor) | module bytecode | pending |
| high | B8-G4 Confirm or refute that outbound HTTP/sockets from third-party modules are ungated in N5 (okhttp3/Jetty client layer) | nre.jar + bin/ext + module bytecode | ✅ covered — B15 |
| medium | B8-G3 Are reflection / JMX / native-library / system-property accesses gated elsewhere in N5 | nre.jar + baja.jar | ✅ covered — B33 |
| low | B8-G1 ModifyProtectedPropertiesPermission construction sites | module bytecode | pending |
| low | B8-G2 Permission-denial log filename: code vs doc discrepancy | nre.jar | pending |
| medium | B10-G1 Compile-verify the 15-item porting checklist by building DashboardPan/CompPan/ColdRoomPan against N5 | prototype build | ✅ covered — B16 |
| high | B10-G5 The n5mig station migration application: where it ships, what it transforms (N4 station → N5) | install bin + migration/migrator modules | ✅ covered — B14 |
| medium | B10-G2 Locate the full Niagara 5.0 Breaking Changes list (in-jar or web-only) and diff vs B10 32-row table | docDeveloper.jar + web | pending |
| low | B10-G3 BFoxProxySession.getRemoteNiagaraVersion signature/package | docSource + javadoc | pending |
| low | B10-G4 Re-run fox grep across our three modules to certify CHK-14 | our module sources | pending |
| low | B10-G6 DashboardPan-ux preview tooling has no N5-relevant surface | our module sources | pending |
| medium | B5-G3 niagaraSync subsystem (new BINiagaraSyncCapableComplex on status types) — feeds N5-G10 | niagaraSync.jar + baja | ✅ covered — B18 |
| medium | B5-G2 Does any Tridium or our own B* type rely on the removed BObject.equals override | baja + our sources | ✅ covered — B52 |
| medium | B5-G4 The javax.baja.web import sites in our modules vs the jakarta.servlet break | our module sources | ✅ covered — B52 |
| low | B5-G1 HsmManager: real N5 drop or N4 OEM-baseline artifact | N4 stock vs OEM jars | pending |
| high | B9-G2 Real niagaraTest run with a TestNG test in the PoC (settles B2-G4) | prototype build | ✅ covered — B16 (build+sign OK; niagaraTest platform-gated: test.exe Windows-only) |
| medium | B9-G3 Is com.tridium.n-java required per module or at root (wizard template omits it) | devkit templates + PoC | ✅ covered — B51 |
| low | B9-G4 NDriver / device-driver module scaffold on N5 | devkit templates | pending |
| high | B14-G1 Run n5mig -premigrate (dry-run report) on a copy of a real N4.15 station backup/bog (e.g. PANCCADIA) with and without our modules installed | n5mig.exe + station copy | ✅ covered — B17 (partial: run blocked by license tridium:nre; static census substituted) |
| medium | B14-G3 Open the ~26 unread migrator.jar converter types (driver/protocol bog converters) | migrator.jar | ✅ covered — B24 |
| medium | B14-G4 BBogMigrator 4-phase pipeline full read | migrator.jar | ✅ covered — B24 |
| low | B14-G2 propMigration.jar 8 declarative converter classes | propMigration.jar | ✅ covered — B24 |
| low | B14-G5 MigratorTypeResolver / MigratorOrdConverter / MigrationUtils | migrator.jar | ✅ covered — B24 |
| medium | B15-G2 Independent egress gate inside okhttp / jetty-client / jetty library internals | bin/ext third-party jars | ✅ covered — B55 |
| low | B15-G3 OS/platform-level egress control outside NiagaraPermission (daemon, platform firewall) | platform modules | pending |
| low | B15-G4 Full niagara.security.dashboard module: any provider surfacing network grants | security dashboard module | pending |
| medium | B12-G4 nftables firewall backend: N5-only? and is it PermissionManager-gated | nre.jar firewall | ✅ covered — B33 |
| medium | B12-G5 totpAuth enrollment UI flow and secret storage path | totpAuth.jar | ✅ covered — B38 |
| medium | B12-G6 SAML IdP servlet flow in N5 | saml.jar | ✅ covered — B38 |
| low | B12-G1 Location of the Nimbus OAuth SDK jar required by oauth2 | bin/ext + modules | pending |
| low | B12-G2 platCrypto daemon protocol | platCrypto.jar | pending |
| low | B12-G3 signingService Fox CSR protocol | signingService.jar | pending |
| low | B12-G7 LDAP v2/v3 bind details | ldap.jar | ✅ covered — B38 |
| low | B12-G8 SRP6 key exchange: new in N5 or carried over | baja/nre | ✅ covered — B38 |
| medium | B11-G1 Capacity licensing mode: Metrics.isUsingCapacityLicensing() and resource.limit | baja metrics + license | ✅ covered — B34 |
| low | B11-G3 Six dynamic (non-literal) checkFeature/getFeature call sites | module bytecode | pending |
| low | B11-G4 Upgrade B11 bytecode-offset citations to source file:line via full decompile | organized/ decompile | pending |
| deferred | B11-G2 OEM-branded module absence (Honeywell UI, eSignature): edition gap vs removal | OEM N5 build | pending (parked; needs an OEM N5 build) |
| medium | B13-G1 The 49 Tridium code modules absent from N5 with no removal/merge evidence: confirm against N5 GA docs | N5 GA / web docs | pending |
| medium | B13-G4 Why N5 module.xml declares fewer explicit dependencies (declaration slimming) | module.xml + build plugin | ✅ covered — B51 |
| low | B13-G2 cloudLink family stuck at vendorVersion 5.0.0.26 | module.xml | pending |
| low | B13-G3 59 N4 doc-guides absent from docDeveloper.jar | doc jars | pending |
| low | B13-G5 What the Atlas hardware (platHwScanAtlas) is | platHwScanAtlas.jar | pending |
| low | B13-G6 Licensing of Honeywell-branded modules shipped under vendor Tridium | cloudLinkForge/HonSbp | pending |
| medium | B18-G2 cloudLink AMQP link-handler method-body trace | cloudLink.jar | ✅ covered — B42 |
| medium | B18-G7 Fate of N4 nCloudDriver (Azure IoT / Forge) in N5 | N4 vs N5 modules | ✅ covered — B42 |
| low | B18-G3 Per-provider channel config classes (Forge / HonSbp) | cloudLink satellites | ✅ covered — B42 |
| low | B18-G4 Other BINiagaraSyncCapableComplex consumers (full-tree search) | organized/ decompile | ✅ covered — B37 |
| low | B18-G5 NCS-Agent registration vs cloudLinkNcs station identity convergence | NCS-Agent + cloudLinkNcs | pending |
| low | B18-G6 Deeper NCS-Agent Go binary RE beyond strings | NCS-Agent Go binary | pending |
| medium | B19-G1 BOrientSystemDb at-rest AES encryption toggle: new in N5 or pre-existing | orientSystemDb.jar vs N4 | ✅ covered — B57 |
| low | B19-G2 EncryptionKeySource enum in N4 (never decompiled there) vs N5 five members | N4 baja decompile | ✅ covered — B57 |
| low | B19-G4 KeyRing/SecurityInitializer proprietary blocker unchanged in N5 | nre/baja | ✅ covered — B43 |
| medium | B19-G5 OrientDB 3.2.23 → 3.2.55 on-disk compatibility for migrated stations | prototype run | requires-execution → §19 (open an N4 systemDb store with the N5 OrientDB libs) |
| medium | B17-G2 Why wb.exe boots on the unlicensed beta while n5mig/station do not (tridium:nre gate path) | nre.jar + launchers | ✅ covered — B53 |
| low | B17-G3 Reconstruct the native launcher VM/module-path args to run n5mig via java | bin launchers + nre.dll | pending |
| low | B17-G4 DefrostMode declared in ColdRoomPan-rt module.xml has zero bog instances | our module + PANCCADIA bog | pending |
| medium | B20-G2 niagaraSync ticks integration in kitControl BLoopPoint (BNiagaraSyncTicks) semantics | kitControl + niagaraSync | ✅ covered — B37 |
| medium | B20-G3 BIActionAuditProvider old-value audit path end-to-end | baja security + control | ✅ covered — B41 |
| medium | B20-G4 History rollover mechanism after BCapacity storage-size mode removal (migration hazard) | history.jar | ✅ covered — B26 |
| low | B20-G5 Decompile control/alarm/kitControl/schedule to source for file:line citations | organized/ decompile | pending |
| low | B21-G1 uxBuilder ux/make + ux/fe sub-packages: new vs N4 | uxBuilder.jar | pending |
| low | B21-G2 JxBrowser vs JavaFX WebView default selection in Workbench | workbench.jar | pending |
| medium | B21-G3 CSP / security headers served by niagara.web / jetty (static half) | web.jar + jetty | ✅ covered — B27 (static half) |
| low | B21-G4 Stale JxBrowser 7.30.3 log string vs 9.5.0 engine | jxBrowser.jar | pending |
| high | B16-G1 Run niagaraTest on the ColdRoomPan TestNG test via the Windows test.exe (WSL interop) — may hit the tridium:nre license gate | prototype run | ✅ covered — B29 (test.exe blocked by license tridium:nre; plain TestNG 51/51) |
| high | B16-G6 Port the 5 N4 JUnit4 ColdRoomPan tests to TestNG and write a JUnit4→TestNG recipe | our module tests | ✅ covered — B29 |
| high | B16-G7 Port CompPan and DashboardPan (multi-part rt/ux/wb, jakarta servlet) with the B16 recipe | prototype build | ✅ covered — B28 |
| medium | B16-G2 Does a multi-module group like DashboardPan still need a parent grouping file | devkit templates + build | ✅ covered — B28 |
| low | B16-G3 Locate the TestNG Support in Niagara 5 doc | docDeveloper.jar | pending |
| low | B16-G5 moduleTest dependency vendorVersion truncated 2.0.7 → 2.0 | n-plugin | ✅ covered — B51 |
| medium | B22-G1 Decompile bacnetUtil to resolve the Descriptor interface behind BC-10 | bacnetUtil.jar | ✅ covered — B35 |
| medium | B22-G3 Which other bundled drivers still extend the deprecated basicDriver chassis | driver modules | ✅ covered — B35 |
| low | B22-G4 niagaraDriver logic diff N4→N5 | niagaraDriver.jar | ✅ covered — B35 |
| low | B22-G2 Compile a basicDriver-based module on N5 | prototype build | requires-execution → §19 (build a minimal basicDriver module against the local mirror) |
| medium | B23-G1 PROGRAM ModuleType is dead code: where program objects actually load (com.tridium.program) | program.jar | ✅ covered — B32 |
| medium | B23-G3 Is skipModuleValidation blacklisted on the N5 command line | nre + launchers | ✅ covered — B53 |
| low | B23-G2 Locate com.tridium.crypto.core (absent from nre/baja) | bin/ext + modules | pending |
| low | B23-G5 NreInstantiator DI plumbing | nre.jar | pending |
| low | B23-G6 Prove or refute module.xml vs module-info dependency divergence | module census | pending |
| high | B24-G6 No converter exists for tagdictionary (105), kitControl (100), nrio (96) PANCCADIA objects — confirm they load unchanged in N5 (type names, slot compatibility) | migrator + module registry | ✅ covered — B31 |
| medium | B24-G2 Census the PANCCADIA points/histories/alarm stores beyond config.bog | PANCCADIA station copy | pending |
| low | B24-G3 Tabulate the 180-entry zwave removal type list | migrator.jar | pending |
| low | B24-G4 MigrationUtils (40 static methods) line-by-line read | migrator.jar | pending |
| low | B24-G5 BBackupDistMigrator / BPxMigrator / premigrate classes full bodies | migrator.jar | pending |
| medium | B27-G3 NiagaraConstraintSecurityHandler / NiagaraAuthenticator: web authn/authz proper | jetty.jar + web.jar | ✅ covered — B41 |
| medium | B27-G6 Adopt the real x-niagara-csrfToken in DashboardPan-ux on N5 instead of the hand-rolled X-Requested-With guard (design note) | web.jar CsrfUtil + our module | ✅ covered — B52 |
| low | B27-G2 Per-module jetty-web.xml census | all modules | pending |
| low | B27-G4 NModuleInfo.isWar() definition | baja/jetty | pending |
| low | B27-G5 hx.jar WebAppContext registration path | hx.jar | pending |
| low | B26-G2 Can a raw property-sheet string edit construct a restrictBy=2 capacity on N5 | history + workbench | pending |
| low | B26-G3 BHistoryDbTable subclasses: alternate capacity enforcement | history.jar | pending |
| low | B26-G4 BTypeSpecConverter generic simple-value handling | migrator.jar | pending |
| low | B29-G4 Does the niagaraTest runner require BTestNg even for pure-logic tests | test module | pending |
| low | B29-G5 compileModuleTestJava "cannot determine module name" message root cause | n-plugin | pending |
| low | B29-G3 assertArrayEquals mapping in the port script | tools/port-junit4-to-testng.py | pending |
| low | B25-G1 instanceof-pattern adoption (bytecode-invisible) via decompiled sources | organized/ + docSource | pending |
| low | B25-G2 Classify the 34 ambiguous Deque-family SequencedCollection call sites | bytecode census | pending |
| medium | B25-G3 Full 253-jar jdeprscan --for-removal pass | all jars | ✅ covered — B44 |
| low | B25-G4 Read the switch logic of control.jar B*Writable pattern switches | control.jar | pending |
| medium | B32-G2 Compile a program object that depends on a non-default module (readability end-to-end) | prototype run | requires-execution → §19 (needs a running station; blocked with the license gate) |
| low | B32-G3 Confirm bin/javac ships on embedded-tier device images | device image | pending |
| low | B32-G4 Any station/platform flag relaxing mandatory program signing beyond dev-license test mode | program.jar + nre | pending |
| low | B30-G1 Format and verifier of the bin/ext <jar>.jar.sig sidecars | bin/ext + nre | pending |
| medium | B30-G3 N5 embedded trust anchor that accepts the Honeywell code-signing chain | nre/baja crypto | ✅ covered — B53 |
| low | B30-G4 Full N4 obfuscation census (beyond the 53-module ZKM sample) | N4 organized/ | pending |
| low | B31-G1 Slot diff for 5 types in the 4.14→4.15 version gap (needs an N4 4.15 decompile) | N4 4.15 jars | pending |
| low | B31-G3 Re-read BWebBogConverter / BJettyQoSFilterMigrator property lists | migrator.jar | pending |
| low | B31-G5 box HistoryChannel/AlarmChannel parent swap BBoxChannel → BWrapperBoxChannel | box.jar | pending |
| medium | B35-G1 niagaraSync package semantics (standby/active RPC state machine in niagaraDriver) | niagaraSync + niagaraDriver | ✅ covered — B37 |
| low | B35-G2 BNiagaraEdgeLiteStation | niagaraDriver | pending |
| low | B35-G5 BFoxClientWebsocketBehavior / BReachableStations deeper read | niagaraDriver + fox | pending |
| medium | B33-G3 All callers of SystemPropertiesUtil.setSystemProperty (ungated except a 24-key denylist) | all modules | ✅ covered — B40 |
| medium | B33-G4 BServerPort.adapter → nft rule-hint injection reachability | nre + baja | ✅ covered — B40 |
| medium | B33-G5 Where niagara.firewall.enabled / frontend=nft are set by default (platform template?) | install + platform | ✅ covered — B40 |
| low | B33-G1 JMX usage across the remaining modules | all modules | pending |
| low | B33-G6 Operational impact of the firewall losing port-redirect (N4 pf) in N5 nft | platform docs + code | pending |
| high | B28-G7 niagara.alarm transitive dependency on javafx/batik platform modules forces stub module-info jars when compiling third-party modules on Linux — find the supported way (Windows javac.exe? SDK module path?) | n-plugin + alarm/gx/bajaui module-info | ✅ covered — B39 |
| medium | B28-G2 Batik (org.apache.xmlgraphics) provider: JavaFX confirmed in the bundled JRE release MODULES (7 javafx.* modules); batik not a JRE module and svgBatik.jar holds no org/apache classes | jre + bin/ext + modules | ✅ covered — B39 |
| low | B28-G1 Fate of the N4 test-wb module in N5 | modules | pending |
| medium | B28-G3 Does the Windows jre/bin/javac.exe resolve niagara.alarm without stubs | prototype build | ✅ covered — B39 |
| medium | B34-G3 Caller of AuthenticatedLicenseRetrievalUtil (perpetual LicenseAccessKey flow) | nre + workbench | ✅ covered — B53 |
| low | B34-G1 Backup-restoration write site for the subscription cache | nre | pending |
| low | B34-G4 Workbench UI consumer of the LicenseAccessKey flow | workbench | pending |
| low | B34-G5 N4 nre.jar client-package comparator for subscription | N4 nre | pending |
| low | B34-G6 Is security/licenses/conf N5-only | N4 vs N5 | pending |
| low | B36-G1 Read doc/js/buildingJS.html and doc/requirejs.html fully | docDeveloper.jar | pending |
| medium | B36-G2 Live gradlew gruntBuild / gruntCi run on a JS module | prototype build | requires-execution → §19 (needs node/npm on PATH + a JS module scaffold) |
| low | B36-G3 Locate the grunt-niagara successor npm package contents | m2 + npm | pending |
| low | B38-G1 Account-lockout defaults: N4 vs N5 provenance | baja security | pending |
| medium | B38-G2 SP-side SAML signature algorithm allowlist | saml.jar | pending |
| low | B38-G3 LDAP Kerberos/GSSAPI location | ldap + kerberos | pending |
| low | B38-G4 SRP6 group size cross-check | nre/fox | pending |
| high | B37-G6 HA-ready design for our modules under niagaraSync: replace raw Clock.schedule timers with BNiagaraSyncTicket, state as Properties, BNiagaraSyncTicks, implement BINiagaraSyncCapableComplex (design note + PoC) | our modules + niagaraSync API | ✅ covered — B45 |
| low | B37-G2 Three driver-specific sync-folder classes | bacnet/modbus/niagaraDriver | pending |
| low | B37-G4 niagaraSync license-fault severity wiring | niagaraSync | pending |
| low | B37-G5 modbusAsync/modbusTcp chassis lineage | modbus modules | pending |
| high | B41-G6 DashboardPan N5 write path: pass the servlet request niagara.context (authenticated user) into set()/invoke so writes land in AuditHistory with user and old→new value (design + PoC in the ported copy) | our module + web/baja | ✅ covered — B46 |
| medium | B41-G1 SecurityAuditEvent / SecurityAuditor full mapping | baja security | ✅ covered — B54 |
| low | B41-G2 JAAS Subject / AddSubjectFilter contents | web.jar | pending |
| low | B41-G3 Jetty LoginService / UserIdentity resolution | jetty.jar | pending |
| low | B41-G5 Do first-party N5 servlets thread niagara.context through to writes | web modules | pending |
| low | B42-G2 Three cloudLinkExtension satellite modules | cloudLinkExtension* | pending |
| low | B42-G3 retriableError() classification body | cloudLink | pending |
| low | B42-G4 Authoritative statement on nCloudDriver retirement (newer releases / web) | web | pending |
| low | B42-G5 Forge message-handler classes | cloudLinkForge | pending |
| low | B42-G6 Throttle / backpressure numeric defaults | cloudLink | pending |
| high | B43-G1 KeyRing alias rename javax.baja.security.BAes256PasswordEncoder.key → niagara.security.BAes256PasswordEncoder.key: does N5 (or n5mig) remap it, or do migrated stations lose reversible passwords? | nre KeyRing + migrator | ✅ covered — B47 (MITIGATED by n5mig force-clear/passphrase path; PANCCADIA uses external encoding (3 pbkdf2-aes-256 secrets)) |
| low | B43-G2 N4 orientSystemDb default-encryption parity (narrows B19-G1) | N4 orientSystemDb | ✅ covered — B57 |
| low | B43-G3 N4 EncryptionKeySource member count | N4 baja decompile | ✅ covered — B57 |
| low | B43-G4 NativePlatformProviderNpsdk getKeyMaterial0/setKeyMaterial0 native RE | native npsdk lib | pending |
| low | B39-G2 Does the batik-awt-util version matter beyond 1.19 | prototype build | pending |
| medium | B39-G3 Why 3 other absent gx.jar requires (batik.transcoder, swt win32, owasp.encoder) never fail compilation | javac module resolution | ✅ covered — B55 |
| low | B39-G4 Runtime behaviour of a module that really calls JavaFX/Batik APIs with these artifacts | prototype build | requires-execution → §19 (needs a licensed station to run) |
| low | B40-G1 OPC UA component-name charset vs ruleHintOverride validation | opcUaServer + baja | pending |
| medium | B40-G2 Which BComponentSpace subtype a live station instantiates (decides whether BTunnelService ruleHintOverride is validated) | baja + station | pending |
| low | B40-G4 N4 netsh / CAP_NET_ADMIN host-firewall mechanism | N4 platform | pending |
| medium | B46-G1 Slotomatic-generated setters pass null Context (setXxx → setString(prop, v, null)): framework-wide audit implication and recommended pattern | slotomatic + baja | ✅ covered — B49 |
| medium | B46-G2 Implement the x-niagara-csrfToken check in the DashboardPan-ux port | our module + web.jar | ✅ covered — B52 |
| low | B46-G3 Should the 3 read-side BOrd.get(this, null) resolutions use the request Context | our module | pending |
| deferred | B46-G5 Port the audited-write fix back into the live N4 DashboardPan source (same N4 gate B829/B830) — product change in the client repo, needs operator decision | client repo | pending (parked; recommendation only — outside research scope) |
| low | B47-G1 Confirm the vestigial source-.kr extraction code has no live call site (Premigrate + bytecode xref) | migrator.jar | pending |
| low | B47-G2 Purpose of the source-.kr extraction machinery (dist-container encryption?) | migrator.jar | pending |
| low | B47-G3 AxPasswordUtil.usesPasswordEncodings definition | migrator/baja | pending |
| medium | B48-G1 Resolve the public Java 21 vs Java 25 contradiction (first-party says 25; code confirms JRE 25.0.4) | web + install | ✅ covered — B56 (narrowed: Java 25 authoritative (first-party + local jre/release); HA name = Niagara Sync) |
| medium | B48-G5 N5 HA/niagaraSync 'limited availability first' signal — scope of niagaraSync at GA | web + niagaraSync | ✅ covered — B56 (narrowed: Java 25 authoritative (first-party + local jre/release); HA name = Niagara Sync) |
| deferred | B48-G2 Read the login-gated docs.niagara-community.com N5 breaking-changes page | Developer Program credentials | pending (parked; needs Developer Program login) |
| deferred | B48-G3 Re-run the 49 absent-module check on the N5 GA build (target Dec 2026) | N5 GA install | pending (parked; needs a GA build) |
| deferred | B48-G4 Watch for a post-GA nCloudDriver statement | web after GA | pending (parked; revisit after GA) |
| medium | B49-G2 Trace N5 NiagaraRpc servlet/BOX dispatch for Context injection into @NiagaraRpc methods | web/box modules | ✅ covered — B54 |
| low | B49-G3 Feasibility of a Context-taking overload in Slotomatic output | slotomatic | pending |
| low | B49-G4 Whole-corpus census of generated action invoke wrappers | organized/ | pending |
| low | B44-G1 The 13 cloudLink* finalize() overrides: resource, shared base class, Cleaner replacement | cloudLink family | pending |
| medium | B44-G2 AccessController-family call sites in jetty/platform/hx: inert after SecurityManager removal or live authorization | jetty/platform/hx | ✅ covered — B54 |
| low | B44-G4 svgBatik ThreadDeath usage | svgBatik | pending |
| deferred | B44-G3 Re-run jdeprscan on the 29 classpath-incomplete jars with vendor SDKs (Prosys OPC UA etc.) | vendor SDKs | pending (parked; needs licensed vendor SDKs) |
| low | B45-G2 Census other modules for list/queue state under niagaraSync (no stock BSimple list; CSV String precedent) | organized/ | pending |
| low | B45-G4 Link-wiring validator rule checked only structurally | niagaraSync validator | pending |
| medium | B50-G1 Driver-module N5 build PoC (ndriver or BDeviceNetwork chassis) | prototype build | requires-execution → §19 (scaffold + build a minimal ndriver module) |
| low | B50-G2 Native-module (npsdk) build on N5 | m2 native plugins | pending |
| low | B50-G6 Greenfield (non-ported) N5 module path via the devkit wizard templates | devkit.jar | pending |
| low | B54-G1 Is -Djava.security.manager set by the N5 launcher (moot: vulnerable Subject API never called) | launchers | pending |
| low | B54-G3 Open SecurityAgent / SecurityProviderAdvice directly | nre.jar | pending |
| low | B54-G4 BUserService.auditLoginAttempt appears dead code | baja | pending |
| low | B54-G5 BOrionSecurityAudit parallel audit DB | orion | pending |
| medium | B51-G2 Where Flags.TRANSIENT/OPERATOR live in N5 (niagara.sys.Flags?) — lints keyed on Flags vocabulary | baja | pending |
| medium | B51-G5 Does any real N5 gradle.kts need per-profile splitting at all (single-jar world) | PoC build files | pending |
| low | B51-G1 verify-module.sh stored check on N5 jars | prototype build | pending |
| low | B51-G3 lint-bundled-jar-class-version.sh major-version constants | kit lints | pending |
| low | B51-G4 rc-scan.sh / bog-audit.sh -rt|-ux|-wb assumptions | kit lints | pending |
| low | B51-G6 lint-wb-threading: Swing invokeLater vs JavaFX Platform.runLater on real N5 wb code | prototype build | pending |
| low | B51-G7 Measured N4 vs N5 explicit dependency counts | module.xml census | pending |
| deferred | B51-G8 Implement the build-n5-module kit fork in niagara-tools (9-step plan in B51 §51.7) | niagara-tools repo | pending (parked; separate kit campaign in niagara-tools with its own gates) |
| medium | B53-G3 niagara.commandLinePropertyDenyList is itself read via System.getProperty — can a -D override neuter the denylist (static hypothesis, measure) | nre/baja Nre | ✅ covered — B57 |
| low | B53-G2 portalApi LicenseDownload flow | portalApi | pending |
| low | B53-G4 Runtime cacerts contents (structure only) | install jre | pending |
| low | B53-G5 TPK pin vs Honeywell leaf key identity | nre + signed jars | pending |
| low | B53-G6 TRIDIUM_DEV_CA_CERT usage | nre | pending |
| low | B52-G1 CsrfUtil token compare is String.equals (not constant-time) — platform code, low practical severity | web.jar | pending |
| low | B52-G2 Frontend should refetch the CSRF token after a 403 | our module | pending |
| deferred | B52-G5 Port the CSRF + audited-write hardening back to the live N4 DashboardPan (product change, operator decision) | client repo | pending (parked; recommendation only) |
| low | B56-G2 Niagara Sync vs Cloud Suite licensing coupling | web + license features | pending |
| deferred | B56-G3 Supervisor Linux support at N5 GA | N5 GA docs | pending (parked; revisit at GA) |
| low | B56-G4 Survey the rest of the 2023 Loyalty Program Q&A transcript | web | pending |
| low | B57-G1 Are nre.properties-sourced JVM args also cmdline::-tagged (nre.dll disassembly) | nre.dll | pending |
| medium | B57-G2 How platDaemon spawns station.exe (no ProcessBuilder in the Java corpus) — remote reachability of JVM-arg injection | platDaemon + native | pending |
| low | B57-G4 N4 BogPasswordObjectEncoder semantics for shared/undefined | N4 baja | pending |
| low | B55-G1 Cross-check the transitive-vs-plain javac rule with the Windows javac.exe | prototype run | pending |
| low | B55-G2 Decompile okio-jvm for any egress hook | bin/ext okio | pending |
| low | B55-G4 Does any N5 module hit the okhttp-5.5.0 empty placeholder jar trap | bin/ext + builds | pending |
| deferred | B4-G6 Is the absence of docUser/migration doc jars permanent in N5 GA or beta-only | N5 GA install | pending (parked; needs a GA build) |

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

## Blocked gaps (each tagged with what it needs)

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

## Stop control (primary = read-only-investigable exhaustion, METHODOLOGY §8)

- **Open gaps — read-only investigable**: 132
- **Open gaps — requires-execution**: 8
- **Open gaps — blocked**: 27
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
