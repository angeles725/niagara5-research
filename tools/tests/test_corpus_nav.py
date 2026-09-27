"""Tests for tools/corpus-nav.py adapted for the N5 corpus.

Locks down the N4 -> N5 filename/glob/regex adaptation: block files are
`niagara5-block<N>.md` (English H1 "Block N"), not the N4
`niagara-mental-model-bloque<N>.md` (Spanish "Bloque N"); there is no
consolidated "1-3" snapshot file; and block cross-references use `[Block N]`
/ `[BN]` forms (no Spanish "Bloque").
"""
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "corpus_nav_n5", os.path.join(TOOLS_DIR, "corpus-nav.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCorpusNavN5(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_block_label_for_niagara5_block_file(self):
        self.assertEqual(self.mod.block_label_for_file("niagara5-block12.md"), "12")

    def test_block_label_rejects_n4_bloque_file(self):
        self.assertIsNone(self.mod.block_label_for_file("niagara-mental-model-bloque12.md"))

    def test_no_consolidated_1_3_file_recognized(self):
        # N5 has no consolidated bloque-1-3 file; N4's name must not resolve.
        self.assertIsNone(self.mod.block_label_for_file("niagara-mental-model.md"))

    def test_ref_re_matches_block_and_b_forms(self):
        text = "See [Block 12] and [B34] for details."
        nums = [g for m in self.mod._REF_RE.finditer(text) for g in m.groups() if g]
        self.assertEqual(sorted(int(n) for n in nums), [12, 34])

    def test_ref_re_does_not_require_spanish_bloque(self):
        # Old N4 regex also matched bare "bloque106"; N5 corpus is English-only,
        # so the pattern should not special-case that Spanish form any more.
        pattern_src = self.mod._REF_RE.pattern
        self.assertNotIn("bloque", pattern_src.lower())

    def test_iter_block_files_globs_niagara5_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "niagara5-block1.md").write_text("# Block 1: X\n")
            (root / "niagara-mental-model-bloque1.md").write_text("# Bloque 1: Y\n")
            self.mod.REPO_ROOT = root
            files = self.mod.iter_block_files()
            names = {p.name for _, p in files}
            self.assertIn("niagara5-block1.md", names)
            self.assertNotIn("niagara-mental-model-bloque1.md", names)


if __name__ == "__main__":
    unittest.main()
