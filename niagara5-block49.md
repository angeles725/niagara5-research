# Block 49 — Which N5 writes get audited: generated setters, Fox/BajaScript commit paths and the Context rule

> Research closing **B46-G1**: whether Slotomatic-generated setters/invokers (`setXxx(v) { setString(prop,
> v, null); }` — [Block 46] §46.5) should carry a `Context`-accepting overload, whether Tridium's own
> user-facing write paths (Fox/Workbench, BajaScript/web, `@NiagaraRpc`) route through those generated
> members or bypass them, and which N5 write shapes therefore end up audited vs silently unaudited. Covers:
> (1) full reading of the Slotomatic property/action code generators (`PropertyProcessor`, `ActionProcessor`)
> to settle whether a second, `Context`-taking overload is ever emitted; (2) a whole-corpus census of
> generated setters/invokers and of the hand-written call sites in Fox, BajaScript/BOX, and `@NiagaraRpc`
> that write through `set(prop, value, cx)`/`invoke(action, arg, cx)` with a real `Context`; (3) the
> resulting classification of which N5 write shapes are audited today and the recommended pattern for
> third-party module code, compared against the N4 corpus's B829/B830 finding. Does **not** cover: opening
> the `com.github.javaparser`-based comment-syntax generators (legacy pre-annotation Baja-comment slot
> declarations — a third, older code path Slotomatic still supports per [Block 7] §7.4, not used by any
> `@NiagaraProperty`/`@NiagaraAction` class and therefore out of this gap's scope); a live-station
> `$/AuditHistory` readback for a Fox or BOX write (no runnable N5 station this session — same constraint
> as [Block 41]'s **B41-G4**/[Block 46]'s **B46-G4**); re-deriving N4's own Slotomatic generator source
> (out of scope — this is an N5-focus block; the N4 comparison uses the existing corpus REMIT only, per
> task instruction).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as Blocks 7/27/28/41/46
> (`etc/brand.properties:workbench.notice`). The Slotomatic generator source read this session
> (`com.tridium.slottool.processor.{PropertyProcessor,ActionProcessor}`) is the SAME already-decompiled
> tree [Block 7] produced this corpus's session (`tridium-niagara-slotomatic-library-5.0.2.jar`,
> [Block 7]'s own sourcing) — re-read fresh this session from its scratch location, not re-decompiled. All
> other citations are this corpus's own pre-existing `organized/*/vineflower/` decompiled trees ([Block 1]'s
> corpus-wide extraction), read fresh this session; nothing was re-decompiled and no new tool run beyond
> `grep`/`find`/direct file reads.
>
> Sources:
> - `com/tridium/slottool/processor/{PropertyProcessor,ActionProcessor}.java` — the property/action code
>   generators, read in full this session (locations: [Block 7]'s decompile scratch tree, path recorded in
>   §49.1).
> - `organized/{baja,web,box,fox,bajaScript,bql}/vineflower/...` — whole-tree `grep`/direct reads this
>   session: `niagara/sync/{SyncBuffer,SetOp}.java` (full reads), `com/tridium/box/{BComponentSpaceSessionHandler,
>   BBoxServlet,BoxOp}.java` (full/partial reads), `com/tridium/fox/sys/broker/BBrokerChannel.java`
>   (partial, targeted reads, extending [Block 46] §46.2's own partial read of this file's `Context`
>   plumbing), `niagara/sys/BasicContext.java` (partial), `niagara/web/WebOp.java` +
>   `com/tridium/util/SecurableContext.java` (partial), `com/tridium/web/{rpc/BPasswordRpc.java,
>   servlets/OrdServlet.java}` (partial, targeted reads).
> - [Block 41] §41.1–§41.4, §41.7 (REMIT, not re-derived: the `ComponentSlotMap`/`ComplexSlotMap` audit
>   gate `context != null && context.getUser() != null`; `ContextFilter`'s `"niagara.context"` request
>   attribute) and [Block 46] §46.1–§46.5 (REMIT: the exact generated-setter pattern this block traces to
>   its source, and the named child gap **B46-G1** this block closes).
> - [Block 7] §7.4/§7.4.1 (REMIT: `SlotGenerator`/`Constants`/`SlotMode` — the marker-text and mode-dispatch
>   layer this block's `PropertyProcessor`/`ActionProcessor` read sits directly underneath) and [Block 36]/
>   [Block 512]/[Block 869] REMIT via the sibling N4 corpus (`SetOp`, `BoxOp`, the BOX wire — cited to show
>   this block's N5 finding is architecturally the SAME mechanism the N4 corpus already named structurally,
>   not a newly-invented one) and [Block 613] REMIT via the sibling N4 corpus (`@NiagaraRpc`
>   Context-injection contract, `NiagaraRpcServlet`/`NiagaraRpcUtil.rpc(...)`).
> - N4 corpus `B829`/`B830` (REMIT, via `python3 tools/corpus-nav.py find "B829"` this session, sibling
>   corpus `/home/cristian/niagara-research`) — the audit-gate finding [Block 41] §41.4 already confirmed
>   architecturally unchanged in N5.
>
> Method: direct reading of the Slotomatic property/action generator source (settling the literal
> "does a Context overload exist" question by exhaustive code inspection, not inference), whole-tree `grep`
> census across every already-organized N5 decompiled module for the generated-setter pattern and for
> hand-written `set(...)/invoke(...)` call sites passing a Context-typed third argument, and one
> `corpus-nav.py` REMIT lookup into the sibling N4 corpus for the N4 comparison the task named explicitly.
> No fresh decompilation. Markers: `[CERT]` a source file read/grepped directly this session ·
> `[CERT-hw]` — none this block (no build/bytecode/probe run) · `[INFER]` deduction ·
> the corpus-nav `B829`/`B613`/`B36`/`B512`/`B869` hits are REMIT (cited, not re-derived).
>
> N5 build-toolchain/code-generation layer + web/Fox/BOX RPC transport layer. Connects [Block 46] (closes
> the named child gap **B46-G1**), [Block 41] (extends §41.4's audit-gate finding with the missing
> mechanistic link: WHY Workbench/web-UI edits end up audited while a hand-rolled third-party servlet does
> not), [Block 7] (the generator machinery this block reads one layer deeper), and the N4 corpus's B829/
> B830/B613/B36/B512/B869 (comparison REMIT).
>
> **Type:** standard (evidence)
>
> **Breakthrough:** Slotomatic's `PropertyProcessor`/`ActionProcessor` emit **exactly one** signature per
> slot — `setXxx(Type v) { set<Kind>(prop, v, null); }` / `name(Params) { invoke(action, arg, null); }` —
> with **no `Context`-taking overload ever generated**, confirmed by reading the full switch/branch logic
> of both generators (every one of 7 `PropertyProcessor` type branches and the single `ActionProcessor`
> code path hardcode the literal token `null` as the third argument; §49.1). Separately, and answering the
> literal "does Tridium route user writes through `set(prop, value, cx)` instead" question: **yes** — three
> independent, hand-written N5 subsystems (Fox's `syncToMaster`/`invoke` RPC handlers, BOX's
> `BComponentSpaceSessionHandler.{syncToMaster,invokeAction}`, and the `@NiagaraRpc` Context-injection
> contract) all call the raw `BComplex.set(Property, BValue, Context)` / `BComponent.invoke(Action, BValue,
> Context)` overloads directly with a REAL per-session/per-request `Context` recovered from the same
> `"niagara.context"`/`WebOp`/session-context chain [Block 41] §41.7 documented — never through the
> generated convenience members. The property-write case funnels through one shared class both transports
> reuse unmodified: `niagara.sync.SetOp.commit()` (`target.set(property, value, context)`), fed a real
> `Context` by both `BBrokerChannel.getSessionContext()` (Fox) and `BoxOp` (BOX, itself `extends
> BasicContext`, constructed from the servlet's `WebOp`/`"niagara.context"` chain).

---

## 49.1 — The Slotomatic generators: literal code, no Context overload exists `[CERT]`

**`PropertyProcessor.accept(Property property)`** (full method read this session,
`com/tridium/slottool/processor/PropertyProcessor.java:15-141`, scratch location
`/tmp/claude-1000/n5b7/vf-slotomatic/com/tridium/slottool/processor/PropertyProcessor.java` — the same
already-decompiled Slotomatic jar [Block 7] §7.1/§7.4 sourced, re-read fresh this session, not
re-decompiled). Every one of the 7 `switch(type)` branches builds a `setImpl` string with the literal
third argument `null`, and exactly ONE setter is emitted per property:

| Type branch | Generated `setImpl` (verbatim) | Line |
|---|---|---|
| `BOOLEAN_TYPE`/`BBOOLEAN_TYPE` | `{ setBoolean(NAME, v, null); }` | `:51` |
| `INT_TYPE`/`BINT_TYPE` | `{ setInt(NAME, v, null); }` | `:58` |
| `LONG_TYPE`/`BLONG_TYPE` | `{ setLong(NAME, v, null); }` | `:65` |
| `FLOAT_TYPE`/`BFLOAT_TYPE` | `{ setFloat(NAME, v, null); }` | `:72` |
| `DOUBLE_TYPE`/`BDOUBLE_TYPE` | `{ setDouble(NAME, v, null); }` | `:79` |
| `STRING_TYPE`/`BSTRING_TYPE` | `{ setString(NAME, v, null); }` | `:89` |
| `BVALUE_TYPE` / default | `{ set(NAME, v, null); }` | `:93`, `:97` |

`[CERT]` (whole `switch` block, `PropertyProcessor.java:45-98`). The ONE public method actually printed
is fixed at `:137`: `this.cg.println("public void " + setter + "(" + typeName + " v) " + setImpl);` —
**a single-parameter signature, unconditionally**. There is no second `cg.println` call anywhere in this
method that would emit a `(TYPE v, Context cx)` overload, no branch on a `slotomaticOptions` flag that
would enable one, and no other generator class in the `processor`/`generator` packages emits property
setters (`PropertyProcessor` is the sole property-accessor generator; [Block 7] §7.4.1 already established
`SlotMode`/`SlotGenerator` only dispatch INTO this class, they do not themselves emit accessor bodies).
**Answer to B46-G1 part 1: no, Slotomatic never emits a Context-taking setter overload — the getter/setter
pair per property is always exactly the one no-Context signature.** `[CERT]`.

**`ActionProcessor.generateActionInvoke(Action action)`** (full method read this session,
`processor/ActionProcessor.java:63-97`, same scratch tree) — identical pattern for actions: the generated
invoke wrapper's body is built at `:92-95` as `"invoke(" + name + ", " + <arg-or-"null"> + ", null); }"` —
the literal string `", null); }"` is hardcoded at `:95` regardless of the action's parameter type,
producing e.g. `public void reset() { invoke(reset, null, null); }` or `public void override(BStatusValue
parameter) { invoke(override, parameter, null); }` — **one signature, Context argument always `null`, no
overload.** `[CERT]`. This is the exact mechanism underlying [Block 41] §41.1's `ComponentSlotMap.invoke`
finding from the CALLER side: a component's own generated `override(...)`/`reset()` convenience method,
if called directly (in-JVM, no external actor), always invokes with a `null` Context — audited only if
SOME caller further up the stack used the 3-argument `invoke(Action, BValue, Context)` form instead.

## 49.2 — Census: generated setters across the whole N5 decompiled corpus `[CERT]`

Whole-`organized/`-tree `grep` this session (every already-decompiled N5 module, all `vineflower/`
subtrees, not limited to any one module):

| Metric | Count | Method |
|---|---|---|
| Files containing a `BAJA AUTO GENERATED CODE` region | **1,893** | `grep -rl "BEGIN BAJA AUTO GENERATED CODE" --include="*.java" .` |
| Generated setter methods matching the exact `set<Kind>(prop, v, null)` pattern | **3,589** | `grep -rhoE 'public void set[A-Za-z0-9_]+\([A-Za-z0-9_.\[\]<>]+ v\) \{ set[A-Za-z]*\(...,v,null\); \}'` |

`[CERT]` (both commands run this session, `organized/` as CWD; sample hits: `setErrorLimit`,
`setExtensionName`, `setPropagateFlags` across unrelated modules — the pattern §49.1 traced to source is
confirmed to be the actual on-disk shape everywhere, not a hypothetical reading of the generator alone).
**Every one of these 3,589 generated setters is unaudited if called directly** (§49.1's `null`), which is
the literal scale of B46-G1's premise: this is not a DashboardPan-specific idiom, it is the universal
shape of every `@NiagaraProperty` accessor in the whole platform + every third-party module built against
it.

## 49.3 — Fox: `SetOp`/`invoke` server handlers thread the real session `Context`, bypassing the generated setter entirely `[CERT]`

`com/tridium/fox/sys/broker/BBrokerChannel.java` (server-side Fox request dispatch, the channel Workbench
talks to) has two relevant handlers, both re-read this session extending [Block 46] §46.2's own partial
read of this same file:

**Action invoke** (`private FoxResponse invoke(FoxRequest req)`, `:1265-1281`):
```java
BComponent comp = this.fromOrd(ord);
Action action = comp.getAction(actionName);
Context cx = this.getSessionContext();
BValue ret = comp.invoke(action, arg, cx);
```
`[CERT]` `BBrokerChannel.java:1276-1282`. This calls the RAW 3-argument `BComponent.invoke(Action, BValue,
Context)` directly — NOT the generated single-argument convenience wrapper (§49.1) — with `cx =
this.getSessionContext()`, the channel's own per-connection authenticated session Context.

**Property-write commit** (`public void syncToMaster(FoxCircuit circuit)`, `:1597-1625`):
```java
SyncBuffer buf = new SyncBuffer(this.space, false);
buf.decode(in);
Context cx = this.getSessionContext();
buf.commit(cx);
```
`[CERT]` `BBrokerChannel.java:1611-1616`. `buf.commit(Context)` (`niagara/sync/SyncBuffer.java:128-129`,
full method read this session) iterates the decoded `SyncOp[]` and calls `op.commit(this, this.space,
cx)` for each — for a property change, that op is `niagara.sync.SetOp` (full file read this session,
`baja/vineflower/niagara/sync/SetOp.java`), whose `commit()` override is:
```java
void commit(SyncBuffer parent, BComponentSpace space, Context context) throws Exception {
   ...
   this.getTarget().set(this.getProperty(), this.value, context);
}
```
`[CERT]` `SetOp.java:96-102` — the RAW `BComplex.set(Property, BValue, Context)` overload, called with the
SAME real `context` threaded in from `getSessionContext()` above. **A Workbench property-sheet edit over
Fox never touches a generated setter at all** — it is decoded into a `SetOp`, and `SetOp.commit()` calls
the 3-argument `set()` directly with the operator's real session Context, satisfying [Block 41] §41.4's
audit gate (`context != null && context.getUser() != null`) by construction.

## 49.4 — BOX/BajaScript: the identical `SetOp`/`SyncBuffer` machinery, fed a `Context` recovered through the SAME `"niagara.context"` chain a plain servlet uses `[CERT]`

`com/tridium/box/BComponentSpaceSessionHandler.java` (the BOX channel handler behind the BajaScript client
library — `bajaScript`'s own JS source, `resources/rc/baja/boxcs/BoxComponentSpace.js`, confirmed this
session by `grep -rl "commitSet\|\.commit(" resources/rc` to be the client-side counterpart, per [Block 36]
§36.6/§36.9 REMIT) uses the SAME `niagara.sync.SetOp`/`SyncBuffer` classes §49.3 traced, with its own
`BsonSyncBuffer`/`BsonSyncDecoder` wrapper subclasses that add no logic to `commit()`/`SetOp` themselves:

```java
private void syncToMaster(JSONObject body, BoxWriter out, BoxOp op) throws Exception {
   ...
   BsonSyncDecoder in = new BsonSyncDecoder(new BsonDecoderPlugin(body), op);
   BsonSyncBuffer buf = new BsonSyncBuffer(this.space, false);
   buf.decode(in);
   buf.commit(op);              // op IS the Context — see below
   ...
}
```
`[CERT]` `BComponentSpaceSessionHandler.java:767-796`. And the action-invoke handler, symmetric to Fox's:
```java
private void invokeAction(JSONObject body, BoxWriter out, BoxOp op) throws Exception {
   ...
   String remoteAddr = Objects.toString(op.getRemoteAddr(), "");
   Context cx = new BasicContext(op, BFacets.make("remoteAddr", BString.make(remoteAddr)));
   retVal = comp.invoke(action, arg, cx);
```
`[CERT]` `BComponentSpaceSessionHandler.java:404-434`. Both pass `op` — a `BoxOp` — as (or to construct)
the `Context`. Tracing WHERE `op`'s `Context`-ness comes from, this session, closes the chain fully:

1. `BoxOp` `[CERT]` `com/tridium/box/BoxOp.java:17-29`: `public final class BoxOp extends BasicContext
   implements SecurableContext`, constructor `BoxOp(Context cx, boolean isSecure, String remoteAddr) {
   super(cx); ... }` — `BasicContext(Context base)` copies `this.user = base.getUser()`
   (`niagara/sys/BasicContext.java:41-51`, `[CERT]`) — so `BoxOp` inherits whatever `BUser` its input `cx`
   carried.
2. That input `cx` is built in `BBoxServlet.doPost(WebOp op)` `[CERT]` `com/tridium/box/BBoxServlet.java:52-66`:
   `Context cx = new BasicContext(op, facets); ... new BoxOp(cx, req.isSecure(), ...)` — `op` here is a
   `WebOp`, the SAME `WebOp` instance `BWebServlet.doService()` builds per [Block 41] §41.7/[Block 46]
   §46.2.
3. `WebOp` `[CERT]` `niagara/web/WebOp.java:21`: `public abstract class WebOp extends ExportOp implements
   SecurableContext`, and `SecurableContext` `[CERT]` `com/tridium/util/SecurableContext.java:5`: `public
   interface SecurableContext extends Context` — so `WebOp` IS a `Context` (it calls `this.getUser()` on
   itself at `WebOp.java:71`), carrying the same authenticated `BUser` `BWebServlet.doService()` recovered
   from `req.getAttribute("niagara.context")` (`[Block 41]` §41.7, REMIT — not re-derived here).

**Result: `op` in `syncToMaster`/`invokeAction` carries the REAL authenticated `BUser` all the way from
the servlet's `"niagara.context"` attribute through `WebOp` → `BasicContext` → `BoxOp`, and `SetOp.commit()`
(§49.3, shared code) writes with it.** A BajaScript/web-UI property edit or action invocation is therefore
audited by the SAME mechanism as a Fox/Workbench edit, through the SAME shared `SetOp` class, never through
a generated setter.

## 49.5 — A third, framework-formalized path: `@NiagaraRpc` Context injection, and Tridium's own generic `OrdServlet`/`BPasswordRpc` bypass the generated setter the same way `[CERT]`

Two more hand-written, user-facing N5 write sites confirm the pattern is systemic, not limited to the two
RPC transports above:

- **`com/tridium/web/servlets/OrdServlet.java`** — a generic ORD-addressed property-write servlet
  (Tridium's own, not a third-party module): `applyParametersToProperties(Map<String,String> parameters,
  BComponent component, Context cx)` calls `component.set(property, newValue, cx)` at `:148`, where `cx`
  is literally the `NWebOp op` recovered from `req.getAttribute("niagara.op")` at `:68` `[CERT]`
  `OrdServlet.java:68,97,134,148` — the exact per-request recovery pattern [Block 46] §46.3 applied by
  hand to the DashboardPan PoC, confirmed here to be how Tridium's OWN generic property-editing servlet
  already does it.
- **`com/tridium/web/rpc/BPasswordRpc.java`** — a static method annotated
  `@NiagaraRpc(permissions="unrestricted", transports=@Transport(type=TransportType.box))` with a `Context
  cx` **declared as a formal parameter**: `public static void setPassword(String pwd, String slotName,
  String baseOrd, boolean useDefault, Context cx)`, body: `target.set(pwdProp, BPassword.make(pwd, cx),
  cx);` `[CERT]` `BPasswordRpc.java:33-45`. Per the N4 corpus's `@NiagaraRpc` REMIT ([Block 613] §613.1,
  sibling corpus, same annotation/dispatch contract package-renamed `javax.baja.rpc.NiagaraRpc` →
  `niagara.rpc.NiagaraRpc`), the dispatching servlet (`NiagaraRpcServlet`/BOX-transport equivalent)
  INJECTS the real request Context into any `@NiagaraRpc` method whose signature declares a trailing
  `Context` parameter — this is a FRAMEWORK-FORMALIZED third mechanism (distinct from manually recovering
  `"niagara.context"`) for third-party module code to receive a real, audited-write-capable `Context`
  without hand-rolling the servlet-attribute recovery [Block 46] did. Whole-corpus census this session:
  **110 N5 files** use `@NiagaraRpc` (`grep -rl "@NiagaraRpc" --include="*.java" organized/ | wc -l`)
  `[CERT]`.

## 49.6 — Classification: which N5 writes are audited, and the recommended pattern `[CERT]`+`[INFER]`

| Write shape | Context reaching `set()`/`invoke()` | Audited? |
|---|---|---|
| Workbench property-sheet edit (Fox `syncToMaster`) | `BBrokerChannel.getSessionContext()`, real `BUser` | **Yes** `[CERT]` §49.3 |
| Workbench action invoke (Fox `invoke`) | `BBrokerChannel.getSessionContext()`, real `BUser` | **Yes** `[CERT]` §49.3 |
| Web/BajaScript property edit (BOX `syncToMaster`→`SetOp`) | `BoxOp`←`WebOp`←`"niagara.context"`, real `BUser` | **Yes** `[CERT]` §49.4 |
| Web/BajaScript action invoke (BOX `invokeAction`) | `BasicContext(op,...)`, real `BUser` | **Yes** `[CERT]` §49.4 |
| `@NiagaraRpc` method declaring a `Context` parameter | framework-injected, real `BUser` (N4 REMIT [Block 613]) | **Yes** `[INFER]` (N5 injection site itself not traced this session — census only; mechanism REMIT from N4) |
| Tridium's own `OrdServlet` (generic property-write servlet) | `NWebOp op` from `"niagara.op"` request attribute | **Yes** `[CERT]` §49.5 |
| A component's own generated convenience setter/invoker, called directly | `null` (hardcoded, §49.1) | **No** `[CERT]` — silently, not merely unattributed ([Block 41] §41.4) |
| A hand-written third-party servlet calling `set()`/`invoke()` with `null` (pre-fix DashboardPan) | `null` | **No** `[CERT]` — the exact N4 B829/B830 finding, confirmed unchanged in N5 by [Block 41] §41.4 and fixed in the PoC by [Block 46] |

`[INFER]`: the dividing line is not "web vs. Workbench vs. programmatic" but **whether the call site is
part of one of Tridium's own request-scoped transports (Fox, BOX, `@NiagaraRpc`) that already recover and
thread a real `Context`, or is hand-written code (third-party module servlet, or in-JVM code invoking a
component's own convenience accessor) that must do so itself and, per [Block 46] §46.1's DashboardPan
finding and this block's §49.2 census, overwhelmingly does not.** The generated setter is not a security
hole by itself — every N5 developer implicitly agrees to write to `set(prop, val, null)` from WITHIN a
component's own logic, where there is no external actor and no Context to thread (station startup, an
internal state-machine transition) — the risk is specifically an external-facing write path (servlet,
custom RPC handler, driver ingest from an untrusted network) that reaches the generated setter or calls
`set()`/`invoke()` with a hand-rolled `null` instead of recovering and threading the real Context. This
mirrors the N4 corpus's finding exactly: `B829` established the FRAMEWORK gate is `context != null &&
context.getUser() != null` for N4 too (same `ComplexSlotMap.set` mechanism, [Block 41] §41.4's confirmed
unchanged-in-N5 finding), and the N4 corpus's own BOX/Fox wire documentation ([Block 36] §36.6/§36.9,
[Block 512], [Block 869]) already names the SAME `SetOp`/`BoxOp` classes this block traced in N5 — this
block's contribution is closing the missing mechanistic step: WHY a Workbench/web-UI edit ends up audited
while a hand-rolled third-party servlet write does not, by reading the actual dispatch code on both sides
of that line for N5, not merely re-asserting the gate exists.

**Recommended pattern for third-party module code** (synthesis, `[INFER]` built from §49.1–§49.5's
`[CERT]` facts): a third-party module's own user-facing write entry point should NOT call the generated
single-argument setter/invoker for a value that originated from an external actor. In order of framework
support:
1. Prefer `@NiagaraRpc` with a declared `Context` parameter (§49.5) where the RPC shape fits — the
   dispatcher injects the real Context, no manual recovery code needed.
2. Otherwise, in a `BWebServlet` subclass, recover `Context cx = (Context) req.getAttribute("niagara.context")`
   (or accept the framework-provided `WebOp`/`NWebOp` directly, per `OrdServlet`'s own pattern, §49.5) and
   call the raw `set(prop, value, cx)` / `invoke(action, arg, cx)` overloads explicitly — the exact fix
   [Block 46] §46.3 applied to the DashboardPan PoC, now shown to match Tridium's OWN `OrdServlet`
   convention rather than being an ad hoc workaround.
3. Reserve the generated single-argument convenience setter/invoker for genuinely internal, in-JVM state
   transitions with no external actor and no Context to thread.

## 49.7 — Self-verification

**Token check.** Every load-bearing citation was read/grepped directly this session (not hand-recalled):
`PropertyProcessor.java` (whole 150-line file, all 7 type branches + the single `println` call site) and
`ActionProcessor.java` (whole 159-line file, `generateActionInvoke` in full); the 2 whole-corpus `grep`
census commands (§49.2, both run against `organized/` this session, counts pasted verbatim); `BBrokerChannel.java`
`invoke(FoxRequest)` (`:1265-1281`) and `syncToMaster(FoxCircuit)` (`:1597-1625`); `SyncBuffer.java`
`commit(Context)`/`startCommit` (`:114-129`, full method); `SetOp.java` (whole 161-line file, `commit()`
at `:95-102`); `BComponentSpaceSessionHandler.java` `invokeAction` (`:404-434`) and `syncToMaster`
(`:767-796`); `BoxOp.java` (`:1-45`, class decl + constructor); `BBoxServlet.java` (`:1-70`, whole
`doPost`); `WebOp.java:21` (class decl) + `SecurableContext.java` (whole 6-line file); `BasicContext.java`
(`:41-64`, the 2 relevant constructors); `OrdServlet.java` (`:68,97,134,148`); `BPasswordRpc.java` (`:1-50`);
the `@NiagaraRpc` census `grep`; the `corpus-nav.py find "B829"`/`"SetOp"`/`"BoxOp"`/`"getSessionContext"`/
`"PropertyProcessor"`/`"setImpl"`/`"NiagaraRpc"` REMIT lookups (7 queries, output read in full) — **≈33
distinct load-bearing tokens/citations, all sourced from this session's own reads or command output, 0
absent, 0 downgraded**.

**Marker tally — mechanized, literal `verify-block.sh` output** (run this session from
`/home/cristian/niagara5-research`, matching [Block 41]/[Block 46]'s convention):

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block49.md .
== verify-block: niagara5-block49.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 3  (adj 2)
   [CERT-live] 0
   [CERT] 35  (adj 34)
   [CERT-doc] 1
   [CERT-web] 2
   [CERT-a] 1
   [INFER] 7  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/40 = 0.15
-- [CERT] file:line citation resolution --
   synth-ref  [B36] / [B512] / [B613] / [B829] / [B830] / [B869]  (block back-references — not
              file-verifiable)
   extern  (17 citations)  — every N5 `file:line` citation (this corpus's `organized/` decompiled tree
            and the `/tmp/claude-1000/n5b7/vf-slotomatic/...` scratch re-read) and the N4-sibling-corpus
            references, cited short-form or full-path — neither form matches this script's expected
            on-disk layout for this corpus
   resolved 0 of 17
   WARN    resolved 0 of 17 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```

The raw `[CERT-hw]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` non-zero counts are **not** claims in this block's
body — this block cites zero hardware/doc/web/forum sources (pure decompiled-source read plus one
`corpus-nav.py` REMIT lookup). They are the tool over-counting this self-verify section's own prose and the
block-header legend, which names those marker tokens in backticks while stating "0 this block" — the same
RAW-vs-ADJUSTED distortion [Block 41] §41.9 documented for a block whose own prose discusses the marker
vocabulary. The **adjusted** `[INFER]`/`[CERT]` ratio of **0.15** is the usable number: low, consistent
with an evidence block whose central claims are direct generator-source reads (§49.1) and direct
dispatch-code reads (§49.3–§49.5), with a bounded synthesis tail (§49.6's dividing-line paragraph and its
3-item recommended-pattern list, plus the `@NiagaraRpc`-injection-site `[INFER]` flagged as **B49-G2**).

**Citation resolution.** `resolved 0 of 17` is the **expected signature for a decompiled-tree block**
(METHODOLOGY §11's explicit convention, matching [Block 41] §41.9's and [Block 46] §46.7's identical
signature on this same corpus): every N5 citation points into `organized/*/vineflower/...` (this corpus's
own pre-existing decompiled tree) or the `/tmp/claude-1000/n5b7/vf-slotomatic/...` scratch tree ([Block 7]'s
own decompile output, re-read not re-decompiled) — the script's resolver does not match either short-form
(`WebOp.java:21`) or fully-qualified (`niagara/web/WebOp.java:21`) citations against files at those paths,
a citation-FORMAT gap, not a missing-source gap (every cited path was confirmed to exist and was read
directly this session; see Token check above). The 6 `synth-ref` rows are legitimately block
back-references (sibling N4 corpus + this corpus's own prior blocks), same convention [Block 41]/[Block 46]
use.

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block49.md`. Per task
scope (single-file deliverable, read-only, no commit), `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were
**not** regenerated this session — flagged here for the next iteration/orchestrator to pick up, same
disclosure [Block 27]/[Block 28]/[Block 41]/[Block 46] each made for this corpus.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 49.8 — Child gaps

- **B49-G1** — Live confirmation (`[CERT-hw]`): on a running N5 5.0.0.28 station, perform (a) a Workbench
  property-sheet edit over Fox and (b) a BajaScript/web-UI property edit over BOX, then read
  `$/AuditHistory` to confirm both produce a `Changed` `AuditEvent` attributed to the real operator — this
  block proves the CALL sites thread a real Context (source-level, §49.3/§49.4); it does not prove the
  full round-trip on a live station. `blocked-on-source` — no runnable N5 station this session, same
  blocker as [Block 41]'s **B41-G4** and [Block 46]'s **B46-G4**.
- **B49-G2** — Trace the actual `@NiagaraRpc` Context-injection call site inside N5's `NiagaraRpcServlet`/
  BOX-transport RPC dispatcher (this block only cited the N4 corpus's [Block 613] REMIT for the injection
  MECHANISM and confirmed the ANNOTATION/method-shape is present and census-counted at 110 files in N5 —
  it did not re-open N5's own `NiagaraRpcServlet`/dispatch-util source to confirm the injection code itself
  is unchanged from N4, the reason §49.6's `@NiagaraRpc` audited-row carries `[INFER]` rather than
  `[CERT]`). `investigable` — the N4 sibling file locations are already named in [Block 613]'s own
  sourcing; the N5 renamed-package equivalents are very likely already present in `organized/web/` per this
  corpus's established package-rename convention, just not opened this session.
- **B49-G3** — Whether a `@NiagaraProperty`/`@NiagaraAction`-style Context-overload COULD be added to
  Slotomatic without breaking the generated-code contract (a genuine framework-design question raised but
  not pursued by [Block 46] §46.5, restated here with the generator internals now fully read, §49.1) — this
  block confirms the CURRENT absence exhaustively but does not evaluate feasibility of a hypothetical
  future overload (e.g. would `newProperty`'s slot metadata need to change, would existing `override`
  properties need regeneration). `investigable` — would require reading `SlotMode`/`Compiler`'s broader
  code-emission contract beyond the two processor classes opened this session.
- **B49-G4** — This block's §49.2 census counted the exact `set<Kind>(prop, v, null)` regex pattern; it did
  not separately census generated ACTION invoke wrappers (`invoke(action, arg, null)`) at the same
  whole-corpus scale — only `ActionProcessor`'s generator source was read (§49.1), not a matching
  whole-tree occurrence count. `investigable` — mechanical, same `grep` technique as §49.2, not run this
  session for time/scope reasons.

## 49.x — Connections

- **[Block 46]** — this block closes **B46-G1**: confirms by direct generator-source read that
  `@NiagaraProperty`-generated setters never carry a Context overload (no ambiguity — the generator's
  `println` call sites are exhaustively enumerated, §49.1), and extends Block 46's PoC-scoped fix into a
  corpus-wide finding: Tridium's OWN Fox/BOX/`@NiagaraRpc`/`OrdServlet` machinery already does exactly what
  Block 46 hand-applied to DashboardPan — recover the real request Context and call the raw
  `set(prop,val,cx)`/`invoke(action,arg,cx)` overload directly, never the generated convenience member.
- **[Block 41]** — extends §41.4's audit-gate finding (`context != null && context.getUser() != null`,
  unchanged from N4) with the missing mechanistic link: this block traces WHERE a real, non-null Context
  actually originates for the two transports that make Workbench/web-UI edits work (`getSessionContext()`
  for Fox, the `"niagara.context"`→`WebOp`→`BasicContext`→`BoxOp` chain for BOX — the SAME chain §41.7
  named generically for "a `BWebServlet` subclass", now traced concretely through Tridium's own BOX
  dispatcher).
- **[Block 7]** — this block reads one layer deeper into the exact generator classes ([Block 7] §7.4.1
  named `PropertyProcessor`/`ActionProcessor`'s existence and general role without reading their branch
  logic; this block opens both in full).
- **N4 corpus (remit)** — **[B829]**/**[B830]** (the audit-gate finding this whole N4→N5 chain traces,
  confirmed structurally identical), **[B613]** (the `@NiagaraRpc` Context-injection contract, cited for
  §49.5's third mechanism), **[B36]**/**[B512]**/**[B869]** (the N4 corpus's own BOX/`SetOp`/`BoxOp` wire
  documentation — confirms this block's N5 finding is the SAME architecture the N4 corpus already named
  structurally, not a new N5 invention; the specific mechanistic claim in §49.3/§49.4 — that `SetOp.commit()`
  is what BOTH Fox and BOX funnel property writes through, fed a real Context — is this block's own
  contribution, not previously stated this explicitly in either corpus).
