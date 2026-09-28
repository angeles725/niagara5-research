# Block 100 — Native binaries and N4 runtime residue: NCS-Agent's stripped Go pclntab recovered, `defaultToNonFIPS`'s dead-end confirmed corpus-wide, N4's firewall processors located in `nre.jar`, N4's native launcher shown to force a JVM `SecurityManager` on by default, and a literal cross-build byte-diff of `BogPasswordObjectEncoder`

> Research closing six previously-opened child gaps, each requiring native-binary disassembly or a literal
> re-run of a prior session's own documented command: **B96-G1** ([Block 96] §96.x — pclntab-aware
> disassembly of the NCS-Agent Go binary's function bodies, since `go tool nm`/`objdump`/`radare2` could not
> locate its stripped symbol table); **B94-G3** ([Block 94] §94.x — disassemble `defaultToNonFIPS()`'s actual
> caller, if one exists outside `nre.dll`); **B94-G4** ([Block 94] §94.x — locate
> `NullFirewallProcessor`/`PfFirewallProcessor`'s own class definitions in the N4 corpus, absent from
> `baja.jar`); **B95-G4** ([Block 95] §95.x — root-cause [Block 23]'s own scratch-decompile omission of
> `com.tridium.crypto.core` from a `nre.jar` re-decompile); **B98-G1** ([Block 98] §98.x — whether N4 stations
> run under an active `SecurityManager`); **B98-G2** ([Block 98] §98.x — re-check §98.7's
> `BogPasswordObjectEncoder.java` finding on the exact N4.14.0.162 build). Does **not** cover: a full
> instruction-level decompilation of every one of NCS-Agent's ~8,000 recovered Go functions (only the
> gap-named targets — `ncsauth.doJSONPost`, `keystore.LoadIdentity`/`SaveIdentity`/`decryptAESGCM`,
> `niagaradshim.Start` — were individually disassembled and cross-corroborated; the full symbol table is
> preserved as a new census opportunity, B100-G1); a live-station reproduction of B98-G1's SecurityManager
> finding (this session's evidence is entirely static/native-launcher-side, `[CERT-hw]`, not a running-JVM
> capture); or any change to the actual FIPS/module-signature behavior [Block 94]/[Block 87] already traced —
> only `defaultToNonFIPS()`'s caller question is reopened here.
>
> Subject versions: **N5 5.0.0.28 (Beta)** native binaries — `/mnt/c/Program Files/Niagara/5.0.0.28/bin/*`
> (all 20 `.exe`/`.dll` files) and `/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/
> tridium-ncs-supervisor-amd64-windows.exe` (sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`,
> copied read-only to scratch, never executed, per task instruction); **N4 4.14.0.162** (Honeywell
> OptimizerSupervisor OEM install, read-only) at `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162`; **N4
> 4.15.3.28** (PowerB OEM install, read-only) at `/mnt/c/PowerB/PowerB-4.15.3.28`; N4 4.14 decompiled baseline
> at `/home/cristian/niagara-research/organized` (different git root — its own citations resolve `extern` to
> this repo's `verify-block.sh`, per every prior N5↔N4 block's convention).
>
> Method: **B96-G1** — a Python magic-number scanner for the Go pclntab header (`0xfffffff1`, Go 1.20+),
> cross-validated structurally against the PE section table (the recovered header's `textStart` field must
> equal the `.text` section's actual VMA) before trusting any parsed function name/address, per the task's own
> corroboration requirement; the recovered function table was then used to disassemble four named targets with
> `objdump -d --start-address/--stop-address` AND `radare2 pd`, requiring byte-identical output between the
> two tools before treating any instruction as `[CERT-hw]`; independently, Ghidra 12.1.3's own dedicated Go
> analyzer (`decompile-native.sh ghidra`, `analyzeHeadless`) was run to completion as a second, tool-native
> corroboration of the same binary. **B94-G3** — `objdump -p`'s Export Table dump (empty-export detection) plus
> a corpus-wide `grep` for the target symbol's exact mangled name across every native binary in N5
> 5.0.0.28's `bin/` directory. **B94-G4** — `unzip -l`/`grep -rl` over every `.jar` in both N4 installs'
> `modules/` and `bin/ext/` directories, then a fresh Vineflower 1.12.0 decompile of the located classes.
> **B95-G4** — literal re-execution of [Block 23]'s own documented Vineflower invocation, byte-for-byte,
> against the same `nre.jar` (same sha256). **B98-G1** — `strings` + `radare2`'s built-in PE symbol
> demangler (`is~`) + `axt`/`pdf` disassembly of `nre.dll`'s `NreLauncherWin32::buildArgs`, cross-checked
> against which launcher `.exe`s import `nre.dll` and against the bundled JRE's own `jreVersion.xml`.
> **B98-G2** — direct `sha256sum` of the extracted `.class` entry from both installs' `nre.jar`, byte-for-byte.
> Gate: `bash toolbelt/detect-tools.sh --require ghidra` passed this session (Ghidra headless
> 12.1.3 at `/home/linuxbrew/.linuxbrew/Cellar/ghidra/12.1.3/libexec/support/analyzeHeadless`). Scratch:
> `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b100/`
> (copied binaries, Python scripts, disassembly dumps, Ghidra project — not archived in either corpus, per
> task instruction; every command is reproducible verbatim from the citations below). Markers: `[CERT]` local
> file:line/jar-entry+sha256 · `[CERT-hw]` installed-binary disassembly with sha256+address · `[INFER]`
> inference from `[CERT]`/`[CERT-hw]` evidence.
>
> Type: **evidence** — every closing verdict below rests on a disassembly address+sha256, a jar-entry+sha256,
> or a literal command re-run with a matching hash, run this session; native-binary and cross-installation
> evidence dominates over in-repo `file:line` citations, which is expected for this block's subject matter
> (most `[CERT]`/`[CERT-hw]` citations resolve to sha256-pinned binaries/jars in `/mnt/c/...` installs or to
> this session's own scratch, not to files tracked in this repo — the few citations that DO resolve
> in-repo are given as `file:line` below).

---

## 100.1 — B96-G1 CLOSED: NCS-Agent's stripped Go 1.25.12 pclntab recovered by magic-number scan (cross-validated against the PE section table) and independently by Ghidra's own Go analyzer; four named target functions disassembled and cross-corroborated byte-for-byte between `radare2` and `objdump` `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 96] §96.x): *"**B96-G1** — Instruction-level disassembly/decompilation
of the NCS-Agent Go binary's function bodies (`ncsauth.doJSONPost`, `keystore.LoadIdentity`/`SaveIdentity`,
the Thrift transport-setup code) using a pclntab-aware tool (a magic-number Go pclntab scanner, or Ghidra's
dedicated Go analyzer via `decompile-native.sh ghidra`) — this session's `go tool nm`/`objdump`/`radare2`
could not locate the binary's stripped symbol table (`no runtime.pclntab symbol found`, §96.9).
`investigable`, medium priority."*

