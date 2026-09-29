# Block 121 — The four Kotlin-compiled Tridium jars: 696 classes all decode from `kotlin.Metadata`, the corpus trees for them are already Vineflower Kotlin-plugin output (not a Java decompile), 73 sites are unreadable in them, and 1 of 42 audited corpus claims is contradicted

> Research task for gap **B117-G2** ([Block 117] §117.4 and child-gap list: "Audit every corpus claim read from a Java decompile of the
> Kotlin-compiled Tridium jars (`n-plugin` 650/724 classes, `n-conv-plugin`, `settings`, `utils`) and re-check each against `kotlin.Metadata`
> or a Kotlin-aware decompile"). Answers: (1) which jars are Kotlin-compiled, re-derived from class files; (2) which Kotlin constructs a
> Java-shaped view loses or distorts and how often each occurs in these jars; (3) what a Kotlin-aware recovery achieves — decoding
> `kotlin.Metadata` with `kotlin-metadata-jvm`, and running Vineflower's Kotlin plugin; (4) a SAFE / SUSPECT / CONTRADICTED audit of the
> corpus claims that cite these jars. Does **not** cover: recompiling the recovered `.kt` (B121-G2); behaviour of the Gradle plugins at run
> time (no `gradlew` run); claims about third-party Kotlin jars beyond the two blocks that cite them (B121-G4); the 10 out-of-pipeline
> Tridium jars other than these four (B117-G1 asks for their durable decompile; §121.2 records that the `_etc-m2` trees now exist).
>
> Type: evidence. **Subject version:** Niagara N5 5.0.0.28 (Beta); subject jars `etc/m2/repository/com/tridium/tools/{n-plugin-5.0.54.9.2,
> n-conv-plugin-5.0.54.9.2,settings-5.0.9.8.14,utils-5.0.7.8.14}.jar` (Kotlin metadata version 2.2.0, class-file major 69), byte-exact
> class files under `organized/_etc-m2/<jar>/extracted/`. Markers: `[CERT-hw]` = executed this session, script and output under `evidence/b121/`;
> `[CERT]` = read at a `file:line` of a durable tree; `[INFER]` = derived.
> **Repo hygiene:** the repository is public; no decompiled or reconstructed Tridium source is committed. The 696 recovered Kotlin
> declaration listings, the fresh Vineflower trees and the `kotlin-metadata-jvm` jar live in the gitignored `organized/_evidence/b121/`,
> identified by sha256 in `evidence/b121/kotlin-signatures.sha256`, `evidence/b121/trees.sha256` and `evidence/b121/README.md`; this block quotes
> at most a few lines.
>
> **ALREADY-COVERED check (literal queries, 2026-09-29):** `rg -il "kotlin" niagara5-block*.md` → [Block 2] (title), [Block 7], [Block 25], [Block 36],
> [Block 39], [Block 55], [Block 74], [Block 89], [Block 97], [Block 106], [Block 108], [Block 117]; none decodes `kotlin.Metadata` or grades a
> Kotlin decompile. `rg -il "kotlin.Metadata|kotlin-metadata|kt-enable" niagara5-block*.md` → [Block 117] only (the `Lkotlin/Metadata;` byte scan).
> `rg -il "n-plugin|n-conv-plugin" niagara5-block*.md` → B2, B7, B36, B39, B51, B74, B79, B89, B97, B108, B117 (as [Block 117] listed).
> `python3 tools/check-coverage.py kotlin n-plugin` → prior coverage of the plugin content, none of the decompile fidelity.

---

## 121.1 — B117-G2 step 1 CLOSED: Kotlin is confined to 4 Tridium jars (696 classes) plus 6 third-party jars; none of the 247 module jars carries its own Kotlin class `[CERT-hw]`

`evidence/b121/kotlin_census.py` walks every jar of the install — the 247 config-home module jars, `bin/ext`, `etc/m2`, `lib`, `javadoc` — and follows nested jars recursively
(**475 jar entries**). A class counts as Kotlin-compiled only if its class-level `RuntimeVisibleAnnotations` attribute holds `Lkotlin/Metadata;`, parsed from the class file
(not a byte scan). **10 jars** hold 3,368 Kotlin classes:

| Jar | Tridium? | Classes | Kotlin classes | Kinds (k=1 class / 2 file facade / 3 synthetic) | Metadata version |
|---|---|---|---|---|---|
| `n-plugin-5.0.54.9.2` | yes | 724 | **650** | 306 / 28 / 316 | 2.2.0 |
| `n-conv-plugin-5.0.54.9.2` | yes | 14 | **14** | 4 / 0 / 10 | 2.2.0 |
| `settings-5.0.9.8.14` | yes | 20 | **20** | 14 / 3 / 3 | 2.2.0 |
| `utils-5.0.7.8.14` | yes | 12 | **12** | 4 / 4 / 4 | 2.2.0 |
| `kotlin-stdlib-2.3.0` (nested in `devkit.jar!LIB-INF`) | no | 977 | 934 | | 2.3.0 |
| `bin/ext/kotlin-stdlib-2.4.10` | no | 989 | 946 | | 2.4.0 |
| `bin/ext/okhttp-jvm-5.5.0` | no | 383 | 383 | | 2.1.0 |
| `bin/ext/okio-jvm-3.18.1` | no | 121 | 121 | | 2.1.0 |
| `jackson-module-kotlin-2.22.0` (`etc/m2`) | no | 150 | 147 | | 1.9.0 |
| `kotlin-reflect-2.1.21` (`etc/m2`) | no | 1,963 | 141 | | 2.1.0 |

The four Tridium jars hold **696** Kotlin classes (694 under `com/tridium/`, 2 under `extensions/`); the other 6 jars hold 2,672. This reproduces [Block 117] §117.4 exactly (650/724, 14/14, 20/20,
12/12) and confirms its statement that no module jar carries Kotlin of its own: the only Kotlin in the 247 module jars is `devkit.jar`'s nested `kotlin-stdlib-2.3.0.jar`. `[CERT-hw]`
(`evidence/b121/kotlin_census.py`, `evidence/b121/kotlin-census-all.tsv`). 74 of `n-plugin`'s 724 classes are plain Java (62 top-level `.java` files in the trees, §121.2).

## 121.2 — The corpus trees for these four jars are NOT a Java decompile: they are Vineflower 1.12.0 Kotlin-plugin output (329 `.kt` + 62 `.java` files) `[CERT-hw]`

[Block 117] §117.4 and B117-G2 speak of "a Java decompile of Kotlin bytecode". The durable trees `organized/_etc-m2/<jar>/vineflower2/` (created after B117) say otherwise: `n-plugin` has **302 `.kt`** and 62 `.java` files, `n-conv-plugin` 4 `.kt`,
`settings` 15 `.kt`, `utils` 8 `.kt`. Vineflower 1.12.0 embeds `META-INF/plugins/vineflower-kotlin-0.1.0.jar` and `--kt-enable` defaults to `true` ("Decompile Kotlin classes as Kotlin instead of Java"; `--list-plugins` prints
`Kotlin (loaded from JarPluginSource) - Detects and decompiles Kotlin class files`). `tools/n5-decompile.sh:82-84,2328` and each `recon.json` (`vineflower_kotlin_plugin_used: true`) record that the plugin applies but only as an assumption
(`kotlin > 0`), never that it produced `.kt`. This session re-ran Vineflower with and without the plugin (`evidence/b121/run_vineflower.sh`; `--kt-enable=true` vs `--kt-enable=false`, same library context `-e`, 4 jars, 8 runs, 4–15 s each) and
compared both with the corpus tree (`evidence/b121/compare_trees.py`, `evidence/b121/tree-compare.tsv`):

| Metric (4 jars summed) | fresh `--kt-enable=true` | fresh `--kt-enable=false` (Java) | corpus `vineflower2/` |
|---|---|---|---|
| files (`.kt` / `.java`) | 391 (329 / 62) | 391 (0 / 391) | 391 (329 / 62) |
| lines | 25,446 | 43,608 | 25,418 |
| methods printed as "Couldn't be decompiled" | **67** | 0 | 67 |
| whole classes "Unable to decompile class" | **6** | 0 | 6 |
| `Intrinsics.` lines (null-check intrinsics) | 236 | 2,067 | 236 |
| `@NotNull` / `@Nullable` lines | 46 | 2,225 | 46 |
| `$this$` names | 456 | 3,157 | 456 |
| `$i$f$` names / `$i$a$` names (inline-expansion markers) | 8 / 0 | 424 / 390 | 8 / 0 |
| synthetic `varN` names | 3,075 | 6,541 | 3,070 |
| `<unrepresentable>` placeholders | 41 | 123 | 41 |
| `fun` signatures with a default value (`= …`) | 41 | 0 | 41 |
| `open fun <ClassName>(` pseudo-functions (constructors) | 75 | 0 | 75 |

The fresh `.kt` run is byte-identical to the corpus tree for **374 of 391 files** (`n-plugin` 347/364, the other three 27/27); the 17 differing `n-plugin` files come from the pipeline's extra flags (`decompile_assert`,
`decompiler_comments`, `dump_bytecode_on_error`), which `run_vineflower.sh` omits. So the corpus's `vineflower2/` and `vineflower-cons/` trees for these jars are the Kotlin-plugin view, and every earlier `.kt` citation
([Block 2], [Block 7], [Block 36], [Block 39], [Block 51], [Block 74], [Block 89]) was read from that view or an earlier run of it.

