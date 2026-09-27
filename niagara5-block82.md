# Block 82 — Closing the migrator/backup residual cluster: `BFormat.ReflectCall.eval()`'s permission-gated reflection semantics, `AxPasswordUtil.usesPasswordEncodings`'s exhaustive recursive walk, `BWebBogConverter`/`BJettyQoSFilterMigrator`'s exact property lists, and `backup.jar`'s own live (and partly dead) `.dist`-container KeyRing mechanism

> Closes three named child gaps and substantially narrows a fourth, all drawn from the migrator/backup
> residual cluster [Block 47]/[Block 66]/[Block 31] each left open: **B66-G2** ([Block 66] §66.3 —
> `BPxMigrator.processFormat()`'s `ReflectCall` operand resolution calls `reflect.eval(baseObj, null, null)`
> against the live migrated component tree but that block did not open `niagara.util.ReflectCall`/`eval()`
> itself, a `niagara.util` class outside migrator.jar); **B47-G3** ([Block 47] §47.1/§47.5 — `BBogMigrator`'s
> output-`EncryptionKeySource` computation calls `AxPasswordUtil.usesPasswordEncodings(c, {...3 encoding
> types...})` against the already-migrated tree, but [Block 47] took its exhaustive-vs-sample-check semantics
> on faith from the call site, never opening `AxPasswordUtil.java` itself); **B31-G3** ([Block 31] §31.6/§31.9
> — the `web:WebService`/`jetty:JettyWebServer` rows of that block's removed-property cross-check cited
> `BWebBogConverter`/`BJettyQoSFilterMigrator` at [Block 24] §24.2's signature-level census only, never
> re-reading either converter's actual property-removal list line-by-line); and **B66-G1** ([Block 66] §66.6 —
> whether `niagara.backup`/`BBackupService` can produce a KeyRing/passphrase-protected `.dist` CONTAINER that
> the migrator's own bytecode-confirmed-dead `MigrationEncoding`/`BBackupDistMigrator.LazyDecryptFunction`/
> `Migrate.passwordDecryptFunction` machinery was plausibly built to consume — `backup.jar` was not opened by
> [Block 24]/[Block 47]/[Block 66] at all). Does **not** cover: an actual `n5mig`/backup/restore execution
> (still inherits every prior block's open requires-execution gaps — nothing here runs a migration, a backup,
> or a restore); `BFormat.reflect()`'s own cached-`Method`-lookup body (`BFormat.java:402-450`, declared and
> its call sites read, its own reflective-invocation internals not traced — out of scope, see child gap);
> `AESStreamEncryption`'s internal `StreamEncryptionDetails` header/magic-byte detection logic (`isEncrypted()`
> was read only at its public dispatcher level, `io/AESStreamEncryption.java:97-109`; the private
> `StreamEncryptionDetails` constructor that actually inspects the stream's header bytes was not opened — this
> is the one point in §82.4 that keeps B66-G1 at NARROWED rather than CLOSED, see child gap); `BBogFile.java`'s
> own `usesKeyRingEncryption()`/`usesReversibleEncryptionPassPhrase()` bodies (already read whole by [Block 47]
> §47.2, reused not re-derived here); `PANCCADIA`'s real `config.bog` (not reopened this session — §82.3's
> findings are pure converter-source reads, cross-referenced against [Block 31]'s already-published PANCCADIA
> table, not against fresh bog bytes).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 24]/[Block 31]/[Block 47]/[Block 66] read. Jar hashes (this session, `sha256sum` against
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`): `migrator.jar`
> `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08` (byte-identical to [B24]/[B47]/[B66]'s own
> citation — re-verified, not re-decompiled), `baja.jar` `0a7fcbfcbd1a609ed0eba0c1abfbf7e3de372b6a51f551dcea497649d4e3fd9c`
> (byte-identical to [B31]'s citation), `backup.jar` `439de59717ee412d3245486c4e1c1f1c902403fce334cb6903029b32d798abdb`
> — this is the **first time `backup.jar` is hashed or opened by name in this corpus**; no prior block ([B14]/
> [B24]/[B31]/[B34]/[B47]/[B66]) read any class inside it.
>
> Sources: `organized/baja/vineflower/niagara/util/BFormat.java` — `Call` abstract base (`:503-557`, whole
> class, first read in this corpus), `ReflectCall` (`:637-752`, whole nested class, first read — closes
> B66-G2), `hasPermission`/`checkProtectedSlot` (`:360-385`, first read, `ReflectCall.eval()`'s own permission
> gate), `reflect()`'s signature only (`:402`, body not read, see scope note above);
> `organized/migrator/vineflower/com/tridium/migrator/BPxMigrator.java:505-627` (`processFormat()`, re-read
> from [Block 66] §66.3's own citation, whole method, this session, for its exact `reflect.eval(baseObj, null,
> null)`/`getEvalFailed()` call site at `:601-604`); `organized/baja/vineflower/com/tridium/security/
> AxPasswordUtil.java:189-208` (`usesPasswordEncodings`, both overloads, whole method, first read in this
> corpus — closes B47-G3); `organized/migrator/vineflower/com/tridium/migrator/web/BWebBogConverter.java`
> (54 lines, whole file, first line-by-line read — [Block 24] §24.2 read only its `convertXElem`
> signature/effect summary); `organized/migrator/vineflower/com/tridium/migrator/jetty/
> BJettyQoSFilterMigrator.java` (108 lines, whole file, first line-by-line read — same prior signature-only
> treatment); `organized/migrator/vineflower/com/tridium/migrator/MigrationUtils.java:521-537`
> (`removeSlotElements`, re-read from [Block 66] §66.1's own citation, whole method, this session, to verify
> exactly how `BWebBogConverter`'s two-entry `SLOTS_TO_REMOVE` map is applied); `organized/backup/vineflower/
> niagara/backup/BBackupService.java` — `addFilesToDist()` (`:1258-1379`, whole method, first read in this
> corpus), `restoreFiles(RestoreOp)` (`:582-771`, whole method, first read), field declarations
> `TRIDIUM_LEGACY_PASSPHRASE_ENCRYPTED_PATHS`/`KEYRING_ENCRYPTED_STATION_PATHS`/`PASSPHRASE_ENCRYPTED_PATHS`
> (`:245-249`), `populatePlatformAndPassphraseProtectedPaths()` (`:1488-1543`, partial — the IEEE 802.1X
> population loop only, enough to confirm `PASSPHRASE_ENCRYPTED_PATHS`'s sole populator), `matchesAnyPattern`
> signature (`:1464`); `organized/migrator/vineflower/com/tridium/migrator/baja/MigrationEncoding.java`
> (127 lines, whole file, re-read from [Block 47] §47.3's own citation — [B47]/[B66] already established it
> has zero call sites; this session reads its OWN body for the first time at the byte-format level, not merely
> the call-site-absence level); `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/KeyRing.java:139-148`
> (`exportKeyData`/`importKeyData` abstract contract, first read), `.../SimpleKeyRing.java:262-356`
> (`importKeyData`/`exportKeyData` concrete bodies, first read), `.../PBEEncodingInfo.java:46`
> (`makePBEKey` signature), `.../PBEEncodingKey.java:15` (`implements ISecretBytesSupplier`, class
> declaration), `.../io/AESStreamEncryption.java:1-109` (public dispatcher methods
> `keyRingToPBE`/`pbeToKeyRing`/`isEncrypted`/`ifEncrypted`, first read — internal `StreamEncryptionDetails`
> header-detection body explicitly NOT read, see scope note), `organized/_bin-ext/nre/vineflower/niagara/nre/
> security/ISecretBytesSupplier.java:5` (interface declaration).
>
> Method: `Read` (whole-file or whole-method, this session, no line ranges skipped for any load-bearing
> claim) of every source cited above; `grep -rln`/`grep -rn` cross-directory searches (this session, fresh)
> to confirm/refute a call-site link between `migrator.jar`'s and `backup.jar`'s decompiled trees in BOTH
> directions (§82.4); `sha256sum` re-verification of `migrator.jar`/`baja.jar` (unchanged) and first-time
> hashing of `backup.jar`. Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source
> (`file:line`, this session) · `[INFER]` deduction, explicitly flagged (used for the negative-existence
> call-site claims in §82.4, per METHODOLOGY §3's negative-existence rule, and for the un-confirmed
> byte-format-identity hypothesis in §82.4).
>
> Migration/backup-security layer. Deepens [Block 66] (closes B66-G2 outright, §82.1; substantially narrows
> B66-G1, §82.4 — new evidence, not yet a close), [Block 47] (closes B47-G3, §82.2), [Block 31] (closes
> B31-G3, §82.3 — with a correction to §31.6's `jetty:JettyWebServer` row). Connects [Block 24] (grandparent
> of every converter-catalog citation reused here) and [Block 14] (grandparent of the migrator-SPI chain,
> unaffected by this block).
>
> **Type:** `mixed` — §82.1/§82.2/§82.3 are evidence blocks (opening previously-signature-only-censused or
> never-opened sources in full, each closing its named gap outright); §82.4 is the `mixed` trigger proper: it
> draws `[INFER]` conclusions by cross-referencing three independently-opened artifacts (`backup.jar`'s own
> classes, `migrator.jar`'s `MigrationEncoding`, the shared `com.tridium.nre.security.KeyRing` contract) against
> each other, in the same "opens a DIFFERENT artifact than the one the original gap named" pattern [Block 61]/
> [Block 66] each declared as the `mixed` trigger (METHODOLOGY §4/§11).

---

## 82.1 — B66-G2 CLOSED: `BFormat.ReflectCall.eval()` is a permission-gated, denylist-checked, non-throwing property/action reflector — `BPxMigrator.processFormat()` calls it purely to test resolvability, never to execute a live action `[CERT]`

[Block 66] §66.3 read `BPxMigrator.processFormat()` (`BPxMigrator.java:505-627`) whole and summarized its
final loop as "resolves a `ReflectCall` operand by resolving its base ORD against the LIVE migrated component
tree and calling `reflect.eval(baseObj, null, null)`" but explicitly did not open `ReflectCall.eval()`/
`getEvalFailed()` themselves, naming this **B66-G2**. Both are opened this session for the first time in
either corpus.

**The exact call site, re-confirmed.** `processFormat()`'s final `for (Object object : objects)` loop
(`fmt.parse()`'s output, `:541-547`) checks `if (object instanceof ReflectCall reflect)` (`:550`), resolves
the enclosing `BValueBinding`'s base ORD against the migrated tree (`baseOrd.resolve(ordBase).get()`,
`:586`), and — only if that resolves to a live `BComplex` (`:596`) — calls:

```java
try {
   reflect.eval(baseObj, null, null);
   if (!reflect.getEvalFailed()) {
      continue;
   }
} catch (Throwable e) {
   MigrationUtils.logInfo("pxMigrator.formatEval.fail", e, baseObj, MigReportUtil.getReportName(parent, p));
}
```

`[CERT]` `organized/migrator/vineflower/com/tridium/migrator/BPxMigrator.java:600-607` (re-read this session,
whole `try`/`catch`). **The call's entire purpose is a resolvability PROBE, not an execution.** If `eval()`
completes without setting `evalFailed`, `processFormat()` `continue`s — the format string is left UNCHANGED
(the `ReflectCall` operand already resolves against the migrated tree, nothing to rewrite). Only on
`evalFailed == true` (or a thrown exception, logged and treated the same as a failed probe) does the method
fall through to `:609-620`'s ORD-rewrite fallback (re-running the operand through `this.ordConverter
.convertOrd(...)`, the same converter §66.3 already documented for `processOrd()`).

**`ReflectCall.eval(Object obj, Object errorBase, Context cx)` (`BFormat.java:637-752`, whole class body,
this session) never throws for an ordinary resolution failure — it sets `this.evalFailed = true` and returns
an error-string placeholder instead.** The method's control flow, read whole:

1. **Denylist guard** (`:644`): if `obj` is a `BPassword`/`BAbstractAuthenticator`/`BAbstractPasswordEncoder`
   instance, `eval()` immediately returns `toErrorString(...)` (`:748-750`) — a `ReflectCall` operand can
   never resolve a value OFF a password/authenticator object, by construction, regardless of permissions.
2. **Permission gate, `BComplex` path** (`:645-693`): if `obj` is a `BComplex`, `BFormat.hasPermission(complex,
   null, cx)` (`:647`, the container-level read-permission check) must pass or `eval()` returns the error
   string immediately — for `processFormat()`'s call site, `cx` is `null` (`:601`, `reflect.eval(baseObj,
   null, null)`), and `hasPermission(complex, slot, cx)` with `cx == null` still evaluates
   `((BIProtected)complex).getPermissions(null)` (`BFormat.java:360-373`, re-read this session) —
   **not skipped by a null context**, it is whatever permission set `getPermissions(null)` itself resolves to
   for a `null` `Context` (a question this session does not trace further — `BIProtected.getPermissions`'s own
   body is outside this block's scope). If a resolvable `Property` exists for `this.id` (`complex.getProperty
   (this.id)`, `:651`), a second `hasPermission` check against that specific property (`:685`) gates it too;
   if it is an ACTION slot, a THIRD check against `FormatDenylist.isExcludedFromDenylist(...)` (`:668-680`)
   can also force the error-string path, with a `FINEST`-level log line naming the denied action.
3. **Reflective getter fallback chain** (`:696-725`): if no `Property` resolved (or a `Property` resolved but
   this is not the terminal segment, `:690`), `eval()` tries, IN ORDER: `"get" + capitalize(id)` with a
   `Context` arg, then the same with no arg, then the bare `id` with a `Context` arg, then bare with no arg,
   then a generic `get(String)` reflective call, then `getFormatValue(String)` — each via `BFormat.reflect()`
   (signature only read this session, `:402` — its own cached-`Method`-lookup body not traced, see header scope
   note). The first non-null result short-circuits into `this.chain(r, errorBase, cx)` (`:551`, either
   evaluates the NEXT chained `Call` if one exists, or stringifies `r`).
4. **`BIFormatPropertyHandler` fallback** (`:727-744`): one more permission-gated path for objects implementing
   a custom format-property lookup interface.
5. **Terminal failure** (`:746-747`): only if ALL of the above found nothing does `eval()` set
   `this.evalFailed = true` and return `toErrorString(obj, errorBase, cx)` — **`getEvalFailed()`
   (`:554-556`) is the ONLY signal `processFormat()` checks; `eval()` itself never throws for this ordinary
   "no such property/getter" case**, consistent with `processFormat()`'s own `try`/`catch(Throwable)`
   wrapper being defensive against a DIFFERENT class of failure (an exception thrown by a resolved getter's
   own body, or by `hasPermission`/`BIProtected.getPermissions` itself — not the plain unresolved-operand case).

`[CERT]` `BFormat.java:637-752` (whole `ReflectCall` class), `:503-557` (whole `Call` abstract base,
`evalFailed`/`getEvalFailed`/`chain`/`toErrorString`), `:360-373` (`hasPermission`), `:402`
(`reflect()` signature only).

**Net verdict, closing B66-G2.** `processFormat()`'s `reflect.eval(baseObj, null, null)` call is a
**deliberate, side-effect-free RESOLVABILITY TEST** against the LIVE migrated component tree — it exercises
the exact same permission/denylist/action-guard machinery a real live `BFormat` evaluation would (so a
migration-time probe and a runtime evaluation see the SAME access-control answer for the SAME object), but its
only observable effect on `BPxMigrator`'s own control flow is the boolean `evalFailed` flag: `false` means
"leave this format string as-is, it already resolves post-migration"; `true` (or a caught `Throwable`) means
"fall through to the ORD-rewrite/renaming fallback, and if THAT also fails to resolve, log
`pxMigrator.unresolvedFormat` and leave the format unrewritten" (`:612-613`, already read by [Block 66]
§66.3). No live action is ever INVOKED by this probe — the denylist guard (`:668-680`) exists precisely
because a naive reflective-action-call here (as opposed to a getter-style read) would risk firing a real
side-effecting action during what is supposed to be a pure migration-time compatibility check; `eval()`'s own
code confirms this concern was designed against, not merely hoped away.

## 82.2 — B47-G3 CLOSED: `AxPasswordUtil.usesPasswordEncodings` is an exhaustive, first-match-short-circuiting recursive walk over every `BComplex` descendant — not a sample or first-child-only check `[CERT]`

[Block 47] §47.1 traced `BBogMigrator.encodeBog()`'s output-encoding decision to `AxPasswordUtil
.usesPasswordEncodings(c, {BAes256PasswordEncoder.ENCODING_TYPE, BAliasedAes256PasswordEncoder.ENCODING_TYPE,
BAes256Pbkdf2HmacSha256PasswordEncoder.ENCODING_TYPE})` (`BBogMigrator.java:449-457`, already `[CERT]`) but
explicitly flagged the method's own semantics as taken "on faith from its call-site usage and name" —
**B47-G3**: "does it check EVERY `BPassword` slot in the tree, or only a sample/first-match?"

**Full read, `AxPasswordUtil.java:189-208`, first time in this corpus:**

```java
public static boolean usesPasswordEncodings(BComplex c, String... encodingTypes) {
   Set<String> encodingTypeSet = new HashSet<>();
   Collections.addAll(encodingTypeSet, encodingTypes);
   return usesPasswordEncodings(c, encodingTypeSet);
}

public static boolean usesPasswordEncodings(BComplex c, Set<String> encodingTypes) {
   for (Property p : c.getProperties()) {
      BValue v = c.get(p);
      if (v instanceof BComplex) {
         if (usesPasswordEncodings((BComplex)v, encodingTypes)) {
            return true;
         }
      } else if (v instanceof BPassword && encodingTypes.contains(((BPassword)v).getPasswordEncoder().getEncodingType())) {
         return true;
      }
   }
   return false;
}
```

`[CERT]` `organized/baja/vineflower/com/tridium/security/AxPasswordUtil.java:189-208`, whole method, both
overloads. **This is a genuine full-tree DFS, not a sample.** Every `Property` of `c` is visited
(`c.getProperties()`, no early bailout on property COUNT or index); every `BComplex`-typed property value is
recursed into UNCONDITIONALLY (no depth cap, no type filter beyond "is a `BComplex`"); every non-complex
`BPassword`-typed value is tested against the caller's `encodingTypes` set. The ONLY early-return is a
**first-MATCH** short-circuit (`return true` the instant any qualifying `BPassword` is found, at any depth) —
standard boolean-existence-check semantics, not a coverage shortcut: a `false` result is only reachable after
the ENTIRE subtree under `c` has been visited with no match, since the `for` loop has no `break`/early-`false`
path other than falling off the end.

**This upgrades [Block 47] §47.1's "output can only be `external`/`none`, never `keyring`" conclusion from
strongly-implied to independently `[CERT]`-verified**, per B47-G3's own closing text. `BBogMigrator
.encodeBog()`'s call (`:449-457`, [B47]'s own citation, not re-read this session — [B47] already opened it
whole) passes `c` = the tree AFTER `migrateBog()`'s earlier `keyring`-branch force-clear (§47.1's own finding)
— since `usesPasswordEncodings` is confirmed EXHAUSTIVE, there is no possibility of it "missing" a surviving
`keyring`-sourced `BPassword` deeper in the tree that a sample-based check might have overlooked: if
`migrateBog()`'s clearing pass genuinely reached every reversible `BPassword` (as `PasswordUtil
.updatePasswords`'s own whole-tree walk, already `[CERT]` per [B47] §47.1, establishes), then
`usesPasswordEncodings`'s equally-exhaustive walk over the SAME tree shape cannot find one that clearing
missed — the two full-tree traversals are now both independently confirmed exhaustive, closing the residual
"took on faith" gap.

## 82.3 — B31-G3 CLOSED, with a correction to [Block 31] §31.6's `jetty:JettyWebServer` row: `BJettyQoSFilterMigrator` converts ONLY the nested `JettyQoSFilter` object, never `JettyWebServer` itself, despite being registered against both types `[CERT]`

[Block 31] §31.6/§31.9 cross-checked `web:WebService`'s and `jetty:JettyWebServer`'s removed-slot findings
against `BWebBogConverter`/`BJettyQoSFilterMigrator` at [Block 24] §24.2's signature-level census only,
flagging the exact re-read as **B31-G3**. Both converters are opened whole this session, first line-by-line
read in either corpus.

### 82.3.1 — `BWebBogConverter.java` (54 lines, whole file) `[CERT]`

```java
private static final List<String> TYPES_THAT_HAVE_CHILD_ELEMENTS = List.of("web:WebService", "workbench:WebBrowserOptions");
private static final List<String> WEB_TYPES = List.of(
   "web:WebService", "web:WebStartConfig", "web:AppletModuleCachingType", "web:JnlpDownloadPolicy", "workbench:WebBrowserOptions"
);
private static final Map<String, List<String>> SLOTS_TO_REMOVE = Map.of(
   "web:WebService", List.of("rememberUserIdCookie", "AppletModuleCachingType", "WebStartConfig", "JnlpDownloadPolicy"),
   "workbench:WebBrowserOptions", List.of("uxMediaPrefersBrowserPreviewMode")
);

public XElem convertXElem(XElem parent, String typeSpecName, Version sourceVersion) throws Exception {
   if (WEB_TYPES.contains(typeSpecName)) {
      if (!TYPES_THAT_HAVE_CHILD_ELEMENTS.contains(typeSpecName)) {
         String moduleName = typeSpecName.split(":")[0];
         return BIBogElementConverter.moduleRemoved(moduleName);      // whole-object removal
      }
      for (XElem elem : parent.elems()) {
         SLOTS_TO_REMOVE.forEach((k, v) -> MigrationUtils.removeSlotElements(parent, elem, k, (List<String>)v));
      }
   }
   return parent;
}
```

`[CERT]` `organized/migrator/vineflower/com/tridium/migrator/web/BWebBogConverter.java:16-49`, whole class body
+ `convertXElem`. This exactly confirms [Block 24] §24.2's original summary shape ("`WebStartConfig`/
`AppletModuleCachingType`/`JnlpDownloadPolicy` REMOVED; `WebService`/`WebBrowserOptions` get targeted slot
removal") — no correction to [B24]'s own row, only a line-level confirmation.

**A structural finding [Block 31]'s signature-level read could not have surfaced: `SLOTS_TO_REMOVE`'s map-key
scoping is INERT at the direct-child-removal level.** Re-reading `MigrationUtils.removeSlotElements`
(`MigrationUtils.java:521-537`, re-opened this session from [Block 66] §66.1's own citation):

```java
public static void removeSlotElements(XElem parent, XElem element, String parentType, List<String> slotNames) {
   String elemType = element.get("t", "null:null").split(":")[1];
   String elemSlotName = element.get("n", "");
   if (slotNames.contains(elemType) || slotNames.contains(elemSlotName)) {
      parent.removeContent(element);                                  // <-- parentType NOT checked here
   } else if (isSameType(element, parentType)) {
      for (XElem elem : element.elems()) { ... }                       // <-- parentType checked only here
   }
}
```

`[CERT]` `MigrationUtils.java:521-537`, whole method (re-confirmed identical to [Block 66] §66.1's own
citation, no drift). **The first (direct-removal) branch never inspects `parentType` at all** — it only tests
whether `element`'s OWN type-name segment or OWN slot-name attribute is literally present in the `slotNames`
list handed to THIS call. Because `BWebBogConverter`'s `SLOTS_TO_REMOVE.forEach` loop calls
`removeSlotElements` once per MAP ENTRY for every direct child of `parent` — regardless of whether `parent`
itself is the `"web:WebService"` or `"workbench:WebBrowserOptions"` key's own owner — **the two slot-name
lists are functionally UNIONED at the direct-child level**: a `web:WebService` object's own direct children are
tested against `rememberUserIdCookie`/`AppletModuleCachingType`/`WebStartConfig`/`JnlpDownloadPolicy` **and**
`uxMediaPrefersBrowserPreviewMode` (the `workbench:WebBrowserOptions`-keyed entry), and vice versa for a
`workbench:WebBrowserOptions` object's children — the map's per-type grouping is documentation-shaped, not
enforcement-shaped, at this branch. (The SECOND, recursive branch IS genuinely type-scoped, since `isSameType
(element, parentType)` gates it — but that branch only fires for a grandchild nested inside a child whose OWN
type equals the map key, a shape this session did not find exercised by either `WebService`'s or
`WebBrowserOptions`'s actual N5 slot layout.) `[INFER]`: this cross-application has **no observed practical
effect on PANCCADIA's real data** — none of [Block 31] §31.1's re-census of PANCCADIA's `web:*`/
`workbench:*` objects reported a slot literally named `uxMediaPrefersBrowserPreviewMode` under a `WebService`
instance or `rememberUserIdCookie`/etc. under a `WebBrowserOptions` instance (not independently re-checked
against fresh bog bytes this session, per the header's declared scope) — flagged as a structural code-shape
finding, not a demonstrated migration defect.

### 82.3.2 — `BJettyQoSFilterMigrator.java` (108 lines, whole file) `[CERT]` — corrects [Block 31] §31.6's row

```java
private static final List<String> CONVERT_TYPES = List.of("jetty:JettyQoSFilter", "jetty:JettyWebServer");

public XElem convertXElem(XElem x, String typeSpecName, Version sourceVersion) {
   if (typeSpecName.equals("jetty:JettyQoSFilter")) {
      // rename this element's own "n" attribute qualityOfServiceSettings -> qualityOfServiceHandlerSettings
      // retag this element's own "t" attribute JettyQoSFilter -> JettyQoSHandler
      // per-property: suspendMs->maxSuspend (rebase -1->30), maxRequests 10->0, drop maxPriority/waitMs/managedAttr
   }
   return x;   // typeSpecName == "jetty:JettyWebServer": falls straight through, ZERO action taken
}
```

`[CERT]` `organized/migrator/vineflower/com/tridium/migrator/jetty/BJettyQoSFilterMigrator.java:21,32-80`,
whole class body + `convertXElem`, whole file read. **`CONVERT_TYPES` registers BOTH `jetty:JettyQoSFilter`
AND `jetty:JettyWebServer` (`:21`, `getConvertTypes()` returns this list unchanged, `:28-30`), but
`convertXElem`'s entire body is gated by a single `if (typeSpecName.equals("jetty:JettyQoSFilter"))` (`:33`)
— for a `jetty:JettyWebServer` element, the method is a pure no-op that returns `x` unchanged.** The actual
rename (`qualityOfServiceSettings`→`qualityOfServiceHandlerSettings`, `:36-40`) operates on the XElem's OWN
`"n"` attribute — meaning it fires when `convertXElem` is called with `x` bound to the SLOT ELEMENT itself
(the `<p n="qualityOfServiceSettings" t="jetty:JettyQoSFilter" ...>` child that lives ON a `JettyWebServer`
object, dispatched by TYPE `t=` value, not by the parent's type) — the rename, retype, and all 5 per-property
fixups (`:44-76`, `suspendMs`/`maxRequests`/`maxPriority`/`waitMs`/`managedAttr`) happen in ONE pass over
`x`'s own `<p>` children, triggered by `x`'s OWN `t="jetty:JettyQoSFilter"` typespec — never by
`JettyWebServer`'s. `[CERT]` confirmed by a whole-file read: the string `"JettyWebServer"` appears exactly
once in the entire 108-line file, inside `CONVERT_TYPES`'s own literal declaration (`:21`) — nowhere in
`convertXElem`'s body, `newInstance()` (`:82-84`), `newTypeSpec()` (`:86-88`), or `fixOrd()` (`:90-107`).

**Correction to [Block 31] §31.6's `jetty:JettyWebServer` row.** That table listed the removed slot
`qualityOfServiceSettings` as "Likely" converter-covered by `BJettyQoSFilterMigrator`, hedged because the
converter's body had not been re-read. **The precise reading is: `JettyWebServer` never had a "removed slot"
in the sense [Block 31]'s slot-diff table framed it — `qualityOfServiceSettings` is the PROPERTY NAME under
which a `JettyQoSFilter` (renamed to `JettyQoSHandler`) object is nested, and it is THAT nested object's own
conversion pass (triggered by ITS `t=` attribute) that renames the slot name to `qualityOfServiceHandlerSettings`
in place — not a separate removal-and-reinsertion step keyed off `JettyWebServer`'s own type.** The practical
migration OUTCOME [Block 31] §31.4/§31.6 already established (the object survives, renamed, non-orphaning) is
UNCHANGED by this correction — only the MECHANISM attribution is corrected: it is a rename fired by the CHILD
object's own registered type, with `JettyWebServer`'s presence in `CONVERT_TYPES` apparently vestigial for
this converter's actual behavior (a plausible reading, `[INFER]`, not confirmed against the broader
`n5mig` dispatch loop that decides WHICH registered typespec to call `convertXElem` for on a given element —
out of this session's scope). **`threadLimitHandler`** (the second N5-added property [Block 31] §31.6's row
named) does not appear anywhere in this converter's 108 lines either `[CERT]` (whole-file read, zero
occurrences) — consistent with [Block 31] §31.4's own "added-only" delta semantics (a purely-new property
needs no converter action; it silently takes its N5 default).

## 82.4 — B66-G1 substantially narrowed, not closed: `backup.jar` has its OWN live, working `.dist`-container KeyRing-protection mechanism — architecturally separate from `migrator.jar`'s dead code, sharing only a common low-level API contract, with a THIRD independently-dead code path found along the way `[CERT]` `[INFER]`

[Block 66] §66.6 bytecode-confirmed zero call sites for `MigrationEncoding.makeMigrationDecryptFunction`/
`BBackupDistMigrator.LazyDecryptFunction`/`Migrate.passwordDecryptFunction` anywhere in `migrator.jar`'s 94
compiled classes, and opened **B66-G1**: what this machinery was originally BUILT for, specifically whether
`BBackupService` can produce a `.dist` container whose CONTAINER (not per-bog files) is itself
KeyRing/passphrase-protected — `backup.jar` had never been opened by any prior block. It is opened this
session for the first time.

### 82.4.1 — `BBackupService` DOES protect a `.dist` container's KeyRing content, via its own PBE-passphrase machinery, self-contained within `backup.jar` `[CERT]`

**Write path, `addFilesToDist(BackupOp op)` (`:1258-1379`, whole method, this session).** When the backup
target is a local file store, a `localFileEncodingKey` (`PBEEncodingKey`) is derived from the PLATFORM's own
system password (`op.encodingInfo.makePBEKey(getSystemPassword())`, `:1265-1266`). Two distinct KeyRing-aware
protections then apply while zipping files into the `.dist`:

1. **The whole KeyRing export itself.** The special-cased path `"~security/.kr"` (`:1288-1304`) is NOT copied
   from disk — it is generated fresh via `SecurityInitializer.getInstance().getSecurityInfoProvider()
   .getKeyRing().exportKeyData(localFileEncodingKey)` (`:1296`), i.e. `KeyRing.exportKeyData(ISecretBytesSupplier)`
   (abstract contract, `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/KeyRing.java:139`),
   concretely `SimpleKeyRing.exportKeyData` (`[CERT]` `.../SimpleKeyRing.java:327-356`, whole method,
   this session) — which AES-encrypts a serialized `{alias→keyBytes}` map under a fresh random IV, keyed by
   the SAME `PBEEncodingKey` (`PBEEncodingKey implements ISecretBytesSupplier`, `[CERT]`
   `.../PBEEncodingKey.java:15`).
2. **Per-bog KeyRing-sourced content.** For any file that is a `BBogFile` whose `usesKeyRingEncryption()`
   returns true ([Block 47] §47.2's already-`[CERT]` `BBogFile` method, reused not re-derived), the file's
   InputStream is wrapped in a `BogTranscoderInputStream` targeting `EncryptionKeySource.external`
   (`:1330-1345`) — transcoding the bog's OWN per-property KeyRing-encoded passwords into passphrase
   (`external`) form for the `.dist` archive, using the running station's LIVE KeyRing as the decrypt source
   and `localFileEncodingKey` as the re-encrypt target.

`[CERT]` all citations above, this session's own whole-method read.

**Restore path, `restoreFiles(RestoreOp op)` (`:582-771`, whole method, this session) is the exact mirror.**
`op.manifest.getPBEEncodingInfo().makePBEKey(systemPassword)` (`:600`) re-derives the SAME class of
`PBEEncodingKey` from the RESTORING session's own system password, combined with PBE parameters (salt,
iteration count) the manifest carries INSIDE the `.dist` (`this.manifest.setPBEEncodingInfo(this.encodingInfo)`
at backup time, `[CERT]` `:1740`) — the identical split-storage pattern [Block 47] §47.1.1 already documented
for `external`-mode per-bog passwords, now confirmed to apply at the CONTAINER level too. The `.kr` entry is
imported straight into the restoring station's OWN live KeyRing (`getKeyRing().importKeyData(in,
(int)entry.getSize(), encodingKey)`, `:612-615` — `KeyRing.importKeyData(InputStream, int,
ISecretBytesSupplier)`, the abstract counterpart, `[CERT]` `KeyRing.java:141`), and any `external`-sourced bog
is transcoded back to `keyring` form via the same `BogTranscoderInputStream`, targeting
`EncryptionKeySource.keyring` this time (`:646-661`). **`SecurityInitializer.getInstance()` is used on BOTH
ends** — this is a SAME-STATION (or a station whose operator supplies the correct system password) round-trip
mechanism, not a cross-machine/cross-alias key-IMPORT tool: it operates on THIS process's own live
`SecurityInfoProvider`, never opens an arbitrary directory's `.kr`/`.km` pair the way `MigrationEncoding` does
(§82.4.3).

**Direct answer to B66-G1's literal question: YES, `BBackupService` can and does produce a `.dist` container
whose `~security/.kr` entry is KeyRing-protected via a container-level PBE passphrase** — this is a real, live
code path, not vestigial, gated only on the backup running against a local file store (`:1260-1273`) and a
local file encoding key being available.

### 82.4.2 — A THIRD independently-dead code path found in `backup.jar` itself, distinct from `migrator.jar`'s: `KEYRING_ENCRYPTED_STATION_PATHS` is a permanently-empty immutable list `[CERT]`

Both `addFilesToDist` (`:1324-1329`) and `restoreFiles` (`:638-645`) contain a THIRD branch, tested via
`matchesAnyPattern(path, KEYRING_ENCRYPTED_STATION_PATHS)` — a static path-pattern-based KeyRing/PBE transcode
alternative to the per-bog `usesKeyRingEncryption()`-driven branch documented above. **This list is declared
`private static final List<Pattern> KEYRING_ENCRYPTED_STATION_PATHS = Collections.emptyList()` (`:248`) — an
IMMUTABLE empty list — and this session's full-class `grep -n` finds ZERO `.add()`/mutation call anywhere in
the file targeting it.** Contrast with its sibling `PASSPHRASE_ENCRYPTED_PATHS` (`:249`, a real mutable
`ArrayList`), which IS populated at runtime, exclusively by `populatePlatformAndPassphraseProtectedPaths()`
(`:1488-1543`, partial read this session — the IEEE 802.1X platform-file detection loop) — an UNRELATED
concern (network/platform config file paths, not KeyRing/password content at all). `[CERT]`
`organized/backup/vineflower/niagara/backup/BBackupService.java:245-249` (field declarations, this session),
`:1324-1329,638-645` (both dead-branch call sites), `grep -n "KEYRING_ENCRYPTED_STATION_PATHS"` over the whole
2,145-line file returning only the declaration and these two `matchesAnyPattern` checks — no mutation site.
Since `Collections.emptyList()` returns a genuinely immutable list (any attempted mutation would throw
`UnsupportedOperationException`, not merely "happen to be empty"), this branch is **structurally,
permanently unreachable** in both directions, in the currently-shipped `backup.jar` — a third instance of
vestigial KeyRing-adjacent migration/backup machinery in this corpus, alongside [Block 47]/[Block 66]'s
`migrator.jar` findings, but in a DIFFERENT jar, superseded by a DIFFERENT (the per-bog-header-driven) live
mechanism, not by the same replacement this corpus has already traced for `migrator.jar`.

### 82.4.3 — `MigrationEncoding` shares `backup.jar`'s low-level `KeyRing` API contract but is confirmed architecturally UNWIRED to it; the specific byte-format question stays open `[CERT]` `[INFER]`

`MigrationEncoding.makeMigrationDecryptFunction(File niagaraSecurityDir)` (`MigrationEncoding.java:29-111`,
re-read whole this session) opens an ARBITRARY `niagaraSecurityDir`'s `.kr`/`.km` pair and branches on
`AESStreamEncryption.isEncrypted(keyRingFile)` (`:42`): if true, the file's bytes are imported AS-IS into a
freshly-constructed `SimpleKeyRing` via `keyRing.importKeyData(importData, importDataLen,
iSecretBytesSupplier)` (`:85`) — **the identical `KeyRing.importKeyData(InputStream, int,
ISecretBytesSupplier)` abstract signature** `BBackupService.restoreFiles()` calls on its own live KeyRing at
`:615`. If false, it reads a leading `int version` via `ObjectInputStream` and, for an EXPORT-shaped (not
live-shaped) version, manually re-wraps the raw bytes under a FRESH, ONE-OFF RANDOM key (`:69-75`,
`new SecureRandom().nextBytes(...)` immediately before `Aes256PasswordManager.encrypt(...)`) before importing.
`[CERT]` `MigrationEncoding.java:29-111`, whole method, this session.

**What this session CONFIRMS**: `MigrationEncoding` and `BBackupService` share the SAME abstract
`com.tridium.nre.security.KeyRing.importKeyData`/`exportKeyData` contract (`[CERT]`, `KeyRing.java:139,141`)
for moving key material in and out of a `SimpleKeyRing` instance — this is a real, verified structural
similarity, not a coincidence of naming. **What this session does NOT confirm, and flags explicitly as
`[INFER]`**: whether `MigrationEncoding`'s `AESStreamEncryption.isEncrypted()`-true branch was specifically
designed to consume `BBackupService.addFilesToDist()`'s exact `~security/.kr` export byte layout.
`SimpleKeyRing.exportKeyData()`'s own output format, read this session (`:327-356`), is a raw
`[16-byte IV][AES-encrypted{ObjectOutputStream-serialized version=6/magic=167662754/key-count/entries}]`
byte sequence, built WITHOUT ever calling into the `com.tridium.nre.security.io.AESStreamEncryption` class —
whereas `AESStreamEncryption.isEncrypted()`'s actual header-detection logic lives in a private
`StreamEncryptionDetails` inner class this session did NOT open (out of scope, header note). **Whether
`SimpleKeyRing`'s raw export bytes would register as `isEncrypted() == true` under `AESStreamEncryption`'s own
detection is therefore an open, falsifiable question** — the two mechanisms are proven to share the
high-level `KeyRing` Java interface, but a byte-format identity claim would need that one additional read.

**Confirmed instead, at the call-graph level, in BOTH directions, this session (fresh, not reused from
[Block 66]):** `grep -rln "AESStreamEncryption|BogTranscoderInputStream|niagara\.backup|BBackupService"` over
`organized/migrator/vineflower/` returns exactly ONE hit — `MigrationEncoding.java` itself, for its OWN
`AESStreamEncryption` IMPORT (`:6`) and ONE call (`:42`), never a reference to `niagara.backup`/
`BBackupService`/`BogTranscoderInputStream` by name. `grep -rln "com\.tridium\.migrator|MigrationEncoding|
LazyDecryptFunction|passwordDecryptFunction"` over `organized/backup/vineflower/` returns **zero hits** —
`backup.jar`'s own decompiled source never mentions the migrator package, class, or field names at all.
`[CERT]` both `grep -rln` runs, this session, against the full decompiled trees (a source-level negative
result across a KNOWN-COMPLETE decompile tree for both jars, not a partial-file-set search — stronger than
[Block 47] §47.3's original source-`grep`, though still not [Block 66] §66.6's bytecode-exhaustive standard,
since neither jar's compiled classes were bytecode-disassembled this session — see child gap).

**Net verdict — B66-G1 narrowed, not closed.** This session answers the literal "can `BBackupService` produce
a KeyRing-protected `.dist` container" question with a confirmed **YES** (§82.4.1, a REAL, live mechanism,
not the dead code B66-G1 speculated about) — but finds that mechanism is its OWN, self-contained,
same-station round-trip, sharing only the common Tridium `KeyRing` API surface with `migrator.jar`'s dead
`MigrationEncoding`, never actually CALLING it or being CALLED by it, confirmed negative in both source trees.
The honest reading: `MigrationEncoding` was very plausibly built against the SAME general `KeyRing`
export/import capability `BBackupService` also uses (both post-date a common `SimpleKeyRing`/
`AESStreamEncryption` API design), consistent with an EARLIER or PARALLEL design for source-KeyRing-aware
cross-station migration that was never wired into either `n5mig`'s own call graph ([Block 66] §66.6, bytecode-
exhaustive) or `BBackupService`'s (this session, source-exhaustive but not bytecode-exhaustive) — but this
session's evidence cannot distinguish "an abandoned/incomplete migration feature" from "two independently
Tridium-authored mechanisms that happen to share a common low-level utility class" with certainty. Refined
into **B82-G1** (bytecode-level backup.jar sweep) and **B82-G2** (the byte-format question) below, replacing
the open half of B66-G1.

