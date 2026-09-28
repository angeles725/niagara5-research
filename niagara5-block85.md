# Block 85 — `PortalApi.getOnlineLicenseRequestPortalAddress()`'s real (and only) caller inside the `LicenseProcedure` wizard, the wizard's full subscription+legacy flow, and closing the entitlement `scope`-field and `canCheckTpk()`-gate questions

> Research closing four named child gaps against their PARENT BLOCK's own text (not this task's summary
> text — see DRIFT notes per gap below): **B77-G1** ([Block 77] §77.x's own child-gap text —
> `PortalApi.ONLINE_LICENSE_REQUEST_HOST`/`getOnlineLicenseRequestPortalAddress()`'s own caller was not
> located that session); **B77-G2** ([Block 77] §77.x — the two structural inconsistencies inside
> `PortalApi.getLicenseUpdates()`, whether defect or intentional); **B77-G3** ([Block 77] §77.x's OWN text —
> whether `EntitlementStatus.getScope()`/the `scope` OAuth response field is read anywhere outside the
> `nre.jar` package, that session's negative-existence grep having been scoped to
> `organized/_bin-ext/nre/vineflower/` only); **B77-G5** ([Block 77] §77.x's OWN text — whether
> `SecurityConstants.canCheckTpk()` being the shared gate for TPK-pin module classification,
> TLS-trust-bypass unreachability, and `TRIDIUM_DEV_CA_CERT` unpopulation is a deliberate single-flag
> production/dev-build design or incidental reuse); **B71-G2** ([Block 71] §71.x — the `LicenseProcedure`
> wizard's full flow, named as the real self-service license-download consumer of
> `AuthenticatedLicenseRetrievalUtil` in [Block 71] §71.3 but not itself traced end-to-end).
>
> **DRIFT DISCLOSURE (mandatory per task instructions):** this task's own gap list describes **B77-G3** as
> "RegistrationApi/EntitlementApi full field enumeration" and **B77-G5** as "Three unreferenced
> device-registration sibling constants." Neither description matches [Block 77]'s own `## 77.x — Child
> gaps opened` section verbatim. Cross-checked against `RESEARCH-STATE.md:389-391` (the source the task's
> summary was drawn from), the mismatch is confirmed there too — `RESEARCH-STATE.md`'s one-line summaries
> for B77-G3/G4/G5 do not reproduce [Block 77]'s own child-gap prose. The "three unreferenced sibling
> constants" description actually matches [Block 77]'s own **B77-G4** (not assigned to this block), whose
> OWN open question is WHY they are dead (refactor vs. unfinished path), not whether they exist — that
> enumeration was already done, in full, by [Block 77] §77.3 itself. This block uses [Block 77]'s OWN
> child-gap TEXT for B77-G3 and B77-G5 throughout, per task instruction. §85.6 below opportunistically
> closes the RESEARCH-STATE-described intent behind the "full field enumeration" phrasing as a HEAVY-mode
> bonus, without renaming it as a "closure" of the mismatched B77-G3 label.
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> Files opened this session in full: `organized/portalApi/vineflower/com/tridium/portal/api/PortalApi.java`
> (331 lines), `organized/portalApi/vineflower/com/tridium/portal/wb/LicenseProcedure.java` (1058 lines),
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SecurityConstants.java` (342 lines),
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/{EntitlementUtil,RegistrationApi}.java`
> in full, plus targeted reads of `EntitlementApi.java`, `HttpConnectionlessTransport.java`,
> `RetrieveEntitlements.java`, `UnbindApi.java`, `RotateKeys.java`, `RequestCertificates.java`, and
> `com/tridium/platform/license/PortalLicenseUtil.java`.

## 85.1 — B77-G1 CLOSED: `PortalApi.getOnlineLicenseRequestPortalAddress()`'s ONLY caller corpus-wide is `LicenseProcedure.requestLicense(String)`, in the legacy (non-subscription) license wizard's "Request Online" step — and the `ONLINE_LICENSE_REQUEST_HOST` constant it exists to return is ITSELF a dead shadow-literal `[CERT]`

A whole-corpus grep for `getOnlineLicenseRequestPortalAddress` returns exactly **3 hits total**: the method's
own declaration and the `ONLINE_LICENSE_REQUEST_HOST` constant's own declaration (`PortalApi.java:28,45`),
plus exactly **one call site** — `LicenseProcedure.java:181`,
`String portalHost = PortalApi.getOnlineLicenseRequestPortalAddress();` `[CERT]` (`grep -rn
getOnlineLicenseRequestPortalAddress organized`, this session, whole-tree, not package-scoped).

That call site is inside `LicenseProcedure.requestLicense(String hostId)` (`LicenseProcedure.java:176-218`),
the implementation behind the wizard's **`RequestLicenseOnline` step** (`LicenseProcedure.java:880-903`,
reached from `CheckServer` at `:491-492` when no local license file was found but
`PortalApi.checkConnectivity()` succeeds — see §85.3). `requestLicense()`:
1. Reads `portalHost` via the traced call (`:181`), validates it contains none of a fixed
   `INVALID_CHARACTERS` blacklist (`:79-81,183-187` — `{ } ( ) < > & * ‘ | = ? ; $ ^ # ~ ! % @ + , \` "`, an
   injection guard against the URL it is about to hand a shell process).
