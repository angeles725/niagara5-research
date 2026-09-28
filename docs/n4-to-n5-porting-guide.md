# N4 → N5 Porting Guide

Practical, ordered guide for porting our custom Niagara N4 modules (ColdRoomPan, CompPan,
DashboardPan — and any future module built with the `build-n4-module` kit) to Niagara N5
5.0.0.28, and for migrating a station (PANCCADIA) from N4 to N5.

Audience: an engineer who is actually going to sit down and do this. Every rule below cites
its source block as `[Bn §x.y]` — open `niagara5-blockN.md` in this corpus for the full
evidence, decompiled code, and certainty marker behind any claim.

Subject version throughout: **N5 5.0.0.28 (Beta)**, JRE 25.0.4.7, vs. baseline **N4
4.14.0.162** (Honeywell OptimizerSupervisor OEM) / PANCCADIA's real **N4 4.15** station.

---

## 1. One-screen summary

**The rename is total but mechanical.** Every `javax.baja.*` import becomes `niagara.*`
(zero exceptions found; `com.tridium.*` is untouched) with **no Java compatibility shim** —
only bog-file/program-source-text converters exist, and only for migrating *saved station
data*, not for compiling your `.java` [B5 §5.1, §5.5][B14 §14.6]. Budget one `sed` pass per
module plus a handful of real signature deltas (below).

**Module packaging changed, not your code's logic.** N4's `-rt`/`-ux`/`-wb`/`-se`/`-doc`
JAR-per-part split is gone; N5 ships one JAR per module with `schemaVersion="5"` and a real
JPMS `module-info.class` [B1 §1.2–§1.3]. `module-permissions.xml` is gone, replaced by
`@Grant*` annotations on `module-info.java` [B8 §8.2][B10 §10.5]. Slotomatic itself is
**unchanged** — same tool, same "BAJA AUTO GENERATED CODE" markers, same disconnected
Gradle task you must still run by hand before `jar`/`compileJava` [B7 §7.4][B9 §9.3].

**All three of our modules build and jar successfully on N5 5.0.0.28** — this is proven,
not theoretical: ColdRoomPan-rt [B16], CompPan-rt and DashboardPan-rt (merged from its
N4 3-part split) [B28] all compiled, jarred, and signed with the shipped Gradle plugins.

**Decision list — what you must decide before you start:**

| Decision | Recommendation | Why |
|---|---|---|
| Where does `niagara_config_home` point during any build? | A **local mirror** of symlinks, never the real `/mnt/c/.../config/5.0.0.28` | The `jar` task silently **installs** the built jar into whatever `modules/` dir `niagara_config_home` resolves to — pointing it at a shared/real install pollutes it on every build [B16 §16.3]. |
| Which JDK builds the module? | Any JDK 25 (a plain Homebrew/Temurin JDK 25 is fine) | The `n-java` plugin's `--module-path` never references the JRE directory at all; JavaFX/Batik come from Maven, not the JDK [B39 §39.2]. |
| Does a module touching `niagara.alarm`/`bajaui`/`gx`/`workbench` need stub jars? | **No** — declare 6 real `compileOnly` Maven dependencies instead | Stub jars satisfy the resolver but ship no API; the real fix is ~53 MB, cached, and is what a Windows/vendor toolchain needs too [B39 §39.3, §39.5]. |
| Do our N4 JUnit4 tests port as-is? | No — port to TestNG with a paren-aware script, not `sed` | Argument order/position differs per assertion; N5 ships TestNG, not JUnit4, in its `test` module [B16 §16.5.2][B29 §29.1–§29.2]. |
| Can `niagaraTest` actually run in this environment? | Not on Linux/WSL, and not on this *unlicensed* beta install at all (any OS) | `bin/test` is Windows-only (`test.exe`) **and** every headless Niagara tool on this install (`n5mig`, `station`, `test`) hits a `tridium:nre` `FeatureNotLicensedException` [B16 §16.5.4][B29 §29.6][B17 §17.2]. Use the plain-TestNG fallback (§4 below) for logic confidence today. |
| Does a servlet write need an explicit `Context`? | **Yes, always**, for any externally-triggered write | Slotomatic-generated setters/invokers hard-code `null` for `Context` — **3,589 of them**, corpus-wide — and are therefore never audited if called directly [B49 §49.1–§49.2]. |
| Must our 3 modules be installed on the target N5 box before running `n5mig`? | **Yes, before every real migration run** | An unresolvable module's bog objects are **silently stripped** (`BModuleRemovalConverter`), not skipped or flagged [B14 §14.5][B17 §17.5–§17.7]. |
| Will PANCCADIA's `kitControl`/`tagdictionary`/`nrio` objects need a converter? | No — they load byte-identical, unconverted, by design | 315 of PANCCADIA's real objects checked; zero removed slots [B24 §24.6][B31 §31.7]. |
| Does a module need new code before it can sit in a `niagaraSync` HA folder? | Yes — every `Clock.Ticket`/plain interlock field becomes a `BNiagaraSyncTicket`/hidden Property; a working reference port already exists | A real ColdRoomPan-rt HA refactor (3 classes, 8 timers, 9 interlock fields, 1 FIFO) builds clean and passes 55/55 tests plus every static validator admission rule — only a *live* two-station failover is unverified [B45 §45.3–§45.6]. |

---

## 2. Module porting procedure, step by step

This is the procedure validated end-to-end on ColdRoomPan-rt [B16], CompPan-rt and
DashboardPan-rt [B28], plus the JavaFX/Batik fix [B39] and the audited-write fix [B46][B49].
Follow it in this order.

### 2.1 — Set up the build environment (do this once)

`gradle.properties` — **critical**: `niagara_config_home` must be a **local mirror**, never
the real install directory, or the `jar` task will write your module's built JAR straight
into the shared install every time you build [B16 §16.3]:

```properties
niagara_home=/mnt/c/Program Files/Niagara/5.0.0.28
# NEVER point this at the real config/modules directory — the jar task PUBLISHES into it.
niagara_config_home=/path/to/your/poc/.n5config
niagara_user_home=/path/to/your/poc/.niagara_user_home
org.gradle.java.installations.paths=/path/to/a/jdk-25
```

