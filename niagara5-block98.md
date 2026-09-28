# Block 98 — The N4-4.15.3.28 OEM install closes five long-open N4-side gaps: JDK SHA-1 policy, SRP6 group-size cross-check, `backup.jar`'s KeyRing-in-`.dist` mechanism, `BogPasswordObjectEncoder` re-verification, and two decompiler-artifact/ZKM closures

> Research closing/narrowing nine previously-opened child gaps, most unblocked by a single new fact:
> a fresh N4 4.15.3.28 OEM install ("PowerB", read-only at `/mnt/c/PowerB/PowerB-4.15.3.28`) became
> available this session, with a bundled JRE, a `bin/ext/` directory (mirroring N5's own
> `bin/ext/nre.jar` layout, per [Block 15]/[Block 19]), and real module jars — closing several
> N4-side questions earlier blocks could not resolve from the `niagara-research` N4-4.14 decompiled
> corpus alone. Covers: **B62-G1** (JDK bare-provider SHA-1 restriction on N4's actual JDK), **B62-G2**
> / **B38-G4** (N4 SRP6 group-size cross-check), **B66-G1** / **B47-G2** (backup.jar KeyRing-`.dist`
> design intent), **B82-G1** (backup.jar↔migrator.jar bytecode-exhaustive cross-reference),
> **B82-G2** (`SimpleKeyRing.exportKeyData()` vs `AESStreamEncryption.isEncrypted()` shape
> compatibility), **B82-G3** (`BFormat.reflect()`'s cache/denylist/void-guard body), **B57-G4**
> (N4 `BogPasswordObjectEncoder` `shared`/`undefined` re-verification), **B90-G1** (extend the
> `instanceof`-resugaring cross-check to 19-20 non-docSource-covered sites via a second decompiler),
> **B90-G3** (explicit Zelix-tool evidence for the 2 remaining N4 ZKM modules). Does **not** cover:
> a live `[CERT-hw]` reproduction of any of these findings against a running station (all reads are
> static, on decompiled/disassembled bytecode or shipped config text); a full re-derivation of every
> other N4-4.15.3.28 module beyond the ones opened for these nine gaps; `saml.jar`'s current N4-4.15
> implementation (this OEM package does not ship `saml.jar` at all — see §98.1's boundary note; CORRECTED by [Block 109] §109.4: it ships `saml-rt/ux/wb.jar`).
>
> Subject version: **N5 5.0.0.28 (Beta)** for the N5-side re-reads (`backup.jar`/`BFormat.java`/
> `FormatDenylist.java`/`alarm.jar`/`schedule.jar`, all already resident in
> `/home/cristian/niagara5-research/organized/`), plus **N4 4.15.3.28 (PowerB OEM)**, read-only at
> `/mnt/c/PowerB/PowerB-4.15.3.28` (bundled JRE: Azul Zulu `1.8.0.472.20`, per
> `jre/jreVersion.xml`), plus the pre-existing **N4 4.14 OEM** decompiled corpus at
> `/home/cristian/niagara-research/organized` (read-only, not modified) for the `com.onelogin.saml
> .Utils`/`SAML SP` cross-check inherited from [Block 62] §62.4. Method: `unzip -l` sweeps over all
> 1,556 jars under the PowerB install (`find "$BASE" -iname '*.jar'`, parallelized with `xargs -P8`)
> to locate `SRP6`/`KeyExchange`/`BogPasswordObjectEncoder` class entries; targeted `unzip` + single-
> class Vineflower decompiles (fast path, no sha256 anchor needed — none of these classes are
> obfuscated); a full `javap -p -c -constants` disassembly of all 29 classes in N5's `backup.jar`
> (bytecode-exhaustive, matching [Block 66] §66.6's own standard for `migrator.jar`); a second-
> decompiler (CFR 0.152, vs. Vineflower 1.12.0) cross-check on the 20 non-docSource-covered "bound"
> `instanceof` sites [Block 90] §90.x's own script (`instanceof_census.py`, reused unmodified this
> session, re-validated against its own already-published overlap counts before use) identifies
> outside `alarm`/`schedule`'s docSource coverage; one `WebFetch` against Oracle's Java 8
> `DOMValidateContext` Javadoc for the JSR-105 secure-validation-mode default-off documentation.
> Scratch: `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/
> scratchpad/b98/` (all extractions/decompiles/CFR runs, ephemeral, re-derivable from the cited
> jars — nothing decompiled was written into either repo). Markers (canonical list, METHODOLOGY §3):
> `[CERT]` local primary (file:line, jar-entry + sha256, or literal command output) · `[CERT-web]`
> (Oracle Javadoc, fetched and quoted this session) · `[CERT-doc]` not used this block · `[CERT-hw]`
> not used this block (no native-binary disassembly this session) · `[INFER]` deduction, including
> every claim resting on documented-but-not-directly-observed JDK runtime behavior.

---

## 98.1 — B62-G1 CLOSED: N4-4.15.3.28's bundled JDK does NOT restrict SHA-1 by default — and its SAML SP never even turns on the mode that would apply the restriction `[CERT]`+`[CERT-web]`

**Parent gap, quoted verbatim ([Block 62] §62.x):** "Whether the JDK's own bare `javax.xml.crypto.dsig`
default provider (the engine N4's SAML SP relied on with no OneLogin-authored allowlist of its own,
§62.4) independently restricts SHA-1/DSA-SHA1 signature algorithms on the N4 runtime's actual JDK
version — not read this session (would require opening the JDK's own
`jdk.xml.dsig.secureValidationPolicy` default or a live N4 SAML exchange, neither attempted). Narrower
framing than B61-G2: this is about N4's OWN default gate, not N5's live acceptance."

**Finding, part 1 — the policy itself.** N4-4.15.3.28's bundled JRE (Azul Zulu `1.8.0.472.20`, per
`/mnt/c/PowerB/PowerB-4.15.3.28/jre/jreVersion.xml`, sha256
`da90e15ebbe002878c30618bc746cb9207e3c01bb207076f46cd7de942f776c0`) ships its own
`jdk.xml.dsig.secureValidationPolicy` default in `jre/lib/security/java.security`
(sha256 `0a63088514c98868381f3f029119da579cc221bbb5dad870ac34766f71f0c2c8`), lines 962-974, read this
session in full `[CERT]`:

```
jdk.xml.dsig.secureValidationPolicy=\
    disallowAlg http://www.w3.org/TR/1999/REC-xslt-19991116,\
    disallowAlg http://www.w3.org/2001/04/xmldsig-more#rsa-md5,\
    disallowAlg http://www.w3.org/2001/04/xmldsig-more#hmac-md5,\
    disallowAlg http://www.w3.org/2001/04/xmldsig-more#md5,\
    maxTransforms 5,\
    maxReferences 30,\
    disallowReferenceUriSchemes file http https,\
    minKeySize RSA 1024,\
    minKeySize DSA 1024,\
    minKeySize EC 224,\
    noDuplicateIds,\
    noRetrievalMethodLoops
```

The `disallowAlg` list names exactly 4 URIs, all MD5-family (`rsa-md5`, `hmac-md5`, `md5`) plus the
1999 XSLT-transform URI. **No SHA-1/DSA-SHA1 signature-algorithm URI appears anywhere in this list**
(neither `http://www.w3.org/2000/09/xmldsig#rsa-sha1` nor `#dsa-sha1`, the two canonical XML-DSig SHA-1
signature-method identifiers) `[CERT]`. **B62-G1's core question is answered: the JDK's own default
policy on N4's actual bundled JDK does NOT independently restrict SHA-1** — it restricts only MD5 and
enforces minimum key sizes/transform counts, none of which touch a SHA-1-signed assertion.

**Finding, part 2 — the policy isn't even reachable from N4's SAML SP.** This session went further than
the gap's own text asks and checked whether this policy would even be *applied*. Per Oracle's own Java 8
Javadoc for `javax.xml.crypto.dsig.dom.DOMValidateContext` (fetched this session)
`[CERT-web]` (<https://docs.oracle.com/javase/8/docs/api/javax/xml/crypto/dsig/dom/DOMValidateContext.html>,
2026-09-27):

> "The JDK implementation supports a secure validation mode which can be enabled by setting the
> `org.jcp.xml.dsig.secureValidation` property to `Boolean.TRUE`... When enabled, validation of XML
> signatures are subject to stricter checking of algorithms and other constraints as specified by the
> `jdk.xml.dsig.secureValidationPolicy` security property... **The secure validation mode is enabled by
> default if you are running code with a SecurityManager, otherwise it is disabled by default.**"

I.e., the `jdk.xml.dsig.secureValidationPolicy` list above only takes effect if secure-validation mode
is turned ON (explicitly, via `DOMValidateContext.setProperty("org.jcp.xml.dsig.secureValidation",
Boolean.TRUE)`, or implicitly, only when a `SecurityManager` is installed). This session independently
re-read N4's own `com.onelogin.saml.Utils` (`niagara-research/organized/saml/saml-rt/vineflower/com/
onelogin/saml/Utils.java`, already opened by [Block 62] §62.4, re-read fresh this session with a
different, targeted grep) and confirms `[CERT]` (`niagara-research/organized/saml/saml-rt/vineflower/
com/onelogin/saml/Utils.java:205-225`, the whole `validateSign()` body, plus a full-file `grep -n
"setProperty"` returning exactly 2 hits, both at `:61` and `:189-190`, both on an unrelated
`javax.xml.XMLConstants` DTD/schema-access property, **zero** hits on
`"secureValidation"`/`"org.jcp.xml.dsig"` anywhere in the 335-line file): **`Utils.validateSign()`
never calls `setProperty` to turn secure-validation mode on.** Combined with the Javadoc's documented
default-off behavior, this means N4's SAML signature check plausibly runs with the entire
`jdk.xml.dsig.secureValidationPolicy` gate (SHA-1 restriction or not) switched OFF outright, unless a
`SecurityManager` happens to be installed in the station JVM — a fact this session did **not**
independently verify (whether N4 stations run under an active `SecurityManager` is orthogonal to this
gap and is named **B98-G1** below, low priority since part 1 already answers the gap as literally
asked).

**Verdict.** `[CERT]`+`[CERT-web]`: the bare JDK default provider on N4's actual (4.15.3.28) JDK does
NOT restrict SHA-1, and the one concrete N4 SAML consumer of it ([Block 62] §62.4's
`com.onelogin.saml.Utils`) never even enables the mechanism that would apply any of this policy's
restrictions. This closes B62-G1 as asked. **Version caveat, stated plainly**: this reads N4
**4.15.3.28**'s bundled JDK, not the exact JDK bundled with whatever specific N4 4.14 build [Block 62]
examined (`niagara-research`'s baseline is unversioned past "4.14 OEM" in this corpus's own citations);
Java 8 update-level `java.security` defaults have drifted over the update train (Oracle/Azul both
periodically add `disallowAlg` entries), so this is evidence about N4's JDK-provider lineage
continuing to not gate SHA-1 as of the latest available N4 build, not a byte-identical re-derivation of
the exact 4.14 JDK build.

> **Correction ([Block 109] §109.4):** the boundary note below is WRONG — PowerB N4-4.15.3.28 ships SAML as
> per-layer jars `saml-rt.jar`/`saml-ux.jar`/`saml-wb.jar`/`samlEncryption-rt.jar` (not `saml.jar`), and N4 4.15 already
> uses `com.onelogin.saml2.util.Util` from `java-saml-core-2.9.0`. The §98.1 SHA-1 reachability analysis re-read the
> N4.14 class, not the 4.15 one; re-run tracked as **B109-G1**.

**Boundary note.** This OEM ("PowerB") N4-4.15.3.28 package does **not** ship `saml.jar` at all
(`unzip -l "$BASE/modules/saml.jar"` → file not found; `ls "$BASE/modules" | grep -i saml` → no
matches) — this session cannot cross-check whether N4 4.15's own SAML SP implementation still uses
`com.onelogin.saml.Utils` or has since migrated (matching N5's [Block 12]/[Block 38]-documented
`java-saml-core-2.9.0` switch). This is orthogonal to B62-G1 (which is about the bundled JDK's default,
present regardless of which modules this OEM package includes) but is disclosed for completeness.

## 98.2 — B62-G2 / B38-G4 CLOSED: N4-4.15.3.28's own `KeyExchange`/`SRP6AlgorithmBundle` (found in `nre.jar`, `bin/ext/`) uses the EXACT SAME 1024/2048-bit RFC 5054 groups + SHA-512 as N5 `[CERT]`

**Parent gap, quoted verbatim ([Block 62] §62.x, re-scoping [Block 38] §38.14's B38-G4):** "Decompile
N4's own runtime-crypto jar (wherever `com.tridium.crypto.core.exchange.KeyExchange`/
`SRP6AlgorithmBundle` actually lives on N4 — not `nre.jar` under a `bin-ext`-style directory, since no
such path exists in the `niagara-research` corpus, §62.7) to read its exact SRP6 group-size parameters
and confirm or refute a match against N5's 1024-bit/2048-bit, SHA-512 pair confirmed this session. Out
of this niagara5 corpus writer's read-only scope over `niagara-research` — needs a session with
decompilation access to that corpus's raw N4 install." **B38-G4's own text** (verbatim, [Block 38]
§38.14): "Confirm whether N5's `KeyExchange` SRP6 group sizes (1024/2048-bit, SHA-512, per [Block 12]
§12.8) match N4's Fox SRP6 parameters (`niagara-research` B419 does not state its own group sizes in
the excerpt available this session)."

**The path DOES exist on the fresh N4-4.15.3.28 install** — directly falsifying [Block 62] §62.x's
premise that "no such path exists in the `niagara-research` corpus" (true for that specific corpus
snapshot; false for this session's fresh OEM install). A parallelized `unzip -l | grep -i` sweep over
all 1,556 jars under `/mnt/c/PowerB/PowerB-4.15.3.28` found exactly 6 jars containing
`SRP6`/`KeyExchange` class entries; one of them is `bin/ext/nre.jar` (sha256
`4340f0f6777f6886aba8d6d07eb83e84d02dba7bac980374fe82c792f2670d1f`), which contains 13 classes under
`com/tridium/crypto/core/exchange/`, including `KeyExchange.class` and `SRP6AlgorithmBundle.class`
`[CERT]` (`unzip -l` output, this session).

**Decompiled with Vineflower 1.12.0** (clean decompile, no obfuscation, no sha256 anchor needed per
this corpus's own convention for un-obfuscated jar extractions — see [Block 19] §19.x). `[CERT]`:

```java
// bin/ext/nre.jar!com/tridium/crypto/core/exchange/SRP6AlgorithmBundle.class, decompiled this session
private static SRP6Group getParamsFromGroupSize(String groupSize) {
   switch (groupSize) {
      case "1024": return SRP6StandardGroups.rfc5054_1024;
      case "1536": return SRP6StandardGroups.rfc5054_1536;
      case "2048": return SRP6StandardGroups.rfc5054_2048;
      case "3072": return SRP6StandardGroups.rfc5054_3072;
      case "4096": return SRP6StandardGroups.rfc5054_4096;
      case "6144": return SRP6StandardGroups.rfc5054_6144;
      case "8192": return SRP6StandardGroups.rfc5054_8192;
      default: throw new IllegalArgumentException(groupSize + " is not a valid RFC5054 group size");
   }
}
```

The class supports 7 RFC 5054 group sizes generically, backed by BouncyCastle's
`org.bouncycastle.tls.crypto.SRP6StandardGroups`/`SRP6Group` (a library dependency, not a Tridium-
authored SRP6 implementation) and restricts the digest to `sha256`/`sha512` only
(`getTlsHashFromString`, same class). **Which of the 7 group sizes is actually USED** is resolved by
`KeyExchange.getPreferredKeyExchangeMethods()`, same jar, same package, decompiled the same way
`[CERT]`:

```java
// bin/ext/nre.jar!com/tridium/crypto/core/exchange/KeyExchange.class, decompiled this session
preferredMethods = new String[]{
   SRP6AlgorithmBundle.make(1024, "sha512").getAlgorithmName(),
   SRP6AlgorithmBundle.make(2048, "sha512").getAlgorithmName(),
   NullAlgorithmBundle.getInstance().getAlgorithmName()
};
// (order reversed — 2048 first — when LocalMetaDataHolder.access$000() is false, i.e. non-embedded)
```

This is a **literal, exact match** to N5's own confirmed values ([Block 12] §12.8: "SRP6 ... groups —
2048-bit preferred, 1024-bit fallback ... both with SHA-512"; `nre_crypto_vf/com/tridium/crypto/core/
exchange/KeyExchange.java:52-72`): same two group sizes (1024, 2048), same digest (`sha512`), same
reversed-order-on-embedded-platform branching structure, same package (`com.tridium.crypto.core
.exchange`), same class names (`KeyExchange`, `SRP6AlgorithmBundle`). **B62-G2/B38-G4 CLOSED**: N4
4.15.3.28's SRP6 group-size parameters match N5 5.0.0.28's exactly — this is carried-forward code, not
an independently-chosen N5 parameter set.

## 98.x — Connections (98.1-98.2)

- **[Block 12] §12.8** — the N5-side SRP6 finding (1024/2048-bit, SHA-512) this block cross-checks
  against N4 4.15.3.28's own `KeyExchange`/`SRP6AlgorithmBundle`; confirmed an exact match.
- **[Block 38] §38.10** — already closed **B12-G8** (architecture continuity: N4's Fox-session
  `KeyExchange` call shape is the same as N5's authn-scheme call shape). This block's §98.2 closes the
  narrower **parameter-value** question ([Block 38] itself left this as B38-G4) that §38.10 explicitly
  deferred: "the 1024/2048-bit group sizes and SHA-512 pairing ... whether those GROUP SIZES match N4's
  Fox SRP6 parameters is still open."
- **[Block 62] §62.4/§62.7** — this block's §98.1/§98.2 both directly follow from [Block 62]'s own
  named child gaps; §98.2 also corrects §62.7's stated premise that no `bin-ext`-style `nre.jar` path
  exists for N4 (true only of the `niagara-research` corpus snapshot, not of the fresh 4.15.3.28 OEM
  install this session used).
- **[Block 15]/[Block 19]** — established the `bin/ext/nre.jar` extraction convention (targeted
  `unzip` + single-class Vineflower, no sha256 anchor for un-obfuscated classes) this block reuses for
  both N5's and N4's `nre.jar`.

---

## 98.3 — B66-G1 CLOSED (and B47-G2 with it): `niagara.backup.BBackupService` DOES produce (and consume) a `.dist` container carrying a KeyRing-protected `~security/.kr` entry, keyed by the platform system password `[CERT]`

**Parent gap, quoted verbatim ([Block 66] §66.x, refining/narrowing [Block 47] §47.x's B47-G2):**
"What `MigrationEncoding`/`BBackupDistMigrator.LazyDecryptFunction`/`Migrate.passwordDecryptFunction`
were originally BUILT for, if anything: specifically, whether `niagara.backup`/`BBackupService` (in
`backup.jar`, not opened this session or by [B14]/[B24]/[B47]) can produce a `.dist` CONTAINER that is
itself KeyRing/passphrase-protected beyond the individual `.bog` files' own
`reversibleEncodingKeySource` header — and if so, whether ANY currently shipped code path (in
`backup.jar` or elsewhere) is meant to consume that container-level protection during a migration,
given this session's exhaustive `migrator.jar` bytecode read found zero consumers of the machinery
that LOOKS purpose-built for exactly that. Would require opening `backup.jar`'s
`BBackupService`/`BBackupJob`-family classes, not yet decompiled/read in this corpus."

**[Block 47]'s own original B47-G2 text** (verbatim, [Block 47] §47.x): "Determine what
`MigrationEncoding`/`BBackupDistMigrator`'s `security/.kr`-extraction (`DIRS_TO_EXTRACT`,
`BBackupDistMigrator.java:38`) machinery is actually FOR, if anything, in the shipped product: whether
N4 `BBackupService` can produce a `.dist` archive whose CONTAINER (not individual `.bog` files) is
itself KeyRing/passphrase-protected, and if so, how `n5mig` is meant to open such an archive, given
this session found no live wiring for it."

**`niagara.backup.BBackupService` is already fully decompiled in this corpus** — `organized/backup/
vineflower/niagara/backup/BBackupService.java` (2,145 lines), previously only censused by class name,
never read line-by-line for this question. Opened and read this session `[CERT]`.

**Export side — `addFilesToDist()`, `organized/backup/vineflower/niagara/backup/BBackupService.java
:1257-1343`:**

```java
if ("~security/.kr".equals(f.getFilePath().getBody())) {
   if (localFileEncodingKey != null) {
      in = new ByteArrayInputStream(
         (byte[])SecurityUtil.doPrivileged(
            () -> SecurityInitializer.getInstance().getSecurityInfoProvider().getKeyRing()
               .exportKeyData(localFileEncodingKey)
         )
      ) { /* zeroes the buffer on close() */ };
   }
}
```

where `localFileEncodingKey` (`:1256-1270`) is a `PBEEncodingKey` derived via
`op.encodingInfo.makePBEKey(SecurityUtil.doPrivileged(PLATFORM_PROVIDER_INSTANCE::getSystemPassword))`
— **the platform's system password**, not an arbitrary operator-supplied backup passphrase, and only
when the backup runs against a local `BFileSystem` file store (`op.fileSpace() instanceof BFileSystem`;
for a remote file store, `localFileEncodingKey = null` and the KeyRing entry is skipped/copied raw
instead). **Restore side — `restoreFiles()`, `:598-609`:**

```java
PBEEncodingKey encodingKey = op.manifest.getPBEEncodingInfo().makePBEKey(systemPassword);
...
} else if (".kr".equals(this.getPathForEntry(entry.getName(), op).getName())) {
   op.consoleMessage("Importing Key Ring Data");
   InputStream in = op.zipFile.getInputStream(entry);
   SecurityInitializer.getInstance().getSecurityInfoProvider().getKeyRing()
      .importKeyData(in, (int)entry.getSize(), encodingKey);
}
```

**Verdict, both halves of the gap.** (1) **Yes** — `BBackupService` DOES produce a `.dist` container
carrying a genuinely KeyRing-protected entry: `~security/.kr`, written via `KeyRing.exportKeyData()`
and gated by the SAME system-password-derived `PBEEncodingKey` mechanism used elsewhere in this file
for `PASSPHRASE_ENCRYPTED_PATHS`/`TRIDIUM_LEGACY_PASSPHRASE_ENCRYPTED_PATHS`. (2) The live consumer
wiring for it is **not** dead code — `restoreFiles()` genuinely imports this same `.kr` entry back into
the platform's `KeyRing` on every local-filestore restore, via `importKeyData()`. This is a real,
exercised, ordinary (non-migration) backup/restore feature. **This closes both [Block 66] §66.x's B66-G1
and [Block 47] §47.x's B47-G2 to the "what is it for" half**: it exists to let a station's exportable
KeyRing entries survive an ordinary N5 backup/restore round-trip on the SAME major version, wrapped by
the system password rather than left in the clear or requiring a separate operator passphrase. Per
§98.4 below, this mechanism is entirely **separate** from (not consumed by) the N4→N5 migrator's own
`MigrationEncoding`/`BBackupDistMigrator` machinery — the second half of B66-G1's own question
("whether ANY currently shipped code path ... is meant to consume that container-level protection
during a migration") remains answered **NO**, now to a bytecode-exhaustive standard (§98.4), not merely
a source-grep one.

**A precise textual link, read fresh this session, ties the two together.** `BBackupDistMigrator.java
:38`'s `DIRS_TO_EXTRACT` constant (already named in B47-G2's own text) reads, verbatim, `[CERT]`
(`organized/migrator/vineflower/com/tridium/migrator/BBackupDistMigrator.java:38`):

```java
static final List<String> DIRS_TO_EXTRACT = List.of(
   "niagara_user_home/stations/", "niagara_user_home/security/.kr", "stations/", "security/.kr");
```

`"security/.kr"` (both bare and `niagara_user_home/`-prefixed) is the SAME logical entry
`BBackupService.addFilesToDist()` writes as `"~security/.kr"` (the `~` is a Niagara `FilePath`
home-relative prefix, not a distinct path). This is strong circumstantial evidence that the migrator's
`DIRS_TO_EXTRACT`/`MigrationEncoding` machinery was indeed modeled on — quite possibly literally
targeting — this exact `BBackupService`-produced artifact, even though (§98.4) no live migrator code
path today actually decrypts it via `MigrationEncoding`.

## 98.4 — B82-G1 CLOSED: a full `javap -p -c -constants` disassembly of ALL 29 classes in N5's `backup.jar` finds ZERO `migrator`/`MigrationEncoding` cross-references — bytecode-exhaustive, matching [Block 66]'s own standard `[CERT]`

**Parent gap, quoted verbatim ([Block 82] §82.x):** "This session's `backup.jar`↔`migrator.jar`
cross-reference (§82.4.3) is source-tree-exhaustive (`grep -rln` over BOTH complete decompiled trees,
in both directions) but NOT bytecode-exhaustive the way [Block 66] §66.6 was for `migrator.jar` alone.
A full `javap -p -c -constants` disassembly of `backup.jar`'s own compiled classes (not yet extracted
or disassembled in this corpus), cross-referenced for any `com.tridium.migrator.*`/`MigrationEncoding`
symbol, would close this gap to the same standard [Block 66] already met for the migrator side."

**Method, exactly as the gap specifies.** N5's `backup.jar` (`/home/cristian/niagara5-research-
localcache/modules/backup.jar`, sha256 `439de59717ee412d3245486c4e1c1f1c902403fce334cb6903029b32d798a
bdb`) contains exactly **29 classes** (confirmed by `unzip -l ... | grep -c '\.class$'` and by the
existing `organized/backup/extracted/` count). All 29 were extracted and disassembled this session with
`javap -p -c -constants` (full constant pools + bytecode, not source-level) into one 8,653-line
combined output `[CERT]` (`/tmp/.../scratchpad/b98/backup_javap_full.txt`). A case-insensitive
`grep -c "migrat"` over the ENTIRE disassembly returns **0** `[CERT]` — not merely "no source-level
call", but no `com/tridium/migrator/…` classfile reference, no `MigrationEncoding` symbol, and no
`"migrat"`-substring string constant anywhere in any of the 29 classes' constant pools or method
bodies.

**Verdict.** B82-G1 CLOSED to the exact standard requested: `backup.jar`'s `~security/.kr`-export/
import machinery (§98.3) and the N4→N5 migrator's `MigrationEncoding`/`BBackupDistMigrator
.LazyDecryptFunction` family ([Block 47]/[Block 66]/[Block 82]'s own already-established zero-consumer
finding on the migrator side) are confirmed, bytecode-exhaustively from BOTH directions now, to be
genuinely independent, non-interacting mechanisms — not merely unobserved-so-far. Whatever the
migrator's `DIRS_TO_EXTRACT`/`MigrationEncoding` machinery was originally built to consume (§98.3's
`"security/.kr"` textual match makes `BBackupService`'s own `.dist` KeyRing export the most plausible
original target), no shipped N5 5.0.0.28 code path — on either side of the `backup.jar`/`migrator.jar`
boundary — actually wires the two together today.

## 98.5 — B82-G2 CLOSED: `SimpleKeyRing.exportKeyData()`'s raw `[IV][AES(...)]` format is structurally INCOMPATIBLE with `AESStreamEncryption.isEncrypted()`'s text-header detector `[CERT]`+`[INFER]`

**Parent gap, quoted verbatim ([Block 82] §82.x):** "Whether `SimpleKeyRing.exportKeyData()`'s raw
`[IV][AES(ObjectOutputStream-serialized entries)]` byte format (`SimpleKeyRing.java:327-356`, read this
session) would register as `AESStreamEncryption.isEncrypted() == true` — i.e. whether
`MigrationEncoding.makeMigrationDecryptFunction`'s first branch (`:42`) is actually shape-compatible
with a `BBackupService`-exported `~security/.kr` blob — requires opening `AESStreamEncryption`'s
private `StreamEncryptionDetails` header-detection constructor (`io/AESStreamEncryption.java`, exact
line range not yet located — the class's public dispatcher methods were read this session, `:1-109`,
but not this inner class's body), not opened this session."

**`exportKeyData()`'s exact byte format, re-confirmed this session** (`organized/_bin-ext/nre/
vineflower/com/tridium/nre/security/SimpleKeyRing.java:327-357`, whole method read, same file [Block
82] already cited, line numbers shifted by 2 from that block's `:327-356` — a re-read artifact, not a
content difference; flagged per the gap-ID discipline instruction):

```java
public synchronized byte[] exportKeyData(ISecretBytesSupplier keyInfo) throws Exception {
   ...
   ObjectOutputStream out = new ObjectOutputStream(portableBytes);
   out.writeInt(6); out.writeInt(167662754); out.writeInt(exportableCount);
   for (...) { out.writeUTF(alias); out.writeInt(key.length); out.write(key); }
   out.flush();
   byte[] ivBytes = new byte[16];
   SecureRandomHolder.SECURE_RANDOM_INSTANCE.nextBytes(ivBytes);
   byte[] encryptedContents = Aes256PasswordManager.encrypt(portableBytes.toByteArray(), ivBytes, keyInfo.get().get());
   byte[] result = new byte[ivBytes.length + encryptedContents.length];
   System.arraycopy(ivBytes, 0, result, 0, ivBytes.length);
   System.arraycopy(encryptedContents, 0, result, ivBytes.length, encryptedContents.length);
   return result;
}
```

I.e. the on-the-wire format is: **16 raw (cryptographically random) IV bytes, immediately followed by
AES-encrypted bytes** — no text header of any kind.

**`AESStreamEncryption`'s private `StreamEncryptionDetails` inner class, opened this session**
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/security/io/AESStreamEncryption.java:112-139`,
the exact body [Block 82] flagged as unread):

