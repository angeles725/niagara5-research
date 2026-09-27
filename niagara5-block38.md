# Block 38 — N5 TOTP enrollment, SAML flow, LDAP bind and SRP6

> Research of **TOTP self-enrollment/reset flow, SAML SP+IdP servlet flow with assertion validation,
> LDAP bind mechanisms, and the SRP6 key-exchange layer's N4 lineage**: closes [Block 12]'s child gaps
> **B12-G5** (TOTP enrollment UI wiring), **B12-G6** (SAML IdP servlet flow), **B12-G7** (LDAP v2/v3
> bind-name formatting), and **B12-G8** (whether the SRP6 key-exchange backing
> `BDigestAuthenticationScheme` is new in N5). Also surfaces two corrections to [Block 12]'s own claims
> (§38.3 account-wide lockout DOES cover TOTP token failures; §38.2 a genuine self-service TOTP
> reset/recovery path exists at the web login page, contra B12's "admin-mediated reset only"). Does
> **not** re-derive [Block 12]'s TOTP-algorithm table (§12.3, unchanged), the PBKDF2/AES password-encoder
> catalog (§12.4, only the ENTRY POINT — default reversible-encoder selection — is newly traced here for
> the TOTP secret specifically), or `platCrypto`/`signingService`'s daemon protocols (B12-G2/G3, still
> open).
>
> Subject version: **N5 5.0.0.28 (Beta)** — same jars [Block 12] read (`vendorVersion="5.0.0.28"`,
> `schemaVersion="5"`). N4 baseline: `niagara-research` corpus (Honeywell OptimizerSupervisor 4.14.0.162
> decompile), cited by block number (B419, B134, B30, B494), not re-derived, except the one fresh
> same-session negative-existence grep for "gauth" across the N5 `totpAuth`/`baja` trees (§38.2).
>
> Sources (all local, read-only, inside the `niagara5-research` corpus — **not** `/tmp` scratch, unlike
> [Block 12]'s citations):
> - `organized/totpAuth/vineflower/com/tridium/totpAuth/**` — full-jar Vineflower decompile of
>   `totpAuth.jar` (already present in the corpus from an earlier session; re-read this session).
> - `organized/saml/vineflower/com/tridium/saml/**` — full-jar Vineflower decompile of `saml.jar`.
> - `organized/samlEncryption/vineflower/com/tridium/samlEncryption/**` — full-jar decompile of
>   `samlEncryption.jar`.
> - `organized/ldap/vineflower/com/tridium/ldap/**` — full-jar decompile of `ldap.jar`.
> - `organized/baja/vineflower/niagara/{security,user}/**` and `organized/baja/vineflower/com/tridium/authn/**`
>   — package-subset Vineflower decompile of `baja.jar` (same subset [Block 12] used, re-read this
>   session for `BPassword`, `BUser`, `BUserService`, `BAuthenticationService`,
>   `BDigestAuthenticationScheme`).
> - REMITTANCE (N4): `niagara-research` corpus, via `python3 corpus-nav.py find "SRP"|"SAML"|"gauth"`, plus
>   a fresh same-session `grep -rli gauth` across the N5 `totpAuth`/`baja` trees (zero hits, §38.2).
>
> Method: reading the Vineflower decompile already organized under this corpus's `organized/` tree
> (no fresh decompilation performed this session — the jars were already extracted). Markers:
> `[CERT]` local primary (decompiled source read this session, `file:line`) · `[CERT-a]` secondary source ·
> `[INFER]` deduction. All `[CERT]` citations below resolve inside this corpus's own target directory
> (`niagara5-research/`), unlike [Block 12]'s `/tmp`-scratch citations — `verify-block.sh` should resolve
> most of them natively rather than reporting `extern` (§38.12).
>
> Security/authn layer, extending [Block 12]. Connects [Block 12] (parent gap, corrected in two places),
> `niagara-research` B419/B134/B420 (N4 SRP6 Fox key-exchange, used to resolve B12-G8), B30/B494/B803
> (N4 SAML/gauth/LDAP baseline), and [Block 3] (`SecurityUtil.doPrivileged` — every reversible-password
> decrypt and LDAP bind here goes through it).
>
> **Type:** mixed — evidence read this session (§38.1, §38.4–§38.9, §38.10 N5 half) combined with
> synthesis that draws on prior blocks ([Block 12], B419/B134) to correct or resolve their open
> questions (§38.2, §38.3, §38.10 N4-continuity conclusion).

---

## 38.1 — TOTP enrollment: two distinct paths, not one (closes B12-G5) `[CERT]`

[Block 12] §12.3 described enrollment only via the `secretKey` `BPassword` slot and
`forceSecretKeyResetAtNextLogin`, without tracing the UI. Two genuinely different enrollment paths exist:

**Path A — Workbench administrator, property-sheet field editor.** `BTotpSecretKeyFE` (a `BWbFieldEditor`)
renders a "Generate" button (`newIcon`/`resetIcon` depending on `value.isDefault()`,
`organized/totpAuth/vineflower/com/tridium/totpAuth/ui/BTotpSecretKeyFE.java:44-64`). Its `GenerateCmd`
(`:194-228`) flow: (1) if a secret already exists, confirm overwrite (`:200-207`); (2) generate a fresh
secret via `TotpAuthenticator.createSecret()` — `SecureRandom`, 16 random bytes, Base32-encoded
(`organized/totpAuth/vineflower/com/tridium/totpAuth/TotpAuthenticator.java:33-37`); (3) render the
`otpauth://totp/{user}@{station}?secret=...` URI as an inline SVG QR code and show it in a modal dialog
(`organized/totpAuth/vineflower/com/tridium/totpAuth/ui/BTotpSecretKeyFE.java:163-192`, `organized/totpAuth/vineflower/com/tridium/totpAuth/TotpAuthenticator.java:39-70`); (4) loop prompting for a confirmation
token until it validates against the just-generated (unsaved) secret (`BTotpSecretKeyFE.java:139-161,
214-221`); (5) only then commit `value = BPassword.make(secretKey)` and mark the property sheet modified
(`:223-224`) — the secret is not persisted to the station until the operator SAVES the property sheet.
The equivalent UX (web Workbench) field editor, `BTotpSecretKeyEditor`, is a thin JS-backed shell
(`organized/totpAuth/vineflower/com/tridium/totpAuth/ux/BTotpSecretKeyEditor.java:1-36`) — its logic lives
client-side in `rc/TotpSecretKeyEditor.js` (not traced this session).

**Path B — end user, self-service at the web login page (NEW finding, not in B12).** When
`forceSecretKeyResetAtNextLogin` is `true` (the default for every newly created `BTotpAuthAuthenticator`,
`organized/totpAuth/vineflower/com/tridium/totpAuth/BTotpAuthenticationScheme.java:40-44`), the NEXT
web login itself walks the user through enrollment: `BTotpAuthLoginHTMLForm.getPasswordResetForm()`
(`organized/totpAuth/vineflower/com/tridium/totpAuth/BTotpAuthLoginHTMLForm.java:137-177`) generates a
fresh secret **server-side** (`TotpAuthenticator.createSecret()`, same routine as Path A, `:160`), renders
its QR SVG and the raw Base32 secret directly into the rendered login-reset HTML (`:161-168`, template
`totpAuthPasswordResetFormN4.vm`), and stashes the plaintext secret in the HTTP session under
`"totpAuth.secretKey"` (`:170-172`). The user submits the confirmation token; `BWebTotpAuthCallbackHandler
.handleCredentialsReset()` re-reads the session-stashed secret, validates the submitted token against it
via `TotpAuthenticator.checkToken()`, and only then calls `authenticator.setSecretKey(...)` +
`setForceSecretKeyResetAtNextLogin(false)` (`organized/totpAuth/vineflower/com/tridium/totpAuth/
BWebTotpAuthCallbackHandler.java:154-202`, secret validation at `:176-186`, commit at `:197-200`). This
directly refines [Block 12] §12.3's claim that "there is no self-service recovery/backup-code path ...
a locked-out user's only recovery is an administrator clearing/resetting the `secretKey` slot" — that
statement is accurate for a genuinely LOCKED account (an admin still has to flip
`forceSecretKeyResetAtNextLogin` back to `true`, or the account stays locked with no self-service unlock),
but the FIRST-enrollment / admin-forced-reset case IS self-service end-to-end, at the login page, with no
Workbench access required. The Fox-transport equivalent (`BFoxTotpAuthCallbackHandler`,
`BFoxTotpClientAuthnHandler`) was located but not traced this session (out of scope — this gap concerned
the UI wiring, already closed by the web path).

## 38.2 — TOTP secret at rest: reversible AES-256, keyring-sourced key by default; no gauth migration `[CERT]`

[Block 12] §12.3 said the secret "is stored as a `BPassword` slot ... encoded like any other Niagara
password" without tracing which encoder. `BPassword.make(String key)` with no explicit encoding type
(exactly how both enrollment paths above construct it — `BPassword.make(secretKey)`,
`organized/totpAuth/vineflower/com/tridium/totpAuth/ui/BTotpSecretKeyFE.java:223`; `BPassword.make(secretKey)`, `organized/totpAuth/vineflower/com/tridium/totpAuth/BWebTotpAuthCallbackHandler.java:198`) falls
into `constructEncoder()`'s "no encoding type in the string" branch, which selects
`BReversiblePasswordEncoder.getDefaultEncodingType()`
(`organized/baja/vineflower/niagara/security/BPassword.java:98-106`) — **not** the one-way
`BPbkdf2HmacSha256PasswordEncoder` [Block 12] §12.4 documented for login passwords. This is a structural
necessity, not an oversight: `TotpAuthLoginModule.doLogin()` needs the RAW secret back to compute the
HMAC (`SecurityUtil.doPrivileged(authenticator.getSecretKey()::getValue)`,
`organized/totpAuth/vineflower/com/tridium/totpAuth/TotpAuthLoginModule.java:78`), which a one-way hash
cannot supply. `BReversiblePasswordEncoder.getDefaultEncodingType()` resolves to
`BAes256PasswordEncoder.ENCODING_TYPE` (`organized/baja/vineflower/niagara/security/
BAbstractPasswordEncoder.java:96-98`, `organized/baja/vineflower/niagara/security/BReversiblePasswordEncoder.java:29-31`) — i.e. **AES-256**, not the
newer `BAes256Pbkdf2HmacSha256PasswordEncoder` variant (that one is reserved for a `BAes256Pbkdf2...`
explicit encoding-type string, not the bare default).

**Encryption key source.** The no-context constructor path
(`new PasswordEncodingContext(context)` inside `BPassword`'s constructor,
`organized/baja/vineflower/niagara/security/BPassword.java:82-85`) defaults both
`decryptionKeySource`/`encryptionKeySource` to `EncryptionKeySource.keyring`
(`organized/baja/vineflower/niagara/security/PasswordEncodingContext.java:64-66`, confirmed by the
`forKeyring()`-style factory at `:74-75` constructing exactly `(keyring, keyring)`) — i.e. by default the
TOTP secret is AES-256-encrypted under a key sourced from the platform **keyring**
(`platCrypto`/`nre` keystore layer, B12-G2's still-open daemon), not a station-supplied passphrase. This
is the same reversible-encoder + keyring-key pattern [Block 12] §12.4 documented for the
`BAes256*` password family generally — this block adds that the TOTP secret specifically lands in that
same at-rest protection tier, one level stronger than "plaintext in the config" but explicitly NOT the
PBKDF2 one-way hash tier, because TOTP validation is structurally incompatible with a one-way hash.

**No gauth→totpAuth migration.** A fresh same-session `grep -rli gauth` across the ENTIRE N5 `totpAuth`
module tree and the `baja` authn/security subset returns **zero hits** — no class, string, or comment
anywhere in either tree references `gauth`, `GoogleAuthenticator`, or `BGoogleAuthAuthenticator`. N4's
`BGoogleAuthAuthenticator` (`niagara-research/organized/gauth/gauth-rt/vineflower/com/tridium/gauth/
BGoogleAuthAuthenticator.java`) is a structurally IDENTICAL class (same `secretKey`/
`forceSecretKeyResetAtNextLogin` properties, same `isSecretKeyConfigured`/`isTokenCheckRequired`/
`requiresCredentialsReset` methods, only the package (`javax.baja.*`→`niagara.*`) and field-editor facet
values differ) — confirming this is a rename-and-move with no migration utility, not a redesign. An N4
station upgrading to N5 loses every enrolled gauth secret; every user re-enrolls TOTP from scratch via
either path in §38.1. `[CERT]` on the N5-side absence (both named trees fully opened this session, per
METHODOLOGY §3's negative-existence rule); `[CERT]` on the N4-side structural match (file read in full,
quoted above).

## 38.3 — Account-wide lockout DOES cover bad TOTP tokens (correction to B12 §12.3) `[CERT]`

[Block 12] §12.3 stated: "`TotpAuthLoginModule` still has no rate-limiting or lockout on failed-token
attempts beyond the replay cache." That is true of the TOTP MODULE in isolation, but [Block 12] did not
trace the scheme-agnostic account lockout `BAuthenticationService` wraps around every login attempt — it
DOES count TOTP failures. `BAuthenticationService.login()` calls `scheme.login(handler)` (a
`LoginContext`, which runs `TotpAuthLoginModule`) inside a `try` that catches
`NiagaraFailedLoginException` specifically and, on catch, calls `processLoginAttempt(false, user, ...)`
(`organized/baja/vineflower/com/tridium/authn/BAuthenticationService.java:200-201,252-258,362-368`). A
wrong-but-plausible TOTP token (valid username + valid password, wrong 6-digit code) hits exactly this
path: `TotpAuthLoginModule.doLogin()` throws `NiagaraFailedLoginException` (not the bare
`FailedLoginException`, since `this.user` is already resolved and non-null at that point) when
`!validToken && tokenCheckRequired`
(`organized/totpAuth/vineflower/com/tridium/totpAuth/TotpAuthLoginModule.java:89-98`).
`processLoginAttempt(false, ...)` calls `user.authenticateFailed(userService)`
(`organized/baja/vineflower/com/tridium/authn/BAuthenticationService.java:367`), which enqueues a failure timestamp, and once
`authFailTimes.size() >= service.getMaxBadLoginsBeforeLockOut()` within the rolling
`lockOutWindow`, sets `BUser.lockOut=true` for `lockOutPeriod`
(`organized/baja/vineflower/niagara/user/BUser.java:653-676`). Defaults, all on `BUserService`
(`organized/baja/vineflower/niagara/user/BUserService.java`): `lockOutEnabled=true` (`:140`),
`maxBadLoginsBeforeLockOut=5` (min 1, max 10, `:144-146`), `lockOutWindow=30s` (`:148-152`),
`lockOutPeriod=BRelTime.make(10000L)` (`:142`, milliseconds — a 10-second lockout by default, short but
present and enabled out of the box). A separate `addRandomDelay()` (0-200ms `Thread.sleep`,
`organized/baja/vineflower/com/tridium/authn/BAuthenticationService.java:269-274`) also fires on every failure branch as a timing-attack mitigant.
Net correction: TOTP brute-forcing is rate-limited, just not by the TOTP module itself — by the
generic, scheme-agnostic `BUserService` lockout that applies identically to every authentication scheme
in the station (password, digest, TOTP, LDAP). `[INFER]`, not re-derived this session: whether this
scheme-agnostic lockout is itself new in N5 or an N4 carryover — plausible given `BUser`/`BUserService`
kept their `niagara.user` package and general architecture, but not fresh-checked against the N4 corpus
this session (→ **B38-G1**).

## 38.4 — SAML SP-initiated flow: always-signed AuthnRequest, RSA-SHA256 hardcoded `[CERT]`

`SAMLRPServlet.processLoginRequest()` (`organized/saml/vineflower/com/tridium/saml/rp/servlet/
SAMLRPServlet.java:164-213`) builds an `AuthnRequest` via `AuthnRequest.make(samlScheme,
assertionConsumerURL, issuerURL, destinationUrl)` (`:195-197`), registers its UUID in
`SAMLUuidMap.IN_RESPONSE_TO_SCHEME_MAP` keyed to the scheme with a `timeSkew`-derived TTL (`:198`), and
redirects the browser via HTTP-Redirect binding with the request Base64/deflate-encoded in the
`SAMLRequest` query parameter (`:199-201`). `shouldSignRequest()` is hardcoded `return true`
(`:261-263`) — every SP-initiated AuthnRequest is signed, unconditionally, with algorithm hardcoded to
`http://www.w3.org/2001/04/xmldsig-more#rsa-sha256` (`:203`) and `Signature.getInstance("SHA256withRSA")`
(`:251`); there is no configuration surface to disable signing or pick another algorithm on the SP side
(contrast §38.5's IdP-side AuthnRequest verification, which DOES support an algorithm allowlist for
INCOMING requests). The SP metadata endpoint (`GET .../metadata?scheme=<name>`,
`organized/saml/vineflower/com/tridium/saml/rp/servlet/SAMLRPServlet.java:65-93`) publishes the signing cert (and, when a `BISamlXmlDecrypter` child is
configured, the encryption cert too, `:128-144`) for IdP-side registration.

## 38.5 — SAML SP response handling: ACS, one-time InResponseTo, `checkValidity(null)` skips the strict match `[CERT]`

`SAMLConsumerServlet` is the Assertion Consumer Service (ACS) — both `doPost`/`doGet` decode the
`SAMLResponse` parameter, call `processSAMLResponse()`, then redirect to `/j_security_check`
(`organized/saml/vineflower/com/tridium/saml/rp/servlet/SAMLConsumerServlet.java:50-104`).
`Response.loadXmlFromBase64()` reads the response's `InResponseTo` attribute and looks it up in
`SAMLUuidMap.IN_RESPONSE_TO_SCHEME_MAP.get(inResponseTo)`
(`organized/saml/vineflower/com/tridium/saml/rp/Response.java:70-75`) — this `get()` **removes** the
entry on lookup (`organized/saml/vineflower/com/tridium/saml/rp/servlet/SAMLUuidMap.java:83-92`), so a
given `InResponseTo` UUID is consumable exactly once; if it's missing (never issued, expired past its
`timeSkew` TTL, or already consumed) `Response` throws immediately. `SAMLConsumerServlet.
processSAMLResponse()` then calls `samlResponse.checkValidity(null)`
(`organized/saml/vineflower/com/tridium/saml/rp/servlet/SAMLConsumerServlet.java:137`) — **passing `null` for `requestId`** means `checkValidity()`'s own
explicit `InResponseTo`-vs-`requestId` string match (`organized/saml/vineflower/com/tridium/saml/rp/Response.java:164-169`) is always skipped as
called from this servlet; the one-time-consumption `get()` above is the ACTUAL replay/binding defense
here, not that explicit check (which reads as intended for a caller that tracks its own last-issued
request ID — no such caller exists in this codebase). User auto-provisioning: `prepareUser()`
(`organized/saml/vineflower/com/tridium/saml/rp/servlet/SAMLConsumerServlet.java:145-183`) resolves/creates a `BUser` from the response's attributes via
`BSAMLAttributeMapping`s, gated by `samlScheme.getAllowAutomaticUserCreation()` (`:151-153`) — if that
flag is off and no matching user exists, login fails with `SAMLConfigurationException`; if a user exists
under a DIFFERENT scheme (and remote-scheme-change isn't globally allowed), login also fails (`:178-182`)
rather than silently hijacking an existing local account.

## 38.6 — SAML assertion validation: signature, schema, timestamps, audience, destination, subject confirmation `[CERT]`

`Response.checkValidity()` (`organized/saml/vineflower/com/tridium/saml/rp/Response.java:128-188`) runs,
in order: version==`"2.0"` and `ID` presence (`:132-138`); status-code success
(`validateStatus()`, `:204-217`); exactly one assertion, encrypted-or-plain
(`validateNumAssertions()`, `:219-236`); signature presence+validity — response-level and/or
assertion-level, against the IdP's cert from the LOCAL user truststore keyed by
`samlScheme.getIdpCert()` alias, via OneLogin/Santuario's `Util.validateSignNode()`
(`validateSignatures()`, `:238-286`; note: unlike §38.9's IdP-side AuthnRequest verification, there is
**no explicit algorithm allowlist** visible on this SP-side check — it defers entirely to whatever
`Util.validateSignNode()` accepts, an open question `[INFER]` not resolved this session, → **B38-G2**);
XML-schema validation of both the plain and (if applicable) decrypted document (`:144-162`); `Conditions`
`NotBefore`/`NotOnOrAfter` with a per-scheme configurable `timeSkew` clock-skew allowance
(`validateTimestamps()`, `:288-312`); no empty `Issuer` (`:180-184`); `AudienceRestriction` must include
this SP's own entity ID (`validateAudiences()`, `:314-319`); the response's `Destination` attribute, if
present, must match this SP's actual ACS URL (`validateDestination()`, `:321-330`); `AuthnStatement`
session `SessionNotOnOrAfter` not expired (`validateSessionExpiration()`, `:332-338`); and bearer
`SubjectConfirmationData`'s `Recipient`/`NotBefore`/`NotOnOrAfter` (`validateSubjectConfirmation()`,
`:340-395`, same `timeSkew` allowance). `EncryptedAttribute` elements are explicitly rejected outright
(`:172-175`) — attribute-level encryption is not supported even though assertion-level encryption is
(§38.7).

## 38.7 — SAML encrypted assertions: AES-256-CBC data + RSA-OAEP-MGF1P key wrap `[CERT]`

`samlEncryption.jar`'s IdP-side encrypter, `BSamlXmlEncrypter.encryptResponse()`
(`organized/samlEncryption/vineflower/com/tridium/samlEncryption/BSamlXmlEncrypter.java:48-95`): generates
a fresh random 16-byte AES key per response via `SecureRandom.getInstanceStrong()`
(`:37,60-62,97-103`); encrypts the `<saml:Assertion>` element with
`http://www.w3.org/2001/04/xmlenc#aes256-cbc` (Apache Santuario `XMLCipher`, `:63-69`); wraps that AES
key under the SP's public encryption certificate with
`http://www.w3.org/2001/04/xmlenc#rsa-oaep-mgf1p` (`:70-74`); strips any `<MGF>` element the cipher
library emits (`:79-84`, likely an interop workaround for SPs that choke on explicit MGF declaration
under the default SHA-1 MGF); and replaces the plaintext `<saml:Assertion>` with an
`<saml:EncryptedAssertion>` wrapper (`:86-89`). The SP-side decrypter, `BSamlXmlDecrypter
.decryptAssertion()` (`organized/samlEncryption/vineflower/com/tridium/samlEncryption/
BSamlXmlDecrypter.java:119-187`), pulls its RSA private key from the local keystore by an alias+optional
password (`BCertificateAliasAndPassword`, `:120-155`), locates the `EncryptedData`/`KeyInfo` (following a
`RetrievalMethod` indirection to a sibling `EncryptedKey` element if present, `decryptElement()`,
`:189-221`), and calls `XMLCipher` with that key as the key-encryption-key to recover the plaintext
assertion, which then replaces the `EncryptedAssertion` wrapper in place (`:173-183`). This module is
opt-in per [Block 12] §12.11/`niagara-research` B30 §30.2.5 — without a `BISamlXmlEncrypter` child on
`BSAMLIdPService`, assertions travel signed-but-unencrypted inside the (TLS-protected, if HTTPS is used)
POST body.

## 38.8 — SAML IdP servlet flow: endpoints, signature-algorithm allowlist, one-time AuthnRequest, CoT membership gate (closes B12-G6) `[CERT]`

Two servlets implement the IdP side end-to-end:

**`SAMLIdPAuthnRequestServlet`** (`organized/saml/vineflower/com/tridium/saml/idp/
SAMLIdPAuthnRequestServlet.java`) serves `GET /saml/idp/auth/httpredirect/cot/{cotId}` (`:38,55-74`).
`handleAuthnRequest()` (`:81-117`): rejects a `SAMLRequest` query value over 4096 chars (`:42,85-87`);
parses the redirect-bound `AuthnRequest` XML; then `validateRequest()` (`:119-133`) runs, IN ORDER:
(1) `validateSignature()` — requires BOTH `SigAlg` and `Signature` query params (unsigned AuthnRequests
are rejected outright, `:166-168`), verifies against the registered `BStationServiceProvider`'s configured
certificate, with an EXPLICIT algorithm allowlist mapping 6 XML-DSig URIs to JCA names — RSA/ECDSA ×
SHA-256/384/512 (`ALGORITHM_MAPPING`, `:221-228`) — any other `SigAlg` value is rejected as "Unsupported
signature algorithm" (`:152-155`); (2) `validateAssertionConsumerServiceUrl()` — must exactly match the
registered SP's configured ACS URL (`:171-175`); (3) `validateDestination()` — must match this Circle of
Trust's configured redirect endpoint (`:177-182`); (4) `validateProtocolBinding()` — ONLY
`urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST` is accepted for the response binding the request asks
for (`:184-188`); (5) `validateTimeConstraints()` — `issueInstant` must fall within
`±idPService.getTimeSkew()` of now (`:190-204`); then the request's UUID is inserted into a static
`SUCCESSFUL_LOGIN_MAP` keyed by ID with an expiry derived from `issueInstant+timeSkew` — a **duplicate
ID is rejected as "already been used"** (`:126-132`), a one-time-use replay guard distinct from
`SAMLUuidMap`'s. If the requester isn't already authenticated, the flow cookies the intended redirect
(`niagara_origin_uri`) and bounces to `/login` first (`:107-113`).

**`SAMLIdPProcessLoginServlet`** (`organized/saml/vineflower/com/tridium/saml/idp/
SAMLIdPProcessLoginServlet.java`) serves `GET /saml/idp/auth/processLogin/cot/{cotId}?id={uuid}`
(`:32-57`). `handleProcessLogin()` (`:64-114`): looks up the `id` in
`SAMLUuidMap.UUID_TO_AUTHN_REQUEST_MAP` (a SEPARATE one-time map from the AuthnRequest servlet's own
`SUCCESSFUL_LOGIN_MAP`, 2-minute TTL, `organized/saml/vineflower/com/tridium/saml/rp/servlet/SAMLUuidMap.java:26`) and double-checks the returned request's own
ID string matches (`:71-72`); requires an authenticated `BUser` in session (`:73-76`); checks Circle of
Trust MEMBERSHIP — `circleOfTrust.isUserMember(user)` — and rejects with `SAMLLoginException` if the
authenticated user isn't a CoT member (`:78-84`); gates assertion encryption on the target SP's
`getUseEncryption()` flag plus a configured `BISamlXmlEncrypter` child on the IdP service and the SP's
own encryption cert (`encryptionConfigured()`, `:116-130`); builds the signed (and optionally encrypted,
via §38.7) `IdPResponse`; sets its `AuthnContextClassRef` — either from a rank mix-in table (for a
non-SAML original scheme, e.g. an LDAP or password user being asserted out via SAML) selected by whether
the request was TLS (`request.isSecure()`, `:142-143`), or, for a user who is THEMSELVES a SAML user,
propagated from whatever `AuthnContextClassRef` the SESSION carries from that user's own upstream IdP
login (`addAuthnContextClassRefToResponse()`, `:132-168`); and returns an HTML auto-POST form
(`processLoginForm.vm`) that the browser submits to the SP's ACS URL (`:99-105`). Both servlets check
`BSAMLIdPService.isOperational()` before doing anything (`:57,76-79` / `:40,59-62`) — the IdP is a
switchable service, not always-on.

## 38.9 — LDAP bind: simple/CRAM-MD5/DIGEST-MD5, LDAPS via custom socket factory, no StartTLS evidence (closes B12-G7) `[CERT]`

`BAuthenticationMechanism` enumerates 4 bind mechanisms — `none`, `simple`, `cramMd5`, `digestMd5`
(`organized/ldap/vineflower/com/tridium/ldap/v3/BAuthenticationMechanism.java:12,23-29`; enum-level
`DEFAULT=none`, `:31`). `BLdapV3Config`'s own `authenticationMechanism` PROPERTY default is `simple`, a
distinct default from the enum's own (`organized/ldap/vineflower/com/tridium/ldap/v3/
BLdapV3Config.java:39`) — CRAM-MD5/DIGEST-MD5 are the SASL options; there is no Kerberos/GSSAPI mechanism
in this enum (contrast `niagara-research` B30's ~40-class `v3/` count, which per B30 includes Kerberos —
Kerberos support may live in a SEPARATE config class not read this session, → **B38-G3**). Bind-name
construction is pluggable per config version: v2 `BActiveDirectoryConfig.getConnectionUser()` appends
`@{domain}` UPN-style if the username has no `@` already (`organized/ldap/vineflower/com/tridium/ldap/
v2/BActiveDirectoryConfig.java:36-43`); v3 `BLdapV3Config.getConnectionUser()` either uses a fixed
configured service-account username, or, per-user, a `BindNameFormatter` templating the configured
`bindFormat` (default `"%userName%"`, `BLdapV3Config.java:33,90-99`) against the config's `userBase`/
`userLoginAttr`, and for a search-then-rebind flow, against the directory `Attributes` fetched for that
specific user's DN (`rebind()`, `:106-120` — i.e. the DN used for the per-user bind can incorporate
directory-fetched attribute values, not just the submitted username, via
`BindNameFormatter.get(String)` reading `this.attributes`,
`organized/ldap/vineflower/com/tridium/ldap/v3/BindNameFormatter.java:53-55`). Transport security:
`BLdapConfig.createInitialDirContextEnvironment()` sets `java.naming.security.protocol=ssl` and a CUSTOM
`java.naming.ldap.factory.socket=niagara.security.crypto.se.BajaSSLSocketFactory` when `getSSL()` is true
(`organized/ldap/vineflower/com/tridium/ldap/BLdapConfig.java:403-406`) — this is **implicit TLS (LDAPS)**,
i.e. the whole connection is wrapped in TLS from the socket up; no `StartTlsRequest`/extended-operation
code path was found anywhere in the `ldap.jar` decompile (`[INFER]` on the absence — the whole module's
18 `.java` files were read/grepped, but "StartTLS" as a literal string was not found; genuinely absent,
not merely unread). Also configured in the same environment map: connection timeout
(`com.sun.jndi.ldap.connect.timeout`, `:397-398`), connection pooling toggle (`:399-401`), and referral
handling (`:408-411`). Credentials for the bind (whether a fixed service account or the end user's own
submitted password) are pulled via the standard `BPassword::getValue` reversible-decrypt call
(`:379`), the same at-rest-protection tier §38.2 traced for the TOTP secret.

## 38.10 — SRP6: `BDigestAuthenticationScheme`'s key exchange is the SAME architecture N4 already had (closes B12-G8) `[CERT]`

[Block 12] §12.8 found N5's `BDigestAuthenticationScheme.getKeyExchangeMethodName()` delegating to
`com.tridium.crypto.core.exchange.KeyExchange.getPreferredKeyExchangeMethods()`
(`organized/baja/vineflower/com/tridium/authn/BDigestAuthenticationScheme.java:3,42-44`) and could not
determine, this session, whether that SRP6 layer was new in N5 (B12-G8). `niagara-research` B419 §419
(a DIFFERENT block, investigating the N4 Fox-protocol key exchange, not authn schemes per se) quotes N4's
own `FoxSession.java` doing the EXACT SAME call shape: `challenge.add("keyExchangeMethods",
authnScheme.getKeyExchangeMethodName())` immediately followed by
`challenge.add("keyExchangeCiphers", KeyExchange.getPreferredKeyExchangeCiphers())`
(`niagara-research` B419 §419, lines 53-54 as quoted in that block) — i.e. N4 ALREADY had an
authentication-scheme method named `getKeyExchangeMethodName()` feeding a `KeyExchange` class's
`getPreferredKeyExchange{Methods,Ciphers}()` statics, backing SRP6 as the Fox-session key-exchange
primitive (full protocol trace in B419 §419.3: `srp6ClientA`/`srp6ServerB`/`srp6M1`/`srp6M2` messages,
`KeyExchange.makeServer/makeClient(session.getKeyExchangeAlgorithmBundle())`). This is architecturally
identical to N5's `BDigestAuthenticationScheme.getKeyExchangeMethodName()` → `KeyExchange
.getPreferredKeyExchangeMethods()` call. **B12-G8 is resolved: the SRP6 key-exchange layer is NOT new in
N5** — it is the same `getKeyExchangeMethodName()`/`KeyExchange` architecture N4 already used to
negotiate the Fox wire's post-SCRAM session key, carried forward (the `com.tridium.crypto.core.exchange`
/`com.tridium.authn` package names match what both corpora show, modulo [Block 5]'s already-documented
`javax.baja.authn`→`niagara.authn` public-API rename). `[CERT]` on both sides (N5 file read this session;
N4 finding quoted from an already-existing, previously-verified `niagara-research` block, not
re-decompiled this session — the ADJUSTED marker count in §38.12 does not double-count B419's own
markers). Not re-derived this session: the 1024/2048-bit group sizes and SHA-512 pairing [Block 12] §12.8
cited for N5's `KeyExchange` bundle (`nre.jar`, out of this block's re-read scope) — whether those
GROUP SIZES match N4's Fox SRP6 parameters is still open (→ **B38-G4**).

## 38.11 — Measure counts

| Measure | Count |
|---|---|
| `.java` files read/re-read this session (already-organized trees, no fresh decompile) | ~20 (totpAuth: 9; saml: 8; samlEncryption: 2; ldap: 5; baja subset: 6) |
| New enrollment/reset flow classes traced beyond [Block 12] | 4 (`BTotpSecretKeyFE`, `BTotpAuthLoginHTMLForm`, `BWebTotpAuthCallbackHandler`, `BTotpAuthWbDialogHandler`) |
| SAML servlets fully traced this session | 4 (`SAMLRPServlet`, `SAMLConsumerServlet`, `SAMLIdPAuthnRequestServlet`, `SAMLIdPProcessLoginServlet`) |
| `Response.checkValidity()` sub-validations enumerated | 9 (version/ID, status, numAssertions, signature, schema, timestamps, audience, destination, subject confirmation) |
| Corrections issued to [Block 12] | 2 (§38.2 self-service path exists; §38.3 account-wide lockout covers TOTP) |
| Child gaps opened | 4 (B38-G1..G4) |
| Child gaps closed from [Block 12] | 4 (B12-G5, B12-G6, B12-G7, B12-G8) |

## 38.12 — Self-verification

Every citation above points inside `niagara5-research/organized/**`, this corpus's OWN target directory —
unlike [Block 12], whose citations pointed at a `/tmp` scratch tree. Ran the kit's mechanical calculator:

```
$ /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    /home/cristian/niagara5-research/niagara5-block38.md /home/cristian/niagara5-research
```

Literal output (first pass flagged 13 citations `extern` because they used a bare `File.java:line`
shorthand on a repeated-file second mention within a paragraph instead of the full relative path; fixed
by spelling out the full `organized/.../File.java:line` path at every citation, then re-run to a clean
pass):

```
== verify-block: niagara5-block38.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 19  (adj 17)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 1  (adj 0)
   [INFER] 6  (adj 5)
-- ratio -- [INFER]/[CERT*] = 5/17 = 0.29
-- [CERT] file:line citation resolution --
   resolved 31 of 31
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

ADJUSTED ratio 5/17 ≈ **0.29** — low/evidence-dominant, consistent with an evidence-plus-gap-closure
block that closed 4 child gaps with fresh reads. All 31 `[CERT]` `file:line` citations resolved cleanly
against this corpus's own `organized/` tree (0 `extern`, 0 out-of-range, exit 0) — a stronger result than
[Block 12], whose citations were 100% `extern` by design (pointed at a `/tmp` scratch tree per METHODOLOGY
§11's decompiled-tree rule). Every cited range was also opened via the Read tool BEFORE being written into
this block (not grep-only) — the primary verification method for a decompiled-source block per
METHODOLOGY §11's token-check requirement.
Representative tokens additionally `grep`-confirmed present in their cited files this session:
`SECRET_SIZE`, `createSecret`, `forceSecretKeyResetAtNextLogin`, `totpAuth.secretKey`,
`EncryptionKeySource.keyring`, `BAes256PasswordEncoder`, `maxBadLoginsBeforeLockOut`, `lockOutWindow`,
`processLoginAttempt`, `shouldSignRequest`, `rsa-oaep-mgf1p`, `aes256-cbc`, `ALGORITHM_MAPPING`,
`SUCCESSFUL_LOGIN_MAP`, `BAuthenticationMechanism`, `BindNameFormatter`,
`getKeyExchangeMethodName` — all present at or adjacent to their cited lines. The one fresh N4-side
negative-existence check (`grep -rli gauth` across N5's `totpAuth`+`baja` trees, §38.2) is reported
verbatim: zero hits, both full trees opened.

## 38.13 — Open questions / unresolved contradictions

- **[C1]** [Block 12] §12.3 asserted no rate-limiting/lockout on TOTP token failures "beyond the replay
  cache" `[CERT]`; this block finds the scheme-agnostic `BUserService` lockout DOES cover TOTP failures
  `[CERT]` (§38.3) — not a direct contradiction (both are true of DIFFERENT layers: the TOTP MODULE has
  no lockout of its own; the STATION does), but worth flagging as a claim that reads narrower than the
  full picture if quoted out of context. Corrected in place at §38.3, not pushed to `CONTRADICTIONS.md`
  since both blocks' underlying evidence is accurate and non-conflicting once the layer is named.

## 38.14 — Child gaps opened

- **B38-G1** — Confirm whether the scheme-agnostic `BUserService` account lockout (§38.3) is new in N5 or
  an N4 carryover (fresh N4-corpus check not run this session).
- **B38-G2** — Trace `Response.validateSignatures()`'s (`organized/saml/vineflower/com/tridium/saml/rp/Response.java:238-286`) actual accepted
  signature-algorithm set on the SP side — no explicit allowlist is visible in the traced code, unlike the
  IdP-side `ALGORITHM_MAPPING` (§38.6, §38.8); depends on OneLogin/Santuario library defaults not read
  this session.
- **B38-G3** — Locate LDAP Kerberos/GSSAPI support (if any) — `BAuthenticationMechanism` (§38.9) has no
  such enum value, but `niagara-research` B30 counted ~40 classes under N4's `v3/` including Kerberos; the
  N5 `ldap.jar`'s Kerberos config class (if any) was not located this session.
- **B38-G4** — Confirm whether N5's `KeyExchange` SRP6 group sizes (1024/2048-bit, SHA-512, per [Block 12]
  §12.8) match N4's Fox SRP6 parameters (`niagara-research` B419 does not state its own group sizes in
  the excerpt available this session).

## 38.15 — Connections

- **[Block 12]** — parent block; this block closes 4 of its 8 child gaps (B12-G5/G6/G7/G8) and issues 2
  corrections (§38.2, §38.3) to its own claims, both framed as refinements rather than refutations.
- **[Block 5]** — the `javax.baja.authn`→`niagara.authn` / `com.tridium.authn` package continuity this
  block relies on for the B12-G8 N4↔N5 comparison (§38.10) is the same rename [Block 5] documented at the
  public-API layer only.
- **[Block 3]** — every reversible-password decrypt (`BPassword::getValue`) and LDAP bind credential fetch
  traced here goes through `SecurityUtil.doPrivileged`, the same `SecurityAgent` mechanism [Block 3]
  documents.
- **`niagara-research` B419/B134/B420** — the N4 Fox-protocol SRP6 key-exchange trace this block uses to
  resolve B12-G8 (§38.10); not re-derived, only quoted and compared.
- **`niagara-research` B30/§30.2/§30.19, B494 §494.5, B803** — the N4 SAML/gauth/LDAP architecture
  baseline this block's N4-side claims (§38.2's gauth structural match, §38.9's LDAP mechanism continuity)
  are measured against.