The trade: the plugin removes ~89 % of the null-check noise (236 vs 2,067 `Intrinsics.` lines) and restores `fun`, `val`, `companion object`, `@JvmOverloads`, default values and extension receivers, at the price of 67 unreadable method bodies and 6 unreadable classes;
Java mode reads everything but keeps the intrinsics and the `$this$` / `$i$` names and mis-binds three inline markers: Java mode prints `String $i$f$withType = "slotomatic"` (`organized/_evidence/b121/vf-java/n-plugin/com/tridium/gradle/plugins/module/NiagaraModulePlugin.java:624`;
the marker slot is reused by a `String`, so the LocalVariableTable name is wrong for that value; `compare_trees.py` finds 3 such bindings). `[CERT-hw]`

The `_etc-m2` trees now exist for all 10 out-of-pipeline Tridium jars (`organized/_etc-m2/*` + `organized/_lib/*`, each with `recon.json`), which is what B117-G1 asked for; the orchestrator can flip that row (§121.11).

## 121.3 — Where the Kotlin plugin fails: 67 method walls and 6 class walls, and 93.6 % agreement with the metadata truth on function names `[CERT-hw]`

`evidence/b121/kt_plugin_audit.py` lists every failure site (`evidence/b121/kt-plugin-walls.tsv`, 67 rows: `n-plugin` 60, `n-conv-plugin` 1, `settings` 2, `utils` 4) plus the whole-class failures (6, all `n-plugin`: `SignedZip`, `SignedTar`,
`KarmaConfig`, `GruntOptions`, `SigningProfileFactory`, `LocalSigningProfile`). The plugin's stack traces (`evidence/b121/kt-plugin-vf-markers.txt`) name `IllegalStateException: Anonymous class does not have Class Kotlin metadata` 70 times, `ArrayIndexOutOfBoundsException` 8
and `NullPointerException` 4 (each class-level failure prints two traces). The first is structural: **all 333 synthetic (`k=3`) classes carry no `d1` payload** (§121.5), so the plugin cannot write an anonymous-class expression such as the `Action`/`Transformer` lambdas Gradle plugins are full of.
The 36 `local visibility outside of methodSupplier` and 23 `Class flags could not be determined` markers are diagnostics inside otherwise printed code.

