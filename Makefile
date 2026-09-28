.PHONY: test test-verbose shellcheck catalog lint check install-hooks

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

# Mechanical decompiler-fidelity / method-blind-spot rules (R0-R8): enforced mode only applies to
# blocks >= tools/lint-block.py's --min-block (currently 115) and check-gap-drift must report zero
# suspects. This is what CI and the pre-commit hook both run.
lint:
	python3 tools/lint-block.py
	python3 tools/check-gap-drift.py

# Install this repo's own git hooks (tools/githooks/) as the active hooksPath for this checkout.
install-hooks:
	git config core.hooksPath tools/githooks
	@echo "core.hooksPath set to tools/githooks — pre-commit now runs tools/lint-block.py + check-gap-drift.py on staged files."

# Everything CI runs, in one target: unit tests plus the mechanical corpus lint.
check: test lint
