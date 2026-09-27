"""Unit tests for the N5 flat-layout inventory builder in build_module_inventory.py.

TDD note: these exercise `build_inventory_flat()`, which does not exist in the
ported N4 script yet -- they are expected to fail (RED) until the N5 port adds
it, then pass (GREEN).
"""

import json
import os
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

import build_module_inventory as bmi  # noqa: E402


def _write_recon(path, module="x", class_count=1, fallback_used=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "module": module,
        "jar_path": "/mnt/c/ProgramData/Niagara/tridium/config/5.0.0.28/modules/{}.jar".format(module),
        "class_count": class_count,
        "class_major_version_histogram": {"69": class_count},
        "signed": True,
        "obfuscation_heuristic": {"top_level_classes": class_count, "short_named": 0, "ratio": 0.0},
        "docsource_coverage": {"available": False, "covered": 0, "total": 0, "ratio": 0.0},
        "primary_decompiler": "vineflower-1.12.0",
        "primary_status": "ok",
        "fallback_decompiler": "cfr-0.152",
        "fallback_used": fallback_used,
        "fallback_reason": "cfr-fallback" if fallback_used else "none",
        "decompile_failure_markers": 0,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f)


def _make_module(root, name, java_rel="pkg/Foo.java", package="pkg"):
    mod_dir = os.path.join(root, name)
    vf_dir = os.path.join(mod_dir, "vineflower")
    os.makedirs(os.path.join(vf_dir, os.path.dirname(java_rel)), exist_ok=True)
    with open(os.path.join(vf_dir, java_rel), "w", encoding="utf-8") as f:
        f.write("package {};\n\npublic class Foo {{\n}}\n".format(package))
    _write_recon(os.path.join(mod_dir, "recon.json"), module=name, class_count=1)
    return mod_dir


class BuildInventoryFlatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.organized = os.path.join(self.tmp.name, "organized")
        os.makedirs(self.organized)

    def tearDown(self):
        self.tmp.cleanup()

    def test_flat_module_keyed_by_module_name_no_submodule_split(self):
        _make_module(self.organized, "baja")
        inventory, skipped = bmi.build_inventory_flat(self.organized)
        self.assertIn("baja", inventory)
        self.assertEqual(inventory["baja"]["module"], "baja")
        self.assertEqual(inventory["baja"]["class_count"], 1)
        self.assertTrue(inventory["baja"]["has_vineflower"])

    def test_bin_ext_module_keyed_with_prefix(self):
        os.makedirs(os.path.join(self.organized, "_bin-ext"))
        _make_module(os.path.join(self.organized, "_bin-ext"), "nre")
        inventory, skipped = bmi.build_inventory_flat(self.organized)
        self.assertIn("_bin-ext/nre", inventory)
        self.assertEqual(inventory["_bin-ext/nre"]["module"], "_bin-ext/nre")

    def test_non_module_top_dirs_skipped(self):
        os.makedirs(os.path.join(self.organized, "docSource", "whatever"))
        os.makedirs(os.path.join(self.organized, "_logs"))
        os.makedirs(os.path.join(self.organized, "_recon"))
        _make_module(self.organized, "baja")
        inventory, skipped = bmi.build_inventory_flat(self.organized)
        self.assertEqual(set(inventory.keys()), {"baja"})

    def test_reads_recon_json_directly_not_fase1(self):
        mod_dir = _make_module(self.organized, "baja")
        self.assertFalse(os.path.isfile(os.path.join(mod_dir, "pipeline", "fase1-recon.json")))
        inventory, skipped = bmi.build_inventory_flat(self.organized)
        self.assertIn("baja", inventory)
        self.assertEqual(skipped, [])

    def test_module_missing_recon_json_is_skipped_not_crashed(self):
        os.makedirs(os.path.join(self.organized, "broken", "vineflower"))
        _make_module(self.organized, "baja")
        inventory, skipped = bmi.build_inventory_flat(self.organized)
        self.assertNotIn("broken", inventory)
        self.assertIn("baja", inventory)


if __name__ == "__main__":
    unittest.main()
