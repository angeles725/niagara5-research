# Block 108 — NCS-Agent's full 8,005-function pclntab census resolves buildinfo-blob module versions and own-package capabilities; the build-side `LIB-INF` packing task pinned to one bytecode `ldc`; a "toolchain-specific" javac warning corrected to a pre-existing artifact; Atlas narrowed to a named commercial candidate

> Research closing/narrowing four child gaps: **B100-G1** ([Block 100] §100.x — census the NCS-Agent Go
> binary's full recovered symbol table, 8,005 functions/4,209 types, into a package-level map now that
> the pclntab is recoverable); **B101-G4** ([Block 101] §101.6/§101.x — Tridium's own commercial/
> marketing name for the "Atlas" ARM64 snap-packaged hardware target); **B101-G5** ([Block 101] §101.x —
> the build-side Gradle task that packs third-party jars into a module jar's `LIB-INF/` at build time);
> **B106-G2** ([Block 106] §106.8/§106.x — whether the Windows bundled `jre/bin/javac.exe`'s
> `NiagaraPermissionGrant$Type.WORKBENCH` enum warning is toolchain-specific, reproducible on a Linux
> JDK 25). Does **not** cover: a walk of NCS-Agent's separate Go type-metadata table (`moduledata.types`/
> `typelinks`, the "4,209 types" half of B100-G1's own ask — the pclntab this session parsed covers only
> the 8,005-entry FUNCTION table; preserved as a new child gap, **B108-G1**); an explicit Tridium-
> published statement equating "Atlas" with any shipped product SKU (B101-G4's own bar; this session's
> narrowing is architectural-fingerprint correlation, not a found label); a native/native-agg devkit build
> (out of scope for all four assigned gaps).
>
> Subject versions: **N5 5.0.0.28 (Beta)** — `/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/
> tridium-ncs-supervisor-amd64-windows.exe` (sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`,
> identical to [Block 96]/[Block 100]'s own subject binary, copied read-only, never executed) for B100-G1;
> `etc/m2/repository/com/tridium/tools/n-plugin/5.0.54.9.2/n-plugin-5.0.54.9.2.jar` (sha256
> `eb9831b65465f7f06831f875215ba7b0511aae9572b866ad21135752d6d93356`) and `.../n-conv-plugin/5.0.54.9.2/
> n-conv-plugin-5.0.54.9.2.jar` (sha256 `2769afff5668cde85aee0a75a0af68cbee253c3771488a324c405211aacc98a8`)
> for B101-G5; the real bundled Windows `jre/bin/javac.exe` (`javac 25.0.4`, per [Block 106] §106.8) PLUS
> a fresh Linux Homebrew OpenJDK 25 (`javac 25.0.4.1`, package `openjdk@25`) for B106-G2, against the
> SAME 4 real jars [Block 55]/[Block 106] already sha256-pinned (`gx.jar` `3ad3ea9124d7…`, `bajaui.jar`
> `1294cf5bc38e…`, `workbench.jar` `487ea4ea3049…`, `alarm.jar` `fb5b21c30412…`, unchanged at
> `/tmp/claude-1000/n5b55/copies/`, re-`sha256sum`-verified this session).
>
> Method: **B100-G1** — reused [Block 100] §100.1's own already-validated pclntab header (`base=0x512a40`,
> `nfunc=8005`, `textStart=0x140001000`, cross-validated against the PE `.text` VMA) via that block's own
> preserved scratch scripts (`parse_pclntab.py`/`dump_funcs.py`, re-derivable verbatim from the same
> sha256, not re-derived from scratch); extended with a full (not target-filtered) function-table walk
> dumping all 8,005 name/address pairs, then a Python package-prefix classifier (own-package/third-party/
> Go-stdlib-vendor/Go-stdlib split); corroborated against `go version -m` (buildinfo blob parsing — Go
> 1.27.0 toolchain, this session) and against `strings -a`/`r2 iz~` hits for the same buildinfo-blob text
> at two on-disk offsets (`.rdata` and `.data`). **B101-G5** — `unzip -l` census of `n-plugin`'s
> `com/tridium/gradle/plugins/module/` classes for `*CopySpec` naming; Vineflower 1.12.0 decompile of
> `UnterjarCopySpec.class`/`UberjarCopySpec.class`; `javap -p -c -constants` bytecode disassembly of
> `NiagaraModulePlugin.class` (Kotlin-lambda-heavy, Vineflower could not fully decompile it — same
> confound [Block 97] §97.x already named) and of its `registerModuleTasks$jarTask$1$4` inner-class
> lambda, tracing the exact `Jar.from(Object, Action)` call site. **B106-G2** — literal re-run of
> [Block 55] §55.2's exact `javac --module-path copies -d out1 src/angeles.probe1/module-info.java`
> command against a Linux JDK 25 toolchain, byte-for-byte console-output diff against both [Block 106]
> §106.8's Windows run and [Block 55]'s own ORIGINAL raw output file (not its §55.2 prose paraphrase).
> **B101-G4** — `WebSearch` (this session, access date **2026-09-27**) cross-referencing [Block 101]
> §101.6's own `[CERT]` architecture fingerprint (ARM64, Ubuntu-Core-snap-packaged Niagara core, contrasted
> with Titan's AM335x/ARMv7) against public Tridium hardware datasheets. Gate: no `detect-tools.sh`
> gate needed beyond what [Block 100]/[Block 106] already passed this corpus session (Ghidra not
> re-invoked; `go`/`r2`/`javap`/Homebrew `javac` all present, confirmed live). Scratch (never archived,
> per task instruction): `/tmp/claude-1000/-home-cristian-niagara-research/
> 4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b108/` (`ncsagent.exe` copy + sha256, `all_funcs.tsv`
> full 8,005-row dump, `census.py`/`census_output.txt`, `b101g5/` decompile+javap dumps, `b106g2/` the
> Linux-JDK25 probe1 re-run) — reused, without re-copying, [Block 100]'s own
> `dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b100/` scripts and [Block 55]'s own
> `/tmp/claude-1000/n5b55/copies/` jars, both still present on disk this session.
>
> Markers (canonical list, METHODOLOGY §3): `[CERT]` local `file:line` · `[CERT-hw]` live/real-binary
> evidence (disassembly address/sha256, decompiled real jar, live `javac` run) · `[CERT-web]`
> WebSearch/WebFetch result, URL + access date · `[INFER]` deduction from `[CERT]`/`[CERT-hw]`/`[CERT-web]`
> evidence.
>
> **Type:** `evidence` — every closing verdict rests on a disassembly/bytecode citation, a live command
> re-run, or a cited external artifact; the sole exception (§108.2/B101-G4) is explicitly reported as
> `[INFER]`-grade ADVANCED, not CLOSED.

---

## 108.1 — B100-G1 CLOSED: NCS-Agent's full 8,005-function table classified into 279 own-code functions (14 `github.com/HON-HCE/*` packages), 396 direct third-party functions (5 modules with exact versions from the recovered buildinfo blob), and 214 Go-stdlib-internal-vendor functions, corroborated by `go version -m`, `strings`, and `r2` `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 100] §100.x): *"Census the NCS-Agent Go binary's full recovered
symbol table (8,005 functions, 4,209 types, per §100.1's Ghidra corroboration) into a package-level map,
extending [Block 96] §96.9's architecture sketch with the complete inventory now that the pclntab is
recoverable."*

**Binary identity unchanged**: `sha256sum` of this session's copy of
`tridium-ncs-supervisor-amd64-windows.exe` → `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`,
matching [Block 96]/[Block 100]'s own subject binary `[CERT-hw]`.

**Full function table dumped (not target-filtered).** [Block 100] §100.1's own already-`[CERT-hw]`-
validated pclntab header (magic `0xfffffff1`, `base=0x512a40`, `nfunc=8005`, `textStart=0x140001000`,
matching the PE's own `.text` VMA) was walked to completion — every one of the 8,005 `{entryOff,funcOff}`
function-table entries resolved to its name via the `funcnametab`, sorted by address, written to
`all_funcs.tsv` (this session's scratch). `[CERT-hw]` (`dump_all_funcs.py`, re-derivable verbatim against
the same sha256 and the same `base` offset [Block 100] §100.1 already cross-validated against the PE
section table — no new pclntab-location claim is made here, only a full rather than target-filtered walk
of the SAME already-validated table).

**Package-level classification (Python prefix classifier, this session, `census.py`):**

| Class | Functions | Distinct packages | Note |
|---|---|---|---|
| `github.com/HON-HCE/*` own library packages | 233 | 13 | `tridium-ncs-rsm-agent/internal/*` + `tridium-uc-shared/go-packages/*` |
| `main` (own, `cmd/ncs-agent`) | 46 | 1 | the agent's own entrypoint/state-machine driver |
| **Own total** | **279** | **14** | **3.5% of the binary** |
| Third-party direct module deps | 396 | 6 | `apache/thrift` 299, `sslmate/go-pkcs12`(+`internal/rc2`) 67, `golang.org/x/sys/windows` 24, `google/uuid` 5, `golang.org/x/crypto/pbkdf2` 1 |
| Go-stdlib-internal `vendor/golang.org/x/*` copies | 214 | ~14 | stdlib's OWN internal vendoring (used BY `net/http`/`crypto/tls`, not a project dependency) |
| Go standard library (`runtime`, `net/http`, `crypto/*`, `encoding/*`, …) | 6,743 | ~245 | dominated by `runtime` (1,368), `net/http` (685), `crypto/tls` (476), `net` (393), `reflect` (189) |
| Compiler-generated (`type:.eq.*`, `go:*` build-id/fips markers, hand-asm `<no-dot>` runtime primitives) | 373 | — | 326 `type:.eq` equality-method stubs + 11 `go:*` + 36 hand-asm (`gcWriteBarrier`, `debugCall*`, `p256MulInternal`, …) |
| **Total** | **8,005** | **279** | matches [Block 96] §96.9's/[Block 100]'s own `nfunc=8005` exactly |

`[CERT-hw]` (`census.py`/`census_output.txt`, this session, scratch — deterministic re-run against the
same `all_funcs.tsv`).

**Own packages named, with capabilities inferred from their own function names (corroborated by a live
disassembly of two call sites — see below):**

| Package | Funcs | Capability |
|---|---|---|
| `internal/niagaradshim/niagaradshimgen` | 87 | Apache-Thrift-generated IDL stubs for the local Niagara-station-facing service |
| `internal/rsmclient` | 53 | REST client (`callAPI`/`prepareRequest`/`DownloadPartExecute`/`SyncManifestExecute`) — cloud "Remote Software Management" API |
| `internal/keystore` (+`/dpapi`,`/flock`) | 33 | local identity/cert storage: AES-GCM keyring decrypt, atomic file write+backup+restore, Windows DPAPI blob wrapping, file locking |
| `internal/ncsauth` | 18 | device registration/auth to the cloud (`InitRegistration`/`BootstrapCert`/`RollingCert`/`doJSONPost`) + CSR/TLS-identity lifecycle |
| `internal/platform` | 14 | local platform introspection: `JREInfo`/`NREInfo`/`BrandId`/`SnapList`/`ReadVersion`/`WriteVersion` |
| `internal/niagaradshim` | 11 | the Thrift SERVER side: `buildServerTLSConfig`/`generateCert`/`StartRegistration`/`Deregister` — a local mTLS RPC endpoint |
| `go-packages/propserializer`,`/tridiumarchive`,`/fsm`,`/ncs/conf` | 14 | shared `.properties`-shaped config (de)serialization, a Niagara-module-archive parser (`parseModuleInfo`/`ModulesList`), and a finite-state-machine driver (`fsm.(*Machine).Run`, matching `main`'s own `AgentStruct` state names `Idle`/`Validate`/`Transmit`/`InstallSoftware`) |
| `main` | 46 | the FSM's own concrete states/actions: `DownloadParts`, `BuildManifest`, `InstallSoftware`, `EntryPoint`, `mapNiagaradshimRequests` |

`[CERT-hw]` (`all_funcs.tsv`, this session — every listed function name is a literal pclntab-recovered
symbol; the capability wording is `[INFER]` from the name/grouping, standard practice for a symbol-only
census with no gap-mandated full decompile).

**Live disassembly corroboration of one capability claim** (network+file, `main.DownloadParts`,
`0x1403384e0`–`0x140339780`): `objdump -d --start-address/--stop-address -M intel`, every `call` target
resolved back against `all_funcs.tsv`, shows calls to
`rsmclient.(*DeviceAPIService).DownloadPartExecute` (network fetch), `os.OpenFile`+`io.copyBuffer`
(writes the fetched part to a local file), `os.Getenv`/`path/filepath.join` (destination path
construction), and `os.Exit`/`log`/`log/slog` — no `os/exec` call anywhere in this function; a corpus-wide
`grep "	os/exec\."` over the full 8,005-row table returns **zero hits** — this binary imports no Go
`os/exec` package at all (an `exec`-capability claim would need a `syscall.CreateProcess` call site, not
identified this session). `[CERT-hw]` (`downloadparts.objdump.txt`, this session).

**Module identity and third-party versions recovered from the intact Go buildinfo blob** (a SEPARATE
structure from the pclntab that `-ldflags="-s -w"` does NOT strip): `go version -m ncsagent.exe` (Go 1.27.0
toolchain, this session) parses it directly:

```
ncsagent.exe: go1.25.12
	path	github.com/HON-HCE/tridium-ncs-rsm-agent/cmd/ncs-agent
	mod	github.com/HON-HCE/tridium-ncs-rsm-agent	v0.0.0-20260813111400-8e8f1806a707
	dep	github.com/HON-HCE/tridium-uc-shared/go-packages/fsm	v0.0.0-20260618152018-7dcdc4cc7209
	dep	github.com/HON-HCE/tridium-uc-shared/go-packages/ncs	v0.0.0-20260618152018-7dcdc4cc7209
	dep	github.com/HON-HCE/tridium-uc-shared/go-packages/propserializer	v1.0.0
	dep	github.com/HON-HCE/tridium-uc-shared/go-packages/tridiumarchive	v0.0.0-20260618152018-7dcdc4cc7209
	dep	github.com/apache/thrift	v0.22.0
	dep	github.com/google/uuid	v1.6.0
	dep	golang.org/x/crypto	v0.53.0
	dep	golang.org/x/sys	v0.46.0
	dep	software.sslmate.com/src/go-pkcs12	v0.7.2
	build	-ldflags="-s -w -X main.CloudAPIVersion=0ce8a6de -X main.AgentVersion=0.0.1"
	build	-tags=supervisor
	build	vcs=git
	build	vcs.revision=8e8f1806a707562ae6ee1649fd55cae41eff42f9
	build	vcs.time=2026-08-13T11:14:00Z
	build	vcs.modified=false
```

This is a NEW fact beyond [Block 100] §100.1's own GitHub-import-path finding: exact **build Go version
(1.25.12)**, exact **git commit** the binary was built from (`8e8f1806a707…`, 2026-08-13), and exact
**third-party dependency versions** (`apache/thrift` v0.22.0, `google/uuid` v1.6.0, `golang.org/x/crypto`
v0.53.0, `golang.org/x/sys` v0.46.0, `software.sslmate.com/src/go-pkcs12` v0.7.2), plus the two
ldflags-injected build-time constants (`main.CloudAPIVersion=0ce8a6de`, `main.AgentVersion=0.0.1`).
`[CERT-hw]` (`go version -m` output, this session, live tool run against the same sha256).

**Corroborated by `strings`/`r2`, per the gap's own requirement** (a decompile/parse of a native binary
is not evidence until corroborated): `strings -a ncsagent.exe | grep` and `r2 -q -c "iz~<needle>"` both
independently hit the IDENTICAL buildinfo text at two separate on-disk offsets (`.rdata` offset
`0x74a23c`/VA `0x14074c03c` in `.data`, and a second copy in `.rdata`) — the git revision
`8e8f1806a707562ae6ee1649fd55cae41eff42f9`, the `CloudAPIVersion`/`0ce8a6de` ldflags pair, the
`apache/thrift` module line, and the bare `go1.25.12` version string all appear as literal ASCII in BOTH
tools' independent scans, not merely in `go version -m`'s parsed interpretation. `[CERT-hw]`
(`corroboration.txt`, this session — `strings -a` + `r2 -q -c "iz~…"`, four separate anchor greps, all
hit).

**Closing B100-G1**: the FUNCTION half of the gap's "8,005 functions/4,209 types" ask is fully censused —
every one of the 8,005 recovered functions is classified by package, the 14 own packages are named with
function counts and inferred capabilities, the 6 real third-party dependencies are identified with EXACT
versions (not previously known — [Block 96]/[Block 100] had only import paths for the OWN packages, no
version data for anything), and one capability claim (network+file, `DownloadParts`) is corroborated by
live disassembly. The TYPE half (4,209 types) is **not** censused this session — walking Go's separate
type-metadata table is a materially different task than the pclntab function walk this session (and
[Block 100] §100.1) both used; preserved as **B108-G1** below.

## 108.2 — B101-G5 CLOSED: the build-side `LIB-INF` packing task pinned to one bytecode instruction — `NiagaraModulePlugin$registerModuleTasks$jarTask$1$4.execute(CopySpec)` literally calls `CopySpec.into("LIB-INF")`, wired onto `Jar.from(UnterjarCopySpec(...), thatAction)` `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 101] §101.x): *"Locate and read the build-side Gradle task
(likely an `unterjar`-family plugin, per [Block 95]'s own naming) that actually PACKS third-party jars
into a module jar's `LIB-INF/` at build time — §101.1 fully closed the runtime-extraction side
(`jar-cache/`) but the build-side packing step was not directly read this session."*

**The plugin jar and the two `CopySpec` classes.** [Block 97]'s own citation already located
`NiagaraModulePlugin.class` inside `etc/m2/repository/com/tridium/tools/n-plugin/5.0.54.9.2/
n-plugin-5.0.54.9.2.jar` (this session's `sha256sum`: `eb9831b65465f7f06831f875215ba7b0511aae9572b866ad21135752d6d93356`).
An `unzip -l` census of that jar's `com/tridium/gradle/plugins/module/` package finds exactly two classes
matching the `unterjar`/`uberjar` naming [Block 2] §2.4/[Block 95] §95.1 already established from the
CONSUMER side: `util/UnterjarCopySpec.class` and `util/UberjarCopySpec.class`. Both decompile cleanly with
Vineflower 1.12.0 (unlike the Kotlin-lambda-heavy `NiagaraModulePlugin.class` itself, which hits the same
"no d1 attribute" Kotlin-metadata confound [Block 97] §97.x already documented, and which this session
instead reads via `javap -p -c -constants` bytecode, per that same block's own convention):

```java
// UnterjarCopySpec.call() — preserves each artifact's own identity
for (File file : this.unterjarConfiguration) {
    if (file.isDirectory())        objects.add(file);
    else if (file.getName().endsWith(".jar")) objects.add(file);   // kept WHOLE
    else                            objects.add(this.archiveOperations.zipTree(file));
}
// UberjarCopySpec.call() — ALWAYS explodes
for (File file : this.uberjarConfiguration) {
    if (file.isDirectory()) objects.add(file);
    else                     objects.add(this.archiveOperations.zipTree(file));   // never kept whole
}
```

`[CERT-hw]` (`vf_out/com/tridium/gradle/plugins/module/util/{Unterjar,Uberjar}CopySpec.java`, this
session's fresh Vineflower decompile). This is the exact mechanism [Block 1]/[Block 10]'s own doc-sourced
framing ("`unterjar` preserves a third-party jar's own module identity; `uberjar` explodes it") already
stated from `doc/modules.html` — now confirmed from the plugin's OWN implementation, not merely its
documentation.

**The exact `Jar.from(...)` call sites, `javap`-disassembled from `NiagaraModulePlugin.class`'s
`registerModuleTasks` method:**

```
224: new UberjarCopySpec(archiveOperations, configurations.maybeCreate("uberjarClasspath"))
252: jarTask.from([<that spec>])                              // Jar.from(Object[])  — NO destination action
258: new UnterjarCopySpec(archiveOperations, configurations["unterjarClasspath"])
295: jarTask.from(<that spec>, jarTask$1$4.INSTANCE)           // Jar.from(Object, Action<CopySpec>) — WITH an action
```

`[CERT-hw]` (`NiagaraModulePlugin.javap.txt`, this session, `javap -p -c -constants` against the same
sha256-pinned jar). The uberjar path uses the 1-arg-array `from([Object])` overload with no
`CopySpec`-configuring `Action` — its exploded classes land at the jar's ROOT, unprefixed (flattening
third-party classes into the module's own namespace, the JPMS-breaking behavior [Block 10]'s BC-23 already
named). The unterjar path uses the 2-arg `from(Object, Action<? super CopySpec>)` overload, passing the
singleton `NiagaraModulePlugin$registerModuleTasks$jarTask$1$4` as the destination-configuring action.

**That action's own bytecode, disassembled directly (this is the literal `LIB-INF` write):**

```
public final void execute(org.gradle.api.file.CopySpec):
     6: aload_1
     7: ldc  #25          // String LIB-INF
     9: invokeinterface   // CopySpec.into(Ljava/lang/Object;)
```

`[CERT-hw]` (`javap -p -c -constants` against
`NiagaraModulePlugin$registerModuleTasks$jarTask$1$4.class`, same jar/sha256, this session — the literal
ASCII constant-pool string `LIB-INF`, not an inference from a class/method NAME).

**Closing B101-G5**: the build-side task is `NiagaraModulePlugin.registerModuleTasks()`'s configuration
of the module's main `Jar` task (registered per-module by the plugin `apply()`, not a separately-named
Gradle task type) — it wires `unterjarClasspath`-resolved artifacts through `UnterjarCopySpec` (kept
whole) into the jar's `Jar.from(spec, action)` 2-arg overload, whose action calls
`CopySpec.into("LIB-INF")` — matching [Block 101] §101.1's own already-closed runtime-extraction finding
(`NModuleModuleFinderFactory.readModule()` reading `LIB-INF/*.jar` back out at runtime) exactly on the
build side, with a single literal-string citation closing the gap's own stated bar.

## 108.3 — B106-G2 CLOSED, with a correction to [Block 106] §106.8: the `NiagaraPermissionGrant$Type.WORKBENCH` warning is NOT toolchain-specific — it reproduces byte-for-byte on Linux Homebrew OpenJDK 25, AND it was already present in [Block 55]'s own raw Homebrew probe-1 output file, just never quoted in [Block 55] §55.2's prose `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 106] §106.x): *"the Windows bundled `jre/bin/javac.exe` emitted a
new benign warning in probe 1 (`warning: unknown enum constant NiagaraPermissionGrant$Type.WORKBENCH …`)
that [Block 55]'s own Homebrew probe 1 output (quoted in full, [Block 55] §55.2) does not mention. Whether
this is a genuine toolchain-specific difference … or simply an unreported detail of [Block 55]'s own
session was not determined — a re-run of Homebrew's identical probe 1 side-by-side with this session's
Windows run, diffed line-for-line, would settle it."*

**The annotation is `RUNTIME`-retained** (`organized/_bin-ext/niagaraAnnotationProcessors/vineflower/
com/tridium/nre/annotations/NiagaraPermissionGrant.java:8-14`): `@Retention(RetentionPolicy.RUNTIME)` on
an `enum Type { STATION, WORKBENCH, ALL; }` nested inside the annotation — meaning any class file carrying
a `@Grant*Permission(type=WORKBENCH)`-shaped annotation embeds a `RuntimeVisibleAnnotations` reference to
this exact enum constant, resolvable by `javac` only if `NiagaraPermissionGrant$Type.class` itself is on
the classpath. `[CERT]`. The [Block 55]/[Block 106] 4-jar minimal probe (`gx.jar`/`bajaui.jar`/
`workbench.jar`/`alarm.jar`) never includes `niagaraAnnotationProcessors.jar` (the module that ships this
annotation class) — so the warning is a deterministic function of THAT classpath composition, not of any
JVM/OS-specific behavior.

**Re-run against a real Linux JDK 25** (`/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac`, `javac
25.0.4.1`), the SAME sha256-pinned 4 jars, the SAME `angeles.probe1` `module-info.java`
(`requires niagara.alarm;`):

```
$ javac --module-path copies -d out1 src/angeles.probe1/module-info.java
… 14 errors (identical set to [Block 55] §55.2's own list, including all 4 javafx.* targets) …
warning: unknown enum constant NiagaraPermissionGrant$Type.WORKBENCH
  reason: class file for com.tridium.nre.annotations.NiagaraPermissionGrant$Type not found
1 warning
```

`[CERT-hw]` (`b106g2/probe1-linux-jdk25.txt`, this session, reproduced from the unmodified `/tmp/claude-1000/
n5b55/copies/` jars, re-`sha256sum`-verified identical to [Block 55]'s own citations before running).

**Correcting [Block 106] §106.8's own framing**: [Block 55]'s ORIGINAL raw output file for this exact
probe — `/tmp/claude-1000/n5b55/probe/probe1-output.txt`, the file [Block 55] §55.2 itself cites as its
`[CERT-hw]` evidence — is **still on disk, unmodified**, and reading it directly (not [Block 55] §55.2's
own prose paraphrase, which only lists the 14 error TARGETS) shows it **already contains the identical
warning line**, verbatim:

```
warning: unknown enum constant NiagaraPermissionGrant$Type.WORKBENCH
  reason: class file for com.tridium.nre.annotations.NiagaraPermissionGrant$Type not found
14 errors
1 warning
```

So [Block 106] §106.8's claim that "[Block 55]'s own Homebrew probe 1 output … does not mention" this
warning is **incorrect as stated**: [Block 55]'s own raw ARTIFACT does mention it; only [Block 55] §55.2's
PROSE summary (which transcribed error counts/targets, not the full console text) omitted it. [Block 106]
§106.8 compared its own verbatim Windows transcript against [Block 55]'s prose, not against [Block 55]'s
own cited raw file. `[CERT-hw]` (direct `cat` of `/tmp/claude-1000/n5b55/probe/probe1-output.txt`, this
session — file untouched since [Block 55]'s own session, same directory/mtime as the other 3 probe
outputs [Block 55] §55.2 also cites).

**Closing B106-G2**: NOT toolchain-specific. The warning is a deterministic consequence of compiling
against a classpath that includes a `RUNTIME`-retention annotation's USE (in `bajaui`/`gx`/`alarm`'s own
class files) without that annotation's OWN defining class present — reproduced identically on Windows
`jre/bin/javac.exe` (25.0.4, [Block 106] §106.8), Linux Homebrew OpenJDK 25 (25.0.4.1, this session AND
[Block 55]'s own original, unquoted, run), i.e. on every JDK-25 toolchain this corpus has tested, with the
SAME 4 jars. Benign on all three.

## 108.4 — B101-G4 ADVANCED, not CLOSED: "Atlas" narrowed to one named candidate — the JACE 9000 — by full architecture-fingerprint correlation (ARM64 quad-core + Ubuntu Core/snap delivery), but no Tridium-published source states the "Atlas" codename itself `[CERT-web]` + `[INFER]`

**Parent gap, quoted verbatim** ([Block 101] §101.x): *"Locate Tridium's own commercial/marketing name for
the 'Atlas' hardware target identified in §101.6 (ARM64, snap-packaged) — this session's one `WebSearch`
found nothing public."*

**[Block 101] §101.6's own fingerprint, restated**: `ATLAS_SNAP_TRIDIUM_NIAGARA_NAME =
"snap-tridium-niagara-arm64"` (`organized/docSource/backup/niagara/backup/BBackupService.java:3159`) —
Atlas's Niagara core ships as an installable Linux **snap**, **ARM64**, contrasted in the SAME file with
`TITAN_OS_NAME_SUFFIX="-n4-titan-am335x-hs"` (Titan = **AM335x/ARMv7**, a traditional OS/JRE/NRE split).

**This session's `WebSearch` (2026-09-27) does not find "Atlas" published anywhere by Tridium** — same
zero-hit result [Block 101] §101.x already reported (`Tridium Niagara "ATLAS" hardware platform
snap-tridium-niagara-arm64 JACE` and equivalent queries return no Tridium-authored page naming "Atlas").
The gap's own bar (an explicit commercial LABEL) remains unmet. `[CERT-web]`.

**But the architecture fingerprint itself resolves to one named, currently-shipping product with high
confidence**, via a second, independent public-datasheet fingerprint match for the KNOWN sibling name
(Titan) that already correlates with a REAL product:

| Fingerprint element | "Titan" ([Block 101] §101.6, `[CERT]`) | Public match | "Atlas" ([Block 101] §101.6, `[CERT]`) | Public match |
|---|---|---|---|---|
| CPU | AM335x, ARMv7 | **JACE 8000**: TI Sitara AM335x, Cortex-A8 `[CERT-web]` | ARM64 | **JACE 9000**: NXP i.MX8M+, quad-core Cortex-A53 (ARM64) `[CERT-web]` |
| OS delivery | traditional OS/JRE/NRE | (JACE 8000: QNX-era, traditional) | single snap-bundled Niagara core | **JACE 9000: OS changed from QNX to "Ubuntu Core 20 Linux (ARM64)…segregated into snaps for various components"** `[CERT-web]` |

Sources (`WebSearch`, this session, access date **2026-09-27**): JACE 9000 SoC/OS — "NXP iMX8M+ …
Quad-core ARM Cortex-A53 … The operating system was changed from QNX to Ubuntu Core 20 Linux (ARM64), with
the system segregated into snaps for various components" (Cochrane Supply, tridium.com TridiumTalk
announcement); JACE 8000 SoC — "the AM335x is an Arm Cortex-A8 processor" (TI product page,
tridium.com/Tyrrell Products datasheets).

**The correlation is exact and two-for-two** (both the CPU-architecture jump AND the OS-delivery-mechanism
jump named in [Block 101] §101.6's own citation match JACE 8000→JACE 9000's own public transition), but
this remains `[INFER]`, not `[CERT]`: no source states "Atlas is the internal Tridium codename for the
JACE 9000" — the correlation is this session's own architecture-fingerprint match, not a found label.
[Block 101] §101.6's own B13-G5 "architecture/identity" closure already stands; this section only narrows
the SEPARATE "commercial name" half with a single, well-evidenced candidate rather than leaving it wholly
unidentified.

**Advancing, not closing, B101-G4**: report the JACE 9000 as the strongly-indicated candidate, with both
supporting sources cited, but do not mark the gap CLOSED, since its own stated bar (an explicit published
equivalence) is still unmet.

## 108.x — Corrections to earlier blocks

- **[Block 106] §106.8** — corrected by §108.3 above: its claim that "[Block 55]'s own Homebrew probe 1
  output … does not mention" the `NiagaraPermissionGrant$Type.WORKBENCH` warning is wrong as stated. The
  warning IS present, verbatim, in [Block 55]'s own cited raw artifact
  (`/tmp/claude-1000/n5b55/probe/probe1-output.txt`, unmodified, still on disk) — [Block 106] §106.8
  compared against [Block 55] §55.2's PROSE summary (which only listed error targets, not full console
  text), not against [Block 55]'s own raw file. The correct reading of B106-G2's own premise is "this
  warning is toolchain-independent and was already captured, un-transcribed, by [Block 55]'s own session"
  — not "a new Windows-only warning."

## 108.x — Connections

- **[Block 100]/[Block 96]** — §108.1 extends [Block 100] §100.1's pclntab recovery (reused verbatim, not
  re-derived) into the full package census [Block 96] §96.9's own architecture sketch asked for, adding
  exact third-party versions neither block had.
- **[Block 108]/[Block 101]** — §108.1's own `internal/platform.SnapList`/`BrandId` function names
  (NCS-Agent detects the local platform's installed snaps and brand at runtime) independently corroborate
  [Block 101] §101.6's "Atlas ships as a snap" finding from a SECOND binary (the Go agent, not just the
  Java-side `BBackupService.java` constants) — a connection neither block previously drew.
- **[Block 101]/[Block 97]** — §108.2 closes B101-G5 using the SAME `n-plugin-5.0.54.9.2.jar` and the SAME
  Kotlin-lambda-decompile confound [Block 97] §97.x first documented (Vineflower fails on
  `NiagaraModulePlugin.class` itself; `javap` bytecode reading is the working fallback both blocks use).
- **[Block 106]/[Block 55]** — §108.3 closes B106-G2 and, in doing so, narrows [Block 106] §106.8's own
  finding from "a new Windows-specific warning" to "a pre-existing, toolchain-independent warning [Block
  106] §106.8 rediscovered because it compared against the wrong artifact" (Corrections, above).
- **[Block 101]/[Block 13]** — §108.4's JACE-8000/JACE-9000 correlation reuses [Block 13] §13.4.4's own
  `platHwScanAtlas`/Titan naming-convention observation as the anchor for the SAME public-datasheet
  cross-check [Block 101] §101.6 already ran for Titan alone; this session extends it to Atlas.

## 108.x — Child gaps opened

- **B108-G1** (refines **B100-G1**, medium priority) — walk NCS-Agent's separate Go type-metadata table
  (`moduledata.types`/`typelinks`, reachable from `firstmoduledata`, a DIFFERENT structure than the
  pclntab function table this session and [Block 100] §100.1 both parsed) to census the "4,209 types"
  half of the original gap's own ask — which own/third-party TYPES (not functions) are compiled in, e.g.
  whether any `HON-HCE`-owned struct types embed fields not visible from the function-name census alone.
  `investigable`, read-only, same binary/session-tooling, no new artifact needed — just a second parser
  script.
- **B108-G2** (new, low priority) — an actual `syscall`/`golang.org/x/sys/windows`-level disassembly trace
  of `main.(*AgentStruct).InstallSoftware`'s eventual process-execution path (this session confirmed NO
  `os/exec` package is linked at all, and `InstallSoftware` itself calls only logging/channel-send
  primitives — meaning the actual install-invocation code, if any, is either inlined elsewhere in `main`
  or performed by a mechanism this session's two targeted disassemblies did not reach). `investigable`,
  read-only, same binary.
- **B108-G3** (refines **B101-G4**, low priority, `blocked-external`) — obtaining any Tridium-internal or
  partner-only document that explicitly names the "Atlas" codename (the public web surface this session's
  tools reach has none) would fully close B101-G4 outright; out of this session's tool access.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `tridium-ncs-supervisor-amd64-windows.exe` sha256 unchanged from [Block 96]/[Block 100] | `[CERT-hw]` | `sha256sum` this session, `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7` |
| 2 | Full pclntab walk recovers exactly 8,005 function-table entries, matching [Block 100] §100.1's `nfunc` | `[CERT-hw]` | `all_funcs.tsv`, this session, `wc -l` = 8005 |
| 3 | 14 own (`github.com/HON-HCE/*` + `main`) packages total 279 functions; 6 third-party module deps total 396 functions | `[CERT-hw]` | `census.py`/`census_output.txt`, this session |
| 4 | `go version -m` recovers exact module versions (`apache/thrift` v0.22.0, `google/uuid` v1.6.0, `golang.org/x/crypto` v0.53.0, `golang.org/x/sys` v0.46.0, `sslmate/go-pkcs12` v0.7.2) and git revision `8e8f1806a707…` from the intact buildinfo blob | `[CERT-hw]` | `go version -m ncsagent.exe`, this session, Go 1.27.0 toolchain |
| 5 | The buildinfo text is independently corroborated by `strings -a` and `r2 -q -c "iz~…"` at two on-disk offsets | `[CERT-hw]` | `corroboration.txt`, this session |
| 6 | `main.DownloadParts` calls `rsmclient.DownloadPartExecute` + `os.OpenFile`/`io.copyBuffer`, no `os/exec` anywhere in the 8,005-function table | `[CERT-hw]` | `downloadparts.objdump.txt`, this session; `grep -c "	os/exec\." all_funcs.tsv` = 0 |
| 7 | `NiagaraPermissionGrant.Type` is `enum { STATION, WORKBENCH, ALL }`, `RUNTIME`-retention | `[CERT]` | `organized/_bin-ext/niagaraAnnotationProcessors/vineflower/com/tridium/nre/annotations/NiagaraPermissionGrant.java:8-14` |
| 8 | `UnterjarCopySpec.call()` keeps directories/`.jar` files whole; `UberjarCopySpec.call()` always `zipTree`-explodes | `[CERT-hw]` | Vineflower decompile of `n-plugin-5.0.54.9.2.jar` (sha256 `eb9831b6…`), this session |
| 9 | `NiagaraModulePlugin$registerModuleTasks$jarTask$1$4.execute(CopySpec)` calls `CopySpec.into("LIB-INF")` — literal constant-pool string | `[CERT-hw]` | `javap -p -c -constants`, same jar/sha256, this session |
| 10 | The `Jar.from(UnterjarCopySpec, jarTask$1$4)` 2-arg overload vs. `Jar.from([UberjarCopySpec])` 1-arg-array overload, exact bytecode offsets 258–304 vs. 224–257 | `[CERT-hw]` | `NiagaraModulePlugin.javap.txt`, this session |
| 11 | The WORKBENCH warning reproduces identically on Linux Homebrew OpenJDK 25 (25.0.4.1) against the same sha256-pinned 4 jars | `[CERT-hw]` | `b106g2/probe1-linux-jdk25.txt`, this session |
| 12 | [Block 55]'s OWN original raw `probe1-output.txt` already contains the identical warning line | `[CERT-hw]` | direct `cat` of `/tmp/claude-1000/n5b55/probe/probe1-output.txt`, this session (file unmodified since [Block 55]'s own session) |
| 13 | Titan = JACE 8000 (AM335x/Cortex-A8); Atlas's fingerprint (ARM64 quad-core + Ubuntu-Core/snap) matches JACE 9000 (i.MX8M+ Cortex-A53, Ubuntu Core 20, snap-segregated) | `[CERT-web]` | WebSearch, this session, access date 2026-09-27 (Cochrane Supply/tridium.com TridiumTalk JACE 9000 announcement; TI/tridium.com JACE 8000 datasheets) |
| 14 | No Tridium-published source names "Atlas" as a product/marketing label | `[CERT-web]` | WebSearch, this session, access date 2026-09-27, zero relevant hits (same result [Block 101] §101.x already reported) |

**Tally**: 11 `[CERT-hw]`, 1 `[CERT]`, 2 `[CERT-web]` (adjusted, header legend excluded) · `[INFER]` count:
1 (the JACE 9000 identification, §108.4, explicitly flagged non-`[CERT]`) · ratio `[INFER]`/`[CERT]`-family
= 1/14 ≈ 0.07 (evidence block, low ratio expected — 3 of 4 gaps fully `[CERT-hw]`-closed, the 4th
explicitly reported as `[INFER]`-grade ADVANCED).

**Artifacts** (scratch, not archived, per task instruction — all re-derivable verbatim against the cited
sha256es): `ncsagent.exe` (copy, sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`),
`all_funcs.tsv`, `census.py`/`census_output.txt`, `corroboration.txt`, `downloadparts.objdump.txt`,
`b101g5/n-plugin.jar` (sha256 `eb9831b6…`), `b101g5/vf_out/`, `b101g5/NiagaraModulePlugin.javap.txt`,
`b106g2/probe1-linux-jdk25.txt` — all under
`/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b108/`.
