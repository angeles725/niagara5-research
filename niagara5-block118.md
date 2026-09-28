# Block 118 — Logic-recovery method ladder for N5: what each instrument proves (line-mapped Vineflower, a LineNumberTable pattern discriminator, SootUp/Joern/bytecode-xref call graphs, sandboxed differential execution, an ASM trace agent, CodeQL vs Joern dataflow, and a krak2 round-trip of all 20,724 module classes)

> Research task **T18** of `odd/tasks/decompiler-fidelity-audit.md` (user requirement: "as faithful as possible;
> verify everything is right; try a thousand ways that can help us with the decompile and to know the logic").
> Evaluates seven method families (M1-M7) plus the orchestrator's addendum (forensic Vineflower flags, CFR git
> master, Fernflower upstream, Recaf/Bytecode Viewer, japicmp, jqwik + coverage, Maven Central SHA-1, ASM
> versions) ON REAL N5 CLASSES, and ranks them into a ladder: which instrument is ground truth for which
> question. Complements, does not duplicate: [Block 115] (idiom matrix), [Block 116] (loss catalogue), [Block
> 117] (extraction / native / third-party identity) and the T15 round-trip grader `tools/n5-fidelity.py` (not
> read or edited here; coordination by files only).
>
> **Fixed test set (10 classes, known answers from the corpus):** `niagara.io.ValueDocDecoder` (baja, docSource
> original exists, [Block 110]); `com.tridium.history.BRootHistoryFolder` + `com.tridium.history.fox.BFoxHistorySpace`
> (history, dynamic dispatch, [Block 112]); `com.tridium.nre.subscription.EntitlementApi` (bin/ext nre, 12
> `typeSwitch`, [Block 84] §84.2); `com.tridium.tagdictionary.tag.BQudtUnitTag` (resugaring, [Block 115] §115.2);
> `com.tridium.signing.profile.BSimpleSigningProfile` (CSR extension copy-through, [Block 99] §99.6 / [Block 107]);
> `com.tridium.rdb.jdbc.trans.BSqlType` + `niagara.rdb.ddl.Column` (DDL, [Block 110] / [Block 114]; Column has a
> docSource original); `niagara.ui.style.StyleUtils` (bajaui, the module whose whole-module Vineflower run timed
> out and fell back to CFR; docSource original exists); `niagara.control.BNumericWritable` (docSource-covered
> control class with a real guarded pattern switch). 29 class files including inner classes.
>
> **Does NOT cover:** running any Tridium launcher (refused, §118.6); the licensed NRE runtime (refused);
> regenerating the whole decompiled tree with the conservative variant (child gap B118-G2); the grader's per-class
> grades (T15). **Subject:** Niagara 5.0.0.28 beta, config-home modules `/mnt/c/ProgramData/Niagara/tridium/config/
> 5.0.0.28/modules` (247 jars) + `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext` (109 jars incl. subdirectories),
> read-only; N4 baseline `/mnt/c/PowerB/PowerB-4.15.3.28`. JDK 25.0.4.1 (Homebrew) for every Java step unless
> stated. Every execution of vendor bytecode ran in a `bwrap` sandbox (read-only `/`, no network, `--clearenv`,
> no `NIAGARA_*` variable, only the scratch dir writable — `evidence/b118/sandbox.sh`).
>
> **ALREADY-COVERED check (literal queries, 2026-09-28):** `rg -il` over `niagara5-block*.md docs/*.md` for
> `SootUp`, `Joern`, `CodeQL`, `jqwik`, `Xlog`, `dump_original_lines`, `bytecode-source-mapping`, `japicmp` → 0
> files each; `tools/check-coverage.py SootUp Joern CodeQL` → `VERDICT: clear`. `krak2` → only
> `docs/decompile-fidelity-report.md` (39-method normalizer cross-check, not a class round-trip) and
> `docs/decompiler-bakeoff.md`. `LineNumberTable` → [Block 115], [Block 116] §116.1 (docSource recompiles to
> identical LNTs — used here as the line oracle), `docs/decompile-fidelity-report.md`. `getNavChildren` → only
> [Block 51]/[Block 97] (unrelated). Third-party Maven identity → **ALREADY-COVERED by [Block 117] §117.x**
> (not re-derived; §118.9 only corroborates).

---

## 118.1 — M1 ADOPTED as the second, citation-grade view: Vineflower 1.12.0 with resugaring OFF and ORIGINAL source line numbers mapped (`--bytecode-source-mapping` + the hidden `--__dump_original_lines__`) — 669/669 mapped lines verified against docSource originals, and it removes [Block 116]'s D6/D7 pattern-scope defects `[CERT-hw]`

**Option set, read from the jar itself.** `java -jar vineflower-1.12.0.jar --help` lists the toggles; the
constant pool of `org/jetbrains/java/decompiler/main/extern/IFernflowerPreferences.class` (`javap -constants`)
adds one the help does not print: `DUMP_ORIGINAL_LINES = "__dump_original_lines__"`. The conservative +
line-mapped set (`evidence/b118/conservative-flags.txt`):

`--pattern-matching=false --decompile-switch-expressions=false --ternary-in-if=false --prettify-ifs=false
--inline-simple-lambdas=false --bytecode-source-mapping=true --__dump_original_lines__=true`

There is no `var` or text-block toggle because Vineflower 1.12.0 emits neither from ordinary code: 0 files
with `"""` in the whole decompiled tree, and `var` appears only for intersection-typed locals (17 files, e.g.
`var serialService = (BISerialService & BComponent)Sys.getService(...)` at
`organized/platCcn/vineflower/com/tridium/platCcn/BCcnPlatformServiceAtlas.java:142`), where Java offers no
denotable type `[CERT-hw]`.

**CLI trap found on the way (silent option loss).** Any option placed AFTER an `-e=<lib>` argument is
ignored without a warning: `--pattern-matching=false -e=control.jar` renders BQudtUnitTag classically,
`-e=control.jar --pattern-matching=false` renders `instanceof BNumericPoint np` `[CERT-hw]` (scratch `x2/`
vs `x3/`). Every variant below puts all `--options` before `-e`.

**BQudtUnitTag, classic and line-mapped** (`evidence/b118/BQudtUnitTag.cons-linemapped.java`):

```java
   public Tag getTag(Entity entity) {
      if (entity instanceof BNumericPoint) {// 89
         BNumericPoint np = (BNumericPoint)entity;// 91
         BFacets df = np.getFacets();// 92
```

The `// N` comments are the class file's own LineNumberTable (`javap -c -l`: `line 89: 0`, `line 91: 7`,
`line 92: 12` …), i.e. the line numbers of Tridium's source file.

