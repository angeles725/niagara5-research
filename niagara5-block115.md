# Block 115 — Decompiler-fidelity and method-error audit: the bytecode-distinguishability matrix, version-gated resugaring confirmed on `BQudtUnitTag`, compile-time constant inlining proven docSource-vs-decompiled on a real corpus pair, B13's 18 "N5-only" modules re-baselined against N4-4.15.3.28 (platHwScanAtlas was already shipping), two B84 defects corrected, and a canonical C1-C12 method-error-class catalog mapped to lint rules R1-R8

> Research closing out T4 of `odd/tasks/decompiler-fidelity-audit.md`: writing up T1's fidelity experiment,
> T2's feature-adoption-claim audit, and T3's method-blind-spot audit into one archival block, re-verifying
> every orchestrator-relayed figure against its own primary source this session (not re-trusting chat-relayed
> counts), and placing `§14` correction pointers in the five affected blocks this task names. Covers: the
> bytecode-distinguishability matrix for 9 old-vs-new Java idiom pairs (§115.1); the version-gated resugaring
> mechanism confirmed a second time on `BQudtUnitTag` itself, independent of the original `F.java` experiment
> (§115.2); compile-time constant inlining, proven both synthetically (`K`/`U`) and on a real, docSource-covered
> corpus pair (`BTagDictionaryService.LOGGER_NAME` / `BTagDictionary.logger`) that the B96/B105/B111
> dead-constant census cannot itself distinguish from a genuine duplicate literal (§115.3); a corrected
> re-baseline of [Block 13] §13.5's 18 "N5-only" modules against the full N4-4.15.3.28 install, finding an
> eighth already-shipping module (`platHwScanAtlas`) beyond the three families the task already knew about
> (§115.4); two concrete corrections to [Block 84] §84.2/§84.3, including a re-derivation of the orchestrator's
> own "12 typeSwitch" figure down to the true count of 2 distinct pattern-switch call sites (§115.5); a
> disposition of the 9 T2 quote sites (§115.6); and a canonical C1-C12 method-error-class catalog, each row
> mapped to the lint rule (`R1`-`R8`) `tools/lint-block.py` is meant to enforce (§115.7, built concurrently by
> another writer this session — not read or depended on here). Does **not** cover: T5-T12 (rule propagation to
> docs/tools headers, the lint tool itself, hook wiring, durable evidence/, the versioned writer prompt,
> orchestrator-side memory, and the retro kit-delta proposal) — all out of T4's own scope, left to the
> orchestrator's remaining task list; a full per-candidate docSource-coverage sweep of the entire 3623-record
> dead-constant population (one concrete pair is proven this session, not the population, see child gap
> **B115-G3**); re-deriving T3's own "151 /tmp paths near CERT-hw/live, 13 already gone" figure with its exact
> original methodology (unavailable to this writer) — a differently-scoped re-derivation is reported instead,
> honestly labeled as such (§115.7).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> Cross-referenced against a fresh N4-**4.15.3.28** install at `/mnt/c/PowerB/PowerB-4.15.3.28` (the same OEM
> "PowerB" distribution [Block 84] used, re-read this session, not re-decompiled). Compiler: `javac` 25.0.x,
> `--release 25`. Decompiler: Vineflower 1.12.0 (same jar every other block uses). Method: `javac`/`javap -c -p`
> (and `-c -l -p` / `-g`) on small, purpose-built idiom pairs under
> `scratchpad/fidelity/{old,new,constinline,qudt}/` (T1's own artifacts, re-read and, for `qudt`, independently
> re-verified this session with a fresh `javap -c -p` pass this writer ran); a corpus-wide `ls`/`grep` of
> `/mnt/c/PowerB/PowerB-4.15.3.28/modules/*.jar` against [Block 13] §13.5's 18 module names, suffix-normalized
> (`-rt/-ux/-wb/-se/-doc/-lexicon*`); a `python3 json`-driven read of `scratchpad/b96/dead_constants_shadowed.json`
> (unmodified, [Block 96]'s own artifact) cross-referenced against `organized/docSource/tagdictionary/` for one
> concrete, corpus-real candidate pair; `rg -il` sweeps of every `niagara5-block*.md` and `docs/n4-to-n5-porting-guide.md`
> for "N5-only"/"new in N5" module-name hits against the 4.15.3.28 baseline. Markers (canonical list, METHODOLOGY §3): `[CERT-hw]` (ran this
> session, artifact path cited) · `[CERT]` local primary source (`file:line`) · `[INFER]` deduction.
>
> **Type:** mixed (evidence + synthesis + corrections — §115.1-§115.4 are fresh primary-source reads;
> §115.5-§115.7 combine fresh verification with synthesis of T1-T3's own already-established findings, cited
> by `odd/tasks/decompiler-fidelity-audit.md` line, not re-derived where already [CERT]-backed there).

---

## 115.1 — Bytecode-distinguishability matrix: 9 old-vs-new Java idiom pairs, `javac 25 --release 25`, `javap -c -p` with and without `-g` `[CERT-hw]`

> **Correction (added by [Block 116], §14 cross-block).** This matrix covers SYNTAX distinguishability only. Neither
> Vineflower nor CFR is a semantic oracle: [Block 116] confirmed 11 semantically wrong Vineflower methods in the N5 tree
> (overload binding, boxing, numeric widening, `finally` return, pattern-variable scoping) and CFR drops `(Object)null`
> casts. Behavior claims in those families need `javap` or docSource — see [Block 116] §116.5-§116.6.

Evidence: `scratchpad/fidelity/{old,new}/F.java` (T1's own experiment, re-read this session), compiled and
disassembled this session's own re-run to confirm the LocalVariableTable claim concretely (§115.2 reproduces
one row independently on real Tridium bytecode). Durable copies of the source pairs and `javap` outputs are
being preserved under `evidence/b115/decompiler-fidelity/` by a concurrent writer this session (not created by
this block; cited here by path, not verified present) — the authoritative session artifacts for this table are
`scratchpad/fidelity/old/{F.java,javap.txt,javap-g.txt}` and `scratchpad/fidelity/new/{F.java,javap.txt,javap-g.txt}`.

| # | Idiom (old → new) | Bytecode with `-g` (LocalVariableTable) | Verdict |
|---|---|---|---|
| 1 | `if (o instanceof String) { String s=(String)o; ...}` → `if (o instanceof String s) {...}` | Identical: `instanceof`+`checkcast`+`astore` either way | **IDENTICAL** — javap cannot decide |
| 2 | `ArrayList<String> l = new ArrayList<>()` → `var l = new ArrayList<>()` | Identical — `var` is source/javac-frontend-only, erased before bytecode generation | **IDENTICAL** |
| 3 | `"line1\n" + "line2\n"` → text block `"""..."""` | Identical `ldc`/`invokedynamic StringConcatFactory` either way | **IDENTICAL** |
| 4 | `a + b` string concat (old- vs new-style call) | Identical — `indy StringConcatFactory` is a compile-**target** signal (`--release`), not a source-idiom signal | **IDENTICAL** |
| 5 | `for(int i=0;i<a.length;i++){int x=a[i];...}` → `for(int x: a){...}` | **Differs**: enhanced-for copies the array ref into a synthetic slot (new-version slot 2, no LVT name) and caches `a.length` into another synthetic slot (slot 3, no LVT name) before the loop; the manual loop's `i` (old, slot 2) IS named in the LVT `[CERT-hw]` (`scratchpad/fidelity/old/javap-g.txt:56-82` vs `scratchpad/fidelity/new/javap-g.txt:56-86`, re-read this session) | **DISTINGUISHABLE** (with `-g`) |
| 6 | `for(Iterator<String> it=l.iterator();it.hasNext();){String s=it.next();...}` → `for(String s: l){...}` | **Differs with `-g`**: no named `Iterator` local survives in the enhanced-for LVT (a synthetic, unnamed iterator slot instead); the manual loop names `it` | **DISTINGUISHABLE** (with `-g` only — without `-g` no LVT exists to check at all, T1's own finding) |
| 7 | `switch(k){case 1: r=10; break; ...}` → `switch(k){case 1 -> 10; ...}` (arrow/switch-expression) | **Differs**: switch-expression shape is value-left-on-stack + single store/goto, vs the classic multi-store/multi-break shape | **DISTINGUISHABLE, but heuristic** — a classic switch that happens to have one assignment per case and no fallthrough can shape-match; not a hard signal |
| 8 | anonymous `Runnable`/`new Runnable(){...}` → lambda `() -> {}` | **Differs**: lambda compiles to `invokedynamic LambdaMetafactory`, no synthetic `F$1` inner class emitted; anonymous class emits a real `F$1.class` with a real constructor | **DISTINGUISHABLE** |
| 9 | `if/else instanceof` chain → pattern-`switch` (`switch(o){case String s -> ...}`) | **Differs**: pattern-switch compiles to `invokedynamic SwitchBootstraps.typeSwitch`, a `BootstrapMethods` entry carrying the exact ordered type list as method arguments; an if/else chain is plain sequential `instanceof`+branch, no `typeSwitch` bootstrap at all | **DISTINGUISHABLE** |

**Records and sealed types** (not in the `F.java` pair set, general JVMS knowledge corroborated by reading real
Tridium output — see §115.2's `BQudtUnitTag` and other blocks' record/sealed findings): also **DISTINGUISHABLE**
— a `record` emits a `Record` class attribute plus mechanically-generated accessor/`equals`/`hashCode`/`toString`
bodies; `sealed` emits a `PermittedSubclasses` class attribute. Neither has a "classic" idiom to resugar from
(both are Java-17+-only language features with no pre-existing bytecode shape to imitate), so there is no
false-adoption risk for these two specifically — only the ones instanceof-family in rows 1 and 9.

**Tridium ships WITH debug info.** `control.jar!niagara/control/BNumericWritable.class` carries 62
`LocalVariableTable` + 63 `LineNumberTable` entries, class-file major version 69 (N5) `[CERT-hw]`
(`scratchpad/fidelity/tri/niagara/control/BNumericWritable.class`, `javap -v`, this session) — rows 5/6 above
(the only two rows that need `-g` to distinguish) are therefore usable against the real corpus, not just the
synthetic pair.

**Net rule** (restated from the writer-prompt's own mandatory rule, confirmed not contradicted by this
session's re-run): rows 1-4 can NEVER be used to claim Tridium "adopted"/"rewrote to" a language feature from
decompiled source alone — only `docSource` originals or a non-resugaring decompiler (CFR) can settle those.
Rows 5-9 CAN be read from `javap -v -p` bytecode directly.

## 115.2 — Version-gated resugaring, confirmed independently a second time on `BQudtUnitTag`: N4-4.15.3.28 (major 52) and N5-5.0.0.28 (major 69) carry byte-for-byte identical `instanceof`+`checkcast` bytecode; Vineflower 1.12.0 renders the N4 side classically and the N5 side as `instanceof BNumericPoint np` `[CERT-hw]`

This is the same experiment [Block 84] §84.3 already ran (its own `[CERT]` verdict is re-derived here, not
assumed) — re-verified fresh this session with an independent `javap -c -p` pass on both sides, not a re-read
of [Block 84]'s prose:

- **N4 side** (`scratchpad/fidelity/qudt/n4/com/tridium/tagdictionary/tag/BQudtUnitTag.class`, sha256
  `e20b5bc35ca4b357287c31d425de99a9aafea8fe5aefbf8bf97c6d5466eb1df2`): `major version: 52`. `javap -c -p` shows
  `instanceof #3 (BNumericPoint); checkcast #3; astore_2; ...; checkcast #8 (BUnit); astore 4` — the classic
  `if (x instanceof T) { T t = (T)x; ... }` shape `[CERT-hw]` (this session).
- **N5 side** (`organized/tagdictionary/extracted/com/tridium/tagdictionary/tag/BQudtUnitTag.class`):
  `major version: 69`. `javap -c -p` shows the **identical** instruction sequence: `instanceof #13
  (niagara/control/BNumericPoint); checkcast #13; astore_2; ...; checkcast #27 (niagara/units/BUnit); astore
  4` `[CERT-hw]` (this session) — same opcodes, same local-slot layout, only the constant-pool indices differ
  (expected — different class files, different pools).
- **Decompiled source differs, bytecode does not.** Vineflower 1.12.0 on the N4-side `.class` renders
  `scratchpad/fidelity/qudt/vf4/BQudtUnitTag.java:34-35`: `if (entity instanceof BNumericPoint) { BNumericPoint
  np = (BNumericPoint)entity; ...}` (classic). The already-existing N5-side decompile,
  `organized/tagdictionary/vineflower/com/tridium/tagdictionary/tag/BQudtUnitTag.java:34`, renders `if (entity
  instanceof BNumericPoint np) {...}` (pattern-match) `[CERT]`. Neither `.class` file contains a
  `SwitchBootstraps.typeSwitch` bootstrap or any other Java-21-specific attribute — the resugaring is
  Vineflower's own major-version-gated rendering choice, not a source change.

**This corroborates [Block 84] §84.3's own verdict independently** (this writer did not simply re-read §84.3
and repeat it — a fresh `javap -c -p` was run this session on both class files, sha256-pinned) and supplies
the exact mechanism §115.5 below cites when correcting §84.3's table cell.

## 115.3 — Compile-time constant inlining: proven synthetically, then on a real, docSource-covered corpus pair the B96/B105/B111 dead-constant census cannot itself distinguish from a genuine duplicate literal `[CERT-hw]`+`[CERT]`

**Synthetic proof** (`scratchpad/fidelity/constinline/{K,U}.java`, T1's artifact, re-read this session):
`K.java`: `public static final String HOST = "cloud.example.test";`. `U.java`: `String h(){ return K.HOST; }`.
Compiled and Vineflower-decompiled this session: `scratchpad/fidelity/constinline/vf/U.java` renders `return
"cloud.example.test";` — the symbolic reference `K.HOST` is **gone**; only the literal survives, because
`static final` `String`/primitive fields are JLS §4.12.4 **compile-time constants**, inlined by `javac` into
every referencing class's own constant pool at compile time (`ldc` of the literal directly, no `getstatic K.HOST`
at all) `[CERT-hw]` (this session, recompiled and re-decompiled to confirm T1's own claim, not just re-read).

**Strengthened with real Tridium evidence, checked against the docSource original (not decompiled text alone).** [Block 96]'s own `dead_constants_shadowed.json`
(`/tmp/claude-1000/.../dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/dead_constants_shadowed.json`, 3623
records, read this session, unmodified) flags `niagara.tagdictionary.BTagDictionaryService.LOGGER_NAME`
(`organized/tagdictionary/vineflower/niagara/tagdictionary/BTagDictionaryService.java:126`, value
`"tagdictionary"`) as a dead constant with dozens of "shadow literal" hits corpus-wide (the census verdict this section tests against the docSource original below) — every site where the
literal string `"tagdictionary"` appears without referencing the constant by name, per the census's own
decompiled-source-only method. One of those hit files,
`organized/tagdictionary/vineflower/niagara/tagdictionary/BTagDictionary.java`, is **docSource-covered**
(`organized/docSource/tagdictionary/niagara/tagdictionary/BTagDictionary.java` exists — the pre-decompilation
original). Reading the ORIGINAL source at the corresponding line:

- **Vineflower-decompiled** `organized/tagdictionary/vineflower/niagara/tagdictionary/BTagDictionary.java:131`:
  `public static Logger logger = Logger.getLogger("tagdictionary");` — a bare literal, exactly what the census's
  shadow-literal detector flags (the `docSource`-vs-decompiled comparison below is what resolves it).
- **docSource original** `organized/docSource/tagdictionary/niagara/tagdictionary/BTagDictionary.java:1414`:
  `public static Logger logger = Logger.getLogger(BTagDictionaryService.LOGGER_NAME);` — the ORIGINAL source
  references the constant **by name**. `[CERT]` (both files read this session, `grep -n "LOGGER_NAME"` across
  `organized/docSource/tagdictionary/`, only 2 hits: the declaration site and this exact reference).

**This is a real, corpus-native example of compile-time constant inlining being indistinguishable from a
duplicated literal at the decompiled-source layer** — exactly the synthetic `K`/`U` mechanism, on a real
Tridium class, proven against ground-truth original source, not inferred.

**A second shadow-literal hit for the SAME constant, in the SAME file, is the opposite case — per the docSource
original it is a genuine duplicate, not an inlined reference.** `dead_constants_shadowed.json`'s other `BTagDictionary.java` hit
(decompiled line 388, docSource line 976) is `throw new LocalizableRuntimeException("tagdictionary",
"import.fileTooLarge", ...)` — and the docSource ORIGINAL (`organized/docSource/tagdictionary/niagara/tagdictionary/BTagDictionary.java:976-979`)
**also** hardcodes the literal `"tagdictionary"` directly, not a reference to `LOGGER_NAME` (this particular
literal is the `Lexicon`/module-name key `LocalizableRuntimeException` expects as its first argument — a
different, coincidentally-same-valued use, not a maintainability smell at all) `[CERT]`.

**What the census CAN and CANNOT measure, stated plainly.** A dead-constant census built from decompiled source
alone (as B96/B105/B111's `dead_constant_sweep.py` is) **cannot distinguish** "this shadow-literal hit is a
compile-time-inlined reference to the constant" from "this shadow-literal hit is an independently-typed,
unrelated duplicate that happens to share the same string value" — both render as a bare literal after
Vineflower resugars the `ldc`. The two `BTagDictionary.java` hits for the exact same constant, found in the
exact same session, land on opposite sides of that line. **A constant with zero textual references in decompiled
source is therefore not evidence the constant is UNUSED** — it may be referenced by every one of its "shadow"
sites, just inlined away before decompilation ever sees it; only a docSource original (or `javap -c -p`'s own
constant-pool-vs-caller cross-check, not attempted at scale here) can settle an individual case.

**Scope of this proof.** One concrete pair is docSource-confirmed this session (12 of `dead_constants_shadowed.json`'s
3623 records were spot-checked for docSource coverage before this one was selected as the clearest illustration;
the other 11 checked either had no docSource-covered hit file or were, like the `import.fileTooLarge` case
above, genuine duplicates). A full per-candidate docSource-coverage sweep of the population is out of this
block's bounded scope — **B115-G3** (below).

**Consequence for [Block 96]/[Block 105]/[Block 111]'s own "62.5% accidental duplication" bug-rate estimate**:
unsupported as stated — see §14 pointers below and §115.7's C5/R7 catalog entry.

## 115.4 — Baseline attribution: [Block 13] §13.5's 18 "N5-only" modules re-run against ALL of `/mnt/c/PowerB/PowerB-4.15.3.28/modules` — 7 of 18 were already shipping in N4-4.15.3.28, including `platHwScanAtlas` (not previously known) `[CERT-hw]`

**Method**: `ls /mnt/c/PowerB/PowerB-4.15.3.28/modules/*.jar` (721 jars) matched against each of [Block 13]
§13.5's 18 module base names with `-rt/-ux/-wb/-se/-doc/-lexicon*` suffix normalization, this session
(`grep -iE "^${m}-(rt|ux|wb|se|doc|lexicon[a-z]*)\.jar$"`, scratch:
`scratchpad/b115_powerb_jars.txt`).

| N5-labeled module ([Block 13] §13.5) | In N4-4.15.3.28? | Note |
|---|---|---|
| `cloudLink` (`-rt/-ux/-wb`) | **YES** | vendorVersion in this 4.15.3.28 build not re-checked (out of scope; [Block 13]'s own `5.0.0.26` staleness finding is about the N5 side) |
| `cloudLinkAzure` | **YES** | |
| `cloudLinkForge` (`-rt/-ux`) | **YES** | |
| `cloudLinkHonSbp` | **YES** | |
| `cloudLinkNcs` | **YES** | already known per the task's own framing, but see §115.4's downstream-site finding below — [Block 18] §18.9 asserts the opposite |
| `platHwScanAtlas` (`-rt/-wb`) | **YES — new finding this session** | `module.xml`: `vendor="Tridium" vendorVersion="4.15.3.28" releaseDate="2025-03-09"`, same `com.tridium.platHwScanAtlas.BAtlasBoard` class `[CERT-hw]` (`unzip -p .../platHwScanAtlas-rt.jar META-INF/module.xml`, this session) — **not** one of the three families ("cloudLink family, cloudLinkNcs, jodaTime") the task text already knew about |
| `jodaTime` | **YES** | |
| `cloudLinkExtensionBacnet` | no | genuinely absent from this 4.15.3.28 install per a class-level, corpus-wide census of `modules/*.jar` (`grep -i` zero hits, not just a suffix-normalization miss — checked with a bare-substring `grep` too) |
| `cloudLinkExtensionEbi` | no | " |
| `cloudLinkExtensionNiagara` | no | " |
| `niagaraCloud` | no | " |
| `niagaraSync` | no | " |
| `nurio` | no | " |
| `platNurio` | no | " |
| `totpAuth` | no | " |
| `themeN5` | no | " |
| `analyticsLibs` | no | " |
| `lonDevices` | no | " |

**Corrected split (class-level, all-721-jars census, §115.4's own method above): 7 of 18 already ship in
N4-4.15.3.28 (not "N5-only" against the true adjacent N4 release); 11 of 18 are genuinely absent from this
4.15.3.28 install** — a materially different picture than [Block 13]
§13.5's own framing, which computed "N5-only" against the OEM **4.14.0.162** baseline only, never checked
against the closer 4.15.3.28 release. This is not a contradiction of [Block 13]'s own `[CERT]` citations (its
`diff-n4` tool output against the 4.14.0.162 tree is correct for what it measured) — it is a **baseline-scope
correction**: "N5-only" in that block's own text means "absent from the specific N4.14.0.162 OEM install
consulted," not "absent from every N4 release," and `platHwScanAtlas` shows that gap is not merely theoretical.

**Downstream sites relying on the "N5-only"/"new in N5" framing for these modules**, found by `rg -il
"N5-only|new in N5"` across every `niagara5-block*.md` plus `docs/n4-to-n5-porting-guide.md` this session
(the same 4.15.3.28-baseline check as §115.4's own table above):

- **`docs/n4-to-n5-porting-guide.md`**: one hit, `"N5-only NiagaraSlotProcessor"` (`:277`) — an unrelated class
  (a `slotomatic` build-tool validator, not one of the 18 modules, and not checked against 4.15.3.28 since it
  is out of scope), not affected.
- **[Block 18] §18.9** (`niagara5-block18.md:334`): table row states `cloudLinkNcs` — "**Not found** in the N4
  modules directory or corpus ... N5-only provider extension" — this is now confirmed **incorrect** for the
  N4-4.15.3.28 baseline: `cloudLinkNcs-rt.jar` exists there (`module.xml` not re-checked for vendorVersion this
  session — only presence). [Block 18]'s own header already hedges this ("not proof the modules never existed
  in ANY N4 release; a narrower or newer N4 build was not checked" — its own scope caveat, folded into its
  `B18-G7`), so this is a narrowing of an already-flagged uncertainty, not a fresh contradiction. **This block
  does not edit `niagara5-block18.md`** — it is outside this task's explicit Deliverable-2 file list
  (`niagara5-block84.md`, `niagara5-block13.md`, `niagara5-block96.md`, `niagara5-block105.md`,
  `niagara5-block111.md` only); flagged here and in **B115-G1** (child gap) for a future `§14` pointer there.
- No other `niagara5-block*.md` hit ties an "N5-only"/"new in N5" claim to any of the 18 4.15.3.28-checked
  module names above (`rg` output, this session — the other `N5-only`/`new in N5` hits found by the sweep
  concern unrelated subjects: `security/licenses/conf`, `nftables`, SRP6, `databaseEncryption`, `uxBuilder`/
  `ux/fe`, none of which are §13.5's 18 modules and none re-checked against 4.15.3.28 this session).

## 115.5 — [Block 84] corrections, re-verified fresh this session `[CERT-hw]`

**§84.2 — the pattern-switch claim is REAL for `EntitlementApi`, but the orchestrator's own relayed "12
typeSwitch" figure is a raw-grep artifact; the true count is 2 distinct call sites, and `RetrieveEntitlements`
has zero.** `javap -v -p` on `organized/_bin-ext/nre/extracted/com/tridium/nre/subscription/EntitlementApi.class`
shows the string `typeSwitch` **13** times in the raw `-v` output — but that count is `grep -c` over every
textual occurrence of the token, which includes the `Utf8`/`NameAndType`/`Methodref` constant-pool entries AND
the `BootstrapMethods` table entries for the SAME underlying call sites, not one line per distinct switch.
Re-counted properly this session, two ways: (1) the `BootstrapMethods:` table itself lists exactly **2** entries
whose method reference is `java/lang/runtime/SwitchBootstraps.typeSwitch` (bootstrap indices `#9`, argument
types `HttpStatusException`/`SocketTimeoutException`/`NoRouteToHostException`/`UnknownHostException` — a
`Throwable`-typed cause dispatch; and `#19`, argument names `publicKey`/`refreshIncrement`/`restoreId` — a
`String`-typed key dispatch); (2) `javap -c -p`'s disassembly shows exactly **2** `invokedynamic ...
typeSwitch` instructions in the whole class (`:140` and method-local `:42` of a second method) `[CERT-hw]`
(both re-run this session, raw output preserved in this session's scratch). `RetrieveEntitlements.class`
carries **zero** occurrences of `typeSwitch` at any level (`grep -c`, this session) — confirming the T2/T3
finding that a pattern-switch claim scoped to "`EntitlementApi`/`RetrieveEntitlements`" (§84.2's own section
title names both classes) is only true for one of the two. §14 pointer added.

**§84.3 — the `BQudtUnitTag` table row's "instanceof BNumericPoint np pattern-match (Java 21) replaces N4's
cast" language describes a Vineflower resugaring artifact, not an actual N4→N5 code change.** §115.2 above
re-derives this independently: N4-4.15.3.28 and N5-5.0.0.28's `BQudtUnitTag.class` carry byte-for-byte identical
`instanceof`+`checkcast`+`astore` bytecode (major 52 vs major 69, same opcodes, same slot layout) — the
decompiled-source "replaces N4's cast" framing is true of the TEXT Vineflower renders, not of anything Tridium
changed. §84.3's own bottom-line verdict ("CLEAN... `@NiagaraProperty` block itself byte-identical") is correct
and unaffected — only the one table cell's causal language needs the correction. §14 pointer added.

**Self-verify row 9 also restates the pattern-switch claim** ("if/instanceof→switch-pattern-match are the only
other diffs in `EntitlementApi`/`RetrieveEntitlements`") — the same `EntitlementApi`-only scoping correction
applies; noted in the same §14 pointer rather than a second one (task instruction: one blockquote per affected
section/claim, not one per restatement).

## 115.6 — The 9 T2 quote sites: 7 harmless, 2 (`[Block 84]`) are defects `[CERT]` (T2 result, reused not re-derived)

T2 (delegated, `odd/tasks/decompiler-fidelity-audit.md:32`) classified all 9 SUSPECT quote sites this feature's
audit found: `[Block 27] §27.5`, `[Block 37]`, `[Block 41] §41.1`, `[Block 67]`, `[Block 82] §82.1`, `[Block
84] §84.2`, `[Block 84] §84.3`, `[Block 86]`, `[Block 103]`. Per the writer-prompt's own rule ("Quoting
decompiled code to explain BEHAVIOR is fine" — only asserting a language-FEATURE adoption or an N4↔N5
syntax DELTA from decompiled text is the violation), 7 of the 9 quote decompiled code only to describe what the
code DOES (control flow, values, call targets) — no bytecode-undecidable syntax-adoption or cross-version
syntax-delta claim rides on them. Only the 2 `[Block 84]` sites (§115.5 above) make that kind of claim. Per
task instruction, **no §14 pointer is added for the 7 harmless sites** — re-verifying and pointer-stamping 7
sites that do not carry the defect would itself be a form of the C10/measured-by failure this block is trying
to prevent (a correction pointer implies a correction; these 7 have none).

## 115.7 — Method-error classes catalog, C1-C12, mapped to lint rules R1-R8

No prior C1-C8 catalog exists anywhere in this corpus or the kit (`grep` over `METHODOLOGY.md` and every retro
this session found no such table) — this section canonicalizes the full sequence for the first time. C9-C12 are
reused verbatim from `odd/tasks/decompiler-fidelity-audit.md`'s "Additional failure classes" section (their own
numbering, not renumbered here); C1-C8 are assigned from the failure families this feature's own T1-T3 work and
this block's fresh re-verification actually surfaced, each anchored to one of the 8 rules T8's concurrent writer
is building into `tools/lint-block.py` (`R1`-`R8`, per `odd/tasks/decompiler-fidelity-audit.md`'s own T8 text).

| Class | Instance (this feature) | Detection method | Prevention (rule) |
|---|---|---|---|
| **C1** — decompiler resugaring read as a syntax-ADOPTION or N4↔N5 syntax-DELTA | B70's `instanceof`-pattern census inflation; [Block 84] §84.3's `BQudtUnitTag` row (§115.2/§115.5) | Compile old-vs-new idiom pairs, `javap -c -p` diff, check class-file major version on both sides (§115.1) | R1 |
| **C2** — absence claim from the wrong location/name/jar instead of a class-level corpus-wide search | B102 pxEditor, B98 saml.jar (both self-corrected per T3, `odd/tasks/decompiler-fidelity-audit.md:42`) | Corpus-wide `rg` for the FQN/bare class name across ALL jars, never one guessed directory | R2 |
| **C3** — comparing a new finding against another block's PROSE paraphrase instead of its raw cited artifact | B106-G2 (`odd/tasks/decompiler-fidelity-audit.md:15`) | Re-open the cited `file:line`/artifact itself before writing a comparison claim | R6 |
| **C4** *(same root cause as C11 below — not separately instanced; kept as a named slot so the catalog stays legible, folded into C11's count)* | — | — | R3 |
| **C5** — compile-time constant inlining conflated with a genuine duplicate literal in a dead-constant/shadow-literal census | §115.3's `BTagDictionary.logger`/`LOGGER_NAME` pair — one shadow-literal hit is an inlined reference, the sibling hit for the same constant is a real duplicate, and decompiled source alone cannot tell them apart | docSource original vs decompiled-source diff at the exact flagged line | **R7** (constant inlining) |
| **C6** — baseline attribution: "N5-only"/"new in N5" computed against one historical N4 release without checking the closer adjacent release | §115.4's `platHwScanAtlas` (already in N4-4.15.3.28, not previously known); [Block 13] §13.5's 7-of-18 correction | Re-run the same "N5-only" name list against every available N4 install, not just the one first found | **R8** (baseline attribution) |
| **C7** — claim scope creep: a verified finding for one class/method silently generalized to a sibling class/method that was never itself checked | [Block 84] §84.2's "`EntitlementApi`/`RetrieveEntitlements`... pattern-matching switch" framing — only `EntitlementApi` has one (§115.5) | Re-run the exact same check (`javap`, `grep`) independently on EVERY class named in a shared claim, not just the one actually read | R6 |
| **C8** — a raw string-token grep count over `javap -v` text mistaken for a semantic count of call sites/statements | The orchestrator's own relayed "12 typeSwitch" figure for `EntitlementApi` — actually 2 distinct call sites; the other 10 hits are constant-pool cross-references to the same 2 (§115.5) | Count `BootstrapMethods:` table entries or `invokedynamic ... <name>` disassembly lines, never `grep -c "<token>"` over full `-v` output | R4 |
| **C9** — gap opened without running the mandatory ALREADY-COVERED check at open time | B109-G3, already answered by [Block 4] §4.2 + [Block 109] §109.3 before it was ever opened (closed as ALREADY-COVERED in [Block 114]) | Run the `rg -il` sweep BEFORE investigating, not after | R4 |
| **C10** — a figure carried forward from one tool/method into a gap's own text without stating how it was measured | "4,209 types" (a Ghidra count) vs 2,418 `typelinks` entries (a different method), conflated in a gap's own wording (`odd/tasks/decompiler-fidelity-audit.md:71-72`, closed in [Block 113]) | Every 3+ digit number or percentage in a gap bullet states its own measurement method inline | R4 |
| **C11** — evidence kept only in ephemeral session `/tmp` scratch, unrecoverable once the session's temp directory is cleaned | This feature's own writer prompt (`common.txt`) instructs writers to use `/tmp/claude-1000/.../scratchpad/`; §115.7's own re-count below finds a real fraction of prior blocks' cited `/tmp` paths from OLDER, pre-session-UUID-convention sessions no longer exist | `stat`/`os.path.exists` re-check of cited `/tmp` paths this session (below) | R3 |
| **C12** — a null-argument/fail-open call-site read without resolving the actual dynamic-dispatch target | B107 §107.3's three `getPermissions(null)` sites read as fail-open, when dispatch: resolves to `BRootHistoryFolder`'s override, which ignores the null `cx` and fetches real session permissions ([Block 112] §112.1, `BRootHistoryFolder.java:42-49`) | Resolve the concrete override actually invoked (class hierarchy read; state it as `dispatch:`), never assume the interface-declared default from the call site alone | R5 |

**Re-count of the "151 /tmp paths near CERT-hw/live, 13 already gone" figure — different methodology, reported
honestly as such, not reconciled with T3's own script (unavailable to this writer).** This session's own
mechanical sweep used two different cuts, both `[CERT-hw]` (this session, `python3`/`stat`):

1. **Whole-block co-occurrence** (a block file contains at least one `[CERT-hw]`/`[CERT-live]` marker anywhere
   → collect every `/tmp/claude-1000/...` path cited anywhere in that same block): **122** distinct paths, of
   which **34** fail `os.path.exists` this session. Of those 34, roughly a third are not literal paths at all —
   brace-expansion/glob citations such as `/tmp/claude-1000/n5b7/vf-out/**` or
   `/tmp/claude-1000/n5b26/decompiled/niagara/history/{BBooleanTrendRecord.java:76-78` — never meant to be
   `stat`-checked verbatim, a false-positive artifact of this writer's own regex, not a genuine loss.
2. A tighter **±2-line proximity window** around each `/tmp` citation, requiring a `CERT-hw`/`CERT-live` token
   within that window specifically, found only **9** paths (all still present) — almost certainly too narrow,
   since block prose paragraphs routinely separate a marker from its cited path by more than 2 physical lines.

Neither cut reproduces T3's own "151"/"13" figures, and this writer does not have T3's original script or exact
filter to reconcile the difference — reported honestly rather than silently accepted or silently contradicted.
The directionally consistent finding across all three methodologies (T3's, and both of this session's own):
**scratch-path rot is real and non-trivial** — a material fraction of `/tmp`-cited evidence from earlier blocks
no longer resolves, concentrated in the OLDER `/tmp/claude-1000/n5b<N>/` path convention (pre-dating this
session's own `/tmp/claude-1000/-home-.../‹uuid›/scratchpad/` convention), which is exactly what T9-T11's
planned `evidence/`-directory durable-preservation work (out of this block's scope) is meant to fix.

## 115.x — Corrections to earlier blocks

- **[Block 84] §84.2 / §84.3 / self-verify row 9** — see §115.5. `§14` pointers added to `niagara5-block84.md`.
- **[Block 13] §13.5** — see §115.4. `§14` pointer added to `niagara5-block13.md`.
- **[Block 96] dead-constant section / [Block 105] §105.8 / [Block 111] (B105-G2 section)** — see §115.3.
  `§14` pointers added to all three files: the method cannot separate an inlined constant reference from a
  duplicated literal; the 62.5%/"accidental duplication" split is unsupported as a bug-RATE claim (it may still
  be a correct count of the 40-candidate SAMPLE's own classifications — the caveat is about what the method can
  distinguish, not about re-litigating the sample's own 40 individual reads).
- **[Block 18] §18.9** — flagged in §115.4 as a downstream site relying on the now-corrected "N5-only" framing
  for `cloudLinkNcs` (confirmed present in N4-4.15.3.28, §115.4's own table); **not edited** (outside this
  task's Deliverable-2 file list) — see child gap **B115-G1**.

## 115.x — Connections

- **[Block 90] §90.2 / [Block 98] §98.8** — the resugaring rule §115.1/§115.2 re-confirm was first established
  there; this block is the first to formalize it into a bytecode-distinguishability MATRIX (9 rows) rather than
  a single-idiom observation.
- **[Block 70]** — the original `instanceof`-pattern adoption census this whole feature exists to audit; not
  re-opened or re-corrected here (out of T4's scope; the Problem/why section already records the caveat gap).
- **[Block 96]/[Block 105]/[Block 111]** — §115.3's constant-inlining proof directly extends their own shared
  `dead_constants_shadowed.json` artifact; no new script was written, the existing one's OUTPUT was read against
  a docSource cross-check their own method never performed.
- **[Block 101]** — §101.6 already independently established `platHwScanAtlas`'s hardware identity (ARM64 snap
  board) without asserting an "N5-only" module-shipping claim either way; §115.4's own 4.15.3.28-baseline
  correction (the module already shipping in N4-4.15.3.28) is additive to, not in tension with, §101.6's own
  finding.

## 115.x — Child gaps opened

- **B115-G1** (low, `investigable`) — add a `§14` pointer to `niagara5-block18.md` §18.9's `cloudLinkNcs` row
  (§115.4), outside this task's authorized file list. `coverage-check:` `rg -il "cloudLinkNcs"
  niagara5-block*.md` (this session, single hit outside its own lineage: `niagara5-block18.md:334`).
  `measured-by:` line number 334 is `rg`'s own reported match line, this session.
- **B115-G2** (medium, `blocked-on-tools/lint-block.py`) <!-- lint-ok: R2 tool-file presence check on our own
  repo, not a corpus absence claim --> — once the concurrently-built `tools/lint-block.py` lands, run it in
  `--audit` mode against every block numbered under 115 to find every existing R1-R8 violation this catalog's
  manual, sampled checks did not reach; this block's own findings (§115.3-§115.5) were found by targeted,
  task-directed reading, not an exhaustive corpus sweep. `coverage-check:` `ls tools/lint-block.py`, this
  session — absent at the start of this block's writing session, present by the time this block finished (the
  other writer's concurrent work). `measured-by:` "under 115" is this block's own threshold, not a measured count.
- **B115-G3** (medium, `investigable`, mechanical but large) — extend §115.3's one-pair docSource-coverage proof
  to the full `dead_constants_shadowed.json` population (3623 records): for each record whose `file` is
  docSource-covered (`organized/docSource/<module>/...` exists for the matching path), read the original at
  each `shadow_literal_hits` line and classify inlined-reference vs genuine-duplicate. `coverage-check:` `find
  organized/docSource -type d` cross-referenced against the 3623 records' own `file` field (not run to
  completion this session — 12 records spot-checked, see §115.3). `measured-by:` a full population run would
  report `<N docSource-covered records> / 3623` as its own denominator, not yet computed.
- **B115-G4** (low, `investigable`) — [Block 13] §13.4.4(d-2)'s 49 "no-N5-package-overlap" removed Tridium
  modules were checked only against the N4.14.0.162→N5.0.0.28 diff; whether any of THOSE 49 are also present in
  N4-4.15.3.28 (the reverse direction from §115.4's check, which only covered the 18 "added" modules) was not
  checked this session. `coverage-check:` `rg -il "13.4.4"` this session — not previously investigated
  cross-baseline. `measured-by:` the "49" figure is [Block 13] §13.4.4(d-2)'s own count, reused verbatim, not
  re-derived here.
- **B115-G5** (low, `investigable`) — reconcile this block's own two `/tmp`-path re-counts (§115.7) against
  T3's original delegated-worker script/methodology, once that script's own location is located (not found
  in this writer's own scratch directory). `coverage-check:` `find /tmp/claude-1000 -iname "*tmp_path*"` /
  `find /tmp/claude-1000 -iname "*151*"` this session, no script found. `measured-by:` T3's own "151"/"13"
  figures are reused verbatim from `odd/tasks/decompiler-fidelity-audit.md:37-44`, not re-derived here — see
  §115.7's own two differently-methodology'd re-counts (122/34 and 9/0) for what this writer measured instead.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | Rows 1-4 of the idiom matrix (instanceof-pattern, `var`, text block, string concat) are bytecode-IDENTICAL old-vs-new | [CERT-hw] | `scratchpad/fidelity/{old,new}/javap.txt`,`javap-g.txt`, this session (T1's own re-read) |
| 2 | Rows 5-9 (array/Iterable for-each, switch-expr, lambda, pattern-switch) are bytecode-DISTINGUISHABLE | [CERT-hw] | `scratchpad/fidelity/{old,new}/javap-g.txt`, `scratchpad/fidelity/{old,new}/F.java`, this session |
| 3 | Tridium N5 classes ship with LocalVariableTable/LineNumberTable debug info (62/63 entries, `BNumericWritable`) | [CERT-hw] | `scratchpad/fidelity/tri/niagara/control/BNumericWritable.class`, `javap -v`, this session |
| 4 | N4-4.15.3.28 and N5-5.0.0.28 `BQudtUnitTag.class` carry byte-for-byte identical `instanceof`/`checkcast`/`astore` bytecode (major 52 vs 69) | [CERT-hw] | `scratchpad/fidelity/qudt/n4/.../BQudtUnitTag.class` + `organized/tagdictionary/extracted/.../BQudtUnitTag.class`, `javap -c -p`, this session |
| 5 | `K.HOST` (compile-time constant) is inlined to a bare literal by `javac`, invisible to Vineflower as a symbolic reference | [CERT-hw] | `scratchpad/fidelity/constinline/{K,U}.java`, `scratchpad/fidelity/constinline/vf/U.java`, this session |
| 6 | `BTagDictionary.java` docSource line 1414 references `BTagDictionaryService.LOGGER_NAME` by name; the Vineflower decompile of the same site (line 131) shows a bare `"tagdictionary"` literal | [CERT] | `organized/docSource/tagdictionary/niagara/tagdictionary/BTagDictionary.java:1414`; `organized/tagdictionary/vineflower/niagara/tagdictionary/BTagDictionary.java:131` |
| 7 | A second shadow-literal hit for the SAME constant, same file (decompiled :388 / docSource :976), is a genuine duplicate in the ORIGINAL source, not an inlined reference | [CERT] | `organized/docSource/tagdictionary/niagara/tagdictionary/BTagDictionary.java:976-979` |
| 8 | 7 of [Block 13] §13.5's 18 "N5-only" modules (cloudLink family, including Azure/Forge/HonSbp/Ncs, plus jodaTime and platHwScanAtlas) already ship in N4-4.15.3.28; 11 do not | [CERT-hw] | `ls /mnt/c/PowerB/PowerB-4.15.3.28/modules/*.jar`, this session, `scratchpad/b115_powerb_jars.txt` |
| 9 | `platHwScanAtlas-rt.jar` in N4-4.15.3.28 declares `vendorVersion="4.15.3.28"`, same `BAtlasBoard` class as the N5 module | [CERT-hw] | `unzip -p .../platHwScanAtlas-rt.jar META-INF/module.xml`, this session |
| 10 | `EntitlementApi.class` carries exactly 2 distinct `SwitchBootstraps.typeSwitch` call sites, not 12; `RetrieveEntitlements.class` carries 0 | [CERT-hw] | `javap -v -p`/`javap -c -p` on both `organized/_bin-ext/nre/extracted/com/tridium/nre/subscription/{EntitlementApi,RetrieveEntitlements}.class`, this session |
| 11 | `niagara5-block18.md:334` asserts `cloudLinkNcs` is "N5-only," contradicted by finding 8 above | [CERT] | `niagara5-block18.md:334`; cross-referenced against `scratchpad/b115_powerb_jars.txt` |

**Tally:** 8 `[CERT-hw]`, 3 `[CERT]`, 0 `[INFER]` in the numbered self-verify table (this block's body prose
carries no additional `[INFER]`-marked claims beyond the ones in this table; every causal/attribution claim in
§115.1-§115.6 is backed by a `[CERT-hw]`/`[CERT]` citation inline). Ratio 0/11 ≈ 0.00 — expected for an
evidence-heavy audit block whose central claims are all freshly re-run this session, not deduced.

**Artifacts:** `scratchpad/fidelity/{old,new,constinline,qudt}/` (T1's own artifacts, re-read and, for `qudt`,
independently re-run this session) · `scratchpad/b115_powerb_jars.txt` (721-line `ls` of the PowerB-4.15.3.28
modules directory, this session) · `scratchpad/b115_tmp_paths_all.txt` / `b115_tmp_paths_clean.txt` (§115.7's
re-count, this session) · `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/dead_constants_shadowed.json`
(reused unmodified from [Block 96], not regenerated).

**Verify-block:** see final report for this session's `verify-block.sh` run and output.