2. Builds a base64url-encoded query param `brand=<brandId>&hostId=<hostId>&clientVersion=<2-part
   version>` (`:193-195`) and appends it as `<portalHost>/license/request?params=<encoded>` (`:196-201`).
3. Launches it in the OS default browser via `xdg-open` (Linux) or `cmd.exe /c start` (Windows)
   (`:203-209`), through `SecurityUtil.doPrivileged` — i.e. this is a **local browser-launch flow**, not a
   direct HTTP call from the client to the portal; the portal-side `/license/request` page (not decompiled,
   server-side) presumably then leads a human through a web form.
`[CERT]` — whole method read this session, `LicenseProcedure.java:176-218`.

**Second finding, same shape as [Block 77] §77.3's three dead device-registration constants:**
`ONLINE_LICENSE_REQUEST_HOST` (`PortalApi.java:28`, value `"https://axlicensing.tridium.com"`) has **zero**
call sites referencing the constant itself anywhere in the corpus — its only hit is its own declaration
line. The real call site, `getOnlineLicenseRequestPortalAddress()` (`:45-52`), does NOT read
`ONLINE_LICENSE_REQUEST_HOST`; it hardcodes the IDENTICAL literal `"https://axlicensing.tridium.com"`
directly as the `System.getProperty` fallback default (`:48`) `[CERT]`. This is the exact same
"declared-but-shadowed-by-an-independent-identical-literal" pattern [Block 77] §77.3 found three times in
`EntitlementUtil.java` (its own **B77-G4**) — now confirmed a SECOND, independent time in a different
module (`portalApi`, not `nre.jar`) — see child gap **B85-G1**.

## 85.2 — B77-G2 ADVANCED, not closed: `getLicenseUpdates()`'s growing-payload accumulation bug is confirmed LIVE-REACHABLE from Workbench's real "Sync Online" call path, still without a changelog to settle intent `[CERT]`+`[INFER]`

[Block 77] §77.x named two structural inconsistencies in `PortalApi.getLicenseUpdates()` (re-read this
session, `PortalApi.java:87-109`): the request-accumulation pattern and the missing `<error>` element check
(present in every sibling method — `getLicenses`, `getCertificates`, `getCertificate` all call
`resp.elem("error")` and throw `PortalApiException`; `getLicenseUpdates` never does). Both re-confirmed
verbatim this session `[CERT]`.

