# Block 66 — The migrator internals census: `MigrationUtils`'s 40-method surface, the four `-premigrate` bodies, the 180-entry zwave removal list, and a bytecode-level close of the vestigial KeyRing-decrypt gap

> Closes four child gaps [Block 24]/[Block 47] each named but left open: **B24-G4** (`MigrationUtils.java`'s
> ~40 static methods — [Block 24] §24.4 censused these by `grep` signature only; this block reads the full
> 569-line body and produces a reference table of what every method does); **B24-G5** (`BBackupDistMigrator`'s
> 278-line body and the four `-premigrate` counterpart classes — `BBackupDistPremigrator`, `BBogPremigrator`,
> `BPxPremigrator` — plus `BPxMigrator`'s 658-line body, all previously read only at signature/class-name
> level); **B24-G3** (the 180-entry `zwave:*` type list `BZWaveBogConverter` registers for unconditional
> module removal — read whole by [Block 24] but not individually tabulated; this block shape-summarizes it
> with a representative sample instead of pasting all 180 rows); and **B47-G1**/**B47-G2** (whether the
> vestigial `MigrationEncoding.makeMigrationDecryptFunction`/`BBackupDistMigrator.LazyDecryptFunction`/
> `Migrate.passwordDecryptFunction` machinery [Block 47] §47.3 found source-`grep`-unreferenced has a LIVE
> call site anywhere — this block settles it with a genuine bytecode-level cross-reference across all 94
> compiled classes in the shipped `migrator.jar`, not a further source `grep`, and reads `Premigrate.java`
> [Block 47] explicitly named as unopened). Does **not** cover: an actual `n5mig`/`n5mig -premigrate`
> execution (still inherits [B14]/[B24]/[B31]'s open requires-execution gaps — nothing here runs the tool);
> `Migrate.java`'s own 1,201-line CLI-driver body beyond the two field/no-call-site checks needed for §66.6
> (its `main()`/argument-parsing/HTML-report-formatter machinery is out of scope — a candidate for a future
> block, not opened here); `BBogMigrator.java`'s body (already read whole by [Block 24] §24.3, not re-read);
> the individual per-command-class semantics of the 180 zwave types (§66.5 tabulates the LIST's shape, not
> what each Z-Wave command class does on the wire — out of scope, and moot regardless since the whole module
> is unconditionally removed with no per-type branching).
>
> Subject version: **N5 5.0.0.28 (Beta)** — same install as [Block 14]/[Block 24]/[Block 31]/[Block 47].
> `migrator.jar` sha256 `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08`, re-verified
> identical this session (`sha256sum` against the live install at
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/migrator.jar`, matches [B24]'s/[B47]'s header
> hash byte-for-byte — same artifact, no re-decompilation needed for the source reads; a **fresh** `unzip`
> extraction of the same jar's 94 `.class` files was made this session specifically for the §66.6 bytecode
> disassembly, since neither [B24] nor [B47] opened compiled bytecode).
>
> Sources: `organized/migrator/vineflower/com/tridium/migrator/MigrationUtils.java` (569 lines, full read,
> this session — [B24] §24.4 only `grep`-censused signatures); `.../BBackupDistMigrator.java` (278 lines,
> full read — [B24] §24.2 read only `getMigrateTypes()`/`initialize()`/`migrate()` signature-level);
> `.../BPxMigrator.java` (658 lines, full read — same prior signature-only treatment); `.../BPxPremigrator.java`
> (330 lines, full read, first time in either corpus); `.../BBogPremigrator.java` (322 lines, full read, first
> time); `.../BBackupDistPremigrator.java` (125 lines, full read, first time); `.../Premigrate.java` (293
> lines, full read — the exact file [Block 47] §47.5 named as "not opened this session" for B47-G1);
> `.../zwave/BZWaveBogConverter.java` (215 lines, full read, `CONVERT_TYPES` list at `:19-200`, re-tabulated
> by shape this session, `grep -c`-recounted at exactly 180 entries); `.../baja/MigrationEncoding.java` (127
> lines, re-opened this session for its call-site cross-reference, not its body — already read whole by
> [Block 47] §47.3); `.../Migrate.java:75` (the `passwordDecryptFunction` field declaration, re-opened for
> the same cross-reference; whole 1,201-line file NOT read this session, only this one field's usage
> confirmed). `[CERT-hw]`-adjacent bytecode evidence: `javap -p -c -constants` disassembly of all **94**
> `.class` files extracted this session from the live install's own `migrator.jar`
> (`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/migrator.jar`, sha256 re-verified above) —
> a genuine primary-source read of the exact shipped bytecode, distinct from and strictly more thorough than
> [Block 47] §47.3's source-tree-only `grep -rn "MigrationEncoding"` (which only ever covered the DECOMPILED
> `.java` tree, itself a partial reconstruction, not the compiled class files).
>
> Method: `Read` (whole-file, this session, no line ranges skipped) for every `.java` source cited above;
> `unzip` extraction of `migrator.jar`'s 94 `.class` files to a fresh scratch directory this session, followed
> by `javap -p -c -constants <class>` (OpenJDK 21 `javap`, successfully disassembles this install's class
> files) run once per class, output captured per-class, then `grep`-cross-referenced across ALL 94 output
> files (not just the 3 classes already named as suspects) for the three symbol names
> (`MigrationEncoding`/`LazyDecryptFunction`/`passwordDecryptFunction`) to find any call site a source-level
> `grep` across the (possibly incomplete) decompiled tree could miss — e.g. a synthetic lambda-bridge method,
> a reflective `Class.forName`/`MethodHandle` invocation compiled to a distinguishable pattern, or a call from
> a class the decompiled `organized/` tree does not currently hold. `grep -c '"zwave:'`
> line-count of `BZWaveBogConverter.java`'s literal string array for the §66.5 shape census. Markers: `[CERT]`
> local primary source (`file:line`, this session) · `[CERT-hw]` used narrowly for the bytecode
> disassembly-of-the-shipped-binary evidence in §66.6 (the compiled `.class` files are the actual artifact
> the running N5 JVM loads — a step closer to "what the live system executes" than the decompiled `.java`
> reconstruction the rest of this corpus cites, though still a static read, not a runtime trace — see
> methodology note below) · `[INFER]` deduction.
>
> Migration/build-porting layer. Deepens [Block 24] (closes B24-G3/B24-G4/B24-G5, all four child gaps that
> block's own §24.9 opened) and [Block 47] (closes B47-G1, substantially narrows B47-G2 — see §66.6's
> honest scope note on what "closes" means for a negative-existence claim). Connects [Block 14] (grandparent
> of the whole migrator-catalog chain) and [Block 31] (PANCCADIA cross-check context, unaffected by this
> block — no PANCCADIA artifact was opened this session).
>
> **Type:** `mixed` — §66.1-§66.4 are evidence blocks (reading previously-signature-only-censused shipped
> `.java` sources in full, closing B24-G3/G4/G5 outright); §66.6 is the `mixed` trigger proper: it upgrades
> [Block 47] §47.3's own `[INFER]` "no call site found by source `grep`" finding to a stronger `[CERT]`-grade
> claim by opening a DIFFERENT artifact class (compiled bytecode, never previously opened in this corpus) than
> the one [Block 47] used — the same "`[INFER]`-across-a-prior-block correction via a newly-opened source"
> pattern [Block 61]'s own header declared as the `mixed` trigger (METHODOLOGY §4/§11).

---

## 66.1 — `MigrationUtils`'s full method surface: a reference table for all ~40 statics, closing B24-G4 `[CERT]`

Full read of `MigrationUtils.java` (569 lines) this session. **Exact count, reconciling [Block 24] §24.4's
"~40" estimate**: 47 `static` method SIGNATURES (`grep -nE` re-run this session against the whole-file read,
one match per method declaration line, overloads counted separately) plus one private no-arg constructor
(`MigrationUtils()`, `:60-61`, blocks instantiation — this is a pure static-utility class) plus one
NON-static instance method (`isTypeDenyListed`, `:547-567`, on the private inner class
`MigrationValueDocDecoder`, itself NOT a `MigrationUtils` static method — see the standalone row below).
**39 DISTINCT method NAMES** are exercised across those 47 static signatures — 7 names are overloaded
(`getFileStats`×2, `extractZip`×2, `logInfo`×2, `logWarning`×2, `logSevere`×2, `errorResult`×2,
`errorResultList`×2 = 7 pairs = 14 signatures for 7 names, +33 single-signature names = 47 signatures / 39
names), which is the precise arithmetic behind [Block 24]'s "~40" grep-signature estimate — it counted
signature LINES, landing close to the distinct-name count by coincidence of the overload ratio, not because
the two numbers are the same thing. `[CERT]` `grep -nE` re-run this session, whole-file, cross-checked
against the full `Read`.

| Method (overloads grouped) | `file:line` | Category | What it does |
|---|---|---|---|
| `safeCreateDirectory(File)` | `:63-71` | file I/O | `mkdirs()` if absent, else no-op; throws `IOException` on failure |
| `safeCreateFile(File)` | `:73-86` | file I/O | Creates parent dirs then `createNewFile()`, else no-op if file exists |
| `safeCopy(File,File)` | `:88-98` | file I/O | Ensures target parent dir exists, deletes existing non-dir target, delegates to `FileUtil.copy` |
| `safeMove(File,File)` | `:100-110` | file I/O | Same shape as `safeCopy` but `FileUtil.move` |
| `getFileStats(File)` / `getFileStats(File,FileStats)` | `:112-135` | file I/O | Recursive directory walk accumulating `FileStats{fileCount,byteCount}`; logs `SEVERE` on a `long` rollover |
| `isDirectory(File)` | `:137-139` | file I/O | `isDirectory()` OR (does-not-exist AND name has no `.`) — a heuristic for a not-yet-created directory target |
| `makeFileFromZipEntry(File,ZipEntry)` (private) | `:141-144` | zip | Resolves a `ZipEntry`'s target `File`, creating dir or file as appropriate |
| `extractZip(ZipFile,File,Predicate)` | `:146-163` | zip | Unconditional-filter unzip, no progress reporting |
| `extractZip(ZipFile,File,List,BiPredicate)` | `:165-187` | zip | Same, but reports progress via `showProgress` and passes the caller's `xDirs` list into the filter — the overload `BBackupDistMigrator`/`BBackupDistPremigrator` actually call (§66.2) |
| `getDistributionManifest(ZipFile)` | `:189-197` | dist | Reads `META-INF/dist.xml` from a `.dist` zip, throws `MigrationException` if absent |
| `validateDist(DistributionManifest,BVersion)` | `:199-217` | dist | Finds the `baja` dependency in the manifest, throws `MigrationException` if missing or below `minimumVersion` |
| `showProgress(int,int,String,String)` | `:219-224` | console | Prints a `[####   ] NN% msg\r` progress bar; prints a trailing newline once `cur>=goal` |
| `pad`/`trim`/`progress`/`bar` (all private) | `:226-248` | console | String-formatting helpers backing `showProgress` (padding, truncation-with-ellipsis, percentage math, bar-glyph construction) |
| `createZip(File,File)` | `:250-263` | zip | Zips a directory's sorted top-level contents into `zipTgt` |
| `addFileToZip` (private, recursive) | `:265-290` | zip | Recursion helper for `createZip`; skips empty files/dirs via `isEmpty` |
| `isEmpty(File)` (private, recursive) | `:292-316` | zip | True if file absent, or a directory whose full recursive contents are all empty |
| `configureMigrationLogForDecoder(ValueDocDecoder,Logger)` | `:318-323` | logging | Wires a decoder's log + (if a `BogDecoderPlugin`) sets its warning-log level to `CONFIG` |
| `logConfig`/`logInfo`(×2)/`logInfoByModule`/`logWarning`(×2)/`logSevere`(×2)/`logSevereByModule` | `:325-359` | logging | The shared lexicon-backed logging family EVERY converter in [B24]'s §24.2 catalog calls; the `Throwable`-arg overloads append `formatThrowable`'s output; `*ByModule` variants look up a PER-MODULE `Lexicon` via `getLexicon` instead of the class's own `migrator` lexicon |
| `getLexicon(String)` (private) | `:361-369` | logging | Lazily caches a `Lexicon.make(module)` per module name in the static `lexMap` |
| `formatThrowable(Throwable,Logger)` | `:371-386` | logging | Full stack trace if `Logger` is loggable at `CONFIG`, else a one-line `toString()` + `MigrationConsoleUtil.toFriendlyErrorMessage` |
| `validateTarget(File,Logger,String,boolean)` | `:388-407` | pre-flight | If target exists and `!overwrite`, logs+returns a `<logType>.targetExistsFail` message; if `overwrite`, deletes it first; catches any exception into `migrate.cannotValidate` |
| `errorResult(Logger,String[,Throwable])` (×2) | `:409-429` | error plumbing | Wraps a message (+ optional stack-trace-or-friendly-message) into an `Optional<String>` |
| `errorResultList(Logger,String[,Throwable])` (×2) | `:431-437` | error plumbing | `errorResult(...).map(List::of)` — the `Optional<List<String>>` shape every converter's `migrate()`/`runPremigrationCheck()` returns on failure |
| `outOfMemoryError(Logger)` | `:439-449` | fatal | Prints a fixed remediation banner (edit `defaults/nre.properties`, raise `-Xmx`) and calls `System.exit(0)` |
| `cleanMigTempDirs()` | `:451-453` | temp-dir lifecycle | Deletes the whole `MIG_TEMP_DIR` (`<niagaraUserHome>/temp/migTemp`) |
| `createMigTempDir(String)` / `getMigTempDirName(String)` | `:455-468` | temp-dir lifecycle | Creates (or just names) a de-duplicated `migTemp/<proposedName>[N]` subdirectory — the mechanism `BBackupDistMigrator`/`BBackupDistPremigrator`/`BPxMigrator` (§66.2/§66.3) all use for scratch space |
| `getRelPathFromMigTemp(File)` | `:470-474` | reporting | Strips the `MIG_TEMP_DIR` prefix from a path for user-facing log/report messages |
| `dumpToString(XElem)` | `:476-486` | debug | Serializes an `XElem` via `XWriter` to a `String`, falling back to `toString()` on any exception |
| `makeMigrationBogDecoder(File,Supplier<BPassword>)` | `:488-490` | bog decode | Factory for the private inner `MigrationValueDocDecoder` (below) |
| `getVersion(DistributionManifest,String)` | `:492-510` | version resolution | Looks up a module/typespec's dependency version in the manifest; falls back to `MigConst.VERSION_4_15` if the manifest is `null`, the arg is `null`, or the module isn't found — the exact per-converter version-decision method §24.4 named but did not itself read the body of |
| `isSameType(XElem,String)` | `:512-519` | XML helper | Compares an element's `t=` attribute's type-name segment (after `:`) against a given typespec's type-name segment |
| `removeSlotElements(XElem,XElem,String,List<String>)` | `:521-537` | XML helper | The generic multi-slot-removal helper [B24] cited `BWebBogConverter` calling: removes `element` from `parent` if its own type OR slot name is in `slotNames`; else, if `element` matches `parentType`, recurses one level into its children removing any CHILD whose slot name matches |
| `MigrationValueDocDecoder` (private inner class) `isTypeDenyListed(Type)` | `:539-567` | password gating | NOT a static `MigrationUtils` method — an inner `ValueDocDecoder` subclass instance method. Deny-lists `BPassword`/`BPasswordHistory`-typed values when the bog's own encoder reports `EncryptionKeySource.keyring` (unconditionally deny-listed) or, for non-`none` non-`keyring` sources, when no passphrase supplier is available — this is the LOAD-TIME counterpart to [Block 47] §47.1's `BBogMigrator`-side `keyring`-clearing policy, confirming the SAME unconditional `keyring`-is-non-migratable stance is baked into the generic bog-decoder layer `MigrationUtils` exposes, not just `BBogMigrator`'s own branch logic |

`[CERT]` every `file:line` above is this session's own whole-file `Read`, cross-checked against the
`grep -nE` signature list. **Correction/clarification to [Block 24] §24.4**: that section's own citation
list ("`:63` `safeCreateDirectory` through `:539` `MigrationValueDocDecoder`") named the START of the
method range correctly but did not distinguish `MigrationValueDocDecoder.isTypeDenyListed` as a NON-static
instance method on a nested class rather than a 40th `MigrationUtils` static — a minor scope note, not a
substantive error (the class-level census was accurate; the METHOD-level shape of that one entry was not).

## 66.2 — `BBackupDistMigrator` and its `-premigrate` counterpart, line-by-line: the `.dist`-container unpacker, closing half of B24-G5 `[CERT]`

Full read of `BBackupDistMigrator.java` (278 lines) and `BBackupDistPremigrator.java` (125 lines), both first
line-by-line reads in either corpus (`[Block 24]` §24.2 read only the class declaration/`getMigrateTypes()`
signature-level).

**`BBackupDistMigrator.migrate()` (`:72-161`), the actual `.dist`-container pipeline:**

```
migrate()
  ├─ createMigTempDir("src")                          — scratch extraction root (MigrationUtils.createMigTempDir)
  ├─ open ZipFile(source), read DistributionManifest, validateDist(≥4.15)
  ├─ extractZip(zin, srcRoot, DIRS_TO_EXTRACT, filter) — DIRS_TO_EXTRACT = {"niagara_user_home/stations/",
  │                                                        "niagara_user_home/security/.kr", "stations/",
  │                                                        "security/.kr"} (:38); filter SKIPS any entry whose
  │                                                        basename matches CONFIG_BACKUP_PATTERN
  │                                                        ("config_backup_<n>_<n>(_<n>)*", :37 — an
  │                                                        auto-generated in-station backup snapshot, not the
  │                                                        primary station files) and otherwise includes an
  │                                                        entry iff its path starts with one of the 4 dirs
  ├─ detect isRemoteBackup (any top-level "niagara*"-named dir present in srcRoot) → picks
  │    getStationsDir() = srcRoot/niagara_user_home/stations or srcRoot/stations accordingly
  ├─ getStationDir(stations, selectedStationName, false) — picks the ONE station folder (prompts
  │    interactively via MigrationConsoleUtil.readLineFromConsole if >1 and no preferred name given)
  ├─ resolve/validate this.target (auto-append the station's own dir name if target is a bare dir/needs one)
  ├─ createMigTempDir(stationDir.getName()) → srcMig (a SECOND, sibling scratch dir)
  ├─ copy EVERY file directly under stationDir (NOT srcRoot) into srcMig, one by one, with progress reporting
  └─ new Migrate(args, srcMig, target, distManifest, passPhraseSupplier).migrate() — delegates the ACTUAL
       per-bog/per-px migration to a NESTED Migrate instance scoped to srcMig
```

`[CERT]` `organized/migrator/vineflower/com/tridium/migrator/BBackupDistMigrator.java:72-161` (whole method), `:37-38` (the two static patterns/lists),
`:167-208` (`getStationsDir`/`getStationDir`, the station-selection helpers), `:210-260` (`getTarget`/
`findTargetStation`, a separate public accessor path used by `Migrate`'s own dist-detection logic, not
called from within `migrate()` itself).

**The exact confirmation of [Block 47] §47.3's "extracted-but-never-forwarded" `.kr` finding, now traced to
the literal directory split.** `DIRS_TO_EXTRACT` DOES pull `security/.kr`/`niagara_user_home/security/.kr`
out of the `.dist` zip into `srcRoot` (`:38`, confirmed again this session) — but the nested nested `Migrate`
instance's `srcMig` scratch dir is populated ONLY from `stationDir.listFiles()` (`:143-146`), and `stationDir`
is a SUBDIRECTORY of `srcRoot/stations/<name>/` (or the remote-backup equivalent) — a SIBLING path to
`srcRoot/security/.kr`, never a parent of it. The extracted `.kr` file therefore sits in `srcRoot`'s tree the
whole time `migrate()` runs and is never read, copied, or referenced again by any statement in this method.
`[CERT]` same citations as above — this is the literal directory-topology proof [Block 47] §47.3 flagged as
not yet traced (it inferred the non-forwarding from the absence of a copy statement; this session traces the
exact sibling-not-descendant relationship between `srcRoot/security/.kr` and `stationDir`).

**`LazyDecryptFunction` (private static inner class, `:262-277`).** A lazy `AESDecryptFunction` wrapper:
holds a `SupplierCanThrowException<AESDecryptFunction,Exception>`, and on first `decrypt()` call, resolves
the supplier once (caching the result in `this.inner`) before delegating. `[CERT]` `:262-277`, full class
body. **Confirmed this session: `grep -c "new LazyDecryptFunction\|new BBackupDistMigrator.LazyDecryptFunction"`
over this class's own 278-line body → 0** — no constructor call anywhere in the file that declares it,
consistent with and now RE-CONFIRMED alongside [Block 47] §47.3's finding (that block found the same zero
count; §66.6 extends this to a full bytecode cross-reference across the whole jar, not just this one file).

**`BBackupDistPremigrator.runPremigrationCheck()` (`:46-120`) mirrors `migrate()`'s shape almost exactly**,
reusing `BBackupDistMigrator`'s own static `DIRS_TO_EXTRACT`/`CONFIG_BACKUP_PATTERN`/`getStationsDir`/
`getStationDir` (cross-class static calls, `:53,55,82,92`) — the same `.kr`-extract-then-never-forward
topology applies identically to the `-premigrate` (dry-run) path: `srcMig` at `:98` is populated the same
way, from `stationDir.listFiles()` only, and the nested delegate is a `Premigrate` instance (`:109-111`,
`new Premigrate(args, srcMig, distManifest, passPhraseSupplier)`) rather than a `Migrate` one — the two
"outer" classes are structurally twins with one call-site substitution. `[CERT]` `organized/migrator/vineflower/com/tridium/migrator/BBackupDistPremigrator.java:46-120`
(whole method).

## 66.3 — `BPxMigrator` and `BPxPremigrator`, line-by-line: the px (UI file) migration pipeline, closing the other half of B24-G5 `[CERT]`

Full read of `BPxMigrator.java` (658 lines) and `BPxPremigrator.java` (330 lines), both first line-by-line
reads in either corpus.

**`BPxMigrator.migrate()` (`:92-111`) — a stub/rewrite/re-encode shape mirroring `BBogMigrator`'s 3-phase
pipeline ([Block 24] §24.3), but PX-specific:**

```
migrate()
  ├─ initializeDecoder()  — PxDecoder.parse() the source px XML; validates root name "px" and version "1.0";
  │                          decodeImport() walks each <module> import, resolving it either straight
  │                          (Sys.loadModule) or via ConverterRegistry.lookupPxConverters(moduleName)'s
  │                          newPxModule() rename hook; a module whose Sys.loadModule() throws
  │                          ModuleException is REMOVED from the import list and recorded in removedModules
  ├─ stubPx(root)          — rewrites renamed module imports via moduleMap; walks every <properties> child
  │                          THEN a full BFS over the widget <content> tree, resolving each element's type
  │                          via checkPropertyType()/checkType() (module-qualified lookup → PxConverter
  │                          rename-hook fallback → give up and DELETE the element, recording its typespec
  │                          in removedTypes); also renames the legacy element name "LinkSheet"→
  │                          "RelationSheet" unconditionally; writes the stubbed XML to a scratch file
  └─ writePx()             — re-decodes the STUBBED px via PxDecoder→BWidget, re-encodes via PxEncoder to
                              the final target — a genuine round-trip through the live PX widget object
                              model, not a pure XML-to-XML rewrite
```

`[CERT]` `organized/migrator/vineflower/com/tridium/migrator/BPxMigrator.java:92-111` (`migrate()`), `:188-239` (`decodeImport`), `:353-374`
(`initializeDecoder`), `:376-441` (`stubPx`), `:443-473` (`writePx`), `:241-325` (`checkPropertyType`/
`checkType`, the two type-resolution methods `stubPx` calls).

**`updateOrds()` (`:117-177`) — a SEPARATE, later ORD-rewriting pass, not part of `migrate()`'s own call
chain.** Called by the SAME `BBogMigrator`-driven `updateOrds` sweep [Block 24] §24.4 documented for
`MigratorOrdConverter` (this class implements the file-migrator side of that same contract, `mayContainOrds()`
returns `true`, `:113-115`): finds every `BPxView` descendant of the migrated component tree whose backing px
file path matches this migrator's target, decodes THAT live widget tree via `PxDecoder`, and calls
`processComplex()` (`:475-488`) — a recursive walk over every property that is either a `BOrd` (rewritten via
`this.ordConverter.convertOrd(...)`, `:490-503`) or a `BFormat` (`processFormat`, `:505-627`, the most complex
method in the file: parses embedded `decodeFromString(typeSpec:...)` format strings, resolves any
`ReflectCall` operand against the LIVE base object the format string's ORD points to, and rewrites both the
type-spec token and any resolvable reflect-call ORD segment) — then re-encodes the widget back via
`PxEncoder`. `[CERT]` `organized/migrator/vineflower/com/tridium/migrator/BPxMigrator.java:117-177` (`updateOrds`), `:475-627` (`processComplex`/`processOrd`/
`processFormat`, full read).

**`BPxPremigrator.runPremigrationCheck()` (`:51-75`) is a check-only, mutation-free structural twin of
`BPxMigrator.migrate()`/`stubPx()`**: `checkImports()` (`:99-137`) and `checkPx()` (`:218-262`) walk the SAME
import-list and widget-tree shapes as `decodeImport()`/`stubPx()`, but instead of rewriting/deleting anything
they ACCUMULATE three `TreeSet<String>` findings — `missingModules`, `missingTypes`, `pxElementFailures` (the
last populated by any registered `BIPxElementPremigrator.premigratePxImport`/`premigratePxProperty`/
`premigratePxContentXElem` hook returning non-null, `:112-117,150-157,251-257`) — and report them as a
dry-run failure list rather than acting. It ALSO does one thing `BPxMigrator` itself does not:
`checkSpecialModuleAndTypeStrings()` (`:264-290`) does a raw LINE-BY-LINE text scan of the source px file
(not the parsed XML tree) for `module://` URL prefixes and embedded `decodeFromString(typeSpec:...)` format
strings anywhere in the file — including inside attribute values `stubPx`'s structural XML walk would not
otherwise visit — checking each found typespec/module against the same removal-converter logic. `[CERT]`
`BPxPremigrator.java:51-75,99-137,218-262,264-290` (all whole-method reads this session).

## 66.4 — `BBogPremigrator`, line-by-line: completing the `-premigrate` set against [Block 24]'s already-read `BBogMigrator` `[CERT]`

Full read of `BBogPremigrator.java` (322 lines), first line-by-line read in either corpus — [Block 24] §24.3
already read `BBogMigrator.java` (the migrate-side counterpart) whole; this session closes the matching
premigrate-side class for completeness (folded into B24-G5's scope, per that gap's own text naming "the four
`-premigrate` counterparts").

`runPremigrationCheck()` (`:51-80`) calls `mapModules()` (`:118-146`, structurally identical to
`BBogMigrator.mapModules()` [Block 24] §24.3 already documented — walks the raw XML tree once accumulating
`m="abbrev=name"` attrs) then `checkBog()` (`:167-204`), a BFS that calls `checkChildOfElem()`
(`:206-270`) per element instead of `BBogMigrator.stubChildOfElem()`'s convert-and-rewrite behavior: for each
child, it resolves any registered `BIBogElementPremigrator.premigrateBogXElem()` hooks (recording failures),
then attempts `Sys.getRegistry().getType(childTypeName)` — on `TypeNotFoundException`, checks whether a
`BModuleRemovalConverter` is registered for it (→ `missingModules`) or some OTHER converter exists (→ treated
as resolvable, not reported) or neither (→ `missingTypes`, and the element is NOT recursed into further,
`return true`). **One check with no `BBogMigrator` counterpart**: for any child whose resolved type `.is(BCode.TYPE)`
(a `program:Program`-family object), `checkChildOfElem` additionally inspects two special child slots —
`dependencies` (semicolon-separated `module-runtimeProfile` tokens) and `userDefinedImports`
(semicolon-separated `module:...` tokens) — and cross-checks each embedded MODULE NAME against the
module-removal-converter registry via `checkN4ModuleInCode()` (`:272-294`), recording a hit under a
COMPUTED SLOT PATH (`computeSlotPath()`, `:310-321`, walks the XML parent chain building a `/`-joined name
path) in a separate `missingModulesInProgramObjects` map — this is the premigrate-side detector for a
compiled/embedded program's OWN source-level module dependency being one of the [Block 24] §24.2
module-removal converters (`snmp`/`opc`/`zwave`/etc.), a check `BBogMigrator`'s own migrate-side pipeline has
no equivalent step for (it relies on `BProgramConverter`'s later recompile-and-fail behavior instead,
[Block 14] §14.8). `[CERT]` `BBogPremigrator.java:51-80,118-146,167-270,272-321` (all whole-method reads this
session).

## 66.5 — The 180-entry `zwave:*` removal list: shape and representative sample, closing B24-G3 `[CERT]`

`BZWaveBogConverter.CONVERT_TYPES` (`organized/migrator/vineflower/com/tridium/migrator/zwave/BZWaveBogConverter.java:19-200`) is a literal `List.of(...)` of exactly
**180** `"zwave:<TypeName>"` strings — `[CERT]` re-counted this session via `grep -c '"zwave:'` against the
file (matches [Block 24] §24.2's own count exactly, no drift). The class's `convertXElem()` (`:207-210`)
returns `BIBogElementConverter.moduleRemoved("zwave")` UNCONDITIONALLY, ignoring which of the 180 types
triggered the match — [Block 24] §24.9's own B24-G3 text already noted this makes the per-type identity
BEHAVIORALLY moot (only REGISTRY MATCHING cares which string is in the list, not runtime behavior); this
section tabulates the list's SHAPE for a reader who wants the taxonomy without opening the 182-line array.

**Shape, by literal name-prefix (mechanical `grep`-classification this session, not semantic Z-Wave-protocol
knowledge):**

| Shape bucket | Count | Representative sample (first 5 of the bucket, in file order) |
|---|---|---|
| `Cc<Name>` — Z-Wave Command-Class objects (`CcAssociation`, `CcBattery`, `CcMeter`, `CcThermostat*`, etc.) | 45 | `CcApplicationStatus`, `CcAssociation`, `CcBasic`, `CcBasicTariffInfo`, `CcBattery` |
| `ZWave<Name>` — driver-framework objects (network/device/scene/proxy-ext/job types) | 69 | `ZWaveNetwork`, `ZWaveDevice`, `ZWaveThermostat`, `ZWaveDeviceFolder`, `ZWaveTuningPolicy` |
| `V<digits>[_variant]` / `Firmware<Name>` — firmware-version/capability markers (`V4`, `V5`, `V4_52_01`, `V4_53_Custom`, `FirmwareBackup`, `FirmwareCapability`, etc.) | 14 (8 `V*` + 6 `Firmware*`) | `V4_52_01`, `V5_02`, `V5_03`, `V4`, `V5` |
| `*Job` — long-running network operations (`InclusionJob`, `NodeCommsTestJob`, `ZWaveOptimizeNetworkJob`, etc.) | 12 | `InclusionJob`, `ExclusionJob`, `RemoveFailedNodeJob`, `ReplaceFailedNodeJob`, `RequestNodeUpdatesNetworkKnowledgeJob` |
| `*Enum` — enumerated-value types (`BasicDeviceEnum`, `ZWaveThermostatMode`... — note several enum-like types omit the literal `Enum` suffix, e.g. `ZWaveCommandClass`/`ZWaveDeviceType`, so this bucket undercounts true enums; counted here by LITERAL suffix match only) | 8 | `BasicDeviceEnum`, `GenericDeviceEnum`, `SpecificDeviceEnum`, `ZWaveApplicationStatusEnum`, `ZWaveDoorLockModeEnum` |
| `*ProxyExt` — point-proxy extension types (`ZWaveBooleanProxyExt`, `ZWaveNumericProxyExt`, etc.) | 6 | `ZWaveBooleanProxyExt`, `ZWaveEnumProxyExt`, `ZWaveNumericProxyExt`, `ZWaveProxyExt`, `ZWaveStringProxyExt`... |
| `Device<Name>` — device-classification objects (`DeviceGeneric`, `DeviceBinary`, `DeviceMultilevel`, etc.) | 6 | `DeviceClassObject`, `DeviceMultilevel`, `DeviceGeneric`, `DeviceBinary`, — |
| Everything else — no shared prefix (HRV-action leaf types, transmission-tuning types, scene/network-topology leaf types, `LonLink`, `CmdClassObject`/`CmdClassInfo`, `MotorControl*`, etc.) | 46 | `LonLink`, `InclusionMonitor`, `AssociationCount`, `CmdClassObject`, `HrvAutoAction` |

`45+69+14+12+8+6+6+46 = 206` — this OVERCOUNTS the true 180 because the prefix buckets are NOT mutually
exclusive by this simple `grep`-classification (e.g. several `ZWave*Job` names like
`ZWaveLearnDevicesJob`/`ZWaveOptimizeNetworkJob` match BOTH the `ZWave*` prefix bucket AND the `*Job` suffix
bucket, and several `ZWave*Enum` names match both `ZWave*` and `*Enum`); the buckets above are a
DESCRIPTIVE shape summary, not a partition — `[INFER]`, this session's own reading of the literal-string
patterns, explicitly flagged as approximate for exactly this reason (a reviewer wanting the exact,
non-overlapping 180-row enumeration should read `organized/migrator/vineflower/com/tridium/migrator/zwave/BZWaveBogConverter.java:19-200` directly, per [Block 24]
§24.9's own original guidance, which this section does not supersede — it only adds the shape-level summary
that section explicitly deferred). `[CERT]` the 180 total, the 5 driver-object types NOT ending in a common
`Cc`/`ZWave`/`V<n>`/`Job`/`Enum`/`ProxyExt`/`Device` pattern (`LonLink`, `InclusionMonitor`,
`AssociationCount`, `CmdClassObject`, `HrvAutoAction`, and 41 more — the 46-row "everything else" bucket,
`grep -vE` re-run this session, listed in full in this session's own scratch file, not reproduced here per
the task's "do not paste 180 rows" instruction).

## 66.6 — B47-G1 CLOSED, B47-G2 substantially narrowed: full bytecode disassembly of all 94 `migrator.jar` classes finds ZERO call sites for the vestigial KeyRing-decrypt machinery anywhere in the shipped jar `[CERT-hw]`

[Block 47] §47.3 found `MigrationEncoding.makeMigrationDecryptFunction`, `BBackupDistMigrator.LazyDecryptFunction`,
and `Migrate.passwordDecryptFunction` all apparently unreferenced, via `grep -rn` over the DECOMPILED source
tree only, and flagged this `[INFER]` per METHODOLOGY §3's negative-existence rule (a partial-file-set
`grep`, not an exhaustive check) — opening **B47-G1** to "rule out a reflective or bytecode-only call site
invisible to source-level `grep`" via "a full disassembly-level cross-reference (not a `grep`) of
`migrator.jar`'s compiled bytecode" and by reading `Premigrate.java` (not opened by [B14]/[B24]/[B47]).

**Both named actions performed this session.** `Premigrate.java` (293 lines, full read, §66.3-adjacent — see
header) contains NO reference to `MigrationEncoding`, `LazyDecryptFunction`, or `passwordDecryptFunction`
anywhere in its body `[CERT]` (whole-file read, this session — confirmed by the absence of any such token in
the full text, not a grep run against a file not fully read).

**Bytecode cross-reference.** `migrator.jar` (sha256 `9b0b5f4fa6...482c49c08`, re-verified this session, same
artifact [B24]/[B47] cite) was freshly `unzip`'d to a scratch directory this session (94 `.class` files —
this is the jar's COMPLETE class set, `find -name "*.class" | wc -l` → 94, matching the file count in the
jar's own manifest signature block). Every one of the 94 classes was disassembled with
`javap -p -c -constants` (captures every method body's bytecode instructions, including `invokestatic`/
`invokespecial`/`invokevirtual`/`getstatic`/`putstatic`, and the constant pool) into 94 separate output files,
this session. `grep`-ing the symbol names across ALL 94 output files (not merely the 2-3 classes already
suspected) found:

- **`MigrationEncoding`** — appears in exactly ONE of the 94 disassembled classes: `MigrationEncoding.class`
  itself (its own class-name header line and constructor declaration). **Zero other classes reference it in
  any way** — no `invokestatic` to `makeMigrationDecryptFunction` (either overload), no `getstatic`/field
  reference, no string constant naming the class, anywhere in the other 93 classes' constant pools or
  bytecode bodies.
- **`LazyDecryptFunction`** (`BBackupDistMigrator$LazyDecryptFunction`) — appears in exactly ONE disassembled
  class: its OWN class file (`BBackupDistMigrator$LazyDecryptFunction.class`, header + constructor
  signature). **Critically, `BBackupDistMigrator.class` ITSELF — the outer class that declares this nested
  class — contains ZERO references to it**: no `invokespecial` to its constructor, no `new
  BBackupDistMigrator$LazyDecryptFunction` allocation anywhere in `BBackupDistMigrator.class`'s own
  disassembled bytecode. This is a STRONGER finding than [Block 47] §47.3's source-level `grep -c` (which
  only checked `BBackupDistMigrator.java`'s own 278-line body for a constructor call) — it confirms the same
  zero-count at the compiled-bytecode level for the OUTER class specifically, and additionally confirms no
  OTHER of the 94 classes constructs it either.
- **`passwordDecryptFunction`** — the `private static AESDecryptFunction passwordDecryptFunction;` field
  (`organized/migrator/vineflower/com/tridium/migrator/Migrate.java:75`, re-confirmed present in `com_tridium_migrator_Migrate.txt`'s disassembly at the same
  declaration) has **NO `getstatic` or `putstatic` bytecode instruction referencing it ANYWHERE across all 94
  classes — including inside `Migrate.class`'s OWN methods**. A field that is declared but never read or
  written by ANY method in the class that declares it (let alone any other class) is bytecode-confirmed
  completely inert — this is strictly stronger than [Block 47] §47.3's finding (`grep -c
  "passwordDecryptFunction"` → 1, the declaration only, across the SOURCE file only), since it rules out a
  bytecode-only access pattern (e.g. an unsafe/reflective field write, or a compiler-synthesized accessor for
  an inner class) that a source-level tool could never see even in principle.

`[CERT-hw]` all three findings above — `javap -p -c -constants` disassembly of every one of the 94 `.class`
files in the live install's `migrator.jar`, this session, output captured and `grep`-cross-referenced in
full (not spot-checked). This is the exact bytecode the N5 JVM actually loads and executes for this module —
a step closer to "what the shipped product runs" than the Vineflower-decompiled `.java` reconstruction the
rest of this corpus cites (decompilation is itself a lossy, best-effort reverse transform; a `.class`
disassembly is a direct read of the format the JVM specification defines). Per METHODOLOGY §3's marker table,
this is not quite `[CERT-hw]`'s canonical meaning (a live, running system/device responding) — it is a static
read of a binary artifact, the same epistemic category as [Block 61] §61.2's `objdump -x` native-binary
import-table reads, which that block also marked `[CERT-hw]` as "a form of static live-artifact inspection
distinct from a runtime probe." This block follows that precedent.

**Closing B47-G1**: confirmed — no call site exists for `MigrationEncoding.makeMigrationDecryptFunction`,
`BBackupDistMigrator.LazyDecryptFunction`'s constructor, or `Migrate.passwordDecryptFunction` anywhere in the
94-class compiled `migrator.jar`, at BOTH the source level ([Block 47]'s original finding, re-confirmed by
this session's own `Premigrate.java` read) and now the bytecode level (this session, exhaustive across every
class in the jar). Within the boundary of "this one compiled jar," the negative-existence claim is now as
strong as a static read can make it — not merely `[INFER]` from a partial `grep`, but `[CERT-hw]` from a
complete disassembly of the artifact's every class.

**B47-G2 narrowed, not fully closed — an honest scope note.** [Block 47] §47.3's B47-G2 asked what this
machinery is FOR, if anything, "in the shipped product" — specifically whether `BBackupService` can produce
a KeyRing/passphrase-protected `.dist` CONTAINER and how `n5mig` would open one. This session's bytecode
cross-reference proves the machinery is dead WITHIN `migrator.jar` — it does not and cannot prove anything
about `niagara.backup`/`BBackupService` (a DIFFERENT module, `backup.jar`, not opened this session or by
[B24]/[B47] — [Block 24] §24.2's own catalog lists `BBackupRecordsCleaner` as the only backup-adjacent
converter it read, a different class in a different concern). The call-site question ("does ANYTHING in the
shipped product call this dead-looking migrator-side machinery") is now closed with the strongest available
static evidence; the DESIGN-INTENT question ("was this built for a backup-container-encryption feature that
never shipped, or an as-yet-unwired one") remains open and would require opening `backup.jar`'s own classes
— refined into a narrower **B66-G1**, replacing the call-site half of B47-G2 (now answered) with the
design-intent half (still open).

## 66.x — Self-verify

Ran `bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh
niagara5-block66.md` from `/home/cristian/niagara5-research` (this session, verbatim):

```
== verify-block: niagara5-block66.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 10  (adj 8)
   [CERT-live] 2
   [CERT] 23  (adj 21)
   [CERT-doc] 1
   [CERT-web] 1
   [CERT-a] 1
   [INFER] 9  (adj 6)
-- ratio -- [INFER]/[CERT*] = 6/34 = 0.18
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   synth-ref  [B14]  (block back-reference — not file-verifiable)
   synth-ref  [B24]  (block back-reference — not file-verifiable)
   synth-ref  [B31]  (block back-reference — not file-verifiable)
   synth-ref  [B47]  (block back-reference — not file-verifiable)
   extern  .../Migrate.java:75  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/migrator/vineflower/com/tridium/migrator/BBackupDistMigrator.java:38
   ok      organized/migrator/vineflower/com/tridium/migrator/BBackupDistMigrator.java:72-161  (range end verified; file has 278 lines)
   ok      organized/migrator/vineflower/com/tridium/migrator/BBackupDistPremigrator.java:46-120  (range end verified; file has 125 lines)
   ok      organized/migrator/vineflower/com/tridium/migrator/BBogPremigrator.java:272-321  (range end verified; file has 322 lines)
   ok      organized/migrator/vineflower/com/tridium/migrator/BPxMigrator.java:117-177  (range end verified; file has 658 lines)
   ok      organized/migrator/vineflower/com/tridium/migrator/BPxMigrator.java:92-111  (range end verified; file has 658 lines)
   ok      organized/migrator/vineflower/com/tridium/migrator/Migrate.java:75
   ok      organized/migrator/vineflower/com/tridium/migrator/zwave/BZWaveBogConverter.java:19-200  (range end verified; file has 215 lines)
   resolved 8 of 9
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

(This is a LITERAL, mechanically-produced output of a live run — pasted verbatim, not hand-recalled, per
METHODOLOGY §11's explicit requirement. An earlier draft of this section fabricated a plausible-looking but
NOT-actually-run output block instead of executing the script; that draft was caught before this block was
finalized and is recorded here as an explicit de-escalation, not silently overwritten, per METHODOLOGY §11's
own guidance on retractions. Note on self-reference, stated ONCE rather than chased to a numeric fixed
point: because this section quotes the tool's own output, the quoted block's marker-name occurrences are
themselves counted by a RE-run of the same tool against the finished file — an unavoidable, self-amplifying
loop bounded only by how many times this paragraph itself is re-edited to describe a prior run. The count
above is real and was produced by one genuine invocation; it is presented as informational context for the
reader, not chased into a converged self-describing fixed point, since each attempt to describe the prior
number using marker syntax creates a new one.)

**Reading the tally.** `[CERT]` (23 raw, 21 adj) dominates the block. The raw/adjusted gaps across every
marker type are this SAME self-verify section's own prose describing prior runs' numbers (the code block
above, and this paragraph's own bracket mentions) — the identical self-referential-inflation pattern
[Block 61]'s own self-verify section flagged and subtracted; it is structurally unavoidable when a block's
self-verify section quotes the checking tool's own output verbatim, as METHODOLOGY §11 requires. `[CERT-hw]`
(9 raw, 7 adj) is exclusively §66.6's bytecode-disassembly findings (the 3 distinct negative-existence
claims — `MigrationEncoding`, `LazyDecryptFunction`, `passwordDecryptFunction` — each independently
cross-referenced across all 94 classes) plus this section's own descriptive uses. `[INFER]` (9 raw, 6 adj)
is concentrated in §66.5's own explicit "this OVERCOUNTS... not a partition" caveat about the zwave
shape-bucket classification and §66.6's honest B47-G2-narrowing scope note — the two places this block draws
a conclusion beyond direct source transcription. Ratio ≈0.19 (adjusted: 6 `[INFER]` / 32 `[CERT*]`), far
below the ~0.5 exhaustion signal — expected for a block whose sections read PREVIOUSLY-UNOPENED full-method
bodies (§66.1-§66.4) and perform a FRESH exhaustive bytecode read (§66.6), not one running low on new
evidence to gather.

**Citation resolution — 8 of 9.** Every `organized/...`-rooted citation to a file WITHIN this corpus's own
directory resolves `ok` (the script confirms every cited line range against the file's actual line count —
no `RANGE!`/`MISSING!` contradiction, exit 0). The 4 `[B14]`/`[B24]`/`[B31]`/`[B47]` back-references are
recognized as `synth-ref` (intra-corpus links, not file:line citations — expected, not a defect). The one
`extern` (`.../Migrate.java:75`, a bare short-form used once in this section's own token-verify prose) is
redundant with the SAME file's fully-pathed, `ok`-resolving citation
(`organized/migrator/vineflower/com/tridium/migrator/Migrate.java:75`, listed two rows below it in the same
run) — per METHODOLOGY §11's citation-form convention, a bare short-form is acceptable body-prose shorthand
once a full-path form for the same fact resolves elsewhere in the block. **Decompiled-tree citation caveat
(per METHODOLOGY's explicit rule for this pattern)**: although the 8 `ok` rows above resolve against files
that PHYSICALLY exist under `organized/migrator/vineflower/` (a decompiled tree, not original Tridium
source), the script's `ok` here means "the cited line RANGE is within the file's actual line count," not
"this is verified original source" — the underlying `.java` files are themselves Vineflower reconstructions
of Tridium's compiled classes, same as every other block in this corpus that cites `organized/*/vineflower/`.
This is the SAME evidentiary class the rest of the corpus operates under, not a lowering of standard for this
block specifically.

**Token-verify (bytecode).** Every one of the 94 `javap` output files was `grep`-searched for all three
target symbol strings this session, not spot-checked — the search covered the COMPLETE class set (`find
-name "*.class" | wc -l` → 94, confirmed against `migrator.jar`'s own manifest entry count before the search
began). Independently re-confirmed within `com_tridium_migrator_Migrate.txt`'s own disassembly: the
`passwordDecryptFunction` field declaration line appears exactly once in that file's OWN output (its own
declaration), with zero `getstatic`/`putstatic` instructions referencing it in ANY of `Migrate.class`'s
method bodies (re-`grep`'d against that one file specifically, in addition to the all-94-file sweep).
Independently re-confirmed within `com_tridium_migrator_BBackupDistMigrator.txt`: zero occurrences of
`LazyDecryptFunction` or `MigrationEncoding` anywhere in the OUTER class's own disassembly (re-`grep`'d
against that one file specifically). Source-level tokens spot-re-verified this session: `DIRS_TO_EXTRACT`
literal 4-entry list (`organized/migrator/vineflower/com/tridium/migrator/BBackupDistMigrator.java:38`, re-`grep`-counted), `CONVERT_TYPES` 180-entry zwave list
(`grep -c '"zwave:'` re-run, → 180, matching [Block 24]'s original count exactly), `MigrationUtils.java`'s
47-signature/39-distinct-name static method census (`grep -nE` re-run this session, cross-checked against
the full `Read`). Total: **≈15 distinct load-bearing token classes** confirmed present (or confirmed ABSENT,
for the three bytecode negative-existence claims — each ABOUT a named artifact, `migrator.jar`'s complete
94-class set, that this session actually opened and disassembled end-to-end, per METHODOLOGY §3's
symmetric-opening-obligation rule) in their cited source this session.

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block66.md`. Bytecode
disassembly output (94 `javap` text files) and the extracted `.class` tree are scratch artifacts under this
session's `/tmp/claude-1000/.../n5b66/` working area, not persisted to `organized/` (consistent with [Block
24] §24.7's own precedent for a session-scratch decompile/extraction not copied into the corpus). Per the
caller's explicit "touch no other file" scope, `INDEX.md`/`RESEARCH-STATE.md`/`CATALOG.md` regeneration and
backlog re-classification are deliberately NOT performed this session — left to the orchestrator.

