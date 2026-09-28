# Block 109 — No first-class N5 UI command reaches `BComplex.setFacets()`'s frozen-slot branch (three independent gates, corpus-wide `setFacets(` census); N5's 3-doc-jar dual-indexing census refined; `docDeveloperAnalytics.jar`'s own `bajadoc.index` IS read at runtime, by the Help side-bar's API tree, not `BajadocIndex`; and the PowerB N4-4.15.3.28 package DOES ship `saml`, already on the same `java-saml-core-2.9.0` library as N5

> Research closing four assigned child gaps from two prior blocks. **B103-G1** ([Block 103] §103.3/§103.x
> — is there any GUI path reaching `BComplex.setFacets()`'s frozen-slot branch, beyond the two already
> searched?); **B103-G2** ([Block 103] §103.x — do other doc jars share `docDeveloperAnalytics.jar`'s
> dual-indexing pattern?); **B103-G3** ([Block 103] §103.x — is `docDeveloperAnalytics.jar`'s own index
> actually read at runtime by `BajadocIndex`/the help system?); **B98-G4** ([Block 98] §98.1's own
> boundary note — does the PowerB N4-4.15.3.28 OEM package ship `saml` under another jar name, and does
> N5 ship `saml`?). Does **not** cover: a live commissioning-time reproduction of any UI command found
> (all reads are static, decompiled-source/jar-content only, per METHODOLOGY's live-station exclusion);
> an exhaustive line-by-line read of `BMetadataBrowser.java` (652 lines) or `BSAMLAuthenticationScheme`-
> family classes beyond the specific methods cited; a byte-level diff of every `com.onelogin.saml2.*`
> class between N4-4.15.3.28 and N5 5.0.0.28 beyond the one spot-checked (`Util.class`).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`
> (`vineflower/` primary), N5 module jars at `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`
> (247 jars, read-only). N4 baseline for **B98-G4**: the same PowerB N4-4.15.3.28 OEM package [Block 98]
> already used, read-only at `/mnt/c/PowerB/PowerB-4.15.3.28`. Method: `grep -rn "\.setFacets("` across
> the ENTIRE `organized/` tree (both `*.java` and `*.js`, ~120 hits total, this session), narrowed to
> GUI-layer modules (`workbench`, `wbutil`, `webEditors`, `bajaui`) and each remaining hit read in full
> context to classify as programmatic-only, dynamic-property-only, or a genuine frozen-slot-capable UI
> command, for B103-G1; a fresh `ls`/`unzip -l` sweep of `doc*.jar` in the live N5 config-home modules
> dir (3 jars found, matching [Block 4] §4.9's own count) plus per-jar `unzip -l | grep` for
> `bajadoc.index`/`{words,postings,documents,worddocs}.dat`, for B103-G2; a full re-read of
> `com.tridium.help.BajadocIndex`/`HelpSystem`/`SearchLoader`/`BHelpSideBar` (4 whole files, `help`
> module, none previously opened together in one session) to trace every reader of a file literally
> named `bajadoc.index` vs. the `bajadoc.dat` `BajadocIndex` itself consumes, for B103-G3; a fresh
> `ls "$BASE/modules" | grep -i saml"` re-run against the exact same PowerB path, plus `unzip -l`/
> `unzip -p`+`sha256sum` on the found jars and a byte-for-byte `cmp` against N5's own nested
> `LIB-INF/java-saml-core-2.9.0.jar`, for B98-G4. All commands run this session, 2026-09-27. Scratch
> (never committed): `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/
> scratchpad/b109/` (`n5-java-saml-core-2.9.0.jar`, `n4-Util.class`, `n5-Util.class` — extracted this
> session for the `cmp`). Markers (canonical list, METHODOLOGY §3): `[CERT]` local primary source
> (`file:line` or literal command/tool-output) · `[CERT-hw]` a live command run this session against a
> real installed jar/tree (sha256-anchored) · `[CERT-doc]`/`[CERT-web]`/`[CERT-a]`/`[CERT-live]` not used
> in this block · `[INFER]` deduction.

---

## 109.0 — ALREADY-COVERED check (all four gaps)

`rg -il` over `niagara5-block*.md` with at least two distinct terms per gap, run before investigating
each: `setFacets`/`FacetEditor` → hits only `niagara5-block37.md` (an unrelated BOX-protocol op-code
listing, `:160`, not a UI trace) and `niagara5-block72.md`/`niagara5-block103.md` (the gap's own prior
sessions, not a later closure); `docDeveloperAnalytics`/`BajadocIndex` → hits only [Block 59]/[Block 75]/
[Block 103] (the gap's own lineage, already read into this block's header); `saml-rt`/`saml-wb`/
`samlEncryption` → hits [Block 12]/[Block 13]/[Block 38]/[Block 62]/[Block 98] (N5-side and the gap's
own N4-side origin, not a later closure of B98-G4 itself). **No block postdating [Block 103]/[Block 98]
already closes any of these four gaps — none reported ALREADY-COVERED; all four investigated fresh.**
`[CERT]` (`rg -il` output, this session).

## 109.1 — B103-G1 CLOSED: a corpus-wide census of every `.setFacets(` caller finds THREE independent, genuinely-first-class Workbench/web UI mechanisms that can reach a component's facets — and all three explicitly, structurally exclude frozen slots; no fourth mechanism exists `[CERT]`

**Gap text (verbatim, from `niagara5-block103.md` §103.x):** "**B103-G1** ... Find whether ANY
first-class N5 UI command (Workbench or web) can invoke `BComplex.setFacets()`'s frozen-slot branch
... for a slot that is BOTH frozen AND not a dynamic property ... a third, unsearched candidate is the
'Slot Facets' dialog reachable from a component's own right-click 'Properties'/'Edit Tags' style dialog
outside the Slot Sheet proper, not yet checked."

**A full-corpus `grep -rn "\.setFacets("` across `organized/` (both `.java` and `.js`) returns roughly
120 call sites.** The great majority are programmatic, module-internal calls a driver/control-logic
class makes on its OWN children at runtime (e.g. `BBacnetLoop`/`BBacnetAnalog` setting facets on a
freshly-decoded BACnet object property, `BHonSbpHistoryChannelConfig` setting a transport's own
size-limit facet) — not reachable from any UI action at all, and not further pursued (out of scope: the
gap is about UI reachability, not the model API's general legitimacy, already established by [Block
103] §103.3). Narrowing to the four GUI-layer modules (`workbench`, `wbutil`, `webEditors`, `bajaui`)
finds exactly the following distinct UI-triggered call sites, EACH read in full and classified:

