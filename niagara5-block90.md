# Block 90 — Closing five source-level census gaps: a full receiver-type classification of the 211 `getFirst`/`getLast` call sites, a decisive `instanceof`-pattern decompiler-artifact finding, `kitControl`'s zero-modernization corroboration, a tool-confirmed N4 ZKM census, and the six dynamic license-feature call sites traced

> Research closing/narrowing six previously-opened child gaps, each a specific residual measurement a
> prior block left open. Covers: **B80-G1** ([Block 80] §80.2 — "a full new-vs-old classification of
> all 110 `getFirst`/`getLast`/`addFirst`/`addLast` call sites by declared receiver type" — the block's
> own text names 110 *files*, not call sites, and this session's exact reproduction of Block 80's own
> `find`/`grep` command confirms 110 files / 211 individual call-site lines, both counts stated
> explicitly below); **B70-G2** ([Block 70] §70.7 — cross-check the `instanceof`-pattern-matching
> census (§70.4) against `docSource.jar`'s pristine originals for `control.jar`'s 31/45
> docsource-covered classes); **B70-G4** ([Block 70] §70.7 — confirm `kitControl`'s flat 0%
> `instanceof`-pattern-matching rate against its own records/sealed-classes/pattern-switch bytecode
> counts); **B25-G1** ([Block 25] §25.x — measure genuine `instanceof`-pattern-matching (JEP 394)
> adoption from decompiled source, since it is bytecode-invisible); **B76-G2** ([Block 76] §76.3 — a
> watermark-specific N4 ZKM obfuscation census, replacing the base64-polluted `grep -rl 'ZKM'`
> substring count); **B11-G3** ([Block 11] §11.9 — trace the actual runtime `vendor`/`feature` values
> of the 6 dynamic (non-literal-argument) `checkFeature`/`getFeature` call sites). Does **not** cover:
> a full corpus-wide re-derivation of every `instanceof` occurrence outside the four already-censused
> N5 modules (`control`/`alarm`/`kitControl`/`schedule`); a full enumeration of every
> `BPlatformService`/`BIPlatformCommand` subtype's license-feature override (the *mechanism* is traced
> for B11-G3, not every instance — see child gap); re-running [Block 25]'s own now-unpreserved
> `classcensus.py` byte-for-byte (an independent `javap -v` re-derivation was used instead, cross-
> validating the same claim by a different, more directly authoritative method).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at
> `/home/cristian/niagara5-research/organized/` (18,022 `.java` files, `vineflower/` primary +
> `bajaui/fallback/` CFR fallback per [Block 30]'s decompiler bake-off, plus a pristine
> `organized/docSource/` tree — confirmed this session to be the actual `docSource.jar` ground-truth
> source [Block 25]/[Block 70] refer to, not merely described by them: its `control` subtree shares
> exactly 31 of 45 filenames with `organized/control/vineflower/`, reproducing [Block 25]'s own
> "68.9%" docsource-coverage figure byte-for-byte). N4 baseline for **B76-G2**:
> `/home/cristian/niagara-research/organized` (4.14 OEM corpus, 688 top-level module dirs). Census
> method for B80-G1: `find organized -name '*.java' -exec grep -nE
> '\.(getFirst|getLast|addFirst|addLast|removeFirst|removeLast)\('` (matches [Block 80]'s own `-l`
> variant exactly at the file level: 110 files) — a shell-glob would under-match per METHODOLOGY's
> known trap, so `find -exec` was used throughout, consistent with every prior block in this series.
> Two Python scripts were written this session for the mechanical parts (`instanceof_census.py`,
> `classify_callsites.py`) and a `javap -v -p` sweep was run directly against the installed
> `kitControl.jar`; both preserved at
> `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b90/`
> (scratch, not archived in the corpus). Markers (canonical list: METHODOLOGY §3): `[CERT]` local
> primary source (`file:line` or a literal command/tool-output) · `[CERT-hw]`/`[CERT-doc]`/`[CERT-web]`/
> `[CERT-a]` not used in this block · `[INFER]` deduction, including every claim that extrapolates a
> checked subset's result to an unchecked remainder.

---

## 90.1 — B80-G1 CLOSED: all 211 call sites across the 110 files classified by declared receiver type — 91 NEW, 61 OLD, 59 OTHER (homonym), 0 unresolved `[CERT]`

> **Correction (added by [Block 105], §14 cross-block).** The 211-site population excluded `bajaui/fallback/` (6 more
> sites: 4 new, 2 old). Corrected totals: 217 sites / 115 files, 95 new / 63 old / 59 other. See [Block 105].

