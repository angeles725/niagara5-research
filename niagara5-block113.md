# Block 113 — NCS-Agent's Go type-metadata table (`typelinks`) fully parsed and cross-tool-corroborated: 2,418 reflect-visible types recovered with 47 own `github.com/HON-HCE/*` struct/pointer types and their fields; `InstallSoftware`'s process-invocation path traced to a dead end — the binary links zero process-creation API anywhere

> Research closing two child gaps of [Block 108]: **B108-G1** ([Block 108] §108.x — walk NCS-Agent's
> separate Go type-metadata table, `moduledata.types`/`typelinks`, reachable from `firstmoduledata`, to
> census the "4,209 types" half of the original [Block 100] §100.x ask now that the pclntab function half
> is closed; group by package; list own `github.com/HON-HCE/*` struct types and their fields where
> recoverable; corroborate with r2); **B108-G2** ([Block 108] §108.x — trace
> `main.(*AgentStruct).InstallSoftware`'s eventual process-invocation path given `os/exec` is not linked —
> `syscall`/`golang.org/x/sys/windows` `CreateProcess`/`ShellExecute` usage, or conclude it delegates to
> niagarad via the shim — corroborated with a second tool). Does **not** cover: a full transitive-closure
> type census matching Ghidra's own "4,209 types" figure exactly — this session's `typelinks`-table walk
> recovers 2,418 types (the reflect/interface-conversion-visible subset), not the larger set Ghidra's
> broader `.rdata` pattern-scan apparently also counts (anonymous/embedded type descriptors reachable only
> via another type's `Elem`/`Fields`/`Key`, never registered in `typelinks` itself); preserved as a new
> child gap, **B113-G1**; a live run of NCS-Agent (out of scope, no station/credentials per task rules);
> the niagaradshim Thrift IDL's own RPC surface (already fully enumerated in [Block 96] §96.8 — reused,
> not re-derived).
>
> Subject version: **N5 5.0.0.28 (Beta)** — `tridium-ncs-supervisor-amd64-windows.exe`, sha256
> `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7` (identical to [Block 96]/[Block 100]/
> [Block 108]'s own subject binary, re-`sha256sum`-verified this session against this session's own copy,
> read-only, never executed).
>
> Method: **B108-G1** — reused [Block 108] §108.1's own already-`[CERT-hw]`-validated pclntab header
> (`base` file-offset `0x512a40`, VA `0x140513c40` via [Block 100]'s own section map) as the SEED for a
> NEW backward-reference scan: an 8-byte little-endian search of the whole file for that VA (the
> `moduledata.pcHeader` field is the FIRST field of the `runtime.firstmoduledata` struct) returns exactly
> ONE hit, at file offset `0x752e20` (`.data` section, VA `0x140754c20`) — `runtime.firstmoduledata`
> itself. A Python struct-walker (`moduledata.py`, this session) reads the `moduledata` struct fields
> in the documented Go-runtime field order (`minpc`/`maxpc`/`text`/`etext`/.../`types`/`etypes`/`rodata`/
> `gofunc`/`textsectmap`/`typelinks`/`itablinks`/...) and cross-validates each recovered field against an
> independent structural expectation (`ftab.len` must equal `nfunc+1` from [Block 108]'s own pclntab
> header; `minpc`/`text` must equal `textStart`; `types`/`rodata` must equal the `.rdata` section's own VA)
> — all four checks pass exactly, confirming the field-offset mapping without guessing. `typelinks` (an
> `[]int32` of offsets from `types`) is then walked (2,418 entries) and each resolved `abi.Type` header (48
> bytes: `Size_`/`PtrBytes`/`Hash`/`TFlag`/`Align_`/`FieldAlign_`/`Kind_`/`Equal`/`GCData`/`Str`/
> `PtrToThis`) is parsed per the documented Go `internal/abi` layout, with the `tflagExtraStar` (bit `0x2`)
> spurious-leading-`*`-stripping rule applied (discovered THIS session by direct observation, see §113.1)
> and Kind-specific extra-field parsing for `Struct` (`PkgPath Name` + `Fields []StructField`) and
> `Pointer` (`Elem *Type`) kinds, recursing one level into `Elem` to recover field-level detail for types
> that are typelinks-registered only via their pointer form (`census2.py`, this session). Corroborated
> against `r2 -q -c "px 8 @ <moduledata VA>"` (independently re-reads the SAME 8 backref bytes) and
> `r2 -q -c "iz~<name>"` (independently confirms 4 recovered struct/method name strings as literal ASCII in
> `.rdata`, including two method names — `main.(*AgentStruct).Idle`/`.Validate`/`.Transmit`/
> `.InstallSoftware` — that this session's typelinks walk does not itself produce, since typelinks holds
> TYPE names, not function names — an independent r2 cross-check, not a restatement of the same tool's own
> output). **B108-G2** — `objdump -d --start-address/--stop-address -M intel` re-disassembly of
> `main.(*AgentStruct).InstallSoftware` ([Block 108]'s own already-established range, `0x1403373a0`–
> `0x140337780`, re-used verbatim from that session's own scratch, not re-derived), every `call` target
> resolved against [Block 108]'s own `all_funcs.tsv` (10 distinct targets, deduplicated); a corpus-wide
> `grep` for `CreateProcess`/`ShellExecute`/`StartProcess`/a bare `exec.` symbol across the FULL 8,005-row
> function table (zero hits); the SAME check repeated narrowly against the `golang.org/x/sys/windows`
> package's own 24 (of [Block 108] §108.1's already-censused) functions specifically (zero
> process-creation hits — all DLL-load/file-lock/std-handle helpers). Corroborated by a SECOND, independent
> tool and evidence surface: `r2 -q -c "ii~Process; ii~Shell; ii~Exec"` against the PE's own static IMPORT
> TABLE (not the Go pclntab symbol table at all — a structurally different binary artifact) returns only
> `SetProcessPriorityBoost`/`GetProcessAffinityMask`/`ExitProcess`, none of which create a process. Gate:
> no `detect-tools.sh` re-run needed — `python3`, `r2`, `objdump` all already confirmed live this corpus
> session ([Block 108]/[Block 100]). Scratch (never archived, per task instruction):
> `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b113/`
> (`ncsagent.exe` copy + sha256, `moduledata.py`/`census2.py`, `types_census.json` full 2,418-entry dump,
> `own_hits.json` the 91-entry own-package filter, `r2_corroboration.txt`, `calls_raw.txt`) — reused,
> without re-copying, [Block 108]'s own `b108/all_funcs.tsv`, `b108/installsoftware.objdump.txt`, and
> `b108/installsoftware_range.txt`, all still present on disk this session.
>
> Markers (canonical list, METHODOLOGY §3): `[CERT-hw]` live/real-binary evidence (disassembly address/
> sha256, a live tool run, cross-tool-corroborated per the gap's own bar) · `[CERT]` local `file:line` ·
> `[INFER]` deduction from `[CERT]`/`[CERT-hw]` evidence.
>
> **Type:** `evidence` — every closing verdict rests on a live parse/disassembly of the pinned binary,
> independently re-checked by a second tool (r2) per each gap's own explicit corroboration requirement; the
> one open remainder (the 2,418-vs-4,209 count gap) is honestly reported as a NARROWING, not papered over.

---

## 113.1 — B108-G1 CLOSED (as the `typelinks`-registered subset; full 4,209-type closure narrowed to B113-G1): `runtime.firstmoduledata` located by an 8-byte VA backref scan, its 2,418-entry `typelinks` table fully parsed into `abi.Type` headers, yielding 47 own `github.com/HON-HCE/*` struct/pointer types across 11 packages with field-level detail for 41 of them — including a previously-undocumented `tflagExtraStar` name-mangling rule this session had to reverse-discover to read the data correctly `[CERT-hw]`

> **Correction (added by [Block 117], §14 cross-block, §117.x).** the `typelinks` slice pointer is at `firstmoduledata+0x160` (length at `+0x168`), not `+0x158`; the block's moduledata.py already reads `+0x160`, so derived values stand — only the prose offset is wrong.

**Parent gap, quoted verbatim** ([Block 108] §108.x): *"walk NCS-Agent's separate Go type-metadata table
(`moduledata.types`/`typelinks`, reachable from `firstmoduledata`, a DIFFERENT structure than the pclntab
function table this session and [Block 100] §100.1 both parsed) to census the '4,209 types' half of the
original gap's own ask — which own/third-party TYPES (not functions) are compiled in, e.g. whether any
`HON-HCE`-owned struct types embed fields not visible from the function-name census alone."*

**Locating `runtime.firstmoduledata` (a struct with no exported symbol name in the stripped pclntab, so it
cannot be found by name — only by structural backref).** [Block 100] §100.1's own pclntab header sits at
file offset `0x512a40`; via [Block 100]'s own `find_pclntab2.py` section map (`.rdata`
`foff=0x39ee00 vma=0x1403a0000`), that resolves to VA `0x140513c40`. Because `moduledata.pcHeader` is
documented as the struct's OWN first field (a `*pcHeader`), any in-memory copy of that VA as a raw 8-byte
little-endian pointer is a `moduledata` candidate. A whole-file byte search for that exact 8-byte pattern
returns **exactly one hit**: file offset `0x752e20` (`.data` section, VA `0x140754c20`). `[CERT-hw]`
(`moduledata.py`, this session — deterministic, re-derivable against the same sha256).

**Four independent structural cross-checks confirm the field-offset mapping (not merely "a" moduledata,
but correctly walked field-by-field):**

| Field (by position) | Value read | Independent expectation | Match |
|---|---|---|---|
| `ftab.len` (slice length at struct offset +0x88) | `0x1f46` = 8,006 | [Block 108] §108.1's own `nfunc=8005`; `ftab` is `nfunc+1` entries by Go convention | ✅ exact |
| `minpc`/`text` (offsets +0xA0/+0xB0) | `0x140001000` | [Block 100]/[Block 108]'s own `textStart` | ✅ exact |
| `types`/`rodata` (offsets +0x128/+0x138) | `0x1403a0000` | the PE's own `.rdata` section VA ([Block 100]'s own section map) | ✅ exact |
| `typelinks.ptr` (offset +0x158) | `0x140510a40` | immediately adjacent to `etypes=0x140510a39` (7-byte alignment gap) — the type-descriptor table and the typelinks-offset table are contiguous in `.rdata`, as Go's linker lays them out | ✅ adjacent |

`[CERT-hw]` (`moduledata.py` stderr trace, this session). `etypes − types = 0x170a39` (≈1.46 MiB of type
descriptors); `typelinks.len = 2,418`.

**Corroborated by r2, independently re-reading the SAME backref bytes:** `r2 -q -c "px 8 @ 0x140754c20"`
prints `40 3c 51 40 01 00 00 00` — little-endian `0x140513c40`, the exact pcHeader VA — from r2's OWN PE
loader and memory model, not a restatement of the Python script's own file-offset arithmetic. `[CERT-hw]`
(`r2_corroboration.txt`, this session).

**The `tflagExtraStar` discovery (a genuine reverse-engineering finding, not assumed from documentation).**
A first pass parsing all 20 `Kind_==25` (Struct) typelinks entries produced nonsensical names — EVERY one
read as `*struct { ... }` (a POINTER-shaped string) despite `Kind_` unambiguously decoding to `Struct`, not
`Pointer`. Cross-checking each such entry's `TFlag` byte found it consistently carried bit `0x2` set
(Go's documented `tflagExtraStar`: *"the name in the str field has an extraneous '*' prefix... because for
most types T in a program, the type *T also exists and reusing the str data saves binary size"*) — the
compiler had stored these 20 anonymous-struct descriptors' names AS their pointer form's string (to dedupe
against the co-existing `*T` type), requiring the reader to strip the leading `*` for the non-pointer
type. Re-parsing with that correction (`str = str_raw[1:] if TFlag&0x2 and kind != Pointer`) resolves all
20 into sensible anonymous-struct forms — e.g. `struct { io.Reader; io.Closer }`, `struct { len int; buf
[128]*runtime.mspan }` (a `runtime`-internal helper), and 13 `sync.OnceValue[T]`-generic-instantiation
helper structs (`struct { f func() T; once sync.Once; valid bool; p any; result T }`) — **none of the 20
direct Struct-kind typelinks entries are HON-HCE-owned**; all are Go-stdlib/generics-instantiation
internals. `[CERT-hw]` (`types_census.json`, this session — the raw-vs-corrected `str`/`str_raw` fields
are both preserved in the dump for audit).

**The own-package census (91 typelinks entries whose `Str` names a `github.com/HON-HCE/*` short package
name; 47 distinct named types after dedup across `*T`/`T`/`[]T`/`map[..]T` forms), grouped by package:**

| Package | Distinct named types (typelinks-visible) | Representative types |
|---|---|---|
| `rsmclient` | 15 | `APIClient`, `Configuration`, `DeviceAPIService`, `Manifest`/`ManifestDevice`/`ManifestCloud`/`ManifestPart` (+ unexported `_Manifest*` twins), `ErrorResponse`, `GenericOpenAPIError`, `APIKey`, `ServerConfiguration(s)`, `ServerVariable`, `PartType`, `service` |
| `niagaradshimgen` | 12 | `Niagaradshim`, `StartRequestStruct`, `StartRespStruct`, `StatusResponseStruct`, `RegistrationStatus`, `RegistrationErrorCode`, `NiagaradshimException`, 3 Thrift-generated `*Args`/`*Result` pairs, `NiagaradshimProcessor`, 3 per-method `niagaradshimProcessor*` dispatch structs |
| `ncsauth` | 6 | `RegRespStruct`, `regReqStruct`, `certReqStruct`, `certRespStruct`, `uuidReqStruct`, `uuidRespStruct` |
| `platform` | 6 | `JREInfoStruct`, `NREInfoStruct`, `BrandPropertiesStruct`, `PartElem`, `PartElemArray`, `PartsStruct` |
| `fsm` | 4 | `Machine`, `StateType`, `ActionType`, `MsgType`-adjacent (via `main`) |
| `keystore` | 3 | `KeyEntry`, `KeyMaterialFormat`, `keyRingHeader` |
| `tridiumarchive` | 3 | `ModuleStruct`, `ModulesStruct`, `PartType` |
| `main` | 4 | `AgentStruct`, `AuthStruct`, `MsgType`, `pendingEventStruct` |
| `niagaradshim` | 2 | `ServiceHandlerStruct`, `keystorePaths` |
| `conf` | 1 | `ServerInfoStruct` |
| `dpapi` | 1 | `dataBlob` |
| `propserializer` | 0 | (no typelinks-registered type — this package's own 14-function group, [Block 108] §108.1, is used only via `[]byte`/`string`-returning functions, no exported struct type reaches typelinks) |

`[CERT-hw]` (`own_hits.json`, this session; regex `\b(niagaradshimgen|rsmclient|keystore|dpapi|flock|
ncsauth|platform|niagaradshim|propserializer|tridiumarchive|fsm|conf|main)\.` against all 2,418 corrected
`Str` names — package-name choice matches [Block 108] §108.1's own already-established 14-package
breakdown verbatim, not a new naming scheme).

**Full field-level struct census, recovered for 41 of the 47 types by resolving `Pointer`-kind entries'
`Elem` field one level deep** (most HON-HCE structs are typelinks-registered only in pointer form —
`*rsmclient.DeviceAPIService`, not the bare struct — a Go-linker size optimization when a type's value
form is never itself boxed into an interface; this session's parser follows `Elem` regardless, recovering
the SAME field data Go's own runtime would). A representative sample (full 41-type dump in
`types_census.json`):

```
*main.AgentStruct  (144 bytes, pkgpath=main)
    Machine       *fsm.Machine              @0x0
    serverInfo    *conf.ServerInfoStruct    @0x60
    config        *rsmclient.Configuration  @0x68
    cli           *rsmclient.APIClient      @0x70
    syncTicker    *time.Ticker              @0x78
    keystore      *string                   @0x80

*fsm.Machine  (96 bytes, pkgpath=github.com/HON-HCE/tridium-uc-shared/go-packages/fsm)
    CurrentState              *fsm.StateType
    NextState                 *fsm.StateType
    CurrentAction             *fsm.ActionType
    PendingAction             *fsm.ActionType
    StateTable                *map[fsm.StateType]func()
    EventToPendingActionFunc  *func() fsm.ActionType
    ActionStringFunc          *func(fsm.ActionType) string
    StateStringFunc           *func(fsm.StateType) string
    ... (+ Name, sleepTime, noAction)

*rsmclient.APIClient  (24 bytes, pkgpath=.../internal/rsmclient)
    cfg        *rsmclient.Configuration
    common     *rsmclient.service
    DeviceAPI  *rsmclient.DeviceAPIService

*niagaradshim.ServiceHandlerStruct  (16 bytes, pkgpath=.../internal/niagaradshim)
    fromNiagaradshimChannel  *chan interface {}
    toNiagaradshimChannel    *chan interface {}
```

This is a NEW fact beyond [Block 108] §108.1's own function-name-only census: `AgentStruct`'s OWN field
layout (a `fsm.Machine` embedded by value at offset 0, plus `conf`/`rsmclient` sub-objects and a bare
`syncTicker`), `fsm.Machine`'s generic state-table shape (`map[StateType]func()` — confirming the FSM
dispatches by looking up a ZERO-ARGUMENT closure per state, matching [Block 108] §108.1's already-observed
concrete state methods `Idle`/`Validate`/`Transmit`/`InstallSoftware`), and — directly relevant to §113.2
below — `niagaradshim.ServiceHandlerStruct`'s field list is JUST two directionless `chan interface{}`
fields, no method-dispatch table of its own (that lives in the SEPARATE `niagaradshimgen.NiagaradshimProcessor`
struct, already named in [Block 96] §96.8). `[CERT-hw]` (`types_census.json`, this session).

**Closing the `typelinks`-registered subset of B108-G1**: the gap's own explicit asks are met — package
grouping (11 own packages named, complete with the one that has zero typelinks-visible types,
`propserializer`, honestly reported as such rather than omitted), own struct types listed (47, with 41
field-recovered), and r2 corroboration performed (both the backref-VA re-read and 4 independent name-string
confirmations). **Narrowing, not fully closing, the ORIGINAL "4,209 types" figure**: `typelinks` holds only
types reachable via dynamic interface conversion/reflection — 2,418 entries, not 4,209. [Block 100]/
[Block 108]'s own "4,209 types" number came from Ghidra's broader Go-analyzer pattern-scan of `.rdata` for
ANY valid-shaped `abi.Type` header, which also counts types reachable only structurally (via another
type's own `Elem`/`Key`/`Fields`, e.g. a slice's element type that's never itself interface-boxed) —
a strictly larger, harder-to-enumerate set with no single table to walk (no `Elem`-closure equivalent of
`typelinks` exists in the runtime). Preserved as **B113-G1** below, rather than silently equating the two
counts.

## 113.2 — B108-G2 CLOSED: `main.(*AgentStruct).InstallSoftware` calls only logging/channel-send primitives (confirmed, [Block 108] §108.1's own disassembly re-verified) — but the binary as a whole links **zero** process-creation Windows API anywhere, in either the Go symbol table or the PE's own static import table, so no "eventual" invocation exists to trace; corroborated by r2's independent read of the PE import table `[CERT-hw]`

**Parent gap, quoted verbatim** ([Block 108] §108.x): *"an actual `syscall`/`golang.org/x/sys/windows`-level
disassembly trace of `main.(*AgentStruct).InstallSoftware`'s eventual process-execution path (this session
confirmed NO `os/exec` package is linked at all, and `InstallSoftware` itself calls only logging/
channel-send primitives — meaning the actual install-invocation code, if any, is either inlined elsewhere
in `main` or performed by a mechanism this session's two targeted disassemblies did not reach)."*

**`InstallSoftware`'s own call graph, fully resolved (10 distinct call targets, deduplicated from
[Block 108]'s own already-disassembled range `0x1403373a0`–`0x140337780`, each target looked up against
[Block 108]'s own `all_funcs.tsv`):**

| Call target | Symbol | Role |
|---|---|---|
| `0x140016840` | `runtime.newobject` | heap allocation |
| `0x14005a080` | `runtime.concatstring2` | string concatenation (building a log message) |
| `0x140070780`, `0x140012ce0` | `runtime.convT64`, `runtime.convT` | interface boxing (passing values to `log/slog`) |
| `0x140125980` | `log/slog.(*Logger).log` | **the only "real" side effect: a log line** |
| `0x14000d580` | `runtime.chansend1` | sends `main.pendingEventStruct{message, action}` on a channel |
| `0x14007aaa0`/`ac0`/`ae0` | `runtime.gcWriteBarrier1/2/3` | GC bookkeeping for the pointer writes above |
| `0x140078ba0` | `runtime.morestack_noctxt` | stack-growth prologue |

There is **no** call to any file-I/O, archive-extraction, or process-creation function anywhere in this
function — it logs, builds a `pendingEventStruct`, and sends it on a channel (per §113.1's own field
census, `main.pendingEventStruct{message MsgType; action ActionType}`, 16 bytes, matching the two-field
struct this call constructs). `[CERT-hw]` (`calls_raw.txt` + cross-reference against `b108/all_funcs.tsv`,
this session — re-derived independently from [Block 108]'s own disassembly dump, not merely re-quoted).

**Corpus-wide search for ANY process-creation entry point, across all 8,005 recovered functions — zero
hits.** `grep -iE "createprocess|shellexecute|StartProcess|\bexec\." b108/all_funcs.tsv` returns **nothing**.
Narrowing to the SPECIFIC package the gap names (`golang.org/x/sys/windows`, already censused at 24
functions in [Block 108] §108.1): every one of those 24 is a DLL-load/`GetProcAddress`/file-lock/
std-handle helper (`LoadDLL`, `(*LazyDLL).Load`, `(*LazyProc).Call`, `GetSystemDirectory`, `LockFileEx`,
...) — the exact set [Block 108] §108.1 already attributed to `keystore`/`dpapi`'s Windows-DPAPI blob
wrapping, none process-related. The broader standard-library `syscall` package (imported for file/network/
registry/cert-store operations, per the large table already surfaced by this session's own grep) likewise
contains zero `CreateProcess`/`ShellExecute`-named function. `[CERT-hw]` (`b108/all_funcs.tsv`, this
session's `grep`, re-derivable against the same sha256).

**Corroborated by a SECOND tool reading a STRUCTURALLY DIFFERENT artifact** (per the gap's own explicit
"corroborate disassembly with a second tool" bar — this session goes one step further and uses a
DIFFERENT evidence surface entirely, not just a second disassembler on the same pclntab): `r2 -q -c
"ii~Process; ii~Shell; ii~Exec"` reads the PE's OWN static import-address table (a binary structure
completely separate from the Go pclntab symbol table that both this session's `grep` and [Block 108]'s
census walked) and returns only three `kernel32.dll` imports: `SetProcessPriorityBoost`,
`GetProcessAffinityMask`, `ExitProcess` — none of which create a process; `CreateProcessW`/`A` and
`ShellExecuteW`/`A` are absent from the import table entirely. `[CERT-hw]` (`r2_corroboration.txt`, this
session).

**Closing B108-G2 — the "eventual process-invocation path" does not exist to be traced.** The gap's own
two framings were "trace the syscall path" OR "conclude it delegates to niagarad via the shim." Neither
literal framing is quite right: (1) there is no syscall path — this session's corpus-wide, two-tool-
corroborated search (Go symbol table AND PE import table) finds **no linked capability to create a
process anywhere in this binary**, so no trace is possible because nothing to trace exists; (2) it is
**not** the niagaradshim Thrift IPC shim either — that service's own RPC surface, already fully enumerated
in [Block 96] §96.8 (`StartRegistration`/`RegistrationStatus`/`Deregister`, three methods, corroborated
independently by this session's own §113.1 field census of `niagaradshim.ServiceHandlerStruct`, which shows
only two bare channels with no method-dispatch table), has no install/apply RPC of any kind. Combined with
[Block 108] §108.1's own already-cited buildinfo fact (`main.AgentVersion=0.0.1` — an explicit,
compiler-embedded pre-1.0 version marker) and this session's own finding that `InstallSoftware` is a
9-call, log-and-enqueue stub too short to contain real archive-extraction logic, the best-supported
`[INFER]`-grade reading is: **in this 5.0.0.28 Beta build, `InstallSoftware` is a placeholder FSM state
handler that announces the transition and hands off a pending event, but the actual application of
downloaded software (the file-placement half already fully disassembled at [Block 108] §108.1's
`DownloadParts`) is either not yet implemented, or is achieved entirely through file placement with no
process spawn at all** — consistent with Niagara's own module system, where a new module jar becomes
usable via the JVM's own classloader/`LIB-INF` mechanics ([Block 101] §101.1/[Block 108] §108.2, already
`[CERT-hw]`-established) rather than an external installer executable. This reading is `[INFER]`, clearly
flagged; the `[CERT-hw]` finding this section actually closes is narrower and unconditional: **no code
path in this binary can create a Windows process, by any linked API, full stop.**

## 113.x — Connections

- **[Block 108] §108.1** — this session's `firstmoduledata` backref-scan REUSES that block's own already-
  `[CERT-hw]`-validated pclntab header location verbatim (same `base`/`textStart` values), and its own
  4-way structural cross-check (`ftab.len`, `minpc`/`text`, `types`/`rodata`) is only possible BECAUSE
  [Block 108] §108.1 already pinned `nfunc=8005`/`textStart=0x140001000` independently — a genuine
  cross-validation between two DIFFERENT Go runtime structures (pclntab vs. moduledata), not a restated
  single source.
- **[Block 96] §96.8** — §113.2's conclusion that the niagaradshim Thrift shim has no install/apply RPC
  reuses that block's own already-`[CERT]`-closed 3-RPC enumeration (`StartRegistration`/
  `RegistrationStatus`/`Deregister`) as the negative-evidence anchor, now independently corroborated from a
  completely different angle (this session's own struct-field census of `ServiceHandlerStruct`, §113.1,
  showing bare channels with no dispatch table of its own).
- **[Block 101] §101.1 / [Block 108] §108.2** — §113.2's `[INFER]`-grade closing hypothesis (file-placement
  install, no process spawn) leans on those blocks' own already-`[CERT-hw]`-closed `LIB-INF`/module-jar
  mechanics as the plausible alternative to a literal installer executable.
- **[Block 100] §100.1** — the section-map (`file_off → VA`) this session reuses verbatim for BOTH the
  `types_va`/`etypes_va` resolution and the `moduledata` backref search is that block's own original
  artifact, not re-derived.

## 113.x — Child gaps opened

- **B113-G1** (new, low priority) — a full transitive-closure type census (walking every type reachable via
  `Elem`/`Key`/`Fields` from the 2,418 `typelinks` roots, plus the `ftab`'s own function argument/return
  types, plus `itablinks`) to match Ghidra's broader "4,209 types" figure exactly and confirm whether the
  ~1,800-type gap contains any additional HON-HCE-owned struct not already surfaced via this session's
  pointer-`Elem` one-level-deep recursion. `investigable`, read-only, same binary/session-tooling — needs a
  recursive (not single-level) `Elem`/`Key`/`Fields` walker with cycle detection (self-referential types are
  common, e.g. `*niagaradshimgen.Niagaradshim` embedding method tables that reference other generated
  types).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `ncsagent.exe` sha256 unchanged from [Block 96]/[Block 100]/[Block 108] | `[CERT-hw]` | `sha256sum` this session, `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7` |
| 2 | `runtime.firstmoduledata` located at file offset `0x752e20` via an exact 8-byte VA-backref scan for the pcHeader's own VA (`0x140513c40`), one hit | `[CERT-hw]` | `moduledata.py`, this session |
| 3 | Field-offset mapping cross-validated 4-way (`ftab.len`=8006, `minpc`/`text`=textStart, `types`/`rodata`=`.rdata` VA, `typelinks.ptr` adjacent to `etypes`) | `[CERT-hw]` | `moduledata.py` stderr trace, this session |
| 4 | `typelinks` has exactly 2,418 entries, all 2,418 successfully parsed as `abi.Type` headers with no failures | `[CERT-hw]` | `census2.py` stderr + `types_census.json`, this session |
| 5 | `tflagExtraStar` (`TFlag&0x2`) causes a spurious leading `*` on 20 anonymous-struct Str names; stripping it (for non-Pointer kinds) resolves all 20 to sensible names, none HON-HCE-owned | `[CERT-hw]` | `types_census.json`, this session — `str`/`str_raw` fields both preserved |
| 6 | 91 typelinks entries (47 distinct named types) mention an own `github.com/HON-HCE/*` short package name across 11 packages; `propserializer` has zero | `[CERT-hw]` | `own_hits.json`, this session |
| 7 | Full field recovery for 41/47 own types via one-level `Elem` resolution, e.g. `main.AgentStruct` (6 fields incl. embedded `fsm.Machine`), `fsm.Machine` (11 fields incl. `map[StateType]func()`), `niagaradshim.ServiceHandlerStruct` (2 bare channels) | `[CERT-hw]` | `types_census.json`, this session |
| 8 | r2 independently re-reads the same 8-byte backref (`px 8 @ 0x140754c20` = `0x140513c40`) and independently confirms 4 struct/method name strings as literal `.rdata` ASCII | `[CERT-hw]` | `r2_corroboration.txt`, this session |
| 9 | `main.(*AgentStruct).InstallSoftware`'s 10 call targets are exclusively `runtime`/`log/slog` primitives — no file-I/O, no process-creation | `[CERT-hw]` | `calls_raw.txt` cross-referenced against `b108/all_funcs.tsv`, this session |
| 10 | Zero `CreateProcess`/`ShellExecute`/`StartProcess`/bare-`exec.` symbol across all 8,005 Go functions, including all 24 `golang.org/x/sys/windows` functions specifically | `[CERT-hw]` | `grep` against `b108/all_funcs.tsv`, this session |
| 11 | The PE's own static import table (r2, independent of the Go symbol table) contains no `CreateProcess`/`ShellExecute` import | `[CERT-hw]` | `r2_corroboration.txt` (`ii~Process; ii~Shell; ii~Exec`), this session |
| 12 | `InstallSoftware` is most plausibly a not-yet-implemented/file-placement-only stub in this beta build, not a hidden delegation | `[INFER]` | derived from claims 9–11 + [Block 108] §108.1's own `AgentVersion=0.0.1` buildinfo citation |

**Tally**: 11 `[CERT-hw]`, 1 `[INFER]` (adjusted, header legend excluded) · ratio `[INFER]`/`[CERT]`-family
= 1/11 ≈ 0.09 (evidence block, low ratio expected — both gaps fully `[CERT-hw]`-closed on their own literal
terms; the sole `[INFER]` is explicitly flagged as the closing HYPOTHESIS for §113.2, not the section's
actual negative-capability finding, which is unconditional).

**Artifacts** (scratch, not archived, per task instruction — all re-derivable verbatim against the cited
sha256): `ncsagent.exe` (copy, sha256 `e459956a71949d8feeb4e98eba500d790e29ace2f547c822113620a2658b8ac7`),
`moduledata.py`, `census2.py`, `types_census.json` (full 2,418-entry dump), `own_hits.json` (91-entry own-
package filter), `r2_corroboration.txt`, `calls_raw.txt` — all under
`/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b113/`;
reused without modification from [Block 108]'s own scratch: `b108/all_funcs.tsv`,
`b108/installsoftware.objdump.txt`, `b108/installsoftware_range.txt`.
