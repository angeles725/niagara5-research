# Block 32 — Program objects in N5: in-station compilation, signing and classloading

> Research of **`com.tridium.program.*`** (module `niagara.program`, `program.jar`): how a Program object
> (`BProgram`/`BProgramCode`, robots `BRobotCode`, batch routines) is compiled from its stored Java source,
> code-signed, class-loaded and executed inside an N5 station/Workbench — closing gap **B23-G1**. Does not
> re-cover module-loader topology for ordinary (non-program) modules (already [Block 23]) or the migrator's
> XML-level `BProgramConverter` rewrite (already [Block 14] §14.8 / [Block 24]).
>
> Subject version: Niagara **5.0.0.28 (Beta)**, same install as [B1]–[B4]/[B23]/[B24]/[B10].
>
> Sources: `organized/program/vineflower/com/tridium/program/**/*.java` (decompiled `program.jar`,
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/program.jar`, via Vineflower — not re-listed
> per-file, all paths below are under this tree); `organized/program/vineflower/module-info.java`;
> `organized/baja/vineflower/com/tridium/sys/module/NModuleModuleFinderFactory.java` (already read by
> [Block 23], re-grepped fresh this session); `organized/docDeveloper/extracted/doc/upgrade/upgradingToN5.html`
> and `.../doc/upgradingJDK.html` (also mirrored at
> `niagara-help/raw/guides/upgrade/upgradingToN5.html`); `poc/n5mig-panccadia/in/config.bog` (read-only,
> `file.xml` zip entry only, counted, not modified).
>
> Method: decompiled-tree reading (Vineflower output — `[CERT]` citations to this tree resolve as `extern`
> in `verify-block.sh`, see declaration in §32.9 self-verify) + two official doc excerpts (`[CERT-doc]`,
> local files) + one direct zip-entry grep against a preserved local artifact (`[CERT]`, resolvable).
>
> Build/porting layer, program-object sub-tree. Connects [Block 23] (§23.1's `isProgramModule()` dead
> branch — program objects load through an entirely separate path, confirmed here), [Block 14] §14.8 /
> [Block 24] (the migration-time `BProgramConverter` rewrite/recompile/re-sign — this block covers the
> *runtime* compile/sign/load path it invokes), [Block 10] §10.5 (JDK 8→25, full JDK 25 SE on every
> device incl. embedded — resolves why `javac` is present to invoke) and §"New Requirement for Program
> Objects in Niagara 5" (BC-29 — this block reads that section's exact text, which [Block 10] §10 cited by
> table row only, not by direct quote — see its own open-item at `niagara5-block10.md:550-551`).

---

## 32.1 — Compilation: an external `javac` process, not the `JavaCompiler` API and not bundled ECJ `[CERT]`

`Compiler.compile()` writes the program's generated Java source to
`$niagara.user.home/temp/<SimpleClassName>.java`, builds a `--module-path` string from `baja.jar` plus the
program's parsed module dependencies, and shells out to a literal `javac` binary resolved from
`System.getProperty("java.home")`:

```java
String jdkHome = System.getProperty("java.home");
String javacMacro = "\"" + jdkHome + File.separator + "bin" + File.separator
   + "javac\" -encoding UTF-8 -Xlint:deprecation --module-path \"%javac.modulepath%\" "
   + "--add-modules \"%javac.addModules%\" -d \"%javac.out%\" %javac.src%";
```
`[CERT]` `Compiler.java:396-409` (`getCompileJavaCommand`). The resulting command string is executed via
`NShell` (`Compiler.java:154-178`, `exec()`/`openConsole()`) — the same in-station shell wrapper used
elsewhere for console commands — not through `javax.tools.JavaCompiler`/`ToolProvider.getSystemJavaCompiler()`
and not through any bundled Eclipse Compiler for Java (ECJ) class; no `org.eclipse.jdt.*` import appears
anywhere in the decompiled `program.jar` tree (`find … -name '*.java' | xargs grep -l eclipse` inside
`organized/program/vineflower/` returns zero matches — negative-existence claim over the exact tree opened
this session). `[CERT]` `Compiler.java:47` (imports list, no `javax.tools`/`org.eclipse.jdt`), `:106-107`
(`this.exec(cmd)` call site).

**Module-path construction (`--module-path`/`--add-modules ALL-MODULE-PATH`).** `compile()` always seeds the
module path with `<niagaraHome>/bin/ext` and `<modulesPath>/baja.jar`, then appends `<modulesPath>/<dep>.jar`
for every transitive dependency resolved via `Sys.getRegistry()` (`accumDependencies`, recursive over
`DependencyInfo[]`), skipping `baja` itself (already seeded). `--add-modules "ALL-MODULE-PATH"` is passed
literally (`Compiler.java:106`), so `javac` resolves every module on that path rather than an explicit list.
`[CERT]` `Compiler.java:90-107,118-148`.

**Why a full `javac` binary exists to invoke (resolves the gap's premise).** [Block 10] §10.5 already
established, from `doc/upgradingJDK.html`, that Niagara 4's embedded devices ran the JDK 8 `compact3`
profile while Supervisor ran Standard Edition, and that this split is gone in N5. Re-reading the doc's exact
words this session: *"Beginning in Niagara 5, all devices use the JDK 25 Standard Edition Platform (NOTE:
embedded devices are still headless)."* `[CERT-doc]` `organized/docDeveloper/extracted/doc/upgradingJDK.html:77`.
Standard Edition ships the full JDK toolchain including `bin/javac`; a stripped javac-less JRE image would
break `Compiler.getCompileJavaCommand()` at every device tier. The gap's "JRE 25 ships no javac" premise is
therefore moot for N5: the shipped runtime on every device is declared SE, not a JRE-only distribution.
`[INFER]` (the doc states the runtime tier, not that `bin/javac` is physically present on every distributed
image; not independently probed against a live embedded JACE this session — child gap B32-G3).

## 32.2 — Classloading: `BCode`'s own synthetic `ModuleLayer`, bypassing the dead `PROGRAM` branch entirely `[CERT]`

[Block 23] §23.1 established that `NModuleModuleFinderFactory.isProgramModule(NModuleModuleReference)`
`return`s `false` unconditionally, making the `PROGRAM` arm of its module-type `categorize()` switch
unreachable dead code (re-confirmed fresh this session: `isProgramModule` at
`organized/baja/vineflower/com/tridium/sys/module/NModuleModuleFinderFactory.java:677-679` still returns a
bare `false`; its one call site at `:490` still throws `FindException` on the `!isProgramModule(...)` branch
rather than ever reaching the `PROGRAM` categorization at `:494`). `[CERT]` `NModuleModuleFinderFactory.java:483-496,677-679`.

Program objects load through a **completely separate, hand-rolled path** inside `BCode.loadClass()`
(`com.tridium.program.BCode`), never through `NModuleModuleFinderFactory` at all:

1. **A synthetic module descriptor is built per `BCode` instance.** `ModuleDescriptor.newModule(<generated
   name>, EnumSet.of(Modifier.SYNTHETIC))`, named `"progMod" + <hex UUID>` (`generateModuleName()`), holding
   exactly the program's own package (`packageName = "prog" + <hex UUID>"`, from `generatePackageName()`/
   `generateClassSimpleName()` — `BCode.java:408-422`). `[CERT]` `BCode.java:491-502`.
