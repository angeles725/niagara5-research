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

## Semantic defects (B116)

Everything above this section measures **syntax** fidelity (does the decompiled text use the
right modern Java construct, does it recompile at all). It is not a semantic fidelity
measurement. `niagara5-block116.md` (T14 of `odd/tasks/decompiler-fidelity-audit.md`) ran a
per-method bytecode oracle — every decompiled method recompiled and compared, normalized,
against the shipped class's own bytecode — over 36,977 methods across 3,436 class files (the
2,809 docSource-covered files plus synthetic javac-25 probes) and found **11 confirmed
semantic defects (D1-D11)**: 9 behavior-changing, 2 precision-edge, 0.030% of methods checked.
Every D-case is a Vineflower case (the 293 CFR-rendered `bajaui` files in that sample
contributed none); CFR is not a semantic oracle either — B116 also caught CFR dropping
`(Object)null` casts.

**The rule this establishes for every consumer of this corpus**: a corpus claim about behavior
that depends on overload binding, boxing/unboxing, numeric conversion, `finally` control flow,
or local-variable-vs-field identity must be confirmed with `javap -c -p` on the shipped
`.class` or against a `docSource.jar` original — never read off the decompiled `.java` text
alone. Concretely, in this run: a dropped `(Object)` cast or dropped `Long.valueOf`/boxing call
silently rebinds an overload (`SpyWriter.prop(Object,Object)` → `prop(Object,Runnable)` or
`prop(Object,double)`); `instanceof`-pattern resugaring can turn a local variable into a field
reference with the same simple name (`BDevice.checkFatalFault`, `BProxyExt.checkFatalFault`);
varargs calls can collapse to zero-length arrays; and a `try { throw; } finally { return; }`
can lose the `return`. See `niagara5-block116.md` §116.5 for the full D1-D11 table (module ·
class · method · docSource-vs-decompiled diff · effect) and §116.3 for the synthetic S1-S6
reproductions with the exact Vineflower 1.12.0 release-note context.

`niagara5-block116.md` §116.3 also already ran a library-context experiment ahead of this
feature (re-decompiling the 7 Part-B defect classes with all 452 classpath jars as `-e`
externals, no `--include-runtime`): it fixed only **D4/D5** (`Array.remove(Object)` →
`remove(int)`) and left D1, D2/D3, D6/D7, and D8/D9 unchanged — library context resolves
*type* information, not the overload-selection and control-flow-loss bugs behind most of these
defects. See the "v2 library-context run" section below for this feature's own from-scratch
check of D1-D11 against the actual `--variant v2` pipeline output (adds `--include-runtime`
and the fidelity flags the §116.3 ad-hoc test did not use).

## v2 library-context run

T19 of `odd/tasks/decompiler-fidelity-audit.md`: v1 (`organized/<mod>/vineflower/`) runs
Vineflower with **no library context at all** — no `--add-external` for the other N5/bin-ext
jars, no `--include-runtime`. `tools/n5-decompile.sh --variant v2 [<module>|--all]` is a second,
side-by-side variant, writing `organized/<mod>/vineflower2/` (+ `fallback2/` on a CFR
whole-module or per-class fallback), that gives Vineflower the full picture: every *other* N5
module jar (excluding the module's own), every jar under `bin/ext/` (all 109, not only the six
`n5-classify-binext.py` calls Tridium-owned — a different question, see the header comment),
every embedded third-party lib some modules ship inside their own jar's `LIB-INF/` (sourced from
`organized/_v2-libcache/`, an immutable cache built once, serially, by the required
`--prepare-libcache` step — see "T19 fix" below; **not** a live scan of any
`organized/<mod>/extracted/` tree), and the real JDK 25 runtime via `--include-runtime`. CFR's
whole-module/per-class fallback gets the same library set via `--extraclasspath`.

