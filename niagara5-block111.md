# Block 111 — Four cross-block census extensions: a receiver-type-aware Feature-API script, a stratified dead-constant re-sample, six more plat*/exportTags module.xml diffs, and an exhaustive template-comment read

> Research advancing/closing four previously-opened child gaps, all extensions of prior census/sweep
> methods rather than new investigations: **B105-G1** ([Block 105] §105.7/§105.11 — write a
> receiver-declared-type-aware script, the same shape as [Block 90]'s `classify_callsites.py`, to find the
> licensing-API `Feature.get()`/`getb()`/`geti()`/`list()`/`isExpired()`/`getExpiration()`/`check()` call
> sites [Block 105]'s literal-substring regex missed because the receiver variable isn't cased/named
> `...Feature...`); **B105-G2** ([Block 105] §105.8/§105.11 — continue the dead-constant/shadow-literal
> triage past [Block 105]'s 40-candidate sample, "starting with the hit-count pre-filter heuristic"); **
> B105-G3** ([Block 105] §105.4-105.5/§105.11 — extend the `module.xml` rt/ux/wb-consolidation mechanism to
> the rest of the `plat*`/`html`/`file`/`fox`/`export` cluster: `platLon`/`platMstp`/`platNrio`/`platCcn`/
> `platEdgeIo`/`platSerialNpsdk`/`exportTags`); **B106-G3** ([Block 106] §106.7/§106.x — an exhaustive,
> non-keyword-filtered read of the 5,161 `ndriver`/`videodriver` `.vm` template lines beyond the
> TODO/NOTE/IMPORTANT/WARNING/MUST/REQUIRED keyword sweep). Does **not** cover: a full 100%-of-population
> reconciliation of B11-G4's original 253-site bytecode census (B105-G1's script closes its OWN narrower
> ask — build+run+evaluate — not the parent B11-G4 gap, which stays as [Block 105] left it); full
> per-candidate triage of the 3623-candidate dead-constant population (B105-G2 draws one more principled
> stratified sample, cumulative n=160/3623 ≈ 4.4%, not the full set); a byte-level diff of every
> conceivable `plat*`-family module (only the 6 named stragglers plus `exportTags` were diffed this
> session, on top of [Block 105]'s `platBacnet`/`html`/`file`/`fox`/`export`).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (used read-only for B105-G1). N5 config/module mirror (READ-ONLY): `/mnt/c/ProgramData/Niagara/tridium/
> config/5.0.0.28/modules/` (used for B105-G3's N5 `module.xml` reads). N4 baseline, TWO independent OEM
> installs (used for B105-G3's N4 `module.xml` reads): Honeywell `OptimizerSupervisor-N4.14.0.162` at
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162` and PowerB `PowerB-4.15.3.28` at
> `/mnt/c/PowerB/PowerB-4.15.3.28` (confirmed present for cross-vendor corroboration, not separately
> diffed this session since [Block 105]'s own cross-vendor check already ruled out Honeywell-side
> minimization for this exact mechanism). [Block 96]'s own `dead_constants_shadowed.json` artifact
> (3623 records, preserved at a PRIOR session's scratch, `/tmp/claude-1000/-home-cristian-niagara-research/
> dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b96/dead_constants_shadowed.json`, read this session,
> not regenerated) for B105-G2. [Block 106]'s own re-extracted `n-templates-5.0.54.9.2.jar` `.vm` templates
> (preserved at that same prior session's scratch, `.../scratchpad/b106/templates/gradle/`, 56 files, 5,161
> lines, read this session, not re-extracted) for B106-G3. Tools: `python3` (both new scripts, this
> session's own artifacts, preserved at `/tmp/claude-1000/-home-cristian-niagara-research/
> 4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b111/`, not archived in either repo per instructions),
> `unzip` (module.xml reads, read-only against installed jars).
>
> Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line` or a `module.xml`
> extract, this session) · `[INFER]` deduction/classification-judgment, explicitly flagged by confidence
> tier where more than one tier is used in the same section.

---

## 111.1 — B105-G1 CLOSED: a receiver-declared-type-aware census script, built and run this session, finds 76 additional `Feature`-typed follow-on call sites the literal-substring regex missed — nearly double the ~42 [Block 105] §105.7 diagnosed; the script itself is judged NOT worth promoting to `tools/` `[CERT]`

**Verbatim parent text** ([Block 105] §105.11 "Child gaps opened," `niagara5-block105.md:458-462`):
"**B105-G1** — Write a receiver-declared-type-aware script (the same shape as [Block 90] §90.1's
`classify_callsites.py`) to classify the remaining ~42 of [Block 11]'s 253 bytecode call sites that a
literal-substring regex misses because the receiver variable isn't cased/named `...Feature...` (§105.7's
own diagnosed cause) — would close B11-G4 to full 253/253 reconciliation. `investigable`, medium priority."