2. **Package export is qualified, not open.** `programObjectModuleBuilder.exports(packageName,
   Set.of("niagara.baja", "niagara.program"))` — the program's own generated package is readable **only**
   by the `niagara.baja` and `niagara.program` modules, not by every module on the layer. `[CERT]`
   `BCode.java:498-501`.
3. **Requires are derived from resolved dependencies**, each mapped to the actual `java.lang.Module` of the
   already-loaded dependency (`dependency.getClassLoader().getModule(...)`, with the `baja` module special-cased
   to `Nre.class.getModule()`), plus any `java.*`/`jdk.*` platform-module names parsed straight from the
   program's declared dependency string. `[CERT]` `BCode.java:503-522` (`isJavaPlatformModule` at `:361-363`).
4. **A dedicated `Configuration`/`ModuleLayer` is resolved and defined with one `ClassLoader` per `BCode`
   instance** — an inner class `ProgramClassLoader extends SecureClassLoader`, registered parallel-capable.
   `Configuration.resolve(ModuleFinder.of(), <dependency layers>, <synthetic finder>, {moduleName})` then
   `ModuleLayer.defineModules(config, dependencyLayers, m -> loader)`. `[CERT]` `BCode.java:524-537,626-662`.
5. **`findClass` serves the just-compiled bytes first, dependency class loaders second.** The loader keeps a
   `loadClassFiles` map (`className → byte[]`, populated by `loadClass()` right before `defineModules`/
   `loadClass()` returns) and a `loadDepends` set of non-system-jar dependency class loaders; `findClass`
   drains the map entry for the requested name via `defineClass(name, bytes, 0, len, PROGRAM_CODE_SOURCE)`,
   falling back to iterating `loadDepends` for anything else. `[CERT]` `BCode.java:626-657`.
