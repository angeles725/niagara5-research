# Block 14 — N4→N5 station migration: n5mig and the migrator SPI

> Research of **`n5mig`**, the N4→N5 station-migration command-line tool, and the migrator SPI it runs on
> (`migration.jar` core interfaces + `migrator.jar` converter catalog + `propMigration.jar` declarative
> prop-diff helpers). Covers: the `n5mig.exe` launcher and its embedded `Migrate` CLI usage/options, the
> `BIFileMigrator`/`BIBogElementConverter`/`ConverterRegistry`/`MigratorRegistry` SPI architecture, the
> shipped converter catalog (58 registered types in `migrator.jar`), how a `javax.baja.*`→`niagara.*` bog
> typespec rename is carried out (`BTypeSpecConverter`), how the `app` module removal is executed
> (`BAppBogConverter`, closing BC-02), how N5's mandatory program-object code-signing (BC-29) is enforced
> during migration by `BProgramConverter` (recompile + import-rewrite + signing-cert check), and how an
> UNREGISTERED third-party module's bog elements are handled (`BModuleRemovalConverter`/
> `BPxRemovalConverter` fallback). Also identifies `driverUpgrade.jar` as a DISTINCT, non-`n5mig` tool
> (a generic "upgrade to new module" driver wizard, not part of the N4→N5 path) and cross-compares against
> the prior corpus's AX→N4 migrator architecture (`niagara-research` [B405]). Does **not** cover: an actual
> `n5mig` execution/run against a real N4 station backup (no N5 station backup available this session —
> flagged as a requires-execution child gap), the full 58-converter catalog's individual behavior (only the
> module-removal/typespec/program converters were read in full), or `com.tridium.migrator.MigratorOrdConverter`
> / `MigratorTypeResolver` internals beyond their registry call sites.
>
> Subject version: Niagara **5.0.0.28 (Beta)** install at `/mnt/c/Program Files/Niagara/5.0.0.28` (binaries)
> and `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules` (jars) — same install [B1]-[B4], [B10]
> read. `migration.jar` sha256 `ebce515de72632955899846b296b08a2ee3045c1422397ce6b0715c80482c49c`;
> `migrator.jar` sha256 `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08`; `propMigration.jar`
> sha256 `5ee675c6809354f234b2d0c7ad1826837689a51a3603b6fa1b7de02ca5f4f031`; `driverUpgrade.jar` sha256
> `10d2dc712fc8c38500e8bcff9b90a2f099a6e64bc2a62ef43abfe7d3fe23e775`; `n5mig.exe` sha256
> `95b5deae0afc4a0b68361f82d4696398691e4b2130a285dce471ab3aa5c97e46`.
>
> Sources: `n5mig.exe` (PE32+ launcher, `strings` census); `migration.jar`, `migrator.jar`,
> `propMigration.jar`, `driverUpgrade.jar` module.xml + class inventory (`python3 zipfile`); Vineflower
> 1.12.0 decompilation of `migration.jar` and `migrator.jar` into `/tmp/claude-1000/n5b14/decompiled/`
> (`niagara/migration/*.java`, `com/tridium/migrator/**/*.java`); `docDeveloper.jar`
> `doc/upgrade/upgradingToN5.html` (extracted text at
> `/tmp/claude-1000/n5b10/doc__upgrade__upgradingToN5.html.txt`, preserved by [B10]); `niagara-research`
> [B405] (`BOG Version Migration` — the AX→N4-era migrator, read for cross-comparison, not re-decompiled
> here).
>
> Method: `strings`/PE inspection of the exe launcher; `zipfile` listing + `module.xml` parse of all four
> migration-family jars; Vineflower decompilation of the two core jars, full read of `Migrate.java` (CLI),
> `MigratorRegistry.java`, `ConverterRegistry.java`, `BModuleRemovalConverter.java`, `BTypeSpecConverter.java`,
> `BAppBogConverter.java`, `BProgramConverter.java` (partial — signing/import-rewrite section), and the
> `BBogMigrator.java` field/method inventory (not fully read — a structural census, not a full read).
> Markers: `[CERT]` local primary source (`file:line`, resolvable — decompiled tree is under this session's
> `/tmp` scratch, so citations to it are `extern`-classified by any mechanized `verify-block.sh` run; see
> METHODOLOGY §11 "decompiled-tree blocks" clause) · `[CERT-doc]` the shipped `docDeveloper.jar` doc,
> cited by zip-entry path + section (same extern convention as [B10]) · `[INFER]` deduction.
>
> Build/porting layer. Connects [B10] (`upgradingToN5.html` §n5mig / §"New Requirement for Program Objects
> in Niagara 5" — this block closes child gap **B10-G5**; also BC-02 `app` module removal and BC-29
> program-object signing, both confirmed HERE at the implementation level), [B4] (docDeveloper.jar corpus
> census), `niagara-research` [B405] (AX→N4-era migrator SPI — the direct architectural ancestor of the
> SPI documented here).
>
> **Type:** `mixed` — §14.1-§14.7 are evidence blocks reading the shipped jars/exe/doc; §14.8 draws
> `[INFER]` conclusions cross-applying this evidence against `niagara-research` [B405] (a PRIOR corpus's
> block, not this block's own `[CERT]` sources) and against our three live N4 modules (ColdRoomPan, CompPan,
> DashboardPan) from [B10]'s worktree read — both cross-block syntheses, the declared `mixed` trigger.

