# Block 86 — Closing the ORD-permission, JAAS-chain, and grant-matching residual gaps: `BOrdScheme.resolve()` is mostly caller-gated (a few schemes enforce their own), a null-`Context` permission check grants `BPermissions.all` by documented N4+N5 contract, every `BAuthenticationScheme` installs exactly ONE hardcoded `LoginModule` (never a real chain), `SuperSessionPrincipal` is CSRF/session-identity load-bearing, four more `doIsGrantedTo` bodies read, `ModifyProtectedPropertiesPermission`'s per-call trust set traced to its one construction site, the developer-log filename discrepancy resolved to "doc mismatch, not a hidden caller", and `BUserService.auditLoginAttempt` shown to have zero first-party callers across BOTH N4 and N5

> Research closing seven named child gaps carried over from [Block 68], [Block 81], [Block 8], and [Block 69]
> on this corpus. **B68-G3** (whether a `BOrdScheme.resolve()` implementation itself checks
> `target.getUser() == null` to deny/restrict resolution, or resolves structurally and relies on the caller
> having already gated read access); **B68-G4** (which concrete JAAS `LoginModule`(s) a
> `BAuthenticationScheme.login(handler)` call actually installs into the `LoginContext`); **B68-G5** (whether
> any in-station code branches differently on `Subject.getPrincipals(SuperSessionPrincipal.class)` versus the
> plain `niagara.context` `BUser`); **B81-G2** (`doIsGrantedTo`/wildcard-matching bodies for the four
> `NiagaraPermission` subclasses [Block 81] did not open: `KeyRingPermission`, `KeyStorePermission`,
> `PublicNiagaraBasicPermission`, `SigningPasswordPermission`); **B8-G1** (where
> `ModifyProtectedPropertiesPermission` instances are actually constructed, since its `trustedModules` set is
> a constructor argument, not a static list); **B8-G2** (the `developerNiagaraPermissionLog` filename
> code/doc discrepancy — does a `STATION`/`WORKBENCH`/`DAEMON` process-type token get threaded in from an
> untraced caller, or does the doc describe a different build); **B69-G2** (residual half of B54-G4 —
> strengthen or refute the "documented third-party API surface, not dead code" reading of
> `BUserService.auditLoginAttempt`'s zero-callers finding, within this corpus's structural limits).
>
> Parent-block gap-text confirmation: all seven gap texts were re-read directly from their source block files
> this session (`niagara5-block68.md`, `niagara5-block81.md`, `niagara5-block8.md`, `niagara5-block69.md`)
> before investigation began; every gap's text as quoted above matches its parent block verbatim — no drift
> found, no gap text needed correction.
>
> Does **not** cover: a live-station reproduction of any finding here (`[CERT-hw]`, blocked — no runnable N5
> station this session, same constraint as every predecessor block on this corpus); a full census of all ~40
> classes found overriding `getTrustedModulesForSlotOperations()`/`trustSubclassesForSlotOperations()`
> (§86.5 spot-checks one, `BUser`, for corroboration only — a full census is named as a residual, not
> attempted); a definitive resolution of whether ANY code anywhere in the universe of third-party/OEM N5
> modules calls `BUserService.auditLoginAttempt` (structurally outside both corpora's scope, per [Block 69]
> §69.3's own disclosed limit — §86.7 narrows the evidentiary picture with a second, independent corpus but
> does not and cannot close this to `[CERT]`); a byte-level disassembly of `niagarad.exe`'s native launcher
> (unrelated to this block's scope, already tracked as [Block 69]'s **B69-G1**).
>
> Subject version: **N5 5.0.0.28 (Beta)**, the same install every predecessor block in this corpus reads
> (`etc/brand.properties:workbench.notice`, not re-verified this session — REMIT of [Block 65]/[Block 81]'s
> convention). N4 comparison baseline for §86.7 only: `niagara-research` corpus, decompiled from
> OptimizerSupervisor-N4.14.0.162, at `/home/cristian/niagara-research/organized/`. No fresh decompilation —
> every file cited was already present in one of the two corpora's `organized/` trees from prior extraction
> sessions.
>
> Sources: `organized/baja/vineflower/niagara/naming/{BSlotScheme,BOrdScheme,OrdTarget}.java`,
> `organized/baja/vineflower/com/tridium/sys/station/BStationScheme.java`,
> `organized/baja/vineflower/niagara/file/BFileScheme.java`,
> `organized/baja/vineflower/niagara/space/BSpaceScheme.java`,
> `organized/baja/vineflower/niagara/nav/{BRootScheme,BNavScheme}.java`,
> `organized/baja/vineflower/niagara/spy/BSpyScheme.java`, `organized/rdb/vineflower/niagara/rdb/sql/BSqlScheme.java`,
> `organized/hierarchy/vineflower/niagara/hierarchy/BHierarchyScheme.java`,
> `organized/baja/vineflower/niagara/sys/BComponent.java` (targeted `:865-908`);
> `organized/baja/vineflower/niagara/authn/{BAuthenticationScheme,BPasswordAuthenticationScheme}.java`,
> `organized/baja/vineflower/com/tridium/authn/{BHTTPBasicAuthenticationScheme,NiagaraLoginConfiguration,
> UsernamePasswordLoginModule,AbstractNiagaraLoginModule,NiagaraLoginModule,BLegacyBasicAuthenticationScheme,
> BDigestAuthenticationScheme,BLegacyDigestAuthenticationScheme,BSessionIdAuthenticationScheme}.java`,
> `organized/ldap/vineflower/com/tridium/ldap/BLdapAuthenticationScheme.java`,
> `organized/saml/vineflower/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java`,
> `organized/clientCertAuth/vineflower/com/tridium/clientCertAuth/{BClientCertAuthScheme.java,
> pki/BPKIAuthenticationScheme.java}`, `organized/cloudLink/vineflower/com/tridium/cloudLink/security/
> BCloudAuthenticationScheme.java`, `organized/totpAuth/vineflower/com/tridium/totpAuth/
> BTotpAuthenticationScheme.java`, `organized/opcUaServer/vineflower/com/tridium/opcUaServer/authn/
> BOpcUaAuthenticationScheme.java`, `organized/workbench/vineflower/com/tridium/workbench/web/browser/
> BLoopbackAuthenticationScheme.java`, `organized/bacnet/vineflower/com/tridium/bacnet/stack/link/sc/
> authentication/BBacnetScAuthenticationScheme.java`;
> `organized/baja/vineflower/com/tridium/session/{SuperSessionPrincipal,SessionManager}.java`,
> `organized/baja/vineflower/niagara/session/SessionUtil.java`,
> `organized/web/vineflower/niagara/web/CsrfUtil.java`;
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/{KeyRingPermission,
> ModifyProtectedPropertiesPermission}.java`, `organized/_bin-ext/nre/vineflower/niagara/nre/security/
> permissions/{KeyStorePermission,PublicNiagaraBasicPermission,SigningPasswordPermission}.java`,
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/{Aes256PasswordManager,SimpleKeyRing}.java`;
> `organized/baja/vineflower/niagara/sys/{BIFrozenSlotContextValidator,BIReadonlyPropertyContainer}.java`,
> `organized/baja/vineflower/niagara/user/BUser.java` (targeted `:529-536`),
> `organized/workbench/vineflower/com/tridium/workbench/security/BChangeSystemPassphraseDialog.java`
> (targeted `:215`); `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/
> PermissionManager.java` (targeted `:141-145,277-317`), `organized/baja/vineflower/com/tridium/sys/Nre.java`
> (targeted `:931-945`); REMIT cross-corpus: `/home/cristian/niagara-research/organized/baja/baja/vineflower/
> javax/baja/user/BUserService.java` (targeted `:360-381`), `/home/cristian/niagara-research/organized/baja/
> baja/vineflower/com/tridium/authn/BAuthenticationService.java` (targeted `:341-347`). Corpus-wide
> `grep -rln`/`grep -rn` censuses (`extends BOrdScheme`/`extends BSpaceScheme` — 53 files, each individually
> checked for `getUser()`/`checkPermission`/`PermissionException`/`hasOperatorRead`/`hasAdminRead`/
> `hasAdminWrite`; `SuperSessionPrincipal`; `getCurrentNiagaraSuperSession`; `new
> ModifyProtectedPropertiesPermission`; `developerNiagaraPermissionLog`; `getTrustedModulesForSlotOperations`/
> `trustSubclassesForSlotOperations`; `BAes256PasswordEncoder`; `\.auditLoginAttempt\(` on both corpora), all
> run this session, each reported as an exhaustive count.
>
> Method: direct reading of pre-existing in-corpus Vineflower decompiles (nothing re-decompiled this
> session); corpus-wide `grep -rn`/`grep -rln` negative-existence and positive-inventory censuses, each run
> to completion and reported verbatim, not sampled (METHODOLOGY §3's symmetric-opening rule). Markers
> (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device — highest ·
> `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official downloaded document · `[INFER]`
> deduction. `file:line` citations use the full `organized/<module>/vineflower/...` path (this corpus's root
> IS `/home/cristian/niagara5-research/`, so these resolve `ok` under METHODOLOGY §11's flat-layout rule,
> matching [Block 81]'s convention) at least once per cited file; a bare `File.java:NN` short form appears in
> prose only where a fully-pathed citation to the same file already appears nearby or in this header. The two
> `niagara-research` (N4) citations are explicitly marked `[N4]` and use that corpus's own root.
>
> Security/naming layer, closing residual gaps across four prior blocks. Connects [Block 68] (closes
> **B68-G3**, **B68-G4**, **B68-G5**), [Block 81] (closes **B81-G2**, and its finding in §86.1 is a direct
> structural extension of [Block 81] §81.1's "two undocumented bypasses" pattern — a third and fourth
> bypass-shaped finding, in `KeyRingPermission`), [Block 8] (closes **B8-G1** and **B8-G2**; §86.1's
> `BComponent.getPermissions(Context)` null-context-grants-`BPermissions.all` finding is a direct, load-
> bearing extension of [Block 8] §8.1's/[Block 46]'s dropped-`Context` findings and [Block 68] §68.6's
> null-`Context`-resolves-to-null-user finding), [Block 69] (closes/advances **B69-G2**, the residual half of
> [Block 54]'s **B54-G4**), [Block 46] (§86.1 directly extends **B46-G3**, already narrowed by [Block 68]
> §68.6 — this session traces the SAME null-`Context` chain one hop further, into the actual permission
> DECISION a caller reaches when it does check).
>
> **Type:** `mixed` — §86.1–§86.6 are dense fresh `[CERT]` evidence (whole/targeted reads of files no prior
> block on this corpus opened, plus 8 corpus-wide grep censuses); §86.1's "resolve is mostly caller-gated"
> and "null-Context grants BPermissions.all by design, not accident" conclusions are `[INFER]` built across
> this session's own `[CERT]` reads (cross-checked against N4's identical, doc-commented contract); §86.7 is
> a `[CERT]`-evidenced strengthening of a prior block's `[INFER]` via a second independent corpus, explicitly
> not a closure.

---

## 86.1 — B68-G3 CLOSED: `BOrdScheme.resolve()` is mostly structural/caller-gated (49 of 53 implementations never check `getUser()`), but a handful of security-sensitive schemes DO enforce their own permission checks — and when a caller does check a null-`Context` resolution's permissions, the documented N4+N5 contract GRANTS `BPermissions.all`, not denial `[CERT]`+`[INFER]`

**The corpus-wide census, run to completion.** Every one of the 53 `extends BOrdScheme`/`extends
BSpaceScheme` files in this corpus (`grep -rln`, `fallback/`/`docSource` excluded) was individually
`grep`-checked this session for `getUser()`/`checkPermission`/`PermissionException`/`hasOperatorRead`/
`hasAdminRead`/`hasAdminWrite` `[CERT]`. **49 of 53 have zero hits** — including every core scheme a `station:`
or `file:` ORD actually resolves through:

- `BStationScheme.resolve(OrdTarget base, OrdQuery query, BSpace space)` — the entire body is
  `return new OrdTarget(base, space);`, no check of any kind `[CERT]`
  `organized/baja/vineflower/com/tridium/sys/station/BStationScheme.java:49-51` (whole 84-line file).
- `BFileScheme.resolve(OrdTarget base, OrdQuery query, BSpace space)` — resolves `fs.resolveFile(path)` and
  wraps it in an `OrdTarget`; no `getUser()`/permission call anywhere in the file `[CERT]`
  `organized/baja/vineflower/niagara/file/BFileScheme.java:79-101` (whole 146-line file).
- `BSlotScheme.doResolve(OrdTarget base, OrdQuery query)` (the workhorse for ordinary slot-path traversal —
  126 lines of component/property-container walking logic) never references `getUser`/permissions once
  `[CERT]` `organized/baja/vineflower/niagara/naming/BSlotScheme.java:71-196` (whole 202-line file).
- `BSpaceScheme.resolve(OrdTarget base, OrdQuery query)` (the shared abstract base every `file:`/`station:`-
  style scheme extends) and `BRootScheme.resolve(...)` (`return new OrdTarget(base, BNavRoot.INSTANCE);`)
  are equally silent `[CERT]` `organized/baja/vineflower/niagara/space/BSpaceScheme.java:37-51` (whole
  83-line file), `organized/baja/vineflower/niagara/nav/BRootScheme.java:42-45` (whole 77-line file).

**4 of 53 DO enforce their own check — a genuine, previously-undocumented split, not a uniform rule.**
`grep` surfaced exactly four positive hits:

| Scheme | Check | Null-user behavior | `[CERT]` |
|---|---|---|---|
| `BSpyScheme` (`spy:` diagnostics ORD) | `if (base.getUser() != null && !base.getUser().getPermissions().isSuperUser()) throw new UnresolvedException(...)` | **A `null` user does NOT trigger the deny branch** (short-circuits false on the first operand) — only a non-null, non-superuser is blocked; a null-user resolution passes straight through to `ss.resolveSpy(path)` | `organized/baja/vineflower/niagara/spy/BSpyScheme.java:46-55` (whole 56-line file) |
| `BNavScheme` (`nav:` UI-navigation ORD) | `checkPermissions(BINavNode node, Context cx)`: if the node `instanceof BIProtected`, requires `node.getPermissions(cx).has(1)` (operator-read bit) or throws `PermissionException` | Delegates entirely to the target's own `getPermissions(Context)` — see the `BComponent` finding below for what a `null` `cx` produces there | `organized/baja/vineflower/niagara/nav/BNavScheme.java:46-87` (whole 106-line file) |
| `BSqlScheme` (`sql:` RDBMS-query ORD) | `obtainConnectionAndContext`: requires `db.getPermissions(base).hasAdminWrite() && hasAdminInvoke()`, else `throw new PermissionException()` | Same delegation pattern — resolves through `BPermissions`, same downstream question | `organized/rdb/vineflower/niagara/rdb/sql/BSqlScheme.java:155-185` |
| `BHierarchyScheme` (hierarchy-node ORD) | Resolves the target via `BOrd.make(...).resolve(base.get(), user)` (explicit `HierarchyUtil.getUser()`) then requires `target.canRead()`, else `throw new UnresolvedException(...)` | Same `canRead()` delegation | `organized/hierarchy/vineflower/niagara/hierarchy/BHierarchyScheme.java:107-113` |

**The decisive downstream fact: `canRead()`/`getPermissions(Context)` do NOT deny on a `null` user — they
GRANT `BPermissions.all`, and this is a documented cross-version contract, not an N5-specific accident.**
`OrdTarget.canRead()`/`getPermissionsForTarget()` delegate to the target's own `BIProtected.getPermissions`:
```java
public BPermissions getPermissionsForTarget() {         // OrdTarget.java:270-281
   if (this.permissions == null) {
      BIProtected target = this.getSecurityTarget();
      this.permissions = target != null ? target.getPermissions(this) : BPermissions.all;
   }
   return this.permissions;
}
public boolean canRead() {                               // OrdTarget.java:283-286
   BIProtected st = this.getSecurityTarget();
   return st != null ? st.canRead(this) : true;
}
```
`[CERT]` `organized/baja/vineflower/niagara/naming/OrdTarget.java:270-286`. `BComponent`'s own
`getPermissions(Context cx)` — the concrete implementation every ordinary station component uses — is:
```java
public BPermissions getPermissions(Context cx) {         // BComponent.java:882-893
   BPermissions permissions = this.slotMap.getCachedPermissions();
   if (permissions == null) {
      if (cx != null && cx.getUser() != null) {
         permissions = cx.getUser().getPermissionsFor(this);
      } else {
         permissions = BPermissions.all;
      }
   }
   return permissions;
}
```
`[CERT]` `organized/baja/vineflower/niagara/sys/BComponent.java:882-893`. **A `null`-`Context`/`null`-user
check does not deny — it returns `BPermissions.all`, i.e. FULL read/write/invoke/admin permissions.**
`canRead(OrdTarget cx)` (`BComponent.java:896-908`) and its `canWrite`/`canInvoke` siblings all route through
this same `getPermissionsForTarget()`/`getPermissions(cx)` call. This is **not** a novel N5 defect: the
identical method, with the identical `cx != null && cx.getUser() != null ? ... : BPermissions.all` shape,
exists verbatim in the N4.14 corpus, and N4's OWN shipped bajadoc-adjacent source comment states the
contract explicitly (re-read this session, `[N4]`):
```java
/**
 * Get the set of permissions available based on the specified context. ...
 * If the context is null then typically this method should return {@code BPermissions.all}.
 * ... Under no circumstances should this method return null or make a network call.
 */
public BPermissions getPermissions(Context cx) { ... }
```
`[CERT]` `[N4]` `/home/cristian/niagara-research/organized/docSource/docSource-doc/vineflower/baja/javax/
baja/sys/BComponent.java:1953-1982` (doc comment + method body, N4.14) — confirming N5's
`:882-893` is an unchanged carry-forward of a deliberate, documented API contract, not an N5 regression.

**Net verdict, closing B68-G3.** The gap's own framing offered two possibilities: a scheme itself denies on
`null` user, or it resolves structurally and relies on the caller having already gated access. **Both are
true, split by scheme**: the overwhelming majority (49/53, including every core `station:`/`file:`/`slot:`/
`root:`/space-scheme path) resolve with zero user/permission check of their own, structurally relying on the
caller; a minority (`spy:`, `nav:`, `sql:`, hierarchy) DO enforce their own gate — but even where enforcement
exists, it is expressed by calling the SAME `getPermissions(Context)`/`canRead()` API that (per the
`BComponent`/`OrdTarget` reading above) treats a `null` `Context`/user as **fully permitted**, not denied.
This directly extends [Block 68] §68.6's "a `null` `Context` resolves to `user = null`, not ambient identity"
finding one hop further: a `null` user is not itself dangerous at the `OrdTarget` level (§68.6, unchanged),
but if that null-user target's permissions are ever CHECKED via the standard `BComponent`/`OrdTarget` API
(as `BNavScheme`/`BSqlScheme`/`BHierarchyScheme` do), the check **grants everything** rather than denying —
the opposite of a fail-safe default. It also extends the still-open **B46-G3** (the three DashboardPan
`BOrd.make(...).get(this, null)` read-side calls, [Block 46]/[Block 68] §68.6) with the concrete consequence
of that pattern: IF any code resolves an ORD via a `null` Context and then calls `.canRead()`/
`.getPermissions()` on the result to decide whether to expose it to a less-trusted caller, that check would
report "fully readable" rather than "denied" — a real amplifying risk factor for B46-G3's still-open half,
though this session found no first-party call site that actually chains null-Context-resolve →
canRead-as-an-exposure-gate together (named as **B86-G1** below, not asserted as an active exploit chain).

**Severity assessment.** This is `[INFER]`, reasoned as follows: the `BPermissions.all`-on-null-Context
behavior is a **long-standing, explicitly documented API contract** (confirmed identical and doc-commented
in N4.14, carried forward unchanged into N5 5.0.0.28) — not a newly introduced N5 defect, and not silent
undocumented behavior. Its risk is entirely conditional on a caller choosing to pass `null` as `Context` in a
situation where the result then gates exposure to an untrusted party; the API's own contract (`niagara-
research` N4 doc comment) frames `null` as meaning "no context available — behave as fully privileged",
consistent with an internal/system-level call convention, not a user-supplied value. **Rated LOW severity as
a standalone fact** (working as documented, cross-version-stable); it is however a genuine **risk-amplifying
detail** for any future finding of a null-Context resolution feeding an authorization decision for an
untrusted caller — flagged, not fixed, since no such call site was found this session.

## 86.2 — B68-G4 CLOSED: `NiagaraLoginConfiguration` is structurally single-entry — every `BAuthenticationScheme` subclass installs exactly ONE hardcoded, `REQUIRED`-flagged `LoginModule`, never a real multi-module JAAS chain; `NiagaraLoginModule`'s shared `commit()` is where a `BUser` becomes a `Principal` `[CERT]`

**`BAuthenticationScheme.login(CallbackHandler handler)`** (whole 117-line file) is the single call site every
scheme's login flows through: `new LoginContext("", null, handler, this.getLoginConfiguration())` `[CERT]`
`organized/baja/vineflower/niagara/authn/BAuthenticationScheme.java:97-110`. The empty-string login-context
name (`""`) means the `Configuration` object itself — not a named entry in a system-wide `login.config` file
— supplies the module list.

**`NiagaraLoginConfiguration` hardcodes a ONE-element `AppConfigurationEntry[]` in its constructor — this is
a structural limitation, not a per-scheme choice:**
```java
public NiagaraLoginConfiguration(String moduleClassName, LoginModuleControlFlag flag, Map<String, ?> options) {
   AppConfigurationEntry entry = new AppConfigurationEntry(moduleClassName, flag, options);
   this.entries = new AppConfigurationEntry[1];
   this.entries[0] = entry;
}
```
`[CERT]` `organized/baja/vineflower/com/tridium/authn/NiagaraLoginConfiguration.java:11-15` (whole 21-line
file). **A corpus-wide census of every `getLoginConfiguration()` override found in this corpus (13 concrete
schemes) confirms every single one constructs exactly one `NiagaraLoginConfiguration`, always with
`LoginModuleControlFlag.REQUIRED`:**

| Scheme (`SCHEME_NAME`/purpose) | `LoginModule` installed | `[CERT]` |
|---|---|---|
| `BHTTPBasicAuthenticationScheme` (`n4HTTPbasic`, the default local-user scheme) | `UsernamePasswordLoginModule` | `organized/baja/vineflower/com/tridium/authn/BHTTPBasicAuthenticationScheme.java:32-39` |
| `BDigestAuthenticationScheme` / `BLegacyDigestAuthenticationScheme` | `DigestLoginModule` | `organized/baja/vineflower/com/tridium/authn/BDigestAuthenticationScheme.java:34-40`, `organized/baja/vineflower/com/tridium/authn/BLegacyDigestAuthenticationScheme.java:33-39` |
| `BSessionIdAuthenticationScheme` | `SessionIdLoginModule` | `organized/baja/vineflower/com/tridium/authn/BSessionIdAuthenticationScheme.java:33-39` |
| `BLdapAuthenticationScheme` | `LdapLoginModule` (options carry the `BLdapTypeConfig`) | `organized/ldap/vineflower/com/tridium/ldap/BLdapAuthenticationScheme.java:116-124` |
| `BSAMLAuthenticationScheme` | `SAMLLoginModule` | `organized/saml/vineflower/com/tridium/saml/authnScheme/BSAMLAuthenticationScheme.java:315-321` |
| `BClientCertAuthScheme` / `BPKIAuthenticationScheme` | `ClientCertLoginModule` / `PKILoginModule` | `organized/clientCertAuth/vineflower/com/tridium/clientCertAuth/BClientCertAuthScheme.java:48-54`, `organized/clientCertAuth/vineflower/com/tridium/clientCertAuth/pki/BPKIAuthenticationScheme.java:113-119` |
| `BCloudAuthenticationScheme` | `CloudLoginModule` (options carry the scheme instance itself) | `organized/cloudLink/vineflower/com/tridium/cloudLink/security/BCloudAuthenticationScheme.java:91-99` |
| `BTotpAuthenticationScheme` | `TotpAuthLoginModule` | `organized/totpAuth/vineflower/com/tridium/totpAuth/BTotpAuthenticationScheme.java:32-38` |
| `BOpcUaAuthenticationScheme` | `OpcUaLoginModule` | `organized/opcUaServer/vineflower/com/tridium/opcUaServer/authn/BOpcUaAuthenticationScheme.java:31-37` |
| `BLoopbackAuthenticationScheme` (Workbench-only, throws if run in a station) | `LoopbackLoginModule` | `organized/workbench/vineflower/com/tridium/workbench/web/browser/BLoopbackAuthenticationScheme.java:33-39` |
| `BBacnetScAuthenticationScheme` | `BacnetScLoginModule` | `organized/bacnet/vineflower/com/tridium/bacnet/stack/link/sc/authentication/BBacnetScAuthenticationScheme.java:70-76` |
| `BLegacyBasicAuthenticationScheme` (`basic`) | **none — `getLoginConfiguration()` returns `null`** | see §86.7's sibling finding below |

`[CERT]` every row read directly this session. **13 distinct `LoginModule` implementation classes exist in
this corpus** (`grep -rln "LoginModule\b"`, this session), and every scheme-to-module mapping is 1:1 and
hardcoded at construction — **"LoginModule chain" is a misnomer for N5's actual design: there is no genuine
multi-module JAAS stack anywhere in this corpus**, only a dispatch table from scheme name to a single
required module.

**The shared module hierarchy, and where a `BUser` becomes a JAAS `Principal`.**
`NiagaraLoginModule` (abstract, `implements javax.security.auth.spi.LoginModule`, whole 77-line file) is the
common base every concrete `LoginModule` in the table above extends (directly or via
`AbstractNiagaraLoginModule`):
```java
public boolean commit() throws LoginException {          // NiagaraLoginModule.java:28-41
   if (!this.succeeded) return false;
   if (this.user == null) throw new SecurityException("attempting to add an object which is not an instance ...");
   this.subject.getPrincipals().add(this.user);           // <- BUser IS the Principal, added here
   this.commitSucceeded = true;
   return true;
}
```
`[CERT]` `organized/baja/vineflower/com/tridium/authn/NiagaraLoginModule.java:22-68` — this is the EXACT
mechanism [Block 68] §68.7 inferred generically ("`BUser`... acting as its own `java.security.Principal`");
this session traces it to its precise origin line. `AbstractNiagaraLoginModule.login()`
(`organized/baja/vineflower/com/tridium/authn/AbstractNiagaraLoginModule.java:8-23`, whole 26-line file)
wraps the subclass's `doLogin()` with a mandatory `getUserService().canLogin(this.user)` gate (lockout/
disabled-account check) BEFORE returning success — so even a password-correct `doLogin()` can still fail
login overall. `UsernamePasswordLoginModule.doLogin()` (whole 72-line file) — the default HTTP-Basic path —
resolves the username via `BUserService.getUser(username)` then validates the password via
`((BPasswordCache)user.getAuthenticator()).validate(password)` `[CERT]`
`organized/baja/vineflower/com/tridium/authn/UsernamePasswordLoginModule.java:14-71`.

**Net verdict, closing B68-G4.** The concrete `LoginModule`(s) a `BAuthenticationScheme.login(handler)` call
installs are: exactly one, chosen entirely by which scheme subclass is invoked, hardcoded in that subclass's
`getLoginConfiguration()` override, always `REQUIRED`, never composed with a second module. 13 distinct
`LoginModule` classes were catalogued corpus-wide; all but one scheme (`BLegacyBasicAuthenticationScheme`)
installs one. The shared `NiagaraLoginModule.commit()` step is confirmed as the exact mechanism that adds a
`BUser` (not a separate role/principal wrapper) to the `Subject`'s principal set — consistent with, and now
mechanically explaining, [Block 68] §68.7's/§68.8's independent findings about what an authenticated
`Subject` carries.

## 86.3 — B68-G5 CLOSED: `SuperSessionPrincipal` is genuinely load-bearing — it is the ONLY way first-party code recovers "which `NiagaraSuperSession` is this ambient JAAS `Subject` tied to", and CSRF verification fails closed without it `[CERT]`

A corpus-wide `grep -rn "SuperSessionPrincipal"` (this session, `fallback/`/`docSource` excluded) finds
exactly **3 files** total: the class itself, `BAuthenticationService.java` (the construction site [Block 68]
§68.7 already fully traced), and — **not previously cited by [Block 68]** — `SessionManager.java`, which
reads it via a THIRD, distinct method:
```java
public static NiagaraSuperSession getCurrentNiagaraSuperSession() {   // SessionManager.java:286-300
   Subject subject = SecurityUtil.getCurrentAuthenticatedSubject();
   if (subject != null) {
      Set<SuperSessionPrincipal> set = subject.getPrincipals(SuperSessionPrincipal.class);
      if (!set.isEmpty()) {
         for (SuperSessionPrincipal principal : set) {
            if (principal != null) return principal.getSuperSession();
         }
      }
   }
   return null;
}
```
`[CERT]` `organized/baja/vineflower/com/tridium/session/SessionManager.java:286-300` (whole 494-line file,
this method not cited by any prior block). This reads the AMBIENT JAAS `Subject`
(`SecurityUtil.getCurrentAuthenticatedSubject()`, the exact `AddSubjectFilter`-bound `Subject` [Block 68]
§68.7 traced) and extracts the caller's own `NiagaraSuperSession` via its `SuperSessionPrincipal` —
**something the plain `niagara.context` `BUser` request attribute structurally cannot provide**, because a
`BUser` object carries no session/request identity of its own.

**This is genuinely load-bearing, first-party, security-relevant code — not a diagnostic-only path.** A
second corpus-wide census (`grep -rn "getCurrentNiagaraSuperSession"`) finds **19 call sites** across `axvelocity`,
`backup` (`BHxBackupManager`), `web` (`CsrfUtil`, `LogoutConfirmServlet`), `hx` (`HxUtil`, `BHxView`,
`BHxProfile`), `bajaux` (`WbWebWidgetServlet`), `baja` (`SpyWriter`×3, `SpyUtil`, `BAbstractAuthenticator`,
`BUser` itself), `httpClient` (`BStringServlet`), and `jetty` (`BJettyWebServer`) `[CERT]` (verbatim grep,
this session, exhaustive not sampled). The most security-relevant is CSRF verification:
```java
public static boolean verifyCsrfToken(String token) throws IOException, CsrfException {
   NiagaraSuperSession session = SessionManager.getCurrentNiagaraSuperSession();
   if (session == null) {
      throw new CsrfException(WEBLEX.get("csrf.token.verify.error"));   // fails CLOSED
   } else {
      return verifyCsrfToken(session.getCsrfToken(), token);
   }
}
```
`[CERT]` `organized/web/vineflower/niagara/web/CsrfUtil.java:27-34` (whole 45-line file). **Answer to
B68-G5's own framing**: yes, there is a concrete behavioral divergence between the two parallel identity
channels [Block 68] §68.7 named — the plain `niagara.context` `BUser` attribute (populated by `ContextFilter`
per-request) and the `AddSubjectFilter`-bound ambient JAAS `Subject` (populated once per authenticated
session). CSRF-token verification, session-identity lookups for Spy diagnostics, HX-view session tie-in, and
the backup manager's session tracking ALL require the SECOND channel specifically — a caller holding only a
`Context`/`BUser` (the first channel) cannot recover "which super-session is this" at all, and CSRF
verification is coded to **fail closed** (throw, not silently pass) when the ambient-`Subject` channel is
unavailable. [Block 68] §68.7's own negative finding (no ROLE principal exists to branch on) stands
unchanged; this session's positive finding is that `SuperSessionPrincipal` itself — the ONE non-`BUser`
principal type §68.7 found — is exactly the mechanism session-identity code depends on, closing B68-G5 to
`[CERT]`.

## 86.4 — B81-G2 CLOSED: the four remaining `doIsGrantedTo` bodies read whole — two undocumented self-grant bypasses (`KeyRingPermission`, `SigningPasswordPermission`), one hardcoded universal never-checked key (`KeyRingPermission`), and a wildcard asymmetry between the core and public `NiagaraBasicPermission` siblings `[CERT]`

All four classes [Block 81] §81.1 did not open were read whole this session:

**`KeyRingPermission.doIsGrantedTo(Module)`** (whole 70-line file) has TWO bypasses [Block 81]'s
`FilePermission`/`RuntimeExecPermission` census did not have an analogue for:
```java
protected void doIsGrantedTo(Module module) {
   ...
   if (!"niagara.security.BAes256PasswordEncoder.key".equals(this.keyName)) {          // bypass #1
      if (!moduleName.equals(this.keyName) && !this.keyName.startsWith(moduleName + ".")) {  // bypass #2 guard
         for (NiagaraPermission permission : getPermissions(module, KeyRingPermission.class)) {
            String grantedKeyName = ((KeyRingPermission)permission).keyName;
            if (grantedKeyName.equals("*")) return;                                    // wildcard: all keys
            if (grantedKeyName.endsWith("*")
               && this.keyName.startsWith(grantedKeyName.substring(0, grantedKeyName.length() - 1))) return; // trailing-* prefix match
            if (grantedKeyName.equals(this.keyName)) return;                           // exact match
         }
         throw new PermissionException(...);
      }
   }
}
```
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/KeyRingPermission.java:20-54`.
**Bypass #1**: the literal key name `"niagara.security.BAes256PasswordEncoder.key"` is EXEMPT from the
entire check — every module can access this ONE specific keyring key unconditionally, no grant needed at
all. **Bypass #2 (self-grant)**: any module can access a keyring key equal to, or dot-prefixed by, its OWN
resolved Niagara module name (`moduleName.equals(keyName) || keyName.startsWith(moduleName + ".")`) with no
`@GrantKeyRingPermission` declaration — every module implicitly owns its own keyring namespace. Cross-check:
`"niagara.security.BAes256PasswordEncoder.key"` is confirmed as `Aes256PasswordManager.DEFAULT_AES_KEY_ALIAS`
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/Aes256PasswordManager.java:18,23` — the
DEFAULT AES-256 password-transcoding key every `BPassword`-touching module needs to read to decode ordinary
station passwords (`SimpleKeyRing.java:213` special-cases the same alias) `[CERT]`
`organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SimpleKeyRing.java:213` — i.e. this bypass is a
deliberate, sensibly-scoped design choice (the whole password-encoding subsystem structurally needs this one
key universally readable), not an accidental hole, **rated LOW severity** for the same reason as [Block 81]
§81.1's `FilePermission` "granted to all modules" bypass: a hardcoded universal exception for infrastructure
every module legitimately needs, not a broad or unbounded grant.

**`KeyStorePermission.doIsGrantedTo(Module)`** (whole 110-line file) — NO self-grant bypass exists.
Wildcard-or-exact on `name` (`"*".equals(name) || this.name.equals(name)`) ANDed with an action-bitmask
subset test (`(grantedPermission.actions & this.actions) == this.actions`) — the same bitmask-subset shape
[Block 81] §81.1 found for `FilePermission`, but with **no partial/prefix-name grant shape at all** (unlike
`FilePermission`'s/`KeyRingPermission`'s trailing-`*`/trailing-`-` support): a keystore grant is either `"*"`
(every store) or one EXACT store name `[CERT]`
`organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/KeyStorePermission.java:63-82`.

**`PublicNiagaraBasicPermission.doIsGrantedTo(Module)`** (whole 49-line file) — exact-name match ONLY, **no
wildcard mechanism at all**:
```java
public void doIsGrantedTo(Module module) {
   for (NiagaraPermission permission : NiagaraPermission.getPermissions(module, PublicNiagaraBasicPermission.class)) {
      if (this.name.equals(((PublicNiagaraBasicPermission)permission).name)) return;
   }
   throw new PermissionException(...);
}
```
`[CERT]` `organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/
PublicNiagaraBasicPermission.java:24-33`. This is a concrete, class-vs-class asymmetry with its CORE-tier
sibling: [Block 81] §81.1 already found `NiagaraBasicPermission.doIsGrantedTo`
(`organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/NiagaraBasicPermission.java:94-104`,
cited there) DOES support a literal `"*"` wildcard grant. **`PublicNiagaraBasicPermission` — the ONLY
`NiagaraBasicPermission`-shaped class a genuinely third-party module can ever request (per [Block 8] §8.1's
`isAnnotationPermitted` trust-tier gate) — has no equivalent**: a third-party module must individually
declare `@GrantPublicNiagaraBasicPermission` for EACH of the 5 named public constants it needs
(`SET_TIME`/`RESTORE_BACKUP`/`MANAGE_SERVER_TRUST_ANCHORS`/`RDB_CONNECTION`/`RENAME_AND_RESTART`, [Block 8]
§8.1) — it cannot request "all public basic permissions" in one annotation the way a core module can via
`"*"`.

**`SigningPasswordPermission.doIsGrantedTo(Module)`** (whole 53-line file) has the SAME self-grant shape as
`KeyRingPermission`, but narrower (exact match only, no dot-prefix variant):
```java
protected void doIsGrantedTo(Module module) {
   ...
   if (!checkedModuleName.equals(this.moduleName)) {                 // self-grant: exact match only
      for (NiagaraPermission permission : NiagaraPermission.getPermissions(module, SigningPasswordPermission.class)) {
         if ("*".equals(grantedPermission.moduleName) || this.moduleName.equals(grantedPermission.moduleName)) return;
      }
      throw new PermissionException(...);
   }
}
```
`[CERT]` `organized/_bin-ext/nre/vineflower/niagara/nre/security/permissions/
SigningPasswordPermission.java:15-37` — every module can access its OWN module's signing password with no
grant; wildcard (`"*"`) or exact-name match required for any OTHER module's signing password.

**Net verdict, closing B81-G2.** All four remaining `doIsGrantedTo` bodies are now read. Wildcard support is
inconsistent across the 8-class taxonomy: `FilePermission`/`RuntimeExecPermission`/`KeyRingPermission`
support trailing-wildcard PREFIX grants; `KeyStorePermission`/`PublicNiagaraBasicPermission` support only
exact-or-full-wildcard (no prefix shape); `NiagaraBasicPermission` supports full-wildcard but its public
sibling `PublicNiagaraBasicPermission` does not at all. Self-grant bypasses (a module implicitly trusted for
its OWN resource) exist in `KeyRingPermission` and `SigningPasswordPermission` but NOT in `KeyStorePermission`
or `PublicNiagaraBasicPermission` — this is a real, previously undocumented inconsistency across the
taxonomy, not a uniform policy, extending [Block 81] §81.1's "undocumented bypass" finding from `FilePermission`
alone to a corpus-wide pattern spanning 3 of the 8 permission classes now fully read (`FilePermission`,
`KeyRingPermission`, `SigningPasswordPermission`).

## 86.5 — B8-G1 CLOSED: `ModifyProtectedPropertiesPermission` has exactly ONE construction site corpus-wide — its `trustedModules` set is computed per-call from the target's own class hierarchy and two overridable per-type hooks, not a global hardcoded list `[CERT]`

A corpus-wide `grep -rn "new ModifyProtectedPropertiesPermission"` finds **exactly one** construction site
`[CERT]` (verbatim, exhaustive):
```java
static void checkSlotOperationCalledByOwnerOrFramework(BComplex complex, Slot slot, Context context, Property... path) {
   Set<String> trustedModules = new HashSet<>();
   getFrozenSlotContextValidatorSuperclasses(complex.getClass(), trustedModules);      // walk 1
   if (trustedModules.isEmpty()) {
      trustedModules.add(complex.getClass().getModule().getName());                   // fallback: self-trust
   }
   if (complex instanceof BIFrozenSlotContextValidator frozenSlotContextValidator) {
      trustedModules.addAll(frozenSlotContextValidator.getTrustedModulesForSlotOperations(slot, path)); // hook #1
      if (frozenSlotContextValidator.trustSubclassesForSlotOperations(slot, path)) {   // hook #2, default true
         trustedModules.add(complex.getClass().getModule().getName());
      }
   }
   ModifyProtectedPropertiesPermission permission = new ModifyProtectedPropertiesPermission(trustedModules);
   try { SecurityUtil.checkPermission(permission); }
   catch (PermissionException e) { /* rethrow as a localized IllegalXxxOperation */ }
}
```
`[CERT]` `organized/baja/vineflower/niagara/sys/BIFrozenSlotContextValidator.java:148-181` (whole 194-line
file). `getFrozenSlotContextValidatorSuperclasses` (`:183-193`, whole method) walks the target's class
hierarchy collecting the JPMS module name of every class that DIRECTLY declares
`implements BIFrozenSlotContextValidator` (checked via `getInterfaces()` at each level). The two overridable
hooks default to the empty set and `true` respectively:
```java
default Set<String> getTrustedModulesForSlotOperations(Slot slot, Property... path) { return Collections.emptySet(); }  // :31-33
default boolean trustSubclassesForSlotOperations(Slot slot, Property... path) { return true; }                          // :35-37
```
`[CERT]` `BIFrozenSlotContextValidator.java:31-37`. A corpus-wide `grep -rln "getTrustedModulesForSlotOperations"`
finds **~40 overriding classes** (mostly `kitControl` conversion/select/latch blocks, plus `BCode`,
`BOutgoingAccount`, `BHistoryConfig`, `BArchiveHistoryProvider`, `BCertificateHealth`, `BUser`,
`BUserPasswordConfiguration`, `BHttpClient`, `BWebsocketClient`, `BAbstractSigningRequester`, `BSessionToken`,
`BAbstractSigningProfile` — real, active usage, not a theoretical extension point) `[CERT]`. A spot-check of
one — `BUser` itself — shows it simply re-declares the interface's OWN inherited default via
`BIReadonlyPropertyContainer.super.getTrustedModulesForSlotOperations(...)` `[CERT]`
`organized/baja/vineflower/niagara/user/BUser.java:529-536` — i.e. `BUser` does not actually widen or narrow
the default self-trust rule; a full census of all ~40 overrides (whether any GENUINELY widens beyond
self-module trust) was not attempted this session and is left as a residual, not a load-bearing claim here.
The mechanism has exactly two callers corpus-wide: `BIReadonlyPropertyContainer.validateContextForPropertySet`
(the generic "frozen/protected property" write-gate every `BIReadonlyPropertyContainer` implementor gets,
`[CERT]` `organized/baja/vineflower/niagara/sys/BIReadonlyPropertyContainer.java:24-42`, whole 48-line file)
and one direct call, `BChangeSystemPassphraseDialog` guarding its own action `[CERT]`
`organized/workbench/vineflower/com/tridium/workbench/security/BChangeSystemPassphraseDialog.java:215`.

**Net verdict, closing B8-G1.** There is no hardcoded, global "who is trusted to modify protected properties"
list anywhere in the corpus. The trust set is computed FRESH on every check, per target-`BComplex`-type, from
(a) the JPMS modules of every class in that type's hierarchy directly implementing
`BIFrozenSlotContextValidator`, defaulting to the target's OWN module when none is found, plus (b)/(c) two
overridable per-type hooks that, by default, add nothing extra and re-affirm self-trust. Combined with [Block
8] §8.1's already-`[CERT]` finding that any `niagara.`/`com.tridium.`-prefixed non-`Test` module bypasses the
whole `ModifyProtectedPropertiesPermission` check regardless of `trustedModules`, the practical rule is: a
component can always modify its own protected properties, and any core Tridium module can modify anyone's.

## 86.6 — B8-G2 CLOSED: the `developerNiagaraPermissionLog` filename discrepancy is a genuine doc/code mismatch — the ENTIRE call chain from `niagara.permissions.disable` to the log file's creation carries no process-type parameter anywhere, corpus-wide `[CERT]`

The full call graph of `initDebugLogFile()` was traced exhaustively this session (3 call sites corpus-wide,
`grep -rln "initDebugLogFile"`, all three inside `PermissionManager.java` itself except the one external
entry point below):
```java
public static String disablePermissionChecks() {              // PermissionManager.java:141-145
   SecurityUtil.checkPermission(NiagaraBasicPermission.DISABLE_PERMISSION_CHECKS_PERMISSION);
   PermissionUtil.permissionChecksDisabled = true;
   return initDebugLogFile();
}
private static String initDebugLogFile() {                     // PermissionManager.java:285-317
   String niagaraUserHome = System.getProperty("niagara.user.home");
   String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss"));
   File logFile = new File(niagaraUserHome + File.separator + "developerNiagaraPermissionLog-" + timestamp + ".txt");
   ...
}
```
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/PermissionManager.java:141-145,285-317`
— `initDebugLogFile()` is `private static`, takes NO parameters, and its filename format string is a fixed
literal with no process-type placeholder anywhere. The ONE external caller of `disablePermissionChecks()`
corpus-wide (`grep -rn "PermissionManager.disablePermissionChecks"`, this session) is:
```java
private static void checkDisablePermissionChecks() {           // Nre.java:931-945
   boolean disablePermissionChecks = Boolean.getBoolean("niagara.permissions.disable");
   if (disablePermissionChecks) {
      try {
         licenseManager.checkFeature("tridium", "developer");
         String logFileName = PermissionManager.disablePermissionChecks();
         ...
         LOGGER.severe("Niagara permission exceptions are being written to " + logFileName);
         ...
      } catch (FeatureNotLicensedException ignore) { ... }
   }
}
```
`[CERT]` `organized/baja/vineflower/com/tridium/sys/Nre.java:931-945` — the returned `logFileName` string is
logged VERBATIM, with no `STATION`/`WORKBENCH`/`DAEMON` prefix/suffix concatenation anywhere in this method
or any other caller. A corpus-wide `grep -rln "developerNiagaraPermissionLog"` confirms the literal string
exists in exactly ONE file, `PermissionManager.java` itself `[CERT]` — no second implementation, no niagarad-
specific override, no other producer of this filename exists anywhere in the decompiled corpus.

**Net verdict, closing B8-G2.** [Block 8] §8.6 left open two possibilities: a process-type token gets threaded
in from an untraced caller, or the doc describes a different/later build. This session traces the CLASS's
entire caller graph and the CLASS's only method body to their absolute exhaustive limit (every reachable line
from `niagara.permissions.disable`'s boot-time read through the file's actual construction) and finds **zero**
process-type parameter anywhere. **The first possibility is now `[CERT]`-refuted; the second (a doc/build
mismatch) is the only reading this corpus's evidence supports.** This closes B8-G2 to `[CERT]`: on 5.0.0.28,
the on-disk filename is definitively `developerNiagaraPermissionLog-<yyyyMMdd-HHmmss>.txt`, no process-type
segment, full stop — the doc's `developerNiagaraPermissionLog-STATION-...` example does not and cannot match
this build's code.

## 86.7 — B69-G2 ADVANCED, not closed: `BUserService.auditLoginAttempt`'s public 3-arg signature has ZERO first-party callers in BOTH N4.14 and N5 5.0.0.28 — cross-generational evidence strengthening the "public third-party API surface" reading over "dead code" `[CERT]`+`[INFER]`

[Block 69] §69.3 found N5's `niagara.user.BUserService.auditLoginAttempt(boolean, BUser, Context)` has zero
Java call sites anywhere in the N5 corpus, with only its own `bajadoc` `<method>` entry as corroborating
evidence (`@since Niagara 3.3`, no `@deprecated` tag) — closed to the corpus's own evidentiary limit and
flagged residual as **B69-G2** (structurally blocked, since neither corpus contains third-party/OEM modules).
**This session adds a second, independent line of evidence: the SAME public method, in the N4.14 corpus,
ALSO has zero callers — including from Tridium's own `BAuthenticationService`, which has a DIFFERENT,
private, same-named helper method that is NOT the same call.**

`niagara-research`'s N4.14 corpus (`grep -rln "auditLoginAttempt"`, this session) surfaces
`javax/baja/user/BUserService.java` (the public method itself) and `com/tridium/authn/
BAuthenticationService.java` (a DISTINCT private method, confirmed by signature):
```java
// javax/baja/user/BUserService.java:360-375  — the PUBLIC 3-arg method (N4, unchanged into N5)
public final void auditLoginAttempt(boolean loginSuccessful, BUser user, Context auditContext) {
   if (auditContext != null) { ... Sys.getAuditor().audit(new AuditEvent(...)); ... }
}
// com/tridium/authn/BAuthenticationService.java:346,349-381 — a DIFFERENT private helper, same name, AuditInfo param
auditLoginAttempt(loginSuccessful, user, auditInfo);
private static void auditLoginAttempt(boolean loginSuccessful, BUser user, AuditInfo auditInfo) { ... }
```
`[N4]` `[CERT]` `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/user/
BUserService.java:360-381`, `/home/cristian/niagara-research/organized/baja/baja/vineflower/com/tridium/
authn/BAuthenticationService.java:341-381` (both read in full this session). A targeted corpus-wide
`grep -rn "\.auditLoginAttempt("` (a CALL, not a declaration) across the entire N4 corpus finds **exactly one
hit**, and it is `BAuthenticationService`'s own call to ITS OWN private `AuditInfo`-typed overload — NOT a
call to `BUserService`'s public `Context`-typed method `[CERT]` (verbatim grep, this session). **The public
`BUserService.auditLoginAttempt(boolean, BUser, Context)` method has zero callers in N4.14 either.**

**Reading this together.** A method that is: (a) public, `final`, documented with a stable `@since Niagara
3.3` tag; (b) carried forward with an IDENTICAL signature across at least two major framework generations
(N4.14 → N5 5.0.0.28, an interval spanning a full architectural rewrite — JPMS modularization, the
SecurityManager-to-agent migration, JAAS restructuring, all independently documented across this corpus's
other blocks); and (c) never called by Tridium's OWN first-party code in EITHER generation — is much better
explained as a deliberately maintained, stable SDK entry point for external (third-party/OEM custom
auth-scheme) callers than as forgotten dead code. Dead first-party helper methods are commonly pruned or
folded during a rewrite of this scale (the sibling PRIVATE, same-named `BAuthenticationService` method,
notably, DOES still exist and IS called in N4 at least); a public API surface method surviving UNCHANGED and
UNCALLED across the same rewrite, with no deprecation tag added at any point, is a stronger signal of
intentional external-facing design than a single-corpus zero-callers finding alone could support.

**This still does not, and structurally cannot, CLOSE B54-G4/B69-G2 to `[CERT]`.** Neither corpus contains
third-party/OEM module source (both are exhaustive extractions of Tridium's OWN shipped module catalogs, per
[Block 69] §69.3's own disclosed limit) — the evidentiary ceiling named there is UNCHANGED by this session; a
second corpus only rules out "called by SOME OTHER first-party N4 module before N5 removed the call", not
"called by any third-party module in the field". **B69-G2 verdict: ADVANCED from single-corpus to
cross-generational two-corpus zero-callers evidence — the "documented third-party entry point" reading is
now measurably better supported, but the gap remains open** for the same structural reason [Block 69] named,
restated (not reopened) at §86.x below.

## 86.x — Connections

- **[Block 68]** — closes **B68-G3** (§86.1: the resolve()-checks-or-relies-on-caller split, plus the
  null-Context-grants-`BPermissions.all` extension), **B68-G4** (§86.2: the single-`LoginModule`-per-scheme
  census and `NiagaraLoginModule.commit()`'s exact `BUser`-as-`Principal` mechanism), **B68-G5** (§86.3:
  `SuperSessionPrincipal`'s CSRF/session-identity load-bearing role). §68.6's "null Context → null user, not
  ambient identity" finding is extended, not corrected, by §86.1's downstream `BComponent.getPermissions`
  reading. §68.7's `BUser`-as-`Principal` finding is mechanically explained (not corrected) by §86.2's
  `NiagaraLoginModule.commit()` citation.
- **[Block 81]** — closes **B81-G2** (§86.4: the 4 remaining `doIsGrantedTo` bodies) and directly extends
  §81.1's "two undocumented bypasses" finding to a third permission class (`KeyRingPermission`'s self-grant
  + universal-key bypasses) and a fourth (`SigningPasswordPermission`'s self-grant bypass) — a corpus-wide
  pattern across 3 of 8 permission classes now fully read, not a `FilePermission`-only quirk.
- **[Block 8]** — closes **B8-G1** (§86.5: `ModifyProtectedPropertiesPermission`'s one construction site and
  its per-call trust computation) and **B8-G2** (§86.6: the developer-log filename discrepancy resolved to a
  genuine doc mismatch, not a hidden caller). §86.1's `BComponent.getPermissions(Context)` finding is a
  direct extension of §8.4's dropped-Context/network-audit-only findings — a THIRD instance of "a documented
  `null`-tolerant convenience path with real security consequences if misused at the wrong layer", after
  §8.1's `FilePermission`-all-modules grant and §8.8's network-connection audit-only finding.
- **[Block 69]** — advances **B69-G2** (§86.7: cross-generational two-corpus zero-callers evidence for
  `BUserService.auditLoginAttempt`), explicitly not closing it, preserving [Block 69] §69.3's own disclosed
  evidentiary ceiling.
- **[Block 46]** — §86.1 extends the still-open **B46-G3** (the read-side `BOrd.make(...).get(this, null)`
  calls) with the exact downstream consequence of a null-Context resolution being checked for permissions —
  named as risk-amplifying, not as a closure of B46-G3, and yields new child gap **B86-G1**.
- **N4 corpus (`niagara-research`)** — §86.1's `BComponent.getPermissions` doc-comment citation and §86.7's
  `BUserService`/`BAuthenticationService` cross-check are this block's only N4 REMIT reads; both are used to
  establish CROSS-VERSION STABILITY of an N5 finding, not to import an N4-specific claim.

## 86.x — Child gaps opened

- **B86-G1** — Whether any first-party N5 code chain actually COMBINES a null-`Context` ORD resolution
  (the read-side pattern [Block 46]'s **B46-G3** named) with a subsequent `canRead()`/`getPermissions()`
  check used to decide exposure to a less-trusted or remote caller — the concrete exploit shape §86.1's
  finding makes possible in principle. This session found the two ingredients (null-Context resolution
  exists; null-Context permission checks grant `BPermissions.all`) but did NOT find them chained together at
  a single call site. `investigable` — would need a targeted grep for `BOrd.*get\(.*,\s*null\)` results
  immediately followed by a `.canRead()`/`.canWrite()`/`.getPermissions()` call in the same method, across
  the whole corpus (broader than [Block 46]'s DashboardPan-only scope).
- **B86-G2** — Whether `BLegacyBasicAuthenticationScheme` (`SCHEME_NAME = "basic"`, `getLoginConfiguration()`
  returns `null`, `getDefaultAuthenticator()` returns `null`) is ever actually SELECTED/invoked at runtime —
  since `BAuthenticationScheme.login(handler)`'s `new LoginContext("", null, handler, null)` would, per
  ordinary JAAS semantics, fall back to the JVM's SYSTEM-WIDE default `Configuration` (not a Niagara-supplied
  one) when passed a `null` `Configuration`, and no `""`-named entry is likely to exist there — meaning this
  scheme may be structurally incapable of completing a login via this code path. `investigable` — would need
  to find `BLegacyBasicAuthenticationScheme.INSTANCE`/`getSchemeFromName("basic")` call sites and confirm
  whether the scheme is ever actually reachable as an active login path versus a vestigial N4-compat name
  kept only for enumeration/migration purposes.
- **B86-G3** — Whether `BSpyScheme`'s `spy:` diagnostics-ORD superuser-only gate
  (`base.getUser() != null && !isSuperUser()`, §86.1's table) is reachable with a genuinely `null`
  `base.getUser()` from an authenticated (but non-superuser) live web session — since the condition's
  short-circuit means a null user bypasses the deny branch entirely, and this session did not trace whether
  any live HTTP/web request path can produce a `spy:`-scheme `OrdTarget` with a null user while still being
  session-authenticated. `blocked-on-source` for a decompiled-only session (needs a live station /
  `[CERT-hw]` request trace to determine whether this is reachable, not just theoretically present in the
  code) — same live-station blocker class as every other `[CERT-hw]`-tagged gap on this corpus.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 49 of 53 `BOrdScheme`/`BSpaceScheme` implementations have zero `getUser`/permission-check hits; 4 do | [CERT] | corpus-wide `grep` loop, this session, verbatim counts |
| 2 | `BStationScheme`/`BFileScheme`/`BSlotScheme`/`BSpaceScheme`/`BRootScheme` resolve with no user/permission check | [CERT] | `BStationScheme.java:49-51`, `BFileScheme.java:79-101`, `BSlotScheme.java:71-196`, `BSpaceScheme.java:37-51`, `BRootScheme.java:42-45` |
| 3 | `BSpyScheme`/`BNavScheme`/`BSqlScheme`/`BHierarchyScheme` each enforce their own permission check | [CERT] | `BSpyScheme.java:46-55`, `BNavScheme.java:46-87`, `BSqlScheme.java:155-185`, `BHierarchyScheme.java:107-113` |
| 4 | `BComponent.getPermissions(Context cx)` grants `BPermissions.all` when `cx==null` or `cx.getUser()==null` | [CERT] | `BComponent.java:882-893` |
| 5 | The identical `getPermissions(Context)` null-grants-all shape + doc comment exists in N4.14 | [CERT] [N4] | `docSource/.../BComponent.java:1953-1982` |
| 6 | Every `BAuthenticationScheme.getLoginConfiguration()` override (13 checked) installs exactly ONE `LoginModule`, `REQUIRED` | [CERT] | table in §86.2, each row cited |
| 7 | `NiagaraLoginConfiguration`'s `AppConfigurationEntry[]` is hardcoded length 1 | [CERT] | `NiagaraLoginConfiguration.java:11-15` |
| 8 | `NiagaraLoginModule.commit()` adds `this.user` (a `BUser`) directly as the `Subject`'s `Principal` | [CERT] | `NiagaraLoginModule.java:28-41` |
| 9 | `SuperSessionPrincipal` appears in exactly 3 files corpus-wide; `SessionManager.getCurrentNiagaraSuperSession()` is a 3rd, previously-uncited reader | [CERT] | `grep -rn "SuperSessionPrincipal"`; `SessionManager.java:286-300` |
| 10 | `getCurrentNiagaraSuperSession()` has 19 call sites including CSRF verification, which fails closed on `null` | [CERT] | `grep -rn "getCurrentNiagaraSuperSession"`; `CsrfUtil.java:27-34` |
| 11 | `KeyRingPermission` has a self-grant bypass (own-module keyring namespace) and a universal-key bypass (`BAes256PasswordEncoder.key`) | [CERT] | `KeyRingPermission.java:20-54`; `Aes256PasswordManager.java:18,23` |
| 12 | `KeyStorePermission`/`PublicNiagaraBasicPermission` have NO self-grant bypass; `PublicNiagaraBasicPermission` has NO wildcard | [CERT] | `KeyStorePermission.java:63-82`; `PublicNiagaraBasicPermission.java:24-33` |
| 13 | `SigningPasswordPermission` has a self-grant bypass (exact-match only) | [CERT] | `SigningPasswordPermission.java:15-37` |
| 14 | `ModifyProtectedPropertiesPermission` has exactly ONE construction site corpus-wide | [CERT] | `grep -rn "new ModifyProtectedPropertiesPermission"`; `BIFrozenSlotContextValidator.java:148-181` |
| 15 | `initDebugLogFile()`'s entire call graph (3 sites) carries no process-type parameter anywhere | [CERT] | `PermissionManager.java:141-145,277-317`; `Nre.java:931-945` |
| 16 | `BUserService.auditLoginAttempt`'s public 3-arg method has zero callers in N4.14 too (the one grep hit is a different, private, same-named method) | [CERT] [N4] | `BUserService.java:360-381`; `BAuthenticationService.java:341-381`; corpus-wide `grep -rn "\.auditLoginAttempt("` |

Tally: 15 [CERT]-rows (16 counting the split row 5/16 markers), 0 pure [INFER]-only rows — every row above
rests on a direct `Read`/`grep` this session. Prose-level `[INFER]` conclusions (§86.1's severity read,
§86.7's "better explained as..." reasoning) are each explicitly hedged in place and not represented as
standalone table rows, consistent with this block's own `Type: mixed` declaration.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; the one doc-comment citation
(§86.1's N4 `BComponent.getPermissions` javadoc) is a LOCAL file already present in the `niagara-research`
corpus's own `organized/docSource/` tree, opened via direct `Read`, not fetched from the web.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block86.md`. Per the task's
explicit single-file/read-only-elsewhere instruction, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` were **not**
regenerated or hand-edited, and no other file in either corpus was modified — flagged here for the
orchestrator to pick up, matching every predecessor block's identical disclosure on this corpus.
