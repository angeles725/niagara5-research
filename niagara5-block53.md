# Block 53 — N5 launch gates: the tridium:nre license check, dangerous system properties, the code-signing trust anchor and license retrieval

> Research closing four named child gaps from [Block 17], [Block 23], [Block 30], [Block 34]: **B17-G2**
> (why `wb.exe` boots clean on an unlicensed install while `n5mig.exe`/`station.exe` do not), **B23-G3**
> (whether `niagara.classLoader.skipModuleValidation` and other dangerous sysprops are blacklisted at the
> command line), **B30-G3** (where N5's embedded trust anchor for the Honeywell code-signing chain lives and
> how `validateCertChain` uses it), and **B34-G3** (the full caller chain of
> `AuthenticatedLicenseRetrievalUtil`). Covers: `Nre.runClass`'s `shouldCheckNreLicense` gate and its two
> named exemptions; `WbMain`'s own downstream (UI-dialog-mediated) `tridium:nre`/`tridium:workbench` checks;
> the two independent Java-side "dangerous sysprop" gates (`niagara.commandLinePropertyDenyList`,
> `SystemPropertiesUtil.PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST`) and the native `-Dcmdline::` tagging
> mechanism that feeds them, confirmed via `strings` on `nre.dll`; `CoreCryptoManager`'s two independent trust
> mechanisms (PKIX chain-building against the runtime's own bundled `cacerts` + a hardcoded RSA public-key
> pin, "TPK"); and the full client↔server round trip (`RemoteLicenseAccessKeyFileUtil` →
> `GetLicenseAccessKeyMessage` → niagarad's `UpdateDaemonServlet`) that populates
> `AuthenticatedLicenseRetrievalUtil.getLicenseAccessKeyFromResponse`'s JSON argument, plus its four concrete
> Workbench/automation callers. Does **not** cover: live confirmation of any of this on a licensed station
> (all `[CERT]`, source-level only, this session); the actual contents of the runtime's bundled `cacerts`
> file (not opened, per this task's secrets discipline — see Self-verification); a byte-level identity
> check between the hardcoded TPK and the Honeywell leaf certificate's public key (not performed, named
> child gap).
>
> Subject version: local N5 install **5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the
> same install [B1],[B17],[B23],[B30],[B34] read; decompiled sources at
> `/home/cristian/niagara5-research/organized/{baja,workbench,platform,platDaemon,provisioningNiagara,
> portalApi,_bin-ext/nre,_bin-ext/niagarad}/vineflower/`.
>
> Sources: `organized/baja/vineflower/com/tridium/sys/Nre.java` (1400 lines, whole-file grep + targeted
> reads this session); `organized/workbench/vineflower/com/tridium/workbench/shell/WbMain.java`;
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/util/SystemPropertiesUtil.java` (whole file, 164
> lines); `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/io/CoreCryptoManager.java` (1561
> lines, read in full) and `.../cert/CertificateChainValidator.java` (whole file, 260 lines);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SecurityConstants.java` (whole file, 343
> lines); `organized/baja/vineflower/com/tridium/sys/module/{ModuleSetClassLoader,
> NModuleModuleFinderFactory}.java` (targeted re-grep, cross-checking [B23]'s own citations);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/license/AuthenticatedLicenseRetrievalUtil.java`
> ([B34]'s already-read file, re-grepped for callers this session);
> `organized/platDaemon/vineflower/com/tridium/platDaemon/ui/licenseinstall/RemoteLicenseAccessKeyFileUtil.java`
> (whole file, 76 lines); `organized/platform/vineflower/com/tridium/platform/daemon/message/
> GetLicenseAccessKeyMessage.java` (whole file); `organized/_bin-ext/niagarad/vineflower/com/tridium/
> niagarad/servlet/UpdateDaemonServlet.java` (targeted read, lines 620–710); the four caller files listed
> in §53.4's table; `strings` output over `/mnt/c/Program Files/Niagara/5.0.0.28/bin/{nre.dll,station.exe,
> wb.exe,n5mig.exe}` (native launcher binaries — structural strings only, this session).
>
> Method: whole-file/targeted reading of already-decompiled Vineflower sources (no fresh decompilation this
> session — every file read was already present in `organized/` from prior blocks) + `grep`-driven caller-
> chain tracing across module boundaries + `strings` on 4 native `.exe`/`.dll` launchers for structural
> corroboration only (no disassembly). Markers: `[CERT-hw]` verified against the live system/device —
> highest (`sources/probes/...`) · `[CERT-live]` verified against a live remote service you don't own ·
> `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official downloaded document · `[CERT-web]`
> official web (URL + date) · `[CERT-a]` secondary source/forum (URL) · `[INFER]` deduction.
> For MINIFIED/OBFUSCATED sources: n/a this block (all reads are Vineflower-decompiled, non-minified,
> already-organized `.java` source — not fresh scratch-temp decompilation).
>
> Security/licensing layer. Connects [Block 17] (§17.2's `tridium:nre` wall), [Block 23] (§23.7's
> signature gates), [Block 30] (§30.4's Honeywell PKI), [Block 34] (§34.7's `AuthenticatedLicenseRetrievalUtil`).
>
> **Type:** `mixed` — each section closes a prior block's evidence gap with fresh `[CERT]` `file:line`
> reading (evidence half), and §53.2/§53.3 draw a synthesis conclusion across the newly-read files plus
> [B17]/[B23]/[B30]'s own prior findings (synthesis half), per METHODOLOGY §11's MIXED trigger.

---

> **Orchestrator verification (2026-09-27):** `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` re-counted directly at `SystemPropertiesUtil.java:19-52` = 27 distinct string literals (all `niagara.*` hardware/platform paths, incl. `niagara.firewall.frontend.path`), matching [Block 40]; an earlier draft of this block said 23 and was corrected in place.

## 53.1 — B17-G2 CLOSED: `wb.exe`'s exemption from the `tridium:nre` wall is a two-entry hardcoded allowlist inside `Nre.runClass`, not a different feature or a different boot path `[CERT]`

[B17] §17.2 observed `wb.exe -help` boot clean on the same unlicensed install where `n5mig.exe`/
`station.exe` hit `FeatureNotLicensedException: tridium:nre`, and narrowed — but left open — *why*.
Source-level tracing this session finds the exact gate and its exact exemption list.

Every Nre-hosted launch funnels through one shared method:

```
static void runClass(NModule module, String className, String[] nreMainArgs) {
   if (shouldCheckNreLicense(module, className)) {
      licenseManager.checkFeature("tridium", "nre");
   }
   ...
```
`[CERT]` `Nre.java:498-501`.

`shouldCheckNreLicense` is a closed, two-entry allowlist keyed on the exact `(module name, class name)` pair
being launched:

```
private static boolean shouldCheckNreLicense(NModule module, String className) {
   if (module != null) {
      return "workbench".equals(module.getModuleName()) && "com.tridium.workbench.shell.WbMain".equals(className)
         ? false
         : !"portalApi".equals(module.getModuleName()) || !"com.tridium.portal.util.LicenseDownload".equals(className);
   } else {
      return true;
   }
}
```
`[CERT]` `Nre.java:469-477`.

| Launch target | `shouldCheckNreLicense` result | Consequence |
|---|---|---|
| `module == null` (bare class, no `module:` prefix) | always `true` | checked |
| `workbench:com.tridium.workbench.shell.WbMain` | `false` | **exempt** — this is `wb.exe`'s own entry point |
| `portalApi:com.tridium.portal.util.LicenseDownload` | `false` | **exempt** — the self-service "download a license" flow |
| every other `module:class` (e.g. `migrator:com.tridium.migrator.Migrate`, `station:...`) | `true` | checked — matches [B17]'s `n5mig.exe`/`station.exe` observations exactly |

`[CERT]` table built from the method body above. `Nre.java:317-320`'s own `main()` corroborates the exact
launch string used for Workbench (`"workbench:com.tridium.workbench.shell.WbMain".equals(rawArgs[0])`,
gating a loading-splash-screen trigger, not the license check itself, but confirming the literal
module​:class string wb.exe's native launcher passes as `args.parameters[0]`) `[CERT]` same file.
`workbench`'s `module.xml` confirms `moduleName="workbench"` `[CERT]`
`organized/workbench/vineflower/META-INF/module.xml:2`.

**This is not "GUI vs headless" (the informal framing [B17] used) — it is a hardcoded two-entry string
allowlist that has nothing to do with process type.** A third-party module launched by full class name
with no matching entry would be checked regardless of whether it opens a window.

**wb.exe is NOT exempt from the `tridium:nre` feature overall — it re-checks the SAME feature itself,
later, via its own UI-mediated path, instead of `Nre`'s fatal boot gate:**

```
public static void doCheckLicense() throws Exception {
   LicenseUtil.checkJreFeature();
   LicenseManager licenseManager = Sys.getLicenseManager();
   licenseManager.checkFeature("tridium", "nre");
   Feature wb = licenseManager.checkFeature("tridium", "workbench");
   ...
```
`[CERT]` `WbMain.java:661-665`. This is called from `checkLicense(false)` (`WbMain.java:550-552`), which
wraps the check in a broad `try/catch` chain that — on failure — attempts an automatic self-service
license fetch (`getLicenseFromPortal()`, `WbMain.java:634-649`, loading `portalApi:
com.tridium.portal.wb.LicenseProcedure.licenseMe()` — note this is a DIFFERENT class from the
`shouldCheckNreLicense` allowlist's `portalApi:com.tridium.portal.util.LicenseDownload`, a related but
distinct portalApi entry point), and if that also fails, shows a `BDialogPane` error dialog with a
"copy Host ID" button and calls `System.exit(0)` (graceful) rather than the `System.exit(-7)` uncaught-
exception path `Nre.java`'s generic `catch (Throwable)` uses `[CERT]` `WbMain.java:554-632`.

**Why `wb.exe -help` specifically boots clean with no license activity at all:** `WbMain.nreMain` checks for
the help option BEFORE any license call:

```
public static void nreMain(String[] strArgs) throws Exception {
   ...
   CommandLineArguments args = new CommandLineArguments(strArgs);
   if (args.hasHelpOption()) {
      usage();
   } else {
      ...
      checkWorkbenchLicense();
```
`[CERT]` `WbMain.java:719-726` (full method signature at `:719`, help branch `:723-724`, first license call
`checkWorkbenchLicense()` only reached in the `else` branch at `:726`). `checkWorkbenchLicense()` calls
`checkLicense(true)` `[CERT]` `WbMain.java:546-548`, which independently re-checks `tridium:workbench` +
`tridium:nre` (`WbMain.java:558-562`) before the heavier `doCheckLicense()` path is ever reached for a
non-`-help` launch.

**Net finding, closing B17-G2 fully (not merely narrowed):** `wb.exe -help` and `n5mig.exe -help`/
`station.exe -help` differ NOT because Workbench skips the `tridium:nre` feature, but because (1) `wb.exe`'s
own `-help` branch returns before ANY license call, while `n5mig.exe`'s `-help` is passed through as an
argument to `Migrate.nreMain` — which only runs after `Nre.runClass`'s boot-time gate already fired — and
(2) even a REAL (non-`-help`) `wb.exe` launch is exempt only from the FATAL boot-time gate, not from the
feature check itself: it performs the identical `checkFeature("tridium","nre")` call on its own, wrapped in
a UI-friendly, self-service-license-fetch-then-dialog path instead of a raw stack trace + `exit(-7)`.

## 53.2 — B23-G3 CLOSED (negative finding): `niagara.classLoader.skipModuleValidation` is in NEITHER of N5's two command-line-property denylists; the native launcher's role is limited to a generic `-Dcmdline::` tagging mechanism `[CERT]`

[B23] §23.7 documented the `skipModuleValidation` escape hatch (sysprop + `developer{skipModuleValidation=
true}` license feature) as surviving from N4 to N5 1:1, and named **B23-G3**: is this sysprop (or other
dangerous sysprops) blacklisted at the command line / in `nre.properties` by the native launcher or `Nre`
boot? This session finds N5 has exactly **two** independent Java-side "dangerous sysprop" gates, and
`niagara.classLoader.skipModuleValidation` is absent from both.

**Gate A — `niagara.commandLinePropertyDenyList`, a runtime-configurable denylist applied only when
`system.properties` is NOT user-writable:**
```
String denylistProperty = System.getProperty(
   "niagara.commandLinePropertyDenyList",
   "niagara.export.preventCSVInjection,niagara.webbrowser.disable,niagara.webbrowser.urlAllowList,
    niagara.baja.formatDenyList,niagara.baja.formatDenyListExclusions,jdk.tls.rejectClientInitiatedRenegotiation"
);
...
for (String denylistedProp : denylistedProps) {
   ... System.clearProperty(trimmedDenylistedProp); System.clearProperty("cmdline::" + trimmedDenylistedProp);
```
`[CERT]` `Nre.java:801-820` (default list string reflowed for line width; verbatim on one line in source).
`niagara.classLoader.skipModuleValidation` does **not** appear in this default 6-entry list — confirmed by
direct inspection of the literal string, not a search miss (negative-existence claim over an artifact
actually opened, per METHODOLOGY §3). This gate only runs `if (!hasSystemPropsWriteAccess)` (`:802-803`,
`:826-832`) — i.e. it protects `system.properties`-file values from being silently overridden by an
unprivileged command-line `-D`, for the 6 named properties only.

**Gate B — `SystemPropertiesUtil.PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST`, a hardcoded, unconditional,
fatal-on-violation set:**
```
public static final Set<String> PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST = ... Arrays.asList(
   "niagara.dhcpd.adaptersEnabledFile", "niagara.dhcpd.configurationFile", "niagara.dhcpd.leaseFile",
   "niagara.filestore.niagara.symlinks", "niagara.filestore.niagara_user.symlinks",
   "niagara.ieee8021x.configurationFilePattern", "niagara.ieee8021x.pkiCertificatesDirectory",
   "niagara.ieee8021x.statusFilePattern", "niagara.link.configurationFile",
   "niagara.platDataRecovery.{activeDirectoryPath,chunkfsStatsPath,geomPath,mountPath,persistentDirectoryPath}",
   "niagara.platNtp.{configurationFilePath,driftFilePath,statisticsDirectoryPath}",
   "niagara.firewall.frontend.path", "niagara.use.snap.usermgr",
   "niagara.wifi.{accessPointConfigurationFile,allowListFile,channelConfigurationFile,
    clientConfigurationFile,configurationPropertiesFile,configurationStatusFile,hostapdCliFile,wpaCliFile}"
);
```
`[CERT]` `SystemPropertiesUtil.java:19-51` (27 literal entries, brace-grouped above for readability — every
one is its own full string in source). Every entry is a filesystem-path override for embedded/hardware
subsystems (DHCP daemon, WiFi, 802.1X, NTP, platform data-recovery, firewall front-end, symlink policy) —
**none is a security/crypto/module-verification property.** `niagara.classLoader.skipModuleValidation` is
absent here too `[CERT]` (same file opened, list read in full). This list is enforced two ways: silently
dropped from `system.properties`-file loading (`Nre.java:822-825`, "Native system properties cannot be
overridden") and **fatally** if supplied via the actual OS command line (`Nre.java:875-881`,
`verifySystemProperties()`: `fatal("System properties verification failed. Native system property cannot be
overridden at command line: " + protectedNativeProperty)` when `System.getProperty("cmdline::" + key) !=
null`).

**The `cmdline::` sentinel is stamped by the NATIVE launcher, not by any Java code** — no `.java` file
anywhere in this corpus sets a `cmdline::`-prefixed property; only `Nre.java`/`SystemPropertiesUtil.java`
*read* it. `strings` on the shared native engine confirms the native side of this exact mechanism:
```
nre>   argv[%d] = "%s"
-Dcmdline::
--add-opens=java.base/java.net=niagara.nre
...
```
`[CERT-hw]` `strings /mnt/c/Program Files/Niagara/5.0.0.28/bin/nre.dll`, this session (`-Dcmdline::` literal
present, immediately following the `argv[%d]` format string used while `nre.dll`'s `buildArgs()` assembles
the JVM's `-D` option list, per the adjacent `nre>   buildArgs()`/`nre>   javaOptions[%d]` debug-trace
strings in the same dump). `station.exe`, `wb.exe`, and `n5mig.exe` carry **none** of these strings
themselves `[CERT-hw]` (`strings` on all three, zero hits for `cmdline::`, `denylist`, `blacklist`,
`skipModuleValidation`) — confirming the 4 native launchers are thin stubs sharing one engine, `nre.dll`,
which is the sole native contributor to this mechanism, and its ONLY contribution is the generic
`-Dcmdline::<key>=<value>` tagging — no property NAME is special-cased inside the native binary itself; the
entire denylist/protected-list VALUE tables live in the two Java classes above.

**Net finding, closing B23-G3:** neither of N5's two command-line-property gates — the runtime-overridable
6-entry `niagara.commandLinePropertyDenyList` or the hardcoded 27-entry
`PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` — names `niagara.classLoader.skipModuleValidation` or any other
signature/module-verification sysprop. That escape hatch remains gated only by the `developer{
skipModuleValidation=true}` license feature [B23] already documented, not by any command-line sysprop
denylist. The native launcher (`nre.dll`) supplies the generic `cmdline::` tagging infrastructure these
gates depend on, but does not itself filter by property name.

**Static-defect / runtime-exploitability split (METHODOLOGY §3):** `niagara.commandLinePropertyDenyList`
itself is read via a plain `System.getProperty(key, default)` (`Nre.java:804-807`) and is **not** a member of
either list — so a bare `-Dniagara.commandLinePropertyDenyList=` (empty) supplied on the actual OS command
line would, because `-D` flags are already live System properties before `Nre.main` runs at all, replace the
default 6-entry string with an empty one, silently disabling Gate A's own 6 protections (CSV-injection
prevention, browser URL allowlist, TLS-renegotiation rejection) regardless of `hasSystemPropsWriteAccess`.
This is a genuine self-referential gap in Gate A's design, confirmed `[CERT]` at the code level; whether it
is exploitable in practice (e.g. whether some outer layer — the native launcher, a permission check on who
may pass arbitrary `-D` flags at all — already restricts who can reach `Nre.main` with attacker-chosen `-D`
flags) is `[INFER]`, not independently confirmed this session — named child gap **B53-G3**. This does *not*
reopen `skipModuleValidation` (never a member of Gate A to begin with), only Gate A's own 6 named
protections.

## 53.3 — B30-G3 CLOSED: N5's Honeywell trust anchor is NOT a bundled keystore resource — it is the runtime's own external `cacerts` file (PKIX chain-building) PLUS a hardcoded RSA public-key pin ("TPK", format only) `[CERT]`

[B30] §30.4 found the default JDK trust store has no PKIX path to Honeywell's private root
(`jarsigner`'s own warning), and named the runtime's OWN trust mechanism —
`SecurityConstants.getTpk()`/`CoreCryptoManager` — as the unread explanation, closing the loop with [B23]
§23.7's signature gates. This session opens both classes in full.

**Negative-existence check first: no bundled keystore/truststore resource file exists inside `nre.jar`'s own
resources.** `find organized/_bin-ext/nre/resources -type f` (non-`.class` files) returns only
`META-INF/{MANIFEST.MF,module.xml,NIAGARA4.SF,NIAGARA4.RSA}` and a handful of `com/tridium/nre/jetty/rc/`
JavaScript auth helpers — **zero** `.p12`/`.jks`/`.pem`/`cacerts`-named files `[CERT]` (this session's own
`find`, both `resources/` and `vineflower/` trees checked for `nre`). The trust anchor is not a jar-bundled
resource; it is built at runtime from two other sources, both traced below.

**Mechanism 1 — PKIX chain-building against the runtime's OWN bundled `cacerts`, external to any jar:**
```
File systemTrustStoreFile = new File(System.getProperty("java.home"), systemTrustStorePath);
   // systemTrustStorePath = "lib/security/cacerts" (or "lib/security/cacerts.bcfks" under FIPS)
...
   verifyCacertsSignature(systemTrustStoreFile);
   ...
   this.systemTrustStore = new CoreTrustStore(this, this.secInfo, cacerts, SYSTEM_TRUST_STORE_NAME);
```
`[CERT]` `CoreCryptoManager.java:805-819` (`initPrivileged()`). `java.home` here is the bundled JRE N5
ships under its own install tree, distinct from whatever standalone JDK a developer's `jarsigner` resolves
against — the exact reconciliation [B30]'s `jarsigner` PKIX-path warning needed: `jarsigner` (run against
the *default* JDK's cacerts) cannot build a path to the Honeywell private root, but N5's OWN runtime loads
its OWN `cacerts` file, under its OWN `java.home`, which this session did **not** open (see Self-
verification) but which is architecturally the only remaining place the Honeywell root could be trusted
from, given resources are ruled out above — named as an explicit follow-up, **B53-G4** (confirm the root is
actually present in that file, without extracting key material).

That loaded `systemTrustStore`, plus a `userTrustStore` (`<security-dir>/cacerts`, same class,
`CoreCryptoManager.java:826-834`), feed `CertificateChainValidator.rebuildTrustAnchors()`:
```
for (IX509CertificateEntry systemCert : cryptoManager.getSystemTrustStore().getCertificateEntries())
   this.trustAnchors.add(new TrustAnchor(systemCert.getCertificate(0).getCertificate(), null));
for (IX509CertificateEntry userCert : cryptoManager.getUserTrustStore().getCertificateEntries())
   this.trustAnchors.add(new TrustAnchor(userCert.getCertificate(0).getCertificate(), null));
```
`[CERT]` `CertificateChainValidator.java:53-75`. This `Set<TrustAnchor>` is what `PKIXParameters`/
`CertPathValidator.getInstance("PKIX")` validates a jar's signer chain against (`:140-162`, `validateCertChain
(CertPath, ...)`), with revocation checking explicitly disabled (`params.setRevocationEnabled(false)`,
`:151`) — an independent `[CERT]` finding not previously logged: N5's own module-signature PKIX validation
never checks CRLs/OCSP for the code-signing chain, only for the separate TLS-CRL path
`CoreCryptoManager.java` §configureContextFactoryForCRLs already documents for server certs.

**Mechanism 2 — a hardcoded RSA public-key PIN ("TPK"), entirely independent of the PKIX/cacerts path
above, format only — no key bytes reproduced here per this task's secrets discipline:**
```
private static final byte[] TPK = new byte[]{ /* 294 bytes */ };
public static final boolean canCheckTpk() { return TPK.length != 0; }
public static void checkTpk(String className, X509Certificate cert) throws SecurityException {
   ... if (!Arrays.equals(TPK, pubBytes)) throw new SecurityException(className + " violates integrity check");
}
```
`[CERT]` `SecurityConstants.java:12-323` (array declared `:12-307`, 294 elements counted this session by
direct enumeration of the source array — count is a structural fact, not key material). The 294-byte length
and its opening 4-byte header (`SEQUENCE`, length `0x0122`) are consistent with a standard X.509
`SubjectPublicKeyInfo` DER encoding of a single **2048-bit RSA** public key (`AlgorithmIdentifier` = `1.2.
840.113549.1.1.1` rsaEncryption + NULL, then a `BIT STRING` wrapping a `SEQUENCE{modulus INTEGER, exponent
INTEGER}` sized for a 256-byte/2048-bit modulus) — **format only**, `[INFER]` for the "2048-bit RSA" reading
(derived from DER length bytes, not a key-material comparison). This matches the KEY SIZE (not identity) of
the Honeywell "Niagara4Modules Code Signing" leaf certificate [B30] §30.4 measured (`2048-bit RSA`) —
consistent with, but not proof of, TPK pinning that exact leaf's public key; a byte-for-byte (or SHA-256
fingerprint-only) identity check was deliberately not performed this session — named **B53-G5**.

`checkTpk` is a **direct equality comparison of a certificate's re-encoded `SubjectPublicKeyInfo` DER bytes
against this hardcoded constant** — not a PKIX chain, not a keystore lookup, no expiry/revocation semantics
at all. It is invoked only when `canCheckTpk()` is true (i.e. always, since the array is non-empty) AND the
caller passes `checkTpk=true`:
```
if (validated && SecurityConstants.canCheckTpk()) {
   try { SecurityConstants.checkTpk("", (X509Certificate)certPath.getCertificates().getFirst()); tpkChecked = true; }
   catch (SecurityException var7) {}
}
```
`[CERT]` `CertificateChainValidator.java:225-231` (`mapCertPath`) — note the TPK pin is checked **only after**
PKIX chain validation already succeeded (`validated == true`), i.e. it is an ADDITIONAL, stricter constraint
layered on top of the ordinary chain-trust model, not an alternative to it: a cert chain that fails PKIX
(e.g. because the runtime's `cacerts` lacked the Honeywell root) never reaches the TPK check at all.

**How `validateCertChain` ties both mechanisms together, and how both of [B23]'s gates reach
`CoreCryptoManager`:**
```
CoreCryptoManager mgr = ...CoreCryptoManagerHolder.MODULE_CORE_CRYPTO_MANAGER; // = CoreCryptoManager.get()
...
mgr.validateCertChain(signer, checkTpk);           // ModuleSetClassLoader.java:515,540 (Gate 2)
mgr.validateCertChain(signer, nModule.getCheckTpk()); // NModuleModuleFinderFactory.java:525,543 (Gate 1)
```
`[CERT]` both call sites, cross-checked against [B23] §23.7's own citations for the same two gates.
`CoreCryptoManager.validateCertChain(CodeSigner, boolean)` (`CoreCryptoManager.java:1136-1142`) rebuilds
`trustAnchors` if the user trust store changed since the last check, then delegates straight to
`this.certValidator.validateCertChain(codeSigner, checkTpk)` — the `CertificateChainValidator` instance
whose PKIX-then-TPK sequence is traced above. `[CERT]` same file.

**Net finding, closing B30-G3:** N5's trust anchor for the Honeywell code-signing chain is **not** a bundled
resource inside `nre.jar`/`baja.jar` (ruled out by direct search). It is the union of (a) whatever CA
certificates the runtime's own bundled `<java.home>/lib/security/cacerts` file contains — external to any
jar, loaded fresh at `CoreCryptoManager` init and itself integrity-checked via a detached `.sig` verified
with the SAME hardcoded TPK public key (`verifyCacertsSignature`, `CoreCryptoManager.java:928-945`) — plus
(b) an entirely separate, harder-edged mechanism: a single hardcoded 2048-bit-RSA-shaped public key
constant (`SecurityConstants.TPK`) that `checkTpk` compares a chain's leaf certificate against byte-for-byte,
gating a distinct `tpkChecked` outcome layered ON TOP OF (never instead of) ordinary PKIX chain trust.

## 53.4 — B34-G3 CLOSED: `getLicenseAccessKeyFromResponse`'s caller is a platform-daemon-protocol round trip to niagarad's `UpdateDaemonServlet`, invoked by four independent Workbench/automation call sites `[CERT]`

[B34] §34.7 traced `AuthenticatedLicenseRetrievalUtil`'s own methods in full but left its network-side
caller — `getLicenseAccessKeyFromResponse(String jsonResponse)` — unresolved, since that method only
*consumes* an already-fetched JSON string with no HTTP call site of its own. This session traces the
complete round trip on both ends.

**Client side.** The sole caller is `RemoteLicenseAccessKeyFileUtil.getRemoteLicenseAccessKey`:
```
try (InputStream inputStream = remoteSession.getInputStream(new GetLicenseAccessKeyMessage(hostId))) {
   String licenseAccessKeyJSONString = new BufferedReader(...).lines().collect(Collectors.joining("\n"));
   return AuthenticatedLicenseRetrievalUtil.getLicenseAccessKeyFromResponse(licenseAccessKeyJSONString);
}
```
`[CERT]` `RemoteLicenseAccessKeyFileUtil.java:26-40` (whole method). `remoteSession` is a `BDaemonSession` —
Niagara's **platform daemon protocol** session (the same transport Workbench's Platform Administration /
commissioning-wizard tooling uses against a remote station's `niagarad`, distinct from Fox/HTTP station
traffic). The message itself is a plain HTTP-style query string, not a bespoke binary protocol:
```
private final StringBuilder message = new StringBuilder("updatedaemon?getLicenseAccessKey=true");
public GetLicenseAccessKeyMessage(String hostId) { message.append('&').append("hostId=")... }
```
`[CERT]` `GetLicenseAccessKeyMessage.java:6-11`. `updatedaemon` is niagarad's own servlet path.

**Server side.** `UpdateDaemonServlet` (niagarad, i.e. the platform daemon HTTP service every N5 install
runs) handles exactly this query:
```
SecretChars licenseAccessKey = AuthenticatedLicenseRetrievalUtil.readLicenseAccessKey(hostId);
...
JSONObject licenseAccessKeyResponseJson = new JSONObject();
licenseAccessKeyResponseJson.put("licenseAccessKey", licenseAccessKey.asString(true));
licenseAccessKeyResponseJson.write(content, 2, 2);
```
`[CERT]` `UpdateDaemonServlet.java:648-668` — the exact `{"licenseAccessKey": "..."}` shape
`getLicenseAccessKeyFromResponse` ([B34] §34.7) parses. The sibling write path (a peer PUSHING a key,
matched to `CreateLicenseAccessKeyMessage` on the client side) is handled a few lines later:
```
String brandId = query.get("brandId", AuthenticatedLicenseRetrievalUtil.getDefaultLicenseBrandId());
...
AuthenticatedLicenseRetrievalUtil.createLicenseAccessKeyFile(hostId, brandId, version, licenseAccessKey);
```
`[CERT]` `UpdateDaemonServlet.java:684-703`. This closes the full round trip: client `GetLicenseAccessKeyMessage`
→ niagarad `UpdateDaemonServlet` GET-shaped handler → `readLicenseAccessKey` → JSON response → client
`getLicenseAccessKeyFromResponse`; and the mirror-image PUSH: client `CreateLicenseAccessKeyMessage` →
niagarad handler → `createLicenseAccessKeyFile`.

**Who calls `getRemoteLicenseAccessKey`/`updateRemoteLicenseAccessKey` — four independent, concrete sites,
spanning interactive Workbench UI AND headless provisioning automation, not "Workbench license manager UI"
alone as this task's own framing assumed:**

| Caller | Module | Context | Citation |
|---|---|---|---|
| `LicenseStep.getLicenseAccessKey` | `platDaemon` | Remote-platform **Commissioning Wizard**, license step | `LicenseStep.java:802-808` |
| `FinishPane` | `platDaemon` | Commissioning Wizard's finish step (pushes the local key to the newly-commissioned remote) | `FinishPane.java:397-400` |
| `BLicenseManager.getLicenseAccessKey` | `platDaemon` | Standalone **Platform Administration → License Manager** tool | `BLicenseManager.java:533-538` |
| `BLicenseStationExt` | `provisioningNiagara` | **Automated provisioning job step** (`BUpdateLicensesJobStep`'s network ext) — headless, fleet-wide license sync | `BLicenseStationExt.java:295-299` |

`[CERT]` all four, direct `grep`+read this session. All four gate the call behind
`session.getHostProperties().isMinNiagaraVersion(Version.N5)` (e.g. `BLicenseManager.java:534`,
`LicenseStep.java:803`) — this whole LicenseAccessKey mechanism is **N5-only**, gated off entirely for N4
remote targets, consistent with [B34] §34.8's `security/licenses/conf/<hostid>/` row finding this artifact
absent from the N4 (`niagara-research`) corpus.

**`readLicenseAccessKey`/`createLicenseAccessKeyFile`/`isLicenseAccessKeyFormatValid` (the LOCAL, non-
network methods)** have a wider caller set already partly visible in [B34] §34.7's own file list: Workbench's
`BWorkbenchLicenseTree`/`BLicensePlatformServicePlugin`/`BRequestLicenseAccessKeyDialog`/
`BLicenseTreeAccessKeyDialog` (`platform` module — the interactive "enter/view a LicenseAccessKey" UI), and
`portalApi`'s `LicenseProcedure` (the automatic self-service flow WbMain's `getLicenseFromPortal()`, §53.1,
invokes) — all `[CERT]` grep hits this session, methods not individually re-read beyond the `AuthenticatedLicenseRetrievalUtil.*`
call-site lines already shown in the search output above.

**Net finding, closing B34-G3:** `getLicenseAccessKeyFromResponse`'s one caller,
`RemoteLicenseAccessKeyFileUtil.getRemoteLicenseAccessKey`, is fed by a platform-daemon-protocol HTTP query
(`updatedaemon?getLicenseAccessKey=true&hostId=...`) answered by niagarad's `UpdateDaemonServlet`, which
itself calls straight back into `AuthenticatedLicenseRetrievalUtil.readLicenseAccessKey` on the SERVER side
— i.e. the whole mechanism is a peer-to-peer LicenseAccessKey exchange between two N5 installs' own
`nre.jar` copies over the platform daemon channel, invoked from four call sites: two Commissioning-Wizard
steps, one standalone License Manager tool, and one headless provisioning job step — not a single UI
workflow.

## 53.5 — Connections

- **[Block 17]** — §53.1 closes **B17-G2** at the source level, replacing the block's own "narrowed, not
  fully closed" verdict with an exact two-entry allowlist and a full explanation of `wb.exe`'s later,
  UI-mediated re-check of the identical feature.
- **[Block 23]** — §53.2 closes **B23-G3**: neither sysprop gate names `skipModuleValidation`. §53.3 closes
  the trust-anchor half of §23.7's `SecurityConstants.getTpk()`/`CoreCryptoManager` citation, and
  independently confirms both of §23.7's signature gates call the exact same `CoreCryptoManager.get().
  validateCertChain(...)` this block traces end-to-end.
- **[Block 30]** — §53.3 closes **B30-G3**, reconciling §30.4's `jarsigner` PKIX-path-building failure
  (default JDK cacerts) against N5's OWN runtime `cacerts` (different file, same mechanism) plus the
  independent TPK pin; the 2048-bit RSA key-size match to §30.4's leaf certificate is noted as consistent
  but unproven identity (**B53-G5**).
- **[Block 34]** — §53.4 closes **B34-G3**, and additionally surfaces that this whole mechanism is gated
  `isMinNiagaraVersion(Version.N5)`-only, corroborating §34.8's independent N5-only finding for the
  `security/licenses/conf/<hostid>/` artifact itself.

## 53.6 — Child gaps

- **B53-G1** — Live confirmation, on an actually-licensed N5 station, that a real (non-`-help`) `wb.exe`
  launch reaches `doCheckLicense()` and correctly shows the license-error dialog (vs. proceeding normally)
  under the SAME license state that fails `n5mig.exe`/`station.exe` — requires-execution, `[CERT-hw]`, needs
  a licensed or deliberately-unlicensed test install this session did not have.
- **B53-G2** — Trace `portalApi:com.tridium.portal.util.LicenseDownload` (the SECOND `shouldCheckNreLicense`
  allowlist entry, §53.1) — not opened this session; likely a lower-level license-bootstrap utility distinct
  from `LicenseProcedure` (the class WbMain's `getLicenseFromPortal()` actually calls), possibly used by a
  non-Workbench (headless/CLI) license-download path.
- **B53-G3** — Confirm whether anything upstream of `Nre.main` (native launcher argument filtering, an OS-
  level permission boundary) prevents an unprivileged local user from supplying arbitrary `-D` flags
  (including `-Dniagara.commandLinePropertyDenyList=`) to `n5mig.exe`/`station.exe`/`wb.exe` in the first
  place — the self-referential Gate-A bypass noted in §53.2 is a static `[CERT]` code fact; its runtime
  exploitability is `[INFER]`, unconfirmed.
- **B53-G4** — Confirm the runtime's own `<java.home>/lib/security/cacerts` (or `.bcfks` under FIPS)
  actually contains the Honeywell `Product PKI RSA` root as a trusted CA entry — deliberately NOT opened
  this session (secrets discipline: this file lives under a `security/` path); a future pass with explicit
  authorization to inspect alias/subject METADATA ONLY (e.g. `keytool -list`, never exporting a key) could
  close this without violating the no-key-material rule.
- **B53-G5** — A byte-for-byte (or SHA-256-fingerprint-only) identity check between the hardcoded `TPK`
  constant (`SecurityConstants.java`) and the Honeywell "Niagara4Modules Code Signing" leaf certificate's
  public key [B30] §30.4 measured — both are 2048-bit RSA (consistent), but identity was not verified this
  session, and was deliberately not attempted here given the secrets-discipline scope of this block.
- **B53-G6** — `NModuleModuleFinderFactory.CoreCryptoManagerHolder.TRIDIUM_DEV_CA_CERT` (`NModuleModuleFinderFactory.java:654-656`,
  used for an `isCoreFrameworkModule` public-key comparison) is a THIRD, separate hardcoded-cert holder
  spotted in passing this session, distinct from both the TPK pin and the PKIX trust-anchor set — not traced
  beyond its field name; out of this block's scope.

## Self-verification

**Token check:** every `file:line` citation in §53.1–§53.4 points into files already organized in this
corpus's `vineflower/` trees (no fresh decompilation this session); every citation was `grep`-confirmed
present at or adjacent to the stated line while drafting (batch `grep -n` runs shown inline above for the
multi-hit searches; single-hit citations — e.g. `SystemPropertiesUtil.java`, `GetLicenseAccessKeyMessage.java`
— were read whole-file, so location is exact by construction). No citation in this block points into a
scratch-temp decompiled path, so this is NOT the "decompiled-tree" zero-resolved case METHODOLOGY §11
describes — these are ordinary `organized/` corpus files, though `verify-block.sh` is still not installed in
this corpus (same disclosed absence [B17]/[B23] noted), so resolution below is a manual re-grep, not a tool
run.

**Manual re-grep spot-check (5 of the highest-load-bearing citations, this session, immediately before
closing the block):**
- `Nre.java:469` — `shouldCheckNreLicense` declaration — present.
- `Nre.java:498` — `runClass` gate call — present.
- `SystemPropertiesUtil.java:19` — `PROTECTED_NATIVE_SYSTEM_PROPERTIES_LIST` declaration — present.
- `CertificateChainValidator.java:125` — `validateCertChain(CodeSigner, boolean)` — present.
- `RemoteLicenseAccessKeyFileUtil.java:33` — `getLicenseAccessKeyFromResponse` call — present.
All 5 re-confirmed by direct `grep -n` immediately before this section was written; none absent.

**Marker tally (manual count — no `toolbelt/verify-block.sh` in this corpus, same disclosed absence as
[B17]/[B23]):** `[CERT]` 46 (every numbered code-block citation + table cell across §53.1–§53.4, including the
5 re-verified above) · `[CERT-hw]` 4 (the `nre.dll`/`station.exe`/`wb.exe`/`n5mig.exe` `strings` runs, §53.2) ·
`[INFER]` 4 (§53.3's "2048-bit RSA" DER-structure reading, §53.3's TPK↔leaf key-size-match observation,
§53.2's Gate-A self-bypass exploitability note, §53.4's "not traced beyond field name" TRIDIUM_DEV_CA_CERT
aside). Ratio `[INFER]`/`[CERT]` ≈ 0.09 — consistent with a `mixed`-declared, evidence-dominant block: every
one of the four target gaps was closed by direct source reading, not deduction, and the `[INFER]`s present
are narrow, explicitly-scoped readings (a DER length interpretation) or explicitly-named follow-up
questions, not load-bearing conclusions resting on inference.

**Artifacts:** block file at `/home/cristian/niagara5-research/niagara5-block53.md`. No scratch/output
directories created this session (no execution, no fresh decompilation — pure reading of already-organized
sources plus 4 `strings` invocations against read-only native binaries). `CATALOG.md`/`INDEX.md`/
`RESEARCH-STATE.md` **NOT** regenerated this run — left to the orchestrator/next session, same disclosed
choice [B17]/[B23]/[B30] made.

**MCP-doc snapshots:** N/A — no MCP/web fetch used this session; all sources are local corpus files and
local native binaries.

**Secrets discipline (this task's own requirement, stricter than METHODOLOGY's general rule):** no key
material was extracted, printed, or reproduced anywhere in this block. §53.3 reports the hardcoded TPK
constant's BYTE COUNT (294) and DER STRUCTURE (SubjectPublicKeyInfo header shape implying 2048-bit RSA) —
format facts, not key values — and explicitly declines the one comparison (§53.3, B53-G5) that would require
handling actual key bytes. No file under a path containing a `security/` or `licenses/` directory segment
that holds LIVE credential/keystore/license DATA was opened this session: the `<java.home>/lib/security/
cacerts` file itself was explicitly named as unread evidence (B53-G4) rather than opened, and
`security/licenses/conf/<hostid>/`'s actual `licenseInfo.xml` content (already out of scope — [B34] §34.7
covered its format, not its live values) was not touched. The files this block DOES cite under `.../
security/...`-named PACKAGE paths (e.g. `com/tridium/nre/security/SecurityConstants.java`,
`com/tridium/crypto/core/io/CoreCryptoManager.java`) are decompiled JAVA SOURCE CODE — Niagara's own package
naming convention, not a live credential-storage directory — and were already present in this corpus's
`organized/` tree from prior sessions' decompilation, not freshly extracted from a live/licensed install
this session.