Build the local mirror once (symlinks, not copies — resolution needs the real jars, writes
must land locally):

```bash
mkdir -p "$MIRROR/modules"
ln -sf "$NIAGARA_CONFIG_HOME/modules/"*.jar "$MIRROR/modules/"
```

Use the Gradle wrapper bundled inside `devkit.jar!LIB-INF/n-templates-*.jar` — it ships a
complete `gradle-wrapper.jar`/`.properties`/`gradlew`; no manual Gradle download is needed
[B9 §9.1]. Any JDK 25 works as the build JDK (Homebrew/Temurin is fine) — the JRE bundled
with Niagara is JRE-only in this beta for the Linux/WSL path relevant here [B9 header],
though it does ship a Windows-only `jre/bin/javac.exe` too [B39 §39.4].

### 2.2 — Rewrite the plugin ids and manifest DSL

Every N4 `<part>.gradle.kts` uses this plugin block — rename per the table, and add
`com.tridium.n-java` explicitly (the wizard's own default template omits it, which is a
trap — without it `--module-path` is never set and you'll misdiagnose the resulting error
as a namespace problem) [B2 §2.2][B9 §9.4]:

| N4 plugin id | N5 plugin id |
|---|---|
| `com.tridium.niagara-module` | `com.tridium.n-module` |
| `com.tridium.niagara-signing` | `com.tridium.sign` |
| `com.tridium.niagara-jacoco` | `com.tridium.jacoco` |
| `com.tridium.niagara-grunt` | `com.tridium.grunt` |
| `com.tridium.niagara-annotation-processors` | **removed** — replace with `com.tridium.n-helper-modularity` |
| `com.tridium.convention.niagara-home-repositories` | `com.tridium.conv.n-repo` |
| `com.tridium.settings.multi-project` | `com.tridium.set.mpr` |
| `com.tridium.settings.local-settings-convention` | `com.tridium.set.lsc` |
| `com.tridium.settings.niagara` | `com.tridium.set.niagara` |

`[B2 §2.2][B10 BC-25]`

```kotlin
// <module>.gradle.kts — final shape, e.g. ColdRoomPan-rt
plugins {
  id("com.tridium.n-module")
  id("com.tridium.n-helper-modularity")
  id("com.tridium.n-java")              // ADD — not in the wizard's own default list, [B9 §9.4]
  id("com.tridium.sign")
  id("com.tridium.bajadoc")
  id("com.tridium.jacoco")
  id("com.tridium.nap")
  id("com.tridium.conv.n-repo")
}
moduleManifest { moduleName.set("ColdRoomPan"); checkModuleName.set(false) }
dependencies {
  nre(":niagaraAnnotationProcessors")     // SPLIT from nre — was implicit in N4, [B2 §2.6]
  nre(":nre")
  niagaraAnnotationProcessor(":niagaraAnnotationProcessors")
  api(":baja")
}
```

Delete the `moduleManifest { runtimeProfile.set(rt) }` line and its `RuntimeProfile`
import — the extension is simplified to just `moduleName.set(...)` [B10 §10.3 step 9].
Drop the parent `niagara-module.xml` entirely — even a multi-part group's grouping file is
**not needed at all** in N5; `com.tridium.set.mpr`'s `findProjects()` auto-discovers every
subproject with no grouping XML anywhere [B16 §16.4 CHK-7][B28 §28.3.5, closes B16-G2].

### 2.3 — Write `src/module-info.java`

Entirely new, hand-authored (or wizard-generated) per module/part folder:

```java
module angeles.ColdRoomPan {
  requires transitive niagara.baja;
  requires niagara.nre;
  requires niagara.niagaraAnnotationProcessors;
}
```

`[B2 §2.7][B16 §16.2 step 3]`. Module naming is `<vendor>.<moduleName>`; every Niagara
dependency in the `.gradle.kts` needs a matching `requires niagara.<x>;` (confirm exact JPMS
module names with `javap -v` on the dependency's `module-info.class` — do not guess; e.g.
`niagara.alarm`, `niagara.web`, not `niagara.Alarm`) [B28 §28.3.7].

### 2.4 — Rewrite the source: the `javax.baja.*` → `niagara.*` rename

One global substitution, run per file, is **sufficient** for a module that does not touch
the handful of renamed *members* below (§2.5) — a real ColdRoomPan port needed zero manual
fixups beyond this [B16 §16.2 step 2]:

```bash
sed -e 's/javax\.baja\./niagara./g' -e 's/javax\/baja\//niagara\//g' <src> > <dest>
```

There is **no Java-level compatibility shim** for the old namespace — only bog-file
type-spec strings and embedded `BProgram` source text get rewritten by the migrator tooling
at *station-migration* time, not at compile time [B5 §5.5][B14 §14.6]. A file that still
`import javax.baja.sys.*;` will not compile against N5 at all [B9 §9.2].

If the module touches servlets, also rename the servlet namespace (§2.6).

### 2.5 — Fix the real signature deltas (only where your code actually calls them)

These are the confirmed, non-cosmetic API changes in the core packages our modules use
[B5 §5.3][B10 §10.4 BC-01, BC-04, BC-05, BC-06]:

| N4 | N5 | Where it bites |
|---|---|---|
| `Sys.getLanguage()`/`setLanguage(String)`, `Context.getLanguage()` | `getLanguageCode()`/`setLanguageCode(String)` | any i18n call |
| `BObject`'s `equals(Object)` override | **removed** — falls back to identity equality | a subclass that relied on `BObject`'s override instead of declaring its own |
| `javax.baja.log.Log` (whole package) | **fully removed**, not deprecated — use `java.util.logging.Logger` | any leftover `Log.getLog(...)` call; N4's own `getLog()` convenience methods on `BDeviceNetwork`/`BDevice` are gone, not just marked `@Deprecated` [B22 §22.3] |
| `BAbstractDescriptor.isUnoperational()` | `isNonOperational()` + new paired `isOperational()` | driver code overriding/calling operational status |
| `Type`/`TypeInfo`.`getRuntimeProfile()`, `BModule.getRuntimeProfile(FilePath)`/`getRuntimeProfiles()` | **removed**, no replacement — the module-part concept is gone | any reflective code checking a module's runtime profile |
| `Clock` — public class, public constructor | `final class`, **private** constructor — cannot be instantiated/subclassed | code that ever `new Clock()`'d (uncommon) |
| `BWebServlet`'s `javax.servlet.*` types | `jakarta.servlet.*` | any servlet subclass (§2.6) |

