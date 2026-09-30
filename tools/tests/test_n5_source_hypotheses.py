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


class TestLiftIncrements(unittest.TestCase):
    """`gen = base + ++i;` compiles with the increment inside the expression; source that had
    `i++;` as its own statement compiles differently. The decompiler folds the statement into
    the expression that uses it."""

    def setUp(self):
        self.h = _load()

    def wrap(self, body):
        return "   void f(int n) {\n      int i = 0;\n" + body + "   }\n"

    def test_pre_increment_moves_before_the_statement(self):
        self.assertEqual(self.h.lift_increments(self.wrap("      gen = base + ++i;\n")),
                         self.wrap("      i++;\n      gen = base + i;\n"))
        self.assertEqual(self.h.lift_increments(self.wrap("      return sb.append(buf[--i]);\n")),
                         self.wrap("      i--;\n      return sb.append(buf[i]);\n"))

    def test_post_increment_moves_after_the_statement(self):
        self.assertEqual(self.h.lift_increments(self.wrap("      out[i++] = v;\n")),
                         self.wrap("      out[i] = v;\n      i++;\n"))

    def test_left_alone(self):
        for body in (
            "      a[i] = ++i;\n",                    # i is read twice: evaluation order matters
            "      x = ok && ++i > 0;\n",             # conditional evaluation
            "      x = ok ? ++i : 0;\n",
            "      while (--i > 0) {\n",              # re-evaluated each iteration
            "      if (--i == -1) {\n",               # control header: not a plain statement
            "      return out[i++];\n",               # post-increment cannot move after a return
            "      x = ++total;\n",                   # not an int local
            "      f(++i,\n",                         # multi-line statement
        ):
            self.assertEqual(self.h.lift_increments(self.wrap(body)), self.wrap(body))


class TestPrivilegedVoid(unittest.TestCase):
    """A raw `(PrivilegedAction)` cast makes javac infer an Object-returning lambda; the shipped
    lambda returns Void."""

    def setUp(self):
        self.h = _load()

    def test_raw_privileged_casts_get_a_void_argument(self):
        src = ("      SecurityUtil.doPrivileged((niagara.nre.security.privileged.PrivilegedExceptionAction) () -> {\n"
               "      SecurityUtil.doPrivileged((niagara.nre.security.privileged.PrivilegedAction) () -> {\n")
        out = self.h.privileged_void(src)
        self.assertIn("(niagara.nre.security.privileged.PrivilegedExceptionAction<Void>) () -> {", out)
        self.assertIn("(niagara.nre.security.privileged.PrivilegedAction<Void>) () -> {", out)

    def test_parameterized_and_two_argument_forms_are_left_alone(self):
        src = ("      f((niagara.nre.security.privileged.PrivilegedAction<String>) () -> {\n"
               "      f((niagara.nre.security.privileged.PrivilegedSingleExceptionAction<Void, IOException>) () -> {\n"
               "      f((niagara.nre.security.privileged.PrivilegedAction) x);\n")
        self.assertEqual(self.h.privileged_void(src), src.replace("PrivilegedAction) x", "PrivilegedAction) x"))


JAVAP = """  public niagara.serial.BISerialPort open(java.lang.String) throws java.lang.Exception;
    descriptor: (Ljava/lang/String;)Lniagara/serial/BISerialPort;
    flags: (0x0001) ACC_PUBLIC
    Code:
      stack=5, locals=5, args_size=2
         0: return
      LineNumberTable:
        line 10: 0
      LocalVariableTable:
        Start  Length  Slot  Name   Signature
            0     460     0  this   Lniagara/serial/BSerialHelper;
            0     460     1 owner   Ljava/lang/String;
           10     450     2 platSvc   Lniagara/serial/BISerialService;
           47      39     4 items   Ljava/util/List;
           36      50     3     e   Ljava/lang/Exception;
           98      39     3     e   Ljava/lang/RuntimeException;
      LocalVariableTypeTable:
        Start  Length  Slot  Name   Signature
           47      39     4 items   Ljava/util/List<Lniagara/sys/BValue;>;
  static {};
    descriptor: ()V
    Code:
      LocalVariableTable:
        Start  Length  Slot  Name   Signature
            0      1     0     i   I
"""


class TestDeclaredLocalTypes(unittest.TestCase):
    """The shipped LocalVariableTable says what each local was declared as; the decompiler prints
    `var x = (A & B)expr` or a narrower/wider type than the original declaration."""

    def setUp(self):
        self.h = _load()

    def test_lvt_types_are_read_per_method_with_generics(self):
        lvt = self.h.lvt_types(JAVAP)
        self.assertEqual(lvt[("open", "(Ljava/lang/String;)Lniagara/serial/BISerialPort;")], {
            "this": "niagara.serial.BSerialHelper", "owner": "java.lang.String", "platSvc": "niagara.serial.BISerialService",
            "items": "java.util.List<niagara.sys.BValue>", "e": None})
        self.assertEqual(lvt[("<clinit>", "()V")], {"i": "int"})

    def ctx(self, text):
        key = ("open", "(Ljava/lang/String;)Lniagara/serial/BISerialPort;")
        return {"methods": [{"name": key[0], "desc": key[1], "body_start": text.index("{", text.index(")")),
                             "end": len(text) - 2}], "lvt": self.h.lvt_types(JAVAP), "mismatched": {key}}

    SRC = ("class T {\n   public BISerialPort open(String owner) {\n"
           "      var platSvc = (BComponent & BISerialService)Sys.getService(BISerialService.TYPE);\n"
           "      ArrayList<BValue> items = new ArrayList<>();\n"
           "      Exception e = null;\n   }\n}\n")

    def test_var_with_intersection_cast_takes_the_declared_type(self):
        out = self.h.declared_local_types(self.SRC, self.ctx(self.SRC))
        self.assertIn("      niagara.serial.BISerialService platSvc = (niagara.serial.BISerialService)Sys.getService("
                      "BISerialService.TYPE);\n", out)

    def test_differing_declared_type_is_replaced_and_agreeing_or_ambiguous_ones_are_kept(self):
        out = self.h.declared_local_types(self.SRC, self.ctx(self.SRC))
        self.assertIn("      java.util.List<niagara.sys.BValue> items = new ArrayList<>();\n", out)
        self.assertIn("      Exception e = null;\n", out)      # two entries with different types: ambiguous

    def test_methods_that_do_not_mismatch_are_left_alone(self):
        ctx = self.ctx(self.SRC)
        ctx["mismatched"] = set()
        self.assertEqual(self.h.declared_local_types(self.SRC, ctx), self.SRC)


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