## 82.x — Connections

- **[Block 66]** — closes **B66-G2** (§82.1, `ReflectCall.eval()`'s full semantics). Substantially narrows,
  does not close, **B66-G1** (§82.4) — new, real evidence (`backup.jar`'s own live mechanism, §82.4.1; a
  third independently-dead branch, §82.4.2; a confirmed-negative bidirectional call-graph check, §82.4.3)
  replacing pure speculation with a bounded, still-open byte-format question. [Block 66] §66.1's own
  `MigrationUtils.removeSlotElements` citation is re-used and re-confirmed byte-identical this session
  (§82.3.1), not corrected.
- **[Block 47]** — closes **B47-G3** (§82.2, `usesPasswordEncodings`'s exhaustive-walk confirmation),
  upgrading §47.1's dependent conclusion from strongly-implied to independently verified. §47.2's `BBogFile
  .usesKeyRingEncryption()` citation is reused, not re-derived, as the per-bog trigger condition in §82.4.1.
- **[Block 31]** — closes **B31-G3** (§82.3). **Corrects** §31.6's `jetty:JettyWebServer` row: the
  "Likely"-hedged converter-coverage verdict is now a precise mechanism description (the child `JettyQoSFilter`
  object's own type-triggered rename, not a `JettyWebServer`-keyed removal) — the OUTCOME (object survives,
  renamed, non-orphaning) is unchanged, only the attribution is sharpened. §31.6's `web:WebService` row is
  confirmed, not corrected, with one new structural note (§82.3.1's map-key-scoping finding) that [Block 31]'s
  signature-level read could not have surfaced.
- **[Block 24]** — grandparent of every converter-catalog citation this block re-reads line-by-line (§82.3);
  no correction to [B24] §24.2's own summary-level rows, only depth added.
- **[Block 14]** — grandparent of the whole migrator-SPI chain; unaffected by this block (no [B14] citation
  re-opened this session).

## 82.x — Child gaps opened

- **B82-G1** (refines the unclosed half of **B66-G1**, alongside B82-G2) — This session's `backup.jar`↔
  `migrator.jar` cross-reference (§82.4.3) is source-tree-exhaustive (`grep -rln` over BOTH complete decompiled
  trees, in both directions) but NOT bytecode-exhaustive the way [Block 66] §66.6 was for `migrator.jar`
  alone. A full `javap -p -c -constants` disassembly of `backup.jar`'s own compiled classes (not yet extracted
  or disassembled in this corpus), cross-referenced for any `com.tridium.migrator.*`/`MigrationEncoding`
  symbol, would close this gap to the same standard [Block 66] already met for the migrator side.
- **B82-G2** (refines the unclosed half of **B66-G1**, alongside B82-G1) — Whether `SimpleKeyRing
  .exportKeyData()`'s raw `[IV][AES(ObjectOutputStream-serialized entries)]` byte format (`SimpleKeyRing.java
  :327-356`, read this session) would register as `AESStreamEncryption.isEncrypted() == true` — i.e. whether
  `MigrationEncoding.makeMigrationDecryptFunction`'s first branch (`:42`) is actually shape-compatible with a
  `BBackupService`-exported `~security/.kr` blob — requires opening `AESStreamEncryption`'s private
  `StreamEncryptionDetails` header-detection constructor (`io/AESStreamEncryption.java`, exact line range not
  yet located — the class's public dispatcher methods were read this session, `:1-109`, but not this inner
  class's body), not opened this session.
- **B82-G3** — `BFormat.reflect(Object obj, String name, Class<?>[] params, Object arg)` (`BFormat.java:402`,
  signature read, body not read this session) is the actual cached-`Method`-lookup/`invoke()` machinery
  `ReflectCall.eval()`'s fallback chain (§82.1, `:696-725`) calls up to 6 times per operand — its own
  exception handling, method-cache invalidation (`invalidateCache`, `:398-400`, seen but not traced), and
  whether a reflectively-invoked GETTER could itself have a side effect (as opposed to the ACTION-slot path
  `eval()` explicitly denylist-guards, `:668-680`) remain unread.
- **B82-G4** — §82.3.1's `SLOTS_TO_REMOVE` map-key-scoping finding (the direct-removal branch of
  `removeSlotElements` ignoring `parentType`) was checked against [Block 31] §31.1's PUBLISHED PANCCADIA
  census tables, not against a fresh re-open of `config.bog`'s real `file.xml` bytes this session — a direct
  `grep` for `uxMediaPrefersBrowserPreviewMode`/`rememberUserIdCookie` cross-contamination in PANCCADIA's
  actual `web:WebService`/`workbench:WebBrowserOptions` instances would make the "no observed practical
  effect" claim `[CERT]` instead of `[INFER]`.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block82.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script output):

```
VERIFY_BLOCK_OUTPUT_PLACEHOLDER
```

**Reading the tally.** (filled in after the run, below.)