**Line-map accuracy, measured against docSource.** For the four test classes with a docSource original
(ValueDocDecoder, Column, StyleUtils, BNumericWritable), every decompiled line carrying `// N` was checked for a
shared identifier with original lines N..N+2: **669/669 hits (100%)**; the same check with every N shifted by
+7 scores 226/669 (33.8%), so the check discriminates (`evidence/b118/linecheck.py`, `linecheck.out`,
`linecheck-shift7.out`) `[CERT-hw]`. [Block 116] §116.1 independently proved docSource recompiles to identical
LineNumberTables for all 42,922 methods, so these line numbers are the original file's.

**What it recovers that default Vineflower does not.**

| Effect | Default | Conservative + line-mapped | Evidence |
|---|---|---|---|
| instanceof-pattern renders on the test set | 7 | 0 | per-class grep, `ts/*/vf-{default,cons}` |
| arrow/switch-expression renders | 12 | 0 | same |
| [Block 116] D6 `BDevice.checkFatalFault` (pattern scope captures the local `network`, text then reads the FIELD) | defect present | **absent** — `BDeviceNetwork network = null;// 550` … `network = (BDeviceNetwork)parent;// 564` … `if (network == null) {// 571`, matching `organized/docSource/driver/niagara/driver/BDevice.java:550-571` | `evidence/b118/BDevice.cons-linemapped.java` |
| [Block 116] D7 `BProxyExt` `deviceExt` | defect present | **absent** (`BPointDeviceExt deviceExt = null;// 636`, cf. `organized/docSource/driver/niagara/driver/point/BProxyExt.java:636`) | scratch `m1/d6/cons/` |
| [Block 116] D9 `LonFacetsUtil.parseNumber` (two returns merged into a numeric-promoting ternary) | defect present | **still present** — but visible: the merged line carries THREE original lines, `// 484 486 488`, cf. `organized/docSource/lonworks/niagara/lonworks/londata/LonFacetsUtil.java:478-489` | scratch `m1/d6/cons/` |
| Citation coordinates | decompiled-file lines | original-source lines, joinable with SootUp/Joern/`n5-bytecode-xref` output and docSource | this section |

**Where the default is MORE faithful.** Real pattern switches: BNumericWritable's docSource original is a
guarded pattern switch (`organized/docSource/control/niagara/control/BNumericWritable.java:1088-1093`, `case
Action a when set.equals(a) -> …`); default Vineflower reproduces it, the conservative view prints the desugared
`SwitchBootstraps.typeSwitch<…>` state machine (not compilable Java, but bytecode-shaped, still line-mapped:
`Action a = var4;// 1090`). So the conservative view is a SECOND view for syntax-neutral, line-cited reading,
not a replacement.

**Forensic flag set (addendum).** All thirteen names the addendum proposed exist in 1.12.0's `--help`
(`remove-synthetic`, `remove-bridge`, `hide-default-constructor`, `prettify-ifs`, `keep-literals`,
`hide-empty-super`, `decompile-complex-constant-dynamic`, `ignore-invalid-bytecode`, `decompiler-comments`,
`dump-bytecode-on-error`, `use-lvt-names`, `use-method-parameters`, `rename-members`) plus `--include-runtime=<JDK
25 home>` (`evidence/b118/run-forensic.sh`). On the test set it adds only structure the compiler generated:
default constructors (4 classes), explicit `super()` (16 sites), the synthetic enum `$values()` (EntitlementApi),
and un-prettified `if/else` nesting; `keep-literals` changed nothing (no NaN/π literals) `[CERT-hw]`.

**Cost:** one extra Vineflower pass (same engine, ≈ default time). **Recommendation: adopt** as the
citation-grade second variant, generated per module next to `vineflower/` (B118-G2 measures it corpus-wide).

## 118.2 — M7a NEW INSTRUMENT, ADOPTED: the LineNumberTable decides most instanceof-pattern-vs-classic questions that [Block 115] §115.1 declared undecidable — validated on the docSource originals: 326/326 classic casts detected, 1 of 93 patterns misflagged `[CERT-hw]`