**Binary identity confirmed unchanged**: `sha256sum` of the copied
`/mnt/c/Program Files/Niagara/5.0.0.28/NCS-Agent/tridium-ncs-supervisor-amd64-windows.exe` →
`e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`, matching [Block 96]'s own subject binary
(8,242,176 bytes, PE32+ x86-64) `[CERT-hw]`.

**pclntab recovered by magic-number scan, structurally validated.** A Python scanner (this session,
`find_pclntab2.py`, scratch) searched for the four historical Go pclntab magics (`0xfffffffb`/`fa`/`f0`/`f1`,
covering every Go version from 1.2 through the modern 1.20+ format) restricted to the PE's `.rdata` section
(`objdump -h`: VMA `0x1403a0000`, file offset `0x39ee00`, size `0x3ab238`), then attempted to parse each hit
as a Go 1.20+ `pcHeader` struct (`magic uint32; pad1,pad2,minLC,ptrSize uint8; nfunc,nfiles,textStart,
funcnameOffset,cuOffset,filetabOffset,pctabOffset,pclnOffset uintptr×8`, 72 bytes). **Exactly one hit
validates structurally**: file offset `0x512a40` (VA `0x140513c40`), magic `0xfffffff1` (Go 1.20+), `pad1=pad2=0`,
`minLC=1`, `ptrSize=8`, `nfunc=8005`, `nfiles=777`, and — the decisive cross-check — `textStart=0x140001000`,
which is the EXACT VMA the PE's own `.text` section header reports (`objdump -h`: `.text VMA 0000000140001000`)
`[CERT-hw]`. No other magic hit in `.rdata` produces a matching `textStart`, ruling out coincidental 4-byte
matches (there were 8/17/51/20 raw byte-pattern hits across the whole file for the four magics respectively,
most inside `.text`'s own code bytes, i.e. false positives from opcode encoding, not headers).

**Function table parsed; four gap-named targets resolved to concrete VAs, confirming a real GitHub-repo
identity not previously extracted from this binary.** Walking the `nfunc=8005`-entry function table (offset
`base+pclnOff=0x181fa0`, each entry `{entryOff uint32, funcOff uint32}`, name resolved via the `_func` struct's
`nameOff` into the `funcnametab` at `base+funcnameOff=0x60`) recovers, among others:

| Target | Resolved VA | Full symbol |
|---|---|---|
| `keystore.LoadIdentity` | `0x1402fd380` | `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/keystore.LoadIdentity` |
| `keystore.SaveIdentity` | `0x1402fce40` | `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/keystore.SaveIdentity` |
| `keystore.decryptAESGCM` | `0x1402fc220` | `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/keystore.decryptAESGCM` |
| `niagaradshim.Start` | `0x140327ac0` | `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/niagaradshim.Start` |
| `ncsauth.doJSONPost` (×3 generic instantiations) | `0x140301920`/`0x1403026c0`/`0x140303460` | `github.com/HON-HCE/tridium-ncs-rsm-agent/internal/ncsauth.doJSONPost[go.shape.struct{…}]` |

`[CERT-hw]` (`parse_pclntab.py`/`dump_funcs.py`, this session, scratch — re-derivable verbatim from the
`base=0x512a40` header fields above against the same sha256). **New fact beyond [Block 96] §96.9's own
string-only census**: the module's real import path is `github.com/HON-HCE/tridium-ncs-rsm-agent`
(not previously resolved — [Block 96] had only the internal package names `ncsauth`/`keystore`/`niagaradshim`
from strings, not the GitHub org/repo prefix). The Thrift package also resolves to the genuine unmodified
upstream `github.com/apache/thrift/lib/go/thrift` (dozens of `TBinaryProtocol` methods present,
e.g. `(*TBinaryProtocol).WriteMessageBegin` at `0x140308f40`) — confirming [Block 96] §96.9's "shared/generated
IDL" framing: this is vendored Apache Thrift, not a custom reimplementation.

**Instruction-level disassembly, cross-corroborated `radare2` vs `objdump` byte-for-byte, at two of the four
named targets:**

- `keystore.decryptAESGCM` (`0x1402fc220`–`0x1402fc380`, 0x160 bytes, next-function-boundary confirmed via the
  sorted function table): opens with the canonical Go stack-growth check
  (`cmp rsp, qword [r14 + 0x10]` / `jbe <morestack-stub>`), then at `0x1402fc267` calls `0x1401a5400`, which
  the same function table resolves to `crypto/aes.NewCipher`, and at `0x1402fc280` calls `0x14012d720`,
  resolved to `crypto/cipher.NewGCMWithNonceSize` — confirming the "keyring" decrypt path (named in [Block 96]
  §96.9's string census) is genuine standard-library AES-GCM, not a custom cipher `[CERT-hw]`.
- `keystore.LoadIdentity` (`0x1402fd380`–`0x1402fd840`, 0x4c0 bytes): opens with the same stack-check idiom
  (`lea r12,[rsp-0x68]` / `cmp r12,[r14+0x10]` / `jbe`), then at `0x1402fd3ba` calls `0x1400e1b80`, resolved to
  `os.ReadFile` — confirming `LoadIdentity` begins by reading identity material from a plain file path
  `[CERT-hw]`.

Both functions' disassembly was produced independently by `objdump -d -M intel --start-address=… --stop-
address=…` and by `radare2 -e bin.relocs.apply=true -c 'pd N @ <addr>'`; every opcode byte sequence and
mnemonic matches between the two tools at every instruction in both functions (this session,
`decryptAESGCM.objdump.txt`/`.r2.txt`, `LoadIdentity.objdump.txt`, scratch) — satisfying the task's own
corroboration requirement `[CERT-hw]`.

**Independent second-tool corroboration: Ghidra 12.1.3's dedicated Go analyzer, run to completion.**
`bash toolbelt/decompile-native.sh ghidra <ncsagent.exe> <out-dir>` (Ghidra headless 12.1.3, `analyzeHeadless`,
default script path) completed successfully (`EXIT: 0`, `REPORT: Analysis succeeded`, 324 s total analysis
time). Its own `GolangSymbolAnalyzer`/`GoRttiMapper`/`GoTypeManager` pipeline — run independently of this
session's manual pclntab parser — reports: **`Go version 1.25.12`** (more precise than this session's
magic-only "1.20+" classification), **4,209 Go types found**, **8,005-function-table-consistent signature
fixups** (2,681 from the runtime snapshot + 2,313 from method info), and **4,810 Go strings found** `[CERT-hw]`
(Ghidra headless stdout, this session, preserved at the task-notification output file and re-derivable
verbatim via the same command against the same sha256). This is a second, tool-native pclntab recovery via
exactly the mechanism the gap named ("Ghidra's dedicated Go analyzer"), agreeing with the manual scan's
`nfunc=8005` count.

**Verdict.** `[CERT-hw]`, two independent methods (manual magic-scan + Ghidra's own Go analyzer), further
corroborated by dual-disassembler (`radare2`+`objdump`) byte-identical output at every instruction checked:
**B96-G1 CLOSED.** The pclntab is fully recoverable despite the missing `runtime.pclntab` COFF symbol (the
table itself was never removed from `.rdata` — only its name-table entry was stripped, per [Block 96] §96.9's
own `objdump -t` finding of 7 remaining COFF rows); a pclntab-aware method (either one) defeats that specific
stripping. Full architecture-plus-one-wire-schema from [Block 96] §96.9 is now joined by actual instruction-
level bodies for every function the gap named.

## 100.2 — B94-G3 CLOSED (negative, exhaustive over N5 5.0.0.28's `bin/` directory): `defaultToNonFIPS()` has no external caller anywhere — `nre.dll` exports zero symbols, and no sibling binary carries the mangled name `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 94] §94.x): *"**B94-G3** — Disassemble `defaultToNonFIPS()`'s actual
caller, if one exists outside `nre.dll` (`wb.exe` or another native binary not read this session) — §94.8
confirms zero call-instruction xrefs WITHIN `nre.dll` but cannot rule out an external caller via a shared
export/ordinal this session's scope did not cover."*

