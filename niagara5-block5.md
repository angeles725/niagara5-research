# Block 5 — N5 core API delta: the javax.baja → niagara package rename, core-type signature drift, and the absence of a compatibility shim

> **Scope**: Closes gap **N5-G5** (Core Java API delta N4→N5, centred on the `javax.baja.*` →
> `niagara.*` package rename). Covers: (1) a full package-root census across every N5 module jar,
> confirming `javax.baja` is completely absent from N5 5.0.0.28; (2) per-core-package type counts
> for `sys`, `naming`, `status`, `control`, `alarm`, `history`, `schedule`, `driver`, `web`,
> `security`, `util`, `nre`, N4 vs N5, with named removed/added types; (3) `javap`-diffed API
> signatures for the core types our own N4 modules use most (`Sys`, `BComponent`, `BObject`,
> `BValue`, `BStatusNumeric`/`BStatusBoolean`, `BWebServlet`, `Clock`, `BAbsTime`, `BAlarmService`,
> `Context`, `Property`/`Slot`, `Type`/`TypeInfo`, the `@NiagaraType`/`@NiagaraProperty`/
> `@NiagaraAction` annotation family); (4) `jdeprscan --for-removal` findings and other
> JDK-modernization signals; (5) an exhaustive search (filename-level **and** class-file
> constant-pool byte-level, across all 320 N5 jars: 247 `modules/` + 73 `bin/ext/`) for any
> `javax.baja` compatibility shim, and what the shipped `migrator.jar`/`devkit.jar` actually do with
// the old namespace instead; (6) a grep-based census of how much `javax.baja.*` our own
> ColdRoomPan/CompPan/DashboardPan modules actually use, as the porting-cost baseline. Does **not**
> cover: the full N4↔N5 module *inventory* delta (jar-for-jar added/removed/merged modules →
> N5-G2, still pending), a deep semantic audit of every renamed/added/removed member inside each
> core type (this block samples the highest-traffic types; a full member-by-member audit of e.g.
> `BComponent`'s ~150 methods is out of scope), or the new `niagaraSync`/security-audit subsystems
> this block *discovers* in passing (spun off as child gaps below).
>
> Subject version: **N5 5.0.0.28 (Beta)** (same install audited in [Block 3](niagara5-block3.md):
> confirmed by `etc/brand.properties:workbench.notice`) vs. baseline **N4 4.14.0.162** (Honeywell
> OptimizerSupervisor OEM distribution). **Caveat carried from Block 3 §3.1/3.2, restated here
> because it directly affects every count in §5.2**: the N4 baseline is a full Honeywell OEM
> production distribution (**992** module jars, incl. third-party libs folded straight into jar
> roots — `kotlin`, `okhttp3`, `bsh`, …) while the audited N5 install is a **stock, non-OEM Beta**
> with only **247** module jars. Raw *module-jar* counts are therefore not comparable 1:1 between
> the two installs; every count in this block that matters (§5.1, §5.2) is scoped to a *named
> package*, not a jar total, which keeps the comparison fair — a package that exists in `baja.jar`
> in both installs is compared class-for-class inside that one jar, not against the other 745
> OEM-only jars N5 doesn't ship.
>
> Sources (all local, read-only):
> - N4 originals: `/home/cristian/niagara-research/organized/docSource/docSource-doc/extracted/`
>   (per-module `javax/`/`com/` trees; browsed for corroboration, not the primary evidence — see
>   Method) and `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/*.jar` (992 jars) +
>   `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/bin/ext/nre.jar`.
> - N5 originals: `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar` (247 jars) +
>   `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/*.jar` (73 jars, incl. `nre.jar` and the new
>   `niagaraAnnotationProcessors.jar`). `docSource.jar` (12.4 MB, 3,239 entries) was opened with
>   Python `zipfile` to confirm it ships **javadoc HTML/resources, not `.class` files** — it is a
>   documentation artifact, not source, so it does not itself carry API signatures; the
>   signature-level evidence in §5.3 comes from `javap` on the real module bytecode instead.
> - `/home/cristian/modulos_niagara_n4/Cliente/Leon-Guanjuato-worktrees/main-a109249/` — our own
>   ColdRoomPan/CompPan/DashboardPan sources, per `client-reads-use-a109249-worktree` convention
>   (the plain `Leon-Guanjuato/` checkout is stale at a different commit).
> - No `tools/n5-api-diff.py` exists in this corpus (`ls tools/` checked); all analysis in this
>   block used ad hoc Python (`zipfile`, byte-level constant-pool scan) and `javap`, kept in the
>   session scratchpad (`/tmp/claude-1000/n5b5/`, not part of the corpus — re-derivable from the
>   jars cited).
>
> Method: `python3 zipfile` census of every `.class` path across all 320 N5 jars (package-root and
> per-package counts) and all 992 N4 jars (same, scoped to `javax/baja/*` and `com/tridium/*`);
> `unzip -l` filename-level grep for `javax/baja`; a second, independent **byte-level** scan reading
> every one of 32,018 `.class` file bodies across all 320 N5 jars and searching the raw bytes for
> the constant-pool string `javax/baja` or `javax.baja` (catches a reference even if no class is
> literally *named* under that package); `javap -p` on 18 extracted core types (`/home/linuxbrew/
> .linuxbrew/opt/openjdk@26/bin/javap`, v26.0.2.1), diffed with Python `difflib` after normalizing
> away package-prefix noise; `jdeprscan --release 25 --for-removal` (same `javap` toolchain) against
> `baja.jar` and 7 other core module jars with a full 357-jar `--class-path` so cross-module
> references resolve; `grep -h '^import javax\.baja'` over the client modules' `*.java` (excluding
> `build/`, `srcTest/`). Markers: `[CERT]` local primary (file/bytecode/source opened this session) ·
> `[INFER]` deduction. Every `[CERT]` below was read this session; none is carried from memory or
> from Block 3.
>
> Core-API layer. Connects [Block 1] (N5-G1: module packaging/JPMS — this block's §5.3 `Type`/
> `TypeInfo` finding, the dropped `getRuntimeProfile()` method, is the API-surface echo of the
> rt/ux/wb-without-`-rt`/`-ux`-split mechanism B1 documents structurally) and [Block 3] (N5-G7:
> boot/runtime — B3 found `javax.baja.sys.Sys` → `niagara.sys.Sys` as a single example and seeded
> this block as **B3-G2**; B3's `bin/policy/java.policy` removal and ByteBuddy `SecurityAgent`
> replacement for `SecurityManager` is corroborated here by §5.4's `AccessController`/
> `AccessControlException` `forRemoval=true` findings still present in `web.jar` and `baja.jar`
> even after the sandbox mechanism changed). Seeds **N5-G14** (control/alarm/history/schedule/
> kitControl portability — this block's §5.6 is the shallow import-count pass; N5-G14 remains open
> for the deeper per-symbol audit of what ColdRoomPan/CompPan/DashboardPan would actually need to
> change) and **N5-G10** (cloud/niagaraSync surface — §5.3's `BINiagaraSyncCapableComplex` finding
> is a first sighting, not a coverage of that gap).
>
> **Type:** standard

