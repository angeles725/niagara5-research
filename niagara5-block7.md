# Block 7 — N5 code generation: Slotomatic vs the nap annotation processor

> Research of **what `com.tridium.slottool.Slotomatic` generates vs what the `com.tridium.nap`
> JSR-269 annotation processor generates** in Niagara N5 5.0.0.28 beta — closing child gap B2-G1
> ([Block 2] §2.6). Covers: the processor's own class identity, its `META-INF/services` registration,
> the 3 concrete `Processor` implementations and what each one does (or does not) write, Slotomatic's
> continued in-class code generation and its exact marker/region syntax, whether Slotomatic still
> rewrites source in place, the supported-annotation set (both mechanisms), the `niagara.*` package
> rename away from N4's `javax.baja.*`, and the observed division of labor with its residual open
> question (Gradle task-graph ordering — Kotlin-lambda decompile ceiling, named child gap). Does NOT
> cover: a live N5 `gradlew build` run (no runnable station in this beta install — same limitation as
> [Block 2]), the full `SlotMode`/`PropertyProcessor`/`ActionProcessor` code-generation internals beyond
> what is needed to state the marker/output shape, or the legacy Baja-comment grammar
> (`model/comment/parsers/*`) beyond noting its size and role.
>
> Subject version: **Niagara 5.0.0.28 beta**. Artifacts: `niagaraAnnotationProcessors.jar`
> (sha256 `fbffe97b…c2a0832d`, at `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/`) and
> `tridium-niagara-slotomatic-library-5.0.2.jar` (sha256 `e7a8f322…93efb66c2`, at
> `/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/tools/tridium-niagara-slotomatic-library/5.0.2/`).
>
> Sources:
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/niagaraAnnotationProcessors.jar` — the module B2-G1
>   could not locate (absent from the 247-module minimal `config/5.0.0.28/modules/` set searched in
>   [Block 2]); found this session under `bin/ext` instead (the Gradle-build classpath location, not the
>   station-runtime module set — consistent with it being a build-time-only artifact).
> - `/mnt/c/Program Files/Niagara/5.0.0.28/etc/m2/repository/com/tridium/tools/tridium-niagara-slotomatic-library/5.0.2/tridium-niagara-slotomatic-library-5.0.2.jar`
>   — same artifact [Block 2] §2.1/§2.5 identified but did not decompile.
> - `/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/NiagaraModulePlugin.kt` — re-opened
>   this session for the Slotomatic-task/compileJava wiring question (§7.7).
> - N4 remittances (READ, not re-derived — cited `REMIT`): `niagara-research` B12 §12.1.8, B631
>   §631.1-2, B434, B637 §637.2, B711, B780, B863 (package-name cross-check).
>
> Method: `python3 zipfile` inventory of both jars (`META-INF/services/javax.annotation.processing.Processor`
> search + full `.class` listing); Vineflower 1.12.0 full-jar decompilation of both jars (JDK 26 —
> `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`) into `/tmp/claude-1000/n5b7/vf-out/` (AP jar) and
> `/tmp/claude-1000/n5b7/vf-slotomatic/` (Slotomatic jar); `javap -p -v` byte-level cross-check of the 3
> registered processor classes against their decompiled source (JDK 26 `javap`). Direct `Read` of every
> cited `.java` file, whole-file or the shown range. `python3 tools/corpus-nav.py find <term>` against the
> N4 `niagara-research` corpus for package-rename and REMIT cross-checks. Markers (METHODOLOGY §3):
> `[CERT]` local primary source (`file:line` or `zip-entry:path`) · `[CERT-doc]` official installed HTML
> doc (none newly opened this session — [Block 2] already cited `buildN5.html`'s claim; this block
> supplies the primary-source confirmation) · `[INFER]` deduction · `REMIT` = cited from a prior corpus
> block, not re-opened this session.
>
> N5 build-toolchain layer, second block. Connects [Block 2] (opened this gap, §2.6/§2.9) and REMIT
> `niagara-research` B12/B631/B434/B637 (the N4 baseline this directly supersedes/extends).
>
> **Type:** mixed — direct decompiled evidence (`[CERT]`) for the mechanism, with one `[INFER]`-flagged
> synthesis section (§7.8, the kit-impact delta) and one genuinely unresolved technical point (§7.7,
> Kotlin-lambda decompile opacity on the exact task-graph edge).
>
> **Breakthrough:** the `niagaraAnnotationProcessors.jar` that [Block 2] could not find (it searched only
> `config/5.0.0.28/modules/`) is sitting in `bin/ext/` — the Gradle-classpath location, not the
> station-module location — and its `META-INF/services/javax.annotation.processing.Processor` file names
> exactly 3 classes. Reading them settles B2-G1 outright: **`NiagaraTypeAnnotationProcessor` is the ONLY
> code that writes `module-include.xml`, and it does nothing else; `NiagaraSlotProcessor` does not
> generate a single line of code — it only VALIDATES that Slotomatic already ran, emitting the literal
> compiler error "have you run slot-o-matic?" when a `@NiagaraProperty`/`@NiagaraAction`/`@NiagaraTopic`
> name has no matching field; and `NullProcessor` silently claims `@NiagaraEnum`/`@NiagaraSingleton`/
> `@NiagaraSlots`/`@niagara.rpc.NiagaraRpc`/`@NoSlotomatic` and does absolutely nothing with them.** All
> in-class slot code generation (the getter/setter/constant boilerplate) is still 100% Slotomatic's job,
> unchanged in kind from N4 — the JSR-269 processor's entire contribution to code generation is the
> `module-include.xml`/`moduleTest-include.xml` type list.

---

## 7.1 — The processor jar: found in `bin/ext/`, not in the station module set `[CERT]`

`niagaraAnnotationProcessors.jar` (67 zip entries, 52 `.class` files) ships at
`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/niagaraAnnotationProcessors.jar` (with a companion
`.jar.sig`), alongside `annotations-13.0.jar`, `jakarta.annotation-api-3.0.0.jar`, and the Jetty
annotation-scanning jars — i.e. it lives with the OTHER build/compile-time-only annotation jars under
`bin/ext`, not under `ProgramData/.../config/5.0.0.28/modules/` where [Block 2] looked (that directory
holds 247 STATION runtime modules; this artifact is absent from it). `[CERT]`
(`find "/mnt/c/Program Files/Niagara/5.0.0.28/bin"` listing, this session) — this resolves [Block 2]'s
open question about WHY the module wasn't found: it was never a station module to begin with, it is a
Gradle-annotationProcessor-classpath jar, matching how it is consumed in `build.gradle.kts`
(`niagaraAnnotationProcessor(":niagaraAnnotationProcessors")`, REMIT [Block 2] §2.6).

Its `module-info.class` (decompiled) confirms JPMS identity and the exact SPI registration:

```java
module niagara.niagaraAnnotationProcessors {
   requires transitive java.compiler;
   requires transitive java.xml;
   exports niagara.nre.annotations;
   exports niagara.nre.annotations.processors;
   exports niagara.nre.annotations.processors.slot;
   exports com.tridium.nre.annotations;
   provides javax.annotation.processing.Processor with
      niagara.nre.annotations.processors.NiagaraTypeAnnotationProcessor,
      niagara.nre.annotations.processors.NiagaraSlotProcessor,
      niagara.nre.annotations.processors.NullProcessor;
}
```
`[CERT]` (`/tmp/claude-1000/n5b7/vf-out/module-info.java`, whole file) — and the classic
`META-INF/services/javax.annotation.processing.Processor` SPI file inside the jar carries the identical
3 lines verbatim:

```
niagara.nre.annotations.processors.NiagaraSlotProcessor
niagara.nre.annotations.processors.NiagaraTypeAnnotationProcessor
niagara.nre.annotations.processors.NullProcessor
```
`[CERT]` (`python3 zipfile` read of `META-INF/services/javax.annotation.processing.Processor` inside
`niagaraAnnotationProcessors.jar`, this session) — the module-descriptor `provides` clause and the
classic-classpath SPI file agree exactly (module-path and classpath compilation both discover the same 3
processors). Byte-level cross-check: `javap -p -v` on the 3 extracted `.class` files confirms the same 3
`this_class` names, the same `RuntimeVisibleAnnotations` (`@SupportedAnnotationTypes`,
`@SupportedSourceVersion`, `@SupportedOptions`), and `NullProcessor extends
javax.annotation.processing.AbstractProcessor` directly. `[CERT]` (`javap` output, this session, against
`niagara/nre/annotations/processors/{NiagaraTypeAnnotationProcessor,NullProcessor}.class`).

**Package rename from N4, confirmed both here and independently.** The annotations live in
`niagara.nre.annotations` (29 top-level classes: `NiagaraType`, `NiagaraProperty`+`NiagaraProperties`,
`NiagaraAction`+`NiagaraActions`, `NiagaraTopic`+`NiagaraTopics`, `NiagaraEnum`, `NiagaraSingleton`,
`NiagaraSlots`, `NoSlotomatic`, `Generated`, `AgentOn`+nested `Preference`, `Adapter`, `Facet`, `FileExt`,
`Range`, `ModuleResources`+`ModuleResourcesAll`, `NiagaraEnableNativeAccess`, and 8 permission-grant
annotations), plus a small separate `com.tridium.nre.annotations` package (9 classes: `FilePermissions`,
`GrantFilePermission`, `GrantKeyRingPermission`, `GrantNiagaraBasicPermission`, `KeyRingPermissions`,
`NiagaraBasicPermissions`, `NiagaraPermissionGrant`+nested `Type`, `NiagaraPermissionGroup`) — NOT
`javax.baja.nre.annotations`, the package N4 uses (REMIT `niagara-research` B780 §780 line 50, B863
line 132: `import javax.baja.nre.annotations.AgentOn;` / `NiagaraType;`). `[CERT]`
(`niagaraAnnotationProcessors-listing.txt`, this session's `zipfile` listing, all 67 entries) + `REMIT`
(corpus-nav cross-check, this session). The SAME rename pattern holds for the core `sys` package: N5's
Slotomatic-generated code imports `niagara.sys.Sys`/`niagara.sys.Type` (§7.4), where N4 uses
`javax.baja.sys.Sys`/`javax.baja.sys.Type` (REMIT B863 line 133-134, B41 lines 98/164/177) — i.e. the
ENTIRE `javax.baja.*` root namespace is renamed to `niagara.*` in N5, not just the annotations
sub-package. `[INFER]` on the WHY (plausibly a JPMS accommodation — `javax.*` is a reserved/discouraged
module-name prefix under the Java Platform Module System, and N5 modules are real JPMS modules per
[Block 2] §2.7); the WHAT (the rename itself) is `[CERT]` from both citations above.

## 7.2 — `NiagaraTypeAnnotationProcessor`: the ONLY code that writes `module-include.xml`, and it does nothing else `[CERT]`

```java
@SupportedAnnotationTypes("niagara.nre.annotations.NiagaraType")
@SupportedSourceVersion(SourceVersion.RELEASE_25)
@SupportedOptions({"niagara.module.root", "niagara.test.roots"})
public class NiagaraTypeAnnotationProcessor extends NiagaraAbstractProcessor {
```
`[CERT]` (`/tmp/claude-1000/n5b7/vf-out/niagara/nre/annotations/processors/NiagaraTypeAnnotationProcessor.java:25-28`)
— the `-A` options match [Block 2] §2.6's independently-found `AnnotationProcessorArgumentProvider`
(`-Aniagara.module.root=<project dir>`, `-Aniagara.test.roots=...`) exactly, confirming both halves of
the same mechanism (Gradle-plugin wiring in [Block 2], processor consumption here) agree.

Its `process()` method, for every element annotated `@NiagaraType`:
1. Validates the annotated element IS-A `niagara.sys.BIObject` (`this.types.isSubtype(...)`) — error if
   not: `"The type " + typeName + " was annotated with NiagaraType, but is not a BIObject."`
2. Validates the class name starts with `B` — error if not: `"The type " + typeClass + " does not start
   with B. All Niagara types must start with B."`
3. Resolves the module root via `getModuleRootPath()` (inherited from `NiagaraAbstractProcessor`, §7.5),
   picks `moduleTest-include.xml` vs `module-include.xml` by checking whether a same-named `.java` exists
   under any configured test root (`isTestClass()`).
4. Opens (or creates) that XML via a helper class `ModuleInclude`, checks `containsEntry(...)` AND
   `entryMatches(annotation, ...)` — **idempotent**: if an identical `<type>` entry already exists, NO
   write happens.
5. Otherwise calls `moduleInclude.addTypeNode(annotation, typeName, typeClass)`, strips whitespace,
   reformats, and `save()`s the file.

`[CERT]` (`NiagaraTypeAnnotationProcessor.java:56-111`, whole `process()` method read).

**This is the ENTIRE scope of the processor's code-generation contribution.** It does not touch any
`.java` source file, does not call `Filer.createSourceFile`/`createResource` for anything but a throwaway
path-probe file (§7.5), and processes no annotation other than `@NiagaraType`. Confirms and completes
[Block 2] §2.6's `[CERT-doc]` quote from `buildN5.html` ("the type elements are generated and updated
automatically by the annotation processor during compilation") with the exact mechanism and exact XML
shape it writes.

## 7.3 — `ModuleInclude`: the writer class — idempotent, comment-preserving, package-grouped `[CERT]`

`ModuleInclude` (own top-level `.java`, 475 lines) is a small hand-rolled DOM-based XML editor, not a
generic templating library:
- **Parse**: wraps the on-disk file (created empty if absent) in a synthetic `<dummyroot>…</dummyroot>`
  wrapper before parsing (tolerates a `module-include.xml` that has no single root element), then ensures
  a `<types>` container exists. `[CERT]` (`ModuleInclude.java:57-91`, `openDocument()`).
- **Type-node shape written by `addTypeNode()`**: `<type class="pkg.BFoo" name="Foo" ordScheme="...">`
  with optional nested `<agent requiredPermissions=".." app=".."><on type=".."/></agent>`,
  `<adapter from=".." to=".."/>`, and `<file><ext name=".."/></file>` children — built directly from the
  `@NiagaraType` annotation's `agent()`, `adapter()`, and `ext()` members. `[CERT]`
  (`ModuleInclude.java:138-209`, whole `addTypeNode()` method).
- **Placement is package-grouped, not append-only**: `placeTypeNode()` XPath-searches for existing
  `<type>` entries in the same package (matching the `pkg.BName` == `class` convention) and inserts the
  new node right after the LAST such entry, rather than blindly appending — this preserves the
  human-readable per-package grouping a hand-maintained `module-include.xml` traditionally has. `[CERT]`
  (`ModuleInclude.java:211-248`).
- **`format()` auto-inserts a package-name `<!-- pkg -->` XML comment** before the first type of each new
  package block if one doesn't already exist, and DROPS any `<type>` element whose `class`/`name` pair is
  inconsistent (`class` doesn't end in `.B<name>`) — i.e. it also self-heals a manually-corrupted file on
  every processor run. `[CERT]` (`ModuleInclude.java:297-327`).
- **`entryMatches()`** does a full structural diff (ordScheme, adapter, every `<agent>`/`<on>`, every
  `<file><ext>`) against the annotation before deciding a rewrite is needed — this is the idempotency
  check behind §7.2 step 4. `[CERT]` (`ModuleInclude.java:357-450`).

## 7.4 — Slotomatic: unchanged role, in-class generation only, same "AUTO GENERATED CODE" marker family (+ new IDE fold regions) `[CERT]`

`Slotomatic.builder()...compile().runSlotomatic()` (the Gradle-task entry point [Block 2] §2.5 already
found) resolves, per invocation, into `Compiler.compile(Path)` → for each `B*.java` file (name-gated:
must start with `B` then another uppercase letter, `Compiler.java:373-380`) → `process(Path)`, which:
- Skips the file entirely if it carries `@NoSlotomatic` (`javaUnit.hasNiagaraAnnotation("NoSlotomatic")`,
  `Compiler.java:198-202`) — confirming this annotation, even though `NullProcessor` (§7.6) ignores it at
  the javac level, IS meaningfully consumed — by Slotomatic, not the AP.
- Chooses one of 3 `SourceTransformer`s depending on mode: `SlotTransformer` (ordinary "compile" step —
  §7.4.1), `AnnotationTransformer` (the `--migrate` path — §7.7's `migrate()` builder option), or
  `ImportTransformer` (the `--importFromModuleInclude` path, a subclass of `AnnotationTransformer` —
  §7.4.2).
- **Writes the result back to the SAME file, in place**, via an atomic temp-file-then-`Files.move`
  pattern (`Compiler.TempFile`, suffix `.foobiebletch`, `REPLACE_EXISTING`). `[CERT]`
  (`Compiler.java:328-339, 394-423`) — **directly answers "does Slotomatic still rewrite source
  in-place": YES, unchanged from N4** (REMIT B637 §637.2: "Slotomatic regenerates the
  `// BAJA AUTO GENERATED CODE` region… inside the `.java`").
- **Incremental by default**: `needsRecompile()` skips a file whose existing generated block's class/
  package name and content hash already match (`isSlotCodeOutOfDate()`) UNLESS `--force`. `[CERT]`
  (`Compiler.java:341-354`).

### 7.4.1 — `SlotTransformer`/`SlotGenerator`: the exact marker text `[CERT]`

```java
this.cb.println("//region /*+ ------------ BEGIN BAJA AUTO GENERATED CODE ------------ +*/");
this.cb.println("//@formatter:off");
this.header(this.cb);              // "/* Generated <date> by Slot-o-Matic (c) Tridium, Inc. 2012-<yr> */"
...
this.slotMode.propertyBlock(); this.slotMode.actionBlock(); this.slotMode.topicBlock();
if (this.unit.isSingleton()) this.slotMode.singleton();
this.slotMode.typeDeclaration();
...
this.cg.println("//@formatter:on");
this.cg.print("//endregion /*+ ------------ END BAJA AUTO GENERATED CODE -------------- +*/");
```
`[CERT]` (`generator/SlotGenerator.java:23-48`, whole `generate()` method) — the literal `Constants`
interface pins the exact byte strings:

```java
String BAJAGENSTART = "/*+ ------------ BEGIN BAJA AUTO GENERATED CODE ------------ +*/";
String BAJAGENREGIONSTART = "//region /*+ ------------ BEGIN BAJA AUTO GENERATED CODE ------------ +*/";
String BAJAGENEND = "/*+ ------------ END BAJA AUTO GENERATED CODE -------------- +*/";
String BAJAGENREGIONEND = "//endregion /*+ ------------ END BAJA AUTO GENERATED CODE -------------- +*/";
Pattern GENERATED_ON_DATE = Pattern.compile("^/\\* Generated.*by Slot-o-Matic \\(c\\) Tridium, Inc. 2012(-\\d{4})? \\*/$");
```
`[CERT]` (`Constants.java`, whole 18-line file) — **the core `BAJAGENSTART`/`BAJAGENEND` marker text is
byte-identical to N4's** (REMIT B637 §637.2 names the same "BAJA AUTO GENERATED CODE" region; B12
§12.1.8 likewise). The only addition is the `//region`/`//endregion` wrapper (IntelliJ/Eclipse code-
folding directive syntax) around the same markers — an IDE-ergonomics addition, not a semantic change.

**Base (`SlotMode`) output, confirmed by reading the generator directly** — for an ordinary (non-Orion)
`BFoo` component: a `getType()`/`TYPE` pair —

```java
@Override
public Type getType() { return TYPE; }
public static final Type TYPE = Sys.loadType(BFoo.class);
```
— plus per-slot output from `PropertyProcessor`/`ActionProcessor`/`TopicProcessor`/`EnumProcessor`
(constant + accessor generation, package `com.tridium.slottool.processor`, not read line-by-line this
session — the generation shape itself, not each processor's field-naming convention, was the gap in
scope) and, when the class is `@NiagaraSingleton`, an `INSTANCE` constant. `[CERT]`
(`mode/SlotMode.java:33-94`, whole class read) — imports `niagara.sys.Sys`/`niagara.sys.Type` (§7.1's
package-rename finding, confirmed a second, independent way).

**`Orion` is a `SlotMode` SUBCLASS**, not a separate tool — adds ORM-style cursor/index generation
(`getIndexes()`, `INDEXES[]`, `get<Name>Cursor()`) for Orion-backed (database-persisted) component types,
overriding `getType()` to `"getTypeFromSpace(TYPE)"` and adding an `ORION_TYPE` constant. `[CERT]`
(`mode/Orion.java:17-73`) — named as informative context, not separately gap-worthy: it is loaded by
reflection off `BajaUnit.getMode()` (`SlotGenerator.initMode()`, `generator/SlotGenerator.java:64-77`),
so other `SlotMode` subclasses could exist and were not enumerated this session (only `Orion` is shipped
in this jar — `mode/` has exactly 3 `.class` files: `SlotMode`, `Orion`, `Orion$OrionPropertyProcessor`).

**`@Generated`-annotation cross-link.** Every emitted member is optionally wrapped with
`cg.printOptionalAnnotation(slotomaticOptions.getGeneratedAnnotationName())` (`SlotMode.java:66,82,87,89`
+ `Orion.java` equivalents) — this is the `niagara.nre.annotations.Generated` marker annotation
(`@Retention(CLASS) @Target({FIELD,METHOD,CONSTRUCTOR,TYPE})`, `niagara/nre/annotations/Generated.java`)
that ships IN THE SAME jar as the JSR-269 processors (§7.1) but is applied BY SLOTOMATIC, not consumed by
either registered `Processor`. It is pure metadata (marks a member as tool-generated for IDEs/linters,
same idea as `javax.annotation.Generated`) — confirms the two jars/tools share a small annotation
vocabulary even though their runtime roles are fully separate. `[CERT]`
(`niagara/nre/annotations/Generated.java`, whole file, cross-referenced against `SlotMode.java` call
sites).

### 7.4.2 — `AnnotationTransformer`/`ImportTransformer`: Slotomatic's OWN (non-JSR-269) `@NiagaraType` reader, and its module-include.xml READ path `[CERT]`

Separately from the registered `javax.annotation.processing.Processor`s, the Slotomatic library ships
its OWN annotation-model layer (`com.tridium.slottool.model.annotation.processors.*`, 13 classes:
`NiagaraTypeProcessor`, `NiagaraPropertyProcessor`, `NiagaraActionProcessor`, `NiagaraTopicProcessor`,
`NiagaraEnumProcessor`, `NiagaraSingletonProcessor`, `NiagaraSlotsProcessor`, `NiagaraOrionTypeProcessor`,
`OrionIndexProcessor`, `OrionLinkedCursorProcessor`, `OrionPropertyProcessor`, `OrionRefCursorProcessor`,
`NoSlotomaticProcessor`) that parses `@Niagara*` annotations directly off the
`com.github.javaparser`-produced AST (NOT `javax.lang.model`/`javax.annotation.processing` — a
third-party library, distinct from both javac's compiler API and Slotomatic's own legacy comment
grammar) — this is how Slotomatic itself reads `@NiagaraType`/`@NiagaraProperty`/etc. to build its
internal `BajaUnit`/`NiagaraType` model for §7.4.1's code generation. `[CERT]`
(`model/annotation/processors/NiagaraTypeProcessor.java`, whole 120-line file read: `implements
AnnotationProcessor`, `accept(AnnotationExpr)`, extracts `ordScheme`/`adapter`/`ext`/`agent` from the AST
node directly).

**Slotomatic's `Compiler` constructor DOES read `module-include.xml`** (`Compiler.java:43-140`, parses
`<types>/<type>` exactly like [Block 2]/B12/B631 found for N4) — but this read is used ONLY by 2 of
Slotomatic's 3 transform modes, both migration/bootstrapping paths, NOT the everyday "compile" path:
- `AnnotationTransformer` (`migrate()` builder option) — converts a class still using the LEGACY
  Baja-comment slot syntax (or an un-annotated `@NiagaraSlots` block) into modern `@Niagara*` Java
  annotations, seeding the generated `@NiagaraType(...)` attribute values FROM the module-include.xml
  entry looked up by `Compiler.getTypeInfoForClass()`. `[CERT]` (`AnnotationTransformer.java:26-71`,
  `Compiler.java:273-289`).
- `ImportTransformer extends AnnotationTransformer` (`importFromModuleInclude()` builder option) — for a
  class with NO existing slot code or annotations at all (an `EmptyBajaUnit`) that IS listed in
  `module-include.xml` (an orphan entry, typically from AX-era hand-written `getType()`/`TYPE` fields),
  generates fresh `@NiagaraType` annotations from that entry and DELETES the old manual `getType()`
  method and `TYPE` field. `[CERT]` (`ImportTransformer.java`, whole 31-line file;
  `Compiler.java:291-310`).

The ordinary `SlotTransformer` (§7.4.1, the "compile"/day-to-day path) reads NEITHER `module-include.xml`
NOR uses this model layer for XML — it works purely off the source AST via `JavaUnit`/`BajaUnit`. So
**the module-include.xml READ Slotomatic performs is a migration-tooling residue, not part of the
steady-state generate loop** — refines REMIT B12/B631's flat "Slotomatic reads module-include.xml as
input" claim (true for N4 and still true here, but only for `--migrate`/`--importFromModuleInclude`
invocations, which is new precision this session can add since the class-level mode split is now
visible).