| Caller | UI surface | Target slot | Frozen-slot reachable? |
|---|---|---|---|
| `ConfigFacetsCommand.java`/`.js` (Slot Sheet "Facets" command, both sides) | Workbench Slot Sheet + web Slot Sheet `.col-facets` column | any selected slot | **NO** — gated by `allDynamics`/`isFrozen()` (already established, [Block 103] §103.3) |
| `BEditTagDialog.java:376,447` (`this.directTags.setFacets(tgProp, ...)`) | Workbench "Edit Tags" dialog (the actual right-click dialog the gap named as its unsearched 3rd candidate) | `tgProp` on `this.directTags`, an internal SCRATCH container | **NO** — `tgProp` is a property `this.directTags.add(...)` JUST created on the same line, i.e. always dynamic; the real target component's own frozen slots are never touched by this call `[CERT]` (`organized/workbench/vineflower/com/tridium/workbench/util/BEditTagDialog.java:373-376,444-447`, both call sites read in full method context) |
| `MgrColumn.java:745` (`parent.setFacets(tagProp, originalFacets)`) | Workbench Manager (Mgr) table's Tag column, inline-edit `save()` | a tag property on the row's real target component | **NO** — `tagProp` is guarded upstream by `isCellValid()`'s own `Flags.isReadonly`/`isHidden` check, and the call only RESTORES facets captured before a `tags().remove()`/`tags().set()` round-trip on what is, by construction, a dynamic tag-backed property — never a static `@NiagaraProperty` `[CERT]` (`organized/workbench/vineflower/niagara/workbench/mgr/MgrColumn.java:703-745`, whole `isCellValid`+`save` methods) |
| `BMetadataJob.java:328` (`container.setFacets(prop, facets, cx)`) — the "Metadata Browser" tool's Set operation | `BMetadataBrowser` (`@AgentOn(types="baja:Station")`, a genuine registered Workbench VIEW on any Station, reachable via the ordinary Views menu) → right-click "Slot Edit" command → `BSetDialog` | **any** existing property on **any** selected `BIPropertyContainer` node in the station's nav tree, including a frozen one | **NO — explicitly, by name**: `if (facets != null && !prop.isFrozen()) { container.setFacets(prop, facets, cx); }` `[CERT]` (`organized/wbutil/vineflower/com/tridium/workbench/metadata/BMetadataJob.java:312-330`, whole `addMeta()` set-branch) |
| `WebProperty.setFacets(BWidget, name, metadata)` | embedded web-hosted Px/ux widget → `WebWidgetInterop.browserCalledMetadataChanged()` (browser-side JS widget reports its own metadata change back to its host `BWidget`) | any property flagged `Flags.USER_DEFINED_3` ("web property") on that widget | **theoretically yes, in practice NO** — `isWebProperty()` only requires the flag bit, which COULD in principle sit on a static (frozen) `@NiagaraProperty`, but a corpus-wide `grep -rln "USER_DEFINED_3"` finds exactly 3 non-doc hits (`Flags.java`'s own constant, `Fw.java`'s flag-decode table, and `ComponentWriter.java:411` — a Program-editor CODE-GENERATOR emitting the flags-constant NAME as a text string, not a property declaration) — **zero** `BWidget` subclasses in this corpus statically declare a frozen property with that flag; every corpus use of the "web property" mechanism instead `widget.add(...)`s a NEW dynamic property when none exists yet (`organized/docSource/bajaui/niagara/ui/util/WebProperty.java:180`) `[CERT]` |
| `PxDecoder.decodeProps()` (`organized/bajaui/fallback/niagara/ui/px/PxDecoder.java:322-331`) | Px view LOAD (opening a `.px` file) | any property named in the file's own `<p name=... ft="...">` XML, frozen or dynamic, no `isFrozen()` check at all | **N/A — not an origination path**: this is the persistence-layer REPLAY of whatever a `.px` file's XML already encodes; it can only reproduce a frozen-slot facets override that was already written into that file by SOME earlier act (the model API itself, per [Block 103] §103.3's own `BComplex.setFacets()` citation, or direct external hand-editing of the XML text outside any Niagara UI command) — it is not itself a UI command an operator invokes to CREATE a new override `[CERT]` |

**Net verdict: B103-G1 is CLOSED.** All three genuinely first-class, interactive Niagara UI commands
this session found that can call `setFacets()` on an arbitrary user-selected slot — the web/Workbench
Slot Sheet "Facets" command ([Block 103] §103.3, reconfirmed), and the newly-traced Workbench
**Metadata Browser's "Slot Edit" dialog** (this section, the gap's own named 3rd candidate) — either
structurally restrict themselves to dynamic slots or explicitly test `!prop.isFrozen()` before calling
through. `BEditTagDialog`/`MgrColumn` only ever touch dynamic tag-backed properties despite calling the
same API. The one path with no `isFrozen()` gate at all (`PxDecoder`) is a file-deserialization replay,
not an operator-facing command that originates an override. **The raw-string `fieldEditor`-facet
override for a frozen, non-dynamic slot (`capacity`, [Block 26]/[Block 72]'s scenario) is reachable
ONLY through the model API directly — a station script, BQL, a `.px`/`.bog` file hand-edit, or a
third-party tool calling `component.setFacets(prop, facets)` — never through any first-class N5
Workbench or web UI command.**

## 109.2 — B103-G2 ADVANCED: exactly 3 of 247 N5 module jars carry any `doc/` content at all (matching [Block 4] §4.9 exactly) — but the dual-indexing PATTERN itself splits: 2 of the 3 carry BOTH `bajadoc.index` and the 4-file search index, while `docSource.jar` carries only the search index half `[CERT]`

**Gap text (verbatim):** "**B103-G2** — Confirm whether `docDeveloperAnalytics.jar`'s dual-indexing
pattern (§103.1) is unique to `analytics`, or whether OTHER N5 doc-content-bearing jars ... exist with
the same self-contained-index-plus-shared-index pattern."

A fresh `ls /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/ | grep -iE "^doc.*\.jar$"` this
session returns exactly **3 jars**: `docDeveloper.jar`, `docDeveloperAnalytics.jar`, `docSource.jar`
`[CERT]` — matching [Block 4] §4.9's own exhaustive 247-jar census bit-for-bit (that table's other 5
`doc/`-entry-bearing jars — `ffmpeg.jar`, `bajaui.jar`, `web.jar`, `workbench.jar`, `xprotect.jar` — carry
only incidental license text/theme fixtures/About-screens, zero bajadoc). This re-citation confirms
[Block 103] §103.x's own "moot" framing was correct on the CENSUS question. **But the finer-grained
question — does each of the 3 carry the SAME index shape — was not previously checked, and the answer
is NOT uniform:**