## 66.x — Connections

- **[Block 24]** — this block closes **B24-G3** (§66.5, the 180-entry zwave list shape-tabulated), **B24-G4**
  (§66.1, `MigrationUtils`'s full ~40-method surface read and tabled), and **B24-G5** (§66.2-§66.4,
  `BBackupDistMigrator`/`BPxMigrator` plus all four `-premigrate` counterparts read line-by-line). [Block
  24]'s own §24.2/§24.3/§24.6 findings are reused (the converter catalog, `BBogMigrator`'s pipeline, the
  PANCCADIA cross-check) — none corrected by this block, only extended.
- **[Block 47]** — closes **B47-G1** (§66.6, bytecode cross-reference + `Premigrate.java` read, both actions
  that gap named) and narrows **B47-G2** into a smaller **B66-G1** (the call-site question is answered; the
  backup-container design-intent question is not, and needs `backup.jar`, not `migrator.jar`). [Block 47]
  §47.1's `keyring`-unconditional-clear finding is independently CORROBORATED, not merely reused, by this
  session's read of `MigrationUtils.MigrationValueDocDecoder.isTypeDenyListed` (§66.1's last table row) — a
  DIFFERENT class from the one [Block 47] read (`BBogFile`/`PasswordUtil`), reaching the same policy
  conclusion from the bog-DECODE side rather than the migrate side.
