# Block 48 — Public evidence on Niagara 5: breaking changes, retired modules and cloud/licensing statements

> Research of **PUBLIC web evidence about Niagara 5** (release/GA schedule, hardware support, Java
> version, breaking changes, module signing, retired/absent modules, cloud-connector and
> licensing/subscription statements), collected read-only via WebSearch/WebFetch and diffed against three
> prior local-corpus findings: [B10]'s 32-row breaking-changes table and its child gap **B10-G2** (the
> external "Niagara 5.0 Breaking Changes" page `upgradingToN5.html` cross-references but does not embed),
> [B13]'s 49-module "zero N5 package overlap" list and its child gap **B13-G1** (genuine removal vs.
> beta-only omission), and [B42]'s `nCloudDriver` migration-fate finding and its child gap **B42-G4** (an
> authoritative Tridium statement on `nCloudDriver`'s retirement). Also corroborates [B6]/[B34]'s
> code-derived subscription-licensing findings against public statements. Does **not** cover: any content
> behind Tridium's Developer Program login or the `docs.niagara-community.com` authenticated portal (found
> gated, not fetched — see §48.5); a live N5 GA build (does not exist publicly as of this session); or a
> systematic per-module public search for all 49 §13.4.4(d-2) names (a representative sample was searched,
> not all 49 — see §48.6).
>
> Subject version: **not applicable in the usual sense** — this block's subject is the public web as it
> stood on the access date below, not a fixed software artifact. Where a source itself carries an internal
> version/date stamp (e.g. the Tridium FAQ PDF's own "Updated October 27, 2025" header), that stamp is
> quoted verbatim and used to resolve contradictions between sources of different freshness (§48.3, §48.9).
> Access date for every `[CERT-web]` citation in this block: **2026-09-27**.
>
> Sources: `https://pages1.tridium.com/rs/808-SGM-271/images/N5-FAQ.pdf` (Tridium official, PDF
> content-stamped "Frequently Asked Questions Updated October 27, 2025") · `https://www.tridium.com/us/en/Products/niagara/niagara5`
> (Tridium official product page) · `https://www.tridium.com/content/dam/tridium/en/documents/document-lists/jace/tri-jace9000-faq-en-2025-0007.pdf`
> (Tridium official, doc code 2025-0007, branded "niagara4" — pre-N5 JACE-9000 FAQ) ·
> `https://www.tridium.com/us/en/Products/niagara-cloud-suite` and `.../niagara-cloud-suite/niagara-data-service`
> (Tridium official product pages) · `https://www.tridium.com/us/en/services-support/events/2025/09/2025-09-25-containerized-niagara`
> (Tridium official event page, dated 2025-09-25) · `https://docs.forestrock.co.uk/niagara-5-frequently-asked-questions`
> (third-party partner aggregator, page stamped "February 12, 2026") · `https://onesight.solutions/tridium-niagara-5-n5-information/`
> (third-party partner aggregator, page stamped "February 6, 2025") · `https://docs.niagara-community.com/`
> (Tridium documentation portal — confirmed login-gated, no content read). Every URL was fetched this
> session via WebFetch/WebSearch; the two official Tridium PDFs were additionally downloaded and read
> page-by-page (8 pages + 2 pages respectively) to eliminate WebFetch's lossy PDF-to-markdown summarization.
>
> Method: targeted WebSearch queries per the assigned gap list, WebFetch/PDF full-read on every
> promising hit, cross-diff of extracted facts against [B10]'s §10.4 table, [B13]'s §13.4.4(d-2) list, and
> [B42]'s §42.8 finding. Every claim below is tagged `[CERT-web]` (WebFetch/WebSearch-derived, quoted or
> closely paraphrased from the source, URL + access date given) or `[INFER]` (this block's own synthesis
> across sources/prior blocks). No `[CERT]`/`[CERT-doc]` markers apply — no local file or downloaded
> artifact was read; only live web content.
>
> Public-evidence layer. Connects [B10] (§48.3–§48.5 diff its breaking-changes table and close/narrow
> B10-G2), [B13] (§48.6 addresses B13-G1), [B42] (§48.7 addresses B42-G4), [B6]/[B34] (§48.8 corroborates
> the subscription-licensing code findings with public statements).
>
> **Type:** `mixed` — §48.1/§48.2/§48.7/§48.8/§48.9 are evidence sections citing only this session's web
> reads; §48.3/§48.4/§48.5/§48.6 draw `[INFER]` conclusions by diffing this session's web evidence AGAINST
> prior blocks' ([B10]/[B13]/[B42]) own findings, the declared trigger for `mixed` per METHODOLOGY §4.

