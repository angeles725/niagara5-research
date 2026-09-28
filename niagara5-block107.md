# Block 107 — Four `signingService`/`platCrypto`/`*Rpc` permission-census child gaps closed: real JDK PKIX chain validation empirically confirmed (and empirically defeated) against the B99 misissuance shape, `BSelfSignedDialog` Workbench reachability traced, a new null-Context call-site sub-shape found, and the LON read-gates-write pattern confirmed non-recurring

> Research closing/narrowing four previously-opened child gaps from [Block 99] §99.x: **B99-G1**
> (medium priority — does any downstream Niagara consumer of a `signingService`-issued certificate
> perform CA-chain/path validation, as opposed to leaf-pinning/hostname-only validation, bearing on
> §99.6c's `BasicConstraints{CA:TRUE}`-on-a-non-CA-profile issuance defect); **B99-G3** (low priority —
> Workbench/UI reachability of §99.6b's ungated `BPlatCryptoManager.generateSelfSignedCert`/
> `resetUserKeyStore`); **B99-G4** (low priority — extend the null-Context census beyond [Block 99]
> §99.2's own declared-variable-shape 41-hit sweep, to a caller/callee split or a non-standard wrapper
> method name); **B99-G5** (low priority — does `BLonworksRpc.startJob()`'s read-gates-a-write shape,
> §99.1 Step 5, recur elsewhere among the corpus's `*Rpc` classes). Does **not** cover: a live two-party
> TLS handshake against a real N5 station (this session's PKIX proof is a standalone `CertPathValidator`
> unit test against hand-built certificates, not a live `BFoxClientConnection`/`httpClient` socket
> negotiation); a full semantic caller/callee-split trace of the null-Context census (B99-G4's own
> "neither mechanical" framing stands — this session extended the census by one genuinely new,
> still-mechanical shape (`getPermissions(null)` as a literal call-site argument) rather than performing
> full call-graph tracing); an exploitability trace of the new `BFoxHistorySpace` finding opened as a
> child gap below, not chased further this session.
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> N5 install (READ-ONLY): `/mnt/c/Program Files/Niagara/5.0.0.28`. N5 config/modules mirror (READ-ONLY):
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules`. Method: decompiled source reads for the
> consumer-census/reachability/wrapper-shape gaps (B99-G1's consumer-identification half, B99-G3, B99-G4,
> B99-G5); a live `keytool`+small Java harness experiment run against the REAL bundled Windows
> `jre/bin/{keytool,javac,java}.exe` (Zulu OpenJDK `25.0.4`, same JRE [Block 55]/[Block 106] used) via WSL
> interop, building two hand-crafted 3-certificate chains and validating them with
> `java.security.cert.CertPathValidator.getInstance("PKIX")` (B99-G1's decisive empirical half). Scratch
> (never committed): `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/
> scratchpad/b107/` (`tmfcheck/` — `TrustManagerFactory` algorithm-resolution probes; `pkixtest/` — the two
> keystores/cert chains and the `PkixTest.java` harness + its output).
>
> Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) · `[CERT-hw]`
> live/real-binary evidence, this session, real bundled JRE (sha256/version cited) · `[INFER]` deduction.
>
> **Type:** `mixed` — §107.1–§107.4 cite pre-existing `organized/`-tree files (resolve under this corpus's
> own `file:line` check); §107.1's decisive PKIX-validation proof is this session's own fresh scratchpad
> harness output against the real bundled JRE (correctly `extern`/non-file-verifiable, per METHODOLOGY
> §11's decompiled/external-evidence precedent).

---

## 107.1 — B99-G1 CLOSED: N5's own TLS-peer trust manager (`CoreClientTrustManager`, reused by 13+ modules including `fox`/`httpClient`/`cloudLink`/`opcUaClient`) performs REAL JDK PKIX certificate-chain validation — and this session's own live `CertPathValidator` reproduction proves that validation does NOT stop the §99.6c misissuance: a cert improperly carrying `BasicConstraints{CA:TRUE}` is accepted by the JDK exactly as a legitimate intermediate CA would be `[CERT]` + `[CERT-hw]`

[Block 99] §99.x's own text: *"Confirm live ... whether any downstream Niagara consumer of a
`signingService`-issued end-entity certificate (§99.6c) performs CA-chain/path validation (as opposed to
leaf-pinning/hostname-only validation) — this determines whether the `BasicConstraints{CA:TRUE}`-on-a-
non-CA-profile issuance defect is exploitable beyond the code-level policy gap itself. `investigable` —
would need to open every `BISigningTransport`/certificate-consumer implementation and trace its
validation logic."*

**Step 1 — where a `signingService`-issued cert actually goes.** `BCombinedSignedCertConfig
.certificateSigned(X509Certificate[])` (the object [Block 99] §99.6 itself traced the issuance defect
through) applies the freshly-signed certificate directly to **`BFoxService`, `BWebService`, and the
platform daemon's own SSL settings** as each service's OWN server-identity certificate `[CERT]`
(`organized/signingService/vineflower/com/tridium/signing/BCombinedSignedCertConfig.java:433-435`,
`applySignedCertificateToService`/`applySignedCertificateToPlatform`, `:539-602`) — i.e. this cert's
real-world "downstream consumer" is whatever TLS CLIENT later connects to this station's fox/https/
platform endpoint and validates the presented server certificate.

**Step 2 — that consumer-side validation is `CoreClientTrustManager`, corpus-wide.** A search for
`X509TrustManager`/`TrustManagerFactory`/`SSLContext` usage finds `com.tridium.crypto.core.io
.CoreClientTrustManager` referenced from **13 files across 10 modules**: `fox` (`BFoxClientConnection`),
`httpClient` (`WebsocketClientHolder`), `cloudLink`/`cloudLinkAzure`-style transports
(`BHttpTransport`, `BNiagaraRemoteTransport`), `opcUaClient`/`opcUaServer` (their own certificate
validators), `platCrypto` (`BDaemonSecureSession`), `awsUtils`, `jxBrowser`, and the `nre`/`niagarad`
cloud transports `[CERT]` (`grep -rl CoreClientTrustManager organized --include=*.java`, this session, 13
hits). `CoreClientTrustManager.initializeTrustManagers()` builds its delegate list from **real JDK
`TrustManagerFactory.getInstance("X509")`** instances, initialized against BOTH the station's own
Niagara-managed "user trust store" and the JDK's own `lib/security/cacerts` "system trust store"
`[CERT]` (`organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/io/CoreClientTrustManager.java:
62-92`); `checkServerTrusted`/`checkClientTrusted` (`:179-216`) delegate to each in turn and only fall
through to a SEPARATE, narrower TOFU-style leaf-fingerprint exemption flow (`TridiumCertValidator`/
`ExemptionApprover`/`NHostExemption`, `:279-401`) if-and-only-if the real trust-manager chain check
THROWS — i.e. the exemption/pinning path is a fallback for an UNTRUSTED chain, not a replacement for
chain validation on a trusted one. `CoreCryptoManager`'s system trust store is confirmed to be the literal
JDK `lib/security/cacerts` file `[CERT]` (`organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/
io/CoreCryptoManager.java:807-818`); the user trust store is the station's own admin-managed trust store
— the standard place an operator imports a fleet-internal CA (such as a `signingService` CA) specifically
so peer stations will trust certs it issues, which is this whole feature's intended deployment model.

**Step 3 — live confirmation that `TrustManagerFactory.getInstance("X509")` (the exact literal string
`CoreClientTrustManager` uses) is a REAL PKIX validator, not the simplified `SunX509` leaf-only algorithm.**
This session ran a small Java harness against the REAL bundled Windows `jre/bin/java.exe`
(`Zulu25.36+16-SA`, `openjdk 25.0.4`, confirmed this session, same JRE [Block 55]/[Block 106] used)
`[CERT-hw]`:

```
Registered TrustManagerFactory algorithms: [SUNX509, PKIX]
getInstance("X509")  -> validatorType = PKIX
getInstance("PKIX")  -> validatorType = PKIX
getInstance("SunX509") -> validatorType = Simple
```

(`/tmp/.../scratchpad/b107/tmfcheck/TmfCheck3.java` + output, this session, reflectively reading
`sun.security.ssl.X509TrustManagerImpl`'s private `validatorType` field via
`--add-opens java.base/sun.security.ssl=ALL-UNNAMED`). **`"X509"` — the exact algorithm string
`CoreClientTrustManager.java:66,79` passes to `TrustManagerFactory.getInstance` — resolves to the SAME
internal `PKIX` validator type as explicitly requesting `"PKIX"`,** and is distinct from `"SunX509"`'s
`Simple` (leaf-only, no chain-building) validator. `[Block 95]`/`[Block 53]`'s own prior finding that the
module-signing (TPK) validation path also uses `CertPathValidator.getInstance("PKIX")`/`PKIXParameters`
(`CertificateChainValidator.java`) is independent corroboration that genuine PKIX-family validation, not
leaf-pinning, is the corpus's standard pattern for BOTH major certificate-consumer families (TLS peer
trust and module-signature trust).

**Step 4 — the decisive experiment: does that real PKIX validation actually BLOCK the §99.6c misissuance
shape, or does it accept it?** This session built two 3-certificate chains with the real bundled
`keytool.exe`, using a common self-signed root, and validated each with
`java.security.cert.CertPathValidator.getInstance("PKIX")` + `PKIXParameters` (trust anchor = the root,
revocation disabled) — the exact same JDK API `X509TrustManagerImpl`'s `PKIX` validator type wraps
internally `[CERT-hw]` (`/tmp/.../scratchpad/b107/pkixtest/PkixTest.java` + live output, this session):

| Chain shape | Intermediate's `BasicConstraints` | PKIX `CertPathValidator` result |
|---|---|---|
| **Baseline** — intermediate is an ordinary non-CA end-entity cert (no CSR-requested `BasicConstraints` at all — the shape a correctly-issued `SERVER_CERT`/`CLIENT_CERT` profile cert would have) reused to sign a further leaf | `getBasicConstraints() == -1` (not a CA) | **REJECTED**: `basic constraints check failed: this is not a CA certificate` (`reason=NOT_CA_CERT, index=1`) |
| **§99.6c misissuance shape** — intermediate carries `BasicConstraints{CA:TRUE}` (simulating a CSR-requested `BasicConstraints` copied through on a non-CA-purpose profile, exactly [Block 99] §99.6's own finding) reused to sign a further leaf | `getBasicConstraints() == Integer.MAX_VALUE` (CA, unlimited path length) | **ACCEPTED**: full chain validates as trusted, no exception |

**This settles the gap's own conditionality precisely.** JDK PKIX chain validation IS the real,
corpus-wide consumer-side mechanism (Step 2/3) — refuting the "leaf-pinning/hostname-only" alternative
[Block 99]'s own gap text raised. But that validation enforces PRESENCE of the `BasicConstraints` CA flag
on an intermediate, not whether the issuing policy should have granted it — so it does **not** protect
against §99.6c's defect; it is precisely the mechanism the defect would be laundered through. An attacker
who (a) completed [Block 94] §94.2's onboarding+approval precondition, (b) was approved for a non-CA
profile, and (c) embedded `BasicConstraints{CA:TRUE}` in their CSR per §99.6c, would hold a certificate
that a REAL downstream JDK PKIX consumer (any of the 13 `CoreClientTrustManager` call sites, or the
`CertificateChainValidator`/module-signing path) would accept as a valid intermediate CA for signing
further certificates — PROVIDED the victim consumer's trust store contains the issuing `signingService`
CA as a trust anchor, which for the "user trust store" case is satisfied by design for exactly the
deployment scenario this feature exists for (an admin imports the fleet's internal CA into peer stations'
user trust stores specifically so they will trust certs it issues).

**Closing B99-G1: severity is CONFIRMED, not merely conditional.** [Block 99] §99.6's own "MEDIUM-HIGH,
conditional" rating is upgraded to **MEDIUM-HIGH, CONFIRMED against the standard consumer** — this session
did not merely identify WHICH code performs chain validation (the gap's literal ask) but empirically
proved, against the real JDK shipped with N5, that this validation fails to neutralize the defect.
**Fix recommendation** (defensive, no exploit steps): the issuance-policy gap [Block 99] §99.6 already
named — `BSimpleSigningProfile.getSigningParameters`/`isBasicConstraintsExtensionValid` should reject
(not merely pass through) a CSR-requested `BasicConstraints{CA:true}` extension on any profile whose
`KeyPurpose` is not `CA_CERT` — remains the correct and sufficient fix; no change to the downstream PKIX
consumers is needed or appropriate, since rejecting an inappropriate CA flag at the SOURCE is the correct
layer (downstream PKIX validators are working exactly as RFC 5280 specifies).

## 107.2 — B99-G3 CLOSED: `BPlatCryptoManager.generateSelfSignedCert`/`resetUserKeyStore` are reachable from THREE first-party Workbench dialogs (`BSelfSignedDialog`, used by `provisioningNiagara`'s `BSignCertDialog`, `program`'s `BCertificateNotSelectedDialog`, and `platCrypto`'s own `CertificateWizardModel`), but every one of them is constructed from an ALREADY-ESTABLISHED local-or-remote `CoreCryptoManager`/daemon-session object — no lower-privilege or session-bypassing path exists `[CERT]`

[Block 99] §99.x's own text: *"Trace whether `BPlatCryptoManager.generateSelfSignedCert(NX509CertificateBuilder,
...)`/`resetUserKeyStore()` (§99.6b's un-gated methods) are reachable from ANY first-party Workbench
dialog (`BSelfSignedDialog`, `platCrypto/ui/`) without an already-established admin daemon session, which
would raise §99.6(b)'s severity rating beyond 'requires a pre-existing admin session in the same JVM.'"*

**`BSelfSignedDialog.doOkButtonPressed` is confirmed the real call path** to
`BPlatCryptoManager.generateSelfSignedCert` `[CERT]` (`organized/platCrypto/vineflower/com/tridium/
platcrypto/ui/BSelfSignedDialog.java:399,693`: `mgr.generateSelfSignedCert(builder, generator,
existingPasswordChars, pkPasswordChars)`). A corpus-wide search for every construction site of this
dialog finds exactly **4 call sites, all requiring a pre-obtained `ICoreKeyStore`/session object**
`[CERT]` (`grep -rn "new BSelfSignedDialog(" organized`, this session):

1. `provisioningNiagara/.../BSignCertDialog.java:268` — `new BSelfSignedDialog(this,
   this.coreCryptoManager.getKeyStore())` — a `CoreCryptoManager` field already held by the dialog.
2. `program/.../BCertificateNotSelectedDialog.java:147` — same shape, `ccm.getKeyStore()`.
3/4. `platCrypto/.../CertificateWizardModel.java:561,577` — `this.localCoreCryptoManager.getKeyStore()`
   and `this.remoteCoreCryptoManager.getKeyStore()`; the "remote" one is confirmed constructed as
   `new BPlatCryptoManager(this.session)` `[CERT]` (`CertificateWizardModel.java:80`) — i.e. even the
   REMOTE-target wizard path is bound to `this.session`, an already-authenticated daemon session field of
   the wizard, not an independently-obtained or lower-privilege handle.

`getRemoteVersion()`'s own dispatch on `this.store` (`BSelfSignedDialog.java:324-330`) confirms the two
possible backing stores are `ChannelKeyStore` (bound to an existing `BFoxSession`) or `BPlatKeyStore`
(bound to `.getDaemonSession()`) — both requiring an already-open, already-authenticated connection
object as a structural precondition to even construct the dialog; there is no Workbench menu path,
standalone view, or unauthenticated tool that opens `BSelfSignedDialog` directly against a bare ORD or
unauthenticated target.

**Closing B99-G3**: reachable from 3 distinct first-party Workbench UI flows (direct cert-signing request,
program-signing-failure recovery dialog, and the general certificate wizard's local AND remote steps) —
broader reach than [Block 99] itself traced (which found none) — but in every one of the 4 call sites the
dialog is handed an `ICoreKeyStore` sourced from a `CoreCryptoManager`/`BPlatCryptoManager` object that
itself required a prior successful platform-or-fox session/login to exist. This confirms, rather than
raises, §99.6(b)'s own severity framing: "requires a pre-existing admin session in the same JVM" stands
as the accurate bound, now demonstrated across every first-party UI path rather than assumed absent one.

## 107.3 — B99-G4 ADVANCED, not fully closed: a NEW null-Context sub-shape — a literal `.getPermissions(null)` argument at the call site (distinct from [Block 99] §99.2's own declared-variable census) — is found at 12 call sites across 7 files; one of them (`BFoxHistorySpace`'s fox-protocol nav-folder gate) drops an ALREADY-IN-SCOPE non-null `cx` in favor of `null`, opened as a new, more concretely scoped child gap; the caller/callee-split shape itself remains untraced `[CERT]`

> **Correction (added by [Block 112], §14 cross-block).** The "no-op / drops `cx`" reading of the three
> `BFoxHistorySpace` `getPermissions(null)` sites is WRONG: they dispatch to `BRootHistoryFolder.getPermissions(Context)`
> (`organized/history/vineflower/com/tridium/history/BRootHistoryFolder.java:42-49`), which ignores `cx` and fetches the
> real session permissions via `BHistoryChannel.getPermissionsByOrd()`; record reads re-check the session. See [Block 112] §112.1.

[Block 99] §99.x's own text: *"Trace the caller/callee-split and non-standard-wrapper-name sub-shapes of
the null-Context census that §99.2 did not attempt (requires call-graph tracing or a semantic definition
of 'acts as a permission-check wrapper,' neither mechanical)."* [Block 91]'s own **B91-G1** (the same-shape
parent gap) explicitly named three untried shapes: *"a `Context cx = null;` variable passed by name, a
resolve/check pair split across a caller/callee method boundary, or a check performed through a
non-standard wrapper method name."* [Block 99] §99.2's own 41-hit census (Self-verify claim 5) covered
only the LITERAL DECLARATION shape `Context X = null;` — a call site that passes the **literal token
`null` directly as an argument** (never assigned to a named variable at all) is a textually distinct shape
neither census attempted.

**A corpus-wide `getPermissions(null)` call-site sweep finds 12 hits across 7 non-duplicate source files**
`[CERT]` (`grep -rn "getPermissions(null" organized --include=*.java`, this session; `docSource/` mirror
duplicates of the same lines excluded from this count): `kitPx/BLocalizableButton.java:214`,
`workbench/nav/menu/NavMenuUtil.java:138,248`, `workbench/propsheet/BPropertyEntry.java:499`,
`workbench/nav/BComponentMenuAgent.java:136`, `history/BHistorySpace.java:116,124`,
`history/BHistory.java:696`, `history/fox/BFoxHistorySpace.java:177,228,248`, `baja/file/
BAbstractFile.java:305`. Since [Block 99] §99.2's own citation (Self-verify claim 4) already established
`BComponent.getPermissions(cx)` returns `BPermissions.all` unconditionally when `cx==null`, every one of
these 12 sites unconditionally evaluates as fully-permitted, by construction — the same fail-open
semantics as the declared-variable shape, just reached through a different textual pattern.

**Ten of the 12 are architecturally forced or display-only, not a bypass of an available check.**
`BComponentMenuAgent.java:136`/`NavMenuUtil.java`/`BPropertyEntry.java`/`BLocalizableButton.java` are
Workbench-side (client-only) menu-enablement/label-rendering helpers — cosmetic UI hints, not a server-side
enforcement point (the actual mutating action, when invoked, re-checks permissions with a real `Context`
on the station side; [Block 91]'s own prior finding that nav/discovery-shaped gates commonly fail open
while the real read/write gate sits downstream applies here too). `BAbstractFile.java:305`'s
`out.prop("permissions", this.getPermissions(null))` is a serialization helper with no `Context` parameter
in scope at all to propagate — architecturally forced, not a developer choice. `BHistory.java:696`'s
`getFlags(Slot)` likewise has no `Context` parameter in its signature; its `getPermissions(null)` result
only sets a display-oriented `READONLY` slot-flag bit consumed by UI/serialization, not a live `.set()`
write-authorization gate (which is separately enforced via `checkAdminWriteOnHistory(cx)` on the real
`setFlags(Slot, int, Context)` mutator two lines below, per the same file). `BHistorySpace.java:116,124`
gate default ROOT-folder bootstrap visibility during station startup, before any requester `Context`
exists to check — also architecturally forced.

**One site is a genuinely new, more interesting finding: an available, non-null `cx` is explicitly NOT
passed.** `BFoxHistorySpace.java:177,228,248` (a fox-protocol history-space nav-listing handler) calls
`rootFolder.getPermissions(null).hasOperatorRead()` / `folder.getPermissions(null).hasOperatorRead()` to
decide whether a `BRootHistoryFolder`/`BHistoryFolder` gets added to the in-memory nav cache and a
`NavEvent.makeAdded` fired — **while a real, non-null `cx` is already in local scope in the SAME method**
(used two lines later at `BNavRoot.INSTANCE.fireNavEvent(..., cx)`, `:178,188` etc.) `[CERT]`
(`organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java:160-248`, whole method
region read this session). Since `getPermissions(null)` always evaluates `hasOperatorRead()==true`
regardless of the actual remote fox requester's real permissions, this visibility gate is a no-op —
EVERY history root-folder/device-folder gets added to the folder cache and nav-advertised over fox,
irrespective of whether the connecting user has any real operator-read grant on that folder. Whether
this actually exposes unauthorized history CONTENT (versus only unauthorized folder-existence/nav-tree
visibility, with the real per-history read enforced by a separate, later check when leaf history data is
actually served) was not traced this session — opened as **B107-G1** below.

**Advancing, not closing B99-G4**: this session's method (a literal-argument `getPermissions(null)` grep,
plus full reads of every hit) is mechanical and exhaustive for that ONE additional shape, and surfaces one
concretely new finding beyond [Block 99] §99.2's own declared-variable census — but [Block 91]'s own
SECOND named shape (a resolve/check pair split across a caller/callee method boundary, e.g. a `Context`
obtained non-locally then silently dropped before a downstream check in a DIFFERENT method) and its THIRD
(a non-standard wrapper method name wrapping an internal null-Context check) remain genuinely untraced,
exactly as [Block 99]/[Block 91] both already flagged as non-mechanical residuals.

## 107.4 — B99-G5 CLOSED: `BLonworksRpc.startJob()`'s read-gates-a-write pattern does NOT recur anywhere else among the corpus's 34 `*Rpc.java` classes — every other read-only-gated method census this session found is genuinely read-shaped, and every write-shaped method census this session found is gated by `canWrite()` (or `canRead()&&canWrite()`) `[CERT]`

[Block 99] §99.x's own text: *"Confirm whether `BLonworksRpc.startJob()`'s read-gates-a-write shape (§99.1
Step 5) recurs elsewhere in the corpus beyond this one LON-specific instance — not searched this session
beyond the single file found."*

**Full census of all 34 `*Rpc.java` classes corpus-wide** `[CERT]` (`find organized -iname "*Rpc.java"
-path "*vineflower*"`, this session, 34 files) for any method gated by `.canRead()` alone: **7 files**
(including `BLonworksRpc` itself) contain a bare `.canRead()` gate: `BLonworksRpc` (§99.1's own finding),
`BHistoryRpc`, `BWorkbenchRpc`, `BDriverHistoryRpc`, `BNiagaraHistoryExportRpc`, `BFileRpc`,
`BResolveServerSideRpc`. Each of the other 6 was read in full to classify the gated method's own shape:

- `BHistoryRpc.setHistoryDisplayNameFormat` (write) uses `canWrite()`; its sibling
  `getHistoryDisplayNameFormat` (read) uses `canRead()` — a correctly symmetric pair `[CERT]`
  (`organized/history/vineflower/com/tridium/history/ux/BHistoryRpc.java:30-51`).
- `BWorkbenchRpc.getBestViewId`/`getWorkbenchViewList` — both genuinely read-shaped (view-metadata/list
  queries, no mutation) — `canRead()` is the correct gate `[CERT]`
  (`organized/workbench/vineflower/com/tridium/workbench/util/BWorkbenchRpc.java:33-62`).
- `BDriverHistoryRpc.getDriverHistoryInfo` / `BNiagaraHistoryExportRpc.getExportHistoryDiscoveryRpc` —
  both genuinely read-shaped (JSON info/discovery queries) — `canRead()` is correct `[CERT]`
  (`organized/driver/vineflower/com/tridium/driver/ui/history/BDriverHistoryRpc.java:32-38`;
  `organized/niagaraDriver/vineflower/com/tridium/nd/discover/BNiagaraHistoryExportRpc.java:33-40`).
- `BFileRpc`'s actual file-MUTATING methods (copy/move/rename/create-directory) all gate on
  `target.canRead() && target.canWrite()` (BOTH), never `canRead()` alone `[CERT]`
  (`organized/web/vineflower/com/tridium/web/rpc/BFileRpc.java:137,154,171,197`) — the architecturally
  CORRECT counter-pattern to §99.1 Step 5's bug.
- `BResolveServerSideRpc.isParentLegal` — a pure legality QUERY (does not mutate anything; answers "could
  this value legally become a child of this parent"), correctly `canRead()`-gated `[CERT]`
  (`organized/webEditors/vineflower/com/tridium/webeditors/ux/servlets/BResolveServerSideRpc.java:
  53-68`).

**Closing B99-G5**: across all 34 `*Rpc.java` classes corpus-wide, `BLonworksRpc.startJob()` remains the
ONLY instance where a write/action-shaped (here, hardware-facing device-download-job) method is gated by
a read-only permission check; every other candidate this census found is either a genuinely read-shaped
method correctly gated by `canRead()`, or a genuinely write-shaped method correctly gated by `canWrite()`
(or the stronger `canRead()&&canWrite()` conjunction `BFileRpc` uses). The bug class is a singular,
LON-specific issuance, not a systemic `*Rpc`-family pattern.

## 107.x — Corrections to earlier blocks

None found this session — no contradiction of an earlier block's stated verdict; §107.1's severity
upgrade ("conditional" → "confirmed against the standard consumer") is an explicit RESOLUTION of [Block
99] §99.6's own named conditionality, not a correction of anything it asserted.

## 107.x — Connections

- **[Block 99]** — §107.1 CLOSES **B99-G1**, upgrading §99.6's own "MEDIUM-HIGH, conditional" rating to
  confirmed, via a live JDK PKIX reproduction; §107.2 CLOSES **B99-G3**, confirming (not merely failing to
  raise) §99.6(b)'s "pre-existing admin session" severity bound across all 4 real UI call sites; §107.3
  ADVANCES **B99-G4** with one new call-site shape and one new concrete finding, opening **B107-G1** for
  its unresolved blast-radius question; §107.4 CLOSES **B99-G5**, confirming §99.1 Step 5's finding is a
  singular instance, not a systemic `*Rpc` pattern.
- **[Block 91]** — §107.3 extends **B91-G1**'s own three-shapes framing (declared-variable / caller-callee
  split / non-standard wrapper) by one additional mechanical shape (literal call-site argument); the other
  two remain exactly as open as [Block 91] left them.
- **[Block 95]/[Block 53]** — §107.1's finding that BOTH major certificate-consumer families (TLS peer
  trust via `CoreClientTrustManager`, and module-signature/TPK trust via `CertificateChainValidator`) use
  genuine `CertPathValidator.getInstance("PKIX")`-family validation reuses and corroborates [Block 95]
  §95.x's/[Block 53]'s own prior `CertificateChainValidator`/`PKIXParameters` citations as a second,
  independent instance of the same corpus-wide pattern, rather than re-deriving them.
- **[Block 55]/[Block 106]** — §107.1's live PKIX experiment and §107.1 Step 3's `TrustManagerFactory`
  algorithm-resolution probe both reuse the exact same real bundled Windows `jre/bin/*.exe` (Zulu
  `25.0.4`) [Block 55]/[Block 106] already established as this corpus's live-JDK-behavior reference point.

## 107.x — Child gaps opened

- **B107-G1** (medium priority, refines **B99-G4**) — Trace whether `BFoxHistorySpace`'s
  `getPermissions(null)`-gated nav-folder-visibility check (§107.3) has any real consequence beyond
  folder-EXISTENCE/nav-tree visibility over the fox protocol — specifically, whether the actual per-history
  READ (the leaf `BHistory`/`BHistoryMirror` object's own content, once a folder is visible) is
  independently re-checked with a real, non-null `Context` at the point of serving history data, which
  would make this an unauthorized-DISCOVERY-only issue (low severity), versus a case where folder
  visibility is the ONLY gate and no downstream re-check exists (higher severity, unauthorized-content
  exposure). `investigable` — needs tracing `BFoxHistorySpace`'s history-data-serving path (distinct from
  the nav-listing path this session read) and/or the `BHistoryFolder`/`BHistoryMirror` classes' own
  read-time permission enforcement.
- **B107-G2** (low priority, refines the untraced half of **B99-G4**/**B91-G1**) — A semantic
  caller/callee-split trace (a `Context` resolved or obtained in one method, then passed — possibly as a
  narrowed/derived/`null`-defaulted value — into a DIFFERENT method's permission check) and a
  non-standard-wrapper-method-name census, neither of which this session's mechanical literal-argument
  grep could reach. `investigable`, low priority, same "requires call-graph tracing or a semantic
  definition, neither mechanical" framing [Block 99]/[Block 91] both already gave this residual.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `BCombinedSignedCertConfig.certificateSigned` applies the signed cert to `BFoxService`/`BWebService`/platform SSL settings | [CERT] | `organized/signingService/vineflower/com/tridium/signing/BCombinedSignedCertConfig.java:433-435,539-602` |
| 2 | `CoreClientTrustManager` is referenced from 13 files across 10 modules incl. `fox`, `httpClient`, `cloudLink`, `opcUaClient`/`opcUaServer`, `platCrypto` | [CERT] | `grep -rl CoreClientTrustManager organized --include=*.java`, this session, 13 hits listed in §107.1 |
| 3 | `CoreClientTrustManager.initializeTrustManagers()` builds real `TrustManagerFactory.getInstance("X509")` delegates from the user + system (JDK `cacerts`) trust stores | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/io/CoreClientTrustManager.java:62-92`; `CoreCryptoManager.java:807-818` |
| 4 | On the real bundled JRE (Zulu `25.0.4`), `TrustManagerFactory.getInstance("X509")` resolves to `validatorType=PKIX`, identical to `"PKIX"` and distinct from `"SunX509"`'s `Simple` | [CERT-hw] | `/tmp/.../scratchpad/b107/tmfcheck/TmfCheck3.java` + live output, this session |
| 5 | Live `CertPathValidator.getInstance("PKIX")` REJECTS a chain whose intermediate lacks `BasicConstraints` CA:true (`NOT_CA_CERT`), and ACCEPTS the identical chain shape when the intermediate carries `BasicConstraints{CA:true}` (the B99 misissuance shape) | [CERT-hw] | `/tmp/.../scratchpad/b107/pkixtest/PkixTest.java` + live output, this session |
| 6 | All 4 `new BSelfSignedDialog(...)` call sites pass an `ICoreKeyStore` sourced from an already-constructed `CoreCryptoManager`/`BPlatCryptoManager`/session object | [CERT] | `organized/provisioningNiagara/.../BSignCertDialog.java:268`; `organized/program/.../BCertificateNotSelectedDialog.java:147`; `organized/platCrypto/.../CertificateWizardModel.java:80,561,577` |
| 7 | 12 corpus-wide `.getPermissions(null)` literal call-site hits across 7 non-duplicate files, distinct from [Block 99] §99.2's declared-variable-shape census | [CERT] | `grep -rn "getPermissions(null" organized --include=*.java`, this session, file:line list in §107.3 |
| 8 | `BFoxHistorySpace.java:177` calls `getPermissions(null)` while a non-null `cx` is in scope in the same method (used at `:178` for `fireNavEvent`) | [CERT] | `organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java:160-248` |
| 9 | Across all 34 `*Rpc.java` classes, only `BLonworksRpc.startJob()` gates a write-shaped method with `canRead()` alone; every other bare-`canRead()`-gated method censused this session is genuinely read-shaped, and `BFileRpc`'s write methods gate on `canRead()&&canWrite()` | [CERT] | `organized/history/vineflower/.../BHistoryRpc.java:30-51`; `organized/workbench/vineflower/.../BWorkbenchRpc.java:33-62`; `organized/driver/vineflower/.../BDriverHistoryRpc.java:32-38`; `organized/niagaraDriver/vineflower/.../BNiagaraHistoryExportRpc.java:33-40`; `organized/web/vineflower/.../BFileRpc.java:137,154,171,197`; `organized/webEditors/vineflower/.../BResolveServerSideRpc.java:53-68` |

**Tally**: 9 `[CERT]`-family claims (7 `[CERT]`, 2 `[CERT-hw]`) · 0 `[INFER]` used as a load-bearing claim
marker (the severity-upgrade language in §107.1 and the display-only/architecturally-forced
characterizations in §107.3 are hedged prose built directly on the `[CERT]`/`[CERT-hw]` claims above them,
not independently marker-tagged deductions). [INFER]/[CERT*] ratio: 0.

**Artifacts**: `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/
scratchpad/b107/` — `tmfcheck/TmfCheck.java`,`TmfCheck2.java`,`TmfCheck3.java` (+ compiled `.class` +
captured stdout) — `TrustManagerFactory` algorithm-resolution probes against the real bundled JRE;
`pkixtest/` — `root.jks`/`root.pem` (self-signed CA:true root), `inter_noca.{jks,csr,pem}` (baseline,
no `BasicConstraints`), `inter_yesca.{jks,csr,pem}` (misissuance shape, `BasicConstraints{CA:true}`),
`leaf_noca.pem`/`leaf_yesca.pem` (each intermediate's own further-signed leaf), `PkixTest.java` (+
compiled `.class`) — the live `CertPathValidator` harness and its captured output.