**New this session:** the reflective caller, `PortalLicenseUtil.getPortalUpdates(BEnvLicenseSummary[],
Map)` (`organized/platform/vineflower/com/tridium/platform/license/PortalLicenseUtil.java:143-168`), passes
the **entire multi-host summary array in ONE reflective call** to `getLicenseUpdates()` — it does not loop
per-host itself `[CERT]`. This means the growing-`req`/repeat-POST behavior inside `getLicenseUpdates()`'s
own per-summary loop (`PortalApi.java:91-106`: each iteration adds one more `<params>` child to the SAME
never-reset `req` element, then POSTs the whole growing element again) is reachable in a single real
Workbench "Sync Online"/"Import" action ([Block 71] §71.3's traced UI consumers) whenever a station has
**2 or more** host summaries with license-access keys — i.e., this is not a purely theoretical code-reading
concern; a real 2+-host portal sync would, on the wire, re-POST host 1's params again when fetching host 2's
update, and again for host 3, etc. `[CERT]` on the mechanism (direct code read), `[INFER]` on real-world
impact (whether the portal server tolerates/ignores the repeated leading `<params>` elements or double-
processes them — this needs live traffic capture, out of static-read scope, matching [Block 77]'s own
deferral). **B77-G2 stays open** — WHY (defect vs. intentional) still has no changelog to consult; this
session narrows WHEN it fires (any 2+-host sync) rather than settling intent. See child gap **B85-G2**.

## 85.3 — B71-G2 CLOSED: the `LicenseProcedure` wizard's full flow traced end-to-end — two independent top-level branches (SUBSCRIPTION device-flow registration, and LEGACY portal/email license-file fetch), both converging on license installation `[CERT]`

`LicenseProcedure.licenseMe()` (`LicenseProcedure.java:84-161`) is the single entry point, branching on
`SubscriptionLicenseUtil.getLicenseMode()`:

**Branch A — `LicenseMode.SUBSCRIPTION`** (`:89-151`), driven by `SubscriptionLicenseUtil.getHostIdStatus()`:
- `"cloned"` → `RegenerateNreIdDialog` confirm → `SubscriptionLicenseUtil.regenerateNreId()`, else
  `Nre.licenseFailure()` (`:91-103`).
- `"unregistered"` → optional `RegenerateUnregisteredNreIdDialog`, then `RegisterNreIdDialog` confirm →
  `new DeviceCodeApi().getDeviceCode()` → on success, `stepTo(ShowUserCode(deviceCodeStatus))`
  (`:105-124`). **`ShowUserCode`** (`:933-1005`) renders the RFC-8628-shaped user code + verification URL
  ([Block 77] §77.3's traced fields), starts `AccessTokenApi.Poll.start(deviceCode, interval)` in its
  `run()` (`:1003`), and its "Continue" command checks `AccessTokenApi.isAccessTokenPollComplete()`
  (`:945`) — on success, steps to **`GetNreIdAndSubscriptionKey`** (`:640-718`), which prompts for a
  subscription key + optional "replacement NRE ID" checkbox, then calls
  `new RegistrationApi().register(pollStatus, subKeyField.getText(), replacement ? nreIdField.getText() :
  "")` (`:693-698`) — the exact 3-arg overload traced in §85.6 below. Success → `fetchEntitlements()` +
  close; failure → `ShowRegistrationFailure`.
- `"ok"` → `new SubscriptionLicenseManager().checkEntitlement()`, then
  `RetrieveEntitlements.getLastEntitlementStatus()`; a non-success status steps to `ShowEntitlementFailure`
  (`:127-149`).

**Branch B — legacy (non-subscription) mode** (`:152-160`): if `license.autoFetch` brand-prop is true,
`stepTo(CheckServer())`, else `LicenseUnavailable`. **`CheckServer`** (`:456-517`, background thread) calls
the private `getLicenseAccessKey()` (`:259-268`) — which reads a cached key via
`AuthenticatedLicenseRetrievalUtil.readLicenseAccessKey(Nre.getHostId())` ([Block 71] §71.3's own traced
util) and, if none cached, blocks on a **`RequestLicenseAccessKey`** dialog step (`:774-870`) that validates
the entered key's UUID-like format, calls `PortalApi.getLicenses(...)`, and on success persists it via
`AuthenticatedLicenseRetrievalUtil.createLicenseAccessKeyFile(...)` (`:802-809`). Back in `CheckServer.run()`
(`:471-516`): `PortalApi.getLicenses(...)` is called with the (now-available) key; **1 license file** →
`LicenseInstalled` (`:720-743`, which calls `LicenseDownload.copyLicenses`/`copyCertificates` — [Block 71]
§71.1's traced dead-launch-target class, here used only for its static copy methods, not launched);
**2+ license files** → `ChooseLicense` (`:519-572`) lets the user pick one via radio buttons, then follows
the same install path; **0 license files** → if `license.onlineRequest` + `PortalApi.checkConnectivity()`,
`RequestLicenseOnline` (`:880-903`, traced in §85.1 — launches the browser, then `DoneOnline`); otherwise
`RequestLicenseEmail` (`:872-878`, shows a static submit-by-email form built from `brand.*` `submit.*`
properties, `createRequestEmailContent`, `:270-315`).

**B71-G2 verdict: CLOSED.** Both branches, all steps, and both terminal outcomes (installed license vs.
online-request vs. email-fallback vs. hard failure) are traced to concrete method/line evidence `[CERT]`.
This also directly answers [Block 71] §71.1's own open question about why `LicenseDownload`'s `nreMain`-less
exemption entry looked vestigial: `LicenseDownload` IS actively used in this wizard, but only for its static
`copyLicenses`/`copyCertificates`/`licenseToVendors` helper methods (`LicenseProcedure.java:481,555,735-736`)
— never launched as a standalone target, consistent with (not contradicting) [Block 71] §71.1's "cannot
actually launch" finding.

## 85.4 — B77-G3 CLOSED (using [Block 77]'s own gap text): `EntitlementStatus.getScope()`/the `scope` OAuth response field has ZERO readers anywhere in the FULL 246-module N5 corpus, not just the `nre.jar` package `[CERT]`

[Block 77] §77.3 found `scope` written once (`AccessTokenApi.java:34`, into `EntitlementStatus.scope`,
declared `EntitlementApi.java:455`) but scoped its negative-existence check for a reader to
`organized/_bin-ext/nre/vineflower/` only, naming the wider-corpus check as **B77-G3**. This session widens
the grep to the WHOLE `organized/` tree: `getScope()` (the accessor, `EntitlementApi.java:636-638`) appears
in exactly **10 other files corpus-wide**, and every one of them is an UNRELATED same-named method on a
DIFFERENT class — `com.tridium.nre.cloud.NiagaraCloudConfiguration.getScope()` (a Niagara-Cloud OAuth scope,
different subsystem), `niagara.file.BIScopedFileSpace.getScope()`/`BScopedFileSpace.getScope()` (filesystem
ORD scoping, unrelated), `niagara.collection.BQueryResult.getScope()` (query `OrdTarget`, unrelated), and
LonWorks/hierarchy/box/cloudLink classes with their own unrelated `scope` fields `[CERT]` (`grep -rln
"getScope()" organized`, this session, whole-tree). **Zero** of these are
`com.tridium.nre.subscription.EntitlementApi.EntitlementStatus` — confirmed by reading each hit's own
class declaration; none imports or references `EntitlementApi`/`EntitlementStatus`. **B77-G3 verdict:
CLOSED.** The OAuth `scope` field is genuinely dead code corpus-wide, not merely package-locally: written
once from the Salesforce token response, stored, and read by nothing anywhere in this 246-module beta build
`[CERT]`.

## 85.5 — B77-G5 CLOSED (using [Block 77]'s own gap text): `SecurityConstants.canCheckTpk()` IS a single, deliberate, corpus-wide dev-vs-production-build gate — confirmed by the code's OWN error-message text, not incidental reuse `[CERT]`

A whole-corpus grep for `canCheckTpk` (`grep -rn canCheckTpk organized`, this session) returns **≥24 call
sites across 8 distinct modules** — far more than the three mechanisms [Block 77] §77.5 named
(TPK-pin module classification in `ModuleSetClassLoader.java`/`NModuleModuleFinderFactory.java`;
TLS-trust-bypass in `HttpConnectionlessTransport.java`; `TRIDIUM_DEV_CA_CERT` unpopulation, same file class)
`[CERT]`:

| Module | File | Use |
|---|---|---|
| `baja` | `com/tridium/sys/module/{ModuleSetClassLoader,NModuleModuleFinderFactory}.java` | module TPK-pin verification gating (traced [Block 77] §77.4/§77.5) |
| `baja` | `com/tridium/sys/Nre.java:642`; `com/tridium/logging/LogSettings.java:50` | log-level selection (`SEVERE` vs `WARNING`) |
| `platform` | `com/tridium/install/SignedDistFilter.java:29`; `com/tridium/platform/daemon/LocalSessionUtil.java:278` | distribution-signature filtering; local session trust |
| `_bin-ext/niagarad` | `NiagaraDaemon.java:159`; `log/NiagaraDaemonLogSettings.java:247` | daemon logger level selection |
| `_bin-ext/nre` | `subscription/HttpConnectionlessTransport.java` (5 sites: `:76,209,216,223,234`) | TLS cleartext/trust-bypass gating |
| `_bin-ext/nre` | `security/{KeyRing.java:260,SystemPassphrase.java:17,km/KeyMaterial.java:42,TextFileSignatureVerifier.java:139,144}` | simple-passphrase/simple-keymaterial fallback modes; text-signature check |
| `_bin-ext/nre` | `crypto/core/io/CoreCryptoManager.java:929,1128`; `crypto/core/cert/CertificateChainValidator.java:129,225` | core crypto/cert-chain TPK validation |

`[CERT]` — direct grep, this session, 24 lines counted across these files.

**Decisive evidence for "deliberate design," not "incidental reuse":** `HttpConnectionlessTransport.java`'s
own `AlwaysTrustManager`/`TrustingHostnameVerifier` inner classes throw
`new CertificateException("Use of AlwaysTrustManager outside of Development Build not allowed")` and `new
RuntimeException("Use of TrustingHostnameVerifier outside of Development Build not allowed")` when
`canCheckTpk()` is true (`HttpConnectionlessTransport.java:209-234`, exact strings) `[CERT]`. The code's OWN
literal error text equates `!canCheckTpk()` with "Development Build" — i.e., Tridium's own source
comments-as-strings confirm `canCheckTpk()` (gated on whether `SecurityConstants.TPK` is non-empty,
`SecurityConstants.java:312-314`) is THE canonical, singular is-this-a-dev-build flag, consulted uniformly
for log verbosity, TLS trust bypass, module signature pinning, passphrase/keymaterial simple-mode fallback,
and cert-chain validation across at least 8 unrelated modules. **B77-G5 verdict: CLOSED — deliberate
single-flag production/dev-build design, not incidental reuse**, directly evidenced by the gate's own
call-site error strings rather than inferred from usage count alone.

## 85.6 — Bonus (addresses the task summary's "RegistrationApi/EntitlementApi full field enumeration" intent, distinct from B77-G3's actual text closed in §85.4): the `nre.jar` subscription API's five concrete endpoints, request/response JSON field sets, and shared transport plumbing `[CERT]`

All five `EntitlementApi` subclasses share one POST-JSON transport (`EntitlementApi.makeRequest`/
`sendRequestMessageAndHandleResponse`, `EntitlementApi.java:35-115`, this session) against
`getConnectionUrl()` = `license.entitlementUrl` (default `https://www.niagaracentralapis.honeywell.com`,
`EntitlementUtil.DEFAULT_ENTITLEMENT_URL`) + per-API path, `Content-Type: application/json` unless
overridden `[CERT]`:

| Class : path constant (`EntitlementUtil.java`) | Endpoint | Request body fields | Response fields read |
|---|---|---|---|
| `RegistrationApi` : `NCENTS_REGISTER_API_PATH` | `/ncents/register` | `id`,`issued_at`,`signature` (from the access-token status), `nreId`, `metadata`(JSON), optional `reregistrationCause`/`existingNreId`/`refreshIncrement`, `licenseKey`,`publicKey`,`restoreId` — `RegistrationApi.java:115-140` | `type`,`message` (`:149`) |
| `RetrieveEntitlements` : `ENTITLEMENTS_API_PATH` | `/ncents/entitlements` | `nreId`,`productId`,`refreshIncrement`,`restoreId`,`nonce` — `RetrieveEntitlements.java:141-146` | `entitlements` presence check (`:157`) |
| `UnbindApi` : `NCENTS_UNBIND_API_PATH` | `/ncents/unbind` | `nreId` — `UnbindApi.java:73` | `type`,`message`,`licenseKey` — `:80,90` |
| `RotateKeys` : `ROTATE_KEY_API_PATH` | `/ncents/authn/api_key` | `nreId`,`publicKey` — `RotateKeys.java:32` | (not read this session) |
| `RequestCertificates` : `CERTIFICATES_API_PATH` | `/ncents/certificates` | `version`,`vendors`,`nreId` — `RequestCertificates.java:56` | (not read this session) |
| `DeviceCodeApi`/`AccessTokenApi` : `DEVICE_CODE_API_PATH`/`ACCESS_TOKEN_API_PATH` (both `/services/oauth2/token`, form-urlencoded, on `license.registrationUrl` — [Block 77] §77.3, unchanged) | — | — | — |

`[CERT]` — every path/field cited resolves to the file:line shown, this session. Auth headers:
`EntitlementUtil.makeRegistrationHeader(contentType, accept, authorization)` sets `Authorization: Bearer
<token>` + `Content-Type` + `Accept` (`EntitlementUtil.java:150-156`); `RetrieveEntitlements` instead signs
with a per-request JWT (`makeJwtAuthHeader`, `EntitlementUtil.makeJwtHeaderString`, ES256, `kid=K1`, audience
`license.entitlementServerName` default `www.niagaracentralapis.honeywell.com`, `EntitlementUtil.java:79-106`
— unchanged from [Block 77]'s general characterization, now with the exact JWS algorithm/kid/audience
triple). This is presented as a bonus close of the RESEARCH-STATE-drift intent, not a renaming of B77-G3's
own (already-closed, §85.4) text.

## 85.x — Connections

- §85.1's `ONLINE_LICENSE_REQUEST_HOST` dead-constant finding is a SECOND confirmed instance of the exact
  "declared constant shadowed by an identical hardcoded literal at its real call site" pattern [Block 77]
  §77.3 found three times for `DEVICE_REGISTRATION_*` — see **B85-G1**, which asks whether this is a
  corpus-wide Tridium convention.
- §85.2 extends [Block 77] §77.x's B77-G2 by naming the exact real-world trigger condition (any 2+-host
  Workbench "Sync Online") via the newly-read `PortalLicenseUtil.getPortalUpdates()` reflective caller.
- §85.3 closes the flow [Block 71] §71.1/§71.3 both partially named (`LicenseDownload`'s real, non-launch
  use; `AuthenticatedLicenseRetrievalUtil`'s dialog consumers) and connects it to [Block 77] §77.3's
  device-code/access-token/registration field-level schema, now shown wired into concrete wizard steps.
- §85.4 and §85.5 both close [Block 77] §77.x child gaps using that block's OWN text, per this task's drift
  discipline, distinct from the RESEARCH-STATE.md one-line summaries this task quoted (see header DRIFT
  DISCLOSURE).
- §85.6 is a bonus corpus-wide endpoint/field census that gives the RESEARCH-STATE-drift phrasing ("full
  field enumeration") a real, cited answer without re-labeling B77-G3.

## 85.x — Child gaps opened

- **B85-G1** — A systematic corpus-wide audit for the "declared constant shadowed by an independent
  identical-literal at its real call site" anti-pattern, now confirmed twice ([Block 77] §77.3's three
  `DEVICE_REGISTRATION_*` constants; §85.1's `PortalApi.ONLINE_LICENSE_REQUEST_HOST`) but never searched for
  systematically — would require grepping every `public/private static final String` constant against its
  own call sites corpus-wide, a bounded but not-yet-run mechanical sweep.
- **B85-G2** — Live-traffic confirmation of whether the portal server actually mishandles or safely ignores
  `getLicenseUpdates()`'s repeated/growing `<params>` payload (§85.2) on a genuine 2+-host sync — requires a
  real multi-host station and network capture, out of this corpus's static-read scope (same class of
  blocked-on-live-traffic gap as [Block 77]'s own B77-G2).
- **B85-G3** — `RotateKeys`'s and `RequestCertificates`'s RESPONSE field shapes (§85.6's table) were not
  read this session (only their request bodies) — a small, cheap follow-on read of the same two files
  already open in `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/`.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `getOnlineLicenseRequestPortalAddress`'s only call site corpus-wide is `LicenseProcedure.java:181` | [CERT] | `grep -rn getOnlineLicenseRequestPortalAddress organized` → 3 hits (2 decls + 1 call) |
| 2 | `requestLicense()` builds `<portalHost>/license/request?params=<base64url(brand&hostId&clientVersion)>` and launches it via `xdg-open`/`cmd.exe start` | [CERT] | `LicenseProcedure.java:176-218` |
| 3 | `ONLINE_LICENSE_REQUEST_HOST` constant has zero referencing call sites; `getOnlineLicenseRequestPortalAddress()` hardcodes the identical literal instead | [CERT] | `PortalApi.java:28,45-52`; grep shows only the decl line as a hit for the constant name |
| 4 | `PortalLicenseUtil.getPortalUpdates()` passes the full multi-host summary array in one reflective call to `getLicenseUpdates()` | [CERT] | `PortalLicenseUtil.java:143-168` |
| 5 | Real-world server-side impact of the growing-payload pattern on 2+-host sync | [INFER] | mechanism confirmed by code read; server tolerance unconfirmed, no live capture this session |
| 6 | `LicenseProcedure.licenseMe()` two-branch (SUBSCRIPTION device-flow vs. legacy portal/email) full flow traced to concrete steps | [CERT] | `LicenseProcedure.java:84-1005` (line ranges cited per step in §85.3) |
| 7 | `getScope()` (the `EntitlementStatus` accessor) has zero corpus-wide readers; the 10 other `getScope()` hits are unrelated classes | [CERT] | `grep -rln "getScope()" organized` → 10 files, each read/confirmed unrelated class |
| 8 | `canCheckTpk()` has ≥24 call sites across 8 modules, not just the 3 mechanisms [Block 77] §77.5 named | [CERT] | `grep -rn canCheckTpk organized` count + module breakdown table |
| 9 | `AlwaysTrustManager`/`TrustingHostnameVerifier` throw "...outside of Development Build not allowed" when `canCheckTpk()` is true | [CERT] | `HttpConnectionlessTransport.java:209-234` exact strings |
| 10 | Five `nre.jar` subscription endpoints' request/response field sets (register/entitlements/unbind/rotateKeys/certificates) | [CERT] | per-file:line citations in §85.6 table |

Tally: 9 [CERT], 1 [INFER] (ratio 0.11). No [CERT-hw]/[CERT-live]/[CERT-doc]/[CERT-web]/[CERT-a] markers used
this session — every claim rests on direct `Read`/`grep` of the decompiled source in this session, not on
recalled prior-block content (prior-block content is cited as `[Block N] §N.x` context, never re-asserted as
a fresh marker). **MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block. **Secrets
discipline**: `SecurityConstants.TPK` and `DEVICE_REGISTRATION_CLIENT_ID` are referenced only by file:line
and prior-block characterization (both already closed as format-only in [Block 77]); their byte/character
values are not reproduced in this file. B77-G4 (live token exchange / requires-execution) was NOT attempted
— no network calls were made this session, consistent with the task's explicit instruction.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block85.md`.
`RESEARCH-STATE.md`/`INDEX.md`/`CATALOG.md` were NOT edited, per task instructions — regeneration is left to
the integrator step.
