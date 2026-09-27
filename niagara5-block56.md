# Block 56 — Niagara 5 public statements on Java version and high availability, reconciled with the beta

> Research of **PUBLIC web evidence dating and reconciling two open contradictions/gaps from [Block 48]**:
> **B48-G1** (the Java-21-vs-Java-25 public contradiction, [B48] §48.3/[C1]) and **B48-G5** (the FAQ's
> "limited availability first" framing of Niagara Sync/redundancy/HA, [B48] §48.10). Covers: every public
> statement on Niagara 5's Java version this session could locate (Tridium product page, FAQ PDF, Niagara
> Summit agenda, a Niagara Forum 2025 technical slide deck, three independent third-party aggregator pages,
> and the earliest located first-party Java-migration discussion), each dated where a date exists, with a
> verdict on whether the Java-21 statements are stale-vs-current or simply wrong; local corroboration
> against the installed N5 5.0.0.28 beta JRE's own `release` file and class-file major-version census
> ([Block 25]/[Block 30]) and the shipped devkit's build-requirement doc ([Block 2]/[Block 39]); and what
> Tridium publicly says about Niagara 5 high availability / Niagara Sync / redundancy (names, availability
> framing, licensing, hardware) reconciled against the beta's shipped `niagaraSync` module and its
> `tridium:niagaraSync` license-feature string ([Block 37] §37.7). Also checks for any public N5 statement
> on Supervisor OS (Windows/Linux) and the JACE-9000 image. Does **not** cover: a live N5 GA build (does
> not exist publicly as of this session — per [B48] §48.1, GA is targeted December 2026), Developer-Program-
> gated documentation (`docs.niagara-community.com`, confirmed login-gated in [B48] §48.5), or a full
> archival (Wayback Machine) crawl — the WebFetch tool used this session explicitly refuses
> `web.archive.org` URLs (reported as a tool limitation below, not a finding).
>
> Subject version: **not applicable in the usual sense** for the web-evidence sections — this block's
> subject is the public web as it stood on the access date below. For the local-corroboration sections
> (§56.4), Subject version: **N5 5.0.0.28 (Beta)**, same install as [Block 25]/[Block 30]/[Block 2]/
> [Block 37]. Access date for every `[CERT-web]` citation in this block: **2026-09-27**.
>
> Sources: `https://pages1.tridium.com/rs/808-SGM-271/images/N5-FAQ.pdf` (Tridium official, content-stamped
> "Updated October 27, 2025" — fetched fresh this session via `curl`, not WebFetch's lossy summarizer, and
> read in full locally via `pdftotext -layout`, saved at `/tmp/n5faq.pdf`/`/tmp/n5faq.txt`, 265 lines) ·
> `https://www.tridium.com/us/en/Products/niagara/niagara5` (Tridium official product page) ·
> `https://www.tridium.com/us/en/niagarasummit/agenda-overview` (Tridium official, Niagara Summit 2026,
> April 7-9 2026, agenda overview — session-level detail not present on this page) ·
> `https://www.tridium.com/content/dam/tridium/en/documents/niagara-forum-2025/technical/
> tri-NF25_Technical_Niagara_Today_and_Tomorrow_News_Update.pdf` (Tridium official, Niagara Forum 2025
> technical-update slide deck, PDF metadata: author "Chris Irwin", creation date **2025-04-29** — fetched
> fresh via `curl`, read in full locally via `pdftotext -layout`, saved at
> `/tmp/.../webfetch-1790516366212-rqge4v.pdf`) ·
> `https://www.tridium.com/content/dam/tridium/en/documents/events/2023-03-23-Customer-Loyalty-Program-QA.pdf`
> and its `-QA-update.pdf` sibling (Tridium official, TridiumTalk Q&A transcript, dated **2023-03-23** —
> fetched fresh via `curl`, read in full locally via `pdftotext -layout`) ·
> `https://guides.smartbuildingsacademy.com/tridiumguide` (third-party training-vendor guide, self-stamped
> "initially published November 9, 2016; updated as of April 15, 2025") ·
> `https://onesight.solutions/tridium-niagara-5-n5-information/` (third-party partner aggregator, self-
> stamped "February 6, 2025" — re-verified fresh this session, matches [B48] §48.3's prior read) ·
> `https://docs.forestrock.co.uk/niagara-5-frequently-asked-questions` (third-party partner aggregator,
> self-stamped "Updated February 12, 2026" — re-verified fresh this session, matches [B48] §48.3's prior
> read) · local: `/mnt/c/Program Files/Niagara/5.0.0.28/jre/release` (installed N5 beta JRE, read directly
> this session) · [Block 25] §25.1/§25.5, [Block 30] §30.2 (prior-sealed local `[CERT]` class-file
> major-version census, cross-referenced not re-derived) · [Block 2] §2.8, [Block 39] (prior-sealed local
> `[CERT-doc]` `buildN5.html`/`gradle.properties.vm` Java-25-JDK-with-JavaFX requirement, cross-referenced
> not re-derived) · [Block 37] §37.7 (prior-sealed local `[CERT]` `tridium:niagaraSync` license-feature
> finding, cross-referenced not re-derived). Two dead links encountered and reported as data (§56.6):
> `2024.11.21-Nagara-Newsletter-November-2024.pdf` and `2025.01.30-Niagara-Newsletter-January-2025.pdf`
> both 404 on `tridium.com` this session.
>
> Method: targeted WebSearch queries per the assigned gap list, WebFetch on promising hits, `curl`+
> `pdftotext -layout` full-text extraction on every PDF (bypassing WebFetch's lossy PDF-to-markdown
> summarization and its binary-PDF failure on the image-heavy Forum-2025 deck), `grep -in` full-text search
> for "java"/"sync"/"redundan"/"linux"/"windows"/"premium" across every extracted `.txt`, direct local file
> read of the installed beta JRE's `release` manifest, cross-reference (not re-read) of four prior blocks'
> already-sealed `[CERT]`/`[CERT-doc]` findings. Markers (canonical list, METHODOLOGY §3): `[CERT-hw]`/
> `[CERT-live]` highest (none this block — no live station probed) · `[CERT]` local primary source
> (none newly derived this block; §56.4 cross-references PRIOR blocks' own `[CERT]`/`[CERT-doc]` findings,
> cited by block+section, not re-verified line-by-line) · `[CERT-doc]` official downloaded document (none
> newly downloaded-and-registered this block — PDFs were fetched to session-scratch, quoted inline, not
> preserved under `sources/`, per this block's read-only public-web task scope, same convention as [B48]) ·
> `[CERT-web]` official web (the dominant marker this block) · `[CERT-a]` secondary source (the three
> third-party aggregator pages) · `[INFER]` this block's own synthesis.
>
> Public-evidence layer, dating layer over [Block 48]. Connects [Block 48] (§56.1-§56.3 date-resolve
> B48-G1/[C1], §56.5 extends B48-G5), [Block 25]/[Block 30] (§56.4.1 local Java-version corroboration),
> [Block 2]/[Block 39] (§56.4.1 devkit-requirement corroboration), [Block 37] (§56.5 reconciles the public
> "Niagara Sync" name against the code's `tridium:niagaraSync` license feature).
>
> **Type:** `mixed` — §56.1/§56.2/§56.4/§56.6/§56.7 are evidence sections citing only this session's fresh
> web/local reads; §56.3/§56.5 draw `[INFER]` conclusions by diffing this session's evidence AGAINST
> [Block 48]'s own open gaps and [Block 37]'s prior code-level finding, the declared trigger for `mixed`
> per METHODOLOGY §4.

---

## 56.1 — Source table: every public Java-version statement located this session, dated `[CERT-web]`

| Source | Type | Own date stamp | Java statement (verbatim) | Access date |
|---|---|---|---|---|
| `tridium.com/.../niagara5` product page | Tridium official | none visible on page | "Built on **Java 25**, Niagara 5 delivers enhanced performance, expanded capabilities, and a future-ready foundation." | 2026-09-27 |
| `N5-FAQ.pdf` | Tridium official | **"Updated October 27, 2025"** (content stamp, [B48]) | "...to support **Java 25** and code migration readiness" (p.3, availability-schedule answer) AND "Because Niagara 5 moves from **Java 8 to Java 25** and includes platform changes..." (p.4, module-compatibility answer) — **only 2 occurrences of "java" in the whole 265-line extracted text, both say 25, zero say 21** | 2026-09-27 (re-verified fresh this session, `/tmp/n5faq.txt`) |
| Niagara Forum 2025 technical-update slide deck | Tridium official | PDF metadata creation date **2025-04-29**, author "Chris Irwin" | **Zero occurrences of "java" anywhere in the extracted text** (checked via `grep -in "java"` over the full local `pdftotext -layout` extraction) — the deck places N5 on a roadmap timeline chart positioned after "4.15 LTS", toward the chart's right edge (~2028-2029 region), but states no Java version | 2026-09-27 |
| 2023-03-23 Customer Loyalty Program Q&A (+ `-update` sibling) | Tridium official | **2023-03-23** (event date, filename + page header) | "N4 currently runs on Java 8 which is almost a decade old... Tridium will be migrating it's Java versions and when we migrate Java version it typically comes with a new release." — **discusses the Java-8-EOL migration MOTIVE, names NO target version number** (no "21", no "25" anywhere in either PDF's text) | 2026-09-27 |
| `guides.smartbuildingsacademy.com/tridiumguide` | Third-party training vendor | **"initially published November 9, 2016; updated as of April 15, 2025"** | "**Java 21 Support**: Upgrades from Java 8 to Java 21." | 2026-09-27 |
| `onesight.solutions/tridium-niagara-5-n5-information/` | Third-party partner aggregator | **"February 6, 2025"** | "Since the underlying base for Niagara is moving from JAVA 8 to JAVA 21, it will be up to the module developers to confirm compatibility." | 2026-09-27 (re-verified fresh, matches [B48] §48.3) |
| `docs.forestrock.co.uk/niagara-5-frequently-asked-questions` | Third-party partner aggregator | **"Updated February 12, 2026"** | "the platform is moving from **Java 8 to Java 21**" | 2026-09-27 (re-verified fresh, matches [B48] §48.3) |

All statements `[CERT-web]` (direct quote, URL + access date given). Every Tridium-first-party source that
states a specific version number says **Java 25**, with zero exceptions found across the FAQ, the product
page, and the earlier 2023 Q&A transcript (which names no version at all). Every source that says **Java
21** is third-party, and every one of them carries a date stamp — two clearly BEFORE the FAQ's October 2025
Java-25 statement (April 2025, February 2025), one AFTER it (February 2026).

## 56.2 — Dead-link report (task instruction: report zero-result/failed fetches literally) `[CERT-web]`

Two candidate Tridium-official newsletter PDFs, surfaced by WebSearch as plausible sources for a dated
Java-version mention, both **404'd** on direct `curl` fetch this session:
`https://www.tridium.com/content/dam/tridium/en/documents/document-lists/2024.11.21-Nagara-Newsletter-November-2024.pdf`
and
`https://www.tridium.com/content/dam/tridium/en/documents/document-lists/2025.01.30-Niagara-Newsletter-January-2025.pdf`
— both returned an AEM "404 Resource ... not found: No resource found" HTML body in place of the PDF
`[CERT-web]`, accessed 2026-09-27. Additionally, `web.archive.org` could not be queried at all this
session: the WebFetch tool explicitly refused the URL with "Claude Code is unable to fetch from
web.archive.org" — a **tool restriction**, not a finding about the archive's content; a full Wayback-Machine
crawl for earlier dated snapshots of `tridium.com/.../niagara5` remains a `requires-different-tooling` gap
(§56.7, B56-G1). A `site:tridium.com "Niagara 5" "Java 21"` WebSearch (and a `filetype:pdf` variant)
returned **no genuine tridium.com page containing that exact string** — every hit that surfaced was either
the third-party aggregators above or the FAQ PDF itself (which, per §56.1, says Java 25, not 21); the
search engine's own AI-synthesized summary conflated the FAQ URL with a "Java 21" claim it does not
actually contain — flagged explicitly here as a caution `[INFER]`, consistent with METHODOLOGY's own
warning (quoted in [B48]'s method note) against citing search-engine synthesis as fact without opening the
primary source, which this block did (§56.1's FAQ row is from the locally re-extracted PDF text, not the
search summary).

## 56.3 — B48-G1 resolved: Java 21 is a stale/uncorrected third-party echo, not a genuine Tridium roadmap
reversal — dated evidence now supports (but does not fully prove) the "earlier, superseded" hypothesis `[INFER]`

[B48] §48.3/B48-G1 asked whether the Java-21 statements reflect a genuine earlier Tridium commitment later
revised to Java 25, or are simply wrong. This session's dated source table (§56.1) narrows, without fully
closing, that question:

- **No Tridium-first-party document located at any date states "Java 21"** — not the 2023-03-23 Q&A
  (earliest located first-party discussion of the Java-migration motive, names no version), not the
  2025-04-29 Forum slide deck (silent on Java version entirely), not the 2025-10-27 FAQ (states Java 25
  twice). This is a genuine gap in the positive case for "Tridium once said 21, then changed to 25" — no
  first-party artifact saying 21 was found despite three different first-party documents spanning
  2023-2025 being opened and full-text-searched this session. `[CERT-web]` (absence across three opened,
  full-text-searched first-party PDFs).
- **The third-party dating is consistent with a stale-copy chain, not independent confirmation.**
  `onesight.solutions` (Feb 6, 2025) and `guides.smartbuildingsacademy.com` (Apr 15, 2025) both predate the
  FAQ's Oct 27, 2025 Java-25 statement — consistent with them having captured an EARLIER, non-public-PDF
  Tridium communication (a webinar, a sales conversation, an internal roadmap slide shown to partners) that
  named Java 21, sometime before Feb 2025, which this session could not independently locate as a
  document. `[INFER]`, moderate confidence — plausible but not directly evidenced.
- **`docs.forestrock.co.uk`'s February 2026 stamp is the harder case**, since it POST-dates the FAQ's
  Java-25 statement by ~3.5 months yet still says Java 21, using near-identical phrasing to
  `onesight.solutions`'s February 2025 text ("moving from Java 8 to Java 21" vs. "moving from JAVA 8 to
  JAVA 21"). `[INFER]`, moderate-high confidence: this is evidence the forestrock page's "Updated February
  12, 2026" stamp reflects a site-wide or unrelated-section edit, not a refresh of the Java-version content
  specifically — the two pages' Java sentences are too similar in structure to be independently authored,
  and forestrock's own page was, per [B48] §48.3, already read this session without other evidence it
  cites the FAQ or any Tridium source directly for that claim. A "last updated" stamp on an aggregator page
  is evidence about THAT page's edit history, not evidence every section was re-verified against the
  current Tridium source — a caution worth generalizing beyond this one contradiction.

**Verdict, dated:** `[INFER]`, moderate confidence — the public evidence is consistent with Java 21 having
been an earlier, non-PDF-documented Tridium communication (webinar/partner briefing) sometime before
February 2025, silently superseded by the Java 25 target that is the ONLY version any first-party document
states from April 2025 (silence) through October 2025 (explicit Java 25) onward, with the third-party pages
never revisiting their original text. This session **narrows but does not fully close B48-G1**: no
first-party "Java 21" document was found to directly confirm the reversal (as opposed to a stale echo of an
unlocatable earlier communication). Local corroboration (§56.4) independently confirms Java 25 is what
actually shipped in the 5.0.0.28 beta, which is the strongest evidence for treating Java 25 as authoritative
regardless of the historical-reversal question's final resolution.

## 56.4 — Local corroboration of Java 25 against the installed 5.0.0.28 beta and the devkit's own
requirement doc `[CERT]`/`[CERT-doc]`

### 56.4.1 — Fresh local read this session: the installed beta JRE's own `release` manifest `[CERT]`

`/mnt/c/Program Files/Niagara/5.0.0.28/jre/release` (read directly this session, full file):

```
JAVA_VERSION="25.0.4"
MODULES="java.base ... javafx.base jdk.unsupported javafx.graphics javafx.controls javafx.fxml
         javafx.media jdk.unsupported.desktop javafx.swing jdk.jsobject jdk.xml.dom javafx.web
         jdk.accessibility ..."
```

`[CERT]` — direct read of the bundled JRE's own OpenJDK-standard `release` manifest, this session, real
path under the mounted Windows install. `JAVA_VERSION="25.0.4"` is unambiguous — the installed beta bundles
OpenJDK 25 specifically (matching [B30] §30.4's independent `java -version`-equivalent finding of "OpenJDK
25.0.1" for a DIFFERENT artifact, the devkit toolchain — the two 25.0.x point releases differing slightly is
expected for a JRE bundled at build time vs. a devkit toolchain fetched separately, both still major-version
25). The `MODULES` list additionally contains `javafx.base`, `javafx.controls`, `javafx.fxml`,
`javafx.media`, `javafx.swing`, `javafx.web`, and `jdk.jsobject`/`jfx.incubator.*` — **direct local
confirmation that the shipped JRE bundles JavaFX as system modules**, corroborating §56.4.2's devkit-doc
"Java 25 JDK with JavaFx" requirement from the runtime side, not just the doc side.

### 56.4.2 — Cross-reference (not re-derived): prior blocks already sealed this at `[CERT]`/`[CERT-doc]`
strength

- [Block 25] §25.1/§25.5 and [Block 30] §30.2: **100% of 247-253 module jars in the N5 5.0.0.28 corpus
  compile to class-file major version 69 (= Java SE 25), zero exceptions**, cross-checked against N4's own
  100%-major-52 (Java 8) baseline — `[CERT]`, already sealed, cited by block+section per this block's
  cross-reference convention, not re-read line-by-line this session.
- [Block 2] §2.8: the shipped `docDeveloper.jar!doc/buildN5.html` guide states, as literally the first line
  of its "Getting started" section, *"In order to build Niagara modules, you need a valid Java 25 JDK with
  JavaFx."* — `[CERT-doc]`, already sealed.
- [Block 39] §39.2: the shipped `devkit.jar!rc/gradle.properties.vm` template repeats the same requirement
  programmatically (`org.gradle.java.installations.paths=C:\\JDKS\\java-25-jdk-with-javafx` as its own
  example path) — `[CERT-doc]`, already sealed.

**Verdict: three independent local evidence channels (bundled JRE runtime manifest — newly read this
session; class-file bytecode census — [B25]/[B30]; devkit build-requirement docs — [B2]/[B39]) agree with
each other and with the current first-party public statement (§56.1): the N5 5.0.0.28 beta is Java 25,
unambiguously, with the JavaFX-bundling detail independently confirmed at the runtime-manifest level for
the first time this session.** `[INFER]` (synthesis across the newly-read local file and three prior
sealed blocks) — no local evidence anywhere in this corpus supports a Java 21 target at any point.

## 56.5 — B48-G5 extended: "Niagara Sync" is publicly named and matches the code's license-feature string;
tier/hardware/licensing detail remains unpublished `[CERT-web]`/`[INFER]`

The FAQ PDF's HA question, read in full this session (`/tmp/n5faq.txt:146-148`, matching [B48] §48.10's
prior read exactly, no new text found around it): *"WILL NIAGARA 5 HAVE NIAGARA SYNC/REDUNDANCY/HIGH
AVAILABILITY? High availability remains an important area of focus. The rollout strategy has shifted from
broad general availability to a more limited availability approach first, allowing the offering to be
refined and validated before broader release."* `[CERT-web]` (`N5-FAQ.pdf` p.5, accessed 2026-09-27).

**This is the direct public-to-code reconciliation [B48] §48.10 flagged as unresolved:** the FAQ's question
literally names **"Niagara Sync"** — the exact same name as the shipped beta's `niagaraSync` module and its
license-check string, `Sys.getLicenseManager().getFeature("tridium", "niagaraSync")`, found and fully traced
in [Block 37] §37.7 (`BNiagaraSyncService.java:286-288`). `[INFER]` (naming cross-reference across this
session's public read and [B37]'s prior code-level finding), high confidence — the term "Niagara Sync" is
distinctive enough (not a generic industry term) that independent coinage is implausible; this is the SAME
feature, publicly named and privately license-gated under the identical name.

**What remains unpublished, checked and reported as zero-result this session:**
- No public source (the FAQ, the product page, the Forum-2025 deck, either third-party aggregator) states
  **which license tier, SKU, or price point** "Niagara Sync" belongs to, nor any **hardware requirement**
  for a primary/secondary pair beyond the generic "eligible N4 devices... require active SMA to move to
  Niagara 5" statement already in [B48] §48.2 (which is about the N5 migration eligibility gate generally,
  not niagaraSync specifically). `[CERT-web]`, zero-result, accessed 2026-09-27 (searched
  `"Niagara Sync" license feature availability tier`).
- **A naming-adjacency risk worth flagging, not resolving:** [B48] §48.8 already established that N5's
  OTHER near-term subscription surface — "Niagara Recover" / "Premium Workbench" / Niagara Cloud Suite — is
  a SEPARATE, cloud-hosted, SMA-gated commercial family, publicly marketed and dated back to a 2023/2025
  TridiumTalk trail. "Niagara Sync" (this section) is architecturally distinct per [B37] — an on-station,
  primary/secondary warm-standby REPLICATION protocol, not a cloud service — yet both are described in FAQ
  language using the SAME "limited availability first" / "rollout strategy" framing pattern. `[INFER]`,
  low-moderate confidence: this session found no evidence the two are bundled or licensed together, only
  that Tridium's FAQ prose style for BOTH near-term features uses similar hedged-availability language; a
  reader could conflate them. Filed as a child gap (§56.7, B56-G2), not resolved here.

## 56.6 — Supervisor OS (Windows/Linux) and JACE-9000: no explicit N5 statement found; one indirect signal
`[CERT-web]`/`[INFER]`

**Zero explicit public statement located** on which operating system(s) the Niagara 5 Supervisor will
support. The FAQ PDF's 265-line full text (this session's own fresh extraction) contains **zero occurrences
of "windows" and zero occurrences of "linux"** (`grep -in "windows\|linux"` on `/tmp/n5faq.txt` returned no
hits) `[CERT-web]`, accessed 2026-09-27. WebSearch for `"Niagara 5" Supervisor "operating system"
requirements` likewise surfaced no page stating final N5 Supervisor OS requirements, with the search
synthesis itself noting the information "may not be publicly available yet" given N5's early-access stage
`[CERT-web]`, accessed 2026-09-27.

**One indirect signal, flagged as `[INFER]` only, not overclaimed:** the FAQ's own "KEY FEATURES" list
states *"Flexible MSI installer experience for Supervisors, including support for either side-by-side
installs or upgrade-in-place workflows"* `[CERT-web]` (`N5-FAQ.pdf` p.1, lines 28-29). **MSI (Microsoft
Installer) is a Windows-specific package format** — this is the ONLY installer-format statement anywhere in
the FAQ, and it names no Linux-equivalent packaging (`.deb`/`.rpm`/container image) alongside it. `[INFER]`,
low-moderate confidence: this is consistent with, but does not prove, a Windows-first (or Windows-only at
early-access stage) N5 Supervisor packaging emphasis — N4's own Supervisor has publicly documented Linux
(RHEL) support in prior Niagara 4.10-era datasheets (found via WebSearch this session, not re-verified in
full), so an N5 regression to Windows-only would be a notable product change that this single MSI mention
cannot establish on its own; it is only silent-plus-one-data-point evidence, not a stated policy. Filed as
a child gap (§56.7, B56-G3).

**JACE-9000:** no NEW public statement beyond what [B48] §48.2 already fully quoted (sole eligible N4
controller for N5 migration, region-staggered JACE-8000 ordering wind-down, June 26 2026 license-transfer
window) — this session's fresh FAQ re-read (`/tmp/n5faq.txt:210-220`) confirms the SAME text verbatim,
no drift. `[CERT-web]`, accessed 2026-09-27 — not re-quoted in full here to avoid duplicating [B48]; see
that block's §48.2 for the verbatim text.

## 56.7 — Open questions / contradictions / child gaps

- **[C1] (continued from [B48]).** Java 21 (three third-party sources, dated Feb 2025 / Apr 2025 / Feb
  2026) vs. Java 25 (every first-party source that states a version, Oct 2025 FAQ + product page) —
  narrowed but not closed this session (§56.3): no first-party document at any date was found to state
  "Java 21", so the "genuine roadmap reversal" hypothesis remains `[INFER]`, not `[CERT-web]`-confirmed.
- **[B56-G1]** — A full Wayback Machine crawl of `tridium.com/.../niagara5` and any pre-2025 cached FAQ
  revision, to find whether an earlier PUBLIC (not just partner-aggregator-echoed) Tridium page ever stated
  Java 21 directly — blocked this session by a tool restriction (WebFetch refuses `web.archive.org`; §56.2),
  not by absence of the archive itself. Would fully close B48-G1/[C1] if a dated snapshot is found.
- **[B56-G2]** — Whether "Niagara Sync" (on-station replication, [B37]) and "Niagara Recover"/Niagara Cloud
  Suite (cloud subscription, [B48] §48.8) share any licensing/rollout coupling, or are purely independently
  staged features that happen to share FAQ phrasing — no public source distinguishes or bundles them
  explicitly; worth a targeted follow-up once more N5 licensing documentation is public (post-beta,
  September 2026 per [B48] §48.1).
- **[B56-G3]** — Whether N5 Supervisor will support Linux at GA — the MSI-installer-only FAQ mention
  (§56.6) is a single indirect signal, not a stated policy; re-check once the July 2026 SI Early Access or
  September 2026 beta milestones ([B48] §48.1) produce Supervisor-specific installation documentation.
- **[B56-G4]** — The 2023-03-23 Customer Loyalty Program Q&A's Java-migration discussion (§56.1) was read
  in full for its Java content only; the rest of that transcript (AX-to-N4 licensing migrator demo,
  Q&A on unrelated topics) was not surveyed for other Niagara-5-relevant statements this session — a
  narrow, targeted read, not a full transcript audit.

## 56.8 — Self-verification (METHODOLOGY §11)

- **Token check.** No local `file:line` `[CERT]` citations are newly derived in this block except §56.4.1
  (the freshly-read `release` manifest, quoted verbatim above from the actual file content) — that quote
  was taken directly from this session's own `Read`/`cat`-equivalent of
  `/mnt/c/Program Files/Niagara/5.0.0.28/jre/release`, not hand-recalled. Every `[CERT-web]` claim is
  either a direct quote (marked with quotation marks) from a page/PDF fetched or `curl`+`pdftotext`-
  extracted this session, or a `grep -in` zero-result reported literally (§56.2/§56.5/§56.6). The three PDFs
  central to this block's dating table (`N5-FAQ.pdf`, the Forum-2025 deck, the 2023 Q&A pair) were all
  independently re-`curl`ed and locally text-extracted this session specifically to avoid citing
  WebFetch's lossy PDF summarizer as fact — the Forum-2025 deck's WebFetch summary explicitly FAILED to
  extract readable content ("heavily encoded/compressed... extremely difficult to extract readable text");
  the local `pdftotext -layout` re-extraction succeeded and is what §56.1's zero-Java-mentions finding for
  that deck is based on, not the failed WebFetch summary.
- **Marker tally — mechanically computed, no local `verify-block.sh` target applies to a pure-web block
  (same caveat as [B48] §48.11, restated, not re-litigated). Literal commands run this session against the
  finished file, output pasted verbatim (RAW, whole file, header legend + Type-field boilerplate included,
  no hand rounding):**

  ```
  $ grep -o '\[CERT-hw\]' niagara5-block56.md | wc -l    → 1
  $ grep -o '\[CERT-live\]' niagara5-block56.md | wc -l  → 1
  $ grep -o '\[CERT\]' niagara5-block56.md | wc -l       → 13
  $ grep -o '\[CERT-doc\]' niagara5-block56.md | wc -l   → 9
  $ grep -o '\[CERT-web\]' niagara5-block56.md | wc -l   → 20
  $ grep -o '\[CERT-a\]' niagara5-block56.md | wc -l     → 3
  $ grep -o '\[INFER\]' niagara5-block56.md | wc -l      → 16
  ```

  Ratio `[INFER]`/`[CERT-web]` (dominant marker as denominator, consistent with [B48]'s own pure-web-block
  convention) = 16/20 = **0.80**. This is markedly higher than [B48]'s 0.31, and higher than [B37]'s 0.39 —
  correctly so: this block's own core deliverable (§56.3, §56.5, §56.6) is explicitly a
  DATING/RECONCILIATION synthesis drawn ACROSS [B48]'s and [B37]'s prior findings plus this session's fresh
  reads, not a fresh evidence dump — the elevated ratio is the correct signature of that task shape under
  the declared `mixed` type, not an evidence-exhaustion signal (METHODOLOGY §11's `mixed`-type ratio-
  reading guidance). Adjusted-count note (RAW vs. ADJUSTED, per METHODOLOGY §11): the RAW `[CERT]` (13) and
  `[CERT-doc]` (9) counts include every mention of these markers in the header's marker-legend paragraph
  (quoted once), the Type-field boilerplate (quoted once more), AND every §56.4.2/§56.9 sentence that NAMES
  a prior block's already-sealed `[CERT]`/`[CERT-doc]` finding by cross-reference without re-deriving it —
  those cross-reference mentions are NOT fresh claims of this block's own. The only NEWLY-derived `[CERT]`
  claim in this block's own body is §56.4.1's direct read of the installed beta's `jre/release` manifest;
  every other `[CERT]`/`[CERT-doc]`/`[CERT-hw]`/`[CERT-live]` token is either legend/Type-boilerplate text
  or an explicit cross-reference to [B2]/[B25]/[B30]/[B37]/[B39]'s own prior sealed findings, consistent
  with how this block's header explicitly scopes its own markers ("none newly derived this block" for
  `[CERT]` beyond §56.4.1, "none newly downloaded-and-registered" for `[CERT-doc]`). The three third-party
  aggregator pages (§56.1) are tagged `[CERT-web]`, not `[CERT-a]`, because each was fetched and quoted
  directly this session — matching [B48]'s own convention of reserving `[CERT-a]` for forum/blog/answer-
  style secondary sources, not dated aggregator pages fetched and quoted first-hand; the 3 `[CERT-a]`
  RAW hits above are the legend-line mention only, appearing across the header and Type-field text, zero
  used as an actual claim marker in the body.
  **Caveat, restated from [B48] §48.11:** `toolbelt/verify-block.sh` was **not run** — its citation-
  resolution logic targets this corpus's own `file:line`/artifact-name convention and has no mode for
  auditing external URLs or PDF-extracted quotes; the one local `file:line`-shaped citation in this block
  (`/mnt/c/Program Files/Niagara/5.0.0.28/jre/release`, §56.4.1) is a path OUTSIDE this git-tracked corpus
  (a mounted Windows install directory), so it would resolve as unverifiable-external to the script
  regardless — flagged explicitly rather than silently omitted, per the decompiled-tree convention's own
  instruction.
