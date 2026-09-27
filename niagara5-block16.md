# Block 16 — Porting ColdRoomPan to N5: a real build validates the porting checklist

> Research of **whether N5 5.0.0.28's shipped Gradle plugins actually build a real, existing N4
> module** — not a fresh stub like [Block 9]'s `n5Hello` — once [Block 10]'s CHK-1..CHK-15 porting
> checklist is applied to it, and whether the checklist's static predictions survive contact with a
> live `gradlew` invocation. This is the §19 build/PoC gap GAP B10-G1 + B9-G2 named directly ("no live
> N5 Gradle build was actually run against any of our three modules"; "a real `niagaraTest`/TestNG run
> with actual `srcTest`/`moduleTest` source"). Covers: porting `ColdRoomPan-rt` (the smallest,
> single-part, dependency-lightest of our three N4 modules per [Block 10] §10.10) into a COPY under
> `poc/coldroompan-n5/`, the full attempt log, a CHK-1..CHK-15 validation table against real compiler/
> Gradle output, a genuinely dangerous unpredicted build side-effect (writes into the read-only N5
> install), the produced main + moduleTest jar anatomy, and one TestNG test's `niagaraTest` run result.
> Does NOT cover: CompPan or DashboardPan (DashboardPan's CHK-1 module-part merge remains untested by
> any build — new child gap), a live N5 station deploy of the built jar (same open gap as B9's
> §9.6.G1), or porting the module's 5 existing JUnit4 tests to TestNG (scoped out — only ONE new
> minimal TestNG test was added, per task scope; the 5 JUnit4 tests were left unconverted, new child
> gap below).
>
> Subject version: **Niagara 5.0.0.28 beta**, Gradle plugin artifacts `5.0.54.9.2`/`5.0.9.8.14`, Gradle
> **9.2.1**, JDK `/home/linuxbrew/.linuxbrew/opt/openjdk@25` (OpenJDK 25.0.4.1) — identical toolchain to
> [Block 9]. N4 source: `ColdRoomPan-rt` read from
> `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`, commit
> **`a109249d98b795c934c71b2165af976dbc39716e`** (2026-09-05, clean working tree, `git log -1`/
> `git status --short` both confirmed this session) — the SAME worktree [Block 10] §10.10 read from.
> Install root (READ-ONLY, see §16.3 for a session where this almost wasn't true):
> `/mnt/c/Program Files/Niagara/5.0.0.28`; config/modules root (READ-ONLY):
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`. PoC workspace:
> `/home/cristian/niagara5-research/poc/coldroompan-n5/` (created this session).
>
> Sources:
> - `Paccadia/ColdRoomPan/ColdRoomPan-rt/**` in the `main-a109249` worktree — 8 `src/` files (4,163
>   total lines across `src/`+`srcTest/`), `ColdRoomPan-rt.gradle.kts`, `module-include.xml`,
>   `module-permissions.xml`, `module.lexicon`, `module.palette`, and the parent
>   `Paccadia/ColdRoomPan/niagara-module.xml`, all read verbatim this session.
> - `docSource.jar!test/niagara/test/BTestNg.java` — extracted and read in full this session (the
>   TestNG base-class source; the `docDeveloper.jar` bajadoc for the same class was consulted first
>   but is a stub summary, not the implementation — §16.6 below explains why the source jar was needed).
> - `docDeveloper.jar!doc/buildN5.html` — re-consulted for the "TestNG Support in Niagara 5" cross-
>   reference (a separate document this jar does NOT itself contain — new finding, §16.9.G3) and the
>   module/srcTest file-tree convention.
> - [Block 9] `niagara5-block9.md` (PoC scaffold pattern, gradle.properties/wrapper reuse, attempt-log
>   format), [Block 10] `niagara5-block10.md` §10.11 (the CHK-1..CHK-15 checklist under validation),
>   [Block 5] `niagara5-block5.md` §5.3 (the `Clock`/`getLanguage`/`equals`/`getRuntimeProfile` real
>   signature deltas, cross-checked against this module's actual usage), [Block 8] `niagara5-block8.md`
>   §8.2 (permission-annotation replacement model, confirmed not needed here), [Block 7]
>   `niagara5-block7.md` (Slotomatic/AP division of labor, re-confirmed against an ALREADY-generated
>   module rather than a fresh stub).
> - This session's own command output: every `./gradlew` invocation, `javap`, `jarsigner`, `unzip`,
>   `diff`, `find`/`stat` timestamp check — none archived under `sources/probes/` per task scope
>   (single-block deliverable), all reproducible from the cited jars/worktree/PoC tree.
>
> Method: mechanical port (copy + `sed` package rename + hand-authored `module-info.java`/gradle.kts)
> applied to REAL, unmodified N4 source, then iterative `./gradlew <task>` execution against the real
> `/mnt/c` install (read-only after §16.3's fix) with `JAVA_HOME` on the JDK 25 Homebrew build. Every
> failure below is a real invocation, not predicted. Markers: `[CERT-hw]` observed build/tool output
> this session (the dominant marker, as in [Block 9]) · `[CERT]` a source file read directly · `[INFER]`
> deduction.
>
> N5 build-toolchain layer, §19 requires-execution phase. Connects [Block 9] (PoC scaffold pattern,
> B2-G7 closure this block extends to a real module), [Block 10] (the CHK-1..CHK-15 checklist this
> block validates against live output, closing B10-G1), [Block 5] (signature deltas cross-checked
> against real usage), [Block 7]/[Block 8] (Slotomatic and permission-annotation findings re-confirmed
> on a non-trivial module).
>
> **Type:** standard (evidence, requires-execution/§19 build-PoC)
>
> **Breakthrough:** the real client module **builds, jars, and signs successfully** end-to-end from the
> N4 source with only mechanical changes — but getting there surfaced a genuinely dangerous,
> completely unpredicted build side-effect (§16.3: the `jar` task writes into the READ-ONLY N5 install
> directory unless `niagara_config_home` is redirected away from it), and `niagaraTest` reaches actual
> TestNG execution readiness (compiles, wires, packages) but then **hard-fails at native-process launch**
> on this Linux host — a decisive, previously-unreachable answer to B9-G2/B2-G4: the blocker is a
> Windows-only native launcher (`bin/test.exe`), not a test-discovery or annotation-processing defect.

---

## 16.1 — Source provenance `[CERT]`

| Item | Value |
|---|---|
| Worktree | `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249` |
| Commit | `a109249d98b795c934c71b2165af976dbc39716e`, 2026-09-05 20:20:07 -0600 |
| Working tree state | clean (`git status --short` empty), confirmed this session |
| Module | `Paccadia/ColdRoomPan/ColdRoomPan-rt/` — single-part (`runtimeProfiles="rt"`), 8 `src/` files (4,163 combined `src/`+`srcTest/` lines), 5 existing JUnit4 test files |
| Why this module | [Block 10] §10.10 identified it as the smallest/single-part/dependency-lightest of our three modules — the cheapest real port to validate the checklist against, matching B10-G1's own suggestion verbatim |

`[CERT]` (`git log -1`, `git status --short`, `find`/`wc -l` over the module tree, this session).

## 16.2 — Mechanical porting recipe applied (ordered) `[CERT-hw]`

Applied in this order; each step names the CHK item it operationalizes (§16.4 validates the outcome):

1. **Copy** `src/**/*.java` (8 files) verbatim from the worktree into `poc/coldroompan-n5/ColdRoomPan-rt/src/`.
2. **Rename the import namespace** with a single global substitution, run once per file:
   ```
   sed -e 's/javax\.baja\./niagara./g' -e 's/javax\/baja\//niagara\//g' <file> > <dest>
   ```
   (CHK-10.) This one substitution was **sufficient** for all 8 files — a post-rename
   `grep -rn "javax"` over the ported tree returned **zero hits** `[CERT-hw]`. No manual per-import
   fixups were needed, because none of this module's ~24 import lines touch any of [Block 5] §5.3's
   *renamed-symbol* deltas (`getLanguage`→`getLanguageCode`, `BObject.equals` removal,
   `Type.getRuntimeProfile` removal) — confirmed by grep, §16.4 CHK-10 row.
3. **Author `src/module-info.java` by hand** (new file, no N4 equivalent):
   `requires transitive niagara.baja; requires niagara.nre; requires niagara.niagaraAnnotationProcessors;`
   — the same 3-`requires` set [Block 9]'s `n5Hello` used, sufficient here too (this module needs no
   additional N5 module namespace).
4. **Rewrite `ColdRoomPan-rt.gradle.kts`**: plugin id renames (CHK-5: `niagara-module`→`n-module`,
   `niagara-signing`→`sign`, `niagara-jacoco`→`jacoco`, `niagara-annotation-processors`→REMOVED + add
   `n-helper-modularity`, `convention.niagara-home-repositories`→`conv.n-repo`); delete
   `moduleManifest{ runtimeProfile.set(rt) }` line + its `RuntimeProfile` import (CHK-6); add
   `com.tridium.n-java` (undocumented-by-wizard requirement, [Block 9] §9.4); add
   `moduleTestImplementation("org.testng:testng:7.12.0")` alongside `moduleTestImplementation(":test")`
   (new finding, §16.5.3 — `:test` alone did not suffice).
5. **Delete `module-permissions.xml` outright** (CHK-8) — all three `<req-permission>` blocks were
   already commented out in the N4 source, so nothing needed translation to `@Grant*` annotations.
6. **Replace `module-include.xml` with an empty `<types></types>` skeleton** (CHK-9) rather than
   hand-porting its 6 `<type>` entries — the AP regenerates it on first build.
7. **Drop the parent `niagara-module.xml` grouping file entirely** — not copied at all (refines CHK-7,
   §16.4).
8. **Copy `module.lexicon` and `module.palette` verbatim**, no changes.
9. **Point `niagara_config_home` at a LOCAL mirror**, not the real `/mnt/c` install (§16.3 — this step
   was added mid-session after a real incident, not planned up front).
10. **Build**: `./gradlew :ColdRoomPan-rt:jar` directly — **no separate `slotomatic` step needed first**
    for this already-Slotomatic'd module (§16.5.1, a new finding [Block 9]'s fresh-stub PoC could not
    have surfaced).
11. **Test**: one new file, `srcTest/test/com/angeles/ColdRoomPan/ColdRoomControlN5Test.java`, extending
    `niagara.test.BTestNg`, `org.testng.annotations.Test` methods (§16.6). The module's 5 existing
    JUnit4 test files were **removed from this PoC's `srcTest/`**, not ported — they do not compile
    against N5's shipped `test` module (§16.5.2) and porting all 5 was out of this task's stated scope
    (new child gap, §16.9.G1).

## 16.3 — Unpredicted break #1: the `jar` task writes into the READ-ONLY N5 install `[CERT-hw]`

**This is the single most operationally important finding in this block.** Pointing
`niagara_config_home` at the real install (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`,
exactly as [Block 9]'s `n5-hello` PoC did safely for a module name that never collided with anything
already installed there) and running `./gradlew :ColdRoomPan-rt:jar` produced a **new file**,
`.../modules/ColdRoomPan-rt.jar`, inside the real read-only install directory —

