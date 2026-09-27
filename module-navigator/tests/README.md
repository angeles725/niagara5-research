# Module Navigator — Test Suite

Smoke, JSON-contract, and robustness tests for the `module_nav.py` CLI.
Zero deps (Python `unittest`, stdlib only) — same policy as the tool itself.

These are **integration/smoke tests**: they invoke the real CLI as a subprocess
against the real `indexes/`. They verify the tool is wired up and its output
contracts hold — not the internals of every function.

## Run

    # all tests
    python3 -m unittest discover -s tests -p 'test_*.py'

    # one file
    cd tests && python3 -m unittest test_json_contract -v

Runtime is ~90s (some commands load the 143 MB method-index or run every audit).
Requires the indexes to be built (`./reindex.sh` if missing).

## Files

| File | Covers |
|------|--------|
| `_harness.py` | Shared `run_nav()` subprocess helper + known-valid corpus fixtures |
| `test_smoke.py` | Core navigation commands (`stats`, `class`, `module`, `search`, `methods`, `hierarchy`) run and return plausible output |
| `test_json_contract.py` | Every `--json` command emits **pure JSON on stdout** (no progress noise). Enforces the project criterion "--json produce JSON válido en todos los comandos" |
| `test_robustness.py` | Missing class/module fails gracefully — plain message, no Python traceback |

## Fixtures

All known-valid corpus entities (class, module, feature, method) live in
`_harness.py`. If the corpus changes and a fixture disappears, update it there
in one place.

## History

The JSON-contract suite caught 6 real bugs on its first run: three audit
commands (`resolve-audit`, `driver-cleanup-audit`, `service-order`) leaked
`Scanning...` to stdout, and three callgraph commands (`integration-contract`,
`virtual-callers`, `feature-brief`) leaked `Loading...` — all breaking `--json`.
Progress output now goes to stderr.