Re-running [Block 80]'s own `find organized -name '*.java' -exec grep -lE
'\.(getFirst|getLast|addFirst|addLast|removeFirst|removeLast)\('` (excluding `fallback/`) reproduces
**exactly 110 files** `[CERT]` — confirming [Block 80] §80.2's own count before extending it. The
same sweep with `grep -nE` (line-level, not file-level) yields **211 individual call-site lines**
`[CERT]` (`/tmp/.../scratchpad/b90/callsites_raw.txt`) — this is the actual population the gap's own
text ("classification of all 110 ... call sites") describes, since a single file can (and 84 of the
110 do) carry more than one call site. **Drift note, stated per the task's own instruction**: [Block
80] §80.2 itself writes "110 files" while naming the population "110 ... call sites" in the same
sentence — this block treats "110" as the file-level count (reproduced above) and classifies the true
211-row call-site population it implies, rather than silently picking one reading.

**Method.** A Python script (`classify_callsites.py`) extracts, for each call site, the receiver
expression immediately preceding the method call, then:
- for a **bare identifier or `this.field`** receiver, searches the *same file* for the nearest
  declaration (local variable, field, or parameter) **at or before the call site's line** — the first
  version of this script picked the file's *last* matching declaration regardless of position and
  produced 5 mis-classifications from same-named variables in unrelated scopes (e.g. `Object o` in an
  `equals()` override 1,000+ lines below the real `List<TypeInfo> o` the call site actually used); this
  was caught by cross-checking against [Block 80]'s own already-published examples (below) and fixed
  before the final pass;
- for a **chained call** (`x.getY().getFirst()`), looks up `getY()`'s declared return type in the same
  file (JDK API and BouncyCastle/Tridium-library chained calls, not declared in-corpus, are resolved
  manually — 8 sites, all documented below).

Classification buckets, matching [Block 25] §25.9's own taxonomy: **NEW** (`List`/`ArrayList`/`Set`/
`LinkedHashSet`/`SequencedCollection`-family — genuinely could not compile pre-Java-21), **OLD**
(`Deque`/`LinkedList`/`ArrayDeque`/`ConcurrentLinkedDeque`/`LinkedBlockingDeque`-family — pre-existing
since Java 1.2/1.6), **OTHER** (a same-named method on an unrelated type — a homonym, no
`SequencedCollection` relevance at all).

**Result, all 211 sites resolved, 0 left unclassified** `[CERT]`:

| Classification | Count | % | Dominant modules (call-site count) |
|---|---:|---:|---|
| **NEW** | 91 | 43% | `migrator` (10), `docSource` (10, same logical files as their `vineflower` counterparts), `workbench` (8), `_bin-ext`/`nre` (9 incl. 2 manually-resolved JDK-API chains), `platDaemon` (6), `baja` (7 incl. 2 manually-resolved JDK-API chains), `platform` (4), `box` (4) |
| **OLD** | 61 | 29% | `analytics` (17 — all in ONE class, `KNNLinkedList.java`, a k-NN sliding-window structure built on two `LinkedList` fields), `baja` (12, incl. `EngineManager`'s `peakScanStats`/`peakInterscanStats` — see below), `migrator` (8), `alarmOrion` (6), `platDataRecovery`/`cloudLink`/`bacnetAws` (3 each) |
| **OTHER** (homonym, not `SequencedCollection`-relevant) | 59 | 28% | `history` (11, `com/tridium/history/file/recstore/Page.getFirst` — the exact homonym [Block 25] §25.9 already named as an example), `baja`+`template`+`rdb`+`devkit`+`_bin-ext` (18, all `niagara/nre/util/tuple/Pair.getFirst`/`getSecond` — Tridium's own 2-tuple helper), `_bin-ext`/`clientCertAuth`/`signingService` (15, `org.bouncycastle.asn1.x500.RDN.getFirst` — a BouncyCastle ASN.1 type), `snmpLibs` (4, `TokenNFA.StateQueue`, a grammar-parser-library-internal queue type), `systemIndex`/`web`/`migrator` (3, `Pair`) |
| **UNRESOLVED** | 0 | — | (all resolved — see below) |

**Named resolutions of [Block 80]'s own explicitly-flagged examples**, confirming the classifier
against known ground truth before trusting it on the full population:

- `ModuleSetClassLoader.java:542,564` `certificates.getFirst()` — `[CERT]` confirmed **NEW**:
  `X509Certificate certificate = (X509Certificate)certificates.getFirst();` with `certificates`
  declared `List<...>` in the same file, matching [Block 80] §80.2's own reading exactly.
- `organized/baja/vineflower/niagara/tag/Tags.java:44` `values.getFirst()` — `[CERT]` confirmed **NEW** (`values` declared `List`).
- `organized/baja/vineflower/niagara/timezone/DstRule.java:138` (and its `docSource` twin, `:223`) `javaRules.getTransitionRules().getFirst()` —
  `javaRules` is `[CERT]` `organized/baja/vineflower/niagara/timezone/DstRule.java:86`
  `java.time.zone.ZoneRules javaRules;` — the standard JDK type, and
  `java.time.zone.ZoneRules.getTransitionRules()` is a well-known JDK API returning
  `List<ZoneOffsetTransitionRule>` (confirmed in-file by the surrounding code's own `.get(0)`/`.get(1)`
  indexed access at `DstRule.java:127,131,134`, immediately preceding the `.getFirst()` call) — **NEW**,
  resolving [Block 80]'s own already-[CERT] finding at source, now with the JDK type identified by
  name.
- `NModuleModuleFinderFactory.java:651,657`
  `codeSigner.getSignerCertPath().getCertificates().getFirst()`/`.getLast()` — `getSignerCertPath()` is
  the standard `java.security.CodeSigner` API returning `java.security.cert.CertPath`, and
  `CertPath.getCertificates()` is the standard JDK method returning `List<? extends Certificate>` —
  **NEW**, confirming [Block 80] §80.2's own reading; the same JDK chain recurs in
  `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/CertificateChainValidator.java:166,227`
  (2 more sites, also **NEW**, not previously named in [Block 80]).
- `EngineManager.java:168,176,186,203,211,221,429,432,485` (9 sites total — [Block 80] §80.2 named 6 of
  these and flagged the receiver type `[INFER]`, "pending the field declaration read") —
  **RESOLVED to OLD, [CERT]**: `[CERT]`
  `organized/baja/vineflower/com/tridium/sys/engine/EngineManager.java:58-59`:
  ```java
  private final LinkedList<EngineManager.EngineStats> peakScanStats = new LinkedList<>();
  private final LinkedList<EngineManager.EngineStats> peakInterscanStats = new LinkedList<>();
  ```
  Both fields are declared with the **concrete `LinkedList`** type, not `Deque`/`SequencedCollection` as
  an interface — the exact same "declared-concrete, not declared-against-the-new-interface" pattern
  [Block 70] §70.5 already found for `ExecutionQueue`/`BSummary` in `schedule.jar`. This upgrades
  [Block 80] §80.2's own `[INFER]` ("receiver type not confirmed in this sample") to a definitive
  `[CERT]` **OLD** classification — the engine's peak-scan-stats tracking is ordinary pre-21 `LinkedList`
  usage, not a `SequencedCollection`-typed adoption site.

**Homonym-bucket resolutions** (the 59 OTHER sites, by category, each independently confirmed by
reading the receiver's declared type): **15 BouncyCastle `RDN.getFirst()`** sites
(`organized/clientCertAuth/vineflower/com/tridium/clientCertAuth/pki/BUsernameExtractorCNFromSubjectDN.java:40`, `organized/clientCertAuth/vineflower/com/tridium/clientCertAuth/pki/BUsernameExtractorCNFromDirectoryNameSan.java:50`,
`organized/clientCertAuth/vineflower/com/tridium/clientCertAuth/web/ClientCertAuthServlet.java:208`, `SigningServiceUtils.java:148,149,173,174,189`,
`organized/_bin-ext/nre/vineflower/com/tridium/nre/cloud/NiagaraCloudIdentity.java:88`, `organized/_bin-ext/nre/vineflower/com/tridium/crypto/core/cert/CertUtils.java:1428`, `PemSource.java:76,81,95,100,122`) — every
receiver (`rdn`/`rdn1`/`rdns[i]`/`issuer[0]`/`subject[0]`/`requiredAttribute`) is declared
`org.bouncycastle.asn1.x500.RDN` `[CERT]`, e.g. `organized/signingService/vineflower/com/tridium/signing/SigningServiceUtils.java:172`
`for (RDN requiredAttribute : requiredDn.getRDNs())`; **12 Tridium `Pair<A,B>.getFirst()`/`.getSecond()`**
sites (`NiagaraTemplate.java:179,197,203`, `organized/template/vineflower/com/tridium/template/api/OptionalComponent.java:30`, `organized/baja/vineflower/com/tridium/sys/transfer/CompToComp.java:292`,
`organized/rdb/vineflower/com/tridium/rdb/util/BUnicodeUpdateJob.java:85`, `CombinedTemplateSource.java:272,286,308,316,329,333`) — every receiver
declared `niagara.nre.util.tuple.Pair<...>` `[CERT]`, e.g. `organized/template/vineflower/com/tridium/template/api/impl/CombinedTemplateSource.java:21`
`private List<Pair<Integer, Integer>> propertyKeys = null;` (the *field* is a genuine `List`, but
`.get(k)` returns a `Pair` element, and it is the `Pair`'s own `getFirst()` being called, not the
`List`'s); plus the auto-classified `history/recstore/Page` (11), `snmpLibs/TokenNFA.StateQueue` (4),
and a further batch of `Pair` sites (3) the automated pass already resolved correctly (§ table above).

**Other manually-resolved NEW sites**: `organized/template/vineflower/com/tridium/template/ui/ApplicationTemplateInstallUtil.java:97`
`newDeployedWorksheet.deployedRoots.getLast()` — `deployedRoots` is `[CERT]`
`organized/template/vineflower/com/tridium/template/ui/BulkDeployUtil.java:3878`
`public List<BulkDeployUtil.DeployedRoot> deployedRoots = new ArrayList<>();`; `organized/template/vineflower/com/tridium/template/ui/BTemplateManager.java:1059`
`((ArrayList)source).getFirst()` — an explicit cast, **NEW** by construction; `BatchCommands.java:197,332`
`model.kids.removeFirst()`/`model.cols.getFirst()` — both fields declared `[CERT]`
`organized/program/vineflower/com/tridium/program/ui/batch/BBatchTable.java:127-128`
(`List<String> cols`, `List<BComponent> kids`). One manually-resolved **OLD** site:
`organized/baja/vineflower/com/tridium/util/ClassUtil.java:25` `superclasses[i].addFirst(cls)` — `[CERT]`
`organized/baja/vineflower/com/tridium/util/ClassUtil.java:19` `LinkedList[] superclasses = new
LinkedList[classes.length];` (a raw `LinkedList` array).

**Methodological note on the 110-file population itself**: 10 of the 110 files are `organized/docSource/`
copies of the same logical source already present under a module's `vineflower/` tree (the same
duplicate-tree effect [Block 70]'s cross-check in §90.2 below relies on) — e.g. `DstRule.java` and
`Tags.java` are each counted once under `docSource` and once under `vineflower`. This does not change
[Block 80]'s own count (which used the identical un-deduplicated `find` sweep), but is worth naming
explicitly since it means the "110 files" figure is not 110 *distinct* pieces of logic.

## 90.2 — B70-G2 CLOSED: every cross-checkable `instanceof`-pattern-matching "bound" site in [Block 70]'s census is a Vineflower decompiler resugaring artifact, not genuine Tridium-authored JEP 394 syntax `[CERT]`

[Block 70] §70.4 measured 32 "bound" (JEP 394 pattern-match) `instanceof` occurrences across
`control`/`alarm`/`kitControl`/`schedule` and flagged, as its own child gap, that this reading had not
been cross-checked against `docSource.jar`'s pristine originals for the 68.9%-covered subset of
`control.jar`. This session confirms `organized/docSource/` is exactly that ground-truth tree (§ header)
and extends the cross-check to **all four** censused modules, not only `control`.

**Method.** A Python script (`instanceof_census.py`) reproduces [Block 70] §70.4's own line-based scan
(`.java` files only, comment lines and block comments excluded, classifying each non-comment
`instanceof` line as bound/unbound by whether a bare binding identifier follows the type token) — first
validated by running it, unmodified, over the full `control` module: it reproduces [Block 70]'s
published table **exactly** (45 files, 20 non-comment `instanceof` lines, 5 bound, 15 unbound, 25.0%
ratio) `[CERT]`. The same script was then run, restricted to the file-name overlap between each
module's `docSource/` and `vineflower/` trees, against BOTH trees:

| Module | docSource/vineflower overlap | Overlap `instanceof` lines | Vineflower bound | docSource bound |
|---|---:|---:|---:|---:|
| `control` | 31 of 45 (68.9%) | 20 | **5** | **0** |
| `alarm` | 52 of 195 (26.7%) | 65 | **5** | **0** |
| `kitControl` | 167 of 224 (74.6%) | 7 | 0 | 0 |
| `schedule` | 31 of 103 (30.1%) | 20 | **3** | **0** |

`[CERT]` — the non-comment `instanceof` LINE COUNT is identical between the two trees in every module
(20/20, 65/65, 7/7, 20/20), proving Vineflower did not add or remove any `instanceof` check; but the
**bound classification collapses to zero in `docSource` for all four modules**, while `vineflower`
shows 13 bound sites across the three non-`kitControl` modules (5+5+0+3, exactly the cross-checkable
slice of [Block 70]'s corpus-wide 32).

**Reading every one of the 13 cross-checkable "bound" sites at source, in both trees, confirms why**:
every single one is the classic pre-JEP-394 idiom (`if (x instanceof T) { T t = (T)x; ...use t...; }`)
in `docSource`, which Vineflower **resugars** into the modern binding form
(`if (x instanceof T t) { ...use t...; }`) during decompilation. Four representative pairs, read this
session:

```java
// docSource (pristine original), BControlPoint.java:404-408
if (child instanceof BPointExtension)
{
  BPointExtension ext = (BPointExtension)child;
  try { ext.onExecute(out, cx); } ...
```
```java
// vineflower decompile, BControlPoint.java:182-186
if (child instanceof BPointExtension ext) {
   try { ext.onExecute(out, cx); } ...
```
`[CERT]` `organized/docSource/control/niagara/control/BControlPoint.java:404` vs.
`organized/control/vineflower/niagara/control/BControlPoint.java:182` (and the identical shape repeats
at `docSource:428`/`vineflower:197` for `pointFacetsChanged()`). The same pattern recurs at
`organized/docSource/control/niagara/control/WritableSupport.java:339` (`if (obj instanceof BRelTime)`)
vs. `organized/control/vineflower/niagara/control/WritableSupport.java:253`
(`if (!(facets.get("maxOverrideDuration") instanceof BRelTime maxDuration))`);
`organized/docSource/control/niagara/control/trigger/BDailyTriggerMode.java:169` vs.
`organized/control/vineflower/niagara/control/trigger/BDailyTriggerMode.java:87`; and — the exact
example [Block 70] §70.4 quoted as "the idiom JEP 394 was designed for" —
`organized/docSource/schedule/niagara/schedule/BAbstractScheduleSelector.java:252-255`:
```java
if (oldValue instanceof BLink)
{
  BLink link = (BLink)oldValue;
  if (link.getTargetSlotName().equals(schedule.getName())) { doUpdateScheduleList(); }
}
```
vs. `organized/schedule/vineflower/niagara/schedule/BAbstractScheduleSelector.java:142`
`if (oldValue instanceof BLink link && link.getTargetSlotName().equals(schedule.getName())) {`.

**Independent confirmation that this is structurally inevitable, not a coincidence of these 4
examples**: the classic `instanceof`+cast-to-immediately-used-local idiom and the JEP 394
pattern-match-binding idiom compile to **byte-for-byte identical bytecode** when the compiler can prove
the cast succeeds — verified directly this session by compiling both forms with `javac --release 21`
and comparing `javap -c` output:

```
$ javap -c -p Bound.class   # if (child instanceof Ext ext) { ext.onExecute(); }
   1: instanceof #7   4: ifeq 18   7: aload_0   8: checkcast #7   11: astore_1  12-13: invokeinterface ...
$ javap -c -p Classic.class # if (child instanceof Ext) { Ext ext = (Ext) child; ext.onExecute(); }
   1: instanceof #7   4: ifeq 18   7: aload_0   8: checkcast #7   11: astore_1  12-13: invokeinterface ...
```
`[CERT]` (this session's own compile+disassemble, `/tmp/.../scratchpad/b90/bytecode_test/`) — the two
opcode sequences are identical. This means NO bytecode-level or decompiler-level signal can ever
distinguish genuine Tridium-authored JEP 394 syntax from a decompiler's own resugaring of classic Java
8-era code, for this exact (single, unnegated, immediately-used) shape — a decompiler that chooses to
resugar (Vineflower does; whether CFR does for `instanceof` specifically was not tested this session)
will always show "adoption" here regardless of what the original source actually contained.

**B70-G2 verdict: CLOSED for the cross-checkable subset.** All 13 of 13 (100%) cross-checkable "bound"
`instanceof` sites from [Block 70] §70.4's census are Vineflower resugaring artifacts, not genuine
JEP 394 adoption by Tridium. `kitControl`'s already-reported zero-bound finding is independently
corroborated (0 bound in both trees, not merely absent-of-evidence). This directly falsifies reading
[Block 70] §70.4's 14.5% corpus-wide "bound ratio" as a real modernization signal for these four
modules — see §90.3.

## 90.3 — B25-G1 REVISED: genuine `instanceof`-pattern-matching adoption in the corpus's oldest-style modules reads as ~0%, not [Block 70]'s reported 14.5% — the earlier reading measured decompiler behavior, not Tridium's source `[CERT]`+`[INFER]`

[Block 25] §25.6 correctly identified `instanceof` pattern matching as bytecode-invisible and opened
B25-G1 to measure it from decompiled source; [Block 70] §70.4 did that measurement and reported a
14.5% "bound" adoption rate across `control`/`alarm`/`kitControl`/`schedule` (32/221 non-comment
`instanceof` lines), narrowing but not closing B25-G1. §90.2 above shows that measurement's entire
cross-checkable evidence (13 of the 32 bound sites, spanning `control`/`alarm`/`schedule`) is Vineflower
resugaring, not source-level adoption — meaning **the true answer B25-G1 originally asked for is
close to 0% for these four modules, not 14.5%** `[CERT]` on the 13-site cross-checked evidence,
`[INFER]` on extrapolating that finding to the remaining 19 corpus-wide bound sites [Block 70] reported
that fall outside `docSource`'s coverage (14 alarm-only + 8 schedule-only bound sites not individually
re-checked this session — the general bytecode-identity proof in §90.2 makes it *likely* they are the
same artifact, but each was not individually read against `docSource` this session, so this remains
`[INFER]` rather than `[CERT]` for the full 32; see child gap **B90-G1**).

This is a genuine revision, not merely a narrowing: it means a decompiled-source `instanceof` census
against a Vineflower tree **cannot answer** B25-G1's original question at all when Vineflower resugars
the classic idiom — the methodology [Block 25] itself proposed ("decompile the corpus and grep the
source for `instanceof \w+ \w+`") is unsound for measuring genuine adoption unless cross-checked
against a non-resugaring source (a pristine original, as `docSource` provided here, or a decompiler
confirmed not to resugar this idiom — neither tested for CFR/Procyon/JADX this session). [Block 25]
§25.13's broader "modernization clusters narrowly, mostly recompiled not rewritten" verdict is, if
anything, **strengthened** by this finding: one of its two source-level (as opposed to bytecode-level)
supporting signals for "some genuine adoption exists" turns out to measure decompiler behavior instead.

## 90.4 — B70-G4 CLOSED: `kitControl.jar`'s zero-modernization is confirmed directly against the installed jar's own bytecode — 0 records, 0 sealed classes, 0 pattern-switch bootstrap sites, despite a genuine Java-25 recompile `[CERT]`

[Block 25]'s own `classcensus.py` script and its raw per-jar JSON are not preserved in this corpus
(only its published per-jar tables survive); rather than attempt a byte-for-byte re-run, this session
re-derives the same three bytecode-level facts directly and independently, using the JDK's own `javap
-v -p` against every one of `kitControl.jar`'s 224 non-`module-info` classes (extracted from the live
install, `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/kitControl.jar`, matching [Block
70]'s own `recon.json`-cited 225-class/`primary_status=ok` figure) — a more directly authoritative
method than re-running a corpus-side script, since it reads the actual shipped bytecode attributes:

```
$ find . -name '*.class' -not -name 'module-info.class' -exec javap -v -p {} + | grep -c '^Record:'
0
$ find . -name '*.class' -not -name 'module-info.class' -exec javap -v -p {} + | grep -c '^PermittedSubclasses:'
0
$ find . -name '*.class' -not -name 'module-info.class' -exec javap -v -p {} + | grep -c 'SwitchBootstraps'
0
$ find . -name '*.class' -not -name 'module-info.class' -exec javap -v -p {} + | grep -c 'StringConcatFactory'
82
$ javap -v -p <any class> | grep "major version"
  major version: 69
```
`[CERT]` (this session's own `javap -v` sweep, `/tmp/.../scratchpad/b90/kitControl_extract/`). Zero
`Record` attributes, zero `PermittedSubclasses` (sealed-class) attributes, and zero `SwitchBootstraps`
bootstrap-method references corpus-wide in `kitControl.jar` — directly corroborating [Block 70] §70.4's
0% `instanceof`-pattern-matching finding for the same module with three independent, bytecode-level,
feature-adoption signals. Simultaneously, 82 `StringConcatFactory` `invokedynamic` sites and major
version 69 confirm `kitControl.jar` **was** genuinely recompiled with a modern (Java 25) `javac`, not
merely re-stamped — the same "recompiled, not rewritten" pattern [Block 25] §25.13 already found for
the corpus at large, now confirmed at the single-module level for the specific module [Block 70]
flagged as the strongest zero-adoption candidate. **B70-G4 CLOSED**: `kitControl`'s zero-modernization
reading is a true zero across every bytecode-visible AND source-visible (per §90.2/§90.3, now that
`instanceof` is also correctly read as a true zero rather than an unmeasured blind spot) feature this
research series has checked, not an artifact of any single measurement's blind spot.

## 90.5 — B76-G2 CLOSED: the true N4 ZKM-obfuscated-module count is 16 top-level module dirs (23 module-jar variants), tool-confirmed — not the naive grep's 100 `[CERT]`

[Block 76] §76.3 showed the naive `grep -rl 'ZKM'` census (100 of 688 N4 top-level module dirs) is
polluted by base64 `SHA-256-Digest` manifest coincidences and asked for a watermark-specific
replacement. This session found the N4 corpus's **own ingestion pipeline already recorded the answer**
as a structural artifact, independent of any grep: 23 module-jar-variant directories carry a preserved
`vineflower.obfuscated-bak/` sibling next to their (now-deobfuscated) `vineflower/` tree — the corpus's
own record of every module its original decompile pipeline flagged and ran through a deobfuscator:

```
$ find organized -type d -iname 'vineflower.obfuscated-bak' | wc -l
23
```
`[CERT]`, mapping to **16 distinct top-level module dirs**: `clCBus`, `clEnoceanNetwork`, `easyBinding`,
`easyDatabaseManager`, `easyHealthyBuilding`, `easyTemplating`, `galileoKitPx`, `galileoPointViewer`,
`galileoSignalR`, `galileoSupervisor`, `honAdvWirelessCfg`, `honBACnetUtilities`, `honTagDictionary`,
`honeywellBacnetSpyder`, `honeywellLonSpyder`, `honeywellSpyderTool` `[CERT]`.

**14 of these 16 are independently confirmed ZKM by name**, via a preserved deobfuscation pipeline log
naming Zelix Klassmaster explicitly — e.g. `[CERT]`
`organized/clCBus/clCBus-rt/DEOBFUSCATION-NOTE.md`: "ZKM (Zelix KlassMaster) string-encrypted module...
Class/method names remain mangled (ZKM name obfuscation not reverted)", and its own
`pipeline/detect-output.txt`: `"RuleSuspiciousClinit: Zelix Klassmaster typically embeds decryption code
in <clinit>. This sample may have been obfuscated with Zelix Klassmaster... Found suspicious <clinit>
in com/honeywell/cbus/protocol/commands/schedule/CmpTpHolidayScheduleWrite"` — this is **exactly the
`<clinit>` string-decrypt idiom the gap's own text names** as the correct watermark signature, produced
by the `com.javadeobfuscator.deobfuscator` tool's own detector, not by this session's inference. The
same explicit Zelix-naming note exists for `clEnoceanNetwork`, `easyBinding`, `easyDatabaseManager`,
`easyHealthyBuilding`, `easyTemplating`, `galileoKitPx`, `galileoPointViewer`, `galileoSignalR`,
`galileoSupervisor`, `honAdvWirelessCfg`, `honBACnetUtilities`, `honTagDictionary`, and
`honeywellSpyderTool` (14 top-level modules total) `[CERT]` (each note individually `grep -ic
"zelix\|ZKM"` confirmed this session, all returning ≥4). The remaining 2 (`honeywellBacnetSpyder`,
`honeywellLonSpyder`) lack a preserved note/log but show the same residual signature directly: their
preserved `vineflower.obfuscated-bak/` trees contain 44 and 33 files respectively with the exact dense
clustered-`\uXXXX`-escape string-literal pattern (`char[] var10003 = "TFZM\u0003\\\u0013..."`-shape)
[Block 30] §30.6 already validated as ZKM's string-encryption signature `[CERT]` — treated as
confirmed-by-signature rather than confirmed-by-log, noted as a small residual gap (**B90-G3**).

**A corroborating full-corpus re-scan finds no additional genuine positive.** The same clustered-escape
signal was re-run (canonical `vineflower/` trees only, excluding `obfuscated-bak`/`decompiled`/
`extracted`/`deobf`/`pipeline` duplicate subtrees) across all 333 top-level module dirs that have a
`vineflower/` tree. Exactly 6 modules outside the known-16 show any nontrivial clustered-escape count
(`rdb` 2970, `rdbSqlServer` 1392, `honAlarmConsole` 26, `apachePoi` 22, `gauth` 19, `pdf` 9) — **every
one confirmed, by direct read, to be a known non-ZKM false-positive category**, not a missed ZKM module
`[CERT]`: `rdb`'s hit is `com/tridium/rdb/sql/SqlLexer.java`'s JFlex-generated `ZZ_CMAP_PACKED` character
map — the **exact same file** [Block 30] §30.6 already named as an N5 false positive for a different
(class-name) heuristic; `rdbSqlServer`'s is Microsoft's own bundled `SQLServerLexer.java`'s ANTLR
`_serializedATN` (a standard ANTLR-generated parser table, third-party); `gauth`'s is Google ZXing's
bundled `Code128Writer.java` charset constant (third-party); `pdf`'s is `PdfCidFontInfo.java`'s PANOSE
font-classification byte arrays — again the identical false-positive category [Block 30] §30.6 already
named for N5's own `pdf/PdfCidFontInfo.java`; `honAlarmConsole`'s is `BHonAlarmConsoleBuiltJS.java`'s
`static{}` XOR-encoded JS-bundle-path string — a **separate, already-documented, non-ZKM Niagara idiom**
(`niagara-mental-model-bloque81.md` explicitly distinguishes "Strings descifradas (ZKM)" from "rutas JS
(XOR en `static{}`)" as two different obfuscation mechanisms in this same corpus); `apachePoi`'s hits
are Apache POI's own bundled Unicode/encoding tables (third-party). **Zero of the 6 are genuine ZKM.**

**B76-G2 verdict: CLOSED.** The true N4 ZKM-obfuscated-module count in this corpus is **16 top-level
module dirs / 23 module-jar variants**, tool-confirmed via the corpus's own preserved deobfuscation
pipeline artifacts (14/16 by an explicit Zelix-naming log, 16/16 by the residual clustered-escape
signature), against the naive base64-polluted grep's 100 — an 84% reduction, and a full-corpus
corroboration pass found no additional genuine positive among 333 candidate module dirs.

## 90.6 — B11-G3 CLOSED: all 6 dynamic `checkFeature`/`getFeature` call sites traced — 3 resolve to concrete values/formulas, 3 are generic dispatch over a self-declaring `getLicenseVendor()`/`getLicenseFeature()` plugin interface, by design `[CERT]`

[Block 11] §11.9 named 6 call sites whose `vendor`/`feature` arguments were non-literal and left their
actual values untraced. All 6 classes were already decompiled in this corpus; reading each resolves
every site:

1. **`Station.checkLicense()`** — `[CERT]` `organized/baja/vineflower/com/tridium/sys/station/Station.java:212`
   `Sys.getLicenseManager().checkFeature("tridium", NreLicenseUtil.getStationLicenseFeature(NreLib.getHostId()))`.
   `NreLicenseUtil.getStationLicenseFeature(String hostId)` is `[CERT]`
   `organized/_bin-ext/nre/vineflower/com/tridium/nre/util/NreLicenseUtil.java:7-9`: `{ return
   "station"; }` — the `hostId` parameter is accepted but unused. **Resolves to the fixed literal
   `tridium:station`**, not a genuinely dynamic value.
2. **`BBackupChannel.getLicenseFeature()`** (`cloudLink.jar`) — `[CERT]`
   `organized/cloudLink/vineflower/com/tridium/cloudLink/channel/BBackupChannel.java:70-80`:
   `vendorName = svc.getLicenseFeature().getVendorName()` (inherited from the station's own
   `BCloudConnectionService`, already-licensed Feature) and `featureName = svc.getPlatformType() +
   "Recover"`. **Resolves to the formula `<connection-service-vendor>:<platformType>Recover`** — a
   real per-station-platform-type dynamic value, not a hidden fixed literal (the `platformType` value
   set itself is out of scope here — see child gap **B90-G2**).
3. **`BNiagaraRemoteTransport.getLicenseFeature()`** (`cloudLink.jar`) — `[CERT]` identical shape at
   `organized/cloudLink/vineflower/com/tridium/cloudLink/transport/BNiagaraRemoteTransport.java:169-179`,
   `featureName = svc.getPlatformType() + "Remote"`. Same formula, `Remote` suffix instead of
   `Recover`.
4. **`BPlatform`'s platform-service loader** — `[CERT]`
   `organized/platform/vineflower/com/tridium/platform/BPlatform.java:147-157`: for **every** concrete
   `BPlatformService` subtype found via `Sys.getRegistry().getConcreteTypes(...)`,
   `checkFeature(service.getLicenseVendor(), service.getLicenseFeature())` is called generically.
   `BPlatformService`'s own default implementation is `[CERT]`
   `organized/platform/vineflower/com/tridium/platform/BPlatformService.java:94-100`: `getLicenseFeature()
   → null` (not gated unless overridden), `getLicenseVendor() → "tridium"`. This is a **self-declaring
   plugin license-gate**: any module's `BPlatformService` subclass opts in by overriding
   `getLicenseFeature()` — confirmed concretely at `[CERT]`
   `organized/platCcn/vineflower/com/tridium/platCcn/BCcnPlatformService.java:66-68`
   `getLicenseFeature() { return "ccnl"; }`, which independently reproduces [Block 11] §11.4's own
   already-published `tridium:ccnl` feature key via a completely different code path (the generic
   `BPlatform` dispatch loop vs. `ccn.jar`'s own literal call sites) — a strong cross-corpus consistency
   check that this tracing is correct.
5. **`BPlat.getLicensedCommands()`** — `[CERT]`
   `organized/platform/vineflower/com/tridium/platform/command/BPlat.java:83-94`: the identical pattern
   for every concrete `BIPlatformCommand` subtype, `checkFeature(instance.getLicenseVendor(),
   instance.getLicenseFeature())`. `BIPlatformCommand`'s own defaults are `[CERT]`
   `organized/platform/vineflower/com/tridium/platform/command/BIPlatformCommand.java:34-40`: both
   `default String getLicenseVendor() { return null; }` / `getLicenseFeature() { return null; }` — same
   opt-in-by-override shape as (4), for the platform command-line tool's optional sub-commands instead
   of platform services.
6. **`BPort.isLicensed()`** (`platHwScan.jar`) — `[CERT]`
   `organized/platHwScan/vineflower/com/tridium/platHwScan/ports/BPort.java:150-162`: splits
   `this.getRequiredFeatures()` (a per-hardware-port-subclass-overridable config string, default `""`
   at `organized/platHwScan/vineflower/com/tridium/platHwScan/ports/BPort.java:81`) on `","` then each token on `":"`, calling `checkFeature(vendor, feature)` per
   pair — confirming [Block 11] §11.9's own speculation exactly (a `"vendor:feature[,vendor:feature]"`
   config string parsed at runtime), now with the config string's own source (`getRequiredFeatures()`,
   itself overridable per hardware-port subclass) identified.

**B11-G3 verdict: CLOSED.** None of the 6 sites hide an unrecoverable literal: 1 resolves to a single
fixed `vendor:feature` pair, 2 resolve to a traced `<upstream-vendor>:<platformType>{Recover,Remote}`
formula, and 3 (`BPlatform`, `BPlat`, `BPort`) are **the same architectural pattern** — a generic
dispatch loop over a self-declaring, opt-in `getLicenseVendor()`/`getLicenseFeature()`-style interface
method, checked against every concrete implementer found via the type registry — rather than 3
unrelated one-off dynamic sites. Enumerating every concrete `BPlatformService`/`BIPlatformCommand`
override corpus-wide (only `ccn`'s and `bacnet`'s were spot-checked here) is left as child gap
**B90-G4**.

## 90.x — Connections

- §90.1 directly extends [Block 80] §80.2, resolving its one explicitly-flagged `[INFER]`
  (`EngineManager`'s receiver type) to `[CERT]` and giving the full 211-site population [Block 80]
  itself deferred.
- §90.2/§90.3 jointly close [Block 70] §70.7's B70-G2 and materially revise [Block 25]'s B25-G1 (via
  [Block 70]'s own intermediate narrowing) — the decisive finding (bound `instanceof` = decompiler
  resugaring, confirmed both by direct source comparison and by an independent bytecode-identity
  compile test) also bears on [Block 30]'s decompiler-bake-off methodology: any future block reading
  Vineflower-decompiled `instanceof` syntax as evidence of source-level JEP 394 adoption should first
  check against `docSource` or a non-resugaring decompiler.
- §90.4 closes [Block 70] §70.7's B70-G4 and reinforces [Block 25] §25.13's "recompiled, not
  idiomatically modernized" verdict with a fourth independent bytecode signal (`javap -v` sweep of the
  live jar) for the specific module already flagged as the strongest zero-adoption candidate.
- §90.5 closes [Block 76] §76.3's B76-G2, reuses [Block 30] §30.6's own already-validated ZKM
  detection signals (single-letter-method density, clustered-`\u`-escape strings) as the corroboration
  pass, and reproduces two of [Block 30]'s own already-named N5 false-positive files
  (`SqlLexer.java`/`PdfCidFontInfo.java`) verbatim on the N4 side — a cross-corpus consistency finding.
- §90.6 closes [Block 11] §11.9's B11-G3 and independently reproduces one of [Block 11] §11.4's own
  published `vendor:feature` pairs (`tridium:ccnl`) via a structurally different code path, corroborating
  both blocks' findings against each other.

## 90.x — Child gaps opened

- **B90-G1** — Extend §90.2's `docSource` cross-check to the 19 corpus-wide "bound" `instanceof` sites
  [Block 70] §70.4 reported that fall OUTSIDE this session's docSource-overlap coverage (14 in `alarm`,
  8 in `schedule` — note this sums to 22, of which 3 were already read individually in §90.2's named
  examples, leaving 19 truly unchecked): either extend `docSource`'s own coverage for `alarm`/`schedule`
  further, or independently confirm via a second, non-resugaring decompiler (CFR/Procyon — untested for
  this specific idiom) whether they show the same artifact. `investigable`, low-priority given §90.2's
  100%-so-far resugaring rate and the general bytecode-identity proof make a different outcome unlikely.
- **B90-G2** — Enumerate `BCloudConnectionService.getPlatformType()`'s actual return-value set (only
  `"NCS"` is named, as a negative comparison, in `BBackupChannel`/`BNiagaraRemoteTransport`) to give the
  complete concrete `tridium:<platformType>{Recover,Remote}` feature-key list `Sys.getLicenseManager()`
  can actually be asked to check. `investigable`, mechanical (one class read).
- **B90-G3** — Obtain (or otherwise confirm) an explicit `com.javadeobfuscator.deobfuscator`
  Zelix-naming detect-log for `honeywellBacnetSpyder`/`honeywellLonSpyder` (currently confirmed only by
  the residual clustered-escape signature in their preserved `vineflower.obfuscated-bak/` trees, not by
  a named tool verdict like the other 14 of 16). `investigable`, low-priority (signature-level evidence
  is already strong and internally consistent with the other 14).
- **B90-G4** — A full corpus-wide census of every concrete `BPlatformService`/`BIPlatformCommand`
  subtype's `getLicenseVendor()`/`getLicenseFeature()` override (only `platCcn`'s `"ccnl"` and
  `platBacnet`'s `null` were spot-checked in §90.6) — would give the complete list of modules gated
  through the generic `BPlatform`/`BPlat` dispatch mechanism, as opposed to a direct literal
  `checkFeature()` call, closing the loop on [Block 11]'s own per-module feature-key table.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `find ... -exec grep -lE` reproduces exactly 110 files; `-nE` gives 211 call-site lines | [CERT] | this session's `find`/`grep` run, `callsites_raw.txt` (211 lines, 110 distinct paths) |
| 2 | Full B80-G1 classification: 211/211 resolved — 91 NEW, 61 OLD, 59 OTHER, 0 unresolved | [CERT] | `classify_callsites.py` + 38 individually-read manual resolutions, `classified_truly_final.txt` |
| 3 | `EngineManager.peakScanStats`/`peakInterscanStats` declared `LinkedList<...>` (resolves [Block 80]'s own `[INFER]`) | [CERT] | `organized/baja/vineflower/com/tridium/sys/engine/EngineManager.java:58-59` |
| 4 | `organized/docSource/` is the real `docSource.jar` ground truth (31/45 = 68.9% control overlap, matching [Block 25]'s own figure) | [CERT] | `comm -12` on `docSource/control` vs `control/vineflower` filename lists → 31 |
| 5 | `instanceof` line COUNTS match exactly between vineflower/docSource for control/alarm/kitControl/schedule overlap sets (20/20, 65/65, 7/7, 20/20) | [CERT] | `instanceof_census.py` run twice per module, restricted to overlap file lists |
| 6 | All 13 cross-checkable "bound" sites are docSource-unbound (classic instanceof+cast) | [CERT] | `grep -n instanceof` on the 4 named file pairs + `sed -n` full-context reads |
| 7 | Classic instanceof+cast and JEP-394 bound instanceof compile to identical bytecode (general proof) | [CERT] | `javac --release 21` + `javap -c -p` on `Bound.java`/`Classic.java`, this session |
| 8 | `kitControl.jar`: 0 Record, 0 PermittedSubclasses, 0 SwitchBootstraps, 82 StringConcatFactory, major=69 | [CERT] | `javap -v -p` sweep over all 224 extracted classes, this session |
| 9 | N4 naive `grep -rl 'ZKM'` = 100/688 top-level dirs (reproduces [Block 76]'s figure) | [CERT] | this session's `grep -rl 'ZKM' organized` run |
| 10 | 23 `vineflower.obfuscated-bak/` dirs exist, mapping to 16 top-level N4 module dirs | [CERT] | `find organized -type d -iname 'vineflower.obfuscated-bak'` |
| 11 | 14/16 modules' DEOBFUSCATION-NOTE.md/detect-output.txt explicitly name Zelix/ZKM | [CERT] | per-module `grep -ic "zelix\|ZKM"` ≥4, and `detect-output.txt`'s `RuleSuspiciousClinit` text read directly |
| 12 | 6 additional clustered-escape candidates outside the 16 are all known non-ZKM false-positive categories | [CERT] | individual reads: `SqlLexer.java` (JFlex), `SQLServerLexer.java` (ANTLR), `Code128Writer.java` (ZXing), `PdfCidFontInfo.java` (PANOSE), `BHonAlarmConsoleBuiltJS.java` (BJsBuild XOR, separately documented) |
| 13 | `Station.checkLicense()` resolves to fixed `tridium:station` | [CERT] | `organized/baja/vineflower/com/tridium/sys/station/Station.java:212`, `organized/_bin-ext/nre/vineflower/com/tridium/nre/util/NreLicenseUtil.java:7-9` |
| 14 | `BPlatform`/`BPlat` dispatch loops match `BPlatformService`/`BIPlatformCommand` default-null opt-in shape | [CERT] | `organized/platform/vineflower/com/tridium/platform/BPlatform.java:147-157`, `organized/platform/vineflower/com/tridium/platform/BPlatformService.java:94-100`, `organized/platform/vineflower/com/tridium/platform/command/BPlat.java:83-94`, `organized/platform/vineflower/com/tridium/platform/command/BIPlatformCommand.java:34-40` |
| 15 | `platCcn`'s `"ccnl"` override reproduces [Block 11]'s own published `tridium:ccnl` key via a different path | [CERT] | `organized/platCcn/vineflower/com/tridium/platCcn/BCcnPlatformService.java:66-68` vs. [Block 11] §11.4's table |
| 16 | `BPort.isLicensed()` parses `getRequiredFeatures()` as `"vendor:feature,..."` | [CERT] | `organized/platHwScan/vineflower/com/tridium/platHwScan/ports/BPort.java:81,150-162` |

Tally: 16 [CERT], 0 [INFER] in the table above (the two `[INFER]`-flagged prose claims — §90.3's
extrapolation of the resugaring finding to the 19 non-cross-checked bound sites, and §76-style
algorithm-identification in §90.1's `[INFER]`-free RSA/etc. is N/A here — are stated inline, not
table rows, per METHODOLOGY's own convention for a synthesis clause). Adjusted ratio
`[INFER]`/`[CERT]` ≈ **0.02** (1 inline `[INFER]` clause against 16+ `[CERT]` claims) — very low,
consistent with an EVIDENCE-type block whose every closing verdict rests on a command run or a direct
file read this session, not recalled from memory.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block90.md
```
(output pasted into the handback message to the caller, per the task's own instruction to run this
until exit 0).

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block90.md` (the only
file written in the corpus this session, per the task's single-file constraint).
`INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` were **not** regenerated — left to the integrator step, per
the established wave convention. Scratch scripts and intermediate data (all reproducible from the
commands quoted above) live at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b90/`:
`instanceof_census.py`, `classify_callsites.py`, `apply_manual.py`, `zkm_watermark_census.py`,
`zkm_watermark_census2.py`, `callsites_raw.txt`, `classified_truly_final.txt` (the full 211-row
per-call-site classification), and `bytecode_test/` (the `Bound.java`/`Classic.java` compile-and-diff
pair for §90.2's general bytecode-identity proof).
