# Module Navigator

Navegador del código decompilado de **926 JARs** Niagara N4 (**51,167 clases**).
Complementa al Help Navigator (docs públicas) y al BOG Navigator (stations).

**Estado:** 100% DONE — 43 fases (F0–F42), 175 comandos CLI + web dashboard, 12 indexes (~1,354.7 MB). Zero deps (Python stdlib only).

## Quickstart

    # CLI directo
    python tools/module_nav.py stats
    python tools/module_nav.py class BWebServlet
    python tools/module_nav.py unified AlarmService

    # REPL interactivo (autocomplete contra 46,969 clases)
    python tools/module_nav.py repl

    # Web dashboard (F32)
    python tools/module_nav_web.py --port 8042
    # → http://localhost:8042

## Documentación

- **Manual completo de los 3 navegadores (Help / Module / BOG):**
  `../NAVIGATORS_MANUAL.md`
- **Plan y estado de las 43 fases:** `ROADMAP.md`
- **Gaps / ideas pendientes:** `GAPS.md`

## Layout

    tools/
      module_nav.py           CLI principal (175 comandos)
      module_nav_web.py       Web dashboard (F32, port 8042)
      module_nav_lib/         Una lib por fase/dominio (50+ módulos)
      web/                    Frontend ES5 vanilla del dashboard
      build_*.py              12 builders (1 por index)
    indexes/                  10 JSON + 2 SQLite (token-index.db, string-index.db)
    reindex.sh                Orquestador seguro de re-index (orden + validación + rollback)

## Re-indexado

Para regenerar los índices tras cambiar el corpus, usar SIEMPRE `./reindex.sh`
(no correr los `build_*.py` a mano). Respeta el orden de dependencias
(`class-index` -> `module-inventory` -> resto: los builders de method/field/xref/
annotations leen el `source` del corpus desde `module-inventory.json`, así que
debe regenerarse antes que ellos), hace backup previo, valida que ningún índice
quede vacío y revierte el que se rompa. `./reindex.sh --check` muestra el plan
sin ejecutar; `--only <builder.py>` regenera uno solo.

## Fuente de datos

Vineflower 1.11.1 decompila `C:\modules\Prototipos\modulos\organized\{module}\{module}-{type}\vineflower\`.
