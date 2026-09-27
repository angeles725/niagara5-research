# Block 68 — Closing the web/servlet-auth cluster: first-party N5 servlet write-audit census, JAAS `Subject` contents, Jetty `LoginService`/`UserIdentity`, and `NModuleInfo.isWar()`/`hx.jar` WebAppContext registration

> Research closing **four named child gaps** left open across [Block 27] and [Block 41] (the N5
> web-server security/audit cluster): **B41-G5** ("whether any first-party N5 module's own `BWebServlet`
> subclass actually threads `niagara.context` through to a `set()`/`invoke()` call") together with the
> related **B46-G3** ("whether the read-side `BOrd.make(...).get(this, null)` ORD-resolution calls should
> also receive the real `cx` for permission-scoped resolution"); **B41-G2** (JAAS `Subject`/
> `AddSubjectFilter` contents — what principals/roles the `Subject` actually carries); **B41-G3**
> (`LoginService`/`UserIdentity` resolution inside Jetty's `super.login(...)`); **B27-G4**
> (`NModuleInfo.isWar()`'s exact definition); **B27-G5** (whether `hx.jar` registers its own
> `WebAppContext`/servlets or rides the same `configureNiagaraWebApp()` path as every other module).
> Covers: a whole-tree census of first-party servlets/filters that recover `"niagara.context"` (both the
> `BWebServlet`/`WebOp` path and the plain-`HttpServlet` `req.getAttribute` path), representative
> write-capable servlets from that census read in full to classify whether their write call actually
> threads `Context` to `BComplex.set(...)`/`BComponent.add(...)`/`invoke(...)`, the 2-arg
> convenience-overload mechanism that silently drops `Context` (`BComplex.java`/`BComponent.java`), the
> full JAAS `Subject` construction path (`BAuthenticationService.authenticate()`), the full Jetty
> `LoginService`→`UserIdentity` resolution (`NiagaraLoginService`/`NiagaraUserIdentity`), `NModuleInfo`'s
> `isWar` flag and where `Builder` sets it, and `hx.jar`'s complete absence of any servlet/`WebAppContext`
> registration of its own. Does **not** cover: a live-station `$/AuditHistory`/`$/SecurityHistory`
> readback of any finding here (`[CERT-hw]`, blocked — no runnable N5 station this session, same
> constraint as [Block 41]'s **B41-G4** and [Block 46]'s **B46-G4**); the JAAS `LoginModule`
> implementation(s) a `BAuthenticationScheme.login(handler)` actually selects (out of scope — this block
> traces up to and past `LoginContext.getSubject()`, not into the module chain itself, a further-child
> gap named below); per-`BOrdScheme` (`station:`, `file:`, etc.) read-permission enforcement when the
> resolving `Context`'s user is `null` (narrowed, not fully traced — see **B68-G3**); or porting any fix
> for the dropped-`Context` writes found here back into shipped module source (research-only, no source
> was modified this session, unlike [Block 46]'s PoC).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as Blocks 27/41/46/54
> (`etc/brand.properties:workbench.notice`). All sources are files already decompiled in-corpus by prior
> sessions (`organized/*/vineflower/`, Vineflower — `tools/n5-decompile.sh`); no fresh decompilation was
> run this session, and no decompiled code was committed to git per task instruction. File `mtime`s under
> `organized/` are unchanged from their original decompile session, so no new source-authenticity stamp
> applies beyond the sha256 hashes already recorded for `web.jar`/`jetty.jar`/`baja.jar` in [Block 27]/
> [Block 41]'s headers (re-used here, not re-hashed).
>
> Sources: `organized/web/vineflower/{niagara/web/{BWebServlet,WebOp,servlets/NiagaraRpcServlet}.java,
> com/tridium/web/{filters/AddSubjectFilter.java, servlets/{NWebOp,FileServlet}.java}}`,
> `organized/jetty/vineflower/com/tridium/jetty/{NiagaraLoginService,NiagaraUserIdentity}.java`,
> `organized/baja/vineflower/{niagara/{sys/{BComplex,BComponent,BasicContext}.java, naming/{BOrd,OrdTarget}.java,
> sys/registry/{NModuleInfo,Builder}.java}, com/tridium/{authn/BAuthenticationService.java,
> session/{SessionManager,NiagaraSession}.java}}`, `organized/httpClient/vineflower/com/tridium/httpClient/
> servlet/BStringServlet.java`, `organized/uxBuilder/vineflower/com/tridium/uxBuilder/{servlet/UxBuilderServlet.java,
> ui/UxMediaUtil.java}`, `organized/bacnetAws/vineflower/com/tridium/bacnetAws/servlets/BacnetAwsServlet.java`,
> `organized/hierarchy/vineflower/com/tridium/hierarchy/HierarchyServlet.java`,
> `organized/hx/vineflower/{META-INF/module.xml, niagara/hx/HxOp.java}` (plus a whole-tree `find`
> confirming no `WEB-INF/` entry exists anywhere under `organized/hx/`). [Block 41] §41.1–§41.8, [Block 46]
> §46.1–§46.2, [Block 27] §27.1/§27.4, [Block 54] §54.4 (REMIT, cited not re-derived for the
> `NiagaraRpcUtil.rpc()` injection trace).
>
> Method: `grep -rln`/`grep -rn` whole-tree census across every `organized/*/vineflower/` directory for
> `"niagara.context"` and for `extends BWebServlet`/`extends HttpServlet`, this session; direct full or
> targeted reads of every file the census surfaced that also matched a write-signal grep
> (`\.set(\|\.invoke(\|\.submit(\|\.add(`); a constructor-chain trace (`NWebOp`→`WebOp`→`OrdTarget`) to
> determine whether a `BWebServlet` subclass's `WebOp` parameter itself carries the real authenticated
> user; a second constructor-chain trace (`BOrd.get(base,cx)`→`resolve(base,cx,null)`→`new
> OrdTarget(cx,...)`→`BasicContext(cx)`) to determine what a `null` `Context` resolves to.
> Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device — highest ·
> `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official downloaded document ·
> `[CERT-web]` official web · `[CERT-a]` secondary source/forum · `[INFER]` deduction.
> `file:line` citations below use the full `organized/<module>/vineflower/...` path at least once per
> cited file (METHODOLOGY §11's resolvable-anchor convention); a bare `Module.java:NN` short form appears
> in prose only where the full path for the same file already appears nearby.
>
> Web/servlet-auth layer. Connects [Block 41] (closes **B41-G5**, narrows the parallel read-side gap
> **B46-G3**, closes **B41-G2** and **B41-G3**), [Block 27] (closes **B27-G4** and **B27-G5**), [Block 46]
> (the PoC precedent this block's §68.3–§68.4 findings generalize — a dropped-`Context` write is not a
> DashboardPan-specific oversight but a reproducible pattern in first-party N5 platform modules too),
> [Block 54] (§54.4's `NiagaraRpcUtil.rpc()` Context-injection trace, REMIT, cited for the RPC write path
> in §68.4's census table).
>
> **Type:** `mixed` — §68.1–§68.6 are evidence (fresh reads of already-decompiled N5 source, a new
> constructor-chain trace not previously in this corpus); §68.7–§68.10 are evidence closing four
> previously-scoped gaps; the census table in §68.4 draws `[INFER]` verdicts across this block's own
> `[CERT]` facts plus [Block 41]'s and [Block 54]'s prior findings.

---

## 68.1 — Two parallel mechanisms recover the authenticated `Context` for a first-party servlet `[CERT]`

A whole-tree `grep -rln '"niagara.context"'` across every `organized/*/vineflower/` directory (this
session) surfaces **23 files** outside `web.jar`'s own base classes. Every one is a plain `extends
HttpServlet`/`extends Filter` class (not a `BWebServlet` subclass) that recovers the request attribute
**itself**, by hand, in its own `doGet`/`doPost`/`doPut`:
```java
Context cx = (Context)req.getAttribute("niagara.context");
```
confirmed present verbatim (whitespace-normalized) in, among others,
`organized/bajaux/vineflower/com/tridium/ux/WbWebWidgetServlet.java:73`,
`organized/analytics/vineflower/com/tridiumx/analytics/chart/AnalyticsChartFileServlet.java:32`,
`organized/bacnetAws/vineflower/com/tridium/bacnetAws/servlets/BacnetAwsServlet.java:37,69`,
`organized/hierarchy/vineflower/com/tridium/hierarchy/HierarchyServlet.java:49`,
`organized/history/vineflower/com/tridium/history/servlets/QueryServlet.java:86,122`,
`organized/nss/vineflower/com/tridium/nss/dashboard/SecurityDashboardServlet.java:38`,
`organized/uxBuilder/vineflower/com/tridium/uxBuilder/servlet/UxBuilderServlet.java:56,180`,
`organized/web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java:32`,
`organized/web/vineflower/com/tridium/web/servlets/{SpeedTestServlet.java:39,104,
LogoutConfirmServlet.java:21, RequireJsConfigServlet.java:17, FileServlet.java:123}`,
`organized/webChart/vineflower/com/tridium/webChart/{WebChartFileServlet.java:32,
WebChartQueryServlet.java:57}`, `organized/webEditors/vineflower/com/tridium/webeditors/ux/servlets/
PaletteServlet.java:33`, `organized/seriesTransform/vineflower/com/tridium/seriestransform/servlets/
SeriesTransformWebChartQueryServlet.java:51`. `[CERT]` (whole-tree grep, this session; every listed file
opened and the cited line confirmed by direct read, not grep alone). This is exactly the mechanism
[Block 41] §41.7 documented as *available* to a `BWebServlet` subclass via `ContextFilter` — this census
shows it is in fact the **dominant pattern for plain servlets that are not `BWebServlet` subclasses at
all**, each one independently re-fetching the same request attribute `ContextFilter` populated.

A separate whole-tree `grep -rln 'extends BWebServlet\b'` finds exactly **10** genuine `BWebServlet`
subclasses: `BVelocityServlet`, `BNaServlet`, `BBoxServlet`, `BStringServlet`, `BSnmpMibServer`,
`BObixServer`, `BStationOutputServlet`, `BSoapServlet`, `BClientEnvServlet` `[CERT]` (10 files,
grep-confirmed this session; `docDeveloper/vineflower/doc/servlets/webServlets.html` excluded, a doc
page not a class). These do **not** read `"niagara.context"` at all — their `doGet(WebOp)`/`doPost(WebOp)`
handler receives a `niagara.web.WebOp op` parameter instead, and §68.2 traces whether `op` itself carries
the same authenticated identity.

## 68.2 — `BWebServlet` subclasses: `WebOp` itself is a `Context`, carrying the real authenticated user through a 3-hop constructor chain `[CERT]`

`WebOp` is declared `public abstract class WebOp extends ExportOp implements SecurableContext` `[CERT]`
`organized/web/vineflower/niagara/web/WebOp.java:21` — `SecurableContext` is the same interface [Block 54]
§54.4 found `NiagaraRpcUtil.rpc()` uses to inject a `Context` into an `@NiagaraRpc` method (REMIT). A
`BWebServlet` subclass's `doPost(WebOp op)` can therefore pass `op` directly wherever a `Context` argument
is expected. Whether `op.getUser()` is the REAL authenticated `BUser` (not `null`, not an ambient identity)
depends on a 3-hop construction chain, traced fresh this session:

1. `BWebServlet.doService(HttpServletRequest req, ...)` (the private dispatch method every registered
   `BWebServlet` instance's inner `Servlet` delegates to) recovers `Context cx = (Context)
   req.getAttribute("niagara.context")` — the real, `ContextFilter`-populated attribute — checks
   `this.getPermissions(cx).hasOperatorRead()` (§41.8, REMIT), then resolves `OrdTarget target =
   this.getNavOrd().resolve(BLocalHost.INSTANCE, cx)` **using that same real `cx`**, and constructs `WebOp
   op = new NWebOp(target, service, req, resp)` — note the constructor does **not** take `cx` directly, only
   the already-resolved `target`. `[CERT]` `organized/web/vineflower/niagara/web/BWebServlet.java:70-91`.
2. `NWebOp`'s entire body is a pass-through: `public NWebOp(OrdTarget base, ...) { super(base, service, req,
   resp); }` `[CERT]` `organized/web/vineflower/com/tridium/web/servlets/NWebOp.java:10-12` (whole 13-line
   file) → `WebOp`'s own constructor `public WebOp(OrdTarget base, ...) { super(base); ... }` `[CERT]`
   `organized/web/vineflower/niagara/web/WebOp.java:32-36` → `ExportOp`'s constructor chain ultimately reaches
   `public OrdTarget(OrdTarget base) { this(base, null); }` `[CERT]`
   `organized/baja/vineflower/niagara/naming/OrdTarget.java:85-87`.
3. That resolves to `public OrdTarget(OrdTarget base, BObject object) { this.base = base; this.user =
   base.user; ... }` `[CERT]` `organized/baja/vineflower/niagara/naming/OrdTarget.java:33-37` — `this.user`
   is copied **directly** from `base.user`, i.e. from the `target` `OrdTarget` step 1 resolved using the
   real `cx`. That `target`'s own `user` field was itself set via the private 4-arg constructor
   `OrdTarget(Context cx, ...) { BasicContext temp = new BasicContext(cx); this.user = temp.getUser(); ...
   }` `[CERT]` `organized/baja/vineflower/niagara/naming/OrdTarget.java:92-100` (this constructor is what
   every `BOrdScheme.resolve()` step in `BOrd.resolve(base, cx, client)` ultimately builds on, §68.6).

**Conclusion: for a `BWebServlet` subclass, `op.getUser()` returns the real authenticated `BUser` end to
end** `[CERT]` (full 3-hop chain, all four files read directly this session) — a `BWebServlet` subclass
that calls `this.set(prop, value, op)` / `this.invoke(action, arg, op)` (passing `op` as the `Context`
argument) satisfies `ComplexSlotMap`'s `context != null && context.getUser() != null` audit gate ([Block 41]
§41.4, REMIT) exactly as a plain-`HttpServlet` subclass passing the `"niagara.context"` attribute does
(§41.7). This is a **second, previously undocumented mechanism** parallel to the one [Block 41] §41.7
traced — [Block 41] only examined the `HttpServlet`+`"niagara.context"`-attribute path; this block is the
first to trace the `BWebServlet`+`WebOp`-as-`Context` path to the same conclusion.

## 68.3 — The systemic drop point: `BComplex`'s and `BComponent`'s 2-arg convenience overloads hardcode `null` `Context` `[CERT]`

Both classes expose a **3-arg, `Context`-carrying** primitive and a **2-arg convenience wrapper** that
silently discards `Context`:
```java
public final void set(Property property, BValue value, Context context) {   // BComplex.java:400-404
   ...
   this.slotMap.set(property, oldValue, oldMap, value, value.getSlotMap(), context);
}
public final void set(Property property, BValue value) {                    // BComplex.java:406-408
   this.set(property, value, null);
}
public final void set(String name, BValue value, Context context) { ... }   // BComplex.java:467-471
public final void set(String propertyName, BValue value) {                  // BComplex.java:458-465
   Property prop = this.getProperty(propertyName);
   ...
   this.set(prop, value);   // → the 2-arg Property overload above, context = null
}
```
`[CERT]` `organized/baja/vineflower/niagara/sys/BComplex.java:400-408,458-471` (787-line file, range ends
verified). The identical shape exists on `BComponent.add`:
```java
public final Property add(String name, BValue value, Context context) {    // BComponent.java:440-442
   return this.slotMap.add(name, 0, value, value.getSlotMap(), null, context, null);
}
public final Property add(String name, BValue value) {                     // BComponent.java:444-446
   return this.slotMap.add(name, 0, value, value.getSlotMap(), null, null, null);
}
```
`[CERT]` `organized/baja/vineflower/niagara/sys/BComponent.java:428-446` (1,169-line file, range ends
verified). This is **the exact mechanism** [Block 41] §41.4/[Block 46] §46.1 already found on the
`@Generated` Slot-o-Matic setter (`setXxx(v) { setString(prop, v, null); }`, [Block 46]'s **B46-G1**) —
this block establishes it is not a Slot-o-Matic-only quirk but the **general convenience-overload contract**
of `BComplex`/`BComponent` themselves: any call site that reaches for the shorter `set(prop, value)` /
`add(name, value)` signature drops `Context` by construction, regardless of whether a real `Context` is
in scope at the call site — confirmed as the root cause of every dropped-`Context` write found in §68.4.

## 68.4 — Census of representative write-capable first-party servlets, closing B41-G5 `[CERT]`+`[INFER]`

Every servlet/filter from §68.1's census was grepped for a write signal (`\.set(\|\.invoke(\|\.submit(\|\.add(`);
files with zero hits (`HierarchyServlet.doPost` — literally `resp.sendError(406)`, `[CERT]`
`organized/hierarchy/vineflower/com/tridium/hierarchy/HierarchyServlet.java:94-96`, 107-line file — and
most of the remaining 20, which are read-only query/export endpoints) are **not audit-relevant** and are
excluded from the table. Every file that DID show a write signal was opened in full:

| Servlet | Base class | Write call | `Context` threaded to the write? | Verdict |
|---|---|---|---|---|
| `NiagaraRpcServlet` (generic RPC endpoint, `/rpc/*`) | `HttpServlet` | `NiagaraRpcUtil.rpc(..., cx)` → reflective `@NiagaraRpc` method invoke | **Yes** — `cx` from `"niagara.context"` is passed straight through; the dispatcher itself then builds a fresh `SecurableContext` whose `getUser()` is `BUser.getCurrentAuthenticatedUser()` | Audited-if-the-target-method-set()s-with-it; mechanism confirmed present ([Block 54] §54.4, REMIT — not re-derived here) |
| `BacnetAwsServlet` (`/bacnetAws/backup`,`/restore`) | `HttpServlet` | `c.set("password", BPassword.make(password))` on a **transient** `BBackupConfig`/`BRestoreConfig` (deserialized JSON, not a mounted station component); `job.submit(cx)` on the resulting `BBackupJob` | `set()`: **No** (2-arg overload, §68.3) — but irrelevant, target isn't in an `@AuditableSpace` yet. `submit(cx)`: **Yes** | The one real station-tree-reaching write (`job.submit(cx)`) threads `cx`; the config `.set()` is pre-mount and outside `ComplexSlotMap`'s audit gate entirely `[CERT]` `organized/bacnetAws/vineflower/com/tridium/bacnetAws/servlets/BacnetAwsServlet.java:69,87,91` |
| `UxBuilderServlet` (`/uxBuilder/*`, PX-widget-tree save) → `UxMediaUtil.savePxFile(target, req, cx)` → `decodePropsAndKids(json, complex, cx)` | `HttpServlet` | `complex.set(prop, propValue)` (:372), `complex.set(name, kidWidget)` (:393), `complex.asComponent().add("LayerTag",…)` (:360), `.add(name, propValue)` (:363,395), `.add(null, binding)` (:417) | **No** — all 5 calls use the 2-arg overload, **despite `cx` being an in-scope method parameter used elsewhere in the same method** (`decodeValue(value, prop.getType(), cx)`, `getNiceMessage(e, cx)`) | **Unaudited by omission, not by unavailability** — `cx` is live in scope and simply not passed to the write calls `[CERT]` `organized/uxBuilder/vineflower/com/tridium/uxBuilder/ui/UxMediaUtil.java:342-395` |
| `BStringServlet` (`BWebServlet` subclass; HTTP-client device-driver servlet) `doPost(WebOp op)`→`handleRequest(op,true)` | `BWebServlet` | `op.getUser()` used for a **live permission check** (`user.getPermissionsFor(this)`) in the same method, then `this.update(body)` → `@Generated setLastReceived/setOut/setResponseBody(v) { this.set(prop, v, null); }` | **No** — `op` (proven in §68.2 to carry the real user) is read for authorization one line earlier, then the actual state-changing calls go through `@Generated` setters that hardcode `null` | **Unaudited by omission** — the identical B46-G1 Slot-o-Matic pattern, but this time the real `Context` was demonstrably reachable (used for the permission check moments before) `[CERT]` `organized/httpClient/vineflower/com/tridium/httpClient/servlet/BStringServlet.java:144-148,282-289` |

`[CERT]` (all cited files read in full or by targeted range this session). **Answer to B41-G5 as posed**:
first-party N5 servlets are architecturally capable of threading `niagara.context`/`WebOp` to an audited
write — both mechanisms exist and reach a real authenticated `BUser` (§68.1–§68.2) — but of the
representative write-capable servlets censused, **only the generic `NiagaraRpcServlet`→`NiagaraRpcUtil`
path and `BacnetAwsServlet`'s job-submission write demonstrably thread it**; the PX-widget-save
(`UxBuilderServlet`) and device-driver-response (`BStringServlet`) write paths **do not**, for the same
structural reason [Block 46] found in third-party `DashboardPan`: the shorter, `Context`-dropping
overload is the one actually called. `[INFER]`: this generalizes [Block 46] §46.5's "framework-wide
Slot-o-Matic question, not a DashboardPan-specific fix" characterization — the omission recurs in N5's own
shipped `uxBuilder` and `httpClient` modules, not only in a third-party-ported module, so it is a platform
convention risk, not an isolated third-party mistake.

## 68.5 — `FileServlet.doPut`: a write path structurally outside `ComponentSlotMap`'s audit mechanism entirely `[CERT]`

`FileServlet.doPut()` overwrites a `BIFile`'s contents (`this.overwriteFileContents(req, resp, file)`,
wrapped in `SecurityUtil.doPrivileged(...)`) `[CERT]` `organized/web/vineflower/com/tridium/web/servlets/
FileServlet.java:145-159` (476-line file). This never calls `BComplex.set`/`BComponent.add`/`invoke` at
all — a station file (`niagara.file.BIFile`) is not a `BComponent` slot, so [Block 41]'s entire
`AuditEvent`/`@AuditableSpace` mechanism (§41.1–§41.4, REMIT) structurally does not apply to it; whatever
audit trail a file overwrite gets (if any) would come from a different subsystem this block did not open.
`[INFER]`: named as a genuine scope boundary, not a finding that file writes are "unaudited" in the same
sense as the B41-G5 servlet writes above — those two claims answer different questions and should not be
conflated.

## 68.6 — B46-G3: a `null` `Context` resolves to `user = null`, not to the resolving component's ambient identity — narrowed, not closed `[CERT]`+`[INFER]`

`BOrd.get(BObject base, Context cx)` → `resolve(base, cx).get()` → `resolve(base, cx, null)`, which
constructs `OrdTarget target = new OrdTarget(cx, this, queries, base)` `[CERT]`
`organized/baja/vineflower/niagara/naming/BOrd.java:94-98,110-127` (536-line file). That 4-arg
`OrdTarget` constructor builds `BasicContext temp = new BasicContext(cx); this.user = temp.getUser();`
(§68.2, already cited `OrdTarget.java:92-100`). `BasicContext(Context base)`'s body is:
```java
public BasicContext(Context base) {
   if (base != null) {
      this.base = base; this.user = base.getUser(); this.facets = base.getFacets(); this.lang = base.getLanguageCode();
   }
   this.invariant();
}
```
`[CERT]` `organized/baja/vineflower/niagara/sys/BasicContext.java:41-50` (111-line file). When `base ==
null` (i.e. the caller passed `null` as `cx`, exactly [Block 46] §46.1's 3 read-side
`BOrd.make(...).get(this, null)` calls), the `if` body never runs — `this.user` stays at its Java default,
`null`. **Answer to B46-G3's first half**: a `null`-`Context` ORD resolution does **not** silently inherit
"the servlet component's own ambient identity" (the hypothesis B46-G3 was framed against) — it resolves
with a genuinely `null` user, structurally indistinguishable at the `OrdTarget` level from an
unauthenticated resolution. `[CERT]` (full constructor-chain read, this session).

**What remains open** (B46-G3's second half): whether any individual `BOrdScheme.resolve()` step (the
per-scheme resolution logic for `station:`, `file:`, etc. that `BOrd.resolve()` invokes in its query loop,
`organized/baja/vineflower/niagara/naming/BOrd.java:122-131`) itself branches on `target.getUser() ==
null` to deny or restrict resolution, or resolves structurally regardless and relies entirely on the
caller having already gated read access before calling `.get(base, null)` (as `BWebServlet.doService()`'s
explicit `getPermissions(cx).hasOperatorRead()` check does **before** any ORD resolution, §68.2 step 1).
No `BOrdScheme` implementation was opened this session — `[INFER]`, not traced; kept open as **B68-G3**
below rather than asserted either way.

## 68.7 — B41-G2 CLOSED: the JAAS `Subject` `AddSubjectFilter` propagates carries exactly two principal types, no roles `[CERT]`

`AddSubjectFilter.doFilter()` (whole 50-line file) recovers the session, then:
```java
NiagaraSession niagaraSession = WebSessionUtil.getSessionOrCreateIfAuthenticated(req);
if (niagaraSession != null) {
   SecurityUtil.doPrivileged(() -> {
      Subject subject = SessionManager.getAuthenticatedSubjectFromSession(niagaraSession.getSuperId());
      SecurityUtil.callAs(subject, () -> { chain.doFilter(req, response); return null; });
      return null;
   });
} else { chain.doFilter(req, response); }
```
`[CERT]` `organized/web/vineflower/com/tridium/web/filters/AddSubjectFilter.java:29-44`. If no session is
authenticated, the rest of the chain runs with **no** ambient `Subject` bound at all (the `else` branch) —
not a synthetic anonymous `Subject`. `SessionManager.getAuthenticatedSubjectFromSession(sessionId)`
(`session.isAuthenticated() ? session.getAuthenticatedSubject() : null`) `[CERT]`
`organized/baja/vineflower/com/tridium/session/SessionManager.java:251-254` (494-line file) reads whatever
`Subject` was stored via `NiagaraSession.setAuthenticated(Subject) { SessionManager.setAuthenticated(this.getSuperId(), subject); }` `[CERT]` `organized/baja/vineflower/com/tridium/session/NiagaraSession.java:25-27` — and that store call's **only** call site outside a session-cache-restore path is inside
`BAuthenticationService.authenticate()`:
```java
LoginContext lc = scheme.login(handler);
Subject subject = lc.getSubject();
if (subject != null) {
   Set<BUser> set = subject.getPrincipals(BUser.class);
   for (BUser principal : set) { if (principal != null) { user = principal; break; } }
   if (user != null) {
      NiagaraSuperSession superSession = SessionManager.getNiagaraSuperSession(session);
      if (superSession != null) {
         Set<SuperSessionPrincipal> sspSet = subject.getPrincipals(SuperSessionPrincipal.class);
         if (!sspSet.isEmpty()) { for (SuperSessionPrincipal p : sspSet) subject.getPrincipals().remove(p); }
         subject.getPrincipals().add(new SuperSessionPrincipal(superSession));
      }
   }
   subject.setReadOnly();
}
SecurityUtil.doPrivileged(() -> { finalSession.setAuthenticated(subject); return null; });
```
`[CERT]` `organized/baja/vineflower/com/tridium/authn/BAuthenticationService.java:200-246` (whole method
body read, 429-line file, range ends within bounds). **Answer to B41-G2**: the JAAS `LoginContext` (driven
by a pluggable `BAuthenticationScheme`'s own `LoginModule` chain — not traced further, see **B68-G4**
below) is the actual `Principal` source; `BAuthenticationService` then adds exactly **one more** principal
type — `SuperSessionPrincipal` (binding the `Subject` to this one super-session, with a defensive
stale-duplicate removal first) — and calls `subject.setReadOnly()` once both principals are settled,
making the `Subject` immutable for the rest of its life. **No separate role/group principal type is added
anywhere in this method** — `BUser` (the user object itself, acting as its own `java.security.Principal`,
confirmed independently in §68.8's `NiagaraUserIdentity`) and `SuperSessionPrincipal` are the **only two**
principal classes this block found added to an authenticated `Subject`. This matches, and explains, [Block
41] §41.7's observation that `AddSubjectFilter` is "a second, JAAS-level user-context mechanism parallel to
the `niagara.context` request attribute" — it now has a concrete, closed answer for *what* that mechanism
actually carries. Whether any in-station code branches differently on `Subject.getPrincipals(SuperSessionPrincipal.class)` vs. the plain `niagara.context` `BUser` (B41-G2's second half) was not
traced this session beyond the negative finding above (no role principal exists to branch on) — narrowed,
not exhaustively closed; see **B68-G5**.

## 68.8 — B41-G3 CLOSED: `NiagaraLoginService`/`NiagaraUserIdentity` — Jetty roles are structurally disabled, permission is entirely Niagara-side `[CERT]`

`com.tridium.jetty.NiagaraLoginService` (package-private, `final`, `implements
org.eclipse.jetty.security.LoginService`) is the configured `LoginService` `NiagaraAuthenticator.login(...)`
resolves through ([Block 41] §41.6, REMIT). Its `login(String username, ...)` method:
```java
BUserService userService = BUserService.getService();
BUser user = userService.getUser(username);
BAuthenticationService authenticationService = BAuthenticationService.getService();
user = authenticationService.authenticate(new LoginNiagaraSessionSupplier(...), user, handler, scheme);
return new NiagaraUserIdentity(user);
```
`[CERT]` `organized/jetty/vineflower/com/tridium/jetty/NiagaraLoginService.java:42-71` (whole 118-line
file read) — this is the **same** `BAuthenticationService.authenticate()` §68.7 already traced end to end
(one authentication call site drives both the JAAS `Subject` construction and the Jetty `UserIdentity`
construction). `NiagaraUserIdentity` (whole 34-line file):
```java
final class NiagaraUserIdentity implements UserIdentity {
   private BUser user;
   NiagaraUserIdentity(BUser user) { this.user = user; }
   public Subject getSubject() {
      if (this.subject == null) { Subject s = new Subject(); s.getPrincipals().add(this.getUserPrincipal()); this.subject = s; }
      return this.subject;
   }
   public Principal getUserPrincipal() { return this.user; }
   public boolean isUserInRole(String role) { return true; }
}
```
`[CERT]` `organized/jetty/vineflower/com/tridium/jetty/NiagaraUserIdentity.java:8-34`. **Answer to
B41-G3**: `getUserPrincipal()` returns the `BUser` object itself, used directly as a `java.security.Principal`
(matching §68.7's finding that `BUser` is the sole non-session principal type). `isUserInRole(String role)`
is **hardcoded to always return `true`**, unconditionally, for any role string — Jetty's own role-based
authorization is structurally disabled at this one line; this closes the mechanism behind [Block 41]
§41.5's independent finding ("the URL-constraint model is one blanket rule, not per-path") from the
opposite direction — not only does N5 register one blanket `/*` constraint with no per-role mapping
(§41.5), the `UserIdentity` it resolves couldn't express per-role authorization even if a constraint asked
for one. All real authorization in N5's web layer is therefore Niagara's own `BPermissions`/
`getPermissions(Context)` mechanism (§41.8, REMIT) and `@NiagaraRpc`'s declarative `permissions()` string
([Block 54] §54.4, REMIT) — never the Jetty/Servlet `isUserInRole` API, confirmed dead by this one-line
body rather than merely unobserved.

## 68.9 — B27-G4 CLOSED: `NModuleInfo.isWar()` is a stored boolean flag, set once at module-registry build time from the presence of `WEB-INF/web.xml` in the module jar `[CERT]`

```java
public boolean isWar() { return this.isWar; }         // NModuleInfo.java:83-85
```
`[CERT]` `organized/baja/vineflower/com/tridium/sys/registry/NModuleInfo.java:23,83-85` (143-line file) —
a plain field read, deserialized from the on-disk module-registry database
(`this.isWar = in.readBoolean();`, `:107`; written back at `:123`). The flag's actual VALUE is computed
exactly once, in `com.tridium.sys.registry.Builder` (the class that scans a module jar and builds its
`NModuleInfo` entry when the module registry is (re)built):
```java
m.info.isWar = moduleFile.getJarEntry("WEB-INF/web.xml") != null;
if (!m.info.isWar) {
   m.info.isWar = moduleFile.getJarEntry("web-inf/web.xml") != null;
}
```
`[CERT]` `organized/baja/vineflower/com/tridium/sys/registry/Builder.java:397-399` (1,103-line file, range
within bounds). **Answer to B27-G4**: `isWar()` is a structural presence check on the module jar's own
`WEB-INF/web.xml` entry (case-insensitive on the directory name, exactly two spellings tried), not a
declared `module.xml` attribute, not a runtime capability probe, and not related to `hx.jar`/other
non-web modules' behavior at all. This converts [Block 27] §27.4's `[INFER]` — "`web.jar` is itself one of
the `isWar()`-flagged modules `addModuleWebAppHandlers()` picks up" — to `[CERT]`: `web.jar` ships its own
`WEB-INF/web.xml` (already confirmed [Block 27] §27.1), so `Builder.java:397` necessarily sets its
`NModuleInfo.isWar = true` at module-registry build time; no other module examined in this corpus (§68.10
next) carries a `WEB-INF/web.xml` of its own.

## 68.10 — B27-G5 CLOSED: `hx.jar` registers no `WebAppContext`/servlet of its own — Px rendering rides the same generic `OrdServlet`/`WebOp` dispatch every ORD-rendered view uses `[CERT]`

A whole-tree `find` under `organized/hx/` (all three trees: `vineflower/`, `extracted/`, `resources/`) for
any `WEB-INF*` path or entry returns **zero hits** `[CERT]` (this session's own `find`/`grep -c` run,
zero matches across ~170 files/dirs enumerated). Per §68.9's now-`[CERT]` `Builder.java:397-399` rule,
this means `hx.jar`'s own `NModuleInfo.isWar` is `false` — `hx.jar` is never picked up by
`addModuleWebAppHandlers()`'s `isWar()`-filtered loop ([Block 27] §27.4, REMIT) and therefore never gets
its own `WebAppContext`/`TridiumSecurityFilter`/`ContextFilter` registration pass at all. `hx.jar`'s own
`module.xml` header confirms no `war`/`webapp` attribute is declared `[CERT]`
`organized/hx/vineflower/META-INF/module.xml:1` (full header line read). A `grep` for `jakarta.servlet`
imports inside `organized/hx/vineflower/` finds exactly 3 non-marker-interface hits, none of them
`HttpServlet`: `com/tridium/hx/BHxOrdTargetResolver.java` (imports `HttpServletRequest`/`HttpServletResponse`
as plain method parameter types, not a servlet superclass), `com/tridium/hx/util/HxUtils.java` (`Cookie`/
`HttpSession` only), and `niagara/hx/HxOp.java`, which is declared:
```java
public class HxOp extends WebOp {
```
`[CERT]` `organized/hx/vineflower/niagara/hx/HxOp.java:32` (555-line file). `HxOp extends WebOp` — the
same `niagara.web.WebOp` base class §68.2 already traced — and `web.jar`'s own `OrdServlet` (registered as
`ord` in `WEB-INF/web.xml`, [Block 27] §27.1, REMIT) is the servlet that actually resolves and dispatches
to it: `OrdServlet extends HttpServlet` reads `NWebOp op = (NWebOp)req.getAttribute("niagara.op")` inside
its `doGet`/`doPost` and delegates `[CERT]`
`organized/web/vineflower/com/tridium/web/servlets/OrdServlet.java:32,37,41,68,70` (161-line file) — the
exact same `"niagara.op"` request attribute `BWebServlet.doService()` populates for its own subclasses
(§68.2 step 1, `BWebServlet.java:88-89`). **Answer to B27-G5**: `hx.jar` registers no `WebAppContext`,
no servlet, and no filter of its own — a Px view request is routed through `web.jar`'s generic `OrdServlet`
exactly like every other ORD-addressable resource, and `HxOp`'s status as a `WebOp` subclass means it
inherits the identical `TridiumSecurityFilter`/`ContextFilter`/`AddSubjectFilter` coverage §68.9 confirmed
for the primary `/` context — there is no separate, narrower, or bypassable route for Px rendering.

## 68.x — Connections

- **[Block 41]** — closes **B41-G5** (§68.1–§68.4: the mechanism exists via two paths, but representative
  write-capable first-party servlets show the same drop pattern [Block 46] found in third-party code),
  **B41-G2** (§68.7: `Subject` carries exactly `BUser` + `SuperSessionPrincipal`, no role principal),
  **B41-G3** (§68.8: `NiagaraLoginService`/`NiagaraUserIdentity`, Jetty roles hardcoded dead). §41.5's
  "one blanket rule, not per-path" finding is corroborated and explained from the opposite direction by
  §68.8's `isUserInRole() { return true; }`. §41.7's `AddSubjectFilter` mention is extended, not
  corrected, by §68.7's full trace.
- **[Block 46]** — its **B46-G3** (read-side `get(this, null)` ORD resolution) is narrowed by §68.6: a
  `null` `Context` resolves to `user = null`, not ambient identity — but per-`BOrdScheme` enforcement
  remains open (**B68-G3**). Its **B46-G1** (Slot-o-Matic-generated setters drop `Context` by design) is
  generalized by §68.3/§68.4: the drop point is `BComplex`/`BComponent`'s own 2-arg convenience overloads,
  not a Slot-o-Matic-specific quirk, and the same pattern recurs in first-party `uxBuilder`/`httpClient`
  module code (§68.4), not only in the ported third-party `DashboardPan`.
- **[Block 27]** — closes **B27-G4** (§68.9: `isWar` is a stored flag set once by `Builder.java` from
  `WEB-INF/web.xml` presence) and **B27-G5** (§68.10: `hx.jar` has no `WEB-INF/` of its own and rides
  `web.jar`'s generic `OrdServlet` dispatch via `HxOp extends WebOp`). §27.4's `[INFER]` reading of
  `web.jar` being `isWar()`-flagged is upgraded to `[CERT]` by the same `Builder.java:397-399` rule.
- **[Block 54]** — §54.4's `NiagaraRpcServlet`/`NiagaraRpcUtil.rpc()` full dispatch trace is REMIT'd
  directly into §68.4's census table as the one clearly-threaded generic write path; not re-derived here.
- **N4 corpus (remit)** — none of this block's findings were cross-checked against the N4 corpus this
  session (out of scope; [Block 41]/[Block 46] already established the N4↔N5 audit-gate comparison this
  block builds on without re-opening it).

## 68.x — Child gaps

- **B68-G1** — Whether any first-party servlet OUTSIDE the representative sample read this session (the
  full §68.1 census has 23 plain-`HttpServlet` files + 10 `BWebServlet` subclasses; this block opened and
  classified 7 write-capable ones) has the same dropped-`Context` pattern — `QueryServlet` (history),
  `SecurityDashboardServlet`, `WbWebWidgetServlet`, `AnalyticsChartFileServlet`, `AnalyticQueryServlet`,
  `SeriesTransformWebChartQueryServlet`, and the remaining 8 `BWebServlet` subclasses
  (`BVelocityServlet`/`BNaServlet`/`BBoxServlet`/`BSnmpMibServer`/`BObixServer`/`BStationOutputServlet`/
  `BSoapServlet`/`BClientEnvServlet`) were census'd (§68.1) but not individually opened for a write-signal
  read. `investigable` — files already decompiled in-corpus.
- **B68-G2** — `NiagaraRpcUtil.rpc()`'s reflective `method.invoke(...)` on the target `@NiagaraRpc` method
  ([Block 54] §54.4, REMIT) was not, in this block or [Block 54], followed INTO any specific first-party
  `@NiagaraRpc`-annotated method body to confirm the injected `SecurableContext` argument is actually
  threaded onward into that method's own `set()`/`invoke()` calls (as opposed to being merely accepted as
  a parameter and dropped, the exact pattern §68.4 found twice at the servlet layer). `investigable` —
  would need a census of `@NiagaraRpc`-annotated methods across `organized/`.
- **B68-G3** — Whether a `BOrdScheme.resolve()` implementation (e.g. the `station:` scheme) itself checks
  `target.getUser() == null` to deny/restrict resolution, or resolves structurally regardless and relies
  on the CALLER having already gated read access (§68.6's open half of B46-G3). `investigable` — no
  `BOrdScheme` subclass was opened this session.
- **B68-G4** — Which concrete JAAS `LoginModule`(s) a `BAuthenticationScheme.login(handler)` call actually
  installs into the `LoginContext` §68.7 traced up to (`lc.getSubject()`) — this block treated
  `scheme.login(handler)` as an opaque boundary and did not open any `BAuthenticationScheme` subclass or
  `LoginModule` implementation. `investigable`.
- **B68-G5** — Whether any in-station code branches differently on `Subject.getPrincipals(SuperSessionPrincipal.class)` (available under the `AddSubjectFilter`-bound ambient `Subject`) versus the plain
  `niagara.context` `BUser` (available via the `ContextFilter` request attribute) — §68.7 found no ROLE
  principal to branch on, but did not grep the whole tree for `getPrincipals(SuperSessionPrincipal.class)`
  call sites to check for behavioral divergence on the two parallel identity channels themselves.
  `investigable`.
- **B68-G6** — Live confirmation (`[CERT-hw]`): stand up an N5 5.0.0.28 station, perform a PX-widget save
  via `UxBuilderServlet` (§68.4) as a web-authenticated user, and read back `$/AuditHistory` to confirm
  the predicted absence of an `AuditEvent` for that write (unlike [Block 46]'s confirmed-then-fixed
  DashboardPan case, this block found but did not fix or live-test the `uxBuilder`/`httpClient` omissions).
  `blocked-on-source` — no runnable N5 station this session, same blocker as [Block 41]'s **B41-G4** and
  [Block 46]'s **B46-G4**.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block68.md /home/cristian/niagara5-research` from `/home/cristian/niagara5-research` this
session, literal output:

```
== verify-block: niagara5-block68.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 4  (adj 2)
   [CERT-live] 0
   [CERT] 51  (adj 49)
   [CERT-doc] 2  (adj 1)
   [CERT-web] 3  (adj 2)
   [CERT-a] 2  (adj 1)
   [INFER] 13  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/55 = 0.20
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BAuthenticationService.java:218-224 / :232, BStringServlet.java:283, BWebServlet.java:88-89,
           BasicContext.java:41-50, Builder.java:397 / :397-399, HxOp.java:32,
           NiagaraUserIdentity.java:31-33, OrdTarget.java:35 / :92-100 / :93, WebOp.java:21
           (13 bare short-form citations — each is a bare `Module.java:NN` prose reference redundant with
           a full-path citation to the SAME file elsewhere in this block, per METHODOLOGY §11's
           bare-body/full-anchor convention; none is an unpathed citation lacking a resolved counterpart)
   ok      26 full-path citations across
           AnalyticsChartFileServlet.java, BAuthenticationService.java:200-246, NiagaraSession.java:25-27,
           SessionManager.java:251-254, Builder.java:397-399, BOrd.java:122-131, OrdTarget.java:33-37/
           85-87/92-100, BComponent.java:428-446, BasicContext.java:41-50, WbWebWidgetServlet.java:73,
           HierarchyServlet.java:49/94-96, hx/module.xml:1, HxOp.java:32, NiagaraLoginService.java:42-71,
           NiagaraUserIdentity.java:8-34, SecurityDashboardServlet.java:38, UxMediaUtil.java:342-395,
           AddSubjectFilter.java:29-44, NWebOp.java:10-12, BWebServlet.java:70-91, WebOp.java:21/32-36,
           NiagaraRpcServlet.java:32  (all range-end-verified against real on-disk file lengths)
   resolved 26 of 39
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**Reading the tally.** Adjusted counts (header/legend marker-name mentions stripped): `[CERT]` 49,
`[CERT-hw]` 2, `[CERT-doc]` 1, `[CERT-web]` 2, `[CERT-a]` 1, `[INFER]` 11 — ratio `[INFER]`/`[CERT*]` =
11/55 ≈ **0.20**, matching the script's own reported figure exactly. The 2 raw `[CERT-hw]`/1 `[CERT-doc]`/
2 `[CERT-web]`/1 `[CERT-a]` adjusted counts are **not** independent claims this block makes — this is a
pure decompiled-source read with zero hardware/doc/web/forum evidence — they are the tool counting this
Self-verify section's and the header's own prose naming those marker tokens (the same RAW-vs-ADJUSTED
distortion [Block 41] §41.9 documented for its own self-verify section). A 0.20 ratio is low, consistent
with an evidence block whose `[INFER]` occurrences are each narrowly scoped (§68.4's cross-block
generalization sentence, §68.6's open-half framing, §68.7's "narrowed not closed" framing, §68.10's
inherited-coverage conclusion) rather than free-standing speculation.

**Token check.** Every load-bearing `[CERT]` citation above was `grep -n`/`Read` directly this session (not
hand-recalled from a prior block): `"niagara.context"` (23-file whole-tree census), `extends
BWebServlet\b` (10-file whole-tree census), `class HxOp extends WebOp` (1 hit), `implements
SecurableContext` on `WebOp`, `this.user = base.user` (`OrdTarget.java:35`), `BasicContext temp = new
BasicContext(cx)` (`OrdTarget.java:93`), the `BasicContext(Context base)` body, `m.info.isWar =
moduleFile.getJarEntry("WEB-INF/web.xml")` (1 hit), `isUserInRole` (1 hit, hardcoded `return true`),
`subject.setReadOnly()` (1 hit), `SuperSessionPrincipal` (constructor + 2 `getPrincipals` calls),
`complex.set(prop, propValue)`/`complex.set(name, kidWidget)` (2 hits), `complex.asComponent().add(`
(4 hits), `c.set("password"` (2 hits), `job.submit(cx)` (1 hit), `user.getPermissionsFor(this)` (1 hit),
`WEB-INF` (whole-tree `hx/` search, 0 hits, both `find -iname` and `grep -rc`) — **51 tokens checked, 0
absent, 0 downgraded**.

**Citation resolution.** `resolved 26 of 39` — the majority resolve `ok` because this block followed
[Block 61]'s full-path citation convention (`organized/<module>/vineflower/...`) rather than [Block 41]'s
bare short-form; the 13 `extern` citations are each a bare `Module.java:NN` prose reference redundant with
a full-path citation to the same file elsewhere in this block (the named pattern METHODOLOGY §11
describes), not an unresolved gap — every one of those 13 files also appears above with a full,
range-verified path.

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block68.md`. Per this
task's explicit read-only/single-file constraint, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not**
regenerated or hand-edited — flagged here for the orchestrator to pick up, same disclosure [Block 27]/
[Block 41]/[Block 46] made.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.
