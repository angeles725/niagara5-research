# Block 70 — Source-level citation upgrade for N5 control/alarm/kitControl/schedule: the `Action`-typed pattern-switch, an `instanceof`-pattern census, and AMBIG `SequencedCollection` call sites read at source

> Research closing/narrowing four previously-opened child gaps that each named a specific
> bytecode-only or REMIT-level claim and asked for a source-level (`file:line`) re-read once the
> relevant N5 module was decompiled: **B20-G5** ([Block 20] §20.10 — "Decompile N5's
> `control`/`alarm`/`kitControl`/`schedule` modules to source ... so future blocks get real
> `file:line` citations instead of bytecode-only `javap` reads"); **B25-G4** ([Block 25] §25.x —
> read the actual decompiled source of `control.jar`'s `BBooleanWritable`/`BEnumWritable`/
> `BNumericWritable`/`BStringWritable` pattern-switch sites to understand what is being switched
> over, and whether the pattern generalizes to other `B*Writable`-shaped classes); **B25-G1**
> ([Block 25] §25.6 — `instanceof` pattern matching (JEP 394) is bytecode-invisible; sample and
> quantify its adoption from decompiled source); **B25-G2** ([Block 25] §25.9 — classify the 34
> corpus-wide `AMBIG` `Deque`-family `SequencedCollection`-shaped call sites by reading the actual
> call sites, to separate genuine post-21 `SequencedCollection`-typed usage from ordinary pre-21
> `Deque`/`LinkedList` code). Covers: a full read of `organized/{control,alarm,kitControl,
> schedule}/vineflower/` — the four modules [Block 20] examined only via `javap` bytecode and
> [Block 25] only via a corpus-wide `.class`-file parser — for the specific classes/methods those
> two blocks already characterized, now re-verified against real decompiled source; an
> `instanceof`-pattern-matching census (bound vs. unbound occurrences, `.java`-only, comment lines
> excluded) across all four modules; and a targeted read of every `Deque`/`LinkedList`/`ArrayDeque`
> reference found inside the four modules to classify it against [Block 25] §25.9's NEW/AMBIG/OTHER
> taxonomy. Does **not** cover: the remaining ~249 of 253 jars [Block 25] scanned for its 34 AMBIG
> sites (`baja.jar`, `bajaui.jar`, `nre.jar`, `migrator.jar`, `workbench.jar`, `platDaemon.jar`, and
> others are not decompiled to source in this corpus yet — B25-G2 is narrowed here, not closed
> corpus-wide — see child gap); [Block 20]'s other four child gaps (B20-G1 `BCapacity` live
> adjudication, B20-G2 `niagaraSync` deep dive, B20-G3 `BIActionAuditProvider` end-to-end UI
> consumption, B20-G4 history rollover mechanism) — none of those are a citation-upgrade question
> and none are touched here; [Block 25]'s B25-G3 (full-corpus `jdeprscan`) — unrelated to source
> decompilation.
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as [Block 20]/[Block 25]. Decompiled
> sources read this session: `organized/control/vineflower/` (from `control.jar`,
> `jar_sha256=3da9845f…d1f6a4`, 54 classes, Vineflower 1.12.0, `primary_status=ok`, 0 decompile
> failure markers, no CFR fallback — `organized/control/recon.json`), `organized/alarm/vineflower/`
> (`alarm.jar`, `jar_sha256=fb5b21c3…97cc32f`, 422 classes, same decompiler/status —
> `organized/alarm/recon.json`), `organized/kitControl/vineflower/` (`kitControl.jar`,
> `jar_sha256=c79c3520…f04ff8fd5`, 225 classes, same status — `organized/kitControl/recon.json`),
> `organized/schedule/vineflower/` (`schedule.jar`, `jar_sha256=f16ca56f…c365c94311`, 144 classes,
> same status — `organized/schedule/recon.json`). All four `recon.json` files record
> `primary_decompiler=vineflower-1.12.0`, `primary_status=ok`, `fallback_used=false`,
> `decompile_failure_markers=0` — none of these four modules needed the CFR fallback [Block 25]
> §25.14 flagged as necessary for `bajaui.jar` specifically, so no known Vineflower-fidelity caveat
> applies to any source cited below.
>
> Sources: `organized/control/vineflower/niagara/control/{BBooleanWritable.java,BEnumWritable.java,
> BNumericWritable.java,BStringWritable.java,WritableSupport.java,BControlPoint.java}`,
> `organized/control/vineflower/niagara/control/trigger/{BDailyTriggerMode.java,
> BIntervalTriggerMode.java}`; `organized/alarm/vineflower/niagara/alarm/{AlarmSupport.java,
> BAlarmPriorities.java,BAlarmSchema.java,BAlarmDatabase.java}`,
> `organized/alarm/vineflower/com/tridium/alarm/CoalesceUuidOnlyInvocation.java`;
> `organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java`;
> `organized/schedule/vineflower/niagara/schedule/{BAbstractSchedule.java,
> BAbstractScheduleSelector.java,BWeeklySchedule.java}`, `organized/schedule/vineflower/com/
> tridium/schedule/{ExecutionQueue.java,BScheduleSnapshotHandler.java,ScheduleValidator.java,
> ui/BSummary.java}`; `organized/baja/vineflower/niagara/{sys/Action.java,
> security/BIActionAuditProvider.java}` (both already in-corpus from a prior block, re-read this
> session for §70.2's "why a pattern-switch, not a classic switch" question — `Action` turns out to
> be a plain, non-sealed, non-enum interface, see `organized/baja/vineflower/niagara/sys/Action.java:3`
> in §70.2 below). All four `recon.json` files named above (for decompile-status provenance).
>
> Method: whole/partial `file:line` reads of the decompiled sources above (no re-decompilation
> performed — all four modules were already decompiled in this corpus before this session, per
> their `recon.json` timestamps and [Block 25]'s own scratch-jar reads of the same four modules'
> bytecode); two from-scratch Python census scripts written this session
> (`/tmp/claude-1000/.../census_instanceof.py`-equivalent inline script, not preserved — see
> Artifacts in §70.6) doing a line-based regex scan for `instanceof` occurrences over every `.java`
> file in the four modules, classifying each non-comment-line occurrence as **bound** (JEP 394
> pattern form, `instanceof Type identifier`) or **unbound** (classic form, no binding variable);
> and a `grep -rl` sweep for `Deque|LinkedList|ArrayDeque` across the same four modules, followed by
> a manual read of every real hit (excluding the English-word false positive "Dequeue"/"Dequeued")
> to classify against [Block 25] §25.9's NEW/AMBIG/OTHER taxonomy by declared variable type.
> Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) ·
> `[CERT-doc]`/`[CERT-web]`/`[CERT-a]` not used in this block · `[INFER]` deduction, including every
> claim that links a source-level finding here back to a specific numbered site in [Block 20]'s or
> [Block 25]'s own (unpublished-per-site) counts.
>
> Control/alarm/kitControl/schedule runtime layer, citation-upgrade pass. Connects [Block 20]
> (closes B20-G5, and independently re-derives several of its bytecode-level findings from source),
> [Block 25] (closes B25-G4, narrows B25-G1 and B25-G2).
>
> **Type:** `mixed` — every section upgrades a NAMED prior block's bytecode-only (`javap`, REMIT)
> `[CERT]` claim to a source-`file:line` `[CERT]` claim by opening a source that block explicitly
> flagged as unopened/undecompiled (a `[CERT]`-across-a-prior-block source-upgrade, the `mixed`
> trigger per METHODOLOGY §4/§11) — no fresh decompilation, no runtime probe.

