"""Unit tests for the N5 flat-layout class index builder (fallback/ overlay).

TDD note: build_class_index() in the ported N4 script assumes an
organized/<module>/<submodule>/vineflower/ layout. These tests exercise the
N5 flat layout (organized/<module>/{vineflower,fallback}/) with a
fallback-overlay class (present only under fallback/, i.e. vineflower failed
to decompile it) -- expected to fail (RED) until the port adds flat-layout +
overlay support, then pass (GREEN).
"""

import json
import os
import sys
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))

import build_class_index as bci  # noqa: E402


def _make_flat_corpus_with_fallback(tmp_root):
    organized = os.path.join(tmp_root, "organized")
    mod = os.path.join(organized, "acme")
    vf = os.path.join(mod, "vineflower", "pkg")
    fb = os.path.join(mod, "fallback", "pkg")
    os.makedirs(vf)
    os.makedirs(fb)

    with open(os.path.join(vf, "Foo.java"), "w", encoding="utf-8") as f:
        f.write("package pkg;\n\npublic class Foo {\n}\n")

    # Bar.java exists ONLY in fallback/ -- vineflower failed to decompile it.
    with open(os.path.join(fb, "Bar.java"), "w", encoding="utf-8") as f:
        f.write("package pkg;\n\npublic class Bar {\n}\n")

    # Foo.java ALSO exists in fallback/ (stale/duplicate) -- vineflower must win.
    with open(os.path.join(fb, "Foo.java"), "w", encoding="utf-8") as f:
        f.write("package pkg;\n\npublic class FooFallbackDuplicate {\n}\n")

    with open(os.path.join(mod, "recon.json"), "w", encoding="utf-8") as f:
        json.dump({"module": "acme", "class_count": 2, "fallback_used": True}, f)

    return organized


class BuildClassIndexFlatTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base_dir = os.path.join(self.tmp.name, "module-navigator")
        os.makedirs(os.path.join(self.base_dir, "indexes"))
        self.organized = _make_flat_corpus_with_fallback(self.tmp.name)

        inventory = {
            "_meta": {"source": self.organized, "layout": "flat"},
            "modules": {
                "acme": {
                    "module": "acme",
                    "type": "",
                    "jar": "acme.jar",
                    "class_count": 2,
                    "java_files": 1,
                    "zkm": False,
                    "bytecode": 69,
                    "has_vineflower": True,
                    "has_cfr": True,
                    "has_code": True,
                    "packages": ["pkg"],
                    "third_party": [],
                }
            },
        }
        with open(os.path.join(self.base_dir, "indexes", "module-inventory.json"), "w", encoding="utf-8") as f:
            json.dump(inventory, f)

    def tearDown(self):
        self.tmp.cleanup()

    def test_vineflower_class_is_indexed_and_resolves_to_real_file(self):
        classes, stats = bci.build_class_index(self.base_dir, self.organized)
        self.assertIn("Foo", classes)
        entry = classes["Foo"][0]
        full = os.path.join(self.organized, entry["path"])
        self.assertTrue(os.path.isfile(full))
        with open(full, encoding="utf-8") as f:
            self.assertIn("class Foo", f.read())

    def test_fallback_overlay_fills_class_vineflower_failed_on(self):
        classes, stats = bci.build_class_index(self.base_dir, self.organized)
        self.assertIn("Bar", classes)
        entry = classes["Bar"][0]
        self.assertIn("fallback", entry["path"])
        full = os.path.join(self.organized, entry["path"])
        self.assertTrue(os.path.isfile(full))

    def test_vineflower_wins_over_fallback_duplicate_for_same_relpath(self):
        classes, stats = bci.build_class_index(self.base_dir, self.organized)
        self.assertEqual(len(classes["Foo"]), 1)
        self.assertIn(os.path.join("vineflower", "pkg", "Foo.java").replace("\\", "/"),
                       classes["Foo"][0]["path"].replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
