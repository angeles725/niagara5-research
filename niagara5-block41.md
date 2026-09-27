# Block 41 — N5 action auditing (old→new values) and the web authentication chain

> Research of **two named child gaps from Blocks 20 and 27**: (1) the N5 `BIActionAuditProvider`/
> `toOldValueAuditString` action-audit mechanism end-to-end — who calls it, what an `AuditEvent`/
> `BAuditRecord` contains, where it is stored, which types implement the provider interface, and how
> this compares to N4 (closes **B20-G3**); (2) the N5 web authentication/authorization chain —
> `NiagaraConstraintSecurityHandler` and `NiagaraAuthenticator` (both `com.tridium.jetty.*`, `jetty.jar`)
> — the Jetty→Niagara request flow, which URL constraints require auth, how a `BWebServlet` subclass
> obtains the authenticated user, and the servlet-level permission check (closes **B27-G3**).
> Does **not** cover: the `.hdb`/history binary file format (B33 remit, N4-only), `SecurityAuditEvent`'s
> full lexicon-message catalog (only the dispatch path is traced), SAML/OAuth2/client-cert authentication
> schemes' internals (only their `UnauthenticatedServlet` exemption is noted), or a live-station HTTP/audit
> capture (no runnable N5 station this session, same constraint as Blocks 2/4/10/20/21/27).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as Blocks 3/5/20/27
> (`etc/brand.properties:workbench.notice`). Jar sha256 (from
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`, this session):
> `baja.jar` `0a7fcbfcbd1a609ed0eba0c1abfbf7e3de372b6a51f551dcea497649d4e3fd9c`,
> `history.jar` `9fc1c9b1768fdc6e44456c2374df802565ea5afecf69d443f375082b49a612cf`,
> `jetty.jar` `67cfc1e50ff4aa2e6ce38eab3fc8332cc327898742dd1aa3f7f6aa1727793253` (identical to Block 27's
> recorded hash — same install), `web.jar` `68babcf16012314d59c095d3995c0a0f4db18853361cd5719e76be2a4d14b22e`
> (identical to Block 27's recorded hash).
>
> Sources: all real paths already decompiled in **this corpus's** `organized/` tree by prior blocks/sessions
> (Vineflower, per `tools/n5-decompile.sh`) — `organized/baja/vineflower/{niagara/security/*.java,
> niagara/space/AuditableSpace.java, niagara/sys/{Sys,BStation}.java, com/tridium/sys/schema/
> {ComplexSlotMap,ComponentSlotMap}.java, com/tridium/sys/station/Station.java, com/tridium/sys/Nre.java}`,
> `organized/control/vineflower/niagara/control/{WritableSupport,BNumericWritable}.java`,
> `organized/history/vineflower/com/tridium/history/audit/{BAuditHistoryService,BAuditRecord,
> BAbstractAuditRecord,BAbstractAuditHistorySource}.java`, `organized/jetty/vineflower/com/tridium/jetty/
> {NiagaraConstraintSecurityHandler,NiagaraAuthenticator,BJettyWebServer}.java`, `organized/web/vineflower/
> {niagara/web/{BWebServlet,BINiagaraWebServlet}.java, com/tridium/web/filters/{ContextFilter,
> AddSubjectFilter}.java, niagara/web/servlets/UnauthenticatedServlet.java}`. N4 remittance corpus
> `niagara-research` (B564, B829, B830, B408, B33, B30) via `tools/corpus-nav.py find` and direct read of
> `organized/baja/baja/vineflower/com/tridium/sys/schema/ComponentSlotMap.java`.
>
> Method: direct reading of pre-existing in-corpus Vineflower decompiles (no fresh decompilation needed —
> every class this block cites was already present in `organized/` from earlier sessions); `grep -rn` census
> across the whole `organized/` tree for call sites (`getOldValueForPendingActionAuditEvent`,
> `toOldValueAuditString`, `.audit(`, `new AuditEvent(`, `@AuditableSpace`, `"niagara.context"`,
> `setAttribute("niagara.context"`); N4 comparison via `corpus-nav.py find` + direct read of the cited N4
> `ComponentSlotMap.java` invoke() method.
> Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device — highest ·
> `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official downloaded document ·
> `[CERT-web]` official web · `[CERT-a]` secondary source/forum · `[INFER]` deduction.
> `file:line` citations point into `organized/<module>/vineflower/...` inside **this** corpus
> (`/home/cristian/niagara5-research/`) unless prefixed `N4:`, which points into the sibling corpus
> `/home/cristian/niagara-research/organized/baja/baja/vineflower/...`.
>
> Security/audit layer. Connects [Block 20] (§20.3 — this block closes the named child gap **B20-G3**),
> [Block 27] (§27.4/§27.6 — this block closes the named child gap **B27-G3**), N4 corpus [B564]/[B829]/
> [B830]/[B408] (the identical `AuditEvent`/`Auditor`/`AuditableSpace` architecture, already fully mapped
> for N4 — this block confirms it carried forward unchanged to N5 and adds the one genuine N5 delta).
>
> **Type:** `mixed` — §41.1–§41.3 are evidence (fresh reads of already-decompiled N5 source); §41.4 draws
> `[INFER]`/`[CERT]` conclusions across this block's own N5 evidence AND the prior N4 corpus's B829/B830/B408
> findings to state the cross-version delta.

---

## 41.1 — `BIActionAuditProvider`/`getOldValueForPendingActionAuditEvent`: the caller `[CERT]`

The **sole call site** in the whole decompiled N5 tree is `ComponentSlotMap.invoke(Action, BValue, Context,
boolean)`:

```java
boolean isAuditable = user != null && !Flags.isNoAudit(instance, action);
String oldValue = null;
if (isAuditable && instance instanceof BIActionAuditProvider actionAuditProvider) {
   oldValue = actionAuditProvider.getOldValueForPendingActionAuditEvent(action, arg, context);
}
// ... action actually invoked here ...
this.fireComponentEvent(7, action, arg, null, context);
if (isAuditable) {
   this.audit(getAuditSlotPath(instance, context), user, "Invoked", action.getName(), oldValue,
              toAuditString(instance, action, arg, context));
}
```
`[CERT]` `com/tridium/sys/schema/ComponentSlotMap.java:1366-1402`. The old value is captured **before** the
action executes (so an `override`/`set` action's prior priority-array value is read before it is
overwritten) and threaded into the `AuditEvent`'s `oldValue` field only if the invoking `Context` carries a
non-null `BUser` (`isAuditable`) — identical audit-gate semantics to N4 (§41.4). `getOldValueForPendingActionAuditEvent`
is otherwise never referenced outside its own interface declaration and its four implementers (§41.3).

`WritableSupport.toOldValueAuditString(BControlPoint, Property, Context)` — the static helper every
implementer delegates to — formats the string via a lexicon key, not a raw value dump:
```java
static String toOldValueAuditString(BControlPoint point, Property prop, Context cx) {
   return LEX.getText("actionAuditOldValue", cx, new Object[]{
      ComplexSlotMap.toAuditString(point, prop, point.get(prop), cx),
      ComplexSlotMap.toAuditString(point, point.getOutProperty(), point.get(point.getOutProperty()), cx)
   });
}
```
`[CERT]` `niagara/control/WritableSupport.java:269-278` — it reports **both** the priority-slot's current
value (before being overwritten) **and** the point's current `out` value in the same string, giving the
audit reader "what the slot held" and "what the point was outputting" at the moment of write, not just a
single scalar.

## 41.2 — `AuditEvent`/`Auditor`: record shape and dispatch (`ComplexSlotMap`) `[CERT]`

`AuditEvent` (`niagara/security/AuditEvent.java:9-39`) is a plain value object: `operation` (one of 13
named constants — `Changed`/`Added`/`Removed`/`Renamed`/`Reordered`/`Flags Changed`/`Facets Changed`/
`Recategorized`/`Invoked`/`Login`/`Logout`/`Login Failure`/`Logout (Timeout)`), `target` (slot-path string),
`slotName`, `oldValue`, `value`, `userName`, and a `BAbsTime timestamp` stamped at construction via
`Clock.time()`. `[CERT]` `AuditEvent.java:9-39`. `Auditor` is a one-method interface,
`void audit(AuditEvent)` `[CERT]` `niagara/security/Auditor.java:3-4`. This shape is **byte-identical** to
N4's `javax.baja.security.AuditEvent`/`Auditor` per the N4 corpus (B564 §564, already token-checked there) —
N5 only renamed the package `javax.baja.security` → `niagara.security` (the whole-tree N4→N5 package rename
already established generically in earlier blocks).

The dispatcher lives in `ComplexSlotMap`, not `ComponentSlotMap` — every `add`/`remove`/`rename`/`reorder`/
`change`/flags/facets/recategorize AND the `Invoked` case from §41.1 funnel through one private `audit(...)`
overload that gates on the **target `BComponentSpace`'s own class** carrying `@AuditableSpace`:
```java
public final void audit(OrdQuery targetPath, BUser user, String op, String slotName, String oldValue, String value) {
   BComponentSpace componentSpace = this.getSpace();
   if (componentSpace != null) {
      if (componentSpace.getClass().isAnnotationPresent(AuditableSpace.class)) {
         Auditor auditor = Nre.auditor;
         if (auditor != null && targetPath != null) {
            auditor.audit(new AuditEvent(op, targetPath.getBody(), slotName, oldValue, value, user.getUsername()));
         }
      } else if (log.isLoggable(Level.FINE)) { /* "auditing was disallowed for Space" */ }
   }
}
```
`[CERT]` `com/tridium/sys/schema/ComplexSlotMap.java:1725-1750`. `@AuditableSpace`
(`niagara/space/AuditableSpace.java:8-9`) is `@Retention(RUNTIME) @Target(TYPE)` with **no `@Inherited`
meta-annotation** `[CERT]`, so `Class.isAnnotationPresent()` only returns true for a class **literally**
carrying the annotation, not an unannotated subclass of an annotated one. The base `niagara.space.
BComponentSpace` itself carries `@AuditableSpace` `[CERT]` `niagara/space/BComponentSpace.java:67-68`, and
the running station's own root component space (`station:` scheme) is instantiated as a **direct**
`BComponentSpace`, not a further subclass — `space = new BComponentSpace("station", ...,
BOrd.make("station:"));` `[CERT]` `com/tridium/sys/station/Station.java:190` — so the primary station space
is audited by construction. Two other concrete spaces re-declare the annotation explicitly:
`BVirtualComponentSpace` `[CERT]` `niagara/virtual/BVirtualComponentSpace.java:21-22` and (module) `BOrionSpace`
`[CERT]` `com/tridium/orion/BOrionSpace.java:31-32`. Any *other* `BComponentSpace` subclass that does **not**
re-declare `@AuditableSpace` (three found with no annotation: `BModulePaletteNode`, `BBogSpace`,
`BToolSpace`, `BAceSpace`) is silently **excluded** from the `AuditEvent` trail — `[INFER]`: the annotation's
lack of `@Inherited` is a deliberate per-space opt-in, not an oversight, since the framework re-declares it
explicitly on every space that needs it.

`Nre.auditor` (`com/tridium/sys/Nre.java:118`) is a single static field, set/cleared via
`Sys.setAuditor(Auditor)`/`Sys.getAuditor()` `[CERT]` `niagara/sys/Sys.java:168-173` — one pluggable auditor
station-wide, matching N4's identical `Sys.getAuditor()` singleton design (N4 corpus B564 §564.1).

## 41.3 — Where it is stored: `BAuditHistoryService`, and the census of implementers `[CERT]`

`BAuditHistoryService` (`com/tridium/history/audit/BAuditHistoryService.java:44`) is the **sole** `Auditor`
implementer found across the whole decompiled tree (the only other `implements ... Auditor`-pattern hits are
`niagara.nre.security.SecurityAuditor` implementers, a **separate** interface/event pair for login-centric
security events — see below). It registers itself via lifecycle hooks:
```java
protected void auditStarted() { Sys.setAuditor(this); }
protected void auditStopped()  { Sys.setAuditor(null); }
public void audit(AuditEvent event) {
   boolean shouldAudit = checkSecurityAudit(event);
   if (shouldAudit) { this.audit(BAuditRecord.fromEvent(event)); syslogAuditHandler.publish(event, false); }
}
```
`[CERT]` `BAuditHistoryService.java:87-113`. Its `historyConfig` property default is
`new BHistoryConfig(BHistoryId.make("station", "AuditHistory"), BTypeSpec.make("history", "AuditRecord"))`
`[CERT]` `BAuditHistoryService.java:35-38` — the audit trail is an ordinary station history named
`$/AuditHistory` of record type `history:AuditRecord`, appended through the same `HistorySpaceConnection`/
`BFileHistoryTable` machinery Block 33 (N4 corpus) already documents; no separate audit-specific storage
engine exists. `checkSecurityAudit()` is a **routing filter, not a gate on the config-audit trail itself** —
every event still reaches `BAuditRecord.fromEvent(event)`/history append (`shouldAudit` from `audit()` above
is actually a hardcoded artifact of the method's own control flow — re-reading it, `checkSecurityAudit`'s
`return false` paths correspond to operations it has *already* re-routed to the parallel `SecurityAuditor`
channel — `Login`/`Logout`/`Login Failure`/`Logout (Timeout)`/`Recategorized` and the security-flagged-
property branches of `Added`/`Renamed`/`Removed`/`Changed`); the two channels are not mutually exclusive for
every operation — a `Changed` event on a `security`-facet property is dual-published to **both** the config
`AuditHistory` (`BAuditRecord`) and, via `SecurityAuditEvent`, the syslog/security handler `[CERT]`
`BAuditHistoryService.java:180-217` (`securityAuditHandler.publish(event, true)` always follows a
`securityAuditor.audit(...)` call in every branch that reaches it, and the outer `audit(AuditEvent)` always
appends to history regardless of `shouldAudit`'s value — `shouldAudit` in fact never evaluates `false`
for a real operation; every branch explicitly `return`s `true` or `false` but **all** paths fall through to
`this.audit(BAuditRecord.fromEvent(event))` in the caller because `checkSecurityAudit`'s return value is
used only to decide the syslog dual-publish for a small subset — `[INFER]`: re-reading the caller,
`shouldAudit` DOES gate the outer `if` at `BAuditHistoryService.java:107-110`, so a `Recategorized` event
(the one `return false` case reached from the main branch) is **excluded from `AuditHistory`** and goes
**only** to the security channel; every other operation reaches both `BAuditRecord` history AND,
conditionally, the security channel).

`BAuditRecord` (`com/tridium/history/audit/BAuditRecord.java:29`) is the persisted record type — properties
`target`/`slotName`/`oldValue`/`value`/`userName` plus inherited `operation`
(`BAbstractAuditRecord.java:13`) and `timestamp` (`BHistoryRecord` base) — a direct 1:1 field mapping from
`AuditEvent` via `BAuditRecord.fromEvent(AuditEvent)` `[CERT]` `BAuditRecord.java:112-116`.

**Census — types implementing `BIActionAuditProvider`** (whole-tree `grep`, this session): exactly **four**,
all in `niagara.control`, all writable-point types, all delegating to the same
`WritableSupport.toOldValueAuditString` helper with per-action-name routing:
`BNumericWritable` (`niagara/control/BNumericWritable.java:443-450` —
`set`→`fallback` property, `override`/`auto`→`in8`, `emergencyOverride`/`emergencyAuto`→`in1`),
`BBooleanWritable`, `BStringWritable`, `BEnumWritable` `[CERT]` (all four files grep-confirmed to contain
`getOldValueForPendingActionAuditEvent`; the numeric one's full switch body was read directly — the other
three were confirmed present by token, not read in full, since their shape is structurally identical per
Block 20's finding that `WritableSupport` itself is shared). No other component type in the decompiled tree
implements the interface `[CERT]` (0 additional hits in the whole-tree `grep -rl`).

## 41.4 — The N4→N5 delta: a real fix for a documented gap, same audit-gate ceiling `[CERT]`+`[INFER]`

N4's identical call site (`ComponentSlotMap.invoke`, same class name, sibling corpus) **hardcodes** `null`
for the `Invoked` operation's old value, unconditionally, for every action on every component type:
```java
this.audit(ComponentSlotMap.getAuditSlotPath(instance, context), user, "Invoked", action.getName(), null,
           toAuditString(instance, action, arg, context));