| Jar | `doc/bajadoc.index` | `doc/{words,postings,documents,worddocs}.dat` |
|---|---|---|
| `docDeveloper.jar` | YES (984 bytes) | YES (all 4 present) |
| `docDeveloperAnalytics.jar` | YES (9 bytes, literal string `"analytics"`, [Block 103] §103.1) | YES (all 4 present) |
| `docSource.jar` | **NO** | YES (all 4 present) |

`[CERT]` (fresh `unzip -l /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{docDeveloper,
docDeveloperAnalytics,docSource}.jar \| grep -iE "bajadoc.index\|words.dat\|postings.dat\|documents.dat\|
worddocs.dat"`, this session). **B103-G2 ADVANCED, not merely re-cited:** `docDeveloperAnalytics.jar`'s
"dual-indexing" (a self-contained 4-file search index PLUS its own `bajadoc.index`) is shared with
`docDeveloper.jar` (both halves) but only HALF-shared with `docSource.jar` (search index only, no
`bajadoc.index`) — the census the gap asked for is exhaustive (only 3 jars exist to check, confirmed
fresh) and the pattern is genuinely non-uniform across them, not a `docDeveloperAnalytics`-only quirk
as the gap's phrasing might have suggested, nor identically shared by all 3 either.

## 109.3 — B103-G3 CLOSED: `docDeveloperAnalytics.jar`'s own `doc/bajadoc.index` IS read at runtime — by `BHelpSideBar.buildApi()`, which seeds the Help panel's "API" tree with one root node per doc-module — NOT by `BajadocIndex.lookup()`, which reads a completely different, separately-built `bajadoc.dat` file `[CERT]`

