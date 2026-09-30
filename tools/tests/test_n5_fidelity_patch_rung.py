#!/usr/bin/env python3
"""The patch-tree rung of tools/n5-fidelity.py (T21/F8): a mechanically patched
source (tools/n5-patch-doprivileged.py, organized/<mod>/<patch-tree>/) is graded
as its own ladder rung right after the primary tree, recorded under its own
engine label, and a class counts as patched only when that rung's grade is the
class grade."""
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
BROKEN = 'package p;\npublic class Foo {\n  static int f(int a, int b) { return a - ; }\n}\n'
WRONG = 'package p;\npublic class Foo {\n  static int f(int a, int b) { return b - a; }\n}\n'


class _Fixture:
    def __init__(self, td: str, primary: str, patched):
        self.root = Path(td)
        self.organized = self.root / "organized"
        self.mod_dir = self.organized / "m"
        (self.mod_dir / "extracted" / "p").mkdir(parents=True)
        (self.mod_dir / "vineflower2" / "p").mkdir(parents=True)
        src = self.root / "src" / "p" / "Foo.java"
        src.parent.mkdir(parents=True)
        src.write_text(GOOD)
        subprocess.run([JAVAC, "--release", "25", "-g", "-d", str(self.root / "g"), str(src)],
                       check=True, capture_output=True)
        shutil.copy(self.root / "g" / "p" / "Foo.class", self.mod_dir / "extracted" / "p" / "Foo.class")
        (self.mod_dir / "vineflower2" / "p" / "Foo.java").write_text(primary)
        if patched is not None:
            (self.mod_dir / "vineflower2p" / "p").mkdir(parents=True)
            (self.mod_dir / "vineflower2p" / "p" / "Foo.java").write_text(patched)
            (self.mod_dir / "vineflower2p" / "PATCHES.json").write_text(json.dumps({"schema": 1, "classes": {}}))
        (self.mod_dir / "recon.json").write_text(json.dumps({"jar_sha256": "j"}))


@unittest.skipUnless(os.path.isfile(JAVAC) and os.path.isfile(JAVAP), "JDK 25 not installed")
class TestPatchRung(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def _grade(self, fx, patch_tree="vineflower2p", decompile=(None, None)):
        calls = []

        def fake_decompile(java_bin, engine, tool_jar, classfile, out_dir):
            calls.append(engine)
            return decompile
        with mock.patch.object(self.mod, "_decompile_one_class_with", side_effect=fake_decompile):
            res = self.mod.grade_module("m", organized_dir=fx.organized, classpath="", primary_tree="vineflower2",
                                        javac_bin=JAVAC, javap_bin=JAVAP, patch_tree=patch_tree)
        return res["classes"]["p/Foo"], calls

    def test_patch_rung_follows_the_primary_tree_and_stops_the_ladder(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, BROKEN, GOOD)
            rec, calls = self._grade(fx)
            self.assertEqual(rec["attempted"], [("vineflower2", "no-compile"), ("vineflower2p", "roundtrip-exact")])
            self.assertEqual(calls, [])
            self.assertEqual((rec["grade"], rec["best_decompiler"]), ("roundtrip-exact", "vineflower2p"))
            self.assertTrue(rec["patched"])
            self.assertEqual(rec["patch"]["manifest"], "vineflower2p/PATCHES.json")
            self.assertEqual(rec["patch"]["patched_sha256"],
                             self.mod.sha256_of(fx.mod_dir / "vineflower2p" / "p" / "Foo.java"))

    def test_a_non_clean_patch_rung_is_recorded_but_not_patched(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, BROKEN, WRONG)
            rec, calls = self._grade(fx)
            self.assertEqual(rec["attempted"][:2], [("vineflower2", "no-compile"), ("vineflower2p", "compiles-mismatch")])
            self.assertEqual(calls, ["cfr", "procyon"])
            self.assertFalse(rec["patched"])
            self.assertNotIn("patch", rec)

    def test_no_patch_file_means_no_rung(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, BROKEN, None)
            rec, _ = self._grade(fx)
            self.assertEqual([n for n, _g in rec["attempted"]], ["vineflower2", "cfr", "procyon"])
            self.assertFalse(rec["patched"])

    def test_without_patch_tree_the_record_is_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, BROKEN, GOOD)
            rec, _ = self._grade(fx, patch_tree=None)
            self.assertNotIn("patched", rec)
            self.assertEqual([n for n, _g in rec["attempted"]], ["vineflower2", "cfr", "procyon"])

    def test_primary_exact_skips_the_patch_rung(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, GOOD, GOOD)
            rec, _ = self._grade(fx)
            self.assertEqual(rec["attempted"], [("vineflower2", "roundtrip-exact")])
            self.assertFalse(rec["patched"])