Grep for each token before assuming it applies — none of these hit ColdRoomPan, CompPan, or
DashboardPan directly except the servlet rename [B16 §16.2 step 2][B20 §20.8][B22 §22.2].

`Clock.schedule()`/`schedulePeriodically()`'s `time<=0`/`period<=0` validation is
**unchanged** — the `positiveDelayMs()`/`intervalDelayMs()` floor already shipped for the
ColdRoomPan defrost-timer bug (client `c66e412`) is still necessary and sufficient after
porting; the crash class is not fixed upstream [B20 §20.2]. What *did* change: `Clock.ticks()`
now reads `System.nanoTime()` directly instead of a platform-provider tick counter — this is
why HA-relevant tick state was promoted to a new `BNiagaraSyncTicks` wrapper type (§2.10)
[B20 §20.2, §20.7][B37 §37.4].

### 2.6 — `jakarta.servlet` migration (only if the module has a `-ux`/servlet part)

Confirmed a namespace-only rename with **zero call-site changes** for our servlet code —
every `HttpServletResponse.SC_*` constant, every `getParameter`/`setHeader`/`getWriter`
call compiled unchanged [B28 §28.5]:

```bash
sed 's/javax\.servlet\./jakarta.servlet./g' <src> > <dest>
```

```kotlin
// gradle.kts
compileOnly("jakarta.servlet:jakarta.servlet-api:6.1.0")   // was javax.servlet:javax.servlet-api:3.1.0
```

Confirm no `jetty-web.xml` exists in the module (none of ours do) — if one did, it would
also need the `ee11`-namespace `Configure` class fix [B10 §10.11 CHK-3][B28 §28.5].
`niagara.web.BWebServlet`'s own `doGet(WebOp)`/`doPost(WebOp)` shape is unchanged; `WebOp`
already returns `jakarta.servlet.*` types from `getRequest()`/`getResponse()` [B28 §28.5].

### 2.7 — Merge multi-part modules (DashboardPan-style, `rt`+`ux`+`wb`)

Only needed if `niagara-module.xml` declares more than one `runtimeProfiles` letter — a
single-part module (ColdRoomPan, CompPan) skips this entirely [B10 §10.10, CHK-1].

1. Pick the highest-precedence part as destination: `rt(4) > ux(3) > wb(2) > se(1)`
   [B10 §10.3 step 3].
2. Merge source trees into one `src/` (JPMS modules span multiple packages freely — no
   package unification needed) [B28 §28.3.1].
3. **`-wb` frequently contributes zero source** — check `find` before assuming work exists;
   DashboardPan's own `-wb` part was build/manifest files only [B28 §28.3].
4. Delete the now-intra-module `api(project(":Module-ux"))`-style dependency outright — a
   plain-Java cross-package reference inside one compilation unit needs no build-time
   indirection [B28 §28.3.2].
5. Strip every `-rt`/`-ux`-suffixed cross-module dependency (`api(":alarm-rt")` →
   `api(":alarm")`), and **check whether the dependency is actually used** before keeping it
   — DashboardPan's declared-but-unconsumed `api(":control-rt")` was correctly dropped
   entirely, not just renamed [B28 §28.3.4].
6. Merge `module-include.xml`/`module.lexicon`/`module.palette` by concatenation (or just
   start `module-include.xml` empty — the annotation processor regenerates it, §2.8)
   [B28 §28.3.6].
7. Do not copy the parent `niagara-module.xml` at all (§2.2).

### 2.8 — `module-permissions.xml` and `module-include.xml`

**Delete `module-permissions.xml` outright.** N5 has no XML permission-declaration element
at all; permissions are `@Grant*` annotations on the `module-info.java` module declaration
[B8 §8.2][B10 §10.5]. All three of our modules had every `<req-permission>` already
commented out, so this is a pure deletion with no annotation work needed
[B10 §10.11 CHK-8][B16 §16.4].

Only **4 Grant annotations are usable by a genuinely third-party module** — the other 3
(`@GrantFilePermission`, `@GrantKeyRingPermission`, `@GrantNiagaraBasicPermission`) live in
a restricted `com.tridium.*` package and are silently dropped for any module whose JPMS
name doesn't start with `com.tridium.`/`niagara.` [B8 §8.1]:

```java
@GrantKeyStorePermission(name = "userKeyStore", actions = "read")
@GrantPublicNiagaraBasicPermission(MANAGE_SERVER_TRUST_ANCHORS)
@GrantRuntimeExecPermission(value = "/usr/bin/ffmpeg", type = STATION)
@GrantSigningPasswordPermission("myAlias")
module myCompany.myModule { ... }
```

**Practical implication for file/network I/O** — a third-party module cannot request
`@GrantFilePermission` at all; it is confined to the always-granted shared-directory
allowlist (`${niagara.user.home}/shared/-`, `logging/-`, read-only `modules/-` etc.)
[B8 §8.8]. **Outbound sockets/HTTP are effectively ungated** — `NetworkConnectionAdvice`
only audits, never calls `checkPermission` — so no `PermissionException` will stop an
outbound call, but this is not something DashboardPan currently exercises (it makes no
outbound call at all) [B8 §8.8][B28 §28.1 correction].

