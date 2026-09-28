# Block 29 — Tests on N5: JUnit4 to TestNG and running them (niagaraTest, test.exe, plain TestNG)

> Research of **whether ColdRoomPan-rt's 5 existing N4 JUnit4 test files can be ported to TestNG,
> compiled into a real N5 `moduleTest` jar, and actually RUN** — closing gaps **B16-G6** (port the 5
> JUnit4 files, scoped out of [Block 16]) and **B16-G1** (whether `niagaraTest` reaches TestNG execution
> on a REAL `bin/test.exe`, not just a missing-launcher wall). Covers: a reusable JUnit4→TestNG source
> mapping table + a paren/string-literal-aware Python port script (not a bare `sed`, because the
> `assertEquals`/`assertTrue`/`assertFalse` MESSAGE-ARGUMENT POSITION differs between the two
> frameworks and a naive prefix-only rename silently mis-orders or does not compile); applying it to all
> 5 files (117 `assert*` calls total, count-preserved, zero leftover `org.junit`); building
> `:ColdRoomPan-rt:moduleTestJar` with the resulting 6-class jar (5 ported + [Block 16]'s existing
> `ColdRoomControlN5Test`); re-attempting `niagaraTest` via `./gradlew` (reproduces [Block 16] §16.5.4's
> wall, now with a real, non-trivial test population instead of 1 trivial test); a NEW attempt this
> block adds that [Block 16] did not — invoking the REAL `bin/test.exe` directly via WSL→Windows
> interop (`wslpath -w`), both `-help` and with Gradle's own exact positional arguments recovered from
> `--info` logging — which decisively answers **half** of B16-G1 (native-launcher discovery is NOT the
> remaining blocker; a SYSTEM-WIDE LICENSE GATE is, and it is the SAME gate [Block 17] found blocking
> `n5mig.exe`/`station.exe`); and a fallback that needs no Niagara runtime at all — compiling +
> running the 5 ported files under plain `java -cp testng+jcommander+slf4j`, JDK 25, **51/51 PASS**,
> plus a mutation-kill (bite) proof that the harness is not vacuously green. Does NOT cover: obtaining a
> `tridium:nre` license entitlement to get past the wall on either `n5mig`/`station` ([Block 17]'s
> B17-G1) or `test.exe` (this block's own new B29-G2); porting CompPan or DashboardPan's tests (out of
> scope, same modules [Block 16]/[Block 17] left unbuilt); or the "TestNG Support in Niagara 5" document
> [Block 16]'s B16-G3 still could not locate.
>
> Subject version: **Niagara 5.0.0.28 beta** — same install [Block 16]/[Block 17] used:
> `/mnt/c/Program Files/Niagara/5.0.0.28` (read-only), `/mnt/c/ProgramData/Niagara/tridium/config/
> 5.0.0.28/modules` (read-only, **247 jars** this session — [Block 17] §17.6's timeline shows
> `ColdRoomPan-rt.jar`/`n5Hello.jar` were quarantined OUT of this install by a concurrent session before
> this block started; the 247 count was verified stable before AND after every build in this session,
> never mutated by this block). Gradle **9.2.1**, JDK `/home/linuxbrew/.linuxbrew/opt/openjdk@25`
> (OpenJDK 25.0.4.1). N4 test source read from
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`, commit
> **`a109249d98b795c934c71b2165af976dbc39716e`** (2026-09-05, clean working tree, `git status --short`
> confirmed both before AND after this session — the worktree was never written to) — the SAME worktree/
> commit [Block 16] read. PoC workspace: `/home/cristian/niagara5-research/poc/coldroompan-n5/`
> (existing, from [Block 16]; this block adds `srcTest/` content, `tools/port-junit4-to-testng.py`,
> `codegen-plaintestng/`, `logs/`).
>
> Sources:
> - The 5 real N4 JUnit4 files, read in full this session: `ColdRoomControlTest.java`,
>   `ColdRoomWritePathTest.java`, `ColdRoomControlDelayTest.java`, `ResistanceLockoutTest.java`,
>   `ColdRoomControlSequenceTest.java`, all in `Paccadia/ColdRoomPan/ColdRoomPan-rt/srcTest/test/com/
>   angeles/ColdRoomPan/` in the `main-a109249` worktree (117 total `assert*` calls, cross-counted by
>   `grep`).
> - `ColdRoomPan-rt/src/com/angeles/ColdRoomPan/ColdRoomControl.java` in the PoC (identical to the N4
>   source per [Block 16]'s mechanical rename-only port) — the production class under test, read for its
>   exact package-private static signatures (`decideCall`, `applyHoa`, `resistanceCommand`, `freezeTrip`,
>   `positiveDelayMs`, `eligibleForDefrost`, `stopDelayShouldStopFan`, `intervalDelayMs`).
> - [Block 16] `niagara5-block16.md` §16.5.2-16.5.4 (the prior JUnit4-does-not-compile and
>   native-launcher findings this block extends), §16.6 (`ColdRoomControlN5Test`, the one existing
>   TestNG file, kept in place and rebuilt alongside the 5 new ones).
> - [Block 17] `niagara5-block17.md` §17.2 (the `tridium:nre` `FeatureNotLicensedException` wall this
>   block's §29.6 independently reproduces against a DIFFERENT binary, `test.exe`, not `n5mig.exe`/
>   `station.exe`).
> - `org.testng:testng:7.12.0` (`~/.gradle/caches/modules-2/files-2.1/org.testng/testng/7.12.0/
>   55b39526598d8eb2e0e75bffbbd4b683adb85dcc/testng-7.12.0.jar`), `org.jcommander:jcommander:1.83`, and
>   `org.slf4j:slf4j-api:2.0.16` — all resolved from the LOCAL Gradle module cache this session (not
>   downloaded fresh; pre-existing from [Block 16]'s own dependency resolution), used for the §29.7
>   no-Niagara-runtime fallback run.
> - This session's own command output: every `./gradlew`, `test.exe` (WSL interop), `javac`, `java
>   -cp ... org.testng.TestNG` invocation, preserved under `poc/coldroompan-n5/logs/` and
>   `poc/coldroompan-n5/codegen-plaintestng/{compile,run,run-mutated}.log` (gitignored per task scope,
>   same `poc/coldroompan-n5/` blanket rule [Block 16] already relies on).
>
> Method: mechanical source-to-source port via a purpose-written paren/string-aware Python script
> (`poc/coldroompan-n5/tools/port-junit4-to-testng.py`), applied to real N4 JUnit4 source, validated by
> (a) an automated `assert*`-call-count-preserved check per file, (b) a manual grep sweep for zero
> leftover bare (un-prefixed) `assert*`/`org.junit` tokens, (c) a real `javac`+`./gradlew` compile, and
> (d) two independent RUN attempts — the real Niagara `niagaraTest`/`test.exe` path (blocked, §29.5-6)
> and a Niagara-runtime-free plain-TestNG path (unblocked, §29.7) — plus one deliberate mutation-kill
> (bite) proof that the unblocked path is not vacuously green. Markers: `[CERT-hw]` observed command/
> build/run output this session (the dominant marker, same convention [Block 16]/[Block 17]
> established) · `[CERT]` a source file read directly · `[INFER]` deduction.
>
> N5 build-toolchain layer, §19 requires-execution phase. Connects [Block 16] (closes its scoped-out
> B16-G6, re-answers its still-open B16-G1 with a decisive new datum), [Block 17] (the identical
> `tridium:nre` license wall reproduced against a second, different binary — `test.exe` instead of
> `n5mig.exe`/`station.exe` — strengthening §17.2's "no headless/server tool runs on this unlicensed
> install" generalization from n=3 binaries to n=4).
>
> **Type:** standard (evidence, requires-execution/§19 build-PoC)
>
> **Breakthrough:** invoking the REAL Windows `bin/test.exe` directly via WSL→Windows interop — bypassing
> Gradle's `Exec` task entirely — proves the remaining blocker named by [Block 16] B16-G1 is **not**
> "no Linux launcher exists" (true, but not the operative constraint once the real binary IS reachable
> via interop) but the **exact same system-wide `tridium:nre` `FeatureNotLicensedException`** [Block 17]
> §17.2 already found blocking `n5mig.exe`/`station.exe` on this install. A single license fix
> ([Block 17]'s B17-G1) would very likely unblock BOTH `n5mig` migration AND `niagaraTest` execution at
> once — previously two separately-tracked open gaps that this block's evidence now ties to one root
> cause. Independently, the plain-TestNG fallback (§29.7) gives FULL, licence-independent behavioral
> certainty for all 5 ported files today: 51/51 pass, with a mutation-kill proof the pass is not
> vacuous — the corpus does not have to wait on B29-G2 to trust these 5 tests' logic.

---

## 29.1 — JUnit4→TestNG mapping table `[CERT-hw]`

Built from the real 117-call census across the 5 files (`grep -oE 'assert[A-Za-z]*\(' *.java | wc -l`
run in the N4 worktree this session) and confirmed against actual `javac`/TestNG behavior, not just
API docs:

| JUnit4 (N4) | TestNG (N5) | Gotcha | Present in this corpus? |
|---|---|---|---|
| `import org.junit.Test;` | `import org.testng.annotations.Test;` | package rename only | all 5 files |
| `import static org.junit.Assert.*;` | `import org.testng.Assert;` | static import → qualified class; every call site needs an `Assert.` prefix | all 5 files |
| `assertTrue(cond)` / `assertFalse(cond)` | `Assert.assertTrue(cond)` / `Assert.assertFalse(cond)` | prefix only, no reorder | 40 of 98 calls (no message) |
| `assertTrue(String msg, boolean cond)` | `Assert.assertTrue(boolean cond, String msg)` | **message moves FIRST→LAST.** TestNG's `Assert` class has **no** `(String, boolean)` overload at all — a bare `Assert.` prefix with no reorder is a **compile error**, not a behavior change, confirmed by `javac` this session (§29.3) | 58 of 98 calls (message-bearing) |
| `assertEquals(expected, actual)` | `Assert.assertEquals(actual, expected)` | **expected/actual SWAP.** Functionally symmetric for a pass/fail equality check, but wrong for what TestNG reports as "expected" vs "actual" on a failure | 14 of 19 calls |
| `assertEquals(String msg, expected, actual)` | `Assert.assertEquals(actual, expected, msg)` | swap **and** message FIRST→LAST, in the SAME call | 5 of 19 calls |
| `assertNull(msg, obj)` / `assertNotNull(msg, obj)` | `Assert.assertNull(obj, msg)` / `Assert.assertNotNull(obj, msg)` | message FIRST→LAST (same shape as `assertTrue`/`assertFalse`) | **0** — not present in this corpus; script handles it, untested here |
| `assertSame(msg, expected, actual)` / `assertNotSame(...)` | `Assert.assertSame(actual, expected, msg)` / `assertNotSame(...)` | same swap+reorder as `assertEquals` | **0** — not present; script handles it, untested here |
| `assertArrayEquals(expected, actual)` | `Assert.assertEquals(actualArray, expectedArray)` — **same method name**, no `assertArrayEquals` exists in TestNG's `Assert` class at all | name change, not just reorder — the script does NOT implement this case (documented limitation, **B29-G3**) | **0** — not present in this corpus |
| test class extends nothing special | may extend `niagara.test.BTestNg` (a `BComponent`, `@NiagaraType`) for classloader-safe reflection over `BObject`s ([Block 16] §16.6) | **only needed when the test touches Baja/`BObject` reflection.** All 5 ported files are PURE-Java seam tests against `ColdRoomPan-rt`'s package-private static methods — their own N4 javadoc says so explicitly ("ColdRoomPan-rt has ZERO Baja types" / "runs in plain JUnit... no station"). This block deliberately does **NOT** make them extend `BTestNg` — see §29.3's reasoning | n/a — a design choice, not a mechanical rename |

**Census cross-check** `[CERT-hw]`: 98 `assertTrue`/`assertFalse` + 19 `assertEquals` = **117**, matching
the file-level `grep -oE 'assert[A-Za-z]*\('` total exactly (`ColdRoomControlTest.java` 34,
`ColdRoomWritePathTest.java` 39, `ColdRoomControlDelayTest.java` 13, `ResistanceLockoutTest.java` 16,
`ColdRoomControlSequenceTest.java` 15 — sums to 117). Of the 98 `assertTrue`/`assertFalse` calls, 58
(59%) carry a message and therefore hit the reorder gotcha — this is the DOMINANT gotcha by call count
in this corpus, not the `assertEquals` one, contrary to what a reviewer might expect from TestNG's own
documentation emphasis on the `assertEquals` argument-order difference.

## 29.2 — The recipe: a paren/string-aware port script, not `sed` `[CERT-hw]`

`poc/coldroompan-n5/tools/port-junit4-to-testng.py` (full source in the PoC tree). Why not a one-line
`sed 's/assertEquals(/Assert.assertEquals(/'`-style substitution: a regex alone cannot correctly REORDER
arguments when one of them is itself a nested call with its own commas —
`assertEquals(interval, delay(interval, Long.MIN_VALUE, NOW))` has 2 TOP-LEVEL arguments (`interval` and
the whole `delay(...)` call), not 4. The script implements:

1. `split_top_level_args(s)` — a hand-rolled comma splitter that tracks `()[]{}`  nesting depth and
   `"…"`/`'…'` string/char literal boundaries (with backslash-escape handling), so a nested call's
   internal commas never leak into the top-level split.
2. `find_matching_paren(s, open_idx)` — the same string/escape-aware scan to find an `assertX(`'s real
   closing `)`, so the extracted argument-list substring is exactly right even across multi-line calls.
3. Two reorder functions per the mapping table: `reorder_message_last_args` (assertTrue/False/Null/
   NotNull: message FIRST→LAST) and `reorder_assert_equals_args` (assertEquals/Same/NotSame:
   expected/actual SWAP, message FIRST→LAST when present).
4. A single pass over the whole file: for every `assert*(` call found (paren-matched, not consumed by a
   prior replacement span), extract → reorder-per-kind → reassemble with an explicit `Assert.` prefix.

**Self-check built into the script**: it prints `<N before> assert* calls in, <M after> out` and flags
a MISMATCH — this caught nothing wrong this session (all 5 files: count preserved, §29.3), but exists so
a future reuse of this script on a DIFFERENT test file cannot silently drop or duplicate an assertion.

Usage: `python3 tools/port-junit4-to-testng.py <src.java> <dest.java>`.

## 29.3 — Port results: all 5 files, count-preserved, zero leftovers `[CERT-hw]`

| File | `assert*` in | `assert*` out | Bare (un-prefixed) leftover? | `org.junit` leftover? |
|---|---|---|---|---|
| `ColdRoomControlTest.java` | 34 | 34 | none | none |
| `ColdRoomWritePathTest.java` | 39 | 39 | none | none |
| `ColdRoomControlDelayTest.java` | 13 | 13 | none | none |
| `ResistanceLockoutTest.java` | 16 | 16 | none | none |
| `ColdRoomControlSequenceTest.java` | 15 | 15 | none | none |
| **Total** | **117** | **117** | **0** | **0** |

`[CERT-hw]` — the script's own printed self-check (§29.2 point 4) for all 5 files, PLUS an independent
manual `grep -n "[^.]assert(True|False|Equals|Null|NotNull|Same|NotSame)(" <file> | grep -v "Assert\."`
sweep (confirms zero bare calls) and `grep -n "org.junit" <file>` (confirms zero leftover imports), both
run against the ported files this session.

**Reorder-correctness spot checks** `[CERT-hw]` (full call-by-call read of the diff, not just the count):
- `assertEquals("at-boundary overdue must return 1, not 0 (Niagara rejects delay <= 0)", 1L,
  delay(interval, last, NOW));` → `Assert.assertEquals(delay(interval, last, NOW), 1L, "at-boundary
  overdue must return 1, not 0 (Niagara rejects delay <= 0)");` — expected/actual swapped AND message
  moved to last position, correctly, across a NESTED call argument.
- `assertTrue("HAND → ON even when auto is false", hoa(ColdRoomControl.HOA_HAND, false, false));` →
  `Assert.assertTrue(hoa(ColdRoomControl.HOA_HAND, false, false), "HAND → ON even when auto is false");`
  — message moved to last position; this is the gotcha a naive `Assert.` prefix-only rename would have
  left as a COMPILE ERROR (§29.4 confirms zero such errors after the reorder).
- A final grep across all 5 ported files for `Assert\.assert(True|False|Equals)\(\s*"` (i.e. a quoted
  string IMMEDIATELY after the opening paren — the signature of a still-wrong message-first call)
  returned **zero matches** `[CERT-hw]`.

**Design choice: none of the 5 ported files extend `niagara.test.BTestNg`.** All 5 exercise ONLY
`ColdRoomControl`'s package-private static methods (`decideCall`, `applyHoa`, `resistanceCommand`,
`freezeTrip`, `positiveDelayMs`, `eligibleForDefrost`, `stopDelayShouldStopFan`, `intervalDelayMs`) —
zero `BObject`/`BComponent` reflection, matching the N4 files' own javadoc claim verbatim ("ColdRoomPan-
rt has ZERO Baja types" / W25's own note that its ONE genuinely stateful case "requires a Baja/rt-
lifecycle seam ... cannot be exercised in plain JUnit without the station" and is deliberately left as a
documentation-only test). [Block 16]'s existing `ColdRoomControlN5Test` DOES extend `BTestNg` (kept
unchanged, rebuilt alongside these 5) — this block does not second-guess that choice for [Block 16]'s
own file, but does not impose it here either, since `BTestNg`'s own javadoc-documented reason
(`PA.invokeMethod` needing `ModuleClassLoader` for `BObject` reflection, [Block 16] §16.6) does not
apply to any of these 5 pure-logic files. Whether `niagaraTest`'s real TestNG runner REQUIRES every
discovered class to extend `BTestNg` regardless of whether it touches Baja types is untested — same
open question as B16-G1, folded into **B29-G4** below.

