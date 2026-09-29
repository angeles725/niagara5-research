# Block 117 — Extraction and native-binary fidelity audit: the analysed Java bytes are the vendor's (21,751 classes byte-exact, 356 signed jars verified), but 24,896 nested-jar classes and 958 out-of-pipeline Tridium classes were never decompiled; 45 of 46 single-instrument native claims confirmed by a second instrument, 3 details refuted

> Research for the decompile-fidelity feature (`odd/tasks/decompiler-fidelity-audit.md`, extraction + native
> half; the Java-language lossy-aspects half is [Block 116]). User requirement 2026-09-28: "the decompile must be
> faithful, no inventions, not tainted". This block answers three questions: **(A)** are the bytes the corpus
> analysed exactly the vendor's jar bytes, and was anything inside the install left unanalysed (nested jars,
> multi-release entries, resources, skipped jars, obfuscation, signatures)? **(B)** does every central
> native-binary claim in the corpus rest on at least two independent instruments anchored to a sha256 + VA/offset,
> and do the cited sha256 values match the installed files? **(C)** what is the mandatory sequence for any future
> binary or decompile claim, and which steps are mechanized? Does **not** cover: Vineflower's source-level lossy
> aspects and the docSource differential (that is [Block 116] / T14); the semantic round-trip grader (T15); the
> JxBrowser/Chromium and Microsoft-redistributable natives beyond inventory (third-party, not Tridium code).
>
> Type: evidence (audit). Subject version: **N5 5.0.0.28 (Beta)**. Module jars (READ-ONLY):
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/` (247). Install (READ-ONLY):
> `/mnt/c/Program Files/Niagara/5.0.0.28/`. Decompiled tree: `organized/`. N4 comparison binaries:
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/bin/nre.dll`, `/mnt/c/PowerB/PowerB-4.15.3.28/bin/nre.dll`.
> Method: a new TDD-built census tool `tools/n5-extract-census.py` (RED observed first: 11 tests, 2 failures +
> 9 errors before the script existed; GREEN 11/11); `jarsigner -verify -strict` (JDK 26.0.2) on all 373 jars in the
> install; java-deobfuscator detect mode (sha256 `c1835bd9c9aad4cc…`) with an N4 ZKM positive control; `file`,
> `diec`, `objdump`, `rabin2`/`radare2`, Ghidra 12.1.3 headless (`ExportDecompiledC.java`), a Go-stdlib
> `debug/gosym` pclntab reader written this session, `go version -m`, and the kit's `corroborate-native.sh`.
> Native-claim inventory mapped by one delegated read-only worker (67 rows, `native-claims.tsv`), every
> corroboration then run by this block's author. Markers: `[CERT-hw]` = run this session (artifact under the
> scratch dir below), `[CERT]` = file:line in this repo, `[CERT-web]` = URL + access date 2026-09-28,
> `[INFER]` = derived.
>
> Scratch (session-local, see B117-G8 for durability): `/tmp/claude-1000/-home-cristian-niagara-research/
> 4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b117/`.

---

## 117.1 — A2 CLOSED: every extracted `.class` and every resource is byte-identical to its jar entry — 0 mismatches, 0 missing across 246 modules + 6 bin/ext jars + docSource `[CERT-hw]`

`tools/n5-extract-census.py sweep` hashes every jar entry (sha256) and compares it to
`organized/<mod>/extracted/<entry>` (classes) and `organized/<mod>/resources/<entry>` (every non-`.class`
file); the rule lives in `census_module` (`tools/n5-extract-census.py:145`). Result over the 246 decompiled
module jars (247 minus `docSource.jar`, which the pipeline extracts separately):

| Measure | Count | Mismatched | Missing |
|---|---|---|---|
| `.class` entries vs `extracted/` | 20,723 | 0 | 0 |
| non-class entries vs `resources/` | 20,481 | 0 | 0 |
| bin/ext Tridium jars (6) `.class` vs `organized/_bin-ext/<jar>/extracted/` | 1,028 | 0 | 0 |
| `docSource.jar` entries vs `organized/docSource/` (2,879 `.java` + 1 `module-info.class`) | 2,880 | 0 | 0 |

`[CERT-hw]` (`census-modules-agg.json`, sha256 `cd9068a446926ef7…`; per-module detail `census-modules.json`,
sha256 `66038a4663393ad3…`; exit 0 = clean). Combined with the orchestrator's T13 check (0 jar sha256
mismatches in 252 `recon.json`), the chain *installed jar → extracted bytes* is exact for all 21,751 top-level
jar classes. The extraction itself is a plain `unzip` (`tools/n5-decompile.sh:178`) and the resource copy is a
`find ! -name '*.class'` walk (`tools/n5-decompile.sh:184`) — neither transforms bytes, and the census proves it.

## 117.2 — A1 NARROWED: nested jars are copied verbatim, never decompiled — 98 `LIB-INF` jars in 24 modules carry 24,896 top-level classes with 0 sources, 160 of them Tridium's own; no Tridium code is multi-release, so the pipeline decompiled exactly what a Java 25 JVM loads `[CERT-hw]`

**Nested content.** 103 jar entries are themselves ZIPs: 98 `LIB-INF/*.jar` (24 modules) plus 5 `.bog` files
that are ZIP containers (`kitControl` 1, `tagdictionary` 1, `tls` 3). Vineflower, handed the outer jar
(`tools/n5-decompile.sh:199`), copies nested jars unchanged into `vineflower/LIB-INF/` — e.g.
`organized/devkit/vineflower/LIB-INF/tridium-niagara-slotomatic-library-5.0.2.jar` has the same sha256
(`e7a8f322…`) as the `extracted/` copy `[CERT-hw]` (`sha256sum`, this session). The census counts
**34,605 class entries / 24,896 top-level classes inside nested jars, 0 of them with a `.java`** in
`vineflower/` or `fallback/` `[CERT-hw]` (`census-modules.json`, `nested_top_level_decompiled = 0`).

Tridium-namespace share of nested jars (`com/tridium/`, `niagara/`, `javax/baja/`, same rule as
`tools/n5-classify-binext.py:22`): only **devkit's `n-templates-5.0.54.9.2.jar` (15/15) and
`tridium-niagara-slotomatic-library-5.0.2.jar` (145/145)** — 160 Tridium classes; the other 96 nested jars are
0 % Tridium (Jackson, POI, Batik, Prosys OPC UA SDK, mssql-jdbc, TestNG, …) `[CERT-hw]`. Both Tridium nested jars
are byte-identical to the `etc/m2` copies (§117.4): sha256 `285e6463…` and `e7a8f322…` in both places.

