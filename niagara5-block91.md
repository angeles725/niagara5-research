# Block 91 — Web-layer security exposure and Context threading: no first-party null-Context→canRead exploit chain found corpus-wide, `BLegacyBasicAuthenticationScheme` is reachable-but-likely-broken, DashboardPan's 3 read-side null-Context resolves are safe today but fragile, the CSRF timing side-channel is rated LOW, `SimpleKeyRing`'s export format is empirically confirmed incompatible with `AESStreamEncryption.isEncrypted()`, and a first-party `@NiagaraRpc` method traces the injected `SecurableContext` into a real write — while exposing a fail-open permission-skip on a null ambient user

> Research closing/narrowing seven named child gaps on the web-layer security exposure and Context-threading
> theme: **B86-G1** (whether any first-party N5 code chain combines a null-`Context` ORD resolution with a
> subsequent `canRead()`/`getPermissions()` exposure-gate check); **B86-G2** (whether
> `BLegacyBasicAuthenticationScheme`, whose `getLoginConfiguration()` returns `null`, is ever actually
> selected/invoked at runtime, versus vestigial); **B46-G3** (whether the 3 read-side
> `BOrd.make(...).get(this, null)` resolutions in the DashboardPan PoC should also receive the request's real
> `Context`); **B52-G1** (severity assessment of `CsrfUtil`/`NiagaraSuperSession`'s non-constant-time
> `String.equals()` CSRF-token comparison); **B52-G2** (whether the frontend should refetch the CSRF token
> after a 403); **B82-G2** (refines the unclosed half of B66-G1: whether `SimpleKeyRing.exportKeyData()`'s raw
> `[IV][AES(...)]` byte format would register as `AESStreamEncryption.isEncrypted() == true`); **B68-G2**
> (whether `NiagaraRpcUtil.rpc()`'s injected `SecurableContext` argument is actually threaded onward into a
> first-party `@NiagaraRpc`-annotated method's own `set()`/`invoke()` calls, or merely accepted and dropped).
>
> **Parent-block gap-text confirmation, with one drift found and corrected per task instruction.** All seven
> gap texts were re-read directly from their source block files this session
> (`niagara5-block86.md`, `niagara5-block46.md`, `niagara5-block52.md`, `niagara5-block82.md`,
> `niagara5-block68.md`) before investigation began. Six match the task's paraphrase closely (B86-G1, B86-G2,
> B46-G3, B52-G1, B52-G2, B68-G2 — verbatim quotes given per-section below). **B82-G2 drifted**: the task
> handed this session the text "BFormat.ReflectCall.eval permission-gate caller census" (reproducing
> `RESEARCH-STATE.md`'s own backlog-table row for `B82-G2`, `low | B82-G2 BFormat.ReflectCall.eval
> permission-gate caller census | baja | pending`), but `niagara5-block82.md`'s own "Child gaps opened"
> section defines **B82-G2** as something else entirely: "Whether `SimpleKeyRing.exportKeyData()`'s raw
> `[IV][AES(ObjectOutputStream-serialized entries)]` byte format ... would register as
> `AESStreamEncryption.isEncrypted() == true` ... requires opening `AESStreamEncryption`'s private
> `StreamEncryptionDetails` header-detection constructor ... not opened this session." Per this task's own
> GAP-ID DISCIPLINE instruction ("if the text I give differs, use the block's text and say so explicitly"),
> **this session investigated block82's own real B82-G2** (§91.6 below), not the backlog-table's
> mismatched row. The "ReflectCall.eval permission-gate" topic the task's paraphrase actually names was
> **already closed** by [Block 82] itself as **B66-G2** (§82.1) — `RESEARCH-STATE.md`'s `B82-G2` row appears
> to be a bookkeeping mix-up, most likely a stray copy of `B66-G2`'s topic under the wrong ID; this session
> does not correct `RESEARCH-STATE.md` (out of this task's scope — orchestrator integrates), but flags the
> row here so the drift is not silently perpetuated a second time.
>
> Covers: a corpus-wide (not DashboardPan-scoped) two-pattern regex census for a chained null-Context-resolve
> → permission-check shape (B86-G1); a reachability trace for `BLegacyBasicAuthenticationScheme` via its
> `@AgentOn`/`BAuthenticationSchemeFolder` registration path, cross-checked against the N4 corpus and the
> official `docUser` doc set (B86-G2); a direct read of the DashboardPan PoC's actual current 4 `.get(this,
> null)` call sites (3 matching B46-G3's original framing, 1 newer and out of scope) against `BWebServlet
> .doService()`'s own request-wide `OPERATOR_READ` gate (B46-G3); a CSRF-token-entropy/timing-side-channel
> severity assessment with explicit exploit preconditions, no working exploit attempted (B52-G1); a
> restated recommendation for the frontend refetch-after-403 gap, not implemented (B52-G2); a full read of
> `AESStreamEncryption$StreamEncryptionDetails`'s constructor plus a 200,000-trial empirical
> `DataInputStream.readUTF()` test against random IV-shaped bytes (B82-G2); and a full trace of
> `NiagaraRpcUtil.rpc()`'s `SecurableContext` injection into a representative first-party `@NiagaraRpc`
> method (`BComponentRpc.setCategoryMask`), including its own permission-check code path and a
> corpus-wide sweep for the same conditional-skip shape (B68-G2). Does **not** cover: a live-station
> reproduction of any finding here (`[CERT-hw]`/`[CERT-live]`, blocked — no runnable N5 station this session,
> same constraint as every predecessor block on this corpus); a full census of all 57 "unrestricted"-permission
> `@NiagaraRpc` methods for the fail-open-on-null-user shape (only ~4 files spot-checked — see child gap
> **B91-G3**); a vendor security-bulletin search or live timing-attack probe for B52-G1 (named, not attempted,
> per the gap's own original closing bar — this session answers the ORCHESTRATOR's separate "rate severity
> with reasoning and exploit preconditions" instruction instead, which does not require either).
>
> Subject version: **N5 5.0.0.28 (Beta)**, the same install every predecessor block in this corpus reads
> (`etc/brand.properties:workbench.notice`, not re-verified this session — REMIT of [Block 65]/[Block 81]'s
> convention). PoC module cross-checked: `poc/dashboardpan-n5/` (`DashboardPan` `vendorVersion="2.1.1"`,
> unchanged this session — no PoC source was edited, this is an EVIDENCE block, unlike [Block 46]/[Block 52]'s
> PoC-implementation blocks). N4 comparison baseline for B86-G2 only: `niagara-research` corpus, decompiled
> from OptimizerSupervisor-N4.14.0.162, at `/home/cristian/niagara-research/organized/`. No fresh
> decompilation was run this session — every file cited was already present in one of the two corpora's
> `organized/` trees from prior extraction sessions.
>
> Sources: `organized/baja/vineflower/com/tridium/util/{NiagaraRpcUtil,SecurableContext}.java`,
> `organized/webEditors/vineflower/com/tridium/webeditors/ux/servlets/BComponentRpc.java`,
> `organized/box/vineflower/com/tridium/box/BSysChannel.java`,
> `organized/web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java`,
> `organized/baja/vineflower/niagara/sys/BComponent.java` (targeted `:877-893`),
> `organized/baja/vineflower/niagara/user/{BUser,BUserService}.java` (targeted, corroborating reads),
> `organized/alarm/vineflower/niagara/alarm/BAlarmService.java` (targeted `:761-824`),
> `organized/baja/vineflower/com/tridium/authn/{BLegacyBasicAuthenticationScheme,
> BHTTPBasicAuthenticationScheme,BAuthenticationSchemeFolder}.java`,
> `organized/web/vineflower/niagara/web/BWebServlet.java` (targeted `:70-88`),
> `organized/web/vineflower/niagara/web/CsrfUtil.java`,
> `organized/baja/vineflower/com/tridium/session/NiagaraSuperSession.java` (targeted `:170-198`),
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/io/AESStreamEncryption.java`,
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SimpleKeyRing.java` (targeted `:327-357`),
> `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/bundle/CryptographicAlgorithmBundle.java`,
> `/home/cristian/niagara-research/organized/baja/baja/{vineflower,decompiled}/com/tridium/authn/
> BLegacyBasicAuthenticationScheme.java` (N4 cross-check), `/home/cristian/niagara-research/organized/docUser/
> docUser-doc/extracted/doc/baja-HTTPBasicAuthenticationScheme.html`, `poc/dashboardpan-n5/DashboardPan-rt/src/
> com/angeles/DashboardPan/ux/{BDashboardServlet,DashboardRbacHelper}.java` (read, not edited, this session).
> [Block 86] §86.1 (`OrdTarget.canRead()`/`BComponent.getPermissions(cx)` null-grants-all finding, REMIT),
> [Block 68] §68.4/§68.6 (write-audit census, `BOrd`→`OrdTarget`→`BasicContext` null-resolve chain, REMIT),
> [Block 46] §46.1 (the original 3-site DashboardPan inventory, REMIT), [Block 52] §52.1/§52.9 (`CsrfUtil`
> read, non-constant-time finding, REMIT), [Block 82] §82.1/§82.4 (`ReflectCall.eval` closed, `backup.jar`
> KeyRing mechanism, REMIT), [Block 54] §54.4 (`NiagaraRpcUtil.rpc()` injection point, REMIT).
>
> Method: corpus-wide `find organized -name '*.java' -exec grep` census (two independent regex passes, one
> variable-assignment-based, one inline-chain-based, both zero-hit — negative-existence census per
> METHODOLOGY's "completed whole-corpus search" bar for the LITERAL-`null`-keyword shape only, residual named
> as **B91-G1**); direct reads of every cited file, whole-method or whole-class; a compile-and-run empirical
> test (`javac`/`java`, this session's own JDK) of `DataInputStream.readUTF()` against 200,000 random
> 80-byte samples shaped like `[16-byte IV][64 bytes]`, to move B82-G2's answer from pure code-reading
> `[INFER]` to an empirically-measured `[CERT-hw]`; a grep-based file-list intersection (`permissions =
> "unrestricted"` ∩ `getUser() != null` guard) to find B68-G2's representative case and assess how systemic
> its shape is. Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) ·
> `[CERT-hw]` this session's own compile/run/tool output · `[CERT-doc]` official downloaded/extracted document
> · `[INFER]` deduction, including every claim that extrapolates a checked subset's result to an unchecked
> remainder. `[CERT-live]`/`[CERT-web]`/`[CERT-a]` not used in this block.
>
> **Type:** mixed (evidence)

---

## 91.1 — B86-G1 NARROWED (strong negative evidence, not fully closed): a corpus-wide two-pattern census finds zero first-party chains combining a literal null-`Context` ORD resolve with a subsequent `canRead()`/`canWrite()`/`getPermissions()` exposure check `[CERT]`

**Gap's own text** (`niagara5-block86.md`, "Child gaps opened"): *"Whether any first-party N5 code chain
actually COMBINES a null-`Context` ORD resolution (the read-side pattern [Block 46]'s **B46-G3** named) with
a subsequent `canRead()`/`getPermissions()` check used to decide exposure to a less-trusted or remote caller
— the concrete exploit shape §86.1's finding makes possible in principle. This session found the two
ingredients ... but did NOT find them chained together at a single call site. `investigable` — would need a
targeted grep for `BOrd.*get\(.*,\s*null\)` results immediately followed by a `.canRead()`/`.canWrite()`/
`.getPermissions()` call in the same method, across the whole corpus (broader than [Block 46]'s
DashboardPan-only scope)."* Matches the task's paraphrase.

**Method, exactly the gap's own suggested next step, run to completion this session.** A Python script
scanned every `.java` file under `organized/*/vineflower/` (fallback/docSource excluded, consistent with
every prior block's census convention) for two independent shapes:

1. **Assignment shape**: `VAR = <expr>.(get|resolve)(<args>, null)` followed, within the next 800 characters
   of source (roughly the remainder of the enclosing method for ordinary Niagara code), by `VAR.(canRead|
   canWrite|canInvoke|getPermissions)(`.
2. **Inline-chain shape**: `.get(<args>, null)` or `.resolve(<args>, null)` directly, syntactically, chained
   into `.canRead(|canWrite(|canInvoke(|getPermissions(` on the SAME expression (no intermediate variable).

```
$ python3 <script scanning both patterns over all organized/*/vineflower/*.java>
0 hits (pattern 1)
0 hits (pattern 2)
```
`[CERT]` (this session's own script run, `/tmp/.../scratchpad/b91/` — scripts not preserved in the corpus
per task's single-file constraint, reproducible from the two regexes above). **Zero first-party N5 code
chains combine a literal null-`Context` ORD resolution with a subsequent permission-exposure check on the
same resolved object corpus-wide** — this extends [Block 86] §86.1's own DashboardPan-scoped negative finding
to the full ~18,000-file corpus, using the gap's own proposed method.

**Residual scope, honestly bounded** (why this is NARROWED, not CLOSED, per METHODOLOGY's "negative-existence
claims require a completed whole-corpus search" — the search completed for the SHAPE described, not for
every conceivable shape): this census only catches the LITERAL `null` keyword appearing as the second
argument. It cannot detect (a) a `Context cx = null;` variable later passed by name, (b) a resolve/check pair
split across a caller and a callee method (e.g. one method resolves with `null` and RETURNS the target, a
different method later calls `.canRead()` on it), or (c) a check performed through an intermediary that is
not literally spelled `canRead`/`canWrite`/`canInvoke`/`getPermissions` (e.g. a wrapper method name). Named as
child gap **B91-G1** below, `investigable`, low priority given the negative result across two independent,
complementary regex shapes and [Block 86]'s own prior DashboardPan-scoped negative.

## 91.2 — B86-G2 NARROWED: `BLegacyBasicAuthenticationScheme` is statically reachable only via a manual Workbench "New" add (agent-registered, not auto-wired), cross-version-identical to N4, undocumented in the official user doc — live selection/login outcome remains unconfirmed `[CERT]`+`[INFER]`

**Gap's own text** (`niagara5-block86.md`): *"Whether `BLegacyBasicAuthenticationScheme` (`SCHEME_NAME =
"basic"`, `getLoginConfiguration()` returns `null`, `getDefaultAuthenticator()` returns `null`) is ever
actually SELECTED/invoked at runtime — since `BAuthenticationScheme.login(handler)`'s `new LoginContext("",
null, handler, null)` would, per ordinary JAAS semantics, fall back to the JVM's SYSTEM-WIDE default
`Configuration` (not a Niagara-supplied one) when passed a `null` `Configuration`, and no `""`-named entry is
likely to exist there — meaning this scheme may be structurally incapable of completing a login via this code
path. `investigable` — would need to find `BLegacyBasicAuthenticationScheme.INSTANCE`/`getSchemeFromName
("basic")` call sites and confirm whether the scheme is ever actually reachable as an active login path versus
a vestigial N4-compat name kept only for enumeration/migration purposes."* Matches the task's paraphrase.

**No hardcoded selection call site exists.** A corpus-wide `grep -rn "BLegacyBasicAuthenticationScheme"`
finds exactly ONE hit outside the class's own file — nothing (the class is referenced by name nowhere else in
the N5 corpus) `[CERT]`. Schemes are not selected by a hardcoded name lookup in first-party code at all:
`BAuthenticationSchemeFolder` (the actual container station operators populate) `isChildLegal()`-gates any
`BAuthenticationScheme`-typed child and enumerates whatever is PRESENT via `getChildren(BAuthenticationScheme
.class)` `[CERT]` `organized/baja/vineflower/com/tridium/authn/BAuthenticationSchemeFolder.java:34-36,60-63`
(whole 66-line file) — reachability is therefore a STATION-CONFIGURATION question (has an operator instantiated
one?), not a code-path question. `BLegacyBasicAuthenticationScheme` is registered as an installable AGENT via
`@NiagaraType(agent = @AgentOn(types = "baja:AuthenticationScheme"))` `[CERT]` `organized/baja/vineflower/
com/tridium/authn/BLegacyBasicAuthenticationScheme.java:12` — this is the mechanism that makes it appear in
Workbench's "New" palette when browsing `AuthenticationSchemes`, i.e., **it IS instantiable by any operator
with write access to that folder**, even though nothing in the platform ever creates one automatically or by
default.

**Cross-version stability and documentation gap, both confirming "vestigial name-compat shim", not "N5-new
defect".** The identical class (same package, same `SCHEME_NAME = "basic"`, same `null`/`null` overrides) is
present in the N4.14.0.162 corpus too, in both the pristine `vineflower/` decompile and an independently-run
CFR `decompiled/` copy `[CERT]` `/home/cristian/niagara-research/organized/baja/baja/vineflower/com/tridium/
authn/BLegacyBasicAuthenticationScheme.java:1-33` — not an N5 addition, carried forward unchanged. **Neither
tree's copy carries a source-level doc comment** (confirmed on both the Vineflower and CFR decompiles, no
`/** ... */` block precedes the class in either), and the official N4 `docUser` help set documents ONLY the
real, functional HTTP-Basic scheme — `BHTTPBasicAuthenticationScheme` (`SCHEME_NAME = "n4HTTPbasic"`, a proper
`NiagaraLoginConfiguration` wrapping `UsernamePasswordLoginModule`, `[CERT]` `organized/baja/vineflower/
com/tridium/authn/BHTTPBasicAuthenticationScheme.java:14-34`) — under the doc page titled "HTTP Basic
Authentication Scheme (baja-HTTPBasicAuthenticationScheme)" `[CERT-doc]` `/home/cristian/niagara-research/
organized/docUser/docUser-doc/extracted/doc/baja-HTTPBasicAuthenticationScheme.html`. The doc's own
instructions to access it name the palette path `AuthenticationService > AuthenticationSchemes >
WebServicesSchemes > HTTPBasicScheme` — never mentioning a "Legacy"/`"basic"`-named alternative anywhere in
this document. **No official doc names `BLegacyBasicAuthenticationScheme` at all**, corpus-wide (checked
against every `*BasicAuthenticationScheme*` doc hit found).

**Residual outcome question, unconfirmed, `[INFER]` only.** If an operator DID add one and select it as an
active scheme, [Block 86] §86.1's own reading of `BAuthenticationScheme.login(handler)`'s `new LoginContext
("", null, handler, null)` stands: ordinary JAAS semantics resolve a `null` `Configuration` argument to
`Configuration.getConfiguration()` (the JVM-wide installed default), which on an ordinary Niagara station JVM
(no `java.security.auth.login.config` system property or `${java.home}/conf/security/java.auth.login.config`
file set up for Niagara's own purposes — not independently confirmed this session, named as residual **B91-G5**)
very likely either throws (`SecurityException`/`LoginException: unable to locate a login configuration`) or
finds no `""`-named entry and fails with `"no LoginModules configured"` — i.e., **the scheme is far more
likely to be BROKEN (fails to authenticate at all) than to be an authentication BYPASS**, which is the
opposite of a live security exposure. **Net verdict**: NARROWED, not CLOSED — this session establishes
concrete, cross-version-stable, code-and-doc-based evidence for "reachable-if-manually-added,
undocumented, vestigial-by-design" over "actively wired"; the actual runtime login OUTCOME if selected
remains `[INFER]`, blocked on a live station (**B91-G5**).

## 91.3 — B46-G3 answered with a concrete recommendation: today's 3 named `.get(this, null)` reads are safe because of a COARSER caller-side gate, but the design is fragile and should thread the real `Context` as defense-in-depth `[CERT]`

**Gap's own text** (`niagara5-block46.md`, quoted by [Block 68] §68.6 and [Block 86] as still-open): the 3
`BOrd.make(...).get(this, null)` reads in `BDashboardServlet` (resolving `parentOrd`, `SERVICE_ORD`, and an
alarm-record source ORD) — *"whether ... [these] should also receive the real `cx` for permission-scoped ORD
resolution ... whether resolution itself respects the caller's read permissions rather than the servlet
component's own ambient identity"*. Matches the task's paraphrase.

**The PoC's current source has grown to 4 such call sites; the 3 named ones are still identifiable by name.**
A fresh read of `poc/dashboardpan-n5/DashboardPan-rt/src/com/angeles/DashboardPan/ux/BDashboardServlet.java`
this session finds `niagara.naming.BOrd.make(...).get(this, null)` at 4 lines: `:273` (`parentOrd`, inside
`handleSetpointWrite`), `:365` (`DashboardReader.SERVICE_ORD`, inside `resolveDashboardService()`), `:622`
(a BQL query string, inside `buildAlarmsJson()` — **not** one of B46-G3's original 3, added after [Block 46],
out of this gap's named scope), and `:689` (`rawSource`, the alarm record's own source ORD, inside
`resolveSourceLabel()`) `[CERT]` (all 4 read this session). The 3 matching B46-G3's own framing are `:273`,
`:365`, `:689` — parentOrd, `SERVICE_ORD`, alarm-record-source, exactly as named.

**Why today's answer is "safe, but not because of these resolutions themselves".** Every request to
`BDashboardServlet` — GET or POST, read or write, before ANY of `handleEquipment`/`handleAlarms`/
`handleSetpointWrite` ever runs — passes through the shared `BWebServlet.doService()` base-class gate:
```java
Context cx = (Context)req.getAttribute("niagara.context");
if (!this.getPermissions(cx).hasOperatorRead()) {
   resp.sendError(403);
} else { ... this.service(op); ... }
```
`[CERT]` `organized/web/vineflower/niagara/web/BWebServlet.java:70-88` (whole `doService()` method, already
established REMIT of [Block 41]/[Block 68]) — using the REAL `"niagara.context"` request attribute, not a
synthetic or `null` one. This means the 3 named `.get(this, null)` resolutions execute only AFTER the caller
has already been confirmed to hold `OPERATOR_READ` on the servlet ITSELF; the null-Context resolution is
purely an internal implementation detail of HOW the servlet locates its OWN facade components, not a
second, independent authorization decision. Combined with §91.1's corpus-wide finding that no `BOrdScheme` in
an ordinary `station:`/`slot:`-style ORD path (the kind `SERVICE_ORD`/`parentOrd`/an alarm-record ORD all are)
enforces its own permission check regardless of Context (`[Block 86] §86.1`, REMIT — reused, not re-derived),
resolving these 3 sites with `null` versus the real `cx` produces **structurally identical results today**: no
narrower per-resolution check is being bypassed, because none exists on this particular ORD family.

**Why the recommendation is still "yes, thread the real `cx`", as defense-in-depth, not as a fix for an active
hole.** The safety above is CONTINGENT and silent-on-failure: (1) it depends on `BWebServlet.doService()`'s
own gate remaining in front of every handler — an implementation detail of the base class, not something
`BDashboardServlet`'s own code enforces or re-verifies at the 3 read sites themselves; (2) per [Block 86]
§86.1, 4 of 53 `BOrdScheme`s (`spy:`, `nav:`, `sql:`, hierarchy) DO enforce their own permission check — if
`SERVICE_ORD`/`parentOrd`/the alarm-source ORD ever traversed through one of those (e.g. a future `nav:`-scheme
link), a `null`-Context resolution would silently receive `BPermissions.all` at that scheme's own gate (per
[Block 86] §86.1's `BComponent.getPermissions`/`OrdTarget.canRead()` finding, REMIT), reintroducing exactly
the exposure shape B86-G1 searched for and did not find — with **zero test failure and zero log line**
signaling the regression, since a null-Context resolution never throws. Threading the real `cx` costs nothing
functionally here (per the equivalence just shown) and removes this latent fragility. **Verdict: B46-G3
answered, not merely narrowed** — current risk is LOW (a coarser, already-real gate covers it, and the
specific ORD family in play never self-checks permissions), but the recommendation is to fix it as
defense-in-depth against future ORD/scheme changes, not because an active exposure was found. No code change
was made this session (out of this EVIDENCE block's scope, unlike [Block 46]/[Block 52]'s PoC-implementation
blocks).

## 91.4 — B52-G1 severity assessment: LOW, with explicit exploit preconditions — a real but narrow timing side-channel against a 192-bit token, gated by session possession and heavy statistical-averaging requirements `[CERT]`+`[INFER]`

**Gap's own text** (`niagara5-block52.md`): *"The non-constant-time `String.equals()` CSRF-token comparison
(§52.9) is PLATFORM code ... Whether Tridium's own threat model accepts this ... was not confirmed against any
vendor security advisory or changelog this session. `investigable` — would need a vendor security-bulletin
search or a live timing-attack probe against a real station, neither attempted this session."* This session
answers the ORCHESTRATOR's separate, explicit instruction ("rate severity with reasoning and exploit
preconditions, no working exploit") rather than the gap's own narrower closing bar (a vendor-advisory search
or live probe) — neither of the latter two was attempted, so this NARROWS rather than CLOSES the gap as
originally framed, while fully satisfying the task's own ask.

**Token generation, re-confirmed this session.** `NiagaraSuperSession.getCsrfToken()` mints a **24-byte
(192-bit) `SecureRandom` value, Base64-encoded to a 32-character string, once per session and cached** (not
rotated per-request):
```java
byte[] bytes = new byte[24];
rand.nextBytes(bytes);
this.csrfToken = Base64.getEncoder().encodeToString(bytes);
```
`[CERT]` `organized/baja/vineflower/com/tridium/session/NiagaraSuperSession.java:177-187` (`rand` is a static
`SecureRandom`, `:33`, same file). Comparison is `this.csrfToken.equals(srcCsrfToken)` /
`sessionToken.equals(token)` at both the session-object level and the public `CsrfUtil` utility, `[CERT]`
`organized/baja/vineflower/com/tridium/session/NiagaraSuperSession.java:190-198`,
`organized/web/vineflower/niagara/web/CsrfUtil.java:36-44` (both already
cited [Block 52] §52.1, re-confirmed here). Java's `String.equals()` returns `false` immediately on a LENGTH
mismatch (both strings are the SAME fixed 32-char length in the ordinary case, so this leaks nothing extra
here) but otherwise compares character-by-character with an EARLY EXIT on the first mismatch — the
textbook variable-time comparison a timing side-channel targets.

**Severity reasoning and exploit preconditions, `[INFER]`:**
1. **Attacker must already possess or induce sending toward a LIVE, valid session** — a timing attack recovers
   the token value, it does not forge a session; the attacker needs either (a) to be a CROSS-SITE attacker
   riding the victim's browser (the ordinary CSRF threat model: `fetch()`-based timing IS measurable
   cross-origin even when the response BODY is not readable, since completion timing is not blocked by
   Same-Origin Policy — so a malicious page COULD in principle fire many background guesses through the
   victim's authenticated browser and time them), or (b) a network position capable of timing responses with
   sub-millisecond precision (same-LAN/low-jitter — a WAN attacker's jitter typically swamps a single-character
   timing delta long before amortization completes).
2. **Statistical cost is large for a 192-bit token over a 64-symbol (Base64) alphabet compared 1 char at a
   time**: recovering each of 32 characters via early-exit timing requires many repeated, averaged samples per
   candidate character to separate a genuine signal from network/scheduler jitter (well-documented prior art
   on remote string-comparison timing attacks needs on the order of hundreds to low-thousands of samples PER
   CANDIDATE CHARACTER for a reliable signal even on a fast LAN) — for 64 candidate values × 32 positions this
   plausibly runs to tens-of-thousands to low-hundreds-of-thousands of timed requests for one full token,
   sustained against ONE unrotated session token, before the session naturally expires/rotates.
3. **The token is unrotated per-request but IS per-session** — a successful full recovery is only useful for
   the remaining lifetime of that one session; it does not compromise other sessions, other users, or any
   password/credential material.
4. **Whether Niagara enforces any rate-limiting/lockout on repeated failed CSRF verifications was not checked
   this session** — its presence would sharply raise the practical cost (or block the attack outright); its
   absence would make the large-sample requirement above merely slow, not infeasible. Named as **B91-G4**.

**Rated LOW severity.** Reasoning: the underlying bug class (non-constant-time secret comparison) is real and
textbook, but (a) the secret being compared is a single-session-scoped, 192-bit value, not a long-lived
credential; (b) exploitation needs tens-of-thousands-plus precisely-timed requests sustained against one
session, a large and almost certainly noisy/detectable footprint against a live OT/BMS deployment; (c) this
is PLATFORM code (`niagara.web.CsrfUtil`/`com.tridium.session.NiagaraSuperSession`), unchanged and unmodifiable
by any first-party module or this PoC, consistent with [Block 52]'s own framing; (d) it is not a novel
N5-specific regression this session found any evidence of (no cross-version comparison was run this session,
unlike B86-G2 — named as a residual completeness note only, not a new gap, since [Block 52] itself already
scoped the platform-code framing). This matches, and gives explicit reasoning + preconditions for, [Block
52]'s own already-stated "network-jitter-dominated, low practical exploitability" read.

## 91.5 — B52-G2 reaffirmed as a UX/robustness gap, not a security defect: the write correctly fails CLOSED on a stale token; a concrete refetch-and-retry design is given, not implemented `[CERT]`+`[INFER]`

**Gap's own text** (`niagara5-block52.md`): *"The frontend's cached `csrfToken` variable ... is never
refreshed after a 403 `csrf token invalid` response ... A retry-once-with-refetch pattern would close this;
not implemented this session (explicitly a UX/robustness gap, not a security gap — the write still correctly
fails closed, just with a less helpful error until reload)."* Matches the task's paraphrase.

**Confirmed still accurate this session**: `verifyCsrf(req, resp)` on the server side (§52.3, REMIT) throws
`CsrfException` → HTTP 403 `{"error":"csrf token invalid"}` on any mismatch, INCLUDING a stale
client-cached token — there is no code path in which a stale token is silently accepted; the write is denied,
not weakened. This is a correctness/availability gap for the legitimate user (a session rollover mid-page
leaves them unable to write until a manual reload), not an authorization gap. **Concrete design for closing
it** (not implemented, per this EVIDENCE block's scope): on receiving a 403 with body matching
`"csrf token invalid"` from the `POST /api/setpoint` call sites, call `fetchCsrfToken()` once more and retry
the ORIGINAL write exactly once before surfacing an error to the user — bounded to one retry (never an
unbounded refetch loop, which would itself be a minor availability risk against a persistently-invalid
session). **Verdict: NARROWED, reaffirmed** — no new evidence changes [Block 52]'s own severity read; a fix
design is now on record but not applied.

## 91.6 — B82-G2 (real text per drift note above) CLOSED: `SimpleKeyRing.exportKeyData()`'s `[IV][AES-ciphertext]` format is NOT shape-compatible with `AESStreamEncryption.isEncrypted()` — confirmed by code trace AND a 200,000-trial empirical test `[CERT]`+`[CERT-hw]`

**Gap's own text** (`niagara5-block82.md`, "Child gaps opened," **B82-G2**, quoted verbatim per this task's
GAP-ID DISCIPLINE instruction since the task-supplied paraphrase drifted — see header note above): *"Whether
`SimpleKeyRing.exportKeyData()`'s raw `[IV][AES(ObjectOutputStream-serialized entries)]` byte format
(`SimpleKeyRing.java:327-356`, read this session) would register as `AESStreamEncryption.isEncrypted() ==
true` — i.e. whether `MigrationEncoding.makeMigrationDecryptFunction`'s first branch (`:42`) is actually
shape-compatible with a `BBackupService`-exported `~security/.kr` blob — requires opening
`AESStreamEncryption`'s private `StreamEncryptionDetails` header-detection constructor ..., not opened this
session."*

**`exportKeyData()`'s exact output shape, re-confirmed.** `[CERT]` `organized/_bin-ext/nre/vineflower/
com/tridium/nre/security/SimpleKeyRing.java:327-357` (whole method, re-read this session): a 16-byte random
`SecureRandom` IV, immediately followed by AES-encrypted ciphertext of an `ObjectOutputStream`-serialized
entry list — `System.arraycopy(ivBytes, 0, result, 0, ivBytes.length); System.arraycopy(encryptedContents, 0,
result, ivBytes.length, ...)` (`:354-355`) — **the very first 16 bytes of the export are RAW RANDOM BYTES**,
not any kind of length-prefixed string header.

**`AESStreamEncryption$StreamEncryptionDetails`'s detection mechanism, opened for the first time in either
corpus this session.** `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/io/
AESStreamEncryption.java:112-139` (whole private nested class, first read):
```java
private StreamEncryptionDetails(InputStream originalInputStream) throws IOException {
   this.stream = new DataInputStream(new BufferedInputStream(originalInputStream));
   this.stream.mark(1024);
   try {
      String encodedHeader = this.stream.readUTF();
      CryptographicAlgorithmBundle algorithmBundle = CryptographicAlgorithmBundle.getInstanceFor(encodedHeader);
      String[] data = algorithmBundle.decode(encodedHeader);
      this.isEncrypted = algorithmBundle instanceof AesAlgorithmBundle;
   } catch (Exception e) {
      this.isEncrypted = false;
   } finally {
      this.stream.reset();
   }
}
```
Detection reads the very FIRST bytes of the stream as a `DataInputStream.readUTF()`-format (2-byte
big-endian length prefix + modified-UTF-8 payload) string, then requires that string to parse as
`"[<algorithmName>]=<data>"` via `CryptographicAlgorithmBundle.getInstanceFor()`/`.decode()` — confirmed by
reading `extractName()`/`getInstanceFor()`: a header not containing the literal substrings `"["` and `"]="`
makes `extractName()` throw `IllegalArgumentException`, which `getInstanceFor()` catches and returns `null`
for; the immediately-following `algorithmBundle.decode(encodedHeader)` call on that `null` then throws
`NullPointerException` `[CERT]` `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/bundle/
CryptographicAlgorithmBundle.java:43-58`. **ANY exception in this chain — a failed `readUTF()`, a `null`
bundle, a failed decode — is caught by the outer `catch (Exception e)` and sets `isEncrypted = false`.**

**Empirical confirmation, this session's own test (`[CERT-hw]`), not merely code-reasoned.** A small Java
program (`UtfTest.java`, this session, `javac`/`java` — build JDK per this corpus's existing toolchain)
generated 200,000 random 80-byte buffers shaped `[16-byte IV][64 arbitrary bytes]` (matching `exportKeyData
()`'s own IV-then-ciphertext shape) and ran `new DataInputStream(new BufferedInputStream(new
ByteArrayInputStream(buf))).readUTF()` on each:
```
throws=199994 noThrow=6 / 200000 trials
```
`readUTF()` throws an exception **99.997%** of the time on IV-shaped random bytes; in the residual 6/200,000
(0.003%) cases it does not throw, it decodes to a 2–3 CHARACTER garbage string (`"F`, `[aJ`, `?C?` observed) —
far too short to ever contain BOTH the literal substrings `"["` and `"]="` `CryptographicAlgorithmBundle
.extractName()` requires, so even these residual cases still fall through to `isEncrypted = false` at the
NEXT step. **Net verdict: 100% of tested cases (200,000/200,000, both by direct outcome and by the
follow-on `extractName()` reasoning for the residual 6) resolve to `isEncrypted() == false`.**

**B82-G2 CLOSED.** `SimpleKeyRing.exportKeyData()`'s raw `[IV][AES-ciphertext]` byte format is **NOT**
shape-compatible with `AESStreamEncryption.isEncrypted()` — it will register as unencrypted (`false`), not
encrypted (`true`), essentially always (empirically: 100.000% in this session's 200,000-trial sample;
theoretically: the residual near-zero tail also fails on independent grounds). This directly answers the
question [Block 82] §82.4/[Block 66]'s B66-G1 raised: `MigrationEncoding.makeMigrationDecryptFunction`'s
`AESStreamEncryption`-based first branch (`:42`, REMIT — not re-opened this session) is **structurally
incapable** of recognizing a `BBackupService`-exported `~security/.kr` blob as its own format — reinforcing
[Block 82] §82.4's own finding that `backup.jar`'s KeyRing-export mechanism is architecturally SEPARATE from
`migrator.jar`'s, sharing only a low-level API contract (`Aes256PasswordManager.encrypt`/`decrypt`), not an
actual interoperable byte format.

## 91.7 — B68-G2 CLOSED for the traced representative case, with a new fail-open finding: `NiagaraRpcUtil.rpc()`'s injected `SecurableContext` DOES thread onward into a first-party `@NiagaraRpc` method's own `set()` call — but that method's own permission gate silently SKIPS (fails open) when the ambient authenticated user is `null`, and box- vs. web/fox-transport RPCs derive "the current user" through two DIFFERENT, non-equivalent mechanisms `[CERT]`+`[INFER]`

**Gap's own text** (`niagara5-block68.md`): *"`NiagaraRpcUtil.rpc()`'s reflective `method.invoke(...)` on the
target `@NiagaraRpc` method ([Block 54] §54.4, REMIT) was not, in this block or [Block 54], followed INTO any
specific first-party `@NiagaraRpc`-annotated method body to confirm the injected `SecurableContext` argument
is actually threaded onward into that method's own `set()`/`invoke()` calls (as opposed to being merely
accepted as a parameter and dropped, the exact pattern §68.4 found twice at the servlet layer).
`investigable` — would need a census of `@NiagaraRpc`-annotated methods across `organized/`."* Matches the
task's paraphrase.

