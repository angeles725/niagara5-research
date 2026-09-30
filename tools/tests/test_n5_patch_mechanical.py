#!/usr/bin/env python3
"""tools/n5-patch-mechanical.py (C3b/C3c/C3a-G2): javac-error-driven mechanical fixes of
decompiled sources. Runner: `cd tools/tests && python3 -m unittest test_n5_patch_mechanical`.

Every fixer is tested with a real javac 25: the fixture must FAIL to compile before the
patch (the decompiler defect) and compile after it.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(TOOLS_DIR, "n5-patch-mechanical.py")
JDK = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin"
HAVE_JDK = os.path.isfile(f"{JDK}/javac")


def _load():
    spec = importlib.util.spec_from_file_location("n5_patch_mechanical", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def javac_compile(text: str, cls: str = "T") -> str:
    """'' when `text` compiles, else javac's stderr."""
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / f"{cls}.java"
        src.write_text(text, encoding="utf-8")
        r = subprocess.run([f"{JDK}/javac", "--release", "25", "-proc:none", "-nowarn", "-Xmaxerrs", "1000",
                            "-d", str(Path(td) / "out"), str(src)], capture_output=True, text=True)
        return "" if r.returncode == 0 else r.stderr


@unittest.skipUnless(HAVE_JDK, "needs JDK 25")
class MechanicalCase(unittest.TestCase):
    def setUp(self):
        self.m = _load()

    def patch(self, text: str, cls: str = "T"):
        self.assertNotEqual(javac_compile(text, cls), "", "fixture must fail to compile before the patch")
        res = self.m.patch_source(text, lambda t: javac_compile(t, cls))
        return res


class TestFramework(MechanicalCase):
    def test_parse_javac_errors_reads_line_column_message_and_detail(self):
        err = javac_compile("public class T {\n  int f() { return y; }\n}\n")
        errs = self.m.parse_javac_errors(err)
        self.assertEqual(len(errs), 1)
        self.assertEqual((errs[0]["line"], errs[0]["message"]), (2, "cannot find symbol"))
        self.assertEqual(errs[0]["col"], 19)
        self.assertIn("symbol:   variable y", "\n".join(errs[0]["detail"]))

    def test_unfixable_source_is_returned_unchanged_with_residual_errors(self):
        src = "public class T {\n  int f() { return y; }\n}\n"
        res = self.patch(src)
        self.assertEqual(res["text"], src)
        self.assertFalse(res["compiles"])
        self.assertEqual(res["patches"], [])


class TestPatternBindingScope(MechanicalCase):
    SRC = """public class T {
   Object g() { return "x"; }
   int f(Object c) {
      if (!(c instanceof String var6)) {
         var6 = String.valueOf(this.g());
      }

      return var6.length();
   }
}
"""

    def test_binding_used_after_assigning_block_becomes_declared_local(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["pattern-binding-scope"])
        self.assertIn("String var6;", res["text"])
        self.assertIn("var6 = (String)c;", res["text"])
        self.assertNotIn("instanceof String var6", res["text"])
        self.assertEqual(javac_compile(res["text"]), "")

    def test_compound_condition_is_left_alone(self):
        src = """public class T {
   int f(Object c, Object d) {
      if (!(c instanceof String s) && d != null) {
         s = "a";
      }

      return s.length();
   }
}
"""
        res = self.patch(src)
        self.assertFalse(res["compiles"])
        self.assertEqual(res["patches"], [])


class TestForEachRawCast(MechanicalCase):
    def test_raw_list_cast_in_for_each_takes_the_loop_variable_type(self):
        src = """import java.util.*;
public class T {
   Object g() { return new ArrayList<String>(); }
   int f() {
      int n = 0;
      for (String s : (List)this.g()) {
         n += s.length();
      }

      return n;
   }
}
"""
        res = self.patch(src)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["foreach-raw-cast"])
        self.assertIn("for (String s : (List<String>)this.g())", res["text"])

    def test_primitive_loop_variable_uses_the_boxed_type(self):
        src = """import java.util.*;
public class T {
   int f(Object o) {
      int n = 0;
      for (int i : (List)o) {
         n += i;
      }

      return n;
   }
}
"""
        res = self.patch(src)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertIn("(List<Integer>)o", res["text"])


class TestBooleanDeclaredAsInt(MechanicalCase):
    def test_int_initialised_with_boolean_literal_becomes_boolean(self):
        src = """public class T {
   int f(String d) {
      int star = false;
      for (int i = 0; i < d.length(); i++) {
         if (!star && d.charAt(i) == '*') {
            star = true;
         }
      }

      return star ? 1 : 0;
   }
}
"""
        res = self.patch(src)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["boolean-declared-int"])
        self.assertIn("boolean star = false;", res["text"])


class TestUnsafeGenericInstanceof(MechanicalCase):
    def test_generic_instanceof_pattern_type_becomes_raw(self):
        src = """import java.util.*;
public class T {
   int f(Object o) {
      if (o instanceof Comparable<String> c) {
         return c.compareTo("a");
      }

      return 0;
   }
}
"""
        res = self.patch(src)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["instanceof-generic-raw"])
        self.assertIn("o instanceof Comparable c", res["text"])


class TestSwitchGroupRedeclaration(MechanicalCase):
    SRC = """public class T {
   int f(int type, String s) {
      int r;
      switch (type) {
         case 1:
            StringBuilder sb = new StringBuilder(s);
            r = sb.length();
            break;
         case 2:
            StringBuilder sb = new StringBuilder(s + s);
            r = sb.length();
            break;
         default:
            r = 0;
      }

      return r;
   }
}
"""

    def test_case_groups_declaring_the_same_local_are_braced(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["switch-group-scope"] * 2)
        self.assertIn("case 1: {", res["text"])
        self.assertIn("case 2: {", res["text"])
        self.assertNotIn("default: {", res["text"])

    def test_stacked_labels_brace_after_the_last_label(self):
        src = self.SRC.replace("         case 2:\n", "         case 3:\n         case 2:\n")
        res = self.patch(src)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertIn("case 3:\n         case 2: {", res["text"])


if __name__ == "__main__":
    unittest.main()
