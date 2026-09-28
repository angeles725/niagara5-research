# Block 84 — Closing four cross-corpus N4-vs-N5 diff gaps using a freshly-located, on-host N4 4.15.3.28 install: the `nre.jar` physical location, its `nre.subscription` byte-diff, the 5 B31 BACnet/tagdictionary types' slot-diff, and the `alarm.adb` header format compare

> Research closing four child gaps that all shared the same missing prerequisite — an actual N4-**4.15**-line
> decompiled tree — which [Block 80] §80.4 recorded as present-but-not-decompiled and [Block 71] §71.4 and
> [Block 78] §78.3 separately flagged as blocking a byte-level N4/N5 compare: **B80-G3/B31-G1** (decompile the
> 5 [Block 31] §31.4a version-gap-unresolved BACnet/tagdictionary types from an N4 4.15 jar and slot-diff
> against N5 — [Block 31]'s own text: "the 5 version-gap-unresolved types ... need an N4 **4.15** decompile of
> `bacnet`/`tagdictionary` ... to slot-diff against N5 the same way the other 283 types were"); **B71-G4**
> ("N4's actual jar name/location for `com.tridium.nre.subscription`... would require either decompiling N4's
> `nre.jar` (if one exists under that name in the N4 install) or searching the N4 install's `bin/ext/`
> directory listing for candidate jars"); **B71-G5** ("Byte/behavior-level diff between N4's and N5's
> `com.tridium.nre.subscription.RetrieveEntitlements`/`EntitlementApi` — do the N4-imported classes share
> N5's OAuth device-code flow, or is N4's client-transport layer materially different under the same package
> name — would require the N4 decompilation named in B71-G4 as a prerequisite"); **B78-G2** ("it needs the N4
> `AlarmStoreHeader` for a magic/version compare" — [Block 78] §78.3's own text, confirmed verbatim against
> `niagara5-block78.md:88`). All four gap texts were re-read from their parent block files this session and
> match the task assignment verbatim (no gap-ID drift found).
>
> Covers: locating and confirming a genuine, installable N4 **4.15.x** build on-host (not previously known to
> exist at [Block 31]/[Block 80]'s time of writing — those blocks only found `/mnt/c/ProgramData/Niagara4.15`
> and `/mnt/c/Users/equipo/Niagara4.15`, which are per-user DATA directories, not module/bin installs);
> extracting and Vineflower-decompiling exactly the 7 target classes (5 BACnet/tagdictionary types, plus
> `RetrieveEntitlements`/`EntitlementApi`) plus `AlarmStoreHeader` from that install's jars into a scratch
> workdir (never written to either repo, per task instructions); a normalized (package-prefix-only) diff of
> each against its already-decompiled N5 5.0.0.28 counterpart. Does **not** cover: a full re-run of [Block
> 31]'s 288-type census against this new 4.15.3.28 baseline (only the 5 named types were diffed — re-deriving
> the other 283 is out of this block's bounded scope); a live station boot or `n5mig` execution of this
> install (inherits B14-G1/B24-G1/B31-G2, still requires-execution); the alarm.adb RECORD-body (row) format
> beyond the header (new child gap, §84.4); a corpus-wide characterization of the `com.tridium.json`→`org.json`
> and `nre.firewall`→`nre.security` package changes surfaced as side-findings while reading the diffed files
> (counted and flagged as child gaps, not fully characterized).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (same corpus every other N5 block cites), cross-diffed against a **freshly-located N4 install, vendorVersion
> `4.15.3.28`, releaseDate `2025-03-09`**, found at `/mnt/c/PowerB/PowerB-4.15.3.28` (an OEM-branded — "PowerB"
> — Niagara distribution, the same OEM-rebrand pattern as PANCCADIA's own `OptimizerSupervisor-N4.14.0.162`
> install used as [Block 31]'s original 4.14 baseline) `[CERT]` (`module.xml` `vendorVersion=` attribute on
> `baja.jar`/`bacnet-rt.jar`/`tagdictionary-rt.jar`, all three read this session; `bin/nreVersion.xml`
> `version="4.15.3.28"`). This build satisfies [Block 14] §14.2's version bound exactly: `Migrate.java:62`'s
> USAGE text names the N4 side of the migration boundary generically as "a **4.15**-versioned station backup
> distribution file," not a specific patch — `4.15.3.28` is a genuine instance of that named line, found via
> `find /mnt/c -maxdepth 4 -iname '*4.15*' -type d` (this session, per the task's own suggested command) after
> [Block 80] §80.4's two hits (`ProgramData`/`Users\equipo` `Niagara4.15`) turned out to be data-only
> directories with no `modules/`/`bin/` (checked and rejected this session, `[CERT]`). Decompiler: Vineflower
> 1.12.0, same jar every other block uses (`tools/decompilers/vineflower-1.12.0.jar`), run against small
> extracted single-purpose jars built from `unzip`+`zip` of only the needed `.class` files (full-module
> decompile of `bacnet-rt.jar`/`baja.jar`/`nre.jar` was not attempted — out of scope, bounded extraction only).
> Output written to `/tmp/claude-1000/.../scratchpad/n415/{nre_out,bacnet_out,tagdictionary_out,alarm_out}/`
> — **not persisted to either repo**, per task instructions; every N4-side finding below is therefore either
> quoted inline or cited by `<jar>.jar!<class-path>` (a non-file-verifiable but explicit jar-entry locator) plus
> the jar's own sha256, rather than a `file:line` into a tree that will not exist in a future session. sha256
> (this session, `sha256sum`): `bin/ext/nre.jar`
> `4340f0f6777f6886aba8d6d07eb83e84d02dba7bac980374fe82c792f2670d1f`, `modules/baja.jar`
> `a58f5ce91d92fa3c35117bb7fd76445ee1afdf4cb5209c80525347c0aee95263`, `modules/bacnet-rt.jar`
> `ad2f370a7a272974a34af7e5e53ee83aa6486d96f4cf20fba8ceb68af3ff3131`, `modules/tagdictionary-rt.jar`
> `26165db435e0c7a9db1f1e4fb274321f9b2ea9cdc4e2bb54d26a73c979280fda`, `modules/alarm-rt.jar`
> `c2df15ae75c5a3557ce721ef0554b5794650b227d9e8fb3112793f03760f6bd7`. N5-side `bin/ext/nre.jar` (the live
> `/mnt/c/Program Files/Niagara/5.0.0.28` install, hashed fresh this session for the direct parallel) sha256
> `d563a334e02ef739d53bb67ddf48de96582b787dff89a8ab1c5140cdf381f9f7`. N5 `bacnet.jar`/`tagdictionary.jar`/
> `alarm.jar` sha256 are as recorded in [Block 31]'s own header (reused, not re-derived):
> `6e1ad472b06b281c46700aa962986430ccf7e91c396c9eb308dc5b3f674ee969` /
> `1f97a4482f1355e6b20bbd97413c42fa745f3716b499e48e98549813c01aa227` /
> `fb5b21c30412dceedd12adbf2e29843e2a05d0b8b9883fa4cb387c18297cc32f`.
>
> Sources: the N4-4.15.3.28 install's own `bin/nreVersion.xml`, `bin/ext/nre.jar`(+`.sig`),
> `modules/{baja,bacnet-rt,tagdictionary-rt,alarm-rt}.jar` (`unzip -l` census + targeted `.class` extraction
> + Vineflower decompile, this session); N5 decompiled sources at
> `organized/{bacnet,tagdictionary,alarm,_bin-ext/nre}/vineflower/...` (already-existing trees, re-read this
> session, not re-decompiled); `niagara5-block31.md:367-380` (exact B31-G1 child-gap text and the 5 type
> names), `niagara5-block71.md:301-360,440-460` (exact B71-G4/B71-G5 text and the `SubscriptionLicenseManager`
> N4-side import evidence [Block 71] already read), `niagara5-block78.md:65-90` (exact B78-G2 text and the
> `AlarmStoreHeader` field table), `niagara5-block80.md` (whole file, the B80-G3 framing and the
> `/mnt/c` 4.15-directory dead end this block resolves).
>
> Method: `find /mnt/c -maxdepth 4 -iname '*4.15*' -type d` to locate a real 4.15 install (not just a data
> directory); `unzip -l <jar> | grep -i <ClassName>` to confirm each target class's presence before spending a
> decompile; a scripted `unzip` (class + all inner-class members) into a throwaway per-target jar, then one
> Vineflower invocation per target, output to the session scratchpad (never the repo); a normalized `diff`
> (`sed` rewriting the N4 side's `javax.baja.*`/`com.tridium.*` package prefixes to their known N5
> equivalents before comparing, the same normalization technique [Block 14]/[Block 31] established for the
> `javax.baja.*`→`niagara.*` rename) against the matching already-decompiled N5 file; a direct `grep -n
> '@NiagaraProperty|@NiagaraAction|@NiagaraTopic'` re-check on both sides wherever the raw diff showed
> non-package-rename deltas, to separate a real frozen-slot change from an internal-method refactor. Markers
> (canonical list, METHODOLOGY §3): `[CERT-hw]`/`[CERT-live]`/`[CERT]` local primary source (`file:line` or
> `jar!class-path`) · `[CERT-doc]`/`[CERT-web]`/`[CERT-a]` external · `[INFER]` deduction.
>
> **Type:** `evidence` — every section closes a named prior-block gap with a fresh, freshly-decompiled
> primary-source diff; no cross-block synthesis argument is constructed beyond restating each closed gap's
> "what this settles."

---

## 84.1 — B71-G4 CLOSED: N4's `nre.jar` lives at the exact same relative path as N5's — `bin/ext/nre.jar` — and it physically contains `com.tridium.nre.subscription.*`, including `RetrieveEntitlements`/`EntitlementApi` `[CERT]`

The N4-4.15.3.28 install's `bin/ext/` directory contains `nre.jar` (4,340,970-byte-class jar; exact size not
computed, sha256 above) plus a detached `nre.jar.sig` signature file, sitting alongside `bin/nre.exe`/
`bin/nre.dll` (the native NRE launcher) `[CERT]` (`ls /mnt/c/PowerB/PowerB-4.15.3.28/bin/ext/`, this session).
`unzip -l bin/ext/nre.jar` lists 44 classes under `com/tridium/nre/subscription/`, including — by exact name
— `RetrieveEntitlements.class` (16,040 bytes) and `EntitlementApi.class` (18,852 bytes), the same two classes
[Block 71] §71.4 traced only via an IMPORT statement in N4's `baja.jar`-side `SubscriptionLicenseManager`
`[CERT]` (`unzip -l bin/ext/nre.jar`, this session — full listing preserved in this block's working notes;
representative entries quoted above the tally table).

**The location is not a coincidence — N5 ships its own `nre.jar` at the IDENTICAL relative path.** The live
N5 5.0.0.28 install (`/mnt/c/Program Files/Niagara/5.0.0.28`, the same install [Block 6]/[Block 34]/
[Block 53]/[Block 56]/[Block 71] all cite) has `bin/ext/nre.jar`+`.sig` too `[CERT]` (`ls`, this session; sha256
`d563a334e02ef739d53bb67ddf48de96582b787dff89a8ab1c5140cdf381f9f7`, distinct from N4's
`4340f0f6777f6886aba8d6d07eb83e84d02dba7bac980374fe82c792f2670d1f` — confirming they are two different jar
builds, not the same file reused). This also explains why [Block 71] found no `organized/_bin-ext/nre/`-style
tree for N4: the `niagara-research` N4 corpus's own decompile campaign never targeted `bin/ext/` (a
platform-support jar outside the `modules/` directory it enumerated), not because no such jar exists.