**The injection mechanism, read in full for the first time in either corpus.** `NiagaraRpcUtil.rpc(...)`
resolves the target ORD, then appends a purpose-built anonymous `SecurableContext` (an interface extending
`Context`, `[CERT]` `organized/baja/vineflower/com/tridium/util/SecurableContext.java`, whole 7-line file) as
the LAST reflective-call argument whenever the target method declares a trailing `Context`-typed parameter:
```java
final BUser user = BUser.getCurrentAuthenticatedUser();
...
args.add(new SecurableContext() {
   public boolean isSecure() { return isSecure; }
   public Context getBase() { return cx; }
   public BUser getUser() { return user; }
   ...
});
...
return Optional.ofNullable(convertFromCollection(method.invoke(isStatic ? null : object, args.toArray())));
```
`[CERT]` `organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:87-121,187-188` (whole method body
read, `:54-196`). **Critically, this injected wrapper's `getUser()` does NOT return `cx.getUser()`** (the
caller-supplied `Context`'s own user) — it returns `BUser.getCurrentAuthenticatedUser()`, a STATIC lookup
independent of the `cx` argument, itself defined as `SecurityUtil.getCurrentAuthenticatedSubject()` →
`getUserFromSubject(subject)` (i.e., whatever JAAS `Subject` is bound to the CURRENT THREAD at the moment
`rpc()` runs) `[CERT]` `organized/baja/vineflower/niagara/user/BUser.java:1212-1215`.