@unittest.skipUnless(os.path.isfile(JAVAC) and os.path.isfile(JAVAP), "JDK 25 not installed")
class TestRecordDetailFollowsMostAdvancedRung(unittest.TestCase):
    """C3a-G3: the record's first_error / mismatch detail belongs to the most advanced rung at the
    best rank, never to a stale lower rung; every rung's own error stays in rung_errors."""

    def setUp(self):
        self.mod = _load()
        self.helper = TestPatchRung._grade

    def _grade(self, fx, decompile=(None, None)):
        return self.helper(self, fx, decompile=decompile)

    def test_patched_rung_that_compiles_supersedes_the_stale_primary_error(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, BROKEN, WRONG)
            rec, _ = self._grade(fx)
            self.assertEqual(rec["grade"], "bytecode-only")
            self.assertIsNone(rec["first_error"])
            self.assertEqual(rec["detail_rung"], "vineflower2p")
            self.assertEqual(rec["mismatched_methods"], [["f", "(II)I"]])
            self.assertIn("vineflower2", rec["rung_errors"])
            self.assertNotIn("vineflower2p", rec["rung_errors"])

    def test_proven_class_carries_no_first_error_from_a_lower_rung(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, BROKEN, GOOD)
            rec, _ = self._grade(fx)
            self.assertEqual(rec["grade"], "roundtrip-exact")
            self.assertIsNone(rec["first_error"])
            self.assertIn("vineflower2", rec["rung_errors"])

    def test_no_compile_everywhere_reports_the_most_advanced_rung_error(self):
        with tempfile.TemporaryDirectory() as td:
            fx = _Fixture(td, "package p;\npublic class Foo { int x = \"s\"; }\n", BROKEN)
            rec, _ = self._grade(fx)
            self.assertEqual(rec["detail_rung"], "vineflower2p")
            self.assertEqual(rec["first_error"], rec["rung_errors"]["vineflower2p"])
            self.assertNotEqual(rec["rung_errors"]["vineflower2"], rec["rung_errors"]["vineflower2p"])


class TestMergeBestOfRecords(unittest.TestCase):
    """The cross-JSON best-of (fidelity.<rung>.json files): rank first, a tie goes to the most
    advanced rung (spliced > patched > canon > vineflower2 > vineflower)."""

    def setUp(self):
        self.mod = _load()

    def rec(self, grade, err=None, mm=()):
        return {"grade": grade, "first_error": err, "mismatched_methods": [list(m) for m in mm]}

    def test_tie_goes_to_the_most_advanced_rung_and_keeps_every_error(self):
        out = self.mod.merge_best_of_records({
            "vineflower": self.rec("no-compile", "v1 err"),
            "vineflower2": self.rec("no-compile", "reference to doPrivileged is ambiguous"),
            "vineflower2.patched": self.rec("no-compile", "cannot find symbol"),
        })
        self.assertEqual(out["first_error"], "cannot find symbol")
        self.assertEqual(out["detail_rung"], "vineflower2.patched")
        self.assertEqual(out["rung_errors"], {"vineflower": "v1 err",
                                              "vineflower2": "reference to doPrivileged is ambiguous",
                                              "vineflower2.patched": "cannot find symbol"})

    def test_higher_rank_beats_advancement(self):
        out = self.mod.merge_best_of_records({
            "vineflower2": self.rec("compiles-mismatch", None, [("m", "()V")]),
            "vineflower2.spliced": self.rec("no-compile", "boom"),
        })
        self.assertEqual(out["detail_rung"], "vineflower2")
        self.assertIsNone(out["first_error"])
        self.assertEqual(out["mismatched_methods"], [["m", "()V"]])
        self.assertEqual(out["rung_errors"], {"vineflower2.spliced": "boom"})

    def test_spliced_wins_a_mismatch_tie(self):
        out = self.mod.merge_best_of_records({
            "vineflower2.patched": self.rec("compiles-mismatch", None, [("a", "()V")]),
            "vineflower2.spliced": self.rec("compiles-mismatch", None, [("b", "()V")]),
        })
        self.assertEqual(out["detail_rung"], "vineflower2.spliced")
        self.assertEqual(out["mismatched_methods"], [["b", "()V"]])

    def test_proven_record_has_no_first_error(self):
        out = self.mod.merge_best_of_records({
            "vineflower2": self.rec("no-compile", "old"),
            "vineflower2.canon": self.rec("roundtrip-canonical"),
        })
        self.assertIsNone(out["first_error"])
        self.assertEqual(out["rung_errors"], {"vineflower2": "old"})