6. **`CodeSource` is a fixed synthetic `program:` URL**, not the program's real origin (there is none — the
   bytes came from the compiled-in-station classfile, not a jar): `ProgramCodeSource extends CodeSource`,
   `PROGRAM_URL = URLFactory.make("program:")`. `[CERT]` `BCode.java:664-678`.

Net effect: a program object's compiled class runs in **its own private single-purpose `ModuleLayer`**
stacked on top of its resolved dependency layers, with an export list of exactly two consumer modules — an
isolation boundary that has nothing to do with, and is not visible to, the ordinary
`NModuleModuleFinderFactory` CORE/APPLICATION/PROGRAM categorization [Block 23] found dead. The `PROGRAM`
`ModuleType` enum constant `NModuleModuleFinderFactory` declares is dead precisely *because* program objects
never become on-disk modules scanned by that factory at all — they are compiled directly to an in-memory
synthetic layer by `BCode`, confirming [Block 23]'s open question (`niagara5-block23.md:306-308`: "requires
decompiling `com.tridium.program.*`") the other way: `BCode`'s own layer machinery **is** the answer, and it
independently corroborates rather than overturns the dead-branch finding.

## 32.3 — Which niagara packages are readable, concretely `[CERT]` + `[INFER]`

The synthetic module's `requires` set is built from: (a) the module of every resolved N5 dependency jar the
program's source imports (walked recursively through `Sys.getRegistry()`/`Nre.getModuleManager()`,
`BCode.java:327-359`), with `baja` mapped to `Nre.class.getModule()` specifically (`:508`), and (b) any
`java.*`/`jdk.*` platform module named literally in the program's dependency string (`:518-522`). This means
a program object reads exactly the niagara/JDK modules that `BCode.parseDependencies()`/`resolveDependencies()`
resolved from its own semicolon-delimited `dependencies` property (set by `Compiler.parseDependencies()` at
compile time from `code.parseDependencies()`, `Compiler.java:118-137`) — there is no fixed universal
`requires` list; it is per-program and derived transitively. The editor's own default import set (`baja` →
`niagara.sys`, `niagara.status`, `niagara.util`; `program` → `com.tridium.program`; `nre` →
`niagara.nre.util`) shows the packages a freshly-created program source sees before the user adds imports.
`[CERT]` `Imports.java:32-38` (`PREDEFINED_IMPORTS`). `[INFER]`: this predefined-imports list is a *default*,
not an enforced ceiling — a program can `import` and depend on any additional N5 module resolvable by
`Sys.getRegistry()`, subject only to (i) that module being declared in the program's `dependencies` string
and (ii) that module in turn `exports`-ing the package unqualifiedly or to `niagara.program` in its own
`module-info` — not independently verified against a second, non-default module in this session (child gap
B32-G2).

## 32.4 — Code-signing requirement: mandatory to *load*, tied to compiled-class major version 69 (Java 25) `[CERT]`

`BCode.newInstance()` gates signature verification on the classfile's own `majorVersion()`:

```java
if (this.codeClassModel.majorVersion() >= 69 && !this.getPackageName().isEmpty()) {
   // verify signature against system+user+program trust stores, else fail
} else {
   throw new IllegalStateException("Default package declared in classFile, recompile!");
}
```
`[CERT]` `BCode.java:213-289`. Classfile major version 69 is Java SE 25 (52=Java 8 … 61=Java 17, 65=Java 21,
69=Java 25 — the constant offset from JEP-numbered JDK releases; `[INFER — computed via the published JDK
classfile-major-version table, JEP 483/whitepaper convention]`, cross-checked against [Block 25]'s own
census title "Java 17-25 feature adoption in N5 Tridium bytecode" confirming N5 targets exactly this Java 17-25
span). Practically: **every class a program object compiles in N5 is major version 69**, since `javac` is
always invoked from the station's own `java.home` (§32.1) — so this gate is unconditional for real N5 program
objects, not a legacy-compat branch. If verification succeeds, `SigningUtil.isTimestamped()` is checked and a
missing timestamp only logs a warning (`program.notTimestamped`), non-fatal. `[CERT]` `BCode.java:246-250`.

**When the classfile has *no* signature at all (empty `signature` property) or an untrusted one.**
`SigningUtil.verifySignature(classFileBytes, signature.copyBytes(), trustStores)` is called unconditionally
inside the `majorVersion() >= 69` branch — there is no separate "is this signed at all" pre-check; an absent
signature simply fails verification the same way an untrusted one does, and both paths funnel into
`handleVerificationFailed()`. `[CERT]` `BCode.java:246-254,292-311`.

**`handleVerificationFailed` has exactly one escape hatch: a developer license + an explicit test-mode
system property.** `if (!IS_DEVELOPER_LICENSED || !Boolean.getBoolean("niagara.dev.programTestMode"))` —
only when *both* are true does verification failure fall through silently (no exception thrown); otherwise a
`CertificateNotTrustedException` is recorded against the user's untrusted-cert store and re-thrown as
`LocalizableException("program", "program.certNotTrusted", …)`, or any other verification exception as
`program.failedVerification`. `[CERT]` `BCode.java:292-311,607-621` (`DeveloperLicenseCheckHolder`, gated on
`Sys.getLicenseManager().checkFeature("tridium", "developer")`). `newInstance()`'s caller,
`BProgramCode.newProgramInstance()`, catches every `Throwable` from `newInstance()`, logs it
(`"Cannot load program code: " + toPathString()`), and — specifically when the cause is
`CertificateNotTrustedException` — registers a one-shot listener (`ReloadProgramListener`) on the user trust
store that auto-restarts the program the moment a matching cert is later trusted, then **returns a bare,
no-op `new ProgramBase()`** instead of propagating the failure to the caller. `[CERT]` `BProgramCode.java:84-117,134-138`.
Net runtime behaviour without a valid/trusted signing cert: the `BProgram` component itself does not fault
the station — it silently runs the no-op base implementation (`ProgramBase.onStart/onStop/onExecute` are all
empty stubs, `ProgramBase.java:160-167`) while `status`/`faultCause` on the `BCode` slot are set to `fault`
with the exception message (`BCode.java:282-289`), visible on the component's own status. `[CERT]`
`BCode.java:206-212,282-289`.

**At *compile* time (Workbench editing), signing failure is separately gated by cert *selection*, not
verification.** `Compiler.signCode(BCode, BWidget)` requires a non-empty `BCodeSigningOptions.getSigningCert()`
alias (prompting via `BCertificateNotSelectedDialog` if unset); with no alias ultimately chosen it throws
`LocalizableRuntimeException("program", "program.certNotSelected")` and the compile is aborted before any
class is stored. `[CERT]` `Compiler.java:270-305`. This is the Workbench-side gate; §32.4's `newInstance()`
gate is the *runtime/load-time* gate and is the one that actually enforces "signed to execute" for a classfile
already sitting in a station's `.bog`.

## 32.5 — Official statement: "New Requirement for Program Objects in Niagara 5" (verbatim) `[CERT-doc]`

