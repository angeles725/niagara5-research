# Block 116 — What Java decompilation cannot or did not preserve: an empirical loss catalog for the N5 tree (synthetic javac-25 first principles, a 2,809-file docSource differential, a recompile-and-compare bytecode oracle, 11 confirmed semantic defects in the corpus's own decompiled text, and docSource proven byte-identical to the shipped bytecode)

> Research answering T14 of `odd/tasks/decompiler-fidelity-audit.md` ("find EVERYTHING that is not faithful, with
> evidence"). It extends [Block 115] §115.1 (which established WHICH Java idioms are bytecode-distinguishable) to
> the full question of WHAT a decompile loses, invents, or gets semantically wrong. Three parts: **A** — minimal
> source pairs compiled with `javac 25.0.4.1 --release 25` (with `-g`, as Tridium ships, and without), decompiled by
> Vineflower 1.12.0, CFR 0.152, Procyon 0.6.0 and JADX 1.5.6, each output RECOMPILED and compared per method
> against the original bytecode; **B** — every docSource original that has a corpus decompile (2,809 top-level
> files, 46 modules: 2,516 Vineflower + 293 CFR-fallback in `bajaui`) diffed after staged normalization, and the
> decompiled text recompiled against the shipped jars and compared per method to the shipped class files;
> **C** — a four-way verdict (faithful / unrecoverable-but-harmless / unrecoverable-and-claim-relevant /
> semantic-risk) with the claim rules that follow. Also answers the orchestrator addendum (JEP 513, JEP 456,
> constant-dynamic, preview class files, record patterns with guards, anonymous-class expressions, library
> context, IntelliJ `@NotNull` instrumentation).
>
> Does **not** cover: the ~12,100 top-level classes with no docSource original (their semantic fidelity needs
> the shipped-bytecode round-trip grader of T15, child gap **B116-G1**); the 152 decompiled files that do not
> recompile (**B116-G3**); N4 trees.
>
> Subject: N5 5.0.0.28 beta. Decompiled tree `organized/<mod>/vineflower|fallback/`, shipped classes
> `organized/<mod>/extracted/` (nre: `organized/_bin-ext/nre/`), docSource originals `organized/docSource/<mod>/`
> (from `docSource.jar` in the config-home modules). Classpath for every recompile: all 247 config-home module
> jars + every `bin/ext` jar + the 96 nested `LIB-INF/*.jar` of the module jars + `javafx.base`/`javafx.graphics`
> extracted from the Niagara JRE `jre/lib/modules` (javafx is needed by `workbench` `BWbProfile` and `test`
> `TestRunnerNg`). Decompiler jars: `tools/decompilers/` (Vineflower sha256
> `1dfcfe974395734fa467ce620661c7623d05ba83670de0529b1fbd63ff548b9d`). Method tooling (scratch, sha256 in
> Self-verify): a pure-Python class-file parser that resolves constant-pool references and expresses branch
> targets as instruction ordinals (`cf.py`), a per-method comparer (`cmp.py`), an effect-multiset differ and
> rule classifier (`semdiff.py`, `classify.py`), a staged text normalizer (`normdiff.py`), a bytecode census
> (`census.py`). ALREADY-COVERED check: `rg -il 'overload|recompil|docSource.*stale'` over the corpus — only
> [Block 115] touches the topic (§115.1 matrix, §115.3 one constant-inlining pair); nothing in the corpus
> measures semantic fidelity or docSource currency, so nothing here is re-derived.

## 116.1 — docSource is ground truth: the 45 docSource module trees recompile to BYTE-IDENTICAL instruction streams and identical LineNumberTables for all 3,707 class files / 42,922 methods of the shipped jars `[CERT-hw]`

Every `organized/docSource/<mod>/**/*.java` (minus `package-info`) was compiled per module with
`javac --release 25 -g -proc:none` and compared per method with the shipped `organized/<mod>/extracted/` class of
the same name (instructions with resolved constant-pool operands + exception tables), and separately on
LineNumberTable equality.

| Measure | Result |
|---|---|
| Modules compiled | 45 of 45 docSource trees (`doc` holds no `.java`); 0 compile errors once LIB-INF + javafx are on the classpath |
| Class files compared (top-level + nested/anonymous) | 3,707 — **3,707 `exact`**, 0 method-set deltas, 0 field-set deltas |
| Methods compared | 42,922 — **42,922 identical** instruction streams + exception tables |
| LineNumberTables | 42,922 / 42,922 identical |

**Verdict: docSource is NOT stale.** It is the exact source text of the shipped 5.0.0.28 bytecode (identical line
numbers rule out even a whitespace-level edit), and Tridium's compiler emits the same code as `javac 25.0.4.1`
([INFER] same javac 25 update line; only equal output is proven). Consequence for every later section: the 2,776
docSource-covered classes (T13's figure; 2,809 files here counting `nre`) are a valid oracle, and a
docSource citation is strictly stronger than any decompiler citation. Evidence: `organized/docSource/control/niagara/control/BStringWritable.java`
vs `organized/control/extracted/niagara/control/BStringWritable.class` (representative); full per-module result
in scratch `b116/ds-vs-shipped.txt`, `cmpres/ds-*.json`.

## 116.2 — Retention facts: what the class file keeps at all `[CERT-hw]`

- **Comments/javadoc, imports, `package` spelling, source formatting, radix/underscore of literals, unicode escapes,
  explicit `this.`/`super()`/qualifiers, `final` on locals, local/param generic spelling without `-g`**: not encoded in
  the class file (javap `-v` of every `pa` suite class shows no attribute or constant-pool entry for them) — no
  decompiler can recover them.
- **Annotations** (javap `-v` on `organized/_bin-ext/niagaraAnnotationProcessors/extracted/niagara/nre/annotations/*.class`,
  jar sha256 `fbffe97b5b8836b4fa5960da40cdb5d0463b319c8045af2331684007a2c0832d`): Tridium's slot annotations
  `@NiagaraProperty`, `@NiagaraProperties`, `@NiagaraAction(s)`, `@NiagaraEnum`, `@NiagaraTopic(s)`, `@NiagaraSlots`,
  `@Facet`, `@Range` declare **no `@Retention` → CLASS** (kept as `RuntimeInvisibleAnnotations`, and Vineflower
  renders them); `@Generated` is explicit **CLASS**; `@NiagaraType`, `@NiagaraSingleton`, `@AgentOn`, `@FileExt`,
  `@Adapter`, `@ModuleResources*`, `@NiagaraEnableNativeAccess` and the permission annotations are **RUNTIME**;
  `@NoSlotomatic` is **SOURCE** (lost). JDK: `@Override`/`@SuppressWarnings`/`@SafeVarargs`-on-nothing are
  SOURCE-level for our purposes (`@Override`, `@SuppressWarnings` have no constant-pool entry in the javap of the
  synthetic `A02Annot`), while `@FunctionalInterface`, `@Deprecated`, `@SafeVarargs` are RUNTIME (javap shows
  `RuntimeVisibleAnnotations: java.lang.FunctionalInterface` on `A02Annot$Fn`) — i.e. `@FunctionalInterface` IS
  preserved, contrary to the task's candidate list.
- **Annotation element values are constant-folded**: docSource `flags = Flags.SUMMARY | Flags.TRANSIENT`
  (`organized/docSource/control/niagara/control/BStringWritable.java:135`) is `flags = 10` in the decompile
  (`organized/control/vineflower/niagara/control/BStringWritable.java:42`), and every slotomatic
  `newProperty(Flags.READONLY, …)` becomes `newProperty(1, …)`. The symbolic flag NAMES are unrecoverable; the
  value is exact.
- **Debug info**: every shipped class whose methods have local variables carries a LocalVariableTable (census:
  20,325 of 20,744 classes-with-code have one; the other 419 have no method with any local slot). So local and
  parameter NAMES in the N5 tree are Tridium's, except where the decompiler renames (§116.3 A5). All 21,751 shipped
  class files are major 69, minor 0.

## 116.3 — Part A: the synthetic loss matrix, decided by recompiling each decompiler's output and diffing bytecode `[CERT-hw]`

Three suites (`pa` 27 files / 43 classes, `pb` 3 classes / 50 probes, `pc` 6 classes / 12 probes). "Keeps?" is the
javap/`cf.py` verdict on the ORIGINAL class; the four decompiler columns say what the decompiled text shows, and
**SEM** marks a recompile whose bytecode binds or computes differently from the original.

| # | Loss class | Bytecode keeps? | Vineflower 1.12 | CFR 0.152 | Procyon 0.6 | JADX 1.5.6 |
|---|---|---|---|---|---|---|
| A1 | comments, javadoc | no | lost | lost | lost | lost |
| A2 | `@Override` | no (SOURCE) | **synthesized** on some overriding methods (on `run()`, not on bridged `compareTo`) | synthesized on all | synthesized | synthesized + `// java.lang.Runnable` note |
| A2b | `@SuppressWarnings`, custom SOURCE annotation | no | lost | lost | lost | lost |
| A2c | CLASS / RUNTIME annotations, type-use annotations | yes (`RuntimeInvisible*`, `RuntimeVisible*`, `…TypeAnnotations`) | recovered | recovered | type-use **dropped** | type-use dropped; visible/invisible order swapped |
| A3 | compile-time constant inlining (cross-class `K.HOST`, same-class, `60*1000`, `"a"+"b"`, `1\|8\|256`) | only the folded value (`ldc`/`sipush`) | literal everywhere | same-class names re-symbolized, cross-class literal | literal | **re-symbolizes by value across classes**: `60*1000` → `MS`, ordinal `0` → `case K.DEBUG /* 0 */` (a boolean), `3` → `A31Iface.X` — invented references |
| A3b | non-constant `static final` (`Integer BOXED = 7`, `String.valueOf(3)`) | yes (`getstatic`) | kept symbolic | kept | kept | kept |
| A4 | dead code (`if(false)`, `if(DEBUG)` with constant false, `DEBUG && x`) | eliminated by javac | gone | gone | gone | gone |
| A5 | local names / declared types | LVT+LVTT with `-g` | names + generic declared types recovered; **drops single-use named locals** (`short s = 300; return s` → `return 300`); renames on scope clash (`t` → `tx`, `x = 2` → `int var6 = 2`) | names kept, declared type replaced by allocation type (`ArrayList<String> names`) | adds `final` everywhere (invented) | recovered |
| A5b | same, compiled without `-g` | no | `var1…`, raw types + explicit casts | heuristic names (`n`, `string`) | heuristic | heuristic |
| A6 | erasure casts, bridge methods | casts yes; bridges `ACC_BRIDGE` | bridges hidden | hidden | hidden | **emits a bridge as source** with a wrong signature (`compareTo(A06Generics)`) |
| A7 | lambdas / method refs (`LambdaMetafactory` indy) | yes | recovered | recovered, `Supplier<List>` generic lost | recovered + casts | `String::length` rendered as a lambda |
| A8 | inner / anonymous / local classes, outer `this$0`, `Objects.requireNonNull` null-checks | yes (`InnerClasses`, `NestMembers`) | recovered; nested types moved to the end of the class | leaks `this$0` + `requireNonNull` (does not compile) | recovered | local class turned into `new Object(this){…}` |
| A9 | enum switch (same nest: direct `ordinal()` lookupswitch, no `$SwitchMap`; cross-class: `R$1.$SwitchMap`), string switch (hashCode lookupswitch), arrow/switch-expression, pattern switch | yes (shapes) | all recovered | enum switch → `switch (c.ordinal()) case 0` | same as CFR; pattern switch → helper class | `case K.DEBUG /* 0 */` |
| A10 | try-with-resources, finally copies, multi-catch | yes (duplicated finally code, handler table) | recovered | nested twr; multi-catch order swapped | recovered | twr expanded; **`fin()` SEMANTIC: finally body emitted inline AND as `finally`** (prints twice) |
| A11 | `assert` | yes (`$assertionsDisabled`) | recovered | recovered | recovered | expanded |
| A12 | labeled `break`/`continue` | only as gotos | labels removed; `break outer` → `return n` (equivalent) | label kept | label kept | label kept |
| A13 | ternary vs if/else, `&&` vs nested `if` | no (javac output interchangeable) | `if(a){if(b)…}` → `a && b ? 1 : 0` | if/else → ternary | kept | mixed |
| A15 | char/byte/short literals, radix, suffixes, unicode escapes, `0.0/0.0` | values only | `'0'` → `48`; hex/octal/`_` lost; `é` → raw `é`, lone surrogates escaped; `Double.NaN` re-symbolized | `'0'` → `48`; hex heuristic | `'0'` kept | `'0'` kept |
| A16 | implicit vs explicit boxing (`Integer i = 5` vs `Integer.valueOf(5)`) | identical bytecode | `valueOf` stripped (see S1-S5) | `(Integer)3` casts | `valueOf` kept | `.intValue()` explicit |
| A17 | varargs call vs explicit array | identical | `v(new String[]{"c"})` → `v("c")` | explicit `new String[0]` | same | same |
| A18 | string concat form (`indy StringConcatFactory` recipe) | recipe only | `""+i` → `i+""`; `StringBuilder` chains resugared to `+` | kept | kept | **`""+i` → `return i;`** (type error) |
| A20 | records / sealed (`Record`, `PermittedSubclasses` attributes) | yes | recovered | recovered | not tested (crashed on `pc`) | fails to compile (`classes cannot directly extend Record`) |
| A21 | static/instance init order (merged `<clinit>`/`<init>`) | merged | field initializers kept at fields | merges into one `static{}` with chained assignment | moves field initializers into constructors | kept |
| A22 | `synchronized` blocks (`monitorenter/exit` + `any` handler) | yes | recovered (moves a constant `return -1` inside, equivalent) | recovered | recovered | recovered |
| A23 | overload binding of `m((Object)null)`, `w((Object)null)` vs `w(String...)` | the exact descriptor | correct in all 16 `pa` probes | **SEM: `m((Object)null)` → `m(null)` binds `m(String)`; `w((Object)null)` → `w(null)` binds `w(String...)`** | `m((String)null)` → `m(null)` (still binds `m(String)`) | correct |
| A24 | compound assignment with implicit narrowing (`bs[i] += 200`, `fi *= 2.5`), `x = x - 1` vs `x--` | narrowing casts yes; spelling no (`x = x - 1` is `isub`, `x--` is `iinc`) | explicit casts (correct) | explicit casts | **SEM: `fi *= (int)2.5`** (multiplies by 2) | correct |
| A25 | float widening constant (`double d = 0.1f`) | value | `0.1F` kept | kept | writes `0.10000000149011612` and makes the local `final` (turns it into a constant variable; javac then folds `f + d`) | kept |
| A26 | JEP 513 flexible constructor body (statements + field store before `super(v)`) | yes (code before `invokespecial <init>`) | order preserved | preserved (real N5 case: `CompoundSelector`, `SimpleDragRenderer` in `organized/bajaui/fallback/`) | crashed | — |
| A27 | JEP 456 unnamed `_` (for-each, catch, record component) | no LVT entry for `_` | rendered as named `String var4`, `var5` | — | — | — |
| A28 | record pattern + guard in switch (javac 25 emits `CONSTANT_Dynamic` for primitive class labels) | yes | **pseudo-Java** `SwitchBootstraps.typeSwitch<"typeSwitch",…>` + `/* VF: Constant Dynamic */`, does not compile | does not compile | crashed | does not compile |
| A29 | anonymous class used as an expression (`new Object(){int z=5;}.z`) | yes | `((<unrepresentable>)(new Object(){…})).z` | does not compile | — | — |
| A30 | static call through an instance receiver (`m.sf()`, `make().sf()`) | receiver evaluated then popped | `sf()` for a local receiver (equivalent); `make(); return sf();` for a side-effecting one (correct) | `A29Misc.sf()` | kept | kept |

**Vineflower semantic defects reproduced synthetically (suite `pc`, class `Q`)** — each recompile binds or
computes differently from the original bytecode:

| ID | Source idiom | Vineflower 1.12 text | Effect |
|---|---|---|---|
| S1 | `sink("p", (Object) poll)` with `sink(Object,Object)` + `sink(Object,Runnable)` | `sink("p", this.poll)` | cast dropped → binds the `Runnable` overload (calls `run()`) |
| S2 | `sink("n", Long.valueOf(n))` with a `sink(Object,double)` overload | `sink("n", n)` | boxing dropped → binds `(Object,double)` |
| S3 | `va(new boolean[len])`, `va(new boolean[3])` for `va(boolean...)` | `va()` / `va()` | varargs collapse → array length ignored |
| S4 | `if (…) return Double.valueOf(d); return Float.valueOf(f);` | `return … ? d : f;` | ternary numeric promotion → returns a `Double` for the float branch |
| S5 | `a == Integer.valueOf(1000)` | `a == 1000` | reference comparison became value comparison |
| S6 | `try { throw …; } finally { return 3; }` | `finally { ; }` | the `return` is lost; the decompile throws where the original returns 3 |

Library context (the orchestrator's question; the corpus tree was produced with NO `-e`/`--add-external`):
re-decompiling the seven Part-B defect classes with all 452 classpath jars as `-e` externals fixed ONE
(`map.remove(Integer.valueOf(this.index))` returns) and left S1 (`pollService`), S2 (`"Message Count"`), S3
(`emptyBitString`), S4 (`parseNumber`) and the §116.5 D6 pattern-scope defect unchanged. CFR 0.152 with
`--extraclasspath` rendered all seven correctly (e.g. `out.prop((Object)"pollService", (Object)this.pollService)`,
`BBacnetBitString.make(new boolean[len])`). Vineflower's 1.12.0 release notes list "Fixed ambiguous vararg calls not
emitting casts, leading to wrong method being picked" and "Removed redundant primitive casts" `[CERT-web]`
(https://github.com/Vineflower/vineflower/releases/tag/1.12.0, accessed 2026-09-28) — S1-S3 show the 1.12.0 fix is
incomplete. No other survey source cited in the addendum is relied on here; every verdict above comes from this
session's recompile runs.

## 116.4 — Part B: the text differential over all 2,809 docSource-covered files (46 modules) `[CERT-hw]`

Members (fields, methods, constructors, initializers, nested types) were aligned by signature: 65,136 aligned
pairs, 556 original-only and 527 decompile-only members (renamed anonymous/lambda members, varargs-vs-array
signatures, bridges). Each aligned pair is assigned to the FIRST normalization stage at which the two token
streams become equal (cumulative stages, `normdiff.py` docstring):

| Stage that explains the WHOLE difference | Members | % | slotomatic `@Generated` | hand-written |
|---|---|---|---|---|
| S0 identical after comments/whitespace/imports | 25,465 | 39.1 | 7,588 | 17,877 |
| S1 annotations (SOURCE ones lost; CLASS/RUNTIME values folded) | 2,466 | 3.8 | 1,490 | 976 |
| S2 qualification (`this.`, `Outer.this.`, own/nested/package qualifiers, static-import form) | 18,457 | 28.3 | 7,437 | 11,020 |
| S3 `final`, generic arguments, redundant parentheses | 150 | 0.2 | 0 | 150 |
| S4 literal form (radix, suffix, char-as-int, escapes) | 869 | 1.3 | 151 | 718 |
| S5 compile-time constant inlining + folding (JLS 15.29 re-applied to the original) | 7,414 | 11.4 | 5,450 | 1,964 |
| S6 local / parameter / pattern / lambda names | 871 | 1.3 | 0 | 871 |
| S7 braces, `++`/`+= 1`/`= x + 1` spelling | 510 | 0.8 | 0 | 510 |
| residual structural | 8,934 | 13.7 | 587 | 8,347 |

Residual sub-tags (a member can carry several): control-flow / expression restructuring 4,661; local-variable
inlining or splitting 1,876; cast insertion/removal 1,615 (587 of the generated residuals are CFR's redundant
`(int)`/`(BValue)` casts in `bajaui` slotomatic code); literal/constant residue 1,538; array/varargs/allocation
shape 950; modifier spelling (implicit interface `public static final`, modifier order) 866; inherited-constant or
nested-type qualification 209; instanceof-pattern shape 27; nested/anonymous-class shape 20; other 179.

File-level: **1,148 of 2,809 files (40.9%) differ only cosmetically** (every aligned member reaches S0-S7 or a
modifier/qualification residue, and no unaligned member); 183 are identical after S0. Text alone cannot say
whether the other 1,661 differ in meaning, so every residual is referred to the bytecode oracle (§116.5).
Slotomatic code is recognisable in both trees by `@Generated` (CLASS retention, §116.2): the original carries the
`//region /*+ BEGIN BAJA AUTO GENERATED CODE +*/` banner and a `Generated … by Slot-o-Matic` comment
(`organized/docSource/control/niagara/control/BStringWritable.java:251-254`), which the decompile loses; what
remains is `@Generated` on every slot field/getter/setter and the constant-folded flags. The main slotomatic loss is
S5 (5,450 members: `Flags.X` names → ints).

## 116.5 — Part B: the bytecode oracle, and the 11 confirmed semantic differences in the corpus's own decompiled text `[CERT-hw]`

The corpus decompile of each docSource-covered class was recompiled against the shipped jars (files that fail
dropped iteratively): **2,657 of 2,809 top-level files compiled** (152 did not, **B116-G3**), yielding 3,436 class
files / 36,977 methods compared to the shipped bytecode. Methods: 31,611 identical, 64 identical after
local-slot renumbering, 2,023 without code, 3,279 different. Each differing method was classified by the multiset
of its EFFECT instructions (invokes, field ops, allocations, casts, constants, arithmetic/conversions, compares,
throws, monitors, returns, handler types; loads/stores/branches ignored as structure):

| Bytecode delta class | Methods | Verdict |
|---|---|---|
| effect sequence identical (only locals/branch layout differ) | 514 | structural, equivalent |
| effect multiset identical (block order differs) | 618 | structural, equivalent |
| only return-instruction count differs (javac duplicates returns per branch) | 1,873 | equivalent |
| + boolean-materialisation `iconst_0/1` shape | 27 | equivalent |
| `Objects.requireNonNull` added/removed (outer-instance and method-ref receiver checks) | 44 | equivalent except NPE timing on a null method-ref receiver |
| exception-table range splits (76 methods; handler-type SET identical in all 76, checked) | 76 | equivalent |
| `checkcast` only (redundant/erased casts) | 16 | equivalent |
| anonymous-class / lambda / `access$` numbering permutation (`BLonNetwork$2` ↔ `$3`, `lambda$…$0` ↔ `$1`, `access$500` ↔ `$600`) + 93 member/8 field set deltas of the same cause | 93 + 8 | equivalent at run time; synthetic NAMES differ (reflection/serialization-visible) |
| candidate semantic (`SEM?` rule tags) | 124 | inspected one by one at delta level: **11 confirmed**, 113 benign |

The 113 benign `SEM?` verdicts: field re-reads from splitting `a = b = x` or `f(e, x = y)` (single-threaded
equivalent), `x == true` vs `x` comparison shape, CFR allocation-type receivers (`ArrayList.add` vs `List.add`,
virtual dispatch identical), dropped `(BNrio16Module)` receiver casts on `invokevirtual` (same run-time target),
CFR's explicit outer-instance constructor parameters in `bajaui` inner classes, twr/finally `close()`/`pop()` copy
counts, explicit `(byte)`/`(char)` casts on constants, `index = index - 1` vs `index--`.

**Confirmed semantic differences** (the decompiled text, recompiled, binds or computes differently from the
shipped bytecode; each checked with `javap -c -p` on the shipped class):

| # | Module · class · method | docSource (= shipped) | Corpus decompile | What differs |
|---|---|---|---|---|
| D1 | bacnet · `BBacnetProxyExt` · `spy(SpyWriter)` | `out.prop("pollService", (Object) pollService)` (`organized/docSource/bacnet/niagara/bacnet/point/BBacnetProxyExt.java:1859`) | `out.prop("pollService", this.pollService)` (`organized/bacnet/vineflower/niagara/bacnet/point/BBacnetProxyExt.java:1102`) | shipped binds `SpyWriter.prop(Object,Object)`; the text binds `prop(Object,Runnable)` → would execute `BBacnetPoll.run()` while rendering the spy page (S1) |
| D2 | nrio · `BNrioNetwork` · `spy` | `out.prop("Message Count", Long.valueOf(this.getUnsolicitedMsgCount()))` (`organized/docSource/nrio/com/tridium/nrio/BNrioNetwork.java:1735`) | `out.prop("Message Count", this.getUnsolicitedMsgCount())` (`organized/nrio/vineflower/com/tridium/nrio/BNrioNetwork.java:1056`) + 7 more `prop` calls | `prop(Object,Object)` with `Long`/`Double`/`Float` boxes → `prop(Object,double)` (prints `12.0` instead of `12`) (S2) |
| D3 | nurio · `BNurioNetwork` · `spy` | same idiom, 3 `Long.valueOf` sites | boxing dropped | same rebinding as D2 (S2) |
| D4 | nrio · `BNrioTabularThermistorDialog$DeleteCmd` · `doInvoke` | `map.remove(Integer.valueOf(index))` (`organized/docSource/nrio/com/tridium/nrio/ui/BNrioTabularThermistorDialog.java:380`) | `map.remove(this.index)` (`organized/nrio/vineflower/com/tridium/nrio/ui/BNrioTabularThermistorDialog.java:326`) | `niagara.nre.util.Array.remove(Object)` (remove by value) → `remove(int)` (remove by index). The only case library context fixed |
| D5 | nurio · `BNurioTabularThermistorDialog$DeleteCmd` · `doInvoke` | `organized/docSource/nurio/com/tridium/nurio/ui/BNurioTabularThermistorDialog.java:379` | `organized/nurio/vineflower/com/tridium/nurio/ui/BNurioTabularThermistorDialog.java:327` | as D4 |
| D6 | driver · `BDevice` · `checkFatalFault` | local `BDeviceNetwork network = null;` assigned in the parent walk (`organized/docSource/driver/niagara/driver/BDevice.java:550-568`) | `network = null;` … `if (parent instanceof BDeviceNetwork network) break;` … `if (network == null)` (`organized/driver/vineflower/niagara/driver/BDevice.java:251-278`) | instanceof-pattern resugaring moved the local into pattern scope; the remaining `network` references bind the FIELD `BDevice.network` (`:70`) → the text always reports "Not under DeviceNetwork" (recompile: `putfield`/`getfield BDevice.network`) |
| D7 | driver · `BProxyExt` · `checkFatalFault` | local `BPointDeviceExt deviceExt = null;` (`organized/docSource/driver/niagara/driver/point/BProxyExt.java:636`) | `deviceExt = null;` + pattern variable (`organized/driver/vineflower/niagara/driver/point/BProxyExt.java:301`) | as D6, field `BProxyExt.deviceExt` |
| D8 | bacnet · `BBacnetBitString` · `emptyBitString(int)` | `return make(new boolean[len]);` (`organized/docSource/bacnet/niagara/bacnet/datatypes/BBacnetBitString.java:333`) | `return make();` (`organized/bacnet/vineflower/niagara/bacnet/datatypes/BBacnetBitString.java:204`) | the length is lost: shipped `iload_0; newarray boolean` vs recompiled `iconst_0; newarray` (S3) |
| D9 | lonworks · `LonFacetsUtil` · `parseNumber` | three `if` returns of `Long.valueOf`/`Double.valueOf`/`Float.valueOf` (`organized/docSource/lonworks/niagara/lonworks/londata/LonFacetsUtil.java:478-489`) | `return s instanceof BDouble ? …getDouble() : …getFloat();` (`organized/lonworks/vineflower/niagara/lonworks/londata/LonFacetsUtil.java:299-305`) | a `BFloat` input yields a `Double` instead of a `Float`; the adjacent `toBNumber` then casts `(Float)n` (S4) |
| D10 | kitControl · `BSequenceLinear` · `calculate` | `range / (float)(numOutputs)` (`organized/docSource/kitControl/com/tridium/kitControl/hvac/BSequenceLinear.java:287`) | `range / this.numOutputs` (`organized/kitControl/vineflower/com/tridium/kitControl/hvac/BSequenceLinear.java:139`) | `i2f;f2d` → `i2d`; value-identical for \|n\| < 2^24 (numOutputs is a small count) — precision cast lost, harmless in range |
| D11 | nre · `Base64` · `encode(byte[],int)` | `(int)((float)buf.length * 1.33)` (`organized/docSource/nre/niagara/nre/util/Base64.java:79`) | `(int)(buf.length * 1.33)` (`organized/_bin-ext/nre/vineflower/niagara/nre/util/Base64.java:87`) | as D10; only a capacity hint |

Measured rates: **9 behavior-changing methods (D1-D9) + 2 precision-edge methods (D10-D11) out of 36,977
recompiled methods (0.030%)**, in 11 of 3,436 class files. **62.8% of class files (2,157 / 3,436) recompile to
identical bytecode** (exact or slot-renumbering only) and **97.5% (3,349)** differ only in the benign classes above.
Every D-case is a Vineflower case; the 293 CFR-rendered `bajaui` files contributed no confirmed semantic
difference. The 152 non-recompiling files fail closed, and their top javac errors are the same defect family made
visible: `reference to do… is ambiguous` (55 in `baja`, 39 in `kitControl`), `variable … is already defined`
(bacnet local-merge), `cannot find symbol`.

## 116.6 — Addendum census over all 21,751 shipped class files `[CERT-hw]`

| Feature | Count | Consequence |
|---|---|---|
| preview class files (minor 65535) | 0 | none |
| `CONSTANT_Dynamic` (condy) in any constant pool | 0 | Vineflower's `--decompile-complex-constant-dynamic` question does not arise in N5 |
| IntelliJ `@NotNull` instrumentation (`$$$reportNull$$$` / "Argument for @NotNull parameter") | 0 | `--resugar-idea-notnull` irrelevant |
| `typeSwitch` indy sites / `enumSwitch` sites | 27 / 7 | pattern switches are real in N5 bytecode; 1 renders as pseudo-Java in the tree: `organized/platform/vineflower/com/tridium/platform/daemon/PlatformStationManager.java:69` (`SwitchBootstraps.typeSwitch<"typeSwitch",Version,Version,Version>(…)`) — **B116-G5** |
| classes referencing `java/lang/MatchException` (record deconstruction / exhaustive switch) | 10 | e.g. `organized/baja/extracted/niagara/timezone/DstRule.class`, `organized/bajaui/extracted/com/tridium/ui/layout/FlexBoxLayoutStrategy.class` |
| JEP 513 constructors: `putfield` of a non-synthetic field before `super/this` | 0 | — |
| JEP 513 constructors: `athrow` / local stores before `super/this` | 1 / 8 | real (docSource `organized/docSource/bajaui/niagara/ui/transfer/SimpleDragRenderer.java:52-63` has statements before `this(icons, text, owner)`); the CFR decompile keeps the order |
| `ObjectMethods` (record) indy / `Record` attributes / `PermittedSubclasses` | 126 / 45 / 3 | recoverable (§116.3 A20) |
| decompiled files with `$VF`/"Couldn't be decompiled" markers (whole tree) | 3 | T13 scope |
| `<unrepresentable>` in the tree | 0 | A29 has no N5 occurrence |

## 116.7 — Part C: the definitive verdict and the claim rules

1. **Faithful (bytecode-exact; decompiled text may be cited as-is):** method/field/type SETS and signatures,
   generic signatures, `throws` clauses, CLASS/RUNTIME annotations incl. all `@Niagara*` slot annotations (values
   folded to ints), string/number VALUES, lambda/method-ref targets, records/sealed/nests, local and parameter
   names (LVT is always present), enum/string/pattern switch structure (Vineflower), try/catch handler types. 85.5%
   of methods recompile identically.
2. **Unrecoverable but harmless (never claim anything about them from decompiled text; no semantics depend on
   them):** comments/javadoc, formatting, import form, `this.`/qualification, `final` on locals, redundant casts and
   parentheses, literal radix/escapes/char-vs-int spelling, `@Override`/`@SuppressWarnings` presence (Vineflower and
   the others INVENT `@Override`), ternary-vs-if and `&&`-vs-nested-if, labels, loop form, `i++` vs `i = i + 1`,
   string-concat operand order with `""`, StringBuilder-vs-`+`, varargs-vs-explicit-array call form, static
   initializer layout, member order, anonymous/lambda/`access$` numbering, JEP 456 `_`.
3. **Unrecoverable and claim-relevant (claims about these need docSource or javap, never the decompile):**
   (a) every [Block 115] §115.1 resugared idiom (instanceof patterns, `var`, text blocks); (b) compile-time
   constants — the decompile shows the folded value, so "uses a literal instead of constant X", "flag bits
   hard-coded", "dead constant" claims need docSource or `ldc` + JLS-inlining reasoning (7,414 members, 11.4%,
   explained only by constant inlining; slotomatic flags always); (c) dead code (`if (DEBUG)` bodies vanished —
   absence of a debug path in the decompile is not absence in the source); (d) SOURCE-retention intent
   (`@NoSlotomatic`, `@SuppressWarnings`); (e) which locals/statements exist (Vineflower inlines single-use locals
   and splits chained assignments), and exact synthetic names.
4. **Semantic risk (decompiled text can state WRONG behavior):** overload selection after a dropped cast or
   dropped boxing call (S1/S2, D1-D5), varargs collapse (S3, D8), ternary numeric promotion (S4, D9), boxed
   reference `==` (S5), `finally { return }` (S6), instanceof-pattern scope with a same-named field (D6, D7),
   precision casts `(float)` of ints (D10, D11); JADX and Procyon add their own (JADX value-matched symbol names for folded `ldc` values,
   a finally body emitted twice, `return i` for `""+i`; Procyon `*= (int)2.5`; all shown by bytecode recompile in §116.3); CFR renders `m((Object)null)` as `m(null)`.
   **Rule:** a claim whose truth depends on WHICH method a call binds to (overloads, `remove`, `prop`, varargs),
   on a boxed/primitive distinction, on a numeric conversion, on `finally` control flow, or on whether a name is a
   local or a field must be confirmed at bytecode level (`javap -c -p` on `organized/<mod>/extracted/…class`, the
   `invoke*` descriptor / `getfield` / conversion opcodes) or against docSource; quoting decompiled code to explain
   such behavior without that check is not `[CERT]`.

Tool choice: no decompiler is semantically clean on these probes; Vineflower is best at syntax and failed 6 of the
`pc` semantic probes; CFR failed the null-overload probe but got all seven Part-B defect classes right. T15's
round-trip grader (recompile, compare to the shipped bytecode, fall back per class) is therefore the only
mechanical guarantee.

## 116.x — Corrections to earlier blocks

- [Block 115] §115.1 (line 83: "only `docSource` originals or a non-resugaring decompiler (CFR) can settle
  those"): refine — CFR is not a semantic oracle either (§116.3 A23: `m((Object)null)` → `m(null)` rebinds); only
  docSource (now proven byte-identical, §116.1) or javap settle questions. The syntax statement itself stands.
- `docs/decompiler-bakeoff.md` / `tools/n5-decompile.sh` header ("best Java 17-25 feature fidelity"): true for
  syntax recovery, but the primary decompiler has the semantic defects of §116.5 in the committed tree; the
  orchestrator should add a pointer to this block (the doc is outside this writer's scope).
- The writer rule "Quoting decompiled code to explain BEHAVIOR is fine" (scratch `common.txt`, and wherever T11's
  `docs/writer-prompt.md` inherits it) needs the §116.7-4 exception.
- Task premise (T14 list): `@FunctionalInterface` is RUNTIME-retained and preserved (§116.2).

## 116.x — Connections

- [Block 115] §115.1-§115.3 (distinguishability matrix, constant inlining) — this block supplies the population
  counts (§116.4 S5) and the semantic layer. T15 (`tools/n5-fidelity.py`) should reuse §116.1's classpath recipe
  (LIB-INF + javafx) and §116.5's effect-multiset classifier; T16 (lint R9) should key on the D1-D11 classes.
- `docSource` recompile recipe and classpath: §116.1 header; [Block 90] / [Block 98] resugaring findings are
  consistent with §116.4 (27 instanceof-pattern residual members).

## 116.x — Child gaps opened

- **B116-G1** (high, requires-execution, investigable read-only otherwise) — run the §116.5 bytecode oracle over
  the ~12,100 top-level classes that have no docSource original (the T15 grader). `coverage-check:`
  `ls tools/n5-fidelity.py` and `organized/*/fidelity.json` (`tools/n5-fidelity.py` appeared untracked during this session from the T15 writer; its outputs were not read or relied on here).
  `measured-by:` per-class grade counts (`roundtrip-exact` / `compiles-mismatch` / `no-compile`) over
  `sum(recon.json class_count top-level)` = 14,894, with the effect-multiset classifier deciding benign vs `SEM?`.
- **B116-G2** (high, investigable) — audit corpus blocks that quote any D1-D11 method, or describe spy-page
  output, `Array.remove`, `BBacnetBitString.emptyBitString`, `LonFacetsUtil`, or `checkFatalFault` behavior, from
  the decompiled text. `coverage-check:` `rg -n 'checkFatalFault|emptyBitString|parseNumber|pollService|DeleteCmd|SpyWriter.prop' niagara5-block*.md`
  (not run this session). `measured-by:` number of block lines citing `organized/<mod>/vineflower/` for those
  eleven methods, each re-checked against docSource.
- **B116-G3** (medium, requires-execution) — classify the 152 decompiled docSource-covered files that do not
  recompile (bajaui 29, kitControl 34, baja 24, bacnet 15, others ≤ 6; list in scratch `recompile-dec/*.dropped`)
  by fixing only the decompiler-artifact compile errors (ambiguous calls, duplicate locals) and then running the
  §116.5 oracle; ambiguity errors are expected to hide more S1/S2 cases. `coverage-check:` §116.5 counts only
  2,657 compiled files. `measured-by:` confirmed-semantic methods per repaired file.
- **B116-G4** (medium, requires-execution) — measure whether a whole-tree Vineflower re-run with library
  context (`-e` for all 452 jars) changes the §116.5 rates; this session tested 10 classes (1 of 7 defects fixed).
  `coverage-check:` `tools/n5-decompile.sh` passes no `-e` (line 199). `measured-by:` confirmed-semantic method
  count over the same 36,977 methods, with and without `-e`.
- **B116-G5** (medium, investigable read-only) — review the 27 `typeSwitch` and 10 `MatchException` classes'
  decompiles for A28-style pseudo-Java or wrong guards (one confirmed: `PlatformStationManager.java:69`).
  `coverage-check:` `rg -l 'typeSwitch<' organized/*/vineflower` = 1 file this session. `measured-by:` per site,
  docSource or javap comparison of each case label and guard.
- **B116-G6** (low, investigable read-only) — independent second review of the 113 `SEM?` methods judged benign
  in §116.5 (scratch `classified.json`, `sem-rows.txt`). `coverage-check:` this block's own per-category
  reasoning only. `measured-by:` reviewer agreement count out of 113.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | docSource recompiles to identical instructions, exception tables and LineNumberTables for all 3,707 class files / 42,922 methods | [CERT-hw] | `organized/docSource/*/` vs `organized/*/extracted/` (nre: `organized/_bin-ext/nre/extracted/`); javac 25.0.4.1; scratch `b116/ds-vs-shipped.txt`, `cmpres/ds-*.json` |
| 2 | `@NiagaraProperty/Action/Enum/Topic/Slots` have no `@Retention` (CLASS); `@Generated` CLASS; `@NiagaraType` RUNTIME; `@NoSlotomatic` SOURCE | [CERT-hw] | `javap -v organized/_bin-ext/niagaraAnnotationProcessors/extracted/niagara/nre/annotations/*.class`; scratch `b116/nre-annot-retention.txt` |
| 3 | Annotation and slot flags are constant-folded (`Flags.SUMMARY \| Flags.TRANSIENT` → `10`) | [CERT] | `organized/docSource/control/niagara/control/BStringWritable.java:135`; `organized/control/vineflower/niagara/control/BStringWritable.java:42` |
| 4 | Every shipped class with local slots carries a LocalVariableTable; 21,751 classes all major 69 | [CERT-hw] | census over `organized/*/extracted` + `organized/_bin-ext/*/extracted`; scratch `b116/census.txt` |
| 5 | Part A matrix A1-A30 and S1-S6 (Vineflower/CFR/Procyon/JADX, recompiled and bytecode-diffed) | [CERT-hw] | decompilers `tools/decompilers/` (Vineflower sha256 `1dfcfe97…548b9d`); scratch `b116/partA{,2,3}/src,dec,rt`, `rt-*.json` |
| 6 | CFR `m((Object)null)` → `m(null)` recompiles to `invokestatic m(String)` | [CERT-hw] | `tools/decompilers/cfr-0.152.jar`; scratch `b116/partA/rt/cfr/pa/A23Overload.class` via `mdiff.py` |
| 7 | Text differential: 65,136 aligned members, stage counts of §116.4, 1,148/2,809 files cosmetic-only | [CERT-hw] | `organized/docSource/` vs `organized/*/vineflower|fallback/`; scratch `b116/normdiff.jsonl`, `ndstats.txt`, `subcats.txt` |
| 8 | Oracle: 2,657/2,809 files recompile; 36,977 methods; 31,611 identical; 124 `SEM?`; 11 confirmed | [CERT-hw] | recompiled vs `organized/*/extracted/`; scratch `b116/recompile-dec/`, `cmpres/dec-*.json`, `semdiff.jsonl`, `classified.json`, `metrics.txt` |
| 9 | D1: shipped `spy` calls `prop(Object,Object)` for `pollService`; decompile recompiles to `prop(Object,Runnable)` | [CERT-hw] | `javap -c -p` on `organized/bacnet/extracted/niagara/bacnet/point/BBacnetProxyExt.class`; `organized/bacnet/vineflower/niagara/bacnet/point/BBacnetProxyExt.java:1102` |
| 10 | D4: shipped `DeleteCmd.doInvoke` calls `Array.remove(Object)`, decompile binds `remove(int)` | [CERT-hw] | `javap -c -p` on `organized/nrio/extracted/com/tridium/nrio/ui/BNrioTabularThermistorDialog$DeleteCmd.class`; `organized/nrio/vineflower/com/tridium/nrio/ui/BNrioTabularThermistorDialog.java:326` |
| 11 | D6: decompiled `checkFatalFault` assigns and tests the field `network`, not a local | [CERT] | `organized/driver/vineflower/niagara/driver/BDevice.java:70,251-278` vs `organized/docSource/driver/niagara/driver/BDevice.java:550-568` |
| 12 | D8: `emptyBitString(len)` decompiles to `make()`; shipped bytecode `iload_0; newarray boolean` | [CERT-hw] | `javap -c -p` on `organized/bacnet/extracted/niagara/bacnet/datatypes/BBacnetBitString.class`; `organized/bacnet/vineflower/niagara/bacnet/datatypes/BBacnetBitString.java:204` |
| 13 | D9: `parseNumber` rendered as a double/float ternary | [CERT] | `organized/lonworks/vineflower/niagara/lonworks/londata/LonFacetsUtil.java:299-305` vs `organized/docSource/lonworks/niagara/lonworks/londata/LonFacetsUtil.java:478-489` |
| 14 | Library context (`-e`, 452 jars) fixes 1 of 7 defect classes; CFR with `--extraclasspath` renders all 7 correctly | [CERT-hw] | inputs copied from `organized/{bacnet,nrio,driver,lonworks}/extracted/`; scratch `b116/libctx/out-{noctx,ctx}`, `libctx/cfr` |
| 15 | Census: 0 preview, 0 condy, 0 IDEA NotNull; 27 typeSwitch, 7 enumSwitch, 10 MatchException classes; JEP 513 athrow 1 / local-store 8 ctors | [CERT-hw] | `organized/*/extracted`, `organized/_bin-ext/*/extracted`; scratch `b116/census.txt`, `census-examples.json` |
| 16 | Vineflower renders a raw `typeSwitch<…>` pseudo-call in `PlatformStationManager` | [CERT] | `organized/platform/vineflower/com/tridium/platform/daemon/PlatformStationManager.java:69` |
| 17 | Vineflower 1.12.0 release notes claim a fix for ambiguous vararg calls not emitting casts | [CERT-web] | https://github.com/Vineflower/vineflower/releases/tag/1.12.0, accessed 2026-09-28 |

**Tally**: 12 `[CERT-hw]` · 4 `[CERT]` · 1 `[CERT-web]` · 1 load-bearing `[INFER]` (§116.1, Tridium's javac update
line; only equal output is proven). [INFER]/[CERT*] ratio 1/17.

**Artifacts**: scratch `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b116/`
— tools `cf.py` (sha256 `432eb5fd…57a088`), `cmp.py` (`2082ae6f…d78`), `semdiff.py` (`6fe26d8e…51`),
`classify.py` (`8751be9b…be`), `normdiff.py` (`b41893ce…2d6`), `census.py` (`1af3bf4d…675`), `mdiff.py`,
`showm.py`, `consts.json` (108,250 compile-time constants from 106,663 classes incl. JDK `java.base/desktop/sql/
logging/xml/net.http/management/naming`); classpath `cp3.txt`; results named in the table. Durable inputs are all
under `organized/` and `tools/decompilers/`; the orchestrator may copy the small result files (`ds-vs-shipped.txt`,
`metrics.txt`, `classify.txt`, `census.txt`, the six scripts) into `evidence/b116/` (T10).
