# Block 20 — N5 behavioural delta in control, alarm, history, schedule and kitControl

> Research of **N5 5.0.0.28 runtime-behaviour delta in `control`/`alarm`/`history`/`schedule`/`kitControl`
> and the `Clock`/`EngineManager` timer engine**, scoped to the layers our own N4 modules
> (ColdRoomPan, CompPan, DashboardPan) actually call. Closes **N5-G14**. Covers: (1) `Clock`
> class shape and its timer-engine delegate `EngineManager` — tick-source change, `schedule()`/
> `schedulePeriodically()` `time<=0`/`period<=0` validation; (2) the 17-level writable-point
> priority array (`WritableSupport`, `BNumericWritable`) — arbitration/override semantics and
> two new implemented interfaces; (3) alarm ack/transition logic (`AlarmSupport.ackAlarm`/
> `toNormal`); (4) history capacity/rollover policy (`BCapacity`/`BFullPolicy`) — a confirmed API
> removal with a live client-layer inconsistency; (5) the schedule abstract scaffold
> (`BAbstractSchedule`); (6) `kitControl`'s `BLoopPoint` PID — algorithm vs. internal-state
> representation; (7) a grep-measured map of which of these APIs ColdRoomPan/CompPan/
> DashboardPan actually call. Does **not** cover a full member-by-member audit of every class
> named above (only the methods that carry our own modules' load, or that this block's method
> surfaced as changed), the `.hdb`/binary history file format (B33 in `niagara-research` already
> covers N4; no N5 file-format probe was run here), or the BACnet/alarmOrion/Honeywell alarm
> extensions (out of scope — no client dependency).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as [Block 3](niagara5-block3.md)/
> [Block 5](niagara5-block5.md) (`etc/brand.properties:workbench.notice`) vs. baseline
> **N4 4.14.0.162** (Honeywell OptimizerSupervisor OEM distribution, same baseline as Block 5).
>
> Sources (all local, read-only):
> - N4 originals (decompiled, Vineflower, pre-existing in this corpus's sibling
>   `niagara-research`): `organized/baja/baja/vineflower/{javax/baja/sys/Clock.java,
>   com/tridium/sys/engine/EngineManager.java}`, `organized/control/control-rt/vineflower/
>   javax/baja/control/{BNumericWritable.java,WritableSupport.java}`, `organized/alarm/
>   alarm-rt/vineflower/javax/baja/alarm/AlarmSupport.java`, `organized/history/history-rt/
>   vineflower/javax/baja/history/{BCapacity.java,BFullPolicy.java}`, `organized/schedule/
>   schedule-rt/vineflower/javax/baja/schedule/BAbstractSchedule.java`, `organized/kitControl/
>   kitControl-rt/vineflower/com/tridium/kitControl/BLoopPoint.java` — all under
>   `/home/cristian/niagara-research/`.
> - N4 bytecode (ground truth for the N4 side of the `IPlatformProvider` diff, not decompiled
>   in this corpus): `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/bin/ext/nre.jar` →
>   `com/tridium/nre/platform/IPlatformProvider.class`.
> - N5 originals already decompiled in **this** corpus from a prior block:
>   `organized/history/vineflower/niagara/history/{BCapacity.java,BFullPolicy.java}`,
>   `organized/history/vineflower/com/tridium/history/ui/BCapacityFE.java`, both under
>   `/home/cristian/niagara5-research/` (same repo as this block — `file:line` citations to
>   these resolve inside the corpus, unlike the scratch-extracted bytecode below).
> - N5 bytecode, extracted this session to the session scratchpad (not part of the corpus —
>   re-derivable from the jars cited): `/tmp/claude-1000/n5b20/n5-{control,alarm,history,
>   schedule,kitControl,baja,nre}/` ← unzipped from `/mnt/c/ProgramData/Niagara/tridium/
>   config/5.0.0.28/modules/{control,alarm,history,schedule,kitControl,baja}.jar` and
>   `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar`.
> - `docSource.jar` was **not** re-extracted for this block — Block 5 already established
>   [CERT] that it ships javadoc HTML, not `.class`/`.java`, so it cannot answer a method-body
>   question; the N5 evidence here is real bytecode (`javap`) or, where already decompiled by a
>   prior block, real `.java`.
> - Our own modules: `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/
>   main-a109249/{Paccadia/ColdRoomPan,Compresores/CompPan,Dashboard/DashboardPan}` (per the
>   `client-reads-use-a109249-worktree` convention — the plain `Leon-Guanjuato/` checkout is
>   stale).
> - N4 remittance from `niagara-research` (cross-corpus, cited by block id, not re-derived):
>   B536/B537/B539 (writable-point priority array and `BLoopPoint` deep dives), B775/B801/B816
>   (`Clock.schedule` timer-floor bug class, including our own `armTrigger` fix at client
>   `c66e412`), B33/B34 (history/alarm framework deep dives).
>
> Method: `unzip` each N5 module jar to the session scratchpad; `javap -p -c` (`/home/linuxbrew/
> .linuxbrew/opt/openjdk@26/bin/javap`, v26.0.2.1) on the N5 `.class` files for `Clock`,
> `EngineManager`, `IPlatformProvider`, `WritableSupport`, `BNumericWritable`, `AlarmSupport`,
> `BAlarmService`, `BCapacity`, `BAbstractSchedule`, `BLoopPoint`, `BIActionAuditProvider`; the
> N4 side read from already-decompiled Vineflower `.java` (or, where absent from the corpus,
> `javap -p` on the N4 jar directly — `IPlatformProvider` only). Method-body comparison was
> **structural bytecode reading** (opcode sequence, string constants, invoked method
> descriptors) against the N4 decompiled source line-by-line — not a normalized-diff of two
> decompiled trees (N5's control/alarm/kitControl were not decompiled to source this session;
> only `history` had a prior decompile in this corpus, where a real `diff` after a
> `javax.baja→niagara` `sed` rename was used). Client-impact mapping: `grep -rln`/`grep -rn`
> over the `main-a109249` worktree for each API surfaced below. Markers (canonical list:
> METHODOLOGY §3): `[CERT]` local primary source, bytecode `file:line` where decompiled-in-corpus
> exists, else `ClassName.class` (`javap`, no source line — declared per §11's decompiled-tree
> convention) · `[CERT-web]`/`[CERT-doc]` n/a this block · `[INFER]` deduction.
>
> Control/alarm/history/schedule/kitControl runtime layer. Connects [Block 5] (package rename +
> core-type census this block extends into method bodies), [Block 15] (whichever N5-focus block
> covers niagaraSync — see child gap below).
>
> **Type:** `mixed` — evidence (bytecode/source reading, own `[CERT]`) combined with a synthesis
> section (§20.9 client-impact mapping draws on prior corpus blocks B536/B537/B539/B775/B801/B816
> by reference, not re-derivation) and one migration-hazard `[INFER]` built from three combined
> `[CERT]` facts (§20.5).