Walls hit methods that earlier blocks cite: `NiagaraModulePlugin.apply/registerModuleTasks/registerNiagaraTestTasks/configureIdeaPlugin`, `NiagaraJavaPlugin.apply` (the whole durable `NiagaraJavaPlugin.kt` is 41 lines), `VendorExtension.defaultGroup/defaultVendor/defaultModuleVersion/defaultDistVersion`,
`NativeCommand.execute`, `GruntPlugin.configureTask`, `NiagaraAnnotationProcessorsPlugin.apply`, `YarnWorkspacePlugin.apply`, `YarnWorkspaceAggregationPlugin.apply`, `RootProjectNiagaraNativePlugin.apply`, `CheckNodeInstalled.findNodeVersion`, `JavaScriptTaskKt.wireSkipJsConvention`.
Java mode prints all of these bodies (0 walls, though 122 lambda placeholders remain there), and [Block 36]/[Block 89] already used `javap` at several of these points.

Against the recovered metadata (§121.5), the plugin printed the declared function names for **663 of 708** (`n-plugin` 594/639, the other three 69/69) `[CERT-hw]` (`evidence/b121/kt-plugin-decl-agreement.tsv`); the 45 missing names sit in 8 top-level files, six of them the whole-class failures above.
It also prints 90 `fun` names that metadata does not declare (87 in `n-plugin`), among them the 75 `open fun <ClassName>(` pseudo-functions that are really the constructors of abstract `@Inject` classes (e.g. `Compact3ArgumentProvider.kt`); a citation of "the function `Compact3ArgumentProvider`" would be wrong.

## 121.4 — Fidelity matrix: what a Java-shaped view of Kotlin bytecode loses, measured per construct in these 696 classes `[CERT-hw]`

`evidence/b121/KotlinAudit.java` (ASM over the bytecode plus `kotlin-metadata-jvm` for the declarations) counted each construct (`evidence/b121/summary.tsv`, classes-with / occurrences):

| Construct | In these jars | What a Java view shows | Kotlin-level truth |
|---|---|---|---|
| default arguments | 92 default-valued params in 40 classes (44 functions, 12 constructors); **44 `$default` synthetic methods**, **52 constructors with `DefaultConstructorMarker`**, 159 `$default` call sites | `foo$default(this, a, 0, null, 6, null)`, bit-mask, default expression lost | `fun foo(a, b = <expr>)`; kt run still shows 119 `$default` tokens (Java run 151) |
| `@JvmOverloads` / same-name overloads | 104 JVM methods share a declared function's name | several unrelated-looking overloads | one declaration with defaults |
| companion objects | 39 companions in 39 classes; **9 `@JvmStatic` forwarders in 8 classes**; 2 static methods in companions | `Companion` field, `$Companion` class, static forwarder | `companion object { @JvmStatic fun }` |
| inline functions | 6 inline funs in 3 classes; **435 `$i$f$` expansion markers in 142 classes, 406 `$i$a$` in 148 classes, 47 distinct inline functions expanded** (top: `named` 52, `typeOf` 36, `newInstance` 34, `property` 33, `register` 32) | the inlined body pasted at each call site under marker locals | one call to the inline function |
| reified type parameters | 6 in 3 classes; 0 reified-stub methods | `TypeOf`/`Class` plumbing | `inline fun <reified T>` |
| suspend / coroutines | **0** suspend functions, 0 `Continuation` parameters, 0 state-machine classes (class-level census over all 696 classes) | n/a | not used in these jars (measured, not assumed) |
| null-check intrinsics | **2,250 calls in 531 classes** (`checkNotNullParameter` 1,054, `checkNotNullExpressionValue` 1,030, `checkNotNull` 84, `areEqual` 77, `throwUninitializedPropertyAccessException` 5) | explicit calls, `@NotNull` everywhere | non-null types are the default |
| nullability inside generics | 119 nullable types in signatures (50 classes); **3 nullable type arguments (2 classes) that the JVM generic signature does not carry** | `List<String>` | `List<String?>` |
| data classes | 9 data classes; 61 synthesized member functions | plain class with `component1`, `copy`, `copy$default` | `data class` |
| extension receivers | 160 extension functions in 57 classes, 5 extension properties; 1,006 `$this$` names in 360 classes | static method with first parameter `<this>` | `fun Receiver.name()` |
| file facades | 35 `*Kt` classes (all file-facade kind), 0 multifile | class named `FooKt` | top-level functions in `Foo.kt` |
| properties | 836 declared; 226 with no explicit getter signature; 107 private with no getter at all; 28 `var`, 808 `val`; **5 `lateinit`** in 2 classes; 137 `const val` in 27 classes; 17 delegated properties (8 classes, 17 `LazyKt.lazy` calls) | fields plus getters | `val`/`var`/`lateinit`/`const`/`by lazy` |
| `internal` | 38 functions in 13 classes, 28 with a module-suffixed JVM name in 9 classes (e.g. `getSourceFiles$n_plugin`) | public method with odd name | `internal fun` |
| class delegation `by` | 1 class (`LazyList`): 42 delegated functions in metadata, **16 mutator stubs** that throw `UnsupportedOperationException("Operation is not supported for read-only collection")` | a `java.util.List` with `add`/`remove`/`sort` | a read-only Kotlin `List<T>`; the stubs are compiler-generated |
| other | `object` INSTANCE fields 124 (2 objects), `$WhenMappings` 12 classes, 14 enum classes with 74 entries, stdlib `*Kt` static calls 480 (73 distinct: `CloseableKt.closeFinally` 99, `TuplesKt.to` 41, `CollectionsKt.joinToString$default` 39), 92 `LambdaMetafactory` sites in 43 classes, 333 synthetic lambda/SAM classes | statics and switch-map tables | idiomatic constructs |

