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
- **B7-G3** — Something already done and closed.
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
        flagged = [l for l in r.stdout.splitlines() if l.startswith(("DRIFT?", "NO-BULLET", "NO-BLOCK"))]
        self.assertFalse(any("B7-G1" in l for l in flagged))
        self.assertIn("checked=2 suspects=1", r.stdout)

    def test_all_flag_includes_closed_rows(self):
        r = run(self.tmp.name, "--all")
        self.assertIn("checked=3", r.stdout)
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("DRIFT? B7-G3", r.stdout)

    def _write_state(self, rows):
        with open(os.path.join(self.tmp.name, "RESEARCH-STATE.md"), "w", encoding="utf-8") as f:
            f.write("| Priority | Gap | Artifact type / source | Status |\n|---|---|---|---|\n" + rows)

    def test_clean_backlog_exits_zero(self):
        self._write_state("| low | B7-G1 Census of the widget palette registry entries | mod | pending |\n")
        r = run(self.tmp.name)
        self.assertEqual(r.returncode, 0)
        self.assertIn("checked=1 suspects=0", r.stdout)

    def test_missing_block_file_is_reported_separately_from_missing_bullet(self):
        self._write_state("| low | B8-G1 Anything at all here | mod | pending |\n"
                          "| low | B7-G9 Something undefined | mod | pending |\n")
        r = run(self.tmp.name)
        self.assertIn("NO-BLOCK B8-G1", r.stdout)
        self.assertIn("NO-BULLET B7-G9", r.stdout)

    def test_gap_like_rows_the_regex_cannot_parse_are_warned(self):
        self._write_state("| low | B7-G1 Census of the widget palette registry entries | mod | pending | \n")
        r = run(self.tmp.name)
        self.assertIn("UNPARSED", r.stdout)
        self.assertEqual(r.returncode, 1)

    def test_unreadable_block_is_an_io_error(self):
        with open(os.path.join(self.tmp.name, "niagara5-block7.md"), "wb") as f:
            f.write(b"\xff\xfe not utf-8 \xff")
        r = run(self.tmp.name)
        self.assertEqual(r.returncode, 2)

    def test_missing_state_is_usage_error(self):
        empty = tempfile.TemporaryDirectory()
        self.addCleanup(empty.cleanup)
        self.assertEqual(run(empty.name).returncode, 2)


if __name__ == "__main__":
    unittest.main()