**Multi-release verdict.** No module jar and none of the 6 included bin/ext jars declares `Multi-Release: true`
or has `META-INF/versions/` entries (0 of 253) `[CERT-hw]` (`explore.py` + `mr_resolution`,
`tools/n5-extract-census.py:83`, JarFile semantics: versions honoured only with the manifest flag). Every
Tridium top-level class is therefore a base entry, and the base entry is what the JVM loads on Java 25 — the
pipeline's choice and the JVM's choice coincide for 100 % of decompiled Tridium code. Multi-release content
exists only in third-party jars: 16 nested jars (23 classes overridden on release 25, e.g.
`jackson-core-2.22.2.jar` versions 9/11/17/21 → the JVM selects `versions/21` for 4 classes) and 20 bin/ext /
5 etc/m2 jars (`bcprov-jdk18on-1.85.2.jar` versions 9/11/15/17/25 → 1,361 classes resolve to a version entry;
`bc-fips-2.1.2.jar` 3,269) `[CERT-hw]` (`nonmodule-jars.txt`). Any future decompile of those libraries must
decompile the `versions/<v≤25>/` entry, not the base; nothing in the corpus does so today. Whether Niagara's
module class loader honours Multi-Release for `LIB-INF` jars is `[INFER]`-unknown (not traced).

## 117.3 — A3 CLOSED: non-class payload is complete; 23 native payloads live inside jars, 234 of 2,560 JS files are minified, and no unidentified encrypted blob exists `[CERT-hw]`

All 20,481 non-class entries are present byte-exact in `resources/` (§117.1). By type (top entries):
`.bajadoc` 6,742 · `.png` 3,123 · `.java` 2,871 (docSource) · `.js` 2,560 · `.svg` 2,049 · `.lnml` 1,726 ·
`.font` 704 · `.html` 696 · `.lexicon` 405 · `.xml` 307 · `.hbs` 150 · `.css` 141 · `.palette` 118 · `.jar` 98 ·
`.map` 86 · `.dll` 21 · `.bog` 5 · `.exe` 1 `[CERT-hw]` (`explore.py`).

**Native payloads inside jars** (detected by magic bytes, `native_format`, `tools/n5-extract-census.py:56`):
`aceEdge.jar!rc/bin/ace-tridium-edge-4.15.4.0` (ELF 32-bit ARM, `diec`: GCC 8.3.0 qnx710 — a QNX 7.1 binary),
`ffmpeg.jar!nativeLib/x86_64/` 8 PE DLLs (FFmpeg libs + `ffmpeg-wrapper.dll`, MSVC C++, 24 of 26 exports
`Java_*` — the only JNI library shipped inside a jar), `xprotect.jar!nativeLib/` 14 .NET CLR-4 assemblies
(Milestone VideoOS SDK + `XProtectBridgeService.exe`), and 6 SWT DLLs inside `gx.jar!LIB-INF/org.eclipse.swt…jar`
`[CERT-hw]` (`census-modules.json` `natives`, `file`, `diec`, `r2 iEj`). None of these was ever decompiled by the
pipeline; the .NET ones are decompilable with the kit's `decompile-net.sh` (B117-G4).

**Minified JS.** 234 of 2,560 `.js` files meet the minified rule (longest line ≥ 1,000 B or mean line ≥ 250 B,
`tools/n5-extract-census.py:66`); 86 `.map` source maps ship alongside. Heaviest: `js` 35/76, `docDeveloper`
21/114, `analytics` 18/141, `webEditors` 12/400, `uxBuilder` 11/116 `[CERT-hw]`. Any corpus claim about those
234 files rests on minified code (B117-G3).
**[CORRECTED by [Block 119] §119.6:** the 234 over-count by 102 — only 132 files are truly minified (mean line ≥ 250 B); 102 are readable Babel output caught by the longest-line half of the rule. The 86 maps do not "ship alongside minified JS": 42 map LESS, 42 map readable Babel ES5 with embedded ES2015+ originals, 1 maps underscore, 1 is empty; none of the 234 has a map.]**

**Encoded/encrypted blobs.** Scanning every non-image/non-font/non-archive entry ≥ 256 B for Shannon entropy
≥ 7.2 bits/byte: 956 hits, all identified by magic — 704 gzip (`fonts.jar` `microFont/*.font`), 5 ZIP (`.bog`),
247 PKCS#7 (`META-INF/NIAGARA4.RSA`) — **0 unidentified high-entropy payloads** `[CERT-hw]` (entropy scan, this
session).

## 117.4 — A4 CLOSED for bin/ext, NEW FINDING outside it: the 103 skipped bin/ext jars carry 0 Tridium classes, but 10 Tridium jars in `etc/m2` and `lib/` (958 Tridium classes, 4 of them Kotlin-compiled) sit outside the pipeline entirely `[CERT-hw]`

**bin/ext skip rule verified.** All 109 bin/ext jars (recursive, incl. `bcfips/`, `bcstd/`, `system/`,
`jxbrowser/`, `securityBridge/`) re-classified: the 6 included jars are 67–100 % Tridium (1,022 of 1,028
classes); the 103 skipped jars hold 43,321 classes with **0** under `com/tridium/`, `niagara/`, `javax/baja/`
`[CERT-hw]` (`nonmodule-jars.txt`, matches `organized/_logs/_bin-ext.log` "included=6 skipped=103"). The
`> 0.5` threshold (`tools/n5-classify-binext.py:49`) has no near-miss.

**Tridium code the pipeline never looks at.** The pipeline scans only `modules/` and `bin/ext/`. Also in the
install:

| Location | Jars | Tridium classes | Class version | Notes |
|---|---|---|---|---|
| `etc/m2/repository/com/tridium/tools/*` | 8 | 935 | 65 or 69 | `n-plugin` (722), `slotomatic` (145), `settings` (20), `n-templates` (15), `n-conv-plugin` (14), `utils` (12), `java-utils` (4), `filetypes` (3) |
| `etc/m2/repository/com/tridium/xelem/4.0.3` | 1 | 8 | 65 | |
| `lib/tridium-niagara-baja-doclet-5.0.4.jar` | 1 | 15 (of 23) | 65 | javadoc doclet |

`[CERT-hw]` (`nonmodule-jars.txt`). Earlier blocks decompiled `n-plugin`/`slotomatic` ad hoc into `/tmp` dirs
that no longer exist ([Block 74] header, citing [Block 2]/[Block 49]); there is no durable `organized/` tree for
any of the 10 (B117-G1). **Kotlin:** `n-plugin` (650 of 724 classes carry `Lkotlin/Metadata;`), `n-conv-plugin`
(14/14), `settings` (20/20), `utils` (12/12) are Kotlin-compiled `[CERT-hw]` (constant-pool byte scan, this
session) — [Block 2]'s title already calls `n-plugin` a Kotlin plugin, but a Java decompile of Kotlin bytecode
explains behaviour without being the source; claims read from it carry that caveat (B117-G2). No module jar or
included bin/ext class carries Kotlin, Scala (`ScalaSig`/`ScalaSignature`) or Groovy (`GroovyObject`) markers
(0 of 21,752) `[CERT-hw]` (`jvmlang-preview.txt`).