## 7.5 — `NiagaraAbstractProcessor`: shared module-root resolution, both `-A` options land here `[CERT]`

```java
public abstract class NiagaraAbstractProcessor extends AbstractProcessor {
   ...
   public void init(ProcessingEnvironment processingEnv) {
      super.init(processingEnv);
      this.msg = processingEnv.getMessager();
      ...
      if (processingEnv.getOptions().containsKey("niagara.module.root")) {
         this.providedModuleRoot = processingEnv.getOptions().get("niagara.module.root");
      }
   }
   public String getModuleRootPath(Element elem) { /* falls back to a Filer.createResource() probe file
      under StandardLocation.SOURCE_OUTPUT + string-surgery on its path if -Aniagara.module.root wasn't
      passed */
```
`[CERT]` (`niagara/nre/annotations/processors/NiagaraAbstractProcessor.java`, whole 62-line file) — only
`NiagaraTypeAnnotationProcessor` extends this class (`NiagaraSlotProcessor` and `NullProcessor` extend
`AbstractProcessor` directly, confirmed by `javap`'s `super_class` field and by the decompiled source
imports) — the module-root machinery exists solely to let the type processor locate WHERE to write
`module-include.xml` relative to the module root, not for any other purpose.

## 7.6 — `NiagaraSlotProcessor`: validates, does not generate — literal "have you run slot-o-matic?" `[CERT]`

