#!/usr/bin/env python3
"""The splice-tree rung of tools/n5-fidelity.py (T21/F9): a per-method spliced
source (tools/n5-splice-methods.py, organized/<mod>/<tree>s/ + SPLICES.json) is
graded through the same --patch-tree machinery as F8's patch tree, but under its
own label: the output is fidelity.<tree>.spliced.json (never the F8
fidelity.<tree>.patched.json), the cache key is SPLICES.json, and a class
counts as spliced only when the splice rung's grade IS the class grade."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-fidelity.py")
JAVAC = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"
JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"


def _load():
    spec = importlib.util.spec_from_file_location("n5_fidelity", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


GOOD = 'package p;\npublic class Foo {\n  static int f(int a, int b) { return a - b; }\n}\n'
WRONG = 'package p;\npublic class Foo {\n  static int f(int a, int b) { return b - a; }\n}\n'
DONORS = {"p/Foo": {"methods": [{"name": "f", "descriptor": "(II)I", "donor": "cfr", "reason": "exact"}]}}


class TestLabels(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_tree_plus_s_is_the_splice_label_and_manifest(self):
        self.assertEqual(self.mod.patch_output_label("vineflower2", "vineflower2s"), "spliced")
        self.assertEqual(self.mod.patch_output_label("vineflower2", "vineflower2p"), "patched")
        self.assertEqual(self.mod.patch_manifest_name("vineflower2", "vineflower2s"), "SPLICES.json")
        self.assertEqual(self.mod.patch_manifest_name("vineflower2", "vineflower2p"), "PATCHES.json")
        d = Path("/x/m")
        self.assertEqual(self.mod.patch_output_path(d, "vineflower2", "vineflower2s"),
                         d / "fidelity.vineflower2.spliced.json")
        self.assertEqual(self.mod.patch_output_path(d, "vineflower2", "vineflower2p"),
                         d / "fidelity.vineflower2.patched.json")


@unittest.skipUnless(os.path.isfile(JAVAC) and os.path.isfile(JAVAP), "JDK 25 not installed")
class TestSpliceRung(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def _fixture(self, td, primary, spliced):
        root = Path(td)
        mod_dir = root / "organized" / "m"
        (mod_dir / "extracted" / "p").mkdir(parents=True)
        (mod_dir / "vineflower2" / "p").mkdir(parents=True)
        src = root / "src" / "p" / "Foo.java"
        src.parent.mkdir(parents=True)
        src.write_text(GOOD)
        subprocess.run([JAVAC, "--release", "25", "-g", "-d", str(root / "g"), str(src)], check=True,
                       capture_output=True)
        shutil.copy(root / "g" / "p" / "Foo.class", mod_dir / "extracted" / "p" / "Foo.class")
        (mod_dir / "vineflower2" / "p" / "Foo.java").write_text(primary)
        (mod_dir / "vineflower2s" / "p").mkdir(parents=True)
        (mod_dir / "vineflower2s" / "p" / "Foo.java").write_text(spliced)
        (mod_dir / "vineflower2s" / "SPLICES.json").write_text(json.dumps({"schema": 1, "classes": DONORS}))
        return root / "organized", mod_dir

    def _grade(self, organized):
        with mock.patch.object(self.mod, "_decompile_one_class_with", return_value=(None, None)):
            res = self.mod.grade_module("m", organized_dir=organized, classpath="", primary_tree="vineflower2",
                                        javac_bin=JAVAC, javap_bin=JAVAP, patch_tree="vineflower2s")
        return res["classes"]["p/Foo"]

    def test_clean_splice_rung_records_spliced_and_donors(self):
        with tempfile.TemporaryDirectory() as td:
            organized, mod_dir = self._fixture(td, WRONG, GOOD)
            rec = self._grade(organized)
            self.assertEqual(rec["attempted"], [("vineflower2", "compiles-mismatch"),
                                                ("vineflower2s", "roundtrip-exact")])
            self.assertTrue(rec["spliced"])
            self.assertNotIn("patched", rec)
            self.assertEqual(rec["splice"]["manifest"], "vineflower2s/SPLICES.json")
            self.assertEqual(rec["splice"]["spliced_sha256"],
                             self.mod.sha256_of(mod_dir / "vineflower2s" / "p" / "Foo.java"))
            self.assertEqual(rec["splice"]["donors"], DONORS["p/Foo"]["methods"])

    def test_a_non_clean_splice_is_not_spliced(self):
        with tempfile.TemporaryDirectory() as td:
            organized, _ = self._fixture(td, WRONG, WRONG)
            rec = self._grade(organized)
            self.assertEqual(rec["attempted"][1], ("vineflower2s", "compiles-mismatch"))
            self.assertEqual(rec["grade"], "bytecode-only")
            self.assertFalse(rec["spliced"])
            self.assertNotIn("splice", rec)


class TestRegradeWithSpliceTree(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_output_is_the_spliced_file_keyed_on_splices_json(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = Path(td) / "m"
            (mod_dir / "vineflower2s" / "p").mkdir(parents=True)
            (mod_dir / "vineflower2s" / "p" / "B.java").write_text("class B {}\n")
            (mod_dir / "vineflower2s" / "SPLICES.json").write_text(json.dumps({"schema": 1, "classes": {}}))
            patched = mod_dir / "fidelity.vineflower2.patched.json"
            src = {"module": "m", "schema_version": 2, "classes": {"p/A": {"grade": "roundtrip-exact"},
                                                                   "p/B": {"grade": "bytecode-only"}}}
            (mod_dir / "fidelity.vineflower2.json").write_text(json.dumps(src))
            patched.write_text("{}")
            calls = []

            def grade(fqcn, classfile, **kwargs):
                calls.append(fqcn)
                return fqcn, {"grade": "roundtrip-exact", "spliced": True}
            out = self.mod.regrade_nonclean_module("m", organized_dir=Path(td), tree="vineflower2",
                                                   grade_fn=grade, patch_tree="vineflower2s")
            self.assertEqual(calls, ["p/B"])
            written = json.loads((mod_dir / "fidelity.vineflower2.spliced.json").read_text())
            self.assertEqual(written, json.loads(json.dumps(out)))
            self.assertEqual(written["patch_manifest_sha256"],
                             self.mod.sha256_of(mod_dir / "vineflower2s" / "SPLICES.json"))
            self.assertEqual(patched.read_text(), "{}")


if __name__ == "__main__":
    unittest.main()