> **Correction (added by [Block 121], §121.2, §14 cross-block).** The four counts above are reproduced exactly (`evidence/b121/kotlin-census-all.tsv`), but "a Java decompile" is the wrong description of the corpus trees for these jars:
> `organized/_etc-m2/<jar>/vineflower2/` holds Vineflower 1.12.0 **Kotlin-plugin** output (329 `.kt` + 62 `.java` files) with 67 method walls and 6 class walls; a Java-mode run (`--kt-enable=false`) has none. Scope clarification, not a refutation.

**Preview class files:** 0. All 21,752 classes in the 247 module jars + 6 bin/ext jars are exactly
major 69 / minor 0 (no minor 65535) `[CERT-hw]` (`jvmlang-preview.txt`).

**Integrity anchor for the unsigned etc/m2 jars.** The 18 file entries in the 9 Tridium `etc/m2` Gradle
`.module` metadata files carry sha256 values; all 18 match the jar bytes `[CERT-hw]` (`.module` JSON check,
this session). That is a self-consistency anchor, not a signature (the `.module` files are unsigned too).

## 117.5 — A5 CLOSED: no N5 Tridium jar is obfuscated — java-deobfuscator's full detector suite (Zelix, Allatori, Stringer, DashO, Smoke, …) fires 0 obfuscator rules on 252 jars while firing both Zelix rules on the N4 ZKM positive control `[CERT-hw]`

