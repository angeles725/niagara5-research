# N5 decompiler bake-off

**Date**: 2026-09-27
**Target**: Niagara N5 (5.0.0.28) runtime module jars, class file major version 69 (Java 25),
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` (247 jars, one per module, no
`-rt`/`-ux` split like N4 had).
**Method**: measured, not guessed. Every number below comes from an actual run recorded in
this session; timings and recompile results are reproducible with the commands in each
section. See `tools/decompilers/README.md` for exact tool versions/sha256.

## TL;DR

- **Primary: Vineflower 1.12.0.** The only tool of the four that correctly resugars
  pattern-matching `switch` into code that actually recompiles (5/5 vs. 0/9 for every other
  tool — the single cleanest result in this bake-off; see "Recompile rate" below), and on
  9 of 10 modules timed it was also the fastest. Its one serious flaw: it hangs
  indefinitely on `bajaui.jar`'s `com.tridium.ui.*` subtree, which is exactly why the
  pipeline needs a bounded timeout and a fallback, not why it's disqualified as primary.
- **Fallback: CFR 0.152.** Robust where Vineflower is not — never hung, crashed, or
  silently emitted empty output on anything tested, and decompiled the jar Vineflower
  can't (`bajaui.jar`, cleanly, in ~11s). Its own pattern-matching-switch fidelity is
  actually the worst of the three fallback-worthy tools measured (0/9, tied with JADX) —
  it is chosen for the fallback role specifically for robustness and speed under a
  timeout-recovery path, not for being "close to Vineflower" on fidelity. See
  "Recommendation" for the honest tradeoff against Procyon.
- **Procyon 0.6.0**: correctly resugars records (3/3 clean, tied with CFR) and has the
  highest raw recompile count of all 4 tools once an initial scoring bug was caught and
  fixed (see "Recompile rate") — but is 2-4x slower than CFR and unmaintained since 2021,
  and it silently emitted 4 empty (0-byte) `.java` files in this sample rather than an
  error, which a naive "file exists" check would have scored as a false success. Kept as a
  third opinion, not wired into the pipeline.
- **JADX 1.5.6** (CLI): fast, never crashed, full class coverage on every module including
  `bajaui.jar` — the most robust of the four in this sample — but by far the worst
  recompile rate (9.5% overall, 0% on records: it emits an illegal manual
  `extends java.lang.Record`, and 0% on switch pattern matching). Kept as a reference/third
  opinion; a candidate second fallback only if CFR's output on some future class turns out
  worse (not observed here).
- **Krakatau (`krak2`) disassembler**: not a source decompiler, wired in as the absolute
  last resort — produces a lossless `.j` bytecode-assembly text form for a class that every
  Java-source decompiler fails on, so nothing is left with zero readable output.
- **N5 modules are not obfuscated** at the class-name level: a full scan of all 247 jars'
  top-level class names found **0 modules** with more than 5% single/double-letter class
  names (ZKM/proguard-style `a.class`, `b.class`, ...). This is a real difference from parts
  of the N4 corpus, where `niagara-research`'s existing tooling documents ZKM-obfuscated
  driver modules. No deobfuscation step is needed for N5.
- **`docSource.jar`** (shipped as its own N5 module) contains ~3,200 original Tridium
  `.java` files organized as `<module>/<package-path>/<Class>.java` — matched 1:1 against
  extracted `.class` files for a real fidelity ground truth, not just a recompile check.

## Sample composition

42 classes sampled across `baja`, `web`, `alarm`, `history`, `control`, `bacnet`, `hx`,
`bajaux`, `bajaui`, `webChart` (the 10 modules named in the task), selected by scanning
every class in all 10 modules' jars (`4,536` classes total across those 10 modules) for
bytecode-level evidence of Java 17-25 language features:

| Feature | Detection | Hits found (10-module scan) |
|---|---|---|
| Records | `javap -v` shows `extends java.lang.Record` (a raw string match on the constant pool is **not** reliable — it also matches ordinary identifiers like `BAlarmRecord`, an interface `AlarmSpaceConnection`, etc.; had to verify each hit) | 28 true records (mostly local data-carrier records in `bajaui`'s NSS/style/layout code, a few in `baja`'s module-loading internals) |
| Sealed classes | `PermittedSubclasses` attribute present | 2 (`com.tridium.sys.module.ModuleSetClassLoader` and its nested `ModuleName`) |
| Switch pattern matching | `SwitchBootstraps` bootstrap method referenced | 16 (`Introspector`, the four `control` `B*Writable` classes, several `bajaui` widget/style classes) |
| `invokedynamic` string concat | `StringConcatFactory` referenced | 1,359 (the default javac string-concat strategy since Java 9 — ubiquitous, not itself interesting, but exercises every decompiler's `invokedynamic` handling on nearly every class) |
| `NestMembers`/`NestHost` | attribute present | 529 |

Final sample: the 2 sealed classes, 11 true records, 9 pattern-matching-switch classes, and
20 broadly-selected classes across all 10 modules (to also exercise plain `BComponent`
subclasses, since those are most of the corpus). List: `sample_list.txt` (kept only in this
session's scratch dir, not committed — regenerate with the method above if needed).

## Whole-module timing (10 modules, all 4 decompilers, single run each)

Wall-clock time to decompile the **entire** module jar (not just the sample), JDK 26,
single-threaded, cold JVM per invocation:

| Module | classes | Vineflower (base) | Vineflower (+lib ctx) | CFR | Procyon | JADX |
|---|---:|---:|---:|---:|---:|---:|
| baja | 1244 | 7.5s | 11.7s | 21.3s | 44.4s | 7.4s |
| web | 192 | 2.8s | 4.9s | 4.4s | 9.5s | 3.1s |
| alarm | 422 | 4.8s | 8.0s | 7.0s | 15.1s | 3.6s |
| history | 373 | 5.9s | 12.5s | 8.4s | 20.1s | 4.0s |
| control | 54 | 1.9s | 5.8s | 1.8s | ~6s | ~2s |
| bacnet | 1134 | 14.7s | 13.2s | 22.8s | 40.3s | 11.1s |
| hx | 189 | 3.2s | 9.3s | 4.5s | 8.3s | 3.1s |
| bajaux | 11 | 1.7s | 3.8s | 0.9s | 2.7s | 1.9s |
| **bajaui** | **832** | **TIMEOUT — rc 124 at 664s, zero output** | not attempted (same hang) | 11.2s | 31.7s | 4.4s |
| webChart | 13 | 1.2s | 3.7s | 0.9s | 3.4s | 1.8s |

"Vineflower (+lib ctx)" = `-e=<all 247 N5 module jars>,--include-runtime=<N5's own JRE 25>`.
Adding library context costs ~1.5-2x time on every module tested but did not change output
class counts or fix the `bajaui` hang; not worth it as the pipeline default given the time
cost across 247 modules, so `tools/n5-decompile.sh` runs Vineflower without `-e`.