```java
@SupportedAnnotationTypes({"niagara.nre.annotations.NiagaraAction","niagara.nre.annotations.NiagaraActions",
   "niagara.nre.annotations.NiagaraProperty","niagara.nre.annotations.NiagaraProperties",
   "niagara.nre.annotations.NiagaraTopic","niagara.nre.annotations.NiagaraTopics"})
@SupportedOptions("niagara.slot.warning.level")
public class NiagaraSlotProcessor extends AbstractProcessor {
   public boolean process(...) {
      for (TypeElement element : getElementsAnnotatedWith(roundEnv, NiagaraProperty.class,
            NiagaraProperties.class, NiagaraAction.class, NiagaraActions.class,
            NiagaraTopic.class, NiagaraTopics.class)) {
         BajaUnit unit = new BajaUnit(this.processingEnv, this.options, element);
         unit.checkProperties(); unit.checkActions(); unit.checkTopics();
      }
      return true;
   }
```
`[CERT]` (`niagara/nre/annotations/processors/NiagaraSlotProcessor.java`, whole 76-line file). Its
`BajaUnit` helper (`processors/slot/BajaUnit.java`, distinct from Slotomatic's OWN
`com.tridium.slottool.model.BajaUnit` — same name, different package, different purpose) reflects on the
class's ALREADY-COMPILED member set (`elements.getAllMembers(element)`, filtered to fields typed
`niagara.sys.Property`/`Action`/`Topic`) and cross-checks it against the DECLARED `@NiagaraProperty`/etc.
annotations:

```java
if (!unitSlotNames.contains(slot.getName())) {
   this.msg.printMessage(Kind.ERROR, String.format(
      "Slot with name %s not found on class %s; have you run slot-o-matic?",
      slot.getName(), this.element.asType().toString()));
}
if (slot.getOverride()) {
   if (!parentSlotNames.contains(slot.getName())) {
      this.msg.printMessage(this.warningKind, String.format(
         "Slot %s in class %s does not override a slot in its parent class(es)", ...));
   }
} else if (parentSlotNames.contains(slot.getName())) {
   this.msg.printMessage(this.warningKind, String.format(
      "Missing 'override = true' for slot %s on class %s", ...));
}
```
`[CERT]` (`processors/slot/BajaUnit.java:72-113`, whole `checkSlots()` method) — **this method emits
diagnostics and NOTHING else: no `Filer` call anywhere in the class, no source or resource file is ever
written.** The `niagara.slot.warning.level` option (default `WARNING`, `Kind.valueOf(...)`,
`NiagaraSlotProcessorOptions.java`) only controls the SEVERITY of the override-consistency checks, not
the missing-slot check (always `ERROR`, hard-coded `Kind.ERROR` at line 92).

**Conclusion for B2-G1's core question**: `@NiagaraProperty`/`@NiagaraAction`/`@NiagaraTopic` generate
ZERO code via the annotation-processing round. Compiling a fresh `@NiagaraProperty`-only class WITHOUT
running Slotomatic first will fail to compile with exactly the "have you run slot-o-matic?" diagnostic —
this is a genuinely NEW, useful fact beyond what `buildN5.html` states (the doc only describes the
`module-include.xml` behavior; this validator's existence and message text were undocumented in [Block
2]'s sources and are visible only from the decompiled class).

