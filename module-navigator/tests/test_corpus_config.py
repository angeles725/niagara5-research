"""Unit tests for tools/corpus_config.py (N5 corpus dir/layout resolution)."""

import json
import os
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

import corpus_config as cc  # noqa: E402


class ResolveOrganizedDirTests(unittest.TestCase):
    def setUp(self):
        self._old_env = os.environ.get("NAV_ORGANIZED_DIR")

    def tearDown(self):
        if self._old_env is None:
            os.environ.pop("NAV_ORGANIZED_DIR", None)
        else:
            os.environ["NAV_ORGANIZED_DIR"] = self._old_env

    def test_cli_value_wins_over_env(self):
        os.environ["NAV_ORGANIZED_DIR"] = "/should/not/be/used"
        got = cc.resolve_organized_dir("/tmp/module-navigator", cli_value="/explicit/dir")
        self.assertEqual(got, "/explicit/dir")

    def test_env_var_used_when_no_cli(self):
        os.environ["NAV_ORGANIZED_DIR"] = "/from/env"
        got = cc.resolve_organized_dir("/tmp/module-navigator")
        self.assertEqual(got, "/from/env")

    def test_sibling_default_when_present(self):
        os.environ.pop("NAV_ORGANIZED_DIR", None)
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "module-navigator")
            organized = os.path.join(tmp, "organized")
            os.makedirs(base)
            os.makedirs(organized)
            got = cc.resolve_organized_dir(base)
            self.assertEqual(os.path.realpath(got), os.path.realpath(organized))

    def test_falls_back_to_inventory_source_when_no_sibling(self):
        os.environ.pop("NAV_ORGANIZED_DIR", None)
        with tempfile.TemporaryDirectory() as tmp:
            base = os.path.join(tmp, "module-navigator")
            os.makedirs(os.path.join(base, "indexes"))
            with open(os.path.join(base, "indexes", "module-inventory.json"), "w") as f:
                json.dump({"_meta": {"source": "/some/prior/corpus"}}, f)
            got = cc.resolve_organized_dir(base)
            self.assertEqual(got, "/some/prior/corpus")

    def test_no_n4_literal_in_resolution(self):
        # The whole point of this module: never return/contain N4's absolute path.
        with open(cc.__file__) as f:
            src = f.read()
        self.assertNotIn("/home/cristian/modules", src)
        self.assertNotIn("Prototipos", src)


class ResolveLayoutTests(unittest.TestCase):
    def test_defaults_to_flat(self):
        self.assertEqual(cc.resolve_layout(), "flat")

    def test_cli_value_respected(self):
        self.assertEqual(cc.resolve_layout("n4"), "n4")

    def test_invalid_value_raises(self):
        with self.assertRaises(ValueError):
            cc.resolve_layout("bogus")


class IterFlatModuleDirsTests(unittest.TestCase):
    def test_skips_housekeeping_dirs_and_finds_bin_ext(self):
        with tempfile.TemporaryDirectory() as tmp:
            organized = os.path.join(tmp, "organized")
            os.makedirs(os.path.join(organized, "docSource", "whatever"))
            os.makedirs(os.path.join(organized, "_logs"))
            os.makedirs(os.path.join(organized, "_recon"))
            os.makedirs(os.path.join(organized, "baja"))
            with open(os.path.join(organized, "baja", "recon.json"), "w") as f:
                f.write("{}")
            os.makedirs(os.path.join(organized, "_bin-ext", "nre"))
            with open(os.path.join(organized, "_bin-ext", "nre", "recon.json"), "w") as f:
                f.write("{}")
            found = dict(cc.iter_flat_module_dirs(organized))
            self.assertEqual(set(found.keys()), {"baja", "_bin-ext/nre"})
            self.assertTrue(found["_bin-ext/nre"].endswith(os.path.join("_bin-ext", "nre")))


if __name__ == "__main__":
    unittest.main()
