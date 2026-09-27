# Block 54 — N5 security auditing, NiagaraRpc Context injection and residual AccessController/Subject usage

> Research closing **three named child gaps**: (1) **B41-G1** — the full `SecurityAuditEvent`/
> `SecurityAuditor`/`BSecurityAuditHistorySource` channel [Block 41] §41.3 only partially traced (event
> shape, storage, and — the part Block 41 explicitly left `[INFER]` — exactly which operations the
> `BAuditHistoryService.checkSecurityAudit()` router sends to this channel vs the general `AuditHistory`);
> (2) **B49-G2** — the actual `NiagaraRpcServlet`/`NiagaraRpcUtil.rpc()` dispatch code that injects a
> `Context` into an `@NiagaraRpc` method, which [Block 49] §49.5/§49.6 cited only via N4 REMIT ([Block 613])
> without opening N5's own dispatcher; (3) **B44-G2** — per-site disposition of the 25
> `AccessController`/`AccessControlContext`/`AccessControlException`/`SubjectDomainCombiner` for-removal
> call sites [Block 44] §44.2 found in `jetty`/`platform`/`hx` (+ `baja`/`nre`/`web`), settling whether any
> of them makes a live authorization decision from an `AccessControlContext`/`Subject` — including the
> specific Java 18+/23 hazard the task named: `Subject.getSubject(AccessControlContext)` is deprecated and
> throws `UnsupportedOperationException` unless `-Djava.security.manager=allow`, so a call site relying on
> it would be a real runtime break, not merely dead plumbing.
>
> Does **not** cover: a live-station capture of any audited event (`[CERT-hw]`, blocked — no runnable N5
> station this session, same constraint as [Block 41]'s **B41-G4**/[Block 49]'s **B49-G1**); the JAAS
> `LoginService`/`UserIdentity` internals that first populate the `Subject` `SecurityUtil.current()` reads
> ([Block 41]'s **B41-G3**, still open, not re-derived); the `securityBridge.jar`/ByteBuddy-agent mechanics
> themselves ([Block 3], REMIT only); the 152 third-party `bin/ext` jars outside `nre.jar`'s
> `AccessController` family ([Block 44] §44.6, out of scope); or a JVM-launch-flag confirmation of
> `-Djava.security.manager=<value>` (no launcher script/manifest was in the corpus's decompiled-source
> scope this session — flagged as a genuine limitation in §54.5, not silently assumed).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as Blocks 3/7/20/27/28/41/44/46/49
> (`etc/brand.properties:workbench.notice`). No fresh decompilation — every file cited was already present
> in this corpus's `organized/` tree from prior sessions ([Block 1]'s corpus-wide extraction, or [Block 25]/
> [Block 44]'s `bin/ext` extraction for `nre.jar`, `platform.jar`, `hx.jar`, `jetty.jar`).
>
> Sources: `organized/_bin-ext/nre/vineflower/niagara/nre/security/{SecurityAuditEvent,SecurityAuditor,
> DefaultSecurityAuditor}.java`, `organized/_bin-ext/nre/vineflower/niagara/nre/util/SecurityUtil.java`,
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/{PermissionBridge,
> PermissionManager}.java`, `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/
> Aes256PasswordManager.java`, `organized/_bin-ext/nre/vineflower/com/tridium/nre/util/
> {PrivilegedNamedThreadFactory,PrivilegedRunnable}.java`, `organized/history/vineflower/com/tridium/
> history/audit/{BAuditHistoryService,BSecurityAuditHistorySource,BSecurityAuditRecord,
> BAbstractAuditHistorySource}.java`, `organized/baja/vineflower/com/tridium/syslog/SyslogAuditHandler.java`,
> `organized/baja/vineflower/niagara/user/{BUser,BUserService}.java`, `organized/baja/vineflower/com/
> tridium/authn/BAuthenticationService.java`, `organized/baja/vineflower/com/tridium/session/AuditInfo.java`,
> `organized/baja/vineflower/com/tridium/sys/{Console,Nre,station/Station}.java`, `organized/baja/
> vineflower/niagara/{sys/Sys.java,security/BPassword.java}`, `organized/jetty/vineflower/com/tridium/
> jetty/{NiagaraHttpSession,BJettyWebServer,PrivilegedQueuedThreadPool}.java`, `organized/platform/
> vineflower/com/tridium/platform/daemon/BDaemonSession.java`, `organized/hx/vineflower/com/tridium/hx/
> BHxPathBar.java`, `organized/web/vineflower/{niagara/web/servlets/NiagaraRpcServlet.java,com/tridium/
> util/NiagaraRpcUtil.java,com/tridium/web/filters/OrdTargetFilter.java}` (`NiagaraRpcUtil` is physically
> under `organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java` — see §54.3 note),
> `organized/baja/vineflower/niagara/rpc/NiagaraRpc.java`, `organized/platCrypto/vineflower/com/tridium/
> platcrypto/web/BCertificateManagementRpc.java`, `organized/httpClient/vineflower/com/tridium/httpClient/
> util/HttpClientUtils.java`, `organized/orion/vineflower/com/tridium/orion/priv/securityAudit/
> BOrionSecurityAudit.java`, `organized/abstractMqttDriver/vineflower/com/tridium/mqttClientDriver/
> authenticator/gcp/BTokenParameters.java`, `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/
> {http/WebServer.java,app/AppRegistry.java}` — all pre-existing in-corpus decompiles, read fresh this
> session. N4 comparison via `python3 tools/corpus-nav.py find "SecurityAudit"` (sibling corpus
> `/home/cristian/niagara-research`, N4 corpus **B564**/**B30**/**B167**/**B700**/**B689**/**B685**/**B123**
> REMIT).
>
> Method: direct reading of pre-existing in-corpus Vineflower decompiles (nothing re-decompiled this
> session); whole-tree `grep -rn` census across every `organized/*/vineflower/` subtree for
> `SecurityAuditor`/`new SecurityAuditEvent(`/`@NiagaraRpc`/`AccessController`/`AccessControlContext`/
> `Subject.getSubject(`/`Subject.doAs(`/`Subject.current(`/`Subject.callAs(`/`SubjectDomainCombiner`/
> `System.setSecurityManager` (each reported as a **corpus-wide** hit count, not a sample); one
> `corpus-nav.py find` REMIT lookup into the sibling N4 corpus.
> Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device — highest ·
> `[CERT]` local primary source (`file:line`) · `[CERT-a]` secondary/forum · `[INFER]` deduction.
> `file:line` citations point into `organized/<module>/vineflower/...` inside **this** corpus
> (`/home/cristian/niagara5-research/`) unless prefixed `N4:`, which points into the sibling corpus.
>
> Security/audit + RPC-dispatch + JDK-deprecation layers, all converging on the same question ("does this
> code make a real authorization/audit decision, or is it inert/plumbing"). Connects [Block 41] (closes
> **B41-G1**, corrects §41.3's hedged `[INFER]` reading with a direct `checkSecurityAudit()` re-read),
> [Block 49] (closes **B49-G2**, opens the N5 dispatcher §49.6 cited only via N4 REMIT), [Block 44] (closes
> **B44-G2**, per-site disposition of the `AccessController` family), [Block 3] (the
> `SecurityManager`→ByteBuddy-agent replacement this block's §54.5 confirms file-by-file, not just at the
> architectural-family level), and N4 corpus **B564** (byte-identical-until-N5 audit architecture REMIT).
>
> **Type:** `mixed` — §54.1–§54.4 are evidence (fresh reads of already-decompiled N5 source, whole-tree
> `grep` censuses); §54.5's per-site "inert vs. live" verdict draws `[INFER]` conclusions across this
> block's own `[CERT]` evidence and [Block 3]'s prior finding.

---

## 54.1 — `SecurityAuditEvent`/`SecurityAuditor`: shape and storage, and the N4→N5 package split `[CERT]`

`SecurityAuditEvent` is a flat value object — `operation`, `userName`, `message` (a pre-formatted string,
not structured fields), and `timestamp` (stamped at construction via `System.currentTimeMillis()`) — with
13 named operation constants: `LOGIN`, `LOGOUT`, `LOGIN_FAILURE`, `TIMEOUT` ("Logout (Timeout)"), `ADDED`,
`CHANGED`, `RENAMED`, `REMOVED`, `RECATEGORIZED`, `SYSTEM_USER` (not an operation — the `"--system--"`
username sentinel), `STARTUP`, `SHUTDOWN`, `INVOKED` `[CERT]` `niagara/nre/security/SecurityAuditEvent.java:8-32`.
`SecurityAuditor` is a one-method interface, `void audit(SecurityAuditEvent)` `[CERT]`
`niagara/nre/security/SecurityAuditor.java:3-4`. `DefaultSecurityAuditor.INSTANCE` is a singleton whose
`audit()` body is **empty** — a genuine no-op, not merely a null-check fallback `[CERT]`
`niagara/nre/security/DefaultSecurityAuditor.java:9-11` — installed as `SecurityUtil`'s static default
(§54.2) until a real auditor registers.

**N4→N5 architectural delta not previously named in this corpus.** N4's identical interfaces
(`Auditor`/`SecurityAuditor`/`AuditEvent`/`SecurityAuditEvent`) all live in **one** package,
`javax.baja.security`, per N4 corpus **B564** (`corpus-nav.py find "SecurityAudit"`, lines 10/26/36/47
of that block — REMIT, not re-derived). N5 **splits** this in two: the general-purpose
`Auditor`/`AuditEvent` pair stays in the `baja` module as `niagara.security.{Auditor,AuditEvent}`
(confirmed already by [Block 41] §41.2), but `SecurityAuditor`/`SecurityAuditEvent` moved **out of `baja`
entirely** into `niagara.nre.security` — physically inside `nre.jar`, the Niagara Runtime Environment
layer that loads *before* the `baja` framework module `[CERT]` (package `niagara.nre.security`,
`organized/_bin-ext/nre/vineflower/niagara/nre/security/*.java`, a `bin/ext`-jar path per [Block 25]'s
established `nre.jar` location, distinct from every `organized/<module>/vineflower/` module-jar path cited
elsewhere in this block). `[INFER]`: this is consistent with the security-audit channel needing to be
reachable from code that runs *before* a station/`baja` module context exists — e.g. §54.2's `Console`
bridge (platform-daemon-to-station audit relay, which fires from the NRE bootstrap layer, not from
inside a running station) — a placement N4's single-package design did not need to make.

## 54.2 — Emitters: the full census, and the general-Auditor → SecurityAuditor bridge (`checkSecurityAudit`) `[CERT]`

**The wiring.** `SecurityUtil` (nre.jar) holds the single static `SecurityAuditor` field (default
`DefaultSecurityAuditor.INSTANCE`) with `setSecurityAuditor`/`getSecurityAuditor` `[CERT]`
`niagara/nre/util/SecurityUtil.java:42,313-320`; `Nre.setSecurityAuditor`/`getSecurityAuditor` and
`Sys.getSecurityAuditor` are thin pass-throughs to it `[CERT]` `com/tridium/sys/Nre.java:1323-1328`,
`niagara/sys/Sys.java:176-178`. `BSecurityAuditHistorySource` (a nested component of
`BAuditHistoryService`, own `historyConfig` default `BHistoryId.make("station", "Security History")` /
`BTypeSpec.make("history", "SecurityAuditRecord")`) is the **sole** first-party implementer in the whole
decompiled tree: it registers itself as the process-wide `SecurityAuditor` on `auditStarted()`/clears it
on `auditStopped()` `[CERT]` `com/tridium/history/audit/BSecurityAuditHistorySource.java:36,60-79`, and its
`audit(SecurityAuditEvent)` converts to `BSecurityAuditRecord.fromEvent(event)` and appends via the shared
`BAbstractAuditHistorySource.audit(BAbstractAuditRecord)` history-append path `[CERT]`
`BSecurityAuditHistorySource.java:76-79`, `BAbstractAuditHistorySource.java:205-235` — an ordinary station
history (`$/SecurityHistory`), the same `HistorySpaceConnection`/`BFileHistoryTable` machinery [Block 41]
§41.3 already named for the general `AuditHistory`, just a second, parallel stream. `BSecurityAuditRecord`
carries exactly `operation` (inherited) + `userName` + `message` + `timestamp` `[CERT]`
`BSecurityAuditRecord.java:20-26,66-67` — a flat 1:1 mapping from `SecurityAuditEvent`, confirming §54.1's
"message is pre-formatted prose, not structured old/new fields" reading; **this is the concrete answer to
Block 41's open question** (§41.10 B41-G1: "does it reach a history, or only syslog?") — it reaches BOTH,
via `SyslogAuditHandler.publish(event, true)` (§54.1's sibling call, `com/tridium/syslog/
SyslogAuditHandler.java:21-61`, gated independently by `SyslogManager.getSecurityAuditEnabled()`) AND the
`$/SecurityHistory` append.

**`checkSecurityAudit()` — the exact router, resolving Block 41's `[INFER]` hedge to a `[CERT]` reading.**
[Block 41] §41.3 read this method and, unable to reconcile its own observation that "every branch
explicitly returns `true` or `false`" with a hypothesis that "all paths fall through" to the general
history, left the routing as `[INFER]`. A direct re-read this session (`BAuditHistoryService.java:108-263`,
whole method) settles it exactly: the **return value directly gates** whether `BAuditHistoryService.audit()`
appends to the general `$/AuditHistory` (`if (shouldAudit) { this.audit(BAuditRecord.fromEvent(event));
syslogAuditHandler.publish(event, false); }`, `:108-114`) — there is no unconditional fall-through.

| Operation | Returns | General `$/AuditHistory`? | Routed to `SecurityAuditor`/`$/SecurityHistory`? | Condition |
|---|---|---|---|---|
| `Login` / `Logout` / `Login Failure` / `Logout (Timeout)` | `false` | **No** | **Always**, if a `SecurityAuditor` is registered | unconditional (`:248-261`) |
| `Recategorized` | `false` | **No** | Only if a `SecurityAuditor` is registered | unconditional message build, gated only by auditor presence (`:122-130`) |
| `Added` | `true` | **Yes** | Only if the added slot's type `is(BISecurityAuditable.TYPE)` | slot-type check (`:131-147`) |
| `Renamed` | `true` | **Yes** | Only if the renamed-to slot's type `is(BISecurityAuditable.TYPE)` | slot-type check (`:148-164`) |
| `Removed` | `true` | **Yes** | Only if `event.getValue() != null` | value-presence check (`:165-179`) |
| `Changed` | `true` | **Yes** | Only if the changed slot (or a segment of a nested slot path) carries facet `security=true` | facet walk over `event.getSlotName().split("/")` (`:180-217`) |
| `Invoked` | `true` | **Yes** | Only if the invoked action's slot carries facet `security=true` | facet check (`:219-247`) |

`[CERT]` (every cell traced to the cited line range this session). **Net effect:** the login/logout family
and `Recategorized` are the only operations *excluded* from the general audit trail — every other
operation always lands in `$/AuditHistory`, and *additionally* reaches `$/SecurityHistory` exactly when a
`security=true` facet (or, for `Added`/`Renamed`, a `BISecurityAuditable`-typed slot) is present on the
affected slot. `BUser`'s own `roles`, `allowConcurrentSessions`, and `autoLogoffSettings` properties all
carry `BFacets.make("security", BBoolean.TRUE)` `[CERT]` `niagara/user/BUser.java:226,229,231` — so a role
or session-policy change on a user IS dual-routed to `$/SecurityHistory` through this generic `Changed`
facet path, not through a dedicated `SecurityAuditEvent` operation constant (there is no `"Role Changed"`
constant in §54.1's 13-constant list).

**Whole-corpus emitter census** (every `new SecurityAuditEvent(` / `SecurityAuditor.audit(` call site
found this session, `grep -rn` over `organized/`, 19 hits total — §54.2's table below is exhaustive for
this corpus, not a sample):

| Emitter | Operation(s) | Channel | Citation |
|---|---|---|---|
| `BAuthenticationService.auditLoginAttempt` (private, called from `processLoginAttempt` at `:250,257`) | `Login`/`Login Failure` — via general `Auditor`, `AuditInfo.makeAuditEvent(...)`, re-routed by `checkSecurityAudit` | general→security | `[CERT]` `com/tridium/authn/BAuthenticationService.java:362-386` |
| `NiagaraHttpSession.auditLogout()` | `Logout`/`Logout (Timeout)` — general `Auditor`, re-routed | general→security | `[CERT]` `com/tridium/jetty/NiagaraHttpSession.java:256-268` |
| `Station` (station startup/shutdown) | `Startup`/`Shutdown` — general `Auditor`, **not** an operation `checkSecurityAudit` re-routes (falls to the `else` branch, `:248-261`, still forwarded since neither is `Recategorized` — wait, see note below) | general | `[CERT]` `com/tridium/sys/station/Station.java:320,344` |
| `BUserService.fwStationStarted` (password-conversion migration) | `Changed`, user `"--system--"` — **direct** `SecurityAuditor` call, bypasses the general channel entirely | security (direct) | `[CERT]` `niagara/user/BUserService.java:706-719` |
| `PermissionManager` (a permission check throws `PermissionException`) | `"Permission Check"` (not one of §54.1's 13 constants — a free-form string) | security (direct) | `[CERT]` `com/tridium/nre/security/permissions/PermissionManager.java:123` |
| `PermissionBridge.auditNetworkConnection` | `"Network connection"` | security (direct) | `[CERT]` `com/tridium/nre/security/permissions/PermissionBridge.java:40-46` |
| `BCertificateManagementRpc.audit(op,msg)` helper | `"Certificate generation"`, `"User Key Store reset"` | security (direct) | `[CERT]` `com/tridium/platcrypto/web/BCertificateManagementRpc.java:1092-1098,351,390` |
| `HttpClientUtils.auditAddressChange` | `"Changed"`, outbound HTTP client address edits | security (direct) | `[CERT]` `com/tridium/httpClient/util/HttpClientUtils.java:230-236` |
| `Console.securityAuditEvent` (see below) | any operation string, relayed verbatim from a spawned child process | security (direct, cross-process) | `[CERT]` `com/tridium/sys/Console.java:121-140` |
| `BOrionSecurityAudit.securityAudit{Created,Deleted,Modified}` | `Added`/`Removed`/`Changed`, Orion-subsystem objects | security (direct) + a **separate** Orion-owned database record (`session.insert(secRec)`), independently of `BSecurityAuditHistorySource` | `[CERT]` `com/tridium/orion/priv/securityAudit/BOrionSecurityAudit.java:142-234` |
| `BTokenParameters` (MQTT/GCP cloud auth) | `"Token generation"` | security (direct) | `[CERT]` `com/tridium/mqttClientDriver/authenticator/gcp/BTokenParameters.java:504` |
| `BUserService.auditLoginAttempt` (public, `niagara/user/BUserService.java:415-434`) | `Login`/`Login Failure` — general `Auditor` | **dead code in this corpus**: whole-tree `grep` for `.auditLoginAttempt(` finds this method's own definition and zero callers anywhere in `organized/` `[CERT]` (grep run this session) | — |

`[INFER]` on the `Station` startup/shutdown row: `checkSecurityAudit`'s operation-string `switch` has no
`case` for `"Startup"`/`"Shutdown"` (its named branches are only the 4 login/logout strings, `Recategorized`,
`Added`, `Renamed`, `Removed`, `Changed`, `Invoked` — `:118-247`), so control falls to the final `else`
(`:248-261`), which **unconditionally forwards to the security channel** (if a `SecurityAuditor` is
registered) but **returns `false`** — meaning station startup/shutdown, like login/logout, is excluded
from the general `$/AuditHistory` and lands **only** in `$/SecurityHistory`. `[INFER]` because this is
this block's own reading of the `else` fallback's consequence for an operation string not explicitly named
in Block 41's table, not a literal quote of a `case "Startup"` branch (there is none).

**The `daemonspawn` cross-process bridge — a genuine N5 mechanism not previously documented in this
corpus.** `com.tridium.niagarad.app.AppRegistry.sendSecurityAuditEvent(operation, username, message)`
(a method in the **platform daemon**, `niagarad.jar`, a *separate JVM process* from the station) Base64-encodes
`"<op>;<user>;<message>"` and sends it as a `"securityauditevent"` message to every running station app
process it manages `[CERT]` `com/tridium/niagarad/app/AppRegistry.java:360-368`. It is called from
`WebServer` (the daemon's own embedded HTTP config UI) on platform-level `Login`/`Login Failure`/`Logout`
`[CERT]` `com/tridium/niagarad/http/WebServer.java:1407,1444,1470`. On the receiving (station) side,
`Console.securityAuditEvent(String eventEncoding)` — reachable only when the station process was launched
with the `"daemonspawn"` command-line option — decodes the Base64 payload, splits it on `;`, and calls
`Sys.getSecurityAuditor().audit(new SecurityAuditEvent(event, user, message))` directly, but **only if** a
real (non-default) `SecurityAuditor` is currently registered `[CERT]` `com/tridium/sys/Console.java:121-140`.
`[INFER]`: this is the mechanism by which a login to the **platform daemon's own web config port** (distinct
from a login to the running station's own Niagara session) still ends up in that station's `$/SecurityHistory`
— necessary because `niagarad` is a separate process with no station component tree of its own to host a
`BSecurityAuditHistorySource`.

## 54.3 — N4 comparison (REMIT) `[CERT-a]`+`[CERT]`

N4 corpus **B564** (`python3 tools/corpus-nav.py find "SecurityAudit"`, this session, sibling corpus
`/home/cristian/niagara-research`) already fully mapped the byte-identical *mechanism*: two interfaces
(`Auditor`/`SecurityAuditor`), the same flat `SecurityAuditEvent` shape, the same `Sys.getAuditor()`/
`getSecurityAuditor()` pluggable-singleton pattern, and the same `BAuditHistoryService`/
`BSecurityAuditHistorySource` sink pair — confirming N5 carried this architecture forward essentially
unchanged (only the package split named in §54.1 is new). N4 corpus **B700** (a live JACE `$/SecurityHistory`
capture, `[CERT-hw]` in that corpus) independently confirms the **same 4-field `SecurityAuditRecord` schema**
(`timestamp`/`operation`/`userName`/`message`) this block's §54.1 read from N5 source — cross-version
structural stability, not merely a naming coincidence. N4 **B167** additionally documents that N4's
`BSecurityAuditHistorySource` hardcodes its history name as `"SecurityHistory"` with a javadoc explicitly
stating login/logout are diverted there — matching this block's §54.2 finding for N5 exactly (`getHistoryId()`
returns `BHistoryId.make(..., "SecurityHistory")`, `BSecurityAuditHistorySource.java:56-58`). No
`checkSecurityAudit`-equivalent routing-logic block was surfaced in the `corpus-nav.py find` output — this
block's §54.2 table is (`[INFER]`, based on an absence in the search results, not a confirmed absence per
METHODOLOGY §3's negative-existence rule) the first place *either* corpus documents the routing rule
per-operation, rather than only the two sinks' existence.

## 54.4 — `@NiagaraRpc` Context injection and the permission check that precedes it: full dispatch trace, closing B49-G2 `[CERT]`

**Servlet entry.** `NiagaraRpcServlet.doPost()` recovers `Context cx = (Context)
req.getAttribute("niagara.context")` — the **exact same** request attribute [Block 41] §41.7 traced back to
`ContextFilter` — and passes it straight into `NiagaraRpcUtil.rpc(TransportType.web, req.isSecure(),
remoteAddr, ord, methodName, arguments, cx)` for both the single-call (`/method/ord`) and batch (JSON body
array) request shapes `[CERT]` `niagara/web/servlets/NiagaraRpcServlet.java:31-54,80-91`. This confirms
[Block 49] §49.5's premise mechanically: the RPC-dispatching servlet, not manual per-method code, is what
recovers the authenticated `Context`.

**`NiagaraRpcUtil.rpc()` — the actual injection site (whole 54-196 method read this session).** Note this
file's package/physical location: it is `com.tridium.util.NiagaraRpcUtil`, but physically lives under
`organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java` in this corpus (the `baja` module, **not**
`web` — [Block 49] §49.x's header implied a `web`-module location that this session's direct file lookup
corrects; flagged here rather than silently repeated). The method:

1. Resolves the target `BObject`/`Class` from the `ord` via `OrdTarget`/reflection (`:57-69`).
2. Reflectively locates the target `Method` by name + arg types (`:122-127`), then reads its
   `@NiagaraRpc` annotation — `NoSuchMethodException` if absent (`:129-132`) or if the transport doesn't
   match (`:134-136`).
3. **Builds the injected `Context` argument as a fresh anonymous `SecurableContext`**, not a pass-through
   of the raw `cx` from the servlet:
   ```java
   final BUser user = BUser.getCurrentAuthenticatedUser();
   args.add(new SecurableContext() {
      public boolean isSecure() { return isSecure; }
      public Context getBase() { return cx; }
      public BUser getUser() { return user; }
      ...
   });
   ```
   `[CERT]` `com/tridium/util/NiagaraRpcUtil.java:87-121`. **This is the answer to the task's literal
   question "user-bound? super context?": neither directly** — the injected `Context`'s `getUser()` returns
   `BUser.getCurrentAuthenticatedUser()` (a **thread-bound JAAS `Subject` lookup**, traced to its source in
   §54.5), independently of whatever `BUser` the original servlet-recovered `cx` carried; `cx` itself is
   preserved only as `getBase()`, a fallback/delegation target for other `Context` methods (e.g.
   `getLanguageCode()`, `:118-120`) — **not** as the direct source of `getUser()`. In the ordinary web
   request path both resolve to the same authenticated user (§54.5 confirms `getCurrentAuthenticatedUser()`
   ultimately reads the same session-bound identity `ContextFilter` populated `niagara.context` from), but
   they are architecturally two different lookups, not one value threaded through.
4. **The permission check precedes invocation, and is declarative from the annotation, not hand-coded per
   method** — in order: `rpc.isSecure()` vs the transport's actual security (`:139-141`); if the target
   `object` is `BIProtected`, `object.getPermissions(cx).has(BPermissions.make(rpc.permissions()))`
   (`:152-157`, using the ORIGINAL servlet `cx`, not the injected wrapper); else, if `protectedTargets()` is
   empty and a non-empty `permissions()` string is declared, the same check against
   `target.getSecurityTarget().getPermissions(cx)` (`:158-169`); then, for every entry in
   `rpc.protectedTargets()` (additional named ORDs each carrying their own required-permission string), the
   identical `getPermissions(cx).has(...)` check against **that** ORD's resolved security target
   (`:171-185`). Any failed check throws `PermissionException` **before** `method.invoke(...)` is ever
   reached (`:187-188`, the last line of the method). `[CERT]` (whole block, `:138-188`).

**Answer to the task's implication question.** A third-party `@NiagaraRpc` method that declares a trailing
`Context cx` parameter receives a real, framework-constructed `Context` whose `getUser()` is bound to the
CURRENT authenticated `BUser` — it does not need to (and structurally cannot easily) forge or omit this,
since it never constructs the `Context` itself; the dispatcher does. Authorization is likewise not
optional boilerplate the method must remember to call — `permissions()` (default `"I"`, i.e. Invoke) is
enforced by `NiagaraRpcUtil.rpc()` **before** reflection ever invokes the method body. This closes B49-G2:
the injection mechanism is confirmed present, source-read, and file:line-cited for N5 itself (not merely
inherited via N4 REMIT as [Block 49] §49.6 left it).

## 54.5 — `AccessController`/`AccessControlContext`/`Subject`: per-site disposition, closing B44-G2 `[CERT]`+`[INFER]`

**The central corpus-wide fact, settling the task's `Subject.getSubject`/`UnsupportedOperationException`
concern directly.** A whole-tree `grep -rn` this session for every `javax.security.auth.Subject` call
shape found:

| Pattern | Hits | Citation |
|---|---:|---|
| `Subject.getSubject(` (deprecated `AccessControlContext`-bound lookup — Java 18+ throws `UnsupportedOperationException` unless `-Djava.security.manager=allow`) | **0** | — |
| `Subject.doAs(` (deprecated 2-arg `PrivilegedAction`/`PrivilegedExceptionAction` form) | **0** | — |
| `Subject.current()` (Java 18+ replacement, no `AccessControlContext`/`SecurityManager` dependency) | **1** | `[CERT]` `niagara/nre/util/SecurityUtil.java:358` |
| `Subject.callAs(` (Java 18+ replacement for `doAs`) | **2** | `[CERT]` `SecurityUtil.java:276,292` |

`[CERT]` (all four counts from `grep -rn` over the whole `organized/` tree this session). **N5's own
`SecurityUtil` is the SOLE `Subject`-API call site in the entire decompiled corpus, and it exclusively uses
the modern, SecurityManager-independent API** — `getCurrentAuthenticatedSubject()` returns `Subject.current()`
(falling back to an `InheritableThreadLocal<Subject>` cache, `:357-364`), and `callAs(Subject, Callable)`
wraps `Subject.callAs(subject, callable)` (`:272-302`) — this is exactly the API [Block 49] §49.4 already
named as the mechanism behind `AddSubjectFilter.SecurityUtil.callAs(subject, ...)` (REMIT, confirmed
concretely here). **The task's hypothesized runtime break does not apply to N5**: because
`Subject.getSubject(AccessControlContext)` is never called anywhere in this corpus, its Java 18+
`UnsupportedOperationException`-under-restricted-mode hazard has no call site to trigger it. N5 had already
migrated this specific API surface before this corpus's subject build (5.0.0.28); `BUser.getCurrentAuthenticatedUser()`
itself reads through this exact path — `Subject subject = SecurityUtil.getCurrentAuthenticatedSubject();
return subject != null ? getUserFromSubject(subject) : null;` `[CERT]` `niagara/user/BUser.java:1212-1214` —
which is also what §54.4's `NiagaraRpcUtil.rpc()` injection ultimately resolves through.

**No launch-flag confirmation possible from source alone.** Whether the N5 station process is actually
launched with `-Djava.security.manager=allow`/`disallow`/`default` cannot be determined from decompiled
`.class`/`.java` content — that is a JVM command-line argument, not compiled into any class. This session's
scope (decompiled source only, no launcher script/manifest in the corpus) cannot certify this either way;
flagged as **B54-G1** rather than silently assumed. `[INFER]` (not asserted as `[CERT]`): given zero
`Subject.getSubject(AccessControlContext)` call sites exist to trip the restricted-mode exception regardless
of the flag's value, this gap is lower-priority than it would be if such a call site existed.

**Per-site disposition of the 25 `AccessController` family for-removal sites (§44.2), the 3 modules
[Block 44] flagged new to this block's scope (`jetty`/`platform`/`hx`) plus the `web`/`baja`/`nre` sites
this session additionally opened:**

| Class | Pattern | What it actually does under N5 (no `SecurityManager` — [Block 3] REMIT) | Verdict |
|---|---|---|---|
| `BHxPathBar` | `catch (AccessControlException ignore)` | Dead catch clause — nothing in the corpus's reachable code throws this exception without an installed `SecurityManager` | **inert** `[CERT]` `com/tridium/hx/BHxPathBar.java:358` |
| `Aes256PasswordManager` | `catch (AccessControlException ace)` | Same — dead catch | **inert** `[CERT]` `com/tridium/nre/security/Aes256PasswordManager.java:180` |
| `BPassword` | `catch (MissingEncodingKeyException \| AccessControlException rethrow)` | Same — dead catch, combined with an unrelated live exception type | **inert (for the `AccessControlException` half)** `[CERT]` `niagara/security/BPassword.java:257` |
| `PrivilegedNamedThreadFactory` | stores an `AccessControlContext` field, constructs `PrivilegedRunnable(r, context)` | The context is threaded through but only consumed by `PrivilegedRunnable.run()` below | **plumbing, not itself a decision** `[CERT]` `com/tridium/nre/util/PrivilegedNamedThreadFactory.java:9,24` |
| `PrivilegedQueuedThreadPool` | same pattern — field + `newThread()` wraps in `PrivilegedRunnable` | Same | **plumbing** `[CERT]` `com/tridium/jetty/PrivilegedQueuedThreadPool.java:10-13` |
| `PrivilegedRunnable` | `AccessController.doPrivileged(() -> { r.run(); return null; }, this.context)` | The 2-arg for-removal overload. Without an installed `SecurityManager`, `AccessController.checkPermission()`/`SecurityManager.checkPermission()` are never invoked, so nothing ever consults `this.context` — the call degrades to `r.run()` inside a privileged marker frame that has no observer | **inert (executes correctly, `context` argument has zero effect)** `[CERT]` `com/tridium/nre/util/PrivilegedRunnable.java:16-21` |
| `BJettyWebServer` | `AccessController.getContext()` captured and stored into a fresh `PrivilegedQueuedThreadPool` (`:555-557`) | Feeds the inert chain above — every embedded-Jetty worker thread is wrapped, but the wrap is a no-op under N5's security model | **inert** `[CERT]` `com/tridium/jetty/BJettyWebServer.java:555-557` |
| `BDaemonSession.initWsExecutorService` | same `AccessController.getContext()` → `PrivilegedNamedThreadFactory` pattern, for the daemon's cloud-websocket-client executor | Same inert chain | **inert** `[CERT]` `com/tridium/platform/daemon/BDaemonSession.java:2974-2986` |
| `OrdTargetFilter.doFilter` | `AccessControlContext privilegedContext = AccessController.getContext(); ... SecurityUtil.addSubjectToContext(privilegedContext); AccessController.doPrivileged(() -> {...}, privilegedContextWithSubject);` | Same degradation as `PrivilegedRunnable` — the 2-arg `doPrivileged` executes the lambda directly; `addSubjectToContext` additionally wraps a `SubjectDomainCombiner(subject)` around the context (`SecurityUtil.java:308-311`), but **nothing in the whole corpus ever reads that Subject back out via the deprecated `Subject.getSubject(AccessControlContext)`** (0 hits, above) — the embedded `SubjectDomainCombiner` is itself dead weight | **inert** `[CERT]` `com/tridium/web/filters/OrdTargetFilter.java:76-84`, `niagara/nre/util/SecurityUtil.java:308-311` |
| `nre.jar`'s own `SecurityUtil.doPrivileged(PrivilegedAction<T>)` overload | `return privilegedAction.run();` | **Does not call `AccessController.doPrivileged` at all** — a bare passthrough. Every one of the dozens of `SecurityUtil.doPrivileged(...)` call sites this session encountered across `BJettyWebServer`, `BDaemonSession`, `BPassword`, `BAbstractAuditHistorySource`, etc. is therefore not exercising the deprecated API at all, regardless of what the lambda body does | **N/A — not an `AccessController` call site; a same-named convenience wrapper that dropped the real mechanism** `[CERT]` `niagara/nre/util/SecurityUtil.java:236-238` |

`[CERT]` for every individual site's code shape; the aggregate **verdict is `[INFER]`**, built directly from
this session's own per-site `[CERT]` reads plus [Block 3]'s independently-established "N5 has no installed
`SecurityManager`, enforcement moved to a ByteBuddy `-javaagent`" finding (REMIT, not re-derived): **every
one of the 25 for-removal `AccessController`-family sites census-counted by [Block 44] §44.2, across all
six modules (`nre`, `jetty`, `web`, `platform`, `baja`, `hx`), is either a dead exception-catch clause or a
"privileged context" propagation chain (`getContext()` → store/thread → `doPrivileged(action, context)`)
whose `context` argument is provably never consulted for an authorization decision anywhere in this
corpus** — because (a) no `SecurityManager` is installed to invoke `checkPermission` against it
([Block 3]), and (b) the one place a `Subject` is embedded into such a context via `SubjectDomainCombiner`
(`OrdTargetFilter`) is never read back through the one API (`Subject.getSubject(AccessControlContext)`)
that could extract it. This **confirms [Block 3]'s "architecturally inert" reading site-by-site rather than
at the family level** (closing B44-G2) and **positively rules out** the task's hypothesized
`Subject.getSubject`/`UnsupportedOperationException` runtime-break scenario for this specific codebase, for
the concrete reason that the deprecated call is simply never made — authorization in the RPC/web path
instead runs through `NiagaraRpcUtil`'s declarative `BIProtected.getPermissions()` checks (§54.4) and the
`niagara.context`/`BPermissions` chain [Block 41] §41.8 already documented, neither of which touches
`AccessController`/`Subject.getSubject` at all.

## 54.6 — Self-verification

**Token check.** Every load-bearing `[CERT]` `file:line`/grep-count citation above was read or `grep`-run
directly this session (not hand-recalled): `SecurityAuditEvent.java`/`SecurityAuditor.java`/
`DefaultSecurityAuditor.java` (whole files, 3 reads), `BSecurityAuditHistorySource.java` (whole 117-line
file), `BAuditHistoryService.java` `checkSecurityAudit` (whole `:108-263`, the full method, not excerpted),
`BSecurityAuditRecord.java` (whole 126-line file), `SyslogAuditHandler.java` (whole 73-line file),
`BAbstractAuditHistorySource.java` (whole 308-line file), `BUser.java` (facet lines `:220-231`,
`getCurrentAuthenticatedUser` `:1212-1214`, lockout logic `:590-680`), `BUserService.java`
(`auditLoginAttempt` `:415-434`, `fwStationStarted`-equivalent `:700-719`), `BAuthenticationService.java`
(`:330-400`, `processLoginAttempt`/`auditLoginAttempt`/caller sites), `AuditInfo.java` (whole 38-line file),
`NiagaraHttpSession.java` (`:220-268`), `Console.java` (`:95-140`), `Nre.java`/`Sys.java` (targeted grep +
read), `AppRegistry.java` (`:340-368`), `WebServer.java` (niagarad, `:1390-1475`), `PermissionBridge.java`
(whole file), `PermissionManager.java` (`:95-140`), `BCertificateManagementRpc.java` (`:1060-1110` +
2 call-site greps), `HttpClientUtils.java` (`:200-240`), `BOrionSecurityAudit.java` (`:140-235`),
`NiagaraRpcServlet.java` (whole 112-line file), `NiagaraRpc.java` (whole 18-line file), `NiagaraRpcUtil.java`
(whole 361-line file, `rpc()` method `:54-196` read in full), `SecurityUtil.java` (nre, whole 375-line file),
`BJettyWebServer.java`/`BDaemonSession.java`/`OrdTargetFilter.java` targeted greps + reads at every cited
line, `PrivilegedQueuedThreadPool.java`/`PrivilegedNamedThreadFactory.java`/`PrivilegedRunnable.java` (3
whole small files), `BHxPathBar.java`/`Aes256PasswordManager.java`/`BPassword.java` targeted greps — **≈70
distinct load-bearing tokens/citations, all sourced from this session's own reads/grep output, 0 absent, 0
downgraded**. The 4 corpus-wide `Subject.*` grep counts (§54.5) were each run as standalone whole-tree
commands and their literal output (0, 0, 1, 2) is quoted verbatim, not summarized.

**Marker tally — mechanized, literal `verify-block.sh` output** (run this session from
`/home/cristian/niagara5-research`, matching [Block 41]/[Block 44]/[Block 49]'s convention):

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block54.md .
== verify-block: niagara5-block54.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 4  (adj 2)
   [CERT-live] 0
   [CERT] 59  (adj 57)
   [CERT-doc] 0
   [CERT-web] 1
   [CERT-a] 3  (adj 2)
   [INFER] 19  (adj 15)
-- ratio -- [INFER]/[CERT*] = 15/62 = 0.24
-- [CERT] file:line citation resolution --
   synth-ref  [B123] / [B167] / [B564] / [B613] / [B685] / [B689] / [B700]  (block back-references — not
              file-verifiable)
   extern  (34 citations)  — every N5 `file:line` citation, this corpus's own `organized/*/vineflower/...`
            decompiled tree, cited short-form or full-path — neither form matches this script's expected
            on-disk layout for this corpus
   resolved 0 of 34
   WARN    resolved 0 of 34 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```

The raw `[CERT-hw]` (4) / `[CERT-web]` (1) / `[CERT-a]` (3) counts are **not** load-bearing claims in this
block's body — this block cites zero hardware/web sources and only one legitimate `[CERT-a]` use (§54.3's
`corpus-nav.py find` REMIT lookup, a secondary-tool query rather than a primary read). The remaining raw
counts are the tool over-counting this self-verify section's own prose and the header-blockquote legend,
which names those marker tokens in backticks while discussing them — the same RAW-vs-ADJUSTED distortion
[Block 41] §41.9/[Block 49] §49.7 both document for a block whose own prose discusses the marker
vocabulary; the script's own `(adj ...)` column already strips the header legend and reduces `[CERT-hw]`
4→2, `[CERT-a]` 3→2, `[INFER]` 19→15, `[CERT]` 59→57. The **adjusted** `[INFER]`/`[CERT]` ratio of **0.24**
(script-reported: 15/62) is the usable number — moderate-low, consistent with a `mixed` block whose
synthesis (§54.2's `Station` startup/shutdown routing reading, §54.1's package-split rationale, §54.3's
N4-absence reading, §54.5's launch-flag-unknown caveat and its aggregate per-site verdict) is built
directly from this block's own dense `[CERT]` evidence, not free-standing speculation.

**Citation resolution.** `resolved 0 of 34` is the **expected signature for a decompiled-tree block**
(METHODOLOGY §11's explicit convention, matching [Block 41] §41.9/[Block 44] §44.x/[Block 49] §49.7's
identical signature on this same corpus): every N5 citation points into `organized/*/vineflower/...` (this
corpus's own pre-existing decompiled tree) — the script's resolver does not match either short-form
(`Console.java:121-140`) or fully-qualified (`com/tridium/sys/Console.java:121-140`) citations against
files at those paths, a citation-FORMAT gap, not a missing-source gap (every cited path was confirmed to
exist and was read directly this session; see Token check above). The 7 `synth-ref` rows are legitimately
block back-references (sibling N4 corpus + this corpus's own prior blocks), same convention every
predecessor block on this corpus uses.

**Artifacts.** This file (`/home/cristian/niagara5-research/niagara5-block54.md`) is the only artifact
written this session, per the task's explicit read-only/single-file constraint — `CATALOG.md`/`INDEX.md`/
`RESEARCH-STATE.md` were **not** regenerated or hand-edited, matching every predecessor block's identical
disclosure ([Block 27]/[Block 28]/[Block 41]/[Block 44]/[Block 49]).

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 54.7 — Child gaps

- **B54-G1** — Confirm the actual `-Djava.security.manager=<value>` JVM launch flag N5 5.0.0.28 stations
  run with (launcher script, service wrapper config, or a live `jcmd <pid> VM.system_properties` /
  `ManagementFactory.getRuntimeMXBean().getInputArguments()` probe) — this block's §54.5 could not
  determine it from decompiled source alone; the finding's practical weight is unaffected either way (zero
  `Subject.getSubject(AccessControlContext)` call sites exist regardless), but the flag itself remains
  unconfirmed. `blocked-on-source` for a decompiled-only session; `investigable` live if a station becomes
  available (would also close [Block 41]'s **B41-G4**/[Block 49]'s **B49-G1** in the same session).
- **B54-G2** — Live confirmation (`[CERT-hw]`): stand up an N5 station, perform a login, a login failure, a
  role change, and a manual `@NiagaraRpc` call, then read `$/SecurityHistory` and `$/AuditHistory` to
  confirm the §54.2 routing table matches observed records exactly (in particular, that `Startup`/`Shutdown`
  truly land only in `$/SecurityHistory` as this block's `[INFER]` predicts, and that a role-facet `Changed`
  event dual-publishes as this block's `BUser` facet finding predicts). `blocked-on-source` — no runnable
  N5 station this session, same blocker as [Block 41]'s **B41-G4**/[Block 49]'s **B49-G1**.
- **B54-G3** — Read `niagara.nre.security.SecurityAgent`/`SecurityProviderAdvice`
  (`organized/_bin-ext/nre/vineflower/com/tridium/nre/security/advice/*.java`, already decompiled in this
  corpus, not opened this session) — the ByteBuddy-agent classes [Block 3] names as the
  `SecurityManager` replacement — to confirm directly (rather than via REMIT) that they are what makes
  §54.5's `AccessController`/`Subject` sites inert, and whether the advice layer itself ever consults an
  `AccessControlContext`/`Subject` for a real decision (a possibility this block did not rule out — the
  advice classes intercept calls **before** they reach `AccessController`, a different mechanism than what
  this block traced). `investigable` — files already present in-corpus.
- **B54-G4** — This block found `BUserService.auditLoginAttempt` (public, `:415-434`) has zero callers in
  the whole decompiled corpus, while `BAuthenticationService`'s own private, differently-signed
  `auditLoginAttempt` (`:374-386`) is the live path. Determine whether the `BUserService` method is
  genuinely dead code (a candidate for [Block 44]-style deprecation/removal-risk framing), a public API
  surface for third-party module callers not present in this corpus, or a legacy path from an earlier N5
  beta superseded by `BAuthenticationService`. `investigable`.
- **B54-G5** — `BOrionSecurityAudit`'s own database-record channel (`session.insert(secRec)`, §54.2) is a
  **third**, Orion-subsystem-specific audit sink, parallel to and independent of `BSecurityAuditHistorySource`
  — not traced further here (what `OrionSession`/database it targets, retention, and whether Orion is a
  first-party N5 subsystem or a licensed/OEM layer). `investigable`.

## 54.x — Connections

- **[Block 41]** — closes **B41-G1**: §54.1–§54.2 open `SecurityAuditEvent`/`SecurityAuditor`/
  `BSecurityAuditHistorySource` end-to-end (event shape, storage, syslog dual-publish) and, specifically,
  resolve §41.3's self-acknowledged `[INFER]` hedge on `checkSecurityAudit()`'s routing into a directly-cited
  `[CERT]` per-operation table (§54.2). §54.4 also directly extends §41.7's `"niagara.context"` finding into
  the `@NiagaraRpc` path, and §54.5 extends §41.8's `BPermissions`/`getPermissions(Context)` finding by
  showing the SAME declarative-permission pattern governs `@NiagaraRpc` authorization.
- **[Block 49]** — closes **B49-G2**: §54.4 opens `NiagaraRpcServlet`/`NiagaraRpcUtil.rpc()` directly (N5
  source, not N4 REMIT), confirms the Context-injection mechanism §49.6 flagged `[INFER]`, and corrects a
  minor sourcing note (the file's actual module/package location).
- **[Block 44]** — closes **B44-G2**: §54.5 gives a per-site verdict for all 25 `AccessController`-family
  for-removal sites census-counted in §44.2 (6 modules), confirming [Block 3]'s "architecturally inert"
  reading holds at the individual-call-site level, not just as a family-wide inference — and additionally
  resolves the specific `Subject.getSubject`/`UnsupportedOperationException` hazard the task named, by
  corpus-wide census showing that deprecated overload is never called (N5 already uses `Subject.current()`/
  `Subject.callAs()` exclusively).
- **[Block 3]** — REMIT: the `SecurityManager`→ByteBuddy-`-javaagent` replacement this block's §54.5 relies
  on as the reason every `AccessController` site is inert; **B54-G3** proposes opening the advice classes
  directly rather than continuing to REMIT this finding.
- **N4 corpus (remit)** — **[B564]** (byte-identical `Auditor`/`SecurityAuditor`/`AuditEvent`/
  `SecurityAuditEvent` architecture, confirming N5's only real delta is the §54.1 package split), **[B700]**
  (live `$/SecurityHistory` 4-field schema, cross-version structural confirmation), **[B167]**/**[B689]**/
  **[B685]**/**[B123]** (N4's own `SecurityHistory`-diversion naming convention, matching §54.2 exactly),
  **[B613]** (the `@NiagaraRpc` Context-injection contract [Block 49] cited via REMIT — this block's §54.4
  independently confirms the N5-side mechanism matches).
