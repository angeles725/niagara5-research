# Block 12 — N5 authentication and security surface: a new vendor-neutral TOTP module (128-bit secret, up from N4 gauth's 80-bit), a 10×-stronger PBKDF2 default (100,000 vs N4's 10,000 iterations), a new CRL-checking PKI scheme absent from N4's client-cert auth, and a real Linux-`nftables` firewall processor behind the "firewall" package name

> **§14 correction (2026-09-27, [Block 38]):** TOTP enrollment has TWO paths (Workbench admin field editor, and a self-service web-login reset that fires on first login because `forceSecretKeyResetAtNextLogin` defaults true), not admin-only; and bad TOTP tokens ARE rate-limited by the station-wide `BUserService` account lockout (5 bad logins / 30 s → 10 s lockout) via `BAuthenticationService.processLoginAttempt()`, although `TotpAuthLoginModule` itself has none. N4 gauth secrets have no migration path.


> **Scope**: Closes gap **N5-G9** (Security/authn surface: `totpAuth` [new], `oauth2`, `saml`,
> `clientCertAuth`, `firewall`, `authn`). Covers: every `BAuthenticationScheme` subclass shipped across
> `totpAuth.jar`, `oauth2.jar`, `saml.jar`, `samlEncryption.jar`, `clientCertAuth.jar`, `ldap.jar`,
> `tls.jar`, `platCrypto.jar`, `signingService.jar`, and `baja.jar`'s `com.tridium.authn`/
> `com.tridium.firewall`/`com.tridium.security`/`com.tridium.session` packages plus the public
> `niagara.authn`/`niagara.security`/`niagara.security.crypto` API; the TOTP design (algorithm, secret
> size/storage, enrollment/reset flow); password-hashing algorithms and defaults; the `com.tridium.firewall`
> package's real implementation (`com.tridium.nre.firewall`, in `nre.jar`); session management
> (`com.tridium.session`); TLS protocol/cipher-suite defaults (`niagara.security.crypto`,
> `com.tridium.crypto.core.io.CryptoSupport` in `nre.jar`); and the N4→N5 delta for every item above,
> established via fresh same-session `grep` against the `niagara-research` (N4) corpus decompile. Does
> **not** cover: `platCrypto`'s full daemon-IPC certificate-management protocol (161 classes, inventoried
> only, → **B12-G2**); `signingService`'s Fox-borne CSR-signing wire protocol (→ **B12-G3**); the SAML IdP
> servlet flow end-to-end (→ **B12-G6**); LDAP v2/v3 bind-name-formatting details (→ **B12-G7**); or the
> `PermissionManager` grant table already covered by [Block 8]. **Correction to the gap's own premise**:
> `tls.jar` is **not** Transport Layer Security — it is the Veeder-Root **TLS-250/350 fuel-tank-monitoring
> serial/TCP protocol driver** (`com.tridium.tls.*`, tank inventory/delivery-variance reports); actual TLS
> (crypto) lives in `niagara.security.crypto` (`baja.jar`) and `com.tridium.crypto.core.io` (`nre.jar`),
> read instead.
>
> Subject version: **N5 5.0.0.28 (Beta)**. All nine module jars share `vendorVersion="5.0.0.28"`,
> `schemaVersion="5"`, `releaseDate="2026-03-11"` (`META-INF/module.xml` inside each, read this session);
> jar `mtime` 2026-09-11 22:39 (matches [Block 3]/[Block 6]'s stamp). `baja.jar`/`nre.jar` at the same
> mtime. N4 baseline: `niagara-research` corpus (target #1), Honeywell OptimizerSupervisor 4.14.0.162
> decompile — cited by block number, not re-derived, except where marked "fresh re-grep this session".
>
> Sources (all local, read-only):
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{totpAuth,oauth2,saml,samlEncryption,
>   clientCertAuth,ldap,tls,platCrypto,signingService}.jar` — full-jar Vineflower decompile.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` →
>   `com/tridium/{authn,firewall,security,session}/*` (60 zip entries) and `niagara/{authn,security}/*`
>   (84 zip entries) — extracted to a subset jar and Vineflower-decompiled (whole-jar decompile of
>   `baja.jar` itself was out of scope this session; [Block 6]/[Block 3] already did that for other
>   packages).
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` →
>   `com/tridium/nre/firewall/**` (12 entries), `niagara/nre/security/{ClientTlsParameters,
>   ServerTlsParameters,TlsCipherSuiteGroup,TlsParameters}.class`, `com/tridium/crypto/core/io/
>   CryptoSupport*.class`+`NiagaraSslContextFactory.class`, `com/tridium/crypto/core/exchange/*` — each
>   extracted to its own subset jar and Vineflower-decompiled.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` →
>   `doc/security/*.html` (9 files: `authentication.html`, `codeSigning.html`, `csrfProtection.html`,
>   `headerAuthentication.html`, `niagaraPermissions.html`, `requestingPermissions.html`, `roles.html`,
>   `scramshaexample.html`, `security.html`) — extracted and HTML-tag-stripped for reading.
> - REMITTANCE baseline (N4): `niagara-research` corpus, via
>   `python3 corpus-nav.py find "AuthenticationScheme"|totp|"password hash"|pbkdf2|SessionManager|SuperSession|clientCertAuth|BPKIAuthenticationScheme|BCaConfiguration|BKeySizeValidationRule|samlEncryption|oauth2`,
>   plus fresh same-session `grep -n` against the corpus's own decompiled files
>   (`organized/baja/baja/vineflower/javax/baja/security/BPbkdf2HmacSha256PasswordEncoder.java`,
>   `organized/gauth/gauth-rt/vineflower/com/tridium/gauth/GoogleAuthenticator.java`).
>
> Decompiled/extracted this session into `/tmp/claude-1000/n5b12/` (scratch, not part of the corpus;
> re-derivable from the cited jars): `totpAuth/`, `oauth2/`, `saml/`, `samlEncryption/`, `clientCertAuth/`,
> `ldap/`, `tls/`, `platCrypto/`, `signingService/` (primary whole-jar decompiles), `baja_subset_vf/`
> (`com.tridium.{authn,firewall,security,session}`), `baja_subset2_vf/` (`niagara.{authn,security}`),
> `nre_fw_vf/` (`com.tridium.nre.firewall`), `nre_tls_vf/` (`niagara.nre.security.Tls*`), `nre_crypto_vf/`
> (`com.tridium.crypto.core.{io,exchange}`), `docs/doc/security/` (doc HTML).
>
> Method: Vineflower 1.12.0 (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar`),
> run by `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`, on whole module jars and on hand-built
> subset jars (`zip`/`unzip` package-filtered extracts of `baja.jar`/`nre.jar`, since decompiling either
> whole jar was out of this block's scope/budget). Markers: `[CERT]` local primary (decompiled source
> read this session) · `[CERT-doc]` official installed HTML doc · `[INFER]` deduction. Per METHODOLOGY
> §11 "decompiled-tree blocks" rule: every citation below points into the `/tmp` scratch trees above,
> which are **not** corpus-resolvable by `verify-block.sh` (all report as `extern`) — self-verify is
> therefore 100% inline token-`grep` (§12 below), 0/0 script-resolved by design.
>
> Security/authn layer. Connects [Block 3] (SecurityAgent/`SecurityUtil.doPrivileged` — every
> authenticator here calls it), [Block 6] (licensing's own `SecurityUtil.doPrivileged` migration — same
> pattern), [Block 8] (`PermissionManager`/`NiagaraPermission` — gates the RPCs this block's schemes
> expose), and `niagara-research` B27/B29/B30/B134/B494/B510/B562/B695/B777/B803/B929 (N4 baseline for
> nearly every subsystem here).

---

## 12.1 — Module inventory and where the gap's premise was wrong `[CERT]`

| Module jar | `module.xml` description | Role established this session |
|---|---|---|
| `totpAuth.jar` | "Time-based One-Time Password (TOTP) Authenticator Module" | **NEW module name**, replaces N4's `gauth` (removed — no `gauth.jar`/`google*.jar` under N5's `modules/`) |
| `oauth2.jar` | "OAuth 2.0 Client API" | Outbound OAuth2 **client** only (client-credentials + JWT-bearer grants) — not a station login scheme, same as N4 (B929) |
| `saml.jar` | "SAML Authentication Module" | SP (relying-party) + IdP, same architecture as N4 (B777) |
| `samlEncryption.jar` | "SAML Encryption Module" | XML-assertion encrypt/decrypt, split out as its own module — same split as N4 (B30 §30.2.5, B113) |
| `clientCertAuth.jar` | "Client Certificate Authentication Module" | Now ships **two** schemes: N4's simple `clientcert` **and** a new `pkiAuth` with CA-chain + CRL (§12.9) |
| `ldap.jar` | "LDAP Authentication Schemes" | Same architecture as N4 (B30 §30.19) |
| `tls.jar` | "N/A — not a security module" | **Gap-description error**: `com.tridium.tls.*` is the Veeder-Root **fuel-tank-monitoring** protocol driver (`BTls250FuelTankDevice`, `BTls350ConsoleDevice`, `BFuelManagementTable`, `BInTankInventoryTable`, …) — a `TLS-250`/`TLS-350` gas-station console integration, unrelated to Transport Layer Security `[CERT]` (`tls/com/tridium/tls/devices/BTls250FuelTankDevice.java`, `tls/com/tridium/tls/enums/BTlsTypeEnum.java`, 136 `.java` files, none crypto-related) |
| `platCrypto.jar` | "Crypto Platform Service" | Platform-daemon keystore/truststore/exemption-store service + a runtime `BCertManagerService`; 161 classes, only lightly explored this session (§12.10, → B12-G2) |
| `signingService.jar` | "Signing Service" | Station-hosted CSR-signing service (a mini internal CA), Fox-transported (§12.11, → B12-G3) |

The **actual** TLS-crypto surface — protocol/cipher-suite defaults — lives in `niagara.security.crypto`
(`baja.jar`) and `com.tridium.crypto.core.io`/`com.tridium.crypto.core.exchange` (`nre.jar`), covered in
§12.7-§12.8.

## 12.2 — `BAuthenticationScheme` subclass census across every module read `[CERT]`

Same base-class hierarchy as N4 (`niagara-research` B510/B777): `niagara.authn.BAuthenticationScheme`
(abstract SPI) → `niagara.authn.BSSOAuthenticationScheme` (external-IdP family) and
`niagara.authn.BPasswordAuthenticationScheme` (local-credential family). Package location moved from
N4's `javax.baja.authn` to N5's `niagara.authn` — the [Block 5] core-API rename, confirmed here by a
fresh decompile (`baja_subset2_vf/niagara/authn/BAuthenticationScheme.java`).

| Class | Module | Scheme name | Family | Source |
|---|---|---|---|---|
| `BDigestAuthenticationScheme` | `baja.jar` | `n4digest` | Password | `baja_subset_vf/com/tridium/authn/BDigestAuthenticationScheme.java:19` |
| `BHTTPBasicAuthenticationScheme` | `baja.jar` | `n4HTTPbasic` | Password | `baja_subset_vf/com/tridium/authn/BHTTPBasicAuthenticationScheme.java:18` |
| `BLegacyBasicAuthenticationScheme` | `baja.jar` | `basic` | Password | `baja_subset_vf/com/tridium/authn/BLegacyBasicAuthenticationScheme.java:16` |
| `BLegacyDigestAuthenticationScheme` | `baja.jar` | `digest` | Password | `baja_subset_vf/com/tridium/authn/BLegacyDigestAuthenticationScheme.java:18` |
| `BSessionIdAuthenticationScheme` | `baja.jar` | `session` | direct (throws on `getDefaultAuthenticator()`) | `baja_subset_vf/com/tridium/authn/BSessionIdAuthenticationScheme.java:18` |
| `BTotpAuthenticationScheme` | `totpAuth.jar` (NEW) | `totpAuth` | Password | `totpAuth/com/tridium/totpAuth/BTotpAuthenticationScheme.java:19` |
| `BLdapAuthenticationScheme` | `ldap.jar` | `n4LDAP` | direct (own SPI, not Password/SSO) | `ldap/com/tridium/ldap/BLdapAuthenticationScheme.java:40` |
| `BSAMLAuthenticationScheme` | `saml.jar` | `n4saml` | SSO | `saml/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java:137` |
| `BClientCertAuthScheme` | `clientCertAuth.jar` | `clientcert` | SSO | `clientCertAuth/com/tridium/clientCertAuth/BClientCertAuthScheme.java:35` |
| `BPKIAuthenticationScheme` (NEW, § 12.9) | `clientCertAuth.jar` | `pkiAuth` | SSO | `clientCertAuth/com/tridium/clientCertAuth/pki/BPKIAuthenticationScheme.java:47` |

`oauth2.jar` and `samlEncryption.jar` ship **no** `BAuthenticationScheme` subclass — confirmed by
`grep -rl "extends B\(Password\)\?AuthenticationScheme\|extends BAbstractAuthenticationScheme"` across
every decompiled tree this session, matching zero files in either module. `oauth2` is a client-only
library (§12.12); `samlEncryption` is a XML-crypto helper consumed by `saml`'s IdP (§12.11).

**N4→N5 delta on this table**: every scheme name and class above is unchanged from N4
(`niagara-research` B27 §27.8.5, B30, B510, B777) **except** `totpAuth`/`BTotpAuthenticationScheme`
(new class, replaces N4's `gauth`/`BGoogleAuthenticationScheme`, scheme name changed `"gauth"`→`"totpAuth"`)
and `BPKIAuthenticationScheme` (wholly new — `python3 corpus-nav.py find "BPKIAuthenticationScheme"` and
`find "BCaConfiguration"` both return **zero matches** in the N4 corpus).

## 12.3 — TOTP design (`totpAuth`): RFC-6238 algorithm unchanged, secret upgraded 80→128 bits `[CERT]`

`TotpAuthenticator.java` implements RFC 6238 TOTP directly (no external OTP library):

| Parameter | N5 value | Citation |
|---|---|---|
| HMAC algorithm | `HmacSHA1` | `totpAuth/com/tridium/totpAuth/TotpAuthenticator.java:126-127` |
| Digits | 6 (`truncatedHash %= 1000000L`) | `totpAuth/.../TotpAuthenticator.java:139` |
| Time step | 30 s (`TimeUnit.SECONDS.toMillis(30L)`) | `totpAuth/.../TotpAuthenticator.java:73,77` |
| Validation window | ±3 steps (±90 s clock drift tolerance) | `totpAuth/.../TotpAuthenticator.java:75` |
| Secret size | **16 bytes (128 bits)**, Base32-encoded | `totpAuth/.../TotpAuthenticator.java:26,34` |
| Replay protection | in-memory per-secret `HashMap<Long, QueueEntry>` cache, pruned by the ±3-window expiry | `totpAuth/.../TotpAuthenticator.java:79-104` |
| QR provisioning | `otpauth://totp/{user}@{host}?secret=...` rendered as inline SVG via bundled **ZXing** | `totpAuth/.../TotpAuthenticator.java:39-67` |

N4's `gauth` module (`GoogleAuthenticator.java`) used the **identical** algorithm — same HMAC-SHA1,
6-digit, 30-second, ±3-window design (`niagara-research` B494 §494.5) — with one concrete difference,
confirmed by a fresh same-session `grep` against the N4 corpus decompile:

```
organized/gauth/gauth-rt/vineflower/com/tridium/gauth/GoogleAuthenticator.java:26: SECRET_SIZE = 10
```
(10 bytes = **80-bit** secret) vs N5's `SECRET_SIZE = 16` (**128-bit**) — a genuine strengthening, not
just a rename. Both remain RFC-6238-compliant, so any standard TOTP app (Authy, Microsoft/Google
Authenticator) still works against either; the rebrand from `gauth`/`GoogleAuthenticator` to
`totpAuth`/`TotpAuthenticator` drops the Google-specific class/module naming without changing wire
compatibility. `TotpAuthLoginModule` still has **no rate-limiting or lockout** on failed-token attempts
beyond the replay cache (matches N4's documented gap, B494 §494.5 row 6) — this is unchanged, not a
regression introduced in N5.

**Credential/enrollment model** (`BTotpAuthAuthenticator`, `totpAuth/com/tridium/totpAuth/
BTotpAuthAuthenticator.java`): the secret is stored as a `BPassword` slot (`secretKey`, encoded like any
other Niagara password — §12.4), with `forceSecretKeyResetAtNextLogin` defaulting `true` on a newly
created authenticator (`BTotpAuthenticationScheme.getDefaultAuthenticator():38-39`) — i.e. **enrollment
is enforced on first login**, not optional. There is no self-service recovery/backup-code path in the
decompiled classes; a locked-out user's only recovery is an administrator clearing/resetting the
`secretKey` slot, mirroring the admin-mediated reset pattern N4 already documents for other credential
resets (`niagara-research` B803).

## 12.4 — Password hashing: PBKDF2-HMAC-SHA256 iteration count raised 10,000 → 100,000 `[CERT]`

`niagara.security.BPbkdf2HmacSha256PasswordEncoder` (moved from N4's `javax.baja.security` package,
[Block 5] rename) is unchanged in algorithm and salt size, but the default work factor increased 10×:

| Parameter | N5 (`baja_subset2_vf/niagara/security/BPbkdf2HmacSha256PasswordEncoder.java`) | N4 (fresh re-grep, `organized/baja/baja/vineflower/javax/baja/security/BPbkdf2HmacSha256PasswordEncoder.java`) |
|---|---|---|
| KDF | PBKDF2 + HMAC-SHA256 (`Pbkdf2.deriveKey`) | same |
| Iteration count | **100,000** (`:32,45`) | **10,000** (`:32,45`) |
| Salt length | 16 bytes, `SecureRandom` (`:33`) | 16 bytes (same) |
| Encoding tag | `pbkdf2hmacsha256/text` (via `NiagaraStationAlgorithmBundle`) | same |
| Timing-safe compare | `SecurityUtil.equals(tkey, this.key)` in `validate()` (`:82-85`) | same pattern |
| Username-enumeration defense | `makeFake(userName)` — deterministic salt from `SHA-256(fixedRandomPrepend+username)`, random key, so a non-existent user still produces a plausible-looking encoder to compare against (`:112-127`) | same method present in N4 |

100,000 iterations is well inside 2020s OWASP guidance for PBKDF2-HMAC-SHA256 (≥ ~600,000 is the more
recent, stricter figure — N4's B562 already flagged 10,000 as low); N5 does not reach that stricter bar,
but the 10× jump is a real, measurable hardening, not cosmetic. The encoder chain otherwise matches N4's
documented HASHED-vs-ENCRYPTED fork exactly (`niagara-research` B562): `AxPasswordUtil`
(`baja_subset_vf/com/tridium/security/AxPasswordUtil.java`) still recognizes the same three legacy AX
encodings (`plain/text`, `aes256/text`, `pbkdf2hmacsha256/text`) for upgrade-in-place migration, and the
reversible family (`BAes256PasswordEncoder`, `BAes256Pbkdf2HmacSha256PasswordEncoder`,
`BAliasedAes256CbcPasswordEncoder`) is present unchanged by class name
(`baja_subset2_vf/niagara/security/BAes256*.java`).

## 12.5 — `com.tridium.firewall`: NAT/port-redirect rule bookkeeping, real enforcement is `nftables` `[CERT]`

`baja.jar`'s `com.tridium.firewall` package (`ConcurrentFirewallProcessor`, `FirewallRulesPage`) is a
thin wrapper/spy-page over `com.tridium.nre.firewall` in **`nre.jar`** — the actual rule model and (on
Linux) real enforcement:

- **Rule model** (`nre_fw_vf/com/tridium/nre/firewall/FirewallRule.java`): abstract base with
  `RuleType` enum `{REDIRECT_RULE, INPUT_RULE, NOOP_RULE}` (`:38-42`); concrete `InputRule`
  (port/protocol/adapter/loopback-bind/hint) and `RedirectRule`.
- **`NftablesFirewallProcessor`** (`nre_fw_vf/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java`)
  is a real Linux **nftables** backend: it shell-execs the `nft` binary (path from
  `niagara.firewall.frontend.path`) via `ProcessBuilder` under `SecurityUtil.doPrivileged`, targeting
  table `filter`/chain `input` by default (`niagara.firewall.input.table`/`niagara.firewall.input.chain`
  system properties, `:27-28`), e.g. `nft add rule inet filter input iifname eth0 tcp dport 80 counter
  accept comment "..."` (`:83-118`), and looks up/deletes rules by parsing `nft list -a ruleset` output
  for a `handle` number (`:203-231`). Only `INPUT_RULE` is accepted (`REDIRECT_RULE` is explicitly
  rejected by `validateRule()`, `:52-62`) — i.e. this backend **opens inbound ports**, it does not do NAT
  redirection. The rule-hint string is sanitized to `[A-Za-z0-9.$]` before being embedded in the shell
  command (`:234-241`) — a real (if narrow) injection guard on a value that otherwise flows straight into
  a constructed command line.
- **`FirewallRulesPage`** (`baja_subset_vf/com/tridium/firewall/FirewallRulesPage.java`) is a Workbench
  spy page reading `BServerPort.getRuleList()`/`getFirewallName()` — display only, "may be an incomplete
  list" per its own hard-coded caveat text (`:15`).

So the gap's "firewall" package is real perimeter enforcement (dynamic `nft` rule injection tied to which
`BServerPort`s a station has open) rather than an IP packet-filter policy engine or a rule editor UI —
closer in spirit to a container/cloud platform auto-opening its own listen ports than to a
firewall-management console. `com.tridium.nre.firewall` was **not found** in the N4 corpus by
`corpus-nav.py find "FirewallRule\|FirewallProcessor"` in the earlier searches this session (no hits
returned), so this whole subsystem is provisionally **N5-only** — flagged `[INFER]` pending a dedicated
N4 `nre.jar`/platform-daemon check, since N4's own daemon-side firewall handling (if any) was not
re-searched exhaustively this session (→ **B12-G4**, also covering whether the `nft` `ProcessBuilder` exec
is itself gated by the [Block 8] `PermissionManager` model).

## 12.6 — Session management: `com.tridium.session` is architecturally unchanged from N4 `[CERT]`

`SessionManager`/`NiagaraSuperSession`/`NiagaraSession` (`baja_subset_vf/com/tridium/session/*.java`)
kept their **package name** (`com.tridium.session`, not renamed to `niagara.session` — unlike
`javax.baja.authn`→`niagara.authn`), and the design matches N4's documented model
(`niagara-research` B30 §30.13) point for point:

| Property | N5 (this session) | N4 (`niagara-research` B30) |
|---|---|---|
| Session-ID generation | `SecureRandom`, hex-encoded, `DEFAULT_SESS_ID_LEN = 25` bytes (200 bits) (`SessionManager.java:22,133-141`) | `SecureRandom`-based (B30 §30.13.1) |
| Aggregation model | one `NiagaraSuperSession` aggregates N child `NiagaraSession`s (HTTP/Fox/Box) per authenticated identity — `Map<BUser, NiagaraSuperSession> byUser` invariant | identical `Set<NiagaraSession> sessions` aggregator (B30 §30.13.2) |
| Concurrent-session policy | `checkConcurrentSession()` invalidates the prior super-session unless `BUser.getAllowConcurrentSessions()` is set (`:215-227`) | identical (B30 §30.13.2, "segundo login patea al primero") |
| Session-fixation defense | `changeSuperSessionId()` explicit post-auth ID regeneration (`:196-211`) | identical mechanism present (B30 §30.13.1) |
| Log hygiene | `printSessions()` logs `SecurityUtil.calculateSessionIdHash(...)`, never the raw ID (`:398-433`) | not contradicted by anything read this session |
| Persistence | `sessions` is a `static` in-memory `Map` — no disk persistence, confirmed absent again here | identical (B30 §30.13.1, "puro in-memory. NO persisted") |

No delta found. This is presented as a **negative finding** (architecture-preserved), not exhaustively
proven identical byte-for-byte — only the class inventory and the methods read above were compared;
a full diff of every method body was out of scope.

## 12.7 — TLS protocol defaults: minimum floor raised to TLSv1.2, cipher lists derived from the live JRE `[CERT]`

`niagara.security.crypto.BSslTlsEnum` (`baja_subset2_vf/niagara/security/crypto/BSslTlsEnum.java`) still
enumerates all four historical protocol tags — `tlsv1`/`tlsv1_1`/`tlsv1_2`/`tlsv1_3` — with the BOG-level
**default staying `tlsv1`** (`:19,32`, i.e. "lowest acceptable floor if nothing overrides it" — this is
a permissive per-object default, not the effective runtime minimum). The effective **runtime** minimum
is computed separately by `com.tridium.crypto.core.io.CryptoSupport.getDefault()` (`nre.jar`):

```java
// nre_crypto_vf/com/tridium/crypto/core/io/CryptoSupport.java:174-181
DEFAULT_MINIMUM = sysPropMinTlsVersion != null && sysPropMinTlsVersion.equalsIgnoreCase("tlsv1.3")
    ? "tlsv1_3" : "tlsv1_2";
```
i.e. **TLSv1.2 is the effective floor unless `niagara.crypto.requireMinTlsVersion=tlsv1.3` is set**
(`:181`) — SSLv2/v3 and TLSv1.0/1.1 are excluded from every `TYPE_EXCLUDE_LISTS` entry at `tlsv1.2`+
(`:249-256`). Cipher-suite lists are **not** a hard-coded string array; they are computed once at class-init
time (`static {}` block, `:277-311`) from the running JRE's own `SSLContext.getInstance("TLS")
.getServerSocketFactory().getSupportedCipherSuites()`, filtered by an exclude predicate that strips
`DES`/`NULL`/`EXPORT`/`RC4`/`MD5`/`SSL`/`anon`/`CAMELLIA`/`ARIA`/`_ECDH_`/`DSS` matches plus a few named
suites and an externally configurable `cipherSuite.exclude.patterns` system property (`:286-303`). Three
named tiers, all derived from that one filtered list:

| Tier (`niagara.security.crypto.BTlsCipherSuiteGroup`) | Derivation |
|---|---|
| `supported` | JRE-supported minus the hard exclude list above |
| `recommended` (**default**) | `supported`, further restricted to `TLS_ECDHE*`/`TLS_AES*`/`TLS_DHE*`/`TLS_CHACHA20*` families, excluding CBC-mode and plain-`SHA` suites (`:314-321`) |
| `strict` | `recommended`, further excluding any suite whose name contains `_WITH_` (i.e. TLS 1.3's `TLS_AES_*_GCM_SHA*` cipher-suite naming convention, which has no `_WITH_` token, survives; legacy TLS-1.2-style `TLS_..._WITH_..._..._...` names do not) — this is the practical mechanism by which `strict` becomes "TLS 1.3 ciphers only" |

Because the list is JRE-derived rather than hard-coded, its literal membership will differ by installed
JRE build; the **exclusion policy** (the filters themselves) is the durable, version-independent fact
`[CERT]`. This block does not have a fresh N4-side TLS-cipher-defaults citation to compare against
(out of this session's search scope) — flagged `[INFER]` that this represents continuity rather than
change, pending a dedicated N4 `CryptoSupport`/`javax.baja.security.crypto` read.

## 12.8 — Key exchange: SRP6 (1024/2048-bit, SHA-512) backs the Digest scheme's pre-auth key negotiation `[CERT]`

`BDigestAuthenticationScheme.getKeyExchangeMethodName()` delegates to
`com.tridium.crypto.core.exchange.KeyExchange.getPreferredKeyExchangeMethods()`
(`baja_subset_vf/com/tridium/authn/BDigestAuthenticationScheme.java:33-35`), which advertises SRP6
(Secure Remote Password, RFC 2945 family) groups — 2048-bit preferred, 1024-bit fallback (reversed
preference order on an embedded platform), both with **SHA-512**, plus a `null` bundle as a final
fallback (`nre_crypto_vf/com/tridium/crypto/core/exchange/KeyExchange.java:52-72`). `IKeyExchanger` is
implemented concretely by `SRP6KeyExchangerClient`/`SRP6KeyExchangerServer`
(`nre_crypto_vf/com/tridium/crypto/core/exchange/SRP6KeyExchanger*.java`). This is distinct from the Fox
wire's own SCRAM-SHA-256 login digest documented in N4 B134 — SRP6 here negotiates a **pre-shared
encryption key** for the Digest scheme's key-exchange metadata (`KEY_EXCHANGE_STATUS_VALUE_SRP6`
constant, `:16`), not the login proof itself. Whether this SRP6 layer is new in N5 or an existing N4
mechanism not previously catalogued was not resolved this session (no N4-side `SRP6` hit surfaced by the
searches run) — named **B12-G8**, low priority.

## 12.9 — `clientCertAuth`: a new `pkiAuth` scheme adds CRL revocation checking N4 documented as absent `[CERT]`

N4's `clientCertAuth-rt` shipped exactly one scheme, `BClientCertAuthScheme` (`"clientcert"`), and B30
§30.5 documented, from decompile, that it performs **no** revocation check at all ("sin llamadas a
`PKIXRevocationChecker` ni `X509CertSelector.setRevocationChecker()`" — a named FIPS 140-2 CMVP gap). N5
still ships that exact class unchanged (`clientCertAuth/com/tridium/clientCertAuth/
BClientCertAuthScheme.java:31,35` — `extends BSSOAuthenticationScheme implements TrustAnchorProvider`,
no `CRLProvider`), **plus** a new class absent from the N4 corpus (`corpus-nav.py find
"BPKIAuthenticationScheme"`/`"BCaConfiguration"` → zero matches both):

- `BPKIAuthenticationScheme` (`"pkiAuth"`) implements **both** `TrustAnchorProvider` **and**
  `CRLProvider` (`clientCertAuth/com/tridium/clientCertAuth/pki/BPKIAuthenticationScheme.java:40`), and
  its `getCRLs()` genuinely reads a CRL per configured CA: `caConfiguration.getCaCertAndCrl().getCrl()`
  (`:154-159`), registering itself with `CoreCryptoManager` as both a trust-anchor and a CRL provider
  (`:93-102`).
- CA trust is configured per-scheme via a `BCaConfigurationFolder` of `BCaConfiguration` entries
  (`:37`), not a single fixed truststore.
- A pluggable **certificate-validation-rule** engine backs it (`BValidationRules` +
  `BICertValidationRule`), all new relative to N4:
  - `BKeySizeValidationRule` — default `keySize=2048`, `comparisonMode=minimum`
    (`clientCertAuth/com/tridium/clientCertAuth/pki/BKeySizeValidationRule.java:20-21`).
  - `BKeyAlgorithmValidationRule` — default `allowedAlgorithms="RSA;EC"`
    (`clientCertAuth/com/tridium/clientCertAuth/pki/BKeyAlgorithmValidationRule.java:16`).
  - `BExtendedKeyUsageValidationRule` — defaults `requireTlsWebClientAuthenticationExtension=true` and
    `requireSmartcardLogonExtension=true`, plus an OID-validated custom-EKU list
    (`clientCertAuth/com/tridium/clientCertAuth/pki/BExtendedKeyUsageValidationRule.java:34-36,48,156`).
- Five pluggable username-extraction strategies ship as separate classes — CN from Subject DN, CN from
  Directory-Name SAN, email-address SAN, email-user-from-SAN, UPN SAN
  (`clientCertAuth/com/tridium/clientCertAuth/pki/BUsernameExtractor*.java`, 5 files) — vs. N4's
  documented single fixed match strategy (B30 §30.5.1, "match por... lookup BUser").

Both schemes coexist in the same module; nothing in the decompiled classes marks `BClientCertAuthScheme`
deprecated, so this reads as **additive** (a stronger PKI option was added alongside the simple one, not
a replacement) — not confirmed by any deprecation annotation or doc statement, `[INFER]`.

## 12.10 — `platCrypto`: the platform crypto/keystore daemon service (inventoried, not traced) `[CERT]`

161 decompiled `.java` files under `com.tridium.platcrypto`: a `BCertManagerService` façade over a
daemon-message protocol (`com/tridium/platcrypto/daemon/messages/*` — ~20 message classes:
`GenerateCertificateMessage`, `GenerateCsrMessage`, `GetCertificateChainMessage`,
`SetKeyEntryWithResponseMessage`, etc.) that talks to `BPlatCryptoManager`/`BPlatKeyStore`/
`BPlatTrustStore`/`BPlatExemptionStore` daemon-side objects, plus a parallel `com.tridium.platcrypto.fox`
package (`BCryptoChannel`, `ChannelKeyStore`, `ChannelTrustStore`) that appears to expose the same
keystore/truststore operations over a Fox channel for Workbench UI use, and a `migration` package
(`CertificateMigrationUtil`, `CoreCertificateMigrationTarget`) for moving certs between stores. This is
the backing platform service `BPKIAuthenticationScheme`'s `CoreCryptoManager` calls (§12.9) ultimately
reach. Full protocol trace (message request/response pairing, which operations require which
permission) is out of scope this session — **B12-G2**.

## 12.11 — SAML / SAML encryption: unchanged architecture, unchanged scheme name `[CERT]`

`BSAMLAuthenticationScheme` keeps N4's exact scheme name `"n4saml"`
(`saml/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java:137`, matches
`niagara-research` B777 §777.3 verbatim) and the same RP/IdP split N4 documents (B777): RP side
(`com.tridium.saml.rp`, `AuthnRequest`/`Response`/servlets) and IdP side
(`com.tridium.saml.idp`, `BSAMLIdPService`/`BCircleOfTrust`/servlets), both still built on the
**OneLogin java-saml2** library (`com.onelogin.saml2.*` imports, e.g.
`samlEncryption/com/tridium/samlEncryption/BSamlXmlEncrypter.java:5`) and **Apache Santuario**
(`org.apache.xml.security.*`) for XML-DSig/XML-Enc — same third-party stack N4 used (B113's
`SignatureDSA` finding). `samlEncryption.jar` remains a separate module consumed by `saml.jar`'s IdP
(`BSamlXmlEncrypter.isParentLegal()` only allows attaching under `BSAMLIdPService`,
`samlEncryption/com/tridium/samlEncryption/BSamlXmlEncrypter.java:40-41`) — the same module split N4
already had (B30 §30.2.5). No architectural delta found; the IdP servlet flow itself was not traced
end-to-end this session (→ **B12-G6**, would mirror N4's dedicated B777).

## 12.12 — OAuth2: still an outbound-only client; the Nimbus SDK moved out of the module jar `[CERT]`

`oauth2.jar` ships **zero** `BAuthenticationScheme` subclasses (§12.2) — confirmed again here: it is a
client-credentials/JWT-bearer token-acquisition helper (`OAuth2ClientCredentialsGrantRequest`,
`OAuth2JWTBearerGrantRequest`, `OAuth2AuthorizationServerMetadataResolver` for `.well-known` discovery),
identical role to N4's `oauth2-rt` (`niagara-research` B929: "does not implement OAuth2 itself — wraps
Nimbus... consumed by the EMAIL module"). The concrete delta is **packaging**: N4's `oauth2-rt.jar`
bundled the vendored Nimbus JOSE/OAuth2 SDK inside the module jar (~776 of ~788 files per B929); N5's
`oauth2.jar` contains **only 12 classes**, all `com.tridium.oauth2.*` — zero `com.nimbusds.*` classes
(`unzip -l oauth2.jar | grep -c com/nimbusds/` → 0). Its `module-info.java` instead **declares** Nimbus
as external JPMS dependencies:

```java
// oauth2/module-info.java
module niagara.oauth2 {
   requires com.nimbusds.jose.jwt;
   requires transitive com.nimbusds.oauth2.sdk;
   requires transitive org.json;
   ...
}
```
i.e. the vendored SDK became separate automatic modules under N5's JPMS layout ([Block 1]'s
module-per-jar finding) instead of being bundled per-consuming-module as in N4. This session could
**not** locate a jar named for `com.nimbusds.*`/`org.json` anywhere under either
`.../config/5.0.0.28/modules/` or `.../5.0.0.28/bin/ext/` — flagged as an open question, **B12-G1**.

## 12.13 — Shipped documentation cited this session `[CERT-doc]`

All from `docDeveloper.jar`'s `doc/security/` (9 HTML files, all read this session):

| File | Content confirmed |
|---|---|
| `doc/security/authentication.html` | Authentication Service overview — multiple schemes per station, per-user `authenticationSchemeName` binding, developer guidance for authoring new schemes; text matches N4-era wording (`niagara-research` B510) verbatim in the excerpt read |
| `doc/security/headerAuthentication.html` | The HTTP-header (`HELLO`/`SCRAM`) machine-to-machine auth mechanism, dated to "Niagara 4.4" in its own text — confirms this mechanism is **not new** to N5 despite the doc's presence here; corroborates N4 B27 §27.8.6's finding that no `BHeaderAuthenticationScheme` class exists (this is a wire *mechanism* under the session-id scheme, not a separate scheme class) |
| `doc/security/codeSigning.html` | Module code-signing overview, default self-signed dev profile at `USER_HOME/.tridium/security/niagara.signing.{jks,xml}`, `gradlew :createProfile` — text dated to "Niagara 4.6"/"4.8" in its own body, i.e. unrevised for N5 |
| `doc/security/csrfProtection.html`, `roles.html`, `niagaraPermissions.html`, `requestingPermissions.html`, `scramshaexample.html`, `security.html` | Listed and confirmed present; not read in full this session (out of this gap's scope — RBAC/permissions is [Block 8]'s territory) |

Every one of these files' *content* reads as N4-vintage prose (explicit "Niagara 4.4"/"4.6"/"4.8"
version references inside the text) carried forward into the N5 doc jar unrevised — no N5-specific
doc content (e.g. nothing mentioning `totpAuth` or `pkiAuth` by name) was found in this directory.
`totpAuth`/`saml`/`ldap`/`clientCertAuth`/`oauth2` modules were also checked for their own bundled
`doc/` resources (none carry HTML docs of their own — only `.properties`/lexicon resources, per each
module's `resources/` census implied by the whole-jar decompile above).

## 12.14 — Measure counts

| Measure | Count |
|---|---|
| Module jars decompiled whole (Vineflower) | 9 (`totpAuth`, `oauth2`, `saml`, `samlEncryption`, `clientCertAuth`, `ldap`, `tls`, `platCrypto`, `signingService`) |
| Total `.java` files across those 9 | 18+10+61+4+32+18+136+161+33 = **473** |
| `baja.jar`/`nre.jar` package-subset jars built + decompiled | 5 (`com.tridium.{authn,firewall,security,session}`; `niagara.{authn,security}`; `com.tridium.nre.firewall`; `niagara.nre.security.Tls*`; `com.tridium.crypto.core.{io,exchange}`) |
| `.java` files from those 5 subsets | 39+84+9+4+10 = **146** |
| `BAuthenticationScheme` subclasses found | 10 (§12.2) |
| Genuinely new classes vs N4 (confirmed zero N4-corpus hits) | 2 (`BTotpAuthenticationScheme`+family; `BPKIAuthenticationScheme`+`BCaConfiguration`+3 validation-rule classes+5 username extractors) |
| N4 constants fresh-re-grepped this session for a same-session `[CERT]` | 2 (`ITERATION_COUNT` 10,000; `SECRET_SIZE` 10) |
| doc/security HTML files censused | 9; 3 read in full excerpt |
| Child gaps opened | 8 (B12-G1..G8) |

## 12.15 — Self-verification

Every load-bearing citation above points into `/tmp/claude-1000/n5b12/**`, a scratch tree outside the
corpus (per METHODOLOGY §11's decompiled-tree rule) — `verify-block.sh`'s `file:line` resolver would
classify 100% of them `extern`. Self-verify is inline token-`grep`, run against the scratch files
immediately before writing each citation this session (see the tool-call transcript): `ITERATION_COUNT`,
`SALT_LENGTH`, `SECRET_SIZE`, `HmacSHA1`, `1000000L`, `DEFAULT_SESS_ID_LEN`, `getAllowConcurrentSessions`,
`niagara.firewall.input.table`, `tlsv1_2`/`tlsv1_3`, `getStrictCipherSuites`/`getRecommendedCipherSuites`,
`SRP6AlgorithmBundle.make`, `CRLProvider`/`TrustAnchorProvider`, `keySize.*2048`, `allowedAlgorithms` — all
confirmed present by `grep -n` against the cited file before being written into this block; none
hand-recalled. The two N4-side numeric citations (`ITERATION_COUNT = 10000`, `SECRET_SIZE = 10`) were
likewise fresh-`grep`ped against the `niagara-research` corpus's own decompiled files this session, per
METHODOLOGY §3's "numeric constants are `[CERT]` only with a fresh same-session grep" rule.

```
$ grep -o '\[CERT\]' niagara5-block12.md | wc -l
      19
$ grep -o '\[CERT-doc\]' niagara5-block12.md | wc -l
       2
$ grep -o '\[INFER\]' niagara5-block12.md | wc -l
       7
```
Raw counts (literal, run against the finished file). **Adjusted**: 2 of the raw `[INFER]` hits and 1 of
the raw `[CERT]` hits are the header-blockquote's own marker-legend line and this section's own
prose-discussion of the ratio — not fresh claims — so the ADJUSTED counts are **18 `[CERT]`** (mostly
one per numbered-section header, per this corpus's own convention — see [Block 6]'s tail — plus a handful
of inline re-assertions) / **2 `[CERT-doc]`** / **4 `[INFER]`**. Adjusted `[INFER]`/`[CERT]` ratio ≈
**0.22** — low, evidence-dominant: the 4 real `[INFER]`s are (a) whether `com.tridium.nre.firewall` is
genuinely N5-only vs. an uncatalogued N4 feature (§12.5), (b) whether TLS cipher-suite policy changed vs.
N4 (§12.7, no N4-side citation available this session), (c) whether `BPKIAuthenticationScheme` deprecates
`BClientCertAuthScheme` (§12.9), and (d) the Nimbus-jar-location absence (§12.16 [C1]) — each also named
as its own child gap rather than asserted either way.

## 12.16 — Open questions / unresolved artifacts

- **[C1]** `oauth2/module-info.java` declares `requires com.nimbusds.jose.jwt`, `requires transitive
  com.nimbusds.oauth2.sdk`, `requires transitive org.json` (§12.12) `[CERT]`, but no jar exposing those
  package names was found under `.../config/5.0.0.28/modules/` or `.../5.0.0.28/bin/ext/` this session
  `[INFER]` on the absence (searched, not exhaustively — could be in a `jar-cache/` or a path outside
  `modules/`/`bin/ext/` not enumerated). → **B12-G1**.

## 12.17 — Child gaps opened

- **B12-G1** — Locate the JPMS automatic-module jar(s) backing `oauth2`'s `com.nimbusds.jose.jwt` /
  `com.nimbusds.oauth2.sdk` / `org.json` `requires` (§12.12, §12.16 [C1]).
- **B12-G2** — Trace `platCrypto`'s daemon-message protocol end-to-end (`BCertManagerService` →
  `BPlatCryptoManager`/`BPlatKeyStore`/`BPlatTrustStore`; which messages require which permission) (§12.10).
- **B12-G3** — Trace `signingService`'s Fox-borne CSR-signing flow (`BSigningService`,
  `BFoxSigningRequester`/`BSigningChannel`, `BSessionToken`) as a mini internal-CA protocol.
- **B12-G4** — Confirm whether `com.tridium.nre.firewall`/`NftablesFirewallProcessor` is genuinely N5-only
  or an uncatalogued existing N4 daemon feature, and whether its `nft` `ProcessBuilder` exec is gated by
  the [Block 8] `PermissionManager` model (§12.5).
- **B12-G5** — Trace `totpAuth`'s enrollment UI wiring end-to-end (`BTotpAuthAuthenticatorFE` (wb),
  `BTotpSecretKeyEditor`/`BTotpSecretKeyFE` (ux/wb field editors), QR-display step ordering vs.
  `forceSecretKeyResetAtNextLogin`) (§12.3).
- **B12-G6** — Full SAML IdP servlet flow trace (`SAMLIdPAuthnRequestServlet`/
  `SAMLIdPProcessLoginServlet`, `BCircleOfTrust` validation) — the N5-side mirror of N4's B777 (§12.11).
- **B12-G7** — LDAP v2/v3 config classes not read in detail this session (`BActiveDirectoryConfig`,
  `BindNameFormatter`, `BAuthenticationMechanism` wiring into the actual bind call).
- **B12-G8** — Determine whether the SRP6 key-exchange layer backing `BDigestAuthenticationScheme`
  (§12.8) is new in N5 or an existing, previously-uncatalogued N4 mechanism.

## 12.18 — Connections

- **[Block 3]** — every authenticator/session/crypto call site here that touches privileged operations
  goes through `SecurityUtil.doPrivileged` (`SessionManager`, `NftablesFirewallProcessor`,
  `AxPasswordUtil`), the same `SecurityAgent`/`AccessController`-replacement mechanism [Block 3]
  documents for the boot/runtime layer.
- **[Block 5]** — the `javax.baja.authn`→`niagara.authn` and `javax.baja.security`→`niagara.security`
  package moves this block confirms for `BAuthenticationScheme`/`BPbkdf2HmacSha256PasswordEncoder` are
  concrete authn-layer instances of [Block 5]'s core-API rename; `com.tridium.session` and
  `com.tridium.firewall`, by contrast, kept their `com.tridium.*` package names — evidence the rename was
  scoped to the **public** `javax.baja.*` API surface, not internal `com.tridium.*` implementation
  packages.
- **[Block 6]** — this block's password/session/crypto call sites use the same
  `SecurityUtil.doPrivileged` idiom [Block 6] documented for the licensing layer's own migration off
  `AccessController`.
- **[Block 8]** — the `@NiagaraRpc(permissions = "r", ...)` annotation on
  `BTotpAuthAuthenticator.isSecretKeyConfigured()` (§12.3) is a concrete RPC this block found that
  [Block 8]'s `PermissionManager`/`NiagaraPermission` grant table would need to cover; not cross-checked
  against that block's grant table this session.
- **`niagara-research` B27, B29, B30, B134, B494, B510, B562, B695, B777, B803, B929** — the N4 baseline
  every §12.2-§12.12 delta claim above is measured against; none of these blocks were re-derived, only
  read and fresh-re-grepped where a numeric constant needed a same-session citation.