Sealed classes, value classes, `tailrec`, `infix`, `fun interface`, `crossinline`/`noinline` and multifile facades do not occur: 0 in a class-level census of every one of the four jars' 696 classes.

## 121.5 — Kotlin-level recovery from `kotlin.Metadata`: 696 of 696 classes decode, yielding 774 functions, 836 properties and 262 constructors with names, nullability, defaults, visibility, receivers and accessors `[CERT-hw]`

No Kotlin metadata reader was available locally (`~/.m2` and `organized/_lib-inf-3p` hold only `kotlin-stdlib`; `find / -iname "*kotlin*metadata*"` found none). `org.jetbrains.kotlin:kotlin-metadata-jvm:2.4.10` was fetched from Maven Central on 2026-09-29;
**its SHA-1 equals Central's `.sha1` file** (`6bbc294143523b1d327772bd3a09d4a18a7ac837`), sha256 `233aaa84ca268e26d6d3a99ce30401e6dc111a7ae10e0a0b4794ce6351d7adc4`; provenance in `sources/SOURCES.md` and `evidence/b121/README.md`.
`KotlinAudit.java` rebuilds a `kotlin.Metadata` instance from each class's annotation (ASM `AnnotationNode` → `Proxy`), calls `KotlinClassMetadata.readStrict` and prints one listing per class into `organized/_evidence/b121/kotlin-signatures/` (696 files, 3.1 MB, out of git; sha256 list in git).

| Recovered | Count |
|---|---|
| classes decoded / classes | **696 / 696** (0 `metadata-decode-FAILED`) |
| functions (243 classes) | 774 |
| properties (214 classes) | 836 |
| constructors (259 classes) | 262 (3 secondary) |
| class kinds (the 328 `k=1` classes) | 247 classes (9 of them data classes), 39 companions, 26 interfaces, 14 enums, 2 objects |
| `k=3` synthetic classes without any declaration payload | **333 of 333** (this is why the Kotlin plugin cannot render lambdas, §121.3) |

Recovered facts that neither Java-shaped view carries, with sample lines in `evidence/b121/sample-signatures.txt`: `public lateinit var os/arch/devkitName/compiler` on `NiagaraNativePlatform` (a `public final data class`), `public fun defaultModuleVersion(version: kotlin.String): kotlin.Unit` as a
member of `VendorExtension` (not an extension function), `private val props: java.util.Properties by <delegate>` on `SigningProfileProperties`. **What metadata does not carry: method bodies** — 0 bytes of body logic are recovered; bodies still need the plugin's `.kt`, a Java-mode run or `javap`.
For 226 properties the metadata stores no getter signature (the default accessor is implied), which is why the tool falls back on name matching for those.

## 121.6 — JVM-method mapping: 1,801 of 3,297 JVM methods are declared Kotlin functions or accessors, 1,494 are compiler-generated, 2 are generated `toArray` `[CERT-hw]`

Each JVM method of the 696 classes was matched to a metadata declaration (exact `name+descriptor` from the JVM signature, else same-name overload, else property accessor) or to a named generation rule (`evidence/b121/top.tsv`, `classes.tsv`):
declared 1,691 · same-name overload 104 · property accessor 6 · constructors with no metadata (default and synthetic-class constructors) 373 · synthetic lambda/SAM bodies 300 · bridges 299 · `<clinit>` 195 · lambda bodies (`foo$lambda$0`) 100 · enum generated 56 ·
`$default` constructors 52 · `$default` methods 44 · `access$` 29 · other synthetic 21 · read-only-collection mutator stubs 16 · `@JvmStatic` forwarders 9 · **unexplained 2** (`LazyList.toArray()` and `toArray(T[])`,
whose bodies call `kotlin/jvm/internal/CollectionToArray.toArray`, i.e. also compiler-generated: `javap -c` of `LazyList.class`; `evidence/b121/residual.tsv`). 45 % of the JVM surface of these classes is therefore not Kotlin source.