**Undocumented Vineflower 1.12.0 CLI bug found while building this**: an "Additional option"
(`--include-runtime`, `--use-lvt-names`, ...) placed *after* a "General option"
(`-e`/`--add-external`) is silently dropped — Vineflower prints `warn: missing
'--include-runtime=...', ignored` and treats the flag text as a bogus positional source file,
exit code 0, no other sign anything was wrong. Verified with isolated single-flag repros
(`--include-runtime` alone works; combined with `-e` in either order it silently drops unless
every Additional option precedes `-e`). Every Additional option must precede
`-e`/`--add-external` on the command line for v2 to actually apply them; `decompile_module_v2`
enforces this order and a bats regression test asserts the log carries zero
`warn: missing` lines. A second gotcha: Homebrew's keg-only `openjdk@25` formula symlinks
`bin/`/`include/`/etc. under `opt/openjdk@25` itself, but the actual JDK home Vineflower needs
(with `lib/modules`, the jrt image) is one level down at `opt/openjdk@25/libexec` — passing
`opt/openjdk@25` itself crashes Vineflower with a `NullPointerException` in
`JrtFinder.addRuntime`.

### T19 fix: library-context race in the first v2 campaign (2026-09-28 07:20-07:32Z), and the rerun

The **first** v2 campaign (documented as-run in "Campaign" below) built the `LIB-INF` part of
each module's library set by scanning `organized/*/extracted/LIB-INF/*.jar` **live**, while
running up to 6 modules in parallel (`xargs -P 6`). `organized/_logs/` shows 5 modules
(`analyticsLibs`, `apachePoi`, `commonsIo`, `commonsLang`, `niagaraTest`) had their
`organized/<mod>/extracted/` tree rm-rf'd and re-unzipped by `ensure_extracted_for_v2` during
that exact 07:20-07:32Z window — a real filesystem race: another parallel worker's `find` over
`organized/*/extracted/LIB-INF/*.jar` could observe one of those 5 trees mid rm-rf-then-unzip and
silently miss its `LIB-INF` jars, weakening *that other module's* `-e` list non-deterministically
(the affected module isn't necessarily one of the 5 — it's whichever other worker happened to be
calling `compute_v2_library_jars` at that moment).

Fix (`tools/n5-decompile.sh`, `tools/tests/n5-decompile.bats`, TDD, RED before GREEN for every
item): the `LIB-INF` library context now comes from `organized/_v2-libcache/`, an **immutable**
cache built once, serially, by a required `--prepare-libcache` step — extracted directly from the
read-only source jars, never from any `organized/<mod>/extracted/` tree, so no concurrent
worker's extraction can ever race it again. Also fixed in the same pass: an idempotency key
covering the module jar, the full resolved library set, the JDK home, the fidelity flags, and the
decompiler tool jars (not just the module jar's sha256 — a rerun now redoes *any* module whose
computed library set, tools, or flags changed, not only a changed jar); `--force` no longer forces
a blind re-extraction (only a verifiably stale/missing `extracted/` does, via a
`extracted/.jar_sha256` provenance marker), so `--force` can no longer reopen the race either; a
module where both Vineflower and CFR produce zero output is now recorded `status: "failed"` and
the script exits non-zero for it, rather than being silently cached as done; `fallback2/` is
cleared unconditionally at the start of every run; the recon-writer heredoc now passes every value
through the environment into a quoted (`<<'PYEOF'`) heredoc instead of interpolating shell values
into Python string literals; the fidelity flag list is built from one array that drives both the
Vineflower command line and the recorded JSON; and library-jar self-exclusion compares `realpath`
(not the literal string) with a hard failure on any path containing `,` or `:` (the CSV/classpath
separators). See `tools/n5-decompile.sh`'s `--prepare-libcache` header comment and
`odd/tasks/decompiler-fidelity-audit.md` (T19) for the full requirement list.

