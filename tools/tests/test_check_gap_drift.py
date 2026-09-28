"""Tests for tools/check-gap-drift.py (backlog row vs block child-gap bullet drift)."""
import os
import subprocess
import sys
import tempfile
import unittest

TOOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "check-gap-drift.py")

STATE = """| Priority | Gap | Artifact type / source | Status |
|---|---|---|---|
| low | B7-G1 Census of the widget palette registry entries | mod | pending |
| low | B7-G2 Firewall nftables rule generation path | mod | pending |
| low | B7-G3 Something already done | mod | ✅ covered — B9 |
"""
BLOCK = """# Block 7

## 7.x — Child gaps opened

- **B7-G1** — Census of the widget palette registry entries across modules.
- **B7-G2** — Read the Jetty QoS filter migrator property list.
- **B7-G3** — Anything.
"""


def run(root, *extra):
    return subprocess.run([sys.executable, TOOL, "--root", root, *extra],
                          capture_output=True, text=True)


class TestCheckGapDrift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        with open(os.path.join(self.tmp.name, "RESEARCH-STATE.md"), "w") as f:
            f.write(STATE)
        with open(os.path.join(self.tmp.name, "niagara5-block7.md"), "w") as f:
            f.write(BLOCK)

    def tearDown(self):
        self.tmp.cleanup()

    def test_flags_only_the_drifted_pending_row(self):
        r = run(self.tmp.name)
        self.assertEqual(r.returncode, 1)
        self.assertIn("DRIFT? B7-G2", r.stdout)
        self.assertNotIn("B7-G1", r.stdout.replace("checked", ""))
        self.assertIn("checked=2 suspects=1", r.stdout)

    def test_all_flag_includes_closed_rows(self):
        r = run(self.tmp.name, "--all")
        self.assertIn("checked=3", r.stdout)

    def test_missing_state_is_usage_error(self):
        empty = tempfile.TemporaryDirectory()
        self.addCleanup(empty.cleanup)
        self.assertEqual(run(empty.name).returncode, 2)


if __name__ == "__main__":
    unittest.main()
