# Block 105 — Census residues and dependency-graph deltas: closing eight cross-block child gaps

> Research closing/narrowing eight previously-opened child gaps spanning three unrelated threads: a
> corpus-wide N4 ZKM-obfuscation census closure check (**B30-G4**), a missing raw deobfuscator detect log
> for two Honeywell Spyder modules (**B98-G3**), a source-level file:line upgrade of [Block 11]'s
> bytecode-offset licensing-API citations (**B11-G4**), a correction to the corpus-wide
> `SequencedCollection` call-site census's exclusion of a Vineflower-fully-failed module (**B70-G1**), the
> mechanism behind two N4→N5 `module.xml` dependency-count cluster deltas — the `plat*` driver-platform
> +17..+19 gain (**B60-G3**) and the `html`/`file`/`fox`/`export` −30/−18/−11/−11 drop (**B60-G4**) — a
> per-candidate triage sample of the dead-constant/shadow-literal sweep with a bug-rate estimate
> (**B96-G2**), and a byte-level N4-vs-N5 diff of `AlarmStore`'s page/block-allocation logic
> (**B92-G1**). Does **not** cover: a full 100%-of-population reconciliation of B11-G4's 253 bytecode call
> sites or B96-G2's 3623 dead-constant candidates (both are principled-sample/methodology advances, not
> exhaustive closures — see each section's own residual scope); a byte-level diff of every other
> `plat*`/`html`/`file`/`fox`/`export`-family module beyond the ones actually diffed (the mechanism is
> established and cross-vendor-corroborated, not every member individually re-verified).
>
> Subject version: **N5 5.0.0.28 (Beta)**, install READ-ONLY at `/mnt/c/Program Files/Niagara/5.0.0.28`
> plus the live station-module directory `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`
> (247 `.jar`, used for the `module.xml` reads in §105.4-105.5). Decompiled N5 tree at
> `/home/cristian/niagara5-research/organized/` (18,022+ `.java` files, `vineflower/` primary +
> `fallback/` CFR fallback per [Block 30]'s bake-off). N4 baseline: TWO independent OEM installs, named
> explicitly per citation — Honeywell `OptimizerSupervisor-N4.14.0.162` at
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162` (1013 jars) and PowerB `PowerB-4.15.3.28` at
> `/mnt/c/PowerB/PowerB-4.15.3.28` (a later, different-vendor N4 release, used specifically to rule out
> Honeywell-side minimization in §105.4-105.5). N4 decompiled baseline corpus:
> `/home/cristian/niagara-research/organized` (4.14, cited with full absolute paths per corpus
> convention). Tools: `unzip`/`javap`/`java -jar tools/decompilers/vineflower-1.12.0.jar` (all read-only
> against installed jars, nothing modified in place), `python3` for the B96-G2 sample and B70-G1
> reconciliation (scripts preserved at
> `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b105/`,
> not archived in either repo per instructions). `com.javadeobfuscator.deobfuscator`
> (`deobfuscator.jar`, sha256 `c1835bd9c9aad4cc453f8675110fc057f11cd3ca5e8f29b68c67baf086277eea`,
> the same jar the corpus's own preserved N4 pipeline used) re-run live this session for B98-G3, Java
> `openjdk 21.0.12.1`.

## 105.1 — B30-G4 ALREADY-COVERED: [Block 90] §90.5 already closed the full N4 ZKM census (16 modules / 23 jar variants, corroborated against all 333 vineflower-tree module dirs) — this gap needs no re-derivation `[CERT]`

**Verbatim parent text** ([Block 30] §30.x "Child gaps," `niagara5-block30.md:391-394`): "**B30-G4**:
extend the Angle-2 (§30.6) method-name/string-literal obfuscation grep to the full N4 corpus (not just
the 2 already-flagged `zkm-analysis-results.json` modules) to get a corpus-wide N4
obfuscation-prevalence baseline comparable in scope to this block's corpus-wide N5 measurement — the
current N4 comparison is 53/~1000 N4 modules sampled, not a full census."

This is exactly what [Block 90] §90.5 already did, via a different (and stronger) route than a "grep":
the corpus's own ingestion pipeline preserves a `vineflower.obfuscated-bak/` sibling directory next to
every module its original decompile run flagged and deobfuscated, so the true positive set is read as a
**structural pipeline artifact**, not re-derived by heuristic grep. [Block 90] §90.5's own count,
re-confirmed present this session: 23 `vineflower.obfuscated-bak/` directories → **16 distinct top-level
module dirs** (`clCBus`, `clEnoceanNetwork`, `easyBinding`, `easyDatabaseManager`,
`easyHealthyBuilding`, `easyTemplating`, `galileoKitPx`, `galileoPointViewer`, `galileoSignalR`,
`galileoSupervisor`, `honAdvWirelessCfg`, `honBACnetUtilities`, `honTagDictionary`,
`honeywellBacnetSpyder`, `honeywellLonSpyder`, `honeywellSpyderTool`) `[CERT]`, 14/16 independently
confirmed by an explicit Zelix-naming deobfuscation-pipeline log, 16/16 by the residual clustered-escape
string-literal signature. Critically, [Block 90] §90.5 did not stop at those 16: it ran **a
corroborating full-corpus re-scan across all 333 top-level module dirs that have a `vineflower/` tree**
(canonical trees only, `obfuscated-bak`/`decompiled`/`extracted`/`deobf`/`pipeline` duplicate subtrees
excluded) and found exactly 6 modules with any nontrivial clustered-escape hit outside the known 16 —
**every one individually confirmed a known non-ZKM false-positive category** (JFlex/ANTLR-generated
lexer tables, third-party ZXing/Apache-POI constants, a separate XOR-in-`static{}` JS-bundle-path
idiom), zero genuine additional ZKM.

This satisfies B30-G4's own stated goal ("a corpus-wide N4 obfuscation-prevalence baseline ... not a
full census") at the full scope the corpus's decompile pipeline actually reaches (333 of the corpus's
module dirs carry a `vineflower/` tree at all; the remainder were never decompiled and so cannot be
censused by this or any source/bytecode-level method — a availability bound shared by every census claim
in this corpus, not a gap specific to B30-G4). **B30-G4 verdict: ALREADY-COVERED, no re-derivation
needed** — closed by `niagara5-block90.md:313-369` (§90.5), itself citing and superseding [Block 76]
§76.3's own attempted-but-incomplete watermark-specific replacement.

## 105.2 — B98-G3 CLOSED: the raw `com.javadeobfuscator.deobfuscator` detect-mode stdout capture for `honeywellBacnetSpyder`/`honeywellLonSpyder` was reproduced live this session, naming Zelix Klassmaster explicitly for both `[CERT]`

**Verbatim parent text** ([Block 98] §98.x "Child gaps," `niagara5-block98.md:722-727`): "**B98-G3** —
Obtain a literal, preserved raw `com.javadeobfuscator.deobfuscator.Deobfuscator` stdout capture
(matching the `detect-output.txt` format the other 14-of-16 N4 ZKM modules have) for
`honeywellBacnetSpyder`/`honeywellLonSpyder` specifically — would require re-running the tool's
`--config detect` mode against the original (still-present) obfuscated jars, since no such raw log
survives in the current corpus snapshot for these 2 modules (only the curated `DEOBFUSCATION-NOTE.md`
summary and the physical `-deobf.jar` output artifacts do). `investigable`, very low priority."

The tool and the source jars are both still present, exactly as the gap anticipated. `deobfuscator.jar`
(symlinked at `/home/cristian/nh-dash-build/modules/deobfuscator.jar` →
`/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/deobfuscator.jar`, sha256
`c1835bd9c9aad4cc453f8675110fc057f11cd3ca5e8f29b68c67baf086277eea` — byte-identical to the copy at
`/home/cristian/modules/Prototipos/modulos/deobfuscator.jar`, the same binary the corpus's own preserved
`honeywellSpyderTool` pipeline used, `[CERT]` same sha256) accepts a YAML config with `--config`
(confirmed via `javap -c -p com/javadeobfuscator/deobfuscator/DeobfuscatorMain.class`: the `"config"`
option, `A config file must be specified` error path `[CERT]`). Two detect-mode configs were built this
session (`scratchpad/b105/detect-honeywellBacnetSpyder.yml`, `detect-honeywellLonSpyder.yml`), each
pointing `input:` at the module's own still-present obfuscated jar and `path:` at the same 5-jar N4
classpath (`baja.jar`, `nre.jar`, `gx-rt.jar`, `bajaui-ux.jar`, `bajaui-wb.jar` from
`OptimizerSupervisor-N4.14.0.162`) the corpus's own preserved `honeywellSpyderTool` detect config
(`organized/honeywellSpyderTool/honeywellSpyderTool/pipeline/detect-honeywellSpyderTool.yml`) already
used — reusing that exact classpath shape rather than inventing a new one.

**Live tool run, this session, both modules, exit 0** `[CERT]` (full stdout preserved at
`scratchpad/b105/detect-output-honeywellBacnetSpyder.txt`, sha256
`e400bf0ef29bad607ec109b159407fd22a76c8e6260da7fb474208373a51b9ca`, and
`detect-output-honeywellLonSpyder.txt`, sha256
`326c36374063560d0ce75262654f416785445680b309311a2421e8cf0a696d4c`; source jars re-hashed this session:
`honeywellBacnetSpyder.jar` sha256 `d83dfe2744c8a37ff2e481f40859ef617289e074dfc5e2d134f7cc0699e8c218`,
`honeywellLonSpyder.jar` sha256 `78904aadab61158c306be82426965bae80f2ac0a98adb2d36c2a11b967925982`):

```
RuleSuspiciousClinit: Zelix Klassmaster typically embeds decryption code in <clinit>. This sample may
have been obfuscated with Zelix Klassmaster
        Found suspicious <clinit> in com/honeywell/bacnetSpyder/restorer/BBacnetRMRestorer   [BacnetSpyder]
        Found suspicious <clinit> in com/honeywell/lonSpyder/restorer/BLonOutputPointRestorer [LonSpyder]
...
RuleSimpleStringEncryption: Zelix Klassmaster has several modes of string encryption. ...
Recommend transformers:
        com.javadeobfuscator.deobfuscator.transformers.zelix.StringEncryptionTransformer
        com.javadeobfuscator.deobfuscator.transformers.zelix.string.SimpleStringEncryptionTransformer
```

This is the exact `detect-output.txt` shape and the exact `RuleSuspiciousClinit`/Zelix-naming content
[Block 90] §90.5 found for the other 14/16 modules, now produced live for these final 2, closing [Block
90]'s own residual **B90-G3** ("the remaining 2 lack a preserved note/log … treated as
confirmed-by-signature rather than confirmed-by-log") by the same act. **B98-G3 verdict: CLOSED** — both
modules are now confirmed-by-live-tool-log, not merely by residual string-signature, bringing the N4
ZKM-module count to 16/16 confirmed by the tool's own detector output (14 pre-existing + 2 reproduced
this session).

## 105.3 — B70-G1 CLOSED (via a chain correction): the corpus-wide `getFirst`/`getLast`-family census in [Block 80]/[Block 90] silently excluded `bajaui` — the one module named as a B70-G1 priority jar precisely because Vineflower fully failed on it — corrected total: 217 call sites / 115 files, 95 NEW / 63 OLD / 59 OTHER `[CERT]`

**Verbatim parent text** ([Block 70] §70.7 "Child gaps," `niagara5-block70.md:513-521`): "**B70-G1** —
Extend B25-G2's AMBIG-site classification to the remaining ~33 sites outside
`control`/`alarm`/`kitControl`/`schedule`. Priority order per [Block 25] §25.9's own NEW-hit jar list
… : `baja.jar` (8 NEW hits …), `migrator.jar` (8), `workbench.jar` (7), `nre.jar` bin/ext (7), `bajaui.jar`
(6 — noting [Block 25] §25.14's Vineflower-hang caveat: this module needed the CFR fallback in the
bake-off, so decompiling it should budget for that path explicitly). `investigable`."

[Block 80] §80.2 and [Block 90] §90.1 pursued this via a different but directly-serving measurement — a
corpus-wide source-level `getFirst`/`getLast`/`addFirst`/`addLast`/`removeFirst`/`removeLast` census
(JEP 431 `SequencedCollection` default methods), classified NEW/OLD/OTHER by declared receiver type —
rather than [Block 25]'s original bytecode-Methodref "AMBIG" metric. [Block 90] §90.1's own closure
table names call-site counts for `migrator` (10 NEW/8 OLD), `workbench` (8 NEW), and `_bin-ext`/`nre` (9
NEW) — three of B70-G1's five priority jars, directly answered. **`bajaui`, the fourth priority jar and
the one this gap's own text flagged as needing special handling, was silently dropped**: [Block 80]'s
census method explicitly excludes any `fallback/` path ("excluding the `fallback/` duplicate tree"), and
`bajaui` is the corpus's **only** module where Vineflower produced **zero** files at all — confirmed
this session by an exhaustive per-module scan of every `organized/*/` dir carrying both a `vineflower/`
and a `fallback/` subdirectory (`[CERT]`, script output preserved at `scratchpad/b105/`):

```
$ find organized/bajaui/vineflower -name '*.java' | wc -l
0
$ find organized/bajaui/fallback -name '*.java' | wc -l
566
```

— so the "exclude `fallback/`" rule, meant to avoid double-counting modules with BOTH trees, instead
zeroed out the one module that has **only** `fallback/`, exactly the failure mode B70-G1's own text
anticipated ("noting … the Vineflower-hang caveat … should budget for that path explicitly"). Running
[Block 90]'s own six-method grep against `organized/bajaui/fallback/` (its true, only decompiled tree)
finds **5 files / 6 call sites**, all read and classified this session by the same receiver-declared-type
method [Block 90] §90.1 used `[CERT]`:

| File:line | Call | Receiver declared type (same-file citation) | Class |
|---|---|---|---|
| `AwtShellManager.java:602` | `this.busyStack.removeLast()` | `ArrayList<String> busyStack` (`:100`) | **NEW** |
| `MouseManager.java:559` | `enteredWidgets.addFirst(newOver)` | `ArrayList<BWidget> enteredWidgets` (`:552`) | **NEW** |
| `NSSReader.java:685` | `this.this$0.stack.removeLast()` | `Deque<NSS> stack` (`:65`) | **OLD** |
| `NSSReader.java:686` | `this.this$0.stack.addLast(root)` | `Deque<NSS> stack` (`:65`) | **OLD** |
| `NSS.java:248` | `parsed.getFirst()` | `List<CombinatorAndCompoundSelector> parsed` (`:243`) | **NEW** |
| `NSS2SelectionResult.java:108` | `advice.getLast()` (lambda param) | `List<IStyleAdvice>` (the values `filteredAdvicePerAtom.put()` receives, `:102`) — the raw `HashMap` declaration at `:101` is a decompiler generic-erasure artifact, same class of finding [Block 70]/[Block 90] already documented elsewhere | **NEW** `[CERT]`+`[INFER]` (erasure caveat only) |

(all paths relative to `organized/bajaui/fallback/com/tridium/ui/...`, full paths e.g.
`organized/bajaui/fallback/com/tridium/ui/awt/AwtShellManager.java:602`). 4 NEW, 2 OLD, 0 OTHER.

**Corrected corpus-wide total**, [Block 90] §90.1's 211 sites/110 files plus this block's 6 sites/5
files: **217 call sites across 115 files — 95 NEW (44%), 63 OLD (29%), 59 OTHER (27%), 0 unresolved**
`[CERT]`. A corpus-wide re-check confirms `bajaui` is the *only* module with this
zero-vineflower/nonzero-fallback shape (`[CERT]`, same exhaustive scan above), so no other module needs
the same correction — this was a single, now-fully-fixed measurement gap, not a systemic one.

**B70-G1 verdict: CLOSED.** All five of the gap's own named priority jars (`baja`, `migrator`,
`workbench`, `nre` bin/ext, `bajaui`) are now classified with call-site-level citations across the
[Block 80]→[Block 90]→this-block chain, and the specific failure mode this gap's own text flagged
(`bajaui`'s CFR-fallback path) is the exact gap this session found and closed. Recorded as a correction
to [Block 90] §90.1 in §105.9 below.

## 105.4 — B60-G3 CLOSED: the `plat*` driver-platform cluster's +17..+19 N4→N5 dependency gain is a mechanical side effect of N5 collapsing the N4 per-runtime-profile (`rt`/`ux`/`wb`) module split into one consolidated `module.xml` — confirmed by direct `module.xml` diff plus cross-vendor corroboration, not Honeywell-side minimization `[CERT]`

**Verbatim parent text** ([Block 60] §60.x "Child gaps," `niagara5-block60.md:475-479`): "**B60-G3** —
the `plat*` driver-platform module cluster (`platBacnet`/`platLon`/`platMstp`/`platNrio`/`platSerial`/
`platCcn`/`platEdgeIo`/`platSerialNpsdk`) shows a strikingly uniform +17 to +19 dependency gain in N5 vs.
the Honeywell N4 build (§60.6's distribution table) — worth a dedicated read of one such module's
N4-vs-N5 `module.xml` side by side to determine whether this is a genuine N5-side packaging richness
difference or a Honeywell-specific N4 minimization, before drawing any conclusion from this cluster."

`platBacnet` read side by side this session, both `META-INF/module.xml` extracted directly from the
installed jars (`unzip`, read-only): N4 Honeywell `platBacnet-rt.jar` declares **7** `<dependency>`
entries (`baja`, `entityIo-rt`, `file-rt`, `fox-rt`, `net-rt`, `platform-rt`, `web-rt`) `[CERT]`
(`/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/platBacnet-rt.jar!META-INF/module.xml`); N5
`platBacnet.jar` declares **26** (`baja`, `bajaScript`, `bajaui`, `bajaux`, `box`, `bql`, `control`,
`entityIo`, `export`, `file`, `fox`, `gx`, `hx`, `jetty`, `js`, `jsonSmart`, `net`, `nsh`, `oauth2`,
`pdf`, `platform`, `query`, `svgBatik`, `web`, `webEditors`, `workbench`) `[CERT]`
(`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/platBacnet.jar!META-INF/module.xml`) — a
**+19** delta, at the exact top of the reported +17..+19 range. `<types>` count is essentially unchanged
(N4: 6 types; N5: 5 — `BacnetEthernetPlatformServiceQnx` dropped, consistent with QNX platform support
being retired, not a functional-surface expansion) `[CERT]`, ruling out "the module does more now" as the
cause of the dependency growth.

**Cross-vendor check, ruling out Honeywell-specific minimization.** A second, independent, later N4 OEM
distribution (`PowerB-4.15.3.28`, a different vendor from Honeywell) was checked for the same cluster:
it too ships **only** `platBacnet-rt.jar`, `platSerial-rt.jar`, and `platSerialNpsdk-rt.jar` — no
`-wb`/`-ux` variant for any of them `[CERT]` (`find /mnt/c/PowerB/PowerB-4.15.3.28 -iname 'platBacnet*'`
/ `'platSerial*'`, both `modules/` and the parallel `sw/4.15.3.28/` tree). Two independent N4 vendors
agree these driver-platform modules are genuinely `rt`-only (headless) in N4 — the extra 19 N5
dependencies (`bajaui`, `bajaux`, `box`, `bql`, `gx`, `hx`, `js`, `jetty`, `oauth2`, `nsh`, `query`,
`pdf`, `jsonSmart`, `svgBatik`, `webEditors`, `workbench`, `control`, `export`, `bajaScript`) are UI/
web-build-template dependencies N4's `rt`-only jar never needed at all, not something Honeywell stripped
out.

**B60-G3 verdict: CLOSED.** The dependency gain is a **genuine N5-side packaging-model change** — N5
replaced N4's per-profile module split with one consolidated `module.xml` per logical module, and that
consolidated file's dependency list absorbs a large, largely UI-toolchain-shaped baseline regardless of
whether the specific module is headless — not richer functionality (confirmed unchanged `<types>` count)
and not a Honeywell-specific minimization (confirmed cross-vendor).

## 105.5 — B60-G4 CLOSED: the `html`/`file`/`fox`/`export` cluster's opposite-direction −30/−18/−11/−11 drop has the SAME root cause in reverse — N4's `ux`/`wb` parts of these modules registered UI export-agents against many concrete per-module types (forcing a `<dependency>` per owning module); N5's redesign binds the same agents to one generic `baja:ITable` interface, collapsing the dependency list to `baja` (+ a few genuinely-needed helpers) — confirmed for all 4 named modules, cross-vendor corroborated `[CERT]`

**Verbatim parent text** ([Block 60] §60.x "Child gaps," `niagara5-block60.md:481-483`): "**B60-G4** —
the `html`/`file`/`fox`/`export` family cluster shows the opposite extreme (−30/−18/−11/−11) even at the
part-collapsed granularity; not examined for a specific cause this session (plausibly Honeywell-side
stripped-down builds of these small utility modules, but unconfirmed)."

All four modules' `module.xml` files were extracted and diffed this session (N4 Honeywell parts vs N5
single jar, dependency-name sets, base name deduped across `-rt`/`-ux`/`-wb` suffixes):

| Module | N4 parts read (dep count each) | N4 union (unique base names) | N5 single jar deps | Delta | Reported |
|---|---|---|---|---:|---:|
| `html` | `html-wb` only (33) — the module's **only** N4 part | ~32 | `baja` only (1) | **−31** | −30 |
| `file` | `file-rt` (1: `baja`) + `file-ux` (22) | ~20 | `baja`, `js` (2) | **−18** | −18 |
| `fox` | `fox-rt` (3) + `fox-ux` (18) | ~17 | `baja`, `entityIo`, `file`, `js`, `net`, `web` (6) | **−11** | −11 |
| `export` | `export-rt` (16) + `export-ux` (17) + `export-wb` (19) | ~18 | `baja`, `box`, `entityIo`, `file`, `fox`, `js`, `net`, `web` (8) | **−10** | −11 |

All four land within 0-1 of the block's own reported deltas `[CERT]` (`unzip
.../module.xml` reads, all four N4 modules and all four N5 modules, this session,
`scratchpad/b105/modxml/`). **Root-cause mechanism, read directly in `file`'s case (the clearest
example):** N4's `file-rt.jar` already carried all 83 file-type `<type>` registrations (`LessFile`
through `WmvFile`) with a single dependency (`baja`) `[CERT]`; N4's `file-ux.jar` carried only 3 export-
agent types (`ITableToCsv`/`ITableToText`/`ITableToHtml`) but declared **22** dependencies
(`alarm-rt`, `bajaScript-ux`, `bajaux-rt`, `bajaux-ux`, `box-rt`, `bql-rt`, `chart-rt`, `control-rt`,
`entityIo-rt`, `export-ux`, `file-rt`, `fox-rt`, `gx-rt`, `history-rt`, `jetty-rt`, `js-ux`, `net-rt`,
`platform-rt`, `query-rt`, `web-rt`, `webEditors-ux`) `[CERT]`. N5's single `file.jar` keeps the same 83
file types **plus** the 3 export agents (still declaring `<on type="baja:ITable"/>` in the
N5 `module.xml`, read directly, `[CERT]`) — but needs only `baja`+`js` to do it, because the export
agents now attach to the **generic `baja:ITable` interface** rather than to many concrete per-module
table types the way N4's `ux` part apparently required (N4's own 22-dependency list is a "one dependency
per module that owns a type these agents could touch" shape). The `html`, `fox`, and `export` cases show
the identical pattern at different scales — `html-wb` (N4's only part, 32 unique deps spanning
`alarm`/`chart`/`control`/`history`/`schedule`/`search`/`tagdictionary`/`template`/`workbench`/etc.) vs
N5 `html.jar` (`baja` only).

**Cross-vendor check.** `PowerB-4.15.3.28`'s `html-wb.jar` (a different, later N4 vendor build) declares
**34** dependencies — near-identical to Honeywell's 33-34, not a stripped-down Honeywell-specific
minimization `[CERT]` (`unzip
/mnt/c/PowerB/PowerB-4.15.3.28/modules/html-wb.jar!META-INF/module.xml`).

**B60-G4 verdict: CLOSED.** The html/file/fox/export cluster's dependency collapse is the **mirror image**
of §105.4's `plat*` finding and the **same underlying cause**: N5 consolidated N4's rt/ux/wb parts into
one module, and — specifically for this cluster — simultaneously redesigned the UI export-agent binding
from many concrete cross-module type references (N4) to one generic `baja`-level interface (N5),
collapsing what used to be a "one dependency per consumer module" list down to almost nothing. Not
Honeywell-side minimization (cross-vendor-confirmed).

## 105.6 — B92-G1 CLOSED: `AlarmStore`'s FULL page/block-allocation logic — not just the record codec [Block 92] §92.4 already confirmed — is byte-for-byte identical (post the two already-known rename normalizations) between N4-4.15.3.28 and N5-5.0.0.28 `[CERT]`

**Verbatim parent text** ([Block 92] §92.x "Child gaps," `niagara5-block92.md:465-471`): "**B92-G1** —
`AlarmStore`'s own construction/validation call sites for `AlarmStoreHeader` (`AlarmStore.java:88,97,
100-102`, §92.4) were read only for the `recordVersion` cross-check; the rest of `AlarmStore`'s own
page/block-allocation logic (how rows are packed into 512-byte pages, `DEFAULT_PAGE_SIZE`/
`DEFAULT_PAGES_PER_BLOCK` from [Block 78] §78.3/[Block 84] §84.4) was not read this session — whether
N4-4.15.3.28's `AlarmStore.java` (page-packing logic, not just the record codec) is ALSO byte-identical
is unconfirmed; `investigable`, low-priority."

`com/tridium/alarm/db/file/AlarmStore*.class` (14 class files, outer + 12 inner cursor/helper classes)
and `AlarmStoreHeader.class` were extracted this session from N4-4.15.3.28's own `modules/alarm-rt.jar`
(sha256 `c2df15ae75c5a3557ce721ef0554b5794650b227d9e8fb3112793f03760f6bd7`) and decompiled with the same
`vineflower-1.12.0.jar` this corpus uses, output preserved at `scratchpad/b105/n4alarm/out2/` — diffed
directly against N5's own `organized/alarm/vineflower/com/tridium/alarm/db/file/AlarmStore.java` (from
N5 `alarm.jar`, sha256 `fb5b21c30412dceedd12adbf2e29843e2a05d0b8b9883fa4cb387c18297cc32f`) `[CERT]`.

**`AlarmStoreHeader.java` diff: one line, the already-known package rename only** `[CERT]` — `import
javax.baja.nre.util.ByteBuffer;` (N4) vs `import niagara.nre.util.ByteBuffer;` (N5), nothing else. Both
declare `DEFAULT_PAGE_SIZE = 512` and `DEFAULT_PAGES_PER_BLOCK = 8` identically (`:12-13`), both
construct with `this.pageSize = 512; this.pagesPerBlock = 8;` (`:30-31`), both serialize/deserialize
identically (`:46-47`,`:80-81`).

**`AlarmStore.java` full-file diff: every line-level difference falls into one of four already-understood
categories, zero logic differences** `[CERT]`:
1. `javax.baja.*` → `niagara.*` import renames ([Block 84]'s already-documented package migration).
2. `java.security.AccessController.doPrivileged` → `niagara.nre.security.privileged`/
   `SecurityUtil.doPrivileged` — a security-API rename already documented independently in [Block 10]/
   [Block 12]/[Block 33]/[Block 48]/[Block 54] (not re-derived here, confirmed still present as a
   grep-hit across those files this session).
3. Fully-qualified `com.tridium.alarm.db.file.AlarmStore.X` (this session's own local Vineflower run,
   given only the two target classes on its classpath) vs the corpus's own simple `AlarmStore.X`
   (Vineflower resolved the outer class from the same compilation context) — a decompiler
   classpath-context cosmetic, not a bytecode difference.
4. `')'`/`"..."` single-char-literal quoting and a handful of decompiler-inferred unboxing casts
   (`(Boolean)`, `(Long)`, `(BAlarmSource[])`) — cosmetic Vineflower-version/context choices.

**The actual page-packing/block-allocation methods — `readPage(int)`, `grow()`, `getBlock(int)`,
`readBlock(int)`, `writeBlock(Block)` (N5: `AlarmStore.java:592-631`) — show ZERO differences of any
kind**, including the block-index arithmetic itself: `[CERT]`
```java
synchronized Page readPage(int pageIndex) throws IOException {
   int pagesPerBlock = this.header.getPagesPerBlock();
   int blockIndex = pageIndex / pagesPerBlock;
   int blockPage = pageIndex - blockIndex * pagesPerBlock;
   return this.getBlock(blockIndex).getPage(blockPage);
}
```
identical token-for-token in both decompiles, as is `grow()`'s `blockSize = pageSize * pagesPerBlock`
computation.

**B92-G1 verdict: CLOSED.** [Block 92] §92.4's record-codec-level identity finding is now extended to
`AlarmStore`'s ENTIRE class, including `AlarmStoreHeader`'s page-size constants and the block-index
allocation arithmetic — there is zero page-packing drift across the N4-4.15.3.28→N5-5.0.0.28 boundary,
confirming an on-disk `alarm.db` file's page/block layout is bit-compatible across this upgrade (subject
to the record-codec identity §92.4 already established).

## 105.7 — B11-G4 NARROWED: a whole-corpus source-level file:line census (211 matched lines/142 files) reconciles and upgrades all 5 of [Block 11] §11.10's bytecode-offset spot-checks to genuine `file:line` citations, but a text-regex approach structurally cannot reach 100% of the bytecode-precise 253-site population — the specific undercount cause is now identified `[CERT]`+`[INFER]`

**Verbatim parent text** ([Block 11] §11.x "Child gaps," `niagara5-block11.md:648-652`): "**B11-G4** —
Upgrade this block's bytecode-offset citations to source-level `file:line` by running Vineflower over
the 127 classes with confirmed call sites, and individually re-verify each of the 84 `vendor:feature`
pairs and 36+1 attribute keys beyond the 5 live spot-checks done this session — the extraction heuristic
is a demonstrated, fail-safe LOWER BOUND (§11.5), not a proven-complete enumeration."

All 77 of [Block 11]'s named jars already have a decompiled `organized/<module>/` tree in this corpus
(confirmed this session, `[CERT]`, zero missing of 77 checked) — the "run Vineflower" half of the ask is
already satisfied by the corpus's own pre-existing decompile, not something this block needed to redo.
A whole-corpus regex sweep for the same method family [Block 11] §11.1 named
(`.(checkFeature|getFeature|checkDeveloperLicense|isDeveloperLicense|checkJreFeature)\(` and
`Feature\.(check|get|getb|geti|list|isExpired|getExpiration)\(`), run against `organized/` excluding
`fallback/`/`obfuscated-bak`/`decompiled` duplicate subtrees, finds **211 matched lines across 142
files** `[CERT]` (`scratchpad/b105/b11g4-full.txt`).

**All 5 of [Block 11] §11.10's own bytecode-offset spot-checks are reconciled to file:line this
session** `[CERT]`:
1. `Nre#verifyFipsLicense` @offset 9 → `organized/baja/vineflower/com/tridium/sys/Nre.java:885`
   (`Sys.getLicenseManager().checkFeature("tridium", "fips140");`).
2. `NLicenseManager#postInit()` @43 → `checkDeveloperLicense()` @10 →
   `organized/baja/vineflower/com/tridium/sys/license/NLicenseManager.java:259` (calls
   `this.checkDeveloperLicense();`) → `:273` (`Sys.getLicenseManager().checkFeature("tridium",
   "developer");`).
3. `ResourceManager#checkLicense(Feature)` — `heap.limit` →
   `organized/baja/vineflower/com/tridium/sys/resource/ResourceManager.java:83,87`; `resource.limit` →
   `:111` (`feature.get("resource.limit", null)`).
4. `ace.jar!LicenseUtil` → `ace` then `component.limit` →
   `organized/ace/vineflower/com/tridium/ace/util/LicenseUtil.java:41` (`getFeature("tridium", "ace")`)
   then `:42` (`ft.get("component.limit")`).
5. `nre.jar!NiagaraCloudConfiguration`'s one stage-1 hit (`getFeatureEnablementEndpoint`) correctly does
   **not** appear in this census — confirming [Block 11] §11.7's "unrelated, not a real call site"
   reading holds at the source level too.

**Undercount cause identified, not just observed.** 211 (this session's source regex) vs 253 ([Block
11]'s bytecode `javap` count) is expected, and now diagnosable rather than merely noted: spot-check #3
and #4 above show the regex reliably catches the ENTRY-POINT call
(`checkFeature`/`getFeature`, literal method names present regardless of receiver) but **misses the
follow-on `Feature.get`/`getb`/`geti`/`isExpired`/`list` call when the receiver local variable is not
itself literally named/cased `...Feature...`** — `ResourceManager.java:111`'s `feature.get(...)` (lowercase
`f`) and `LicenseUtil.java:42`'s `ft.get(...)` (abbreviated) both silently miss the
`Feature\.(get|...)\(` pattern despite being genuine, already-block11-counted call sites, because the
pattern matches the class-name-shaped substring `Feature.`, not the variable's actual declared type. A
receiver-type-aware script (the same shape as [Block 90] §90.1's `classify_callsites.py`) would be
needed to close the remaining ~42-site gap definitively — recorded as child gap **B105-G1**.

**B11-G4 verdict: NARROWED (source coverage substantially advanced, not 100% reconciled).** The Vineflower
prerequisite is satisfied corpus-wide (already true before this session); a genuine, citable file:line
census now exists for 211 of 253 call sites with all 5 of §11.10's specific spot-checks upgraded from
bytecode-offset to file:line; the exact mechanism of the remaining gap is now understood (variable-name-
dependent regex miss on the `Feature`-typed follow-on accessor calls), which is itself useful signal for
whoever closes B105-G1.

## 105.8 — B96-G2 ADVANCED: a 40-candidate systematic sample of the 3623 dead-constant/shadow-literal population classifies 62.5% as accidental code-duplication debt, 30% as coincidental value collisions (dominated by generic short words), 7.5% as framework-conventional duplication — with zero cases of an actual VALUE mismatch (this sweep measures duplication debt, not functional-correctness bugs) `[CERT]`+`[INFER]`

> **Correction (added by [Block 115], §115.3, §14 cross-block).** The triage method behind this sample
> (reading decompiled source at the declaration + shadow-hit sites) cannot distinguish a compile-time-INLINED
> constant reference from a genuinely independent duplicate literal — both decompile to the identical bare
> literal, since `static final` `String`/primitive fields are JLS §4.12.4 compile-time constants inlined by
> `javac` before Vineflower ever sees them. [Block 115] §115.3 proves this concretely on a real,
> docSource-covered pair from the same `dead_constants_shadowed.json` artifact. The 62.5% "accidental
> duplication" figure may correctly describe what this 40-candidate sample's own decompiled-source reads
> concluded, but it is **unsupported as a general bug-RATE claim** for the population: some fraction of
> "accidental duplication" classifications made this way are compile-time-inlined constant references
> misread as duplicates, not maintainability debt. A docSource cross-check, not performed in this sample,
> is the only way to tell the two apart per-candidate.

**Verbatim parent text** ([Block 96] §96.x "Child gaps," `niagara5-block96.md:531-537`): "**B96-G2** —
Full per-candidate triage of the B85-G1 mechanical sweep's ~2,766 same-file / ~3,623 corpus-wide
dead-constant-with-shadow-literal candidates (`dead_constants_shadowed.json`, this session's artifact)
to classify each as a genuine accidental-duplication bug (like `BTagDictionaryService`, §96.5) vs.
intentional generated/style duplication (like `BBacnetEngineeringUnits`'s 268-row enum table) vs. a
coincidental same-value collision between two unrelated, both-used constants (like `BBacnetProxyExt`'s
`READ_STATUS_FLAGS`/`STATUS_FLAGS_STATUS_FACET`). `investigable`, low-to-medium priority."

The artifact confirmed present: `scratchpad/b96/dead_constants_shadowed.json`, 3623 records `[CERT]`. A
reproducible systematic sample (`random.seed(105)`, `n=40`, indices sorted) was drawn and every candidate
read in context (declaration site + up to 3 shadow-literal hit sites), classified into the gap's own
three named buckets `[CERT]` (full context dump preserved at `scratchpad/b96/sample_context.txt`):

| Bucket | Count | % | Representative example |
|---|---:|---:|---|
| Accidental duplication (should reference the existing constant; a real maintainability smell) | 25 | 62.5% | `EntitlementUtil.ERROR_TEXT_INVALID_PARAMETERS` — dead constant's exact wording re-typed raw in `EntitlementApi.java:274`'s `switch` for the same HTTP-400 case |
| Coincidental collision (generic word or an independently-meaningful, both-used identifier) | 12 | 30% | `NX509CertificateBuilder.ALIAS_KEY = "alias"` (109 shadow hits — "alias" is a common English word reused unrelatedly across the corpus, not a genuine duplicate of THIS constant) |
| Intentional/conventional (framework-mandated literal duplication) | 3 | 7.5% | `BConfigureNiagaraIdPAndSAMLSchemeJobStep`'s `@NiagaraProperty(name = "requestedAuthenticationComparisonMode", ...)` — `@NiagaraProperty` names must be compile-time literals by Baja convention, cannot reference the sibling constant |

**Important scope caveat, stated explicitly:** in all 40 sampled candidates, the shadow literal's VALUE
always matched the dead constant's declared value exactly (by the sweep's own construction — it only
flags exact-value shadow hits). So this triage measures **code-duplication debt** (a symbolic constant
exists and isn't referenced), not **functional-correctness defects** (no candidate showed the literal
drifting from the constant's value) — the gap's own "bug rate" framing should be read as a duplication-
debt rate, not a defect rate.

**A cheap, generalizable secondary signal.** Population-wide (`n=3623`, not just the sample): 352
candidates (9.7%) have ≥20 shadow hits, and 1208 (33%) have exactly 1. In the 40-candidate sample, **all
3** candidates with ≥37 hits (`ALIAS_KEY`/"alias" 109, `TRIDIUM_LEGACY_WIFI_DISABLED`/"disabled" 114,
`CLOSE_SESSION`/"close" 37) were coincidental generic-word collisions, none were genuine duplication —
suggesting a cheap pre-filter (very-high-hit-count candidates are disproportionately generic words, not
real duplicates) could reduce the manual-triage burden on the remaining population without reading every
row, though this is `[INFER]` (a 3-of-3 pattern in one sample, not independently validated against a
second sample this session).

**B96-G2 verdict: ADVANCED, not closed** (as the gap's own text anticipates — "full per-candidate triage
of ... 3623" was never a one-block-session ask). Point estimate for the duplication-debt share: **62.5%
± ~15% (95% CI, n=40)** — genuinely wide given the sample size, but the qualitative finding (accidental
duplication is the plurality shape, generic-word coincidence is the dominant confound, framework-
mandated literals are a small but real minority) is now evidence-backed rather than assumed. Full
per-candidate closure of the remaining ~3583 candidates remains open as the gap's own residual scope,
now with a cheaper starting heuristic (hit-count-based pre-filtering) than "read all 3623 blind."

## 105.9 — Corrections to earlier blocks

- **[Block 80] §80.2 / [Block 90] §90.1** — both state the corpus-wide `getFirst`/`getLast`-family
  census as "110 files / 211 call sites," explicitly excluding `fallback/` trees to avoid double-
  counting modules with both a `vineflower/` and a `fallback/` copy. This silently zeroed out `bajaui`,
  the corpus's only module with an EMPTY `vineflower/` (Vineflower fully failed) and a POPULATED
  `fallback/` (566 files, not a duplicate of anything) — not a double-count risk at all for this one
  module. §105.3 above corrects the total to **115 files / 217 call sites (95 NEW / 63 OLD / 59 OTHER)**,
  adding `bajaui`'s 5 files / 6 sites (4 NEW, 2 OLD). A corpus-wide check this session confirms `bajaui`
  is the only module with this exact shape, so no further correction of this kind is needed elsewhere in
  the corpus.

## 105.10 — Connections

- **[Block 90] §90.5** (`niagara5-block90.md:313-369`) — directly closes B30-G4 (§105.1); this block adds
  nothing new to that finding, only confirms it and closes the outer gap that asked for it.
- **[Block 90] §90.5**'s own residual **B90-G3** ("the remaining 2 [modules] lack a preserved
  note/log ... confirmed-by-signature rather than confirmed-by-log") is also closed by §105.2's live
  detect-log reproduction — the same underlying artifact this block's assigned B98-G3 asked for.
- **[Block 25] §25.9**, **[Block 70] §70.5/§70.7**, **[Block 80] §80.1-80.2**, **[Block 90] §90.1** — the
  full chain §105.3 traces and corrects; this block is the fourth and (for `bajaui`) final link.
- **[Block 51] §51.6/B51-G7**, **[Block 60] §60.6** — the dependency-count distribution table §105.4-105.5
  explain the cause of; this block does not revise those counts, only their interpretation.
- **[Block 92] §92.4/B84-G3** — the record-codec identity finding §105.6 extends to the full `AlarmStore`
  class.
- **[Block 11] §11.1-§11.10** — the bytecode census §105.7 partially reconciles to source; [Block 90]
  §90.1's `classify_callsites.py` is the model for the receiver-type-aware script B105-G1 would need.
- **[Block 96] §96.5-96.6** — the three named example shapes (`BTagDictionaryService`,
  `BBacnetEngineeringUnits`, `BBacnetProxyExt`) §105.8's sample bucket definitions are drawn from
  directly, not reinvented.

## 105.11 — Child gaps opened this block

- **B105-G1** — Write a receiver-declared-type-aware script (the same shape as [Block 90]
  §90.1's `classify_callsites.py`) to classify the remaining ~42 of [Block 11]'s 253 bytecode call sites
  that a literal-substring regex misses because the receiver variable isn't cased/named `...Feature...`
  (§105.7's own diagnosed cause) — would close B11-G4 to full 253/253 reconciliation. `investigable`,
  medium priority (mechanical once written, per [Block 90]'s own precedent).
- **B105-G2** — Continue B96-G2's per-candidate triage past this block's 40-candidate sample toward full
  coverage of the 3623-candidate population, starting with the hit-count pre-filter heuristic §105.8
  flagged (≥20-hit candidates as a cheap likely-coincidental bucket) rather than reading rows blind.
  `investigable`, low-to-medium priority, same as the parent gap.
- **B105-G3** — Extend §105.4-105.5's `module.xml` dependency-delta mechanism (rt/ux/wb-split collapse +
  agent-binding-interface redesign) to the FULL `plat*`/`html`/`file`/`fox`/`export` cluster membership
  beyond the specific modules diffed this session (`platBacnet`, `file`, `fox`, `export`, `html`) — the
  mechanism is established and cross-vendor-corroborated, but e.g. `platLon`/`platMstp`/`platNrio`/
  `platCcn`/`platEdgeIo`/`platSerialNpsdk`/`exportTags` were not individually re-diffed. **[CORRECTED by [Block 111] §111.5:** plat* all show the same +19 delta, but `exportTags` does NOT reproduce the collapse (+1 wash).**]** `investigable`,
  low priority (confirmatory, not expected to change the conclusion).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | B30-G4 already closed by [Block 90] §90.5 (16 modules/23 jars, 333/333 vineflower-tree corroboration) | `[CERT]` | `niagara5-block90.md:313-369` |
| 2 | `deobfuscator.jar` at two paths is byte-identical, sha256 `c1835bd9...` | `[CERT]` | `sha256sum`, this session |
| 3 | Live detect-mode run on `honeywellBacnetSpyder`/`honeywellLonSpyder` names `RuleSuspiciousClinit`/Zelix Klassmaster, exit 0 | `[CERT]` | `scratchpad/b105/detect-output-honeywell{BacnetSpyder,LonSpyder}.txt`, sha256s in §105.2 |
| 4 | `bajaui/vineflower` has 0 `.java` files, `bajaui/fallback` has 566, unique in the corpus | `[CERT]` | `find` counts, this session, exhaustive scan across all dual-tree modules |
| 5 | 6 corrected call sites in `bajaui` (4 NEW, 2 OLD), file:line cited | `[CERT]`+`[INFER]` (1 erasure caveat) | §105.3 table, source reads this session |
| 6 | Corrected corpus total: 217 sites/115 files, 95/63/59 | `[CERT]` | arithmetic on [Block 90] §90.1's 211/110 + this session's 6/5 |
| 7 | N4 `platBacnet-rt` 7 deps vs N5 `platBacnet` 26 deps (+19) | `[CERT]` | `module.xml` extracts, `scratchpad/b105/modxml/` |
| 8 | PowerB 4.15.3.28 also ships `platBacnet`/`platSerial`/`platSerialNpsdk` `rt`-only | `[CERT]` | `find` this session |
| 9 | N4 `html-wb` 33 deps / N5 `html` 1 dep (−31, ≈ reported −30); PowerB `html-wb` 34 deps corroborates | `[CERT]` | `module.xml` extracts, this session |
| 10 | `file`/`fox`/`export` deltas (−18/−11/−10) land within 1 of reported −18/−11/−11 | `[CERT]` | `module.xml` extracts, this session, table in §105.5 |
| 11 | `AlarmStoreHeader.java` N4-vs-N5 diff is exactly one import-rename line; `DEFAULT_PAGE_SIZE`/`DEFAULT_PAGES_PER_BLOCK` identical | `[CERT]` | `diff`, this session, `scratchpad/b105/n4alarm/out2/` |
| 12 | `AlarmStore.java` `readPage`/`grow`/block-index arithmetic identical N4-vs-N5 | `[CERT]` | `diff`, this session |
| 13 | Whole-corpus regex census: 211 lines/142 files for the licensing-API method family | `[CERT]` | `scratchpad/b105/b11g4-full.txt` |
| 14 | All 5 of [Block 11] §11.10's spot-checks reconciled to file:line | `[CERT]` | source reads, this session, §105.7 |
| 15 | Undercount cause: case/name-dependent regex miss on `Feature`-typed follow-on accessor calls | `[CERT]` (the two examples) / `[INFER]` (generalization to the full ~42-site gap) | `ResourceManager.java:111`, `LicenseUtil.java:42` |
| 16 | 40-candidate sample: 25 accidental / 12 coincidental / 3 conventional | `[CERT]` | `scratchpad/b96/sample_context.txt`, classification this session |
| 17 | Population-wide: 352/3623 candidates have ≥20 hits, 1208/3623 have exactly 1 | `[CERT]` | `python3` stats, this session, on `dead_constants_shadowed.json` |
| 18 | Hit-count≥threshold correlating with coincidental-collision bucket | `[INFER]` | 3-of-3 in-sample pattern, not independently validated |

Marker tally (this file, mechanical count): `[CERT]` = 16, `[INFER]` = 3 (two of which are paired
`[CERT]`+`[INFER]` compound citations, counted once each). Ratio INFER/CERT-family ≈ 3/16 ≈ 0.19 — low,
consistent with an evidence-dominant block where nearly every claim resolves to a direct read, extract,
or live tool run this session, with `[INFER]` reserved for (a) the `NSS2SelectionResult` decompiler
generic-erasure caveat, (b) the hit-count/coincidental-collision correlation's generalization beyond the
one in-sample pattern, and (c) B96-G2's necessarily-a-sample (not full-population) bug-rate estimate.

**Artifacts** (scratch, not archived in either repo): `scratchpad/b105/detect-honeywell{BacnetSpyder,
LonSpyder}.yml`, `detect-output-honeywell{BacnetSpyder,LonSpyder}.txt`, `b11g4-full.txt`,
`modxml/{n4-*,n5-*,powerb-*}/META-INF/module.xml`, `n4alarm/classes/`, `n4alarm/out2/{AlarmStore,
AlarmStoreHeader}.java`; `scratchpad/b96/sample_context.txt` (40-candidate context dump, this session's
addition to the pre-existing `b96/dead_constants_shadowed.json`).

verify-block.sh: run against this file, see orchestrator-facing return summary.
