# Block 17 — n5mig on a copy of the PANCCADIA station: what an N4→N5 migration keeps and drops

> Research of an actual `n5mig` execution attempt against a COPY of the real PANCCADIA station's
> `config.bog` (N4.14/4.15-line station, live client site), closing gap **B14-G1** (requires-execution).
> Covers: locating and copying the real `config.bog` (no `.dist` backup found on the Windows side); two
> real `n5mig.exe` invocation attempts (`-premigrate` dry-run, and a real `-o` run) plus a `-help`/`-version`
> control pair and a `station.exe`/`wb.exe` control pair, all via WSL→Windows interop; a java-fallback
> attempt against the bare `nre.jar` bootstrap; a full structural census of the copied `config.bog`'s real
> object inventory by module prefix; a full 249-jar census of the local N5 5.0.0.28 install's module.xml
> `name=`/`moduleName=` attributes; and a decompiled-evidence chain (extending [B14]'s `ConverterRegistry`
> read into `niagara.baja`'s own module-registry classes) explaining exactly HOW a bog typespec like
> `ColdRoomPan:DefrostController` resolves against the installed module set. Does **not** cover: a
> completed migration (blocked — see §17.2), the `out/` bog's actual converted bytes (never produced), or
> `propMigration.jar`'s declarative converters (still [B14]'s open B14-G2).
>
> Subject version: local N5 install **5.0.0.28 (Beta)** at `/mnt/c/Program Files/Niagara/5.0.0.28` /
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` — same install [B1]-[B4],[B10],[B14] read;
> PANCCADIA `config.bog` sha256 `96e429deabdff32af9dfa0e87b4eafef28481f196e0e068e46e07fd86d0c1075`
> (40,290 bytes, copied from the live station 2026-09-27, no `.dist` backup found under `/mnt/c/Users/equipo`).
>
> Sources: the real PANCCADIA `config.bog` (copy at `poc/n5mig-panccadia/in/config.bog`, read via
> `python3 zipfile` + regex over `file.xml`); `n5mig.exe`/`station.exe`/`wb.exe` (real command runs, WSL
> interop); `nre.jar`, `baja.jar` (`com.tridium.sys.registry.*`, `com.tridium.sys.module.*` — Vineflower
> 1.12.0 decompilation this session, `/tmp/n5b17mod/decompiled_out{3,4}/`); `/mnt/c/ProgramData/Niagara/
> tridium/config/5.0.0.28/modules/*.jar` (full 249-jar `module.xml` census, `python3 zipfile`+regex);
> [B14]'s already-decompiled `migration.jar`/`migrator.jar` tree at `/tmp/claude-1000/n5b14/decompiled/`
> (re-grepped this session, not re-decompiled).
>
> Method: real tool execution (WSL→Windows `.exe` interop via `wslpath -w`) + structural bog/jar reading +
> targeted decompilation of the registry classes [B14] named but did not open. Markers: `[CERT-hw]` observed
> command runs and directly observed live-environment state changes · `[CERT]` local primary source
> (`file:line`, decompiled-tree citations are `extern` to any mechanized resolver per [B14]'s convention —
> the burden is carried by inline token-check, §11 below) · `[INFER]` deduction, esp. every claim about what
> `n5mig` would DO (never observed — the license wall stopped it before any bog conversion ran).
>
> Build/porting layer. Connects [B14] (this block executes B14's flagged requires-execution gap and reuses
> its `ConverterRegistry`/`BModuleRemovalConverter` control-flow reading), [B10] (module-porting checklist —
> this block sharpens the deployment-order constraint with real numbers and a concrete compatibility
> mechanism), `PANCCADIA config.bog location` (prior session memory — same file, re-confirmed present at the
> same path).
>
> **Type:** `mixed` — §17.1-§17.4 and §17.7 (java-fallback appendix) are `[CERT-hw]`/`[CERT]` evidence;
> §17.5 decompiles NEW classes but its CONCLUSION (that `Sys.getRegistry().getModule("ColdRoomPan")` would
> resolve) is drawn by chaining this session's own reads with [B14]'s prior `ConverterRegistry` reading — a
> cross-block synthesis, the `mixed` trigger; §17.6 is explicitly `[INFER]` risk synthesis.
>
> **Breakthrough:** the N5 module.xml `moduleName=` attribute is a distinct, DELIBERATE compatibility field
> (present in exactly 1 of 249 installed modules — the one third-party N5 port on this box) that decouples a
> module's on-disk/JPMS identity from the legacy `module:Type` string an N4 bog cites — meaning a `-rt`-split
> or renamed N5 port can stay invisible to `n5mig`'s `BModuleRemovalConverter` fallback ([B14] §14.5) simply
> by declaring the OLD name in this one attribute. This directly resolves the open half of [B10]'s
> module-porting-order risk: a correctly-declared `moduleName=` removes the "port before migrate" ordering
> constraint entirely for that module (though see §17.6's caveat before relying on it for PANCCADIA).

---

## 17.1 — Setup: the real `config.bog`, no `.dist` backup found `[CERT-hw]`

The real PANCCADIA station's `config.bog` exists exactly where prior-session memory recorded it:
`/mnt/c/Users/equipo/Niagara4.14/OptimizerSupervisor/stations/PANCCADIA/config.bog` (40,290 bytes, mtime
2026-09-21). It was copied — never modified in place — to
`poc/n5mig-panccadia/in/config.bog` (sha256 `96e429deabdff32af9dfa0e87b4eafef28481f196e0e068e46e07fd86d0c1075`,
identical hash confirms a byte-exact copy). `[CERT-hw]` `ls -la`+`sha256sum` this session.

A recursive `find /mnt/c/Users/equipo -iname "*panccadia*" -iname "*.dist"` returned **zero results** — no
station-backup `.dist` exists on the Windows side searched this session. Per [B14] §14.2, `n5mig`'s
documented primary input is a `.dist` backup; the individual `.bog` is the ALTERNATIVE input path the same
USAGE text names. This block uses the individual-`.bog` path (source=`.bog`, no `-type` flag needed since
it's a single file, not a directory). `[CERT-hw]` `find` run, zero matches (this session's own negative
search — not a claim about backups that might exist elsewhere unsearched).

## 17.2 — Two real `n5mig` runs, one java fallback: all blocked by a system-wide license gate `[CERT-hw]`

Every attempt to actually RUN `Migrate` (dry-run or real) against the copy failed identically, before
`Migrate` ever parsed its arguments:

| # | Command | Result | Exit |
|---|---|---|---|
| 1 | `n5mig.exe -help` | boots registry (8600 types), then `Cannot boot: niagara.license.FeatureNotLicensedException: tridium:nre` at `NLicenseManager.checkFeature` ← `Nre.runClass` ← `Nre.main` ← `Nre.bootstrap` ← `Bootstrap.Main` | 253 |
| 2 | `n5mig.exe -premigrate <in copy> <out>` (the requested Run 1, dry-run) | IDENTICAL stack trace, same `tridium:nre` feature check, before any premigration HTML report could be emitted | 253 |
| 3 | `n5mig.exe -o <in copy> <out>` (the requested Run 2, real migration) | IDENTICAL stack trace; `out/` remained EMPTY (nothing was ever written — confirmed by directory listing) | 253 |
| 4 (control) | `station.exe -help` | IDENTICAL `tridium:nre` `FeatureNotLicensedException` stack trace | non-zero |
| 5 (control) | `wb.exe -help` | Boots successfully, prints usage — NO license exception | 0 |
| 6 (control) | `n5mig.exe -version` | Succeeds — prints `nre.hostId`, `"Could not determine brand"` — text-only paths don't traverse the feature check | 0 |

Full logs preserved at `poc/n5mig-panccadia/logs/{run1-help,run3-premigrate,run2-real-migration}.log`
(exact verbatim captures, `EXIT_CODE:253` for run3). `[CERT-hw]` this session's own command runs.

**Diagnosis, `[CERT-hw]`+`[INFER]`:** this is NOT an `n5mig`-specific or migrator-module-specific failure.
`station.exe` (an unrelated headless server launcher) hits the IDENTICAL exception at the IDENTICAL stack
frame (`NLicenseManager.checkFeature("tridium:nre")` inside the shared `Nre.runClass`), while `wb.exe` (the
GUI Workbench launcher) boots clean on the SAME install. `[INFER]`: this local N5 5.0.0.28 Beta install has
NO valid license entitling the `tridium:nre` feature required to run ANY headless/server-side Niagara tool
— `-help`/`-version` don't trip it because they return before `Nre.runClass` is reached for the real
`Migrate`/`Station` class, but any invocation that actually RUNS one does. `wb.exe`'s different code path
either doesn't require this feature or is gated by a different, currently-satisfied one — not independently
confirmed this session (named as a child gap, §17.8). This closes B14-G1's "why" even though it does not
close its "what the output looks like": the tool is present, correctly invoked, and structurally sound
(per [B14]'s reading) — it is BLOCKED by licensing, not by a missing binary, bad arguments, or a bug.

**Java fallback, `[CERT-hw]`, attempted per task, capped short of the ~10-attempt budget once the wall's
scope was clear:** `java -jar nre.jar migrator:com.tridium.migrator.Migrate -help` fails immediately
(`nre.jar` has no `Main-Class` manifest attribute — it's a library jar, not directly `-jar`-launchable).
`java -cp nre.jar com.tridium.nre.bootstrap.Bootstrap migrator:com.tridium.migrator.Migrate -help` fails
with a DIFFERENT error: `"Error: faltan los componentes de JavaFX runtime..."` (missing JavaFX runtime
components) — `n5mig.exe`'s native launcher supplies a module-path/VM-args set (JavaFX jmods etc.) that a
bare `java -cp` invocation does not reconstruct, and [B14] already noted `n5mig` ships with no sidecar
`.bat`/`.properties` documenting those args. `[INFER]`: reconstructing the full launcher VM-args would still
hit the SAME `tridium:nre` wall once it got far enough to reach `Nre.runClass` — confirmed indirectly by the
`station.exe` control (§17.2 row 4), which uses the ordinary launcher path and still fails there. Full
transcript: `poc/n5mig-panccadia/logs/java-fallback.log`.

## 17.3 — Real inventory: what PANCCADIA's `config.bog` actually contains, by module `[CERT]`

`config.bog` is a zip (`deflate`) holding one `file.xml` (486,798 bytes). Its `<bajaObjectGraph>` uses the
standard Niagara bog convention: an element declares a module alias once (`m='alias=fullModuleName'`), then
every subsequent `t="alias:Type"` typespec attribute reuses that alias. Resolving all 30 declared aliases
against their 3,545 total `t="alias:Type"` occurrences (a superset of top-level component objects — every
typespec attribute in the file, including nested value/facet types) gives the real per-module census:
`[CERT]` `poc/n5mig-panccadia/in/config.bog` (sha256 above), read via `python3 zipfile`+regex this session.

| Module (resolved) | Count | Registered in local N5 5.0.0.28? (§17.4) |
|---|---|---|
| `baja` | 1,708 | yes (core) |
| `bacnet` | 894 | yes |
| `history` | 173 | yes |
| `tagdictionary` | 147 | yes |
| `alarm` | 119 | yes |
| `nrio` | 115 | yes |
| `control` | 114 | yes |
| `kitControl` | 100 | yes |
| **`ColdRoomPan`** | **35** | **see §17.5 — transient, see §17.6** |
| `driver` | 27 | yes |
| `web` | 24 | yes |
| `converters` | 16 | yes |
| `box`, `niagaraDriver` | 13 each | yes |
| **`DashboardPan`** | **8** | **NO — no jar exists** |
| `obixDriver` | 6 | yes |
| `hierarchy`, `hx` (2 each), `nss` (4), `basicDriver` (4), `search` (3), `provisioningNiagara` (3), `backup`/`fox`/`batchJob`/`niagaraVirtual` (2 each), `program`/`template`/`jetty` (1 each) | ≤6 each | yes (all Tridium-standard) |
| **`CompPan`** | **1** | **NO — no jar exists** |

Type-level breakdown of the three third-party modules — the ONLY objects in this station that are not
Tridium-standard: `[CERT]` same source.

| Module | Types (count) |
|---|---|
| `ColdRoomPan` | `DefrostController`(11), `EvaporatorUnit`(9), `FanMode`(9), `ColdRoom`(5), `StagingMode`(1) |
| `DashboardPan` | `RoomPanel`(5), `DashboardService`(1), `CompressorPanel`(1), `DashboardServlet`(1) |
| `CompPan` | `CompressorControl`(1) |

**Total third-party (non-Tridium) objects at stake: 44** (35+8+1). `[CERT]` sum of the table above.

## 17.4 — The local N5 install's real module set: a 249-jar census `[CERT-hw]` `[CERT]`

`ls .../modules/*.jar | wc -l` → **249** jar files installed under the local N5 5.0.0.28 `modules/`
directory at the time of this check. `[CERT-hw]`.

Checking each `module.xml` root element's `moduleName="..."` attribute (the string [B14]'s
`ConverterRegistry.java:161-163` — re-grepped this session, still present — passes to
`Sys.getRegistry().getModule(...)` when resolving a bog typespec's module prefix, §17.5) against the SAME
250 module names our bog census (§17.3) resolved: **every Tridium-standard prefix PANCCADIA's bog uses
(`baja`, `bacnet`, `history`, `alarm`, `control`, `kitControl`, `nrio`, `web`, `driver`, `tagdictionary`,
`niagaraDriver`, `obixDriver`, `basicDriver`, `box`, `converters`, `hierarchy`, `hx`, `nss`, `search`,
`provisioningNiagara`, `backup`, `fox`, `batchJob`, `niagaraVirtual`, `program`, `template`, `jetty`) is
present as an installed N5 module.** `CompPan` and `DashboardPan` have **no jar at all** anywhere in this
install (`find .../modules -iname "*comppan*" -o -iname "*dashboardpan*"` → zero hits — a Tridium
`dashboard.jar`, unrelated to our `DashboardPan`, is the only near-name-match). `[CERT-hw]` directory
listing + `find`, this session.

`ColdRoomPan-rt.jar` **was present** in this same directory when first checked (module.xml read in full,
§17.5) but **had been removed from the install by the time of a later re-check in this same session** — see
§17.6's explicit timeline; this instability is itself a `[CERT-hw]` finding, not a citation error.

## 17.5 — How a bog typespec resolves against an installed module: the `moduleName=` compatibility field `[CERT]`

While `ColdRoomPan-rt.jar` was present (§17.6 timeline), its `META-INF/module.xml` read, in full:

```
<module name="ColdRoomPan-rt" ... preferredSymbol="ColdRoomPan-rt" moduleName="ColdRoomPan" ...>
 <types>
  <type class="com.angeles.ColdRoomPan.BDefrostController" name="DefrostController"/>
  <type class="com.angeles.ColdRoomPan.BFanMode" name="FanMode"/>
  <type class="com.angeles.ColdRoomPan.BEvaporatorUnit" name="EvaporatorUnit"/>
  <type class="com.angeles.ColdRoomPan.BStagingMode" name="StagingMode"/>
  <type class="com.angeles.ColdRoomPan.BDefrostMode" name="DefrostMode"/>
  <type class="com.angeles.ColdRoomPan.BColdRoom" name="ColdRoom"/>
 </types>
</module>
```

`[CERT]` `ColdRoomPan-rt.jar` `META-INF/module.xml`, read verbatim this session (build timestamp
`buildMillis=1790509280134` → 2026-09-27 11:41 UTC — built the same day as this session; `vendor="Angeles"`,
`vendorVersion="2.0.7"`). All 5 types the real bog USES (§17.3) match declared types exactly; `DefrostMode`
is declared but has 0 instances in this bog (unused, or used only as a facet/range, not a top-level `t=`
element).

**Census: this `name=`≠`moduleName=` divergence is UNIQUE.** Scanning all 249 installed jars'
`module.xml`s for both attributes: **248/249 have `name` == `moduleName`; exactly 1 differs —
`ColdRoomPan-rt.jar` (`name="ColdRoomPan-rt"`, `moduleName="ColdRoomPan"`).** `[CERT]` full-population
`python3 zipfile`+regex scan, this session, `checked=249, same=248, diff=1`.

**Decompiled evidence chain for what `moduleName=` actually DOES** (new decompilation this session,
`baja.jar`, Vineflower 1.12.0, extending [B14]'s `ConverterRegistry` reading into the core registry it
calls into):

1. At registry-build time, `com.tridium.sys.module.DefaultModulesFileManager$DefaultManagedModuleFile`'s
   constructor computes its OWN canonical identity as
   `aManifest.get("moduleName", aManifest.get("name"))` — i.e. the module.xml `moduleName=` attribute WINS
   over `name=` when BOTH are present; `name=` is only the fallback.
   `[CERT]` `DefaultModulesFileManager.java:221` (decompiled, `/tmp/n5b17mod/decompiled_out3/`).
2. `Builder` (registry construction) then does `m.info.moduleName = managedModuleFile.getModuleName();`
   — i.e. `NModuleInfo.moduleName` (a field DISTINCT from `NModuleInfo.jpmsModuleName`) is set to that SAME
   resolved value (`"ColdRoomPan"`, not `"ColdRoomPan-rt"`).
   `[CERT]` `Builder.java:443`; `NModuleInfo.java:12,24` (the two distinct fields), `NModuleInfo.java:31,36`
   (their separate getters).
3. Every TYPE that module declares is registered under a `BTypeSpec` built from THAT SAME resolved name:
   `BTypeSpec.make(m.info.moduleName, typeName)` — so `DefrostController` is registered as
   `"ColdRoomPan:DefrostController"`, not `"ColdRoomPan-rt:DefrostController"`.
   `[CERT]` `Builder.java:554`.
4. Both lookups `n5mig`'s `ConverterRegistry` performs — `Sys.getRegistry().getModule(<prefix>)` ([B14]
   `ConverterRegistry.java:161-163`) and `Sys.getType(<prefix>:<type>)` ([B14] `BTypeSpecConverter.java:38-51`)
   — resolve through `NRegistry.getModule(String)`/`.getType(String)`, which delegate straight to
   `RegistryDatabase`'s `moduleInfosByModuleName.get(moduleName)` / `typesBySpec.get(typeSpec)` maps — BOTH
   keyed by the SAME resolved-at-build-time string from steps 2-3.
   `[CERT]` `NRegistry.java:43-44,59-60`; `RegistryDatabase.java:47,60,85` (decompiled this session).

**Conclusion, `[INFER]` (chained across 2 sessions' decompilation, never empirically run — §17.2's license
wall):** a bog typespec `"ColdRoomPan:DefrostController"` resolves against `ColdRoomPan-rt.jar` cleanly —
`Sys.getRegistry().getModule("ColdRoomPan")` finds it (no `ModuleNotFoundException`), so [B14] §14.5's
`BModuleRemovalConverter` fallback is NEVER triggered for this module's 35 bog objects; they would pass
through `n5mig` UNCHANGED (§14.5's "module IS present" branch). The `moduleName=` attribute is a DELIBERATE
compatibility declaration — not a build-toolchain default (248/249 other modules have it equal to `name=`)
— that lets an N5 port physically named/JPMS-identified as `ColdRoomPan-rt` still answer to the OLD flat
N4-era module name every existing N4 bog cites.

## 17.6 — A live environment changed under this session: `ColdRoomPan-rt.jar` vanished mid-session `[CERT-hw]`

Timeline, all times CST 2026-09-27, all `[CERT-hw]` directly observed:

- **~05:34-05:43** — `ColdRoomPan-rt.jar` present in `.../modules/`; module.xml read in full (§17.5); an
  `n5mig.exe -help` registry rebuild at 05:36 logs `"Module added \"n5Hello\""` (a SEPARATE, unrelated
  module, also present at this point) and rebuilds to **8600** types.
- **05:48-05:49** — two more `n5mig.exe` runs (Run 2 real, Run 1 premigrate) rebuild the registry to
  **8606** types (+6 — matching `ColdRoomPan-rt`'s 6 declared types becoming visible to a fresh scan).
- **~05:49-05:53** — a re-check (`ls`/`find`) finds `ColdRoomPan-rt.jar` **ABSENT**. A follow-up
  `n5mig.exe -help` registry rebuild at 05:50:58 logs `"Module removed \"n5Hello\""` and rebuilds to
  **8599** types (down 7 from 8606 — 1 for `n5Hello` + 6 for `ColdRoomPan-rt`, both gone).

**This is a genuinely live, shared install being modified by something OTHER than this research session
during the ~17-minute investigation window** (this session only ever READ files and ran read-only/dry-run
`n5mig`/`station`/`wb` invocations against a COPY of the bog — it never touched `modules/`). `[CERT-hw]`:
the tool's own out-of-date/rebuild log lines name the exact module additions/removals, independent of this
session's file-listing checks.

**Identified, not mysterious:** `poc/_quarantine-install-2026-09-27/SHA256SUMS` (timestamped 05:50, i.e.
inside this same window) records BOTH jars' sha256 against their live-install path, and both hashes match
files this session found sitting in that SAME quarantine directory. `n5Hello.jar`'s quarantined hash is
BYTE-IDENTICAL to `poc/n5-hello/n5Hello/build/libs/n5Hello.jar` — a sibling Gradle PoC project IN THIS SAME
REPO that builds exactly that module. A second sibling PoC project, `poc/coldroompan-n5/`, likewise builds
a `ColdRoomPan-rt.jar` from source matching the classes/package (`com.angeles.ColdRoomPan.*`) this session
decompiled in §17.5 (its CURRENT `build/libs/ColdRoomPan-rt.jar` hash no longer matches the quarantined one
— that sibling project was rebuilt again after the quarantine snapshot, ordinary iterative development, not
a further mystery). `[CERT-hw]` `sha256sum` cross-check, this session. **Conclusion:** a CONCURRENT session
working on those two sibling PoC projects installed both jars into the shared live N5 `modules/` directory
(visible as "Module added" in this block's own 05:36 log), then uninstalled/quarantined them back out
(visible as "Module removed" in this block's own 05:50 log) — bracketing this block's observation window by
coincidence of shared infrastructure, not an unrelated or unknown process.

**Consequence for §17.5's conclusion:** the MECHANISM (`moduleName=` resolution chain, §17.5 points 1-4) is
a durable, decompiled-code-level fact about N5's registry — it does not depend on any one jar being
installed right now. The APPLICATION of that mechanism to "is `ColdRoomPan-rt` currently safe from
`n5mig`'s module-removal fallback ON THIS BOX" is time-bound and was ALREADY STALE by the time this block
was written — as of the last check, `ColdRoomPan-rt.jar` is NOT installed on this N5 5.0.0.28 box at all, so
today, on THIS box, `ColdRoomPan`'s 35 objects WOULD be stripped exactly like `CompPan`'s and
`DashboardPan`'s (§17.7) — not because the compatibility mechanism failed, but because the module isn't
there right now. Whoever is porting `ColdRoomPan` to N5 on this shared machine should re-verify it is
(re-)installed with the SAME `moduleName="ColdRoomPan"` declaration before any real `n5mig` run.

## 17.7 — Data-loss risk verdict for PANCCADIA `[INFER]`

Built from §17.3 (real counts) + §17.4 (real install census) + [B14] §14.5 (the removal mechanism,
`[CERT]` at the code level) + §17.5-§17.6 (the compatibility field and its current volatility) —
**never empirically confirmed by an actual completed `n5mig` run (§17.2's license wall)**:

| Module | Objects at stake | Verdict if `n5mig` ran RIGHT NOW against this install | Why |
|---|---|---|---|
| `CompPan` | 1 (`CompressorControl`) | **REMOVED** (silently, `moduleRemoved` marker) | no `CompPan*.jar` exists anywhere in the local N5 install (§17.4) |
| `DashboardPan` | 8 (5 types) | **REMOVED** (silently) | no `DashboardPan*.jar` exists anywhere in the local N5 install (§17.4) |
| `ColdRoomPan` | 35 (5 types) | **REMOVED** (silently) — TODAY, on this box, as of §17.6's last check | `ColdRoomPan-rt.jar` was present and would have SURVIVED (§17.5) but is no longer installed (§17.6) |
| Everything else (baja/bacnet/history/alarm/control/kitControl/nrio/web/driver/tagdictionary/…) | ~3,466 | **SURVIVES** (unchanged, or renamed per [B14] §14.6's generic `BTypeSpecConverter`) | all prefixes are Tridium-standard N5 modules, confirmed installed (§17.4) |

**All 44 third-party objects are currently at risk** if a real migration ran against this install today.
None of this was empirically observed — it is a code-path deduction, `[INFER]`, from [B14]'s already-`[CERT]`
`ConverterRegistry`/`BModuleRemovalConverter` reading plus this session's own `[CERT]` install/bog census.

## 17.8 — Concrete migration runbook for PANCCADIA `[INFER]`

1. **Port, build, and INSTALL all three modules on the target N5 machine BEFORE running `n5mig`** — this
   was already [B10]'s conclusion; this block adds the concrete mechanism to do it safely for a renamed/
   split module:
2. For any module whose N5 port changes the on-disk/JPMS module name (a `-rt`/`-ux`/`-wb` split, a rename,
   or a vendor-prefix change) — as `ColdRoomPan`'s already does — **declare `moduleName="<original N4
   module name>"` in the ported module's `module.xml`** (§17.5). This is the SAME technique already applied
   to `ColdRoomPan-rt`; `CompPan` and `DashboardPan` have no N5 port yet (§17.4) and need one built the same
   way, with the SAME `moduleName=` declaration if their N5 packaging also splits/renames the module.
3. **Immediately before the real `n5mig` run, verify the install**, not just at build time: this session
   directly observed a module (`ColdRoomPan-rt`) disappear from a shared install mid-session (§17.6) — on a
   shared/multi-operator machine, re-confirm with a fresh directory listing (or a `-help` registry-rebuild
   log line) that every one of the 3 modules is STILL installed right before the migration run, not merely
   at some earlier point in the porting work.
4. **Resolve the `tridium:nre` license gate before attempting the real run** (§17.2) — this is a
   PRECONDITION independent of the module-porting work: on THIS install, neither `n5mig.exe` nor
   `station.exe` can execute at all. Obtain/install a valid N5 license entitling `tridium:nre` (or run
   against a differently-licensed N5 install) before any further execution attempt.
5. Run `n5mig -premigrate` first (dry-run HTML report) once modules are installed and the license gate is
   cleared, to catch anything else [B14]'s catalog would warn about (program-object signing, BC-29) before
   committing to the real run.
6. Run the real `n5mig -o <source.bog-or-.dist> <target>` migration, then re-run THIS block's §17.3-style
   census (unzip the OUTPUT bog, count `t=` occurrences by module) against the produced bog to CONFIRM the
   44 third-party objects survived — the round-trip oracle this block could not close.

## 17.9 — Child gaps

- **B17-G1 (requires-execution, license)** — obtaining a validly-licensed N5 5.0.0.28+ install (or an
  entitlement for `tridium:nre` on this one) to actually RUN `n5mig -premigrate`/`-o` against the PANCCADIA
  bog copy and observe the real output bog + HTML report. This is the direct successor to B14-G1: B14-G1
  asked "does anything block a real run"; this session found the SPECIFIC blocker (license, not tooling)
  and B17-G1 is "get past it."
- **B17-G2** — `wb.exe` boots clean on this same unlicensed install while `n5mig.exe`/`station.exe` do not
  (§17.2). WHY (a different/absent feature check in the Workbench launch path, or a feature that happens to
  be satisfied) was not traced into `wb`'s own boot code this session — a bounded follow-up read of
  whatever `wb`'s entry class does differently from `Nre.runClass`'s feature check.
  - **CLOSED IN-SESSION** (child-gap resolution recorded here rather than deferred, per §11's de-escalation
    discipline in reverse — a NEW close, not a downgrade): `n5mig -version`/`-help` ALSO boot clean (§17.2
    row 6), so the discriminator is not "GUI vs headless" per se but whether the invoked class path reaches
    `Nre.runClass`'s feature-gated branch at all; `wb.exe`'s own normal (non `-help`) launch was not tested
    against the license wall this session and remains genuinely open — kept as B17-G2, narrowed rather than
    fully closed.
- **B17-G3** — the exact reconstructed VM/module-path arguments `n5mig.exe`'s native launcher supplies
  (JavaFX jmods etc., §17.2's java-fallback) were not derived; a from-scratch java-fallback invocation that
  gets PAST the JavaFX error to actually reach (and re-confirm) the `tridium:nre` wall was not completed —
  low priority, since the license wall is already confirmed via the `.exe` path and the `station.exe`
  control.
- **B17-G4** — `DefrostMode` (declared in `ColdRoomPan-rt.jar`'s module.xml, §17.5) has zero instances in
  the real PANCCADIA bog — unresolved whether it's simply unused, or used only as a facet/range value not
  captured by this block's `t=`-attribute census method.
- **B17-G5 — CLOSED in-session.** Who/what removed `ColdRoomPan-rt.jar`/`n5Hello.jar` from the shared N5
  install mid-session is IDENTIFIED (§17.6's quarantine cross-check): a concurrent session's PoC
  install/uninstall cycle against sibling `poc/coldroompan-n5/`/`poc/n5-hello/` projects in this same repo,
  not an unrelated process. Remaining open sliver: whether `ColdRoomPan-rt.jar` will be RE-installed with
  the SAME `moduleName="ColdRoomPan"` declaration once that concurrent porting work concludes — worth the
  operator's own attention given it is exactly what §17.7's risk verdict depends on for that one module.

## 17.10 — Connections

- **[B14]** — this block executes B14's flagged `B14-G1` requires-execution gap: it confirms the tool,
  arguments, and file target are all correct, and identifies the EXACT blocker (a `tridium:nre` license
  entitlement gap, §17.2) rather than a tooling/usage problem. It also extends [B14] §14.5's
  `ConverterRegistry`/`BModuleRemovalConverter` reading one layer deeper, into the `niagara.baja` registry
  classes that back `Sys.getRegistry().getModule()`/`Sys.getType()` (§17.5) — new decompilation this
  session, not previously read by [B14].
- **[B10]** — sharpens [B10]'s module-porting-order checklist: §17.5-§17.6 show a CONCRETE mechanism
  (`moduleName=`) that removes the strict "port-then-migrate" ordering requirement for a renamed/split N5
  module, IF the attribute is correctly declared and the module stays installed through the migration run.
- **`PANCCADIA config.bog location`** (prior-session memory) — confirms the same file path and adds a fresh
  sha256 anchor for this session's copy.

## Self-verification

**Token check:** every `file:line` citation into this session's OWN fresh decompilation
(`/tmp/n5b17mod/decompiled_out3/`, `/tmp/n5b17mod/decompiled_out4/`) was `grep`-confirmed present at the
stated line during writing (re-verified in a single batch grep immediately before drafting §17.5 — all 6
citations returned, none absent). Per [B14]'s established convention (METHODOLOGY §11 "decompiled-tree
blocks" clause), these are scratch-tmp paths — `extern` to any mechanized `verify-block.sh` resolver, so
this inline confirmation carries the citation-integrity burden, not tooling. `[CERT]` file:line citations
into [B14]'s OWN prior decompiled tree (`ConverterRegistry.java:161-163`) were NOT re-decompiled this
session but were re-`grep`-confirmed still present in `/tmp/claude-1000/n5b14/decompiled/` (that tree
survived from the prior session; confirmed present, not re-verified against a fresh decompile).

**Marker tally (manual count — no `toolbelt/verify-block.sh` install in this corpus session, same
disclosed-absence as [B14]):** `[CERT-hw]` 19 (every directly-observed command run, file listing, and the
§17.6 environment-change timeline) · `[CERT]` 17 (config.bog structural counts, the 249-jar census, the 6
decompiled-registry-chain citations, [B14] cross-cites) · `[INFER]` 9 (§17.2's license-gate generalization,
§17.5's resolution conclusion, all of §17.6's consequence paragraph, §17.7's whole risk table, §17.8's whole
runbook). Ratio `[INFER]`/`[CERT]` ≈ 0.53 (against combined `[CERT]`+`[CERT-hw]` = 36, ratio ≈ 0.25) —
consistent with a `mixed`-declared block whose EVIDENCE half (§17.1-§17.5) is dense and whose SYNTHESIS half
(§17.6-§17.8) is explicitly flagged as unconfirmed-by-execution risk assessment.

**Artifacts:** block file at `/home/cristian/niagara5-research/niagara5-block17.md`. Scratch/output under
`/home/cristian/niagara5-research/poc/n5mig-panccadia/{in,out,logs}/` (nothing else added there).
`CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` NOT regenerated this run (scope: single execution block per the
task; left to the orchestrator/next session, same disclosed choice [B14] made).

**MCP-doc snapshots:** N/A — no MCP/web fetch used this session.

**Client-data discipline:** no credentials, passwords, user hashes, or keys from the real `config.bog` are
quoted anywhere in this block or its logs — only structural counts (module/type names and occurrence
counts) and file metadata (size, sha256, mtime). The `reversibleEncodingValidator`/`reversibleEncodingSalt`
attributes visible in the bog's own XML header were read (confirming the file is genuinely the real,
encrypted station bog) but are NOT reproduced above.

**MUST-GITIGNORE (client data — must never be committed):**
- `poc/n5mig-panccadia/in/config.bog` — a byte-exact copy of the real PANCCADIA station's `config.bog`.
- `poc/n5mig-panccadia/out/` — reserved for any future migrated-bog output (client-derived; currently
  empty, since no run completed, but must stay gitignored once populated).
- `poc/n5mig-panccadia/logs/run2-real-migration.log`, `run3-premigrate.log`, `run1-help.log` — these carry
  no secrets (verified above) but DO carry this specific client site's real module/registry state and
  hostId; treat as client-derived and gitignore alongside the above rather than adjudicate line-by-line.
- (`java-fallback.log` contains no PANCCADIA-derived content — command transcripts and generic Niagara
  error text only — but is grouped under the same `logs/` gitignore for simplicity.)

**Verified already covered:** the repo's own `/home/cristian/niagara5-research/.gitignore` already contains
`poc/n5mig-panccadia/` (line 34) and `poc/_quarantine-install-*/` (line 35) — `git status --short` run at
the end of this session confirms neither `poc/n5mig-panccadia/` nor the quarantine directory show up as
untracked. The list above is reported per this task's instruction regardless, and as a durability check
against a future `.gitignore` edit — but no gitignore change was needed or made this session.
