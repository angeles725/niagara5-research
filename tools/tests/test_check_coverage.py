"""Tests for tools/check-coverage.py adapted for the N5 corpus.

N5 differs from the N4 kit tool in two ways this test locks down:
  1. Block glob is `niagara5-block*.md` (not `niagara-mental-model-bloque*.md`).
  2. Coverage also scans `RESEARCH-STATE*.md` files (gap backlogs), tagging each
     hit with its source kind ("block" vs "state") so callers can tell a mapped
     block from a merely-mentioned-in-the-backlog name apart.
"""
import importlib.util
import os
import sys
import tempfile
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "check_coverage_n5", os.path.join(TOOLS_DIR, "check-coverage.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCheckCoverageN5(unittest.TestCase):
    def setUp(self):
        self.mod = _load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        with open(os.path.join(root, "niagara5-block12.md"), "w") as fh:
            fh.write("# Block 12: FooModule internals\n\nBody text about FooModule.\n")
        with open(os.path.join(root, "niagara5-block13.md"), "w") as fh:
            fh.write("# Block 13: unrelated\n\nMentions BarModule in passing.\n")
        with open(os.path.join(root, "RESEARCH-STATE.md"), "w") as fh:
            fh.write("# Research State\n\nOpen gap: investigate BarModule further.\n")
        self.block_glob = os.path.join(root, "niagara5-block*.md")
        self.state_glob = os.path.join(root, "RESEARCH-STATE*.md")

    def test_block_glob_uses_niagara5_prefix_not_bloque(self):
        # The un-adapted N4 tool's BLOCK_GLOB looks for *-bloque*.md; the N5
        # tool must look for niagara5-block*.md instead.
        self.assertIn("niagara5-block", self.mod.BLOCK_GLOB)
        self.assertNotIn("bloque", self.mod.BLOCK_GLOB)

    def test_subject_hit_in_block_h1(self):
        results, nfiles = self.mod.scan(
            ["FooModule"], block_glob=self.block_glob, state_glob=self.state_glob
        )
        self.assertEqual(nfiles, 3)
        hits = results["FooModule"]["subject"]
        self.assertTrue(any(h["kind"] == "block" for h in hits))

    def test_state_file_hit_is_tagged_state_kind(self):
        results, _ = self.mod.scan(
            ["BarModule"], block_glob=self.block_glob, state_glob=self.state_glob
        )
        kinds = {h["kind"] for h in results["BarModule"]["body"]}
        self.assertIn("state", kinds)
        self.assertIn("block", kinds)  # also mentioned in block13 body

    def test_clear_name_has_no_hits(self):
        results, _ = self.mod.scan(
            ["TotallyAbsentName"], block_glob=self.block_glob, state_glob=self.state_glob
        )
        r = results["TotallyAbsentName"]
        self.assertEqual(r["subject"], [])
        self.assertEqual(r["body"], [])


if __name__ == "__main__":
    unittest.main()
