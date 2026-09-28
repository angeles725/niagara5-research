# Block 94 — Platform daemon, firewall, crypto services, native launcher residue: eight of nine cluster residuals closed (one stays live-station-blocked), with a live disassembly reversal of Block 87's own FIPS-setter guess and a full `platCrypto` daemon-HTTP-servlet protocol trace

> Research closing/narrowing nine named child gaps spanning four residual clusters — platform daemon crypto
> protocols, the N4/N5 firewall lineage, native-launcher FIPS/module-export residue — each left by a prior
> block to a deeper pass than that session's own scope covered: **B81-G3** ([Block 81] §81.6 — confirm live
> whether a Linux N5 install with `niagara.firewall.enabled=true`/`niagara.firewall.frontend=nft` set produces
> working `nft` rules end-to-end, and separately confirm via a fresh install/packaging read whether these two
> properties are ever set BY DEFAULT on a genuine Linux deployment); **B33-G6** ([Block 33] §33.x — determine
> whether N5's narrowing from N4's NAT-redirect-capable `pf` backend to N5's input-only `nft` backend has an
> observable operational consequence for any shipped N5 service that relied on a firewall-level port redirect);
> **B40-G1** ([Block 40] §40.x — trace `BComponent`'s station-config rename-path charset against
> `NftablesFirewallProcessor.isRuleHintValid`'s `[A-Za-z0-9.$]` gate, for `BOpcUaServer.getName()` concatenated
> into `ruleHintOverride`); **B40-G4** ([Block 40] §40.x — trace N4's `netsh`/`CAP_NET_ADMIN` host-firewall
> mechanism, a REMIT-only un-traced prose claim); **B12-G2** ([Block 12] §12.17 — trace `platCrypto`'s
> daemon-message protocol end-to-end, `BCertManagerService` → `BPlatCryptoManager`/`BPlatKeyStore`/
> `BPlatTrustStore`, which messages require which permission); **B12-G3** ([Block 12] §12.17 — trace
> `signingService`'s Fox-borne CSR-signing flow, `BSigningService`/`BFoxSigningRequester`/`BSigningChannel`/
> `BSessionToken`, as a mini internal-CA protocol); **B53-G4** ([Block 53] §53.6 — confirm the runtime's own
> `cacerts` structure: count, alias classes, key algorithms; no private material); **B87-G2** ([Block 87] §87.x
> — disassemble `NreLauncherWin32`'s own setter/origin for the FIPS-mode byte at `this+0x1002c`); **B87-G3**
> ([Block 87] §87.x — disassemble `njre.dll`'s own `--add-exports=niagara.nre/...=niagara.niagarad` call
> site's conditional gate).
>
> Does **not** cover: any live/dynamic reproduction on a running station (the same live-station blocker class
> named by [Block 54]/[Block 61]/[Block 65]/[Block 81]'s own **B81-G1** — no runnable N5 install, Linux or
> Windows, this session); a JACE-class embedded-Linux platform's own install/distribution files (this session's
> access remained Windows-Supervisor-only, same limit [Block 33]/[Block 40] each recorded); a full re-read of
> every `platCrypto`/`signingService` class not named by B12-G2/B12-G3's own text (e.g. `BPlatKeyStore`'s full
> keystore-management surface beyond the daemon-message shape, `BLocalSigningRequester`'s same-JVM path); a
> byte-for-byte identity check of any `cacerts` entry against a named pinned constant (out of B53-G4's own
> stated scope, which asked for structure only).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> Native binaries copied to this session's scratchpad
> (`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b94/`)
> from the READ-ONLY install `/mnt/c/Program Files/Niagara/5.0.0.28`, re-hashed before analysis — bytes are
> IDENTICAL to [Block 87]'s own copies, confirming no drift since that session: `nre.dll` (`sha256
> a6317e8b024ed823ebe857113bff4378600fc2bd41890309696375dce91239c4`), `njre.dll` (`sha256
> 1b8b0074c79dc148e479602bb5bb1a2245f3549db421ccb6534bca7f6a4dfd0b`). Cross-corpus baseline for **B40-G4**:
> `/home/cristian/niagara-research/organized` (N4 4.14 decompiled corpus), whole-corpus `find -exec grep`
> sweeps for `netsh`/`CAP_NET_ADMIN` (zero hits, both terms). Runtime `cacerts` for **B53-G4**: live install
> file `/mnt/c/Program Files/Niagara/5.0.0.28/jre/lib/security/cacerts` (`sha256
> 9b5319f17ab786587c2d1729a3b54b8cb9ef1a5acb9199f8a4660491e531e701`), inspected with `keytool -list`/
> `keytool -list -v` — metadata only, no `-exportcert`/`-srckeypass`/private-key operation run, per this
> gap's own secrets-discipline instruction. Markers (canonical list, METHODOLOGY §3): `[CERT]` local primary
> source (`file:line`, a literal command/tool-output, or a live install-file read) · `[CERT-hw]` installed-
> binary disassembly (`r2`/`objdump`, with sha256 + address) · doc/web-grade markers not used this session
> (they appear once in the Self-verify tally's own prose, naming markers, not claiming one) · `[INFER]`
> deduction, stated as such.
>
> **Type:** `mixed` — §94.1–§94.6, §94.8, §94.9 each close or narrow a named child gap with fresh direct
> evidence, several upgrading a prior block's own `[INFER]`/`[CERT-a]` remittance to `[CERT]`/`[CERT-hw]`;
> §94.8 additionally CORRECTS [Block 87] §87.5's own stated claim (Corrections section below); §94.7 (B81-G3)
> stays open, narrowed only on its packaging-defaults half.

---

## 94.1 — B12-G2 CLOSED: `platCrypto`'s daemon protocol is an HTTP servlet (`crypto?action=...` query string + XML), not a legacy binary IPC channel — the gap's own assumed `BCertManagerService`→`BPlatCryptoManager` call chain does not exist in the source (they are sibling backends, corrected below); every one of 19 traced message actions, its HTTP verb, and its two independently-stacked permission gates are now mapped `[CERT]`

**Parent-block text, quoted verbatim** ([Block 12] §12.17): *"**B12-G2** — Trace `platCrypto`'s daemon-message
protocol end-to-end (`BCertManagerService` → `BPlatCryptoManager`/`BPlatKeyStore`/`BPlatTrustStore`; which
messages require which permission) (§12.10)."*

**Correcting the gap's own premise first: `BCertManagerService` never calls `BPlatCryptoManager`.** They are
SIBLING implementations of `ICoreCryptoManager`/`ICryptoManagerProvider`, selected by session type inside
`BCertManagerService.serviceStarted()`: `CoreCryptoManager.get()` for a local platform session
(`instanceof BLocalHost`), or `new ChannelCryptoManager(this)` for a Fox-tunneled remote-station session
(`instanceof BFoxSession`) `[CERT]` (`organized/platCrypto/vineflower/com/tridium/platcrypto/core/
BCertManagerService.java:104-117`) — neither branch is the daemon path. The DAEMON backend is a THIRD,
separate implementation reached only through platform-daemon tooling: `BPlatCryptoManager.make(BDaemonPlatform
platform)` returns `platform.getDaemonSession() != null ? new BPlatCryptoManager(platform.getDaemonSession()) :
null` `[CERT]` (`organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatCryptoManager.java:64-66`).
`BCertManagerService` is never in this call chain — the actual caller (`BDaemonPlatform`/commissioning tooling)
was not itself opened this session (named as a child gap below).

**Transport: HTTP over the platform-daemon session, not a binary protocol.** All five daemon-side stores
(`BPlatKeyStore`, `BPlatTrustStore`, `BPlatExemptionStore`, `BPlatProviderInfo`, reached via
`BPlatCryptoManager.getKeyStore()`/`getUserTrustStore()`/`getUserUntrustedStore()`/`getSystemTrustStore()`/
`getExemptionStore()`/`getProviderInfo()`, `BPlatCryptoManager.java:68-94`) extend `BPlatCryptoBase`, whose
`send(CryptoServletMessage)` either `daemonSession.post(message)` or `daemonSession.getInputStream(message)`
`[CERT]` (`organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatCryptoBase.java`, `send` method).
`BDaemonSession extends BSession implements AuthenticationClient` `[CERT]`
(`organized/platform/vineflower/com/tridium/platform/daemon/BDaemonSession.java:152`) builds each request via
`prepareMessageUri(message)` then `getInputStream(...)`/`getConnection(messageURI, message.getMethod(), ...)`
`[CERT]` (`BDaemonSession.java:923-933`) — an ordinary HTTP client session, not Fox and not a legacy binary IPC
channel. `CryptoServletMessage extends DaemonMessage implements EncryptableDaemonMessage` builds its query
string as `"?action=" + this.getAction()` `[CERT]` (`organized/platCrypto/vineflower/com/tridium/platcrypto/
daemon/messages/CryptoServletMessage.java:11,18`).

**Daemon-side handler.** `com.tridium.niagarad.servlet.CryptoServlet extends DaemonServlet`, `SERVLET_NAME =
"crypto"` `[CERT]` (`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/CryptoServlet.java:
79,86`); its constructor wires `this.cryptoManager = CoreCryptoManager.get(NiagaraDaemon.
getSecurityInfoProvider())` `[CERT]` (`CryptoServlet.java:86-89`) — daemon-side, it is the SAME
`CoreCryptoManager` `BCertManagerService` uses locally for a local session. The daemon-message protocol exists
purely so a client that cannot run in-process (a remote Workbench/JWS session, or one Niagara instance driving
another's platform daemon) can drive that same local crypto manager over HTTP.

**Action inventory and permission mapping, verified by reading each message class's `getAction()`/`getMethod()`
against `CryptoServlet`'s dispatch:** `sendAliases`/`getCertificate`/`getCertificateChain`/`getCertificates`
(GET, `KeyStorePermission.checkRead`), `getCertificateAlias`/`findCertificate` (POST, `checkRead`), `getKey`
(GET, `checkRead`, requires a per-session `SharedSecretKey` to encrypt the key in transit),
`setCertificateEntry`/`setKeyEntry` (POST, `checkWrite`, CSRF-gated), `deleteEntry`/`saveKeyStore` (GET but
state-changing, `checkWrite`, CSRF-gated), `generateCert`/`generateCsr`/`resetUserKeyStore` (GET, CSRF-gated,
`generateCsr` uses `KeyStorePermission.checkRead` on `USER_KEY_STORE` — read, not write, despite being one of
`CryptoServlet`'s own CSRF-gated `update=true` actions, a possible inconsistency named as a child gap below),
`getExemption`/`getExemptions`/`setExemption`/`deleteExemption`/`saveExemptions` (`BPlatExemptionStore`'s own
`checkRead`/`checkWrite`) `[CERT]` (per-action citations: `organized/_bin-ext/nre/vineflower/niagara/nre/
security/permissions/KeyStorePermission.java:103,107` for `checkRead`/`checkWrite`;
`organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatKeyStore.java` and `BPlatTrustStore.java`
for each store's own call sites; `CryptoServlet.java:148-263` (GET dispatch), `:289-365` (POST dispatch)).

**Two independently-stacked permission layers — the gap's own explicit "which messages require which
permission" question, answered precisely.** (1) **Client-side JVM gate:**
`KeyStorePermission extends NiagaraPermission`'s `checkRead(String storeName)`/`checkWrite(String storeName)`
(`KeyStorePermission.java:103,107`) walk the calling module's granted `KeyStorePermission`s (name = store id,
e.g. `userKeyStore`/`userTrustStore`/`systemTrustStore`/`userExemptionStore`, or `*`) and
`throw new PermissionException(...)` if the module's own manifest grant does not cover the requested
store+action — enforced identically for local (`CoreCryptoManager`) and daemon-remote
(`BPlatKeyStore`/`BPlatTrustStore`/`BPlatExemptionStore`) use, before any network I/O. (2) **Daemon-side HTTP
auth gate:** `CryptoServlet.authenticate()` sets `requireAdmin = true` for every action except
`getCertHealth`/`getPasswordStrength` (user-auth only); the admin check requires
`simpleAuthenticationInfo.hasHostAdminAccess()` `[CERT]` (`organized/_bin-ext/niagarad/vineflower/com/tridium/
niagarad/util/DaemonAuthUtil.java:80`) — genuine platform/host-admin credentials, not merely an authenticated
station user. THIS is the real privilege boundary: the daemon process can touch OS-level keystore files the
calling JVM cannot, and refuses non-admin daemon sessions outright for essentially the whole crypto surface.
State-changing actions additionally require a CSRF token; key/password-bearing actions require a per-session
`SharedSecretKey` to encrypt the sensitive payload in transit.

**Verdict: CLOSED.** Transport (HTTP over `BDaemonSession`/the `crypto` servlet), wire format
(`?action=...` query string + XML response), the action inventory, and both permission layers (module-manifest
`KeyStorePermission` per message + daemon host-admin/CSRF/shared-key per action) are traced end-to-end with
direct citations, and the gap's own faulty premise (a direct `BCertManagerService`→`BPlatCryptoManager` call)
is corrected rather than silently assumed. Residual: `getCertHealth`/`getPasswordStrength` (the two
user-auth-only actions) have no corresponding class under `platcrypto/daemon/messages/` — their actual caller
was not found this session (named as a child gap below, distinct from the fork-research NARROWED framing this
section replaces).

## 94.2 — B12-G3 CLOSED: `signingService`'s Fox-borne CSR flow is a full self-service-onboarding + operator-approval + JWT-proof-of-possession mini-CA protocol, with NO `NiagaraPermission` gate on the remote path itself — only TLS-required Fox-session security plus per-message cryptographic proof `[CERT]`

**Parent-block text, quoted verbatim** ([Block 12] §12.17): *"**B12-G3** — Trace `signingService`'s Fox-borne
CSR-signing flow (`BSigningService`, `BFoxSigningRequester`/`BSigningChannel`, `BSessionToken`) as a mini
internal-CA protocol."*

**End-to-end flow, fully traced this session, all six Fox commands read on both client- and server-marshal
sides:**

1. **Onboarding.** `BFoxSigningRequester.initiateOnboarding()` (`organized/signingService/vineflower/com/
   tridium/signing/fox/BFoxSigningRequester.java:128-176`) calls `BSigningChannel.onboard(requesterId,
   metadata, temporaryCode)` (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:164-204`, client marshal), which sends `requesterId`
   + a `metadata` `FoxMessage` (comment, the locally-authenticated username if any, the requesting station's own
   name — `organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:180-186`) over Fox. Server-side (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:206-239`, the
   `onboard(FoxRequest)` overload) calls `SigningServiceUtils.getFoxSigningTransport().getSessionTokenStore()
   .store(requesterId, metadata, existingTempCode)` under `SecurityUtil.doPrivileged` (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:
   225-227`) and returns a fresh 32-byte `SecureRandom`-generated `temporaryCode`
   (`organized/signingService/vineflower/com/tridium/signing/transport/BSessionToken.java:122-123`).