```
$ ls -la --time-style=full-iso /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules | grep -i coldroom
-rw-rw-rw- 1 cristian cristian 28562 2026-09-27 05:42:39.465885200 -0600 ColdRoomPan-rt.jar
```

`[CERT-hw]` — a real write to `/mnt/c`, forbidden by this task's read-only scope. The exact task
responsible was not isolated to one named Gradle task this session (a `tasks --all` listing showed no
task literally named `install*`/`copy*`; the write is a side effect inside the `com.tridium.n-module`/
`com.tridium.conv.n-repo` plugin machinery, most likely the same flat-file-repo wiring the
`ColdRoomPan-rt.gradle.kts.vm`-derived comment calls "configures `!bin/ext` and `!modules` as flat-file
Maven repositories" — this plugin apparently also PUBLISHES the just-built jar into that same directory
as a convenience for resolving it from a sibling module in the same multi-project build, not just
reading from it). **[Block 9]'s `n5-hello` PoC never observed this** because it used a module name
(`n5Hello`) that had never been installed anywhere before, so the write was silent and indistinguishable
from "nothing happened" — this session's collision with a REAL client module name is what surfaced it.

**Fix applied, verified working:** `niagara_config_home` redirected to a local mirror,
`poc/coldroompan-n5/.n5config/`, whose `modules/` subfolder holds **249 symlinks** (not copies) to the
real jars — dependency resolution is unaffected, but the install-style write now lands in the local
mirror instead:

```
$ ln -sf "$C/modules/"*.jar "$MIRROR/modules/"   # 249 symlinks created
$ ./gradlew clean :ColdRoomPan-rt:jar
BUILD SUCCESSFUL
$ find /mnt/c/.../modules -iname "*coldroom*"     # after the fix
(no output — confirmed clean)
$ ls -la .n5config/modules/ColdRoomPan-rt.jar
-rw-r--r-- ... Sep 27 05:49 ColdRoomPan-rt.jar    # the write now lands here instead
```

Every build from this point in the session onward was preceded/followed by an explicit
`find /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules -iname "*coldroom*"` check; all
returned either the pre-fix stale file (unchanged timestamp, confirming no NEW write) or nothing at all
(the pre-fix file was apparently later removed by the parent agent, per its own message mid-session —
not by this agent). `[CERT-hw]`

**Corpus-level defensive precedent, not investigated further here:** `.gitignore` already carried a
`poc/**/.n5config/` rule *before* this block ever wrote there, alongside `poc/n5mig-panccadia/` and
`poc/_quarantine-install-*/` under a "CLIENT DATA — station copies and migration outputs" heading —
suggesting an earlier, undocumented PoC session hit the same or a related install-write hazard and left
this defensive rule as a scar. `[INFER]` (no block or retro in this corpus documents that session; the
`.gitignore` comment itself is the only evidence) — named as **B16-G4** below.

**Kit-delta consequence.** Any future N5 module port (via this recipe or a `build-n4-module`-kit-style
automated scaffold) MUST redirect `niagara_config_home` away from a real, shared, read-only Niagara
install before running any task that reaches `compileJava`→`jar`, or it will silently install into that
shared install — this is a load-bearing addition the kit's N5 delta list did not carry before this
session, extending [Block 9] §9.7's 3-item list to a 4th item.