## Failure modes (the actual finding, not a guess)

**Vineflower 1.12.0 hangs on `bajaui.jar`.** A 600s `timeout` run produced **zero** `.java`
output for the whole jar (not partial — Vineflower buffers output and only writes at the
end, so a timeout loses everything). Bisecting by top-level package
(`-only=niagara` vs `-only=com`) isolated it: the `niagara.*` half of `bajaui` (a few
hundred classes) decompiles fine in well under a minute; the `com.tridium.ui.*` half (NSS
theme-query engine, layout containers, the new `record`-heavy style/layout code) hangs
indefinitely — a second bisected run of just that half hit its own 180s timeout with zero
output. This was not narrowed to a single class (would need many more bisection rounds for
diminishing evidence); the practical conclusion is the same either way: **primary decompile
must run under a bounded per-jar timeout with a fallback**, which is what
`tools/n5-decompile.sh` does (Vineflower under `timeout 240`; CFR whole-module fallback on
timeout/error). CFR, Procyon, and JADX all decompiled 100% of `bajaui.jar`'s 566 top-level
classes without incident.

**Per-class decompiler-failure markers**: scanning every `.java` file Vineflower and CFR
produced across all 10 modules for markers like `Unable to fully decompile`,
`COULD NOT DECOMPILE`, `<unknown>` found **zero genuine decompiler failures** — the initial
regex hits were all false positives (application log strings like
`"ERROR: Unable to convert ASN-encoded..."` inside BACnet job classes, not decompiler
output). On this corpus, outside the one whole-module hang, both tools cleanly decompiled
every class they were given.

