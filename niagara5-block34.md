# Block 34 — N5 subscription entitlements and capacity licensing: the `nre.jar` `com.tridium.nre.subscription`/`com.tridium.nre.license` bootstrap (closing B6-G1), and `resource.limit`'s NOT-capacity-licensing polarity corrected against B11 §11.5 (closing B11-G1)

> Research of **N5 5.0.0.28's subscription-entitlement client (`com.tridium.nre.subscription`, `nre.jar`)
> and capacity-licensing enforcement (`com.tridium.sys.metrics`, `baja.jar`)**: the online/offline
> registration-and-entitlement-refresh bootstrap that runs *before* `baja` loads (device-code OAuth-style
> registration, JWT-signed API calls, certificate/license caching, key rotation), and what
> `Metrics.isUsingCapacityLicensing()` actually gates. Closes [Block 6]'s child gap **B6-G1**
> (`com.tridium.nre.subscription`/`EntitlementApi` in `nre.jar`) and [Block 11]'s child gap **B11-G1**
> (`Metrics.isUsingCapacityLicensing()`/`resource.limit`). Also resolves [Block 6]'s **B6-G2** (the
> unexplained `security/licenses/conf/<hostid>/` directory on the live install). Covers: the subscription
> bootstrap/cache-file layout (names/format only, per SECRETS DISCIPLINE), online-vs-offline behavior,
> endpoints as STRUCTURE (path/host constants, not live traffic), retry/backoff and failure modes, how this
> relates to [Block 6]'s `SubscriptionLicenseManager` (`baja.jar`), the two-tier capacity-licensing
> enforcement map compared against N4, and a `conf/` directory closure. Does **not** cover: live
> registration/entitlement traffic against Tridium's servers (read-only static block, no N5 station
> available); a full decompile of `com.tridium.nre.security.KeyRing`/`Aes256PasswordManager`/`SecurityInitializer`
> (referenced, not opened, this session — their internals back every cache-file encryption cited below);
> or OEM-branded N5 builds (continues [Block 11]'s **B11-G2** framing).
>
> Subject version: N5 **5.0.0.28** (Beta) — same install as [Block 6]/[Block 11]:
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` and
> `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` (unversioned by git; jar `mtime` serves as the
> version stamp, per METHODOLOGY §3). N4 baseline: the `niagara-research` corpus (read as remittance, not
> re-derived).
>
> Sources:
> - `/home/cristian/niagara5-research/organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/**`
>   (24 `.java` files, [Block 6]/[Block 11]'s own prior extraction of `nre.jar`, read here — not
>   re-decompiled) — `EntitlementApi`, `SubscriptionLicenseUtil`, `RetrieveEntitlements`, `RegistrationApi`,
>   `RefreshIncrement`, `RestoreId`, `JwtSignatureKeys`, `RotateKeys`, `UnbindApi`, `DeviceCodeApi`,
>   `AccessTokenApi`, `RequestCertificates`, `HttpConnectionlessTransport`, `SubscriptionMetadataUtil`,
>   `LicenseRefreshToken`, `EntitlementStatusListener`, `LicenseValidator`.
> - `.../nre/vineflower/com/tridium/nre/license/AuthenticatedLicenseRetrievalUtil.java` (1 file, new
>   package this block opens) — closes B6-G2.
> - `.../nre/vineflower/com/tridium/nre/util/NiagaraFiles.java`,
>   `.../nre/vineflower/com/tridium/nre/security/SecurityConstants.java` — path resolution and the TLS
>   trust-bypass gate.
> - `/home/cristian/niagara5-research/organized/baja/vineflower/com/tridium/sys/metrics/{Metrics,GlobalGroup,
>   SubGroup,Group,BISubLicenseable}.java`, `.../com/tridium/sys/resource/ResourceManager.java` — this
>   session's own read of [Block 6]/[Block 11]'s prior `baja.jar` extraction, `diff`-ed against N4.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` — live `javap -c -p` re-run this
>   session on `com.tridium.sys.resource.ResourceManager#checkLicense` to settle the `ifeq`/`ifne` polarity
>   [Block 11] left unresolved-in-bytecode.
> - N4 REMITTANCE (read, not re-derived): `niagara-research/organized/baja/baja/vineflower/com/tridium/sys/
>   {metrics,resource}/**` (`diff`-ed file-by-file against the N5 files above),
>   `niagara-research/niagara-mental-model-bloque488.md` (full text), plus
>   `python3 niagara-research/tools/corpus-nav.py find "resource.limit"|"capacity licens"|"EntitlementCheck"`
>   → B387, B477, B478, B479, B480, B481, B483, B487, B806, B1144.
>
> Method: read the already-decompiled Vineflower trees (no new decompilation — [Block 6]/[Block 11] already
> extracted both jars); `diff` every N5 file cited above against its N4 namesake in the `niagara-research`
> corpus decompile; one live `javap -c -p -classpath baja.jar com.tridium.sys.resource.ResourceManager`
> re-run this session to read the exact `ifeq`/branch-target bytecode (settles the polarity question
> [Block 11] left as a bytecode-offset-only citation without the branch condition itself).
> Markers: `[CERT]` local primary (`file:line`) · `[CERT — negative existence, artifact opened]` ·
> `[INFER]` deduction. No `[CERT-doc]`/`[CERT-web]` this block (no manual/web consulted).
>
> Licensing/subscription layer. Connects [Block 6] (parent gap B6-G1, direct closure; also closes B6-G2),
> [Block 11] (parent gap B11-G1, direct closure — corrects §11.5's inferred polarity), [Block 3]
> (`SecurityUtil.doPrivileged`/`checkPermission` call sites throughout this package are the same
> `SecurityAgent`-routed permission model Block 3 documents), and, across corpora, `niagara-research` B477/
> B481/B487/B1144 (N4's own subscription-watchdog documentation, the comparator for §34.3) and B488 (N4's
> license limit-enforcement map, the comparator for §34.6).
>
> **Type:** standard

---

## 34.1 — Subscription bootstrap: directory layout and cache-file inventory (structure/names only) `[CERT]`

`SubscriptionLicenseUtil` (`nre.jar`, `com.tridium.nre.subscription`) is the class every other class in this
package routes through for paths and host identity. Its directory tree, rooted at
`NiagaraFiles.getSubscriptionPath()` = `<niagara.config.home>/security/subscription`
(`NiagaraFiles.java:135-137`, `SubscriptionLicenseUtil.java:52`), is built from field constants — no file
content was opened, only these class-level `File` declarations and their creation sites: `[CERT]`
`SubscriptionLicenseUtil.java:44-58,104-182`.

| Path (relative to `security/subscription/`) | Purpose (from code, not content) | Written by |
|---|---|---|
| `licenses/` | subscription `.license` files, one per vendor (`<Vendor>.license`) | `writeLicense()` `:501-538` |
| `certificates/` | subscription `.certificate` files, one per vendor | `writeCertificate()` `:413-443` |
| `db/<licenseKey>/` | per-remote-device NRE-ID directory (multi-device/remote-station subscriptions) | `getSubscriptionDbDirectory()` `:139-158` |
| `deregistration/<licenseKey>` | a marker file dropped after a successful `unbind`, holding `"<nreId> - <licenseKey>"` | `UnbindApi.createLicenseKeyFile()` `:129-144` |
| `nreId` | the device's subscription Host-ID (`Nre-<UUID, uppercased>` format) | `establishNreId()` `:322-398` |
| `.restoreId` | AES-256-GCM-encrypted UUID, KeyRing-backed (`baja.licensing.subscription.restoreId` alias) | `RestoreId.write()` `:96-140` |
| `.refreshIncrement` | AES-256-encrypted monotonic replay-counter, KeyRing-backed (`baja.licensing.subscription.refreshIncrement` alias) | `RefreshIncrement.write()` `:78-123` |
| `.ecKeyPair` | AES-256-encrypted EC (secp256r1) key pair used to JWT-sign every API request, KeyRing-backed (`baja.licensing.subscription.ecKeyPair` alias) | `JwtSignatureKeys.generateKeys()` `:120-132` |
| `.ecKeyPair.r1` | the ROTATION-CANDIDATE key pair, staged during `RotateKeys`/`KeyRotation` before commit | `JwtSignatureKeys.KEY_PAIR_ROTATION_FILE` `:34-36` |
| `.registered` | serialized `Instant.now()` of a successful registration | `RegistrationApi.registerApi()` `:150-190` |
| `.cloned` | serialized `Instant` marking a detected clone (read by `isCloned()`; write site not in this package — set by the [Block 6]-documented `baja.jar` clone-detection path) | `SubscriptionLicenseUtil.isCloned()`/`readCloningTime()` `:286-301` |
| `.kr`/`.km` | a LEGACY subscription-scoped key ring, merged into the MAIN key ring and deleted on upgrade | `mergeSubscriptionKeyRingWithMainKeyRing()` `:540-564` |

Every write of a `.working` temp file followed by `Files.move(..., ATOMIC_MOVE)` (`RefreshIncrement.java:91-113`,
`RestoreId.java:105-140`, `JwtSignatureKeys.java:247-303`, `SubscriptionMetadataUtil.java:93-109`) is the SAME
crash-safe write pattern repeated across every cache file in this package — a `.working` orphan left by a
crash mid-write is transparently recovered on the next `read()` (`Files.move` back to the canonical name before
reading, e.g. `RestoreId.java:153-160`). `[CERT]` — this is a structural/robustness observation, not content.

`license.properties` (`<niagara.config.home>/etc/license.properties`, `NiagaraFiles.java:111-113`, referenced
as `SubscriptionLicenseUtil.LICENSE_PROPERTIES_FILE`, `:44`) is the ONE plaintext, unencrypted file in this
tree — it holds override properties (`license.entitlementUrl`, `license.subscriptionMode`,
`license.clientId`, `license.deviceRegistrationHost`, `license.certificateVersion`, …, §34.2) plus, in a
distinct `registration.metadata.*` key namespace, arbitrary registration metadata
(`SubscriptionMetadataUtil.java:16,28-38`) — including a `reregistrationCause` flag used to detect a
backup-restoration re-registration (§34.3). `[CERT]` — key NAMES only, no values read (this file is not
under `security/`, `licenses/`, or `certificates/`, so it is outside this block's read exclusion, but no
instance of it was opened on the live install either — the property names come from the code, not a read
file).

## 34.2 — Online endpoints and auth flow, as STRUCTURE `[CERT]`

Every host/path below is a CONSTANT read from `EntitlementUtil`/`EntitlementApi` subclass overrides — no
network traffic was generated. Default values are code defaults, overridable via `license.properties`
(`EntitlementApi.makeRequest():48-68`, `SubscriptionLicenseUtil.getLicenseProperties()`).

| API | Host (default) | Path | Auth | Purpose |
|---|---|---|---|---|
| Device Code | `EntitlementUtil.DEFAULT_REGISTRATION_URL` | `/services/oauth2/token` | none (client_id + response_type=device_code, form-urlencoded) | start OAuth 2.0 device-authorization flow `DeviceCodeApi.java:59-93` |
| Access Token | same registration host | `/services/oauth2/token` | none (client_id + grant_type=device + code) | poll for token after user approves `AccessTokenApi.java:12-41`, 10-min window `:120-176` |
| Register | same registration host | `/ncents/register` | Bearer = access token | bind this NRE-ID to a license key `RegistrationApi.java:24-26,61-195` |
| Entitlements | `EntitlementUtil.DEFAULT_ENTITLEMENT_URL` | `/ncents/entitlements` | Bearer = ES256 JWT (self-signed) | fetch/refresh licensed entitlements `RetrieveEntitlements.java:53-54` |
| Certificates | same entitlement host | `/ncents/certificates` | Bearer = ES256 JWT | fetch vendor certificate(s) `RequestCertificates.java:21-23` |
| Rotate Keys | same entitlement host | `/ncents/authn/api_key` | Bearer = ES256 JWT | rotate the EC JWT-signing key `RotateKeys.java:14-16` |
| Unbind | same entitlement host | `/ncents/unbind` | Bearer = ES256 JWT | deregister this NRE-ID `UnbindApi.java:21-23` |

`EntitlementUtil.java:45,47` names the two default hosts as CONSTANTS in source (not reproduced verbatim
here beyond confirming they exist as HTTPS, port-443 defaults, `:46,48`); `getConnectionUrl()` is overridden
per-API-subclass, so entitlement/certificate/rotate/unbind traffic defaults to one host and
device-code/access-token/register traffic defaults to a SECOND, different host — a genuine two-server split
`[CERT]` (`EntitlementApi.java:32-34` base default vs `AccessTokenApi.java:80-82`/`DeviceCodeApi.java:25-27`
overrides).

**JWT auth**: `EntitlementUtil.makeJwtHeaderString(hostId)` builds a `JwtClaims` (`subject`=hostId,
`audience`=configurable, default expiration 10 minutes) signed `ES256` with the device's own EC private key
(`JwtSignatureKeys.getInstance().getPrivateKey()`), key-ID header `"K1"` — a **self-issued, self-signed**
bearer token; the server side validates it against the public key uploaded at registration time (§34.1's
`.ecKeyPair`, `publicKey` field in the registration request body, `RegistrationApi.java:53-54,140`).
`[CERT]` `EntitlementUtil.java:79-106`.

**Device-code (OAuth 2.0 RFC 8628-shaped) flow**: `DeviceCodeApi` → user visits `verification_uri` and enters
`user_code` → `AccessTokenApi.Poll` polls every `interval` seconds (doubling on a `"too_fast"` 400 response,
`AccessTokenApi.java:148-151`) for up to 10 minutes (`ACCESS_TOKEN_POLLING_MINUTES=10`, `:10,121`) →
`RegistrationApi.register()` binds the NRE-ID using the resulting access token. `[CERT]` — this is the
HUMAN-INTERACTIVE first-time-registration path; `RetrieveEntitlements`/`RotateKeys`/`UnbindApi` (already
registered) use the self-signed JWT path instead, no human interaction.

**Sanitization discipline**: `EntitlementApi.sanitizeMessage()` masks `publicKey`/`refreshIncrement`/`restoreId`
fields with `"********"` before any request/response body is written to the FINE/FINER log level
(`EntitlementApi.java:247-270`), and `getSanitizedRequestHeadersForLog()` decodes and re-masks the
`Authorization` JWT payload rather than logging the raw bearer token (`:207-227`) — a deliberate,
code-level logging-redaction discipline for exactly the fields this block's own SECRETS DISCIPLINE also
protects. `[CERT]`

## 34.3 — Offline/failure-mode behavior and grace periods `[CERT]`/`[INFER]`

Two INDEPENDENT retry/failure layers exist, at two different jars:

- **`nre.jar` (this block, client-transport layer)**: `RetrieveEntitlements.retrieveEntitlements(initialDelay)`
  retries with DOUBLING delay (`retryDelay *= 2L`, `:97`) inside a hard **5-minute** wall-clock budget
  (`RETRIEVE_ENTITLEMENTS_RETRY_TIMEOUT = Duration.ofMinutes(5)`, `:26`, checked via
  `entitlementCheckExpired()` `:136-138`), only for RETRYABLE HTTP codes (`isRetryableError`: anything except
  200/409, `:132-134`). A non-retryable failure (`INVALID_REFRESH_TOKEN`, `LICENSE_EXPIRED`,
  `LICENSE_REVOKED`, `RESTORE`) returns immediately without exhausting the budget (`:77-95`). On exhaustion,
  it returns state `FAILURE` code `10` ("retry expired after 5 minutes") `[CERT]` `RetrieveEntitlements.java:57-130`.
- **`baja.jar` (already documented by [Block 6] §6.11 and N4's own B477/B481/B487/B1144 — not re-derived
  here)**: `SubscriptionLicenseManager`'s `EntitlementCheck` runs every `validCheckFreq` (default **6 h**) +
  30 min + `random(0..900s)` jitter, with its own `periodicCheckFailureCount` reset-on-success
  (`niagara-research` B477 §…, B481 §481, `[Block 6] §6.11` — remitted, not re-derived), and
  `KeyRotationCheck` on a separate ~90-day cadence.

These two layers COMPOSE: the 6-hour `SubscriptionLicenseManager` job is what CALLS into
`SubscriptionLicenseUtil.getLicenseUpdate()` → `new RetrieveEntitlements(lrt, null)` →
`getLicenseUpdate(RetrieveEntitlements)` (`SubscriptionLicenseUtil.java:449-463`), and the 5-minute
inner-retry budget is the bounded, SYNCHRONOUS transport-layer retry INSIDE one 6-hourly attempt — not a
separate cadence. `[CERT]` on the call chain; `[INFER]` on "not a separate cadence" being the intended
design (not independently confirmed against a running system this session).

**Key-revocation grace behavior**: on an `INVALID_REFRESH_TOKEN`/`LICENSE_EXPIRED` response, the client just
surfaces the failure (no automatic remediation). On `LICENSE_REVOKED`, the client PROACTIVELY calls
`SubscriptionLicenseUtil.regenerateNreId()` — which DELETES the entire `security/subscription/` directory
contents (§34.1's whole cache: `.registered`, `.restoreId`, `.refreshIncrement`, `.ecKeyPair`, `licenses/`,
`certificates/`) and mints a fresh Host-ID — before returning the `LICENSE_REVOKED` status to the caller
(`RetrieveEntitlements.doCheckEndpointErrorResponse():301-309`, `SubscriptionLicenseUtil.regenerateNreId():
192-200`). `[CERT]` — this is a client-initiated, automatic "wipe-and-remint" reaction to server-signaled
revocation, distinct from the `.cloned`-flagged clone-detection path (§34.1) which is written elsewhere
([Block 6]'s `baja.jar` scope) and only READ here.

**Backup-restoration re-registration**: `SubscriptionMetadataUtil`'s `registration.metadata.reregistrationCause`
key, when set to `"backup-restoration"`, causes the NEXT `RegistrationApi.registerApi()` call to include a
`refreshIncrement` in the request body and flag `reregistrationCause` server-side
(`RegistrationApi.java:132-135`) — a distinct re-registration path from `"device-replacement"` (used when
`existingNreId` is supplied, `:114,122-126`). `[CERT]` `RegistrationApi.java:61-138`. Neither write site for
`reregistrationCause` was found in this package (it is set by a caller outside `com.tridium.nre.subscription`,
not traced this session) — named **B34-G1**.

**Certificate-version fallback**: `RequestCertificates.getCertificateVersion()` reads
`license.certificateVersion` from `license.properties`, defaulting to `"5.0"`, and falls back to that same
default if the configured value fails `new Version(...)` parsing (`RequestCertificates.java:98-111`) — a
fail-safe default rather than a hard error.

## 34.4 — TLS trust bypass, GATED by a build-time tamper-proofing key `[CERT]`/gate condition `[CERT]`/exploitability `[INFER]`

`HttpConnectionlessTransport` defines `AlwaysTrustManager`/`TrustingHostnameVerifier` inner classes that,
if wired up, would accept ANY server certificate and ANY hostname (`HttpConnectionlessTransport.java:206-241`).
Per METHODOLOGY §3's static-defect/gate-condition split, this is recorded precisely:

- **The static defect exists**: `AlwaysTrustManager.checkServerTrusted()`/`checkClientTrusted()` have empty
  bodies (no exception unless gated, `:214-219`), and `TrustingHostnameVerifier.verify()` returns `true`
  unconditionally (unless gated, `:232-237`). `[CERT]`
- **The wiring is GATED, at TWO independent points, by `SecurityConstants.canCheckTpk()`**
  (`SecurityConstants.java:312-314`, `return TPK.length != 0` — `TPK` is a hardcoded byte array, an X.509
  `SubjectPublicKeyInfo`-shaped RSA public key, present and non-empty in THIS installed build): `[CERT]`
  1. `HttpConnectionlessTransport.makeClient()` only calls `.hostnameVerifier(TRUSTING_HOSTNAME_VERIFIER)
     .sslSocketFactory(factory, TRUSTING_MANAGER)` inside an `if (!SecurityConstants.canCheckTpk())` branch
     (`:76-84`) — on a build where `canCheckTpk()` is TRUE (this installed build), this branch never runs,
     so the trusting managers are NEVER installed on the `OkHttpClient`; standard system TLS validation
     applies. `[CERT]`
  2. Even if `AlwaysTrustManager`/`TrustingHostnameVerifier` were instantiated and invoked directly, each of
     their three methods independently re-checks `canCheckTpk()` and THROWS
     (`CertificateException`/`RuntimeException` "…outside of Development Build not allowed") if it is true
     (`:209-211,215-217,222-227,234-238`) — a second, defense-in-depth gate. `[CERT]`
- **Exploitability in THIS build**: `TPK.length != 0` in the installed `nre.jar` (a populated ~256-byte RSA
  key, structure only — not reproduced, per SECRETS DISCIPLINE), so `canCheckTpk()` returns `true` and BOTH
  gates are closed — the TLS-bypass code is present but UNREACHABLE in this build. `[INFER]` on "unreachable
  in THIS build" resting on the observed non-empty `TPK` array; the gate condition itself
  (`TPK.length == 0`, i.e. an unsigned/dev build shipping an empty placeholder key) is `[CERT]` from the code.
  Not independently verified against an actual dev/unsigned N5 build this session (none available) — named
  **B34-G2**.

## 34.5 — `EntitlementApi.EntitlementState`: 9-value enum, implicitly sealed (JLS), not `sealed`-keyword `[CERT]`

`EntitlementApi.EntitlementState` (`EntitlementApi.java:386-441`) is a 9-constant `public enum` —
`SUCCESS`, `FAILURE`, `INVALID_VENDOR`, `INVALID_REFRESH_TOKEN`, `LICENSE_EXPIRED`, `LICENSE_REVOKED`,
`REGISTERED`, `RESTORE`, `KEY_ROTATION_FAILURE` — each with a per-constant anonymous-body `toString()`
override (e.g. `LICENSE_REVOKED.toString()` → `"license revoked"`, used both for display and as the
`responseType` string matched in `doCheckEndpointErrorResponse()` implementations, §34.3). `[CERT]` — the
decompiled source shows NO explicit `sealed` keyword (Java enums do not carry one; every `enum` is
IMPLICITLY a closed/sealed type set by the JLS, which is presumably what [B25]'s "sealed" framing
generalizes over — [B25] catalogued explicit `sealed` CLASS/INTERFACE declarations, a different Java 17+
feature; this enum is not one of those). `[CERT]` on the enum shape; `[INFER]` on reconciling this with the
task's "sealed per B25" framing — [B25] itself was not re-opened this session to confirm it counted this
specific enum.

## 34.6 — Capacity licensing: `Metrics.isUsingCapacityLicensing()` gates `resource.limit` OFF, not ON — correcting [Block 11] §11.5 `[CERT]`

**The correction.** [Block 11] §11.5 stated `resource.limit` "is read only when
`com.tridium.sys.metrics.Metrics.isUsingCapacityLicensing()` returns `true`" — inferred from a bytecode
OFFSET adjacency (`invokestatic isUsingCapacityLicensing` at offset 148 immediately before the
`ldc "resource.limit"` at 156) without reading the branch CONDITION itself. This block re-ran
`javap -c -p -classpath baja.jar com.tridium.sys.resource.ResourceManager` live this session and reads the
actual instructions:

```
148: invokestatic  Metrics.isUsingCapacityLicensing:()Z
151: ifeq          155        // if FALSE, jump to 155 (read resource.limit)
154: return                   // if TRUE (fell through from 151), return early — resource.limit NOT read
155: aload_1
156: ldc           "resource.limit"
158: aconst_null
159: invokeinterface Feature.get:(String,String)String
...
179: invokevirtual update()
```

`ifeq` branches when the value is `0`/`false`. So the method returns EARLY (skipping the `resource.limit`
read entirely) when `isUsingCapacityLicensing()` is TRUE, and only reads/acts on `resource.limit` when it is
FALSE — the OPPOSITE polarity from [Block 11] §11.5's inference. `[CERT]` — re-run live this session,
matches the Vineflower decompile 1:1:

```java
if (!Metrics.isUsingCapacityLicensing()) {
   String limit = feature.get("resource.limit", null);
   if (limit != null && !limit.equalsIgnoreCase("none")) {
      this.update();
   }
}
```
`[CERT]` `ResourceManager.java:110-115` (this block's own read of [Block 6]/[Block 11]'s existing
`baja.jar` Vineflower extraction).

**This is a DE-ESCALATION, not a new finding requiring fresh evidence**: the SAME method logic is
byte-for-byte identical (module-rename/refactor-only `diff`) to N4's `ResourceManager.checkLicense` —
`diff niagara-research/…/ResourceManager.java niagara5-research/…/ResourceManager.java` shows only import
renames (`javax.baja.*`→`niagara.*`), a `Logger`/`lock` field-naming refactor, and one N5-only logging
upgrade (`printStackTrace()`→`LOG.log(SEVERE,…)` in the daemon-thread catch block) — the `checkLicense()`
method body itself is UNCHANGED. `[CERT]` (full `diff`, 87 lines changed, zero of them inside
`checkLicense()`'s logic). And **N4's OWN corpus already had this right**: `niagara-research`'s B488
§488.2 row 32 reads `resource.limit | ResourceManager.checkLicense:109-114 (only when NOT
capacity-licensing) | station | ResourceReport.platStationFault→Station.setStationFault` — i.e. N4's
manual analysis (line-range `109-114`, almost identical to N5's `110-115`) already stated the correct
"only when NOT capacity-licensing" polarity, TWO focuses before [Block 11]'s bytecode-offset-only N5 read
inverted it. `[CERT]` `niagara-mental-model-bloque488.md:32`.

**Why [Block 11]'s corpus-search found no counterpart**: B11 §11.5/§11.11 searched
`corpus-nav.py find "CapacityLicensing"` (one camelCase token) and got zero hits, hedging the finding as
`[INFER — corpus-absence, not proven N4-absence]`. That hedge was well-placed: B488's own prose writes
"capacity-licensing" (hyphenated, lowercase) and never spells the literal method name — a **literal-string
search miss, not a real absence**. `[CERT]` (direct `grep` of `niagara-mental-model-bloque488.md` for both
`isUsingCapacityLicensing` and `capacity-licensing`: zero hits on the first, one hit on the second, at the
exact `resource.limit` row).

**`Metrics.isUsingCapacityLicensing()` itself, and the whole `driverCapacity*` sub-licensing mechanism it
gates, is ALSO NOT new to N5** — `diff`-ed against N4's own `Metrics.java`/`GlobalGroup.java`/`SubGroup.java`/
`Group.java`, every one of these N5 files is logic-identical to its N4 namesake (191/22/14/15 diff-lines
respectively, 100% import-rename + Java-version cosmetic refactor — variable renames `lock`→`LOCK`,
`Set.of(...)` for `Collections.unmodifiableSet(new HashSet<>(...))`, char→String concat style, one added
defensive `startsWith("driverCapacity")` check in the Spy display path, `MetricSpy.write()`; **zero logic
deltas**). `[CERT]` `diff` of all four files. N4's own B488 §488.2 row 38 already documents
`driverCapacity*` sub-limits at `SubGroup:19-21`/`Metrics.findSubGroup:286`/`loadSubGroups:298-311` —
line-numbers essentially unchanged from N5's `SubGroup.java:14-31`/`Metrics.java:287-312`. `[CERT]`

**What `isUsingCapacityLicensing()` actually IS**: `return global.isGlobalEnabled || !moduleGroups.isEmpty();`
(`Metrics.java:240-244`) — TRUE when EITHER the station-wide `tridium:globalCapacity` feature is present
(`GlobalGroup`'s constructor sets `isGlobalEnabled=true` only on successful `feature.check()`,
`GlobalGroup.java:20-49`) OR at least one `tridium:driverCapacity<X>` per-module-group feature is present
(`SubGroup`, loaded by `loadSubGroups()` scanning ALL licensed features for a `driverCapacity`-prefixed
name, `Metrics.java:299-312`). **It is not a separate, mutually-exclusive licensing MODE — it is the
existing `globalCapacity`/`driverCapacity*` feature-presence check** ([Block 6] §6.1's `niagara.license.Feature`
API, [Block 11] §11.4's `globalCapacity` row), generalized to "any capacity-shaped feature is present."
`[CERT]` — closes [Block 11]'s **B11-G1** open question ("new N5-new licensing MODE, or an existing-but-
previously-unenumerated N4 mechanism?") in favor of the SECOND option: existing, unenumerated (by a literal-
string search), unchanged.

**What `resource.limit` does when read**: unlike every OTHER `*.limit` in [Block 6]/[Block 11]/B488's map
(which either `System.exit(-3)`, throw, or raise a component `fatalFault`), `resource.limit`'s ONLY observed
effect is `this.update()` — an IMMEDIATE (out-of-cycle) resource-report refresh (`ResourceManager.java:113`,
normally run every 60s by the daemon thread, `:139-141`), which THEN feeds `ResourceReport.platStationFault()`
→ `Station.setStationFault()` per B488's own citation (not independently re-traced this session, remitted).
`[CERT]` on the immediate-`update()` call; the `platStationFault`/`setStationFault` DOWNSTREAM effect is
B488's finding, not re-verified here.

## 34.7 — B6-G2 closure: `security/licenses/conf/<hostid>/` is `AuthenticatedLicenseRetrievalUtil`'s cache, a THIRD, perpetual-license bootstrap package `[CERT]`

[Block 6] §6.7/§6.13 left the live install's `security/licenses/conf/<hostid-shaped-name>/` directory as an
unexplained artifact — `com.tridium.sys.license.LicenseDatabase` (the class B6 decompiled) creates `db/`
under the perpetual license root, never `conf/`. This block finds the answer in a THIRD `nre.jar` package,
`com.tridium.nre.license` (distinct from BOTH `com.tridium.nre.subscription` §34.1-34.5 AND `baja.jar`'s
`com.tridium.sys.license*` [Block 6] scope), containing exactly one class:

```java
private static File getLicenseAccessKeyDirectory(String hostId) {
   File licenseDirectory = NiagaraFiles.getPerpetualLicensePath();
   return new File(licenseDirectory, "conf" + File.separator + hostId);
}
```
`[CERT]` `AuthenticatedLicenseRetrievalUtil.java:137-140`, where `NiagaraFiles.getPerpetualLicensePath()` =
`getWritableSecurityPath()/licenses` = `<niagara.config.home>/security/licenses`
(`NiagaraFiles.java:119-121,127-129`) — i.e. exactly `security/licenses/conf/<hostId>/`, matching the live
install's directory shape (§6.8's `WINN5-`-prefixed HostId-shaped name) byte-for-byte. `[CERT]` — this
CLOSES **B6-G2**.

**What this package does**: `AuthenticatedLicenseRetrievalUtil` manages a `licenseInfo.xml` file at
`conf/<hostId>/licenseInfo.xml` (`getLicenseAccessKeyFileName():133-135`) holding a per-`brandId`
"LicenseAccessKey" — a UUID-FORMAT credential (`isLicenseAccessKeyFormatValid()` parses it as
`UUID.fromString`, `:34-46`), AES-encrypted via the same `KeyRing`/`SecurityInitializer` infrastructure as
§34.1's subscription cache files, under key alias `"com.tridium.licensing.LicenseAccessKey"`
(`:28,59,86`). `[CERT]` `AuthenticatedLicenseRetrievalUtil.java:26-163` (whole file, 163 lines).

**Read side** (`readLicenseAccessKey(hostId)`, `:48-69`): reads `licenseInfo.xml`, extracts the
`<brandId licenseAccessKey="…">` attribute, decrypts it via `Aes256PasswordEncoderUtil.decodePassword()`.
**Write side** (`createLicenseAccessKeyFile()`, `:75-104`): builds `<licenseInfo hostId="…"
version="…"><brandId name="…" licenseAccessKey="…encrypted…"/></licenseInfo>` and writes it.
**Network side**: `getLicenseAccessKeyFromResponse(String jsonResponse)` (`:149-153`) parses a
`{"licenseAccessKey": "…"}` JSON field from SOME response — no HTTP call site is defined IN this class (it
takes an already-fetched JSON string), so the actual caller/endpoint that populates this key is OUTSIDE this
one-class package, not traced this session. `[CERT]` on the class's own methods; the caller is unresolved —
named **B34-G3**.

**Relationship to the subscription flow (§34.1-34.5)**: this is a SEPARATE, PERPETUAL-license-oriented
authenticated-retrieval mechanism — `DEFAULT_LICENSE_BRAND_ID = "tridium"` (`:27,71-73`), keyed by HostId +
brandId, permission-gated by `NiagaraBasicPermission.GET_LICENSE_ACCESS_KEY_PERMISSION` (`:49,76`) — DISTINCT
from `NiagaraBasicPermission.ENTITLEMENT_WORKFLOW_PERMISSION`/`GET_ENTITLEMENT_PRIVATE_KEY_PERMISSION` gating
every subscription-flow write in §34.1. `[CERT]` — a genuinely separate permission class, consistent with a
genuinely separate feature (likely backing a Workbench "download my license using an access key" flow, distinct
from subscription self-registration) — not independently confirmed against a UI/caller this session, named
**B34-G4**.

## 34.8 — N4 comparison summary `[CERT]`/`[INFER]`

| Question | N5 (this block) | N4 comparator | Verdict |
|---|---|---|---|
| Does `com.tridium.nre.subscription` exist in N4's `nre.jar`? | 24 classes, `nre.jar` | not decompiled by the `niagara-research` corpus (`nre.jar` internals are largely `javax.baja.license`/`com.tridium.sys.license`-side per B477/B480/B481; N4's OWN client-side transport package was not independently located this session) | `[INFER]` — not settled; named **B34-G5** |
| `resource.limit` polarity | only when `!isUsingCapacityLicensing()` | same, B488 §488.2 row 32 (pre-existing, correctly stated) | **UNCHANGED**, `[CERT]` |
| `Metrics`/`GlobalGroup`/`SubGroup`/`Group` logic | identical to N4 (diff = cosmetic only) | B488 §488.1-488.2 | **UNCHANGED**, `[CERT]` |
| `driverCapacity*` sub-licensing | present, `SubGroup` | present, B488 §488.2 row 38 | **UNCHANGED**, `[CERT]` |
| `EntitlementCheck`/`KeyRotationCheck` cadence (6h/90d) | not re-derived here (already [Block 6] §6.11) | B477/B481/B487/B1144 | **UNCHANGED** per [Block 6] §6.14, not re-verified this session |
| `security/licenses/conf/<hostid>/` | `AuthenticatedLicenseRetrievalUtil`'s LicenseAccessKey cache (`nre.jar`) | no `security/licenses/conf` hits anywhere in the `niagara-research` corpus (per [Block 6] §6.7's own grep) | possibly **N5-only or simply undocumented in N4's corpus** — `[INFER]`, named **B34-G6** |

## 34.9 — Open questions / unresolved contradictions

- **[C1]** [Block 11] §11.5 asserted `resource.limit` is read "only when `isUsingCapacityLicensing()` returns
  `true`" `[CERT — pipeline output, not individually spot-verified]`; this block, re-reading the live
  bytecode's branch condition and the Vineflower source, finds the OPPOSITE (`only when ... returns FALSE`)
  `[CERT]`, matching N4's own pre-existing B488 finding. This is a DE-ESCALATION of [Block 11] §11.5's
  specific polarity claim (not of B11's overall census, which remains sound elsewhere) — not pushed to a
  corpus `CONTRADICTIONS.md` (this corpus has none yet, same convention as [Block 6]/[Block 11]) but
  recorded here per METHODOLOGY §11's de-escalation guidance, and [Block 11] itself is left unedited (only
  cross-referenced) per this task's read-only/single-file-write constraint.

## 34.10 — Self-verification

**Token check.** Every load-bearing citation above (`isUsingCapacityLicensing`, `resource.limit`,
`heap.limit`, `driverCapacity`, `conf`, `getLicenseAccessKeyDirectory`, `AlwaysTrustManager`, `canCheckTpk`,
`TPK.length`, `ifeq`, `ES256`, `RETRIEVE_ENTITLEMENTS_RETRY_TIMEOUT`, `LICENSE_REVOKED`,
`regenerateNreId`, `.ecKeyPair.r1`, `reregistrationCause`) was `grep`-confirmed present in its cited source
file, or directly read off the live `javap`/Vineflower output reproduced above, immediately before being
written — 16 tokens checked.

**DECOMPILED-TREE BLOCK — per METHODOLOGY §11's explicit convention**: every `[CERT]` citation in this
block points into `organized/_bin-ext/nre/vineflower/**` or `organized/baja/vineflower/**` (decompiled
trees) or into the `niagara-research` sibling corpus (a DIFFERENT corpus root) — `verify-block.sh`/
`verify-state.sh` were not run (this corpus's layout, like [Block 6]/[Block 11], carries no
`research-sdd` kit checkout, and even if it did, every citation here would resolve `extern`). Citation gate
= 100% inline token-verify, declared explicitly per §11's requirement:
`verify-block: 0 resolved (all extern — decompiled trees + cross-corpus); citation gate = inline
token-verify 16/16 tokens`.

**Marker tally** (mechanized `grep -c`, run against this file after writing it — literal output, not
hand-recalled):

```
$ grep -o '\[CERT\]' /home/cristian/niagara5-research/niagara5-block34.md | wc -l
      48
$ grep -o '\[CERT — negative existence' /home/cristian/niagara5-research/niagara5-block34.md | wc -l
       2
$ grep -o '\[CERT — pipeline output' /home/cristian/niagara5-research/niagara5-block34.md | wc -l
       2
$ grep -o '\[INFER\]' /home/cristian/niagara5-research/niagara5-block34.md | wc -l
      12
```

RAW vs ADJUSTED (METHODOLOGY §11): of the raw counts above, one `[CERT — negative existence` hit is the
header's own MARKER-LEGEND line (§ blockquote, not a claim), one `[CERT — pipeline output` hit is a marker
QUOTED FROM [Block 11] §11.5 for correction purposes (§34.9's `[C1]`, not this block's own claim), and the
second `[CERT — pipeline output` hit is this self-verify section's own `grep` COMMAND TEXT matching its own
search pattern reflexively (the code fence above literally contains the string being searched for). Stripping
these three non-claim/self-referential hits: ADJUSTED `[CERT]`-family ≈ 48 + 1 + 0 = 49 own claims.
Raw `[INFER]` similarly includes the header legend line (1) and this section's own prose describing the
ratio/count (2-3 self-referential mentions of the literal token `[INFER]` inside sentences ABOUT `[INFER]`,
§34.10 itself) — ADJUSTED `[INFER]` ≈ 8 own claims (§34.3, §34.4 ×2, §34.5, §34.8 ×2, plus one in §34.9's
correction discussion).

Adjusted ratio `[INFER]`/`[CERT]`-family ≈ 8/49 ≈ **0.16** — low, consistent with an evidence-dominant
block: most claims are direct `diff`/`grep`/`javap` reads of two decompiled trees plus one live bytecode
re-run; `[INFER]` is reserved for (a) exploitability-in-this-build conclusions resting on an observed
non-empty byte array rather than a live-tested dev build (§34.4), (b) the `.cloned`/backup-restoration
write-site attribution gaps (§34.3, →B34-G1/G6), (c) reconciling "sealed" with the JLS-implicit reading
(§34.5), and (d) the N4-side `nre.jar` client-package comparator gap (§34.8, →B34-G5).

**Live spot-check performed this session** (not merely trusted from [Block 11]'s prior pipeline output):
`javap -c -p -classpath /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar
com.tridium.sys.resource.ResourceManager`, full `checkLicense(Feature)` method disassembly re-read live this
session — the exact `ifeq 155` branch that settles §34.6's correction.

**Artifacts.** This file exists at `/home/cristian/niagara5-research/niagara5-block34.md`. Per the task's
explicit instruction, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were NOT updated (no other file was
touched this session), and no commit was made.

## 34.11 — Connections

- **[Block 6]** — direct closure of **B6-G1** (`com.tridium.nre.subscription`/`EntitlementApi` bootstrap,
  §34.1-34.5) and **B6-G2** (the `security/licenses/conf/<hostid>/` directory, §34.7). Confirms [Block 6]
  §6.11's `SubscriptionLicenseManager` findings (`SecurityUtil.doPrivileged`, JSON-library swap, testability
  `exitConsumer` hook, `periodicCheckFailureCount` reset) are the `baja.jar` SIDE of the SAME bootstrap this
  block documents from the `nre.jar` side — §34.3 shows exactly how the two compose (6h outer job calling a
  5-minute-budget inner retry).
- **[Block 11]** — direct closure of **B11-G1**, with a CORRECTION of §11.5's inferred `resource.limit`
  polarity (§34.6), confirmed against both live bytecode and N4's own pre-existing B488 finding. Does not
  revisit B11-G2/G3/G4 (OEM absence, dynamic call-site values, source-line upgrade) — out of this block's
  assigned scope.
- **[Block 3]** — every write path in `com.tridium.nre.subscription`/`com.tridium.nre.license` routes
  through `niagara.nre.util.SecurityUtil.checkPermission()`/`doPrivileged()` (§34.1's `.refreshIncrement`/
  `.restoreId`/`.ecKeyPair` writers, §34.4's registration flow) — the same `SecurityAgent`-routed permission
  model [Block 3] documents, now traced through the subscription-licensing package specifically, alongside
  [Block 6] §6.9's two `baja.jar`-side call sites.
- **[Block 25]** — §34.5 checks `EntitlementApi.EntitlementState` against B25's Java 17+ language-feature
  census and finds it is a plain enum (implicitly closed by the JLS), not an explicit `sealed`
  class/interface — a scoping note for whoever cited it as "sealed," not a contradiction of B25 itself
  (B25 was not re-opened to confirm what it counted).
- **`niagara-research` B488** — the N4-side comparator for §34.6's whole capacity-licensing map; its
  §488.2 row 32 already had the `resource.limit` polarity right, which is how this block catches [Block 11]
  §11.5's inversion.
- **`niagara-research` B477/B481/B487/B1144** — the N4-side comparator for §34.3's grace-period/failure-mode
  discussion (6h `EntitlementCheck` + jitter, 90-day `KeyRotationCheck`, `Nre.licenseFailure()`) — remitted,
  not re-derived, since [Block 6] §6.14 already established these cadences are unchanged in N5.

---

## Child gaps opened this block

- **B34-G1** — `registration.metadata.reregistrationCause="backup-restoration"`'s WRITE site was not found
  in `com.tridium.nre.subscription`; trace the caller (likely a platform/backup-restore module outside this
  package) that sets this flag before a re-registration.
- **B34-G2** — `SecurityConstants.canCheckTpk()`'s gate condition (`TPK.length == 0`) was confirmed as CODE,
  but no dev/unsigned N5 build was available to confirm the TLS-trust-bypass branch is actually LIVE-REACHABLE
  there; needs a dev-build install to close.
- **B34-G3** — `AuthenticatedLicenseRetrievalUtil.getLicenseAccessKeyFromResponse()`'s CALLER (the HTTP
  endpoint that returns `{"licenseAccessKey": "…"}`) was not located in the classes read this session; likely
  another `com.tridium.nre.*` or Workbench-side class not yet decompiled/read.
- **B34-G4** — Confirm the Workbench-side UI/workflow that consumes `AuthenticatedLicenseRetrievalUtil`
  (a "download license via access key" feature, inferred from the class's shape, not confirmed against a
  caller).
- **B34-G5** — Locate and decompile N4's OWN client-side subscription-transport package (if
  `com.tridium.nre.subscription` or an N4-namesake exists in the `niagara-research` corpus's own `nre.dll`/
  `nre.jar`-equivalent extraction) to give §34.8's N4-comparison row a real answer instead of `[INFER]`.
- **B34-G6** — Confirm whether `security/licenses/conf/` is genuinely N5-only or simply an N4-corpus
  documentation gap (the `niagara-research` corpus's own `nre.jar`/native decompile scope for this exact
  class was not checked this session).
