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


class TestIincForms(unittest.TestCase):
    """javac emits `iinc` for `i++` / `i += c` on an int local but iload/iconst/iadd/istore for
    `i = i + c`; the decompiler prints the first form for both."""

    def setUp(self):
        self.h = _load()

    SRC = ("   void f(int n) {\n      int i = 0;\n      long total = 0L;\n      i++;\n      --n;\n      i += 2;\n"
           "      total++;\n      for (int k = 0; k < n; k++) {\n         i -= 3;\n      }\n   }\n")

    def test_int_local_increments_are_expanded(self):
        out = self.h.expand_iinc(self.SRC)
        self.assertIn("      i = i + 1;\n", out)
        self.assertIn("      n = n - 1;\n", out)
        self.assertIn("      i = i + 2;\n", out)
        self.assertIn("         i = i - 3;\n", out)
        self.assertIn("k = k + 1) {", out)

    def test_non_int_variables_are_left_alone(self):
        out = self.h.expand_iinc(self.SRC)
        self.assertIn("      total++;\n", out)

    def test_name_declared_with_two_types_is_left_alone(self):
        src = "   void f() {\n      int i = 0;\n      i++;\n   }\n   void g() {\n      long i = 0L;\n      i++;\n   }\n"
        self.assertEqual(self.h.expand_iinc(src), src)

    def test_collapse_is_the_inverse_for_statements(self):
        expanded = self.h.expand_iinc(self.SRC)
        out = self.h.collapse_iinc(expanded)
        self.assertIn("      i += 1;\n", out)
        self.assertIn("      n -= 1;\n", out)
        self.assertIn("      total++;\n", out)


class TestRestoreNullChecks(unittest.TestCase):
    """The decompiler drops `Objects.requireNonNull(x);` statements as if they were javac's own
    null checks; the shipped method begins with them."""

    NN = "invokestatic // Method java/util/Objects.requireNonNull:(Ljava/lang/Object;)Ljava/lang/Object;"

    def setUp(self):
        self.h = _load()

    def ctx(self, text, name, desc, params, shipped, ours, static=True):
        return {"methods": [{"name": name, "desc": desc, "params": params, "body_start": text.index("{", text.index(")"))}],
                "shipped": {(name, desc): shipped}, "ours": {(name, desc): ours}, "static": {(name, desc): static}}

    def test_prologue_checks_are_restored_for_the_right_parameters(self):
        text = "class T {\n  static int f(int a, String s, long l, Object o) {\n    return a;\n  }\n}\n"
        shipped = ["insn0: aload_1", "insn1: " + self.NN, "insn2: pop", "insn3: aload 4", "insn4: " + self.NN,
                   "insn5: pop", "insn6: iload_0", "insn7: ireturn"]
        ours = ["insn0: iload_0", "insn1: ireturn"]
        out = self.h.restore_null_checks(text, self.ctx(text, "f", "(ILjava/lang/String;JLjava/lang/Object;)I",
                                                        ["a", "s", "l", "o"], shipped, ours))
        self.assertEqual(out, "class T {\n  static int f(int a, String s, long l, Object o) {\n"
                              "    java.util.Objects.requireNonNull(s);\n    java.util.Objects.requireNonNull(o);\n"
                              "    return a;\n  }\n}\n")

    def test_instance_methods_skip_this_and_constructors_are_left_alone(self):
        text = "class T {\n  int f(String s) {\n    return 1;\n  }\n}\n"
        shipped = ["insn0: aload_1", "insn1: " + self.NN, "insn2: pop", "insn3: iconst_1", "insn4: ireturn"]
        ctx = self.ctx(text, "f", "(Ljava/lang/String;)I", ["s"], shipped, ["insn0: iconst_1", "insn1: ireturn"], static=False)
        self.assertIn("java.util.Objects.requireNonNull(s);", self.h.restore_null_checks(text, ctx))
        text = "class T {\n  T(String s) {\n    this.x = 1;\n  }\n}\n"
        ctx = self.ctx(text, "<init>", "(Ljava/lang/String;)V", ["s"], ["insn0: aload_1", "insn1: " + self.NN, "insn2: pop"],
                       ["insn0: return"], static=False)
        self.assertEqual(self.h.restore_null_checks(text, ctx), text)

    def test_nothing_to_restore_when_the_recompiled_method_already_checks_or_does_not_start_with_a_check(self):
        text = "class T {\n  static int f(String s) {\n    return 1;\n  }\n}\n"
        chk = ["insn0: aload_0", "insn1: " + self.NN, "insn2: pop", "insn3: iconst_1", "insn4: ireturn"]
        self.assertEqual(self.h.restore_null_checks(text, self.ctx(text, "f", "(Ljava/lang/String;)I", ["s"], chk, chk)), text)
        plain = ["insn0: iconst_1", "insn1: ireturn"]
        self.assertEqual(self.h.restore_null_checks(text, self.ctx(text, "f", "(Ljava/lang/String;)I", ["s"], plain, plain)),
                         text)


if __name__ == "__main__":
    unittest.main()
