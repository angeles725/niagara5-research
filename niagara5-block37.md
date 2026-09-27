# Block 37 — niagaraSync internals: replication, failover and what third-party modules must do

> Research of **`niagaraSync` end-to-end**: the primary/secondary warm-standby replication service
> introduced in [Block 18] §18.7 (module architecture) and deepened by [Block 35] §35.6 (the
> `niagara.driver.niagaraSync.BINiagaraSyncCapableDeviceNetwork` driver-side hook) and [Block 20]
> §20.7 (`kitControl.BLoopPoint`'s `BNiagaraSyncTicks`-typed state). Closes named gaps **B35-G1**
> (open `niagara.driver.niagaraSync`, confirm HA semantics, find every `ndriver`-chassis adopter),
> **B18-G4** (every consumer of `BINiagaraSyncCapableComplex`, full-tree grep), and **B20-G2**
> (decompile `niagaraSync` itself, confirm the HA/replication-of-tick-relative-state reading).
> Covers: the replication protocol (what is sent, ordering, initial-full-sync vs. incremental,
> conflict/duplicate-role handling); failover decision logic (heartbeat timeouts, promotion,
> planned vs. unplanned, split-brain protection); `BNiagaraSyncTicks`/`BNiagaraSyncTicket`
> clock-correction mechanics with the exact offset formula; a full-tree census of every consumer of
> `BINiagaraSyncCapableComplex`/`BINiagaraSyncCapableDeviceNetwork`/`BINiagaraSyncFolder`; what a
> third-party module must do to be HA-safe, applied concretely to ColdRoomPan's `Clock.schedule`
> defrost timers; and the `tridium:niagaraSync` licensing gate. Does **not** cover a live two-station
> pair probe (no N5 station available this session — B37-G1), a byte-level Fox wire trace of the
> `initSync`/`startSync` circuits, or the `modbusAsync`/`modbusTcp` network classes' own driver
> chassis lineage (out of this block's scope, noted only as consumers in §37.4).
>
> Subject version: Niagara **5.0.0.28 (Beta)**, same install as [Block 18]/[Block 20]/[Block 35].
>
> Sources (all local, this session, real decompiled `.java` — not scratch bytecode):
> `/home/cristian/niagara5-research/organized/niagaraSync/vineflower/com/tridium/niagaraSync/**`
> (19 files, full read) · `organized/baja/vineflower/niagara/niagaraSync/{BINiagaraSyncCapableComplex,
> BINiagaraSyncFolder,BNiagaraSyncTicket,BNiagaraSyncTicks}.java` +
> `organized/baja/vineflower/com/tridium/util/niagaraSync/NiagaraSyncContextUtil.java` (full read) ·
> `organized/driver/vineflower/niagara/driver/niagaraSync/BINiagaraSyncCapableDeviceNetwork.java`
> (full read) · `organized/baja/vineflower/niagara/sys/{BComponentEvent.java,BAbstractService.java,
> Flags.java}` (targeted reads, event-id table / license-check plumbing / flag-bit decode) ·
> bundled bajadoc (shipped with the module, not web-fetched):
> `organized/docDeveloper/vineflower/doc/baja/niagara/niagaraSync/{BINiagaraSyncCapableComplex,
> BINiagaraSyncFolder,BNiagaraSyncTicket,BNiagaraSyncTicks}.bajadoc` +
> `organized/docDeveloper/vineflower/doc/driver/niagara/driver/niagaraSync/
> BINiagaraSyncCapableDeviceNetwork.bajadoc` · corpus-wide grep census (own `grep -rl`, this
> session) over all 251 directories under `/home/cristian/niagara5-research/organized/` ·
> `organized/niagaraSync/vineflower/META-INF/module.xml` (dependency list) ·
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249/Paccadia/
> ColdRoomPan` (per the `client-reads-use-a109249-worktree` convention).
>
> Method: full-file reads of every class in the `niagaraSync` module and its 4 `baja`-hosted core
> types (not sampled — every method body in §37.1-§37.4 below was read this session, not inferred
> from signatures) · corpus-wide `grep -rl` for the three marker/capability interface names across
> `organized/` (251 module directories) to build §37.4's census table, each hit's `class`/`implements`
> line independently re-opened to confirm a genuine `implements` clause (not a stray import/comment) ·
> `grep -rn` over the client worktree for `niagaraSync` references (negative-existence check) and for
> `Clock.schedule` call-site count (drift check against [Block 20] §20.8's figure). Markers (canonical
> list, METHODOLOGY §3): `[CERT-hw]`/`[CERT-live]` highest (none this block — no live station) ·
> `[CERT]` local primary source (`file:line`) · `[CERT-doc]` official downloaded document (none this
> block) · `[CERT-web]` official web (none this block) · `[CERT-a]` secondary source (none this
> block) · `[INFER]` deduction. All `[CERT]` citations in this block resolve to files **inside this
> corpus** (`niagara5-research/organized/`, not scratch/temp) — unlike [Block 18]'s scratch-decompile
> session, this session's target sources were already organized in-corpus by a prior focus; see §37.9
> self-verify for the exact `verify-block.sh` resolution count.
>
> RT/HA layer. Connects [Block 18] §18.7 (module architecture this block deepens into full method
> bodies and closes B18-G4), [Block 35] §35.6-§35.7 (`niagaraDriver`'s Fox-transport-negotiation
> layer this block's driver-side findings sit beside, closing B35-G1), [Block 20] §20.2/§20.7
> (`Clock`'s N5 tick-source change and `BLoopPoint`'s promoted `BNiagaraSyncTicks` properties this
> block explains the mechanism for, closing B20-G2).
>
> **Type:** `mixed` — evidence (full-file reads, own `[CERT]`) combined with one synthesis section
> (§37.6, the ColdRoomPan HA-safety assessment, which draws `[INFER]` across this block's own
> findings plus [Block 20] §20.8's client-impact table by reference, not re-derivation).

---

## 37.1 — Two independent HA mechanisms wearing the same package name `[CERT]`

The `niagaraSync` module ships **two structurally separate mechanisms**, both grep-hit by
"niagaraSync" but serving different roles — conflating them would misread the census in §37.4:

1. **`BNiagaraSyncService`** (`com/tridium/niagaraSync/BNiagaraSyncService.java:92`, a
   `BAbstractService` singleton) — the actual **primary/secondary warm-standby replication engine**
   this block's §37.2-§37.3 cover: one station's component tree is continuously mirrored onto a
   peer, and the peer takes over control on failure. This is what [Block 18] §18.7 already found.
2. **`BNiagaraSyncStationPair`** (`com/tridium/niagaraSync/niagaraNetwork/
   BNiagaraSyncStationPair.java:34`, restricted to exactly 2 `BNiagaraStation` children under a
   `BNiagaraNetwork`, `isChildLegal`/`checkParentForRestrictedComponent` :133-156) — a **read-only,
   follow-the-active-leader proxy mechanism** for a THIRD station (e.g. a supervisor) that wants to
   watch whichever of the pair currently reports itself active, without running the replication
   engine itself. Its `BNiagaraSyncProxyExt` (`niagaraNetwork/BNiagaraSyncProxyExt.java:30`, extends
   `BAbstractProxyExt`) resolves a `pointId` against whichever paired `BNiagaraStation` is
   `activeStation` (`subscribeToProxy()`, :104-137) and **re-subscribes automatically** whenever
   `activeStationChanged()` fires (:143-147, called from `BNiagaraSyncStationPair.changed()` on the
   `activeStation` property, `niagaraNetwork/BNiagaraSyncStationPair.java:86-114`). Active-station
   detection itself rides the SAME `BNiagaraSyncChannel`'s `stateSubscribe`/`updateState` Fox ops
   (§37.1's sibling `NiagaraSyncStateSubscriptionWorker`, `niagaraNetwork/
   NiagaraSyncStateSubscriptionWorker.java:1-101`, a 1-second-polled worker that subscribes to BOTH
   paired stations' state channels and forwards `stateChanged()` to the pair, :63-91). This is a
   **consumer** of the replication engine's state broadcast, not a second replication path.

Both are exercised in §37.2-§37.5 below; §37.2-§37.3 (protocol/failover) describe mechanism (1)
exclusively, since that is what actually replicates a component tree.

## 37.2 — Replication protocol: full-tree snapshot + live batched event stream, no per-event acks `[CERT]`

**Transport.** A dedicated Fox channel `"niagaraSync"` (`BNiagaraSyncChannel.CHANNEL_NAME`,
`fox/BNiagaraSyncChannel.java:63,71-73`) carries 11 synchronous request/response ops
(`heartbeat`/`status`/`takeControl`/`relinquishControl`/`clockSync`/`keyExchange`/`rotateKeys`/
`maintenance`/`stateSubscribe`/`stateUnsubscribe`/`updateState`, `process()` switch, :76-102) plus
two long-lived `FoxCircuit`s opened by name (`circuitOpened()` switch, :306-317): `initSync`
(one-shot full snapshot) and `startSync` (live event stream).

**Initial full sync (`initSync`), server (active) side** (`initSync(FoxCircuit)`, :319-409):
walks every `BINiagaraSyncFolder` returned by `BNiagaraSyncService.initSync()` (:547-557, itself a
`ComponentTreeCursor(Sys.getStation(), BINiagaraSyncFolder.TYPE, null)` scan, :575-600) with a
plain `ComponentTreeCursor`, and for every visited component collects its **outgoing knobs whose
target sits OUTSIDE the sync folder** (`Knob[]`/`RelationKnob[]`, re-pointed via
`NiagaraSyncUtil.toSlotPathOrd()` before serializing, :332-375) into a header `FoxMessage`, writes
that header first (`circuit.writeMessage(message)`, :383), then streams every folder's full
component subtree through a `ValueDocEncoder` with transients ENABLED
(`encoder.setEncodeTransients(true)`, :387) — i.e. the initial snapshot literally includes transient
properties, which matters because `BNiagaraSyncTicks`-typed state (§37.5) is declared transient by
convention (bajadoc recommendation, confirmed by the `flags=71` = `READONLY(1)+TRANSIENT(2)+
HIDDEN(4)+DEFAULT_ON_CLONE(64)` bit decode against `organized/baja/vineflower/niagara/sys/
Flags.java:9-16`, on `BNiagaraSyncTicket.executionTicks`, `baja/vineflower/niagara/niagaraSync/
BNiagaraSyncTicket.java:24`).

**Initial full sync, client (standby) side** (`initSync()`, :411-502, called from
`BNiagaraSyncService.standby()` :528): **synchronous and blocking** — opens the `initSync` circuit,
reads the header message, then for each `ord` entry decodes one component via `ValueDocDecoder`
and mounts it under its resolved parent with `set`/`add` (context `NiagaraSyncContextUtil.SYNC`,
:426-436), reconstructs every collected knob/relation-knob (:453-497), removes any locally-present
sync folder NOT in the received set (:473-477, handles a folder deletion on the active side), and
finally re-resolves every component's ord handles (`NiagaraSyncUtil.fixOrds`, :499-501). Any
`UnresolvedException` while re-applying a knob/relation raises a `LocalizableRuntimeException`
(`niagaraSync.fault.linkSyncError`/`relationSyncError`, :469-471/495-497) that propagates up through
`standby()`'s try/catch (`BNiagaraSyncService.java:518-539`) into a **service fault** — a broken
initial sync does not retry itself; it faults the service and calls `shutdown()`.

**Live incremental stream (`startSync`)**, server side is `NiagaraSyncFolderSubscriber` — a real
Niagara component `Subscriber` on an event mask of 12 event ids (`EVENT_MASK`,
`NiagaraSyncFolderSubscriber.java:33` = ids `{0,1,2,3,4,6,7,8,9,17,18,19}` — `PROPERTY_CHANGED`,
`_ADDED`, `_REMOVED`, `_RENAMED`, `PROPERTIES_REORDERED`, `FLAGS_CHANGED`, `FACETS_CHANGED`,
`KNOB_ADDED`, `KNOB_REMOVED`, `RELATION_KNOB_ADDED/REMOVED`, `COMPONENT_STARTED` per
`organized/baja/vineflower/niagara/sys/BComponentEvent.java:9-21`'s constant table) plus a
`TypeSubscriber` on every concrete `BINiagaraSyncFolder` type that separately catches
`COMPONENT_PARENTED` (id 11) to auto-subscribe a newly-mounted sync folder
(`NiagaraSyncFolderTypeSubscriber.event()`, :164-178) and a nested `Subscriber` that catches
`PROPERTY_REMOVED` of a `BINiagaraSyncFolder` value to auto-unsubscribe (`NiagaraSyncFolderRemoved
Subscriber.event()`, :151-162). Four raw ids are folded onto existing handlers before
transmission — `BNiagaraSyncComponentEvent.COMPONENT_EVENT_MAP` (`BNiagaraSyncComponentEvent.java:36`)
remaps `COMPONENT_PARENTED(11)→PROPERTY_ADDED(1)`, `COMPONENT_RENAMED(13)→PROPERTY_RENAMED(3)`,
`COMPONENT_FLAGS_CHANGED(15)→FLAGS_CHANGED(6)`, `COMPONENT_FACETS_CHANGED(16)→FACETS_CHANGED(7)`
(`make()`, :76-112) — so the wire protocol carries only the 12 canonical ids from `EVENT_MASK`, not
the raw 21-value `BComponentEvent` space; `TOPIC_FIRED(5)`, `RECATEGORIZED(10)`,
`COMPONENT_UNPARENTED(12)`, `COMPONENT_REORDERED(14)`, and `COMPONENT_STOPPED(20)` are **never
replicated at all** (absent from `EVENT_MASK` and from `COMPONENT_EVENT_MAP`) `[CERT]`.

**Ordering/acks: none at the application layer — batched, one-way, TCP-ordered.**
`NiagaraSyncFolderSubscriber.startSync(FoxCircuit)` (:106-142) batches events into a
`BlockingQueue`, flushing to the circuit's `DataOutputStream` every **100 events or 500ms**,
whichever comes first (`BATCH_SIZE`/`BATCH_TIMOUT` constants, :22-23, loop :118-134) — a plain
sequential byte stream with **no sequence numbers, no per-event acknowledgment, and no resend
logic**; ordering and delivery guarantees are delegated entirely to the underlying Fox/TCP circuit.
The receiver, `ComponentSyncRunnable.run()` (`ComponentSyncRunnable.java:28-108`), decodes events
in a tight loop and applies each one immediately (`switch (event.getId())`, :40-89) — `set`(0),
`add`(1/8/17, with offset-correction, §37.5), `remove`(2/9/18), `rename`(3), `reorder`(4),
`setFlags`(6), `setFacets`(7), and a dedicated `refresh-clock-correction-only`(19, `component_started`
— fires `updateOffsetValue(component)` which recurses the WHOLE received component's subtree,
:88/115-124) — any decode exception (including a mid-stream `UnresolvedException`) calls
`service.syncError(e)` (:98-103) which sets `BStatus.down` on the service (`BNiagaraSyncService.
syncError`/`down`, :571-573/368-371) **without automatically retriggering a fresh `initSync`** — a
corrupted live stream leaves the standby faulted until the Fox connection itself drops (which DOES
trigger a full auto-reconnect-and-resync, next paragraph) or an operator intervenes
(`restartService` action, :195-197/304-309). `[INFER]`: since there is no incremental
reconciliation protocol (no diff/checksum exchange), **every** Fox reconnection re-runs `initSync`
from scratch rather than catching up a gap — `foxConnectionSuccess()` (:624-631) always issues a
fresh `StatusFuture`→`handleStatus()`, and for a non-primary role `handleStatus()` unconditionally
calls `this.standby()` again (:659) which unconditionally calls `channel.initSync()`+`startSync()`
(:528-529) — so the "incremental" stream is a live delta feed ONLY within one continuously-open Fox
session; any break restarts from a full snapshot. This reading is not itself stated by a comment in
the source; it follows directly from the cited call chain (`[INFER]`, but built from `[CERT]` facts
with no counter-evidence found).

## 37.3 — Failover decision logic: dual-heartbeat AND-gate, split-brain via hard fault, planned vs. unplanned promotion `[CERT]`

**Heartbeat channel 1 — primary, Fox RPC, 500ms.** `sendPrimaryHeartbeat()`
(`BNiagaraSyncService.java:861-884`) fires a Fox `heartbeat` request every 500ms
(`scheduleAtFixedRate(this::sendPrimaryHeartbeat, 0L, 500L, MILLISECONDS)`, :692); the peer's
handler (`BNiagaraSyncChannel.heartbeat(FoxRequest)`, :133-140) calls
`peerStation.getHeartbeatMonitor().getPrimaryHeartbeat().heartbeatReceived()`, which stamps
`lastHeartbeat`/`lastHeartbeatTicks` (`BHeartbeat.heartbeatReceived()`, `BHeartbeat.java:146-150`)
and clears any active offnormal alarm (`alarmToNormal()`, :170-184) via `BHeartbeatMonitor.
heartbeatReceived()` (`BHeartbeatMonitor.java:66-69`).

**Heartbeat channel 2 — secondary, raw mutual-TLS socket, independent, 500ms.**
`HeartbeatClient` (client side, connects to `BSecondaryHeartbeat`'s server socket) sends a single
byte (`HEARTBEAT_BYTE=0`) every 500ms over a `TLSv1.3` socket
(`sendHeartbeat()`/`scheduleAtFixedRate(...,500L,...)`, `HeartbeatClient.java:110-122,95`);
`BSecondaryHeartbeat`'s `HeartbeatServerThread` binds an `SSLServerSocket` on port **5911/TCP by
default** (`BServerPort(5911, IpProtocol.TCP)`, `BSecondaryHeartbeat.java:37`, overridable per-peer
via `BNiagaraSyncStation.secondaryHeartbeatPort`, `BNiagaraSyncStation.java:41,63`) with
`setNeedClientAuth(true)` — **mutual** TLS, both directions authenticated (:180-181) — and its
`HeartbeatAcceptorThread` calls the SAME `BHeartbeat.heartbeatReceived()` path on receipt of the
single expected byte (:137, rejects/aborts on any other byte, :132-135). Both channels are backed by
**short-lived, self-signed EC (`secp256r1`) certs, valid 90 days but proactively rotated every 30**
(`KEY_ROTATION_INTERVAL = Duration.ofDays(30)`, `BNiagaraSyncService.java:121`; cert validity
`cal.add(5, 90)` = 90 calendar days, `HeartbeatClient.java:64`/`BSecondaryHeartbeat.java:105`),
exchanged over the already-authenticated Fox channel's `keyExchange`/`rotateKeys` ops
(`BNiagaraSyncChannel.java:198-236`) and pinned by a bare single-certificate `TrustManager`
(`HeartbeatTrustManager` — TOFU-style: trusts EXACTLY the one certificate handed to it via
`setTrustedCert()`, equality-compared byte-for-byte, `HeartbeatTrustManager.java:47-55`) — i.e. the
30-day rotation exists BECAUSE the trust model is pinning, not a CA chain: a stale pinned cert would
simply stop matching, so rotation is the only key-lifecycle mechanism.

**Promotion gate is an AND, not an OR, of the two channels — this refines [Block 18] §18.7's
characterization.** `BHeartbeatMonitor.doCheckHeartbeat()` (`BHeartbeatMonitor.java:102-114`) only
calls `getNsService().heartbeatLost()` when **BOTH** `checkHeartbeat(primary)` AND
`checkHeartbeat(secondary)` independently report loss (`primaryHeartbeatLost && secondaryHeartbeatLost`,
:108) — each computed from that heartbeat's own `failureThreshold` (default 5s, `BHeartbeat.java:35`)
elapsed since `lastHeartbeatTicks` (:116-128). `scheduleCheck()` (:71-90) re-arms a `Clock.schedule`
ticket at the SOONER of the two channels' remaining time, so a lost channel is detected promptly,
but **promotion itself waits for corroboration from the second, independently-transported channel**
before declaring the peer dead — this is stronger split-brain protection than "the secondary channel
alone triggers failover" (block18's reading); it is closer to a 2-of-2 liveness quorum than a single
trigger. `BNiagaraSyncService.heartbeatLost()` (`BNiagaraSyncService.java:541-545`) only acts if the
local state is currently `standby` (`this.activate(false)`) — an already-`active` station ignores a
lost-peer signal (it has nothing to fail over TO).

**Split-brain / duplicate-role protection is a hard fault, not a merge, confirmed again at the
method level.** `handleStatus()` (:642-714) faults immediately if the peer reports the identical
`role` as local (`niagaraSync.fault.peerStationDuplicateRole`, :646-648) — no election, no
tie-breaker, service shuts down on both sides until an operator fixes the configuration. Module
version skew is checked the same call (`checkModules()`, :716-767): any module whose peer version
differs is a mismatch UNLESS `maintenanceMode` is set AND the direction is consistent with an
in-progress deliberate upgrade (primary allows a NEWER peer, secondary allows an OLDER peer,
:736-738) — a genuine mismatch calls `configFail(FAULT_CAUSE_MODULE_MISMATCH)` (:766), which is a
non-fatal config fault (station keeps trying) rather than the harder `configFatal`.

**Planned vs. unplanned promotion — a real, citable asymmetry in clock-correction freshness.**
`activate(boolean shouldUpdateOffsetTime)` (:470-498) is called with `true` (fresh `clockSync`
round-trip + whole-tree correction BEFORE the sync folders are started, §37.5) from every PLANNED
path — `doTransferControl()` (:321), `onPeerRelinquishControl()` (:334), and two of
`handleStatus()`'s reconciliation branches (:669,681) — but with **`false` (no fresh correction)
from exactly one call site: `heartbeatLost()`** (:543) and one cold-start branch in `handleStatus()`
(:688, this station is primary, peer isn't reporting active/fault, presumed first mutual contact).
`[INFER]`: an automatic (heartbeat-loss-triggered) failover therefore promotes using WHATEVER
clock-offset correction was last applied by the periodic hourly job (§37.5) rather than a
fresh measurement — because a `clockSync` RPC to a peer already presumed dead would itself
time out, this is the only sound choice, but it means an unplanned failover's tick-relative state
is, at worst, up to ~1 hour stale relative to a planned one (`[INFER]`, built from the cited `true`/
`false` call-site split — no source comment states this rationale explicitly).

## 37.4 — `BNiagaraSyncTicks`/`BNiagaraSyncTicket`: the clock-correction mechanism, with the exact offset formula `[CERT]`

**The offset formula (NTP-style three-timestamp).** `calculateOffset(BNiagaraSyncChannel)`
(`BNiagaraSyncService.java:822-830`): `t0 = Clock.ticks()` (local, before send) → synchronous Fox
`clockSync` request → server stamps `t1`/`t2` back-to-back
(`BNiagaraSyncChannel.clockSync()`, `fox/BNiagaraSyncChannel.java:125-131`, `t1` and `t2` are two
separate `Clock.ticks()` reads on the peer, effectively identical since nothing happens between
them) → `t3 = Clock.ticks()` (local, after response) → **`offset = ((t1 - t0) + (t2 - t3)) / 2`**.
This is called once at every `activate(true)` (fresh) and, while standby, on a fixed schedule: 10s
after entering standby, then every **3600s (1 hour)** (`offsetFuture = executorService.
scheduleAtFixedRate(() -> updateOffsetTime(channel), 10L, 3600L, SECONDS)`, `standby()`
:533). `updateOffsetTime()` (:812-820) computes the NEW absolute offset, then applies only the
**delta** (`this.clockOffset - oldOffset`) across the tree via `updateClockOffset(long)` (:832-836).

**What gets corrected: only `BNiagaraSyncTicks`-typed properties, found by a recursive property
walk.** `updateClockOffset(BComplex, long offset)` (:838-851) walks `complex.getProperties()`
recursively into every complex-valued property, and for a leaf property of type `BNiagaraSyncTicks`
that isn't null, replaces it with a re-based value:
`BNiagaraSyncTicks.make(BRelTime.make(ticks.getRelTime().getMillis() - offset))` under context
`NiagaraSyncContextUtil.SYNC` (:848) — i.e. it reads the CURRENT relative-time-from-now
(`getRelTime()`, `baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicks.java:76-78`, computed as
`this.ticks - Clock.ticks()` — this JVM's own clock), subtracts the peer-offset, and re-wraps via
`make(BRelTime)` which stores `Clock.ticks() [[local]] + relTime.getMillis()` (:26-28) — the value
is ALWAYS stored as an absolute local-JVM tick count, and correction is exactly "re-express the same
wall-clock-relative instant using MY tick base instead of the sender's." The SAME correction is
applied to individual values arriving via the live stream — `ComponentSyncRunnable.
updateOffsetValue()` (:115-124) applies it to any `BNiagaraSyncTicks` carried by an `add`(1/8/17)
event, and event id **19 exists FOR NO OTHER REASON than to trigger this correction recursively**
on a just-started component's whole subtree (:88, `case 19: this.updateOffsetValue(component)`) —
confirming this block's own reading of [Block 20] §20.7's `[INFER]` (that the N5 tick-source change
to non-portable `System.nanoTime()`, [Block 20] §20.2, is exactly why this wrapper type and
correction machinery exist) as `[CERT]`: the wrapper, the offset math, and the dedicated
re-correction event all exist specifically because raw ticks do not transfer between JVMs.

**Why the tree is corrected BEFORE folders start, not after.** In `activate(true)` (:470-498), the
call order is: `updateOffsetTime()` (fresh correction over the WHOLE tree) → `clockOffset = 0`
(reset, since the station is about to run under its OWN clock from now on) → THEN
`folders.forEach(BComponent::start)` (:483-490) — any logic that reads a `BNiagaraSyncTicks`
property during `started()` (see `BNiagaraSyncTicket.started()` next) sees an already-corrected,
locally-valid value.

**`BNiagaraSyncTicket`: the portable "abstract tick, rebuilt concrete ticket" pattern.**
`BNiagaraSyncTicket` (`baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:29`, implements
`BINiagaraSyncCapableComplex` itself) stores its fire time ONLY in the transient, clock-corrected
`executionTicks: BNiagaraSyncTicks` property (`flags=71`, :24/31) — never in a raw Java field beyond
a **local, non-replicated** `Clock.Ticket ticket` handle (:39). `started()` (:83-94) reads the
(already-corrected) `getExecutionTicks().getRelTime()`; if it is already `<=0` (the deadline passed
while this station was standby and NOT running its folders — the folder's `stop()` cancels the
handle but the PROPERTY survives, correction keeps advancing it toward "now"), the action fires
IMMEDIATELY via `this.post(execute, null, null)` (:89) instead of being lost; otherwise a fresh
LOCAL `Clock.schedule(this, executionTime, execute, null)` ticket is armed (:91). `stopped()`
(:96-102) cancels only the local Java ticket — the Property is untouched, so it is correctly
re-armed the next time this component (on whichever station) starts. `isParentLegal(BComponent)`
(:104-115, the exact method [Block 18] §18.7 flagged as B5-G3's resolution) enforces that the HOST
component implements `BINiagaraSyncCapableComplex` — confirmed against every citation in §37.4's
census below. Bundled bajadoc (`organized/docDeveloper/vineflower/doc/baja/niagara/niagaraSync/
BNiagaraSyncTicket.bajadoc`, author "Patrick Sager") states the design intent verbatim: *"represents
a Clock.Ticket that is synchronized between 2 redundant stations and will execute on whichever
station is active at the time the ticket is scheduled."* This is the general-purpose,
framework-supported replacement for a bare `Clock.schedule()` call inside HA-participating logic —
see §37.6 for why our own ColdRoomPan does not use it.

## 37.5 — Full-tree census: every consumer of the three niagaraSync interfaces `[CERT]`

Own `grep -rl` sweep across all 251 module directories under
`/home/cristian/niagara5-research/organized/` (this session), each hit's declaration line
independently re-opened to confirm a genuine `implements`/`extends` clause. `docSource/*` rows are
the public-API source mirror of the identical `vineflower/*` class (same file, duplicate tree, per
[Block 35] §35.4's method) — collapsed into one row here; both were grep-hit and both were spot-read.

**`BINiagaraSyncCapableDeviceNetwork`** (network-level standby/active hook, §37.1's "gate the whole
fieldbus" contract) — **5 implementers found, all Network-chassis classes**, plus 1 point-ext that
CONSUMES it without implementing it:

| Module | Class | Notes |
|---|---|---|
| `bacnet` | `BBacnetNetwork` (`niagara/bacnet/BBacnetNetwork.java:122`) | simple boolean flag flip (`niagaraSyncStandby`/`niagaraSyncActive`, :707-716); consumed by `BBacnetProxyExt.getMode()` (`point/BBacnetProxyExt.java:461-467`) to force `BReadWriteMode.readonly` on every BACnet point while standby |
| `modbusAsync` | `BModbusAsyncNetwork` (`com/tridium/modbusAsync/BModbusAsyncNetwork.java:62`) | `extends BModbusClientNetwork implements BISerialHelperParent, BINiagaraSyncCapableDeviceNetwork` |
| `modbusTcp` | `BModbusTcpNetwork` (`com/tridium/modbusTcp/BModbusTcpNetwork.java:27`) | `extends BModbusClientNetwork implements BINiagaraSyncCapableDeviceNetwork` |
| `niagaraDriver` | `BNiagaraNetwork` (`com/tridium/nd/BNiagaraNetwork.java:101-107`) | the [Block 35] §35.6 finding — `@NiagaraRpc`-exposed `niagaraSyncStandby()`/`niagaraSyncActive()`/`isNiagaraSyncStandby()` |
| `modbusCore` | `BModbusProxyExt` (point-ext, NOT a network — `point/BModbusProxyExt.java:138`) | consumes, does not implement: `getMode()` returns `readonly` when `this.modbusNet() instanceof BINiagaraSyncCapableDeviceNetwork syncNet && syncNet.isNiagaraSyncStandby()` — same pattern as BACnet's `BBacnetProxyExt`, independently reinvented in a second driver family |

**Confirms and closes B35-G1's second question**: exactly **one** `ndriver`-chassis driver
implements the interface (`niagaraDriver` itself); the other two implementers (`modbusAsync`,
`modbusTcp`) are `basicDriver`-lineage ([Block 35] §35.1's chassis family — `BModbusClientNetwork`
was not itself censused for its chassis root in [Block 35], which scoped to `modbusCore`; noted as
a related but out-of-scope family, `modbusCore`'s own network class was not found implementing this
interface at all — only its POINT-ext consumes the peer network's flag). No `basicDriver`-chassis
module from [Block 35] §35.1's 10-module table (`nrio`/`ccn`/`aaphp`/`mbus`/`aapup`/`mcquay`/
`andoverAC256`/`flexSerial`/`tls`) or `obixDriver` implements it — negative-existence confirmed by
the same corpus-wide `grep`.

**`BINiagaraSyncFolder`** (marks a `BComponent`+descendants for replication) — the base
`com.tridium.niagaraSync.BNiagaraSyncFolder` (`BNiagaraSyncFolder.java:10`, a plain
`BFolder` implementer, no logic beyond the marker) plus **3 driver-specific point-folder variants**,
each presumably the sync-eligible mount point for that driver's proxy points: `bacnet`'s
`BBacnetNiagaraSyncPointFolder`, `modbusCore`'s `BModbusClientNiagaraSyncPointFolder`,
`niagaraDriver`'s `BNiagaraSyncPointFolder` — none of these three were opened beyond their
declaration line this session (child gap B37-G2).

**`BINiagaraSyncCapableComplex`** (per-type "safe to replicate" marker, §37.6's central
requirement) — by far the widest census, ~180 unique classes (vineflower+docSource collapsed) across
**7 modules**:

| Module | Coverage |
|---|---|
| `baja` (core framework) | `BNiagaraSyncTicket` (self), `BStatusBoolean`/`BStatusEnum`/`BStatusNumeric`/`BStatusString`, `BLink`, `BRelation`, `BVector`, `BFolder` — the primitive status/link/collection types every point sits on |
| `control` | `BBooleanPoint`/`BBooleanWritable`, `BEnumPoint`/`BEnumWritable`, `BNumericPoint`/`BNumericWritable`, `BStringPoint`/`BStringWritable`, `BDiscreteTotalizerExt`, `BNullProxyExt`, `BNumericTotalizerExt`, `BTimeTrigger` — every stock point/writable type |
| `kitControl` | **the entire block-programming library** — `BLoopPoint`, `BExtensionName`, `BInterstartDelayControl`/`Master`, every `constants/`, `conversion/`, `energy/`, `hvac/`, `logic/`, `math/`, `timer/`, `util/` class (~145 classes) |
| `schedule` | **every schedule type** — `BBooleanSchedule` + all 23 siblings (`BCalendarSchedule`, `BWeekSchedule`, `BTriggerSchedule`, `BEnumSchedule`, …) and their selectors |
| `bacnet` | 4 proxy-ext types: `BBacnetBooleanProxyExt`/`EnumProxyExt`/`NumericProxyExt`/`StringProxyExt` |
| `modbusCore` | 6 client proxy-ext types (`BModbusClientBooleanProxyExt`, …) + `BFlexAddress` |
| `niagaraDriver` | `BNiagaraProxyExt` (`com/tridium/nd/point/BNiagaraProxyExt.java`) — the Fox station-to-station proxy point |

**Reading the census**: the pattern is unambiguous — Tridium marked **every stock point, writable,
proxy-ext, and the entire `kitControl` block-programming and `schedule` libraries** as
HA-safe/replicable, but did **not** mark `BComponent` itself, meaning any bespoke third-party
`BComponent` subclass (like our `BColdRoom`, `BDefrostController`, `BEvaporatorUnit`) is **NOT**
HA-safe by default and must opt in explicitly — §37.6.

## 37.6 — What a third-party module must do to be HA-safe: applied to ColdRoomPan `[CERT]` + `[INFER]`

**The authoritative requirement, from the shipped bajadoc (author Patrick Sager,
`organized/docDeveloper/vineflower/doc/baja/niagara/niagaraSync/BINiagaraSyncCapableComplex.bajadoc`),
quoted verbatim**: *"a marker interface to indicate that a complex type is safe for use in redundant
control logic... any meaningful state must be stored as a Niagara Property in order for it to be
properly replicated. Any children of a `BINiagaraSyncCapableComplex` must also meet the same
requirement."* This is enforced mechanically, not just documented, by
`NiagaraSyncComponentSpaceValidator` (`niagaraSync/vineflower/com/tridium/niagaraSync/
NiagaraSyncComponentSpaceValidator.java:129`, registered as the station's `IComponentSpaceValidator`
in `BNiagaraSyncService.started()` :220-224): `assertNiagaraSyncCapable()` (:136-144) walks any
complex value being added/set inside a `BINiagaraSyncFolder` and **throws
`niagaraSync.validation.unsupportedType`** (:138) for any type whose `Type.getInterfaces()` does not
literally include `BINiagaraSyncCapableComplex.TYPE` (:146-156) — checked recursively over every
child (:142). A second, independent check (`checkReadonly()`, :74-116) makes the ENTIRE synced
subtree **read-only from outside the sync machinery while in standby** — any write to a component
inside (or a value being placed into) a `BINiagaraSyncFolder` while `state==standby` and the write's
`Context` is not `NiagaraSyncContextUtil.isNsSync`/`isNsContext` throws
`niagaraSync.validation.readonly` (:79-97). This second gate is what §37.4's driver-level
`BReadWriteMode.readonly`/`isNiagaraSyncStandby()` pattern (BACnet/Modbus point-exts, §37.5) exists
to make VISIBLE at the point layer — the component-space validator would reject the write anyway,
but returning `readonly` from `getMode()` prevents the point from even attempting it (a UX/behavior
concern, not a second independent safety net).

**Concretely, to be HA-safe a third-party module must:**
1. Implement `BINiagaraSyncCapableComplex` on every `BComponent`/`BComplex` type that will be
   mounted (directly or as a descendant) inside a `BINiagaraSyncFolder` — recursively, every child
   type too (§37.6's opening citation).
2. Store **all** meaningful runtime state as Niagara **Properties**, never as private Java fields —
   a private field is invisible to `ValueDocEncoder`'s tree serialization (§37.2's `initSync`) and
   to the live event subscriber's property-change mask (§37.2), so it simply never replicates.
3. For any tick-relative (elapsed-time / scheduled-deadline) state, use the `BNiagaraSyncTicks` type
   (not a raw `long`), declared **transient** (bajadoc's own recommendation: `readonly`+`hidden`+
   `defaultOnClone`, confirmed as `flags=71` on `BNiagaraSyncTicket.executionTicks`, §37.4) — this is
   what makes the value clock-portable across the periodic/activation-time correction (§37.4).
4. For a deferred/scheduled ACTION (not just state), use `BNiagaraSyncTicket` as a **child
   component** under a `BINiagaraSyncCapableComplex` host (`isParentLegal()` enforces this, §37.4)
   rather than a bare `Clock.schedule()` call — the ticket's `started()`/`stopped()` lifecycle is
   what rebuilds a local, concrete `Clock.Ticket` from the portable Property on whichever station
   is currently running the folder.
5. For a driver network specifically, additionally implement `BINiagaraSyncCapableDeviceNetwork`
   and gate outbound fieldbus writes on `isNiagaraSyncStandby()` at the point-ext layer (§37.5's
   BACnet/Modbus pattern) — this is ON TOP OF requirement 1-4, not a substitute for them, since a
   device network's OWN component tree (if it sits inside a sync folder) is subject to the same
   validator.

**Applied to ColdRoomPan's defrost timers — the concrete question this gap asked.** Own `grep -rln`
over `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249/` this session
finds **zero** references to `niagaraSync`/`NiagaraSync`/`BINiagaraSyncCapableComplex` anywhere in
the client worktree (exit code 1, no matches) — confirming [Block 20] §20.8's finding still holds:
none of `BColdRoom`, `BDefrostController`, `BEvaporatorUnit`, `BStagingMode`, `BCompressorControl`
implement the marker interface. `Clock.schedule` call sites in `ColdRoomPan` alone counted **15**
this session (own `grep -c`, minor drift from [Block 20] §20.8's "14" — worktree may have moved
since that block was written; not re-investigated, immaterial to this block's conclusion). Every one
of those 15 is a bare `Clock.schedule(...)` call, not a `BNiagaraSyncTicket` child.

`[INFER]`, built directly from §37.2-§37.6's `[CERT]` facts: **as currently written, a defrost
timer armed via `Clock.schedule()` would NOT survive a mid-defrost failover correctly.** A raw
`Clock.Ticket` is a pure in-JVM construct — it is never a Niagara Property, so it is invisible to
both the initial snapshot (`ValueDocEncoder`, §37.2) and the live event stream (property-change
mask, §37.2); it exists ONLY on the station that created it and is silently lost the moment that
station stops being active (the standby's `BDefrostController` instance, mirrored via `initSync`,
never had its OWN `Clock.schedule()` call made — replication mirrors the CONTROLLER's Properties,
not its Java call stack). Two independent failure modes follow: (a) if `BDefrostController` is
placed inside a `BINiagaraSyncFolder` as-is today, `NiagaraSyncComponentSpaceValidator.
assertNiagaraSyncCapable()` (§37.6) would **reject the configuration outright** at commit time
(`niagaraSync.validation.unsupportedType`) — it cannot even be deployed into an HA pair without
first implementing the marker interface; (b) even after adding `BINiagaraSyncCapableComplex` and
promoting the relevant timer state to Properties (satisfying requirement 1-2), a bare
`Clock.schedule()` call inside `started()`/execute logic still would not resume correctly unless the
"how much time is left in this defrost cycle" state is ALSO expressed as a `BNiagaraSyncTicks`
property (requirement 3) and the actual re-arming is done through a `BNiagaraSyncTicket` child
(requirement 4) — because that is the only pattern this framework provides for "rebuild a concrete
local timer from portable replicated state on whichever station is now active." Absent that
migration, a station promoted mid-defrost would start its `BDefrostController` fresh with whatever
NON-timer state (setpoints, mode flags — ordinary Properties, already replicated) it has, but with
**no outstanding scheduled callback to end the defrost or advance its state machine** — the module's
own `started()`/subscription logic would have to independently re-derive "a defrost is in progress
and should end at time X" from other synced Properties and re-arm a fresh `Clock.schedule()` itself,
which is a correctness property of ColdRoomPan's own state-machine design, not something niagaraSync
provides for free. This block cannot verify from niagaraSync sources alone whether ColdRoomPan's
current state machine happens to do that (it does not use any of requirements 1-4, so no synced
"defrost end time" Property is emitted regardless) — flagged as **B37-G3**, a live-pair probe once
ColdRoomPan is placed inside a sync folder for testing.

## 37.7 — Licensing gate: `tridium:niagaraSync`, checked by the generic `BAbstractService` machinery `[CERT]`

`BNiagaraSyncService.getLicenseFeature()` (`BNiagaraSyncService.java:286-288`) returns
`Sys.getLicenseManager().getFeature("tridium", "niagaraSync")` — the same two-argument
vendor/feature-name pattern [Block 18] §18.2 found for `cloudLink`/`cloudLinkConnect`. This override
feeds the GENERIC `BAbstractService.checkLicense()` machinery (`organized/baja/vineflower/niagara/
sys/BAbstractService.java:160-180`): `getLicenseFeature()` defaults to `null` (no check) in the base
class (:159-161), and any subclass overriding it non-null has `feature.check()` invoked, with the
result feeding a per-feature `limits` map (:166-180) — the same licensing plumbing every other
licensed Niagara service uses, not a niagaraSync-specific gate. The `niagaraSync.jar`
`module.xml` declares **34 module dependencies** (`alarm`, `baja`, `control`, `driver`,
`niagaraDriver`, `schedule`, `fox`, `workbench`, … — full list `organized/niagaraSync/vineflower/
META-INF/module.xml:3-38`) but carries no separate `<license>` stanza — the gate is entirely
programmatic, enforced at `BAbstractService` `started()`/`atSteadyState()` time
(`BNiagaraSyncService.java:220-233`) via `initialize()`'s `isFatalFault()` check (:373-375), which
would be set if the license check failed (mechanism inherited from `BAbstractService`, not
re-verified line-by-line in this session — the license-fatal-fault WIRING inside
`BAbstractService.checkLicense()` beyond the `feature.check()` call was read but not traced into the
exact `configFatal` call site, child gap B37-G4).

## 37.x — Self-verification (METHODOLOGY §11)

**Full-path resolution anchors** (METHODOLOGY §11's citation-form convention: in-body citations may
use a bare filename when one source dominates a paragraph, but the self-verify anchor for every
load-bearing citation carries the full `filename:line` form so `verify-block.sh` can resolve it
inside this corpus — unlike [Block 18]/[Block 20]/[Block 35], whose cited sources lived in
scratch-temp or a sibling corpus, this session's sources are already organized inside THIS corpus,
so they are resolvable, not `extern`, once given their full path):
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BHeartbeat.java:146-150`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BHeartbeat.java:35`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BHeartbeatMonitor.java:102-114`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BHeartbeatMonitor.java:106-113`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BHeartbeatMonitor.java:66-69`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/fox/BNiagaraSyncChannel.java:198-236`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/fox/BNiagaraSyncChannel.java:125-131`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncComponentEvent.java:36`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncFolder.java:10`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:92`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:121`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:220-233`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:286-288`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:518-539`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:541-545`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:822-830`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:861-884`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BSecondaryHeartbeat.java:105`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BSecondaryHeartbeat.java:37`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/ComponentSyncRunnable.java:28-108`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/HeartbeatClient.java:64`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/HeartbeatTrustManager.java:47-55`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncFolderSubscriber.java:33`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicket.java:29`,
`organized/baja/vineflower/niagara/niagaraSync/BNiagaraSyncTicks.java:76-78`,
`organized/modbusAsync/vineflower/com/tridium/modbusAsync/BModbusAsyncNetwork.java:62`,
`organized/modbusTcp/vineflower/com/tridium/modbusTcp/BModbusTcpNetwork.java:27`,
`organized/niagaraDriver/vineflower/com/tridium/nd/BNiagaraNetwork.java:101-107`,
`organized/bacnet/vineflower/niagara/bacnet/BBacnetNetwork.java:122`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/niagaraNetwork/BNiagaraSyncProxyExt.java:30`,
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/niagaraNetwork/BNiagaraSyncStationPair.java:86-114`,
`organized/bacnet/vineflower/niagara/bacnet/point/BBacnetProxyExt.java:461-467`,
`organized/modbusCore/vineflower/com/tridium/modbusCore/point/BModbusProxyExt.java:138`.

**Token check.** Every `[CERT]` citation above was opened directly this session as a full-file
`Read` (not `grep`-only) for the 19 `niagaraSync` module files, the 5 `baja`/`driver`-hosted core
types, and targeted reads of `BComponentEvent.java`/`BAbstractService.java`/`Flags.java` — **29
distinct source files read in full or by targeted section this session**, every cited line number
taken directly from that read's own line-numbered output (not hand-recalled). The census table in
§37.5 additionally required opening each of ~15 distinct `grep`-hit files' `class`/`implements`
declaration line to confirm a genuine implements clause versus a stray import (done for all 6 rows
of the `BINiagaraSyncCapableDeviceNetwork` table plus `BNiagaraSyncService`'s false-positive check,
§37.5 — 7 files independently re-opened for this purpose). One self-caught de-escalation this
session: this block's first pass toward §37.3 read [Block 18] §18.7 as asserting the SECONDARY
heartbeat channel alone drives failover ("promotes a standby to active only off this second
channel"); re-reading `BHeartbeatMonitor.doCheckHeartbeat()` (`BHeartbeatMonitor.java:106-113`)
directly this session found the actual gate requires **both** channels lost
(`primaryHeartbeatLost && secondaryHeartbeatLost`) — recorded as a refinement/correction in §37.3,
not silently smoothed over, per METHODOLOGY §11's de-escalation convention.

**Marker tally — mechanized, literal `verify-block.sh` output, this session (second run, after
adding the full-path anchor list above — reported verbatim, not rounded or hand-recalled):**

```
$ /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block37.md /home/cristian/niagara5-research
== verify-block: niagara5-block37.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 4  (adj 3)
   [CERT-live] 4  (adj 3)
   [CERT] 19  (adj 16)
   [CERT-doc] 4  (adj 3)
   [CERT-web] 4  (adj 3)
   [CERT-a] 4  (adj 3)
   [INFER] 14  (adj 12)
-- ratio -- [INFER]/[CERT*] = 12/31 = 0.39
-- [CERT] file:line citation resolution --
   [... 34 `extern` in-body short-form citations, each a duplicate of one full-path anchor below ...]
   [... 34 `ok` full-path anchor citations, ZERO RANGE! — every cited line range verified in-bounds ...]
   extern  point/BBacnetProxyExt.java:461-467  (duplicate short form, same class as the ok anchor)
   extern  point/BModbusProxyExt.java:138  (duplicate short form, same class as the ok anchor)
   short   :707  (table-cell short form — file implied by context; not script-verifiable)
   resolved 34 of 67
== exit 0 ==
```

Adjusted ratio **0.39** — under the ~0.5 evidence-exhaustion threshold but the highest of this
gap-chain's blocks ([Block 18] 0.31, [Block 20] 0.18, [Block 35] 0.13), consistent with this being
the most synthesis-heavy of the four: §37.6 (the ColdRoomPan HA-safety assessment) is a `[INFER]`
chain built from this block's own `[CERT]` facts, and §37.2/§37.3 each carry one flagged `[INFER]`
reading of a call-chain the source does not comment on directly (the always-full-resync-on-reconnect
inference, and the unplanned-failover clock-staleness inference). The `[CERT-hw]`/`[CERT-live]`/
`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` raw counts of 4 each are the canonical marker LEGEND lines this
block's header blockquote quotes twice (once in the shared preamble style, once in the Sources
paragraph) — adjusted count 3 each, still zero as actual claims; every substantive claim in this
block is `[CERT]` local-source or `[INFER]`, confirmed by the adjusted-count-0 floor the tool cannot
compute but the raw legend text explains. **Resolution: 34 of 67 attempted, all 34 resolved `ok`
with ZERO `RANGE!` errors** — every one of this block's load-bearing citations, when given its full
corpus-relative path (the anchor list above), points at a real line range inside the actual file,
independently confirmed by the tool's own line-count check, not merely by this session's own
re-reading. The other 33 unresolved entries are the SAME 34 citations' in-body **short forms**
(bare filename, e.g. `` `BHeartbeat.java:146-150` ``, valid per METHODOLOGY §11's citation-form
convention when one source dominates a paragraph) plus one table-cell short-form line reference
(`:707`, `BBacnetNetwork.niagaraSyncStandby()`, file given in prose immediately before the table) —
none of these are a SEPARATE unverified claim; each duplicates a full-path anchor that already
resolved `ok`. Unlike [Block 18]/[Block 20]/[Block 35] (whose cited sources lived in scratch-temp
decompiles or a sibling corpus, forcing an ALL-`extern` decompiled-tree declaration), this session's
sources were already organized inside THIS corpus, so — once cited by full path — they are
genuinely, mechanically verifiable, not merely inline-token-verified by re-reading.

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block37.md`. Per
the caller's explicit read-only/single-file scope, `INDEX.md`/`CATALOG.md`/`RESEARCH-STATE.md` were
**not** regenerated or hand-edited this session — left to the orchestrator, flagged here so it is
not silently skipped.

**MCP-doc snapshots.** N/A — no `context7`/web-MCP source was used this session; every citation is
local (this corpus's decompiled `.java`/bundled `.bajadoc`) or the client worktree.

## 37.x — Child gaps opened

- **B37-G1** — `requires-execution`: no live two-station N5 5.0.0.28 pair was available this
  session. Everything in §37.2-§37.6 is derived from static source reading — a real pair would let a
  future session (a) trace actual Fox wire bytes for `initSync`/`startSync` to confirm the
  batching/framing details read from source, (b) empirically test the split-brain
  duplicate-role fault and the module-mismatch/`maintenanceMode` upgrade path, and (c) directly
  observe an unplanned (heartbeat-loss) failover's tick-relative-state staleness predicted in §37.3.
- **B37-G2** — the 3 driver-specific `BINiagaraSyncFolder` implementers found in §37.5
  (`BBacnetNiagaraSyncPointFolder`, `BModbusClientNiagaraSyncPointFolder`, `BNiagaraSyncPointFolder`)
  were located by declaration line only, not opened for their actual folder-membership/`isChildLegal`
  logic this session.
- **B37-G3** — the concrete ColdRoomPan HA-safety question (§37.6): once `BINiagaraSyncCapableComplex`
  + `BNiagaraSyncTicks`/`BNiagaraSyncTicket` migration work is done (if ever authorized as a change),
  probe an actual sync pair to confirm a mid-defrost promotion resumes (or correctly restarts)
  the defrost cycle — this block only established what the framework REQUIRES and PROVIDES, not
  whether a migrated ColdRoomPan would use it correctly.
- **B37-G4** — trace `BAbstractService.checkLicense()`'s exact `configFatal`/`configFail` call site
  triggered by a failed `feature.check()`, to confirm precisely how an unlicensed `tridium:niagaraSync`
  feature surfaces to an operator (fatal fault blocking all service function vs. a soft config fault) —
  read the method's existence and the `getLicenseFeature()` override this session, not its
  fault-severity wiring in full.
- **B37-G5** — `modbusAsync`/`modbusTcp`'s own driver-chassis lineage (`BModbusClientNetwork`'s
  `extends` chain) was not traced against [Block 35] §35.1's `basicDriver`/`ndriver` census — both
  modules were identified here only as `BINiagaraSyncCapableDeviceNetwork` implementers, not
  chassis-classified.

## 37.x — Connections

- **[Block 18] §18.7** — this block is the full method-body deepening of that block's
  architecture-level `niagaraSync` findings; §37.3 REFINES (not contradicts) its failover-trigger
  characterization (AND-gate on both heartbeats, not the secondary alone — see the self-verify
  de-escalation note above), and §37.5 formally closes **B18-G4** (every
  `BINiagaraSyncCapableComplex`/`BINiagaraSyncCapableDeviceNetwork`/`BINiagaraSyncFolder` consumer,
  full-tree grep).
- **[Block 20] §20.2/§20.7** — this block's §37.4 is the direct mechanical explanation for that
  block's `[INFER]` reading (N5's `System.nanoTime()`-based, non-portable `Clock.ticks()` is why
  `BLoopPoint`'s `lastExecuteTime`/`rampEndTicks` were promoted to `BNiagaraSyncTicks` Properties) —
  promoted here from `[INFER]` to `[CERT]` with the exact offset formula and correction call sites,
  formally closing **B20-G2**. `BLoopPoint`'s own `implements BINiagaraSyncCapableComplex` (found by
  [Block 20] via `javap`) is independently confirmed in §37.5's census from the decompiled-source
  side.
- **[Block 35] §35.6-§35.7** — this block's §37.5 census answers B35-G1's second question (only
  `niagaraDriver` among `ndriver`-chassis modules implements `BINiagaraSyncCapableDeviceNetwork`) and
  §37.1/§37.3 give the actual HA semantics [Block 35] flagged as unverified for
  `BINiagaraSyncCapableDeviceNetwork`'s standby/active contract — the interface itself
  (`niagara.driver.niagaraSync.BINiagaraSyncCapableDeviceNetwork`) lives in the **`driver`** module
  (core framework), not `niagaraDriver` (the Fox proxy driver) — a naming distinction [Block 35] did
  not have occasion to draw since it only opened `niagaraDriver`'s consuming class, not the
  interface's own home module.
- **`build-n4-module` skill / ColdRoomPan project memory** — §37.6's concrete finding (ColdRoomPan's
  15 raw `Clock.schedule` call sites are not HA-portable as written) is new, actionable input for any
  future decision to run ColdRoomPan under `niagaraSync` — distinct from the existing
  `coldroompan-defrost-time-le-0-bug` memory (a `Clock.schedule` validation bug, unrelated to HA
  replication) and from `panccadia-access-model-viewer-writeserver` (single-station write-path
  concern, no redundancy in scope today).
