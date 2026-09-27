"""Tests for tools/obix-nav.py adapted for the N5 corpus.

The N4 original hardcoded PANCCADIA-specific defaults for --base (the JACE's
oBIX endpoint) and --pass-file (a scratchpad path from a past N4 session).
Neither default applies to any N5 target — --base and --pass-file must be
required, explicit arguments so the tool never silently points at a stale,
unrelated station.
"""
import os
import subprocess
import sys
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "obix-nav.py")


class TestObixNavN5(unittest.TestCase):
    def test_no_hardcoded_base_default(self):
        with open(SCRIPT, encoding="utf-8") as fh:
            src = fh.read()
        # No DEFAULT_BASE/DEFAULT_PASS constant left to fall back to (a mention
        # of the old N4 default value in porting-history prose is fine).
        self.assertNotIn("DEFAULT_BASE", src)
        self.assertNotIn("DEFAULT_PASS", src)
        self.assertNotIn("scratchpad/.obix_pass", src)

    def test_missing_base_and_pass_file_errors(self):
        # No --base / --pass-file given: argparse must refuse (required=True),
        # not silently fall back to a PANCCADIA default.
        r = subprocess.run(
            [sys.executable, SCRIPT, "cond"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--base", r.stderr)

    def test_help_shows_required_base_and_pass_file(self):
        r = subprocess.run(
            [sys.executable, SCRIPT, "-h"],
            capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--base", r.stdout)
        self.assertIn("--pass-file", r.stdout)


if __name__ == "__main__":
    unittest.main()