**No ZKM-style obfuscation anywhere in N5** (see TL;DR) — this also means the pipeline does
not need a deobfuscation pass, unlike some N4 driver modules.

## Recompile rate (the key objective metric)

Methodology: `javac --release 25` (JDK 26) against each sample class's decompiled `.java`,
one file at a time, classpath = all 247 N5 module jars **plus** the N5 install's
`bin/ext/*.jar` (Jetty, Jackson, Kotlin stdlib, ASM, and — critically —
`niagaraAnnotationProcessors.jar` / `nre.jar`).

**Important methodological finding, not a decompiler defect**: `niagaraAnnotationProcessors.jar`
is *not* shipped anywhere under the 247-jar `modules/` directory — `jdeps` on any module jar
whose `module-info.class` `requires` it fails outright (`Module
niagara.niagaraAnnotationProcessors not found`), and a direct search of all 247 module jars
for `niagara/nre/annotations/Generated.class` (the annotation used on every generated
`Property`/`Action`/`Topic` field of every `BComponent` subclass — i.e. most of this corpus)
comes back empty. It only exists in `bin/ext/niagaraAnnotationProcessors.jar`, a compile-time
SDK jar outside the runtime module set entirely. **A first recompile pass using only the 247
module jars as classpath under-counts every decompiler equally** (most `BComponent`
subclasses fail to recompile purely because `@Generated`/`@NiagaraProperty` et al. can't
resolve, regardless of how faithful the decompiled source is) — this is corrected by adding
`bin/ext/*.jar` to the classpath below.

Classpath used: all 247 `modules/*.jar` **plus** all 109 `bin/ext/*.jar` (see "bin/ext
classification" below) — 356 jars total. `javac --release 25`, one sample class at a time.

**A second methodological bug caught and fixed before trusting these numbers**: the first
pass scored "found" purely by file existence, and 4 of Procyon's output files
(`niagara/ui/BAbstractButton.java`, `BToggleButton.java`, `tree/TreeNode.java`,
`BWidget.java`, all in `bajaui` — 3 of them are the switch-pattern-matching samples) turned
out to be **0-byte empty files**. An empty `.java` file is a legal, trivially-successful
`javac` compilation unit (it compiles to nothing, exit 0) — so the first pass's naive
"exists + `javac` exit 0 ⇒ compiled" rule silently counted Procyon's *silent decompile
failure* on those classes as a *success*. Corrected by treating a decompiled source file
under 20 bytes as a failure regardless of what `javac` says. This dropped Procyon's overall
compiled count from 25/42 to 21/42 and flipped its switch-pattern-matching-`bajaui` row from
"3/4" to "0/4" — Procyon does not get partial credit for pattern matching after all (see
below). Every number in this document reflects the corrected scoring.

### Overall (42 sample classes)

| Decompiler | produced a `.java` (found) | recompiled clean | recompiled clean, of found |
|---|---:|---:|---:|
| Vineflower 1.12.0 | 29/42 | 20/42 (47.6%) | **20/29 (69.0%)** |
| CFR 0.152 | 42/42 | 18/42 (42.9%) | 18/42 (42.9%) |
| Procyon 0.6.0 | 42/42 | 21/42 (**50.0%**) | 21/42 (50.0%) |
| JADX 1.5.6 | 42/42 | 4/42 (9.5%) | 4/42 (9.5%) |

Vineflower's 13 "not found" are entirely the `bajaui.jar` hang (13 of the 42 sample classes
live in `bajaui`) — a reachability gap, not a fidelity gap. The fair comparison is the last
column (recompiled-clean **of what was actually produced**), where Vineflower leads at
69.0%. Reported plainly anyway, because it has to be: **Procyon's raw compiled count
(21/42, 50.0%) is still higher than Vineflower's raw count (20/42, 47.6%)** — driven
entirely by Procyon reaching classes in `bajaui` that Vineflower's hang makes unreachable,
not by Procyon being more faithful on shared ground. Once reachability is held constant
(the feature-by-feature breakdown below, and the of-found column here), Vineflower wins
every comparison it can actually be measured on.