## 121.7 — B117-G2 audit CLOSED: 42 claims from 15 blocks — 36 SAFE, 4 SUSPECT, 1 CONTRADICTED, 1 ADVANCED `[CERT-hw]`

`evidence/b121/claim-audit.tsv` lists each claim (block, section and line, paraphrase, verdict, and the check that decided it). Method: every citation of these jars was located by class name, `.kt` name and package prefix across all 120 blocks (31 blocks match a class name, package or plugin name, many of them coincidences such as `Version` or `Plugin`; the load-bearing ones are B2, B7, B9, B36, B39, B51,
B60, B74, B79, B89, B97, B108, B117 plus B55/B106 for third-party Kotlin), then re-checked against three durable sources: the corpus `vineflower2` tree, the fresh Java-mode tree (for the 73 wall sites) and the shipped bytecode (`javap -c -p`), plus the recovered metadata.
A claim is SAFE when the behaviour it states is present in that evidence and does not rest on a construct §121.4 marks as lossy; SUSPECT when the value is right but the cited location/identifier is not, or the count is off; CONTRADICTED when the same artifact says otherwise.

| Block | Claims | SAFE | SUSPECT | CONTRADICTED | ADVANCED |
|---|---|---|---|---|---|
| B2 | 9 | 7 | 1 | 1 | 0 |
| B7 | 1 | 0 | 0 | 0 | 1 |
| B9, B55, B60, B79, B97, B106 | 6 | 6 | 0 | 0 | 0 |
| B36 | 11 | 10 | 1 | 0 | 0 |
| B39 | 2 | 2 | 0 | 0 | 0 |
| B51 | 2 | 2 | 0 | 0 | 0 |
| B74 | 5 | 5 | 0 | 0 | 0 |
| B89 | 3 | 2 | 1 | 0 | 0 |
| B108 | 2 | 2 | 0 | 0 | 0 |
| B117 | 1 | 0 | 1 | 0 | 0 |
| **Total** | **42** | **36** | **4** | **1** | **1** |

The six non-SAFE rows:

- **CONTRADICTED — [Block 2] §2.5 heading** ("now exposed as a Kotlin `Slotomatic` task type"). `Slotomatic`, `SlotomaticTask` and `MigrateSlotomaticTask` in `com/tridium/gradle/plugins/module/task/` carry no `kotlin/Metadata` (zip read of `n-plugin-5.0.54.9.2.jar`); they are Java, as the section's own citation (`Slotomatic.java`) shows.
  Only the registering plugin `NiagaraModulePlugin` is Kotlin. [Block 74] §74.1 already states it correctly ("Slotomatic/generator code stays Java while the Gradle plugins are Kotlin"). `[CERT-hw]`
- **SUSPECT — [Block 36] §36.5** (`GruntCiOptions.kt:18-130`, "`stationHttpPort` (default 9088) / `stationHttpsPort` (9089) / `stationFoxPort` (9911)"). The values are right; the location is not. `GruntCiOptions` only declares `Property<Int>` (`GruntCiOptions.kt:36-38`). The defaults are
  `private const val DEFAULT_STATION_HTTP_PORT/…HTTPS…/…FOX… = 9088/9089/9911` in `GruntPlugin.Companion` (`organized/_etc-m2/n-plugin-5.0.54.9.2/vineflower2/com/tridium/gradle/plugins/grunt/GruntPlugin.kt:235-237`), applied by the lambda class `GruntPlugin$configureTask$2`
  (`javap -c`: `GruntCiOptions.getStationHttpPort` then `sipush 9088` … `Property.convention`); `const val` is inlined, and `GruntPlugin.configureTask` is a wall in the durable `.kt`. `[CERT-hw]`
- **SUSPECT — [Block 89] §89.8** ("the full list of 17 companion-object key-name constants", `NativeCommand.kt:43-77`). The companion declares **18** `const val` key names (CC 7, LD 7, AR 4) and B89's own enumerated list has 18; count only, not caused by Kotlin. → B121-G3. `[CERT]`
  (`organized/_etc-m2/n-plugin-5.0.54.9.2/vineflower2/com/tridium/gradle/plugins/natives/command/NativeCommand.kt:387-409`)
- **SUSPECT — [Block 2] §2.4 :246** quotes the decompiler names `var59`/`var60` as evidence (the tree carries 3,075 such synthetic names); the behaviour claimed is true (`moduleManifest`, `writeModuleXml` at `NiagaraModulePlugin.java:395,422`). Cosmetic.
- **SUSPECT — [Block 117] §117.4 :129** ("a Java decompile of Kotlin bytecode"): counts reproduced; the trees are Kotlin-plugin output (§121.2). Scope clarification, not a refutation.
- **ADVANCED — [Block 7] §7.x (B7-G1)**, §121.8.

