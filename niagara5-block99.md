# Block 99 — RPC/permission fail-open census and crypto service callers: the `BComponentRpc`-literal fail-open shape stays a corpus-wide outlier, but the SAME bug class resurfaces under a different guard in `platCrypto`'s certificate-management RPC, `BPlatCryptoManager` ships two daemon-remote operations with zero client-side permission gate, `BSimpleSigningProfile`'s CA lets a non-CA-purpose requester smuggle a `CA:TRUE` certificate, CSRF verification has no lockout of its own, and every named daemon/dashboard caller is traced

> Research closing/narrowing eight named child gaps on the "RPC/permission fail-open census and crypto
> service callers" theme: **B91-G3** ([Block 91] §91.x Child gaps — census the remaining ~53 of 57
> `permissions="unrestricted"` `@NiagaraRpc` files for the fail-open-on-null-ambient-user write shape);
> **B91-G1** ([Block 91] §91.x Child gaps — extend the null-`Context`→`canRead` census beyond the literal
> `null` keyword); **B91-G4** ([Block 91] §91.4 — whether Niagara rate-limits/locks out repeated CSRF
> verification failures); **B94-G1** ([Block 94] §94.x Child gaps — identify the actual caller of
> `BPlatCryptoManager.make(BDaemonPlatform)`); **B94-G6** ([Block 94] §94.x Child gaps — trace
> `getCertHealth`/`getPasswordStrength`'s actual caller); **B94-G7** ([Block 94] §94.x Child gaps — open
> `BSigningService.processCsr`'s own CA-signing internals and the `checkRead`-vs-`checkWrite` question for
> `generateCsr`/`getParams`); **B32-G4** ([Block 32] §32.10 — any station/platform flag relaxing mandatory
> program signing beyond the developer-license + `niagara.dev.programTestMode` path); **B15-G4** ([Block 15]
> §15.x Child gaps — open the full `niagara.security.dashboard` module for any OTHER provider surfacing
> network grants).
>
> **Parent-block gap-text confirmation.** All eight gap texts were re-read directly from their source block
> files this session (`niagara5-block91.md`, `niagara5-block94.md`, `niagara5-block32.md`,
> `niagara5-block15.md`) before investigation began; verbatim quotes are given per-section below. All eight
> match the task's paraphrase (no drift found this session).
>
> **ALREADY-COVERED check, run first.** `grep -l "<GAP-ID>"` against every existing block found each gap ID
> mentioned ONLY in its own parent block, with one exception: **B15-G4** is also named (not closed) in
> [Block 81] §81.4 ("B15-G4 ... remains separately open and is NOT addressed by this session") — confirmed
> still open before starting.
>
> Does **not** cover: **B91-G2** (whether the `TransportType.box` dispatch thread is guaranteed a bound JAAS
> `Subject` — [Block 91]'s own still-open precondition that this block's §99.1 finding shows is load-bearing
> for the TRUE systemic scope of the framework-level null-grants-all mechanism, but which this session did
> not itself trace); a live/dynamic reproduction on a running station (same blocker class as
> [Block 54]/[Block 61]/[Block 65]/[Block 81]/[Block 94]'s own **B81-G1** — no runnable N5 install this
> session); a byte-for-byte trace of every one of the 157 remaining `@NiagaraRpc` method bodies (33 were read
> in full or in the relevant excerpt this session; the rest were classified by an exhaustive two-stage
> regex/keyword census, itself preserved as scratch, not read line-by-line); the caller/callee-split or
> non-standard-wrapper-name sub-shapes B91-G1 itself named (only the variable-assignment sub-shape was
> censused to completion this session).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (`vineflower/` primary, consistent with every prior block in this series). No fresh decompilation was run
> this session — every file cited was already present in `organized/` from prior extraction sessions.
>
> Method: a Python AST-light census script (`census2.py`, brace-matched extraction of every
> `@NiagaraRpc(...)`-annotated method body whose annotation text contains `unrestricted`) enumerated all 164
> such methods across 57 files corpus-wide (`find organized -name '*.java' -path '*/vineflower/*' -exec grep`,
> the `find -exec` form per METHODOLOGY's shell-glob-under-match warning), reproducing [Block 91]'s own
> "57 files" figure exactly and refining its "~53 remaining" gap text to an exact **53 files / 157 methods**
> after excluding the 4 files [Block 91] itself read (`BComponentRpc`, `BAlarmService`, `BUser`,
> `BUserService`, 7 of the 164 methods). A second classification pass (`classify.py`/`classify2.py`/
> `classify3.py`) grep-matched each remaining method body against (a) the literal `cx != null && cx.getUser()
> != null`-guard shape [Block 91] searched for, (b) an explicit throw-on-null shape, (c) any framework
> permission-decision call (`.getPermissions(`/`.canRead(`/`.canWrite(`/`hasAdmin*`), and (d) a write-shaped
> method-name heuristic with no check-reference at all in its body — each bucket's members were then read
> directly (not inferred from the regex hit) before any claim below. Scripts preserved at
> `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b99/`
> (scratch, not archived in the corpus, reproducible from the regexes described). Markers (canonical list:
> METHODOLOGY §3): `[CERT]` local primary source (`file:line`) · `[INFER]` deduction, including every claim
> extrapolating a checked subset's result to an unchecked remainder. `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/
> `[CERT-web]`/`[CERT-a]` not used in this block.
>
> **Type:** mixed (evidence, with several `[INFER]`-flagged severity/reachability assessments per the task's
> explicit "rate any security defect with reasoning + preconditions, no working exploit" instruction).

---

## 99.1 — B91-G3 NARROWED (not closed): the literal `BComponentRpc` fail-open shape stays a corpus-wide outlier, but the same bug CLASS recurs once more under a different guard variable, and 18 of the 53 files route their gating through the framework's own null-tolerant `getPermissions(cx)` primitive instead of an ad-hoc check `[CERT]`

**Gap's own text** (`niagara5-block91.md`, "Child gaps opened"): *"A full census of the remaining ~53 of 57
'unrestricted'-permission `@NiagaraRpc` methods (only 4 files were read this session — `BComponentRpc`,
`BAlarmService`, `BUser`, `BUserService`) for the same fail-open-on-null-ambient-user shape found in
`BComponentRpc`, versus `BAlarmService`'s safer fail-closed shape or `BUserService`'s no-gate-at-all-by-design
shape. `investigable`, medium priority — this is the actual systemic-surface question §91.7 could only
partially answer."* Matches the task's paraphrase.

**Step 1 — the literal shape is confirmed rare.** Grepping `.getUser() != null`/`.getUser() == null` across
all 57 files (not just the 4 [Block 91] read) finds the exact `if (cx != null && cx.getUser() != null) { ...
check ... }` guard used by `BComponentRpc.setCategoryMask`/`getCategoryMask`/`getAppliedCategoryMask` in
**zero other files** `[CERT]` (`organized/webEditors/vineflower/com/tridium/webeditors/ux/servlets/
BComponentRpc.java:32,42,53`, whole-corpus grep, no other hit). This is a genuine, now corpus-wide-confirmed
negative — [Block 91]'s specific finding does not generalize by literal shape.

**Step 2 — the SAME bug class recurs under a different guard: `Sys.isStation()`, in `platCrypto`'s
certificate-management RPC.** `BCertificateManagementRpc` (`organized/platCrypto/vineflower/com/tridium/
platcrypto/web/BCertificateManagementRpc.java`) gates essentially every write-shaped method
(`deleteCertificate`, `generateCertificate`, `importCertificate`, `generateCSR`, `setExemption`, and others)
through two shared helpers:

```java
private static void verifyHasPermissionsOnCertManagerService(BPermissions permissions, Context context) {
   if (Sys.isStation()) {
      BCertManagerService certManagerService = (BCertManagerService)Sys.getService(BCertManagerService.TYPE);
      BUser authenticatedUser = BUser.getCurrentAuthenticatedUser();
      if (certManagerService != null && authenticatedUser != null) {
         BPermissions actualPermissions = authenticatedUser.getPermissionsFor(certManagerService);
         if (actualPermissions.has(permissions)) { return; }
         ...
      }
      throw new PermissionException(...);
   }
}
```
`[CERT]` `organized/platCrypto/vineflower/com/tridium/platcrypto/web/BCertificateManagementRpc.java:575-592`
(`verifyHasPermissionsOnCertManagerService`), `:594-605` (`verifyHasSuperUserPermissions`, same
`if (Sys.isStation())` guard). **If `Sys.isStation()` is false, the ENTIRE method body — including the
`throw`, the only enforcement point — is skipped and returns silently, and every caller (e.g.
`generateCertificate` at `:264-266`, `deleteCertificate` at `:231-238`) falls straight through to the
unconditional write.** This is structurally the identical bug class §91.7 found in `BComponentRpc` (a
condition whose FALSE branch skips the only check and lets the write proceed) — just gated on
`Sys.isStation()` instead of `cx.getUser() != null`.

**Reachability is materially narrower than `BComponentRpc`'s, which bounds the severity down.**
`Sys.isStation()` is true for the entire life of any deployed, running N5 station process — a live PANCCADIA-
style station never has this guard evaluate false. The only reachable precondition is a NON-station JVM
running this same `box`-transport RPC method — i.e. Workbench editing an OFFLINE/local database (no station
running in that JVM). In that scenario the "attacker" is the same local human already editing their own
local `.bog` file — not a remote privilege boundary crossing. **Rated LOW severity**: real bug-class instance,
zero remote-exploitability against a live deployed station, `[INFER]` (reachability reasoning; no
Workbench-offline reproduction attempted this session, no working exploit per task instruction).

**Step 3 — an inverse-but-same-class edge in `BScheduleRpc`'s shared write-gate, also LOW severity.**
`BScheduleRpc.getSourceComp()` (called by `save()` with `BPermissions.operatorWrite`) is FAIL-CLOSED in the
ordinary case but has one narrow edge:

```java
private static BComponent getSourceComp(String sourceOrd, BPermissions required, Context cx) {
   BComponent sourceComp = (BComponent)BOrd.make(sourceOrd).get(BLocalHost.INSTANCE, cx);
   BUser user = cx.getUser();
   if (user != null) {
      cx.getUser().check(sourceComp, required);
   } else if (Sys.getStation() != null) {
      throw new PermissionException("No user found");
   }
   return sourceComp;
}
```
`[CERT]` `organized/schedule/vineflower/com/tridium/schedule/ux/rpc/BScheduleRpc.java:187-197`. A null
`cx.getUser()` THROWS (fails closed) whenever `Sys.getStation() != null` — i.e. on every live station. The
only theoretical fail-open edge is `Sys.getStation() == null` (no station running in this JVM at all), the
same narrow non-station precondition as Step 2, `[INFER]` LOW severity, no reproduction attempted.

**Step 4 — the real systemic surface is a FRAMEWORK primitive, not a per-file bug, and its blast radius is
gated by the still-open B91-G2.** `BComponent.getPermissions(Context cx)` — the same method [Block 86]/[Block
91] §91.1 already cited for a different question — is:

```java
public BPermissions getPermissions(Context cx) {
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
`[CERT]` `organized/baja/vineflower/niagara/sys/BComponent.java:880-891` — **this is the documented, N4-and-N5
"no ambient identity ⇒ grant everything" contract** [Block 86] §86.1 already established, not a new defect.
What this session's census adds: **33 of the 157 remaining methods (18 of the 53 files) route their OWN
write/read gating through THIS exact framework call** (`.getPermissions(cx)`/`.canRead(`/`.canWrite(`/
`hasAdminInvoke`/`hasAdminRead`/etc.), rather than an ad-hoc `.check()` throw — e.g.
`BVideoDriverRpc.ensureAdminInvokePermissions()` (`organized/videoDriver/vineflower/com/tridium/videoDriver/
ux/util/BVideoDriverRpc.java:378-386`, gates `zoom`/`move`/`pan`), `BNiagaraVirtualComponent
.findDescendantHistories()` (`organized/niagaraVirtual/vineflower/com/tridium/nv/BNiagaraVirtualComponent.java:
1120-1121`, gates history-ID disclosure via `.hasOperatorRead()`), `BNiagaraNetworkBatchAgent
.listNiagaraNetworkBatchDeviceNames()` (`organized/provisioningNiagara/vineflower/com/tridium/
provisioningNiagara/BNiagaraNetworkBatchAgent.java:191-198`, throws `PermissionException` only if
`!hasOperatorRead()`), and `BAwsAuthRpc.getAccessKeyIds()`/`BSigningServiceRpc.getSigningProfileMap()`
(`organized/awsUtils/vineflower/com/tridium/awsUtils/auth/BAwsAuthRpc.java:36-45`,
`organized/signingService/vineflower/com/tridium/signing/BSigningServiceRpc.java:37-50`, both fail CLOSED in
OUTCOME by returning an empty list/map when `contextUser` is null — but that safe outcome is a coincidence of
each method's own `if (contextUser != null && ...)` wrapper, not of `getPermissions`/`getPermissionsFor`
itself, which would have returned a truthy grant on a null user for `BComponent`-backed targets). **All of
these are conditioned on the SAME unconfirmed precondition [Block 91] named as B91-G2**: whether the
`TransportType.box` dispatch thread ever actually runs with `cx.getUser() == null` in practice. This session
did not re-open B91-G2; it establishes that ITS answer, not a per-file audit, is what actually bounds the
systemic scope of the null-ambient-identity exposure — reframing rather than closing the "how systemic"
question.

**Step 5 — one more, DIFFERENT-shaped finding: a READ-only check gates a WRITE-shaped action.**
`BLonworksRpc.startJob()` (a LON application-download job — pushes program/firmware data to physical LON
devices, a genuine write-shaped, hardware-facing action) resolves its `netmgmtOrd` target via a shared helper
that only checks `.canRead()`:
```java
private static OrdTarget getTarget(String ord, Context cx) throws Exception {
   OrdTarget target = BOrd.make(ord).resolve(BLocalHost.INSTANCE, cx);
   if (!target.canRead()) { throw new UnresolvedException(); }
   return target;
}
```
`[CERT]` `organized/lonworks/vineflower/com/tridium/lonworks/rpc/BLonworksRpc.java:86-93` (`startJob`),
`:110-117` (`getTarget`). This is a read-gates-a-write pattern, not a null-skip — a DIFFERENT permission-model
gap shape than either §91.7's or this section's fail-open findings, `[INFER]` severity LOW-MEDIUM (an
operator-READ-only user on the LON network object could trigger a device application download, arguably
beyond what read access should authorize) — not chased further this session.

**Verdict: NARROWED, not closed.** The literal `BComponentRpc` shape is confirmed a corpus-wide outlier (Step
1). The SAME bug class recurs exactly once more, in `BCertificateManagementRpc`, under a `Sys.isStation()`
guard rather than a null-user guard, with materially lower severity due to a non-station-only reachable
precondition (Step 2), plus one inverse-shaped low-severity edge in `BScheduleRpc` (Step 3). The TRUE
systemic surface is architectural (Step 4: `BComponent.getPermissions(cx)`'s documented null-grants-all
contract, load-bearing for at least 18 of the 53 files), and its real-world blast radius is gated entirely by
the still-open **B91-G2**. One unrelated read-gates-write shape was also found (Step 5).

## 99.2 — B91-G1 NARROWED further: the variable-assignment sub-shape is now also censused to zero hits corpus-wide; the caller/callee-split and non-standard-wrapper-name sub-shapes remain untraced `[CERT]`

**Gap's own text** (`niagara5-block91.md`, "Child gaps opened"): *"Extend §91.1's corpus-wide null-Context→
canRead census beyond the LITERAL-`null`-keyword shape: a `Context cx = null;` variable passed by name, a
resolve/check pair split across a caller/callee method boundary, or a check performed through a non-standard
wrapper method name. `investigable`, low priority given the negative result across two independent regex
shapes and [Block 86]'s own prior negative."* Matches the task's paraphrase.

**Method.** `find organized -name '*.java' -path '*/vineflower/*' -exec grep -nE '(Context|BasicContext)\s+
\w+\s*=\s*null\s*;'` — the gap's own named first sub-shape — returns **41 hits corpus-wide** `[CERT]`.

**Every one of the 41 hits was read in its enclosing method; none matches the dangerous shape.** All 41 are
the ordinary Java pre-`try`-block declaration idiom (`Context cx = null;` immediately followed, before any
`.get(`/`.resolve(` call, by unconditional reassignment `cx = (Context)req.getAttribute("niagara.context");`
or `cx = this.getSessionContext();`), used so a `catch` block can reference the variable even if the
assignment itself threw — confirmed directly in `organized/history/vineflower/com/tridium/history/servlets/
QueryServlet.java:82-84,118-120` (a network-facing servlet — the single most security-relevant candidate),
`organized/niagaraDriver/vineflower/com/tridium/nd/point/BPointChannel.java:479-483`,
`organized/lonworks/vineflower/niagara/lonworks/proxy/BLonProxyExt.java:461-471` (a `Runnable` inner class's
field, set via `setContext()` before `run()` ever executes), `organized/exportTags/vineflower/com/tridium/
exporttags/BJoinAction.java:52-56` (reassigned from `ContextThread.getContext()` before use),
`organized/history/vineflower/com/tridium/history/fox/BHistoryChannel.java:969-971` (a genuinely-conditional
`BasicContext cx = null;` that stays null only when a response field is absent, then is passed as a CURSOR
constructor argument, never through a resolve→canRead/canWrite chain). **Zero of the 41 hits combine a
still-null `Context` variable with a subsequent ORD resolve AND a permission check** `[CERT]` (all 41
individually read this session).

**Verdict: NARROWED further, not closed.** This extends the negative result to the gap's own first-named
sub-shape (variable-assignment), corpus-wide. The other two named sub-shapes (a resolve/check pair split
across a caller/callee method boundary; a check performed through a non-standard wrapper method name) were
NOT traced this session — genuinely harder to census mechanically (they require call-graph tracing or a
semantic, not lexical, definition of "is a wrapper for `canRead`/`canWrite`"). Re-opened as the residual of
**B91-G1** below, low priority given three independent negative regex passes now (two from [Block 91], one
from this session) plus [Block 86]'s own prior DashboardPan-scoped negative.

## 99.3 — B91-G4 CLOSED: no CSRF-specific rate-limiting or lockout exists anywhere in the corpus; a generic, CSRF-agnostic Jetty request-rate limiter exists but ships disabled by default; Niagara's OWN daemon-login lockout mechanism proves the capability exists elsewhere and was not applied here `[CERT]`

**Gap's own text** (`niagara5-block91.md`, §91.4, restated as a named child gap): *"Whether Niagara enforces
any rate-limiting/lockout on repeated failed CSRF-token verifications — its presence would sharply raise the
practical cost (or block the attack outright); its absence would make the large-sample requirement ...
merely slow, not infeasible. Named as **B91-G4**."* Matches the task's paraphrase.

**The station-side CSRF verification path has zero state of any kind.** `CsrfUtil.verifyCsrfToken(String
sessionToken, String token)` is a pure, stateless comparison:
```java
public static boolean verifyCsrfToken(String sessionToken, String token) throws IOException, CsrfException {
   if (Objects.isNull(token) || Objects.isNull(sessionToken)) { throw new CsrfException(...); }
   else if (!sessionToken.equals(token)) { throw new CsrfException(...); }
   else { return true; }
}
```
`[CERT]` `organized/web/vineflower/niagara/web/CsrfUtil.java:36-44` (whole 45-line file read; no field, no
counter, no timestamp anywhere in the class). The servlet filter that calls it is equally stateless:
`CsrfProtectedFilter.doFilter()` catches `CsrfException`, logs it, and immediately returns HTTP 403 — no
counter increment, no delay, no IP/session tracking across requests `[CERT]` `organized/web/vineflower/
niagara/web/filters/CsrfProtectedFilter.java:43-50` (whole 65-line file read). Each failed attempt is
independent of every other; there is no state an attacker's Nth request could trip.

**A generic (CSRF-agnostic) rate limiter exists station-wide but ships disabled by default.**
`BJettyDoSFilter` wraps a standard Jetty `DoSFilter`-style per-remote-address request throttle
(`maxRequestsPerSec`, default `50`; `throttledRequests`, default `5`; `delayMs`, default `100`;
`tooManyCode`, default `429`) — but its own `enabled` property defaults to `false`:
```java
@NiagaraProperty(name = "enabled", type = "boolean", defaultValue = "false"),
@NiagaraProperty(name = "maxRequestsPerSec", type = "int", defaultValue = "50", ...),
```
`[CERT]` `organized/jetty/vineflower/com/tridium/jetty/BJettyDoSFilter.java:18-19` (property declarations,
whole class header read). This filter, if an operator opts in, would incidentally slow ANY high-frequency
traffic from one source — including the tens-of-thousands-of-requests volume [Block 91] §91.4 estimated a
CSRF-token timing attack needs — but it is off out of the box and is not CSRF-specific.

**Niagara clearly HAS the concept of failure-based lockout — just not applied to CSRF.** The platform daemon's
own login-authentication path enforces one: `AuthFailureRateLimiter`, constructed unconditionally inside the
`Authenticator` base class (`protected AuthFailureRateLimiter authFailureRateLimiter = new
AuthFailureRateLimiter();`) `[CERT]` `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/http/
Authenticator.java:36`, and consulted by `BasicAuthenticator`/`ScramAuthenticator`, which set an
`AuthenticationLocked` response header on repeated failures `[CERT]` `organized/_bin-ext/niagarad/vineflower/
com/tridium/niagarad/http/BasicAuthenticator.java:173`,
`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/http/ScramAuthenticator.java:252,403,519,534`.
This is a SEPARATE mechanism (guards password/login failures at the platform-daemon HTTP layer, not CSRF-token
mismatches at the station web layer) — its existence shows the platform's engineers have both the pattern and
the willingness to apply it elsewhere, making its absence for CSRF a scope gap in the CSRF path specifically,
not a platform-wide inability.

**One adjacent, corroborating discovery: `platCrypto`'s daemon-side `CryptoServlet` has its own,
DIFFERENT CSRF-bypass condition, gated on debug mode, not a failure counter.**
`CryptoServlet.doGet()`'s CSRF gate is `if (update && !DebugServlet.debugEnabled && !CsrfTokenUtil
.verifyCsrfToken(...))` `[CERT]` `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/
CryptoServlet.java:170`. `DebugServlet.debugEnabled` is a static, daemon-process-wide flag, default `false`,
settable only via an admin-authenticated (`DaemonAuthUtil.authAdmin`) request that itself still requires a
valid CSRF token while `debugEnabled` is still false `[CERT]` `organized/_bin-ext/niagarad/vineflower/com/
tridium/niagarad/servlet/DebugServlet.java:17-41,73-90` (whole 95-line file read). So this is NOT a
remotely-triggerable bypass on its own — but it means an administrator who enables daemon debug mode for
support/troubleshooting silently and undocumentedly ALSO disables CSRF enforcement for every one of
`CryptoServlet`'s state-changing actions (`savekeystore`/`deleteentry`/`generatecsr`/`generatecert`/
`resetuserkeystore`/`deleteexemption`/`saveexemptions`) until debug mode is turned back off — an unrelated,
undocumented side-effect coupling, `[INFER]` LOW severity given the admin-auth precondition, named as a
residual note rather than a full finding (not what B91-G4 asked, but discovered investigating it).

**Verdict: CLOSED.** Niagara does not rate-limit or lock out repeated CSRF verification failures anywhere in
the corpus (`[CERT]`, both classes read whole). A generic per-IP request throttle exists but is off by
default (`[CERT]`). The platform's own login-lockout mechanism (`[CERT]`) demonstrates the capability exists
elsewhere in the same codebase, reinforcing that CSRF's exposure is a deliberate/overlooked scope gap rather
than a platform-wide constraint — directly answering [Block 91] §91.4's severity reasoning: the large-sample
timing-attack requirement is confirmed merely slow, not infeasible, with no built-in backstop.

## 99.4 — B94-G1 CLOSED: `BPlatCryptoManager.make(BDaemonPlatform)`'s actual callers are `provisioningNiagara`/`platDaemon`'s install/backup/deploy commissioning-tooling classes, using it exclusively for remote-platform TLS-chain validation and a read-only trust-store inventory snapshot `[CERT]`

**Gap's own text** (`niagara5-block94.md`, "Child gaps opened"): *"Identify the actual caller of
`BPlatCryptoManager.make(BDaemonPlatform)` (the concrete `BDaemonPlatform`/commissioning-tooling class that
constructs the daemon-side crypto manager) — §94.1 confirms `BCertManagerService` is NOT that caller, but the
true caller was not itself opened this session."* Matches the task's paraphrase.

**Six call sites found, corpus-wide, all commissioning tooling** `[CERT]` (`find organized -name '*.java'
-path '*/vineflower/*' -exec grep -n 'BPlatCryptoManager\.make('`, exhaustive):

1. `organized/platDaemon/vineflower/com/tridium/platDaemon/command/BModuleInstallCommand.java:118`
2. `organized/platDaemon/vineflower/com/tridium/platDaemon/command/BBackupInstallCommand.java:272`
3. `organized/platDaemon/vineflower/com/tridium/platDaemon/command/BDistInstallCommand.java:213`
4. `organized/platDaemon/vineflower/com/tridium/platDaemon/ui/distinstall/DependenciesStep.java:70`
5. `organized/provisioningNiagara/vineflower/com/tridium/provisioningNiagara/template/
   ProvisioningBulkDeployUtil.java:433`
6. `organized/provisioningNiagara/vineflower/com/tridium/provisioningNiagara/software/
   BSoftwareStationExt.java:149`

**Sites 1-5 all wrap the manager in the SAME idiom**: `CertificateChainValidator.make(BPlatCryptoManager.make
(platform/targetPlatform))` — used to validate the TARGET remote platform's TLS/identity certificate chain
BEFORE a privileged provisioning action (module install, backup install, distribution install, a dependency-
check wizard step, or a bulk multi-station deploy) proceeds against it `[CERT]` (each site read in its
immediate calling context this session).

**Site 6 is a different, read-only use**: `BSoftwareStationExt` (the Niagara Software Manager's remote-station
extension) reads `manager.getUserTrustStore().getCertificateEntries()` to populate a `platformTrustStoreSnapshot`
BVector for display in the Workbench Software Manager UI — a trust-store INVENTORY snapshot, not a
chain-validation call `[CERT]` `organized/provisioningNiagara/vineflower/com/tridium/provisioningNiagara/
software/BSoftwareStationExt.java:146-156`.

**Verdict: CLOSED.** The concrete caller class family is `platDaemon`'s install-command classes and
`provisioningNiagara`'s bulk-deploy/software-manager classes — exactly the "commissioning tooling" [Block 94]
itself predicted but did not open. Both of the two distinct usages (TLS-chain validation gating a privileged
install/deploy, and a read-only trust-store inventory snapshot) are traced with direct citations; neither
reaches the daemon crypto protocol's write-side keystore-CRUD actions directly.

## 99.5 — B94-G6 CLOSED: `getCertHealth`/`getPasswordStrength` ARE modeled by dedicated daemon-message classes — [Block 94] searched the wrong package (`platcrypto/daemon/messages/` instead of the base `platform` module's own `platform/daemon/message/`); callers are `BDaemonSession`'s convenience wrapper, the Workbench Platform Administration UI, and — directly connecting to B15-G4 — a Security Dashboard provider agent `[CERT]`

**Gap's own text** (`niagara5-block94.md`, "Child gaps opened"): *"Trace `getCertHealth`/`getPasswordStrength`'s
actual caller — no class under `platcrypto/daemon/messages/` targets either `CryptoServlet` action, suggesting
a direct browser/JS caller of the `crypto` servlet unmodeled by the traced Java message classes (§94.1)."*
Matches the task's paraphrase.

**[Block 94]'s premise was a scoping miss, not a genuine absence.** The message classes DO exist, one package
over from where [Block 94] looked:
```java
public class CertHealthMessage extends DaemonMessage {
   public String getMessageString() { return "crypto?action=getCertHealth"; }
}
public class GetPasswordStrengthMessage extends DaemonMessage {
   public String getMessageString() { return "crypto?action=getPasswordStrength"; }
}
```
`[CERT]` `organized/platform/vineflower/com/tridium/platform/daemon/message/CertHealthMessage.java:1-8`,
`organized/platform/vineflower/com/tridium/platform/daemon/message/GetPasswordStrengthMessage.java:1-8` — both
in `com.tridium.platform.daemon.message` (the base `platform` module), NOT `com.tridium.platcrypto.daemon
.messages` ([Block 94]'s searched package) — matching `CryptoServlet`'s own `getCertHealth`/`getPasswordStrength`
action strings exactly (§94.1, `authenticate()`'s special-cased user-auth-only actions).

**Three callers found, corpus-wide** `[CERT]` (`find organized -name '*.java' -exec grep -n 'new
CertHealthMessage(\|new GetPasswordStrengthMessage('`, exhaustive):
1. `organized/platform/vineflower/com/tridium/platform/daemon/BDaemonSession.java:2882` — `BDaemonSession`'s
   own convenience wrapper method, the general-purpose entry point any daemon-session-holding caller can use.
2. `organized/platDaemon/vineflower/com/tridium/platDaemon/ui/config/BPlatformAdministration.java:783` — the
   Workbench "Platform Administration" view, surfacing certificate health status in its UI panel.
3. `organized/platform/vineflower/com/tridium/platform/BSystemPlatformServiceSecurityDashboardProviderAgent
   .java:517` — a **Security Dashboard provider agent**, directly relevant to §99.8/B15-G4 below: the
   dashboard DOES surface certificate-health status (via this exact daemon message), just not the
   network-connection-grant view B15-G4 asks about.

**Verdict: CLOSED.** Both actions are modeled by dedicated message classes (in a sibling package to where
[Block 94] looked), and all three callers are traced with direct citations — a convenience session wrapper, a
Workbench admin UI, and a Security Dashboard provider.

## 99.6 — B94-G7 ADVANCED (checkRead-vs-checkWrite closed; CA-signing internals opened with a genuine security-relevant finding): `generateCSR`'s read-only client-side gate is a narrow, real inconsistency; two NEWER `BPlatCryptoManager` operations (self-signed cert generation, key-store reset) have ZERO client-side permission check at all; and `BSimpleSigningProfile`'s extension copy-through logic lets a non-CA-purpose, operator-approved requester obtain a `CA:TRUE` certificate `[CERT]`+`[INFER]`

**Gap's own text** (`niagara5-block94.md`, "Child gaps opened"): *"Open `BSigningService.processCsr`'s own
CA-signing internals (the actual CSR→certificate cryptographic step both §94.1's crypto-manager cluster and
§94.2's Fox channel call as a boundary but neither this block nor [Block 12] opened), and confirm why
`generateCsr`/`getParams` authorize via `KeyStorePermission.checkRead` rather than `checkWrite` despite being
CSRF-gated, state-changing actions in `CryptoServlet`'s own `update=true` set — a possible read/write
permission-model inconsistency spotted in passing (§94.1)."* Matches the task's paraphrase.

### (a) `checkRead`-vs-`checkWrite`: confirmed real, narrow, and bounded by an existing manifest-grant requirement

`BPlatCryptoManager.generateCSR(String alias, String passwd)` is the CLIENT-JVM-side method backing the
daemon's `generatecsr` action:
```java
public NPKCS10CertificationRequest generateCSR(String alias, String passwd) throws Exception {
   KeyStorePermission.checkRead(CryptoStoreId.USER_KEY_STORE.getValue());
   XElem csr = this.send(new GenerateCsrMessage(...));
   ...
}
```
`[CERT]` `organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatCryptoManager.java:164-172`. This
confirms §94.1's spotted inconsistency: `CryptoServlet`'s OWN dispatcher classifies `generatecsr` as
`update = true` (CSRF-gated, state-changing, `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/
servlet/CryptoServlet.java:159-168`), while the client-JVM module-manifest gate for the SAME action only
requires READ permission on the user key store. **Practical effect**: a module holding only a
`KeyStorePermission("userKeyStore", "read")` manifest grant — intended for modules that only need to DISPLAY
existing certs — can also trigger CSR generation, a private-key-proof-of-possession operation whose output
(the CSR) discloses the public key and identity fields signed by the existing private key. Bounded: still
requires SOME declared `KeyStorePermission` grant (not reachable by a module with none at all) and does not
itself expose the private key bytes. `[INFER]` LOW-MEDIUM severity: a genuine, if narrow, permission-model
inconsistency, not a bypass of the gate entirely.

### (b) NEW finding: two of `BPlatCryptoManager`'s daemon-remote operations have NO client-side permission check whatsoever

Reading every method in `BPlatCryptoManager.java` for its own `KeyStorePermission` call (or lack of one):
```java
@Deprecated
public int generateSelfSignedCert(NCertificateParameters certParams) throws Exception {
   KeyStorePermission.checkWrite(CryptoStoreId.USER_KEY_STORE.getValue());   // present
   ...
}

public int generateSelfSignedCert(NX509CertificateBuilder builder, NKeyPairGenerator generator, SecretChars newPassword) throws Exception {
   if (this.getDaemonSession().getHostProperties().isMinNiagaraVersion(...)) {
      XElem request = this.send(new GenerateCertificateBuilderMessage(...));   // NO checkWrite/checkRead call
      return request != null ? request.geti("requestId", -1) : -1;
   } else { throw new UnsupportedOperationException(...); }
}

public int resetUserKeyStore() throws Exception {
   if (this.getDaemonSession().getHostProperties().isMinNiagaraVersion(...)) {
      ResetUserKeyStoreMessage msg = new ResetUserKeyStoreMessage();
      XElem request = this.send(msg);                                        // NO checkWrite/checkRead call
      return request != null ? request.geti("requestId", -1) : -1;
   } else { throw new UnsupportedOperationException(...); }
}
```
`[CERT]` `organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatCryptoManager.java:122-131`
(deprecated overload, HAS `checkWrite`), `:132-146` (modern, non-deprecated overload — the one actually used
by builder-based cert generation — has NO permission call anywhere in its body), `:149-157`
(`resetUserKeyStore` — a DESTRUCTIVE, whole-key-store-wiping operation — also has NO permission call). Their
shared transport, `BPlatCryptoBase.send(CryptoServletMessage)`, is confirmed to perform no check of its own
either — a pure HTTP-transport wrapper `[CERT]` `organized/platCrypto/vineflower/com/tridium/platcrypto/
daemon/BPlatCryptoBase.java:39-51` (whole 63-line file read). **Both un-gated methods are the newer
`ADVANCED_CERT_GEN_VERSION`-tier operations**, while the OLDER, deprecated sibling and every method in the
companion `BPlatKeyStore` class (`getKey`/`setKeyEntry`/`deleteEntry`/`setCertificateEntry`/`save`, all
`[CERT]`-checked in §94.1) consistently call `checkRead`/`checkWrite` — this reads as a permission-check
regression introduced when the newer builder-based/reset operations were added, not an intentional design
choice.

**Severity and preconditions, `[INFER]`, no working exploit attempted.** The REAL wire-level privilege
boundary — per §94.1's own analysis, re-confirmed here, not re-derived — is `CryptoServlet.authenticate()`'s
daemon-side `requireAdmin=true` host-admin HTTP auth check, enforced independently of anything in the client
JVM. The missing client-side check therefore matters for exactly one scenario: a SAME-JVM caller (e.g. a
malicious or compromised module loaded into a Workbench/Supervisor process) that does NOT itself hold a
`KeyStorePermission` grant, but which shares that JVM with an operator's ALREADY-AUTHENTICATED admin
platform-daemon session (opened for some legitimate purpose, e.g. routine platform administration) — that
caller could invoke `generateSelfSignedCert(builder, ...)`/`resetUserKeyStore()` directly and ride the
existing admin session to (respectively) generate a new self-signed certificate on, or WIPE the user key
store of, the REMOTE platform — bypassing the in-process module-isolation model every other daemon-remote
crypto operation enforces. **Rated MEDIUM severity, conditional**: real, unauthenticated-at-the-client-JVM-
layer privilege bypass for an already-admin-connected JVM, but requires that precondition (an established
admin daemon session already open in the SAME process as the malicious code) rather than being reachable by
an arbitrary remote or unauthenticated party.

### (c) CA-signing internals, opened for the first time in either corpus, with a genuine issuance-policy defect

`BSigningService.processCsr()` → `processDequeuedCsr()` (async, dequeued from `SigningRequestWorker`) calls
`profile.validateCsr(csr); profile.signCertificate(csr, requesterId);` on the concrete `BAbstractSigningProfile`
implementation `[CERT]` `organized/signingService/vineflower/com/tridium/signing/BSigningService.java:154-191`.
The first-party concrete implementation, `BSimpleSigningProfile`:

- **`doSignCertificate`** retrieves the CA's own private key/cert via `SecurityUtil.doPrivileged(this::
  retrieveCaCertificate)` (privileged local-keystore access, protecting the CA key from ordinary
  module-permission restriction) and calls `CertUtils.signCertificate(csr, caCert, parameters, true)` — a
  genuine local RSA/EC signing operation, not a further-delegated call `[CERT]`
  `organized/signingService/vineflower/com/tridium/signing/profile/BSimpleSigningProfile.java:221-241`.
- **Extension copy-through is selective, per-extension-type, EXCEPT for one case.** `getSigningParameters()`
  only copies a CSR-supplied `KeyUsage`/`ExtendedKeyUsage`/`BasicConstraints` extension into the issued
  certificate if the matching `isXValid()` check passes — `[CERT]` `:250-266`. For `KeyUsage`/
  `ExtendedKeyUsage`, the check REQUIRES a purpose-specific set of flags to be PRESENT (`checkKeyUsageExtension
  (ext, requiredFlags)`/`checkExtendedKeyUsageExtension(ext, requiredPurposeIds)`, both defined as "every
  required flag/purpose must be present," `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/crypto/
  core/cert/CertUtils.java:475-493`) — it does **not** check that OTHER, unrequested flags are ABSENT.
- **`isBasicConstraintsExtensionValid()` only validates when the PROFILE's own `keyPurpose` is `CA_CERT`; for
  every other purpose it is unconditionally `true`:**
  ```java
  private boolean isBasicConstraintsExtensionValid(NBasicConstraints basicConstraintsExtension) {
     return this.getKeyPurpose().toKeyPurpose() == KeyPurpose.CA_CERT
        ? CertUtils.checkBasicConstraintsExtension(basicConstraintsExtension)
        : true;
  }
  ```
  `[CERT]` `organized/signingService/vineflower/com/tridium/signing/profile/BSimpleSigningProfile.java:298-300`,
  where `checkBasicConstraintsExtension` for a genuine CA_CERT profile requires `basicConstraintsExtension
  .isCA()` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/CertUtils.java:495-497`.
  **For a `SERVER_CERT`/`CLIENT_CERT`/`CODE_SIGNING_CERT`-purpose profile, a CSR-supplied `BasicConstraints`
  extension is copied into the issued certificate UNCONDITIONALLY — including one declaring `CA:TRUE`.**
  Combined with `KeyUsage`'s "required-present, not forbidden-absent" semantics (§ above), a CSR could also
  carry `KeyUsage = {keyCertSign(4), cRLSign(2), ...the profile's own required flags...}` and have ALL of it
  accepted, since `checkKeyUsageExtension` for e.g. `SERVER_CERT` only requires `{digitalSignature(128),
  keyEncipherment(32)}` present — `keyCertSign`/`cRLSign` are simply extra bits it never inspects. Bit-to-name
  mapping confirmed directly in-file: `128`→`digitalSignature`, `32`→`keyEncipherment`, `4`→`keyCertSign`,
  `2`→`cRLSign` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/ext/NKeyUsage.java:
  33-58` (`getFlags()`, whole bit-mapping block read).

**Severity and preconditions, `[INFER]`, no working exploit attempted.** A requester who has already completed
[Block 94] §94.2's onboarding + operator-approval steps (a HUMAN must click "Approve" on that specific
requester's onboarding record before any CSR is even accepted — this is NOT reachable anonymously or without
a prior human-authorization step) — but who was approved for a **non-CA** profile (SERVER_CERT/CLIENT_CERT/
CODE_SIGNING_CERT, the ordinary enrollment case for a fleet of managed Niagara devices/services) — could embed
a `BasicConstraints{CA:TRUE}` + `KeyUsage{keyCertSign,cRLSign,...}` extension pair in their submitted CSR and
receive back a certificate carrying full subordinate-CA signing capability, chained to the SAME CA the
signing service issues from, when they were only ever approved for an end-entity certificate. **Rated
MEDIUM-HIGH, conditional**: the code-level defect (issuance policy not enforcing "no CA capability outside a
CA-purpose profile") is confirmed and unconditional once the onboarding/approval precondition is met; full
exploit impact additionally depends on whether ANY downstream consumer of certificates issued by this CA
performs CA-chain/path validation on such an end-entity certificate (rather than simple leaf-certificate
pinning or hostname-only validation) — this was NOT traced this session (no signingService-issued-certificate
consumer/validator was opened), so the FULL blast radius remains `[INFER]`, named as a child gap below.

**Verdict: ADVANCED.** (a) closes the `checkRead`-vs-`checkWrite` question precisely — real, narrow,
manifest-grant-bounded. (b) is a NEW, unasked-for finding: two newer daemon-remote crypto operations have zero
client-side permission gate at all. (c) opens the CA-signing internals in full for the first time and finds a
genuine issuance-policy gap (non-CA-purpose profiles do not reject a CSR-requested CA capability) — significant
enough that this session rates it explicitly rather than leaving it as a pure trace, per the task's own
instruction, while being precise that downstream-consumer exploitability is unconfirmed.

> **Independent verification (orchestrator, same session — one scoped assumption challenge for a
> high-consequence premise).** Re-read without the writer's notes: `BSimpleSigningProfile.getSigningParameters`
> copies each CSR extension into the signing parameters, filtering `NBasicConstraints` through
> `isBasicConstraintsExtensionValid`, which returns `true` for every purpose except `CA_CERT`
> (`organized/signingService/vineflower/com/tridium/signing/profile/BSimpleSigningProfile.java:250-263,298-299`).
> `CertUtils.checkKeyUsageExtension` only requires the listed bits to be present, so extra bits such as
> `keyCertSign` pass (`organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/CertUtils.java:475-483`).
> The profile signs with `preferParams=true`, and `addKeyPurposeExtensions(..., preferExisting=true)` keeps an
> existing `KeyUsage` and never touches `BasicConstraints` outside `CA_CERT` (`CertUtils.java:283-284` and the
> `addKeyPurposeExtensions` body). The copy-through premise holds `[CERT]`. Exploitability still depends on an
> operator approving the requester and on downstream CA-chain validation (B99-G1).

## 99.7 — B32-G4 CLOSED: no additional flag relaxing mandatory program signing exists anywhere in the corpus; the adjacent, broader `niagara.permissions.disable` dev-mode kill switch is architecturally SEPARATE from `BCode`'s own signature-verification gate and does not reach it `[CERT]`

**Gap's own text** (`niagara5-block32.md`, "Open questions / child gaps"): *"Search for any station-level or
platform-level flag that disables/relaxes the §32.4 mandatory signature-verification gate outside the
developer-license + `niagara.dev.programTestMode` system-property path found in `BCode.java` — not found in
`program.jar`; may exist in a platform/security module not opened this session."* Matches the task's
paraphrase.

**Direct search finds no other file referencing the mechanism at all.** `find organized -name '*.java' -exec
grep -lniE 'programTestMode|IS_DEVELOPER_LICENSED|handleVerificationFailed|program\.certNotTrusted|
program\.failedVerification'` returns exactly TWO files corpus-wide: `program/vineflower/com/tridium/program/
BCode.java` (the gate itself, already read by [Block 32]) and `program/vineflower/com/tridium/program/ui/
signing/BCertificateNotTrustedDialog.java` (a Workbench UI dialog that only DISPLAYS the exception, does not
bypass it) `[CERT]`. **`SigningUtil.verifySignature()` itself — the actual cryptographic verification routine
[Block 32] §32.4's gate calls — contains zero `System.getProperty`/`Boolean.getBoolean` calls anywhere in the
file** `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/SigningUtil.java` (grepped
whole file for property-access calls, 2 matches both unrelated to verification: `java.version`/`java.vendor`
diagnostic logging at `:445-446`). There is no OTHER property-gated bypass anywhere in the actual verification
call chain.

**The broader `niagara.permissions.disable` dev-mode flag was traced to full completion and confirmed
NOT to reach `BCode` at all.** `com.tridium.sys.Nre.checkDisablePermissionChecks()`:
```java
private static void checkDisablePermissionChecks() {
   boolean disablePermissionChecks = Boolean.getBoolean("niagara.permissions.disable");
   if (disablePermissionChecks) {
      try {
         licenseManager.checkFeature("tridium", "developer");
         String logFileName = PermissionManager.disablePermissionChecks();
         ...
      } catch (FeatureNotLicensedException ignore) { ... }
   }
}
```
`[CERT]` `organized/baja/vineflower/com/tridium/sys/Nre.java:929-941`. `PermissionManager
.disablePermissionChecks()` sets `PermissionUtil.permissionChecksDisabled = true` (after its OWN
`NiagaraBasicPermission.DISABLE_PERMISSION_CHECKS_PERMISSION` check) `[CERT]` `organized/_bin-ext/nre/
vineflower/com/tridium/nre/security/permissions/PermissionManager.java:141-144`. Reading `checkPermission()`'s
full body confirms the flag's actual effect: a `PermissionException` caught inside `checkPermission()` is
audited/logged and then, in a `finally` block, **re-thrown only if `!PermissionUtil.permissionChecksDisabled`**
`[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/PermissionManager.java:
51-129` (whole method read) — i.e. this flag is a GLOBAL kill switch for every `NiagaraPermission`-family
check corpus-wide (including `KeyStorePermission.checkRead`/`checkWrite`, used throughout §99.6's
`platCrypto` findings). **But `BCode.java`'s own signature-verification gate never calls `PermissionManager`
or `PermissionUtil` anywhere** (confirmed by [Block 32]'s own full read of `BCode.java:213-311,607-621`,
re-confirmed by this session's grep above finding no `PermissionManager`/`PermissionUtil` reference in
`program.jar` at all) — the two mechanisms are architecturally independent, each gated by the SAME `developer`
license feature but keyed to two DIFFERENT, non-overlapping system properties
(`niagara.dev.programTestMode` for `BCode`, `niagara.permissions.disable` for `PermissionManager`).

**Verdict: CLOSED.** No additional flag relaxes mandatory program-object signature verification anywhere in
the corpus, including the one broader, adjacent dev-mode kill switch this session specifically traced to its
full mechanics. Both of the corpus's TWO signature/permission-bypass escape hatches (`BCode`'s
`programTestMode`, `PermissionManager`'s `permissions.disable`) independently require the SAME `developer`
license feature and are confirmed, by direct code reading rather than absence-of-reference alone, to be
non-overlapping mechanisms.

## 99.8 — B15-G4 CLOSED: a corpus-wide census of the full `niagara.security.dashboard` provider population (found by BOTH name-pattern AND direct interface-implementation search) finds no provider surfacing a live network-connection or NiagaraPermission-grant view; every "network"-adjacent provider is a TLS/protocol/config-hygiene advisory instead `[CERT]`

**Gap's own text** (`niagara5-block15.md`, "Child gaps opened"): *"Open the broader `niagara.security.dashboard`
module itself (only `httpClient.jar`'s `BHttpClientSecurityDashboardAgent` AGENT into it was read this
session) to confirm no OTHER dashboard provider anywhere in the 247-module census surfaces a live 'which
modules have opened outbound network connections' view — i.e. rule out that the missing PolicySpy-equivalent
(§15.5) exists under an unrelated module name not yet identified."* Matches the task's paraphrase.

**Census method, two independent passes for completeness.** Pass 1: `find organized -iname
"*SecurityDashboard*" -name "*.java"` — **34 classes** across 24 modules (`backup`, `bacnet`, `baja`, `email`,
`fox`, `httpClient`, `ldap`, `nSnmp`, `nss`, `opcUaClient/Server`, `orientSystemDb`, `platform`, `rdb`, `saml`,
`signingService`, `tunnel`, `web`, plus the `niagara.security.dashboard` interface package itself). Pass 2:
`find organized -name '*.java' -exec grep -l 'implements.*BISecurityDashboardProviderAgent\|implements.*
BISecurityDashboardItemProvider\|, BISecurityDashboardProviderAgent\|, BISecurityDashboardItemProvider'` —
catches providers whose CLASS NAME doesn't literally contain "SecurityDashboard": adds
`BAzureMqttSasSecurityAgent`/`BGcpAuthenticator` (mqtt), `BScDashboardProvider`/`BScSchemeSecurityDashboardItemProvider`
(bacnet Secure Connect), `BLdapSchemeSecurityItemProvider`, `BSnmpNetwork` (SNMP network object itself), `BOpcUaDevice`/
`BOpcUaServer`, `BOrientSystemDbDashboardProvider`, `BSecurityPropertyDashboardItemProviderAgent` (nss). Both
lists' union was grepped for `network|outbound|socket|NETWORK_COMMUNICATION|remoteHost|remoteAddr|egress`;
every match was read in full.

**Every network-adjacent match is a TLS/protocol/config-hygiene advisory, never a connection/grant view.**
`BRdbmsSecurityDashboardProviderAgent.getSecurityDashboardItems()` reports whether each configured RDBMS
connection uses TLS, which TLS protocol version, and whether it runs as a non-privileged account `[CERT]`
`organized/rdb/vineflower/com/tridium/rdb/BRdbmsSecurityDashboardProviderAgent.java:34-43,108-163` (lexicon
keys `securityDashboard.rdbmsNetwork.tls.*`/`.tlsProtocol.*`/`.nonPrivilegedConnection.*`). `BSnmpNetwork
.getSecurityDashboardItems()` warns only if the read or read-write SNMP community string is still the default
`"public"` `[CERT]` `organized/nSnmp/vineflower/com/tridium/nSnmp/BSnmpNetwork.java:710-729`.
`BBacnetSecurityDashboardProvider` reports device-comm-control and reinit-device configuration status
`[CERT]` `organized/bacnet/vineflower/com/tridium/bacnet/BBacnetSecurityDashboardProvider.java:22-40`.
`BFoxServiceSecurityDashboardProviderAgent` reports Fox-over-websocket enablement status `[CERT]`
`organized/fox/vineflower/com/tridium/fox/dashboard/BFoxServiceSecurityDashboardProviderAgent.java:161`.
`BSecurityPropertyDashboardItemProviderAgent` (the `nss` module's own generic provider) checks whether
specific `java.security` JVM properties (`ocsp.enable`, `jdk.tls.server.defaultDHEParameters`,
`jdk.crypto.disabledAlgorithms`, etc.) still match their JDK-shipped defaults `[CERT]`
`organized/nss/vineflower/com/tridium/nss/dashboard/BSecurityPropertyDashboardItemProviderAgent.java:35-60`.
[Block 15]'s own `BHttpClientSecurityDashboardAgent` (already read, REMIT) fits the same pattern —
TLS-cipher/protocol posture, not a connection-grant view. **None of the 34+ providers exposes a per-module,
per-connection host/port record — the schema itself (`SecurityDashboardConstants`) has no such field, only a
generic sections→subsections→(status/summary/description/lexiconKey) item shape** `[CERT]`
`organized/baja/vineflower/niagara/security/dashboard/SecurityDashboardConstants.java:1-47` (whole 47-line
file read) — confirming the framework itself imposes no fixed taxonomy that would either mandate or preclude
a network-grant category; its absence is a genuine absence of ANY provider choosing to report one, not a
schema limitation this session found a workaround for.

**Verdict: CLOSED.** This reinforces, rather than merely narrows, [Block 15] §15.6's original finding: N5
5.0.0.28 has no PolicySpy-equivalent live network-connection/grant view anywhere in its Security Dashboard
provider population, now confirmed against the FULL provider census (34 classes, 24 modules, found by two
independent search strategies) rather than the single `httpClient.jar` agent [Block 15] itself read. The
`niagara.security.dashboard` module DOES surface certificate health (§99.5's `BSystemPlatformServiceSecurityDashboardProviderAgent`),
module-signature status, password strength, and multiple TLS/protocol/config-hygiene advisories — but never a
"which module opened a connection to what host" view.

## 99.x — Corrections to earlier blocks

None found this session — no §14-shaped contradiction between this block's findings and any earlier block's
stated claim; §99.5's "wrong package searched" note for [Block 94] and §99.1's "literal-shape confirmed rare
but bug-class recurs" note for [Block 91] are both extensions/refinements of the parent's own OWN framing
(each parent block explicitly named its own scope limit as the residual gap this session closes), not
corrections of a stated verdict.

## 99.x — Connections

- **[Block 91]** — §99.1 NARROWS **B91-G3** (literal shape confirmed rare corpus-wide; same bug class found
  once more under a different guard, lower severity; the true systemic scope is reframed onto the still-open
  **B91-G2**); §99.2 further NARROWS **B91-G1** (one more sub-shape censused to zero); §99.3 CLOSES **B91-G4**
  (no CSRF lockout anywhere; a generic-but-disabled Jetty rate limiter and the daemon's own login-lockout
  mechanism both exist as comparison points). Reuses [Block 86]/[Block 91] §91.1's `BComponent.getPermissions`
  null-grants-all citation as load-bearing evidence in §99.1 Step 4, rather than re-deriving it.
- **[Block 94]** — §99.4 CLOSES **B94-G1** (six commissioning-tooling call sites); §99.5 CLOSES **B94-G6**
  (message classes exist one package over from where [Block 94] searched; three callers traced, one of which
  is the §99.8 Security Dashboard connection); §99.6 CLOSES the `checkRead`-vs-`checkWrite` half of **B94-G7**
  and ADVANCES its CA-signing-internals half with a new, rated finding (two un-gated `BPlatCryptoManager`
  operations; `BSimpleSigningProfile`'s non-CA-purpose `BasicConstraints` bypass). Reuses §94.1's "two
  independently-stacked permission layers" framing as the baseline §99.6(b) shows one specific exception to.
- **[Block 32]** — §99.7 CLOSES **B32-G4**, tracing the adjacent `niagara.permissions.disable` mechanism
  ([Block 15] §15.6/[Block 8] §8.6's own citation, REMIT for its EXISTENCE) to its full mechanics for the
  first time and confirming it does not reach `BCode`.
- **[Block 15]/[Block 81]** — §99.8 CLOSES **B15-G4**, extending [Block 15] §15.6's single-agent
  (`httpClient.jar`) reading to the full 34-class, 24-module provider population; [Block 81] §81.4's own
  "B15-G4 remains separately open" note (this session's ALREADY-COVERED check target) is now resolved.
- **Cross-theme**: §99.1's `BCertificateManagementRpc`/§99.6's `BPlatCryptoManager` findings both live in the
  `platCrypto` module family §94.1/§94.2 already mapped — this session's two independent fail-open/no-gate
  findings sit at DIFFERENT layers of that same module (the web-facing station RPC vs. the daemon-remote
  client API), neither previously opened by [Block 94] itself.

## 99.x — Child gaps opened

- **B99-G1** (medium priority) — Confirm live (same blocker class as **B91-G2**/B81-G1/B54-G1/B54-G2/B61-G1/
  B65-G1/B94-G2/B94-G3) whether any downstream Niagara consumer of a `signingService`-issued end-entity
  certificate (§99.6c) performs CA-chain/path validation (as opposed to leaf-pinning/hostname-only
  validation) — this determines whether the `BasicConstraints{CA:TRUE}`-on-a-non-CA-profile issuance defect
  is exploitable beyond the code-level policy gap itself. `investigable` — would need to open every
  `BISigningTransport`/certificate-consumer implementation and trace its validation logic.
- **B99-G2** (low priority) — Reproduce the `Sys.isStation()`-false / `Sys.getStation()`-null fail-open edges
  named in §99.1 Steps 2-3 live in a Workbench-offline-database session, to move their `[INFER]` reachability
  reasoning to `[CERT-hw]`.
- **B99-G3** (low priority) — Trace whether `BPlatCryptoManager.generateSelfSignedCert(NX509CertificateBuilder,
  ...)`/`resetUserKeyStore()` (§99.6b's un-gated methods) are reachable from ANY first-party Workbench dialog
  (`BSelfSignedDialog`, `platCrypto/ui/`) without an already-established admin daemon session, which would
  raise §99.6(b)'s severity rating beyond "requires a pre-existing admin session in the same JVM."
- **B99-G4** (low priority, same shape as **B91-G1**'s own residual) — Trace the caller/callee-split and
  non-standard-wrapper-name sub-shapes of the null-Context census that §99.2 did not attempt (requires
  call-graph tracing or a semantic definition of "acts as a permission-check wrapper," neither mechanical).
- **B99-G5** (low priority) — Confirm whether `BLonworksRpc.startJob()`'s read-gates-a-write shape (§99.1 Step
  5) recurs elsewhere in the corpus beyond this one LON-specific instance — not searched this session beyond
  the single file found.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 57 files / 164 methods total match `@NiagaraRpc(...unrestricted...)` corpus-wide; 53 files / 157 methods remain after excluding [Block 91]'s 4 | [CERT] | `census2.py` run this session, `census_full.json` |
| 2 | The literal `cx != null && cx.getUser() != null` guard exists ONLY in `BComponentRpc` among all 57 files | [CERT] | whole-corpus `grep -n 'getUser()'` over the 57-file list, this session |
| 3 | `BCertificateManagementRpc`'s two permission helpers no-op when `Sys.isStation()` is false | [CERT] | `organized/platCrypto/vineflower/com/tridium/platcrypto/web/BCertificateManagementRpc.java:575-605` |
| 4 | `BComponent.getPermissions(cx)` returns `BPermissions.all` when `cx==null` or `cx.getUser()==null` | [CERT] | `organized/baja/vineflower/niagara/sys/BComponent.java:880-891` |
| 5 | 41 corpus-wide `Context X = null;` hits, all immediately-reassigned or otherwise non-security-relevant | [CERT] | `find -exec grep -nE` this session, each hit individually read |
| 6 | `CsrfUtil`/`CsrfProtectedFilter` contain zero counter/lockout state; `BJettyDoSFilter.enabled` defaults to `false` | [CERT] | `organized/web/vineflower/niagara/web/CsrfUtil.java:36-44`, `organized/web/vineflower/niagara/web/filters/CsrfProtectedFilter.java:43-50`, `organized/jetty/vineflower/com/tridium/jetty/BJettyDoSFilter.java:18-19` |
| 7 | `AuthFailureRateLimiter` exists as the daemon's OWN login-failure lockout, a separate mechanism from CSRF | [CERT] | `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/http/Authenticator.java:36` |
| 8 | 6 corpus-wide call sites of `BPlatCryptoManager.make(`, all in `platDaemon`/`provisioningNiagara` | [CERT] | `find -exec grep -n` this session, each site read |
| 9 | `CertHealthMessage`/`GetPasswordStrengthMessage` exist under `platform/daemon/message/`, not `platcrypto/daemon/messages/` | [CERT] | `organized/platform/vineflower/com/tridium/platform/daemon/message/{CertHealthMessage,GetPasswordStrengthMessage}.java` |
| 10 | `BPlatCryptoManager.generateSelfSignedCert(NX509CertificateBuilder,...)`/`resetUserKeyStore()` have zero `KeyStorePermission` call | [CERT] | `organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatCryptoManager.java:132-157`, `organized/platCrypto/vineflower/com/tridium/platcrypto/daemon/BPlatCryptoBase.java:39-51` |
| 11 | `isBasicConstraintsExtensionValid()` is unconditionally `true` for any non-`CA_CERT` profile purpose | [CERT] | `organized/signingService/vineflower/com/tridium/signing/profile/BSimpleSigningProfile.java:298-300` |
| 12 | `checkKeyUsageExtension`/`checkExtendedKeyUsageExtension` only require listed flags present, never check others absent | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/CertUtils.java:475-493` |
| 13 | `niagara.permissions.disable` silently swallows caught `PermissionException`s via a `finally` re-throw guard, but never calls into `program.jar`/`BCode` | [CERT] | `organized/baja/vineflower/com/tridium/sys/Nre.java:929-941`, `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/PermissionManager.java:51-144` |
| 14 | 34-class, 24-module Security Dashboard provider census (2 independent search methods); zero surface network-connection grants | [CERT] | `find -iname "*SecurityDashboard*"` + `grep -l 'implements.*BISecurityDashboard*'`, this session, each network-adjacent match individually read |

Tally: 14 [CERT] table rows; every severity/reachability rating in §99.1/§99.3/§99.6/§99.7 is stated inline as
`[INFER]` (reasoning from confirmed code facts to real-world exploitability, per the task's own "rate with
reasoning + preconditions, no working exploit" instruction), not claimed as a table-row `[CERT]`. Adjusted
ratio: this is a mixed evidence block whose closing verdicts rest on direct file reads and exhaustive greps
this session (all 14 table claims `[CERT]`), with a proportionate number of `[INFER]`-flagged severity clauses
layered on top of each `[CERT]`-established code fact — consistent with an EVIDENCE-type block that also
carries the task's explicit rating requirement.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block99.md`. Census scripts
(`census.py`, `census2.py`, `classify.py`, `classify2.py`, `classify3.py`) and their JSON outputs preserved at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b99/`
(scratch, not archived in the corpus, per the task's single-file constraint — reproducible from the regexes
quoted in the header Method paragraph). No other file was edited; `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration is left to the orchestrator per the task's explicit instruction.