```
`[CERT]` `N4: com/tridium/sys/schema/ComponentSlotMap.java:1366` (sibling corpus
`niagara-research/organized/baja/baja/vineflower/...`, confirmed by direct read this session — no
`instanceof BIActionAuditProvider` branch exists anywhere in that N4 file; `grep` for the interface name
across the whole N4 corpus returns zero hits, §B20-G3's premise). This means: in N4, an operator overriding
a writable point's value through the `override`/`set`/`auto` action produces an `AuditEvent(Invoked, ...,
oldValue=null, value=<new value>)` — the audit history records **that** a write happened and **to what**,
but never **from what**. N5's `BIActionAuditProvider` mechanism (§41.1) is a genuine, targeted fix for
exactly this gap, scoped precisely to the four writable-point types that most need it (operator overrides
are the highest-frequency manual-write action in a BAS). `[INFER]`: this closes the specific slice of the
"no who-changed-what audit today" concern (project memory,
`panccadia-access-model-viewer-writeserver`) that is about the **value diff**, not the **attribution** — see
next paragraph for why attribution itself is unchanged.

**What did NOT change: the audit gate.** N5 preserves the exact same `context != null &&
context.getUser() != null` gate pattern at every audit-relevant call site in `ComponentSlotMap`/
`ComplexSlotMap` (`property set` at `ComponentSlotMap.java:437-438`, `invoke` at `:1352-1353`, and 8 further
occurrences through the file) `[CERT]` (grep-counted, this session). This is **structurally identical** to
the N4 finding already sealed in the N4 corpus (B829/B830): `ComplexSlotMap.set`/`invoke` only builds an
`AuditEvent` when the write's `Context` carries a real `BUser`; a `null`-`Context` write (e.g., a servlet
calling `component.set(prop, value, null)` instead of threading the authenticated `Context` through) is
**silently unaudited**, not merely unattributed. N5 does not add a fallback, a warning, or a forced-Context
requirement — the ceiling on "who changed what" that B829/B830 measured against N4's DashboardPan servlet
write path is **unchanged in N5**: whether a write is audited at all still depends entirely on the caller
choosing to pass a real `Context`, and §41.6–§41.8 below show that the web layer *does* make a real,
authenticated `Context` available to a `BWebServlet` subclass via `"niagara.context"` — but only if that
subclass's `doPost`/`doPut` handler actually uses it when calling `set()`/`invoke()`, which this block
cannot verify for third-party module code (out of scope; the N4 corpus's B829 already found DashboardPan's
own servlet passes `null`).

## 41.5 — `NiagaraConstraintSecurityHandler`: the URL-constraint model is one blanket rule, not per-path `[CERT]`

The entire class is 10 lines of logic:
```java
protected Constraint getConstraint(String pathInContext, Request request) {
   Class<? extends Servlet> servletClass = ((MappedServlet)((ServletContextRequest)request)
      .getMatchedResource().getResource()).getServletHolder().getHeldClass();
   return !UnauthenticatedServlet.class.isAssignableFrom(servletClass)
       && !UnauthenticatedWebSocketServlet.class.isAssignableFrom(servletClass)
       ? super.getConstraint(pathInContext, request) : Constraint.ALLOWED;
}
```
`[CERT]` `com/tridium/jetty/NiagaraConstraintSecurityHandler.java:13-20`. It overrides Jetty's normal
path-pattern constraint lookup with a **class-based** exemption: if the servlet resolved for this request
(via Jetty's already-matched `MappedServlet`) extends either marker base class, the constraint is
`Constraint.ALLOWED` (no auth required); otherwise it falls through to the ordinary constraint-mapping
lookup (`super.getConstraint`). That ordinary lookup has exactly **one** registered mapping, built in
`BJettyWebServer.makeAllMapping()`:
```java
constraint.name("FORM"); constraint.authorization(Authorization.SPECIFIC_ROLE);
constraint.roles(new String[]{String.valueOf(Authorization.ANY_USER), String.valueOf(Authorization.KNOWN_ROLE)});
if (service.getHttpsEnabled() && service.getHttpsOnly()) { constraint.transport(Transport.SECURE); }
mapping.setPathSpec("/*");
```
`[CERT]` `com/tridium/jetty/BJettyWebServer.java:1316-1329`, installed via
`security.setConstraintMappings(Collections.singletonList(makeAllMapping()))` `[CERT]`
`BJettyWebServer.java:1266`. **Answer to "which URL constraints require auth": all of them (`/*`), with
exactly one path-independent exemption class** — a servlet whose registered implementation class extends
`UnauthenticatedServlet` or `UnauthenticatedWebSocketServlet`. There is no declarative `web.xml`
`<security-constraint>` (confirmed already by Block 27 §27.1) — the whole model is these ~12 lines across
two classes plus the marker-class census below.

**Census — servlets registered as `Unauthenticated*`** (whole-tree grep, this session): 8 —
`niagara.web.servlets.{LoginServlet, PreloginServlet, LoginFileServlet}` (registered directly in
`configureNiagaraWebApp`, §41.6), `com.tridium.clientCertAuth.web.ClientCertAuthServlet`,
`com.tridium.fox.sys.FoxWebSocketServlet`, `com.tridium.saml.rp.servlet.{SAMLRPServlet,
SAMLConsumerServlet}`, `com.tridium.saml.idp.SAMLIdPAuthnRequestServlet` `[CERT]` (8 files, grep-confirmed
`extends UnauthenticatedServlet`/`extends UnauthenticatedWebSocketServlet`). Every one of these is either
part of the login flow itself (chicken-and-egg — you cannot require auth to reach the login page) or an
external-IdP handshake endpoint (SAML/cert/Fox) that authenticates by a different mechanism than the Niagara
session cookie.

## 41.6 — `NiagaraAuthenticator`: request flow from Jetty to a Niagara `UserIdentity` `[CERT]`

`NiagaraAuthenticator extends org.eclipse.jetty.security.authentication.LoginAuthenticator`, registered as
`security.setAuthenticator(this.authenticator)` on the same `ConstraintSecurityHandler` in
`configureNiagaraWebApp` `[CERT]` `BJettyWebServer.java:1265-1267`. Its `validateRequest(Request, Response,
Callback)` `[CERT]` `com/tridium/jetty/NiagaraAuthenticator.java:108-205` is the single entry point Jetty
calls per protected request, and it branches on the **same** `UnauthenticatedServlet`/
`UnauthenticatedWebSocketServlet` class check as §41.5 (`if (!Unauthenticated...isAssignableFrom(servletClass))`
at `:136`) — for those it immediately `return AuthenticationState.defer(this)`, i.e. no login required.
For everything else, in order:
1. **`/j_security_check`** (`isJSecurityCheck(uri)`, `:138,674-687`) → `jSecurityCheck(req, resp)`
   (`:211-392`), the actual credential-verification path (login form POST target).
2. **`super_session_id` cookie** (`:146-149`) → if it names an authenticated `SessionManager` session,
   binds that session as the request's `NiagaraWebSession`.
3. **Existing session attribute** `"org.eclipse.jetty.security.UserIdentity"` (`:151-160`) → already-logged-in
   fast path, returns the cached `AuthenticationState` unchanged.
4. **`Authorization` header** (`:162-169`) → `authenticateHeader(...)` (`:394-535`) — HTTP Basic or a
   Niagara-proprietary `HELLO` scheme (`AuthMessage`), used by non-browser/API clients (fox/bql/REST callers
   that cannot do a form POST).
5. **`SecurityCheckServlet`** target class (`:170-176`) → `authenticateServlet(...)` (`:537-592`), a
   servlet-declared authentication scheme path (`SecurityCheckServlet.getConfiguredAuthenticationScheme()`).
6. **Fallback** (`:177-197`): redirect to `/login` (or `/login?auth=fail`), `AuthenticationState.CHALLENGE`.

`jSecurityCheck()` resolves the applicable `BAuthenticationScheme` (per-user via
`BUserService.getAuthenticationSchemeForUser`, or discovered from the request via
`FormsAndSchemesHandler`), drives it through a `BWebCallbackHandler.handleRequest(req, resp)` state machine
(response codes: 0=success, 1=challenge, 2=redirect-to-login, 3=fail), and on success calls
`this.login(username, session, request, response)` → `super.login(...)` (Jetty's standard
`LoginAuthenticator.login`, which resolves a Jetty `UserIdentity` via the configured `LoginService` — not
re-derived here, out of this block's scope) and returns a `NiagaraAuthenticator.NiagaraAuthentication`
(`UserAuthenticationSent`+`ResponseSent`) or, on the header path, a `NiagaraUserAuthentication`
(`UserAuthenticationSucceeded`+`Succeeded`) `[CERT]` `:743-753`. Both carry the resolved Jetty `UserIdentity`
forward — this is what later surfaces as `req.getUserPrincipal()` for the servlet layer (§41.7).

## 41.7 — How a `BWebServlet` subclass gets the authenticated user: `niagara.context`, not `getUser()` `[CERT]`

`BWebServlet` has **no** `getUser()`/`getContext()` method of its own. Its `doService(HttpServletRequest,
HttpServletResponse)` reads a pre-populated request attribute:
```java
Context cx = (Context)req.getAttribute("niagara.context");
if (!this.getPermissions(cx).hasOperatorRead()) { resp.sendError(403); }
```
`[CERT]` `niagara/web/BWebServlet.java:70-97` (§41.8 covers the permission check). That attribute is set by
one filter, `ContextFilter`, registered `/*` alongside the security handler in the same
`configureNiagaraWebApp` method (`context.addFilter(ContextFilter.class, "/*", null)` `[CERT]`
`BJettyWebServer.java:1290`):
```java
public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) {
   HttpServletRequest req = (HttpServletRequest)request;
   BUser user = (BUser)req.getUserPrincipal();
   BasicContext context = new BasicContext(user, req.getLocale().toLanguageTag());
   if (user != null) { context = new BasicContext(context, BFacets.make("username", BString.make(user.getUsername()))); }
   req.setAttribute("niagara.context", context);
   chain.doFilter(req, response);
}
```
`[CERT]` `com/tridium/web/filters/ContextFilter.java:16-26`. `req.getUserPrincipal()` is standard
Jetty/Servlet API surface populated by the container from the `UserIdentity` the security handler/
`NiagaraAuthenticator` resolved during `validateRequest` (§41.6) — Jetty's `SecurityHandler` wraps the
`ServletHandler` that runs the filter chain, so authentication completes before any `/*` filter (including
`ContextFilter`) executes `[INFER]`: this ordering follows from both being configured on the same
`ServletContextHandler` via `setSecurityHandler`/`addFilter` (`BJettyWebServer.java:1265-1290`) and Jetty's
documented handler-wraps-servlet-handler architecture; not independently traced through Jetty's own source
in this session.

**This answers the servlet-audit question directly.** A `BWebServlet` subclass that calls
`component.set(prop, value, cx)` / `component.invoke(action, arg, cx)` using **this same `cx`** (the
`"niagara.context"` attribute) passes a `Context` whose `getUser()` returns the real authenticated `BUser` —
which satisfies `ComponentSlotMap`'s `context != null && context.getUser() != null` gate (§41.4), so the
resulting write **is** audited, attributed to that user's `getUsername()`. A subclass that instead calls
`set(...)`/`invoke(...)` with `null` (or a locally-constructed `Context` that drops the user) bypasses the
gate — exactly the N4 DashboardPan finding (B829/B830) this block confirms is architecturally unchanged in
N5 (§41.4). One further filter matters for *session*-scoped API callers specifically:
`AddSubjectFilter` (registered before `TridiumSecurityFilter`/`ContextFilter`, `:1287`) additionally runs
the rest of the chain under the session's JAAS `Subject` via `SecurityUtil.callAs(subject, ...)` when an
authenticated `NiagaraSession` exists `[CERT]` `com/tridium/web/filters/AddSubjectFilter.java:26-46` — a
second, JAAS-level user-context mechanism parallel to the `niagara.context` request attribute, for code that
checks the ambient `Subject` rather than reading the servlet request attribute.

## 41.8 — Permission check on servlet access: `BPermissions` via `getPermissions(Context)`, not a per-servlet ACL component `[CERT]`

`BWebServlet.doService()`'s `this.getPermissions(cx).hasOperatorRead()` check (§41.7 quote) is inherited —
`BWebServlet` does not override `getPermissions`; it resolves through the ordinary `BComponent` permission
chain (the same mechanism a Workbench nav-tree node or any protected component uses,
`niagara.security.BIProtected`/`BPermissions` — already established generically by earlier blocks' security
coverage, not re-derived here). `[INFER]`: this means a `BWebServlet` component instance is **itself** a
security-checkable node in the station tree — an operator needs read permission **on that servlet
component** (wherever it is mounted) to reach `doGet`/`doPost` at all, layered *underneath* the
authentication requirement from §41.5–§41.6 (you must be logged in as *some* user, AND that user needs
`hasOperatorRead()` on this specific servlet component) — a two-layer check (session-level: are you
authenticated; component-level: are you allowed to read *this* servlet), not a single flat gate. No
separate per-servlet ACL/constraint list exists beyond ordinary component permissions — confirmed by the
absence of any additional permission-check API on `BINiagaraWebServlet`
(`niagara/web/BINiagaraWebServlet.java:11-20` — only `getServletName`/`getHttpServlet`/
`setValidServletName`).

## 41.9 — Self-verification

**Token check.** Every load-bearing `[CERT]` `file:line`/method citation above was `grep -n`/read directly
this session (not hand-recalled): `getOldValueForPendingActionAuditEvent` (5 hits: interface + 4
implementers), `toOldValueAuditString` (definition + 4 call sites), `@AuditableSpace` (6 hits: declaration +
5 annotated/checked classes), `Nre.auditor`/`Sys.getAuditor`/`Sys.setAuditor` (4 hits), `new
BComponentSpace("station"` (1 hit, `Station.java:190`), `"niagara.context"` (24 files; 2 read in full —
`BWebServlet.java`, `ContextFilter.java`), `setAttribute("niagara.context"` (1 hit, confirming `ContextFilter`
is the sole producer), `UnauthenticatedServlet`/`UnauthenticatedWebSocketServlet` (8 implementer files +
2 marker-class definitions + the constraint-handler check), `makeAllMapping`/`setConstraintMappings`/
`setAuthenticator` (`BJettyWebServer.java`, read directly), N4 `ComponentSlotMap.java:1366` (read directly
in the sibling corpus, confirming the hardcoded `null` and the absence of any `BIActionAuditProvider`
reference in that file) — **46 tokens checked, 0 absent, 0 downgraded**.

**Marker tally — mechanized, literal `verify-block.sh` output** (run this session, matching Block 20's
convention; Block 27 predates the tool being usable on this corpus and self-counted by hand instead):

```
$ /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block41.md /home/cristian/niagara5-research
== verify-block: niagara5-block41.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 3  (adj 2)
   [CERT-live] 0
   [CERT] 45  (adj 43)
   [CERT-doc] 2  (adj 1)
   [CERT-web] 3  (adj 2)
   [CERT-a] 2  (adj 1)
   [INFER] 11  (adj 9)
-- ratio -- [INFER]/[CERT*] = 9/49 = 0.18
-- [CERT] file:line citation resolution --
   synth-ref  [B33] / [B408] / [B564] / [B829] / [B830]  (block back-references — not file-verifiable)
   extern  (31 citations)  — every N5 `file:line` citation (this corpus's own `organized/` tree, cited as
            short-form `Module.java:NN` or full `path/Module.java:NN` — neither form matches the script's
            expected on-disk layout for this corpus) and the one N4 citation (sibling corpus, cited
            `N4: com/tridium/sys/schema/ComponentSlotMap.java:1366`) — EXPECTED per METHODOLOGY §11's
            decompiled-tree-blocks convention; the burden for these 31 falls entirely on the inline
            token-verify reported above (46 tokens checked, 0 absent).
   resolved 0 of 36
== exit 0 ==
```

The raw `[CERT-hw]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` non-zero counts above are **not** claims in this
block's body — this block cites zero hardware/doc/web/forum sources (pure decompiled-source read). They are
the tool over-counting this very self-verify section's own prose, which names those marker tokens in
backticks while stating "0 each" (e.g. the sentence discussing "no doc/web/forum/hardware source used") —
the same RAW-vs-ADJUSTED distortion METHODOLOGY §11 documents for a block that quotes another block's
markers; here it is this block quoting the marker *names* themselves, not another block's claims. The
adjusted `[INFER]`/`[CERT]` ratio of **0.18** is otherwise directly usable: low, consistent with a `mixed`
block whose 7 distinct synthesis claims (§41.2's non-`@Inherited` opt-in-by-design reading, §41.3's
`checkSecurityAudit`/`shouldAudit` gating resolution, §41.4's "closes the value-diff slice of the PANCCADIA
gap" synthesis, §41.7's handler-wraps-filter-chain ordering, §41.8's two-layer-check characterization, and
two narrower inline INFERs) are each built from named `[CERT]` facts in this block or the cited N4 blocks,
not free-standing.

**Citation resolution.** `resolved 0 of 36` is the **expected signature for a decompiled-tree block**
(METHODOLOGY §11's explicit convention) — every N5 citation points into this corpus's own pre-existing
`organized/...` decompiles (not scratch/session-temp, unlike Blocks 20/27 which decompiled fresh this
session), but the script's citation-resolver does not match either the short-form (`ComponentSlotMap.java:1366`)
or qualified (`com/tridium/sys/schema/ComponentSlotMap.java:1366`) forms used in this block's prose against
files actually on disk at those paths — this is a citation-FORMAT gap in this corpus's tooling, not a
missing-source gap (every cited path was confirmed to exist and was read directly this session; see Token
check above). The single N4 citation is legitimately `extern` (sibling corpus, by design — same convention
Block 20 used for its N4 citations).

**Artifacts**: this block file exists at `/home/cristian/niagara5-research/niagara5-block41.md`. Per this
task's explicit read-only/single-file constraint, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not**
regenerated or hand-edited — flagged here for the next iteration/orchestrator to pick up (mirrors Block 27's
same disclosure).

**MCP-doc snapshots**: N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 41.10 — Child gaps

- **B41-G1** — `SecurityAuditEvent`/`SecurityAuditor` full mapping: this block traced only the dispatch
  edges from `BAuditHistoryService.checkSecurityAudit()` into the security channel (login/logout/
  security-flagged-property operations); it did not open `niagara.nre.security.{SecurityAuditor,
  SecurityAuditEvent,DefaultSecurityAuditor}` (`organized/_bin-ext/nre/vineflower/niagara/nre/security/`,
  already decompiled in this corpus) to document that channel's own record shape, storage, and consumers
  end-to-end (syslog only, or also a history?). `investigable` — files already present in-corpus.
- **B41-G2** — `SessionManager.getAuthenticatedSubjectFromSession`/JAAS `Subject` construction
  (`AddSubjectFilter`, §41.7): what principals/roles the `Subject` actually carries, and whether any
  in-station code branches on it differently than on the `niagara.context` `BUser` — not traced here.
  `investigable`.
- **B41-G3** — `LoginService`/`UserIdentity` resolution inside Jetty's `super.login(...)` call
  (`NiagaraAuthenticator.login`, §41.6): this block treated it as standard Jetty machinery and did not
  decompile/trace the configured `LoginService` implementation that maps a Niagara username to a Jetty
  `UserIdentity` with roles. `investigable`.
- **B41-G4** — Live confirmation (`[CERT-hw]`): stand up an N5 5.0.0.28 station, perform an `override`
  action on a `BNumericWritable` point as a web-authenticated user (threading `niagara.context` through, if
  a test module is built to do so), and read back the resulting `history:$/AuditHistory` `BAuditRecord` to
  confirm `oldValue` is populated exactly as §41.1/§41.4 predict from static reading. `blocked-on-source` —
  no runnable N5 station this session (same blocker as Blocks 2/4/10/20/21/27's `B27-G1`).
- **B41-G5** — Whether any first-party N5 module's own `BWebServlet` subclass (in the modules already
  decompiled in this corpus) actually threads `niagara.context` through to a `set()`/`invoke()` call — this
  block established the *mechanism* exists and is available, but did not grep first-party servlet
  implementations (`niagara/web/servlets/*`, `com/tridium/*/servlets/*`) for whether they use it correctly.
  Directly relevant to whether N5's own shipped servlets (as opposed to third-party modules like
  DashboardPan) are audit-clean. `investigable`.

## 41.x — Connections

- **[Block 20]** — §20.3 found the `BIActionAuditProvider`/`toOldValueAuditString` API surface and its N4
  absence but left the consumer/storage chain and the "is it wired up or scaffolding" question as **B20-G3**
  (this block's §41.1–§41.4 close it): the mechanism is fully wired, not scaffolding — `BAuditHistoryService`
  is the sole `Auditor`, and the action-audit path reaches real persisted history the same way every other
  `AuditEvent` does.
- **[Block 27]** — §27.4 read `configureNiagaraWebApp()`'s programmatic `TridiumSecurityFilter`/
  `security.setAuthenticator(this.authenticator)` registration but explicitly deferred
  `NiagaraConstraintSecurityHandler`/`NiagaraAuthenticator` as **B27-G3** (closed here, §41.5–§41.6); §27.6's
  CSRF-token finding (`x-niagara-csrfToken`) and this block's authentication chain are complementary
  layers of the same request (CSRF protects the authenticated session from cross-site forgery; this block's
  chain establishes that session in the first place). §27.4's **B27-G4** (`NModuleInfo.isWar()`) remains
  open and unrelated to this block's scope.
- **N4 corpus (remit)** — **[B564]** (the `Sys.getAuditor()`/`AuditEvent`/`Auditor`/`SecurityAuditor` wiring,
  byte-identical package-renamed architecture, confirmed carried forward §41.2), **[B408]** (the
  `AuditableSpace` annotation and `ComplexSlotMap.audit()` dispatch, confirmed identical §41.2), **[B829]**/
  **[B830]** (the null-Context audit bypass on the DashboardPan servlet write path — this block's §41.4/§41.7
  confirms the exact same gate exists in N5, with no change to the attribution ceiling, while §41.1's new
  `BIActionAuditProvider` mechanism closes the separate value-diff gap for the `Invoked` operation on
  writable points specifically), **[B33]** (history storage/`.hdb` format that `AuditHistory` rides on top
  of, REMIT, not re-derived here).
