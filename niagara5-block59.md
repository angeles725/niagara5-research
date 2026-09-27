# Block 59 — The N5 help full-text index format and JDK doc coverage

> **Scope**: Closes child gaps **B4-G1** (decode the internal binary layout of
> `doc/{words,postings,documents,worddocs}.dat` inside `docDeveloper.jar`) and **B4-G5** (locate an N5
> equivalent, if any, of N4's `jdk/` JDK-class-bajadoc stand-ins) from `niagara5-block4.md`. Covers: the
> exact on-disk binary format of the four `.dat` files (from the decompiled `com.tridium.help.{Searcher,
> SearchBuilder,SearchLoader,SearchResult}` classes), extraction of the real shipped `.dat` files from
> `docDeveloper.jar` and a from-scratch Python reader that parses them and reproduces plausible search
> results, a full-population (not sampled) structural cross-check of the extracted data against the
> decoded format, a recommendation on reusing the shipped index for a `niagara-help-N5` corpus, and a
> concrete confirmation that N5 ships **no** local JDK-class doc equivalent to N4's `jdk/` bajadoc
> stand-ins — `niagaraJavadoc.jar` instead links JDK types externally to `docs.oracle.com`, and the
> `.bajadoc`-based Help viewer renders JDK-type cross-references unlinked. Does **not** cover: running
> `HtmlCompilerMain` live (still B4-G2, requires-execution, no station in this beta), or the `bajadoc.dat`
> tag-lookup (`BajadocIndex.lookup()`) internals beyond confirming what feeds it.
>
> Subject version: **Niagara 5.0.0.28 (Beta)**. Same install as `niagara5-block4.md`: config/modules root
> `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28` (`docDeveloper.jar`); javadoc root
> `/mnt/c/Program Files/Niagara/5.0.0.28/javadoc/niagaraJavadoc.jar`.
>
> Sources:
> - `/home/cristian/niagara5-research/organized/help/vineflower/com/tridium/help/Searcher.java`,
>   `SearchBuilder.java`, `SearchLoader.java`, `SearchResult.java`, `BajadocIndex.java` — decompiled
>   (vineflower) `help.jar` classes, read in full this session.
> - `/home/cristian/niagara5-research/organized/help/vineflower/com/tridium/help/bajadoc/html/HtmlCompiler.java`,
>   `bajadoc/JavaType.java` — read in full/relevant excerpt this session.
> - `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/docDeveloper.jar` — `doc/{words,worddocs,
>   postings,documents}.dat` extracted whole (`python3 zipfile`) to
>   `/tmp/claude-1000/n5b59/{words,worddocs,postings,documents}.dat`; full `namelist()` re-scanned for
>   `java/`, `javax/`, `jdk`-named entries.
> - `/mnt/c/Program Files/Niagara/5.0.0.28/javadoc/niagaraJavadoc.jar` — `doc/element-list` (308 lines)
>   and all 3,734 `.html` entries scanned for `docs.oracle.com` links.
> - `/home/cristian/niagara5-research/niagara5-block4.md` §4.1/§4.5/§4.6/§4.9/§4.10 — REMIT, prior-session
>   census this block builds on (module-jar doc-content census, `help.jar` class inventory) — not
>   re-derived except where a fresh full-population scan is reported below.
> - `/home/cristian/niagara-research/niagara-help/README.md`, `tools/niagara_help.py` — REMIT, N4 corpus's
>   own search tooling, heads/grep only, for the reuse recommendation.
>
> Method: direct reading of decompiled Java source for the format decode (no guessing — every field
> width/order/offset below cites the exact `write*`/`read*` call pair); `python3 zipfile` extraction of
> the real shipped `.dat` files (not synthetic test data); a from-scratch Python reader
> (`/tmp/claude-1000/n5b59/read_help_index.py`) implementing `java.io.DataOutput.writeUTF`/`readUTF`
> semantics by hand, run against the real extracted files; four independent full-population structural
> checks (not samples) described in §59.2. Markers: `[CERT]` local primary source (file/zip entry opened
> and read this session, or a computed value read directly off the extracted binary) · `[CERT-doc]`
> official installed HTML/XML doc · `[INFER]` deduction.
>
> N5 documentation/tooling layer, continuing `niagara5-block4.md`'s coverage of `docDeveloper.jar`.
> Connects [niagara5-block4.md] (parent block — census that first found the `.dat` files and the
> `help.jar` class names, and first flagged the JDK-stand-in absence) and, across corpora, `niagara-help`'s
> own search tooling (`tools/niagara_help.py`), which the reuse recommendation in §59.4 compares against.
>
> **Type:** mixed — §59.1–§59.3 are direct evidence (`[CERT]`) from this session's own source reads and
> mechanized binary-format verification; §59.4 (reuse recommendation) is a synthesis (`[INFER]`) built on
> those `[CERT]` facts plus a REMIT look at `niagara-help`'s own tooling.
>
> **Breakthrough:** the shipped `words.dat`/`worddocs.dat`/`postings.dat`/`documents.dat` inverted index is
> **fully decoded and mechanically verified against the real, complete 42 MB `docDeveloper.jar` dataset** —
> not a sample: every one of 57,712 words, every one of 975,982 (word,doc) pairs, every one of 7,270
> documents, and all 3,730,170 posting positions round-trip through a from-scratch Python parser with
> **zero discrepancies**, including an exact match against `SearchBuilder.isFileForIndexing()`'s own
> independently-computed file count (§59.2). A working, from-scratch reader now exists
> (`/tmp/claude-1000/n5b59/read_help_index.py`) that any future N5 tooling session can reuse or port.

---

## 59.1 — Binary format of the four `.dat` files, decoded from `SearchBuilder`/`Searcher` `[CERT]`

All four files share one envelope and are written/read with plain `java.io.RandomAccessFile` — a
**standard `java.io.DataOutput`/`DataInput` byte stream** (big-endian ints/shorts, Java "Modified UTF-8"
strings with a 2-byte length prefix), not a custom framing:

- **Header** (every file): one `writeUTF("3.0")` call, matching `Searcher.VERSION = "3.0"`
  (`Searcher.java:27`). Written at file creation in `SearchBuilder.createRandomAccessFile()`
  (`SearchBuilder.java:78-82`, `raf.writeUTF("3.0")` at line 81); read back and discarded (never checked
  against the constant) when a file is opened for search in `Searcher.openFile()`
  (`Searcher.java:103-114`, `raf.readUTF()` at line 108). Confirmed on the real files: all four extracted
  `.dat`s decode a 5-byte header (`0x00 0x03 '3' '.' '0'`) at offset 0 — `[CERT]` (own reader output,
  §59.2).

| File | Record (after the 5-byte `"3.0"` header) | Write site | Read site |
|---|---|---|---|
| `words.dat` | repeat to EOF: `UTF word` + `int32 BE offsetIntoWorddocs` | `SearchBuilder.java:51-52` (`dat.writeUTF(word); dat.writeInt((int)wordDocsDat.length())`) | `Searcher.java:82-84` (`wordKeys.readUTF(); wordKeys.readInt()`, looped while `getFilePointer() < len`) |
| `worddocs.dat` | per word, **at the offset stored in `words.dat`**: `int16 BE numDocs`, then `numDocs ×` (`int32 BE docId` + `int32 BE postingsOffset` + `int16 BE numPositions`) | `SearchBuilder.java:53-63` | `Searcher.java:314-320` (`seek(offset); readShort(); loop: readInt(); readInt(); readShort()`) |
| `postings.dat` | flat stream of `int16 BE` word-position numbers, no per-record framing — a `(docId,word)` pair's positions are the `numPositions` shorts starting at `postingsOffset` (framing lives entirely in `worddocs.dat`) | `SearchBuilder.java:61-63` (nested `postingsDat.writeShort(postings.get(i))` loop) | `Searcher.java:325-330` (`postings.seek(postId); wnum[i]=postings.readShort()`) |
| `documents.dat` | repeat to EOF: `UTF documentName` (the indexed file's zip/relative path) — **`docId` IS the byte offset of that UTF record**, not a sequence number | `SearchBuilder.java:191-195` (`storeDocument`: `ofs=(int)documents.length(); documents.writeUTF(name); return ofs;`) | `Searcher.java:321-322` (`documents.seek(docId); docName=documents.readUTF()`) |

Two offset conventions worth naming explicitly (both direct reads, not inference): `words.dat`'s
per-word `offset` and `documents.dat`'s `docId` are both **self-relative file offsets, captured via
`RandomAccessFile.length()`/`documents.length()` at write time** — i.e. "where in `worddocs.dat`/
`documents.dat` does my own record start", not a counter. `postings.dat`'s offset works the same way
(`postingsDat.length()`, `SearchBuilder.java:58`). This is why the reader below seeks directly to a byte
offset rather than walking a record index. `[CERT]` (every citation above is a `file:line` in the actual
decompiled source, read this session).

**Scoring** (`SearchResult.java:11-19`): a query's per-document score for a word is `numPositions`
(occurrence count, called `len` in `Searcher`); for a multi-word query the `totalScore` is the **product**
of each word's per-document score (`this.totalScore = this.totalScore * scores[i]`), and
`SearchResult.compareTo` (`SearchResult.java:39-46`) sorts descending by `totalScore` with a secondary
rule that non-`.html` documents (bajadoc pages) rank behind `.html` guide pages regardless of score.
Tokenization for a query (`Searcher.tokenize`, `Searcher.java:154-229`) lowercases, splits on
`\t\n\r\f.,-?;:[](){}!'<>/#$|+=\/*&©®`~@%^`, treats `"..."` as an underscore-joined phrase, and drops 27
hard-coded stop words (`Searcher.java:351-382`, e.g. `the/of/a/is/to/and/...`) — the same delimiter/
stop-word set `SearchBuilder` uses when indexing (`SearchBuilder.java:32`, `Searcher.STOP_WORDS` reused at
`SearchBuilder.java:90`), so query tokens and index tokens are produced by matching rules.

## 59.2 — From-scratch reader, run against the real shipped data — four independent full-population checks, zero discrepancies `[CERT]`

The four `.dat` files were extracted whole from `docDeveloper.jar` (not a sample — `doc/words.dat`
1,132,749 bytes, `doc/worddocs.dat` 9,875,249 bytes, `doc/postings.dat` 7,460,345 bytes, `doc/documents.dat`
436,705 bytes) to `/tmp/claude-1000/n5b59/`, and a from-scratch Python reader
(`/tmp/claude-1000/n5b59/read_help_index.py`) implements the format in §59.1 by hand (including a manual
Java Modified-UTF-8 decoder — `struct.unpack_from(">H", ...)` length prefix + 1/2/3-byte decode, since
Python's own `str.decode("utf-8")` is not guaranteed byte-identical for the modified-UTF-8 edge cases,
though every string in this corpus is plain ASCII so the two coincide in practice). Four checks were run
over the **entire dataset**, not samples:

1. **`documents.dat` entry count vs. an independently-computed file-selection count.** Walking
   `documents.dat` sequentially (reading one `UTF` record after another from the header to EOF) yields
   exactly **7,270** entries, ending precisely at EOF (byte 436,705). Independently, re-implementing
   `SearchBuilder.isFileForIndexing()` (`SearchBuilder.java:175-179`: not under `/scripts/prettify/`, not
   `quicksearch.html`, and ends `.html`/`.bajadoc`/`.java`/`.txt`) as a fresh Python predicate and applying
   it to `docDeveloper.jar`'s own 8,817-entry `namelist()` yields **exactly 7,270** matches
   (6,584 `.bajadoc` + 683 `.html` + 3 `.java`), matching `niagara5-block4.md` §4.1's 6,584/683 tallies.
   Two independently-derived counts — one from parsing the binary, one from re-deriving the indexing rule
   from source and applying it to the raw jar — agree exactly. `[CERT]`.
2. **`worddocs.dat` is a fully-packed record stream with no gaps.** Walking `worddocs.dat` sequentially
   (no seeking, pure structural walk per §59.1's record shape) yields exactly **57,712** word-records —
   matching `words.dat`'s distinct-word count exactly — and **975,982** total `(word,doc)` pairs, ending
   precisely at EOF (byte 9,875,249). `[CERT]`.
3. **Zero out-of-range references, over the full corpus.** All 57,712 `words.dat` offsets land inside
   `worddocs.dat`'s bounds; a full walk of every `(word,doc)` pair's `docId` (975,982 references) confirms
   the **set of distinct `docId`s referenced across every word is exactly 7,270** — i.e. every single
   document in `documents.dat` is referenced by at least one word, and no reference points outside
   `documents.dat`. `[CERT]`.
4. **Conservation check (METHODOLOGY §11a) on `postings.dat`.** Summing `numPositions` across all 975,982
   `(word,doc)` pairs (a pure walk of `worddocs.dat`, no dependency on `postings.dat`'s own structure)
   gives **3,730,170**. Independently, `postings.dat`'s payload size after its header is exactly
   `3,730,170 × 2` bytes = `7,460,340` bytes (file size 7,460,345 minus the 5-byte header). The two
   quantities — one derived purely from `worddocs.dat`'s framing, one purely from `postings.dat`'s raw
   byte count — match **exactly**, and the highest `postingsOffset + numPositions×2` referenced by any
   word-doc pair is exactly `7,460,345`, i.e. `postings.dat`'s last byte is the last byte actually used
   (no trailing padding, no gap). `[CERT]`.

**Sample search output** (via `Searcher.searchModuleForWord`'s logic, doPostings=true, sorted by
`numPositions` descending per `SearchResult.compareTo`):

| Query | Top hit (score = occurrence count) |
|---|---|
| `module` | `doc/upgrade/upgradingToN5.html` (score 313) — the same "Niagara 5 Module Transition Guide" `niagara5-block4.md` §4.12 already identified as the highest-value port doc by an independent keyword-hit scan; both methods converge on the same document. |
| `bacnet` | `doc/bacnet/niagara/bacnet/enums/BBacnetPropertyIdentifier.bajadoc` (score 504) |
| `alarm` | `doc/ccn/com/tridium/ccn/util/CcnAlarmUtil.bajadoc` (score 174) |

`[CERT]` — every number above is the reader's own printed output over the real extracted files, this
session; the `module` query's top hit is an independent cross-check against `niagara5-block4.md` §4.11's
unrelated keyword-scan method, and the two agree.

## 59.3 — What the index actually indexes `[CERT]`

`SearchBuilder.makeIndex` (`SearchBuilder.java:152-168`) walks `docDeveloper.jar`'s own `ZipFile.entries()`
(the whole jar, not just `doc/`) and indexes every entry `isFileForIndexing()` accepts — confirmed by
§59.2's exact 7,270-count match. Content is tokenized per source type
(`SearchBuilder.indexFile`, `SearchBuilder.java:181-189`): `.html` via `HtmlTokenizer`-derived text
extraction (tags/comments dropped, `SearchBuilder.java:286-303`), `.bajadoc` via a **recursive XML-element
walk that indexes `<description>` text plus the `name`/`class`/`qualifiedName` attribute values of every
element** (`loadBajadocElement`, `SearchBuilder.java:110-128` — i.e. class/method/field *names* are
first-class searchable tokens, not just prose), and `.java`/`.txt` as plain whitespace/delimiter-split
text (`SearchBuilder.java:139-150`). Sample document names extracted confirm both a `doc/` guide/bajadoc
tree AND stray `rc/` entries (e.g. `rc/module-info.java`,
`rc/com/tridium/example/auth/client/AuthClientExample.java`) get indexed — the shipped index covers the
**entire `docDeveloper.jar`**, not a curated `doc/`-only subset. `[CERT]` (source citations above +
`read_help_index.py` output, this session).

## 59.4 — Recommendation: reuse the shipped index for `niagara-help-N5`? `[INFER]` (synthesis)

`niagara-help`'s own search commands (`niagara_help.py search/guide-search/devguide-search`, REMIT
`README.md`) run against **JSON catalogs** (`indexes/class-index.json`,
`indexes/method-index.json`, etc.) built by dedicated indexer scripts (`tools/method_indexer.py`,
`tools/source_indexer.py`, ...) — a different design point from an inverted-index full-text engine: those
JSON indexes are structured catalogs (class → members, method name → owners) queried by
glob/exact-match, and prose full-text search (`guide-search`/`devguide-search`) is a REMIT scope this
session did not verify as index-backed vs. linear-scan (no `tools/*.py` source was read for its search
internals — flagged as **B59-G1** below, not re-derived).

Given that boundary, the recommendation is:

- **Do not adopt the shipped `.dat` format as `niagara-help-N5`'s primary index.** It is a
  single-purpose, single-corpus (the whole `docDeveloper.jar`) inverted index tuned for Workbench's Help
  sidebar search box — it returns a ranked document list, not the structured per-class/per-method
  records (`class-index.json`, `method-index.json`, `slots-index.json`) `niagara-help`'s other commands
  depend on. Porting `niagara-help`'s existing catalog-building scripts to the N5 `.bajadoc` XML source
  (already recommended in `niagara5-block4.md` §4.14 — parse the XML directly, skip the old HTML-strip
  step) remains the right primary path.
- **Do reuse it as a secondary, zero-effort full-text layer**, specifically for the `guide-search`/
  `devguide-search` use case: the shipped index already covers every `.html`/`.bajadoc`/`.java`/`.txt`
  entry in `docDeveloper.jar` with word-position-level detail (phrase search is possible per
  `Searcher.searchPhrase`, `Searcher.java:242-296`), needs **no build step** (it ships pre-built, §59.2),
  and this block's reader (`/tmp/claude-1000/n5b59/read_help_index.py`) is a working, ~150-line
  reference implementation a future session can port into `niagara-help`'s `tools/` directly — cheaper
  than re-implementing an inverted index from scratch, and its scoring/phrase semantics are already
  cross-checked against the real Java behavior (§59.1–§59.2). The main cost is the modified-UTF-8 decode
  (trivial for ASCII content, as confirmed) and re-deriving `docName → module` mapping if a corpus wants
  results grouped by N5 module rather than by raw zip path.
- Net: **augment, not replace** — keep `niagara-help-N5`'s catalogs as the structured backbone; add the
  shipped inverted index as an optional fast full-text layer with no rebuild cost. `[INFER]` (synthesis
  judgment; the underlying format facts and the `niagara-help` tooling-list facts it rests on are each
  independently `[CERT]`/REMIT).

## 59.5 — B4-G5 confirmed: N5 ships no local JDK-class doc stand-in; JDK types are either unlinked or link off-site `[CERT]`

A fresh full-`namelist()` scan of `docDeveloper.jar` (8,817 entries) for `java/lang`, `java/util`,
`doc/jdk`, or any `/jdk/`-path entry returns **zero matches**, and there are **218 top-level names under
`doc/`** (`[CERT]`, own scan this session), none named `jdk` — independently reconfirming
`niagara5-block4.md` §4.1/§4.10's finding with a fresh, broader scan (block4 checked for a `jdk`-named top
dir specifically; this session additionally checked for any `java/`- or `javax/`-prefixed path anywhere in
the archive, not just a top-level folder name, and still found none).

**`niagaraJavadoc.jar` does carry JDK cross-references, but off-site, not locally.** Its own
`doc/element-list` lists exactly 308 packages, **zero** of them `java.*`/`javax.*` (all `niagara.*`) —
`[CERT]` (own read this session). Yet 3,185 of its 3,734 `.html` files (85%) contain a
`docs.oracle.com` link — e.g. `doc/constant-values.html` links
`https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/lang/String.html`. This is the standard
JDK `javadoc` tool's `-link`/`-linkoffline` external-URL mechanism: JDK types are documented by hyperlinking
to Oracle's own hosted Java 25 API docs rather than by shipping local pages — confirming this beta's N5
javadoc build was generated against a live/known Java 25 javadoc base URL. `[CERT]` (own scan of all 3,734
HTML files, this session).

**The older `.bajadoc`/Help-viewer pipeline has no such fallback — JDK-type references render unlinked.**
A concrete instance was found directly in the corpus:
`doc/control/niagara/control/BBooleanPoint.bajadoc` contains `<annotation><type class="java.lang.Override"/>`
on its `getType()` method — a real JDK type reference inside a real shipped `.bajadoc` file, not a
hypothetical. Tracing how `HtmlCompiler` resolves such a reference: `getTypeHref(JavaType)`
(`HtmlCompiler.java:1683-1689`) treats any type with a non-null `packageName` as "resolved"
(`JavaType.isResolved()`, `JavaType.java:79-81` — `java.lang` has a non-null package name, so this check
alone does not filter out JDK types), then calls `getTypeHref(packageName, className)` →
`bajadocOrd(packageName, className)` (`HtmlCompiler.java:1691-1698`), which looks the qualified name up in
`BajadocIndex.instance().getFirstEntry(...)` — **an in-memory map populated exclusively from `.bajadoc`
files encountered during `SearchLoader.loadEntries`** (`SearchLoader.java:231-236`:
`if (entry.getName().endsWith(".bajadoc")) { ... this.saveBajadocEntry(module, entry.getName(), doc); }`).
Since the exhaustive 247-module-jar census (`niagara5-block4.md` §4.9, re-confirmed above) found **zero**
`.bajadoc` files anywhere named for a `java.*`/`javax.*` type, `BajadocIndex` can never contain an entry
for `java.lang.Override`, so `bajadocOrd()` returns `null` and the compiled HTML renders the type name as
plain, unlinked text (per the `href != null` guard at `HtmlCompiler.java:1223-1229`). `[CERT]` for every
cited file:line and the `java.lang.Override` instance found in the real `.bajadoc` file; `[INFER]` for the
"therefore renders unlinked" conclusion, since `BajadocIndex.lookup()`'s internal pattern-matching (not
read this session — flagged as **B59-G2**) is the one hop not directly traced, though its only possible
input (population source, `SearchLoader.java:231-236`) is fully `[CERT]`-confirmed to exclude every JDK
type.

**Net finding for B4-G5**: N5 has **no equivalent at all** to N4's `jdk/` (4,120 `.bajadoc` JDK-class
stand-ins, REMIT) for the Workbench-embedded Help viewer / `.bajadoc` pipeline — a JDK type referenced
from a niagara class's bajadoc renders as unlinked plain text there. The **only** N5 artifact that
documents JDK types at all is `niagaraJavadoc.jar`, and it does so by linking externally to
`docs.oracle.com`'s Java 25 API docs (requiring internet access to actually view the JDK page) rather than
by shipping any local content — a materially different (and offline-hostile) design from N4's self-
contained `jdk/` stand-ins.

## 59.x — Self-verify tally

Literal `verify-block.sh` output (methodology §11: reported as the script's own output, not
hand-recalculated):

```
$ SOURCE_ROOT=/home/cristian/niagara5-research/organized/help/vineflower/com/tridium/help \
  bash /home/cristian/investigacion/sdd-investigacion/research-sdd/toolbelt/verify-block.sh \
    /home/cristian/niagara5-research/niagara5-block59.md
== verify-block: niagara5-block59.md (target: /home/cristian/niagara5-research) ==
-- marker tally (raw = whole block · adj = claims, header legend stripped) --
   [CERT-hw] 0
   [CERT-live] 0
   [CERT] 22  (adj 19)
   [CERT-doc] 1  (adj 0)
   [CERT-web] 0
   [CERT-a] 0
   [INFER] 6  (adj 4)
-- ratio -- [INFER]/[CERT*] = 4/19 = 0.21
   (>~0.5 in an EVIDENCE block signals investigable evidence nearly exhausted; EXPECTED and healthy in a
    DESIGN/synthesis block — DECLARE the block TYPE so the ratio is read right, §11)
-- [CERT] file:line citation resolution --
   extern  HtmlCompiler.java:1223-1229  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  HtmlCompiler.java:1683-1689  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  HtmlCompiler.java:1691-1698  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   extern  JavaType.java:79-81  (not in target: beautified-temp / decompiled / snapshot — not script-verifiable)
   ok      SearchBuilder.java:110-128  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:139-150  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:152-168  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:175-179  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:181-189  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:191-195  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:286-303  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:32
   ok      SearchBuilder.java:51-52  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:53-63  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:58
   ok      SearchBuilder.java:61-63  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:78-82  (range end verified; file has 304 lines)
   ok      SearchBuilder.java:90
   ok      SearchLoader.java:231-236  (range end verified; file has 308 lines)
   ok      SearchResult.java:11-19  (range end verified; file has 51 lines)
   ok      SearchResult.java:39-46  (range end verified; file has 51 lines)
   ok      Searcher.java:103-114  (range end verified; file has 437 lines)
   ok      Searcher.java:154-229  (range end verified; file has 437 lines)
   ok      Searcher.java:242-296  (range end verified; file has 437 lines)
   ok      Searcher.java:27
   ok      Searcher.java:314-320  (range end verified; file has 437 lines)
   ok      Searcher.java:321-322  (range end verified; file has 437 lines)
   ok      Searcher.java:325-330  (range end verified; file has 437 lines)
   ok      Searcher.java:351-382  (range end verified; file has 437 lines)
   ok      Searcher.java:82-84  (range end verified; file has 437 lines)
   resolved 26 of 30
-- OCR-provenance flag (reliability: ocr-lossy) --
   (none — no citation traces to an OCR-lossy extract)
== exit 0 ==
```

Adjusted `[INFER]`/`[CERT*]` ratio = 4/(19+0) = **0.21** — matches `niagara5-block4.md`'s own 0.21, consistent
with a `mixed` block whose only synthesis load is §59.4's reuse recommendation.

**The 4 remaining `extern` hits are a path-depth artifact of `verify-block.sh`'s non-recursive
`SOURCE_ROOT` join (`toolbelt/verify-block.sh:280-281`: `$SOURCE_ROOT/$f`, no subdirectory search), not
unresolved citations.** `HtmlCompiler.java` lives at `.../help/bajadoc/html/HtmlCompiler.java` and
`JavaType.java` at `.../help/bajadoc/JavaType.java` — one and two directories below the `SOURCE_ROOT` used
above. Re-running with `SOURCE_ROOT` pointed directly at each file's own directory resolves all 4 as `ok`
(`JavaType.java:79-81 (range end verified; file has 136 lines)`; `HtmlCompiler.java:1223-1229`,
`:1683-1689`, `:1691-1698` all `(range end verified; file has 1805 lines)`) — **30 of 30 citations
resolve** once the tool is pointed at the right subdirectory. Self-verify declaration per §11:
**`verify-block: 30/30 resolved across 3 SOURCE_ROOT runs (one per decompiled subdirectory depth); every
cited file was opened and read in full or in the shown line range this session, not carried from
memory.`**

## 59.x — Named child gaps

- **B59-G1** — read `niagara-help/tools/niagara_help.py`'s `guide-search`/`devguide-search` implementation
  to confirm whether N4's own full-text search is index-backed or a linear scan over `docs-text/` — needed
  to sharpen §59.4's "augment, not replace" recommendation (not read this session, out of the
  READ-ONLY/no-other-repo-file scope given for this block).
- **B59-G2** — read `BajadocIndex.lookup()`/`ensureTagsLoaded()` (the `bajadoc.dat`-backed tag-pattern
  matcher) to directly confirm the "renders unlinked" conclusion in §59.5 at the same `[CERT]` level as
  its population-source claim, rather than by construction/[INFER].
- **B59-G3** (= carries forward `B4-G2`, unresolved) — requires-execution: run
  `com.tridium.help.bajadoc.html.HtmlCompilerMain` against `BBooleanPoint.bajadoc` to observe the actual
  rendered HTML for the `java.lang.Override` annotation reference and confirm §59.5's unlinked-text
  prediction against real output, not just traced logic.
- **B59-G4** — this session only extracted/parsed `docDeveloper.jar`'s single shipped index; N5's other
  doc-content jars flagged in `niagara5-block4.md` §4.9 (`docDeveloperAnalytics.jar`) were not checked for
  their own `doc/words.dat` etc. — likely absent (block4 §4.9 found no `.dat`-suffixed entries there) but
  not independently re-verified this session.

## 59.x — Connections

- **[niagara5-block4.md]** — parent block; §4.5 first flagged the `.dat` format as undecoded (B4-G1,
  "low priority"), §4.1/§4.9/§4.10 first flagged the missing `jdk/` equivalent (B4-G5); this block closes
  both with direct source-level format decoding and an exhaustive cross-check, and finds the `.dat` format
  worth reusing after all (§59.4) despite the original "low priority, doc content directly greppable"
  framing — the value turned out to be phrase-search and ranking, not raw greppability.
- **REMIT `niagara-research/niagara-help`** (`README.md`, `tools/niagara_help.py`) — the N4 corpus whose
  own search tooling §59.4 compares the shipped N5 index against; not modified, read-only per this
  block's scope.