**Gap text (verbatim):** "**B103-G3** — Trace WHERE/HOW `docDeveloperAnalytics.jar`'s own separate index
... actually gets USED at runtime — is it consulted by `BajadocIndex.lookup()` ... as a second,
per-module index source, or is `docDeveloper.jar`'s combined index the only one actually queried ...
making `docDeveloperAnalytics.jar`'s own copy a build-artifact leftover never read at runtime?"

**A whole-file read of `com.tridium.help.BajadocIndex`** (`organized/help/vineflower/com/tridium/help/
BajadocIndex.java`, 261 lines) shows `loadAllEntries()` reads exactly ONE file: `new File(HelpSystem.HELP,
"bajadoc.dat")` — a single flat file in the config-home's `help/` DIRECTORY (`Sys.getNiagaraConfigHome()
+ "/help"`, `organized/help/vineflower/com/tridium/help/HelpSystem.java:27`), not any jar's own `doc/
bajadoc.index`. **This file does not even exist yet in this beta install** (`ls /mnt/c/ProgramData/
Niagara/tridium/config/5.0.0.28/help/` → "No such file or directory", this session — confirming the
combined help index is built lazily, e.g. on first Help-panel open or an explicit "Build Help" action,
never bundled pre-built at the module-jar level for this consolidated index) `[CERT]`
(`organized/help/vineflower/com/tridium/help/BajadocIndex.java:100-153`, whole `ensureTagsLoaded`+
`loadAllEntries` methods).

**A whole-file read of the class that WRITES `bajadoc.dat`, `com.tridium.help.SearchLoader`** (271
lines, not previously opened in this corpus), traces exactly how it's built: `findModules()` calls
`HelpSystem.getModulesForHelp()`, which enumerates every registered module whose name starts with `doc`
(the same 3-jar universe as §109.2) `[CERT]` (`organized/help/vineflower/com/tridium/help/HelpSystem.java:
64-68`). For each such module, `decompress(NModule)` parses EVERY `.bajadoc` XML entry inside that
module's jar via `BajadocParser`, and `saveBajadocEntry()` accumulates one `BajadocIndex.Entry` per
class/package/module doc page into an in-memory map, keyed by simple name — **this is a
qualified-class-name lookup table built from ALL 3 doc jars' raw `.bajadoc` content combined**, entirely
independent of any `bajadoc.index` file `[CERT]` (`organized/help/vineflower/com/tridium/help/
SearchLoader.java:109-165,214-235`, whole `findModules`/`saveBajadocEntry`/`loadEntries` methods).
`persistBajadocEntries()` then writes that combined map out to the single `<HELP>/bajadoc.dat` file
`BajadocIndex` reads `[CERT]` (`SearchLoader.java:154-176`, whole method).

**The actual reader of `doc/bajadoc.index` is a third, distinct class: `com.tridium.help.ui.BHelpSideBar`**
— a genuinely new finding, no framing in [Block 75]/[Block 103] anticipated this consumer.
`buildApi()` calls `HelpSystem.getModulesHavingFile("doc/bajadoc.index")` (a live `zip.getEntry(...) !=
null` filter over every doc-eligible module, returning exactly `docDeveloper`/`docDeveloperAnalytics`
per §109.2's table) and, for EACH such module, opens that module's own `doc/bajadoc.index` file and
reads it **line by line**, creating one `DocModuleNode` tree-root PER LINE, labeled with that line's
text — these become the top-level entries of the Workbench Help panel's "API" tab tree `[CERT]`
(`organized/help/vineflower/com/tridium/help/ui/BHelpSideBar.java:232-254`, whole `buildApi()` method).
Concretely, `docDeveloperAnalytics.jar`'s single-line `doc/bajadoc.index` content (the literal 9-byte
string `"analytics"`, [Block 103] §103.1's own hex dump) becomes exactly one root node, labeled
`"analytics"`, in that live API tree, alongside `docDeveloper.jar`'s own (984-byte, presumably
multi-line) root-node list.

**B103-G3 CLOSED, with a corrected mechanism: `docDeveloperAnalytics.jar`'s own `bajadoc.index` is NOT
a build-artifact leftover — it is live, currently-read data — but it feeds the Help panel's API-tree
NAVIGATION structure (`BHelpSideBar`), not `BajadocIndex`'s class-name SEARCH lookup (which instead
consumes a separately-built, differently-named `bajadoc.dat` combining all 3 jars' `.bajadoc` content
regardless of any `bajadoc.index` file's presence).** The corpus effectively runs TWO independent,
parallel per-doc-module indexing mechanisms under the "help" umbrella, both real, neither redundant with
the other.

## 109.4 — B98-G4 CLOSED, with a correction to [Block 98]: the PowerB N4-4.15.3.28 package DOES ship `saml` — as `saml-rt.jar`/`saml-ux.jar`/`saml-wb.jar`/`samlEncryption-rt.jar`, not a monolithic `saml.jar` — and it already uses `com.onelogin.saml2.util.Util` from `java-saml-core-2.9.0`, the BYTE-IDENTICAL library N5 ships `[CERT-hw]`

**Gap text (verbatim, from `niagara5-block98.md` §98.1's boundary note):** "**B98-G4** — This OEM
('PowerB') N4-4.15.3.28 package ships no `saml.jar` at all, so this session could not confirm whether N4
4.15's own SAML SP implementation still uses `com.onelogin.saml.Utils` ... or has since migrated toward
N5's `java-saml-core-2.9.0`-based rewrite ... Would need a fuller N4 4.15.x install/package (or a
different OEM's package) that includes the `saml` module."

**A fresh re-run of [Block 98]'s own two boundary-note commands, against the identical `$BASE=/mnt/c/
PowerB/PowerB-4.15.3.28` path, contradicts [Block 98]'s own stated result.** `unzip -l "$BASE/modules/
saml.jar"` does correctly fail (no such literal filename) — but `ls "$BASE/modules" | grep -i saml`
returns **4 matches**, not the "no matches" [Block 98] §98.1 reported: `saml-rt.jar`, `saml-ux.jar`,
`saml-wb.jar`, `samlEncryption-rt.jar` `[CERT]` (this session's own `ls`/`unzip` output; file mtimes
`2026-01-21`, i.e. present in the package well before [Block 98]'s own session — this is a stale/
incomplete prior search, not a package that changed underneath). **This is a correction to [Block 98]
§98.1's boundary note and the block's own header "Does not cover" line** (§109.x below): N4 uses
the SAME per-layer module-part naming convention N5 abandoned (`-rt`/`-ux`/`-wb` suffixes on separate
jars, wired together by one `module.xml`'s `<modulePart>` declarations — confirmed `[CERT]`,
`unzip -p "$BASE/modules/saml-rt.jar" META-INF/module.xml`, this session), not a single `saml.jar`; a
plain substring `ls | grep -i saml` (not an exact-filename `unzip -l`) was the correct, and available,
search all along.