**Representative traced case: `BComponentRpc.setCategoryMask` — the injected context reaches a real write.**
`[CERT]` `organized/webEditors/vineflower/com/tridium/webeditors/ux/servlets/BComponentRpc.java:49-68` (whole
method, first read in either corpus):
```java
@NiagaraRpc(permissions = "unrestricted", transports = @Transport(type = TransportType.box))
public static void setCategoryMask(String ord, String maskEncoding, Context cx) throws Exception {
   if (maskEncoding != null) {
      BIProtected iProtected = (BIProtected)BOrd.make(ord).resolve(null, cx).get();
      if (cx != null && cx.getUser() != null) {
         cx.getUser().check(iProtected, BPermissions.adminWrite);
      }
      BCategoryMask mask = BCategoryMask.make(maskEncoding);
      if (iProtected instanceof BComponent) {
         ((BComponent)iProtected).setCategoryMask(mask, cx);
      } ...
```
`cx` here IS the injected `SecurableContext` (its declared type is `Context`, matching `NiagaraRpcUtil
.convertToArgClass`'s `obj instanceof Context → Context.class` reflection-signature match, `[CERT]`
`organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:209-210`), and it IS threaded onward: `((BComponent)iProtected).setCategoryMask(mask,
cx)` calls straight into `BComponent.setCategoryMask(BCategoryMask mask, Context cx) {
this.slotMap.setCategoryMask(mask, cx); }` `[CERT]` `organized/baja/vineflower/niagara/sys/BComponent.java:
877-879` — a real, `Context`-carrying state-changing call, not a dropped/2-arg convenience overload. **This
answers B68-G2 as posed: YES, at least this first-party `@NiagaraRpc` method threads the injected
`SecurableContext` onward into its own write call, rather than accepting-and-dropping it (the pattern [Block
68] §68.4 found in `UxBuilderServlet`/`BStringServlet`).**