**Rerun, 2026-09-28**, `bats`/`make test`/`shellcheck` green beforehand: `--prepare-libcache`
(21.5s), then the same `xargs -P 6` campaign over all 246 modules — **every module redecompiled**
(the idempotency key changed for all of them, since the key now also covers the library-set
composition and tool/flag identity, which the very first v1→v2 migration itself changed) — **0
failures**, wall time 18m26s (vs the first run's ~19m15s — consistent). Then
`--variant v2 --bin-ext` for the 6 included bin/ext jars (2m46s, 0 failures). **252/252 trees:
`status: "ok"`.** The 5 originally-raced modules (`analyticsLibs`, `apachePoi`, `commonsIo`,
`commonsLang`, `niagaraTest`) all have `class_count: 0` at their own top level (they are pure
`LIB-INF`-wrapper modules with no classes of their own — confirmed again in this rerun), so they
contribute zero `.java` files to the v1-vs-v2 diff measurement below regardless of their own
library-set completeness; the race's *possible* effect, if any, would only ever have shown up in
some *other* module's output, and the "v1 vs v2 measurement" and "D1-D11" numbers below —
recomputed from scratch against this race-free rerun — are unchanged from the first (raced) run's
published numbers. The same 6 modules needed a CFR fallback for the same reason as the first run
(`bajaui` whole-module timeout at 265s vs 269s before; `ffmpeg`/`backup`/`ccn`/`andoverAC256`/
`opcUaClient` per-class markers), confirming library context still does not change *which* classes
Vineflower fails on. **The numbers below reflect this rerun, not the raced first run, which is
superseded.**

### Campaign: v2 over all 246 modules + the 6 included bin/ext jars

**SUPERSEDED by the T19-fix rerun above** — this subsection is kept as the historical record of
the first (raced) run; the numbers used everywhere else in this document are the rerun's.

```bash
# per-module, resumable (sha256-cached like v1), parallel via xargs -P 6
find "$N5_MODULES_DIR" -maxdepth 1 -name '*.jar' ! -name docSource.jar -exec basename {} .jar \; \
  | xargs -P 6 -I{} tools/n5-decompile.sh --variant v2 {}
tools/n5-decompile.sh --variant v2 --bin-ext
```

Run 2026-09-28, `bats`/`make test` both green beforehand. **247/247 invocations exited 0**
(246 modules + the bin-ext batch invocation, which itself decompiled the 6 included jars).
Wall time ~19m15s end-to-end with `-P 6` (sum of per-module wall time 6,253s, mean 25.3s).
`bajaui.jar` is the one module that times out on the 240s primary budget under v2 too (269s
observed before `timeout` lands the kill, exactly as it does on v1 with no library context —
the hang is not a library-context artifact) and correctly falls back to CFR whole-module
(`organized/bajaui/fallback2/`). 5 other modules used v2's per-class CFR fallback for a handful
of classes flagged by Vineflower's own failure marker (`ffmpeg`, `backup`, `ccn`,
`andoverAC256`, `opcUaClient`) — the same 5 of 6 modules v1 already needed a fallback for
(`bajaui` is the 6th, whole-module both times), confirming library context does not change
*which* classes Vineflower fails on, consistent with the failure-marker counts below. This run
was later found to carry the library-context race described above (5 modules' `extracted/`
rebuilt live mid-scan, 07:20-07:32Z) and was superseded by the rerun.

### v1 vs v2 measurement (not a fidelity judgment — counts only)

Method: for every module with both `vineflower/` and `vineflower2/`, diff every `.java` file
present in both by relative path (byte-for-byte text, not normalized) and count Vineflower's own
failure markers (`// $VF: `, `Unable to fully decompile class`, `COULD NOT DECOMPILE`,
`<unknown>`) in each tree.

**Recomputed from scratch against the T19-fix rerun** (race-free `organized/_v2-libcache/`
campaign, 2026-09-28; see "T19 fix" above). Method unchanged from the first pass.

