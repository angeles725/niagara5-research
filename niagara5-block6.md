# Block 6 — N5 licensing layer: ECDSA-P256 replaces the DSA-1024 master key, `algorithm`/`licenseId` become mandatory license-XML attributes, a `~~` config-home storage tier appears, and the `com.tridium.sys.license.subscription` package is NOT new to N5

> Research of the **Java licensing/entitlement layer in N5 5.0.0.28's `baja.jar`**: the
> `com.tridium.sys.license` / `com.tridium.sys.license.dom` / `com.tridium.sys.license.subscription`
> packages and the public `niagara.license` API (N4: `javax.baja.license`), compared class-by-class
> against the same packages already decompiled from N4's `baja.jar` in the `niagara-research` corpus.
> Covers: package/type inventory delta, the subscription/entitlement model, the master-key signature
> algorithm, license/certificate XML-format deltas, the HostId directory-name format, new license
> storage path tier, and concrete licensing call sites that switched from `AccessController` to the
> N5 `SecurityUtil` (the [Block 3] `SecurityAgent` replacement for `SecurityManager`). Does **not**
> cover: `com.tridium.nre.subscription.*` (`SubscriptionLicenseUtil`, `RetrieveEntitlements`,
> `EntitlementApi`, `LicenseValidator`) or `com.tridium.nre.util.LicenseMode` — those live in
> `bin/ext/nre.jar`, not `baja.jar` (→ child gap B6-G1); the native `dsfspi`/`nverify` trust layer
> ([B126] in the N4 corpus, not re-probed here since no N5 native binary was opened this session);
> or live/on-station verification of any of these code paths (read-only static block).
>
> Subject version: N5 **5.0.0.28** (Beta), `baja.jar` at
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` (unversioned by git; jar
> `mtime` 2026‑09‑11 22:39 serves as the version stamp per METHODOLOGY §3 "no git, no problem"). N4
> baseline: the `niagara-research` corpus's own `baja.jar` decompile at
> `niagara-research/organized/baja/baja/vineflower/**` (per that corpus's B41/B322, sourced from an
> iC‑Niagara 4.10.9.14‑family build, sha256 `8f8351b2…` for the cross‑checked real build — see B322).
> Both installs are read‑only, unversioned trees.
>
> Sources:
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` → `com/tridium/sys/license/**`,
>   `com/tridium/sys/license/dom/**`, `com/tridium/sys/license/subscription/**`,
>   `com/tridium/sys/metrics/BISubLicenseable.class`, `niagara/license/**`,
>   `niagara/sys/BAbstractService$LicenseLimit.class` (40 class-file entries extracted; 28 top-level
>   `.java` recovered by Vineflower — inner/nested classes are embedded in their outer file's source,
>   not emitted as separate `.java`, which accounts for the 40→28 delta).
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/security/` — `certificates/` and
>   `licenses/{conf,db,inbox}` directory listings (names only; no `.license`/`.certificate` file
>   content read beyond the single installed `Tridium.certificate`'s *name*, per SECRETS DISCIPLINE).
> - `niagara-research/organized/baja/baja/vineflower/{javax/baja/license,com/tridium/sys/license,
>   com/tridium/sys/metrics}/**` — N4 REMITTANCE baseline (already decompiled in that corpus; read,
>   not re-derived) — `python3 niagara-research/tools/corpus-nav.py find license|"license signature"|subscription`
>   located it plus blocks B41, B126, B316, B322, B442, B477, B478, B479, B480, B481, B483, B487 and
>   `niagara-research/docs/niagara-licensing.md` (a synthesis doc) as the N4 remittances cited below.
>
> Method: `unzip -l`/`unzip -oq` extracted the 40 class entries listed above into a scratch dir; Vineflower
> 1.12.0 (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar`, run by
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`, JDK 26.0.2.1) decompiled them whole into
> `/tmp/claude-1000/n5b6/out/` (scratch, not archived in the corpus; re-derivable from the jar cited).
> Every N5 class was `diff`-ed file-by-file against its exact N4 namesake in the `niagara-research`
> corpus decompile; the master-public-key byte array's ASN.1 structure was read by eye against known
> X.509 `SubjectPublicKeyInfo` OID encodings (`2A 86 48 CE 3D …` = `1.2.840.10045.*`, id‑ecPublicKey /
> secp256r1) — no external ASN.1 tool was used, so the OID decode is `[CERT]` on the byte sequence and
> `[INFER]` on the "= P‑256" curve-name reading of that OID (standard, but not tool-verified this
> session).
> Markers: `[CERT]` local primary (`file:line` into the Vineflower output, or a `niagara-research`
> `file:line`/block citation for the N4 side) · `[INFER]` deduction. No `[CERT-doc]`/`[CERT-web]` this
> block (no manual/web consulted).
>
> Security/licensing layer. Connects [Block 1] (module-part collapse — §6.2's `getModulePartName()` →
> `getModuleName()` rename is a licensing-side echo of that collapse), [Block 3] (`SecurityAgent`
> ByteBuddy replacement for `SecurityManager` — §6.8 gives it two concrete `AccessController`→
> `SecurityUtil.doPrivileged` call sites), and, across corpora, `niagara-research` B41/B322 (N4 Java
> licensing baseline + the real-build DSA/ECDSA delta this block resolves), B126 (native DSA‑1024/SHA‑1
> signature scheme + HostId format, §6.7's N4 comparator), B479–B481/B483/B487 (N4's own
> subscription/entitlement documentation — §6.2's correction source).
>
> **Type:** standard

---

## 6.1 — Package/type inventory: zero classes added or removed; two packages renamed `[CERT]`

Every one of the 28 top-level classes (40 class-file entries incl. 12 inner/nested classes) present
in N5's `com.tridium.sys.license*`/`com.tridium.sys.metrics.BISubLicenseable`/`niagara.license` surface
has an **exact same-named counterpart** in the N4 corpus decompile. No class was added; no class was
removed. `[CERT]` (file-by-file `diff` of both trees' listings).

| Package | N4 (`niagara-research`) | N5 (`baja.jar` 5.0.0.28) | Delta |
|---|---|---|---|
| license public API | `javax.baja.license` (7 files: `BILicensed`, `Feature`, `FeatureLicenseExpiredException`, `FeatureNotLicensedException`, `LicenseDatabaseException`, `LicenseException`, `LicenseManager`) | `niagara.license` (same 7 files, identical bodies) | **package renamed** `javax.baja.license` → `niagara.license` |
| license impl | `com.tridium.sys.license` (10 files) | `com.tridium.sys.license` (same 10 files) | unchanged package, internal deltas (§6.3-§6.6) |
| license DOM | `com.tridium.sys.license.dom` (8 files) | `com.tridium.sys.license.dom` (same 8 files) | unchanged package, internal deltas (§6.6) |
| subscription | `com.tridium.sys.license.subscription` (3 files: `EntitlementCheck`, `KeyRotationCheck`, `SubscriptionLicenseManager`) | `com.tridium.sys.license.subscription` (same 3 files) | **unchanged package — see correction §6.2** |
| sub-license metering | `com.tridium.sys.metrics.BISubLicenseable` | `com.tridium.sys.metrics.BISubLicenseable` | unchanged package, identical logic (one added `@Generated` marker annotation on `TYPE`) |
| service license limit | `javax.baja.sys.BAbstractService$LicenseLimit` (nested in `BAbstractService`) | `niagara.sys.BAbstractService$LicenseLimit` | package renamed with the rest of `javax.baja.sys`→`niagara.sys` (same 3 fields: `key`,`limit`,`used`) |

The only structural change at the package/type level is the **`javax.baja.*` → `niagara.*` rename**
already established for the core API surface in other N5 blocks (this block's own evidence:
`niagara.license.*`, `niagara.sys.*`, `niagara.file.*`, `niagara.xml.*`, `niagara.util.*`,
`niagara.nre.util.*`, `niagara.nre.annotations.*` imports throughout §6.3-§6.9's cited files)
`[CERT]` — consistent with, and now licensing-layer evidence for, the rename N5-G5 names.

## 6.2 — Correction: `com.tridium.sys.license.subscription` is not a new N5 package `[CERT]`

The gap this block was opened to close (**N5-G8**) is framed around "the NEW package
`com/tridium/sys/license/subscription` in N5 baja.jar". That framing is **incorrect**: the package,
with the same 3 classes (`EntitlementCheck`, `KeyRotationCheck`, `SubscriptionLicenseManager`), already
exists in the N4 corpus's own `baja.jar` decompile —
`niagara-research/organized/baja/baja/vineflower/com/tridium/sys/license/subscription/{EntitlementCheck,KeyRotationCheck,SubscriptionLicenseManager}.java`
`[CERT]` — and is extensively documented there: `niagara-research` B480 ("Subscription onboarding and
the trust model…"), B481 ("Who watches a license change/tamper…"), B483, B487, and synthesized in
`niagara-research/docs/niagara-licensing.md` §6.4 ("SERVER — `SubscriptionLicenseManager` (phones
home, fails closed)"). `[CERT]`

What **is** new/changed in N5 is not the package's existence but its internals (§6.9) and its
companion package `com.tridium.nre.subscription` (`SubscriptionLicenseUtil`, `RetrieveEntitlements`,
`EntitlementApi`) moving/staying in `nre.jar` rather than `baja.jar` — out of this block's jar scope,
named as **B6-G1**.

## 6.3 — Master-key signature algorithm: DSA‑1024 → sole ECDSA P‑256 key `[CERT]`

N4's `LicenseUtil` embeds a DSA public key (`masterPublicKeyData`, decoding to SubjectPublicKeyInfo
OID `1.2.840.10040.4.1` = id‑dsa, 1024‑bit prime — cross-confirmed against the native trust anchor in
the N4 corpus's B126 §126.6, `[CERT]` via `niagara-research` `LicenseUtil.java:32` /
`CertificateFile.java` in that corpus) plus a second, optional ECDSA key
(`version2PublicKeyData`/`getVersion2PublicKey()`) selected only when a license/cert's `version`
attribute routes to it (`niagara-research/organized/…/LicenseUtil.java:477,749-753`).

N5's `LicenseUtil` **replaces this with a single embedded key, decoded as `"ECDSA"` unconditionally**,
and a *second*, differently-purposed key slot for subscription mode:

| | N4 | N5 |
|---|---|---|
| Embedded key field | `masterPublicKeyData` (DSA, 1024‑bit) | `MASTER_PUBLIC_KEY_DATA` — `Base64`/DER decodes to X.509 `SubjectPublicKeyInfo`: `30 59 30 13 06 07 2A 86 48 CE 3D 02 01 06 08 2A 86 48 CE 3D 03 01 07 03 42 00 04 …` = alg OID `1.2.840.10045.2.1` (id‑ecPublicKey) + curve OID `1.2.840.10045.3.1.7` (secp256r1/NIST P‑256), 91 bytes total `[CERT]` `LicenseUtil.java:41-133` (structure only — no key byte cited beyond the fixed ASN.1 header, per SECRETS DISCIPLINE) |
| Decode algorithm string | `"DSA"` (`toPublicKey(data)` default, `LicenseUtil.java:731-733` in N4) | `"ECDSA"` literal at both call sites `[CERT]` `LicenseUtil.java:420,430,432` |
| Second key | `version2PublicKeyData` (ECDSA, cert‑`version`‑gated) `getVersion2PublicKey()` | `SUBSCRIPTION_QA_PUBLIC_KEY_DATA` — same 91‑byte EC‑P‑256 SPKI structure `[CERT]` `LicenseUtil.java:134-219` — selected by `getSubscriptionPublicKey()` (§6.9), **not** by a license/cert version attribute |
| Deprecated DSA convenience setter | `VendorCertificate.setPublicKey(String)` `@Deprecated`, hardcoded `"DSA"` (`niagara-research/…/VendorCertificate.java:129-131`) | **removed** — no such overload in N5's `VendorCertificate.java` `[CERT]` (diff against N4 shows the method absent) |
| Literal `"DSA"` string anywhere in the license tree | throughout (`toPublicKey(data)`, `verify(data,sig,publicKeyData)` default) | **one residual occurrence**: `VendorCertificate.java:123` `publicKeyElem.get("algorthm", "DSA")` — a fallback default string used only if a certificate XML's `<publicKey>` carries neither the correctly-spelled `algorithm` nor the legacy-typo `algorthm` attribute; not exercised by the installed `Tridium.certificate` (its `algorithm`/`algorthm` attribute was not read this session — content not opened, per SECRETS DISCIPLINE) |
| `SHA1`/`SHA-1` literal anywhere in the license tree | present (native/doc side, B126 §126.1) | **zero hits**, `grep -r "SHA1\|SHA-1" out/` `[CERT]` |

`grep -rn "\"DSA\"\|DSA1024\|DSA-1024\|\bDSA\b" /tmp/claude-1000/n5b6/out/` returns exactly the one
`VendorCertificate.java:123` default-string hit above; `grep -rn "SHA1\|SHA-1"` returns zero. `[CERT]`

**Reading the delta**: N5 does not merely add ECDSA alongside DSA (as N4's dual-key design already
supported by cert `version`) — it **retires the DSA master key entirely** and repurposes the "second
key" slot from a cert-version-routed legacy/rollover key into an **environment-routed** (QA vs
Production) subscription-signing key (§6.9). `[INFER]` on "retires" (no DSA-decoding call site survives
in the reachable code this session read; a residual DSA-shaped legacy `.license`/`.certificate` file
would now fail at `KeyFactory.getInstance("ECDSA")`/parse time, not at signature-mismatch time — not
observed live, so this is a static-code inference, not a live-verified failure mode).

## 6.4 — Signature verification: the `algorithm` attribute becomes mandatory for licenses `[CERT]`

N4's `LicenseFile.load(licMan, root)` had two verify paths depending on whether the `<signature>`
element carried an `algorithm` attribute: `algorithm == null` → `LicenseUtil.verify(xml, sig,
publicKey)` (implicit DSA, via `PublicKey.getAlgorithm()`); `algorithm != null` → the explicit
4‑arg `verify(xml, sig, publicKey, signatureAlgorithm)` (`niagara-research/…/LicenseFile.java:174-186`,
paraphrased from that corpus's own decompile, not re-quoted verbatim here).

N5's `LicenseFile.load(NLicenseManager, XElem)` **removes the implicit branch entirely**:

```
String signatureAlgorithm = sigElem.get("algorithm", null);
if (signatureAlgorithm == null) {
   this.error = "Missing license signature algorithm";
} else {
   this.licenseId = root.get("licenseId", null);
   if (this.licenseId == null) {
      … this.error = "Missing licenseId";
   } else if (!LicenseUtil.verify(xml, sig, publicKey, signatureAlgorithm)) {
      this.error = "Invalid " + signatureAlgorithm + " signature";
   } else { … loadFeature … }
}
```
`[CERT]` `LicenseFile.java:171-192`.

Consequence `[INFER]`: an N4-era `.license` file whose `<signature>` element has no `algorithm`
attribute (the legacy implicit-DSA form N4 still accepted) will fail to load on N5 with
`"Missing license signature algorithm"` — a **license-format forward-compatibility break**, not
independently live-verified this session (no live N5 station probed).

`CertificateFile.java` (certificate, not license, loading) still contains an `algorithm == null`
branch (`CertificateFile.java:76-80`), but it now calls the 3‑arg `LicenseUtil.verify(xml, sig, new
Version(versionString))`, which internally throws `LicenseException` whenever
`version.isBefore(DEFAULT_CERT_VERSION="5.0")` is false *and* the algorithm is null (`LicenseUtil.java:394-401`,
§6.6) — i.e. for any N5-versioned certificate, this branch is dead-but-present: it always throws before
returning a boolean, caught by the outer `catch (Throwable)` as a generic parse error rather than a clean
`"Invalid signature"` message. `[CERT]` on the code path; `[INFER]` on "dead-but-present" (not exercised
live).

## 6.5 — License XML format: new mandatory `licenseId` attribute `[CERT]`

`LicenseFile.java:173-178` reads `root.get("licenseId", null)` from the `<license>` root element and
**fails the license** (`"Missing licenseId"`, clearing both `maintenanceExpiration` and
`unreleasedSwAccessExpiration`) if absent — a brand-new required attribute; N4's `LicenseFile` has no
`licenseId` field or read at all (absent from `niagara-research/…/LicenseFile.java`, confirmed by
absence-check: `grep licenseId` on that file returns nothing, and the corresponding N4 corpus blocks
(B126 §126.6, B442, B479) name only `vendor`, `expiration`, `hostId`, `version`, `generated` as
`<license>` attributes). `[CERT — negative existence checked against the N4 file actually opened]`.

`NLicenseManager` grew a matching accessor, `getLicenseId()` → `this.getLicenseByVendor("tridium").licenseId`
(`NLicenseManager.java:173-175`), and `LicenseFile.toString()`'s valid-license format string gained the
id: `getLicenseName() + " (" + licenseId + ") <" + vendor + ">…"` (`LicenseFile.java:245`) vs N4's
`getLicenseName() + " <" + vendor + ">…"` (no id segment). `[CERT]`

All other `<license>`/`<certificate>`/`<feature>`/`<signature>`/`<publicKey>` element and attribute
NAMES read this session (`vendor`, `expiration`, `generated`, `hostId`, `version`,
`maintenanceExpiration`, `unreleasedSwAccessExpiration`, `feature name=`/`expiration=`,
`signature algorithm=`, `publicKey algorithm=`/legacy-typo `algorthm=`) are **unchanged** between N4
and N5 — confirmed by diffing `VendorLicense.java`/`VendorCertificate.java`'s `parse()`/`save()`
methods, whose only deltas are the package-rename imports and Java-style refactors (early-return
instead of `if/else`, try-with-resources) with zero attribute-name changes. `[CERT]`

## 6.6 — Tridium module/license version gate: floor bumped `"4.0"` → `"5.0"` `[CERT]`

`LicenseFile.load()`'s Tridium-vendor branch computes a `curVer` to compare against the license's own
`version` attribute. Every literal `new Version("4.0")` fallback in the N4 source
(`niagara-research/…/LicenseFile.java:144,153,156,263` — three occurrences the N4 file uses as its
"current baseline version" floor) is **`new Version("5.0")`** at the identical call sites in N5
(`LicenseFile.java:141,148,171,258` — offsets shifted by the same refactor noted in §6.4). `[CERT]`
`NLicenseManager` also gained a `private static final String N5_LICENSE_VERSION = "5.0";` constant
(`NLicenseManager.java:29`, declared but its only read site is inside string-building not independently
traced this session — noted, not fully chased).

Separately, `LicenseUtil` gained a class-level `DEFAULT_CERT_VERSION = new Version("5.0")`
(`LicenseUtil.java:40`) used by the `verify(data,sig,Version,signatureAlgorithm)` overload
(§6.3/§6.4) to require version ≥ 5.0 before accepting an explicit `signatureAlgorithm` argument at all
— `version.isBefore(DEFAULT_CERT_VERSION)` throws `LicenseException` (`LicenseUtil.java:395-399`).
`[CERT]`

And `com.tridium.sys.license.dom.LicenseDatabase` gained two version *sentinels*,
`Version.N5`/`Version.N4` (referenced, not decompiled here — they live in `niagara.util.Version` itself,
out of this block's extracted class set), used by `getVersionSpecificFilePath()` (§6.7) to branch
storage-path resolution purely on `Version.compareTo()` against these constants
(`LicenseDatabase.java:406-411`). `[CERT]` on the call sites; `[INFER]` that `Version.N5`/`Version.N4`
are literal `"5.0"`/`"4.0"`-equivalent sentinels (not independently decompiled).

## 6.7 — New license storage path tier: `~~security/licenses` (config-home) for N5 `[CERT]`

N4's `LicenseDatabase` resolves perpetual/subscription license directories to exactly two tiers keyed
off `NiagaraFiles.isNiagaraHomeReadonly()`: `!security/licenses` (writable Niagara-home) or
`~security/licenses` (read-only home) — and the subscription twin under `security/subscription/licenses`
(`niagara-research` B479 §479.1, `SystemFilePaths.java:123-135`/`LicenseInfo.java:213-279` as cited
there; corroborated in N4's own `LicenseDatabase.getPerpetualLicenseDirPath(boolean)` /
`getSubscriptionLicensesDirPath(boolean)`).

N5's `LicenseDatabase` adds a **third, `~~`-prefixed "config-home" tier** and makes it the
version-≥5.0 default, demoting the old `!`/`~` split to the version-<5.0 (N4-compat) path:

```
private static final FilePath PERPETUAL_LICENSE_DEFAULT_PATH   = new FilePath("!security/licenses");
private static final FilePath PERPETUAL_LICENSE_USER_PATH      = new FilePath("~security/licenses");
private static final FilePath PERPETUAL_LICENSE_CONFIG_PATH    = new FilePath("~~security/licenses");
private static final FilePath SUBSCRIPTION_LICENSE_DEFAULT_PATH = new FilePath("!security/subscription/licenses");
private static final FilePath SUBSCRIPTION_LICENSE_USER_PATH    = new FilePath("~security/subscription/licenses");
private static final FilePath SUBSCRIPTION_LICENSE_CONFIG_PATH  = new FilePath("~~security/subscription/licenses");
…
private static FilePath getVersionSpecificFilePath(Version version, boolean isNiagaraHomeReadonly,
      FilePath configHomePath, FilePath userHomePath, FilePath niagaraHomePath) {
   if (version.compareTo(Version.N5) >= 0) {
      return configHomePath;
   } else if (version.compareTo(Version.N4) >= 0) {
      return isNiagaraHomeReadonly ? userHomePath : niagaraHomePath;
   } else {
      throw new IllegalArgumentException(…);
   }
}
```
`[CERT]` `LicenseDatabase.java:31-37,363-411`. `com.tridium.sys.license.Brand` picked up the same
`~~`-tier convention for its own config file: `CONFIG_HOME_BRAND_PROPS_PATH = new
FilePath("~~etc/brand.properties")` (`Brand.java:14`, absent from the N4 `Brand.java`). `[CERT]`

**Live-install corroboration** `[CERT]`: the actual N5 5.0.0.28 `config/5.0.0.28/security/` tree holds
`licenses/{conf,db,inbox}` and `certificates/Tridium.certificate` (name only). `db/`/`inbox/` match
N4's documented `LocalLicenseDatabase.init()`/`exportNewLicenses()` layout (`niagara-research` B479
§479.3: "`security/licenses/inbox`… `<perpetualLicenseDir>/db/<hostId>/<name>.license`"). The **`conf/`
subdirectory has no N4 precedent** in the corpus searched (`grep -rn "security/licenses/conf"` across
the whole `niagara-research` corpus returns zero hits) and is not explained by any method this session
read in `LicenseDatabase.java` (which creates `db` under the *perpetual* dir root, not `conf` —
`loadLicenseDbRoot()`, `LicenseDatabase.java:418-420`). `conf/` is left as an **open, unexplained
on-disk artifact** — plausibly the physical target of the new `~~` config-home tier resolved by
`FileSystem`/`NiagaraFiles` machinery this block did not decompile (out of `com.tridium.sys.license*`
scope) — named as **B6-G2**, not asserted as `[CERT]`.

## 6.8 — HostId directory-name format: longer, differently-prefixed (structure only) `[CERT]`

**SECRETS DISCIPLINE — no literal HostId value is reproduced below; only its shape.** The single entry
under the live N5 install's `security/licenses/conf/` directory is named after a HostId-shaped string:
prefix `WINN5-` followed by **8 groups of 4 hex characters** (32 hex digits total, hyphen-separated).
`[CERT]` (directory listing, name-only; `find … -maxdepth 3`).

N4's documented soft HostId format (`niagara-research` B126 §126.6, `Win‑` prefix + **4 groups of 4 hex
characters**, i.e. 16 hex digits, derived from the native `getHostId0`/`GetVolumeInformation` path) is
shorter and uses a different, non‑numbered prefix (`Win-` vs `WINN5-`). `[CERT]` on the N4 shape
(cited from that block, not re-derived); `[CERT]` on the N5 shape (this session's own directory
listing). The `N5` token embedded in the N5 prefix plausibly encodes the major version into the HostId
namespace itself (so an N4 and an N5 install on the same physical machine mint textually-distinguishable
HostIds) — `[INFER]`, not confirmed against any HostId-generation code (`Nre.getHostId0`/native path
not decompiled this session — that's [B125]/[B126]'s native-layer territory in the N4 corpus; no N5
native binary was opened here).

## 6.9 — `SecurityManager` replacement reaches licensing: two concrete call sites `[CERT]`

[Block 3] documented N5's platform-wide replacement of the removed JDK `SecurityManager` with a
ByteBuddy `-javaagent` (`SecurityAgent`) routed through Niagara's own `PermissionManager`, without
yet tracing a caller inside `baja.jar` itself. This block supplies two:

- `NLicenseManager.load()`: N4 wraps the module lookup in
  `AccessController.doPrivileged((PrivilegedAction<ModuleManager>)(() -> Nre.getModuleManager()))
  .loadModule("baja", RuntimeProfile.rt)` (`niagara-research/…/LicenseFile.java:140-141`, actually the
  call site is in `LicenseFile`, not `NLicenseManager` — corrected here from the initial diff read).
  N5 replaces it with a plain, unprivileged
  `Nre.getModuleManager().loadModule("baja")` (`LicenseFile.java:135`, one-arg overload — no
  `RuntimeProfile` parameter, consistent with [Block 1]'s single-profile-per-jar N5 packaging). `[CERT]`
- `SubscriptionLicenseManager.regenerateNreId()`/key-rotation path: N4's
  `AccessController.doPrivileged((PrivilegedAction<Void>)(() -> {…}))` becomes N5's
  `com.tridium.nre.util.SecurityUtil.doPrivileged(() -> {…; return null;})`, at two call sites
  (`SubscriptionLicenseManager.java:407,592`) — one of which now wraps `cert.load(null)` (certificate
  loading) that was **not** privileged-wrapped at all in N4. `[CERT]` `diff` of both files (§ evidence
  block above, "SecurityUtil.doPrivileged" hits).

`SecurityUtil` itself (`com.tridium.nre.util.SecurityUtil`) was not decompiled this session — it is
imported, not defined, in this block's class set (out of `baja.jar`'s license packages; likely `nre.jar`
alongside [Block 3]'s `SecurityAgent` — **B6-G1** covers tracing it).

## 6.10 — New license-gated enforcement points inside `baja.jar` `[CERT]`

Two license/feature checks exist in N5's `com.tridium.sys.license` that have **no N4 counterpart** in
this package (absence checked by `grep` against the N4 files actually opened, not inferred):

- **`LicenseUtil.checkJreFeature()`** (`LicenseUtil.java:267-289`): on a Tridium-vendor host
  (`isTridiumHost()`, `Nre.getHostVendor()`), calls `Sys.getLicenseManager().checkFeature("tridium",
  "zulu25")` (`ZULU25_FEATURE` constant, `LicenseUtil.java:37`) and compares the current Niagara
  `Version` against the feature's `minVersion` facet (default `"5.0"`), throwing
  `FeatureNotLicensedException` if the running Niagara version is older than what the licensed `zulu25`
  feature permits. This is a **license check gating the bundled Azul Zulu JRE 25** ([Block 3]'s JRE
  migration) — a new licensable capability with no N4 equivalent (N4 shipped Java 8, no JRE feature
  gate in this package). `[CERT]` on the code; `[INFER]` on "no N4 equivalent" (absence checked only
  in this package, not the whole N4 corpus).
- **`NLicenseManager.checkDeveloperLicense()`/`isDeveloperLicense()`** (`NLicenseManager.java:35,259,265-278`):
  called from `postInit()`, tries `Sys.getLicenseManager().checkFeature("tridium", "developer")` and
  caches the boolean result on the manager itself, exposed via `isDeveloperLicense()`. N4's
  `NLicenseManager` has no `isDeveloperLicense` field, no `checkDeveloperLicense()` method, and no
  `"developer"`-feature check anywhere in the file (confirmed by reading N4's `postInit()`, which only
  calls `this.load()` and swaps the spy-manager page — `niagara-research/…/NLicenseManager.java:295-303`).
  `[CERT]` — this is a new, cached, station-startup-time developer-license gate.

Both are **new enforcement points added to N5's licensing layer itself**; a fuller enumeration of every
*caller* of `LicenseManager.checkFeature()`/`getFeature()` across the rest of `baja.jar` (outside the
license package) was not attempted this session — named **B6-G3**.

## 6.11 — `SubscriptionLicenseManager` internal deltas (package unchanged, behavior changed) `[CERT]`

Beyond the master-key/verify changes already covered (§6.3-§6.4), `SubscriptionLicenseManager.java`
diffs from its N4 namesake in:

- **New interface**: `public final class SubscriptionLicenseManager extends NLicenseManager implements
  LicenseValidator` (`SubscriptionLicenseManager.java:56`) — `LicenseValidator` is
  `com.tridium.nre.subscription.LicenseValidator`, imported but not defined in this class set (→ B6-G1).
  It adds one method, `validateLicenseSignature(XElem, File)`, that simply delegates to the existing
  `isLicenseSignatureValid(XElem, File)` (`:358-360`) — exposing the manager as an injectable validator
  to whatever `nre.jar`-side caller now constructs it (`RetrieveEntitlements`'s constructor gained a
  second `this` argument at all three of its call sites, `:138,257,262,345` vs N4's single-arg
  constructor calls). `[CERT]`
- **JSON library swap**: `import com.tridium.json.JSONObject;` (N4) → `import org.json.JSONObject;`
  (N5) `[CERT]` (import-line diff only; no behavioral difference traced in this file beyond the import).
- **Testability hook**: `private static IntConsumer exitConsumer = System::exit;` (`:74`), and `exit()`
  now calls `exitConsumer.accept(-3)` (`:242`) instead of N4's direct `System.exit(-3)` — a seam that
  lets a test harness intercept the fatal-exit path. `[CERT]`
- **Failure-counter reset**: after a successful periodic entitlement check, N5 explicitly resets
  `this.periodicCheckFailureCount = 0` (`:312-314`) — logic absent from the N4 method body (N4 never
  zeroes the counter back out in the success branch it decompiles to). `[CERT]`
- `EntitlementCheck` (the `Runnable` scheduled task) gained a static `Instant lastRunInstant` field and
  `getLastRunInstant()` accessor (`EntitlementCheck.java:6-18`, N5-only) — a small observability
  addition to the existing 6‑hour check-in cadence N4 already documents (`niagara-research` B480/B481:
  `validCheckFreq` default 6h + jitter). `[CERT]`
- `KeyRotationCheck.java` is **byte-for-byte logic-identical** to N4's (only the package-rename imports
  differ, and this file has none to rename) `[CERT]` — the 90-day rotation cadence N4 documents (B480
  §…, B481 §481.2) is not contradicted or changed by anything read this session.

## 6.12 — Measure counts `[CERT]`

| Measure | Count |
|---|---|
| Class-file entries extracted from N5 `baja.jar` (license+subscription+metrics+niagara.license+LicenseLimit) | 40 |
| Top-level `.java` files Vineflower emitted (inner/nested classes embedded, not separate) | 28 |
| N4-side comparator files opened (`niagara-research` corpus decompile, same scope) | 26 (7 `javax.baja.license` + 10 `com.tridium.sys.license` + 8 `dom` + 3 `subscription`, minus the 2 files N5 renamed package for = still 1:1 by simple name) |
| Total N5 `.java` lines (this block's extracted set) | 4,549 |
| Total N4 `.java` lines (same class set, N4 corpus) | 4,754 |
| Classes added in N5 vs N4 (by simple name) | 0 |
| Classes removed in N5 vs N4 (by simple name) | 0 |
| Packages renamed | 2 (`javax.baja.license`→`niagara.license`; `javax.baja.sys`→`niagara.sys` for the one nested class) |
| Master public-key algorithm | DSA‑1024 (N4) → ECDSA P‑256 sole key (N5) |
| New required `<license>` XML attribute | `licenseId` |
| New license storage path tier | `~~security/licenses` / `~~security/subscription/licenses` (config-home, N5-only) |
| N4 remittance blocks read (not re-derived) | 12 (B41, B126, B316, B322, B442, B477, B478, B479, B480, B481, B483, B487) + `docs/niagara-licensing.md` |
| Child gaps opened | 3 (B6-G1, B6-G2, B6-G3) |

**Self-verification.** `toolbelt/verify-block.sh` targets the `niagara-research`-kit corpus layout
(`RESEARCH-STATE*.md` at the corpus root) and was run against this file from the kit; its
`[CERT]`/`[INFER]` scanner reports by regex match on marker tokens, independent of corpus wiring:

```
$ grep -o '\[CERT\]' /home/cristian/niagara5-research/niagara5-block6.md | wc -l
      53
$ grep -o '\[INFER\]' /home/cristian/niagara5-research/niagara5-block6.md | wc -l
      11
```
Adjusted ratio `[INFER]`/`[CERT]` ≈ **0.21** — low, consistent with an evidence-dominant block: the
vast majority of claims are direct `diff`/`grep`/byte-structure reads of two decompiled trees, with
`[INFER]` reserved for (a) the OID→"P‑256" curve-name reading, (b) functional consequences of a code
path not exercised live (e.g. "old license files will fail to load"), and (c) the unexplained `conf/`
directory's likely cause. Token check: every load-bearing `file:line` citation above was re-`grep`ped
against the actual Vineflower output in `/tmp/claude-1000/n5b6/out/` or the `niagara-research` corpus
file it names, immediately before or after being written into this block (see the Bash transcript this
session; no citation was hand-recalled). `licenseId`, `MASTER_PUBLIC_KEY_DATA`, `"ECDSA"`,
`getSubscriptionPublicKey`, `PERPETUAL_LICENSE_CONFIG_PATH`, `Version.N5`, `checkJreFeature`,
`isDeveloperLicense`, `SecurityUtil.doPrivileged`, `exitConsumer`, `LicenseValidator` — all confirmed
present by `grep -n` against the decompiled source before citing.

## 6.13 — Open questions / unresolved artifacts

- **[C1]** The `security/licenses/conf/<hostid-shaped-name>/` directory on the live N5 install has no
  corresponding code path in anything this block decompiled (`LicenseDatabase` creates `db/`, not
  `conf/`, under the perpetual license root) `[CERT]` on the absence-in-what-was-read, vs the directory
  demonstrably existing on disk `[CERT]` — unresolved; not pushed to a corpus `CONTRADICTIONS.md` (this
  corpus has none yet) but named **B6-G2** for a follow-up decompile of the `FileSystem`/`NiagaraFiles`
  `~~`-scheme resolver.

## 6.14 — Connections

- **[Block 1]** — the `javax.baja.*`→`niagara.*` rename and single-profile-per-jar module packaging
  this block finds in the licensing package (`getModulePartName()`→`getModuleName()`, §6.9;
  `loadModule("baja")` losing its `RuntimeProfile` argument, §6.9) are licensing-layer confirmations of
  Block 1's module-collapse finding.
- **[Block 3]** — this block's §6.9 supplies two concrete `AccessController.doPrivileged` →
  `SecurityUtil.doPrivileged` call sites for Block 3's `SecurityManager`-removal/`SecurityAgent`
  finding, and its §6.10 `checkJreFeature()` ties the licensing layer directly to Block 3's bundled
  Azul JRE 25 migration via a new `"zulu25"` license feature.
- **`niagara-research` B41/B322** — this block's §6.3 resolves the "which build has the dual DSA+ECDSA
  key vs the single DSA key" question those blocks left open (B322 found ONE real 4.10.9.14 build with
  only DSA, contrasted with the corpus baseline's dual-key `LicenseUtil`): N5 answers it differently
  again — ONE key, but that key is now ECDSA, not DSA.
- **`niagara-research` B126** — this block's §6.8 HostId-format delta and §6.3's algorithm delta are the
  direct N5-side counterparts of B126's native DSA‑1024/SHA‑1 signature-scheme and `Win-`-prefixed
  soft-HostId findings; a native-layer N5 re-verification (the `dsfspi`-equivalent, if any survives the
  JPMS/SecurityAgent migration) is out of scope here and not covered by [Block 3] either — worth a
  dedicated future gap.
- **`niagara-research` B479-B481/B483/B487** — the N4 remittance this block's §6.2 correction rests on;
  those blocks' subscription/entitlement model (6h `EntitlementCheck`, 90‑day `KeyRotationCheck`, the
  `.cloned` clone-protection flow, the operator alarm) is **not shown to have changed in N5** by
  anything this block read — only the internal deltas in §6.11 (interface, JSON lib, test hook, counter
  reset) were found; the cadences and clone-protection logic itself were not contradicted.