## 16.4 — CHK-1..CHK-15 validation table (against real compiler/Gradle output) `[CERT-hw]`

| CHK | [Block 10]'s prediction | Outcome this session | Verdict |
|---|---|---|---|
| CHK-1 (Module Part Combination) | DashboardPan-only; ColdRoomPan explicitly skips it | Not exercised — single-part module, no merge attempted | **not-hit (correctly predicted N/A)** |
| CHK-2 (intra-module dependency disappears) | DashboardPan-ux-only | Not exercised | **not-hit (correctly predicted N/A)** |
| CHK-3 (servlet API migration) | DashboardPan-ux-only | Not exercised — ColdRoomPan-rt has no servlet import | **not-hit (correctly predicted N/A)** |
| CHK-4 (module-part-suffixed deps stripping) | DashboardPan-only | `ColdRoomPan-rt.gradle.kts` has no `-rt`/`-ux`-suffixed cross-module deps to strip | **not-hit (correctly predicted N/A)** |
| CHK-5 (Gradle plugin id renames) | All 6 ids rename per table | Applied verbatim; `:ColdRoomPan-rt:jar` succeeded | **CONFIRMED** `[CERT-hw]` |
| CHK-6 (`moduleManifest` simplification) | Delete `runtimeProfile.set(rt)` + import | Deleted; build succeeded with no residual reference | **CONFIRMED** `[CERT-hw]` |
| CHK-7 (`niagara-module.xml` attribute drop) | Drop the `runtimeProfiles` **attribute** (file stays) | The file was **never copied into the PoC at all**, and `com.tridium.set.mpr`'s `findProjects()` located the single `ColdRoomPan-rt.gradle.kts` subproject with no grouping XML present anywhere in the tree; the build never referenced it | **REFINED/PARTIALLY REFUTED** `[CERT-hw]` — for a single-module group, the file is not merely edited, it is not needed at all. Whether a MULTI-module group (DashboardPan-style) still needs it in some reduced form is untested — **B16-G2** |
| CHK-8 (`module-permissions.xml` deletable) | Delete outright, no `@Grant*` needed | Deleted; build succeeded, no permission-related compile/runtime error | **CONFIRMED** `[CERT-hw]` |
| CHK-9 (`module-include.xml` auto-regenerate) | Delete-and-regenerate, no hand-merge | Started as an empty `<types></types>` skeleton; the AP rewrote it with the correct 6 `<type>` entries on first `jar` | **CONFIRMED** `[CERT-hw]` |
| CHK-10 (`javax.baja`→`niagara` rename) | Global rename, all files | One `sed` substitution, zero manual fixups, zero residual `javax` hits | **CONFIRMED** `[CERT-hw]` |
| CHK-11 (breaking-change rows absent) | BACnet/JSON/AccessController/etc. not present | Compile succeeded with zero errors touching any of those surfaces | **CONFIRMED (by absence)** `[CERT-hw]` |
| CHK-12 (bajaui/UI migration N/A) | Not applicable to any of our 3 modules | ColdRoomPan-rt has no UI surface — not exercised | **not-hit (correctly predicted N/A)** |
| CHK-13 (program-object signing N/A) | No `BProgram`/`ProgramObject` | Confirmed — compile succeeded, no signing-related error | **CONFIRMED (by absence)** `[CERT-hw]` |
| CHK-14 (Fox interop N/A) | `[INFER]` in Block 10 (not independently re-grepped) | No `Fox`-related import in this module; not independently re-grepped this session either | **not-hit — still `[INFER]`, not promoted to `[CERT]`** (same gap Block 10 named as B10-G4) |
| CHK-15 (priority ordering) | Mechanical-first, then structural, then rename, then delete-regenerate | This module has no structural (CHK-1/2/4) or servlet (CHK-3) work, so the order collapsed trivially to: copy+rename (CHK-10) → gradle.kts (CHK-5/6) → module-info.java (new) → delete/empty (CHK-8/9); no contradiction with the stated ordering | **compatible / not refuted** |

**Tally**: 8 CONFIRMED, 5 not-hit (correctly predicted N/A), 1 REFINED/partially refuted (CHK-7), 1
unchanged `[INFER]` (CHK-14), 0 flatly refuted.

## 16.5 — Unpredicted breaks #2–#4 (not covered by any CHK item) `[CERT-hw]`