**Why it works.** The instruction stream is identical (§115.1 is right about that), but javac emits a
LineNumberTable entry at the start of every statement. A classic `T x = (T)e;` written on its own line gets a
line entry starting between the `instanceof` and the `checkcast`; a pattern binding's `checkcast` belongs to the
`if` line. javac 25 experiment (`-g --release 25`, scratch `m1/lnt/`): pattern → entries `4:0, 6:12`; classic on
its own line → `4:0, 6:7` (a new entry exactly at the cast's `aload`); classic on the SAME line as the `if` →
`4:0, 5:12`, indistinguishable from a pattern; a pattern whose type token is on a later line of a multi-line
condition also produces an entry at the cast (`line 6: 7`) — the known false-positive shape `[CERT-hw]`.

**Validation against Tridium's own originals** (`evidence/b118/lnt_pattern_validate.py`, `.out`): every
`instanceof T … checkcast T; astore` site in the shipped bytecode of the classes behind the 2,868 docSource `.java` files, classified by
the bytecode rule, compared with the original source line:

| docSource truth \ bytecode verdict | classic-separate-line | pattern-or-same-line |
|---|---|---|
| classic cast | **326** | 0 |
| pattern (`instanceof T name`) | 1 (`organized/docSource/bajaui/niagara/ui/style/StyleUtils.java:206-209`, multi-line condition) | **92** |
| unresolvable text | 2 | 2 |

Tridium never wrote a same-line classic cast in this sample, so on Tridium code "pattern-or-same-line" means
"pattern" with 92/92 = 100% observed precision and "classic-separate-line" means classic with 326/327 = 99.7%
precision. It is a measured heuristic, not a proof; say so when citing it.

**BQudtUnitTag decided from the N5 class alone.** Its `getTag` has `line 89: 0` (instanceof) and `line 91: 7`
(a new statement at the cast) → `classic-separate-line`. Independently, the N4-4.15.3.28 class (major 52, where
patterns cannot exist) has the IDENTICAL instruction stream AND the identical LineNumberTable after
normalizing the `javax.baja.`→`niagara.` rename and constant-pool indices (both normalized dumps sha256
`009753a0412c88c1…`, `evidence/b118/BQudtUnitTag.getTag.{n4-4.15,n5}.norm.txt`) `[CERT-hw]` — same source lines,
same code: the N5 source is classic, closing [Block 115] §115.2 from two directions.

**N5-wide census from bytecode** (`tools/n5-bytecode-xref.py casts` logic; `evidence/b118/casts_census.py`,
`casts-census.out`; 21,504 class files, all major 69, 0 parse errors): **2,332** instanceof→cast→astore sites,
**1,918 classic-separate-line (82.2%)** and **414 pattern-or-same-line (17.8%)**. The decompiled tree renders
**1,912** `instanceof T name` patterns (`rg -c 'instanceof [A-Z][A-Za-z0-9_.<>]* [a-z][A-Za-z0-9_]*'` over every
`vineflower/` dir) — about 4.6x the bytecode upper bound, the quantitative size of the resugaring bias
[Block 115] described qualitatively `[CERT-hw]`.

**Other idioms, same trick.** `var`: the LocalVariableTable records the DECLARED type, so `List<String> l = new
ArrayList<>()` (LVT `Ljava/util/List;`) differs from `var l = new ArrayList<String>()` (LVT
`Ljava/util/ArrayList;`), and an anonymous-class-typed local (`LV$1;`) can only have been `var`; when the declared
type equals the initializer's type the question stays undecidable. Text block vs concatenation: identical `ldc`
and no line signal — undecidable (scratch `m1/lnt/V.java`) `[CERT-hw]`.

**Recommendation: adopt**, as `tools/n5-bytecode-xref.py casts <class>` (§118.3), for every syntax-adoption
question without a docSource original.

## 118.3 — M2 ADOPTED: bytecode-level call graphs work on class-file 69 — SootUp 3.0.1 and Joern jimple2cpg (Soot 4.7.1) both resolve the BFoxHistorySpace→BRootHistoryFolder dispatch mechanically and find 5 static callers where the source-text call graph finds 0; the kit's SootUp 2.0.0 exporter fails silently on N5 `[CERT-hw]`

**Java 25 support, tested.** SootUp 3.0.1 (ASM 9.10.1) loads the N5 jars: over all 247 module jars + the 73
top-level bin/ext jars it built 262,982 Jimple bodies from 31,688 classes with **0 body failures** (86.7 s, 12 GB
heap) (`evidence/b118/sootup-history.out`). Joern v4.0.639 `jimple2cpg` (Soot 4.7.1, ASM 9.9.1) turned
`history.jar` into a CPG in 6.9 s: 376 internal type declarations for 373 `.class` entries, 3,842 methods
(`evidence/b118/joern-history-callers.out`). OPAL was not provisioned (last GitHub release 7.0.0, 2025-12-16; two
independent Soot-family engines already answered). **The kit's `toolbelt/jvm-callgraph.sh` (SootUp 2.0.0, its
bundled ASM tops out at `V24 = 68`) is unusable on N5 and does not say so:** the same one-class program compiled
with `--release 21`/`24` yields 1 path; with `--release 25` it exits 2 with `jvm-callgraph: no application main
method found; provide --entry or --entry-contains` (`evidence/b118/kit-jvm-callgraph-release25.log`,
`kit-jvm-callgraph-Hello.java`), and on `history.jar` it answers `entry selector matched no methods` — a tool
failure presented as a zero (B118-G5) `[CERT-hw]`.

**Dispatch resolved mechanically** (`evidence/b118/SootUpProbe.java`): the three BFoxHistorySpace call sites are
`invokevirtual com/tridium/history/BRootHistoryFolder.getPermissions:(Lniagara/sys/Context;)…` (`javap -c -p`),
the whole-install subtype census of `BRootHistoryFolder` is empty, and both CHA and RTA resolve `navEvent →
BRootHistoryFolder.getPermissions(Context)` as the only target — [Block 112] §112.1's reading now rests on
instruments, not on reading the override by eye `[CERT-hw]`.

**"Who calls X" — three bytecode instruments agree, the text index does not.**

| Instrument | Callers of `BRootHistoryFolder.getPermissions(Context)` | Lines reported |
|---|---|---|
| `module-navigator callers BRootHistoryFolder getPermissions` (Vineflower-text index) | **0** ("No callers found") | — |
| SootUp 3.0.1 whole-view Jimple scan | 5 exact-owner + 42 via `niagara.security.BIProtected` | 293, 356, 399 (navEvent); 194, 205 (BHistorySpace.getNavChildren) |
| Joern `jimple2cpg` `cpg.call` / `.caller` | 5 sites, 2 callers | same five |
| `tools/n5-bytecode-xref.py callers … [--cha]` (new, §118.3 tool note) | 5 exact + 42 supertype-owner | same five (`evidence/b118/xref-brootfolder-getpermissions-cha.json`) |

The reported lines are ORIGINAL source lines (the docSource original has the two getNavChildren calls at
`organized/docSource/history/niagara/history/BHistorySpace.java:194` and `:205`), while the decompiled file
shows them at `organized/history/vineflower/niagara/history/BHistorySpace.java:116` and `:124` — the line-mapped
view of §118.1 is what joins the two coordinate systems `[CERT-hw]`.

**Tool note — `tools/n5-bytecode-xref.py` (created, strict TDD).** Pure-stdlib class-file parser (constant pool,
Code, LineNumberTable; `tableswitch`/`lookupswitch`/`wide` handled) over `organized/*/extracted`, with `callers
[--cha]`, `subtypes`, `overriders`, `casts`. Tests first: `tools/tests/test_n5_bytecode_xref.py` (12 tests:
javac-25 fixtures for exact vs supertype-owner sites, transitive subtypes, switch/wide/long-constant parsing,
an invoke at an LNT start pc, the three cast shapes, CLI JSON, unknown class = exit 2 not a zero, a real-corpus
smoke test for the five sites). Observed RED (module missing) → GREEN 12/12; two hand mutants (`<=`→`<` in the
line lookup, inverted cast verdict) each turn a test red (the first survived until the LNT-start-pc test was
added). Full corpus: 21,504 classes, 0 parse errors, ≈12 s. It complements `module-navigator` (text search) and
does not replace SootUp/Joern for reachability or dataflow.

**Cost:** xref 12 s/no install; SootUp 105 s + Maven; Joern 1.86 GB download, ≈7-13 s per jar.
**Recommendation: adopt** xref for who-calls/subtypes/casts; SootUp (with the JDK runtime input location, see
§118.6) for CHA/RTA reachability; Joern for bytecode dataflow (§118.7).

## 118.4 — B107/B112 call-site census ADVANCED: two more `getPermissions(null)` sites exist, in `BHistorySpace.getNavChildren()` (dispatch: `BRootHistoryFolder.getPermissions(Context)`), and on a server-side space they take the `BPermissions.all` branch `[CERT]`+`[CERT-hw]`

dispatch: `com.tridium.history.BRootHistoryFolder.getPermissions(Context)` — resolved by SootUp CHA+RTA, Joern
and `n5-bytecode-xref` (0 subtypes install-wide, §118.3).

