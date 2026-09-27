# Block 45 — Making ColdRoomPan HA-ready for niagaraSync (PoC refactor and build)

> Research of **making the ColdRoomPan N5 port HA-ready under niagaraSync**: closes named gap
> **B37-G6** (migrate the port's `Clock.schedule` timers and plain-field interlock state to the
> `niagaraSync` replication contract, and prove it still builds/tests). Covers: a full inventory
> of every raw `Clock.schedule`/`Clock.Ticket` field and every non-Property Java-field state in
> `BColdRoom`/`BDefrostController`/`BEvaporatorUnit`; the real N5 `niagaraSync` API read from
> source plus one stock exemplar (`kitControl.timer.BBooleanDelay`, already the module's own
> cited design pattern) that uses it; a concrete refactor implementing
> `BINiagaraSyncCapableComplex` on all three classes, replacing every bare `Clock.Ticket` with a
> `BNiagaraSyncTicket` child Property, and promoting every remaining plain-field interlock/
> hysteresis state (including a FIFO queue, encoded as a comma-separated `String` Property — no
> stock list/queue type exists) to hidden Properties; a real `./gradlew` build (jar +
> moduleTestJar) of the refactored module; a re-run of the 51 pure-logic TestNG tests (JDK 25,
> no Niagara runtime, per [Block 29]) showing zero regression, plus 4 new directed tests (with a
> mutation-kill bite-proof) for the one genuinely new pure helper this refactor extracted; and a
> static walk of `NiagaraSyncComponentSpaceValidator`'s exact rules against the refactored
> classes. Does **not** cover: a live two-station niagaraSync pair actually exercising a
> mid-defrost failover (no N5 station/license available this session — carries forward [Block 37]
> B37-G3/B37-G1, unresolved by construction); `niagaraTest`/`bin/test.exe` execution of the
> ported test classes (still blocked on the `tridium:nre` license wall [Block 17]/[Block 29]
> found — this block does not re-attempt it, the plain-TestNG lane is the oracle here exactly as
> in [Block 29]); or CompPan/DashboardPan (out of scope, ColdRoomPan-rt only, matching
> [Block 16]/[Block 29]'s own scope).
>
> Subject version: **Niagara 5.0.0.28 beta** — same install [Block 16]/[Block 17]/[Block 29] used:
> `/mnt/c/Program Files/Niagara/5.0.0.28` (read-only), `/mnt/c/ProgramData/Niagara/tridium/config/
> 5.0.0.28/modules` (read-only, **247 jars** this session, verified stable before AND after every
> build below — never mutated). Gradle **9.2.1**, JDK `/home/linuxbrew/.linuxbrew/opt/openjdk@25`
> (OpenJDK 25.0.4.1). N4/N5-ported ColdRoomPan-rt source: forked from the existing, already-built
> N5 port at `/home/cristian/niagara5-research/poc/coldroompan-n5/` ([Block 16]/[Block 29]) into a
> NEW, isolated copy `/home/cristian/niagara5-research/poc/coldroompan-n5-ha/` (created this
> session via `rsync -a --exclude=build/ --exclude=.gradle/`, gitignored — `.gitignore` already
> carried the `poc/coldroompan-n5-ha/` rule before this session started). The original
> `poc/coldroompan-n5/` tree and the real client source at
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249/` were **never
> written to** this session (only read, for the `client-reads-use-a109249-worktree` convention —
> not re-read this session; the port's `ColdRoomControl.java` diff against [Block 16]/[Block 29]'s
> corpus, §45.3, is the evidence trail instead).
>
> Sources:
> - `organized/baja/vineflower/niagara/niagaraSync/{BINiagaraSyncCapableComplex,BNiagaraSyncTicket,
>   BNiagaraSyncTicks}.java` — read in full this session (the real N5 API, not bajadoc).
> - `organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncComponentSpaceValidator.java`
>   — read in full this session (the exact enforcement rules walked in §45.6).
> - `organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java` — read in
>   full this session; the stock exemplar `BEvaporatorUnit`'s own javadoc already cites
>   ("Actuation sequence mirrors kitControl BBooleanDelay") — its use of a `BNiagaraSyncTicket`
>   child Property (`ticket`, flags=71) is the pattern this block's refactor follows directly.
> - `organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java` — read in full this
>   session (a second exemplar: promotes `lastExecuteTime`/`rampEndTicks` to `BNiagaraSyncTicks`
>   Properties but keeps its PERIODIC re-arming `Clock.Ticket` as a plain field, re-armed
>   unconditionally in `started()` — the precedent this block's own design decisions, §45.3, are
>   checked against).
> - `organized/baja/vineflower/niagara/status/{BStatusBoolean,BStatusNumeric}.java`,
>   `organized/baja/vineflower/niagara/sys/{BString,BAbsTime,BRelTime,BEnum}.java` — targeted reads
>   this session, confirming which of the module's existing Property types are `BComplex`
>   (subject to the validator's `isComplex()` filter) vs. `BSimple` (exempt), for §45.6.
> - [Block 37] `niagara5-block37.md` §37.2-§37.7 (the replication protocol, the offset-correction
>   mechanism, and requirements 1-4 this block implements against).
> - [Block 16] `niagara5-block16.md` (the porting recipe and `niagara_config_home` mirror
>   redirection hazard this block's own `gradle.properties` fix reapplies to the new `-ha` copy).
> - [Block 29] `niagara5-block29.md` §29.1-29.3 (the JUnit4->TestNG mapping already applied to the
>   5 ported test files this block re-runs unchanged) and §29.7 (the plain-TestNG-on-JDK-25
>   no-station oracle this block reuses for its own new test).
> - This session's own command output: every `./gradlew` invocation (jar, slotomatic,
>   moduleTestJar), `javac`/`java org.testng.TestNG` runs (baseline + mutated), preserved under
>   `poc/coldroompan-n5-ha/codegen-plaintestng/{compile,run,run-mutated}.log` — mutated-run
>   artifacts (`src-mutated/`, `build-mutated/`, `report-mutated/`) deleted after the bite-proof
>   per the isolated-scratch-mutation convention ([Block 29] §29.7.1); the module source diff
>   confirming the real `src/` was never touched is quoted in §45.5.
>
> Method: full-file reads of the 3 real `niagaraSync` API classes + the validator + 2 stock
> exemplars (not sampled) · a mechanical, section-by-section refactor of all 3 ColdRoomPan-rt
> component classes, applied to a REAL, working N5 port (not a fresh stub) · real `./gradlew`
> builds against the actual N5 5.0.0.28 plugins (same toolchain as [Block 16]/[Block 29]) ·
> real `javac`+`java org.testng.TestNG` runs, JDK 25, zero Niagara runtime · one deliberate
> mutation-kill (bite) proof on the one new pure helper, isolated to a scratch copy. Markers:
> `[CERT-hw]` observed build/test/tool output this session (the dominant marker, as in
> [Block 16]/[Block 29]) · `[CERT]` a source file read directly, `file:line` · `[INFER]`
> deduction/design choice.
>
> N5 build-toolchain + HA/RT layer, §19 requires-execution phase. Connects [Block 37] (this block
> is the concrete implementation of §37.6's requirements 1-4, closing **B37-G6**), [Block 16]
> (reapplies its `niagara_config_home` mirror-redirection fix to a NEW PoC copy, confirming the
> hazard and fix both transfer unchanged), [Block 29] (reruns its 51 ported tests unchanged plus 4
> new ones, same plain-TestNG oracle, same isolated-mutation bite-proof discipline).
>
> **Type:** standard (evidence, requires-execution/§19 build-PoC)
>
> **Breakthrough:** the real ColdRoomPan-rt component tree — 3 classes, 8 `Clock.Ticket`/plain-field
> pieces of timer/interlock state — was migrated to the `niagaraSync` replication contract
> end-to-end (every timer now a `BNiagaraSyncTicket` child Property, every plain interlock field
> now a hidden Property, a documented no-stock-type FIFO-as-CSV-string design for the one state
> shape niagaraSync has no built-in type for) and **still builds and packages cleanly** — `jar`
> and `moduleTestJar` both `BUILD SUCCESSFUL`, and the pre-existing 51 pure-logic tests **plus 4
> new ones for the new codec pass 55/55 with zero regression**, with a real mutation-kill proving
> the new tests are not vacuous. This decisively answers the "requires-execution" half of B37-G6:
> the refactor this block's design implies is not merely theoretically sound (as [Block 37] left
> it) but **mechanically compiles, packages, and passes its own tests** against the real N5
> toolchain.

---

## 45.1 — Inventory: every raw timer/state field before migration `[CERT]`

Full-file reads of `BColdRoom.java`, `BDefrostController.java`, `BEvaporatorUnit.java` in the
(pre-refactor) `poc/coldroompan-n5/` copy this session. `[CERT]` citations below are to that
pre-refactor tree (identical to the still-live `poc/coldroompan-n5/` PoC, not touched this
session).

| Class | Field / call | Kind | Purpose |
|---|---|---|---|
| `BEvaporatorUnit` | `startDelayTicket` | `Clock.Ticket` | valve->evaporator start delay (rising-edge `runCmd`, BBooleanDelay-mirror pattern) |
| `BEvaporatorUnit` | `stopDelayTicket` | `Clock.Ticket` | fan run-on after valve close (falling-edge `runCmd`, `RUN_ON_DELAY` mode) |
| `BEvaporatorUnit` | `defrostEntryTicket` | `Clock.Ticket` | defrost-entry fan-off delay before resistance energizes |
| `BEvaporatorUnit` | `powerOnTicket` | `Clock.Ticket` | power-on stagger (soft-start) hold |
| `BEvaporatorUnit` | `lastCmd` | `boolean` field | edge-detect memory for the last applied `runCmd` |
| `BEvaporatorUnit` | `inDefrost` | `boolean` field | this unit currently owns/is-owned-by an active defrost cycle |
| `BEvaporatorUnit` | `freezeTripped` | `boolean` field | freeze-stat trip latch (anti-frost hysteresis) |
| `BEvaporatorUnit` | `startingUp` | `boolean` field | power-on stagger hold-active flag |
| `BEvaporatorUnit` | `defrostController` | `BDefrostController` field | back-reference the parent controller sets while this unit is defrosting (see §45.3 for why this one stays a plain field) |
| `BDefrostController` | `intervalTicket` | `Clock.Ticket` | interval-mode defrost re-arm timer |
| `BDefrostController` | `durationTicket` | `Clock.Ticket` | max-defrost-length timeout |
| `BDefrostController` | `pollTicket` | `Clock.Ticket` | periodic resistance-temp termination poll (5 s) |
| `BDefrostController` | `staggerTicket` | `Clock.Ticket` | inter-unit stagger delay before the next queued unit takes the token |
| `BDefrostController` | `defrostingUnit` | `int` field (default -1) | index of the unit currently holding the interlock token |
| `BDefrostController` | `waitingQueue` | `Deque<Integer>` field | FIFO of units requested while busy (design #1, room with 3+ defrost units) |
| `BDefrostController` | `pendingStaggerUnit` | `int` field (default -1) | unit whose stagger timer is running |
| `BDefrostController` | `lastSchedule` | `boolean` field | edge-detect memory for `scheduleInput` (SCHEDULE mode) |
| `BColdRoom` | `call1` | `boolean` field | zone-1 cooling-call hysteresis HOLD latch |
| `BColdRoom` | `call2` | `boolean` field | zone-2 cooling-call hysteresis HOLD latch (Room 1 only, staged) |

**18 pieces of state total**: 8 `Clock.Ticket` timers, 9 plain-field interlock/hysteresis
booleans/ints/queue, 1 same-tree back-reference (deliberately excluded, §45.3).
`BDefrostMode`/`BFanMode`/`BStagingMode` (enum classes) and `ColdRoomControl` (the pure-logic
class, zero Baja types by design) carry no Clock/field state and needed no migration — confirmed
by full-file read, zero hits.

## 45.2 — Real N5 `niagaraSync` API and the stock exemplar `[CERT]`

**`BINiagaraSyncCapableComplex`** — a pure marker interface, zero methods:
`interface BINiagaraSyncCapableComplex extends BInterface { Type TYPE = ...; }`
(`organized/baja/vineflower/niagara/niagaraSync/BINiagaraSyncCapableComplex.java:10-13`).

**`BNiagaraSyncTicket`** — `final class BNiagaraSyncTicket extends BComponent implements
BINiagaraSyncCapableComplex` with 2 Properties, both `flags=71`
(`READONLY|TRANSIENT|HIDDEN|DEFAULT_ON_CLONE`): `executionTicks: BNiagaraSyncTicks` and
`actionName: String`
(`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:24-25`). Factory:
`make(BRelTime time, Action action, BValue arg)` sets `executionTicks =
BNiagaraSyncTicks.make(time)` and `actionName = action.getName()`, optionally adding `arg` as a
dynamic child (:72-81). Lifecycle: `started()` reads the (already clock-corrected, [Block 37]
§37.4) `executionTicks.getRelTime()` — if `<= 0` (deadline passed while this station was not
running the folder), fires immediately via `post()`; otherwise arms a fresh LOCAL
`Clock.schedule()` (:83-94, exactly the "abstract portable tick, rebuilt concrete ticket" pattern
[Block 37] §37.4 named). `stopped()` cancels only the local Java ticket, leaving the Property
untouched so it re-arms correctly on whichever station starts the folder next (:96-102).
`cancel()`/`isExpired()` are self-guarding — `cancel()` no-ops safely if never armed, and always
leaves `executionTicks == NULL` (:117-128) — the getter this block's refactor relies on
(`getXxxTicket().cancel()`, no `!= null` guard needed) never returns a null reference because the
Property's own default value is `new BNiagaraSyncTicket()`, not `null`.

**`BNiagaraSyncTicks`** — `final class BNiagaraSyncTicks extends BSimple`, an
absolute-local-tick wrapper: `make(BRelTime)` stores `Clock.ticks() + relTime.getMillis()`;
`getRelTime()` reads back `ticks - Clock.ticks()` — i.e. always expressed relative to THIS JVM's
current clock, which is exactly what the periodic offset-correction job ([Block 37] §37.4)
re-bases on a standby->active promotion
(`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicks.java:26-28,76-78`).

**Stock exemplar — `com.tridium.kitControl.timer.BBooleanDelay`**
(`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java`), chosen
because `BEvaporatorUnit`'s OWN javadoc already names it as the design's actuation-sequence model
("mirrors kitControl BBooleanDelay") — this block's refactor is therefore not importing an
unrelated pattern, it is completing one the module's original author already pointed at.
`BBooleanDelay implements BINiagaraSyncCapableComplex` (:54) and declares a single
`ticket: BNiagaraSyncTicket` child Property, `flags=71`, default `new BNiagaraSyncTicket()`
(:49,72); `startOnTimer()`/`startOffTimer()` both call `this.getTicket().cancel();` FIRST, then
`this.setTicket(BNiagaraSyncTicket.make(delay, action, null));` (:257-269) — cancel-then-replace,
not replace-and-rely-on-implicit-unmount-stop. This exact two-line idiom
(`getXxxTicket().cancel(); setXxxTicket(BNiagaraSyncTicket.make(...));`) is what §45.3's refactor
uses at all 8 timer call sites. `BBooleanDelay` also promotes its own edge-detect memory
(`lastInput: boolean`, flags=71, :50/74) and its user-visible timer-active flags
(`onDelayActive`/`offDelayActive: boolean`, flags=3, no HIDDEN, :45-46/64-66) to Properties —
confirming both this block's `lastCmd`/`inDefrost`/etc. HIDDEN-flags choice (internal state, not
operator-facing) and that a DIFFERENT flag set (3, not 71) is correct for anything meant to be
visible in Workbench — not needed here since none of ColdRoomPan's promoted fields were
previously operator-visible either.

**Second exemplar — `com.tridium.kitControl.BLoopPoint`**
(`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java`) — `implements
BINiagaraSyncCapableComplex` (:72) and promotes `lastExecuteTime`/`rampEndTicks` to
`BNiagaraSyncTicks` Properties (:66-67,119-121) — but its OWN periodic re-arming timer stays a
PLAIN `private Clock.Ticket ticket` field (:not a Property), unconditionally re-armed by
`initTimer()` inside `started()` on every station (re)start (:412-422,
`Clock.schedulePeriodically(...)`). This is a DELIBERATE precedent this block's own design
checked against (§45.3): a periodic ticket that just needs to keep firing needs no replication of
its own — only a ONE-SHOT DEADLINE that must be resumed correctly on a specific station matters,
and `BLoopPoint` promotes exactly the deadline-shaped state (`lastExecuteTime`, `rampEndTicks`),
not the periodic ticket itself. This block's own timers (`startDelayTicket`, `durationTicket`,
etc.) are all one-shot deadlines (not periodic), so ALL of them are promoted to
`BNiagaraSyncTicket` — the `BLoopPoint` precedent does not create an exception here, but its
EXISTENCE is why the refactor deliberately checked each timer's shape before promoting it wholesale.

## 45.3 — Refactor implemented `[CERT-hw]`

Applied to the working copy `poc/coldroompan-n5-ha/ColdRoomPan-rt/src/com/angeles/ColdRoomPan/`
(forked this session from the already-built `poc/coldroompan-n5/`, §45 header). Diff sizes
(`diff -u` against the pre-refactor `poc/coldroompan-n5/` tree, this session):

| File | Lines added | Lines removed |
|---|---|---|
| `BEvaporatorUnit.java` | 323 | 57 |
| `BDefrostController.java` | 350 | 48 |
| `BColdRoom.java` | 81 | 12 |
| `ColdRoomControl.java` | 49 | 0 |

**Pattern applied identically at every one of the 8 `Clock.Ticket` call sites** (the `BBooleanDelay`
idiom, §45.2): replace `private Clock.Ticket xTicket;` with an `@NiagaraProperty(name = "xTicket",
type = "BNiagaraSyncTicket", defaultValue = "new BNiagaraSyncTicket()", flags = Flags.READONLY |
Flags.TRANSIENT | Flags.HIDDEN | Flags.DEFAULT_ON_CLONE)`; replace `xTicket = Clock.schedule(this,
delay, action, null);` with `setXTicket(BNiagaraSyncTicket.make(delay, action, null));`; replace
`if (xTicket != null) { xTicket.cancel(); xTicket = null; }` with `getXTicket().cancel();` (the
null-guard is no longer needed — `BNiagaraSyncTicket.cancel()` self-guards and the Property getter
never returns a Java `null`, §45.2). Example (`BEvaporatorUnit.java:825`,
`poc/coldroompan-n5-ha/`):
```java
setPowerOnTicket(BNiagaraSyncTicket.make(BRelTime.make(delayMs), powerOnExpired, null));
```

**Pattern applied to every plain-field boolean/int** (9 fields across `BEvaporatorUnit`,
`BDefrostController`, `BColdRoom`): `@NiagaraProperty(name = "...", type = "boolean"|"int",
defaultValue = "false"|"-1", flags = Flags.READONLY | Flags.TRANSIENT | Flags.HIDDEN |
Flags.DEFAULT_ON_CLONE)`, same flags as `BBooleanDelay.lastInput` (§45.2) since none of these were
previously operator-visible. Every read/write site changed from bare-field access to
`getX()`/`setX(v)`.

**`waitingQueue` (the one shape with no stock exemplar) — `[INFER]`, design choice.** niagaraSync
ships no list/queue-typed `BSimple`, so the FIFO of waiting unit indexes is encoded as a
comma-separated `String` Property (`waitingQueueCsv`,
`BDefrostController.java:218-223`, `poc/coldroompan-n5-ha/`) via a pure codec — extracted into
`ColdRoomControl.parseWaitingQueue(String)`/`formatWaitingQueue(Deque<Integer>)`
(`ColdRoomControl.java`, §45.5) — with `BDefrostController` reduced to two one-line delegating
methods (`loadQueue()`/`saveQueue()`) plus small `queueContains`/`queueAddLast`/`queuePollFirst`/
`clearQueue()` wrappers that read-mutate-write the Property so no parallel in-memory `Deque` can
ever drift from what niagaraSync actually replicates. Without this, a 3rd-or-later waiting unit's
place in line would be silently lost on failover — worse than losing a single ticket, since there
is no other synced source of truth for queue order. `String` is confirmed `BSimple` (not subject
to the validator's complex-type check, §45.6), so this choice adds no new validator obligation.

**`defrostController` — deliberately NOT a Property, `[INFER]`.**
`BEvaporatorUnit.defrostController` (a same-tree back-reference the parent
`BDefrostController.beginDefrost()` sets so a mid-cycle HOA-OFF lockout can call back into
`terminateCurrent()`) stays a plain Java field. Rationale: it is a REDUNDANT CACHE of information
the parent's own `defrostingUnit` Property (now synced) already encodes — "unit 2 is currently
defrosting" — not new state. Leaving it un-replicated is correct PROVIDED the parent re-derives it
on every promotion, so `BDefrostController.started()` was extended (`BDefrostController.java:845`,
`poc/coldroompan-n5-ha/`) to re-set `unit(getDefrostingUnit()).defrostController = this` whenever
`getDefrostingUnit() != -1` at start time — closing the correctness gap that would otherwise open
if only the ticket/boolean state were migrated and this back-reference were simply forgotten.

**Recursive lifecycle re-arm — no manual code needed, `[CERT]` (by construction from §45.2).**
`durationTicket`/`pollTicket`/`intervalTicket`/`staggerTicket`/all 4 `BEvaporatorUnit` tickets are
now ordinary CHILD Properties. Niagara's standard component-tree `started()` cascade already calls
`started()` on every child when the PARENT (re)starts — so `BNiagaraSyncTicket.started()`
(§45.2) re-arms each ticket automatically from its own (clock-corrected) `executionTicks` the
moment `BDefrostController`/`BEvaporatorUnit` (re)starts on the newly-active station. This block's
`BDefrostController.started()` change (previous paragraph) is needed ONLY for the
non-replicated `defrostController` back-reference — the tickets themselves needed zero additional
re-arm code, which is the entire point of the pattern (§37.6 requirement 4).

**All 3 classes now `implements BINiagaraSyncCapableComplex`**: `BEvaporatorUnit.java:288`,
`BDefrostController.java:225`, `BColdRoom.java:149` (`poc/coldroompan-n5-ha/`) — `BColdRoom` needs
it too (not just its leaf children) because it is the equip container that would itself be mounted
inside a `BINiagaraSyncFolder`, and requirement 1 (§37.6) is recursive over the whole subtree, not
just the components carrying timers.

**`ColdRoomControl.java` unchanged except the 2 new pure methods** — `parseWaitingQueue`/
`formatWaitingQueue`, 49 added lines, 0 removed; every existing pure-logic method
(`decideCall`, `applyHoa`, `resistanceCommand`, `freezeTrip`, `positiveDelayMs`,
`eligibleForDefrost`, `stopDelayShouldStopFan`, `intervalDelayMs`) is byte-identical to the
pre-refactor `poc/coldroompan-n5/` copy (`diff` confirmed empty for every OTHER file in the module
that this refactor did not touch: `BDefrostMode.java`, `BFanMode.java`, `BStagingMode.java`,
`CrLog.java` — zero diff, this session).

## 45.4 — Build results `[CERT-hw]`

`niagara_config_home`/`niagara_user_home` in `poc/coldroompan-n5-ha/gradle.properties` were
repointed at the NEW `-ha` copy's own local mirror (they were still pointing at the OLD
`poc/coldroompan-n5/.n5config` immediately after the `rsync` fork — a real miss this session,
fixed before the first build) — reapplying [Block 16] §16.3's install-write-hazard fix to the new
PoC tree, confirmed still necessary and still sufficient: `/mnt/c/ProgramData/Niagara/tridium/
config/5.0.0.28/modules` stayed at **247 jars**, checked before the first command and after every
build below, never mutated.

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew :ColdRoomPan-rt:jar` (first attempt, new `@NiagaraProperty` annotations added but generated boilerplate not yet regenerated) | **FAILED** — 18× `error: Slot with name <x> not found on class ...; have you run slot-o-matic?` — expected, same signature [Block 9]/[Block 16] already established for a fresh/changed slot set |
| 2 | `./gradlew :ColdRoomPan-rt:slotomatic` | **BUILD SUCCESSFUL** (50s) — regenerated the `//region ... BAJA AUTO GENERATED CODE` blocks for all 3 classes with the new Properties' `newProperty(...)`/getter/setter boilerplate |
| 3 | `./gradlew clean :ColdRoomPan-rt:jar` | **BUILD SUCCESSFUL** (3m22s) — 19-entry main jar, same anatomy shape as [Block 16] §16.7 (`MANIFEST.MF`, `NIAGARA4.SF/.RSA`, `module.xml`, `module-info.class`, 8 `.class` files, `module.palette`, `ColdRoomPan-rt.lexicon`) |
| — | extracted `parseWaitingQueue`/`formatWaitingQueue` into `ColdRoomControl.java`, delegated `BDefrostController.loadQueue()/saveQueue()` to them | — |
| 4 | `./gradlew clean :ColdRoomPan-rt:jar` (re-verify after the pure-helper extraction) | **BUILD SUCCESSFUL** (1m35s) |
| 5 | `./gradlew :ColdRoomPan-rt:moduleTestJar` (6 existing/ported test classes + new `WaitingQueueCodecTest`) | **BUILD SUCCESSFUL** (2m32s) — `compileModuleTestJava` a real recompile (not UP-TO-DATE), `ColdRoomPan-rt-module-test.jar` has all **7** expected `.class` files |

`ColdRoomPan-rt-module-test.jar` entries (`unzip -l`, this session): `ColdRoomControlDelayTest`,
`ColdRoomControlN5Test`, `ColdRoomControlSequenceTest`, `ColdRoomControlTest`,
`ColdRoomWritePathTest`, `ResistanceLockoutTest`, `WaitingQueueCodecTest` — 15 total entries
(same `META-INF` shape as [Block 16] §16.7/[Block 29] §29.4, minus the `NIAGARA4.SF`-adjacent
count difference from having 1 more test class).

5 `gradlew` invocations total (well under the ~20 cap), plus the `slotomatic` re-run and
`unzip`/`find`/`diff` diagnostic commands not counted above.

## 45.5 — Test results: 55/55 pass, zero regression, bite-proof on the new codec `[CERT-hw]`

**`niagaraTest`/`bin/test.exe` not re-attempted this block** — [Block 17]/[Block 29] already
established this install has NO valid `tridium:nre` license entitlement, blocking every headless
Niagara tool including `test.exe`'s TestNG runner (B17-G1/B29-G2, still open, out of this block's
scope). The plain-TestNG-on-JDK-25 lane ([Block 29] §29.7's own oracle) is reused unchanged for
this block's own regression check.

**Setup**: `poc/coldroompan-n5-ha/codegen-plaintestng/src/` — the same 5 already-ported test files
from [Block 29] (byte-identical, not re-ported), `ColdRoomControl.java` copied FRESH from the
refactored `ColdRoomPan-rt/src/` (i.e. INCLUDING the new `parseWaitingQueue`/`formatWaitingQueue`
methods — `diff` against the module's real source: empty, this session), plus one new file,
`WaitingQueueCodecTest.java` (4 `@Test` methods). Dependencies: the same LOCAL Gradle module-cache
jars [Block 29] resolved (`testng-7.12.0.jar`, `jcommander-1.83.jar`, `slf4j-api-2.0.16.jar`) —
re-used, not re-downloaded, confirmed present this session before compiling.

| # | Command | Result |
|---|---|---|
| 1 | `javac -cp testng-7.12.0.jar -d build $(find src -name "*.java")` (JDK 25, 6 source files, zero Niagara jars on the classpath) | **0 compile errors** |
| 2 | `java -cp <4 jars>:build org.testng.TestNG -testclass <6 classes>` | **`Total tests run: 55, Passes: 55, Failures: 0, Skips: 0`**, exit 0 |

**Per-class breakdown**: the original 51 ([Block 29] §29.7's table, unchanged: `ColdRoomControlTest`
22, `ColdRoomWritePathTest` 8, `ColdRoomControlDelayTest` 11, `ResistanceLockoutTest` 3,
`ColdRoomControlSequenceTest` 7) **plus 4 new**: `WaitingQueueCodecTest`
(`w1_emptyRoundTrips`, `w2_roundTripMultiple`, `w3_toleratesWhitespace`,
`w4_fifoOrderPreserved`) — `51 + 4 = 55` matches the suite total exactly.

**Bite-proof on the new codec** (same "prove a guard by breaking it" discipline [Block 29] §29.7.1
established, applied to an ISOLATED scratch copy, never the real module `src/`): a single-line
mutation to `codegen-plaintestng/src-mutated/.../ColdRoomControl.java`
(a copy of the scratch copy, not the module source):
```diff
- if (sb.length() > 0) sb.append(',');
+ if (sb.length() > 0) sb.append(' ');   // MUTATED (B45 bite-proof - space instead of comma)
```
— recompiled into a separate `build-mutated/` dir, rerun: **`Total tests run: 55, Passes: 53,
Failures: 2, Skips: 0`**, exit 1. The 2 failures, read from the TestNG report, are EXACTLY
`w2_roundTripMultiple` and `w4_fifoOrderPreserved` — the two multi-element-queue cases (a
space-joined `"2 3"` fails to re-`Integer.valueOf`-parse as two tokens through the unchanged
comma-splitting `parseWaitingQueue`) — no unrelated test flipped, confirming the new tests' signal
is load-bearing, not vacuous. The scratch mutation directory (`src-mutated/`, `build-mutated/`,
`report-mutated/`) was deleted after the proof; `diff` against the module's real
`ColdRoomControl.java` and against the UNMUTATED `codegen-plaintestng/src/` copy both returned
**zero differences**, confirming neither the real module source nor the baseline scratch copy was
ever touched by the mutation exercise. `[CERT-hw]` (TestNG XML results parsed, `diff` output, this
session).

10 real command attempts total this section (compile+run baseline, compile+run mutated, plus the
setup/diff/cleanup checks not counted), well under any budget cap.

## 45.6 — `NiagaraSyncComponentSpaceValidator` walk against the refactored classes `[CERT]`

Read in full this session (`organized/niagaraSync/vineflower/com/tridium/niagaraSync/
NiagaraSyncComponentSpaceValidator.java`); each rule walked against the refactored tree as it
would be evaluated if `BColdRoom` were mounted inside a `BINiagaraSyncFolder` (this block does not
have a live station to actually mount one into — the walk is static, matching the requirement's
own "statically check" wording; a live check remains B37-G3, unresolved by construction, §45.7).

**Rule 1 — `assertNiagaraSyncCapable`/`isNiagaraSyncCapable`
(`NiagaraSyncComponentSpaceValidator.java:136-156`): every `BComplex` value added/set inside a
sync folder must have `BINiagaraSyncCapableComplex.TYPE` in `Type.getInterfaces()`, checked
recursively over `getChildren(BComplex.class)`.** Walking the tree from a hypothetical
`BColdRoom` root:
- `BColdRoom` itself — **PASS** (`implements BINiagaraSyncCapableComplex`, `BColdRoom.java:149`).
- `BEvaporatorUnit[]` children — **PASS** (`BEvaporatorUnit.java:288`).
- `BDefrostController` child — **PASS** (`BDefrostController.java:225`).
- Every `BStatusBoolean`/`BStatusNumeric`-typed Property on all 3 classes (`runCmd`, `valveOut`,
  `evapOut`, `resistanceOut`, `coilTemp`, `resistanceTemp`, `scheduleInput`, `defrostActive`,
  `defrostSkipped`, `setpoint`, `zone1`, `zone2`, `cooling`, …) — **PASS**, confirmed directly
  (not merely by [Block 37]'s census table): `BStatusBoolean extends BStatusValue implements
  BIBoolean, BINiagaraSyncCapableComplex` (`organized/baja/vineflower/niagara/status/
  BStatusBoolean.java:20`), `BStatusNumeric extends BStatusValue implements BINumeric,
  BINiagaraSyncCapableComplex` (`organized/baja/vineflower/niagara/status/
  BStatusNumeric.java:19`).
- Every `BNiagaraSyncTicket`-typed Property (the 8 timers) — **PASS** (implements the interface
  on itself, §45.2).
- `BRelTime`/`BAbsTime`/`String`/`BFanMode`/`BDefrostMode`/`BStagingMode`-typed Properties
  (`startDelay`, `stopDelay`, `interval`, `duration`, `lastDefrostTime`, `defrostStart`,
  `nextDefrostTime`, `waitingQueueCsv`, `lastSkipReason`, `fanRunMode`, `mode`) — **OUT OF
  SCOPE, not `BComplex`**, confirmed directly: `BRelTime extends BSimple`
  (`organized/baja/vineflower/niagara/sys/BRelTime.java:14`), `BAbsTime extends BSimple`
  (`.../BAbsTime.java:19`), `BString extends BSimple` (`.../BString.java:10`), and
  `BFanMode`/`BDefrostMode`/`BStagingMode extends BFrozenEnum extends BEnum extends BSimple`
  (`organized/baja/vineflower/niagara/sys/BEnum.java:7`) — none of these are ever passed to
  `assertNiagaraSyncCapable` in the first place (`checkChildType`'s `isComplex()` filter,
  `NiagaraSyncComponentSpaceValidator.java:118-134`, excludes them by construction).
- **Verdict: the entire refactored subtree PASSES rule 1 — zero `niagaraSync.validation.
  unsupportedType` faults would fire.**

**Rule 2 — `checkReadonly` (`NiagaraSyncComponentSpaceValidator.java:74-116`): while
`service.getState()==standby`, any write inside a sync folder whose `Context` is not
`NsSync`/`NsContext` throws `niagaraSync.validation.readonly`.** Not a concern for this refactor's
OWN internal writes: per [Block 37] §37.2/§37.4, a station's sync folders are only ever
`started()` while that station is `active` — `BNiagaraSyncService.standby()` never starts the
folders at all, so none of `BColdRoom`/`BDefrostController`/`BEvaporatorUnit`'s own
engine-thread logic (which is what performs every `set()` call this refactor added) ever executes
while this station is standby in the first place. The rule exists to block EXTERNAL API writes
into the (stopped, mirror-only) tree while standby — orthogonal to this block's changes.

**Rule 3 — `checkLink`/`assertLinkNiagaraSyncCapable`
(`NiagaraSyncComponentSpaceValidator.java:164-208`): a `BLink` crossing a sync-folder boundary
must resolve through a schedule-import-extension zone.** None of the 3 refactored classes declare
or manage a `BLink` themselves — link wiring is a commissioning-time concern (design section 6,
per the module's own javadoc, e.g. `BEvaporatorUnit.java`'s `// TODO: link to proxy point`
comments) outside this block's scope. Not exercised, not a defect — no rule in this validator
requires the CONTROL LOGIC classes themselves to manage links; only whatever BLink a commissioning
engineer later adds is subject to this check, and that check is unconditional/structural (does
the link's source sit in a schedule-import zone), not something this refactor could satisfy or
violate from inside the component classes.

**Verdict: the refactored `ColdRoomPan-rt` tree would pass every one of
`NiagaraSyncComponentSpaceValidator`'s static admission rules** as currently constructed. This is
a STATIC verdict from reading the validator's own rules against the refactored source — it is
not, and cannot be without a live station (B37-G3), a confirmation that the validator's runtime
code path actually admits the tree without throwing; the walk covers every branch the validator's
source contains, but a live station remains the only source that can produce a `[CERT-hw]` result
for this specific claim.

## 45.7 — Remaining risks `[INFER]`

- **B37-G3 (unresolved by construction, carried forward)**: no live niagaraSync pair exists this
  session to confirm a MID-CYCLE promotion actually resumes a defrost cycle correctly end-to-end
  (durations counting down right, the FIFO queue handing off correctly, the back-reference
  restore in `BDefrostController.started()` firing at the right moment relative to `armTrigger()`
  and the children's own `started()` cascade). This block establishes that the framework's static
  admission rules are satisfied and that the refactor builds/packages/passes its existing tests —
  it does NOT and cannot (without hardware/license) prove the live failover behavior itself.
- **The `waitingQueueCsv` design is `[INFER]`, unprecedented in this corpus.** No stock Tridium
  module (censused across 7 modules in [Block 37] §37.5) was found encoding a variable-length
  queue as a Property — this block's comma-separated-`String` choice is a reasoned but
  UNVALIDATED-AGAINST-A-STOCK-PATTERN design. It is testable and tested (§45.5), and passes the
  static validator walk (§45.6, `String` is `BSimple`, no admission concern) — but a live pair
  test would be the first confirmation this specific encoding actually round-trips through the
  real `ValueDocEncoder`/live-event-stream replication path ([Block 37] §37.2), not just through
  this block's own `parseWaitingQueue`/`formatWaitingQueue` unit tests.
- **`BDefrostController.started()`'s back-reference restore is itself untested live.** The new
  `unit(getDefrostingUnit()).defrostController = this;` line (§45.3) is exercised by NEITHER the
  build (compiles, but that only proves it type-checks) NOR the plain-TestNG lane (which only
  tests `ColdRoomControl`'s pure methods, not `BDefrostController`'s own Baja lifecycle methods —
  no Baja runtime is available in that lane by construction, [Block 29] §29.7). This is a genuine
  coverage gap this block did not close: a `niagaraTest`/live-station run (blocked on B17-G1/
  B29-G2's license wall) is the only channel that could exercise it.
- **`niagaraTest` itself remains blocked** on the same `tridium:nre` license gate [Block 17]/
  [Block 29] already found — this block adds no new evidence on B17-G1/B29-G2, it only confirms
  (again) that the plain-TestNG fallback is the sole available oracle on this install.

## 45.x — Self-verification (METHODOLOGY §11)

**Full-path resolution anchors** (METHODOLOGY §11's citation-form convention: in-body citations
may use a bare filename when one source dominates a paragraph, but the self-verify anchor for
every load-bearing citation carries the full `filename:line` form so `verify-block.sh` can
resolve it inside this corpus):
`organized/baja/vineflower/niagara/niagaraSync/BINiagaraSyncCapableComplex.java:10-13`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:24-25`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:72-81`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:83-94`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:96-102`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:117-128`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicks.java:26-28`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicks.java:76-78`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncComponentSpaceValidator.java:74-116`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncComponentSpaceValidator.java:118-134`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncComponentSpaceValidator.java:136-156`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncComponentSpaceValidator.java:164-208`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:45-46`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:49`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:50`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:54`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:64-66`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:72`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:74`,
`organized/kitControl/vineflower/com/tridium/kitControl/timer/BBooleanDelay.java:257-269`,
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:66-67`,
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:72`,
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:119-121`,
`organized/kitControl/vineflower/com/tridium/kitControl/BLoopPoint.java:412-422`,
`organized/baja/vineflower/niagara/status/BStatusBoolean.java:20`,
`organized/baja/vineflower/niagara/status/BStatusNumeric.java:19`,
`organized/baja/vineflower/niagara/sys/BRelTime.java:14`,
`organized/baja/vineflower/niagara/sys/BAbsTime.java:19`,
`organized/baja/vineflower/niagara/sys/BString.java:10`,
`organized/baja/vineflower/niagara/sys/BEnum.java:7`.
Every citation into `poc/coldroompan-n5-ha/` (`BColdRoom.java`, `BDefrostController.java`,
`BEvaporatorUnit.java`) is genuinely `extern` to the resolver — that tree is gitignored (confirmed
pre-existing `.gitignore` rule, §45 header) and was never meant to be corpus-tracked, the same
declared convention [Block 16]/[Block 29] used for their own PoC-tree citations.

**Reproducibility check** — build attempt 4 (`clean :ColdRoomPan-rt:jar` after the pure-helper
extraction) reproduced the same 19-entry jar shape as attempt 3, confirming the extraction did not
change the packaged surface; the moduleTestJar's 15-entry/7-class shape was independently
confirmed via `unzip -l` this session.

**Token check** — every quoted error string (`Slot with name call1 not found...`,
`Slot with name intervalTicket not found...`, all 18 slot-o-matic errors), every `BUILD
SUCCESSFUL`/timing line, the `Total tests run: 55, Passes: 55/53, Failures: 0/2` lines, and the
mutation diff were copied verbatim from this session's captured command output — **≈24 distinct
load-bearing tokens**, all mechanically sourced from this session's own terminal capture (not
archived under `sources/probes/` per the task's single-block/no-archival scope, matching [Block
16]/[Block 29]'s own disclosed choice for PoC-tree-gitignored blocks).

**Marker tally — mechanized, literal `verify-block.sh` output, this session (reported verbatim,
not hand-recalled or rounded):**

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block45.md .
== verify-block: niagara5-block45.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 9  (adj 8)
   [CERT-live] 0
   [CERT] 10  (adj 9)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 9  (adj 8)
-- ratio -- [INFER]/[CERT*] = 8/17 = 0.47
-- [CERT] file:line citation resolution --
   [... 12 extern: 2 duplicate in-body short forms of BAbsTime.java:19/BString.java:10, 4
        duplicate in-body short forms of NiagaraSyncComponentSpaceValidator.java (each a
        repeat of one of the 4 full-path anchors below), and 6 genuinely-extern PoC-tree
        citations (BColdRoom.java/BDefrostController.java/BEvaporatorUnit.java — gitignored,
        never meant to be corpus-tracked) ...]
   [... 30 full-path anchor citations, ZERO RANGE! errors — every cited line range verified
        in-bounds against the real file's own line count ...]
   resolved 30 of 42
== exit 0 ==
```

Adjusted ratio **0.47** — just under the ~0.5 evidence-exhaustion threshold, and higher than
[Block 16] (0.22-0.24) or [Block 29] (0.20), consistent with this block being more DESIGN-heavy
than either predecessor: §45.3's 3 explicit design choices (`waitingQueueCsv` encoding, the
`defrostController` exclusion, the `BLoopPoint`-precedent check) and §45.7's risk list are genuine
`[INFER]` synthesis on top of the `[CERT]`/`[CERT-hw]` evidence, not evidence exhaustion — this
block is declared `Type: standard (evidence, requires-execution/§19 build-PoC)` matching [Block
16]/[Block 29]'s own convention for this gap-chain, and the ratio should be read as "design-heavy
build block," not as a signal this gap is running out of investigable ground (B45-G1/G2 remain
concretely open, §45.7).

**Resolution: 30 of 42 attempted, all 30 resolved `ok` with ZERO `RANGE!` errors** — every
citation given its full corpus-relative path (the anchor list above) points at a real line range
inside the actual file, independently confirmed by the tool's own line-count check. The other 12
unresolved entries are NOT separate unverified claims: 6 are the SAME `NiagaraSyncComponentSpace
Validator.java`/`BAbsTime.java`/`BString.java` citations' in-body SHORT forms (bare filename,
valid per METHODOLOGY §11's citation-form convention when one source dominates a paragraph), each
duplicating a full-path anchor that already resolved `ok`; the remaining 6 are the genuinely
`extern` `poc/coldroompan-n5-ha/` citations (`BColdRoom.java`, `BDefrostController.java`,
`BEvaporatorUnit.java`) — that PoC tree is gitignored (confirmed pre-existing `.gitignore` rule,
§45 header) and therefore invisible to a resolver that only walks the tracked corpus, the same
declared convention [Block 16] §16.9/[Block 29] §29.8 already established for their own PoC-tree
citations. The burden for those 6 is carried by this session's own direct command output (quoted
verbatim in §45.4/§45.5), not by the mechanized resolver.

**Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block45.md`.
The PoC tree exists at `/home/cristian/niagara5-research/poc/coldroompan-n5-ha/` — gitignored (the
parent's `.gitignore` already carried this exact rule before this session; no `.gitignore` edit
was needed or made). Per task scope (single-block deliverable), `CATALOG.md`/`INDEX.md`/
`RESEARCH-STATE.md` were **not** regenerated this session, matching [Block 16]/[Block 29]/[Block
37]'s own disclosed choice for this corpus's single-block-deliverable sessions.

**MCP-doc snapshots** — N/A, no MCP/context7/web source was used this session; every citation is
local (this corpus's organized decompiled `.java`, or this session's own PoC tree / command
output).

## 45.x — Child gaps opened

- **B45-G1 (requires-execution, merges into B37-G1/B37-G3)** — the single biggest open item: a
  live two-station niagaraSync pair (still blocked on the same `tridium:nre` license wall
  B17-G1/B29-G2 name) is needed to confirm (a) the refactored tree actually mounts inside a real
  `BINiagaraSyncFolder` without throwing (this block's §45.6 walk is static, not a live
  admission test), (b) a mid-defrost promotion resumes the cycle correctly using the now-synced
  `defrostingUnit`/`waitingQueueCsv`/ticket Properties, and (c) the `BDefrostController.started()`
  back-reference restore (§45.3) fires correctly relative to the framework's own child-started()
  cascade.
- **B45-G2** — the `waitingQueueCsv` comma-separated-`String` encoding (§45.3) is this block's own
  design, with no stock Tridium precedent found in [Block 37]'s 7-module census. A future focus
  should grep a WIDER set of modules (beyond the 7 already censused) specifically for ANY
  Tridium-authored list/queue-shaped niagaraSync Property, to confirm or refute whether this
  block's pattern matches an existing (undiscovered) convention or is genuinely novel.
- **B45-G3** — this block did not attempt to reproduce [Block 29] §29.4.1's benign
  `compileModuleTestJava` "cannot determine module name" anomaly against the new `-ha` PoC's own
  `.n5config` mirror (the anomaly did not appear in this session's `moduleTestJar` build output,
  plausibly because the stale `ColdRoomPan-rtTest.jar` this block deleted from the mirror before
  building, §45 header, was the self-referential artifact that triggered it in [Block 29]'s
  session). Not investigated further — B29-G5 already tracks the underlying plugin-internals
  question.
- **B45-G4** — `checkLink`/`assertLinkNiagaraSyncCapable` (§45.6 rule 3) was walked only for
  "does this refactor's OWN classes manage a BLink" (no) — a full commissioning-time link-wiring
  scenario (an operator linking a proxy point INTO one of these components while they sit inside a
  sync folder) was not modeled or tested, static or live.

## 45.x — Connections

- **[Block 37] §37.6** — this block IS the concrete implementation B37-G6 asked for: every
  requirement (1: implement the marker interface recursively; 2: promote all meaningful state to
  Properties; 3: use `BNiagaraSyncTicks` for tick-relative state — satisfied transitively via
  `BNiagaraSyncTicket`, which itself uses `BNiagaraSyncTicks` internally; 4: use
  `BNiagaraSyncTicket` as a child component for deferred actions) is now applied to the real
  ColdRoomPan-rt tree and PROVEN to build/package/test-pass, closing the gap between [Block 37]'s
  theoretical requirement table and a working artifact. B37-G3 (the live-pair defrost-resume
  probe) remains open — this block narrows it to a concrete, buildable artifact rather than a
  hypothetical migration.
- **[Block 16]** — the `niagara_config_home`/`niagara_user_home` install-write-hazard fix
  (§16.3) was reapplied to this session's NEW PoC copy and confirmed still necessary (the fork's
  `gradle.properties` still pointed at the OLD copy's mirror immediately after `rsync`) and still
  sufficient (247-jar `/mnt/c` guard held through every build).
- **[Block 29]** — the 51 ported pure-logic tests were re-run completely unchanged (byte-identical
  source files) and pass with zero regression; the plain-TestNG-on-JDK-25 oracle and the
  isolated-scratch-mutation bite-proof discipline (§29.7.1) were both reused directly for this
  block's one new test file, extending the pattern to a SECOND helper (`ColdRoomControl`'s new
  CSV codec) beyond the original `positiveDelayMs` case.
- **`build-n4-module` skill / ColdRoomPan project memory** — this block is new, actionable
  evidence that an eventual real HA migration of ColdRoomPan (if ever authorized as a production
  change, not just this PoC) has a concrete, already-compiling reference implementation to start
  from, distinct from the `coldroompan-defrost-time-le-0-bug` memory (a `Clock.schedule`
  validation bug, unrelated to HA replication) and from `panccadia-access-model-viewer-writeserver`
  (single-station write-path concern, no redundancy in scope there).