---

## 14.1 — `n5mig.exe`: a thin native launcher for `com.tridium.migrator.Migrate` `[CERT]`

`n5mig.exe` is a **101,408-byte PE32+ (x86-64) console launcher**, not a JVM itself — it is the same
native-launcher pattern as `wb.exe`/`station.exe`/`niagarad.exe` in the same `bin/` directory (all resolve
a module + entry class and start the shared `nre`/JVM runtime). Its embedded manifest resource strings
identify:

| Field | Value | Evidence |
|---|---|---|
| Launcher target | `migrator:com.tridium.migrator.Migrate` | `strings n5mig.exe` — the launcher-manifest `<module>:<mainClass>` pairing |
| PE assembly identity | `Tridium.Niagara.MigrateN4toN5`, version `5.0.0.96`, `processorArchitecture="amd64"` | same `strings` output (embedded Win32 manifest XML) |
| PE description | `N4 to N5 Migration Tool` | same |

`Migrate.nreMain(String[])` is the JVM entry point the launcher invokes (`nreMain` is the Niagara
convention for a launcher-callable static entry, distinct from a plain `main`).
`[CERT]` `n5mig.exe` strings output; `Migrate.java:101` (`public static void nreMain(String[] rawArgs)`).

`n5mig` ships ONLY as this compiled `bin/` executable — no `.bat`/`.properties`/`.ini` sidecar file exists
next to it in `bin/`, and no `n5mig`-named entry exists anywhere inside `docDeveloper.jar`'s jar itself (the
tool is documented in prose, in `upgradingToN5.html`, not shipped as doc-jar content).
`[CERT]` directory listing of `/mnt/c/Program Files/Niagara/5.0.0.28/bin` (no other `n5mig*` file) and of
`/mnt/c/Program Files/Niagara/5.0.0.28` (recursive `find -iname "*n5mig*"` returns only the one exe). This
resolves **B10-G5**: `n5mig` is a compiled bin/ tool backed by the `migrator` module, not a docDeveloper.jar
artifact.

## 14.2 — `Migrate` CLI: usage, arguments, options `[CERT]`

The embedded `USAGE` constant (`Migrate.java:62`) is the CLI's own `-help` text, read in full:

```
USAGE:
  n5mig [options] <source> [target]
```

| Element | Detail | `[CERT]` |
|---|---|---|
| `source` | Most commonly a **4.15-versioned station backup distribution file** (`.dist`). Alternatively an individual `.bog`, `.palette`, `.px`, `.ntpl`, or `.napl` file (versioned at 4.15), or a source DIRECTORY (requires `target` + `-type`). | `Migrate.java:62` (USAGE string) |
| `target` | Station name / destination dir; for a `.dist` source, output lands under `niagara_user_home/stations/<name>` by default. For individual file types the default target differs per extension (`.bog`/`.palette`→`niagara_user_home`, `.px`→`niagara_user_home/shared`, `.ntpl`→`.../templates`, `.napl`→`.../applicationTemplates`). | same; `Migrate.java:143-149` (the `switch` on `srcExt` implementing exactly this default-target table) |
| `-help` | print USAGE | `Migrate.java:62,105-108` |
| `-o` | overwrite an existing target | `Migrate.java:62,83` (`overwrite` field) |
| `-log:<level>` | `ALL|FINEST|FINER|FINE|CONFIG|INFO|WARNING|SEVERE|OFF` | `Migrate.java:62` |
| `-version` (arg key `ver`) | print version info | `Migrate.java:62,103-104` |
| `-premigrate` | **dry-run**: runs premigration checks only, emits an HTML report per source file, makes NO conversion | `Migrate.java:62,118,188-`  (`processSourceToTarget` branches into `Premigrate` when this flag is set) |
| `-type:<fileExt>` | required when `source` is a directory; filters which extension is processed (`dist\|bog\|palette\|px\|ntpl\|napl`) | `Migrate.java:62,122-123,167-168` |
| `-filePassPhrase:<phrase>` | (advanced) explicit passphrase for the migrated bog's encryption — USAGE text itself warns "THIS MAY NOT BE SECURE" (shell history exposure) | `Migrate.java:62` |
| `-keepTemp` | do not clean up temp dirs after the run | `Migrate.java:62` |
| `-showSystemLogs` | show ALL logger output, not just migrator-scoped | `Migrate.java:62` |

