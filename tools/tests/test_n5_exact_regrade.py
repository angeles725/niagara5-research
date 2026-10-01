#!/usr/bin/env python3
"""tools/n5-exact-regrade.py (C4): best-of population, exact targets, per-rule census, a regrade of
classes that are already proven (canonical) but not exact through the official splice rung, and the
0-regression recount."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("n5_exact_regrade", TOOLS_DIR / "n5-exact-regrade.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def rec(grade, rules=(), engine="vineflower2"):
    return {"grade": grade, "best_decompiler": engine, "canonical_rules": list(rules),
            "canonical_methods": [["m", "()V"]] if rules else [], "first_error": None, "attempted": []}


def write_module(org: Path, mod: str, rungs: dict):
    d = org / mod
    d.mkdir(parents=True)
    for rung, classes in rungs.items():
        (d / f"fidelity.{rung}.json").write_text(json.dumps({"module": mod, "classes": classes}))


class TestPopulation(unittest.TestCase):
    def setUp(self):
        self.m = _load()
        self.td = tempfile.TemporaryDirectory()
        self.org = Path(self.td.name)
        write_module(self.org, "a", {
            "vineflower2": {"p/A": rec("roundtrip-canonical", ["tail"]), "p/B": rec("no-compile"),
                            "p/C": rec("roundtrip-exact")},
            "vineflower2.spliced": {"p/B": rec("roundtrip-canonical-t2", ["boolmat"], "vineflower2s")}})
        write_module(self.org, "b", {"vineflower2": {"q/D": rec("roundtrip-equivalent"),
                                                     "q/E": rec("bytecode-only")}})

    def tearDown(self):
        self.td.cleanup()

    def test_best_of_merges_rungs_across_files(self):
        best = self.m.load_best(self.org)
        self.assertEqual(best[("a", "p/B")]["grade"], "roundtrip-canonical-t2")
        self.assertEqual(len(best), 5)

    def test_targets_are_proven_but_not_exact(self):
        best = self.m.load_best(self.org)
        self.assertEqual(self.m.exact_targets(best), [("a", "p/A"), ("a", "p/B"), ("b", "q/D")])

    def test_rule_census_counts_classes_per_rule_and_rule_set(self):
        best = self.m.load_best(self.org)
        census = self.m.rule_census(best)
        self.assertEqual(census["rules"], {"tail": 1, "boolmat": 1})
        self.assertEqual(census["no_rules"], 1)
        self.assertEqual(census["sets"], {("tail",): 1, ("boolmat",): 1})

    def test_recount_reports_counts_improvements_and_regressions(self):
        before = self.m.load_best(self.org)
        after = {k: dict(v) for k, v in before.items()}
        after[("a", "p/A")]["grade"] = "roundtrip-exact"      # improved
        after[("b", "q/E")]["grade"] = "no-compile"           # bytecode-only (1) -> no-compile (0): regressed
        out = self.m.recount(before, after)
        self.assertEqual(out["improved"], [("a", "p/A")])
        self.assertEqual(out["regressed"], [("b", "q/E")])
        self.assertEqual(out["after"]["roundtrip-exact"], 2)
        self.assertEqual(out["before"]["roundtrip-canonical"], 1)


class TestRegrade(unittest.TestCase):
    """A class that is clean (canonical) at baseline is regraded through the official splice rung."""

    def setUp(self):
        self.m = _load()
        self.td = tempfile.TemporaryDirectory()
        self.org = Path(self.td.name)
        write_module(self.org, "a", {
            "vineflower2": {"p/A": rec("roundtrip-canonical", ["tail"]), "p/B": rec("roundtrip-canonical", ["min"])}})
        (self.org / "a" / "extracted" / "p").mkdir(parents=True)
        for c in ("A", "B"):
            (self.org / "a" / "extracted" / "p" / f"{c}.class").write_bytes(b"\xca\xfe")
            (self.org / "a" / "vineflower2s" / "p").mkdir(parents=True, exist_ok=True)
            (self.org / "a" / "vineflower2s" / "p" / f"{c}.java").write_text("class X {}")
        (self.org / "a" / "vineflower2s" / "SPLICES.json").write_text("{}")

    def tearDown(self):
        self.td.cleanup()

    def fake(self, exact):
        def grade(fqcn, classfile, **kw):
            return fqcn, rec("roundtrip-exact" if fqcn in exact else "roundtrip-canonical", (), "vineflower2s")
        return grade

    def test_clean_baseline_class_is_regraded_and_merged_into_the_spliced_json(self):
        out = self.m.regrade_module(self.org, "a", ["p/A", "p/B"], grade_fn=self.fake({"p/A"}))
        self.assertEqual(out, {"replaced": 2, "kept": 0})
        merged = json.loads((self.org / "a" / "fidelity.vineflower2.spliced.json").read_text())
        self.assertEqual(merged["classes"]["p/A"]["grade"], "roundtrip-exact")
        self.assertEqual(merged["classes"]["p/A"]["previous_grade"], "roundtrip-canonical")
        self.assertEqual(sorted(merged["regraded_classes"]), ["p/A", "p/B"])
        best = self.m.load_best(self.org)
        self.assertEqual(best[("a", "p/A")]["grade"], "roundtrip-exact")
        self.assertEqual(self.m.exact_targets(best), [("a", "p/B")])

    def test_a_lower_ranking_result_never_replaces_an_existing_record(self):
        self.m.regrade_module(self.org, "a", ["p/A"], grade_fn=self.fake({"p/A"}))
        out = self.m.regrade_module(self.org, "a", ["p/A"], grade_fn=self.fake(set()))
        self.assertEqual(out, {"replaced": 0, "kept": 1})
        merged = json.loads((self.org / "a" / "fidelity.vineflower2.spliced.json").read_text())
        self.assertEqual(merged["classes"]["p/A"]["grade"], "roundtrip-exact")

    def test_real_baseline_json_is_never_modified(self):
        path = self.org / "a" / "fidelity.vineflower2.json"
        before = path.read_bytes()
        self.m.regrade_module(self.org, "a", ["p/A"], grade_fn=self.fake({"p/A"}))
        self.assertEqual(path.read_bytes(), before)