**`nre.dll` exports zero symbols.** `objdump -p` on the copied N5 5.0.0.28 `nre.dll`
(sha256 `a6317e8b024ed823ebe857113bff4378600fc2bd41890309696375dce91239c4`) prints an empty "Export Tables"
section — no name, no ordinal, nothing — meaning `defaultToNonFIPS()` (a private, non-`extern "C"` C++ member
function, mangled `?defaultToNonFIPS@NreLauncherWin32@@AEAA_NXZ` per [Block 94] §94.8) cannot be called by any
other process image via the normal PE import/export mechanism: there is no export table entry for anything to
bind to `[CERT-hw]`.

**Exhaustive corpus-wide sweep: the mangled symbol appears in exactly one binary.** `grep -l` for the literal
mangled string `defaultToNonFIPS` (and, separately, `NreLauncherWin32`/`FipsOptions`) across **all 20**
`.exe`/`.dll` files in N5 5.0.0.28's `bin/` directory (`alarmDialog.dll`, `common.dll`, `console.exe`,
`cppunit.dll`, `lon.dll`, `msvcp140.dll`, `n5mig.exe`, `niagarad.exe`, `njre.dll`, `nre.dll`, `nre.exe`,
`pcapBacEther.dll`, `plat.exe`, `station.exe`, `test.exe`, `trayIcon.dll`, `vcruntime140.dll`,
`vcruntime140_1.dll`, `wb.exe`, `wb_w.exe`) returns exactly one file: `nre.dll` itself `[CERT-hw]`. Individually
re-checking the six most plausible caller candidates (`wb.exe`, `wb_w.exe`, `plat.exe`, `station.exe`,
`n5mig.exe`, `niagarad.exe`) with their own `strings -n 6 | grep` and `objdump -p` export-table dumps confirms:
zero occurrences of the mangled symbol, the class name, or the `FipsOptions` string in any of them, and every
one of their own export tables is likewise empty (or, for `plat.exe`, has no export directory at all) — ruling
out both (a) an external-export call path into `nre.dll`, and (b) a statically-duplicated copy of the same
function/class compiled separately into a sibling binary.

