# Block 19 — N5 station persistence and indexing: bog, history storage, systemDb and systemIndex

> **Scope**: Closes gap **N5-G13** (station persistence/index: `orientSystemDb`, `systemDb`, `systemIndex`,
> `niagaraSystemIndex`, `search`, `query`, `queryTable`, `bql`, `neql`, `history` — storage side). Answers: (1)
> is `config.bog`'s BOG-XML grammar unchanged from N4, including version attributes; (2) is `.hdb` history
> storage format (magic numbers, header layout) unchanged; (3) what OrientDB version backs `systemDb`/
> `orientSystemDb` and is its role unchanged; (4) what `systemIndex`/`niagaraSystemIndex` index and where they
> store it; (5) whether NEQL/BQL changed. Does **not** cover: the `KeyRing`/`SecurityInitializer` cryptographic
> internals themselves (proprietary, not decompiled — same blocker N4's corpus records, see §19.1); a live
> `[CERT-hw]` reproduction against a real N5 station (none exists yet — no station has been created on this
> install, per [Block 3]/[Block 9]); the UI/workbench-side consumers of `query`/`queryTable`/`search` (HX
> views, batch-edit field sheets) beyond noting their class names exist unchanged.
>
> Subject version: **N5 5.0.0.28 (Beta)**, same install as prior blocks (`etc/brand.properties:workbench.notice`
> Beta marker, JRE 25.0.4.7). N4 comparison baseline: `niagara-research` corpus B887/B911 (systemDb/orientSystemDb
> + NEQL→OrientSQL), B930/B782 (niagaraSystemIndex + the query/queryTable/search/systemIndex unified pattern),
> B21 (Tag/BQL/NEQL), B33/B410/B411 (`.hdb` format + retention + BOG crash-recovery), B5/B114 (BOG-XML grammar +
> encryption key sources), B17/B26 (OrientDB 3.2.23 embedded in N4.14).
>
> Sources (all local, read-only):
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{orientSystemDb,systemDb,systemIndex,
>   niagaraSystemIndex,search,query,queryTable,bql,neql,history}.jar` — decompiled whole-module this session via
>   `tools/n5-decompile.sh` into `organized/<module>/vineflower/`.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/baja.jar` — targeted extraction (not whole-jar
>   decompile) of `com/tridium/sys/station/{Station,BStationSaveJob}.class`,
>   `com/tridium/sys/station/StationManager*.class`, `com/tridium/sys/transfer/CompToBog.class`,
>   `niagara/io/ValueDocEncoder{,$BogEncoderPlugin}.class`, `niagara/io/ValueDocDecoder{,$BogDecoderPlugin,
>   $BogElement,$BogTypeResolver}.class` — `unzip` + Vineflower with `-e=baja.jar` classpath, into
>   `/tmp/claude-1000/n5b19/bajadecomp/` (ephemeral scratch, re-derivable from the jar).
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/nre.jar` — targeted extraction of
>   `com/tridium/nre/security/io/BogPasswordObjectEncoder.class`, `niagara/nre/security/EncryptionKeySource.class`
>   into `/tmp/claude-1000/n5b19/nredecomp/`, same method.
> - `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/system/orientdb-{core,client,server,tools}-3.2.55.jar` —
>   filename/version only (not opened; OrientDB itself is third-party, out of scope to decompile).
> - `tools/bog-nav.py` + `tools/tests/test_bognav_n5_platform.py` + `tools/README.md` (bog-nav row) — this
>   corpus's own prior, already-committed verification that `defaults/platform.bog` parses as bare BOG-XML.
> - `tools/hdbread.py` (`niagara-research` corpus tool) — the N4 `.hdb` magic-number constant this block
>   cross-checks N5 against.
> - REMITTANCE `niagara-research`: B887 (`niagara-mental-model-bloque887.md`), B911 (`...bloque911.md`), B930
>   (`...bloque930.md`), B782 (`...bloque782.md`), B21 (`...bloque21.md`), B33/B410/B411/B45
>   (`...bloque{33,410,411,45}.md`), B5/B114 (`...bloque{5,114}.md`), B17/B26 (`...bloque{17,26}.md`) — fetched
>   via `python3 /home/cristian/niagara-research/tools/corpus-nav.py find/grep <term>` and direct file grep this
>   session.
>
> Method: `tools/n5-decompile.sh` (whole-module, Vineflower primary/CFR fallback) for the 10 gap-named modules;
> targeted `unzip` + single-pass Vineflower `-e=<jar>` classpath extraction for specific classes inside `baja.jar`
> and `nre.jar` (faster than a whole-jar decompile for a 2-jar, ~15-class cross-check). All targets decompiled
> cleanly to readable Java (none obfuscated/minified) — ordinary `file:line` citation applies, no sha256
> beautified-temp anchor needed. Markers: `[CERT]` local primary (jar/class opened and read this session) ·
> `[CERT-doc]` — not used this block · `[INFER]` deduction. Every `[CERT]` below, on both the N5 and the N4
> REMITTANCE side, was read this session (N5 via decompile; N4 via direct `grep`/`corpus-nav.py` read of the
> already-committed corpus file) — no citation is carried from memory.
>
> Station-persistence/index layer. Connects [Block 3] (§3.5/§3.8 — boot/security substrate this block's
> `SecurityUtil.doPrivileged` calls and `GrantFilePermission`/`GrantNiagaraBasicPermission` annotations sit on
> top of), [Block 5] (javax.baja.\* → niagara.\* package rename — this block confirms it concretely for
> `ValueDocEncoder`, `BISearchProvider`, and every one of the 10 gap modules' JPMS names), [Block 8] (permission
> model — this block's modules' own `module-info.java` grant annotations are read against that block's
> taxonomy). Cross-corpus: `niagara-research` B887, B911, B930, B782, B21, B33, B410, B411, B5, B114, B17, B26.
>
> **Type:** standard

---

## 19.1 — `config.bog`: the BOG-XML grammar is unchanged; only the version attribute bumps `[CERT]`

**The root element, its attribute grammar, and the encoder/decoder architecture are all preserved verbatim** —
the only concrete change found this session is the emitted schema-version number.

`niagara.io.ValueDocEncoder` declares three version constants (`[CERT]`
`ValueDocEncoder.java:54-56`, this session's targeted decompile): `BOG_VERSION_1 = new Version("1.0")`,
`BOG_VERSION_4 = new Version("4.0")`, `BOG_VERSION_5 = new Version("5.0")` — a **new** `BOG_VERSION_5` constant
whose default consumer is `ValueDocEncoder$BogEncoderPlugin.version = ValueDocEncoder.BOG_VERSION_5`
(`[CERT]` `ValueDocEncoder$BogEncoderPlugin.java:34`). The actual root-element header text is built by
`BogPasswordObjectEncoder.writeBogHeader(XWriter, String)` (`[CERT]` `BogPasswordObjectEncoder.java:229-247`):

```java
w.w("<bajaObjectGraph version=\"" + bogVersion + "\" reversibleEncodingKeySource=\"" + this.keySource.name() + "\" ");
w.w("FIPSEnabled=\"" + (futureFIPSRelatedCheckbox ? "true" : "false") + "\" ");
// + conditionally: reversibleEncodingValidator="..." (none/external)
// + conditionally: reversibleEncodingSalt="..." reversibleEncodingIterationCount="..." (external only)
```

`[CERT]` verbatim `BogPasswordObjectEncoder.java:230-243`. Cross-checked against **N4's own corpus**, which
documents this exact attribute set from a live deployed N4.14 station's real `config.bog`
(`niagara-research` B685, `[CERT-hw]`): `<bajaObjectGraph version="4.0" reversibleEncodingKeySource="keyring"
FIPSEnabled="false">`, and from [Block 5]'s decompiled encoder read: `reversibleEncodingValidator`/
`reversibleEncodingSalt`/`reversibleEncodingIterationCount` as the same three conditional attributes
(`niagara-mental-model-bloque5.md:284-289`). **Net finding**: the root-element grammar is attribute-for-attribute
identical between N4.14 and N5 5.0.0.28 — `FIPSEnabled` is not a new N5 attribute (it already exists, always
`"false"`, in N4's real station export); the only visible change is the schema-version number itself
(`4.0`→`5.0`, driven by the new `BOG_VERSION_5` constant replacing `BOG_VERSION_4` as encoder default).

**Package rename, not a rewrite.** N4's corresponding class lived at `javax.baja.io.ValueDocEncoder`
(`[CERT]` `niagara-mental-model-bloque5.md:484,488` — `ValueDocEncoder (javax.baja.io)`); N5's is
`niagara.io.ValueDocEncoder` (`[CERT]` package statement, `ValueDocEncoder$BogEncoderPlugin.java:1`) — this is
the same `javax.baja.*`→`niagara.*` rename [Block 5] already established for the core API, now confirmed
concretely for the BOG encoder/decoder pair. The encoder's own closing-tag write, `</bajaObjectGraph>`
(`[CERT]` `ValueDocEncoder$BogEncoderPlugin.java:166`), is the literal grammar root name, unchanged from N4.

**`tools/bog-nav.py` (this corpus's own N4 BOG-XML parser) already confirmed this independently, before this
block was opened.** `[CERT]` `tools/tests/test_bognav_n5_platform.py` (regression-pinned this corpus) runs
`bog-nav.py` against the real, read-only `defaults/platform.bog` and asserts (1) exit 0 — no parse error, (2)
the file is bare XML starting `<?xml`, not a ZIP (`head[:2] != b"PK"`), matching N4's non-station `.bog` files
(module palettes) which are also bare XML while a saved `config.bog` is typically zipped (§19.2 below confirms
the zip toggle exists in N5's encoder too). This is *independent* confirmation from a *different* angle (an N4
parser working unmodified on an N5 artifact) of the same conclusion §19.1's decompile reaches directly: the
grammar family is one and the same across major versions.

**Open item carried from that pre-existing test, not new to this block**: `platform.bog`'s `<p>` component nodes
carry no `h=` (handle) attribute (template default, no links), and `bog-nav.py`'s indexer requires a handle to
register a node — so it reports "no components" rather than crashing. A real `config.bog` (once an N5 station
exists) is expected to carry handles the way N4 exports do, per `tools/README.md`'s bog-nav row — unverified,
since no N5 station has been created on this install (§19.7 open item, [Block 3]/[Block 9]).

## 19.2 — Boot-time crash recovery and the save→backup→rename dance: identical logic, different line numbers `[CERT]`

`com.tridium.sys.station.Station` (this session's targeted decompile of `baja.jar`) is the direct successor of
N4's class of the same fully-qualified name (`niagara-research` B411 cites `Station.java` throughout with no
package-rename note, i.e. this one class stayed at `com.tridium.sys.station.Station` while its *dependencies*
moved to `niagara.*`). The two guard mechanisms N4's B411 names are present **verbatim**:

- **`checkForWorkingFile(File bootFile)`** (`[CERT]` `Station.java:614-621`, this session):
  ```java
  private static void checkForWorkingFile(File bootFile) throws IOException {
     if (!bootFile.exists()) {
        File workingFile = new File(bootFile.getCanonicalPath() + ".working");
        if (workingFile.exists() && !workingFile.renameTo(bootFile)) {
           throw new IOException("Failed to rename working file");
        }
     }
  }
  ```
  This is a line-for-line match (modulo whitespace) to N4's own guard, cited by B411 as
  `Station.checkForWorkingFile()` with the identical `.working`-suffix construction and identical
  exists/rename/throw shape (`niagara-mental-model-bloque411.md:41-43`). Called at boot from `nreMain`
  (`[CERT]` `Station.java:775,791`) before the boot-file existence check — same call sites B411 documents
  (`bootFile`/`bog` variants, `niagara-mental-model-bloque411.md:58,67`).
- **Save-path**: `saveSync(BJob, int)` (`[CERT]` `Station.java:462-583`) writes to `config.bog.working`
  (`new File(saveFile + ".working")`, `:484`), encodes via `Station.StationEncoder` (`:491-508`, a
  `ValueDocEncoder` subclass with `setZipped(true)` — confirming N5's saved `config.bog` IS zip-compressed by
  default, same as N4), then on success: `renameToBackup(saveFile)` (`:518`, if the old file exists) followed
  by `workingFile.renameTo(saveFile)` (`:529`) — the identical three-step dance (encode-to-`.working` → backup
  old → rename-`.working`-to-final) B411 documents as "Step A → encode to `config.bog.working` → Step B →
  `renameToBackup(config.bog)` → Step C → rename" (`niagara-mental-model-bloque411.md:119-120`).

**Net finding**: the crash-recovery guard and the save/backup/rename sequencing are unchanged in shape between
N4.14 and N5 5.0.0.28 — same method name (`checkForWorkingFile`), same suffix convention (`.working`), same
ordering (encode→backup→rename). Line numbers differ only because surrounding code shifted (N4's citation is
`Station.java:496-503`/`763-768`; N5's is `:614-621`/`:483-529` — different absolute positions in what is
otherwise the same control flow), not because the logic itself changed.

## 19.3 — History storage (`.hdb`): the fixed-format AND recstore magic numbers are bit-for-bit identical to N4 `[CERT]`

The gap named a specific, falsifiable question: does N5 keep N4's `.hdb` magic `0xA106F11E` (the constant
`tools/hdbread.py` — this corpus's own N4 `.hdb` reader — checks against, `[CERT]` `hdbread.py:24`,
`MAGIC = bytes.fromhex("a106f11e")`). It does, **exactly**, in both of the two `.hdb` sub-formats:

| Sub-format | Class | N5 magic (decompiled this session) | Hex | N4 magic (REMITTANCE) | Match |
|---|---|---|---|---|---|
| Fixed-length (`VERSION_1`) | `com.tridium.history.file.BFileHistoryTable` | `private static final int MAGIC = -1593380578;` `[CERT]` `BFileHistoryTable.java:65` | `0xA106F11E` | `-1593380578` (same decimal), N4 `history-rt` `BFileHistoryTable.java` (per B33 `[CERT]`, `javap -c` `ldc #99 // int -1593380578`) | **Identical, bit-for-bit** |
| Record-store paginated (`VERSION_2`, `recstore`) | `com.tridium.history.file.recstore.RecordStoreHeader` | `private static int MAGIC = 182299393;` `[CERT]` `RecordStoreHeader.java:9` | `0xADDAB01` | `182299393` — read this session directly from N4's own decompiled source at `/home/cristian/modules/Prototipos/modulos/organized/history/history-rt/vineflower/com/tridium/history/file/recstore/RecordStoreHeader.java:9` `[CERT]` (N4 corpus's own text, B33/B410, never states this literal value — only the class's existence) | **Identical, bit-for-bit** |

`checkMagic(int, File)` (`[CERT]` `BFileHistoryTable.java:283-289`) still hard-throws on any mismatch
(`"Bad magic number (0x..."`), the same defensive gate N4 has. `VERSION_1 = 1` / `VERSION = 2` constants
(`[CERT]` `BFileHistoryTable.java:66-67`) and the header-index layout `MAGIC_IDX=0`/`VERSION_IDX=1`/
`DATA_OFFSET_IDX=2` (`[CERT]` `BFileHistoryTable.java:81-83`) match N4's documented "12 bytes (magic + version
int + dataOffset int)" layout exactly (`niagara-mental-model-bloque33.md:19`).