**16.5.1 — An already-Slotomatic'd, unchanged module needs no `slotomatic` re-run at all.**
[Block 9]'s `n5Hello` PoC started from a hand-authored 3-line stub with zero generated code, so it
*had* to hit the `"have you run slot-o-matic?"` compile error and run `:n5Hello:slotomatic` before
`:n5Hello:jar` could succeed. `ColdRoomPan-rt`'s source, by contrast, already carries N4's Slotomatic-
generated `Property`/`Action` regions (checked into git, hash-stamped `/*@ $com.angeles.ColdRoomPan.
BColdRoom(...)1.0$ @*/`). `./gradlew :ColdRoomPan-rt:jar` **succeeded outright on the very first real
attempt**, no AP validation error at all — the N5 `NiagaraSlotProcessor` ([Block 7] §7.6) validates
slot NAMES against the annotations, not the Slotomatic hash stamp, so pre-existing, name-matching
generated code satisfies it with zero re-generation. A follow-up `./gradlew :ColdRoomPan-rt:slotomatic`
run confirmed this independently: `diff -u` against a pre-run copy of all 6 annotated source files
showed **zero byte differences** — N5's Slotomatic recognized the existing generated regions as
already up to date and rewrote nothing. `[CERT-hw]` (both the successful first `jar` attempt and the
zero-diff `slotomatic` re-run, this session). This is genuinely new: neither [Block 7]/[Block 9]
(which established WHAT Slotomatic does and that it's a disconnected task) nor [Block 10]'s CHK-9 (which
is about `module-include.xml`, a different artifact) addressed whether re-running it is even NECESSARY
for a module whose property/action set did not change during porting.

**16.5.2 — N4's `org.junit`-based `srcTest` does not compile against N5's shipped `test` module.**
Copying the 5 existing JUnit4 test files (`import org.junit.Test; import static org.junit.Assert.*;`)
verbatim into `srcTest/` and running `:ColdRoomPan-rt:niagaraTest` failed at `compileModuleTestJava`
with `package org.junit does not exist` — **61 errors**, one per `@Test`/`assert*` usage across the 5
files. `[CERT-hw]` (full compiler output, this session). Neither [Block 9] (zero test sources) nor
[Block 10] (only examined `src/`, not `srcTest/`'s test-framework surface) predicted this — porting a
module's MAIN source is a different, and apparently easier, problem than porting its TEST source, since
N5's shipped `test` module carries TestNG (`org.testng`), not JUnit4.

**16.5.3 — `moduleTestImplementation(":test")` alone does not put `org.testng.*` on the compile
classpath.** After removing the 5 JUnit4 files and adding one TestNG test extending `niagara.test.
BTestNg` (§16.6), the FIRST `niagaraTest` attempt with only `moduleTestImplementation(":test")`
declared still failed: `package org.testng does not exist; package org.testng.annotations does not
exist` — even though `test.jar` bundles `LIB-INF/testng-7.12.0.jar` internally `[CERT]` (`unzip -l`,
confirmed present). The bundled jar is packaging, not an exposed transitive dependency across the
module boundary. Adding the explicit coordinate `org.testng:testng:7.12.0` (the exact version pinned in
the shipped `libs.versions.toml`, `testng = {group = "org.testng", name = "testng", version =
"7.12.0"}` `[CERT]`) alongside `:test` resolved it — `compileModuleTestJava` then succeeded. `[CERT-hw]`

**16.5.4 — `niagaraTest` cannot execute on this Linux/WSL host at all — this is the decisive answer to
B9-G2/B2-G4.** With the TestNG dependency fixed, `compileModuleTestJava`→`moduleTestClasses`→
`writeTestModuleXml`→`moduleTestJar` all succeeded, and the task graph reached `niagaraTest` itself —
which then failed, not with a test-framework or annotation-processing error, but with:

```
Execution failed for task ':ColdRoomPan-rt:niagaraTest'.
> A problem occurred starting process 'command '/mnt/c/Program Files/Niagara/5.0.0.28/bin/test''
Caused by: java.io.IOException: Cannot run program ".../bin/test" (in directory "...\ColdRoomPan-rt"):
  Exec failed, error: 2 (No such file or directory)
```

`ls "/mnt/c/Program Files/Niagara/5.0.0.28/bin/"` shows the actual file is **`test.exe`** — a Windows
PE binary, alongside `station.exe`, `wb.exe`, `console.exe`, `niagarad.exe`, all Windows-only; the `bin/`
directory ships **no Linux ELF equivalent anywhere** (confirmed by directory listing and `file
bin/test`, which itself fails since no extensionless `test` exists) `[CERT-hw]`. `niagaraTest` is
implemented as a Gradle `Exec`-style task that shells out to a native per-platform launcher rather than
running purely inside the JVM that's already executing Gradle — and this beta install (`5.0.0.28`) only
ships the Windows launcher set. **This directly answers B9-G2/B2-G4** in a way neither prior PoC could:
[Block 9]'s `n5-hello` niagaraTest run never got past "zero sources, task SKIPPED" — it never reached
the native-process-launch step at all, so it was inconclusive by construction. This session's run
reached that step and hit a **hard platform gate**, not a test-discovery defect: on a Linux/WSL host
with only a Homebrew JDK and no Windows Niagara install, `niagaraTest` cannot run ANY test, regardless
of framework, annotation correctness, or module-include wiring. Whether the SAME beta running on
Windows (with real `test.exe`) would then correctly discover and run the TestNG method is a separate,
now much narrower, open question — **B16-G1** below.

## 16.6 — The TestNG test added, and why `docSource.jar` (not `docDeveloper.jar`) was needed `[CERT]`

`docDeveloper.jar!doc/buildN5.html` cross-references a **separate document**, "TestNG Support in
Niagara 5," for test setup details — but that document does **not** ship inside `docDeveloper.jar`
itself (a `unzip -l` filename search across the whole jar found no file matching `testng`/`test-ng` by
that title `[CERT-hw]`; only `doc/test/niagara/test/BTestNg.bajadoc`/`BTestNgStation.bajadoc`, thin
API-reference stubs, not a setup guide — new finding, **B16-G3**). `docSource.jar` (a separate shipped
module carrying Java SOURCE, not bajadoc HTML) has the real implementation, `test/niagara/test/
BTestNg.java`, read in full this session (quoted in the header's Sources list) — it shows the base
class is itself `@NiagaraType`, `org.testng`-`@Listeners`-annotated, and wraps `setClassLoader`/
`restoreClassLoader` `@BeforeMethod`/`@AfterMethod` hooks around every test method (documented reason:
`"PA.invokeMethod will not find any BObject classes when TestNg is running with a non-
ModuleClassLoader as the current context class loader"` `[CERT]`, `BTestNg.java`, doc-comment quoted
verbatim). The new test, `ColdRoomControlN5Test`, extends this class directly (no new `@NiagaraType`/
slots declared — it inherits `BTestNg`'s own `TYPE`), and exercises `ColdRoomControl.positiveDelayMs`
— the defrost-time≤0 guard from the corpus's own "ColdRoomPan defrost time<=0 bug" finding (`Clock.
schedule` rejects a delay ≤ 0; this method floors it to 1 ms) — with 3 `@Test` methods covering zero,
negative, and ordinary-positive input. `[CERT]` (test file quoted in full in the PoC tree,
`poc/coldroompan-n5/ColdRoomPan-rt/srcTest/test/com/angeles/ColdRoomPan/ColdRoomControlN5Test.java`).

## 16.7 — Final jar anatomy `[CERT-hw]`

**Main jar** (`ColdRoomPan-rt/build/libs/ColdRoomPan-rt.jar`, 19 entries):

| Entry | Notes |
|---|---|
| `META-INF/MANIFEST.MF` | `Implementation-Vendor: Angeles`, `Implementation-Version: 2.0.7` (matches the real N4 group's `Paccadia/build.gradle.kts` `defaultModuleVersion("2.0.7")` `[CERT]`), `Sealed: true`, `Automatic-Module-Name: com.angeles.ColdRoomPan-rt` |
| `META-INF/NIAGARA4.SF`/`.RSA` | same signature-file naming as [Block 9] |
| `META-INF/module.xml` | `schemaVersion="5"`; `moduleName="ColdRoomPan"` (distinct from the jar's own `name="ColdRoomPan-rt"`); auto `<dependency name="baja".../>`; `<types>` with all 6 entries, AP-written |
| `module-info.class` | `module angeles.ColdRoomPan@2.0.7`, major version **69** (Java 25); `requires transitive niagara.baja`, `requires niagara.nre`, `requires niagara.niagaraAnnotationProcessors`; 0 exports |
| 8 `.class` files | `BColdRoom`, `BDefrostController`, `BDefrostMode`, `BEvaporatorUnit`, `BFanMode`, `BStagingMode`, `ColdRoomControl`, `CrLog` — all package-private/final where the N4 source declared them so (`ColdRoomControl` stayed package-private, confirming JPMS's lack of `exports` does not itself change intra-package visibility) |
| `module.palette` | copied verbatim, unchanged |
| `ColdRoomPan-rt.lexicon` | **renamed on packaging** from the source's `module.lexicon` — an unpredicted, minor packaging-convention detail, not itself a break |

Signing: `jarsigner -verify` → `jar verified`, same reused OS-level keystore CN as [Block 9]
(`CN=cristian@DESKTOP-4AAQ77H(Niagara4Modules)...`) — continuity, not a new finding.

**ModuleTest jar** (`ColdRoomPan-rt-module-test.jar`, 9 entries): `META-INF/module.xml` declares
`name="ColdRoomPan-rtTest"`, `moduleName="ColdRoomPanTest"`, dependencies on `ColdRoomPan-rt`
(`vendorVersion="2.0"` — truncated from the declared `2.0.7` to major.minor, an observed but
unexplained truncation, **B16-G5**), `baja`, and `test`. **No `module-info.class` at all** — the
moduleTest jar is NOT its own JPMS module, unlike the main jar. Also signed with the same keystore.
`[CERT-hw]` (`unzip -l`/`unzip -p`/`jarsigner -verify`, this session).

## 16.8 — Attempt log `[CERT-hw]`

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew help` | BUILD SUCCESSFUL — plugin/subproject resolution confirmed |
| 2 | `./gradlew :ColdRoomPan-rt:jar` (niagara_config_home = real `/mnt/c`) | **BUILD SUCCESSFUL — but wrote `ColdRoomPan-rt.jar` into the read-only install** (§16.3) |
| 3 | `./gradlew :ColdRoomPan-rt:slotomatic` | BUILD SUCCESSFUL, **zero-diff** rewrite (§16.5.1) |
| 4 | `./gradlew clean :ColdRoomPan-rt:jar --dry-run` | diagnostic — task graph `compileJava→processResources→classes→writeModuleXml→jar`, `slotomatic` absent (confirms [Block 9] §9.3's finding on a real module) |
| 5 | `./gradlew clean :ColdRoomPan-rt:jar` (still real `/mnt/c`) | BUILD SUCCESSFUL |
| — | fix: redirect `niagara_config_home` to `.n5config/` local mirror (249 symlinks) | — |
| 6 | `./gradlew clean :ColdRoomPan-rt:jar` (post-fix) | BUILD SUCCESSFUL — **verified zero new writes under `/mnt/c`** |
| 7 | `./gradlew :ColdRoomPan-rt:niagaraTest` (5 JUnit4 tests copied in) | **FAILED** — `package org.junit does not exist`, 61 errors (§16.5.2) |
| — | remove the 5 JUnit4 files; add `ColdRoomControlN5Test` (TestNG, `moduleTestImplementation(":test")` only) | — |
| 8 | `./gradlew :ColdRoomPan-rt:niagaraTest` | **FAILED** — `package org.testng does not exist` (§16.5.3) |
| — | add `moduleTestImplementation("org.testng:testng:7.12.0")` | — |
| 9 | `./gradlew :ColdRoomPan-rt:niagaraTest` | **FAILED** — compile succeeded through `moduleTestJar`; hard-failed launching native `bin/test` (§16.5.4) |
| 10 | `./gradlew :ColdRoomPan-rt:niagaraTest --stacktrace` | diagnostic — full `ProcessExecutionException`/`IOException` chain captured |
| 11 | `./gradlew clean :ColdRoomPan-rt:jar :ColdRoomPan-rt:moduleTestJar` | BUILD SUCCESSFUL — final artifacts, `/mnt/c` re-verified clean |

11 `gradlew` invocations total (well under the ~20 cap), plus `jarsigner`/`javap`/`unzip`/`diff`/`find`/
`stat` diagnostic commands not counted above.

## 16.9 — Self-verify

This is a **build/PoC (§19) block** — its `[CERT-hw]` claims are live command output captured this
session, matching [Block 9]'s established convention for this block type (methodology §11 "LIVE-BUILD
BLOCKS").

- **Reproducibility check** — attempt 11 (final `clean` + rebuild) reproduced the same 19-entry main
  jar / 9-entry moduleTest jar structure as attempts 5/6/9, confirming the build files described in
  §16.2 are the actual files producing the artifacts in §16.7 (byte-identical hashes were NOT expected
  or claimed — `module.xml`'s embedded `buildMillis` timestamp changes every run, same as [Block 9]'s
  non-claim).
- **Token check** — every quoted error string (`package javax.baja.sys does not exist`-class errors
  never occurred at all this session, confirming CHK-10; `package org.junit does not exist`;
  `package org.testng does not exist`; the `ProcessExecutionException`/`Exec failed, error: 2`
  chain; the `module angeles.ColdRoomPan@2.0.7` disassembly line; the `ColdRoomPan-rt.lexicon`
  packaging rename; the `.n5config` timestamp/`find` outputs) was copied verbatim from this session's
  captured command output, not paraphrased — **≈15 distinct load-bearing tokens**, all mechanically
  sourced.
- **Marker tally** — literal `verify-block.sh` output, run this session from
  `/home/cristian/niagara5-research`:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block16.md .
== verify-block: niagara5-block16.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 27  (adj 26)
   [CERT-live] 1
   [CERT] 12  (adj 11)
   [CERT-doc] 1
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 10  (adj 9)
-- ratio -- [INFER]/[CERT*] = 9/41 = 0.22
-- [CERT] file:line citation resolution --
   jar-entry  docDeveloper.jar!doc/buildN5.html  (jar archive path — not file-verifiable)
   jar-entry  docSource.jar!test/niagara/test/BTestNg.java  (jar archive path — not file-verifiable)
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

  The `[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` counts of 1 each are the script matching the
  marker-legend line in this block's own header blockquote (which names all markers for the reader),
  not a real claim carrying that marker — this block makes zero actual `[CERT-live]`/`[CERT-web]`/
  `[CERT-a]` claims. Adjusted `[INFER]`/`[CERT*]` ratio = 9/(26+11) = **0.24** — low, consistent with a
  §19 build/PoC block whose claims are almost entirely direct `[CERT-hw]` command output; the 9
  `[INFER]` claims are explicitly bounded (CHK-14 unchanged from Block 10, the `.gitignore` precedent
  in §16.3, the `vendorVersion` truncation left unexplained in §16.7, and the parent-grouping-file
  question in CHK-7/B16-G2). Every `[CERT]`/`[CERT-hw]` citation into the worktree or PoC tree is a
  bare `file:line`/command-output reference external to this corpus's own directory — same
  "LIVE-BUILD BLOCKS" convention [Block 9] established (methodology §11); the 2 flagged `jar-entry`
  lines are archive-internal paths read directly this session (`unzip -p`/full read), not carried from
  memory.
- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block16.md`; the
  PoC tree exists at `/home/cristian/niagara5-research/poc/coldroompan-n5/`. Per task scope
  (single-block deliverable), `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated this
  session.
- **MCP-doc snapshots** — N/A, no MCP/context7 web citation used.

## 16.9.G — Child gaps

- **B16-G1** — Whether `niagaraTest` actually discovers and runs `ColdRoomControlN5Test`'s 3 `@Test`
  methods on a REAL Windows Niagara install (where `bin/test.exe` exists) remains untested — this
  session's Linux/WSL host cannot answer that half of B2-G4 at all. This is now the single cleanest,
  most narrowly-scoped remaining piece of B2-G4.
- **B16-G2** — Whether a MULTI-module group (DashboardPan-style, `rt`+`ux`+`wb` before the CHK-1 merge,
  or even just `rt` alone after it) still needs SOME form of a parent grouping file for
  `com.tridium.set.mpr`'s `findProjects()` to work, or whether CHK-7's file is unconditionally
  unnecessary in N5 regardless of module-group size, was not tested (this PoC ported exactly one
  module). Running DashboardPan's full CHK-1 merge + build would settle this and B10-G1's DashboardPan
  half at once.
- **B16-G3** — The "TestNG Support in Niagara 5" document `buildN5.html` cross-references does not
  ship inside `docDeveloper.jar` under any filename this session's search found; locate it (it may be
  web-only, or inside a different shipped doc jar not yet censused).
- **B16-G4** — The `.gitignore` rule `poc/**/.n5config/` predates this block's own write; identify
  which prior (possibly undocumented) session or tool run first hit the install-write hazard §16.3
  describes, to confirm or refute the `[INFER]` connection drawn there.
- **B16-G5** — `ColdRoomPan-rtTest`'s `module.xml` dependency on `ColdRoomPan-rt` lists
  `vendorVersion="2.0"` where the module's own declared version is `2.0.7` — confirm whether N5's
  dependency-version model always truncates to major.minor for inter-module dependency declarations
  (in which case this is expected, not a defect) by checking a shipped Tridium module's own
  intra-suite dependency versions for the same pattern.
- **B16-G6** — Port the module's 5 existing JUnit4 test files to TestNG (scoped out of this task; only
  one new minimal test was added). This would give a much richer `niagaraTest` signal than the 3
  trivial cases added here, once B16-G1's Windows-host question is answered.

## 16.x — Connections

- **[Block 9]** — this block reruns B9's PoC pattern (gradle.properties/wrapper reuse, attempt-log
  format, jar-anatomy table) against a REAL module instead of a stub, confirming several of B9's
  findings transfer unchanged (Slotomatic/AP division of labor, task-graph shape, signing continuity)
  while surfacing 4 genuinely new findings B9's stub could not reach (§16.3, §16.5.1–§16.5.4).
- **[Block 10]** — this block IS the requires-execution validation B10-G1 asked for: 8 of 15 checklist
  items CONFIRMED, 5 correctly predicted not-applicable, 1 (CHK-7) refined, 1 (CHK-14) still open exactly
  as Block 10 left it. DashboardPan and CompPan remain unvalidated (only ColdRoomPan was built).
- **[Block 5]** — none of this module's imports touch any of §5.3's real signature deltas
  (`getLanguage`/`equals`/`getRuntimeProfile`/`Clock` instantiation) — confirmed by a clean compile
  with zero fixups beyond the namespace rename, corroborating Block 5's own module-scoped porting-cost
  baseline (§5.6) for this exact module.
- **[Block 7]** — §16.5.1 extends B7's Slotomatic findings: not only is Slotomatic a disconnected,
  one-shot task (B7/B9), it is also a NO-OP (zero-diff) when re-run against already-generated,
  unchanged source — a case B7/B9 never exercised.
- **[Block 8]** — CHK-8's prediction (permission XML deletable, no `@Grant*` needed) is now CONFIRMED
  by a real build for a real module, not just a doc-vs-code static census.