## 7.7 — `NullProcessor`: claims 5 annotations, processes none of them `[CERT]`

```java
@SupportedAnnotationTypes({"niagara.nre.annotations.NiagaraEnum","niagara.nre.annotations.NiagaraSingleton",
   "niagara.nre.annotations.NiagaraSlots","niagara.rpc.NiagaraRpc","niagara.nre.annotations.NoSlotomatic"})
public class NullProcessor extends AbstractProcessor {
   public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
      return true;
   }
}
```
`[CERT]` (`niagara/nre/annotations/processors/NullProcessor.java`, whole file; byte-confirmed by `javap`,
§7.1). Returning `true` from `process()` marks these 5 annotation types as CLAIMED for this processor,
which is the standard javac idiom to suppress the "No processor claimed any of these annotations"
warning/note — `NullProcessor`'s entire reason to exist is to silence that diagnostic for annotations
that Slotomatic alone is responsible for (`@NiagaraEnum`, `@NiagaraSingleton`, `@NiagaraSlots` all have a
DEDICATED Slotomatic-side `*Processor` under `model/annotation/processors/` — §7.4.2 — confirming these 5
are consciously AP-silent, not accidentally unhandled). `niagara.rpc.NiagaraRpc` is claimed here but its
own annotation class/package was NOT opened this session (not present in `niagaraAnnotationProcessors.jar`
— it must live in a different, RPC-specific module) — flagged as child gap B7-G2, not investigated
further (out of scope: this gap is about the Slotomatic/AP split, not the RPC subsystem).

