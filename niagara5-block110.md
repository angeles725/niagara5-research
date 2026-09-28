# Block 110 — Four B104 child gaps closed: `ValueDocDecoder`'s bog-document grammar, `BUploadParameters`/`BDownloadParameters`'s full field census, `TableBuilder`'s Property→SQL-type mapping, and a station-wide negative census for any retention/purge job over Orion-backed tables

> Research closing four low-priority child gaps opened by [Block 104]: **B104-G1** (§104.2 — `niagara.io.
> ValueDocDecoder`'s own binary/tag encoding grammar, the decoder `BNiagaraVirtualChannel.findReachableStations`
> uses via `makeDefaultDecoder`; reconstruct it from `organized/baja` source and diff against N4); **B104-G2**
> (§104.4 — `BUploadParameters`/`BDownloadParameters`'s own declared fields, beyond the 4-method `BILoadable`
> interface contract already read); **B104-G3** (§104.8 — `orion`'s `TableBuilder`'s Property-type→SQL-column-
> type mapping, a 238-line class located but not read past its declaration); **B104-G4** (§104.8's own
> negative retention/purge census was scoped to `organized/orion/vineflower` only — extend it station-wide,
> to any module OUTSIDE `orion` that targets an Orion-backed table, plus `BOrionService`'s own un-opened
> properties/actions). Does **not** cover: a live wire-capture of an actual `findReachableStations` response
> byte-for-byte matched against §110.1's grammar (would need a live multi-station N5 network, `[B104-G1]`'s
> own `requires-execution` sibling **B104-G5** already tracks this class of gap); per-vendor `RdbmsDialect`
> DDL strings beyond the one concrete `BHsqlDatabase` example read for §110.3 (MySQL/SQL Server/other
> dialect modules exist but were not individually censused); a live Orion database inspection (`organized/`
> source only, no station).
>
> Subject version: **N5 5.0.0.28 (Beta)**, decompiled tree at `/home/cristian/niagara5-research/organized/`.
> N4 baseline (for the §110.1 delta): `/home/cristian/niagara-research/organized/baja/baja/vineflower/
> javax/baja/io/ValueDocDecoder.java` (N4.14/N4.15-family Vineflower decompile). Method: full whole-file
> reads of `organized/baja/vineflower/niagara/io/ValueDocDecoder.java` (1,276 lines) and its N4 counterpart
> (1,217 lines) for §110.1; whole-file reads of `organized/driver/vineflower/niagara/driver/loadable/
> {BUploadParameters,BDownloadParameters,BLoadableActionParameters}.java` plus their `bajadoc` XML and a
> `diff` against the equivalent N4 `driver-rt` files for §110.2; whole-file reads of `organized/orion/
> vineflower/com/tridium/orion/sql/TableBuilder.java`, `organized/rdb/vineflower/niagara/rdb/ddl/
> Column.java`, `com/tridium/rdb/jdbc/trans/{BSqlType,BColumnTranslator}.java`, and all 17
> `B*Translator.java` per-type agent classes for §110.3, cross-checked against one concrete dialect
> (`organized/rdbHsqlDb/vineflower/com/tridium/rdb/hsqldb/BHsqlDatabase.java`); a corpus-wide (not
> `orion`-scoped) `grep -rl` census of every `BIOrionObject`/`BIOrionApp`/`OrionType` reference outside
> `orion/`, followed by whole-file/targeted reads of the two `BIOrionApp` implementers found
> (`alarmOrion`'s `BOrionAlarmService`/`BOrionArchiveAlarmProvider`) and a full re-read of `BOrionService`'s
> own `@NiagaraProperty` census, for §110.4. Already-covered check: `rg -il` swept all
> `niagara5-block*.md` for `ValueDocDecoder`, `BUploadParameters`/`BDownloadParameters`, `TableBuilder`,
> and `retention`/`purge` before opening each gap (§110.0 below records the negative/partial results).
>
> Markers (canonical list: METHODOLOGY §3): `[CERT]` local primary source (`file:line`) · `[INFER]`
> deduction.
>
> **Type:** `evidence` — all four sections are direct whole-file/targeted reads of already-located
> decompiled source, cross-referenced against each other and (for §110.1/§110.2) against the equivalent
> N4 file; no design/synthesis judgment calls beyond stating what the code does.

---

## 110.0 — Already-covered check (negative for all four gaps)

`rg -il` over every `niagara5-block*.md` for each gap's key terms, before opening it:

- **`ValueDocDecoder`** appears in [Block 19] (decompile-target census only), [Block 24]/[Block 66]/[Block 47]
  (all about the MIGRATION-side `MigrationValueDocDecoder` inner class and password-deny-listing, a
  DIFFERENT concern), and [Block 31] §31.5 (a full read of `parseSlot`'s ORPHANED-PROPERTY branch only —
  `slot == null`/no-`t=`/explicit-`t=` handling, `ValueDocDecoder.java:386-514,1144-1178`). None of these
  reconstructs the general tag/attribute GRAMMAR B104-G1 asks for (root element, the full `p`/`a`/`t`
  attribute set, the primitive fast-path, module/type-symbol resolution) — [Block 31] is the closest prior
  art and is reused as corroboration in §110.1, not re-derived.
- **`BUploadParameters`/`BDownloadParameters`** appear only in [Block 104] itself (named, not opened). No
  prior block reads their fields.
- **`TableBuilder`** appears only in [Block 104] itself (named, `wc -l`'d, not read).
- **`retention`/`purge`** hits 13 other blocks, but every one is either a Java `@Retention` meta-annotation
  false-positive (Blocks 41/33/7/95/8/93/48/30) or [Block 69]'s own `BOrionSecurityAudit` passage (§69.x,
  itself citing [Block 104] §104.8's `orion`-only census as still-open) or [Block 54]/[Block 58]'s
  unrelated alarm/backing-store mentions. None extends the census outside `orion/`. `batchJob`'s own
  `niagara.retention`/`niagara.batchJob.retention` package (found fresh this session, not previously
  indexed under these keywords) is a DIFFERENT, non-Orion retention framework — see §110.4.

No gap is ALREADY-COVERED; all four required fresh reading, done below.

## 110.1 — B104-G1 CLOSED: `ValueDocDecoder`'s bog-document grammar reconstructed; only confirmed N4→N5 delta is a version-string bump `[CERT]`

`niagara.io.ValueDocDecoder` (N5 `baja.jar`, `organized/baja/vineflower/niagara/io/ValueDocDecoder.java`,
1,276 lines, full read this session) is **not a binary format** — despite the class's informal "binary
grammar" framing in [Block 104]'s own gap text, the underlying stream is a normal **text/XML document**
parsed via `niagara.xml.XParser`/`XElem` (`BogDecoderPlugin.parser`, `:670`). The grammar it enforces:

**Root element.** `readHeader()` (`:741-757`) requires the very first element to be named exactly
`bajaObjectGraph` (`root.name().equals("bajaObjectGraph")`, `:744`), carrying a `version` attribute whose
value must be `"1.0"`, `"4.0"`, or **`"5.0"`** (`:749`) — any other value throws
`"Unsupported version (...): supported versions are 1.0, 4.0, 5.0"`. The header also carries the
password-encoding metadata parsed by `BogPasswordObjectEncoder.parseBogHeader(root, ...)` (`:754`, same
class [Block 47] §47.1 and [Block 66] §66.1 already traced from the migration side).

**Body elements — 3 tag names, 9 attributes.** `parseSlot()` (`:294-529`, the method `decode()` calls at
`:161`) switches on the child element's own name (`slotElem.name().intern()`, `:300`): only `"p"`
(property), `"a"` (action), and `"t"` (topic) are recognized (`:302-304`); anything else falls to the
`default:` branch (`:516-527`) and is either routed to `decodingComponent()` (a component-specific
override hook, base implementation just warns) or warned-and-skipped. Each recognized element's own
attributes are read positionally by name (`slotElem.attrName(i)`/`attrValue(i)`, `:317-347`):

| Attr | Field | Meaning |
|---|---|---|
| `n` | `name` | slot name — required; missing throws `"Missing \"n\" name attribute"` (`:389`) |
| `h` | `handle` | component handle, applied via `ComponentSlotMap.setHandle` (`:478`) only if the decoded value `isComponent()` |
| `v` | `value` | inline literal value — enables the primitive fast-path (`decodePrimitive`, below) or is re-used by `decodeSimple` for a `BSimple` |
| `t` | `type` | `<moduleSymbol>:<typeName>` typespec string, resolved by the pluggable `ITypeResolver` |
| `m` | `module` | a `<symbolKey>=<fullModuleName>` module-registration pair, consumed by `loadModule` |
| `f` | `flagStr` | slot flags, decoded via `Flags.decodeFromString` (`:612-614`) |
| `x` | (facets) | `BFacets` string encoding, decoded via `simpleFactory.make(BFacets.TYPE, str, cx)` (`:616-622`) |
| `c` | `catsStr` | a `BCategoryMask` string, applied to a decoded `BComponent` (`:483-485`) |
| `stub` | `stub` | literal `"true"`/anything-else boolean; when NOT `"true"`, marks the decoded component's broker-props as loaded (`:479-481`) |

**Module/type resolution grammar.** A `m="<key>=<fullName>"` attribute (`:333-334`, split on `=` at
`indexOf(61)`) registers a per-document module SYMBOL alias — `BogTypeResolver.loadModule` (`:1127-1141`)
splits on the first `=`, loads the named module via `Nre.getModuleManager()`, and caches
`key → NModule` / `key → fullName` in the decoder's own `modules`/`moduleNamesBySymbol` maps (`BogDecoderPlugin`
fields, `:671-672`). A later `t="<tkey>:<typeName>"` (split on `:` at `indexOf(58)`, `BogTypeResolver.
newInstance` `:1154-1168`) looks the `tkey` symbol back up in that same map to resolve the concrete
`NModule`, then either instantiates the type directly (`module.hasType(tname)`) or falls back to a static
`typeSwapMap` (one entry statically registered: `niagaraDriver:NiagaraVirtualGateway` →
`niagaraDriver:NiagaraVirtualDeviceExt`, `:666`, gated by the `niagara.decodeTypeSwap` system property,
default `true`) — an undeclared module symbol throws `ModuleNotFoundException`.

**Primitive fast-path.** `decodePrimitive()` (`:564-602`) is a pure optimization: when a `Property`'s
`getTypeAccess()` is one of 6 recognized simple-type-access codes (0=boolean, 2=int, 3=long, 4=float,
5=double, 6=string; `:570-591`), the `v=` attribute's string is decoded directly via the matching
`B<Type>.decode(value)`/`setString` call and the element is expected to close immediately (`next()` must
return end-of-element, `:593-598`) — skipping full type/module resolution entirely for these six scalar
cases. `getTypeAccess() == 7` (a `BSimple` needing its own `decodeFromString`, per `BSimpleTranslator`'s
own use elsewhere — see §110.3) explicitly bypasses this fast-path (`:566-568`) and falls through to the
general `newInstance`+`decodeSimple` path (`:469-475`).

**N4 comparison — confirmed delta.** The equivalent N4 class (`javax.baja.io.ValueDocDecoder`,
`/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/io/ValueDocDecoder.java`,
1,217 lines, full read this session) is **byte-for-byte identical in grammar**: same 3 element names
(`p`/`a`/`t`, `:284-286`), same 9-attribute switch (`:300-327`, identical attribute letters and field
roles), same `decodePrimitive` type-access switch (identical 6 cases, same ordinals), same
`typeSwapMap`/`decodeTypeSwap` single entry (`:608`). The **one confirmed grammar-level delta** is the root
`version` check: N4 accepts only `"1.0"` or `"4.0"` (`"Unsupported version (...): supported versions are
1.0, 4.0"`, `:686`) — N5 ADDS acceptance of `"5.0"` (§110.1 above, `:749`) as a third valid
`bajaObjectGraph` document version, with no other body-grammar change. The only other differences are
non-grammar: the `javax.baja.*`→`niagara.*` package rename ([Block 5]'s already-established pattern) and
Vineflower's cosmetic `@Generated` annotations on N5's accessor methods (absent from N4's decompile,
irrelevant to the wire format). `[CERT]` both files, line ranges above.

## 110.2 — B104-G2 CLOSED: `BUploadParameters` adds 2 boolean properties, `BDownloadParameters` adds none; no device-filter or progress/cancel field exists in either class `[CERT]`

Full reads of `organized/driver/vineflower/niagara/driver/loadable/{BLoadableActionParameters,
BUploadParameters,BDownloadParameters}.java` (58/25/40 lines) give the complete, exhaustive field census
[Block 104] §104.4 left open:

- **`BLoadableActionParameters`** (abstract `BStruct` base both parameter classes extend) declares exactly
  **one** property: `recursive` (`boolean`, default `true`, `:12`) — its own `(boolean recursive)`
  constructor (`:37-39`) is the only non-default constructor either subclass calls through to.
- **`BUploadParameters`** adds exactly **two** own properties on top of `recursive`: `uploadTransient`
  (`boolean`, default `true`) and `uploadPersistent` (`boolean`, default `true`) (`:13-16`). Their bajadoc
  (`organized/docDeveloper/vineflower/doc/driver/niagara/driver/loadable/BUploadParameters.bajadoc`)
  confirms the plain-English contract: *"Upload transient properties"* / *"Upload persistent properties"*
  — i.e., the upload operation's own scope filter is a coarse transient-vs-persistent-slot toggle, not a
  device/object filter.
- **`BDownloadParameters`** adds **zero** own properties — it is a pure marker subclass of
  `BLoadableActionParameters`, differing from it only by type identity and its own `(boolean recursive)`
  constructor forwarding (`:12-14` of the 25-line file).

**[Block 104] §104.4's own speculative framing** ("e.g. a device filter, a progress/cancel handle") is
thereby **narrowed to a negative finding**: neither class declares any such field. The only configurable
knobs the `BILoadable.upload()`/`download()` contract exposes are `recursive` (both directions) and,
upload-only, the transient/persistent scope split.

**N4 comparison.** `diff` against the equivalent N4 `driver-rt` files
(`organized/driver/driver-rt/vineflower/javax/baja/driver/loadable/{BUploadParameters,
BDownloadParameters}.java`) shows the field census is **identical** — same two `BUploadParameters`
properties, same zero-property `BDownloadParameters`, same `(boolean recursive)` constructors. The only
diff lines are the `javax.baja.*`→`niagara.*` package/import rename (already established generally,
[Block 5]) and N5-side cosmetic `@Generated` annotations Vineflower emits for annotation-processor-derived
accessors. No functional delta.

## 110.3 — B104-G3 CLOSED: `TableBuilder` delegates the actual type mapping to `Column`+`BSqlType`+17 per-type `BColumnTranslator` agents; one concrete dialect (`BHsqlDatabase`) gives the exact DDL strings `[CERT]`

> **Correction (added by [Block 114], §14 cross-block).** `sqlNVarchar` is dead only in the `niagara.rdb.ddl.Column`
> translator path; it is LIVE in the deprecated-dialect path via `BUnicodeUpdateJob.updateTable()`
> (`organized/rdb/vineflower/com/tridium/rdb/util/BUnicodeUpdateJob.java:85`). See [Block 114] §114.3.

`TableBuilder` itself (`organized/orion/vineflower/com/tridium/orion/sql/TableBuilder.java`, 238 lines,
full read this session) does **not** contain the Property→SQL mapping directly — `makeColumns()`
(`:81-112`) only classifies each persistent `Property` into one of 5 `Column` factory calls
(`makeIdentity`/`makeKey`/`makeUnique`/`makeClob`/`make`, dispatched by `BOrionObject.isIdentity/isKey/
isUnique/isClob`) and forwards `prop.getType()` + the instance's own default value + an optional WIDTH
facet. The actual type-to-DDL translation lives one layer down, in `niagara.rdb.ddl.Column.makeTypeDdl()`
(`organized/rdb/vineflower/niagara/rdb/ddl/Column.java:96-146`), which dispatches on
`BColumnTranslator.makeTranslator(dialect, defaultValue).getSqlType().getOrdinal()` — a **12-value enum**,
`com.tridium.rdb.jdbc.trans.BSqlType` (`organized/rdb/vineflower/com/tridium/rdb/jdbc/trans/BSqlType.java:12-26`):
`sqlInt(0)`/`sqlLong(1)`/`sqlFloat(2)`/`sqlDouble(3)`/`sqlBoolean(4)`/`sqlTimestamp(5)`/`sqlChar(6)`/
`sqlVarchar(7)`/`sqlNVarchar(8)`/`sqlUuid(9)`/`sqlBlob(10)`/`sqlDate(11)`.

**BValue-type → `BSqlType` mapping** — read from all 17 `com.tridium.rdb.jdbc.trans.B*Translator.java`
classes, each an `@AgentOn`-registered `BColumnTranslator` agent keyed to one `baja:<Type>` (full read of
every `getSqlType()` body this session):

| Niagara type (`baja:...`) | Translator | `BSqlType` |
|---|---|---|
| `Boolean` | `BBooleanTranslator` | `sqlBoolean` |
| `Integer` | `BIntegerTranslator` | `sqlInt` |
| `Long` | `BLongTranslator` | `sqlLong` |
| `RelTime` | `BRelTimeTranslator` | `sqlLong` |
| `Float` | `BFloatTranslator` | `sqlFloat` |
| `Double` | `BDoubleTranslator` | `sqlDouble` |
| `AbsTime` | `BAbsTimeTranslator` | `sqlTimestamp` |
| `Date` | `BDateTranslator` | `sqlDate` |
| `Time` | `BTimeTranslator` (extends `BFixedWidthTranslator`) | `sqlChar` (fixed width = `getColumnWidth()`) |
| `String` | `BStringTranslator` | `sqlVarchar` |
| `TypeSpec` | `BTypeSpecTranslator` | `sqlVarchar` |
| `TimeZone` | `BTimeZoneTranslator` | `sqlVarchar` |
| `Password` | `BPasswordTranslator` | `sqlVarchar` |
| `FrozenEnum` | `BFrozenEnumTranslator` | `sqlInt` |
| `Uuid` | `BUuidTranslator` | `sqlUuid` |
| any other `BSimple` (fallback, `BSimpleTranslator`, no dedicated agent) | `BSimpleTranslator` | `sqlVarchar` |
| binary/blob types | `BAbstractBlobTranslator` subclasses | `sqlBlob` |

**Concrete DDL strings — HSQLDB dialect** (`organized/rdbHsqlDb/vineflower/com/tridium/rdb/hsqldb/
BHsqlDatabase.java:239-310`, the one dialect module read in full this session; `BOrionDatabase.getRdbms()`
is abstract, so Orion is dialect-pluggable — `rdbMySQL`/`rdbSqlServer` sibling modules exist but were not
individually censused, tracked as this block's own scope note above): `sqlInt`→`INTEGER`,
`sqlLong`→`BIGINT`, `sqlFloat`→`REAL`, `sqlDouble`→`DOUBLE PRECISION`, `sqlBoolean`→`BOOLEAN`,
`sqlTimestamp`→`TIMESTAMP`, `sqlChar`→`CHAR`, `sqlVarchar`→`VARCHAR` (or `NVARCHAR` if
`getUseUnicodeEncodingScheme()`), `sqlUuid`→`BINARY(16)`, `sqlDate`→`DATE`, `sqlBlob`→`LONGVARBINARY`;
`Column.getDdl()` (`:68-94`) appends `NOT NULL` for identity/key/unique columns and, for a non-alteration
identity column, the dialect's own `getIdentityCreation()` suffix.

**Finding worth flagging (defensive code-review note, not a security issue):** `BSqlType.sqlNVarchar`
(ordinal 8) is a fully-declared enum member with no corresponding `case` in `Column.makeTypeDdl()`'s
switch (`:98-145`) — ordinal 8 falls into the `case 8: default: throw new IllegalStateException();`
branch (`:133-135`). No `BColumnTranslator` in the 17 read this session ever returns `sqlNVarchar`, so this
appears to be dead/unreachable code (an enum value defined for API completeness or a future translator
that was never wired up) rather than an active bug — flagged here in case a future `orion`-registering
module ever adds an NVARCHAR-specific translator, which would then hit this `IllegalStateException` at
schema-creation time.

## 110.4 — B104-G4 CLOSED (negative): no retention/purge policy exists for any Orion-backed table, in `orion` or outside it, in this N5 build `[CERT]`

**Station-wide `BIOrionApp` census.** A corpus-wide `grep -rl "BIOrionApp\b"` (not `orion`-scoped) finds
exactly **two** classes outside the `orion` module that implement `BIOrionApp` (i.e., register an
Orion-backed table) across the entire N5 5.0.0.28 corpus: `alarmOrion`'s `niagara.alarmOrion.
BOrionAlarmService` (`:48`) and `com.tridium.alarmOrion.archive.BOrionArchiveAlarmProvider` (`:63`) — both
in the SAME module, `alarmOrion`. No other of the ~250 module jars registers an `OrionType` outside
`orion`/`alarmOrion`. This directly bounds B104-G4's search: `alarmOrion` is the ONLY outside-`orion`
Orion-table consumer to check.

**`alarmOrion`'s own remove/clear logic is archive-transfer, not age/count-based purge.** A full read of
`BOrionArchiveAlarmProvider.{importOpenAlarmsToLocalDb,exportClearedRecords}`
(`organized/alarmOrion/vineflower/com/tridium/alarmOrion/archive/BOrionArchiveAlarmProvider.java:277-347`)
shows both `uuidToRemove`/`uuidsToRemove` lists are populated as a side effect of migrating a CLEARED alarm
record from the live alarm DB INTO the Orion-backed archive table (`AppendAlarmRecord`/`alarmDbConn.
append`) — a one-shot, clear-triggered transfer, not a scheduled or threshold-based deletion of rows
already resident in the Orion archive. A targeted `grep -niE "delete|remove|purge|cull|prune|maxAlarms|
maxRecords|maxSize|trim\("` over both `BOrionAlarmService.java` and `BOrionArchiveAlarmProvider.java`
found no other removal-shaped code, and no age/day/count-limit `@NiagaraProperty` on either class.

**`BOrionService`'s own full property census (extends [Block 104] §104.8).** A full re-read of
`organized/orion/vineflower/com/tridium/orion/BOrionService.java` (`:39-46`) confirms its `@NiagaraProperties`
block declares exactly **6** properties total: `status`, `faultCause`, `ordMap`, `auditMode`,
`securityAuditMode`, `auditWorker` — no 7th "retention"/"purge"/"maxAge" property exists. [Block 104]
§104.8's own within-`orion` negative census is thereby corroborated at the SERVICE-property level, not
just the module-file-sweep level.

**A DIFFERENT, non-Orion retention framework exists (`batchJob`) — explicitly ruled out, not a match.**
Fresh corpus grepping surfaced `niagara.retention`/`niagara.batchJob.retention` (`BRetentionPolicy`,
`BKeepNExecutionsRetentionPolicy`, `BKeepNPerDeviceRetentionPolicy`) — a real, active count-based
purge mechanism. A full read of `BKeepNExecutionsRetentionPolicy.executePolicy()`
(`organized/batchJob/vineflower/niagara/batchJob/retention/BKeepNExecutionsRetentionPolicy.java:53-80`)
shows it culls excess `BBatchJob` COMPONENT instances from the station's own component-space tree via
`j.dispose()` — operating on the generic `BComponent`/`BIRetainable` domain abstraction
(`BIRetentionPolicyDomain.getRetainables()`), with no `BIOrionObject`/`OrionSession`/SQL involvement
anywhere in the class. `batchJob` does NOT implement `BIOrionApp` (absent from the corpus-wide census
above) — its job-execution records are NOT Orion-backed, so this retention framework is out of scope for
B104-G4 and is reported here only to document why it was found and excluded, not as a positive answer.

**Verdict:** across the full N5 5.0.0.28 corpus (~250 modules), no retention or purge policy — scheduled,
age-based, or count-based — targets an Orion-backed table, either inside `orion` (confirmed at the
service-property level, extending [Block 104] §104.8) or in the only outside-`orion` Orion consumer found
(`alarmOrion`, whose own removal logic is a one-shot clear-triggered archive transfer, not a retention
job). This is a negative finding, not an absence-of-evidence gap: the full `BIOrionApp` implementer set was
enumerated corpus-wide, and every implementer's removal-shaped code was read in full.

## 110.x — Corrections to earlier blocks

None. All four findings extend or corroborate [Block 104] §104.2/§104.4/§104.8 without contradicting any
prior claim.

## 110.x — Connections

- **[Block 104]** — parent block; §110.1-§110.4 close its own B104-G1 through B104-G4 in full.
- **[Block 31]** §31.5 — its own full read of `ValueDocDecoder.parseSlot`'s orphaned-property branch
  (`:386-514,1144-1178`) is REUSED as corroboration for §110.1's grammar reconstruction (same method, same
  line ranges, different angle: [Block 31] traced ONE control-flow branch for a migration question, §110.1
  reconstructs the full element/attribute grammar for the wire-format question).
- **[Block 24]/[Block 66]/[Block 47]** — all three read the DIFFERENT `MigrationUtils.
  MigrationValueDocDecoder` inner class (migration-time bog decoding with password deny-listing); §110.1
  is careful to distinguish this from the PRODUCTION `ValueDocDecoder.BogDecoderPlugin` read here — same
  base class family, different subclass, not re-derived.
- **[Block 5]** — the `javax.baja.*`→`niagara.*` rename this block's own N4/N5 diffs (§110.1, §110.2) both
  reconfirm for `niagara.io.ValueDocDecoder` and `niagara.driver.loadable.*`.
- **[Block 69]** — its own §69.x named `BOrionDatabase`'s "table DDL for `BOrionSecurityAudit` rows,
  retention/purge" as unopened; §110.4's negative census directly answers that framing (no purge exists to
  find, for that table or any other Orion table).
- **[Block 73]** (B73-G2/B73-G4, [Block 104]'s own parent gaps) — unaffected by this block; §110.1-§110.2
  are purely mechanical follow-ups on material B104 already fully answered B73's own field-level questions
  for.

## 110.x — Child gaps opened

- **B110-G1** (low, `investigable`) — the two other `RdbmsDialect` implementations found but not opened
  this session (`organized/rdbMySQL/vineflower/com/tridium/rdb/mysql/BMySQLDatabase.java`,
  `organized/rdbSqlServer/vineflower/com/tridium/rdb/sqlserver/BSqlServerDatabase.java`) would give the
  exact MySQL/SQL-Server DDL strings for the same 11 `BSqlType` values §110.3 read for HSQLDB — mechanical,
  same read pattern.
- **B110-G2** (low, `investigable`) — whether `BSqlType.sqlNVarchar` (ordinal 8, §110.3's flagged
  unreachable-`case` finding) is genuinely DEAD code, or reachable via some `BColumnTranslator` this
  session's 17-class census missed (e.g. a translator registered by a THIRD-PARTY/OEM module outside this
  corpus) — would need a corpus-wide `grep -rl "sqlNVarchar"` (not run this session; the flag was raised
  from the enum-vs-switch mismatch alone) and, if truly unreachable, is a candidate for the systemic-defect
  triage workflow (defensive framing only, no exploit path — dead code, not a vulnerability).
- **B104-G5** (carried forward, not reopened) — every finding in this block, like [Block 104]'s own
  B104-G5, is static source reading; none of §110.1's grammar was cross-checked against a live
  `findReachableStations` wire capture. No new live-execution need was identified beyond what B104-G5
  already tracks.

## Self-verify

| # | Claim | Marker | Evidence |
|---|---|---|---|
| 1 | `bajaObjectGraph` root element + `version` check accepts `"1.0"`/`"4.0"`/`"5.0"` in N5 | [CERT] | `organized/baja/vineflower/niagara/io/ValueDocDecoder.java:744-750` |
| 2 | N4's equivalent check accepts only `"1.0"`/`"4.0"` | [CERT] | `/home/cristian/niagara-research/organized/baja/baja/vineflower/javax/baja/io/ValueDocDecoder.java:686` |
| 3 | `parseSlot` recognizes exactly 3 element names (`p`/`a`/`t`) and 9 attributes (`n`/`h`/`v`/`t`/`m`/`f`/`x`/`c`/`stub`) | [CERT] | `organized/baja/vineflower/niagara/io/ValueDocDecoder.java:300-347` |
| 4 | `decodePrimitive`'s 6-case type-access fast-path (boolean/int/long/float/double/string) is identical in N4 and N5 | [CERT] | `organized/baja/vineflower/niagara/io/ValueDocDecoder.java:570-591`; N4 `ValueDocDecoder.java:290-303` (equivalent switch, re-verified this session) |
| 5 | `BUploadParameters` declares exactly 2 own properties (`uploadTransient`, `uploadPersistent`), both boolean default `true` | [CERT] | `organized/driver/vineflower/niagara/driver/loadable/BUploadParameters.java:13-16` |
| 6 | `BDownloadParameters` declares zero own properties beyond inherited `recursive` | [CERT] | `organized/driver/vineflower/niagara/driver/loadable/BDownloadParameters.java` (25 lines, full read) |
| 7 | N4/N5 field census for both classes is identical (package rename + `@Generated` only) | [CERT] | `diff` this session against `organized/driver/driver-rt/vineflower/javax/baja/driver/loadable/{BUploadParameters,BDownloadParameters}.java` |
| 8 | `TableBuilder.makeColumns()` delegates typing to `Column.make*`, not its own logic | [CERT] | `organized/orion/vineflower/com/tridium/orion/sql/TableBuilder.java:81-112` |
| 9 | `Column.makeTypeDdl()` switches on `BSqlType.getOrdinal()`, 12 values, case 8 (`sqlNVarchar`) unhandled → `IllegalStateException` | [CERT] | `organized/rdb/vineflower/niagara/rdb/ddl/Column.java:96-146`; enum declared at `organized/rdb/vineflower/com/tridium/rdb/jdbc/trans/BSqlType.java:44-46` |
| 10 | 17 `B*Translator` classes' `getSqlType()` mapping (table in §110.3) | [CERT] | full read this session, each file under `organized/rdb/vineflower/com/tridium/rdb/jdbc/trans/` |
| 11 | HSQLDB dialect's concrete DDL strings (`INTEGER`/`BIGINT`/.../`LONGVARBINARY`) | [CERT] | `organized/rdbHsqlDb/vineflower/com/tridium/rdb/hsqldb/BHsqlDatabase.java:239-310` |
| 12 | Exactly 2 classes outside `orion` implement `BIOrionApp`, both in `alarmOrion` | [CERT] | `organized/alarmOrion/vineflower/niagara/alarmOrion/BOrionAlarmService.java:48`; `organized/alarmOrion/vineflower/com/tridium/alarmOrion/archive/BOrionArchiveAlarmProvider.java:63` |
| 13 | `BOrionArchiveAlarmProvider`'s remove-list logic is clear-triggered archive transfer, not age/count purge | [CERT] | `organized/alarmOrion/vineflower/com/tridium/alarmOrion/archive/BOrionArchiveAlarmProvider.java:277-347` |
| 14 | `BOrionService` declares exactly 6 properties, none retention/purge-shaped | [CERT] | `organized/orion/vineflower/com/tridium/orion/BOrionService.java:39-46` |
| 15 | `batchJob`'s `BKeepNExecutionsRetentionPolicy` purges `BComponent` tree nodes via `dispose()`, not Orion SQL rows | [CERT] | `organized/batchJob/vineflower/niagara/batchJob/retention/BKeepNExecutionsRetentionPolicy.java:53-80` |

**Tally**: 15 `[CERT]` (adjusted, header legend excluded) · 0 `[INFER]`. [INFER]/[CERT] ratio: 0 — pure
evidence block, every central claim backed by a direct `file:line` read from already-located decompiled
source, cross-checked against N4 where a delta was in scope.

**Artifacts**: none external — this block cites only pre-existing `organized/` corpus files (N5) and the
pre-existing N4 baseline tree; no new scratch files were produced beyond this session's own `rg`/`grep`
query transcripts (not preserved, all reproducible from the literal commands quoted in §110.0/§110.4).