class TestRegradeWithPatchTree(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def _setup(self, td):
        mod_dir = Path(td) / "m"
        (mod_dir / "vineflower2p" / "p").mkdir(parents=True)
        (mod_dir / "vineflower2p" / "p" / "B.java").write_text("class B {}\n")
        (mod_dir / "vineflower2p" / "PATCHES.json").write_text(json.dumps({"schema": 1, "classes": {"p/B": {}}}))
        src = {"module": "m", "schema_version": 2, "jar_sha256": "j", "primary_tree": "vineflower2",
               "class_count": 3, "grade_counts": {}, "limit_per_module": None,
               "classes": {"p/A": {"grade": "roundtrip-exact"}, "p/B": {"grade": "bytecode-only"},
                           "p/C": {"grade": "bytecode-only"}}}
        (mod_dir / "fidelity.vineflower2.json").write_text(json.dumps(src))
        return mod_dir

    def _grader(self, calls):
        def grade(fqcn, classfile, **kwargs):
            calls.append((fqcn, kwargs.get("patch_tree"), kwargs.get("patch_dir")))
            return fqcn, {"grade": "roundtrip-exact", "patched": True}
        return grade

    def test_only_nonclean_classes_with_a_patch_are_regraded_into_the_patched_file(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = self._setup(td)
            calls = []
            out = self.mod.regrade_nonclean_module("m", organized_dir=Path(td), tree="vineflower2",
                                                   grade_fn=self._grader(calls), patch_tree="vineflower2p")
            self.assertEqual([c[0] for c in calls], ["p/B"])
            path = mod_dir / "fidelity.vineflower2.patched.json"
            self.assertEqual(self.mod.patched_output_path(mod_dir, "vineflower2"), path)
            written = json.loads(path.read_text())
            self.assertEqual(written, json.loads(json.dumps(out)))
            self.assertEqual(written["patch_tree"], "vineflower2p")
            self.assertEqual(written["patch_manifest_sha256"],
                             self.mod.sha256_of(mod_dir / "vineflower2p" / "PATCHES.json"))
            self.assertEqual(written["classes"]["p/C"], {"grade": "bytecode-only"})
            self.assertEqual(written["classes"]["p/B"]["previous_grade"], "bytecode-only")
            self.assertFalse((mod_dir / "fidelity.vineflower2.canon.json").exists())

    def test_default_grader_gets_the_patch_dir(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = self._setup(td)
            seen = []

            def fake(fqcn, classfile, **kwargs):
                seen.append((kwargs["patch_tree"], kwargs["patch_dir"]))
                return fqcn, {"grade": "bytecode-only"}
            with mock.patch.object(self.mod, "_grade_one_class", side_effect=fake):
                self.mod.regrade_nonclean_module("m", organized_dir=Path(td), tree="vineflower2",
                                                 patch_tree="vineflower2p", classpath="")
            self.assertEqual(seen, [("vineflower2p", mod_dir / "vineflower2p")])

    def test_changed_patch_manifest_invalidates_the_patched_file(self):
        with tempfile.TemporaryDirectory() as td:
            mod_dir = self._setup(td)
            calls = []
            self.mod.regrade_nonclean_module("m", organized_dir=Path(td), tree="vineflower2",
                                             grade_fn=self._grader(calls), patch_tree="vineflower2p")
            self.mod.regrade_nonclean_module("m", organized_dir=Path(td), tree="vineflower2",
                                             grade_fn=self._grader(calls), patch_tree="vineflower2p")
            self.assertEqual(len(calls), 1)
            (mod_dir / "vineflower2p" / "PATCHES.json").write_text(json.dumps({"schema": 1, "classes": {"x": {}}}))
            self.mod.regrade_nonclean_module("m", organized_dir=Path(td), tree="vineflower2",
                                             grade_fn=self._grader(calls), patch_tree="vineflower2p")
            self.assertEqual(len(calls), 2)


class TestPatchTreeCli(unittest.TestCase):
    def test_patch_tree_is_only_accepted_with_regrade_nonclean(self):
        mod = _load()
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            mod.main(["--modules", "m", "--tree", "vineflower2", "--patch-tree", "vineflower2p"])


if __name__ == "__main__":
    unittest.main()