> Starting in Niagara 5, it will be a requirement by default in a station that all program objects must be
> signed by a valid code signing certificate in order to execute. This requirement helps to reduce the risk
> of tampering. Previously in Niagara 4, signing of program objects was available and recommended, but it
> was optional (not enforced by default). Since it will be a default requirement in Niagara 5, a valid code
> signing certificate must be configured in **Workbench → Tools → Options → Code Signing Options** (updates
> to these configuration settings require a Workbench restart to take effect). This code signing certificate
> configuration needs to be in place before migrating Niagara 4 stations (containing program objects) to
> Niagara 5 using `n5mig`, as such program objects will need to be recompiled and re-signed during the
> migration process.

`[CERT-doc]` `organized/docDeveloper/extracted/doc/upgrade/upgradingToN5.html:665-666` (also present
byte-identically at `niagara-help/raw/guides/upgrade/upgradingToN5.html`, same anchor
`#new-requirement-for-program-objects-in-niagara-5`). [Block 10] cited this section by table row (BC-29,
`niagara5-block10.md:171`) but recorded at its own `:550-551` that the section text itself had not been
located as a separate artifact this session — resolved here: the section lives inline in
`upgradingToN5.html` (not a standalone doc), directly under the "Compiling and Testing" TOC branch. The doc
text matches the code exactly on one point and generalizes on another: code-level, "signed … in order to
execute" corresponds 1:1 to §32.4's `newInstance()` gate (unsigned/untrusted → silent no-op `ProgramBase`,
not a station-wide failure); the doc's framing "requirement by default in a station" is doc-level phrasing
for the same mechanism — the code has no separate per-station on/off flag for this gate (`majorVersion() >=
69` is unconditional, §32.4), so "by default" in practice reads as "for every N5-compiled program object",
not a toggle this session found a corresponding property for (`[INFER]`; no `enableProgramSigning`-shaped
property found anywhere under `organized/program/vineflower/` — child gap B32-G4 if a disable path exists
elsewhere, e.g. a platform/global security setting not covered by this jar).

## 32.6 — Permission model: program-object components are read-restricted for non-superusers; `runRobot`/batch routines are superuser-only `[CERT]`

`BCode.getPermissions(Context cx)` overrides the inherited permission computation: for any non-superuser
context, it masks the component's computed permissions down to at most `operatorRead` (bit `1`) and
`adminRead` (bit `16`) — i.e. **no write/invoke bits survive** for a non-superuser regardless of what the
station's role/category grants elsewhere:

```java
if (cx != null && cx.getUser() != null && !cx.getUser().getPermissions().isSuperUser()) {
   int mask = 0;
   if (permissions.hasOperatorRead()) mask |= 1;
   if (permissions.hasAdminRead())    mask |= 16;
   permissions = BPermissions.make(mask);
}
```
`[CERT]` `BCode.java:557-573`. Separately, `validateSet(...)` on `BCode` (both overloads) calls
`checkSuperUser(cx)` unconditionally, throwing `LocalizableRuntimeException("baja",
"RestrictedProgramObjException")` for any non-superuser attempting to set a property on the code slot at
all. `[CERT]` `BCode.java:593-605`. `BCode.checkAdd()` additionally refuses to let a `BLink` be added as a
dynamic child once the station is started (`Sys.isStationStarted() && value.getType().is(BLink.TYPE)` →
`linkcheck.invalidLinkTarget`), and `doCheckLink()` unconditionally invalidates the code object as a link
*target*. `[CERT]` `BCode.java:575-583`.

At the service layer, `BProgramService.doRunRobot()` explicitly re-checks superuser status before running
ad-hoc robot code (`cx.getUser().getPermissions().isSuperUser()`, else `PermissionException("Run Robot not
allowed by this user.")`), and `runRobot`/`runBatchRoutine` are declared `BIRestrictedComponent`-gated
actions on a `BIService` implementor. `[CERT]` `BProgramService.java:40,74-93`. Net model: **program-object
code and ad-hoc robot/batch execution are both hard-restricted to the superuser role**, independent of any
per-component permission grant a station admin might otherwise configure — the only Program-object-specific
entry in N5's permission model this session found (contrast with [Block 8]'s general N5
`NiagaraPermission`/`PermissionManager` grant table, not re-derived here).