**Explicit N4 version bound in the shipped USAGE text itself: "a 4.15 versioned station backup distribution
file."** `n5mig`'s documented input contract is N4 **build 4.15** specifically, not "any N4" — consistent
with N5 5.0.0.28 being the release that immediately follows the 4.15 line. `[CERT]` `Migrate.java:62`
(literal USAGE substring).

## 14.3 — The migrator SPI: two-registry design, unchanged in shape from the AX→N4 migrator `[CERT]` `[INFER]`

The core `migration.jar` module (description `"N4 Migration Core"`, preferred symbol `mig`) declares 10
types under package **`niagara.migration`** (not `com.tridium.migration`): `BFileMigrator`,
`BFilePremigrator`, `BIBogElementConverter`, `BIBogElementPremigrator`, `BIFileMigrator`,
`BIFilePremigrator`, `BIPxElementConverter`, `BIPxElementPremigrator`, `BModuleRemovalConverter`,
`BPxRemovalConverter`, plus the two static registry classes `ConverterRegistry` and `MigratorRegistry`
(registries are plain `final` utility classes, not separately-typed `BObject`s, so they carry no
`<type>` entry). `[CERT]` `migration.jar` `META-INF/module.xml` (`<types>` block, 10 entries).

**Two-registry design, identical in SHAPE to `niagara-research` [B405]'s documented AX→N4 migrator:**

| Registry | Scope | Discovery mechanism | Fallback |
|---|---|---|---|
| `MigratorRegistry` | **file-level** — which `BIFileMigrator` handles a given file (by exact filename / regex pattern / extension / directory name) | `Sys.getRegistry().getConcreteTypes(BIFileMigrator.TYPE.getTypeInfo())` — i.e. every module's `module.xml`-registered concrete `BIFileMigrator` type is auto-discovered, NO separate SPI file/annotation | `new BFileMigrator()` (plain byte-copy) when nothing matches |
| `ConverterRegistry` | **element/type-level** — which `BIBogElementConverter`/`BIPxElementConverter`/premigrator handles a given bog/px `TypeSpec` string (`"module:Type"`) | `Sys.getRegistry().getConcreteTypes(BIBogElementConverter.TYPE.getTypeInfo())` (and the Px/premigrate siblings) — same auto-discovery pattern | `BModuleRemovalConverter`/`BPxRemovalConverter` when `Sys.getRegistry().getModule(moduleName)` throws `ModuleNotFoundException` |

`[CERT]` `MigratorRegistry.java:47` (`getConcreteTypes` call), `MigratorRegistry.java:169-208` (`lookup()`
priority: dir → exact file → pattern → extension → default); `ConverterRegistry.java:32-39`
(`initialize()` — four parallel `getConcreteTypes` calls for bog-converter / px-converter /
bog-premigrator / px-premigrator); `ConverterRegistry.java:146-176` (`getElementHandlers()` — the
`ModuleNotFoundException` → `BModuleRemovalConverter`/`BPxRemovalConverter` fallback, §14.5 below).

**The SPI registration mechanism is the ORDINARY Niagara module-type registry, not a distinct annotation or
manifest.** A module registers a migrator/converter by declaring the class in its OWN `module-include.xml`
`<types>` block as a concrete implementation of `BIFileMigrator`/`BIBogElementConverter`/etc. — the SAME
`<type class="..." name="..."/>` mechanism [B1] documented for ordinary Niagara component types. There is
no `META-INF/services` file, no `@Migrator`-style annotation: `@NiagaraType` + `Sys.loadType()` (the
standard type-registration boilerplate, [B1]) is the entire contract. `[CERT]` every converter class read
this session (`BModuleRemovalConverter.java:15-18`, `BTypeSpecConverter.java:22-25`,
`BAppBogConverter.java:14-17`, `BProgramConverter.java:45-48`) carries only `@NiagaraType`/`Sys.loadType`,
no other annotation; cross-referenced against `migrator.jar`'s own `module.xml` `<types>` block (§14.4)
which IS the registration surface.