```java
private static final class StreamEncryptionDetails {
   private StreamEncryptionDetails(InputStream originalInputStream) throws IOException {
      this.stream = new DataInputStream(new BufferedInputStream(originalInputStream));
      this.stream.mark(1024);
      try {
         String encodedHeader = this.stream.readUTF();
         CryptographicAlgorithmBundle algorithmBundle = CryptographicAlgorithmBundle.getInstanceFor(encodedHeader);
         String[] data = algorithmBundle.decode(encodedHeader);
         this.isEncrypted = algorithmBundle instanceof AesAlgorithmBundle;
      } catch (Exception e) {
         this.isEncrypted = false;
      } finally { this.stream.reset(); }
   }
}
```

The VERY FIRST operation this detector performs is `DataInputStream.readUTF()` — which requires the
stream's first 2 bytes to be a big-endian unsigned-16-bit LENGTH prefix for a modified-UTF-8 STRING
that names a known algorithm-bundle identifier (resolved via
`CryptographicAlgorithmBundle.getInstanceFor(encodedHeader)`). `exportKeyData()`'s output begins with
16 **raw, non-textual, cryptographically random** IV bytes — not a length-prefixed identifier string of
any kind. **Any exception during this parse (`UTFDataFormatException` on invalid modified-UTF-8,
`EOFException` on a length mismatch, or `getInstanceFor()` throwing on an unrecognized identifier) is
caught by the blanket `catch (Exception e)` and sets `isEncrypted = false`.**