- **Zero/failed searches and fetches reported as data (task instruction).** `site:tridium.com "Niagara 5"
  "Java 21"` (§56.2, no genuine tridium.com hit containing that string) · `"Niagara 5" "Java 21" 2024
  announcement OR roadmap OR webinar` (§56.1, no NEW first-party source beyond the three already found) ·
  `Tridium Niagara 5 "Niagara Sync" license feature availability tier` (§56.5, zero-result) · `"Niagara 5"
  Supervisor "operating system" requirements Tridium 2026` (§56.6, zero-result, search engine itself noted
  the info likely isn't public yet) · two dead-link PDF fetches, both 404 (§56.2) · one refused fetch,
  `web.archive.org`, tool-level restriction not a content finding (§56.2) · zero "java" occurrences in the
  Forum-2025 deck's full extracted text (§56.1) · zero "windows"/"linux" occurrences in the FAQ's full
  extracted text (§56.6).
- **Artifacts.** Block file written at `/home/cristian/niagara5-research/niagara5-block56.md` only, per the
  task's explicit instruction not to touch `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`/any other file. The
  five PDFs fetched and locally extracted this session (`N5-FAQ.pdf`, the Forum-2025 deck, the two 2023 Q&A
  variants) were saved to `/tmp` and the session's own WebFetch tool-results scratch area, not the corpus
  `sources/` tree — same scope decision as [B48] §48.11, restated here rather than silently deviating.
- **MCP-doc snapshots.** N/A — no context7/MCP-doc citation used; all citations are `curl`+`pdftotext`,
  WebFetch/WebSearch, or a direct local file read.

## 56.9 — Connections

- **[Block 48]** — this block is a direct dating/reconciliation follow-up to two of its named child gaps:
  §56.1-§56.3 narrow (not fully close) **B48-G1** (the Java-21-vs-25 contradiction) with a dated seven-row
  source table and the finding that no first-party document at any date states Java 21; §56.5 extends
  **B48-G5** (the HA "limited availability first" framing) by making the public-to-code naming link (FAQ's
  "Niagara Sync" question = [B37]'s `niagaraSync` module/license string) explicit for the first time.
- **[Block 37]** — §56.5 is the direct public-evidence counterpart to [B37] §37.7's code-level
  `tridium:niagaraSync` license-feature finding: this block confirms Tridium publicly uses the exact same
  name in its FAQ, closing the naming half of the gap while leaving the tier/hardware/licensing-detail half
  open (B56-G2).
- **[Block 25]/[Block 30]** — §56.4.1's freshly-read local JRE `release` manifest (`JAVA_VERSION="25.0.4"`)
  is a THIRD independent local evidence channel (after their own class-file major-version census) agreeing
  on Java 25, now including the JavaFX-bundling detail at the runtime-manifest level.
- **[Block 2]/[Block 39]** — §56.4.2 cross-references their prior `[CERT-doc]` devkit-requirement findings
  ("Java 25 JDK with JavaFx") as the third corroborating channel alongside §56.4.1's fresh runtime-manifest
  read and [B25]/[B30]'s bytecode census — all three now independently agree.