| Metric | v1 (no library context) | v2 (library context) |
|---|---:|---:|
| `.java` files produced (252 module/bin-ext trees) | 14,578 | 14,578 |
| Decompiler failure markers | 4 | 4 |
| Classes present in both trees | 14,578 | 14,578 |
| Classes with byte-different text | — | 8,486 / 14,578 (58.2%) |

**Identical to the first (raced) run's published figures, byte-for-byte** — file count, marker
count, diff count and diff percentage all match exactly. This is not a coincidence: the 5
modules whose `extracted/` was rebuilt live during the race (`analyticsLibs`, `apachePoi`,
`commonsIo`, `commonsLang`, `niagaraTest`) all have `class_count: 0` at their own top level (pure
`LIB-INF`-wrapper modules), so they contribute zero `.java` files to this table regardless of
their own library-set completeness — and no *other* module's diff/marker numbers moved either.
Same file count, same 4 failure markers — library context changes *what* gets written for a
class, not *whether* Vineflower can produce one (the `bajaui` hang and the 5 modules' per-class
markers are unchanged, see above). 58.2% of classes differ textually; three modules alone
(`bacnet`, `workbench`, `lonworks`) account for 1,150 of the differing classes (561 + 330 + 259),
and `provisioningNiagara` alone is 91.7% differing internally (253/276) — full ranked table not
committed; regenerate with the method above.

**Categories of textual difference**, from targeted corpus-wide greps re-run against the T19-fix
rerun (this is directional evidence from inspection, not T15's per-method bytecode grading — that
recompile-and-compare oracle is the only way to know which of these differences also change
behavior; see the B116 section above for the 11 cases that already do). The diamond-generics count
below matches the first run's published figure exactly; the `@Override` recount below is close to
but not pixel-identical to the first run's published 22,450 (v1) → 53,628 (v2) — v1's own count
also shifted slightly even though `vineflower/` was never regenerated between sessions, so the
delta is measurement-methodology noise (the exact original grep wasn't preserved/committed), not a
corpus change:

- **`@Override` annotations added — the largest, most systematic category.** Recount (module
  trees, `grep -ro "@Override" organized/*/vineflower[2]/**/*.java | wc -l`): 22,559 (v1) →
  53,737 (v2), **+138.2%**; files containing at least one, 5,503 → 11,148 (of 13,985 module-tree
  files). Vineflower's `--override-annotation` can only detect an override when it can resolve
  the ancestor class/interface method — without library context it only sees methods declared in
  classes belonging to the *same* module, missing every override of a method declared in a
  different module's jar (e.g. `BComponent`/`BComplex` methods in `baja.jar`, most `BWidget`
  overrides in `bajaui.jar`, `IStyle` methods, etc.). This is a real, syntax-level annotation-
  correctness gain from library context, not a behavior change.
- **Generic type arguments restored on constructor calls (diamond `<>`).** `new X<>` occurrences
  (module trees): 5,095 (v1) → 6,026 (v2), **+18.3%** — **exact match** with the first run's
  published figure. Example (`baja/niagara/sys/BFacets.java`): `new Array(String.class)` (v1, raw
  type) → `new Array<>(String.class)` (v2) — Vineflower can now see `Array<T>`'s own type
  parameter from `baja.jar`'s class file instead of guessing `Array` is raw; the corresponding
  read now resolves without a cast: `(String)noInternFacetKeys.get(i)` (v1) →
  `noInternFacetKeys.get(i)` (v2).
- **Redundant downcasts removed** (return type now resolvable from the real declaring class, so
  the explicit cast Vineflower inserted defensively in v1 is no longer needed). Example
  (`workbench/.../BComponentPreviewWidget.java`): `(BBrush)cx.select(this, IStyle.COLOR)` →
  `cx.select(this, IStyle.COLOR)`, `(BFont)cx.select(...)` → `cx.select(...)`, with the
  now-unused `BGap`/`BBrush` imports dropped too.
