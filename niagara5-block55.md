# Block 55 — Why some absent requires break javac and others don't; egress gates inside okhttp and Jetty

> Research closing two independent gaps left open by prior blocks: **B39-G3** (why 3 of `gx.jar`'s own
> nominally-mandatory `requires` edges — `org.apache.xmlgraphics.batik.transcoder`,
> `org.eclipse.swt.win32.win32.x86_64`, `owasp.encoder` — never surface as `module not found` errors on
> either toolchain, while a 4th, `org.apache.xmlgraphics.batik.awt.util`, always does) and **B15-G2**
> (whether `okhttp`/`jetty-client`/`jetty` carry an INDEPENDENT host-allowlist/interceptor gate of their
> own that Niagara's own usage does not add but the library might apply regardless). Covers: a full
> `javap -v` dump of `gx.jar`/`bajaui.jar`/`workbench.jar`/`alarm.jar`'s module descriptors (every
> `requires` edge with its raw access-flag bits); 4 independently-controlled `javac` compiles against
> copies of those 4 jars, each varying exactly one structural variable (root-vs-non-root, direct-vs-
> transitive) to isolate the true resolution rule; a Vineflower decompile of okhttp's
> `RealConnection`/`ConnectPlan`/`Dns`/`NullProxySelector`/`RouteSelector`/`AddressPolicy` and Jetty's
> `ClientConnector`/`HttpClient`/`HttpClientTransportDynamic` connection-establishment code; and a
> corpus-wide sweep of the **N4** `niagara-research/organized/` decompiled tree (4.8 GB, 373+ modules)
> for every Niagara-authored use of `OkHttpClient.Builder`, `addInterceptor`, `proxySelector`,
> `socketFactory`, and `ClientConnector`. Does **not** cover: a live N5 station deploy reproducing either
> finding (§19 build-PoC only, no station involved — same open gap prior blocks left); okhttp's/jetty's
> own test suites or CVE history; whether some THIRD library (not okhttp/jetty) used elsewhere in N5
> adds a gate (out of scope, B15's own original boundary).
>
> Subject version: **Niagara 5.0.0.28 beta** (same install/config roots as [Block 8]/[Block 9]/[Block 15]/
> [Block 16]/[Block 28]/[Block 39]). Homebrew JDK toolchain: `/home/linuxbrew/.linuxbrew/opt/openjdk@25`
> (`javac 25.0.4.1`, re-confirmed this session). Install root (READ-ONLY): `/mnt/c/Program Files/Niagara/
> 5.0.0.28`; config/modules root (READ-ONLY): `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28` —
> `ls modules | wc -l` = **247** before and after this session, unchanged. `okhttp`/`jetty` jars are read
> from `bin/ext` (unversioned by config — they are toolchain/runtime jars, not config-mirrored modules).
> Cross-corpus: N4 baseline read from `/home/cristian/niagara-research/organized/` (REMITTANCE decompiled
> tree, pre-existing, not regenerated this session).
>
> Sources:
> - `module-info.class` extracted fresh this session from `gx.jar`, `bajaui.jar`, `workbench.jar`,
>   `alarm.jar` (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`), `javap -v`'d with the
>   Homebrew `openjdk@25` toolchain — full `Module:` attribute dump (every `requires`, its raw flag byte,
>   and its resolved version string), preserved under `/tmp/claude-1000/n5b55/modinfo/` (ephemeral
>   scratch, sha256'd this session, reproducible from the cited jars).
> - 4 independent `javac --module-path` compiles this session against **copies** of the 4 jars above
>   (`/tmp/claude-1000/n5b55/copies/`, sha256'd) — `probe1` (root requires `niagara.alarm`, full 4-jar
>   path), `probe2` (root requires `niagara.gx` directly, same path), `probe3` (`--add-modules
>   niagara.gx`, empty root, same path), `probe4` (root **is** a hand-written `niagara.gx` module-info
>   mirroring the real one's 15 `requires` lines, `bajaui.jar`+`workbench.jar`+`alarm.jar` only —
>   `gx.jar` itself excluded from the path to avoid a name collision with the source root).
> - `okhttp-jvm-5.5.0.jar`, `okio-jvm-3.18.1.jar`, `jetty-client-12.1.13.jar`, `jetty-io-12.1.13.jar`
>   (`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/`) — Vineflower-decompiled fresh this session
>   (`okhttp3.internal.connection.{RealConnection,ConnectPlan,RouteSelector,AddressPolicy}`,
>   `okhttp3.{Dns,OkHttpClient}`, `okhttp3.internal.proxy.NullProxySelector`,
>   `org.eclipse.jetty.io.ClientConnector`, `org.eclipse.jetty.client.{HttpClient,
>   AbstractHttpClientTransport,AbstractConnectorHttpClientTransport}`,
>   `org.eclipse.jetty.client.transport.{HttpClientTransportDynamic,HttpClientTransportOverHTTP}`).
> - `/home/cristian/niagara-research/organized/` — a `ripgrep`-parallel (`-j16`) sweep of the FULL 4.8 GB
>   N4 decompiled corpus for `OkHttpClient\.Builder`, `addInterceptor`, `\.proxySelector\(`,
>   `ProxySelector`, `\.socketFactory\(`, `SocketFactory`, `ClientConnector` — every hit opened and read
>   this session, not sampled.
> - [Block 39] (§39.x, the parent finding B39-G3 closes), [Block 15] (§15.2/§15.x, the parent finding
>   B15-G2 closes), [Block 28] (the original stub-jar PoC B39/B55 both build on).
>
> Method: `javap -v` module-descriptor reading (no new decompilation needed for that half — the
> `.class` constant pool + `Module` attribute is read directly), a **controlled 4-variable `javac`
> experiment** (§55.2 — copy-to-`/tmp`, vary exactly one structural axis per run, hold the rest fixed),
> Vineflower 1.12.0 decompilation (`/home/cristian/niagara5-research/tools/decompilers/
> vineflower-1.12.0.jar`, run on `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`), and a full-corpus
> `ripgrep` sweep with manual read-through of every hit. Markers: `[CERT-hw]` this session's own live
> `javac`/`ripgrep`/`javap` command output (the dominant marker for §55.1-§55.4) · `[CERT]` local primary
> source read this session (decompiled `.kt`/`.java`, `file:line`) · `[CERT-web]` official web source ·
> `[INFER]` deduction (used narrowly, §55.3's general JPMS characterization only — the RESOLUTION
> BEHAVIOR itself is `[CERT-hw]`, independently reproduced 4 times; only the SPEC-LEVEL "why" framing
> that generalizes beyond what was directly tested is `[INFER]`).
>
> N5 build-toolchain layer (§55.1-§55.4) + N5/N4 security/runtime layer (§55.5-§55.9). Direct child of
> [Block 39] §39.x (closes **B39-G3**) and [Block 15] §15.x (closes **B15-G2**). Cross-corpus:
> `niagara-research/organized/` (N4, read fresh this session, not regenerated).
>
> **Type:** standard (evidence — two independent evidence sub-investigations sharing one block per the
> caller's single-file deliverable scope; each half is self-contained and separately citable).
>
> **Breakthrough:** the anomaly [Block 28] first noticed and [Block 39] restated without resolving —
> "3 nominally-mandatory `requires` edges never error, 1 always does" — is **not a javac quirk and not
> about the `static` modifier at all**. A 4-way controlled experiment (copying the 4 real jars to `/tmp`
> and varying exactly one axis per compile) isolates the true rule: **javac only force-resolves a
> dependency module's `requires transitive` edges when that module is reached indirectly (not the
> compile root); a module's plain, non-transitive `requires` edges are force-resolved ONLY when that
> module IS the compile root.** `org.apache.xmlgraphics.batik.awt.util` is the ONLY one of the 4 flagged
> `ACC_TRANSITIVE` in `gx.jar`'s own descriptor — the other 3 are plain — and `gx.jar` is NEVER the
> compile root in any real N5 third-party-module build (it is always reached transitively, via `alarm`/
> `bajaui`/`workbench`). Making `gx` the root (probe4, a hand-copied module-info) flips all 3 previously-
> silent edges to hard errors, proving the rule directly rather than by elimination. The `static`
> modifier turned out to be a RUNTIME-only optionality flag in this data — `javafx.graphics` (`requires
> transitive static`) still hard-errors at COMPILE time when unresolvable and reachable, refuting the
> literal "requires static is compile-time-optional" framing this gap started from.

---

## 55.1 — Full `requires` tables, every edge's raw flags, for the 4 modules in the chain `[CERT-hw]`

`javap -v` on the freshly-extracted `module-info.class` of each jar (Homebrew `openjdk@25`,
`/tmp/claude-1000/n5b55/modinfo/*-module-info.class`, sha256'd — `gx`: `605520df…`, `bajaui`:
`08bc8be2…`, `workbench`: `d8ce0248…`, `alarm`: `0bd42dfa…`) prints the `Module:` attribute's raw
`requires` table, one row per edge, with its access-flag hex and the JVM's own decoded flag names
(`ACC_TRANSITIVE` = `0x20`, `ACC_STATIC_PHASE` = `0x40`, `ACC_MANDATED` = `0x8000` for the implicit
`java.base` edge). This is the literal `Module:` section of each dump, not a summary:

**`niagara.gx@5.0.0.28`** (16 requires):

| Target | Flags (hex) | Decoded |
|---|---|---|
| `java.base` | `0x8000` | `ACC_MANDATED` (implicit) |
| `java.datatransfer` | `0x0` | plain |
| `java.desktop` | `0x20` | `ACC_TRANSITIVE` |
| `java.logging` | `0x0` | plain |
| `java.xml` | `0x0` | plain |
| `javafx.graphics` | `0x60` | `ACC_TRANSITIVE`+`ACC_STATIC_PHASE` |
| `org.apache.xmlgraphics.batik.awt.util` | `0x20` | `ACC_TRANSITIVE` |
| `owasp.encoder` | `0x0` | plain |
| `niagara.baja` | `0x20` | `ACC_TRANSITIVE` |
| `niagara.niagaraAnnotationProcessors` | `0x0` | plain |
| `niagara.bajaScript` | `0x20` | `ACC_TRANSITIVE` |
| `niagara.file` | `0x0` | plain |
| `niagara.web` | `0x20` | `ACC_TRANSITIVE` |
| `niagara.webEditors` | `0x0` | plain |
| `org.eclipse.swt.win32.win32.x86_64` | `0x0` | plain |
| `org.apache.xmlgraphics.batik.transcoder` | `0x0` | plain |

**The decisive asymmetry, read directly off this table**: of the 4 "nominally-mandatory" edges [Block 39]
§39.x flagged, `org.apache.xmlgraphics.batik.awt.util` is the ONLY one carrying `ACC_TRANSITIVE`. The
other 3 — `batik.transcoder`, `swt.win32.win32.x86_64`, `owasp.encoder` — are ALL plain. None of the 4 is
`ACC_STATIC_PHASE` alone (batik.awt.util has no static bit at all; the JavaFX edges do, separately).

**`niagara.bajaui@5.0.0.28`** (20 requires — excerpt, full list read this session): `java.base`
(mandated), `java.datatransfer` (plain), `java.desktop` (`0x20` transitive), `java.logging` (plain),
`javafx.base` (`0x40` static-only, plain), `javafx.controls` (`0x60` transitive+static), `javafx.graphics`
(`0x40` static-only, **plain**, not transitive — a SECOND path to the same target, contrast with `gx`'s
transitive one), `javafx.swing` (`0x60` transitive+static), `niagara.baja`/`niagara.bajaScript`/
`niagara.bajaux`/`niagara.export`/`niagara.file`/`niagara.gx`/`niagara.web` (all `0x20` transitive),
`niagara.entityIo`/`niagara.fox`/`niagara.webEditors` (plain), **`owasp.encoder` (plain — a second,
independent plain `requires` on the same target `gx` also plainly requires)**, `niagara.svgBatik`
(plain).

**`niagara.workbench@5.0.0.28`** (33 requires — excerpt): `com.nimbusds.oauth2.sdk` (plain),
`javafx.base`/`javafx.controls`/`javafx.graphics` (all `0x40` static-only, plain), `javafx.web` (`0x60`
transitive+static), `org.bouncycastle.fips.tls` (`0x40` static-only), **`owasp.encoder` (plain — a
THIRD independent plain requires on the same target)**, `niagara.baja`/`niagara.bajaui`/`niagara.bql`/
`niagara.gx`/`niagara.pdf` (all `0x20` transitive), `niagara.bajaux`/`niagara.box`/`niagara.export`/
`niagara.file`/`niagara.fox`/`niagara.jetty`/`niagara.net`/`niagara.nre`/`niagara.nsh`/`niagara.web`/
`org.eclipse.jetty.websocket.api` (all plain), `jakarta.servlet`/`org.eclipse.jetty.ee11.servlet`/
`org.eclipse.jetty.ee11.websocket.jetty.server` (plain).

**`niagara.alarm@5.0.0.28`** (22 requires — full list): `java.base` (mandated), `java.desktop` (plain),
`niagara.baja` (`0x20` transitive), `niagara.bajaScript` (plain), **`niagara.bajaui` (`0x20`
transitive)**, `niagara.bajaux`/`niagara.box` (plain), `niagara.bql`/`niagara.control` (`0x20`
transitive), `niagara.file`/`niagara.fox` (plain), **`niagara.gx` (`0x20` transitive)**, `niagara.hx`/
`niagara.net`/`niagara.nre`/`niagara.pdf`/`niagara.platform`/`niagara.smartTableHx`/`niagara.web`/
`niagara.webEditors` (plain), **`niagara.workbench` (`0x20` transitive)**, `jakarta.servlet` (plain).

**The chain that matters for B39/B28's original compile**: `niagara.alarm` reaches `niagara.gx` by THREE
independent transitive paths simultaneously — directly (`alarm` → `gx`, transitive), via `bajaui`
(`alarm` → `bajaui`, transitive; `bajaui` → `gx`, transitive), and via `workbench` (`alarm` →
`workbench`, transitive; `workbench` → `gx`, transitive). `gx` is NEVER the module being compiled from
source in that scenario — it is reached only as a dependency, 1-3 hops down `requires transitive` edges.
`[CERT-hw]` (all 4 dumps read in full this session; excerpts above are the load-bearing rows, not the
complete 20/33/22-row tables, which were read in full to confirm no OTHER transitive edge to `gx`
existed and to confirm `owasp.encoder` is independently plain-declared by 3 separate modules —
`gx`, `bajaui`, AND `workbench` — none of which ever propagates it transitively).

## 55.2 — The controlled experiment: 4 compiles, one variable each, copies-to-`/tmp` `[CERT-hw]`

The 4 real jars were copied to `/tmp/claude-1000/n5b55/copies/` (sha256'd: `gx.jar` `3ad3ea91…`,
`bajaui.jar` `1294cf5b…`, `workbench.jar` `487ea4ea…`, `alarm.jar` `fb5b21c3…`) — this is a DELIBERATELY
MINIMAL module-path (only these 4 jars, none of the other 243 config-mirrored modules, no JavaFX/Batik
artifacts), so that EVERY unresolvable module in each run's output is either a TRANSITIVE-reachable
target or a PLAIN target of the module currently in the graph — nothing is masked by an accidental
present-elsewhere copy.

**Probe 1 — baseline, reproduces [Block 39]'s real scenario at smaller scale.** `module angeles.probe1 {
requires niagara.alarm; }`, compiled with `--module-path` = the 4-jar copy set only:

```
$ javac --module-path copies -d out1 src/angeles.probe1/module-info.java
14 errors: niagara.pdf, niagara.web, niagara.bajaScript, niagara.baja,
  org.apache.xmlgraphics.batik.awt.util, javafx.graphics, niagara.bql, niagara.file,
  niagara.export, niagara.bajaux, javafx.swing, javafx.controls, javafx.web, niagara.control
```

Every one of these 14 is a target of SOME `ACC_TRANSITIVE` edge somewhere in the 4-jar closs (`gx` →
`batik.awt.util`/`javafx.graphics`/`baja`/`bajaScript`/`web`; `bajaui` → `javafx.controls`/
`javafx.swing`/`bajaux`/`export`/`file`(already counted)/`web`(already counted); `workbench` →
`javafx.web`/`bql`/`pdf`; `alarm` → `control`(a target `alarm` itself requires transitively — worth
noting `niagara.control` isn't `gx`/`bajaui`/`workbench`'s target at all, it's `alarm`'s OWN direct
transitive requires, absent from this minimal path)). **`org.apache.xmlgraphics.batik.transcoder`,
`org.eclipse.swt.win32.win32.x86_64`, and `owasp.encoder` — all 3 plain, all 3 genuinely absent from this
4-jar path — do NOT appear.** `[CERT-hw]` (`/tmp/claude-1000/n5b55/probe/probe1-output.txt`, reproduced
twice this session with an identical 14/14 error set both times).

**Probe 2 — isolate "gx directly-but-non-root required".** `module angeles.probe2 { requires
niagara.gx; }`, same 4-jar path:

```
$ javac --module-path copies -d out2 src2/angeles.probe2/module-info.java
5 errors: niagara.web, niagara.bajaScript, niagara.baja, org.apache.xmlgraphics.batik.awt.util,
  javafx.graphics
```

Exactly `gx`'s own 5 non-JDK-platform `ACC_TRANSITIVE` targets that are absent from the path (`java.
desktop` is also transitive but IS present — a JDK platform module, resolved automatically, so it does
not error; it is not a confound, its absence-from-the-error-list has a different cause than the other
5's absence). **Still zero errors for `batik.transcoder`/`swt.win32`/`owasp.encoder`** — proving that
DIRECTLY requiring `gx` (rather than reaching it 1-3 hops down through `alarm`) makes NO difference:
what matters is that `gx` is a DEPENDENCY, not the ROOT. `[CERT-hw]`
(`/tmp/claude-1000/n5b55/probe/probe2-output.txt`).

**Probe 3 — does `--add-modules` alone force a dependency's own graph open?** An EMPTY module (`module
angeles.probe3 {}`, no `requires` at all) compiled with `--add-modules niagara.gx` added on top of the
same 4-jar path:

```
$ javac --module-path copies --add-modules niagara.gx -d out3 src3/angeles.probe3/module-info.java
0 errors (1 unrelated naming-convention warning)
```

`--add-modules` makes `gx` OBSERVABLE but, because `angeles.probe3` never `requires` it (no READS edge
into `gx`), `gx` never actually enters the resolved readability graph — none of its requires, transitive
or plain, get force-checked. This confirms readability (an actual `requires` edge FROM something already
in the graph), not mere observability, is what triggers resolution. `[CERT-hw]`
(`/tmp/claude-1000/n5b55/probe/probe3-output.txt`).

**Probe 4 — the decisive positive control: make `gx` the ROOT.** A hand-written `module-info.java` named
`niagara.gx`, with the SAME 15 non-`java.base` `requires` lines as the real descriptor (§55.1's table,
`export`s omitted — irrelevant to requires-resolution), compiled AS THE SOURCE ROOT against a module-path
holding `bajaui.jar`+`workbench.jar`+`alarm.jar` but **not** the real `gx.jar` (excluded to avoid a
module-name collision with the source root):

```
$ javac --module-path copies-no-gx -d out4 src4/niagara.gx/module-info.java
11 errors: javafx.graphics, org.apache.xmlgraphics.batik.awt.util, owasp.encoder, niagara.baja,
  niagara.niagaraAnnotationProcessors, niagara.bajaScript, niagara.file, niagara.web,
  niagara.webEditors, org.eclipse.swt.win32.win32.x86_64, org.apache.xmlgraphics.batik.transcoder
```

**All 11 of `gx`'s own unresolvable requires error — transitive AND plain alike** — including the exact
3 (`owasp.encoder`, `org.eclipse.swt.win32.win32.x86_64`, `org.apache.xmlgraphics.batik.transcoder`) that
were SILENT in probes 1 and 2. The only variable changed between probe 2 and probe 4 is ROOT-ness (`gx`
required-but-not-root vs. `gx`-as-root); the plain-vs-transitive split in the error set flips exactly as
predicted. `[CERT-hw]` (`/tmp/claude-1000/n5b55/probe/probe4-output.txt`, full javac output with
line-anchored `requires` source spans, quoted verbatim above).

**Reproducibility.** All 4 probes were re-run a second time this session (after an initial pass that
established the same counts) with `out1`-`out4` wiped and rebuilt from a clean directory; exit codes
(`1,1,0,1`) and error/warning counts (`14,5,0,11`) were IDENTICAL both times. `[CERT-hw]`.

## 55.3 — The resolution rule, stated precisely `[CERT-hw]` (behavior) / `[INFER]` (spec-level framing)

**The rule, read directly off the 4 probes (`[CERT-hw]`, independently triangulated, not a single-probe
inference):** when compiling a module `R` from source against a `--module-path`, javac force-resolves
(and errors "module not found" if absent) exactly the modules **reachable from `R` by a chain of `requires`
edges where every edge in the chain, EXCEPT POSSIBLY THE FIRST, is `requires transitive`.** Concretely:
- `R`'s own DIRECT `requires` edges (plain or transitive) are always force-resolved — `R`'s source might
  reference any of their exported types.
- For a module `D` already in the graph (reached, but not `R` itself), only `D`'s `requires transitive`
  edges add further targets to the graph — because ONLY those propagate readability onward to `R`. `D`'s
  plain requires are `D`'s own private compile-time need (satisfied when `D` itself was built, in the
  past, by its own author); `R` has no readability edge to them and never needs them present.
- If `D` IS the root being compiled (probe 4), ALL of `D`'s own requires — transitive or plain — are
  `D`'s direct edges by definition, so the first bullet applies to every one of them.

**The `static` modifier is orthogonal to this and did NOT behave as "compile-time-optional" in this
data.** `javafx.graphics` (`requires transitive static` from `gx`) hard-errored in probes 1 and 2 exactly
like the non-static `batik.awt.util` — both are `ACC_TRANSITIVE`, both got force-resolved, both errored
when absent, `static` bit notwithstanding. This directly falsifies the literal reading of "requires
static is compile-time-optional" that this gap's own framing started from: what B39's real Windows-vs-
Homebrew toolchain comparison (§39.4) actually observed — `javafx.*` resolving automatically on the
bundled JRE but NOT on Homebrew's plain JDK — is fully explained by whether a `javafx.*` SYSTEM MODULE is
OBSERVABLE on that JDK's own image (§39.1's `jimage` finding), not by any compile-time exemption `static`
grants. `[CERT-hw]` for the observed behavior (4 probes, one variable each).

**Why `static` still matters (the part this experiment did NOT test, `[INFER]`):** per general JPMS
design (`java.lang.module.Configuration`'s runtime `resolve()`, not javac's compile-time resolution),
`requires static` is documented as optional specifically for the LAUNCHER/runtime module graph — a
module can `requires static X`, compile against it, ship, and run WITHOUT `X` present at runtime as long
as no executed code path actually touches an `X` type (a lazy `NoClassDefFoundError`/`ClassNotFoundError`
at first use, not an upfront resolution failure). A `WebFetch` of Oracle's `Configuration` javadoc this
session returned only a vague, non-verbatim paraphrase of this runtime-optionality behavior — not a
clean citable quote — so this paragraph is marked `[INFER]` (general JPMS-design characterization, not a
source read to completion this session) and is explicitly NOT load-bearing for §55.4's B39-G3 closure,
which rests entirely on the `[CERT-hw]` probes above.

## 55.4 — B39-G3 closed: the anomaly was root-vs-non-root, not a javac quirk `[CERT-hw]`

[Block 39] §39.x asked why `gx.jar`'s 3 other nominally-mandatory `requires` edges never error on either
toolchain. The answer: **they are not "nominally mandatory" in the sense that mattered — none of the 3
(`batik.transcoder`, `swt.win32.win32.x86_64`, `owasp.encoder`) is `ACC_TRANSITIVE`, and `gx.jar` is never
the compile root in any real DashboardPan-rt/`niagara.alarm` build — it is always reached 1-3 hops down
through `requires transitive` edges from `alarm`, `bajaui`, or `workbench` (§55.1). Per §55.3's rule,
plain requires of a non-root dependency are simply never part of the resolved graph, so their absence is
invisible to javac** — this holds on BOTH toolchains B39 tested (Homebrew OpenJDK 25 and the real bundled
Windows `jre/bin/javac.exe`) because the rule is a property of javac's module-resolution ALGORITHM, not
of which JDK build is running it. `org.apache.xmlgraphics.batik.awt.util` is the ONLY one of the 4 that
IS `ACC_TRANSITIVE`, so it alone gets force-resolved through every path that reaches `gx` — matching
B39/B28's observation exactly. **This closes B39-G3**, downgrading it from "unidentified javac quirk" to
a fully reproduced, independently-triangulated structural property of the requires graph, confirmed by
flipping the ROOT variable in probe 4 and watching all 3 previously-silent edges become errors.

## 55.5 — okhttp/jetty artifact inventory in N5 5.0.0.28 `[CERT-hw]`

`bin/ext` ships (versions + sha256, this session):

| Artifact | Version | sha256 (first 16) | Note |
|---|---|---|---|
| `okhttp-5.5.0.jar` | 5.5.0 | `4e30b6c57d27e2d0` | **metadata-only** (12,998 bytes, 5 entries — `META-INF/` + a Kotlin-multiplatform `project-structure-metadata.json`; ZERO `.class` files) |
| `okhttp-jvm-5.5.0.jar` | 5.5.0 | `573001565954ffa3` | the REAL classes jar — 384 `.class` files |
| `okio-jvm-3.18.1.jar` | 3.18.1 | `8d1049d1fc34912e` | okhttp's I/O dependency |
| `jetty-client-12.1.13.jar` | 12.1.13 | `cbb4df4ca5c82d9d` | `HttpClient`, transports |
| `jetty-io-12.1.13.jar` | 12.1.13 | `d414b86d58f5950b` | `ClientConnector` (the actual socket-connect code lives HERE, not in `jetty-client`) |
| `jetty-util-12.1.13.jar` | 12.1.13 | — | supporting utilities |

There is **no single monolithic `jetty.jar`** — Jetty 12 ships as ~30 separate `jetty-*-12.1.13.jar`
modules under `bin/ext`; the gap's phrasing ("okhttp/jetty-client/jetty") is answered as "okhttp-jvm +
jetty-client + jetty-io" (the 3 jars that actually hold connection-establishment code). `okhttp-5.5.0.jar`
being a near-empty placeholder while `okhttp-jvm-5.5.0.jar` holds the real classes is the SAME
Kotlin-multiplatform "unclassified artifact = deliberate placeholder" pattern [Block 39] §39.3 found for
`org.openjfx:javafx-*:25` — a second, independent instance of it in this same install. `[CERT-hw]` (all 6
sha256s computed directly this session; `unzip -l` entry counts for the metadata-only jar).

## 55.6 — okhttp's own connection path: no allowlist, no interceptor hook exercised by default `[CERT]`

Vineflower-decompiled `okhttp3.internal.connection.ConnectPlan` (657 lines) and `RealConnection` (393
lines) from `okhttp-jvm-5.5.0.jar` this session. The actual socket-open call:

```kotlin
// ConnectPlan.kt:353-354 (this session's decompile)
1, 2 -> var8 = this.route.address.socketFactory.createSocket()
else -> var8 = Socket(this.route.proxy)
```

followed by a plain `Platform.Companion.get().connectSocket(rawSocket, this.route.socketAddress, ...)`
(`ConnectPlan.kt:365`) — a direct call into the JDK's own `Socket.connect(SocketAddress, int)`, the exact
primitive [Block 15] §15.1 already confirmed N5's `SecurityAgent` instruments for AUDIT ONLY (no
`checkPermission`). A full read of `ConnectPlan.kt` (all 657 lines) and `RealConnection.kt` (all 393
lines) plus a `grep -ni` sweep for `checkConnect|SecurityManager|Permission|allowlist|denylist|blocklist|
blacklist|whitelist` across `okhttp3/internal/connection/*.kt`, `okhttp3/Dns.kt`, and
`okhttp3/internal/proxy/*.kt` returns **zero hits** — no destination-gating logic exists anywhere in the
connection-establishment path.

**The only pluggable extension points are caller-supplied, opt-in, and unpopulated by default:**
`okhttp3.Dns` (`Dns.kt:44-48` — `Companion.SYSTEM` is the default, a plain `InetAddress`-backed lookup,
no filtering); `java.net.ProxySelector` (`okhttp3.internal.proxy.NullProxySelector.kt:11-18` — the
built-in default always returns `Proxy.NO_PROXY`, unconditionally, for ANY URI — literally cannot deny a
destination, it has no logic branch that could); `javax.net.SocketFactory` (used at `ConnectPlan.kt:353`,
supplied via `OkHttpClient.Builder.socketFactory(SocketFactory)`, `OkHttpClient.kt:687`); and
`okhttp3.Interceptor` via `Builder.addInterceptor`/`addNetworkInterceptor` (`OkHttpClient.kt:525,563`).
`AddressPolicy` (`okhttp3/internal/connection/AddressPolicy.kt`, 22 lines, read in full) is NOT a
host-policy class despite its name — its 3 fields (`minimumConcurrentCalls`, `backoffDelayMillis`,
`backoffJitterMillis`) are connection-pool CONCURRENCY/BACKOFF tuning, unrelated to destination
filtering. **None of these 4 real extension points is populated with any filtering logic by okhttp
itself** — they are pure caller-configuration seams; okhttp's own default wiring (`NullProxySelector`,
`Dns.SYSTEM`, a plain default `SocketFactory`) performs no gating. `[CERT]` (`ConnectPlan.kt:353-354,365`,
`RealConnection.kt` full read, `Dns.kt:11-48`, `NullProxySelector.kt:11-22`, `AddressPolicy.kt:1-22`,
`OkHttpClient.kt:351-687` — all read directly this session from
`/tmp/claude-1000/n5b55/decompiled-okhttp/out/`).

## 55.7 — Jetty's `ClientConnector`: same picture, plus a listener that CANNOT veto `[CERT]`

Vineflower-decompiled `org.eclipse.jetty.io.ClientConnector` (from `jetty-io-12.1.13.jar`) and
`org.eclipse.jetty.client.HttpClient`/`AbstractHttpClientTransport`/
`AbstractConnectorHttpClientTransport`/`transport.HttpClientTransportDynamic`/
`transport.HttpClientTransportOverHTTP` (from `jetty-client-12.1.13.jar`) this session.
`ClientConnector.connect(SocketAddress, Map)` (`ClientConnector.java:263-325`) goes straight from
resolving the target address to opening a raw `SocketChannel`/`DatagramChannel` and calling
`socketChannel.socket().connect(address, timeout)` (blocking path, `:299`) or `socketChannel.connect
(address)` (non-blocking path, `:304`) — the identical JDK primitives, again bottoming out at the same
`Socket`/`SocketChannel.connect` calls [Block 15] confirmed are audit-only in N5. A `grep -ni` sweep for
the same security-token list across every decompiled Jetty file this session (`ClientConnector.java`,
`HttpClient.java`, `AbstractHttpClientTransport.java`, `AbstractConnectorHttpClientTransport.java`,
`HttpClientTransportDynamic.java`, `HttpClientTransportOverHTTP.java`) returns **zero hits**.

**The one candidate extension point — `ConnectListener` — is structurally incapable of vetoing a
connection.** `ClientConnector.notifyConnectBegin()` (`ClientConnector.java`, read in full):

```java
private void notifyConnectBegin(SocketChannel socketChannel, SocketAddress socketAddress) {
   for (ConnectListener listener : this.listeners) {
      try {
         listener.onConnectBegin(socketChannel, socketAddress);
      } catch (Throwable x) {
         LOG.info("failure notifying listener {}", listener, x);
      }
   }
}
```

Every listener callback is wrapped in `catch (Throwable x)` that only LOGS the exception — even a
listener that THROWS to try to abort the connection has that throw caught and discarded; `connect()`
proceeds to the real `socketChannel.connect(...)` call regardless (`ClientConnector.java:288-315`, read
in full — no branch reads a listener's return/throw to decide whether to proceed). This is a STRONGER
negative than okhttp's: Jetty ships an observability hook shaped like it COULD gate, and the
implementation explicitly prevents it from doing so. `[CERT]` (`ClientConnector.java:105-325` and the
`notifyConnectBegin`/`notifyConnectSuccess`/`notifyConnectFailure` block, all read directly this session
from `/tmp/claude-1000/n5b55/decompiled-jetty/io-out/`).

## 55.8 — N4's `organized/` corpus: Niagara's own okhttp usage never sets a gate either `[CERT]`

A `ripgrep -j16` sweep of the full `/home/cristian/niagara-research/organized/` tree (4.8 GB) for
`OkHttpClient\.Builder`, `addInterceptor`, `\.proxySelector\(`, `ProxySelector`, `\.socketFactory\(`,
`SocketFactory`, `ClientConnector` returns 548 raw hits; narrowed per-token and READ (not sampled):

- **`OkHttpClient.Builder`: 10 files, all tracing to exactly 3 Niagara-authored classes** —
  `httpClient/httpClient-rt/vineflower/com/tridium/httpClient/comm/transport/okHttp/
  BOkHttpTransport.java` (the exact class [Block 15] §15.2 already read in N5's `httpClient.jar`, now
  independently confirmed present in N4's decompiled tree too), `awsUtils/awsUtils-rt/vineflower/
  com/tridium/awsUtils/rest/AwsRestClient.java`, and `cloudLink/cloudLink-rt/vineflower/
  com/tridium/cloudLink/transport/BHttpTransport.java`. All 3, read in full this session, call
  `.sslSocketFactory(getSocketFactory(), trustManager).hostnameVerifier(new NoOpHostnameVerifier())` —
  TLS client-certificate/trust-manager wiring (mutual-TLS to Niagara's own cloud endpoints), paired with
  a **`NoOpHostnameVerifier`** that DISABLES hostname verification (a trust WEAKENING, not a
  destination-restricting gate). **None of the 3 calls `.addInterceptor(...)`, `.proxySelector(...)`,
  `.dns(...)`, or the plain (non-TLS) `.socketFactory(...)`** — confirmed by grepping each file for those
  4 tokens directly (`BOkHttpTransport.java:38-192`, `AwsRestClient.java:35-157`,
  `BHttpTransport.java:45-278` — all read in full).
- **`addInterceptor`: every hit is INSIDE the okhttp/Apache-HttpClient LIBRARY's own decompiled source**
  (`okhttp3/OkHttpClient.java`/`.kt` — the library implementing its own public builder method — and
  Apache `httpcore-nio`'s unrelated `ServerBootstrap`), never a Niagara call site.
- **`ClientConnector`: zero hits anywhere in the 4.8 GB N4 tree.** No N4 driver or transport customizes
  Jetty's `ClientConnector` at all.
- **`ConnectListener`: zero hits matching Jetty's type.** The 26 raw matches are all `opcUaCore`'s own
  unrelated `com.prosysopc.ua.stack.*` classes (`ListenableSocketChannel`, `AsyncServerSocket`,
  `ConnectionMonitor` etc.) — a different OPC-UA stack's internal naming, confirmed by path and full read
  of 2 representative files, not Jetty's `org.eclipse.jetty.io.ClientConnector.ConnectListener`.

`[CERT]` (every cited file opened and read this session from `/home/cristian/niagara-research/
organized/`, not summarized from the `ripgrep` hit list alone).

## 55.9 — B15-G2 verdict: the "audit-only, no gate" finding holds at the library layer too `[CERT-hw]`

**CONFIRMED, extending [Block 15] §15.6's verdict one layer deeper.** Neither okhttp nor Jetty ships any
independent host-allowlist, destination-deny, or interceptor-style gate of its own that would apply
"regardless of Niagara's usage" (the exact question B15-G2 asked): both libraries' connection-
establishment code bottoms out at the same unaudited-beyond-logging JDK `Socket`/`SocketChannel.connect`
primitives [Block 15] §15.1 already showed N5's `SecurityAgent` only AUDITS (never blocks); both expose
ONLY caller-populated extension seams (`Dns`, `ProxySelector`, `SocketFactory`, `Interceptor` for okhttp;
`ConnectListener` for Jetty, and that one is explicitly non-vetoing by construction — §55.7); and a
4.8 GB sweep of N4's actual decompiled driver corpus confirms Niagara's OWN code, across every product
generation checked (N4's `httpClient`/`awsUtils`/`cloudLink` AND N5's `httpClient.jar`/`nre.jar` per
[Block 15] §15.2), populates ONLY the TLS trust seam (`sslSocketFactory`+`hostnameVerifier`, and even
THERE weakens rather than strengthens verification via `NoOpHostnameVerifier`) — never the destination-
gating seams (`Dns`, `proxySelector`, plain `socketFactory`, `addInterceptor`, `ConnectListener`). The
"no network-egress gate" finding [Block 15] sealed at the Niagara-usage layer holds with equal force one
layer down, at the library-internals layer B15-G2 specifically asked about.

## 55.x — Self-verify

This is a **build/PoC (§19) block for §55.1-§55.4** (live `javac`/`javap` command output, LIVE-BUILD
BLOCKS convention per [Block 9]/[Block 16]/[Block 28]/[Block 39]) and a **static decompiled-tree evidence
block for §55.5-§55.9** (same convention as [Block 15]).

- **Reproducibility check** — all 4 probes (§55.2) were rebuilt from a clean `out1`-`out4` a second time
  this session; exit codes (`1,1,0,1`) and error counts (`14,5,0,11`) were identical both times.
- **Token check** — every quoted error line, every `requires` flag-table row, every decompiled `file:line`
  citation (`ConnectPlan.kt:353-354,365`, `Dns.kt:11-48`, `NullProxySelector.kt:11-22`,
  `AddressPolicy.kt:1-22`, `OkHttpClient.kt:351-687`, `ClientConnector.java:105-325`,
  `BOkHttpTransport.java:38-192`, `AwsRestClient.java:35-157`, `BHttpTransport.java:45-278`) was read
  directly from the cited decompiled/scratch file this session, not recalled — **≈24 distinct
  load-bearing tokens**, all mechanically sourced from `javac`/`javap`/`ripgrep`/direct `Read` output
  captured this session.
- **Marker tally** — literal `verify-block.sh` output, run this session from `/home/cristian/
  niagara5-research`:

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh niagara5-block55.md .
== verify-block: niagara5-block55.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 21  (adj 19)
   [CERT-live] 0
   [CERT] 8  (adj 7)
   [CERT-doc] 0
   [CERT-web] 1  (adj 0)
   [CERT-a] 0
   [INFER] 6  (adj 4)
-- ratio -- [INFER]/[CERT*] = 4/26 = 0.15
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  AddressPolicy.kt:1-22 / AwsRestClient.java:35-157 / BHttpTransport.java:45-278 /
           BOkHttpTransport.java:38-192 / ClientConnector.java:105-325,263-325,288-315 /
           ConnectPlan.kt:353,365 / Dns.kt:11-48,44-48 / NullProxySelector.kt:11-22,11-18 /
           OkHttpClient.kt:351-687,687  (not in target: beautified-temp/decompiled — not
           script-verifiable)
   resolved 0 of 15
   WARN    resolved 0 of 15 — no file paths resolved. Set SOURCE_ROOT if source files live in a
           separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

  **Declared per METHODOLOGY §11's decompiled-tree rule**: `verify-block: 0 resolved (all extern —
  15 citations point into `/tmp/claude-1000/n5b55/decompiled-{okhttp,jetty}/out/`, ephemeral scratch,
  reproducible from the sha256'd jars cited in §55.5); citation gate = inline token-verify.` This is the
  EXPECTED signature for a decompiled-tree evidence block ([Block 15] §542-547 precedent, quoted in
  METHODOLOGY §11) — every one of the 15 was opened and read directly this session (§55.6/§55.7), not
  inferred from a class name. The `[CERT-hw]` half (§55.1-§55.4, `modinfo`/`probe` scratch trees) is
  ALSO `extern` by the same rule but is the DOMINANT, higher-certainty marker (21 raw/19 adjusted) —
  live `javac`/`javap` command output captured this session, matching the LIVE-BUILD BLOCKS convention.
  Ratio 0.15 (adjusted 4/26) is low and expected for a `standard`/evidence block whose 2 halves are both
  freshly-read primary evidence, not synthesis. The single `[CERT-web]` (§55.3's `WebFetch`) is adjusted
  to 0 — it was explicitly NOT used as a citation anchor (marked `[INFER]` instead) precisely because the
  fetched content was a non-verbatim paraphrase, not a clean quote; the tool still counts the bracketed
  mention of the marker name in that explanatory sentence, which is the same self-referential-quoting
  inflation [Block 39]/[Block 15] both documented.

- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block55.md`. Per
  task scope (single-block deliverable, no other repo file touched, same convention as [Block 15]/
  [Block 39]), `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated this session — left
  to the orchestrator, including flipping B39-G3/B15-G2's rows from `pending` to covered-by-B55.
- **MCP-doc snapshots** — N/A for the load-bearing claims (all `[CERT-hw]`/`[CERT]`). One `WebFetch` this
  session (Oracle's `java.lang.module.Configuration` javadoc, §55.3) returned only a non-verbatim
  paraphrase — NOT used as a citation anchor, explicitly marked `[INFER]` and non-load-bearing instead of
  snapshotted, per the honesty rule over forcing a weak source into a stronger marker.

## 55.x — Child gaps

- **B55-G1** — Whether the same root-vs-transitive resolution rule (§55.3) holds identically under the
  REAL bundled Windows `jre/bin/javac.exe` (not just Homebrew OpenJDK 25) was not re-tested here — [Block
  39] §39.4 already showed the two toolchains agree on the OUTCOME for the original 1-vs-3 anomaly, but
  the 4-probe ROOT-vs-non-root isolation (§55.2) was only run against Homebrew this session.
  Cross-toolchain confirmation of the ISOLATED rule (not just the aggregate outcome) remains open.
- **B55-G2** — Whether `okio-jvm-3.18.1.jar` (okhttp's I/O dependency, inventoried in §55.5 but not
  decompiled) contributes anything relevant to connection establishment (buffering only, expected, but
  not directly confirmed by reading its source this session).
- **B55-G3** — A `[CERT-hw]` LIVE reproduction of either finding on a running N5 station/build was not
  attempted — same class of gap [Block 9]/[Block 15]/[Block 16]/[Block 28]/[Block 39] all left open, now
  applying to two more findings.
- **B55-G4** — `okhttp-5.5.0.jar` being a metadata-only Kotlin-multiplatform placeholder (§55.5) mirrors
  [Block 39] §39.3's `org.openjfx:javafx-*` "Empty" gotcha exactly, but whether ANY N5-shipped module
  actually declares a bare (unclassified) `requires okhttp` that would hit this same empty-artifact trap
  was not checked — a third instance of the pattern, if one exists, is unconfirmed.

## 55.x — Connections

- **[Block 39] §39.x** — direct parent; this block closes **B39-G3** with a fully reproduced, 4-way
  triangulated causal mechanism (root-vs-non-root graph membership), refining/replacing B39's own
  "static is compile-time-optional" hedge with a `[CERT-hw]`-backed correction (static is orthogonal;
  transitive-vs-plain + root-vs-non-root is the real axis).
- **[Block 15] §15.x** — direct parent; this block closes **B15-G2**, extending §15.1/§15.2's
  Niagara-usage-layer "audit-only, no gate" verdict down into the okhttp/Jetty LIBRARY layer itself, and
  independently re-confirms §15.2's `BOkHttpTransport.java`/`sslSocketFactory`+`NoOpHostnameVerifier`
  finding from the N4 side of the corpus (a second, independent read, not a copy of B15's citation).
- **[Block 28]** — the original PoC/stub-jar work both B39 and this block build on; §55.1's `gx`/`bajaui`/
  `workbench`/`alarm` module chain is the same one B28's original stub-jar workaround target.
- **[Block 9]/[Block 16]** — the `--module-path`/scratch-copy PoC conventions this block's §55.2
  experiment follows (copy real jars to `/tmp`, never write to the install/config roots).