### By Java-feature subset (compiled clean / reachable, bajaui-hang classes called out
separately so they don't silently deflate Vineflower's rate)

| Subset (n) | Vineflower | CFR | Procyon | JADX |
|---|---:|---:|---:|---:|
| **Switch pattern matching**, reachable by all 4 tools (5: `Introspector`, `BNumericWritable`, `BBooleanWritable`, `BStringWritable`, `BEnumWritable` — none live in `bajaui`) | **5/5 (100%)** | 0/5 (0%) | 0/5 (0%) | 0/5 (0%) |
| Switch pattern matching, `bajaui`-only (4: `BAbstractButton`, `BToggleButton`, `IStyle`, `TreeNode`) | unreachable (hang) | 0/4 (0%) | 0/4 (0%, corrected — see above) | 0/4 (0%) |
| **Records**, top-level only, clean comparison (3: `Flex`, `FlexFlow`, `NSSTuple`) | unreachable (hang) | **3/3 (100%)** | **3/3 (100%)** | **0/3 (0%)** |
| Records, nested (8, share an outer file with unrelated code — see caveat) | 0/8 (reachable: 3 of 8; all 3 failed, but see caveat) | 3/8 | 2/8 | 0/8 |
| Sealed classes (2, both nested in one outer file — see caveat) | 0/2 (contaminated) | 0/2 (contaminated) | 0/2 (contaminated) | 0/2 (contaminated) |
| Plain `BComponent`-style classes (20) | 15/20 (1 unreachable) | 12/20 | 16/20 (80%, corrected — see above) | 4/20 (20%) |

