# Block 69 — `NiagaraDaemon.Main()` structurally cannot be reached through `Bootstrap`/`Nre.main`'s `nreMain` dispatch, closing B65-G1's exact question; plus three closed security/audit gaps: `isPrivileged`'s stack-walk rule (pre-closed by [Block 8]), `BUserService.auditLoginAttempt` as a documented-but-uncalled public API (B54-G4), and Orion's first-party RDBMS audit channel (B54-G5)

> Research closing/narrowing the runtime-security confirmation cluster named by the task. **Numbering note,
> stated up front**: the task's own gap description calls the priority gap "B65-G3" ("Block 65 found
> `NiagaraDaemon.Main()` sets `PermissionUtil.isTrustedDomain=true` unconditionally... CONFIRM or REFUTE that
> `NiagaraDaemon.Main()` and the Bootstrap wiring... run in the SAME process/call stack") and separately lists
> "B65-G1: niagarad launch-sequence / call-stack confirmation (same territory)" as though it were a distinct,
> companion gap. A direct re-read of [Block 65] §65.5 this session finds these are the SAME gap, and its real
> ID in that block's own file is **B65-G1** — its literal text: "Confirm whether `niagarad.exe`'s own JVM
> invocation actually loads `nre.jar`'s `-javaagent` instrumentation, and trace the exact call sequence
> between... `Bootstrap`'s startup path and... `NiagaraDaemon.Main()` — specifically, whether `Main()` runs in
> the SAME process/call stack `Bootstrap.java:232-234`'s `permissionBridge` assignment does." [Block 65]'s own
> **B65-G3** is a different, untouched gap (`FilePermission`/`RuntimeExecPermission`/`NiagaraBasicPermission`'s
> `doIsGrantedTo(Module)` grant-matching bodies) — not opened this session either, still open. This block uses
> [Block 65]'s own file's IDs throughout (so a reader following `[Block 65]` §65.5 finds the right entry), not
> the task prompt's mislabeled ones.
>
> Closes/narrows: **B65-G1** (the priority) — traces the actual Java-side dispatch mechanism
> (`Bootstrap.Main()` → `Nre.bootstrap()` → `Nre.main()` → `Nre.runClass()`) that launches every OTHER Niagara
> process type in this corpus and finds `NiagaraDaemon` structurally cannot satisfy its reflection contract —
> closing the Java-source half of B65-G1 to `[CERT]` (narrows, does not fully close, the native-binary half).
> **B65-G2** (read `PermissionUtil.isPrivileged`'s frame-classification rule) — found this session to already
> be fully answered by **[Block 8]**, which predates [Block 65]'s own re-opening of the same question; this
> session's fresh direct read corroborates [Block 8] independently. **B54-G4** — confirm whether
> `BUserService.auditLoginAttempt`'s zero-callers finding is genuine dead code or a public third-party API
> surface. **B54-G5** — trace `BOrionSecurityAudit`'s parallel database-record audit channel: what it records,
> its retention/backing store, and whether Orion is first-party or an OEM/licensed layer.
>
> Does **not** cover: the native-launcher binary read itself (what `niagarad.exe` literally passes to
> `JNI_CreateJavaVM`/`FindClass`/`CallStaticVoidMethod`) — [Block 63] (REMIT, checked this session for overlap
> only) already disassembled `nre.dll`'s `NreLauncherWin32::buildArgs`/`buildVMOptions` for their
> **VM-argument flag content**, not for which Java class/method name is resolved and invoked as the entry
> point; that specific disassembly was not attempted this session and remains the residual half of **B65-G1**,
> restated at §69.6; [Block 65]'s own **B65-G3** (`doIsGrantedTo` grant-matching bodies, unrelated to this
> session's scope, not opened); a live-station capture of any audited event (`[CERT-hw]`, blocked — no
> runnable N5 station this session, same constraint as [Block 41]'s **B41-G4**/[Block 49]'s **B49-G1**/
> [Block 54]'s **B54-G2**/[Block 65]'s **B65-G4**); `BOrionDatabase`'s own physical storage format/retention-
> policy internals (only `OrionSession`'s interface contract was read, not `BOrionDatabase`'s implementation —
> new gap, §69.6).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as every predecessor block
> (`etc/brand.properties:workbench.notice`). No fresh decompilation — every file cited was already present in
> this corpus's `organized/` tree from prior sessions ([Block 1]'s corpus-wide extraction for `nre.jar`/
> `niagarad.jar`; [Block 25]'s `baja.jar`/`platform.jar` extraction; the `orion` module's own extraction,
> already in-corpus since at least [Block 54]'s citation of `BOrionSecurityAudit.java`).
>
> Sources: `organized/_bin-ext/nre/vineflower/com/tridium/nre/bootstrap/Bootstrap.java` (whole 366-line file
> re-read past [Block 65]'s `:228-238` targeted citation — this session reads `:1-119` for the class header/
> `Main()` signature/`isStation` detection and `:230-238` for the `Nre`-loading tail); `organized/baja/
> vineflower/com/tridium/sys/Nre.java` (whole 1400-line file — first whole-file open of this file in this
> corpus; [Block 54] only grep'd/targeted-read it): `:174-178` (`bootstrap`/`main` delegation), `:236-371`
> (`main()`'s full body, args-parsing through `runClass()` call and the `Nre.FatalException` catch),
> `:494-539` (`runClass()`, whole method, the `nreMain` reflection contract), `:1234-1237` (`fatal()`),
> `:1331` (`FatalException` class declaration); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/
> NiagaraDaemon.java` (whole 1641-line file confirmed via corpus-wide `grep -c`/`grep -rl` this session,
> targeted re-read `:1-40,119,185-238` — `Main()` body re-read past [Block 65]'s `:195-199` head-only
> citation); `organized/baja/vineflower/com/tridium/sys/station/Station.java:735-760` (`nreMain()` head, first
> read of this file's `nreMain` in this corpus); `organized/_bin-ext/niagarad/vineflower/module-info.java`
> (whole file, re-read past [Block 65]'s citation — full `requires`/`exports`/`opens` lists read this session,
> not just the `requires transitive niagara.nre` line); `organized/_bin-ext/nre/vineflower/niagara/nre/util/
> SecurityUtil.java:229-232` (`checkPermission`), `:322-355` (`consumePrivilegedModules`/`isPrivileged`, whole
> both methods); `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/PermissionManager.
> java:40-139` (whole `checkPermission` method plus its field-declaration header, wider than [Block 65]'s/
> [Block 8]'s `:51-139` citation); `organized/_bin-ext/nre/vineflower/com/tridium/nre/security/permissions/
> NiagaraPermission.java` (whole 41-line file, re-read); `organized/baja/vineflower/niagara/user/
> BUserService.java:415-434` (`auditLoginAttempt`, re-read past [Block 54]'s citation); `organized/
> docDeveloper/vineflower/doc/baja/niagara/user/BUserService.bajadoc:674-720` (the `auditLoginAttempt`
> `<method>` entry — first bajadoc-XML open for this method in this corpus); `organized/orion/vineflower/com/
> tridium/orion/priv/securityAudit/BOrionSecurityAudit.java` (whole 245-line file, first whole-file open of
> this file in this corpus — [Block 54] cited only `:142-234`); `organized/orion/vineflower/com/tridium/orion/
> BSecurityAuditMode.java` (whole 49-line file, first open); `organized/orion/vineflower/com/tridium/orion/
> OrionSession.java:1-60` (interface header + method signatures, first open); `organized/docDeveloper/
> vineflower/doc/orion/com/tridium/orion/BOrionService.bajadoc:1-40` (class description + `auditMode`/
> `securityAuditMode` property docs, first open). Whole-tree `grep -rn`/`grep -rl` this session for
> `NiagaraDaemon` (corpus-wide), `com.tridium.sys.station.Station` (corpus-wide), `public static void
> nreMain(` (corpus-wide, 40 files, each individually re-`grep`-checked for a `NiagaraDaemon` reference — zero
> hits), `\.auditLoginAttempt\(` (corpus-wide, 1 hit: the bajadoc entry). One `corpus-nav.py find
> "isPrivileged"` REMIT lookup (secondary tool, surfaced [Block 8]'s prior closure of B65-G2).
>
> Method: direct reading of pre-existing in-corpus Vineflower decompiles (nothing re-decompiled this session);
> corpus-wide `grep -rn`/`grep -rl` negative-existence censuses, each reported as an exhaustive count, not a
> sample, per METHODOLOGY §3's negative-existence rule (every named artifact was actually opened/grepped this
> session). Markers (canonical list: METHODOLOGY §3): `[CERT-hw]` verified against the live system/device —
> highest · `[CERT]` local primary source (`file:line`) · `[CERT-a]` secondary/forum · `[INFER]` deduction.
> `file:line` citations point into `organized/<module>/vineflower/...` inside **this** corpus
> (`/home/cristian/niagara5-research/`).
>
> Runtime-security confirmation cluster, closing the loop [Block 65] opened at the end of its own session and
> correcting one instance of gap-reopening across this corpus. Connects [Block 65] (closes **B65-G1** to
> `[CERT]` for the Java-source half; found **B65-G2** was already answered by [Block 8] before [Block 65]
> re-opened it), [Block 8] (the actual prior closer of the `isPrivileged` question — this session's §69.2
> corroborates and lightly extends it, does not supersede it), [Block 63]/[Block 61]/[Block 57] (REMIT only,
> the native-launcher-binary disassembly cluster this session's §69.1 explicitly does NOT extend, naming the
> precise residual sub-question those blocks did not answer either), [Block 54] (closes **B54-G4** and
> **B54-G5**, both opened by that block's own §54.7).
>
> **Type:** `mixed` — §69.1's "`NiagaraDaemon` structurally cannot be reached via `runClass`" finding is
> `[CERT]` evidence (a reflection-contract absence, directly read); its "therefore a separate native entry
> point" conclusion is `[INFER]` built across this session's own dense `[CERT]` reads (the MIXED-block trigger
> METHODOLOGY §11 names — an `[INFER]` drawn across this block's own evidence). §69.2 explicitly corrects a
> cross-block gap-tracking error rather than producing new fact. §69.3–§69.4 are `evidence`-shaped direct
> reads.

---

## 69.1 — `NiagaraDaemon.Main()` cannot be reached via `Bootstrap`→`Nre.main`→`Nre.runClass`'s `nreMain` reflection contract — every other Niagara process type in this corpus goes through it, `NiagaraDaemon` structurally cannot, closing B65-G1's exact question `[CERT]`+`[INFER]`

**The dispatch mechanism every OTHER Niagara Java process in this corpus uses, read whole this session.**
`Bootstrap.Main(String[] args)` — note the capital `M`, not the lowercase `main` the JVM's own native launcher
convention requires, itself evidence this method is invoked by a bespoke native call rather than the standard
`java ClassName` convention `[CERT]` `Bootstrap.java:88` — inspects `args[0]` for the literal string
`"com.tridium.sys.station.Station"` to set an `isStation` flag `[CERT]` `Bootstrap.java:97`, builds the
`niagara.baja` module layer, and — after the already-documented `!PermissionUtil.isTrustedDomain` guard on
`SecurityBridge.permissionBridge` ([Block 65] §65.3, `:232-234`, re-confirmed this session) — reflectively
loads `com.tridium.sys.Nre` and invokes its `bootstrap(String[])` method: `Class<?> bootstrapClass =
loader.loadClass("com.tridium.sys.Nre"); Method bootstrap = bootstrapClass.getMethod("bootstrap",
String[].class); bootstrap.invoke(null, args);` `[CERT]` `Bootstrap.java:236-238`. `Nre.bootstrap(String[])` is
a 1-line delegate to `Nre.main(String[])` `[CERT]` `Nre.java:174-178`. `Nre.main()` — after handling several
CLI-flag early-returns (`-version`, `-modules`, `-hostid`, etc.) and calling `boot()` — reads
`args.parameters[0]` as a **class name** (optionally `module:class`-prefixed) and calls `runClass(module,
className, nreMainArgs)` `[CERT]` `Nre.java:338,360` (whole surrounding block `:236-371` read this session,
extending [Block 54]'s prior targeted citations of this file).

**`Nre.runClass()` — the actual reflective invocation, and its hard failure mode, read whole this session (not
previously opened in full by any prior block on this corpus):**
```java
static void runClass(NModule module, String className, String[] nreMainArgs) {
   ...
   Class<?> cls = module != null ? module.loadClass(className) : Class.forName(className);
   Method nreMain = null;
   try {
      nreMain = cls.getMethod("nreMain", new Class[]{String[].class});
      if (!nreMain.getReturnType().equals(void.class)) fatal("FATAL: nreMain must return void: " + className);
      if (!Modifier.isPublic(nreMain.getModifiers())) fatal("FATAL: nreMain must be public: " + className);
      if (!Modifier.isStatic(nreMain.getModifiers())) fatal("FATAL: nreMain must be static: " + className);
   } catch (Exception exception) {
      fatal("FATAL: No nreMain: " + className);
   }
   nreMain.invoke(null, new Object[]{nreMainArgs});
   ...
}
```
`[CERT]` `Nre.java:494-539` (whole method, condensed for readability — every line above is verbatim from the
source, not paraphrased). `fatal(String)` prints the message and `throw new Nre.FatalException()` `[CERT]`
`Nre.java:1234-1237`; `Nre.main()`'s own enclosing `try` block catches exactly `Nre.FatalException` and calls
`System.exit(-7)` `[CERT]` `Nre.java:361` (cited by [Block 54] as part of its wider `:236-263` citation, the
specific catch clause re-confirmed this session). **The reflection contract is therefore hard-fail, not
best-effort**: a class dispatched through `runClass()` that lacks a `public static void nreMain(String[])`
method causes the WHOLE process to print `FATAL: No nreMain: <className>` and exit with code `-7`, before any
of that class's own logic ever runs.

**`Station` satisfies this contract and visibly depends on state `Nre.main()` populated earlier in the SAME
call — direct evidence `Station` genuinely runs downstream of this exact chain, not merely coincidentally
alongside it:**
```java
public static void nreMain(String[] args) {
   mainMillis = Clock.ticks();
   if (args.length < 1) { usage(); System.exit(-2); }
   if (!Nre.protectedStationHome.exists() || !Nre.protectedStationHome.isDirectory()) { ... }
   String project = Nre.args.parameters[1];
   ...
}
```
`[CERT]` `Station.java:742-756` (head of the method, this session's first open of `nreMain` in this file) —
`Nre.protectedStationHome` and `Nre.args` are both `Nre`'s own static fields, populated during the SAME
`Nre.main()` invocation (`boot()`, args-parsing) that then calls `runClass()` to reach this method — `Station`
is not merely dispatched by the same mechanism, it structurally CONSUMES that mechanism's side effects.

**`NiagaraDaemon` has no `nreMain` method anywhere in its 1641-line file — confirmed by direct `grep`, not
inference from a partial read:**
```
$ grep -c "nreMain" organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/NiagaraDaemon.java
0
```
`[CERT]` (whole-file `grep`, this session — the file itself is confirmed 1641 lines via `wc -l`, the same
`NiagaraDaemon.java` [Block 63]/[Block 65] both already cite, so this is the correct, complete artifact, not a
truncated/stale copy). `NiagaraDaemon`'s own entry point remains exactly the `public static void
Main(String[] args)` [Block 65] §65.3 already cited (`:195-199`) — same capital-`M` naming as `Bootstrap.Main`
— re-read this session `:195-238` (through the `parseArguments`/`serviceMain`/`consoleMain` dispatch tail) —
and, unlike `Station.nreMain()`, this method never references `Nre.` or `Bootstrap.` anywhere in the file
(zero hits, `grep` this session) — it does its own `NiagaraFiles.copyFromDefaults()`/`copyFromEtc()`/
`parseArguments(args)` from scratch, consuming no state any `Nre.main()` invocation would have set up.
**Corollary, mechanically forced by the code above**: if `NiagaraDaemon` were ever dispatched via
`args.parameters[0] = "com.tridium.niagarad.NiagaraDaemon"` through this exact chain, `Nre.runClass()`'s
`cls.getMethod("nreMain", ...)` lookup would throw `NoSuchMethodException`, `runClass()` would call
`fatal("FATAL: No nreMain: com.tridium.niagarad.NiagaraDaemon")`, and the process would `System.exit(-7)`
**before `NiagaraDaemon.Main()` is ever reached** — this specific dispatch path is not merely unused, it is
provably incapable of reaching `NiagaraDaemon.Main()` at all.

**No wrapper class anywhere in the corpus bridges the gap either.** A corpus-wide `grep -rl "public static
void nreMain("` finds exactly **40** classes implementing the contract (`Station`, `WbMain`, `BPlat` [the
`plat` command-line tool [Block 63] §63.1 already found `plat.exe` natively spawned for daemon-restart],
`TestRunner`, `Migrate`, `RegTool`, 34 others — developer/migration/help tools) — each of these 40 files was
individually `grep`-checked this session for the literal string `"NiagaraDaemon"`; **zero** contain it `[CERT]`
(loop run this session, verbatim: `for f in <40 files>; do grep -q "NiagaraDaemon" "$f" && echo HIT; done` —
zero lines printed). No class in this corpus's `nreMain`-contract roster calls or references `NiagaraDaemon`
in any way.

**Reading this together — the exact answer to B65-G1's stated question.** `[CERT]`: `NiagaraDaemon.Main()`
cannot be reached via the `Bootstrap.Main()` → `Nre.bootstrap()` → `Nre.main()` → `Nre.runClass()` chain — the
SAME chain [Block 65] §65.3's own `[INFER]` was worried about (`Bootstrap.java:232-234`'s `permissionBridge`
assignment sits inside `Bootstrap.Main()`, upstream of that exact chain). This is a structural, reflection-
contract impossibility (confirmed by direct absence-reads plus the hard-fail behavior of the one mechanism
that could reach it), not a probabilistic inference from missing evidence. **This closes the Java-source half
of B65-G1 to `[CERT]`: `NiagaraDaemon.Main()` and `Bootstrap.java:232-234`'s wiring do NOT run in the same
call stack** — whatever native mechanism `niagarad.exe` actually uses to invoke `NiagaraDaemon.Main(String[])`
(capital `M`, matching `Bootstrap.Main`'s own unconventional signature — both are plainly designed to be
invoked directly by a native caller via an explicit method-name JNI call, not by the standard `java
ClassName` launcher convention that requires lowercase `main`), it is a SEPARATE entry sequence from the one
`Bootstrap`/`Nre`/`Station` share. **This refines, and partially corrects, [Block 65] §65.3's own framing**:
that section reasoned "for any JVM process where `NiagaraDaemon.Main()` runs before (or instead of)
`Bootstrap`'s `permissionBridge` assignment" — phrasing that left open whether `Bootstrap`'s code executes at
all in the `niagarad` process. This session's evidence favors the STRONGER reading: `Bootstrap.Main()` (and
therefore its `Nre`-loading/`permissionBridge`-wiring sequence) most likely never executes in the `niagarad`
process AT ALL, for the structural reason above — not merely that its `!isTrustedDomain` guard gets evaluated
and skipped. The two readings converge on the SAME observable consequence (`permissionBridge` stays `null` for
`niagarad`), so [Block 65]'s downstream conclusion (the advice layer is inert for that process) is UNCHANGED
and not weakened by this correction — only the mechanism-level "why" is sharpened. `[INFER]` for the "separate
native entry sequence" conclusion specifically (the one residual honestly named): this session did not read
`niagarad.exe`'s own native disassembly (that is [Block 63]/[Block 61]'s territory, and [Block 63]'s Does-not-
cover note above confirms it did not resolve THIS specific sub-question either) — so the claim rests entirely
on Java-side absence-of-a-path evidence, not a direct observation of what `niagarad.exe` literally calls. This
is the correct, narrower framing of the residual gap, tracked at §69.6 as the surviving half of **B65-G1**.