Two non-obvious SAFE rows worth naming: **[Block 89] §89.1**'s `lateinit` finding (derived from `Intrinsics.throwUninitializedPropertyAccessException` in bytecode) is now confirmed by declaration: metadata lists `public lateinit var os/arch/devkitName/compiler`, and the message text
`"lateinit property " + name + " has not been initialized"` is in `kotlin/jvm/internal/Intrinsics` (`javap -c` of the stdlib class), so the exception text B89 quotes is exact. And the **[Block 55]/[Block 106]** claims read from decompiled `okhttp-jvm`/`okio-jvm` were checked against the SHA-1-verified upstream sources
(`organized/_upstream-sources/com.squareup.okio/okio-jvm/3.18.1/` and `com.squareup.okhttp3/okhttp-jvm/5.5.0/`): `DefaultSocket.kt`/`PipeSocket.kt` contain no `connect(`/`Socket(`/`getByName`; `ConnectPlan.kt:271-272` reads `Proxy.Type.DIRECT, Proxy.Type.HTTP -> …createSocket()!!` / `else -> JavaNetSocket(route.proxy)`, which the decompile printed as `1, 2 ->` (a `$WhenMappings` ordinal).

## 121.8 — B7-G1 ADVANCED to `[CERT-hw]`: no Gradle task edge links `slotomatic` to `compileJava`; the unrepresentable lambda only sets `javaLanguageLevel` `[CERT-hw]`

[Block 7] §7.x could not read the Kotlin lambda that Vineflower renders as `var14.configureEach(<unrepresentable>.INSTANCE)` at the end of `registerSlotomaticTasks()` and concluded from the processor's existence that the task graph does not order Slotomatic before `compileJava` `[INFER]`. `javap -c -p` of the lambda class
`NiagaraModulePlugin$registerSlotomaticTasks$3` (and its `$3$1`, `$3$execute$$inlined$the$1`) shows it only calls `SlotomaticTask.getJavaLanguageLevel().set(…)` from `JavaPluginExtension.getToolchain().getLanguageVersion().map(JavaVersion::toVersion)`. The Java-mode tree lists the module plugin's 7 `dependsOn` sites
(`organized/_evidence/b121/vf-java/n-plugin/com/tridium/gradle/plugins/module/NiagaraModulePlugin.java:433,547,576,584,670,1093,1128`): `writeModuleXml`→`compileJava`, `writeTestModuleXml`→`compileTestJava`, `assemble`/a disabled task/`RunNiagaraTestTask`→`moduleTestJar`, `check`→`niagaraTest`, javadoc jar→`javadoc`; none involves `slotomatic` or
`migrateSlotomatic`, and the rest of the plugin package has no `finalizedBy`/`mustRunAfter`. So [Block 7]'s conclusion (Slotomatic is not sequenced automatically) holds, now from bytecode rather than inference; the gap B7-G1 is answered for `n-plugin` 5.0.54.9.2. (The one thing this cannot show is Gradle's implicit ordering through task inputs; that needs a `gradlew` run, B106-G1's family.)

## 121.9 — Claim rules for citing the Kotlin-compiled Tridium jars `[INFER]`

1. Language first: a class is Kotlin only if `@kotlin.Metadata` is on it. `Slotomatic*`, `ModuleXml`, `UnterjarCopySpec`, `UberjarCopySpec` and 70 other `n-plugin` classes are Java.
2. Prefer the recovered declaration (`kotlin-signatures/`, generated by `evidence/b121/run_audit.sh`) for "what is declared" (nullability, `lateinit`, defaults, visibility, extension vs member, `internal`), the Kotlin-plugin `.kt` for control flow where it printed the method, and Java mode or `javap` at every wall in `kt-plugin-walls.tsv`.
3. Never cite a `varN`, `$this$…` or `$i$…` name, nor an `open fun <ClassName>(` line, as source identity.
4. A default value in a Kotlin `const val` lives in the companion and is inlined at use sites; cite the use-site bytecode (`sipush`, `ldc`), not the declaring class's options file.
5. A `.kt:<line>` citation into the pre-2026-09-29 `/tmp/.../vf-out` trees cannot be re-read; re-cite the durable `organized/_etc-m2/<jar>/vineflower2/` path, whose lines differ (the durable `NativeCommand.kt` const block is 8 lines later than B74 cites).

## 121.10 — Typed walls and limits

- **Metadata carries no bodies** (§121.5): `kotlin-metadata-jvm` recovers declarations only. Behaviour claims at the 73 wall sites still rest on Java mode or `javap`.
- **No Kotlin round trip** (`blocked-on-tool`, requires-execution): `kotlinc` is not installed; the `.kt` output was not recompiled and compared with the shipped bytecode, so the Kotlin plugin's control-flow fidelity beyond function names (663/708) is unmeasured (B121-G2).
- **Third-party Kotlin** (`kotlin-stdlib`, `okhttp-jvm`, `okio-jvm`, `jackson-module-kotlin`, `kotlin-reflect`; 2,672 classes) was censused only; two blocks' claims were checked against upstream sources; no other block cites them (`rg -il "okhttp|okio|jackson-module-kotlin|kotlin-reflect" niagara5-block*.md` → B55, B106, B117, B3).
- Everything runs against class-file major 69 with ASM 9.10.1 and Vineflower 1.12.0; a different Vineflower or Kotlin-plugin version would change the wall list.

## 121.11 — Corrections to earlier blocks