**Opening the found `saml-rt.jar` answers the gap's real question directly: N4 4.15.3.28 has ALREADY
migrated off `com.onelogin.saml.Utils`.** `unzip -l` shows the jar bundles `com/onelogin/saml2/**`
(42+ classes: `authn/AuthnRequest`, `authn/SamlResponse`, `settings/Saml2Settings`, `util/Util`, etc.)
plus its own Maven coordinates, `META-INF/maven/com.onelogin/java-saml-core/pom.properties` →
`artifactId=java-saml-core`, `version=2.9.0` `[CERT]` (`unzip -l`+`unzip -p ... pom.properties`, this
session) — **the exact same library and exact same version** [Block 12]/[Block 61]/[Block 38] already
documented for N5. A targeted `unzip -l | grep -E "com/onelogin/saml/[^2]"` (the OLD, singular-`saml`
package [Block 62] §62.4 documented for the `niagara-research` N4-4.14 baseline) returns **zero hits** —
the old class is fully gone, not coexisting alongside the new one `[CERT]`.

**A direct byte-level cross-check confirms this isn't merely the same version number but the identical
compiled artifact.** N5's own `saml.jar` bundles its copy of this dependency differently — as a nested
`LIB-INF/java-saml-core-2.9.0.jar` (N5's `LIB-INF/`-nested-third-party-jar packaging convention, vs. N4's
classes-unpacked-directly-into-the-module-jar convention) — but extracting `com/onelogin/saml2/util/
Util.class` from BOTH (`unzip -p .../saml-rt.jar com/onelogin/saml2/util/Util.class` for N4;
`unzip -p .../saml.jar LIB-INF/java-saml-core-2.9.0.jar | unzip -p - com/onelogin/saml2/util/Util.class`
for N5) and running `cmp`/`sha256sum` on both shows they are **byte-for-byte IDENTICAL**: sha256
`54f43814cd66b48fc9a407b8931d9f18290993822bb924edb8a440ce168f0374` for both `[CERT-hw]` (this session's
own `unzip -p`+`sha256sum`+`cmp` run; extracted files preserved at `/tmp/claude-1000/
-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b109/{n4,n5}-Util.class`).

