.PHONY: test test-verbose shellcheck catalog

# Run every tools/tests/test_*.py. Tests requiring the real, read-only N4/N5
# installs skip automatically when those paths are absent on this machine.
test:
	python3 -m unittest discover -s tools/tests

test-verbose:
	python3 -m unittest discover -s tools/tests -v

# Lint every hook script (requires shellcheck on PATH).
shellcheck:
	shellcheck tools/hooks/*.sh .claude/hooks/*.sh

# Regenerate CATALOG.md from niagara5-block*.md (idempotent).
catalog:
	python3 tools/gen-catalog.py