**New finding: the method's own permission gate is a fail-OPEN conditional skip, not a fail-closed enforcement
— and `setCategoryMask` is declared `permissions = "unrestricted"`, meaning `NiagaraRpcUtil`'s OWN dispatch-
layer permission check does not run for it either.** Re-reading `NiagaraRpcUtil.rpc()`'s own gate (`:138-169`,
already quoted in full above per METHODOLOGY convention — cited once): for a STATIC method (`setCategoryMask`
is `static`), the `!isStatic && object instanceof BIProtected` branch (`:152`) is skipped entirely regardless
of `permissionsStr`; the `else if (rpc.protectedTargets().length == 0 && !permissionsStr.isEmpty())` branch
(`:158`) is also skipped because `permissionsStr` normalizes to `""` for `"unrestricted"` (`:148-150`) —
**`NiagaraRpcUtil` performs ZERO permission check of its own for this method**, `[CERT]` (re-derivation of
`:138-169`'s control flow against `setCategoryMask`'s specific `isStatic=true`/`permissions="unrestricted"`
combination). The ENTIRE gate is therefore the method's own `if (cx != null && cx.getUser() != null) {
cx.getUser().check(iProtected, BPermissions.adminWrite); }` — and if `cx.getUser()` is `null`, this `if`
body (the ONLY permission check anywhere in the call path) is silently SKIPPED, and execution falls straight
through to the unconditional `setCategoryMask(mask, cx)` write two lines later. **This is a FAIL-OPEN shape**:
a null ambient user causes the write to proceed WITHOUT verification, not to be denied — the mirror image of
[Block 86] §86.1's "null-Context-grants-`BPermissions.all`" finding, but this time even the CALL to check
permissions is skipped rather than the check itself over-granting.

**Corpus-wide scope check: this exact fail-open shape is rare, not systemic — 1 of 4 candidate files, and the
other 3 are differently-shaped.** A file-list intersection of the 57 `permissions = "unrestricted"`
`@NiagaraRpc` files against a `getUser() != null`-guard grep surfaces exactly 4 files `[CERT]`: `BComponentRpc`
(this section — fail-open on a WRITE, as traced); `BAlarmService` (`:820`, read this session,
`organized/alarm/vineflower/niagara/alarm/BAlarmService.java:816-823`) — the SAME null-guard shape but on a
READ-accumulation loop that ADDS NOTHING to its output map when the guard is false, i.e. **fails CLOSED**, the
safer shape; `BUser` (`:702-713`, `getLoginHistoryForCurrentAuthenticatedUser`) — a SELF-scoped ambient-user
read (whoever the ambient ID resolves to, that is whose OWN history is returned) that is safe by construction
regardless of null-handling, and a separate, unrelated property-validator use of the same guard text
(`:790`) not part of the `@NiagaraRpc` injection path at all; `BUserService` (`:588-604`,
`getAutoLogoffSettings`) — genuinely unrestricted BY DESIGN (does not consult `cx` at all, reads any supplied
`username`'s auto-logoff settings unconditionally), a different, lower-sensitivity design choice (auto-logoff
period/enabled flag, not a `adminWrite`-gated component write), not the same bug shape. **Only
`BComponentRpc.setCategoryMask`/`getCategoryMask`/`getAppliedCategoryMask` (all 3 methods in that one file
share the identical `if (cx != null && cx.getUser() != null) { check/read-and-return } ` skip-on-null shape
applied to an `adminWrite`/`operatorRead`-gated action) show the fail-open-on-write or fail-open-on-read-then-
disclose pattern this session set out to characterize.** The full 57-file population was NOT individually read
beyond this intersection — named as **B91-G3**.

**Severity assessment and exploit preconditions, `[INFER]`.** A genuine finding discovered along the way sets
the bound on this: `BSysChannel` (the actual `TransportType.box` dispatch entry point — `BComponentRpc`'s own
declared transport) constructs `cx` from the LIVE box session's OWN authenticated user, NOT from an ambient
JAAS lookup: `NiagaraRpcUtil.rpc(TransportType.box, op.isSecure(), op.getRemoteAddr(), ord, methodName,
arguments, new BasicContext(op.getUser(), op.getLanguageCode()))` `[CERT]` `organized/box/vineflower/
com/tridium/box/BSysChannel.java:172-174`. But per the injection mechanism above, `NiagaraRpcUtil.rpc()`
IGNORES this caller-supplied `cx.getUser()` entirely when building its OWN `SecurableContext` wrapper — the
wrapper's `getUser()` independently re-derives via `BUser.getCurrentAuthenticatedUser()` (the ambient
thread-bound JAAS `Subject`), which is a DIFFERENT code path than `op.getUser()`. By contrast, the
`web`-transport path (`NiagaraRpcServlet`) passes `cx` straight from the `"niagara.context"` HTTP request
attribute `[CERT]` `organized/web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java:32,54` — a value
`com.tridium.web.filters.AddSubjectFilter` ([Block 68] §68.7, REMIT) is already known to wrap in a bound JAAS
`Subject` per-request. **Whether the `box`-transport dispatch thread (inside `com.tridium.box`'s own
session/channel handling — a persistent WebSocket-style channel, structurally different from a per-request
Jetty servlet filter chain) is ALSO guaranteed to run under a bound JAAS `Subject` the way `AddSubjectFilter`
guarantees it for ordinary HTTP servlet requests was NOT traced this session** — this is exactly the
precondition that would need to hold FALSE (no bound Subject on that thread) for a live, authenticated
(but non-`adminWrite`) box-session user's `setCategoryMask` call to reach the fail-open branch. Named as
**B91-G2**, `blocked-on-source` (needs a live-station thread trace or box-channel source not yet opened).
**Rated MEDIUM severity, conditional**: IF reachable, this is a privilege-boundary bypass (a non-admin,
already-authenticated box-session user could set a component's category mask without holding
`adminWrite`) — bounded in blast radius (one configuration write, not broad code execution), and NOT
reachable by a fully unauthenticated remote party regardless (a live box session, i.e. SOME valid login, is
still required per `BSysChannel`'s own session-scoping); capped below HIGH pending **B91-G2**'s live
confirmation, since the "no bound Subject on this thread" precondition is plausible but unconfirmed, not
demonstrated. No working exploit was attempted, per task instruction.

## 91.x — Connections

- **[Block 86]** — closes/narrows **B86-G1** (§91.1, corpus-wide negative extension of §86.1's DashboardPan-
  scoped finding) and **B86-G2** (§91.2, new reachability/documentation facts). Reuses §86.1's
  `BComponent.getPermissions`/`OrdTarget.canRead()` null-grants-all finding as load-bearing REMIT in both
  §91.1's framing and §91.3's B46-G3 answer.
- **[Block 46]**/**[Block 68]** — answers **B46-G3** (§91.3), the gap both blocks left open; reuses [Block
  68] §68.6's `BOrd`→`OrdTarget`→`BasicContext` null-resolve chain trace and [Block 41]/[Block 68]'s
  `BWebServlet.doService()` `OPERATOR_READ` gate finding as the decisive REMIT evidence, rather than
  re-deriving either.
- **[Block 52]** — narrows **B52-G1** (§91.4, severity assessment answering the orchestrator's explicit ask,
  not the gap's own original vendor-advisory/live-probe closing bar) and **B52-G2** (§91.5, reaffirmed, fix
  design given, not implemented). No PoC source was edited this session, unlike [Block 46]/[Block 52]
  themselves.
- **[Block 82]**/**[Block 66]** — closes **B82-G2** per block82's own real text (§91.6; the task's supplied
  paraphrase drifted to a topic [Block 82] itself already closed as **B66-G2** — see header note),
  reinforcing [Block 82] §82.4's "architecturally separate mechanisms" reading of `backup.jar` vs.
  `migrator.jar` with a decisive, empirically-tested byte-format incompatibility.
- **[Block 68]**/**[Block 54]** — closes **B68-G2** for its traced representative case (§91.7), extending
  [Block 54] §54.4's REMIT injection-point finding one hop further into a first-party method body, and
  surfaces a new, previously-uncharacterized divergence between `box`- and `web`/`fox`-transport
  "current user" derivation inside the SAME `NiagaraRpcUtil.rpc()` dispatcher.

## 91.x — Child gaps opened

- **B91-G1** — Extend §91.1's corpus-wide null-Context→canRead census beyond the LITERAL-`null`-keyword shape:
  a `Context cx = null;` variable passed by name, a resolve/check pair split across a caller/callee method
  boundary, or a check performed through a non-standard wrapper method name. `investigable`, low priority
  given the negative result across two independent regex shapes and [Block 86]'s own prior negative.
- **B91-G2** — Whether the `TransportType.box` RPC-dispatch thread (inside `com.tridium.box`'s session/channel
  handling, `BSysChannel` and its callers) runs under a bound JAAS `Subject` the way `com.tridium.web.filters
  .AddSubjectFilter` ([Block 68] §68.7) guarantees for ordinary per-request HTTP servlet dispatch — this is
  the precondition that determines whether `BComponentRpc.setCategoryMask`'s fail-open-on-null-ambient-user
  branch (§91.7) is live-reachable for an authenticated, non-`adminWrite` box-session user.
  `blocked-on-source` (needs live-station thread trace or the box-channel's own session-initialization source,
  not yet opened in either corpus), medium priority given the concrete fail-open code shape already confirmed.
- **B91-G3** — A full census of the remaining ~53 of 57 "unrestricted"-permission `@NiagaraRpc` methods (only
  4 files were read this session — `BComponentRpc`, `BAlarmService`, `BUser`, `BUserService`) for the same
  fail-open-on-null-ambient-user shape found in `BComponentRpc`, versus `BAlarmService`'s safer fail-closed
  shape or `BUserService`'s no-gate-at-all-by-design shape. `investigable`, medium priority — this is the
  actual systemic-surface question §91.7 could only partially answer.
- **B91-G4** — Whether Niagara enforces any rate-limiting/lockout on repeated failed CSRF-token verifications
  (bears directly on §91.4's B52-G1 severity read: presence would further lower practical exploitability,
  absence would only make the already-large sample-count requirement slow rather than infeasible).
  `investigable`/`blocked-on-source` — needs either a live-station probe or a source trace of
  `CsrfException`-handling call sites for a throttle/lockout counter, neither attempted this session.
- **B91-G5** — Whether an N5 station JVM has ANY `java.security.auth.login.config` system property or
  `${java.home}/conf/security/java.auth.login.config` file configured (station launcher script/`niagarad`
  config, not yet checked) — determines whether `BLegacyBasicAuthenticationScheme`'s `new LoginContext("",
  null, handler, null)` (§91.2, [Block 86] §86.1's original reading) throws outright or, less likely,
  resolves to SOME installed default JAAS configuration entry. `blocked-on-source`/`investigable`, low
  priority given ordinary JAAS semantics and the complete absence of any Niagara-authored `""`-named
  `Configuration` entry corpus-wide already strongly favor the "throws/fails" outcome.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | Corpus-wide census, 2 independent regex shapes, 0 hits for null-Context-resolve→canRead/canWrite/canInvoke/getPermissions chained on the same object | [CERT] | this session's own Python script run over all `organized/*/vineflower/*.java` |
| 2 | `BAuthenticationSchemeFolder` enumerates children generically, no hardcoded scheme-name selection | [CERT] | `organized/baja/vineflower/com/tridium/authn/BAuthenticationSchemeFolder.java:34-36,60-63` |
| 3 | `BLegacyBasicAuthenticationScheme` is `@AgentOn`-registered (installable via Workbench "New"), zero other corpus references | [CERT] | `organized/baja/vineflower/com/tridium/authn/BLegacyBasicAuthenticationScheme.java:12`; corpus-wide `grep -rn "BLegacyBasicAuthenticationScheme"` |
| 4 | Identical class (no doc comment, either decompiler) exists unchanged in N4.14.0.162 | [CERT] | `/home/cristian/niagara-research/organized/baja/baja/{vineflower,decompiled}/com/tridium/authn/BLegacyBasicAuthenticationScheme.java` |
| 5 | Official `docUser` doc documents only `BHTTPBasicAuthenticationScheme`/`"n4HTTPbasic"`, never names the Legacy scheme | [CERT-doc] | `/home/cristian/niagara-research/organized/docUser/docUser-doc/extracted/doc/baja-HTTPBasicAuthenticationScheme.html` |
| 6 | DashboardPan's 4 current `.get(this, null)` sites identified; 3 match B46-G3's original naming | [CERT] | `poc/dashboardpan-n5/DashboardPan-rt/src/com/angeles/DashboardPan/ux/BDashboardServlet.java:273,365,622,689` |
| 7 | `BWebServlet.doService()` gates EVERY request (GET+POST) on `getPermissions(cx).hasOperatorRead()` with the real request Context, before any handler runs | [CERT] | `organized/web/vineflower/niagara/web/BWebServlet.java:70-88` |
| 8 | CSRF token is 24 raw `SecureRandom` bytes (192 bits), Base64-encoded, cached per-session; compared via `String.equals()` | [CERT] | `organized/baja/vineflower/com/tridium/session/NiagaraSuperSession.java:177-198`, `organized/web/vineflower/niagara/web/CsrfUtil.java:36-44` |
| 9 | `SimpleKeyRing.exportKeyData()` output is `[16-byte random IV][AES-ciphertext]`, no length-prefixed string header | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/SimpleKeyRing.java:327-357` |
| 10 | `AESStreamEncryption$StreamEncryptionDetails` requires a `readUTF()`-decodable `"[name]=data"` header; any exception → `isEncrypted=false` | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/io/AESStreamEncryption.java:112-139`, `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/bundle/CryptographicAlgorithmBundle.java:43-58` |
| 11 | 200,000-trial empirical test: `readUTF()` on IV-shaped random bytes throws 99.997% of the time; residual 6 cases decode to 2-3 char strings, too short to contain `"["`+`"]="` | [CERT-hw] | this session's own `UtfTest.java` compile+run, `/tmp/.../scratchpad/b91/utftest/` |
| 12 | `NiagaraRpcUtil.rpc()` injects a `SecurableContext` whose `getUser()` is `BUser.getCurrentAuthenticatedUser()`, independent of the caller-supplied `cx` | [CERT] | `organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:87-121`; `organized/baja/vineflower/niagara/user/BUser.java:1212-1215` |
| 13 | `BComponentRpc.setCategoryMask` threads the injected `cx` into `BComponent.setCategoryMask(mask, cx)`, a real `set()`-style write | [CERT] | `organized/webEditors/vineflower/com/tridium/webeditors/ux/servlets/BComponentRpc.java:49-68`; `organized/baja/vineflower/niagara/sys/BComponent.java:877-879` |
| 14 | `NiagaraRpcUtil.rpc()` performs zero permission check for a static, `permissions="unrestricted"` method (both gate branches skip) | [CERT] | `organized/baja/vineflower/com/tridium/util/NiagaraRpcUtil.java:138-169`, re-derived against `setCategoryMask`'s `isStatic=true` |
| 15 | Only 1 of 4 candidate "unrestricted"+null-guard files (`BComponentRpc`) shows the write-side fail-open shape; `BAlarmService` fails closed, `BUser`/`BUserService` are differently-shaped | [CERT] | `organized/alarm/vineflower/niagara/alarm/BAlarmService.java:816-823`; `organized/baja/vineflower/niagara/user/BUser.java:702-713,787-794`; `organized/baja/vineflower/niagara/user/BUserService.java:588-604` |
| 16 | `BSysChannel`'s box-transport dispatch builds `cx` from the box session's OWN `op.getUser()`, a different source than `NiagaraRpcUtil`'s injected wrapper's ambient-JAAS `getUser()` | [CERT] | `organized/box/vineflower/com/tridium/box/BSysChannel.java:172-174`; `organized/web/vineflower/niagara/web/servlets/NiagaraRpcServlet.java:32,54` |

Tally: 15 [CERT]-rows, 1 [CERT-hw]-row (empirical test), 0 pure [INFER]-only rows in the table — every row
rests on a direct `Read`/`grep`/script-run/compile-and-run this session. Prose-level `[INFER]` conclusions
(§91.2's login-outcome prediction, §91.3's "safe today, fragile design" framing, §91.4's severity narrative,
§91.7's MEDIUM-severity conditional rating) are each explicitly hedged in place, consistent with this block's
own declared `Type: mixed (evidence)`. Adjusted ratio: 0 tabled [INFER] / 16 tabled CERT-family ≈ **0.00**
(inline prose `[INFER]` clauses are not tallied as table rows, per [Block 90]'s own established convention for
this corpus) — very low, consistent with a block whose every closing verdict rests on a direct read, a
completed corpus-wide census, or a compile-and-run test this session, not recalled from memory.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block91.md
```
(output pasted into the handback message to the caller, per the task's own instruction to run this until
exit 0.)

**MCP-doc snapshots**: N/A — the one `[CERT-doc]` citation (§91.2's `docUser` HTML page) is a LOCAL file
already present in the `niagara-research` corpus's own `organized/docUser/` tree, opened via direct `Read`,
not fetched from the web.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block91.md` (the only file
written in the corpus this session, per the task's single-file constraint). `INDEX.md`/`RESEARCH-STATE.md`/
`CATALOG.md` were **not** regenerated — left to the integrator step, per the established wave convention. No
PoC/product source under `poc/` was modified this session (EVIDENCE block, read-only against that tree).
Scratch scripts and intermediate data (all reproducible from the commands/code quoted above) live at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b91/`:
the two-pattern null-Context-census Python script, `unrestricted_files.txt` (the 57-file "unrestricted"
`@NiagaraRpc` list), and `utftest/UtfTest.java` (the 200,000-trial `readUTF()` empirical test).