## 69.2 — `SecurityUtil.isPrivileged`'s frame-classification rule and its AND-across-the-module-set enforcement — B65-G2 was already closed by [Block 8]; this session's fresh direct read corroborates it independently `[CERT]`

**Corpus-hygiene finding, stated first.** [Block 65] §65.5 opened **B65-G2** — "Read
`PermissionUtil.isPrivileged(StackFrame, int[])`... to confirm precisely which stack frames count as
'privileged'" — as though the question were unanswered. A `corpus-nav.py find "isPrivileged"` lookup this
session (REMIT tool, not a primary source) surfaces that **[Block 8]** ("N5 permission model: SecurityAgent
advice and PermissionManager grants") already read and documented this exact method, with the exact same
citation range this session independently arrived at (`SecurityUtil.java:335-355`), and already states the
takeaway [Block 65] asked for: `isPrivileged` is "a hand-rolled 'privileged frame' boundary detector that
stops the walk 2 frames after it sees either `niagara.nre.util.SecurityUtil.doPrivileged` or
`java.security.AccessController.doPrivileged` on the stack, and skips `Class.forName` frames outright." This
session's own fresh read (below) independently confirms [Block 8]'s reading is correct — **B65-G2 is closed,
by [Block 8], predating [Block 65]'s own re-statement of it as open.** (Naming note: the task also calls this
`PermissionUtil.isPrivileged` — the method is actually `SecurityUtil.isPrivileged`, `private`, in
`niagara.nre.util.SecurityUtil`, not in the 4-field `permissions.restricted.PermissionUtil` static-holder
[Block 65] §65.3 read whole; [Block 8] correctly located it there too — flagged here since the task's own gap
description inherited [Block 65]'s naming.)

**The method, read whole this session (`SecurityUtil.java:335-355`):**
```java
private static boolean isPrivileged(StackFrame frame, int[] stackCounter) {
   if (stackCounter[0] == 0) return false;
   String className = frame.getClassName();
   if ("java.lang.Class".equals(className) && "forName".equals(frame.getMethodName())) return false;
   if (("niagara.nre.util.SecurityUtil".equals(className) || "java.security.AccessController".equals(className))
      && "doPrivileged".equals(frame.getMethodName())) {
      stackCounter[0] = 2;
   }
   if (stackCounter[0] > 0) stackCounter[0]--;
   return true;
}
```
`[CERT]`, whole method, called from `consumePrivilegedModules`'s `StackWalker.walk(frames ->
frames.takeWhile(frame -> isPrivileged(frame, stackCounter)) ...)` `[CERT]` `SecurityUtil.java:322-332`
(re-confirmed whole this session past [Block 65]'s/[Block 8]'s prior citations of the same range). Traced
frame-by-frame from the innermost (closest to the `checkPermission` call site) outward: `stackCounter` starts
at `-1`; every frame is included (`return true`) UNLESS it is a `Class.forName` frame (excluded immediately,
walk stops there) or the counter has counted down to exactly `0` (excluded, walk stops); the counter is only
ever SET (to `2`) the moment a `SecurityUtil.doPrivileged`/`AccessController.doPrivileged` frame is seen — that
triggering frame is itself still included — after which exactly **2 more** outward frames are also included
(counter `2→1→0`) before the walk stops at the 3rd frame past the `doPrivileged` boundary. With **no**
`doPrivileged`/`forName` frame anywhere on the stack, the walk does not stop on its own — it collects every
frame from the call site to the bottom of the thread's stack.

**The AND-across-the-set enforcement mechanics — the one detail this session's read makes more explicit than
[Block 8]'s prose.** `consumePrivilegedModules` collects the surviving frames' declaring-class `Module`s into
a `Set<Module>` and calls `consumer.accept(module)` (= `permission::isGrantedTo`, i.e.
`PermissionManager.checkPermission(permission, module)`) for **every** module in that set, in a bare `for`
loop with **no per-iteration try/catch** `[CERT]` `SecurityUtil.java:322-332`. `PermissionManager.checkPermission`
re-read whole this session (`PermissionManager.java:40-139`, wider than [Block 65]'s/[Block 8]'s `:51-139`
citation — this session additionally reads the class's field-declaration header, `:40-49`, confirming the
`permissionCheckCache`/`modulePermissions` fields' exact types) either returns silently (trusted-by-name
allowlist hit, or a cached `true`) or throws `PermissionException`, which is caught only at the very TOP of
the method (for audit-logging), then **re-thrown unless `PermissionUtil.permissionChecksDisabled`** `[CERT]`
`PermissionManager.java:53-55,79-88,118-139`. Since the `for` loop in `consumePrivilegedModules` has no
per-module exception boundary, the exception propagates straight out of the loop, aborting the WHOLE
`SecurityUtil.checkPermission()` call at the FIRST module (in stack order, innermost-first) that fails — this
is a genuine **AND**: every module the walk collects must INDEPENDENTLY hold the permission (or be
allowlisted/cached-true) for the check to pass; a single failing module anywhere in the collected set denies
the entire operation, regardless of whether a module further out in the set (not yet reached) would have
passed. `[CERT]` for every mechanical step; the characterization "AND, not OR" is `[INFER]` built directly
from this session's own `[CERT]` reads of both methods together (a straightforward reading of "for-loop with
no per-iteration catch feeding a rethrow" — the same structural conclusion [Block 8] independently reached and
named "deny if ANY of them lacks the permission").

**Practical reading, answering the gap's own stated concern ("can a deeply-nested call chain cause an
INTERMEDIATE module... to be silently checked/granted instead of the actual originating third-party
module").** Given AND semantics, the mechanism cannot silently GRANT past a denying intermediate module — a
failing module anywhere in the walked window still denies. The real behavior this design produces is closer
to the opposite: because `PermissionManager`'s trusted-by-name allowlist (`niagara.nre`/`niagara.baja`/
`niagara.niagarad`/`net.bytebuddy.agent`/`java.*`/`javax.*`/`jdk.*`/`javafx.*`, [Block 65] §65.2/[Block 8])
exempts every FRAMEWORK frame in the window by name, the walk's practical effect is to check EVERY
non-framework (i.e. genuinely third-party) module actually present in the calling chain, not just the
immediate caller — a broader, more conservative check than "only the direct caller matters," and a direct
structural echo of the pre-agent `AccessControlContext`/`ProtectionDomain`-intersection model N4's
`SecurityManager` used (already named by [Block 8], REMIT here, not re-derived). The `doPrivileged` 2-frame
cutoff exists to deliberately NARROW this window — matching the classical `AccessController.doPrivileged`
purpose of letting trusted code perform a sensitive operation on behalf of a less-trusted, more-distant caller
without forcing that caller itself into the checked set. `[INFER]` (a design-intent reading built on the
`[CERT]` mechanics above, consistent with — not contradicting — [Block 8]'s own framing).

## 69.3 — `BUserService.auditLoginAttempt`: a documented, `@since Niagara 3.3` public API method with zero callers anywhere in this decompiled corpus — closing B54-G4 to the corpus's evidentiary limit `[CERT]`+`[INFER]`

**The corpus-wide negative-existence check, re-run and widened this session.** [Block 54] §54.2's table already
found zero callers for `niagara.user.BUserService.auditLoginAttempt(boolean, BUser, Context)` (public, `final`,
`BUserService.java:415-434`) inside `organized/`. This session re-runs the same census with a wider pattern
(`\.auditLoginAttempt\(`, corpus-wide, not scoped to any one module) and finds exactly **one** hit total, and
it is not a Java call site:
```
organized/docDeveloper/vineflower/doc/baja/niagara/user/BUserService.bajadoc:674:
<!-- niagara.user.BUserService.auditLoginAttempt(boolean,niagara.user.BUser,niagara.sys.Context) -->
```
`[CERT]` (single corpus-wide `grep -rn` this session). **The bajadoc entry is the decisive new evidence B54-G4
asked for.** Read whole this session, the `<method>` element carries:
```xml
<method name="auditLoginAttempt" public="true" final="true">
<description>
Records a standard formatted audit history record for a user authentication event (login attempt).
The loginSuccessful boolean parameter specifies whether the login attempt was successful (true) or
failed (false). ... The auditContext parameter is used to configure how the audit trail will be
handled when invoking this method. ...
</description>
<tag name="@since">Niagara 3.3</tag>
<parameter name="loginSuccessful"><type class="boolean"/></parameter>
<parameter name="user"><type class="niagara.user.BUser"/></parameter>
<parameter name="auditContext"><type class="niagara.sys.Context"/></parameter>
<return><type class="void"/></return>
</method>
```
`[CERT]` `organized/docDeveloper/vineflower/doc/baja/niagara/user/BUserService.bajadoc:674-720` (the
`<method>` element, whole, first bajadoc-XML open of this specific entry in this corpus). **This is Tridium's
own auto-generated API documentation** (`bajadoc`, `createdBy="tridium-niagara-baja-doclet-5.0.4"`, confirmed
at the file's own XML header this session) — a `public`, `final`, documented, parameter-described method
carrying an `@since Niagara 3.3` tag (i.e. this method has been a PUBLISHED part of the Niagara SDK's
`BUserService` API surface since Niagara 3.3, well before N4 or N5, and was carried forward unchanged into N5
5.0.0.28's own generated docs for this build).

**Verdict, answering B54-G4's three named hypotheses directly.** The bajadoc entry is `[CERT]` evidence AGAINST
the "legacy path superseded by `BAuthenticationService`" hypothesis in its strong form (a truly superseded
internal method would ordinarily carry a `@deprecated` tag in a current-build bajadoc generation — none is
present, `[CERT]` absence, whole `<method>` element read) and POSITIVE evidence FOR the "public API surface for
third-party module callers not present in this corpus" hypothesis: this corpus's `organized/` tree holds only
Tridium's OWN first-party modules (the decompiled jars this corpus's whole extraction history covers,
[Block 1]/[Block 25]) — it structurally CANNOT contain the thousands of third-party/OEM driver and
authentication-integration modules that exist outside Tridium's own shipped module set, and a published,
`@since`-tagged, non-deprecated public method on a core service class (`BUserService`, the very type that owns
login/lockout policy — [Block 54] §54.1's `security=true`-faceted properties) is exactly the shape of API a
third-party custom authentication scheme or SSO-bridge module would call to route ITS OWN login events into
Niagara's standard `$/SecurityHistory`/`$/AuditHistory` channels [Block 54] §54.2 already fully traced, rather
than hand-rolling its own `SecurityAuditEvent` construction. `[CERT]` for the zero-callers-in-corpus fact and
the bajadoc's exact content; `[INFER]` for the "intended third-party entry point, not dead code" conclusion —
this session's evidence supports it strongly but cannot rule out the weaker case (a method published once, in
fact never called by anyone, first-party or third-party) without access to the closed universe of shipped
third-party modules, which is out of this corpus's scope by construction, not merely unexamined this session.
This is the corpus's evidentiary ceiling for this specific question — named as the residual half of **B54-G4**
at §69.6, not silently treated as fully closed.

## 69.4 — `BOrionSecurityAudit`: Orion is a first-party N5 subsystem dating to Baja 1.0 (2007), and its "database record" audit mode is a genuinely separate, operator-configurable third channel backed by Orion's own RDBMS — closing B54-G5 `[CERT]`

**Is Orion first-party or OEM/licensed?** `[CERT]`, first-party — settled directly from `BOrionService`'s own
bajadoc, read whole this session: `"BOrionService is the service that enables a station and its applications to
use the Orion database."`, `@author John Sublett on 11 Jul 2007`, `@since Baja 1.0` `[CERT]`
`organized/docDeveloper/vineflower/doc/orion/com/tridium/orion/BOrionService.bajadoc:1-10`. `@since Baja 1.0`
places Orion's origin at the ORIGINAL "Baja" framework generation — predating even Niagara 4 — with a named
Tridium engineer as author; the `niagara.orion` module (`module-info.java`, whole file read this session)
`requires transitive niagara.rdb` and declares `@GrantPublicNiagaraBasicPermission("RDB_CONNECTION")` at the
module level `[CERT]` — Orion is Tridium's own long-standing, built-in relational-database subsystem, not a
licensed third-party add-on.

**What the "database record" channel actually is, read from `BOrionSecurityAudit.java` whole (245 lines, first
whole-file open in this corpus — [Block 54] cited only `:142-234`):**
```java
public static void securityAuditCreated(BIOrionObject obj, String username, BSecurityAuditMode mode, OrionSession session) {
   String message = makeAuditMessage(obj, null, BOrionAuditType.created, session);
   if (mode.equals(BSecurityAuditMode.securityEventAndDatabaseRecord) || mode.equals(BSecurityAuditMode.databaseRecord)) {
      BOrionSecurityAudit secRec = makeSecurityAuditRecord(username, obj, session);
      secRec.setAuditType(BOrionAuditType.created);
      secRec.setMessage(message);
      session.insert(secRec);                                     // <- the database-record channel
   }
   if (mode.equals(BSecurityAuditMode.securityEventAndDatabaseRecord) || mode.equals(BSecurityAuditMode.securityEvent)) {
      SecurityAuditor securityAuditor = Nre.getSecurityAuditor();
      if (securityAuditor != null) securityAuditor.audit(makeSecurityAuditEvent("Added", username, message));  // <- the SHARED channel
   }
}
```
`[CERT]` `BOrionSecurityAudit.java:142-158` (`securityAuditCreated`, whole method); `securityAuditDeleted`
(`:159-175`) and `securityAuditModified` (`:176-197`) follow the identical two-branch shape, whole methods,
this session. **This settles B54-G5's "parallel vs. shared" framing precisely: it is BOTH, split by branch.**
The `securityEvent` half is NOT a third channel — it calls `Nre.getSecurityAuditor().audit(...)`, the EXACT
same `SecurityAuditor` singleton [Block 54] §54.2 already fully traced to `BSecurityAuditHistorySource`/
`$/SecurityHistory`/syslog. The `databaseRecord` half IS the genuinely separate, third channel: `session.insert
(secRec)` writes a `BOrionSecurityAudit` row through `OrionSession` — an interface (`OrionSession.java:1-60`,
read this session) that extends `Context` and exposes `getRdbmsContext(): RdbmsContext`,
`invokeDdl(DdlCommand)`, and imports `com.tridium.orion.sql.{BSqlUpdate,BatchStatement}` `[CERT]` — i.e. a
genuine SQL-RDBMS-backed persistence layer, structurally distinct from `BSecurityAuditHistorySource`'s ordinary
Niagara history/`BFileHistoryTable` mechanism [Block 54] §54.2 documented.

**The record schema and its self-exclusion from the general audit trail.** `BOrionSecurityAudit`'s own
`@NiagaraProperties` declare exactly `id` (int, `ID_KEY`), `timestamp` (`BAbsTime`), `userName` (String,
`indexed`+`width=64`), `objectTypeSpec` (`BTypeSpec`, the audited object's type), `objectDisplay` (String,
`width=512`, the object's display string), `auditType` (`BOrionAuditType`: `created`/`deleted`/`modified`/
`unspecified`), `message` (String, `width=512`, a pre-formatted diff description built by `makeAuditMessage()`
— which, for `modified`, reads the changed property's old/new value via `BObject.fw(703, ...)` and, per
`BOrionObject.isSensitiveProperty(property)`, either includes the actual old→new values or substitutes a
generic "has been changed" message `[CERT]` `BOrionSecurityAudit.java:205-221`) `[CERT]`
`BOrionSecurityAudit.java:16-70` (whole `@NiagaraProperties` block + generated accessors). Notably,
`BOrionSecurityAudit.isAuditable()` and `isSecurityAuditable()` both hardcode `return false` (`final`, whole
methods) `[CERT]` `BOrionSecurityAudit.java:237-244` — the audit-record TYPE ITSELF is explicitly excluded from
[Block 54] §54.2's `checkSecurityAudit()`/`BISecurityAuditable`-facet general-audit routing, an intentional
anti-recursion design (creating an audit record does not itself generate another audit event through the
generic component-mutation path).

**Is the database-record mode actually active by default?** `[CERT]`, no. `BSecurityAuditMode` (read whole,
49 lines) is a 3-valued frozen enum — `securityEvent` (0), `databaseRecord` (1),
`securityEventAndDatabaseRecord` (2) — with `public static final BSecurityAuditMode DEFAULT = securityEvent`
`[CERT]` `BSecurityAuditMode.java:12-27`. `BOrionService`'s own bajadoc confirms `securityAuditMode` is a
regular, documented, operator-configurable station property (`"Specifies whether security audits will be sent
to a history, or a database table."`, alongside a sibling `auditMode` property covering Orion's GENERAL
(non-security) audit trail the same way) `[CERT]` `BOrionService.bajadoc:24-40`. **Net finding**: by default,
Orion object mutations do NOT produce an RDBMS audit row — only the shared `SecurityAuditor` channel fires;
the RDBMS row is written only when an operator explicitly sets `securityAuditMode` to `databaseRecord` or
`securityEventAndDatabaseRecord` on the `BOrionService` instance. Retention/physical storage internals
(`BOrionDatabase`'s own implementation, table DDL, purge policy) were NOT opened this session — tracked as a
fresh child gap, **B69-G3**, §69.6.

## 69.5 — Self-verification

**Token check.** Every load-bearing `[CERT]` `file:line`/whole-file/grep-count citation above was read or
`grep`-run directly this session (not hand-recalled): `Bootstrap.java` (`:88,97,236-238`, targeted, past
[Block 65]'s prior citation of the same file), `Nre.java` (whole 1400-line file open — first whole-file open
of this file in the corpus; `:174-178,236-371,494-539,1234-1237,1331` individually re-confirmed),
`NiagaraDaemon.java` (whole-file `grep -c "nreMain"` = 0, `:1-40,119,185-238` re-read, 1641-line file length
confirmed via `wc -l`), `Station.java:735-760` (`nreMain` head, first open of this method in-corpus), niagarad
`module-info.java` (whole file, `requires`/`exports`/`opens` lists all read, not just the one line [Block 65]
cited), the 40-file `nreMain`-contract corpus census (`grep -rl`, each file individually re-`grep`-checked for
`"NiagaraDaemon"`, zero hits, loop run and its zero-output result observed this session), `SecurityUtil.java`
(`:229-232,322-355`, both methods whole, re-read past [Block 65]'s/[Block 8]'s prior citations),
`PermissionManager.java:40-139` (whole method + field header, wider range than either predecessor block cited),
`NiagaraPermission.java` (whole 41-line file, re-read), `BUserService.java:415-434` (re-read),
`BUserService.bajadoc:674-720` (first open of this specific `<method>` element), `BOrionSecurityAudit.java`
(whole 245-line file, first whole-file open in-corpus), `BSecurityAuditMode.java` (whole 49-line file, first
open), `OrionSession.java:1-60` (first open), `BOrionService.bajadoc:1-40` (first open). Four corpus-wide
`grep` censuses (`NiagaraDaemon`, `com.tridium.sys.station.Station`, `public static void nreMain(`,
`\.auditLoginAttempt\(`) each run as standalone whole-tree commands this session, their literal hit counts/
file lists quoted verbatim in §69.1/§69.3, not summarized or estimated.

**Marker tally — mechanized, literal `verify-block.sh` output** (run this session from
`/home/cristian/niagara5-research`):

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block69.md .
== verify-block: niagara5-block69.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 0)
   [CERT-live] 0
   [CERT] 51  (adj 46)
   [CERT-doc] 0
   [CERT-web] 1
   [CERT-a] 1  (adj 0)
   [INFER] 14  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/47 = 0.23
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BOrionSecurityAudit.java:142-158 / :16-70 / :205-221 / :237-244, BOrionService.bajadoc:1-40 / :24-40,
           BSecurityAuditMode.java:12-27, BUserService.bajadoc:674-720, BUserService.java:415-434,
           Bootstrap.java:88 / :97 / :232-234 / :236-238, Nre.java:174-178 / :361 / :494-539 / :1234-1237,
           OrionSession.java:1-60, PermissionManager.java:40-139, SecurityUtil.java:322-332 / :335-355,
           Station.java:735-760 / :742-756  (23 short-form citations — bare `file:line` body forms with a
           fully-pathed counterpart cited elsewhere in the block)
   ok      organized/baja/vineflower/com/tridium/sys/station/Station.java:735-760
           (range end verified; file has 885 lines)
   ok      organized/docDeveloper/vineflower/doc/baja/niagara/user/BUserService.bajadoc:674-720
           (range end verified; file has 1179 lines)
   ok      organized/docDeveloper/vineflower/doc/orion/com/tridium/orion/BOrionService.bajadoc:1-10
           (range end verified; file has 522 lines)
   resolved 3 of 26
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**Reading the ratio.** The raw `[CERT-hw]`(2)/`[CERT-web]`(1)/`[CERT-a]`(1) counts are entirely accounted for
by this block's own header-blockquote marker LEGEND (`` `[CERT-hw]` ``/`` `[CERT-web]` ``/`` `[CERT-a]` ``,
naming the canonical marker table) and this Self-verification section's own prose using those tokens by name
— the script's `(adj ...)` column correctly reduces all three to 0, matching this block making zero actual
claims at those levels (the same self-referential inflation [Block 54] §54.6/[Block 65] §65.4 both document).
The real evidence tally is **46 `[CERT]` against 11 `[INFER]`, adjusted ratio 0.23** (script-reported:
11/47 — the denominator folds in the 1 residual `[CERT-a]` from the `corpus-nav.py find` REMIT lookup, §69.2).
This is a `mixed` block: §69.1's evidence is dense (whole-method/whole-file reads of `Nre.java`/`Bootstrap.
java`/`NiagaraDaemon.java`/`Station.java`, none previously opened whole in this corpus, plus the 40-file
corpus-wide negative-existence census), so a ratio well below the ~0.5 exhaustion threshold is expected and
consistent with "evidence still available, not yet exhausted" — §69.1's own single load-bearing `[INFER]`
(the "separate native entry sequence" conclusion, explicitly hedged and given its own residual gap **B69-G1**)
is the one inferential step this block draws across its own dense `[CERT]` reads, the MIXED-block trigger
METHODOLOGY §11 names; §69.2's/§69.3's/§69.4's own `[INFER]`s are each similarly named and hedged in place
above, not free-standing speculation.

**Citation resolution.** `resolved 3 of 26` — 3 full-path (`organized/...`) citations resolve `ok`, all
range-verified against actual on-disk file lengths (`Station.java` 885 lines, `BUserService.bajadoc` 1179
lines, `BOrionService.bajadoc` 522 lines — the cited ranges all fall inside). The 23 `extern` rows are the SAME
citations in bare `file:line` short-form, used in body prose where a fully-pathed citation to the SAME file
already appears in the header-blockquote Sources list (METHODOLOGY §11's named "bare `:line` body + full
`filename:line` self-verify anchor" pair). This is the expected decompiled-tree signature (METHODOLOGY §11:
"DECOMPILED-TREE BLOCKS WILL SHOW ZERO OR PARTIAL RESOLVED CITATIONS — THIS IS EXPECTED"), matching
[Block 41]/[Block 44]/[Block 49]/[Block 54]/[Block 65]'s identical pattern on this corpus; the burden falls on
the Token check above, which independently confirms every cited file was opened and read this session.

**Artifacts.** This file (`/home/cristian/niagara5-research/niagara5-block69.md`) is the only artifact written
this session, per the caller's explicit single-file/read-only-elsewhere constraint — `CATALOG.md`/`INDEX.md`/
`RESEARCH-STATE.md` were **not** regenerated or hand-edited, matching every predecessor block's identical
disclosure on this corpus.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block; the one `corpus-nav.py find`
lookup (§69.2) is a local REMIT tool query, not a web source.

## 69.6 — Child gaps

- **B69-G1** (residual half of [Block 65]'s **B65-G1**) — Disassemble `niagarad.exe`'s own native launcher to
  identify the exact `JNI_CreateJavaVM`/`FindClass`/`CallStaticVoidMethod` (or equivalent) sequence that
  actually invokes `com.tridium.niagarad.NiagaraDaemon.Main(String[])`, confirming §69.1's `[INFER]` (that it
  is a SEPARATE native entry sequence from `Bootstrap.Main()`/`Nre.main()`/`Station.nreMain()`'s shared path)
  as `[CERT]`, and settling whether `-javaagent:nre.jar` is actually passed for this process (the original
  half of B65-G1's text). [Block 63]'s own `NreLauncherWin32::buildArgs`/`buildVMOptions` disassembly did not
  resolve this — it recovered the VM-argument FLAG content, not the entry-class/method resolution. Same
  native-binary-read limitation class as [Block 54]'s **B54-G1**/[Block 61]'s **B61-G1**/[Block 65]'s
  **B65-G4**; `blocked-on-source` for a decompiled-only session, `investigable` with `radare2`/native
  disassembly access to `niagarad.exe` (already extracted per [Block 63], five binaries copied this session's
  predecessor).
- **B69-G2** (residual half of **B54-G4**) — `BUserService.auditLoginAttempt`'s "documented public API for
  third-party callers, not dead code" reading (§69.3) cannot be fully confirmed without visibility into
  third-party/OEM module source outside this corpus's own extraction scope. `blocked-on-source` structurally
  (the corpus by construction holds only Tridium first-party modules); would need either a specific
  third-party module's decompiled source (if one becomes available) or a live station's method-invocation
  trace/breakpoint on this method during a custom-auth-scheme login to move past `[INFER]`.
- **B69-G3** — `BOrionDatabase`'s own physical storage implementation (only its consumer interface,
  `OrionSession`, was read this session, `:1-60`) — table DDL for `BOrionSecurityAudit` rows, retention/purge
  policy, and whether it shares the station's `db/` history storage or a genuinely separate RDBMS file/schema.
  `investigable` — file already present in-corpus, not opened this session.
- **[Block 65]'s own B65-G3** (not renamed, not touched this session) — `FilePermission`/
  `RuntimeExecPermission`/`NiagaraBasicPermission`'s `doIsGrantedTo(Module)` grant-matching bodies remain
  unopened; restated here only to avoid it being mistaken for closed by this block's B65-G1/B65-G2 work.
  `investigable`.

## 69.x — Connections

- **[Block 65]** — closes **B65-G1** (the priority gap, mislabeled "B65-G3" in the task prompt but B65-G1 in
  [Block 65]'s own file) to `[CERT]` for the Java-source half: `NiagaraDaemon.Main()` structurally cannot be
  reached via the exact call chain `Bootstrap.java:232-234`'s `permissionBridge` wiring sits inside, refining
  §65.3's "for any JVM process where `Main()` runs before (or instead of) `Bootstrap`'s assignment" framing
  toward "most likely never runs in that process at all." The observable consequence §65.3 already established
  (`permissionBridge` stays `null` for `niagarad`) is UNCHANGED. Also flags that [Block 65] §65.5 re-opened
  **B65-G2** without checking [Block 8] had already closed it — corrected at §69.2.
- **[Block 8]** — the actual prior closer of **B65-G2** (`isPrivileged`'s frame-classification rule and the
  module-set-AND enforcement it feeds). This block's §69.2 independently re-derives the same reading from a
  fresh direct read this session, corroborating rather than superseding [Block 8], and adds one clarifying
  mechanical detail (the bare-for-loop/no-per-iteration-catch propagation path that makes the AND semantics
  explicit) [Block 8]'s own prose did not spell out as a separate step.
- **[Block 63]/[Block 61]/[Block 57]** — REMIT only, the native-launcher-binary disassembly cluster. [Block 63]
  §63.1's `NreLauncherWin32::buildArgs`/`buildVMOptions` work is adjacent to but does not resolve **B69-G1**
  (VM-argument flag content vs. entry-class/method resolution are different questions); named explicitly in
  this block's Does-not-cover note and at **B69-G1** so the boundary is not silently assumed closed.
- **[Block 54]** — closes **B54-G4** (to the corpus's evidentiary limit, residual tracked as **B69-G2**) and
  **B54-G5** (Orion's first-party status and the database-record channel's exact mechanics, both opened by
  that block's own §54.7).