**ALREADY-COVERED check**: `rg -il "receiver.declared.type|classify_callsites" niagara5-block*.md` finds
only [Block 90] (the method's origin) and [Block 105] (this gap's own text) — no block has already written
this script. Proceeding.

**Method.** [Block 90] §90.1's `classify_callsites.py` (`/tmp/claude-1000/-home-cristian-niagara-research/
dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b90/classify_callsites.py`, read this session for the
pattern) resolves a call receiver's declared type by scanning the SAME FILE for a local-var/field
declaration of that identifier. This session's `feature_census.py`
(`/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b111/
feature_census.py`) adapts the same shape to a single target type instead of a NEW/OLD/OTHER family:
1. Scope to files that import or fully-qualify `niagara.license.Feature` at all (100 files, corpus-wide,
   `grep -rl`, excluding `fallback/`/`obfuscated-bak`/`decompiled`/`docSource` duplicate trees) — a file
   with no such reference cannot declare a `Feature`-typed variable `[CERT]`.
2. Within each scoped file, find every declaration whose TYPE token is the bare word `Feature` (name-
   independent, unlike the old regex) via `\bFeature\s+([A-Za-z_$][\w$]*)\s*[=;,)]`.
3. For each declared name, find every `<name>.method(` call in the same file for `method` in `{get, getb,
   geti, list, isExpired, getExpiration, check}`.
4. Separately catch the no-intermediate-variable chained shape `....getFeature(...).method(...)` (still
   declared-type-aware: `getFeature()`'s own return type is `Feature` by the interface's own signature,
   `organized/baja/vineflower/niagara/license/Feature.java:1-22`, confirmed this session `[CERT]`).

**Run, this session** (`scratchpad/b111/feature_census_output.txt`): 100 files scoped, 53 with ≥1
bare-`Feature`-typed declaration, 56 total declarations, **92 distinct call sites** resolved by declared
type. Diffed against [Block 105]'s own 211-line literal census (`b11g4-full.txt`): 16 already present, **76
NEW** — nearly double [Block 105] §105.7's own ~42-site estimate `[CERT]`. Every new site spot-checked
resolves to a genuine `Feature`-typed local variable named with NO `Feature` substring at all, exactly the
diagnosed failure mode — confirmed directly this session for [Block 105] §105.7's own two diagnosed
examples: `organized/baja/vineflower/com/tridium/sys/resource/ResourceManager.java:111`'s `feature.get(...)`
(receiver `feature`, the method's own `Feature`-typed PARAMETER — `public void checkLicense(Feature
feature)`, `:81`) and `organized/ace/vineflower/com/tridium/ace/util/LicenseUtil.java:42`'s `ft.get(...)`
(receiver `ft`, declared `Feature ft = Sys.getLicenseManager().getFeature("tridium", "ace");` one line
above, `:41`) `[CERT]` — both now reproduced by an automated tool rather than by hand. New sites this session's script additionally found that [Block 105] did NOT hand-diagnose:
`organized/workbench/vineflower/com/tridium/workbench/shell/WbMain.java:665,680,696,682,683`'s `wb`/`about`
variables, `organized/bacnet/vineflower/com/tridium/bacnet/stack/link/mstp/BBacnetMstpLinkLayer.java:
204,209,210`'s `mstp`, `organized/platDataRecovery/vineflower/com/tridium/platDataRecovery/
BDataRecoveryService.java:520-521`'s `dataRecovery`, `organized/platIEEE8021X/vineflower/com/tridium/
platIEEE8021X/BIEEE8021XPlatformService.java:144`'s `ieee8021x` — all confirmed by direct read this session
`[CERT]` (declaration lines, full paths given above: `Feature wb = licenseManager.checkFeature("tridium",
"workbench");`; `Feature mstp = Sys.getLicenseManager().getFeature("tridium", "mstp");`; `Feature
dataRecovery = Sys.getLicenseManager().getFeature("tridium", "dataRecovery");`).

**Residual, honestly scoped, not re-derived further this session.** A 9-line gap between the script's
92-site output and [Block 105]'s 211-line "follow-on-only" 22-line subset (211 total split cleanly into 189
entry-point + 22 follow-on, zero overlap, confirmed this session by re-running both sub-patterns separately
`[CERT]`) resolves as: 4 lines in `organized/docSource/` (a javadoc-stub tree correctly excluded by this
script's own scoping, same convention as every other census in this corpus) and 5 lines in
`organized/_bin-ext/niagarad/`'s OWN separate, unrelated `com.tridium.niagarad.license.Feature` class (a
textually-identical-shaped but structurally DISTINCT type in the `niagarad` daemon module, confirmed by
direct read `[CERT]`, `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/license/Feature.java:1-5`
— `package com.tridium.niagarad.license; ... public class Feature {...}`, not an import of
`niagara.license.Feature`). This is a genuine, narrow scope boundary (this script targets ONE specific
interface by design), not a bug — recorded as child gap **B111-G1** below rather than silently absorbed.

**Promotion judgment (the gap's own explicit ask).** `feature_census.py` is judged **NOT worth promoting to
`tools/`**: it is single-purpose (hardcoded to one interface, `niagara.license.Feature`, and one fixed
method-name family), will not be reused for any other census in this corpus, and the general TECHNIQUE
(same-file declared-type resolution) already has a durable, more-general template in [Block 90]'s own
`classify_callsites.py`, which itself stayed in scratch rather than `tools/` — consistent with this corpus's
own precedent that one-off receiver-type census scripts are scratch artifacts, not registry tools.

**B105-G1 verdict: CLOSED.** The gap's own literal ask — write the script, run it, report whether it is
worth promoting — is fully discharged: script written (`scratchpad/b111/feature_census.py`), run (92 sites
found, 76 new), promotion judged negative with reasoning. This does NOT itself re-close the parent B11-G4
(still NARROWED as [Block 105] left it — the 253-vs-211/287 population-scope question is a separate,
larger question this narrower script was never asked to resolve), but it substantially outperforms the
±42-site estimate the parent gap's own diagnosis produced.

## 111.2 — B105-G2 ADVANCED: a new, disjoint n=120 stratified sample (60 candidates ≥20 shadow-hits, 60 <20 hits) quantifies [Block 105] §105.8's hit-count heuristic far beyond its original 3-of-3 in-sample pattern — the two buckets show INVERTED duplication-debt rates (≥20-hit: 15% accidental / 61.7% coincidental / 23.3% conventional; <20-hit: ~78% accidental / 10% coincidental / 10% conventional) `[CERT]`+`[INFER]` (tiered, see below)

**Verbatim parent text** ([Block 105] §105.11, `niagara5-block105.md:463-466`): "**B105-G2** — Continue
B96-G2's per-candidate triage past this block's 40-candidate sample toward full coverage of the
3623-candidate population, starting with the hit-count pre-filter heuristic §105.8 flagged (≥20-hit
candidates as a cheap likely-coincidental bucket) rather than reading rows blind."

**ALREADY-COVERED check**: no later block references B105-G2 or a continued dead-constant triage — proceeding.

**Method** (`scratchpad/b111/sample_b111.py`, seed=111, disjoint by construction from [Block 105]'s
seed=105 sample): stratified the 3623-record population into bucket A (≥20 shadow hits, 352 records) and
bucket B (<20 hits, 3271 records) — exactly the split §105.8's own heuristic proposed — and drew 60 from
each (n=120 total), dumping declaration + up to 3 shadow-hit-site context per candidate
(`scratchpad/b111/sample_context_b111.txt`, 1594 lines).

**Confidence is explicitly tiered, not uniform**, and reported as such rather than presented as one
uniform-rigor number: **Tier 1** (24 of the 60 bucket-A candidates) got a full context read matching
[Block 96]'s B96-G2 method (declaration + shadow-hit-site content) — `[CERT]`-grounded. **Tier 2** (the
remaining 36 bucket-A candidates + all 60 bucket-B candidates) were classified from declaration
name/value/hit-count alone (no shadow-hit-site content read) — a lighter, `[INFER]`-level pass, disclosed
honestly because this session's token/time budget did not extend to full-context reads for all 120.

**Bucket A (≥20 hits, n=60) tally**: 37 coincidental (61.7%) / 14 conventional (23.3%) / 9 accidental
(15%) — Tier-1-only sub-tally (n=24): 14/6/4 (58.3%/25%/16.7%); Tier-2-only sub-tally (n=36): 23/8/5
(63.9%/22.2%/13.9%) — the two tiers agree closely, which is itself evidence the lighter Tier-2 method is a
usable proxy for the heavier one on this specific stratum. Representative confirmed examples: `DATA_TYPE_
BOOLEAN='boolean'` (1,558 hits, the single highest-hit-count candidate in the ENTIRE 3623 population) —
unambiguously coincidental, the word "boolean" is a generic type-name token with no possible shared
meaning across its hit sites `[CERT]`; `NULL_ENCODING='null'` (411 hits) — same shape `[CERT]`;
`STATUS_FLAGS_STATUS_FACET='statusFlags'` (42 hits, `organized/bacnet/vineflower/niagara/bacnet/point/
BBacnetProxyExt.java:144`) — reproduces [Block 96]'s OWN canonical coincidental-collision example
(`READ_STATUS_FLAGS`/`STATUS_FLAGS_STATUS_FACET`, both declared in the SAME file, `:140,144`) exactly,
confirming this session's classification calibrates correctly against a known ground truth `[CERT]`. A
genuine accidental-duplication PAIR was found within bucket A itself: `_SCRAM_GLIBC_SHA512_NATIVE`/
`_SCRAM_GLIBC_SHA256_NATIVE` (both declared in `organized/_bin-ext/niagarad/vineflower/com/tridium/
niagarad/util/DaemonAuthUtil.java`, 25 hits each) — two sibling SASL-mechanism-name constants in the SAME
file, the exact `BTagDictionaryService`-shaped accidental-duplication pattern `[CERT]`.

**Bucket B (<20 hits, n=60) tally** (Tier 2 only, value/name-judgment, no shadow-hit-content read):
~47 accidental-leaning (78.3%) / 6 coincidental (10%) / 6 conventional (10%) / 1 uncertain (1.7%). A
confirmed accidental PAIR mirrors bucket A's: `NEW_POLL_SLOT`/`POLL_SCHEDULER_PROP`, both = `'pollScheduler'`
(12 hits each, in two DIFFERENT migrator bog-converter classes — `organized/migrator/vineflower/com/
tridium/migrator/video/BVideoPollSchedulerBogConverter.java:19` and `.../opcua/BOpcUaDeviceBogConverter.
java:22`) `[CERT]`. Conventional examples confirmed matching [Block 96]'s own cited shape: `CURRENCY_5_NAME`/
`KILOJOULES_PER_DEGREE_KELVIN_NAME`/`GRAMS_PER_LITER_NAME`, all three from `organized/bacnet/vineflower/
niagara/bacnet/enums/BBacnetEngineeringUnits.java` — the SAME 268-row generated-enum-table module [Block
96] §96.5-96.6 already named as the canonical "intentional/conventional" example `[CERT]`.

**The two buckets' rates are the near-mirror-inverse of each other** — bucket A (≥20 hits) is
coincidental-dominant (61.7%) with accidental duplication comparatively RARE (15%); bucket B (<20 hits) is
accidental-dominant (78.3%) with coincidental collision comparatively rare (10%). This is a much larger,
disjoint, independently-drawn confirmation of [Block 105] §105.8's own flagged pattern (previously only
3-of-3 in one sub-sample) — the hit-count pre-filter heuristic is now evidence-backed at n=120 rather than
n=3, and can be stated with real percentages instead of only a qualitative "suggests."

**B105-G2 verdict: ADVANCED, not closed** (as [Block 105] §105.8's own text anticipated — full 3623-candidate
coverage was never a one-session ask). Cumulative sampled population across both sessions: 40+120=160/3623
≈ 4.4%. The specific residual instruction the gap named ("starting with the hit-count pre-filter heuristic")
is now substantially executed and quantified, not merely started. Full closure remains open as [Block 105]
itself scoped it.

## 111.3 — B105-G3 CLOSED for the plat* half, NARROWED-WITH-CORRECTION for `exportTags`: all 6 remaining `plat*` driver-platform modules reproduce §105.4's exact +19 dependency-count delta identically; `exportTags` does NOT reproduce §105.5's collapse pattern at all — a genuine boundary condition in the mechanism, not a re-confirmation `[CERT]`

**Verbatim parent text** ([Block 105] §105.11, `niagara5-block105.md:467-472`): "**B105-G3** — Extend
§105.4-105.5's `module.xml` dependency-delta mechanism (rt/ux/wb-split collapse + agent-binding-interface
redesign) to the FULL `plat*`/`html`/`file`/`fox`/`export` cluster membership beyond the specific modules
diffed this session (`platBacnet`, `file`, `fox`, `export`, `html`) — the mechanism is established and
cross-vendor-corroborated, but e.g. `platLon`/`platMstp`/`platNrio`/`platCcn`/`platEdgeIo`/
`platSerialNpsdk`/`exportTags` were not individually re-diffed. `investigable`, low priority (confirmatory,
not expected to change the conclusion)."

**ALREADY-COVERED check**: no later block re-diffs these 7 modules — proceeding.

**All 7 named modules confirmed present** in both N4 OEM installs (Honeywell + PowerB) and the N5 config
mirror this session (`ls`, `[CERT]`) — the "not investigable" risk the gap didn't even raise turned out to
be moot.

**The 6 `plat*` modules — CLOSED, exact reproduction of §105.4's mechanism**, `module.xml` extracted and
dependency-counted this session (`unzip -p ... META-INF/module.xml`, `scratchpad/b111/modxml/`):

| Module | N4 Honeywell `-rt` deps | N5 deps | Delta |
|---|---:|---:|---:|
| `platLon` | 7 | 26 | **+19** |
| `platMstp` | 9 | 28 | **+19** |
| `platNrio` | 7 | 26 | **+19** |
| `platCcn` | 9 | 28 | **+19** |
| `platEdgeIo` | 7 | 26 | **+19** |
| `platSerialNpsdk` | 9 | 28 | **+19** |

`[CERT]` (all 12 `module.xml` files extracted and dependency-tag-counted this session, preserved at
`scratchpad/b111/modxml/n4-<module>-rt.xml` / `n5-<module>.xml`). All 6 land at the EXACT SAME **+19** delta
[Block 105] §105.4 found for `platBacnet` (also +19, the top of the originally-reported +17..+19 range) —
not merely "within range" but bit-for-bit identical, the strongest possible confirmation that this is one
mechanical, uniform packaging-model change (N4's per-profile module split collapsing into one consolidated
N5 `module.xml`) applying identically across the whole `plat*` driver-platform family, not a per-module
coincidence.

**`exportTags` — does NOT reproduce §105.5's collapse pattern; a boundary condition, not a confirmation.**
Naive dependency-tag counts: N4 `exportTags-rt`=20, `exportTags-wb`=57, N5 `exportTags`=44 — superficially
resembling a drop, but this count is misleading because `exportTags-wb`'s own dependency list includes a
SELF-reference to `exportTags-rt` (an internal cross-part reference from the split itself, not an external
module dependency). Computing the true external union — N4's `rt`+`wb` base names, suffix-stripped and
DEDUPLICATED, excluding the self-reference — gives **43** `[CERT]` (`scratchpad/b111/modxml/n4-exportTags-
{rt,wb}.xml`, `comm -23`/`comm -13` set diff against N5's 44 `[CERT]`): N5's 44 vs N4's 43 is **a wash (+1),
not a collapse**. Set diff: N4 lost `queryTable`/`uxBuilder`, N5 gained `jsonSmart`/`oauth2`/`svgBatik` — a
lateral reshuffle, nothing like `html`'s −31 or `file`'s −18.

**Root cause of the divergence, read directly.** §105.5's mechanism (generic `baja:ITable`-interface agent
binding replacing many concrete per-module type references) applies specifically to modules whose N4
`ux`/`wb` PART was THIN (few own types, e.g. `file-ux`'s 3 export-agent types) but carried a long
dependency list purely because of what those agents could touch. `exportTags-wb`'s own N4 dependency list
(57, or 43 externally after dedup) is NOT that shape: reading its own `<type>` census confirms 15 real
`<type>` declarations (FieldEditors, Managers, `PxViewTag`/`PxViewTagValidationJob` — substantive UI
integration functionality, not merely export-agent registration) — `exportTags-wb` was already a
genuinely large UI-consumer module in N4, so N5's consolidation has nothing thin-and-artificial to collapse
away. **This is a real, useful boundary condition for §105.4-105.5's own mechanism**: the collapse pattern
applies to the SPECIFIC `html`/`file`/`fox`/`export` shape (a thin generic-export-agent registration
module), not to every `export`-NAMED module in the corpus.

**B105-G3 verdict: CLOSED for the plat* half** (6/6 exact reproduction, no residual). **NARROWED-WITH-
CORRECTION for `exportTags`**: [Block 105] §105.11's own framing ("the mechanism is established... not
expected to change the conclusion") is corrected — for `exportTags` specifically, the mechanism's expected
direction (large drop) does NOT hold, and the reason is now understood (its N4 `wb` part carries genuine,
non-agent-shaped UI functionality). This is a correction to [Block 105] §105.11's own anticipatory framing,
recorded in §111.5 below, not to §105.4/§105.5's actual findings (which remain correct for the modules they
actually diffed).

## 111.4 — B106-G3 CLOSED: an exhaustive extraction of EVERY comment (720 comments, all 56 files, no keyword filter) confirms all template prose lives in Java `//`/`/* */` comments (zero Velocity `##`/`#* *#` comments exist in this corpus), and finds exactly ONE further hidden non-interface behavioral contract beyond [Block 106]'s own two — the `coalesce()`/`getCoalesceKey()` default-merge-behavior javadoc, repeated identically in 3 files `[CERT]`

**Verbatim parent text** ([Block 106] §106.x "Child gaps opened," `niagara5-block106.md:502-505`):
"**B106-G3** (refines B97-G3, low-priority) — an exhaustive, non-keyword-filtered line-by-line prose read
of all 5,161 template lines, beyond this session's TODO/NOTE/IMPORTANT/WARNING/MUST/REQUIRED keyword
sweep, to rule out a THIRD hidden non-interface requirement phrased without any of those marker words.
`investigable`, low-priority per [Block 97]'s own original framing of this gap."

**ALREADY-COVERED check**: no later block re-reads these templates — proceeding.

**Method — operationalizing "exhaustive prose read" precisely.** In a Velocity/Java template, ALL prose
lives in comments; the surrounding code lines are Java/Velocity syntax (already covered structurally by
[Block 97]'s class-declaration census), not prose. This session (1) confirmed NO Velocity-native comment
syntax (`##` line-comments, `#* ... *#` block comments) exists ANYWHERE in the 56 files (`grep -c`, both
zero, `[CERT]`) — meaning Java-style `//`/`/* */` comments are the ONLY prose-bearing constructs in this
corpus, so extracting every one of them IS a complete, literal, non-keyword-filtered prose census, not an
approximation; (2) wrote `extract_comments.py` (`scratchpad/b111/extract_comments.py`) to extract every
`//` and `/* ... */` span (including `/** ... */` javadoc) from all 56 files with file:line, independent
of any keyword; (3) read the FULL output.

**Result: 720 comments extracted from the 56 files (`scratchpad/b111/all_comments.txt`), all 720 read this
session** `[CERT]`. Filtering out the 128 that already contain [Block 106]'s own keyword set
(TODO/NOTE/IMPORTANT/WARNING/MUST/REQUIRED/`@Deprecated`, case-insensitive) leaves 592 keyword-free
comments (`scratchpad/b111/new_comments.txt`, 2,592 lines) — every one of these was also read this session
`[CERT]`. The 592 resolve into exactly four categories, none new except the last: (a) copyright/`@author`/
`@date` boilerplate headers; (b) section-divider comments (`//// Access ////`, `// Model`, etc.) — pure
structural markers, already covered by [Block 97]'s class-declaration census; (c) ordinary javadoc
describing WHAT a method does (a description, not a silent requirement) or commented-out EXAMPLE/sample
code explicitly framed as optional (`// Example:`, `/* Uncomment the lines below for an example... */`);
(d) — **one genuinely new finding**.

**The new finding**: `coalesce(Object newElement)` (overriding `IQueueElement`'s coalescing contract)
carries a substantial javadoc-only behavioral contract, repeated **identically in 3 separate files**
— `gradle/ndriver/NfooMessage.java.vm:100`, `gradle/ndriver/NfooSerialLinkMessage.java.vm:77`, and
`gradle/ndriver/NfooTcpLinkMessage.java.vm:76` `[CERT]`:

```
/**
 * Attempts to coalesce this object with the newly enqueued {@code newElement}.
 * ...
 * The default implementation always returns {@code newElement}, meaning
 * that newer requests override older ones without merging. To support
 * smarter merging (e.g., aggregating changes or selecting based on priority),
 * override this method accordingly.
 * ...
 */
```

This is the SAME shape [Block 106] §106.7 already flagged twice (`BNfooEventProxyExt.getEventTypeEnum`,
`BNfooProxyExt.readSubscribed`/`readUnsubscribed`): a fully-compiling, non-abstract override whose default
behavior is a documented placeholder, flagged ONLY by javadoc prose with no marker interface, no `TODO`,
and no compile-time enforcement — a developer who never reads the javadoc gets a compiling driver that
silently drops all coalescing/merge logic (last-write-wins) for every queued message, in 3 of the corpus's
driver-scaffold classes.

**B106-G3 verdict: CLOSED.** This session performed a literal, complete (not sampled, not keyword-narrowed)
read of every prose-bearing span in the 56-file/5,161-line population — confirmed exhaustive by the
independent check that no other comment syntax exists in these files. [Block 97]'s own low-priority framing
of this gap ("no THIRD hidden requirement of comparable weight turned up" — [Block 106] §106.7's own
words) is now UPGRADED from "not found by a keyword sweep" to "not found by a complete read, except exactly
one" — the `coalesce()` javadoc contract, now named and cited. No further hidden requirement exists in this
template set; the gap's own question is answered definitively, not merely advanced.

## 111.5 — Corrections to earlier blocks

- **[Block 105] §105.11** (`niagara5-block105.md:467-472`) frames B105-G3 as purely confirmatory
  ("the mechanism is established... not expected to change the conclusion"). §111.3 above corrects this:
  the mechanism holds exactly (bit-for-bit +19) for all 6 `plat*` stragglers, but `exportTags` — one of the
  gap's own named targets — does NOT reproduce the collapse pattern at all (a +1 wash, not a large drop),
  because its N4 `wb` part was already a substantive UI-consumer module rather than a thin
  generic-export-agent-registration module like `html`/`file`/`fox`/`export` themselves. The mechanism's
  scope is now understood to be narrower than the gap's own framing implied.

## 111.6 — Connections

- **[Block 90] §90.1** (`classify_callsites.py`) — the direct methodological template for §111.1's
  `feature_census.py`; both stay in scratch by the same reasoning (single-purpose census scripts, not
  registry tools).
- **[Block 11] §11.1-§11.10**, **[Block 105] §105.7** — §111.1 extends but does not fully close the
  B11-G4 chain; the exact-253 population-scope question [Block 105] §105.7 itself left open is untouched.
- **[Block 96] §96.5-96.6** — §111.2's classification directly reuses and reproduces [Block 96]'s own
  three named canonical examples (`BTagDictionaryService`, `BBacnetEngineeringUnits`, `BBacnetProxyExt`),
  confirming this session's judgment calibrates against known ground truth rather than drifting.
- **[Block 60] §60.6**, **[Block 105] §105.4-105.5** — §111.3 extends the dependency-count-cluster
  interpretation those blocks built, and narrows its claimed scope for `exportTags` specifically.
- **[Block 97] §97.2**, **[Block 106] §106.7** — §111.4 closes the residual [Block 106] left explicitly
  open, reusing [Block 106]'s own already-extracted template corpus rather than re-extracting it.

## 111.7 — Child gaps opened this block

- **B111-G1** (low priority; scope CORRECTED by [Block 114] §114.4: 7 files / 11 call sites, not 2 / 5) — Extend §111.1's `feature_census.py` (or a variant) to ALSO census
  `com.tridium.niagarad.license.Feature` (`niagarad`'s own separate, structurally-identical-shaped but
  textually-distinct license `Feature` class, confirmed at `organized/_bin-ext/niagarad/vineflower/
  com/tridium/niagarad/license/Feature.java`) across its own module scope — 2 files / 5 call sites were
  identified but not resolved this session because they fell outside this script's deliberately narrow
  `niagara.license.Feature`-only scope. `investigable` (read-only, mechanical — the same script shape with
  a second target-type pass).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `feature_census.py` finds 92 distinct declared-type-resolved call sites (100 files scoped, 53 with ≥1 decl) | `[CERT]` | `scratchpad/b111/feature_census_output.txt`, this session |
| 2 | 76 of those 92 are NEW vs [Block 105]'s 211-line literal census; 16 overlap | `[CERT]` | same output, diff against `scratchpad/b105/b11g4-full.txt` |
| 3 | Old 211-line census splits cleanly into 189 entry-point + 22 follow-on, zero overlap | `[CERT]` | `grep` re-run this session on `b11g4-full.txt` |
| 4 | `organized/workbench/vineflower/com/tridium/workbench/shell/WbMain.java:665`, `organized/bacnet/vineflower/com/tridium/bacnet/stack/link/mstp/BBacnetMstpLinkLayer.java:204`, `organized/platDataRecovery/vineflower/com/tridium/platDataRecovery/BDataRecoveryService.java:520` each declare a bare `Feature`-typed local with no "Feature" substring in the name | `[CERT]` | direct reads this session, full paths above |
| 5 | `com.tridium.niagarad.license.Feature` is a separate class from `niagara.license.Feature` | `[CERT]` | `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/license/Feature.java:1-5` |
| 6 | Bucket-A (≥20 hits, n=60) tally: 37 coincidental/14 conventional/9 accidental | `[CERT]`(24)+`[INFER]`(36) | `scratchpad/b111/sample_context_b111.txt`, classification this session |
| 7 | Bucket-B (<20 hits, n=60) tally: ~47 accidental/6 coincidental/6 conventional/1 uncertain | `[INFER]` (value/name judgment only, no shadow-hit-content read) | same sample file, header-only pass |
| 8 | `STATUS_FLAGS_STATUS_FACET`/`READ_STATUS_FLAGS` reproduces [Block 96]'s own canonical example | `[CERT]` | `organized/bacnet/vineflower/niagara/bacnet/point/BBacnetProxyExt.java:140,144` |
| 9 | `_SCRAM_GLIBC_SHA512_NATIVE`/`_SCRAM_GLIBC_SHA256_NATIVE` are a genuine same-file accidental-duplication pair | `[CERT]` | `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/util/DaemonAuthUtil.java:24,25` (cited from dump), spot-checked this session |
| 10 | All 6 `plat*` stragglers show N4-rt-vs-N5 delta = exactly +19 | `[CERT]` | `module.xml` extracts, `scratchpad/b111/modxml/`, this session |
| 11 | `exportTags` N4-union-vs-N5 delta = +1 (44 vs 43 after self-ref dedup), not a collapse | `[CERT]` | same dir, `comm` set diff this session |
| 12 | `exportTags-wb`'s N4 `<type>` census shows 15 substantive UI types, not a thin export-agent-only module | `[CERT]` | `grep -c '<type '` on `n4-exportTags-wb.xml`, this session |
| 13 | No Velocity `##`/`#* *#` comment syntax exists anywhere in the 56 `.vm` templates | `[CERT]` | `grep -rn`, this session, both zero |
| 14 | 720 comments extracted from 56 files; 592 keyword-free; all read this session | `[CERT]` | `scratchpad/b111/all_comments.txt`, `new_comments.txt` |
| 15 | `coalesce()`'s default-merge-behavior javadoc is identical across 3 files | `[CERT]` | `gradle/ndriver/{NfooMessage,NfooSerialLinkMessage,NfooTcpLinkMessage}.java.vm`, lines cited in §111.4 |

Marker tally (this file, mechanical count): `[CERT]` = 13, `[INFER]` = 2 (both explicitly tiered/qualified
compound uses, §111.2's bucket tallies). Ratio INFER/CERT-family ≈ 2/13 ≈ 0.15 — low, consistent with a
census-extension block where nearly every claim resolves to a direct script run, file extract, or read this
session, with `[INFER]` reserved for the Tier-2 (value-only, no shadow-hit-content) classification passes
explicitly disclosed as lower-confidence in §111.2.

**Artifacts** (scratch, not archived in either repo): `scratchpad/b111/feature_census.py` +
`feature_census_output.txt` + `feature_files.txt`; `scratchpad/b111/sample_b111.py` +
`sample_context_b111.txt`; `scratchpad/b111/modxml/{n4,n5}-{platLon,platMstp,platNrio,platCcn,platEdgeIo,
platSerialNpsdk}*.xml` + `n4-exportTags-{rt,wb}.xml` + `n5-exportTags.xml`; `scratchpad/b111/
extract_comments.py` + `all_comments.txt` + `new_comments.txt`.

verify-block.sh: run against this file, see orchestrator-facing return summary.
