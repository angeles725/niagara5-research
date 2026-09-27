# Block 46 — Audited writes from DashboardPan on N5: passing the request Context (PoC)

> Research/PoC closing **B41-G6**: make the DashboardPan servlet's live write path audited on N5, by
> threading the request's real authenticated `Context` through the one `BComponent.set(...)` call the
> `-ux` servlet makes, instead of the hardcoded `null` [Block 28]'s ported copy carried over verbatim
> from N4. Covers: a full inventory of every `set(...)`/`invoke(...)` write site in the ported
> `poc/dashboardpan-n5/` module (servlet + service), reading the real N5 API for how a `BWebServlet`
> subclass recovers the per-request `Context` (`niagara.web.BWebServlet.doService()`,
> `com.tridium.web.filters.ContextFilter`), the fix applied to the PoC copy, a rebuild + `javap`
> bytecode confirmation that the fix landed, and residual risks. Does **not** cover: a live-station
> `$/AuditHistory` readback (`[CERT-hw]`, blocked — no runnable N5 station this session, same
> constraint as [Block 41]'s **B41-G4**), porting the fix back into the real N4 client source under
> `modulos_niagara_n4/` (explicitly out of scope — original client sources are never modified by this
> task), or the CSRF hardening note (§46.6, deliberately not implemented per task scope).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as Blocks 27/28/41
> (`etc/brand.properties:workbench.notice`). PoC module version: `DashboardPan` `vendorVersion="2.1.1"`
> (unchanged by this fix — [Block 28] §28.7). Gradle plugin artifacts `5.0.54.9.2`/`5.0.9.8.14`, Gradle
> **9.2.1**, build JDK `/home/linuxbrew/.linuxbrew/opt/openjdk@25` (OpenJDK 25.0.4.1) — identical
> toolchain to [Block 28]. `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` re-counted
> (`ls | wc -l`) before the first build attempt this session and again after the final successful
> build: **247 both times, unchanged** — the install root was never written; all writes (including the
> code edit itself) landed only inside `poc/dashboardpan-n5/` (the existing gitignored ported copy) and
> its local `.n5config/` mirror, per task scope. This block writes NOTHING to the original N4 client
> worktree.
>
> Sources:
> - `poc/dashboardpan-n5/DashboardPan-rt/src/com/angeles/DashboardPan/ux/BDashboardServlet.java` — the
>   file edited this session (before-state read in full, then modified; final state re-read after
>   edit).
> - `poc/dashboardpan-n5/DashboardPan-rt/src/com/angeles/DashboardPan/ux/{DashboardDispatch,
>   DashboardRbacHelper,DashboardReader,JsonUtil}.java`, `.../DashboardPan/{BDashboardService,
>   BRoomPanel}.java` — read/grepped in full this session for the write-site inventory (§46.1).
> - `organized/web/vineflower/niagara/web/{BWebServlet,WebOp}.java` (already-decompiled N5 source,
>   read fresh this session) — `BWebServlet.doService()`/`WebOp.getRequest()`.
> - `organized/baja/vineflower/niagara/sys/{Context,BComplex}.java` — `Context` interface and
>   `BComplex.set(Property,BValue,Context)` signature, read fresh this session.
> - [Block 41] §41.1/§41.4/§41.7 (the `ComponentSlotMap`/`ComplexSlotMap` audit gate
>   `context != null && context.getUser() != null`, and `ContextFilter`'s `"niagara.context"` request
>   attribute — REMIT, not re-derived here, only applied) and [Block 28] §28.3/§28.5 (the ported
>   servlet's own provenance and the `jakarta.servlet` migration).
> - This session's own command output: `./gradlew :DashboardPan-rt:jar` (2 invocations, 1 real
>   failure), `javap -p -c` on the rebuilt `BDashboardServlet.class`, `jarsigner -verify`, `unzip -l`,
>   `ls .../modules | wc -l` — not archived under `sources/probes/` per task scope (single-block
>   deliverable, same convention as [Block 28]), all reproducible from the cited PoC tree and jar.
>
> Method: direct reading of the PoC source (before/after), direct reading of already-decompiled N5
> platform source (no fresh decompilation needed), a real code edit applied to the PoC copy only, a
> real `./gradlew jar` rebuild against the actual N5 5.0.0.28 install, and `javap -p -c` bytecode
> disassembly of the rebuilt class to confirm the edit is what the compiled write site actually calls
> (not merely what the source claims). Markers: `[CERT-hw]` observed build/tool/bytecode output this
> session · `[CERT]` a source file read directly · `[INFER]` deduction.
>
> N5 build-toolchain + security/audit layer, §19 build/PoC phase. Connects [Block 41] (closes
> **B41-G6**, the named child gap this block was launched to close — the mechanism [Block 41] found
> exists but did not verify DashboardPan's own servlet uses), [Block 28] (the ported PoC this block
> edits and rebuilds), [Block 27] (§27.6 CSRF finding — hardening note only, §46.6).
>
> **Type:** standard (evidence, requires-execution/§19 build-PoC)
>
> **Breakthrough:** the PoC's one config-write call site (`BDashboardServlet.java`,
> `handleSetpointWrite`) now threads the request's REAL authenticated `Context` — recovered from the
> same `"niagara.context"` request attribute `niagara.web.filters.ContextFilter` populates from
> `req.getUserPrincipal()` before the servlet ever runs (the exact mechanism [Block 41] §41.7
> documented as available but unverified for DashboardPan) — into `BComponent.set(Property, BValue,
> Context)`, replacing the hardcoded `null` [Block 28]'s port carried over unchanged from N4. The
> module rebuilds clean (`BUILD SUCCESSFUL`), and `javap -p -c` on the rebuilt class file confirms at
> the bytecode level that the `set(...)` call now loads the `cx` parameter (`aload_3`) rather than
> `aconst_null` — closing the exact gap [Block 41] §41.4/§41.7 and the N4 corpus's B829/B830 finding
> named as architecturally unchanged in N5.