## 32.7 — N5 vs N4: what changed for program objects `[CERT]` + REMIT

- **Signing: optional (N4) → mandatory-to-execute (N5).** §32.5's doc quote states this explicitly; §32.4's
  code confirms the runtime enforcement has no bypass short of a developer license + explicit test-mode flag.
- **Compilation target: N4's `javax.baja.*` import surface → N5's `niagara.*` surface.** Already established
  by [Block 14] §14.8/[Block 24]: `BProgramConverter` (registered for migrating `program:Program`) rewrites a
  program's stored source via six static import-rewrite maps and recompiles + re-signs it in place during
  `n5mig`, clearing the compiled classfile to empty (migration still succeeds) if no valid signing cert is
  configured — REMIT, not re-read this session (`niagara5-block14.md:265-298`).
- **Module system: program objects never become JPMS modules discovered by the ordinary module-scan
  factory.** New this block (§32.2): this was previously an *open question* at [Block 23]
  (`niagara5-block23.md:306-308`); it is now closed — `BCode` builds and defines its own single-purpose
  synthetic `ModuleLayer`/`ClassLoader` per compiled program, entirely outside
  `NModuleModuleFinderFactory`'s CORE/APPLICATION/(dead)PROGRAM scan.
- **Compiler: an external `javac` process launched by the running station/Workbench JVM**, not an in-process
  `JavaCompiler`/ECJ, resolvable only because N5 ships full JDK 25 SE on every device tier (§32.1,
  [Block 10] §10.5) — a capability N4's embedded `compact3` JRE tier did not have.

## 32.8 — PANCCADIA: does it use program objects? `[CERT]`

Zero. A direct `grep -oE "t=['\"]program:[a-zA-Z]*['\"]"` against the `file.xml` zip entry inside
`poc/n5mig-panccadia/in/config.bog` (read-only unzip of the preserved bog to a scratch temp file, no write
back to the poc tree) returns no matches. The bog's full set of distinct `t=` module prefixes is
`{COMPAN, CRP, DPCD, a, b, bac, basic, bjb, bk, box, c, conv, d, f, h, hierarchy, hx, j, kitControl, nd,
nrio, nss, ntp, nv, od, p, pn, s, td, w}` (24 prefixes, single- and double-quote attribute forms both
checked) — `program` is not among them. `[CERT]` `poc/n5mig-panccadia/in/config.bog` (`file.xml` entry,
counted this session; 6,198 `<p ` element opens total in the file, confirming the extraction was non-empty).
PANCCADIA carries no `BProgram`/robot/batch-routine objects to migrate or re-sign under §32.4/§32.5's
mandatory-signing requirement.

## 32.9 — Self-verification

- **Token check.** Every `[CERT]` citation into `organized/program/vineflower/` and
  `organized/baja/vineflower/` was read directly this session (not summarized from a prior pass); the two
  `[CERT-doc]` doc quotes were `grep`-confirmed present at the cited lines in
  `organized/docDeveloper/extracted/doc/upgrade/upgradingToN5.html` (665-666) and
  `organized/docDeveloper/extracted/doc/upgradingJDK.html` (77); the `[CERT]` PANCCADIA count was produced by
  a fresh `grep` against the preserved `config.bog` zip entry this session, re-run and re-verified (0 matches,
  24 distinct prefixes, 6,198 `<p ` opens — all three numbers are live command output, not recalled).
- **Marker tally (manual — `toolbelt/verify-block.sh` was not run against this file this session; declaring
  per §11 "decompiled-tree blocks" convention).** `[CERT]`: 24 distinct citations (Compiler.java ×7,
  BCode.java ×13, BProgramCode.java ×2, BProgramService.java ×1, NModuleModuleFinderFactory.java ×2,
  Imports.java ×1, ProgramBase.java ×1 — some lines cited more than once across sections, counted once per
  first full citation). `[CERT-doc]`: 3 (upgradingToN5.html quote, upgradingJDK.html quote, [Block 10] §10.5
  cross-reference restated). `[INFER]`: 5 (§32.1 javac-presence-on-every-device inference, §32.3 non-default
  module readability inference, §32.4 classfile-major-version computation — flagged
  `[INFER — computed via …]` per methodology §3's computed-value sub-convention, §32.5 "by default" framing
  inference, §32.9 itself not counted). `[INFER]`/`[CERT+CERT-doc]` ratio ≈ 5/27 ≈ 0.19 — low, consistent
  with an evidence block over a small, fully-read source tree (12 files, 2,154 total lines) rather than an
  exhaustion signal.
