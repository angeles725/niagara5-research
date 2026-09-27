"""Tests for tools/gen-catalog.py adapted for the N5 corpus.

N5 blocks are named `niagara5-block<N>.md` with English H1s ("# Block N: Title"
or "# Block N — Title"), unlike the N4 original which scanned
`niagara-mental-model-bloque<N>.md` with Spanish "Bloque" H1s. This test locks
down the filename pattern, the H1-title normalization, and that the tool
carries no leftover N4 TITLE_OVERRIDES content.
"""
import importlib.util
import os
import unittest

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load():
    spec = importlib.util.spec_from_file_location(
        "gen_catalog_n5", os.path.join(TOOLS_DIR, "gen-catalog.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGenCatalogN5(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_filename_pattern_matches_niagara5_block(self):
        parsed = self.mod.parse_filename("niagara5-block12.md")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["block_label"], "12")

    def test_filename_pattern_rejects_n4_bloque_name(self):
        parsed = self.mod.parse_filename("niagara-mental-model-bloque12.md")
        self.assertIsNone(parsed)

    def test_normalize_title_strips_block_prefix_english(self):
        title = self.mod.normalize_title("# Block 12: Alarm framework internals")
        self.assertEqual(title, "Alarm framework internals")

    def test_normalize_title_strips_em_dash_form(self):
        title = self.mod.normalize_title("# Block 12 — Alarm framework internals")
        self.assertEqual(title, "Alarm framework internals")

    def test_no_n4_title_overrides_leaked_into_n5_tool(self):
        # The N4 tool hardcoded ~15 Spanish block-title overrides (B27, B271...).
        # None of that content belongs in a fresh N5 corpus tool.
        self.assertEqual(self.mod.TITLE_OVERRIDES, {})


if __name__ == "__main__":
    unittest.main()