---

## 46.1 — Inventory: every write DashboardPan's servlet performs, before this fix `[CERT]`

Full-file `grep -n "\.set(\|\.invoke(\|Context"` across all 8 ported source files (`BDashboardServlet`,
`DashboardDispatch`, `DashboardRbacHelper`, `DashboardReader`, `JsonUtil`, `BDashboardService`,
`BRoomPanel`, `module-info.java`), this session. Result: **exactly one** `BComponent.set(...)` call
reaches a station component from HTTP input, and **zero** `invoke(Action, ...)` calls exist anywhere
in the module — the servlet exposes no HOA/mode/defrost action endpoint; every writable value
(including enum-typed slots such as an HOA-style mode) goes through the single generic
`POST /api/setpoint` handler's `set()` call, dispatched by slot type in `coerceValue()`.

| # | Class#method | Target slot | Context argument (before) | Audited today? (per B41 gate) |
|---|---|---|---|---|
| 1 | `BDashboardServlet#handleSetpointWrite` — `parent.set(prop, toSet, null)` | any resolved `BComponent` property under `SERVICE_ORD` (the facade's config slots — setpoints, and any enum-typed mode/HOA-style slot the facade exposes, per `coerceValue()`'s `BEnum` branch) | `null` `[CERT]` `BDashboardServlet.java:291` (before-state, this session's own read) | **No** — `context != null && context.getUser() != null` fails on `null`; `ComplexSlotMap.audit()` (Block 41 §41.2) is never reached, no `AuditEvent` is built, `$/AuditHistory` never sees the write |
| 2 | `BDashboardService#appendAudit` → generated `setAuditLog(String)` → `setString(auditLog, v, null)` | `BDashboardService.auditLog` (the module's OWN self-rolled JSON-lines audit ring, a private slot on the same component — distinct from Niagara's `$/AuditHistory`) | `null` `[CERT]` `BDashboardService.java:218` (Slotomatic-`@Generated` setter, not hand-written) | **No**, same gate — but see §46.5: this is `@Generated` framework boilerplate, present verbatim on **every** `@NiagaraProperty` setter in **every** Niagara module, not a DashboardPan-specific choice; out of this gap's fix scope (§46.5 explains why) |

No other write path exists: `handleEquipment` (read-only, `DashboardReader.buildEquipmentResponse`)
and `handleAlarms` (read-only BQL query) make zero `set`/`invoke` calls `[CERT]` (full-file grep, zero
hits outside the two rows above). The three `BOrd.make(...).get(this, null)` **reads** (resolving
`parentOrd`, `SERVICE_ORD`, and an alarm-record source ORD) also pass `null` as their second argument,
but that argument is `BObject.get(BObject base, Context cx)`'s **base/Context for resolution**, not an
audited write — out of this gap's scope (`invoke`/`set` only, per the task's own framing); named as
**B46-G3** below for completeness.