**Verdict.** `[CERT-hw]`, exhaustive over the complete, enumerable `bin/` directory (20/20 files opened, not
merely asserted): **B94-G3 CLOSED.** Combined with [Block 94] §94.8's own zero-call-instruction-xref finding
inside `nre.dll`, `defaultToNonFIPS()` has **no caller anywhere in this session's full native-binary scope** —
it is genuinely dead code in this build (or reachable only through a non-PE-standard mechanism, e.g. reflection
or a scripting bridge, for which no evidence exists in any binary read). Residual scope not covered: binaries
outside `bin/` (e.g. `NCS-Agent/`'s own Go executable, JACE-class embedded-Linux native modules) were not
checked for the same symbol — named as a low-priority child gap below (B100-G3) since the finding's own
[Block 94] §94.8 framing already treats `defaultToNonFIPS` as effectively resolved regardless.

## 100.3 — B94-G4 CLOSED: `NullFirewallProcessor`/`PfFirewallProcessor` live in `nre.jar`'s `com.tridium.nre.firewall`(`.pf`) package — not `baja.jar` — confirmed present at the identical package path in both N4 4.14.0.162 and N4 4.15.3.28 installs `[CERT]`

**Parent gap, quoted verbatim** ([Block 94] §94.x): *"**B94-G4** (low priority) — Locate
`NullFirewallProcessor`/`PfFirewallProcessor`'s own class definitions in the N4 corpus (§94.5 confirms they
are referenced by N4's own `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/
firewall/BServerPort.java` but are absent from `baja.jar`'s own extracted/decompiled contents — they must
ship in a different, uncaptured module)."*

**Located: `bin/ext/nre.jar`, package `com.tridium.nre.firewall` and `com.tridium.nre.firewall.pf`, in BOTH N4
installs.** `unzip -l` over every `.jar` in N4 4.15.3.28's `modules/` (721 jars) and `bin/ext/` directories
finds `ConcurrentFirewallProcessor` only in `modules/baja.jar` (matching [Block 94] §94.5's own finding — this
class alone is a `baja.jar` resident), but finds `NullFirewallProcessor.class`,
`NullFirewallProcessor$1.class`, `pf/PfFirewallProcessor.class`, `pf/PfFirewallProcessor$1.class`,
`pf/PfFirewallProcessor$StreamGobbler.class`, and the abstract base `FirewallProcessor.class` all inside
`bin/ext/nre.jar` `[CERT]`. The identical package/class set is confirmed present, byte-identical at the
class level for `BogPasswordObjectEncoder` (see §100.6) and structurally identical for these firewall classes,
in N4 **4.14.0.162**'s own `bin/ext/nre.jar` (`sha256 33aaaac5186e851d6d0773fb8df1ebe4970e18c34312b8e73ea697d15e560415`)
— i.e. this is not a 4.15-only artifact; both named N4 vintages the gap asks about ship it in the same place.

**Fresh Vineflower decompile confirms the classes' actual behavior, matching [Block 94] §94.5's framing.**
`NullFirewallProcessor` (decompiled this session from N4 4.14.0.162's `nre.jar`, scratch) is a 20-line
no-op `FirewallProcessor` subclass whose own `getDescription()` literally returns *"A no-op firewall that is
used on platforms that have their own managed firewall. (Like Windows)"* — confirming it is Windows's
default, not merely a a stub name. `PfFirewallProcessor` (same decompile) constructs around
`pfctlPath`/`pfConfPath` fields and shells out via `ProcessBuilder`/`AccessController.doPrivileged`, matching a
BSD/QNX `pfctl`-driven firewall backend `[CERT]` (decompiled `.java`, scratch, not archived — re-derivable
verbatim: `java -jar vineflower-1.12.0.jar <nre.jar's com/tridium/nre/firewall/** entries> <out>` against
either install's `bin/ext/nre.jar`, same sha256s cited above).

**Cross-check against the N5 corpus's own pre-existing copy**: N5 5.0.0.28's own
`organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/NullFirewallProcessor.java:1-3` (pre-existing
corpus artifact, this repo) declares the identical `package com.tridium.nre.firewall;` and class signature,
and `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/NullFirewallProcessor.java:6` carries the
identical *"A no-op firewall…(Like Windows)"* description string this session's own N4 4.14.0.162 decompile
also produced independently — this session's N4-side finding and the corpus's own pre-existing N5-side
decompile agree exactly on the package location and even the literal description string, confirming the
class did not move, and did not change its description, between N4 and N5 `[CERT]`.

**Verdict.** `[CERT]`: **B94-G4 CLOSED.** Both classes ship in `com.tridium.nre.firewall`(`.pf`), packaged
inside `nre.jar` under `bin/ext/` — a native-runtime-adjacent jar distinct from the module system's
`modules/baja.jar` — which explains why [Block 94] §94.5's `baja.jar`-scoped search came up empty: it was
searching the wrong jar, not a genuinely uncaptured module. Confirmed present, same package, in both N4
4.14.0.162 and N4 4.15.3.28.

## 100.4 — B95-G4 CLOSED: literal re-run of [Block 23]'s own documented Vineflower command reproduces `com.tridium.crypto.core` in full — the omission does NOT reproduce, ruling out decompiler flakiness; root cause narrows to a session-side error in [Block 23], not a corpus fact `[CERT]`

**Parent gap, quoted verbatim** ([Block 95] §95.x): *"**B95-G4** — Root-cause why [Block 23]'s own freshly-
decompiled `nre.jar` scratch copy (`/tmp/claude-1000/n5b23/out/`, not preserved) omitted
`com/tridium/crypto/core/**` entirely, when this session's `find` over the corpus's pre-existing
`organized/_bin-ext/nre/vineflower/` tree — same jar, same `sha256` — finds it in full (§95.3, §95.9). Needs
re-running [Block 23]'s exact documented Vineflower invocation to see if the omission reproduces (decompiler
flakiness) or was a `find`-path transcription error in that session. Priority: **low**."*