**Full jar sha256 census** (this session, both jars fresh-hashed): `saml.jar` (N5)
`6758c4f86dca7a6ab26016e0ccec481cb44c30537bf5256fcf03814bfed3cbaf`; `saml-rt.jar` (N4-4.15.3.28)
`8a2479dcccf2cc5dbe0b58fc67f178c1bafd170c3084ce3d431bb383828beedf`; the extracted N5 nested dependency
`n5-java-saml-core-2.9.0.jar` (`unzip -p saml.jar LIB-INF/java-saml-core-2.9.0.jar`)
`41735e2063f1c511d342aab613b2144efb758e2364ecd9193b7639274a280f24`.

**N5 census confirmation (the gap's second half — "does N5 ship saml?"):** `ls .../modules/ | grep -i
saml` on the live N5 config-home → `saml.jar`, `samlEncryption.jar` (2 jars, N5's usual
consolidated-single-jar-per-module convention, vs. N4's 4 separate `-rt`/`-ux`/`-wb`/`Encryption-rt`
parts) `[CERT]`.

**Defensive security note (framing only, per this task's discipline — no exploit steps).** [Block 61]
§61.3 already established, for N5's copy of this SAME `Util.class`, that its SP-side signature-algorithm
allowlist is a hardcoded set that INCLUDES SHA-1 variants (`niagara5-block61.md` §61.3). Because this
session's byte-level `cmp` shows N4-4.15.3.28's `Util.class` is the identical compiled artifact, that
same allowlist shape is present in N4-4.15.3.28's SAML SP as shipped in this OEM package too — this is
disclosed as an affected-contract observation only (shared third-party dependency, same version, same
bytes), not as a fresh exploit path; whether it is actually reachable/exploitable on either platform
depends on caller-side configuration this session did not re-examine here (out of this gap's scope).
**B98-G4 CLOSED**: the package DOES ship `saml` (under the per-layer `-rt`/`-ux`/`-wb` naming), and N4
4.15.3.28 has fully migrated to the same `java-saml-core-2.9.0` library N5 uses — not merely "toward" it
as the gap's own phrasing hedged, but to the byte-identical compiled class.

## 109.x — Corrections to earlier blocks

- **[Block 98] §98.1 (header "Does not cover" line + the §98.1 "Boundary note")** — both state "this OEM
  package does not ship `saml.jar` at all" / "`ls \"$BASE/modules\" | grep -i saml` → no matches". §109.4
  shows this is incorrect: the identical command against the identical path returns 4 matches
  (`saml-rt.jar`/`saml-ux.jar`/`saml-wb.jar`/`samlEncryption-rt.jar`, file mtimes predating [Block 98]'s
  own session) — [Block 98]'s search checked only the exact literal filename `saml.jar` and did not
  actually turn up the substring-match result it reported. The correct statement is: the package ships
  `saml` under N4's standard per-layer module-part naming, and (§109.4) that shipped implementation has
  already migrated to `java-saml-core-2.9.0`, the same library and byte-identical `Util.class` [Block 61]
  §61.3 examined for N5. [Block 98] §98.1's own SHA-1/`secureValidation` analysis (which explicitly
  re-read the OLD `com.onelogin.saml.Utils` from the separate `niagara-research` N4-4.14 corpus, not this
  package's own SAML jar) was performed against a DIFFERENT, older SAML implementation than the one this
  same PowerB package actually ships — that analysis's SHA-1/secure-validation conclusion has not been
  re-verified against the correct (`com.onelogin.saml2.util.Util`) class and should not be assumed to
  carry over; this residual is opened below as **B109-G1**.

## 109.x — Connections

- **[Block 26]/[Block 72]/[Block 103]** — §109.1 closes B103-G1, the last open child gap in this chain
  (B26-G2 → B72-G1 → B103-G1); the model-layer capability [Block 26]/[Block 72] originally flagged as a
  hazard is now confirmed, exhaustively, to have zero first-class UI origination path in this corpus.
- **[Block 4]/[Block 59]/[Block 75]/[Block 103]** — §109.2 re-confirms [Block 4] §4.9's 3-jar doc census
  fresh and refines [Block 103] §103.1's "dual-indexing" framing into a precise per-jar table (only
  `docDeveloper.jar`+`docDeveloperAnalytics.jar` share BOTH halves of the pattern).
