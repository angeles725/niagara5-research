#!/usr/bin/env python3
"""tools/n5_shape_sites.py (C4): source-shape site hypotheses that make javac 25 emit the SHIPPED
instruction shape instead of a canonically-equal one. Every case is proven with real javac 25: the
decompiler-shaped source compiles to different bytecode than the shipped-shaped source, the
hypothesis rewrites the first into the second's shape, and the two then compile identically."""
import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
JDK = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin"


def _load():
    spec = importlib.util.spec_from_file_location("n5_source_hypotheses", TOOLS_DIR / "n5_source_hypotheses.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _javac_available() -> bool:
    return Path(f"{JDK}/javac").is_file() and Path(f"{JDK}/javap").is_file()


def code_of(java: str, cls: str = "T") -> str:
    """`javap -c -p` of a class compiled by javac 25, constant-pool indices and line tables dropped."""
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / f"{cls}.java").write_text(java)
        subprocess.run([f"{JDK}/javac", "--release", "25", "-g", "-d", td, str(Path(td) / f"{cls}.java")],
                       check=True, capture_output=True)
        out = subprocess.run([f"{JDK}/javap", "-c", "-p", "-cp", td, cls], check=True, capture_output=True,
                             text=True).stdout
    out = "\n".join(l for l in out.splitlines() if not l.startswith("Compiled from"))
    return re.sub(r"#\d+", "#", out)


def wrap(body: str) -> str:
    return f"public class T {{\n   int f;\n   boolean z;\n   Object o;\n{body}\n}}\n"


@unittest.skipUnless(_javac_available(), "javac 25 not installed")
class ShapeSiteCase(unittest.TestCase):
    def setUp(self):
        self.h = _load()

    def apply_all(self, name: str, text: str) -> str:
        hyp = self.h.SITE_HYPOTHESES[name]
        for _ in range(20):
            sites = hyp.sites(text)
            if not sites:
                return text
            new = hyp.apply(text, sites[0])
            if new == text:
                return text
            text = new
        return text

    def assert_reproduces(self, name: str, decompiled: str, shipped: str):
        """decompiled (vineflower shape) != shipped (javac shape) under javac 25, and the site
        hypothesis maps the first onto bytecode equal to the second."""
        self.assertNotEqual(code_of(wrap(decompiled)), code_of(wrap(shipped)), "fixture must start different")
        out = self.apply_all(name, decompiled)
        self.assertEqual(code_of(wrap(out)), code_of(wrap(shipped)))


class TestSplitReturnTernary(ShapeSiteCase):
    def test_reference_ternary_return(self):
        self.assert_reproduces(
            "split-return-ternary",
            "   Object b(Object x) {\n      return x instanceof String ? (String)x : null;\n   }\n",
            "   Object b(Object x) {\n      if (x instanceof String) {\n         return (String)x;\n      }\n      return null;\n   }\n")

    def test_nested_ternary_splits_one_level_per_site(self):
        self.assert_reproduces(
            "split-return-ternary",
            "   int g(int x) {\n      return x > 0 ? 1 : (x < -5 ? 2 : 3);\n   }\n",
            "   int g(int x) {\n      if (x > 0) {\n         return 1;\n      }\n      if (x < -5) {\n         return 2;\n      }\n      return 3;\n   }\n")

    def test_braceless_control_header_is_not_a_site(self):
        src = "   int g(int x) {\n      if (x > 0)\n         return x > 3 ? 1 : 2;\n      return 0;\n   }\n"
        self.assertEqual(self.h.SITE_HYPOTHESES["split-return-ternary"].sites(src), [])


