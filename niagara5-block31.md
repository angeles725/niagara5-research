# Block 31 — Do PANCCADIA's unconverted N4 objects load in N5? Type and slot compatibility census

> Research of **whether PANCCADIA's real `config.bog` objects actually LOAD in Niagara 5**, closing
> [B24]'s child gap **B24-G6**: [B24] §24.6 found that `tagdictionary` (105 counted), `kitControl` (100),
> and `nrio` (96) — PANCCADIA's three largest custom-logic categories — have **NO registered converter** in
> `migrator.jar` and pass through `n5mig` unconverted; this block asks whether "unconverted" means "loads
> unchanged" or "loads broken." For every distinct typespec PANCCADIA's real `config.bog` actually uses
> (full re-census, not [B24]'s partial sample — see §31.1), this block checks (1) the module resolves in
> the N5 5.0.0.28 install, (2) the type name is registered in that module's `module.xml`, and (3) the
> frozen-slot shape of the backing Java class matches between N4 and N5 closely enough that no bog data is
> orphaned — and where it does not match, traces N5's own bog decoder (`ValueDocDecoder`) to determine what
> actually happens to an orphaned property at load time (§31.5). Covers every module prefix present in the
> real `config.bog` sample: `baja`, `bacnet`, `history`, `tagdictionary`, `alarm`, `nrio`, `control`,
> `kitControl`, `driver`, `web`, `converters`, `box`, `niagaraDriver`, `obixDriver`, `hierarchy`, `nss`,
> `basicDriver`, `search`, `provisioningNiagara`, `backup`, `batchJob`, `fox`, `hx`, `niagaraVirtual`,
> `program`, `template`, `jetty`, plus the 3 custom modules (`ColdRoomPan`/`CRP`, `DashboardPan`/`DPCD`,
> `CompPan`/`COMPAN`). **`schedule` does NOT appear in this sample** — `config.bog` is the driver-network
> file only ([B24] §24.6's scope note, re-confirmed §31.1); schedule/points/histories/alarms bogs were not
> in the poc copy, so `schedule:*` typespec compatibility remains untested (child gap, §31.9).
> Does **not** cover: an actual `n5mig` execution (inherits B14-G1/B24-G1, still requires-execution);
> PANCCADIA's points/histories/alarms/schedule bog files (inherits B24-G2, not in the poc copy); a
> byte-for-byte re-encode/round-trip test (this block traces the DECODE path only, via static source
> reading — no station was booted).
>
> Subject version: Niagara **5.0.0.28 (Beta)** N5 install (same as [B10],[B14],[B24]) cross-checked against
> the **N4 4.14.0.162** decompile in `niagara-research/organized` (dated 2024-05-28 per that corpus's own
> `module.xml`) — **NOT** PANCCADIA's actual N4 build, which [B14] §14.2 establishes is **4.15**-versioned
> (`n5mig`'s own USAGE text: "a 4.15 versioned station backup distribution file"). This is a genuine
> **version gap** between the N4 baseline available for slot-diffing and PANCCADIA's real N4 build — flagged
> explicitly wherever it affects a verdict (§31.4, §31.6). N5 jar sha256 (this session):
> `baja.jar` `0a7fcbfcbd1a609ed0eba0c1abfbf7e3de372b6a51f551dcea497649d4e3fd9c`,
> `bacnet.jar` `6e1ad472b06b281c46700aa962986430ccf7e91c396c9eb308dc5b3f674ee969`,
> `history.jar` `9fc1c9b1768fdc6e44456c2374df802565ea5afecf69d443f375082b49a612cf`,
> `tagdictionary.jar` `1f97a4482f1355e6b20bbd97413c42fa745f3716b499e48e98549813c01aa227`,
> `kitControl.jar` `c79c3520ef511602d4349bbcc65a4a6ebbe707ad1e8cd82edabadfcb04ff8fd5`,
> `nrio.jar` `2611d7885feebd076450ae09591c6e110f8edb6d437259668dee596d44fcec19`,
> `control.jar` `3da9845f5d3299f494a5d70898703dd906c1c920a68cc1645b778f1e45d1f6a4`,
> `alarm.jar` `fb5b21c30412dceedd12adbf2e29843e2a05d0b8b9883fa4cb387c18297cc32f`. PANCCADIA `config.bog`
> (`poc/n5mig-panccadia/in/config.bog`, same file [B24] read) sha256
> `96e429deabdff32af9dfa0e87b4eafef28481f196e0e068e46e07fd86d0c1075` — unchanged since [B24]'s session.
>
> Sources: PANCCADIA `config.bog` `file.xml` (unzipped this session, read-only, count-only per task scope —
> no point values or credentials extracted beyond what a `t=`/`m=`/property-name census requires; a handful
> of literal leaf VALUES are quoted below only where load-bearing for the decode trace — e.g. `foxsCert`'s
> literal string `"default"`, `webNavFile`'s literal `"null"` — none are credentials); N5 module.xml files
> under `/home/cristian/niagara5-research/organized/<module>/vineflower/META-INF/module.xml` (27 standard
> modules); N5 Vineflower decompile trees under `organized/<module>/vineflower/`; N4 module.xml files under
> `/home/cristian/niagara-research/organized/<module>/<module>-rt|wb|ux/vineflower/META-INF/module.xml` (or
> `organized/baja/baja/vineflower/...` for the one module with no rt/wb/ux split); N4 Vineflower decompile
> trees under the matching `<module>-rt/vineflower/`; `ValueDocDecoder.java` (1,276 lines, N5 `baja.jar`,
> full read of the bog-decode path `parseSlot()`/`decodePrimitive()`/`BogTypeResolver.newInstance()`);
> `BBacnetBogConverter.java`, `BProgramServiceConverter.java` (migrator.jar, re-read for exact
> converter-covered property lists); `BComponent.java` (N5 baja.jar, `add()` signature confirmation).
>
> Method: `python3 zipfile`+`re` full census of `t=`/`m=` attributes in `file.xml`, **both single- and
> double-quoted attribute forms** (§31.1 — a correction to [B24] §24.6's undercount, which only matched
> single-quoted `t='...'`); scripted cross-reference of every (module, type) pair against each module's
> `module.xml` `<type>` registry (both N4 and N5, both `class=name=` and `name=class=` attribute orderings —
> N4's module.xml uses `name=` before `class=`, the opposite order from N5's, §31.2); scripted `file:line`
> location of each type's backing `.java` source in both trees; scripted `@NiagaraProperty(name = "...")`
> extraction and set-diff (added/removed) per type, own-declared level; a second pass walking one
> `extends <Superclass>` level up for every type that declares zero properties of its own, to catch an
> inherited-only slot delta a leaf-level diff would miss (§31.4); full read of `ValueDocDecoder.parseSlot()`
> or an orphaned/removed bog property (§31.5); spot literal-value grep in `file.xml` for every type with a
> removed property, to determine whether the orphan case is theoretical or actually present in PANCCADIA's
> real data (§31.6).
> Markers: `[CERT]` local primary source (`file:line`) · `[INFER]` deduction.
>
> Build/porting layer. Directly closes [B24] B24-G6 (posed as this block's task). Connects [B14] (migrator
> SPI mechanics), [B24] (the converter catalog + the original, undercounted PANCCADIA cross-check), [B10]
> (module-porting checklist CHK-1..CHK-14).
>
> **Type:** `mixed` — §31.1-§31.3 are evidence blocks (reading module.xml/jar/decompiled-source presence,
> mechanically); §31.4-§31.6 draw `[INFER]` conclusions by cross-referencing three independent artifacts
> (N4 decompile, N5 decompile, PANCCADIA's real bog bytes) against each other and against `ValueDocDecoder`'s
> control flow — the declared `mixed` trigger.

---

## 31.1 — Full re-census of PANCCADIA's `config.bog` typespecs: 3,545 elements, not 1,389 `[CERT]`

Re-unzipping `config.bog` → `file.xml` (486,798 bytes, unchanged size from [B24]) and re-running the `t=`
typespec census **with both XML quoting styles** finds **3,545** typed elements across **30** modules and
**288** distinct types — not [B24] §24.6's **1,389**. The gap is a regex bug in [B24]'s own census, not new
data: [B24] §24.6 used `grep -o "t='[a-zA-Z0-9]*:"` (single-quote only); this bog mixes single-quoted
elements (ones with a handle `h=`, i.e. components with children) and double-quoted LEAF elements (simple
value properties, no children) — `grep -c "t='bac:" file.xml` → **43**, `grep -c 't="bac:' file.xml` → **851**,
combined → **894**. `[CERT]` re-run this session at `/tmp/claude-1000/n5b31/file.xml`; module-alias map
(`m='abbrev=fullname'`, 30 entries, zero collisions) re-derived the same way [B24] did.

| Module | Objects (corrected) | Distinct types | [B24]'s figure |
|---|---|---|---|
| `baja` | 1,708 | 62 | not separately counted |
| `bacnet` | 894 | 57 | 43 |
| `history` | 173 | 14 | 47 |
| `tagdictionary` | 147 | 32 | 105 |
| `alarm` | 119 | 7 | 47 |
| `nrio` | 115 | 12 | 96 |
| `control` | 114 | 7 | not separately counted |
| `kitControl` | 100 | 11 | 100 (matches — single-quoted, handle-bearing) |
| `ColdRoomPan` | 35 | 5 | 25 |
| `driver` | 27 | 8 | not separately counted |
| `web` | 24 | 16 | 17 |
| `DashboardPan` | 8 | 4 | 8 (matches) |
| `CompPan` | 1 | 1 | 1 (matches) |
| (17 more modules) | ≤16 each | — | mostly not separately counted |

`kitControl`/`DashboardPan`/`CompPan` match [B24] exactly because their objects are all handle-bearing
component-level entries (single-quoted); `bacnet`/`tagdictionary`/`nrio`/`history`/`alarm` are undercounted
in [B24] because most of their bulk is double-quoted LEAF properties (simple values, sub-objects) that
[B24]'s single-quote-only regex never saw. `[CERT]` `/tmp/claude-1000/n5b31/type_counts.json`,
`module_counts.json` (this session's script output, full per-type breakdown).

## 31.2 — Module + type registry check: all 27 standard modules resolve 100%, only the 3 custom modules are absent `[CERT]`

For every one of the 30 modules used by PANCCADIA, this session checked (a) does `<module>.jar` exist under
`/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules`, and (b) does that module's `module.xml`
`<types>` block declare EVERY type name PANCCADIA actually uses.

| Result | Modules | Types checked | Missing |
|---|---|---|---|
| Jar present + module.xml present + **0 missing types** | 27 (all standard Tridium modules: `baja`, `bacnet`, `history`, `tagdictionary`, `alarm`, `nrio`, `control`, `kitControl`, `driver`, `web`, `converters`, `box`, `niagaraDriver`, `obixDriver`, `hierarchy`, `nss`, `basicDriver`, `search`, `provisioningNiagara`, `backup`, `batchJob`, `fox`, `hx`, `niagaraVirtual`, `program`, `template`, `jetty`) | 283 distinct (module, type) pairs | **0** |
| Jar absent, module.xml absent | 3 (`ColdRoomPan`, `DashboardPan`, `CompPan`) | 10 distinct types (44 objects: 35+8+1) | **all 10** |

`[CERT]` script output `/tmp/claude-1000/n5b31/module_type_check.json`; a zero-missing result across every
standard module means the TYPE-NAME REGISTRY LOOKUP `BTypeSpecConverter`/`BogTypeResolver.newInstance()`
performs ([B14] §14.6, `MigratorTypeResolver.java:54-107` per [B24] §24.4) succeeds for every standard-module
typespec PANCCADIA's config.bog references — **even where the backing Java CLASS moved package**
(`javax.baja.*`→`niagara.*`, confirmed for 20 of the 288 types this session, e.g. `control:BooleanWritable`
`javax.baja.control.BBooleanWritable`→`niagara.control.BBooleanWritable`) — because the bog's `t=` attribute
encodes the type's **module:TypeName string**, not the Java FQCN; `module.hasType(tname)` (`BogTypeResolver`
line 1162, §31.5) resolves purely off that public name, which is unchanged. This is the mechanical
confirmation [B14]/[B24] inferred but did not directly verify: type-NAME stability survives the
package-rename refactor even where the class itself moved.

The **3 custom modules confirm and refine [B14] §14.5/[B24] §24.6's finding** (44 objects, not [B24]'s 34 —
the corrected census, §31.1): with no jar and no module.xml, `Sys.getRegistry().getModule(moduleName)` throws
`ModuleNotFoundException` for every `coldRoomPan:*`/`dashboardPan:*`/`compPan:*` typespec, which is exactly
the trigger [B14] §14.5 documents for `BModuleRemovalConverter`'s synthesis — these 44 objects are silently
STRIPPED by `n5mig`, not merely left unresolved, unless the 3 modules are rebuilt/signed/installed on the
target N5 machine BEFORE migration (the same CHK-1..CHK-14 deployment-order constraint [B14] §14.10 already
states — not re-derived here, only re-confirmed with the corrected object count).

## 31.3 — Slot-diff method: own-declared `@NiagaraProperty` plus one inheritance-level walk `[CERT]`

For every (module, type) pair that resolves in both N4 and N5 (283 standard pairs minus 5 with no N4-side
match, §31.4), this session located the backing `.java` source in both the N4 4.14.0.162 decompile
(`niagara-research/organized/<module>/<module>-rt|wb|ux/vineflower/`) and the N5 5.0.0.28 decompile
(`niagara5-research/organized/<module>/vineflower/`) by FQCN path, and extracted every `@NiagaraProperty(name
= "...")` declaration. Package/class paths otherwise match 1:1 between N4 and N5 for every
non-core-framework type checked (e.g. `com.tridium.kitControl.math.BMultiply` is the SAME path in both trees,
`[CERT]` `find` this session — present at both
`niagara-research/organized/kitControl/kitControl-rt/vineflower/com/tridium/kitControl/math/BMultiply.java`
and `niagara5-research/organized/kitControl/vineflower/com/tridium/kitControl/math/BMultiply.java`); only
core-framework types under `javax.baja.*` (N4) move to `niagara.*` (N5), confirmed for the 20 renamed classes
this session found (§31.2).

**Own-declared-property diff alone undercounts a delta**: 96 of 288 types declare ZERO properties of their
own (`NO_PROPS_DECLARED` — they inherit their full slot set from a superclass, e.g. `BMultiply extends
BQuadMath` declares nothing itself, `BQuadMath` declares `inA`/`inB`/`inC`/`inD`). A second pass walked one
`extends` level up for all 96 and diffed the PARENT class the same way. Result: 94 of 96 parents are
byte-identical (zero added, zero removed); the 2 exceptions are `box:HistoryChannel`/`box:AlarmChannel`,
whose N4 parent `BBoxChannel` is replaced by a DIFFERENT N5 parent `BWrapperBoxChannel` adding `faultCause`/
`status` — an addition, not a removal, so it does not orphan any bog data (§31.4's safety rule). `[CERT]`
`/tmp/claude-1000/n5b31/slot_diff_results2.json` (script output, this session); representative spot-checks:
`BQuadMath.java` N4 `:15-30` vs N5 `:15-21` (`inA`/`inB`/`inC`/`inD`, identical), `BQuadLogic.java`,
`BComparison.java`, `BBinaryMath.java`, `BMuxSwitch.java`, `BLogic.java` (kitControl's 5 relevant parent
classes, all zero-delta, re-read this session).

## 31.4 — Aggregate verdict: 259/288 types byte-identical, 16 safely add properties, 8 have a removed slot, 5 are version-gap-unresolved `[CERT]` `[INFER]`

| Verdict | Distinct types | Objects (of 3,545) | Meaning |
|---|---|---|---|
| **CLEAN** (own+inherited slot set identical) | 259 | 3,401 (96.0%) | Loads byte-for-byte unchanged |
| **Added-only delta** (N5 adds new optional properties, nothing removed) | 16 | 60 | Loads clean — new property takes its declared default, no orphan data |
| **Removed-property delta** (N5 drops a frozen slot PANCCADIA's type declared) | 8 | 34 | §31.5/§31.6 — orphan-slot risk, traced below |
| **Version-gap unresolved** (type absent from the N4 4.14.0.162 baseline entirely) | 5 | 6 | §31.4a — cannot slot-diff, but type+class fully present in N5 |
| **Custom module, N5-absent entirely** | 10 | 44 | §31.2 — module removal, not a slot question |

`[CERT]` `/tmp/claude-1000/n5b31/slot_diff_results2.json` full tally (259+16+8+5=288 standard-module distinct
types; 3,401+60+34+6=3,501 standard-module objects; +44 custom-module objects = 3,545 total, reconciles to
§31.1's re-census). The 16 added-only types (by object count): `control:BooleanWritable` (33, adds
`minTimer`/`wasActive`), `kitControl:BooleanDelay` (3, adds `lastInput`/`ticket`), `baja:ServerPort` (4, adds
`ruleHintOverride`), `baja:User` (5, adds `faultCause`/`icon`), `baja:AutoLogoffSettings` (2, adds
`absoluteLogoffEnabled`), `kitControl:OneShot` (2, adds `lastInput`/`ticket`), `bacnet:NetworkPort` (2, adds
`networkNumberQuality`), plus 9 single-object types (`backup:BackupService`, `backup:BackupRecord`,
`bacnet:BacnetNetwork`, `bacnet:BacnetServerLayer`, `bacnet:BacnetRouterEntry`, `bacnet:LocalBacnetDevice`,
`bacnet:ExtensibleEnumList`, `baja:UserService`, `niagaraDriver:ProviderStation`). **An added property can
never orphan bog data** — the migrated bog simply doesn't carry an element for a slot that didn't exist yet
when it was written, so the new N5 default silently applies; this class of delta is included here for
completeness (it IS a structural change worth knowing about) but carries no load risk. `[CERT]` per-type
added-list, `slot_diff_results2.json`.

### 31.4a — The 5 version-gap-unresolved types: real N4 4.15 objects, absent from this corpus's 4.14.0.162 baseline `[INFER]`

`bacnet:BacnetNetworkNumberQuality`, `bacnet:BacnetIpServerPort`, `bacnet:BacnetMstpPortDescriptor`,
`bacnet:BacnetNetworkPortPendingChanges`, `tagdictionary:QudtUnitTag` — none of these 5 type names or their
backing classes (`BBacnetNetworkNumberQuality`, `BBacnetIpServerPort`, `BBacnetMstpPortDescriptor`,
`BBacnetNetworkPortPendingChanges`, `BQudtUnitTag`) exist ANYWHERE in the `niagara-research/organized`
decompile tree (`grep -rl` for each class declaration, this session, zero hits). Since these ARE literal
`t=` typespecs in PANCCADIA's real `config.bog` (e.g. `t='bac:BacnetIpServerPort'` backing a real
`udpServerPort` child object at `file.xml:4434`, §31.6), they unambiguously exist in SOME N4 build ≤4.15 —
they cannot be "new in N5" despite matching [B24]'s literal search pattern for such a claim. **The correct
reading is a corpus version gap**: this session's only available N4 `bacnet`/`tagdictionary` decompile is
stamped `vendorVersion="4.14.0.162"` releaseDate 2024-05-28 (`[CERT]`
`niagara-research/organized/bacnet/bacnet-rt/vineflower/META-INF/module.xml:2`), while [B14] §14.2
establishes PANCCADIA's real backup is 4.15-versioned — these 5 types most plausibly correspond to the
BACnet Network-Port / IP-Server-Port object family and a QUDT semantic-tag addition shipped in a 4.14→4.15
point release this corpus's `bacnet-rt`/`tagdictionary-rt` decompile predates. `[INFER]`: no N4 4.15 decompile
is available in either corpus to confirm the exact slot shape at that specific version. **What IS confirmed**:
all 5 types are fully present in N5 with real, non-stub class bodies (`niagara5-research/organized/bacnet/
vineflower/niagara/bacnet/enums/BBacnetNetworkNumberQuality.java`, `.../com/tridium/bacnet/stack/link/ip/
BBacnetIpServerPort.java`, `.../niagara/bacnet/export/BBacnetMstpPortDescriptor.java`, `.../niagara/bacnet/
export/BBacnetNetworkPortPendingChanges.java`, `niagara5-research/organized/tagdictionary/vineflower/
com/tridium/tagdictionary/tag/BQudtUnitTag.java` — all 5 files read this session, non-empty, real
`@NiagaraProperty` declarations present) — so the TYPE-resolution half of "does this load" is answered
(`[CERT]`, yes); only the exact N4-4.15-vs-N5 slot-shape match is open — flagged as **B31-G1**.

## 31.5 — What actually happens to an orphaned removed property: traced through `ValueDocDecoder` `[CERT]`

`ValueDocDecoder.parseSlot()` (N5 `baja.jar`, full read this session,
`niagara5-research/organized/baja/vineflower/niagara/io/ValueDocDecoder.java:294-529`) is the bog-decode
method that resolves every `<p n="..." .../>` element against the LIVE target component's slot table. The
load-bearing branch for a REMOVED frozen property:

```
Slot slot = parent.getSlot(name);          // :392 — null if the N5 class no longer declares this slot
...
Property prop = (Property) slot;            // :416 — null-safe cast; prop is null if slot was null
if (decodePrimitive(parent, prop, value)) ...  // :417 — decodePrimitive() returns false immediately
                                                //         when prop == null (:565), so this never short-circuits
object = plugin.getTypeResolver().newInstance(this, parent, name, prop, type);   // :427
```

`BogTypeResolver.newInstance()` (`:1144-1178`) then branches on whether the ORPHANED element still carries an
explicit `t=` type attribute:

- **No `t=` attribute** (`typeStr == null`, `:1145-1151`): since `prop` is also null (slot removed), this
  hits `decoder.plugin.warningAndSkip("Missing frozen property: " + propName); return null;` — the element
  is **dropped with a logged WARNING, load continues**, nothing is set on the component. `[CERT]`
  `ValueDocDecoder.java:1145-1151`.
- **Explicit `t=` attribute present** (`typeStr != null`): the type still resolves normally
  (`module.hasType(tname)` → `typeResolverNewInstance(module, tname)`, `:1160-1164`) — the ORPHANED VALUE'S
  OWN type is unaffected by ITS PARENT losing the slot — and a real `BValue` instance is constructed and its
  literal value decoded (`decodeSimple`, back in `parseSlot` `:469-475`). Then, back in `parseSlot`
  (`:488-503`): since `prop` is null but `parent` (a `BComponent`, e.g. `BFoxService`/`BHistoryConfig`) IS a
  component, the code takes the `else if (parent.isComponent())` branch and calls
  **`parent.asComponent().add(name, object, i, facets, Context.decoding)`** (`:500`) — the ORDINARY
  DYNAMIC-SLOT-ADD method (`BComponent.add(String, BValue, int, BFacets, Context)`, confirmed a real public
  method, `[CERT]` `niagara5-research/organized/baja/vineflower/niagara/sys/BComponent.java:428`). **The
  orphaned value is silently RESURRECTED as a DYNAMIC property on the loaded component, carrying its
  original literal value, with NO warning logged for this path** (contrast the no-`t=` case, which does warn).

**Either branch is non-fatal — load continues, the station model does not fail to build.** The only
observable difference is whether the orphaned data survives (as a dynamic property, if `t=` was present) or
is dropped (with a warning, if `t=` was absent). No code path in `parseSlot`/`newInstance` throws for a
removed-but-otherwise-well-formed property element — an actual load FAILURE requires either an unresolvable
MODULE (§31.2, not the case for any of PANCCADIA's 27 standard modules) or a malformed XML element (`Unknown
element`, `:520-524`), neither of which applies to a plain removed-property case. `[CERT]`
`ValueDocDecoder.java:386-514` (full `parseSlot` removed-property path, both branches), `:1144-1178`
(`BogTypeResolver.newInstance`, both branches).

## 31.6 — Cross-checking the 8 removed-property types against PANCCADIA's real bog bytes and the migrator catalog `[CERT]` `[INFER]`

| Module:Type | Objects | Removed slot(s) | Registered `migrator.jar` converter? | Literal orphan data present in this bog? | Practical verdict |
|---|---|---|---|---|---|
| `bacnet:BacnetDevice` | 1 | `pollFrequency` | **YES** — `BBacnetBogConverter` ([B24] §24.2 confirms; this session `grep` for `pollFrequency` in `file.xml` → 0 hits anyway) | No | Converter strips it during `stubBog()`, never reaches decode |
| `bacnet:BacnetIpLinkLayer` | 1 | `udpPort` | **YES** — `BBacnetBogConverter.java:207-208`, `this.removeProperties(x, "bacnet:BacnetIpLinkLayer", List.of("udpPort"))` (re-read this session) | **Yes** — `<p n="udpPort" f="rh1"/>` at `file.xml:4433` (flags-only, no `v=`/`t=`) | Converter strips it BEFORE decode; if it somehow survived, §31.5's no-`t=` path applies (warn+skip, non-fatal) |
| `web:WebService` | 1 | `appletModuleCachingType`, `rememberUserIdCookie`, `webStartConfig` | **YES** — `BWebBogConverter` ([B24] §24.2, targeted slot removal for `WebService` since it has children) | Not independently re-checked (already [B24]'s finding) | Converter-covered |
| `jetty:JettyWebServer` | 1 | `qualityOfServiceSettings` (→ split into `qualityOfServiceHandlerSettings`+`threadLimitHandler` in N5) | **Likely** — `BJettyQoSFilterMigrator` ([B24] §24.2 documents the same QoS-Filter→QoS-Handler family rename at slightly different property granularity) | Not checked | Converter-covered (same rename family) |
| `program:ProgramService` | 1 | `allowProgramRuntimeExec`, `compactProfile` | **PARTIAL** — `BProgramServiceConverter.java` (re-read in full this session) removes ONLY `allowProgramRuntimeExec` (literal string match, `convertXElem:30-38`); `compactProfile` is NOT referenced anywhere in the converter | `grep` for both names in `file.xml` → **0 hits** | `compactProfile` is an uncovered orphan CLASS, but this station's real `ProgramService` instance never set a non-default value for either property, so no literal element exists to be orphaned |
| `history:HistoryConfig` | 23 | `historyName` | **NO** — [B24] §24.6 confirms `migrator.jar` registers zero `history:*` converters; re-confirmed this session (no `history` prefix anywhere in [B24] §24.2's 58-row catalog) | `grep` for `historyName` in `file.xml` → **0 hits**; spot-read of 3 real `HistoryConfig` instances (`file.xml:351-360` area) shows only `id`/`source`/`timeZone`/`recordType`/`schema`/`timestampFacets` — `historyName`'s N4 default is `""` (`[CERT]` `BHistoryConfig.java:87`, `newProperty(6, "", null)`), so a station that never set a custom value never encodes the element | Uncovered orphan CLASS, but **zero of the 23 real instances trigger it** — historyName's N4 default is the empty string, and Niagara's bog encoder omits default-valued properties |
| `web:MobileWebProfileConfig` | 5 | `mobileNavFile` | **NO** — [B24] §24.6 documents `BMobileBogConverter` for `web:WebProfileConfig` + 4 legacy `mobile:*` theme types, NOT `web:MobileWebProfileConfig` specifically | `grep` for `mobileNavFile` → **0 hits**; all 5 real instances (`file.xml`, `web_MobileWebProfileConfig` elements) carry `typeSpec`/`selectedHxTheme`/`webNavFile`/`hxWbViews` — no `mobileNavFile` | Uncovered orphan CLASS; not triggered by this station's real data |
| `fox:FoxService` | 1 | `foxsCert` | **NO** — `fox` does not appear anywhere in [B24]'s 58-type catalog or this session's re-check | **Yes** — `<p n="foxsCert" f="rh1" t="b:String" v="default"/>` at `file.xml:339` — a REAL literal value, WITH an explicit `t=` attribute | **The one genuine, uncovered, actually-triggered orphan in this sample** — per §31.5's `t=`-present branch, this resurrects as a DYNAMIC `foxsCert` property on the loaded `BFoxService`, value `"default"` preserved, non-fatal, no warning logged |

**Headline finding**: of PANCCADIA's 3,545 sampled typed elements, exactly **ONE real orphan-slot event**
would occur on an `n5mig` migration as currently cataloged — `fox:FoxService.foxsCert` — and per §31.5's
traced decoder behavior, even that event is **non-fatal**: the station still loads, the value survives as a
dynamic property instead of a frozen one. Every other removed-property case in this sample is either
converter-covered (`BacnetDevice`, `BacnetIpLinkLayer`, `WebService`, `JettyWebServer`) or never triggered by
this station's actual data (`ProgramService.compactProfile`, `HistoryConfig.historyName`,
`MobileWebProfileConfig.mobileNavFile` — all absent because the real instances never set a non-default
value). `[INFER]`: this last point is a property of THIS station's specific configuration, not a structural
guarantee — a DIFFERENT N4 4.15 station that DID set a custom `historyName` or `mobileNavFile` would hit the
no-`t=`-attribute path (if the encoder wrote a bare value-only element) or the `t=`-present resurrection path
(if it wrote a typed element) — §31.5 already shows BOTH outcomes are non-fatal, so the structural conclusion
("removed-but-unconverted slots don't break a load") holds regardless, even though PANCCADIA specifically
happens not to exercise most of them.

## 31.7 — Answering B24-G6 directly: PANCCADIA's `kitControl`/`tagdictionary`/`nrio` pass-through objects load byte-identical `[CERT]`

The three categories [B24] §24.6 flagged as having no registered converter:

- **`kitControl` (100 objects, 11 types)**: `Multiply`, `Subtract`, `Or`, `Equal`, `And`, `Divide`, `Add`
  (own-declared-property CLEAN or inherit cleanly from `BQuadMath`/`BQuadLogic`/`BComparison`/`BBinaryMath`,
  all re-verified zero-delta this session, §31.3); `OneShot`/`BooleanDelay` (added-only:
  `lastInput`/`ticket`); `BooleanSelect` (inherits `BMuxSwitch.facets`, zero-delta) `Not` (inherits
  `BLogic.nullOnInactive`/`propagateFlags`, zero-delta). **All 100 objects: CLEAN or added-only. Zero
  removed slots.**
- **`tagdictionary` (147 objects in the corrected census, §31.1; [B24]'s 105 undercounted the double-quoted
  leaf properties), 32 types**: every type checked (`IsTypeCondition`, `SimpleTagInfo`, `TagRule`,
  `TagInfoList`, `TagGroupInfoList`, `RelationInfoList`, the 7 relation types, etc.) is CLEAN at either the
  own-declared or inherited-parent level (`BInfoList`, `BTagRuleCondition`, `BRelationInfo` all zero-delta,
  §31.3). The ONE exception, `QudtUnitTag`, is version-gap-unresolved (§31.4a) — type/class fully present in
  N5, slot-shape unconfirmed against a matching N4 4.15 baseline. **146 of 147 objects: CLEAN. 1 object
  (0.7%): unresolved but type-resolvable.**
- **`nrio` (115 objects, 12 types)**: `NrioVoltageInputProxyExt`, `LinearCalibrationExt`,
  `NrioRelayOutputProxyExt`, all 5 `Nrio34*` types, `OutputDefaultValues`, `OutputFailsafeConfig`,
  `NrioNetwork` — every one CLEAN, own-declared or inherited (`BNrio16Points`, `BNrio16WriteProxyExt`,
  `BNrio34SecStatus` parents all zero-delta). **All 115 objects: CLEAN.**

`[CERT]` per-type figures, `/tmp/claude-1000/n5b31/slot_diff_results2.json`. **This directly answers B24-G6**:
the absence of a registered converter for these three categories is not a migration RISK — it is
CORRECT, because the frozen-slot shape needs no conversion. `n5mig`'s converter catalog ([B24] §24.2) targets
exactly the modules that changed shape between N4 and N5 (bacnet property removals, web/jetty/program
renames, cloudLink/bacnetAws/opcua restructuring, etc.); `kitControl`/`tagdictionary`/`nrio` were correctly
left out of that catalog because nothing needed converting.

## 31.8 — Self-verification

**Marker tally (mechanical, `grep -o '\[CERT\]' niagara5-block31.md | wc -l` / same for `[INFER]`, run this
session):** `[CERT]` **26** · `[INFER]` **9**. Ratio `[INFER]`/`[CERT]` ≈ **0.35** — moderate, consistent
with a `mixed`-declared block whose evidence-gathering sections (§31.1-§31.3, §31.5) are tag-dense `[CERT]`
and whose cross-referencing sections (§31.4a, §31.6, §31.7's closing paragraph) draw `[INFER]` conclusions
across three independent artifacts (N4 decompile, N5 decompile, PANCCADIA's real bog bytes) — exactly the
declared `mixed` trigger. As with [B24] §24.7, the tag count UNDERSTATES evidence density: §31.4's table
carries 8 individually-cited rows and §31.6's table 8 more, each under one section-header tag. No
`verify-block.sh`/toolbelt exists in this corpus (same as [B14]/[B24]'s precedent, disclosed rather than
hand-rounded).

**Token check (spot-re-verified this session):** `ValueDocDecoder.java:392` (`parent.getSlot(name)`), `:1145-
1151` (no-`t=` warn-and-skip), `:500` (`parent.asComponent().add(...)` dynamic-resurrection call), `:1162-1164`
(`module.hasType(tname)` type resolution); `BComponent.java:428` (`add(String,BValue,int,BFacets,Context)`
signature, `grep -c` = 1 match); `BBacnetBogConverter.java:207-208` (`udpPort` removal, re-grepped);
`BProgramServiceConverter.java:30-38` (`allowProgramRuntimeExec`-only removal, full file re-read, confirmed
`compactProfile` string does NOT appear anywhere in the file); `BHistoryConfig.java:87` (`historyName` N4
default `""`); `file.xml:339` (`foxsCert` literal), `:4433-4436` (`udpPort`/`BacnetIpServerPort` literal
context); `bacnet-rt/vineflower/META-INF/module.xml:2` (`vendorVersion="4.14.0.162"`). `grep -rl "class
BBacnetIpServerPort|BBacnetNetworkNumberQuality|BBacnetMstpPortDescriptor|BBacnetNetworkPortPendingChanges|
BQudtUnitTag"` over the full N4 `organized/` tree → 0 hits (re-run at write time, confirms §31.4a). Total:
~18 distinct load-bearing tokens spot-checked, covering every distinct claim class in the block — not every
one of the 288 per-type diff rows individually (each row's evidence is the direct output of the deterministic
script in `/tmp/claude-1000/n5b31/`, re-runnable, not independently hand-verified per row).

**Artifacts:** block file created at `/home/cristian/niagara5-research/niagara5-block31.md`. Scratch scripts
and JSON outputs at `/tmp/claude-1000/n5b31/` (`file.xml`, `type_counts.json`, `module_counts.json`,
`module_type_check.json`, `slot_diff_results2.json`) — NOT persisted to `organized/`, per [B24]'s precedent
for read-only research scratch. `CATALOG.md`/`INDEX.md`/`RESEARCH-STATE.md` NOT regenerated (read-only task,
per [B14]/[B24]'s precedent).

## 31.9 — Connections

- **[B24]** — this block directly closes **B24-G6** (posed by the task: "will pass-through objects actually
  LOAD in N5?"). It also CORRECTS §24.6's typed-element count (1,389 → 3,545, a quoting-regex undercount,
  §31.1) and its custom-module object count (34 → 44, same cause). §24.2's converter catalog is reused, not
  re-derived, as the authority for "which types have a registered converter" (§31.6's table cites it
  directly for `BacnetDevice`/`BacnetIpLinkLayer`/`WebService`/`JettyWebServer`).
- **[B14]** — §31.2's module/type registry findings mechanically confirm [B14] §14.5's `BModuleRemovalConverter`
  fallback theory (custom-module objects silently stripped) and §14.6's `BTypeSpecConverter` generic-rename
  mechanism (type NAME stability survives the `javax.baja.*`→`niagara.*` class-package rename, §31.2).
- **[B10]** — the corrected 44-object custom-module count (§31.2) updates the exact number [B10]'s
  module-porting checklist CHK-1..CHK-14 needs to reinstall/re-sign before migration; the deployment-order
  constraint itself is unchanged from [B14] §14.10.
- **`niagara-research`'s bacnet/tagdictionary corpus** — §31.4a's 5 version-gap-unresolved types are a
  direct signal that that corpus's `bacnet-rt`/`tagdictionary-rt` decompile (4.14.0.162) is now stale
  relative to PANCCADIA's real 4.15 station; a fresh 4.15 decompile of just these two modules would close
  B31-G1 without redoing this block's other 283 type checks.

## 31.10 — Child gaps

- **B31-G1** — the 5 version-gap-unresolved types (`bacnet:BacnetNetworkNumberQuality`,
  `bacnet:BacnetIpServerPort`, `bacnet:BacnetMstpPortDescriptor`, `bacnet:BacnetNetworkPortPendingChanges`,
  `tagdictionary:QudtUnitTag`, §31.4a) need an N4 **4.15** decompile of `bacnet`/`tagdictionary` (not the
  4.14.0.162 this session had available) to slot-diff against N5 the same way the other 283 types were.
  Type+class presence in N5 is already confirmed `[CERT]` — only the exact frozen-slot match is open, and
  §31.5's decoder trace already shows any mismatch found would be non-fatal regardless.
- **B31-G2 (requires-execution, inherits B14-G1/B24-G1)** — this entire block is a STATIC trace of
  `ValueDocDecoder`'s control flow (§31.5) plus a static slot-diff (§31.3-§31.4), not an observed `n5mig`
  run. Running `n5mig -premigrate` (or a full migration) against PANCCADIA's real backup would directly
  observe whether `fox:FoxService.foxsCert` (§31.6's one real orphan case) actually resurfaces as a dynamic
  property as predicted, and would surface the premigrate HTML report's own accounting for cross-check.
- **B31-G3** — §31.6's converter-coverage claims for `web:WebService`, `jetty:JettyWebServer`, and
  `bacnet:BacnetDevice`/`BacnetIpLinkLayer` are inherited from [B24] §24.2's reading of those converters
  (re-confirmed for `BacnetIpLinkLayer`/`ProgramService` this session via direct re-grep, §31.8's token
  check) but `BWebBogConverter`'s and `BJettyQoSFilterMigrator`'s exact property-removal lists were NOT
  independently re-read line-by-line THIS session — only cross-checked at the "does the slot-diff match the
  converter's documented behavior" level.
- **B31-G4** — PANCCADIA's points/histories/alarms/schedule bog files remain outside the poc copy (inherits
  [B24] B24-G2). The 23 `HistoryConfig` objects checked here live in `config.bog` (service-level history
  config), not the per-point history extensions that would live in a points bog — `schedule:*` typespec
  compatibility (explicitly requested by this task) could not be checked AT ALL, since zero `schedule:*`
  elements exist anywhere in `config.bog` (`[CERT]` re-confirmed this session: `grep -c "schedule" file.xml`
  finds no `t=` typespec matches under that prefix, and `schedule` never appears in the §31.1 module-alias
  map).
- **B31-G5** — the two `box:HistoryChannel`/`box:AlarmChannel` parent-class swaps (`BBoxChannel`→
  `BWrapperBoxChannel`, §31.3) were found as a side effect of the inheritance-walk pass but not investigated
  further — WHY the box-channel hierarchy was restructured (a wrapper/decorator pattern introduced in N5?)
  is unexplored; both objects have only 1 instance each in this sample so the practical stakes are low, but
  the architectural question is open.
