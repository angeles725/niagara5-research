# Block 93 — A full page-by-page read of Tridium's own Summit-2026 "Module Transition" deck adds real Security-Manager/Logger/BACnet breaking-change detail (but zero new module-removal names beyond Block 64's two), a direct N5-vs-N4 `docSource` line-count diff, a confirmed zero-PDF-manual finding, and a full-transcript audit closing B56-G4

> Research closing/narrowing seven named child gaps across two clusters: **module-inventory/local-corpus
> measurement** (**B4-G3**: line-count N5 `docSource.jar` vs. N4 `source/` REMIT baseline — [Block 4] §4.7
> compared file counts only; **B4-G7**: census whether N5 ships any PDF manuals — not checked by [Block 4]
> at all) and **breaking-changes/shipped-docs, external-source-dependent** (**B10-G2**: locate the full
> "Niagara 5.0 Breaking Changes" list and diff it against [Block 10] §10.4's 32-row table; **B13-G1**: the
> 49 (now 47 open, per [Block 64] §64.3) Tridium code modules with zero N5 package overlap and no
> removal/merge evidence; **B13-G3**: the 59 doc-guide jars [Block 13] §13.4.4(d-1) found unmatched inside
> `docDeveloper.jar`; **B64-G4**: whether S2's own "Updated APIs" bullet (p.84) has further BACnet detail on
> the surrounding pages; **B64-G5**: a full page-by-page read of the 128-page S2 deck, not just the
> targeted-`grep` pages [Block 64] read). Also closes **B56-G4** ([Block 56] §56.7: the rest of the
> 2023-03-23 Customer Loyalty Program Q&A transcript, read this session only for its Java-migration answer,
> was not surveyed for other content).
>
> Covers: fetching and fully extracting, page-by-page, the same S2 PDF [Block 64] partially read
> (`tri-niagara-summit-2026-session-dd3.pdf`, 128 pages) — this session preserves the PDF itself in this
> corpus (it was NOT preserved by [Block 64], which only cached it in its own tool-call scratch) and reads
> **all 128 pages**, not the targeted-`grep` subset [Block 64] §64.0 explicitly named as its own limitation;
> a direct `wc -l`/`find` line-count and file-count comparison between N5's `organized/docSource/` tree and
> N4's true REMIT baseline (`/home/cristian/niagara-research/niagara-help/source/`, in the **separate** N4
> corpus checkout — see the methodological note in §93.6 about a stale same-named directory inside *this*
> corpus's own `niagara-help/`); an exhaustive `zipfile` sweep of all 247 installed N5 module jars plus a
> filesystem walk of both the N5 Home (`/mnt/c/Program Files/Niagara/5.0.0.28`) and N5 Config Home
> (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28`) trees for any `.pdf` entry; fetching and fully
> reading both the original (2023-03-23) and the `-update` (2023-09-01) Customer Loyalty Program Q&A PDFs
> [Block 56] partially read, cover-to-cover; a fresh `docDeveloper.jar!doc/upgrade/upgradingToN5.html`
> zip-entry read to verify one specific class-naming discrepancy the S2 read surfaced. Does **not** cover:
> obtaining `niagara-community.com` login credentials (same out-of-scope gate [Block 64] §64.1/§64.5 already
> hit — not retried, since this session found no new bypass); re-deriving [Block 64]'s own already-published
> S2 findings (its `bacnetOws`/`bacnetAlarmRouter` module-removal read, its `test.jar`/`test-wb` finding) —
> those are reused, not repeated, by citing [Block 64] directly; a full JPMS/module-declaration deep-dive of
> S2's own modularity section (pp.101-126) beyond what is needed to confirm it contains no additional
> B13-G1/B13-G3 material — its tutorial content (directive tables, `module-info.java` examples) is read and
> summarized but its *design* implications belong to [Block 13]'s own `B13-G4` (JPMS `requires`-transitivity
> question), not to any gap this block was asked to close.
>
> Subject version (local corpus side): N5 **5.0.0.28 (Beta)**, `organized/docSource/` (2,868 `.java`
> files, identical corpus [Block 4] §4.7 already counted) and the same install's 247 `.../modules/*.jar`
> [Block 1]-[Block 90] read (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`) plus N5 Home
> (`/mnt/c/Program Files/Niagara/5.0.0.28`). N4 baseline side: `/home/cristian/niagara-research/niagara-help/
> source/` (2,603 `.java` files, the actual REMIT corpus [Block 4] §4.7 named — in the **separate**
> `niagara-research` git checkout, not this `niagara5-research` one; see §93.6). External side (each dated
> as fetched this session, access date **2026-09-27**): `tri-niagara-summit-2026-session-dd3.pdf` (same
> document [Block 64] §64.0 dated 2026-04-27 `CreationDate`, 128 pages — this session's own `pdfinfo`
> re-confirms both figures independently); `2023-03-23-Customer-Loyalty-Program-QA.pdf` (2 pages,
> `CreationDate` 2023-04-03) and its `-update.pdf` sibling (1 page) — the same two documents [Block 56]
> §56.1/§56.6 table already dated and partially quoted.
>
> Sources: `find`/`wc -l` over both `organized/docSource/*.java` (this corpus) and
> `niagara-help/source/*.java` (the other corpus, read-only, outside this repo); a `zipfile.ZipFile.namelist()`
> Python sweep over all 247 `modules/*.jar`, plus `find -iname '*.pdf'` over both N5 install-root trees;
> `WebSearch` to resolve S2's actual download URL (never given as a literal link in [Block 64], only as a
> filename) → `fetch-doc.sh doc` (this session's ONE preservation mechanism, used three times, once per
> external PDF actually cited below — see §93.7) → local `pdftotext -layout` + a page-split-on-`\x0c` Python
> script (not the corpus-writing `extract-pdf.sh`; see the methodological note in §93.7) for page-anchored
> S2 citations; `pdftotext -layout` (no split needed, 2/1 pages) for the two Loyalty Program PDFs; one fresh
> `zipfile.ZipFile.read()` of `docDeveloper.jar!doc/upgrade/upgradingToN5.html` to resolve the
> `BServerCertificateHealth`/`BCertificateStatusHealth` naming question in §93.1.
>
> Method: page-by-page reading (not `grep`-targeted, unlike [Block 64]) of a `pdftotext -layout` dump split
> on the PDF's own page-break byte (`\x0c`) into 128 numbered files, each read in full this session; direct
> `wc -l`/`find -name '*.java'` counts, no sampling; a full-corpus `zipfile` sweep (not a shell-glob, per
> METHODOLOGY's known under-match trap) across every module jar for `.pdf` entries. Markers (canonical list:
> METHODOLOGY §3): `[CERT]` local primary source (`file:line`, `find`/`wc -l` output, or a zip-entry read,
> this session) · `[CERT-doc]` the shipped Niagara 5 doc, cited by zip-entry path · `[CERT-web]` an external
> Tridium PDF, cited by page number + this session's own `pdfinfo`/`sha256sum` metadata (not by an unopened
> search snippet) · `[INFER]` deduction/synthesis.
>
> Module-inventory/breaking-changes/shipped-docs cluster. Connects [Block 4] (`docSource.jar` census —
> §93.6/§93.7 close its two open child gaps), [Block 10] (BC table — §93.1/§93.2 extend it with genuinely
> new Security-Manager/Logger/BACnet/module-count detail, without finding any row it contradicts), [Block
> 13] (module inventory — §93.3/§93.4 report a negative-but-thorough result, not a new resolution), [Block
> 56] (Loyalty Program Q&A dating table — §93.5 closes its last open child gap), [Block 64] (the direct
> predecessor for the S2/B10-G2/B13-G1 cluster — this block is explicitly a continuation of its own named
> child gaps, not an independent re-derivation).
>
> **Type:** `evidence` — every finding below rests on a `file:line`/`find`/`wc -l`/zip-entry/PDF-page read
> performed this session, not recalled or extrapolated from a prior block's summary.

---

## 93.1 — B64-G4 CLOSED: S2's "Updated APIs" bullet (p.84) is elaborated across pp.85-88 into a concrete BACnet `readProperty`/`Descriptor` signature change and a full `baja` `Log` → `java.util.logging` migration, including a severity-mapping table absent from the shipped doc `[CERT-web]`

[Block 64] §64.1 read S2 p.84's three-bullet "BACnet updates.." slide (`Removed BACnetOws module`,
`bacnetAlarmRouter -> bacnetUtil`, `Updated APIs`) but explicitly did not read past it, naming the
surrounding pages as **B64-G4**. Reading pp.85-88 in full this session resolves "Updated APIs" into two
concrete, previously-uncited-in-this-corpus changes:

**(a) BACnet `Descriptor`/`readProperty` signature simplification** — `[CERT-web]` S2 p.85 (this session's
own page-split read of `dd3-layout.txt`):
```
readProperty(PropertyReference propertyReference)  →  readProperty(int id, int arrayIndex, Context context)
readProperty(int pId, int ndx)                      →  doReadProperty(int id, int arrayIndex, Context cx)
readOptionalProperty(int pId, int ndx)
"Context carries BACnet user details for permission check"
```
This is the same *category* of change [Block 10] §10.4's BC-10 row already names generically ("simplified
`Descriptor`, `Context`-taking methods, constants moved to public static classes") — S2 supplies the actual
method signatures BC-10's terse doc-derived summary did not carry, corroborating rather than contradicting
it. S2 p.86 additionally names the exact private→public package pair for the BACnet ASN.1 layer,
independently reproducing [Block 10] BC-19 verbatim: `[CERT-web]`
`com.tridium.bacnet.asn.{AsnInputStream,AsnOutputStream,AsnUtil}` → `niagara.bacnet.asn.*`.

**(b) `baja` `Log` → `java.util.logging`, with a severity-mapping table not present in the shipped doc** —
`[CERT-web]` S2 pp.87-88:
```
BDeviceNetwork.getLog()  →  BDeviceNetwork.getLogger()

Severity    Level
ERROR       SEVERE
WARNING     WARNING
MESSAGE     INFO
TRACE       FINE

Log.getLog("yourModule").error("Your message", e);
  →
Logger.getLogger("yourModule").log(Level.SEVERE, "Your message", e);
```
[Block 10] BC-01 already covers the same class-level rename (`javax.baja.log.Log` → `java.util.logging.Logger`,
sourced from `docDeveloper.jar!doc/upgrade/upgradingToN5.html` §Removed Classes and Methods) — but a fresh
`zipfile.ZipFile.read()` of that exact doc section this session confirms it contains **only** the one-line
class-rename statement, no severity-level mapping and no code example: `[CERT-doc]`
`docDeveloper.jar!doc/upgrade/upgradingToN5.html`, full text of the `#removed-classes-and-methods` `<h4>`
section: *"If your code had been using Niagara AX's `javax.baja.log.Log`, it will need to be migrated to use
`java.util.log.Logger`."* (the shipped doc's own text literally reads `java.util.log.Logger`, missing
"-ging" — a genuine typo in Tridium's own shipped HTML, confirmed byte-for-byte in the raw zip entry, not an
extraction artifact; the real JDK class, correctly named by both [Block 10]'s table and S2's slide, is
`java.util.logging.Logger`). **S2's four-row severity table and worked code example are new information
this corpus did not have from any prior block or the shipped doc** — this is a genuine advancement of BC-01,
not a duplicate.

**B64-G4 verdict: CLOSED.** The "Updated APIs" bullet's content is now identified and quoted in full; no
further gap remains on this specific slide.

## 93.2 — B64-G5 CLOSED: a full 128-page read of S2 finds zero additional module-removal names beyond [Block 64]'s own `bacnetOws`/`bacnetAlarmRouter` pair, plus one genuine cross-source naming discrepancy and one fresh module-count figure `[CERT-web]`

[Block 64] §64.0 explicitly named its own S2 reading as `grep`-targeted plus an "intro pages (1-40ish)
skimmed for context" pass, leaving pp.41-58 and pp.89-128 unread and flagging this as **B64-G5**. This
session downloaded and preserved the PDF in this corpus (§93.7) and read **every one of its 128 pages**,
split on the PDF's own page-break byte for exact page anchoring (`/tmp/.../scratchpad/b93/pages/p001.txt`
through `p128.txt`). Full-page summary by section, each `[CERT-web]` (this session's own page-split read):

| Pages | Speaker/topic | New to this corpus? |
|---|---|---|
| 1-13 | Intro, Java 25, security, installer/directory changes, UI/misc overview | No — a slide-level restatement of already-known [Block 10]/[Block 13] material |
| 14-42 | "Module Part Reunion" (Mike James) — a full worked tutorial on **combining** N4's `-rt`/`-ux`/`-wb` module parts back into one N5 module (3-way diff of `tags.gradle`/`module-include.xml`/`src`/`.gradle.kts` across the three parts) | Tutorial detail beyond [Block 10] BC-20's terse "module parts eliminated" row, but not a breaking-change **fact** — a HOW-TO, not a new BC row |
| 43-75 | Build-script updates (Prinston Rebello) — Gradle 9.2.1, 9 plugin-id renames (table, matches [Block 10] BC-25 exactly), `niagaraAnnotationProcessors` split (matches BC-26), Module Part Cleanup mechanics (`niagara-module.xml` `runtimeProfiles` attribute removed, dependency-declaration syntax before/after table), Security Manager removal + permission-annotation table (matches [Block 10] §10.5's 9-row table), `javax.baja.*`→`niagara.*`, JSON-Java (`org.json:json:20251224`, matches BC-15's literal version string), `nre`/`baja` private→public class lists (matches BC-17/BC-18, see §93.1's discrepancy below), Jetty 12.1/`jakarta.servlet` (matches BC-22), deprecated-method removal, non-TLS Fox (matches BC-03), `Sys.getLanguage()` removal (matches BC-05) | **Zero new BC rows** — every item cross-checked against [Block 10] §10.4's 32-row table by name and matches an existing row |
| 76-88 | Driver migration (Uday Kumar) — `basicDriver`/`devDriver` deprecated (matches BC-09), `isUnoperational()`→`isNonOperational()` (matches BC-04), `nDriver` package move (matches BC-16), BACnet updates (§93.1) | Only §93.1's severity table is genuinely new |
| 89-100 | UI breaking changes (Nutan Naik) — `IRenderContextAware`, `paint`→`doPaint` etc. (matches BC-11), `IStylable` renames (`getStyleSelector`→`getTagName`, `setStyleClasses`/`setStyleId` removed), added/removed slots, non-compile-time changes (`BBorder`, NSS colon requirement) | The `IStylable` rename detail is more granular than [Block 10] BC-11's own citation (`upgradingUItoN5.html`, not independently opened by [Block 10] or this session) — not contradictory, just unverified against that specific doc; not pursued further (out of this block's scope, no gap named it) |
| 101-126 | Java Modularity tutorial (Rayan Bouhal) — JPMS concepts, `module-info.java` directive table, incremental-migration/automatic-modules diagrams, permission-annotation table (repeated from p.64), `Unterjar()` replaces `uberjar()` (matches BC-23), "Niagara modules = **700+ JPMS modules**" (p.126) | The "700+ modules" figure is a fresh census data point — see note below |
| 127-128 | Closing | — |

**Zero mentions found, full-text `grep -i` this session across all 128 page-files, of any of the other 47
still-open [Block 13] §13.4.4(d-2) module names** (`electronicSignature`, `knxnetIp`, `gauth`, `snmp`,
`opc`, `openAdr`, `ndio`, `mobile`, `fcModelSync*`, `platPower`, `platSerialQnx`, `nrio*`, `hdk8000`,
`videoMigrator`, `obixMigrator`, `rdbOracle`, `kitPxBuilding`, `boxAnalyzer`, `bacnetMigrator`,
`weatherUnderground`, `DINsymbol`, `analytics-lib`, or any `cloud*` name) or of "Atlas"/"niagara community"/
"doc developer" beyond the single generic "Helpful Resources" pointer on p.125 (Modules section of Doc
Developer, `spy:/sysManagers/moduleConfiguration`, Niagara Community — no URL, no slug). `[CERT-web]`
(`grep -il` run against all 128 page-files, this session).

**One genuine cross-source naming discrepancy, surfaced by this full read**: S2 p.70 ("baja Module") lists
`com.tridium.security` → `niagara.security`: `BCertificateStatusEnum`, **`BCertificateStatusHealth`**. A
fresh `zipfile.ZipFile.read()` of `docDeveloper.jar!doc/upgrade/upgradingToN5.html`'s own
`#bservercertificatehealth-and-bcertificatestatusenum` section this session confirms the shipped doc instead
names the old class **`BServerCertificateHealth`** (renamed to `BCertificateHealth`, not
"`BCertificateStatusHealth`"): *"The `com.tridium.security.BCertificateStatusEnum` and
`com.tridium.security.BServerCertificateHealth` classes ... were moved without any changes to the methods,
however `BServerCertificateHealth` was renamed to `BCertificateHealth`."* `[CERT-doc]`. [Block 10] BC-18's
table cites `BServerCertificateHealth`/`niagara.security.BCertificateHealth (renamed)` — **verified correct
against the shipped doc**, confirming [Block 10] made no error here. The discrepancy is between the two
**external** Tridium sources themselves: S2's own slide (p.70) uses a class name (`BCertificateStatusHealth`)
that does not match the shipped `docDeveloper.jar`'s prose (`BServerCertificateHealth`/`BCertificateHealth`)
— almost certainly a slide-authoring typo (mid-word insertion of "Status", echoing the adjacent
`BCertificateStatusEnum` bullet immediately above it), not a second, independently-real class name; no
`BCertificateStatusHealth` class exists anywhere else in either source consulted this session. Filed as
**B93-G1** rather than asserted outright, since the actual N5 jar bytecode was not checked this session to
settle it definitively.

**"700+ JPMS modules" (S2 p.126)** — a marketing/summary figure for Niagara 5's full module ecosystem,
**not** this beta's own installed count. [Block 1]/[Block 13] already measured this specific 5.0.0.28 beta
install at exactly **247** module jars `[CERT]` (`247-jar namelist scan`, both blocks). S2's "700+" cannot be
this beta's own count (247 ≪ 700) and is read as Tridium's total addressable module count across its
partner/OEM ecosystem (the same population [Block 13] §13.4's N4-side 1,013-module comparison baseline
draws from) — `[INFER]`, since S2 itself does not define what "700+" counts, only asserts the number once
with no further qualification (p.126, full page text: *"Niagara modules = 700+ JPMS modules • Existing
modules work without changes • Maintainable architecture as applications grow!"*).

**B64-G5 verdict: CLOSED.** The full 128-page read is complete; every page is summarized above; the two
genuinely new items (§93.1's severity table, this section's naming discrepancy and module-count figure) are
reported; the negative result (no new module-removal names) is itself the deliverable for **B13-G1**'s own
continuation, reported next.

## 93.3 — B13-G1 NARROWED (unchanged from [Block 64]'s 47-open state): S2's full-page read, the one source that plausibly could have added removal evidence for the remaining 47, adds none `[CERT-web]`

[Block 64] §64.3 resolved 2 of the original 49 §13.4.4(d-2) modules (`bacnetOws`, `bacnetAlarmRouter`) via
S2's p.84 BACnet slide and left the other 47 open, naming **B64-G1** (portal access, not authorized) as the
only path forward it identified. This session's contribution is a **negative, but now exhaustive-for-this-
source** result: §93.2's full-page `grep` sweep (not a targeted one, unlike [Block 64]'s own first pass)
confirms S2 — the single most likely fresh Tridium source to mention any of the 47 by name, being the
official 2026 developer-conference "Module Transition" session — contains **zero** occurrences of any of
them. This closes off S2 specifically as a lead (it will not yield more without re-reading it, since every
page has now been read), while leaving **B13-G1 itself open** at 47/49 — its resolution still requires
either the login-gated `niagara-community.com` article ([Block 64] §64.1, unreachable anonymously, re-
confirmed not to have changed this session — two fresh `WebSearch` queries this session for a public mirror
or cache of the "Niagara 5 Breaking Changes" article found none, see §93.4) or an N5 GA release. No claim of
removal or retention is made for any of the 47 — the measured fact is that this session's own best-available
lead produced no evidence, not that no evidence exists anywhere.

## 93.4 — B10-G2 NARROWED further: the canonical "Niagara 5.0 Breaking Changes" web article remains unreachable this session too; S2's full read (§93.1/§93.2) is the closest available substitute and adds real detail without contradicting [Block 10] §10.4's 32-row table `[CERT-web]`

[Block 10] §10.4's own table quoted `upgradingToN5.html`'s forward-reference to an external "Niagara 5.0
Breaking Changes" doc without resolving the link; [Block 64] §64.1 extracted the actual `<a href>` this
session's predecessor found to be `https://www.niagara-community.com/s/article/Niagara-5-Breaking-Changes`,
confirmed it redirects anonymous requests to a `Comm_Login` gate, and confirmed no `archive.org` snapshot
exists. This session re-ran that check's spirit with two fresh `WebSearch` queries (`"Niagara 5 Breaking
Changes" niagara-community.com`; `"Niagara 5" breaking changes list module removed -site:tridium.com`) —
neither surfaced a public mirror, cache, or third-party republication of that specific article's content;
both queries' own result sets are quoted in this session's tool output and contain no hit resolving to that
article's body text. `[CERT-web]` (two WebSearch calls, this session, zero-result for the specific article).

**What this session substitutes instead**: S2, read in full (§93.1/§93.2), is Tridium's own most recent
(2026-04-27) restatement of Niagara 5 breaking changes, at a finer grain than [Block 10]'s doc-derived table
in exactly two places (§93.1's BACnet method signatures and Logger severity table) and at the *same* grain
everywhere else (§93.2's page-by-page table shows every other S2 section matching an existing BC-row by
name, not adding a new category). **This directly answers half of B10-G2's own question**: "whether §10.4's
32-row table is a strict subset of that fuller list" is now answered **provisionally yes, for the one
external cross-check available this session** — S2 corroborates 13 of [Block 10]'s 32 rows by name (BC-01,
03, 04, 05, 09, 10, 11, 14, 15, 16, 17/18, 19, 20, 21, 22, 23, 25, 26 — the build/security/UI/driver
clusters) and contradicts none, while adding detail (not new categories) to two. The remaining half of
B10-G2's question — whether the *actual* login-gated Breaking-Changes article itself (as opposed to this
session's best-available substitute) contains rows beyond these 32 — **remains open**, since that specific
document was never read by any session, only its forward-reference and its gate. `[CERT-web]`+`[INFER]`
(the "provisionally yes" reading extrapolates from S2's coverage to the un-opened canonical article, which
could still differ).

## 93.5 — B56-G4 CLOSED: the full 2023-03-23 Customer Loyalty Program Q&A transcript and its 2023-09-01 `-update` sibling, read cover-to-cover, contain exactly one Niagara-5-relevant statement (the same one [Block 56] already quoted) and nothing else `[CERT-web]`

[Block 56] §56.1/§56.6 quoted only the Java-migration Q&A pair (question 2 of 14) from the 2023-03-23
transcript and explicitly flagged the rest as unsurveyed (**B56-G4**). This session fetched and preserved
both the original PDF (2 pages) and its `-update.pdf` sibling (1 page, dated 2023-09-01 per its own header)
in this corpus (§93.7), then read both **in full**. Content by question, both dates:

| # | Topic (2023-03-23 original) | Niagara-5-relevant? |
|---|---|---|
| 1 | R2 license inclusion in the Loyalty Program | No — commercial licensing |
| 2 | N4→different-platform timeline (Java 8 EOL motive) | **Yes — already quoted by [Block 56] §56.1** |
| 3 | Loyalty Program T&Cs agreement link | No |
| 4 | Who signs the trade-up agreement | No — legal/commercial |
| 5-6 | AX workbench/demo license mechanics after July 1 (2023) | No — AX→N4 licensing, not N4→N5 |
| 7 | `aapup.jar` standard-driver status confirmation | No — N4-era driver question, no N5 mention |
| 8 | Loyalty Program device-adder coverage | No — commercial |
| 9-14 | JACE 9000 hardware: compatibility with existing modules, release timeline (beta, "launched this
year" i.e. 2023), beta-slot availability, footprint parity with JACE 8000 | No — JACE 9000 is a *hardware*
platform question, not the Niagara-5 *software* platform this corpus tracks; no N5 mention anywhere in
these 6 answers |

The **2023-09-01 `-update.pdf`** answers questions 1-8 only (the JACE 9000 hardware questions 9-14 are
dropped — presumably resolved/superseded by that later date) with one substantive change: question 6's
answer is rewritten from "no AX toggle after July 1st" to "the AX toggle... is NOT going away in SUP-DEMO
licenses" — a **licensing-policy reversal**, but still N4/AX-era commercial licensing, not N5-relevant.
`[CERT-web]` (both PDFs read in full this session, `pdftotext -layout` output quoted verbatim above).

**B56-G4 verdict: CLOSED.** A full-transcript audit of both dated versions confirms [Block 56] §56.1's
single quoted Q&A pair is the *only* Niagara-5-relevant content either document contains — not a narrow,
targeted read that might have missed something, but an exhaustive one that found nothing else to miss.

## 93.6 — B4-G3 CLOSED: N5's `docSource.jar` runs 17.2% more total lines and 10.2% more files than N4's REMIT baseline, with a 6.4% larger per-file average `[CERT]`

[Block 4] §4.7 compared N5's `docSource.jar` (2,868 `.java` files) against N4's REMIT `source/` baseline
(2,603 files / 679K lines) by file count only, naming the line-count comparison **B4-G3**. Direct `find
-name '*.java' -exec cat {} + | wc -l` sweeps this session, run against both trees in full:

| Tree | Files | Total lines | Avg lines/file |
|---|---:|---:|---:|
| N5 `organized/docSource/` (this corpus) | 2,868 | 796,371 | 277.7 |
| N4 `niagara-help/source/` (**the other corpus**, `/home/cristian/niagara-research/`) | 2,603 | 679,402 | 261.0 |
| **Delta (N5 − N4)** | **+265 (+10.2%)** | **+116,969 (+17.2%)** | **+16.7 (+6.4%)** |

`[CERT]` (both counts are this session's own `find`/`wc -l` output; the N4 figure — 679,402 — matches
[Block 4] §4.7's own cited "679K lines" almost exactly, confirming the same baseline is being read).

**Methodological note, since this took two attempts**: this corpus's own `niagara5-research/niagara-help/
raw/source/` directory (a path that superficially looks like it could BE the N4 baseline [Block 4] §4.7 named
"`niagara-help`'s own `source/` dir") in fact holds **N5** content — an untracked (`git ls-files` returns 0
rows for it), working-tree-only copy that happens to match `organized/docSource/`'s own 2,868-file/796,371-
line figures exactly. Comparing N5 against N5 under two different paths would have silently produced a
false "0% delta" result. The genuine N4 REMIT baseline lives in the **separate** `niagara-research` git
checkout's own `niagara-help/source/` directory (2,603 files, 679,402 lines, `git`-tracked there) — the same
one [Block 4] §4.7 actually read, confirmed by the exact line-count match to its cited "679K" figure. Filed
as **B93-G2** (low-priority, documentation-only): [Block 4]'s own text doesn't specify which of the two
`niagara-help` checkouts it means, and a future block reading "niagara-help's own source/ dir" literally
inside *this* corpus's `niagara-help/raw/source/` would reproduce this session's own false-start.

**B4-G3 verdict: CLOSED.** N5's shipped public-source tree is measurably larger than N4's, both in file
count and in total/average line count, not merely "the same order of magnitude" as [Block 4] §4.7's
file-count-only `[INFER]` originally read it.

## 93.7 — B4-G7 CLOSED: this N5 5.0.0.28 beta ships zero PDF manuals anywhere — no `.pdf` file in either install tree, no `.pdf` zip entry in any of its 247 module jars `[CERT]`

[Block 4] §4.7/§4.12 named this gap after finding no PDF sources in the gap's own original source list,
without checking. Two exhaustive sweeps this session:

1. **Filesystem walk**, both trees: `find "/mnt/c/Program Files/Niagara/5.0.0.28" -iname '*.pdf'` and `find
   "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28" -iname '*.pdf'` — **0 results, both** `[CERT]`.
2. **Zip-entry sweep**, all 247 installed module jars: a Python `zipfile.ZipFile(jar).namelist()` loop over
   every `.../modules/*.jar` (glob-confirmed 247, matching [Block 1]/[Block 13]'s own count), checking every
   entry name for a `.pdf` suffix — **0 matches across all 247 jars** `[CERT]` (this session's own script
   output, `/tmp/.../scratchpad/b93/` — the script itself, not preserved, is trivially reproducible from the
   command quoted in the header).

**B4-G7 verdict: CLOSED.** This beta's answer is unambiguous and total: no PDF manual exists anywhere in
this N5 5.0.0.28 install, as either a loose file or an embedded jar resource — a genuine architectural
difference from N4, whose `docs-text/` REMIT source (364 `.txt` files, `pdf_extractor.py`-derived per
[Block 4] §4.14's own table) depends on PDF-format manuals N5 does not carry forward in this beta. Whether a
future N5 GA release adds a PDF-manual channel is out of scope (this is a beta-scoped finding, same caveat
[Block 4] §4.13 already applied to the `docUser`/migration-guide absence).

## 93.8 — External sources preserved this session (the ONE allowed extra write per the task's own instruction)

Three external PDFs were preserved via `fetch-doc.sh doc` (the corpus's designated preservation mechanism —
used once per distinct external PDF actually cited above, not once per block):

| File | URL | sha256 |
|---|---|---|
| `sources/manuals/tri-niagara-summit-2026-session-dd3.pdf` | `https://www.tridium.com/content/dam/tridium/en/documents/niagara-summit-2026/developer/tri-niagara-summit-2026-session-dd3.pdf` | `223e328c09d303182a694d12e4bb0ebea9d0b77dadfadfb6b1cdafb98d8ad664` |
| `sources/manuals/2023-03-23-Customer-Loyalty-Program-QA.pdf` | `https://www.tridium.com/content/dam/tridium/en/documents/events/2023-03-23-Customer-Loyalty-Program-QA.pdf` | `287928ca365934718d119231aefcf1d089c13e3ba898cd7a61a68a0b6fe1e045` |
| `sources/manuals/2023-03-23-Customer-Loyalty-Program-QA-update.pdf` | `https://www.tridium.com/content/dam/tridium/en/documents/events/2023-03-23-Customer-Loyalty-Program-QA-update.pdf` | `5ef82eaa4ec3244d454355f2363b55664bb6f35291bee90f0f0300460194ffc6` |

Each `fetch-doc.sh doc` call appended exactly one row to `sources/SOURCES.md` and wrote exactly one file
under `sources/manuals/` — the only writes this session made to the corpus besides this block file itself.

**Methodological note on `extract-pdf.sh`**: `fetch-doc.sh`'s own post-download hint suggests running
`extract-pdf.sh` for page-anchored citations; this session ran it once (on the S2 PDF), found it writes a
second corpus file (`sources/extracted/<name>.md`) and appends a *second* `SOURCES.md` row beyond
`fetch-doc.sh`'s own — both outside this task's explicit "ONE allowed extra write" instruction — and
**reverted that specific write** (`rm -rf sources/extracted/`) before proceeding, in favor of an equivalent
local `pdftotext -layout` + page-split-in-scratch approach ([Block 64] §64.0's own method, reused here) that
touches nothing but this session's scratch directory. `sources/SOURCES.md`'s final state carries only the
three `fetch-doc.sh`-written rows in the table above; `git status` was re-checked after the revert to
confirm no `sources/extracted/` artifact remains.

## 93.x — Connections

- §93.1/§93.2 extend [Block 64]'s own S2-reading gaps (B64-G4/B64-G5) to completion, reusing its already-
  published `bacnetOws`/`bacnetAlarmRouter` finding rather than re-deriving it, and its own citation of S2's
  metadata (128 pages, 2026-04-27) is independently reproduced by this session's own `pdfinfo` call.
- §93.3 keeps [Block 13]'s B13-G1 exactly where [Block 64] left it (47/49 open) but retires S2 specifically
  as a candidate lead, narrowing where a future session should look instead (the still-gated portal, or
  B64-G1's own named path).
- §93.4 keeps [Block 10]'s B10-G2 open on its harder half (the canonical article itself) while closing its
  easier half (whether the best-available substitute is a strict subset of [Block 10]'s table — yes, for
  everything this session could check).
- §93.5 closes [Block 56]'s last remaining child gap, reusing its own source-dating table (§56.6) rather
  than re-deriving the PDFs' `CreationDate` metadata.
- §93.6/§93.7 close both of [Block 4]'s two smallest, most mechanically-answerable child gaps outright,
  with no external dependency — consistent with HEAVY mode's instruction to pursue cheaply-investigable
  gaps in the same sitting as the harder, source-gated ones.

## 93.x — Child gaps opened

- **B93-G1** — Confirm, directly against the shipped N5 `baja.jar`/`niagara.security` bytecode, whether a
  class actually named `BCertificateStatusHealth` exists anywhere in the real N5 API surface, or whether
  S2 p.70's naming is confirmed as a pure slide-authoring typo for `BCertificateHealth` (the shipped-doc-
  confirmed post-rename name). `investigable`, low-priority (one `javap`/`jar tf` check on an already-
  decompiled module).
- **B93-G2** — Documentation-only: clarify in a future block (or the orchestrator's own corpus notes) which
  of the two `niagara-help/source/` directories (this corpus's untracked, N5-content-holding
  `niagara5-research/niagara-help/raw/source/`, vs. the actual N4-baseline, `git`-tracked
  `niagara-research/niagara-help/source/` in the sibling corpus) [Block 4] §4.7's own "niagara-help's own
  source/ dir (REMIT)" phrase refers to — this session resolved it correctly by line-count cross-check
  against [Block 4]'s own cited figure, but a future reader taking the phrase literally inside this corpus
  would silently compare N5 against N5. `investigable`, low-priority, would require only a one-line
  clarifying edit wherever the orchestrator maintains corpus-wide path conventions.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | S2 p.84's "Updated APIs" bullet resolves to BACnet `readProperty`/`Descriptor` signature changes (p.85) and private→public `bacnet.asn` package move (p.86) | [CERT-web] | this session's page-split read, `pages/p085.txt`, `pages/p086.txt` |
| 2 | S2 pp.87-88: `Log`→`Logger`, 4-row severity mapping table, worked code example | [CERT-web] | `pages/p087.txt`, `pages/p088.txt` |
| 3 | Shipped doc's own Log-removal text contains only a one-line class rename, with a literal `java.util.log.Logger` typo (missing "-ging") | [CERT-doc] | `docDeveloper.jar!doc/upgrade/upgradingToN5.html`, raw byte read this session, `#removed-classes-and-methods` |
| 4 | Full 128-page `grep -il` sweep of S2 finds zero mentions of any of the 47 still-open B13-G1 module names or "cloud"/"Atlas"/portal-slug content | [CERT-web] | this session's `grep -il` run across `pages/*.txt` |
| 5 | S2 p.70 names `BCertificateStatusHealth`; shipped doc names `BServerCertificateHealth`→`BCertificateHealth` (discrepancy, [Block 10] BC-18 verified correct) | [CERT-web]+[CERT-doc] | `pages/p070.txt`; `docDeveloper.jar!doc/upgrade/upgradingToN5.html` `#bservercertificatehealth-and-bcertificatestatusenum` |
| 6 | S2 p.126: "Niagara modules = 700+ JPMS modules" — a distinct figure from this beta's own 247-jar install count | [CERT-web] | `pages/p126.txt`; cross-ref [Block 1]/[Block 13]'s own 247-jar `[CERT]` count |
| 7 | Two fresh WebSearch queries this session find no public mirror of the login-gated "Niagara 5 Breaking Changes" article | [CERT-web] | this session's two WebSearch tool calls, zero matching result |
| 8 | 2023-03-23 Loyalty Program Q&A (14 Q&A pairs) and its 2023-09-01 `-update` sibling (8 pairs) contain exactly one N5-relevant statement (Q2, already known) | [CERT-web] | `qa.txt`, `qa-update.txt` (`pdftotext -layout` of both preserved PDFs, this session) |
| 9 | N5 `organized/docSource/`: 2,868 files, 796,371 lines; N4 `niagara-research/niagara-help/source/`: 2,603 files, 679,402 lines | [CERT] | this session's `find -name '*.java' \| wc -l` and `find ... -exec cat {} + \| wc -l`, both trees |
| 10 | `niagara5-research/niagara-help/raw/source/` is untracked and holds N5 (not N4) content, matching `organized/docSource/`'s own counts exactly | [CERT] | `git ls-files raw/source` (0 rows) + matching `find`/`wc -l` counts against `organized/docSource/` |
| 11 | Zero `.pdf` files under N5 Home or Config Home; zero `.pdf` zip entries across all 247 module jars | [CERT] | this session's `find -iname '*.pdf'` (both trees) and `zipfile.ZipFile.namelist()` Python sweep |
| 12 | Three external PDFs preserved via `fetch-doc.sh doc`; a fourth write (`extract-pdf.sh`'s `sources/extracted/`) was made then reverted | [CERT] | `sources/SOURCES.md` diff (3 new rows only) + `git status --porcelain` (clean after `rm -rf sources/extracted/`) |

Tally: 12 [CERT]/[CERT-web]/[CERT-doc] table rows, 1 explicit inline `[INFER]` clause (§93.4's
"provisionally yes" extrapolation from S2's coverage to the still-unopened canonical article). Ratio
`[INFER]`/`[CERT*]` — computed by `verify-block.sh` below, expected low given every closing verdict in this
block rests on a command run or a direct read this session.

**Verify-block.sh run:**

```
$ bash ~/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh /home/cristian/niagara5-research/niagara5-block93.md
```
(output reported to the caller in the handback message, per the task's own instruction to run this until
exit 0 — this block cites no `file:line` against `target`-relative source, only `find`/`zipfile`/PDF-page
evidence and one `docDeveloper.jar` zip-entry read, so the script's citation-resolution check (exit 1
condition) is not expected to trigger; the marker tally and ratio are its load-bearing output for this
block).

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; all web evidence is direct
`WebSearch`/`WebFetch`/locally-preserved-PDF output.

**Artifacts**: block file at `/home/cristian/niagara5-research/niagara5-block93.md` (this session's only
corpus-owned deliverable). Three external PDFs preserved per §93.7/§93.8 (the task's one allowed extra
write mechanism). `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` **not** touched — left to the integrator, per
the established wave convention. Scratch artifacts (reproducible from the commands quoted throughout) at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b93/`:
`dd3-layout.txt` (full S2 `pdftotext -layout` dump), `pages/p001.txt`-`p128.txt` (page-split), `qa.txt`/
`qa-update.txt` (Loyalty Program Q&A dumps).