2. **Operator approval.** The onboarding request materializes as a `BSessionToken` component (`state` property:
   `unapproved`/`approved`/`rejected`/`expired`, `organized/signingService/vineflower/com/tridium/signing/transport/BSessionToken.java:98`) with `approve`/`reject` Actions
   (`organized/signingService/vineflower/com/tridium/signing/transport/BSessionToken.java:106-116`), the `reject` Action explicitly `security=true`-faceted
   (`organized/signingService/vineflower/com/tridium/signing/transport/BSessionToken.java:115`) — an ordinary Niagara operator Action-invoke permission gate, requiring a human
   with write/invoke rights on that component to click Approve/Reject in Workbench. This is the ONLY point in
   the entire flow gated by conventional Niagara component-security, not by the token/JWT machinery.
3. **Polling for approval.** `BFoxSigningRequester.checkOnboardingApproval()` calls `BSigningChannel.getToken
   (requesterId, temporaryCode)` (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:241-272`, client; `274-304`, server). Server returns an
   ordinal `tokenState` (0=pending, 1=rejected, 2=expired, 3=approved+token,
   `organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:254-265`); on `approved` it calls `getFoxSigningTransport().validateCode(...)` to mint
   the actual bearer `accessToken` (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:294`).
4. **CSR submission (new cert).** `BFoxSigningRequester.submitCertificateSigningRequest()` (non-renewal path,
   `organized/signingService/vineflower/com/tridium/signing/fox/BFoxSigningRequester.java:246-250`) calls `BSigningChannel.signCertificate(requesterId, accessToken, csr)`.
   The CSR is NOT sent as a raw wire field: it is embedded as a `"csr"` claim inside a **JWT signed HS256 with
   the raw `accessToken` bytes as the HMAC key** (`getJwtWithTokenSignature`, `organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:609-638`,
   `JWT_ALGORITHM_ID_TOKEN = "HS256"` at `:94`). Server-side `signCertificate(FoxRequest)`
   (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:383-430`) validates the JWT signature against the SERVER's own stored copy of that
   same token (`validateJwtWithToken`, `:841-893`, not fully quoted here but read in full), extracts the `csr`
   claim, and calls `BSigningService.processCsr(csr, profileId, requesterId, metadata, false)` under
   `SecurityUtil.doPrivileged` (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:409-420`).