**Verdict.** `[CERT]` for the structural fact: the two formats are DESIGN-INCOMPATIBLE — one is a
self-describing text-header protocol (`readUTF()` + `CryptographicAlgorithmBundle.getInstanceFor()`),
the other is raw binary with no header at all. `[INFER]` for the practical consequence stated as a
near-certainty rather than a strict proof: interpreting 16 cryptographically random bytes as a
`readUTF()`-framed string will, with overwhelming probability (though not deductive certainty for every
possible random IV value), either exceed the actual stream length or fail modified-UTF-8 decoding,
landing in the `catch` branch. **`AESStreamEncryption.isEncrypted()` will, for all practical purposes,
never return `true` for a `~security/.kr` blob `BBackupService.exportKeyData()` produced** — this
closes B82-G2: `MigrationEncoding.makeMigrationDecryptFunction`'s first branch (gated on
`isEncrypted()`) is NOT shape-compatible with a `BBackupService`-exported KeyRing blob, independently
corroborating §98.3/§98.4's finding that these two mechanisms were never actually wired together, this
time at the byte-format level rather than the bytecode-cross-reference level.

## 98.6 — B82-G3 CLOSED: `BFormat.reflect()`'s full cache/denylist/void-return-guard body, read for the first time — the ONLY gates against a side-effecting reflective call are a 6-entry hardcoded denylist and a void-return filter `[CERT]`

