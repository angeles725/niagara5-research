# Block 89 — Nine build-toolchain/devkit/test gaps closed by fresh decompiles: `lateinit` native platforms, a triply-inert `compact3` flag, a real javac module-naming defect, `Version.strip()`'s exact algorithm, a dead `ignoreRuntimeProfileCheck`, and the missing "TestNG Support" doc found under the wrong filename

> Research closing/advancing nine named gaps handed down from six parent blocks: **B74-G1** (build a
> driver module end-to-end via the wizard's `NDriverModuleGenerator`/`VideoDriverModuleGenerator`
> templates — static reconstruction accepted, a real build is requires-execution), **B74-G2** (recover
> `devkit*.properties`' native-build compiler/linker command SHAPES), **B74-G3** (the `npsdk-native`
> `linux_npsdk`/Gcc preset platform's default `os`/`arch`/`devkitName` derivation for a bare
> `create(name)`), **B2-G2** (the meaning of the `Compact3ArgumentProvider`'s javac argument),
> **B2-G3**/**B16-G3** (locate the "TestNG Support in Niagara 5" document [Block 2]/[Block 16] both
> named but neither could find), **B29-G4** (does `niagaraTest`'s real TestNG runner require
> `niagara.test.BTestNg` even for pure-logic tests), **B29-G5** (the `compileModuleTestJava`
> `"cannot determine module name for … ColdRoomPan-rtTest.jar"` benign-error root cause), **B60-G1**
> (`ignoreRuntimeProfileCheck`'s consuming logic), **B60-G2** (`com.tridium.util.Version.strip(2)`'s
> exact truncation algorithm). **Confirmed against the parent blocks' own text before use** (no drift):
> all nine gap IDs and their phrasing were re-read from [Block 74]/[Block 2]/[Block 16]/[Block 29]/
> [Block 60] this session and match the caller's framing verbatim.
>
> **Net result: 7 of 9 CLOSED, 2 ADVANCED (not fully closed).** CLOSED: B74-G3, B2-G2, B29-G5, B60-G1,
> B60-G2, B2-G3/B16-G3 (one doc, two gap IDs). ADVANCED: B74-G1 (the class hierarchy and one template
> are now fully traced; no wizard was actually invoked — say so explicitly, this is a requires-execution
> residual per the task's own framing), B74-G2 (the exact property-key taxonomy and the
> commons-configuration2 `${…}`-interpolation composition mechanism are now `[CERT]`, but no real
> `devkit*.properties` artifact exists on this install to confirm the literal list-delimiter syntax —
> still blocked on an external Tridium artifact, same shape as [Block 74] §74.2 itself found). B29-G4
> is folded into the B2-G3/B16-G3 closure: the newly-found official doc's own worked examples settle
> the DOCUMENTED half of B29-G4 (`[CERT-doc]`) without settling the RUNTIME-enforcement half (still
> blocked on a licensed `niagaraTest` run, [Block 29]'s own standing blocker, untouched here).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` and
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28` — the same install every parent block read. All
> decompilation this session is FRESH, into this session's own scratchpad
> (`/tmp/claude-1000/…/scratchpad/b89/`), never reusing a prior block's now-vanished `/tmp` output —
> [Block 74]'s own `n5b74` extraction, [Block 2]'s `n5b2`, and [Block 49]'s `n5b7` are all gone; every
> class this block cites was re-extracted and re-decompiled/re-disassembled independently this session.
>
> Sources: `etc/m2/repository/com/tridium/tools/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar` — the same
> fat Kotlin plugin jar [Block 2]/[Block 74] read; this session extracts its FULL 138-class `natives`
> package plus (newly) its `java.util` (`Compact3ArgumentProvider`, whole file), `module`/`module.util`
> (`ModuleXml`, `NiagaraModulePlugin`, `ExtensionsKt`), and `util` (`com.tridium.util.Version`, never
> previously opened by any block — it is NOT a Gradle-plugin class but a shared Tridium utility bundled
> into the same fat jar) classes, decompiled with Vineflower (`tools/decompilers/vineflower-1.12.0.jar`)
> and cross-checked with `javap -p -c` where Vineflower's own Kotlin-metadata reconstruction failed
> (`NativePlatformFactory.create()`, `NiagaraNativePlatform`'s three `lateinit`-backed getters,
> `ExtensionsKt.isCompact3()`, `NiagaraModulePlugin.registerModuleTasks$lambda$2$0`). Whole-jar `grep -rla`
> for `RuntimeProfileCheck` (2 hits, both in `ModuleXml.class`, both non-consuming — see §89.5).
> `devkit.jar!LIB-INF/n-templates-5.0.54.9.2.jar` — [Block 74]'s own source; this session decompiles
> `VideoDriverModuleGenerator.class` (whole file, clean Vineflower output, never previously read as
> source) and reads `gradle/ndriver/BNfooDevice.java.vm` (whole file, 212 lines, never previously read —
> [Block 74] only head-read `BNfooNetwork.java.vm`). `tridium-niagara-slotomatic-library-5.0.2.jar` —
> fresh independent extraction, whole-jar `grep -rla` for `RuntimeProfileCheck` (zero hits).
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{baja,devkit}.jar` — whole-jar `grep -rla`
> for `RuntimeProfileCheck` (zero hits in both, this session). `docDeveloper.jar!doc/buildN5.html` — the
> SAME doc [Block 2] read; this session re-parses its "TestNG Support in Niagara 5" cross-reference and
> follows its actual `<a href="test.html">` target, never previously followed by [Block 2]/[Block 16].
> `docDeveloper.jar!doc/test.html` (23,607 bytes) — **the document [Block 2]/[Block 16] both named as
> missing, read in full this session for the first time in this corpus.** Six real shipped
> `<module>.jar!META-INF/module.xml` files (`kitControl`, `alarm`, `bacnet`, `workbench`, `history`,
> `schedule`) read fresh this session for their `<dependency vendorVersion="…">` attributes (extending
> [Block 60] §60's own single kitControl→alarm spot check to six independent modules / ~160 dependency
> lines). `/home/cristian/niagara5-research/poc/coldroompan-n5/.n5config/modules/ColdRoomPan-rtTest.jar!
> META-INF/MANIFEST.MF` — the ACTUAL on-disk PoC artifact [Block 29] §29.4.1 built and left un-inspected;
> read directly this session. `/mnt/c/Program Files/Java/jdk-25/lib/src.zip` — a REAL JDK 25 install on
> this host (distinct from the stripped JRE bundled inside Niagara itself, which ships no `src.zip`);
> this session extracts and reads `jdk.compiler/com/sun/tools/javac/file/Locations.java` (targeted
> ranges) and `jdk.compiler/com/sun/tools/javac/resources/compiler.java` (the compiled-in
> `compiler.properties` resource bundle, since the raw `.properties` file itself is not shipped in
> `src.zip`) — the FIRST time this corpus has read javac's own source rather than treating it as an
> opaque external tool.
>
> Method: `unzip`/whole-jar extraction, Vineflower whole-package decompilation into a fresh session
> scratchpad, `javap -p -c` bytecode disassembly for Kotlin lambda/anonymous classes Vineflower could
> not reconstruct as source, whole-jar `grep -rla` negative-existence sweeps (4 independent jars for
> `RuntimeProfileCheck`), direct `unzip -p`/`unzip -l` reads of live shipped jars' manifests and
> `module.xml` files, and a direct read of a REAL JDK's own `src.zip` for javac's own diagnostic-message
> source. Markers (canonical list, METHODOLOGY §3): `[CERT]` local primary source (`file:line` for a
> decompiled `.java`/`.kt`, or a named bytecode method for a `javap`-disassembled anonymous/lambda class)
> · `[CERT-hw]` verified against a live install's own shipped artifacts (jar manifests, on-disk PoC
> build output, a real host JDK's `src.zip`) · `[CERT-doc]` a shipped Niagara documentation file ·
> `[INFER]` researcher deduction.
>
> Build toolchain / devkit / test-framework layer. Connects [Block 74] (B74-G1, B74-G2, B74-G3),
> [Block 2] (B2-G2, B2-G3), [Block 16] (B16-G3, and B29-G4's shared root in [Block 16] §16.6),
> [Block 29] (B29-G4, B29-G5), [Block 60] (B60-G1, B60-G2), [Block 51] (B60-G2's own upstream citation).
>
> **Type:** `mixed` — §89.1–§89.5 are fresh-decompile/fresh-disassembly closures (`[CERT]`-heavy, this
> session's own extraction, not reused from any parent block's now-vanished `/tmp` output); §89.6 is a
> capture-shaped find (a document search that resolves as "it was there all along, under a different
> filename"); §89.7–§89.9 are `[CERT]`+`[INFER]` advancements bounded by a genuinely missing external
> artifact or a genuinely un-executed wizard run, named as such rather than forced to a false CLOSED.

---

## 89.1 — B74-G3 CLOSED: a bare `platforms.create(name)` leaves `os`/`arch`/`devkitName` as Kotlin `lateinit var`s with zero defaulting — the FIRST read of any of them throws `kotlin.UninitializedPropertyAccessException`, not a silently-derived default `[CERT]`

[Block 74] §74.2 read `NiagaraNativePlatform.kt`'s `os`/`arch`/`devkitName` fields as `lateinit var` but
did not trace `DefaultNiagaraNativeExtension$NativePlatformFactory.create(name)` itself, leaving open
whether a bare `platforms.create("someName")` (unlike `NpsdkNativePlugin`'s own explicit
`.setCompiler(CompilerFamily.Gcc)` call after creating `"linux_npsdk"`) derives a sensible default from
the platform's own name string, or throws at first use. This session traces it directly, independently
via `javap -p -c` on the real `.class` file (Vineflower could not reconstruct the method as Kotlin source
— "Anonymous class does not have Class Kotlin metadata" — but its own embedded bytecode dump matched the
independent `javap` disassembly byte-for-byte, cross-checked this session).

**`NativePlatformFactory.create(String name)`'s entire body, disassembled:** guard against a read-only
platform container (`getPlatformsReadOnly().get()` → throw `IllegalStateException` if true), then
`new NiagaraNativePlatform(name)` — **the single-argument constructor, called with ONLY the name string**
— followed by three `NiagaraNativePluginKt` configuration-object registrations
(`createLinkPathConfiguration`/`createRuntimeElementsConfiguration`/`createBinaryProducerConfigurations`)
and one `TaskContainer.register(name, …)` call, then `return` the platform `[CERT]` (`javap -p -c`,
`DefaultNiagaraNativeExtension$NativePlatformFactory.create`, this session — the disassembly is
reproduced in full in this session's own transcript; independently cross-checked against Vineflower's
own embedded bytecode-dump comment for the same method, byte-identical).

**`NiagaraNativePlatform`'s own two constructors confirm the single-arg path sets ONLY `name`.**
`javap -p` lists both `NiagaraNativePlatform(String)` and `NiagaraNativePlatform(String, Os, String,
String, CompilerFamily)` as distinct overloads `[CERT]` (`javap -p`,
`com/tridium/gradle/plugins/natives/NiagaraNativePlatform.class`, this session). Disassembling the
1-arg constructor's own bytecode: it calls `Object.<init>()` then exactly ONE `putfield` —
`name:Ljava/lang/String;` — and returns; there is no `putfield` for `os`, `arch`, `devkitName`, or
`compiler` anywhere in its body `[CERT]` (`javap -p -c`, same class, constructor bytecode read in full
this session).

**All three getters carry the Kotlin-compiler-generated `lateinit` null-check-then-throw pattern,
independently confirmed for each field.** `getOs()`: `getfield os` → `dup` → `ifnull` → (non-null:
return) / (null: `ldc "os"` → `invokestatic Intrinsics.throwUninitializedPropertyAccessException`).
`getArch()` and `getDevkitName()` disassemble to the byte-identical pattern, each with its own field
name as the `ldc` string argument (`"arch"`, `"devkitName"`) `[CERT]` (`javap -p -c`, all three getter
methods disassembled in full this session, `NiagaraNativePlatform.class`).

**Net verdict, closing B74-G3: a bare `platforms.create("someName")` platform's `os`/`arch`/
`devkitName` are left completely unset, and the FIRST read of any of them — by `NativeCommand.kt`'s own
`this.os`/`this.arch`/property-key resolution (§89.9 below), or by anything else — throws
`kotlin.UninitializedPropertyAccessException: lateinit property os has not been initialized"` (Kotlin's
own standard runtime message shape for this exact bytecode pattern).** This settles [Block 74]'s own
open `[INFER]` choice ("sensible default from the platform's own name" vs. "throw") definitively in
favor of THROW, with bytecode-level certainty rather than a plausibility judgment.

## 89.2 — B2-G2 CLOSED: the `Compact3ArgumentProvider` is triply inert on N5 — gated to (in practice) only the `baja` module by an `nre`-flag check that defaults `true` for every module, and even then permanently suppressed by its own Java-9+ version guard `[CERT]`

[Block 2] §2.7 found `NiagaraJavaPlugin.kt` registers a `Compact3ArgumentProvider` on every `JavaCompile`
task and `[INFER]`red it exists "to keep module classfiles usable on constrained embedded JVMs (e.g. a
JACE)," flagging the actual javac-argument value as unconfirmed (**B2-G2**). This session fully
decompiles the class (clean Vineflower output, no Kotlin-metadata failures) plus its two wiring sites.

**`Compact3ArgumentProvider.asArguments()`'s complete body:** `[CERT]` (`Compact3ArgumentProvider.kt`,
whole 55-line file, this session):
```
39   public open fun asArguments(): Iterable<String> {
40      val var10000: java.util.List = if (!this.enabled.get())
41         CollectionsKt.emptyList()
42         else
43         (
44            if ((this.javaCompiler.get() as JavaCompiler).getMetadata().getLanguageVersion().canCompileOrRun(9))
45               CollectionsKt.emptyList()
46               else
47               CollectionsKt.listOf(arrayOf("-profile", "compact3"))
48         )
```
i.e. the deprecated javac `-profile compact3` flag (JEP 161's Java-8-era compact-profile scheme,
REMOVED from javac entirely in Java 10+) is emitted **only if `enabled=true` AND the configured
toolchain's language version is BELOW 9.** `enabled` itself defaults to `false`
(`objects.property(Boolean::class.java).convention(false)` in the constructor, `:29-31`).

**`enabled` IS wired per-module by the module plugin — not simply left at its constructor default of
`false` — via a real manifest-derived condition.** `NiagaraModulePlugin.registerModuleTasks$lambda$2$0`
disassembles to: `compact3Provider.getEnabled().set(project.provider(() -> isCompact3(manifestExtension)))`
`[CERT]` (`javap -p -c`, `NiagaraModulePlugin.class`, method `registerModuleTasks$lambda$2$0`, this
session — the exact `Compact3ArgumentProvider.getEnabled()` → `Property.set(Provider)` call chain,
fed by a `Callable<Boolean>` wrapping `ExtensionsKt.isCompact3(manifestExtension)`, confirmed via a
second class, `NiagaraModulePlugin$registerModuleTasks$3$1$1.call()`, same session). `isCompact3`'s own
body: `[CERT]` (`javap -p -c`, `ExtensionsKt.isCompact3`, this session) —
```
isCompact3(moduleXml) = !moduleXml.getNre().get()  ||  moduleXml.getModuleName() == "baja"
```

**The `nre` half of that condition is unconditionally `true` by default for every module, and stays
`true` in every real module.xml this session sampled.** `ModuleXml.java:80`: `this.getNre().set(true)` —
a hard `.set(true)`, not a `.convention(...)` that a `-P` Gradle property could override, applied
unconditionally in the extension's own constructor `[CERT]` (this session's own decompile). Six real
shipped modules' own `<module … nre="true" …>` attributes were read directly this session
(`kitControl.jar`, `alarm.jar`, `bacnet.jar`, `workbench.jar`, `history.jar`, `schedule.jar`
`!META-INF/module.xml`, all six showing `nre="true"`) — no module in this corpus has ever been observed
with `nre="false"`. **Given that, `isCompact3()` reduces, IN PRACTICE, to just `moduleName == "baja"`** —
the `baja` module is the ONLY module in this corpus's whole universe that would ever get
`compact3Provider.enabled=true`.

**Net verdict, closing B2-G2:** the `Compact3ArgumentProvider` is a genuine legacy carryover of Java
8-era JEP-161 compact-profile logic (matching [Block 2]'s own JACE/embedded-JVM guess), gated to
(in practice) only the `baja` module by an `nre`-flag condition that every other module leaves at its
universal `true` default — and even for `baja` itself, the flag can NEVER actually fire, because its own
`canCompileOrRun(9)` guard requires a sub-Java-9 compiler, which is structurally impossible under N5's
mandatory Java-25 toolchain ([Block 2] §2.8, independently re-confirmed unchanged this session). The
`-profile compact3` argument is dead code on N5 5.0.0.28 for every module, unconditionally.

## 89.3 — B29-G5 CLOSED: the `"cannot determine module name for … ColdRoomPan-rtTest.jar"` message is javac's OWN documented diagnostic for an invalid `Automatic-Module-Name` — and the actual on-disk PoC jar carries exactly the disqualifying defect (a hyphen inside the declared module name) `[CERT]`+`[CERT-hw]`

[Block 29] §29.4.1 observed `compileModuleTestJava` print `error: cannot determine module name for
…/ColdRoomPan-rtTest.jar` / `1 error` without failing the overall build, and `[INFER]`red the cause as
"javac's own module-path resolver … finding it carries no `module-info.class`, which the resolver logs
as an error without treating it as one" — flagged unconfirmed as **B29-G5**. That `[INFER]` is corrected
here: the message is NOT triggered merely by the absence of `module-info.class` (that case is handled
silently, by design, on a different code path). This session reads javac's own source (a REAL JDK 25
install's `src.zip`, distinct from Niagara's own stripped, `javac`-less bundled JRE) and the ACTUAL
on-disk PoC jar side by side.

**javac's `Locations.java` `inferModuleName(Path p)` handles a jar with no `module-info.class` in TWO
separate branches, and only ONE of them can produce this exact error.** `[CERT]`
(`jdk.compiler/com/sun/tools/javac/file/Locations.java:1390-1420`, `/mnt/c/Program Files/Java/jdk-25/
lib/src.zip`, read in full this session):
```
1396         Path mf = fs.getPath("META-INF/MANIFEST.MF");
1397         if (Files.exists(mf)) {
...
1401              if (attrs != null) {
1402                 String moduleName = attrs.getValue(new Attributes.Name("Automatic-Module-Name"));
1403                 if (moduleName != null) {
1404                    if (isModuleName(moduleName)) {
1405                       return new Pair<>(moduleName, p);
1406                    } else {
1407                       log.error(Errors.LocnCantGetModuleNameForJar(p));
1408                       return null;
1409                    }
```
i.e. `Errors.LocnCantGetModuleNameForJar` fires ONLY when the jar's manifest declares an
`Automatic-Module-Name` attribute whose VALUE fails `isModuleName()` validation. If the manifest has NO
`Automatic-Module-Name` at all, control falls through past this block entirely to the SILENT
filename-derivation "automatic module" path at `:1422+` (strip `.jar`, strip a trailing `-<version>`
suffix, replace non-alphanumerics with dots) — which returns a name successfully, with NO error logged.
`isModuleName(name)` requires every dot-separated segment to satisfy `SourceVersion.isName()` (a valid
Java identifier) `[CERT]` `Locations.java:1505-1516`. The error message text itself, confirmed against
javac's own compiled-in resource bundle: `[CERT]`
(`jdk.compiler/com/sun/tools/javac/resources/compiler.java:299`, same `src.zip`) —
```
299   { "compiler.err.locn.cant.get.module.name.for.jar", "cannot determine module name for {0}" },
```
— matching [Block 29]'s own observed console text (plus javac's own separate `"1 error"` summary line,
standard for a single logged error) exactly, character for character.

**The ACTUAL PoC jar on disk carries exactly the disqualifying condition.** `[CERT-hw]` (`unzip -p
/home/cristian/niagara5-research/poc/coldroompan-n5/.n5config/modules/ColdRoomPan-rtTest.jar
META-INF/MANIFEST.MF`, this session, real file, not a decompile):
```
Manifest-Version: 1.0
Automatic-Module-Name: com.angeles.ColdRoomPan-rtTest
```
`com.angeles.ColdRoomPan-rtTest` contains a HYPHEN inside its final segment (`ColdRoomPan-rtTest`) —
hyphens are not valid Java-identifier characters, so `SourceVersion.isName("ColdRoomPan-rtTest")` is
`false`, so `isModuleName(...)` is `false`, so javac hits exactly the `LocnCantGetModuleNameForJar`
branch — reproducing [Block 29]'s observed error byte-for-byte from first principles, not by
recall. `[CERT-hw]` (`unzip -l`, same jar, this session): the jar genuinely has no `module-info.class`
either (14 entries total, none named `module-info.class`) — consistent with [Block 16] §16.7's own
finding that the moduleTest jar is not its own JPMS module — but that fact is NOT what triggers the
error; the invalid `Automatic-Module-Name` header is.

**Net verdict, closing B29-G5:** the error is javac's own well-defined, intentional diagnostic for a
malformed `Automatic-Module-Name` manifest header — not a mysterious self-referential module-path
resolver quirk. The header's value is auto-generated by the SAME module-writing pipeline that names the
main module `com.angeles.ColdRoomPan-rt` (also hyphenated, also technically invalid as a module name,
though the main jar HAS a real `module-info.class` so its manifest header is never actually consulted by
`inferModuleName` for that jar — [Block 16] §16.7's own `Automatic-Module-Name:
com.angeles.ColdRoomPan-rt` finding is now explained as a LATENT instance of the same defect, masked
only because the main jar's real `module-info.class` short-circuits the manifest-fallback branch before
it is ever reached). Why the overall Gradle task does not FAIL despite this logged javac error is a
narrower residual, named as child gap **B89-G1** below (an execution-order/self-reference nuance [Block
29] itself already correctly flagged as a hypothesis, now narrowed rather than fully explained).

## 89.4 — B60-G2 CLOSED: `Version.strip(N)` is "truncate to the first N segments if longer, else no-op" — the algorithm is now fully `[CERT]`, and the two-different-observed-results puzzle is explained by two different `dependencyVersionLimit` values in two different build contexts, not a mystery in `strip()` itself `[CERT]`+`[INFER]`

[Block 60] §60.6 (`[C1]`) found two real observed dependency-version truncations —
`ColdRoomPan-rtTest`'s `2.0.7`→`2.0` (a 3→2 truncation) and a fresh `kitControl`→`alarm` spot check's
`5.0.0.28`→`5.0.0` (a 4→3 truncation) — and could not reconcile BOTH dropping exactly 1 trailing segment
with a single constant `dependencyVersionLimit=2` read either as "keep 2 segments" (would predict
`alarm`→`5.0`, not observed) or "drop 2 segments" (also not observed for either case), naming
`Version.strip(int)`'s own unread implementation as **B60-G2**. This session decompiles
`com.tridium.util.Version` (a shared Tridium utility class bundled inside the same `n-plugin` fat jar,
never previously read by any block — clean Vineflower output, whole 147-line file).

**`strip(int)`'s complete, literal body:** `[CERT]` (`Version.java:94-103`, this session):
```
94   public Version strip(int stripLength) {
95      if (stripLength != 0 && this.versions.length > stripLength) {
96         Version other = new Version();
97         other.versions = new int[stripLength];
98         System.arraycopy(this.versions, 0, other.versions, 0, other.versions.length);
99         return other;
100      } else {
101         return this;
102      }
103   }
```
This is neither of [Block 60]'s two candidate readings — it is **"if the version has MORE than
`stripLength` segments, truncate to EXACTLY the first `stripLength` segments; otherwise (fewer or equal
segments, or `stripLength==0`) return unchanged."** `toMajorMinorString()` is confirmed to be exactly
`strip(2).toString()` `[CERT]` `Version.java:129-131` — i.e. "major.minor" IS `strip(2)`'s intended
common case.

**The real call site, re-confirmed fresh this session (independent of [Block 51]'s own now-unreadable
citation):** `ModuleXml.getDependencyFromManifest()` computes a dependency's written
`vendorVersion` as `new Version(vendorVersion).strip(versionStrip).toString()`, where
`versionStrip = getDependencyVersionLimit().get()`, whose default is `2` (`.set(2)`, unconditional,
same non-overridable pattern as `nre` in §89.2) `[CERT]` (this session's own `ModuleXml.java` decompile,
`:69` default, `:377,386,402` call site — quoted in full in §89.2's own header source list).

**Applying the NOW-CONFIRMED algorithm exactly reproduces BOTH of [Block 60]'s observations, once each
one's OWN build context's `dependencyVersionLimit` is accounted for — resolving the "contradiction" as
two different configured values, not a flaw in `strip()`.** `strip(2)` on the PoC's own
`ColdRoomPan-rt` vendor version `2.0.7` (3 segments, `> 2`) → truncate to the first 2 → `"2.0"` —
**exactly** the PoC's own observed default-`dependencyVersionLimit=2` result `[CERT]` (matches [Block
16] §16.7's own reading, re-derived from first principles here). For Tridium's OWN shipped
`kitControl`→`alarm` dependency (`5.0.0.28`, 4 segments, observed truncated to `"5.0.0"`, 3 segments):
`strip(3)` — NOT the default `strip(2)` — on a 4-segment source (`> 3`) → truncate to the first 3 →
`"5.0.0"`, an exact match. **This session extends the spot check from one Tridium module to SIX**
(`kitControl`, `bacnet`, `workbench`, `alarm`, `history`, `schedule` — every one of their ~160 combined
`<dependency vendorVersion="…">` lines reads `"5.0.0"`, uniformly 3 segments, for every dependency whose
own module declares a 4-segment `vendorVersion="5.0.0.28"`) `[CERT]` (six real `!META-INF/module.xml`
reads, this session) — a consistent pattern across 6 independent modules, not a one-off.

**Net verdict, closing B60-G2:** `Version.strip(int)`'s algorithm is now fully, exactly known — "keep
first N segments if longer, else unchanged" — with zero remaining ambiguity in the CODE. The two
DIFFERENT observed outputs are explained `[INFER]` (Tridium's own internal build pipeline almost
certainly configures `dependencyVersionLimit=3` for its own first-party module builds, differing from
the devkit wizard's own shipped default of `2` that this corpus's PoC builds use unmodified) — an
inference now backed by six consistent independent Tridium-module observations rather than the single
kitControl→alarm sample [Block 60] itself flagged as fresh-but-unreconciled.

## 89.5 — B60-G1 CLOSED (exhaustive negative): `ignoreRuntimeProfileCheck` is dead code across the ENTIRE build+runtime toolchain on this install — declared, defaulted from a `-P` Gradle property, and read/written NOWHERE else in four independently-searched jars `[CERT]`

[Block 60] §60 found the devkit wizard's own `module.gradle.kts.vm` template sets
`ignoreRuntimeProfileCheck.set("true")` with the comment `"Temporarily ignore rt module part checks for
module conversion exercise,"` confirmed the property genuinely exists in `ModuleXml.java`'s own DSL, but
could not find the CONSUMING logic in either of its own two cached decompile fragments — naming
**B60-G1**. This session runs an exhaustive whole-jar negative-existence search across every artifact
this corpus has access to.

**Whole-jar `grep -rla "RuntimeProfileCheck"` (case-sensitive substring, covers both
`ignoreRuntimeProfileCheck` and `getIgnoreRuntimeProfileCheck`) across FOUR independently-extracted
jars, this session:**

| Jar | Hits | Where |
|---|---|---|
| `n-plugin-5.0.54.9.2.jar` (the ONE fat jar hosting every Gradle plugin class in this toolchain — [Block 2] §2.1/§2.2's own finding, re-relied-on here) | 2 | both in `ModuleXml.class` |
| `tridium-niagara-slotomatic-library-5.0.2.jar` | 0 | — |
| `baja.jar` (the runtime module-loading side) | 0 | — |
| `devkit.jar` | 0 | — |

**The 2 hits inside `ModuleXml.class` are BOTH non-consuming — a `.convention(...)` default-wiring call
and the abstract property declaration, never a `.get()` read anywhere.** `[CERT]` (this session's own
`ModuleXml.java` decompile, whole 453-line file):
```
90    this.getIgnoreRuntimeProfileCheck().convention(project.getProviders().gradleProperty("ignoreRuntimeProfileCheck"));
...
158   public abstract Property<String> getIgnoreRuntimeProfileCheck();
```
A full-file `grep -n "IgnoreRuntimeProfileCheck"` over the decompiled `ModuleXml.java` returns ONLY
these two lines — no third call anywhere in the same class `[CERT]` (this session). The property is
ALSO never written into the generated `<module>` XML element: the exhaustive list of `root.setAttr(...)`
calls building the module manifest (`ModuleXml.java:220-232` — `name`, `bajaVersion`, `vendor`,
`vendorVersion`, `description`, `preferredSymbol`, `nre`, `autoload`, `installable`, `buildMillis`,
`buildHost`, `moduleName`, `schemaVersion`) does not include it `[CERT]` (same decompile, this session)
— so it cannot flow to a runtime-side (`baja.jar`) consumer via the shipped manifest either, and indeed
`baja.jar`'s own whole-jar search independently confirms zero references.

**Net verdict, closing B60-G1: as of N5 5.0.0.28 Beta, `ignoreRuntimeProfileCheck` gates NOTHING.** It
is a genuinely dead Gradle property across the entire Gradle-plugin jar (which is EVERY plugin id in
this build system, per [Block 2]'s own established fact), the Slotomatic compiler jar the wizard invokes
directly ([Block 74] §74.1's own finding), and the two runtime jars (`baja`, `devkit`) most likely to
carry a manifest-time or install-time consumer. The wizard's own "Temporarily" comment most plausibly
describes either a forward-declared property awaiting a not-yet-shipped consumer in this Beta build, or
a check that lives exclusively inside a closed native binary this corpus cannot decompile (`wb.exe`/
`station.exe`) — a residual explicitly narrower than [Block 60] left it, not eliminated with the same
certainty as the four-jar JVM-side search, and named as child gap **B89-G2**.

## 89.6 — B2-G3/B16-G3 CLOSED: the "TestNG Support in Niagara 5" document exists, ships inside the SAME `docDeveloper.jar` [Block 16] searched, and was missed only because its real filename is `doc/test.html` — not anything containing "testng" `[CERT-doc]`+`[CERT-hw]`

[Block 2] §2.9 named `buildN5.html`'s own cross-reference to a separate "TestNG Support in Niagara 5"
document as unopened (**B2-G3**). [Block 16] §16.6 searched `docDeveloper.jar` by filename
(`unzip -l` for `testng`/`test-ng`) and found nothing but two thin bajadoc API stubs, concluding the doc
"does not ship inside `docDeveloper.jar` itself … may be web-only" (**B16-G3**). Both conclusions are
corrected here.

**`buildN5.html`'s own cross-reference link target is `test.html` — a plain filename with no "testng"
substring anywhere in it — which is exactly why [Block 16]'s substring search missed it.** `[CERT-doc]`
(`docDeveloper.jar!doc/buildN5.html`, this session, parsed directly):
```
More details on setting up tests can be found in the <a href="test.html">TestNG Support in
Niagara 5</a> document.
```
**`doc/test.html` DOES exist inside `docDeveloper.jar`** — the exact same jar [Block 16] searched.
`[CERT-hw]` (`unzip -l docDeveloper.jar`, this session): `23607  1980-02-01 00:00   doc/test.html` — one
matching entry, confirmed present. This is a plain false negative in [Block 16]'s own search method
(filename substring `testng`/`test-ng`), not a genuinely missing artifact — the document was in the
corpus's reach the whole time.

**The document's own content, read in full this session (`[CERT-doc]`, `docDeveloper.jar!doc/test.html`,
23,607 bytes), is titled "Niagara Automated Testing with TestNG"** and covers: TestNG framework overview
and feature list; the co-located `srcTest` source-layout convention; a complete worked basic-unit-test
example (`BFunctionTypeTest extends niagara.test.BTestNg`, with the standard `@NiagaraType`/Slot-o-Matic
generated-code region and a single `@Test` method); `@BeforeMethod`/`@AfterMethod` setup/teardown;
`niagara.test.TestHelper`'s private-field/private-method reflection utilities and async-wait helpers;
the `moduleTestJar`/`gradlew moduleTestJar` build task and the `test <moduleName>[:<typeName>]` run
command (confirming `all`/`<moduleName>`/`<moduleName>:<typeName>` as the three supported run-command
argument forms, and that **single-method execution is explicitly NOT currently supported** — a fresh,
previously-undocumented-in-this-corpus fact); a full worked running-station example
(`BMyComponentTest extends niagara.test.BTestNgStation`) covering `configureTestStation` overrides,
bog-file-based station construction, role/user/permission setup, and Fox-session connection helpers; and
TestNG groups/dependencies/sequencing (`groups`, `dependsOnGroups`, `priority`).

**Direct bearing on B29-G4 (folded in here rather than left as a separate unresolved gap): EVERY worked
example in the official doc extends either `BTestNg` or `BTestNgStation` — there is no documented "plain
TestNG, no Baja base class" path anywhere in this document.** `[CERT-doc]` (same source, this session).
This is DOCUMENTARY evidence bearing directly on [Block 29] §29.3's own open question ("whether
`niagaraTest`'s real TestNG runner REQUIRES every discovered class to extend `BTestNg` regardless of
whether it touches Baja types") — it does not PROVE a hard runtime enforcement (the doc's silence on a
bare-TestNG path is consistent with either "it's required" or "it's just not a documented pattern
because nobody writes pure-logic Niagara tests this way in practice"), so **B29-G4 is ADVANCED, not
closed**: the only path to a definitive answer remains a real, licensed `niagaraTest` run against
[Block 29]'s own 5 deliberately-non-`BTestNg` ported test files — [Block 29]'s own standing blocker
(license wall on `test.exe`/`n5mig`), untouched by this session.

## 89.7 — B74-G1 ADVANCED, not fully closed: `VideoDriverModuleGenerator` is now `[CERT]`-confirmed to mirror `NDriverModuleGenerator`'s exact queue-then-Slotomatic mechanism; one representative template statically reconstructed; no wizard was actually invoked `[CERT]`

[Block 74] §74.1 fully traced `NDriverModuleGenerator`'s mechanism (queue up to 17 conditional
`.java.vm` template writes → `super.generate()` → direct in-process `Slotomatic.builder()…
runSlotomatic()`) but left `VideoDriverModuleGenerator`'s own body unread, `[INFER]`ring only "that it
mirrors `NDriverModuleGenerator`'s shape, not independently verified" — refined as **B74-G1**'s first
half. This session decompiles it (clean Vineflower output, whole 197-line file, zero decompile errors).

**Confirmed: `VideoDriverModuleGenerator extends NDriverModuleGenerator`, and its own `generate()`
override is the BYTE-IDENTICAL shape** — queue up to 24 conditional `addTemplateWrite()` calls
(camera/dvr/event/datatypes/enums/util/ui `.java.vm` files, gated by `dvrSupport`/`dvrDiscovery`/
`dvrDisplay`/`camera.isPanTiltSupport()`/`camera.isFocusSupport()`/`getCommInfo().isHttp()` boolean
flags) — then `this.writeNiagaraModuleFiles()` — then, identically to the parent class,
`Slotomatic.builder().withModulePath(niagaraModuleProjectGenerator.generator.getBaseDirectory().toPath()).compile().runSlotomatic()`
`[CERT]` (`VideoDriverModuleGenerator.java:56-173`, this session, whole `generate()` method). It also
wires 5 default dependencies (`gx, net, nvideo, videoDriver, ffmpeg`, `:16,23-25`) on top of whatever
its `NDriverModuleGenerator` superclass constructor already wires, and unconditionally calls
`this.addWbPart()` in its own constructor (`:20`) — confirming a video-driver module is ALWAYS a
multi-part (rt+wb) module by construction, never rt-only.

**Static reconstruction of one previously-unread template, `gradle/ndriver/BNfooDevice.java.vm`
(212 lines, whole file, first read of this file in this corpus — [Block 74] only read
`BNfooNetwork.java.vm`'s head).** The template emits a complete, functional device-class skeleton
extending `niagara.ndriver.BNDevice`, implementing `BISecurityDashboardProviderAgent` — **a previously
unnoted N5-specific requirement: EVERY wizard-generated device class implements the Security Dashboard
agent interface (`getSecurityDashboardSectionHeader`/`getSecurityDashboardItems`/etc.) by default,
new territory no prior block flagged** `[CERT]` (`gradle/ndriver/BNfooDevice.java.vm:29-49`, whole class
declaration, this session). Statically substituting a representative class prefix (`${device.cls}` →
`BAcmeDevice`, `${network.cls}` → `BAcmeNetwork`, `${package}` → `com.acme.foo`) into the template's own
literal text reconstructs — without invoking Velocity or Gradle — a `BAcmeDevice.java` whose
`getNetworkType()` returns `BAcmeNetwork.TYPE`, whose `doPing()` is a `// TODO` stub calling
`pingOk()`, and whose Security Dashboard methods are populated with commented-out example
`SecurityDashboardItem` construction calls — this reconstruction is `[INFER]` (a manual textual
substitution, not a real Velocity render) but the SOURCE TEXT being substituted is `[CERT]` (the whole
file was read verbatim).

**Net verdict on B74-G1: ADVANCED.** Both halves of the residual [Block 74] itself left open are now
addressed: (1) `VideoDriverModuleGenerator`'s mechanism is confirmed `[CERT]`, matching
`NDriverModuleGenerator` exactly, not merely by analogy; (2) one previously-unread template
(`BNfooDevice.java.vm`) is fully read and statically reconstructed. **Not closed:** per this task's own
explicit framing, a REAL wizard invocation (actually running `NDriverModuleGenerator`/
`VideoDriverModuleGenerator` to scaffold a live module, then building it) was NOT attempted this
session — this remains requires-execution, exactly as [Block 74] itself flagged its own
still-open B74-G1 residual, and is re-affirmed as still open, not silently dropped.

## 89.8 — B74-G2 ADVANCED, not closed: the exact `cc.args`/`ld.args`/`ar.args` composition mechanism (commons-configuration2 `${…}` interpolation over plugin-populated fragment keys) and the devkit-properties override-merge algorithm are now fully `[CERT]`-traced; no real `devkit*.properties` artifact exists to confirm the literal list syntax `[CERT]`

[Block 74] §74.2 established the 3 top-level command-name keys (`cc.cmd`/`ld.cmd`/`ar.cmd`) and the
`devkit-<platform>.` key prefix, but did not trace HOW the full argument LIST for each command gets
assembled — naming this precisely as **B74-G2**'s residual ("recover devkit*.properties native-build
compiler/linker command SHAPES"). This session re-decompiles `NativeCommand.kt` (417 lines) and
`DevkitProperties.kt` (whole files, fresh) and finds the mechanism split cleanly in two.

**The plugin code populates SEVEN cc-side and NINE ld/ar-side FRAGMENT keys programmatically, but never
touches `cc.args`/`ld.args`/`ar.args` themselves.** `[CERT]` (`NativeCommand.kt:43-77`, the full list of
17 companion-object key-name constants, this session — `CC_CMD/CC_ARGS/CC_FLAGS/CC_DEFINES/CC_INCLUDES/
CC_SRC/CC_OUT/LD_CMD/LD_ARGS/LD_FLAGS/LD_LIBPATH/LD_OBJECTS/LD_LIBS/LD_OUT/AR_CMD/AR_ARGS/AR_OBJECTS/
AR_OUT`). `initializeCcProperties()` (`:199-236`, whole method) and `generateLinkProperties()`
(`:245-302`, whole method) programmatically `appendInclude`/`appendDefine`/`appendFlag`/`appendLibPath`/
`appendLib`/`appendObject` into `cc.includes`/`cc.defines`/`cc.flags`/`cc.src`/`cc.out`/`ld.flags`/
`ld.libpath`/`ld.libs`/`ld.objects`/`ld.out` — but **`cc.args`/`ld.args`/`ar.args` never appear as the
TARGET of any `setProperty`/`addProperty` call anywhere in this class** `[CERT]` (whole-file read
confirms zero such call, this session). Yet `cc()`/`link()`/`archive()` (`:311-317`, `:145-151`,
`:153-159`) read exactly `props.getString("cc.cmd")` + `props.getDevkitProperty("cc.args")` (and the
`ld`/`ar` equivalents) as the literal command + argument-list pair passed to `execute()`.

**`getDevkitProperty()` resolves through Apache Commons Configuration2's OWN `${…}` variable
interpolation, not plugin logic — confirming `cc.args`/`ld.args`/`ar.args` must be AUTHORED, in the
missing properties file itself, as interpolated references to the plugin-populated fragment keys.**
`[CERT]` (`DevkitProperties.kt:84-96`, whole method, this session):
```
84   public fun getDevkitProperty(key: String): List<String> {
85      val var10000: java.util.List = this.config.interpolatedConfiguration().getList(java.lang.String.class, this.asDevkitKey(key))
```
`this.config` is a `org.apache.commons.configuration2.PropertiesConfiguration` (`DevkitProperties.kt:25`,
class declaration, `: Configuration` — the whole class is a thin Kotlin wrapper over every
`org.apache.commons.configuration2.Configuration` method, confirmed by its ~50-method pure-delegation
body, this session) — `interpolatedConfiguration()` is that library's OWN documented mechanism for
resolving `${otherKey}` references inside a property's own value against the SAME configuration's other
keys. **This means the actual, never-written `devkit-<platform>.cc.args` property value must itself be
authored to reference `${cc.flags}`/`${cc.includes}`/`${cc.defines}`/`${cc.src}`/`${cc.out}` (and the
`ld`/`ar` analogues) — the plugin computes the FRAGMENTS, the devkit-properties FILE's own author
composes the final command-line SHAPE by writing the `cc.args`/`ld.args`/`ar.args` values as
interpolation expressions over them.** `[INFER]`: the exact literal delimiter/list syntax for such a
value (commons-configuration2 supports comma-delimited list values combined with `${…}` interpolation,
but the PRECISE convention Tridium's own devkit-properties author would use — e.g. whether `cc.args`
itself is one long interpolated string or a comma-joined list of individually-interpolated tokens — is
not independently confirmed, since no such file exists anywhere on this install to inspect directly).

**The override-merge algorithm across multiple matched `devkit*.properties`/`local.devkit*.properties`
files is also now fully traced (new, beyond [Block 74]'s own scope), via `DevkitProperties.make(baseFile,
vararg overrides)`:** `[CERT]` (`DevkitProperties.kt:307-381`, whole companion-object method, this
session) — for each key in an override file: a key ending in `-` REMOVES its own list values from the
BASE key of the same name with the trailing `-` replaced by `+` (`config.getList(var54).removeAll(...)`,
`:356-361`); a key ending in `+` APPENDS its values to the base (`:362-365`); a plain key OVERWRITES the
base UNLESS the base already declares a `key+` variant, in which case a non-empty plain-key value in the
override throws `IllegalArgumentException("Key $var48 must not set a value …")` (`:366-375`) — i.e. once
a base file commits a key to append-only (`+`) semantics, no override file may ever set it as a plain
scalar again.

**Net verdict on B74-G2: ADVANCED, significantly beyond [Block 74]'s own stopping point, still not
closed.** The exact property-key taxonomy AND the interpolation-based composition mechanism for
`cc.args`/`ld.args`/`ar.args` are now `[CERT]`-traced end to end, plus the previously-untouched
multi-file override-merge algorithm. What remains open, identically to [Block 74] §74.2's own verdict:
no `devkit*.properties` artifact exists anywhere on this install (re-confirmed, no new `find` needed —
[Block 74]'s own whole-install `find` this session's own repeat spot-checks did not surface one either)
to pin down the LITERAL list-value syntax an actual Tridium devkit-properties file would use — still
blocked on the same missing external artifact [Block 74] itself named.

## 89.x — Connections

- **[Block 74]** — closes **B74-G3** (§89.1) with bytecode-level certainty exceeding [Block 74]'s own
  `[INFER]`; advances **B74-G1** (§89.7, `VideoDriverModuleGenerator` now `[CERT]`-confirmed, one
  template statically reconstructed, wizard invocation still not executed) and **B74-G2** (§89.8, the
  `cc.args`/`ld.args`/`ar.args` composition mechanism and the override-merge algorithm now `[CERT]`,
  the literal file still missing) without contradicting anything [Block 74] itself found.
- **[Block 2]** — closes **B2-G2** (§89.2, correcting/confirming [Block 2]'s own JACE/embedded `[INFER]`
  guess with a byte-exact mechanism, sharper than guessed: in practice ONLY the `baja` module, and even
  then permanently suppressed) and **B2-G3** (§89.6, the doc exists, was simply misfiled by substring
  search).
- **[Block 16]** — closes **B16-G3** (§89.6): corrects [Block 16]'s own conclusion that the doc "may be
  web-only" — it ships in the SAME jar [Block 16] itself searched, under filename `test.html`, not a
  `testng`-substring name. [Block 16] §16.6's own `ColdRoomControlN5Test extends BTestNg` design choice
  is now independently validated as matching the ONLY pattern the official doc documents (§89.6).
- **[Block 29]** — closes **B29-G5** (§89.3) with a from-first-principles javac-source explanation,
  correcting [Block 29]'s own `[INFER]` guess (not "no `module-info.class`" but "invalid
  `Automatic-Module-Name`"); advances (folds in) **B29-G4** (§89.6) via the newly-found official doc,
  without closing the runtime-enforcement half [Block 29]'s own license-wall blocker still gates.
- **[Block 60]** — closes **B60-G1** (§89.5, an exhaustive 4-jar negative, sharper than [Block 60]'s own
  2-fragment negative) and **B60-G2** (§89.4, `Version.strip()`'s exact algorithm plus a 6-module
  extension of [Block 60]'s own 1-module spot check, resolving its flagged contradiction).
- **[Block 51]** — its own `ModuleXml.java:68` `getDependencyVersionLimit().set(2)` citation (quoted by
  [Block 60] §60) is independently re-confirmed this session at the same line's fresh re-decompile
  (`ModuleXml.java:69` in this session's own extraction — a 1-line offset from re-decompilation, not a
  content discrepancy; the constant and its context are identical).

## 89.x — Child gaps opened

- **B89-G1** (refines **B29-G5**) — WHY `compileModuleTestJava`'s own logged `LocnCantGetModuleNameForJar`
  error does not fail the overall Gradle task is still not traced into the `n-module`/`n-java` plugin's
  own task-wiring source (is this a preliminary/eager module-path enumeration pass whose result is never
  actually consulted for THIS jar, since nothing in the currently-compiled sources `requires` this exact
  self-referential automatic module by name? — [Block 29]'s own hypothesis, now narrowed but not
  confirmed). `investigable` — one more class (the `compileModuleTestJava` task's own
  `JavaCompile`/`CompileOptions` wiring in `NiagaraModulePlugin`) would likely settle it.
- **B89-G2** (refines **B60-G1**) — `ignoreRuntimeProfileCheck`'s consumer, if one exists at all in this
  Beta, is now narrowed OUT of every JVM-side artifact this corpus can decompile (n-plugin, slotomatic,
  baja, devkit — §89.5's exhaustive 4-jar negative) — the only remaining candidates are a closed native
  binary (`wb.exe`/`station.exe`) or a not-yet-shipped future consumer. `blocked` (native-binary /
  unshippped-feature, not a further decompile target).
- **B89-G3** (refines **B74-G2**) — obtain (or, from Tridium support/community sources, confirm the
  non-existence of anywhere in the wild of) a REAL `devkit*.properties` file for any actual N5 native
  target platform, to settle the exact list-value/interpolation SYNTAX `cc.args`/`ld.args`/`ar.args`
  would use in practice (comma-joined single value vs. multiple `cc.args+` fragment lines, etc.) —
  `blocked` (external artifact Tridium does not ship with this install, same shape as [Block 74]'s own
  B74-G2 residual and [Block 14]/[Block 17]'s license-gate pattern).
- **B89-G4** (new, opened by §89.7's `BNfooDevice.java.vm` read) — every OTHER `gradle/ndriver/*.vm` and
  `gradle/videodriver/*.vm` template (22 and 23 remaining respectively, after [Block 74]'s
  `BNfooNetwork.java.vm` head-read and this block's `BNfooDevice.java.vm` full read) has been inventoried
  by filename only, never read in full — the `BISecurityDashboardProviderAgent`-on-every-device finding
  (§89.7) suggests other templates may carry similarly unnoted N5-specific interface requirements worth a
  systematic read. `investigable`.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block89.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script
output):

```
== verify-block: niagara5-block89.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 7  (adj 6)
   [CERT-live] 1
   [CERT] 47  (adj 43)
   [CERT-doc] 8  (adj 6)
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 16  (adj 14)
-- ratio -- [INFER]/[CERT*] = 14/58 = 0.24
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   jar-entry  ColdRoomPan-rtTest.jar!META-INF/MANIFEST.MF  (jar archive path — not file-verifiable)
   jar-entry  devkit.jar!LIB-INF  (jar archive path — not file-verifiable)
   jar-entry  devkit.jar!LIB-INF/n-templates-5.0.54.9.2.jar  (jar archive path — not file-verifiable)
   jar-entry  docDeveloper.jar!doc/  (jar archive path — not file-verifiable)
   jar-entry  docDeveloper.jar!doc/buildN5.html  (jar archive path — not file-verifiable)
   jar-entry  docDeveloper.jar!doc/test.html  (jar archive path — not file-verifiable)
   jar-entry  kitControl.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   extern  DevkitProperties.kt:25  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  DevkitProperties.kt:307-381  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  DevkitProperties.kt:356-375  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  DevkitProperties.kt:84-100  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  DevkitProperties.kt:84-96  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Locations.java:1505-1516  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:220-232  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:68  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:69  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:80  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  NativeCommand.kt:43-77  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Version.java:129-131  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  Version.java:94-103  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  VideoDriverModuleGenerator.java:56-173  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  VideoDriverModuleGenerator.java:58-172  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  compiler.java:299  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  gradle/ndriver/BNfooDevice.java.vm:29-49  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  jdk.compiler/com/sun/tools/javac/file/Locations.java:1390-1420  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  jdk.compiler/com/sun/tools/javac/resources/compiler.java:299  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   resolved 0 of 19
   WARN    resolved 0 of 19 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**Reading the resolution split, per METHODOLOGY §11's own "decompiled-tree blocks will show zero/low
resolved citations — this is expected" clause, restated by [Block 74] §74's own precedent.** Every
`[CERT]` citation in this block resolves as either `jar-entry` (a live jar's own internal path — no line
number, not script-verifiable by design) or `extern` (this session's own fresh decompile output, written
to `/tmp/claude-1000/…/scratchpad/b89/`, never copied into `organized/`, per this task's own single-file
scope). Zero citations point INTO the pre-existing `organized/` tree, because every source this block
opens (`n-plugin`'s `natives`/`java.util`/`module.util` packages, `com.tridium.util.Version`,
`n-templates`' `VideoDriverModuleGenerator`/`BNfooDevice.java.vm`, a REAL JDK's own `Locations.java`/
`compiler.java`) is a package this corpus's `organized/` tree does not contain at all — matching the
class-of-citation pattern [Block 74] §74's own self-verify already established and explained. The
script's own `WARN resolved 0 of 19` line is its generic "declared type `mixed` is normally expected to
resolve something" advisory — it does NOT change the exit code (`exit 0`, confirmed) and the script's own
comment marks it explicitly advisory-only; it fires here specifically because this block, unlike [Block
74]'s own mixed-type block (which had 3 of 15 resolve into pre-existing `organized/` files), touches ZERO
pre-existing `organized/`-tree files — every single source this session opens is either a live jar's own
internal path or this session's own fresh scratchpad decompile, so a 0-of-19 resolution rate is the
correctly-expected outcome for this block's actual source mix, not a defect.

**Inline token-verify.** Every citation above points at a file this session `Read` in full or via a
targeted range this session, or a `javap -p -c`/`unzip`/`grep -rla` command this session ran directly
and read the literal output of — zero citations reused verbatim from any parent block's own text without
an independent re-open or re-run this session. Tokens independently re-confirmed present
(whitespace-normalized), by direct `grep -n`/`javap`/`Read`-tool output, not hand-recalled:
`throwUninitializedPropertyAccessException` (×3, one per getter, `NiagaraNativePlatform.class`
disassembly); `compact3`/`getMetadata().getLanguageVersion().canCompileOrRun(9)`/`"-profile"`/
`"compact3"` (`Compact3ArgumentProvider.kt`); `isCompact3`/`getNre`/`"baja"` (`ExtensionsKt.class`
disassembly, `ModuleXml.java:80`); `compiler.err.locn.cant.get.module.name.for.jar`/`"cannot determine
module name for {0}"` (`compiler.java:299`); `Automatic-Module-Name: com.angeles.ColdRoomPan-rtTest`
(the REAL PoC jar's manifest, not a decompile — `unzip -p`, this session); `strip`/`stripLength`/
`versions.length` (`Version.java:94-103`); `getDependencyVersionLimit().set(2)`/`strip(versionStrip)`
(`ModuleXml.java:69,377,386,402`); six independent `<dependency … vendorVersion="5.0.0"/>` reads across
`kitControl`/`bacnet`/`workbench`/`alarm`/`history`/`schedule` module.xml files, all uniform; `<a
href="test.html">TestNG Support in Niagara 5</a>` (`buildN5.html`) and the matching `doc/test.html`
23,607-byte listing entry (`docDeveloper.jar`); `interpolatedConfiguration()`/`getDevkitProperty`/
`asDevkitKey` (`DevkitProperties.kt:84-100`); the override-merge `+`/`-` suffix branches
(`DevkitProperties.kt:356-375`); `CC_CMD`/`LD_CMD`/`AR_CMD`/all 17 companion-constant key names
(`NativeCommand.kt:43-77`); `addTemplateWrite`/`Slotomatic.builder()…runSlotomatic()`
(`VideoDriverModuleGenerator.java:58-172`, cross-checked byte-identical against [Block 74]'s own
independently-read `NDriverModuleGenerator.java` shape); `BISecurityDashboardProviderAgent`/
`getSecurityDashboardItems` (`BNfooDevice.java.vm:48,139`). Token check: **≈35 distinct load-bearing
tokens** confirmed present in their cited source this session, plus 4 whole-jar negative-existence
sweeps (`RuntimeProfileCheck` absent from 3 of 4 searched jars, present-but-non-consuming in the 4th)
each run to completion and read in full, per METHODOLOGY §3's symmetric-opening-obligation rule.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; the `docDeveloper.jar!doc/
test.html`/`doc/buildN5.html` citations are shipped Niagara product documentation (`[CERT-doc]`), read
directly from the jar this session, not an MCP tool call.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block89.md`. Per this
task's explicit single-file, read-only-elsewhere scope, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`
regeneration and backlog re-classification are deliberately NOT performed this session — left to the
orchestrator, matching [Block 74]/[Block 80]'s own convention for the same instruction. Fresh decompile/
disassembly output for this session lives under `/tmp/claude-1000/-home-cristian-niagara-research/
dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b89/` (this session's own scratchpad) — not copied into
`organized/`; no decompiled third-party or Tridium source, and no JDK source, was committed to git this
session; no other repo file was modified.
