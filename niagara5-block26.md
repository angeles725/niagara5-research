# Block 26 — History capacity after N4→N5: the removed storage-size mode

> Research of **whether N4's removed `BCapacity` storage-size restriction mode (`restrictBy=2`) is a live
> migration hazard for a station upgraded from N4 to N5**, closing [Block 20]'s child gap **B20-G4** (history
> rollover/trim mechanism) and the *static* half of **B20-G1** (the `BCapacity`/`Capacity.js` client-layer
> contradiction). Covers: (1) independent reconfirmation of the N5 server-side removal (bytecode + decompiled
> source, fresh this session); (2) the exact on-disk rollover/capacity-enforcement mechanism in all three N5
> history-table backends (`BFixedLengthHistoryTable`/`PageManager`, `BRecordStoreHistoryTable`/`RecordStore`,
> `BHistoryDbTable`), each diffed line-for-line against its N4 twin; (3) whether any `migrator.jar`/
> `propMigration.jar` converter touches `BCapacity` or history config; (4) the `Capacity.js`/`CapacityEditor.js`
> web-UI contradiction, resolved for both N4 and N5; (5) a census of PANCCADIA's actual `config.bog` capacity
> values. Does **not** cover a live N5 station probe (no live 5.0.0.28 station reachable this session — the
> dynamic half of B20-G1 stays open, §26.12), nor `BHistoryDbTable`'s SQL/archive-provider internals beyond the
> capacity-enforcement call site, nor `.hdb` binary layout (out of scope, already covered elsewhere).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as [Block 20]/[Block 14] (`etc/brand.properties:
> workbench.notice`) vs. baseline **N4 4.14.0.162** (Honeywell OptimizerSupervisor OEM distribution, same
> baseline as prior blocks).
>
> Sources (all local, read-only):
> - N5 `history.jar` — `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/history.jar`, sha256
>   `9fc1c9b1768fdc6e44456c2374df802565ea5afecf69d443f375082b49a612cf` (fresh `sha256sum` this session) —
>   decompiled this session with Vineflower 1.12.0 to `/tmp/claude-1000/n5b26/decompiled/` (session scratch,
>   not preserved in the corpus, re-derivable from the jar above per METHODOLOGY §5's beautified-temp rule) and
>   independently cross-checked with `javap -p -c` (`/home/linuxbrew/.linuxbrew/opt/openjdk@26/bin/javap`,
>   v26.0.2.1) directly on the unzipped `.class` files in `/tmp/claude-1000/n5b26/history_unzip/`.
> - N5 `migrator.jar` — same path, sha256 `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08`
>   (matches [Block 14]'s citation for the same file — cross-session hash agreement) — unzipped to
>   `/tmp/claude-1000/n5b26/migrator_unzip/`; `BCloudHistoryConverter.class` decompiled to
>   `/tmp/claude-1000/n5b26/decompiled_migrator/`.
> - N5 `propMigration.jar` — same path, sha256
>   `5ee675c6809354f234b2d0c7ad1826837689a51a3603b6fa1b7de02ca5f4f031` — unzipped to
>   `/tmp/claude-1000/n5b26/propmig_unzip/`.
> - N4 originals (already decompiled, Vineflower, pre-existing in the sibling `niagara-research` corpus):
>   `organized/history/history-rt/vineflower/javax/baja/history/BCapacity.java`,
>   `organized/history/history-rt/vineflower/com/tridium/history/file/fixed/{PageManager.java,
>   BFixedLengthHistoryTable.java}`, `organized/history/history-rt/vineflower/com/tridium/history/file/
>   recstore/RecordStore.java`, `organized/history/history-rt/vineflower/com/tridium/history/db/
>   BHistoryDbTable.java`, `organized/history/history-wb/vineflower/com/tridium/history/ui/BCapacityFE.java`,
>   `organized/history/history-ux/vineflower/rc/fe/CapacityEditor.js`,
>   `organized/history/history-rt/vineflower/history-rt.lexicon` — all under `/home/cristian/niagara-research/`.
> - [Block 20] (`niagara5-block20.md`) §20.5/§20.10 — the prior static read that raised B20-G1/B20-G4; this
>   block re-derives every numbered `[CERT]` fact independently rather than trusting the prior citations, per
>   this task's "settle statically" instruction, and corrects two of its framings (§26.6).
> - [Block 14] (`niagara5-block14.md`) §14.4 — the 58-type `migrator.jar` converter catalog census, cross-
>   checked here directly against the raw `module.xml` rather than reused.
> - PANCCADIA live station config (gitignored, read-only): `/home/cristian/niagara5-research/poc/
>   n5mig-panccadia/in/config.bog`, read via Python `zipfile` (§26.9) — counts only, no station identifiers
>   beyond the file itself are reported.
>
> Method: `unzip` each jar to session scratch; Vineflower 1.12.0 decompile of `history.jar` in full and one
> targeted class of `migrator.jar`; `javap -p -c` cross-check of `BCapacity.class` bytecode; `grep`/`diff`
> against the pre-existing N4 decompiled trees in `niagara-research` (fresh re-reads this session, not
> citation reuse); Python `zipfile` + regex census of the PANCCADIA `.bog`. Markers (canonical list:
> METHODOLOGY §3): `[CERT]` local primary source (`file:line`, decompiled-tree paths declared per §11's
> decompiled-tree convention, anchored by the jar's sha256 above) · `[INFER]` deduction.
>
> History persistence/runtime layer. Connects [Block 20] (raised B20-G1/B20-G4, corrected here), [Block 14]
> (migrator SPI/converter catalog, cross-checked here for history-specific coverage).
>
> **Type:** `mixed` — evidence (fresh decompile/bytecode/diff reading, own `[CERT]`) combined with one
> synthesis/correction section (§26.6) that revises [Block 20]'s hazard framing using facts assembled across
> §26.2–§26.5, and one dataset section (§26.9, PANCCADIA capacity census, per-record certainty not needed —
> single regex pass over one preserved-in-place file, reported as counts).

---

## 26.1 — Scope recap

[Block 20] §20.5 found a real, clean removal of N4's `BCapacity` storage-size mode (`restrictBy=2`) from N5's
server-side class, an apparently-contradictory web-UI model (`Capacity.js`) that still declares the removed
mode, and an `[INFER]` migration hazard (an N4 byte-size cap silently reinterpreted as a record-count cap on
N5) — then opened two child gaps to settle it: **B20-G1** (probe a live station to see which side of the
contradiction wins) and **B20-G4** (open the actual rollover-mechanism code, not yet read in that block). This
block does the STATIC half of both: it opens every file B20-G4 named, diffs the enforcement mechanism against
N4 line-for-line, and traces the UI contradiction to its root cause instead of leaving it as an open question.
The result **sharpens and partially corrects** [Block 20]'s hazard framing (§26.6) rather than simply
confirming it — the mechanism is unchanged from N4 (closing B20-G4), and the UI contradiction turns out to
predate N5 entirely (closing B20-G1's static half); only the exact scenario under which the hazard fires turns
out to be much narrower than "any N4 storage-size history migrated to N5."

## 26.2 — N5's `BCapacity` removal, reconfirmed independently `[CERT]`

Fresh decompile this session, `niagara/history/BCapacity.java` (Vineflower 1.12.0 on `history.jar`,
sha256 above): only two restriction constants exist, `RESTRICT_NONE = 0` and `RESTRICT_RECORD_COUNT = 1`
[CERT] `/tmp/claude-1000/n5b26/decompiled/niagara/history/BCapacity.java:19-20`; the only two factory methods
are `makeByRecordCount`/`makeUnlimited` [CERT] `:31-37`; `isUnlimited()`/`isByRecordCount()` are the only two
mode predicates [CERT] `:44-50`; `getMaxRecords()` is a flat two-way branch — `restrictBy==0 → -1`, else
`(int)max` (clamped to `Integer.MAX_VALUE`) — **with no `restrictBy==2` case at all** [CERT] `:52-58`; there is
no `getMaxStorage()`/`isByStorageSize()`/`makeByStorageSize()` method anywhere in the file. `toString(Context)`
is the same flat two-way branch, with no `" KB"` unit [CERT] `:100-106`.

Independently cross-checked at the bytecode level this session (not reused from [Block 20]): `javap -p` on
`niagara/history/BCapacity.class` lists exactly the same reduced member set — two restriction fields, two
factories, two predicates, `getMaxRecords`/`hashCode`/`equals`/`encode`/`decode`/`encodeToString`/
`decodeFromString`/`toString`/`getType`, nothing else [CERT] `javap -p niagara/history/BCapacity.class`
(`/tmp/claude-1000/n5b26/history_unzip/`). `javap -p -c` on `getMaxRecords()` shows the literal opcode sequence
`getfield restrictBy; ifne 9; iconst_m1; ireturn; …(int)max…` — a single `ifne` branch on `restrictBy != 0`,
no comparison against the literal `2` anywhere in the method body [CERT] same command, `getMaxRecords` bytecode
listing. A fresh `grep -rl` for `getMaxStorage|isByStorageSize|makeByStorageSize|RESTRICT_STORAGE_SIZE` across
every `.java` file this session's Vineflower decompile produced from `history.jar` returns **zero matches**
[CERT] `grep -rl … /tmp/claude-1000/n5b26/decompiled` (exit code 1, no hits) — the removal is clean and total
on the server side, confirmed by two independent reads (decompiled source + raw bytecode) rather than one.

## 26.3 — The persistence round-trip validates nothing, either version `[CERT]`

`BCapacity.encode(DataOutput)` writes `restrictBy` (int) then `max` (long) unconditionally [CERT]
`/tmp/claude-1000/n5b26/decompiled/niagara/history/BCapacity.java:74-77`; `decode(DataInput)` reads them back
and constructs a new `BCapacity` with **no range/validity check on `restrictBy`** [CERT] `:79-83`.
`encodeToString()`/`decodeFromString(String)` do the same round-trip through a `"<restrictBy>:<max>"` string
form, again with no validation of `restrictBy` beyond `Integer.parseInt` succeeding [CERT] `:85-98`. This is
**identical in shape** to N4's own `encode`/`decode`/`encodeToString`/`decodeFromString` [CERT]
`/home/cristian/niagara-research/organized/history/history-rt/vineflower/javax/baja/history/BCapacity.java:
100-124` (fresh re-read this session) — the round-trip itself never changed; what changed is only what
`getMaxRecords()` does with a `restrictBy` value the round-trip let through unchecked (§26.2 vs. N4's guard,
quoted in §26.5).

**Worked example.** N4 `BCapacity.makeByStorageSize(10 * 1024 * 1024)` → `new BCapacity(2, 10485760)` [CERT]
N4 `BCapacity.java:36-38`; `encodeToString()` → the literal string `"2:10485760"` [CERT] `:111-117`
(`s.append(restrictBy); s.append(':'); s.append(max)`, evaluated for `restrictBy=2, max=10485760`). On N5,
`decodeFromString("2:10485760")` parses cleanly into `BCapacity(2, 10485760)` (no version-specific parsing
difference — the string grammar is identical) [CERT] N5 `BCapacity.java:93-98`. That object: `isUnlimited()`
→ `false` (`restrictBy≠0`); `isByRecordCount()` → `false` (`restrictBy≠1`, a literal `==1` test, not "any
non-zero value" — same in both versions [CERT] N5 `:48-50` vs. N4 `:53-55`); `getMaxRecords()` → N5 returns
`10485760` (the raw byte count, silently reinterpreted as a record count); N4's equivalent call would instead
**throw** `IllegalStateException("Capacity is not restricted by record count.")` [CERT] N4 `BCapacity.java:
64-65`. This is the literal mechanism behind [Block 20]'s `[INFER]`; §26.6 narrows exactly when it can fire.

## 26.4 — Capacity enforcement mechanism: three call sites, byte-identical to N4 `[CERT]`

N5 has three history-table backends, chosen by record type at `BFileHistoryTable.make()`: `rec.isFixedSize() ?
new BFixedLengthHistoryTable() : new BRecordStoreHistoryTable()` [CERT] `/tmp/claude-1000/n5b26/decompiled/
com/tridium/history/file/BFileHistoryTable.java:112`. `isFixedSize()` returns `true` for
`BBooleanTrendRecord`/`BEnumTrendRecord`/`BNumericTrendRecord` and `false` for `BStringTrendRecord` [CERT]
`/tmp/claude-1000/n5b26/decompiled/niagara/history/{BBooleanTrendRecord.java:76-78,
BEnumTrendRecord.java:56-58, BNumericTrendRecord.java:65-67, BStringTrendRecord.java:55-57}` — so Boolean/
Enum/Numeric histories (everything ColdRoomPan/CompPan/DashboardPan would realistically log) use the fixed
backend, String histories use the record-store backend. A third backend, `BHistoryDbTable` (SQL/archive-
provider-style storage), is a separate abstract path with its own capacity check.

**(a) `BFixedLengthHistoryTable` / `PageManager` — the ONLY unconditional caller of `getMaxRecords()`.**
`createDataSection()`: `if (!capacity.isUnlimited()) { maxRecords = capacity.getMaxRecords(); } else {
maxRecords = Integer.MAX_VALUE; }` — called for **any** non-unlimited capacity, not gated on
`isByRecordCount()` [CERT] `/tmp/claude-1000/n5b26/decompiled/com/tridium/history/file/fixed/
BFixedLengthHistoryTable.java:48-54`; that `maxRecords` sizes the `PageManager` at file-creation time [CERT]
`:56`. `doAppend()` separately gates the "stop when full" policy strictly on `capacity.isByRecordCount()`
[CERT] `:114-123` — for a `restrictBy=2` capacity this branch is skipped (never stops), and the record always
reaches `PageManager.append()` [CERT] `:125`. Inside `PageManager.append()`, capacity enforcement is
**unconditional and policy-independent**: `recordCount++; if (recordCount > this.capacity) {
firstPage.trimFromStart(...); }` [CERT] `/tmp/claude-1000/n5b26/decompiled/com/tridium/history/file/fixed/
PageManager.java:212-221` — this ring-buffer trim runs regardless of `BFullPolicy`, using whatever raw
`this.capacity` value `createDataSection()` handed it. Net effect for the ambiguous state: the file **does**
self-cap, but at the mis-scaled `getMaxRecords()` value (§26.3's example: 10,485,760 records instead of 10
MB).

**(b) `BRecordStoreHistoryTable` / `RecordStore` — enforcement entirely gated, no fallback.**
`RecordStore.append()`: `boolean roll = false; int maxRecords = Integer.MAX_VALUE; if
(capacity.isByRecordCount()) { … roll = true (or stop-check); }` — for `restrictBy=2`, `isByRecordCount()` is
`false`, so `maxRecords` stays `Integer.MAX_VALUE` and `roll` stays `false` [CERT] `/tmp/claude-1000/n5b26/
decompiled/com/tridium/history/file/recstore/RecordStore.java:181-194`; the trim loop at the end of `append()`
is itself gated on `if (roll) { … }` [CERT] `:234-245` — with `roll=false` it never runs. **No enforcement of
any kind fires** for the ambiguous state on this backend (String histories): the store grows without bound.

**(c) `BHistoryDbTable` — same gated-no-fallback pattern.** `if (capacity.isByRecordCount() &&
this.getRecordCount() > capacity.getMaxRecords()) { … }` [CERT] `/tmp/claude-1000/n5b26/decompiled/com/
tridium/history/db/BHistoryDbTable.java:103-105` — again strictly gated on `isByRecordCount()`, so a
`restrictBy=2` capacity gets zero enforcement here either.

**All three mechanisms are byte-for-byte unchanged from N4** — this closes **B20-G4**. Fresh diff this
session, same line ranges in both versions (only the `javax.baja→niagara` package rename differs):
`BFixedLengthHistoryTable.createDataSection()`'s `!isUnlimited()` gate [N4 `:46-47` vs. N5 `:50-51`],
`doAppend()`'s `isByRecordCount()` gate [N4 `:112` vs. N5 `:115`], `PageManager.append()`'s unconditional
`recordCount > capacity` trim [N4 `:215-221` vs. N5 `:212-221`], `RecordStore.append()`'s `isByRecordCount()`
gate with the `roll` flag [N4 `:184-192` vs. N5 `:181-194`], and `BHistoryDbTable`'s identical gated check [N4
`organized/history/history-rt/vineflower/com/tridium/history/db/BHistoryDbTable.java:99-100` vs. N5 `:103-104`]
— all `[CERT]`, all confirmed by direct file reads this session, not citation reuse. **The on-disk rollover
ALGORITHM never changed; the only functional delta anywhere in this chain is `BCapacity.getMaxRecords()`
dropping its `restrictBy==2` guard clause** (§26.5).

## 26.5 — Was storage-size mode ever actually reachable? No — not even on N4 `[CERT]`

This is the key correction to [Block 20]'s framing. **`BCapacity.getMaxStorage()` has exactly one caller in
the entire N4 corpus, and it is a UI display method, never an enforcement path**: `grep -rn "getMaxStorage()"`
across the whole `niagara-research` history corpus returns only `BCapacityFE.java:84-85` (loading a previously
-saved value back into the edit field for display) [CERT] `/home/cristian/niagara-research/organized/history/
history-wb/vineflower/com/tridium/history/ui/BCapacityFE.java:84-85` — **no enforcement code anywhere (N4 or
N5) ever calls `getMaxStorage()`**; §26.4's three enforcement sites all call `getMaxRecords()` only.

**N4's own Workbench field editor never actually lets an operator select storage-size mode.** Its dropdown
list widget is populated with exactly two entries: `typeChoice.getList().addItem(lex.getText("unlimited"))`
and `.addItem(lex.getText("recordCount"))` [CERT] `/home/cristian/niagara-research/organized/history/
history-wb/vineflower/com/tridium/history/ui/BCapacityFE.java:55-56` — a fresh `grep -n "addItem"` over the
whole 137-line file finds no third call [CERT] same file, confirmed no other `addItem` site exists. Yet the
class still declares `BY_STORAGE_SIZE = 2` [CERT] `:36`, still has `doLoadValue()` branches for it — one of
which is dead code, shadowed by an earlier `||` check (`if (c.isUnlimited() || c.isByStorageSize()) {
typeChoice.setSelectedIndex(0); … }` maps a real storage-size value to the **"Unlimited" slot**, never reaching
the `else if (c.isByStorageSize())` branch two lines later) [CERT] `:73-86` — and `doSaveValue()`'s
`typeIndex==2 → makeByStorageSize(...)` branch [CERT] `:96-99` is **unreachable**, because
`typeChoice.getSelectedIndex()` can only ever return `0` or `1` (only two list items exist to select). This is
vestigial N4 code, not a live UI path — confirmed structurally (the dropdown's actual item count), not by
inference from the dead branches' mere presence.

**The web UI shows the identical pattern, in both N4 and N5, confirmed by direct diff.** N5's
`CapacityEditor.js` `TYPES` map has exactly two entries — `RESTRICT_NONE`/`RESTRICT_RECORD_COUNT`, no
storage-size — [CERT] `/tmp/claude-1000/n5b26/history_unzip/rc/fe/CapacityEditor.js:28-31`; its `doLoad()`
collapses **any** non-record-count capacity to the "Unlimited" selection (`byRecords = capacity.isByRecordCount();
capacityType = byRecords ? RESTRICT_RECORD_COUNT : RESTRICT_NONE`) [CERT] `:138-142`; `doRead()` reconstructs a
fresh `Capacity` from whatever the two visible sub-editors currently hold [CERT] `:152-155` — saving after
opening the editor on a migrated storage-size history would silently **overwrite** it with a genuine
`RESTRICT_NONE` (true unlimited), an unannounced but benign-direction data loss (loosens, does not tighten,
the operator's original intent). A fresh `diff` this session against N4's own `history-ux` module
`CapacityEditor.js` shows the same `TYPES` map (`map.put(…RESTRICT_NONE); map.put(…RESTRICT_RECORD_COUNT)`,
no third entry) and the same `doLoad`/`doRead` logic — only cosmetic minifier-output differences (variable
names, whitespace) [CERT] `/home/cristian/niagara-research/organized/history/history-ux/vineflower/rc/fe/
CapacityEditor.js:35-38,154,169` vs. N5 `:28-31,138,152` — **this mislabel-then-launder UI behaviour predates
N5 entirely; it is not a migration-introduced regression.** This resolves **B20-G1's static half**: the
"contradiction" is not "which side wins live" — neither Workbench nor web UI, on N4 or N5, can ever construct
or correctly redisplay a storage-size capacity through normal use; both simply misrepresent one as unlimited
if it somehow exists.

**The `Capacity.js` BajaScript *model* (as opposed to the `CapacityEditor.js` *widget*) is the one place mode-2
support is still functionally intact — and it is stricter than N5's server class, not looser.** Its
`getMaxRecords()` **throws** for anything but `RESTRICT_RECORD_COUNT`/`RESTRICT_NONE` — `default: throw new
Error('Capacity not restricted by record count.')` [CERT] `/tmp/claude-1000/n5b26/history_unzip/rc/baja/
Capacity.js:121-129` — matching N4 server behaviour, not N5's silent reinterpretation; it also still exposes
`isByStorageSize()` [CERT] `:145-146` and a `" KB"`-unit `toString()` branch [CERT] `:101-112`, and
`history.lexicon:60` still carries `storageSize=Storage Size` [CERT] `/tmp/claude-1000/n5b26/history_unzip/
history.lexicon:60` — but N4's own `history-rt.lexicon:60` carries the **identical** entry [CERT]
`/home/cristian/niagara-research/organized/history/history-rt/vineflower/history-rt.lexicon:60` (same key,
same line number) — this is pre-existing lexicon debt, not something N5 introduced. `Capacity.js`'s model-level
support is real (it can `decodeFromString` and `encodeToString` a `restrictBy=2` value, and would not throw
doing so — only `getMaxRecords()` throws), but nothing in the actual `CapacityEditor.js` widget ever
constructs one, so this is dead-but-not-dangerous surface: a script calling the BajaScript API directly
(bypassing the widget) could still build one, but the standard editor cannot.

## 26.6 — Corrected hazard statement `[INFER]`

[Block 20] framed the hazard as "any N4 station whose history configuration was persisted with `restrictBy=2`"
— §26.5 narrows this considerably: because neither N4's Workbench editor nor its web editor can *construct* a
storage-size capacity through normal use (both dropdowns only ever offered 2 items), and because
`BFixedLengthHistoryTable.createDataSection()` calls `getMaxRecords()` unconditionally for any non-unlimited
capacity — which **throws on N4** for `restrictBy=2` [CERT] N4 `BCapacity.java:64-65` — **a Boolean/Enum/
Numeric history extension that was actually ENABLED and RUNNING on N4 could never have had a storage-size
capacity**: N4 itself would have refused to create its backing file with an `IllegalStateException` the moment
the extension tried to open. The narrowed, still-real exposure path is: **a Boolean/Enum/Numeric history
extension configured with a legacy `restrictBy=2` capacity (surviving from an AX-era or otherwise pre-N4-UI
origin, since neither N4 UI can create one fresh) that was never enabled/started under N4** — the config
persisted in the `.bog` but the fixed-length file was never created, so N4's throw was never triggered — **and
is enabled for the first time only after the station is on N5.** At that point `createDataSection()` runs
against N5's non-throwing `getMaxRecords()` (§26.2/§26.3) and silently creates a file sized to the raw byte
count reinterpreted as a record count (§26.4a) — self-capping, but at a value that is typically many orders of
magnitude larger than the operator's original byte-size intent (§26.3's worked example: 10 MB → 10.48M
records). For String histories or DB-backed histories, the same ambiguous capacity would already have been
silently unenforced under N4 (§26.4b/c apply identically pre- and post-migration — `isByRecordCount()` gates
both), so there is **no N4→N5 behavioural change at all** for those two backends specifically from this angle
— the delta is isolated to the fixed-length backend's `createDataSection()` throw-vs.-silent difference.
**Client relevance measured (§26.9): zero** for PANCCADIA specifically, and structurally near-zero fleet-wide
given how narrow the exposure window is (a never-activated legacy-origin history extension, reactivated only
post-upgrade).

## 26.7 — Migrator SPI: no converter or descriptor touches `BCapacity` or history config `[CERT]`

`migrator.jar`'s `META-INF/module.xml` `<types>` block (58 entries, cross-checked here directly against the
raw XML, not reused from [Block 14]'s abridged table) contains exactly **one** History-adjacent converter:
`com.tridium.migrator.cloudLink.BCloudHistoryConverter` [CERT] `/tmp/claude-1000/n5b26/migrator_unzip/
META-INF/module.xml:107`. Decompiled fresh this session: its `getConvertTypes()` returns only
`["cloudLink:HistoriesChannel", "cloudLink:CloudArchiveHistoryProvider"]` [CERT] `/tmp/claude-1000/n5b26/
decompiled_migrator/BCloudHistoryConverter.java:25,34-36] — a `cloudLink`-module bog-element/typespec rename
(`HistoriesChannel`→`HistoryChannel`) and a property-relocation for cloud archive providers, operating on
`BComponent`/`BComplex` bog elements via `convertXElem`/`convertComplex`. **It never touches `history:*`
types, the `capacity` property, or a `b:Capacity` value.** A fresh `grep -io` for `history`/`capacity` across
`migrator.jar`'s `module.xml` finds only the module dependency declaration on `history` itself (line 27) plus
this one unrelated cloudLink converter [CERT] `grep -io ".\{0,40\}\(history\|capacity\).\{0,40\}"
migrator_unzip/META-INF/module.xml`.

`propMigration.jar` is a **generic declarative DSL** (10 descriptor types —
`BNewType`/`BNumPropNameChange`/`BOrdProps`/`BOrigSimple`/`BPropFacetsChange`/`BPropFlagsChange`/
`BPropNameChange`/`BPropRemove`/`BPropValueChange`/`BSimpleEncodingChange`/`BTypeNewName` — plus matching
`.converters.B*Converter` interpreters), not a data file: it ships **zero concrete descriptor instances**
[CERT] `find /tmp/claude-1000/n5b26/propmig_unzip -name "*.class"` — 19 classes, all generic framework types,
no `History`/`Capacity`-named class anywhere. Per [Block 14] §14.3's established pattern (a module registers
its own migrator/propMigration descriptors in its OWN `module-include.xml`, not inside the framework jar), the
concrete descriptor instances that would apply a `propMigration` rule to `history:*` would have to live in
`history.jar`'s own manifest — a fresh `grep -in "propmigration\|migrator\|migration"` over the entire 476-line
`history.jar` `META-INF/module.xml` returns **zero matches** [CERT] `grep -in … history_unzip/META-INF/
module.xml` (no output). **No converter, in either jar, and no declarative descriptor registered by `history`
itself, touches `BCapacity` or any history-config property.** The hazard in §26.6 is confirmed structurally
unmitigated by `n5mig`. (Architecturally this is also the expected result independent of the catalog census:
`BCapacity` is a `BSimple`, persisted as a property VALUE via `encodeToString`/`decodeFromString`, not a typed
bog-element with its own `t="module:Type"` entry — the `BIBogElementConverter`/`ConverterRegistry` layer [Block
14] §14.3 documented operates on component-level typespecs, not simple-value encodings, so even a populated
catalog would need a `propMigration`-style per-property descriptor to intercept it, and none exists.)

## 26.8 — PANCCADIA `config.bog`: measured capacity census `[CERT]`

Read-only Python `zipfile` census of the preserved, gitignored `/home/cristian/niagara5-research/poc/
n5mig-panccadia/in/config.bog` (single `file.xml` entry, 486,798 bytes) this session — reporting counts only,
per this task's constraint. A regex pass for `<p n="capacity" … t="h:Capacity" … v="…">` elements finds
**23** capacity properties total [CERT] `python3 zipfile` + `re.findall`, this session, run against the file
in place (not copied/modified). Breakdown by `restrictBy` prefix: **20** are `"1:1000"` (record-count mode,
1000-record cap) and **3** are `"0:0"` (unlimited); **zero** are `"2:*"` (storage-size mode) [CERT] same
script, `Counter` over the parsed `restrictBy` prefixes. A separate pass for `<p n="fullPolicy" …
t="h:FullPolicy" … v="…">` finds 3 explicit entries, all `"roll"` [CERT] same method. **PANCCADIA's
histories do not use storage-size capacity** — the §26.6 hazard, real in the abstract, measures to **zero**
exposure for this specific station's current config, extending [Block 20] §20.5's "zero in our own module
source" finding to the station's actual persisted history configuration as well.

## 26.9 — Verdict

**CONFIRMED, but narrower and less severe than [Block 20]'s framing, and unmitigated by tooling.**

| Sub-claim | Verdict | Scope |
|---|---|---|
| N5 server-side `BCapacity` storage-size removal is real and clean | **CONFIRMED** [CERT] | §26.2, independently re-derived (source + bytecode) |
| `decode`/`decodeFromString` perform no validation, either version | **CONFIRMED** [CERT] | §26.3 |
| On-disk rollover mechanism changed between N4 and N5 | **REFUTED** [CERT] | §26.4 — byte-identical control flow in all 3 backends; only `getMaxRecords()`'s guard clause changed |
| Storage-size mode was ever operator-constructible via a UI (N4 or N5, Workbench or web) | **REFUTED** [CERT] | §26.5 — both dropdowns, both eras, only ever offered 2 items |
| A genuinely N5-exclusive, live-exposure path exists | **CONFIRMED, narrow** `[INFER]` | §26.6 — only a fixed-length (Boolean/Enum/Numeric) history with a legacy-origin `restrictBy=2` capacity that was never activated under N4 |
| Migrator SPI (`migrator.jar`/`propMigration.jar`) mitigates the hazard | **REFUTED** [CERT] | §26.7 — zero converters/descriptors touch `BCapacity` or history config |
| The `Capacity.js`/`CapacityEditor.js` "contradiction" is a live N4-vs-N5 runtime disagreement | **REFUTED** [CERT] | §26.5 — the UI-layer mislabel-then-launder behaviour is pre-existing (N4), not new |
| PANCCADIA is exposed today | **REFUTED** [CERT] | §26.8 — 0 of 23 capacities are storage-size mode |

## 26.10 — Self-verify

**Token check.** Every load-bearing `[CERT]` citation above was `grep`/`javap`/direct-Read confirmed against
its cited source in this session — 100% fresh, none reused from [Block 20]/[Block 14] without independent
re-derivation (the two cross-session hash agreements — `history.jar` line-number match on
`storageSize=Storage Size`, `migrator.jar` sha256 match with [Block 14] — are noted as confirmatory, not relied
on in place of a fresh read).

**Marker tally — literal `verify-block.sh` output** (run read-only against the block file; the script only
writes to stdout, so this does not violate the task's single-file-write constraint):

```
== verify-block: niagara5-block26.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1
   [CERT-live] 0
   [CERT] 73  (adj 70)
   [CERT-doc] 0
   [CERT-web] 1
   [CERT-a] 0
   [INFER] 9  (adj 8)
-- ratio -- [INFER]/[CERT*] = 8/72 = 0.11
-- [CERT] file:line citation resolution --
   resolved 0 of 11
   WARN    resolved 0 of 11 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

(The `[CERT-hw]`/`[CERT-web]` counts of 1 each are the legend-line hits inside this block's own header
blockquote, which quotes the full marker list per the template — not live claims of that type; this block
makes no `[CERT-hw]`/`[CERT-web]` claims, only `[CERT]`/`[INFER]`, consistent with its header's Type/Method
statement.) Ratio 0.11 — low, consistent with a `mixed` (mostly fresh-evidence) block whose one synthesis
section (§26.6) draws on `[CERT]` facts assembled earlier in the SAME block, not across prior blocks, which is
why it is declared `mixed` rather than a pure `synthesis` type. **`resolved 0 of 11` is the EXPECTED signature
for this block, per METHODOLOGY §11's "DECOMPILED-TREE BLOCKS WILL SHOW ZERO RESOLVED CITATIONS" convention**:
every sampled citation is either a session-scratch decompile path (`/tmp/claude-1000/n5b26/...`, not part of
any corpus) or a path in the **sibling** `niagara-research` corpus (out of `verify-block.sh`'s target scope
when run against `niagara5-research`) — both classes resolve `extern` by construction, confirmed by the tool's
own per-line listing (all 11 sampled citations show `extern … not script-verifiable`). Citation gate for this
block is therefore **inline token-verify, not the mechanized resolver**: every `[CERT]` `file:line` cited in
§26.2–§26.8 was independently confirmed this session by direct `grep`/`javap`/Read against its source, as
documented inline at each citation (the "Token check" paragraph above).

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block26.md` (this write).
Per the explicit read-only/single-file task constraint, `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` were
**not** regenerated or hand-edited — left to the orchestrator/next iteration, flagged here so it is not
silently skipped.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.

**De-escalations recorded (METHODOLOGY §11).** Two findings from [Block 20] are narrowed/corrected here, not
merely extended: (1) the "wildly oversized or undersized" hazard framing is narrowed to the specific
never-activated-under-N4 scenario (§26.6); (2) the `Capacity.js` "unresolved contradiction, no live station to
probe" framing is resolved statically — not by probing a live station, but by showing the actual widget code
on both sides never exposes the contradiction to begin with (§26.5). Neither is a retraction of a `[CERT]`
fact; both are scope narrowings of an `[INFER]`/open-question framing, recorded per the de-escalation
convention.

## 26.11 — Child gaps

- **B26-G1** — Live-station dynamic confirmation (the remaining half of B20-G1/B20-G4): on a real N5 5.0.0.28
  station, construct the narrow §26.6 scenario directly — restore/import a `.bog` fragment carrying a
  Boolean/Enum/Numeric history extension with a `capacity` property manually set to `"2:<N>"` via a raw
  property-sheet string edit (bypassing both `BCapacityFE` and `CapacityEditor.js`, per §26.5's finding that
  neither widget can construct this value), enable it, and observe the created file's actual `PageManager`
  capacity — turns §26.6's `[INFER]` into `[CERT-hw]`. Still blocked: no live N5 station reachable this
  corpus (static/read-only per `RESEARCH-STATE.md`).
- **B26-G2** — Whether a raw property-sheet edit (Workbench "Edit as string" or the web property-sheet's
  generic value field) can actually submit an arbitrary `b:Capacity` encoded string bypassing
  `BCapacityFE`/`CapacityEditor.js` entirely — assumed possible in §26.11/B26-G1 but not confirmed; if the
  generic string editor also validates against the same 2-option enum, the "legacy-origin" scenario in §26.6
  would need to originate from an even older Niagara generation's `.bog`, not from any N4-era action at all.
- **B26-G3** — `BHistoryDbTable`'s concrete subclasses (archive/SQL-backed history storage) were read only at
  the shared capacity-check call site (§26.4c); whether any subclass has an alternate, byte-size-aware
  enforcement path this block did not find was not exhaustively ruled out.
- **B26-G4** — Whether `n5mig`'s generic `BTypeSpecConverter`/property-copy path (§26.7's architectural note)
  ever exercises validation on ANY `BSimple`-typed property value during migration (as opposed to component
  typespecs) — this block established BCapacity specifically has no registered handler, but did not open
  `BTypeSpecConverter`'s generic property-copy code path to confirm it truly passes ALL simple values through
  byte-for-byte unexamined, vs. some other unrelated simple-type validation existing that happens not to cover
  Capacity.

## 26.x — Connections

- **[Block 20]** — raised B20-G1 (client-layer contradiction) and B20-G4 (rollover mechanism not opened) from
  its §20.5; this block closes B20-G4 fully (§26.4) and B20-G1's static half (§26.5), and narrows/corrects
  §20.5's hazard framing (§26.6, §26.10's de-escalation note) rather than simply reconfirming it.
- **[Block 14]** — established the migrator SPI's two-registry architecture and the 58-type `migrator.jar`
  catalog census this block cross-checks directly (§26.7) for history-specific coverage; also established the
  "module registers its own propMigration descriptors in its own manifest" pattern this block used to check
  `history.jar`'s own `module.xml` for propMigration entries (found none).
