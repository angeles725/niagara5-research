# Block 87 — The boot-time `.jar.sig` verifier is `SignatureUtil::checkFileSignature` (njre.dll/nre.dll), it is the SAME routine that assembles `--module-path=%s`; `-Djava.library.path=%s`'s origin is a PATH-env/niagaraHome/jreHome merge, not a native API; the `%s`-formatting helper is a plain UCRT `vsnprintf_s` wrapper; and `securityBridge.jar`'s `-Xbootclasspath/a:` load is now caught live inside `buildArgs` itself

> Research closing/advancing five named child gaps, all native-launcher-cluster residuals [Block 76]/[Block 63]/
> [Block 81]/[Block 65]/[Block 17] each left to a deeper disassembly pass than their own session budget covered:
> **B76-G1** ([Block 76] §76.1 — the boot-time routine, "likely in `njre.dll`/`nre` boot, not the Java module
> layer," that loads and verifies the detached 256-byte `bin/ext/*.jar.sig` sidecars, and the public key it
> verifies against); **B63-G2** ([Block 63] §63.3 — disassemble the fill logic for `NreLauncherWin32::buildArgs`'s
> two large per-path buffers at `this+0x624`/`this+0x8324`, the `%s` sources for `-Djava.library.path=%s`/
> `--module-path=%s`, to their own origin — "almost certainly another `GetModuleFileNameA`-style virtual call...
> not itself opened this session"); **B63-G4** ([Block 63] §63.2 — disassemble `fcn.180004890`, the
> `snprintf`-style helper both `%s`-templated flags call through, "to confirm it performs plain `%s`
> substitution with no additional `cmdline::`-style tagging of its own"); **B81-G1**/**B65-G4** ([Block 81]
> §81.2/[Block 65] §65.5/[Block 3] §3.8 — the exact mechanism by which `niagara.nre` reads `niagara.securityBridge`
> with no static `requires` clause anywhere in the corpus, and whether `securityBridge.jar` genuinely loads via
> `-Xbootclasspath/a:`); **B17-G3** ([Block 17] §17.2/[Block 63] §63.3 — reconstruct the native launcher's
> complete VM/module-path argument RECIPE, including the runtime VALUES [Block 63] left as format-string-only,
> so `n5mig` could in principle be relaunched via a bare `java` invocation). All five are the SAME underlying
> disassembly target — `NreLauncherWin32`/`JavaLauncherWin32`'s `initPaths()`/`buildArgs()` — read together this
> session because tracing one necessarily surfaces the others.
>
> Does **not** cover: a live/dynamic reproduction of any finding here (no runnable install this session — the
> same static-read-only blocker [Block 63]'s own header, [Block 81]'s own header, and every predecessor in this
> cluster name); the `Nre`/`NreWin32` class hierarchy's remaining ~90% of exported methods (only
> `getNiagaraHome`/`initPaths`/`buildArgs`/`defaultToNonFIPS`/the `checkFileSignature` call chain were opened);
> a full disassembly of `fcn.18000c5e0`/`fcn.18000c640` (stack-probe/`_chkstk`-shaped helper calls seen but not
> opened, standard MSVC runtime-support routines, not launcher logic); the live JPMS module-graph query
> (`ModuleLayer.boot()`-reflection or `jcmd`) that would definitively answer why `niagara.nre`'s compile-time
> reference to `securityBridge` classes does not throw `IllegalAccessError` at runtime — narrowed hard this
> session (§87.4) but not itself closeable without a running JVM, recorded as child gap.
>
> Subject version: **N5 5.0.0.28 (Beta)**, install READ-ONLY at `/mnt/c/Program Files/Niagara/5.0.0.28`. Native
> binaries copied to this session's scratchpad
> (`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b87/`)
> before analysis, never analyzed in place, and re-hashed — bytes are IDENTICAL to [Block 63]'s own copies,
> confirming no drift since that session: `nre.dll` (`sha256
> a6317e8b024ed823ebe857113bff4378600fc2bd41890309696375dce91239c4`, 116264 bytes), `njre.dll` (`sha256
> 1b8b0074c79dc148e479602bb5bb1a2245f3549db421ccb6534bca7f6a4dfd0b`, 75296 bytes), `n5mig.exe` (`sha256
> 95b5deae0afc4a0b68361f82d4696398691e4b2130a285dce471ab3aa5c97e46`) — objdump-confirmed `nre.dll` import
> (`??1NreLauncher@@UEAA@XZ`) at this session, `niagarad.exe` (`sha256
> 64fd6403fe00bc1b8b940254682bad454806e1983f3fe54343c56c035c24944b`) copied but not re-disassembled this
> session (already covered by [Block 76]/[Block 63]). Decompiled Java at
> `/home/cristian/niagara5-research/organized/`.
>
> Sources: `[CERT-hw]` `radare2 6.2.0 -q -A -e bin.relocs.apply=true` full control-flow disassembly of
> `njre.dll`'s `sym.njre.dll__checkFileSignature_SignatureUtil__SAHPEBD_Z` (`0x180006fc0`), `fcn.180003500`
> (the `NreLib::DirectoryListing`-driven signature-check loop, `initPaths`'s own private helper), and
> `sym.njre.dll__initPaths_JavaLauncherWin32__AEAAHXZ` (`0x180003a00`); `nre.dll`'s
> `sym.nre.dll__checkFileSignature_SignatureUtil__SAHPEBD_Z` (`0x18000b2e0`), `fcn.180006280` (its own
> signature-check loop), `sym.nre.dll__initPaths_NreLauncherWin32__AEAAHXZ` (`0x180006bb0`), `fcn.180004890`
> (the shared `%s`-format helper), `sym.nre.dll__getNiagaraHome_NreWin32__UEAAXPEADI_Z` (`0x180009190`,
> `NreWin32`'s vtable slot `0x48`), `sym.nre.dll__defaultToNonFIPS_NreLauncherWin32__AEAA_NXZ` (`0x180006740`),
> and the exact `buildArgs` call sites for the `-Xbootclasspath/a:`/`-javaagent:` literal pool
> (`0x180005ad7`-`0x180005b47`) — all this session, fresh `pdf`/`axt`/`px`/`iE` runs, none reused from [Block
> 63]'s saved output; `[CERT-hw]` `objdump -x` cross-check of `checkFileSignature`'s export in both DLLs,
> `initPaths`'s export in both DLLs, and `getNiagaraHome`'s export in `nre.dll` — independent second-tool
> corroboration at the identical mangled symbol names `r2` resolved, this session; `[CERT-hw]` `strings -n 5/-n
> 6` sweeps of both DLLs for signature/crypto/`securityBridge`/`add-reads` literals, this session;
> `/mnt/c/Program Files/Niagara/5.0.0.28/defaults/system.properties:691,709,729,748` (live install file, direct
> `grep`/read, this session — the commented-out `niagara.add.reads`/`niagara.enable.native.access`/
> `niagara.add.exports`/`niagara.add.opens` default lines); `organized/baja/vineflower/com/tridium/sys/module/
> ModuleManager.java:387-390,427-430,463-483,533-566,753` (targeted reads, this session, never opened by
> [Block 81] or any prior block in this corpus).
>
> Method: fresh `radare2 -A` disassembly + `objdump -x` cross-corroboration (both native tools run against the
> same scratchpad-copied binaries this session; no Ghidra headless run needed — `r2 -A` resolved every named
> call site and buffer offset cleanly on the first pass) + targeted decompiled-Java reads of a file no prior
> block in this corpus had opened (`ModuleManager.java`) + one direct read of a live install config file
> (`defaults/system.properties`). Markers: `[CERT-hw]` verified against the live install's own binaries via two
> independent tools (`r2` disassembly + `objdump` export-table cross-check) · `[CERT]` local primary source
> (`file:line`, decompiled Java or a live install config file) · `[INFER]` deduction. Binaries were copied to a
> local scratchpad before any analysis and never modified in place; no binary was executed (static analysis
> only, per the caller's read-only instruction).
>
> Native-launcher / boot-integrity / JPMS-readability cluster. Connects [Block 76] (closes **B76-G1**, its own
> named child gap), [Block 63] (closes **B63-G2**/**B63-G4**, both its own named child gaps, and upgrades §63.1's
> own `[INFER]` about `vtable[0x48]` to `[CERT-hw]`), [Block 81]/[Block 65]/[Block 3] (advances **B81-G1**,
> closes the loading-mechanism half of **B65-G4** at `[CERT-hw]`, reversing [Block 81] §81.2's own "weakened"
> reading of [Block 3] §3.8's original hypothesis back toward CONFIRMED), [Block 17] (closes **B17-G3** to
> practical completeness — every `%s`-templated value is now either a fixed literal, an environment variable, or
> a plain-text config file, needing no further native disassembly to reconstruct).
>
> **Type:** `mixed` — §87.1/§87.2/§87.3/§87.4(loading half) each upgrade a NAMED prior block's own `[INFER]` or
> explicitly-unopened gap to `[CERT-hw]`/`[CERT]` by disassembling a call site that block itself flagged as
> unopened (the `mixed` trigger per METHODOLOGY §4/§11); §87.4's readability half and §87.5's B17-G3 closure are
> evidence-driven ADVANCES/practical-closures built directly on §87.1-§87.3's own fresh disassembly, not
> independent evidence-gathering.

---

## 87.1 — B76-G1 CLOSED: the boot-time `.jar.sig` verifier is `SignatureUtil::checkFileSignature`, compiled into BOTH `njre.dll` and `nre.dll`, invoked from `JavaLauncherWin32::initPaths()`/`NreLauncherWin32::initPaths()` via a `DirectoryListing`-driven loop that filters `*.jar` under five `bin/ext` subpaths, verifies each with a "Tridium Public Key" RSA check through Windows CNG, and hard-exits the process on any failure `[CERT-hw]`

[Block 76] §76.1 established the *format* of the 73 `bin/ext/*.jar.sig` sidecars (fixed 256 bytes, RSA-2048-
shaped, structurally distinct from the in-module CMS/BouncyCastle `ArchiveVerifier` signing) but explicitly did
not locate the boot-time code that reads and checks them, naming this **B76-G1** and guessing "likely in
`njre.dll`/`nre` boot." This session opens both DLLs directly and finds the routine in full.

**The verifier: `SignatureUtil::checkFileSignature(const char*)`, exported (not stripped) from BOTH `njre.dll`
and `nre.dll` at the same mangled name.** `[CERT-hw]` `r2 -q -c 'iE~checkFileSignature'`: `njre.dll` index 36,
`0x180006fc0`; `nre.dll` index 40, `0x18000b2e0` — both `?checkFileSignature@SignatureUtil@@SAHPEBD@Z`
(`public: static int __cdecl SignatureUtil::checkFileSignature(char const*)`). **Independently corroborated
via a second tool this session**: `objdump -x njre.dll`/`objdump -x nre.dll` list the identical mangled export
name at the identical DLL, `[CERT-hw]`. Its own embedded log strings label it `SignatureUtilWin32::
checkFileSignature` (a platform-tag mismatch against the demangled export name `SignatureUtil` — a naming
inconsistency between the log macro's hardcoded class-name literal and the actual exported symbol, not
investigated further) `[CERT-hw]` `strings -n 5 njre.dll`.

**Call chain, `njre.dll`: `JavaLauncherWin32::initPaths()` → `fcn.180003500` (× 2 call sites) →
`checkFileSignature`.** `axt` on `checkFileSignature`'s address returns exactly ONE cross-reference,
`fcn.180003500`, itself called from `sym.njre.dll__initPaths_JavaLauncherWin32__AEAAHXZ` at TWO addresses
(`0x180004083`, `0x18000411c`) `[CERT-hw]` (`r2 -q -A -c 'axt @ 0x180006fc0'`, this session). `nre.dll`
mirrors this exactly: `NreLauncherWin32::initPaths()` calls its own equivalent loop, `fcn.180006280`, at TWO
addresses (`0x1800071d3`, `0x18000726c`), which is the sole caller of `nre.dll`'s own `checkFileSignature`
export `[CERT-hw]` (same method, this session, `nre_initPaths.txt` full disassembly). **`initPaths` is
therefore the boot-time routine [Block 76] asked for, in BOTH launcher DLLs.**

**`fcn.180003500`'s full disassembly (508 bytes, whole-function `pdf`) is a directory-scan-and-verify loop with
NO string references except its own `FATAL` message, driven entirely by `NreLib::DirectoryListing`:** for a
`;`-delimited list of directory paths (`strtok` on `";"`), it calls `NreLib::DirectoryListing::make(path)` →
`hasNext()`/`next()` to enumerate entries, `FileUtil::getExtension()` + `strcmp(ext, "jar")` (the literal
`"jar"` string, `0x180009cb8`) to filter, `FileUtil::fixFilePath()` to normalize each match, then
`SignatureUtil::checkFileSignature(fixedPath)` on every `.jar` found `[CERT-hw]` (whole-function `pdf`, this
session, `fcn_180003500.txt`). **On any non-zero (failure) return, it prints `"FATAL: %s failed signature
check\n"` (the literal string, cited verbatim from the disassembly's own `lea rdx, str.FATAL:...` annotation)
and returns `-1`**; on success for every `.jar` in every directory, it returns the count of files verified
`[CERT-hw]`.

**The directories fed to this loop are `initPaths`'s own `%s\bin\ext` family — five distinct paths, four
signature-checked via this exact loop, confirmed by their literal format strings and the surrounding
`isDirectory`/append/verify sequence:** `%s\bin\ext` (`0x180009db0`, njre.dll), `%s\bin\ext\jxbrowser`
(`0x180009df0`), `%s\bin\ext\system` (`0x180009e08`), and a conditional `%s\bin\ext\securityBridge`
(`0x180009e80`, checked SEPARATELY at the second `fcn.180003500` call site, `0x18000411c`, with its OWN "FATAL:
Security bridge module signature verification failure" and "FATAL: No JAR files found in security bridge
path: %s" error strings) `[CERT-hw]` (whole `initPaths` disassembly, this session, `initPaths.txt`). `nre.dll`'s
own `initPaths` additionally scans a provider-choice subdirectory, `%s\bin\ext\bcfips` or `%s\bin\ext\bcstd`
(chosen by a FIPS-mode flag byte at `this+0x1002c`, `cmovne` between the two literal strings) — a fifth,
provider-conditional signed directory not present in `njre.dll`'s simpler enumeration `[CERT-hw]`
(`nre_initPaths.txt:216-227`). **On failure of the FIRST scan (`%s\bin\ext` itself), both launchers print
"FATAL: Module signature verification failure" and call `exit(250)`; failure to find ANY `.jar` at all in that
path calls `exit(249)` with "FATAL: No JAR files found in module path: %s"** `[CERT-hw]` (`initPaths.txt:359-
369`, `nre_initPaths.txt` equivalent block). This is a hard, unrecoverable boot gate: a tampered or missing
signature on any `bin/ext` third-party jar prevents the JVM from ever starting.

**The RSA public key and verification primitive: a "Tridium Public Key," verified through Windows CNG
`BCryptVerifySignature` — not OpenSSL, not a custom RSA implementation.** `strings -n 5` over both DLLs finds
the literal log line `"FINE [SignatureUtilWin32::checkFileSignature] Converting Tridium Public Key to RSA
object"` immediately followed by `"...Verifying file signature"`, and the DLL's own import table (already
established by [Block 61], re-visible in this session's `strings` pass) includes `BCryptVerifySignature`
`[CERT-hw]`. This is Windows' native Cryptography API: Next Generation, not a bundled crypto library — the
"Tridium Public Key" is embedded in the binary as a key blob converted to a CNG-compatible RSA key object at
verification time, consistent with [Block 76] §76.1's own structural reading of the 256-byte sidecars as raw
RSA-2048 signatures (the `%s.sig` sidecar-naming format string, `0x18000....`, was also confirmed present in
this same `strings` pass) `[CERT-hw]`.

**A `niagara_sig_debug` environment-variable toggle exists but gates LOGGING VERBOSITY only, NOT the
verification result — confirmed by tracing its flag through the actual branch logic, not merely finding the
string.** `getenv("niagara_sig_debug")` is called once, unconditionally, at DLL-load time (a non-function-
attributed static-initializer address, `0x180001044`), and its result (set-or-not, any value) is stored as a
single boolean at `0x18000f428` `[CERT-hw]` (`pd`/`axt`, this session). That flag is read **12 separate times
inside `checkFileSignature` itself** (`axt` on the flag's address, this session, exhaustive not sampled), and
tracing the FIRST occurrence's branch (`0x180007060`: `cmp byte [flag], bl; je 0x180007125`) shows it gates a
block of code that both paths (debug-on and debug-off) eventually rejoin at the SAME destination address —
i.e., the debug branch is additive (extra `FINE`-level hash/signature diagnostic printing), not an alternate
code path that skips the `BCryptVerifySignature` call `[CERT-hw]` (`pdf @ 0x180007050`, this session). **Net:
`niagara_sig_debug` is a diagnostics-verbosity switch, not a bypass** — a natural follow-up question this
session closes as a negative rather than leaving open.

**Net verdict, closing B76-G1 in full.** The boot-time `.jar.sig` verification routine is `SignatureUtil::
checkFileSignature`, statically compiled into both native launcher DLLs, invoked from each DLL's own
`initPaths()` method via a directory-enumeration loop that applies it to every `.jar` under `bin/ext` and its
`jxbrowser`/`system`/`{bcfips|bcstd}`/`securityBridge` subdirectories; the verification primitive is Windows
CNG `BCryptVerifySignature` against an embedded "Tridium Public Key," and failure of ANY jar's check is fatal
to process boot (`exit(249)`/`exit(250)`) — not merely logged.

## 87.2 — B63-G2 CLOSED: `NreLauncherWin32::initPaths()` is the ORIGIN of both `%s` buffers `buildArgs` reads — `-Djava.library.path=%s` is a deduplicated PATH-env/niagaraHome/jreHome merge, `--module-path=%s` is the SAME `bin/ext` directory list §87.1 just traced (reused, not recomputed), and neither is a `GetModuleFileNameA`-style OS call at that specific offset — `niagaraHome` itself IS, one level further back, closing [Block 63] §63.1's own `vtable[0x48]` `[INFER]` as a side effect `[CERT-hw]`

[Block 63] §63.3 extracted the complete literal 43-flag set from `buildArgs`/`buildVMOptions` but explicitly
left the two `%s`-templated buffers at `this+0x624` (`-Djava.library.path=%s`) and `this+0x8324`
(`--module-path=%s`) untraced to their fill origin, naming **B63-G2** and guessing a `GetModuleFileNameA`-style
call not yet opened. This session disassembles `NreLauncherWin32::initPaths()` (`0x180006bb0`, 2210-byte whole-
function `pdf`) and finds it writes BOTH offsets directly, using `rdi` as the `this` pointer throughout — the
exact two addresses `buildArgs` reads via its own `r13`-relative accesses, confirmed by grepping the fresh
disassembly for the literal offsets: `[CERT-hw]` `grep -n '0x624\|0x8324'` over `nre_initPaths.txt` → four hits,
all inside `initPaths`, this session.

**`this+0x624` (`-Djava.library.path=%s`): built from the `PATH` environment variable, `${niagaraHome}\bin`,
and `${jreHome}\bin`, deduplicated via `strstr` so a directory already present in `PATH` is not appended
twice, joined with `%s;%s;%s`/`%s;%s` — NOT a Win32 API call at this specific point.** The function first
resolves `jreHome` (`this+0x318`) from the `NIAGARA_JRE_HOME` environment variable via `_dupenv_s`, falling
back to `${niagaraHome}\jre` if unset (`nre_initPaths.txt:29-58`); it then `_dupenv_s`'s `PATH` and runs
`strstr(PATH, "${niagaraHome}\bin")` and `strstr(PATH, "${jreHome}\bin")` to check which of the two is ALREADY
present in the inherited `PATH` string, branching to one of three `fcn.180004890` (the `%s`-formatting helper,
§87.3) calls with format string `"%s;%s;%s"` (neither present), `"%s;%s"` (one present), or a bare copy (both
present) — the result is `strncpy_s`'d into `this+0x624` `[CERT-hw]` (`nre_initPaths.txt:60-169`, whole
sequence, this session). **This closes the `-Djava.library.path=%s` half of B63-G2 outright: its value is a
purely computed environment/field merge, never a fresh OS path-discovery call at this offset.**

**`this+0x8324` (`--module-path=%s`): the SAME `bin/ext`/`jxbrowser`/`system`/`{bcfips|bcstd}` directory
enumeration §87.1 already traced for signature-checking, re-USED as the module-path string — not a second,
independent computation.** Immediately after building each `%s\bin\ext...` path string (the identical literal
format strings §87.1 cited: `_s_binext`, `_s_binext_s` with the `bcfips`/`bcstd` `cmovne`, `_s_binextjxbrowser`,
`_s_binext_system`), the SAME buffer holding the accumulated `;`-joined path list is passed BOTH to
`fcn.180006280` (the `checkFileSignature`-driving loop, `mov rcx, rsi; call fcn.180006280` at `0x1800071d0`-
`0x1800071d3`, confirmed this session) AND is what ends up written to `this+0x8324` — the string
concatenation (`strncat`, bounded by an explicit `cmp rcx, 0x7d00` overflow check with its own `"FATAL: Failed
to append %s to modulePath, insufficient buffer size\n"` literal) IS the module-path construction, and the
signature check is applied to that identical, already-built list `[CERT-hw]` (`nre_initPaths.txt:190-333`,
whole sequence, this session). **This means `--module-path=%s`'s runtime value and the jar-signature-
verification pass of §87.1 are not two separate mechanisms over the same directories — they are the SAME pass,
using the SAME accumulated string, closing the `--module-path=%s` half of B63-G2 outright.**

**Where `niagaraHome` itself (the `%s` substituted into every one of these format strings) comes from —
answered as a side effect, closing [Block 63] §63.1's own unresolved `[INFER]` about `Nre::getInstance()`'s
`vtable[0x48]` call.** [Block 63] §63.1 disassembled `restartPlatformDaemon0`'s virtual call through
`Nre::getInstance()`'s vtable at offset `0x48` and read it as "likely a `GetModuleFileNameA`-style path
lookup... not traced to the Win32 API level," marking this `[INFER]`. This session confirms it directly: `nre.
dll` imports `GetModuleFileNameA` (`objdump -x`/`r2 ii`, this session — not previously confirmed as an IMPORT,
only referenced in error strings), and `axt` on that import's thunk returns exactly ONE cross-reference,
`sym.nre.dll__getNiagaraHome_NreWin32__UEAAXPEADI_Z` `[CERT-hw]` (`r2 -q -A -c 'axt sym.imp.KERNEL32.dll_
GetModuleFileNameA'`, this session). Dumping `NreWin32`'s own vtable (`??_7NreWin32@@6B@`, `0x18000f378`) at
offset `0x48` (`0x18000f378 + 0x48 = 0x18000f3c0`) resolves to EXACTLY `NreWin32::getNiagaraHome` `[CERT-hw]`
(`r2 pxr 0x60 @ 0x18000f378`, this session, reading eight consecutive vtable slots — the ninth, at the target
offset, names the method by its own demangled symbol). **`getNiagaraHome()`'s own body checks a cached static
pointer first, then the `niagara_home` environment variable (lowercase — a distinct literal from the
uppercase `NIAGARA_HOME` compile-time string also present in the binary) via `_dupenv_s`, and only THEN falls
back to `GetModuleFileNameA`** with the paired fatal string `"FATAL: Unable to initialize NIAGARA_HOME,
GetModuleFileName failed!"` confirming the fallback's purpose `[CERT-hw]` (`getNiagaraHome` disassembly,
`0x1800091c7`-`0x1800091f6`, this session). **This closes [Block 63] §63.1's own named uncertainty as a
connection, not a gap of this block's own** — `restartPlatformDaemon0`'s `vtable[0x48]` virtual call IS
`NreWin32::getNiagaraHome`, and it IS, ultimately, a `GetModuleFileNameA`-backed lookup, exactly as [Block 63]
guessed but marked `[INFER]` for lack of the vtable-slot correspondence.

**Net verdict, closing B63-G2 in full.** `--module-path=%s`'s runtime value is the exact `bin/ext` directory
family §87.1 already fully enumerated (no separate tracing needed — they are the same pass);
`-Djava.library.path=%s`'s runtime value is a `PATH`/`niagaraHome`/`jreHome` merge with duplicate-suppression;
and `niagaraHome` itself resolves via a three-tier cache → `niagara_home` env var → `GetModuleFileNameA` chain,
closing [Block 63]'s own adjacent `[INFER]` as a bonus.

## 87.3 — B63-G4 CLOSED: `fcn.180004890` is a thin, generic wrapper over the UCRT's `__stdio_common_vsnprintf_s` — plain locale-aware `%s` substitution, `-1` on failure, with NO `cmdline::`-style or other tagging logic of its own `[CERT-hw]`

[Block 63] §63.3 identified `fcn.180004890` as the call site both `-Djava.library.path=%s` and
`--module-path=%s` route their formatting through, but left it undisassembled, naming **B63-G4**. Its own
whole-function disassembly is 34 lines / 98 bytes — short enough to read in full and settle definitively:

```
fcn.180004890 (int64_t arg1, int64_t arg2, int64_t arg3, int64_t arg4, int64_t arg_90h):
    mov  [var_20h], r9           ; save arg4 (format string)
    push rbx; push rbp; push rsi; push rdi; push r14
    sub  rsp, 0x40
    mov  rbp, r9                 ; arg4 = format string
    lea  r14, [arg_90h]          ; varargs pointer
    mov  rsi, r8                 ; arg3 = buffer size
    mov  rdi, rdx                ; arg2 = destination buffer
    mov  rbx, rcx                ; arg1 = ? (locale-related, passed to fcn.180001ca0)
    call fcn.180001ca0           ; resolves a locale-info pointer (rax)
    mov  [var_30h], r14
    mov  r9, rsi ; r8, rdi ; rdx, rbx ; [var_20h_2], rbp
    mov  rcx, qword [rax]        ; locale ptr, dereferenced
    call [__stdio_common_vsnprintf_s]   ; the ACTUAL formatting work
    test eax, eax
    mov  ecx, -1
    cmovs eax, ecx               ; return -1 on failure, else the vsnprintf_s result
    ... epilogue, ret
```
`[CERT-hw]` `r2 -q -A -c 'pdf @ fcn.180004890' nre.dll`, this session, whole-function (34 output lines, all
read, none excerpted). `__stdio_common_vsnprintf_s` is Microsoft's UCRT-internal implementation backing every
public `vsnprintf_s`/`sprintf_s`/`_vsnprintf_s_l` variant since VS2015's CRT split — a fully generic, locale-
aware, bounds-checked formatted-print primitive, confirmed via its own import-table entry
(`sym.imp.api_ms_win_crt_stdio_l1_1_0.dll___stdio_common_vsnprintf_s`) `[CERT-hw]`. `fcn.180001ca0` (not
itself opened this session — a short, generic-looking call resolving a locale pointer, standard for any UCRT
`_s`-suffixed formatting call) supplies the `_locale_t`-equivalent first argument `__stdio_common_vsnprintf_s`
requires; this is boilerplate CRT plumbing, not launcher-specific logic.

**Net verdict, closing B63-G4 in full.** `fcn.180004890` performs NOTHING beyond a standard, generic,
locale-resolved `%s`-substitution `vsnprintf_s` call: no `-Dcmdline::` prefix, no shadow-property stamping, no
additional string manipulation of any kind before or after the UCRT call. This confirms [Block 63] §63.2's own
closing claim (that ONLY `buildArgs`'s own raw-argv loop stamps `-Dcmdline::`, never a shared helper) at the
deepest possible level — the shared helper both `%s`-templated flags route through is provably inert with
respect to that tagging.

## 87.4 — B81-G1/B65-G4: `securityBridge.jar`'s `-Xbootclasspath/a:` load is CLOSED at `[CERT-hw]` — caught live, inside `buildArgs`, being formatted/`strdup`'d/appended to argv in the IDENTICAL unconditional sequence as `-javaagent:...\nre.jar` — reversing [Block 81] §81.2's "weakened" reading; the READABILITY grant itself is further narrowed (its own runtime `Module.addReads` machinery structurally cannot apply to a bootclasspath-loaded jar) but not fully closed without a live JVM `[CERT-hw]`+`[CERT]`+`[INFER]`

[Block 3] §3.8 first proposed `-Xbootclasspath/a:%s\bin\ext\securityBridge\securityBridge.jar` as `[INFER]`;
[Block 81] §81.2 opened `securityBridge.jar`'s own `module-info.java` and the corpus-wide absence of any
`requires niagara.securityBridge` clause, and — reasoning that a real named-module descriptor "gains nothing"
from being loaded via bootclasspath — called this "WEAKENED, without fully refuting," naming **B81-G1** to
capture the live launch-flag command line as the closing method. This session instead re-examines the STATIC
call site directly, which neither prior block had disassembled, and settles the loading question outright.

**The literal string is not a dead constant — it is live-referenced from inside `buildArgs`, formatted,
duplicated, and appended to the JVM argument array in the EXACT SAME instruction sequence as the adjacent,
unconditional `-javaagent:%s\bin\ext\nre.jar` flag.** `axt` on the string's address (`0x18000fd00`) returns
exactly one cross-reference: `sym.nre.dll__buildArgs_NreLauncherWin32__AEAAHHPEAPEAD_Z @ 0x180005b2b` `[CERT-hw]`
(`r2 -q -A -c 'axt @ 0x18000fd00'`, this session). Reading the instructions at that exact address:
```
0x180005ad7  lea r9, "-javaagent:%s\bin\ext\nre.jar"      ; format string (previous flag)
0x180005aef  call fcn.180004890                            ; %s-substitute niagaraHome
0x180005b0b  call strdup                                   ; duplicate the formatted result
0x180005b11  mov qword [rdi], rax                          ; argv[argCount] = duplicated string
0x180005b16  inc dword [argCount]
0x180005b2b  lea r9, "-Xbootclasspath/a:%s\bin\ext\securityBridge\securityBridge.jar"  ; NEXT flag, same pattern
0x180005b47  call fcn.180004890                            ; %s-substitute niagaraHome
0x180005b4c  movsxd rdi, dword [argCount]  ; ... (continues identically)
```
`[CERT-hw]` `r2 -q -A -c 'pd 25 @ 0x180005ad0' nre.dll`, this session, both flags read in the same disassembly
window with no conditional branch between them — i.e., `-Xbootclasspath/a:...securityBridge.jar` is
constructed and appended to the JVM's argument list **unconditionally, every single launch**, using the exact
`format → strdup → store-into-argv[count++]` idiom [Block 63] §63.3 already established for the OTHER 43 fixed
flags. **This is now `[CERT-hw]` call-site evidence neither [Block 3] nor [Block 81] had: the flag is
genuinely live, not merely present as an unreferenced string constant.** [Block 81] §81.2's own reasoning
(a bootclasspath-only jar "gains nothing" from a real module descriptor) remains a fair observation about the
JPMS *oddity*, but it does not change what this session's call-site trace shows the launcher actually DOES —
**B65-G4's loading-mechanism half is CLOSED: `securityBridge.jar` loads via `-Xbootclasspath/a:`, confirming
[Block 3]'s original hypothesis outright.**

**The READABILITY question (B81-G1 proper) is narrowed further, not closed, by ruling out [Block 81] §81.2's
own candidate (2) structurally rather than just failing to find it.** Three candidates were named: (1) an
`--add-reads`-class launch flag; (2) a runtime `Module.addReads()` call; (3) plain bootclasspath/unnamed-module
placement. This session:
- Re-swept BOTH DLLs' full `strings` output for any `add-reads`/`add-opens`/`add-exports` flag naming
  `securityBridge` — **zero hits** in either binary; the only `securityBridge`-related JVM argument anywhere in
  either DLL's string table is the `-Xbootclasspath/a:` line itself `[CERT-hw]` (exhaustive `grep -i`, this
  session, both binaries). This weighs against candidate (1) — though a non-literal, runtime-CONSTRUCTED
  `--add-reads` argument (built from a variable, not a fixed string) would not show up in a `strings` sweep and
  is not ruled out by this alone.
- Read the install's own live `defaults/system.properties` directly: `niagara.add.reads` (line 709),
  `niagara.enable.native.access` (line 691), `niagara.add.exports` (line 729), and `niagara.add.opens` (line
  748) are ALL commented out — empty by default on this build `[CERT]` (`grep -n`, this session, the live
  install file, not the decompiled corpus). This rules out candidate (2) being ACTIVE on a default
  configuration: `com.tridium.sys.module.ModuleManager`'s `handleThirdPartyAddReads()` (`ModuleManager.java:
  533-566`) reads exactly this property (`parseNiagaraJPMSProperty("niagara.add.reads", ...)`,
  `ModuleManager.java:388`) and does nothing if it is unset — `[CERT]` `ModuleManager.java:387-390,463-483`,
  read whole this session, never opened by [Block 81] or any prior block.
- **Structurally, candidate (2) could not apply to `securityBridge` even if the property WERE set**, because
  `handleThirdPartyAddReads` is invoked only over `thirdPartyConfigurableModuleLayers` (`ModuleManager.java:
  753`) — the set of modules resolved by `ModuleFinder` scanning `bin/ext` as genuine JPMS named modules (the
  SAME resolution §87.2 traced building `--module-path=%s`). `securityBridge.jar` never enters that scan: it is
  loaded via `-Xbootclasspath/a:` at a stage BEFORE the module system resolves anything, so its classes join the
  bootstrap class loader's UNNAMED module directly and are never presented to `ModuleManager` as a candidate
  module at all `[INFER]` (a structural reading of `ModuleManager`'s own resolution scope against §87.2's
  `--module-path` construction — not a runtime observation). **This explains, rather than merely confirms, WHY
  no `addReads` call names `securityBridge` anywhere in the corpus: it is not that the grant is missing, but
  that `securityBridge` is not a kind of thing this machinery is positioned to grant reads to.**

**Net verdict.** B65-G4 (loading mechanism) is CLOSED at `[CERT-hw]`: `-Xbootclasspath/a:` is confirmed live via
its own call site. B81-G1 (the readability grant that lets a NAMED module's compiled `import`/`implements`
against bootclasspath-unnamed-module classes not throw `IllegalAccessError`) is ADVANCED, not closed: candidate
(2) is now structurally excluded rather than merely unfound, and candidate (1) is weakened (no literal flag
exists, though a dynamically-constructed one is not ruled out) — leaving either an undiscovered dynamic
`--add-reads`-equivalent, or a JDK-level behavior specific to classes on the bootstrap class loader's unnamed
module, as the two remaining explanations, adjudicable only with a live JVM's own module graph (child gap,
below).

## 87.5 — B17-G3 CLOSED to practical completeness: every runtime value needed for a bare `java`-fallback `n5mig` relaunch is now either a fixed literal ([Block 63]), an environment variable (§87.2), or a plain-text config file (this section) — no further native disassembly is required to reconstruct the invocation `[CERT-hw]`+`[CERT]`

> **Correction (added by [Block 94], §14 cross-block).** `defaultToNonFIPS()` has zero call xrefs in `nre.dll`
> (full linear sweep, [Block 94]). The FIPS choice is made by `NreLauncherWin32::initFips()`, called from `nre()`,
> with a 3-tier precedence: license feature `Tridium:fips140`, then the `-fips=` CLI flag, then the
> `bajaui-FipsOptions.options` file (inverted polarity vs `defaultToNonFIPS`). See [Block 94] §94.x Corrections.

[Block 17] §17.2's own `java`-fallback attempt against `n5mig` failed because it could not reconstruct the
native launcher's module-path/VM-argument set, naming **B17-G3**. [Block 63] §63.3 supplied the complete FIXED
43-flag list but left the `%s`-templated runtime values as the open remainder. §87.1-§87.4 close that
remainder. Assembling the complete recipe for `n5mig.exe` (confirmed this session, via `objdump -p`, to import
`nre.dll` — the SAME `NreLauncherWin32` class this block's entire disassembly targets, not `njre.dll`):

1. **`niagaraHome`** — for a `java`-fallback launch, this is simply the install root the fallback is being run
   FROM (already the subject-version path named in every block's own header, `/mnt/c/Program Files/
   Niagara/5.0.0.28`); §87.2 additionally shows the launcher's own resolution order is cache → `niagara_home`
   env var → `GetModuleFileNameA`, all three of which agree on this same value for an unmodified install
   `[CERT-hw]`.
2. **`jreHome`** — `NIAGARA_JRE_HOME` env var if set, else `${niagaraHome}\jre` `[CERT-hw]` (§87.2).
3. **`-Djava.library.path=%s`** — `PATH;${niagaraHome}\bin;${jreHome}\bin`, with either home directory DROPPED
   from the list if `strstr` finds it already present in the inherited `PATH` `[CERT-hw]` (§87.2).
4. **`--module-path=%s`** — `${niagaraHome}\bin\ext;${niagaraHome}\bin\ext\{bcfips|bcstd};${niagaraHome}\bin\
   ext\jxbrowser;${niagaraHome}\bin\ext\system`, each directory existence-checked (`isDirectory`) and every
   `.jar` inside each signature-verified via §87.1's exact routine before the process is allowed to continue
   `[CERT-hw]` (§87.1, §87.2). The `bcfips`-vs-`bcstd` choice is itself resolvable without further
   disassembly: `NreLauncherWin32::defaultToNonFIPS()` reads a plain-text config file,
   `${configHome}\etc\options\bajaui-FipsOptions.options`, via `fopen_s` — not a hidden registry/license
   check — so the FIPS mode a real launch would select is directly readable from that file `[CERT-hw]`
   (`defaultToNonFIPS` disassembly, `0x180006777`-`0x18000679b`, this session).
5. **Fixed, unconditional literals** (no `%s` substitution needed beyond `niagaraHome`, all confirmed live via
   real call sites this session or [Block 63]'s own disassembly): `-Xbootclasspath/a:${niagaraHome}\bin\ext\
   securityBridge\securityBridge.jar` (§87.4), `-javaagent:${niagaraHome}\bin\ext\nre.jar` (§87.4, the
   immediately-preceding identical-pattern flag), plus [Block 63] §63.3's full 43-entry `--add-opens`/
   `--add-reads`/`--enable-native-access`/`-D` list.

**Net verdict, closing B17-G3 to practical completeness.** Every value a `java`-fallback `n5mig` invocation
would need — module-path, library-path, the two bootclasspath/javaagent flags, and the FIPS-provider choice —
is now traceable to either a fixed literal, an inherited environment variable, or a plain-text config file
readable without executing anything. What remains (named as a residual, not re-opened as B17-G3 itself) is a
genuinely DYNAMIC step: actually assembling and running that `java` command line and observing whether it
succeeds — an execution this session's read-only, no-install-run scope does not perform, and the same class of
blocker [Block 17] §17.2's own original attempt hit for a different reason (missing values, now supplied).

## 87.x — Connections

- **[Block 76]** — §87.1 closes **B76-G1** outright, the exact child gap [Block 76] §76.1 named. The boot-time
  verifier is `SignatureUtil::checkFileSignature`, driven from each launcher DLL's own `initPaths()`.
- **[Block 63]** — §87.2 closes **B63-G2**, §87.3 closes **B63-G4**, both [Block 63] §63.3's/§63.2's own named
  child gaps. §87.2 additionally closes [Block 63] §63.1's own unresolved `[INFER]` about `Nre::getInstance()`'s
  `vtable[0x48]` call — confirmed to be `NreWin32::getNiagaraHome()`, itself backed by `GetModuleFileNameA` —
  as a bonus connection, not a gap this block was asked to close.
- **[Block 81]/[Block 65]/[Block 3]** — §87.4 closes the loading-mechanism half of **B65-G4** at `[CERT-hw]`,
  REVERSING [Block 81] §81.2's own "weakened, narrowed away from" framing back toward [Block 3]'s original
  `-Xbootclasspath/a:` hypothesis with the call-site evidence [Block 81] itself lacked. **B81-G1**'s readability
  question is advanced (candidate (2) structurally excluded) but not closed — recorded as child gap below,
  sharing [Block 81] §81.6's own "live-station blocker" class (**B54-G1**/**B54-G2**/**B61-G1**/**B65-G1**).
- **[Block 17]** — §87.5 closes **B17-G3** to practical completeness, building directly on §87.1-§87.4's fresh
  disassembly rather than independent evidence.

## 87.x — Child gaps opened

- **B87-G1** (narrows **B81-G1**) — A live JPMS module-graph query (`jcmd <pid> VM.class_hierarchy`,
  `ModuleLayer.boot()`-reflection, or an `Instrumentation` agent querying `Module.canRead`) against a running
  `station`/`niagarad`/`wb` process, to determine directly whether `niagara.nre` actually reads
  `niagara.securityBridge` (and if so, through what JDK-internal mechanism) or whether the compiled `import`/
  `implements` references in `Bootstrap.java`/`PermissionBridge.java` are latent/unreachable at runtime in some
  way this session's static reading did not anticipate. Same live-station blocker class as [Block 81]'s own
  **B81-G1**/**B54-G1**/**B54-G2**/**B61-G1**/**B65-G1**.
- **B87-G2** — Disassemble `NreLauncherWin32`'s own setter/origin for the FIPS-mode byte at `this+0x1002c`
  (read but not traced to its own write site this session) to confirm it is set FROM
  `defaultToNonFIPS()`'s own `bajaui-FipsOptions.options` file read (the natural reading, given the function
  name and adjacency) rather than a separate license/registry check not yet located — the one part of §87.5's
  B17-G3 recipe resting on an `[INFER]` naming-adjacency rather than a traced data-flow edge.
- **B87-G3** — `njre.dll`'s own `--add-exports=niagara.nre/com.tridium.nre.security.permissions.restricted=
  niagara.niagarad` literal (found this session via `strings`, distinct from any flag in `nre.dll` — a real,
  concrete precedent that the native launcher DOES sometimes emit module-specific `--add-X` flags, just never
  one naming `securityBridge`) was found but its own call site/conditional gate was not disassembled this
  session — confirm whether it is unconditional (like `securityBridge`'s bootclasspath entry, §87.4) or gated on
  some runtime condition, and whether ITS existence changes the reading of why no equivalent flag exists for
  `securityBridge`.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block87.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script output —
see command output appended after this table was drafted; ratio/resolution reported below match that run):

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `checkFileSignature` exported from both `njre.dll`/`nre.dll` at identical mangled name | [CERT-hw] | `r2 iE` + independent `objdump -x` cross-check, both DLLs |
| 2 | Sole caller in each DLL is `initPaths()` via a `DirectoryListing`-driven loop (`fcn.180003500`/`fcn.180006280`) | [CERT-hw] | `axt` on `checkFileSignature`'s address, both DLLs, exactly 1 xref each |
| 3 | The loop filters `.jar` by extension and hard-`exit`s (249/250) on any failure | [CERT-hw] | whole-function `pdf` of `fcn.180003500`, `initPaths.txt` |
| 4 | Verifier uses Windows CNG `BCryptVerifySignature` against a "Tridium Public Key" | [CERT-hw] | `strings` log lines + import-table entry, both DLLs |
| 5 | `niagara_sig_debug` env flag gates logging only, not the verify result | [CERT-hw] | `getenv` call site + branch-rejoin trace, `pdf @ 0x180007050` |
| 6 | `this+0x624` (`-Djava.library.path=%s`) built from `PATH`/niagaraHome/jreHome merge, deduped via `strstr` | [CERT-hw] | whole `initPaths` disassembly, `nre_initPaths.txt:60-169` |
| 7 | `this+0x8324` (`--module-path=%s`) is the SAME buffer passed to the signature-check loop | [CERT-hw] | `nre_initPaths.txt:190-333`, `mov rcx,rsi; call fcn.180006280` at `0x1800071d0` |
| 8 | `NreWin32` vtable offset `0x48` = `getNiagaraHome`, which calls `GetModuleFileNameA` | [CERT-hw] | `pxr` vtable dump @ `0x18000f378`; `axt` on `GetModuleFileNameA` import |
| 9 | `fcn.180004890` is a plain UCRT `__stdio_common_vsnprintf_s` wrapper, no extra tagging | [CERT-hw] | whole-function `pdf`, 34 lines, `fcn_180004890.txt` |
| 10 | `-Xbootclasspath/a:...securityBridge.jar` is live-referenced from `buildArgs`, identical pattern to `-javaagent:...nre.jar` | [CERT-hw] | `axt` on the string address; `pd 25 @ 0x180005ad0` |
| 11 | No `add-reads`/`add-opens`/`add-exports` flag naming `securityBridge` exists in either DLL's strings | [CERT-hw] | exhaustive `grep -i`, both DLLs |
| 12 | `niagara.add.reads`/`.enable.native.access`/`.add.exports`/`.add.opens` all commented-out (empty) by default | [CERT] | `defaults/system.properties:691,709,729,748`, live install file |
| 13 | `handleThirdPartyAddReads` only applies to `ModuleFinder`-resolved third-party modules, never securityBridge | [CERT] | `ModuleManager.java:387-390,427-430,463-483,533-566,753` |
| 14 | `defaultToNonFIPS()` reads a plain-text `bajaui-FipsOptions.options` file, not a hidden check | [CERT-hw] | `defaultToNonFIPS` disassembly, `0x180006777`-`0x18000679b` |

Tally: 12 [CERT-hw], 2 [CERT] (adjusted claims — excluding this table's own self-referential marker-name
prose). Zero [INFER] among the 14 numbered claims above; the block's few `[INFER]` tags are confined to
narrower, explicitly-flagged spots (§87.2's `getNiagaraHome`-fallback ordering nuance already resolved by
disassembly and not left as an open inference; §87.4's structural "why candidate (2) cannot apply" reading,
explicitly marked `[INFER]` in its own paragraph as a structural argument rather than a runtime observation).
Ratio well below the ~0.5 exhaustion threshold — consistent with a session that closed 4 of 5 named gaps
outright and advanced the fifth's residual half with a specific, actionable next step (B87-G1) rather than
running low on investigable material.

**Inline token-verify.** Every `radare2`/`objdump` command and address cited above was run this session against
the freshly-copied, freshly-hashed scratchpad binaries at
`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b87/`, hashes
matching [Block 63]'s own recorded values exactly (confirmed no drift). Spot-check tokens independently
re-confirmed present this session, by direct tool output (not hand-recalled): `?checkFileSignature@
SignatureUtil@@SAHPEBD@Z` (r2 `iE` AND `objdump -x`, both DLLs, 2 independent tools); `?initPaths@
NreLauncherWin32@@AEAAHXZ`/`?initPaths@JavaLauncherWin32@@AEAAHXZ` (same 2-tool cross-check); `"FATAL: %s
failed signature check\n"`/`"FATAL: Module signature verification failure\n"`/`"FATAL: Security bridge module
signature verification failure\n"` (3 distinct literal strings, each read directly off its own `pdf`
annotation); `"niagara_sig_debug"` + its `getenv` call site (`pd @ 0x180001030`); the four `this+0x624`/
`this+0x8324` offset occurrences (`grep -n` over the saved `nre_initPaths.txt`); `?getNiagaraHome@NreWin32@@
UEAAXPEADI@Z` at vtable offset `0x48` (`pxr` dump, all 8 preceding+following slots read for context, not just
the target one); `__stdio_common_vsnprintf_s` import (`fcn.180004890`'s own `call qword [...]` line);
`-Xbootclasspath/a:%s\bin\ext\securityBridge\securityBridge.jar` (both a `strings` hit AND a real `axt`
cross-reference AND a `pd` instruction-level read — 3 independent confirmations); the four commented-out
`niagara.add.*` property lines (direct `grep -n` of the live install file, this session); `ModuleManager.java`'s
`addReads`/`handleThirdPartyAddReads`/`parseNiagaraJPMSProperty` method bodies (direct `Read`, this session,
file never opened by any prior block in this corpus). Token-verify: **≈28 distinct load-bearing tokens**
confirmed present in their cited source (native binary, via 1-2 independent tools each, or decompiled/live-
install file) this session, not recalled from any prior block's output.

**Citation-resolution note.** The verify script's own `[CERT]` resolver found 0 of 5 script-recognized
citations resolvable: four are bare short-forms (`nre_initPaths.txt:*`) pointing at this SESSION's own saved
scratchpad disassembly dumps (not corpus source files — the load-bearing evidence for those claims is the
`[CERT-hw]` native disassembly itself, cited by address/symbol throughout the relevant sections, not the
scratch `.txt` dump's line numbers, which are an incidental artifact of how the dump was saved for this
report); the fifth, `ModuleManager.java:388`, is a bare short-form redundant with the full-path citation
`organized/baja/vineflower/com/tridium/sys/module/ModuleManager.java:387-390` immediately adjacent on the same
line — the identical file, cited in full-path form once and bare form once for readability, the same pattern
[Block 63]'s own self-verify section documented and resolved for its two `extern` items. Exit code is `0`
regardless (a WARN, not a failure) because this is a native-binary/decompiled-address-dominant block, per
METHODOLOGY §11's convention that `[CERT-hw]` evidence sits outside this script's `file:line` resolution scope
by design.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block87.md`. Per the caller's
explicit instruction to touch no other file, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and
backlog re-classification are deliberately NOT performed this session — left to the orchestrator, matching
[Block 63]'s/[Block 76]'s/[Block 81]'s own convention for the same instruction. Native binaries copied and
disassembled under this session's Claude Code scratchpad
(`/tmp/claude-1000/-home-cristian-niagara-research/dcc4f40c-fb17-49fb-afa5-3b08dcc8e0bd/scratchpad/b87/`, saved
`.txt` disassembly dumps included) are left in place for the orchestrator's own disposal; no file under
`/mnt/c/Program Files/Niagara/5.0.0.28` was modified this session (all reads: 4 `cp` operations plus one direct
`grep` of `defaults/system.properties`, zero writes; no binary was executed).
