# Block 47 — Do reversible secrets survive N4→N5? The KeyRing alias rename

> **Scope**: closes (for the `.bog`-level, per-`BPassword`-slot question) [Block 43]'s child gap
> **B43-G1** — whether an N4→N5 migration re-keys/transcodes KeyRing-encrypted reversible secrets stored
> under the OLD alias `javax.baja.security.BAes256PasswordEncoder.key` to the NEW alias
> `niagara.security.BAes256PasswordEncoder.key` ([Block 43] §43.4), or leaves them unreadable. This block
> reads `BBogMigrator`'s per-bog password-handling branch line-by-line (not censused, per [Block 14]/
> [Block 24]'s precedent), the `BAes256PasswordEncoder`/`BAliasedAes256PasswordEncoder`/
> `BAbstractAes256PasswordEncoder` encode/parse/transcode bodies (none previously opened by [Block 43],
> which only opened `Aes256PasswordManager`/`SimpleKeyRing`/`KeyRing*`), `Aes256PasswordManager.getKey`'s
> decrypt-failure path, and a newly-found, apparently-unwired `com.tridium.migrator.baja.MigrationEncoding`
> class + a `Migrate.passwordDecryptFunction` field that together suggest an INTENDED (but, in this build,
> uncalled) source-KeyRing-aware decrypt path. Also counts (never reads values of) the reversible
> `BPassword`-typed slots in the real, gitignored PANCCADIA `config.bog` copy and reads its header to
> classify which `EncryptionKeySource` mode that station actually uses. Does **not** cover: an actual
> `n5mig` execution (requires-execution, inherits [B14]/[B24]'s open gaps); a full disassembly proving
> `Migrate.passwordDecryptFunction`/`MigrationEncoding`/`BBackupDistMigrator.LazyDecryptFunction` are
> UNREACHABLE by every code path (only a `grep`-based absence-of-call-site check across the classes this
> session and [B14]/[B24] opened — flagged `[INFER]`, pushed to a child gap); the `.dist`-container-level
> backup encryption question this same dead code hints at (new child gap **B47-G2**, out of this block's
> literal B43-G1 scope); PANCCADIA's points/histories/alarms bogs (not present in the poc copy, per [B24]
> §24.6/B24-G2 — this block only reads `config.bog`, the same file B24 already opened).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as [Block 14]/[Block 19]/[Block 24]/[Block 43]
> (`migrator.jar` sha256 `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08`, unchanged since
> [B14]/[B24], reused — not re-decompiled). PANCCADIA `config.bog`: the same gitignored poc copy [B24] §24.6
> opened (`file.xml` unzips to exactly **486,798 bytes**, byte-identical to B24's own count — confirms same
> artifact, re-verified this session).
>
> Sources (all local, read-only):
> - `/home/cristian/niagara5-research/organized/migrator/vineflower/com/tridium/migrator/BBogMigrator.java`
>   — [B14]/[B24]'s own reused decompile tree; this session reads `migrateBog()`/`encodeBog()`/
>   `makeEncoderPlugin()` ([B24] §24.3 censused these method names and what `encodeBog` broadly does —
>   "handles AES-256/keyring password re-encoding" — this session opens the actual body for the first time
>   and finds that characterization needs correction, §47.1).
> - `.../organized/migrator/vineflower/com/tridium/migrator/baja/MigrationEncoding.java`,
>   `.../com/tridium/migrator/BBackupDistMigrator.java`, `.../com/tridium/migrator/Migrate.java` — same
>   reused tree, all three opened for the first time this session (B14/B24 named `BBackupDistMigrator` in
>   the converter catalog table but did not read its full body; `MigrationEncoding` and `Migrate`'s
>   `passwordDecryptFunction` field were never previously found by either block).
> - `.../organized/migrator/vineflower/com/tridium/migrator/MigrationUtils.java` — [B24] §24.4 censused
>   this class's 40 method signatures by `grep` only; this session opens the `MigrationValueDocDecoder`
>   inner class body (§47.1) for the first time.
> - `.../organized/migrator/vineflower/migrator.lexicon` — the operator-facing message text for
>   `migrate.breakExternalEncoding`/`migrate.breakKeyringEncoding`/`migrate.noClearedPasswords`, read in
>   full this session (not previously quoted).
> - `/home/cristian/niagara5-research/organized/file/vineflower/com/tridium/file/types/bog/BBogFile.java`
>   — `usesKeyRingEncryption`/`usesReversibleEncryptionPassPhrase`/`forceClearReversibleEncryptionPassPhrase`/
>   `canUseReversibleEncryptionPassPhrase`, opened for the first time in either corpus this session.
> - `/home/cristian/niagara5-research/organized/baja/vineflower/com/tridium/util/PasswordUtil.java` —
>   `forceClearReversiblePasswords`/`updatePasswords`/`ReplaceWithDefaultPasswordPropertyUpdate`, opened
>   for the first time this session.
> - `/home/cristian/niagara5-research/organized/baja/vineflower/niagara/security/{BAes256PasswordEncoder,
>   BAliasedAes256PasswordEncoder,BAbstractAes256PasswordEncoder}.java` — [B43] §43.4 opened
>   `BAbstractAes256PasswordEncoder.java` only for its `encode`/`getKey` call shape; this session reads its
>   `getSecretBytes`/`transcode` bodies (not previously read) and opens `BAes256PasswordEncoder.java` /
>   `BAliasedAes256PasswordEncoder.java` for the first time in either corpus — this is the concrete class
>   pair that resolves B43-G1.
> - `/home/cristian/niagara5-research/organized/_bin-ext/nre/vineflower/com/tridium/nre/security/
>   Aes256PasswordManager.java` — [B43] §43.4 cited `:36,50,83,96,109,117,127,135` (transformation
>   constants) and `:224-237` (`getKey`, already open); this session reads `getManager(KeyRing)` (no-alias
>   overload, `:22-24`, not previously quoted) and the raw `decrypt(byte[],...)` cipher call (`:138-145`,
>   not previously quoted) to settle the decrypt-failure question.
> - `/home/cristian/niagara5-research/poc/n5mig-panccadia/in/config.bog` — the same real, gitignored,
>   read-only PANCCADIA backup copy [B24] §24.6 opened; unzipped to this session's scratchpad
>   (`/tmp/claude-1000/.../scratchpad/b47/extracted/file.xml`), header line and `t=` type-attribute counts
>   read — **no property VALUE, credential, or ciphertext byte reproduced below**, per task SECRETS
>   DISCIPLINE; only the header's `reversibleEncodingKeySource` literal, structural type-prefixes
>   (`b:Password` count) and the self-describing encoding-scheme TAG embedded in each value's first
>   bracketed segment (`[pbkdf2-aes-256.1]`, an algorithm-name label, not key or plaintext material) are
>   reported.
>
> Method: `Read`/`grep -n` of already-decompiled Vineflower source (no new decompilation — all three jars
> reused from [B14]/[B24]'s session-scoped extraction, per those blocks' own headers); `unzip` +
> `grep -o`/`head -c` of the PANCCADIA `config.bog` copy, counts and structural tags only. Markers:
> `[CERT]` local primary (`file:line`, this session) · `[INFER]` deduction, explicitly flagged (used here
> specifically for an absence-of-call-site claim, §47.3 — per METHODOLOGY §3's negative-existence rule:
> "not found by grep across the files THIS session and B14/B24 opened" is `[INFER]`, not `[CERT]`, since it
> is not a claim about one exact artifact fully read, but about a `grep` search's negative result across a
> known-partial set of files).
>
> Security/cryptography layer. Directly closes [Block 43] §43.4's **B43-G1** for the `.bog`-level question
> (§47.1-§47.2). Connects [Block 14] (§14.4's `BBogMigrator` census — this block is the line-by-line
> follow-up on the password-handling branch [B14] B14-G4 flagged as un-read), [Block 24] (§24.3's
> `encodeBog`/`migrateBog` phase census — corrected in §47.1; §24.6's PANCCADIA cross-check — extended here
> with the actual `EncryptionKeySource` mode and `BPassword` slot count), [Block 19] (§19.1's `config.bog`
> header grammar — this block reads the SAME real PANCCADIA header B24 opened and classifies its
> `reversibleEncodingKeySource` value for the first time in either corpus).
>
> **Type:** mixed — §47.1-§47.2 are evidence (reading the shipped `migrator.jar`/`baja.jar`/`file.jar`
> classes and the real PANCCADIA bog); §47.4 draws a verdict synthesizing §47.1/§47.2 against [B43]'s own
> prior finding (a different block's `[CERT]`), the declared `mixed` trigger.

---

## 47.1 — `n5mig` never attempts per-value KeyRing decryption during a bog migration: `keyring`-sourced reversible secrets are unconditionally wiped, not silently mis-decrypted `[CERT]`

Full read of `BBogMigrator.migrateBog()` (`BBogMigrator.java:371-445`). Before opening the source bog into a
live component tree, it inspects the SOURCE bog's own header-derived `EncryptionKeySource` (via
`BMigrationBogFile`/`BBogFile.usesReversibleEncryptionPassPhrase()`/`usesKeyRingEncryption()`, §47.2) and
branches three ways:

| Source `reversibleEncodingKeySource` | Passphrase supplied? | `migrateBog()` behavior | `[CERT]` |
|---|---|---|---|
| `external` | yes, and correct (up to 3 retries) | `bogFile.setReversibleEncryptionPassPhrase(passPhrase)` — reversible passwords DECRYPT and carry forward, re-encoded on write (§47.1.1) | `BBogMigrator.java:375-411` |
| `external` | no / null, or 3 wrong attempts | `bogFile.forceClearReversibleEncryptionPassPhrase()` — **every** reversible password in the tree is wiped; `LOG.severe(..."migrate.breakExternalEncoding"...)`, naming the cleared slot paths | `:382-390` (null-passphrase sub-case), `:400-404` (retry exhaustion), `:412-417` (top-level no-supplier case) |
| `keyring` | n/a — keyring mode has no operator passphrase at all | `bogFile.forceClearReversibleEncryptionPassPhrase()` **unconditionally**, no attempt to open the source's own KeyRing first; `LOG.severe(..."migrate.breakKeyringEncoding"...)` | `:418-423` |

The `keyring` branch (`:418-423`) is the direct, literal answer to [B43] §43.4's open question: **`n5mig` does
not try to decrypt a `keyring`-sourced reversible secret with either the old or the new KeyRing alias at
all** — it treats "the source used keyring encoding" as an unconditional non-migratable condition and clears
it. The operator-facing lexicon message states this as POLICY, not as an incidental side effect of a lookup
failure:

```
migrate.breakKeyringEncoding=Detected that the source used keyring encoding, therefore
encrypted values in the source are not migratable. In particular,
the following password values in the migrated output will not
function and require manual updates: ...
```
`[CERT]` `organized/migrator/vineflower/migrator.lexicon:161` (full text quoted verbatim, this session).
`migrate.breakExternalEncoding` (`:160`) and `migrate.noClearedPasswords` (`:162`, `"(No passwords found)"`,
used when the cleared-slot list is empty) are the sibling messages for the `external`-no-passphrase case.

**What "force clear" actually does, traced to the property-update layer.** `forceClearReversibleEncryptionPassPhrase()`
(`BBogFile.java:117-128`) sets the bog's encoder to `BogPasswordObjectEncoder.makeNone()` and calls
`PasswordUtil.forceClearReversiblePasswords(rootComponent)` (`:125`), which walks EVERY property of EVERY
`BComplex` in the tree recursively (`PasswordUtil.java:91-101`, `updatePasswords`) and, for each
`BPassword`-typed slot whose current encoder `instanceof BReversiblePasswordEncoder`, replaces the value
with `BPassword.DEFAULT` (empty) — `PasswordUtil.java:244-263`
(`ReplaceWithDefaultPasswordPropertyUpdate.apply`). A `BPassword` slot using a ONE-WAY encoder (e.g. a
`BPasswordAuthenticator`-backed user login hash) is explicitly left untouched (`:252`, `else return
password`) — this clearing is scoped to REVERSIBLE secrets only, consistent with the gap's own framing
(driver credentials, SMTP passwords — not login password hashes). `[CERT]` all citations above, this
session.

**`encodeBog()`'s own output-encoding decision (`:447-478`) is DOWNSTREAM of this clearing, not a re-encoder
of the original values.** [B24] §24.3 characterized `encodeBog` as handling "AES-256/keyring password
re-encoding" — full read this session shows this needs correction: `keySource` for the OUTPUT is computed
from `AxPasswordUtil.usesPasswordEncodings(c, {BAes256PasswordEncoder.ENCODING_TYPE,
BAliasedAes256PasswordEncoder.ENCODING_TYPE, BAes256Pbkdf2HmacSha256PasswordEncoder.ENCODING_TYPE})` against
the ALREADY-migrated component tree `c` (`:449-457`) — i.e. by the time `encodeBog` runs, any `keyring`-mode
password has already been cleared to `BPassword.DEFAULT` by `migrateBog()`'s earlier branch, so this check
can only ever see `external`-mode encodings (surviving because a correct passphrase was supplied) or none at
all; the output `EncryptionKeySource` is `external` or `none`, **never `keyring`** for a migrated bog —
`makeEncoderPlugin` (`:539-593`) does have a live `EncryptionKeySource.keyring` branch
(`BogPasswordObjectEncoder.makeKeyring()`, `:569-573`), but `encodeBog`'s own `keySource` computation
(`:449-457`) can only ever produce `external`/`none`, so that branch is unreachable from THIS call site
(`makeEncoderPlugin` is `private`, `BBogMigrator`'s only caller passes `keySource` from `encodeBog`'s
2-value computation — confirmed by re-reading `:461-462`, this session; not independently checked against
every OTHER private caller of `makeEncoderPlugin`, since none other exists in this 771-line file, `grep -c
"makeEncoderPlugin("` → 2, the declaration and the one call site). **Correction to [B24] §24.3**: `encodeBog`
does not "re-encode" a keyring password under a new key — a migrated N5 bog can no longer BE keyring-encoded
at all, by construction of this pipeline.

### 47.1.1 — The `external` (passphrase) path is a genuine decrypt-then-re-encrypt, and is unrelated to the KeyRing alias question `[CERT]`