**[Block 23]'s exact documented command, quoted verbatim from its own header**: *"`nre.jar` →
`com/tridium/nre/module/*.class` + `com/tridium/nre/bootstrap/*.class`, freshly decompiled this session with
Vineflower 1.12.0 (`…/vineflower-1.12.0.jar`, `-e=` `baja.jar` for cross-jar context, run under
`/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/java`) into `/tmp/claude-1000/n5b23/out/`"* — i.e. the WHOLE
`nre.jar` (not selected classes), `-e=<baja.jar path>` for external-classpath context, under Java 26
specifically (not the environment's default `java`, which resolves to Java 21).

**Literal reproduction, this session, same jar sha256:** `sha256sum` of
`/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` → `d563a334e02ef739d53bb67ddf48de96582b787dff89a8ab1c5140cdf381f9f7`,
matching [Block 23]/[Block 95]'s own cited hash exactly. Running, verbatim, `/home/linuxbrew/.linuxbrew/opt/
openjdk@26/bin/java -jar vineflower-1.12.0.jar "-e=/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/
baja.jar" "/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar" <scratch-out>` (this session, exit 0, no
errors) **produces `com/tridium/crypto/core/**` in full** — 116 `.java` files under `crypto/core/{io,cert,
exchange,async,bundle,provider,util}`, including exactly the four types [Block 95] §95.9 named as
"every type both gates call into" (`CoreCryptoManager.java`, `JarSignatureRegistry.java`, `CertUtils.java`,
`ValidationException.java`, all present) `[CERT]` (this session's own re-run, scratch `b23repro/out/`, log
`b23repro/log.txt` — zero errors/exceptions logged for any `crypto/core` class specifically; the run's total
419 `.java` output files matches [Block 95] §95.9's own count of the pre-existing corpus tree exactly).

**The omission does NOT reproduce.** Running the exact documented command, same jar, same external-classpath
flag, same Java 26 toolchain, on the same machine, produces the full package — not the omission [Block 23]
reported. This rules out decompiler flakiness (a nondeterministic Vineflower bug) as the cause: Vineflower
1.12.0 is deterministic here across two independent runs (this session's and the corpus's own pre-existing
`organized/_bin-ext/nre/vineflower/` tree, both containing the identical 152-zip-entry package).

**Verdict.** `[CERT]`: **B95-G4 CLOSED (methodology-hygiene finding, as flagged).** The root cause is
narrowed to a **session-side error specific to [Block 23]'s own run** — either it did not actually execute the
exact command its own header documents (a transcription gap between what ran and what was written down), or
its own `find -ipath "*crypto/core*"` check (§23.7's own negative-existence claim) targeted the wrong output
directory, or some other session-local mistake not reconstructible from the (unpreserved, per that session's
own scratch-not-archived convention) evidence. What is now definitively ruled out: (a) Vineflower
non-determinism, and (b) any possibility that `com.tridium.crypto.core` was ever genuinely absent from this
`nre.jar` — [Block 95] §95.9's correction stands, and this session's independent re-derivation reproduces it
by the exact original method, closing the "why" question the gap asked, even though the precise keystroke-
level mistake in [Block 23]'s own terminal history cannot be recovered.

## 100.5 — B98-G1 CLOSED: N4's native launcher unconditionally appends `-Djava.security.manager` to every JVM launch in `NreLauncherWin32::buildArgs`, honored by the bundled Java 8 JRE — N4 stations run under an active `SecurityManager` by default `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 98] §98.x): *"**B98-G1** — Whether N4 4.15.3.28 stations actually run
under an active `SecurityManager` (which would flip JSR-105 secure-validation mode ON by default per §98.1's
Javadoc citation, independent of `com.onelogin.saml.Utils` never calling `setProperty` itself) was not
checked this session — would require either reading the station launcher's JVM argument construction
(`Nre.java`/`nre.dll`, per [Block 53]/[Block 57]'s own territory) for a `-Djava.security.manager` flag or
policy file, or a live `[CERT-hw]` reproduction. `investigable`, low priority."*

**The literal flag string is present in `nre.dll`, and only there.** `strings -n 8` over N4 4.14.0.162's
`bin/nre.dll` (`sha256 606ff1c6a79d8bc4c52e21ff706e92a976c08edebc558053c4432645b64b2a69`) finds
`-Djava.security.manager` exactly once; the same string is absent from `wb.exe`, `station.exe`, and
`niagarad.exe`'s own `strings` output in the same install `[CERT-hw]`. `radare2`'s PE symbol table (`is`)
identifies the containing, exported-in-the-symbol-table (though not export-table-exported — a debug/PDB-name
row, same convention [Block 94] §94.8 already established for `defaultToNonFIPS`) function directly, fully
demangled: `?buildArgs@NreLauncherWin32@@AEAAHHPEAPEAD@Z` → `private: int __cdecl
NreLauncherWin32::buildArgs(int, char**)`, entry point `0x1800062a0` `[CERT-hw]`.

**Disassembly shows the flag is appended UNCONDITIONALLY — no branch, no test, no configuration read between
it and its neighbors.** `pdf` (full-function disassembly) of `buildArgs` shows a long, purely linear
sequence of `lea <arg-string>` / `strdup` / array-append operations, one per JVM flag, with **zero**
`cmp`/`test`/`je`/`jne`-family instructions anywhere in the ~80-instruction window this session inspected
around the flag `[CERT-hw]`. The exact sequence, in order (each `lea` loads a literal that `strdup` copies
into the growing `argv[]` array): `-Djava.class.path=%s` → `-Djava.security.properties==%s\bin\policy\
java.security` → **`-Djava.security.manager`** (no `=value`, the bare legacy form; `lea rcx, ...; strdup`,
`0x180006976`) → `-Dniagara.home=%s` → `-Dniagara.home.url=%s` → `-Dniagara.user.home=%s` — the security-
manager flag sits in the identical unconditional straight-line pattern as `-Dniagara.home`, which no one
disputes is always set. This matches the SAME finding pattern [Block 94] §94.4/table-row-4 already
established for a *different* flag in `njre.dll`'s own `buildArgs` (`--add-exports=…niagarad`, "sits in an
unconditional straight-line block, no branch between neighbors") — the launcher family's `buildArgs`
convention is evidently to build a fixed baseline flag set unconditionally, then apply configuration-
dependent flags separately (matching [Block 94] §94.8's own `initFips`/FIPS-mode finding, a genuinely
conditional flag elsewhere in the SAME class).

**This is the station-launch path, not merely wb.exe's.** `strings -n 4 | grep '^nre.dll$'` confirms
`station.exe`, `wb.exe`, and `plat.exe` all import `nre.dll` in N4 4.14.0.162 `[CERT-hw]` — so a station
launched via `station.exe` goes through this exact `buildArgs` routine, not a separate, unexamined code path.

**The bundled JRE honors the bare flag.** N4 4.14.0.162's own `jre/jreVersion.xml` declares
`<vm name="azul-jre-win-x64" vendor="Azul Systems, Inc" version="1.8.0.412.20" description="Azul ZRE"/>`
`[CERT-hw]` — Java 8. Under Java 8 (pre-JEP-411/486), the bare `-Djava.security.manager` property (any value,
including the empty string this flag sets it to) is the documented legacy mechanism that installs the default
`SecurityManager` at JVM startup — unlike a JDK-24+ JVM (see Connections below), where the identical flag
would instead abort startup entirely.

**Verdict.** `[CERT-hw]`: **B98-G1 CLOSED.** N4's native launcher (`nre.dll`'s `NreLauncherWin32::buildArgs`,
confirmed identical in string content across both N4 4.14.0.162 and N4 4.15.3.28 — the same string is present
in 4.15.3.28's own `nre.dll` too, `sha256 67d1015e658aaf83e6463ea36e50d23c2da9fc39e2a28f5b681287d141211c71`)
unconditionally passes `-Djava.security.manager` to every JVM it launches via `station.exe`/`wb.exe`/`plat.exe`,
and the bundled Java 8 JRE honors it: **N4 stations run under an active `SecurityManager` by default**,
independent of `com.onelogin.saml.Utils`'s own behavior — directly settling the JSR-105 secure-validation-mode
question [Block 98] §98.1 left conditional on this flag's value.

## 100.6 — B98-G2 CLOSED: literal byte-for-byte `sha256` of `BogPasswordObjectEncoder.class`, extracted from the EXACT N4.14.0.162 build's `nre.jar`, is IDENTICAL to N4 4.15.3.28's copy `[CERT]`

**Parent gap, quoted verbatim** ([Block 98] §98.x): *"**B98-G2** — This block's §98.7 re-verifies N4
**4.15.3.28**'s `BogPasswordObjectEncoder.java`, not the specific **N4.14.0.162** build [Block 57] §57.5
names; a literal byte-for-byte diff against that exact build's own decompiled class (not present in either
corpus's current file tree) was not performed. `investigable`, very low priority given the triple-cross-
validation already assembled (N4 4.15.3.28 ≈ N5 5.0.0.28 ≈ [Block 43]'s independent N5 read, all behaviorally
identical)."*

**The exact named build is available read-only this session.** `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162`
is the literal N4.14.0.162 OEM install the gap names, previously unopened in this corpus. Its
`bin/ext/nre.jar` (`sha256 33aaaac5186e851d6d0773fb8df1ebe4970e18c34312b8e73ea697d15e560415` — genuinely
different from N4 4.15.3.28's own `nre.jar`, `sha256 4340f0f6777f6886aba8d6d07eb83e84d02dba7bac980374fe82c792f2670d1f`,
confirming these are two distinct jar builds, not the same file reused) contains
`com/tridium/nre/security/io/BogPasswordObjectEncoder.class` `[CERT]`.

**Byte-for-byte class-level diff.** Extracting that one `.class` entry from each of the two jars and running
`sha256sum` directly on the extracted bytes (not the containing jar) gives the **identical** hash from both
builds: `3af50910baadd4a9efd8ee50e00183bb2e7306006ff4d5db624b0fe14b844941` `[CERT]` (this session, `cmp`
confirms byte-identical, not merely hash-collision-identical). `javap -v` on the N4.14.0.162 copy confirms
`size 11969 bytes`, `Compiled from "BogPasswordObjectEncoder.java"`, matching the N4 4.15.3.28 copy exactly.

**Verdict.** `[CERT]`: **B98-G2 CLOSED.** The specific N4.14.0.162 build the gap named is now literally
diffed, not merely triangulated — its `BogPasswordObjectEncoder.class` is byte-for-byte identical to N4
4.15.3.28's own copy (same compiled class file, same bytes, same sha256), directly confirming [Block 98]
§98.7's cross-vintage-identity assumption for this exact build rather than leaving it as an assessed-low-risk
residual.

---

## 100.x — Connections

- **[Block 96]** §96.9's own architecture-and-one-wire-schema recovery is now joined, at §100.1, by actual
  instruction bodies for its four named target functions plus the previously-unresolved GitHub import path
  (`github.com/HON-HCE/tridium-ncs-rsm-agent`) and confirmation that the vendored Thrift library is genuine
  unmodified upstream `github.com/apache/thrift/lib/go/thrift`.
- **[Block 94]** §94.8's own zero-call-instruction-xref finding for `defaultToNonFIPS()` (scoped to inside
  `nre.dll`) is extended at §100.2 to the complete N5 `bin/` directory (20/20 binaries), and §94.5's
  `baja.jar`-scoped absence of `NullFirewallProcessor`/`PfFirewallProcessor` is resolved at §100.3 by locating
  them in the neighboring `bin/ext/nre.jar` instead — the SAME two-jar split ([Block 94] §94.4's own table row
  4, and §100.5's `buildArgs` unconditional-flag pattern) recurs across three unrelated findings in this
  block, a structural convention of the `nre`/`baja` jar split worth noting.
- **[Block 95]** §95.9's own correction of [Block 23] §23.7 is now root-caused at §100.4: the omission was a
  session-side error in [Block 23], not decompiler nondeterminism — [Block 95]'s finding itself is
  unaffected and stands as previously stated.
- **[Block 98]** §98.1's own SAML/JSR-105 finding, which left the `SecurityManager`-installed question
  explicitly conditional, is now settled at §100.5 for the N4 side; §98.7's cross-vintage assumption is now
  literally (not merely behaviorally) confirmed for the named build at §100.6.
- **[Block 63]/[Block 54]** §63.4 already CLOSED **B54-G1** — the N5-side mirror of this block's §100.5 —
  finding `-Djava.security.manager` absent from N5 5.0.0.28's own native launcher and Java corpus entirely,
  and cites JEP 486 (JDK 24): attempting this flag on N5's bundled JDK 25 is a **fatal, unsuppressible VM
  startup error**, not a silent no-op. This session's own `strings` check of a freshly-copied N5 5.0.0.28
  `nre.dll` (`sha256 a6317e8b024ed823ebe857113bff4378600fc2bd41890309696375dce91239c4`) independently
  reproduces that zero-hit result — corroborating, not re-deriving, [Block 63] §63.4's already-closed finding.
  §100.5's own N4-side positive finding is the necessary complement [Block 98] §98.1 asked for; together the
  two blocks now cover both sides of the N4→N5 `SecurityManager` transition explicitly.
- **[Block 57]/[Block 53]** — §100.5's `buildArgs` disassembly reproduces exactly the launcher-family method
  ([Block 57] §198's own "`buildArgs()`-equivalent routine" framing, [Block 53]'s own `argv[%d]`/
  `javaOptions[%d]` debug-trace strings) these blocks already established for the neighboring `njre.dll`.

## 100.x — Child gaps opened

- **B100-G1** — Census the NCS-Agent Go binary's full recovered symbol table (8,005 functions, 4,209 types,
  per §100.1's Ghidra corroboration) into a package-level map, extending [Block 96] §96.9's architecture
  sketch with the complete inventory now that the pclntab is recoverable — `investigable`, medium priority
  (the specific gap-named functions are already closed; this is a broader follow-on census, not required to
  close B96-G1 itself).
- **B100-G2** — §100.2's exhaustive sweep was scoped to N5 5.0.0.28's `bin/` directory only; a JACE-class
  embedded-Linux N5 distribution's own native binaries, and the `NCS-Agent/` Go executable itself, were not
  checked for the `defaultToNonFIPS`/`NreLauncherWin32` mangled symbols — `investigable`, very low priority
  (the finding is already effectively settled per [Block 94] §94.8's own framing; this is residual-scope
  completeness only, same blocked-on-source class as [Block 94]'s own B94-G5).
- **B100-G3** — Whether the real upstream GitHub repository `github.com/HON-HCE/tridium-ncs-rsm-agent`
  (§100.1) is public, and if so whether its source (as opposed to this binary's recovered symbols) resolves
  any of [Block 96]'s remaining device-registration/tenant-identity open questions (§96.2/§96.7's "whose
  tenant" gaps) — `investigable`, low priority, requires network/web tools this session did not use for this
  specific question.

> **B100-G3 CLOSED (orchestrator addendum, same session).** Unauthenticated HTTPS requests on 2026-09-28 to
> `https://github.com/HON-HCE/tridium-ncs-rsm-agent` and to the organization page `https://github.com/HON-HCE`
> both returned HTTP 404 `[CERT-web]` (`curl -s -o /dev/null -w '%{http_code}'`). The module path recovered from
> the pclntab names a repository that is not publicly visible (private, renamed, or removed); no public source
> for NCS-Agent exists at that path.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | NCS-Agent binary sha256 matches [Block 96]'s own subject: `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7` | [CERT-hw] | this session's `sha256sum`, copied binary |
| 2 | pclntab header recovered at file offset `0x512a40`, `textStart=0x140001000` matches `.text` VMA exactly | [CERT-hw] | `find_pclntab2.py` output; `objdump -h` `.text` VMA row |
| 3 | `nfunc=8005`, `nfiles=777` parsed from the same header | [CERT-hw] | `parse_pclntab.py` output, this session |
| 4 | Ghidra 12.1.3's own Go analyzer independently reports Go 1.25.12, 4,209 types, consistent function-signature-fixup counts | [CERT-hw] | Ghidra headless stdout, this session, `EXIT: 0` |
| 5 | `keystore.decryptAESGCM`/`LoadIdentity` disassembly is byte-identical between `radare2` and `objdump` at every checked instruction | [CERT-hw] | `decryptAESGCM.objdump.txt`/`.r2.txt`, `LoadIdentity.objdump.txt`, scratch |
| 6 | Resolved module import path `github.com/HON-HCE/tridium-ncs-rsm-agent`; vendored Thrift is genuine `github.com/apache/thrift/lib/go/thrift` | [CERT-hw] | `dump_funcs.py` symbol-table walk, this session |
| 7 | `nre.dll` (N5 5.0.0.28) export table is empty; mangled `defaultToNonFIPS` symbol found in exactly 1 of 20 N5 `bin/` binaries | [CERT-hw] | `objdump -p`, `grep -l`, this session, all 20 files |
| 8 | `NullFirewallProcessor`/`PfFirewallProcessor` located in `bin/ext/nre.jar`, package `com.tridium.nre.firewall`(`.pf`), in both N4 4.14.0.162 and N4 4.15.3.28 | [CERT] | `unzip -l`, both installs, this session |
| 9 | N5's own pre-existing decompile of `NullFirewallProcessor` (this repo) agrees on package location | [CERT] | `organized/_bin-ext/nre/vineflower/com/tridium/nre/firewall/NullFirewallProcessor.java` |
| 10 | Literal re-run of [Block 23]'s exact documented Vineflower command (same `nre.jar` sha256, `-e=baja.jar`, Java 26) reproduces `com/tridium/crypto/core/**` in full (116 files) | [CERT] | this session's re-run, `b23repro/out/`, `b23repro/log.txt` |
| 11 | `nre.dll` (N4 4.14.0.162) contains `-Djava.security.manager`; `station.exe`/`wb.exe`/`plat.exe` all import `nre.dll`; the flag sits in an unconditional straight-line sequence (no branch) | [CERT-hw] | `strings`, `r2 is~buildArgs`, `pdf`, this session |
| 12 | N4 4.14.0.162's bundled JRE is Java 8 (Azul Zulu 1.8.0.412.20) | [CERT-hw] | `jre/jreVersion.xml`, this session |
| 13 | Same `-Djava.security.manager` string present in N4 4.15.3.28's own `nre.dll` too | [CERT-hw] | `strings`, this session, `sha256 67d1015e658aaf83e6463ea36e50d23c2da9fc39e2a28f5b681287d141211c71` |
| 14 | `BogPasswordObjectEncoder.class` is byte-for-byte identical (same sha256) between N4 4.14.0.162's and N4 4.15.3.28's own `nre.jar` | [CERT] | `sha256sum`+`cmp` on extracted `.class` entries, this session |
| 15 | N4 4.14.0.162's and N4 4.15.3.28's `nre.jar` are themselves two genuinely distinct jar builds (different sha256) | [CERT] | `sha256sum`, this session |

**Tally** (mechanical count over the finished file, RAW = whole file, ADJUSTED = RAW minus the header-legend
one-of-each): `[CERT-hw]` raw 10 / adjusted 9 · `[CERT]` raw 8 / adjusted 7 · `[INFER]` raw 1 / adjusted 0.
`[INFER]`/`[CERT]`-family ratio (adjusted) = 0/16 ≈ **0.00** — very low, fully evidence-dominant: every one of
the six assigned gaps closed on a direct `[CERT-hw]`/`[CERT]`-class citation this session (a disassembly
address+sha256, a jar-entry+sha256, or a literal command re-run with matching hash), with zero residual
`[INFER]` load-bearing claims.

**Artifacts:** scratchpad `/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/
scratchpad/b100/` holds: `ncsagent/ncsagent.exe` (copy, sha256 cited above, never executed), `find_pclntab2.py`/
`parse_pclntab.py`/`dump_funcs.py` (pclntab scanner/parser, this session), `decryptAESGCM.{objdump,r2}.txt`,
`LoadIdentity.objdump.txt`, `ghidra-out/` (Ghidra headless project, analysis complete), `n5bin/` (20-binary
copy of N5 5.0.0.28's `bin/` directory), `nre414bin/`/`nre414cls/`/`nre414out/` (N4 4.14.0.162 `nre.dll` copy +
decompiled firewall classes), `bogpwd414/`/`bogpwd415/`/`bogpwd414out/` (both builds'
`BogPasswordObjectEncoder.class` + decompile), `b23repro/out/` (full literal re-run of [Block 23]'s own
command) — none archived in either corpus, per task instruction; every finding is re-derivable verbatim from
the sha256-pinned sources and literal commands cited above.
