#!/usr/bin/env python3
"""tools/n5-vineflower-variants.py (C3d): per-flag Vineflower decompile variants of chosen classes,
written as `organized/<mod>/vf2v-<variant>/` trees that the splice uses as donors."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("n5_vineflower_variants", TOOLS_DIR / "n5-vineflower-variants.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestVariants(unittest.TestCase):
    def setUp(self):
        self.mod = _load()

    def test_command_keeps_the_v2_flags_then_the_variant_flag_and_the_libraries_last(self):
        cmd = self.mod.build_command("ir0", Path("/in"), Path("/out"), ["/l/a.jar", "/l/b.jar"],
                                     java="java", vineflower="vf.jar", jdk_home="/jdk")
        self.assertEqual(cmd[:3], ["java", "-Xmx4g", "-jar"])
        self.assertIn("--use-lvt-names=true", cmd)
        self.assertIn("--include-runtime=/jdk", cmd)
        self.assertLess(cmd.index("--use-lvt-names=true"), cmd.index("--incorporate-returns=false"))
        self.assertEqual(cmd[-3:], ["-e=/l/a.jar,/l/b.jar", "/in", "/out"])   # -e must follow every other flag

    def test_unknown_variant_is_an_error(self):
        with self.assertRaises(KeyError):
            self.mod.build_command("nope", Path("/in"), Path("/out"), [], java="j", vineflower="v", jdk_home="/j")

    def test_stage_copies_the_class_and_its_nested_files_only(self):
        with tempfile.TemporaryDirectory() as td:
            ext = Path(td) / "organized" / "m" / "extracted" / "p"
            ext.mkdir(parents=True)
            for n in ("Foo.class", "Foo$1.class", "Foo$Inner.class", "Bar.class", "Foobar.class"):
                (ext / n).write_bytes(b"x")
            stage = Path(td) / "stage"
            self.mod.stage_classes(Path(td) / "organized" / "m", ["p/Foo"], stage)
            self.assertEqual(sorted(p.name for p in (stage / "p").iterdir()), ["Foo$1.class", "Foo$Inner.class", "Foo.class"])

    def test_targets_are_grouped_by_module(self):
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / "t.json"
            t.write_text(json.dumps([["b", "x/B"], ["a", "x/A"], ["a", "x/C"]]))
            self.assertEqual(self.mod.load_targets(t), {"a": ["x/A", "x/C"], "b": ["x/B"]})


if __name__ == "__main__":
    unittest.main()