For the orchestrator's §14 pointers (added in this commit): **[Block 2] §2.5** heading refuted (same artifact; §121.7); **[Block 36] §36.5** default-port attribution (values right, location wrong; §121.7); **[Block 7] §7.x** B7-G1 answered from bytecode (§121.8); **[Block 117] §117.4** scope clarification (trees are Kotlin-plugin output, not a Java decompile).
[Block 89] §89.8's "17" is a recount for B121-G3 (no pointer needed beyond the register row). B117-G1's row can be flipped: the durable `organized/_etc-m2/*` and `organized/_lib/*` trees with `recon.json` exist for all 10 jars (§121.2); the devkit `LIB-INF` Tridium jars are not part of what this block checked.

## 121.12 — Connections

- [Block 117] §117.4/B117-G2 (the gap; census reproduced exactly; "Java decompile" wording clarified). [Block 115]/[Block 116]: the resugaring and loss-catalog method; this block adds the Kotlin lossy constructs those Java-only catalogs cannot see.
- [Block 118] §118.1 and [Block 120]: conservative and pattern-switch fidelity of the same Vineflower; the Kotlin plugin is a third rendering mode with its own failure class (anonymous classes).
- [Block 2], [Block 7], [Block 36], [Block 39], [Block 51], [Block 74], [Block 89], [Block 97], [Block 108]: the claim register of §121.7.
- [Block 106]/[Block 55]: third-party Kotlin claims verified against upstream sources.

## 121.13 — Child gaps opened

- **B121-G1** (medium, investigable read-only) — Give each of the 73 wall sites a durable readable counterpart: add a Java-mode companion tree (`--kt-enable=false`) for the four jars under `organized/_etc-m2/<jar>/vineflower2-java/`, or a wall index the trees point to, and decide whether `tools/n5-decompile.sh` should emit both for Kotlin jars.
  coverage-check: `rg -il "kt-enable|Couldn't be decompiled" niagara5-block*.md tools/n5-decompile.sh` → only the comment at `tools/n5-decompile.sh:82-84`; no block records the wall list. measured-by: wall sites with a durable Java-mode counterpart, of 73 (baseline 0).
- **B121-G2** (medium, requires-execution → §19) — Recompile the four jars' `.kt` output with `kotlinc` 2.2.x against the Gradle API and Niagara classpath and compare normalized bytecode with the shipped classes (the Kotlin analogue of B116's oracle), to grade control-flow fidelity of the plugin; blocked on `kotlinc` and the Gradle/Kotlin classpath.
  coverage-check: `rg -il "kotlinc" niagara5-block*.md tools/*.py` → none. measured-by: methods with equal normalized bytecode after recompile, of the 3,297 JVM methods (baseline 0 of 3,297).
- **B121-G3** (low, investigable read-only) — Recount [Block 89] §89.8's NativeCommand key sets (17 vs 18 constants; "SEVEN cc-side and NINE ld/ar-side" populated keys) against `NativeCommand.kt` and the bytecode of `initializeCcProperties`/`generateLinkProperties`.
  coverage-check: `rg -n "17 companion|SEVEN cc-side" niagara5-block*.md` → [Block 89] only. measured-by: constants re-enumerated, expected 18 (baseline B89 says 17).
- **B121-G4** (low, investigable read-only) — Audit claims that rest on the five third-party Kotlin jars beyond [Block 55] and [Block 106], and grade `okhttp-jvm`/`okio-jvm` `.kt` output against their upstream sources the way §121.7 did for 2 claims.
  coverage-check: `rg -il "okhttp|okio|jackson-module-kotlin|kotlin-reflect" niagara5-block*.md` → B3, B55, B106, B117. measured-by: third-party Kotlin claims with a SAFE/SUSPECT verdict, of those found (baseline 2 of 2 found so far).
- **B121-G5** (low, investigable read-only) — Root-cause the 45 metadata function names missing from the plugin's `.kt` (8 files) and the 90 `fun` names metadata does not declare (75 are constructor pseudo-functions); report to Vineflower if reproducible on a minimal class.
  coverage-check: `rg -il "unrepresentable|pseudo-function" niagara5-block*.md` → B2, B7, B120 (lambda and switch cases), none on constructors. measured-by: names missing/extra after a per-file diff, baseline 45 and 90.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 475 jar entries censused; 10 hold Kotlin (3,368 classes); the 4 Tridium jars hold 696 (650 + 14 + 20 + 12), third-party 2,672; no module jar has its own Kotlin | [CERT-hw] | `evidence/b121/kotlin_census.py`, `evidence/b121/kotlin-census-all.tsv` |