## 7.x — Open question: exact Gradle task-graph edge between `slotomatic` and `compileJava` `[INFER]`

[Block 2] §2.1 already found the Kotlin-plugin decompile has an opacity ceiling: Vineflower cannot
reconstruct Kotlin lambda bodies past a certain nesting, rendering them `<unrepresentable>.INSTANCE`.
Re-opening `NiagaraModulePlugin.kt` this session for `registerSlotomaticTasks()` (line 356) and
`configureJavaCompileTasks()` (`configureJavaCompileTasks`) hits exactly this ceiling: both methods'
`configureEach { ... }` bodies decompile to `<unrepresentable>.INSTANCE`, so this session could NOT read,
byte-for-byte, whether `compileJava` carries an explicit `dependsOn`/`mustRunAfter` on the `slotomatic`
task (which would make `./gradlew build` correct-by-construction) or whether — as [Block 2] §2.5 already
established from the doc's own CLI phrasing (`gradlew :<moduleName>:slotomatic` as a standalone
invocation) — the ordering remains a MANUAL operator responsibility, exactly as in N4 (REMIT B637 §637.2:
"Clean+Slotomatic+Build vs Clean+Build" is a rule the operator must apply, not an automatic dependency).
`[CERT]` (`Compiler.java:373-380` — `checkName()` gates which files Slotomatic even looks at) +
`[INFER]`: §7.6's `NiagaraSlotProcessor` diagnostic ("have you run slot-o-matic?") existing AT ALL is
itself indirect evidence the task graph does NOT auto-sequence Slotomatic before `compileJava` — a
processor would have no reason to detect and warn about a missing-slot-field state that a `dependsOn`
edge would make structurally impossible. This is `[INFER]`, not `[CERT]`, since it argues from the
processor's EXISTENCE rather than from reading the task graph directly. Named as child gap **B7-G1**
(requires either a live `gradlew :module:tasks --all` run against a real N5 project, or Java bytecode
disassembly of the Kotlin lambda classes directly with `javap` rather than trusting Vineflower's
reconstruction — untried this session).