**`module-include.xml`/`moduleTest-include.xml` are auto-generated.** Start them empty
(`<types></types>`) and let the `NiagaraTypeAnnotationProcessor` regenerate them on build —
the write is idempotent, package-grouped, and self-healing; no hand-merge is needed, even
across a multi-part merge [B7 §7.2–§7.3][B10 §10.11 CHK-9][B16 §16.4 CHK-9]
[B28 §28.3.6].

### 2.9 — Run Slotomatic, then build — in that order, manually

Slotomatic is **unchanged** in mechanism from N4 — same class
(`com.tridium.slottool.Slotomatic`), same `BAJA AUTO GENERATED CODE` region markers, and it
is **not wired into the `compileJava`/`jar` task graph** — the Gradle dry-run task graph is
literally `compileJava → processResources → classes → writeModuleXml → jar`, with
`slotomatic` absent [B7 §7.4][B9 §9.3]. The `NiagaraSlotProcessor` (NOT N5-only: N4.14.0.162 and N4-4.15.3.28 ship it as
`javax.baja.nre.annotations.processors.NiagaraSlotProcessor` in `bin/ext/nre.jar`; N5 relocates it to module
`niagaraAnnotationProcessors.jar` as `niagara.nre.annotations.processors.NiagaraSlotProcessor` — verified by
`unzip -l` over all jars of the three installs, 2026-09-28) validates that
slot fields exist (emitting `"...have you run slot-o-matic?"` if not) but generates zero
code itself [B7 §7.6].

```bash
./gradlew :ColdRoomPan-rt:slotomatic   # required before a fresh/changed module compiles
./gradlew :ColdRoomPan-rt:jar
```

An already-Slotomatic'd, unchanged module (i.e. a straight N4→N5 port with no new
properties/actions) needs **no re-run at all** — the compiled AP validates existing
generated code by slot *name*, not by hash stamp, so a first `jar` attempt can succeed
outright without a separate `slotomatic` step [B16 §16.5.1].

### 2.10 — If the module needs to survive HA failover (niagaraSync)

Flag this only if a module is placed inside a `BINiagaraSyncFolder`. The framework
validator (`NiagaraSyncComponentSpaceValidator`) will **reject** any complex type at
commit time that doesn't implement the marker interface, so this is not optional once HA
is in play [B37 §37.6]:

1. Implement `BINiagaraSyncCapableComplex` on every mounted type, recursively including
   every child type (the container itself, not just its leaf children with timers)
   [B37 §37.6][B45 §45.3].
2. Store all meaningful state as Niagara **Properties**, never private Java fields — a
   private field is invisible to both the initial-sync tree serializer and the live
   event-subscriber mask, so it simply never replicates.
3. For a deferred/scheduled *action*, replace the bare field with a `BNiagaraSyncTicket`
   child Property (`flags = READONLY | TRANSIENT | HIDDEN | DEFAULT_ON_CLONE`) instead of
   a raw `Clock.Ticket` — `Clock.Ticket` is a pure in-JVM construct, invisible to
   replication; a bare `Clock.schedule()` timer is silently lost on failover. The idiom,
   at every call site, is *cancel-then-replace*, matching stock `kitControl.timer.
   BBooleanDelay`: `getXTicket().cancel(); setXTicket(BNiagaraSyncTicket.make(delay,
   action, arg));` — the cancel is self-guarding (no `null` check needed) and the getter
   never returns Java `null` [B45 §45.2–§45.3].
4. Promote every other plain interlock/hysteresis field (booleans, ints, edge-detect
   memory) to a hidden Property the same way — `@NiagaraProperty(..., flags = READONLY |
   TRANSIENT | HIDDEN | DEFAULT_ON_CLONE)` [B45 §45.3].
5. For a **periodic** re-arming timer that just needs to keep firing (not a one-shot
   deadline tied to a specific resume moment), the stock precedent (`kitControl.
   BLoopPoint`) leaves it a plain field, unconditionally re-armed in `started()` — only
   promote the *deadline-shaped* state (e.g. `BNiagaraSyncTicks`), not the periodic ticket
   itself. Check each timer's shape before promoting it wholesale [B45 §45.2].
6. For a variable-length queue (a FIFO of pending work), niagaraSync ships **no
   list/queue-typed `BSimple`** — encode it as a comma-separated `String` Property via a
   pure parse/format codec extracted into a testable helper class, not a parallel in-memory
   `Deque` that could drift from what's actually replicated [B45 §45.3].
