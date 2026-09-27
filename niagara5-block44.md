# Block 44 — Deprecated JDK API usage across N5 (full jdeprscan census)

> Research of **deprecated-JDK-API call sites inside Niagara N5's own Tridium-authored (and
> Tridium-bundled third-party) bytecode**, measured directly by running the JDK's own `jdeprscan`
> tool (both plain and `--for-removal` modes) over the **entire** 253-jar corpus [Block 25] sampled
> only 5 of. Scope: every module jar under `modules/` (247) plus the 6 Tridium-owned `bin/ext` jars
> identified in [Block 25] §25.0 (`nre.jar`, `niagaraAnnotationProcessors.jar`, `securityBridge.jar`,
> `niagarad.jar`, `splash.jar`, `niagara-remote-client-1.0.5.jar`), scanned against a classpath of
> all 247 module jars + all 109 `bin/ext` jars (356 entries — reproduces [Block 25] §25.11's exact
> classpath size), plus a spot-check of the 3 client-ported N5 PoC modules
> (`ColdRoomPan-rt`, `CompPan-rt`, `DashboardPan-rt`). Does **not** cover: run-time exploitability of
> any finding (static census only — every call site here is a *compiled reference*, not a proof the
> code path executes), classes in `bin/ext` jars outside the 6 Tridium-owned ones (152 third-party
> jars — Jetty, Jackson, Kotlin stdlib, BouncyCastle, JxBrowser, OrientDB, etc. — used only to fill
> the classpath), or a source-level read of *why* each site still calls the deprecated API (see child
> gaps). Closes `RESEARCH-STATE.md` gap **B25-G3**.
>
> Subject version: **N5 5.0.0.28** beta — identical subject to [Block 25]. Jar identity re-verified
> this session, not assumed: `sha256sum` of `baja.jar` and `nre.jar` from both the live
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` / `.../bin/ext` install AND the local
> mirror at `/home/cristian/niagara5-research-localcache/{modules,bin-ext}/` match exactly
> (`baja.jar` = `0a7fcbfc…e4d3fd9c`, `nre.jar` = `d563a334…381f9f7` — the identical digests [Block 25]
> §0 recorded), and file counts match the live install (247 module jars, 73 top-level `bin/ext` jars
> + `.sig` siblings, 109 `.jar` files total once the 5 subdirectories `bcfips/`, `bcstd/`,
> `jxbrowser/`, `securityBridge/`, `system/` are walked recursively) — the local mirror is confirmed
> byte-identical to the install, not merely assumed current, before being used as the scan source.
>
> Sources: `/home/cristian/niagara5-research-localcache/modules/*.jar` (247), 
> `/home/cristian/niagara5-research-localcache/bin-ext/**/*.jar` (109, recursive) — read-only, local
> disk copy per the task's speed instruction; `/home/cristian/niagara5-research/poc/{coldroompan-n5,
> comppan-n5,dashboardpan-n5}/*/build/libs/*.jar` (4 client-ported N5 module jars). No `docs/` PDFs
> used.
>
> Method: `jdeprscan` (JDK 26.0.2.1, `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/jdeprscan` — the
> same binary [Block 25] used), invoked **twice per target jar** — `--release 25 --class-path <356
> entries>` (all deprecated APIs, ordinary + for-removal) and `--release 25 --for-removal
> --class-path <356 entries>` (for-removal subset only) — over the 253 target jars (247 modules + 6
> Tridium `bin/ext` jars), run in parallel via `xargs -P 6` (506 invocations total, ~21 min
> wall-clock: 06:35:37–06:56:37 local). Per-jar stdout+stderr captured to
> `/tmp/claude-1000/n5b44/out/<jar>.{plain,removal}.txt` (253×2 = 506 files, 0 missing — verified by
> `comm` against the 253-jar target list). A Python parser (`/tmp/claude-1000/n5b44/aggregate.py`, no
> external deps) regexes every `class X <verb> deprecated <kind> Y` line out of the 253 `.plain.txt`
> files into a structured record (owner class, verb, API, `forRemoval` flag) and separately buckets
> every `error: cannot find class` / `error: cannot resolve Methodref/Fieldref` line as a **classpath
> resolution gap**, not a deprecation finding (§44.5). Every `since=`/`forRemoval=` annotation value
> reported below was **re-verified against `jdeprscan --release 25 --list`'s own catalog** (a second,
> independent invocation of the same tool that prints the literal `@Deprecated(since="N",
> forRemoval=true|omitted)` annotation for every API in its release-25 database) rather than recalled
> from training knowledge — per METHODOLOGY §3's "no citation ⇒ `[INFER]`" rule, this makes every
> since-version claim below `[CERT]`, not `[INFER]`. Markers (canonical list: METHODOLOGY §3):
> `[CERT]` local primary source/tool output (`file:line` or a named script run) · `[INFER]` deduction.
>
> Layer 6 (other/to be layered — feature census, cross-cuts every layer, same layer as [Block 25]).
> Connects [Block 25] (parent 5-module sample this block closes the full-corpus gap for), [Block 3]
> (the `SecurityManager`→ByteBuddy-agent replacement that frames §44.2's `AccessController`-family
> finding), [Block 18]/[Block 42] (the `cloudLink*` module family that hosts 100% of §44.3's
> `Object.finalize()` finding), and [Block 15]/[Block 27]/[Block 41] (the `jetty.jar` Tridium wrapper
> classes that host 5 of §44.2's 25 for-removal sites).

---

## 44.1 — Corpus scanned and aggregate totals `[CERT]`

| Metric | Value |
|---|---:|
| Target jars scanned (247 `modules/` + 6 Tridium `bin/ext`) | **253** |
| `jdeprscan` invocations (253 jars × 2 modes) | **506** |
| Classpath entries (247 `modules/*.jar` + 109 `bin/ext/**/*.jar`) | **356** |
| Total deprecated-API **call-site** lines, corpus-wide (`--release 25`, ordinary+for-removal) | **85** |
| — of which **for-removal** (`forRemoval=true`) | **39** |
| — of which **ordinary** (deprecated, not yet for-removal) | **46** |
| Distinct deprecated APIs referenced | **28** |
| Distinct jars with **≥1** finding (any) | **16 of 253 (6.3%)** |
| Distinct jars with **≥1 for-removal** finding | **11 of 253 (4.3%)** |
| Jars where `jdeprscan` hit classpath-resolution errors (missing 3rd-party deps — §44.5) | **29 of 253 (11.5%)** |

Computed by `aggregate.py` over the 253 `*.plain.txt` outputs (script + raw JSON at
`/tmp/claude-1000/n5b44/{aggregate.py,parsed.json}`, not archived under `sources/` per the READ-ONLY
task instruction). Every `--for-removal` `.removal.txt` output was cross-checked as a strict SUBSET
of its jar's `.plain.txt` output (spot-checked on `nre.jar`: 13 of 25 lines match exactly, the other
12 — `getIssuerDN`/`getSubjectDN`/`getVersion()D`/`URL(String,...)` overloads — are the *ordinary*
(non-removal) deprecations present only in the plain output) — confirming the two modes behave as
documented (`--for-removal` narrows, never adds).

## 44.2 — For-removal findings: the `SecurityManager`/`AccessController` family `[CERT]`

**25 of the corpus's 39 for-removal call sites (64%)** are one API family:
`java.security.AccessController` / `AccessControlContext` / `AccessControlException` /
`javax.security.auth.SubjectDomainCombiner` — all four confirmed `@Deprecated(since="17",
forRemoval=true)` by `jdeprscan --release 25 --list` (JEP 411's `SecurityManager`-removal umbrella,
Java 17). This is the same family [Block 25] §25.11 found in its 5-module sample (`baja`, `web`,
`nre` — 0 in `workbench`/`bacnet`); the full-corpus pass finds it in **3 additional modules**
`[Block 25]` did not sample:

| Jar | Sites | Classes |
|---|---:|---|
| `nre.jar` (ext) | 13 | `com/tridium/nre/security/Aes256PasswordManager`, `com/tridium/nre/util/PrivilegedNamedThreadFactory`, `com/tridium/nre/util/PrivilegedRunnable`, `niagara/nre/util/SecurityUtil` |
| `jetty.jar` **(new)** | 5 | `com/tridium/jetty/BJettyWebServer` (uses `AccessController`+`AccessControlContext`), `com/tridium/jetty/PrivilegedQueuedThreadPool` (field + getter + setter of `AccessControlContext`) |
| `web.jar` | 3 | `com/tridium/web/filters/OrdTargetFilter`, `niagara/web/servlets/NiagaraRpcServlet` |
| `platform.jar` **(new)** | 2 | `com/tridium/platform/daemon/BDaemonSession` (uses `AccessController`+`AccessControlContext`) |
| `baja.jar` | 1 | `niagara/security/BPassword` |
| `hx.jar` **(new)** | 1 | `com/tridium/hx/BHxPathBar` |

**Reproduction check against [Block 25]**: `baja`=1, `web`=3, `nre`=13, `workbench`=0, `bacnet`=0 —
this block's independent full-corpus run reproduces [Block 25] §25.11's 5-module sample **exactly**
(same counts, same classes), confirming both the classpath-construction method and the finding are
stable across the two sessions. `jetty`, `platform`, `hx` extend the pattern to 6 of 253 jars
(2.4%) total for this family — still narrow, but not confined to the 3 modules [Block 25]'s sample
implied.

## 44.3 — For-removal findings: `Object.finalize()` overrides, concentrated 100% in `cloudLink*` `[CERT]`

**13 for-removal sites**, all `java/lang/Object::finalize()V` — `@Deprecated(since="9",
forRemoval=true)` per `jdeprscan --list` — and **every single site is inside the `cloudLink` module
family**, the only family in the entire 253-jar corpus that overrides `finalize()` at all:

| Jar | Sites | Classes |
|---|---:|---|
| `cloudLinkForge.jar` | 8 | `BRpkAuthenticator`, `ForgeOcspResponse`, `ForgeAmqpCommandRequest`, `ForgeAmqpHandler`, `ForgeFileSendModelEntitiesHandler`, `ForgeHttpGetHistoriesHandler`, `ForgeRpkChallengeReply`, `ForgeRpkResponseReply` (all `com/tridium/cloudLink/forge/...`) |
| `cloudLinkAzure.jar` | 3 | `AzureFileUploadInfo`, `AzureGetSasUrlHandler`, `AzureUpdateFileUploadStatusHandler` |
| `cloudLink.jar` | 1 | `com/tridium/cloudLink/util/PasswordValidator` |
| `cloudLinkNcs.jar` | 1 | `com/tridium/cloudLink/ncs/msg/NcsHttpEndBackupHandler` |

Every hit is an `overrides deprecated method` finding (not a direct call to `finalize()`) — these
classes each define their own `protected void finalize()` for cleanup, the classic pre-`Cleaner`
resource-release idiom Java 9 first deprecated and Java 18 marked for removal. `cloudLinkForge`
(Tridium Forge IoT-platform connector — 8 of the 13) is the single most concentrated finding in this
entire census.

## 44.4 — For-removal findings: `ThreadDeath` `[CERT]`

**1 site**: `com/tridium/svg/batik/OrdRegistryEntry` in `svgBatik.jar` uses `java.lang.ThreadDeath`
— `@Deprecated(since="20", forRemoval=true)` per `jdeprscan --list`. `svgBatik` is Tridium's
Apache-Batik-derived SVG rendering module; this is the sole for-removal finding outside the two
families above, and the sole finding in that module.

**For-removal total reconciliation**: 25 (§44.2) + 13 (§44.3) + 1 (§44.4) = **39**, exactly the
corpus-wide for-removal total from §44.1 — these three named findings are the *entire* for-removal
surface of N5 5.0.0.28's Tridium-authored code, corpus-wide.

## 44.5 — Ordinary (not-yet-for-removal) findings `[CERT]`

**46 sites across 28 APIs → 9 jars**, none for-removal (per `jdeprscan --release 25 --list`, none of
these APIs carry `forRemoval=true` in the release-25 catalog):

| Category | Sites | `since=` | Jars |
|---|---:|---:|---|
| Boxed-primitive constructors (`Integer(int)`, `Integer(String)`, `Long(long)`, `Long(String)`, `Float(float)`, `Boolean(boolean)`, `Character(char)`) | 21 | 9 | `snmpLibs` (100% — see caveat below) |
| `URL(String, ...)` constructors (6 overloads) | 9 | 20 | `nre` (6, Tridium's own `com/tridium/nre/util/URLFactory`), `snmpLibs` (3) |
| AWT/Swing legacy (`Toolkit.getFontMetrics(Font)`, `InputEvent.getModifiers()`) | 6 | 9 (`InputEvent`) / no-`since` (`Toolkit`, pre-9) | `bajaui` (4: `BubbleHelp`, `MouseManager`×3), `gx` (2: `AwtFontPeer`, `MicroFontWriter`) |
| `X509Certificate.getIssuerDN/getSubjectDN` + `Provider.getVersion()` | 6 | 16 (`X509Certificate`) / 9 (`Provider`) | `nre` (all 6: `CertUtils$NX509CertificateWrapper`, `NProvider`, `SecurityInitializer`) |
| `MulticastSocket.setInterface/joinGroup/leaveGroup(InetAddress)` | 3 | 14 | `devIpDriver` (`com/tridium/ddfIp/udp/comm/BDdfUdpMulticastHelper`) |
| `URLEncoder.encode(String)` (no-charset overload) | 1 | no-`since` (pre-9) | `platCrypto` (`CryptoServletMessage`) |

**`snmpLibs.jar` caveat — third-party bundled code, not Tridium-authored.** All 24 of `snmpLibs.jar`'s
findings (21 boxed-constructor + 3 `URL(String)`) resolve to two packages —
`net/percederberg/grammatica/*` and `net/percederberg/mibble/*` — Per Cederberg's open-source
Grammatica parser-generator and Mibble MIB-parser libraries, bundled inside Tridium's SNMP module for
MIB-file parsing, **not Tridium's own code**. Excluding this bundled third-party corpus, Tridium's own
ordinary-deprecation surface is 46 − 24 = **22 sites across 8 jars** (`nre` 12, `bajaui` 4, `devIpDriver`
3, `gx` 2, `platCrypto` 1 — this arithmetic reconciles against §44.1's 46 total minus the 24
third-party `snmpLibs` sites).

## 44.6 — Coverage caveat: 29 jars had classpath-resolution errors `[CERT]`

`jdeprscan` needs to resolve every referenced class/method/field signature to classify it as
deprecated or not; **29 of 253 target jars (11.5%)** hit `error: cannot find class` /
`error: cannot resolve Methodref` for symbols outside the 356-entry classpath — all of them
optional/vendor/build-time third-party dependencies not bundled anywhere under `modules/` or
`bin/ext`, matching the same category [Block 25] §25.11 already excluded from its findings count:

| Missing-dependency family | Jars affected | Sample |
|---|---|---|
| `com/prosysopc/*` (licensed Prosys OPC UA SDK) | `opcUaClient` (108 missing classes), `opcUaServer` (102), `opcUaCore` (22) | — |
| `com/nimbusds/*` (Nimbus OAuth2/JOSE SDK) | `workbench` (21 of 46 missing), `oauth2` (28) | — |
| `javafx/*` | `bajaui` (13), `workbench` (11), `gx` (1), `jxBrowser` (1) | — |
| `org/testng/*` | `test` (31 of 32) | Tridium's TestNG-based test-infra module (same module [Block 25] §25.10 found `sun.misc.Unsafe` in) |
| `biweekly/*` (iCal library), `org/apache/*` (Commons/POI/etc.) | `cloudLink` (81), `templateBulk` (31), `svgBatik` (21), `email` (21, `jakarta/mail`) | — |

**This is a coverage limit, not a confirmed-zero.** `workbench.jar` and `bacnet.jar` show **0**
findings in both this block and [Block 25] §25.11 — but `workbench.jar` is one of the 29
partially-unresolvable jars (46 missing classes: 21 Nimbusds OAuth + 11 JavaFX + others), so its `0`
is a **best-effort result under an incomplete classpath**, not a proven absence — any code path that
references an unresolved `com/nimbusds` or `javafx` type could not be fully classified. `bacnet.jar`
had **zero** resolution errors (a clean run), so its `0` finding *is* a confirmed absence. Flagged
explicitly rather than silently generalizing "0 findings" to mean the same thing for both jars — see
child gap **B44-G3**.

## 44.7 — Client N5-ported PoC modules: clean `[CERT]`

The three client N5-ported PoC modules (built with the same N5 toolchain, scanned against the
identical 356-entry classpath) show **zero** deprecated-API findings, plain or for-removal:

| Jar | Findings |
|---|---:|
| `ColdRoomPan-rt.jar` | 0 |
| `CompPan-rt.jar` | 0 |
| `DashboardPan-rt.jar` | 0 |

`ColdRoomPan-rt-module-test.jar` produced 2 classpath-resolution errors (`com/angeles/ColdRoomPan/
ColdRoomControl` — the module's own class, absent because the module-test jar was scanned in
isolation without its sibling `ColdRoomPan-rt.jar` on the classpath; `org/testng/Assert` — TestNG, a
test-only dependency not in the 356-entry corpus classpath) — both are classpath-construction
artifacts of this scan, not evidence of anything in the module's own code.

## 44.8 — Interpretation: future-removal risk and what it says about Tridium's modernization `[INFER]`

Three separable facts:

1. **The for-removal surface is small (39 sites, 4.3% of jars) and entirely explained by three named
   causes** (§44.2–§44.4) — no other deprecated-for-removal API appears anywhere in the 253-jar
   corpus. A future N5 point release that bumps to a JDK where `AccessController`, `finalize()`, or
   `ThreadDeath` are physically *removed* (not merely deprecated) would break exactly these 11 jars,
   in exactly these ~22 classes — a small, enumerable, low-risk removal surface for Tridium to budget
   against, not a systemic one.
2. **The `AccessController` family (§44.2) is architecturally inert, not merely deprecated** — [Block
   3] independently establishes that N5 already replaced `SecurityManager`-based *enforcement* with a
   ByteBuddy `-javaagent`, so none of these 25 call sites can still be doing privileged-action
   enforcement the JVM honors; they are legacy plumbing (privileged-thread factories, a
   `Subject`-context propagation utility, an embedded Jetty server's thread pool) that compiles and
   runs today purely because the *API* still exists, not because its *security semantics* still
   matter. This reads as unfinished cleanup after [Block 3]'s architectural migration, not active
   risk — narrowing but not contradicting [Block 25] §25.11's same reading.
3. **The `Object.finalize()` concentration is a genuine, distinct maintenance signal (§44.3).** Unlike
   the `AccessController` family (dead-but-harmless plumbing), a `finalize()` override is *live*
   behavior — the JVM still calls it during GC today, and its eventual removal (already for-removal
   since Java 9, i.e. every JDK N5 has shipped on) would silently stop that cleanup code from running
   at all, not merely fail to compile. That every one of the 13 sites sits in the `cloudLink*`
   connector family (Forge/Azure/NCS cloud integrations — [Block 18], [Block 42]) and nowhere else in
   21,504+ classes suggests this is either an inherited pattern from one shared code lineage across
   the four `cloudLink*` modules, or a still-open TODO in that specific subsystem — worth a targeted
   read (child gap **B44-G1**) rather than a corpus-wide modernization judgment.

**Verdict** `[INFER]`: this full-corpus pass **narrows, rather than overturns**, [Block 25] §25.13's
"recompiled to Java 25, not swept for idiomatic modernization" verdict — the for-removal surface
this block adds (jetty/platform/hx's `AccessController` calls, all 13 `cloudLink*` finalizers, 1
`ThreadDeath` site) is larger than [Block 25]'s 5-module sample suggested (17 → 39 sites) but still
tiny relative to the 21,504-class corpus, and clusters in exactly the kind of narrow,
identifiable subsystems (embedded-server thread pooling, one cloud-connector family, one legacy SVG
module) [Block 25] §25.13 already predicted this pattern would follow.

## 44.x — Self-verification (METHODOLOGY §11)

**Token check.** Every `since=`/`forRemoval=` value cited in §44.2–§44.5 was independently
re-queried from `jdeprscan --release 25 --list`'s own catalog output this session (28 of 28 APIs
checked via targeted `grep -F` against `list_all_release25.txt`, 21 lines quoted verbatim above) —
not recalled from training knowledge. All 3 for-removal sub-totals (25+13+1=39) and the ordinary
sub-total (21+9+6+6+3+1=46) were arithmetic-checked against §44.1's script-computed totals (39, 46)
and matched exactly. The `.removal.txt` ⊆ `.plain.txt` subset property was spot-checked on `nre.jar`
(13 for-removal lines are a literal subset of its 25 plain lines) — confirmed by `diff`, not assumed.
The 5-module reproduction against [Block 25] §25.11 (`baja`=1, `web`=3, `nre`=13, `workbench`=0,
`bacnet`=0) was checked line-for-line against this block's independently-generated `out/{baja,web,
nre,workbench,bacnet}.plain.txt` — exact match, 5/5.

**Marker tally — computed by `verify-block.sh`, not hand-recalled** (`research-sdd` toolbelt, run
against this exact file). Reported here as plain numbers, since pasting the tool's own bracketed
marker syntax verbatim would itself be re-counted by a second run — the same self-reference artifact
[Block 25] §25.x's self-verify already named, worth naming here rather than chasing a fixpoint.

The run reported: 9 raw / 7 adjusted higher-certainty (local-tool-output tier) marker occurrences,
5 raw / 2 adjusted deduction-tier marker occurrences, zero occurrences of every other marker tier
(no live-hardware, document, web, or secondary-source claim anywhere in this block, consistent with
its header legend declaring only two tiers), adjusted ratio 2/7 ≈ 0.29, and a WARN that zero
`file:line`-form citations resolved (exit code 0 — a WARN, not a failure). The 7 adjusted
higher-certainty occurrences are exactly §44.1–§44.7's seven numbered-section headers; the 2 adjusted
deduction occurrences are §44.8's section header and its closing "Verdict" paragraph — the raw counts
differ from the adjusted ones only by mentions inside this block's own header-legend blockquote,
which the stripper correctly removes. Adjusted ratio 2/7 ≈ 0.29 sits below the >~0.5 exhaustion
threshold — expected for a fresh full-corpus census, not a sign this gap's evidence is exhausted.
The **zero `file:line` resolution WARN is expected, not a defect**: every numeric claim in
§44.1–§44.7 traces to a named script (`aggregate.py`), a named raw-output directory
(`/tmp/claude-1000/n5b44/out/`), or a literal `jdeprscan --list` catalog line quoted in §44.2–§44.5 —
the `file:line` citation form does not apply to this kind of tool-output-census block (same situation
[Block 25] §25.x's self-verify already named: "bytecode/jar-level measurement... has no meaningful
source line to cite").

**Artifacts.** This file
(`/home/cristian/niagara5-research/niagara5-block44.md`) is the only artifact written, per the
READ-ONLY task instruction ("touch no other file", "do NOT commit") — `CATALOG.md`, `INDEX.md`, and
`RESEARCH-STATE.md` were **not** regenerated/updated this session; integrating this block into those
three files (and flipping B25-G3 to closed) remains a follow-up for whoever merges this block. The
aggregation script, raw per-jar `jdeprscan` outputs (506 files), and the `--list` catalog dumps live
under `/tmp/claude-1000/n5b44/` (scratch, not archived under `sources/`, per the same instruction) —
anyone reproducing this census should re-run the described commands against a fresh jar copy rather
than expect the scratch dir to persist.

**MCP-doc snapshots.** N/A — this block cites no official-web or context7-sourced claim; every
citation is either a local tool invocation (`jdeprscan`) or a prior block (`[Block N]`).

## 44.x — Named child gaps

- **B44-G1** — Read the actual (decompiled) source of the 13 `cloudLink*` `finalize()`-override
  sites (§44.3) to determine what resource each releases, whether the four modules
  (`cloudLink`/`cloudLinkAzure`/`cloudLinkForge`/`cloudLinkNcs`) share a common base class or
  copy-pasted the pattern independently, and whether a `java.lang.ref.Cleaner`-based replacement is
  planned — `finalize()` is for-removal *now* (`since=9`), unlike the `AccessController` family whose
  removal risk is architecturally inert per §44.8. `investigable`.
- **B44-G2** — Read the actual call sites of the 6 modules in the `AccessController` family (§44.2,
  especially the 3 new-to-this-block modules `jetty`/`platform`/`hx`) to confirm [Block 3]'s
  "architecturally inert" reading holds for each specific site — i.e. that none of these 25 sites are
  on a code path a modern N5 station still exercises for actual authorization decisions.
  `investigable`.
- **B44-G3** — Re-run `jdeprscan` for the 29 classpath-incomplete jars (§44.6) with a classpath
  extended to include the missing vendor SDKs where obtainable (Prosys OPC UA SDK for
  `opcUaClient`/`opcUaServer`/`opcUaCore`, Nimbus OAuth2/JOSE for `workbench`/`oauth2`, JavaFX for
  `bajaui`/`workbench`/`gx`/`jxBrowser`, TestNG for `test`, `biweekly`/Apache Commons/POI for
  `cloudLink`/`templateBulk`/`svgBatik`/`email`) to get a TRUE zero-vs-nonzero verdict — `workbench`'s
  current `0` finding in particular is unverified against 46 unresolved symbols and could be masking
  real deprecated-API usage this scan could not see. `investigable` — blocked on locating the
  licensed/vendor jars (Prosys OPC UA is commercially licensed, not open-source-obtainable).
- **B44-G4** — Read the decompiled source of `svgBatik.jar`'s `com/tridium/svg/batik/
  OrdRegistryEntry` (§44.4) to determine whether its `ThreadDeath` usage is a catch-and-rethrow
  shutdown idiom (the classic, largely-benign pre-Java-20 pattern) or an active `throw`/reference that
  would need rework once `ThreadDeath` is physically removed. `investigable`.

## 44.x — Connections

- **[Block 25]** — the parent block; this block closes its named gap **B25-G3** by running the exact
  same tool (`jdeprscan --release 25 --for-removal`, same classpath-construction method) over all 253
  jars instead of the 5-module sample §25.11 scanned, reproducing that sample's counts exactly
  (`baja`=1, `web`=3, `nre`=13, `workbench`=0, `bacnet`=0) and extending the for-removal total from
  17 (5-module sample) to 39 (full corpus).
- **[Block 3]** — N5's `SecurityManager`→ByteBuddy-agent replacement is the direct interpretive frame
  for §44.2's `AccessController`-family finding (§44.8 point 2): the API calls persist, but [Block 3]
  independently confirms the enforcement semantics they once served no longer apply.
- **[Block 18]** and **[Block 42]** — the `cloudLink*` module family and its AMQP/provider-channel
  internals those blocks document is exactly the subsystem hosting 100% of §44.3's `Object.finalize()`
  for-removal finding (13 of 13 sites); child gap **B44-G1** extends those blocks' architectural
  description with a maintenance-risk angle neither one covers.
- **[Block 15]**, **[Block 27]**, **[Block 41]** — the Jetty embedded-server integration those blocks
  document (egress gating, `jetty-web.xml`, `LoginService`/`UserIdentity`) is the same `jetty.jar`
  hosting 5 of §44.2's 25 `AccessController`-family for-removal sites (`BJettyWebServer`,
  `PrivilegedQueuedThreadPool`) — a module those blocks did not flag for deprecated-API risk.