[Block 107] §107.3 and [Block 112] §112.1 examined the three sites in `BFoxHistorySpace`. The bytecode census
adds two in the base class `niagara.history.BHistorySpace.getNavChildren()`: `new BRootHistoryFolder(this, new
String[]{groupNames[i]}, this)` then `rootFolder.getPermissions(null)` (dispatch: `BRootHistoryFolder.getPermissions(Context)`) per history group, and the same for the
default root (`organized/docSource/history/niagara/history/BHistorySpace.java:193-205`) `[CERT]`. The override
(`organized/history/vineflower/com/tridium/history/BRootHistoryFolder.java:42-58`) round-trips real permissions
only when `this.space instanceof BFoxHistorySpace`; otherwise it returns `cx != null && cx.getUser() != null ?
cx.getUser().getPermissionsFor(this) : BPermissions.all` `[CERT]`. `BFoxHistorySpace` does not override
`getNavChildren` (no declaration in `organized/history/vineflower/com/tridium/history/fox/BFoxHistorySpace.java`),
and the station-side database `BHistoryDatabase extends BHistorySpace`
(`organized/history/vineflower/niagara/history/db/BHistoryDatabase.java:37`) does not either — so on a
station-side space every group folder passes the `hasOperatorRead()` filter: the filter in
`getNavChildren()` is a no-op there `[CERT]`. Whether that unfiltered listing reaches a remote session without a
later per-user filter is NOT established here: `n5-bytecode-xref callers niagara.history.BHistorySpace
getNavChildren --cha` lists 66 candidate call sites (2 exact, 57 via `BINavNode`, 4 via `BSpace`, 3 via
`BNavContainer`; `evidence/b118/xref-bhistoryspace-getnavchildren-cha.json`) that need triage (B118-G1).
Defensive reading: a code-review finding on the nav-listing contract (a Context-free API evaluating a
Context-sensitive permission as `all`); fix direction — pass the session context into the listing or filter at
the serving layer; [Block 112] §112.1's record-level re-check remains the relevant mitigation for record
content.

## 118.5 — M3 ADOPTED-FOR pure, Baja-free logic: differential execution of the ORIGINAL bytecode vs the Vineflower-recompiled and docSource-recompiled builds agrees on 3,026 fuzzed XML cases and 20,000 jqwik tries, with a killed mutant and measured coverage; 9,266 of 14,307 classes cannot initialise offline because `niagara.sys.BObject`'s static init requires `niagara.home` (typed wall `refused`) `[CERT-hw]`

**What can execute offline** (`evidence/b118/InitProbe.java`, `census-summary.txt`; sandboxed, one JVM per
module, classpath = all 247 module jars + all 109 bin/ext jars): of 14,307 top-level classes in 246 modules,
**4,813 initialise (33.6%)**, 9,494 do not — 9,266 through the NRE chain and 228 because a third-party
`LIB-INF` class (biweekly, json-path, paho, qpid-proton, velocity) is not on the probe classpath. The chain, in
order: first `com.tridium.sys.Nre.<clinit>` needs `com.tridium.securityBridge.IPermissionBridge` (the
`bin/ext/securityBridge/securityBridge.jar` the launcher adds via `-Xbootclasspath/a:`, [Block 87] §87.4); with it
present, `NoSuchElementException: niagara.home not found` at
`com.tridium.nre.security.permissions.PermissionFactory.lambda$fileMapper$0(PermissionFactory.java:88)` ←
`NiagaraPermission.isGrantedTo(NiagaraPermission.java:60)` ← `niagara.sys.BObject.<clinit>`
(`evidence/b118/init-probe2.out`). Every `B*` class (BQudtUnitTag, BSqlType, BNumericWritable,
BSimpleSigningProfile, the history classes) dies there; ValueDocDecoder, Column, StyleUtils and EntitlementApi
initialise but their interesting methods construct or call `B*` objects. **Wall, typed `refused`:** supplying a
`niagara.home` is the §12 runtime-root crossing and the next frames are Tridium's permission/licensing layer,
which the hard limits forbid emulating — not attempted.

**Differential harness on a pure class family: `niagara.xml` (XParser, XElem, XWriter …) from nre.jar**
(sha256 `d563a334e02ef739…`). Three arms: `orig` (nre.jar bytecode), `vf` (the corpus's Vineflower sources
recompiled with javac 25; `XInputStreamReader.java` does not compile — duplicate local `c1` in a switch — so that
one class is the original bytecode, copied into the unsealed directory because nre.jar seals `niagara.xml`), `ds`
(docSource originals recompiled).

- Fixed corpus (`evidence/b118/XpDiff.java`, `xpdiff-summary.txt`): 13 hand-written bog/namespace/CDATA/entity/
  BOM/malformed documents + 1,500 seeded mutants (seed 118) × 2 whitespace modes = 3,026 cases (478 parses,
  2,548 exceptions): **0 differences between any two arms** (identical body sha256 `9ee04f2052ce7e33…`).
- Property-based (`evidence/b118/XmlArmsProperties.java`, `jqwik-run.out`): the three arms in isolated class
  loaders inside one JVM; `XWriter.safe` escaping (5,000 tries), escape→parse round-trip (5,000), raw parse of
  generated XML-ish strings incl. `\u0000` and a lone surrogate (10,000); jqwik edge cases mixed in; **3/3
  properties green**.
- Bite: a one-character mutant of the `vf` arm (`&gt;` → `&#62;` in `XWriter`) is caught and shrunk to the
  one-character input `>` (`evidence/b118/jqwik-run-mutant.out`).
- Coverage of the ORIGINAL bytecode by those runs (JaCoCo 0.8.15 agent, `evidence/b118/cov-orig.csv`): XParser
  263/407 lines, 138/238 branches; the package 429/1,654 lines (25.9%), 202/874 branches (23.1%). Agreement is
  evidence only for the covered lines.
- japicmp 0.26.2 (`-a private`): orig vs vf and orig vs ds report `No changes` (`evidence/b118/japicmp-vf.txt`);
  it flags an added method in a control jar but NOT the `&gt;` behaviour mutant — member-set equivalence, not
  behavioural equivalence.

**Recommendation: adopt-for** station-independent utility logic (parsers, encoders, math) with jqwik +
coverage; not usable for Baja components without a licensed runtime.

## 118.6 — M4: Tridium launchers are `refused` (they rewrite the config home and hit the `tridium:nre` license gate); an ASM trace agent inside our own sandboxed JVM yields an exact dynamic call trace that validates the static graph: CHA covers 146/146 executed edges once the JDK is in the view `[CERT-hw]`

