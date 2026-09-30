#!/usr/bin/env python3
"""tools/n5_source_hypotheses.py (C3d): source-level hypotheses about a decompiler defect. Each
maps a source text to a variant text; none is trusted -- the method splice
(tools/n5-splice-methods.py) keeps a variant's method only when its recompiled Code equals the
shipped one, so a wrong hypothesis is simply never used."""
import importlib.util
import sys
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("n5_source_hypotheses", TOOLS_DIR / "n5_source_hypotheses.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestCompoundAssign(unittest.TestCase):
    def setUp(self):
        self.h = _load()

    def check(self, before, after):
        self.assertEqual(self.h.compound_assign(before), after)

    def test_cast_wrapped_array_element_update(self):
        self.check("      this.buf[3] = (byte)(this.buf[3] | 4);\n", "      this.buf[3] |= 4;\n")
        self.check("      a[i] = (byte)(a[i] & -5);\n", "      a[i] &= -5;\n")
        self.check("      c[k + 1] = (char)(c[k + 1] ^ mask);\n", "      c[k + 1] ^= mask;\n")

    def test_plain_int_element_update(self):
        self.check("      counts[i] = counts[i] + 1;\n", "      counts[i] += 1;\n")
        self.check("      this.v[0][j] = this.v[0][j] << shift(x);\n", "      this.v[0][j] <<= shift(x);\n")

    def test_left_alone(self):
        for src in (
            "      x = (byte)(x | 4);\n",                          # local: the decompiler already handles it
            "      a[i] = (byte)(a[j] | 4);\n",                    # different element
            "      a[i++] = (byte)(a[i++] | 4);\n",                # side effect in the index
            "      a[f()] = a[f()] + 1;\n",                        # call in the index
            "      a[i] = a[i] - b - c;\n",                        # RHS is not one operand: -= would regroup it
            "      a[i] = (byte)(a[i] + b * c);\n",                # RHS has a top-level operator
            "      a[i] = b[i] + 1;\n",
        ):
            self.check(src, src)

    def test_every_site_of_a_method_is_rewritten_and_nothing_else_changes(self):
        src = ("   void f() {\n      a[0] = (byte)(a[0] | 1);\n      int x = 2;\n      a[1] = (byte)(a[1] & 2);\n   }\n")
        out = self.h.compound_assign(src)
        self.assertEqual(out, "   void f() {\n      a[0] |= 1;\n      int x = 2;\n      a[1] &= 2;\n   }\n")


class TestUnfoldArrayInitializers(unittest.TestCase):
    """javac compiles `T[] a = {x}` as newarray/dup/index/value/store; source that was `a = new T[1];
    a[0] = x;` compiles as newarray/store/load/index/value/store. The decompiler folds the second
    into the first form."""

    def setUp(self):
        self.h = _load()

    def test_single_element_initializer_is_unfolded(self):
        self.assertEqual(
            self.h.unfold_single_element_arrays("      byte[] bytes = new byte[]{(byte)(val & 0xFF)};\n"),
            "      byte[] bytes = new byte[1];\n      bytes[0] = (byte)(val & 0xFF);\n")
        self.assertEqual(self.h.unfold_single_element_arrays("      final boolean[] result = new boolean[]{false};\n"),
                         "      final boolean[] result = new boolean[1];\n      result[0] = false;\n")

    def test_every_element_is_assigned_in_order(self):
        self.assertEqual(self.h.unfold_array_initializers("   int[] a = new int[]{1, f(2, 3), \"x,y\".length()};\n"),
                         "   int[] a = new int[3];\n   a[0] = 1;\n   a[1] = f(2, 3);\n   a[2] = \"x,y\".length();\n")

    def test_only_single_element_variant_keeps_longer_initializers(self):
        src = "      int[] a = new int[]{1, 2};\n"
        self.assertEqual(self.h.unfold_single_element_arrays(src), src)

    def test_left_alone(self):
        for src in (
            "      int[][] a = new int[][]{{1}};\n",                 # nested initializer
            "      List<String> a = new ArrayList<>();\n",
            "      return new int[]{1};\n",                          # not a local declaration
            "      this.a = new int[]{1};\n",
            "      int[] a = new int[]{};\n",                        # empty
            "      Object[] a = new String[]{\"s\"};\n",              # element type differs from the declaration
        ):
            self.assertEqual(self.h.unfold_array_initializers(src), src)


if __name__ == "__main__":
    unittest.main()
