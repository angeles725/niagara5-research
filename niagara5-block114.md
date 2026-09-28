# Block 114 — `docDeveloper.jar`'s `bajadoc.index` root-node count is ALREADY fully accounted for by two prior blocks; MySQL/SQL-Server DDL type strings censused against HSQLDB; `BSqlType.sqlNVarchar` is dead in the NEW `ddl.Column` path but LIVE in the OLD deprecated-dialect path via `BUnicodeUpdateJob`; and `com.tridium.niagarad.license.Feature`'s call-site census extended to its true 7-file/11-site population

> Research closing four assigned child gaps from three prior blocks. **B109-G3** ([Block 109] §109.x —
> a line-by-line read of `docDeveloper.jar`'s own `doc/bajadoc.index` and how `BHelpSideBar.buildApi()`
> consumes each line, to characterize the Help panel's API-tree shape); **B110-G1** ([Block 110] §110.x
> — the MySQL and SQL Server `RdbmsDialect` DDL type strings for the same 11 `BSqlType` values §110.3
> read for HSQLDB); **B110-G2** ([Block 110] §110.x — is `BSqlType.sqlNVarchar` genuinely dead code, or
> reachable via some `BColumnTranslator`/caller this corpus's own census missed); **B111-G1** ([Block
> 111] §111.x — extend `feature_census.py` to `com.tridium.niagarad.license.Feature`'s own, separate
> license-`Feature` class). Does **not** cover: re-extracting `docDeveiperAnalytics.jar`'s own index
> (already closed, [Block 103] §103.1); a live Orion/RDB-history database creation/migration against a
> real MySQL or SQL Server instance (all four gaps are static source reads, no live station); re-running
> `feature_census.py` against the ORIGINAL 100-file `niagara.license.Feature` population (only a
> same-package-blind-spot corroboration check was run against it, see §114.4's Connections note, not a
> full re-census — B11-G4/B105-G1 stay exactly as [Block 111] left them).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> Method: `rg -il` already-covered sweep of every `niagara5-block*.md` for each gap's key terms before
> investigating (§114.0); for B109-G3, re-reading [Block 4] §4.2's own full-content citation of
> `docDeveloper.jar`'s `doc/bajadoc.index` (109 module-name lines) alongside [Block 109] §109.3's own
> full read of `BHelpSideBar.buildApi()` (`organized/help/vineflower/com/tridium/help/ui/BHelpSideBar.java:
> 232-254`) — no new extraction, pure synthesis of two already-[CERT] facts; for B110-G1/B110-G2, whole-file
> reads of `organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/BMySQLDatabase.java` (795 lines, DDL-getter
> block only, `:197-291`), `organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/BSqlServerDatabase.java`
> (612 lines, `:195-268`), `organized/rdb/vineflower/niagara/rdb/ddl/Column.java` (152 lines, whole file,
> re-read), `organized/rdb/vineflower/com/tridium/rdb/BRdbmsDeprecatedDialect.java` (whole
> `makeAddColumnSql`/`getDataType` methods), `organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/
> BMySQLDeprecatedDialect.java` (whole 149-line file) and `organized/rdbSqlServer/vineflower/com/tridium/
> rdb/sqlserver/BSqlServerDeprecatedDialect.java` (targeted `getDataType`/`getStringType`/
> `makeAlterColumnTypeSql`), plus a corpus-wide `rg -n "makeAddColumnSql|makeAlterColumnTypeSql|\.getDataType\("`
> to find every real caller and the literal `BSqlType` constant each one passes; for B111-G1, extending
> `scratchpad/b111/feature_census.py` (unmodified — same script, new file list) against a freshly
> corpus-wide-verified population of `com.tridium.niagarad.license.Feature`-referencing files (`rg` for
> the import, the FQN, a wildcard import, and every bare-`Feature`-token file under the `niagarad`
> module's own `license/` package, run this session at
> `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b114/`).
> Markers (canonical list, METHODOLOGY §3): `[CERT]` local primary source (`file:line`) · `[INFER]`
> deduction.

---

## 114.0 — ALREADY-COVERED check (all four gaps)

`rg -il` over every `niagara5-block*.md`, at least two distinct terms per gap, before investigating each:

- **B109-G3**: `bajadoc.index` → hits [Block 4], [Block 103], [Block 109] itself (the gap's own lineage).
  `buildApi` → hits [Block 109] itself only. **Combining [Block 4] §4.2 (full content of `docDeveloper.jar`'s
  own `bajadoc.index`) with [Block 109] §109.3 (full read of the consumer method) fully discharges this
  gap's literal ask without any new extraction** — reported as ALREADY-COVERED below (§114.1), not
  re-derived, per the mandatory-first-step instruction.
- **B110-G1**: `rdbMySQL`/`BMySQLDatabase`/`BSqlServerDatabase`/`rdbSqlServer` → hits [Block 110] itself
  (the gap's own origin) plus five unrelated blocks ([Block 11], [Block 3], [Block 95], [Block 8],
  [Block 104], [Block 90], [Block 101]) that name `rdbMySQL`/`rdbSqlServer` only as module-census entries,
  never opening `BMySQLDatabase.java`/`BSqlServerDatabase.java`'s own DDL-getter bodies. **Not
  already-covered** — investigated fresh (§114.2).
- **B110-G2**: `sqlNVarchar` → hits [Block 110] itself only. **Not already-covered** — investigated fresh
  (§114.3).
- **B111-G1**: `niagarad.license.Feature`/`com.tridium.niagarad.license` → hits [Block 111] itself only
  (the gap's own origin, naming the class but not yet censusing it). **Not already-covered** — investigated
  fresh (§114.4).

`[CERT]` (`rg -il` output, this session).

## 114.1 — B109-G3 ALREADY-COVERED: [Block 4] §4.2's own full read of `docDeveloper.jar`'s `doc/bajadoc.index` (109 module-name lines) plus [Block 109] §109.3's own full read of `BHelpSideBar.buildApi()` already answer the gap's exact question — `docDeveloper.jar` contributes exactly 109 API-tree root nodes, one per MODULE NAME, not per top package `[CERT]`

**Gap text (verbatim):** "`BHelpSideBar.buildApi()`'s per-line `DocModuleNode` construction from
`docDeveloper.jar`'s own (984-byte, presumably multi-line) `doc/bajadoc.index` was not read line-by-line
this session ...; confirming how many distinct API-tree root nodes `docDeveloper.jar` alone contributes
(module names? top packages?) would fully characterize the tree's shape."

Both halves of this question are already fully answered by existing [CERT] citations from two different
prior blocks, and combining them requires no new tool invocation:

**Half 1 — the index's own content, read line-by-line.** [Block 4] §4.2 already performed exactly the
read the gap asks for: *"120 distinct `doc/<name>/` subdirectories exist; **109 of them are indexed as
documented modules** in `doc/bajadoc.index` (a flat newline-separated list — `aapup`, `abstractMqttDriver`,
`ace`, `alarm`, ..., `workbench`, one module name per line, read in full this session)"* — this is a full,
line-by-line read of `docDeveloper.jar`'s own `doc/bajadoc.index` (the 984-byte file [Block 103] §103.1
independently confirmed the byte-size of), not the 9-byte `docDeveloperAnalytics.jar` one. [Block 103]
§103.1's own hex dump corroborates the line-4 entry (`aapup\nabstractMqttDriver\nace\nalarm\nalarmOrion\n
analytics\n...`), matching [Block 4]'s ordering exactly.

**Half 2 — how `buildApi()` consumes each line.** [Block 109] §109.3 already performed a whole-method
read of the consumer: *"`buildApi()` calls `HelpSystem.getModulesHavingFile("doc/bajadoc.index")` ... and,
for EACH such module, opens that module's own `doc/bajadoc.index` file and reads it **line by line**,
creating **one `DocModuleNode` tree-root PER LINE**, labeled with that line's text"*
(`organized/help/vineflower/com/tridium/help/ui/BHelpSideBar.java:232-254`, whole `buildApi()` method,
[Block 109]'s own citation).

**Net, by direct substitution:** `docDeveloper.jar`'s `doc/bajadoc.index` has 109 lines (§4.2), each line
becomes exactly one `DocModuleNode` root (§109.3) — so `docDeveloper.jar` alone contributes **exactly 109
API-tree root nodes**, and each root is labeled with a **module name** (`aapup`, `ace`, `alarm`, ...,
`workbench`), never a "top package" — the gap's own two named hypotheses are resolved in favor of
"module names," matching the same granularity `docDeveloperAnalytics.jar` uses for its own single
`"analytics"` root ([Block 103] §103.1/§109.3). The tree's full shape is now fully characterized: 2
doc-eligible modules (§109.2's own 3-jar-minus-`docSource` count) contribute 109 + 1 = 110 total root
nodes to the live Help panel's "API" tab. `[CERT]` (synthesis of `niagara5-block4.md` §4.2 and
`niagara5-block109.md` §109.3, both already-cited `file:line`/zip-entry evidence, no re-derivation).

**B109-G3 CLOSED as ALREADY-COVERED** — the mandatory first-step check should have caught this at gap-open
time; recorded here so the orchestrator can mark it resolved without spending a fresh read.

## 114.2 — B110-G1 CLOSED: MySQL's and SQL Server's `RdbmsDialect` DDL-getter bodies censused against the same 11 `BSqlType` values [Block 110] §110.3 read for HSQLDB — three genuine, concrete per-dialect deltas found `[CERT]`

**Gap text (verbatim):** "the two other `RdbmsDialect` implementations found but not opened this session
(`BMySQLDatabase.java`, `BSqlServerDatabase.java`) would give the exact MySQL/SQL-Server DDL strings for
the same 11 `BSqlType` values §110.3 read for HSQLDB."

Both `com.tridium.rdb.mysql.BMySQLDatabase` (`organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/
BMySQLDatabase.java:197-291`) and `com.tridium.rdb.sqlserver.BSqlServerDatabase`
(`organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/BSqlServerDatabase.java:195-268`) implement
the identical `RdbmsDialect` getter contract `BHsqlDatabase` does (`getIntType`/`getLongType`/
`getFloatType`/`getDoubleType`/`getCharType`/`getVarCharType`/`getUuidType`/`getDateType`/
`getBooleanType`/`getTimestampType`/`getBlobType`/`getClobType`, each as a private inner class implementing
the interface, exactly [Block 110] §110.3's own `BHsqlDatabase` shape), whole-block read this session:

| `BSqlType` (ordinal) | HSQLDB ([Block 110] §110.3) | **MySQL** (this block) | **SQL Server** (this block) |
|---|---|---|---|
| `sqlInt` (0) | `INTEGER` | `INTEGER` | `INTEGER` |
| `sqlLong` (1) | `BIGINT` | `BIGINT` | `BIGINT` |
| `sqlFloat` (2) | `REAL` | `FLOAT` | `REAL` |
| `sqlDouble` (3) | `DOUBLE PRECISION` | `DOUBLE` | `DOUBLE PRECISION` |
| `sqlBoolean` (4) | `BOOLEAN` | `TINYINT` (`supportsBooleanType()`→true, but the type used is TINYINT, not a native BOOLEAN) | `BIT` |
| `sqlTimestamp` (5) | `TIMESTAMP` (native) | **never reached** — `supportsMillisecondTimestamp()` returns `false` and `getTimestampType()` itself `throw new UnsupportedOperationException()`; `Column.makeTypeDdl()` case 5 falls back to `dialect.getLongType()` = `BIGINT` for every AbsTime column | **effectively never reached from case 5** — `supportsMillisecondTimestamp()` returns `false` too, same `BIGINT` fallback; `getTimestampType()`=`DATETIME` is declared but only reachable from the UNRELATED case 11 (`sqlDate`) fallback below |
| `sqlChar` (6) | `CHAR` | `CHAR` (or `NCHAR` if `getUseUnicodeEncodingScheme()`) | `CHAR` (or `NCHAR` if Unicode) |
| `sqlVarchar` (7) | `VARCHAR` (or `NVARCHAR` if Unicode) | `VARCHAR` (or `NVARCHAR` if Unicode) | `VARCHAR` (or `NVARCHAR` if Unicode) |
| `sqlNVarchar` (8) | unreachable in all three (§114.3 below) | unreachable | unreachable |
| `sqlUuid` (9) | `BINARY(16)` | `BINARY(16)` (same as HSQLDB) | **`UNIQUEIDENTIFIER`** (a genuinely different, SQL-Server-native GUID type, not a raw binary column) |
| `sqlBlob` (10) | `LONGVARBINARY` | `MEDIUMBLOB` | `IMAGE` |
| `sqlDate` (11) | `DATE` (`supportsDateType()` always `true`) | `DATE` (`supportsDateType()` always `true`) | `DATE` **only if** `getVersion().getOrdinal() >= 2` (SQL Server 2008+); older configured versions fall back to `getTimestampType()` = `DATETIME` — the only path that actually reaches SQL Server's `getTimestampType()` |
| (bonus, `isClob()` branch) `getClobType` | `LONGVARCHAR` | `TEXT` (or `TEXT CHARACTER SET utf8 COLLATE utf8_unicode_ci` if Unicode) | `TEXT` (or `NTEXT` if Unicode) |

Three concrete, non-cosmetic deltas worth flagging: (1) **MySQL and SQL Server both store `AbsTime`/
timestamp columns as `BIGINT` milliseconds, never a native `TIMESTAMP`/`DATETIME` column**, unlike HSQLDB
which uses a real `TIMESTAMP` type — both non-HSQLDB dialects set `supportsMillisecondTimestamp() = false`
(`organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/BMySQLDatabase.java:256-258` throws for
`getTimestampType()` itself; `organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/
BSqlServerDatabase.java:241-243`
returns `false` for the capability check even though its own `getTimestampType()` body is a normal,
non-throwing `"DATETIME"` string); (2) **SQL Server's UUID column type is `UNIQUEIDENTIFIER`, a native
GUID SQL type**, not the raw `BINARY(16)` both HSQLDB and MySQL use; (3) **SQL Server's DATE support is
itself version-gated** (`organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/
BSqlServerDatabase.java:249-251`, `getVersion().getOrdinal() >= 2`) — an older
configured SQL Server target silently downgrades every `sqlDate` column to `DATETIME` via the same
`Column.makeTypeDdl()` case-11 fallback pattern used for `sqlTimestamp`. `[CERT]`
(`organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/BMySQLDatabase.java:217-291`;
`organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/BSqlServerDatabase.java:197-268`; cross-checked
against `organized/rdb/vineflower/niagara/rdb/ddl/Column.java:96-146`'s own `makeTypeDdl()` switch, re-read
whole-file this session, unchanged from [Block 110] §110.3's own citation).

**B110-G1 CLOSED** — the gap's own literal ask (the exact DDL strings for both dialects) is fully
discharged; both `RdbmsDialect` implementations opened and censused end-to-end.

## 114.3 — B110-G2 CLOSED (nuanced, not a flat yes/no): `BSqlType.sqlNVarchar` is genuinely DEAD in the NEW `niagara.rdb.ddl.Column`/`BColumnTranslator` path (confirmed dialect-independent) — but it is LIVE, reachable, runtime-invoked code in a SEPARATE, OLDER `BRdbmsDeprecatedDialect` path, via `BUnicodeUpdateJob`'s hardcoded literal `[CERT]`

**Gap text (verbatim):** "whether `BSqlType.sqlNVarchar` (ordinal 8, §110.3's flagged unreachable-`case`
finding) is genuinely DEAD code, or reachable via some `BColumnTranslator` this session's 17-class census
missed ... would need a corpus-wide `grep -rl "sqlNVarchar"`."

**A corpus-wide `rg -n "sqlNVarchar"` finds every reference — 3 files, all inside the `rdb`/`rdbMySQL`
module family, none of them a NEW `BColumnTranslator`:** `com.tridium.rdb.BRdbmsDeprecatedDialect`
(`:266`, `makeAddColumnSql`'s quoting logic), `com.tridium.rdb.mysql.BMySQLDeprecatedDialect` (`:55-60,
69-70`, `makeAddColumnSql`/`makeAlterColumnTypeSql`'s MySQL-specific charset-suffix logic), and
`com.tridium.rdb.util.BUnicodeUpdateJob` (`:82-86`). **No 18th `BColumnTranslator` exists anywhere in the
corpus** — the orchestrator's own flagged classes are the ONLY hits, confirming the 17-class census from
[Block 110] §110.3 was complete for the `BColumnTranslator` agent family.

**Part A — confirmed dead in the path §110.3 actually flagged.** `niagara.rdb.ddl.Column.makeTypeDdl()`
(`organized/rdb/vineflower/niagara/rdb/ddl/Column.java:96-146`, re-read whole method) dispatches on
`BColumnTranslator.makeTranslator(dialect, defaultValue).getSqlType().getOrdinal()` — this switch's `case
8` is combined with `default` and unconditionally `throw new IllegalStateException()`, **for every
dialect**, since `Column.makeTypeDdl()` itself is dialect-independent (the dialect is only used for the
STRING each case returns, never for which case is chosen). No `BColumnTranslator`, in any of the 17 named
agent classes or the `BSimpleTranslator` fallback, ever returns `sqlNVarchar` — confirmed unchanged from
[Block 110] §110.3. This path is genuinely, permanently dead: it is used exclusively for Orion-table
`CREATE`/`ADD COLUMN` DDL generation (`TableBuilder`→`Column.getDdl()`), and no translator anywhere feeds
it an `sqlNVarchar` value.

**Part B — the corrected finding: `sqlNVarchar` IS live in a DIFFERENT, OLDER code path the census never
looked at.** `com.tridium.rdb.BRdbmsDeprecatedDialect` (abstract, 149+-line, `@AgentOn`-registered on
`rdbMySQL:MySQLDatabase`/`rdbSqlServer:SqlServerDatabase` via its two concrete subclasses) implements a
COMPLETELY SEPARATE type-to-DDL translation mechanism: `getDataType(BSqlType)`
(`organized/rdb/vineflower/com/tridium/rdb/BRdbmsDeprecatedDialect.java:392-408`) switches on ordinal 0-3
and 5 explicitly, with **`case 4: default:` COMBINED** — meaning ordinals 4, 6, 7, 8, 9, 10, 11 (including
`sqlNVarchar`=8) all fall into the SAME default branch and return a string type derived from
`getSqlType(BString.TYPE, null)`. **`sqlNVarchar` is reachable here — it just isn't distinguished from
`sqlVarchar`/`sqlChar`/etc. by this particular getter**, but the two per-dialect subclasses DO
distinguish it explicitly one level up: `BMySQLDeprecatedDialect.makeAddColumnSql()`/
`makeAlterColumnTypeSql()` (`:55,60,69-70`) and `BRdbmsDeprecatedDialect.makeAddColumnSql()` (`:266`) both
have live `if (columnType.equals(BSqlType.sqlNVarchar))` branches that append MySQL's
`CHARACTER SET utf8 COLLATE utf8_unicode_ci` suffix and correctly single-quote the default value.

**And this path is genuinely INVOKED at runtime with a literal `sqlNVarchar` constant — not merely
defensive dead code guarding against a value nothing produces.** `com.tridium.rdb.util.BUnicodeUpdateJob.
updateTable()` (`organized/rdb/vineflower/com/tridium/rdb/util/BUnicodeUpdateJob.java:82-86`, whole method
read) does:
```java
String sql = this.getRdbmsDialect().makeAlterColumnTypeSql(
   tableName, columnNameAndWidthPair.getFirst(), BSqlType.sqlNVarchar, columnNameAndWidthPair.getSecond()
);
statement.execute(sql);
```
— `BSqlType.sqlNVarchar` here is a **hardcoded literal**, not derived from any `BColumnTranslator` at all
(bypassing `Column.makeTypeDdl()`/`BColumnTranslator` entirely). `BUnicodeUpdateJob` is a migration job
(subclass of `BRdbmsUpdateJob`, the same update-job family §110.4's own `BOrionService`-adjacent census
touched) that scans every existing `VARCHAR`-typed column (via live JDBC `DatabaseMetaData.getColumns()`)
and `ALTER`s each one to Unicode/NVARCHAR when a database is switched to Unicode encoding after tables
already exist — a real, live-executed schema-migration code path, `[CERT]`
(`organized/rdb/vineflower/com/tridium/rdb/util/BUnicodeUpdateJob.java:51-89`, whole `updateTable()`
method).

**Net answer to the gap's own question:** `sqlNVarchar` is **not** globally dead code. It is
**structurally dead in exactly one of TWO independent RDB type-translation systems** (the newer,
`BColumnTranslator`-driven `niagara.rdb.ddl.Column` path used for Orion/persisted-component table
creation) and **live and runtime-reachable in the other** (the older `BRdbmsDeprecatedDialect`-driven
path used for RDB history import/export/migration jobs, `BRdbmsHistoryExport`/`BUnicodeUpdateJob`/
`BRdbmsDiscoverTablesJob` per the corpus-wide caller census, `organized/rdb/vineflower/com/tridium/rdb/
history/`, `util/`). [Block 110] §110.3's "dead code" flag was correct FOR THE SPECIFIC PATH IT WAS
READING, but did not generalize corpus-wide — this is a **correction of scope, not of fact** (§114.x
below).

**B110-G2 CLOSED** — the gap's own literal ask (dead, or reachable via a missed translator/caller) is
fully answered: not a missed 18th translator (none exists), but a second, entirely separate caller
family that hardcodes the enum constant directly, bypassing translators altogether.

## 114.4 — B111-G1 CLOSED: `com.tridium.niagarad.license.Feature`'s true population is 7 files (not the 2 the parent gap estimated) and 11 declared-type-aware call sites (not the estimated 5) — the same `feature_census.py` script, corrected file-scoping `[CERT]`

**Gap text (verbatim):** "Extend §111.1's `feature_census.py` (or a variant) to ALSO census
`com.tridium.niagarad.license.Feature` ... across its own module scope — 2 files / 5 call sites were
identified but not resolved this session."

**Population census, corpus-wide, before running the script (the step the parent gap's own estimate
skipped):** a corpus-wide `rg` for the exact FQN import, a wildcard import (`import com.tridium.niagarad.
license.*`), and every bare-`Feature`-token `.java` file under the `niagarad` module's own `com/tridium/
niagarad/` tree finds **7 files total**, not the parent's estimated 2 — the 3 files that `import
com.tridium.niagarad.license.Feature` explicitly (`servlet/PlatformInfoServlet.java`, `app/StationApp.java`,
`platform/PlatformInfo.java`, matching the parent gap's own 2-of-these-3 partial finding) **plus 4 files
that use the bare `Feature` token WITHOUT any import at all, because they live in `Feature`'s OWN package**
(`com/tridium/niagarad/license/{LicenseFile,Brand,LicenseManager,Feature}.java` — same-package Java
classes never need an import) — a blind spot the parent gap's own "2 files" estimate fell into (it appears
to have grepped for the import statement alone, not the type's home package). No wildcard import of
`com.tridium.niagarad.license.*` exists anywhere in the corpus. `[CERT]` (`rg` output, this session,
scratch: `.../scratchpad/b114/niagarad_feature_files_full.txt`).

**Running the unmodified `feature_census.py` against this corrected 7-file list** (script needs no
change — its `DECL_RE`/`CALL_RE_TMPL` are already name-independent and package-independent, matching the
bare word "Feature" regardless of which `Feature` class a given file's import resolves it to):

```
Files scoped: 7
Files with >=1 bare-'Feature'-typed declaration: 7
Total bare-'Feature'-typed declarations found: 10
Total distinct call sites (declared-type-aware): 11
```

All 11 sites (0 overlap with [Block 105]'s `niagara.license.Feature`-only 211-line census, as expected —
disjoint type):

| File | Line | Call |
|---|---|---|
| `app/StationApp.java` | 117 | `capacityFeature.isExpired()` |
| `app/StationApp.java` | 118 | `capacityFeature.get("heap.limit", "-1")` |
| `app/StationApp.java` | 528 | `jreFeature.get("vendor", "azul")` |
| `app/StationApp.java` | 529 | `jreFeature.get("minVersion", "5.0")` |
| `license/Brand.java` | 50 | `feature.get("brandId")` |
| `license/Brand.java` | 68 | `feature.get(id, "*")` (inside `AcceptList`'s constructor) |
| `license/LicenseManager.java` | 173 | `result.check()` (inside `checkFeature()`) |
| `platform/PlatformInfo.java` | 239 | `station.check()` |
| `platform/PlatformInfo.java` | 243 | `station.geti("station.limit", 32)` |
| `platform/PlatformInfo.java` | 245 | `station.get("station.limit")` |
| `servlet/PlatformInfoServlet.java` | 196 | `syslogFeature.check()` |

Two of these 3 same-package files' sites (`organized/_bin-ext/niagarad/vineflower/com/tridium/niagarad/
license/LicenseManager.java:173`, both `Brand.java` sites) are the
NEW, previously-unidentified sites this corrected census finds beyond even a naive "grep every importing
file" pass — `license/LicenseFile.java` (declares a `Feature` local at `:127` but only ever touches its
package-private `.props` field and `getVendorName()`/`getFeatureName()`, never a census method) and
`license/Feature.java` itself (its own `merge(Feature x)` only touches `x.expiration`, never a census
method) genuinely have zero call sites, confirmed by direct read, not just the script's silence.
`[CERT]` (`.../scratchpad/b114/niagarad_feature_census_full_output.txt`, this session).

**B111-G1 CLOSED** — the gap's own literal ask (extend the script to this class, report the count) is
fully discharged, with a corrected population (7 files) and corrected site count (11) that supersede the
parent gap's own 2-file/5-site estimate.

## 114.x — Corrections to earlier blocks

- **[Block 110] §110.3's own dead-code framing, corrected in scope (§114.3):** §110.3 stated
  `BSqlType.sqlNVarchar` "appears to be dead/unreachable code ... rather than an active bug" without
  qualifying WHICH of the two independent RDB type-translation systems it meant. This block's finding
  does not contradict §110.3's own citations (the `Column.makeTypeDdl()` switch really does throw for
  ordinal 8, unconditionally, exactly as §110.3 said) — it narrows the claim's scope: dead in that one
  path, live in `BRdbmsDeprecatedDialect`'s sibling path, actually invoked by `BUnicodeUpdateJob`. No
  action needed on §110.3's own text (its citations remain correct for what they examined); this is
  additive, not a retraction.
- **[Block 111] §111.x's own B111-G1 child-gap text, corrected (§114.4):** the parent gap's own "2 files /
  5 call sites were identified" estimate undercounted — the true population is 7 files / 11 sites, due to
  a same-package import blind spot in whatever grep produced that estimate (not `feature_census.py`
  itself, which was never run against `niagarad.license.Feature` before this block).

## 114.x — Connections

- **B109-G3's closure (§114.1) is itself a small methodology finding**: the mandatory ALREADY-COVERED
  check works per-gap, but this gap's answer required COMBINING two DIFFERENT prior blocks' citations
  ([Block 4] + [Block 109]), neither of which alone fully answered it — worth remembering that
  "already-covered" can span a synthesis of multiple blocks, not just one.
- **§114.4's same-package blind spot was spot-checked against the ORIGINAL, larger `niagara.license.Feature`
  population too** (not re-derived — a corroboration check only): `organized/{baja/vineflower,docSource/
  baja}/niagara/license/{LicenseManager,Feature,BILicensed}.java` are NOT in [Block 111]'s own 100-file
  scoped list (`scratchpad/b111/feature_files.txt`), matching the same pattern found here — but a direct
  read confirms all three are bare `@AgentOn`/interface-stub declarations with NO method bodies
  (`niagara.license.LicenseManager` is a 9-line interface; `Feature`/`BILicensed` are the interface/stub
  themselves), so there is no concrete local-variable declaration anywhere in them and this specific
  blind spot resolves NEGATIVE for the original 92-site census — no additional child gap opened for
  B105-G1/B11-G4, which [Block 111] already left NARROWED for an unrelated (population-scope) reason.
- **§114.2's `AbsTime`→`BIGINT`-not-`TIMESTAMP` finding for MySQL/SQL Server** connects to [Block 110]
  §110.4's own finding that no Orion table has a retention/purge policy — timestamp columns being stored
  as raw millisecond `BIGINT` rather than a native temporal type is a plausible reason a
  dialect-portable retention query would need to stay arithmetic (millis-since-epoch comparison) rather
  than relying on any SQL-native date/time function; not independently verified this session, offered as
  an [INFER] connection only.

## 114.x — Child gaps opened

- **B114-G1** (low, `investigable`) — whether `BRdbmsHistoryExport`'s hardcoded `BSqlType.sqlVarchar`
  literal for the fixed `HISTORY_ID` column (`organized/rdb/vineflower/niagara/rdb/history/
  BRdbmsHistoryExport.java:485`, also its `docSource` mirror `:821`) is the ONLY other hardcoded-literal
  `BSqlType` caller in the corpus, or whether other `BRdbmsUpdateJob`/history-migration subclasses
  (`BRdbmsMigrateIndexesJob`, `BRdArchiveHistoryProvider`, etc. — named in §114.3's `BRdbmsDeprecatedDialect`
  referrer list but not individually opened this session) also hardcode a `BSqlType` constant rather than
  deriving it from a translator — would fully map the SECOND (deprecated-dialect) type-translation
  system's own complete caller graph, mirroring what [Block 110] §110.3 already did for the FIRST
  (`BColumnTranslator`) system. `investigable` (read-only, mechanical — same read pattern as §114.3).
- **B114-G2** (low, `investigable`) — a live reproduction of `BUnicodeUpdateJob`'s migration (§114.3)
  against a real MySQL or SQL Server instance was explicitly out of scope this session (static source
  only); confirming the generated `ALTER TABLE ... MODIFY COLUMN ... NVARCHAR(...) CHARACTER SET utf8
  COLLATE utf8_unicode_ci` SQL string is actually valid, executable DDL against a live MySQL 8+ server
  would corroborate this block's [CERT] source-reading with a [CERT-hw] execution. `requires-execution`
  (needs a live MySQL/SQL-Server instance — explicitly excluded from this READ-ONLY corpus per the
  orchestrator's own scope boundary).

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `docDeveloper.jar`'s own `doc/bajadoc.index` has 109 lines, one module name per line, already fully read by [Block 4] §4.2 | [CERT] | `niagara5-block4.md` §4.2 (reused, not re-derived) |
| 2 | `BHelpSideBar.buildApi()` creates one `DocModuleNode` root per line of a module's `doc/bajadoc.index`, already fully read by [Block 109] §109.3 | [CERT] | `niagara5-block109.md` §109.3, citing `organized/help/vineflower/com/tridium/help/ui/BHelpSideBar.java:232-254` (reused, not re-derived) |
| 3 | MySQL/SQL Server DDL getter bodies for all 11 `BSqlType` values, per the table in §114.2 | [CERT] | `organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/BMySQLDatabase.java:217-291`; `organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/BSqlServerDatabase.java:197-268` |
| 4 | `Column.makeTypeDdl()`'s `case 8` (sqlNVarchar) unconditionally throws `IllegalStateException`, dialect-independent | [CERT] | `organized/rdb/vineflower/niagara/rdb/ddl/Column.java:130-135` |
| 5 | `BUnicodeUpdateJob.updateTable()` passes the literal `BSqlType.sqlNVarchar` to `makeAlterColumnTypeSql()`, a live runtime-invoked call, not translator-derived | [CERT] | `organized/rdb/vineflower/com/tridium/rdb/util/BUnicodeUpdateJob.java:82-86` |
| 6 | `com.tridium.niagarad.license.Feature`'s true population is 7 files (3 importing + 4 same-package), 11 declared-type-aware call sites | [CERT] | `.../scratchpad/b114/niagarad_feature_census_full_output.txt`, this session; script `.../scratchpad/b111/feature_census.py` (unmodified) |
| 7 | No 18th `BColumnTranslator` and no wildcard `com.tridium.niagarad.license.*` import exist anywhere in the corpus | [CERT] | `rg -n "sqlNVarchar"` / `rg -n "import com\.tridium\.niagarad\.license\.\*"` output, this session |

**Tally:** 7 `[CERT]` claims, 0 `[INFER]` claims in the numbered self-verify table (one additional `[INFER]`
appears in body prose only, §114.x Connections' retention/purge speculation, explicitly marked as such).

**Artifacts:** `/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/
scratchpad/b114/` — `niagarad_feature_files.txt` (3-file initial scope), `niagarad_feature_files_full.txt`
(corrected 7-file scope), `niagarad_feature_census_output.txt` (3-file run), `niagarad_feature_census_full_output.txt`
(7-file run, the authoritative one cited above). Reused unmodified from [Block 111]:
`/tmp/claude-1000/-home-cristian-niagara-research/4d9a109b-8d01-4d7d-acb1-4d2d675d1b66/scratchpad/b111/
feature_census.py`.