When the operator supplies the correct bog-protection passphrase, `setReversibleEncryptionPassPhrase`
(`BBogFile.java:130-172`, not fully quoted here) derives the PBKDF2 key from the supplied passphrase and the
bog's own stored `reversibleEncodingSalt`/`reversibleEncodingIterationCount` header attributes ([B43]
§43.3.1's mechanism), successfully decrypting the `external`-mode `BPassword` values in place; `encodeBog`
then re-encodes them (still `external`, under a fresh IV, same derivation) into the target bog. This path
never touches the KeyRing/alias machinery at all — [B43]'s alias-rename finding (§43.4) is **entirely
inapplicable** to `external`-mode secrets, only to `keyring`-mode ones. `[CERT]` `BBogFile.java:130-172`
(method signature and keyring-mode guard at `:133-135`, confirming this method REFUSES a keyring-mode bog).

## 47.2 — Why the default (`BAes256PasswordEncoder`) reversible encoder is the exact failure mode B43-G1 asked about — and would NOT be moot outside n5mig's clear-on-sight policy `[CERT]`

[B43] §43.4 found the alias STRING renamed (`javax.baja.security.BAes256PasswordEncoder.key` →
`niagara.security.BAes256PasswordEncoder.key`) but had not yet opened the encoder classes that actually
consume that alias at decrypt time. This session opens both concrete `BAbstractAes256PasswordEncoder`
subclasses and finds they behave **differently** with respect to alias persistence:

| Encoder | Alias source at `parse()`/read time | Encoded-string shape | `[CERT]` |
|---|---|---|---|
| `BAes256PasswordEncoder` (the DEFAULT — what a plain `BPassword` field uses unless a driver explicitly opts into the aliased variant) | **Always** the class's own hard-coded constructor literal `"niagara.security.BAes256PasswordEncoder.key"` (N5's NEW string) — `parse()` decodes only a 2-element `{iv, cipher}` array; the alias is **never read from the encoded value** | `[<algorithm-name>.N]=<iv>:<cipher>` (2 data fields) | `BAes256PasswordEncoder.java:26-28` (ctor), `:30-40` (`parse`, only `data[0]`→iv, `data[1]`→cipher) |
| `BAliasedAes256PasswordEncoder` | Defaults to the same NEW literal in its no-arg ctor, but `parse()` **overwrites `this.keyAlias` from `data[0]` of the decoded value** — the alias travels WITH the ciphertext | `[<algorithm-name>.N]=<alias>:<iv>:<cipher>` (3 data fields, alias first) | `BAliasedAes256PasswordEncoder.java:30-36` (ctor incl. explicit-alias overload), `:38-49` (`parse`, `data[0]`→`this.keyAlias`) |

**This means the alias-rename risk [B43] §43.4 found is REAL and CONFIRMED for the plain, default
`BAes256PasswordEncoder` path** (not merely a renamed-package cosmetic issue): decrypting an N4-encoded
value with N5 code ALWAYS looks up the KeyRing under the class's hard-coded NEW alias, never under whatever
alias the value was actually encrypted with, because the default encoder's wire format carries no alias at
all — the alias is 100% implicit in the class/constant, and that constant changed string value between N4
and N5 ([B43] §43.4). `BAliasedAes256PasswordEncoder` (used, per [B43] §34.1/§38.2 cross-references, by e.g.
subscription-secret and some driver-credential fields) is IMMUNE to this specific failure mode by
construction — its own serialized value is self-describing.

**Traced to the exact runtime failure this WOULD produce, if anything ever called it cross-version (it does
not, via `n5mig`, per §47.1).** `Aes256PasswordManager.getKey(String keyName)` (already partly cited by
[B43] §43.4) auto-creates a FRESH RANDOM key under `keyName` when the KeyRing has no entry for it
(`kr.getKey(keyName)` → `null` → `kr.createKey(keyName, false)`, `[CERT]`
`Aes256PasswordManager.java:224-237`, re-confirmed this session). The raw AES/GCM decrypt call
(`Aes256PasswordManager.java:138-145`, `decrypt(byte[] key, byte[] cipher, byte[] iv, String
aesTransformation)`) has **no catch block of its own** around `aesCipher.doFinal(cipher)` (`:143`) — under
`AES/GCM/NoPadding`, decrypting with the WRONG key throws `javax.crypto.AEADBadTagException` (a
`GeneralSecurityException`), which propagates UNCAUGHT through `decryptSecret`
(`Aes256PasswordManager.java:99-106,120-124`) and through
`BAbstractAes256PasswordEncoder.getSecretBytes()` (`:62-93`, this session's first full read of this method —
[B43] only cited `encode`/`getKey` shape). `getSecretBytes()`'s only local catch is for
`niagara.nre.security.permissions.PermissionException` (`:78-91`); `validate()` (`:96-127`) likewise catches
only `SecurityException`/`MissingEncodingKeyException`, NOT a generic crypto exception — so this would
surface as a genuine **runtime exception/fault**, not a silently-empty password and not a caught-and-logged
degrade. `[CERT]` all citations above, this session — resolving gap item (4)'s "what happens on decrypt
failure" question for the general (non-`n5mig`) case: **exception, not empty password, not a silent fault**.