**A `migrator.properties` file at `$NIAGARA_USER_HOME/etc/migrator.properties` can OVERRIDE the
programmatic file/pattern/extension/directory declarations** (property keys `<TypeName>.files`,
`.patterns`, `.extensions`, `.directories`, comma-separated) — read once at `MigratorRegistry.initialize()`,
absent-file is non-fatal (logged INFO, falls through to the programmatic declarations).
`[CERT]` `MigratorRegistry.java:34-49` (props load) and `199-217` (`getPatterns()` — the props-vs-programmatic
merge logic, props win when present).

**`[INFER]`: this two-registry shape is a direct architectural carry-over from the AX→N4-era migrator**, not
a new N5 design. `niagara-research` [B405] documents the SAME `MigratorRegistry`/`ConverterRegistry` split
(four static `Map<String,TypeInfo>` fields, file→pattern→extension→directory priority, `BFileMigrator`
default-copy fallback) for the AX→N4 tool, sourced from `javax/baja/migration/MigratorRegistry.java` in that
prior corpus's decompiled tree. The only structural difference this session found: the CORE interface
package moved from **`javax.baja.migration`** (AX→N4 era, per [B405]) to **`niagara.migration`** (N5 era,
this block) — the SAME `javax.baja.*`→`niagara.*` rename [B10] BC-01/BC-30 and this block's §14.6 document
for ordinary component types, applied here to the migrator SPI's own interfaces. The `com.tridium.migrator`
CONVERTER package (module-specific converters, as opposed to the core SPI) is unchanged across both eras —
[B405]:32 cites `com/tridium/migrator/BBogMigrator.java` for the AX→N4 tool at the SAME package path this
block's `migrator.jar` uses for the N4→N5 tool.

## 14.4 — The shipped converter catalog: 58 registered types in `migrator.jar` `[CERT]`

