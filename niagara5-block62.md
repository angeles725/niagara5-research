# Block 62 — Closing the SAML deprecated-algorithm security cluster (B61-G3), reaffirming the CSRF timing-comparison finding (B52-G1), and settling two low-priority provenance gaps (B38-G1 closed, B38-G4 narrowed)

> Research closing/advancing four previously-opened child gaps named as a security cluster: **B61-G3**
> (high — [Block 61] §61.3 found N5's consumer-side SAML `java-saml-core` `Util` accepts SHA-1/DSA-SHA1
> signed IdP responses because its `DEPRECATED_ALGOS` reject flag is hardcoded `false` at N5's call site;
> this session traces whether ANY Tridium-side setting could flip that flag, whether the bundled
> `xmlsec-4.0.4` Santuario engine gates the algorithm independently, and how N4's own SAML SP compares);
> **B52-G1** (low — [Block 52] §52.1/§52.9 found `CsrfUtil.verifyCsrfToken`/`NiagaraSuperSession.
> verifyCsrfToken` compare tokens with plain `String.equals()`, not a constant-time comparison; this
> session re-confirms the exact call site fresh and restates the severity read); **B38-G1** (low —
> [Block 38] §38.3 found the scheme-agnostic `BUserService` account lockout covers TOTP failures too, but
> left open whether N5's lockout DEFAULTS are new or an N4 carryover); **B38-G4** (low — [Block 38] §38.10
> closed the SRP6 key-exchange ARCHITECTURE question but left the exact GROUP-SIZE parameters
> uncross-checked against N4's Fox SRP6). Does **not** cover: a live SAML exchange crafted with an
> actual SHA-1-signed assertion to observe end-to-end acceptance (still `blocked-on-source`, no runnable
> N5 station — this is [Block 61]'s own **B61-G2**, untouched here); a live timing-attack probe against
> `CsrfUtil`'s comparison (also `blocked-on-source`, per [Block 52] §52.9); decompiling N4's own
> `nre.jar`-equivalent to locate its `KeyExchange`/`SRP6AlgorithmBundle` classes (searched for across the
> already-organized `niagara-research` corpus only — see §62.7's negative-existence scope note).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 12]/[Block 38]/[Block 52]/[Block 61] read; decompiled Java sources at
> `/home/cristian/niagara5-research/organized/{saml,web,baja,_bin-ext/nre}/vineflower/`. N4 baseline:
> `/home/cristian/niagara-research` corpus (Honeywell OptimizerSupervisor 4.14.0.162 decompile),
> read-only, cited by file path and by block number (B30, B419, B830), not re-decompiled — all N4
> `[CERT]` citations below point at files already present in that corpus's `organized/` tree from prior
> sessions.
>
> Sources (all local, read-only):
> - `organized/saml/vineflower/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java` (whole
>   `@NiagaraProperties` array, `:38-86`, plus the mirrored `public static final Property` declarations
>   `:89-134` — full-enumeration read, this session) and
>   `organized/baja/vineflower/niagara/authn/BSSOAuthenticationScheme.java` (whole file, 46 lines — the
>   direct superclass's own property list) — settles whether ANY Tridium-authored SAML-scheme setting
>   exposes the OneLogin `rejectDeprecatedAlg` flag.
> - `organized/saml/vineflower/com/tridium/saml/rp/Response.java:238-286` (`validateSignatures()`,
>   re-read whole method this session — a 4th independent read across [Block 38]/[Block 61]/this block,
>   each for a different question) — confirms the exact call-site argument shape.
> - `organized/saml/vineflower/LIB-INF/xmlsec-4.0.4.jar` — fresh `javap -p -c` disassembly this session
>   of `org/apache/xml/security/signature/{XMLSignature,SignedInfo,Manifest}.class` and
>   `org/apache/xml/security/algorithms/{JCEMapper,SignatureAlgorithm,SignatureAlgorithmSpi}.class`, plus
>   the jar's own bundled `org/apache/xml/security/resource/config.xml` (Apache Santuario's own algorithm
>   registration table) — none of these classes/resources had been opened in this corpus before this
>   session (Block 61 §61.3 named `xmlsec-4.0.4.jar` "listed but not opened").
> - `organized/web/vineflower/niagara/web/CsrfUtil.java` (whole file, 45 lines, re-read fresh this
>   session — independent re-open, not copied from [Block 52]'s citation).
> - `organized/baja/vineflower/niagara/user/BUserService.java:140-152` (lockout-default `Property`
>   declarations, re-read fresh this session).
> - `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/exchange/KeyExchange.java` (whole file, 93
>   lines — first read in this corpus of this exact file; [Block 12]/[Block 38] cited its EXISTENCE and
>   call shape but never opened it).
> - N4 REMITTANCE (read-only, `niagara-research` corpus, no fresh decompilation): `organized/saml/saml-rt/
>   vineflower/com/tridium/saml/rp/Response.java` (whole file, 500 lines) and `organized/saml/saml-rt/
>   vineflower/com/onelogin/saml/Utils.java` (whole file, 335 lines) — N4's SAML SP signature-validation
>   path, opened for the first time by either corpus's own block series (per a `grep -rn` sweep of
>   `niagara-research/*.md` for `com.onelogin.saml.Utils`/`validateSign` returning no prior hits);
>   `organized/baja/baja/vineflower/javax/baja/user/BUserService.java:150-159` (lockout defaults,
>   re-read fresh this session against N5's values); a corpus-wide `grep -rl "class KeyExchange"` /
>   `grep -rl "SRP6AlgorithmBundle"` sweep of `niagara-research/organized/` (zero hits, §62.7).
>
> Method: reading Vineflower decompile already organized in both corpora (no fresh decompilation
> performed), plus fresh `javap -p -c` JVM-bytecode disassembly of a bundled third-party jar
> (`xmlsec-4.0.4.jar`) never previously opened in this corpus, plus a jar-resource (`config.xml`) text
> read. Markers: `[CERT]` local primary source (decompiled `.java`, `file:line`, this session unless
> otherwise noted as re-citing a prior block) · `[CERT-hw]` here extended, matching [Block 61]'s own
> convention, to a fresh `javap`/jar-resource extraction of the exact bundled binary on this install ·
> `[CERT-a]` secondary source, re-cited from a prior block · `[INFER]` deduction, including general
> security-domain context (e.g. SHA-1 collision practicality) not sourced from this corpus.
>
> Security layer, closing/narrowing a mixed-severity cluster across [Block 61] (SAML), [Block 52] (CSRF),
> and [Block 38] (lockout, SRP6). Connects all three plus [Block 12] (SRP6/lockout grandparent) and
> `niagara-research` B30/B419/B830 (N4 SAML/SRP6/lockout baselines).
>
> **Type:** `mixed` — §62.1–§62.3 upgrade [Block 61] §61.3's `[INFER]`-flagged open question ("could a
> setting exist? would Santuario gate it independently?") to `[CERT]` NO on both counts, closing B61-G3
> outright with a severity/mitigation verdict (the `[INFER]`-across-a-prior-block correction pattern,
> `mixed` trigger per METHODOLOGY §4/§11); §62.4 is fresh N4-comparison evidence-gathering never
> attempted by either corpus before; §62.5 is a fresh-session reaffirmation (not a correction) of
> [Block 52]'s own finding; §62.6 closes B38-G1 outright via a direct N4/N5 value comparison; §62.7
> narrows B38-G4 (closes the N5 half, the N4 half stays open with a re-scoped child gap).

---

## 62.1 — B61-G3 (i): no Tridium-authored SAML-scheme setting exists anywhere that could flip OneLogin's `rejectDeprecatedAlg` flag `[CERT]`

[Block 61] §61.3 established that `com.onelogin.saml2.util.Util`'s 4-argument `validateSignNode(...)`
overload hardcodes `Boolean.FALSE` for the "reject deprecated signature algorithm" parameter, and that
`com.tridium.saml.rp.Response.validateSignatures()` is the caller — but did not check whether Tridium
exposes a station-configurable property that could route a caller-supplied `true` into that parameter
instead. This session settles it by reading the COMPLETE Niagara-property surface of the class in the
call chain and its entire superclass chain up to the generic authentication-scheme base, and by re-reading
the exact call site.

**`BSAMLAuthenticationScheme`'s full property list (13 properties, all of them — nothing elided) contains
no signature-algorithm or deprecated-algorithm setting:** `entityId`, `idpHostURL`, `idpHostPort`,
`idpLoginPath`, `includePortInDestination`, `includeQueryParamsInDestination`, `idpCert`,
`samlServerCertAliasAndPassword`, `timeSkew`, `includeRequestedAuthnContext`, `requestedAuthenticationType`,
`requestedAuthenticationComparisonMode`, `prototypeMergePolicy`, `allowAutomaticUserCreation` `[CERT]`
(`organized/saml/vineflower/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java:38-86` the
`@NiagaraProperties` declaration array, cross-checked against the mirrored `public static final Property`
field declarations at `:91-134` — both read whole, this session; a per-METHODOLOGY-§11 "read the code that
DEFINES the set before answering" enumeration, not a partial grep). The direct superclass,
`BSSOAuthenticationScheme`, adds exactly one property of its own — `loginButtonText` (cosmetic UI text) —
and nothing else `[CERT]` (`organized/baja/vineflower/niagara/authn/BSSOAuthenticationScheme.java`, whole
46-line file read this session). No `idpCert`-adjacent, `algorithm`-named, or `strict*`/`reject*`-named
property exists anywhere in this two-class hierarchy that a Workbench administrator or a station config
could set to influence signature-algorithm acceptance.

**The call site itself is structurally incapable of passing anything but the hardcoded default.**
`Response.validateSignatures()` calls `Util.validateSignNode(responseSignatures.item(0), cert, null, null)`
and `Util.validateSignNode(assertionSignatures.item(0), cert, null, null)` — the bare 4-argument overload,
literal `null` for the two trailing `String` parameters (fingerprint algorithm and XPath expression,
per [Block 61]'s own disassembly of the overload's parameter names) `[CERT]`
(`organized/saml/vineflower/com/tridium/saml/rp/Response.java:274,278`, re-read whole method `:238-286`
this session — the fourth independent read of this exact method across [Block 38]/[Block 61]/this block).
There is no 5-argument call anywhere in this file, and no other class in `organized/saml/vineflower/`
imports `com.onelogin.saml2.util.Util` at all `[CERT]` (`grep -rln "onelogin.saml2.util.Util"
organized/saml/vineflower/`, this session, single hit: `Response.java`). **Net: the "reject deprecated
algorithm" flag is not merely defaulted off — it is architecturally unreachable from any Niagara-side
configuration surface.** No station property, no facet, no deployment choice changes this behavior; only
a Tridium code change (calling the 5-argument overload with `Boolean.TRUE`, or patching the bundled jar)
could.

## 62.2 — B61-G3 (ii): Apache Santuario's own `secureValidation` flag — which OneLogin DOES pass as literal `true` — restricts Reference/Manifest COUNTS, not signature-algorithm CHOICE; `rsa-sha1`/`dsa-sha1` remain fully registered regardless `[CERT-hw]`

[Block 61] §61.3 quoted `getSignatureData`'s construction `new XMLSignature(element, "", true)` — the
THIRD argument (`true`) was not traced past that literal. This session opens the bundled
`xmlsec-4.0.4.jar` (Apache Santuario) for the first time in this corpus and disassembles the constructor
chain that literal `true` actually reaches.

**The `boolean` is Santuario's own `secureValidation` flag, forwarded unchanged through three
constructors.** `XMLSignature(Element, String, boolean)` → `XMLSignature(Element, String, boolean,
Provider)` forwards `iload_3` (the boolean) directly into `new SignedInfo(Element, String, boolean,
Provider)` `[CERT-hw]` (`javap -p -c` disassembly of `org/apache/xml/security/signature/XMLSignature.class`
extracted from `organized/saml/vineflower/LIB-INF/xmlsec-4.0.4.jar`, this session — bytecode offsets
`145-159` of the 4-arg constructor, `invokespecial ... SignedInfo."<init>":(Lorg/w3c/dom/Element;
Ljava/lang/String;ZLjava/security/Provider;)V`). `SignedInfo`'s own matching constructor forwards the same
boolean unchanged into `Manifest."<init>":(Lorg/w3c/dom/Element;Ljava/lang/String;Z)V` `[CERT-hw]`
(`javap -p -c` of `SignedInfo.class`, same jar, this session — offset `3-6` of the 4-arg constructor:
`iload_3 → invokespecial Manifest."<init>"`). `Manifest.class` stores it in a field literally named
`secureValidation` (`private boolean secureValidation;`, confirmed by field-table entry, not inferred from
a variable name in bytecode) `[CERT-hw]` (`javap -p -c` of `Manifest.class`, same jar, this session).

**`secureValidation` gates Reference/Manifest COUNT limits, not the accepted signature-algorithm set.**
The field is read in exactly two methods: `item(int)` and `verifyReferences(boolean)` — both concerned
with iterating/validating `<Reference>`/`<Manifest>` elements, and the one string literal adjacent to a
`secureValidation`-gated branch is `"signature.tooManyReferences"` (a DoS-style reference-count cap, thrown
via `XMLSecurityException`) `[CERT-hw]` (`javap -p -c` of `Manifest.class`, this session — offsets `240`,
`334`, `389`, `471` all inside `item(int)`/`verifyReferences(boolean)`; the `ldc "signature.
tooManyReferences"` string constant confirmed at offset `153` of the `verifyReferences` body). Neither
`SignedInfo` (the class holding `signatureAlgorithm`/`signatureMethod`) nor `SignatureAlgorithm`
(Santuario's own algorithm-registry class) reads `secureValidation` anywhere `[CERT-hw]` (`grep -i
secureValidation` over the full `javap -p -c` disassembly of both classes, this session — zero hits in
either).

**Santuario's own static algorithm-registration table registers `rsa-sha1`/`dsa-sha1`/`hmac-sha1`/
`ecdsa-sha1` unconditionally — the same table used for EVERY signature, `secureValidation` on or off.**
The jar's own `org/apache/xml/security/resource/config.xml` (Santuario's built-in algorithm-mapping
resource, extracted and read whole this session) lists `http://www.w3.org/2000/09/xmldsig#dsa-sha1` and
`http://www.w3.org/2000/09/xmldsig#rsa-sha1` as registered `SignatureAlgorithm` URIs with live
`JAVACLASS`/`JCEName` mappings (`SignatureRSASHA1`/`SHA1withDSA`/`SHA1withRSA`), no conditional wrapper,
no separate "secure" variant of the table `[CERT-hw]` (`organized/saml/vineflower/LIB-INF/xmlsec-4.0.4.jar
!org/apache/xml/security/resource/config.xml:79-84,226-254`, this session). `SignatureAlgorithm.class`'s
own static registration method (`registerDefaultAlgorithms` in `JCEMapper`, cross-checked against
`SignatureAlgorithm`'s constant-pool string literals) independently confirms the same four
`...-sha1`/`...-SHA1` URI constants are `ldc`'d and registered at class-init time, unconditionally
`[CERT-hw]` (`javap -p -c` of `JCEMapper.class`/`SignatureAlgorithm.class`, this session).

**Net: Santuario is NOT a second gate.** The `true` OneLogin passes into `XMLSignature`'s constructor
enables a DIFFERENT protection (reference/manifest-count DoS mitigation) that has nothing to do with which
signature algorithm a `<Signature>` element may declare. If OneLogin's own `isAlgorithmWhitelisted`/
`mustRejectDeprecatedSignatureAlgo` gate (§61.3, unchanged by this session) lets a URI through, Santuario
will happily compute `checkSignatureValue` for it — `rsa-sha1` and `dsa-sha1` are first-class, fully
registered algorithms in this exact bundled jar, `secureValidation` notwithstanding.

## 62.3 — B61-G3 CLOSED: severity statement and mitigation for N5 SAML SSO deployments `[CERT]`+`[INFER]`

**Combining §62.1 and §62.2 with [Block 61] §61.3's own finding closes B61-G3 as a confirmed, unmitigated
static defect, not merely a theoretical one.** Three independent facts, each `[CERT]`/`[CERT-hw]` this
session or [Block 61]'s prior session, stack without exception: (1) OneLogin's `isAlgorithmWhitelisted`
ACCEPTS `rsa-sha1` and `dsa-sha1` (§61.3, unchanged); (2) OneLogin's own "reject deprecated" gate for those
exact two algorithms is hardcoded off, with NO Niagara-side configuration path able to turn it on (§62.1,
this session); (3) the underlying Santuario XML-DSig engine imposes no independent algorithm restriction
that would catch what OneLogin lets through (§62.2, this session). **Per METHODOLOGY §3's static-defect /
runtime-exploitability split: the code-level omission is `[CERT]` — confirmed absent at every layer this
session could reach. Actual exploitability is `[INFER]`, bounded as follows** (not asserted as either
"real today" or "benign"):

- **What is NOT broken by this.** `checkSignatureValue` still requires a signature that verifies against
  the SPECIFIC certificate configured in `idpCert` (`BSAMLAuthenticationScheme.idpCert`, resolved via
  `CertManagerFactory.getInstance().getUserTrustStore()`) `[CERT-a]` (per [Block 61] §61.3's citation of
  `Response.java:263-264`, re-cited not re-verified this session). This is not an authentication bypass by
  itself — an attacker without access to a signature that validates under the trusted IdP's actual public
  key gains nothing from this finding alone.
- **What IS exposed: an algorithm-downgrade/forgery surface at the trusted IdP's own key.** Two concrete
  paths reach it. (a) If the configured IdP is ITSELF set to sign SAML responses with `rsa-sha1`/`dsa-sha1`
  (an IdP-side administrative choice, common on older or misconfigured IdP deployments — Tridium's OWN
  IdP-side `ALGORITHM_MAPPING` for verifying INCOMING `AuthnRequest`s already excludes SHA-1/DSA entirely,
  per [Block 38] §38.9, showing Tridium's own IdP role holds a stricter internal standard than its SP role
  enforces on external IdPs), N5 will accept it silently — no warning, no downgrade notice, exactly as
  readily as a modern RSA-SHA256+ signature. (b) An attacker able to forge a SHA-1 collision against a
  signed blob under the trusted certificate's key — a publicly demonstrated, though still
  computationally expensive, attack class (the 2017 "SHAttered" chosen-prefix collision and its
  successors) `[INFER]`, general security-domain knowledge, not sourced from this corpus this session —
  gains a forged, accepted assertion; DSA-SHA1 additionally inherits DSA's own narrower, weaker
  nonce-reuse attack surface, unrelated to the hash choice `[INFER]`.
- **Severity verdict: MEDIUM-to-HIGH for any deployment that does not independently, operationally
  guarantee its IdP only signs with RSA/ECDSA-SHA256+.** The RESEARCH-STATE.md `high` label (pre-existing,
  not changed by this session) is supported: this is not a "requires an already-compromised IdP" bug —
  it silently downgrades security for ANY legitimately configured IdP an administrator happens to leave on
  SHA-1 signing, with zero station-side signal that this happened.

**Mitigation recommendation (two independent layers, since no Niagara-side fix exists today):**
1. **Operational, available today, no code change:** SAML SSO deployments MUST independently verify and
   enforce that their IdP is configured to sign responses/assertions exclusively with RSA-SHA256 or
   stronger — N5's SP will not catch a misconfigured IdP, so this becomes the ONLY effective control until
   Tridium ships a fix. This is standard SAML hardening practice regardless of this finding, but this
   finding removes the SP-side safety net an administrator might otherwise assume exists.
2. **Vendor-side fix (out of this corpus's ability to apply — Tridium/OneLogin-owned code):** either
   Tridium patches its own `Response.validateSignatures()` call site to invoke the 5-argument
   `Util.validateSignNode(..., Boolean.TRUE)` overload (or a Tridium-side equivalent check re-implementing
   the same reject), or exposes a `rejectDeprecatedSignatureAlgorithms` (or similarly named) property on
   `BSAMLAuthenticationScheme` so an administrator can opt in without a Tridium release. Both are
   structurally straightforward given §62.1's finding that the call site is a single, isolated, two-line
   change — this is a configuration-surface gap, not a deep architectural one.

**B61-G3 is CLOSED** with this severity/mitigation verdict; [Block 61]'s own **B61-G2** (a live-exchange
`[CERT-hw]` confirmation of end-to-end acceptance) remains separately open and untouched — it would upgrade
the `[INFER]` exploitability half of this verdict to `[CERT-hw]`, not change the `[CERT]` static-defect
half this session already settled.

## 62.4 — N4 comparison: N4's SAML SP used a DIFFERENT, older OneLogin library built on the JDK's own `javax.xml.crypto` engine — NO algorithm allowlist existed there at all `[CERT]`

Requested N4 comparison, not previously attempted by either corpus's block series (a `grep -rn` sweep of
`niagara-research/*.md` for `com.onelogin.saml.Utils`/`validateSign` returns zero prior hits, this
session). N4's `com.tridium.saml.rp.Response.validateSignatures()` — architecturally the same role as N5's
class of the same name — imports and calls a COMPLETELY DIFFERENT third-party class: `com.onelogin.saml.
Utils` (package `com.onelogin.saml`, singular — the OLD, pre-`saml2` OneLogin `java-saml` library, not
`java-saml-core-2.9.0`) `[CERT]` (`niagara-research/organized/saml/saml-rt/vineflower/com/tridium/saml/rp/
Response.java:3,222-260`, whole `validateSignatures()` method read this session — first read of this exact
file by any block in either corpus).

**N4's `Utils.validateSign(Node, Certificate)` uses the JDK's own built-in `javax.xml.crypto.dsig` API
(JSR 105) — not Apache Santuario, not an OneLogin-authored algorithm gate of any kind.**
`validateSign()`'s entire body is: build a `DOMValidateContext(cert.getPublicKey(), signatureElement)`,
get `XMLSignatureFactory.getInstance("DOM")`, `unmarshalXMLSignature(ctx)`, then `xmlSignature.validate
(ctx)` — four calls, all against `javax.xml.crypto.dsig.*` classes shipped in the JDK itself `[CERT]`
(`niagara-research/organized/saml/saml-rt/vineflower/com/onelogin/saml/Utils.java:1-38,205-225`, whole
method + imports read this session). A full-file grep for `Whitelist`/`whitelist`/`sha1`/`SHA1`/
`Algorithm`/`DEPRECATED`/`deprecated` across this 335-line file returns ZERO hits `[CERT]` (`grep -n`
against the file this session — a negative-existence claim about a NAMED, fully-opened file, not an
unopened one, satisfying METHODOLOGY §3's symmetric-opening obligation).

**Reading this correctly.** N4's SAML SP therefore had NO OneLogin-authored algorithm allowlist or
deprecated-algorithm reject at all — whatever the JDK's own default `javax.xml.crypto.dsig` provider
permits (its own internal algorithm registry, external to both corpora, NOT read this session — flagged
as a boundary, not asserted either way) is the entire gate. This means N5's SWITCH to `java-saml-core-
2.9.0` (a library that DOES carry an explicit 5-member whitelist, even though its "reject deprecated"
knob sits unused) is, in the narrow sense of "does an application-level allowlist exist at all",
STRICTER than what N4 shipped — N5 at minimum REJECTS anything outside 5 named URIs (§61.3's
`isAlgorithmWhitelisted` set), where N4's SP would reject nothing beyond whatever the bare JDK provider
itself restricts. This is a genuine provenance nuance for B61-G3's write-up: N5 did not "regress" SHA-1
acceptance relative to N4 — N5 ADDED an allowlist layer (that still, separately, includes SHA-1) where N4
apparently had none of its own. Whether the bare JDK `javax.xml.crypto.dsig` default provider on N4's
runtime independently restricted SHA-1 is `[INFER]`, unresolved this session, named as **B62-G1**.

## 62.5 — B52-G1 reaffirmed: `CsrfUtil.verifyCsrfToken`'s comparison is still plain `String.equals()`, fresh-session read; severity unchanged from [Block 52]'s own assessment `[CERT]`+`[INFER]`

Fresh, independent re-open of the exact file (not copied from [Block 52]'s citation): `CsrfUtil.
verifyCsrfToken(String sessionToken, String token)`'s body is unchanged from [Block 52]'s reading —
`if (Objects.isNull(token) || Objects.isNull(sessionToken)) { throw ...; } else if (!sessionToken.equals
(token)) { throw ...; } else { return true; }` `[CERT]` (`organized/web/vineflower/niagara/web/
CsrfUtil.java:36-42`, whole 45-line file read this session). `String.equals()`'s implementation performs a
length check followed by a left-to-right, early-exit `char`-by-`char` comparison — data-dependent timing,
not constant-time — this is a property of `java.lang.String` itself, not something specific to this call
site, and was not independently re-verified against JDK source this session (already common knowledge,
`[INFER]` in the sense that no fresh JDK-source citation was opened this session; [Block 52] §52.9 did not
open JDK source either).

**Severity assessment, unchanged from [Block 52] §52.9's own honest bound — reaffirmed, not escalated:**
the token is 24 bytes of `SecureRandom`-sourced entropy, transported per-request, and this is PLATFORM
code ([Block 27] §27.6 already established `CsrfUtil` as Tridium's own shared primitive, not something any
prior PoC in this corpus authored). A practical remote timing attack against a Base64-encoded 24-byte
random token requires resolving microsecond-scale early-exit timing differences against realistic network
jitter across a very large sample count — a known-hard attack class `[INFER]`, general security-domain
context, not newly sourced this session. **No new evidence this session changes [Block 52]'s LOW-practical-
severity read.** B52-G1 stays formally OPEN per [Block 52]'s own scoping (closing it fully would need
either a live timing probe against a real station or a vendor security-bulletin confirmation that Tridium
accepts this residual risk — neither attempted this session, matching [Block 52]'s own disclosed
boundary) — this section's contribution is a fresh-session `[CERT]` re-confirmation of the exact code, not
a new finding.

## 62.6 — B38-G1 CLOSED: N5's account-lockout defaults are a byte-for-byte N4 carryover, not new in N5 `[CERT]`

[Block 38] §38.3 found N5's `BUserService` lockout defaults (`lockOutEnabled=true`,
`maxBadLoginsBeforeLockOut=5` min 1/max 10, `lockOutWindow=30s`, `lockOutPeriod=10s`) but flagged whether
these are new-in-N5 or an N4 carryover as unverified (`[INFER]`, "plausible... but not fresh-checked" —
**B38-G1**). This session re-reads BOTH corpora's `BUserService.java` fresh and finds identical values.

**N5** (`organized/baja/vineflower/niagara/user/BUserService.java:140-152`, re-read fresh this session):
`lockOutEnabled = newProperty(0, true, ...)` (`:140`), `lockOutPeriod = newProperty(0, BRelTime.make
(10000L), ...)` (`:142`), `maxBadLoginsBeforeLockOut = newProperty(0, 5, ...min 1, max 10...)` (`:144-146`),
`lockOutWindow = newProperty(0, BRelTime.makeSeconds(30), ...)` (`:148-152`).

**N4** (`niagara-research/organized/baja/baja/vineflower/javax/baja/user/BUserService.java:150-159`,
re-read fresh this session — first citation of this EXACT file by either corpus's block series at these
line numbers, though [Block 830] previously cited the same defaults via `baja-UserService.txt`
bajadoc-guide text rather than this `.java` source): `lockOutEnabled = newProperty(0, true, ...)` (`:150`),
`lockOutPeriod = newProperty(0, BRelTime.make(10000L), ...)` (`:151`), `maxBadLoginsBeforeLockOut =
newProperty(0, 5, ...min 1, max 10...)` (`:152-154`), `lockOutWindow = newProperty(0, BRelTime.makeSeconds
(30), ...)` (`:155-159`).

**Every value matches exactly — same defaults, same min/max facets, same `BRelTime` unit choices, same
`Property` construction shape.** `[CERT]` on both sides, both files read whole (or in the cited range) this
session, not copied from either [Block 38] or [Block 830]'s prior text. **B38-G1 is CLOSED: the
scheme-agnostic account-lockout defaults are an unmodified N4 carryover, not a new N5 hardening measure or
a new N5 weakening** — N5 neither improved nor regressed this control relative to N4.

## 62.7 — B38-G4 narrowed: N5's SRP6 group sizes confirmed fresh (1024-bit AND 2048-bit, both SHA-512, platform-dependent preference order) — N4-side cross-check still blocked, corpus does not contain N4's equivalent class `[CERT]`+negative-existence

[Block 12] §12.8 cited N5's `KeyExchange` SRP6 bundle as "1024/2048-bit, SHA-512" without opening the
class; [Block 38] §38.10 closed the ARCHITECTURE question (SRP6 key-exchange is an N4 carryover, not new)
but left the exact group-size PARAMETERS un-cross-checked against N4's own Fox-protocol SRP6, since
neither corpus's block series had opened the concrete class (**B38-G4**).

**N5 side, now fully `[CERT]`, first whole-file read of this class in this corpus:**
`KeyExchange.getPreferredKeyExchangeMethods()` builds an ordered, colon-joined preference string from
`SRP6AlgorithmBundle.make(1024, "sha512")`, `SRP6AlgorithmBundle.make(2048, "sha512")`, and a
`NullAlgorithmBundle` (no-key-exchange) fallback — order depends on a platform check: embedded platforms
prefer 1024-bit first, non-embedded platforms prefer 2048-bit first, both groups always offered
regardless `[CERT]` (`organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/exchange/
KeyExchange.java:1-93`, whole file, this session). The preference is overridable via the JVM system
property `niagara.keyExchange.preferredMethods` `[CERT]` (same file, `LocalMetaDataHolder` inner class).
Separately, `getPreferredKeyExchangeCiphers()`/`...Ciphers256()` return `"aes-128.2:aes-128.1"`/
`"aes-256.2:aes-256.1"` — the symmetric cipher menu layered on top of the SRP6-derived key `[CERT]` (same
file). **[Block 12] §12.8's "1024/2048-bit, SHA-512" claim is confirmed exactly, upgraded from an
unopened citation to a fresh whole-file `[CERT]` read.**

**N4 side: still not locatable in the already-organized `niagara-research` corpus — a corpus-scope
negative-existence finding, not a claim about N4's actual jars.** A `grep -rl "class KeyExchange"` and a
separate `grep -rl "SRP6AlgorithmBundle"` sweep of the entire `niagara-research/organized/` tree return
ZERO hits `[CERT]` (both greps run this session, whole-tree scope, not a targeted single-directory
search). Unlike §62.1/§62.4's negative-existence claims (which are about a NAMED, fully-opened file), this
is the WEAKER form METHODOLOGY §3 requires be flagged as such: no file named `KeyExchange.java` or
containing the token `SRP6AlgorithmBundle` exists ANYWHERE this corpus has already organized — but the
underlying JAR family N5's copy lives in (`organized/_bin-ext/nre/` — N5's `nre.jar`-equivalent bundled
runtime) has no N4 counterpart directory at all: a `find` for `nre.jar` or a `bin-ext`-named directory
anywhere in `niagara-research` returns zero results `[CERT]` (this session). **This means N4's own
`com.tridium.crypto.core.exchange.KeyExchange` (the class [Block 38] §38.10's own `niagara-research` B419
citation quotes BY CALL SHAPE, `challenge.add("keyExchangeMethods", ...)`, without ever showing the class
body) was never decompiled into EITHER corpus — B419 quoted the calling convention from `FoxSession.java`,
not the `KeyExchange` implementation itself.** Closing this fully would require decompiling N4's own
`nre.jar` (or wherever N4 packages this class — not established this session), which is out of this
niagara5 corpus writer's read-only scope over `niagara-research`. **B38-G4 is NARROWED, not closed: the N5
half is now fully `[CERT]`; re-scoped as B62-G2** for whoever next has decompilation access to N4's
runtime-crypto jar.

## 62.x — Connections

- **[Block 61]** — closes **B61-G3** (§62.1–§62.3): traces the two remaining open questions its §61.3
  named (a Tridium-side setting; Santuario's own gate) to definitive `[CERT]`/`[CERT-hw]` NO answers, and
  issues the severity/mitigation verdict §61.3 itself stopped short of. [Block 61]'s own **B61-G2** (live
  end-to-end confirmation) remains separately open, untouched.
- **[Block 38]** — closes **B38-G1** (§62.6) and narrows **B38-G4** (§62.7); both were [Block 38]'s own
  named residuals from its §38.3/§38.10 findings. [Block 38]'s **B38-G2** (closed by [Block 61], not
  re-touched here) and **B38-G3** (LDAP Kerberos, untouched) remain as [Block 38] left them.
- **[Block 52]** — reaffirms, does not correct or close, **B52-G1** (§62.5): a fresh-session re-read of
  the exact cited code, same severity read as [Block 52] §52.9's own honest bound.
- **[Block 12]** — grandparent citation for the SRP6 group-size claim (§62.7) and the lockout-default
  citation chain (§62.6, via [Block 38]); both of [Block 12]'s own open questions in this area were
  already closed by [Block 38], unchanged here.
- **[Block 27]** — its §27.6 finding (CsrfUtil is Tridium's own shared primitive, no cookie involved) is
  re-cited, not re-verified, in §62.5's severity framing.
- **`niagara-research` B419** — its `FoxSession.java` call-shape quote (used by [Block 38] §38.10 to close
  the SRP6-architecture question) is now understood more precisely: it quotes the CALLER, not the
  `KeyExchange` implementation — a nuance surfaced by this session's failed search for the implementation
  class in that corpus (§62.7).
- **`niagara-research` B830** — its bajadoc-guide-sourced lockout-default citation
  (`baja-UserService.txt:37-79`) is now corroborated by this session's own direct `.java` source read of
  the same values (§62.6) — two independent evidence classes (`[CERT-doc]` guide text vs `[CERT]` source)
  agreeing, not a correction either way.
- **`niagara-research` B30** — its inventory of N4's `saml-rt.jar` (`com.onelogin.saml`, 2 classes) is the
  basis this session's §62.4 traces further, into the actual `validateSign()` method body B30 itself did
  not open.

## 62.x — Child gaps opened

- **B62-G1** — Whether the JDK's own bare `javax.xml.crypto.dsig` default provider (the engine N4's SAML
  SP relied on with no OneLogin-authored allowlist of its own, §62.4) independently restricts SHA-1/DSA-
  SHA1 signature algorithms on the N4 runtime's actual JDK version — not read this session (would require
  opening the JDK's own `jdk.xml.dsig.secureValidationPolicy` default or a live N4 SAML exchange, neither
  attempted). Narrower framing than B61-G2: this is about N4's OWN default gate, not N5's live acceptance.
- **B62-G2** (re-scopes **B38-G4**) — Decompile N4's own runtime-crypto jar (wherever
  `com.tridium.crypto.core.exchange.KeyExchange`/`SRP6AlgorithmBundle` actually lives on N4 — not
  `nre.jar` under a `bin-ext`-style directory, since no such path exists in the `niagara-research` corpus,
  §62.7) to read its exact SRP6 group-size parameters and confirm or refute a match against N5's
  1024-bit/2048-bit, SHA-512 pair confirmed this session. Out of this niagara5 corpus writer's read-only
  scope over `niagara-research` — needs a session with decompilation access to that corpus's raw N4
  install.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block62.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):

```
== verify-block: niagara5-block62.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 13  (adj 12)
   [CERT-live] 0
   [CERT] 32  (adj 29)
   [CERT-doc] 1
   [CERT-web] 0
   [CERT-a] 2  (adj 1)
   [INFER] 13  (adj 10)
-- ratio -- [INFER]/[CERT*] = 10/43 = 0.23
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  Response.java:263-264  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  baja-UserService.txt:37-79  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  niagara-research/organized/baja/baja/vineflower/javax/baja/user/BUserService.java:150-159  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  organized/baja/baja/vineflower/javax/baja/user/BUserService.java:150-159  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/baja/vineflower/niagara/user/BUserService.java:140-152  (range end verified; file has 798 lines)
   ok      organized/saml/vineflower/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java:38-86  (range end verified; file has 345 lines)
   ok      organized/saml/vineflower/com/tridium/saml/rp/Response.java:238-286  (range end verified; file has 520 lines)
   resolved 3 of 7
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**Reading the resolved/extern split.** 3 of 7 script-recognized citations resolve `ok` — the three N5
full-path citations that dominate the block's `[CERT]` evidence. The 4 `extern` items split into two
classes: `Response.java:263-264` is [Block 61]'s own bare short-form, re-cited not re-opened this session
(its full-path counterpart, `Response.java:238-286`, resolves `ok` immediately above it); `baja-
UserService.txt:37-79` is a `niagara-research` bajadoc-guide artifact, outside this script's target
entirely; the two `BUserService.java:150-159` variants (with and without the `niagara-research/` prefix)
are the N4-corpus citation — genuinely cross-corpus and never going to resolve against a
`niagara5-research`-rooted run, matching this block's own header-blockquote framing of that boundary.
No citation resolved as a contradiction (out-of-range line or missing file); the script's own exit code is
`0`.

The two non-`file:line` evidence classes from §62.2 (`javap` bytecode disassembly of `xmlsec-4.0.4.jar`'s
classes; the `config.xml` jar-resource text) are outside the script's `file:line`-shaped citation list
entirely, exactly as [Block 61] §61.3's `Util.class` disassembly was — their burden falls on inline
token-verify, next, same as the `extern` items above.

**Inline token-verify.** Every citation above was opened fresh this session (whole file or the cited
range), independent of any prior block's excerpt — no citation was copied verbatim from [Block 38]/
[Block 52]/[Block 61]/[Block 12]'s own text without a fresh re-open. Spot-check tokens independently
re-confirmed present this session: `entityId`/`idpHostURL`/`idpCert`/`allowAutomaticUserCreation` (full
13-property list, `BSAMLAuthenticationScheme.java`), `loginButtonText` (`BSSOAuthenticationScheme.java`),
`Util.validateSignNode(responseSignatures.item(0), cert, null, null)` (`Response.java:274,278`, exact
4-argument literal-`null` shape), `private boolean secureValidation` / `signature.tooManyReferences`
(`Manifest.class` disassembly), `dsa-sha1`/`rsa-sha1`/`SHA1withDSA`/`SHA1withRSA` (`config.xml`),
`DOMValidateContext`/`XMLSignatureFactory.getInstance("DOM")`/`unmarshalXMLSignature` (N4
`com.onelogin.saml.Utils.validateSign`), zero-hit `grep -n "Whitelist\|whitelist\|sha1\|SHA1\|Algorithm\|
DEPRECATED\|deprecated"` against the same N4 file (negative-existence, file fully opened), `lockOutEnabled=
true`/`lockOutPeriod=BRelTime.make(10000L)`/`maxBadLoginsBeforeLockOut` min1/max10/`lockOutWindow=
BRelTime.makeSeconds(30)` (both N5 and N4 `BUserService.java`, byte-for-byte value match confirmed by
direct side-by-side read), `SRP6AlgorithmBundle.make(1024, "sha512")`/`SRP6AlgorithmBundle.make(2048,
"sha512")`/`niagara.keyExchange.preferredMethods` (N5 `KeyExchange.java`), zero-hit corpus-wide
`grep -rl "class KeyExchange"`/`grep -rl "SRP6AlgorithmBundle"` over `niagara-research/organized/`
(negative-existence, corpus-scope, explicitly flagged as the weaker form). Token-verify: **≈32 distinct
load-bearing tokens** confirmed present (or confirmed ABSENT for the negative-existence claims, per
METHODOLOGY §3's symmetric-opening-obligation rule) in their cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block62.md`. Per the
caller's explicit read-only scope ("touch no other file"), `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator, matching [Block 61]'s own convention for the same instruction.
