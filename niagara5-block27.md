# Block 27 — N5 web server security headers, CSP and resource serving

> Research of **the N5 5.0.0.28 web server's HTTP-security-header plane**: how `niagara.web` (`web.jar`)
> and `niagara.jetty` (`jetty.jar`) set `Content-Security-Policy`, `X-Frame-Options`,
> `X-Content-Type-Options`, `X-XSS-Protection`, `Cross-Origin-Opener-Policy`, cookie flags
> (`Secure`/`HttpOnly`/`SameSite` for `JSESSIONID` and app cookies), and CSRF protection
> (`x-niagara-csrfToken`), and where in the Jetty-12/`jakarta.servlet` filter chain this is wired in.
> Does **not** cover authentication/authorization proper (`NiagaraAuthenticator`,
> `NiagaraConstraintSecurityHandler` — named as child gap B27-G3), TLS/certificate configuration
> (`BAdditionalHttpsCert*`, out of scope), or a live-station HTTP capture (no runnable N5 station this
> session, same constraint as Blocks 2/4/10/21).
>
> Subject version: Niagara 5.0.0.28 (beta), `web.jar` sha256
> `68babcf16012314d59c095d3995c0a0f4db18853361cd5719e76be2a4d14b22e`, `jetty.jar` sha256
> `67cfc1e50ff4aa2e6ce38eab3fc8332cc327898742dd1aa3f7f6aa1727793253` (both from
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`, this session).
>
> Sources: `web.jar` (`com.tridium.web.*`, `niagara.web.*`, `WEB-INF/web.xml`, `WEB-INF/jetty-web.xml`,
> `META-INF/module.xml`, `module-info.class`) and `jetty.jar` (`com.tridium.jetty.*`,
> `module-info.class`), both from
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`; Jetty 12.1.13 third-party jars census
> from `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/` (existence only, not decompiled — vendor code);
> N4 remittance corpus `niagara-research` (B9, B11, B27, B29, B47, B602, B763, B796, B803, B813, B823,
> B1015, B1063, B1065) via `tools/corpus-nav.py find`; `DashboardPan-ux/src/rc/index.html` read from the
> `a109249` worktree (`/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`).
>
> Method: decompiled `web.jar` and `jetty.jar` in full with Vineflower 1.12.0
> (`/home/cristian/niagara5-research/tools/decompilers/vineflower-1.12.0.jar`, run on
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`) into `/tmp/claude-1000/n5b27/dec/` and
> `/tmp/claude-1000/n5b27/decjetty/`, this session — scratch decompiles, not preserved in the corpus (no
> `organized/` directory in `niagara5-research`, per B21's convention); anchor is each source jar's own
> sha256 above. `WEB-INF/web.xml`/`jetty-web.xml`/`module.xml` extracted verbatim with `unzip -p`. Header-
> name string census across both jars done with a Python `zipfile` byte-grep (`Content-Security-Policy`
> already known from class names; `Strict-Transport-Security`, `Referrer-Policy`,
> `Access-Control-Allow-Origin`, `X-Requested-With`, `SameSite` searched fresh this session).
> Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) ·
> `[CERT-doc]` official downloaded document · `[CERT-web]` official web ·
> `[CERT-a]` secondary source/forum · `[INFER]` deduction. `file:line` citations point into the
> `dec/`/`decjetty/` scratch trees (path given once per section); every one was read directly this
> session, not recalled.
>
> Web/servlet layer. Connects [Block 10] (§10.9 `@ModuleResources`/JPMS resource-root mechanics — REMIT,
> extended here with a concrete example), [Block 21] (§21.8's negative CSP-string search across 5 UI jars
> — this block closes the named child gap **B21-G3** static-jar-census half).

---

## 27.1 — `WEB-INF/web.xml` and `jetty-web.xml`: the servlet/filter map, and no declarative security-header filter `[CERT]`

`web.jar`'s `WEB-INF/web.xml` (9,120 bytes, read in full via `unzip -p`) registers 8 servlets
(`logoutConfirm`, `file`, `module`, `vFileTypeResolverServlet`, `viewAllOrd`, `niagaraSpeedTest`, `ord`,
`rpc`, `sessionTimeout`, `csp-reports`, `requireJsConfig` — 11 total) and a handful of declarative
filters, all of them **functional** (ORD resolution, caching, view dispatch, locale) or **CSRF**
(`niagara.web.filters.CsrfProtectedFilter`, §27.5) — **no security-header filter is declared in
`web.xml`**. `[CERT]` (`WEB-INF/web.xml`, full text, this session). `jetty-web.xml` (339 bytes) contains
exactly one directive: it overrides the `WebAppContext`'s context path from the module name (`web`) to
`/` — "Change the Context Path from the module name to something else". `[CERT]` (`WEB-INF/jetty-web.xml`,
full text). `module.xml`'s header declares `module name="web" ... moduleName="web"` with no explicit
`war`/`webapp` attribute in the inspected header line `[CERT]` (`META-INF/module.xml:2`) — whether
`web.jar` is picked up as a "war"-type module by `NModuleInfo.isWar()` (§27.4) was inferred from this
structural pattern, not from reading `isWar()`'s own definition (`baja.jar`, not opened this session) —
see **B27-G4**.

## 27.2 — `niagara.web.http`: a component tree of security-header providers, not a filter config file `[CERT]`

Five concrete provider classes implement `niagara.web.http.BIHttpHeaderProvider`
(`applyHeaders(HttpServletRequest,HttpServletResponse)` **and** an overload for Jetty's own
`org.eclipse.jetty.server.Request`/`Response` — both are called from different dispatch points, §27.6):

| Provider class | Header | Default value | Config surface |
|---|---|---|---|
| `BCspHeaderProvider` | `Content-Security-Policy` | built from 12 directive properties, §27.3 | per-directive `BString` properties |
| `BGenericHttpHeaderProvider` (fixed instance) | `Cross-Origin-Opener-Policy` | `same-origin` | `forFixedHeaderName("Cross-Origin-Opener-Policy","same-origin")` |
| `BXContentTypeOptionsHeaderProvider` | `X-Content-Type-Options` | `nosniff` | `xContentTypeOptions` BString property, **or** system property `niagara.web.security.contentTypeOptionsHeader` |
| `BXFrameOptionsHeaderProvider` | `X-Frame-Options` | `DENY` (see discrepancy below) | `xFrameOptions` : `BXFrameOptionsEnum` |
| `BXXssProtectionHeaderProvider` | `X-XSS-Protection` | `1; mode=block` | `xXssProtection` BString property, **or** system property `niagara.web.security.xssProtectionHeader` |

`[CERT]` (`dec/niagara/web/http/BGenericHttpHeaderProvider.java:1-127`,
`BHttpHeaderProviders.java:18-32`, `BXContentTypeOptionsHeaderProvider.java:1-91`,
`BXFrameOptionsHeaderProvider.java:1-83`, `BXXssProtectionHeaderProvider.java:1-84`, this session).
All five are children of one `niagara.web.http.BHttpHeaderProviders` **Niagara component**
(`BComponent`, not a servlet-container config object) that is itself a single property
(`httpHeaderProviders`, default `new BHttpHeaderProviders()`) on the **singleton** `niagara.web.BWebService`
station service — i.e. this is a live, editable Niagara slot tree (visible/editable in Workbench under
`Services > WebService > HttpHeaderProviders`), not a `web.xml`/properties-file setting. `[CERT]`
(`dec/niagara/web/BWebService.java:158,232,480-486`, this session). `BHttpHeaderProviders.applyHeaders()`
just iterates its `BIHttpHeaderProvider` children and delegates — it holds no header logic of its own.
`[CERT]` (`dec/niagara/web/http/BHttpHeaderProviders.java:119-138`).

**No per-servlet override API exists at the framework level.** There is exactly one
`BHttpHeaderProviders` instance station-wide (the `BWebService` singleton's), applied uniformly to every
response that passes through `TridiumSecurityFilter` (§27.6) — a `BWebServlet` subclass cannot register
its own header policy through this mechanism; it can only mutate the response object directly in its own
`doGet`/`doPost`, downstream of the filter. The one legacy exception: `BWebService` itself still exposes a
**standalone** `xFrameOptions` property (pre-existing from before the provider-tree redesign) that is
synced into `httpHeaderProviders.xFrameOptions` on `changed()` and once at `fwStarted()` via a
one-time-migration `Flags` check (bit `268435456`/`268435461`) — a backward-compatibility bridge, not a
second override point. `[CERT]` (`dec/niagara/web/BWebService.java:584,602-603` [`changed()`],
`:688,694-695` [`fwStarted()`], this session).

## 27.3 — `BCspHeaderProvider`: default policy, `%hostname%`/`%scheme%`/`%port%` templating, no nonce support `[CERT]`

The default `Content-Security-Policy` directive set (`newProperty` defaults, `dec/niagara/web/http/BCspHeaderProvider.java:98-121`, this session):

| Directive | Default value |
|---|---|
| `default-src` | `'self' workbench module:` |
| `script-src` | `'self' workbench module: 'unsafe-inline' 'unsafe-eval'` |
| `style-src` | `'self' workbench module: 'unsafe-inline'` |
| `img-src` | `'self' workbench data: module:` |
| `connect-src` | `'self' workbench ws://%hostname%:%port% wss://%hostname%:%port%` |
| `report-uri` | `/csp-reports` |
| `child-src` / `frame-src` / `font-src` / `manifest-src` / `media-src` / `object-src` | empty (directive omitted from the header) |

`generateHeader(Context cx)` walks `getDirectiveProperties()` (the 12 directive slots), skips empty ones,
maps each slot name to its CSP directive keyword via a `switch` (`childSrc→child-src`,
`connectSrc→connect-src`, … `reportUri→report-uri`, `scriptSrc→script-src`, `styleSrc→style-src`), runs
each non-empty value through `FormatUtil.formatFromContextFacets` templating (substituting the 3 context
facets `scheme`/`hostname`/`port`, populated per-request from the live `HttpServletRequest` in
`createContext()`) and strips embedded newlines, then joins with `"; "`; a free-text `additionalDirectives`
property (multi-line facet) is appended verbatim (still newline-stripped) as an escape hatch for directives
the fixed property set doesn't model. `[CERT]` (`dec/niagara/web/http/BCspHeaderProvider.java:302-380`
[`generateHeader`/`template`/`getDirective`], `:382-397` [`createContext`], this session). **No nonce
support of any kind was found**: `generateHeader()`/`template()` were read in full and contain no random-
value generation, no `nonce-` literal, and no per-response mutable state — the entire method reads
directly from the (station-wide, editable, but static-per-config) property values every call. `[CERT]`
(absence — full-method read, same session). The class does carry a live-status feedback loop
unrelated to nonce/override machinery: a `/csp-reports` `report-uri` target (`CspReportServlet`, §27.7)
feeds browser violation reports back into a `violationText` property, which flips the component's own
`BStatus` to `fault` — i.e. a real CSP violation shows up as a Niagara station fault, clearable via the
`clearFaultStatus` action. `[CERT]` (`dec/niagara/web/http/BCspHeaderProvider.java:392-401`
[`changed`/`doClearFaultStatus`]).

## 27.4 — Dispatch: `TridiumSecurityFilter` registered programmatically on `/*`, not via `web.xml` `[CERT]`+`[INFER]`

`TridiumSecurityFilter` (in `web.jar`) is **not** in any `web.xml`/`jetty-web.xml` — it is registered
imperatively, once per `ServletContextHandler`, inside `com.tridium.jetty.BJettyWebServer` (in `jetty.jar`):

```java
context.addFilter(AddSubjectFilter.class, "/*", null);
context.addFilter(TridiumSecurityFilter.class, "/*", null);   // ← security headers
context.addFilter(LocaleFilter.class, "/*", null);
context.addFilter(ContextFilter.class, "/*", null);
```

`[CERT]` (`decjetty/com/tridium/jetty/BJettyWebServer.java:1287-1290`, `configureNiagaraWebApp()`, this
session). `configureNiagaraWebApp()` is invoked from exactly two places: `addModuleWebAppHandlers()`
(`:1228-1254`), which iterates every `NModuleInfo` flagged `isWar()` and builds one
`org.eclipse.jetty.ee11.webapp.WebAppContext` per such module, and the websocket-servlet registration path
(`:1565`). `[CERT]` (`decjetty/com/tridium/jetty/BJettyWebServer.java:1228-1254,1565`, this session).
Because `web.jar` itself ships `WEB-INF/web.xml` + `WEB-INF/jetty-web.xml` (§27.1) — the exact shape
`addModuleWebAppHandlers()` looks for — the simplest reading is that **`web.jar` is itself one of the
`isWar()`-flagged modules this loop picks up**, with its own `jetty-web.xml` overriding the default
`/web` context path to `/` (matching that file's own comment, §27.1); this makes the **primary station
web application** (contextPath `/`, hosting `ord`, `rpc`, `file`, `module`, `login`, etc.) just one more
instance of the same `configureNiagaraWebApp()` path, so `TridiumSecurityFilter` covers it identically to
every other module WAR context. This reading is `[INFER]` — `NModuleInfo.isWar()`'s own predicate
(presumably in `baja.jar`) was not opened this session; see **B27-G4**.

`TridiumSecurityFilter.doFilter()` itself is a 6-line pass-through: it looks up the `BWebService`
singleton, wraps the response in a `TridiumSecurityServletResponse` (§27.5), calls
`webService.getHttpHeaderProviders().applyHeaders(req, resp)`, then continues the chain. `[CERT]`
(`dec/com/tridium/web/filters/TridiumSecurityFilter.java:1-28`, this session). Two other call sites reach
`BHttpHeaderProviders.applyHeaders()` directly, both scoped to unauthenticated static content:
`com.tridium.web.servlets.DefaultServlet` (the `/favicon.ico`/`/robots.txt` handler) applies headers before
serving a cached favicon, and `com.tridium.web.http.BHttpHeaderSecurityDashboardItemProvider` applies
headers 3 times while building the Workbench "security dashboard" preview of the effective header set.
`[CERT]` (`dec/com/tridium/web/servlets/DefaultServlet.java:1-38`,
`dec/com/tridium/web/http/BHttpHeaderSecurityDashboardItemProvider.java:142,168,195`, this session).

## 27.5 — Cookies: `JSESSIONID` forced `Secure`+`HttpOnly`, `SameSite` a per-station `BWebService` property `[CERT]`

The Jetty `SessionHandler` that backs `JSESSIONID` is built with both hardening flags **unconditionally
on**, independent of any Niagara config:

```java
private static SessionHandler newSessionHandler(ContextSessionData contextSessionData) {
   NiagaraSessionHandler sessionHandler = new NiagaraSessionHandler();
   sessionHandler.setSecureRequestOnly(true);
   sessionHandler.setHttpOnly(true);
   ...
```

`[CERT]` (`decjetty/com/tridium/jetty/BJettyWebServer.java:1601-1610`, this session — Jetty's
`setSecureRequestOnly(true)` means the `Secure` attribute is added only when the *request itself* arrived
over HTTPS, not unconditionally; the N4 corpus documents the matching HTTP-behind-reverse-proxy failure
mode at B29 §29.5.4/§29.12.3, B47:657, B27:622 — `req.isSecure()`-based `Secure` flagging silently drops
the session cookie behind an HTTP-terminating proxy). `SameSite` is a first-class, per-station
`BWebService.sameSite` config property (`BSameSiteEnum` : `none`/`lax`/`strict`, default `lax`), applied
to **both** the session cookie and the servlet-context's default `SameSite` attribute for every other
cookie the app sets:

```java
private void configureSameSite(ServletContextHandler servletContextHandler) {
   SameSite sameSite = switch (this.getWebService().getSameSite().getOrdinal()) {
      case 0 -> SameSite.NONE;
      case 2 -> SameSite.STRICT;
      default -> SameSite.LAX;
   };
   servletContextHandler.setAttribute("org.eclipse.jetty.cookie.sameSiteDefault", sameSite);
   servletContextHandler.getSessionHandler().setSameSite(sameSite);
}
```

`[CERT]` (`decjetty/com/tridium/jetty/BJettyWebServer.java:1577-1585`, `configureSameSite()` called from
both context-build paths in §27.4, this session; `BSameSiteEnum` range/default at
`dec/com/tridium/web/BSameSiteEnum.java:11-14`, `Range={none,lax,strict}`, no explicit `defaultValue`
attribute on the enum itself — `none` is index 0 and thus the frozen-enum implicit default, but
`BWebService`'s own `sameSite` property explicitly pins `BSameSiteEnum.lax` as its default,
`dec/niagara/web/BWebService.java:136-138,210`). This matches the N4 architecture
byte-for-byte — same class name/package (`com.tridium.web.BSameSiteEnum`), same 3-value range, same `lax`
default, same "`SameSite=None` silently drops the cookie without `Secure`+real HTTPS" gotcha already
documented for N4 at B27 §27.8.2, B29 §29.5.3/§29.5.4/§29.12.3/§29.16.4, B47:155,582,657,840, B9:330,416,
B11:260, B602 — REMIT, N5 makes no behavioral change here `[CERT]`+`[CERT-a]` (cross-reference, not
independently re-derived).

**Cookie utility (`com.tridium.web.CookieUtil`)**: `createCookie()` always sets `HttpOnly(true)` and
`Path("/")`; `Secure` is an explicit boolean parameter the caller must opt into (defaults `false` via the
2-arg/3-arg overloads). `[CERT]` (`dec/com/tridium/web/CookieUtil.java:88-109`, this session).
Separately, **every** cookie added through a request wrapped by `TridiumSecurityFilter` gets a second,
independent `Secure` upgrade: `TridiumSecurityServletResponse.addCookie(Cookie c)` force-sets
`c.setSecure(true)` whenever `request.isSecure()` is true, before delegating to the real response — this
runs regardless of what the cookie's own creation code set. `[CERT]`
(`dec/com/tridium/web/filters/TridiumSecurityServletResponse.java:1-24`, this session). Named cookie
constants confirm the same set already catalogued for N4 (`JSESSIONID`, `niagara_essential_session_support`
— the successor read by B602 as `niagara_userid`/`niagara_session`-family names, `niagara_auth_scheme`,
`niagara_sso_scheme`, `super_session_id`, etc.), with a 365-day `COOKIE_AGE` constant matching B602's
documented persistence window. `[CERT]` (`dec/com/tridium/web/CookieUtil.java:15-27`, this session).

## 27.6 — CSRF: synchronizer token `x-niagara-csrfToken`, narrowly filter-mapped — not the `X-Requested-With` pattern our own modules use `[CERT]`

`niagara.web.CsrfUtil` defines the token header name (`CSRF_TOKEN_HTTP_HEADER = "x-niagara-csrfToken"`) and
verifies it against the current `NiagaraSuperSession`'s stored `csrfToken` via `String.equals()`, throwing
`CsrfException` on missing/mismatched tokens. `[CERT]` (`dec/niagara/web/CsrfUtil.java:1-44`, this
session). The token is read from the request by `com.tridium.web.WebUtil.getCsrfTokenFromRequest()`:
header `x-niagara-csrfToken` first, falling back to the `csrfToken` request parameter if the header is
absent — no CSRF cookie is involved (pure synchronizer-token pattern, token bound server-side to the
session, not a double-submit-cookie scheme). `[CERT]` (`dec/com/tridium/web/WebUtil.java:418-428`, this
session). Enforcement is `niagara.web.filters.CsrfProtectedFilter`, a declarative `web.xml` filter
(unlike `TridiumSecurityFilter`, §27.4) mapped **narrowly**, per HTTP method, to exactly 4 URL patterns:

| `url-pattern` | `httpMethod` init-param |
|---|---|
| `/logout` | `GET` |
| `/file/*` | `POST,PUT` |
| `/rpc/*` | `POST` |
| `/niagaraSpeedTest/*` | `GET,POST` |

`[CERT]` (`WEB-INF/web.xml`, filter-mapping blocks, this session — full text in §27.1's source). `/module/*`
(module `rc/` resource serving, §27.8), `/ord/*`, and `/view/*` carry **no** CSRF filter — consistent with
the same narrow-mapping shape the N4 corpus already documented for this exact filter
(`niagara.web.filters.CsrfProtectedFilter`/`CsrfUtil` — same package/class names — "framework filter
covers `/rpc/*` only", B763:87, B796:46, B803:66). This is the **real** CSRF mechanism the N4 corpus
repeatedly contrasts against our own modules' (`DashboardPan`, `chihuahua`) **hand-rolled**
`X-Requested-With: XMLHttpRequest`-presence check inside their own `route()`/dispatch code
(B763 §763.3, B796:46, B803 §803.5 "Niagara ships a real CSRF TOKEN, not only `X-Requested-With`", B813:51,90,
B823:103,125,161, B1015:57,78,129) — N5 changes nothing about that contrast: it ships the identical
`x-niagara-csrfToken` synchronizer-token class under the identical package name, so the N4 finding that our
modules use a weaker home-grown guard **carries forward unchanged into N5**. `[CERT]`+`[CERT-a]`
(cross-reference to the pre-existing N4 corpus finding, not independently re-derived this session — the
N5-side half, `CsrfUtil`/`CsrfProtectedFilter` identity, is freshly `[CERT]` this session).

## 27.7 — `CspReportServlet`: browser CSP violation reports feed back into the component's own status `[CERT]`

`csp-reports` is mapped to `/csp-reports` in `web.xml` (matching `BCspHeaderProvider`'s default
`report-uri`, §27.3) and served by `com.tridium.web.servlets.CspReportServlet`: it accepts a `POST`ed JSON
CSP violation report (capped at `niagara.web.security.csp.maxReportSize`, default 8096 bytes; rejects
non-JSON-`Accept` requests with `406` and oversized/unparsable bodies with `403`), and on success calls
`BWebService.getHttpHeaderProviders().getContentSecurityPolicy().setViolationText(violationText)` — i.e. a
live browser-reported CSP violation is written straight into the same `BCspHeaderProvider` component whose
own `changed()` hook (§27.3) flips it to `BStatus.fault`. `[CERT]`
(`dec/com/tridium/web/servlets/CspReportServlet.java:1-64`, this session). The first violation per session
logs at `SEVERE`; subsequent ones downgrade to `FINE` (an `AtomicBoolean` latch), to avoid log-flooding a
station under a live CSP misconfiguration. `[CERT]` (same file, `doPost()` logging branch).

## 27.8 — Resource serving: `/module/*` → `FileServlet`, `@ModuleResources("**/web/rc")`; DashboardPan-ux implication `[CERT]`+`[INFER]`

`web.jar`'s own `module-info.class` carries `@ModuleResources("**/web/rc")` on `module niagara.web` — a
concrete, real instance of the partial-glob form of the `@ModuleResources` mechanic Block 10 read from
`doc/modules.html` (§10.9, REMIT) rather than from a shipped module: it marks `com/tridium/web/rc/**`
(login templates, `loginN4.css`/`loginN4.js`, `theme.css`, `activityMonitor.js`, etc.) as the module's
declared non-package resource root, alongside the always-implicit top-level `rc`/`WEB-INF`/`META-INF`
directory names. `[CERT]` (`dec/module-info.java:9`, this session — `@ModuleResources("**/web/rc")`).
A generic module's `rc/` resources (any module, not just `web.jar`) are served over HTTP through the
same primary station context (§27.4) via the `module` servlet mapping already read in §27.1:
`FileOrdTargetFilter` (`prefix=module://`) → `com.tridium.web.servlets.FileServlet` on `/module/*`. `[CERT]`
(`WEB-INF/web.xml`, `module`/`moduleFilter` blocks). Because that servlet, like every servlet in this
context, sits **behind** `TridiumSecurityFilter` on `/*` (§27.4), a request for a module's `rc/` file gets
the exact same `BHttpHeaderProviders` response headers as any other station response — there is no
separate, weaker, or stronger header policy for static module resources. `[INFER]` (follows directly from
§27.4's filter-registration evidence — not independently traced with a live request/response capture this
session, same `blocked-on-source` constraint as the rest of this block).

**Implication for `DashboardPan-ux`.** `DashboardPan-ux/src/rc/index.html` (the module's entire browser
frontend, already characterized by Block 10 §10.11 CHK-12 as static HTML + vanilla JS + `fetch()`, no
`bajaux`/`bajaui` widget) contains a genuine inline `<script>` block (`index.html:698`) and two inline
`<style>` blocks (`index.html:8,608`) `[CERT]` (`grep -n "<script\|<style"` over the live source at
`/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249/Dashboard/DashboardPan/DashboardPan-ux/src/rc/index.html`,
this session — 1 `<script>` tag, 2 `<style>` tags, no external-file-only front end). The N5 station's
**default** `Content-Security-Policy` (§27.3) sets `script-src ... 'unsafe-inline' 'unsafe-eval'` and
`style-src ... 'unsafe-inline'` — both directives that explicitly permit inline script/style. Given §27.8's
finding that `rc/` resources are served through the same filter-wrapped context as everything else, **the
default N5 CSP would not block `DashboardPan-ux`'s inline `<script>`/`<style>` blocks as shipped today** —
no CSP-compliant rewrite (external-file extraction, nonce, hash-source) is required by the *framework
default*. `[CERT]`+`[INFER]` (the CSP string is `[CERT]`-read, the "would not block" conclusion is a direct
application of that string to the observed markup, not independently verified against a live browser or
station — no runnable N5 station this session). This directly informs Block 21 §21.8's `[INFER]` ("nothing
… suggests DashboardPan-ux's static-HTML+vanilla-JS+`fetch()` pages would newly need a CSP-compliant
rewrite") and Block 10's remit of Block 9's ODA2 audit conclusion — **B1063's `ODA2-G2` recommendation to
add a hand-authored `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'` header
inside `BDashboardServlet` itself is, on this evidence, largely redundant on N5**: the station already
injects a broader default (including `'unsafe-eval'` and a live `report-uri`/fault-status loop the
servlet-local header ODA2-G2 proposed would not have) ahead of the servlet, via `TridiumSecurityFilter`.
This is a **N5-only** finding — Block 9/B1063's N4 audit predates this component tree and was correct for
N4's absence at the time it was written.

## 27.9 — Headers/mechanisms searched for and confirmed absent (scope-limited) `[CERT]`

A byte-level string census (Python `zipfile`, this session) across **every** `.class` file in both
`web.jar` and `jetty.jar` found:

| String searched | Hits |
|---|---|
| `Strict-Transport-Security` (HSTS) | **0** in either jar |
| `Referrer-Policy` | **0** in either jar |
| `Access-Control-Allow-Origin` / `Access-Control-Allow` (CORS) | **0** in either jar |
| `X-Requested-With` | **0** in either jar |
| `SameSite` | 3 hits: `com/tridium/web/BSameSiteEnum.class`, `niagara/web/BWebService.class`, `com/tridium/jetty/BJettyWebServer.class` (all covered §27.5) |

`[CERT]` (byte-grep census, this session — negative evidence, scope-limited to these 2 jars, matching the
same caveat Block 21 §21.8 applied to its 5-jar UI search: not proof of absence platform-wide, and not a
substitute for a live-station response capture). Read together with §27.6's confirmation that
`x-niagara-csrfToken`/`CsrfUtil` (not `X-Requested-With`) is the real CSRF primitive, this **closes** the
static-jar-census half of **B21-G3**: N5's `niagara.web`/`niagara.jetty` inject `Content-Security-Policy`,
`X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, and `Cross-Origin-Opener-Policy` (§27.2)
but **not** HSTS, `Referrer-Policy`, or any CORS header, and do not use `X-Requested-With` for CSRF. The
**live-half** of B21-G3 (a `[CERT-hw]` response capture from a running N5 station) remains open — see
**B27-G1**.

## 27.10 — Discrepancy: `BXFrameOptionsEnum`'s own default tag vs. the property's pinned default `[CERT]`

`BXFrameOptionsEnum`'s `@NiagaraEnum` declares `defaultValue = "sameorigin"` at the enum-type level, but
`BXFrameOptionsHeaderProvider`'s `xFrameOptions` property explicitly overrides this with
`newProperty(0, BXFrameOptionsEnum.deny, ...)` — so the header the station actually serves out-of-the-box
is `X-Frame-Options: DENY`, not `SAMEORIGIN`, despite the enum's own nominal default. `[CERT]`
(`dec/niagara/web/BXFrameOptionsEnum.java:12` vs. `dec/niagara/web/http/BXFrameOptionsHeaderProvider.java:36`,
this session — both read fresh). `generateHeader()` maps the `any` ordinal to an empty string (header
omitted entirely) and every other ordinal to its uppercased range tag. `[CERT]`
(`dec/niagara/web/http/BXFrameOptionsHeaderProvider.java:81-83`).

## 27.x — Self-verification (METHODOLOGY §11)

**Type:** `standard`. **Marker tally (manual — `verify-block.sh` is not adapted for the `niagara5-research`
corpus, matching every prior niagara5 block; this block self-counts):** `[CERT]` ≈ 42 (including combined
`[CERT]`+`[INFER]`/`[CERT]`+`[CERT-a]` tags counted once each toward `[CERT]`), `[INFER]` ≈ 4 (§27.4's
`isWar()` reading, §27.8's filter-coverage-for-`rc/` reading, §27.8's "would not block" application of
the CSP string, and the negative absence framing in §27.9 restated as INFER only where the deduction, not
the byte-search itself, is doing the work). Ratio `[INFER]`/`[CERT]` ≈ 0.10 — low, consistent with an
evidence-dominant block backed by full-file decompiled reads plus verbatim XML extraction, matching Blocks
10/21's profile.

**Token check.** Every quoted string/identifier load-bearing to a `[CERT]` claim was read directly in a
fresh `grep -n`/`cat` this session (not recalled): `Content-Security-Policy`, `X-Frame-Options`,
`X-Content-Type-Options`, `X-XSS-Protection`, `Cross-Origin-Opener-Policy`, `x-niagara-csrfToken`,
`csrfToken`, `TridiumSecurityFilter`, `sameSiteDefault`, `setSecureRequestOnly`, `setHttpOnly`,
`@ModuleResources("**/web/rc")`, `report-uri`/`/csp-reports`, `'unsafe-inline'`/`'unsafe-eval'` —
14/14 confirmed present at the cited `file:line`.

| # | Claim | Marker | Citation | Verified? |
|---|---|---|---|---|
| 1 | No security-header filter declared in `web.xml`; only CSRF/functional filters | `[CERT]` | §27.1 | Y — full-text read |
| 2 | 5 `BIHttpHeaderProvider` children under one `BHttpHeaderProviders` component on the `BWebService` singleton | `[CERT]` | §27.2 | Y — direct decompile read |
| 3 | No per-servlet header-override API; one legacy `xFrameOptions` compat bridge | `[CERT]` | §27.2 | Y — `changed()`/`fwStarted()` read |
| 4 | Default CSP directives (`default-src`/`script-src`/`style-src`/etc.) incl. `'unsafe-inline'`/`'unsafe-eval'` | `[CERT]` | §27.3 | Y — `newProperty` defaults read |
| 5 | No nonce-generation code in `BCspHeaderProvider` | `[CERT]` | §27.3 | Y — full-method read, absence |
| 6 | `TridiumSecurityFilter` registered on `/*` programmatically in `BJettyWebServer`, not `web.xml` | `[CERT]` | §27.4 | Y — direct read |
| 7 | `web.jar` is itself the `isWar()`-flagged primary-context module | `[INFER]` | §27.4, B27-G4 | Partial — structural inference, `isWar()` not read |
| 8 | `JSESSIONID` session handler forces `secureRequestOnly`+`httpOnly` unconditionally | `[CERT]` | §27.5 | Y — direct read |
| 9 | `SameSite` is a per-station `BWebService.sameSite` property, default `lax`, applied to session + context default | `[CERT]` | §27.5 | Y — direct read |
| 10 | `TridiumSecurityServletResponse.addCookie()` force-upgrades `Secure` when request is secure | `[CERT]` | §27.5 | Y — direct read |
| 11 | Real CSRF = `x-niagara-csrfToken` synchronizer token, filter-mapped to 4 narrow URL patterns only | `[CERT]` | §27.6 | Y — direct read + `web.xml` |
| 12 | N4 corpus documents our own modules using `X-Requested-With` instead of the real token | `[CERT-a]` (cross-ref) | §27.6 | Y — `corpus-nav.py find`, 8+ block hits |
| 13 | `CspReportServlet` writes violations into `BCspHeaderProvider.violationText`, flips station fault | `[CERT]` | §27.7 | Y — direct read |
| 14 | `web.jar` declares `@ModuleResources("**/web/rc")`, a concrete non-`@ModuleResourcesAll` example | `[CERT]` | §27.8 | Y — `module-info.java` read |
| 15 | `rc/` resources served through the same filter-wrapped context as everything else | `[INFER]` | §27.8 | Partial — follows from §27.4, not independently traced |
| 16 | `DashboardPan-ux/index.html` has 1 inline `<script>` + 2 inline `<style>` blocks | `[CERT]` | §27.8 | Y — `grep` on live N4 source |
| 17 | Default CSP would not block those inline blocks as shipped | `[CERT]`+`[INFER]` | §27.8 | Y for the CSP string; INFER for the "would not block" application |
| 18 | HSTS/Referrer-Policy/CORS strings absent from both jars (scope-limited) | `[CERT]` | §27.9 | Y — byte-level zipfile census, 0 hits each |
| 19 | `X-Frame-Options` default is `DENY`, not the enum's own nominal `sameorigin` default | `[CERT]` | §27.10 | Y — both sites read fresh |

**Artifacts**: block file written; `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` regeneration is out of
scope for this READ-ONLY task (task instruction: write exactly this one file, touch no other).

## 27.x — Named child gaps

- **B27-G1** — Live-station `[CERT-hw]` HTTP response capture: confirm the computed defaults in §27.2–§27.5
  (CSP string, `X-Frame-Options: DENY`, cookie flags, `SameSite`) actually reach the wire exactly as the
  decompiled code implies, once a runnable N5 install/station exists. Same blocker noted in Blocks 2/4/10/21.
  `blocked-on-source`.
- **B27-G2** — Does any *other* shipped N5 module carry its own `jetty-web.xml` to opt out of
  `TridiumSecurityFilter`, change its context path, or otherwise diverge from the primary-context security
  policy? Only `web.jar`'s own `jetty-web.xml` was read this session. Requires a `WEB-INF/jetty-web.xml`
  census across all shipped module jars. `investigable`.
- **B27-G3** — `NiagaraConstraintSecurityHandler`/`NiagaraAuthenticator` (both in `jetty.jar`,
  `com.tridium.jetty.*`, 29,607 and 1,786 bytes respectively) — the actual authentication/authorization
  handler wired at `configureNiagaraWebApp()` (§27.4, `security.setAuthenticator(this.authenticator)`);
  out of this block's header/cookie/CSRF scope entirely. Requires decompiling and reading both classes.
  `investigable`.
- **B27-G4** — `NModuleInfo.isWar()`'s exact definition (presumably `baja.jar`, not opened this session) —
  needed to convert §27.4's `[INFER]` (that `web.jar` is itself picked up by `addModuleWebAppHandlers()`)
  into a `[CERT]`. `investigable`.
- **B27-G5** — Does `hx.jar` (server-rendered Px, already confirmed by Block 21 §21.8 to require Jetty
  12/`jakarta.servlet` directly) register its own `WebAppContext`/servlets through the same
  `configureNiagaraWebApp()` path, or through a different route that might bypass `TridiumSecurityFilter`?
  Not traced this session — `hx.jar` itself was not decompiled here (Block 21 only did a header-string
  census of it). `investigable`.

## 27.x — Connections

- **[Block 10]** — §10.9's `doc/modules.html` reading of `@ModuleResources`/JPMS resource-root mechanics is
  REMIT here; §27.8 supplies the concrete `@ModuleResources("**/web/rc")` example Block 10 only had from
  the doc's own sample. §10.11 CHK-12's characterization of `DashboardPan-ux/src/rc/index.html` as static
  HTML + vanilla JS + `fetch()` (no `bajaux`/`bajaui`) is the premise §27.8's DashboardPan-ux implication
  builds on.
- **[Block 21]** — §21.8's negative CSP-header-string search across 5 UI jars (`workbench.jar`, `hx.jar`,
  `bajaux.jar`, `webEditors.jar`, `gx.jar`) is corroborated, not contradicted, by this block: those 5 jars
  correctly have **no** header-injection code of their own, because header injection is centralized in
  `web.jar`/`jetty.jar` and applied station-wide via the filter chain (§27.4), not per-UI-module. This
  block **closes** the named child gap **B21-G3**'s static-jar-census half (the live-station half remains
  open as **B27-G1**).
- **N4 corpus (remit)** — [B9]/[B11]/[B27]/[B29]/[B47]/[B602] (the identical `BCspHeaderProvider`,
  `BSameSiteEnum`, `CsrfUtil`, `x-niagara-csrfToken`, cookie-flag, and `SameSite=None`-needs-`Secure`
  architecture already fully documented for N4 — confirmed byte-identical in class/package naming and
  default values for N5 in §27.3/§27.5/§27.6), [B763]/[B796]/[B803]/[B813]/[B823]/[B1015] (our own
  `DashboardPan`/`chihuahua` modules' hand-rolled `X-Requested-With` CSRF-lite guard, contrasted against
  the real `CsrfUtil` token in §27.6 — the N4 finding carries forward unchanged), [B1063]/[B1065] (ODA2's
  ""no CSP anywhere in `BDashboardServlet`"" gap and its proposed fix — §27.8 shows the station-level
  default already covers the inline-script/style case on N5, making that fix largely redundant there).