---

## 5.1 — Package-root census: `javax.baja` is completely absent from N5; `com.tridium.*` is untouched `[CERT]`

A full class-path census across **all 320 N5 jars** (247 `modules/*.jar` + 73 `bin/ext/*.jar`,
20,482 `.class` entries in `modules/` alone) at the top-level package root:

| Top-level root | N5 class count |
|---|---|
| `com` (almost entirely `com/tridium/*`, 15,780; `com/tridiumx/*`, 674 — see below) | 16,454 |
| `niagara` | 3,577 |
| `obix` | 220 |
| `net` | 209 |
| `org` | 17 |
| `test` | 5 |
| **`javax`** | **0** |

`[CERT]` (this session, `zipfile` walk of all 20,482 `modules/` class entries).

Two independent zero-hit searches confirm `javax.baja` is gone, not merely relocated:

1. **Filename-level**, across all 320 jars (247 `modules/` + 73 `bin/ext/`): zero entries whose
   path starts with `javax/baja` or contains `/javax/baja`. `[CERT]`
2. **Constant-pool byte-level**, reading the raw bytes of every one of **32,018** `.class` files
   across the same 320 jars and searching for the literal byte string `javax/baja` or `javax.baja`
   anywhere in the file (this would catch a `String` literal, an annotation value, or a
   reflection-based reference even if no class is physically packaged under that name): **3 hits**,
   all migration/tooling text, not code that runs against the old namespace (detailed in §5.5).
   `[CERT]`