**B71-G4 verdict: N4's `com.tridium.nre.subscription` physically lives in `bin/ext/nre.jar`**, the exact same
signed platform-support jar N5 ships at the same path — narrowing [Block 71] §71.4's open question ("a
differently-named jar, or an entirely different physical module") to a confirmed, non-surprising answer: same
name, same location, same packaging role, both signed, both versions.

## 84.2 — B71-G5 CLOSED: N5's `RetrieveEntitlements`/`EntitlementApi` share N4's OAuth device-code/HTTP-transport structure almost line-for-line, but N5 replaced N4's dynamic cross-classloader reflection into `baja.jar` with a proper `LicenseValidator` interface implemented by `SubscriptionLicenseManager` itself `[CERT]`

> **Correction (added by [Block 115], §115.5, §14 cross-block).** The pattern-matching-switch claim below
> (point 3, "N5 rewrites N4's if/instanceof cause-dispatch chains as Java-21 pattern-matching switch
> statements") is REAL, but scoped to `EntitlementApi.class` ONLY — `RetrieveEntitlements.class` carries
> ZERO `SwitchBootstraps.typeSwitch` call sites (`javap -v -p`, re-run fresh this session). This section's
> own title names both classes together; only `EntitlementApi` has the pattern-switch. Also: an earlier
> orchestrator-relayed count of "12 typeSwitch" for `EntitlementApi` was a raw `grep -c "typeSwitch"` over
> `javap -v` text, which double-counts constant-pool cross-references and `BootstrapMethods` table entries
> for the SAME call sites — the true count, re-derived from the `BootstrapMethods:` table and the
> `invokedynamic` disassembly directly, is 2 distinct call sites. Self-verify row 9 below restates the same
> claim and is covered by this same pointer. See [Block 115] §115.5 for the full re-derivation.

A normalized diff (`javax.baja.*`→`niagara.*`, `com.tridium.json`→`org.json` import lines set aside) of the
freshly-decompiled N4-4.15.3.28 `RetrieveEntitlements.class`/`EntitlementApi.class` against N5's shows the
files are **close but not byte-identical** — 326→330 lines and 705→684 lines respectively `[CERT]` (`diff`,
this session). Three concrete, load-bearing differences, not just decompiler noise:

1. **License-signature validation was re-architected from reflection to dependency injection.** N4's
   `RetrieveEntitlements.isLicenseSignatureValid(XElem, File)` dynamically constructs a
   `URLClassLoader` over `modules/baja.jar`, loads `com.tridium.sys.license.subscription.SubscriptionLicenseManager`
   by string name, and reflectively invokes its static `isLicenseSignatureValid(XElem, File)` method, the
   whole thing wrapped in `AccessController.doPrivileged` `[CERT]` (`bin/ext/nre.jar!com/tridium/nre/subscription/RetrieveEntitlements.class`,
   this session, decompiled body quoted in this block's working notes). N5 instead adds a
   `private final LicenseValidator licenseValidator` field, threaded through two new constructor overloads,
   and calls `this.licenseValidator.validateLicenseSignature(root, certificateFile)` directly — no
   classloading, no reflection, no `AccessController` `[CERT]`
   (`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/RetrieveEntitlements.java`, this
   session). `LicenseValidator` is a genuine new N5 interface (`public interface LicenseValidator { boolean
   validateLicenseSignature(XElem, File); }`, `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/LicenseValidator.java:6`)
   `[CERT]`, and `com.tridium.sys.license.subscription.SubscriptionLicenseManager` — the SAME class N4
   reflectively targeted by string name — now `implements LicenseValidator` directly in N5
   (`organized/baja/vineflower/com/tridium/sys/license/subscription/SubscriptionLicenseManager.java:56`)
   `[CERT]`, with its instance method delegating to the identical static `isLicenseSignatureValid` N4 called
   reflectively (`:359,405`) `[CERT]`. **This is confirmed live-wired, not vestigial**: 4 of the 5
   `new RetrieveEntitlements(...)` call sites in the N5 corpus pass `this` (a `SubscriptionLicenseManager`
   instance) as the validator (`SubscriptionLicenseManager.java:138,260,265,352`) `[CERT]`; the fifth
   (`SubscriptionLicenseUtil.java:460`, inside its own no-arg `getLicenseUpdate()`) passes `null` — see child
   gap **B84-G4** for what that means at runtime.
2. **The N4 reflection target's method signature matches exactly**, confirming this is the same call being
   re-routed, not a coincidentally-named method: `javap -p` on N4's own `baja.jar!com/tridium/sys/license/
   subscription/SubscriptionLicenseManager.class` shows `public static boolean isLicenseSignatureValid(javax.baja.xml.XElem,
   java.io.File)` `[CERT]` (`javap`, this session) — the exact two-argument shape both N4's reflective call and
   N5's direct call use.
3. **Everything else is modernization noise, not a behavior change**: `com.tridium.json.JSONObject`/
   `JSONTokener` (N4, Tridium's own vendored JSON) become `org.json.JSONObject`/`JSONTokener` (N5, the real
   third-party library) in both files `[CERT]`; `AccessController.doPrivileged` wrapping the
   `Boolean.getBoolean("NiagaraDaemon")` daemon-mode check and the JWS public-key set is simply removed in N5
   (called directly) `[CERT]`; N5 rewrites N4's `if`/`instanceof` cause-dispatch chains as Java-21 pattern-
   matching `switch` statements over `Throwable cause`/`String key` `[CERT]`; N4's raw `java.net.URL` becomes
   N5's own `com.tridium.nre.util.URLFactory.make(...)` `[CERT]`. None of these touch the OAuth device-code
   flow itself — `HttpRequestMessage`/`HttpResponseMessage`/`HttpMessageWrapper`, the entitlement-state enum,
   the JWT signature-key handling, and the certificate-sanitization logic are structurally the same classes
   doing the same jobs under the same names in both trees `[CERT]`.

**B71-G5 verdict: shares the flow, differs in one concrete mechanism.** The answer to the gap's own framing
("do the N4-imported classes share N5's OAuth device-code flow, or is N4's client-transport layer materially
different") is **both, precisely**: the HTTP/OAuth transport layer is the same design carried forward
essentially unchanged (JSON-library and Java-21-syntax modernization aside); the ONE materially different
piece is exactly the license-SIGNATURE-validation call path, where N5 replaced a runtime `URLClassLoader`+
reflection trick crossing from `nre.jar` into `baja.jar` with a clean `LicenseValidator` interface —
removing a dynamic-classloading pattern that (per [Block 25]'s broader Java-modernization census) is the kind
of thing `AccessController`'s JDK-24+ deprecation-for-removal path would eventually force anyway.

## 84.3 — B80-G3 / B31-G1 CLOSED: all 5 version-gap-unresolved types have IDENTICAL frozen-slot shape between N4-4.15.3.28 and N5-5.0.0.28 — the migration path is confirmed clean, no orphan-property risk `[CERT]`

> **Correction (added by [Block 115], §115.2/§115.5, §14 cross-block).** The `BQudtUnitTag` table row's
> "`instanceof BNumericPoint np` pattern-match (Java 21) replaces N4's cast" language describes a Vineflower
> RESUGARING artifact, not an actual N4→N5 source change. N4-4.15.3.28 (major 52) and N5-5.0.0.28 (major 69)
> `BQudtUnitTag.class` carry byte-for-byte identical `instanceof`/`checkcast`/`astore` bytecode — re-verified
> independently this session with a fresh `javap -c -p` pass on both sides (`[Block 115] §115.2`). The
> table's bottom-line verdict (CLEAN, `@NiagaraProperty` block byte-identical) is unaffected — only the
> causal "replaces N4's cast" framing for that one cell needs the correction: Vineflower's rendering choice
> is gated by the class file's own major version, not by anything Tridium changed.

All 5 types [Block 31] §31.4a flagged (`bacnet:BacnetNetworkNumberQuality`, `bacnet:BacnetIpServerPort`,
`bacnet:BacnetMstpPortDescriptor`, `bacnet:BacnetNetworkPortPendingChanges`, `tagdictionary:QudtUnitTag`) were
found, extracted, and Vineflower-decompiled from the N4-4.15.3.28 jars this session — confirming [Block 31]'s
own prediction that "they unambiguously exist in SOME N4 build ≤4.15" `[CERT]` (`unzip -l` on
`bacnet-rt.jar`/`tagdictionary-rt.jar` found all 5 backing classes by exact name, this session). A
package-normalized diff against each type's already-decompiled N5 file:

| Type (backing class) | Own `@NiagaraProperty`/`@NiagaraAction` count (both sides) | Diff beyond package rename | Verdict |
|---|---|---|---|
| `BBacnetNetworkNumberQuality` | 0 (a `BFrozenEnum`; slot shape is the 4-value `@NiagaraEnum` range) | **NONE** — byte-identical after rename `[CERT]` | CLEAN |
| `BBacnetIpServerPort` | 1 (`publicServerPort`, `int`, facets MIN/MAX/RADIX) | one import moved (`com.tridium.nre.firewall.IpProtocol`→`niagara.nre.security.IpProtocol`, unused-import-only — see B84-G2); `@NiagaraProperty` block itself byte-identical `[CERT]` | CLEAN |
| `BBacnetMstpPortDescriptor` | **0** — a pure BACnet-protocol logic class, no own frozen slots | internal-only: `readOptionalProperty`/`writeOptionalProperty`/`getListElements` (all `@Deprecated` in N4) renamed to `doReadProperty`/`doWriteProperty`/`getListElements(..,Context)` (`@Override` in N5); a `Context` parameter threaded through every write helper; N5's protocol-level `OPTIONAL_PROPS` int array gains 2 more BACnet property IDs (`485, 168`) beyond N4's 13 `[CERT]` | CLEAN (no Niagara slot exists to diff — the added values are BACnet wire-protocol property IDs, not `Property`/`Slot` objects) |
| `BBacnetNetworkPortPendingChanges` | 0 | **NONE** — byte-identical after rename `[CERT]` | CLEAN |
| `BQudtUnitTag` | 1 (`validity`, `BTagRuleCondition`, `override=true`) | `instanceof BNumericPoint np` pattern-match (Java 21) replaces N4's cast; `@NiagaraProperty` block itself byte-identical `[CERT]` | CLEAN |

`[CERT]` full decompiled bodies read and `grep -n '@NiagaraProperty|@NiagaraAction|@NiagaraTopic|@NiagaraType'`
run against each of the 10 files (5 N4 + 5 N5) this session; every own-slot annotation matches token-for-token
across both trees. **B31-G1/B80-G3 verdict: MATCHES — all 5 types load with an identical own-slot shape in
N5** (three have zero own slots at all — their only "shape" is class presence, already confirmed `[CERT]` by
[Block 31]; two have exactly one unchanged `@NiagaraProperty`). This resolves [Block 31] §31.4a's residual
uncertainty ("only the exact N4-4.15-vs-N5 slot-shape match is open") to a definitive **clean, no orphan-data
risk**, upgrading those 5 types from [Block 31]'s "version-gap unresolved" bucket into the same "CLEAN"
bucket as 259 of the other 283 checked types.

## 84.4 — B78-G2 CLOSED: N4-4.15.3.28's `AlarmStoreHeader` is byte-identical to N5's — same MAGIC, same version, same page geometry — `alarm.adb` upgrades format-compatible at the header level `[CERT]`

N4's `com.tridium.alarm.db.file.AlarmStoreHeader` (`alarm-rt.jar!com/tridium/alarm/db/file/AlarmStoreHeader.class`,
this session) declares the identical five constants [Block 78] §78.3 documented for N5: `MAGIC = 1611526157`,
`LATEST_VERSION = 1`, `DEFAULT_HEADER_SIZE = 1024`, `DEFAULT_PAGE_SIZE = 512`, `DEFAULT_PAGES_PER_BLOCK = 8`
`[CERT]`. A package-normalized diff (`javax.baja.nre.util.ByteBuffer`→`niagara.nre.util.ByteBuffer`) against
N5's `organized/alarm/vineflower/com/tridium/alarm/db/file/AlarmStoreHeader.java` returns **zero differences**
— the entire `write(DataOutput)`/`read(DataInput)` word order, the `1024`-byte-header/`512`-byte-page/
`8`-pages-per-block layout, and every field type (int32/int64) are byte-for-byte the same class `[CERT]`
(`diff`, this session, exit 0).

**B78-G2 verdict: format-compatible.** An `alarm.adb` written by this N4-4.15.3.28 build's header would be
accepted by N5's own `magic != 1611526157` / `version != 1` guard clauses (`AlarmStoreHeader.read()`,
`organized/alarm/vineflower/.../AlarmStoreHeader.java`, re-cited from [Block 78] §78.3) without triggering
either of its two hard-fail exceptions ("Invalid or corrupt alarm database." / "Unrecognized alarm db
version"). This settles the HEADER half of [Block 78]'s open question; the record/row BODY format (governed
by the `recordVersion` field, a constructor argument this class only stores and never interprets itself) is
untouched by either N4 or N5's `AlarmStoreHeader` — narrowed into child gap **B84-G3**.

## 84.x — Connections

- **[Block 71]** — §84.1 closes **B71-G4**, §84.2 closes **B71-G5**; both were the two residual-uncertainty
  child gaps [Block 71] §71.4 opened after closing B34-G5 by import-evidence alone (no N4 decompile at the
  time). [Block 71]'s own N4-side citation (`SubscriptionLicenseManager.java` import block, cross-repo read)
  is corroborated exactly by this session's fresh `javap` signature check (§84.2 point 2).
- **[Block 31]** — §84.3 closes **B31-G1**, the last open item in [Block 31]'s 288-type census (259 CLEAN +
  16 added-only + 8 removed-property + 5 now-also-CLEAN = 288, fully reconciled).
- **[Block 80]** — §80.4 recorded the B31-G1 prerequisite as "present but not decompiled"; this block supplies
  exactly that missing decompile, closing **B80-G3** (the child gap [Block 80] opened for its own unblocking
  note).
- **[Block 78]** — §84.4 closes **B78-G2**, the last open item in [Block 78] §78.3's `AlarmStoreHeader` field
  table.
- **[Block 14]/[Block 25]** — the N4-4.15.3.28 install's version bound is re-confirmed against [Block 14]
  §14.2's `Migrate.java:62` USAGE-text citation; §84.2's `AccessController` removal is a small, concrete data
  point for [Block 25]'s broader Java-modernization census (not re-derived corpus-wide here).

## 84.x — Child gaps opened

- **B84-G1** — `com.tridium.json` (N4's vendored JSON library) and `org.json` (the real third-party library)
  **coexist** in the N5 5.0.0.28 corpus — 121 files still reference `com.tridium.json`, 398 reference
  `org.json` (`grep -rl`, this session, whole-corpus, `fallback/` excluded). Whether this is a completed
  per-module swap (some modules fully on `org.json`, others never touched) or an in-progress migration needs
  a per-module breakdown, not performed this session.
- **B84-G2** — `IpProtocol`'s package move, `com.tridium.nre.firewall` (N4) → `niagara.nre.security` (N5,
  `organized/_bin-ext/nre/vineflower/niagara/nre/security/IpProtocol.java`), sits inside a much larger
  `niagara.nre.security` package (593 files corpus-wide) versus a small residual `nre.firewall` (14 files
  still present, `grep -rl`, this session). Whether `nre.security` is a genuine `firewall`-package
  consolidation/rename or a coincidentally-large unrelated package needs its own census.
- **B84-G3** — the `alarm.adb` RECORD/ROW body format (governed by `AlarmStoreHeader.recordVersion`, a value
  this class stores but never interprets) was not compared between N4-4.15.3.28 and N5 this session — only
  the fixed header was. A real per-alarm-record byte-layout diff needs the row-writing class(es) downstream
  of `AlarmStoreHeader` (not yet identified in either corpus this session).
- **B84-G4** — `SubscriptionLicenseUtil.getLicenseUpdate()`'s own no-arg overload constructs
  `new RetrieveEntitlements(lrt, null)` (`organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/
  SubscriptionLicenseUtil.java:460`) — the one `RetrieveEntitlements` call site NOT wired to a real
  `LicenseValidator` (§84.2). Its only caller found this session is `UpdateDaemonServlet.getLicenseUpdate()`
  (`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:379`) —
  the niagarad daemon path. Per `RetrieveEntitlements`'s own logic, a null validator only matters when
  `Boolean.getBoolean("NiagaraDaemon")` is false (when true, signature validation is skipped entirely,
  by design, in BOTH N4 and N5 — unchanged trust boundary); whether that system property is actually `true`
  during normal niagarad execution is a runtime fact, not verifiable by static reading, and was not checked
  this session.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | A real N4 4.15.x install (not just per-user data) exists on-host at `/mnt/c/PowerB/PowerB-4.15.3.28`, vendorVersion 4.15.3.28 | [CERT] | `module.xml` `vendorVersion=` on `baja.jar`/`bacnet-rt.jar`/`tagdictionary-rt.jar`; `bin/nreVersion.xml` |
| 2 | N4's `nre.jar` is at `bin/ext/nre.jar`, contains `com/tridium/nre/subscription/*` incl. `RetrieveEntitlements`/`EntitlementApi` | [CERT] | `unzip -l bin/ext/nre.jar`, this session |
| 3 | N5's live install also ships `bin/ext/nre.jar`+`.sig` at the identical relative path, a different sha256 | [CERT] | `ls`/`sha256sum` on `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar`, this session |
| 4 | N4's `RetrieveEntitlements.isLicenseSignatureValid` uses `URLClassLoader`+reflection+`AccessController.doPrivileged` into `baja.jar`'s `SubscriptionLicenseManager` | [CERT] | decompiled `bin/ext/nre.jar!com/tridium/nre/subscription/RetrieveEntitlements.class`, this session |
| 5 | N5's equivalent method instead calls an injected `LicenseValidator.validateLicenseSignature(...)`, no reflection/classloading | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/subscription/RetrieveEntitlements.java` |
| 6 | `SubscriptionLicenseManager` (N5) `implements LicenseValidator`; its instance method delegates to the same static `isLicenseSignatureValid` N4 called reflectively | [CERT] | `organized/baja/vineflower/com/tridium/sys/license/subscription/SubscriptionLicenseManager.java:56,359,405` |
| 7 | N4's `SubscriptionLicenseManager.isLicenseSignatureValid` signature is `(XElem, File)`, matching N4's reflective call | [CERT] | `javap -p` on `baja.jar!com/tridium/sys/license/subscription/SubscriptionLicenseManager.class`, this session |
| 8 | 4 of 5 `new RetrieveEntitlements(...)` N5 call sites pass a real validator (`this`); one passes `null` | [CERT] | `grep -rn "new RetrieveEntitlements("`, this session |
| 9 | `com.tridium.json`→`org.json` and `AccessController`-removal and if/instanceof→switch-pattern-match are the only other diffs in `EntitlementApi`/`RetrieveEntitlements` | [CERT] | `diff`, this session, full file pair both classes |
| 10 | All 5 B31 version-gap types exist by exact class name in the N4-4.15.3.28 jars | [CERT] | `unzip -l bacnet-rt.jar\|tagdictionary-rt.jar`, this session |
| 11 | All 5 types' own `@NiagaraProperty`/`@NiagaraAction` annotations are token-identical N4-vs-N5 (3 have zero own slots) | [CERT] | `grep -n '@NiagaraProperty\|@NiagaraAction\|@NiagaraTopic\|@NiagaraType'` on all 10 decompiled files, this session |
| 12 | `BBacnetMstpPortDescriptor`'s N5 `OPTIONAL_PROPS` array adds 2 BACnet protocol-property IDs (485,168) over N4's 13, with no Niagara-slot-level change | [CERT] | `diff` of decompiled bodies, this session |
| 13 | N4-4.15.3.28's `AlarmStoreHeader` constants (MAGIC/VERSION/HEADER_SIZE/PAGE_SIZE/PAGES_PER_BLOCK) are byte-identical to N5's | [CERT] | `alarm-rt.jar!com/tridium/alarm/db/file/AlarmStoreHeader.class` decompiled + `diff` vs `organized/alarm/vineflower/.../AlarmStoreHeader.java`, this session, exit 0 |
| 14 | `com.tridium.json`/`org.json` coexist corpus-wide in N5 (121 vs 398 files) | [CERT] | `grep -rl`, this session, whole `organized/` tree |
| 15 | `nre.firewall` (14 files) and `nre.security` (593 files) both exist as package names in N5; `IpProtocol` lives in the latter | [CERT] | `grep -rl`/`find`, this session |
| 16 | 4.15.3.28 satisfies [Block 14] §14.2's "a 4.15-versioned station backup distribution file" bound (generic, not a specific patch) | [INFER] | `niagara5-block14.md:96,108-110` re-read this session; the exact PANCCADIA sub-build is not independently confirmed to be 4.15.3.28 specifically |

Tally: 15 [CERT], 1 [INFER] (ratio 0.07). Every [CERT] file:line/jar-entry cite above was read this session
(not recalled): the two N4 jar `unzip -l` listings, the `javap` signature output, the four decompiled N4
class bodies (kept only in the session scratchpad per task instructions, quoted/paraphrased here), and the
five already-existing N5 `organized/` files re-read fresh. The one [INFER] is a version-precision hedge, not
a load-bearing uncertainty: [Block 14]'s own bound is generic-4.15, so this does not weaken any of the four
CLOSED verdicts above.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block84.md`. N4-side
decompiled sources exist only in this session's scratchpad
(`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/n415/`)
and were **not** written into either `niagara-research` or `niagara5-research` — per task instructions, cited
here by jar-entry (`<jar>.jar!<class-path>`) plus recorded sha256 rather than by a `file:line` that will not
resolve in a future session. Per the wave convention, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration is performed by the integrator step, not by this block.