---

## 48.1 — Niagara 5 official release schedule: GA target is December 2026, not late 2025 `[CERT-web]`

The Tridium-official FAQ PDF (content-stamped "Updated October 27, 2025") states the schedule as of that
stamp date: *"N5 is currently in Early Access for active Niagara Developer Partners to support Java 25 and
code migration readiness. Broader Early Access for system integrators and other non-developer participants
is planned for July 2026, followed by beta in September 2026 and targeted general availability in December
2026."* `[CERT-web]` (`N5-FAQ.pdf` p.3, accessed 2026-09-27). The same document's front-page availability
schedule repeats this: "Now" = Developer Partner Program early access; July 2026 (planned) = SI early
access + NURIO bench testing; September 2026 (planned) = beta program (real-world deployment); December
2026 (target) = "Niagara 5.0 general availability" `[CERT-web]` (`N5-FAQ.pdf` p.1). The official
`tridium.com/us/en/Products/niagara/niagara5` product page corroborates the same three near-term
milestones (January 2026 Developer Alpha, July 2026 SI Early Access, September 2026 beta program)
`[CERT-web]` (accessed 2026-09-27).

Niagara 4.15 is Tridium's declared **Long-Term Support (LTS)** release and "is expected to remain
supported through 2028, including ongoing security maintenance," continuing to receive updates "through
Q3 of 2028" `[CERT-web]` (`N5-FAQ.pdf` p.3).

## 48.2 — Hardware: JACE-9000 is the sole eligible N5 platform; JACE-8000 is explicitly excluded `[CERT-web]`

Direct FAQ answer, quoted verbatim: *"WILL THE JACE-8000 BE UPGRADABLE TO NIAGARA 5? No, The JACE-8000 was
able to transition from AX to N4, and the JACE-9000 can transition from N4 to N5."* `[CERT-web]`
(`N5-FAQ.pdf` p.7). A time-limited mitigation exists: *"For a limited time, through June 26, 2026, ... a
JACE 8000 license with active maintenance can be transferred to a JACE 9000 by paying just a
license-transfer fee, rather than the full cost of a new JACE 9000 license"* `[CERT-web]` (same page).
JACE-8000 ordering itself is winding down on a region-staggered schedule: closed in Europe 2025-12-31,
closing 2026-12-31 in Americas/MEA/APAC, while "The JACE-9000 with an N4 license is expected to remain
available to be ordered through the planned EOL of Niagara 4 in 2028" `[CERT-web]` (same page). Eligibility
is gated on active SMA: *"Eligible N4 devices, including Supervisors and JACE-9000, will require active
SMA to move to Niagara 5"* `[CERT-web]` (`N5-FAQ.pdf` p.5).

Third-party controller manufacturers ("portability partners") get a non-committal answer: *"To learn about
a specific controller, reach out to the manufacturer for eligibility and timing"* `[CERT-web]` (`N5-FAQ.pdf`
p.7) — no public per-vendor N5 hardware list exists yet.

## 48.3 — Java version: officially Java 25 (Tridium primary sources), but third-party aggregator pages
publicly state Java 21 — a genuine, dated public contradiction `[CERT-web]`