| 2 | Kinds and metadata versions per jar (n-plugin 306/28/316, all 2.2.0) | [CERT-hw] | `evidence/b121/kotlin-census-all.tsv`, `evidence/b121/summary.tsv` |
| 3 | The corpus `vineflower2` trees for the 4 jars are Kotlin-plugin output: 329 `.kt` + 62 `.java`; fresh run byte-identical for 374 of 391 files | [CERT-hw] | `evidence/b121/run_vineflower.sh`, `evidence/b121/compare_trees.py`, `evidence/b121/tree-compare.tsv`, `evidence/b121/trees.sha256` |
| 4 | Vineflower 1.12.0 embeds the Kotlin plugin and `--kt-enable` defaults true | [CERT-hw] | `evidence/b121/README.md` (plugin jar sha256), `tools/decompilers/README.md` |
| 5 | Kotlin plugin: 67 method walls, 6 class walls; Java mode 0; lines 25,446 vs 43,608; `Intrinsics.` 236 vs 2,067; `@NotNull/@Nullable` 46 vs 2,225 | [CERT-hw] | `evidence/b121/tree-compare.tsv`, `evidence/b121/kt-plugin-walls.tsv`, `evidence/b121/kt-plugin-vf-markers.txt` |
| 6 | 333 of 333 synthetic classes carry no d1 payload; 70 "Anonymous class does not have Class Kotlin metadata" traces | [CERT-hw] | `evidence/b121/summary.tsv`, `evidence/b121/kt-plugin-vf-markers.txt` |
| 7 | Plugin function names match metadata for 663 of 708; 90 extra names; 75 constructor pseudo-functions | [CERT-hw] | `evidence/b121/kt_plugin_audit.py`, `evidence/b121/kt-plugin-decl-agreement.tsv`, `evidence/b121/tree-compare.tsv` |
| 8 | `kotlin-metadata-jvm` 2.4.10 sha1 equals Central's; 696 of 696 classes decode; 774 functions, 836 properties, 262 constructors | [CERT-hw] | `evidence/b121/KotlinAudit.java`, `evidence/b121/summary.tsv`, `evidence/b121/README.md`, `evidence/b121/kotlin-signatures.sha256` |
| 9 | Construct counts of §121.4 (defaults, companions, inline markers, intrinsics, extensions, facades, lateinit, const, delegation) and the 0-counts | [CERT-hw] | `evidence/b121/summary.tsv`, `evidence/b121/top.tsv` |
| 10 | JVM-method mapping: 1,691 + 104 + 6 declared, 1,494 generated, 2 `toArray` residual (bodies call `CollectionToArray`) | [CERT-hw] | `evidence/b121/top.tsv`, `evidence/b121/classes.tsv`, `evidence/b121/residual.tsv` |
| 11 | 42 claims audited: 36 SAFE, 4 SUSPECT, 1 CONTRADICTED, 1 ADVANCED | [CERT-hw] | `evidence/b121/claim-audit.tsv` |
| 12 | `Slotomatic`/`SlotomaticTask`/`MigrateSlotomaticTask` are Java (no `kotlin/Metadata`) | [CERT-hw] | `evidence/b121/claim-audit.tsv` row B2 §2.5, `organized/_etc-m2/n-plugin-5.0.54.9.2/extracted/com/tridium/gradle/plugins/module/task/` |
| 13 | Port defaults 9088/9089/9911 are `const val` in `GruntPlugin.Companion`, applied in `GruntPlugin$configureTask$2` | [CERT] | `organized/_etc-m2/n-plugin-5.0.54.9.2/vineflower2/com/tridium/gradle/plugins/grunt/GruntPlugin.kt:235-237`; `javap -c` of `GruntPlugin$configureTask$2.class` |
| 14 | `NativeCommand` companion declares 18 key constants | [CERT] | `organized/_etc-m2/n-plugin-5.0.54.9.2/vineflower2/com/tridium/gradle/plugins/natives/command/NativeCommand.kt:387-409` |
| 15 | B7-G1: the hidden lambda only sets `javaLanguageLevel`; 7 `dependsOn` sites, none for slotomatic | [CERT-hw] | `evidence/b121/claim-audit.tsv` row B7; `javap -c` of `NiagaraModulePlugin$registerSlotomaticTasks$3.class`; `organized/_evidence/b121/vf-java/n-plugin/com/tridium/gradle/plugins/module/NiagaraModulePlugin.java:433` |
| 16 | `lateinit var os/arch/devkitName/compiler` on `NiagaraNativePlatform`; message text in `Intrinsics` | [CERT-hw] | `evidence/b121/sample-signatures.txt`, `evidence/b121/kotlin-signatures.sha256` |
| 17 | okio/okhttp claims of B55/B106 match the upstream sources | [CERT-hw] | `evidence/b121/claim-audit.tsv` rows B55, B106 (sources under `organized/_upstream-sources/`) |
| 18 | Behaviour claims at the 73 wall sites rest on Java mode or `javap`, not metadata | [INFER] | metadata has no bodies (§121.5); B121-G1/G2 |
| 19 | The plugin's control-flow output is faithful beyond function names | [INFER] | not round-tripped; B121-G2 |

**Tally (literal `verify-block.sh` output):** `[CERT-hw]` 31 (adj 30) · `[CERT]` 5 (adj 4) · `[INFER]` 6 (adj 5) · `[INFER]`/`[CERT*]` = 5/34 = 0.15; by table row: 17 rows `[CERT-hw]`/`[CERT]`, 2 rows `[INFER]` (both explicitly gapped).

**Artifacts:** `evidence/b121/` (scripts, tables, README, `claim-audit.tsv`; no binaries, no decompiled or reconstructed source beyond the 3-class sample of declarations); out of git under `organized/_evidence/b121/`: 696 Kotlin declaration listings, fresh Vineflower `vf-kt/` and `vf-java/` trees, the `kotlin-metadata-jvm` jar, sha256 lists in `evidence/b121/`. No new `tools/` code (evidence scripts only).
