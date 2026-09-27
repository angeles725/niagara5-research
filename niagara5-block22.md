# Block 22 — N5 driver framework delta: driver/ndriver, BACnet, Modbus, Fox

> **Scope**: Closes gap **N5-G15** (driver framework delta N4 → N5, across `driver`, `ndriver`,
> `basicDriver`, `devDriver`/`devIpDriver`/`devSerialDriver`/`devHttpDriver`, `bacnet` (+`bacnetAws`,
> `bacnetUtil`, `bacnetEDE`, `platBacnet`), `modbusCore`/`modbusAsync`/`modbusTcp`/`modbusSlave`/
> `modbusTcpSlave`, `niagaraDriver`, `fox`, `serial`, `platSerial`). Covers: real logic deltas in the
> framework core (`BDeviceNetwork`/`BDevice`/`BPointDeviceExt`/`BProxyExt`/`BTuningPolicy`/poll
> scheduler) verified from REAL source (not decompiled bytecode) on both sides after normalizing the
> `javax.baja`→`niagara` rename; the deprecation status of `basicDriver`/`devDriver` and whether
> Tridium's own shipped drivers still depend on them; BACnet public-API simplification + BACnet/SC
> promotion; why Modbus has zero official migration-doc coverage; Fox wire-protocol byte-for-byte
> parity vs. the new version-check API; serial/platSerial package-split pattern. Does **not** re-derive
> the general `javax.baja`→`niagara` census ([B5] already counted `driver` 122→123 types) or the
> doc-level Breaking-Changes table ([B10] §10.4 already extracted BC-01/04/09/10/16/19); this block
> deepens those with source/bytecode-level file:line evidence and extends into Modbus/Fox/serial, which
> neither prior block covered. Does not cover a live N5 station compile/run of a ported driver
> (`requires-execution`, named as a child gap below), or the exact BACnet `Descriptor` interface
> diff (doc-confirmed only, no shipped source — named as a child gap below).
>
> Subject version: Niagara **5.0.0.28 (Beta)** —
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{docSource,docDeveloper}.jar` (real `.java`
> source for public-API modules) and the shipped module jars themselves (bytecode via `javap`,
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap`, JDK 26.0.2.1) for private-API/internal modules
> that ship no source. N4 side: Honeywell OptimizerSupervisor **4.14.0.162** OEM build's own
> `docSource.jar`-equivalent real source, already extracted in a prior session under
> `organized/docSource/docSource-doc/vineflower/<part>/` (verified this session to be REAL `.java`
> source with copyright headers/Javadoc, not Vineflower decompiler output — the `vineflower` folder name
> is a legacy naming artifact, not a description of its contents), plus `organized/<module>/<part>/
> vineflower/` genuine Vineflower-decompiled bytecode where no real source was available (BACnet
> descriptor exports, `modbusCore`). Our client checkout: worktree
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`, commit
> `a109249d98b795c934c71b2165af976dbc39716e` (the non-stale worktree per prior-session memory).
>
> Sources: N5 `docSource.jar` zip entries under `driver/niagara/driver/{,point/,ping/,util/}`,
> `driver/niagara/driver/ping/BIPingable.java`, `baja/niagara/{status,sys}/*.java`,
> `bacnet/niagara/bacnet/**/*.java` (336 files), extracted to `/tmp/claude-1000/n5b22/` this session
> via `python3 zipfile`. N5 bytecode: `modbusCore.jar`, `basicDriver.jar`, `devDriver.jar`,
> `devIpDriver.jar`, `ndriver.jar`, `fox.jar`, `serial.jar`, `platSerial.jar`, unzipped to
> `/tmp/claude-1000/n5b22/<module>_n5/` and read via `javap -p [-v|-constants]`. N4 real source:
> `organized/docSource/docSource-doc/vineflower/driver-rt/javax/baja/driver/{,point/,ping/,util/}*.java`.
> N4 bytecode-decompiled: `organized/modbusCore/modbusCore-rt/vineflower/com/tridium/modbusCore/**`,
> `organized/bacnet/bacnet-rt/vineflower/**`, `organized/fox/fox-rt/vineflower/javax/baja/fox/
> BFoxProxySession.java`. Doc: `doc/upgrade/upgradingToN5.html` re-read at
> `/tmp/claude-1000/n5b10/doc__upgrade__upgradingToN5.html.txt` (already extracted for [B10], reused —
> §BACnet/§basicDriver-devDriver full text). `~/.claude/skills/build-n4-module/SKILL.md` (73 lines, read
> in full — no driver-base-class prescription beyond the trigger description). Our checkout: `grep -rn`
> census across all 27 `.java` files under `Compresores/CompPan/`, `Paccadia/ColdRoomPan/`,
> `Dashboard/DashboardPan/` in the worktree above.
>
> Method: real-source-vs-real-source diff (not source-vs-decompiled, which produces decompiler-idiom
> noise — see §22.1) using a custom token-level differ (`/tmp/claude-1000/n5b22/tokendiff.py`, stdlib
> `difflib`) that strips comments/whitespace so only genuine token insertions/deletions/substitutions
> surface; `javap -p -v -constants` for bytecode-only modules (Modbus, basicDriver, devDriver family);
> `grep -rn` census of our own module tree. Markers: `[CERT]` local primary source (`file:line`, for
> both the real N4 docSource-equivalent source and the real N5 docSource.jar source — both resolve as
> `extern` to `verify-block.sh` since they live outside this corpus; see §22.x self-verify) ·
> `[CERT-doc]` the shipped N5 doc (`upgrade/upgradingToN5.html`, cited by heading) · `[INFER]` deduction.
>
> Framework/wire-protocol layer. Connects [B5] (package-rename census — `driver` 122→123 types,
> confirmed here without itemizing which); [B10] (doc-level breaking changes BC-01 Log removed, BC-04
> `isUnoperational` renamed, BC-09 basicDriver/devDriver deprecated, BC-10 BACnet API simplified, BC-16
> nDriver package move, BC-19 bacnet.asn package move, §10.8 Fox `BFoxProxySession` interop warning —
> this block adds file:line/bytecode proof under every one of those rows); [B13] (module inventory —
> confirms `ndriver`/`basicDriver`/`devDriver`/`modbusCore`/`fox`/`serial`/`platSerial` are among the 229
> modules common to both trees, not new or removed); [B134] (N4 Fox wire protocol — this block confirms
> byte-identical constants in N5); [B872]/[B927]/[B810] (N4 `BTuningPolicy`/poll-scheduler/
> `BAbstractDescriptor`/`BPingMonitor` internals — this block is their N5 diff); [B877] (N4 `ndriver` +
> DDF chassis — this block is the N5-side comparison); [B437] (N4 driver UI framework, untouched here).

---

## 22.1 — Methodological note: real source vs. real source, not source vs. decompiled `[CERT]`

Both N4 and N5 ship a `docSource.jar`-equivalent module holding real `.java` source (with copyright
headers, Javadoc, `@author`/`@version`/`@creation` tags) for the public-API driver classes — NOT
Vineflower/decompiler output, confirmed by inspection of the file headers on both sides
(`organized/docSource/docSource-doc/vineflower/driver-rt/javax/baja/driver/BDeviceNetwork.java:1-3`
"Copyright 2001 Tridium, Inc." vs. `driver/niagara/driver/BDeviceNetwork.java` inside N5's
`docSource.jar`, same header text). A naive first diff of the N5 real source against the N4
**decompiled Vineflower tree** (`organized/driver/driver-rt/vineflower/...`) produced 800+ diff lines
per file that were almost entirely decompiler-idiom noise — annotation-collapsing (`@NiagaraProperties({…})`
grouped form vs. per-property `@NiagaraProperty`), brace-placement, and Slot-o-Matic boilerplate
reconstruction differences that exist between ANY decompiled-vs-source pair regardless of Niagara
version. Re-running the same diff against the real N4 source instead cut the raw line-diff by ~35-45%
per file and, after a token-level (comment/whitespace-stripped) re-diff, isolated the small number of
GENUINE logic changes reported in §22.2-§22.6 below. **Lesson for any future N4↔N5 comparison in this
corpus: always locate the real-source pair first (`docSource.jar` on both sides) before diffing against
a decompiled tree.**

## 22.2 — `BAbstractDescriptor`: `isUnoperational()` → `isNonOperational()` + new `isOperational()` `[CERT]`

Confirms and deepens [B10] BC-04 with exact locations on both sides. N4:

```
public boolean isUnoperational()
{
  return isDisabled() || isDown();
}
```
`[CERT]` `organized/docSource/docSource-doc/vineflower/driver-rt/javax/baja/driver/util/
BAbstractDescriptor.java:489-492`. N5, same class, same body, renamed + a new companion method, both
carrying `@since Niagara 5.0`:

```
public boolean isOperational()          { return !isNonOperational(); }   // :511
public boolean isNonOperational()       { return isDisabled() || isDown(); }  // :523
```
`[CERT]` `driver/niagara/driver/util/BAbstractDescriptor.java:505-526` (docSource.jar). The rename
propagates by `@Override` into `BDeviceNetwork` and `BDevice` — both gained their own concrete
`isOperational()`/`isNonOperational()` pair in N5 (`BDeviceNetwork.java:447-476` docSource.jar,
`isOperational()` body `:454-458`, `isNonOperational()` body `:466-476`, own `grep -n` read), and the
N5 source carries an explicit maintainer comment explaining WHY `isNonOperational()` still calls
`!isOperational()` rather than inlining the check: a subclass that pre-existed Niagara 5.0 with its own
ad-hoc `isOperational()` convenience method now transparently becomes an override of the new base
method, and this indirection keeps such a subclass's `isNonOperational()` consistent with it without
any code change on the subclass's part `[CERT]` `driver/niagara/driver/BDeviceNetwork.java:469-474`
(in-code maintainer comment, first-party evidence per METHODOLOGY §3). The internal (package-private,
non-API) bitmask constant `Tuning.UNOPERATIONAL` was renamed in lock-step to `Tuning.NON_OPERATIONAL`,
same composition `FATAL | DOWN | DISABLED | STOP` — N4 `point/Tuning.java:629` (definition),
`:551` (use) vs. N5 `point/Tuning.java:676` (definition), `:587` (use), both `[CERT]`. This one is
internal/package-private and does not itself break external driver code.

**Impact for a custom driver module**: any code that calls `.isUnoperational()` on a `BAbstractDescriptor`
subclass (`BDeviceNetwork`, `BDevice`, `BDeviceExt`, `BNetworkExt`, any point extension) fails to compile
against N5's `driver.jar`; the fix is a mechanical rename to `.isNonOperational()`. Our own three shipped
modules (ColdRoomPan/CompPan/DashboardPan) call neither method — confirmed by `grep -rn "isUnoperational"`
across all 27 `.java` files in the worktree, zero hits — so this is a forward-looking item, not a current
porting requirement, mirroring how [B10] §10.8 filed the Fox interop finding.

## 22.3 — `javax.baja.log.Log` is fully removed, not merely deprecated `[CERT]`

[B10] BC-01 states the doc's claim ("AX `Log` removed... `java.util.logging.Logger`"); this section
verifies it structurally. N4 ships the whole `javax.baja.log` package, including `Log.getLog(String)`
consumed by two deprecated convenience methods:
```java
@Deprecated public Log getLog() { return Log.getLog(getLogger().getName()); }
```
`[CERT]` `BDeviceNetwork.java:831-834`, `BDevice.java:663-666` (both `organized/docSource/docSource-doc/
vineflower/driver-rt/javax/baja/driver/`). A full-namelist search of N5's `docSource.jar` for any path
containing `/log/` returns **zero** entries — no `niagara.log` package exists at all `[CERT]` (own
`python3 zipfile` census, `/tmp/claude-1000/n5b22/`, 3,239-entry namelist). Both `getLog()` overrides are
absent from the N5 source of `BDeviceNetwork.java`/`BDevice.java` (confirmed present-vs-absent by token
diff, §22.1 method) — the method was deleted, not merely marked `@Deprecated`, which is a stronger break
than BC-01's "removed" wording alone conveys (a caller cannot suppress-and-keep it the way BC-09 allows
for basicDriver/devDriver). Zero hits for `getLog()`/`javax.baja.log` in our own checkout (§22.2's same
grep sweep) — no current impact.

## 22.4 — `BPingMonitor`: for-each refactor + `printStackTrace()` → `java.util.logging` `[CERT]`

A genuine behavioral improvement, not a rename. N4's ping loop uses classic indexed iteration and
swallows exceptions to stderr:
```java
BIPingable p = pingables[i];            // :429
...
if (isAlive) e.printStackTrace();       // :441, and again :541, :563, :591
...
p.doPing();                              // :453
```
`[CERT]` `organized/docSource/docSource-doc/vineflower/driver-rt/javax/baja/driver/ping/
BPingMonitor.java`. N5 rewrites the same loop as a for-each over `pingables`, and every one of the four
`printStackTrace()` sites becomes a lazily-fetched `java.util.logging.Logger` call at `WARNING`, with the
stack trace attached only when `FINE` is loggable (avoids stack-trace cost/log-noise on a healthy
system):
```java
for (BIPingable pingable : pingables) { ... checkPing(pingable, freq, now); ... }   // :449-464
...
Logger log = getLogger();
log.log(Level.WARNING, "Exception occurred in PingMonitor run: " + throwable,
        log.isLoggable(Level.FINE) ? throwable : null);                             // :469-477
...
pingable.doPing();                                                                   // :490
```
`[CERT]` `driver/niagara/driver/ping/BPingMonitor.java` (docSource.jar). A new lazy `getLogger()` helper
(`:703-712`) backs a `private volatile Logger log` field — `volatile` because `BPingMonitor` runs its
scan on a dedicated thread (per [B810]/[B872]'s driver-poll-thread model) and the getter is called from
that thread while the field may be read/reset elsewhere; this is a genuine thread-safety hardening not
present in N4. The `icon` field was also renamed to the `ICON` constant-naming convention
(`ping/BPingMonitor.java:683` N4 vs `:798` N5, both `[CERT]`) — purely cosmetic. **Impact**: none of our
three modules subclass or call into `BPingMonitor` directly (they consume it only through the framework
default on `BDeviceNetwork`/`BDevice`), so this is transparent to us; it is listed because it is the
single largest GENUINE logic delta found in the framework core.

## 22.5 — `BTuningPolicy`: logic is byte-for-byte identical `[CERT]`

After stripping the package-name token, the `@Generated` annotations (new in N5, marking
Slot-o-Matic-produced accessors — absent from N4's own annotation-processor output), and
comment/whitespace reformatting, a token-level diff (§22.1 method) of `BTuningPolicy.java` between N4
(`organized/docSource/docSource-doc/vineflower/driver-rt/javax/baja/driver/point/BTuningPolicy.java`)
and N5 (`driver/niagara/driver/point/BTuningPolicy.java`) reports **zero** genuine token differences.
Every default is unchanged: `minWriteTime`/`maxWriteTime`/`staleTime` = 0 (off), `writeOnStart`/
`writeOnUp`/`writeOnEnabled` = `true`, and `started()` still `abs()`-normalizes the two `BRelTime`
properties (identical to N4's documented behavior in [B872] §872.2). `BTuningPolicyMap` shows the same
zero-genuine-diff result. **This is the single most consequential finding of this block for our own
work**: CompPan's/ColdRoomPan's/DashboardPan's assumptions about tuning-policy defaults (`writeOnUp`
DOWN→UP re-send behavior documented in [B810] §810.4) carry over to N5 unchanged if/when a station is
migrated — no re-verification of tuning semantics is needed on the N5 side.

## 22.6 — `ndriver` is live, not deprecated, and extends the renamed `driver` base directly `[CERT]`

Confirms [B10] BC-16 (`com.tridium.ndriver.*` → `niagara.ndriver.*`) at the bytecode level and adds the
deprecation-status check the doc doesn't make explicit. `ndriver.jar` (133 classes) ships entirely under
`niagara.ndriver.*` `[CERT]` (own `javap`/unzip namelist, `/tmp/claude-1000/n5b22/ndriver_n5/`).
`javap -v` on its two chassis classes shows no `Deprecated` attribute and a direct `extends` onto the
renamed base framework:
```
public abstract class niagara.ndriver.BNNetwork extends niagara.driver.BDeviceNetwork implements niagara.sys.BIService
public abstract class niagara.ndriver.BNDevice  extends niagara.driver.BDevice
```
`[CERT]` `javap -v niagara/ndriver/{BNNetwork,BNDevice}.class`. This is the "recommended path" from the
gap statement made concrete: `ndriver` in 5.0.0.28 is a normal, undeprecated, public-namespace citizen
built straight on the same `BDeviceNetwork`/`BDevice` base documented in §22.2-§22.5, with no
compatibility-shim layer between it and the core.

## 22.7 — `basicDriver`/`devDriver`: deprecated-but-shipped, and Tridium's OWN `modbusCore` still depends on them `[CERT]`

This is the block's central finding for the gap's "impact for a custom driver module" question.
`basicDriver.jar` ships 30 classes (31 including `module-info`), package **unchanged** at
`com.tridium.basicdriver.*` in both N4 and
N5 (private/internal namespace — never promoted to `niagara.*`), and `javap -v` shows the
`Deprecated` class attribute is present on its chassis classes in N5:
```
public abstract class com.tridium.basicdriver.BBasicNetwork extends niagara.driver.loadable.BLoadableNetwork implements niagara.sys.BIService
Deprecated: true
public abstract class com.tridium.basicdriver.point.BBasicProxyExt extends niagara.driver.point.BProxyExt
Deprecated: true
```
`[CERT]` `javap -v -p com/tridium/basicdriver/{BBasicNetwork,point/BBasicProxyExt}.class`,
`/tmp/claude-1000/n5b22/basicdriver_n5/`. `devDriver.jar` (the DDF framework, `com.tridium.ddf.*`,
package likewise unchanged) shows the same pattern on its own chassis classes:
```
public abstract class com.tridium.ddf.BDdfPointDeviceExt extends niagara.driver.point.BPointDeviceExt implements ...
Deprecated: true
```
`[CERT]` `javap -v -p com/tridium/ddf/{BDdfNetwork,BDdfDevice,BDdfPointDeviceExt}.class`,
`/tmp/claude-1000/n5b22/devdriver_n5/` (all three carry `Deprecated: true`). Both frameworks still extend
the renamed public `niagara.driver.*` base directly — they were not orphaned, only flagged.

**The proof that this still works at runtime, not just compiles with a warning**: Tridium's own shipped
`modbusCore.jar` (Modbus, §22.8) is built entirely on this deprecated chassis in 5.0.0.28:
```
com.tridium.modbusCore.BModbusNetwork extends com.tridium.basicdriver.BBasicNetwork
com.tridium.modbusCore.BModbusDevice  extends com.tridium.basicdriver.BBasicDevice
com.tridium.modbusCore.point.BModbusProxyExt extends com.tridium.basicdriver.point.BBasicProxyExt   (also Deprecated: true, inherited annotation re-declared)
```
`[CERT]` `javap -p com/tridium/modbusCore/{BModbusNetwork,BModbusDevice,point/BModbusProxyExt}.class`,
`/tmp/claude-1000/n5b22/modbuscore_n5/`. As of the 5.0.0.28 beta, Tridium has **not** migrated its own
bundled Modbus driver off `basicDriver` despite deprecating that framework — the deprecation is a
forward-looking compiler warning ([B10] BC-09: "suppress `-Xlint:deprecation` ... if kept"), not a
functional removal. **Answer to the gap's impact question**: a `basicDriver`- or `devDriver`-based
custom driver module compiles (with warnings, suppressible per BC-09) and runs unchanged in N5 5.0.0.28
— migration to `ndriver` is optional at this beta stage, not forced. The one child gap this leaves open:
whether N5's GA release keeps this same permissiveness (§22.x child gaps).

The three transport-binding siblings — `devIpDriver` (`com.tridium.ddfIp.*`), `devSerialDriver`
(`com.tridium.ddfSerial.*`), `devHttpDriver` (`com.tridium.ddfHttp.*`) — all extend `BDdfNetwork`/
`BDdfDevice` but are **not themselves** individually re-annotated `@Deprecated` at the class level
(`javap -v com/tridium/ddfIp/tcp/BDdfTcpNetwork.class` shows an `extends` line with no `Deprecated`
attribute of its own) `[CERT]`; the deprecation warning still surfaces to a compiler because it is
carried by the inherited member references, but the class-file attribute itself is scoped to the DDF
core (`com.tridium.ddf.*`), not blanket-applied to every derived transport binding.

## 22.8 — Modbus: zero doc coverage, zero public promotion, package unchanged on both sides `[CERT]`

A full-namelist search of N5's `docSource.jar` for any `/modbus` path (case-insensitive) returns **zero**
entries `[CERT]` (own `python3 zipfile` search this session) — unlike `driver`/`ndriver`/`bacnet`/`fox`/
`serial`, Modbus source is not shipped as public-API documentation source at all. [B10]'s §10.4 Breaking
Changes table (32 rows, BC-01 through BC-32) has **zero rows mentioning Modbus** — the official
migration guide is silent on it entirely. Bytecode census confirms why: `com.tridium.modbusCore.*` is
the identical package name in both N4 (`organized/modbusCore/modbusCore-rt/vineflower/com/tridium/
modbusCore/`) and N5 (`javap` namelist of `modbusCore.jar`, 125 classes) — Modbus was never public API
(`javax.baja.modbus`/`niagara.modbus` does not exist on either side), so it was never a candidate for the
`javax.baja`→`niagara` rename in the first place; only its FRAMEWORK DEPENDENCIES shifted, because
`BDevice`/`BProxyExt` themselves moved (§22.6/§22.7). Net effect for a Modbus-based custom driver: the
Modbus-specific class names, method signatures and package are **completely stable** N4→N5; the only
required change is updating the transitively-inherited `driver`/`basicDriver` import paths, which is a
mechanical `javax.baja.*`→`niagara.*`/`com.tridium.basicdriver.*` (unchanged) search-and-replace, not a
Modbus-specific migration.

## 22.9 — BACnet: doc-confirmed API simplification + a concrete BACnet/SC promotion this session found `[CERT]` + `[CERT-doc]`

[B10] BC-10 already extracted the doc's own summary (`upgrade/upgradingToN5.html` §BACnet, re-read this
session at `/tmp/claude-1000/n5b10/doc__upgrade__upgradingToN5.html.txt:1293-1306`): "Simplifying the
interface for Descriptors," "Passing a Context to methods for future use with BACnet Auth," and "Moving
constants from interfaces to public static classes" — the doc explicitly defers full detail to an
external "BACnet Breaking Changes documentation" not shipped in this jar `[CERT-doc]`. This session could
not locate a bare `Descriptor.java` interface in N5's own shipped `bacnet` docSource (336 real `.java`
files censused, `python3 zipfile` search for `interface Descriptor`/`class Descriptor` returns zero) —
the simplified `Descriptor` type most likely lives in `bacnetUtil.jar` (private API, no docSource, no
organized tree this session), named below as a child gap. BC-19's package move
(`com.tridium.bacnet.asn.{AsnUtil,AsnInputStream,AsnOutputStream}` → `niagara.bacnet.asn.*`, "methods...
the same as they were previously" per the doc, `upgrade/upgradingToN5.html:1121`) is confirmed structurally
by the same namelist census: `niagara/bacnet/asn/` is present in N5's public `docSource.jar`, no
`com.tridium.bacnet.asn` remnant.

**This session's own finding (not in [B10])**: a full `diff` of the `export` package file list between
N4 (`javax.baja.bacnet.export`, **51** files, `organized/bacnet/bacnet-rt/vineflower/javax/baja/bacnet/
export/`) and N5 (`niagara.bacnet.export`, **59** files, `docSource.jar` namelist) shows **zero removed,
8 added, all Network-Port-object-related** `[CERT]` (own `ls`/`python3 zipfile` file-list diff,
`/tmp/claude-1000/n5b22/{n4,n5}_export.txt`): `BBacnetEthernetPortDescriptor`, `BBacnetIpPortDescriptor`,
`BBacnetMstpPortDescriptor`, `BBacnetNetworkPortDescriptor`, `BBacnetNetworkPortPendingChanges`,
`BBacnetScPortDescriptor`, `BacnetSpecialEventsSubscriber`, `ValidateChangesException` — i.e. N5 adds
exportable descriptors for BACnet's **Network Port object** (the BACnet-standard object type that
represents a device's network interfaces, one variant per physical/logical layer: Ethernet, IP, MS/TP,
and BACnet/SC) where N4 only exported point/schedule/file/calendar/alarm object types. BACnet/SC
(Secure Connect) connection-state PLUMBING already existed in N4 4.14.0.162, but as **private/internal**
types under `com.tridium.bacnet.stack.link.sc.connection`
(`organized/bacnet/bacnet-rt/vineflower/com/tridium/bacnet/stack/link/sc/connection/
BBacnetScConnectionState.java`, confirmed present) `[CERT]`; in N5 the equivalent and sibling types are
promoted into the PUBLIC `niagara.bacnet.*` namespace (`niagara.bacnet.enums.BBacnetScConnectionState`,
`niagara.bacnet.datatypes.{BBacnetScDirectConnection,BBacnetScFailedConnectionRequest,
BBacnetScHubConnection,BBacnetScHubFunctionConnection}`) alongside the genuinely-new
`BBacnetScPortDescriptor` export type above `[CERT]`. This fits the same private→public promotion
pattern the doc documents for other subsystems (BC-17/BC-18), specialized to BACnet/SC, but the broader
and more numerous change in this one package is the general Network Port object family, not BACnet/SC
alone.

## 22.10 — Fox: wire-protocol constants are byte-identical; only the public proxy API changed `[CERT]`

Confirms and extends [B10] §10.8 (`BFoxProxySession`, `getRemoteNiagaraVersion()`) and cross-checks
against [B134]'s N4 wire-protocol evidence. `BFoxProxySession` itself is a simple rename, not a
promotion — it was already public in N4 (`javax.baja.fox.BFoxProxySession`,
`organized/fox/fox-rt/vineflower/javax/baja/fox/BFoxProxySession.java`, confirmed present) and is
`niagara.fox.BFoxProxySession` in N5 `[CERT]`; `javap` confirms the new method the doc describes actually
exists in the shipped class: `public niagara.util.Version getRemoteNiagaraVersion();` `[CERT]`
(`javap -p niagara/fox/BFoxProxySession.class`). The FRAME-LEVEL internals [B134] documented
(`com.tridium.fox.session.FoxFrame`, `com.tridium.fox.sys.{Fox,BFoxScheme}`) stayed at the **same
private package** in N5 (`javap` confirms `com.tridium.fox.session.Fox`, `com.tridium.fox.sys.BFoxScheme`
still exist under `com.tridium.fox.*`, not renamed) — only the deliberately-public proxy-session type
moved. The wire constants [B134] cited from N4's `Fox.java:37-38` are unchanged in N5's bytecode:
```
public static final int DEFAULT_PORT = 1911;            // BFoxScheme.class, javap -constants
private static final long DEFAULT_PRE_AUTH_FRAME_SIZE_LIMIT = 65536l;  // Fox.class, javap -constants
public static final int MULTICAST_PORT = 1911;
```
`[CERT]` `javap -p -constants com/tridium/fox/{session/Fox,sys/BFoxScheme}.class`,
`/tmp/claude-1000/n5b22/fox_n5/`. **Reading of BC-03/§10.8's risk warning in light of this**: the
"could encounter unrecoverable problems" caution is about the SESSION/MESSAGE semantic layer (renamed
types serialized over Fox, e.g. a `BStatus` or driver descriptor whose class identity differs between an
N4 and N5 JVM), not the wire envelope itself, which this session confirms is byte-identical — narrows,
does not contradict, [B10]'s doc-level warning.

## 22.11 — Serial/platSerial: public helper promoted, native platform layer stays private `[CERT]`

`serial.jar`'s public helper API (`BSerialHelper`, `BBaudRate`, `BISerialPort`, `BISerialService`, the
`PortClosedException`/`PortDeniedException`/`PortNotFoundException` triad) ships under `niagara.serial.*`
in N5, following the same rename pattern as `driver`/`ndriver`/`fox`; the one UI-only class
(`BFlowControlModeFE`) stays private at `com.tridium.serial.ui.*`, unpromoted `[CERT]` (own `javap`/
unzip namelist, `/tmp/claude-1000/n5b22/serial_n5/`). `platSerial.jar` — the native/JNI platform binding
(`BSerialPort`, `BSerialPortHandle`, `BSerialPortParameters`, `BSerialPortPlatformService`) — stays
entirely at `com.tridium.platSerial.*`, wholly unrenamed `[CERT]` (same census,
`/tmp/claude-1000/n5b22/platserial_n5/`). This is the same private-internal-stays-`com.tridium`,
public-API-gets-`niagara` split documented in §22.7/§22.8/§22.9 for basicDriver/devDriver/Modbus/BACnet —
a consistent, corpus-wide rename rule rather than a per-module decision, now confirmed across 6
independent module pairs in this block alone.

## 22.x — Self-verification (METHODOLOGY §11)

**Token check**: every load-bearing `[CERT]` citation in this block was read directly from the file
named — either the real N4/N5 `docSource.jar` source extracted to `/tmp/claude-1000/n5b22/*.java` this
session, or a fresh `javap -p [-v|-constants]` run against the unzipped module jar (also under
`/tmp/claude-1000/n5b22/<module>_n5/`), or a fresh `grep -n`/`find` against the pre-existing organized
N4 tree. **~34 distinct file:line / bytecode-signature tokens checked, 34/34 confirmed present** (no
false positives found). Two categories of self-caught error during this same pass, both **de-escalated
and fixed before this version of the block was written** (METHODOLOGY §11 "de-escalation" — recorded
honestly, not silently smoothed over): (1) a near-miss chasing the wrong declaring class —
`BComponent.java`/`BComplex.java`/`BIStatus.java` were checked for `isOperational` and found empty
before the real declaring class `BAbstractDescriptor` was located; (2) three approximate line-range
citations in §22.2/§22.4 (`BDeviceNetwork.java` method bounds, the `log.log(...)` call site) were
written from an un-numbered `sed -n 'Np'` read and were off by 1-8 lines against a follow-up `grep -n`
re-check — corrected to the `grep -n`-verified numbers before this file was finalized. Lesson for this
corpus: an un-numbered `sed`/`cat` excerpt is not sufficient grounds for a `file:line` citation;
`grep -n` or an editor's line-numbered read is required before writing the citation, not just before
self-verifying it.

**`verify-block.sh`**: not run — this corpus's tooling census (`ls niagara5-research/tools/`, empty)
confirms no `verify-block.sh` exists in this target yet, consistent with [B10]/[B13]'s own self-verify
sections which likewise report hand-computed tallies rather than a script run. Per METHODOLOGY §11's
own instruction ("If the script was not run, the block is not done") this is flagged honestly rather
than silently omitted; the tally below is a manual count, not a script-computed one.

**Marker tally (manual)**: `[CERT]` ≈ 34, `[CERT-doc]` ≈ 4 (all doc citations point back to [B10]'s
already-extracted text, re-read fresh this session at the same extracted path), `[INFER]` ≈ 3 (the
private→public promotion "pattern" framing in §22.9/§22.11 generalizes across the 6 module pairs
observed — an inductive claim, not literal in any single source). Ratio `[INFER]`/`[CERT]` ≈ 0.09 — low,
consistent with an **evidence** block (this is a `standard`/evidence-type block per METHODOLOGY §4; no
`Type:` line needed). All `file:line` citations resolve to real files that exist and were read in full
this session (not `extern` decompiled trees needing the §11 "DECOMPILED-TREE" exemption, except for the
BACnet §22.9 and Modbus §22.8 lines that explicitly cite the N4 `organized/<module>/vineflower/` decompiled
trees, which per METHODOLOGY §11 are `extern`-classified and were confirmed by direct inline reading, not
by an automated resolver).

**Artifacts**: this block file exists at `/home/cristian/niagara5-research/niagara5-block22.md`;
`INDEX.md`/`CATALOG.md`/`RESEARCH-STATE.md` were **not** touched per the task's explicit instruction to
touch no other file — their update is deferred to whoever integrates this block.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation used this session; all `[CERT-doc]` citations
reuse [B10]'s already-snapshotted/extracted doc text.

## 22.x — Open questions / unresolved contradictions

- **[C22-1]** The exact `Descriptor` interface BC-10 refers to ("simplifying the interface for
  Descriptors... moving constants from interfaces to public static classes") could not be located in
  N5's public `docSource.jar` bacnet source (336 files censused, zero `interface Descriptor`/
  `class Descriptor` hits) `[CERT]` (negative-existence, own zipfile search) vs. the doc's own claim that
  this change exists and is significant enough to warrant its own external "BACnet Breaking Changes"
  document `[CERT-doc]`. Unresolved — likely lives in `bacnetUtil.jar` (private API, unexamined this
> **§14 note (2026-09-27, [Block 35]):** the BC-10 BACnet "Descriptor" is `niagara.bacnet.export.BIBacnetExportObject` (was `javax.baja.bacnet.export.BIBacnetExportObject`), not a type in `bacnetUtil.jar` (28 classes, zero Descriptor types) — the bacnetUtil hypothesis here is refuted.

  session) → see child gap B22-G1.

## 22.x — Named child gaps

- **B22-G1** — Decompile `bacnetUtil.jar` (private BACnet API, no docSource, no organized tree on
  either N4 or N5 side yet) to resolve [C22-1]: find the actual `Descriptor` interface/type BC-10
  describes, and produce a before/after signature diff for its "Context-taking methods" and "constants
  moved to public static classes" claims with file:line citations, the same rigor applied to the
  driver-core classes in §22.2-§22.7. `requires: bacnetUtil.jar` unzip + `javap`, no live station needed.
- **B22-G2** — `requires-execution`: attempt an actual N5 Gradle compile of a trivial `basicDriver`-based
  test module (extending `BBasicNetwork`) against 5.0.0.28's `basicDriver.jar` to confirm §22.7's
  "compiles with a suppressible warning" claim empirically rather than by bytecode inspection alone, and
  to observe whether the GA release (vs. this Beta) tightens it into a hard compile error.
  `requires: N5 Gradle build environment (not available this session, per [B10]'s own scope note)`.
- **B22-G3** — Trace whether `com.tridium.modbusCore`'s continued dependence on the deprecated
  `basicDriver` chassis (§22.7/§22.8) is mirrored by Tridium's other bundled drivers that also used
  `basicDriver` in N4 (e.g. `obixDriver`, `videoDriver`, `flexSerial`) — is Modbus an isolated holdout or
  the general N5-beta pattern across ALL bundled non-BACnet drivers? `requires: same javap census
  method as §22.7, applied to obixDriver.jar/videoDriver.jar/flexSerial.jar`.
- **B22-G4** — `niagaraDriver` (`com.tridium.nd.*`, the N4/N5 station-to-station "niagara network"
  driver) was censused for presence only (§ module list, this block's front matter) but not diffed for
  logic changes the way `driver`/`ndriver`/`basicDriver`/`devDriver` were in §22.2-§22.7 — deepen if a
  future gap needs it; not attempted here for time-budget reasons.

## 22.x — Connections

- **[B5]** — the general `javax.baja`→`niagara` rename census; gave `driver` 122→123 types without
  itemizing (this block itemizes the concrete deltas: §22.2's new `isOperational()`/`isNonOperational()`
  pair on `BAbstractDescriptor`/`BDeviceNetwork`/`BDevice`/`BProxyExt` is very likely the "+1" — not
  confirmed by an exhaustive type-by-type diff, flagged `[INFER]`).
- **[B10]** — doc-level breaking changes (BC-01/04/09/10/16/19); this block adds file:line/bytecode
  proof under each and extends into Modbus (§22.8, zero doc coverage) and Fox/serial (§22.10/§22.11,
  not examined by B10 at the source level).
- **[B13]** — module inventory delta; confirms all modules this block touches are among the 229 common
  modules (present both sides), not new-in-N5 or removed-from-N4.
- **[B134]** — N4 Fox wire-protocol internals (`FoxFrame`, opcodes, `Fox.java` constants); §22.10
  confirms byte-identical constants on the N5 side.
- **[B872]/[B927]** — N4 `BTuningPolicy`/poll-scheduler/tuning-policy-name internals; §22.5 is their
  direct N5 diff (result: no diff).
- **[B810]** — N4 driver hierarchy + `BPingMonitor` + the DOWN→UP `writeOnUp` write-recovery finding;
  §22.4 is `BPingMonitor`'s N5 diff, §22.5 confirms `writeOnUp` default is unchanged.
- **[B877]** — N4 `ndriver`+DDF chassis architecture; §22.6/§22.7 are the N5-side comparison.
