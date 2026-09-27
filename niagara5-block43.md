# Block 43 — N5 data-at-rest cryptography: KeyRing, EncryptionKeySource and systemDb encryption

> **Scope**: N5 5.0.0.28's full data-at-rest cryptography map — the `com.tridium.nre.security.{KeyRing,
> SimpleKeyRing,KeyRingFactory,SecurityInitializer,Aes256PasswordManager,km.*}` secrets store, the
> `niagara.nre.security.EncryptionKeySource` enum's five-member semantics, `BOrientSystemDb`'s at-rest
> AES toggle, and how the platform's master key (`.km`) is itself protected per OS. Directly closes
> [Block 19]'s child gap **B19-G4** (trace the `KeyRing`/`SecurityInitializer` proprietary blocker — this
> block fully decompiles and reads it, where B19 explicitly declined to). Substantially answers **B19-G1**
> (confirms N5's `BOrientSystemDb.databaseEncryption` default is `encrypted`; does **not** settle whether
> this is new-in-N5 vs. pre-existing-in-N4, since the N4-side `orientSystemDb-se` module was not opened —
> see child gap **B43-G2**). Sharpens **B19-G2** (`EncryptionKeySource`'s N4-vs-N5 member count) with new
> structural evidence but does not close it (no N4-side decompile performed this session — see **B43-G3**).
> Does **not** cover: a live `[CERT-hw]` reproduction against a real N5 station (none exists on this
> install, per [Block 3]/[Block 9]/[Block 19]); the native `getKeyMaterial0`/`setKeyMaterial0` JNI
> implementations used by `NativePlatformProviderNpsdk` on embedded/JACE hardware (opaque compiled native
> code, not source — see **B43-G4**); the System Passphrase (`.sp`) chain in depth (a separate,
> non-`.km`-wrapped secret — flagged only in passing, consistent with how `niagara-research` B491 treats
> it); actual key MATERIAL, key file contents, or any file under a live install's `security/` directory
> (SECRETS DISCIPLINE — everything below is algorithms, key sizes, aliases, file *names*, and control
> flow read from decompiled Java **source**, never a live key/secret byte).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as [Block 19]/[Block 34]/[Block 38]
> (`etc/brand.properties:workbench.notice` Beta marker, JRE 25.0.4.7). N4 comparison baseline: the
> `niagara-research` corpus, read as REMITTANCE (not re-derived): B114 (BOG encryption pipeline +
> KeyRing surface, proprietary classes explicitly **not** decompiled at N4-corpus-write-time), B385
> (`nre.dll` native platform-services API, DPAPI natives as the Java crypto twin), B491 (the definitive
> N4 three-layer `KeyMaterial→KeyRing→secret` chain + per-OS `.km` protection, including a native Ghidra
> confirmation of Windows DPAPI machine-scope binding).
>
> Sources (all local, read-only, this session):
> - `/home/cristian/niagara5-research/organized/_bin-ext/nre/vineflower/com/tridium/nre/security/**`
>   (`KeyRing.java`, `SimpleKeyRing.java`, `KeyRingFactory.java`, `SecurityInitializer.java`,
>   `Aes256PasswordManager.java`, `PBEEncodingKey.java`, `PBEEncodingInfo.java`,
>   `io/BogPasswordObjectEncoder.java`, `DefaultSecurityInitializerConfig.java`,
>   `ISecurityInitializerConfig.java`, `km/{KeyMaterial,KeyMaterialFactory,PlatformKeyMaterial,
>   SimpleKeyMaterial}.java`) — already present in this corpus's decompile tree (extracted by a prior
>   session's whole-jar `nre.jar` pass, per [Block 34]'s own header noting these classes as
>   "referenced, not opened, this session"); **read here, verbatim, with line numbers, for the first
>   time this session** — the prior blocks explicitly declined to open them.
> - `.../organized/_bin-ext/nre/vineflower/com/tridium/nre/platform/{DpapiUtil,PlatformUtil,
>   NativePlatformProvider,NativePlatformProviderTridium,NativePlatformProviderNpsdk,
>   NJavaPlatformProvider,JavaPlatformProvider,EtcUtil}.java` — same tree, same status (read here for
>   the first time this session).
> - `.../organized/_bin-ext/nre/vineflower/com/tridium/nre/util/SimpleKeyValueUtil.java`,
>   `.../niagara/nre/security/EncryptionKeySource.java` (the latter already quoted in [Block 19] §19.7;
>   re-`grep`-confirmed this session, not re-decompiled).
> - `/home/cristian/niagara5-research/organized/baja/vineflower/niagara/security/
>   BAbstractAes256PasswordEncoder.java` — [Block 34]/[Block 38]'s own prior `baja.jar` decompile,
>   read here for the first time.
> - `/home/cristian/niagara5-research/organized/orientSystemDb/vineflower/com/tridium/systemDb/orient/
>   BOrientSystemDb.java` — [Block 19]'s own prior whole-module `orientSystemDb.jar` decompile
>   (`organized/orientSystemDb/vineflower/`), re-opened here for the `KeyRingAttributeHolder` static
>   initializer and the `databaseEncryption` property default (§19.4 quoted the encryption-toggle
>   existence but not this default value or the alias-holder mechanics).
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/nre.dll` — `strings` pass (no disassembly) confirming the
>   literal `-Dniagara.platform.provider=%s` format string and the literal class name
>   `com.tridium.nre.platform.NativePlatformProviderTridium` are both present in this build's native
>   launcher.
> - REMITTANCE `niagara-research`: B114 (`niagara-mental-model-bloque114.md`), B385
>   (`...bloque385.md`), B491 (`...bloque491.md`) — located via
>   `python3 /home/cristian/niagara-research/tools/corpus-nav.py find "KeyRing"|"DpapiUtil"|
>   "SecurityInitializer"` this session, then read directly.
>
> Method: `Read` of already-decompiled Vineflower source (no new decompilation this session — the
> `nre.jar` extraction predates this session, per [Block 34]'s header); every `file:line` citation below
> was opened and read verbatim with line numbers this session, not carried from a prior block's prose.
> Markers: `[CERT]` local primary (`file:line`, this session) · `[CERT-web]` — not used · `[CERT-a]` —
> not used · `[INFER]` deduction, explicitly flagged. Numeric constants (magic numbers, iteration counts,
> version numbers) were freshly `grep`-confirmed present at the cited line this session (self-verify below).
>
> Security/cryptography layer. Connects [Block 19] (§19.4/§19.7 — this block is the direct, deeper
> follow-up this block's own header promised as B19-G4/partially-B19-G1/sharpens-B19-G2), [Block 34]
> (§34.1's subscription secret inventory — `.restoreId`/`.refreshIncrement`/`.ecKeyPair`,
> `baja.licensing.subscription.*` aliases — is a KeyRing consumer this block's §43.1/§43.4 formalize the
> mechanism for; §34's own legacy `.kr`/`.km` merge is the SAME `mergeKeyRing` method this block reads at
> `KeyRing.java:278-300`), [Block 38] (§38.2's TOTP-secret AES-256/keyring finding is the SAME
> `BAbstractAes256PasswordEncoder`/`Aes256PasswordManager` mechanism this block documents generally).
> Cross-corpus: `niagara-research` B114, B385, B491.
>
> **Type:** standard

---

## 43.1 — The three-layer secrets chain survives verbatim from N4 to N5, down to the magic numbers `[CERT]`

`niagara-research` B491 (N4.14, `[CERT]`) documented a three-layer chain: **KeyMaterial** (`.km`, a random
32-byte AES-256 master key, never password-derived) → **KeyRing** (`.kr`, per-alias key entries, the whole
blob AES-encrypted under the `.km` bytes) → **secret** (encrypted under a per-alias key drawn from the
KeyRing via `Aes256PasswordManager`). This session's read of N5's own `com.tridium.nre.security` package
confirms every structural constant of that chain is **identical**, not merely architecturally similar:

| Constant | N4 (B491 §491.1) | N5 (this session) | Citation (N5) |
|---|---|---|---|
| KeyRing file format version | `version=5` | `VERSION = 5` | `SimpleKeyRing.java:44` |
| KeyRing magic number | `magic=357109530` | `MAGIC = 357109530` | `SimpleKeyRing.java:46` |
| KeyRing blob cipher | `AES/GCM/NoPadding`, `GCMParameterSpec(128,iv)` | identical | `SimpleKeyRing.java:439-448` |
| Legacy blob cipher (v≤3) | `AES/CBC/PKCS5Padding` | identical (`version <= 3`) | `SimpleKeyRing.java:189-191,223-232` |
| Per-entry cipher | AES-GCM under `.km` | identical, `SimpleKeyRingEntry` ctor | `SimpleKeyRing.java:586-607` |
| Master-key size | 32 bytes, `SecureRandom` | identical | `KeyMaterialFactory.java:14,37-42` |

N5 additionally exposes an **export** format not quoted in B491's N4 read: `EXPORT_VERSION = 6`,
`EXPORT_MAGIC = 167662754` (`[CERT]` `SimpleKeyRing.java:49,51`), used by `exportKeyData`/`importKeyData`
(`:326-358,262-324`) to produce a **portable**, passphrase-wrapped (`Aes256PasswordManager.encrypt` with an
externally supplied key, not the local `.km`) copy of just the *exportable* keyring entries — this is the
mechanism [Block 34]'s "legacy `.kr`/`.km` … merged into the MAIN key ring" (§34.1) and the
crash-recovery/roll pattern (§43.5 below) both build on, and is distinct from a raw file copy of `.kr`
(which stays bound to the local `.km`, per §43.2). Whether B491's N4 read simply didn't quote this constant
(vs. it being new) is **not resolved** — the class-for-class match on every OTHER constant makes new-in-N5
unlikely but not certain; not elevated to a formal child gap since it does not change any security-relevant
conclusion.

The wiring is also unchanged: `SecurityInitializer.initSecurityInfo()` calls
`KeyRingFactory.getInstance(this.siConfig.getSecDir(), ".kr", this.siConfig.getKmName()).getKeyRing(...)`
(`[CERT]` `SecurityInitializer.java:243`), and `DefaultSecurityInitializerConfig` resolves `secDir` to
`new File(System.getProperty("niagara.user.home"), "security")` with `kmName = ".km"` (`[CERT]`
`DefaultSecurityInitializerConfig.java:10-11`) — i.e. the **same** `<niagara.user.home>/security/{.kr,.km}`
layout N4's B491/B114 document, confirmed here directly from the N5 config class rather than inferred from
call sites.

## 43.2 — Master-key (`.km`) protection is per-platform-provider, and this install's own launcher picks the DPAPI-backed one `[CERT]`/`[INFER]`

`PlatformKeyMaterial` (the concrete `KeyMaterial` N5 always uses unless `NIAGARA_USE_SIMPLE_KM` is set,
`[CERT]` `KeyMaterialFactory.java:46`) delegates `.km`'s own read/write entirely to whichever
`IPlatformProvider` is active (`PlatformKeyMaterial.java:44-58` calling
`PlatformProviderHolder.PLATFORM_PROVIDER_INSTANCE.get/setKeyMaterial(...)`), and that provider is selected
once at JVM start from the `niagara.platform.provider` system property, defaulting to the pure-Java
provider with a printed warning if unset (`[CERT]` `PlatformUtil.java:15-48`, esp. `:20-24`).

Four concrete `IPlatformProvider` implementations exist in this build, each with a **different** `.km`
protection posture:

| Provider | Used when | `.km` protection | Citation |
|---|---|---|---|
| `NativePlatformProviderTridium` | native provider, real Tridium build (this install's `nre.exe`/`nre.dll` launcher — see below) | **Windows**: DPAPI-wrapped (`DpapiUtil.encrypt(km, isKeyMaterial=true, localMachine=true)`); **Linux**: raw file, POSIX `rw-rw----` set after write, no extra cipher layer | `NativePlatformProviderTridium.java:283-322` (get), `:324-376` (set, DPAPI at `:352-354`, POSIX perms `:357-364`) |
| `NativePlatformProviderNpsdk` | native provider, NPSDK/embedded-controller build; does **not** override `getKeyMaterial`/`setKeyMaterial` (`[CERT]`, no `@Override` for those methods in the class) | inherits the **abstract** `NativePlatformProvider` base impl: if `KeyMaterial.usingNativeKeyMaterial()` (`niagara.use.native.key.material` system property) → opaque native `getKeyMaterial0`/`setKeyMaterial0` JNI calls (compiled code, not source — **B43-G4**); else → plaintext at `/etc/niagara/<keyName>` via `SimpleKeyValueUtil`, no cipher | `NativePlatformProvider.java:1044-1157` (branch), `:1382-1386` (native decls), `EtcUtil.java:18` (`/etc/niagara` constant) |
| `NJavaPlatformProvider` | pure-Java provider, used e.g. by workbench tooling or any process launched without the native property set | plaintext via `SimpleKeyValueUtil`, **no OS-conditional cipher at all** — same code path on every OS | `NJavaPlatformProvider.java:838-902` |
| `SimpleKeyMaterial` (not a provider — a `KeyMaterial` impl reached only via `NIAGARA_USE_SIMPLE_KM` env var) | explicit opt-out, "NOT FOR PRODUCTION USE" (printed warning) | plaintext file in the security dir | `KeyMaterial.java:41-59`, `SimpleKeyMaterial.java` throughout |

**This install's own native launcher resolves to the DPAPI-backed provider.** `strings` on
`/mnt/c/Program Files/Niagara/5.0.0.28/bin/nre.dll` shows the literal format string
`-Dniagara.platform.provider=%s` immediately followed by the literal class name
`com.tridium.nre.platform.NativePlatformProviderTridium` (`[CERT]` both strings present, this session).
The adjacency of the two strings in the binary strongly suggests, but — absent disassembly of the launcher
routine that formats them — does not conclusively prove, that `%s` is filled with that exact class name;
this is flagged `[INFER — string adjacency, not disassembled]`. Given N4's own B385 independently
disassembled `nre.dll`'s DPAPI natives (Ghidra) and B491 §491.7 confirmed `NativePlatformProviderTridium`
is the real Windows provider for N4, and N5's `nre.dll` carries the identical class name and property
format string, this session treats the Tridium provider as the operative one for the Windows launcher
without re-running Ghidra (no new native disassembly performed this session — the N4 native evidence is
imported as strong prior, not re-derived).

**Net conclusion, consistent with N4's B491 §491.2/§491.4**: on Windows, the root `.km` is machine-bound via
DPAPI `CryptProtectData`/`CryptUnprotectData` — unreadable off-box, but decryptable by *any* local
account/process (LOCAL_MACHINE scope, not user-scope). On Linux (Tridium native provider) and on any
pure-Java-provider process regardless of OS, `.km` is **plaintext on disk**, protected only by filesystem
permissions (`rw-rw----` on the Tridium-Linux path; unspecified/default on the pure-Java path — this
session did not find an explicit `chmod`/`setPosixFilePermissions` call in `NJavaPlatformProvider`'s
`setKeyMaterial`, unlike the Tridium-Linux path's explicit `:357-364`). This is **structurally unchanged
from N4** — no delta found in this session's read of these classes; B491's own conclusion ("possession of
`.km` = decryption everywhere; Windows raises the bar to run-code-on-the-same-machine, Linux/QNX lower it
to read-the-key-file") transfers to N5 verbatim.

## 43.3 — `EncryptionKeySource`'s five members, read directly: what each one actually does `[CERT]`

[Block 19] §19.7 already quoted the enum body (`none, keyring, external, shared, undefined` — 5 members,
`EncryptionKeySource.java:3-9`) and flagged `shared`/`undefined` as unexplained beyond "consumed by
`BogPasswordObjectEncoder`". This session reads `BogPasswordObjectEncoder.java` in full and resolves the
semantics of all five:

| Value | Meaning | Key material source | Where it appears |
|---|---|---|---|
| `none` | The `.bog`'s reversible-password fields carry **no** reversibly-encrypted secret at all — only a `[null.N]=` validator marker; `passPhraseToKey` throws *"does not allow passwords that use reversible encryption algorithm"* | none | `BogPasswordObjectEncoder.java:290-291,80-82` |
| `keyring` | The platform `KeyRing` (§43.1) encrypts/decrypts the `.bog`'s reversible secrets — resolved via `Aes256PasswordManager.getManager(this.keyRing, alias)` at write/read time; `passPhraseToKey` explicitly refuses external passphrases in this mode | `SecurityInitializer`'s main KeyRing | `:259-265,294-295,72-90` |
| `external` | PBE (password-based encryption): the `.bog` carries `reversibleEncodingValidator`/`Salt`/`IterationCount`; the actual key is derived from an operator-supplied passphrase via `PBEEncodingKey`/PBKDF2 (§43.3.1 below) | passphrase-derived, no KeyRing | `:38-54,211-227` |
| `shared` | Raw secret bytes supplied programmatically (an `ISecretBytesSupplier`/`SecretBytes`), not via passphrase or KeyRing — the constructor path used e.g. for backup/restore re-wrapping ([Block 34]-adjacent: B491 §491.4 documents `BBackupService` doing exactly this transcode on the N4 side) | caller-supplied bytes, in-memory only | `:30-36,100-102` |
| `undefined` | A parse-time sentinel used only inside `parseBogHeader` while resolving what the header attribute *should* mean from context (never a value actually written to a saved `.bog` — `populateBogHeaderElement`/`writeBogHeader` never emit it) | n/a — not a real runtime state | `:112-209` (esp. `:130`, `:133,139,145`) |

This resolves the *behavioral* half of [Block 19]'s open comparison (§19.7): `shared` is the backup/restore
in-memory re-wrapping mode, and `undefined` is a header-parsing sentinel, not a fifth persisted key-source
option alongside the three end-user-visible ones (`none`/`keyring`/`external`). It does **not** resolve
whether N4 4.14's own (never-decompiled per B114) `EncryptionKeySource` enum already had these same 5
members — that remains **B19-G2**, now sharpened as **B43-G3** below given how much of the surrounding
package (§43.1) turned out to be byte-identical.

### 43.3.1 — `external` mode's key derivation: PBKDF2-HMAC-SHA256, 100 000/4096 iterations `[CERT]`

Not previously quoted in this corpus. `PBEEncodingKey` (constructed from an operator passphrase) derives
**two independent keys** from the same passphrase via `Pbkdf2.deriveKey(...)` under algorithm bundle
`"pbkdf2-sha256.1"` (`[CERT]` `PBEEncodingKey.java:20`):

- A **validation** hash: 16-byte random salt, **100 000** PBKDF2 iterations (`[CERT]` `:27-29,33,38`).
- The **encoding** key itself: a separate 16-byte random salt, **4 096** PBKDF2 iterations (`[CERT]`
  `:30-32,34,46-48`).

The much lower iteration count on the encoding key (vs. the validation hash) means the actual AES key
derivation is comparatively cheap; the expensive 100 000-round hash exists only to let the system *validate*
a supplied passphrase without ever deriving (and holding in memory) the real encoding key for a wrong guess.
These are exactly the `reversibleEncodingSalt`/`reversibleEncodingIterationCount` attributes [Block 19] §19.1
already found in `config.bog`'s header grammar (unchanged from N4.14's real `config.bog`, per that block's
B685 cross-check) — this session adds the concrete algorithm and iteration counts behind those two numbers.

## 43.4 — The password/secret encoder layer: `Aes256PasswordManager`, and one real alias-string rename `[CERT]`

`Aes256PasswordManager` is the class every reversible AES-256 password/secret encoder in `niagara.security`
(`BAes256PasswordEncoder`, `BAes256CbcPasswordEncoder`, the aliased variants, and — per [Block 38] §38.2 —
the TOTP-secret encoder) routes through. Default transformation is `AES/GCM/NoPadding` everywhere
(`[CERT]` `Aes256PasswordManager.java:36,50,83,96,109,117,127,135`), keys are drawn lazily from the KeyRing
by alias and **auto-created on first use** if absent (`[CERT]` `getKey(String)`, `:224-237`,
`kr.getKey(alias)` → `kr.createKey(alias, false)` fallback), and `BAbstractAes256PasswordEncoder.encode`/
`getSecretBytes` (`niagara.security` package, `[CERT]` `BAbstractAes256PasswordEncoder.java:38-93`) is the
`niagara.security.*` public-API entry point every concrete encoder inherits.

**One concrete, citable rename found this session, not previously in this corpus.** N5's default alias
literal is `"niagara.security.BAes256PasswordEncoder.key"` (`[CERT]` `Aes256PasswordManager.java:18`,
`DEFAULT_AES_KEY_ALIAS`), and `SimpleKeyRing`'s own special-case for this alias (forcing
`isKeyExportable=false` unconditionally, unlike every other alias which honors the caller's flag) matches
that exact literal (`[CERT]` `SimpleKeyRing.java:213-217`). `niagara-research` B491 §491.3 cites the N4-side
literal as `javax.baja.security.BAes256PasswordEncoder.key` (from N4's own `Aes256PasswordManager.java:16`).
This is the **same rename pattern** [Block 5] already established for the `javax.baja.*`→`niagara.*` package
move, but here it is a **string literal used as a KeyRing lookup key**, not merely a Java package/class name
— meaning an N4-created KeyRing entry stored under the *old* alias string will not be found by N5 code
looking up the *new* alias string unless something explicitly migrates it. No migration/transcode call for
this specific alias was found in the classes read this session (`KeyRing.mergeKeyRing` (§43.1) merges *all*
aliases from one ring into another verbatim by name — it would carry the OLD alias forward unchanged, not
rename it). Not resolved this session → child gap **B43-G1**.

## 43.5 — `BOrientSystemDb`'s at-rest AES: three auto-created, EXPORTABLE KeyRing keys, encryption ON by default `[CERT]`

[Block 19] §19.4 found the mechanism (`STORAGE_ENCRYPTION_METHOD="aes"`/`STORAGE_ENCRYPTION_KEY`,
`BDatabaseEncryptionState`) but explicitly left its default polarity and its N4-parity unresolved
(B19-G1). This session reads `BOrientSystemDb`'s static `KeyRingAttributeHolder` and the property
declaration directly:

- **Default is ON.** The `databaseEncryption` property is declared
  `@NiagaraProperty(name = "databaseEncryption", type = "BDatabaseEncryptionState",
  defaultValue = "BDatabaseEncryptionState.encrypted", flags = 5)` (`[CERT]`
  `BOrientSystemDb.java:109`, static `Property` init at `:132`) — i.e. a fresh N5 5.0.0.28 `systemDb`
  is encrypted-at-rest **by default**, not opt-in.
- **Three dedicated KeyRing aliases**, all resolved through the exact same `SecurityInitializer.getInstance()
  .getSecurityInfoProvider().getKeyRing()` main-ring path §43.1/§43.4 document, and all **lazily
  auto-created** the same way `Aes256PasswordManager.getKey` does (`getKey(alias)` → `null` →
  `createKey(alias, true)`, `[CERT]` `BOrientSystemDb.java:933-943`):

  | Alias | Purpose | Exportable? | Citation |
  |---|---|---|---|
  | `orientSystemDb.root` | OrientDB `root` account password (hex-encoded) | `true` | `:162,956-961` |
  | `orientSystemDb.admin` | OrientDB `admin` account password (hex-encoded) | `true` | `:163,964-969` |
  | `orientSystemDb.database` | Storage-level `STORAGE_ENCRYPTION_KEY` (base64-encoded) | `true` | `:164,973-980` |

  **Contrast with §43.4**: `BAes256PasswordEncoder.key` is hard-coded **non-exportable** by `SimpleKeyRing`
  itself, but these three `orientSystemDb.*` keys are created with `isExportable=true` (`[CERT]`
  `createKey(keyAlias, true)`, `:939`) — meaning, subject to `KeyRingPermission`, these three keys CAN be
  extracted via `KeyRing.exportKeyData`/the `.kr` export format §43.1 documents (`EXPORT_VERSION=6`), unlike
  the general password-encoder key. This asymmetry was not previously recorded in this corpus.
- **Still unresolved**: whether `databaseEncryption` (and its `encrypted`-by-default polarity) is new in N5
  or already existed in N4.14's `orientSystemDb-se` module — the class this session read is the N5 module
  only; `niagara-research`'s own secrets-at-rest arc (B114/B491) never mentions `orientSystemDb` at all, so
  it is not settled by REMITTANCE either. Because `OGlobalConfiguration.STORAGE_ENCRYPTION_METHOD`/
  `STORAGE_ENCRYPTION_KEY` are OrientDB's OWN upstream config knobs (not Tridium-authored), and N4.14
  already embeds OrientDB 3.2.23 which [Block 19] §19.4 confirms already supports the same knobs, it is
  plausible this Tridium-side wrapper property existed in N4 too — but this is `[INFER]`, not `[CERT]`,
  without opening N4's `orientSystemDb-se.jar`. → child gap **B43-G2** (narrows B19-G1).

## 43.6 — Data-at-rest cryptography map: artefact × algorithm × key source × default × N4-vs-N5

| Artefact | Algorithm / format | Key source | Default | N4 vs N5 |
|---|---|---|---|---|
| KeyRing (`.kr`) blob | AES/GCM/NoPadding, 128-bit tag, random 16B IV; legacy v≤3 = AES/CBC/PKCS5Padding | KeyMaterial (`.km`) | always on (no opt-out) | **unchanged** — identical magic/version constants (§43.1) |
| Each KeyRing entry | AES/GCM/NoPadding under the SAME `.km`-derived key | KeyMaterial (`.km`) | always on | **unchanged** |
| KeyMaterial (`.km`) itself | none in Java; platform-provider-delegated | OS primitive (DPAPI / file perms / opaque native) | on (mandatory — every station has one) | **unchanged mechanism**; Windows=DPAPI machine-scope, Linux(Tridium native)=plaintext+POSIX 0660, pure-Java=plaintext (§43.2) |
| `config.bog` / any `.bog` reversible secret | AES/GCM/NoPadding (keyring/shared) or PBKDF2-SHA256-derived AES (external) | `EncryptionKeySource`: `keyring`\|`external`\|`shared`\|`none` | `reversibleEncodingKeySource` attribute, no single global default (per-file, set at save time) | grammar unchanged ([Block 19] §19.1); **member-count parity with N4 unresolved** (B43-G3) |
| `BAes256PasswordEncoder.key` (default reversible password/secret encoder) | AES/GCM/NoPadding | main KeyRing, alias hard-coded non-exportable | always on for any reversible password field | **alias STRING renamed** `javax.baja.*`→`niagara.*` (§43.4, B43-G1) |
| TOTP secret ([Block 38] §38.2) | AES-256 via `BReversiblePasswordEncoder`/`BAes256PasswordEncoder` | main KeyRing, `keyring`-sourced by default | on (reversible, not one-way) | not independently re-verified this session; consistent with §43.4's mechanism |
| Subscription `.restoreId`/`.refreshIncrement`/`.ecKeyPair` ([Block 34] §34.1) | AES-256(-GCM) | main KeyRing, `baja.licensing.subscription.*` aliases | on | not independently re-verified this session; consistent with §43.1/§43.4's mechanism |
| `systemDb`/`orientSystemDb` storage | AES (OrientDB `STORAGE_ENCRYPTION_METHOD="aes"`) | main KeyRing, 3 dedicated **exportable** aliases (§43.5) | **`encrypted` (ON)**, confirmed this session | mechanism found unchanged by [Block 19]; **default polarity now confirmed for N5**; N4 parity unresolved (B43-G2, narrows B19-G1) |
| System Passphrase (`.sp`) | none in Java — OS-delegated (Windows Registry `systempw`, Linux/QNX plaintext) | separate chain, NOT `.km`-wrapped | on (mandatory) | file name `.sp` confirmed present in N5 (`SystemPassphrase.java:13`); not independently re-verified beyond that (out of scope, per B491 §491.2 bullet 4) |

## 43.x — Child gaps opened

- **B43-G1** — Determine whether an N4→N5 station upgrade/migration path (e.g. `n5mig.exe`, present in
  this install's `bin/`, not opened this session) re-keys or transcodes KeyRing entries stored under the
  old `javax.baja.security.BAes256PasswordEncoder.key` alias to the new
  `niagara.security.BAes256PasswordEncoder.key` alias (§43.4), or whether upgraded stations silently get a
  freshly auto-created key under the new alias while any pre-existing secret encoded under the old alias
  becomes unreadable. Requires either decompiling `n5mig.exe`'s migration logic or a live upgrade
  `[CERT-hw]` reproduction.
- **B43-G2** (narrows **B19-G1**) — Decompile N4.14's `orientSystemDb-se` module's `BOrientSystemDb` (or
  its N4-side equivalent class) for a `databaseEncryption`-equivalent property and its default value, to
  settle whether N5's `encrypted`-by-default at-rest AES for `systemDb` (§43.5) is new in N5 or was already
  the N4.14 default.
- **B43-G3** (sharpens **B19-G2**) — Decompile N4.14's own `com.tridium.nre.security.EncryptionKeySource`
  enum (still never opened by any block in either corpus) to settle whether `shared`/`undefined` (§43.3)
  are genuinely new N5 members or existed unchanged in N4 — now a stronger prior given every OTHER
  structural constant in the surrounding `com.tridium.nre.security.*` package (magic numbers, cipher
  transformations, class/method names) was found byte-identical between the two versions this session
  (§43.1).
- **B43-G4** — `NativePlatformProviderNpsdk`'s native `getKeyMaterial0`/`setKeyMaterial0`/
  `supportsKeyMaterialRecovery0` JNI implementations (§43.2), used on embedded/JACE-class hardware when
  `niagara.use.native.key.material` is set, are opaque compiled native code — not source, out of scope for
  this static-decompile session. Whether they bind `.km` to a hardware root (TPM, secure element) or are a
  thinner wrapper than the Windows DPAPI path is unknown. Would require the same class of native-binary
  reverse-engineering `niagara-research` B385 already did for `nre.dll`'s `DpapiUtil` natives, applied
  instead to the NPSDK-target native library.

## 43.x — Connections

- **[Block 19]** — §19.4/§19.7: this block is the direct follow-up promised there (B19-G4 CLOSED by
  §43.1-§43.2's full `KeyRing`/`SecurityInitializer` decompile-and-read; B19-G1 substantially answered by
  §43.5's default-polarity finding, narrowed to B43-G2 for full N4 parity; B19-G2 sharpened, not closed, as
  B43-G3). §19.1's `config.bog` header-attribute grammar is the exact surface §43.3/§43.3.1 explain the
  mechanism behind.
- **[Block 34]** — §34.1's subscription secret inventory (`.restoreId`/`.refreshIncrement`/`.ecKeyPair`,
  `baja.licensing.subscription.*` KeyRing aliases) and its `.kr`/`.km` legacy-merge note both consume the
  exact `KeyRing`/`mergeKeyRing` mechanism §43.1 documents from the definition side rather than the
  call-site side.
- **[Block 38]** — §38.2's TOTP-secret AES-256/keyring finding is the same `Aes256PasswordManager`/
  `BAbstractAes256PasswordEncoder` mechanism §43.4 documents generally; §38.7's SAML AES-256-CBC+RSA-OAEP
  assertion encryption is a DIFFERENT, XML-encryption-specific key-wrap scheme, not KeyRing-backed — flagged
  here only to note it is **outside** this block's map (not an omission).
- **REMITTANCE → `niagara-research` B491** — the N4-side three-layer chain and per-OS `.km` protection
  this block confirms structurally unchanged (§43.1/§43.2), with native Windows DPAPI evidence imported as
  strong prior (not re-disassembled this session, per §43.2's explicit `[INFER]` flag on the
  string-adjacency claim).
- **REMITTANCE → `niagara-research` B385** — the `nre.dll` native platform-services surface (DPAPI natives
  as `DpapiUtil`'s Java twin) this block's §43.2 `strings` pass corroborates at the string-literal level
  without repeating B385's own Ghidra disassembly work.
- **REMITTANCE → `niagara-research` B114** — the original (N4-corpus-time) `EncryptionKeySource`/`KeyRing`
  "proprietary, NOT decompiled" blocker this block's §43.1-§43.3 close on the N5 side, 4+ years/one-major-
  version after B114 recorded the same blocker as unresolved for N4.

## Self-verify

Mechanized `toolbelt/verify-block.sh` was not run against this file (not available in this session's
toolset invocation context); the marker tally and citation check below are a manual, fresh count of this
file as saved, per METHODOLOGY §11's decompiled-tree rule for blocks whose citations point entirely into
`organized/*/vineflower/` trees outside any `SOURCE_ROOT`.

```
marker tally (fresh `grep -o` count against this file as saved, this session — not hand-estimated):
  raw [CERT] token occurrences        : 30
  raw [INFER] token occurrences       : 7   (1 of these is the header legend's own
                                              "`[INFER]` deduction, explicitly flagged" — not a claim)
  raw [CERT-doc]/[CERT-web]/[CERT-a]  : 4   (all 4 are the header legend's own marker-list text,
                                              e.g. "`[CERT-web]` — not used" — none is a fresh claim)
  adjusted [INFER] (legend line excluded) : 6