**Net reconciliation with §47.1**: this failure mode is real at the class/mechanism level (confirms [B43]
§43.4's concern was well-founded) but is **structurally unreachable via `n5mig`'s own bog-migration path**,
because §47.1 shows `n5mig` never calls `getSecretBytes()`/`decryptSecret()` on a `keyring`-sourced value at
all — it force-clears first. The mechanism-level bug and the migration-tool-level mitigation are BOTH true
simultaneously; they answer different questions (§47.4 states the combined verdict).

## 47.3 — An apparently-unwired KeyRing-aware decrypt path exists in the compiled jar, but no call site was found `[CERT]` `[INFER]`

Unexpected finding, not anticipated by [B43]'s child gap text. `com.tridium.migrator.baja.MigrationEncoding`
(package name distinct from `com.tridium.migrator`'s other classes — suggests an older/AX-lineage helper
retained in the jar) implements exactly the kind of source-side-aware decrypt [B43]/this gap asked whether
`n5mig` performs: `makeMigrationDecryptFunction(File niagaraSecurityDir)` opens the SOURCE station's OWN
`.kr`/`.km` files directly (`MigrationEncoding.java:29-107`, reads `niagaraSecurityDir/.km` via
`KeyMaterialFactory`, `niagaraSecurityDir/.kr` via `SimpleKeyRing`, including a legacy AX-era export/import
branch for old `.kr` versions, `:42-77`) and returns an `AESDecryptFunction` closure bound to that SOURCE
KeyRing (`:103`). **However**, the closure is built via `Aes256PasswordManager.getManager(keyRing)` — the
**no-alias overload**, which itself hard-codes the SAME NEW literal
(`Aes256PasswordManager.java:22-24`, `getManager(KeyRing kr)` → `new Aes256PasswordManager(kr,
"niagara.security.BAes256PasswordEncoder.key")`) — so even if this function WERE called against a real N4
source `.kr` file, it would suffer the exact §47.2 alias mismatch itself (looking up the NEW alias in a
KeyRing populated under the OLD alias), unless the source `.kr` happens to already have been re-keyed.

**No call site for `MigrationEncoding.makeMigrationDecryptFunction` was found in any class this session or
[B14]/[B24] opened.** `grep -rn "MigrationEncoding"` across `organized/migrator/vineflower/com/` returns only
the class's own declaration (`[INFER]` — a `grep`-based negative result across a known-partial file set, per
METHODOLOGY §3's negative-existence rule, not an exhaustive bytecode cross-reference). A structurally
matching consumer shape exists but is ALSO apparently unused: `BBackupDistMigrator.LazyDecryptFunction`
(`BBackupDistMigrator.java:262-277`, a lazy `AESDecryptFunction` wrapper) is declared but `grep -c "new
BBackupDistMigrator.LazyDecryptFunction\|new LazyDecryptFunction"` → **0** in this class's own 278-line body
(full read this session, §47.3's own citation); and `Migrate.java:99`'s `private static AESDecryptFunction
passwordDecryptFunction;` field is declared but never assigned or read elsewhere in that file (`grep -c
"passwordDecryptFunction"` → **1**, the declaration itself). `BBackupDistMigrator.DIRS_TO_EXTRACT`
(`:38`) DOES list `"niagara_user_home/security/.kr"`/`"security/.kr"` among the paths extracted from a
`.dist` backup archive — so the source `.kr` file IS unpacked to a temp dir during a `.dist`-source
migration — but `migrate()`'s visible body (`:72-161`, full read) only ever copies `stationDir`'s OWN files
(the station folder under `stations/<name>/`) into the working `srcMig` dir passed to the nested `Migrate`
instance (`:143-150`); the extracted `security/.kr` sits in a SIBLING directory (`srcRoot`, not
`stationDir`) and this session found no code path that forwards it into that nested `Migrate` call. `[INFER]`:
taken together, this reads as VESTIGIAL machinery — either an earlier design where `n5mig` attempted
source-KeyRing-aware per-value decryption (superseded by §47.1's simpler unconditional-clear policy) or an
as-yet-unshipped feature for a DIFFERENT concern (decrypting a `.dist` backup archive that was itself
protected, a distinct question from per-`BPassword`-field encoding — not settled this session, not confirmed
to even be what these classes are for). Not elevated past `[INFER]` — no direct evidence of INTENT was read,
only the shape of unused code. → child gap **B47-G2**.

## 47.4 — PANCCADIA's actual `config.bog`: `external` mode, 3 reversible `BPassword` slots — B43-G1's risk does not even apply to this station's driver-credential layer `[CERT]`

The real, gitignored PANCCADIA `config.bog` copy at `poc/n5mig-panccadia/in/config.bog` (same 486,798-byte
`file.xml`, [B24] §24.6) was re-opened this session, header and structural type-counts only:

```
<bajaObjectGraph version='4.0' reversibleEncodingKeySource='external' FIPSEnabled='false'
  reversibleEncodingValidator='[pbkdf2-sha256.1]=<48 redacted hex chars>...' ...>
```

`[CERT]` header line read verbatim except the validator hash value, which is redacted here (not a secret in
the reversible sense — it is a PBKDF2 VALIDATION hash, [B43] §43.3.1 — but out of an abundance of caution
under this task's SECRETS DISCIPLINE, only the `reversibleEncodingKeySource='external'` attribute NAME+VALUE
is asserted as evidence). This is [B24]'s own header, re-read — **`reversibleEncodingKeySource` was not
previously classified by either corpus**; [B19]/[B24] documented the header GRAMMAR but not which mode this
specific station uses.

**Reversible `BPassword` slot count**: `grep -o` for `t=` tokens containing `Password` (case-insensitive)
found **3** occurrences of `t="b:Password"` (the reversible type), plus 5× `t='b:PasswordAuthenticator'`
(one-way login-hash type, NOT in scope — [B43]'s reversible-secret concern and §47.1's `PasswordUtil`
clearing logic both explicitly exclude non-reversible encoders), 3× `t="b:GlobalPasswordConfiguration"`,
2×`t="b:PasswordHistory"`, 5× `t="b:UserPasswordConfiguration"`/`t='b:UserPasswordConfiguration'` (all
policy/config objects, not secret values). `[CERT]` `grep -o` counts against `file.xml`, this session,
structure only.

**All 3 `b:Password` elements' encoded values begin with the literal bracketed tag `[pbkdf2-aes-256.1]=`**
(the algorithm-name segment of the `external`-mode `BAes256Pbkdf2HmacSha256PasswordEncoder`'s wire format,
`ENCODING_TYPE` constant confirmed present at `BAes256Pbkdf2HmacSha256PasswordEncoder.java:28`, this
session) — consistent with, and direct structural confirmation of, the header's `reversibleEncodingKeySource
='external'` declaration: this is exactly the `AxPasswordUtil.usesPasswordEncodings(...,
{BAes256Pbkdf2HmacSha256PasswordEncoder.ENCODING_TYPE, ...})` check §47.1 traced in `encodeBog`. **No cipher
byte, IV, or ciphertext content beyond this 19-character algorithm-name tag is reproduced anywhere in this
block.**

**Operational implication for a real PANCCADIA N4→N5 migration**: because this station's 3 reversible
secrets use `external` (passphrase-derived), not `keyring`, encoding, [B43] §43.4's alias-rename finding and
this block's §47.2 confirmation of it are **NOT APPLICABLE** to PANCCADIA's current `config.bog` — provided
the migration operator supplies the correct bog-protection passphrase (the one set via Workbench's "Bog File
Protection" tool, per the `migrate.breakExternalEncoding` message's own remediation text, §47.1) to `n5mig`
at migration time, per §47.1.1 all 3 values decrypt-and-re-encrypt successfully and carry forward. If that
passphrase is NOT supplied (or not known), all 3 are wiped and the operator is told exactly which slot paths
need manual re-entry post-migration — a loud, actionable failure, not a silent one. This is a narrower,
MORE FAVORABLE finding for PANCCADIA specifically than [B43]'s general alias-rename concern implied, and it
was only discoverable by reading the ACTUAL station file rather than reasoning about the `keyring` default in
the abstract.

## 47.5 — Verdict: MITIGATED for `n5mig`'s own supported migration path; CONFIRMED-RISK at the mechanism level for anything that bypasses it

**CONFIRMED-RISK** (mechanism level, §47.2): the plain/default `BAes256PasswordEncoder`'s hard-coded alias
literal changed string value between N4 and N5 ([B43] §43.4), its wire format carries no alias of its own
(§47.2), `Aes256PasswordManager.getKey` silently auto-creates a fresh key on alias miss rather than failing
fast, and the resulting cross-key AES/GCM decrypt throws an uncaught `AEADBadTagException`-class exception
(§47.2) — this WOULD break decryption of an N4-created `BAes256PasswordEncoder` value read by N5 code using
any path that (a) reuses the original `.kr`/`.km` files unchanged and (b) actually invokes
`getSecretBytes()`/`decryptSecret()` on the old value under the new hard-coded alias.

**MITIGATED for the one shipped, supported path this corpus has read (`n5mig`'s `BBogMigrator`, §47.1)**:
that tool does not exercise the risky code path at all for `keyring`-sourced reversible secrets — it
unconditionally treats them as non-migratable, clears them, and tells the operator exactly what to
re-enter. The alias rename therefore has **zero observable effect** on a real `n5mig` migration's `keyring`-
mode secrets specifically BECAUSE those secrets were never going to survive migration through this tool
REGARDLESS of the alias (Tridium's own design choice, not a side effect of the rename — the
`migrate.breakKeyringEncoding` message's wording, "the source used keyring encoding, therefore ... not
migratable", reads as an unconditional policy, not a caught-exception fallback). `external`-mode secrets
(PANCCADIA's actual case, §47.4) are unaffected by the alias question entirely and DO survive with a correct
passphrase.

**NOT-APPLICABLE for PANCCADIA's current `config.bog`** (§47.4) — it holds 0 `keyring`-sourced reversible
secrets to be at risk in the first place.

**Residual scope, not closed by this block**: whether the SAME unconditional-clear policy holds for
`BPxMigrator` (px files) and `BTemplateFileMigrator` (templates) — this block read only `BBogMigrator`'s
password branch; [B24] §24.2's own catalog notes `BPxMigrator`/`BPxPremigrator`'s bodies were not read
line-by-line (B24-G5) — → does not need its own new child gap, folds into the existing **B24-G5**. Whether
`MigrationEncoding`/the dead-looking decrypt-function fields (§47.3) are genuinely unreachable, vs. reachable
via a path this session's `grep` missed (e.g. reflection, a different `Migrate` overload, or the
`-premigrate`/`Premigrate.java` sibling class, not opened this session) is **B47-G1**.

## 47.x — Child gaps opened

- **B47-G1** — Confirm (or refute) §47.3's `[INFER]` "no call site found" claim for
  `MigrationEncoding.makeMigrationDecryptFunction`/`BBackupDistMigrator.LazyDecryptFunction`/
  `Migrate.passwordDecryptFunction` by reading `Premigrate.java` (not opened this session or [B14]/[B24])
  and by a full disassembly-level cross-reference (not a `grep`) of `migrator.jar`'s compiled bytecode, to
  rule out a reflective or bytecode-only call site invisible to source-level `grep`.
- **B47-G2** — Determine what `MigrationEncoding`/`BBackupDistMigrator`'s `security/.kr`-extraction
  (`DIRS_TO_EXTRACT`, `BBackupDistMigrator.java:38`) machinery is actually FOR, if anything, in the shipped
  product: whether N4 `BBackupService` can produce a `.dist` archive whose CONTAINER (not individual `.bog`
  files) is itself KeyRing/passphrase-protected, and if so, how `n5mig` is meant to open such an archive,
  given this session found no live wiring for it. Would need `niagara.backup`/`BBackupService`'s own
  encryption-option code (not opened this session; [B34] §34.1 read `BBackupService`'s legacy `.kr`/`.km`
  MERGE behavior but not an encrypted-`.dist`-container option) and/or a live `[CERT-hw]` reproduction with
  an encrypted N4 backup.
- **B47-G3** — This block did not open `AxPasswordUtil.usesPasswordEncodings` (`com.tridium.security`
  package, imported by `BBogMigrator.java:7` and cited at `:450-455`) at its own definition site — its
  exact semantics (does it check EVERY `BPassword` slot in the tree, or only a sample/first-match?) were
  taken on faith from its call-site usage and name. A full read would harden §47.1's "output can only be
  `external`/`none`" conclusion from strongly-implied to independently `[CERT]`-verified.

## 47.x — Connections

- **[Block 43]** — this block closes §43.4's **B43-G1** for the `.bog`/per-`BPassword`-field question
  (§47.1-§47.2, verdict §47.5); [B43]'s own `.kr`/`.km`/`KeyRing`/`SecurityInitializer` mechanism reads
  (§43.1-§43.2) are reused, not re-derived, as the foundation for §47.2's `Aes256PasswordManager.getKey`
  auto-create citation.
- **[Block 14]** — deepens B14-G4 (`BBogMigrator`'s pipeline, [B14] censused by method signature only) for
  specifically the password-handling branch of `migrateBog()`/`encodeBog()`, which neither [B14] nor [B24]
  read line-by-line.
- **[Block 24]** — §47.1 CORRECTS §24.3's characterization of `encodeBog()` as performing "AES-256/keyring
  password re-encoding" (it cannot — by the time it runs, `keyring`-mode values are already cleared); §47.4
  extends §24.6's PANCCADIA cross-check with the actual `EncryptionKeySource` mode and `BPassword` slot
  count, information B24 did not extract (B24 counted `t=` PREFIXES by module abbreviation, not by
  `Password`-family type name, and did not open the header's `reversibleEncodingKeySource` attribute).
- **[Block 19]** — §19.1's `config.bog` header-attribute grammar is the exact header this block's §47.4
  reads a live value FROM for the first time in either corpus.
- **[Block 34]** — §34.1's subscription-secret KeyRing aliases (`baja.licensing.subscription.*`) are, per
  that block, `BAliasedAes256PasswordEncoder`-shaped (self-describing alias in the wire format, §47.2's
  table) — NOT subject to this block's §47.2 default-encoder failure mode; flagged here only to avoid a
  reader conflating the two encoder families.

## Self-verify

```
marker tally (LITERAL `grep -o '\[CERT\]'`/`grep -o '\[INFER\]'` count against this file as saved, run
after the prose was written, this session — not hand-recalled):
  RAW whole-file [CERT]   : 21
  RAW whole-file [INFER]  : 13
  body-only (everything above "## Self-verify", i.e. excluding this section's own meta-discussion of the
    tally, which — per METHODOLOGY §11's RAW-vs-ADJUSTED guidance — inflates the raw count by quoting the
    marker tokens themselves rather than making fresh claims):
    [CERT]  : 18   [INFER] : 8
  body-only, further excluding the header blockquote's marker-legend prose (lines quoting `` `[CERT]` ``/
    `` `[INFER]` `` to DEFINE the convention, not to back a claim — 1 CERT legend line + 1 cross-block
    meta-reference "a different block's [CERT]", 2 INFER legend/negative-existence-rule-explanation lines):
    ADJUSTED [CERT]  : 16   ADJUSTED [INFER] : 6
ratio [INFER]/[CERT] (adjusted) = 6/16 ≈ 0.38 — moderate-to-high, consistent with an evidence block whose
  central finding required opening ~14 previously-unread classes fresh this session (§47.1-§47.3), with
  `[INFER]` held to exactly the two places evidence genuinely ran out: §47.3's absence-of-call-site
  negative claim (mechanically downgraded per METHODOLOGY §3's negative-existence rule — a `grep`-based
  "not found" is never `[CERT]`) and §47.3's "vestigial machinery, purpose unconfirmed" interpretive
  framing around it. Every other conclusion in the block (§47.1's unconditional-clear finding, §47.2's
  alias/wire-format asymmetry, §47.4's PANCCADIA mode/count) is a direct read of an opened primary source.
[CERT] file:line citation resolution: 0 resolved by an automated SOURCE_ROOT-relative scan — every citation
  points into organized/*/vineflower/ (decompiled trees), outside this repo's SOURCE_ROOT, OR into the
  session scratchpad's unzipped config.bog copy. Declared per METHODOLOGY §11's decompiled-tree rule:
  citation gate = inline token-verify (below), not the automated resolver. `verify-block.sh` was not run
  (not available in this session's invocation context, consistent with [B14]/[B24]/[B43]'s own precedent
  in this corpus).
```

**Inline token-verify** (fresh `grep -n`/`sed -n` re-checks performed this session, after the block's prose
was written, against the exact files cited above):

```
BBogMigrator.java:418   } else if (bogFile.usesKeyRingEncryption()) {                          ✓
BBogMigrator.java:423   LOG.severe(LEX.getText("migrate.breakKeyringEncoding", ...));           ✓
BBogMigrator.java:449-457  EncryptionKeySource keySource = !isPalette && AxPasswordUtil...      ✓
migrator.lexicon:161    migrate.breakKeyringEncoding=Detected that the source used keyring...   ✓
BBogFile.java:125       PasswordUtil.forceClearReversiblePasswords(...)                         ✓
BBogFile.java:433       return this.bogPasswordObjectEncoder.getKeySource().equals(...keyring); ✓
PasswordUtil.java:250   return BPassword.DEFAULT;                                               ✓
BAes256PasswordEncoder.java:27       this.keyAlias = "niagara.security.BAes256PasswordEncoder.key"; ✓
BAliasedAes256PasswordEncoder.java:43  this.keyAlias = data[0];                                 ✓
Aes256PasswordManager.java:23   return new Aes256PasswordManager(kr, "niagara.security.BAes256PasswordEncoder.key"); ✓
Aes256PasswordManager.java:228  key = this.kr.createKey(keyName, false);                        ✓
Aes256PasswordManager.java:143  byte[] passwordBytes = aesCipher.doFinal(cipher);                ✓
Migrate.java:99         private static AESDecryptFunction passwordDecryptFunction;              ✓ (and
                         grep -c "passwordDecryptFunction" Migrate.java = 1, re-confirmed)
BBackupDistMigrator.java:38   security/.kr" among DIRS_TO_EXTRACT literals                       ✓
BBackupDistMigrator.java: grep -c "new LazyDecryptFunction\|new BBackupDistMigrator.LazyDecryptFunction" = 0 ✓
config.bog (PANCCADIA) header: reversibleEncodingKeySource='external'                            ✓
config.bog (PANCCADIA): grep -oc 't="b:Password"' = 3                                            ✓
```

All 16 spot-checked tokens re-confirmed present at the cited location this session. No hallucinated
citation found.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; every source is a local decompiled
`.java` file, a local `.lexicon` text file, or the local gitignored `config.bog` copy, all opened directly
this session.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block47.md`. Per the
caller's explicit read-only instruction, this task touches no other file — `INDEX.md`/`RESEARCH-STATE.md`/
`CATALOG.md` regeneration and gap-backlog re-classification (B43-G1 → closed for the `.bog`-level question;
new B47-G1/B47-G2/B47-G3 opened) are left to the orchestrator. No `git commit` performed. PANCCADIA
`config.bog` was read read-only from its existing gitignored location; the only new file this session wrote
is the scratchpad unzip at `/tmp/claude-1000/.../scratchpad/b47/extracted/file.xml` (session-scratch, not
part of the corpus, not committed).
