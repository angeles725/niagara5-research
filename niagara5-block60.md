# Block 60 — N5 kit lint facts: Flags, profile splits, version constants and dependency counts

> Research closing 5 named child gaps [Block 51] left open (**B51-G2, B51-G5, B51-G3, B51-G4, B51-G7**):
> whether `niagara.sys.Flags` is confirmed unchanged from N4's `javax.baja.sys.Flags` (constant names AND
> values), and which of the kit's Flags-referencing lints need a code change as a result (B51-G2); whether
> ANY working N5 PoC or the devkit's own wizard template still uses a per-profile (`rt`/`ux`/`wb`) Gradle
> split (B51-G5); the exact bytecode-major constant `lint-bundled-jar-class-version.sh` checks against
> (B51-G3); whether `rc-scan.sh`/`bog-audit.sh`'s `-rt|-ux|-wb` grep hits are structural (path-glob/profile
> matching) or incidental (prose) (B51-G4); and a direct measurement of explicit `module.xml
> <dependency>` counts, N4 vs N5, for the modules common to both a real N4 install and the N5 5.0.0.28
> install (B51-G7). Covers: full reads of `niagara.sys.Flags`/`javax.baja.sys.Flags` side by side; a
> full-corpus grep of the kit's Flags-referencing lint scripts, classified line-by-line as
> works/needs-change/obsolete; a full read of `lint-bundled-jar-class-version.sh` (67 lines) and of
> `rc-scan.sh` (143 lines) + `bog-audit.sh` (889 lines); a fresh, script-computed dependency-count
> comparison across 229 module families common to a real Honeywell N4.14.0.162 install (1013 jars) and the
> N5 5.0.0.28 install (247 jars), at two granularities (raw union vs. part-suffix-collapsed), with a named
> confound and a refinement of [Block 51] §51.6's own comparative claim. Does NOT cover: `lint-wb-threading.sh`
> (B51-G6, JavaFX-vs-Swing — untouched here, out of this task's named scope); re-deriving
> `Version.strip(N)`'s exact algorithm (a genuinely new tension this session's dependency-count spot-check
> surfaced, named as a fresh child gap rather than resolved); running any of the 33 lint scripts against a
> live N5-ported module tree (still no such tree with a full lint sweep exists anywhere in this corpus).
>
> Subject version: **N4 kit** — `build-n4-module-kit` at
> `/home/cristian/modulos_niagara_n4/niagara-tools/build-n4-module-kit`, `HEAD` `ea21c38`
> (2026-09-20 23:01:48 -0600 last commit touching the 3 scripts read in full this session),
> `BUILD-STATE.md` mtime 2026-09-27 04:43 — read-only, not modified. Kit ships **33** `lint-*.sh` scripts
> as of this session's own `find` (not the 37 [Block 51] counted; not re-investigated — the kit is a live,
> actively-committed target and script count drift between sessions is expected, not a contradiction to
> chase). **N4 dependency side** — Honeywell `OptimizerSupervisor-N4.14.0.162` distribution at
> `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules` (1013 jars) — an OEM build, NOT vanilla
> Tridium N4 (confound, named explicitly in §60.6). **N5 side** — Niagara `5.0.0.28` install at
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` (247 jars) + the 4 working PoC trees under
> `/home/cristian/niagara5-research/poc/` (`n5-hello`, `coldroompan-n5`/`coldroompan-n5-ha`, `comppan-n5`,
> `dashboardpan-n5` — all previously built `BUILD SUCCESSFUL`, per [Block 9]/[Block 16]/[Block 28], read
> again this session for their CURRENT on-disk `.gradle.kts` shape) + the devkit's own Velocity wizard
> templates, cached from [Block 36]'s decompile session at `/tmp/claude-1000/n5b36/templates-vf/gradle/`.
>
> Sources:
> - `/home/cristian/niagara5-research/organized/baja/vineflower/niagara/sys/Flags.java` (whole 320-line
>   file, full read) vs.
>   `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/sys/Flags.java` (first 70
>   lines read — the full constant table + `FLAGS[]` array, where every byte-level difference would have
>   to live).
> - `build-n4-module-kit/toolbelt/lint-config-sanity.sh`, `lint-persist-hot-write.sh`,
>   `lint-write-path.sh`, `lint-ext-writable-shape.sh`, `lint-changed-hot-write.sh` — targeted `grep -n`
>   read of every `OPERATOR`/`TRANSIENT` match this session. `lint-structure.sh` (362 lines, L1/L3/L11
>   re-read with line numbers). `verify-module.sh` line 546 (cross-module-type whitelist, re-read for its
>   exact `case` pattern).
> - `build-n4-module-kit/toolbelt/lint-bundled-jar-class-version.sh` (whole 67-line file, full read).
> - `build-n4-module-kit/toolbelt/rc-scan.sh` (whole 143-line file, full read),
>   `build-n4-module-kit/toolbelt/bog-audit.sh` (header + `--source-dir`/`SRC_DIR` handling, `grep -n`
>   targeted read of every `-rt|-ux|-wb`-token line and every `SRC_DIR`/`os.walk` line this session).
> - `poc/dashboardpan-n5/settings.gradle.kts` (whole file), `poc/dashboardpan-n5/DashboardPan-rt/DashboardPan-rt.gradle.kts`,
>   `poc/coldroompan-n5-ha/ColdRoomPan-rt/ColdRoomPan-rt.gradle.kts`, `poc/comppan-n5/CompPan-rt/CompPan-rt.gradle.kts`,
>   `poc/n5-hello/n5Hello/n5Hello.gradle.kts` — all whole files, full read this session; plus a `find
>   -maxdepth 1 -type d` of all 4 PoC roots to confirm project-folder count.
> - `/tmp/claude-1000/n5b36/templates-vf/gradle/module/module.gradle.kts.vm` (whole file),
>   `/tmp/claude-1000/n5b36/templates-vf/gradle/includes/niagara/modulePlugins.vm` (whole file),
>   `/tmp/claude-1000/n5b36/templates-vf/gradle/settings.gradle.kts.vm` (first 40 lines) — devkit's own
>   Velocity wizard templates, cached from [Block 36]'s `n-templates-5.0.54.9.2.jar` extraction, re-read
>   this session (not re-extracted).
> - `/tmp/claude-1000/n5b2/vf-out/com/tridium/gradle/plugins/module/util/ModuleXml.java` lines 60-90,
>   140-160, 370-400 — same cached decompiled tree [Block 2]/[Block 51] used, re-read this session
>   specifically for `getIgnoreRuntimeProfileCheck()`/`getDependencyVersionLimit()`'s declaration sites
>   (`grep -rn` across both `n5b2` and `n5b36` decompile caches confirmed the CONSUMING logic for
>   `ignoreRuntimeProfileCheck` is not present in either cached fragment — named child gap B60-G1).
> - `/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/*.jar!META-INF/module.xml` (1013 jars,
>   scripted read via a fresh Python `zipfile`/`re` scan this session) and
>   `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar!META-INF/module.xml` (247 jars, same
>   scan) — plus hand spot-checks of `kitControl-{rt,ux,wb}.jar!META-INF/module.xml` (N4) and
>   `kitControl.jar`/`alarm.jar`/`baja.jar`/`bajaui.jar!META-INF/module.xml` (N5) to validate the script's
>   regex and the family-collapse logic.
>
> Method: direct `Read`/`grep` of every kit script and PoC file named above (no decompilation needed on
> the N4-kit or PoC side — all plain bash/awk/Kotlin-DSL source); side-by-side full read of the two
> already-decompiled `Flags.java` files (no re-decompilation, both cached from prior sessions'
> Vineflower runs); a purpose-written, single-use Python script (`/tmp` scratchpad, not preserved in the
> kit or corpus) walking both module install directories, opening every jar's `META-INF/module.xml`,
> regex-extracting `<dependency name="...">` entries, and comparing by module family
> (`moduleName`-equivalent, derived by stripping the `-rt|-ux|-wb|-wh|-se|doc` part suffix — confirmed
> this session to match the `<module moduleName="...">` attribute the files themselves already declare,
> `kitControl-ux.jar!META-INF/module.xml`).
> Markers (METHODOLOGY §3): `[CERT]` local primary source (`file:line` or `jar!path`) · `[CERT-hw]` this
> session's own live script-run output (the dependency-count Python scan) · `[INFER]` deduction ·
> REMIT = cited from a prior corpus block, not reopened this session.
>
> N5 build-toolchain layer, direct-evidence focus (closes gaps [Block 51] left as `[INFER]` or fully
> unread). Connects [Block 51] (all 5 gaps closed or substantially narrowed here), [Block 2]/[Block 9]
> (`ModuleXml.java`/devkit-template re-reads), [Block 16]/[Block 28] (the 3 real PoC `.gradle.kts` files
> re-read for §60.3).
>
> **Type:** mixed — §60.1-§60.5 are direct evidence reads (kit scripts, decompiled sources, PoC files);
> §60.6 is a fresh `[CERT-hw]` measurement (script output) plus `[INFER]` interpretation of what the
> measured pattern means, explicitly flagged as such.
>
> **Breakthrough:** none of the 5 gaps required new decompilation — every one closes from files this
> corpus already had cached or that were trivially reachable read-only. The single most consequential
> finding is negative: B51-G7's own premise ("N5 shows fewer explicit dependencies than N4") does **not**
> hold in aggregate once dependency TARGET names are collapsed by part-suffix the same way SOURCE names
> are — the raw, uncollapsed comparison's apparent -5.7 mean delta is shown here to be substantially a
> mechanical artifact of N4's 3-way part split, not evidence of a narrower N5 classpath (§60.6).

---

## 60.1 — B51-G2 (Flags identity) closed: `niagara.sys.Flags` is byte-identical to `javax.baja.sys.Flags` except for 4 import-path renames `[CERT]`

Full 320-line read of
`/home/cristian/niagara5-research/organized/baja/vineflower/niagara/sys/Flags.java` against a 70-line read
of `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/sys/Flags.java` (the header +
constant table + `FLAGS[]` symbol array — the section where any renumbering or renaming would have to
appear). Every constant name AND every literal value is **identical**:

| Constant | N4 value (`javax.baja.sys.Flags`) | N5 value (`niagara.sys.Flags`) | Citation |
|---|---|---|---|
| `READONLY` | `1` | `1` | N4 `Flags.java:9` / N5 `Flags.java:9` |
| `TRANSIENT` | `2` | `2` | `:10` / `:10` |
| `HIDDEN` | `4` | `4` | `:11` / `:11` |
| `SUMMARY` | `8` | `8` | `:12` / `:12` |
| `ASYNC` | `16` | `16` | `:13` / `:13` |
| `NO_RUN` | `32` | `32` | `:14` / `:14` |
| `DEFAULT_ON_CLONE` | `64` | `64` | `:15` / `:15` |
| `CONFIRM_REQUIRED` | `128` | `128` | `:16` / `:16` |
| `OPERATOR` | `256` | `256` | `:17` / `:17` |
| `EXECUTE_ON_CHANGE` | `512` | `512` | `:18` / `:18` |
| `FAN_IN` | `1024` | `1024` | `:19` / `:19` |
| `NO_AUDIT` | `2048` | `2048` | `:20` / `:20` |
| `COMPOSITE` | `4096` | `4096` | `:21` / `:21` |
| `REMOVE_ON_CLONE` | `8192` | `8192` | `:22` / `:22` |
| `METADATA` | `16384` | `16384` | `:23` / `:23` |
| `LINK_TARGET` | `32768` | `32768` | `:24` / `:24` |
| `NON_CRITICAL` | `65536` | `65536` | `:25` / `:25` |
| `USER_DEFINED_1..4` | `268435456`/`536870912`/`1073741824`/`Integer.MIN_VALUE` | same | `:26-29` / `:26-29` |
| Symbol table (`r`/`t`/`h`/`s`/`a`/`n`/`d`/`c`/`o`/`x`/`f`/`A`/`p`/`R`/`m`/`N`/`L`/`1`/`2`/`3`/`4`) | identical 21-entry `FLAGS[]` array, same masks/symbols/names | identical | `:30-52` / `:30-52` |

The **only** delta across the entire class is the package/import block: `javax.baja.sys` →
`niagara.sys`, `javax.baja.nre.util.IntHashMap` → `niagara.nre.util.IntHashMap`,
`javax.baja.sync.Transaction` → `niagara.sync.Transaction`, `javax.baja.util.Lexicon` →
`niagara.util.Lexicon` (both files' lines 1-6). Every method body (`has`/`hasAny`/`hasAll`/`add`/`remove`/
`isTransient`/`isOperator`/`encodeToString`/`decodeFromString`/`toDisplayString`/`setAllReadonly`, the
inner `Flag` class) is line-for-line identical past the import block. `[CERT]` — B51-G2's identity
question is **closed**, not merely "plausible by continuity": this is a direct byte-level comparison, not
an inference from `BComponent`/`Property`/`Type` moving intact.

## 60.2 — B51-G2 (kit lint scan): works / needs-change / obsolete, exact lines `[CERT]`

Because §60.1 confirms the constant NAMES (`OPERATOR`, `TRANSIENT`, etc.) are unchanged, every lint that
matches on the bare constant-name SUBSTRING (as opposed to the fully-qualified import path) needs **zero
change** for N5 — this is now a direct consequence of a confirmed fact, not [Block 51]'s "plausible"
placeholder.

| Script | Line | Pattern | Verdict |
|---|---|---|---|
| `lint-config-sanity.sh` | `152` | `index(prop_buf, "OPERATOR") > 0` | **works** — bare substring match on the annotation text; `Flags.OPERATOR`/`"o"` unchanged |
| `lint-persist-hot-write.sh` | `136` | `index(rest, "TRANSIENT") == 0` | **works** — same reasoning |
| `lint-write-path.sh` | `370` | `index(prop_buf, "OPERATOR") > 0 \|\| index(prop_buf, "\"o\"")` | **works** |
| `lint-ext-writable-shape.sh` | `267` | `pflags !~ /OPERATOR/ && pflags !~ /"o"/` | **works** |
| `lint-changed-hot-write.sh` | `150` | `index(rest, "TRANSIENT") == 0` | **works** |
| `verify-module.sh` (`transient-operator` check, REMIT [Block 51] §51.2) | — | greps `Flags\.TRANSIENT`/`Flags\.OPERATOR` co-occurrence | **works** — confirmed, not merely plausible, now that §60.1 proves the FQN suffix `Flags.OPERATOR`/`Flags.TRANSIENT` is unchanged text regardless of which package `Flags` resolves from |
| `lint-structure.sh` L1 | `232` | `grep -qE '^[[:space:]]*package[[:space:]]+javax\.baja\.'` | **needs-change** — literal `javax\.baja\.` package-namespace match; must extend to also catch `niagara\.` (an N5 module wrongly declaring itself inside the framework namespace) |
| `lint-structure.sh` L3 | `253` | `grep -qE '^[[:space:]]*import[[:space:]]+javax\.baja\.'` | **needs-change** — silently stops firing on N5 source (false-negative, not false-positive): an N5 pure-model package importing `niagara.sys.*` never trips this WARN as shipped |
| `lint-structure.sh` L11 (BTest detector) | `274` | `grep -qE '^[[:space:]]*import[[:space:]]+(javax\.baja\.test\.\|com\.tridium\.btest\.)'` | **needs-change — new finding, not named in [Block 51]** — N5's `BTest` moved to `niagara.test.BTest` (`organized/test/vineflower/niagara/test/BTest.java:1`, `package niagara.test;`, `[CERT]`), so this regex needs a `niagara\.test\.` alternative added or it silently stops detecting BTest-style srcTest mixing on N5, the same false-negative class as L3 |
| `verify-module.sh` `cross-module-type` (REMIT [Block 51] §51.2) | `546` | `case "$t" in javax.baja.*\|com.tridium.*\|com.tridiumx.*\|com.honeywell.*) continue ;; esac` | **needs-change** (already named in [Block 51], re-confirmed this session at the exact line) — whitelist must add `niagara.*` |

**Net count.** Of the (kit-reported) 33 lint scripts, exactly **2** (`lint-structure.sh`,
`verify-module.sh`'s one check) carry a literal `javax\.baja\.`-namespace-coupled pattern, at **4** total
matching lines (`232`, `253`, `274`, `546`) — one more than [Block 51] enumerated (L11's BTest detector,
line 274, was not previously named). Every other Flags-referencing lint (5 scripts, 5 lines, table above)
is a bare constant-name substring match and needs **no code change**, confirming (not merely inferring)
[Block 51] §51.4's central finding that the kit's vocabulary-based lints were never coupled to the
namespace that actually moved.

## 60.3 — B51-G5 closed: per-profile (`rt`/`ux`/`wb`) Gradle split is not meaningful in N5 `[CERT]`

**Every one of the 4 working N5 PoC trees has exactly ONE project folder**, confirmed by `find <poc-root>
-maxdepth 1 -type d` this session:

| PoC | Project folders found | N4 source it was ported from |
|---|---|---|
| `n5-hello` | `n5Hello` (1) | none (fresh scaffold) |
| `coldroompan-n5` / `coldroompan-n5-ha` | `ColdRoomPan-rt` (1) | `ColdRoomPan-rt` + `-ux`/`-wb` (2-3 N4 parts) |
| `comppan-n5` | `CompPan-rt` (1) | `CompPan-rt` (1 N4 part, no merge needed) |
| `dashboardpan-n5` | `DashboardPan-rt` (1) | `DashboardPan-rt` + `-ux` (`-wb` contributed no source, REMIT [Block 51] §51.1.3) |

Not one PoC has a separate `-ux`/`-wb` project folder even where the N4 source genuinely had one
(`DashboardPan`) — CHK-1's module-part merge (REMIT [Block 10]/[Block 16]/[Block 28]) is universal across
every real port this corpus has produced, not a special case. The devkit's own wizard template agrees:
`module.gradle.kts.vm` (`/tmp/claude-1000/n5b36/templates-vf/gradle/module/module.gradle.kts.vm`, whole
file read) scaffolds exactly **one** `.gradle.kts` per module with no per-profile branching (`#if`/`#parse`
directives in the file gate on `$javascriptModule`/`$docModule`/`$description`/`$packages`, never on any
`rt`/`ux`/`wb`-named variable), and `modulePlugins.vm` (same session, whole file read) carries no
`RuntimeProfile`/`modulePart`-conditioned plugin block either. `[CERT]` — B51-G5's main question is closed:
no evidence anywhere in this corpus (4 real builds + the wizard's own generator) that N5 retains a
meaningful per-profile Gradle split.

**Side-finding, not previously surfaced: `ignoreRuntimeProfileCheck`.** `module.gradle.kts.vm:22` sets
`ignoreRuntimeProfileCheck.set("true")` inside `moduleManifest{}`, with the inline comment `//NOTE:
Temporarily ignore rt module part checks for module conversion exercise`. This property IS declared in
N5's own plugin DSL — `ModuleXml.java:87` (`this.getIgnoreRuntimeProfileCheck().convention(...gradleProperty("ignoreRuntimeProfileCheck"))`)
and `:155` (`public abstract Property<String> getIgnoreRuntimeProfileCheck();`), both re-read this session
— confirming N5's `ModuleManifestExtension` DSL still exposes SOME notion of a "runtime profile check" tied
to module-part conversion. `[CERT]` that the property exists and that the wizard sets it. **Not** resolved
this session: neither cached decompile fragment (`n5b2` nor `n5b36`'s `vf-out`) contains the CONSUMING
logic that reads this property — what the check actually verifies, and what fires if a real multi-part
module is NOT converted, is unknown. None of the 4 real, finished PoC `.gradle.kts` files reference this
property at all (confirmed by the full reads in §Sources), meaning either the check never fires once a
module genuinely has one project (the common, post-merge case), or its absence silently defaults to some
value the wizard's own "Temporarily" comment does not fully explain. Named child gap **B60-G1**.

**B51-G5's L7 sub-question also closes here.** `lint-structure.sh` L7 flags an inline-versioned Gradle
dependency string, `grep -qE '":[^:]+:[0-9]+\.[0-9]+"'` — matching a quoted string that STARTS with a bare
colon (`":module:X.Y"`), not a Maven `group:artifact:version` coordinate (which starts with the group ID,
not a colon). Every real N5-module dependency line read in full this session — `DashboardPan-rt`'s
`nre(":nre")`/`api(":baja")`/`api(":alarm")`/`api(":web")`, `ColdRoomPan-rt`'s `api(":baja")`/
`moduleTestImplementation(":test")`, `CompPan-rt`'s `api(":baja")`, `n5Hello`'s `api(":baja")` — uses the
bare `":name"` form with **zero** inline version suffix (§60.3's own table's source files, whole-file
reads). The 3 lines that DO carry an inline version (`compileOnly("jakarta.servlet:jakarta.servlet-api:6.1.0")`,
`compileOnly("org.openjfx:javafx-base:25:linux")`-family, `moduleTestImplementation("org.testng:testng:7.12.0")`)
are all **external Maven coordinates**, none of which start with a leading colon, so L7's regex does not
match them either. `[CERT]`: L7 never fires on any real N5-ported module examined this session — not
merely "every example read uses the bare form" ([Block 51]'s hedge), but a positive confirmation the regex
itself cannot match the external-coordinate form these modules actually use.

## 60.4 — B51-G3 closed: `lint-bundled-jar-class-version.sh`'s exact constant `[CERT]`

Whole 67-line file read. The literal threshold is the bare integer `52`, embedded twice:

- Line `56` (the comparison, inside the `awk` block): `if (m > 52) { print m }`
- Lines `16`/`59` (the row-format string and the printed FAIL message): `"(> 52 = Java 8)"` /
  `'FAIL  lint-bundled-jar-class-version  %s  class %s is major %s (> 52 = Java 8) — ...\n'`

No named constant, no variable — `52` is hardcoded at both sites. This is the **same 52→69 delta** as
`verify-module.sh`'s `bytecode` check (REMIT [Block 51] §51.2, `[CERT-hw]` confirmed on 3 real N5 builds:
every `.class` entry, including `module-info.class`, is major **69**). Confirms [Block 51]'s "almost
certainly the same update" guess directly from source, not by extrapolation.

**A sharper point than a simple constant swap.** This script's CHECK DIRECTION does not merely need a
number update — its entire premise inverts on N5. On N4, `>52` flags a bundled ext-jar as dangerously
"too new" because the module itself compiles to major 52 and the station JVM is Java 8. On N5, the
module's OWN compiled classes are already major 69 (Java 25) — so a bundled ext-jar at major 69 is now the
EXPECTED, safe case, and the check that mattered on N4 (catch Java 9+ bytecode nobody asked for) needs an
N5-appropriate reformulation: flag a bundled jar whose major EXCEEDS the N5 toolchain's own target (69, or
whatever the pinned N5 JDK is), not simply "greater than 52." A bare `52→69` constant swap alone would
correctly stop false-flagging N5's own legitimate 69-major jars, so the swap is sufficient — but it is
worth recording that the fix is "replace the baseline," not "raise the baseline by a small margin."

## 60.5 — B51-G4 closed: `rc-scan.sh`/`bog-audit.sh` have ZERO structural coupling to `-rt|-ux|-wb` `[CERT]`

Stronger than [Block 51]'s own hedge ("likely path-glob/profile-name matching, not confirmed"). Both
scripts read in full (143 + a targeted read of `bog-audit.sh`'s `SRC_DIR`/`--source-dir` handling, 889
lines total file size).

- **`rc-scan.sh`**'s only `-rt|-ux|-wb`-token hit is line `5`, inside the header COMMENT: "from the real
  DashboardPan-**ux** rc/index.html" — plain prose, not code. The script's actual file walker,
  `_scan_files()` (lines 118-126), is a generic `find <artifact-dir> ... -path '*/rc/*' ( -name '*.html'
  -o -name '*.js' -o -name '*.css' )` glob — it takes WHATEVER directory it is invoked against and matches
  any `rc/` subtree inside it, with no dependency on a `-rt`/`-ux`/`-wb`-suffixed project name anywhere in
  the matching logic. N5's merged `-rt` project still has an `rc/` folder (confirmed:
  `DashboardPan-rt.gradle.kts`'s own `tasks.named<Jar>("jar") { from("src/rc") { ... into("rc") } }`
  packaging block, §Sources) — this script finds it exactly the same way it found N4's separate `-ux`
  project's `rc/` folder. **Zero code change needed.**
- **`bog-audit.sh`**'s only `-rt|-ux|-wb`-token hit is line `811`, again a COMMENT: "CONTROL types: ...
  CompressorControl (-rt)." — prose annotating what a component TYPE name means, not a path match. The
  script's `--source-dir` walker is Python's `os.walk(SRC_DIR)` (line `133`), a plain recursive directory
  walk with no `-rt`/`-ux`/`-wb` naming assumption anywhere in the 889-line file (confirmed by `grep -n`
  for `source-dir|SRC_DIR|SRCDIR|profile_dir|src/` across the whole file, §Sources). It walks whatever
  `--source-dir` the caller passes and classifies files by their OWN content (schema-drift, dangling
  links, out-of-facet values), never by which historical N4 part folder they came from. **Zero code
  change needed.**

Both scripts are, if anything, MORE N5-transferable than [Block 51] hypothesized: not "likely
path-glob matching that probably still works," but confirmed to contain no `-rt`/`-ux`/`-wb`-conditioned
logic at all, anywhere, in either file.

## 60.6 — B51-G7: measured N4 vs N5 explicit dependency counts, 229 common module families `[CERT-hw]` + `[INFER]`

A fresh, single-use Python scan (this session, scratchpad-only script, not preserved) walked
`/mnt/c/Honeywell/OptimizerSupervisor-N4.14.0.162/modules/*.jar` (1013 jars) and
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar` (247 jars), opened every jar's
`META-INF/module.xml`, regex-extracted `<dependency name="...">` entries, grouped by module family
(stripping the `-rt|-ux|-wb|-wh|-se|doc` part suffix — confirmed this session to match the file's own
`<module moduleName="...">` attribute, `kitControl-ux.jar!META-INF/module.xml`), and intersected on family
name. **229 families are common to both installs.**

**Named confound, stated up front.** The N4 side is a Honeywell OEM distribution (`OptimizerSupervisor`),
not vanilla Tridium N4; the N5 side is a stock Tridium `5.0.0.28` install. Only 229 of N5's 247 families
have an N4-side counterpart at all (the rest are N5-only modules with no N4 name match, or Honeywell-only
modules absent from stock N5). Any absolute-magnitude claim below inherits this cross-vendor confound —
it is not a same-vendor N4-vs-N5 diff.

**Two granularities, two different pictures.**

1. **Raw union** — source family collapsed (N4's 3 part-jars merged into 1 family), dependency TARGET
   names left as-is (so `alarm-rt` and `alarm-ux` count as 2 distinct entries, matching N5's single
   `alarm`): mean delta (N5 − N4) = **−5.7**, median = **−3**; 125/229 families show fewer deps in N5,
   42/229 show more, 62/229 unchanged. This is the shape that would seem to confirm the task's own framing
   and [Block 51] §51.6's comparative hedge.
2. **Part-suffix-collapsed** — BOTH source family and every dependency TARGET name collapsed the same way
   (`alarm-rt`/`alarm-ux` → `alarm`, matching how N5 already declares it), with self-references to the
   module's own other parts stripped (`kitControl-ux` depending on `kitControl-rt` no longer counts as an
   "external" dependency): mean delta = **−0.09**, median = **0**; 97/229 fewer, 65/229 more, 67/229
   unchanged. At the LOGICAL module-family level, the aggregate effect is essentially a wash.

**`kitControl` spot-check, both granularities.** Raw union: N4 = 49 distinct dependency STRINGS across its
3 parts (`kitControl-rt.jar` 11, `-ux.jar` 38, `-wb.jar` 35, unioned) vs N5's single `kitControl.jar` = 28
(`[CERT]`, both module.xml dumps read in full, §Sources). Part-collapsed (and self-ref `kitControl-rt`
stripped): N4 = 35 distinct FAMILIES vs N5 = 28 — still fewer, but the gap narrows from 21 to 7 once the
part-suffix inflation is removed.

**Interpretation `[INFER]`.** The raw-union −5.7 mean delta is substantially a MECHANICAL ARTIFACT of N4's
own 3-way part split: a family with `-rt`+`-ux`+`-wb` parts naturally accumulates more distinct
`<dependency name="...">` STRINGS across 3 separate `module.xml` files (even when they name the same
underlying module, `alarm-rt` and `alarm-ux` are 2 strings) than a single post-CHK-1-merge N5 jar with one
`<dependencies>` block ever could. This is consistent with — and now measures, rather than merely asserts
— [Block 51] §51.1.3's own documented mechanism (module parts genuinely merge into one compilation unit on
N5). It does **not** by itself demonstrate that N5's LOGICAL dependency graph (which distinct module
families a given piece of functionality actually needs) is narrower than N4's: once part-suffix inflation
is removed from both sides, the aggregate difference is close to zero, with substantial variance in both
directions per family (see table). [Block 51] §51.6's own `[CERT]` mechanism finding — that N5's
`module.xml <dependencies>` is derived by scanning the resolved `compileClasspath` with
`excludedDependencyModules` filtering and `dependencyVersionLimit` version-truncation — remains correct
and is not contradicted by this measurement; what this measurement narrows is the SEPARATE, less certain
comparative claim ("N5 shows FEWER explicit dependencies than N4") that [Block 51] itself flagged as
`[INFER]`-pending-B51-G7. That claim is **not well-supported in aggregate** once the part-suffix confound
is corrected for.

**Distribution tails (part-collapsed granularity), most informative rows:**

| Module | N4 dep (families) | N5 dep (families) | Δ | Note |
|---|---|---|---|---|
| `html` | 31 | 1 | −30 | largest drop; plausibly a Honeywell-side customization, not examined further |
| `signingService` | 58 | 36 | −22 | |
| `alarm` | 37 | 27 | −10 | a framework module central to most other families |
| `kitControl` | 35 | 28 | −7 | see spot-check above |
| `lonWattStopper` | 1 | 35 | +34 | largest gain; N4-side Honeywell build declares almost no explicit deps for this driver, N5-side stock build declares a full driver dependency set — plausibly a distribution-completeness difference, not an N4→N5 mechanism effect |
| `platBacnet`/`platLon`/`platMstp`/`platNrio`/`platSerial`/`platCcn`/`platEdgeIo`/`platSerialNpsdk` | 7-9 each | 26-28 each | +17 to +19 each | a whole CLUSTER of thin `plat*` driver-platform modules, all showing large, similarly-sized gains — suggests a systematic Honeywell-vs-stock packaging difference for this module class specifically, worth a dedicated read if this direction is pursued further |
| `docDeveloperAnalytics` | 29 | 54 | +25 | |
| `obixSeriesTransform` | 22 | 54 | +32 | |

## 60.x — Open questions / unresolved contradictions

- **[C1]** [Block 51] §51.6 cites `ModuleXml.java:68` (`this.getDependencyVersionLimit().set(2)`) as the
  mechanism behind a `vendorVersion` truncation it observed as `2.0.7` → `2.0` (3→2 segments, dropping 1
  trailing segment) for `ColdRoomPan-rtTest`'s dependency on `ColdRoomPan-rt`. This session's fresh spot
  check of `kitControl.jar!META-INF/module.xml`'s own declared dependency on `alarm` shows `vendorVersion="5.0.0"`
  (3 segments) where `alarm.jar`'s OWN `<module vendorVersion="5.0.0.28">` (4 segments) is the source value
  — also a 4→3 truncation, i.e. also dropping exactly 1 trailing segment, NOT 2. Both observed truncations
  drop exactly 1 segment regardless of the source's total segment count (3→2 and 4→3), which is hard to
  reconcile with a single constant `dependencyVersionLimit=2` meaning either "keep 2 segments" (would give
  `alarm`→`5.0`, not observed) or "drop 2 segments" (would give `alarm`→`5.0` from a 4-segment source too,
  not observed either). `Version.strip(int)`'s own implementation was not located in either cached
  decompile fragment (`n5b2`/`n5b36`) this session — genuinely unresolved, not forced into either reading.
  Named child gap **B60-G2**: decompile/read `Version.strip(int)` directly (likely in
  `com.tridium.gradle.plugins.module.util.Version` or a shared baja-side `Version` class) to settle what
  the `2` parameter actually means.

## 60.x — Self-verify tally

```
$ bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    niagara5-block60.md .
== verify-block: niagara5-block60.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 6  (adj 4)
   [CERT-live] 3
   [CERT] 16  (adj 15)
   [CERT-doc] 3
   [CERT-web] 3
   [CERT-a] 3
   [INFER] 9  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/31 = 0.19
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   jar-entry  bajaui.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   jar-entry  cloudLinkAzure.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   jar-entry  kitControl-ux.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   jar-entry  kitControl.jar!META-INF/module.xml  (jar archive path — not file-verifiable)
   extern  Flags.java:9  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:68  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  ModuleXml.java:87  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  lint-structure.sh:232  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  module.gradle.kts.vm:22  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/test/vineflower/niagara/test/BTest.java:1
   extern  verify-module.sh:546  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   resolved 1 of 7
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

This is the script's LITERAL output, run read-only from `/home/cristian/niagara5-research` this session
(methodology §11: "the reported tally MUST BE the LITERAL `verify-block.sh` output"). The exact "resolved N
of M" count is **self-referentially sensitive** in this particular block — because §60.2/§60.4/§60.5's own
tables and prose quote several N4-kit `file:line`-shaped tokens (`lint-structure.sh:232`,
`verify-module.sh:546`, etc.) as DATA (the exact lines being classified works/needs-change), the script's
citation scanner picks those up as citation ATTEMPTS on every run, and each round of self-verify editing
that touched this section shifted the count by ±1. Re-running the script now would very likely print a
slightly different M again for the same underlying reason; this is a property of how densely this block
quotes other files' line numbers, not evidence of an unstable or unreliable file. Reading it correctly
requires context the raw numbers do not carry on their own:

- **`[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` at 1 each are the header's own MARKER-LEGEND
  mentions** (this block's blockquote lists all 7 marker types when explaining which ones it uses, the same
  legend pattern every block in this corpus carries) — the script's raw pass counts every marker TOKEN
  including the legend text; none of §60.1-§60.6's body claims actually use `[CERT-live]`/`[CERT-doc]`/
  `[CERT-web]`/`[CERT-a]` (this block cites no live remote service, no downloaded document, no official web
  page, and no forum/secondary source), so the adjusted/claim-level count for all 4 is effectively 0 once
  the legend is stripped — the script's own "adj" column strips this for `[CERT-hw]`/`[CERT]`/`[INFER]` but
  the tool did not fold these 4 rarely-used markers into "adj" the same way; read them as 0 body claims by
  direct inspection of §60.1-§60.6.
- **Citation resolution: `resolved 1 of 6` for `file:line`-form citations, plus 4 `jar-entry` rows the
  script tracks separately.** The 1 resolved hit is `organized/test/vineflower/niagara/test/BTest.java:1`
  (§60.2's L11 finding) — genuinely inside the target directory and script-verified present at the cited
  line. The 5 `extern` `file:line` citations (`Flags.java:9`, `ModuleXml.java:68`/`87`,
  `lint-structure.sh:232`, `module.gradle.kts.vm:22`) split into two classes: the 2 `ModuleXml.java` and 1
  `Flags.java`/1 `module.gradle.kts.vm` hits are the DECOMPILED-TREE / devkit-template-cache citations
  living under `/tmp`, matching the established DECOMPILED-TREE BLOCKS signature (methodology §11) — every
  one was read in full or targeted-but-complete this session (§Sources); `lint-structure.sh:232` is a
  same-repository-family but DIFFERENT-REPOSITORY citation (`build-n4-module-kit`, not this
  `niagara5-research` corpus) that the script's scan still attempted and correctly could not resolve
  locally — expected, not a defect, for a `file:line` cite into a sibling repository outside the scanned
  target. The 4 `jar-entry` rows are `bajaui.jar`/`cloudLinkAzure.jar`/`kitControl-ux.jar`/`kitControl.jar`,
  all cited in `<jar>!META-INF/module.xml` form (methodology §11's jar-archive convention, same as
  [Block 42]'s precedent) — not file-line-verifiable by design, and correctly flagged as such rather than
  as a failure. The script's citation scan did **not** separately enumerate this block's 6
  PoC-`.gradle.kts` citations (`DashboardPan-rt.gradle.kts`, `ColdRoomPan-rt.gradle.kts`,
  `CompPan-rt.gradle.kts`, `n5Hello.gradle.kts` — each cited by filename/whole-file-read prose rather than
  a `file:line` anchor form) nor most of the other 4 N4-kit script line citations (`verify-module.sh:546`,
  `lint-bundled-jar-class-version.sh:16/56/59`, `rc-scan.sh:5/118-126`, `bog-audit.sh:133/811` — all in the
  separate `build-n4-module-kit` repository, outside this corpus's `.` target). This is
  the expected shape for a block whose evidence spans 3 separate repositories/trees (this corpus, the N4
  kit repo, and 2 `/tmp` decompile caches) — most citations are necessarily `extern` to any single-target
  scan, exactly as [Block 51]/[Block 42] already established for cross-repository research blocks.
- Exit `0`: no verifiable contradiction found (no cited file that exists but whose line is out of range).
- **Artifacts** — this block file exists at `/home/cristian/niagara5-research/niagara5-block60.md`. No
  other file in this corpus, the N4 kit, the PoC trees, or either module install was modified — read-only
  throughout, per task scope. `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were **not** regenerated this
  session, matching [Block 51]'s own stated convention (the parent orchestrator owns that).
- **MCP-doc snapshots** — N/A, no MCP/context7 citation used this session.
- **Token check** — every `Flags.OPERATOR`/`Flags.TRANSIENT` line number cited in §60.2's table was
  independently `grep -n`-confirmed present at the stated line in its script this session (not carried
  from a prior read); the `52` constant in §60.4 was confirmed present at both cited lines (`16`/`56`/`59`)
  by the whole-file read quoted in that section; the `ignoreRuntimeProfileCheck` property was confirmed
  present at both cited `ModuleXml.java` lines (`87`, `155`) by direct `grep -n` this session.

## 60.x — Connections

- **[Block 51]** — this block closes B51-G2 (Flags identity + lint scan), B51-G3 (`lint-bundled-jar-class-version.sh`
  exact constant), B51-G4 (`rc-scan.sh`/`bog-audit.sh` non-coupling), and B51-G5 (per-profile split not
  meaningful in N5, plus the `ignoreRuntimeProfileCheck` side-finding and the L7 confirmation). B51-G7 is
  **narrowed, not fully closed**: this session measures the comparative claim directly and finds it does
  not hold in aggregate once the part-suffix confound is corrected — a genuine refinement of [Block 51]
  §51.6's own framing, recorded as a de-escalation (methodology §11) rather than a simple "confirmed."
- **[Block 2]** — `ModuleXml.java`'s `getDependencyVersionLimit()`/`getIgnoreRuntimeProfileCheck()`
  declarations (§60.3, §60.6/[C1]) extend [Block 2] §2.4's DSL-surface table with two properties it named
  but did not trace to their exact default-value assignment lines.
- **[Block 9]** — `n-java`'s absence from `modulePlugins.vm`'s own default plugin list (re-confirmed
  §60.3, whole-file read) matches [Block 9] §9.4's own load-bearing discrepancy finding exactly.
- **[Block 16]/[Block 28]** — §60.3's PoC-folder-count table and §60.6's `kitControl`/`alarm` spot-checks
  both re-read files these blocks first built/ported, without contradicting either block's own findings.
- **[Block 36]** — the devkit Velocity template cache (`/tmp/claude-1000/n5b36/templates-vf/`) this block
  reads from was extracted in [Block 36]'s own session; re-read here, not re-extracted.

## 60.x — Child gaps

- **B60-G1** — `ignoreRuntimeProfileCheck`'s CONSUMING logic (what it gates, what happens if a genuine
  multi-part module is not "converted") was not located in either cached decompile fragment this session;
  the wizard sets it `"true"` with a "temporarily" comment, but no real N5 module examined in this corpus
  references it, so its actual effect when left at N5's own default (unset) is unconfirmed.
- **B60-G2** — `Version.strip(int)`'s exact algorithm is unresolved; two independent observed truncations
  this session (`ColdRoomPan-rtTest`'s `2.0.7`→`2.0`, REMIT [Block 51] §51.6; this session's fresh
  `kitControl`→`alarm` dependency `5.0.0.28`→`5.0.0`) both drop exactly 1 trailing segment regardless of
  source length, which is in tension with a naive reading of `dependencyVersionLimit`'s literal default
  value `2` as either "keep 2 segments" or "drop 2 segments." Needs a direct read of the `Version` class's
  `strip()` method.
- **B60-G3** — the `plat*` driver-platform module cluster (`platBacnet`/`platLon`/`platMstp`/`platNrio`/
  `platSerial`/`platCcn`/`platEdgeIo`/`platSerialNpsdk`) shows a strikingly uniform +17 to +19 dependency
  gain in N5 vs. the Honeywell N4 build (§60.6's distribution table) — worth a dedicated read of one such
  module's N4-vs-N5 `module.xml` side by side to determine whether this is a genuine N5-side packaging
  richness difference or a Honeywell-specific N4 minimization, before drawing any conclusion from this
  cluster.
- **B60-G4** — the `html`/`file`/`fox`/`export` family cluster shows the opposite extreme (−30/−18/−11/−11)
  even at the part-collapsed granularity; not examined for a specific cause this session (plausibly
  Honeywell-side stripped-down builds of these small utility modules, but unconfirmed).