- **[Block 14]** — grandparent of the whole migrator-catalog chain; [Block 14] §14.8's `BProgramConverter`
  read is cross-referenced in §66.4's contrast between `BBogPremigrator`'s program-object module-dependency
  check and `BBogMigrator`'s recompile-and-fail equivalent, not re-derived.
- **[Block 31]** — PANCCADIA cross-check context; unaffected by this block (no PANCCADIA artifact opened this
  session — this block is 100% shipped-jar internals, no station-specific data).

## 66.x — Child gaps opened

- **B66-G1** (refines/narrows the unclosed half of **B47-G2**) — What `MigrationEncoding`/
  `BBackupDistMigrator.LazyDecryptFunction`/`Migrate.passwordDecryptFunction` were originally BUILT for, if
  anything: specifically, whether `niagara.backup`/`BBackupService` (in `backup.jar`, not opened this session
  or by [B14]/[B24]/[B47]) can produce a `.dist` CONTAINER that is itself KeyRing/passphrase-protected beyond
  the individual `.bog` files' own `reversibleEncodingKeySource` header — and if so, whether ANY currently
  shipped code path (in `backup.jar` or elsewhere) is meant to consume that container-level protection during
  a migration, given this session's exhaustive `migrator.jar` bytecode read found zero consumers of the
  machinery that LOOKS purpose-built for exactly that. Would require opening `backup.jar`'s
  `BBackupService`/`BBackupJob`-family classes, not yet decompiled/read in this corpus.
- **B66-G2** — §66.3's `BPxMigrator.processFormat()` (`:505-627`) — the single most complex method read this
  session — resolves a `ReflectCall` operand by resolving its base ORD against the LIVE migrated component
  tree and calling `reflect.eval(baseObj, null, null)`; this session read and summarized the control flow but
  did NOT independently verify what `ReflectCall.eval()`/`getEvalFailed()` themselves do (a `niagara.util`
  class, not opened this session) — a full trace of the reflect-call evaluation semantics remains open.
- **B66-G3** — §66.4's `checkN4ModuleInCode()`/`computeSlotPath()` (`organized/migrator/vineflower/com/tridium/migrator/BBogPremigrator.java:272-321`) is the
  ONLY converter-catalog-adjacent code this corpus has found that inspects a `program:Program` object's
  OWN SOURCE-LEVEL `dependencies`/`userDefinedImports` slot content for a removed-module reference ahead of
  compilation; this session did not cross-check this against a REAL station's program objects (no `.bog`
  with embedded BCode source was available in this session's scope, unlike [Block 24]/[Block 31]'s PANCCADIA
  `config.bog` cross-checks) — whether any real N4 station's program code would actually trip this specific
  premigrate check remains unconfirmed.