**Launchers, not run.** [Block 17] §17.2 already recorded that `n5mig.exe -help` "boots registry (8600
types)" before `NLicenseManager.checkFeature("tridium:nre")` rejects it, and `station.exe -help` fails the same
way. Booting the registry writes `…/config/5.0.0.28/registry/registry.db` and `jar-cache/` (both present with
2026-09-2x mtimes). Running any launcher therefore violates the read-only-install limit and §12 clause (a), and the
useful part of the trace ends at the license gate: typed **`refused`**, no attempt.

**What works instead** (`evidence/b118/TraceAgent.java`, ASM 9.10.1, jar sha256 `8007e58e3b08ac86…`): a
`-javaagent` that instruments every `niagara/*` method entry and records `caller → callee` via StackWalker, run
over the §118.5 `orig` XParser workload, plus `-Xlog:class+load`. Two instrumentation bugs surfaced and were fixed
before any result was used (StackWalker needs `RETAIN_CLASS_REFERENCE`; `AdviceAdapter` needs
`ClassReader.EXPAND_FRAMES`); the first bug had CHANGED the program's output, which is why the traced run's
output is diffed against the untraced run (identical after the fix). Result: 146 distinct dynamic edges, 90 methods
entered (`evidence/b118/trace-orig.txt`). Against SootUp's static graph from `XpDiff.main`
(`evidence/b118/soundness-jrt.txt`): without the JDK in the view CHA covers 144/146 (misses
`XWriter.safe(Writer,int,boolean) → XWriter.write(…)`, a dispatch through `java.io.Writer`); with
`DefaultRuntimeAnalysisInputLocation` CHA covers **146/146**; RTA 145/146 `[CERT-hw]`.

**Recommendation: adopt-for** validating static call graphs on offline-executable code (dynamic ⊆ static is the
soundness check); never a Tridium-launcher trace.

## 118.7 — M5: dataflow on the CSR → issued-certificate path — Joern on BYTECODE finds all four `csr.getExtensions()` → `addExtension` flows; CodeQL 2.27.1 buildless on decompiled source misses exactly the unguarded one, traced-javac mode finds it `[CERT-hw]`

Question ([Block 99] §99.6, [Block 107] §107.1): which CSR-supplied extensions reach
`NSigningParameters.addExtension`, and under which guard, in `BSimpleSigningProfile.getSigningParameters`.

| Instrument | Input | Flows found | Guard attribution |
|---|---|---|---|
| CodeQL 2.27.1, `--build-mode=none` | Vineflower sources of signingService + nre `com/tridium/crypto` (148 files) | **3/4** — decompiled lines 253, 257, 261; the unconditional `else` at 264 is missing although `DataFlow::localFlow` holds there | `isKeyUsageExtensionValid` / `isExtendedKeyUsageExtensionValid` / `isBasicConstraintsExtensionValid` (Guards library) |
| CodeQL 2.27.1, `--build-mode=manual` (javac 25 with every module jar on the classpath; 71 compile errors elsewhere tolerated) | signingService Vineflower sources | **4/4** | same three + 264 `UNGUARDED` |
| Joern v4.0.639 `jimple2cpg` + `reachableByFlows` | `signingService.jar` bytecode | **4/4** | n/a (paths only), ORIGINAL lines 420, 427, 434, 439 |

Line-join through §118.1's view: original 420/427/434 are the three guarded copies and **439 is the unguarded
`else`** (`// 439` in the conservative output, `evidence/b118/BSimpleSigningProfile.cons-linemapped.java`). The array for-each needed an explicit additional flow step in CodeQL
(`evidence/b118/CsrExtFlow.ql`); results `codeql-csr-flow-{buildless,manual}.csv`, `joern-csr-flow.{sc,out}`.
Java 25 sources are accepted by the CodeQL extractor (javac 25 on PATH) `[CERT-hw]`. None of this changes
[Block 99]'s finding (the BasicConstraints branch is guarded by a check that is constant-true for non-CA
profiles); it shows which instruments can be trusted to FIND such a path.

**Recommendation: adopt-for** — Joern on bytecode as the primary dataflow instrument; CodeQL only in traced mode
with the real classpath; a buildless CodeQL "no flow" is never an absence proof (B118-G3).

## 118.8 — M6 CLOSED as ground truth: krak2 `dis -r` → `asm` reproduces every one of the 20,724 config-home module classes byte-for-byte `[CERT-hw]`

`evidence/b118/krak2-jar-roundtrip.sh` disassembles each jar in round-trip mode, reassembles the concatenated
`.j`, and `cmp`s every class with its jar entry (`krak2-roundtrip.tsv`):