Both Tridium-first-party sources this session read state **Java 25** explicitly and repeatedly: the FAQ
PDF's own release-timeline answer ("N5 is currently in Early Access for active Niagara Developer Partners
to support **Java 25**...") and its development-section answer ("Because Niagara 5 moves from **Java 8 to
Java 25** and includes platform changes...") `[CERT-web]` (`N5-FAQ.pdf` pp.3–4); the official product page
states N5 is "Built on Java 25" `[CERT-web]` (`tridium.com/.../niagara5`, accessed 2026-09-27). This
independently corroborates [B10]'s own code-derived reading of the shipped `5.0.0.28` beta doc corpus
(`upgradingJDK.html`, "all devices... now run full JDK 25 Standard Edition" — B10 §10.5) — the public
statement and the local `[CERT-doc]` finding agree on the JDK target version.

However, **both third-party partner-aggregator pages read this session state Java 21, not Java 25**:
`docs.forestrock.co.uk/niagara-5-frequently-asked-questions` (page self-stamped "February 12, 2026")
states *"Moving from Java 8 to Java 21, requiring all modules to be refactored for compatibility"*
`[CERT-web]`; `onesight.solutions/tridium-niagara-5-n5-information/` (page self-stamped "February 6, 2025")
states *"Niagara 5 upgrades from Java 8 to 'JAVA 21'"* `[CERT-web]`. **Open contradiction, recorded here
and pushed to the corpus-level `CONTRADICTIONS.md` per METHODOLOGY §14** — see §48.10. `[INFER]`, moderate
confidence: the two third-party pages are likely quoting an EARLIER, now-superseded internal Tridium
roadmap slide/announcement (Java 21 was the current LTS release at the time N5 planning first became
public, before Java 25's September 2025 LTS release), and neither page shows evidence of being refreshed
after Tridium's own public Java-25 statements. The Tridium-first-party FAQ PDF is the more authoritative
and more recently content-stamped source (2025-10-27) and is preferred per METHODOLOGY §3's live/official
ranking (`[CERT-web]` official > `[CERT-web]`/`[CERT-a]` third-party aggregator, and freshness is itself
part of that ranking for a moving target). This block does **not** resolve which Java LTS was targeted at
an earlier planning stage — only that the CURRENT public and the CURRENT internal-doc statement agree on
Java 25.

## 48.4 — Diff against [B10]'s 32-row breaking-changes table: no new item found, three items publicly
corroborated `[CERT-web]`/`[INFER]`

No public source read this session names a breaking change absent from [B10]'s §10.4 table (BC-01..BC-32).
Three of B10's rows are independently corroborated by public statements:

| B10 row | B10's local (`[CERT-doc]`) claim | Public corroboration this session |
|---|---|---|
| BC-21 (Security Manager removed) | Java 25 removes AccessController/PrivilegedAction; `niagara.nre.util.SecurityUtil` replaces it | FAQ PDF: module-signing Q&A frames the change generically as a "stronger software integrity and security posture" without naming `SecurityUtil` — directionally consistent, no contradiction `[CERT-web]` (`N5-FAQ.pdf` p.4) |
| (new, not in B10) — mandatory module signing | B10's BC-21 covers the *permission-annotation* mechanics but does not itself assert signing is now *mandatory for every module* as a headline feature | FAQ PDF, verbatim: *"WILL N5 MODULES REQUIRE A SIGNATURE TO BE LOADED INTO A N5 STATION? Yes. Niagara 5 introduces module signing requirements as part of a stronger software integrity and security posture."* `[CERT-web]` (`N5-FAQ.pdf` p.4) — this is a genuine **addition** to B10's picture: B10 documented the permission-annotation replacement mechanics from the doc jar, but did not surface a standalone "signing is now mandatory, no exceptions" public policy statement. Filed as a note, not a new BC-row (same underlying change, different framing) |
| BC-28 (new Configuration Home, directory reshuffle) | new `~~` config-home tier, directories moved | No public source this session names directory paths; not contradicted, simply unaddressed publicly |
| (context) UI theme changes | BC-11/BC-31/BC-32 (bajaui paint/layout signatures, UxModel/BindingList deletion, `Array#contains` removal) | FAQ PDF corroborates at a product-marketing level only: Lucid/Zebra themes "remain available to support Px migration" but "will not be optimized for Niagara 5 enhancements," and N5 "introduce[s] updated navigation, layout, and new themes, including light and dark modes" `[CERT-web]` (`N5-FAQ.pdf` p.5) — consistent with, but far less detailed than, B10's NSS2/`IRenderContextAware` findings (B10 §10.6) |

**No breaking change was found publicly that contradicts B10's table.** `[INFER]` — this is consistent with
B10's table being reasonably complete for the publicly-marketed subset; the FAQ is a sales/readiness
document, not an engineering changelog, so its silence on most of B10's 32 rows is expected (its own
purpose is migration planning, not an API diff) rather than evidence those rows are wrong.