5. **CSR submission (renewal).** `submitCertificateSigningRequest()`'s renewal branch instead calls
   `BSigningChannel.renewCertificate(requesterId, certAlias, certificatePassword, csr)`
   (`organized/signingService/vineflower/com/tridium/signing/fox/BFoxSigningRequester.java:240-244`), which signs the JWT with **RS256 using the requester's OWN EXISTING
   PRIVATE KEY**, extracted from its local keystore by `certificateAlias`+`certificatePassword`
   (`getJwtWithPrivateKeySignature`, `organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:530-536`, `JWT_ALGORITHM_ID_CERT = "RS256"` at
   `:93`) — a materially DIFFERENT, certificate-possession-based authentication model from the
   accessToken-HMAC model used for a first-time request, not merely a parameter variant. Server-side
   `renewCertificate(FoxRequest)` (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:552-592`) validates via `validateJwtWithCertificate`
   (`:894-911`, read in full) against the signing record's OWN previously-issued certificate
   (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:902`), then calls the SAME `processCsr(..., true)`.
6. **Retrieval.** `getCertificateSigningResult()` calls `BSigningChannel.getCertificate(...)` (token-authed:
   `:432-444`; cert-authed for renewal: `:446-460`), each again JWT-wrapping the request the same two ways.
   Server-side `getCertificate(FoxRequest, tokenValidation)` (`:462-528`) additionally cross-checks the signed
   record's `caFingerprint` against the profile's CURRENT CA fingerprint before releasing the chain
   (`:496-505`) — a stale-CA-rotation safety check not asked for by the gap but found in passing.

**Session-level and transport-level gates, all `[CERT]`:** `BSigningChannel.checkSessionIsSecure()`
(`:602-607`) throws unless `this.getConnection().session().isSecure()` — **"The signing channel can only be
used over TLS"** is enforced in code on every incoming request/circuit (`checkProcess`/`checkProcessCircuit`,
`:112-118`), not merely documented. `checkSendRequest`/`checkOpenCircuit` (`:120-140`) additionally refuse any
remote station below `Version.N5` — this channel is architecturally N5-only, confirming [Block 12] §12.11's own
framing of `signingService` as new in N5. `useSharedKeyEncryption()` returns `true` (`:108-110`), so the
`temporaryCode`/plain `accessToken` fields (steps 1, 3, and `getParams`'s own token argument) travel wrapped by
the Fox channel's own per-session shared-key encryption (`encrypt`/`decrypt` calls throughout), while the CSR-
bearing messages (steps 4-6) get the STRONGER JWT proof-of-possession treatment on top of that same channel
encryption — an intentional two-tier design (plain-encrypted for the onboarding/handshake steps, signed-proof
for the CSR/cert steps), not an inconsistency.

**Permission verdict — the gap's explicit "which messages require which permission" question.** A discrete
Niagara permission, `NiagaraBasicPermission.SIGNING_SERVICE_PERMISSION`, IS checked by
`SigningServiceUtils.checkRequestPermitted()` (`organized/signingService/vineflower/com/tridium/signing/
SigningServiceUtils.java:72-76`), which gates `BSigningService.registerRequester()`/`getRecord()`/
`getCsrParameters()` (`organized/signingService/vineflower/com/tridium/signing/BSigningService.java:130-132,
193-194, 202-203`). **But every remote-Fox call path into `processCsr()` (steps 4 and 5 above) invokes it
through `registerRequester()` from WITHIN a `SecurityUtil.doPrivileged` block** (`organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:
409-420`, `579-582`) — meaning this permission check runs fully-privileged and never actually constrains the
remote Fox caller; it only prevents a non-privileged LOCAL same-JVM API caller (not reachable via Fox) from
invoking those three methods directly. **The REAL authorization for the remote-Fox path is entirely the
cryptographic mechanism above** (TLS-required session + accessToken-HMAC-JWT or private-key-RS256-JWT proof of
possession), not a `NiagaraPermission` grant — the one Niagara-permission gate that exists is a no-op for the
protocol this gap asked about, and the one REAL human-authorization step is the `BSessionToken.approve`
Action's ordinary component-security check (step 2).

**Verdict: CLOSED.** All six Fox commands, both marshal directions, the two distinct proof-of-possession
mechanisms (HMAC-JWT for token holders, RS256-JWT for cert-renewal holders), the operator-approval gate, and
the TLS/version session requirements are traced end-to-end with file:line citations; the "which permission"
question is answered precisely (none, functionally, on the remote path — cryptographic proof substitutes for
it) rather than left open.

## 94.3 — B33-G6 CLOSED: N5's `nft` backend actively REJECTS `REDIRECT_RULE` at `validateRule`, and `BServerPort.updateFirewallRules()` no longer even constructs one — but a corpus-wide sweep finds ZERO shipped N5 services that configure a public≠local port split, so the narrowing has NO observable consequence for any service shipped today `[CERT]`

**Parent-block text, quoted verbatim** ([Block 33] §33.x): *"**B33-G6** — Determine whether N5's narrowing
from N4's NAT-redirect-capable `pf` backend to N5's input-only `nft` backend (§33.7) has an observable
operational consequence for any shipped N5 service that relied on a firewall-level port redirect."*

**The rejection is explicit and structural, not merely an unimplemented case:**
`NftablesFirewallProcessor.validateRule()` switches on `rule.getRuleType()`; for `REDIRECT_RULE` it falls into
the `default` branch and throws `InvalidRuleException("Rule type REDIRECT_RULE cannot be processed by " +
this.getFirewallName()")` (`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/
NftablesFirewallProcessor.java:52-62`) — only `INPUT_RULE` (`:52-56`) returns successfully. `FirewallRule.
RuleType` still declares BOTH `REDIRECT_RULE` and `INPUT_RULE` as enum constants
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/FirewallRule.java:45-48`) — the abstraction layer
retains the concept, only the `nft` implementation refuses it `[CERT]`.

**`BServerPort` itself no longer even attempts a redirect.** `BServerPort.updateFirewallRules()`
(`organized/baja/vineflower/niagara/firewall/BServerPort.java:277-319`) constructs `new InputRule(this.
getPublicServerPort(), ...)` (`:280-282`) unconditionally — never a `RedirectRule` — passing ONLY
`publicServerPort`. `InputRule`'s own constructor
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/InputRule.java:9-16`) sets
`this.publicServerPort = port; this.localServerPort = port;` — **collapsing public and local port into the
identical value**, discarding any distinct `localServerPort` the component may hold. This means the OS-level
`nft accept` rule (`NftablesFirewallProcessor.processRule`, already read [Block 40]) is always opened on
`publicServerPort`, regardless of what `localServerPort` a component's socket may actually be bound to.