| Set | Classes | Byte-identical | Differ | Not re-emitted |
|---|---|---|---|---|
| 247 config-home module jars | 20,724 | **20,724** | 0 | 0 |
| 109 bin/ext jars (third-party + Tridium) | 11,294 | 11,257 | 0 | 37 (all `META-INF/versions/*` multi-release entries whose names collide in the harness's single concatenated `.j` — a harness limit) |

On the 29 test-set class files, krak2's non-round-trip mode (`dis` without `-r`) reassembles to DIFFERENT bytes
for 29/29 (constant-pool order is not preserved), so only `-r` output is ground truth `[CERT-hw]`. Cost: ≈0.2-2 s
per jar. **Recommendation: adopt** as the lossless textual form of a class (every attribute, every constant),
the tie-breaker when javap, a decompiler and the grader disagree.

## 118.9 — M7 other instruments: CFR git master, Fernflower upstream, Recaf/Bytecode Viewer, jdeps, ASM versions, Maven Central `[CERT-hw]`

- **CFR git master** (`leibnitz27/cfr` @ `c4145259dfcd8ad3e99004e4d9ecb0aed55dcc5a`, 2026-06-04; built with JDK 8 per
  its README, `cfr-0.153-SNAPSHOT.jar` sha256 `e49a52a63eee1a8d…`). Versus 0.152 on the test set: it now RESUGARS
  instanceof patterns (BQudtUnitTag → `entity instanceof BNumericPoint np`, the provably classic site of §118.2),
  and renders BNumericWritable's pattern switch as `case null, default -> null` while the bytecode begins with
  `Objects.requireNonNull` before the `typeSwitch` (a null argument throws in Tridium's code and returns `null`
  in CFR master's text — a semantic defect). CFR 0.152, conversely, renders the docSource-proven pattern at
  `organized/docSource/bajaui/niagara/ui/style/StyleUtils.java:209` as a classic cast. **Neither CFR is a
  syntax oracle.** Adopt master only as an extra structural opinion.
- **Fernflower upstream** (`JetBrains/fernflower` @ `5ab777bf97c68d57835944cc1003ca1e1fa56b73`, 2026-09-24, `./gradlew
  jar` JDK 21, sha256 `b8c4dc8b1c2f7584…`): runs headless, 0 "couldn't be decompiled" markers on the test set,
  resugars BQudtUnitTag like Vineflower, and renders the BNumericWritable pattern switch as a desugared loop with
  an explicit `Objects.requireNonNull`. Vineflower is its maintained fork; no unique recovery observed. Reject as
  primary; keep as a fourth opinion.
- **Recompilation of each engine's output** (javac 25, all jars on the classpath): see the table at the end of
  this section.
- **Recaf 4 / Bytecode Viewer:** not evaluated — GUI-first tools whose decompilation backends are the same
  engines measured here (Vineflower/CFR/Procyon/Fernflower); no headless recovery path beyond those engines was
  identified, so the marginal evidence value is nil.
- **ASM (or class-reader) versions of every tool run** (class-file 69 needs ASM ≥ 9.8): Vineflower, CFR (both),
  Procyon, Fernflower and krak2 use their own class readers (no `org/objectweb/asm/ClassReader` in their jars);
  JADX 1.5.6 bundles ASM with `V27 = 71`; JaCoCo 0.8.15 shades ASM with `V27 = 71`; SootUp 3.0.1 uses ASM 9.10.1;
  Joern's jimple2cpg ASM 9.9.1; japicmp uses javassist 3.30.2-GA (read the 69 classes without error); the kit's
  SootUp 2.0.0 build tops out at `V24 = 68` (§118.3) `[CERT-hw]`.
- **Maven Central SHA-1 (addendum): ALREADY-COVERED by [Block 117] §117.x.** Corroboration only: the 109 bin/ext
  jars give 0 whole-file SHA-1 hits (52 NOT-FOUND, 57 search-API timeouts), expected because Tridium re-signs them
  (`META-INF/NIAGARA4.SF`/`.RSA` + a rewritten `MANIFEST.MF`); per-entry comparison of `bin/ext/asm-9.10.1.jar`
  with Central's `asm-9.10.1.jar` gives 39/39 identical classes (`evidence/b118/entry-cmp-asm.txt`).

**Recompilation of each engine's output** (javac 25.0.4.1, `-proc:none`, every module + bin/ext jar and the class's own original inner classes on the classpath; cells = javac error count; `evidence/b118/recompile-by-engine.tsv`) `[CERT-hw]`:

| Class | vf-default | vf-cons | vf-forensic | cfr-152 | cfr-master | ff |
|---|---|---|---|---|---|---|
| BFoxHistorySpace | 0 | 0 | 0 | 1 | 1 | 0 |
| BNumericWritable | 0 | 14 | 0 | 2 | 0 | 1 |
| BQudtUnitTag | 0 | 0 | 0 | 0 | 0 | 0 |
| BRootHistoryFolder | 0 | 0 | 0 | 0 | 0 | 0 |
| BSimpleSigningProfile | 5 | 5 | 5 | 5 | 5 | 5 |
| BSqlType | 0 | 0 | 0 | 0 | 0 | 0 |
| Column | 0 | 0 | 0 | 0 | 0 | 0 |
| EntitlementApi | 0 | 30 | 0 | 2 | 1 | 2 |
| StyleUtils | 0 | 0 | 0 | 0 | 0 | 0 |
| ValueDocDecoder | 3 | 3 | 3 | 9 | 3 | 8 |
| **classes compiling (0 errors)** | 8 | 6 | 8 | 5 | 6 | 6 |

All 5 BSimpleSigningProfile errors and all 3 Vineflower ValueDocDecoder errors are `reference to doPrivileged is ambiguous` (a lambda passed to the overloaded `AccessController.doPrivileged`, a [Block 116] loss class) — the same in every engine. The conservative view compiles fewer classes (6 vs 8) because its desugared pattern switches (`SwitchBootstraps.typeSwitch<…>`) are not Java (EntitlementApi 28 × `case, default, or '}' expected`); it is a READING view, never the recompile input. Compiling is not fidelity: the T15 grader decides that.

## 118.10 — The ladder: which instrument is ground truth for which question, and the citation-grade sequence

| Question type | Required instruments | Ground truth | Never sufficient alone |
|---|---|---|---|
| What does this method do (behaviour)? | docSource original if present ([Block 116] §116.1); else Vineflower default + §118.1 line-mapped view + T15 grade | the bytecode (`javap -c -p`; krak2 `-r` text when tools disagree) | any single decompiler's text |
| Was it written with syntax feature F (pattern, switch expr, var, record, lambda …)? | docSource; else bytecode attributes/indy ([Block 115]) or the §118.2 LineNumberTable verdict (`n5-bytecode-xref casts`) | docSource > bytecode attribute > LNT heuristic (measured 326/327, 92/92 on Tridium code) | decompiled text of ANY engine (Vineflower, CFR master and Fernflower resugar; CFR 0.152 de-sugars real patterns) |
| Who calls X? | `n5-bytecode-xref callers` (+ `--cha`), corroborated by SootUp or Joern | invoke instructions' symbolic references | module-navigator's text call graph (0 of 5 here) |
| Which override runs at this call site? | whole-install `subtypes`/`overriders` + SootUp CHA and RTA (with the JDK runtime in the view) | CHA over the whole install is sound for static dispatch (146/146 executed edges covered) | reading the override by eye; a view without the JDK (misses dispatch through JDK supertypes) |
| Does data flow from A to B, under which guard? | Joern `reachableByFlows` on bytecode; CodeQL traced-javac for guard attribution | agreement of both, joined on original line numbers | CodeQL buildless "no flow" (missed 1 of 4) |
| Does the decompiled logic behave like the shipped logic? | three-arm differential execution + jqwik + JaCoCo, for classes that initialise offline (33.6%) | the original bytecode's observed behaviour on covered lines | a green run without coverage; japicmp (API only) |
| Is the decompile byte-faithful? | T15 round-trip grader; krak2 `-r` for the textual form | the class bytes | "it compiles" |
| N4 ↔ N5 delta | normalized bytecode diff (package rename + constant-pool indices) INCLUDING the LineNumberTable | normalized bytecode | decompiled-text diff |
| Line numbers for a citation | §118.1 `// N` comments, SootUp/Joern/xref line fields, docSource lines | the class file's LineNumberTable | decompiled-file line numbers alone |
| Third-party library identity | [Block 117] §117.x per-entry comparison | upstream artifact bytes | whole-file SHA-1 (re-signed jars never match) |

**Recommended citation-grade sequence for a logic claim:**

1. Hash and locate the class by content ([Block 117] §117.10 steps 1-5).
2. If a docSource original exists, cite it (its lines are the shipped LineNumberTable).
3. Otherwise read the default Vineflower text for understanding, and cite the §118.1 conservative line-mapped
   view with ORIGINAL line numbers; flag any cited line carrying several `// N` values (merged statements, D9).
4. Check the class's T15 grade; below `roundtrip-exact`, co-cite `javap -c -p` (or krak2 `-r`) for the cited
   instructions.
5. For call, dispatch or reachability claims, cite `n5-bytecode-xref` plus SootUp or Joern (two instruments, one
   of them Soot-family and one not is not required — xref is independent of both).
6. For a guard/dataflow claim, cite Joern on bytecode and CodeQL traced mode; state that buildless CodeQL is not
   an absence proof.
7. For a syntax-adoption claim, cite docSource, a bytecode attribute, or the LNT verdict with its measured error.
8. For behaviour of pure logic, add a differential run with coverage; for Baja components, state the `refused`
   wall.

## 118.x — Corrections to earlier blocks

- **[Block 115] §115.1, idiom-matrix row 1** (`niagara5-block115.md:58`, "IDENTICAL — javap cannot decide"): the
  instruction stream is identical, but `javap -l`'s LineNumberTable decides the common case — classic casts on
  their own line are detected 326/326 on Tridium's originals, 1 of 93 patterns is misflagged; only same-line
  classic casts (0 observed in Tridium code) stay undecidable (§118.2).
- **[Block 115] §115.1 prose** (`niagara5-block115.md:83`, "only docSource originals or a non-resugaring decompiler
  (CFR) can settle those"): CFR does not settle it — CFR 0.152 renders a docSource-proven pattern
  (`organized/docSource/bajaui/niagara/ui/style/StyleUtils.java:209`) as a classic cast and CFR master resugars a provably classic site (§118.9). The same
  sentence is in the writer prompt's fidelity rule (session `common.txt`) and should be fixed there.
- **[Block 107] §107.3 / [Block 112] §112.1** call-site census: five `BRootHistoryFolder.getPermissions(null)`
  sites exist (dispatch: `BRootHistoryFolder.getPermissions(Context)`), not three; the two in `BHistorySpace.getNavChildren()` take the `BPermissions.all` branch on a
  station-side space (§118.4). [Block 112]'s conclusion for the three fox-proxy sites stands.
- **Kit `toolbelt/jvm-callgraph.sh`** (not a block): silently returns "no main method"/"matched no methods" on
  class-file 69 input (§118.3) — a propose-never-apply kit delta (B118-G5).

## 118.x — Connections

- [Block 116] §116.1 (docSource = shipped LNT) is what makes docSource line numbers a valid oracle for §118.1 and
  §118.2; §116.5's D6/D7 disappear in the conservative view, D9 does not (§118.1).
- [Block 117] §117.10's mandatory sequence gains steps 3-8 of §118.10 for logic claims; §117.x's Maven identity
  is corroborated in §118.9.
- [Block 110]/[Block 114] cite `organized/rdb/vineflower/niagara/rdb/ddl/Column.java:96-146` for `makeTypeDdl`;
  the docSource original exists at `organized/docSource/rdb/niagara/rdb/ddl/Column.java:173-185` with symbolic
  `case BSqlType.SQL_INT:` labels where the decompile shows inlined literals ([Block 115] constant-inlining rule) —
  citation-grade reading should cite the original.
- [Block 29]'s plain-TestNG and [Block 107]'s JDK-only PKIX reproduction were the precedents for §118.5; this block
  is the first to execute the ORIGINAL vendor bytecode side by side with its decompiled rebuild.
- [Block 87] §87.4 (`securityBridge.jar` on the boot class path) explains the first offline wall in §118.5.

## 118.x — Child gaps opened

- **B118-G1** (high) — Triage the 66 call sites that may reach `BHistorySpace.getNavChildren()` to decide whether
  the station-side unfiltered folder listing (§118.4; dispatch: `BRootHistoryFolder.getPermissions(Context)`,
  0 subtypes) is served to a remote session without a later per-user filter. Investigable read-only.
  coverage-check: `rg -il getNavChildren niagara5-block*.md` → [Block 51], [Block 97] only (unrelated).
  measured-by: `python3 tools/n5-bytecode-xref.py callers niagara.history.BHistorySpace getNavChildren --cha`
  (66 sites: 2 exact, 57 BINavNode, 4 BSpace, 3 BNavContainer).
- **B118-G2** (medium) — Regenerate the conservative line-mapped Vineflower view for every module and grade it
  with the T15 grader next to the default tree, to measure which variant round-trips more and how many of
  [Block 116]'s semantic differences disappear. Requires-execution (§19 build).
  coverage-check: `rg -il "dump_original_lines|bytecode-source-mapping" niagara5-block*.md docs/` → 0 before this
  block. measured-by: T15 grade counts per variant (`organized/<mod>/fidelity.json`).
- **B118-G3** (medium) — Root-cause CodeQL buildless's missed unguarded flow (decompiled line 264) — type
  resolution of the `<error type>` return of `addExtension` is the leading hypothesis. Requires-execution.
  coverage-check: `rg -il codeql niagara5-block*.md` → 0 before this block. measured-by: flows found per build
  mode on `BSimpleSigningProfile` (3 of 4 buildless, 4 of 4 traced).
- **B118-G4** (medium) — Build a generator that runs the three-arm differential + jqwik + JaCoCo over every pure
  static method among the 4,813 offline-initialisable classes, so behavioural fidelity is measured, not sampled.
  Requires-execution. coverage-check: `rg -il "differential execution" niagara5-block*.md` → none before this
  block. measured-by: count of classes with ≥1 differential run and their line coverage (`census-summary.txt`
  baseline 4,813 initialisable of 14,307).
- **B118-G5** (low) — Kit delta: `toolbelt/jvm-callgraph` should move to SootUp 3.0.1 (ASM 9.10.1), add the JDK
  runtime input location, and fail loudly on an unsupported class-file version instead of "no main method".
  Blocked-on-kit (propose-never-apply; retro). coverage-check: kit `tool-registry.md` row "JAR / .class JVM
  call-graph export" is the only SootUp entry. measured-by: the `--release 21/24/25` probe (1/1/0 paths).
- **B118-G6** (low) — Extend the LineNumberTable discriminator to other resugarings: statement merging (a decompiled
  line carrying several `// N`, as in D9) and switch-expression shape, validated on docSource like §118.2.
  Investigable read-only. coverage-check: `rg -il LineNumberTable niagara5-block*.md` → [Block 115], [Block 116],
  [Block 30]; none uses it as a discriminator. measured-by: confusion matrix vs docSource (as §118.2's 326/1/92).
- **B118-G7** (low) — A ground-truth runtime trace of a Tridium launcher or station. Blocked: `refused` (licensed
  runtime + config-home mutation, §118.6); reopen only with a licensed, disposable install.
  coverage-check: [Block 17] §17.2, [Block 29] §29.6 record the same license gate. measured-by: n/a until a licensed
  install exists.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | Vineflower 1.12.0 has a hidden `__dump_original_lines__` option; with `--bytecode-source-mapping` it prints original LNT lines | [CERT-hw] | `javap -constants` of `IFernflowerPreferences.class` in `tools/decompilers/vineflower-1.12.0.jar`; `evidence/b118/BQudtUnitTag.cons-linemapped.java` |
| 2 | Options after `-e=` are silently ignored | [CERT-hw] | scratch `x2/` vs `x3/` BQudtUnitTag renders, this session |
| 3 | 669/669 mapped lines match docSource; shifted control 226/669 | [CERT-hw] | `evidence/b118/linecheck.py`, `linecheck.out`, `linecheck-shift7.out` |
| 4 | Conservative view removes [Block 116] D6/D7, keeps D9 (flagged by `// 484 486 488`) | [CERT-hw] | `evidence/b118/BDevice.cons-linemapped.java`; `organized/docSource/driver/niagara/driver/BDevice.java:550-571` |
| 5 | LNT verdict vs docSource: 326 classic / 1 FP / 92 pattern | [CERT-hw] | `evidence/b118/lnt_pattern_validate.py`, `lnt_pattern_validate.out` |
| 6 | N4-4.15 and N5 BQudtUnitTag.getTag identical incl. LNT after normalization | [CERT-hw] | `evidence/b118/BQudtUnitTag.getTag.n4-4.15.norm.txt`, `BQudtUnitTag.getTag.n5.norm.txt` (sha256 `009753a0412c88c1…` both) |
| 7 | N5-wide: 2,332 sites, 1,918 classic-separate-line, 414 pattern-or-same-line; Vineflower renders 1,912 patterns | [CERT-hw] | `evidence/b118/casts_census.py`, `casts-census.out`; `rg -c` over `organized/*/vineflower` |
| 8 | SootUp 3.0.1 loads major 69 (262,982 bodies, 0 failures); CHA/RTA resolve the dispatch; 0 subtypes | [CERT-hw] | `evidence/b118/SootUpProbe.java`, `sootup-history.out` |
| 9 | Kit jvm-callgraph (SootUp 2.0.0) returns "no main method" on release-25 input | [CERT-hw] | `evidence/b118/kit-jvm-callgraph-release25.log` |
| 10 | module-navigator 0 callers vs 5 bytecode sites (SootUp, Joern, xref agree) | [CERT-hw] | `module-navigator/tools/module_nav.py callers`; `evidence/b118/joern-history-callers.out`; `xref-brootfolder-getpermissions-cha.json` |
| 11 | `n5-bytecode-xref.py` RED→GREEN 12/12, mutants killed, 21,504 classes 0 parse errors | [CERT-hw] | `tools/n5-bytecode-xref.py`, `tools/tests/test_n5_bytecode_xref.py` |
| 12 | BHistorySpace.getNavChildren calls getPermissions(null) twice (dispatch: `BRootHistoryFolder.getPermissions(Context)`); else-branch returns BPermissions.all for null cx | [CERT] | `organized/docSource/history/niagara/history/BHistorySpace.java:193-205`; `organized/history/vineflower/com/tridium/history/BRootHistoryFolder.java:42-58` |
| 13 | 4,813/14,307 classes initialise offline; wall = niagara.home in BObject.<clinit> | [CERT-hw] | `evidence/b118/census-summary.txt`, `init-probe2.out`, `InitProbe.java` |
| 14 | XParser three-arm differential 0/3,026 diffs; jqwik 3/3 green; mutant caught; coverage 263/407 XParser lines | [CERT-hw] | `evidence/b118/xpdiff-summary.txt`, `jqwik-run.out`, `jqwik-run-mutant.out`, `cov-orig.csv` |
| 15 | Trace agent: 146 dynamic edges; CHA+JRT 146/146, RTA 145/146, CHA without JDK 144/146 | [CERT-hw] | `evidence/b118/TraceAgent.java`, `trace-orig.txt`, `soundness-jrt.txt` |
| 16 | CodeQL buildless 3/4, traced 4/4; Joern 4/4 at original lines 420/427/434/439 | [CERT-hw] | `evidence/b118/codeql-csr-flow-buildless.csv`, `codeql-csr-flow-manual.csv`, `joern-csr-flow.out` |
| 17 | krak2 `-r` round-trip 20,724/20,724 module classes byte-identical | [CERT-hw] | `evidence/b118/krak2-jar-roundtrip.sh`, `krak2-roundtrip.tsv` |
| 18 | CFR master resugars BQudtUnitTag and renders `case null, default` against a `requireNonNull` prologue | [CERT-hw] | scratch `ts/BQudtUnitTag/cfr-master/`, `ts/BNumericWritable/cfr-master/`; `javap -c -p niagara.control.BNumericWritable` (pc 2 `Objects.requireNonNull`) |
| 19 | bin/ext asm-9.10.1.jar: 39/39 classes identical to Central, whole-file SHA-1 differs (re-signed) | [CERT-hw] | `evidence/b118/entry-cmp-asm.txt` |
| 20 | Engine recompile counts: Vineflower default/forensic 8/10 classes compile, conservative 6, CFR 0.152 5, CFR master 6, Fernflower 6 | [CERT-hw] | `evidence/b118/recompile-by-engine.tsv` |
| 21 | Launcher traces would mutate the config home and hit the license gate (not run) | [INFER] | [Block 17] §17.2 record + registry/jar-cache mtimes; no launcher executed this session |

**Tally:** 19 `[CERT-hw]` · 1 `[CERT]` · 1 `[INFER]` (row 21: the `refused` decision's premise, drawn from
[Block 17]'s record, deliberately not re-tested).

**Artifacts:** small durable copies staged for `evidence/b118/` (46 files, 268 KB, listed in the task report,
sha256 in `evidence/b118/SHA256SUMS`); bulk scratch under
`/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b118/`
(`ts/` per-class variant outputs, `m3/census/`, `m4/static-edges-jrt.txt`, the CodeQL databases, the Joern CPGs).
Tools provisioned into scratch (versions and sha256 in the task report): Maven 3.9.16 (Homebrew), SootUp 3.0.1,
Joern v4.0.639, CodeQL bundle 2.27.1 (Java), CFR master `c4145259`, Fernflower `5ab777bf`, JaCoCo 0.8.15, japicmp
0.26.2, jqwik 1.10.1 + JUnit Platform console 1.14.4.
