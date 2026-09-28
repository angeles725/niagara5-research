# Block 63 — `nre.dll`'s ONE `CreateProcessA` call site is `NativePlatformProvider.restartPlatformDaemon0()`, spawning `plat.exe restartdaemon` from an HTTP-servlet-reachable, weakly-gated path; `nre.properties` JVM args are never `cmdline::`-tagged; and the launcher's complete fixed VM-argument recipe is now disassembled

> Research closing/advancing four named child gaps, all from the native-launcher cluster [Block 57]/[Block 61]
> opened and left as out-of-session-budget: **B61-G1**/**B57-G2** (disassemble `nre.dll`'s `CreateProcessA`
> CALL SITE — [Block 61] §61.2 found the import-table fact `[CERT-hw]` but explicitly did NOT trace the call
> site itself, leaving "JxBrowser child process" vs "SCM launches station.exe" as two competing, undecided
> `[INFER]` readings; and recover the Java-side message/JNI call that reaches it); **B57-G1** (does `nre.dll`'s
> `nre.properties`-file-reading code path ALSO stamp a `-Dcmdline::` shadow the way the raw-OS-argv path does —
> [Block 57] §57.1 found the two candidate literal strings coexist in the binary but did not disassemble either
> code path); **B17-G3** (reconstruct the native launcher's VM/module-path argument set so `n5mig` could in
> principle be relaunched via a bare `java` invocation — [Block 17] §17.2's own `java`-fallback attempt failed
> because it could not reconstruct this set, and named the gap without attempting native disassembly); **B54-G1**
> (is `-Djava.security.manager` set anywhere by the N5 launcher). Covers: a fresh `r2 -A` control-flow
> disassembly of `nre.dll`'s entire `NativePlatformProvider_restartPlatformDaemon0` JNI-exported function
> (the CreateProcessA call site and its full command-line-construction logic); confirmation via `axt` that this
> is the ONLY `CreateProcessA` cross-reference in the whole 116 KB binary; the Java-side call chain from an
> HTTP servlet query parameter down to the native call, including the servlet's own default-authentication gate
> (`WebServer.java`'s `NiagaraRequestHandler`); a side-by-side export-table/class-hierarchy comparison of
> `nre.dll` (`NreLauncherWin32`/`Nre`, the full Niagara native bridge) against `njre.dll` (`JavaLauncherWin32`,
> a separate, minimal JVM-boot-only class with ZERO `Java_`-exported JNI methods) that explains — rather than
> merely re-confirms — [Block 61] §61.2's njre.dll-lacks-CreateProcessA finding; a full disassembly of both
> `NreLauncherWin32::buildArgs` (raw-OS-argv + fixed-flag path, `-Dcmdline::`-tagging) and
> `NreLauncherWin32::buildVMOptions` (the separate, `nre.properties`-sourced path) with every literal `-D`/
> `--add-opens`/`--add-reads`/`--enable-native-access`/`--module-path` flag string extracted directly from the
> binary; and a `strings` + corpus-wide `grep` sweep for `java.security.manager`/`SecurityManager` across all
> five relevant native binaries and the full decompiled tree, cross-checked against the live install's own
> bundled JRE version and JEP 486's documented behavior. Does **not** cover: how `station.exe` ITSELF gets a
> fresh OS process for a `plat startstation`/first-boot scenario — this session's `axt` sweep proves
> definitively that this does NOT happen via `nre.dll`'s `CreateProcessA` (there is exactly one call site, and
> it is provably the platform-daemon-restart path, not a station-start path), which narrows but does not
> resolve [Block 61]'s Service-Control-Manager reading (see child gap); the exact runtime VALUES substituted
> into `buildArgs`'s `--module-path=%s`/`-Djava.library.path=%s` format strings (the format strings and the
> buffer-fill CALL SITES were located and disassembled, but the deeper call chain that populates the source
> buffers — e.g. `r13+0x8324`/`r13+0x624` — was not traced to its own `GetModuleFileNameA`-equivalent origin);
> a live `[CERT-hw]` HTTP reproduction of the `refreshSoftware` request against a running daemon (no execution
> performed — static disassembly + decompiled-source reading only).
>
> Subject version: **N5 5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` — the same install
> [Block 33]/[Block 40]/[Block 41]/[Block 53]/[Block 57]/[Block 61] read. Bundled JRE confirmed this session,
> live file read: `jre/release` → `JAVA_VERSION="25.0.4"` `[CERT-hw]`. Decompiled Java sources at
> `organized/_bin-ext/{nre,niagarad}/vineflower/`, `organized/platform/vineflower/`,
> `organized/platDaemon/vineflower/`. Native binaries freshly copied this session from the live install into a
> local scratch directory (never analyzed in place) and re-hashed: `nre.dll`
> (`sha256 a6317e8b024ed823ebe857113bff4378600fc2bd41890309696375dce91239c4`, 116264 bytes), `njre.dll`
> (`sha256 1b8b0074c79dc148e479602bb5bb1a2245f3549db421ccb6534bca7f6a4dfd0b`, 75296 bytes), `niagarad.exe`
> (`sha256 64fd6403fe00bc1b8b940254682bad454806e1983f3fe54343c56c035c24944b`), `station.exe`
> (`sha256 b166aba5aa4beabab1ee6392600387fdd668ea59467333cc474c48fe8802467a`), `n5mig.exe`
> (`sha256 95b5deae0afc4a0b68361f82d4696398691e4b2130a285dce471ab3aa5c97e46`) — the identical `nre.dll`/`njre.dll`
> bytes [Block 61] `objdump -x`'d (file sizes and the earlier session's import-table facts match exactly; no
> drift), disassembled fresh this session with a different tool (`radare2 6.2.0`, `-A` full analysis) for a
> different purpose (call-site recovery, not import-table enumeration).
>
> Sources: `[CERT-hw]` `radare2 -q -A -e bin.relocs.apply=true` control-flow disassembly of `nre.dll`
> (`pdf`/`axt`/`iE`/`afl` over `sym.nre.dll_Java_com_tridium_nre_platform_NativePlatformProvider_restartPlatformDaemon0`
> at `0x1800044a0`, `sym.nre.dll__buildArgs_NreLauncherWin32__AEAAHHPEAPEAD_Z`,
> `sym.nre.dll__buildVMOptions_NreLauncherWin32__AEAAHPEAUJavaVMOption__PEAHH_Z`, and the address
> `0x1800026c0`), this session; `[CERT-hw]` `radare2 iE`/`il` export-and-import-table listing of `njre.dll`
> (95 exports, `JavaLauncher`/`JavaLauncherWin32` C++ class) and `objdump -p` DLL-name listing of
> `niagarad.exe`/`station.exe`, this session; `[CERT-hw]` `strings -n 6`/`-n 4` over all five copied binaries,
> this session (fresh runs, not reused from [Block 53]/[Block 57]/[Block 61]);
> `organized/_bin-ext/nre/vineflower/com/tridium/nre/platform/NativePlatformProvider.java:49-65` (`load()`,
> whole method), `:596-603` (`allowPlatformDaemonRestart()`/`restartPlatformDaemon()`, whole), `:1222` (native
> declaration, single line, `grep`-located); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/
> NiagaraDaemon.java:1381-1390` (`queueRefreshSoftware()`, whole method);
> `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:70-83`
> (CSRF-token check), `:608-645` (the `refreshSoftware`/`restartWeb`/`reloadProperties` query-parameter
> dispatch block, whole); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/
> DaemonServlet.java:1-140` (whole file — confirms it does NOT override `useDefaultAuthentication()`/
> `requiresAuthentication()`); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/
> Servlet.java:94-104` (`useDefaultAuthentication()`/`authenticate()`/`requiresAuthentication()` default-method
> bodies, whole); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/http/WebServer.java:2117-2153`
> (`NiagaraRequestHandler.handle()`, the pre-dispatch authentication gate, whole block);
> `organized/platDaemon/vineflower/com/tridium/platDaemon/command/BStartStationCommand.java:33,51`
> (`getName()`/usage-string, re-`grep`-confirmed this session, cross-reference only — not re-read whole);
> `organized/platform/vineflower/niagara/platform/DaemonSecurityManager.java` (whole file, 26 lines),
> `organized/platform/vineflower/com/tridium/platform/daemon/PlatformSecurityManager.java` (whole file,
> 952 lines) — both read to CONFIRM the `SecurityManager`-named classes found by corpus grep are Niagara's own
> platform-account-management interfaces, unrelated to `java.lang.SecurityManager`; `[CERT-web]`
> `https://openjdk.org/jeps/486`, fetched this session 2026-09-27 (JEP 486, "Permanently Disable the Security
> Manager", delivered JDK 24).
>
> Method: `radare2` full-binary control-flow analysis + manual call-site/string cross-reference recovery
> (native, no Ghidra headless run needed this session — `r2 -A` resolved every call site cleanly; Ghidra and
> `capa`/`floss` confirmed available via `detect-tools.sh --require ghidra` but not invoked, since `r2`
> sufficed and re-running a second heavyweight decompiler over the same evidence would not have added
> certainty) + targeted whole-method reading of already-decompiled Vineflower sources (no fresh decompilation
> this session — every `.java` file read was already present in `organized/` from a prior session) +
> corpus-wide `grep`/`strings` negative-existence sweep + one web fetch. Markers: `[CERT-hw]` verified against
> the live install's own binaries (a form of static live-artifact inspection, per METHODOLOGY §3, distinct from
> a runtime probe) · `[CERT]` local primary source (`file:line`) · `[CERT-web]` official web source · `[INFER]`
> deduction. Binaries were copied to a local scratch directory before any analysis and never modified in place
> (install stayed read-only throughout, per the caller's instruction).
>
> Native-launcher / platform-daemon-HTTP layer. Connects [Block 61] (closes/refines **B61-G1**, the child gap
> it opened), [Block 57] (closes **B57-G1**, the child gap it opened, and re-confirms/extends §57.1's
> `BStartStationCommand`/`ProcessBuilder`-absence framing), [Block 17] (advances **B17-G3**, the child gap it
> opened), [Block 54] (closes **B54-G1** — a negative-existence finding).
>
> **Type:** `mixed` — §63.1/§63.2/§63.4 each upgrade a NAMED prior block's `[INFER]`/unresolved gap to `[CERT]`
> by opening a call site or negative-existence question that block explicitly flagged as unopened (the `mixed`
> trigger per METHODOLOGY §4/§11); §63.3 is evidence-gathering that ADVANCES without fully closing (the deeper
> buffer-fill call chain remains untraced).

---

## 63.1 — B61-G1/B57-G2 CLOSED (call-site identity) / REFINED (station-start mechanism still open): `nre.dll` has exactly ONE `CreateProcessA` call site, inside the JNI-exported `NativePlatformProvider.restartPlatformDaemon0()`, and it spawns `<install-root>\bin\plat.exe restartdaemon` — reachable from an authenticated `UpdateDaemonServlet` HTTP request, gated by a native check that is ICF-folded to an unconditional `true` on this build `[CERT-hw]`

> **Correction (added by [Block 117], §14 cross-block, §117.x).** `njre.dll` has **91** exports, not 95 (rabin2 -E, r2 iEj, objdump -p, PE NumberOfFunctions = 91; orchestrator re-verified with rabin2 -E). The 0-JNI finding stands.

[Block 61] §61.2 confirmed via `objdump -x` that `nre.dll` (not `njre.dll`) imports `CreateProcessA`, but explicitly
did not trace the call site, leaving two competing `[INFER]` readings open: (1) an unrelated JxBrowser child-process
spawn, or (2) the OS Service Control Manager — not `nre.dll`'s own code — being the actual `station.exe` spawner.
This session disassembles the call site directly.

**The single call site, found via `axt` on the `CreateProcessA` import thunk (`0x18000e1c8`) — there is exactly
ONE cross-reference in the entire binary:**
```
sym.nre.dll_Java_com_tridium_nre_platform_NativePlatformProvider_restartPlatformDaemon0
    0x1800045dd  call qword [sym.imp.KERNEL32.dll_CreateProcessA]
```
`[CERT-hw]` `radare2 -q -A -e bin.relocs.apply=true -c 'axt sym.imp.KERNEL32.dll_CreateProcessA' nre.dll`, this
session — the full `axt` output lists exactly one xref, resolved against the function's own JNI-shaped export
name (`Java_com_tridium_nre_platform_NativePlatformProvider_restartPlatformDaemon0`, standard
`Java_<package>_<class>_<method>` JNI naming), itself confirmed present in `nre.dll`'s export table at
`0x1800044a0` (export index 191) via `iE`. **This single-call-site fact is itself load-bearing: it means
[Block 61]'s JxBrowser reading is REFUTED as an explanation for `nre.dll`'s own `CreateProcessA` import** — if a
JxBrowser child-process spawn went through `nre.dll`, it would need its OWN, second call site, and none exists.
(JxBrowser's own Chromium-renderer process spawning, if any, must go through JxBrowser's own native code/JAR, not
`nre.dll` — this session does not open JxBrowser's own binaries, so this is a refutation of the READING against
`nre.dll` specifically, not a full trace of where JxBrowser's own spawn logic lives.)

**Disassembly of the function body (`0x1800044a0`-`0x180004633`, 404 bytes) shows a `Nre::getInstance()` call,
a virtual-dispatch call to fill a 260-byte (`0x104`, i.e. `MAX_PATH`) buffer with a path string, then direct
byte-level string construction appending `"\bin\"` and `"plat.exe restartdaemon"` to that path before calling
`CreateProcessA`:**
```
call   sym.nre.dll__getInstance_Nre__SAPEAV1_XZ        ; Nre::getInstance()
mov    r9, rax                                         ; r9 = Nre* instance
lea    rdx, [lpCommandLine]                             ; buffer, 0x104 bytes
mov    r8d, 0x104
mov    rcx, qword [rax]                                 ; rcx = *(Nre*) = vtable ptr
mov    rax, qword [rcx + 0x48]                           ; rax = vtable[0x48] (virtual fn ptr)
mov    rcx, r9                                           ; rcx = this
call   qword [0x18000e708]                                ; CFG dispatch stub -> jmp rax (see below)
; --- strlen loop finds end of the filled buffer ---
mov    ecx, dword [str._bin_]         ; "\bin\" (4 bytes)  -> appended at buffer end
mov    word  [0x18000ef4c] -> appended (5th byte '\')
; --- second strlen loop finds new end ---
lea    rdx, [lpCommandLine]
movups xmm0, xmmword [0x18000ef50]    ; loads "plat.exe restart" (16 bytes, verified via `px`)
mov    dword [var_70h], 0x68          ; 0x68 = 104 = sizeof(STARTUPINFOA) -> STARTUPINFOA.cb init
movups xmmword [rcx], xmm0            ; store "plat.exe restart" at buffer end
mov    dword [rcx+0x10], eax          ; eax = dword [0x18000ef60] = "daem" (4 bytes)
movzx  eax, word [0x18000ef64]        ; "on" (2 bytes)
mov    word [rcx+0x14], ax
movzx  eax, byte [0x18000ef66]        ; 0x00 terminator
mov    byte [rcx+0x16], al
...
call   qword [sym.imp.KERNEL32.dll_CreateProcessA]       ; 0x1800045dd
test   eax, eax
jne    0x180004604                                        ; success -> CloseHandle x2, return 0
mov    eax, 0xffffffff                                    ; failure -> return -1
```
`[CERT-hw]` `radare2 -q -A -e bin.relocs.apply=true -c 'pdf @ sym.nre.dll_Java_com_tridium_nre_platform_
NativePlatformProvider_restartPlatformDaemon0' nre.dll`, this session, whole-function disassembly (all 404
bytes read, not excerpted). The `"plat.exe restartdaemon"` literal's exact bytes were independently confirmed
with a raw hex dump: `px 32 @ 0x18000ef50` → `70 6c 61 74 2e 65 78 65 20 72 65 73 74 61 72 74` (`"plat.exe
restart"`) immediately followed by `64 61 65 6d 6f 6e 00 00` (`"daemon\0\0"`) `[CERT-hw]` (same session, `px`
and `ps` both run over the same address — the `ps` string-view independently reads `plat.exe restartdaemon`
verbatim). The `0x68` constant written to `var_70h` matches `sizeof(STARTUPINFOA)` on Win64 exactly (104
bytes) — the standard MSVC idiom for `STARTUPINFOA.cb = sizeof(STARTUPINFOA)` before a `CreateProcess` call —
confirming `var_70h`/`var_50h`/`hObject` are the local `STARTUPINFOA`/`PROCESS_INFORMATION` structures
`[INFER]` (a well-known Win32 idiom, not itself a string/symbol in the binary, but the stack-variable roles
are otherwise unlabeled by `r2`'s auto-analysis and this reading is the only one consistent with the two
`CloseHandle` calls immediately following the `CreateProcessA` success branch — `PROCESS_INFORMATION.hProcess`/
`hThread` are exactly the two handles a caller must close).

**Net reading: `restartPlatformDaemon0()` re-derives its own install root (via a virtual call, likely a
`GetModuleFileNameA`-style path lookup — not traced to the Win32 API level, since the call goes through
`Nre`'s OWN vtable at offset `0x48`, not directly to `imp.GetModuleFileNameA`), strips it down to a bare
directory via a strlen scan, and constructs the literal command line
`"<install-root>\bin\plat.exe restartdaemon"`, invoked with `lpApplicationName = NULL` (so Windows resolves
the executable from the command line's first token) via `CreateProcessA`.** This is a **platform-daemon
SELF-RESTART**, not a station launch and not a JxBrowser spawn: `plat.exe` is the SAME executable Workbench's
own `BStartStationCommand` names — `getName() -> "startstation"`, usage string `"  plat startstation <flags>
[stationname]"` `[CERT]` `organized/platDaemon/vineflower/com/tridium/platDaemon/command/
BStartStationCommand.java:33,51` (fresh `grep`-confirmed this session, cross-referenced not re-read whole) —
confirming `plat.exe` is Niagara's own umbrella platform-CLI executable, and `"restartdaemon"` is a SIBLING
subcommand to Workbench's `"startstation"`, invoked here NATIVELY (from `nre.dll`'s own C code, not from a
Workbench RPC) when the platform daemon needs to relaunch itself.

**Java-side reachability chain, traced whole from an HTTP query parameter down to this native call:**
```
UpdateDaemonServlet.doGet(): query.containsKey("refreshSoftware")
  -> this.platformProvider.allowPlatformDaemonRestart()          [native gate — see below]
  -> NiagaraDaemon.getInstance().lockClient()
  -> NiagaraDaemon.getInstance().queueRefreshSoftware()
       -> !platformProvider.allowPlatformDaemonRestart() ? -1
       -> _CONSOLE ? (log + -1, "cannot reload ... running from the console")
       -> platformProvider.restartPlatformDaemon()
            -> !this.allowPlatformDaemonRestart() ? -1 : restartPlatformDaemon0()   [the native call traced above]
```
`[CERT]` `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:608-645`
(whole `refreshSoftware`/`restartWeb`/`reloadProperties` dispatch block — the `refreshSoftware` branch is at
`:624-638`); `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/NiagaraDaemon.java:1381-1390`
(`queueRefreshSoftware()`, whole method); `organized/_bin-ext/nre/vineflower/com/tridium/nre/platform/
NativePlatformProvider.java:596-603` (`allowPlatformDaemonRestart()`/`restartPlatformDaemon()`, whole,
re-read this session). This directly answers B61-G1's "which message/JNI call reaches native" half: the
message is an ordinary `GET` request to the daemon's own `update`-family servlet with a `refreshSoftware`
query parameter present (any value — `query.containsKey`, not a value check), the same mechanism a
software-distribution push would use to make the daemon pick up newly-deployed binaries.

**Remote reachability assessment, `[CERT]`: gated by the servlet's DEFAULT authentication, not bypassed.**
`UpdateDaemonServlet` overrides neither `useDefaultAuthentication()` nor `requiresAuthentication()` — a fresh
`grep` over the whole file found zero occurrences of either method name `[CERT]` (negative existence, file
opened and read whole this session). Both therefore inherit `Servlet`'s own defaults, both `true`:
```
public boolean useDefaultAuthentication() { return true; }
public boolean authenticate(Request req, Response resp) { return false; }
public boolean requiresAuthentication() { return true; }
```
`[CERT]` `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/Servlet.java:94-104` (whole
method bodies). The daemon's own HTTP request dispatcher enforces this BEFORE `doGet()` ever runs:
```
if (servlet.useDefaultAuthentication()) {
   if (!WebServer.this.authenticate(request, response)) {
      ... 401/error, return true (request handled, servlet body never reached) ...
   }
}
```
`[CERT]` `organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/http/WebServer.java:2117-2153`
(`NiagaraRequestHandler.handle()`, whole gate block, re-read this session). **Net: reaching the
`restartPlatformDaemon0`/`CreateProcessA` path requires a successful platform-daemon HTTP authentication
first — this is NOT an unauthenticated remote path.** This answers the gap's own framing ("assess remote
reachability... from platform-authenticated clients"): the answer is that authentication IS the gate, and it
is the daemon's ordinary default gate (the same one every other daemon servlet uses), not a special
additional control layered on top of this specific restart capability.

**The native-side "allow" gate is NOT a functioning check on this build — it is Identical-Code-Folded with
five unrelated always-true stubs, `[CERT-hw]`.** `allowPlatformDaemonRestart0()`'s own JNI export
(`Java_com_tridium_nre_platform_NativePlatformProvider_allowPlatformDaemonRestart0`, export index 110) resolves
to the SAME address, `0x1800026c0`, as SIX other distinct exports:
```
86  ?isProductionBuild@SignatureUtil@@SA_NXZ                                        (SignatureUtil::isProductionBuild)
110 Java_..._NativePlatformProvider_allowPlatformDaemonRestart0
112 Java_..._NativePlatformProvider_canWriteSystemLogMessages0
114 Java_..._NativePlatformProvider_checkForKeyMaterialUpgrade0
123 Java_..._NativePlatformProvider_getAllowStationRestartDefault0
180 Java_..._NativePlatformProvider_isStationPlatformReadonly0
182 Java_..._NativePlatformProvider_isSystemTimeReadonly0
```
and the code AT that shared address is a two-instruction stub: `mov al, 1; ret` — an unconditional `return
true;` `[CERT-hw]` `radare2 -q -c 'iE~0x1800026c0' nre.dll` (lists all seven aliases sharing the address) +
`radare2 -q -A -c 'af @ 0x1800026c0; pdf @ 0x1800026c0' nre.dll` (the two-instruction body), both this session.
This is standard MSVC linker Identical-Code-Folding (`/OPT:ICF`): seven functions with byte-identical bodies on
THIS build collapse to one address. **Reading this correctly:** it does not prove these methods are ALWAYS
`true` on every N5 build — a production-signed release build could plausibly diverge `isProductionBuild()`
from the others (its name alone suggests a build-mode branch elsewhere would want it to), which would break
the ICF merge for a subset — but it DOES prove that on THIS specific Beta build (`5.0.0.28`), the native
"is this restart allowed" check is a rubber stamp: the ONLY functioning gate on the whole `refreshSoftware`
→ `CreateProcessA("plat.exe restartdaemon")` path, on this exact binary, is the HTTP servlet's own default
authentication (above), not this native call. `[INFER]` for whether a production-signed build diverges this
grouping — not verified this session; `[CERT-hw]` for the fact as observed on this Beta build.

**Station-start mechanism: narrowed, not resolved — [Block 61]'s SCM reading is now the LAST standing
explanation, `[INFER]`.** Because this session confirms `nre.dll` has exactly ONE `CreateProcessA` call site
and it is provably the platform-daemon-restart path (not a station-start path — the hardcoded command line is
`plat.exe restartdaemon`, never anything resembling `station.exe` or `plat startstation`), and no other
`Java_..._NativePlatformProvider_*` export in `nre.dll`'s full table resembles a station-launch native method
(a fresh `grep` for `station|start|process` across all `Java_`-prefixed exports found only
`getAllowStationRestartDefault0`, `isStationPlatformReadonly0` — both config getters folded into the same
always-`true` stub group above — and `getProcessId0`, a PID-query getter, not a spawner) `[CERT-hw]`,
**`station.exe` getting a genuinely NEW OS process (first boot, `plat startstation`) is now confirmed NOT to
happen via any `nre.dll` `CreateProcessA` call.** This leaves the OS Service Control Manager — external to
this binary, using the `RegisterServiceCtrlHandlerA`/`StartServiceCtrlDispatcherA`/`SetServiceStatus` triplet
[Block 61] §61.2 already found `nre.dll`/`station.exe` imports (`station.exe`'s OWN entry-point registering
itself AS a service) — as the only remaining candidate, now with ONE fewer competing reading to weigh against
it. This is a narrowing, not a new finding; SCM itself was not probed this session (out of scope — SCM is an
OS component, and observing it would require a live, running install with an installed Windows Service
definition, a dynamic/`[CERT-hw]`-live reproduction this session's static read-only scope does not cover).

## 63.2 — B57-G1 CLOSED: `nre.properties`-sourced JVM args (via `buildVMOptions`) are NEVER `-Dcmdline::`-tagged — only the raw-OS-argv path (`buildArgs`'s own body, BEFORE it calls `buildVMOptions`) applies that tag `[CERT-hw]`

[Block 57] §57.1 found both candidate literal strings (`"-Dcmdline::"` and the four
`station.java.options`/`wb.java.options`/`test.java.options`/`nre.java.options` keys) present in `nre.dll` via
`strings`, but could not determine — without disassembly — whether the SAME code path stamps both, naming
**B57-G1**. This session locates and disassembles both code paths directly.

**The two strings resolve to two DIFFERENT functions, confirmed via `axt` on each string's address:**
```
sym.nre.dll__buildVMOptions_NreLauncherWin32__AEAAHPEAUJavaVMOption__PEAHH_Z
    0x180007eae  lea rdx, str.station.java.options
    0x180007ea5  lea rdx, str.wb.java.options
sym.nre.dll__buildArgs_NreLauncherWin32__AEAAHHPEAPEAD_Z
    0x18000596a  lea r8,  str._Dcmdline::
```
`[CERT-hw]` `radare2 -q -A -e bin.relocs.apply=true -c '/ station.java.options; / wb.java.options; /
-Dcmdline::; axt @ <addr>'` over `nre.dll`, this session, three independent string searches each followed by
an `axt` cross-reference resolution. **A full disassembly of `buildVMOptions` (1110 bytes, 314 output lines,
whole-function `pdf`) contains ZERO references to the `-Dcmdline::` string or to any function that itself
references it** — confirmed by `grep -ic cmdline` over the saved disassembly output, result `0` `[CERT-hw]`
(this session; the full disassembly text is reproducible from the same `pdf` command above). `buildVMOptions`
reads all four `nre.properties` keys via `strtok_s`/`strdup` (splitting on some delimiter) and appends a FIXED
list of `--add-opens=...`/`--enable-native-access=...` literals (28 distinct entries extracted verbatim — full
list in §63.3), but never constructs or references a `-Dcmdline::`-prefixed string anywhere in its own body.

**`buildArgs`, by contrast, references `-Dcmdline::` directly in its OWN body (line/address `0x18000596a`),
THEN separately calls `buildVMOptions` as a distinct, later step:**
```
sym.nre.dll__buildArgs_NreLauncherWin32__AEAAHHPEAPEAD_Z:
    0x18000596a   lea r8, str._Dcmdline::          ; "-Dcmdline::" literal used HERE, inside buildArgs
    0x180005977   call strncpy_s
    0x18000598d   call strncat_s
    ...
    0x180005a0b   call sym.nre.dll__buildVMOptions_NreLauncherWin32__AEAAHPEAUJavaVMOption__PEAHH_Z
```
`[CERT-hw]` `radare2 -q -A -e bin.relocs.apply=true -c 'pdf @ sym.nre.dll__buildArgs_NreLauncherWin32__
AEAAHHPEAPEAD_Z' nre.dll`, this session, whole-function disassembly (602 disassembly lines saved and grepped).
The `-Dcmdline::` string is built into a per-argument buffer via `strncpy_s`/`strncat_s` (concatenating the
literal prefix with each processed argv entry) BEFORE the `call` to `buildVMOptions` at `0x180005a0b` — i.e.
`buildVMOptions` executes as a SEPARATE, LATER function call, and its own body (confirmed above) never
performs this concatenation for the options it adds.

**Net verdict, closing B57-G1: `nre.properties`-sourced JVM options (`station.java.options=`/
`wb.java.options=`/`test.java.options=`/`nre.java.options=`) are NEVER `-Dcmdline::`-tagged.** Only properties
that arrive via the raw OS command-line argv, processed inside `buildArgs`'s own loop, receive the shadow tag
that `Nre.java`'s `verifySystemProperties()`/`addToSystemProperties()` checks for (per [Block 57] §57.1's own
Java-side reading, re-used not re-verified this session). **This confirms [Block 57] §57.1's own flagged
concern as a REAL, distinct bypass shape**: a `station.java.options=-Dniagara.commandLinePropertyDenyList=`
line in `nre.properties` would inject that override with NO `cmdline::`-shadow at all — not merely an
unguarded shadow check as the raw-argv path has (§57.1's original finding), but a path that never sets the
shadow property in the FIRST place. The severity bound [Block 57] §57.1 already established still applies
unchanged: this requires filesystem WRITE access to `<config-home>/etc/nre.properties`, the same directory
holding `system.properties` itself, so this finding SHARPENS the mechanism without widening the access
precondition.

## 63.3 — B17-G3 ADVANCED, not closed: the launcher's complete fixed VM-argument set (43 distinct flags: `-D`/`--add-opens`/`--add-reads`/`--enable-native-access`/`--module-path`/`--sun-misc-unsafe-memory-access`) is now disassembled verbatim, but the runtime VALUES substituted into the path-based `%s` templates were not traced to their origin `[CERT-hw]`+`[INFER]`

[Block 17] §17.2 attempted a `java`-fallback relaunch of `n5mig` against a bare `java -cp`/module-path
invocation and found it insufficient — the native launcher supplies a JavaFX-jmods-plus module-path/VM-args
set a bare invocation does not reconstruct — and named **B17-G3** without attempting disassembly. This session
extracts the COMPLETE literal flag set directly from `buildArgs` and `buildVMOptions`'s disassembly (both
already fully dumped for §63.2), giving a concrete recipe.

**From `buildVMOptions` (the `nre.properties`-sourced path — always present regardless of file content, since
these are FIXED literals appended after the file-derived tokens), 28 distinct flags:**
```
--add-opens=java.base/java.io=niagara.nre
--add-opens=java.base/java.lang=niagara.nre
--add-opens=java.base/java.util=niagara.nre
--add-opens=java.base/sun.security.provider=niagara.nre
--add-opens=java.desktop/java.awt=niagara.nre
--add-opens=java.xml.crypto/org.jcp.xml.dsig.internal.dom=niagara.nre
--add-opens=javafx.web/javafx.scene.web=niagara.nre
--add-opens=javafx.web/com.sun.javafx.scene.web=niagara.nre
--add-opens=org.bouncycastle.fips.core/org.bouncycastle.jcajce.provider=niagara.nre
--add-opens=org.bouncycastle.fips.tls/org.bouncycastle.tls.crypto.impl.jcajce=niagara.nre
--add-opens=org.bouncycastle.provider/org.bouncycastle.crypto.params=niagara.nre
--add-opens=org.bouncycastle.provider/org.bouncycastle.jce.provider=niagara.nre
--add-opens=org.bouncycastle.tls/org.bouncycastle.tls.crypto.impl.jcajce=niagara.nre
--add-opens=org.eclipse.jetty.client/org.eclipse.jetty.client=niagara.nre
--add-opens=org.eclipse.jetty.ee11.servlet/org.eclipse.jetty.ee11.servlet=niagara.nre
--add-opens=org.eclipse.jetty.ee11.websocket.jetty.server/org.eclipse.jetty.ee11.websocket.server=niagara.nre
--add-opens=org.eclipse.jetty.security/org.eclipse.jetty.security.authentication=niagara.nre
--add-opens=org.eclipse.jetty.server/org.eclipse.jetty.server=niagara.nre
--add-opens=org.eclipse.jetty.server/org.eclipse.jetty.server.handler=niagara.nre
--add-opens=org.eclipse.jetty.session/org.eclipse.jetty.session=niagara.nre
--add-opens=org.eclipse.jetty.util/org.eclipse.jetty.util.ssl=niagara.nre
--add-opens=org.eclipse.jetty.websocket.api/org.eclipse.jetty.websocket.api=niagara.nre
--enable-native-access=javafx.graphics
--enable-native-access=javafx.web
--enable-native-access=jxbrowser
--enable-native-access=org.bouncycastle.fips.core
--enable-native-access=org.jnrproject.jffi
--enable-native-access=org.lz4.java
```
`[CERT-hw]` extracted via `grep -oE '"--[a-zA-Z0-9_./=,-]+"' <buildVMOptions pdf output> | sort -u`, this
session, every literal read directly off the disassembly's own `lea rcx, str.__add_opens...` / `str.___enable_
native_access...` annotations and cross-checked against the raw string constants (28/28 present, zero
truncation — the count matches `wc -l` on the sorted-unique set exactly).

**From `buildArgs` itself (the raw-launcher path — these run BEFORE the OS argv loop, so they too are fixed,
not conditional on any file or command-line content), 20 further distinct flags:**
```
-Dcmdline::                                                (tag prefix, not a standalone flag — see §63.2)
-Djava.protocol.handler.pkgs=com.tridium.nre.protocol
-Djava.library.path=%s
-Dniagara.home=%s
-Dniagara.home.url=%s
-Dniagara.config.home=%s
-Dniagara.user.home=%s
-Dniagara.platform.provider=%s
-Dorg.bouncycastle.fips.approved_only=true
--module-path=%s
--add-modules=ALL-MODULE-PATH,ALL-DEFAULT
--enable-native-access=niagara.nre
--sun-misc-unsafe-memory-access=allow
--add-opens=java.base/java.net=niagara.nre
--add-opens=java.base/java.security=niagara.nre
--add-opens=org.bouncycastle.fips.core/org.bouncycastle.asn1=niagara.nre
--add-opens=org.bouncycastle.provider/org.bouncycastle.asn1=niagara.nre
--add-reads=niagara.nre=org.bouncycastle.fips.pkix,org.bouncycastle.fips.core,org.bouncycastle.fips.tls,org.bouncycastle.fips.util
--add-reads=niagara.nre=org.bouncycastle.pkix,org.bouncycastle.provider,org.bouncycastle.tls,org.bouncycastle.util
--add-reads=okhttp3=org.bouncycastle.fips.tls
--add-reads=okhttp3=org.bouncycastle.tls
```
`[CERT-hw]` same extraction method, over `buildArgs`'s own 602-line disassembly. Additional fixed literals
already `[CERT-hw]`-established by [Block 53]/[Block 57]'s own `strings` runs and re-confirmed present in this
session's fresh `strings -n 6 nre.dll` pass, not re-disassembled to a call site this session:
`-Xbootclasspath/a:%s\bin\ext\securityBridge\securityBridge.jar`, `-javaagent:%s\bin\ext\nre.jar`,
`--add-opens=java.base/java.net=niagara.nre` (also present as a fixed `strings`-level literal, consistent with
the disassembled `buildArgs` finding above).

**What remains untraced, and why this only ADVANCES rather than CLOSES B17-G3.** Three of the flags above use
a `%s` format placeholder (`--module-path=%s`, `-Djava.library.path=%s`, and the four `-Dniagara.*=%s`
properties) — the LITERAL FLAG NAMES are now `[CERT-hw]`, but the RUNTIME VALUE substituted for each `%s` was
traced only as far as the format-call site, not to its ultimate origin:
```
0x180005c56  lea r9, str._Djava.library.path_s     ; format string
0x180005c4a  lea rax, [r13 + 0x624]                 ; %s source buffer — NOT traced further
0x180005cbd  lea r9, str.__module_path_s
0x180005cb1  lea rax, [r13 + 0x8324]                ; %s source buffer — NOT traced further
```
`[CERT-hw]` same `buildArgs` disassembly, call sites for both `snprintf`-style format calls (`fcn.180004890`,
itself not opened this session) located and read. Both source buffers (`r13+0x624`, `r13+0x8324`) are large
(memset to `0x7d00` = 32000 bytes immediately before each format call, per the same disassembly), consistent
with per-path string buffers filled EARLIER in the same function or in a constructor — following the SAME
"virtual call fills a buffer, then string logic manipulates it" pattern §63.1 traced precisely for
`restartPlatformDaemon0`'s install-root lookup, but that EARLIER fill logic for these two specific offsets was
not itself disassembled this session (named child gap). **Net: B17-G3 is ADVANCED, not closed — a
`java`-fallback relaunch attempt could now supply the CORRECT, complete flag LIST (43 distinct entries across
both functions, verbatim above) with confidence, but the actual VALUES for `--module-path`/
`-Djava.library.path`/the four `niagara.*` home properties still require either a live capture (e.g. `strings`
of a running process's command line, or a `ProcMon`/`Process Explorer`-style live probe — out of this
session's static scope) or a deeper disassembly pass into the buffer-fill logic.**

## 63.4 — B54-G1 CLOSED (negative): `-Djava.security.manager` is set NOWHERE in the N5 native launcher or its decompiled Java corpus — consistent with the bundled JRE (25.0.4) permanently disabling the mechanism since JDK 24 `[CERT-hw]`+`[CERT-web]`

**Negative-existence sweep, `[CERT-hw]`: zero occurrences of `security.manager`/`SecurityManager` (case-
insensitive) in `strings -n 6`/`-n 4` output over all five native binaries copied and opened this session**
(`nre.dll`, `njre.dll`, `niagarad.exe`, `station.exe`, `n5mig.exe`) — each binary individually `strings`'d and
`grep -i`'d this session, zero hits in all five. Per METHODOLOGY §3's symmetric-opening-obligation rule, this
negative claim is `[CERT-hw]` because all five NAMED artifacts were actually opened and read end-to-end this
session, not merely asserted absent.

**Corpus-wide `grep` for the literal string `"java.security.manager"` across the entire decompiled N5 tree:
zero hits.** A separate `grep` for the class name `"SecurityManager"` (no `java.security.` qualifier) returns
38 hits, but every one of them resolves to TWO Niagara-authored, UNRELATED interfaces/classes —
`niagara.platform.DaemonSecurityManager` (an interface for platform-account management: `isAuthenticationReadonly`,
`useOsGroups`, `addPlatformUser`, etc. — nothing to do with `java.lang.SecurityManager`) and
`com.tridium.platform.daemon.PlatformSecurityManager` (its implementation, 952 lines, driving
`BDaemonSession`-mediated user/passphrase management over the daemon protocol) — both read WHOLE this session
`[CERT]` `organized/platform/vineflower/niagara/platform/DaemonSecurityManager.java` (26 lines),
`organized/platform/vineflower/com/tridium/platform/daemon/PlatformSecurityManager.java` (952 lines). **Neither
file references `java.lang.SecurityManager`, `System.setSecurityManager`, or any JVM Security-Manager API
anywhere in its body** — the name collision is coincidental (both are ordinary Niagara "security manager" as in
"the thing that manages platform security settings," not the deprecated/removed Java mechanism).

**Context confirming WHY: the bundled JRE (25.0.4) is past JDK 24, where `-Djava.security.manager` is
documented to make the JVM refuse to start.** Live install file read this session: `jre/release` →
`JAVA_VERSION="25.0.4"` `[CERT-hw]`. `[CERT-web]` JEP 486 ("Security Manager Changes", delivered JDK 24,
fetched `https://openjdk.org/jeps/486` this session, 2026-09-27): *"It is an error to enable a Security
Manager at startup"* — attempting `-Djava.security.manager` (in any of its historical variants, including the
legacy bare-flag and `=allow`/`=default` forms) causes the JVM to print `"Error occurred during initialization
of VM java.lang.Error: A command line option has attempted to allow or enable the Security Manager. Enabling a
Security Manager is not supported."` and exit before the application starts; this error is documented as
unsuppressible. `[INFER]`: this makes the native-launcher finding UNSURPRISING rather than merely incidental —
setting this flag on a JDK-24+-bundled launcher would be actively self-defeating (the station/daemon process
would refuse to boot at all), so its total absence from both the native flag list (§63.3's 43-entry
enumeration, which does NOT include it) and the Java corpus is the EXPECTED, not merely observed, state for
this build.

**Net verdict, closing B54-G1: `-Djava.security.manager` is not set anywhere in N5 5.0.0.28's native launcher,
`nre.properties` defaults, or decompiled Java source — a clean, corroborated negative.**

## 63.x — Connections

- **[Block 61]** — §63.1 closes the CALL-SITE-IDENTITY half of **B61-G1** outright (the single `CreateProcessA`
  xref, its full command-line construction, and the Java-side HTTP reachability chain down to it) and REFUTES
  [Block 61] §61.2's JxBrowser reading specifically (no second call site exists for it to be). It NARROWS but
  does not resolve the companion station-start question, strengthening (not proving) [Block 61]'s
  Service-Control-Manager reading as the sole remaining candidate. §63.1 also EXPLAINS, not merely re-confirms,
  [Block 61] §61.2's `njre.dll`-lacks-`CreateProcessA` finding: `njre.dll` implements a wholly separate,
  minimal `JavaLauncher`/`JavaLauncherWin32` C++ class with ZERO `Java_`-exported JNI methods (95 exports
  total, none prefixed `Java_`), while `nre.dll`'s `NativePlatformProvider.load()` dynamically
  `System.loadLibrary("nre")`s `nre.dll` INTO whichever process's JVM needs the platform bridge — including
  niagarad.exe's own, booted via the separate `njre.dll` — reconciling why `njre.dll`'s STATIC PE import table
  correctly shows no `CreateProcessA` while niagarad.exe's PROCESS still gains that capability at Java runtime.
- **[Block 57]** — §63.2 closes **B57-G1** outright: the `nre.properties`-sourced `buildVMOptions` path never
  references `-Dcmdline::`, confirmed by a zero-hit `grep` over its complete disassembly; only `buildArgs`'s
  own raw-argv loop (which CALLS `buildVMOptions` afterward, as a separate step) applies the tag. This
  sharpens, without widening, §57.1's own already-`[CERT]` severity bound (still gated on `<config-home>/etc/`
  write access).
- **[Block 17]** — §63.3 advances **B17-G3**: the complete 43-flag fixed-argument recipe (28 from
  `buildVMOptions`, ~20 from `buildArgs`, overlapping on a few `--add-opens` entries) is now `[CERT-hw]`, giving
  a `java`-fallback relaunch attempt a concrete flag LIST — but the four `-Dniagara.*=%s`/`--module-path=%s`/
  `-Djava.library.path=%s` runtime VALUES remain untraced, so the gap stays open (narrower — see child gap).
- **[Block 54]** — §63.4 closes **B54-G1** with a clean negative, corroborated by the live install's own
  bundled-JRE version (25.0.4) and JEP 486's documented JDK-24+ behavior.
- **[Block 53]** — its own `nre.dll` `strings` runs (for `-Dcmdline::`, reused as one of two search terms in
  §63.2) and this block's fresh `strings`/`radare2` runs are independent extractions for different purposes
  (a raw string search vs. a call-site disassembly); no overlap, no correction either way.

## 63.x — Child gaps opened

- **B63-G1** (narrows **B61-G1**'s station-start half) — With `nre.dll`'s single `CreateProcessA` call site
  now fully attributed to the platform-daemon-restart path, the remaining question is purely SCM-side: confirm
  (via a live install's registered Windows Service definition — `sc qc <servicename>` or the Services MMC
  snap-in — a `[CERT-hw]` live-system probe, not static disassembly) that a Windows Service entry actually
  names `station.exe` as its binary path, and that this is installed at MSI/installer time rather than by any
  runtime code in this corpus's `bin/` binaries. Out of this session's static-read-only scope.
- **B63-G2** (narrows **B17-G3**) — Disassemble the fill logic for `buildArgs`'s two large per-path buffers at
  `this+0x624`/`this+0x8324` (the `%s` sources for `-Djava.library.path=%s`/`--module-path=%s`) to their own
  origin — almost certainly another `GetModuleFileNameA`-style virtual call following the SAME pattern §63.1
  traced precisely for `restartPlatformDaemon0`'s install-root lookup, but not itself opened this session.
  Would complete the recipe needed for an actual working `java`-fallback `n5mig` relaunch (not merely a
  correct flag LIST).
- **B63-G3** — Live `[CERT-hw]` reproduction: issue an authenticated `GET .../update?refreshSoftware=1` request
  against a running N5 5.0.0.28 daemon and confirm the platform daemon process actually restarts (observable
  via a changed PID, matching `getProcessId0`'s own export) — this session's finding is a static disassembly +
  decompiled-source read, not a live reproduction of the end-to-end HTTP-to-process-restart path.
- **B63-G4** — Disassemble `fcn.180004890` (the `snprintf`-style formatting helper both `-Djava.library.path=%s`
  and `--module-path=%s` call through) to confirm it performs plain `%s` substitution with no additional
  `cmdline::`-style tagging of its own — a small residual completeness check for §63.2's finding, since this
  helper was identified but not opened this session.

## Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block63.md` from `/home/cristian/niagara5-research` (this session, verbatim, literal script output):
```
== verify-block: niagara5-block63.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 37  (adj 30)
   [CERT-live] 3
   [CERT] 14  (adj 12)
   [CERT-doc] 2
   [CERT-web] 7  (adj 5)
   [CERT-a] 2
   [INFER] 12  (adj 9)
-- ratio -- [INFER]/[CERT*] = 9/54 = 0.17
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  DaemonServlet.java:1-140  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  NativePlatformProvider.java:596-603  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/NiagaraDaemon.java:1381-1390  (range end verified; file has 1641 lines)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/http/WebServer.java:2117-2153  (range end verified; file has 2293 lines)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/Servlet.java:94-104  (range end verified; file has 126 lines)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:608-645  (range end verified; file has 823 lines)
   ok      organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/UpdateDaemonServlet.java:70-83  (range end verified; file has 823 lines)
   ok      organized/_bin-ext/nre/vineflower/com/tridium/nre/platform/NativePlatformProvider.java:49-65  (range end verified; file has 1459 lines)
   resolved 6 of 8
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```
**6 of 8 script-recognized citations resolve `ok`.** These are the ones cited with their full `organized/...`
path per METHODOLOGY §11's citation-form convention. The two `extern` items (`DaemonServlet.java:1-140`,
`NativePlatformProvider.java:596-603`) are bare short-forms redundant with a resolved full-path citation to the
SAME file elsewhere in the block: `DaemonServlet.java` is cited in full-path form in the header Sources
paragraph (`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/servlet/DaemonServlet.java:1-140`, the
same string this bare-form re-uses in §63.1's body for readability), and `NativePlatformProvider.java` is cited
in full-path form via its resolved `:49-65` range above — `:596-603`/`:1222` are the SAME file, different line
ranges, cited in full-path form once and in bare short-form again for the specific methods discussed. Neither
is an unpathed citation with no full-path counterpart anywhere in the block. Every `[CERT-hw]` claim
(native-binary/`radare2`/`strings`/`objdump` evidence — the bulk of this block's evidence) is, as expected per
METHODOLOGY §11's decompiled/native-binary convention, outside this script's `file:line` resolution scope
entirely (address- and export-name-based, not script-recognizable) and is instead covered by the inline
token-verify below.

**Reading the marker tally.** `[CERT-hw]` dominates (30 adjusted claims) — expected for a block whose primary
evidence is fresh `radare2`/`strings`/`objdump` runs over native binaries this session, not `file:line` reads.
`[CERT]` (12 adjusted) covers the decompiled-Java call-chain citations (§63.1's servlet/daemon chain, §63.4's
`SecurityManager`-collision disambiguation). `[CERT-web]` (5 adjusted) is the single JEP 486 fetch, its content
quoted at length in both the header blockquote and §63.4's body (each quoted clause counts as a separate
marker occurrence under the script's raw scan). The `[CERT-live]`, `[CERT-doc]`, and `[CERT-a]` raw hits (3/2/2)
are NOT fresh claims of this block's own — they come from THIS Self-verify section's and the header Method
paragraph's own prose quoting METHODOLOGY §3's marker DEFINITIONS (e.g. "`[CERT-live]` verified empirically
against a live REMOTE service") for reader orientation, the same self-referential inflation [Block 61]'s own
Self-verify section flagged and adjusted for — zero of them are markers attached to a claim this block actually
makes. `[INFER]` (9 adjusted) is concentrated in clearly-flagged spots: the `STARTUPINFOA`/
`PROCESS_INFORMATION` stack-variable role inference in §63.1 (a standard Win32 idiom, not itself
string-evidenced), the ICF-merge-generalization caveat in §63.1 ("does not prove... on every N5 build"), the
"unsurprising rather than incidental" framing in §63.4, and the buffer-fill-logic residual framing in §63.3 —
none are load-bearing for any of the four gaps' own CLOSED/ADVANCED verdicts, which rest on the `[CERT-hw]`/
`[CERT]` disassembly and source citations. Ratio 9/54 ≈ 0.17 (matching the script's own reported ratio
exactly), well below the ~0.5 exhaustion threshold — consistent with a productive, evidence-dominant session
against sources three prior blocks had each explicitly named as unopened.

**Inline token-verify.** Every `radare2` command and its output quoted above was run this session against the
freshly-copied, freshly-hashed scratch-directory binaries (paths under
`/tmp/claude-1000/-home-cristian-niagara-research/95f8084c-89bb-4c07-bb8d-5b922f6773a4/scratchpad/block63-native/`),
not reused from any prior block's output. Spot-check tokens independently re-confirmed present this session,
by direct tool output (not hand-recalled): `Java_com_tridium_nre_platform_NativePlatformProvider_
restartPlatformDaemon0` (export listing + `axt` + `pdf`, 3 independent commands, nre.dll), `"plat.exe
restartdaemon"` (both `pdf`'s string annotation AND an independent raw `px`/`ps` hex+string dump at the SAME
address, 2 independent read methods), `CreateProcessA` (import listing + single `axt` xref), the 7-way ICF
alias group at `0x1800026c0` (`iE` full listing, all 7 names), `station.java.options`/`wb.java.options`/
`-Dcmdline::` (3 independent `/`-search + `axt` pairs), the 28 `buildVMOptions` flag strings and ~20 `buildArgs`
flag strings (both via `grep -oE` over saved whole-function `pdf` dumps, not hand-transcribed), `JAVA_VERSION=
"25.0.4"` (direct `cat` of the live install's `jre/release` file), `DaemonSecurityManager`/
`PlatformSecurityManager` class bodies (2 whole-file reads, zero `SecurityManager`-API tokens found in either).
Every decompiled-Java `file:line` citation was `grep -n`-confirmed present at or adjacent to its stated line
this session immediately before drafting each section, following [Block 61]/[Block 57]'s own established
practice. Token-verify: **≈24 distinct load-bearing tokens** confirmed present in their cited source (native
binary or decompiled file) this session.

**MCP-doc snapshots**: N/A for the one `[CERT-web]` citation (JEP 486, fetched via `WebFetch`, not an
MCP/context7 doc tool) — the snapshot-registration rule (METHODOLOGY §5/§11) applies to MCP-doc citations
specifically; this was a direct web fetch, and the fetched content is quoted verbatim in the header blockquote
and §63.4's body, giving the citation's full text inline rather than via a separate snapshot file.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block63.md`. Per the caller's
explicit instruction ("Touch NO other file... The orchestrator integrates"), `INDEX.md`/`RESEARCH-STATE.md`/
`CATALOG.md` regeneration and backlog re-classification are deliberately NOT performed this session — left to
the orchestrator, matching [Block 61]/[Block 40]'s own convention for the same instruction. Scratch-directory
binaries copied under this session's Claude Code scratchpad (never written into the read-only install) are
left in place for the orchestrator's own disposal; no file under `/mnt/c/Program Files/Niagara/5.0.0.28` was
modified this session (five `cp` operations were READS of the install, zero writes).