- **[Block 75]** — §109.3 reuses [Block 75] §75.2's own `BajadocIndex.java` citation as the negative
  half of the answer (confirms it does NOT read `bajadoc.index`) and adds two classes ([Block 75] never
  opened) — `SearchLoader`/`BHelpSideBar` — to fully close the loop [Block 103] §103.x left open.
- **[Block 12]/[Block 38]/[Block 61]/[Block 62]/[Block 98]** — §109.4 closes B98-G4 and directly extends
  [Block 61] §61.3's N5-side `java-saml-core-2.9.0` finding onto N4-4.15.3.28 via a fresh byte-identical
  `cmp`; corrects [Block 98] §98.1's boundary note (§109.x Corrections above); leaves [Block 62] §62.4's
  own N4-4.14-baseline analysis (a genuinely different, older library) untouched and still valid for
  that older baseline specifically.

## 109.x — Child gaps opened

- **B109-G1** (opened by §109.4's correction, medium priority — a real security-relevant re-analysis,
  defensive framing only) — Re-run [Block 98] §98.1's own SHA-1/`jdk.xml.dsig.secureValidationPolicy`
  gate analysis against N4-4.15.3.28's ACTUAL, currently-shipped SAML SP class,
  `com.onelogin.saml2.util.Util` inside `saml-rt.jar` (this session's own extracted copy already sits at
  `/tmp/.../scratchpad/b109/n4-Util.class`, undecompiled), instead of the old `com.onelogin.saml.Utils`
  [Block 98] §98.1 actually read — does N4-4.15.3.28's real SAML consumer enable
  `setProperty("org.jcp.xml.dsig.secureValidation", TRUE)` (or run under an active `SecurityManager`)
  anywhere in its own call chain, the same question [Block 61] §61.3 already answered for N5's identical
  class? `investigable` — a decompile of the already-extracted class plus a corpus-wide `grep` for its
  callers in `saml-rt.jar`/`saml-wb.jar`, no live station needed.