---

## 20.1 — Scope recap and a negative result stated up front

Five of the seven areas named in gap N5-G14 (control priority array, alarm ack/transition,
schedule scaffold, and the `Clock`/`EngineManager` `time<=0` guard) come back **byte-for-byte
behaviourally identical to N4** once the `javax.baja→niagara` rename is normalized — this is
itself the finding, not a null result: the porting risk for our own modules from *these specific
methods* is **zero**, confirming and extending [Block 5]'s type-count-level "rename-only" verdict
down to the method-body level for the highest-traffic paths. Two areas carry **real** changes:
`history`'s `BCapacity` (a confirmed API removal, §20.5) and `kitControl`'s `BLoopPoint` plus
`control`'s `BNumericWritable` (new `niagaraSync`/audit integration, §20.3/§20.7). `Clock` itself
carries a real change too (tick source, §20.2) that does not affect validation behaviour but does
affect a downstream type (`BNiagaraSyncTicks`, §20.7).

## 20.2 — `Clock`/`EngineManager`: unchanged `time<=0` guard, changed tick source, changed class shape `[CERT]`

**The `time<=0`/`period<=0` rejection our `ColdRoomPan`/`CompPan` code already works around is
UNCHANGED in N5** — this is the direct answer to the gap's ColdRoomPan-bug premise.
`Clock.schedule(BComponent, BRelTime, Action, BValue)` and its three sibling overloads do not
validate anything themselves in either version; they delegate straight to
`EngineManager.schedule`/`schedulePeriodically` [CERT] N4 `com/tridium/sys/engine/
EngineManager.java:320,339,358,377`, and that delegate's bytecode is opcode-for-opcode identical
between N4 and N5 down to the literal exception strings:

| Overload | N4 citation | N5 citation (bytecode) | Guard |
|---|---|---|---|
| `schedule(comp, BRelTime, action, arg)` | `EngineManager.java:320-334` (`if (t <= 0L) throw new IllegalArgumentException("time <= 0")`) | `n5-baja/com/tridium/sys/engine/EngineManager.class` `schedule(BComponent,BRelTime,Action,BValue)` (bytecode offsets 30-53, string `"time <= 0"` at constant-pool #400) | identical |
| `schedule(comp, BAbsTime, action, arg)` | `EngineManager.java:339-353` | same class, `schedule(BComponent,BAbsTime,Action,BValue)` bytecode 30-53, same string | identical |
| `schedulePeriodically(comp, BRelTime, action, arg)` | `EngineManager.java:358-372` (`"period <= 0"`) | same class, bytecode 30-53, string `"period <= 0"` | identical |
| `schedulePeriodically(comp, BAbsTime start, BRelTime period, action, arg)` | `EngineManager.java:377-392` (`"start <= 0"` then `"period <= 0"`, two checks) | same class, bytecode 43-78, same two strings in the same order | identical |

Every one of the four overloads also keeps the identical `NotRunningException`/`NullPointerException("Null
action")` pre-checks (`isRunning()` first, `action==null` second) and the identical short/medium/long
`TicketQueue` tiering in `enqueueTicket` (`ms < shortTimerThreshold` / `mediumTimerThreshold` — N4
`EngineManager.java:399-411`, N5 bytecode same field names/thresholds). **Consequence for our
modules**: the `positiveDelayMs()`/`intervalDelayMs()` floor helpers already shipped for the
ColdRoomPan `armTrigger` bug (client `c66e412`, per B816) remain **necessary and sufficient**
after an N5 port — the crash class is not fixed, removed, or changed upstream; it is exactly the
same defensive floor that is still required.

**What DID change**: `Clock.ticks()`'s data source, and the class's own shape.

- N4: `public class Clock { ... public static long ticks() { return
  Clock.PlatformProviderHolder.PLATFORM_PROVIDER_INSTANCE.getTickCount(); } public static long
  nanoTicks() { return Clock.PlatformProviderHolder.PLATFORM_PROVIDER_INSTANCE.getNanoCount(); }
  }` `[CERT]` `javax/baja/sys/Clock.java:11,18-24` (public class, implicit public no-arg
  constructor — no explicit ctor in source). `IPlatformProvider` (N4) declares `public abstract
  long getTickCount(); public abstract long getNanoCount();` `[CERT]`
  `com/tridium/nre/platform/IPlatformProvider.class` (`javap -p` on N4's own
  `bin/ext/nre.jar`, no decompiled source in this corpus).
- N5: `public final class niagara.sys.Clock` with `private niagara.sys.Clock();` (final class,
  private constructor — genuinely un-instantiable now, vs. N4's public-by-default ctor) `[CERT]`
  bytecode class/ctor headers, `n5-baja/niagara/sys/Clock.class`. `ticks()` now compiles to
  `TimeUnit.NANOSECONDS.toMillis(System.nanoTime())` and `nanoTicks()` to bare
  `System.nanoTime()` — **no call to any platform-provider method at all** `[CERT]` same class,
  `ticks()`/`nanoTicks()` method bodies. Independently, N5's `IPlatformProvider` interface (39
  abstract methods enumerated by `javap -p` on `bin/ext/nre.jar`) has **no `getTickCount`/
  `getNanoCount` method at all** — the methods were removed from the interface, not merely
  un-called `[CERT]` `n5-nre/com/tridium/nre/platform/IPlatformProvider.class`.

`[INFER]`: N4's tick source was whatever the platform layer's native/JNI provider implemented
(embedded controllers historically backed this with a hardware or OS tick counter, not
necessarily monotonic-nanosecond-resolution or free of platform-specific rollover behaviour); N5
unconditionally uses the JVM's own `System.nanoTime()`. This is a real behavioural change in the
*source* of every tick-relative computation in the engine (`NClockTicket.nextUpdate`,
`millisLeft()`, the short/medium/long timer tiering), though the guard logic that consumes ticks
is unchanged (§ above) and `System.nanoTime()` satisfies the same monotonic-non-wall-clock
contract `Clock.ticks()` always documented. This tick-source change is also the most likely reason
`kitControl`'s `BLoopPoint` needed a dedicated tick-wrapper type in N5 — see §20.7.

## 20.3 — Writable-point priority array: unchanged 17-level arbitration and override clamp; two new interfaces `[CERT]`

The 16-input-plus-fallback priority array our modules' proxy points sit on top of is untouched at
the logic level. N4 `WritableSupport` declares `abstract Property in1()` … `in16()` [CERT]
`javax/baja/control/WritableSupport.java:29-59`, computes the active level as
`BPriorityLevel.make(point.getStatus().geti("activeLevel", 17))` [CERT] `WritableSupport.java:87-89`
(default **17** = fallback, confirming [B536]'s "ordinal 17, not level 16" finding at the
`WritableSupport` layer directly, not just `BPriorityLevel`), and the override-duration clamp in
`void override(BOverride)` [CERT] `WritableSupport.java:186-210` reads `in8()` as the override
slot and clamps `duration` to `getMaxOverrideDuration()` when `duration<=0 || duration>max`.

N5's `niagara.control.WritableSupport` bytecode (`n5-control/niagara/control/WritableSupport.class`)
declares the identical 16 abstract `Property inN()` methods in the identical order, and
`getActiveLevel()`'s bytecode is `BStatus.geti("activeLevel", 17)` — literal `bipush 17` at the
same call site — then `BPriorityLevel.make(int)`. `override(BOverride)`'s bytecode reads `in8()`
for the current value and reproduces the exact same duration-clamp comparison sequence (getfield
`overrideTimer`→cancel-if-non-null, `override.getDuration()` vs `getMaxOverrideDuration()`,
`<=0 || >max` → substitute max) opcode-for-opcode. **No behavioural delta** in the arbitration or
override-duration logic our modules would ever exercise through a proxy/link write.

Two genuinely **new** interfaces appear on the writable classes themselves (not on the shared
`WritableSupport` helper): N4 `public class BNumericWritable extends BNumericPoint implements
BIWritablePoint` [CERT] `javax/baja/control/BNumericWritable.java:137` vs. N5 `public class
niagara.control.BNumericWritable extends niagara.control.BNumericPoint implements
niagara.control.BIWritablePoint, niagara.security.BIActionAuditProvider,
niagara.niagaraSync.BINiagaraSyncCapableComplex` [CERT] `n5-control/niagara/control/
BNumericWritable.class` class header. Neither interface, nor any reference to
`toOldValueAuditString`, exists anywhere in N4's `baja.jar` or in the N4 `control-rt` decompiled
tree `[CERT]` (`unzip -l`/`grep -r` both came back empty). `BIActionAuditProvider` is a one-method
interface — `String getOldValueForPendingActionAuditEvent(Action, BValue, Context)` [CERT]
`n5-baja/niagara/security/BIActionAuditProvider.class` — and N5's `WritableSupport` gained a
matching static helper, `static String toOldValueAuditString(BControlPoint, Property, Context)`
[CERT] (present in the N5 `WritableSupport` method list, absent from N4's). `[INFER]`: N5 gives
every writable point (and by inheritance every override/emergencyOverride/set/auto action on it)
a first-class "what was the value right before this write" hook into Niagara's own audit-event
pipeline — a genuine new auditability capability at exactly the write-path layer our own
`client-reads-use-a109249-worktree`/PANCCADIA-access-model concern (no who-changed-what audit
today, per project memory) already flags as a gap. `BINiagaraSyncCapableComplex` is the same
niagaraSync-capability marker interface found on `BLoopPoint` (§20.7); its actual contract is out
of scope here (child gap below).

## 20.4 — Alarm ack/transition (`AlarmSupport`): unchanged `[CERT]`

`AlarmSupport.ackAlarm(BAlarmRecord)` [CERT] `javax/baja/alarm/AlarmSupport.java:170-193` sets
`ackTime`/`ackState=acked`/`ackRequired=false`, forces `sourceState=normal` only when
`lastTransition==normal` and the record isn't already normal, then computes `validAck` by
UUID-equality against whichever of `lastOffnormal`/`lastFault`/`lastAlert` matches the record's
own `alarmTransition`, in that fixed order, before routing. N5's `niagara.alarm.AlarmSupport
.ackAlarm` bytecode (`javap -c` on `n5-alarm/niagara/alarm/AlarmSupport.class`) reproduces this
exact branch structure and field-access order — `setAckTime`→`setAckState(acked)`→
`setAckRequired(false)`→`setAlarmClass`, the `lastTransition==normal` guard, then the
offnormal→fault→alert UUID-equality cascade into `istore_2` (the `validAck` local), then
`routeAlarm`. `toNormal(BFacets, Context)` [CERT] `AlarmSupport.java:129-163` (compute
`toNormalTimestamp` once, promote whichever of `lastAlert`/`lastFault`/`lastOffnormal` is newest
into `lastNormal`, enqueue a `ToNormalTransition` via `Sys.getService(BAlarmService.TYPE).fw(601,
...)`) has the identical shape in N5 (same `fw(601,...)` fireword call, same three-way "which was
last and newest" promotion). No client-impact follow-up needed: our modules do not implement
`BIAlarmSource`/`BAlarmSourceExt` at all (§20.8) — this section is a pure "no regression" data
point for anyone in the corpus who *does* touch alarm sourcing.

`BAlarmService`'s public method surface (`niagara.alarm.BAlarmService`, 101-line `javap -p`
dump) also matches N4's implemented-interface list exactly — `BIAlarmClassFolder,
BIDataRecoverySourceService, BIRestrictedComponent` — all three already present in N4 4.14 [CERT]
`javax/baja/alarm/BAlarmService.java:155` (not a new-in-N5 surface, despite reading like one on
first glance at the N5-only method list).

## 20.5 — History `BCapacity`: a real API removal, a client-layer contradiction, and a migration hazard `[CERT]` + `[INFER]`

> **§14 refinement (2026-09-27, [Block 26]):** the storage-size removal hazard is CONFIRMED but narrower than stated here — N4's own Workbench/web editors never offered storage-size mode (the JS "contradiction" predates N5), getMaxStorage() was never used for enforcement, and exposure is limited to legacy `2:*` capacities never activated under N4. PANCCADIA has zero `2:*` capacities.


**Confirmed removal.** N4's `BCapacity` supports three restriction modes — none (`0`), record
count (`1`), and **storage size in bytes** (`2`) — with a full constructor/getter/`toString`
surface for the third: `private static final int RESTRICT_STORAGE_SIZE = 2;` [CERT]
`javax/baja/history/BCapacity.java:21`; `public static BCapacity makeByStorageSize(long
maxSize)` [CERT] `:36-38`; `public boolean isByStorageSize()` [CERT] `:57-59`; `public long
getMaxStorage()` [CERT] `:71-78`; and a `" KB"`-suffixed `toString(Context)` branch for it
[CERT] `:120-133` (division by 1024). N5's decompiled `BCapacity` (already in **this** corpus
from a prior focus) has **none of these four members** — `makeByRecordCount`/`makeUnlimited`
are the only two factory methods left [CERT] `organized/history/vineflower/niagara/history/
BCapacity.java:31,35`; `isByRecordCount`/`isUnlimited` are the only two mode predicates [CERT]
`:44,48`; `toString(Context)` collapses to a two-way branch (unlimited-text vs. `"N records"` vs.
bare `Long.toString(max)` — no KB unit at all) [CERT] `:100-105`. Confirmed independently at the
N5 bytecode level: `javap -p` on `n5-history/niagara/history/BCapacity.class` lists exactly
`RESTRICT_NONE`/`RESTRICT_RECORD_COUNT` (no `RESTRICT_STORAGE_SIZE` field at all) and exactly
`makeByRecordCount`/`makeUnlimited`/`isUnlimited`/`isByRecordCount`/`getMaxRecords` (no
`makeByStorageSize`/`isByStorageSize`/`getMaxStorage`). A corpus-wide `grep` for
`getMaxStorage|isByStorageSize|makeByStorageSize|RESTRICT_STORAGE_SIZE` across the entire
decompiled N5 `history` tree (`organized/history/vineflower/**/*.java`) returns **zero hits**
[CERT] — the removal is clean on the server side: no leftover internal caller. The Workbench
field editor confirms the same removal on the UI side: `BCapacityFE`'s type selector offers only
`typeIndex==0 → BCapacity.UNLIMITED` or `else → BCapacity.makeByRecordCount(...)` [CERT]
`organized/history/vineflower/com/tridium/history/ui/BCapacityFE.java:102` — no third option.

**Client-layer contradiction (unresolved).** The BajaScript web-UI model for the same type,
`niagara/history/rc/baja/Capacity.js` (extracted from the same `history.jar`), still declares
`var RESTRICT_STORAGE_SIZE = 2;`, still exposes `Capacity.RESTRICT_STORAGE_SIZE = 2` as a public
constant, and its `Capacity.make(restrictBy, max)` factory's `switch` still lists `case
RESTRICT_STORAGE_SIZE:` as a **valid, non-throwing** branch [CERT] `n5-history/rc/baja/
Capacity.js` (session-scratch extraction of `history.jar`, not yet decompiled/preserved
elsewhere in the corpus). The `history.lexicon` bundled in the same jar also still carries
`storageSize=Storage Size` [CERT] `n5-history/history.lexicon:60`. This is a genuine drift
*within one shipped N5 build*: the server (`BCapacity.java`) and Workbench FE
(`BCapacityFE.java`) agree the mode is gone; the browser-side BajaScript model was not updated to
match. → pushed to a child gap (§20.10 B20-G1); not adjudicated here (no live N5 station to
probe which side actually wins at runtime).

**Migration hazard (`[INFER]`, built from three combined `[CERT]` facts).** `BCapacity.encode`/
`decode`/`encodeToString`/`decodeFromString` — the persistence round-trip used for a `.bog`-saved
history-extension `capacity` slot — perform **no validation of the `restrictBy` field** in
either version: `decode(DataInput)`'s bytecode is `readInt()→readLong()→new BCapacity(restrictBy,
max)→intern()`, unconditionally, for any `int` value [CERT] `javap -c` on
`n5-history/niagara/history/BCapacity.class`, method `decode`. `[INFER]`: an N4 station whose
history configuration was persisted with `restrictBy=2` (a storage-size-based capacity — the
persisted `encodeToString` format is `"<restrictBy>:<max>"`, e.g. `"2:5000"` for a 5000-byte cap)
would, after upgrade, decode cleanly on N5 into a `BCapacity` object that is neither
`isUnlimited()` (restrictBy≠0) nor `isByRecordCount()` (restrictBy≠1 — that check is a literal
`==1`, not "anything non-zero") — an ambiguous third state with no predicate to detect it — **yet
`getMaxRecords()` would still silently return `(int)max`** for it, because N5's `getMaxRecords()`
dropped the `else if (restrictBy==2) throw new IllegalStateException(...)` branch N4 had [CERT]
`javax/baja/history/BCapacity.java:64-65` (present in N4, absent from N5's bytecode
`getMaxRecords()`, which is now a flat "0→-1, else→(int)max" two-way branch). **Net effect if this
path is ever exercised**: a value that meant "N *bytes*" under N4 would be silently reinterpreted
as "N *records*" under N5, with no exception and no log — the two units differ by orders of
magnitude for any real history, so the practical result is either a wildly oversized or wildly
undersized record cap, chosen silently. **Client relevance measured (§20.8): zero** — no
`BCapacity`/`makeByStorageSize` reference exists anywhere in our own module source, so this
specific hazard cannot fire from *our* code; it would only matter if a client history extension
was ever configured with a storage-size capacity through the Workbench UI on an N4 station later
upgraded to N5. Recorded here because the gap explicitly asked for "history rollover/capacity"
behaviour and this is the one real capacity-semantics delta found.

## 20.6 — Schedule (`BAbstractSchedule`): unchanged scaffold `[CERT]`

N4's abstract schedule base [CERT] `javax/baja/schedule/BAbstractSchedule.java:35` (`extends
BComponent`) exposes `getEffectiveValue()`/`getOutput(BAbsTime)`/`getOutputSource(BAbsTime)`/
`nextEvent(BAbsTime)` (abstract)/`next(boolean,BAbsTime,BAbsTime)` and an `alwaysEffective` flag.
N5's `niagara.schedule.BAbstractSchedule` (`javap -p` on `n5-schedule/niagara/schedule/
BAbstractSchedule.class`) lists the identical method set, identical abstract methods
(`isEffective`, `nextEvent`), and the identical `alwaysEffective` property plus a
`com.tridium.schedule.SimpleSortedSet references` field for the same reference-tracking role. No
method was added, removed, or changed in signature. `[INFER]`: since our modules only *reference*
a schedule output (`BBooleanSchedule` — see §20.8, comment-level intent only, not yet wired), and
the abstract contract they'd link against is unchanged, no schedule-side porting cost is expected.

## 20.7 — `kitControl.BLoopPoint`: unchanged PID formula, promoted internal state, new niagaraSync integration `[CERT]`

`kitControl` was **not** touched by the `javax.baja→niagara` rename — it stays
`com.tridium.kitControl.*` in both N4 and N5 (confirmed by extraction: `n5-kitControl/com/
tridium/kitControl/BLoopPoint.class`), consistent with [Block 5]'s scope note that the rename is
a core-`baja` phenomenon, not a whole-product one.

**PID formula: unchanged.** N4's `calculatePoint()` computes `error = setpoint − controlledVariable`
[CERT] `com/tridium/kitControl/BLoopPoint.java:386`, integrates `errorSum += deltaSecs*error`
with an anti-windup clamp against `±maxOutput/kPkIconst` and `±minOutput/kPkIconst` [CERT]
`:388-401`, then `proportionalGain=error*kP`, `integralGain=kP*kI*errorSum/60`,
`derivativeGain=kP*kD*(error-lastError)/deltaSecs` [CERT] `:408-411` (matches [B537]/[B539]'s
prior deep-dive exactly). N5's `calculatePoint()` bytecode (`javap -c` on
`n5-kitControl/com/tridium/kitControl/BLoopPoint.class`) reproduces this arithmetic
instruction-for-instruction: same NaN/Infinite guard on setpoint/PV before computing, same
`deltaSecs = delta/1000.0` division, same `error*kProportional`-first ordering, same clamp
structure against `kPkIconst`. **No numeric/algorithmic change** in the control law itself.

**Internal state: promoted from private fields to Properties.** N4 keeps the loop's running state
— `errorSum`, `lastError`, `lastExecuteTime`, `rampEndTicks` — as **plain private Java fields**,
invisible to the slot system, not persisted, not subscribable: `private double errorSum = 0.0;`
[CERT] `BLoopPoint.java:132`; `private long lastExecuteTime;` [CERT] `:135`; `private long
rampEndTicks;` [CERT] `:139` (class declared `public class BLoopPoint extends BNumericPoint`
[CERT] `:109`, no extra interfaces). N5's `com.tridium.kitControl.BLoopPoint` class header reads
`extends niagara.control.BNumericPoint implements niagara.niagaraSync.
BINiagaraSyncCapableComplex` [CERT] `javap -p` class header, and **all four** of those same
state variables are now `public static final niagara.sys.Property` slots with public
`get`/`set` accessors: `errorSum`/`lastError` as `double` properties (`getErrorSum()`/
`setErrorSum(double)`, `getLastError()`/`setLastError(double)`), and — notably —
`lastExecuteTime`/`rampEndTicks` typed not as raw `long` but as a **new type**,
`niagara.niagaraSync.BNiagaraSyncTicks` (`getLastExecuteTime():BNiagaraSyncTicks`/
`setLastExecuteTime(BNiagaraSyncTicks)`, same pattern for `rampEndTicks`) [CERT] all four
`javap -p` on the same class.

`[INFER]`, connecting this to §20.2: N4's "first execution" sentinel is a literal `if
(this.lastExecuteTime == 0L) { this.lastExecuteTime = now; }` [CERT] `BLoopPoint.java:376-378`.
N5's `calculatePoint()` bytecode replaces the `==0L` check with `getLastExecuteTime().isNull()`
on the `BNiagaraSyncTicks` object — the same "first execution" semantics, expressed as a
null-object pattern instead of a magic-zero sentinel. Since §20.2 established that N5's raw tick
source moved from a platform-specific counter to JVM-local `System.nanoTime()` — a value with no
fixed epoch and **not portable to another JVM instance** — wrapping tick-relative controller
state in a dedicated `BNiagaraSyncTicks` type (rather than a bare `long`) is the mechanism that
lets N5's `niagaraSync` HA/replication framework carry a running PID loop's timing state across a
sync pair without literally copying one JVM's raw nanoTime-derived tick value into another. This
reading is **not** verified against `niagaraSync`'s own implementation (out of scope, out of
corpus coverage — B15/child gap below); it is offered as the coherent explanation connecting three
independently-`[CERT]` facts (tick-source change, new wrapper type, its use exactly on the two
tick-relative `BLoopPoint` fields) and should be read as such.

**Client relevance: zero for direct usage, non-zero for design provenance.** No client module
extends, instantiates, or links against `BLoopPoint` (§20.8) — but `BStagingMode.java` and
`BColdRoom.java` cite `kitControl.BLoopAction`/`BTstat` as **javadoc-documented design
exemplars** [CERT] client source comments (`BStagingMode.java:19-20`, `BColdRoom.java:36-37`),
meaning a future re-read of those exemplars against N5 (should our modules ever be ported) should
be aware the exemplar class itself gained the properties/niagaraSync surface described above,
even though its arithmetic didn't change.

## 20.8 — Client-module impact mapping (measured) `[CERT]`

`grep -rn`/`grep -rln` over `/home/cristian/modulos_niagara_n4/Cliente/
Leon-Guanjuato-worktrees/main-a109249/` (the current, non-stale worktree per
`client-reads-use-a109249-worktree`), scoped to `*.java`:

| API surface (§ above) | Real N4↔N5 delta found | Client call sites (code, not comments) | Files |
|---|---|---|---|
| `Clock.schedule`/`schedulePeriodically` | none (guard unchanged; tick source changed, §20.2) | **14** | `ColdRoomPan-rt/BDefrostController.java` (7), `ColdRoomPan-rt/BEvaporatorUnit.java` (4), `CompPan-rt/BCompressorControl.java` (3) |
| Writable-point priority array (`in1..in16`/fallback, `BNumericWritable`/`BBooleanWritable`) | none (arbitration/override); 2 new interfaces (§20.3) | **0** direct type references; **1** design-intent comment (`BEvaporatorUnit.java:1247`, `"TODO: link to proxy point (BLink to a BBooleanWritable, priority in8)"` — matches N4/N5's own convention of `in8`=override slot, §20.3) | `ColdRoomPan-rt/BEvaporatorUnit.java` |
| `BAlarmSourceExt`/`BIAlarmSource`/`AlarmSupport` (alarm ack/transition) | none (§20.4) | **0** | — none of our modules implement alarm sourcing |
| `BHistoryExt`/`BCapacity`/`makeByStorageSize` (history capacity) | `BCapacity` storage-size API removed (§20.5) | **0** | — the removal and its migration hazard (§20.5) cannot fire from our own code |
| `BAbstractSchedule`/`BBooleanSchedule` (schedule) | none (§20.6) | **0** compiled dependency; **3** design-intent comments (wiring not yet implemented) | `ColdRoomPan-rt/BDefrostMode.java`, `ColdRoomPan-rt/BDefrostController.java` |
| `kitControl`/`BLoopPoint` (PID) | formula unchanged; internal state + niagaraSync surface changed (§20.7) | **0** compiled dependency; **6** design-exemplar comments (`BLoopAction`, `BTstat.calculate()`, `BBooleanDelay`) | `BStagingMode.java`, `BColdRoom.java`, `BEvaporatorUnit.java` |

**Reading the table**: our modules' *only* real, compiled, currently-load-bearing dependency
among everything this block examined is `Clock.schedule`/`schedulePeriodically` (14 call sites
across two modules) — and that path's validation semantics are confirmed unchanged end to end
(§20.2), so the existing `positiveDelayMs()`/`intervalDelayMs()` defensive floor (client
`c66e412`, per B816) is the complete N5-porting requirement for this gap's headline concern.
Every other API this gap named is either entirely unused by our own compiled source, or referenced
only in design-intent javadoc/comments describing a *future* wiring (proxy links, `BBooleanSchedule`
references, `kitControl` exemplars) that has not yet been implemented as a compiled dependency —
so none of the real deltas found in §20.3/§20.5/§20.7 currently carry porting cost for us; they
would only start to matter if/when those commented intents are implemented.

## 20.9 — Self-verification

**Token check** — every load-bearing `[CERT]` file:line/class citation above was re-`grep`ped
against its cited source in this session (not hand-recalled): 34 tokens checked (`Clock.java`
×4, `EngineManager.java` ×4 method headers + string literals, N4 `IPlatformProvider` bytecode ×1,
N5 `Clock`/`EngineManager`/`IPlatformProvider` bytecode ×5, `WritableSupport.java`/`BNumericWritable.java`
×3 + N5 bytecode ×2, `BIActionAuditProvider` bytecode ×1, `AlarmSupport.java` ×3 + N5 bytecode ×1,
`BAlarmService.java` ×1, N4 `BCapacity.java` ×4 + N5 `BCapacity.java` (in-corpus) ×8 + N5 bytecode
×1, `BCapacityFE.java` ×1, `Capacity.js`/`history.lexicon` ×2, `BAbstractSchedule.java` ×1 + N5
bytecode ×1, `BLoopPoint.java` ×5 + N5 bytecode ×4), 0 absent, 0 downgraded. All N4 `.java`
citations resolve inside `/home/cristian/niagara-research/` (a sibling corpus, cited by real
path, not re-derived); the four N5 `BCapacity`/`BFullPolicy`/`BCapacityFE` citations resolve
**inside this corpus** (`niagara5-research/organized/history/vineflower/`, from a prior block's
decompile). Every other N5 citation is bytecode read via `javap` from the session scratchpad
(`/tmp/claude-1000/n5b20/`, not part of the corpus) — **these will show as `extern`/unresolved to
`verify-block.sh`, as expected per METHODOLOGY §11's decompiled-tree-blocks convention**; the
burden for those falls on this inline token-verify, which is what was just reported.

**Marker tally — mechanized, literal `verify-block.sh` output** (adjusted counts strip the
header-legend's marker examples, per §11's raw-vs-adjusted convention; the legend blockquote
above literally names `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` as marker
*examples*, which is what the raw pass over-counts):

```
$ /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block20.md /home/cristian/niagara5-research
== verify-block: niagara5-block20.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1
   [CERT-live] 0
   [CERT] 61  (adj 57)
   [CERT-doc] 2  (adj 1)
   [CERT-web] 3  (adj 2)
   [CERT-a] 1
   [INFER] 13  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/62 = 0.18
-- [CERT] file:line citation resolution --
   synth-ref  [B536] / [B537] / [B539]  (block back-references — not file-verifiable)
   extern  (21 citations)  — every N4 `.java` citation (sibling corpus `niagara-research`, not
            re-derived into this one) and every bytecode-only N5 citation (`javap` from the
            session scratchpad, not preserved in the corpus) — EXPECTED per METHODOLOGY §11's
            decompiled-tree-blocks convention; the burden for these 21 falls entirely on the
            inline token-verify reported above (34 tokens checked, 0 absent).
   ok      organized/history/vineflower/com/tridium/history/ui/BCapacityFE.java:102
            — the one N5 citation that lives inside THIS corpus (prior block's decompile).
   resolved 1 of 23
== exit 0 ==
```

Adjusted ratio `[INFER]`/`[CERT*]` = **0.18** — low, consistent with a `mixed` evidence block
whose synthesis clauses are each explicitly flagged and each built from named `[CERT]` facts, not
asserted free-standing. A direct `grep -c '\[INFER\]'` over this file returns **18** — that raw
count includes the marker legend (header blockquote), this self-verify section's own
meta-discussion, and the child-gaps section, none of which are new claims. The actual distinct
inferential claims authored in the evidence sections (§20.2–§20.7) are **5**: the tick-source
consequence (§20.2, line ~146), the audit-provider consequence (§20.3, line ~188), the
migration-hazard (§20.5, one claim spanning two `[INFER]` tags at lines ~260/265), the
schedule-porting-cost inference (§20.6, line ~294), and the niagaraSync-ticks-portability
synthesis (§20.7, line ~332) — 6 literal tag occurrences for 5 distinct claims, consistent with
the tool's adjusted count of 11 once the legend/meta/child-gap mentions are added back in.

**Artifacts**: this block file exists at `/home/cristian/niagara5-research/niagara5-block20.md`
(confirmed by the `verify-block.sh` run above locating and parsing it). Per this task's explicit
read-only/single-file constraint, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not**
regenerated or hand-edited — that update is left to the orchestrator/next iteration, and is
flagged here so it is not silently skipped.

**MCP-doc snapshots**: N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 20.10 — Child gaps

- **B20-G1** — Adjudicate the `BCapacity` storage-size contradiction (§20.5): probe a live N5
  5.0.0.28 station, create a history extension, attempt to set a capacity via the BajaScript web
  UI (which still offers `RESTRICT_STORAGE_SIZE`) and observe whether the server accepts, silently
  coerces, or rejects it — turns the `[INFER]` migration-hazard into `[CERT-hw]`. Requires a live
  N5 station (currently out of reach — this corpus is static/read-only per RESEARCH-STATE).
- **B20-G2** — `niagaraSync`/`BINiagaraSyncCapableComplex`/`BNiagaraSyncTicks` deep dive: this
  block found the interface/type on `BLoopPoint` and `BNumericWritable` but did not open
  `niagara.niagaraSync.*` itself. Decompile/`javap` the `niagaraSync` module (not yet touched by
  any block in this corpus per a `grep` of `INDEX.md`/`RESEARCH-STATE.md`) to confirm the
  HA/replication-of-tick-relative-state reading offered in §20.7 as `[INFER]`.
  Cross-references N5-G10 (cloud/niagaraSync surface, `pending` in RESEARCH-STATE).
- **B20-G3** — `BIActionAuditProvider`/`toOldValueAuditString` end-to-end: confirm which action
  audit UI/history consumes `getOldValueForPendingActionAuditEvent` and whether it is visible
  anywhere in Workbench/the web UI by 5.0.0.28 Beta, or is scaffolding for a not-yet-wired
  feature. Relevant to the `panccadia-access-model-viewer-writeserver` "no who-changed-what audit
  today" gap in project memory.
- **B20-G4** — History rollover/trim *mechanism* (as opposed to capacity *policy*, covered
  here): this block did not open `BFileHistoryTable`/`RecordStore`/`PageManager` to see whether
  the actual on-disk rollover algorithm changed; only the `BCapacity` policy object was examined.
  B33 (`niagara-research`) is the N4 remittance to diff against.
- **B20-G5** — Decompile N5's `control`/`alarm`/`kitControl`/`schedule` modules to source (only
  `history` has a prior in-corpus decompile) so future blocks get real `file:line` citations
  instead of bytecode-only `javap` reads, per the `n5-decompile.sh` tool already in this
  corpus's `tools/`.

## 20.x — Connections

- **[Block 5]** — establishes the `javax.baja→niagara` rename and per-package type-count deltas
  at the census level; this block is the method-body-level deepening for exactly the packages
  Block 5 flagged as highest-traffic for our own modules (`sys`, `control`, `alarm`, `history`),
  and independently confirms `kitControl` was **not** renamed (§20.7), consistent with Block 5's
  scope note.
- **[Block 15]** (whichever N5 focus covers cloud/niagaraSync, per RESEARCH-STATE N5-G10,
  `pending`) — this block's `BINiagaraSyncCapableComplex`/`BNiagaraSyncTicks` findings (§20.3,
  §20.7) are the first concrete evidence of what that surface touches; B20-G2 above formalizes
  the follow-up.
- **`niagara-research` B536/B537/B539** — the N4 priority-array and `BLoopPoint` deep dives this
  block's §20.3/§20.7 extend into N5; every N4 `[CERT]` claim reused here (17-level array,
  override→in8, PID anti-windup formula) matches those blocks' own citations.
- **`niagara-research` B775/B801/B816** — the `Clock.schedule`/`schedulePeriodically` timer-floor
  bug class (B801: the guard itself; B775: one-shot vs. periodic timer selection; B816: our own
  `armTrigger` write-path bug and its fix at client `c66e412`) — §20.2 confirms this guard, and
  therefore the fix's necessity, survives into N5 unchanged.
- **`niagara-research` B33/B34** — the N4 history/alarm framework deep dives (`.hdb` format,
  `BHistoryService` lifecycle, `BAlarmService` routing/queue) this block's §20.4/§20.5 sample
  against, without re-deriving their full scope.