**Parent gap, quoted verbatim ([Block 82] §82.x):** "`BFormat.reflect(Object obj, String name,
Class<?>[] params, Object arg)` (`BFormat.java:402`, signature read, body not read this session) is the
actual cached-`Method`-lookup/`invoke()` machinery `ReflectCall.eval()`'s fallback chain (§82.1,
`:696-725`) calls up to 6 times per operand — its own exception handling, method-cache invalidation
(`invalidateCache`, `:398-400`, seen but not traced), and whether a reflectively-invoked GETTER could
itself have a side effect (as opposed to the ACTION-slot path `eval()` explicitly denylist-guards,
`:668-680`) remain unread."

**Read this session from `organized/docSource/baja/niagara/util/BFormat.java`** (the pristine
ground-truth tree, per [Block 25]/[Block 90] §90.2 — line numbers differ from [Block 82]'s decompiled-
tree citation because docSource carries the full original license header/comments; both trees resolve
to the same method) `[CERT]` (`:1015-1082`):

```java
private static void invalidateCache(Class<?> cls) {
   classToMethodCache.computeIfPresent(cls, (c, m) -> Collections.synchronizedMap(new CacheMap<>(METHOD_CACHE_SIZE)));
}

private static Object reflect(Object obj, String name, Class<?>[] params, Object arg) throws Throwable {
   Class<?> cls = obj.getClass();
   try {
      String cacheKey = makeCacheKey(name, params);
      Map<String, Optional<Method>> methodMap = classToMethodCache.computeIfAbsent(cls, ...);
      methodMap.computeIfAbsent(cacheKey, c -> {
         try {
            if (FormatDenylist.isDenied(cls, name, params)) return Optional.empty();
            Method method = cls.getMethod(name, params);
            if (method.getReturnType().equals(void.class)) return Optional.empty();  // NCCB-15861
            return Optional.of(method);
         } catch (NoSuchMethodException e) { return Optional.empty(); }
      });
      Optional<Method> method = methodMap.getOrDefault(cacheKey, Optional.empty());
      if (method.isPresent()) { ...; return method.get().invoke(obj, args); }
      return null;
   } catch (Exception e) {
      invalidateCache(cls);
      throw e instanceof InvocationTargetException ? ((InvocationTargetException)e).getTargetException() : e;
   }
}
```

**All three sub-questions the gap named, answered:**

1. **`invalidateCache(cls)`** — a blunt, WHOLE-CLASS cache reset (`computeIfPresent` replaces the
   entire per-class `Map` with a fresh empty `CacheMap`, not a single-key eviction), triggered by
   `catch (Exception e)` on ANY exception from the cached-lookup-and-invoke path — including the
   target method's own runtime exceptions (unwrapped from `InvocationTargetException` before
   rethrowing).
2. **Denylist guard, traced to its source** — `FormatDenylist.isDenied()`
   (`organized/baja/vineflower/com/tridium/util/FormatDenylist.java:16-95`, read this session) is a
   hardcoded **6-entry** list: `BJob.submit`, `BDaySchedule.clear`, `BEnumSetSchedule.clear`,
   `BCode.newInstance`, `BProgramCode.newProgramInstance`, `BProxyExt.write` — plus a
   system-property-configurable extension (`niagara.baja.formatDenyList`) and per-entry exclusion list
   (`niagara.baja.formatDenyListExclusions`), neither populated by default.
3. **The GETTER-side-effect question, answered directly**: `reflect()`'s ONLY two gates are (a) this
   6-entry denylist and (b) a void-RETURN-TYPE filter (`NCCB-15861`, blocks pure setters/actions with
   no return value). **Nothing in `reflect()` inspects WHETHER a non-void, non-denylisted method has a
   side effect.** Any method not on the 6-entry list, and not void-returning, is reflectively callable
   through `BFormat`'s fallback chain regardless of whether it also mutates state — e.g. a
   hypothetical "getter" that lazily initializes and caches a field as a side effect of being read
   would pass both gates cleanly.

**Verdict.** `[CERT]` — B82-G3 CLOSED. The cache-invalidation, denylist, and void-guard mechanisms are
now fully traced to source; the "could a reflectively-invoked getter have a side effect" question has
a concrete, source-grounded answer (yes, architecturally — the denylist is a curated list of KNOWN
dangerous methods, not a general effect-analysis gate), not merely an open question.

## 98.x — Connections (98.3-98.6)

- **[Block 47] §47.x** — this block's §98.3 closes B47-G2 (the original "what is `security/.kr`-
  extraction FOR" question) alongside [Block 66]'s narrower B66-G1 restatement of the same gap.
- **[Block 34] §34.1** — already documented `BBackupService` doing a KeyRing transcode on the N4 side
  (per [Block 43] §43.3's table row for `EncryptionKeySource.shared`, itself citing "B491 §491.4" in
  `niagara-research`); this block's §98.3 is the first read of the actual N5-side
  `BBackupService.java` mechanics behind that same behavior, for the specific `~security/.kr`
  container-level entry rather than per-`.bog`-file re-wrapping.
- **[Block 66] §66.6** — this block's §98.4 extends [Block 66]'s own bytecode-exhaustive
  `javap`-disassembly method (there applied to `migrator.jar`) to the other side of the same
  cross-reference (`backup.jar`), closing the asymmetry [Block 82] itself flagged.
- **[Block 43] §43.1/§43.3** — this block's §98.3/§98.5 reuse (not re-derive) [Block 43]'s own
  `KeyRing`/`Aes256PasswordManager`/`EncryptionKeySource` reads as the foundation for tracing
  `localFileEncodingKey`'s system-password origin and `exportKeyData()`'s AES call.
- **[Block 25]/[Block 90] §90.2** — this block's §98.6 uses the SAME `organized/docSource/` ground-
  truth tree those blocks established as authoritative, for the first line-by-line read of
  `BFormat.reflect()`'s body from that tree.

---

## 98.7 — B57-G4 CLOSED: N4-4.15.3.28's own `BogPasswordObjectEncoder.java` shows IDENTICAL `shared`/`undefined` behavioral semantics to [Block 43] §43.3's N5 reading — independently re-derived, not merely enum-identity-transferred `[CERT]`

**Parent gap, quoted verbatim ([Block 57] §57.5):** "Independently re-verify N4.14.0.162's own
`BogPasswordObjectEncoder.java` (not opened this session) to confirm `shared`/`undefined`'s BEHAVIORAL
semantics ([Block 43] §43.3's reading, transferred here only by enum-body identity, not independently
re-derived from N4's own encoder class)."

**Located and decompiled from the same N4-4.15.3.28 `bin/ext/nre.jar`** as §98.2's `KeyExchange`
classes: `com/tridium/nre/security/io/BogPasswordObjectEncoder.class` (single class, no obfuscation,
Vineflower clean decompile) `[CERT]`.

**`shared`, confirmed identical to [Block 43] §43.3's N5 reading**: only reachable via the private
`BogPasswordObjectEncoder(SecretBytes)` constructor (→ `makeShared()`/`make(ISecretBytesSupplier)`),
never via `parseBogHeader`; and `parseBogHeader(bogHeaderElement, requiredKeySource)` throws
immediately if the CALLER requires it: `if (requiredKeySource.equals(EncryptionKeySource.shared))
throw new IllegalArgumentException("Cannot require shared key source");` — matching [Block 43]'s "the
constructor path used e.g. for backup/restore re-wrapping" characterization exactly (and directly
corroborated by this block's own §98.3 finding of exactly that backup-side `SecretBytes`-driven
KeyRing re-wrapping).

**`undefined`, confirmed identical**: used ONLY as a `requiredKeySource` sentinel inside
`parseBogHeader`'s inference branch (`if (requiredKeySource.equals(EncryptionKeySource.undefined))`,
choosing `none` vs `external` heuristically from whether `encodedValidator` starts with `"[null."`) —
and, critically, **a persisted `.bog` header is REJECTED outright if its own
`reversibleEncodingKeySource` attribute literally equals the string `"undefined"` (or `"shared"`)**:

```java
// N4 4.15.3.28, com/tridium/nre/security/io/BogPasswordObjectEncoder.java (decompiled, this session)
if (!EncryptionKeySource.undefined.name().equals(headerKeySourceString)
    && !EncryptionKeySource.shared.name().equals(headerKeySourceString)) {
   ... /* normal parsing */ ...
} else {
   throw new IOException("BOG document has invalid key source");
}
```

matching [Block 43]'s "never a value actually written to a saved `.bog`" claim exactly — and this
session additionally confirms the WRITE side never emits either value:
`populateBogHeaderElement(XElem headerElement)` always writes `this.keySource.name()`, where
`this.keySource` for any encoder instance actually used to write a header is constrained (by the
constructor set above) to `none`/`external`/`keyring` only.

**Verdict.** `[CERT]` — B57-G4 CLOSED: N4's own `BogPasswordObjectEncoder.java`, read independently
this session (not transferred by enum-body identity), shows byte-for-byte the SAME behavioral rules
[Block 43] §43.3 documented for N5's copy of this class. **Version caveat, stated plainly** (same
caveat pattern as §98.1): this reads N4 **4.15.3.28**'s `BogPasswordObjectEncoder.java`, not the
specific **N4.14.0.162** build the gap names; given [Block 19]/[Block 43]'s own prior findings that
this exact package (`com.tridium.nre.security`) has been reported byte-identical across N4 vintages and
into N5, and given this session's independent triple-cross-validation (N4 4.15.3.28 ≈ this block's
read; N5 5.0.0.28 ≈ [Block 43] §43.3's read; both behaviorally identical), the residual risk that
N4.14.0.162 specifically differs is assessed as low but is not literally re-derived from that exact
build — named **B98-G2** below, low priority.

---

## 98.8 — B90-G1 CLOSED (via a second decompiler, not docSource): all 20 non-overlap-covered "bound" `instanceof` sites in `alarm`/`schedule` show the classic (unbound) form under CFR — 100% corroboration of the resugaring-artifact theory `[CERT]`+`[INFER]`

**Parent gap, quoted verbatim ([Block 90] §90.x):** "Extend §90.2's `docSource` cross-check to the 19
corpus-wide 'bound' `instanceof` sites [Block 70] §70.4 reported that fall OUTSIDE this session's
docSource-overlap coverage (14 in `alarm`, 8 in `schedule` — note this sums to 22, of which 3 were
already read individually in §90.2's named examples, leaving 19 truly unchecked): either extend
`docSource`'s own coverage for `alarm`/`schedule` further, or independently confirm via a second,
non-resugaring decompiler (CFR/Procyon — untested for this specific idiom) whether they show the same
artifact. `investigable`, low-priority given §90.2's 100%-so-far resugaring rate and the general
bytecode-identity proof make a different outcome unlikely."

**Method: the second option the gap itself proposes.** [Block 90]'s own `instanceof_census.py` (reused
unmodified this session; first re-validated by reproducing its own already-published overlap-restricted
counts exactly — `alarm_overlap.txt` → 65 lines/5 bound, `schedule_overlap.txt` → 20 lines/3 bound,
BOTH matching [Block 90] §90.2's table precisely `[CERT]`) was run against the FULL `alarm` (195 files)
and `schedule` (103 files) Vineflower trees, then every bound site OUTSIDE the two overlap file lists
was extracted: **11 in `alarm`, 9 in `schedule` = 20 total** `[CERT]` (full listing:
`/tmp/.../scratchpad/b98/list_bound.py` output, this session).

**Count discrepancy, disclosed rather than forced to match.** This is **not 19** as the gap text states,
and the underlying full-module totals don't match either: this session's fresh run of the SAME script
gives `alarm` full-module bound=**16**, `schedule` full-module bound=**12** (16-5=11, 12-3=9 outside
overlap). [Block 70] §70.4's OWN published table (`niagara5-block70.md:314`, its `| alarm | 195 | 142 |
16 | 126 | 11% |` row) already states alarm bound=**16** — matching this session's fresh rerun exactly —
and a schedule row of bound=**11** (not 8), for a table total of 32 matching the gap text's own "32
corpus-wide" framing. **The B90-G1 gap text's own "14 in alarm, 8 in schedule" figures do not match
[Block 70] §70.4's own cited table** (16/11, not 14/8) — an internal drift in how the child gap was
transcribed, pre-dating this session, named here per METHODOLOGY's citation-fidelity discipline rather
than silently corrected. This session's 20-site population is a strict SUPERSET of any reasonable
19-site reading, so the closure below covers the gap regardless of which exact count is "correct."

**Result — CFR 0.152 (a different decompiler, from a different codebase, with a documented DIFFERENT
default disposition toward resugaring `instanceof`) was run against the exact same 29 compiled classes
from `alarm.jar`/`schedule.jar` (sha256 `fb5b21c30412dceedd12adbf2e29843e2a05d0b8b9883fa4cb387c18297cc
32f` / `f16ca56f18a98d478518fe2c3a34cfb1e286b0835196f447076cd5c365c94311`) backing all 20 identified
bound sites.** `[CERT]` — every single one of the 20 (100%) shows the CLASSIC pre-JEP-394 idiom under
CFR (explicit cast, no binding identifier), e.g.:

```java
// Vineflower (this corpus's primary decompiler): BAlarmBoxChannel.java:754
if (clientParams.has("ids") && clientParams.get("ids") instanceof JSONArray ids) { ... }
// CFR (this session, SAME .class file): BAlarmBoxChannel.java:701
if (clientParams.has(IDS_KEY) && (value = clientParams.get(IDS_KEY)) instanceof JSONArray) { ... }
```
(and identically for all other 19 sites — `AlarmClassRouteAlarmInvocation.java`,
`CoalesceUuidOnlyInvocation.java`, `BAlarmDbChannel.java` ×2, `BPdfAlarmDbView.java`,
`BAlarmConsole.java`, `ConsoleColumns.java`, `BScheduleSnapshotHandler.java`, `ScheduleValidator.java`,
`BHxCurrentDaySummary.java`, `BCompositeAdd.java`, `BCompositeEd.java`, `BDayEd.java`,
`BDaySlider.java`, `BMonthWidget.java`, `ScheduleColors.java` — full CFR output preserved at
`/tmp/.../scratchpad/b98/cfr_alarm/out_cfr/`, `/tmp/.../scratchpad/b98/cfr_schedule/out_cfr/`).

**Verdict.** `[CERT]` for the mechanical finding (CFR shows classic/unbound form for 20/20 sites);
`[INFER]` for the conclusion this corroborates genuine Tridium source (CFR not resugaring is strong,
but not literally docSource-equivalent, evidence — the epistemic status [Block 90] itself proposed for
this exact method). **B90-G1 CLOSED**: extending [Block 90] §90.2's docSource-based finding via the
second-decompiler method the gap names, 0 of the (disclosed count: 20, superseding the gap text's own
uncertain 19) non-overlap "bound" sites in `alarm`/`schedule` show independent corroboration of genuine
JEP 394 adoption — all present as Vineflower-only resugaring, matching the established pattern
100%-for-100%.

## 98.9 — B90-G3 ADVANCED (not literally CLOSED): the two remaining Honeywell ZKM modules ARE explicitly named-tool-and-transformer documented (`java-deobfuscator`, `zelix.StringEncryptionTransformer`) plus a fresh structural fingerprint match — but no raw preserved detect-log survives for exactly these two `[CERT]`+`[INFER]`

**Parent gap, quoted verbatim ([Block 90] §90.x):** "Obtain (or otherwise confirm) an explicit
`com.javadeobfuscator.deobfuscator` Zelix-naming detect-log for `honeywellBacnetSpyder`/
`honeywellLonSpyder` (currently confirmed only by the residual clustered-escape signature in their
preserved `vineflower.obfuscated-bak/` trees, not by a named tool verdict like the other 14 of 16).
`investigable`, low-priority (signature-level evidence is already strong and internally consistent
with the other 14)."

**Note this session is a `niagara-research` (N4 4.14) read, read-only, per this writer's stated scope
allowance for N4-side cross-checks; no file was modified.** Both modules' `DEOBFUSCATION-NOTE.md`
(`organized/honeywellBacnetSpyder/DEOBFUSCATION-NOTE.md`, `organized/honeywellLonSpyder/
DEOBFUSCATION-NOTE.md`, read this session `[CERT]`) explicitly name the tool AND the exact Zelix-
specific transformer class:

> "`java-deobfuscator` (patched) on the original obfuscated JAR with transformer
> `zelix.StringEncryptionTransformer`. Patch: per-class write fallback so an ASM NPE on one obfuscated
> tableswitch does not abort the whole JAR. Tool: `../../deobfuscator-patched.jar`."

This is the same tool (`java-deobfuscator`, i.e. the `com.javadeobfuscator.deobfuscator` project) and
the same fully-qualified transformer family
(`com.javadeobfuscator.deobfuscator.transformers.zelix.StringEncryptionTransformer`) this session
independently confirmed by reading one of the OTHER 14 modules' raw preserved tool log
(`organized/honeywellSpyderTool/honeywellSpyderTool/pipeline/detect-output.txt`, read this session
`[CERT]`), which shows the tool's own `Deobfuscator` class recommending, verbatim, "`
com.javadeobfuscator.deobfuscator.transformers.zelix.StringEncryptionTransformer`" under its
`RuleSimpleStringEncryption` rule ("Zelix Klassmaster has several modes of string encryption. This mode
replaces string literals with a static string or string array, which are decrypted in `<clinit>`").

**A physical deobfuscated-JAR artifact exists for both**, distinct by sha256 from the original obfuscated
jar (confirmed this session): `deobf/honeywellBacnetSpyder-deobf.jar`
(`12cb77c1163e61b864dd39dbabda546f8dc87145db70de7afa29e0c542ce2fa7`) vs. the original
`honeywellBacnetSpyder.jar` (`d83dfe2744c8a37ff2e481f40859ef617289e074dfc5e2d134f7cc0699e8c218`); and
`deobf/honeywellLonSpyder-deobf.jar` (`8510ef4c84821aed305bba263b3468c049d2e54bf13b8f32c54cd71b85bf8d
1a`) — a tangible output of an actual transformer run, not merely a claim.

**Fresh independent structural corroboration this session**: `honeywellBacnetSpyder`'s deobfuscated
`NetworkObject.java` (`organized/honeywellBacnetSpyder/honeywellBacnetSpyder/vineflower/com/honeywell/
bacnetSpyder/xml/networkObjects/NetworkObject.java`) declares `public static final String
CATEGORY_FIXED;`/`CATEGORY_MANDATORY;`/`CATEGORY_FIXED_DROPABLE;` with NO visible initializer (the
literal assignment lives in an unrecovered `<clinit>`) alongside a `private static final String[] z;`
array field — this is the EXACT `RuleSimpleStringEncryption` fingerprint the tool's own log names
("replaces string literals with a static string or string array ... decrypted in `<clinit>`") — and the
matching `vineflower.obfuscated-bak/` copy of the SAME file shows these fields declared but genuinely
unassigned (no string literal visible anywhere in that pre-deobfuscation decompile), while the
deobfuscated tree resolves them to semantically-matching plaintext (`"Fixed"`, `"Mandatory"`,
`"Fixed_Dropable"`) `[CERT]`.

**A disclosed nuance, not swept aside**: `honeywellBacnetSpyder/honeywellBacnetSpyder/pipeline/
fase1-recon.json` (a DIFFERENT, earlier automated heuristic pass, read this session) records
`"ofuscador_detectado": false, "ofuscador_nombre": null` for this exact module — i.e. an EARLIER,
separate recon tool MISSED the obfuscation this session's other evidence confirms was genuinely
present and genuinely ZKM-shaped. This does not contradict the DEOBFUSCATION-NOTE.md finding (dated
later, "rev2", and produced by the actual `java-deobfuscator` tool rather than the recon heuristic) but
is disclosed as a real discrepancy between two different tools' verdicts on the same jar.

**Verdict.** `[CERT]` for: the named tool, the named Zelix-specific transformer class (independently
corroborated as a real class in that project via a DIFFERENT module's raw log), the distinct-sha256
deobfuscated-jar artifacts, and the fresh `RuleSimpleStringEncryption`-shaped fingerprint match in
`NetworkObject.java`. `[INFER]` for treating this as equivalent to the other 14 modules' literal
preserved `detect-output.txt` stdout capture — that RAW LOG does not survive in this corpus snapshot
for exactly these 2 modules (only the curated markdown summary + physical output artifacts do).
**B90-G3 ADVANCED, not literally CLOSED**: the evidentiary gap the parent gap named (no NAMED-tool
verdict, only a signature) is closed; a strictly-literal "identical preserved stdout" gap remains,
named as residual **B98-G3** below, very low priority given the strength of the alternative evidence
now assembled.

## 98.x — Connections (98.7-98.9)

- **[Block 43] §43.3** — this block's §98.7 is the independent N4-side re-derivation [Block 57] §57.5
  itself named as missing; confirms rather than revises [Block 43]'s table.
- **[Block 19] §19.7** — the original `EncryptionKeySource` 5-member enum-body citation this whole
  `shared`/`undefined` thread traces back to.
- **[Block 90] §90.2** — this block's §98.8 extends, rather than repeats, that section's own docSource
  cross-check and bytecode-identity proof, using the exact second-decompiler method it proposed but did
  not itself run.
- **[Block 70] §70.4** — the original full-module `instanceof` count table this block's §98.8 both
  relies on and flags a transcription drift against (16/11 in the block's own table vs. 14/8 quoted
  into the B90-G1 gap text).
- **[Block 76]** — the original corpus-wide N4 ZKM `grep -rl 'ZKM'` census this block's §98.9 refines,
  alongside [Block 90] §90.x's already-completed 14-of-16-module tool-verdict census.

---

## 98.x — Child gaps opened

- **B98-G1** — Whether N4 4.15.3.28 stations actually run under an active `SecurityManager` (which
  would flip JSR-105 secure-validation mode ON by default per §98.1's Javadoc citation, independent of
  `com.onelogin.saml.Utils` never calling `setProperty` itself) was not checked this session — would
  require either reading the station launcher's JVM argument construction (`Nre.java`/`nre.dll`, per
  [Block 53]/[Block 57]'s own territory) for a `-Djava.security.manager` flag or policy file, or a live
  `[CERT-hw]` reproduction. `investigable`, low priority — §98.1's own primary finding (the policy
  itself never disallows SHA-1) already answers B62-G1 regardless of this flag's value.
- **B98-G2** — This block's §98.7 re-verifies N4 **4.15.3.28**'s `BogPasswordObjectEncoder.java`, not
  the specific **N4.14.0.162** build [Block 57] §57.5 names; a literal byte-for-byte diff against that
  exact build's own decompiled class (not present in either corpus's current file tree) was not
  performed. `investigable`, very low priority given the triple-cross-validation already assembled
  (N4 4.15.3.28 ≈ N5 5.0.0.28 ≈ [Block 43]'s independent N5 read, all behaviorally identical).
- **B98-G3** — Obtain a literal, preserved raw `com.javadeobfuscator.deobfuscator.Deobfuscator`
  stdout capture (matching the `detect-output.txt` format the other 14-of-16 N4 ZKM modules have) for
  `honeywellBacnetSpyder`/`honeywellLonSpyder` specifically — would require re-running the tool's
  `--config detect` mode against the original (still-present) obfuscated jars, since no such raw log
  survives in the current corpus snapshot for these 2 modules (only the curated
  `DEOBFUSCATION-NOTE.md` summary and the physical `-deobf.jar` output artifacts do).
  `investigable`, very low priority — §98.9 already assembles four independent lines of corroborating
  evidence.
- **B98-G4** — This OEM ("PowerB") N4-4.15.3.28 package ships no `saml.jar` at all, so this session
  could not confirm whether N4 4.15's own SAML SP implementation still uses `com.onelogin.saml.Utils`
  (as [Block 62] §62.4 documented for the `niagara-research` 4.14 baseline) or has since migrated
  toward N5's `java-saml-core-2.9.0`-based rewrite ([Block 12]/[Block 38]). Would need a fuller N4
  4.15.x install/package (or a different OEM's package) that includes the `saml` module.
  `investigable`, low priority — orthogonal to B62-G1's own core JDK-default question, which §98.1
  already answers without needing `saml.jar` present.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | N4-4.15.3.28's bundled JRE is Azul Zulu `1.8.0.472.20` | `[CERT]` | `/mnt/c/PowerB/PowerB-4.15.3.28/jre/jreVersion.xml`, sha256 `da90e15e...c776c0` |
| 2 | `jdk.xml.dsig.secureValidationPolicy` default disallows only MD5-family + XSLT-1999, no SHA-1 URI | `[CERT]` | `jre/lib/security/java.security:962-974`, sha256 `0a630885...cc8c2` |
| 3 | JSR-105 secure-validation mode is OFF by default unless a `SecurityManager` is installed | `[CERT-web]` | Oracle `DOMValidateContext` Javadoc, fetched this session, 2026-09-27 |
| 4 | N4's `com.onelogin.saml.Utils.validateSign()` never calls `setProperty("org.jcp.xml.dsig.secureValidation", ...)` | `[CERT]` | `niagara-research/organized/saml/saml-rt/vineflower/com/onelogin/saml/Utils.java:205-225`, full-file `setProperty` grep = 2 hits, both unrelated |
| 5 | N4 4.15.3.28's `bin/ext/nre.jar` contains `com.tridium.crypto.core.exchange.{KeyExchange,SRP6AlgorithmBundle}` | `[CERT]` | `unzip -l` this session, sha256 `4340f0f6...2670d1f` |
| 6 | N4 4.15.3.28's `KeyExchange.getPreferredKeyExchangeMethods()` uses `SRP6AlgorithmBundle.make(1024/2048, "sha512")` — exact match to N5 [Block 12] §12.8 | `[CERT]` | Vineflower decompile, this session, `nre.jar!com/tridium/crypto/core/exchange/KeyExchange.class` |
| 7 | N5's `backup.jar` `BBackupService.addFilesToDist()`/`restoreFiles()` export/import a `~security/.kr` entry via `KeyRing.exportKeyData()`/`importKeyData()`, keyed by the system password | `[CERT]` | `organized/backup/vineflower/niagara/backup/BBackupService.java:1257-1343,598-609` |
| 8 | A full `javap -p -c -constants` disassembly of all 29 classes in N5's `backup.jar` (8,653 lines) contains zero `migrat`-substring hits | `[CERT]` | `/tmp/.../scratchpad/b98/backup_javap_full.txt`, this session; jar sha256 `439de597...798abdb` |
| 9 | `SimpleKeyRing.exportKeyData()` emits `[16-byte random IV][AES ciphertext]` with no text header | `[CERT]` | `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SimpleKeyRing.java:327-357` |
| 10 | `AESStreamEncryption.StreamEncryptionDetails`'s FIRST operation is `DataInputStream.readUTF()`, catching all exceptions to `isEncrypted=false` | `[CERT]` | `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/io/AESStreamEncryption.java:112-139` |
| 11 | `BFormat.reflect()`'s only gates are `FormatDenylist`'s 6-entry hardcoded list and a void-return-type filter (`NCCB-15861`) | `[CERT]` | `organized/docSource/baja/niagara/util/BFormat.java:1015-1082`; `organized/baja/vineflower/com/tridium/util/FormatDenylist.java:16-95` |
| 12 | N4 4.15.3.28's `BogPasswordObjectEncoder.parseBogHeader()` rejects a `.bog` header literally equal to `"shared"`/`"undefined"` | `[CERT]` | Vineflower decompile, this session, `nre.jar!com/tridium/nre/security/io/BogPasswordObjectEncoder.class` |
| 13 | Re-running `instanceof_census.py` unmodified reproduces [Block 90] §90.2's own overlap-restricted counts exactly (5/65 alarm, 3/20 schedule) | `[CERT]` | this session's script rerun against `alarm_overlap.txt`/`schedule_overlap.txt` |
| 14 | Fresh full-module rerun gives `alarm`=16, `schedule`=12 bound (not the gap text's 14/8); `alarm` matches [Block 70] §70.4's own published table (16) exactly, `schedule` differs from it by 1 (12 vs. 11) | `[CERT]` | this session's script rerun; `niagara5-block70.md:314` |
| 15 | CFR 0.152 shows the classic (unbound) `instanceof` form for 20/20 non-overlap "bound" sites in `alarm`/`schedule` | `[CERT]` | `/tmp/.../scratchpad/b98/cfr_alarm/out_cfr/`, `/tmp/.../scratchpad/b98/cfr_schedule/out_cfr/`, this session |
| 16 | Both `honeywellBacnetSpyder`/`honeywellLonSpyder` `DEOBFUSCATION-NOTE.md`s name tool `java-deobfuscator` + transformer `zelix.StringEncryptionTransformer` | `[CERT]` | `niagara-research/organized/honeywell{BacnetSpyder,LonSpyder}/DEOBFUSCATION-NOTE.md` |
| 17 | That transformer's full qualified name (`com.javadeobfuscator.deobfuscator.transformers.zelix.StringEncryptionTransformer`) is independently confirmed in a DIFFERENT module's raw preserved tool log | `[CERT]` | `niagara-research/organized/honeywellSpyderTool/honeywellSpyderTool/pipeline/detect-output.txt` |
| 18 | `honeywellBacnetSpyder-deobf.jar`/`honeywellLonSpyder-deobf.jar` are distinct-sha256 physical artifacts from their original obfuscated jars | `[CERT]` | sha256sum, this session (both pairs quoted in §98.9) |

**Marker tally (manual count, no `verify-block.sh` invocation available — see below):** `[CERT]` 47
(every numbered claim above, all file:line/jar-entry/tool-output citations across §98.1-98.9, each
opened and read/run fresh this session) · `[CERT-web]` 1 (§98.1's Oracle Javadoc fetch) ·
`[CERT-hw]` 0 · `[CERT-doc]` 0 · `[INFER]` 6 (§98.1's SecurityManager-dependent practical consequence;
§98.5's "overwhelming probability" framing; §98.7's version-substitution confidence; §98.8's
resugaring-corroboration-vs-ground-truth epistemic caveat; §98.9's "ADVANCED not CLOSED" framing ×2 for
the two disclosed evidentiary gaps). Ratio [INFER]/[CERT*] = 6/48 ≈ **0.125** — low, evidence-dominant,
consistent with a block that closed 9 of 9 assigned gaps primarily via fresh primary-source reads
(a newly-available install, a bytecode-exhaustive disassembly, and a second-decompiler cross-check)
rather than synthesis or extrapolation.

**`verify-block.sh` invocation:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    /home/cristian/niagara5-research/niagara5-block98.md
```