class TestSplitReturnBoolean(ShapeSiteCase):
    def test_comparison_return(self):
        self.assert_reproduces(
            "split-return-boolean",
            "   boolean a(int x) {\n      return (x & 1) == 1;\n   }\n",
            "   boolean a(int x) {\n      if ((x & 1) == 1) {\n         return true;\n      }\n      return false;\n   }\n")

    def test_short_circuit_return(self):
        self.assert_reproduces(
            "split-return-boolean",
            "   boolean a(int x) {\n      return x > 1 && this.z || x < -3;\n   }\n",
            "   boolean a(int x) {\n      if (x > 1 && this.z || x < -3) {\n         return true;\n      }\n      return false;\n   }\n")

    def test_non_boolean_returns_are_not_sites(self):
        src = "   int a(int x) {\n      return x + 1;\n   }\n   Object b() {\n      return this.o;\n   }\n"
        self.assertEqual(self.h.SITE_HYPOTHESES["split-return-boolean"].sites(src), [])


class TestRemoveNullCast(ShapeSiteCase):
    """The decompiler keeps `(T) null` to steer overload resolution; javac then emits `checkcast T`
    after `aconst_null`, which the shipped code does not have."""

    def test_argument_cast_is_dropped(self):
        self.assert_reproduces(
            "remove-null-cast",
            "   static void n(int a, String s) {\n   }\n   void g() {\n      n(4, (String)null);\n   }\n",
            "   static void n(int a, String s) {\n   }\n   void g() {\n      n(4, null);\n   }\n")

    def test_generic_and_array_casts(self):
        src = ("   void g(java.util.List<String> l) {\n      h((java.util.List<String>)null, (byte[])null, "
               "(Object)null);\n   }\n")
        sites = self.h.SITE_HYPOTHESES["remove-null-cast"].sites(src)
        self.assertEqual(len(sites), 3)
        out = self.apply_all("remove-null-cast", src)
        self.assertIn("h(null, null, null);", out)

    def test_casts_of_other_things_are_left_alone(self):
        src = "   void g(Object o) {\n      h((String)o, (String)nullable(), (int)nullCount);\n   }\n"
        self.assertEqual(self.h.SITE_HYPOTHESES["remove-null-cast"].sites(src), [])


class TestReturnTemp(ShapeSiteCase):
    """`T t = <expr>; return t;` compiles with an astore/aload pair the decompiler's `return <expr>;`
    lacks (and the reverse when the decompiler keeps a temporary the shipped code does not have)."""

    def test_temporary_is_introduced_before_the_return(self):
        self.assert_reproduces(
            "introduce-return-temp",
            "   String m(Object x) {\n      return (String)x;\n   }\n",
            "   String m(Object x) {\n      String t = (String)x;\n      return t;\n   }\n")

    def test_temporary_is_removed_before_the_return(self):
        self.assert_reproduces(
            "inline-return-temp",
            "   String m(Object x) {\n      String var2 = (String)x;\n      return var2;\n   }\n",
            "   String m(Object x) {\n      return (String)x;\n   }\n")

    def test_plain_names_and_constants_are_not_sites_for_the_introduction(self):
        src = "   int m(int x) {\n      return x;\n   }\n   int n() {\n      return 4;\n   }\n   void o() {\n      return;\n   }\n"
        self.assertEqual(self.h.SITE_HYPOTHESES["introduce-return-temp"].sites(src), [])

    def test_only_a_temporary_declared_right_before_is_inlined(self):
        src = "   String m() {\n      String t = f();\n      g();\n      return t;\n   }\n"
        self.assertEqual(self.h.SITE_HYPOTHESES["inline-return-temp"].sites(src), [])


class TestContinueGuards(ShapeSiteCase):
    """The loop twin of the early return: javac compiles `if (c) { continue; } A` with a jump back
    that the decompiler's `if (!c) { A }` does not have."""

    def test_guard_at_the_end_of_a_loop_body_becomes_a_continue(self):
        self.assert_reproduces(
            "guard-continue",
            "   void loop(int n) {\n      for (int i = 0; i < n; i++) {\n         if (i % 2 != 0) {\n            this.f++;\n"
            "            this.f += i;\n         }\n      }\n   }\n",
            "   void loop(int n) {\n      for (int i = 0; i < n; i++) {\n         if (i % 2 == 0) {\n            continue;\n"
            "         }\n         this.f++;\n         this.f += i;\n      }\n   }\n")


if __name__ == "__main__":
    unittest.main()