ratio [INFER]/[CERT] (adjusted) = 6/30 = 0.20 — moderate, consistent with an evidence block whose
  primary sources were directly opened and read this session (§43.1-§43.2, §43.4-§43.5) with a handful
  of explicitly-flagged inferences at the exact points evidence ran out (native-launcher string
  adjacency in §43.2; N4-parity questions in §43.3/§43.5, formally pushed to child gaps B43-G2/B43-G3
  rather than asserted).
[CERT] file:line citation resolution: 0 resolved by an automated SOURCE_ROOT-relative scan — ALL
  citations point into organized/*/vineflower/ (decompiled trees) or into the sibling niagara-research
  corpus's own .md files, both outside this repo's SOURCE_ROOT. Declared per METHODOLOGY §11's
  decompiled-tree rule: citation gate = inline token-verify (below), not the automated resolver.
```

**Inline token-verify** (fresh `grep -n` re-checks performed this session, after the block's prose was
written, against the exact files cited above — not carried from memory):

```
SimpleKeyRing.java:44   public static final int VERSION = 5;                         ✓
SimpleKeyRing.java:46   public static final int MAGIC = 357109530;                    ✓
SimpleKeyRing.java:49   public static final int EXPORT_VERSION = 6;                   ✓
SimpleKeyRing.java:51   public static final int EXPORT_MAGIC = 167662754;             ✓
SimpleKeyRing.java:213  "niagara.security.BAes256PasswordEncoder.key".equals(alias)   ✓
Aes256PasswordManager.java:18  DEFAULT_AES_KEY_ALIAS = "niagara.security.BAes256PasswordEncoder.key"  ✓
BOrientSystemDb.java:109  defaultValue = "BDatabaseEncryptionState.encrypted"         ✓
BOrientSystemDb.java:162-164  KEY_RING_{ROOT,ADMIN,DB}_ALIAS = "orientSystemDb.{root,admin,database}" ✓
PBEEncodingKey.java:33  this.validationIterationCount = 100000;                       ✓
PBEEncodingKey.java:34  this.encodingIterationCount = 4096;                           ✓
nre.dll (strings)  "-Dniagara.platform.provider=%s" and
                    "com.tridium.nre.platform.NativePlatformProviderTridium"          ✓ (both present)
```

All 11 spot-checked tokens re-confirmed present at the cited location this session. No hallucinated
citation found. `EncryptionKeySource.java:3-9` (5-member enum body) was previously grep-confirmed in
[Block 19]'s own self-verify and re-read (not re-grepped a second time) this session — not double-counted
here.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; every source is a local decompiled
`.java` file, a local `.dll` (`strings` only, no disassembly), or an already-committed corpus `.md` file
opened directly this session.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block43.md`. Per the
caller's explicit read-only instruction, this task touches no other file — `INDEX.md`/`RESEARCH-STATE.md`/
`CATALOG.md` regeneration and gap-backlog re-classification (B19-G4 → closed; B19-G1 → partially answered,
narrowed to B43-G2; B19-G2 → sharpened, narrowed to B43-G3) are left to the orchestrator. No `git commit`
performed.