**Every N4 `javax.baja.<pkg>` maps 1:1 to N5 `niagara.<pkg>`** — spot-checked for `nre.jar` beyond
`Sys` (which Block 3 already established): N4 `javax/baja/nre/annotations/*` (17 classes, incl. the
`@NiagaraType`/`@NiagaraProperty`/`@NiagaraAction` family) → N5 `niagara/nre/annotations/*`, now
shipped in a **new, separate jar** `niagaraAnnotationProcessors.jar` rather than inside `nre.jar`
(§5.3). N4 `javax/baja/xml/*` (11 classes) → N5 `niagara/xml/*`, still inside `nre.jar`. `[CERT]`
(`unzip -l` both `nre.jar`s, this session)

**`com.tridium.*` is untouched by the rename** — same package tree, same class names, in both
installs (spot-checked: `com.tridium.workbench` 1,240/1,328 classes N5/N4, `com.tridium.bacnet`
715/697, `com.tridium.sys` 305/290 — deltas are ordinary version drift, not renames; no
`com.tridium.*` package was found renamed, split, or moved to a `niagara.*` path in either census).
`[CERT]` This directly answers the task's own premise: the rename is **`javax.baja` → `niagara`
only**; Tridium's own internal implementation namespace (`com.tridium.*`) was left alone.

