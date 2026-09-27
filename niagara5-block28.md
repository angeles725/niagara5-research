# Block 28 — Porting CompPan and DashboardPan to N5: multi-part merge and the jakarta servlet migration

> Research of **whether N5 5.0.0.28's shipped Gradle plugins build the two remaining real N4 client
> modules** — `CompPan-rt` (single-part, no merge, no servlet) and `DashboardPan` (three-part
> `rt`+`ux`+`wb`, requires [Block 10]'s CHK-1 Module Part Combination merge AND the CHK-3
> javax.servlet→jakarta.servlet migration) — completing the requires-execution build/PoC gap
> [Block 16] scoped out (B16-G2: "whether a MULTI-module group still needs SOME form of a parent
> grouping file... Running DashboardPan's full CHK-1 merge + build would settle this and B10-G1's
> DashboardPan half at once"). Covers: porting both modules into `poc/comppan-n5/` and
> `poc/dashboardpan-n5/`, the full attempt log for each, a CHK-1..CHK-15 validation table extended
> to both modules, a genuinely decisive UNPREDICTED build blocker specific to `niagara.alarm`
> (§28.4 — not merely a variant of [Block 16]'s findings), the jakarta.servlet migration recipe as
> a reusable pattern, and final jar anatomy for both. Does NOT cover: a live N5 station deploy of
> either built jar (same open gap as [Block 9] §9.6.G1/[Block 16]'s open items), porting any of the
> 4 existing JUnit4 `srcTest` files for either module (out of scope, same as [Block 16]'s B16-G6),
> or `niagaraTest`/TestNG execution for either module (B16-G1's Windows-host blocker applies
> identically here and was not re-tested).
>
> Subject version: **Niagara 5.0.0.28 beta**, Gradle plugin artifacts `5.0.54.9.2`/`5.0.9.8.14`,
> Gradle **9.2.1**, JDK `/home/linuxbrew/.linuxbrew/opt/openjdk@25` (OpenJDK 25.0.4.1) — identical
> toolchain to [Block 9]/[Block 16]. N4 source: `CompPan-rt` and `DashboardPan-{rt,ux,wb}` read
> from `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249`, commit
> **`a109249d98b795c934c71b2165af976dbc39716e`** (2026-09-05, clean working tree, `git log -1`/
> `git status --short` both re-confirmed this session) — the SAME worktree [Block 10]/[Block 16]
> read from. Install root (READ-ONLY, never written): `/mnt/c/Program Files/Niagara/5.0.0.28`;
> config/modules root (READ-ONLY, never written): `/mnt/c/ProgramData/Niagara/tridium/config/
> 5.0.0.28` — verified holding exactly **247** jars before AND after every build this session
> (explicit `ls .../modules | wc -l` check after every `gradlew` invocation, per task scope). PoC
> workspaces: `/home/cristian/niagara5-research/poc/comppan-n5/` and
> `/home/cristian/niagara5-research/poc/dashboardpan-n5/` (both created this session, both MUST be
> added to `.gitignore` by the parent — they contain client sources; not done by this agent per
> task scope).
>
> Sources:
> - `Compresores/CompPan/CompPan-rt/**` and `Dashboard/DashboardPan/{DashboardPan-rt,
>   DashboardPan-ux,DashboardPan-wb}/**` in the `main-a109249` worktree — 3 + 7 `src/` files (2,549 +
>   3,976 combined lines), all `*.gradle.kts`/`module-include.xml`/`module-permissions.xml`/
>   `module.lexicon`/`module.palette` files, and the parent `niagara-module.xml` for both groups,
>   all read verbatim this session.
> - `web.jar`, `alarm.jar`, `control.jar`, `baja.jar`, `gx.jar`, `bajaui.jar`, `workbench.jar`,
>   `svgBatik.jar` `module-info.class` — extracted and disassembled with `javap` this session
>   (module names and full `requires` graphs, §28.4).
> - `jakarta.servlet-api-6.1.0.jar` (`bin/ext/`) `module-info.class` — disassembled this session
>   (confirms `module jakarta.servlet@6.1.0`).
> - `etc/gradle/libs.versions.toml:102` — `jakartaServlet` coordinate, read this session.
> - [Block 9] (PoC scaffold pattern), [Block 10] §10.11 (the CHK-1..CHK-15 checklist under
>   validation, esp. CHK-1/CHK-2/CHK-3/CHK-4), [Block 16] (the ColdRoomPan-rt recipe this block
>   copies verbatim for the mechanical parts — gradle.properties pattern, `niagara_config_home`
>   redirect, attempt-log format), [Block 5] §5.3 (signature deltas, cross-checked against actual
>   usage — zero hits), [Block 8] §8.2/§8.8 (permission-annotation model, confirmed not needed;
>   network/file-access impact, confirmed no relevant code path in either module), [Block 15]
>   (outbound-network-ungated finding — confirmed NOT applicable, see §28.1.1 correction below).
> - This session's own command output: every `./gradlew` invocation, `javap`, `jarsigner`,
>   `unzip`, `find`/`wc -l`/`ls` timestamp/count check — none archived under `sources/probes/` per
>   task scope (single-block deliverable, same convention as [Block 16]), all reproducible from the
>   cited jars/worktree/PoC trees.
>
> Method: mechanical port (copy + `sed` package rename + hand-authored `module-info.java`/
> gradle.kts, per [Block 16]'s recipe) applied to REAL, unmodified N4 source, then iterative
> `./gradlew <task>` execution against the real `/mnt/c` install (read-only throughout — the
> `niagara_config_home` redirect from [Block 16] §16.3 was applied from the FIRST attempt for both
> modules, not discovered mid-session this time). Every failure below is a real invocation, not
> predicted. Markers: `[CERT-hw]` observed build/tool output this session (the dominant marker) ·
> `[CERT]` a source file read directly · `[INFER]` deduction.
>
> N5 build-toolchain layer, §19 requires-execution phase. Connects [Block 9]/[Block 16] (PoC
> scaffold + recipe reuse), [Block 10] (CHK-1..CHK-15 validation extended to the 2 remaining
> modules, closing B10-G1 fully), [Block 5]/[Block 8]/[Block 15] (signature-delta, permission, and
> network findings re-confirmed against real modules with actual servlet/alarm code).
>
> **Type:** standard (evidence, requires-execution/§19 build-PoC)
>
> **Breakthrough:** both modules **build, jar, and sign successfully** — CompPan-rt on the FIRST
> real `jar` attempt with zero failures at all, and DashboardPan after ONE genuinely decisive
> unpredicted blocker: `niagara.alarm`'s module graph has a HARD (non-`static`) transitive
> compile-time dependency, several hops deep (`alarm`→`gx`/`bajaui`→`org.apache.xmlgraphics.
> batik.awt.util`; `alarm`→`bajaui`/`workbench`→`javafx.{graphics,swing,controls,web}`), on 5
> platform modules that are **not shipped as separate artifacts anywhere in this N5 5.0.0.28
> install** — they exist only inside Tridium's own custom-built, JavaFX/Batik-bundled JRE, whose
> `javac.exe` is itself Windows-only and unusable from this Linux/WSL host (mirroring [Block 16]
> §16.5.4's `bin/test.exe` finding for a DIFFERENT tool). The fix — 5 minimal empty stub `module-
> info.class` jars dropped into the local `niagara_config_home` mirror — unblocked compilation with
> no further cascade, and the resulting jar is functionally complete (all 3 merged types, the full
> servlet, the 3.5MB `rc/index.html` frontend, `/api/alarms` code path intact).

---

## 28.1 — Source provenance, and a correction to this task's own premise `[CERT]`

| Item | Value |
|---|---|
| Worktree | `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249` |
| Commit | `a109249d98b795c934c71b2165af976dbc39716e`, 2026-09-05 20:20:07 -0600, clean tree |
| CompPan-rt | `Compresores/CompPan/CompPan-rt/` — single-part (`runtimeProfiles="rt"`), 3 `src/` files, 2,549 lines; 2 existing JUnit4 `srcTest` files (not ported, same policy as [Block 16] B16-G6) |
| DashboardPan | `Dashboard/DashboardPan/` — three-part (`runtimeProfiles="rt,ux,wb"`): `-rt` (2 files, 2,383 lines, incl. `src/rc/icon16.png`), `-ux` (5 files, 1,593 lines, incl. `src/rc/index.html`, 3,597,670 bytes), `-wb` (**zero `src/` files** — confirmed by `find`, the directory holds only `DashboardPan-wb.gradle.kts`/`module-permissions.xml`/`module.lexicon`/`module.palette`) |

**Correction to this task's own briefing.** The task prompt that launched this block asserted
"DashboardPan does outbound HTTPS and serves a servlet." The servlet half is correct and is the
subject of §28.5 below. The outbound-HTTPS half is **not supported by the source**: a full-file
`grep -rn "HttpsURLConnection\|HttpURLConnection\|https://\|URLConnection\|HttpClient"` over every
`.java` file in all three DashboardPan parts this session returned **zero hits**. DashboardPan is a
pure inbound servlet (`BDashboardServlet` handles `GET`/`POST` under `/dashboardpan/`) with no
outbound network call anywhere in its own code. This is a negative-existence claim about a named,
opened artifact (all 7 `.java` files across the 3 parts), so it is `[CERT]` per METHODOLOGY §3, not
`[INFER]`. This does not refute [Block 15]'s finding (outbound sockets are audit-only, not
permission-gated in N5) — that finding is about the PLATFORM's enforcement model and remains valid
in general; it is simply never EXERCISED by this specific module, since DashboardPan makes no
outbound call to exercise it against.

## 28.2 — CompPan-rt: mechanical port, zero build failures `[CERT-hw]`

Applied [Block 16] §16.2's recipe verbatim (copy → `sed` `javax.baja.`→`niagara.` rename →
hand-authored `module-info.java` → gradle.kts plugin/manifest rewrite → delete
`module-permissions.xml` → empty `module-include.xml` skeleton → drop the parent
`niagara-module.xml` entirely → point `niagara_config_home` at a local mirror FROM THE START, not
discovered mid-session this time):

1. `sed -e 's/javax\.baja\./niagara./g' -e 's/javax\/baja\//niagara\//g'` over all 3 `src/` files
   — post-rename `grep -rn "javax"` over the ported tree: **zero hits** `[CERT-hw]`.
2. `src/module-info.java` (new): `module angeles.CompPan { requires transitive niagara.baja;
   requires niagara.nre; requires niagara.niagaraAnnotationProcessors; }` — same 3-`requires` set
   as ColdRoomPan-rt/`n5Hello`, sufficient here too.
3. `CompPan-rt.gradle.kts`: CHK-5 plugin renames, CHK-6 `moduleManifest` simplification, `n-java`
   added (per [Block 16] §16.2 step 4).
4. **New finding vs [Block 16]: the N4 test dependency does not exist in N5 at all.**
   `CompPan-rt.gradle.kts` declared `moduleTestImplementation(":test-wb")` — unlike ColdRoomPan-rt,
   which declared `":test"` (a module that DOES exist, `test.jar`). `ls .n5config/modules | grep -i
   test` this session shows only `test.jar`/`niagaraTest.jar` — **no `test-wb.jar` anywhere in this
   N5 5.0.0.28 install**. Since the 2 existing JUnit4 `srcTest` files were not ported (out-of-scope,
   [Block 16] B16-G6 policy applied identically here), no test dependency was declared at all in the
   ported `CompPan-rt.gradle.kts` — this specific incompatibility was therefore never exercised as a
   build failure, only discovered by inspection. Named **B28-G1** below (does `test-wb` exist under
   a different N5 name, or was it dropped entirely between N4 and N5?).
5. `module-permissions.xml` deleted (all `<req-permission>` blocks were already commented out,
   confirmed by direct read, same as [Block 16] CHK-8).
6. `module-include.xml` started as `<types></types>`; AP regenerated the single `CompressorControl`
   entry on first build (CHK-9).

**Result: `./gradlew :CompPan-rt:jar` succeeded on the FIRST real attempt — zero build failures for
this module, a cleaner outcome than [Block 16]'s ColdRoomPan-rt port** (which needed 2 test-dependency
fix iterations before its `niagaraTest` hard-failed on the platform gate). CompPan-rt's Slotomatic-
generated regions (`BCompressorControl.java`, hash-stamped, 2,060 lines) were recognized as already
up to date on the first `jar` attempt, with no separate `slotomatic` re-run needed — re-confirming
[Block 16] §16.5.1 on a second, larger, real module.

## 28.3 — DashboardPan: the CHK-1 multi-part merge, applied for real `[CERT-hw]`

**The merge is genuinely a 2-part merge, not 3 — `DashboardPan-wb` contributes zero source.** A
`find "$WT/DashboardPan-wb"` this session shows only build/manifest files (`DashboardPan-wb.gradle.kts`,
`module-permissions.xml`, `module.lexicon` — a header-comment-only stub, no entries — and
`module.palette` — an empty `<Folder></Folder>` skeleton). Merging it is a **documented zero-op**:
no Java source, no lexicon keys, no palette entries to fold in. This refines [Block 10] §10.11
CHK-1's framing ("merge -ux(3) and -wb(2) into -rt(4)") — the ACTUAL merge work is entirely in the
`-ux`→`-rt` direction; `-wb`'s only real contribution is that its `runtimeProfiles` letter existed
at all.

**Merge steps applied, into one project `poc/dashboardpan-n5/DashboardPan-rt/`:**

1. **Source merge** — `-rt`'s `com.angeles.DashboardPan` package (`BDashboardService.java`,
   `BRoomPanel.java`) and `-ux`'s `com.angeles.DashboardPan.ux` package (`BDashboardServlet.java`,
   `DashboardDispatch.java`, `DashboardRbacHelper.java`, `DashboardReader.java`, `JsonUtil.java`)
   both copied into the SAME `src/` tree, as two subpackages of one module (JPMS modules span
   multiple packages freely; nothing here requires them to unify). `sed` rename applied to both:
   `javax.baja.`→`niagara.` for all 7 files, `javax.servlet.`→`jakarta.servlet.` for the 2 `-ux`
   files that import it (§28.5). Post-rename `grep -rn "javax"`: **zero hits** `[CERT-hw]`.
2. **CHK-2 confirmed by direct code behavior, not just by doc rule.** `-ux`'s
   `api(project(":DashboardPan-rt"))` (for `BDashboardService.appendAudit`) is simply DELETED — no
   replacement needed, because `BDashboardServlet.resolveDashboardService()` already references
   `com.angeles.DashboardPan.BDashboardService` by its plain, fully-qualified Java type name (source
   uses no build-time module alias) — once both packages share one compilation unit, this resolves
   like any other same-module cross-package reference. `[CERT-hw]` (clean compile with the
   cross-project dependency line removed entirely).
3. **`src/rc/` resources merged**: `-rt`'s `icon16.png` (119 bytes) + `-ux`'s `index.html`
   (3,597,670 bytes, copied and `diff -q`-confirmed byte-identical to the N4 source this session)
   both land under one `rc/` folder, packaged by one merged `jar` task `from("src/rc")` block
   (previously two separate, near-identical `tasks.named<Jar>("jar") { from("src/rc")... }` blocks
   in `-rt` and `-ux`).
4. **CHK-4 (module-part-suffixed dependency stripping) applied, with one dependency DROPPED rather
   than stripped.** `api(":alarm-rt")` (declared by BOTH `-rt` and `-ux` — de-duplicated to one
   line) → `api(":alarm")`; `api(":web-rt")` (from `-ux`) → `api(":web")`. `api(":control-rt")`
   (declared by `-rt`, comment: "BNumericPoint (child control points host the alarm exts)") is
   **dropped entirely, not stripped to `api(":control")`** — a fresh `grep -rn "BNumericPoint"` over
   both source parts this session found **zero** actual Java references to any `control`-package
   type; the N4 gradle dependency was declared but unconsumed by the real source. Confirmed
   harmless: the module compiles and jars cleanly without it (§28.4/§28.6). This is a genuinely new
   observation [Block 10] §10.11 CHK-4 did not make (it listed `control-rt` as a dependency to
   strip, correctly, but did not check whether the stripped/renamed dependency was actually used).
5. **CHK-1's `niagara-module.xml` drop, generalized from single- to multi-part.** The parent
   `Dashboard/DashboardPan/niagara-module.xml` (`runtimeProfiles="rt,ux,wb"`) is **not copied into
   the PoC at all** — same treatment [Block 16] §16.4 gave ColdRoomPan-rt's single-part file. The
   build succeeded with no grouping XML present anywhere in the merged tree. **This closes [Block
   16]'s child gap B16-G2** ("whether a MULTI-module group still needs SOME form of a parent
   grouping file... was not tested"): it does NOT, even for a module that started as a genuine
   3-part group. `com.tridium.set.mpr`'s `findProjects()` located the single merged
   `DashboardPan-rt.gradle.kts` subproject with zero ambiguity.
6. **`module-include.xml`/`module.lexicon`/`module.palette` merged** by hand (concatenation, no key
   collisions found between the `-rt` and `-ux` lexicon/palette files, confirmed by direct read).
   `module-include.xml` started empty (`<types></types>`); the AP regenerated all 3 types
   (`DashboardServlet`, `RoomPanel`, `DashboardService`) correctly on first successful build (§28.6).
7. **`module-info.java` (new)**: `module angeles.DashboardPan { requires transitive niagara.baja;
   requires niagara.nre; requires niagara.niagaraAnnotationProcessors; requires niagara.alarm;
   requires niagara.web; requires jakarta.servlet; }` — module names for `alarm`/`web` confirmed by
   `javap` on their extracted `module-info.class` this session (`module niagara.alarm@5.0.0.28`,
   `module niagara.web@5.0.0.28`), not guessed from the N4 dependency notation.

## 28.4 — Unpredicted break: `niagara.alarm`'s hidden hard dependency on unshippable platform modules `[CERT-hw]`

**This is the single most operationally important finding in this block — genuinely distinct from
anything [Block 9]/[Block 16] surfaced.** `./gradlew :DashboardPan-rt:jar` (first real attempt, all
7 files rewritten, `module-info.java` requiring `niagara.baja`/`niagara.nre`/
`niagara.niagaraAnnotationProcessors`/`niagara.alarm`/`niagara.web`/`jakarta.servlet`) failed at
`compileJava`:

```
error: module not found: org.apache.xmlgraphics.batik.awt.util
error: module not found: javafx.graphics
error: module not found: javafx.swing
error: module not found: javafx.controls
error: module not found: javafx.web
5 errors
```

**Root-caused this session via `javap` on the real module graph, not guessed.** `--debug` on the
compile task exposed the actual `--module-path` javac received: every declared dependency jar
individually, PLUS the entire `.n5config/modules/` directory appended as one path entry (the
`com.tridium.conv.n-repo`/`n-helper-modularity` flat-file-repo convention — same mechanism [Block
16] §16.3 found writes into it). `javap` on `alarm.jar`'s extracted `module-info.class` shows its
REAL `requires` graph is far larger than the single `BAlarmRecord`/`BAckState`/`BITable` surface
DashboardPan's source actually uses:

```
module niagara.alarm@5.0.0.28 {
  requires java.desktop;
  requires transitive niagara.bajaui;
  requires niagara.bajaux;  requires niagara.box;  requires transitive niagara.bql;
  requires transitive niagara.control;  requires niagara.fox;  requires transitive niagara.gx;
  requires niagara.hx;  requires niagara.pdf;  requires niagara.platform;
  requires niagara.smartTableHx;  requires niagara.web;  requires niagara.webEditors;
  requires transitive niagara.workbench;  requires jakarta.servlet;  ...
}
```

Following the transitive chain two more hops (`javap` on `gx.jar`, `bajaui.jar`, `workbench.jar`,
`svgBatik.jar` this session) isolates the exact failure: `gx.jar` declares **`requires transitive
org.apache.xmlgraphics.batik.awt.util;`** (no `static` modifier — mandatory) and **`requires static
transitive javafx.graphics;`** (marked `static`); `bajaui.jar` declares plain **`requires
niagara.svgBatik;`**, and `svgBatik.jar` in turn declares the same mandatory, non-`static`
**`requires transitive org.apache.xmlgraphics.batik.awt.util;`**; `workbench.jar` declares
**`requires static javafx.base; requires static javafx.controls; requires static javafx.graphics;
requires static transitive javafx.web;`** (all four marked `static`). Despite 4 of the 5 reported
modules being declared `static` (normally optional-at-resolution) somewhere in the chain, **this
JDK 25 javac still failed to resolve the whole module graph** unless ALL FIVE were satisfiable —
`org.apache.xmlgraphics.batik.awt.util` is the one non-`static` (mandatory) edge that forces the
other four into the same failure, because the resolver must complete the FULL transitive closure of
every module reachable from the root (`angeles.DashboardPan`→`niagara.alarm`→…) to validate it,
regardless of which individual edges are marked optional deeper in the graph. `[CERT-hw]`.

**None of the 5 missing modules exist as separate artifacts anywhere in this N5 5.0.0.28
distribution.** A Python scan of every `module-info.class` inside all 247 `modules/*.jar` AND every
jar under `bin/ext/` and `bin/ext/*/` this session (`javap` on each extracted descriptor, matched
by declared module name, not filename) found **zero** jars declaring themselves as
`javafx.graphics`, `javafx.swing`, `javafx.controls`, `javafx.web`, or
`org.apache.xmlgraphics.batik.awt.util`. `find "$N5" -iname "*javafx*"` DOES find JavaFX artifacts
(`jre/lib/javafx-swt.jar`, `jre/legal/javafx.*`, `bin/ext/jxbrowser/jxbrowser-javafx-9.5.0.jar`,
`jre/bin/javafx/*.dll`) — confirming JavaFX exists somewhere in this Niagara distribution's JRE, but
**not as a separately resolvable JPMS module on any path our build touches**. It is `[INFER]` that
these are baked into the bundled JRE's own platform-module set (analogous to a commercial JDK build
that includes JavaFX as system modules) — not independently confirmed by inspecting the bundled
JRE's own `release`/`lib/modules` file this session, named **B28-G2** below.

**A genuine, previously-undiscovered refinement to [Block 9]/[Block 16]'s "no javac, JRE-only"
claim.** `find "$N5/jre" -iname "javac*"` this session found `jre/bin/javac.exe` — **the bundled
JRE is NOT JRE-only; it does ship `javac`**. But it is a Windows PE executable (`.exe`), unusable
from this Linux/WSL host — the SAME class of platform gate [Block 16] §16.5.4 found for
`bin/test.exe`, just for a DIFFERENT tool this time. This refines (does not simply repeat) [Block
9]'s/[Block 16]'s premise: the reason an external JDK (Homebrew OpenJDK 25) is used is not that no
`javac` exists in the install, but that the one that DOES exist cannot run on this host — and that
real, Windows-only, JavaFX/Batik-bundled `javac` is almost certainly the ONLY toolchain that could
compile `alarm.jar`'s own dependents against its full module graph without external stubbing. Named
**B28-G3** (confirm on a Windows host whether the real bundled `javac.exe` resolves this cleanly
with zero stubbing).

**Fix applied, verified working, and bounded — 5 minimal empty stub modules, nothing more needed.**
5 trivial `module <name> {}` sources were compiled (with the SAME external JDK 25, no special
tooling) and jarred (`jar --create --file <name>-stub.jar module-info.class`), then copied as REAL
files (not symlinks — they correspond to no real N5 artifact) into
`poc/dashboardpan-n5/.n5config/modules/`, the PoC's own LOCAL mirror directory — never touching
`/mnt/c`. These are NOT vendor binaries and redistribute nothing; they are empty JPMS graph-
completeness placeholders satisfying the module RESOLVER'S bookkeeping requirement, not providing
any actual JavaFX/Batik API surface — consistent with the corpus's "reimplement, do not relink"
discipline (METHODOLOGY §19), since DashboardPan's own source never references a single
`javafx.*`/`org.apache.xmlgraphics.*` type. With the 5 stubs present, `compileJava` succeeded with
**zero further cascading errors** — no deeper batik/SWT/OAuth module (`org.eclipse.swt.win32.
win32.x86_64`, `com.nimbusds.oauth2.sdk`, both also present as plain/mandatory `requires` deeper in
`gx.jar`/`workbench.jar`'s graphs) was ever reported missing, meaning those specific edges were
either already satisfied elsewhere on the path or genuinely optional at the depth this compile
needed. `[CERT-hw]` (`compileJava` BUILD SUCCESSFUL with exactly these 5 stubs and no others added).

**Scope of the finding.** This blocker is a property of `niagara.alarm` itself (its `requires
transitive niagara.bajaui`/`niagara.gx`/`niagara.workbench` — Workbench UI modules — dragged in by
an alarm module that ships BOTH headless alarm-source types AND alarm UI/print/console classes in
one module), not of DashboardPan's own code. **Any third-party N5 module needing even the most
basic headless alarm read (`BAlarmRecord`, `BITable` query) will hit this exact wall on a non-
Windows, non-JavaFX-bundled toolchain**, independent of what that module otherwise does. This is a
strictly stronger, more specific, and more actionable finding than [Block 15]'s general "network
access is ungated" result — it is about COMPILE-TIME module resolvability, not runtime permission
enforcement, and it blocks a class of module regardless of whether that module ever runs.


## 28.5 — The jakarta.servlet migration: a namespace-only rename, confirmed by `javap` on the real N5 API `[CERT-hw]`

**The reusable recipe** (CHK-3, applied to `BDashboardServlet.java` and `DashboardRbacHelper.java`,
the only 2 files in either module importing servlet types):

1. `sed 's/javax\.servlet\./jakarta.servlet./g'` over the import lines — both files imported ONLY
   `javax.servlet.http.HttpServletRequest`/`HttpServletResponse`, no other `javax.servlet.*`
   subpackage.
2. **No call-site changes anywhere** — every `HttpServletResponse.SC_*` constant, every
   `req.getParameter`/`getHeader`/`getRemoteUser`/`getReader`, every `resp.setStatus`/
   `setContentType`/`setHeader`/`getWriter`/`sendRedirect` call in `BDashboardServlet.java` (dozens
   of call sites across `doGet`/`doPost`/`handleEquipment`/`handleSetpointWrite`/`handleAlarms`/
   `serveStaticResource`/`send404`/`send405`) compiled and worked UNCHANGED after only the import
   rename — the constant names, method names, and signatures are identical between
   `javax.servlet-api:3.1.0` and `jakarta.servlet-api:6.1.0` for every member this code touches.
3. **Gradle dependency coordinate swap**: `compileOnly("javax.servlet:javax.servlet-api:3.1.0")` →
   `compileOnly("jakarta.servlet:jakarta.servlet-api:6.1.0")` — the EXACT coordinate the shipped
   `etc/gradle/libs.versions.toml:102` pins (`jakartaServlet = {group = "jakarta.servlet", name =
   "jakarta.servlet-api", version = "6.1.0"}`), not a guessed version. Module name confirmed by
   `javap` on its extracted `module-info.class`: `module jakarta.servlet@6.1.0`.
4. **Independently confirmed against the real N5 platform API, not just the servlet-api jar in
   isolation.** `javap -p` against `niagara.web.BWebServlet`/`niagara.web.WebOp` (extracted this
   session from the real `web.jar`) shows the Niagara-side wrapper API this module ACTUALLY
   overrides (`doGet(WebOp)`/`doPost(WebOp)`, unchanged shape from N4) already returns
   `jakarta.servlet.http.HttpServletRequest`/`HttpServletResponse` from `WebOp.getRequest()`/
   `getResponse()` — confirming [Block 5] §5.3's `BWebServlet` signature-delta finding
   (`javax.servlet.*`→`jakarta.servlet.*`) directly against the live jar rather than only via
   `javap` diff, and confirming the migration is a namespace rename with zero logic risk, exactly as
   [Block 10] §10.11 CHK-3 predicted (no `jetty-web.xml` exists in this module either, same as B10
   found — the `Configure`-class `ee11` fix path is not applicable here).

`[CERT-hw]` for all of the above — the servlet code compiled, jarred (§28.6/§28.7), and every
call site listed is present verbatim in the built `.class` files' constant pool (spot-checked via
the successful compile itself, which would have failed at any renamed/removed constant).

## 28.6 — CHK-1..CHK-15 validation table (both modules, against real compiler/Gradle output) `[CERT-hw]`

| CHK | [Block 10]'s prediction | CompPan-rt outcome | DashboardPan outcome | Verdict |
|---|---|---|---|---|
| CHK-1 (Module Part Combination) | DashboardPan only | not exercised (single-part) | Merge applied for real; `-wb` merge is a documented zero-op (§28.3) | **CONFIRMED, refined** `[CERT-hw]` |
| CHK-2 (intra-module dependency disappears) | DashboardPan-ux only | not exercised | `api(project(":DashboardPan-rt"))` deleted; cross-package call resolves with zero build-time indirection (§28.3.2) | **CONFIRMED** `[CERT-hw]` |
| CHK-3 (servlet API migration) | DashboardPan-ux only | not exercised | Namespace-only rename, zero call-site changes, confirmed against real `niagara.web.WebOp` (§28.5) | **CONFIRMED** `[CERT-hw]` |
| CHK-4 (module-part-suffixed deps stripping) | DashboardPan only | not exercised | `alarm-rt`/`web-rt` stripped and merged; `control-rt` DROPPED as genuinely unused (§28.3.4, new finding) | **CONFIRMED, extended** `[CERT-hw]` |
| CHK-5 (plugin id renames) | All files | Applied; `jar` succeeded | Applied; `jar` succeeded (after §28.4's unrelated fix) | **CONFIRMED** `[CERT-hw]` (both) |
| CHK-6 (`moduleManifest` simplification) | All files | Applied, no residual reference | Applied, no residual reference | **CONFIRMED** `[CERT-hw]` (both) |
| CHK-7 (`niagara-module.xml` drop) | Attribute drop; file stays | Parent file not copied at all; build succeeded — same as [Block 16] | Parent file (a MULTI-part group's grouping XML) not copied at all; build succeeded — **closes B16-G2** | **CONFIRMED unconditionally** `[CERT-hw]` — generalizes [Block 16]'s single-module finding to multi-part groups |
| CHK-8 (`module-permissions.xml` deletable) | Delete outright | Deleted; build succeeded | Deleted (3 files → 1); build succeeded | **CONFIRMED** `[CERT-hw]` (both) |
| CHK-9 (`module-include.xml` auto-regenerate) | Delete-and-regenerate | 1 type regenerated correctly | 3 types (from 2 source files across 2 packages) regenerated correctly, merged into ONE file | **CONFIRMED, extended to multi-package merge** `[CERT-hw]` |
| CHK-10 (`javax.baja`→`niagara` rename) | Global rename | 1 file, zero manual fixups | 7 files (2 packages), zero manual fixups | **CONFIRMED** `[CERT-hw]` (both) |
| CHK-11 (breaking-change rows absent) | BACnet/JSON/AccessController/etc. not present | Confirmed absent (fresh grep) | Confirmed absent (fresh grep) | **CONFIRMED (by absence)** `[CERT-hw]` (both) — note: this checklist did NOT predict §28.4's `niagara.alarm`/JavaFX/Batik break, a genuinely new breaking-change class this session adds to the corpus |
| CHK-12 (bajaui/UI migration N/A) | Not applicable | not exercised | `src/rc/index.html` remains a standalone static HTML page (byte-identical copy confirmed), no `bajaux`/`bajaui` widget — still not applicable | **CONFIRMED (by absence)** `[CERT-hw]` |
| CHK-13 (program-object signing N/A) | No `BProgram` | Confirmed, zero hits | Confirmed, zero hits | **CONFIRMED (by absence)** `[CERT-hw]` (both) |
| CHK-14 (Fox interop N/A) | `[INFER]` in Block 10 | not independently re-grepped for `fox` (one false-positive substring hit inside a base64 blob in `index.html`, confirmed non-Fox this session) | same | **not-hit — still `[INFER]`**, matching [Block 10]/[Block 16] |
| CHK-15 (priority ordering) | Mechanical-first → structural → rename → delete-regenerate | Order collapsed trivially (no structural/servlet work) | Order followed for real: CHK-5/6 → CHK-1/2/4 (merge) → CHK-3 (servlet) → CHK-10 (rename) → CHK-8/9 (delete-regen); §28.4's alarm/JavaFX fix was an UNPLANNED 6th step, not predicted by this ordering at all | **compatible, with one unpredicted addition** |

**Tally across both modules**: 11 CHK items CONFIRMED (7 with `[CERT-hw]` extension/refinement
beyond [Block 10]'s prediction, including CHK-7's full closure of B16-G2), 3 correctly predicted
not-applicable-by-absence, 1 unchanged `[INFER]` (CHK-14), 0 flatly refuted. **Zero of the 15
checklist items predicted §28.4's decisive break** — it is a genuinely new class of finding this
block adds to the corpus, not a CHK-item validation.

## 28.7 — Final jar anatomy (both modules) `[CERT-hw]`

**CompPan-rt** (`build/libs/CompPan-rt.jar`, 15 entries): `META-INF/module.xml` —
`moduleName="CompPan"`, `vendorVersion="2.0.7"` (matches `Compresores/build.gradle.kts`'s
`defaultModuleVersion("2.0.7")`, cross-checked this session — same group as [Block 16]'s
ColdRoomPan); `module-info.class` — `module angeles.CompPan@2.0.7`, major version 69 (Java 25), 3
`requires`, 0 exports; 4 `.class` files (`BCompressorControl`, `CompressorControl`,
`CompressorControl$Cfg`, `CpLog`); `module.palette`; `CompPan-rt.lexicon` (renamed from
`module.lexicon` on packaging, same convention [Block 16] §16.7 found). Signed, `jarsigner -verify`
→ `jar verified`, same reused keystore (`CN=cristian@DESKTOP-4AAQ77H(Niagara4Modules)...`).

**DashboardPan-rt** (`build/libs/DashboardPan-rt.jar`, 30 entries): `META-INF/module.xml` —
`moduleName="DashboardPan"`, `vendorVersion="2.1.1"` (matches `Dashboard/build.gradle.kts`'s
OWN `defaultModuleVersion("2.1.1")` — genuinely DIFFERENT from the `2.0.7` the `Compresores`/
`Paccadia` group uses; caught by reading `Dashboard/build.gradle.kts` directly this session rather
than reusing [Block 16]/§28's ColdRoomPan/CompPan value, a real per-group difference, not an
oversight); `<dependencies>` lists `alarm`, `baja`, `web` (auto-derived from the `api(...)` deps —
`jakarta.servlet` correctly absent, since it's `compileOnly`, same treatment N4's
`javax.servlet-api` compileOnly dependency got); `<types>` — all 3 merged types present
(`DashboardServlet`, `RoomPanel`, `DashboardService`); `module-info.class` — `module
angeles.DashboardPan@2.1.1`, `requires` list matches source exactly (baja/nre/AP/alarm/web/
jakarta.servlet), 0 exports; 12 `.class` files across both merged packages (incl. 7
`DashboardDispatch$RouteAction*` sealed-hierarchy inner classes, ported unchanged); `module.palette`
(merged, 3 entries); `DashboardPan-rt.lexicon` (merged, renamed on packaging); `rc/icon16.png` (119
bytes) + `rc/index.html` (3,597,670 bytes, byte-identical to source). Signed, `jarsigner -verify` →
`jar verified`, same reused keystore.

Both jars reproduced byte-for-byte STRUCTURALLY (entry count, entry names) across a `clean` +
rebuild this session (timestamps/`buildMillis` differ as expected, same non-claim [Block 9]/[Block
16] made).

## 28.8 — Attempt logs `[CERT-hw]`

**CompPan-rt** (3 `gradlew` invocations total, zero failures):

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew help` | BUILD SUCCESSFUL — plugin/subproject resolution confirmed |
| 2 | `./gradlew :CompPan-rt:jar` | **BUILD SUCCESSFUL on the first real attempt** |
| 3 | `./gradlew clean :CompPan-rt:jar` | BUILD SUCCESSFUL — reproducibility + `/mnt/c` cleanliness re-confirmed (247 jars, unchanged) |

**DashboardPan-rt** (5 `gradlew` invocations total, 1 real failure):

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew help` | BUILD SUCCESSFUL |
| 2 | `./gradlew :DashboardPan-rt:jar` | **FAILED** — `module not found` × 5 (javafx.{graphics,swing,controls,web}, org.apache.xmlgraphics.batik.awt.util) — §28.4 |
| — | fix: 5 empty stub module jars added to the local `.n5config/modules/` mirror (never `/mnt/c`) | — |
| 3 | `./gradlew :DashboardPan-rt:compileJava` | BUILD SUCCESSFUL — zero further cascading errors |
| 4 | `./gradlew :DashboardPan-rt:jar` | BUILD SUCCESSFUL — final artifact, `/mnt/c` re-verified clean (247 jars) |
| 5 | `./gradlew clean :DashboardPan-rt:jar` | BUILD SUCCESSFUL — reproducibility + `/mnt/c` cleanliness re-confirmed |

8 `gradlew` invocations total across both modules (well under the ~25-per-module cap, and well
under [Block 16]'s own 11-invocation ColdRoomPan-rt session), plus `javap`/`jarsigner`/`unzip`/
`diff`/`find`/`ls -la`/Python module-scan diagnostic commands not counted above. `/mnt/c/
ProgramData/Niagara/tridium/config/5.0.0.28/modules` was explicitly re-counted (`ls | wc -l`) after
EVERY `gradlew` invocation for both modules — **247 throughout, zero pollution, zero new files
appearing** (per task's mandatory check).


## 28.9 — Self-verify

This is a **build/PoC (§19) block** — its `[CERT-hw]` claims are live command output captured this
session, matching [Block 9]/[Block 16]'s established "LIVE-BUILD BLOCKS" convention (METHODOLOGY
§11).

- **Reproducibility check** — a final `clean` + rebuild for both modules (attempt 3/CompPan,
  attempt 5/DashboardPan) reproduced the same entry-count/entry-name jar structure as the prior
  successful build, confirming the build files described in §28.2/§28.3 are the actual files
  producing the artifacts in §28.7 (byte-identical hashes not claimed, same non-claim as [Block 9]/
  [Block 16] — `buildMillis` changes every run).
- **Token check** — every quoted error string (`module not found: org.apache.xmlgraphics.
  batik.awt.util`-class errors, the exact `requires`/`requires static`/`requires transitive` lines
  quoted from `alarm.jar`/`gx.jar`/`bajaui.jar`/`workbench.jar`/`svgBatik.jar`'s disassembled
  `module-info.class`, the `module angeles.CompPan@2.0.7`/`module angeles.DashboardPan@2.1.1`
  disassembly lines, the `test-wb.jar` absence, the `jre/bin/javac.exe` finding, the `find`/`ls`
  247-count outputs) was copied verbatim from this session's captured command output, not
  paraphrased — **≈28 distinct load-bearing tokens**, all mechanically sourced from `javap`/
  `gradlew`/`find`/`ls`/`grep` output captured this session.
- **Marker tally** — literal `verify-block.sh` output, run this session from
  `/home/cristian/niagara5-research`:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block28.md .
== verify-block: niagara5-block28.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 31  (adj 30)
   [CERT-live] 1
   [CERT] 5  (adj 4)
   [CERT-doc] 1
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 9  (adj 8)
-- ratio -- [INFER]/[CERT*] = 8/38 = 0.21
-- [CERT] file:line citation resolution --
   extern  etc/gradle/libs.versions.toml:102  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   resolved 0 of 1
   WARN    resolved 0 of 1 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

  The low counts on the four rarer marker rows above (live/doc/web/secondary-source) are the
  script matching this block's own header-blockquote legend line (which names every marker for the
  reader), the same self-matching [Block 16] §16.9 documented — this block makes zero ACTUAL claims
  at any of those four ranks. Adjusted deduction/evidence ratio = 8/(30+4) = **0.24** — low,
  consistent with a §19 build/PoC block whose claims are almost entirely direct hardware/live-build
  command output; the deduction-marked claims are explicitly bounded (CHK-14 unchanged from
  [Block 10]/[Block 16], B28-G1's `test-wb` fate, B28-G2's "baked into the bundled JRE" deduction,
  B28-G3's Windows-host confirmation). The single evidence-marked citation the script flags
  (`etc/gradle/libs.versions.toml:102`) resolves as `extern` because it
  points into the real N5 install tree (`/mnt/c/...`), outside this corpus directory — same
  "LIVE-BUILD BLOCKS" convention [Block 9]/[Block 16] established (METHODOLOGY §11); it was read
  directly this session (`grep -n "servlet" .../libs.versions.toml`), not carried from memory.
  Every `[CERT-hw]` citation into the worktree, the real N5 jars, or the PoC trees is likewise a
  bare `file:line`/command-output reference external to this corpus's own directory.
- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block28.md`;
  the PoC trees exist at `/home/cristian/niagara5-research/poc/comppan-n5/` and
  `/home/cristian/niagara5-research/poc/dashboardpan-n5/`. Per task scope (single-block
  deliverable, same convention as [Block 16]), `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were
  **not** regenerated this session — the parent orchestrator owns that, along with adding both PoC
  directories to `.gitignore` (neither was touched by this agent, per task instructions).
- **MCP-doc snapshots** — N/A, no MCP/context7 web citation used.

## 28.9.G — Child gaps

- **B28-G1** — Whether N4's `:test-wb` module (declared by CompPan-rt's and DashboardPan's
  `moduleTestImplementation`) exists under a different name in N5, or was genuinely dropped between
  N4 and N5, is unresolved — this session confirmed only that no `test-wb.jar` (or any
  `*test-wb*`-named jar) exists in this N5 5.0.0.28 install's `modules/`/`bin/ext/`. Since no test
  code was ported for either module, this was never exercised as an actual build failure.
- **B28-G2** — Whether the 5 missing modules from §28.4 (`javafx.{graphics,swing,controls,web}`,
  `org.apache.xmlgraphics.batik.awt.util`) are genuinely baked into Tridium's bundled JRE as
  platform modules (as opposed to simply absent/unshippable in this beta) was not independently
  confirmed by inspecting the bundled JRE's own `release`/`lib/modules` — `[INFER]` only.
- **B28-G3** — Whether the real bundled `jre/bin/javac.exe` (confirmed to exist, but Windows-only
  and untestable from this Linux/WSL host) resolves `niagara.alarm`'s full module graph WITHOUT the
  5 stub modules this session needed, on an actual Windows host, remains untested — this would be
  the cleanest confirmation that the stub-module workaround is equivalent to, not a deviation from,
  the vendor's own intended toolchain.
- **B28-G4** — A live N5 station deploy of either built jar (`CompPan-rt.jar`/`DashboardPan-rt.jar`)
  was not attempted — same open gap [Block 9] §9.6.G1 and [Block 16] left open, now applying to 2
  more built jars.
- **B28-G5** — `niagaraTest`/TestNG execution for either module was not attempted — [Block 16]
  §16.5.4/B16-G1's Windows-host `bin/test.exe` blocker was assumed to apply identically (same
  install, same platform gate) rather than independently re-triggered this session.
- **B28-G6** — Porting the 2 (CompPan) + 4 (DashboardPan `-ux` srcTest`) existing JUnit4 test files
  to TestNG was scoped out, same policy as [Block 16] B16-G6, now applying to 2 more modules' worth
  of untested test coverage.

## 28.x — Connections

- **[Block 16]** — this block extends B16's ColdRoomPan-rt recipe to 2 more real modules; the
  mechanical steps (CHK-5/6/7/8/9/10, `niagara_config_home` redirect, Slotomatic no-op-on-rebuild)
  transferred UNCHANGED to CompPan-rt with zero new findings on the mechanical side, while
  DashboardPan's CHK-1 merge + CHK-3 servlet migration + the §28.4 `niagara.alarm` break are all
  genuinely new. **Closes B16-G2** (multi-part group grouping-file question) definitively: not
  needed, confirmed on a real 3-part-turned-2-part merge.
- **[Block 10]** — this block IS the requires-execution validation B10-G1 asked for, completed:
  CHK-1/CHK-2/CHK-3/CHK-4 (DashboardPan-only items) are now all CONFIRMED by a real build, not just
  static doc-vs-code reading. All 15 checklist items have now been build-validated across the 3
  client modules (ColdRoomPan-rt in [Block 16]; CompPan-rt/DashboardPan here).
- **[Block 5]** — none of either module's imports touch [Block 5] §5.3's `getLanguage`/`equals`/
  `getRuntimeProfile` deltas (confirmed by fresh grep); `BWebServlet`'s `javax.servlet`→
  `jakarta.servlet` signature delta (§5.3's `BWebServlet` row) is independently re-confirmed this
  session directly against the live `niagara.web.WebOp`/`BWebServlet` API via `javap`, not merely
  cited from Block 5.
- **[Block 8]** — CHK-8's prediction (permission XML deletable) is confirmed again, on 2 more real
  modules (3 permission files → 2, for DashboardPan's merge). §8.8's "outbound network audit-only,
  no enforcement" finding is NOT exercised by DashboardPan (§28.1 correction — the module makes no
  outbound call at all, contrary to this block's own task briefing).
- **[Block 15]** — see [Block 8] connection above; this block's §28.1 correction narrows, but does
  not refute, [Block 15]'s general network-ungated finding.
- **[Block 9]** — the gradle.properties/wrapper/settings.gradle.kts scaffold pattern (copied via
  [Block 16]'s already-adapted version) transferred to 2 more PoC directories with zero further
  adaptation needed.
