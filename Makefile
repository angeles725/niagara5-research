.PHONY: test test-verbose shellcheck catalog lint check install-hooks census census-sweep

# Run every tools/tests/test_*.py. Tests requiring the real, read-only N4/N5
# installs skip automatically when those paths are absent on this machine.
test:
	python3 -m unittest discover -s tools/tests

test-verbose:
	python3 -m unittest discover -s tools/tests -v

# Lint every hook script (requires shellcheck on PATH).
shellcheck:
	shellcheck tools/hooks/*.sh tools/githooks/pre-commit .claude/hooks/*.sh

# Regenerate CATALOG.md from niagara5-block*.md (idempotent).
catalog:
	python3 tools/gen-catalog.py

# Mechanical decompiler-fidelity / method-blind-spot rules (R0-R9): enforced mode only applies to
# blocks >= tools/lint-block.py's --min-block (currently 115; R9 only from block 123) and check-gap-drift must report zero
# suspects. CI runs exactly these two commands, full-corpus, as separate steps (plus `make test`
# and its own shellcheck step, which this target does NOT include). The pre-commit hook does NOT
# run this target: it lints only the staged niagara5-block*.md/RESEARCH-STATE.md blobs it
# materializes from the git index, not the whole corpus -- see tools/githooks/pre-commit.
lint:
	python3 tools/lint-block.py
	python3 tools/check-gap-drift.py

# Extraction gate over the LOCAL corpus (B117-G7): for every Tridium module that has an
# organized/<mod>/recon.json, re-run the byte-exactness census and `jarsigner -verify -strict`
# and record byte_exact / signature_* in that recon.json; exits 1 if any module fails. Needs the
# read-only N5 module jars (N5_MODULES_DIR) and organized/, so it is NOT part of `check` and NOT
# run by CI (CI has neither; it runs only `make test`, lint and shellcheck). `census-sweep` is the
# read-only aggregate (`n5-extract-census.py sweep`, no recon.json writes, no jarsigner).
census:
	tools/n5-decompile.sh --verify

census-sweep:
	python3 tools/n5-extract-census.py sweep "$${N5_MODULES_DIR:-/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules}" "$${N5_OUT_DIR:-organized}"

# Install this repo's own git hooks (tools/githooks/) as the active hooksPath for this checkout.
install-hooks:
	git config core.hooksPath tools/githooks
	@echo "core.hooksPath set to tools/githooks — pre-commit now runs tools/lint-block.py + check-gap-drift.py on staged files."

# Most of what CI runs, in one target: unit tests plus the full-corpus mechanical lint. CI also
# runs a separate `shellcheck tools/githooks/pre-commit` step that this target does not include
# (run `make shellcheck` for that).
check: test lint
