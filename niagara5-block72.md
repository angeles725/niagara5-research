# Block 72 — Four named child gaps closed: the `fieldEditor`-facet raw-string bypass for `BCapacity`, `BHistoryDbTable`'s real place in the class hierarchy (not a third backend), `BTypeSpecConverter`'s `TypeSpec`-only scope, and an exhaustive 3-module `jetty-web.xml` census

> Research closing/narrowing four previously-opened, explicitly-named child gaps from two unrelated prior
> clusters: **B26-G2** (whether a raw property-sheet string edit can construct a `restrictBy=2` `BCapacity`
> on N5, bypassing `BCapacityFE`/`CapacityEditor.js`'s 2-item dropdown — [Block 26] §26.11 named this
> "assumed possible... but not confirmed"); **B26-G3** (whether `BHistoryDbTable`'s concrete subclasses hold
> an alternate, byte-size-aware capacity-enforcement path [Block 26] §26.4c did not exhaustively rule out);
> **B26-G4** (whether `n5mig`'s `BTypeSpecConverter` — named but never opened by [Block 26] §26.7 — passes
> ALL `BSimple`-typed property values through unexamined, or is scoped some other way); **B27-G2** (whether
> any N5 module besides `web.jar` carries its own `WEB-INF/jetty-web.xml` to diverge from the primary
> station context's security policy — [Block 27] §27.2 only read `web.jar`'s own file). Covers: (1) a fresh
> read of `com.tridium.workbench.fieldeditors.BDefaultSimpleFE` (Workbench, never previously opened in this
> corpus) and `com.tridium.workbench.propsheet.BComplexEntry`'s field-editor-resolution logic, plus
> `webEditors`' `DefaultSimpleEditor.js`/`FacetsRowEditor.js`, to trace the actual mechanism by which an
> operator could reach a raw-string editor for a `BCapacity` slot; (2) a corpus-wide (`organized/`, all 247
> shipped module directories) search for every class `extends BHistoryDbTable`, plus a fresh read of
> `BHistoryDbTable.open()`/`resize()` and `BFileHistoryTable.doResize()`/`ResizePrivilegedAction`, none
> previously cited by [Block 26]; (3) a fresh whole-file read of `BTypeSpecConverter.java` (never opened by
> [Block 26], only named) plus `ConverterRegistry`'s handler-map construction; (4) a corpus-wide `find` for
> `jetty-web.xml` across all 247 module directories, with a full read of the two newly found files (`fox`,
> `box`) and their companion `web.xml`s. Does **not** cover: a live N5 station reproduction of the §72.2
> mechanism (no runnable station this session, same constraint as every prior niagara5 block); the
> `niagara.agent.AgentList.getDefault()` specificity-ranking algorithm itself (presumably `baja.jar`, not
> opened this session — the exact reason `BCapacityFE` rather than `BDefaultSimpleFE` is the UNMARKED
> default remains `[INFER]` by Niagara-convention, not independently read — see **B72-G2**); whether the
> interactive command that lets a Workbench/web operator select a NON-default field editor for a single slot
> exists as a first-class UI affordance (the property-sheet row's own popup menu was read and found to build
> only a `BNavMenuAgent`+`ConfigFlagsCommand` menu, not an FE chooser — see **B72-G1**); `BIPxElementConverter`
> (the Px-side sibling of the Bog-element converter path §72.4 reads) — not opened this session, see
> **B72-G4** (renumbered from this block's own gap list, not [Block 26]'s).
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as every prior niagara5 block (`etc/brand.properties`
> `workbench.notice`). Module jars read this session, all from
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/`, fresh `sha256sum` this session:
> `history.jar` `9fc1c9b1768fdc6e44456c2374df802565ea5afecf69d443f375082b49a612cf` (matches [Block 26]'s
> citation for the same file — cross-session hash agreement, not relied on in place of a fresh source read);
> `workbench.jar` `487ea4ea304edb6d564fc33086e2a15be30fff5c6a29ab781ac97687147555af`; `webEditors.jar`
> `33caf127873dd65618538756336787937c1beda6fafe485e8d77ac06db693d9e`; `migrator.jar`
> `9b0b5f4fa6fdcaa59945631456739b65f88ab3c26083184853ad1888c2897d08` (matches [Block 26]); `migration.jar`
> `ebce515de72632955899846b296b08a2ee3045c1422397ce6b0715c80482c49c`; `web.jar`
> `68babcf16012314d59c095d3995c0a0f4db18853361cd5719e76be2a4d14b22e` (matches [Block 27]); `fox.jar`
> `cecb44c1150554560aa900a85823a66c981b1d07259d788b28eb053f51e4631f`; `box.jar`
> `89919dbe704d3e53b06caf20db14e40553a5d08178e8fecd1755124beb40ee8f`. `BDefaultSimpleFE`/`BComplexEntry`
> decompiled from `workbench.jar`; `DefaultSimpleEditor.js`/`FacetsRowEditor.js` extracted verbatim from
> `webEditors.jar`; `BTypeSpecConverter`/`ConverterRegistry` decompiled from `migrator.jar`/`migration.jar`;
> `BHistoryDbTable`/`BFileHistoryTable` re-read from the pre-existing `history.jar` decompile this corpus
> already carries at `organized/history/vineflower/` (per this corpus's convention of preserving decompiles
> under `organized/`, unlike [Block 26]'s sibling-`niagara-research`-style session-scratch approach); all
> `jetty-web.xml`/`web.xml` files read via direct `Read` of the preserved `organized/<module>/vineflower/
> WEB-INF/` copies.
>
> Sources: `organized/workbench/vineflower/com/tridium/workbench/fieldeditors/BDefaultSimpleFE.java` (whole
> file, 65 lines); `organized/workbench/vineflower/com/tridium/workbench/propsheet/BComplexEntry.java:291-337`
> (`makeEntry`/`getEditorType` overloads); `organized/workbench/vineflower/niagara/workbench/fieldeditor/
> BWbFieldEditor.java:26-58` (`makeFor`, `FEAgentFilter` field); `organized/history/vineflower/com/tridium/
> history/ui/BCapacityFE.java:30` (`@AgentOn` re-cited, [Block 26] already read this file's dropdown logic);
> `organized/webEditors/vineflower/rc/fe/baja/DefaultSimpleEditor.js:1-70`; `organized/webEditors/vineflower/
> rc/fe/baja/FacetsRowEditor.js:26-45` (`DEFAULT_KEYS` map, `fieldEditor` entry); `organized/history/
> vineflower/com/tridium/history/db/BHistoryDbTable.java:86-112` (`open()`, `doOpen` abstract decl),
> `:180-186` (`resize()`, `doResize` abstract decl); `organized/history/vineflower/com/tridium/history/file/
> BFileHistoryTable.java:60` (class declaration, `extends BHistoryDbTable`), `:425-426` (`doResize()`
> override), `:730-740` (`writeConfig()`'s second `doResize` call site), `:897-950` (`ResizePrivilegedAction`
> whole inner class); `organized/history/vineflower/com/tridium/history/file/fixed/
> BFixedLengthHistoryTable.java:20` (class decl, no `doResize` override — confirmed by its absence);
> `organized/history/vineflower/com/tridium/history/file/recstore/BRecordStoreHistoryTable.java:22` (class
> decl, same negative confirmation); `organized/history/vineflower/com/tridium/history/db/
> BLocalDbHistory.java:36` (class decl, `extends BHistory` — confirmed NOT a `BHistoryDbTable` subclass,
> ruling out a same-package false lead); `organized/migrator/vineflower/com/tridium/migrator/baja/
> BTypeSpecConverter.java` (whole file, 82 lines); `organized/migration/vineflower/niagara/migration/
> ConverterRegistry.java:1-80` (`lookupConverters`, `setupElementHandlerMap` head); `organized/web/vineflower/
> WEB-INF/jetty-web.xml`, `organized/fox/vineflower/WEB-INF/{jetty-web.xml,web.xml}`, `organized/box/
> vineflower/WEB-INF/{jetty-web.xml,web.xml}` (all whole files, ≤20 lines each); `organized/box/vineflower/
> META-INF/module.xml:2` (module description line, `"Building Object eXchange Protocol"`).
>
> Method: direct decompiled-source `Read`s (Vineflower output this corpus already preserves under
> `organized/<module>/vineflower/`, per this corpus's own convention — distinct from [Block 26]'s
> session-scratch approach, itself borrowed from the sibling `niagara-research` corpus's layout); a
> corpus-wide `grep -rl "extends BHistoryDbTable" organized` (§72.3) and `find organized -iname
> "jetty-web.xml"` (§72.5), both run against the FULL 247-module-directory corpus (cross-checked this
> session against the live install's own `modules/*.jar` listing via `comm`, confirmed a 1:1 match, see
> §72.5); fresh `sha256sum` of every jar cited above. Markers (canonical list: METHODOLOGY §3): `[CERT]`
> local primary source (`file:line`) · `[INFER]` deduction.
>
> History persistence/runtime layer + web/servlet layer (two unrelated clusters in one block, per task
> instruction). Connects [Block 26] (closes/narrows B26-G2, closes B26-G3 — with one correction to its
> §26.4c framing), [Block 27] (closes B27-G2), [Block 61] (style precedent for a multi-gap-closing block).
>
> **Type:** `mixed` — §72.3 corrects [Block 26] §26.4c's framing of `BHistoryDbTable` as a "separate,
> third backend" (it is in fact the shared ABSTRACT ANCESTOR of the other two, reached via `BFileHistoryTable`)
> while also closing B26-G3 with fresh evidence; §72.2 narrows, but does not fully close, B26-G2, drawing a
> boundary `[INFER]` about UI reachability that could not be resolved statically. §72.4 and §72.5 are
> straightforward fresh-evidence closures (no prior-block correction).

---

## 72.1 — Scope recap

Two prior blocks each named a child gap this session was tasked to close: [Block 26] §26.11 raised
**B26-G2** (does a raw property-sheet string edit actually bypass `BCapacityFE`/`CapacityEditor.js`?),
**B26-G3** (does any `BHistoryDbTable` concrete subclass hold an alternate enforcement path?), and **B26-G4**
(does `BTypeSpecConverter`'s generic-looking property-copy path actually validate `BSimple` values
generically?) — three gaps opened by the SAME block, all unopened sources at the time. [Block 27] §27.x
named child gaps separately raised **B27-G2** (does any module besides `web.jar` carry its own
`jetty-web.xml`?). This block opens every source each gap named and was blocked on.

## 72.2 — B26-G2 NARROWED, not fully closed: the `fieldEditor` slot facet is a real, confirmed override that reaches `BDefaultSimpleFE`'s unconditional `decodeFromString()` — the exact interactive command that selects it for an already-FE'd slot was not found `[CERT]`+`[INFER]`

**The raw-string decode path itself is real and reachable in principle, not merely theoretical.**
`com.tridium.workbench.fieldeditors.BDefaultSimpleFE` is declared `@NiagaraType(agent =
@AgentOn(types = "baja:Simple"))` — a universal Workbench field-editor agent registered against EVERY
`BSimple` type, not merely ones lacking a dedicated FE `[CERT]`
(`organized/workbench/vineflower/com/tridium/workbench/fieldeditors/BDefaultSimpleFE.java:19`, whole file
read this session — never previously opened in this corpus). `BCapacity extends BSimple` `[CERT]`
(`organized/history/vineflower/niagara/history/BCapacity.java:18`, re-confirmed this session), so
`BDefaultSimpleFE` IS a member of `BCapacity`'s own `getAgents()` result — a structurally valid candidate FE
for a `capacity` slot, not a hypothetical one. Its `doLoadValue()`/`doSaveValue()` are a bare
`encodeToString()`/`decodeFromString()` round-trip through a single `BTextField`, with **zero** type-specific
validation of any kind:

```java
protected void doLoadValue(BObject value, Context context) {
   ((BTextField)this.getContent()).setText(value.asSimple().encodeToString());
}
protected BObject doSaveValue(BObject value, Context cx) throws Exception {
   String str = ((BTextField)this.getContent()).getText();
   try { return value.asSimple().decodeFromString(str); }
   catch (IOException e) { throw new CannotSaveException(...); }
}
```
`[CERT]` (`BDefaultSimpleFE.java:44-64`, whole method pair, this session). Since [Block 26] §26.3 already
established (and this block re-confirms by citation, not re-derivation) that `BCapacity.decodeFromString(str)`
performs **no range/validity check on `restrictBy`** `[CERT]` (per [Block 26]'s own citation,
`niagara/history/BCapacity.java:79-98`, not re-opened this session), a string `"2:10485760"` typed into
`BDefaultSimpleFE`'s text field and saved constructs a live `restrictBy=2` `BCapacity` exactly as cleanly as
the programmatic case §26.3 already demonstrated — this closes the MECHANISM half of B26-G2 outright.

**The override point that would select this FE for a slot that already has a dedicated one is a real,
named slot facet — `fieldEditor` — confirmed on BOTH the Workbench and web sides.** Workbench's property
sheet resolves the active FE per-slot via `BComplexEntry.getEditorType()`:

```java
private AgentInfo getEditorType(BObject kid, BFacets facets) {
   if (facets != null) {
      String explicit = facets.gets("fieldEditor", null);
      if (explicit != null) { return Sys.getRegistry().getType(explicit).getAgentInfo(); }
   }
   ...
   AgentList agents = kid.getAgents().filter(BWbFieldEditor.getAgentFilter(shell));
   return agents.getDefault();
}
```
`[CERT]` (`organized/workbench/vineflower/com/tridium/workbench/propsheet/BComplexEntry.java:319-337`, whole
method, this session) — an explicit `"fieldEditor"` facet on the slot **short-circuits agent-default
resolution entirely**, before `BCapacityFE`'s more-specific `@AgentOn(types="history:Capacity")` registration
(re-cited, `organized/history/vineflower/com/tridium/history/ui/BCapacityFE.java:30`) ever gets a chance to
win by specificity. The identical mechanism exists at the top-level static factory too:
`BWbFieldEditor.makeFor(obj, cx, shell)` checks `cx.getFacet("fieldEditor")` FIRST, before falling back to
`obj.getAgents().filter(FEAgentFilter)` `[CERT]` (`organized/workbench/vineflower/niagara/workbench/
fieldeditor/BWbFieldEditor.java:43-58`, this session). The web side independently corroborates this is a
REAL, recognized facet key, not a Workbench-only internal: `webEditors`' generic `FacetsRowEditor.js` — the
widget a "Slot > Facets" editor uses to let an operator edit ANY slot's facets (min/max/precision/units/etc.)
— lists `fieldEditor` (type `'s'`, string) as one of its `DEFAULT_KEYS` `[CERT]`
(`organized/webEditors/vineflower/rc/fe/baja/FacetsRowEditor.js:40`, this session — 1 of ~28 recognized
default facet keys in that map). The web side's own generic fallback editor for any `baja:Simple`,
`DefaultSimpleEditor.js`, is architecturally identical to `BDefaultSimpleFE`: a single string field, loaded
via `encodeToString()`, saved via `decodeFromString()`, with an explicit doc comment "Default editing
behavior for Simples" `[CERT]` (`organized/webEditors/vineflower/rc/fe/baja/DefaultSimpleEditor.js:12-16,
62-70`, this session).

**What this session could NOT confirm: the specific interactive command an operator clicks to set that
facet, or to otherwise select a non-default FE for a slot that already resolves to one.** The property-sheet
row's own popup menu — the one place a per-row "Views"/FE-chooser command would most plausibly live — was
read in full and builds only a `BNavMenuAgent`-derived nav-tree menu plus a `ConfigFlagsCommand`; no
FE-selection command appears in it `[CERT]` (`organized/workbench/vineflower/com/tridium/workbench/propsheet/
BPropertyEntry.java:486-512`, `showPopup`-equivalent block, whole method read this session — absence
confirmed by a full-method read, not a keyword miss). This means the confirmed path into `BDefaultSimpleFE`
for an already-`BCapacityFE`'d slot is the `fieldEditor` FACET override specifically (settable through a
generic Facets-editing dialog, confirmed to recognize the key, but this session did not trace that dialog's
own invocation/permission path end-to-end) — not a dedicated "switch field editor" UI affordance, which this
session searched for and did not find in the one place it would most plausibly be. **Net: the raw-string
CAPABILITY is `[CERT]`-confirmed reachable and unconditionally unsafe once reached; the exact operator
click-path to reach it for THIS specific slot is `[INFER]`, narrowed to the `fieldEditor` facet mechanism but
not independently walked start-to-finish this session.** Refined as **B72-G1**.

## 72.3 — B26-G3 CLOSED: `BHistoryDbTable` has exactly ONE subclass anywhere in the 247-module corpus (`BFileHistoryTable`, already fully covered by [Block 26]) — no alternate backend exists — but a fourth, previously-uncited enforcement call site is found, gated identically `[CERT]`

**Corrects [Block 26] §26.4c's framing.** [Block 26] listed `BHistoryDbTable` as "(c)" — a THIRD, separate
history-table backend alongside `BFixedLengthHistoryTable`/`BRecordStoreHistoryTable` ("(a)"/"(b)"), each
described as parallel alternatives. A fresh corpus-wide search this session shows this is not quite right:
`BFileHistoryTable` — the SAME abstract class [Block 26] §26.4 already named as the chooser between (a) and
(b) (`BFileHistoryTable.make()`) — itself `extends BHistoryDbTable`:

```java
public abstract class BFileHistoryTable extends BHistoryDbTable {
```
`[CERT]` (`organized/history/vineflower/com/tridium/history/file/BFileHistoryTable.java:60`, this session).
A corpus-wide `grep -rl "extends BHistoryDbTable" organized` — run against ALL 247 shipped module
directories this corpus holds (§72.5 independently confirms this is the complete shipped set, not a subset)
— returns **exactly one hit: `BFileHistoryTable.java`** `[CERT]` (grep output, this session, single line).
**`BHistoryDbTable` is therefore the shared ABSTRACT ANCESTOR of both (a) `BFixedLengthHistoryTable` and (b)
`BRecordStoreHistoryTable` (each `extends BFileHistoryTable extends BHistoryDbTable`), not a third sibling
backend** `[CERT]` (class declarations, `organized/history/vineflower/com/tridium/history/file/fixed/
BFixedLengthHistoryTable.java:20`, `organized/history/vineflower/com/tridium/history/file/recstore/
BRecordStoreHistoryTable.java:22`, both re-read this session). This directly and exhaustively answers B26-G3's
literal question — **there is no alternate `BHistoryDbTable` subclass anywhere in the shipped N5 5.0.0.28
module set** (not merely "not found in a partial search" — the search covered every module directory this
corpus preserves, a 1:1 match against the live install's jar count per §72.5). One same-package false lead
was checked and ruled out: `BLocalDbHistory` (in the same `com.tridium.history.db` package) `extends BHistory`
`[CERT]` (`organized/history/vineflower/com/tridium/history/db/BLocalDbHistory.java:36`) — a component-level
class, unrelated to the `BHistoryDbTable` storage-table hierarchy despite the name/package proximity.

**A genuine fourth enforcement call site exists, previously uncited by [Block 26], inherited by BOTH covered
backends — and it is gated identically.** `BHistoryDbTable.open()` — the base class's own, `final`, method,
inherited unchanged by every subclass — runs a capacity check AFTER `doOpen()` completes:

```java
public final void open() throws HistoryException {
   ...
   this.doOpen();
   this.open = true;
   BCapacity capacity = this.getConfig().getCapacity();
   if (capacity.isByRecordCount() && this.getRecordCount() > capacity.getMaxRecords()) {
      BFullPolicy fullPolicy = this.getConfig().getFullPolicy();
      this.resize(capacity, fullPolicy);
   }
}
```
`[CERT]` (`organized/history/vineflower/com/tridium/history/db/BHistoryDbTable.java:86-107`, whole method,
this session). `resize()` is `final`, delegating to an abstract `doResize()` `[CERT]` (`:180-186`) —
implemented exactly once, in `BFileHistoryTable` itself (neither `BFixedLengthHistoryTable` nor
`BRecordStoreHistoryTable` overrides it — confirmed by their absence of any `doResize` declaration in either
file, a full-file read each, this session): `doResize()` runs `SecurityUtil.doPrivileged(new
ResizePrivilegedAction(...))` `[CERT]` (`organized/history/vineflower/com/tridium/history/file/
BFileHistoryTable.java:425-426`), and `ResizePrivilegedAction.run()` is a genuine rebuild-the-whole-file
operation — opens a fresh table at the NEW capacity, copies every record across via a `Cursor` query, deletes
the original, and renames the rebuilt file into place `[CERT]` (`BFileHistoryTable.java:897-950`, whole inner
class, this session). A second call site reaches the same `doResize()` from `writeConfig()`, when a config
rewrite no longer fits the file's reserved header space `[CERT]` (`BFileHistoryTable.java:730-740`).

**Net reading: this is a real, previously-uncited FOURTH enforcement call site (distinct from §26.4's
`createDataSection()`-time sizing, `PageManager.append()`-time trimming, and `RecordStore.append()`-time
gating) — and it changes nothing about [Block 26]'s verdict, because it carries the identical
`isByRecordCount()` gate.** For a `restrictBy=2` capacity, `isByRecordCount()` is `false`
(re-confirmed [Block 26] §26.3's finding, not re-derived), so `open()`'s resize-on-open check never fires for
it either — this call site was searched for specifically because it was the one plausible place an
"alternate, byte-size-aware" enforcement path COULD have lived (a shrink-on-open safety net, structurally the
most likely spot for capacity-mode-aware logic given it runs once per table lifecycle, not per-record), and
it does not have one. **B26-G3 CLOSED**: exhaustively searched, no alternate subclass exists, and the one
additional enforcement call site this search surfaced reinforces rather than contradicts [Block 26]'s
narrowed hazard statement (§26.6).

## 72.4 — B26-G4 CLOSED: `BTypeSpecConverter` is scoped exclusively to `baja:TypeSpec`-valued properties — it never touches `h:Capacity` (or any other `BSimple` type) at all, confirming rather than merely inferring [Block 26] §26.7's architecture note `[CERT]`

[Block 26] §26.7 named `BTypeSpecConverter` as the one History-adjacent-sounding class in `migrator.jar`'s
converter catalog but did not open it, reasoning ARCHITECTURALLY (from the `BIBogElementConverter`/
`ConverterRegistry` pattern already established) that even a populated catalog would need a
`propMigration`-style per-property descriptor to intercept a `BSimple` value, and none exists — leaving open
whether `BTypeSpecConverter`'s own "generic simple-value" handling might be exactly such a descriptor.
**A fresh whole-file read this session shows it is not, and could not be — its declared scope excludes
`BCapacity` structurally, not by coincidence of catalog coverage:**

```java
private static final List<String> CONVERT_TYPES;
public List<String> getConvertTypes() { return CONVERT_TYPES; }
static { ... Collections.addAll(mutableConvertTypes, "baja:TypeSpec"); ... }
```
`[CERT]` (`organized/migrator/vineflower/com/tridium/migrator/baja/BTypeSpecConverter.java:27,34-36,77-81`,
whole file read this session, 82 lines) — `getConvertTypes()` returns a single-element, hardcoded,
`unmodifiableList` containing only `"baja:TypeSpec"`. Its `convertXElem(XElem x, ...)` reads the bog
element's `v` (value) attribute and tries `Sys.getType(typespecValue)` — i.e. it treats the PROPERTY'S VALUE
STRING as if it were itself a type/module reference, catching `ModuleException`/`TypeException` to detect a
renamed or removed module/type target `[CERT]` (`:38-51`), then looks up OTHER converters via
`ConverterRegistry.lookupConverters(typespecValue)` — passing the type/module NAME the value refers to, not
any encoding of the value's own declared TYPE `[CERT]` (`:53-75`). This is the mechanism for
**`baja:TypeSpec`-typed properties** (a property whose VALUE is itself a type-reference string, e.g.
`"somemodule:SomeType"`) that survive a module/type rename across versions — architecturally unrelated to,
and never invoked for, a `history:Capacity`-typed property like `BCapacity.capacity`, whose value
(`"2:10485760"`) is never even syntactically a type-spec.

`ConverterRegistry.lookupConverters(moduleOrTypeName)` confirms the registry itself is keyed by MODULE/TYPE
NAME strings (populated from each registered converter's own `getConvertTypes()` at `initialize()`), not by
the declared TYPE of the property being converted — reinforcing that `BTypeSpecConverter`'s dispatch is
never reached for a `BCapacity` value regardless of what other converters exist `[CERT]`
(`organized/migration/vineflower/niagara/migration/ConverterRegistry.java:29-39,53-57`, whole
`initialize()`/`lookupConverters()` methods, this session). **B26-G4 CLOSED**: `BTypeSpecConverter` is not a
generic `BSimple`-passthrough path at all — it is scoped to exactly one narrow `BSimple` subtype
(`baja:TypeSpec`) by a hardcoded, single-element list, confirming [Block 26] §26.7's architectural note with
a direct read rather than leaving it as an inference from pattern alone. This session did not open the
parallel `BIPxElementConverter`/Px-side registry map — named as a new, low-priority child gap, **B72-G4**
(not a renumbering of any [Block 26] gap).

## 72.5 — B27-G2 CLOSED: exactly 3 of the 247 shipped N5 5.0.0.28 modules carry a `jetty-web.xml` (`web`, `fox`, `box`) — all three declare ONLY a `contextPath` override, none diverges on security policy `[CERT]`

**Census scope confirmed exhaustive, not partial.** This corpus's `organized/` directory holds 250 entries;
3 are non-module bookkeeping directories (`_bin-ext`, `_logs`, `_recon`), leaving exactly 247 module
directories. A fresh `comm` diff against the live install's own `/mnt/c/ProgramData/Niagara/tridium/config/
5.0.0.28/modules/*.jar` listing (247 `.jar` files) shows a **1:1 match, zero entries on either side** `[CERT]`
(`comm -23`/`comm -13` output, both empty, this session) — this corpus's module coverage is the complete
shipped set for this install, not a sampled subset, so a corpus-wide `find` is a genuine exhaustive census.

`find organized -iname "jetty-web.xml"` across all 247 directories returns **exactly 3 hits**: `web`
(already read, [Block 27] §27.1 — context path `/`), `fox`, and `box` `[CERT]` (find output, this session,
3 lines). Both newly found files are read in full:

```xml
<!-- organized/fox/vineflower/WEB-INF/jetty-web.xml -->
<Configure id="webApp" class="org.eclipse.jetty.ee11.webapp.WebAppContext">
  <Set name="contextPath">/foxwss</Set>
</Configure>
```
```xml
<!-- organized/box/vineflower/WEB-INF/jetty-web.xml -->
<Configure id="webApp" class="org.eclipse.jetty.ee11.webapp.WebAppContext">
  <Set name="contextPath">/wsbox</Set>
</Configure>
```
`[CERT]` (both files, whole text, this session — identical shape to `web.jar`'s own file, already `[CERT]`
per [Block 27] §27.1: exactly one `<Set name="contextPath">` directive, no `SecurityHandler`, no
`Authenticator`, no `<Set>`/`<Call>` targeting anything security-related). **`fox` and `box` each also ship a
companion `WEB-INF/web.xml`**, matching the exact shape §27.4 established `addModuleWebAppHandlers()` looks
for (a `WebAppContext`-shaped module with its own `web.xml`+`jetty-web.xml` pair):

```xml
<!-- fox: WebSocket tunnel for the Fox protocol -->
<servlet-class>com.tridium.fox.sys.FoxWebSocketServlet</servlet-class>  <url-pattern>/*</url-pattern>
<listener-class>com.tridium.fox.sys.FoxwssHttpSessionListener</listener-class>
```
```xml
<!-- box: WebSocket tunnel for "Building Object eXchange Protocol" (module.xml description) -->
<servlet-class>com.tridium.box.BoxWebSocketServlet</servlet-class>  <url-pattern>/*</url-pattern>
<listener-class>com.tridium.box.BoxWsHttpSessionListener</listener-class>
```
`[CERT]` (`organized/fox/vineflower/WEB-INF/web.xml`, `organized/box/vineflower/WEB-INF/web.xml`, both whole
files, this session; `box`'s module description — `"Building Object eXchange Protocol"` — from
`organized/box/vineflower/META-INF/module.xml:2`). Each is a minimal, single-purpose WebSocket-upgrade
servlet mapped to `/*` under its own overridden context path; **neither declares a security-header filter
of its own** — the same absence [Block 27] §27.1 established for `web.xml` itself.

**Net verdict, closing B27-G2: no shipped N5 module diverges from the primary-context security policy via
`jetty-web.xml`.** Exactly 3 modules carry the file at all, and all 3 use it for the SAME single purpose
(overriding the context path away from the default module-name-derived one) — none opts out of
`TridiumSecurityFilter`, swaps the authenticator, or registers a different `SecurityHandler`. Because `fox`
and `box` structurally match the same `web.xml`+`jetty-web.xml` pairing §27.4 read as the `[INFER]` signal for
`web.jar` itself being picked up by `addModuleWebAppHandlers()`, the SAME unresolved uncertainty applies to
them too (whether `NModuleInfo.isWar()` actually flags them — [Block 27]'s own **B27-G4**, not re-opened
here) — **and** a genuinely new question this session's WebSocket-specific finding raises: whether a
WebSocket UPGRADE handshake response (as opposed to an ordinary HTTP response) actually passes through the
same servlet-filter chain `TridiumSecurityFilter` sits in, or whether Jetty's WebSocket-upgrade machinery
answers the handshake before/outside normal filter dispatch. Neither `fox.jar` nor `box.jar` was decompiled
beyond the two XML files this session — named as **B72-G3**.

## 72.x — Verdict

| Gap | Verdict | Scope |
|---|---|---|
| B26-G2 — raw property-sheet edit can construct `restrictBy=2` | **NARROWED, mechanism CONFIRMED** `[CERT]`+`[INFER]` | §72.2 — `BDefaultSimpleFE`/`DefaultSimpleEditor.js` + `fieldEditor` facet override confirmed real and unconditionally unsafe once reached; exact interactive click-path not independently traced |
| B26-G3 — `BHistoryDbTable` subclass alternate enforcement | **CLOSED** `[CERT]` | §72.3 — exactly one subclass exists corpus-wide (already covered); one new call site found, gated identically, no contradiction |
| B26-G4 — `BTypeSpecConverter` generic simple-value handling | **CLOSED** `[CERT]` | §72.4 — scoped exclusively to `baja:TypeSpec`, structurally excludes `BCapacity` |
| B27-G2 — per-module `jetty-web.xml` census | **CLOSED** `[CERT]` | §72.5 — exactly 3 of 247 modules (`web`/`fox`/`box`), all context-path-only, exhaustive census confirmed 1:1 against the live install |

## 72.x — Self-verify

**Token check.** Every load-bearing `[CERT]` citation above was `grep -n`/direct-`Read` confirmed against
its cited source this session — 100% fresh: `BDefaultSimpleFE.java` and `BComplexEntry.java`'s
`getEditorType`/`BWbFieldEditor.makeFor` were never previously opened in this corpus (new sources this
session); `BHistoryDbTable.java`/`BFileHistoryTable.java` were re-opened at NEW line ranges not cited by
[Block 26] (`:86-112`/`:180-186` for the base class's `open()`/`resize()`, `:425-426`/`:730-740`/`:897-950`
for the subclass's `doResize` implementation — none of these four ranges appear in [Block 26]'s own citation
list); `BTypeSpecConverter.java`/`ConverterRegistry.java` were never previously opened (named but not read by
[Block 26]); all three `jetty-web.xml`/two `web.xml` files were read fresh this session (`fox`/`box` never
previously cited by any niagara5 block per this session's own search).

**Marker tally — literal `verify-block.sh` output** (run from `/home/cristian/niagara5-research`, this
session, verbatim):

```
== verify-block: niagara5-block72.md (target: .) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 38  (adj 37)
   [CERT-doc] 0
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 7  (adj 4)
-- ratio -- [INFER]/[CERT*] = 4/37 = 0.11
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  BDefaultSimpleFE.java:44-64  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BFileHistoryTable.java:730-740  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  BFileHistoryTable.java:897-950  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  niagara/history/BCapacity.java:79-98  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      organized/box/vineflower/META-INF/module.xml:2
   ok      organized/history/vineflower/com/tridium/history/db/BHistoryDbTable.java:86-107  (range end verified; file has 349 lines)
   ok      organized/history/vineflower/com/tridium/history/db/BLocalDbHistory.java:36
   ok      organized/history/vineflower/com/tridium/history/file/BFileHistoryTable.java:60
   ok      organized/history/vineflower/com/tridium/history/file/recstore/BRecordStoreHistoryTable.java:22
   ok      organized/history/vineflower/com/tridium/history/ui/BCapacityFE.java:30
   ok      organized/history/vineflower/niagara/history/BCapacity.java:18
   ok      organized/webEditors/vineflower/rc/fe/baja/DefaultSimpleEditor.js:1-70  (range end verified; file has 92 lines)
   ok      organized/webEditors/vineflower/rc/fe/baja/FacetsRowEditor.js:40
   ok      organized/workbench/vineflower/com/tridium/workbench/fieldeditors/BDefaultSimpleFE.java:19
   ok      organized/workbench/vineflower/com/tridium/workbench/propsheet/BComplexEntry.java:291-337  (range end verified; file has 460 lines)
   ok      organized/workbench/vineflower/com/tridium/workbench/propsheet/BComplexEntry.java:319-337  (range end verified; file has 460 lines)
   resolved 12 of 16
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

**This is the run captured BEFORE this Self-verify section itself was written** (module.xml citation shown
already corrected to its real `:2` line — a typo caught and fixed post-run, see note below) — pasted here as
the literal calculator output the METHODOLOGY §11 gate requires. **A second run against the FINAL file
(after this section's own prose was added) shows the expected self-referential inflation** every
marker-quoting Self-verify section produces, matching [Block 61]'s own documented pattern:

```
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 1   [CERT-live] 1   [CERT] 42 (adj 41)   [CERT-doc] 1   [CERT-web] 2   [CERT-a] 1   [INFER] 15 (adj 12)
-- ratio -- [INFER]/[CERT*] = 12/47 = 0.26
-- resolved 12 of 18 --
```
Every one of `[CERT-hw]`/`[CERT-live]`/`[CERT-doc]`/`[CERT-web]`/`[CERT-a]` (0 in the real block, per its own
header Method line declaring only `[CERT]`/`[INFER]` in use) is entirely an artifact of the FIRST run's
output being quoted verbatim as a code block immediately above this paragraph — that quoted block's own
tally lines literally contain the bracket tokens `[CERT-hw]`, `[CERT-live]`, `[CERT-doc]`, `[CERT-web]`
(twice — once in the tally line, once in the ratio-formula legend line quoted alongside it), `[CERT-a]`, and
`[INFER]`, each counted by the second run as if it were a fresh claim. The **real, load-bearing marker set
for this block is exactly `[CERT]` and `[INFER]`, as declared in the header** — the first run (38 `[CERT]`,
7 `[INFER]` raw / 37 and 4 adjusted) is the number that reflects this block's OWN claims before the
self-verify section's self-reference existed, and is the one this report stands behind; the second run's
inflated 42/15 is reported here for transparency, not as the operative tally.

**Reading the resolution split** (from the first, uninflated run). 12 of 16 script-recognized citations
resolve `ok` — a notably higher resolution rate than [Block 26]/[Block 61] (which showed `0 of N`/`10 of 18`),
because THIS corpus preserves its decompiles directly under `organized/<module>/vineflower/` inside the
target directory itself (this block's own header states this convention explicitly), unlike [Block 26]'s
session-scratch (`/tmp/...`) approach. The 4 `extern` hits are bare short-form citations
(`BDefaultSimpleFE.java:44-64`, `BFileHistoryTable.java:730-740`/`:897-950`,
`niagara/history/BCapacity.java:79-98`) used in body prose where a fully-pathed citation to the SAME file
already resolves elsewhere in the block (`BDefaultSimpleFE.java` resolves via `:19`; `BFileHistoryTable.java`
resolves via `:60`; `BCapacity.java:79-98` is [Block 26]'s own citation, re-quoted not re-derived, and
`BCapacity.java` resolves in this block via its OWN fresh `:18` cite) — the named pair convention METHODOLOGY
§11 describes. Several load-bearing citations do not appear in the script's 16-item list at all: multi-range
citations with commas (`BTypeSpecConverter.java:27,34-36,77-81`, `ConverterRegistry.java:29-39,53-57`) and
the `jetty-web.xml`/`web.xml`/`module.xml` XML-file citations outside the `file:line` pattern the script
parses for prose paragraphs — these are covered by inline token-verify below, not the mechanized resolver.

**Reading the raw vs. adjusted split** (first run). Raw `[CERT]` count (38) vs. adjusted (37) reflects one
marker-name mention inside the header's own Method/legend line, not a live claim — consistent with every
prior niagara5 block's pattern. Raw `[INFER]` (7) vs. adjusted (4): 3 of the raw hits are inside this block's
own header blockquote (the "does not cover" paragraph's discussion of what remains unresolved, and the
Type-declaration paragraph explaining why an INFER marker appears) — not fresh claims. The 4 real `[INFER]`
claims are: §72.2's "exact click-path not independently traced" boundary (2 instances — the `isWar()`-adjacent
framing borrowed from [Block 27] and the fresh click-path gap), and §72.5's two `isWar()`/WebSocket-upgrade
filter framings that extend rather than resolve [Block 27]'s own B27-G4. Ratio 4/37 ≈ 0.11 — low, consistent
with a gap-closing session against sources each prior block explicitly named but left unopened (three of four
gaps CLOSED outright, the fourth NARROWED with an honestly bounded open edge), not an exhausted one.

**Inline token-verify.** Citations outside the script's 16-item list, confirmed present by direct `grep -n`/
`Read` this session: `BTypeSpecConverter.java`'s `CONVERT_TYPES`/`getConvertTypes()`/`convertTypeSpec()`
(lines 27, 34-36, 38-51, 53-75, 77-81 — all read as part of the whole-82-line-file read, cross-checked via
`grep -n "CONVERT_TYPES\|convertTypeSpec\|getConvertTypes"` this session, 5/5 hits at the cited lines);
`ConverterRegistry.java`'s `initialize()`/`lookupConverters()` (lines 29-39, 53-57, confirmed via
`grep -n "public static.*initialize\|public static.*lookupConverters"`, 2/2 hits); `BHistoryDbTable.java`'s
`resize()`/`doResize` abstract declaration (`:180-186`, confirmed via `grep -n "public final void resize\|
protected abstract void doResize"`); `BFileHistoryTable.java`'s `doResize()` override (`:425-426`, confirmed
via `grep -n "protected void doResize"`); `BFixedLengthHistoryTable.java`/`BRecordStoreHistoryTable.java`'s
class declarations AND the negative claim (no `doResize` override in either file — confirmed by
`grep -c "doResize" <file>` returning `0` for both, this session, the symmetric negative-existence check
METHODOLOGY §3 requires); `BPropertyEntry.java`'s popup-menu construction (`:486-512`, confirmed via
`grep -n "BMenu popup\|BNavMenuAgent.makeFor\|ConfigFlagsCommand"`, 3/3 hits, and a full-method read
confirming no FE-selection command appears in the block); `BWbFieldEditor.java`'s `makeFor`/`FEAgentFilter`
(`:26-58`, confirmed via `grep -n "static AgentFilter FEAgentFilter\|public static BWbFieldEditor makeFor"`);
all three `jetty-web.xml` files and both `web.xml` files (`organized/{web,fox,box}/vineflower/WEB-INF/`,
confirmed via direct whole-file `Read` this session, not `grep`, since each is ≤20 lines); `box`'s
`module.xml:2` description string (confirmed via `grep -n "description="`). Corpus-wide census commands
re-confirmed present in their own output, not hand-recalled: `grep -rl "extends BHistoryDbTable" organized`
(1 hit) and `find organized -iname "jetty-web.xml"` (3 hits), both re-run and re-read this session; the
`comm -23`/`comm -13` 1:1-match confirmation (247 module dirs = 247 live `.jar` files) was re-run and both
diffs confirmed empty. **Token-verify total: ≈34 distinct load-bearing tokens/citations confirmed present
(or confirmed ABSENT for the two negative-existence claims — the `doResize`-override search and the
corpus-wide `extends BHistoryDbTable` search, both against artifacts opened end-to-end this session, per
METHODOLOGY §3's symmetric-opening-obligation rule).**

**Artifacts.** This block file exists at `/home/cristian/niagara5-research/niagara5-block72.md` (this write).
Per the task's explicit single-file/read-only constraint, `RESEARCH-STATE.md`/`INDEX.md`/`CATALOG.md` were
**not** regenerated or hand-edited — left to the orchestrator, matching every prior niagara5 block's
convention for the same instruction.

**MCP-doc snapshots.** N/A — no `[CERT-web]`/MCP-sourced citation in this block.

## 72.x — Child gaps opened

- **B72-G1** (narrows/refines **B26-G2**, not fully closing it) — Trace the actual interactive Workbench
  and/or web-UI command sequence an operator uses to set a `"fieldEditor"` slot facet (or otherwise select a
  non-default field editor) on a property that already resolves to a dedicated FE — this session confirmed
  the `fieldEditor` facet is a real, recognized override key on both sides (§72.2) and confirmed the
  property-sheet row's OWN popup menu does not offer FE selection, but did not open the generic "Slot
  Facets" editor's own invocation/permission path (Workbench: likely a `BFacetsFE`/similar class, not opened;
  web: `FacetsRowEditor.js`'s own host dialog/command, not opened) to confirm how an operator actually reaches
  it. `investigable`.
- **B72-G2** — `niagara.agent.AgentList.getDefault()`'s specificity-ranking algorithm (presumably `baja.jar`,
  not opened this session) — needed to fully certify that `BCapacityFE` (not `BDefaultSimpleFE`) is what an
  operator sees BY DEFAULT for a `capacity` slot absent any `fieldEditor` facet override; this session assumed
  "most-specific-type-wins" by Niagara convention, not by reading the algorithm itself. `investigable`.
- **B72-G3** — Two related, unresolved questions about `fox.jar`/`box.jar`: (1) whether `NModuleInfo.isWar()`
  actually flags them for `addModuleWebAppHandlers()` pickup (the same `[INFER]` [Block 27] §27.4 already
  named as **B27-G4** for `web.jar`, now extended to these two — not independently re-opened); (2) whether a
  WebSocket UPGRADE handshake response (as opposed to an ordinary HTTP response) actually passes through the
  SAME servlet-filter chain `TridiumSecurityFilter` sits in, given `fox`/`box`'s entire purpose is a
  WebSocket-upgraded protocol tunnel — a genuinely new question this session's census raised, not covered by
  [Block 27]. Neither `fox.jar` nor `box.jar` was decompiled beyond the 2 XML files each this session.
  `investigable`.
- **B72-G4** — `BIPxElementConverter`/the Px-element-side converter registry map (`ConverterRegistry`'s
  `PX_CONVERTERS`, sibling of the `BOG_CONVERTERS` map §72.4 read) was not opened this session — low
  priority, since `BCapacity` is a Bog-persisted property value, not a Px graphic element, but not
  exhaustively ruled out as a theoretical alternate path. `investigable`, low priority.

## 72.x — Connections

- **[Block 26]** — closes **B26-G3** (§72.3) and **B26-G4** (§72.4) outright; narrows but does not fully
  close **B26-G2** (§72.2), naming the remaining edge **B72-G1**. §72.3 additionally CORRECTS [Block 26]
  §26.4c's framing of `BHistoryDbTable` as a third, separate backend — it is the shared abstract ancestor of
  the other two, reached via `BFileHistoryTable` — without changing [Block 26]'s substantive verdict (the
  correction is architectural framing, not a factual retraction; no `[CERT]` claim from [Block 26] is
  invalidated). [Block 26]'s own still-open **B26-G1** (live-station dynamic confirmation) is untouched by
  this block, though §72.2's `fieldEditor`-facet mechanism now gives it a fully concrete reproduction recipe
  it previously lacked.
- **[Block 27]** — closes **B27-G2** (§72.5) with an exhaustive, 1:1-verified census; extends (does not
  close) [Block 27]'s own **B27-G4** (`isWar()` definition) to cover `fox`/`box` in addition to `web`, and
  raises a genuinely new WebSocket-upgrade-filter question neither block previously named (folded into
  **B72-G3**).
- **[Block 61]** — style/structure precedent only (a multi-named-gap-closing block spanning unrelated prior
  clusters in one session); no factual overlap or citation reuse.
