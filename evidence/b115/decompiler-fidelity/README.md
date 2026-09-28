# Decompiler-fidelity experiment (T1 of `odd/tasks/decompiler-fidelity-audit.md`)

Cited from [Block 115] (§115.1/§115.2). Two independent probes:

1. `old/` vs `new/` — ten old-vs-new Java idiom pairs (`inst`, `v`, `tb`, `ef`, `efi`, `sw`, `ss`, `cat`,
   `lam`, `tsw` in `old/F.java` / `new/F.java`), compiled separately, `javap`-diffed.
2. `constinline/` — one compile-time-constant-inlining pair (`K.HOST` referenced from `U.h()`),
   proving R7's target failure shape: Vineflower renders the inlined literal, not the constant
   reference, and this is **not** a decompiler artifact — `javap` shows the same `ldc` the JVM
   actually executes.

## 1. Idiom-pair probe (`old/`, `new/`)

`old/F.java` writes each of 10 constructs the classic way; `new/F.java` writes the same 10 constructs
using the modern Java-21+ syntax. Both compiled and disassembled **twice** (without and with `-g`, to
check whether `LocalVariableTable`/debug info changes the answer):

    JAVAC=/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac   # 25.0.4.1
    JAVAP=/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap

    $JAVAC --release 25 -d old/out old/F.java   &&  $JAVAP -c -p        old/out/F.class > old/javap.txt
    $JAVAC --release 25 -g -d old/g   old/F.java   &&  $JAVAP -c -l -p     old/g/F.class   > old/javap-g.txt
    $JAVAC --release 25 -d new/out new/F.java   &&  $JAVAP -c -p        new/out/F.class > new/javap.txt
    $JAVAC --release 25 -g -d new/g   new/F.java   &&  $JAVAP -c -l -p     new/g/F.class   > new/javap-g.txt

### Result summary (full detail: `odd/tasks/decompiler-fidelity-audit.md` "Progress / evidence" §T1)

**Bytecode-IDENTICAL** (with and without `-g` — javap alone can never distinguish these; only a
docSource original or a non-resugaring decompiler like CFR can):
- `instanceof` pattern (`if (o instanceof String s)`) vs. classic `instanceof` + cast
- `var` vs. an explicit type
- text block vs. concatenated string literals
- `a + b` string concatenation (both compile to the same `invokedynamic StringConcatFactory` call —
  a **compile-target** signal, not a source-syntax signal)

**Bytecode-DISTINGUISHABLE**:
- array for-each: `javac` copies the array reference and caches its length into synthetic locals —
  visible even without `-g`
- `Iterable` for-each **with `-g`**: the classic explicit-`Iterator` form (`old/`, method `efi`) HAS a
  named iterator entry in `LocalVariableTable`; the for-each form (`new/`, method `efi`) has NO such
  entry (heuristic — requires `-g`). From `old/javap-g.txt`:
  ```
        Start  Length  Slot  Name   Signature
           28       7     3     s   Ljava/lang/String;
            9      29     2    it   Ljava/util/Iterator;
            0      40     0     l   Ljava/util/List;
            2      38     1     t   I
  ```
  vs. `new/javap-g.txt` (same slot 2 that held `it` above is absent — no name is ever assigned to it):
  ```
        Start  Length  Slot  Name   Signature
           28       7     3     s   Ljava/lang/String;
            0      40     0     l   Ljava/util/List;
            2      38     1     t   I
  ```
- arrow switch / switch expression: value-on-stack-then-single-store/goto shape (heuristic, weaker
  than the others — say so whenever cited)
- lambda: `invokedynamic LambdaMetafactory`, no `F$1` inner class (vs. an anonymous class, which
  always compiles to a real `$1` class file)
- pattern switch: `typeSwitch`/`SwitchBootstraps` `invokedynamic`

**Confirms this corpus's real N5 classes ship WITH debug info**: `control.jar`'s
`niagara/control/BNumericWritable.class` carries 62 `LocalVariableTable` + 63 `LineNumberTable`
entries (major version 69) — so the `-g`-dependent distinctions above are actually usable against the
real corpus, not just this synthetic probe.

**Correction to the orchestrator's own first restatement of this rule** ("enhanced for is
indistinguishable"): wrong — enhanced (array/`Iterable`) for-each IS bytecode-distinguishable, per
above. Caught only by running this experiment, which is the entire reason T8-T11 exist: a prose rule
already failed once before this one did too.

## 2. Constant-inlining probe (`constinline/`)

`constinline/K.java` declares `public static final String HOST = "cloud.example.test";`.
`constinline/U.java` references it as `K.HOST` from `U.h()`. Compiled with the same `javac 25.0.4.1`,
then both disassembled and separately decompiled with Vineflower (the corpus's primary decompiler,
`tools/decompilers/vineflower-*.jar`):

    $JAVAC --release 25 -d out constinline/K.java constinline/U.java
    $JAVAP -c -p out/K.class > constinline/javap-K.txt
    $JAVAP -c -p out/U.class > constinline/javap-U.txt
    java -jar tools/decompilers/vineflower-*.jar out/U.class vf/   # -> constinline/U-vineflower-decompiled.java

### Result

`constinline/javap-U.txt` shows `U.h()`'s body is `ldc #9 // String cloud.example.test` — the JVM
never reads `K.HOST` at runtime; `javac` inlined the compile-time constant into `U.class` directly, per
JLS §4.12.4/§13.1. `constinline/U-vineflower-decompiled.java` shows Vineflower rendering that same
literal (`return "cloud.example.test";`), **not** `return K.HOST;` — because there is nothing left in
the bytecode pointing back at `K.HOST` for Vineflower to reconstruct.

This is the mechanism behind the real corpus's dead-constant/shadow-literal sweep (B85-G1, [Block 96]
§96.5, [Block 105] §105.8, ~3,623 candidates): a "constant is dead, shadowed by a literal duplicate"
finding needs to rule out compile-time inlining of THAT SAME constant before it's read as a genuine
maintainability bug — the shadow literal may just be javac's own compiled form of the constant, not
an independent hand-typed duplicate. `tools/lint-block.py`'s **R7** enforces citing this kind of
evidence (`ldc`, "compile-time constant", `JLS 4.12.4`/`JLS 13.1`, or `docSource`) before asserting
that shape as a finding.