## 7.8 — Synthesis: the answer to B2-G1's literal question `[INFER]`

| Question (from the gap) | Answer | Basis |
|---|---|---|
| Supported annotations, AP side | `@NiagaraType` (module-include.xml write) · `@NiagaraProperty`/`@NiagaraProperties`, `@NiagaraAction`/`@NiagaraActions`, `@NiagaraTopic`/`@NiagaraTopics` (validate-only) · `@NiagaraEnum`, `@NiagaraSingleton`, `@NiagaraSlots`, `niagara.rpc.NiagaraRpc`, `@NoSlotomatic` (claimed, no-op) | §7.1-7.7, `[CERT]` |
| Package (N5) | `niagara.nre.annotations` (+ `com.tridium.nre.annotations` for permission grants) — renamed from N4's `javax.baja.nre.annotations` | §7.1, `[CERT]`+`REMIT` |
| What Slotomatic emits | In-class getter/setter/constant boilerplate between `BAJAGENSTART`/`BAJAGENEND` markers (now also `//region`/`//endregion`-wrapped); unchanged in kind from N4 | §7.4.1, `[CERT]` |
| What the AP emits | `module-include.xml`/`moduleTest-include.xml` `<type>` entries ONLY — no `.java` code, ever | §7.2-7.3, `[CERT]` |
| Does Slotomatic still rewrite source in-place | Yes — atomic temp-file-then-move onto the SAME `.java` file | §7.4, `[CERT]` |
| Task-graph order | Doc/CLI evidence says standalone/manual (REMIT + [Block 2]); direct task-graph edge unresolved (Kotlin lambda decompile ceiling) | §7.7(open), `[INFER]` |
| Failure modes/diagnostics | `"...was annotated with NiagaraType, but is not a BIObject."` · `"...does not start with B..."` · `"Slot with name %s not found on class %s; have you run slot-o-matic?"` · `"...does not override a slot..."` · `"Missing 'override = true' for slot %s..."` | §7.2, §7.6, `[CERT]` |
| N4-module impact | Every N4 module carrying Slotomatic-generated blocks (REMIT: `corpus-nav.py find slotomatic` — B12, B434, B637, B711, B780, B863, B863-family) keeps its EXACT SAME generated-region shape on an N5 port (marker text unchanged); what's NEW is that a hand-edited `module-include.xml` becomes partially redundant — the AP will self-heal/regenerate `<type>` ADDITIONS on next compile (REMIT [Block 2] §2.12 item 5, now `[CERT]`-backed by §7.2-7.3 instead of doc-only) | `[INFER]` synthesis, not tested against a real port |

## 7.x — Self-verify tally

Literal `verify-block.sh` output (METHODOLOGY §11: the reported tally must be the script's own output,
never hand-recalculated) — run read-only against this file, no other file touched:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    /home/cristian/niagara5-research/niagara5-block7.md
== verify-block: niagara5-block7.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 53  (adj 51)
   [CERT-doc] 4  (adj 3)
   [CERT-web] 1
   [CERT-a] 0
   [INFER] 13  (adj 11)