7. A same-tree back-reference that is a **redundant cache** of state another Property
   already carries (e.g. "which sibling is currently active", already encoded by that
   sibling's own now-synced index Property) can stay a plain field — but only if it is
   re-derived from the synced Property inside `started()`, so a promoted station rebuilds it
   correctly instead of silently losing it [B45 §45.3].

**A working reference port exists for ColdRoomPan-rt** — all 3 component classes
(`BColdRoom`, `BDefrostController`, `BEvaporatorUnit`), 8 `Clock.Ticket` timers and 9 plain
interlock fields migrated per the pattern above. It **builds clean** (`jar` and
`moduleTestJar` both `BUILD SUCCESSFUL`) and **passes 55/55 tests** — the 51 pre-existing
pure-logic tests unchanged, plus 4 new tests for the CSV queue codec, including a
mutation-kill proof that the new tests are not vacuous — and a static walk of every rule
`NiagaraSyncComponentSpaceValidator` enforces confirms the refactored tree would be
**admitted**, not rejected, by the framework [B45 §45.4–§45.6]. What this does **not**
prove: a *live* two-station pair actually resuming a mid-defrost cycle correctly on
failover (timer deadlines, FIFO hand-off, the back-reference restore in `started()`) — no
licensed N5 station was available to test this; it remains the single largest open item
for HA readiness [B37 B37-G1, B37-G3][B45 §45.7, B45-G1]. Treat this reference port as a
starting point for a real product change, not as itself an authorized change to the live
client module (see §6).

### 2.11 — Building against `niagara.alarm`/`bajaui`/`gx`/`workbench` on Linux

Any third-party module needing even a headless alarm read (`BAlarmRecord`, `BITable` query)
hits a **compile-time** wall: `niagara.alarm`'s module graph has a hard, non-`static`
transitive dependency on 5 platform modules (`javafx.{graphics,swing,controls,web}`,
`org.apache.xmlgraphics.batik.awt.util`) that are **not shipped as separate artifacts
anywhere in the N5 5.0.0.28 install** — they only exist baked into Tridium's own bundled,
JavaFX-capable JRE, and even the vendor's own Windows `javac.exe` does **not** resolve
`batik.awt.util` out of the box either [B28 §28.4][B39 §39.1, §39.4]. This is a genuine
gap in the shipped module graph, not a Linux-only problem.

**Do not use empty stub `module-info` jars** (they satisfy the resolver's bookkeeping only,
provide no real API surface, and are not what a Windows developer would need either). The
supported fix is 6 real `compileOnly` Maven dependencies [B39 §39.3, §39.5]:

```kotlin
compileOnly("org.openjfx:javafx-base:25:linux")        // pin :linux EXPLICITLY —
compileOnly("org.openjfx:javafx-graphics:25:linux")     // the unclassified coordinate is an
compileOnly("org.openjfx:javafx-controls:25:linux")     // intentionally-empty ~300-byte
compileOnly("org.openjfx:javafx-web:25:linux")          // placeholder jar and will fail
compileOnly("org.openjfx:javafx-swing:25:linux")        // with "module not found: javafx.base"
compileOnly("org.apache.xmlgraphics:batik-awt-util:1.19")
```

~53 MB one-time download, cached under `~/.gradle/caches/`. None of this leaks into the
module's own `module-info.java requires` list — `compileOnly` only needs to be resolvable
for `niagara.alarm`'s own graph to validate [B39 §39.3]. Three other nominally-mandatory
`requires` edges on `gx.jar` (`batik.transcoder`, `org.eclipse.swt.win32.win32.x86_64`,
`owasp.encoder`) never surface as errors on either toolchain, for reasons not fully
understood — treat as a known benign anomaly, not a blocker [B39 §39.x, open question].

### 2.12 — Tests: port JUnit4 → TestNG, don't `sed` it

N5 ships **TestNG**, not JUnit4, in its `test` module — an N4 module's `srcTest` copied
verbatim fails to compile (`package org.junit does not exist`) [B16 §16.5.2]. A naive
prefix-only rename also fails to compile, because the **message-argument position differs**
between the two frameworks for the majority of real assertion calls (`assertTrue(msg,
cond)` → `Assert.assertTrue(cond, msg)` — message moves from first to last; `assertEquals`
additionally swaps expected/actual) [B29 §29.1]. In one real 117-assertion sample, 58 of 98
`assertTrue`/`assertFalse` calls (59%) carried a message and would have produced a compile
error, not a silent misbehavior, under a naive rename [B29 §29.1].

Use a paren/string-aware port script — `tools/port-junit4-to-testng.py` in this corpus's
`poc/coldroompan-n5/` PoC does this correctly (hand-rolled comma-splitter that tracks
nesting and string-literal boundaries so a nested-call argument list reorders correctly)
[B29 §29.2].

```kotlin
moduleTestImplementation(":test")
moduleTestImplementation("org.testng:testng:7.12.0")   // REQUIRED explicitly — the version
                                                          // bundled inside test.jar's LIB-INF
                                                          // is NOT exposed transitively
```

`[B16 §16.5.3]` (pin the version from the shipped `libs.versions.toml`, currently `7.12.0`).
Only extend `niagara.test.BTestNg` when the test actually touches `BObject`/`BComponent`
reflection (its classloader-safety reason does not apply to a pure-Java seam test)
[B16 §16.6][B29 §29.3].

`assertArrayEquals` has **no direct TestNG equivalent name** (only an overloaded
`assertEquals` for arrays) — the port script does not implement this case; add it by hand
if your test suite uses it [B29 §29.1, B29-G3].

### 2.13 — Audited writes: always pass the request `Context`

Every Slotomatic-generated property setter and action invoker hard-codes `null` for the
trailing `Context` argument — **3,589 generated setters, corpus-wide**, confirmed by a
whole-tree census, and the *only* signature the generator ever emits (no `Context`-taking
overload exists, or is planned) [B49 §49.1–§49.2]. `ComponentSlotMap`/`ComplexSlotMap`'s
audit gate is `context != null && context.getUser() != null` — unchanged from N4 — so any
write made with `null` is **silently unaudited**, not merely unattributed [B41 §41.4]
[B49 §49.6].

Tridium's own transports (Fox, BOX/BajaScript, `@NiagaraRpc`, the generic `OrdServlet`) all
recover a real per-request `Context` and call the raw `set(prop, value, cx)`/
`invoke(action, arg, cx)` overload directly — never the generated convenience member
[B41 §41.6–§41.7][B49 §49.3–§49.5]. A third-party servlet must do the same:

```java
// niagara.web.filters.ContextFilter already populated this request attribute
// before your servlet ever runs (after Jetty's SecurityHandler finishes auth).
Context cx = (Context) req.getAttribute("niagara.context");
parent.set(prop, toSet, cx);      // NOT: parent.set(prop, toSet, null);
```

`[B41 §41.7][B46 §46.2–§46.3]` — verified this fixes the DashboardPan servlet write path:
rebuilt clean, and `javap -p -c` on the rebuilt class confirms `aload_3` (the real `cx`
parameter) reaches the `set()` call instead of `aconst_null` [B46 §46.4]. Prefer
`@NiagaraRpc` with a declared `Context` parameter where the RPC shape fits — the dispatcher
injects the real context with no manual recovery code [B49 §49.5–§49.6]. Reserve the
generated single-argument setter for genuinely internal, in-JVM state transitions with no
external actor.

---

## 3. Troubleshooting table

| Symptom | Cause | Fix | Source |
|---|---|---|---|
| `error: package javax.baja.sys does not exist` | N5's `baja` module exports zero `javax.*` packages — total rename | `sed` rename per §2.4; if it persists after the rename, check `com.tridium.n-java` is applied (next row) | `[B9 §9.2]` |
| Same error, **after** the rename is already applied | `com.tridium.n-java` missing — the wizard's own `modulePlugins.vm` default omits it; without it `--module-path` is never set on `javac` | Add `id("com.tridium.n-java")` to the module's `plugins {}` block | `[B9 §9.4]` |
| `error: Slot with name X not found on class Y; have you run slot-o-matic?` | `NiagaraSlotProcessor` validates slot fields exist but generates none itself | `./gradlew :module:slotomatic`, then rebuild | `[B7 §7.6][B9 §9.3]` |
| A stray `<ModuleName>.jar` mysteriously appears inside the real, shared N5 install's `modules/` dir | The `jar` task publishes the built jar into whatever `niagara_config_home` resolves to, as a flat-file-repo convenience | Point `niagara_config_home` at a local mirror, never the real install (§2.1) | `[B16 §16.3]` |
| `error: module not found: javafx.graphics` / `javafx.swing` / `javafx.controls` / `javafx.web` / `org.apache.xmlgraphics.batik.awt.util` compiling a module that needs `niagara.alarm`/`bajaui`/`gx`/`workbench` | These 5 platform modules are not shipped as separate N5 artifacts; needed transitively even for a headless alarm read | Add 6 real `compileOnly` Maven deps (§2.11) — not stub jars | `[B28 §28.4][B39 §39.1, §39.3, §39.5]` |
| `error: module not found: javafx.base`, even with the 4-5 other openjfx deps declared | The unclassified `org.openjfx:javafx-base:25` Maven coordinate is an intentionally-empty ~300-byte placeholder | Pin the explicit `:linux` classifier on every `org.openjfx:*` coordinate | `[B39 §39.3]` |
| `error: package org.junit does not exist` | N5 ships TestNG, not JUnit4, in its `test` module | Port with `port-junit4-to-testng.py`, not `sed` (§2.12) | `[B16 §16.5.2][B29 §29.1]` |
| `error: package org.testng does not exist`, despite `moduleTestImplementation(":test")` declared | TestNG is bundled inside `test.jar`'s `LIB-INF/`, not exposed as a transitive dependency | Add `moduleTestImplementation("org.testng:testng:7.12.0")` explicitly | `[B16 §16.5.3]` |
| `niagaraTest` fails: `Cannot run program ".../bin/test" ... No such file or directory` | `bin/test` is a Windows PE executable (`test.exe`); this install ships no Linux ELF launcher | Run on Windows, or use the plain-TestNG fallback (§4) for logic confidence | `[B16 §16.5.4]` |
| `n5mig.exe`/`station.exe`/`test.exe` all fail: `niagara.license.FeatureNotLicensedException: tridium:nre`, exit 253 | This beta install is unlicensed for the `tridium:nre` feature every headless/server-side Niagara tool requires (`wb.exe`/`-help`/`-version` are unaffected) | Obtain a licensed N5 install/dev-license entitlement before attempting a real `n5mig`/`niagaraTest` run | `[B17 §17.2][B29 §29.6]` |
| Third-party module cannot request `@GrantFilePermission` | The 3 core-only Grant annotations are silently dropped for a module whose JPMS name doesn't start with `com.tridium.`/`niagara.` | Confine writes to the always-granted shared directories (`${niagara.user.home}/shared/-`, etc.); no annotation path exists for arbitrary paths | `[B8 §8.1, §8.8]` |
| `n5mig` silently strips **all** objects of our custom module from the migrated station, no error/warning about it specifically | The module was not installed/registered on the target N5 install when `n5mig` ran — `BModuleRemovalConverter` fires unconditionally on `ModuleNotFoundException` | Build, sign, and **install** the module on the target N5 machine BEFORE running `n5mig` (§4.2) | `[B14 §14.5][B17 §17.5–§17.7]` |
| A reversible (`BPassword`) secret is empty/unreadable after migration, operator sees a SEVERE `migrate.breakKeyringEncoding`/`migrate.breakExternalEncoding` log line | `n5mig` force-clears any `keyring`-sourced reversible secret unconditionally (policy, not a bug); an `external`-sourced one is only cleared if the correct bog-protection passphrase was not supplied | Supply the correct bog-protection passphrase to `n5mig` for `external`-mode bogs; **plan to manually re-enter** any `keyring`-mode secret — it cannot survive migration | `[B47 §47.1, §47.5]` |
| A cross-version-encrypted secret throws an uncaught `AEADBadTagException`-class exception when read (outside `n5mig`'s own path) | `BAes256PasswordEncoder`'s default KeyRing alias literal was renamed `javax.baja.security.*` → `niagara.security.*`; the wire format carries no alias, so N5 always looks up the NEW alias, missing an N4-encrypted value's OLD one | Do not reuse a raw `.kr`/`.km` pair across versions expecting transparent decrypt; treat as a hard incompatibility for the default (non-aliased) encoder | `[B43 §43.4][B47 §47.2, §47.5]` |
| `compileModuleTestJava` prints `error: cannot determine module name for .../ModuleTest.jar` / `1 error`, but the build still reports `BUILD SUCCESSFUL` | Benign, self-referential module-path probe against the moduleTest jar the same task is writing (it has no `module-info.class` by design) — not a real failure | Ignore; verify the produced jar's entry count is correct | `[B29 §29.4.1]` |
| DashboardPan-style servlet write never shows up in `$/AuditHistory` | The write called `set()`/`invoke()` with a hard-coded `null` `Context` | Thread `req.getAttribute("niagara.context")` through to the write (§2.13) | `[B41 §41.4, §41.7][B46 §46.3]` |
| `gradlew idea`/`gradlew eclipse` tasks the kit's IDE-setup scripts invoke no longer exist | Both tasks are explicitly removed in N5 — IDE import is now by opening `build.gradle.kts` directly | Update kit scripts to drop these tasks; document the new IDE-import flow | `[B2 §2.8]` |

---

## 4. Plain-TestNG fallback (no Niagara runtime needed)

When `niagaraTest`/`bin/test.exe` is unavailable (Linux host, or a license-gated beta
install), you can still get full logic confidence for pure-Java seam tests with zero
Niagara runtime dependency — proven on ColdRoomPan's 5 ported test files, 51/51 pass,
plus a deliberate mutation ("bite") test that correctly flipped exactly the 3 expected
methods, confirming the harness is not vacuously green [B29 §29.7]:

```bash
javac -cp testng-7.12.0.jar -d build $(find src -name "*.java")
java -cp testng-7.12.0.jar:jcommander-1.83.jar:slf4j-api-2.0.16.jar:build \
  org.testng.TestNG -testclass com.your.pkg.YourTest1,com.your.pkg.YourTest2
```

`jcommander`/`slf4j-api` are required dependencies of TestNG's own CLI runner, not optional
[B29 §29.7]. This only exercises code with **zero `BObject`/Baja reflection** — a test that
extends `BTestNg` needs the real runner.

---

## 5. Station migration runbook: PANCCADIA (N4 → N5)

**Applies to JACE-9000 only, and requires an active SMA.** Tridium's official FAQ
(content-stamped 2025-10-27) states directly: *"No, The JACE-8000 was able to transition
from AX to N4, and the JACE-9000 can transition from N4 to N5."* A limited-time
license-transfer path (through 2026-06-26) lets a JACE-8000 license move to a JACE-9000 for
a transfer fee rather than a full relicense; N4.15 is Tridium's declared LTS release,
supported with security maintenance through Q3 2028 [B48 §48.1–§48.2]. The same FAQ also
gates the move on licensing status, separately from hardware: *"Eligible N4 devices,
including Supervisors and JACE-9000, will require active SMA to move to Niagara 5"* —
confirm the target box's Software Maintenance Agreement is current before planning the
migration window, distinct from the `tridium:nre` build-time license gate in step 2 below
[B48 §48.2].

**Order of operations — do not skip step 1.**

1. **Build, sign, and install every custom module (ColdRoomPan, CompPan, DashboardPan) on
   the target N5 machine BEFORE running `n5mig` against the station backup.** An
   unresolvable module's bog objects are silently STRIPPED via `BModuleRemovalConverter` —
   not left broken, not flagged for manual review, just gone, replaced with a
   `moduleRemoved` marker element [B14 §14.5, §14.10]. Live-verified: PANCCADIA's real
   `config.bog` holds 44 objects across the 3 custom modules; every one of them would be
   removed today on this box because none of the 3 modules is currently installed
   [B17 §17.4, §17.7].

   For a module whose N5 port renames or splits its on-disk/JPMS identity, declare
   `moduleName="<original N4 module name>"` in the ported `module.xml` (`ColdRoomPan-rt.jar`
   already does this — `moduleName="ColdRoomPan"` while `name="ColdRoomPan-rt"`). This is
   the one technique found that decouples the N5 physical module name from the legacy
   `module:Type` string an N4 bog still cites — it is a deliberate compatibility field,
   present in exactly 1 of 249 modules checked on this install, and it makes
   `n5mig`'s registry lookup resolve successfully instead of triggering removal
   [B17 breakthrough finding, §17.5]. **Re-verify the module is still installed
   immediately before the real migration run** — this install was directly observed losing
   a module mid-session on a shared machine during unrelated concurrent work [B17 §17.6].

2. **Resolve the `tridium:nre` license gate first.** On this beta install, `n5mig.exe`,
   `station.exe`, and `test.exe` all hit an identical
   `niagara.license.FeatureNotLicensedException: tridium:nre` at boot (exit 253);
   `wb.exe`/`-help`/`-version` are unaffected because they never reach the gated code path.
   Confirm you have a licensed install before scheduling downtime around a migration
   attempt [B17 §17.2][B29 §29.6].

3. **Run `n5mig -premigrate <source> <target>` first** (dry-run, produces an HTML report,
   makes no conversion) to catch anything else before committing [B14 §14.2, §14.11].
   Input is most commonly a 4.15-versioned `.dist` station backup; an individual `.bog`/
   `.palette`/`.px`/`.ntpl`/`.napl` file also works. The USAGE text itself names 4.15
   explicitly, matching PANCCADIA's real build [B14 §14.2].

4. **Supply the bog-protection passphrase if the station uses `external`-mode reversible
   encoding** (PANCCADIA does — `reversibleEncodingKeySource='external'`, PBKDF2-derived,
   confirmed against its real `config.bog` header, 3 reversible `BPassword` slots). With
   the correct passphrase, all 3 decrypt and re-encrypt cleanly. Without it (or after 3
   wrong attempts), `n5mig` force-clears every reversible password and logs the exact slot
   paths that will need manual re-entry — a loud, actionable failure, not silent [B47 §47.1,
   §47.4]. If any secret was ever `keyring`-encoded, it **cannot** survive migration through
   `n5mig` under any circumstance — plan for manual re-entry (§3 table).

5. **Run the real `n5mig -o <source> <target>` migration**, then re-run a `t=`-typespec
   census against the produced bog to confirm your custom modules' objects survived
   (§5.1 below gives the expected baseline).

6. **Recompile/re-sign any `BProgram` objects.** N5 makes program-object code signing
   mandatory by default; `n5mig`'s `BProgramConverter` rewrites `javax.baja.*` imports in
   embedded program source, checks the configured signing cert
   (Workbench → Tools → Options → Code Signing), and recompiles. If no valid cert is
   configured, the object is migrated with its class file cleared to empty (migration still
   succeeds; the object won't run until manually recompiled/signed later)
   [B10 §10.4 BC-29][B14 §14.8]. PANCCADIA's `config.bog` has zero `BProgram` objects
   today, so this is a forward-looking note, not a current blocker
   [B10 §10.11 CHK-13].

### 5.1 — What survives PANCCADIA's migration unconverted, and what doesn't

A full re-census of PANCCADIA's real `config.bog` (3,545 typed elements, 288 distinct
types, corrected from an earlier undercount) against the actual `migrator.jar` converter
catalog and a slot-by-slot N4↔N5 diff found [B24 §24.6][B31 §31.4, §31.7]:

- **259 of 288 types (96.0% of objects) are byte-for-byte identical**, including
  `kitControl` (100 objects, 11 types — zero registered converter, and correctly so: zero
  slot delta), `tagdictionary` (147 objects, zero delta except 1 version-gap-unresolved
  type), and `nrio` (115 objects, zero delta). The absence of a converter for these is
  **correct**, not a gap — nothing needs converting.
- **16 types add new optional properties only** — never orphans data; the migrated bog
  just doesn't carry an element for a slot that didn't exist when it was written.
- **8 types have a genuinely removed slot.** Of these, PANCCADIA's real data triggers
  exactly **one** live orphan case: `fox:FoxService.foxsCert` (a real, unconverted,
  literal `"default"` value). Traced through the bog decoder: this is **non-fatal** — the
  orphaned value is silently *resurrected* as a dynamic property on the loaded component
  (not dropped, since it carries an explicit type attribute) [B31 §31.5–§31.6].
- **The `BCapacity` storage-size restriction mode (`restrictBy=2`) was removed cleanly on
  the N5 server side** and has **zero exposure for PANCCADIA today** — 0 of its 23 real
  history capacity properties use that mode, and neither N4's nor N5's Workbench/web
  capacity editor could ever construct one through normal use in the first place. The
  theoretical hazard only applies to a fixed-length (Boolean/Enum/Numeric) history whose
  storage-size capacity was set some other way and never activated under N4
  [B20 §20.5][B26 §26.5–§26.8].

---

## 6. Known open risks

- **niagaraTest / test.exe cannot be validated end-to-end from this environment.** Whether
  a real, licensed N5 station on Windows correctly discovers and runs a ported TestNG suite
  (as opposed to just compiling and packaging one) remains unconfirmed — only the plain-
  TestNG fallback (§4) gives current logic confidence [B16 B16-G1][B29 B29-G2].
- **The `tridium:nre` license gate blocks every real migration/test rehearsal on this
  install today.** No `n5mig` run, station boot, or `niagaraTest` run has been observed to
  completion — every finding about migration/test *behavior* beyond the boot/argument-
  parsing stage is a static code trace, not a live observation [B17 B17-G1][B29 B29-G2].
- **`niagaraSync`'s *live* failover path is unverified; the static/build path is not.** A
  concrete reference HA port of ColdRoomPan-rt exists, builds clean, passes 55/55 tests,
  and passes every one of the framework validator's static admission rules by construction
  [B45 §45.4–§45.6]. What remains open is whether a *live* two-station pair actually
  resumes a mid-defrost cycle correctly end-to-end (timer deadlines counting down right,
  the FIFO queue handing off correctly, the back-reference restore in `started()` firing at
  the right moment) — no licensed N5 station was available to test this
  [B37 B37-G1, B37-G3][B45 §45.7, B45-G1].
- **Live `$/AuditHistory` readback was never observed.** The Context-threading fix (§2.13)
  is confirmed correct at the bytecode level (the right value reaches the right call), but
  not confirmed to produce a persisted, correctly-attributed `BAuditRecord` on a running
  station [B41 B41-G4][B46 B46-G4][B49 B49-G1].
- **The 5 JavaFX/Batik `compileOnly` fix has not been runtime-tested.** It resolves the
  module graph at compile time; whether a module that actually *calls* a JavaFX/Batik API
  (unlike DashboardPan, which never does) behaves correctly at runtime against these
  artifacts is untested [B39 B39-G4].
- **Whether N5 GA (targeted December 2026) preserves the beta's permissiveness is
  unknown** — e.g. whether `basicDriver`/`devDriver`-chassis drivers still compile with
  only a suppressible warning, or whether the 49 modules with zero N5 package overlap are
  genuinely removed vs. beta-only omissions, cannot be confirmed pre-GA
  [B22 B22-G2][B48 §48.1, §48.6].
- **PANCCADIA's `schedule:*`, points/histories/alarms bog files were never available for
  census** — only `config.bog` (driver-network structure) was inspected; schedule-type
  compatibility for this station is completely unverified [B31 B31-G4].
- **The `javax.baja.*` → `niagara.*` KeyRing alias rename's real-world blast radius on our
  own modules is unconfirmed** — none of our 3 modules currently use `BAes256PasswordEncoder`
  directly, so this is a platform-level risk noted for awareness, not a currently-triggered
  defect [B43 §43.4][B47 §47.5].
- **Module signing on N5 was proven to work, but only via a reused, pre-existing self-signed
  developer keystore** (`$HOME/.tridium/security/niagara.signing.{jceks,xml}`, located and
  reused unmodified by `com.tridium.sign`), not a freshly-created or CA-issued one — whether
  a station trusts a signature from a keystore an operations team creates independently, as
  opposed to this dev environment's pre-existing default identity, is untested
  [B9 §9.5][B48 §48.4].
- **The `build-n4-module` kit's own `.gradle.kts` templates have not been updated or diffed
  against the N5 plugin DSL** — every porting step above was applied by hand to each real
  module; whether the kit's scaffold generator itself should be updated to emit N5-shaped
  files by default remains open (B2-G6, still pending — see also [B50] child gaps B50-G1/G2
  for the untested driver- and native-module shapes).

---

## Appendix: source blocks

Every rule above cites `[Bn §x.y]`. Full evidence, decompiled code excerpts, and certainty
markers live in `niagara5-blockN.md` in this corpus. See also `niagara5-block50.md` for the
synthesis self-verify table mapping every rule in this guide back to its source section.

Source blocks cited: B1, B2, B5, B7, B8, B9, B10, B14, B16, B17, B20, B22, B24, B26, B28,
B29, B31, B37, B39, B41, B43, B45, B46, B47, B48, B49 (B45 — the ColdRoomPan HA-ready PoC
closing B37-G6 — was added to §2.10/§6 after this guide's initial draft, once it was
written; see `niagara5-block50.md` header for the amendment note).
