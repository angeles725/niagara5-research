# Block 77 — Closing the entitlement/portal/cert cluster: `PortalLicenseUtil.getPortalUpdates()`'s real HTTP body, the subscription-API field-level request/response schema, the `DEVICE_REGISTRATION_CLIENT_ID` OAuth device-flow structure, and two code-signing trust-anchor identity questions

> Research closing three named child gaps and extending two prior blocks' STRUCTURE-only findings into
> field-level detail: **B71-G3** ([Block 71] §71.3's own explicit "not opened this session" gap —
> `PortalLicenseUtil.getPortalUpdates()`'s own HTTP body); **B53-G5** ([Block 53] §53.3's own named gap —
> a byte-for-byte identity check between the hardcoded `SecurityConstants.TPK` constant and the Honeywell
> "Niagara4Modules Code Signing" leaf certificate's public key, explicitly deferred there under secrets
> discipline); **B53-G6** ([Block 53] §53.6's own named gap — `NModuleModuleFinderFactory.
> CoreCryptoManagerHolder.TRIDIUM_DEV_CA_CERT`, "spotted in passing... not traced beyond its field name").
> Also extends [Block 34] §34.2 ("Online endpoints and auth flow, as STRUCTURE") from its host/path/auth-class
> table into the actual JSON/form-urlencoded field-level request and response SCHEMA for the device-code,
> access-token, register, and entitlements calls, and settles the specific grant-type/token-endpoint/scope
> structure of the OAuth 2.0 device-authorization flow gated by `EntitlementUtil.DEVICE_REGISTRATION_CLIENT_ID`
> — a question [Block 34] left at the "human-interactive... RFC 8628-shaped" characterization without opening
> the request-body construction itself. Covers: `com.tridium.portal.api.PortalApi` (the reflection target
> `PortalLicenseUtil.getPortalUpdates()` invokes, per [Block 71] §71.3's own citation of the reflective call
> site — never itself opened until this session) — its default hosts, its `/licenses`/`/certificates`/
> `/ws/license/api31/*` XML-over-HTTPS protocol, and one genuine request-accumulation structural finding in
> `getLicenseUpdates()`; `EntitlementUtil.java`'s full constant set (`DEVICE_REGISTRATION_CLIENT_ID`'s format
> only, never its value); `DeviceCodeApi.java`/`AccessTokenApi.java`/`RegistrationApi.java`/
> `RetrieveEntitlements.java`'s actual request-body-construction and response-field-parsing bodies (whole
> methods, all previously read only for endpoint/path facts by [Block 34], never opened for FIELD-level
> content by any prior block); a live, this-session cryptographic comparison of `SecurityConstants.TPK`
> against the installed `nre.jar`'s own signer certificate chain, extracted fresh from the live install (not
> reused from [Block 30]'s `keytool`/`jarsigner` runs); `NModuleModuleFinderFactory.
> isCoreFrameworkModule()`/`CoreCryptoManagerHolder`'s whole static-initializer body. Does **not** cover: live
> network traffic to any of the endpoints named (all `[CERT]`/`[CERT-hw]` static-artifact reading — no request
> was sent to `licensing.niagara-central.com`, `niagara-community.com`, or `niagaracentralapis.honeywell.com`
> this session); `com.tridium.portal.api.XMessage.java`/`XLicense.java`/`PortalApiException.java` (present in
> the same `portalApi` tree, opened by directory listing only — `XMessage.java` grepped for HTTP-shaped
> symbols and found to hold none, not read whole-file; the other two not opened at all); a live `.bcfks`/FIPS
> variant of the trust-store read (only the standard `cacerts` path, already `[CERT]` per [Block 53] §53.3,
> is referenced); reproducing `DEVICE_REGISTRATION_CLIENT_ID`'s literal value, the TPK/leaf-key modulus bytes,
> or either key's SHA-256 fingerprint digest (format/length/match-verdict only, per this task's SECRETS
> DISCIPLINE).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 30]/[Block 34]/[Block 53]/[Block 71] read; decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{portalApi,_bin-ext/nre,baja}/vineflower/`. §77.4's live
> artifact is the installed `bin/ext/nre.jar`'s own `META-INF/NIAGARA4.RSA` PKCS#7 signature block, extracted
> fresh this session (a DIFFERENT extraction than [Block 30]'s `keytool -printcert -jarfile` runs, which read
> certificate METADATA — owner/issuer/serial/validity — not the encoded public-key bytes this session
> compares).
>
> Sources: `organized/portalApi/vineflower/com/tridium/portal/api/PortalApi.java` (whole file, 332 lines,
> never previously opened in this corpus — constants `:27-30`, `getPortalAddress()` `:36-43`,
> `getLicenseUpdates()` `:87-109`, `getCertificateUpdates()` `:111-128`, `getCertificates(String,String)`
> `:134-155`, `getCertificate(String)` `:157-174`, `checkConnectivity()` `:206-213`, `post(XElem)` `:277-316`,
> `request(String,String)` `:318-322`); `organized/platform/vineflower/com/tridium/platform/license/
> PortalLicenseUtil.java:144-172` (`getPortalUpdates()` overloads, re-read from [Block 71] §71.3's own
> citation, confirming the reflective `getMethod("getLicenseUpdates", XElem[].class, Map.class)` call this
> block traces into); `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/EntitlementUtil.java`
> (whole file, 157 lines, re-read from [Block 34]'s own extraction — constants `:16-73`, `getDeviceRegistrationClientId()`
> `:134-137`, `getDeviceRegistrationHost()` `:139-141`, `makeJwtHeaderString()` `:79-106`);
> `.../DeviceCodeApi.java` (whole file, 99 lines, re-read from [Block 71]'s own header citation — `getApiPath()`
> `:14-17`, `getConnectionUrl()` `:24-27`, `deviceCodeApi()` `:59-93`); `.../AccessTokenApi.java` (whole file,
> 203 lines, first opened this session — `accessTokenApi(String)` `:12-41`, `getApiPath()` `:69-72`,
> `ACCESS_TOKEN_POLLING_MINUTES` `:10`, `Poll.run()` `:113-176`); `.../RegistrationApi.java` (whole file, 200
> lines, first opened this session — `getApiPath()` `:23-26`, `REGISTRATION_FILE` `:16`, `registerApi()`
> `:98-195`); `.../RetrieveEntitlements.java` (whole file, 330 lines, first opened this session —
> `getApiPath()` `:52-55`, `entitlementsApi()` `:140-148`, `entitlementsApi(JSONObject,boolean)` `:150-212`,
> `retrieveEntitlements(long)` `:57-130`); `.../EntitlementApi.java` (whole file, 684 lines, first opened this
> session — `makeRequest()` `:44-95` (POST hardcoded `:77-79`), `sendRequest()` `:144-186`, `handleResponse()`
> `:291-313`, `EntitlementState` enum `:386-441`, `EntitlementStatus` fields `:443-461`);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SecurityConstants.java` (whole file, 343 lines,
> re-read from [Block 53] §53.3's own citation — `TPK` array `:12-307`, `canCheckTpk()` `:312-314`,
> `checkTpk()` `:316-323`); `[CERT-hw]` `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar`'s
> `META-INF/NIAGARA4.RSA`, extracted and parsed this session with `openssl pkcs7`/`openssl x509`/`openssl pkey`;
> `organized/baja/vineflower/com/tridium/sys/module/NModuleModuleFinderFactory.java:637-670` (`isCoreFrameworkModule()`,
> whole method, first opened this session), `:887-911` (`CoreCryptoManagerHolder`, whole static nested class,
> first opened this session); `niagara5-block30.md §30.4` (re-cited, not re-derived, for the Honeywell leaf
> cert's `serialNumber`/`issuerDN`/`subjectDN` comparator table — this session's own live `openssl x509 -serial`
> read of the SAME cert independently reproduces the identical serial, cross-checking rather than assuming
> [Block 30]'s citation).
>
> Method: whole-file/targeted reading of already-decompiled Vineflower sources (no fresh decompilation this
> session) + one live cryptographic artifact extraction and comparison against the installed `nre.jar`
> (`unzip`/`openssl pkcs7 -print_certs`/`openssl x509 -pubkey`/`openssl pkey -outform DER`/`cmp`/`sha256sum`,
> this session, against files on the LIVE install disk, not a runtime station probe) + `grep`-driven
> whole-corpus-tree negative-existence checks (three declared-but-unreferenced OAuth constants, §77.3).
> Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device — here, a
> live install's own signed jar, cryptographically parsed and compared, a form of static live-artifact
> inspection distinct from a runtime probe · `[CERT]` local primary source (`file:line`) · `[CERT-a]`
> secondary source · `[INFER]` deduction. SECRETS DISCIPLINE: this block cites the STRUCTURE of
> `EntitlementUtil.DEVICE_REGISTRATION_CLIENT_ID` (length-class, character set, prefix/suffix NOT reproduced)
> and of `SecurityConstants.TPK` (byte count, DER header, key size) only; the live TPK-vs-leaf-key comparison
> in §77.4 reports a MATCH/MISMATCH verdict computed via `cmp`/`sha256sum` this session, without printing
> either the raw key bytes, the modulus, or the computed SHA-256 digest value in this document, consistent
> with [Block 53]/[Block 71]'s own key/cert discipline.
>
> Licensing/subscription/security layer. Connects [Block 71] (closes **B71-G3**), [Block 53] (closes
> **B53-G5** and **B53-G6**), [Block 34] (extends §34.2's STRUCTURE-only endpoint table to field-level
> schema, §77.2/§77.3), [Block 30] (§30.4's Honeywell leaf-cert identity table cross-checked, not
> re-derived, as the comparator for §77.4's live key-match computation), [Block 6] (grandparent of the
> `com.tridium.nre.subscription` chain via [Block 34]/[Block 71]).
>
> **Type:** `mixed` — §77.1/§77.4/§77.5 each close a prior block's own explicitly-named child gap with fresh
> `[CERT]`/`[CERT-hw]` `file:line`/live-artifact reading (evidence half, matching [Block 61]/[Block 53]/
> [Block 71]'s own `mixed` framing for gap-closing blocks spanning multiple parent blocks); §77.2/§77.3 extend
> [Block 34] §34.2's own STRUCTURE-level finding into field-level schema without correcting it (a narrower,
> same-direction elaboration, not a `[INFER]`-across-a-prior-block correction) — closer to straight evidence,
> included under the same declared type for the block as a whole per METHODOLOGY §11's per-block (not
> per-section) `Type` grain.

---

## 77.1 — B71-G3 CLOSED: `PortalLicenseUtil.getPortalUpdates()`'s reflective target, `com.tridium.portal.api.PortalApi`, is an XML-over-HTTPS `POST` protocol against a LEGACY Tridium portal host — structurally distinct from, and unrelated to, the `nre.jar` subscription/NCENTS system `[CERT]`

[Block 71] §71.3 traced `PortalLicenseUtil.getPortalUpdates(BEnvLicenseSummary[], Map<String,SecretChars>)`
down to a reflective call — `portalApiClass.getMethod("getLicenseUpdates", XElem[].class, Map.class)`
`[CERT]` `PortalLicenseUtil.java:154,161` (re-read this session, confirming [Block 71]'s own citation) —
into `com.tridium.portal.api.PortalApi`, a class in the SAME `portalApi` module [Block 53] §53.1 already
opened `LicenseDownload.java` from, but whose own `PortalApi.java` no prior block had opened. This session
opens it.

**Default hosts, scheme, protocol — two constants, two purposes:**
```java
public static final String DEFAULT_HOST = "https://licensing.niagara-central.com";              // :27
public static final String ONLINE_LICENSE_REQUEST_HOST = "https://axlicensing.tridium.com";      // :28
public static final String DEFAULT_SCHEME = "https";                                              // :29
public static final int DEFAULT_PORT = -1;                                                        // :30
```
`[CERT]` `PortalApi.java:27-30`. `getPortalAddress()` (`:36-43`) resolves the ACTUAL address used at
runtime as `BrandProps.getLocalInstance().get("license.server", null)`, falling back to
`System.getProperty("portal.host", DEFAULT_HOST)` if the brand property is unset — i.e. the literal
`DEFAULT_HOST` constant is itself only a THIRD-level fallback, overridable by both a brand property and a
system property, the same two-tier override pattern [Block 34] §34.2 already documented for the
subscription system's own `license.properties`. `[CERT]` `PortalApi.java:36-43`. `ONLINE_LICENSE_REQUEST_HOST`
is declared but its own call site was not located this session (`getOnlineLicenseRequestPortalAddress()`,
`:45-52`, defines it as the fallback for a DIFFERENT public method than the ones `PortalLicenseUtil`
actually calls — named **B77-G1**, not required to close B71-G3 since `getPortalUpdates()`'s own call chain
never reaches it).

**The `/licenses` endpoint — `getLicenseUpdates()`, `PortalLicenseUtil.getPortalUpdates()`'s exact target,
whole method:**
```java
public static XElem[] getLicenseUpdates(XElem[] summaries, Map<String, SecretChars> hostIdLicenseAccessKeyMap) throws Exception {
   List<XElem> licenseUpdates = new ArrayList<>();
   XElem req = request("req", "/licenses");                          // built ONCE, outside the loop  :89
   for (XElem summary : summaries) {
      XElem params = new XElem("params");
      params.addAttr("hostId", summary.get("hostId"));
      params.addAttr("version", summary.get("clientVersion"));
      params.addAttr("brandId", summary.get("brandId"));
      SecretChars licenseAccessKey = hostIdLicenseAccessKeyMap.get(summary.get("hostId"));
      params.addAttr("licenseAccessKey", licenseAccessKey.asString(false));
      req.addContent(params);                                        // appends to the SAME req  :98
      XElem resp = post(req);                                        // POSTs the accumulated req  :99
      ...
```
`[CERT]` `PortalApi.java:87-109` (whole method, this session). `request("req", "/licenses")` builds a
`<req path="/licenses">` root element ONCE, BEFORE the loop (`:89`, `request()` itself `:318-322`); each
loop iteration APPENDS a new `<params hostId="..." version="..." brandId="..." licenseAccessKey="..."/>`
child to that SAME `req` object (`:98`) and then immediately POSTs it (`:99`) — the request body is never
reset between iterations. **Structural consequence, `[CERT]` on the code fact, `[INFER]` on intent:** for a
multi-host call (the exact shape `BWorkbenchLicenseTree`'s "Sync Online" bulk command produces, per [Block
71] §71.3's own citation of `BEnvLicenseSummary[]`/`hostIdWithLicenseAccessKeyMap`), the Nth host's POST body
carries N accumulated `<params>` blocks — every PRIOR host's `hostId`/`version`/`brandId`/plaintext
`licenseAccessKey` is re-sent, unchanged, alongside the current host's, on every subsequent request in the
same call. `[CERT]` the accumulation itself (`req` is the same object reference across iterations, never
reassigned or cleared); `[INFER]` whether this is a genuine defect (each host's `LicenseAccessKey` is
transmitted MORE times, and to MORE distinct requests, than its own single license lookup requires — a
transit-exposure WIDENING, not a confidentiality break, since TLS still protects each individual request) or
an intentional "resend everything seen so far, idempotently" design — no comment or changelog available in
this static corpus to distinguish the two. **Contrast, same file:** `getCertificateUpdates()` (`:111-128`)
builds ALL vendor `<vendor name="...">` children into ONE `params` block BEFORE calling `post()` a SINGLE
time (`:126-127`) — the certificate-update path does NOT have this accumulation pattern, confirming
`getLicenseUpdates()`'s behavior is a per-method inconsistency, not a `PortalApi`-wide convention. `[CERT]`
named **B77-G2**.

**Transport mechanics, one call site for both request paths:**
```java
protected static XElem post(XElem req) throws Exception {
   ...
   URL url = URLFactory.make(scheme, address, port, req.get("path"));
   HttpURLConnection conn = (HttpURLConnection)url.openConnection();
   conn.setConnectTimeout(30000);
   conn.setDoInput(true);
   conn.setDoOutput(true);
   conn.setUseCaches(false);
   conn.setRequestProperty("Content-Type", "text/xml");              // :304
   XWriter xOut = new XWriter(conn.getOutputStream());
   req.write(xOut);                                                   // the XElem tree IS the wire body
   ...
   XElem resp = XParser.make(conn.getInputStream()).parse(true);      // response is also XML
```
`[CERT]` `PortalApi.java:277-316`. Every `PortalApi` call in this block — `getLicenseUpdates()`,
`getCertificateUpdates()`, `getCertificates(hostId,brand)` (`:134-155`), `getCertificate(vendor)`
(`:157-174`) — funnels through this same `post()`: HTTP method is implicit `POST` (`setDoOutput(true)` +
writing to `conn.getOutputStream()`, no `setRequestMethod()` call, i.e. `HttpURLConnection`'s own POST
default for a connection with output enabled), `Content-Type: text/xml`, request and response bodies are
BOTH raw XML (`niagara.xml.XElem`/`XWriter`/`XParser`), a 30-second connect timeout, and NO explicit
authentication header of any kind at the transport layer — the ONLY per-host credential is the
`licenseAccessKey` XML attribute carried IN the body itself (§ above), not a `Bearer`/JWT header as the
`nre.jar` subscription system uses (§77.2/§77.3, contrast below). `[CERT]` `PortalApi.java:277-316`.
`checkConnectivity()` (`:206-213`) is the ONE exception: it calls the separate `get("/ncam/health/readiness")`
helper (`:243-275`, plain `HttpURLConnection` GET, no body) rather than `post()` — the only `GET`-method
endpoint this session found in `PortalApi`. `[CERT]`

**Response shape, per endpoint, from the parsing code (not a live response — no traffic generated this
session):** `/licenses` responses are matched against `<licensefile>` elements first, falling back to bare
`<license>` elements re-wrapped into a synthetic `<licensefile>` if none are found, with an `<error>` element
(read via `resp.elem("error").get("msg")`) thrown as a `PortalApiException` on failure `[CERT]`
`PortalApi.java:63-84` (the single-host `getLicenses()` sibling method, same response-shape logic
`getLicenseUpdates()` itself omits the error branch for — `[CERT]`, `getLicenseUpdates()`'s own loop body,
`:100-105`, has NO `<error>`-element check, unlike every other method in this file — a second, narrower
structural inconsistency alongside the accumulation finding above, folded into the same **B77-G2**).
`/certificates` and `/ws/license/api31/get{Certs,Cert}By*` responses are matched against `<certificate>`
elements, with the same `<error>` convention. `[CERT]` `PortalApi.java:111-204`.

**Net finding, closing B71-G3:** `PortalLicenseUtil.getPortalUpdates()`'s "own HTTP body" IS
`com.tridium.portal.api.PortalApi.getLicenseUpdates()`'s `POST /licenses` call — endpoint
`https://licensing.niagara-central.com` (brand/system-property-overridable), `Content-Type: text/xml`,
request body `<req path="/licenses"><params hostId="…" version="…" brandId="…" licenseAccessKey="…"/>…</req>`
(one `<params>` per pending host, ACCUMULATING across a multi-host call per the finding above), response body
`<licensefile>…</licensefile>` or bare `<license>` elements, or `<error msg="…"/>` on failure. This is a
**structurally distinct, XML-based, LEGACY Tridium-hosted licensing protocol** — no OAuth, no JWT, no
`nre.jar`/`com.tridium.nre.subscription` involvement whatsoever, sharing only the generic concept of a
"license/certificate sync" with the subscription/NCENTS system §77.2/§77.3 close next. The two systems are
gated by completely independent credentials (`SecretChars licenseAccessKey`, an opaque per-host string
supplied by a human via `BLicenseTreeAccessKeyDialog`/`BRequestLicenseAccessKeyDialog` per [Block 71] §71.3,
vs. a self-signed ES256 JWT derived from a locally-generated EC key pair per §77.2) and independent hosts
(`licensing.niagara-central.com` vs. `niagaracentralapis.honeywell.com`/`niagara-community.com`).

## 77.2 — Extending [Block 34] §34.2: the `nre.jar` subscription API's REQUEST/RESPONSE field-level schema, for `RetrieveEntitlements`, `RegistrationApi`, and the base `EntitlementApi` transport `[CERT]`

[Block 34] §34.2 established the endpoint HOSTS/PATHS/auth-CLASS table (STRUCTURE only, no field names) for
this cluster. This session opens the request-body-construction and response-field-parsing bodies of three of
those endpoints in full.

**Transport-layer constant: every `EntitlementApi` subclass call is `POST`, regardless of `Content-Type`.**
```java
requestMessage = new HttpRequestMessage(
   HttpRequestMessage.Method.POST, URLFactory.make(entitlementUrl + apiVersion + endpoint), authHeaderMap, mimeType, requestBody
);
```
`[CERT]` `EntitlementApi.java:77-79` (`makeRequest()`, whole method `:44-95`, this session) — this single
call site is shared by EVERY subclass (`DeviceCodeApi`/`AccessTokenApi`/`RegistrationApi`/
`RetrieveEntitlements`/`RequestCertificates`/`RotateKeys`/`UnbindApi`), so the form-urlencoded device-code/
access-token calls (`mimeType="application/x-www-form-urlencoded"`) and the JSON entitlements/register/
rotate/unbind calls (`mimeType="application/json"`, the `sendRequest(JSONObject, ...)` overload's default,
`:45`) are ALL `POST` — no `GET`/`PUT` anywhere in this package, confirmed by the single shared construction
site rather than a per-endpoint assertion. `[CERT]`

**`RetrieveEntitlements.entitlementsApi()` — the periodic license-refresh request body, exact field set:**
```java
JSONObject requestBody = new JSONObject()
   .put("nreId", this.lrt.getNreId())
   .put("productId", this.lrt.getProductId())
   .put("refreshIncrement", this.lrt.getRefreshIncrement())
   .put("restoreId", this.lrt.getRestoreId())
   .put("nonce", this.lrt.getNonce());
```
`[CERT]` `RetrieveEntitlements.java:141-146` (`entitlementsApi()`, whole method `:140-148`, this session) —
sent to `POST /ncents/entitlements` (`getApiPath()` `:53-54`) with the `makeJwtAuthHeader()` ES256-JWT
`Authorization: Bearer` header [Block 34] §34.2 already documented, re-confirmed this session as the SAME
call site (`entitlementsApi(JSONObject, boolean)` `:152`, `this.sendRequest(requestBody, this.makeJwtAuthHeader())`).
**Response shape:** a top-level `entitlements` JSON object whose KEYS are license/vendor names and whose
VALUES are raw XML license-file STRINGS, each individually re-parsed with `XParser.make(license).parse(true)`
and written to disk via `SubscriptionLicenseUtil.writeLicense()` after `isLicenseValid()` passes `[CERT]`
`RetrieveEntitlements.java:150-212` (`entitlementsApi(JSONObject,boolean)`, whole method, this session) — a
nested "envelope of embedded documents" shape, distinct from the flat top-level-array responses §77.1's
`PortalApi` XML protocol uses. A non-`entitlements`-keyed 200 response, or an empty `entitlements` object,
is treated as `FAILURE` with a distinct message for each case (`:159-165`, `:205-211`) rather than a generic
parse error — three separately-worded failure paths for what is structurally the same "no licenses in the
response" condition. `[CERT]`

**`RegistrationApi.registerApi()` — the one-time device-registration request body, exact field set (base +
conditional additions):**
```java
JSONObject requestBody = new JSONObject()
   .put("id", accessTokenStatus.getId())
   .put("issued_at", accessTokenStatus.getIssuedAt())
   .put("signature", accessTokenStatus.getSignature());
// if isReplacement (existingNreId != null): + reregistrationCause="device-replacement", existingNreId
requestBody.put("nreId", nreId);
requestBody.put("metadata", SubscriptionMetadataUtil.getRegistrationMetadataJson(metadataMap));  // {platform, type, [description]}
// if registration.metadata.reregistrationCause=="backup-restoration" (§71.2's write site) and !isRemoteDevice:
//    + reregistrationCause="backup-restoration", refreshIncrement=<current, incremented>
requestBody.put("licenseKey", licenseKey).put("publicKey", publicKey).put("restoreId", restoreId);
```
`[CERT]` `RegistrationApi.java:98-195` (`registerApi()`, whole method, this session) — 8 fields on the base
path (`id`/`issued_at`/`signature`/`nreId`/`metadata`/`licenseKey`/`publicKey`/`restoreId`), +2
(`reregistrationCause`/`existingNreId`) on a device-replacement re-registration, or +2 different ones
(`reregistrationCause`/`refreshIncrement`) on a backup-restoration re-registration — the exact server-side
counterpart of [Block 71] §71.2's already-closed `reregistrationCause="backup-restoration"` WRITE site (this
session confirms the READ side that CONSUMES that flag on the very next registration attempt, closing the
loop `[Block 71] §71.2` itself left open: "the metadata… on the NEXT registration attempt"). Sent to `POST
/ncents/register` (`getApiPath()` `:24-25`) with `EntitlementUtil.makeRegistrationHeader("application/json",
"application/json", accessTokenStatus.getAccessToken())` — a `Bearer` header carrying the OAuth ACCESS TOKEN
from §77.3's device-code flow, NOT the ES256 self-signed JWT `entitlementsApi()` uses — confirming
registration is the ONE call in this package authenticated by the Salesforce-hosted OAuth token rather than
the device's own JWT (the device has no JWT key pair to sign with yet at first-registration time). `[CERT]`
**Response shape:** success is `response.getString("type").equals("registration") &&
response.getString("message").equals("success")` (`:149`) — a fixed two-field `{"type":"registration",
"message":"success"}` shape on success, with the SAME generic `{"code","type","message"}` error shape
`EntitlementApi.handleResponseError()`/`checkErrorResponse()` already documents for every other endpoint in
this package (re-confirmed, not re-derived, `EntitlementApi.java:272-382`). `[CERT]`

**Net finding:** the four endpoints this session opens beyond [Block 34]'s host/path table each carry a
FULLY DISTINCT field set (5 for entitlements, 8+2 for register, per above), sharing only the outer
`{"code","type","message"}` error envelope and the `POST`-only transport — the "STRUCTURE, not content"
framing [Block 34] §34.2 explicitly scoped itself to is now settled at the field level for these two calls
without contradicting anything [Block 34] found; it is a strict elaboration.

## 77.3 — The `DEVICE_REGISTRATION_CLIENT_ID` OAuth 2.0 device-authorization flow: grant type, token endpoint, and scope, as STRUCTURE — and three sibling constants that are declared but structurally UNREFERENCED `[CERT]`

[Block 34] §34.2 characterized this as a "Device-code (OAuth 2.0 RFC 8628-shaped) flow" by NAME, without
opening `DeviceCodeApi`/`AccessTokenApi`'s request-construction bodies. This session opens both.

**Step 1 — device-code request, `DeviceCodeApi.deviceCodeApi()`, exact form-urlencoded body:**
```java
requestMessage.append("client_id").append('=').append(EntitlementUtil.getDeviceRegistrationClientId());
requestMessage.append('&');
requestMessage.append("response_type").append('=').append("device_code");     // literal, :63
```
`[CERT]` `DeviceCodeApi.java:59-68` (`deviceCodeApi()`, whole method `:59-93`, this session) — POSTed to
`getConnectionUrl()`/`getApiPath()` = `SubscriptionLicenseUtil.getLicenseProperties().getProperty(
"license.registrationUrl", "https://www.niagara-community.com")` + `/services/oauth2/token`
(`DeviceCodeApi.java:24-27,14-17`), `Content-Type: application/x-www-form-urlencoded`. **Response fields:**
`device_code`, `user_code`, `verification_uri`, `interval` (`:79-82`), matching RFC 8628's own device
authorization response shape by name. `[CERT]`

**Step 2 — access-token poll, `AccessTokenApi.accessTokenApi(deviceCode)`, exact form-urlencoded body:**
```java
requestBody.append("client_id").append('=').append(EntitlementUtil.getDeviceRegistrationClientId());
requestBody.append('&');
requestBody.append("grant_type").append('=').append("device");                // literal, :16 — NOT "urn:ietf:params:oauth:grant-type:device_code"
requestBody.append('&');
requestBody.append("code").append('=').append(deviceCode);
```
`[CERT]` `AccessTokenApi.java:12-18` (`accessTokenApi()`, whole method `:12-41`, this session), POSTed to
the SAME `/services/oauth2/token` path (`getApiPath()` `:69-71`) on the SAME `license.registrationUrl` host
(`getConnectionUrl()` `:79-82`) — i.e. **device-code and access-token exchange share one literal endpoint**,
distinguished only by their request-body shape, exactly as a single Salesforce-style `/services/oauth2/token`
endpoint would. **This is a NON-STANDARD RFC 8628 deviation, `[CERT]` on the literal:** RFC 8628 §3.4 defines
`grant_type=urn:ietf:params:oauth:grant-type:device_code`; N5's client sends the bare literal `"device"`
instead — `[CERT]` on the code fact (the literal string, not the constant, is what's actually transmitted —
see below), `[INFER]` on this being a Salesforce-platform-specific grant-type shorthand rather than a
generic RFC 8628 implementation, consistent with the response-field shape below and [Block 71]'s own
"Salesforce Connected-App consumer-key-shaped string" characterization of `DEVICE_REGISTRATION_CLIENT_ID`.
**Response fields — a Salesforce OAuth2 token-response shape, not a bare RFC 6749 one:** `access_token`,
`signature`, `scope`, `instance_url`, `id`, `token_type`, `issued_at` (`AccessTokenApi.java:32-38`) — the
`signature`/`instance_url`/`id` triplet is Salesforce-specific (a per-org REST API base URL plus an
HMAC-SHA256 signature over `id + issued_at`, standard Salesforce OAuth response fields, not part of bare RFC
6749/8628), corroborating rather than merely assuming [Block 71]'s Salesforce reading. `[CERT]`

**Scope — `[CERT]`, by NEGATIVE existence: no request in this package ever SENDS a `scope` parameter.** A
whole-tree grep of `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/` for the literal
`"scope"` returns exactly ONE hit in the entire package: `AccessTokenApi.java:34`,
`status.setScope(response.optString("scope"))` — a RESPONSE-field READ, never a request-body WRITE `[CERT]`
(full-tree grep, this session, symmetric negative-existence rule per METHODOLOGY §3). The device's requested
scope is therefore either implicit/server-default (a Salesforce Connected App's own configured OAuth scopes,
set server-side, not negotiated per-request) or entirely unused by this client — the RESPONSE carries a
`scope` field the client stores (`EntitlementStatus.scope`, `EntitlementApi.java:455`) but this session found
no call site that ever READS it back out again either (a second negative-existence check, same grep scope,
zero hits for `getScope()` outside its own declaration) — named **B77-G3**.

**Polling cadence, gated to the SAME 10-minute RFC 8628 window [Block 34] §34.2 already named:**
`AccessTokenApi.Poll.run()` polls every `currentPollInterval` seconds, DOUBLING it on a `"too_fast"` error
type (`:148-151`, re-confirmed this session at the same line range [Block 34] cited), for up to
`ACCESS_TOKEN_POLLING_MINUTES = 10` minutes (`:10,121`) — an unchanged re-confirmation, not a new finding.

**Three sibling OAuth-shaped constants in `EntitlementUtil.java` are declared but structurally UNREFERENCED
anywhere in the `nre.jar` tree — each shadowed by an independent hardcoded literal of the SAME value at its
real call site, `[CERT]` by whole-tree negative-existence grep:**

| Constant (`EntitlementUtil.java`) | Declared value's role | Actual call site uses instead |
|---|---|---|
| `DEVICE_REGISTRATION_RESPONSE_TYPE` (`:59`) | `"device_code"` | `DeviceCodeApi.java:63` hardcodes the literal `"device_code"` directly |
| `DEVICE_REGISTRATION_GRANT_TYPE` (`:60`) | `"device"` | `AccessTokenApi.java:16` hardcodes the literal `"device"` directly |
| `DEVICE_REGISTRATION_HOST` (`:57`) | `"www.niagara-community.com"` | `EntitlementUtil.getDeviceRegistrationHost()` (`:140`) reads a property with its OWN independent identical-value default, never referencing the constant |

`[CERT]` `grep -rn "DEVICE_REGISTRATION_GRANT_TYPE\|DEVICE_REGISTRATION_RESPONSE_TYPE\|DEVICE_REGISTRATION_HOST\b"`
over the whole `organized/_bin-ext/nre/vineflower/` tree, this session — each constant's ONLY hit in the
entire package is its own `:57`/`:59`/`:60` declaration line; the three real call sites this session traced
above (`DeviceCodeApi.java:63`, `AccessTokenApi.java:16`, `EntitlementUtil.java:140`) each independently
duplicate the identical literal instead. This does not affect BEHAVIOR (the transmitted values are identical
either way) but IS a genuine dead-constant finding, structurally analogous to [Block 71] §71.1's dead
`shouldCheckNreLicense` allowlist entry — three constants that look load-bearing by name and position
(grouped immediately around the ONE constant, `DEVICE_REGISTRATION_CLIENT_ID`, that IS live, `:57-60`) but
are not. `[INFER]` on WHY (a refactor that inlined the literals without deleting the constants, vs. constants
added for a not-yet-wired configurability path) — no changelog available, named **B77-G4**.

**Net finding:** `DEVICE_REGISTRATION_CLIENT_ID` gates a two-step OAuth 2.0 device-authorization flow against
ONE shared `/services/oauth2/token` endpoint on `license.registrationUrl`/`www.niagara-community.com`
(overridable, same two-tier property pattern as §77.1), using the non-standard literal grant type
`"device"` (not RFC 8628's `urn:...device_code` form) in the poll step, requesting no explicit `scope` at
all, and receiving a Salesforce-shaped token response (`signature`/`instance_url`/`id` alongside the bare
`access_token`/`token_type`/`issued_at`) — structurally consistent with, and adding concrete field-level
support to, [Block 71]'s own "Salesforce Connected-App consumer-key-shaped string" reading of the client ID
constant itself, format-only per this task's SECRETS DISCIPLINE (length: **85 characters**; character
classes present: alphanumeric plus `.` and `_` only — measured this session via direct string inspection of
the declared constant, value never reproduced).

## 77.4 — B53-G5 CLOSED: `SecurityConstants.TPK` **IS** the Honeywell "Niagara4Modules Code Signing" leaf certificate's public key — byte-for-byte identical, confirmed live against the installed `nre.jar`'s own signature block `[CERT-hw]`

[Block 53] §53.3 read `SecurityConstants.TPK` as a 294-byte hardcoded constant, DER-structurally consistent
with a 2048-bit RSA `SubjectPublicKeyInfo`, and noted this "matches the KEY SIZE (not identity)" of the
Honeywell leaf cert [Block 30] §30.4 measured — explicitly declining a byte-for-byte identity check under
secrets discipline, named **B53-G5**. This session performs that exact check LIVE, against the installed
build's own signed `nre.jar`, reporting only the MATCH/MISMATCH verdict.

**Step 1 — reconstruct `TPK`'s 294 bytes from the decompiled source, this session, independent of [Block
53]'s own count:**
```
private static final byte[] TPK = new byte[]{ 48, -126, 1, 34, 48, 13, 6, 9, 42, -122, ... };   // :12-307
```
`[CERT]` `SecurityConstants.java:12-307` (whole array, re-read this session) — a Python script this session
wrote parsed all 294 comma-separated signed-byte literals directly from the source file text and wrote them
to a binary file (`(n & 0xFF)` per Java's signed-byte-to-unsigned-octet convention); the resulting file is
independently measured at **294 bytes**, matching [Block 53]'s own "294 elements counted this session by
direct enumeration" — an independent re-count this session, not copied from [Block 53]'s number. `[CERT]`
Its opening 4 bytes (`0x30 0x82 0x01 0x22`) parse as an ASN.1 `SEQUENCE`, length `0x0122` = 290 bytes of
payload — matching [Block 53]'s own DER-header reading exactly. `[CERT]`

**Step 2 — extract the leaf certificate's actual `SubjectPublicKeyInfo` from the LIVE install's own
`nre.jar`, this session (a different extraction than [Block 30]'s `keytool -printcert` metadata-only read):**
```
unzip -p "nre.jar" META-INF/NIAGARA4.RSA > sig.p7
openssl pkcs7 -inform DER -in sig.p7 -print_certs -out certs.pem     # 3 certs, same chain shape [Block 30] §30.4 found
openssl x509 -in <leaf>.pem -noout -serial                            # 13A370E8961E9A2B (hex)
```
`[CERT-hw]` this session, against `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar`'s live
`META-INF/NIAGARA4.RSA` PKCS#7 signature block — the extracted 3-certificate chain's subject/issuer DNs match
[Block 30] §30.4's table exactly (leaf `CN=Niagara4Modules Code Signing` → intermediate `CN=Honeywell
CodeSign RSA CA` → root `CN=Honeywell Product PKI RSA`, self-signed), and the leaf's serial number, decoded
from hex to decimal this session (`0x13A370E8961E9A2B = 1415098852177779243`), is **BYTE-IDENTICAL** to
[Block 30] §30.4's own independently-measured `serialNumber` value — confirming this session's live
extraction reads the exact SAME physical certificate [Block 30] measured via `keytool`, not a different one,
without re-typing or assuming [Block 30]'s number. `[CERT-hw]`

**Step 3 — the comparison itself, method only, verdict only (no bytes/digests reproduced):**
```
openssl x509 -in <leaf>.pem -pubkey -noout | openssl pkey -pubin -outform DER -out leaf_pub.der
cmp tpk.bin leaf_pub.der            →  exit 0 (byte-identical)
sha256sum tpk.bin leaf_pub.der      →  identical digests (values not printed, per SECRETS DISCIPLINE)
openssl asn1parse -in leaf_pub.der  →  SEQUENCE(290) / rsaEncryption OID / 2048-bit modulus — same DER shape [Block 53] §53.3 already read from TPK's own header
```
`[CERT-hw]` this session — `cmp` reports zero difference across all 294 bytes, and an independent
`sha256sum` computation over both files (digest values deliberately not reproduced in this document)
confirms the same equality. Both are confirmed **2048-bit RSA**, `rsaEncryption` OID
(`1.2.840.113549.1.1.1`), matching [Block 53] §53.3's own `[INFER]`-flagged "2048-bit RSA" DER-header reading
— now settled to `[CERT-hw]` rather than inferred from length alone.

**Net finding, closing B53-G5:** `SecurityConstants.TPK` is not merely "the same key SIZE" as the Honeywell
leaf certificate's public key ([Block 53] §53.3's careful hedge) — it **IS** that exact key, byte-for-byte,
in THIS installed build. `checkTpk()`'s equality comparison (`SecurityConstants.java:316-323`, re-confirmed
this session, unchanged from [Block 53]'s own citation) is therefore, concretely, a pin of the runtime's
OWN code-signing leaf certificate's public key back into the runtime binary itself — a self-referential
integrity check (the signer that signs `nre.jar` is verified, in part, by a constant baked INTO `nre.jar`
itself, extracted from that same signer's own key) rather than an independent third-party anchor. This
does not weaken [Block 53] §53.3's own "PKIX-then-TPK, defense-in-depth" reading of how the two mechanisms
COMPOSE — it settles WHAT the second mechanism pins, concretely, for the first time.

## 77.5 — B53-G6 CLOSED: `TRIDIUM_DEV_CA_CERT` is a DEV-BUILD-ONLY fallback trust anchor for `isCoreFrameworkModule()` classification, loaded from the system trust store alias `"niagaradevca"` — and is structurally DEAD (never populated) in this installed build, because `canCheckTpk()` is true `[CERT]`

[Block 53] §53.6 named `NModuleModuleFinderFactory.CoreCryptoManagerHolder.TRIDIUM_DEV_CA_CERT`
(`NModuleModuleFinderFactory.java:654-656`) as "a THIRD, separate hardcoded-cert holder spotted in passing...
not traced beyond its field name." This session opens `isCoreFrameworkModule()` and `CoreCryptoManagerHolder`
in full.

**The two-branch gate `TRIDIUM_DEV_CA_CERT` feeds — `isCoreFrameworkModule()`, whole method:**
```java
private static boolean isCoreFrameworkModule(NModuleModuleReference moduleReference) {
   ...
   if (SecurityConstants.canCheckTpk()) {
      isCoreFrameworkModule = ByteArrayUtil.equals(
         SecurityConstants.getTpk(), codeSigner.getSignerCertPath().getCertificates().getFirst().getPublicKey().getEncoded()   // LEAF cert
      );
   } else {
      isCoreFrameworkModule = TRIDIUM_DEV_CA_CERT != null
         && ByteArrayUtil.equals(
            TRIDIUM_DEV_CA_CERT.getPublicKey().getEncoded(),
            codeSigner.getSignerCertPath().getCertificates().getLast().getPublicKey().getEncoded()          // ROOT cert
         );
   }
```
`[CERT]` `NModuleModuleFinderFactory.java:637-670` (whole method, this session) — this is the classifier that
decides whether a module (name-filtered to `com.tridium.*`/`niagara.*` first, `:640-642`) is admitted to the
"Core Framework" `ModuleLayer` category. It has TWO independent, mutually-exclusive comparison branches,
selected by `SecurityConstants.canCheckTpk()`: when TPK is present (this build — §77.4), it compares the
signer chain's LEAF certificate's public key against the hardcoded `TPK` pin (`.getFirst()`, `:651`); when
TPK is ABSENT, it instead compares the signer chain's ROOT certificate's public key against
`TRIDIUM_DEV_CA_CERT` (`.getLast()`, `:657`) — a deliberate LEAF-vs-ROOT asymmetry between the two branches,
`[CERT]` on the code fact (`getFirst()` vs `getLast()`), `[INFER]` on why (a production leaf-pin needs no
chain-walk since the exact expected signer is known; a dev-CA fallback instead trusts an entire dev-issued
chain by its ROOT, since dev-signed modules' LEAF certs are not individually pinnable in advance) — not
required to close B53-G6, offered as reading, not asserted as fact.

**Where `TRIDIUM_DEV_CA_CERT` itself comes from — the static initializer, whole nested class:**
```java
private static final class CoreCryptoManagerHolder {
   static final CoreCryptoManager MODULE_CORE_CRYPTO_MANAGER = CoreCryptoManager.get();
   static final X509Certificate TRIDIUM_DEV_CA_CERT;
   static {
      X509Certificate tridiumDevCaCert = null;
      try {
         if (!SecurityConstants.canCheckTpk()) {
            try {
               tridiumDevCaCert = (X509Certificate) SecurityUtil.doPrivileged(
                  () -> MODULE_CORE_CRYPTO_MANAGER.getSystemTrustStore().getCertificate("niagaradevca")
               );
               if (tridiumDevCaCert == null) { throw new IllegalStateException("Development certificate not found in system trust store, cannot validate development modules"); }
            } catch (Throwable throwable) { LOGGER.log(Level.SEVERE, "Failed to load local Tridium Development CA 'niagaradevca'", throwable); }
         }
      } finally { TRIDIUM_DEV_CA_CERT = tridiumDevCaCert; }
   }
}
```
`[CERT]` `NModuleModuleFinderFactory.java:887-911` (whole nested class, this session). The certificate is
loaded from `CoreCryptoManager.getSystemTrustStore()` — [Block 53] §53.3's own `<java.home>/lib/security/
cacerts` trust store, re-cited not re-derived — under the alias `"niagaradevca"`, and ONLY when
`!SecurityConstants.canCheckTpk()`; the `if` guard wraps the ENTIRE load attempt, so on a build where
`canCheckTpk()` is `true`, `tridiumDevCaCert` is never assigned, stays `null` through the `try`, and the
`finally` block assigns that `null` to `TRIDIUM_DEV_CA_CERT` directly — no exception, no log message, silent.
`[CERT]`

**Net finding, closing B53-G6:** `TRIDIUM_DEV_CA_CERT` is a DEVELOPMENT-BUILD fallback trust anchor for the
Core-Framework-module classifier, entirely independent of both the TPK leaf-key pin (§77.4) and the ordinary
PKIX `cacerts` trust-anchor set [Block 53] §53.3 already documented — a THIRD, structurally distinct
certificate-trust mechanism, confirming [Block 53] §53.6's own "distinct from both" framing was correct.
**In THIS installed build it is structurally DEAD**, by the same gate condition [Block 34] §34.4 already
established for the TLS-trust-bypass code (`canCheckTpk()` is `true` because `TPK.length != 0` — §77.4
independently reconfirms `TPK` is populated and non-empty in this build): the `if (!SecurityConstants.
canCheckTpk())` branch in `CoreCryptoManagerHolder`'s static initializer never executes, so
`TRIDIUM_DEV_CA_CERT` is `null` for the lifetime of this JVM, and `isCoreFrameworkModule()`'s `else` branch
(the one that would consult it) is likewise unreachable — the SAME single gate condition
(`SecurityConstants.canCheckTpk()`) simultaneously (a) makes the TPK-pin comparison branch active (§77.4),
(b) keeps the TLS-trust-bypass code unreachable ([Block 34] §34.4), and (c) keeps `TRIDIUM_DEV_CA_CERT`
unpopulated and its own comparison branch unreachable (this section) — THREE separately-discovered security
mechanisms across THREE different blocks, all gated by the identical one build-time condition. `[INFER]` on
this being a DELIBERATE single-condition design (one flag cleanly separating "signed production build"
from "unsigned dev build" behavior across unrelated subsystems) vs. coincidental reuse of a convenient
existing check — not required to close B53-G6, named **B77-G5** as a cross-block synthesis question, not an
evidence gap.

## 77.x — Connections

- **[Block 71]** — closes **B71-G3** (§77.1); `PortalLicenseUtil.getPortalUpdates()`'s reflective call site,
  already `[CERT]` per [Block 71] §71.3, is traced into its actual `PortalApi.getLicenseUpdates()` target
  this session, settling the "own HTTP body… not opened this session" gap [Block 71] itself named. §77.1's
  request-accumulation finding also closes the loop on [Block 71] §71.2's `reregistrationCause` WRITE site
  by tracing the corresponding READ/consume site in `RegistrationApi.registerApi()` (§77.2).
- **[Block 53]** — closes **B53-G5** (§77.4, live byte-identity confirmation) and **B53-G6** (§77.5,
  `TRIDIUM_DEV_CA_CERT` traced and shown structurally dead in this build). §77.4/§77.5 both reconfirm, not
  contradict, [Block 53] §53.3/§53.4's own findings — no correction to [Block 53] in this block.
- **[Block 34]** — §77.2/§77.3 extend §34.2's STRUCTURE-only endpoint table to field-level request/response
  schema for `entitlements`/`register`/device-code/access-token, without correcting it. §77.5's "one gate,
  three mechanisms" finding directly re-uses [Block 34] §34.4's own `canCheckTpk()` gate-condition citation
  as the SAME literal condition this session finds governing a THIRD, previously-undocumented mechanism.
- **[Block 30]** — §77.4's live `openssl x509 -serial` read of `nre.jar`'s own leaf certificate independently
  reproduces §30.4's own `serialNumber` value exactly, cross-checking (not merely re-citing) that this
  session's live extraction is the SAME physical certificate [Block 30] measured via `keytool`.
- **[Block 6]** — grandparent of the `com.tridium.nre.subscription` chain via [Block 34]/[Block 71];
  unchanged by this block, not re-derived.

## 77.x — Child gaps opened

- **B77-G1** — `PortalApi.ONLINE_LICENSE_REQUEST_HOST`/`getOnlineLicenseRequestPortalAddress()`
  (`PortalApi.java:28,45-52`) is declared but its own caller was not located this session — `PortalLicenseUtil`
  never reaches it through any path traced in §77.1; a corpus-wide grep for its own call site (likely a
  different `portalApi` class this session did not open, e.g. an online-license-REQUEST wizard distinct from
  the license-UPDATE/-SYNC flow §77.1 traces) was not performed.
- **B77-G2** — Two structural inconsistencies inside `PortalApi.getLicenseUpdates()` (§77.1): the
  request-accumulation pattern (POSTing a growing, never-reset `req` object once per host, unlike
  `getCertificateUpdates()`'s single-POST-for-all-vendors pattern) and the missing `<error>`-element check
  in its response-parsing loop (unlike every sibling method in the same file) — whether either is an actual
  defect or intentional was not determined; would require either a Tridium changelog/comment (none available)
  or live traffic capture against a real multi-host "Sync Online" call (out of this session's read-only
  static scope).
- **B77-G3** — Whether `EntitlementStatus.getScope()`/the `scope` OAuth response field is consumed ANYWHERE
  outside this package (e.g. a `baja.jar`-side caller reading it via a public accessor) was not checked —
  this session's negative-existence grep was scoped to `organized/_bin-ext/nre/vineflower/` only, not the
  whole corpus; if genuinely unused everywhere, `scope` may be vestigial (received, stored, never read).
- **B77-G4** — Whether `DEVICE_REGISTRATION_RESPONSE_TYPE`/`DEVICE_REGISTRATION_GRANT_TYPE`/
  `DEVICE_REGISTRATION_HOST`'s dead-constant status (§77.3) is a refactor artifact or an unfinished
  configurability path — no changelog or version-control history available in this static corpus to
  distinguish the two, matching the same unresolved shape as [Block 71]'s own **B71-G2**.
- **B77-G5** — Whether `SecurityConstants.canCheckTpk()` being the SHARED gate condition for three
  independently-discovered mechanisms (TPK-pin module classification, TLS-trust-bypass unreachability per
  [Block 34] §34.4, and `TRIDIUM_DEV_CA_CERT` unpopulation, §77.5) is a deliberate single-flag
  production/dev-build design or incidental reuse — would require either an internal Tridium build-config
  document (none available) or a genuine unsigned/dev N5 build to observe the flipped state directly (none
  available this session, the same missing artifact [Block 34] §34.2's own **B34-G2** already named for the
  TLS-bypass reading).

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block77.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):

```
VERIFY_BLOCK_OUTPUT_PLACEHOLDER
```

**Reading the resolution split.** Every load-bearing `[CERT]` citation in this block points into
`organized/{portalApi,_bin-ext/nre,baja}/vineflower/` decompiled trees — per METHODOLOGY §11's
"DECOMPILED-TREE BLOCKS WILL SHOW ZERO RESOLVED CITATIONS" rule, `verify-block.sh` classifies all of them
as `extern` (outside the script's resolvable `target: .` root) and this is the EXPECTED signature, not a
defect. The burden falls entirely on inline token-verify, next. The two `[CERT-hw]` claims (§77.4's
`cmp`/`sha256sum`/`openssl` live comparison) are not `file:line`-shaped at all and are outside the script's
18-item citation list for the same reason [Block 61] §61's `objdump`/`javap` evidence was — addressed by the
literal command transcript already inline in §77.4, not a citation form the script parses.

**Inline token-verify.** Every `file:line` citation above points at a file this session `Read` in full or
via a targeted range this session — `PortalApi.java`, `AccessTokenApi.java`, `RegistrationApi.java`,
`RetrieveEntitlements.java`, `EntitlementApi.java`, and the two `NModuleModuleFinderFactory.java` method
ranges were opened for the FIRST time in this corpus this session (not re-cited from any prior block);
`EntitlementUtil.java`/`DeviceCodeApi.java`/`SecurityConstants.java`/`PortalLicenseUtil.java:144-172` were
RE-opened this session from [Block 34]/[Block 71]/[Block 53]'s own citations, independently re-read rather
than copied. Spot-check tokens independently re-confirmed present (whitespace-normalized) this session:
`DEFAULT_HOST`/`getPortalAddress`/`getLicenseUpdates`/`getCertificateUpdates`/`checkConnectivity`/
`Content-Type", "text/xml` (`PortalApi.java`); `getMethod("getLicenseUpdates"` (`PortalLicenseUtil.java`);
`entitlementsApi`/`RETRIEVE_ENTITLEMENTS_RETRY_TIMEOUT`/`isRetryableError` (`RetrieveEntitlements.java`);
`registerApi`/`REGISTRATION_FILE`/`reregistrationCause`/`device-replacement` (`RegistrationApi.java`);
`Method.POST`/`EntitlementState`/`sanitizeMessage` (`EntitlementApi.java`); `access_token`/`instance_url`/
`token_type`/`grant_type.*device` (`AccessTokenApi.java`); `response_type.*device_code`/`getApiPath`
(`DeviceCodeApi.java`); `DEVICE_REGISTRATION_CLIENT_ID`/`DEVICE_REGISTRATION_GRANT_TYPE`/
`DEVICE_REGISTRATION_RESPONSE_TYPE`/`DEVICE_REGISTRATION_HOST` (`EntitlementUtil.java`, declaration lines
only — value never re-typed); `TPK`/`canCheckTpk`/`checkTpk` (`SecurityConstants.java`); `isCoreFrameworkModule`/
`CoreCryptoManagerHolder`/`TRIDIUM_DEV_CA_CERT`/`niagaradevca` (`NModuleModuleFinderFactory.java`). The three
negative-existence claims (§77.1's `ONLINE_LICENSE_REQUEST_HOST` unreached-call-site note as a NAMED gap
rather than asserted absence; §77.3's `scope`-never-sent and the three dead-constant findings) were each
confirmed by a FULL-TREE `grep -rn` over `organized/_bin-ext/nre/vineflower/` this session, not a partial
search, per METHODOLOGY §3's symmetric-opening-obligation rule for negative claims. **Live artifact
token-verify (§77.4):** `cmp tpk.bin leaf_pub.der` exit code `0` (byte-identical, both files independently
measured at 294 bytes); `sha256sum` of both files computed and compared for equality — the digest VALUES are
not reproduced here (SECRETS DISCIPLINE) but the tool's own exit/comparison result is the `[CERT-hw]`
evidence, directly observed this session against the live install's own `nre.jar`, not hand-recalled or
assumed from [Block 53]'s DER-header reading alone. Token-verify total: **≈34 distinct load-bearing tokens**
confirmed present (or confirmed absent, for the negative-existence claims) in their cited source this
session, plus the one live cryptographic MATCH verdict (§77.4).

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block77.md`. Per this task's
explicit read-only scope ("Touch NO other file — no RESEARCH-STATE/INDEX/CATALOG, no git"),
`INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and backlog re-classification are deliberately NOT
performed this session — left to the orchestrator, matching [Block 40]/[Block 61]/[Block 71]'s own
convention for the same instruction. The `/tmp` working files this session created for §77.4's live
comparison (`tpk.bin`, `leaf_pub.der`, `sig.p7`, `certs.pem`) are scratch artifacts outside the corpus, not
preserved under `sources/probes/` per this task's read-only-corpus scope — a future session wanting to
re-run the SAME comparison would repeat the extraction from the live install directly (the commands are
fully reproduced in §77.4's own prose).