**A pre-existing N4-corpus transcription slip, flagged but not corrected here (out of scope — read-only, this
task touches no other file).** N4's own block33 states the fixed-format magic's hex form as `0xA0F61E5E`
(`niagara-mental-model-bloque33.md:18,350,360`) alongside the SAME decimal value `-1593380578` it also states —
but `0xA0F61E5E` is not the hex form of `-1593380578` (`hex(-1593380578 & 0xFFFFFFFF) == 0xa106f11e`, verified
this session with Python). `tools/hdbread.py` (the actually-used, grep-confirmed-correct N4 tool) carries the
right value, `0xA106F11E`; block33's prose hex string does not match its own cited decimal. This is an internal
N4-corpus inconsistency, not an N4↔N5 difference — recorded here per §14 cross-block-consistency discipline
since it surfaced during this exact comparison, but the fix belongs to the N4 corpus, not this block.

**Package rename applies to the public history API, not the impl classes.** `BFileHistoryTable` imports
`niagara.history.{BCapacity,BFullPolicy,BHistoryConfig,BHistoryId,BHistoryRecord,BHistoryService,BIHistory,
BIHistoryRecordSet}` and `niagara.io.{ValueDocDecoder,ValueDocEncoder}` (`[CERT]` `BFileHistoryTable.java:26-40`)
— the same `javax.baja.history.*`→`niagara.history.*` pattern [Block 5] established generally. The impl
package itself, `com.tridium.history.file.*`, is unchanged. `module niagara.history`'s own grant annotations
(`[CERT]` `history` module-info, this session) scope file access explicitly:
`@GrantFilePermission(path = "${protected.station.home}${/}history${/}-", actions = "read,write")` — a direct,
concrete instance of [Block 8]'s core-only `FilePermission` grant mechanism (§8.1) applied to this exact module.