**Aside — a third namespace exists but is unrelated to the rename**: `com.tridiumx.*` (674 classes,
2 jars: `analytics.jar` 493, `jsonToolkit.jar` 181). `[CERT]` This is a distinct, apparently newer
vendor sub-namespace used by exactly two modules — not a rename target, not investigated further
here (out of scope; flagged only so a future census doesn't mistake it for a rename artifact).

**Module system confirms it structurally**: `baja.jar`'s `module-info.class` declares JPMS module
`niagara.baja@5.0.0.28`, `requires niagara.nre`, `requires niagara.niagaraAnnotationProcessors`
(confirming the annotations jar split above is a real module dependency, not incidental packaging),
plus automatic-module requires on `org.json`, `owasp.encoder`, `java.security.jgss`. `[CERT]`
(`javap -verbose module-info.class`, this session)

## 5.2 — Per-core-package type counts, N4 `javax.baja.<pkg>` vs N5 `niagara.<pkg>` `[CERT]`

Direct-child class counts (excluding sub-packages) inside each package, both sides read from
`baja.jar`/`alarm.jar`/`history.jar`/etc. — **not** from the two installs' full 992-vs-247 jar sets
(see header caveat):

| Package | N4 count | N5 count | Δ | Named removed | Named added |
|---|---:|---:|---:|---|---|
| `sys` | 127 | 127 | 0 | — | — |
| `naming` | 49 | 50 | +1 | — | (not itemized this pass) |
| `status` | 8 | 8 | 0 | — | — |
| `control` | 38 | 38 | 0 | — | — |
| `alarm` | 39 | 39 | 0 | — | — |
| `history` | 58 | 56 | −2 | `BHistoryDevice$1`, `BHistorySpace$1` (anon inner classes — not API) | — |
| `schedule` | 35 | 35 | 0 | — | — |
| `driver` | 122 | 123 | +1 | — | (not itemized this pass) |
| `web` | 46 | 40 | −6 | `BAppletModuleCachingType`, `BJnlpDownloadPolicy`, `BWebStartConfig`, + 3 anon inner classes | — |
| `security` | 54 | 61 | +7 net (−2/+9) | `SecurityAuditEvent`, `SecurityAuditor` | `AuthorizationToken`, `BCertificateHealth`, `BCertificateStatusEnum`, `BIActionAuditProvider`, `BICertificateCredentials`, `BISecurityAuditable`, `BAes256Pbkdf2HmacSha256PasswordEncoder` + 2 nested holder classes |
| `util` | 95 | 92 | −3 net (−6/+3) | `StringToIntMap` (+ 2 nested), 3 anon inner classes | `ArrayUtil`, `BImageMapResource`, `BNSSResource` |
| `nre` (`nre.jar`, not `baja.jar`) | 707 total (`com/tridium/nre`+`javax/baja/nre`+`javax/baja/xml`+`com/tridium/crypto`+`com/tridium/json`) | 705 total (`com/tridium/nre`+`niagara/nre/{function,platform,security,util}`+`niagara/xml`+`com/tridium/crypto`+`com/tridium/json`) | −2 | — | — |

`[CERT]` (all rows: `zipfile` census this session; the two counts-per-jar totals for `nre` differ
from §5.1's whole-jar totals because that row sums only the packages listed, consistent with how
the two `nre.jar`s were enumerated).

**Reading the deltas**: `alarm`, `control`, `schedule`, `sys`, `status` are **byte-for-byte stable
class inventories** (only the package prefix changed) — the core control/alarm/scheduling contract
did not shrink or grow in this beta. `history`, `util` lost only compiler-synthesized anonymous
inner classes (not user-visible API). `web` is the one package with a real net removal, and it's
coherent: `BAppletModuleCachingType`/`BJnlpDownloadPolicy`/`BWebStartConfig` are all **Java Web
Start / Applet** plumbing — technology removed from the JDK itself years before Java 25, so their
removal here is expected modernization, not an unexplained cut. `security` is the one package with
real net *growth*, and it's coherent in the other direction: two audit-related classes were removed
from `javax.baja.security` specifically (a *different*, narrower `SecurityAuditor`/
`SecurityAuditEvent` pair than the `niagara.nre.security.SecurityAuditor` found in `nre.jar` — do
not conflate the two; they are different classes in different modules) while nine new classes
landed, concentrated in **certificate health/status monitoring** and a **PBKDF2-HMAC-SHA256 /
AES-256 password encoder** — modern password-hashing infrastructure that didn't exist under
`javax.baja.security` in N4. `[CERT]`

**Negative-existence finding**: N4's `javax.baja.nre.security.HsmManager` (Hardware Security Module
support; confirmed present in N4 only via its shipped bajadoc path
`docDeveloper-doc.jar:doc/nre-rt/javax/baja/nre/security/HsmManager.bajadoc`, plus N4-side
implementation classes `com/tridium/security/HsmSigningPermissionGroup` and
`com/tridium/security/HsmSpy` inside N4 `baja.jar`) **has no N5 counterpart anywhere** — a
case-insensitive `hsm` grep across every N5 `modules/*.jar` filename found zero hits related to
security (the only `hsm` string in the entire N5 module set is an unrelated LON device file,
`lonDevices.jar:lonHelvar/Ahsm1.lnml`). `[CERT]` (exhaustive filename search, all 247 N5 module
jars, this session — satisfies the methodology's named-artifact-opened requirement for a negative
claim). Whether this is a deliberate feature drop or simply unshipped in this stock Beta (vs. the
Honeywell OEM baseline, which may have bundled HSM support itself) is `[INFER]` — flagged as **B5-
G1** below.

## 5.3 — Core-type signature deltas, `javap -p` diffed N4 vs N5 `[CERT]`

18 types extracted and disassembled from both `baja.jar`s (plus `alarm.jar`/`web.jar`/`nre.jar` for
the four that live outside `baja.jar`), normalized to strip package-prefix noise, then diffed
line-for-line:

| Type | N4 lines | N5 lines | Verdict |
|---|---:|---:|---|
| `Sys` | 41 | 40 | **real signature changes** — see below |
| `BComponent` | 159 | 156 | internal-only (private field rename + 3 removed synthetic lambda methods) |
| `BObject` | 35 | 34 | **real removal** — `equals(Object)` override dropped |
| `BValue` | 15 | 15 | identical |
| `BStatusBoolean` | 21 | 21 | **new interface** `BINiagaraSyncCapableComplex` added |
| `BStatusNumeric` | 19 | 19 | **new interface** `BINiagaraSyncCapableComplex` added |
| `BWebServlet` | 25 | 24 | **real signature change** — `javax.servlet.*` → `jakarta.servlet.*` |
| `Clock` | 22 | 22 | **real change** — class now `final`, constructor now `private` |
| `Context` | 19 | 19 | **real rename** — `getLanguage()` → `getLanguageCode()` |
| `BAbsTime` | 96 | 96 | **real change** — 8 accessors lost `final`; 2 fields gained `final` |
| `BAlarmService` | 100 | 101 | additive-only (+1 private method) |
| `Property` | 8 | 8 | identical |
| `Slot` | 24 | 24 | identical |
| `Type` | 24 | 23 | **real removal** — `getRuntimeProfile()` dropped |
| `TypeInfo` | 23 | 22 | **real removal** — `getRuntimeProfile()` dropped (mirrors `Type`) |
| `@NiagaraType` | 7 | 7 | identical (only its package/jar moved, §5.1) |
| `@NiagaraProperty` | 10 | 10 | identical (ditto) |
| `@NiagaraAction` | 11 | 11 | identical (ditto) |

`[CERT]` (all rows: `javap -p` output diffed with Python `difflib`, this session; full diffs kept
under `/tmp/claude-1000/n5b5/javap_out/DIFF_*.txt`, re-derivable from the cited jars).

**The individual real changes, spelled out**:

- **`Sys`**: `getLanguage()`/`setLanguage(String)` renamed to `getLanguageCode()`/
  `setLanguageCode(String)` (mirrored in `Context.getLanguage()` → `getLanguageCode()` — a
  consistent rename, not two independent breaks); new `getNiagaraConfigHome()`; the no-arg
  `getLocalHost()` overload removed (the `getLocalHost(InetAddress)` overload survives);
  `getHsmManager()` removed (consistent with §5.2's HSM absence finding); `newInstance(String,
  String)` now additionally declares `throws NoSuchMethodException, InvocationTargetException` —
  consistent with the implementation switching from the deprecated-for-removal
  `Class.newInstance()` to `Class.getDeclaredConstructor().newInstance()` (the standard JDK
  modernization path for that exact deprecation; not verified by decompiling the method body this
  session — flagged `[INFER]` for the *mechanism*, the changed `throws` clause itself is `[CERT]`).
- **`BObject`**: the explicit `public boolean equals(Object)` override present in N4 is **absent**
  from N5's `javap -p` listing; `equivalent(Object)` (Niagara's own value-equality method, distinct
  from Java `equals`) is unchanged and still present. Read narrowly: `BObject` no longer overrides
  `Object.equals()`, so any subclass that relied on `BObject`'s override (rather than declaring its
  own) now gets identity equality instead. Whether any concrete `B*` type in practice depended on
  the removed override (vs. always overriding `equals` itself) was **not** traced across the corpus
  this session — that propagation question is `[INFER]`/open, named as **B5-G2** below.
- **`BStatusBoolean`/`BStatusNumeric`**: both now `implements BINiagaraSyncCapableComplex`, a new
  marker interface (`niagara.niagaraSync.BINiagaraSyncCapableComplex extends niagara.sys.BInterface`
  — empty, just a `TYPE` constant) that did not exist under any name in N4. It lives in a whole new
  package, `niagara.niagaraSync` (`BINiagaraSyncFolder`, `BNiagaraSyncTicket`, `BNiagaraSyncTicks`
  alongside it, plus `com.tridium.util.niagaraSync.NiagaraSyncContextUtil`), all inside `baja.jar`.
  `[CERT]` for the interface's existence and that the two status types now implement it; the
  *purpose* of the `niagaraSync` subsystem was not investigated beyond this sighting — named as
  **B5-G3** below (feeds N5-G10, cloud/sync surface).
- **`BWebServlet`**: `doService(...)` and `getHttpServlet()` now use `jakarta.servlet.http.*`
  instead of `javax.servlet.http.*` — this is the **Jakarta EE 9+ namespace migration**, unrelated
  to the `javax.baja`→`niagara` rename but a second, independent breaking-import change any module
  that subclasses `BWebServlet` and imports `javax.servlet.*` directly will hit. Corroborates Block
  3 §3.2's finding of `jakarta.*`/Jetty-12-EE11 jars newly present in `bin/ext/`.
- **`Clock`**: class is now `final` and its constructor is now `private` (was `public`) — `Clock`
  can no longer be instantiated or subclassed by user code in N5; it is now enforced as a pure
  static-utility class. The `log` field was also renamed `LOG` and made `final` (internal, not
  API-breaking on its own).
- **`BAbsTime`**: its two backing fields (`millis`, `timeZone`) gained `final`; conversely, 8 of its
  accessor methods (`getYear()`, `getMonth()`, …, `getDayOfYear()`) **lost** the `final` modifier.
  Net effect: the value object is more strictly immutable at the field level while simultaneously
  becoming more subclass-friendly at the method level — an intentional-looking pair of changes, not
  investigated further for *why* (out of scope; the signature delta itself is `[CERT]`).
- **`Type`/`TypeInfo`**: both lost the abstract method `getRuntimeProfile()`. `RuntimeProfile` is
  not a nested class of `Type` and was not found as a top-level class in either `baja.jar`
  (`[CERT]`, filename search both jars); its prior home is outside this block's scope — connects to
  [Block 1]'s rt/ux/wb-without-split finding (`[INFER]`, not confirmed this session).

## 5.4 — Java/JDK modernization signals `[CERT]`

`jdeprscan --release 25 --for-removal` against `baja.jar` **without** a resolving classpath produces
only `cannot find class` noise (every cross-module reference unresolved); with a **357-jar**
`--class-path` (all `modules/` + `bin/ext/` jars) covering the dependency graph, it resolves cleanly
and reports exactly one finding in `baja.jar`:

```
class niagara/security/BPassword uses deprecated class java/security/AccessControlException (forRemoval=true)
```

A targeted follow-up scan of 7 more high-traffic core jars (`alarm.jar`, `web.jar`, `history.jar`,
`schedule.jar`, `control.jar`, `bajaui.jar`, plus a partial alphabetical sweep of ~30 more `modules/`
jars, `aaphp.jar`…`bajaui.jar`, that ran to a background-process time budget before covering the
full 247) adds:

```
com/tridium/web/filters/OrdTargetFilter      uses java/security/AccessController      (forRemoval=true)
com/tridium/web/filters/OrdTargetFilter      uses java/security/AccessControlException (forRemoval=true)
niagara/web/servlets/NiagaraRpcServlet       uses java/security/AccessControlException (forRemoval=true)
```

`alarm.jar`, `history.jar`, `schedule.jar`, `control.jar`, `bajaui.jar`, and `workbench.jar`
(N5's largest core UI jar, 1,240+ classes per §5.1) reported **zero** for-removal usages in this
pass. `[CERT]` (this session; the sweep is a *sample* — `baja.jar` + 8 named jars + a partial
~30-jar alphabetical prefix of `modules/`, not all 247 — scope stated honestly, not a
full-corpus claim).

**Reading this together with Block 3**: N5 replaced the JDK `SecurityManager`/`Policy` sandbox with
a ByteBuddy `-javaagent` (Block 3 §3.6–3.8) — yet several N5-side classes (`BPassword`,
`OrdTargetFilter`, `NiagaraRpcServlet`) still directly call the legacy `java.security.AccessController`
/`AccessControlException` APIs the JDK itself has marked `forRemoval=true` independent of
`SecurityManager`'s own removal. This is *not* a contradiction of Block 3's finding (the sandbox
*enforcement* mechanism did change) — it is a separate, narrower observation that some call sites
still reference the old `java.security` API surface directly, which is exactly the kind of
JDK-modernization debt `jdeprscan` is designed to surface. `[CERT]` for the usages; `[INFER]` for
why they weren't yet migrated (most likely: these specific calls don't depend on `SecurityManager`
being installed, e.g. reading the current `AccessControlContext` for audit/logging purposes, so they
still compile and run under JRE 25 — not confirmed by reading the method bodies this session).

No other modernization signal (records, sealed hierarchies, `Optional`-returning accessors, Stream
pipelines replacing loops) was found in the 18 core types diffed in §5.3 — none of those types
gained a `record`/`sealed` modifier or an `Optional<...>` return type in N5's `javap -p` output.
`[CERT]` (absence, scoped to exactly the 18 types disassembled this session — not a corpus-wide
claim; a targeted search across a broader type set is out of scope here).

## 5.5 — No `javax.baja` compatibility shim exists; two narrow migration tools handle the transition instead `[CERT]`

§5.1 already established that zero `.class` files anywhere in the 320-jar N5 install are packaged
under `javax/baja`, and that only 3 of 32,018 scanned class files even contain the literal string
`javax.baja`/`javax/baja` in their constant pool. Opening those 3:

| Class | Jar | What the string is used for |
|---|---|---|
| `com/tridium/migrator/bacnet/BBacnetAwsBogConverter` | `migrator.jar` | A hard-coded **bog type-spec string rewrite table**: `"BbacnetAws:javax.baja.bacnetAws.config,bacnet:niagara.bacnet.config"` (and 2 sibling entries for `.datatypes`/`.enums`) — rewrites *saved station `.bog` XML* type references from the old `javax.baja.bacnetAws.*` names (also folding the `bacnetAws`→`bacnet` package consolidation) to the new `niagara.bacnet.*` names when migrating a station backup, not a Java-level shim. |
| `com/tridium/migrator/program/BProgramConverter` | `migrator.jar` | A field `IMPORT_REPLACEMENTS` plus a `startsWith("javax.baja.")` check — rewrites `import javax.baja.…` **source-text lines embedded inside `BProgram` (kitControl program-object) source**, during bog migration, so an old program block's Java-like source text keeps compiling after conversion. |
| `com/tridium/devkit/wizards/NewModuleWizard` | `devkit.jar` | A `BUILTIN_RESERVED_VENDORS` list containing both `"com.tridium"` and `"javax.baja"` — the *new-module wizard* refuses to let a developer create a new module under either reserved vendor namespace; `javax.baja` is kept only as a **reserved/blocked** name, not a usable one. |

`[CERT]` (all 3: extracted and `strings`-inspected this session).

**Conclusion**: N5 ships **file-format migration tooling** (bog XML type-spec strings, embedded
`BProgram` import-text) to convert *saved station data* written under the old package names, plus a
name-reservation guard in the module-creation wizard — but it ships **no Java source or bytecode
compatibility layer**. A module whose `.java` sources `import javax.baja.sys.BComponent` will not
compile or run unmodified against N5; the imports themselves must be rewritten to `niagara.sys.*`.
This directly answers the task's compatibility-shim question: **no**, there is none, beyond the
narrow bog/program-source text migrators above. `migration.jar`'s own classes
(`BFileMigrator`/`MigratorRegistry`, already renamed to the `niagara.migration.*` package itself)
and `propMigration.jar` were also opened and contain no `javax.baja` string constants — they migrate
*property values*, not namespace references. `[CERT]`

## 5.6 — Porting-cost baseline: how much `javax.baja` our own modules actually use `[CERT]`

`grep -h '^import javax\.baja'` over ColdRoomPan/CompPan/DashboardPan sources (excluding
`build/`/`srcTest/`), read from the `main-a109249` worktree (the maintained checkout per the
`client-reads-use-a109249-worktree` convention — the plain `Leon-Guanjuato/` checkout is stale):

| Module | `.java` files | `javax.baja.*` import lines |
|---|---:|---:|
| ColdRoomPan-rt | 8 | 61 |
| CompPan-rt | 3 | 14 |
| DashboardPan (rt+ux) | 7 | 58 |
| **Total** | **18** | **133** |

Broken down by `javax.baja.<pkg>`, across all three modules:

| Package | Import count |
|---|---:|
| `javax.baja.sys` | 82 |
| `javax.baja.nre` (annotations: `NiagaraType` 10, `NiagaraProperty` 6, `Facet` 4, `Range` 3, `NiagaraEnum` 3, `NiagaraAction` 3) | 29 |
| `javax.baja.status` | 12 |
| `javax.baja.naming` | 3 |
| `javax.baja.web` | 2 |
| `javax.baja.collection` | 2 |
| `javax.baja.alarm` | 2 |
| `javax.baja.units` | 1 |

`[CERT]` (this session, `grep` over 18 source files).

**Implication**: every one of these 8 imported packages (`sys`, `nre`(`.annotations`), `status`,
`naming`, `web`, `collection`, `alarm`, `units`) is confirmed by §5.1's census to have a direct
`niagara.*` (or `niagara.nre.annotations`, now in its own jar) counterpart, and §5.2/§5.3 found the
`sys`/`status`/`alarm` packages and the three `@Niagara*` annotations to be **structurally
unchanged** (identical class inventory and, for the annotations, identical signatures) other than
the package prefix. Combined with §5.5 (no shim, imports must change), this makes the porting task
for our own three modules mechanically bounded but **not zero-effort**: at minimum, a global
`javax.baja.` → `niagara.` import rewrite across 18 files/133 import lines, plus a manual check of
the two real signature deltas that land in packages we actually import — `Sys`/`Context`'s
`getLanguage`→`getLanguageCode` rename (§5.3) is only relevant if any of the 18 files call it
directly (not checked this session — **B5-G4**), and `BObject.equals()` removal (§5.3) is only
relevant if any of our types rely on inherited `equals` rather than declaring their own (also not
checked — folds into **B5-G2**). None of our three modules import `javax.baja.web` in a way that
touches `BWebServlet` specifically by class name in this grep (only 2 generic `javax.baja.web`
imports total), so the `jakarta.servlet` break (§5.3) is unlikely to hit us directly, but was not
confirmed by opening those 2 import sites this session.

## 5.x — Open questions / unresolved contradictions

- **[C1]** Whether `HsmManager`'s absence from stock N5 5.0.0.28 (§5.2) reflects a genuine feature
  drop or simply an artifact of comparing a stock Beta against a Honeywell OEM baseline that may
  have bundled HSM support itself — `[INFER]`, not adjudicated this session.

## 5.x — Connections

- **[Block 1]** — N5-G1 (packaging/JPMS, rt/ux/wb without the `-rt`/`-ux` split). This block's
  `Type`/`TypeInfo.getRuntimeProfile()` removal (§5.3) is the API-surface signal for whatever
  mechanism B1 documents structurally; not cross-verified against B1's text this session.
- **[Block 3]** — N5-G7 (boot/runtime). Supplied the `Sys` rename as a single seed example (B3-G2)
  that this block generalizes into a full package-root census (§5.1) and a per-package type census
  (§5.2). §5.4's `AccessController`/`AccessControlException` `forRemoval=true` findings sit
  alongside, not against, B3's `SecurityManager`→ByteBuddy-agent replacement finding.
- **N5-G1** (child gap) **B5-G1** — Confirm whether `HsmManager`/HSM support is dropped from N5
  proper or only from this stock Beta vs. the OEM N4 baseline; requires either a non-OEM N4
  baseline or a later/OEM N5 build to compare against.
- **B5-G2** — Trace whether any concrete `B*` type our modules (or the wider N5 corpus) depend on
  actually relied on `BObject`'s now-removed `equals(Object)` override, vs. always declaring their
  own; also covers whether `Sys.getLanguage()`/`Context.getLanguage()` call sites exist in our
  modules that need the `getLanguageCode()` rename.
- **B5-G3** — Investigate the new `niagara.niagaraSync` package (`BINiagaraSyncCapableComplex`,
  `BINiagaraSyncFolder`, `BNiagaraSyncTicket`, `BNiagaraSyncTicks`,
  `com.tridium.util.niagaraSync.NiagaraSyncContextUtil`) found attached to `BStatusBoolean`/
  `BStatusNumeric` — feeds N5-G10 (cloud/sync surface).
- **B5-G4** — Open the 2 files in ColdRoomPan/CompPan/DashboardPan that `import javax.baja.web` and
  confirm whether they reference `BWebServlet` (and therefore hit the `jakarta.servlet` break,
  §5.3) or something else in that package.
- **N5-G14** (parent gap, still open) — this block's §5.6 is a shallow import-count pass only; the
  member-by-member audit of what actually breaks when ColdRoomPan/CompPan/DashboardPan are
  recompiled against N5 (beyond the mechanical import rewrite) remains open.