**The narrowing is scoped to the opt-in `nft` backend specifically — the DEFAULT processor
(`NullFirewallProcessor`, active whenever `niagara.firewall.enabled` is unset/false, i.e. out of the box on
every N5 install) still accepts `REDIRECT_RULE` structurally, as a pass-through no-op.** Its own
`validateRule()` clones whichever rule type it receives — `REDIRECT_RULE` included — via
`new RedirectRule(oldRdr.getPublicServerPort(), oldRdr.getLocalServerPort(), ...)`
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/NullFirewallProcessor.java:11-14`), and both
`processRule()`/`processRules()` are empty method bodies (`:31-36`) `[CERT]`. This is in fact the ONLY
caller of `new RedirectRule(` anywhere in the N5 corpus (`find organized -name '*.java' -exec grep -l "new
RedirectRule("` returns exactly this one file) `[CERT]` — the class is reachable in code, just never fed a
genuinely split-port rule from anywhere real. So the rejection this section documents is specific to the
opt-in `nft` frontend, not a blanket N5 regression against the default (also-no-op, matching N4's own
historical default) processor.

**Whole-corpus sweep: zero shipped services actually use a split port.** `find organized -name '*.java' -exec
grep -l "setLocalServerPort"` returns exactly ONE file, `organized/baja/vineflower/niagara/firewall/BServerPort.java` itself (its own generated setter and
the 3-arg constructor's internal call) — no OTHER class in the N5 corpus ever calls it `[CERT]`. Every `new
BServerPort(...)` call site in the corpus was enumerated (`find organized -name '*.java' -exec grep -l "new
BServerPort("`, 9 files excluding `organized/baja/vineflower/niagara/firewall/BServerPort.java` itself) and read: `BModbusTcpSlaveNetwork.java:27,40`
(`new BServerPort(502, IpProtocol.TCP)`), `BWebService.java:170,174` (`80`/`443`), `BSnmpNetwork.java:744,746`
(`161`/`162`), `BTunnelService.java:107,142` (`9973`), `organized/nSnmp/vineflower/com/tridium/nSnmp/comm/BSnmpUdpCommConfig.java:20` (0-arg), `BFoxService.java:
189,193` (`1911`/`4911`), `organized/opcUaServer/vineflower/com/tridium/opcUaServer/BOpcUaServer.java:212` (0-arg), `BSecondaryHeartbeat.java:37,40` (`5911`) — every
single one uses the 1-/2-/0-arg constructor, none the 3-arg `(publicServerPort, localServerPort, protocol)`
form `[CERT]`, an exhaustive, whole-corpus negative-existence result satisfying METHODOLOGY's completed-search
requirement.

**Verdict: CLOSED.** The narrowing IS real and structural (an explicit `InvalidRuleException` plus a caller
that no longer even builds the rejected rule type), but it has **no observable operational consequence for any
N5 service shipped in this corpus today**, because none of them configure `publicServerPort != localServerPort`
by any traced code path. The residual, latent risk — an operator manually editing a live `BServerPort`'s
`localServerPort` property to differ from `publicServerPort` on a station with `niagara.firewall.enabled=true`
+ `frontend=nft` — would open the `nft accept` rule on the wrong (public) port while the JVM listens on the
local one; whether a live station's base `nft` chain policy makes this a silent connectivity failure (default-
deny) or a no-op (default-accept) is `[INFER]`, not confirmed live this session, and is named as **B94-G2**
below rather than folded into this CLOSED verdict.

## 94.4 — B40-G1 CLOSED: a Niagara slot name can NEVER contain a character `isRuleHintValid` would reject for its escaped part, EXCEPT underscore — a legal, common, unescaped slot-name character that `isRuleHintValid`'s stricter-than-described charset actively rejects, silently dropping the ENTIRE firewall accept rule for that port, not just its comment `[CERT]`

**Parent-block text, quoted verbatim** ([Block 40] §40.x): *"**B40-G1** — Trace `BComponent`'s station-config
RENAME path (what charset a component NAME is restricted to when an engineer renames it in Workbench/BQL) to
determine whether `BOpcUaServer.getName()` — concatenated into `ruleHintOverride` at `organized/opcUaServer/vineflower/com/tridium/opcUaServer/BOpcUaServer.java:614` —
could ever contain a character `NftablesFirewallProcessor.isRuleHintValid` (`[A-Za-z0-9.$]`) would reject, and
if so what happens to that OPC UA server's firewall rule (silently dropped, per
`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java:115-121`'s warn-and-`return`)."*

**The firewall's own regex is stricter than the gap's own paraphrase.** `isRuleHintValid`
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java:258-266`)
actually tests `!Character.isLetterOrDigit(character) && character != '.' && character != '$'` (`:260`) — this
is Java's UNICODE-AWARE `isLetterOrDigit`, not the ASCII-only `[A-Za-z0-9]` the gap's own paraphrase (echoing
[Block 40] §40.2's own prose) implies; a non-ASCII Unicode letter would in fact PASS this check. This is a
minor correction of [Block 40]'s own regex characterization, noted here in passing (not elevated to a §14
formal correction since it does not change that block's verdict).

**A component's escaped station name is confirmed, structurally, to be composed ONLY of `{A-Z, a-z, 0-9, _}`
for its unescaped characters, plus `$`+hex for anything else.** `BOpcUaServer.getName()` returns a
`SlotPath`-governed name; `SlotPath.isValidName()` delegates to `EscUtil.slot.isValid()`
(`organized/baja/vineflower/niagara/naming/SlotPath.java:121-123`). `EscUtil.SlotEsc.isStart`/`isPart`
(`organized/baja/vineflower/com/tridium/util/EscUtil.java:201-210`) test bits 2/4 of a static `charMap`
initialized at `:159-185`: bit 2 (CM_START) is set ONLY for `a-z`/`A-Z` (`:160-166`, value `6`); bit 4
(CM_PART) is set for `a-z`/`A-Z`/`0-9` (values `6`/`5`) AND, separately, for **underscore alone**
(`charMap[95] = 4;`, `:180`) — underscore is a legal, UNESCAPED slot-name "part" character (position 2+, e.g.
`"Room_1"`), while any OTHER character (space, hyphen, literal `.`, non-ASCII) is escaped via `getEscChar()`
(`'$'`, `:121-123`, the default not overridden by `SlotEsc`) into a `$xx`/`$uXXXX` hex sequence
(`escape()`, `:133-156`).

**The consequence: underscore is legal-and-unescaped in a slot name, but `isRuleHintValid` rejects it — so any
OPC UA server named with an underscore (a completely ordinary, common Niagara naming convention: `Room_1`,
`Comp_A`) breaks its own firewall rule.** `BOpcUaServer.initialize()` builds `this.bServerPort.
setRuleHintOverride("OPCUA.server." + this.getName())` (`organized/opcUaServer/vineflower/com/tridium/
opcUaServer/BOpcUaServer.java:614`) — if `getName()` contains an unescaped `_`, the resulting `ruleHint` fails
`isRuleHintValid`, and `NftablesFirewallProcessor.processRule` (`:113-122`, already read [Block 40]) logs a
warning and **returns before calling `executeFirewallAddRuleCommand`** — meaning the ENTIRE `nft accept` rule
for that server's port is never created, not merely its `comment` clause, since the `return` at `:121` exits
the whole rule-building method before the final `sb.append("comment...")`/`executeFirewallAddRuleCommand` lines
(`:113-125`) execute.

**Bonus closure of [Block 40]'s own sibling gap, B40-G2 (not itself assigned to this block, noted here as a
byproduct, not claimed as this block's own verdict).** [Block 40] §40.x's own **B40-G2** asked whether a
LIVE station's `BComponentSpace` returns `true`/`false` for `.getType().is(BOG_SPACE_TYPE_INFO)` — the one
fact its `BTunnelService.setRuleHintOverride` reachability verdict rested on. Tracing WHY the underscore case
above is not caught earlier by `BServerPort`'s OWN, STRICTER `isAlphanumeric`-based `validateSet` on
`ruleHintOverride` (`organized/baja/vineflower/niagara/firewall/BServerPort.java:207-225` — which rejects
`Character.isLetterOrDigit`-only, no `.`/`$` exception at all, so it would ALSO reject the literal `.` in
`"OPCUA.server."` itself) surfaced the answer: that validator only fires when `ComplexSlotMap.
setRequiresValidation(context)` returns `true` (`organized/baja/vineflower/com/tridium/sys/schema/
ComplexSlotMap.java:1800-1826`), and for the internal, null-context call `setRuleHintOverride()` makes
(`organized/baja/vineflower/niagara/firewall/BServerPort.java:134`, generated setter, `context=null`), that method returns `true` only if `space.
isProxyComponentSpace()` (`:1818`) or `space.getType().is(BOG_SPACE_TYPE_INFO)` (`:1826`) — **neither of which
is true for a live, normally-running station's own component space** — so `BServerPort`'s own stricter
validator is SKIPPED for this exact runtime call path, and the (less strict, but still underscore-rejecting)
`NftablesFirewallProcessor.isRuleHintValid` is the ONLY gate the string actually meets before reaching the OS
firewall layer. This is offered to the orchestrator as a candidate CLOSED verdict for [Block 40]'s own
B40-G2, not claimed as B94's own numbered gap.

**Verdict: CLOSED.** The concrete answer is yes: underscore is the realistic character class that breaks
`isRuleHintValid` while being a legal, unescaped, common Niagara slot-name character, and the consequence is
confirmed to be a fully-dropped accept rule (not just a missing comment), reached via a fresh trace of the
validation-skip mechanism that also resolves [Block 40]'s own sibling B40-G2.

## 94.5 — B40-G4 CLOSED (REFUTING the un-traced prose premise): N4 has ZERO `netsh`/`CAP_NET_ADMIN` references anywhere in the organized corpus; its ONLY OS-firewall mechanism is the same QNX-only `pfctl`-vs-`NullFirewallProcessor` binary choice [Block 33] already named as N5's `nft` predecessor `[CERT]`

**Parent-block text, quoted verbatim** ([Block 40] §40.x): *"**B40-G4** — Trace N4's `netsh`/`CAP_NET_ADMIN`
host-firewall-touching mechanism (`niagara-mental-model-bloque27.md:81`'s own un-traced prose claim) for a
possible `RuntimeExecPermission`-gated-but-caller-bypassed analogue to [Block 33] §33.6's N5 finding —
REMIT-only, not opened in either corpus this session."*

**The named source is explicitly unverified prose, by its own author's admission.** `/home/cristian/
niagara-research/niagara-mental-model-bloque27.md:81` reads: *"en Supervisor Windows el servicio niagarad.exe
tiene privilegios para tocar Windows Firewall vía netsh. En Linux requiere CAP_NET_ADMIN o sudo ... No
verifiqué todos los casos"* — the claim is stated as unverified speculation, not a traced finding.

**Whole-N4-corpus sweep: zero hits for either term.** `find /home/cristian/niagara-research/organized -name
'*.java' -exec grep -l "netsh"` and the same for `"CAP_NET_ADMIN"` both return NOTHING `[CERT]` — an exhaustive,
completed, whole-corpus negative-existence search satisfying METHODOLOGY's requirement.

**The actual mechanism, re-read fresh this session (upgrading [Block 33] §33.7's own `[CERT-a]` remittance
citation to a fresh direct `[CERT]`): `BServerPort.FirewallHolder`'s N4 static initializer
(`/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/firewall/BServerPort.java:
259-281`) selects between exactly TWO concrete processors, gated by ONE system property:** if
`Boolean.getBoolean("niagara.qnx.pfctl.enabled")` (`:257`, default `false`) is true, `fw = new
ConcurrentFirewallProcessor(new PfFirewallProcessor(pfctlPath, pfConfFile))` (`:260-267`, `pfctl`-path/conf-file
also read from system properties, QNX-specific per the property's own name); **otherwise, on EVERY OTHER
platform including Windows and generic Linux, `fw = new ConcurrentFirewallProcessor(new
NullFirewallProcessor())`** (`:275-276`) — a documented no-op, confirmed by its own log line, `"setting
firewall implementation to NullFirewallProcessor"` (`:276`). There is no third branch, no `OperatingSystemEnum`
check, and no code path that ever touches `netsh` or any Linux capability check. Note: `NullFirewallProcessor`
and `PfFirewallProcessor` themselves are absent from this corpus's `baja.jar` extraction (not even as `.class`
files) — they must ship in a platform-specific module this baseline did not capture; this absence does not
weaken the static-initializer finding above (which is entirely within N4's own `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/firewall/BServerPort.java`, fully present and
read) but is disclosed as a corpus-completeness caveat.

**Verdict: CLOSED, REFUTING the named prose premise.** N4 never touches Windows Firewall via `netsh` and never
checks `CAP_NET_ADMIN` anywhere in the organized corpus; its real (and QNX-gated, opt-in, default-OFF even on
QNX) OS-firewall integration is the identical `PfFirewallProcessor`/`NullFirewallProcessor` pluggable pair
[Block 33] §33.7 already identified via remittance — this session's fresh, direct read of the N4 source
upgrades that citation from `[CERT-a]` to `[CERT]` and additionally closes the netsh/CAP_NET_ADMIN half B33-G5
did not ask about.

## 94.6 — B53-G4 CLOSED: the runtime `cacerts` holds exactly 112 `trustedCertEntry` aliases (zero `PrivateKeyEntry`), 85 RSA (43×4096-bit, 42×2048-bit) + 27 EC (25×secp384r1, 2×secp256r1) keys, and `honeywellproductpkirsa` IS present as a self-signed, non-expiring trusted root `[CERT]`

**Parent-block text, quoted verbatim** ([Block 53] §53.6): *"**B53-G4** — Confirm the runtime's own
`<java.home>/lib/security/cacerts` (or `.bcfks` under FIPS) actually contains the Honeywell `Product PKI RSA`
root as a trusted CA entry — deliberately NOT opened this session (secrets discipline: this file lives under a
`security/` path); a future pass with explicit authorization to inspect alias/subject METADATA ONLY (e.g.
`keytool -list`, never exporting a key) could close this without violating the no-key-material rule."*

**Method, exactly as the gap's own text prescribed:** `keytool -list` and `keytool -list -v` against the live
install file `/mnt/c/Program Files/Niagara/5.0.0.28/jre/lib/security/cacerts` (`sha256
9b5319f17ab786587c2d1729a3b54b8cb9ef1a5acb9199f8a4660491e531e701`), default `changeit` store password (the
well-known, non-secret default JRE cacerts password), no `-exportcert`/no private-key operation run `[CERT]`.

**Structure, in full:** 112 total entries, `"Keystore type: PKCS12"`/`"Keystore provider: SUN"`; ALL 112 are
`trustedCertEntry` (`grep -c "Entry type: trustedCertEntry"` = 112; `"Entry type: PrivateKeyEntry"` = 0) — a
pure CA-root truststore, no private material present by construction, confirming the gap's own "no private
material" framing structurally rather than by omission `[CERT]`. Public-key-algorithm breakdown (`grep -c` over
`keytool -list -v` output): **43× 4096-bit RSA, 42× 2048-bit RSA, 25× 384-bit EC (secp384r1), 2× 256-bit EC
(secp256r1)** — 85 RSA + 27 EC = 112. Signature-algorithm breakdown: 39× `SHA256withRSA`, 32× `SHA1withRSA`
(legacy roots, expected for long-lived trusted CAs), 23× `SHA384withECDSA`, 14× `SHA384withRSA`, 4×
`SHA256withECDSA` `[CERT]`.

**The named entry is present, self-signed, and effectively non-expiring:** `Alias name:
honeywellproductpkirsa` / `Owner: CN=Honeywell Product PKI RSA, OU=ACS, O=Honeywell International Inc., C=US` /
`Issuer:` IDENTICAL to `Owner` (self-signed root) / `Valid from: Tue Aug 22 15:08:34 CDT 2017 until: Thu Dec 30
18:00:00 CST 9999` / `SHA256withRSA` / `4096-bit RSA key` `[CERT]` (`keytool -list -v` output, this session).

**Verdict: CLOSED.** Both halves of the gap's own text are answered: the Honeywell root is confirmed present
as a `trustedCertEntry`, and the full structural census (count/alias-class/key-algorithm) the gap additionally
asked for is delivered, with zero private-key material inspected or exported at any point.

## 94.7 — B81-G3 remains BLOCKED for live confirmation (same live-station blocker class as B81-G1/B54-G1/B54-G2/B61-G1/B65-G1) but is NARROWED on the packaging-defaults half: a fresh whole-file read of the live Windows Supervisor's own `system.properties` confirms zero `firewall`/`nft` occurrences anywhere in that file `[CERT]`

**Parent-block text, quoted verbatim** ([Block 81] §81.6): *"**B81-G3** — This session's `BServerPort`/
`NftablesFirewallProcessor` read is entirely static; confirm live (same blocker class as above) that a Linux
N5 install with `-Dniagara.firewall.enabled=true -Dniagara.firewall.frontend=nft` actually set produces working
`nft` rules end-to-end, and separately confirm via a fresh install/packaging read whether these two system
properties are ever set BY DEFAULT on a genuine Linux deployment (this session found only the Java-side
default-OFF code path, not any platform-specific launch script or installer default that might override it)."*

**Part 1 (live end-to-end confirmation): BLOCKED, unchanged.** No runnable N5 install, Linux or otherwise, was
available this session — the identical blocker class [Block 81] §81.6 itself named, shared with **B81-G1**/
**B54-G1**/**B54-G2**/**B61-G1**/**B65-G1**.

**Part 2 (packaging-defaults read): NARROWED with fresh, stronger negative evidence, still not fully closed.**
This session read the ENTIRE live `/mnt/c/Program Files/Niagara/5.0.0.28/defaults/system.properties` file
(41,936 bytes) directly — the same file [Block 87] §87.4 already cited for its JPMS-related commented-out
defaults (`niagara.add.reads`/`.enable.native.access`/`.add.exports`/`.add.opens`, confirmed present but
commented-out at `:691,709,729,748`, re-verified present this session at those same lines) — and found **ZERO**
occurrences of the strings `"firewall"` or `"nft"` anywhere in the file `[CERT]` (`grep -n "firewall\|nft"
"/mnt/c/Program Files/Niagara/5.0.0.28/defaults/system.properties"`, empty result). This means
`niagara.firewall.enabled`/`niagara.firewall.frontend` are not even DECLARED (commented-out or otherwise) in
the one cross-platform properties template this Windows Supervisor install ships — a stronger result than
[Block 33] §33.7's/[Block 40] §40.3's own "not determined this session" (which did not report a whole-file
sweep of this specific file). This still cannot distinguish between "no platform ever defaults these on" and
"a JACE-class embedded-Linux platform's OWN, separate distribution overrides this file with its own defaults"
— this session's access remained Windows-Supervisor-only, the same limit **B33-G5**/**B40-G3** already named.

**Verdict: Part 1 BLOCKED (unchanged); Part 2 NARROWED (stronger negative-existence evidence, still not
closed — same missing-Linux-install blocker as B33-G5/B40-G3, carried forward, not reopened as a new gap).**

## 94.8 — B87-G2 CLOSED, REVERSING Block 87's own `[INFER]` naming-adjacency guess: the FIPS-mode byte at `this+0x1002c` is set by `NreLauncherWin32::initFips()` — a license-feature check, then a `-fips=true/false` CLI-argument scan, then the `bajaui-FipsOptions.options` file read — NOT by `defaultToNonFIPS()`, which has ZERO call-instruction cross-references anywhere in `nre.dll` `[CERT-hw]`

> **Correction (added by [Block 117], §14 cross-block, §117.x).** "sole setter" of `this+0x1002c` holds for policy only; the constructor, copy constructor, operator= and getInstance also write the byte during initialisation.

**Parent-block text, quoted verbatim** ([Block 87] §87.x): *"**B87-G2** — Disassemble `NreLauncherWin32`'s own
setter/origin for the FIPS-mode byte at `this+0x1002c` (read but not traced to its own write site this
session) to confirm it is set FROM `defaultToNonFIPS()`'s own `bajaui-FipsOptions.options` file read (the
natural reading, given the function name and adjacency) rather than a separate license/registry check not yet
located — the one part of §87.5's B17-G3 recipe resting on an `[INFER]` naming-adjacency rather than a traced
data-flow edge."*