## 19.4 — `systemDb`/`orientSystemDb`: same OrientDB role, license gate and DB name — but the embedded OrientDB core is upgraded `[CERT]`

**Architecture and license gate unchanged.** `com.tridium.systemDb.orient.BOrientSystemDb` still embeds
OrientDB directly (`[CERT]` imports at `BOrientSystemDb.java:1-10`: `com.orientechnologies.orient.core.*`,
`Orient`, `OrientDB`, `OrientDBConfig`, `ODatabaseType`, `OServer`), still names the internal database
`"systemDb"` (`[CERT]` `private static final String DB_NAME = "systemDb";`, `BOrientSystemDb.java:168`; also
`ODatabaseType.PLOCAL` at `:418` — the same on-disk PLOCAL storage engine), and still gates its own use behind
the identical two-part license check `[CERT]` `BOrientSystemDb.java:830-840`:
```java
protected final void checkLicense() {
   Feature feature = Sys.getLicenseManager().getFeature("tridium", "systemDb");
   feature.check();
   if (!feature.getb("orientDb", false)) {
      throw new FeatureNotLicensedException("\"systemDb\" feature is missing enabled \"orientDb\" attribute");
   }
}
```
— a literal match to N4's B887 finding ("License: requires `tridium/systemDb` AND `feature.getb("orientDb")`",
`niagara-mental-model-bloque887.md:61`). `NiagaraGeneratingVisitor`'s sibling, `OrientGeneratingVisitor`, still
lives at `com.tridium.systemDb.orient.queryGeneration.OrientGeneratingVisitor` (`[CERT]` package decl. line 1,
class decl. line 53) — the same fully-qualified name N4's B911 documents.