- **B109-G2** (opened by §109.1, low priority) — `WebProperty`'s "web property" mechanism (`Flags.
  USER_DEFINED_3`) is architecturally CAPABLE of exposing a frozen slot's facets to browser-side editing
  if any `BWidget` subclass ever statically declares a property with that flag; this session found zero
  such declarations in the current 247-module corpus, but did not exhaustively check every third-party
  module SPI surface (e.g. a custom driver's own Px widget) for one. `investigable`, low priority — a
  targeted `grep` for `USER_DEFINED_3` alongside `@NiagaraProperty` in any module not yet opened would
  close it outright.
- **B109-G3** (opened by §109.3, low priority, cosmetic) — `BHelpSideBar.buildApi()`'s per-line
  `DocModuleNode` construction from `docDeveloper.jar`'s own (984-byte, presumably multi-line)
  `doc/bajadoc.index` was not read line-by-line this session (only `docDeveloperAnalytics.jar`'s 9-byte
  single-line file was, by [Block 103] §103.1); confirming how many distinct API-tree root nodes
  `docDeveloper.jar` alone contributes (module names? top packages?) would fully characterize the tree's
  shape. `investigable`, low priority — a single `unzip -p docDeveloper.jar doc/bajadoc.index` read.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `ConfigFacetsCommand`'s web/Workbench Facets command excludes frozen slots | [CERT] | reused from [Block 103] §103.3's own citation, not re-derived |
| 2 | `BEditTagDialog`'s two `setFacets` calls target a property `this.directTags.add(...)` just created (always dynamic) | [CERT] | `organized/workbench/vineflower/com/tridium/workbench/util/BEditTagDialog.java:373-376,444-447` |
| 3 | `MgrColumn.save()`'s `setFacets` call only restores pre-captured facets on a tag-backed (dynamic) property, gated by `isCellValid()`'s readonly/hidden check | [CERT] | `organized/workbench/vineflower/niagara/workbench/mgr/MgrColumn.java:703-745` |
| 4 | `BMetadataJob.addMeta()`'s set-branch explicitly skips frozen slots: `if (facets != null && !prop.isFrozen())` | [CERT] | `organized/wbutil/vineflower/com/tridium/workbench/metadata/BMetadataJob.java:312-330` |
| 5 | `BMetadataBrowser` is a real registered Workbench view, `@AgentOn(types="baja:Station")`, whose "Slot Edit" command opens `BSetDialog` | [CERT] | `organized/wbutil/vineflower/com/tridium/workbench/metadata/BMetadataBrowser.java:55-56`; `organized/wbutil/vineflower/com/tridium/workbench/metadata/MetadataCommands.java:59-68` |
| 6 | `WebProperty.isWebProperty()`'s flag (`USER_DEFINED_3`) is never statically declared on any corpus `BWidget` property | [CERT] | `grep -rln "USER_DEFINED_3" organized --include="*.java"` = 3 non-declaration hits only, this session |
| 7 | `PxDecoder.decodeProps()` calls `c.setFacets(...)` with no `isFrozen()` guard, driven by the `.px` file's own `ft=` XML attribute | [CERT] | `organized/bajaui/fallback/niagara/ui/px/PxDecoder.java:308-331` |
| 8 | Exactly 3 `doc*.jar` files exist in the live N5 5.0.0.28 config-home modules dir | [CERT] | `ls /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/ \| grep -iE "^doc.*\.jar$"`, this session |
| 9 | `docSource.jar` ships the full 4-file `words/postings/documents/worddocs.dat` index but NOT `doc/bajadoc.index`; `docDeveloper.jar`/`docDeveloperAnalytics.jar` ship both | [CERT] | `unzip -l` on all 3 jars, this session (§109.2 table) |
| 10 | `BajadocIndex.loadAllEntries()` reads only `<HelpSystem.HELP>/bajadoc.dat`, never any jar's `doc/bajadoc.index` | [CERT] | `organized/help/vineflower/com/tridium/help/BajadocIndex.java:100-153` |
| 11 | `<config-home>/help/` does not exist yet in this beta install (combined index never built) | [CERT] | `ls /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/help/` → No such file or directory, this session |
| 12 | `SearchLoader.persistBajadocEntries()` builds `bajadoc.dat` by parsing every `.bajadoc` XML entry across all doc-eligible modules — unrelated to `bajadoc.index` | [CERT] | `organized/help/vineflower/com/tridium/help/SearchLoader.java:109-176,214-235` |
| 13 | `BHelpSideBar.buildApi()` reads each doc module's own `doc/bajadoc.index` file, one tree-root node per line | [CERT] | `organized/help/vineflower/com/tridium/help/ui/BHelpSideBar.java:232-254` |
| 14 | The PowerB N4-4.15.3.28 package ships `saml-rt.jar`/`saml-ux.jar`/`saml-wb.jar`/`samlEncryption-rt.jar` (not `saml.jar`) | [CERT] | `ls /mnt/c/PowerB/PowerB-4.15.3.28/modules \| grep -i saml`, this session |
| 15 | N4-4.15.3.28's `saml-rt.jar` bundles `com.onelogin.saml2.*` from `java-saml-core` version `2.9.0`, and zero `com.onelogin.saml` (old, singular) classes | [CERT] | `unzip -l`+`unzip -p ... pom.properties` on `saml-rt.jar`, this session |
| 16 | N4-4.15.3.28's `com/onelogin/saml2/util/Util.class` and N5 5.0.0.28's own copy (inside `saml.jar`'s nested `LIB-INF/java-saml-core-2.9.0.jar`) are byte-for-byte identical | [CERT-hw] | `cmp`+`sha256sum` both = `54f43814cd66b48fc9a407b8931d9f18290993822bb924edb8a440ce168f0374`, this session, files preserved at `/tmp/.../scratchpad/b109/{n4,n5}-Util.class` |
| 17 | N5 ships `saml.jar`+`samlEncryption.jar` (2 consolidated jars) | [CERT] | `ls /mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules \| grep -i saml`, this session |

**Tally**: 16 `[CERT]` (adjusted, header legend excluded) + 1 `[CERT-hw]` · 0 `[CERT-doc]`/`[CERT-web]`/
`[CERT-a]`/`[CERT-live]` · 0 `[INFER]` used as a load-bearing claim marker. [INFER]/[CERT*] ratio: 0 —
every closing verdict in this block rests on a file read, jar/zip inspection, or command run this
session; the one reused citation ([Block 103] §103.3's `ConfigFacetsCommand` gating, row 1 of the
census table) is explicitly marked as reused, not re-derived, per METHODOLOGY's ALREADY-COVERED
discipline.

**Artifacts**: `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/
scratchpad/b109/n5-java-saml-core-2.9.0.jar` (sha256
`41735e2063f1c511d342aab613b2144efb758e2364ecd9193b7639274a280f24`, extracted from N5's `saml.jar`
this session), `n4-Util.class`/`n5-Util.class` (both sha256
`54f43814cd66b48fc9a407b8931d9f18290993822bb924edb8a440ce168f0374`, extracted this session for the
`cmp`).