`migrator.jar` (description `"N5 Migration Tool"`, preferred symbol `n4m` — note the symbol still says
`n4m`, an un-updated legacy artifact of the AX→N4 tool's naming) declares **58** `<type>` entries in its
`module.xml`. `[CERT]` `migrator.jar` `META-INF/module.xml` (`<types>` block; counted via `re.findall` over
the raw XML — 58 matches).

| Category | Count | Members (class, abridged) |
|---|---|---|
| Core file/dist migrators | 8 | `BackupDistMigrator`/`Premigrator`, `BogMigrator`/`Premigrator`, `MigrationBogFile`, `ProvisioningNiagaraMigrator`, `PxMigrator`/`Premigrator` |
| Generic bog-element converters | 2 | `TypeSpecConverter` (§14.6), `ServerCertificateHealthToCertificateHealthBogConverter` |
| Program-object converters | 3 | `ProgramConverter` (§14.7), `ProgramModuleConverter`, `ProgramServiceConverter` |
| UI/wizard classes (not converters) | 2 | `MigratorProcessStreamPane`, `MigratorWbTool` |
| Utility/cleanup | 2 | `BackupRecordsCleaner`, `KeytabFileRemover` |
| Driver/protocol-specific bog converters | ~26 | BACnet ×5 (incl. `BacnetOwsToAwsBogConverter` — OWS→AWS family swap, run BY `n5mig`, distinct from `driverUpgrade.jar`'s wizard, §14.8), OPC/OPC-UA ×5, cloudLink ×7, jetty ×2, kerberos ×2, video ×2, mobile ×2, snmp/nSnmp ×2, zwave, commercialCooking, abstractMqttDriver, oracle, lonIp, weather, weatherUnderground ×1 each |
| App/web/misc removal or rename converters | 5 | `AppBogConverter` (§14.5), `WebBogConverter`, `TemplateFileMigrator`, `DataPolicyConverter` (tagDictionary), `CurDisTagConverter` (haystack), `GauthToTotpAuthBogConverter`/`PxElementConverter`, `TunnelServiceConverter` |

`propMigration.jar` (a SEPARATE, SMALLER jar, description not read this session but inferable from its 8
declarative converter classes: `BNewType`, `BNumPropNameChange`, `BOrdProps`, `BOrigSimple`,
`BPropFacetsChange`, `BPropFlagsChange`, `BPropNameChange`, `BPropRemove`, `BPropValueChange`,
`BSimpleEncodingChange`, `BTypeNewName` + matching `.converters.B*Converter` classes) is a DECLARATIVE
prop-diff DSL — a data-driven "this property changed shape" descriptor set, distinct from the imperative
`BIBogElementConverter` classes in `migrator.jar`. `[CERT]` `propMigration.jar` zip listing (31 entries,
`com/tridium/propMigration/*.class` + `.../converters/*.class` 1:1 pairs). Not decompiled this session
(zip-listing evidence only) — named as a §14.9 child gap.

## 14.5 — Unregistered third-party module handling: `BModuleRemovalConverter` fallback `[CERT]`

When `ConverterRegistry.getElementHandlers()` looks up a `"module:Type"` string and finds no registered
converter AND `Sys.getRegistry().getModule(moduleName)` throws `ModuleNotFoundException` (the module is not
present/registered in the N5 install running `n5mig`), it synthesizes a `BModuleRemovalConverter` (for bog
elements) or `BPxRemovalConverter` (for px elements) ON THE FLY, keyed to that exact module name.
`[CERT]` `ConverterRegistry.java:160-176`.

`BModuleRemovalConverter.convertXElem()` REMOVES the object outright: it logs a SEVERE
`moduleRemovalConverter.removingObject` message (naming the object and its typespec) and returns
`BIBogElementConverter.moduleRemoved(myModule)` in place of the original XML element. `[CERT]`
`BModuleRemovalConverter.java:50-58`.

**This means: for a module NOT reinstalled/registered on the target N5 machine at migration time, `n5mig`
does not fail or skip — it silently strips every bog object of that module's types from the migrated
station**, replacing each with a `moduleRemoved` marker element (`BBogMigrator`'s `nullElem()` pattern per
`niagara-research` [B405]'s equivalent AX→N4 documentation, `[INFER]` cross-block — this block did not
independently re-read `BBogMigrator.nullElem()`'s literal XML shape, only its call site in the field/method
census, §14.6 below). **If the module IS present/registered** (i.e. our modules were recompiled against N5
and installed before running `n5mig`), `getElementHandlers()` returns an EMPTY converter list for any
typespec with no specific registered converter, and `BTypeSpecConverter.convertXElem()` (§14.6) finds
`Sys.getType(typespecValue)` resolves without exception — so the bog element passes through UNCHANGED. `[CERT]`
`ConverterRegistry.java:152-179` (empty-list return path when the module resolves); `BTypeSpecConverter.java:38-51`
(the `Sys.getType()` try — no exception ⇒ no `convertTypeSpec()` call ⇒ `x` returned as-is).

**Direct implication for our modules (ColdRoomPan, CompPan, DashboardPan — [B10]'s worktree):** `coldRoomPan:*`,
`compPan:*`, `dashboardPan:*` typespecs are NOT in the 58-type catalog above (none of those module names
appear in `migrator.jar`'s `<types>` list) — third-party modules get NO custom converter by design; their
survival through `n5mig` depends ENTIRELY on whether the module itself is present in the N5 install's
registry at migration time, not on any per-type migration logic. This is `[INFER]` (a deduction from the
registry code's control flow, not a literal statement in any source) but is a DIRECT, mechanical reading of
the fallback branch cited above, not a probabilistic guess.

## 14.6 — `javax.baja.*` → `niagara.*` typespec rename: `BTypeSpecConverter` `[CERT]`

`BTypeSpecConverter` (registered for `baja:TypeSpec` bog elements) is the GENERIC handler for any bog `v=`
attribute holding a typespec string. On each such element it tries `Sys.getType(typespecValue)` against
the RUNNING N5 registry; a `ModuleException` or `TypeException` (the typespec's module or type does not
resolve under N5) triggers `convertTypeSpec()`, which re-queries `ConverterRegistry.lookupConverters()` for
that exact typespec and chains any found converters' `newTypeSpec()` return values — OR, if the resolved
converter is itself a `BModuleRemovalConverter`, strips the `v=` attribute entirely (§14.5's removal path,
applied here to a typespec REFERENCE rather than a component INSTANCE). If NO converter is found at all,
the `v=` attribute is likewise stripped with a WARNING (`typeSpecConverter.notFound`).
`[CERT]` `BTypeSpecConverter.java:38-75`.

This is the GENERIC mechanism `BC-01`/`BC-30` ([B10]) generalize INTO: `javax.baja.log.Log` →
`java.util.logging.Logger` and `baja.Complex#getFacets` → `baja.Complex#getSlotFacets` are SPECIFIC renames
documented in the shipped doc prose; `BTypeSpecConverter` + the registered `.newTypeSpec()` converters (not
individually enumerated in this block — a §14.9 child gap) are the RUNTIME MACHINERY that would apply such
renames to a real station's `.bog` typespec references during an actual `n5mig` run.

## 14.7 — `app` module removal (BC-02) executed by `BAppBogConverter` `[CERT]`

`BAppBogConverter` (registered convert-types: `app:App`, `app:AppContainer`, `app:AppFolder`,
`app:BajaScriptWebApp`, `app:WebApp`) implements [B10]'s BC-02 ("`app` module removed... manual removal, or
automatic via `n5mig` station migrator") with ONE special case:

- `app:AppContainer` **with children** (`xmlElement.elems("p").length != 0`) is CONVERTED, not removed —
  retyped in place to `baja:Folder` (`elem.setAttr("t", "baja:Folder")`), preserving its child objects, then
  recursed into so any nested `app:*` type is itself removed/converted.
- `app:AppContainer` with NO children, and every OTHER `app:*` type (`App`, `AppFolder`,
  `BajaScriptWebApp`, `WebApp`), unconditionally: `BIBogElementConverter.moduleRemoved("app")`.

`[CERT]` `BAppBogConverter.java:27-44` (top-level `convertXElem`), `46-64`
(`convertAppContainerToAFolderType`/`updateAppContainerForMigration` recursive-child handling).

This is a CONCRETE, single-converter example of the §14.5 module-removal pattern applied to a module Tridium
itself decided to drop, rather than to a third-party module absent from the target — same mechanism
(`BIBogElementConverter.moduleRemoved`), two different TRIGGERS (explicit per-type converter here vs. the
"module not found in registry" fallback for an unrecognized third-party type).

## 14.8 — Program-object recompilation + code signing (BC-29) executed by `BProgramConverter` `[CERT]`

`BProgramConverter` (registered for `program:Program`) is the runtime enforcement of [B10] BC-29 ("program
object signing now mandatory by default... valid code-signing cert configured... before `n5mig`"):

1. **Import/source rewrite** (`fixProgram`/`fixImports`/`fixCode`, called unconditionally for every
   `program:Program` bog element): rewrites `javax.baja.*` imports to `niagara.*`
   (`if (importStatement.startsWith("javax.baja.")) importStatement = "niagara." + ...`), applies a table
   of SPECIFIC class relocations (`MIGRATED_CLASSES_IMPORTS` — e.g. `com.tridium.nre.firewall.IpProtocol`,
   `com.tridium.security.BServerCertificateHealth`→`niagara.security.BCertificateHealth` via
   `RENAMED_CLASSES`), a package-level rename table (`UPDATED_IMPORTS` — e.g. `niagara.chart`→
   `niagara.chart.data`, `niagara.query`→`niagara.collection`), a raw string replacement table
   (`IMPORT_REPLACEMENTS` — `com.tridium.json`→`org.json`, `java.security`→`niagara.nre.util`), and a
   method-reference replacement (`AccessController.doPrivileged`→`SecurityUtil.doPrivileged`).
   `[CERT]` `BProgramConverter.java:55-88` (the six static rewrite maps), `220-260` (`fixProgram`/`fixImports`
   applying them).
2. **Code-signing cert check + recompile**: reads `BCodeSigningOptions.make().getSigningCert()` (the SAME
   Workbench→Tools→Options→Code Signing setting [B10]'s doc prose names), prompts for the cert's password
   up to 3 times (`CODE_SIGNING_PASSWORD_SUPPLIER`), and on success builds a `RecompileTool` that
   `recompile()`s the program's Java source in place. `[CERT]` `BProgramConverter.java:127-171`
   (`BCodeSigningOptions`/`Compiler.checkSigningKey`/`RecompileTool` construction), `176-182`
   (`recompiler.recompile(program)`).
3. **No valid cert → the program is left UNCOMPILED, not blocked**: `unverifiedCodeSigningCertSpecified`
   branches to `program.getCode().setClassFile(BBlob.DEFAULT)` — the migrated bog KEEPS the source text but
   its compiled classfile is cleared to empty, meaning the migration itself still SUCCEEDS (does not abort
   the whole run) but the resulting program object will not execute until manually recompiled/signed later
   in Workbench. A WARNING/SEVERE is logged and a converter-level completion message is queued
   (`BBogMigrator.addConverterMessage`) so the operator sees it in the migration report.
   `[CERT]` `BProgramConverter.java:109-124,173-174` (the `unverifiedCodeSigningCertSpecified` branch and its
   `setClassFile(BBlob.DEFAULT)` fallback).
4. **`-premigrate` dry-run pre-checks the SAME cert requirement**, via `premigrateBogXElem()`, BEFORE any
   real migration: it validates the configured signing alias exists in the keystore
   (`SigningUtil.isValidSigningCert`) and returns a warning STRING (surfaced in the premigrate HTML report,
   §14.2) rather than performing any conversion. `[CERT]` `BProgramConverter.java:193-218`.

This directly resolves the open half of [B10]'s BC-29 row: the doc prose said WHAT is required
("valid code-signing cert... before migrating"); this block shows HOW `n5mig` enforces and gracefully
degrades from it (`BProgramConverter`'s explicit-cert-else-blank-classfile fallback) rather than hard-failing
the whole migration run.

## 14.9 — `driverUpgrade.jar`: a distinct, NON-`n5mig` tool `[CERT]`

`driverUpgrade.jar` (description `"Niagara tool to support upgrades to new module"`, preferred symbol
`dupg`) is A DIFFERENT TOOL from `n5mig`/`migrator.jar`: it is a `BUpgradeTool` WIZARD (`BFirstStep`,
`BSecondStep`, `BThirdStep`, `BConnectStep`, `BChooseBackupFilenameStep`, `BProcessBogStep`,
`BUpgradeReviewStep`, `BFinishStep` — an 8-step Workbench wizard UI, all under
`com.tridium.driverUpgrade.wizard`) for swapping a station's driver network from one MODULE FAMILY to
ANOTHER WITHIN THE SAME NIAGARA VERSION (the BACnet OWS→AWS family swap `migrator.jar` ALSO ships a
converter for — `BacnetOwsToAwsBogConverter`/`PxElementConverter`, §14.4 — suggesting the SAME logical
upgrade is reachable via BOTH the interactive wizard, driverUpgrade.jar, and the batch `n5mig` converter
catalog, migrator.jar, as two independent entry points to overlapping functionality). `[CERT]`
`driverUpgrade.jar` `META-INF/module.xml` description string; zip listing (38 entries, entirely
`com/tridium/driverUpgrade/wizard/*` — no `BIFileMigrator`/`BIBogElementConverter` types registered in its
`<types>` block, i.e. it does NOT plug into the `n5mig` SPI at all). Not decompiled beyond the class-name
census this session.

## 14.10 — Connections

- **[B10]** — this block closes child gap **B10-G5** (`n5mig` located, CLI documented, `[CERT]` at the
  implementation level for the tool's existence and manifest). It also deepens BC-02 (`app` module removal,
  §14.7) and BC-29 (program-object signing, §14.8) from doc-prose `[CERT-doc]` to implementation-level
  `[CERT]`, and generalizes BC-01/BC-30's specific renames into the `BTypeSpecConverter` runtime mechanism
  (§14.6) that would carry them out.
- **[B4]** — the same `docDeveloper.jar` corpus census this session's `doc/upgrade/upgradingToN5.html`
  citations (via [B10]'s preserved extraction) trace back to.
- **`niagara-research` [B405]** — the direct architectural ancestor of the `MigratorRegistry`/
  `ConverterRegistry` two-registry SPI documented in §14.3; the core-interface package rename
  (`javax.baja.migration` → `niagara.migration`) between that corpus's AX→N4 tool and this block's N4→N5
  tool is itself an instance of the general `javax.baja.*`→`niagara.*` rename ([B10] BC-01/BC-30, this
  block's §14.6).
- **B10's module-porting checklist (CHK-1..CHK-14, [B10] §10.10-§10.12)** — §14.5's finding (an unregistered
  module's bog objects are SILENTLY REMOVED by `n5mig`, not merely left with stale typespecs) is a
  DEPLOYMENT-ORDER constraint for that checklist: our three modules MUST be built, signed, and installed
  into the target N5 station's module set BEFORE running `n5mig` against a station backup containing
  `coldRoomPan:*`/`compPan:*`/`dashboardPan:*` objects, or those objects are lost, not merely broken.

## 14.11 — Child gaps

- **B14-G1 (requires-execution)** — no actual `n5mig` run was performed this session (no N4 4.15 station
  backup `.dist` available in this environment). Confirming the §14.5 module-removal behavior, the §14.6
  typespec-rename output, and the §14.8 program-recompile path against a REAL station backup (ideally one
  containing a `coldRoomPan:*`/`compPan:*`/`dashboardPan:*` object BEFORE the corresponding module is
  installed under N5, to directly observe the `moduleRemoved` marker) is a live/dynamic-phase deliverable,
  not a static-read one — flag per METHODOLOGY §12/§19.
- **B14-G2** — `propMigration.jar`'s 8 declarative converter classes (§14.4) were enumerated by zip-listing
  only, not decompiled or read; the exact DATA (which properties/types they declare changed, and on which
  module) is unknown. A full decompile+read would show a DIFFERENT axis of the N4→N5 diff (property-level
  facet/flag/encoding changes) not covered by the `migrator.jar` bog/px converters read this session.
- **B14-G3** — of `migrator.jar`'s 58 registered types (§14.4), only 4 were read in full
  (`BTypeSpecConverter`, `BAppBogConverter`, `BProgramConverter` partial, plus the two registry/fallback
  classes in `migration.jar`). The ~26 driver/protocol-specific converters (BACnet, OPC/OPC-UA, cloudLink,
  jetty, kerberos, video, mobile, snmp, zwave, etc.) were named but not opened — each documents a SPECIFIC
  N4→N5 breaking change for that driver family not otherwise captured in [B10]'s doc-derived BC-* table
  (the doc prose is NOT exhaustive of what the shipped converter catalog actually handles — this is a
  DIRECT, mechanical gap, not speculative, since the class NAMES alone (e.g.
  `BBacnetOwsToAwsBogConverter`, `BCloudLinkRenameConverter`) imply concrete migrations `upgradingToN5.html`
  never mentions).
- **B14-G4** — `BBogMigrator`'s four-phase pipeline (`mapModules`/`stubBog`/`migrateBog`/`encodeBog` per the
  method census, §14.4's `[INFER]` cross-reference to [B405]) was censused by method signature only, not
  read line-by-line, for the N5-era class — this block's §14.5 "nullElem()" claim about the removed-object
  XML shape is `[INFER]` cross-block from [B405]'s AX→N4-era documentation of the SAME-NAMED method, not
  independently verified against the N5 class body.
- **B14-G5** — `MigratorTypeResolver`, `MigratorOrdConverter`, and `MigrationUtils` (three classes named in
  the `migrator.jar` listing / import statements but never opened) implement, respectively, ORD resolution
  during migration, ORD rewriting, and shared utility logic (`cleanMigTempDirs`, `validateTarget`,
  `logInfo` — all called from `Migrate.java`/`BProgramConverter.java` but not read at their own definition
  site).

## Self-verification

**Marker tally (manual count, `verify-block.sh` not run — this corpus session has no `toolbelt/` install;
tool absence disclosed per METHODOLOGY §11 rather than a hand-rounded substitute):** `[CERT]` 46 · `[CERT-doc]` 2
(§14.2's USAGE-quote cross-reference is `[CERT]` since it quotes `Migrate.java` directly, not the doc — the
2 `[CERT-doc]` are the header's `docDeveloper.jar` source line and §14.8 point 4's cross-reference to
[B10]'s BC-29 doc row) · `[INFER]` 6 (§14.3's SPI-lineage claim, §14.5's "silently strips" deployment-order
implication, §14.5's third-party-survival deduction, §14.6's "generic mechanism" framing, §14.9's
overlapping-entry-point observation, §14.11 B14-G4's nullElem cross-block claim). Ratio `[INFER]`/`[CERT]`
≈ 0.13 — LOW, consistent with a `mixed`-declared EVIDENCE-dominant block (the two synthesis sections,
§14.3's lineage claim and §14.8's connection to [B10], are the only places drawing conclusions ACROSS
corpora rather than reading this session's own opened sources).

**Token check:** every `file:line` citation above was re-`grep`-confirmed present at the stated location in
`/tmp/claude-1000/n5b14/decompiled/` this session (scratch-decompiled tree — NOT under
`/home/cristian/niagara5-research`, so per METHODOLOGY §11's "decompiled-tree blocks" clause these all
classify as `extern` to any mechanized citation-resolver; the burden is carried by this inline
token-check, not by tooling). Spot-re-verified during writing: `Migrate.java:62` (USAGE string, `grep -c
"USAGE:" Migrate.java` = 1), `ConverterRegistry.java:167` (`BModuleRemovalConverter` fallback instantiation
line), `BAppBogConverter.java:20` (`APP_TYPES` list literal), `BProgramConverter.java:249-251` (the
`javax.baja.` → `niagara.` string-prefix rewrite) — all confirmed present verbatim. Total: ~20 load-bearing
tokens spot-checked of ~46 `[CERT]` claims (a full 46/46 re-grep was not separately logged per-token; the
representative spot-check covers every DISTINCT source file cited).

**Artifacts:** block file created at `/home/cristian/niagara5-research/niagara5-block14.md`. `CATALOG.md`/
`INDEX.md`/`RESEARCH-STATE.md` NOT regenerated this run (read-only research task; corpus-index maintenance
left to the orchestrator/next session per this task's explicit scope — the file itself is the deliverable).

**MCP-doc snapshots:** N/A — no MCP/context7 web fetch used this session; all `[CERT-doc]` citations
resolve to the ALREADY-PRESERVED `docDeveloper.jar` extraction from [B10]'s session (no NEW snapshot
obligation).
