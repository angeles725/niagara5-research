#!/usr/bin/env python3
"""tools/n5_clinit_order.py (C3d): restore the static-initializer order of a decompiled class
from the shipped `<clinit>` (fields un-hoisted into the static block where the original
interleaved them). Real javac-25 fixtures; nothing is guessed: a class that does not fit the
model is refused."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
JDK = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin"


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, TOOLS_DIR / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _jdk() -> bool:
    return all(os.path.isfile(f"{JDK}/{t}") for t in ("javac", "java", "javap"))


class TestPure(unittest.TestCase):
    def setUp(self):
        self.mod = _load("n5_clinit_order", "n5_clinit_order.py")

    def test_match_order_finds_the_shipped_permutation(self):
        slices = {0: ["a", "b"], 1: ["c"], 2: ["d", "e"]}
        self.assertEqual(self.mod.match_order(["insn0: c", "insn1: a", "insn2: b", "insn3: d", "insn4: e", "insn5: return"],
                                              slices), [1, 0, 2])
        self.assertIsNone(self.mod.match_order(["insn0: c", "insn1: x", "insn2: return"], slices))

    def test_statements_are_kept_before_any_number_of_fields(self):
        # fields f0,f2,f5 and statements s1,s3,s4: shipped f0 s1 f2 s3 s4 f5, source f0 f2 f5 s1 s3 s4
        kept = self.mod.longest_kept([0, 2, 5, 1, 3, 4], [0, 1, 2, 3, 4, 5], frozenset({1, 3, 4}))
        self.assertEqual(kept, {0, 1, 3, 4})

    def test_shared_line_and_multi_variable_declarations_are_refused(self):
        text = "class T {\n static int a = 1, b = 2;\n}\n"
        inits = [{"kind": "field", "name": "a", "start": 11, "end": 26, "init_start": 24, "init_end": 25},
                 {"kind": "field", "name": "b", "start": 11, "end": 32, "init_start": 31, "init_end": 32}]
        with self.assertRaises(self.mod.Unsupported):
            self.mod.build_units(text, inits)
        text = "class T {\n static int a = f(); static int b = g();\n}\n"
        inits = [{"kind": "field", "name": "a", "start": 11, "end": 30, "init_start": 24, "init_end": 29},
                 {"kind": "field", "name": "b", "start": 31, "end": 50, "init_start": 44, "init_end": 49}]
        with self.assertRaises(self.mod.Unsupported):
            self.mod.build_units(text, inits)


SHIPPED = """package p;
public class T {
  static java.util.List<String> log = new java.util.ArrayList<>();
  static {
    log.add("a");
  }
  static int x = compute();
  static {
    log.add("b");
    log.add("c");
  }
  static java.util.List<String> y = new java.util.ArrayList<>(log);
  static int compute() { return log.size(); }
}
"""
# decompiler style: every field initializer hoisted to its declaration, the static block last
HOISTED = """package p;
public class T {
  static java.util.List<String> log = new java.util.ArrayList<>();
  static int x = compute();
  static java.util.List<String> y = new java.util.ArrayList<>(log);
  static int compute() { return log.size(); }
  static {
    log.add("a");
    log.add("b");
    log.add("c");
  }
}
"""


@unittest.skipUnless(_jdk(), "JDK 25 not installed")
class TestEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load("n5_clinit_order", "n5_clinit_order.py")
        cls.fid = _load("n5_fidelity_for_clinit", "n5-fidelity.py")
        cls.sp = _load("n5_splice_for_clinit", "n5-splice-methods.py")
        cls.td = tempfile.TemporaryDirectory()
        cls.root = Path(cls.td.name)
        cls.helper = cls.sp.compile_helper(cls.root / "helper", f"{JDK}/javac")

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def _compile(self, name, text):
        d = self.root / name
        (d / "src" / "p").mkdir(parents=True)
        src = d / "src" / "p" / "T.java"
        src.write_text(text)
        subprocess.run([f"{JDK}/javac", "--release", "25", "-g", "-d", str(d / "out"), str(src)],
                       check=True, capture_output=True)
        cls_file = d / "out" / "p" / "T.class"
        javap = self.fid.run_javap_verbose(str(cls_file), javap_bin=f"{JDK}/javap")
        code = self.fid.parse_javap_verbose(javap)["methods"][("<clinit>", "()V")]["code"]
        return src, javap, code

    def _reorder(self, name, shipped, ours):
        _s, _j, ship_code = self._compile(name + "-ship", shipped)
        src, javap, code = self._compile(name + "-ours", ours)
        scan = self.sp.scan_spans([src], self.helper, f"{JDK}/java", "")[str(src)]
        return self.mod.reorder_clinit(ours, scan["inits"], ship_code, javap, code), ship_code

    def test_interleaved_static_blocks_are_restored_and_grade_exact(self):
        new, ship_code = self._reorder("a", SHIPPED, HOISTED)
        self.assertIn("static int x;", new)
        self.assertNotIn("static int x = compute();", new)
        _s, _j, new_code = self._compile("a-new", new)
        self.assertEqual(new_code, ship_code)
        # only the two field initializers moved, into the block after the statements that precede them
        self.assertEqual(new.count("x = compute();"), 1)
        self.assertLess(new.index('log.add("a");'), new.index("x = compute();"))
        self.assertLess(new.index("x = compute();"), new.index('log.add("b");'))
        self.assertLess(new.index('log.add("c");'), new.index("y = new java.util.ArrayList<>(log);"))

    def test_matching_order_is_left_alone(self):
        new, _code = self._reorder("b", SHIPPED, SHIPPED)
        self.assertIsNone(new)

    def test_unmatched_code_is_refused(self):
        other = HOISTED.replace('log.add("c");', 'log.add("z");')
        with self.assertRaises(self.mod.Unsupported):
            self._reorder("c", SHIPPED, other)

    def test_statements_that_would_have_to_move_are_refused(self):
        swapped = HOISTED.replace('log.add("a");\n    log.add("b");', 'log.add("b");\n    log.add("a");')
        with self.assertRaises(self.mod.Unsupported):
            self._reorder("d", SHIPPED, swapped)


if __name__ == "__main__":
    unittest.main()
