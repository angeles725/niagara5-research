"""Integration test for tools/githooks/pre-commit.

The hook must gate the commit on the STAGED (git index) content of niagara5-block*.md and
RESEARCH-STATE.md, never the working-tree files. Before this fix the hook ran
`tools/lint-block.py "${staged_blocks[@]}"` directly on the working-tree paths, so:
  - fixing a violation in the working tree WITHOUT re-`git add`-ing it still let a violating
    STAGED blob through (fail-open, contradicting the hook's own "staged files only" comment);
  - the reverse also mattered: a clean staged version must commit even if the working tree is
    later dirtied with an unrelated, unstaged violation.

Both directions are exercised here against a real scratch git repo with the hook installed as
core.hooksPath, so this is a black-box proof of the actual `git commit` gate, not of any Python
internals.
"""
import os
import shutil
import stat
import subprocess
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VIOLATING = """# Block 9100 — pre-commit hook integration fixture

## 9100.1

This class now uses pattern-matching for the switch expression `[CERT]`.
"""

CLEAN = """# Block 9100 — pre-commit hook integration fixture

## 9100.1

This class now uses pattern-matching for the switch expression, confirmed via javap typeSwitch
bytecode `[CERT]`.
"""


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


class _ScratchRepoTestCase(unittest.TestCase):
    """Builds a minimal scratch git repo with the real hook + tools installed."""

    HOOK_SOURCE = os.path.join(TOOLS_DIR, "githooks", "pre-commit")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = self.tmp.name

        self.assertEqual(_git(self.repo, "init", "-q").returncode, 0)
        _git(self.repo, "config", "user.email", "test@example.com")
        _git(self.repo, "config", "user.name", "Test")

        os.makedirs(os.path.join(self.repo, "tools", "githooks"))
        shutil.copy(os.path.join(TOOLS_DIR, "lint-block.py"),
                    os.path.join(self.repo, "tools", "lint-block.py"))
        shutil.copy(os.path.join(TOOLS_DIR, "check-gap-drift.py"),
                    os.path.join(self.repo, "tools", "check-gap-drift.py"))
        hook_dest = os.path.join(self.repo, "tools", "githooks", "pre-commit")
        shutil.copy(self.HOOK_SOURCE, hook_dest)
        st = os.stat(hook_dest)
        os.chmod(hook_dest, st.st_mode | stat.S_IEXEC)

        r = _git(self.repo, "config", "core.hooksPath", "tools/githooks")
        self.assertEqual(r.returncode, 0, r.stderr)

        with open(os.path.join(self.repo, "README.md"), "w") as f:
            f.write("seed\n")
        _git(self.repo, "add", "README.md")
        r = _git(self.repo, "commit", "-q", "-m", "seed")
        self.assertEqual(r.returncode, 0, r.stderr)

    def _write_block(self, content):
        path = os.path.join(self.repo, "niagara5-block9100.md")
        with open(path, "w") as f:
            f.write(content)
        return path

    def _write_path(self, name, content):
        path = os.path.join(self.repo, name)
        with open(path, "w") as f:
            f.write(content)
        return path


class TestPreCommitHookStagedOnly(_ScratchRepoTestCase):
    def test_staged_violation_still_blocks_after_working_tree_fix(self):
        # Stage a VIOLATING version, then fix the file in the working tree WITHOUT re-staging.
        # The hook must still lint the staged (violating) blob and block the commit.
        path = self._write_block(VIOLATING)
        _git(self.repo, "add", "niagara5-block9100.md")
        with open(path, "w") as f:
            f.write(CLEAN)
        r = _git(self.repo, "commit", "-q", "-m", "add block 9100")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("lint-block.py", r.stdout + r.stderr)

    def test_staged_clean_commits_even_if_working_tree_is_later_dirtied(self):
        # Stage a CLEAN version, then dirty the working tree with a violation WITHOUT staging it.
        # The hook must lint only the staged (clean) blob and let the commit through.
        path = self._write_block(CLEAN)
        _git(self.repo, "add", "niagara5-block9100.md")
        with open(path, "w") as f:
            f.write(VIOLATING)
        r = _git(self.repo, "commit", "-q", "-m", "add block 9100")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


BLOCK_9101 = """# Block 9101 — pre-commit hook integration fixture (gap drift)

## 9101.x — Child gaps opened

- **B9101-G1** — Census of the widget palette registry entries across modules. coverage-check:
  not yet swept.
"""

STATE_DRIFTED = """| Priority | Gap | Artifact type / source | Status |
|---|---|---|---|
| low | B9101-G1 Firewall nftables rule generation path (unrelated topic) | mod | pending |
"""

STATE_CLEAN = """| Priority | Gap | Artifact type / source | Status |
|---|---|---|---|
| low | B9101-G1 Census of the widget palette registry entries | mod | pending |
"""


class TestPreCommitHookResearchStateStagedOnly(_ScratchRepoTestCase):
    """Same staged-vs-working-tree discipline, but for the RESEARCH-STATE.md / check-gap-drift.py
    leg of the hook (the parent niagara5-block9101.md is committed up front and untouched)."""

    def setUp(self):
        super().setUp()
        self._write_path("niagara5-block9101.md", BLOCK_9101)
        _git(self.repo, "add", "niagara5-block9101.md")
        r = _git(self.repo, "commit", "-q", "-m", "seed block 9101")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_staged_drift_still_blocks_after_working_tree_fix(self):
        path = self._write_path("RESEARCH-STATE.md", STATE_DRIFTED)
        _git(self.repo, "add", "RESEARCH-STATE.md")
        with open(path, "w") as f:
            f.write(STATE_CLEAN)
        r = _git(self.repo, "commit", "-q", "-m", "add RESEARCH-STATE.md")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("check-gap-drift.py", r.stdout + r.stderr)

    def test_staged_clean_commits_even_if_working_tree_is_later_dirtied(self):
        path = self._write_path("RESEARCH-STATE.md", STATE_CLEAN)
        _git(self.repo, "add", "RESEARCH-STATE.md")
        with open(path, "w") as f:
            f.write(STATE_DRIFTED)
        r = _git(self.repo, "commit", "-q", "-m", "add RESEARCH-STATE.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