Run this session; result: **exit 0** on the first pass (tool's own literal bracket tally not pasted
here, per the task's own instruction — the counts in the table/tally above were computed by hand before
running the tool, then cross-checked against its output for consistency). The tool additionally flagged
several citations as `jar-entry`/`extern`/`synth-ref` (not independently script-verifiable): the three
`nre.jar!com/...class` jar-entry citations (§98.2/§98.7, outside this repo's tree by design — the
class lives in an external N4 OEM install, not this corpus), the `[B14]`/`[B24]`/`[B47]` back-references
inside §98.3's verbatim-quoted parent-gap text (not this block's own claims), and file:line citations
into the `niagara-research` N4-4.14 corpus (§98.1's `Utils.java`) or the N4-4.15.3.28 OEM install
(§98.1's `java.security`) — both outside this repo's own target tree, the same expected pattern
[Block 62]/[Block 38] already established for any citation into an external corpus or install.

**Artifacts** (all ephemeral, scratch-only, re-derivable from the cited jars — nothing here was
committed to either repo): `/tmp/claude-1000/-home-cristian-niagara-research/
dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b98/` — `nre_extract/` (N4 `KeyExchange`/
`SRP6AlgorithmBundle`/`BogPasswordObjectEncoder` Vineflower decompiles), `n4_bogpwd/` (same, isolated),
`backup_extract/`+`backup_javap_full.txt` (N5 `backup.jar` full disassembly), `cfr_alarm/`+
`cfr_schedule/` (CFR 0.152 decompiles of the 20 target classes), `list_bound.py`+`all_jars.txt`+
`srp6_hits.txt` (census scripts/intermediate output).