## 46.2 — The real N5 API: how a `BWebServlet` subclass recovers the authenticated `Context` `[CERT]`

Re-confirmed fresh this session against the already-decompiled N5 platform source (no new
decompilation needed — REMIT of [Block 41] §41.7, cited here for this block's own inventory work):

```java
private void doService(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
   ...
   Context cx = (Context)req.getAttribute("niagara.context");
   if (!this.getPermissions(cx).hasOperatorRead()) { resp.sendError(403); }
   else {
      OrdTarget target = this.getNavOrd().resolve(BLocalHost.INSTANCE, cx);
      ...
      req.setAttribute("niagara.target", newTarget);
      req.setAttribute("niagara.op", op);
      this.service(op);
   }
}
```
`[CERT]` `organized/web/vineflower/niagara/web/BWebServlet.java:70-92` (read fresh this session). This
is the critical structural fact for the fix: `doService()` reads `"niagara.context"` **only into a
local variable `cx`**, uses it for the `hasOperatorRead()` permission gate and `OrdTarget` resolution,
and **never stores it on `req`, `op`, or any field** — `BWebServlet.doGet(WebOp)`/`doPost(WebOp)`
(overridden by `BDashboardServlet`) receive only the `WebOp`, with no `Context` parameter at all
`[CERT]` `BWebServlet.java:99-125`. A subclass cannot obtain the SAME `Context` object `doService`
built by any accessor — it must **independently re-read the identical request attribute**:
```java
public HttpServletRequest getRequest() { return this.request; }   // WebOp.java:111
```
`[CERT]` `organized/web/vineflower/niagara/web/WebOp.java:111` — `WebOp.getRequest()` returns the
SAME `HttpServletRequest` instance `doService` received, and `"niagara.context"` is a request
attribute (not a local var), so it is still present and unchanged: `req.getAttribute("niagara.context")`
called again from inside `doPost(WebOp op)` returns the identical `Context` object `doService` computed
moments earlier from `op.getRequest()`. This attribute is populated upstream, before the servlet ever
runs, by `com.tridium.web.filters.ContextFilter` (`/*`-registered filter, runs after Jetty's
`SecurityHandler` completes authentication — [Block 41] §41.7, `ContextFilter.java:16-26`), so the
`Context` a subclass recovers this way carries the real authenticated `BUser` whenever one exists — not
a synthetic or elevated one. `[CERT]` (structural finding this session, `BComponent.set`'s Context
overload confirmed at `organized/baja/vineflower/niagara/sys/BComplex.java:400`:
`public final void set(Property property, BValue value, Context context)`).

## 46.3 — The fix applied to the PoC copy `[CERT-hw]`

Three changes to `poc/dashboardpan-n5/DashboardPan-rt/src/com/angeles/DashboardPan/ux/BDashboardServlet.java`
(the existing gitignored ported copy — original N4 client source under `modulos_niagara_n4/` untouched,
confirmed not opened for writing this session):

1. **Import added** (`BDashboardServlet.java:10`): `import niagara.sys.Context;`.
2. **`doPost(WebOp op)`** (`BDashboardServlet.java:156-157`) — recover the attribute BEFORE dispatching
   to the write handler:
   ```java
   Context cx = (Context) req.getAttribute("niagara.context");
   handleSetpointWrite(req, resp, cx);
   ```
3. **`handleSetpointWrite`** — signature extended with a third parameter
   (`BDashboardServlet.java:212`: `private void handleSetpointWrite(HttpServletRequest req,
   HttpServletResponse resp, Context cx)`), and the write call itself changed
   (`BDashboardServlet.java:308`): `parent.set(prop, toSet, null);` → `parent.set(prop, toSet, cx);`.

No other line in the module changed. `DashboardRbacHelper.checkCanWrite(req, resp)` — the RBAC guard
that must run first — is untouched and still runs before `cx` is ever used, so behavior for an
unauthenticated (`401`) or under-privileged (`403`) caller is identical to before: `cx` is only reached
by a request that already passed the `OPERATOR_WRITE` check via an independent `BUserService` lookup
(§41-unrelated path, [Block 28]/this PoC's own RBAC design, not the `ComponentSlotMap` gate). File grew
from 612 to 629 lines (+17: 1 import, 1 doc comment block, 1 local-variable line, 1 parameter, 1
call-site argument change). `[CERT-hw]` (file read before and after the edit this session).

## 46.4 — Build result and bytecode confirmation `[CERT-hw]`

**Attempt log** (2 real `gradlew` invocations this session, from
`/home/cristian/niagara5-research/poc/dashboardpan-n5`):

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew :DashboardPan-rt:jar --console=plain` (ambient `java` = Homebrew OpenJDK 21) | **FAILED** — `Could not resolve com.tridium.tools:settings:5.0.9.8.14 ... Dependency requires at least JVM runtime version 25. This build uses a Java 21 JVM.` A gradle-DAEMON toolchain mismatch (the wrapper process itself, distinct from [Block 28]'s `org.gradle.java.installations.paths` compile-toolchain property, which only pins the JDK gradle hands to `compileJava`) — never reached `compileJava`, so this is not a code-level failure. |
| 2 | `JAVA_HOME=/home/linuxbrew/.linuxbrew/opt/openjdk@25 ./gradlew :DashboardPan-rt:jar --console=plain` | **BUILD SUCCESSFUL in 3m 18s** — `compileJava`→`processResources` (NO-SOURCE)→`classes`→`writeModuleXml` (UP-TO-DATE)→`jar`, 3 actionable tasks (2 executed, 1 up-to-date). |

`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` re-counted before attempt 1 and again
after attempt 2's success: **247 both times** `[CERT-hw]`. The 5 stub module jars [Block 28] §28.4
needed for `niagara.alarm`'s transitive JavaFX/Batik graph were already present in this PoC's local
`.n5config/modules/` mirror from that prior session (confirmed present, `ls`, this session) — this
fix touches none of that machinery and needed no new stubs.

**`jarsigner -verify`** on the rebuilt `build/libs/DashboardPan-rt.jar`: `jar verified.` (self-signed
warnings only — same reused keystore as [Block 28], not a failure). 30 entries, identical count to
[Block 28] §28.7's original build (this fix changes code inside one existing `.class` file, not the
entry set).

**`javap -p -c`** on the rebuilt `com/angeles/DashboardPan/ux/BDashboardServlet.class` (extracted from
the jar this session) confirms the fix at the bytecode level, not merely in source text:

```
public void doPost(niagara.web.WebOp) throws java.io.IOException;
    ...
        73: aload_2
        74: ldc           #100    // String niagara.context
        76: invokeinterface #102,  2  // HttpServletRequest.getAttribute:(Ljava/lang/String;)Ljava/lang/Object;
        81: checkcast     #106    // class niagara/sys/Context
        84: astore        8
        86: aload_0
        87: aload_2
        88: aload_3
        89: aload         8
        91: invokevirtual #108    // Method handleSetpointWrite:(Ljakarta/servlet/http/HttpServletRequest;Ljakarta/servlet/http/HttpServletResponse;Lniagara/sys/Context;)V
```
`[CERT-hw]` — `doPost` literally reads `"niagara.context"` off the request and casts it to `Context`
before calling `handleSetpointWrite`, matching §46.3's source exactly, not a compiler no-op. And inside
`handleSetpointWrite` itself:
```
private void handleSetpointWrite(...HttpServletRequest, HttpServletResponse, niagara.sys.Context) ...;
       468: aload         17
       470: aload         10
       472: invokestatic  #292    // Method coerceValue:(Lniagara/sys/BValue;Ljava/lang/String;)Lniagara/sys/BValue;
       475: astore        19
       477: aload         15
       479: aload         16
       481: aload         19
       483: aload_3
       484: invokevirtual #296    // Method niagara/sys/BComponent.set:(Lniagara/sys/Property;Lniagara/sys/BValue;Lniagara/sys/Context;)V
```
`[CERT-hw]` — offset `483: aload_3` loads local-variable slot 3, which for this instance method's
parameter layout (`this`=0, `req`=1, `resp`=2, `cx`=3) is the `cx` parameter, immediately before the
`set(...)` invocation. This is the decisive check: the OLD compiled bytecode (before this session's
edit, per [Block 28]'s already-built jar, not re-disassembled here since the source diff at
`BDashboardServlet.java:291` unambiguously read `null`) would show `aconst_null` at this position
instead of `aload_3` — a real, compiler-verified difference between "pass nothing" and "pass the
caller's actual Context object", not just a source-level claim.

## 46.5 — What this fix does NOT reach, and why `[CERT]`+`[INFER]`

**The self-rolled `auditLog` ring (§46.1 row 2) is left untouched, deliberately.** Threading `cx` into
`setAuditLog` (via `BComplex.set`, generated) would make EVERY successful setpoint write additionally
fire a SECOND `AuditEvent` — one for the config slot itself (now fixed, §46.3), and one for the
module's own append-only `auditLog` string slot changing underneath it (since the running station's
root `BComponentSpace` already carries `@AuditableSpace` unconditionally, [Block 41] §41.2). That
second event would be pure internal noise in `$/AuditHistory` (the `auditLog` property is a serialized
JSON-lines blob, not a human-meaningful config value), and the fix would require editing
**Slot-o-Matic-generated code** (`setAuditLog(String v) { setString(auditLog, v, null); }` at
`BDashboardService.java:218`, regenerated on every build from the `@NiagaraProperty` annotation) rather
than hand-written logic — the same `null`-Context pattern appears on **every** generated property
setter in **every** Niagara module (`BWebServlet.setServletName`, `organized/web/vineflower/niagara/web/
BWebServlet.java:38-40`, is the identical pattern on a completely different module, confirmed this
session). `[INFER]`: fixing this systemically is a framework-wide question (whether `@NiagaraProperty`
setters should accept an optional `Context` overload), not a DashboardPan-specific defect — named
**B46-G1** below rather than attempted here.

**No `invoke(Action, ...)` call exists in this module** (§46.1) — the value-diff fix [Block 41] §41.1
documented for `BIActionAuditProvider`/`getOldValueForPendingActionAuditEvent` (the four
`niagara.control` writable-point types) is therefore **not directly exercisable** through
DashboardPan's own servlet: the facade writes raw component properties via `set()`, not through an
`override`/`auto`/`set` ACTION on a `BNumericWritable`-family point. This is a genuine scope note, not
a gap in this fix — §46.3's `set(...)` fix is the correct and complete mechanism for THIS module's
actual write shape.

## 46.6 — Optional hardening noted, not implemented: `x-niagara-csrfToken` `[CERT]` (note only)

Per this task's explicit instruction, this is recorded but **not implemented**. [Block 27] §27.6
found N5 ships a real synchronizer-token CSRF primitive (`niagara.web.CsrfUtil`,
`CSRF_TOKEN_HTTP_HEADER = "x-niagara-csrfToken"`, verified against the session's stored token) mapped
narrowly to 4 built-in URL patterns (`/logout`, `/file/*`, `/rpc/*`, `/niagaraSpeedTest/*`) — NOT to a
third-party module's own servlet path like `/dashboardpan/*`. `DashboardDispatch`/`BDashboardServlet`
in this PoC use no CSRF guard of any kind (confirmed by grep this session: zero hits for
`X-Requested-With`, `csrfToken`, or `CsrfUtil` anywhere in the ported source) — narrower than even the
hand-rolled `X-Requested-With` pattern [Block 27] §27.6 found in the broader N4 corpus for sibling
modules (chihuahua). Moving to the real `x-niagara-csrfToken` header would require the frontend
(`rc/index.html`, 3.6MB, unmodified static HTML) to read the token from its session and attach it to
the `POST /api/setpoint` call, plus a server-side `CsrfUtil`-based check in `handleSetpointWrite` before
`checkCanWrite` — a strictly separate, larger change than this block's Context-threading fix, correctly
out of scope per the task's own instruction. Named **B46-G2** below.

## 46.7 — Self-verification

**Token check.** Every load-bearing citation was read/grepped directly this session (not
hand-recalled): `BDashboardServlet.java` before-state (`parent.set(prop, toSet, null)` at line 291,
pre-edit) and after-state (lines 10, 156-157, 212, 308, all re-confirmed post-edit); `BWebServlet.java`
`doService`/`doGet`/`doPost` (`:70-125`, read fresh); `WebOp.java:111`; `Context.java` (full interface,
137 lines); `BComplex.java:396-406` (`set` overloads); `BDashboardService.java:196-220` (the generated
`auditLog` property block) and `:265-271` (`appendAudit`); the full-file `grep` inventory across all 8
ported source files (§46.1); 2 `gradlew` invocations' full console output; `jarsigner -verify` output;
`javap -p -c` disassembly (2 method bodies read: `doPost`, `handleSetpointWrite`) — **≈22 distinct
load-bearing tokens/citations, all sourced from this session's own reads or command output, 0 absent,
0 downgraded**.

**Marker tally — mechanized, literal `verify-block.sh` output:**

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block46.md .
== verify-block: niagara5-block46.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 8  (adj 6)
   [CERT-live] 0
   [CERT] 12  (adj 11)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 3  (adj 2)
-- ratio -- [INFER]/[CERT*] = 2/17 = 0.12
-- [CERT] file:line citation resolution --
   extern  BComplex.java:396-406 / BDashboardService.java:196-220 / BDashboardService.java:218 /
           BDashboardServlet.java:{10,156-157,212,291,308} / BWebServlet.java:99-125 /
           ContextFilter.java:16-26 / WebOp.java:111  (short-form citations into the PoC tree and the
           N4 corpus — not this corpus's own `organized/` layout, so the script cannot resolve them;
           the token-check above confirms every one by direct read this session, same convention
           [Block 41]/[Block 28] established for decompiled-tree/PoC-tree blocks)
   ok      organized/baja/vineflower/niagara/sys/BComplex.java:400
   ok      organized/web/vineflower/niagara/web/BWebServlet.java:70-92  (range end verified; file has 195 lines)
   ok      organized/web/vineflower/niagara/web/WebOp.java:111
   resolved 3 of 14
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

Adjusted `[INFER]`/`[CERT*]` ratio = **0.12** — low, consistent with a §19 build/PoC block whose claims
are almost entirely direct source-read/`[CERT-hw]` bytecode/build output; the 2 adjusted `[INFER]`
claims are both explicitly bounded (§46.2's "still present and unchanged" request-attribute-lifetime
deduction, §46.5's systemic-framework-pattern scope note). **Citation resolution `resolved 3 of 14`**
is the expected signature: the 3 `ok` rows are this corpus's own pre-existing `organized/...`
decompile paths (the fully-qualified form the script can resolve); the 11 `extern` rows are short-form
citations into (a) the PoC tree `poc/dashboardpan-n5/...` — a sibling directory this script's
`SOURCE_ROOT` does not walk — and (b) two already-`organized/`-qualified N5 files cited by short
basename instead of the full path in the running prose (`BWebServlet.java:99-125`,
`ContextFilter.java:16-26`) — a citation-FORMAT gap, not a missing-source gap, matching [Block 41]
§41.9's identical finding on this same corpus/tooling. Every `extern` row was read directly this
session (Token check above).

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block46.md`. The
edited PoC file exists at `poc/dashboardpan-n5/DashboardPan-rt/src/com/angeles/DashboardPan/ux/
BDashboardServlet.java` (629 lines, up from 612). The rebuilt, re-signed jar exists at
`poc/dashboardpan-n5/DashboardPan-rt/build/libs/DashboardPan-rt.jar` (30 entries, `jarsigner -verify` →
`jar verified.`). Per task scope (single-block deliverable, no commit, original N4 client sources
untouched, `/mnt/c` untouched — 247 jars before and after), `CATALOG.md`/`INDEX.md`/
`RESEARCH-STATE.md` were **not** regenerated this session — flagged here for the next
iteration/orchestrator to pick up, same disclosure [Block 27]/[Block 28] made.

**MCP-doc snapshots.** N/A — no MCP/context7/web citation used.

## 46.8 — Child gaps

- **B46-G1** — Whether `@NiagaraProperty`-generated setters (`setXxx(v) { setString(prop, v, null); }`
  pattern, confirmed identical on `BDashboardService.setAuditLog` and, in a completely different
  module, `BWebServlet.setServletName`) should have a `Context`-accepting overload generated
  alongside the no-Context convenience one — a framework-wide Slot-o-Matic question, not a
  DashboardPan-specific fix; genuinely out of this PoC's reach (regenerated code, not hand-editable).
  `investigable` (would need reading the Slot-o-Matic code-generation templates, not yet opened in
  this corpus).
- **B46-G2** — Implementing the `x-niagara-csrfToken` synchronizer-token check (§46.6) on
  `POST /api/setpoint`, replacing the module's current total absence of any CSRF guard — noted per
  task instruction, not implemented this session. `investigable` — the mechanism ([Block 27] §27.6) is
  already fully documented; this is an implementation gap, not a research gap.
- **B46-G3** — Whether the 3 read-side `BOrd.make(...).get(this, null)` calls (§46.1, resolving
  `parentOrd`/`SERVICE_ORD`/an alarm-record ORD) should also receive the real `cx` for
  permission-scoped ORD resolution (a DIFFERENT concern than audit — whether resolution itself
  respects the caller's read permissions rather than the servlet component's own ambient identity) —
  not traced this session; `BObject.get(BObject base, Context cx)`'s own resolution-permission
  semantics were not opened. `investigable`.
- **B46-G4** — Live confirmation (`[CERT-hw]`): stand up an N5 5.0.0.28 station, deploy this PoC's
  rebuilt `DashboardPan-rt.jar`, perform a `POST /api/setpoint` write as a web-authenticated
  OPERATOR_WRITE user, and read back `$/AuditHistory` to confirm a `Changed`/`AuditEvent` now appears
  attributed to that user — the bytecode confirmation (§46.4) proves the CALL now carries a non-null
  Context object; it does not prove that object survives to a persisted `BAuditRecord` on a real
  running station. `blocked-on-source` — no runnable N5 station this session, same blocker as [Block
  41]'s **B41-G4** and [Block 28]'s **B28-G4** (no live deploy attempted for either module).
- **B46-G5** — Porting this exact fix back into the real N4 client source
  (`modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249/Dashboard/DashboardPan/
  DashboardPan-ux/`) was explicitly out of scope for this task (PoC-only, original client sources never
  modified) — the N4 codebase still has the identical `null`-Context write B829/B830 found, unfixed.
  `investigable` (mechanical — the same 3-line change, on the N4 source, pending explicit
  authorization to modify client sources).

## 46.x — Connections

- **[Block 41]** — this block closes **B41-G6**: §41.4/§41.7 established the mechanism (`ContextFilter`
  populates `"niagara.context"`; `ComponentSlotMap`/`ComplexSlotMap` gate on
  `context != null && context.getUser() != null`) exists and is available to a `BWebServlet` subclass,
  but explicitly left "whether DashboardPan's own servlet threads it through" unverified (out of that
  block's scope, since it was reading platform source, not the third-party module). This block reads
  the module, finds it did NOT (the exact N4-carried-forward gap B829/B830 named), and fixes it in the
  PoC copy, confirmed by bytecode. §41.1's `BIActionAuditProvider` value-diff mechanism remains
  unreached by this module (§46.5 — no `invoke()` call exists here), a genuine scope boundary, not an
  oversight.
- **[Block 28]** — this block edits and rebuilds the exact PoC [Block 28] ported
  (`poc/dashboardpan-n5/DashboardPan-rt/`), reusing its build recipe unchanged (same
  `niagara_config_home` local-mirror redirect, same JDK 25 toolchain, same 247-jars-before-and-after
  discipline) — confirming the recipe is stable across a second, much smaller, source-only change (no
  new stub modules, no dependency changes, `compileJava`→`jar` succeeded without touching §28.4's
  `niagara.alarm`/JavaFX machinery at all).
- **[Block 27]** — §27.6's CSRF finding (`x-niagara-csrfToken`, narrowly filter-mapped, NOT covering
  `/dashboardpan/*`) is confirmed still true for this module and noted as optional hardening (§46.6,
  **B46-G2**) per this task's explicit instruction not to implement it.
- **N4 corpus (remit)** — **[B829]**/**[B830]** (the original N4 finding this whole chain traces: a
  null-Context servlet write is silently unaudited) — this block is the first in either corpus to
  actually APPLY a fix and prove it compiles and reaches the right call site at the bytecode level,
  though live-station confirmation remains open (**B46-G4**) and the N4 source itself remains unfixed
  by design (**B46-G5**).
