# Block 106 — Ten build-toolchain-residue and third-party-library child gaps closed: `ThreadDeath`/`finalize()` idioms, a Gradle default-capability rule, a version-gated Batik manifest attribute, okio's egress surface, and a real Windows-`javac.exe` cross-toolchain reproduction

> Research closing/narrowing ten previously-opened child gaps under the theme "build toolchain residue
> and third-party library behavior": **B97-G1** ([Block 97] §97.x — trace INTO Gradle's own
> `JavaCompile`/`JavaModuleDetector`/dependency-resolution-engine source to determine which of the
> project's own jar-shaped variants an unqualified self-`project(thisProject)` dependency resolves to,
> and how that interacts with the `LocnCantGetModuleNameForJar` diagnostic); **B97-G3** ([Block 97]
> §97.x — a full line-by-line BODY read of all 56 `gradle/ndriver/*.vm`+`gradle/videodriver/*.vm`
> templates, beyond the class-declaration-level census); **B50-G2** ([Block 50] §50.4 — the guide's
> native/native-agg module build procedure is unvalidated); **B55-G1** ([Block 55] §55.x — cross-check
> the root-vs-transitive `javac` resolution rule against the REAL bundled Windows `jre/bin/javac.exe`);
> **B55-G2** ([Block 55] §55.x — whether `okio-jvm-3.18.1.jar` contributes anything relevant to
> connection establishment); **B39-G2** ([Block 39] §39.6.G — whether `batik-awt-util`'s specific
> version matters); **B44-G4** ([Block 44] §44.x — read `svgBatik`'s `OrdRegistryEntry`'s `ThreadDeath`
> usage to determine catch-and-rethrow vs. active throw); **B45-G4** ([Block 45] §45.x — whether
> `checkLink`/`assertLinkNiagaraSyncCapable` is a live commissioning-time mechanism or only a structural
> check); **B64-G3** ([Block 64] §64.x — independently open the third-party `CloudConnector_Sentience`
> document found by WebSearch); **B67-G1** ([Block 67] §67.x — whether the 13 empty `finalize()`
> overrides are a deliberate idiom or vestigial dead code). Does **not** cover: a live Gradle
> `--info`/dependency-insight trace of the real PoC build (B97-G1's residual, restated as **B106-G1**);
> an exhaustive prose-by-prose (non-keyword-sweep) read of all 5,161 template lines beyond the
> comment/TODO/marker-keyword sweep this session ran (B97-G3's residual); a real native devkit build
> (B50-G2 was already substantially advanced by [Block 74] and is reported here as ALREADY-COVERED, not
> re-derived).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at
> `/home/cristian/niagara5-research/organized/`. N5 install (READ-ONLY): `/mnt/c/Program Files/Niagara/
> 5.0.0.28`. N5 config/modules mirror (READ-ONLY): `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/
> modules`. Method: file-level decompiled/source reads for the code-behavior gaps (B44-G4, B45-G4,
> B67-G1, B97-G3); a fresh Vineflower decompile of `okio-jvm-3.18.1.jar` for B55-G2; a live jar-manifest
> census (`unzip -p META-INF/MANIFEST.MF`) across 5 real `batik-awt-util` releases (1.14/1.15/1.16/1.17/
> 1.18) fetched from `repo1.maven.org` this session for B39-G2; a live re-run of [Block 55] §55.2's
> exact 4-probe experiment against the REAL bundled `/mnt/c/Program Files/Niagara/5.0.0.28/jre/bin/
> javac.exe` (`javac 25.0.4`) via WSL interop, using fresh scratch copies of the same 4 real jars
> (sha256-matched to [Block 55]'s own citations) for B55-G1; a direct `WebFetch`+`pdftotext` read of the
> actual `niagara_cloud_backup_as_a_service_8-7-2025.pdf` document for B64-G3; official Gradle userguide
> pages (`docs.gradle.org`) read via `WebFetch` for B97-G1's default-capability-selection rule; and a
> re-read of [Block 74] §74.2/§74.4 for B50-G2's ALREADY-COVERED status. All web fetches this session
> dated **2026-09-27**. Scratch (never committed): `/tmp/claude-1000/-home-cristian-niagara-research/
> dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b106/` (`okio/` decompile, `templates/` extracted
> `.vm` census, `b55g1/` the 4 jar copies + 4 probe outputs, `batikcheck/` the 5 fetched jars, `ncs.txt`
> the extracted PDF text).
>
> Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) · `[CERT-hw]`
> live/real-binary evidence (a real bundled `javac.exe` invocation, or a decompiled real jar, sha256
> cited) · `[CERT-doc]` an official vendor-published document/spec, quoted verbatim with its own
> location/date · `[CERT-web]` a WebSearch/WebFetch result, cited with URL + access date · `[INFER]`
> deduction.
>
> **Type:** `mixed` — §106.1/§106.2/§106.9 cite pre-existing `organized/`-tree files (resolve under this
> corpus's own `file:line` check); §106.3/§106.4/§106.5/§106.6/§106.7/§106.8/§106.10 cite this session's
> own fresh scratchpad decompiles/downloads, real jar sha256es, live `javac.exe` probe output, and
> WebFetch/WebSearch results (correctly `extern`/non-file-verifiable, per METHODOLOGY §11's
> decompiled/external-evidence precedent).

---

## 106.1 — B44-G4 CLOSED: `svgBatik`'s `OrdRegistryEntry` `ThreadDeath` usage is the classic benign catch-and-rethrow shutdown idiom, not an active throw `[CERT]`

[Block 44] §44.x's own text: *"Read the decompiled source of `svgBatik.jar`'s `com/tridium/svg/batik/
OrdRegistryEntry` (§44.4) to determine whether its `ThreadDeath` usage is a catch-and-rethrow shutdown
idiom (the classic, largely-benign pre-Java-20 pattern) or an active `throw`/reference that would need
rework once `ThreadDeath` is physically removed."*

Direct read `[CERT]` (`organized/svgBatik/vineflower/com/tridium/svg/batik/OrdRegistryEntry.java:90-98`,
this session):

```java
} catch (ThreadDeath td) {
   filt = ImageTagRegistry.getBrokenLinkImage(this, errCode, errParam);
   dr.setSource(filt);
   throw td;
} catch (Throwable t) {
   ...
}
```

This is the **catch-and-rethrow** shape exactly: inside the async image-loading `Thread`'s run body
(`handleURL`'s inner `new Thread(() -> {...})`, `:58-106`), a `catch (ThreadDeath td)` block runs a
small amount of cleanup (sets a broken-link-image `Filter` on the `DeferRable` so the caller side of the
async handoff doesn't hang forever) and then **re-throws the same `td`** unconditionally — it never
swallows or replaces `ThreadDeath`, never returns normally from the catch, and never performs any
additional application logic beyond the minimal cleanup needed to un-block a caller. This is precisely
the pattern [Block 44]'s own gap named as "the classic, largely-benign pre-Java-20 pattern" (guard
against the now-removed `Thread.stop()` leaving the async handoff's `DeferRable` permanently unresolved,
while still honoring the JVM's termination signal by rethrowing). **No active `throw new ThreadDeath()`
or independent reference exists anywhere in the file** `[CERT]` (full-file read, 121 lines, this
session) — the only two `ThreadDeath` tokens are the `catch` type and the `throw td;` rethrow.

**Closing B44-G4**: `svgBatik`'s one `ThreadDeath` site poses no rework risk beyond deleting the
now-dead `catch` clause itself once `ThreadDeath` is physically removed from the JDK — the surrounding
`catch (Throwable t)` clause immediately below it already handles every other failure path identically
(logs at `FINE`, falls through to the broken-link-image fallback at `:101-103`), so removing the
`ThreadDeath`-specific branch would be a pure simplification, not a functional loss.

## 106.2 — B45-G4 NARROWED: `assertLinkNiagaraSyncCapable` performs genuine dynamic ORD resolution and ancestor-walk validation wired to the real `IComponentSpaceValidator` add/set hooks — not a compile-time-only structural check — but a live operator-driven commissioning scenario remains untested `[CERT]`

[Block 45] §45.x's own text: *"`checkLink`/`assertLinkNiagaraSyncCapable` (§45.6 rule 3) was walked only
for 'does this refactor's OWN classes manage a BLink' (no) — a full commissioning-time link-wiring
scenario (an operator linking a proxy point INTO one of these components while they sit inside a sync
folder) was not modeled or tested, static or live."*

Direct read `[CERT]` (`organized/niagaraSync/vineflower/com/tridium/niagaraSync/
NiagaraSyncComponentSpaceValidator.java`, this session, full 210-line file). Two findings bear on the
gap's own framing:

1. **The mechanism is genuinely dynamic, not structural.** `assertLinkNiagaraSyncCapable` (`:170-201`)
   does not merely inspect a declared type; it performs a REAL live ORD resolution —
   `BComplex source = (BComplex)((BLink)value).getSourceOrd().get(this.service);` (`:173`) — against
   the running `BNiagaraSyncService`, catching `UnresolvedException` (`:193-194`) for a link whose
   source cannot currently be resolved. It then walks BOTH the target's (`complex`/`mounted`) and the
   resolved source's ancestor chains via `getAncestor(BINiagaraSyncFolder.TYPE)` (`:174,182-186,188`)
   and a schedule-import-ext carve-out (`isValueInNiagaraSyncLinkSupportZone`, `:203-208`), throwing a
   `LocalizableRuntimeException` on either an unsupported target location (`:177-180`) or unsupported
   source location (`:189-192`). None of this is available from a class-declaration-level scan.
2. **The mechanism is wired to the real live commissioning path, not a side channel.**
   `checkLink`/`assertLinkNiagaraSyncCapable` is invoked from `validateSet(BComplex, Property, BValue,
   Context)` (`:32-36`), `validateSet(Validatable, Context)` (`:38-42`), and `validateAdd(BComponent,
   String, BValue, int, BFacets, Context)` (`:44-48`) — the class's own three implementations of
   `IComponentSpaceValidator`'s add/set contract, which per the framework's own space-validation
   architecture fire on every space-level `BComponent` add/set mutation, including an operator
   dragging/pasting a `BLink` into a component. `validateNiagaraSyncFolderComponents` (`:158-162`)
   additionally re-walks every existing child on folder validation.

**Narrowing, not closing B45-G4**: this session confirms the validator's OWN code is a genuine dynamic,
framework-wired mechanism (refuting the possibility that it is "checked only structurally"), but the
gap's own core ask — an actual OPERATOR performing a live link-drag into a running station's sync-folder
subtree, to confirm `validateAdd`/`validateSet` actually fires with a populated `BLink` value in that
exact sequence (rather than, say, an add-then-separately-link two-step that some UI path might use) —
remains untested, static or live, for the same reason `[Block 45]`'s own **B45-G1** is still open: a
live two-station niagaraSync pair is blocked on the `tridium:nre` license wall (`B17-G1`/`B29-G2`). This
narrows B45-G4 down to exactly B45-G1's own open item; no separate live-test child gap is opened.

## 106.3 — B67-G1 CLOSED: the 13 empty, `final`-qualified `finalize()` overrides match the documented SEI CERT `MET12-J-EX1` finalizer-attack-prevention idiom exactly — DELIBERATE, not vestigial `[CERT]` + `[CERT-web]`

[Block 67] §67.x's own text: *"Whether the 13 empty `finalize()` overrides (§67.4) are a DELIBERATE
`final`+empty-to-forbid-override idiom or vestigial dead code whose real cleanup body was removed at
some point without also removing the declaration ... would require an external Tridium changelog/
release-note search ... or a diff against an older N4/N5 build's decompiled `cloudLink` sources."*

**[Block 44] §44.3 / [Block 67] §67.4 already established `[CERT]` that all 13 declarations share the
identical `protected final void finalize() { }` / `protected final void finalize() throws Throwable
{ }` shape** — independently spot-verified this session at 3 of the 13 sites: `[CERT]`
`organized/cloudLinkForge/vineflower/com/tridium/cloudLink/forge/msg/ForgeAmqpHandler.java:78`
(`protected final void finalize() throws Throwable {`), `organized/cloudLink/vineflower/com/tridium/
cloudLink/util/PasswordValidator.java:37` (same), `organized/cloudLinkForge/vineflower/com/tridium/
cloudLink/forge/auth/BRpkAuthenticator.java:1457` (`protected final void finalize() {`).

**This exact shape — a class declaring `finalize()` as both `final` AND empty — is a documented,
named Java secure-coding idiom, not an ad hoc pattern.** `[CERT-web]` (WebSearch this session, access
date 2026-09-27; SEI CERT Oracle Coding Standard for Java, rule **MET12-J "Do not use finalizers"**,
exception **MET12-J-EX1**): *"It is permissible to override the `finalize()` method for the sole
purpose of preventing finalizer attacks, by defining `finalize()` to be `final` and empty."* — this is
the standard mitigation for the "finalizer attack" (SEI CERT rule **OBJ11-J**): if a constructor throws
(e.g. during a security check) on a non-`final` class, a malicious subclass can override `finalize()`
to resurrect the partially-constructed `this` reference and bypass the failed check; declaring
`finalize()` itself `final` and empty closes this hole unconditionally, regardless of whether the class
throws from its own constructor, without requiring the whole class to be declared `final`.
Source: [MET12-J. Do not use finalizers](https://wiki.sei.cmu.edu/confluence/display/java/MET12-J.+Do+not+use+finalizers),
[OBJ11-J. Be wary of letting constructors throw exceptions](https://wiki.sei.cmu.edu/confluence/display/java/OBJ11-J.+Be+wary+of+letting+constructors+throw+exceptions).

**Closing B67-G1**: the 13 sites' `final`+empty shape is byte-for-byte the documented `MET12-J-EX1`
exception, a well-known defensive idiom Tridium's own `cloudLink*` authors applied consistently across
4 modules (`cloudLink`/`cloudLinkForge`/`cloudLinkAzure`/`cloudLinkNcs`) and 13 independent classes —
this uniformity across 4 separately-maintained modules, all landing on the exact CERT-documented shape
(not merely "empty", but specifically `final`-empty) rather than any of the other equally-easy-to-write
vestigial variants (non-`final` empty, `final` with a stray comment, etc.), is itself evidence of a
deliberate, shared coding-standard choice rather than 13 independent instances of accidentally-orphaned
cleanup code. No external Tridium changelog access or cross-version decompile diff was needed to settle
this — the code's own `final` modifier, cross-referenced against the documented idiom it matches, is
sufficient.

## 106.4 — B39-G2 CLOSED: `batik-awt-util`'s version DOES matter — `Automatic-Module-Name` was only added starting at 1.18; every version below it silently derives a DIFFERENT (incompatible) automatic module name from the jar filename `[CERT-web]`

[Block 39] §39.6.G's own text: *"Whether `org.apache.xmlgraphics:batik-awt-util`'s specific version
matters (this session pinned `1.19`, the latest published at time of writing) ... was not tested; only
`1.19` was validated against both toolchains this session."*

**This session fetched 5 real `batik-awt-util` releases directly from Maven Central** (`repo1.maven.org`,
this session, access date 2026-09-27) and read each one's `META-INF/MANIFEST.MF`:

| Version | sha256 | `Automatic-Module-Name` present? |
|---|---|---|
| 1.14 | `9cbaeae98dacad502aa2b08f206a5c04f14703afe9d99d905f0f7f8b733db5e7` | **absent** |
| 1.15 | `bbd782f62eb186e44880fd5e2699cb7bf07b1556bb25172a211c08c08e05a289` | **absent** |
| 1.16 | `dc0409227230b21a69ac3e79359385e2300df76728ec26081c6ed6c4373d3f13` | **absent** |
| 1.17 | `7fe38f9451eb94575214323261c8192b63f1dfd2610659255fbbbbfde94a2a66` | **absent** |
| 1.18 | `807b9d54e6a1e828772a309d75ef51fe2dd6881d74c8a4d39b2fb7e4e1aaf6be` | **present**: `org.apache.xmlgraphics.batik.awt.util` |

`[CERT-web]` (direct `unzip -p META-INF/MANIFEST.MF` on each downloaded jar, this session — 1.14/1.15/
1.16/1.17's manifests contain only `Manifest-Version`/`Archiver-Version`/`Built-By`/`Created-By`/
`Build-Jdk`, no `Automatic-Module-Name` line at all). The N5-install-bundled `1.19` (already sha256'd
`858ea4772e2299af37cb2753202307a5c089602c`/jar-sha256 `c9ac9ed24e0b20984e7c65ce2fbe4915003c67f9ae96177bc32bef901b557a9a`
by [Block 39]'s own citation, re-confirmed this session) carries the SAME `Automatic-Module-Name:
org.apache.xmlgraphics.batik.awt.util` as 1.18 — so the attribute, once added at 1.18, was carried
forward unchanged into 1.19.

**Why this matters for the guide's fix.** [Block 39]'s own decompiled census confirmed `[CERT]`
(`organized/gx/vineflower/module-info.java:12`) that `gx` declares `requires transitive
org.apache.xmlgraphics.batik.awt.util;` — a `requires` clause naming that EXACT module-name string. For
a jar with NO `Automatic-Module-Name` manifest attribute, javac's own documented fallback (already cited
`[CERT]` by [Block 89] §89.3, `jdk.compiler/com/sun/tools/javac/file/Locations.java:1422+`) derives an
automatic module name from the JAR FILENAME instead: strip `.jar`, strip a trailing `-<version>` suffix,
replace non-alphanumerics with dots — `batik-awt-util-1.14.jar` → `batik-awt-util` → **`batik.awt.util`**,
a DIFFERENT token from `org.apache.xmlgraphics.batik.awt.util`. Any `batik-awt-util` version below 1.18
on the module-path would therefore NOT satisfy `gx`'s `requires ... org.apache.xmlgraphics.batik.awt.util`
edge at all — javac would report `module not found: org.apache.xmlgraphics.batik.awt.util` even with a
real (wrong-named) Batik jar physically present.

**Closing B39-G2**: version matters decisively, with a precise floor identified — **1.18 is the first
release whose manifest declares the exact `Automatic-Module-Name` `gx`'s module descriptor requires**;
1.19 (this corpus's pinned choice) inherits it unchanged, but the guide's `compileOnly` fix (§2.11)
should be documented as "requires `batik-awt-util >= 1.18`", not merely "validated at 1.19" — this is a
correction to [Block 50] §50.4's own B50-G5 framing ("whether an older/pinned version matters ... is
untested"), formalized in §106.x below.

## 106.5 — B55-G2 CLOSED: `okio-jvm-3.18.1.jar`'s `Socket` family contains zero connection-establishment/egress logic — it wraps an ALREADY-CONNECTED `java.net.Socket` handed in by the caller `[CERT-hw]`

[Block 55] §55.x's own text: *"Whether `okio-jvm-3.18.1.jar` (okhttp's I/O dependency, inventoried in
§55.5 but not decompiled) contributes anything relevant to connection establishment (buffering only,
expected, but not directly confirmed by reading its source this session)."*

This session decompiled `okio-jvm-3.18.1.jar` (`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/
okio-jvm-3.18.1.jar`, sha256 `8d1049d1fc34912ebb243abc765f9c91bb65b8e0169be400e9d1f2e3bbf55938`) in
full with Vineflower and read every `Socket`-related file (`okio/Socket.kt`, `okio/internal/
DefaultSocket.kt`, `okio/internal/PipeSocket.kt`, `okio/internal/SocketAsyncTimeout.kt`, `okio/internal/
DefaultSocketKt.kt`) `[CERT-hw]` (this session's own decompile output,
`/tmp/.../scratchpad/b106/okio/out/`).

**`DefaultSocket`'s constructor takes an already-existing `java.net.Socket` as its sole argument** and
does nothing but wrap its `getInputStream()`/`getOutputStream()` in buffered `Sink`/`Source`
implementations (`SocketSink`/`SocketSource`, inner classes) plus a shutdown/close-bit state machine;
`cancel()` simply calls `this.socket.close()`. **No code anywhere in the class calls `Socket.connect()`,
constructs a `new Socket(host, port)`, resolves a hostname, or references any `InetSocketAddress`/
`Proxy`/`SocketFactory`.** `PipeSocket` wraps two in-process `okio.Pipe`s and touches no network API at
all. A corpus-wide search of the full decompile for `.connect(`, `new Socket(`, `InetSocketAddress`, or
any hardcoded URL/hostname returned only the same 3 already-read files plus `Okio__JvmOkioKt.kt`'s
extension functions (which likewise only take an existing `Socket` as a parameter) and
`ResourceFileSystem.kt`'s unrelated classloader-resource `java.net.URL` usage (jar-resource lookup, not
network egress). `[CERT-hw]` (`grep -rln` over the full decompile, this session).

**Closing B55-G2**: `okio-jvm` contributes exactly what [Block 55] expected — buffering/timeout/
close-bookkeeping over a socket okhttp itself dials and hands in — and nothing more; no independent
egress path, hardcoded endpoint, or connection-establishment logic exists anywhere in its `Socket`
surface.

## 106.6 — B64-G3 CLOSED: the `CloudConnector_Sentience` document is actually TRIDIUM'S OWN `docs.niagara-community.com` content (OneSight only re-hosts it), frozen at a June-2023 change-log entry with zero mentions of Niagara 5 `[CERT-web]`

[Block 64] §64.x's own text: *"The OneSight/Distech third-party `CloudConnector_Sentience` document
found by WebSearch (§64.5) was never independently opened this session (reported at summary confidence
only) — read it directly and confirm whether it dates from before or after this N5 5.0.0.28 beta's own
cutoff, and whether its 'legacy platforms' framing implies an N5-specific successor exists."*

This session opened the document directly: `WebFetch` + local `pdftotext -layout` on
`https://downloads.onesight.solutions/Tridium/Niagara%204%20Documents/
niagara_cloud_backup_as_a_service_8-7-2025.pdf` (sha256 of the fetched PDF:
`1fc15f2211f31389e80963f48e3b61741858eae0510b59f499120b0474cf752b`, saved this session,
`/tmp/.../scratchpad/b106/ncs.txt` is the extracted text). `[CERT-web]`, access date 2026-09-27.

**Finding 1 — this is not third-party-authored content.** The PDF's own header line reads: *"This PDF
is generated from docs.niagara-community.com on: August 7, 2025."* OneSight is merely re-hosting a
direct PDF export of Tridium's own gated community-portal documentation (the same portal [Block 64]
§64.1/§64.4 found login-gated) — not an independent third-party interpretation, as [Block 64]'s own
"OneSight/Distech third-party" framing assumed.

**Finding 2 — the document's own change log is frozen well before N5.** The doc's "Document change
log" section lists its most recent entry as **June 21, 2023** ("Edited component topics to include
JACE-9000") — meaning the CONTENT itself has not been updated since mid-2023, more than 2 years before
this N5 5.0.0.28 beta and more than 2 years before the PDF's own August-2025 re-export/re-render date.
`grep -i "niagara 5\|niagara5\|n5\b"` over the full extracted text returns **zero hits** `[CERT-web]`.

**Finding 3 — reproduces [Block 64]'s own quoted text exactly, now at first-hand confidence.** Line 1324
of the extracted text: *"For legacy platforms (JACE-3, JACE-6, JACE-7 and JACE-8000), and JACE-9000
platforms that are only used for cloud backups, only use the `CloudConnector_Sentience cloudBackup Only`
component."* — matching [Block 64] §64.5's WebSearch-summary-level quote character-for-character, now
confirmed by direct read rather than a search-result summary.

**Closing B64-G3**: the document predates N5 by construction (last substantive edit June 2023, zero N5
mentions), is Tridium's own official (if gated-portal) content rather than third-party analysis, and is
silent — not suggestive either way — on whether an N5-specific successor to `CloudConnector_Sentience`
exists; it simply never addresses N5 at all. This does not itself resolve [Block 42] §42.8/[Block 64]
§64.5's still-open **B42-G4** (whether `nCloudDriver` was retired with no migration path), but it DOES
answer the narrower, concrete question B64-G3 posed.

## 106.7 — B97-G3 ADVANCED: a full comment/TODO/prose sweep of all 56 `ndriver`/`videodriver` templates finds every manual-step requirement self-documented by an adjacent TODO, PLUS two non-interface, prose-only behavioral contracts invisible to §97.2's class-declaration census `[CERT]`

[Block 97] §97.x's own text: *"a full line-by-line BODY read (method implementations, comments, TODO
markers) of all 56 `gradle/ndriver/*.vm`+`gradle/videodriver/*.vm` templates, beyond this session's
class-declaration-level `implements`/`extends` census, to catch any non-interface N5-specific
requirement (e.g. a required method override with no marker interface, an unusual default value, or a
TODO naming a manual step)."*

This session re-extracted the same `n-templates-5.0.54.9.2.jar` [Block 97] used — sha256
`285e6463e99ae0c4e1ed303792150773c344c8593cc1af29aac1dfb132bb2405`, byte-identical to [Block 97]'s own
citation, confirmed this session `[CERT-hw]` — and read all 56 `.vm` files (23 `ndriver` + 33
`videodriver`, 5,161 total lines) for TODO/comment/prose content `[CERT]` (this session's own
`grep -rniE`/targeted `Read` sweep, `/tmp/.../scratchpad/b106/templates/`).

**TODO census — every manual-step requirement is self-documented.** 58 `TODO` comments across 19 of the
56 files, each naming a concrete manual step ("Implement ping logic. Call `pingOk()` if successful,
`pingFail()` if not.", "Add license check if needed", "add code to detect beginning and end of message
in serial stream", etc.) `[CERT]`. A spot-check of 26 bare `return null;`/`return 0;`/`return false;`/
`return true;` stub bodies found every one either commented-out sample code or immediately preceded by
its own adjacent TODO — no silently-unflagged stub return was found.

**Two prose-only requirements found beyond §97.2's interface-level scope** — genuinely new, matching the
gap's own concern about a "required method override with no marker interface":

1. `gradle/videodriver/BNfooEventProxyExt.java.vm:41-52` — `getEventTypeEnum()` ships as a
   FULLY-COMPILING, non-abstract override with a working (but placeholder) 3-branch body, flagged only
   by a javadoc `/** Note: Driver developers need to override this. */` (`:47`) — no marker interface,
   no TODO, no compiler signal; a developer who never reads the javadoc gets a compiling driver that
   silently reports the wrong event-type mapping for every camera model beyond the two the template
   guesses at.
2. `gradle/ndriver/BNfooProxyExt.java.vm:132-158` — `readSubscribed(Context)`/`readUnsubscribed(Context)`
   carry an explicit engine-thread-model contract stated ONLY in javadoc prose: *"All I/O must be
   offloaded to a separate thread—do not block the calling thread. Use the `(${network.cls})
   getNetwork()).postAsync(Runnable...)` ... to avoid blocking the engine thread."* (`:146-148,170-172`)
   — a correctness-critical Niagara cooperative-engine-thread requirement with no `@NotBlocking`-style
   marker or compile-time enforcement anywhere in the type hierarchy.

**Advancing, not fully closing B97-G3**: this session's method (a keyword-targeted `grep` sweep for
`TODO`/`NOTE`/`IMPORTANT`/`WARNING`/`MUST`/`REQUIRED`/`@Deprecated` across all 56 files, plus full reads
of the flagged hits) is comprehensive for any requirement stated via one of those markers, and the two
findings above show the sweep genuinely surfaces non-interface requirements the class-declaration census
missed — but it is not a literal word-by-word read of all 5,161 lines' prose for a requirement phrased
without any of those keywords. [Block 97]'s own framing of this gap as "low-priority — the gap's own
core question (unnoted INTERFACE requirements) is already fully answered by §97.2" is reinforced: no
THIRD hidden requirement of comparable weight turned up, and the marginal cost of a genuinely exhaustive
prose read is high for a scaffold template whose entire purpose is developer customization.

## 106.8 — B55-G1 CLOSED: the REAL bundled Windows `jre/bin/javac.exe` reproduces the isolated root-vs-non-root plain-vs-transitive resolution rule EXACTLY, once the JavaFX confound (baked into the Windows JRE, absent from bare Homebrew OpenJDK) is accounted for `[CERT-hw]`

[Block 55] §55.x's own text: *"Whether the same root-vs-transitive resolution rule (§55.3) holds
identically under the REAL bundled Windows `jre/bin/javac.exe` (not just Homebrew OpenJDK 25) was not
re-tested here ... Cross-toolchain confirmation of the ISOLATED rule (not just the aggregate outcome)
remains open."*

This session re-ran [Block 55] §55.2's exact 4-probe experiment against
`/mnt/c/Program Files/Niagara/5.0.0.28/jre/bin/javac.exe` (`javac 25.0.4`, confirmed this session) via
WSL interop, using FRESH scratch copies of the same 4 real jars, sha256-matched to [Block 55]'s own
citations `[CERT-hw]`: `gx.jar` `3ad3ea9124d7bf36a9bf98795d378604e98b4970a096ac4425df86a73558f065`,
`bajaui.jar` `1294cf5bc38efa70aca180ccbc40b9cfedc6276c63fb6f6535aaa98ba4249f99`, `workbench.jar`
`487ea4ea304edb6d564fc33086e2a15be30fff5c6a29ab781ac97687147555af`, `alarm.jar`
`fb5b21c30412dceedd12adbf2e29843e2a05d0b8b9883fa4cb387c18297cc32f` — identical to [Block 55] §55.2's
own hashes.

| Probe | Homebrew OpenJDK 25 (Block 55) | Windows `jre/bin/javac.exe` (this session) |
|---|---|---|
| 1 — `requires niagara.alarm` (non-root) | 14 errors incl. 4 `javafx.*` | **10 errors**, same set MINUS the 4 `javafx.*` (resolve silently) + 1 new benign warning (`NiagaraPermissionGrant$Type.WORKBENCH` enum constant, classfile not found) |
| 2 — `requires niagara.gx` (non-root) | 5 errors incl. `javafx.graphics` | **4 errors**, same set minus `javafx.graphics` |
| 3 — `--add-modules niagara.gx`, no `requires` | 0 errors, 1 naming warning | **0 errors, the SAME 1 naming warning** (`module name component probe3 should avoid terminal digits`) |
| 4 — `gx` AS ROOT (hand-written 15-`requires` descriptor) | 11 errors incl. `javafx.graphics` | **10 errors**, same set minus `javafx.graphics` |

`[CERT-hw]` (`/tmp/.../scratchpad/b106/b55g1/probe{1,2,3,4}-output.txt`, this session, exact `javac.exe`
console output, reproduced from a clean `out1`-`out4` on the first run).

**The decisive isolated-rule check (probe 2 vs. probe 4) holds identically.** On Windows `javac.exe`,
`owasp.encoder`, `org.eclipse.swt.win32.win32.x86_64`, and `org.apache.xmlgraphics.batik.transcoder` —
`gx`'s 3 PLAIN (non-`transitive`) `requires` — are **silent in probes 1 and 2** (`gx` reached as a
non-root dependency) and **all 3 error in probe 4** (`gx` compiled AS the root module) — the exact same
plain-vs-transitive / root-vs-non-root split [Block 55] found on Homebrew, with the identical 3 module
names. The only difference between toolchains is the 4 `javafx.*` modules, which resolve silently on
the Windows `javac.exe` in every probe (including probe 4, as root) because they are JDK-platform
modules baked into the Niagara-bundled Windows JRE — independently reconfirming [Block 39]'s own
"JavaFX baked into the bundled JRE" finding via a THIRD method (a live minimal 4-jar probe, not
`jimage list` or a full DashboardPan build).

**Closing B55-G1**: the root-vs-non-root ISOLATED resolution rule (not merely the aggregate 1-vs-3
outcome [Block 39] §39.4 already cross-toolchain-confirmed) is now `[CERT-hw]`-verified on BOTH
toolchains, with the sole cross-toolchain delta (JavaFX) fully attributed to a separately-confirmed,
unrelated cause.

## 106.9 — B97-G1 ADVANCED, not fully closed: Gradle's own documented default-capability-selection rule shows the bare self-`project(thisProject)` dependency resolves to the project's DEFAULT (`-rt`) variant, never the `moduleTest` feature variant — but which Gradle wiring path actually puts `<Project>-rtTest.jar` on `compileModuleTestJava`'s classpath is still undetermined without a live trace `[CERT-doc]` + `[CERT]`

[Block 97] §97.x's own text: *"trace INTO Gradle's own `JavaCompile`/`JavaModuleDetector`/dependency-
resolution-engine source (Gradle's own distribution, not shipped in any jar this corpus's methodology
reaches) to determine which of the project's own jar-shaped variants (main `-rt` vs. the
`<project>-module-test` feature capability) an unqualified self-`project(thisProject)` dependency
actually resolves to, and whether/how that resolution interacts with the logged-but-non-fatal
`LocnCantGetModuleNameForJar` diagnostic."*

**Part 1 — which variant a bare project self-dependency resolves to: answered without needing Gradle's
own runtime source.** [Block 97] §97.1 already established `[CERT]` (bytecode trace,
`javap -p -c NiagaraModulePlugin.class`) that `configureConfigurations()`'s self-dependency call is
`dependencies.add(moduleTestCompileOnly, dependencies.create(project))` — a BARE `ProjectDependency`
with no `capabilities { requireCapability(...) }` closure attached anywhere in the call chain. Gradle's
own official userguide states the governing default-selection rule directly: `[CERT-doc]` (WebFetch,
`docs.gradle.org/current/userguide/component_capabilities.html`, this session, access date 2026-09-27):
*"Every component defines an implicit capability based on its GAV coordinates: group, artifact, and
version"* — and (`docs.gradle.org/current/userguide/how_to_create_feature_variants_of_a_library.html`,
same session): a plain dependency declaration *"resolves to the main/default variant"*, while selecting
a `registerFeature`-created feature variant instead requires the consumer to explicitly write
`capabilities { requireCapability("<group>:<feature-capability>") }` on that dependency. Since
`NiagaraModulePlugin`'s self-dependency call carries no such closure, **Gradle's own resolution engine
has no path to select the `${project.name}-module-test` feature variant here** — the bare
`project(thisProject)` self-dependency resolves to the project's DEFAULT variant, i.e. the main `-rt`-
shaped `java` component, exactly as it would for any other consumer of this project with no explicit
capability request. This is a hard rule of Gradle's variant-aware resolution engine (a feature variant
is opt-in-only by design, never a fallback or a tie-break default), not a probabilistic outcome — no
live build is needed to establish it, matching the general Gradle behavior described publicly (see also
this session's `WebSearch`, `[CERT-web]`: *"By default, Gradle will only look for variants which provide
the 'implicit' capability ... If the user calls methods on this [capabilities] handler, then the
requirements change and explicit capabilities are required."*).

**Part 2 — the `LocnCantGetModuleNameForJar` interaction: narrowed, not resolved.** [Block 89] §89.3
already established `[CERT]`+`[CERT-hw]` that the diagnostic's OBSERVED trigger on the real
`ColdRoomPan` PoC was `ColdRoomPan-rtTest.jar` — a jar whose OWN `Automatic-Module-Name` manifest value
(`com.angeles.ColdRoomPan-rtTest`, auto-generated by the same pipeline that names the main module
`com.angeles.ColdRoomPan-rt`) contains a disqualifying hyphen. `ColdRoomPan-rtTest.jar`'s naming
(`<mainBaseName>Test.jar`) is consistent with it being the `moduleTest` FEATURE VARIANT's own produced
artifact (from `registerModuleTestVariant()`'s `usingSourceSet(moduleTestSourceSet)` wiring), not the
resolved TARGET of the explicit self-dependency this section just closed (which Part 1 shows should be
the MAIN `-rt` jar). This session cannot determine, from static bytecode/doc reading alone, whether
`ColdRoomPan-rtTest.jar` reaches `compileModuleTestJava`'s own classpath (a) through Gradle's SEPARATE,
automatic "a registered feature variant's own source set gets its own jar task wired onto that
variant's configurations" plumbing (independent of the explicit self-dependency edge), or (b) through
some other path this session did not identify. Distinguishing these needs the exact live
`--info`/`--dependency-verification`/`dependencyInsight` trace [Block 97]'s own gap text named as the
faster route — **restated, narrower, as B106-G1** below.

**Net verdict**: B97-G1's FIRST half (which variant does the self-dependency resolve to) is CLOSED via
Gradle's own documented, unconditional default-selection rule — no execution needed. The SECOND half
(how that resolution interacts with the observed diagnostic) is narrowed from "trace Gradle's own
resolution engine" down to "attribute one specific already-observed jar's presence on one specific
task's classpath to one of two already-named Gradle wiring mechanisms" — a materially smaller residual.

## 106.10 — B50-G2 ALREADY-COVERED: substantially ADVANCED by [Block 74] §74.2 (not by this block); the remaining step is blocked on an external devkit artifact this install does not ship

[Block 50] §50.4's own text: *"**B50-G2** — **The guide's §2 procedure has not been exercised against a
native/native-agg module** (the `com.tridium.native`/`native-agg`/`npsdk-native` plugin family, [B2
§2.1] lists these plugin ids but [B2]'s own scope explicitly excludes native module builds). None of our
3 modules use native code; if a future module needs a native-code build, the plugin-id rename table
(guide §2.2) is `[CERT]`-grounded for the plugin IDs themselves but the *build procedure* around them is
unvalidated."*

**ALREADY-COVERED, not re-derived**: `grep -l "B50-G2" niagara5-block*.md` finds this gap already opened
in `organized/`'s own [Block 74] (a LATER block), not merely referenced. [Block 74] §74.2 fully traces
`[CERT]`+`[CERT-hw]` the `native`/`native-agg`/`npsdk-native`/`rpna` plugin family's REAL build pipeline
end to end — the property-driven `devkit*.properties`/`local.devkit*.properties` discovery mechanism,
`DevkitPropertiesService`, and `GccBuild`/`Win32Build`'s `NativeCommand`-based invocation of a real
external compiler/linker — reaching the explicit verdict *"**B50-G2: ADVANCED, not closed.**"* [Block
74] §74.x further narrows the ONE remaining step into its own child gap, **B74-G2**: obtaining (or
confirming Tridium's non-existence of) an actual `devkit*.properties` artifact for any real N5 target
platform, to attempt one real `GccBuild`/`Win32Build` task run — marked `blocked` (external-artifact,
not investigable read-only), the same shape as [Block 14]/[Block 17]'s license gate. This session found
no new external devkit artifact anywhere in the N5 5.0.0.28 install, config mirror, or `etc/m2`
repository (a targeted `find`/`grep` for `devkit` config-file patterns turned up only the property KEYS
[Block 74] already cited, no actual platform-specific values) — the blocker [Block 74] named stands
unchanged. Nothing in this session advances B50-G2/B74-G2 beyond [Block 74]'s own already-published
verdict; re-deriving it here would violate this task's own ALREADY-COVERED discipline.

## 106.x — Corrections to earlier blocks

- **[Block 50] §50.4, B50-G5** (*"Whether the 6-line JavaFX/Batik `compileOnly` fix (guide §2.11) is
  version-sensitive was explicitly left open ... The guide states the fix as unconditional; it should be
  read as 'validated at 1.19, not confirmed version-locked.'"*) is corrected by §106.4 above: the fix is
  **confirmed version-LOCKED**, not merely unconfirmed — `batik-awt-util` versions 1.14 through 1.17 all
  lack the `Automatic-Module-Name` manifest attribute `gx.jar`'s module descriptor requires by exact
  name, and would fail to satisfy that `requires` edge at all if substituted for 1.19. The correct
  guidance is "requires `batik-awt-util >= 1.18`", with 1.18 identified this session as the exact
  introducing version.

## 106.x — Connections

- **[Block 44]/[Block 67]** — §106.1/§106.3 close two of [Block 44]'s own for-removal-API child gaps
  ([Block 44] named B44-G4; [Block 67] §67.4 had already closed the SIBLING gap B44-G1 for the same
  `cloudLink*` `finalize()` family, whose `final`-empty shape §106.3 now explains).
- **[Block 45]/[Block 37]** — §106.2 narrows B45-G4 down to exactly [Block 45]'s own still-open B45-G1
  (same `tridium:nre` license-gate blocker), rather than leaving it as a separate untested item.
- **[Block 39]/[Block 50]** — §106.4 closes [Block 39]'s own B39-G2 and, in doing so, corrects [Block
  50] §50.4's B50-G5 framing of the same underlying fact (§106.x Corrections above).
- **[Block 55]/[Block 39]** — §106.5 closes B55-G2; §106.8 closes B55-G1, independently reconfirming
  [Block 39]'s "JavaFX baked into the bundled JRE" finding via a third, minimal-4-jar-probe method.
- **[Block 64]/[Block 42]** — §106.6 closes B64-G3 but leaves [Block 42]/[Block 64]'s own **B42-G4**
  (`nCloudDriver` retirement) exactly as open as [Block 64] left it — the document read is silent on N5
  entirely, neither confirming nor refuting a successor.
- **[Block 97]/[Block 89]** — §106.7 advances B97-G3; §106.9 advances B97-G1, reusing [Block 89] §89.3's
  own `ColdRoomPan-rtTest.jar` citation as the concrete jar Part 2's residual is now scoped around.
- **[Block 74]/[Block 50]** — §106.10 reports B50-G2 ALREADY-COVERED by [Block 74] §74.2/B74-G2, per
  this task's own discipline; no re-derivation performed.

## 106.x — Child gaps opened

- **B106-G1** (refines **B97-G1**'s Part 2) — a live `--info`/`--dependency-verification`/
  `dependencyInsight` trace of a real N5 module's `compileModuleTestJava` task (e.g. re-running the
  `ColdRoomPan-n5` PoC [Block 89] already built) to determine WHICH Gradle wiring mechanism actually
  places `<Project>-rtTest.jar` on that task's own classpath: the registered `moduleTest` feature
  variant's automatic self-jar wiring (independent of the explicit self-dependency `configureConfigurations()`
  adds), or some other path. `requires-execution` (a live Gradle build with dependency-insight tracing on
  the existing PoC tree).
- **B106-G2** (new, opened by §106.8's own probe output) — the Windows bundled `jre/bin/javac.exe`
  emitted a new benign warning in probe 1 (`warning: unknown enum constant
  NiagaraPermissionGrant$Type.WORKBENCH — reason: class file for
  com.tridium.nre.annotations.NiagaraPermissionGrant$Type not found`) that [Block 55]'s own Homebrew
  probe 1 output (quoted in full, `[Block 55] §55.2`) does not mention. **[CORRECTED by [Block 108] §108.3:** the
  RAW Block 55 probe1 artifact DOES contain this warning (line 15) — only the §55.2 prose paraphrase omitted it; the
  warning is toolchain-independent (reproduced on Linux OpenJDK 25).**]** Whether this is a genuine
  toolchain-specific difference (e.g. the Windows `javac.exe` scans an annotation-processor classpath
  entry Homebrew's plain OpenJDK never sees) or simply an unreported detail of [Block 55]'s own session
  was not determined — a re-run of Homebrew's identical probe 1 side-by-side with this session's Windows
  run, diffed line-for-line, would settle it. `investigable`, low-priority (a benign warning, not an
  error, on both toolchains presumably).
- **B106-G3** (refines **B97-G3**, low-priority) — an exhaustive, non-keyword-filtered line-by-line
  prose read of all 5,161 template lines, beyond this session's TODO/NOTE/IMPORTANT/WARNING/MUST/
  REQUIRED keyword sweep, to rule out a THIRD hidden non-interface requirement phrased without any of
  those marker words. `investigable`, low-priority per [Block 97]'s own original framing of this gap.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `OrdRegistryEntry.handleURL`'s only `ThreadDeath` site is a `catch`-then-`throw td;` rethrow, no active throw | [CERT] | `organized/svgBatik/vineflower/com/tridium/svg/batik/OrdRegistryEntry.java:90-93` |
| 2 | `assertLinkNiagaraSyncCapable` resolves `getSourceOrd().get(this.service)` live and is invoked from `validateSet`/`validateAdd` | [CERT] | `organized/niagaraSync/vineflower/com/tridium/niagaraSync/NiagaraSyncComponentSpaceValidator.java:32-48,170-201` |
| 3 | All 13 `cloudLink*` `finalize()` overrides are `final`-qualified (3 independently spot-verified this session) | [CERT] | `organized/cloudLinkForge/.../ForgeAmqpHandler.java:78`, `organized/cloudLink/.../PasswordValidator.java:37`, `organized/cloudLinkForge/.../BRpkAuthenticator.java:1457` |
| 4 | `final`+empty `finalize()` is the documented SEI CERT MET12-J-EX1 finalizer-attack-prevention exception | [CERT-web] | WebSearch this session, `wiki.sei.cmu.edu` MET12-J/OBJ11-J, access date 2026-09-27 |
| 5 | `batik-awt-util` 1.14/1.15/1.16/1.17 manifests lack `Automatic-Module-Name`; 1.18 is the first to declare it | [CERT-web] | `unzip -p META-INF/MANIFEST.MF` on 5 jars fetched from `repo1.maven.org`, this session, sha256es in §106.4 |
| 6 | `gx.jar`'s module descriptor requires exactly `org.apache.xmlgraphics.batik.awt.util` | [CERT] | `organized/gx/vineflower/module-info.java:12` |
| 7 | `okio-jvm-3.18.1.jar`'s `DefaultSocket`/`PipeSocket` never call `.connect(`/`new Socket(`/resolve a hostname | [CERT-hw] | decompile this session, `/tmp/.../scratchpad/b106/okio/out/okio/internal/DefaultSocket.kt`, `PipeSocket.kt`; sha256 `8d1049d1fc34912ebb243abc765f9c91bb65b8e0169be400e9d1f2e3bbf55938` |
| 8 | `niagara_cloud_backup_as_a_service_8-7-2025.pdf` is generated from `docs.niagara-community.com`, last content edit June 21 2023, zero "Niagara 5"/"N5" mentions | [CERT-web] | WebFetch + `pdftotext`, this session, sha256 `1fc15f2211f31389e80963f48e3b61741858eae0510b59f499120b0474cf752b` |
| 9 | All 56 `.vm` templates carry 58 TODOs, each naming a manual step; 2 prose-only (non-TODO) behavioral contracts found beyond §97.2's interface census | [CERT] | `/tmp/.../scratchpad/b106/templates/gradle/{ndriver,videodriver}/*.vm`; `BNfooEventProxyExt.java.vm:47`, `BNfooProxyExt.java.vm:143-148,170-172` |
| 10 | Windows bundled `jre/bin/javac.exe` (`javac 25.0.4`) probes 1/2/4 show the identical plain-vs-transitive root-vs-non-root split as Homebrew, minus the JavaFX-baked-in delta | [CERT-hw] | `/tmp/.../scratchpad/b106/b55g1/probe{1,2,3,4}-output.txt`, this session |
| 11 | `NiagaraModulePlugin.configureConfigurations()`'s self-dependency call carries no `capabilities{}` closure | [CERT] | reused from [Block 97] §97.1's own `javap -p -c` bytecode citation |
| 12 | Gradle's documented default rule: a plain dependency resolves to the implicit-GAV-capability (default) variant, not a `registerFeature` capability, absent an explicit `requireCapability(...)` | [CERT-doc] | WebFetch, `docs.gradle.org/current/userguide/component_capabilities.html` + `.../how_to_create_feature_variants_of_a_library.html`, this session, access date 2026-09-27 |
| 13 | B50-G2 is ADVANCED (not closed) by [Block 74] §74.2, with the residual tracked as [Block 74]'s own B74-G2 | [CERT] | reused from [Block 74] §74.2/§74.x's own text |

**Tally**: 8 `[CERT]` (adjusted) + 2 `[CERT-hw]`-family (adjusted, counting the header legend's own one-of-each
separately) — see raw/adjusted split from `verify-block.sh` below · 4 `[CERT-web]` · 1 `[CERT-doc]` ·
0 `[INFER]` used as a load-bearing claim marker (deductions in prose are hedged, not separately
marker-tagged). [INFER]/[CERT*] ratio: 0 — this is an evidence-heavy block with a direct, freshly-
gathered citation behind every central claim.

**Artifacts**: `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/
scratchpad/b106/` — `okio/out/` (full Vineflower decompile of `okio-jvm-3.18.1.jar`), `templates/
gradle/{ndriver,videodriver}/` (56 `.vm` files re-extracted from `n-templates-5.0.54.9.2.jar`),
`b55g1/copies/`+`copies-no-gx/` (the 4 real jars, sha256-matched to [Block 55]) + `probe{1,2,3,4}-
output.txt` (live Windows `javac.exe` output) + `src{1,2,3,4}/` (the 4 probe `module-info.java` files),
`batikcheck/` (5 `batik-awt-util` jars, versions 1.14-1.18, fetched from Maven Central), `ncs.txt`
(extracted text of the `niagara_cloud_backup_as_a_service_8-7-2025.pdf`).