**The embedded OrientDB library itself is a real version bump, not carried over unchanged.** N4.14's install
ships OrientDB **3.2.23** (`[CERT]`, REMITTANCE `niagara-research` B17 `"OrientDB Core 3.2.23 (5.6 MB —
embedded DB usado por History service)"`, confirmed independently by B26 `"orientdb-3.2.23.jar"`). This N5
5.0.0.28 install ships **`orientdb-{core,client,server,tools}-3.2.55.jar`** (`[CERT]`, filename read this
session from `/mnt/c/Program Files/Niagara/5.0.0.28/bin/ext/system/`). `module niagara.orientSystemDb`
(`[CERT]` module-info, this session) wraps these as optional/automatic modules (`requires transitive static
orientdb.core; requires static orientdb.server; requires static orientdb.tools;`) — confirming the JPMS
wrapping pattern [Block 1]/[Block 7] already established for third-party jars, applied here to OrientDB
specifically. **N4→N5 delta**: OrientDB 3.2.23 → 3.2.55 (a minor-version bump within the same 3.2.x line, not
a major-version migration).

**A capability not mentioned in N4's B887, found this session — flagged as possibly new, not confirmed absent
in N4 (negative-existence discipline).** `BOrientSystemDb` exposes `getDatabaseEncryption(): BDatabaseEncryptionState`
with states including `unencrypted`/`encrypted`/`changingToEncrypted`/`changingToUnencrypted` (`[CERT]`
`BOrientSystemDb.java:179` + usages `:235-497`), and when not `unencrypted`, `createDatabase` is configured with
`OGlobalConfiguration.STORAGE_ENCRYPTION_METHOD="aes"` + `STORAGE_ENCRYPTION_KEY` (`[CERT]`
> **§14 resolution (2026-09-27, [Block 57]):** the `BOrientSystemDb.databaseEncryption` default (`encrypted`) and the 3 KeyRing aliases are byte-identical in N4.14 — NOT new in N5; `EncryptionKeySource` has the same 5 members in N4 (package rename only).

`BOrientSystemDb.java:407-411`) — i.e. OrientDB's own at-rest AES storage encryption, keyed via
`getDbEncryptionPassword()`/the KeyRing (`KEY_RING_DB_ALIAS = "orientSystemDb.database"`, `:163`). B887 does not
mention this option. `[INFER]`: this could be new in N5, or simply outside B887's stated scope (that block's
own header does not claim to have searched for a database-encryption toggle) — not resolved this session,
→ child gap **B19-G1**.