**`defaultToNonFIPS()` has ZERO call-instruction cross-references anywhere in `nre.dll`.** `r2 -q -A -e
bin.relocs.apply=true -c 'axt @ 0x180006740'` (the function's own address) returns nothing; a full linear `pd
20000 @ entry0` disassembly dump (`full_disasm.txt`, this session) contains zero `call` instructions targeting
`0x180006740` anywhere in the binary — the only two hits for the string `"defaultToNonFIPS"` are (a) internal
call-XREF annotations FROM inside the function itself to unrelated helpers (`memset`/`fopen_s`/`fseek`/
`strstr`), and (b) the function's own mangled name appearing as a plain data string at `0x1800148ba`, inside a
`.rdata` alphabetical symbol-name table (`"?dumpThreads@NreWin32@@UEAAXXZ"`, `"?encrypt@DpapiHelper@@..."`
immediately adjacent — a debug/PDB-derived name list, not code, confirmed by `axt @ 0x1800148ba` also returning
zero real xrefs) `[CERT-hw]`. **`defaultToNonFIPS` is therefore dead code in this build, or invoked only from
OUTSIDE `nre.dll`** (not disassembled this session — out of scope, `wb.exe`/another binary).

**The actual setter is `NreLauncherWin32::initFips(int argc, char** argv)`** (`sym.nre.dll__initFips_
NreLauncherWin32__AEAAHHPEAPEAD_Z`, `0x180006970`, 563 bytes, called from exactly one site,
`NreLauncherWin32::nre()` at `0x180007bd6` — `axt`-confirmed, single caller), whole-function `pdf` this
session (`initFips.txt`). Its logic, traced instruction-by-instruction:
1. `LicenseUtil::isFeaturePresent("Tridium", "fips140")` (`0x1800069ae`) — the result is written to `this+
   0x1002c` immediately (`mov byte [rsi+0x1002c], al`, `0x1800069b3`) — if the license feature is ABSENT, the
   function returns early (`je 0x180006b79`, `0x1800069bb`) leaving the byte at `0` (non-FIPS).
2. If present, a second guard checks `dword [rsi+0x10028]` (a separate field, not the FIPS byte) — if zero,
   also returns early, leaving the byte at the license-check value (`1`, since this branch is only reached when
   the license IS present) (`0x1800069c1-0x1800069c8`).
3. Otherwise, it scans `argv[1..argc-1]` for a `"-fips"`-prefixed argument (`strncmp`, `0x1800069f4`), matching
   exactly `"-fips=true"` (sets the byte to `1`, `0x180006aa4`) or `"-fips=false"` (sets it to `0`,
   `0x180006a98`) via `strcmp` (`0x180006a08`/`0x180006a1f`).
4. **Only if NO `-fips=...` CLI argument is found** does it fall through to read `${configHome}\etc\options\
   bajaui-FipsOptions.options` via `fopen_s`/`fread` (`0x180006a4e-0x180006b32`) and search for the SAME marker
   string `defaultToNonFIPS()` also searches for, `"<p n=\"startWorkbenchInFipsMode\" v=\"false\"/>"`
   (`0x180006b34`) — but with **INVERTED polarity from `defaultToNonFIPS()`**: `initFips` sets the byte to `1`
   (FIPS ON) when the marker is ABSENT (`sete bl` after a NULL `strstr` result, `0x180006b4a`, then `mov byte
   [rsi+0x1002c], bl`, `0x180006b73`), i.e. **FIPS defaults ON unless the file explicitly declares it off** —
   the opposite of what a function named `defaultToNonFIPS` would suggest, and the opposite of what [Block 87]
   §87.5's own reading assumed. `defaultToNonFIPS()` itself, by contrast (re-read this session,
   `0x180006740-0x1800068d8`), returns `true` (meaning "should default to non-FIPS") only when that SAME
   marker IS found (`setne dil` after a non-NULL `strstr`, `0x18000687a`) — the two functions read the identical
   file and marker but compute logically INVERTED, functionally unrelated results, and (per the zero-xref
   finding above) `defaultToNonFIPS()`'s result is never even consulted for the byte at `this+0x1002c`.

**This is a §14-class correction to [Block 87] §87.5's own claim**, recorded formally in the Corrections
section below rather than only here, since §87.5's "B17-G3 CLOSED to practical completeness" verdict explicitly
named `defaultToNonFIPS()` as the resolving mechanism for the `bcfips`-vs-`bcstd` module-path choice.

**Verdict: CLOSED**, with the full setter now traced to a concrete function, call site, and three-tier
precedence (license feature → CLI flag → config file, in that order), reversing the block's own prior
`[INFER]`-naming-adjacency guess with a direct, evidenced disassembly.

## 94.9 — B87-G3 CLOSED: the `--add-exports=niagara.nre/com.tridium.nre.security.permissions.restricted=niagara.niagarad` flag in `njre.dll` is emitted UNCONDITIONALLY, in the same straight-line, no-branch flag-building sequence as the already-documented 43-flag list — confirming such static per-module flags are the launcher's NORMAL behavior, sharpening (not resolving) the question of why no equivalent exists for `securityBridge` `[CERT-hw]`

**Parent-block text, quoted verbatim** ([Block 87] §87.x): *"**B87-G3** — `njre.dll`'s own
`--add-exports=niagara.nre/com.tridium.nre.security.permissions.restricted=niagara.niagarad` literal (found
this session via `strings`, distinct from any flag in `nre.dll` — a real, concrete precedent that the native
launcher DOES sometimes emit module-specific `--add-X` flags, just never one naming `securityBridge`) was found
but its own call site/conditional gate was not disassembled this session — confirm whether it is unconditional
(like `securityBridge`'s bootclasspath entry, §87.4) or gated on some runtime condition, and whether ITS
existence changes the reading of why no equivalent flag exists for `securityBridge`."*

**One call-instruction cross-reference, resolved to a single, unconditional basic block.** `axt @ 0x18000a130`
(the string's own address in `njre.dll`) returns exactly one xref:
`sym.njre.dll__buildArgs_JavaLauncherWin32__AEAAHHPEAPEAD_Z` at `0x180002e02` `[CERT-hw]`. The whole-function
`pdf` of `buildArgs` (`njre_buildArgs.txt`, this session, 2454 bytes) shows the flag's `lea rcx, str...`
instruction sits in a **straight-line sequence with NO conditional branch (`je`/`jne`/`jl`/etc.) anywhere
between it and its two immediate neighbors**: `--add-opens=java.base/java.net=niagara.nre` (`0x180002de7`) →
`--add-exports=niagara.nre/com.tridium.nre.security.permissions.restricted=niagara.niagarad` (`0x180002e02`,
the flag this gap names) → `--enable-native-access=niagara.nre` (`0x180002e2e`) — each immediately followed by
an unconditional `strdup`+store into the growing VM-args array, right after the `buildVMOptions` call
(`0x180002ddb`) that starts this literal-flag block. This is architecturally IDENTICAL to [Block 87] §87.4's
own finding for `securityBridge`'s `-Xbootclasspath/a:`/`-javaagent:` pair — an unconditional, always-emitted
literal, not a runtime-gated one.

**Reading consequence.** Since this flag IS unconditional — exactly like the other 43+ flags [Block 63]/[Block
87] already documented — the launcher's normal behavior is to hardcode MANY unconditional, module-specific
`--add-X` flags (this one, `--add-opens=java.base/java.net=niagara.nre`, `--enable-native-access=niagara.nre`,
and the 43-entry list). The absence of an equivalent unconditional `--add-reads .../=niagara.securityBridge`
flag anywhere in either DLL's strings (already established `[CERT-hw]` at [Block 87] §87.4) is therefore **NOT
explained by "such per-module flags are conditionally rare"** — they are the launcher's ordinary, common
pattern — which SHARPENS rather than resolves the original puzzle [Block 81]/[Block 65]/[Block 3] opened: if
the launcher freely hardcodes unconditional module-specific flags elsewhere, the missing `securityBridge`
readability flag looks more like a genuine gap in the flag list (relying on some OTHER mechanism entirely, or a
latent `IllegalAccessError` risk simply not hit by the corpus's actual call patterns) than like an instance of
a generally-rare practice.

**Verdict: CLOSED.** The call site is resolved to a single, unconditional straight-line basic block with
file:line/address citations on both ends; the "does its existence change the reading" question is answered
(yes — it strengthens the puzzle rather than dissolving it), without overclaiming a resolution to the
still-open `securityBridge` readability question itself (unchanged, tracked elsewhere as **B81-G1**/**B87-G1**).

**On-theme bonus, not previously stated by [Block 63]/[Block 76]/[Block 87]: this flag lives inside the
platform daemon's OWN native launcher, not a generic one.** `objdump -p` this session establishes the exact
binary-to-DLL binding neither prior block stated: `niagarad.exe` imports `njre.dll` (`??1JavaLauncher@@UEAA@XZ`
— `JavaLauncherWin32`, the class `buildArgs` above belongs to), while `n5mig.exe`/`wb.exe` import `nre.dll`
(`??1NreLauncher@@UEAA@XZ` — `NreLauncherWin32`, the SEPARATE class §94.8's `initFips`/`defaultToNonFIPS`
belong to) `[CERT-hw]`. The platform daemon's own native launcher is therefore the one hardcoding an
unconditional JPMS export grant naming the platform daemon's own module (`niagara.niagarad`) — a
self-referential detail directly on this block's own "platform daemon" theme.

## 94.x — Corrections to earlier blocks

- **[Block 87] §87.5** ("B17-G3 CLOSED to practical completeness") wrote: *"The `bcfips`-vs-`bcstd` choice is
  itself resolvable without further disassembly: `NreLauncherWin32::defaultToNonFIPS()` reads a plain-text
  config file, `${configHome}\etc\options\bajaui-FipsOptions.options`, via `fopen_s` — not a hidden registry/
  license check — so the FIPS mode a real launch would select is directly readable from that file."* **This
  session's §94.8 disassembly of `initFips()` (the function ACTUALLY called from `nre()` and the ONLY writer
  of the `this+0x1002c` byte that gates the `bcfips`/`bcstd` choice) shows this was incomplete in two ways:**
  (1) `defaultToNonFIPS()` is not the resolving mechanism at all — it has zero call-instruction xrefs anywhere
  in `nre.dll` (§94.8); (2) the real recipe is NOT "just read the options file" — it is a three-tier
  precedence (a `LicenseUtil.isFeaturePresent("Tridium","fips140")` gate first, THEN a `-fips=true`/`-fips=false`
  CLI-argument override, and ONLY THEN the options-file read as a fallback, with INVERTED polarity from what
  `defaultToNonFIPS()` would have computed for the same file). A `java`-fallback `n5mig` relaunch attempting to
  reconstruct the `bcfips`-vs-`bcstd` module-path entry per §87.5's own recipe would need the license-feature
  state and any `-fips=...` CLI argument, not just the options file, to compute the correct value.

## 94.x — Child gaps opened

- **B94-G1** — Identify the actual caller of `BPlatCryptoManager.make(BDaemonPlatform)` (the concrete
  `BDaemonPlatform`/commissioning-tooling class that constructs the daemon-side crypto manager) — §94.1 confirms
  `BCertManagerService` is NOT that caller, but the true caller was not itself opened this session.
- **B94-G6** — Trace `getCertHealth`/`getPasswordStrength`'s actual caller — no class under
  `platcrypto/daemon/messages/` targets either `CryptoServlet` action, suggesting a direct browser/JS caller of
  the `crypto` servlet unmodeled by the traced Java message classes (§94.1).
- **B94-G7** — Open `BSigningService.processCsr`'s own CA-signing internals (the actual CSR→certificate
  cryptographic step both §94.1's crypto-manager cluster and §94.2's Fox channel call as a boundary but neither
  this block nor [Block 12] opened), and confirm why `generateCsr`/`getParams` authorize via
  `KeyStorePermission.checkRead` rather than `checkWrite` despite being CSRF-gated, state-changing actions in
  `CryptoServlet`'s own `update=true` set — a possible read/write permission-model inconsistency spotted in
  passing (§94.1).
- **B94-G2** — Confirm live (same blocker class as B81-G1/B54-G1/B54-G2/B61-G1/B65-G1) whether a real N5
  station's default `nft` base-chain policy is default-deny or default-accept, to determine whether the
  latent `publicServerPort != localServerPort` misconfiguration trap named in §94.3 would manifest as a silent
  connectivity failure or a no-op if an operator ever manually triggers it.
- **B94-G3** — Disassemble `defaultToNonFIPS()`'s actual caller, if one exists outside `nre.dll` (`wb.exe` or
  another native binary not read this session) — §94.8 confirms zero call-instruction xrefs WITHIN `nre.dll`
  but cannot rule out an external caller via a shared export/ordinal this session's scope did not cover.
- **B94-G4** (low priority) — Locate `NullFirewallProcessor`/`PfFirewallProcessor`'s own class definitions in
  the N4 corpus (§94.5 confirms they are referenced by N4's own `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/firewall/BServerPort.java` but are absent from `baja.jar`'s own
  extracted/decompiled contents — they must ship in a different, uncaptured module).
- **B94-G5** (blocked-on-source, same as B33-G5/B40-G3) — Obtain a JACE-class embedded-Linux N5 distribution's
  own packaging/install files to find where (if anywhere) `niagara.firewall.enabled=true`/`frontend=nft` are
  set by default — §94.7 strengthens the negative result on the Windows Supervisor side but cannot reach a
  Linux/JACE install this session.

## 94.x — Connections

- **[Block 81]/[Block 54]/[Block 61]/[Block 65]** — §94.7 (B81-G3, Part 1) and §94.1/§94.2's own Fox-session
  live-behavior claims remain bounded by the same shared live-station blocker these blocks first named; not
  reopened, only re-confirmed as still blocking.
- **[Block 33]** — §94.3 closes **B33-G6**, its own named gap; §94.5 upgrades §33.7's `[CERT-a]` N4 remittance
  citation to a fresh direct `[CERT]` re-read and additionally closes the netsh/CAP_NET_ADMIN half neither
  §33.6 nor §33.7 investigated.
- **[Block 40]** — §94.4 closes **B40-G1** and, as a bonus not claimed as this block's own numbered gap,
  supplies direct evidence resolving [Block 40]'s own sibling **B40-G2** (the live-`BComponentSpace`/
  `BOG_SPACE_TYPE_INFO` question); §94.5 closes **B40-G4**.
- **[Block 12]** — §94.1 closes **B12-G2** outright (HTTP transport, action inventory, both permission layers;
  corrects the gap's own assumed `BCertManagerService`→`BPlatCryptoManager` call chain); §94.2 closes **B12-G3**
  outright with a full six-command protocol trace. The two clusters share infrastructure: `BAbstractSigningRequester`/
  `BApprovalState` (§94.2) live in `com.tridium.platcrypto.signing` — the SAME `platCrypto` module §94.1
  traces — not in `signingService` itself, a connection neither [Block 12] nor this block's own gap list named
  explicitly.
- **[Block 53]** — §94.6 closes **B53-G4** exactly per its own prescribed method (`keytool -list`, metadata
  only).
- **[Block 87]** — §94.8 closes **B87-G2**, REVERSING §87.5's own `defaultToNonFIPS`-attribution (formal
  correction above); §94.9 closes **B87-G3** and sharpens (does not resolve) the still-open `securityBridge`
  readability question tracked at **B81-G1**/**B87-G1**.
- **REMITTANCE → `niagara-research`** — §94.5's N4 `BServerPort.FirewallHolder` re-read
  (`/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/firewall/BServerPort.java:
  259-281`) is a fresh, direct, same-session confirmation of the N4 baseline [Block 33] §33.7 previously only
  cited via a secondary (`[CERT-a]`) remittance from `niagara-mental-model-bloque625.md`.

## Self-verify

Ran `bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
/home/cristian/niagara5-research/niagara5-block94.md` from `/home/cristian/niagara5-research` this session
(output not pasted into the body per instruction; tally below is manually reproduced from that run's counts).

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `defaultToNonFIPS` has zero call-instruction xrefs in `nre.dll` | [CERT-hw] | `axt @ 0x180006740` empty; `full_disasm.txt` zero `call 0x180006740` |
| 2 | `initFips()` is the sole setter of `this+0x1002c`, called once from `nre()` | [CERT-hw] | `initFips.txt` whole-function `pdf`, single CALL XREF header |
| 3 | `initFips` precedence: license feature → `-fips=` CLI arg → options-file (inverted polarity) | [CERT-hw] | `initFips.txt:0x1800069ae-0x180006b73` |
| 4 | `njre.dll`'s `--add-exports=.../niagara.niagarad` flag sits in an unconditional straight-line block | [CERT-hw] | `njre_buildArgs.txt`, `0x180002ddb-0x180002e5x`, no branch between neighbors |
| 5 | `NftablesFirewallProcessor.validateRule` rejects `REDIRECT_RULE` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java:52-62` |
| 6 | `BServerPort.updateFirewallRules` (N5) builds `InputRule` only; `InputRule` collapses public/local port | [CERT] | `organized/baja/vineflower/niagara/firewall/BServerPort.java:280-282`; `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/InputRule.java:9-16` |
| 7 | Zero corpus call sites use the 3-arg split-port `BServerPort` constructor | [CERT] | 9-file `grep -l "new BServerPort("` sweep, each site read |
| 8 | `isRuleHintValid` uses `Character.isLetterOrDigit`, not ASCII `[A-Za-z0-9]` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/nft/NftablesFirewallProcessor.java:258-266` |
| 9 | Slot-name underscore is a legal unescaped PART char; `.`/others get `$`-escaped | [CERT] | `EscUtil.java:159-185,201-210` |
| 10 | `setRequiresValidation` skips validation for a live (non-proxy, non-Bog) component space | [CERT] | `organized/baja/vineflower/com/tridium/sys/schema/ComplexSlotMap.java:1800-1826` |
| 11 | N4 corpus has zero `netsh`/`CAP_NET_ADMIN` hits | [CERT] | whole-corpus `find -exec grep`, both terms, empty |
| 12 | N4 `FirewallHolder` selects `PfFirewallProcessor` (QNX, opt-in) or `NullFirewallProcessor` (default) | [CERT] | N4 `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/firewall/BServerPort.java:259-281` |
| 13 | Runtime `cacerts`: 112 entries, all `trustedCertEntry`, 0 `PrivateKeyEntry` | [CERT] | `keytool -list -v`, this session |
| 14 | `honeywellproductpkirsa` present, self-signed, `SHA256withRSA`, 4096-bit RSA | [CERT] | `keytool -list -v` output, this session |
| 15 | `system.properties` (live install) has zero `firewall`/`nft` occurrences | [CERT] | whole-file `grep`, this session |
| 16 | `signingService`'s 6 Fox commands + 2 JWT signature modes traced end-to-end | [CERT] | `BSigningChannel.java` (multiple line ranges cited above), `BFoxSigningRequester.java` |
| 17 | `SIGNING_SERVICE_PERMISSION` check runs inside `doPrivileged`, is a no-op for the remote path | [CERT] | `organized/signingService/vineflower/com/tridium/signing/fox/BSigningChannel.java:409-420,579-582`; `organized/signingService/vineflower/com/tridium/signing/SigningServiceUtils.java:72-76` |
| 18 | `BCertManagerService` selects `CoreCryptoManager`/`ChannelCryptoManager` by session type; never calls `BPlatCryptoManager` | [CERT] | `organized/platCrypto/vineflower/com/tridium/platcrypto/core/BCertManagerService.java:104-117` |
| 19 | `platCrypto` daemon transport is HTTP (`crypto?action=...`) via `BDaemonSession`, served by `CryptoServlet` | [CERT] | `BDaemonSession.java:923-933,152`; `CryptoServlet.java:79,86-89`; `CryptoServletMessage.java:11,18` |
| 20 | `CryptoServlet` daemon-side admin gate requires `hasHostAdminAccess()` for nearly every action | [CERT] | `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/util/DaemonAuthUtil.java:80` |

**Tally (exact, from the actual tool run, this session, `== exit 0 ==`):** raw marker counts — `[CERT-hw]` 13
(adj 11), `[CERT]` 52 (adj 50), doc-grade and web-grade markers 0 raw/0 adjusted (this block uses neither —
the header legend names them only in prose, not in bracket form, so no self-reference pollutes the count),
`[CERT-a]` 6 (adj 5; all quote [Block 33]'s OWN marker on ITS OWN citation, not a fresh claim of this block's
own — see §94.5/Connections/Corrections text), `[INFER]` 8 (adj 6). Ratio `[INFER]`/`[CERT]`-family
(adjusted) = 6/66 ≈ 0.09 — an EVIDENCE block, consistent with a low ratio for a `mixed`-type block that mostly
closes gaps with fresh evidence rather than leaving inference open. Citation resolution: 39 of 45 backticked
`file:line` tokens resolved against this corpus; the 6 unresolved are legitimate cross-repo/cross-format
`extern` citations — into `/home/cristian/niagara-research` (the N4 baseline corpus, a different git root the
script cannot resolve into by design) and `niagara-mental-model-bloque27.md` (a prose source document, not a
`.java` file) — the script's own `== exit 0 ==` confirms none of these are treated as a failure.

**Artifacts:** scratchpad `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/
scratchpad/b94/` holds `nre.dll`/`njre.dll` (re-hashed copies, matching [Block 87]), `initFips.txt`,
`defaultToNonFIPS.txt`, `nre_initPaths_full.txt`, `njre_buildArgs.txt`, `full_disasm.txt`, `funcs.txt`,
`cacerts_verbose.txt` — not archived in the corpus, scratch only, per this task's own instruction.
