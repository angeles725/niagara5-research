#!/usr/bin/env python3
"""load_best_of_module_result (tools/n5-fidelity.py, C2a-G1): one module's best-of over its rung files
fidelity.<tree>.json, .canon, .patched, .mech (--patch-label mech) and .spliced, with the summary
fields the report sections read. A rung file that is absent is skipped; a class missing from a rung
keeps the other rungs' records."""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-fidelity.py")


def _load():
    spec = importlib.util.spec_from_file_location("n5_fidelity", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def rec(grade, **kw):
    r = {"grade": grade, "nested": {"files": {}, "missing": [], "extra": [], "drift_suspected": False}}
    r["fully_proven"] = grade.startswith("roundtrip")
    r.update(kw)
    return r


def write(mod_dir, label, classes):
    name = "fidelity.vineflower2.json" if label is None else f"fidelity.vineflower2.{label}.json"
    (Path(mod_dir) / name).write_text(json.dumps({"module": "m", "classes": classes}))


class BestOfModuleTest(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def test_rung_order_includes_the_mech_label_before_spliced(self):
        r = self.m.BEST_OF_RUNGS
        self.assertLess(r.index("vineflower2.patched"), r.index("vineflower2.mech"))
        self.assertLess(r.index("vineflower2.mech"), r.index("vineflower2.spliced"))

    def test_best_grade_wins_across_rungs_and_counts_are_recomputed(self):
        with tempfile.TemporaryDirectory() as td:
            write(td, None, {"a/A": rec("bytecode-only"), "a/B": rec("roundtrip-exact"),
                             "a/C": rec("bytecode-only"), "a/D": rec("bytecode-only")})
            write(td, "patched", {"a/A": rec("roundtrip-canonical")})
            write(td, "mech", {"a/A": rec("bytecode-only"), "a/C": rec("roundtrip-exact")})
            write(td, "spliced", {"a/D": rec("roundtrip-canonical")})
            res = self.m.load_best_of_module_result(Path(td), "vineflower2", module="m")
        self.assertEqual(res["module"], "m")
        self.assertEqual(res["class_count"], 4)
        self.assertEqual(res["grade_counts"], {"roundtrip-canonical": 2, "roundtrip-exact": 2})
        self.assertEqual(res["classes"]["a/A"]["detail_rung"], "vineflower2.patched")
        self.assertEqual(res["fully_proven_count"], 4)

    def test_missing_base_file_is_none(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertIsNone(self.m.load_best_of_module_result(Path(td), "vineflower2", module="m"))

    def test_bin_ext_loader_reads_the_best_of(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "_bin-ext" / "nre"
            d.mkdir(parents=True)
            (d / "recon.json").write_text(json.dumps({"signature_file": "NIAGARA4.SF"}))
            write(d, None, {"a/A": rec("bytecode-only")})
            write(d, "spliced", {"a/A": rec("roundtrip-exact")})
            out = self.m.load_bin_ext_results(Path(td), best_of=True)
        self.assertEqual([r["grade_counts"] for r in out], [{"roundtrip-exact": 1}])


if __name__ == "__main__":
    unittest.main()
