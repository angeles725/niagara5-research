# Block 64 — Fresh 2026 Tridium sources close B28-G1 (`test-wb`→`test`), name two concrete BACnet casualties for B13-G1, and locate (but cannot pass) the login gate behind B10-G2's canonical Breaking-Changes list

> Research closing/narrowing **five** named child gaps by pairing a fresh re-read of this install's own
> shipped doc (`docDeveloper.jar`) against **external Tridium sources located and fetched this session**:
> **B10-G2** (locate the full "Niagara 5.0 Breaking Changes" list and diff it against [Block 10] §10.4's
> 32-row table — [Block 10] itself only quoted the doc's own forward-reference sentence, `[external
> cross-reference doc, not shipped in this jar]`, without resolving the actual hyperlink target); **B13-G1**
> (the 49 Tridium-vendor code modules [Block 13] §13.4.4(d-2) found with zero N5 package overlap and no
> removal/merge evidence — classify against web docs/release notes); **B13-G3** (the 59 doc-guide jars
> [Block 13] §13.4.4(d-1) found unmatched inside `docDeveloper.jar` — resolve against the official Tridium
> web doc portal); **B28-G1** (whether N4's `:test-wb` module-test dependency — used by CompPan-rt's and
> DashboardPan's `moduleTestImplementation` — exists under a different N5 name or was genuinely dropped;
> [Block 28] §28.9.G confirmed only that no `test-wb.jar` exists on disk, never exercised as a build
> failure); **B42-G4** (an authoritative Tridium statement on N4's `nCloudDriver` retirement — [Block 42]
> §42.8 found only a documented-team-practice-plus-clean-absence `[INFER]`, no positive statement, and
> named finding it as out-of-scope local-corpus work requiring "external/web sourcing"). Covers: a fresh
> `zipfile`-level re-open of `doc/upgrade/upgradingToN5.html` (same file [Block 10] read, re-opened this
> session specifically to extract its `<a href>` target for the "Niagara 5.0 Breaking Changes" cross-
> reference, which [Block 10] left unresolved); `curl`/WebFetch probes of that resolved URL and an
> `archive.org` availability check; a local `test.jar`/`niagaraTest.jar` `module.xml` + zip-namelist read
> (fresh this session, not reused from [Block 16]/[Block 28]); and WebSearch/WebFetch retrieval + `pdftotext`
> extraction of five external Tridium PDF documents (§64.0 table below) never opened by any prior block in
> either corpus. Does **not** cover: obtaining `niagara-community.com` login credentials (out of authorized
> scope — anonymous access only); exhaustive per-module classification of all 49 §13.4.4(d-2) modules or all
> 59 §13.4.4(d-1) doc-guides (only 2 of the 49 are resolved this session — see §64.3 for why the other 47
> stay open); a live N5 GA build or release; a positive Tridium statement on `nCloudDriver` (none found —
> §64.5 narrows the absence, does not manufacture a statement that was not there).
>
> Subject version (jar side): Niagara **5.0.0.28 (Beta)**, `docDeveloper.jar` /
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{test,niagaraTest,bacnet*}.jar` — the
> identical install [Block 1]–[Block 61] read. Subject version (external side, each dated as fetched this
> session, access date **2026-09-27** for every URL): see the source table in §64.0.
>
> Sources: `docDeveloper.jar!doc/upgrade/upgradingToN5.html` (zip entry, re-read this session via
> `zipfile.ZipFile.read()`, not carried from [Block 10]'s extracted-text cache); `.../modules/test.jar!
> META-INF/module.xml` + full zip `namelist()`; `.../modules/niagaraTest.jar!META-INF/module.xml`;
> `.../modules/` directory listing filtered on `bacnet*` (`ls`, this session); `https://www.niagara-
> community.com/s/article/Niagara-5-Breaking-Changes` (`curl -sL`, this session, HTTP 200 body inspected —
> a client-side JS redirect to `Comm_Login`, not the article); `http://archive.org/wayback/available?
> url=niagara-community.com/s/article/Niagara-5-Breaking-Changes` (`curl`, this session, JSON response);
> three additional `niagara-community.com/s/article/*` slugs probed the same way (§64.1); five external
> Tridium PDFs, WebFetch-retrieved then `pdftotext -layout`'d locally this session (§64.0 table); one 2022
> NS22 conference PDF for `test-wb`/`test-se` N4-era background (§64.2).
>
> Method: targeted `<a href>` extraction from a doc file already in this corpus (not a blind re-read);
> `curl`/WebFetch probes of the resolved URL and its likely siblings; WebSearch to locate recent (2025/2026)
> official Tridium conference-session PDFs, each downloaded via WebFetch (which persists the raw PDF
> locally) and re-extracted with `pdftotext`/`pdftotext -layout` (page-numbered) since the WebFetch
> summarizer cannot parse PDF binary streams — the **text is read directly from the extracted `.txt`**, not
> from the summarizer's own (failed) attempt. Markers (canonical list: METHODOLOGY §3): `[CERT]` local
> primary source (jar zip-entry path, `module.xml` attribute, or `ls` output, this session) · `[CERT-doc]`
> the shipped Niagara 5 doc, cited by zip-entry path (extern to this corpus, same convention as [Block 10]
> §10.x) · `[CERT-web]` an official Tridium web/PDF source, cited by URL + access date 2026-09-27, or by PDF
> page number for a WebFetch-retrieved document · `[INFER]` deduction/synthesis.
>
> Inventory/breaking-changes cluster. Connects [Block 10] (BC table — §64.1 adds two BACnet-module rows,
> resolves the "Niagara 5.0 Breaking Changes" hyperlink [Block 10] left unresolved), [Block 13] (module
> inventory delta — §64.3/§64.4 narrow B13-G1/B13-G3), [Block 16] (`test.jar`/TestNG anatomy — §64.2 extends
> its `test.jar` finding to explain `test-wb`'s fate), [Block 28] (closes B28-G1), [Block 18]/[Block 24]/
> [Block 42] (`nCloudDriver`/cloudLink migration chain — §64.5 extends B42-G4).
>
> **Type:** `mixed` — §64.2 upgrades [Block 28]'s named `[INFER]`-leaning gap to `[CERT]`/`[CERT-web]` by
> opening a source that gap explicitly flagged as unopened (the `mixed` trigger per METHODOLOGY §4/§11);
> §64.1/§64.3/§64.4/§64.5 are evidence-gathering that narrows without fully closing, cross-referencing
> [Block 10]/[Block 13]/[Block 42]'s own prior `[INFER]`/open-gap framing rather than deriving purely from
> this session's own primary reads.

---

## 64.0 — External sources opened this session, none previously in either corpus `[CERT-web]`

| # | Document | Publisher/context | Dated | Retrieved via | Pages |
|---|---|---|---|---|---|
| S1 | `N5-FAQ.pdf` | Tridium, confidential internal FAQ | 2026-06-24 (`CreationDate`) | WebSearch → WebFetch → local `pdftotext` | 8 |
| S2 | `tri-niagara-summit-2026-session-dd3.pdf` — **"Niagara 5 Module Transition"**, Niagara Summit 2026 Developer track, 6 named Tridium engineers | Tridium, confidential | 2026-04-27 (`CreationDate`) | WebSearch → WebFetch → local `pdftotext -layout` | 128 |
| S3 | `tri-NF25_Technical_Niagara_Today_and_Tomorrow_News_Update.pdf` | Tridium, Niagara Forum 2025 Technical track | 2025-04-29 | WebSearch → WebFetch → local `pdftotext` | 41 |
| S4 | `tri-NF25_Developer_Introduction_and_Product_News.pdf` | Tridium, Niagara Forum 2025 Developer track | 2025-04-30 | WebSearch → WebFetch → local `pdftotext` | 33 |
| S5 | `DD2-Niagara Development with Gradle.pdf` — NS22 conference | Tridium, Niagara Summit 2022 | 2022-04-26 | WebSearch → WebFetch → local `pdftotext` | 77 |

`[CERT-web]` for each row (WebFetch's own tool-result metadata: file size, retrieval this session; `pdfinfo`
`CreationDate`/`Pages` read directly off each saved PDF, this session — not asserted from search-snippet
text). **S2 is the load-bearing source for §64.1/§64.2/§64.3** — it is the only one of the five that is
both N5-specific and dated after the 5.0.0.28 beta's own `docDeveloper.jar` content, making it the freshest
available cross-check for this gap cluster. S1/S3/S4/S5 are corroborating/negative-evidence sources (S1 for
general N5 timeline context, §64.5's absence-check; S3/S4 mostly pre-date N5 specifics — checked and found
irrelevant to the module-removal question, §64.3; S5 for `test-wb`'s N4-era origin, §64.2).

**WebFetch's built-in summarizer cannot read any of the five** — each WebFetch call returned an apology
that the PDF is "raw binary"/"compressed stream data," while separately confirming the file was saved
locally (`[Binary content ... also saved to .../tool-results/webfetch-*.pdf]`). This is expected and
methodologically fine: WebFetch's stated job is HTML→markdown conversion, not PDF parsing, and it never
claimed to have read the content it couldn't — no `[CERT-web]` claim in this block rests on the
summarizer's own prose. Every citation below is read from the **locally re-extracted** `.txt` (`pdftotext`/
`pdftotext -layout`, run by this session against the saved PDF), quoted or paraphrased verbatim, and for
S2 specifically cross-checked against a **page-numbered** re-extraction (`-layout`, split on the PDF page-
break character `\x0c`) so every S2 citation below carries an exact slide/page number, not just a line
number in an unpaginated dump.

## 64.1 — B10-G2 NARROWED: the "Niagara 5.0 Breaking Changes" hyperlink resolves to a login-gated
Tridium developer-community article, unreachable anonymously; S2 supplies two concrete BACnet-module
rows [Block 10]'s table only had generically `[CERT-web]` / `[CERT]`

**The exact hyperlink, never extracted by [Block 10].** [Block 10] §10.4 quoted the doc's own
forward-reference sentence but bracketed it `[external cross-reference doc, not shipped in this jar]`
without pulling the actual `<a href>`. Re-opening the same zip entry this session and locating the anchor
around the quoted sentence:

```html
<h2 id="niagara-5-breaking-changes">Niagara 5 Breaking Changes</h2>
<p>A full list of breaking changes in 5.0 can be found at
<a href="https://www.niagara-community.com/s/article/Niagara-5-Breaking-Changes">Niagara 5.0 Breaking
Changes</a>. Some important ones you may be likely to run into are detailed below.</p>
```
`[CERT-doc]` (`docDeveloper.jar!doc/upgrade/upgradingToN5.html`, `zipfile.ZipFile.read()`, this session —
the `<h2 id="niagara-5-breaking-changes">` anchor immediately preceding the sentence [Block 10] §10.4
already quoted, confirming this is the SAME cross-reference, not a different one). This resolves half of
B10-G2 outright: the "full list" is **genuinely web-only**, not hidden elsewhere inside `docDeveloper.jar`
under a different path — the doc's own author-supplied link says so directly, ending the "or is it shipped
under a different path" branch of B10-G2's original framing.

**The URL is login-gated — confirmed by direct fetch, not by assumption.** `curl -sL -A "Mozilla/5.0"`
against that exact URL this session returns HTTP 200 with a 1,464-byte body containing only a client-side
JavaScript redirect:

```js
function redirectOnLoad() {
  ... window.location.replace('https://www.niagara-community.com/Comm_Login?ec=302&startURL=%2Fs%2Farticle%2FNiagara-5-Breaking-Changes');
}
redirectOnLoad();
```
`[CERT-web]` (`curl` output, this session, access date 2026-09-27) — a Salesforce Experience-Cloud
("Community") login wall, not a 404: the page exists but requires an authenticated
`niagara-community.com` account (the Tridium developer/partner portal, distinct from the public
`tridium.com` marketing site). Two further probes this session against different `niagara-community.com/
s/article/<slug>` paths (`Niagara-User-Guide`, `docUser`, `Niagara-Obix-Guide` — chosen as B13-G3-relevant
doc-guide-name candidates, §64.4) return the **identical** `Comm_Login` redirect body regardless of
whether the slug names a real article — i.e. this is a site-wide authentication gate on the whole
`/s/article/` path space, not evidence for or against any individual article's existence `[CERT-web]`
(same `curl` method, this session).

**No public archive exists either.** `curl "http://archive.org/wayback/available?url=niagara-
community.com/s/article/Niagara-5-Breaking-Changes"` returns `{"url": "...", "archived_snapshots": {}}` —
zero snapshots `[CERT-web]` (Wayback Machine Availability API, this session, access date 2026-09-27). Net:
this session **cannot** diff [Block 10] §10.4's 32-row table against the canonical list — the canonical
list is reachable only from inside an authenticated Tridium developer-community session, which was not
authorized or attempted this session, and no third-party mirror/archive exists to substitute for it.
**B10-G2's "is the doc-only table a strict subset" question stays open** — but its "web-only vs.
shipped-elsewhere" half is now answered `[CERT-doc]`, and its practical blocker (WHY no prior session
could find it) is now a documented, verified access gate rather than an unexplained miss.

**S2 (the Niagara Summit 2026 developer session, §64.0) is Tridium's own fresh restatement of the same
"Niagara 5 Breaking Changes" material**, independent of the gated article, and it adds real content
[Block 10]'s table did not have at module granularity. S2's own "Niagara 5 Breaking Changes" slide groups
the same core buckets [Block 10] already covers (Security Manager, `javax.baja`→`niagara` namespace,
private→public API moves) `[CERT-web]` (S2 p.61, `pdftotext -layout` this session) — no conflict, no new
information there. But S2's separate **"BACnet updates.."** slide states, verbatim:

```
BACnet updates..
• Removed BACnetOws module
• bacnetAlarmRouter -> bacnetUtil
• Updated APIs
```
`[CERT-web]` (S2 p.84, `pdftotext -layout` this session). [Block 10] §10.4's row **BC-10** covers BACnet
only at the API-shape level ("public API simplified... `Descriptor` interface... constants moved") — it
names no MODULE-level casualty. This session's S2 finding is a genuine addition: **`bacnetOws` is
documented-removed and `bacnetAlarmRouter` is documented-renamed to `bacnetUtil`**, directly answering two
of [Block 13] §13.4.4(d-2)'s 49 unmatched modules (§64.3) — filed as new table rows **BC-33**/**BC-34**
(extending, not replacing, [Block 10]'s BC-01..BC-32 numbering) rather than editing [Block 10]'s own file,
per this task's read-only-single-file scope.

## 64.2 — B28-G1 CLOSED: Tridium's own migration slide shows `moduleTestImplementation(":test-wb")` (4.15)
becoming `moduleTestImplementation(":test")` (5.0) verbatim, side-by-side, as a paired before/after example
`[CERT-web]` + `[CERT]`

[Block 28] §28.9.G named **B28-G1**: CompPan-rt's and DashboardPan's N4 `moduleTestImplementation(":test-
wb")` declaration has no `test-wb.jar` anywhere in the N5 5.0.0.28 install (`ls .../modules | grep -i
test` → only `test.jar`/`niagaraTest.jar`), but since neither module's ported N5 build actually declared a
test dependency (no `srcTest` ported), this was "never exercised as a build failure" — leaving open
whether `test-wb` was renamed, merged, or genuinely dropped.

**S2's "Module Part Cleanup" slide (p.59) answers this directly, as a paired code sample:**

```
 4.15 (post module part reunion)        5.0
 ...
 // Test dependencies                   // Test dependencies
 moduleTestImplementation(":test-wb")   moduleTestImplementation(":test")
```
`[CERT-web]` (S2 p.59, `pdftotext -layout` this session, exact two-column layout preserved by `-layout` —
this is Tridium's own presenter showing the SAME line of build-script code before (N4 4.15, left column)
and after (N5 5.0, right column) migration, not two unrelated examples: every other paired line on the same
slide is an unambiguous rename (`api(":alarm-rt")`→`api(":alarm")`, `api(":bajaui-wb")`→`api(":bajaui")`,
`api(project(":myOtherModule-rt"))`→`api(project(":myOtherModule"))`), confirming the slide's own convention
is left=N4/right=N5 for the SAME dependency, not a list of independent examples).

**This is a positive, authoritative statement — not an absence inference.** It directly settles B28-G1:
`test-wb` is not a "genuinely dropped, no successor" casualty; it is **renamed/consolidated into the single
`:test` module dependency**, the same module-part-reunion pattern (§10.3/BC-20, [Block 10]) applied to
every ordinary `-rt`/`-ux`/`-wb`/`-se` suffix in this exact slide's OTHER rows (`alarm-rt`→`alarm`,
`bajaui-wb`→`bajaui`) — `test-wb` was simply a part-suffixed dependency name like any other, and N5's
module-part elimination collapsed it the same way.

**Corroborated locally, independently of S2, by re-opening `test.jar`'s own `module.xml` this session:**

```xml
<module name="test" ... description="Niagara Test Framework" ...>
 <types>
  <type class="com.tridium.testng.BBaseLocaleTest" name="BaseLocaleTest"/>
  <type class="com.tridium.testng.BBaseUiTest" name="BaseUiTest"/>
  <type class="com.tridium.testng.BCanaryTest" name="CanaryTest"/>
  <type class="com.tridium.testng.BStationTestBase" name="StationTestBase"/>
  <type class="com.tridium.testng.BTridiumTestNg" name="TridiumTestNg"/>
  <type class="niagara.test.BISystemTest" name="ISystemTest"/>
  ... (21 types total)
 </types>
</module>
```
`[CERT]` (`.../modules/test.jar!META-INF/module.xml`, `zipfile.ZipFile.read()`, this session, fresh — not
reused from [Block 16]/[Block 28]'s own opens of the same file; 21 `<type>` entries counted directly). The
type set spans a `BBaseUiTest`/`BCanaryTest` family plausible for a former `-ux`/`-wb`-flavored test
surface alongside the plain `niagara.test.BTest`/`BTestNg` core — consistent with `test.jar` being a
genuine multi-flavor merge target, not merely the old `test-rt`/plain-`:test` module relabeled. `test.jar`
also bundles `LIB-INF/testng-7.12.0.jar` internally, already established by [Block 16] §16.5.3 — this
session's fresh read corroborates that finding rather than contradicting it. `niagaraTest.jar`'s own
`module.xml` (also re-read this session) declares zero `<type>` entries and a single dependency (`baja`
only) — it is a separate, lighter-weight "Simple (and fast) tests to validate basic Niagara module
functionality" runner module, not a `test-wb` candidate.

**Net: B28-G1 CLOSED.** `test-wb` was neither dropped nor mysteriously absent — it is Tridium's own
documented rename target `:test`, the identical module CompPan-rt's/DashboardPan's real N5 build already
depends on implicitly having available (even though neither module's ported build actually re-declared a
test dependency, per [Block 28] §28.2/§28.3's decision to not port the JUnit4 `srcTest` files). A future
session porting real test code for either module should declare `moduleTestImplementation(":test")`, not
search for a `test-wb`/`test-ux` successor module that does not exist as a separate artifact.

**S5 (NS22, 2022) supplies `test-wb`'s own N4-era origin story, background only, not load-bearing for the
closure above.** The 2022 Gradle-migration deck (Ant→Gradle, N4 4.10 era, predating N5 by 4+ years) shows
`moduleTestImplementation("Tridium:test-wb")` and, separately, `moduleTestImplementation("Tridium:test-se")`
as the then-current per-runtime-profile test-dependency names, paired with the generic Ant→Gradle
configuration rename `'niagaraModuleTestCompile' -> 'moduleTestImplementation'` `[CERT-web]` (S5, lines
194/361-441 of the plain-text extraction, this session) — confirming `test-wb`/`test-se` were always
profile-suffixed artifacts of the SAME `-rt`/`-ux`/`-wb`/`-se` naming scheme BC-20 eliminated, `[INFER]`
strengthening (not independently proving) the reading that `test-rt`/`test-ux`/`test-se` collapsed into
`:test` alongside `test-wb` by the identical mechanism, though S2's own paired example names only `test-wb`
specifically.

## 64.3 — B13-G1 narrowed by 2 of 49: `bacnetOws` and `bacnetAlarmRouter` now have documented fates;
the other 47 stay open behind the same login gate `[CERT-web]` + `[CERT]`

[Block 13] §13.4.4(d-2) listed 49 Tridium-vendor code modules with zero N5 `.class`-package overlap and no
removal/merge evidence, asking this session to classify each as documented-removal / merged / renamed /
still-unknown. §64.1's S2 finding directly resolves two:

| Module ([Block 13] §13.4.4(d-2) row) | N4 `.class` count | This session's finding | Class |
|---|---|---|---|
| `bacnetOws` | 4 | S2 p.84: **"Removed BACnetOws module"** — explicit, named, positive removal statement | **documented removal** |
| `bacnetAlarmRouter` (`Tridium Europe`) | 17 | S2 p.84: **"bacnetAlarmRouter -> bacnetUtil"** — explicit rename target | **documented rename** |

The rename is independently corroborated **locally**, not merely asserted by the slide: `ls .../modules |
grep -i bacnet` this session returns `bacnet.jar bacnetAws.jar bacnetEDE.jar bacnetUtil.jar
cloudLinkExtensionBacnet.jar platBacnet.jar` — **`bacnetUtil.jar` genuinely exists** in this exact N5
5.0.0.28 install `[CERT]` (`ls`, this session), giving `bacnetAlarmRouter`→`bacnetUtil` the same two-source
confirmation pattern ([Block 13] §13.4.2's `lonDevices` merge got from directory-name matching) rather than
resting on the slide's prose alone.

**The other 47 modules in [Block 13]'s (d-2) table are NOT resolved this session.** WebSearch/WebFetch
probes were run for a representative sample chosen for plausible public-documentation visibility
(`electronicSignature`, `nCloudDriver`'s `cloudIotHubDep`/`cloudIotHubConnector` siblings — folded into
§64.5 instead, since that family is B42-G4's own subject — `knxnetIp`, `gauth`, `snmp`, `mobile`) against
S1/S3/S4 and general WebSearch; none returned a positive removal/merge/rename statement for any of them.
S3/S4 (Niagara Forum 2025, §64.0) DO mention `GAuth Enrollment Workflow` (S3 p.14) and `Niagara Mobile –
Profile Removal` (S4 p.9) by name, but both are **N4-history timeline recap slides** — the GAuth item is a
4.14 FEATURE-ADDITION bullet (not a removal), and the Mobile item is explicitly about the mobile-PX
`Html5HxProfile`, "Deprecated since 4.6 (Introduced 3.7)" — i.e. it is [Block 10] BC-02's already-known
`app`-module story restated, not new evidence about the SEPARATE `mobile`/`mobileThemeZebra` modules
[Block 13] listed `[CERT-web]` for the quoted text, `[INFER]` for "not the same finding" — read carefully,
neither hit actually answers its corresponding (d-2) row. **Net for the remaining 47: still `(d)
no-merge/removal-evidence found`, unchanged from [Block 13]'s own verdict** — this session narrows the
TOTAL open count from 49 to 47, nothing more; the same `niagara-community.com` login gate identified in
§64.1 is the most likely reason these stay unresolved (Tridium's own release-note/removal announcements for
individual modules, if they exist in prose form at all, most plausibly live on that same gated portal, per
§64.4's parallel finding for doc-guides — `[INFER]`, since this session did not confirm any SPECIFIC (d-2)
module's absence is due to portal-gating rather than genuine non-existence of any such announcement).

## 64.4 — B13-G3 not closed: the doc-guide web portal is behind the SAME login gate identified in §64.1,
not independently tested per-guide `[CERT-web]`

[Block 13] §13.4.4(d-1) found 59 doc-guide jars (`docUser`, `docObix`, `docModbus`, `docSnmp`, etc.) with no
matching artifact inside `docDeveloper.jar`, naming the official Tridium web doc portal as the un-checked
resolution path. Three representative `niagara-community.com/s/article/<slug>` probes this session
(`Niagara-User-Guide`, `docUser`, `Niagara-Obix-Guide` — chosen to plausibly match `docUser`/`docObix`'s
guide names) all returned the identical `Comm_Login` redirect body documented in §64.1, byte-for-byte
`[CERT-web]` (`curl`, this session). Since this redirect fires **regardless of whether the target slug
names a real article** (§64.1 already established this for the Breaking-Changes slug, and these three
probes show the same non-discriminating behavior), **the portal's response is uninformative about any
individual guide's existence or absence** — this session cannot distinguish "the guide exists at a
different, unguessed slug" from "the guide never had a public web page" from "the guide's page exists but
this probe's slug guess is wrong." **B13-G3 stays fully open** — the practical blocker (an authenticated-
only Tridium community portal) is now documented and verified rather than merely presumed, matching §64.1's
finding for the Breaking-Changes article; a session with an authorized `niagara-community.com` account
could plausibly resolve both B13-G1's remaining 47 and all 59 of B13-G3's doc-guides in one sitting, but
that access was not authorized or attempted this session.

## 64.5 — B42-G4 not closed: three more official 2026/2025 Tridium sources (N5-FAQ, the 128-slide N5
Module Transition session, two NF25 decks) make ZERO mention of `nCloudDriver`, narrowing but not
resolving the absence [Block 42] §42.8 already found `[CERT-web]` + `[INFER]`

[Block 42] §42.8 found `nCloudDriver` (N4's Azure-IoT-Hub-backed N-driver bridging Honeywell Sentience)
absent from N5's module set with no dedicated migrator converter registered, concluding `[INFER]` "N4's
`nCloudDriver` was retired without a migration path" — moderately strong, but resting on absence-of-
evidence rather than a positive Tridium statement, and naming this exact gap (B42-G4) as requiring external/
web sourcing out of that session's scope.

**This session ran that external/web search and still found no positive statement.** `grep -i` for
`nCloudDriver`, `Sentience`, `cloudBackup`, or `CloudConnector_Sentience` across S1 (8pp), S2 (128pp — the
single largest, freshest, most N5-specific official source available), S3 (41pp), and S4 (33pp) returns
**zero hits in all four** `[CERT-web]` (grep over the local `pdftotext` extractions, this session). A
general WebSearch for `Tridium nCloudDriver Honeywell Sentience Forge retired deprecated "no longer
supported"` surfaces only an August-2025-dated third-party (OneSight/Distech) technical document describing
`CloudConnector_Sentience`/`nCloudDriver` as still-referenced current terminology for LEGACY N4 platforms
("legacy platforms should use the cloudBackup Only component" — i.e. a component-choice guidance for
EXISTING N4 sites, not an N5-migration statement) `[CERT-web]` (WebSearch result summary, this session,
access date 2026-09-27 — the source document itself was not independently opened this session, so this is
reported at the WebSearch-summary confidence level, weaker than S1-S5's direct PDF reads).

**Reading this correctly.** A 128-slide, 6-named-engineer, dedicated "Niagara 5 Module Transition" official
Tridium developer-conference session (S2) that DOES cover cloud-adjacent driver-framework changes in detail
(nDriver enhancements, BACnet module casualties, §64.1/§64.3) and is unambiguously the single most
authoritative and most N5-specific external artifact this session could locate, **saying nothing about
nCloudDriver at all** is itself informative `[INFER]` — it is consistent with [Block 42]'s own retirement
reading (a retired driver would not appear in a forward-looking migration-training deck), but it is still
not a POSITIVE statement, and this session cannot rule out the explanation that `nCloudDriver` coverage
simply lives on the gated `niagara-community.com` portal (§64.1/§64.4) rather than in any conference deck.
**B42-G4 remains open**, narrowed by checking four additional fresh, high-quality, N5-specific-or-adjacent
official sources (S1-S4) beyond what [Block 42] itself checked, all four negative.

## 64.x — Self-verification (METHODOLOGY §11)

**Token check.** Every `[CERT]` citation (jar zip-entry paths, `module.xml` XML content, `ls` output) was
opened directly this session via `zipfile.ZipFile.read()`/`ls`, not recalled — 6 distinct local artifacts
(`upgradingToN5.html`'s href, `test.jar` module.xml, `niagaraTest.jar` module.xml, the `bacnet*.jar`
directory listing). Every `[CERT-web]` citation is either (a) a direct `curl`/Wayback-API HTTP response
this session (4 probes: the Breaking-Changes article, 3 doc-guide-slug probes, the Wayback availability
check) or (b) a `pdftotext`/`pdftotext -layout` extraction of a WebFetch-retrieved PDF, spot-checked by
re-`grep`ping the exact quoted phrases ("Removed BACnetOws module", "bacnetAlarmRouter -> bacnetUtil",
"moduleTestImplementation(\":test-wb\")", "moduleTestImplementation(\":test-se\")") back against their
source `.txt` files — all 4 resolved on first grep. The one exception, explicitly flagged at reduced
confidence in §64.5, is the OneSight/Distech third-party document, reported only at WebSearch-summary
level (not independently opened this session) — this is a deliberate downgrade, not an oversight.

**Marker tally — literal `toolbelt/verify-block.sh niagara5-block64.md .` output, run this session from
`/home/cristian/niagara5-research`:**

```
== verify-block: niagara5-block64.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 9  (adj 7)
   [CERT-doc] 4  (adj 3)
   [CERT-web] 22  (adj 20)
   [CERT-a] 0
   [INFER] 11  (adj 7)
-- ratio -- [INFER]/[CERT*] = 7/30 = 0.23
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   jar-entry  docDeveloper.jar!doc/upgrade/upgradingToN5.html  (jar archive path — not file-verifiable)
   jar-entry  niagaraTest.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   jar-entry  test.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   (only non-file-verifiable citations recognized: archive-entry paths — see entries above; token-verify inline against cited artifacts)
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

Adjusted tally: 7 `[CERT]` + 3 `[CERT-doc]` + 20 `[CERT-web]` = 30 real evidence claims against 7 real
`[INFER]` claims, ratio **0.23** — low, consistent with a `mixed` block whose two CLOSED/upgraded findings
(§64.1's href resolution, §64.2's B28-G1 closure) rest on direct `[CERT]`/`[CERT-web]` reads, while the
`[INFER]` claims are concentrated in the explicitly-bounded narrowing sections (§64.3's "why the other 47
stay open" reasoning, §64.5's "informative absence" reading) — none load-bearing for either of this
session's two settled verdicts (the href/gate finding, B28-G1's closure).

**Reading the resolution split.** Every `[CERT]`/`[CERT-doc]` citation in this block points into the N5
install tree (`/mnt/c/ProgramData/Niagara/...`) or a WebFetch-saved PDF outside `/tmp` scratch — both
outside this corpus's own directory, so `verify-block.sh` classifies them `extern`, the same
"decompiled/external-tree blocks show zero resolved citations" signature METHODOLOGY §11 documents for
[Block 10]/[Block 13]/[Block 61]'s own jar/native-binary citations. Citation gate for this block is
therefore **inline token-verify**, reported above, not the script's own file:line resolver.

**Artifacts.** This block file created at `/home/cristian/niagara5-research/niagara5-block64.md`. Per the
caller's explicit "touch no other file" scope (matching [Block 10]/[Block 13]/[Block 61]'s own convention),
`INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and backlog re-classification are deliberately
**not** performed this session — left to the orchestrator.

**MCP-doc snapshots.** N/A — no context7/MCP-doc citation in this block; all web evidence is direct
WebSearch/WebFetch/`curl` output, not an MCP documentation-server snapshot.

## 64.x — Child gaps opened

- **B64-G1** (refines **B13-G1**, the remaining 47) — Obtain authorized `niagara-community.com` developer-
  portal access and re-run the removal-classification search for the 47 still-unresolved (d-2) modules
  (`electronicSignature`, `knxnetIp`, `gauth`, `snmp`, `micros`, `opc`, `openAdr`, `ndio`, `mobile`/
  `mobileThemeZebra`, the `fcModelSync*` family, `platPower`/`platNdio`/`platSerialQnx`, `boxAnalyzer`,
  `rdbOracle`, `kitPxBuilding`, the `platHwScanJ*` family, `nrioConversion`, `hdk8000`, `videoMigrator`,
  `modbusTcpSlaveMigrator`, `obixMigrator`, `snmpMigrator`, `weatherUnderground`, `DINsymbol`,
  `analytics-lib`) — not attempted this session (no login credentials authorized).
- **B64-G2** (refines **B13-G3**) — Same portal-access gate as B64-G1, applied to all 59 (d-1) doc-guide
  jars; this session confirmed only that the gate is non-discriminating (fires identically for a real vs.
  guessed slug), not any individual guide's actual web status.
- **B64-G3** (extends **B42-G4**) — The OneSight/Distech third-party `CloudConnector_Sentience` document
  found by WebSearch (§64.5) was never independently opened this session (reported at summary confidence
  only) — read it directly and confirm whether it dates from before or after this N5 5.0.0.28 beta's own
  cutoff, and whether its "legacy platforms" framing implies an N5-specific successor exists.
- **B64-G4** — S2's own "BACnet updates.." slide (§64.1/§64.3, p.84) lists "Updated APIs" as a third bullet
  alongside the two module casualties, with no further detail visible on that slide — the surrounding S2
  pages (p.80-90, not read in full this session, only grepped for specific terms) may contain additional
  BACnet-specific breaking-change detail beyond [Block 10] BC-10's existing API-shape summary.
- **B64-G5** — S2 is a 128-page/slide deck; this session read only the pages returned by a targeted `grep`
  for this gap cluster's specific terms (module-part cleanup, BACnet, breaking changes) plus the intro
  pages (1-40ish) skimmed for context. A full page-by-page read of S2 — especially its JPMS/modularity
  section (p.~100-128, per the earlier untruncated grep's line numbers) and any cloud/driver-migration
  content beyond BACnet — was not performed and could surface further B13-G1/B10-G2 material.

## 64.x — Connections

- **[Block 10]** — §64.1 resolves the exact `<a href>` [Block 10] §10.4 left unresolved (confirms
  web-only, locates the login gate); adds two new BACnet-module breaking-change rows (`bacnetOws` removed,
  `bacnetAlarmRouter`→`bacnetUtil`) that [Block 10]'s own BC-10 row covered only at the API-shape level, not
  the module level — no correction to [Block 10]'s existing 32 rows, a genuine addition alongside them.
- **[Block 13]** — §64.3 resolves 2 of the 49 §13.4.4(d-2) modules (`bacnetOws`, `bacnetAlarmRouter`) from
  "no-evidence" to "documented removal"/"documented rename"; §64.4 confirms (does not newly discover) that
  §13.4.4(d-1)'s un-checked "web doc portal" resolution path is login-gated, explaining why 47+59 items
  remain open rather than leaving that as an unexplained gap.
- **[Block 16]** — §64.2's `test.jar`/`niagaraTest.jar` re-read corroborates (does not contradict) [Block
  16] §16.5.3's finding that `test.jar` bundles `LIB-INF/testng-7.12.0.jar`; extends it with the full
  21-entry `<types>` list and the `niagaraTest.jar` sibling's own (empty-types, single-dependency) anatomy.
- **[Block 28]** — closes **B28-G1** (§64.2) with a positive, dated, official-Tridium-source statement,
  upgrading [Block 28]'s own open "renamed, merged, or genuinely dropped?" framing to a settled "renamed to
  `:test`" answer.
- **[Block 18]/[Block 24]/[Block 42]** — §64.5 extends [Block 42] §42.8's `nCloudDriver`-retirement
  `[INFER]` by checking four additional fresh official sources (all negative), narrowing without closing
  **B42-G4**; no correction to [Block 42]'s own `cloudLink`-vs-`nCloudDriver` architectural-shape analysis.