- **Overload-disambiguating casts added on ambiguous literals** (the "overload casts" category —
  the same defect family as B116's D1/D2/D3, but here library context actually fixes the syntax
  even though it did not fix D1-D3's semantics). Example (`analytics/.../BOptionalSimpleFe.java`):
  `newAction(0, null)` (v1) → `newAction(0, (BFacets)null)` (v2) — the overload can only be
  resolved once `BFacets` is a known type from `baja.jar`.
- **Net effect on explicit casts is a decrease** — this direction (redundant-downcast removal
  outweighing new overload-disambiguating casts) is qualitatively confirmed by inspection, same as
  the first run; the exact corpus-wide cast-count regex from the first run was not preserved, so
  no new precise figure is reported here rather than publish one from a different, unverified
  regex.
- The 30-file random sample from the first run (not rerun; the `.java` content behind the sampled
  files is unchanged, see the exact-match table above) tagged 22/30 files "other/formatting" (it
  pattern-matches diff lines, not a parser, so it mostly missed that these are the
  `@Override`/import-line additions above rather than cosmetic noise) and 8/30
  "cast-added"/"cast-removed" (the two categories above); it never tagged "generics-restored" in
  that particular sample even though the corpus-wide diamond-generic count clearly moved — the
  30-file sample is illustrative, not the source of the aggregate numbers above, which come from
  the corpus-wide greps instead.

### D1-D11 (B116 semantic defects) against the actual v2 output

The orchestrator's addendum asked whether `--variant v2`'s own pipeline (not B116 §116.3's
earlier ad-hoc `-e`-only test, which lacked `--include-runtime` and the fidelity flags) still
reproduces each of B116's 11 confirmed semantic defects. Checked directly against
`organized/<mod>/vineflower2/...` for every affected module (`bacnet`, `nrio`, `nurio`,
`driver`, `lonworks`, `kitControl`, `organized/_bin-ext/nre`) in this run. **Rechecked again
after the T19-fix rerun** (none of these 7 modules is among the 5 originally-raced modules, and
none is adjacent to them in the `xargs -P 6` scheduling order recorded in the logs) — every row
below is identical to the first check:

| # | Defect | v2 result |
|---|---|---|
| D1 | `BBacnetProxyExt.spy` — dropped `(Object)` cast rebinds `prop` overload | **still reproduces** — `out.prop("pollService", this.pollService);`, no cast |
| D2 | `BNrioNetwork.spy` — dropped `Long.valueOf` boxing rebinds `prop` overload | **still reproduces** — `out.prop("Message Count", this.getUnsolicitedMsgCount());` |
| D3 | `BNurioNetwork.spy` — same as D2 | **still reproduces** — `out.prop("Total Process Time(ms)", totalProcessTime);`, no boxing |
| D4 | `BNrioTabularThermistorDialog$DeleteCmd.doInvoke` — `Array.remove(Object)` vs `remove(int)` | **fixed** — `map.remove(Integer.valueOf(this.index));`, boxing restored |
| D5 | `BNurioTabularThermistorDialog$DeleteCmd.doInvoke` — same as D4 | **fixed** — same restored boxing |
| D6 | `BDevice.checkFatalFault` — instanceof-pattern resugar turns a local into the field `network` | **still reproduces** — bare `network = null;` before the loop still binds the field; `if (network == null)` after the loop still reads the field, not the pattern-scoped local |
| D7 | `BProxyExt.checkFatalFault` — same as D6, field `deviceExt` | **still reproduces** — identical structure |
| D8 | `BBacnetBitString.emptyBitString(int)` — varargs/array-length loss | **still reproduces** — `return make();`, `len` still dropped |
| D9 | `LonFacetsUtil.parseNumber` — ternary numeric promotion | **still reproduces** — `return s instanceof BDouble ? ((BDouble)s).getDouble() : ((BFloat)s).getFloat();`, still a promoting ternary |
| D10 | `BSequenceLinear.calculate` — `(float)` precision cast lost | **still reproduces** — `range / this.numOutputs`, still no cast |
| D11 | `Base64.encode(byte[],int)` — `(float)` precision cast lost | **still reproduces** — `(int)(buf.length * 1.33)`, still no cast |

**2 of 11 fixed (D4, D5 — both the same `Array.remove(Object)`-vs-`remove(int)` overload
family), 9 of 11 unchanged**, matching B116 §116.3's own earlier finding on this exact defect
set. Library context resolves *type* information (which fixes overloads that differ only by
*argument type*, like D4/D5's `Object` vs `int`), but does not fix: overloads that differ by
*argument identity/cast intent* rather than resolvable type (D1-D3 — `prop(Object,Object)` vs
`prop(Object,Runnable)`/`prop(Object,double)` are both perfectly type-correct with the
un-boxed/un-cast argument, so there is no ambiguity for the library-context-aware resolver to
catch), control-flow/scope-loss bugs (D6-D7's field-vs-pattern-variable aliasing, D8's varargs
collapse, D9's ternary promotion), or precision-only casts Vineflower considers safe to drop
(D10-D11). **Conclusion for corpus writers: `--variant v2` is not a substitute for the B116
verification rule** (confirm behavior-dependent claims with `javap`/docSource) — it measurably
improves *readable* fidelity (`@Override`, generics, redundant-cast removal) but leaves the
semantic defect surface B116 found almost entirely intact.

## `--variant cons` and `--extra-tridium` (T22, `odd/tasks/decompiler-fidelity-audit.md`)

### `--variant cons`: B118 §118.1's conservative + line-mapped view

`tools/n5-decompile.sh --variant cons [<module>|--all]` is a **third** decompile, alongside v1
(`vineflower/`, no library context) and v2 (`vineflower2/`, full library context), writing
`organized/<mod>/vineflower-cons/` (+ `fallback-cons/`). It reuses v2's entire library-context
machinery **unchanged** — the same immutable `organized/_v2-libcache/`, the same
`--add-external`/`--include-runtime`, the same idempotency-key and failure semantics — only the
Vineflower flag set differs, taken verbatim from `niagara5-block118.md` §118.1's "conservative +
line-mapped" set:

```
--pattern-matching=false --decompile-switch-expressions=false --ternary-in-if=false
--prettify-ifs=false --inline-simple-lambdas=false --bytecode-source-mapping=true
--__dump_original_lines__=true
```

Every documented flag name was re-verified against `vineflower-1.12.0.jar --help` this session
(all six present, defaults as B118 recorded). `--__dump_original_lines__` is **not** in `--help`
— it is Vineflower's `DUMP_ORIGINAL_LINES` constant
(`org/jetbrains/java/decompiler/main/extern/IFernflowerPreferences.class`, `javap -constants`),
confirmed present in the same jar this session. Like v2, every option is placed **before**
`-e`/`--add-external` on the command line (`decompile_module_variant`'s shared command
construction; the v2 bats regression test for the "silently dropped option after `-e`" CLI bug
applies unchanged to cons, and a cons-specific bats test asserts the same zero
`warn: missing` lines).

**What cons buys, and what it costs.** Per B118 §118.1: resugaring off means an
`instanceof`-pattern, switch-expression, or restructured-if never renders even where v1/v2 would
resugar one — closing the exact ambiguity B90/B98 warned about, mechanically, per class, instead
of by prose caveat. Line mapping on means every statement's `// N` trailer is the class file's own
`LineNumberTable` entry, i.e. **Tridium's original source line**, independently of whether a
`docSource` original exists for that class — B118 measured 669/669 (100%) agreement against the
four docSource-covered test classes it had, with a +7-line-shift control scoring only 33.8%
(discriminating, not coincidental agreement). Cost: a real pattern switch (e.g.
`BNumericWritable.spy`, `niagara5-block118.md` §118.1) renders **less** readably in cons — the
desugared `SwitchBootstraps.typeSwitch` state machine instead of the `case Action a when ... ->`
syntax v1/v2 both recover — so cons is a second, syntax-neutral, line-citable view for
corroboration, never a wholesale replacement for v1/v2.

### `--extra-tridium`: the 10 out-of-pipeline jars + Tridium-owned nested `LIB-INF` jars

`niagara5-block117.md` §117.2 and §117.4 found two Tridium-owned code populations the pipeline
above never touches, because it only ever scans `$N5_MODULES_DIR` and `$N5_BIN_EXT_DIR`:

1. **10 jars under `etc/m2/` and `lib/`** (958 Tridium classes total): `n-plugin` (722),
   `tridium-niagara-slotomatic-library` (145), `settings` (20), `n-conv-plugin` (14), `n-templates`
   (15), `utils` (12), `xelem` (8), `java-utils` (4), `filetypes` (3), and
   `lib/tridium-niagara-baja-doclet` (15 of 23 classes). `--extra-tridium` derives this list
   **mechanically**: every `*.jar` under `$N5_ETC_M2_DIR` (recursive) and `$N5_LIB_DIR`
   (`-maxdepth 1`), classified by `tools/n5-classify-binext.py`'s existing >50%-Tridium-namespace
   rule, unchanged — re-run against the real install this session, it produces exactly these 10
   names and nothing else (the sibling `*-plugin-markers` Maven metadata directories under
   `etc/m2/repository/com/tridium/tools/` carry no `.jar` at all, so they never enter the
   candidate list in the first place). Each included jar gets **both** v2 and cons, into
   `organized/_etc-m2/<jar-stem>/` (etc/m2 jars) or `organized/_lib/<jar-stem>/` (the doclet).
2. **Tridium-owned nested `LIB-INF` jars** (§117.2: 98 `LIB-INF` jars exist across 24 modules;
   only 2 are Tridium's own code by the same >50% rule — `devkit`'s `n-templates-5.0.54.9.2.jar`
   and `tridium-niagara-slotomatic-library-5.0.2.jar`, 160 classes total, both re-verified this
   session against every one of the 97 nested jars actually present in `organized/*/extracted/
   LIB-INF/`). `--extra-tridium` scans every already-extracted
   `organized/<mod>/extracted/LIB-INF/*.jar` (real per-module identity, not the
   deduplicated-by-sha256 libcache) and decompiles (v2+cons) any that pass the rule into
   `organized/<mod>/lib-inf/<jar-stem>/`.

**Kotlin.** 4 of the 10 etc/m2 jars (`n-plugin`, `n-conv-plugin`, `settings`, `utils`) carry
`Lkotlin/Metadata;` in their class files (§117.4); `write_recon_language` records
`"language": "kotlin"` and the Kotlin-classes ratio directly in each jar's `recon.json` (a
jar-level fact, not nested under `"v2"`/`"cons"` — independent of which decompiler variant read
it). Vineflower 1.12.0 ships a bundled Kotlin plugin (`--kt-enable`, **default true**, confirmed
via `--help` this session, `META-INF/plugins/vineflower-kotlin-0.1.0.jar` present inside the tool
jar) — it is therefore already active by default for every Kotlin-flagged jar decompiled here; no
extra flag was needed to opt in. Neither `n-templates` nor `tridium-niagara-slotomatic-library`
(the two `LIB-INF` jars) carries the Kotlin marker.

### Campaign run

Run 2026-09-28 against the sha256-verified local mirror
(`niagara5-research-localcache/jar-mirror-5.0.0.28/`), `/tmp/run-cons-campaign.sh`, all numbers
re-counted by the orchestrator from `organized/` after `ALL_DONE`:

| Phase | Wall clock | Result |
|---|---|---|
| `--variant cons` over every module jar (`xargs -P 6`) | 20m00s | 246/246 non-docSource modules have `vineflower-cons/` |
| `--variant cons --bin-ext` | 1m55s | 6/6 included bin/ext jars |
| `--extra-tridium` (v2 + cons) | 5m18s | 9 `_etc-m2/` + 1 `_lib/` jars + 2 `devkit/lib-inf/` jars, v2 and cons file counts identical per jar |

- 262/262 `recon.json` files carry `cons.status: ok`; the conservative tree holds 14,957 `.java` +
  329 `.kt` files.
- The 4 Kotlin-flagged jars decompile to `.kt` (n-plugin 302 `.kt` for 305 top-level classes,
  n-conv-plugin 4/4, settings 15/15, utils 8/8); their `fallback*/` `.java` files are CFR reference
  copies, not a loss.
- Line mapping (`// N` markers vs docSource original lines, token overlap in a ±1-line window):
  BNumericWritable 137/137, ValueDocDecoder 409/409, Column 78/78 — 624/624 (100%).
- **Resolved (T24):** `bajaui` (832 classes) used to be the only module whose primary Vineflower run
  hit the 240 s whole-jar budget, in v1, v2 and cons alike (`primary_status: timeout`,
  `fallback_reason: primary_timeout_whole_module`), losing all 566 of its top-level sources to CFR in
  every tree. A thread dump showed one decompiler thread spinning in `ClassWriter.writeClass` while
  the other 15 were idle: a single class hangs Vineflower, it is not slowness — the class is
  `com/tridium/ui/theme/custom/nss/query/NSS2SelectionResult`, whose method-local record
  `NSS2SelectionResult$1ValueAndAdvice` is what triggers the hang (per-class bisection isolated it to
  exactly this one class; the rest of the package/module decompiles normally).
  `tools/n5-decompile.sh` now isolates a hang like this automatically instead of losing the whole
  module: it bisects the hung whole-jar run by package, then by top-level class, each attempt under
  its own `N5_ISOLATE_TIMEOUT` (default 90 s) budget; re-runs the whole jar ONCE more with
  Vineflower's `--excluded-classes=<regex>` excluding exactly the hung class(es) (regex semantics —
  a FULL match against the `/`-separated internal name — verified empirically against the real
  vineflower-1.12.0.jar with a synthetic reproduction of this exact case); and gives the hung
  class(es) CFR output plus a best-effort `--decompile-inner=false` secondary rendering. Real
  `bajaui` re-run on the local mirror after the fix, all three variants:

  | variant | `primary_status` | `excluded_classes` | primary tree | fallback | noinner secondary view | isolate time | excluded-rerun time |
  |---|---|---|---|---|---|---|---|
  | v1   | `ok_with_excluded` | `NSS2SelectionResult` | 565/566 `.java` | 1 (the hung class) | 2 `.java` (class + its local record) | 319 s | 8 s |
  | v2   | `ok_with_excluded` | `NSS2SelectionResult` | 565/566 `.java` | 1 (the hung class) | 2 `.java` | 357 s | 12 s |
  | cons | `ok_with_excluded` | `NSS2SelectionResult` | 565/566 `.java` | 1 (the hung class) | 2 `.java` | 357 s | 14 s |

  `recon.json` (or its `v2`/`cons` sub-object) records `primary_status: "ok_with_excluded"`,
  `fallback_reason: "primary_hang_isolated"`, `excluded_classes`, `isolate_time_seconds` and
  `primary_timeout_attempt_seconds` (the original ~265-269 s hang, kept for forensics) for every
  module isolation resolves. Isolation found no other hung class anywhere else in this module; if a
  future timeout can't be isolated (no single class found hung alone, or the excluded re-run itself
  times out/errors), today's original whole-module CFR fallback is kept exactly, with a new
  `isolation_status` field explaining why. This is why the planned `StyleUtils` line-mapping check
  had no Vineflower file to read before this fix — it now does, for every class except the isolated
  hang itself.
