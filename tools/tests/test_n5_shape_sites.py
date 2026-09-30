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


if __name__ == "__main__":
    unittest.main()
