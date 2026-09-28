# Block 92 — Closing five child gaps on box protocol internals and the alarm subsystem: alarm-acknowledgment attribution generalizes corpus-wide, the box JSON message-dispatch envelope, why box's channel hierarchy was decoupled from `alarm`/`history`, a byte-identical N4-vs-N5 `alarm.adb` row format, and the unlicensed-`niagaraSync` fault-severity wiring

> Research closing five child gaps (six gap IDs — **B78-G3** and **B37-G4** are the same underlying
> mechanism, per the task's own overlap note, and are closed together in one section). Covers:
> **B83-G2** (niagara5-block83.md §83.5/§83.x's own text: *"Whether the manual, non-`ComponentSlotMap`
> alarm-attribution pattern found in `analytics`'s `BNaServlet`/`UpdateAlarms` (§83.5) is the GENERAL
> mechanism for all N5 alarm acknowledgement, or specific to the `analytics` websocket API — the primary
> `alarm` module's own UI/servlet-driven ack path was not opened this session."*); **B83-G3**
> (niagara5-block83.md's own text: *"The plain-JSON (non-`'F'`-fragment) box frame path's own internal
> message-type/method-dispatch structure beyond the `p`/`v`/`id` envelope keys read in §83.2 —
> `BBoxService.handleBoxFrame`'s full body past its `frame.put(...)` header stamping was not read in full
> this session."*); **B31-G5** (niagara5-block31.md §31.10's own text: *"the two
> `box:HistoryChannel`/`box:AlarmChannel` parent-class swaps (`BBoxChannel`→`BWrapperBoxChannel`, §31.3)
> were found as a side effect of the inheritance-walk pass but not investigated further — WHY the
> box-channel hierarchy was restructured (a wrapper/decorator pattern introduced in N5?) is unexplored"*);
> **B84-G3** (niagara5-block84.md §84.4/§84.x's own text: *"the `alarm.adb` RECORD/ROW body format
> (governed by `AlarmStoreHeader.recordVersion`, a value this class stores but never interprets) was not
> compared between N4-4.15.3.28 and N5 this session — only the fixed header was. A real
> per-alarm-record byte-layout diff needs the row-writing class(es) downstream of `AlarmStoreHeader`
> (not yet identified in either corpus this session)."*); **B78-G3** (niagara5-block78.md §78.x's own
> text: *"niagaraSync `getLicenseFeature()` consumer: unlicensed → fault/down/disabled severity
> branch."*); **B37-G4** (niagara5-block37.md §37.x's own text: *"trace
> `BAbstractService.checkLicense()`'s exact `configFatal`/`configFail` call site triggered by a failed
> `feature.check()`, to confirm precisely how an unlicensed `tridium:niagaraSync` feature surfaces to an
> operator (fatal fault blocking all service function vs. a soft config fault) — read the method's
> existence and the `getLicenseFeature()` override this session, not its fault-severity wiring in
> full."*). All six gap texts were re-read from their parent block files this session; the task's own
> paraphrases matched each parent block's substance — no gap-ID drift found.
>
> Does **not** cover: a full corpus-wide re-audit of every OTHER alarm-acknowledgment call site beyond
> `BAlarmBoxChannel`/`BAlarmAcknowledger` (email/SMS/cloud-link acknowledgers were named but not
> re-opened — they were already known, non-primary paths per [Block 83]); a full byte-level compare of
> every OTHER box-protocol JSON message shape beyond the envelope/dispatch skeleton (§92.2's own scope);
> a byte diff of `AlarmStoreHeader` itself (already `[CERT]`-closed identical by [Block 84] §84.4 — not
> re-derived); a live station capture of an actual unlicensed-`niagaraSync` startup (static trace only).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (same corpus every prior block in this series cites). N4 baselines: the 4.14 corpus at
> `/home/cristian/niagara-research/organized` (§92.3's `box-rt` module.xml/`BHistoryChannel.java` compare)
> and the freshly-relocated N4 **4.15.3.28** OEM install at `/mnt/c/PowerB/PowerB-4.15.3.28` (§92.4's
> `alarm-rt.jar` extraction — the same install [Block 84] used; this session independently re-extracted
> `javax/baja/alarm/BAlarmRecord*.class` and re-hashed `modules/alarm-rt.jar`, confirming sha256
> `c2df15ae75c5a3557ce721ef0554b5794650b227d9e8fb3112793f03760f6bd7` matches [Block 84]'s own recorded
> value byte-for-byte — the SAME jar, re-read, not a different build). Decompiler: Vineflower 1.12.0
> (`tools/decompilers/vineflower-1.12.0.jar`), run against a targeted extraction of exactly
> `javax/baja/alarm/BAlarmRecord{,$1,$2}.class` + `com/tridium/alarm/db/file/AlarmStoreHeader.class` from
> the N4 jar, output to session scratchpad only
> (`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b92/`),
> never written to either repo, per task instructions. Markers (canonical list, METHODOLOGY §3): `[CERT]`
> local primary source (`file:line`) or a literal command/tool-output this session · `[CERT]` on an N4
> jar-entry is cited as `<jar>.jar!<class-path>` (this session's own extraction, jar sha256 given above)
> · `[INFER]` deduction.
>
> **Type:** `evidence` — every section closes a named parent-block gap with a fresh, this-session
> file-read or diff; no cross-block synthesis argument is constructed beyond restating what each closed
> gap settles.

---

## 92.1 — B83-G2 CLOSED: the manual, non-`ComponentSlotMap` alarm-attribution pattern is NOT specific to `analytics`'s websocket API — it is the SAME mechanism the primary `alarm` module's own box-channel-driven ack path uses, and the underlying `@NiagaraAction`-generated invoke API structurally cannot carry a real `Context` at all `[CERT]`

The primary `alarm` module's own UI-driven acknowledgment path is `com.tridium.alarm.box.BAlarmBoxChannel`
(`extends BObject implements IBoxChannel`, dispatched by `BBoxService.handleMessage()`'s
`channel.service(keyName, boxMessage.get("b"), messageOut, op)` — the exact dispatch mechanism §92.2
below reads in full) `[CERT]` `organized/alarm/vineflower/com/tridium/alarm/box/BAlarmBoxChannel.java:72`.
Its `service()` switch routes box-protocol key `"ackAlarms"` to `ackAlarms(JSONObject, BoxWriter, Context
op)` (`:102,131-132,490-492`) `[CERT]`, which calls the shared `process(BAlarmBoxChannel::ack,
clientParams, out, cx)` helper (`:490-492`).

**`process()` (`:736-834`) is a REAL, per-record authorization gate — stronger than `analytics`'s
`UpdateAlarms`, not weaker.** It first rejects an unauthenticated `Context` outright
(`if (user == null) throw new Exception(...)`, `:742-743`) `[CERT]`, then, for EVERY individual alarm
record targeted by the request (by `ids` or by `srcs`), looks up that specific record's OWN
`BAlarmClass` and calls `user.check(alarmClass, BPermissions.adminWrite)` (for a `forceCleared` request)
or `user.check(alarmClass, BPermissions.operatorWrite)` (ordinary ack), catching any `PermissionException`
per-record into a `permissionFailureClasses` set returned to the caller rather than failing the whole
batch (`:769-777,805-816`) `[CERT]`. This is a genuine, live, per-alarm-class permission check against the
real authenticated `BUser` — structurally MORE granular than [Block 83] §83.5's `UpdateAlarms`, which
checked a single fixed `(svc, prop)` pair once for the whole request.

**The attribution mechanism itself is byte-for-byte the same manual pattern [Block 83] §83.5 found in
`analytics`.** After the permission check passes, `process()` calls the operation callback
`BAlarmBoxChannel::ack` (`:494-516`) `[CERT]`:

```java
private static void ack(Map<String, Object> params, AlarmSpaceConnection conn) {
   BAlarmService alarmService = getAlarmService();
   BAlarmRecord alarm = (BAlarmRecord)params.get("record");
   Context cx = (Context)params.get("cx");
   String username = cx.getUser().getUsername();
   if (!alarm.isAcknowledged()) {
      ...
      alarm.setUser(username);
      alarm.setAckTime(BAbsTime.now());
      alarm.setAckState(BAckState.ackPending);
      alarm.setLastUpdate(BAbsTime.now());
      conn.update(alarm);
      alarmService.ackAlarm(alarm);
   }
}
```

`cx.getUser().getUsername()` resolves the REAL authenticated user (the same `WebOp`/`BoxOp`-as-`Context`
chain [Block 68] §68.2/§68.6 and [Block 83] §83.1 already traced through the box filter chain), and that
username is written directly via `alarm.setUser(username)` — `BAlarmRecord.setUser(String)`
(`organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java:288-291`) `[CERT]`, which is
`this.setString(user, v, null)`, a plain `BStruct` property setter with a **hardcoded `null` Context**,
because `BAlarmRecord extends BStruct` — it is never a mounted `BComponent`/`ComponentSlotMap` node at
all, the same structural reason [Block 83] §83.5 already gave for `analytics`'s `BAlarmRecord` writes.
`alarmService.ackAlarm(alarm)` is the `@NiagaraAction`-generated one-argument convenience method
(`organized/alarm/vineflower/niagara/alarm/BAlarmService.java:232-235`) `[CERT]`:

```java
@Generated
public void ackAlarm(BAlarmRecord parameter) {
   this.invoke(ackAlarm, parameter, null);
}
```

**This `null` is not a caller oversight — it is the ONLY signature the codegen exposes.** No overload of
this generated method accepts a `Context` at all (confirmed by reading the full generated-method block,
`:220-243`, and the action's own downstream handler, `doAckAlarm(BAlarmRecord alarm)`
(`organized/alarm/vineflower/niagara/alarm/BAlarmService.java:565-579`) `[CERT]`, which routes the alarm
to its source/recipient using only fields already baked into the record — it never reads a `Context`
parameter, because the generated `invoke()` call never gives it one). **Structural consequence,
generalizing beyond both `analytics` and `alarm`:** for ANY alarm-acknowledgment call path in this
corpus, the ONLY way a real user identity reaches the persisted alarm record is the manual
`BAlarmRecord.setUser(String)` call made by the caller BEFORE invoking the action — the station-level
`BComponent.invoke(Action, BValue, Context)` audit path ([Block 68] §68.2's `ComponentSlotMap`-level
attribution mechanism) is architecturally unreachable for alarm acknowledgment, because the
`@NiagaraAction`-generated convenience method that every caller actually calls hardcodes `null`.

`com.tridium.alarm.ack.BAlarmAcknowledger.ackAlarm(BUuid, String userName)` — the base class for the
email/SMS/cloud-link message-driven acknowledgers [Block 83] §83.5 did not open — confirms the identical
shape at a THIRD call site `[CERT]`
`organized/alarm/vineflower/com/tridium/alarm/ack/BAlarmAcknowledger.java:310-322`:
`rec.ackAlarm(userName)` (→ `BAlarmRecord.ackAlarm(String)`,
`organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java:370-381`, which itself just calls
`this.setUser(user)` at `:378`) followed by `alarmService.ackAlarm(rec)` — the same generated,
`null`-Context invoke.

**B83-G2 verdict: CLOSED.** The manual, non-`ComponentSlotMap` alarm-attribution pattern [Block 83] §83.5
found in `analytics`'s `BNaServlet`/`UpdateAlarms` is the GENERAL mechanism for all N5 alarm
acknowledgement, confirmed at three independent call sites (`analytics`'s `UpdateAlarms`, `alarm`'s own
`BAlarmBoxChannel.ack()`, and `BAlarmAcknowledger`'s message-driven ack) — not specific to the
`analytics` websocket API. It generalizes for a structural reason stronger than convention: the
`@NiagaraAction`-generated `ackAlarm(BAlarmRecord)` invoke method hardcodes a `null` `Context` at
codegen level, so no caller — however it resolves its own real user — could thread that identity through
the action-invoke audit path even if it tried; manual `BAlarmRecord.setUser()` before the invoke is the
ONLY attribution channel this framework provides for alarm records. The primary `alarm` module's own
permission GATE (per-alarm-class `user.check(..., operatorWrite/adminWrite)`) is, however, materially
STRONGER than `analytics`'s single fixed-property `checkWrite` — a real refinement over [Block 83] §83.5's
framing, not a weaker copy.

## 92.2 — B83-G3 CLOSED: the plain-JSON box frame carries an `m` array of per-message envelopes, each keyed by `t` (message type, "rt"=request), `c` (channel name), `k` (key/method name), `r` (request number), and `b` (body) — dispatched to the named `BBoxChannel`'s own `service(key, body, ...)` method, with a bootstrap-only exception for session creation `[CERT]`

`BBoxService.handleBoxFrame(JSONObject frame, Writer writer, BoxOp op)`
(`organized/box/vineflower/com/tridium/box/BBoxService.java:348-395`) validates the frame
(`p`="box", optional `c`=client-env typespec, optional `v`=version — [Block 83] §83.2's envelope), builds
the outgoing frame skeleton (`v`/`p`/optional `n`), then delegates the actual per-message work to
`handleMessages(frame, out, op)` (`:376`) `[CERT]`.

**`handleMessages` (`:440-467`)** reads `frame.getJSONArray("m")` — confirming the `m` key already named
in [Block 83] §83.2's response-encoding read is equally the REQUEST's own message-array key, not just the
response's `[CERT]`. It first validates the frame carries (or does not need) a live `BServerSession`
(`validateFrameServerSession`, `:481-493`) — a bootstrap exception is carved out explicitly:
`requiresServerSession()` (`:497-503`) returns `false` ONLY for a message whose channel is `"ssession"`
and key is `"make"` (session creation itself), so a client can create its first server session before one
exists, but every other message type requires one. Each message object `m` is then routed to its
resolved `BServerSession` (via `getServerSession(m.optJSONObject("b"), op)`, `:461`) and processed inside
that session's own event-broker lock (`session.synchronizedOnEventBroker(...)`, `:469`) — a
messages-belonging-to-different-sessions-get-batched-per-session detail not previously read.

**`handleMessage(JSONObject boxMessage, BoxWriter out, BoxOp op)` (`:503-533`) is the actual
per-message dispatch, and its field layout is now fully named `[CERT]`:**

```java
private void handleMessage(JSONObject boxMessage, BoxWriter out, BoxOp op) {
   String messageType = getMessageType(boxMessage);   // "t"
   String channelName = getChannelName(boxMessage);   // "c" (SlotPath-escaped)
   String keyName = getKeyName(boxMessage);            // "k" (interned)
   long requestNumber = getRequestNumber(boxMessage);  // "r"
   if ("rt".equals(messageType)) {
      ...
      BBoxChannel channel = (BBoxChannel)this.get(channelName);
      boolean handled = channel.service(keyName, boxMessage.get("b"), messageOut, op);
      ...
   }
}
```

confirmed field-by-field against the private static accessors (`getMessageType`→`"t"` `:746-748`,
`getChannelName`→`"c"`, `SlotPath.escape`-wrapped, `:734-736`, `getKeyName`→`"k"`, `.intern()`-ed,
`:738-740`, `getRequestNumber`→`"r"` `:754-756`, `getMessages`→`"m"` `:742-744`) `[CERT]`. **`"t"`'s only
handled value is the literal string `"rt"`** ("request") — any other/missing `messageType` value is
silently ignored (the `if` simply does not fire, no `out.value()` is written for that message at all,
`:512-533` — no `else` branch exists) `[CERT]`, meaning the box JSON protocol's message-type enum is a
single-value gate in this build, not a multi-way dispatch switch as the gap's own framing speculated.

**Per-request fault gating happens BEFORE the channel is even looked up**: `isFatalFault()` and
`isNonOperational()` (both inherited `BAbstractService` checks, §92.5 below) are checked first, throwing
a typed `BoxServiceFatalFaultException`/`BoxServiceNonOperationalException` if the whole `BBoxService` is
down — a station-wide box outage fails every message uniformly, before any per-channel `service()` call
`[CERT]` `:510-514`. The named channel is then resolved by string key off the `BBoxService` component
tree itself (`this.get(channelName)`, `:518` — `BBoxService` is the parent `BComponent` every `BBoxChannel`
mounts under, per [Block 78] §78.1's channel-type census and [Block 92] §92.3's `isParentLegal` citation
below), cast to `BBoxChannel`, and its own `service(keyName, boxMessage.get("b"), messageOut, op)` is
called with the message's `"b"` field as the opaque per-channel body — this is exactly the entry point
§92.1's `BAlarmBoxChannel.service("ackAlarms", body, ...)` dispatch above rides. Any exception thrown
anywhere in that call (including a channel-not-found `Exception`, an "Unsupported Key" `Exception`, or a
channel-internal failure) is caught uniformly and converted to a `t="e"`-tagged error message via
`handleMessageError()` (`:541-573`), never propagated as a raw Java exception to the frame response.

**B83-G3 verdict: CLOSED.** The plain-JSON box frame's message-dispatch structure beyond `p`/`v`/`id` is:
an `m` JSON array, each element carrying `t` (message type — only `"rt"`="request" is handled),
`c` (channel name), `k` (key/method name, the per-channel operation to invoke), `r` (request/correlation
number), and `b` (opaque per-channel body, forwarded verbatim to `BBoxChannel.service(key, body, ...)`).
One bootstrap exception (`c="ssession"`, `k="make"`) is exempted from the live-server-session requirement
every other message needs. Fault/non-operational service state is checked once per message before
channel resolution; any channel-level exception is uniformly converted into a `t="e"` error envelope
rather than propagated.

## 92.3 — B31-G5 CLOSED: `BWrapperBoxChannel` is a genuine lazy-resolving decorator introduced specifically to let `box` declare `AlarmChannel`/`HistoryChannel` types WITHOUT a hard module dependency on `alarm`/`history` — N4's `box-rt` had that hard dependency (15 total, including `alarm-rt`/`history-rt`/`chart-rt`/`control-rt`) and implemented both channels' logic directly inline; N5's `box` drops to 7 dependencies (neither `alarm` nor `history` among them) and resolves the real implementation by string typespec at runtime, degrading gracefully instead of failing to load `[CERT]`

`BWrapperBoxChannel` (`extends BBoxChannel`, `organized/box/vineflower/com/tridium/box/BWrapperBoxChannel.java:22`)
`[CERT]` is a genuine, general-purpose decorator/proxy, not a one-off `HistoryChannel`/`AlarmChannel`
special case:

```java
protected BWrapperBoxChannel(String typeSpec) {
   this.resolveBoxChannel(typeSpec).ifPresentOrElse(channel -> {
      this.channel = channel;
      this.setStatus(BStatus.ok);
   }, () -> {
      this.setStatus(BStatus.fault);
      this.setFaultCause(LEX.getText("channel.couldNotInitializeBoxChannel", new Object[]{typeSpec}));
   });
}

private Optional<IBoxChannel> resolveBoxChannel(String typeSpec) {
   try {
      BObject o = Sys.getRegistry().getType(typeSpec).getInstance();
      return Optional.ofNullable(o instanceof IBoxChannel ? (IBoxChannel)o : null);
   } catch (Exception e) {
      return Optional.empty();
   }
}

@Override
public boolean service(String key, Object body, BoxWriter out, BoxOp op) throws Exception {
   return !this.getStatus().isOk() ? false : this.getChannel().service(key, body, out, op);
}
```

`[CERT]` `organized/box/vineflower/com/tridium/box/BWrapperBoxChannel.java:57-79`. The constructor takes a
STRING typespec, resolves it against `Sys.getRegistry()` at construction time (a live type-registry
lookup, not a compile-time class reference), and — critically — **never throws** if resolution fails: it
sets `BStatus.fault` with a localized `faultCause` instead, and `service()` simply returns `false`
(unhandled key) rather than NPE-ing on a null inner channel, while the box-level fault status itself IS
observable (a station admin sees the channel component fault, per §92.2's `isFatalFault`/`isNonOperational`
station-wide gate being a SEPARATE, coarser mechanism from this per-channel graceful-degradation one).

**`BHistoryChannel`/`BAlarmChannel` are now trivial call sites of this decorator, pointing at real
implementation types that live IN the `history`/`alarm` modules themselves** `[CERT]`
`organized/box/vineflower/com/tridium/box/BHistoryChannel.java:20` (`super("history:HistoryBoxChannel")`),
`organized/box/vineflower/com/tridium/box/BAlarmChannel.java:18` (`super("alarm:AlarmBoxChannel")`) —
confirmed to resolve to real, non-`box`-module classes: `organized/history/vineflower/META-INF/module.xml:474`
`<type class="com.tridium.history.box.BHistoryBoxChannel" name="HistoryBoxChannel"/>` and
`organized/alarm/vineflower/META-INF/module.xml:340`
`<type class="com.tridium.alarm.box.BAlarmBoxChannel" name="AlarmBoxChannel"/>` `[CERT]` — the latter is
exactly §92.1/§92.2's own `BAlarmBoxChannel` class, now confirmed to be reached from the station's `box`
channel tree via this lazy-wrapper indirection rather than a direct `implements`/inheritance relationship.

**Why: N5's `box` module.xml drops `alarm`/`history` (and `chart`/`control`/`bql`/`gx`) from its
dependency list entirely — a real, measured dependency-count reduction, not merely a refactor for its own
sake.** N5 `box`'s `<dependencies>` block lists exactly **7** modules — `baja`, `entityIo`, `file`, `fox`,
`js`, `net`, `web` `[CERT]` `organized/box/vineflower/META-INF/module.xml:3-10`. N4's `box-rt` lists **15**
`[CERT]` `/home/cristian/niagara-research/organized/box/box-rt/vineflower/META-INF/module.xml:2-16`:
`alarm-rt`, `baja`, `bql-rt`, `chart-rt`, `control-rt`, `entityIo-rt`, `file-rt`, `fox-rt`, `gx-rt`,
`history-rt`, `jetty-rt`, `net-rt`, `platform-rt`, `query-rt`, `web-rt`. N4's own
`BHistoryChannel extends BBoxChannel` (not `BWrapperBoxChannel` — that type does not exist in the N4
corpus at all) implements the history-clear operations DIRECTLY, calling
`javax.baja.history.BHistoryService`/`BHistoryDatabase`/`HistoryDatabaseConnection` straight from box's
own code `[CERT]` `/home/cristian/niagara-research/organized/box/box-rt/vineflower/com/tridium/box/BHistoryChannel.java:1-17,29-46`
— exactly the hard-coupling `alarm-rt`/`history-rt` dependency entries exist to satisfy. N5 removed that
coupling: `box` no longer imports a single `history`/`alarm`-package class anywhere in
`BHistoryChannel.java`/`BAlarmChannel.java` (both files' full imports are `niagara.nre.annotations.*` +
`niagara.sys.{Sys,Type}` only, confirmed by the whole-file reads quoted above), and the real logic moved
INTO `history`/`alarm`'s own `com.tridium.history.box.BHistoryBoxChannel`/`com.tridium.alarm.box.BAlarmBoxChannel`
classes, reached only through `BWrapperBoxChannel`'s runtime type-registry lookup.

**B31-G5 verdict: CLOSED.** The `BBoxChannel`→`BWrapperBoxChannel` parent-class swap for
`box:HistoryChannel`/`box:AlarmChannel` is a genuine, deliberate N4→N5 dependency-inversion refactor: N5's
core `box` transport module (WebSocket/Fox session-channel machinery, [Block 78] §78.1) no longer has a
compile-time or module-loader dependency on the FEATURE modules (`alarm`, `history`, and — by the same
15→7 count — `chart`, `control`, `bql`, `gx`) whose data it exposes a channel for; those feature modules
now each own their OWN box-channel implementation class, and `box` reaches them only through a
lazy-resolving, gracefully-degrading `Sys.getRegistry()` lookup wrapper — allowing (in principle) a
station with `box` but without `alarm`/`history` installed to still load its channel tree with a faulted
(not crashed) `AlarmChannel`/`HistoryChannel` component, rather than failing to load `box` at all.

## 92.4 — B84-G3 CLOSED: `BAlarmRecord`'s ENTIRE class — including its `write(DataOutput,Context)`/`read(DataInput,Context)` row-body serialization and its `getSerialVersionId()`=0 recordVersion source — is byte-for-byte identical (post package-rename normalization) between N4-4.15.3.28 and N5-5.0.0.28; there is zero row-format drift across this upgrade boundary `[CERT]`

The alarm-record row-body writer is `niagara.alarm.BAlarmRecord.write(DataOutput out, Context context)`
(N5: `organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java:477-495`) `[CERT]`, the exact class
`AlarmStore`'s own on-disk record I/O uses (`AlarmStore` constructs its header from
`new BAlarmRecord(BUuid.DEFAULT).getSerialVersionId()`,
`organized/alarm/vineflower/com/tridium/alarm/db/file/AlarmStore.java:88,97,100-102`, and re-validates
that same value against the persisted `header.getRecordVersion()` on open, throwing `"Incompatible record
versions"` on a mismatch — confirming `BAlarmRecord.getSerialVersionId()` IS the
`AlarmStoreHeader.recordVersion` value the gap's own text names) `[CERT]`. The 14-field row layout, in
wire order: `timestamp` (`encodeAbsTime` — `encode48` under the data-recovery `Context`, else `encode64`),
`uuid` (`BUuid.encode`), `sourceState`, `ackState` (both `BSourceState`/`BAckState.encode`), `ackRequired`
(raw `boolean`), `source` (`BOrdList.encode`), `alarmClass` (`writeUTF`), `priority` (raw `int`),
`normalTime`, `ackTime` (both `encodeAbsTime`), `user` (`writeUTF`), `alarmData` (`BFacets.encode`),
`alarmTransition` (`BSourceState.encode`), `lastUpdate` (`encodeAbsTime`) — read/write mirror each other
field-for-field (`:481-494` write, `:508-521` read) `[CERT]`.

**N4-4.15.3.28 extraction and diff, this session.** `javax/baja/alarm/BAlarmRecord{,$1,$2}.class` was
extracted from the same N4-4.15.3.28 `modules/alarm-rt.jar` [Block 84] already hashed (sha256
`c2df15ae75c5a3557ce721ef0554b5794650b227d9e8fb3112793f03760f6bd7`, re-confirmed identical this session)
`[CERT]` and Vineflower-decompiled to session scratchpad. A line-range diff of the write/read/
getSerialVersionId/encodeAbsTime/decodeAbsTime method block (source lines 469-545 in both files) against
N5's identical-numbered block returns **zero differences, exit 0** `[CERT]` (`diff`, this session,
`/tmp/.../scratchpad/b92/`). A SECOND, stronger check — normalizing N4's `javax.baja.*` import prefixes
to N5's `niagara.*` (the same technique [Block 14]/[Block 31]/[Block 84] already established) and diffing
the **entire 602-line file**, not just the row-serialization block — ALSO returns **zero differences**,
and both files independently report **602 lines** each `[CERT]` (`sed`+`diff`, this session,
`n4_norm.java` vs. `organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java`). `getSerialVersionId()`
returns the hardcoded literal `0` in BOTH trees `[CERT]` (line 469-471 of both files, part of the
zero-diff block).

**B84-G3 verdict: CLOSED — no drift at all, not merely no orphan-data risk.** The `alarm.adb`
RECORD/ROW body format is byte-for-byte identical between N4-4.15.3.28 and N5-5.0.0.28: same 14-field
layout, same field order, same encode/decode calls, same hardcoded `recordVersion`=0 source. Combined
with [Block 84] §84.4's already-`[CERT]`-closed identical HEADER finding, this makes the ENTIRE `alarm.adb`
file format — header AND row body — confirmed byte-compatible across this specific N4→N5 upgrade path;
an `alarm.adb` produced by this N4-4.15.3.28 build would not merely pass N5's header magic/version guard
([Block 84] §84.4) but would have every one of its row bytes decode identically, since the decoding class
itself is the unmodified same source. This is a stronger, more definitive answer than the gap's own
framing anticipated (it asked for "a real per-alarm-record byte-layout diff," implicitly expecting to
find SOME delta worth cataloguing) — none exists for this record type at this specific N4/N5 version pair.

## 92.5 — B78-G3 / B37-G4 CLOSED together: an unlicensed `getLicenseFeature()` always produces a permanent, unrecoverable `fatalFault` (mapped to `BStatus.fault`, never `.disabled` or a soft `configFail`) via the SAME generic `BAbstractService.checkLicense()` machinery every licensed service uses; niagaraSync adds no override and maps the fault straight into its own domain-specific `BNiagaraSyncStateEnum.fault` state `[CERT]`

Both gaps ask the identical underlying question from two different parent blocks ([Block 78] §78.4's
framing: fault/down/disabled?; [Block 37] §37.7's framing: fatal vs. soft config fault?) — the task's own
overlap note is confirmed correct by reading the code: there is exactly ONE license-fault-severity
mechanism in this corpus, `BAbstractService.checkLicense()`, and `BNiagaraSyncService` neither overrides
nor bypasses it.

**The generic mechanism** (`organized/baja/vineflower/niagara/sys/BAbstractService.java`), read in full
this session:

```java
private void checkLicense() {                                    // :164
   try {
      Feature feature = this.getLicenseFeature();
      if (feature == null) { return; }                            // :167-169, no override = no gate
      feature.check();                                            // :171, throws if unlicensed
      ...                                                         // (limit-map bookkeeping, licensed path)
   } catch (Exception e) {
      this.fatalFault = true;                                     // :198 — HARD fault, not configFault
      Logger.getLogger("service").log(Level.SEVERE, "Unlicensed: " + this.toPathString(), e);
      this.setFaultCause("Unlicensed: " + e);
   }
}
```

`[CERT]` `:164-199`. Called from `fwServiceStarted()` (`:265-268`, the framework hook fired at service
start, `case 15` of `fw()`, `:255`), immediately followed by `this.updateStatus()` in the same method —
so the `fatalFault` bit is applied to the component's real `BStatus` on the very same call. `updateStatus()`
(`:99-124`) treats `fatalFault` and the softer `configFault` identically at the bit level
(`if (!this.fatalFault && !this.configFault) { clear fault bit } else { set fault bit }`, `:110-114`) —
**there is no separate `BStatus.disabled` outcome for a license failure**: `disabled` is driven purely by
the unrelated `enabled` property bit (`:104-108`), never by `fatalFault`. `[CERT]` `isFatalFault()`
(`:129-131`) feeds `isOperational()` (`:91-94`, `!fatalFault && !disabled && !fault`) — once tripped, the
WHOLE service is non-operational.

**The fault is permanent for the life of the running service — `fatalFault` is never reset to `false`
anywhere in this class.** A corpus-wide grep of every `fatalFault` occurrence in the file (`:33` field
decl, `:110` read, `:130` read, `:139,147` guard reads in `configFail`/`configOk`, `:154` set-true in
`configFatal`, `:198` set-true in `checkLicense`'s catch, `:284` a read-only re-assertion guard in
`fwChanged` that RE-RUNS `updateStatus()` if an external write tries to clear the visible `status`
property while `fatalFault` is still `true` internally — forcing the fault status back, not clearing it)
confirms **zero assignments of `fatalFault = false`** anywhere in `BAbstractService` `[CERT]`. The only way
out is a fresh service start (a new `fwServiceStarted()`/`checkLicense()` cycle — e.g. a station restart
or an enable-cycle), not any in-process recovery path.

**`configFail`/`configFatal` (the two methods B37-G4 named by their own signatures) are DIFFERENT,
lighter mechanisms `checkLicense()` does NOT call at all**: `configFail(String)` (`:145-151`) sets the
softer `configFault` flag and ONLY updates status/cause `if (!this.fatalFault)` (a fatal fault always
wins over a later config-fail call); `configFatal(String)` (`:153-157`) is a PUBLIC method any subclass
can call directly to force the same `fatalFault=true` path `checkLicense()`'s catch block reaches
internally — `checkLicense()` sets the field directly rather than calling the public `configFatal()`
method, but produces the identical `fatalFault=true`+`setFaultCause`+(deferred)`updateStatus()` effect.
This resolves B37-G4's own framing directly: an unlicensed feature is a **fatal fault**, not a soft
`configFail` — the gap asked which of the two `BAbstractService` calls the license path uses, and the
answer is neither method call directly, but the field-level equivalent of `configFatal`, never
`configFail`.

**`BNiagaraSyncService` overrides ONLY `getLicenseFeature()`, nothing else** — confirmed by a full-file
grep for `checkLicense`/`fatalFault`/`case 15`/`Object fw(` inside
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java`: zero hits `[CERT]`.
Its override (`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:286-288`,
already `[CERT]`'d by [Block 78] §78.4/[Block 37] §37.7) returns
`Sys.getLicenseManager().getFeature("tridium", "niagaraSync")` — the generic machinery above applies
completely unmodified. niagaraSync's OWN `initialize()` method (its post-`fwServiceStarted()` domain
lifecycle hook) reads the inherited `isFatalFault()` FIRST, before anything else `[CERT]`
`organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:372-378`:

```java
private void initialize() {
   if (this.isFatalFault()) {
      this.setState(BNiagaraSyncStateEnum.fault);
   } else {
      this.configOk();
      this.setState(BNiagaraSyncStateEnum.initializing);
      if (!this.getEnabled()) {
         this.setState(BNiagaraSyncStateEnum.disabled);
         ...
```

— confirming an unlicensed `tridium:niagaraSync` forces `BNiagaraSyncStateEnum.fault` UNCONDITIONALLY,
never reaching the `configOk()`/`initializing`/`disabled` branch at all; `BNiagaraSyncStateEnum.disabled`
is reachable ONLY when licensed but `getEnabled()==false` — a completely separate condition from
licensing. This also confirms [Block 78] §78.4's `down()` helper (`setStatus(BStatus.down)`, reserved for
OPERATIONAL causes like `peerStationNotFound`/`maintenanceMode`, [Block 78] §78.4/[Block 37] §37.3) is
architecturally unreachable for a licensing failure — `down` and `fault` are two disjoint severities in
this service's own state machine, and licensing only ever produces the latter.

**B78-G3 / B37-G4 verdict: CLOSED (both, together, confirming the task's own overlap prediction).** An
unlicensed `tridium:niagaraSync` feature surfaces as a **fatal fault** — `BAbstractService.fatalFault=true`
(the field-level equivalent of `configFatal`, never `configFail`), a SEVERE log line, a `faultCause` of
`"Unlicensed: " + <exception>`, `BStatus.fault` (never `.disabled`, `.down` is a disjoint severity reserved
for operational causes), permanent until the service's next start cycle — and niagaraSync's own domain
state machine maps this straight into `BNiagaraSyncStateEnum.fault`, bypassing its `initializing`/`disabled`
branches entirely. This is the generic `BAbstractService` licensing gate every OTHER licensed N5 service
([Block 11]'s `BPlatformService`/`BIPlatformCommand`/`BPort` census, [Block 18]'s `cloudLink`) shares —
niagaraSync adds no niagaraSync-specific severity logic on top of it.

## 92.x — Connections

- **[Block 83]** — closes **B83-G2** (§92.1), confirming and STRENGTHENING §83.5's own generalization
  question: the pattern is corpus-wide (3 independent call sites now confirmed) and structurally forced
  by the `@NiagaraAction` codegen, not a convention two unrelated teams happened to both follow. Also
  closes **B83-G3** (§92.2), the last gap [Block 83] §83.2 itself opened.
- **[Block 31]** — closes **B31-G5** (§92.3), the last open item in [Block 31] §31.3's inheritance-walk
  side-finding; reuses [Block 14]/[Block 31]/[Block 84]'s own package-normalization diff technique.
- **[Block 84]** — closes **B84-G3** (§92.4), completing [Block 84] §84.4's `AlarmStoreHeader`-only compare
  into a full header+row `alarm.adb` format-compatibility verdict for the N4-4.15.3.28↔N5-5.0.0.28 pair;
  reuses and re-confirms [Block 84]'s own N4 jar sha256 rather than re-deriving it independently.
- **[Block 78]/[Block 37]** — jointly closes **B78-G3**/**B37-G4** (§92.5), the two residual gaps both
  blocks opened from the same underlying `BNiagaraSyncService.getLicenseFeature()` finding; corroborates
  [Block 11] §11.9's own `BAbstractService`-adjacent generic-dispatch findings (`BPlatformService`/
  `BIPlatformCommand`) by tracing the SAME base class's licensing path from a different consumer
  (`niagaraSync`) — a second, independent confirmation that N5's service-licensing architecture is one
  shared mechanism, not per-module reinvention.
- **[Block 68]** — §92.1's `WebOp`/`BoxOp`-as-`Context` chain and §92.2's channel-dispatch entry point
  both ride the identical authenticated-`Context` machinery [Block 68] §68.2/§68.6 traced for
  `NiagaraRpcServlet`/`BacnetAwsServlet`/`BObixServer`.

## 92.x — Child gaps opened

- **B92-G1** — `AlarmStore`'s own construction/validation call sites for `AlarmStoreHeader`
  (`AlarmStore.java:88,97,100-102`, §92.4) were read only for the `recordVersion` cross-check; the rest of
  `AlarmStore`'s own page/block-allocation logic (how rows are packed into 512-byte pages,
  `DEFAULT_PAGE_SIZE`/`DEFAULT_PAGES_PER_BLOCK` from [Block 78] §78.3/[Block 84] §84.4) was not read this
  session — whether N4-4.15.3.28's `AlarmStore.java` (page-packing logic, not just the record codec) is
  ALSO byte-identical is unconfirmed; `investigable`, low-priority given §92.4's already-definitive
  record-codec-level identity (a page-packing difference could not orphan data without also changing the
  record codec, which is now confirmed unchanged).
- **B92-G2** — `BWrapperBoxChannel`'s graceful-degradation fault path (§92.3, `BStatus.fault` +
  `channel.couldNotInitializeBoxChannel` lexicon message) was read only for `HistoryChannel`/`AlarmChannel`;
  whether any OTHER `box` module type besides these two now uses the same wrapper (a corpus-wide census of
  `BWrapperBoxChannel` subclasses/instantiations was not run this session) is open. `investigable`,
  mechanical (one `grep -rl 'extends BWrapperBoxChannel'` across `organized/`).
- **B92-G3** — §92.5 confirms unlicensed-niagaraSync is a permanent `fatalFault` until the NEXT service
  start cycle, but this session did not trace what actually TRIGGERS a fresh start cycle in practice (a
  full station restart is the obvious case; whether toggling the `enabled` property alone re-runs
  `fwServiceStarted()`/`checkLicense()`, or only a full component restart does, was not verified against
  `BComponent`'s own start/stop lifecycle this session). `investigable`, would need `BComponent`'s own
  `enabled`-property-change-to-restart wiring traced, not `BAbstractService`-specific.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `BAlarmBoxChannel.ackAlarms`→`process()`→`ack()` checks `user==null` then a REAL per-alarm-class `user.check(alarmClass, operatorWrite/adminWrite)` before acknowledging | [CERT] | `organized/alarm/vineflower/com/tridium/alarm/box/BAlarmBoxChannel.java:490-492,736,742-743,769-777,805-816` |
| 2 | `ack()` resolves `username` from a real `Context` and writes it via `alarm.setUser(username)` — a plain `BStruct` property set, not `BComplex.set(...,Context)` | [CERT] | `organized/alarm/vineflower/com/tridium/alarm/box/BAlarmBoxChannel.java:494-498,504` |
| 3 | `BAlarmRecord.setUser(String)` is `this.setString(user, v, null)` — hardcoded `null` Context, `BAlarmRecord extends BStruct` | [CERT] | `organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java:288-291` |
| 4 | `BAlarmService.ackAlarm(BAlarmRecord)` (the `@Generated` convenience method every caller uses) is `this.invoke(ackAlarm, parameter, null)` — no Context-accepting overload exists | [CERT] | `organized/alarm/vineflower/niagara/alarm/BAlarmService.java:232-235` |
| 5 | `doAckAlarm(BAlarmRecord)` never reads a `Context` parameter — routes purely off fields already on the record | [CERT] | `organized/alarm/vineflower/niagara/alarm/BAlarmService.java:565-579` |
| 6 | `BAlarmAcknowledger.ackAlarm(BUuid,String)`→`rec.ackAlarm(userName)`→`BAlarmRecord.ackAlarm(String)` is a THIRD call site reaching the same `setUser`+generated-invoke shape | [CERT] | `organized/alarm/vineflower/com/tridium/alarm/ack/BAlarmAcknowledger.java:310-322`; `organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java:370-381` |
| 7 | box JSON message array `m`, per-message fields `t`/`c`/`k`/`r`/`b`; only `t=="rt"` is handled, dispatched to `BBoxChannel.service(k, b, ...)` | [CERT] | `organized/box/vineflower/com/tridium/box/BBoxService.java:440-467,503-533,734-756` |
| 8 | bootstrap exception: `c=="ssession"`,`k=="make"` does not require a pre-existing `BServerSession` | [CERT] | `organized/box/vineflower/com/tridium/box/BBoxService.java:481-503` |
| 9 | fatal-fault/non-operational service state is checked once per message, before channel lookup; channel exceptions convert uniformly to a `t="e"` envelope | [CERT] | `organized/box/vineflower/com/tridium/box/BBoxService.java:510-533,541-573` |
| 10 | `BWrapperBoxChannel` resolves `IBoxChannel` by string typespec via `Sys.getRegistry()`, never throws — sets `BStatus.fault`+lexicon cause on failure instead | [CERT] | `organized/box/vineflower/com/tridium/box/BWrapperBoxChannel.java:57-79` |
| 11 | `BHistoryChannel`/`BAlarmChannel` (N5) are `BWrapperBoxChannel` subclasses pointing at `"history:HistoryBoxChannel"`/`"alarm:AlarmBoxChannel"`, real types owned by `history`/`alarm` modules | [CERT] | `organized/box/vineflower/com/tridium/box/BHistoryChannel.java:20`; `organized/box/vineflower/com/tridium/box/BAlarmChannel.java:18`; `organized/history/vineflower/META-INF/module.xml:474`; `organized/alarm/vineflower/META-INF/module.xml:340` |
| 12 | N5 `box` module.xml: exactly 7 dependencies, none of `alarm`/`history`/`chart`/`control`/`bql`/`gx` | [CERT] | `organized/box/vineflower/META-INF/module.xml:3-10` |
| 13 | N4 `box-rt` module.xml: exactly 15 dependencies, including `alarm-rt`/`history-rt`/`chart-rt`/`control-rt`/`bql-rt`/`gx-rt` | [CERT] | `/home/cristian/niagara-research/organized/box/box-rt/vineflower/META-INF/module.xml:2-16` |
| 14 | N4's own `BHistoryChannel extends BBoxChannel` (not `BWrapperBoxChannel`) calls `javax.baja.history.*` directly inline | [CERT] | `/home/cristian/niagara-research/organized/box/box-rt/vineflower/com/tridium/box/BHistoryChannel.java:1-17,29-46` |
| 15 | `BAlarmRecord.write/read` row-body field layout (14 fields, exact order) matches source read | [CERT] | `organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java:477-521` |
| 16 | N4-4.15.3.28's `alarm-rt.jar` re-extracted this session, sha256 matches [Block 84]'s own recorded value exactly | [CERT] | `sha256sum /mnt/c/PowerB/PowerB-4.15.3.28/modules/alarm-rt.jar` this session = `c2df15ae75c5a3557ce721ef0554b5794650b227d9e8fb3112793f03760f6bd7` |
| 17 | N4 vs N5 `BAlarmRecord.java` lines 469-545 (write/read/getSerialVersionId/encodeAbsTime/decodeAbsTime): `diff` exit 0, zero differences | [CERT] | `diff`, this session, `/tmp/.../scratchpad/b92/out/javax/baja/alarm/BAlarmRecord.java` vs. `organized/alarm/vineflower/niagara/alarm/BAlarmRecord.java` |
| 18 | Whole-file (602 lines both sides), package-normalized `BAlarmRecord.java`: `diff` exit 0, zero differences | [CERT] | `diff`, this session, `n4_norm.java` vs. N5 file; `wc -l` both = 602 |
| 19 | `getSerialVersionId()` returns hardcoded `0` in both N4-4.15.3.28 and N5 | [CERT] | both files, line 469-471 (part of claim 17's zero-diff block) |
| 20 | `BAbstractService.checkLicense()`: unlicensed → `fatalFault=true` + SEVERE log + `faultCause`; licensed-`null`-feature → no-op; `fatalFault` never reset to `false` anywhere in the class | [CERT] | `organized/baja/vineflower/niagara/sys/BAbstractService.java:33,99-124,129-131,139,147,154,164-199,255,265-268,284` |
| 21 | `fatalFault`/`configFault` map to the SAME `BStatus.fault` bit in `updateStatus()`; `.disabled` is driven only by `enabled`, never by licensing | [CERT] | `organized/baja/vineflower/niagara/sys/BAbstractService.java:99-124` |
| 22 | `BNiagaraSyncService` overrides only `getLicenseFeature()` — zero hits for `checkLicense`/`fatalFault`/`case 15`/`Object fw(` in its own file | [CERT] | `grep`, this session, `organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java` |
| 23 | niagaraSync's own `initialize()` checks `isFatalFault()` first, mapping straight to `BNiagaraSyncStateEnum.fault`, never reaching `initializing`/`disabled` | [CERT] | `organized/niagaraSync/vineflower/com/tridium/niagaraSync/BNiagaraSyncService.java:286-288,372-378` |

Tally: 23 [CERT], 0 [INFER]. Every citation above was read or run directly this session (not recalled):
the `BAlarmBoxChannel`/`BAlarmRecord`/`BAlarmService`/`BAlarmAcknowledger` full-body reads; the
`BBoxService` message-dispatch full read (fields, bootstrap exception, fault-gate ordering, error
conversion); the `BWrapperBoxChannel`/`BHistoryChannel`/`BAlarmChannel` whole-file reads plus the two
module.xml dependency-count reads (N4 and N5); the fresh `alarm-rt.jar` re-extraction, re-hash, and
Vineflower re-decompile plus the two `diff` runs (method-block and whole-file, both exit 0); and the
`BAbstractService`/`BNiagaraSyncService` full/targeted reads plus the corroborating `grep` for absent
overrides. Zero `[INFER]` — every verdict in this block rests on a direct read or a mechanically-run
`diff`/`grep`/`sha256sum`, not an extrapolation across an unchecked remainder.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block92.md
```

(run until exit 0; output reported in the handback to the caller, per the task's own instruction — the
tool's own tally brackets are not pasted into this block body, per the same instruction).

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; no web tool was used.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block92.md` (the only file
written in either corpus this session, per the task's single-file constraint). `INDEX.md`/
`RESEARCH-STATE.md`/`CATALOG.md` were **not** regenerated or hand-edited — left to the orchestrator's
integration step. Scratch extraction/decompile output (N4-4.15.3.28's `BAlarmRecord`/`AlarmStoreHeader`
classes, never persisted to either repo) lives at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b92/`
(`extract/`, `out/`, `n4_norm.java`).