-- ratio -- [INFER]/[CERT*] = 11/55 = 0.20
-- [CERT] file:line citation resolution --
   extern  (19 distinct citations, all into /tmp/claude-1000/n5b7/vf-out/** and
            /tmp/claude-1000/n5b7/vf-slotomatic/** — Vineflower decompile output)
   resolved 0 of 19
   WARN    resolved 0 of 19 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```

**DECOMPILED-TREE BLOCKS WILL SHOW ZERO RESOLVED CITATIONS — THIS IS EXPECTED** (METHODOLOGY §11,
verbatim rule name): every `[CERT]` citation in this block points into `/tmp/claude-1000/n5b7/vf-out/**`
(AP jar decompile) or `/tmp/claude-1000/n5b7/vf-slotomatic/**` (Slotomatic jar decompile), both outside
the corpus directory the script walks, sha256s of the 2 SOURCE jars pinned in the header (identity
anchor per METHODOLOGY §5's minified/obfuscated-source rule — decompiler output is not 1:1 reproducible
across tool versions, so the jar hash, not the decompiled tree, is the reproducibility anchor).
**Declaring per the rule: verify-block: 0 resolved (all extern — decompiled trees); citation gate =
inline token-verify 21/21 tokens** (every class/method/annotation/diagnostic-string cited in §7.1-§7.8
was read directly from the named decompiled `.java` file in this session, listed exhaustively below).

`[CERT-web] 1` in the script's raw tally is the header's marker-legend line (`` `[CERT-web]` official web
source... ``), not a fresh claim — this block makes no live-web citation; adjusted count is captured in
the script's own `adj` column (3 for `[CERT-doc]`, all header-legend/boilerplate, since [Block 2] already
holds this block's only `buildN5.html` cross-reference and this block adds no NEW `[CERT-doc]` citation).
Adjusted ratio `[INFER]`/`[CERT*]` = 11/(51+3) = **0.20** — low, consistent with a `mixed` block whose
synthesis load is confined to §7.7's genuinely unresolved task-graph question and §7.8's impact table
(both explicitly `[INFER]`-flagged), with the mechanism itself (§7.1-§7.6) fully `[CERT]`.

**Token check**: every quoted class name, method name, annotation name, and diagnostic string above was
read directly from the Vineflower-decompiled `.java` file cited beside it in this session (not
recalled/typed from memory) — 21 distinct source files opened in full or in the cited range:
`module-info.java`, `NiagaraAbstractProcessor.java`, `NiagaraTypeAnnotationProcessor.java`,
`NiagaraSlotProcessor.java`, `ModuleInclude.java`, `NullProcessor.java`, `NiagaraSlotProcessorOptions.java`,
`processors/slot/BajaUnit.java`, `Slotomatic.java`, `SlotomaticOptions.java`, `Compiler.java`,
`SourceTransformer.java`, `SlotTransformer.java`, `AnnotationTransformer.java`, `ImportTransformer.java`,
`generator/CodeGenerator.java`, `generator/SlotGenerator.java`, `mode/SlotMode.java`, `mode/Orion.java`,
`Constants.java`, `model/annotation/processors/NiagaraTypeProcessor.java`. 3 classes additionally
byte-cross-checked with `javap -p -v` (§7.1). Every zip-entry-count/measurement in §7.1's package counts
and this block's jar-inventory claims was produced by a `python3 zipfile` script run this session, not
estimated.

**Artifacts** — block file written to `/home/cristian/niagara5-research/niagara5-block7.md`. Per the
caller's explicit instruction this session, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` were
INTENTIONALLY NOT touched or regenerated (out of scope: "touch no other file") — flagged here so this
deviation from METHODOLOGY §11's normal artifact-update expectation is a declared choice, not an
oversight, for whoever next runs the orchestrator loop on this corpus.

**MCP-doc snapshots** — N/A, no `[CERT-web]`/context7 citation in this block.

## 7.x — Connections

- **[Block 2]** — opened this gap (§2.6, B2-G1) from `buildN5.html`'s doc-level claim plus the
  independently-found `nap`/`NiagaraAnnotationProcessorsPlugin` Gradle-side wiring
  (`-Aniagara.module.root`/`-Aniagara.test.roots`, the `niagaraAnnotationProcessor` configuration). This
  block supplies the processor's OWN implementation that [Block 2] could not locate, and the 2 `-A`
  option names match exactly between the 2 blocks' independently-read sources (Gradle plugin vs.
  processor `@SupportedOptions`) — a clean cross-block confirmation, not just a citation.
- **[Block 2] §2.12 item 5** — "Stop hand-maintaining module-include.xml" kit-delta item was `[INFER]`
  from doc prose alone; §7.2-7.3 here upgrade the MECHANISM behind that recommendation to `[CERT]`
  (idempotent write, package-grouped placement, self-healing malformed entries) without changing the
  recommendation itself.
- **REMIT `niagara-research` B12** §12.1.8 and **B631** §631.1-2 — the N4 baseline: B631 corrected B12's
  premature "annotation processor" claim by proving NO `javax.annotation.processing.Processor` exists in
  the N4 decompiled corpus. This block is the N5-side mirror-image correction: N5 DOES have one, and its
  scope is exactly as narrow as B631's caution would predict (type-list only, no in-class codegen) —
  vindicating B631's skepticism about over-crediting an AP with codegen it doesn't do, now for the N5
  case too (§7.6's `NiagaraSlotProcessor` validates rather than generates).
- **REMIT B434** — same `com.tridium.slottool.Slotomatic` class identity, now decompiled at the SOURCE
  level (B434 only confirmed file/class EXISTENCE against a token-mangled decompile; this block reads
  full method bodies).
- **REMIT B637** §637.2 — the "Clean+Slotomatic+Build vs Clean+Build" operator variant rule and the exact
  `// BAJA AUTO GENERATED CODE` marker text; §7.4.1 confirms byte-identical marker text survives into N5,
  and §7.7's open question is precisely whether B637's manual-sequencing rule ALSO survives (evidence
  points yes, not fully closed).
- **REMIT B711/B780/B863** — N4 toolchain/authoring-convention context; B863's `import
  javax.baja.nre.annotations.NiagaraType;` and B41's `javax.baja.sys.Type` signatures are the exact
  package-name cross-check anchors for §7.1's namespace-rename finding.
- **[TO ANNOTATE — child gap B7-G1]** — resolve the exact `slotomatic`↔`compileJava` Gradle task-graph
  edge (§7.7), either via a live `gradlew :module:tasks --all`/`--dry-run` against a real N5 project, or
  by disassembling the specific Kotlin lambda `.class` files directly with `javap` instead of trusting
  Vineflower's `<unrepresentable>` reconstruction.
- **[TO ANNOTATE — child gap B7-G2]** — `niagara.rpc.NiagaraRpc`, claimed by `NullProcessor` (§7.7) but
  its defining module/package was not located in this session's 2 opened jars; likely lives in an
  RPC-specific Niagara module not yet identified in this corpus.