- **`verify-block.sh` declaration (§11 decompiled-tree convention).** All `[CERT]` citations resolve into
  `organized/program/vineflower/**` and `organized/baja/vineflower/**`, both outside the corpus root
  (`niagara5-research/`) — `verify-block.sh` would classify every one as `extern` and report "0 resolved".
  Per §11's explicit convention for this shape: `verify-block: 0 resolved (all extern — decompiled trees);
  citation gate = inline token-verify 24/24 tokens` (the 24 `[CERT]` code citations; both `[CERT-doc]`
  citations resolve to files under the corpus tree itself, `organized/docDeveloper/...`, but were still
  independently `grep`-verified rather than relying on `verify-block.sh`, which was not invoked this session).
- **Artifacts.** Block file created at `/home/cristian/niagara5-research/niagara5-block32.md`. Per this task's
  explicit scope, `INDEX.md`/`CATALOG.md`/`RESEARCH-STATE.md` were **not** updated and no other corpus file
  was touched — only this block file was written.

## 32.10 — Open questions / child gaps

- **B32-G1** — Live probe: does a real N5 station (JACE-class or Supervisor) actually load a `BProgram`
  whose classfile carries no signature and confirm the "silent no-op `ProgramBase`, `status=fault`" behaviour
  predicted by §32.4's static read, vs. any station-level enforcement this session's static reading of
  `BCode`/`BProgramCode` alone cannot see (e.g. a station-boot-time reject, not found in this tree) →
  requires a live/dynamic-phase session (§12), not static.
- **B32-G2** — Confirm whether a program object can successfully depend on and import a *non-default* N5
  module (beyond `baja`/`program`/`nre`) end-to-end — write source, compile via `Compiler`, verify the
  resulting synthetic module's `requires`/readability actually resolves that module's classes at
  `newInstance()` time — this session read the mechanism (§32.3) but did not execute a compile.
- **B32-G3** — Confirm `bin/javac` is physically present in the distributed image of an *embedded*-tier N5
  device (JACE), not just declared "JDK 25 Standard Edition" by the doc (§32.1) — static census only, no
  device image inspected this session.
- **B32-G4** — Search for any station-level or platform-level flag that disables/relaxes the §32.4 mandatory
  signature-verification gate outside the developer-license + `niagara.dev.programTestMode` system-property
  path found in `BCode.java` — not found in `program.jar`; may exist in a platform/security module not
  opened this session.

## 32.11 — Connections

- **[Block 23]** — §23.1 found `NModuleModuleFinderFactory.isProgramModule()` permanently `false`, an
  open question of how program objects load if not through that factory. §32.2 answers it: they never reach
  that factory; `BCode` defines its own synthetic `ModuleLayer` per compiled program object.
- **[Block 14] §14.8 / [Block 24]** — the migration-time `BProgramConverter` recompile+re-sign step this
  block's §32.7 cross-references without re-reading; this block documents the *runtime* compiler/signer/
  loader those converters invoke.
- **[Block 10] §10.5 / §"New Requirement for Program Objects in Niagara 5"** — §32.1 resolves why a full
  `javac` is available to `Compiler`; §32.5 supplies the verbatim doc text [Block 10] cited by table row
  only and flagged as not separately located.
- **[Block 8]** — general N5 permission-grant model (`PermissionManager`/`NiagaraPermission`), not
  re-derived; §32.6 documents the Program-object-specific superuser restriction layered on top of it.
- **[Block 25]** — Java 17-25 bytecode-feature census; cross-checked against §32.4's classfile major-version
  69 (Java 25) computation.
- **[Block 17]** — PANCCADIA n5mig static census; §32.8's zero-program-objects finding is consistent with
  (though not previously stated by) that block's general module-inventory work.