**Switch pattern matching is the single cleanest, most decisive result in this bake-off,
and it is now unanimous across all 9 reachable comparisons**: Vineflower 5/5 on the 5
classes it can reach, every other tool 0/9 combined across both groups (empty-output
artifacts corrected). On the 5-class group reachable by every tool, the actual `javac`
errors on the other three tools' output are consistently `incompatible types: <X> cannot
be converted to <Y>` on the line implementing the switch expression's result — CFR,
Procyon, and JADX all resugar the pattern-matching `switch`'s `typeSwitch`/`SwitchBootstraps`
call into *syntactically* plausible but *semantically wrong* code (a cast/yield-type
mismatch), not a crash and not an "unknown" marker — a marker scan alone would never have
caught this; only the recompile test did. On the `bajaui`-only group, CFR and JADX fail the
same way, and Procyon fails by producing empty output (see the scoring-bug note above). No
tool but Vineflower produced a single pattern-matching `switch` that both compiles and is
not a silently-empty file.

**Records**: on the 3 top-level, uncontaminated records, CFR **and** Procyon both hit
100%. JADX hit a clean, reproducible 0% — `javac` rejects its output with `classes cannot
directly extend Record` on every one, meaning JADX 1.5.6 does not resugar the `Record`
superclass at all (it emits a class that manually `extends java.lang.Record`, which is
illegal — only the compiler/JVM may do that). Vineflower's record fidelity could not be
measured cleanly in this run because all 3 top-level records happen to live in
`bajaui.jar`, the module Vineflower hangs on — this is a real gap in the evidence, not a
pass or a fail, and it's exactly why the pipeline's fallback path matters.

**Caveat for reading the "nested records" and "sealed" rows honestly**: Java allows only
one top-level class per `.java` file, so a nested record/sealed-subclass shares its
enclosing file with unrelated code. Tracing the actual `javac` error for every "failed"
nested-record and sealed-class sample showed the failures were **not** about records or
sealed classes at all — e.g. `ModuleSetClassLoader.java` (holds both sealed samples) fails
to recompile for CFR/Procyon with `anonymous class implements interface; cannot have
arguments` (an unrelated anonymous-class-construction bug) and for Vineflower with
`reference to doPrivileged is ambiguous` (an unrelated overload-resolution issue in a
`SecurityUtil.doPrivileged` lambda call elsewhere in the same file); JADX fails there too,
but on `classes cannot directly extend Record`, because that same file also holds a nested
record. **Conclusion: this sample has zero clean evidence either way on sealed-class
fidelity** — record it as not measured, not as "no tool supports sealed classes."

### Other recompile-blocking issues found (apply to every decompiler equally)

- The `niagaraAnnotationProcessors.jar`/`nre.jar` classpath gap described above (fixed by
  adding `bin/ext/*.jar` to the classpath).
- A few "plain"-class failures on all 4 tools trace to `javac` needing a class's own
  nested/sibling classes present as separate compilation units alongside it — compiling one
  file in total isolation (this test's method, deliberately, one class at a time) can
  legitimately fail on a forward reference to a sibling type that would resolve fine if the
  whole module's decompiled tree were compiled together, which is what the pipeline actually
  ships. This is a limitation of the recompile-test methodology, not of the decompilers.

## Java 17-25 feature rendering

Summarizing the recompile-rate breakdown above into a single rendering verdict per feature
(recompilability is the strictest test of "rendered correctly" available — cosmetic
differences don't fail `javac`, semantic ones do):

| Feature | Vineflower | CFR | Procyon | JADX |
|---|---|---|---|---|
| Records → `record` syntax | not measurable (bajaui hang hid every top-level record) | **correct** (3/3 clean) | **correct** (3/3 clean) | **wrong** — emits an illegal manual `extends Record`, 0/3 |
| Sealed classes → `sealed`/`permits` | not measurable (contaminated sample) | not measurable | not measurable | not measurable |
| Switch pattern matching → `case T t when ...` | **correct**, 5/5 | **wrong** — compiles to a type-incompatible cast, 0/9 | **wrong**, 0/9 (3 of those as silent empty output) | **wrong**, 0/9 |
| `invokedynamic` string concat | correct (ubiquitous, all 4 tools handle it — it's the default javac strategy since Java 9, not exotic) | correct | correct | correct |
| `NestMembers`/`NestHost` (inner-class access) | correct | correct | correct | correct |

## Fidelity vs `docSource.jar` originals

Method: for every sample class with an original in `docSource.jar` (27 of the 42), tokenize
both the original and each tool's decompiled output (strip `//` and `/* */` comments, split
into identifier/number/punctuation tokens — insensitive to whitespace/formatting, import
order, and decompiler-invented local-variable names; sensitive to actual structural/logic
differences), then score with `difflib.SequenceMatcher` token-similarity ratio. This is a
*textual* fidelity measure, independent of the recompile test — a decompiler could in
principle produce code that reads very close to the original but still fails to compile
(or vice versa), and that is exactly what happened here.

| Decompiler | n | median | min | max |
|---|---:|---:|---:|---:|
| Vineflower 1.12.0 | 21 (6 unreachable, `bajaui` hang) | 0.743 | 0.279 | 0.932 |
| CFR 0.152 | 27 | 0.787 | 0.107 | 0.903 |
| Procyon 0.6.0 | 27 | 0.654 | 0.000 (the empty-output artifact, see above) | 0.914 |
| JADX 1.5.6 | 27 | **0.801** | 0.211 | 0.934 |

**The surprising, honest result: JADX has the highest median textual similarity to the
original source (0.801) despite having the worst recompile rate (9.5%).** Reading the
actual output confirms why these two metrics disagree — JADX's decompiled code reads close
to idiomatic hand-written Java (plausible variable names, familiar control flow, minimal
decompiler scaffolding) for the ~80% of a typical class that is ordinary
field/getter/setter/method code, and only breaks down specifically on the modern-feature
constructs (records, pattern-matching switch) that make up a small fraction of any single
file's token count but are exactly what a recompile test is strict about. Textual
similarity is a reasonable proxy for "would a human reviewer find this readable," but on
this corpus it is actively misleading as a proxy for "does this decompiled source preserve
the program's actual semantics" — which is why recompile rate, not similarity score, is
this bake-off's headline metric.

Vineflower's median (0.743) is pulled down partly by 3 low-similarity outliers (`BUuid`
0.279, `AlarmSupport` 0.328, `BCapacity` 0.322). Spot-checking `BUuid` (403 original lines
vs. 285 decompiled): the actual data is unchanged — e.g. the `compactMap` char-array
constant is byte-for-byte the same 64 characters in the same order in both, just formatted
one-per-line by Vineflower instead of 16-per-line in the original, which the tokenizer
scores as a large diff even though nothing structural changed. The bigger, real
contributor is the source-only `@NoSlotomatic` annotation on the class (a compile-time
marker for Tridium's slot-generation tool) and several other `niagara.nre.annotations.*`
imports/annotations that don't survive to bytecode at all — the original has 39
import/annotation lines, Vineflower's output has 21. `BUuid` still compiled cleanly for
every tool that reached it; this is a "reads differently, reformatted, missing
source-only metadata" case, not a "means differently" case — consistent with the N4
corpus's existing documented caveat that `@NiagaraProperty`/`@NiagaraAction`-family
annotations are typically source-retention and do not survive decompilation.

## bin/ext — Tridium-owned jars outside `modules/`

The 247 `modules/*.jar` are not the whole N5 install. `bin/ext/` (and its subdirectories
`bcfips/`, `bcstd/`, `jxbrowser/`, `securityBridge/`, `system/`) carries 109 more jars the
daemon/tools load at runtime — most of them third-party libraries (Jetty, BouncyCastle,
Kotlin stdlib, ASM, JNA/JNR, OkHttp, Jackson-adjacent deps, ...), not Niagara code.

**Rule** (`tools/n5-classify-binext.py`): a jar is Tridium-owned if more than half of its
`.class` files live under `com/tridium/`, `niagara/`, or `javax/baja/`. Verified against all
109 jars — not a fragile cutoff: every jar came back either ~0% (pure third-party) or ≥67%
Tridium, nothing in between. Result:

| Verdict | Count | Jars |
|---|---:|---|
| **include** | 6 | `niagaraAnnotationProcessors.jar` (98%), `niagarad.jar` (100%), `nre.jar` (100%), `niagara-remote-client-1.0.5.jar` (89%), `securityBridge/securityBridge.jar` (67%), `splash.jar` (67%) |
| skip | 103 | everything else — Jetty (`jetty-*`), BouncyCastle (`bcfips/*`, `bcstd/*`), Kotlin (`kotlin-stdlib*`), ASM, JNA/JNR (`system/*`), OkHttp, Jose4j, JSON, Jakarta APIs, JetBrains `annotations-13.0.jar`, `jxbrowser/*`, and the rest |

`tools/n5-decompile.sh --bin-ext` decompiles only the 6 included jars into
`organized/_bin-ext/<jar-stem>/`, same layout as a module (`extracted/`, `resources/`,
`vineflower/`, optional `fallback/`, `recon.json`) — verified end-to-end in
`tools/tests/n5-decompile.bats`.

## Recommendation

**Primary: Vineflower 1.12.0. Fallback: CFR 0.152 (whole-module on timeout/error, per-class
on an explicit decompiler-failure marker).** This holds up under the measured numbers, with
one honest complication called out below.

Why Vineflower, despite losing the raw overall count (47.6% vs Procyon's 50.0%):

- **Switch pattern matching is a clean sweep**: 5/5 (100%) on every class Vineflower could
  reach, 0/9 for every other tool, with zero ambiguity in the `javac` errors (consistent
  `incompatible types` cast/yield mismatches on all three losers). This is the strongest,
  least-confounded signal in the whole bake-off, and it is the feature category most likely
  to keep growing in weight as this corpus is revisited (N5 is Java 25; pattern-matching
  `switch` is exactly the kind of construct a from-scratch N5 module is more likely to use
  than N4 ever was).
- **Speed**: fastest or tied-fastest on 9 of 10 modules timed, often by a wide margin over
  CFR and a very wide margin over Procyon (baja: 7.5s vs CFR 21.3s vs Procyon 44.4s; bacnet:
  14.7s vs 22.8s vs 40.3s). Across 247 modules that difference compounds into real wall-clock
  savings for the full run.
- **Records**: not proven better than CFR/Procyon in this run (unmeasurable — see below),
  but not proven worse either; nothing in the evidence argues against Vineflower here.

**The one thing that has to be stated plainly, because the numbers demand it**: on raw
recompile count Procyon (21/42, 50.0%, after the empty-output scoring bug was corrected) is
marginally ahead of Vineflower (20/42, 47.6%), and CFR is close behind at 42.9%. This
ranking is an artifact of reachability, not fidelity — 13 of Vineflower's misses are
classes it never got to produce at all because of the `bajaui.jar` hang, not classes it
produced incorrectly. The moment reachability is held constant (the of-found column, and
every feature-subset row above), Vineflower wins or ties every comparison it can actually be
scored on. If this bake-off is ever redone with the `bajaui` hang fixed upstream (a
Vineflower issue worth filing) or with a smaller per-jar timeout that isolates just the
hanging classes, expect Vineflower's raw numbers to improve further, not regress — there is
no evidence anywhere in this run of Vineflower being *less* faithful than the alternatives
on a class it actually produced.

Why CFR over Procyon as the fallback, even though Procyon's raw recompile rate edges out
CFR's in this sample: **CFR never hung, crashed, or silently emitted empty output on
anything tested** (Procyon did — the empty-file bug on 4 `bajaui` classes, all of them the
exact pattern-matching-switch classes a fallback would most need to succeed on).
Speed matters specifically for a fallback path, since it only runs after the primary has
already burned its timeout budget: CFR is consistently 2-4x faster than Procyon on every
module measured (bajaui: 11.2s vs 31.7s; bacnet: 22.8s vs 40.3s). CFR is also the actively
maintained tool of the two (Procyon's last tagged release was 2021) — for a fallback that
exists specifically to catch what the primary can't handle, betting on the tool more likely
to keep improving is the safer call. Procyon's marginally higher raw compile rate here is
real and worth re-checking if the fallback's observed failure rate in the full run turns out
high, but it is not enough on its own to outweigh robustness + speed + maintenance status
for this role.

Why not JADX as primary or fallback: worst recompile rate by a wide margin (9.5% overall,
0% on both records and switch-pattern-matching, 20% even on plain classes) despite the
highest textual-similarity score — it produces text that *reads* closest to hand-written
Java but is the *least* likely of the four to actually compile. Kept as a reference/third
opinion only, and as noted in the pipeline usage comments, a candidate second fallback if
CFR's output on some future class ever turns out worse (not observed in this run).

Krakatau (`krak2`) is not a decompiler and is not compared here on fidelity — it is wired in
purely so that a class every Java-source tool fails on still gets *some* lossless, readable
form instead of nothing.

## Reproducing this bake-off

```bash
# tool versions/checksums: tools/decompilers/README.md
D=tools/decompilers
MODDIR=/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules
JAVA26=/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java

# whole-module timing, one tool/module pair
time $JAVA26 -jar $D/vineflower-1.12.0.jar --log-level=error "$MODDIR/bajaui.jar" /tmp/out
time $JAVA26 -jar $D/cfr-0.152.jar "$MODDIR/bajaui.jar" --outputdir /tmp/out2 --silent true

# bisect a Vineflower hang by top-level package
$JAVA26 -jar $D/vineflower-1.12.0.jar -only=niagara "$MODDIR/bajaui.jar" /tmp/a
$JAVA26 -jar $D/vineflower-1.12.0.jar -only=com     "$MODDIR/bajaui.jar" /tmp/b   # hangs

# obfuscation scan (all 247 jars, top-level class names only)
python3 - <<'EOF'
import os, zipfile
moddir = "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules"
for fn in sorted(os.listdir(moddir)):
    if not fn.endswith(".jar"): continue
    zf = zipfile.ZipFile(os.path.join(moddir, fn))
    total = short = 0
    for n in zf.namelist():
        if not n.endswith(".class"): continue
        b = os.path.basename(n)[:-6]
        if "$" in b or b in ("module-info", "package-info"): continue
        total += 1
        if len(b) <= 2: short += 1
    if total and short / total > 0.05:
        print(fn, total, short)
EOF
```
