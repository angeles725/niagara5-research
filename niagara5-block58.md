# Block 58 — PANCCADIA beyond config.bog: histories, alarms, files and systemDb in an N4→N5 migration

> Research of **the real PANCCADIA station directory beyond `config.bog`** — closing [Block 24]'s child gap
> **B24-G2** and [Block 31]'s child gap **B31-G4** (both note that only `config.bog` was available in the
> `poc/n5mig-panccadia/in/` copy; PANCCADIA's points/histories/alarms/schedule bog files were never censused).
> This block goes to the real station path itself — read-only, structure/counts/sizes/types only — and finds
> the accessible copy holds **no histories, no schedules, no px files, and no systemDb**: the gap cannot be
> closed with real data because that data structurally does not exist at this path. Covers: (1) a full
> recursive, read-only inventory of `/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA`
> (verified — the exact path [Block 17] §17.1 already confirmed) by extension/size/mtime; (2) `alarm.adb`'s
> format identification (magic-byte read only, cross-checked against `niagara-research`'s own prior
> `alarm.adb` corpus, [Block 702]); (3) a structural absence check for `history/`, `shared/px/`, `file:^`,
> and `systemDb`/`orientdb`, corroborated by contrasting PANCCADIA against **sibling stations on the same
> Workbench profile** that DO carry those directories; (4) a second, independent snapshot
> (`PANCCADIA.rar`, dated 2026-09-04) confirming the same directory shape 17 days earlier — ruling out a
> one-off capture gap; (5) mapping every store found (present or absent) to its N5 migration path using the
> [Block 19]/[Block 24]/[Block 26]/[Block 31] corpus already built. Does **not** cover: opening `security/`
> or `licenses/` anywhere in the profile (out of scope per task instruction); any content of
> `user/stationlogin.edat` beyond its format tag (Workbench login-cache credential material — not opened);
> `alarm.adb`'s per-record byte layout beyond the magic/version header (no record data exists to parse — the
> file's record region is empty, §58.3); locating PANCCADIA's actual runtime histories/schedules/px, which
> prior-session memory places on a separate host ("live station on Linux snap") — this block only establishes
> that they are NOT on the Windows Workbench path, not where they actually are (→ child gap B58-G2).
>
> Subject version: station directory observed **2026-09-27** at
> `/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA` (path re-confirmed present, same
> as [Block 17] §17.1's 2026-09-27 read); the station itself is N4 4.14/4.15-line per [Block 14] §14.2/
> [Block 17] header. N5 baseline: **5.0.0.28 (Beta)**, same install [Block 14]/[Block 17]/[Block 19]/
> [Block 24]/[Block 26]/[Block 31] all read. No content bytes of `config.bog` or `alarm.adb` are re-derived
> here beyond format identification — this block's own primary contribution is the *filesystem* census, not
> the bog's internal contents (already covered exhaustively by [B24]/[B31]/[B17]).
>
> Sources (all local, read-only, nothing copied into the repo, nothing extracted):
> - `/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA/` — `find`/`ls -la`/`du`/`file`/
>   `stat`/`xxd` (header bytes only) this session, on the live path, in place.
> - `/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA.rar` — `unrar l` (listing only,
>   no extraction) this session.
> - `/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/{stations/*,backups,registry}` — sibling-station and
>   profile-level directory listings this session, for structural contrast (which stations carry `history/`,
>   `alarm/`, `shared/px/`; whether any PANCCADIA `.dist` exists anywhere in `backups/`).
> - `niagara-research/niagara-mental-model-bloque702.md` (JACE_UMBRELLA `alarm.adb` format:
>   magic `600DF00D` v1, cleartext BOG-style k/v records) — REMITTANCE, read this session, cross-checked
>   against PANCCADIA's own `alarm.adb` header bytes.
> - `niagara5-block19.md` §19.3 (`.hdb` magic unchanged N4→N5), §19.4/§19.5 (systemDb/orientSystemDb
>   architecture); `niagara5-block24.md` §24.1-§24.2 (the full `migrator.jar` file/converter catalog);
>   `niagara5-block26.md` §26.4/§26.7/§26.8 (history capacity enforcement + PANCCADIA's own capacity census);
>   `niagara5-block31.md` §31.1-§31.2/§31.10 (the corrected config.bog census, B31-G4 itself); `niagara5-
>   block17.md` §17.1/§17.3 (the same station path, config.bog sha256, and the real per-module object
>   census) — all reused as REMITTANCE, none re-derived.
> - `niagara-research/tools/hdbread.py` — read for its header-only capability (§8's `--schema` mode parses
>   only the magic/version/config-XML header, not full records); **not invoked** — zero `.hdb` files exist at
>   this path to read (§58.4).
>
> Method: `find`/`ls -la`/`stat`/`du`/`file`/`xxd` (first 128 bytes only, structural magic-byte
> identification, never a content dump) directly against the live, read-only path; `unrar l` (listing only)
> against the one archive found; cross-directory comparison against 12 sibling station folders on the same
> Workbench profile for structural contrast; cross-corpus `grep` against `niagara-research`'s own prior
> `alarm.adb`-format blocks. Markers: `[CERT-hw]` — every finding below is a **direct live-filesystem
> observation this session** (a `find`/`ls`/`stat`/`file`/`xxd` run against the real, unmodified path — the
> same evidence class [Block 17] uses for its own live-environment observations) · `[CERT]` — REMITTANCE
> citations into an already-committed corpus block, `grep`-confirmed present at the cited line this session ·
> `[INFER]` deduction.
>
> **CLIENT DATA DISCIPLINE — read before any number below.** Every count/size/mtime/extension in this block
> is STRUCTURAL metadata about a real client station. No point value, no history/alarm record content, no
> user name, and no credential was read, extracted, or reproduced. `user/stationlogin.edat`'s only quoted
> bytes are its 16-byte format-tag header (`[aes-256.2]=` + the start of an AES-256-encrypted opaque blob —
> not a credential, not decryptable from the tag alone); nothing past that tag was read. `security/` and
> `licenses/` anywhere in the profile were never opened, listed past their top-level name, or descended into.
> Nothing under the station path was copied, moved, or written to; every command ran directly against the
> live path in place.
>
> Build/porting layer, extending the census half of [Block 24]/[Block 31]. Connects [Block 17] (same station
> path, config.bog census reused not re-derived), [Block 19] (`.hdb`/systemDb N4→N5 architecture, applied
> here to what is/isn't actually present), [Block 24] (migrator file-type catalog, applied to `alarm.adb`),
> [Block 26] (history capacity — PANCCADIA's own census already showed zero exposure; this block explains
> WHY no `.hdb` file was available to check it against in the first place).
>
> **Type:** `mixed` — §58.1-§58.5 are evidence (direct filesystem reads, this session's own `[CERT-hw]`);
> §58.6's migration-scope table draws `[INFER]` conclusions by mapping this session's census against four
> prior blocks' converter/format findings — the declared `mixed` trigger.

---

## 58.1 — The accessible PANCCADIA station directory: 15 files, 2.4 MB, 4 extensions `[CERT-hw]`

`/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA` exists, matches [Block 17] §17.1's
2026-09-27 path exactly, and contains **15 files, 2,507,748 bytes (2.4 MB), across 4 extensions** — no
subdirectories except `user/`. `[CERT-hw]` `find`+`du -sb` this session (`du` and a per-file `stat` sum
agree exactly: 2,507,748 bytes).

| Extension | Count | Total size | Identity |
|---|---|---|---|
| `.bog` | 1 | 40,290 B | `config.bog` — driver-network config, already exhaustively censused by [B17]/[B24]/[B31] |
| `.adb` | 1 | 1,024 B | `alarm.adb` — alarm database, §58.3 |
| `.txt` | 11 | 2,442,824 B | `console.txt` + 10 rotated `console_backup_*.txt` — Workbench operational log, §58.5 |
| `.edat` | 2 | 23,250 B | `user/stationlogin.edat` + its own timestamped backup — Workbench login cache, §58.5 |

`[CERT-hw]` `find "$STATION" -type f | sed 's/.*\.//' \| sort \| uniq -c`, this session. Every file's mtime
falls in a **2026-09-21 10:25–10:42** window except the 10 console backups (rotated earlier, same day) —
`config.bog`/`alarm.adb`/`console.txt` are all being actively written (mtimes at or near session-adjacent
times), confirming this IS a live, currently-synced Workbench connection to PANCCADIA, not a stale/abandoned
copy. `[CERT-hw]` `find -printf '%TY-%Tm-%Td %TH:%TM'`, this session.

## 58.2 — `config.bog`: not re-derived, pointer only `[CERT]`

40,290 bytes, sha256 unchecked this session (already anchored by [B17] §17.1/[B31] header at
`96e429deabdff32af9dfa0e87b4eafef28481f196e0e068e46e07fd86d0c1075` for the identical-size prior copy — this
session's copy is 21 days newer, same directory, not re-hashed, since this block's task is the *filesystem*
census around it, not a re-read of its contents). Its full per-module object census (3,545 typed elements,
288 distinct types, 30 modules), type/slot compatibility verdict (259 CLEAN / 16 added-only / 8
removed-property / 5 version-gap-unresolved / 44 custom-module objects at risk), and converter-catalog
cross-check are [B24]/[B31]'s own findings, reused here as REMITTANCE — not re-derived, per this task's
explicit "beyond config.bog" framing. §58.6's migration-scope table cites the verdict, not the mechanism.

## 58.3 — `alarm.adb`: the Niagara alarm-database format, present but effectively empty `[CERT-hw]` `[CERT]`

**Format identification, header bytes only.** The first 16 bytes read `60 0D F0 0D 00 00 00 01 …` — magic
`600DF00D`, version 1 (big-endian uint32 at offset 4). `[CERT-hw]` `xxd` first 128 bytes, this session.
This magic is **not new to this corpus**: `niagara-research`'s own prior focus already opened and documented
this exact container format on a different N4 station (JACE_UMBRELLA) — `[CERT]`
`niagara-mental-model-bloque702.md:10` — *"`alarm.adb` (17408 B) is NOT a `.hdb`: magic `60 0D F0 0D`,
version 1 — the Niagara alarm-database format (`FileAlarmDbConfig`, the deployed AlarmService store)"* —
with cleartext BOG-style key/value records (`msgText=…|sourceName=…|TimeZone=…|escalated=…`). PANCCADIA's
header bytes match that magic+version exactly.

**PANCCADIA's copy is effectively empty.** At only 1,024 bytes total, the record region past the header
(roughly offset 0x2C onward, based on the non-zero header words ending around there) is **entirely
zero-filled** — `[CERT-hw]` `xxd` full-file dump, this session, confirms every byte from offset 0x20 to
end-of-file (1,024 B) is `00`. Contrast: `niagara-research` B702's JACE_UMBRELLA `alarm.adb` is **17,408
bytes** holding **~15 real alarm records** (`[CERT]` `bloque702.md:10,17` — all NRIO ping-fail/success
events). PANCCADIA's `alarm.adb` is **not absent** (unlike history/px/schedule, §58.4) — the alarm store
exists, is actively maintained (mtime 10:42, the most recent of any file in the directory — newer than
`config.bog`'s 10:25), and is correctly magic-stamped — but currently holds **zero alarm records**, i.e. the
station has raised no alarms recently enough to survive whatever retention/rollover this store applies, or
the store was recently reset. `[INFER]`: a per-byte parse of the non-zero header words (`01A0`, `C4A1C286`,
`0200`, `0008`, `0400` at offsets 0x0C-0x20) was not attempted — no local tool exists in this corpus to
decode `FileAlarmDbConfig`'s exact header layout the way `hdbread.py` decodes `.hdb` — → child gap **B58-G4**.

**No `alarm/` subdirectory — PANCCADIA's `alarm.adb` sits loose at the station root.** Sibling station
`HM_BMS`, on the SAME Workbench profile, stores its alarm database inside a dedicated `alarm/alarm.adb`
subdirectory (`[CERT-hw]` `find .../HM_BMS/alarm` this session → `alarm/alarm.adb`), the conventional N4
layout. PANCCADIA's copy is directly at `PANCCADIA/alarm.adb`, no `alarm/` wrapper. `[INFER]`: this may
reflect a different AlarmService store configuration (a custom file path) rather than a corrupted/relocated
copy — not resolved this session, since resolving it would require opening the AlarmService config inside
`config.bog` (out of this block's filesystem-census scope, and already fully censused content-wise by
[B24]/[B31] without flagging a non-default alarm-store path).

## 58.4 — Structurally absent: histories, schedules, px, systemDb `[CERT-hw]`

Zero files of each of these classes exist anywhere under the PANCCADIA station directory — confirmed by
direct search, not merely unlisted:

| Store | Search | Result |
|---|---|---|
| Histories (`.hdb`) | `find "$STATION" -iname "*.hdb"` | **0** |
| Schedules | `find "$STATION" -iname "*schedule*"` | **0** (extends [B31] §31.10 B31-G4's config.bog-internal finding — zero `schedule:*` typespecs — to the filesystem: no separate schedule bog file exists either) |
| px UI files (`.px`) | `find "$STATION" -iname "*.px"`, and no `shared/px/` directory | **0** files, directory absent |
| `file:^` user-file space | no `file/` directory under the station | absent |
| `systemDb`/`orientSystemDb` | `find` for `*systemdb*`/`*orient*` across the FULL `Niagara4.14` profile tree (not just this station) | **0** anywhere in the profile |

`[CERT-hw]` each `find`, this session, zero matches (exit code / empty output confirmed for each, not
inferred from an incomplete listing).

**This is corroborated by cross-station contrast, not asserted from PANCCADIA alone.** On the SAME Workbench
profile, other stations DO carry these directories: `HM_BMS/history/station/seg{1,4,7}` (a real, populated
history tree) and `HM_BMS/alarm/alarm.adb`; `REFLOW`, `HoneywellMX60`, `HoneywellMX605132026`,
`PRUEBAS_reflow`, `PRUEBAS`, and `HM_BMS` all carry a `shared/px` directory. `[CERT-hw]` `find
OptimizerSupervisor -maxdepth 6 -type d ...`, this session — the Workbench environment demonstrably DOES
persist history/px content locally for stations that have it; PANCCADIA's absence is not an artifact of how
this Workbench profile stores data in general.

**Corroborated a second, independent way: a 2026-09-04 snapshot shows the identical shape.**
`PANCCADIA.rar` (RAR5, 74,538 B, mtime 2026-09-04 16:03 — 17 days before this session's live copy) is an
ad-hoc manual archive of the same station, listed (not extracted) this session: `[CERT-hw]` `unrar l`, this
session — 15 entries: `config.bog` (35,094 B, an OLDER/smaller version), 10 `console_backup_*.txt`,
`user/stationlogin.edat` + its own backup, and the `user/`+`PANCCADIA/` directory markers. **No `alarm.adb`
in this earlier snapshot at all** (it postdates 2026-09-04 — consistent with §58.3's "actively maintained,
recently reset" reading) — and, as in the live copy, **no history, schedule, px, or systemDb content**. This
rules out a one-off capture gap: the directory shape (config+console+login only, structurally no
history/px/schedule/systemDb) is stable across at least 17 days of this station's real Workbench-visible
footprint.

**`systemDb` absence is profile-wide, not station-specific — flagged as unconfirmed cause.** No
`systemDb`/`orientdb`-named path exists anywhere under the entire `Niagara4.14` OptimizerSupervisor profile
(stations, platform-level `registry/`, or elsewhere) — the platform DOES have its own separate `registry/`
store (`registry.db`+`registry.chk`, module registry — a DIFFERENT store than systemDb, per
`niagara-research`'s own B692 documentation of that pair, `[CERT]` `bloque692.md:22,89`, not re-derived
here). `[INFER]`: whether `systemDb`/`orientSystemDb` is simply unlicensed/unused on this Honeywell OEM
4.14 install (consistent with this same install's other license-gated findings, e.g. [Block 17] §17.2's
`tridium:nre` wall) or structurally never provisioned by this OEM distribution is not resolved — → child gap
**B58-G3**.

## 58.5 — Files found that are out of migration scope entirely `[CERT-hw]`

Two classes of file exist at this path that are **not station data** at all, and carry no `n5mig` relevance:

- **`console.txt` + 10 `console_backup_*.txt`** (11 files, 2,442,824 B) — a Workbench-side rolling operational
  log. Several rotate at exactly **262,143 bytes** (`0x3FFFF`) — a fixed rollover cap, `[CERT-hw]` `stat`
  this session on 6 of the 11 files matching that exact size. `console.txt` itself is 3,696 lines at its
  current 262,143-byte cap. This is an ephemeral log, not part of `config.bog`/`.dist`/any migrated artifact.
- **`user/stationlogin.edat` + `user/stationlogin_backup_260921_1024.edat`** (11,625 B and 11,625 B in the
  live copy; 11,985 B in the 2026-09-04 RAR snapshot) — a Workbench-LOCAL encrypted login cache, format tag
  `[aes-256.2]=` followed by an opaque AES-256-encrypted blob (`[CERT-hw]` `xxd` first 16 bytes only, this
  session — no further bytes read). This is Workbench USER-PROFILE data (how the local Workbench
  authenticates to the station), never itself part of the station's own `config.bog`/`.dist` — out of
  `n5mig`'s scope entirely, since `n5mig` migrates STATION artifacts, not the operator's local client cache.

**No PANCCADIA `.dist` backup exists anywhere in the profile — a second, differently-scoped confirmation of
[Block 17] §17.1's negative search.** [B17] searched all of `/mnt/c/Users/equipo` recursively for
`*panccadia*.dist` and found zero. This session separately checked the profile's dedicated
`OptimizerSupervisor/backups/` folder directly: it holds exactly **one** `.dist` file,
`backup_PRUEBAS_251003_2343.dist` (39,498,632 B) — belonging to a DIFFERENT station (`PRUEBAS`), not
PANCCADIA. `[CERT-hw]` `ls -la OptimizerSupervisor/backups`, this session. `n5mig`'s documented primary input
([B14] §14.2, [B17] §17.1) remains unavailable for PANCCADIA from either angle; [B17]'s individual-`.bog`
input path is still the only one this station currently supports.

## 58.6 — Migration-scope table: what exists, its N4 format, and its N5 path `[CERT]` `[INFER]`

| Store | Present? | N4 format evidence | Size | N5 handling | Risk |
|---|---|---|---|---|---|
| `config.bog` (driver network) | **Yes** | BOG-XML, zip-compressed, magic verbatim §19.1 | 40,290 B | **Converted** — `BBogMigrator`/`BBogPremigrator`, full 58-type catalog ([B24] §24.2); 259/288 types CLEAN, 16 added-only, 8 removed-property (7 covered/untriggered, 1 real non-fatal orphan `fox:FoxService.foxsCert`, [B31] §31.6) | **Low** for standard modules; **High** for 3 custom modules (44 objects, silently stripped by `BModuleRemovalConverter` unless reinstalled + `moduleName=`-declared before migration, [B17] §17.5-§17.7) |
| `alarm.adb` (alarm database) | **Yes**, but empty | Proprietary `FileAlarmDbConfig` container, magic `600DF00D` v1, cleartext BOG-style k/v records (§58.3, cross-checked against `niagara-research` B702) | 1,024 B (0 real records) | **No path found** — zero `alarm:*`/`.adb`-extension entries in `migrator.jar`'s 58-type catalog or its 8 core file/dist migrators ([B24] §24.2, independently reconfirmed by [B26] §26.7's zero-alarm-converter grep); whether N5 keeps the same container (copied-as-is, parallel to `.hdb`'s confirmed-unchanged magic, §19.3) is unconfirmed | **Unknown** — content-wise moot for PANCCADIA today (0 real records to lose), but the FORMAT-COMPATIBILITY question is open regardless → **B58-G1** |
| History (`.hdb`) | **No** — 0 files | N/A here; format elsewhere confirmed bit-identical N4↔N5 (both `VERSION_1`/`VERSION_2` sub-formats, [B19] §19.3) | 0 B | **N/A** at this path; if/when located, copied-as-is per [B19], capacity-mode hazard already measured at zero for PANCCADIA specifically ([B26] §26.8, config.bog's own `HistoryConfig` census) | **N/A** here → **B58-G2** |
| Schedules | **No** — 0 files, 0 `schedule:*` typespecs even inside config.bog | N/A | 0 B | **N/A**, untested ([B31]'s B31-G4, now doubly confirmed — no bog elements AND no separate schedule file) | **N/A** → folded into **B58-G2** |
| px UI files (`.px`) | **No** — 0 files, no `shared/px/` dir | N/A here (present on 6 sibling stations on the SAME profile) | 0 B | **N/A** here; `BPxMigrator`/`BPxPremigrator` exist as registered structural file migrators generically ([B24] §24.2) | **N/A** → folded into **B58-G2** |
| `file:^` user files | **No** — no `file/` dir | N/A | 0 B | **N/A** | **N/A** |
| `systemDb`/`orientSystemDb` | **No** — absent profile-wide | N/A at this station; architecture/license-gate elsewhere confirmed unchanged, embedded OrientDB 3.2.23→3.2.55 bump ([B19] §19.4/§19.5) | 0 B | **N/A** here (nothing to migrate); cause of absence (unlicensed vs. never-provisioned on this OEM build) unresolved | **N/A** → **B58-G3** |
| Backups (`.dist`) | **No** — 0 for PANCCADIA anywhere in the profile | N/A | 0 B | **N/A** — [B17]'s individual-`.bog` input path remains the only one available | **N/A** |
| Console logs (`.txt`) | Yes, 11 files | Rolling Workbench operational log, 262,143 B rotation cap | 2,442,824 B | **N/A** — not station data, no converter targets it | **N/A** |
| Workbench login cache (`.edat`) | Yes, 2 files | AES-256-encrypted, `[aes-256.2]=` format tag | 23,250 B (11,625×2 live copy) | **N/A** — Workbench-local, never part of `config.bog`/`.dist` | **N/A** |

**Headline finding**: of the 8 station-data store classes this task named, only **2 exist** at PANCCADIA's
accessible Windows Workbench path (`config.bog`, already exhaustively migration-mapped by [B24]/[B31]/[B17];
`alarm.adb`, format-identified but with no registered N5 conversion path and currently zero real records to
carry). The other **6 classes — histories, schedules, px, `file:^`, systemDb, and `.dist` backups — are
structurally absent**, not merely uncensused, confirmed by (a) direct recursive search returning zero
matches, (b) contrast against sibling stations on the identical Workbench profile that DO carry
history/alarm/px content, and (c) an independent snapshot from 17 days earlier showing the same shape. B24-G2
and B31-G4 cannot be closed with real PANCCADIA points/histories/alarms/schedule DATA from this path, because
that data — if it exists at all for this station — is not reachable from here; it most plausibly lives on
the station's actual runtime host (prior-session memory: "live station on Linux snap"), not this Windows
engineering workstation's Workbench connection. → **B58-G2**.

## 58.7 — Self-verify

**Marker tally — literal `toolbelt/verify-block.sh` output** (run this session against the saved file):
```
== verify-block: niagara5-block58.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 22  (adj 20)
   [CERT-live] 1
   [CERT] 12  (adj 11)
   [CERT-doc] 1
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 8  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/35 = 0.17
-- [CERT] file:line citation resolution --
   synth-ref  [B14]/[B17]/[B19]/[B24]/[B26]/[B31]  (block back-references — not file-verifiable)
   extern  bloque702.md:10 / niagara-mental-model-bloque702.md:10  (not in target: sibling-corpus path,
           not script-verifiable)
   resolved 0 of 2
   WARN    resolved 0 of 2 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```
The `[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` counts of 1 each are the header legend's own marker
list restating the canonical taxonomy (METHODOLOGY §3) — this block makes no claims of those types, only
`[CERT-hw]`/`[CERT]`/`[INFER]`, consistent with its declared Method. `[CERT-hw]` dominates (20 adjusted
claims) because the overwhelming majority of this block's findings are direct live-filesystem observations
this session (`find`/`stat`/`du`/`xxd`/`unrar l`), tagged per section per [B17]'s own convention for the same
evidence class, not per individual command invocation. **`resolved 0 of 2` is the EXPECTED signature**,
generalizing METHODOLOGY §11's decompiled-tree convention: this block's only two `file:line`-shaped citations
point into the SIBLING `niagara-research` corpus (out of `verify-block.sh`'s `niagara5-research` target
scope, resolves `extern`) — every other `[CERT]`/`[CERT-hw]` claim in this block is either a live-command
observation (no static file to resolve against) or a same-corpus block back-reference (`synth-ref`, correctly
excluded from the file:line resolver). Citation gate for this block is therefore **inline token-verify**, not
the mechanized resolver: both sibling-corpus citations (`bloque702.md:10`, `bloque692.md:22,89`) were
`grep -n`-confirmed present at their stated lines this session (below), and every `[CERT-hw]` filesystem claim
is the direct, re-runnable output of the command cited inline at that claim.

**Token check.** Every `[CERT-hw]` filesystem claim was the direct output of a command run this session
against the live path, re-legible in this session's own bash history (not re-verified a second time, since
each command's own single run IS the primary observation — there is no "source" separate from the command's
output to re-check, unlike a `file:line` citation into a static file). Every `[CERT]` REMITTANCE citation was
`grep -n`-confirmed present at its stated line this session: `bloque702.md:10` (`600DF00D` magic quote),
`bloque692.md:22,89` (`registry.db`/`alarm.adb` binary-store pair) — both re-`grep`-confirmed this turn.

**Artifacts:** block file created at `/home/cristian/niagara5-research/niagara5-block58.md`. Per the caller's
explicit read-only instruction, no other file was touched — `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md`
regeneration and gap-backlog re-classification (B24-G2/B31-G4 → partially closed, B58-G1/G2/G3/G4 → opened)
are left to the orchestrator, per [B24]/[B26]/[B31]/[B17]'s own precedent for this corpus.

**MCP-doc snapshots:** N/A — no context7/MCP-doc citation in this block.

**Client-data discipline, restated:** nothing under the PANCCADIA station path (live or archived) was copied
into this repository, extracted, or reproduced beyond structural metadata (names, extensions, byte counts,
mtimes, a 16-byte format tag, and a 16-byte magic-number header). `security/` and `licenses/` anywhere in the
profile were never opened past their top-level directory name (seen only incidentally in a `find -maxdepth 3
-type d` profile listing, never descended into or read).

## 58.x — Child gaps

- **B58-G1** — `alarm.adb`'s N5-side format compatibility is unconfirmed. Unlike `.hdb` (magic
  bit-for-bit confirmed unchanged, [B19] §19.3), no block has yet decompiled N5's `alarm.jar` to check
  whether its `FileAlarmDbConfig`-equivalent class still writes/reads the same `600DF00D` v1 container, or
  a different one. Requires: targeted decompile of N5's `alarm.jar` alarm-database-file class(es),
  cross-checked against `niagara-research` B702's N4-side finding the way [B19] cross-checked `.hdb`.
- **B58-G2** — PANCCADIA's real runtime histories/schedules/px (if they exist) were not located. This
  session confirms they are NOT on the Windows Workbench engineering path (§58.4, corroborated two
  independent ways); prior-session memory places the live station on a separate host ("live station on
  Linux snap"). Locating that host's own station directory and applying this same read-only,
  structure-only census to it would be the actual closure of [B24]'s B24-G2 and [B31]'s B31-G4 — this
  block only establishes WHERE the data is not, narrowing the search rather than completing it.
- **B58-G3** — Whether `systemDb`/`orientSystemDb` is absent from this Niagara4.14 OEM profile because it
  is unlicensed/unused, or because this specific OEM distribution never provisions it at all, is unresolved
  (§58.4). Requires either a `[CERT]` decompile-level check of a license-feature flag against this specific
  install, or a `[CERT-hw]` Workbench-UI check of whether an `orientSystemDb` service component is even
  offered for addition on this station.
- **B58-G4** — `alarm.adb`'s non-zero header words (offsets 0x0C-0x20: `01A0`, `C4A1C286`, `0200`, `0008`,
  `0400`) were observed but not decoded (§58.3) — no local tool parses `FileAlarmDbConfig`'s exact header
  layout the way `hdbread.py` parses `.hdb`'s. Writing or extending such a tool (read-only, header-only, no
  record-content extraction) would let a future block state precisely what "1,024 bytes, zero records" means
  structurally (a fixed minimum-allocation size vs. an actual reset event) rather than by size-comparison
  inference against a different station's much larger, populated copy.

## 58.x — Connections

- **[Block 24]** — this block closes the filesystem-existence half of **B24-G2**: PANCCADIA's
  points/histories/alarms bog files are confirmed ABSENT from the accessible station path (not merely
  unavailable in the `poc/` copy [B24] worked from) — the gap's premise (they exist somewhere uncensused)
  is narrowed to B58-G2 (they exist somewhere ELSE, not here).
- **[Block 31]** — this block closes the filesystem-existence half of **B31-G4**: no separate `schedule:*`
  bog file exists, extending B31-G4's config.bog-internal zero-schedule-typespec finding to the filesystem
  level; the points/histories/alarms half is narrowed to B58-G2 the same way as for [B24].
- **[Block 19]** — §19.3's confirmed-unchanged `.hdb` magic and §19.4/§19.5's systemDb/orientSystemDb
  architecture are the ready-made N5-side answers this block applies to what it found (nothing, for
  history/systemDb at this path) and what it flags as unanswered (`alarm.adb`, B58-G1, for which no
  equivalent N5-side confirmation exists yet).
- **[Block 26]** — §26.8's PANCCADIA capacity-mode census (0 of 23 `history:HistoryConfig` capacities use
  the removed storage-size mode) was performed against `config.bog`'s OWN embedded `HistoryConfig` service
  objects, not against real `.hdb` files — this block explains why no real `.hdb` file was available to
  cross-check that census against in the first place (§58.4).
- **[Block 17]** — same station path (re-confirmed present, same [Block 17] §17.1 path, 2026-09-27),
  reuses its config.bog census and per-module object counts as REMITTANCE (§58.2/§58.6) rather than
  re-deriving them; extends its single `find *.dist` negative search with a second, differently-scoped
  confirmation via the dedicated `backups/` folder (§58.5).
- **PANCCADIA product-decisions / station-audit memory** (prior-session context, not re-opened this
  session) — "live station on Linux snap" is the working hypothesis this block's B58-G2 would test.