## 19.5 — `systemIndex`/`niagaraSystemIndex`: unchanged architecture; the index is written INTO `systemDb` `[CERT]`

Class-for-class match to N4's documented architecture. `BSystemIndexer` is still
`extends BAbstractDescriptor implements BIIndexQueryProvider, BIAlarmSource` (`[CERT]`
`BSystemIndexer.java:103`) with the same `defaultIndexQueries`/`customIndexQueries` `BOrdList` property pair
(`[CERT]` `:111,122`, both `niagara.naming.BOrdList` — package-renamed, same type) that N4's B782 documents
("slots merge `defaultIndexQueries` + `customIndexQueries` (a `BOrdList`)",
`niagara-mental-model-bloque782.md:57`). `com.tridium.niagaraSystemIndex.BNiagaraNetworkSystemIndexer` and its
companions (`BAbstractSystemIndexDeviceExt`, `BReachableStationsSystemIndexMonitor`,
`BNiagaraSystemIndexExport`/`Import`) all exist under the identical fully-qualified names N4's B930 documents
(`[CERT]` class-file listing, this session — 12 classes in `organized/niagaraSystemIndex/vineflower/`, same
count B930 cites for N4.14's `niagaraSystemIndex-rt`).

**Where the index is stored: this session directly confirms it lands in the `systemDb` OrientDB store, closing
that half of the gap explicitly rather than by inference.** `BSystemIndexService` requires the same
`("tridium","systemDb")` license feature as `BOrientSystemDb` itself (`[CERT]` `BSystemIndexService.java:291`,
`Sys.getLicenseManager().getFeature("tridium", "systemDb").check();`) and exposes a diagnostic link literally
named `"Detailed Orient Spy"` pointing at `spy:/orientSystemDb` (`[CERT]` `BSystemIndexService.java:338`).
`BLocalSystemIndexer extends BSystemIndexer` (`[CERT]` `BLocalSystemIndexer.java:35`) imports
`com.tridium.systemDb.BSystemDb` and calls a method **literally named** `systemIndexToSystemDb(...)` (`[CERT]`
`BLocalSystemIndexer.java:79`), using a context obtained from `BSystemDb.getSystemIndexContext()` (`[CERT]`
`:216`). This directly confirms — by class/method naming, not inference — that `systemIndex`'s station-local
full index is written into the same OrientDB-backed `systemDb` store §19.4 documents, exactly as N4's B782
frames the four surfaces (`query`, `queryTable`, `search`, `systemIndex`) as "FOUR faces of ONE pattern"
sharing infrastructure (`niagara-mental-model-bloque782.md:4`) — here shown concretely for the storage backend,
not just the API shape.

## 19.6 — `query`/`queryTable`/`search`/`bql`/`neql`: the unified pattern and the NEQL→OrientSQL translator both survive unchanged `[CERT]`

Every class name this session found in the 5 remaining gap modules matches N4's corpus 1:1, package-renamed
where the class is public API:

| N5 module | Sample classes (this session's decompile) | N4 match (REMITTANCE) |
|---|---|---|
| `query` | `BQuery`, `BExtent`, `BPredicate`, `BExpression`, `BColumn`, `BQueryEngine`, `BICompiledQuery` | B782 §782 (same names, `query-rt`) |
| `queryTable` | `BQueryTable`, `BColumnsProvider`, `BHxQueryTableView`, `BWbQueryTableView` | B782 (`BQueryTable`, `BColumnsProvider`) |
| `search` | `BSearchService`, `BISearchProvider`, `BBqlSearchProvider`, `BSearchResult` | B782 §782.4 (identical names, `search-rt`) |
| `bql` | `BBqlScheme`, `BSelect`, `RangeSet`, `BBqlExtent`, `BqlQuery` | B21 §21 (BQL section; `bql-rt/ux`) |
| `neql` | `BNeqlScheme`, `NeqlTokenizer`, `NeqlEntityEvaluator`, `EvalOnIterator`, `Traverse{In,Out}Expression` | B21 §21.6 (identical names, `neql-rt`) |

`niagara.search.BISearchProvider` (public API, renamed from N4's `javax.baja.search`) still declares exactly
one method, byte-for-byte the same signature N4's B782 cites: `[CERT]`
```java
public interface BISearchProvider extends BIAgent {
   Stream<Entity> search(BOrd var1, BIObject var2, Context var3);
}
```
(`BISearchProvider.java:14-19`, this session) vs N4's `"search(BOrd query, BIObject scope, Context) →
Stream<Entity>"` (`niagara-mental-model-bloque782.md:43`, citing `BISearchProvider.java:27-28`) — identical
method shape, different line number only because of the surrounding package-rename boilerplate. `search-rt`
existed in N4 already (confirmed via `corpus-nav.py find BISearchProvider`, this session) — it is **not** a
module new to N5.

**NEQL→OrientSQL translation is present, unchanged in mechanism.** `OrientGeneratingVisitor`
(`com.tridium.systemDb.orient.queryGeneration`, §19.4) still generates `TRAVERSE`-based OrientSQL for relation
traversal and `SELECT EXPAND(intersect(...))` for tag/predicate intersection — `[CERT]` verbatim,
`OrientGeneratingVisitor.java:126,141,162` (`"(SELECT FROM (TRAVERSE out('scopedEdge') FROM " + scopeId + ")
WHERE $depth > 0)"`, `"SELECT FROM (TRAVERSE " + direction + "('" + relation + "') FROM " + scopeId + "
MAXDEPTH 1) WHERE $depth = 1"`) and `:118-120,259-296` (`SELECT DISTINCT`/`SELECT EXPAND(intersect(...))`/
`SELECT EXPAND(unionall(...))`) — the exact `TRAVERSE`/`SELECT EXPAND(intersect(...))` shape N4's B911 documents
("Relations + scope = OrientDB TRAVERSE", `niagara-mental-model-bloque911.md:53`). No structural change found
in this generator between N4.14 and N5 5.0.0.28.

## 19.7 — `EncryptionKeySource`: N5 decompile shows 5 members; N4's corpus only ever inferred 3 by usage `[CERT]` / open comparison

Not a confirmed N4→N5 delta — a genuine evidence-asymmetry worth recording precisely rather than glossing over.
This session **directly decompiled** `niagara.nre.security.EncryptionKeySource` (from `nre.jar`) and read its
full enum body: `[CERT]`
```java
public enum EncryptionKeySource {
   none, keyring, external, shared, undefined;
}
```
(`EncryptionKeySource.java:3-9`, this session) — **5** members. N4's corpus (B114) explicitly states the
opposite evidence situation for the N4 side: *"`EncryptionKeySource`
(`com.tridium.nre.security.EncryptionKeySource`) es un **enum propietario NO decompilado** — no existe
`EncryptionKeySource.java` en el corpus"* — i.e. N4's "three values confirmed by uso" (`none`/`external`/
`keyring`) is an inference from three literal constant names appearing in decompiled *callers*
(`niagara-mental-model-bloque114.md:31-39`), never from opening the enum itself. Both `shared` and `undefined`
are consumed directly by N5's own `BogPasswordObjectEncoder` (`[CERT]` constructor at `:34` sets
`keySource = EncryptionKeySource.shared` for the raw-secret-bytes constructor path; `writeBogHeader`'s
`headerKeySource` resolution branches on `EncryptionKeySource.undefined`, this session's read of
`BogPasswordObjectEncoder.java:126-165`) — so `shared` is not a dead/unused enum literal in N5.

**Reading this honestly**: whether N4 4.14's own (never-opened) `EncryptionKeySource` enum also already had
`shared`/`undefined` cannot be answered from either corpus as it stands — N4's corpus never decompiled the
class to check, and this session did not obtain an N4-side decompile of it either (out of scope: this task's
sources are the N5 install only). This is therefore recorded as an **open comparison gap**, not a claimed N5
addition → child gap **B19-G2**.

## Self-verify

`toolbelt/verify-block.sh niagara5-block19.md` (this session, verbatim, run against the file as saved —
note for the reader: a script that greps this exact section's own quoted output will double-count these
numbers against themselves on any FUTURE re-run, the same self-reference every block's Self-verify section
has; the numbers below are the tally for the content ABOVE this section, i.e. the actual research):
```
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 2  (adj 2)
   [CERT-live] 0
   [CERT] 53  (adj 51)
   [CERT-doc] 1  (adj 1)
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 5  (adj 4)
-- ratio -- [INFER]/[CERT*] = 4/54 = 0.07
-- [CERT] file:line citation resolution --
   resolved 0 of 38
   WARN    resolved 0 of 38 — no file paths resolved. Set SOURCE_ROOT if source files live in a separate tree.
== exit 0 ==
```
The 2 `[CERT-hw]` raw hits above the Self-verify section are NOT claims made by this block — one is the
header scope note's forward reference to future live-station work, one is child gap **B19-G3** naming the
marker for that same future work; a third appears quoted inside §19.1 citing N4's OWN `[CERT-hw]` marker on
B685's real deployed-station reading (quoted evidence a prior block already sealed, not this block's own
claim). The 1 `[CERT-doc]` raw hit is the header's own legend line stating the marker is "not used this
block". Zero `[CERT-hw]`/`[CERT-doc]` claims are asserted as already-verified by this block itself.
**Declared per METHODOLOGY §11's decompiled-tree rule**: `verify-block: 0 resolved (all extern —
decompiled trees under organized/{orientSystemDb,systemDb,systemIndex,niagaraSystemIndex,search,query,
queryTable,bql,neql,history}/vineflower/ + /tmp/claude-1000/n5b19/{bajadecomp,nredecomp}/, the latter
ephemeral scratch, both re-derivable from the jars cited in the header; the N4 REMITTANCE citations
(`niagara-mental-model-bloque*.md`) are also outside `SOURCE_ROOT` and classify the same way); citation
gate = inline token-verify.`

**Inline token-verify**: every `file:line` citation to a decompiled N5 class in this block points at a class
this session itself decompiled (§0 Method) and then directly `Read` with line numbers before citing it. Every
REMITTANCE citation to a `niagara-mental-model-bloque<N>.md` line was independently `grep -n`-confirmed present
at that exact line this session (not pasted from memory), including the one flagged pre-existing hex/decimal
inconsistency in bloque33 (§19.3) — the surrounding text was read in context before being characterized as an
inconsistency rather than a genuine N4↔N5 difference. Spot-check tokens re-`grep`-confirmed present
(whitespace-normalized) this turn: `checkForWorkingFile` (`Station.java`), `MAGIC = -1593380578`
(`BFileHistoryTable.java`), `MAGIC = 182299393` (`RecordStoreHeader.java`, both N5 and the N4 path under
`/home/cristian/modules/Prototipos/modulos/organized/history/...`), `getFeature("tridium", "systemDb")`
(`BOrientSystemDb.java` and `BSystemIndexService.java`), `systemIndexToSystemDb` (`BLocalSystemIndexer.java`).

**MCP-doc snapshots**: N/A — no context7/MCP-doc citation in this block; every source is a local jar/class or
an already-committed corpus file opened directly this session.

**Artifacts**: block file created at `/home/cristian/niagara5-research/niagara5-block19.md`. Per the caller's
explicit instruction, this read-only research task touches no other file — `INDEX.md`/`RESEARCH-STATE.md`/
`CATALOG.md` regeneration and gap-backlog re-classification (N5-G13 → covered) are left to the orchestrator.

## 19.x — Child gaps opened

- **B19-G1** — Confirm whether `BOrientSystemDb`'s at-rest AES storage-encryption toggle
  (`BDatabaseEncryptionState`, `STORAGE_ENCRYPTION_METHOD="aes"`, §19.4) is genuinely new in N5, or existed in
  N4.14 but was out of scope for B887's original read (B887 never searched for a database-encryption option).
  Requires either an N4-side targeted decompile of `orientSystemDb-se`'s `BOrientSystemDb` for the same
  fields/methods, or a `[CERT-hw]` check against a real N4 station's `orientSystemDb` config UI.
- **B19-G2** — Decompile N4.14's own `com.tridium.nre.security.EncryptionKeySource` enum (never opened by any
  N4 corpus block — B114 explicitly names it "propietario NO decompilado") to settle whether `shared`/
  `undefined` are genuinely new N5 enum members or were always present and simply never surfaced in N4's
  usage-only inference (§19.7).
- **B19-G3** — `[CERT-hw]` reproduction: once an N5 station exists ([Block 3]/[Block 9]'s open item), save it
  and read the real `config.bog` header to confirm `version="5.0"` in practice (this block's finding is from
  reading the encoder's default constant, not from a live saved file — no N5 station has been created on this
  install) and confirm `<p>` component nodes carry `h=` handle attributes the way `bog-nav.py`'s indexer
  requires (§19.1's carried-over open item from the pre-existing `platform.bog` test).
- **B19-G4** — Trace the `KeyRing`/`SecurityInitializer` proprietary blocker on the N5 side (this block did not
  attempt to decompile `com.tridium.nre.security.{KeyRing,SecurityInitializer,SecurityInfoProvider}` — same
  named blocker N4's B114 records) to determine whether the at-rest master-key custody mechanism for
  `orientSystemDb.database`/`orientSystemDb.root`/`orientSystemDb.admin` KeyRing aliases (§19.4,
  `KEY_RING_*_ALIAS` constants) changed at all between N4 and N5.
- **B19-G5** — Confirm live (not just static) OrientDB 3.2.23→3.2.55 compatibility for an in-place N4→N5
  station migration: does N5's `orientSystemDb` module open an existing N4-created OrientDB `PLOCAL` database
  file directly, or does it require a schema/engine upgrade step? Not investigated this session (static
  decompile only; §19.4's `ORIENT_V3_2_SCHEMA = 2` constant name suggests OrientDB's own internal schema
  version is tracked, but this block did not trace what happens when that constant meets an on-disk database
  written by 3.2.23).

## 19.x — Connections

- **[Block 3]** — boot/security substrate: this block's `SecurityUtil.doPrivileged` calls (§19.1/§19.2) and
  every `@GrantFilePermission`/`@GrantNiagaraBasicPermission` module-info annotation cited (§19.3/§19.4) sit
  directly on the mechanisms that block documents.
- **[Block 5]** — the `javax.baja.*`→`niagara.*` rename: this block confirms it concretely for
  `ValueDocEncoder`/`ValueDocDecoder` (§19.1), `BISearchProvider` (§19.6), and the public-facing packages of
  every one of the 10 gap modules (`niagara.history`, `niagara.search`, `niagara.systemDb`, etc.) via their
  `module-info.java` `exports`/`requires` declarations.
- **[Block 8]** — permission model: §19.3's `history` module `@GrantFilePermission` scoped to
  `${protected.station.home}/history/-`, and §19.4's `orientSystemDb` module's `@GrantFilePermission` list
  (`security.json`, `/sys/fs/cgroup/memory/-`, `orientSystemDb/-`, etc.) and `@GrantNiagaraBasicPermission`
  (`KEY_MATERIAL`, `NIAGARA_SYSTEM_INDEX`) are concrete, real-module instances of that block's taxonomy —
  useful worked examples for that block's own `[INFER]`-flagged discussion of what a real module's grant
  profile looks like (§8.3's caveat that its 89/247 census contains no genuinely third-party module).
- **REMITTANCE → `niagara-research` B887/B911** — the N4-side systemDb/orientSystemDb + NEQL→OrientSQL
  architecture this block confirms as unchanged (§19.4/§19.6), with one real delta found (OrientDB 3.2.23→
  3.2.55, §19.4) and one open item B887 never covered (database-at-rest AES, §19.4/B19-G1).
- **REMITTANCE → `niagara-research` B930/B782** — the N4-side systemIndex/niagaraSystemIndex/query/queryTable/
  search unified pattern this block confirms unchanged class-for-class (§19.5/§19.6), now with a direct
  (not inferred) confirmation that the index storage target is `systemDb` (§19.5).
- **REMITTANCE → `niagara-research` B33/B410/B411** — the N4-side `.hdb` format and BOG crash-recovery
  mechanics this block confirms bit-for-bit identical magic numbers (§19.3) and identical control flow
  (§19.2), while flagging one pre-existing N4-corpus hex-transcription inconsistency (§19.3) that is out of
  this block's scope to fix.
- **REMITTANCE → `niagara-research` B5/B114** — the N4-side BOG-XML attribute grammar (§19.1) and
  `EncryptionKeySource` usage-inferred taxonomy (§19.7) this block cross-checks; §19.7 specifically documents
  an evidence-asymmetry (N5 decompiled directly, N4 never was) rather than asserting a delta.
- **[N5-G14]** (control/alarm/history/schedule/kitControl delta) — this block's §19.3 `.hdb`/history findings
  are a ready-made storage-layer baseline for that gap's own history-module coverage.