[Block 30] §30.6 already ruled obfuscation out with a class-name ratio and a decompiled-source grep. This block
adds a bytecode-level detector with a positive control. `java-deobfuscator` detect mode
(`/home/cristian/modules/Prototipos/modulos/deobfuscator.jar`, sha256 `c1835bd9c9aad4cc453f8675110fc057f11cd3ca5e8f29b68c67baf086277eea`,
the same tool whose N4 detect logs [Block 90] §90.5 cites) refuses major 69 ("Unsupported class file major
version 69", even with `patchAsm: true` — a tool failure, not a zero). The class-file version bytes were
therefore lowered 69 → 61 in class-only copies (`deobf/patch.py`, sha256 `2fa46fdb…`; method bodies and constant
pools untouched), and detect was run on all 247 module jars + 6 bin/ext jars (253 runs, all exit 0, 0 parse
errors). The positive control, N4 `clCBus-rt.jar` (ZKM per [Block 90] §90.5), run through the same
preparation, fires `RuleSuspiciousClinit` and `RuleSimpleStringEncryption` (Zelix) `[CERT-hw]` (`deobf/pos.out`,
sha256 `972776a6…`).

Across the 253 N5 runs the only rule that ever fires is `RuleSourceFileAttribute`, in 5 jars (`alarm`, `ccn`,
`lonworks`, `platform`, `videoDriver`) — each a package-private secondary top-level class compiled from another
file, e.g. `com/tridium/alarm/CoalesceUuidOnlyInvocation.class` carries `SourceFile:
AlarmClassRouteAlarmInvocation.java` `[CERT-hw]` (`javap -v`, this session). That is standard `javac`
behaviour, not obfuscation. **No N5 module needs a low-fidelity flag for obfuscation.** One fidelity side-note:
Vineflower writes such secondary classes into their own file
(`organized/alarm/vineflower/com/tridium/alarm/CoalesceUuidOnlyInvocation.java`), so the decompiled tree's file
layout does not match the original source layout — relevant to [Block 116]'s lossy-aspects catalog.

## 117.6 — A6 CLOSED: all 247 module jars and all 109 bin/ext jars verify (`jar verified`, entry digests intact); the only failure is the expected untrusted chain; 18 jars are unsigned (all outside the pipeline) `[CERT-hw]`

`jarsigner -verify -strict` (JDK 26.0.2.1, `/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/jarsigner`) on all 373
jars in the install (247 modules + everything under Program Files except `jre/`):

| Result | Count | Where |
|---|---|---|
| `jar verified, with signer errors`, exit 4 | 356 | 247 modules, 109 bin/ext (incl. all 6 Tridium bin/ext jars and the 140 MB `jxbrowser-win64-9.5.0.jar`) |
| `jar is unsigned`, exit 16 | 17 | 15 `etc/m2` jars, `javadoc/niagaraJavadoc.jar`, `lib/tridium-niagara-baja-doclet-5.0.4.jar` |

`[CERT-hw]` (`jarsigner/*.txt`, `jarsigner-summary` pass). In every exit-4 output the only error is "certificate
chain is invalid … PKIX path building failed" plus the `META-INF/` JarFile-vs-JarInputStream ordering warning;
**no digest mismatch, no unsigned entry, no `SecurityException`** in any file `[CERT-hw]`. Exit 4 is jarsigner's
"untrusted chain" bit: every entry's SHA-256 digest matched `NIAGARA4.SF`/`MANIFEST.MF` and the PKCS#7 signature
over the `.SF` verified; only the Tridium signing chain is not in the JDK's cacerts, the case [Block 53] §53.3
reconciled with the runtime's own trust store. Because the outer jar signature covers nested entries, devkit's
two Tridium `LIB-INF` jars are also vendor-anchored (their sha256 equals the unsigned `etc/m2` copies, §117.4).
The pipeline's own `recon.json` `signed: true` only records that a `.SF` file exists
(`tools/n5-decompile.sh:132`); it never verified the signature until this run (§117.10).

The NCS-Agent directory is a signed tree too: `META-INF/MANIFEST.MF` sha256 digests match the `.exe` and `.sig`,
`BOARDUPD.SF`'s manifest digest matches, and `openssl cms -verify -noverify` on `BOARDUPD.RSA` succeeds; the
signer is `CN=Open Board Update, OU=For Development Purposes Only - Do Not Distribute, O=Tridium, Inc` — the
development-certificate observation [Block 18] already made `[CERT-hw]` (openssl, this session).

## 117.7 — B1 CLOSED: native inventory — 21 Tridium-signed MSVC C/C++ PE files in `bin/`, one Go binary (NCS-Agent), 16 third-party JxBrowser/Chromium files, 29 natives inside jars `[CERT-hw]`

`jre/` excluded: `jre/release` is a stock `JAVA_VERSION="25.0.4"` runtime image (module list only; no Tridium
entries). Every other PE/ELF (by magic, not extension) under Program Files:

| File | sha256 (first 16) | Format | Language (diec + imports/RTTI) | Authenticode leaf | JNI exports |
|---|---|---|---|---|---|
| `bin/nre.dll` | `a6317e8b024ed823` | PE32+ DLL | MSVC 19.44 C++ | Tridium, Inc. | 101 of 206 |
| `bin/njre.dll` | `1b8b0074c79dc148` | PE32+ DLL | MSVC C++ | Tridium, Inc. | 0 of 91 |
| `bin/common.dll` | `799c6c8dedfc69aa` | PE32+ DLL | MSVC C++ | Tridium, Inc. | 0 of 400 |
| `bin/lon.dll` | `a0f0dadc86a96d64` | PE32+ DLL | MSVC C++ (MSVCP140) | Tridium, Inc. | 4 of 11 |
| `bin/pcapBacEther.dll` | `d5d4e7eeddf5f925` | PE32+ DLL | MSVC (diec C++; no class RTTI) | Tridium, Inc. | 6 of 6 |
| `bin/alarmDialog.dll` | `90b095755f6c5a10` | PE32+ DLL | MSVC **C** | Tridium, Inc. | 4 of 4 |
| `bin/trayIcon.dll` | `3cff7cc74febc051` | PE32+ DLL | MSVC C++ | Tridium, Inc. | 5 of 5 |
| `bin/cppunit.dll` | `3386491a276acdcb` | PE32+ DLL | MSVC C++ | Tridium, Inc. | — |
| `bin/niagarad.exe` | `64fd6403fe00bc1b` | PE32+ console | MSVC C++ (`JavaLauncher`) | Tridium, Inc. | — |
| `bin/nre.exe`, `station.exe`, `wb.exe`, `wb_w.exe`, `n5mig.exe` | `098b52fb…`, `b166aba5…`, `026622cd…`, `7a99fdc0…`, `95b5deae…` | PE32+ | MSVC C++ (`NreLauncher`) | Tridium, Inc. | — |
| `bin/plat.exe`, `console.exe`, `test.exe` | `86e6878e…`, `d8601f84…`, `21c6020c…` | PE32+ console | MSVC C++ | Tridium, Inc. | — |
| `bin/x86/ldvProxy.exe` | `2876acfa8305eadc` | PE32 (x86) | MSVC C++ (`Lon32`, `WLon32`) | Tridium, Inc. | — |
| `bin/{msvcp140,vcruntime140,vcruntime140_1}.dll`, `bin/x86/{msvcp140,vcruntime140}.dll` | `03e31b7b…` etc. | PE | Microsoft CRT | Microsoft | — |
| `NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe` | `e459956a71949d8f` | PE32+ console, 8 sections | **Go 1.25.12** (buildinfo), `-ldflags=-s -w`, `CGO_ENABLED=0` | none (tree-signed, §117.6) | — |
| `JxBrowser/9.5.0/*` (16) | per `natives-install.tsv` | PE/PE32 | third-party Chromium/TeamDev | not assessed | — |

`[CERT-hw]` (`natives-install.tsv` sha256 `f1317d33…`; `diec`; `objdump -p` imports; `strings` RTTI `.?AV`
type descriptors; Authenticode leaf subject from the PE security directory via `openssl pkcs7 -print_certs`;
`r2 iEj` exports). Language is two-instrument for every Tridium PE (diec's compiler signature + import/RTTI
evidence), with one disagreement kept visible: `diec` says `Go(1.18.X-1.24.0)` for NCS-Agent while the embedded
buildinfo says `go1.25.12` — diec's signature range is stale; buildinfo is authoritative. The Authenticode
*certificate* was extracted, but the PE *digest* was not verified (no `osslsigncode`/`signtool` available,
B117-G5).

## 117.8 — B2 AUDIT: 67 central native claims in 16 blocks; 46 were single-instrument; 45 now CONFIRMED by a second instrument, 1 already superseded, 0 central claim refuted, 3 details refuted; every cited sha256 matches the installed file `[CERT-hw]`

**Twin-binary check (the [niagara B424] risk).** Every sha256 the corpus cites for a native binary matches the
file analysed here: N5 `nre.dll` `a6317e8b…`, `njre.dll` `1b8b0074…`, `n5mig.exe` `95b5deae…`, `niagarad.exe`
`64fd6403…`, NCS-Agent `e459956a…`; N4 4.14.0.162 `nre.dll` `606ff1c6…`, N4 4.15.3.28 `nre.dll` `67d1015e…`;
[Block 113]'s scratch copy `ncsagent.exe` also hashes to `e459956a…` `[CERT-hw]` (`sha256sum`, this session).
Blocks 3, 43, 57, 61, 76 cite no sha256 at all (they read the live install path) — acceptable only because the
install bytes are unchanged, which this check now proves.

**Instrument coverage before this block** (`native-claims.tsv`, sha256 `eb199aa4…`): of 67 rows, 3 had 0
instruments (stat/find structural facts), 46 had exactly 1, 16 had 2, 2 had 3. Blocks 66, 69, 79, 93 make no
native claim. Second-instrument results for the 46 (instrument used → outcome):

| Block § | Claim (short) | First instrument | Second instrument this session | Outcome |
|---|---|---|---|---|
| 43.2 | `nre.dll` pairs `-Dniagara.platform.provider=%s` with `NativePlatformProviderTridium` | `strings` | `rabin2 -zz` + r2 `axt` + `objdump -d` @ `0x1800060be`–`0x1800060e4` | CONFIRMED, and the block's `[INFER — string adjacency]` is now resolved: `buildArgs` loads the class-name string into the first vararg (`[rsp+0x20]`) and the format into `r9`, then calls the `vsnprintf_s` wrapper `0x180004890` — the `%s` IS the constant class name. Detail: in file order the class name precedes the format string (the block says "followed by") |
| 57.1 | `-Dcmdline::` literal; no deny-list strings | `strings` | `rabin2 -zz` + `objdump` (`lea r8` @ `0x18000596a`) | CONFIRMED |
| 61.2 (×4) | njre ADVAPI32 registry-only / no CreateProcess; nre service APIs + `CreateProcessA` | `objdump -x` | `rabin2 -i` | CONFIRMED; completeness detail: nre's ADVAPI32 set also imports `RegDeleteValueA` (7 registry calls, not 6) |
| 61.2→63.1 | exactly one `CreateProcessA` xref, in `restartPlatformDaemon0` | r2 `axt` | `objdump -d` (only ref: `call [rip+…] # 0x18000e1c8` @ `0x1800045dd`) + Ghidra decompile (builds `"plat.exe restartdaemon"`, calls `CreateProcessA`) | CONFIRMED (3 instruments) |
| 63.1 | `njre.dll` has **95** exports, 0 JNI | r2 `iE` | `rabin2 -E`, `r2 iEj`, `objdump -p` EAT size `0x5b`, PE `NumberOfFunctions` | **REFUTED detail: 91 exports** (4 instruments agree); 0 `Java_` CONFIRMED |
| 63.2 | `buildArgs` `strncpy_s`/`strncat_s` then `call buildVMOptions` | r2 `pdf` | `objdump -d` @ `0x180005977`/`0x18000598d`/`0x180005a0b`, IAT names via `rabin2 -i` | CONFIRMED |
| 63.3 | `%s` buffers at `r13+0x624`/`r13+0x8324` | r2 `pdf` | `objdump -d` @ `0x180005c4a`/`0x180005cb1` | CONFIRMED (origins closed by 87.2) |
| 63.4 | 0 `SecurityManager` strings in 5 binaries | `strings` | `rabin2 -zz` (ASCII + UTF-16) | CONFIRMED 0/5 |
| 76.2 (×3) | niagarad imports only njre/kernel32/CRT; no process/SCM APIs; manifest `Tridium.Niagara.Service` 5.0.0.96 | `objdump -x`, `strings` | `rabin2 -l`/`-i`, `rabin2 -zz` (`.rsrc`) | CONFIRMED |
| 3.5 | N5 boot flags: 26 `--add-opens=`, 4 `--add-reads=`, bootclasspath securityBridge, njre `--add-exports` | `strings` | `rabin2 -zz` counts 26/4 + addresses | CONFIRMED |
| 87.1 (×3) | sole `checkFileSignature` caller per DLL; `.jar` filter; `niagara_sig_debug` gates logging only | r2 | `objdump -d` (callers `0x180003603`/`0x180006383`; `exit(0xfa)` in `initPaths` after both loop calls) + Ghidra decompile of `checkFileSignature` (every `DAT_18000f428` test guards only a `fprintf`; return values independent of the flag; SHA256 + `BCryptVerifySignature`) | CONFIRMED; precision: the loop returns −1 after printing "FATAL: %s failed signature check"; the 249/250 exits are in `initPaths`, as §87.1's prose says (self-verify row 3 compresses this) |
| 87.2 (×2) | `this+0x624` built from PATH etc.; `this+0x8324` is the same buffer fed to the signature loop | r2 | `objdump -d` (`lea rsi,[rdi+0x8324]` @ `0x180006f92` → `mov rcx,rsi; call 0x180006280` @ `0x1800071d0`; PATH string ref @ `0x180006dca`) | CONFIRMED |
| 87.3 | `fcn.180004890` = thin `__stdio_common_vsnprintf_s` wrapper | r2 | `objdump -d` (single IAT call `# 0x18000e370`) | CONFIRMED |
| 87.4 (×2) | bootclasspath string live-referenced in `buildArgs`, unconditional; no securityBridge add-reads | r2, `strings` | `objdump -d` (`lea r9` @ `0x180005b2b`, 0 branches in `0x180005ad7`–`0x180005b47`), `rabin2 -zz` | CONFIRMED |
| 87.5 (×2) | `defaultToNonFIPS` chooses bcfips/bcstd; `n5mig.exe` imports nre.dll | r2; `objdump -p` | not re-run (already reversed by [Block 94] §94.8, re-confirmed in the 94.8 row); `rabin2 -l` | SUPERSEDED; import CONFIRMED |
| 87 hdr | copies byte-identical | sha256 | sha256 vs install | CONFIRMED |
| 94.8 (×3) | `defaultToNonFIPS` has 0 xrefs; `initFips` sole setter of `this+0x1002c`, called once from `nre()`; precedence license → CLI → options file | r2 | `objdump -d` (0 refs), raw-qword scan (0), import tables of all 20 bin/ binaries (0 importers), Ghidra decompile of `initFips` | CONFIRMED; precision: the constructor, copy-constructor, `operator=` and `getInstance` also write `+0x1002c` (initialisation) — `initFips` is the sole *policy* setter |
| 94.9 (×2) | njre `--add-exports` in an unconditional block of `buildArgs`; exe→DLL import binding | r2, `objdump -p` | `objdump -d` (`lea rcx` @ `0x180002e02`, 0 branches in `0x180002ddb`–`0x180002e2e`), `rabin2 -i` | CONFIRMED |
| 96.8 / 96.9 | NCS-Agent keystore/p12 strings; `internal/ncsauth`, `internal/keystore/{dpapi,flock}` names, JSON tags | `strings` | `rabin2 -zz` (5/5 strings) + Go-stdlib `debug/gosym` pclntab function names | CONFIRMED |
| 100.1 (×3) | pclntab function VAs (`LoadIdentity 0x1402fd380`, `SaveIdentity`, `decryptAESGCM`, `niagaradshim.Start`, 3× `doJSONPost`); Ghidra-only Go summary | python pclntab walk; Ghidra | `debug/gosym` (independent parser: pclntab at file offset `0x512a40`, 8,005 functions, every cited VA+name identical) + `go version -m` (go1.25.12) | CONFIRMED; Ghidra's "4,209 types" / "4,810 strings" stay Ghidra-only (non-central; the types count is [Block 113]'s B113-G1) |
| 100.5 | N4 4.15.3.28 `nre.dll` carries `-Djava.security.manager` | `strings` | `rabin2 -zz` + r2 `axt` (`buildArgs` @ `0x180006980`) + `objdump` (1 ref) | CONFIRMED |
| 108.1 (×4) | 14 own packages / 279 functions; package split; `DownloadParts` calls; buildinfo | python census, `objdump` | `debug/gosym` (14 packages, 279 functions exact; `vendor/` 214 exact; third-party 398 by module-prefix rule vs the block's 396 — rule-dependent, not refuted) + r2 `pD` of `DownloadParts` (calls `rsmclient.DownloadPartExecute`, `os.OpenFile`, `io.copyBuffer`, `os.Getenv`, `filepath.join`, `os.Exit`; 0 `os/exec` functions in the whole table) | CONFIRMED |
| 113.1 (×4) | moduledata fields; 2,418 typelinks; own type names/fields | python | r2 `pxq` at `firstmoduledata` (`ftab.len` 0x1f46, `minpc` `0x140001000`, `types` `0x1403a0000`, typelinks ptr `0x140510a40`, len `0x972` = 2,418); 91/91 type-name and 107/107 field-name strings present in the binary bytes | CONFIRMED values; **REFUTED detail: the typelinks slice pointer is at moduledata offset `+0x160`, not `+0x158`** (r2 reads `0x1` at `+0x158`; [Block 113]'s own `moduledata.py` reads `vals[44]` = `+0x160`, so only the prose table is wrong). Struct sizes stay single-parser (B117-G6) |
| 113.2 | `InstallSoftware` has 10 distinct call targets, none process-creating | `objdump` + python | r2 `pD` over `0x1403373a0`–`0x140337780` resolved through `debug/gosym` | CONFIRMED (identical 10 targets) |

`[CERT-hw]` for every row (artifacts: `native/*.objdump-d.txt`, `native/*.rabin2-i.txt`, `native/*.zz.txt`,
`native/ghidra-out/{njre,nre}.dll.c` sha256 `4e8df2dd…`/`605553b0…`, `go/gosym-funcs.tsv` sha256 `10943a0e…`,
`go/r2-{downloadparts,installsoftware}.txt`, `go/typename-corroboration.txt`). The three refuted items are
details inside otherwise-confirmed claims: the njre export count (63.1), the typelinks offset (113.1), and the
§43.2 string order. The kit's `corroborate-native.sh` also ran cleanly on `nre.dll` (`status: complete`,
328 functions, staged sha256 = source sha256) `[CERT-hw]` (`native/cn-nre/native-static.v1.json`), so the
sandboxed r2 route is available for future blocks.

## 117.9 — B3 CLOSED: the Go symbol names the corpus recovered from NCS-Agent's pclntab are confirmed by a second, independent parser and by buildinfo `[CERT-hw]`

The binary is built `-ldflags="-s -w"` (no COFF symbol table: `go tool nm` → "no symbols"), so every Go name in
[Block 96]/[Block 100]/[Block 108]/[Block 113] came from pclntab. A second reader built on Go's own
`debug/pe` + `debug/gosym` (not Ghidra, not the blocks' Python) finds the Go 1.20+ `pcHeader` magic `0xfffffff1`
at file offset `0x512a40` in `.rdata` and decodes 8,005 functions whose entry VAs and names match every value
cited in §100.1/§108.1/§113.2 `[CERT-hw]` (`go/gosyms/main.go`, `go/gosym-funcs.tsv`). `go version -m` gives an
independent metadata channel: `go1.25.12`, `path github.com/HON-HCE/tridium-ncs-rsm-agent/cmd/ncs-agent`,
`vcs.revision=8e8f1806a707562ae6ee1649fd55cae41eff42f9`, `-tags=supervisor`, `CGO_ENABLED=0`, and the 10 module
dependencies [Block 108] lists `[CERT-hw]` (`go version -m`, this session).

## 117.10 — C CLOSED: the mandatory fidelity sequence, and what is mechanized today

Every future decompile or binary claim follows this order. A step that was skipped must be named in the block.

| # | Step | Java (jar/class) | Native (PE/ELF/Go/.NET) | Mechanized? |
|---|---|---|---|---|
| 1 | **Locate by content, not by name** — search all jars/dirs (modules, bin/ext, `LIB-INF`, `etc/m2`, `lib/`) | `n5-extract-census.py` nested census; absence rule in the writer prompt | magic-byte scan (§117.7) | partly: modules + bin/ext only; `etc/m2`/`lib`/`LIB-INF` not in the pipeline (B117-G1) |
| 2 | **Hash the input** — sha256 of the exact file; compare to install before citing (twin-binary rule) | `recon.json jar_sha256` | manual `sha256sum` | Java yes (`recon.json`); native no |
| 3 | **Verify vendor signature** | `jarsigner -verify -strict`; exit 0/4 with 0 digest errors | Authenticode digest + chain; `.sig`/`BOARDUPD` trees via openssl | **no** — `recon.json` records only `.SF` presence (`tools/n5-decompile.sh:132`); jarsigner and openssl were run by hand here |
| 4 | **Extract byte-exactly** and prove it | `n5-extract-census.py sweep` (exit 1 on any mismatch) | copy + re-hash | tool exists (this block); not yet called by the pipeline or CI (B117-G7) |
| 5 | **Rule out obfuscation / wrong language** | deobfuscator detect + positive control; Kotlin/Scala/Groovy marker scan; minor-65535 scan | `diec` packer/compiler signature | no (manual, §117.4–§117.5) |
| 6 | **Decompile with the primary** | Vineflower 1.12 (CFR fallback) | Ghidra headless (`ExportDecompiledC.java`) | Java yes; native via kit wrapper |
| 7 | **Corroborate with an independent second instrument** | CFR/Procyon/`javap` (`corroborate-java.sh`); T15 round-trip grader | a different disassembler (objdump vs r2) or decompiler (Ghidra vs r2), a different parser (`debug/gosym` vs Python), a different string/import extractor (`rabin2` vs `strings`/`objdump`) | kit tools exist (`corroborate-java.sh`, `corroborate-native.sh`, `ghidra-evidence`); nothing requires them |
| 8 | **Anchor to bytes** — cite bytecode (`javap -c -p`) or disassembly at a VA | [Block 115] fidelity rule | VA + instruction bytes | no (lint R1 planned, T8) |
| 9 | **Cite sha256 + offset/VA + the two instruments** in the claim; keep evidence durable (not only `/tmp`) | class path + jar sha | binary sha + VA/file offset | no (lint R3 planned for `/tmp`; no rule for the native anchor yet, B117-G7) |

Instrument-independence rule used in §117.8: two runs of one tool, or two front-ends of one engine, count once;
`objdump` (GNU opcodes) and radare2 (capstone) count as two disassemblers; Ghidra decompile vs any disassembler
counts as two families; `strings` vs `rabin2 -zz` counts as two extractors of the same bytes (weakest pair —
acceptable for string presence and absence only, never for behaviour).

## 117.x — Third-party library identity against Maven Central `[CERT-web]`

Every third-party (≤ 50 % Tridium) jar in `LIB-INF/` (95), `bin/ext/` (103) and `etc/m2/` (6) was
identified by its own `META-INF/maven/<g>/<a>/pom.properties` coordinates (or its Maven-repo path for `etc/m2`),
then checked against Maven Central's published `.jar.sha1` at `https://repo1.maven.org/maven2/<g>/<a>/<v>/`
(accessed 2026-09-28; the `search.maven.org` SHA-1 query API was tried first and began timing out after ~100
queries, so the deterministic repo path was used instead) `[CERT-web]` (`maven_repo1.py`, `maven_content.py`,
result `maven-repo1.json` sha256 `282f3e88df9f3f23…`):

| Location | Jars | Whole-file SHA-1 = Central | Content-identical to Central except `META-INF/` (Tridium re-signed) | Different build | No Maven coordinates in jar |
|---|---|---|---|---|---|
| `LIB-INF/` | 95 | 81 (incl. `oauth2-oidc-sdk-11.26-jdk11` classifier and `mssql-jdbc` `13.4.0.jre11`) | — | 1 | 13 |
| `bin/ext/` | 103 | 0 | 72 (every non-`META-INF` entry sha256-equal to the downloaded upstream jar) | 0 | 31 |
| `etc/m2/` | 6 | 6 | — | 0 | 0 |

So 159 of 204 third-party jars are provably the upstream artifact byte-for-byte in code and resources: claims
about them can and should rest on the upstream `-sources.jar`, not on a decompile. The bin/ext jars differ as
whole files only because Tridium re-signs them (their `NIAGARA4.SF` is what jarsigner verified, §117.6). **One
exception:** `abstractMqttDriver.jar!LIB-INF/org.eclipse.paho.client.mqttv3-1.2.5.jar` (SHA-1 `7c81f3ee…`) has the
same 110 classes and sizes as Central's 1.2.5 (SHA-1 `1546cfc7…`), but every class differs in its bytes and the
entries carry 2021-08-16 timestamps against upstream's 2020-07-14 — it is a separate build of 1.2.5 whose source
is not proven to be upstream's (B117-G9). 44 jars carry no `pom.properties` and stay unidentified by this
method (B117-G9).

## 117.x — Corrections to earlier blocks

- **[Block 63] §63.1** (Connections and header): `njre.dll` has **91** exports, not 95 (`rabin2 -E`, `r2 iEj`,
  `objdump -p` EAT size `0x5b`, PE export directory `NumberOfFunctions = 91`). The 0-JNI finding stands.
- **[Block 113] §113.1** field table: the `typelinks` slice pointer is at `firstmoduledata+0x160` (length at
  `+0x168` = `0x972`), not `+0x158`; the block's `moduledata.py` already reads `vals[44]` (`+0x160`), so every
  value it derived is right and only the prose offset is wrong.
- **[Block 43] §43.2**: the `%s` in `-Dniagara.platform.provider=%s` IS filled with the literal
  `com.tridium.nre.platform.NativePlatformProviderTridium` — `buildArgs` passes it as the vararg to the
  `vsnprintf_s` wrapper at `0x1800060be`–`0x1800060e4` (r2 + objdump). Upgrades the block's `[INFER — string
  adjacency]` to `[CERT-hw]` for that call site (whether the call is unconditional was not assessed). The strings
  appear class-name-first in the file, not format-first.
- **[Block 61] §61.2**: `nre.dll`'s ADVAPI32 import set has 7 registry calls (adds `RegDeleteValueA`), not 6.
- **[Block 94] §94.8** self-verify row 2: "sole setter" of `this+0x1002c` holds for policy; the constructor,
  copy constructor, `operator=` and `getInstance` also write the byte during initialisation (r2 `afi.` on the
  four `objdump` write sites).
- **[Block 87] §87.1** self-verify row 3: the 249/250 exits are in `initPaths` after the loop returns −1 (the
  section prose already says so).
- **[Block 30] §30.6**: its no-obfuscation verdict is re-derived with a bytecode-level detector run on every
  one of the 253 Tridium jars with a positive control (§117.5), and its jarsigner check on 4 jars is extended
  to all 373 (§117.6).

## 117.x — Connections

- **[Block 115]** (decompiler-fidelity rule) and **[Block 116]** (lossy-aspects catalog): this block is the
  byte-level half; §117.5's secondary-class file-layout note belongs to [Block 116]'s catalog.
- **[Block 2]**, **[Block 49]**, **[Block 74]**: their `n-plugin`/`slotomatic` decompiles are the out-of-pipeline
  Tridium jars of §117.4 (B117-G1, B117-G2).
- **[Block 18]**: the NCS-Agent development signing certificate, re-verified in §117.6.
- **[Block 53]** §53.3: why exit 4 (untrusted chain) is the expected jarsigner result.
- **[Block 90]** §90.5 / **[Block 98]** §98.9: the N4 ZKM positive control and the same deobfuscator jar.
- **[Block 100]**, **[Block 108]**, **[Block 113]**: pclntab/moduledata claims corroborated in §117.8–§117.9.

## 117.x — Child gaps opened

- **B117-G1** (high) — Give the 10 out-of-pipeline Tridium jars (`etc/m2/.../com/tridium/**` 9 jars, 943
  Tridium classes; `lib/tridium-niagara-baja-doclet-5.0.4.jar`, 15) and devkit's 2 Tridium `LIB-INF` jars a
  durable `organized/` decompile with `recon.json`, replacing the vanished `/tmp` decompiles earlier blocks cite.
  Investigable read-only (decompile only). coverage-check: `python3 tools/check-coverage.py n-plugin slotomatic
  xelem n-templates` plus `rg -l "organized/_etc-m2"` over `niagara5-block*.md` before starting. measured-by:
  count of `organized/_etc-m2/*/recon.json` + `organized/_lib/*/recon.json` = 10, and
  `python3 tools/n5-extract-census.py module <devkit.jar> organized/devkit` reporting
  `nested_classes_decompiled` ≥ 160 (or an equivalent nested-jar tree).
- **B117-G2** (medium) — Audit every corpus claim read from a Java decompile of the Kotlin-compiled Tridium jars
  (`n-plugin` 650/724 classes, `n-conv-plugin`, `settings`, `utils`) and re-check each against `kotlin.Metadata`
  or a Kotlin-aware decompile. Investigable read-only. coverage-check: `rg -il "n-plugin|n-conv-plugin"` over the
  blocks (currently B2, B7, B36, B39, B51, B74, B79, B89, B97, B108) and `rg -il kotlin` on that set. measured-by: a
  per-claim SAFE / SUSPECT table with a count of each, every SUSPECT fixed or tracked.
- **B117-G3** (medium) — Tag corpus claims that rest on the 234 minified JS files, and check whether the 86
  `.map` files carry `sourcesContent` (originals) usable instead. Investigable read-only. coverage-check:
  `rg -l "\.js\b" niagara5-block*.md` cross-referenced with the minified list from `census-modules.json`.
  measured-by: number of JS-citing claims whose cited file has `is_minified_js() == True`, and number of `.map`
  files with non-empty `sourcesContent`.
- **B117-G4** (low) — Decompile and inventory the 14 .NET assemblies in `xprotect.jar!nativeLib/`
  (`decompile-net.sh`) and the `ffmpeg-wrapper.dll` JNI surface, if any corpus claim ever depends on them.
  Investigable read-only. coverage-check: `rg -il "XProtectBridgeService|ffmpeg-wrapper"` over the blocks.
  measured-by: assemblies decompiled / 14 and JNI exports mapped / 24.
- **B117-G5** (medium) — Verify Authenticode *digests* and chains for the 21 Tridium/Microsoft PE files (only
  the certificate was extracted here). Blocked on a tool: `osslsigncode` is not installed and `signtool` needs
  Windows interop. coverage-check: `rg -il "Authenticode|osslsigncode"` over the blocks. measured-by: per-binary
  verify result, target 21/21 "Signature verification: ok".
- **B117-G6** (low) — Corroborate [Block 113]'s 47 own-type struct sizes and field offsets with a second
  parser (Ghidra `GoTypeManager` export or an independent `internal/abi` reader); names are already confirmed by
  byte presence. Investigable read-only. coverage-check: `rg -n "typelinks" niagara5-block113.md` for anything
  added since. measured-by: number of the 47 types whose size and every field offset match between the two
  parsers.
- **B117-G7** (high) — Mechanize steps 3, 4, 5 and 9 of §117.10: call `n5-extract-census.py sweep` and a
  `jarsigner -verify -strict` pass from `tools/n5-decompile.sh` (recording `signature_verified` and
  `byte_exact` in `recon.json`), and add a lint rule that a native claim must carry a sha256, a VA or file
  offset, and two instrument names. Investigable (tool work under strict TDD). coverage-check:
  `rg -n "signature_verified|byte_exact" tools/` and the T8/T15 task state in
  `odd/tasks/decompiler-fidelity-audit.md`. measured-by: `recon.json` files carrying both fields = 252, and the
  lint rule's fixture tests passing under `make test`.
- **B117-G8** (medium) — Preserve this block's small evidence files (`census-modules-agg.json`,
  `jarsigner-summary`, `native-claims.tsv`, `gosym-funcs.tsv`, the two Ghidra `.c` exports, `typename-
  corroboration.txt`) under a durable in-repo `evidence/b117/` once T10 defines the location. Investigable.
  coverage-check: T10 state in `odd/tasks/decompiler-fidelity-audit.md`. measured-by: files present in
  `evidence/b117/` with the sha256 values listed in the Artifacts line.

- **B117-G9** (low) — Establish the provenance of the 45 third-party jars not proven upstream: the paho
  `mqttv3-1.2.5` rebuild (diff it against upstream at the bytecode level, `javap -c -p` on all 110 classes) and
  the 44 jars without `pom.properties` (identify via the `search.maven.org` SHA-1 API once reachable, or via
  `MANIFEST.MF` `Implementation-*`/`Bundle-*` headers). Investigable read-only (network). coverage-check:
  `rg -il "paho|mqttv3"` over the blocks for any claim resting on that jar. measured-by: jars with a proven
  upstream artifact or a documented rebuild delta, target 204/204.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | 20,723 module `.class` + 20,481 resources + 1,028 bin/ext classes byte-identical, 0 missing | [CERT-hw] | `census-modules-agg.json` (sha256 `cd9068a4…`) |
| 2 | 98 LIB-INF jars / 24,896 top-level classes, 0 decompiled; 160 Tridium (devkit) | [CERT-hw] | `census-modules.json` (sha256 `66038a46…`) |
| 3 | 0 of 253 Tridium jars is multi-release; MR only in third-party jars | [CERT-hw] | `nonmodule-jars.txt`, `mr_resolution` |
| 4 | 103 skipped bin/ext jars: 0 Tridium classes of 43,321 | [CERT-hw] | `nonmodule-jars.txt` (sha256 `d94ad6a6…`) |
| 5 | 10 Tridium jars in `etc/m2` + `lib/` outside the pipeline; 4 Kotlin-compiled | [CERT-hw] | `nonmodule-jars.txt`, constant-pool scan |
| 6 | 0 preview (minor 65535) classes; 0 Kotlin/Scala/Groovy in pipeline jars | [CERT-hw] | `jvmlang-preview.txt` (sha256 `97b9071d…`) |
| 7 | deobfuscator: 0 obfuscator rules on 253 N5 jars; 2 Zelix rules on the N4 control | [CERT-hw] | `deobf/out/*.out`, `deobf/pos.out` (sha256 `972776a6…`) |
| 8 | 356 jars verify with only the untrusted-chain error; 17 unsigned, all outside the pipeline | [CERT-hw] | `jarsigner/*.txt` |
| 9 | 234/2,560 JS minified; 0 unidentified high-entropy blobs | [CERT-hw] | `census-modules.json` `js`; entropy scan |
| 10 | native inventory: 21 Tridium-signed MSVC PEs, 1 Go binary, sha256 + language per file | [CERT-hw] | `natives-install.tsv` (sha256 `f1317d33…`), `diec`, `objdump -p` |
| 11 | every cited native sha256 matches the installed file | [CERT-hw] | `sha256sum` of the 7 binaries |
| 12 | 46 single-instrument native claims: 45 confirmed by a second instrument, 1 superseded, 3 details refuted | [CERT-hw] | `native-claims.tsv` (sha256 `eb199aa4…`) + §117.8 artifacts |
| 13 | `njre.dll` has 91 exports (not 95) | [CERT-hw] | `rabin2 -E`, `r2 iEj`, `objdump -p` |
| 14 | typelinks pointer at `firstmoduledata+0x160` | [CERT-hw] | `r2 pxq` @ `0x140754d80` |
| 15 | B43's `%s` is filled with the constant provider class name | [CERT-hw] | `native/r2-43-pd.txt`, `native/objdump-43.txt` (sha256 `dbbd3af7…`) |
| 16 | Go pclntab names confirmed by `debug/gosym` (8,005 functions) and buildinfo | [CERT-hw] | `go/gosym-funcs.tsv` (sha256 `10943a0e…`), `go version -m` |
| 17 | The census rules are pinned by tests (RED then GREEN, 11 tests) | [CERT] | `tools/n5-extract-census.py:145`, `tools/tests/test_n5_extract_census.py` |
| 18 | Pipeline records signature presence only, not verification | [CERT] | `tools/n5-decompile.sh:132` |
| 19 | 159 of 204 third-party jars are upstream Maven Central artifacts (81 + 6 exact, 72 content-identical); paho 1.2.5 is a different build | [CERT-web] | `maven-repo1.json` |

**Tally**: see `verify-block.sh` output (reported to the orchestrator). Block type: evidence (audit); every central
claim is `[CERT-hw]`/`[CERT]` from this session; the single `[INFER]` (Niagara's module loader and Multi-Release)
is flagged in place and is not load-bearing.

**Artifacts**: `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/
b117/` — `census-modules{,-agg}.json`, `nonmodule-jars.txt`, `jvmlang-preview.txt`, `jarsigner/`,
`deobf/{patch.py,pos.out,out/}`, `natives-install.tsv`, `native-claims.tsv`, `native/` (binary copies with
`sha256.txt`, `*.objdump-d.txt`, `*.rabin2-i.txt`, `*.zz.txt`, `r2-43-*.txt`, `ghidra-out/`, `cn-nre/`),
`go/` (`ncs.exe` copy, `gosyms/main.go`, `gosym-funcs.tsv`, `r2-*.txt`, `typename-corroboration.txt`),
`jarnatives/`, `maven-repo1.json`, `up/`. Tool: `tools/n5-extract-census.py` + `tools/tests/test_n5_extract_census.py`
(uncommitted).