## 48.5 — B10-G2 narrowed, not closed: the "Niagara 5.0 Breaking Changes" page is real but login-gated `[CERT-web]`

[B10]'s child gap B10-G2 asked whether the doc-jar's cross-referenced "Niagara 5.0 Breaking Changes" page
is a separate public web document. This session did **not** locate that page as an openly-indexed public
URL — every WebSearch query for the exact phrase `"Niagara 5.0 Breaking Changes"` returned only this
research corpus's own file (github.com/angeles725/... hits, excluded) or unrelated results (Niagara 4.8
breaking-changes PDF, Unreal Engine's unrelated "Niagara" VFX system, generic changelog pages). Zero
on-topic hits for the literal query `"Niagara 5.0 Breaking Changes"` `[CERT-web]` (WebSearch, this session,
accessed 2026-09-27 — reported as data per task instructions, not absence of trying).

However, this session confirmed the STRUCTURAL reason: Tridium's documentation portal
`docs.niagara-community.com` — the natural home for a page cross-referenced from inside the shipped
`docDeveloper.jar` — is **login-gated**. WebFetch of the bare portal root returned a login interface
("Tridium Documentation - Best Practice Portal," Zoomin-powered, "Users must authenticate via the login
system to access actual documentation content") with zero visible Niagara 5 breaking-changes content
`[CERT-web]` (`docs.niagara-community.com`, accessed 2026-09-27). This corroborates the earlier public
finding that Developer Program membership grants "dedicated access to developer documentation" `[CERT-web]`
(WebSearch summary of `tridium.com/us/en/purchase/developer-program`, accessed 2026-09-27) — i.e., the full
breaking-changes list most plausibly lives inside this gated portal, consistent with (not contradicting)
B10's own reading that the doc jar names it as an external cross-reference without embedding it.
**Verdict: B10-G2 is narrowed from "find the page" to "the page is gated behind Developer Program /
niagara-community.com login, not publicly indexed"** `[INFER]`, moderate confidence (a structural
explanation for an absence, not a direct read of the gated page itself — genuinely closing B10-G2 would
require Developer Program credentials, out of this block's read-only public-web scope).

## 48.6 — B13-G1: the 49 "zero N5 package overlap" modules have no public removal/retention record `[CERT-web]`

[B13] §13.4.4(d-2) listed 49 Tridium-vendor N4 modules (`electronicSignature`, the seven old cloud-stack
modules including `nCloudDriver`, `knxnetIp`, `gauth`, `snmp`, `micros`/`opc`/`openAdr`/`ndio`/`mobile`,
the `fc*` family, `platPower`/`platNdio`/`platSerialQnx`, the BACnet trio, `boxAnalyzer`/`rdbOracle`,
`kitPxBuilding`, the seven `platHwScanJ*` variants, six migrator utilities, and two resource-only modules)
with zero `.class` package overlap against the N5 5.0.0.28 beta install. This session ran representative
public-web checks against a sample of the most distinctive/searchable names:

| Query (literal) | Result |
|---|---|
| `"Niagara 5" removed module OR discontinued "nCloudDriver" OR "electronicSignature" OR "cloudSentienceConnector"` | No on-topic hit naming any of these three as removed/retired in N5; the only substantive hit was an N4-era Niagara Cloud release-note snippet unrelated to N5 `[CERT-web]`, accessed 2026-09-27 |
| `"electronicSignature" module Niagara Tridium removed N5` | Zero on-topic hits; search-engine synthesis explicitly states it could not confirm the claim `[CERT-web]`, accessed 2026-09-27 |
| `Niagara "app module" removed "mobile app" Niagara 5` | Zero on-topic hits across four query reformulations attempted by the search tool (mostly returned an unrelated consumer Android app called "Niagara Launcher") `[CERT-web]`, accessed 2026-09-27 |

**No public source this session confirms or refutes removal-vs-beta-omission for any of the 49 named
modules.** `[INFER]` — this is itself informative: these are internal/legacy Tridium module names with no
independent public documentation trail (unlike, say, `app`, which B13 §13.4.1 already found named
explicitly in the shipped doc jar). **B13-G1 remains OPEN**; closing it would require either an N5 GA
build (not yet released — §48.1) or Developer-Program-gated release notes (§48.5's same access barrier).
This session's contribution is narrowing the search space: the public web carries essentially zero
independent signal on these 49 names, so B13-G1's eventual resolution will have to come from a live N5
install census (a `requires-execution` child gap, consistent with B13's own framing) rather than further
web research.

## 48.7 — B42-G4: no authoritative public statement on `nCloudDriver`'s N5 fate; N4-era docs still active `[CERT-web]`

[B42] §42.8 found `[INFER]`-level evidence (absent module + absent migrator-converter registration) that
N4's `nCloudDriver` was retired without a migration path, but flagged that no official Tridium
migration-guide/release-note statement had been located (B42-G4). This session's targeted search
(`Honeywell Sentience nCloudDriver retired Forge cloud`, `nCloudDriver Niagara 5 retired`) found:

- **No Niagara-5-specific statement exists publicly** about `nCloudDriver`'s status, one way or the other
  `[CERT-web]`, accessed 2026-09-27.
- `nCloudDriver`/the Sentience cloud connector is still **actively documented as an N4-era component** in
  material dated as recently as August 2025: a "Niagara Cloud Backup as a Service" technical document
  (hosted via `downloads.onesight.solutions`, dated 2025-08-07) references `CloudConnector_Sentience
  nCloudDriver` as supporting "the Niagara Cloud" `[CERT-web]`, accessed 2026-09-27. Honeywell's own product
  page for "N4 to Sentience Cloud" (`buildings.honeywell.com/.../n4-to-sentience-cloud`) is live and
  describes N4-generation engineering tooling for the Sentience cloud `[CERT-web]`, accessed 2026-09-27 —
  no N5 mention on that page.
- Honeywell Forge (the current branding) is confirmed publicly as "a reboot version of the 'Sentience'
  platform which was launched by the company in 2017" `[CERT-web]` (WebSearch synthesis of
  `honeywell.com/us/en/solutions/honeywell-forge` and related pages), consistent with B42's own reading
  that `cloudLinkForge`/`cloudLinkHonSbp` are the N5-era, differently-architected successors — but this is
  branding-history corroboration, not a stated migration/retirement decision for `nCloudDriver` itself.

**Verdict: B42-G4 remains OPEN.** `[INFER]`: the absence of any N5-specific nCloudDriver statement,
combined with nCloudDriver's Sentience/N4 documentation still being actively maintained as of August 2025
(i.e., Tridium/Honeywell have not yet published an N4 sunset notice for it either), is consistent with
B42's own reading that this is simply undocumented territory rather than a confirmed migration path this
session missed. No stronger conclusion is supportable from public evidence alone.

## 48.8 — Licensing/subscription public statements corroborate [B6]/[B34]: subscription licensing predates
N5 and is publicly documented as an existing Niagara Cloud Suite mechanism `[CERT-web]`

[B6] §6.2 corrected an earlier framing to establish that `com.tridium.sys.license.subscription` is **not
new to N5** — the package exists unchanged from N4. [B34] then fully mapped the `nre.jar`
subscription-entitlement client (`com.tridium.nre.subscription`) as an existing N4/N5-shared bootstrap.
Public evidence this session corroborates that subscription licensing is a real, publicly-marketed,
pre-existing Tridium commercial mechanism, not an N5 invention:

- **Niagara Cloud Suite** is Tridium's existing subscription product family. Its official product page
  states Niagara Recover, Niagara Remote, and **Niagara Data Service** require "an active Niagara Software
  Maintenance Agreement (SMA)" `[CERT-web]` (`tridium.com/.../niagara-cloud-suite/niagara-data-service`,
  accessed 2026-09-27) — an SMA-gated subscription model, consistent with B34's finding of an
  entitlement-check client tied to license/SMA state.
- Tridium ran a public **"TridiumTalk: Niagara 4.13 Feature Preview – Containerized Niagara and
  Subscription Licensing"** event in 2023, and a follow-up **"TridiumTalk: Containerized Niagara and
  Subscription Licensing Update"** on **2025-09-25** `[CERT-web]` (`tridium.com/us/en/services-support/
  events/2025/09/2025-09-25-containerized-niagara`, accessed 2026-09-27). The 2025 event page, read in
  full this session, describes containerized Niagara's subscription model explicitly as a "CapEx to OpEx"
  shift, "Software-as-a-Service"-style, with Docker delivery (AMD x86 + ARM64), File Domain Auth / Native
  Domain Auth, and a documented "registration, backup, and unregistration" workflow `[CERT-web]` (same
  page). **This event page makes no mention of Niagara 5** — the subscription-licensing mechanism it
  describes is framed purely around N4's containerized offering, publicly confirming B6's "not new to N5"
  correction from the opposite direction (public marketing already treated subscription licensing as an
  N4-era feature well before N5 existed).
- The N5 FAQ PDF's own "KEY FEATURES" list frames N5's cloud/subscription angle as an *extension* of this
  existing model, not a new one: "Expanded lifecycle management value for hosts **subscribed to Niagara
  Recover**, including Remote Software Manager eligibility" and "Workbench packaging is evolving... including
  a **Premium** option for expanded remote and cloud-enabled capabilities" `[CERT-web]` (`N5-FAQ.pdf` pp.1–2)
  — i.e., N5 adds a new Premium Workbench subscription tier on top of the pre-existing Niagara Cloud Suite
  subscription infrastructure that B6/B34 already found in the code, rather than introducing subscription
  licensing as a concept.

**Verdict: public evidence fully corroborates B6 §6.2's correction and gives B34's code-level subscription
client a public commercial home (Niagara Cloud Suite / SMA-gated services / containerized Niagara).**
`[INFER]` (synthesis across this session's sources and B6/B34's prior code-level findings) — no public
source states the specific `EntitlementApi`/`SubscriptionLicenseUtil` class names B34 found (expected;
those are internal implementation details, not marketing content).

## 48.9 — N5 beta program and the `5.0.0.28` build number: publicly unconfirmed, consistent with a
Developer-Program-only pre-release build `[CERT-web]`/`[INFER]`

No public source read this session names a `5.0.0.x` build number for Niagara 5 — not the FAQ PDF, not the
product page, not either third-party aggregator. WebSearch for the literal string `"Niagara 5.0.0.28
beta"` returned no on-topic hit beyond this research corpus's own GitHub artifacts (excluded as
self-referential) `[CERT-web]`, accessed 2026-09-27. This is consistent with, not contradicting, the
official schedule in §48.1: as of the FAQ's 2025-10-27 stamp, the ONLY publicly-acknowledged N5 access
tier is Developer Partner Program early access ("Now"); the broader September-2026 "beta program" is
explicitly future-dated, so a build numbered `5.0.0.28` accessed and read locally by [B1]–[B47] of this
corpus is plausibly a Developer-Program-internal build, not the eventual public beta artifact — its
internal "(Beta)" self-label (per [B10]'s header) is Tridium's own internal build-channel naming, not
evidence of public beta-program membership. `[INFER]`, moderate confidence — this block cannot verify the
local install's provenance beyond what [B1]'s own census already established; it only confirms no public
web source independently corroborates or contradicts that build number.

## 48.10 — Open questions / contradictions / child gaps

- **[C1]** Java 21 (third-party: `docs.forestrock.co.uk` "Feb 12, 2026", `onesight.solutions` "Feb 6, 2025")
  `[CERT-web]` vs. Java 25 (Tridium official FAQ PDF "Oct 27, 2025" + official product page) `[CERT-web]` —
  unresolved which is stale vs. current; pushed to corpus `CONTRADICTIONS.md` (§14). This block treats
  Java 25 as authoritative per source-freshness + first-party ranking (§48.3) but does not erase the
  discrepancy.
- **[B48-G1]** Confirm whether the Java-21-vs-25 discrepancy (§48.3/[C1]) reflects a genuine Tridium
  roadmap change (an earlier public commitment to Java 21, later revised to Java 25) — would require
  locating an earlier-dated Tridium-first-party statement (press release, Niagara Summit deck, or an
  earlier FAQ PDF revision) naming Java 21 explicitly; none was found this session, only third-party pages
  that do not cite their own primary source.
- **[B48-G2]** Read the full content of `docs.niagara-community.com`'s Niagara 5 / breaking-changes section
  under Developer Program credentials (out of this session's public-web-only scope) — the only path
  remaining to fully close B10-G2.
- **[B48-G3]** Re-run a systematic (not sampled) public-web check for all 49 §13.4.4(d-2) module names once
  N5 reaches beta (September 2026 per §48.1) or GA (December 2026) — a live install census or a published
  N5 module list at that point would let B13-G1 be closed definitively; this session's zero-result public
  search (§48.6) is a snapshot, not a proof of permanent absence.
- **[B48-G4]** Monitor for a post-GA Tridium migration-guide or release-note statement specifically naming
  `nCloudDriver`'s fate (B42-G4) — none exists pre-GA; Tridium's migration documentation cadence (per
  §48.1's schedule) suggests fuller migration guides are more likely to appear around the July 2026 SI
  Early Access or September 2026 beta milestones, not before.
- **[B48-G5]** The FAQ PDF's High-Availability answer ("The rollout strategy has shifted from broad general
  availability to a more limited availability approach first") implies Niagara Sync/redundancy support in
  N5 is being intentionally staged/limited at GA `[CERT-web]` (`N5-FAQ.pdf` p.5) — this appears to extend
  [B13]'s own `niagaraSync`/`B5-G3` thread (a new `BINiagaraSyncCapableComplex` on status types, §13.5) with
  a product-strategy signal not derivable from the module inventory alone; worth cross-referencing in a
  future [B5]/[B13] follow-up, not resolved here.

## 48.11 — Self-verification (METHODOLOGY §11)

- **Token check.** This block cites no local `file:line` or archived-artifact tokens — every citation is a
  URL + access date (`[CERT-web]`) or this block's own `[INFER]` synthesis. `verify-block.sh`'s citation
  gate is therefore not applicable in its usual `file:line`-resolution sense; the equivalent discipline
  applied here is that every `[CERT-web]` claim above is either a direct quote (marked with quotation
  marks) or a closely-paraphrased fact traceable to the named URL, and the two official PDFs were read in
  full (8 + 2 pages) rather than relied on via WebFetch's lossy summarization alone, specifically to avoid
  citing a search-engine hallucination as fact.
- **Marker tally — mechanically computed, no local `verify-block.sh` target applies to a pure-web block;
  see note below.** Literal command run this session: `grep -o '\[CERT-web\]' niagara5-block48.md | wc -l`
  → **51**; `grep -o '\[INFER\]' niagara5-block48.md | wc -l` → **16** (RAW, whole file, header legend and
  template boilerplate included — no adjusted/stripped count taken). Ratio `[INFER]`/`[CERT-web]` = 16/51 ≈
  **0.31** — moderate, expected for a `mixed`-type block per
  METHODOLOGY §11 (this block both reports raw web evidence AND draws cross-block synthesis against
  [B10]/[B13]/[B42]/[B6]/[B34]'s prior findings in nearly every section).
  **Caveat, stated explicitly per METHODOLOGY §11's "mechanize the counting" rule:** `toolbelt/verify-block.sh`
  was **not run** against this file. The script's citation-resolution logic is built around this corpus's
  own `file:line`/artifact-name convention and has no mode for auditing external URLs; running it would
  correctly report "ZERO file:line citations resolved" for a reason the script cannot distinguish from a
  decompiled-tree block (METHODOLOGY §11's own decompiled-tree caveat) — but the TRUE reason here is "no
  local citations exist by design, this is a pure public-web block." This is flagged explicitly, per the
  decompiled-tree convention's own instruction, rather than silently omitting the tool-run line.
- **Zero/failed searches reported as data (task instruction).** Literal queries that returned no on-topic
  result this session: `"Niagara 5.0 Breaking Changes"` (§48.5); `"Niagara 5.0.0.28 beta"` narrowly
  construed as a public build reference (§48.9); `"electronicSignature" module Niagara Tridium removed N5`
  (§48.6); `Niagara "app module" removed "mobile app" Niagara 5` (§48.6); `"Niagara 5" removed module OR
  discontinued "nCloudDriver" OR "electronicSignature" OR "cloudSentienceConnector"` returned only
  tangential N4-era hits, no on-topic N5 removal confirmation (§48.6/§48.7).
- **Artifacts.** Block file written at `/home/cristian/niagara5-research/niagara5-block48.md` only, per
  the task's explicit instruction not to touch `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md`/any other file.
  The two official Tridium PDFs fetched this session were saved by the WebFetch tool to this session's own
  scratch/tool-results area (not the corpus `sources/` tree, since this block's task scope did not include
  corpus-source preservation) — their content is fully quoted/paraphrased inline above so the block remains
  self-contained even if those transient files are not retained.
- **MCP-doc snapshots.** N/A — no context7/MCP-doc citation used; all citations are plain WebSearch/WebFetch.

## 48.12 — Connections

- **[Block 10]** — §48.1–§48.5 diff this session's public evidence against B10's §10.4 32-row
  breaking-changes table and its child gap B10-G2; no contradiction found, one narrowing (B10-G2's target
  page is real but login-gated, §48.5), one minor addition (mandatory module-signing as a headline public
  policy statement, §48.4).
- **[Block 13]** — §48.6 directly addresses B13-G1 (the 49 zero-package-overlap modules); verdict is that
  public web evidence is essentially silent on all of them, narrowing the search space rather than
  resolving the gap, and pointing back to B13's own conclusion that a live N5 install census is the only
  path to resolution.
- **[Block 42]** — §48.7 directly addresses B42-G4 (`nCloudDriver`'s authoritative migration-fate
  statement); verdict is the gap remains open, with corroborating evidence that nCloudDriver/Sentience
  documentation is still N4-era-active as of August 2025, i.e., no sunset has been announced on either
  side of the migration.
- **[Block 6]** — §48.8 corroborates B6 §6.2's "subscription package is not new to N5" correction with a
  2023/2025 public TridiumTalk event trail showing subscription licensing was already an N4-era
  commercial feature (containerized Niagara) before N5 existed.
- **[Block 34]** — §48.8 gives B34's code-level `nre.jar` subscription-entitlement client a public
  commercial home: Niagara Cloud Suite's SMA-gated services (Niagara Recover, Niagara Remote, Niagara Data
  Service) and the containerized-Niagara subscription offering.