## 29.4 — Build: `moduleTestJar` with all 6 test classes `[CERT-hw]`

`ls .../modules | wc -l` = **247** before this block's first command; re-checked after EVERY build
below; never changed. `git -C <n4-worktree> status --short` confirmed clean before and after.

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew :ColdRoomPan-rt:moduleTestJar` (default `JAVA_HOME`, resolves to Homebrew JDK 21) | **FAILED** — `Could not resolve com.tridium.tools:settings:5.0.9.8.14 ... Dependency requires at least JVM runtime version 25. This build uses a Java 21 JVM.` — a settings-plugin-resolution failure, not a compile error; same JDK-25-toolchain requirement [Block 16]/[Block 9] already established, re-confirmed here as a distinct failure MODE (wrong-JVM plugin resolution) from a compile failure |
| 2 | `JAVA_HOME=.../openjdk@25 ./gradlew :ColdRoomPan-rt:moduleTestJar` | **BUILD SUCCESSFUL** — `compileModuleTestJava` ran (not UP-TO-DATE — real recompile with the 5 new files), `moduleTestClasses`→`writeTestModuleXml`→`moduleTestJar` all completed; the produced `ColdRoomPan-rt-module-test.jar` has all **6** expected `.class` files (5 new + `ColdRoomControlN5Test` — confirmed by `unzip -l`, §29.4.1 below) |

**29.4.1 — A benign, unexplained anomaly in `compileModuleTestJava`'s own output, not a real failure**

> **Correction (added by [Block 89], §14 cross-block).** The `[INFER]` below ("no `module-info.class`") is
> wrong. [Block 89] traced JDK 25 javac source: the error fires when a jar's `Automatic-Module-Name` manifest
> header fails `isModuleName()` validation. The PoC jar's header `com.angeles.ColdRoomPan-rtTest` contains a
> hyphen, which is invalid. Why the task still succeeds is child gap B89-G1.
`[CERT-hw]`: attempt 2's console output for that task printed
`error: cannot determine module name for /home/cristian/niagara5-research/poc/coldroompan-n5/.n5config/
modules/ColdRoomPan-rtTest.jar` followed by a bare `1 error` line — yet the task did NOT fail (no
`FAILED` marker, the overall build reported `BUILD SUCCESSFUL`, and all 6 `.class` files compiled and
were packaged correctly, byte-identical entry names to the ported source set). `[INFER]`: the message is
javac's own module-path resolver probing `ColdRoomPan-rtTest.jar` — the SAME jar this exact task is in
the process of writing, sitting on the module path as a self-referential artifact from a prior run — and
finding it carries no `module-info.class` ([Block 16] §16.7 already established the moduleTest jar is
NOT its own JPMS module), which the resolver logs as an "error" without actually treating it as one for
this task's own compilation unit. Not independently traced into the plugin's own source this session —
named as **B29-G5**.

**`ColdRoomPan-rt-module-test.jar` entries after attempt 2** `[CERT-hw]` (`unzip -l`, this session): 14
total entries — the same `META-INF/{MANIFEST.MF,NIAGARA4.SF,NIAGARA4.RSA,module.xml}` shape [Block 16]
§16.7 described, plus **6** `.class` files under `com/angeles/ColdRoomPan/`: `ColdRoomControlDelayTest`,
`ColdRoomControlN5Test`, `ColdRoomControlSequenceTest`, `ColdRoomControlTest`, `ColdRoomWritePathTest`,
`ResistanceLockoutTest` — matching the `.n5config/modules/ColdRoomPan-rtTest.jar` mirror copy
byte-for-byte (both `unzip -l` listings identical).

## 29.5 — `niagaraTest` via `./gradlew`: reproduces [Block 16]'s wall with a real test population `[CERT-hw]`

| # | Command | Result |
|---|---|---|
| 3 | `./gradlew :ColdRoomPan-rt:niagaraTest --stacktrace` | **FAILED** — `Execution failed for task ':ColdRoomPan-rt:niagaraTest'. > A problem occurred starting process 'command '/mnt/c/Program Files/Niagara/5.0.0.28/bin/test'' ... Caused by: java.io.IOException: Cannot run program "/mnt/c/Program Files/Niagara/5.0.0.28/bin/test" ... Exec failed, error: 2 (No such file or directory)` |
| 4 | `./gradlew :ColdRoomPan-rt:niagaraTest --info` (diagnostic — to recover the exact command line Gradle constructs) | reveals: `Command: /mnt/c/Program Files/Niagara/5.0.0.28/bin/test ColdRoomPan -output:<build/reports/ColdRoomPan-rt> -@javaagent:<...jacocoagent.jar>=destfile=build/jacoco/niagaraTest.exec,... -@Djacoco.reportDir=... -@Djacoco.reportName=... -@Djacoco.agentJarPath=...` — the FIRST positional argument is `ColdRoomPan` (the module's `moduleName=` attribute per [Block 17] §17.5, **not** `ColdRoomPan-rt`), confirming [Block 17]'s registry-resolution mechanism is also what `niagaraTest`'s own task uses to address the module under test |

This is IDENTICAL in kind to [Block 16] §16.5.4's finding — extensionless `bin/test` does not exist,
only `bin/test.exe` — now independently re-confirmed with **6** real TestNG classes packaged (vs.
[Block 16]'s 1 trivial test), ruling out "maybe it was a task-graph/zero-sources fluke" as an explanation
(the same wall [Block 9]'s zero-source run could not distinguish from a SKIPPED task — [Block 16]
§16.5.4 already made this point once; this attempt reconfirms it holds with real content in the jar,
not just an empty one).

## 29.6 — NEW this block: `test.exe` invoked directly via WSL→Windows interop — same wall as [Block 17] `[CERT-hw]`

[Block 16] stopped at the Gradle `Exec`-task IOException (§29.5) and inferred a "Windows-only native
launcher" gap (B16-G1) without ever reaching the real binary. This block goes one step further: `bin/
test.exe` genuinely EXISTS (`ls -la` confirms, executable bit set) and IS reachable from WSL via
`wslpath -w` path translation — so it was invoked DIRECTLY, bypassing Gradle's `Exec` task entirely.

| # | Command | Exit | Result |
|---|---|---|---|
| 5 | `"/mnt/c/Program Files/Niagara/5.0.0.28/bin/test.exe" -help` (direct WSL→Windows interop) | **253** | Boots the registry (logs `sys.registry Up-to-date`, `sys.module Core ModuleLayer defined`), THEN: `GRAVE [sys.license] Could not determine brand` → `GRAVE [sys] Cannot boot` → `niagara.license.FeatureNotLicensedException: tridium:nre` at `NLicenseManager.checkFeature` ← `Nre.runClass` ← `Nre.main` ← `Nre.bootstrap` ← `Bootstrap.Main` |
| 6 | `"/mnt/c/.../bin/test.exe" ColdRoomPan "-output:<wslpath -w of build/reports/...>"` (Gradle's own recovered positional args, §29.5 attempt 4, run manually) | **253** | **IDENTICAL** stack trace, byte-for-byte the same exception chain as attempt 5 |

**Full logs preserved**: `poc/coldroompan-n5/logs/test-exe-help.log`, `logs/test-exe-manual-run.log`.

**This is the decisive finding of this block.** The binary EXISTS, IS reachable from WSL via interop,
DOES start (the registry boots, module layer resolves — real progress well past "file not found"), and
THEN hits the EXACT SAME `tridium:nre` `FeatureNotLicensedException` `[Block 17]` §17.2 already found
blocking `n5mig.exe -help`/`-premigrate`/`-o` AND `station.exe -help` on this SAME install — same
exception class, same `checkFeature`→`Nre.runClass`→`Nre.main`→`Nre.bootstrap`→`Bootstrap.Main` frame
chain, same exit code 253. `[Block 17]`'s own diagnosis ("this local N5 5.0.0.28 Beta install has NO
valid license entitling the `tridium:nre` feature required to run ANY headless/server-side Niagara
tool") now has a 4th confirming data point (`n5mig.exe`, `station.exe`, and now `test.exe`, vs. only
`wb.exe`/`-version`/`-help`-on-text-only-paths succeeding, per [Block 17] §17.2's own control pair).
**B16-G1 is therefore NOT "does a Windows Niagara install run niagaraTest" (open, requires a Windows
host) — it NARROWS to "does a LICENSED Niagara install run niagaraTest" (the SAME open question as
[Block 17]'s B17-G1), regardless of host OS.** This block's own environment (Linux/WSL, via interop)
already reaches the real binary; a Windows host would very likely hit the identical wall on this SAME
unlicensed install, and a licensed install would very likely unblock BOTH `n5mig` and `niagaraTest` at
once. Neither half is independently confirmed this session — named as **B29-G2** below, explicitly
merging with (not duplicating) [Block 17]'s B17-G1.

**One minor observed-but-inconsequential artifact**: this session's `wslpath -w` output for a LONG
`build/reports/...` path did not print cleanly in the captured shell transcript (a UNC-style `\\wsl.
localhost\...` prefix appears truncated/mis-rendered — a terminal/encoding display quirk, not a
functional failure, since the license wall fires during BOOT, before `-output:<path>` is ever parsed by
the `Migrate`/`Station`-equivalent test-runner class). Not investigated further — cosmetic, zero
consequence for this block's conclusion.

## 29.7 — Fallback: plain TestNG on JDK 25, NO Niagara runtime — 51/51 PASS `[CERT-hw]`

**Explicitly labeled: this is NOT a Niagara runtime test.** It proves the 5 ported files' LOGIC and
their TestNG-annotation CORRECTNESS independent of `niagaraTest`/`bin/test.exe`/any Niagara boot — the
exact `[Block 19 methodology]` "scratchpad PoC proving control-logic claims" pattern (a pure-Java PoC,
no live system needed, oracle = the PoC's own test output).

**Setup** `[CERT-hw]`: `poc/coldroompan-n5/codegen-plaintestng/src/` holds a COPY of `ColdRoomControl.
java` (unmodified, zero Baja types per its own javadoc) plus the 5 ported test files. Dependencies
resolved from the LOCAL Gradle module cache (already present from [Block 16]'s own build, not
freshly downloaded this session): `testng-7.12.0.jar`, `jcommander-1.83.jar` (TestNG's CLI arg parser —
required; a first attempt without it failed `NoClassDefFoundError: com/beust/jcommander/
ParameterException`), `slf4j-api-2.0.16.jar` (TestNG's logging facade — required; a second attempt
without it failed `NoClassDefFoundError: org/slf4j/LoggerFactory`). Both missing-dependency failures are
themselves `[CERT-hw]` evidence, preserved in the attempt log below.

| # | Command | Result |
|---|---|---|
| 7 | `javac -cp testng-7.12.0.jar -d build $(find src -name "*.java")` (JDK 25, `ColdRoomControl.java` + 5 ported test files, **zero Niagara jars on the classpath**) | **0 compile errors** — direct confirmation the reordered `assert*` calls (§29.3) are not just count-correct but genuinely COMPILE against TestNG's real `Assert` API, closing the risk named in the mapping table's `assertTrue`/`assertFalse` message-reorder row |
| — | `java -cp testng+jcommander -cp build org.testng.TestNG -testclass <5 classes>` | **FAILED** — `NoClassDefFoundError: com/beust/jcommander/ParameterException` |
| — | + `jcommander-1.83.jar` on classpath | **FAILED** — `NoClassDefFoundError: org/slf4j/LoggerFactory` |
| 8 | + `slf4j-api-2.0.16.jar` on classpath, `java -cp <4 jars>:build org.testng.TestNG -testclass com.angeles.ColdRoomPan.{ColdRoomControlTest,ColdRoomWritePathTest,ColdRoomControlDelayTest,ResistanceLockoutTest,ColdRoomControlSequenceTest} -d codegen-plaintestng/report` | **BUILD via TestNG CLI succeeded — exit 0.** `Total tests run: 51, Passes: 51, Failures: 0, Skips: 0` |

**Per-class breakdown** `[CERT-hw]` (parsed from `testng-results.xml` this session, cross-checked against
a `grep -c "@Test"` count per source file — both agree exactly):

| Class | `@Test` methods | Ran | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| `ColdRoomControlTest` | 22 | 22 | 22 | 0 | 0 |
| `ColdRoomWritePathTest` | 8 | 8 | 8 | 0 | 0 |
| `ColdRoomControlDelayTest` | 11 | 11 | 11 | 0 | 0 |
| `ResistanceLockoutTest` | 3 | 3 | 3 | 0 | 0 |
| `ColdRoomControlSequenceTest` | 7 | 7 | 7 | 0 | 0 |
| **Total** | **51** | **51** | **51** | **0** | **0** |

`22+8+11+3+7 = 51` matches the TestNG suite total exactly — no test silently skipped or double-counted.

**29.7.1 — Bite-proof: the 51/51 is not vacuously green** `[CERT-hw]`. Per the methodology's "prove a
guard by breaking it" discipline (§11b) and the §11a "NULL-OR-NEGATIVE METRIC: probe against a
known-positive case" heuristic applied in reverse (probe the harness against a KNOWN-NEGATIVE case): a
single-line mutation was applied to the SCRATCH COPY (`codegen-plaintestng/src/...ColdRoomControl.java`
— never the module's real `src/`, confirmed by `diff` after revert, below) —

```diff
- return ms >= 1L ? ms : 1L;
+ return ms; // MUTATED (B29 bite-proof — floor removed)
```

— recompiled (`javac`, attempt 9), rerun (attempt 10): **`Total tests run: 51, Passes: 48, Failures: 3,
Skips: 0`**, exit code **1**. The 3 failures, read from `testng-results.xml`, are EXACTLY the 3 methods
that exercise `positiveDelayMs`'s floor directly or via `intervalDelayMs`'s overdue branch —
`w6_intervalWriteMidCycleOverdue` (`ColdRoomWritePathTest`), `positiveDelayMs_negative_returnsOne` and
`positiveDelayMs_zero_returnsOne` (`ColdRoomControlDelayTest`) — no unrelated test flipped, confirming
the harness's pass/fail signal is load-bearing, not an artifact of the runner or classpath. The mutation
was then reverted; `diff /tmp/ColdRoomControl.java.orig ColdRoomPan-rt/src/com/angeles/ColdRoomPan/
ColdRoomControl.java` (the ORIGINAL scratch copy vs. the untouched module source) returned **zero
differences**, confirming the module's real `src/` was never touched by this mutation exercise (it only
ever existed in `codegen-plaintestng/src/`, a separate copy). `[CERT-hw]` (`testng-results.xml` parsed
via `python3 xml.etree`, this session; `diff` output, this session).

| # | Command | Result |
|---|---|---|
| 9 | `javac -cp testng-7.12.0.jar -d build-mutated $(find src -name "*.java")` (with the 1-line mutation applied) | 0 compile errors (mutation is still valid Java) |
| 10 | `java -cp <4 jars>:build-mutated org.testng.TestNG -testclass <5 classes>` | exit **1** — `Total tests run: 51, Passes: 48, Failures: 3, Skips: 0` — exactly the 3 methods that exercise the mutated branch |
| — | mutation reverted; `diff` against the never-touched module `src/` | **zero differences** — module source confirmed untouched |

10 real command attempts total this block (well under any budget cap), plus the diagnostic `--info` run
and various `grep`/`unzip`/`diff` checks not counted above.

## 29.8 — Self-verify

This is a **build/PoC (§19) block** — its `[CERT-hw]` claims are live command output captured this
session, matching [Block 16]/[Block 17]'s established convention for this block type.

- **Reproducibility check** — attempt 2 (`moduleTestJar`) and the §29.4.1 anomaly were each independently
  re-observed via a second `unzip -l` read of both the module's own `build/libs/` jar AND its `.n5config/
  modules/` mirror copy (byte-identical entry lists, both listed this session).
- **Token check** — every quoted error/output string in this block (`Dependency requires at least JVM
  runtime version 25`; `cannot determine module name for ... ColdRoomPan-rtTest.jar`; the
  `IOException: Cannot run program ".../bin/test"`; the FULL `tridium:nre` `FeatureNotLicensedException`
  stack for BOTH `test.exe` attempts; `Total tests run: 51, Passes: 51/48, Failures: 0/3, Skips: 0`) was
  copied verbatim from this session's captured command output/log files, not paraphrased —
  **≈12 distinct load-bearing tokens**, all mechanically sourced from `poc/coldroompan-n5/logs/*.log`
  and `poc/coldroompan-n5/codegen-plaintestng/{compile,run,run-mutated}.log` plus this session's own
  terminal capture.
- **Marker tally** — `verify-block.sh` was run this session (output below); this block otherwise makes
  essentially zero `[INFER]` claims of consequence — the one interpretive step (§29.6's "very likely
  unblocks both" framing) is explicitly hedged as `[INFER]` and separated from the `[CERT-hw]` observed
  exception chain it is built on:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block29.md .
== verify-block: niagara5-block29.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 21  (adj 20)
   [CERT-live] 0
   [CERT] 1  (adj 0)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 5  (adj 4)
-- ratio -- [INFER]/[CERT*] = 4/20 = 0.20
-- [CERT] file:line citation resolution --
   WARN    [CERT] markers present (20) but ZERO file:line citations resolved — the citation gate
   checked nothing and exits 0 silently. Expected for synthesis / REMITTANCE / [CERT-live]-only or
   [CERT-doc]-only blocks (check your block-type declaration); otherwise add file:line citations or
   re-check the citation format.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

  `[INFER]`/`[CERT*]` ratio 0.20 — low, consistent with a §19 build/PoC block whose claims are almost
  entirely direct `[CERT-hw]` command output (same as [Block 16] at 0.22-0.24 and lower than [Block 17]'s
  0.25-0.53 mixed-type ratio); this block's handful of `[INFER]` claims are explicitly bounded (§29.4.1's
  plugin-internals guess, §29.6's "very likely unblocks both" synthesis, B29-G2/G5/G6's open framing).
  The **ZERO resolved `[CERT]` file:line citations** WARN is EXPECTED here, same convention [Block 16]
  §16.9/[Block 17]'s self-verification already declared: every `[CERT]`/`[CERT-hw]` citation in this
  block points into `poc/coldroompan-n5/` (this corpus's own gitignored PoC tree, never committed, so
  `verify-block.sh` cannot resolve a path it will never see under version control) or into the N4
  worktree at `/home/cristian/modulos_niagara_n4/...` (external to this corpus entirely) — both `extern`
  to the mechanized resolver by construction, not a citation-quality defect. The burden is carried by the
  inline token-check in this section, not by the mechanized resolver, exactly as [Block 16]/[Block 17]
  already established for this block type.

- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block29.md`; the
  updated PoC tree exists at `/home/cristian/niagara5-research/poc/coldroompan-n5/` (new: `srcTest/`'s 5
  ported files, `tools/port-junit4-to-testng.py`, `codegen-plaintestng/`, `logs/`). Per task scope
  (single-block deliverable, `poc/coldroompan-n5/` blanket-gitignored), `CATALOG.md`/`INDEX.md`/
  `RESEARCH-STATE.md` were **not** regenerated this session, matching [Block 16]/[Block 17]'s own
  disclosed choice.
- **MCP-doc snapshots** — N/A, no MCP/context7 web citation used.
- **`/mnt/c` module-count guard** — `ls /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules | wc
  -l` returned **247** before this block's first command and was re-checked after EVERY `./gradlew`
  invocation and after the final `test.exe` interop attempts; it never changed. `git -C
  <main-a109249-worktree> status --short` returned empty before and after. No write to `/mnt/c` and no
  modification to the client's N4 source occurred this session.

## 29.9 — Child gaps

- **B29-G2 (requires-execution, license — merges with B17-G1, narrows B16-G1)** — obtaining a validly
  licensed N5 5.0.0.28+ install (entitling `tridium:nre`) to determine whether `test.exe`/`niagaraTest`
  actually discovers and runs the 6 TestNG classes once past the boot-time license gate. This is now the
  SAME open precondition as [Block 17]'s B17-G1 for `n5mig`; a single license fix would very likely
  resolve both simultaneously (`[INFER]`, not independently confirmed — no licensed install was
  available this session).
- **B29-G3** — `assertArrayEquals` JUnit4→TestNG mapping (a NAME change, not just an argument reorder —
  TestNG's `Assert` class has no `assertArrayEquals` method at all, only overloaded `assertEquals` for
  arrays) is documented in the mapping table (§29.1) but NOT implemented in `port-junit4-to-testng.py`
  — zero uses in this corpus meant it was never exercised or needed; a future reuse of this script on a
  test file that DOES use `assertArrayEquals` will need this case added first.
- **B29-G4** — whether `niagaraTest`'s real TestNG runner (once B29-G2 is resolved) requires every
  discovered test class to extend `niagara.test.BTestNg` regardless of whether it touches Baja/
  `BObject` types, or accepts a plain TestNG class with no special base — this block's 5 ported files
  deliberately do NOT extend `BTestNg` (§29.3's reasoning), and that choice is untested against the real
  runner.
- **B29-G5** — the `compileModuleTestJava` task's benign `"error: cannot determine module name for ...
  ColdRoomPan-rtTest.jar" / "1 error"` console output (§29.4.1) that does NOT fail the build is an
  unexplained (though functionally inconsequential, confirmed by the correct 6-class jar output)
  artifact of the `com.tridium.n-module`/`com.tridium.n-java` plugin's module-path handling — not traced
  into the plugin's own source this session.
- **B29-G6** — the `wslpath -w` output display anomaly noted in §29.6 (a long path's UNC-style prefix
  rendering truncated in the captured shell transcript) was not root-caused — cosmetic and
  zero-consequence for this block's findings (the license wall fires before `-output:<path>` is ever
  consumed), but worth a follow-up if a future block needs to actually READ a `test.exe`-produced HTML/
  XML report from WSL.

## 29.x — Connections

- **[Block 16]** — this block closes B16-G6 (the 5 JUnit4 files, scoped out of [Block 16] entirely) and
  substantially narrows B16-G1: [Block 16] could only conclude "no Linux launcher exists"; this block
  reaches the REAL launcher via WSL interop and shows the remaining blocker is licensing, not platform.
- **[Block 17]** — this block's §29.6 is an independent re-confirmation of §17.2's `tridium:nre`
  diagnosis against a 4th binary (`test.exe`, alongside `n5mig.exe`/`station.exe` from [Block 17] and
  the `-help`/`-version`/`wb.exe` control pair) — strengthening rather than merely repeating [Block 17]'s
  finding, and explicitly merges this block's own B29-G2 with [Block 17]'s B17-G1 rather than opening a
  duplicate gap.
- **[Block 9]** — the plain-TestNG fallback (§29.7) extends [Block 9]'s "zero sources, task SKIPPED"
  `niagaraTest` result and [Block 16]'s "reaches native-process launch, hard-fails" result with a THIRD,
  runtime-INDEPENDENT data point: the tests' own logic is proven correct without needing `niagaraTest`
  to ever succeed at all.
