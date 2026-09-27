# Module Navigator (N5 port)

N5 port of the N4 `module-navigator` tool (`/home/cristian/niagara-research/module-navigator`,
left unmodified). Navigates the decompiled Niagara **N5** corpus at
`/home/cristian/niagara5-research/organized/`: **252 modules** (246 regular +
6 `_bin-ext/<jar>`), **~21,751 .class files** / **14,578 .java files**,
**18,239 unique class names**, **171,104 method definitions**,
**207,971 call-graph edges**. 12 indexes, ~347 MB total. Zero deps (Python
stdlib only).

Complements the N4 tool the same way it did for N4: same 175+ CLI commands,
same REPL, same web dashboard -- pointed at a different (flat) corpus layout.

## Corpus layout differences vs N4

N4's corpus was `organized/{module}/{module}-{type}/vineflower/` (one
submodule per rt/wb/ux/doc/se type, read from
`<submodule>/pipeline/fase1-recon.json`). N5's corpus is **flat**:

    organized/<module>/
      extracted/       raw jar extraction (includes .class files)
      resources/       non-.class jar entries only (what `resources` reads)
      vineflower/       primary decompile output
      fallback/         CFR output, present only where vineflower failed
      recon.json        per-module decompile report (class_count, etc.)
    organized/docSource/   original Tridium sources (not a module)
    organized/_bin-ext/<jar>/   same per-module layout, one level deeper --
                                indexed as module "_bin-ext/<jar>"
    organized/_logs/, organized/_recon/   pipeline housekeeping (not modules)

Inventory keys are the module name directly (no `-rt`/`-ux` suffix, since
there's no submodule split). `class-index.json`'s `path` field is always
relative to `organized/`, e.g. `baja/vineflower/niagara/sys/BComponent.java`
or, for an overlay class, `acme/fallback/pkg/Bar.java`.

**Fallback overlay:** `build_class_index.py` scans `vineflower/` first, then
scans `fallback/` and only adds classes whose relative path wasn't already
found under `vineflower/` -- so vineflower always wins on overlap, and
fallback (CFR) fills in classes vineflower failed to decompile.

## Quickstart

    # CLI directo
    python3 tools/module_nav.py stats
    python3 tools/module_nav.py class BComponent
    python3 tools/module_nav.py callers BComponent started
    python3 tools/module_nav.py resources baja --type xml
    python3 tools/module_nav.py strings "License"

    # REPL interactivo
    python3 tools/module_nav.py repl

    # Web dashboard
    python3 tools/module_nav_web.py --port 8042

## Layout

    tools/
      corpus_config.py         N5 port: shared organized/ dir + layout resolution
      module_nav.py             CLI principal
      module_nav_web.py         Web dashboard
      module_nav_lib/           Una lib por fase/dominio
      web/                      Frontend ES5 vanilla del dashboard
      build_*.py                12 builders (1 por index)
    indexes/                    10 JSON + 2 SQLite (gitignored -- see below)
    reindex.sh                  Orquestador seguro de re-index (orden + validación + rollback)
    tests/                      unittest suite (unit tests for the port + the
                                 N4 smoke/contract/robustness suite, fixtures
                                 updated for the N5 corpus)

## Re-indexado

Usar SIEMPRE `./reindex.sh` (no correr los `build_*.py` a mano). Respeta el
orden de dependencias (`class-index` -> `module-inventory` -> resto: los
builders de method/field/xref/annotations leen el `source` del corpus desde
`module-inventory.json`), hace backup previo, valida que ningún índice quede
vacío y revierte el que se rompa. `./reindex.sh --check` muestra el plan sin
ejecutar; `--only <builder.py>` regenera uno solo.

The corpus root is resolved automatically (in order): `--organized <dir>` CLI
flag on the three builders that read the corpus directly
(`build_module_inventory.py`, `build_class_index.py`), the `NAV_ORGANIZED_DIR`
environment variable, the sibling `organized/` directory next to
`module-navigator/` (the default for this copy), or an existing
`indexes/module-inventory.json`'s `_meta.source`. See `tools/corpus_config.py`.
`build_module_inventory.py --layout flat|n4` selects the corpus shape (default
`flat`, i.e. N5); `n4` reproduces the original N4 submodule/fase1-recon.json
scan for reuse against an N4-shaped corpus.

## Fuente de datos

Decompiled from `/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/*.jar`
(and `bin/ext/*.jar` for `_bin-ext/`) with vineflower (primary) + CFR
(fallback), into `/home/cristian/niagara5-research/organized/`.

## Known gaps

- `swing-index.json` builds successfully but is empty (0 WB/UX modules): its
  WB/UX filter keys off `module-inventory`'s legacy `type` field
  (`"wb"`/`"ux"`), which doesn't exist in N5's flat layout (no submodule
  split). Redesigning UI-module detection for N5 was out of scope for this
  port. `reindex.sh` reports this index as a validation failure ("tiny") even
  though 0 WB+UX modules is the correct, expected result for N5 today --
  known false positive in the size-based validation heuristic.
- `bog-trace` / `bog-classes` / `bog-coverage` (BOG-Code Bridge) no longer
  have a hardcoded fallback path to the sibling N4 "Reflow-Clean" project's
  `bog_index.json` (dropped, not replaced -- out of scope). They still work
  if a `bog_index.json` is placed next to `module-navigator/` or in the CWD,
  or via `--bog-index`/`BOG_INDEX_PATH`.
- `method-index.json`/`field-index.json`/`callgraph-index.json`/etc.
  (the 9 builders not touched by this port) still print/store the literal
  string "Niagara N4 decompiled modules" in their `_meta.description` --
  cosmetic only, no path or behavior is N4-specific; left as-is since fixing
  it was outside this port's explicit scope.
