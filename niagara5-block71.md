# Block 71 — Closing the licensing/subscription/portalApi cluster: the dead `LicenseDownload` `Nre.runClass` exemption, the backup-restoration re-registration write site, the LicenseAccessKey Workbench UI, the N4 client-package location, and the Niagara Sync / Niagara Cloud licensing split

> Research closing five named child gaps across the N5 licensing/subscription/portalApi cluster:
> **B53-G2** (trace `portalApi:com.tridium.portal.util.LicenseDownload`, [Block 53] §53.1's second
> `shouldCheckNreLicense` allowlist entry — not opened in that session); **B34-G1** (the write site for
> `registration.metadata.reregistrationCause="backup-restoration"`, [Block 34] §34.3's own explicit
> "not traced this session" gap); **B34-G4** ([Block 34] §34.7's "not independently confirmed against a
> UI/caller this session" gap — which Workbench UI actually consumes the `AuthenticatedLicenseRetrievalUtil`
> LicenseAccessKey flow, beyond the four call sites [Block 53] §53.4 already named but did not individually
> re-open); **B34-G5** ([Block 34] §34.8's table row — whether N4's `nre.jar` has its own
> `com.tridium.nre.subscription`-equivalent client-transport package, not settled because the `niagara-research`
> N4 corpus never independently decompiled N4's `nre.jar`); and **B56-G2** ([Block 56] §56.5's flagged
> naming-adjacency risk — whether "Niagara Sync" and "Niagara Recover"/Niagara Cloud Suite share any
> licensing/rollout coupling, or are independently gated). Covers: `Nre.java`'s `runClass` method body past
> the `shouldCheckNreLicense` gate (the `nreMain` reflection contract) cross-read against `LicenseDownload.java`'s
> full method set; `EntitlementUtil.java`'s `REREGISTRATION_CAUSE_*` constants and their write/read sites across
> `RegistrationApi.java` and niagarad's `UpdateDaemonServlet.java`, traced back to the platDaemon Distribution
> Installer wizard (`FinishDistInstall.java`) and its `ResetRestoreParametersMessage`; the four
> `AuthenticatedLicenseRetrievalUtil` UI consumers named by [Block 53] §53.4
> (`BWorkbenchLicenseTree`/`BLicensePlatformServicePlugin`/`BLicenseTreeAccessKeyDialog`/
> `BRequestLicenseAccessKeyDialog`), now individually opened; a direct grep of the N4 `niagara-research` corpus
> for `com.tridium.nre.*` packages, plus a fresh read of N4's own `SubscriptionLicenseManager.java` (`baja.jar`,
> `com.tridium.sys.license.subscription`) for its own import statements; and the license-feature-gating call
> sites inside N5's `niagaraSync` and `niagaraCloud` modules (`BNiagaraSyncService.java`,
> `BNiagaraCloudSideBar.java`) plus the `niagaraCloud` module's own shipped lexicon string. Does **not**
> cover: live confirmation of any of this on a running station (all `[CERT]`, source-level only, this
> session); decompiling N4's actual `nre.jar` bytes (the N4 corpus was only grepped/cross-referenced, not
> newly decompiled — no N4 decompilation performed this session, per this task's N5-corpus scope); the full
> `PortalLicenseUtil.getPortalUpdates()` HTTP call itself (its call sites were read, its own body was not
> opened this session); the `niagara-remote-client-1.0.5` bundled library found alongside the `niagaraCloud`
> cluster during search (named only, not opened — see child gap).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 6]/[Block 34]/[Block 53]/[Block 56] read; decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{baja,portalApi,platform,platDaemon,_bin-ext/nre,
> _bin-ext/niagarad,niagaraSync,niagaraCloud}/vineflower/`. The N4 comparator (B34-G5) is the sibling
> `niagara-research` corpus at `/home/cristian/niagara-research/organized/baja/baja/vineflower/` — an
> already-existing decompiled tree, cross-referenced/grepped this session, not freshly decompiled.
>
> Sources: `organized/baja/vineflower/com/tridium/sys/Nre.java:469-477` (`shouldCheckNreLicense`, re-read
> from [Block 53] §53.1's own citation), `:498-545` (`runClass`, whole method, fresh this session — the
> reflection/`nreMain` contract half [Block 53] did not trace);
> `organized/portalApi/vineflower/com/tridium/portal/util/LicenseDownload.java` (whole file, 78 lines, never
> previously opened in this corpus); `organized/portalApi/vineflower/com/tridium/portal/wb/LicenseProcedure.java`
> (targeted reads: `:90-160` construction flow, `:774-1058` `RequestLicenseAccessKey`/`ShowUserCode` steps);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/DeviceCodeApi.java` (whole file, 96 lines);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementUtil.java:1-60` (constants
> block); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:547-559`
> (`resetRestoreParameters` handler, new range — [Block 53] §53.4 read `:620-710`, a disjoint range in the
> same file); `organized/platform/vineflower/com/tridium/platform/daemon/message/ResetRestoreParametersMessage.java`
> (whole file, 12 lines); `organized/platDaemon/vineflower/com/tridium/platDaemon/ui/distinstall/FinishDistInstall.java:1-40,250-300`
> (imports + finish-step body, targeted read); `organized/platform/vineflower/com/tridium/platform/ui/license/BWorkbenchLicenseTree.java:550-792`
> (`SyncOnline` inner class, whole); `organized/platform/vineflower/com/tridium/platform/ui/license/BLicensePlatformServicePlugin.java:826-930`
> (`ImportCommand`, targeted); `organized/platform/vineflower/com/tridium/platform/ui/license/auth/BLicenseTreeAccessKeyDialog.java`
> (whole file, 271 lines); `organized/platform/vineflower/com/tridium/platform/ui/license/auth/BRequestLicenseAccessKeyDialog.java`
> (whole file, 217 lines); `/home/cristian/niagara-research/organized/baja/baja/vineflower/com/tridium/sys/license/subscription/SubscriptionLicenseManager.java:1-20`
> (import block, N4 corpus, cross-repo read this session); `organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:287`
> (re-read from [Block 37] §37.7's citation); `organized/niagaraCloud/vineflower/com/tridium/niagaraCloud/sidebar/BNiagaraCloudSideBar.java:140-165`;
> `organized/niagaraCloud/vineflower/niagaraCloud.lexicon:32`.
>
> Method: whole-file/targeted reading of already-decompiled Vineflower sources (no fresh decompilation this
> session — every N5 file read was already present in `organized/` from prior blocks or newly extracted by
> those blocks' own tooling) + `grep`-driven caller/write-site tracing across module boundaries within the N5
> corpus + one cross-repository `grep`/targeted-read against the SIBLING N4 corpus (`niagara-research`,
> already-decompiled, not touched or modified this session). Markers (canonical list: METHODOLOGY §3):
> `[CERT-hw]` verified against the live system/device — highest · `[CERT-live]` verified against a live
> remote service you don't own · `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official
> downloaded document · `[CERT-web]` official web (URL + date) · `[CERT-a]` secondary source/forum (URL) ·
> `[INFER]` deduction. SECRETS DISCIPLINE: this block cites the STRUCTURE of one hardcoded OAuth
> `client_id`-shaped constant (`EntitlementUtil.DEVICE_REGISTRATION_CLIENT_ID`) by name, length-class, and
> format only (a Salesforce Connected-App consumer-key-shaped string) — its literal value is never
> reproduced here, consistent with [Block 6]/[Block 34]/[Block 53]'s own key/cert discipline.
>
> Security/licensing layer. Connects [Block 53] (closes B53-G2), [Block 34] (closes B34-G1/B34-G4/B34-G5),
> [Block 56] (closes B56-G2), [Block 6] (§6.11's `com.tridium.sys.license.subscription` re-cited for the N4
> side), [Block 37] (§37.7's `tridium:niagaraSync` re-cited), [Block 48] (§48.8's "Niagara Recover"/Premium
> Workbench framing, now tied to a concrete license-feature string).
>
> **Type:** `mixed` — each section closes a prior block's evidence gap with fresh `[CERT]` `file:line`
> reading (evidence half), and §71.2/§71.5 draw a synthesis conclusion across newly-read files plus prior
> blocks' own findings (synthesis half), per METHODOLOGY §11's MIXED trigger.

---

## 71.1 — B53-G2 CLOSED: `portalApi:com.tridium.portal.util.LicenseDownload` is a launch target that CANNOT actually launch — it has no `nreMain` method — so its `shouldCheckNreLicense` exemption is dead code; the real self-service license-download flow is `LicenseProcedure`, riding the FIRST (`WbMain`) exemption `[CERT]`

[Block 53] §53.1 found the exact two-entry allowlist inside `Nre.java:469-477` but did not open
`portalApi.LicenseDownload` itself, framing it as "likely a lower-level license-bootstrap utility... possibly
used by a non-Workbench (headless/CLI) license-download path." This session opens it and finds the opposite:
it is not a launchable entry point at all.

**What `Nre.runClass` requires of any launch target, past the license check:**
```java
static void runClass(NModule module, String className, String[] nreMainArgs) {
   if (shouldCheckNreLicense(module, className)) {
      licenseManager.checkFeature("tridium", "nre");
   }
   Class<?> cls = ...;   // module.loadClass(className) or Class.forName(className)
   Method nreMain = null;
   try {
      nreMain = cls.getMethod("nreMain", new Class[]{String[].class});
      if (!nreMain.getReturnType().equals(void.class)) fatal("FATAL: nreMain must return void: " + className);
      if (!Modifier.isPublic(nreMain.getModifiers())) fatal("FATAL: nreMain must be public: " + className);
      if (!Modifier.isStatic(nreMain.getModifiers())) fatal("FATAL: nreMain must be static: " + className);
   } catch (Exception exception) {
      fatal("FATAL: No nreMain: " + className);
   }
   nreMain.invoke(null, new Object[]{nreMainArgs});
   ...
```
`[CERT]` `Nre.java:498-539` (whole method, this session) — the license check is gated by
`shouldCheckNreLicense`, but the ABILITY TO LAUNCH AT ALL is gated by a SEPARATE, unconditional reflection
requirement: the target class MUST expose a `public static void nreMain(String[])` method, or `runClass`
calls `fatal(...)` (which terminates the process) regardless of whether the license check was skipped.

**`LicenseDownload.java`'s complete method inventory — no `nreMain`, no `main`, not even an instance
constructor a caller could reach (it is `final` with a `private` no-arg constructor):**
```java
public final class LicenseDownload {
   private LicenseDownload() { }                                            // :17-18
   public static void copyLicenses(XElem[] licenses) throws Exception { }   // :20-30
   public static void copyCertificates(XElem[] certificates) throws Exception { } // :33-43
   private static String getFilePrefix(XElem license) { }                  // :46-56
   public static String[] licenseToVendors(XElem[] licenseElems) { }       // :59-70
   private static void validateVendor(String vendor) { }                  // :73-77
}
```
`[CERT]` `LicenseDownload.java:13-78` (whole file, this session; class declaration `:13`, constructor `:17`,
each method's own line cited above). Every method is either `private` or a narrow static file-I/O helper
(write an `XElem` to a `.license`/`.certificate` file under `NiagaraFiles.getPerpetualLicensePath()` /
`getPerpetualCertificatesPath()`, or extract a `vendor`/`brandId` string from parsed license XML). None
matches the `public static void nreMain(String[])` signature `runClass` requires.

**Net finding:** if `Nre.runClass` were ever invoked with `module="portalApi"`,
`className="com.tridium.portal.util.LicenseDownload"` — the exact literal pair its own allowlist entry
names (`Nre.java:473`) — it would pass the license-check exemption cleanly, successfully `Class.forName`
the class (it exists, is public, is on the classpath), and then hit `cls.getMethod("nreMain", ...)`, which
throws `NoSuchMethodException` (caught by the generic `catch (Exception exception)` at `:530-532`), landing
on `fatal("FATAL: No nreMain: com.tridium.portal.util.LicenseDownload")` — an unconditional process-fatal
error, independent of license state. `[CERT]` — this is a STATIC-STRUCTURE finding (the method set is fixed
and directly read), not a runtime trace; no execution was performed this session, so whether some OTHER,
not-yet-found `LicenseDownload`-named class exists elsewhere on the classpath and shadows this one is not
ruled out (`module.loadClass` resolves within the `portalApi` module's own classloader, and only one
`portalApi.vineflower` tree exists in this corpus) — `[INFER]`, low-risk, named **B71-G1**.

**Where `LicenseDownload` IS actually used — confirming [Block 53] §53.4's own cross-reference, closing the
loop:** its three real callers are all inside `LicenseProcedure.java` — `licenseToVendors()` at `:481,555`
and `copyLicenses()`/`copyCertificates()` at `:735-736` — invoked from within `LicenseProcedure`'s own
license-installation step, itself constructible only from `WbMain`'s already-exempt Workbench boot path
(the FIRST allowlist entry, `Nre.java:470-472`). `[CERT]` `LicenseProcedure.java:481,555,735-736`, direct
grep+read this session (already listed by name, not individually re-opened, in [Block 53] §53.4's own
"Local, non-network methods" paragraph — now confirmed as `LicenseDownload`'s ONLY real call sites in the
corpus, per the earlier corpus-wide grep in this session's own tooling).

**Closing B53-G2:** the second `shouldCheckNreLicense` allowlist entry does not name a genuine alternate
headless/CLI launch path, as [Block 53] §53.1 speculated — it names a class that is architecturally
incapable of being an `Nre` launch target in this build (no `nreMain`). `LicenseProcedure` — the real
self-service "download a license from the portal" wizard, using `LicenseDownload` purely as an internal
file-write utility — is reachable only through the WbMain-hosted Workbench UI, i.e. through the FIRST
allowlist entry, not the second. The second entry is either (a) dead/vestigial code (a class that was once
launchable and lost its `nreMain` in a refactor, or was drafted as a launch target and never finished), or
(b) a defensive allowlist entry added in anticipation of a future headless launcher that does not exist in
this beta build. `[INFER]` on which of (a)/(b) — no changelog or comment in `Nre.java` states an intent;
both readings are consistent with the same static evidence — named **B71-G2**, not required to resolve the
security question (either way, this exemption grants no REACHABLE unlicensed capability in the current
build, since the class cannot successfully launch at all).

## 71.2 — B34-G1 CLOSED: `reregistrationCause="backup-restoration"` is written by niagarad's `UpdateDaemonServlet` handling a `resetRestoreParameters` platform-daemon message, sent by the platDaemon Distribution Installer wizard's finish step when restoring a subscription-licensed station from a `.dist` backup `[CERT]`

[Block 34] §34.3 found `RegistrationApi.java:132-135` READING
`SubscriptionMetadataUtil.getRegistrationMetadata("reregistrationCause")` but explicitly stated "Neither
write site for `reregistrationCause` was found in this package... not traced this session." A corpus-wide
grep this session (not scoped to `com.tridium.nre.subscription`, per [Block 34]'s own framing of the gap as
"a caller outside" that package) finds it immediately.

**The constants themselves live in `nre.jar`, alongside the reader, but the WRITE happens in a different
jar entirely:**
```java
public static final String REREGISTRATION_CAUSE_METADATA_KEY = "reregistrationCause";  // :54
public static final String REREGISTRATION_CAUSE_BACKUP = "backup-restoration";          // :55
public static final String REREGISTRATION_CAUSE_REPLACEMENT = "device-replacement";     // :56
```
`[CERT]` `EntitlementUtil.java:54-56` (`com.tridium.nre.subscription`, `nre.jar` — the same jar/package
[Block 34] already fully scoped). These constants are declared here but the literal STRING `"backup-restoration"`
(not the constant reference) is what actually appears at the one write site found:

```java
// UpdateDaemonServlet.java, inside the "resetRestoreParameters" query handler:
if (query.containsKey("resetRestoreParameters")) {
   ...
   try {
      SubscriptionLicenseUtil.removeRestoreParameters();
      SubscriptionMetadataUtil.addRegistrationMetadata("reregistrationCause", "backup-restoration");
      SubscriptionMetadataUtil.addRegistrationMetadata("previousNreId", this.platformProvider.getHostId());
   } catch (IOException e) { ... }
```
`[CERT]` `UpdateDaemonServlet.java:547,557-558` (`com.tridium.niagarad.servlet`, the `_bin-ext/niagarad`
module — niagarad, the platform daemon HTTP service, the SAME class [Block 53] §53.4 already traced for the
`getLicenseAccessKey`/`createLicenseAccessKey` query actions at lines `620-710`; this write sits at a
disjoint, previously-unread range in the same file). Note the literal string is used directly rather than the
`EntitlementUtil.REREGISTRATION_CAUSE_BACKUP` constant — `[CERT]`, a minor internal inconsistency (same
value, different jar, no shared constant reference across the `nre.jar`/`niagarad` module boundary), not a
functional difference.

**The client-side trigger — who sends the `resetRestoreParameters` platform-daemon query:**
```java
public class ResetRestoreParametersMessage extends XmlResponseMessage {
   public String getMessageString() { return "updatedaemon?resetRestoreParameters=true"; }  // :5-7
   public boolean isStateChangeMessage() { return true; }
}
```
`[CERT]` `ResetRestoreParametersMessage.java:1-12` (whole file, `com.tridium.platform.daemon.message`) — the
same `updatedaemon?...` query-string shape [Block 53] §53.4 already documented for
`GetLicenseAccessKeyMessage`, confirming this is the SAME platform-daemon-protocol channel, a different
query action. Its one sender:
```java
if (this.getWizardModel().getSession().getHostProperties().getHostIdSettings().getLicenseMode() == LicenseMode.SUBSCRIPTION) {
   this.getLog().append(LEX.getText("DistInstaller.FinishDistInstall.resetSubscriptionParameters"));
   this.getWizardModel().getSession().sendMessage(new ResetRestoreParametersMessage());
}
```
`[CERT]` `FinishDistInstall.java:280-283` — the FINISH step of the **platDaemon Distribution Installer**
wizard (`com.tridium.platDaemon.ui.distinstall`), gated by `LicenseMode.SUBSCRIPTION` (skipped entirely for
a perpetual-license target). The lexicon key's own name — `DistInstaller.FinishDistInstall.resetSubscriptionParameters`
— and the class's own package name (`distinstall`) both independently corroborate this is the
"install/restore a distribution image (backup) onto a station" wizard, not any subscription-specific UI.
`[CERT]` naming evidence, same file.

**Net finding, closing B34-G1:** the write site is `UpdateDaemonServlet.java:557` on the SERVER (niagarad)
side; the trigger is the Distribution Installer wizard's finish step calling `sendMessage(new
ResetRestoreParametersMessage())` on the CLIENT (Workbench/platDaemon UI) side, gated on the target
station's license mode being SUBSCRIPTION. The causal story: restoring a subscription-licensed station from
a `.dist` backup (which would otherwise carry the OLD instance's now-stale subscription cache state) triggers
a server-side "reset restore parameters" step that (a) deletes stale restore-related state
(`SubscriptionLicenseUtil.removeRestoreParameters()`, not independently opened this session — its own
internals are a narrower follow-up, not needed to close THIS gap) and (b) flags the metadata cause as
`"backup-restoration"` plus records the PRE-restore Host ID (`previousNreId`) — precisely the two fields
[Block 34] §34.3 found `RegistrationApi.registerApi()` reading on the NEXT registration attempt to include a
`refreshIncrement` in its request body. `[CERT]` full chain, this session.

## 71.3 — B34-G4 CLOSED: all four named Workbench UI consumers of `AuthenticatedLicenseRetrievalUtil` are real, working call sites — `BWorkbenchLicenseTree`'s "Sync Online" tree command and `BLicensePlatformServicePlugin`'s "Import" command both prompt for a LicenseAccessKey via dedicated dialogs when one is missing, then feed it into `PortalLicenseUtil.getPortalUpdates()` `[CERT]`

[Block 34] §34.7 named the class's permission gate (`GET_LICENSE_ACCESS_KEY_PERMISSION`) as "likely backing a
Workbench 'download my license using an access key' flow... not independently confirmed against a
UI/caller this session." [Block 53] §53.4 then named four concrete file locations but stated they were "not
individually re-read beyond the... call-site lines already shown." This session opens all four.

**`BWorkbenchLicenseTree`'s "Sync Online" tree command** — the standalone Workbench License-tree view's bulk
license-refresh action:
```java
private class SyncOnline extends AsyncCommand {              // :550
   public void doInvokeAsync() {
      ...
      if (!hostIdWithoutLicenseAccessKeyMap.isEmpty()) {
         this.showLicenseAccessKeyDialog(hostIdWithLicenseAccessKeyMap, hostIdWithoutLicenseAccessKeyMap);  // :588
      }
      ...
      for (VendorLicense update : PortalLicenseUtil.getPortalUpdates(
         (BEnvLicenseSummary[])ArrayUtil.arrayFromCollection(pending, ...), hostIdWithLicenseAccessKeyMap
      )) { ... }                                              // :610-612
```
`[CERT]` `BWorkbenchLicenseTree.java:550-792` (whole inner class, this session). `showLicenseAccessKeyDialog`
(`:785-792`) opens `BLicenseTreeAccessKeyDialog.open(...)` (`:786`) for every selected host lacking a cached
key; the dialog collects one text field per missing host and calls
`AuthenticatedLicenseRetrievalUtil.createLicenseAccessKeyFile(hostId, brandId, requiredLicenseVersion,
licenseAccessKey)` on confirm (`BLicenseTreeAccessKeyDialog.java:218`, whole 271-line file read this
session), after validating the format with `isLicenseAccessKeyFormatValid()` (`:204`). The collected keys
then feed directly into `PortalLicenseUtil.getPortalUpdates(...)` (`:610-612,618`) — the actual
license/certificate sync call.

**`BLicensePlatformServicePlugin`'s "Import" command** — the per-station License Manager plugin's file-import
flow:
```java
private class ImportCommand extends AsyncCommand {          // :826
   ...
   if (AuthenticatedLicenseRetrievalUtil.getLicenseAccessKeyFile(BLicensePlatformServicePlugin.this.hostId).exists()) {
      ... AuthenticatedLicenseRetrievalUtil.readLicenseAccessKey(...)   // :908,918
   } else {
      BRequestLicenseAccessKeyDialog.open(...)                          // :885
   }
```
`[CERT]` `BLicensePlatformServicePlugin.java:826-930` (targeted read, this session) — if a key is already
cached for the target host, it is read directly (`readLicenseAccessKey`); if not, `BRequestLicenseAccessKeyDialog`
is opened, which validates and writes a NEW key via `createLicenseAccessKeyFile()` at two of its own call
sites (`BRequestLicenseAccessKeyDialog.java:156,171`, whole 217-line file read this session) after format
validation (`:144`).

**Net finding, closing B34-G4:** both dialogs are genuine, currently-wired UI — not dead code, not
speculative. `BLicenseTreeAccessKeyDialog` is the BULK variant (multiple hosts at once, used by the
tree-wide "Sync Online" command), and `BRequestLicenseAccessKeyDialog` is the SINGLE-host variant (used by
the per-station License Manager plugin's Import flow) — two separate dialog classes for the two separate UI
entry points [Block 53] §53.4's table already distinguished ("Standalone Platform Administration → License
Manager tool" row vs. the tree-wide sync), both registered as first-class types in `platform`'s own
`module.xml` (`:291-292`, `[CERT]` — `LicenseTreeAccessKeyDialog`/`RequestLicenseAccessKeyDialog`). In both
paths the access key, once obtained (cached-read or freshly entered), is what makes the subsequent
`PortalLicenseUtil.getPortalUpdates()` call an AUTHENTICATED per-host portal license/certificate sync — the
"perpetual-license, authenticated-retrieval" mechanism [Block 34] §34.7 characterized correctly by structure,
now confirmed end-to-end from UI to file cache. `PortalLicenseUtil.getPortalUpdates()`'s own HTTP body was
not opened this session (out of scope for closing B34-G4 specifically) — named **B71-G3**.

## 71.4 — B34-G5 CLOSED: N4's own decompiled `baja.jar` IMPORTS `com.tridium.nre.subscription` by fully-qualified name — the package is NOT N5-new at the API level, only its physical jar location within the N4 build was never independently decompiled by the `niagara-research` corpus `[CERT]`/`[INFER]`

[Block 34] §34.8's comparison table left this row `[INFER]` — "not settled" — because N4's `nre.jar`
internals were never independently decompiled by the `niagara-research` corpus. This session does not
decompile anything new; it greps the EXISTING N4 corpus, which turns out to already contain conclusive
IMPORT evidence.

**A corpus-wide grep for `package com.tridium.nre` across the entire `niagara-research` (N4) `organized/`
tree returns ZERO hits** `[CERT]` (negative-existence claim over the full corpus tree, this session,
matching METHODOLOGY §3's symmetric-opening-obligation rule — the whole tree was grepped, not a subset). N4's
own decompiled corpus has never organized an `nre.jar`-rooted tree at all (no `organized/_bin-ext/nre/`-style
directory exists for N4, unlike N5's).

**But N4's ALREADY-decompiled `baja.jar` class directly imports the N5-side package by name:**
```java
package com.tridium.sys.license.subscription;
...
import com.tridium.nre.subscription.RetrieveEntitlements;                       // :10
import com.tridium.nre.subscription.EntitlementApi.EntitlementState;            // :13
import com.tridium.nre.subscription.EntitlementApi.EntitlementStatus;           // :14

public final class SubscriptionLicenseManager extends NLicenseManager {        // :54
```
`[CERT]` `/home/cristian/niagara-research/organized/baja/baja/vineflower/com/tridium/sys/license/subscription/SubscriptionLicenseManager.java:1-54`
(N4 corpus, cross-repository read this session) — this is the SAME class [Block 6] §6.11 already documented
(package unchanged N4→N5, per [Block 6] §6.2's correction that `com.tridium.sys.license.subscription` is not
N5-new) and the SAME class [Block 34] §34.3 already cited for its N5-side behavior. Its N4-decompiled form
IMPORTS `com.tridium.nre.subscription.RetrieveEntitlements`/`EntitlementApi` — proving these classes existed,
under this EXACT package name, in WHATEVER jar N4's `SubscriptionLicenseManager` was compiled against.
`[CERT]` — an import statement in decompiled bytecode is definitive for "this FQCN existed at N4's compile
time," independent of whether that jar was itself ever decompiled.

**What this settles and what it does not:**
- **SETTLED, `[CERT]`:** `com.tridium.nre.subscription` (or at minimum its `RetrieveEntitlements` and
  `EntitlementApi` members) is NOT an N5-introduced package at the API-surface level — N4 already compiled
  against the identical fully-qualified names. This directly extends [Block 6] §6.2's "not new to N5" finding
  (which covered `com.tridium.sys.license.subscription`, the `baja.jar` CONSUMER package) to the `nre.jar`-side
  CLIENT-TRANSPORT package as well.
- **NOT independently settled this session, `[INFER]`:** whether N4's copy lives in a jar literally named
  `nre.jar` (matching N5's), a differently-named jar, or an entirely different physical module — the import
  statement proves the PACKAGE existed, not its packaging. Named **B71-G4**.
- **Also not settled:** whether N4's `com.tridium.nre.subscription.RetrieveEntitlements`/`EntitlementApi` are
  BYTE-IDENTICAL to N5's, evolved, or merely name-compatible stubs — no N4-side decompilation of those
  specific classes was performed (only the N4-side CALLER, `SubscriptionLicenseManager`, was read, and only
  its import block). `[INFER]`, named **B71-G5** — would require decompiling N4's actual `nre.jar` (or
  equivalent), out of this block's N5-corpus scope.

**Net finding, closing B34-G5 with a corrected verdict:** [Block 34] §34.8's table framed this as "does
`com.tridium.nre.subscription` exist in N4's `nre.jar`?" — an existence question. The answer is **YES**, at
the package/import level, settled without any new decompilation, purely by reading evidence the N4 corpus
already contained. The residual uncertainty (B71-G4/B71-G5) is narrower than the original gap: not WHETHER,
but WHERE (jar) and HOW MUCH CHANGED (byte-level diff).

## 71.5 — B56-G2 CLOSED: "Niagara Sync" (`tridium:niagaraSync`) and the Niagara Cloud sidebar's "Niagara Remote" feature (`tridium:premiumWBNiagaraRemote`) are gated by two DISTINCT, independently-checked license-feature strings in two DISTINCT modules — no shared feature, permission, or module coupling found `[CERT]`

[Block 56] §56.5 flagged, as an unresolved naming-adjacency risk, whether "Niagara Sync" (on-station
replication, [Block 37]) and "Niagara Recover"/Niagara Cloud Suite (cloud-hosted, [Block 48] §48.8) are
licensed/bundled together, or purely coincidentally described using similar FAQ hedging language. This
session reads both gates directly.

**`niagaraSync`'s own gate, re-confirmed (already `[CERT]`-sealed by [Block 37] §37.7, re-opened this
session at the same line for direct side-by-side comparison, not re-derived):**
```java
return Sys.getLicenseManager().getFeature("tridium", "niagaraSync");
```
`[CERT]` `BNiagaraSyncService.java:287` — feature string is the literal `"niagaraSync"`, module is
`niagaraSync` (`com.tridium.niagaraSync`, per this file's own package declaration and [Block 37]'s prior
read).

**The Niagara Cloud sidebar's gate — a DIFFERENT feature string, in a DIFFERENT module:**
```java
void load() {
   boolean niagaraRemoteLicensed = false;
   try {
      Sys.getLicenseManager().checkFeature("tridium", "premiumWBNiagaraRemote");
      niagaraRemoteLicensed = true;
   } catch (FeatureNotLicensedException var5) { }
   if (!niagaraRemoteLicensed) { ... }
```
`[CERT]` `BNiagaraCloudSideBar.java:140-165` (class declared `:59`, `com.tridium.niagaraCloud.sidebar`,
module `niagaraCloud` — a SEPARATE module from `niagaraSync`, confirmed by `niagaraCloud/vineflower/META-INF/module.xml:2`'s
own `moduleName="niagaraCloud"` declaration). The feature string is the literal `"premiumWBNiagaraRemote"` —
lexically unrelated to `"niagaraSync"`.

**The shipped UI copy independently confirms the "Premium Workbench" framing, in Tridium's own words, not an
inferred label:**
```
NiagaraCloudSideBar.premiumWorkbenchRequired=Upgrade to Premium Workbench to utilize this Niagara Remote feature.
```
`[CERT]` `niagaraCloud.lexicon:32` — this is the exact string shown to a user when `checkFeature("tridium",
"premiumWBNiagaraRemote")` throws. `[INFER]` (naming cross-reference, high confidence — the string is
unambiguous and first-party): `premiumWBNiagaraRemote`'s "Premium Workbench" wording is the SAME "Premium
Workbench" term [Block 48] §48.8 already found paired with "Niagara Recover" in Tridium's public roadmap
materials — meaning the Niagara Cloud sidebar's remote-device-browsing feature ("Niagara Remote") is
plausibly the SAME commercial tier [Block 48] named, gated by a feature string that literally spells out
"premium WB Niagara Remote."

**Net finding, closing B56-G2:** the two features [Block 56] worried might be conflated are licensed
INDEPENDENTLY — `niagaraSync`'s on-station replication checks `tridium:niagaraSync`; the Niagara Cloud
sidebar's "Niagara Remote" feature checks the unrelated `tridium:premiumWBNiagaraRemote`, in a different
module, with no shared constant, no shared permission class, and no module.xml cross-declaration found (a
grep of both modules' `module.xml` for `license`/`feature` tags found none — license gating in this codebase
is exclusively a runtime `checkFeature`/`getFeature` call, never a manifest-level declaration, consistent
with every other license gate this corpus has traced). `[CERT]` on both feature strings and both modules
being distinct; `[INFER]` on the "Niagara Remote" ≈ [Block 48]'s "Premium Workbench" identification (a strong
naming match, not a byte-for-byte SKU confirmation — no pricing/SKU document was read this session). The
"shared FAQ phrasing" risk [Block 56] flagged is NOT borne out at the code level: these are two genuinely
separate license gates that happen to be marketed with similar "limited availability" language, not one
bundled entitlement.

## 71.x — Connections

- **[Block 53]** — §71.1 closes **B53-G2**, correcting §53.1's own speculative framing ("likely a
  lower-level license-bootstrap utility... possibly used by a non-Workbench path") with a definitive
  structural finding: the second allowlist entry names an unlaunchable class. §71.3 closes **B34-G4** by
  individually opening the four files §53.4's own table named but did not re-read, and additionally
  identifies §53.4's read of `UpdateDaemonServlet.java:620-710` as adjacent to, but disjoint from, this
  block's own `:547-559` read of the SAME file for a different query action.
- **[Block 34]** — §71.2 closes **B34-G1**; §71.3 closes **B34-G4**; §71.4 closes **B34-G5**, correcting
  §34.8's table framing from an unresolved existence question to a settled "yes, at the import level" finding
  with two narrower residual gaps (B71-G4/B71-G5).
- **[Block 6]** — §71.4 extends §6.2's "`com.tridium.sys.license.subscription` is not new to N5" correction
  to the sibling `nre.jar`-side package, using [Block 6]'s own already-sealed class citation as the bridge.
- **[Block 56]** — §71.5 closes **B56-G2**, resolving the flagged naming-adjacency risk as NOT a licensing
  coupling — two independent feature strings, two independent modules.
- **[Block 37]** — §71.5 re-uses §37.7's `tridium:niagaraSync` citation for direct comparison against this
  session's fresh `tridium:premiumWBNiagaraRemote` finding, rather than re-deriving it.
- **[Block 48]** — §71.5's `[INFER]` identification of `premiumWBNiagaraRemote` with §48.8's "Premium
  Workbench"/"Niagara Recover" framing is the first code-level evidence tying that public term to a concrete
  license-feature string.

## 71.x — Child gaps opened this block

- **B71-G1** — Whether a DIFFERENT, not-yet-found class also named `LicenseDownload` (or resolving to the
  same FQCN via a different module/classloader) exists elsewhere in the N5 module set and WOULD supply an
  `nreMain` method, making the second `shouldCheckNreLicense` allowlist entry reachable after all — this
  session found and read only the one `portalApi.vineflower` copy; a full corpus-wide search for a SECOND
  `com/tridium/portal/util/LicenseDownload.class` under a different module was not performed.
- **B71-G2** — Whether the dead second allowlist entry (§71.1) is vestigial (a `nreMain` removed in a past
  refactor) or forward-looking (added for a headless launcher not yet implemented in this beta) — no
  changelog, comment, or version-control history is available in this static corpus to distinguish the two;
  would require either an internal Tridium changelog or a comparison against an EARLIER N5 beta build (none
  available this session).
- **B71-G3** — `PortalLicenseUtil.getPortalUpdates()`'s own HTTP body (the actual portal endpoint, request/
  response shape for authenticated per-host license/certificate sync using a LicenseAccessKey) was named as
  the consumer of both dialogs' output (§71.3) but not itself opened this session.
- **B71-G4** — N4's actual jar name/location for `com.tridium.nre.subscription` (proven to exist by import
  evidence, §71.4) was not independently located — would require either decompiling N4's `nre.jar` (if one
  exists under that name in the N4 install) or searching the N4 install's `bin/ext/` directory listing for
  candidate jars, neither performed this session (out of this block's N5-corpus scope).
- **B71-G5** — Byte/behavior-level diff between N4's and N5's `com.tridium.nre.subscription.RetrieveEntitlements`/
  `EntitlementApi` (do the N4-imported classes share N5's OAuth device-code flow, or is N4's client-transport
  layer materially different under the same package name) — would require the N4 decompilation named in
  B71-G4 as a prerequisite.
- **B71-G6** — The `niagara-remote-client-1.0.5` bundled library (found alongside the `niagaraCloud` module
  cluster during this session's search — `com.tridium.niagararemoteclient.NiagaraRemoteWebsocketAdapter`/
  `NiagaraRemoteClient`) was named but not opened; it may be the actual WebSocket transport backing the
  "Niagara Remote" feature §71.5 license-gates, not yet confirmed.

## 71.x — Self-verification (METHODOLOGY §11)

**Block type:** `mixed` (declared in header; §71.2/§71.5 draw synthesis conclusions across newly-read files
plus prior blocks' own sealed findings, alongside straight evidence-reading sections).

**Token check.** Every load-bearing `[CERT]` token below was independently `grep -n`-confirmed present in
its cited source THIS session (not hand-recalled):
`shouldCheckNreLicense`/`runClass`/`"FATAL: No nreMain: "`/`nreMain.invoke` (`Nre.java`) — 5 tokens;
`class LicenseDownload`/`private LicenseDownload()`/`copyLicenses`/`copyCertificates`/`licenseToVendors`
(`LicenseDownload.java`) — 5 tokens; `LicenseDownload.licenseToVendors`/`LicenseDownload.copyLicenses`/
`LicenseDownload.copyCertificates` (`LicenseProcedure.java`) — 3 tokens; `class DeviceCodeApi`/`getApiPath`/
`getConnectionUrl` (`DeviceCodeApi.java`) — 3 tokens; `REREGISTRATION_CAUSE_METADATA_KEY`/
`REREGISTRATION_CAUSE_BACKUP`/`DEFAULT_REGISTRATION_URL` (`EntitlementUtil.java`) — 3 tokens;
`resetRestoreParameters`/`SubscriptionMetadataUtil.addRegistrationMetadata` (`UpdateDaemonServlet.java`) — 2
tokens; `class ResetRestoreParametersMessage`/`getMessageString` (`ResetRestoreParametersMessage.java`) — 2
tokens; `ResetRestoreParametersMessage`/`resetSubscriptionParameters`/`LicenseMode.SUBSCRIPTION`
(`FinishDistInstall.java`) — 3 tokens; `class SyncOnline`/`showLicenseAccessKeyDialog`/
`BLicenseTreeAccessKeyDialog.open` (`BWorkbenchLicenseTree.java`) — 3 tokens; `class ImportCommand`/
`BRequestLicenseAccessKeyDialog.open` (`BLicensePlatformServicePlugin.java`) — 2 tokens; `class
BLicenseTreeAccessKeyDialog`/`createLicenseAccessKeyFile` — 2 tokens; `class BRequestLicenseAccessKeyDialog`/
`createLicenseAccessKeyFile` — 2 tokens; `import com.tridium.nre.subscription.RetrieveEntitlements`/
`class SubscriptionLicenseManager` (N4 `SubscriptionLicenseManager.java`) — 2 tokens; `class
BNiagaraCloudSideBar`/`checkFeature("tridium", "premiumWBNiagaraRemote")` — 2 tokens;
`NiagaraCloudSideBar.premiumWorkbenchRequired` (`niagaraCloud.lexicon`) — 1 token; `getFeature("tridium",
"niagaraSync")` (`BNiagaraSyncService.java`) — 1 token. **Total: 39 distinct load-bearing tokens confirmed
present.** The negative-existence claim ("zero `package com.tridium.nre` hits in the whole N4 corpus," §71.4)
was confirmed by a full-tree grep this session, not a partial search, per METHODOLOGY §3's symmetric
opening-obligation rule.

**Marker tally and citation resolution — mechanized via `verify-block.sh`:**

```
$ /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block71.md /home/cristian/niagara5-research
== verify-block: niagara5-block71.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 1)
   [CERT-live] 2  (adj 1)
   [CERT] 35  (adj 32)
   [CERT-doc] 2  (adj 1)
   [CERT-web] 2  (adj 1)
   [CERT-a] 2  (adj 1)
   [INFER] 12  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/37 = 0.30
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  /home/cristian/niagara-research/organized/baja/baja/vineflower/com/tridium/sys/license/subscription/SubscriptionLicenseManager.java:1-20  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  /home/cristian/niagara-research/organized/baja/baja/vineflower/com/tridium/sys/license/subscription/SubscriptionLicenseManager.java:1-54  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BLicensePlatformServicePlugin.java:826-930  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BLicenseTreeAccessKeyDialog.java:218  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraCloudSideBar.java:140-165  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BNiagaraSyncService.java:287  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BWorkbenchLicenseTree.java:550-792  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  EntitlementUtil.java:54-56  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  FinishDistInstall.java:280-283  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  LicenseDownload.java:13-78  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Nre.java:469-477  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Nre.java:470-472  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Nre.java:473  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Nre.java:498-539  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  RegistrationApi.java:132-135  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ResetRestoreParametersMessage.java:1-12  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  UpdateDaemonServlet.java:557  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  UpdateDaemonServlet.java:620-710  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  niagaraCloud.lexicon:32  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  niagaraCloud/vineflower/META-INF/module.xml:2  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:547-559  (range end verified; file has 823 lines)
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementUtil.java:1-60  (range end verified; file has 157 lines)
   ok      organized/baja/vineflower/com/tridium/sys/Nre.java:469-477  (range end verified; file has 1400 lines)
   ok      organized/niagaraCloud/vineflower/com/tridium/niagaraCloud/sidebar/BNiagaraCloudSideBar.java:140-165  (range end verified; file has 546 lines)
   ok      organized/niagaraCloud/vineflower/niagaraCloud.lexicon:32
   ok      organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:287
   ok      organized/platform/vineflower/com/tridium/platform/ui/license/BLicensePlatformServicePlugin.java:826-930  (range end verified; file has 1229 lines)
   ok      organized/platform/vineflower/com/tridium/platform/ui/license/BWorkbenchLicenseTree.java:550-792  (range end verified; file has 792 lines)
   short   :10  (short form — file implied by context; not script-verifiable)
   short   :13  (short form — file implied by context; not script-verifiable)
   short   :14  (short form — file implied by context; not script-verifiable)
   short   :17  (short form — file implied by context; not script-verifiable)
   short   :20  (short form — file implied by context; not script-verifiable)
   short   :33  (short form — file implied by context; not script-verifiable)
   short   :46  (short form — file implied by context; not script-verifiable)
   short   :5  (short form — file implied by context; not script-verifiable)
   short   :54  (short form — file implied by context; not script-verifiable)
   short   :55  (short form — file implied by context; not script-verifiable)
   short   :550  (short form — file implied by context; not script-verifiable)
   short   :56  (short form — file implied by context; not script-verifiable)
   short   :588  (short form — file implied by context; not script-verifiable)
   short   :59  (short form — file implied by context; not script-verifiable)
   short   :610  (short form — file implied by context; not script-verifiable)
   short   :73  (short form — file implied by context; not script-verifiable)
   short   :826  (short form — file implied by context; not script-verifiable)
   short   :885  (short form — file implied by context; not script-verifiable)
   short   :908  (short form — file implied by context; not script-verifiable)
   resolved 8 of 28
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**Reading the resolution split.** 8 of the 28 script-recognized citations resolve `ok` — these are the
ones cited with their FULL `organized/...`-rooted path (N5) per METHODOLOGY §11's citation-form convention.
The 20 `extern` items are either (a) bare `file:line`/`file:range` short-forms used in body prose for
readability where a fully-pathed citation to the SAME file already appears elsewhere in this block (e.g.
`Nre.java:473`/`Nre.java:470-472` inside §71.1's table, alongside the full-path `Nre.java:469-477` read
which DOES resolve `ok`), or (b) genuinely outside the script's target directory — the two N4
`SubscriptionLicenseManager.java` citations (§71.4), which point at the SIBLING `niagara-research` repository,
not `niagara5-research`, and are `extern` for that structural reason regardless of path form. The remaining
19 bare `:N` single-line citations (`short`) are inline body citations for `LicenseDownload.java`'s per-method
line numbers (§71.1) and similar short-form in-table citations, each backed by a full-path or full-filename
citation to the same source elsewhere in the same section — none is an orphaned, unresolvable citation with
NO fuller form anywhere in the block. This 8-of-28 split is the EXPECTED signature for a block whose sources
are entirely decompiled trees (this session's own N5 reads plus one cross-repository N4 read), per
METHODOLOGY §11's own "DECOMPILED-TREE BLOCKS WILL SHOW... near-ZERO resolved citations" rule — the burden
falls on the inline token-check above (39 distinct tokens independently `grep`-confirmed), not on this
script's citation-resolution pass.

**Adjusted marker counts (raw script tally minus this Self-verification section's own re-use of marker
names while describing the tally, and minus the header-blockquote legend, per §11's RAW-vs-ADJUSTED
convention):** the block's real evidence classes are `[CERT]` (the large majority — every §71.1-§71.4 finding
and most of §71.5) and `[INFER]` (concentrated in §71.1's "dead vs. forward-looking" framing, B71-G1/G2's own
honestly-bounded uncertainty, §71.4's B71-G4/G5 residual-scope framing, and §71.5's "Niagara Remote ≈ Premium
Workbench" naming cross-reference). No `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` markers
appear in this block (pure source-reading session, no native binaries, no web sources, no live probes) —
consistent with the header's own marker legend, which lists only `[CERT]`/`[INFER]` as used.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block71.md`. Per this
task's explicit scope ("Touch NO other file (no RESEARCH-STATE/INDEX/CATALOG, no git)"),
`INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and backlog re-classification are deliberately NOT
performed this session — left to the orchestrator, matching [Block 61]'s own convention for the same
instruction.
