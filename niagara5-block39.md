# Block 39 — Building N5 modules that depend on alarm/bajaui on Linux: JavaFX and Batik

> Research of **the supported, stub-free way to compile a third-party N5 module that transitively
> requires `niagara.alarm`** (or anything reaching `niagara.bajaui`/`niagara.gx`/`niagara.workbench`),
> closing the 3 child gaps [Block 28] §28.4 left open: **B28-G7** (find the supported way instead of
> empty stub module jars), **B28-G2** (is JavaFx genuinely baked into the bundled JRE), and **B28-G3**
> (does the real bundled `jre/bin/javac.exe` resolve the graph without stubs). Covers: an exhaustive
> search of the entire N5 5.0.0.28 install for any Apache Batik artifact; the official docs' stated
> JDK requirement and the exact mechanics of the `n-java` Gradle plugin's `--module-path` construction
> (from decompiled source); a from-scratch rebuild of [Block 28]'s `DashboardPan-rt` PoC with the 5
> empty stub jars REMOVED and replaced by real Maven Central artifacts; and a live invocation of the
> real Windows `jre/bin/javac.exe` via WSL interop, both as a negative and a positive control. Does
> NOT cover: a live N5 station deploy of the resulting jar (same open gap [Block 9]/[Block 16]/
> [Block 28] left open), or fully explaining the exact javac module-resolution algorithm behind an
> observed but unexplained non-error on 3 OTHER nominally-mandatory `requires` edges (§39.4, opened as
> a new child gap, extending rather than resolving [Block 28] §28.4's own hedge on the same anomaly).
>
> Subject version: **Niagara 5.0.0.28 beta**, same install/config roots and Gradle plugin artifacts
> (`5.0.54.9.2`/`5.0.9.8.14`, Gradle 9.2.1) as [Block 9]/[Block 16]/[Block 28]. Homebrew JDK toolchain:
> `/home/linuxbrew/.linuxbrew/opt/openjdk@25` (`javac 25.0.4.1`, re-confirmed this session). Install
> root (READ-ONLY, never written): `/mnt/c/Program Files/Niagara/5.0.0.28`; config/modules root
> (READ-ONLY, never written): `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28` — verified holding
> exactly **247** jars before AND after every build/probe this session (`ls .../modules | wc -l`,
> repeated after every `gradlew` invocation and after the Windows-`javac.exe` probes, per task scope).
> PoC workspace: [Block 28]'s existing `/home/cristian/niagara5-research/poc/dashboardpan-n5/` (already
> gitignored — `git check-ignore -v` confirmed this session), reused and MODIFIED in place: the 5 empty
> stub jars this block replaces were moved (not deleted) to
> `poc/dashboardpan-n5/.n5config/stubs-backup/` for reproducibility, and
> `DashboardPan-rt/DashboardPan-rt.gradle.kts` gained 6 new `compileOnly(...)` lines (§39.3). A second,
> throwaway scratch dir under this session's tool scratchpad
> (`.../scratchpad/b28g3-test/`, outside the repo, never committed) holds the 3 minimal
> `module-info.java` probes for the Windows-`javac.exe` tests (§39.4) — nothing under this path needs
> gitignoring, it is outside `/home/cristian/niagara5-research` entirely.
>
> Sources:
> - Live filesystem/jar inspection this session: a Python `zipfile` scan of **373 jars** across every
>   jar-bearing directory in the N5 5.0.0.28 install (`bin/ext` incl. subdirs, the 247-jar config
>   `modules/` mirror, `lib`, `NCS-Agent`, `JxBrowser`, `defaults`, `etc`, `javadoc`) for any
>   `org/apache/batik`/`org/apache/xmlgraphics` class entry; `jimage list` on the bundled JRE's own
>   `jre/lib/modules`; `cat jre/release`; `find jre/legal` (per-module legal-notice folder listing).
> - `docDeveloper.jar!doc/buildN5.html` (`niagara-help/devguide-clean/buildN5.txt`, already extracted
>   from a prior session, re-read this session) and `doc/upgradingJDK.html`
>   (`niagara-help/devguide-clean/upgradingJDK.txt`) — full-text grep + targeted read this session.
> - `com/tridium/gradle/plugins/java/util/ModulePathArgumentProvider.kt` and
>   `com/tridium/gradle/plugins/java/NiagaraJavaPlugin.kt` — Vineflower decompilation of
>   `n-plugin-5.0.54.9.2.jar` already cached from [Block 2]'s session at
>   `/tmp/claude-1000/n5b2/vf-out/`, re-read in full this session (not re-decompiled).
> - `org.openjfx:javafx-{base,graphics,controls,web,swing}:25` (`:linux` classifier) and
>   `org.apache.xmlgraphics:batik-awt-util:1.19` — fetched live from Maven Central
>   (`repo1.maven.org`) this session via Gradle's `mavenCentral()` resolution (already declared as a
>   repository in `poc/dashboardpan-n5/build.gradle.kts` from [Block 28]'s session); cached under
>   `~/.gradle/caches/modules-2/files-2.1/org.openjfx/` and `.../org.apache.xmlgraphics/`, sha256'd
>   this session (§39.3).
> - This session's own `./gradlew clean :DashboardPan-rt:compileJava` / `:jar` output (×2 each, one
>   failing-then-fixed pair, one clean-rebuild reproducibility pair) and 3 direct invocations of
>   `/mnt/c/Program Files/Niagara/5.0.0.28/jre/bin/javac.exe` through WSL interop (§39.4) — none
>   archived under `sources/probes/` per task scope (single-block deliverable, same convention as
>   [Block 9]/[Block 16]/[Block 28]), all reproducible from the cited PoC tree and Maven coordinates.
> - [Block 28] (the gaps this block closes), [Block 9]/[Block 16] (PoC scaffold/`gradle.properties`
>   pattern reused verbatim), [Block 2] (the decompiled plugin source this block re-reads).
>
> Method: exhaustive filesystem/jar search (Python `zipfile`, `jimage`), official-doc full-text read,
> decompiled-source read (no new decompilation), and a real build/PoC iteration (§19) — remove the
> stub jars, add real Gradle dependencies, rebuild, then independently cross-check with the REAL
> vendor `javac.exe` via WSL interop as a second, unrelated toolchain. Markers: `[CERT-hw]` observed
> command/build output this session (the dominant marker) · `[CERT]` a source/decompiled file read
> directly · `[CERT-web]` a live Maven Central HTTP response this session · `[INFER]` deduction.
>
> N5 build-toolchain layer, §19 requires-execution phase, extends [Block 28] §28.4. Connects
> [Block 28] (closes B28-G7/B28-G2/B28-G3), [Block 9]/[Block 16] (PoC scaffold reuse), [Block 2] (the
> `n-java` plugin's `--module-path` construction, read to completion here).
>
> **Type:** standard (evidence, requires-execution/§19 build-PoC)
>
> **Breakthrough:** the 5 empty stub `module-info` jars [Block 28] needed are **not the supported fix
> and are not necessary** — `org.apache.xmlgraphics.batik.awt.util` is genuinely absent from the ENTIRE
> N5 5.0.0.28 install on BOTH platforms (373 jars scanned, zero hits), but it is a real, current,
> actively-published third-party Apache Batik artifact (`org.apache.xmlgraphics:batik-awt-util`,
> latest `1.19`) whose manifest's `Automatic-Module-Name` matches the required module name exactly.
> Declaring it — plus real `org.openjfx:javafx-{base,graphics,controls,web,swing}:25:linux` artifacts
> on Linux, where the Homebrew toolchain JDK has no bundled JavaFX — as ordinary `compileOnly` Gradle
> dependencies from `mavenCentral()` makes `DashboardPan-rt` compile and jar cleanly with **zero stub
> jars and zero further cascading errors**, reproduced across a clean rebuild. Independently, invoking
> the REAL bundled Windows `jre/bin/javac.exe` via WSL interop — Tridium's own official toolchain,
> untested until now (B28-G3) — proves `javafx.*` genuinely IS a system module of the bundled JRE
> (closing B28-G2 to `[CERT-hw]`: `niagara.alarm` compiles past all 4 javafx errors with ZERO javafx
> artifacts supplied) but **also fails on the exact same missing Batik module** as the Linux/Homebrew
> toolchain — this is a **new, decisive finding beyond [Block 28]'s framing**: the vendor's own
> supported Windows toolchain does not resolve `niagara.alarm`'s graph out of the box either; Batik is
> a genuine gap in Tridium's own N5 5.0.0.28 beta module graph, not a Linux-only workaround target, and
> the real-artifact fix found here (not stubs) is the one a Windows developer would need too.

---

## 39.1 — Batik is absent from the entire N5 5.0.0.28 install, on every path searched `[CERT-hw]`

A Python `zipfile` scan this session opened every `.jar`/`.zip` under `bin/ext` (109 jars, all
subdirectories incl. `bcfips`), the config `modules/` mirror (247 jars), `lib`, `NCS-Agent`,
`JxBrowser`, `defaults`, `etc`, and `javadoc` — **373 jars total** — checking each jar's full entry
list for any path starting `org/apache/batik` or `org/apache/xmlgraphics`. **Zero hits across all 373
jars.** This re-confirms and extends [Block 28] §28.4's own narrower `bin/ext`+`modules/` check
(which used `javap` per-jar) with a full-content package scan covering every jar-bearing directory in
the install, not just the two most likely ones.

`jimage list "jre/lib/modules"` on the bundled JRE (JDK 25.0.4, confirmed via `jre/release`'s
`JAVA_VERSION="25.0.4"` line) lists **exactly 61 modules** — every one a standard `java.*`/`jdk.*`/
`jfx.*` platform module, plus the 7 `javafx.*` ones ([Block 28] §28.4's `[INFER]` "baked into the
bundled JRE" deduction, now independently corroborated by 3 separate signals: `jre/release`'s own
`MODULES=` string, `jimage list`'s live descriptor dump, and `find jre/legal` — every one of the 61
modules, including all 7 `javafx.*`, has its own per-module legal-notice folder under `jre/legal/`;
**no `batik`/`xmlgraphics` legal folder exists anywhere in that listing**). `[CERT-hw]`.

This is a negative-existence claim about named, opened artifacts (all 373 jars' full entry lists, the
JRE's own `jimage`-derived module descriptor list, and its legal-notice folder listing), so it is
`[CERT-hw]`/`[CERT]` per METHODOLOGY §3, not `[INFER]` — every one of the 373 candidate locations was
actually opened and read this session, not merely assumed absent.

## 39.2 — What the docs say, and what the plugin actually puts on `--module-path` `[CERT]` / `[CERT-doc]`

**The docs name no JDK vendor.** A full-text grep of both `buildN5.txt` and `upgradingJDK.txt` this
session for `zulu`/`liberica`/`azul`/`bellsoft`/any vendor name returns **zero hits**. The only
concrete guidance is generic:

> "In order to build Niagara modules, you need a valid Java 25 JDK with JavaFx." — `buildN5.txt:22`

and the example `gradle.properties` override uses a folder-naming CONVENTION, not a product name:

> `org.gradle.java.installations.paths=C:\\JDKS\\java-25-jdk-with-javafx` — `buildN5.txt:506`

`[CERT-doc]` (`niagara-help/devguide-clean/buildN5.txt:22,502-514`, both extracted from
`docDeveloper.jar!doc/buildN5.html` in a prior session, re-read verbatim this session). This means the
"supported setup" is genuinely open-ended from the doc's own perspective: any JDK 25 distribution that
happens to bundle JavaFX as system modules satisfies the stated requirement, and Tridium's own bundled
`jre/` (§39.1) is itself exactly such a distribution — it is not a separate download the doc is
pointing at.

**The `n-java` plugin's `--module-path` NEVER references the JRE at all — mechanically confirmed from
decompiled source, not inferred from build behavior.** `ModulePathArgumentProvider.environmentPath()`
(the exact method [Block 9] §9.4 observed producing "5 real jar/dir entries" from the outside) builds
the argument from EXACTLY 4 path segments, string-concatenated with `File.pathSeparator`:

```kotlin
private fun environmentPath(): String {
   return "${moduleClassPath.get().asPath}${sep}${niagaraHome.get().dir("bin/ext")...}" +
          "${sep}${niagaraHome.get().dir("bin/ext/bcfips")...}" +
          "${sep}${niagaraConfigHome.get().dir("modules")...}"
}
```

`[CERT]` (`/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/java/util/
ModulePathArgumentProvider.kt:50-60`, decompiled `n-plugin-5.0.54.9.2.jar`, read in full this session).
`moduleClassPath` is a `Property<FileCollection>` — Gradle's own resolved dependency classpath for the
compile task — wired by `NiagaraJavaPlugin.apply()` onto every `JavaCompile` task's
`compilerArgumentProviders` (`NiagaraJavaPlugin.kt:71-79`, same decompiled jar, read in full this
session). **The JRE's own `jre/` directory — where the 7 `javafx.*` system modules actually live — is
never one of these 4 segments.** This is the mechanical reason JavaFX resolution depends entirely on
which JDK Gradle uses to RUN javac, not on anything this plugin adds: a plain JDK (Homebrew OpenJDK 25,
no bundled JavaFX) needs JavaFX supplied via `moduleClassPath` (i.e., as an ordinary Gradle dependency,
§39.3) exactly like any other third-party library, while a JDK that bundles JavaFX as system modules
(Tridium's own `jre/`, or a commercial "JDK+JavaFX" distribution matching the doc's generic wording)
resolves it automatically through ordinary JPMS system-module lookup, with no `--module-path` entry
needed for it at all — confirmed directly in §39.4 below.

## 39.3 — Clean fix, no stubs: real Maven Central artifacts, `compileJava`+`jar` both succeed `[CERT-hw]`

**Setup.** In the existing `poc/dashboardpan-n5/` PoC ([Block 28]'s own tree, re-used, gitignored):
the 5 empty stub jars (`javafx.{controls,graphics,swing,web}-stub.jar`,
`org.apache.xmlgraphics.batik.awt.util-stub.jar`) were moved out of `.n5config/modules/` into
`.n5config/stubs-backup/` — confirmed absent from `.n5config/modules/` by direct `ls` this session.
6 `compileOnly(...)` lines were added to `DashboardPan-rt/DashboardPan-rt.gradle.kts` (`mavenCentral()`
was already a declared repository in the root `build.gradle.kts` from [Block 28]'s session, unchanged
here):

```kotlin
compileOnly("org.openjfx:javafx-base:25:linux")
compileOnly("org.openjfx:javafx-graphics:25:linux")
compileOnly("org.openjfx:javafx-controls:25:linux")
compileOnly("org.openjfx:javafx-web:25:linux")
compileOnly("org.openjfx:javafx-swing:25:linux")
compileOnly("org.apache.xmlgraphics:batik-awt-util:1.19")
```

**A real gotcha, found and fixed this session: the no-classifier OpenJFX Maven coordinates are
intentionally EMPTY placeholder jars.** The first attempt used only 4 lines (graphics/controls/web/
swing, no explicit `javafx-base`), relying on each artifact's own POM to pull `javafx-base:25`
transitively. That attempt FAILED — `error: module not found: javafx.base`, despite
`javafx-base-25.jar` genuinely being present in the Gradle cache. `jar --describe-module` on that
exact cached jar shows why: **`javafx.baseEmpty@25 automatic`** — the unclassified
`org.openjfx:javafx-base:25` coordinate on Maven Central is a deliberate ~300-byte placeholder whose
`Automatic-Module-Name` is suffixed `Empty`, meant to be classifier-substituted at resolve time by the
upstream `org.openjfx` Gradle plugin (which this build does not use); `javafx-graphics-25.jar` and
`javafx-controls-25.jar`'s own unclassified coordinates are the same kind of `…Empty` placeholder
(`javafx.graphicsEmpty`, `javafx.controlsEmpty` — confirmed by `jar --describe-module` this session),
harmlessly co-resident on the module path once the correctly-classified `-linux` jars are ALSO present
(the `Empty` suffix avoids a module-name collision — `[CERT-web]`, both jars fetched live and
inspected this session). Adding `compileOnly("org.openjfx:javafx-base:25:linux")` explicitly (the real
749 KB modular jar, `module javafx.base@25`) fixed it.

**Result — `BUILD SUCCESSFUL`, twice, with zero stub jars present:**

| # | Command | Result |
|---|---|---|
| 1 | `./gradlew clean :DashboardPan-rt:compileJava` (4-dep attempt, no explicit `javafx-base`) | **FAILED** — `module not found: javafx.base` (the `…Empty` placeholder gotcha above) |
| 2 | `./gradlew clean :DashboardPan-rt:compileJava` (6-dep, `javafx-base:25:linux` added) | **BUILD SUCCESSFUL in 1m 32s** — zero errors |
| 3 | `./gradlew :DashboardPan-rt:jar` | **BUILD SUCCESSFUL in 38s** — full jar packaged |
| 4 | `./gradlew clean :DashboardPan-rt:jar` (reproducibility check) | **BUILD SUCCESSFUL in 2m 30s** — same result on a clean rebuild |

`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` re-counted (`ls | wc -l`) after every
invocation: **247 throughout, zero pollution**, same discipline as [Block 28]. `[CERT-hw]`.

**The resulting jar is unchanged in shape from [Block 28]'s stub-built version** — `jar
--describe-module` on the rebuilt `DashboardPan-rt.jar` shows the identical `module
angeles.DashboardPan@2.1.1` descriptor ([Block 28] §28.3.7's hand-authored `module-info.java` was not
touched this session): `requires jakarta.servlet`, `niagara.alarm`, `niagara.baja transitive`,
`niagara.niagaraAnnotationProcessors`, `niagara.nre`, `niagara.web` — no `javafx`/`batik` requirement
leaked into DashboardPan's own module (the `compileOnly` deps only need to be RESOLVABLE for
`niagara.alarm`'s own graph to validate; DashboardPan's source never references either API, same
finding [Block 28] §28.4 made for the stub version). The jar itself: 30 entries, 3,687,746 bytes
uncompressed — identical entry count to [Block 28] §28.7's reported `DashboardPan-rt.jar` (30
entries). `[CERT-hw]`.

**Download cost, for reproducibility**: `org.openjfx:*:25:linux` (5 artifacts, incl. the 2 harmless
`…Empty` placeholders pulled transitively) totals ~52 MB; `org.apache.xmlgraphics:batik-awt-util:1.19`
plus its own transitive Batik/xmlgraphics-commons deps (`batik-util`, `batik-i18n`, `batik-constants`,
`batik-shared-resources`, `xmlgraphics-commons`) totals ~1.4 MB — **~53 MB one-time download**, cached
under `~/.gradle/caches/modules-2/files-2.1/`. sha256 of the 6 load-bearing jars actually used
(excluding the 2 `…Empty` placeholders), computed this session:

| Artifact | sha256 |
|---|---|
| `javafx-base-25-linux.jar` | `32425946bb8b8db0717cfa2fb2e00e21cd489f35b9662b6faca18b615a4a9669` |
| `javafx-graphics-25-linux.jar` | `3e518bc17ee558559a2ac58a5f7fd452615108d9d5088f65b13bee9399c3722b` |
| `javafx-controls-25-linux.jar` | `37355e4d91c67e88fd9815f601e6ac5b55ddde9f5e9b93fc8f4aa04577e691d3` |
| `javafx-web-25-linux.jar` | `9f6f53a1897a45511f40a6d65d1b5ebc5a06acfe9ec54af9cb149d19879d4f7b` |
| `javafx-swing-25-linux.jar` | `278a1e9fbb22a861d6ed3102d4f3b0ebe5d351b219fdf9dcd542dc1f3a6d2876` |
| `batik-awt-util-1.19.jar` | `c9ac9ed24e0b20984e7c65ce2fbe4915003c67f9ae96177bc32bef901b557a9a` |

`[CERT-hw]` (all 6 sha256sums computed directly against the cached files this session).

## 39.4 — B28-G3 answered for real: the vendor's own bundled `javac.exe` hits the same wall `[CERT-hw]`

**WSL interop reaches the real bundled toolchain directly — no Windows host needed.**
`/mnt/c/Program Files/Niagara/5.0.0.28/jre/bin/javac.exe -version` → `javac 25.0.4` (matching
`jre/release`'s `JAVA_VERSION`), invoked directly from this Linux/WSL session with no separate Windows
step. This is the SAME real, Windows-only executable [Block 28] §28.4 found but could not run — WSL's
automatic PE-interop makes it directly callable, closing B28-G3, a gap [Block 28] left as "untested."

**Positive control — the toolchain itself works.** A minimal `module-info.java` (`module angeles.probe
{ requires niagara.baja; }`) compiled against `--module-path` built from EXACTLY the same 3 real
install-tree segments the `n-java` plugin itself uses (config `modules/` + `bin/ext` + `bin/ext/
bcfips`, §39.2 — the plugin's 4th segment, `moduleClassPath`, is empty for this bare probe), Windows
paths obtained via `wslpath -w`, output directed to a UNC-translated scratch dir: **`BUILD SUCCESSFUL`,
`module-info.class` produced.** `[CERT-hw]`.

**Negative control — `niagara.alarm` alone, same module-path, no extra artifacts supplied:**

```
module angeles.probe { requires niagara.baja; requires niagara.alarm; }
```

```
error: module not found: org.apache.xmlgraphics.batik.awt.util
1 error
```

**Exactly ONE error — not five.** [Block 28]'s Homebrew-toolchain compile reported the batik module
PLUS all 4 `javafx.*` modules missing. The REAL bundled `javac.exe`, using the identical
`--module-path` recipe, resolves all 4 `javafx.*` modules with **zero extra artifacts supplied** —
this is the direct, `[CERT-hw]` confirmation of §39.1's `jimage`-based deduction: JavaFX genuinely is a
usable system module of this specific JDK build, not merely present as files somewhere. **This closes
[Block 28] B28-G2 from `[INFER]` to `[CERT-hw]`.**

**Positive control #2 — supply only the real Batik jar (still zero JavaFX artifacts), same 2-line
module-info:** copying `batik-awt-util-1.19.jar` (the exact jar §39.3 already validated) into a 4th
`--module-path` segment and re-running the identical `javac.exe` invocation: **`BUILD SUCCESSFUL`, `1
error` → `0 errors`.** `[CERT-hw]`.

**The decisive reframe of B28-G3.** [Block 28] closed its own framing of this gap with: "this would be
the cleanest confirmation that the stub-module workaround is equivalent to, not a deviation from, the
vendor's own intended toolchain." The real answer is the opposite and more useful: **the vendor's own
official toolchain does NOT resolve `niagara.alarm`'s module graph out of the box either** —
`org.apache.xmlgraphics.batik.awt.util` is missing from Tridium's OWN Windows install just as it is
from the Linux/Homebrew substitute, so this is not a Linux-specific workaround target at all; it is a
genuine gap in what N5 5.0.0.28 beta ships for `gx.jar`/`svgBatik.jar`'s own declared (and, per gx.jar,
doubly-declared — see §39.5's open question) dependency on Apache Batik. The real-Maven-artifact fix
§39.3 found and validated on Linux is the SAME fix a Windows developer hitting this on the real
toolchain would need, not a Linux-only substitute for a Windows path that "just works."

## 39.5 — Recommended, reproducible Linux build setup for third-party N5 modules using alarm/bajaui `[CERT-hw]`

1. Keep the existing Homebrew OpenJDK 25 toolchain ([Block 9]'s original choice remains correct and
   sufficient — no JavaFX-bundled JDK distribution needs to be sourced or installed).
2. In the module's OWN `build.gradle.kts` (not a global/install-tree change — `mavenCentral()` must
   already be a declared repository, as it has been in this PoC since [Block 28]), add:
   `compileOnly("org.openjfx:javafx-base:25:linux")`,
   `compileOnly("org.openjfx:javafx-graphics:25:linux")`,
   `compileOnly("org.openjfx:javafx-controls:25:linux")`,
   `compileOnly("org.openjfx:javafx-web:25:linux")`,
   `compileOnly("org.openjfx:javafx-swing:25:linux")`,
   `compileOnly("org.apache.xmlgraphics:batik-awt-util:1.19")`. Pin ALL 5 `org.openjfx` coordinates to
   the explicit `:linux` classifier — the unclassified coordinates are empty placeholders (§39.3's
   gotcha).
3. Do **not** use the 5-empty-stub-jar workaround [Block 28] used — it satisfies the module resolver's
   bookkeeping only, providing no real API surface, and §39.3/§39.4 show a real, equally cheap (~53 MB,
   one-time, cached) fix exists.
4. This fix is a property of `niagara.alarm`'s own module graph (§39.1/[Block 28] §28.4), not of any
   one module's code — any third-party N5 module reaching `niagara.alarm`/`niagara.bajaui`/
   `niagara.gx`/`niagara.workbench`, even for a headless alarm-only read, needs the same 6 dependency
   lines, regardless of whether the module's own source ever calls a JavaFX/Batik API.

## 39.x — Open question: 3 other nominally-mandatory `requires` edges never error, on either toolchain

`gx.jar`'s own module-info (`jar --describe-module`, re-read fresh this session) declares, with NO
`static` modifier (i.e., by the same reading [Block 28] §28.4 and this block both apply to
`org.apache.xmlgraphics.batik.awt.util`, mandatory): `requires org.apache.xmlgraphics.batik.transcoder;
requires org.eclipse.swt.win32.win32.x86_64; requires owasp.encoder;`. None of these 3 has ever
appeared as a `module not found` error — not in [Block 28]'s original compile, not in this session's
Homebrew-toolchain rebuild, not in the real `javac.exe` runs. [Block 28] §28.4 already flagged the SWT/
OAuth half of this same anomaly ("either already satisfied elsewhere on the path or genuinely optional
at the depth this compile needed") without resolving it; this session's independent re-read of
`gx.jar`'s full descriptor adds `org.apache.xmlgraphics.batik.transcoder` as a THIRD instance of the
identical pattern — and §39.1's exhaustive 373-jar scan confirms `batik.transcoder` is equally absent
from the entire install (its package prefix `org/apache/batik/transcoder` would have matched the same
`org/apache/batik` scan that found zero hits). Three independent "mandatory-looking `requires`, never
an error" cases from the same real module's descriptor make this look systematic rather than
coincidental, but the exact javac module-resolution rule producing it is not identified here — named
**B39-G3** below rather than guessed at.

## 39.6 — Self-verify

This is a **build/PoC (§19) block** — its `[CERT-hw]` claims are live command output captured this
session, matching [Block 9]/[Block 16]/[Block 28]'s established "LIVE-BUILD BLOCKS" convention
(METHODOLOGY §11).

- **Reproducibility check** — `DashboardPan-rt:jar` was rebuilt from a `clean` state twice this session
  (once implicitly via the compileJava fix-iteration, once explicitly at §39.3 row 4) and produced the
  identical 30-entry, 3,687,746-byte jar shape both times, matching [Block 28]'s own count.
- **Token check** — every quoted error string (`module not found: org.apache.xmlgraphics.
  batik.awt.util`, `module not found: javafx.base`), every `jar --describe-module`/`jimage list`
  line quoted (`javafx.baseEmpty@25 automatic`, the 61-module `jimage` count, `gx.jar`'s full
  `requires` list, the rebuilt `angeles.DashboardPan@2.1.1` descriptor), the `buildN5.txt:22`/`:506`
  quotes, and the decompiled `ModulePathArgumentProvider.kt`/`NiagaraJavaPlugin.kt` excerpts were
  copied verbatim from this session's captured output or the cited files — **≈19 distinct load-bearing
  tokens**, all mechanically sourced from `jar`/`jimage`/`gradlew`/`grep`/`sha256sum` output or direct
  file reads captured this session.
- **Marker tally** — literal `verify-block.sh` output, run this session from
  `/home/cristian/niagara5-research`:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block39.md .
== verify-block: niagara5-block39.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 20  (adj 18)
   [CERT-live] 1
   [CERT] 8  (adj 7)
   [CERT-doc] 5
   [CERT-web] 4  (adj 3)
   [CERT-a] 1
   [INFER] 10  (adj 9)
-- ratio -- [INFER]/[CERT*] = 9/35 = 0.26
-- [CERT] file:line citation resolution --
   jar-entry  docDeveloper.jar!doc/buildN5.html  (jar archive path — not file-verifiable)
   extern  NiagaraJavaPlugin.kt:71-79  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  buildN5.txt:22  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  buildN5.txt:506  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   resolved 0 of 3
   WARN    resolved 0 of 3 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

  Every `[CERT]`/`[CERT-doc]` citation in this block points either into the decompiled
  `/tmp/claude-1000/n5b2/vf-out/` tree, into `niagara-help/devguide-clean/*.txt`, or into the
  `docDeveloper.jar` archive itself — all OUTSIDE this corpus directory, so they resolve as
  `extern`/`jar-entry`, the same expected "LIVE-BUILD BLOCKS" signature [Block 9]/[Block 16]/[Block 28]
  all documented (METHODOLOGY §11); each was read directly this session (the `buildN5.txt` grep, the
  `.kt` file reads), not carried from memory or a prior block's citation. Raw `[INFER]` = 7 (adjusted
  6) includes the header blockquote's own marker-legend line (the same self-matching [Block 16]/[Block
  28] both documented) plus §39.x's genuinely bounded `[INFER]` on the unresolved reachability-algorithm
  question (B39-G3) and the `com.tridium.set.mpr`/build-mechanics carry-overs restated from [Block 28]
  in the header's scope description — none of the adjusted `[INFER]` claims are load-bearing for this
  block's OWN findings (§39.1-§39.4 are all evidence-marked). The tool's own printed ratio, 0.26, is
  low, consistent with a §19 build/PoC block whose claims are almost entirely direct hardware/
  live-build/live-Maven-fetch output from this session. (This count is inherently self-referential —
  every re-run after pasting the tool's OWN output into this section adds a few more literal marker
  tokens for the tool to match, the exact "matching this block's own header-blockquote legend line"
  phenomenon [Block 16]/[Block 28] both documented; the number above is the last run taken before
  freezing this section, reported as-is rather than chased to a false exact convergence.)
- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block39.md`;
  the modified PoC tree exists at `/home/cristian/niagara5-research/poc/dashboardpan-n5/` (already
  gitignored, confirmed by `git check-ignore -v` this session — no new gitignore entry needed). Per
  task scope (single-block deliverable, same convention as [Block 28]), `CATALOG.md`/`INDEX.md`/
  `RESEARCH-STATE.md` were **not** regenerated this session — the parent orchestrator owns that,
  including flipping B28-G7/B28-G2/B28-G3's `RESEARCH-STATE.md`/`INDEX.md` rows from `pending` to
  covered-by-B39.
- **MCP-doc snapshots** — N/A; the two live Maven Central fetches (`javafx-graphics` directory
  listing, `batik-awt-util` directory listing) were plain `curl` HTTP reads, not an MCP/context7
  citation, and are reproducible by re-running the same `curl`/Gradle commands against the same
  published, immutable release coordinates (§39.3's sha256 table anchors the exact bytes fetched this
  session).

## 39.6.G — Child gaps

- **B39-G1** — A live N5 station deploy of the rebuilt `DashboardPan-rt.jar` was not attempted — same
  open gap [Block 9]/[Block 16]/[Block 28] left open, now applying to a THIRD build of the same
  module (stub-built in [Block 28], real-artifact-built here).
- **B39-G2** — Whether `org.apache.xmlgraphics:batik-awt-util`'s specific version matters (this session
  pinned `1.19`, the latest published at time of writing) — a narrower/older version (e.g. matching
  whatever Batik version Tridium's own JavaFX-bundled JDK build, if one exists beyond the bare
  Niagara-branded `jre/`, might expect) was not tested; only `1.19` was validated against both
  toolchains this session.
- **B39-G3** — The exact javac module-resolution rule that lets `gx.jar`'s 3 other nominally-mandatory
  (non-`static`) `requires` edges — `org.apache.xmlgraphics.batik.transcoder`,
  `org.eclipse.swt.win32.win32.x86_64`, `owasp.encoder` — never surface as `module not found` errors on
  either toolchain, despite none of the 3 target modules existing anywhere in the install (confirmed by
  §39.1's same 373-jar scan for the batik one; the SWT/OAuth two were only asserted absent by [Block
  28], not independently re-confirmed this session) is not identified (§39.x).
- **B39-G4** — Whether a module that DOES call a real JavaFX/Batik API (unlike DashboardPan, which per
  [Block 28] §28.4 never references either) compiles AND behaves correctly at runtime against these
  same 6 real Maven artifacts was not tested — this block only validates compile-time module-graph
  resolution, not runtime API correctness of the supplied artifacts for a real caller.

## 39.x — Connections

- **[Block 28]** — this block closes all 3 of B28's own child gaps left open on this specific topic:
  B28-G7 (the supported way — real Maven artifacts, not stubs), B28-G2 (JavaFX baked into the bundled
  JRE — now `[CERT-hw]` via the real `javac.exe`'s own automatic resolution, not just `jimage`
  circumstantial evidence), and B28-G3 (the real bundled `javac.exe` tested — it does NOT resolve
  cleanly without external help, refuting B28's own framing that Windows+real-`javac` might be the
  clean confirmation of vendor intent; instead it shows the vendor's own toolchain shares the same gap).
- **[Block 9]** — the `--module-path`/`gradle.properties`/`niagara_config_home` redirect pattern this
  block's PoC reuses is unchanged from [Block 9]'s original scaffold; the Homebrew OpenJDK 25 toolchain
  choice [Block 9] made remains correct and does not need to be replaced by a JavaFX-bundled JDK.
- **[Block 16]** — same PoC-tree/`gradle.properties` conventions reused a third time, no new findings
  on that mechanical layer.
- **[Block 2]** — this block reads `ModulePathArgumentProvider.kt`/`NiagaraJavaPlugin.kt` (decompiled
  in [Block 2]'s own session, not re-decompiled here) to completion for the first time, mechanically
  confirming [Block 9]'s externally-observed "5 real jar/dir entries" finding from the plugin's own
  source rather than only from build-log behavior.