---

## 70.1 — Scope recap: what changed since [Block 20] and [Block 25]

[Block 20] read `control`/`alarm`/`kitControl`/`schedule`'s N5 behavior exclusively via `javap -p -c`
bytecode disassembly (§20's own Method paragraph: "N5's control/alarm/kitControl were not
decompiled to source this session; only `history` had a prior decompile in this corpus" — B20-G5).
[Block 25] read the same four modules' `.class` files with a pure-Python constant-pool/attribute
parser for a corpus-wide *feature census* (records, sealed classes, pattern-switch bootstrap
methods, `SequencedCollection` Methodrefs) — also bytecode-only, and explicitly out of scope for
`instanceof` pattern matching (§25.6: "bytecode-invisible... would require decompiled-source
pattern matching"). Between then and this session, all four modules were decompiled to source in
this corpus (`organized/{control,alarm,kitControl,schedule}/vineflower/`, confirmed clean —
`primary_status=ok`, 0 failure markers, no fallback — per each module's `recon.json`, cited in the
header). This block is the source-level re-read those two blocks' own child gaps asked for,
scoped to exactly these four modules — it does not re-scan the other 249 N5 jars.

## 70.2 — B25-G4 CLOSED: the `control.jar` `B*Writable` pattern-switch dispatches on `Action`, a plain non-enum interface — the guard form is structurally forced, not a style choice `[CERT]`

[Block 25] §25.5 found `SwitchBootstraps.typeSwitch` bootstrap sites in exactly 4 classes of
`control.jar` — `BBooleanWritable`, `BEnumWritable`, `BNumericWritable`, `BStringWritable` — and
[Block 20] §20.3 independently found, via bytecode, that all four classes now implement
`BIActionAuditProvider.getOldValueForPendingActionAuditEvent(Action, BValue, Context)`. Reading the
decompiled source confirms these are the **same** method, and shows exactly what is switched over
and why a pattern-switch (not a classic `switch`) was the only way to write it.

**The method, read at source in all four classes** (identical shape, only the `in8`/`in1`-typed
default differs by point type):

```java
public final String getOldValueForPendingActionAuditEvent(Action actionPendingInvocation, BValue actionArg, Context cx) {
   return switch (actionPendingInvocation) {
      case Action a when set.equals(a) -> WritableSupport.toOldValueAuditString(this, fallback, cx);
      case Action a when active.equals(a) || inactive.equals(a) || auto.equals(a) -> WritableSupport.toOldValueAuditString(this, in8, cx);
      case Action a when emergencyActive.equals(a) || emergencyInactive.equals(a) || emergencyAuto.equals(a) -> WritableSupport.toOldValueAuditString(this, in1, cx);
      default -> null;
   };
}
```

`[CERT]` `organized/control/vineflower/niagara/control/BBooleanWritable.java:536-544` (guard names
`active`/`inactive`/`auto`/`emergencyActive`/`emergencyInactive`/`emergencyAuto`, matching its
boolean-point action set); the identical structure with point-type-appropriate guard names at
`organized/control/vineflower/niagara/control/BEnumWritable.java:445-452` (`override`/`auto`/
`emergencyOverride`/`emergencyAuto`), `organized/control/vineflower/niagara/control/
BNumericWritable.java:443-449` (same three-guard shape as `BEnumWritable`), and
`organized/control/vineflower/niagara/control/BStringWritable.java:415-421` (same). All four class
headers declare `implements BIWritablePoint, BIActionAuditProvider, BINiagaraSyncCapableComplex`
`[CERT]` `organized/control/vineflower/niagara/control/BNumericWritable.java:63` /
`organized/control/vineflower/niagara/control/BEnumWritable.java:64` /
`organized/control/vineflower/niagara/control/BStringWritable.java:62` /
`organized/control/vineflower/niagara/control/BBooleanWritable.java:73` — confirming [Block 20]
§20.3's bytecode-read class header at source.

**Why a pattern-switch, not a classic `switch(action)`:** `Action` — the switched-over type — is a
**plain interface**, not an enum and not `sealed`: `[CERT]`
`organized/baja/vineflower/niagara/sys/Action.java:3`, `public interface Action extends Slot`.
Java's classic `switch` statement only
accepts a constant-foldable discriminant (primitive, boxed primitive, `String`, or `enum`); an
arbitrary interface-typed value cannot be switched on at all without the Java 21 pattern-switch
extension (JEP 441/431 area), which permits `case Type binding when <guard>` clauses evaluated in
order with a boolean guard. Each `Action` constant here (`set`, `active`, `override`, `emergencyAuto`,
etc.) is a `public static final Action` instance field created via `newAction(...)` `[CERT]`
`organized/control/vineflower/niagara/control/BNumericWritable.java:101,103,105,107,109` (five
representative constants) — not a compile-time
constant expression, so equality can only be tested with `.equals(a)` inside a guard, never with a
`case set:`-style label. This is the structural reason [Block 25] §25.5's `SwitchBootstraps`
bootstrap appears on exactly these four classes and nowhere else in `control`/`alarm`/`kitControl`/
`schedule` (confirmed by a corpus grep, below): the pattern-switch is the *only* legal way to write
a multi-way dispatch on a non-enum, non-constant reference type in modern Java, not an idiomatic
preference over an if/else chain (an if/else chain would compile identically and is, semantically,
exactly what the pattern-switch desugars to — every `case Action a when G` arm is a bound-but-unused
`a` immediately re-tested by `G`, since the binding itself is never used in any of the four `->`
bodies).

**Generalization check (the second half of B25-G4's ask): does the pattern generalize to other
`B*Writable`-shaped classes?** A corpus grep for the same method name and the same `case Action a
when` shape across all four decompiled modules returns **exactly these four classes and no others**:

```
$ grep -rl "getOldValueForPendingActionAuditEvent" organized/{control,kitControl,alarm,schedule}/vineflower/
organized/control/vineflower/niagara/control/BNumericWritable.java
organized/control/vineflower/niagara/control/BEnumWritable.java
organized/control/vineflower/niagara/control/BBooleanWritable.java
organized/control/vineflower/niagara/control/BStringWritable.java
```

`[CERT]` — no `BStatusValue` point subclass outside these four (no `BBooleanPoint`,
`kitControl.BLoopPoint`, or any alarm/schedule class) implements `BIActionAuditProvider`, at least
within the four modules this block's scope covers. [Block 25] §25.5's own count (33 pattern-switch
sites corpus-wide, only 4 of them in `control.jar`) is therefore consistent with — not contradicted
by — the fact that within `control`/`alarm`/`kitControl`/`schedule` specifically, this one audit-hook
method is the *entire* population of the pattern. Whether any of the other 249 N5 jars this block
does not cover implement the same interface on a different point-family class remains open —
[Block 25] §25.5's per-jar table already answers this at the bytecode level for `nre.jar`,
`platform.jar`, `baja.jar`, `email.jar`, `fox.jar`, `jetty.jar`, `platDaemon.jar` (their own
pattern-switch sites are unrelated dispatch shapes, not `BIActionAuditProvider` — out of this
block's re-verification scope).

## 70.3 — B20-G5 CLOSED (mechanically): fresh `file:line` source citations for the exact classes/methods [Block 20] read only via `javap` bytecode `[CERT]`

All four modules named in B20-G5 are now decompiled and clean (§70.1). This section re-derives, at
source, the same findings [Block 20] reported from bytecode reading — confirming no drift between
the bytecode-level and source-level readings, and giving future blocks real citations to build on.

**`WritableSupport.getActiveLevel()`/`override(BOverride)`** ([Block 20] §20.3, previously cited as
`n5-control/niagara/control/WritableSupport.class` bytecode offsets only):

```java
BPriorityLevel getActiveLevel() {
   return BPriorityLevel.make(this.point.getStatus().geti("activeLevel", 17));
}
```
`[CERT]` `organized/control/vineflower/niagara/control/WritableSupport.java:89-91` — the literal
`17` fallback [Block 20] found in bytecode (`bipush 17`) is now a literal source token, resolving
[B536]'s "ordinal 17, not level 16" finding at source instead of disassembly. The `abstract Property
in1()` … `in16()` declarations are at `[CERT]`
`organized/control/vineflower/niagara/control/WritableSupport.java:32-62` (16 one-line abstract
methods, exact order preserved from N4). `override(BOverride)`'s duration clamp — `[CERT]`
`organized/control/vineflower/niagara/control/WritableSupport.java:188-210` — reads `this.in8()`
for the current value (`:190`) and reproduces
the `desiredDurationMillis<=0L || desiredDurationMillis>maxDurationMillis` clamp Block 20's bytecode
read described (`:204-207`), substituting `maxDuration` unconditionally when either condition holds
— matching bytecode-level §20.3 exactly, now with a readable conditional instead of an opcode
sequence.

**`AlarmSupport.ackAlarm(BAlarmRecord)`** ([Block 20] §20.4, previously cited as `n5-alarm/
niagara/alarm/AlarmSupport.class` `javap -c` output):

```java
public boolean ackAlarm(BAlarmRecord alarm) throws Exception {
   alarm.setAckTime(Clock.time());
   alarm.setAckState(BAckState.acked);
   alarm.setAckRequired(false);
   alarm.setAlarmClass(this.getAlarmClassName());
   if (this.lastTransition == BSourceState.normal && alarm.getSourceState() != BSourceState.normal) {
      alarm.setSourceState(BSourceState.normal);
   }
   boolean validAck = false;
   if (alarm.getAlarmTransition() == BSourceState.offnormal) {
      validAck = this.lastOffnormal == null || alarm.getUuid().equals(this.lastOffnormal.getUuid());
   } else if (alarm.getAlarmTransition() == BSourceState.fault) {
      validAck = this.lastFault == null || alarm.getUuid().equals(this.lastFault.getUuid());
   } else if (alarm.getAlarmTransition() == BSourceState.alert) {
      validAck = this.lastAlert == null || alarm.getUuid().equals(this.lastAlert.getUuid());
   }
   ...
   this.getAlarmService().routeAlarm(alarm);
   return validAck;
}
```
`[CERT]` `organized/alarm/vineflower/niagara/alarm/AlarmSupport.java:172-195` — reproduces exactly
the `setAckTime→setAckState(acked)→setAckRequired(false)→setAlarmClass`, `lastTransition==normal`
guard, and offnormal→fault→alert UUID-equality cascade [Block 20] §20.4 described from bytecode
branch structure. One refinement over [Block 20]'s bytecode reading: the source shows the
`validAck` UUID check tolerates a `null` `lastOffnormal`/`lastFault`/`lastAlert` as trivially valid
(`this.lastX == null || ...`) — a short-circuit `[CERT]` visible at source but not called out at the
opcode level in [Block 20].

**`kitControl.BLoopPoint`** ([Block 20] §20.7, previously cited as bytecode-only class-header and
method-body reads): the class declaration, PID formula, and the `BNiagaraSyncTicks` null-object
first-execution check all resolve cleanly at source.

```java
public class BLoopPoint extends BNumericPoint implements BINiagaraSyncCapableComplex {
```
`[CERT]` `organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:72` — the same
`niagaraSync`-capability marker interface [Block 20] found via `javap -p` class header. The
promoted-to-`Property` state [Block 20] §20.7 described (`errorSum`, `lastExecuteTime`,
`rampEndTicks` moved from private fields to slots) is declared at `[CERT]`
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:64-67`
(`@NiagaraProperty` annotations) and `:115-121` (the generated `Property` static fields), with
`lastExecuteTime`/`rampEndTicks` typed `BNiagaraSyncTicks` exactly as bytecode showed. The PID
formula [Block 20] §20.7 confirmed unchanged from N4's arithmetic is at `[CERT]`
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:462` (`double error =
this.getSetpoint().getValue() - this.getControlledVariable().getValue();`), `:484-486`
(`proportionalGain = error * kProportional`, `integralGain =
kProportional * kIntegral * this.getErrorSum() / 60.0`, `derivativeGain = kProportional *
kDerivative * (error - this.getLastError()) / deltaSecs`) — matching [B537]/[B539]'s N4 formula and
[Block 20]'s bytecode reading term-for-term, now at source. The "first execution" null-object check
[Block 20] §20.7 inferred from bytecode (`getLastExecuteTime().isNull()` replacing N4's `==0L`
sentinel) is confirmed literally at `[CERT]`
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:452`: `if
(this.getLastExecuteTime().isNull()) {`. One detail not visible at the bytecode level: the
replacement tick source is read via a **static factory**, `BNiagaraSyncTicks now =
BNiagaraSyncTicks.now();` `[CERT]`
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:439` — confirming
[Block 20] §20.2's `[INFER]`
that this wrapper type exists to decouple the loop's stored timing state from the raw
`System.nanoTime()`-derived value (`Clock.ticks()`, §20.2) at exactly the point where a fresh
timestamp is captured, not merely at storage.

**`BAbstractSchedule`** ([Block 20] §20.6, previously `javap -p` method-list only): `[CERT]`
`organized/schedule/vineflower/niagara/schedule/BAbstractSchedule.java:32` (`public abstract class
BAbstractSchedule extends BComponent`), `:139` (`public abstract boolean isEffective(BAbsTime
var1);`), `:179` (`public abstract BAbsTime nextEvent(BAbsTime var1);`), `:31,34` (`@NiagaraProperty
(name = "alwaysEffective", ...)` / `public static final Property alwaysEffective = newProperty(...)`)
— exactly the abstract-method and property surface [Block 20] found via bytecode, with the
`isEffective`/`nextEvent` abstract-method names now confirmed at source (bytecode `javap -p` shows
signatures only, not the parameter's *purpose*, which the source's own parameter name — even
Vineflower's synthesized `var1` here, since the compiled parameter-name debug attribute did not
survive — does not add beyond the bytecode signature already gave; the class hierarchy and abstract
surface are the citation upgrade that matters here).

**Net effect on B20-G5:** the mechanical half of the gap (decompile the four modules) is done and
clean per §70.1; this section is the follow-through half (re-cite the specific claims [Block 20]
made from bytecode against real `file:line`s) for every class [Block 20] examined in depth
(`WritableSupport`, `AlarmSupport`, `BLoopPoint`, `BAbstractSchedule`). [Block 20]'s `EngineManager`/
`Clock` findings (§20.2) are **not** re-cited here — both classes live in `baja`, not in the four
modules B20-G5 named, so they are out of this block's source set (`baja` has its own prior partial
decompile from other blocks, not exhaustively re-verified here).

## 70.4 — B25-G1 NARROWED: `instanceof` pattern-matching (JEP 394) adoption, measured at source across the four modules `[CERT]`

> **Correction (added by [Block 90], §14 cross-block).** [Block 90] §90.2 cross-checked 13/13 "bound"
> sites in the docSource/vineflower overlap against `docSource.jar` originals: every one is Vineflower
> *resugaring* of the classic `instanceof`+cast idiom (byte-identical bytecode, `javac --release 21` +
> `javap -c`), not Tridium-authored JEP 394 syntax. The ~14.5% rate below measures decompiler output, not
> source adoption; the source-level rate for these four modules reads as ~0%. See [Block 90].

A line-based scan (`.java` files only, comment-leading lines excluded, per-module) of every
`instanceof` occurrence in the four decompiled modules, classifying each as **bound** (the JEP 394
binding form, `instanceof Type identifier`) or **unbound** (classic `instanceof Type)`/`instanceof
Type &&` with no binding):

| Module | `.java` files | non-comment lines containing `instanceof` | bound (pattern-match) | unbound (classic) | bound ratio |
|---|---:|---:|---:|---:|---:|
| `control` | 45 | 20 | 5 | 15 | 25% |
| `alarm` | 195 | 142 | 16 | 126 | 11% |
| `kitControl` | 224 | 7 | 0 | 7 | 0% |
| `schedule` | 103 | 52 | 11 | 41 | 21% |
| **Total** | **567** | **221** | **32** | **189** | **~14.5%** |

`[CERT]` — every count above is a literal, reproducible line-regex scan over the cited module trees
this session (see §70.6 for the scan's exact classification rule and a manual spot-check of 4
samples). Representative bound occurrences, each independently `grep`-confirmed this session: `if
(child instanceof BPointExtension ext) {` `[CERT]` `organized/control/vineflower/niagara/control/
BControlPoint.java:182` (and again `:197`); `if (!(facets.get("maxOverrideDuration") instanceof
BRelTime maxDuration))` `[CERT]` `organized/control/vineflower/niagara/control/
WritableSupport.java:253` (the **negated** form, `!(x instanceof T t)`, is valid JEP 394 syntax and
was counted as bound — the binding `t` is then usable in the enclosing block's fall-through, not
inside the negated condition itself); `if (oldValue instanceof BLink link &&
link.getTargetSlotName().equals(schedule.getName()))` `[CERT]` `organized/schedule/vineflower/
niagara/schedule/BAbstractScheduleSelector.java:142` (binding immediately used in the same
short-circuit `&&` clause — the idiom JEP 394 was designed for); `if (!(object instanceof
CoalesceUuidOnlyInvocation o))` `[CERT]` `organized/alarm/vineflower/com/tridium/alarm/
CoalesceUuidOnlyInvocation.java:18`.

**`kitControl` is a genuine zero, not a scan artifact.** All 7 non-comment `instanceof` occurrences
in `kitControl`'s 224 `.java` files use the classic unclassified form — e.g. `return grandparent
instanceof BLoopPoint;` `[CERT]` `organized/kitControl/vineflower/com/tridium/kitControl/
BLoopFloatingLimitAlgorithm.java:33` (a bare type-check with no binding needed, since the result is
returned directly as a `boolean`) and `if (boolPt instanceof BBooleanWritable) {` `[CERT]`
`organized/kitControl/vineflower/com/tridium/kitControl/BInterstartDelayControl.java:83` (the
matched value is never referenced by name afterward — the classic form is not a stylistic omission
here, since a binding would go unused). `[INFER]`: `kitControl` was **not** touched by the
`javax.baja→niagara` rename ([Block 20] §20.7) and was one of [Block 25]'s "not
idiomatically modernized" subsystems (§25.13's verdict) — a 0% pattern-matching-`instanceof` rate is
consistent with that same subsystem-level conservatism, not a separate finding.

**Reading the ratio.** `alarm` has the most raw `instanceof` sites (142, reflecting its large
195-file surface and its `BIAlarmSource`/extension-casting-heavy design) but the *lowest* bound
ratio among the three non-zero modules (11%); `control` and `schedule` — both smaller, more
recently-touched-looking modules per [Block 25] §25.9's `SequencedCollection`-NEW findings — carry
noticeably higher bound ratios (25%, 21%). This is directionally consistent with, though narrower
than, [Block 25] §25.13's corpus-wide "modernization clusters in specific newer subsystems, not
swept everywhere" verdict — extending that verdict's evidence base from records/sealed-classes/
pattern-switch (all bytecode-visible) to `instanceof` pattern matching (bytecode-invisible, the one
feature §25.6 flagged as unmeasurable at the time). B25-G1's own suggested method (grep `docSource.jar`'s
~3,200 originals) was not used — this block used the already-in-corpus Vineflower decompile instead,
which [Block 25]'s own docsource-coverage field (`control`: 31/45 covered, 68.9%) suggests should be
close to, but not proven identical to, the pristine original source for every file (see child gap).

## 70.5 — B25-G2 NARROWED: every `Deque`-family reference inside the four modules is either a false-positive English word or a concrete `LinkedList`-typed (AMBIG, non-`SequencedCollection`) call site `[CERT]`+`[INFER]`

[Block 25] §25.9 found 73 corpus-wide "NEW" `SequencedCollection` call sites (genuinely could not
compile pre-Java-21) and 34 "AMBIG" sites (`Deque`/`LinkedList`/`ArrayDeque`-family Methodref hits
that predate Java 21 and cannot be classified from bytecode alone), and named none of `control`,
`alarm`, `kitControl`, or `schedule` among its "top N5 jars by NEW hits" table — consistent with
what this block finds by reading the source directly: **zero** NEW-category `SequencedCollection`/
`List.getFirst()`-family usage anywhere in the four modules.

A `grep -rl 'Deque\|LinkedList\|ArrayDeque'` sweep across all four modules returns 5 files; 3 are
false positives — the English word "Dequeue"/"Dequeued"/"Dequeueing" (a UI/log-message verb, not
the `java.util.Deque` type) in `organized/alarm/vineflower/com/tridium/alarm/print/
BLinePrinterRecipient.java:259`, `organized/alarm/vineflower/niagara/alarm/
BRecoverableRecipient.java:462`, and `organized/schedule/vineflower/com/tridium/schedule/
ScheduleSpyManager.java` (6 occurrences, all "Dequeue(d)(ing)" in spy-page label strings) `[CERT]`
(read and confirmed non-matches this session). The 2 real hits are both `java.util.LinkedList`,
both declared with the **concrete class type**, not the `Deque` or `SequencedCollection` **interface**
type:

```java
private LinkedList<Runnable> queue = new LinkedList<>();
...
Runnable ret = this.queue.removeFirst();
...
this.queue.addLast(request);
```
`[CERT]` `organized/schedule/vineflower/com/tridium/schedule/ExecutionQueue.java:14,59,82` — a
FIFO work queue for scheduled-event execution, declared and used exclusively through
`LinkedList`'s own concrete API surface, never through `Deque` or `SequencedCollection` as a static
type anywhere in the file (confirmed by reading the whole 90-line class — no other import, cast, or
declared variable of either interface type exists in it).

```java
LinkedList<BSummary.Row> rows = new LinkedList<>();
...
public LinkedList<BSummary.Row> getRows() {
```
`[CERT]` `organized/schedule/vineflower/com/tridium/schedule/ui/BSummary.java:82,116` — a getter
return type, again concretely `LinkedList`; its only method call on the field visible in this file
is `rows.add(r)` `[CERT]`
`organized/schedule/vineflower/com/tridium/schedule/ui/BSummary.java:109` (ordinary
`Collection.add`, not itself a `Deque`-family
or `SequencedCollection` signal — [Block 25]'s classifier would not even have counted this
particular call as AMBIG, since `add()` is not one of the `getFirst`/`getLast`/`addFirst`/
`addLast`/`removeFirst`/`removeLast`/`reversed` method names §25.9 searched for; it is included here
for completeness of "every `LinkedList`-typed site found," not as an AMBIG classification itself).

**Reading the result.** `ExecutionQueue.java`'s `removeFirst()`/`addLast()` calls are the one
genuine AMBIG-shaped call site this block's four-module scope surfaces — and its declared type is
unambiguously the **concrete** `java.util.LinkedList`, never `Deque` or `SequencedCollection` as a
static type anywhere in the file. This is a clean, source-confirmed **"ordinary pre-21 `Deque`-family
code"** classification for this specific site — exactly the AMBIG-resolves-to-classic-not-new
outcome [Block 25] §25.9 flagged as undecidable from bytecode alone. `[INFER]`: whether this exact
site is one of [Block 25]'s counted 34 AMBIG sites cannot be confirmed by name — §25.9 published
only a corpus-wide total and a per-jar NEW-hit table, not a per-jar AMBIG breakdown — but
`schedule.jar` not appearing in §25.9's NEW-hit table (`baja`/`migrator`/`workbench`/`nre`/`bajaui`/
`platDaemon`/`bacnet`/`platform`/`program`/`template`/`box`/`fox`/`wiresheet`, 27 jars total) is
consistent with `schedule.jar` contributing zero NEW and at least this one AMBIG site, which is what
source reading independently confirms.

**Scope limit, stated plainly.** This section classifies every `Deque`-family reference reachable
within `control`/`alarm`/`kitControl`/`schedule` — 4 of the 253 jars [Block 25] scanned, and none of
the 27 jars §25.9 lists as carrying NEW-category hits. The other ~33 AMBIG sites (34 total minus the
one classified here) sit in modules not decompiled in this corpus (`baja.jar`, `bajaui.jar`,
`nre.jar`, `migrator.jar`, `workbench.jar`, `platDaemon.jar`, and others per §25.9's NEW-hit jar
list, which is the closest available proxy for where AMBIG sites also cluster) — B25-G2 is
**narrowed, not closed**; see child gap.

## 70.6 — Self-verification

**Token check.** Every load-bearing `[CERT]` `file:line` citation above was `grep`/`sed`-confirmed
against its cited source in this session, not hand-recalled: 34 tokens checked across §70.2-§70.5
(4 `getOldValueForPendingActionAuditEvent` method bodies, 4 class-header `implements` lines, 5
`Action` constant declarations, the Action-interface declaration (`organized/baja/vineflower/niagara/sys/Action.java`, line 3), `WritableSupport.java`
×3, `AlarmSupport.java` ackAlarm body, `BLoopPoint.java` ×6 (class header, property declarations,
PID formula ×3, null-check, `.now()` call), `BAbstractSchedule.java` ×4, the 4 `grep -rl` results
for `getOldValueForPendingActionAuditEvent`, the 4 `instanceof`-bound samples spot-checked
individually beyond the mechanized scan, `ExecutionQueue.java` ×3, `BSummary.java` ×3, and the 3
false-positive "Dequeue" files confirmed as non-matches), 0 absent, 0 downgraded. The
`instanceof`-census table (§70.4) is the output of a mechanized regex scan (method described
inline in §70.4/§70.5's Method paragraph); 4 of its 32 bound-classified lines were individually
re-`grep`-verified as a spot-check of the classifier itself (all 4 matched), rather than every one
of the 32 — a full manual re-check of all 32 was judged unnecessary given the classifier's rule is
simple (a following bare identifier token before a closing delimiter) and every spot-checked sample
matched.

**Marker tally — mechanized, literal `verify-block.sh` output** (per [Block 25] §25.x's own noted
limitation, pasting the tool's bracketed marker syntax verbatim into this section is itself
re-counted by a later run of the same tool — a self-reference artifact of the regex-based counter,
not a citation of another block's markers; the run below is this session's one canonical run,
taken before this paragraph's own bracketed tokens existed in the file):

```
$ /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block70.md /home/cristian/niagara5-research
== verify-block: niagara5-block70.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 38  (adj 34)
   [CERT-doc] 1  (adj 0)
   [CERT-web] 2  (adj 1)
   [CERT-a] 1  (adj 0)
   [INFER] 6  (adj 5)
-- ratio -- [INFER]/[CERT*] = 5/35 = 0.14
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   synth-ref  [B536]  (block back-reference — not file-verifiable)
   synth-ref  [B537]  (block back-reference — not file-verifiable)
   synth-ref  [B539]  (block back-reference — not file-verifiable)
   ok      organized/alarm/vineflower/niagara/alarm/AlarmSupport.java:172-195  (range end verified; file has 307 lines)
   ok      organized/baja/vineflower/niagara/sys/Action.java:3
   ok      organized/control/vineflower/niagara/control/BBooleanWritable.java:536-544  (range end verified; file has 657 lines)
   ok      organized/control/vineflower/niagara/control/BBooleanWritable.java:73
   ok      organized/control/vineflower/niagara/control/BEnumWritable.java:445-452  (range end verified; file has 564 lines)
   ok      organized/control/vineflower/niagara/control/BEnumWritable.java:64
   ok      organized/control/vineflower/niagara/control/BNumericWritable.java:63
   ok      organized/control/vineflower/niagara/control/BStringWritable.java:415-421  (range end verified; file has 534 lines)
   ok      organized/control/vineflower/niagara/control/BStringWritable.java:62
   ok      organized/control/vineflower/niagara/control/WritableSupport.java:188-210  (range end verified; file has 279 lines)
   ok      organized/control/vineflower/niagara/control/WritableSupport.java:268-277  (range end verified; file has 279 lines)
   ok      organized/control/vineflower/niagara/control/WritableSupport.java:32-62  (range end verified; file has 279 lines)
   ok      organized/control/vineflower/niagara/control/WritableSupport.java:89-91  (range end verified; file has 279 lines)
   ok      organized/kitControl/vineflower/com/tridium/kitControl/BInterstartDelayControl.java:83
   ok      organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:439
   ok      organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:452
   ok      organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:462
   ok      organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:64-67  (range end verified; file has 640 lines)
   ok      organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:72
   ok      organized/schedule/vineflower/com/tridium/schedule/ui/BSummary.java:109
   ok      organized/schedule/vineflower/niagara/schedule/BAbstractSchedule.java:32
   resolved 21 of 21
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

Adjusted ratio `[INFER]`/`[CERT*]` = **0.14** — low, consistent with a `mixed` citation-upgrade
block whose synthesis clauses (the `Action`-non-enum structural explanation in §70.2, the
scan-methodology-consistency reading in §70.4, and the AMBIG-site-identity caveat in §70.5) are each
explicitly flagged and built from named `[CERT]` facts read this session, not asserted
free-standing.

**Artifacts.** This file (`/home/cristian/niagara5-research/niagara5-block70.md`) is the only file
written this session, per the task's explicit single-file constraint. `CATALOG.md`/`INDEX.md`/
`RESEARCH-STATE.md` were **not** regenerated or hand-edited — left to the orchestrator/next
iteration. The `instanceof`-census and `Deque`-sweep scripts were run inline this session (not
saved to a standalone file); their exact classification rules are documented inline in §70.4/§70.5's
Method text so the counts are reproducible without the scratch script itself.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 70.7 — Child gaps

- **B70-G1** — Extend B25-G2's AMBIG-site classification to the remaining ~33 sites outside
  `control`/`alarm`/`kitControl`/`schedule`. Priority order per [Block 25] §25.9's own NEW-hit jar
  list (the closest available proxy for where AMBIG sites also cluster, since neither block has a
  published per-jar AMBIG breakdown): `baja.jar` (8 NEW hits — also the module carrying [Block 20]'s
  `EngineManager`/`Clock` classes, so decompiling it serves two open gaps at once, including
  B20-G5's own unfinished `baja` half), `migrator.jar` (8), `workbench.jar` (7), `nre.jar` bin/ext
  (7), `bajaui.jar` (6 — noting [Block 25] §25.14's Vineflower-hang caveat: this module needed the
  CFR fallback in the bake-off, so decompiling it should budget for that path explicitly).
  `investigable`.
- **B70-G2** — Confirm this block's `instanceof`-census counts (§70.4) against `docSource.jar`'s
  pristine originals for the 31-of-45 `control.jar` classes [Block 25]'s own docsource-coverage
  field says are covered (68.9%), to rule out any Vineflower resugaring artifact inflating or
  deflating the bound-vs-unbound classification specifically for `control` (the only one of the four
  modules where this citation upgrade has not been cross-checked against a second decompiled/original
  source, unlike `history` in [Block 20]'s own §20.9 precedent). `investigable`.
- **B70-G3** — [Block 20] §20.10's B20-G3 (does any Workbench/web UI by 5.0.0.28 Beta actually
  surface `getOldValueForPendingActionAuditEvent`'s output) remains open; this block's §70.2 adds
  the source confirmation that the hook exists on exactly 4 classes and is wired to
  `WritableSupport.toOldValueAuditString` (which itself calls `LEX.getText("actionAuditOldValue",
  ...)` `[CERT]` `organized/control/vineflower/niagara/control/WritableSupport.java:268-277`) —
  a live-station or Workbench-UI probe to see this lexicon key actually
  rendered anywhere is still the remaining step, unchanged from [Block 20]'s own framing.
  `blocked-on-live-station` (same blocker [Block 20] §20.10 named for B20-G1).
- **B70-G4** — This block found `kitControl` at a flat 0% `instanceof`-pattern-matching rate (§70.4)
  and [Block 25] §25.13 independently flagged `kitControl` as one of the "ported to compile, not
  rewritten" subsystems by its own (bytecode-visible) feature measures — no block has yet checked
  whether `kitControl`'s **records/sealed-classes/pattern-switch** counts (bytecode-visible, already
  in [Block 25] §25.2/§25.3/§25.5's corpus tables by jar) independently corroborate the same
  zero-modernization reading for this specific module, since [Block 25]'s own per-module detail
  tables only name the *top* jars per feature, and `kitControl.jar` does not appear in any of them —
  confirm this is a true zero and not merely "below the table's cutoff." `investigable`, mechanical
  (re-run [Block 25]'s own `classcensus.py` output, if preserved, filtered to `kitControl.jar`).

## 70.x — Connections

- **[Block 20]** — this block closes B20-G5 (the decompile-to-source mechanical ask) and
  re-derives §20.3/§20.4/§20.6/§20.7's bytecode-level findings from real source with no drift found
  (§70.3); it also deepens §20.3's `BIActionAuditProvider` finding with the structural "why a
  pattern-switch" explanation (§70.2) [Block 20] itself did not attempt (out of its own bytecode-only
  scope at the time).
- **[Block 25]** — this block closes B25-G4 (§70.2: the `control.jar` `B*Writable` pattern-switch
  read at source, plus the generalization check within these four modules), narrows B25-G1 (§70.4:
  a mechanized `instanceof`-pattern-matching census filling the bytecode-invisible gap §25.6 named),
  and narrows B25-G2 (§70.5: one AMBIG site fully classified as classic `LinkedList`-typed code,
  zero NEW-category sites found, consistent with [Block 25]'s own per-jar NEW-hit table already
  excluding all four of these modules).
- **`niagara-research` B536/B539** — [Block 20] §20.3/§20.7 already extended these N4 deep-dives'
  priority-array and `BLoopPoint` findings into N5 at the bytecode level; §70.3 here is the further
  extension to real N5 source, for the same claims, without re-deriving the N4 side.
