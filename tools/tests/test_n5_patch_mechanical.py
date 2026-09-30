#!/usr/bin/env python3
"""tools/n5-patch-mechanical.py (C3b/C3c/C3a-G2): javac-error-driven mechanical fixes of
decompiled sources. Runner: `cd tools/tests && python3 -m unittest test_n5_patch_mechanical`.

Every fixer is tested with a real javac 25: the fixture must FAIL to compile before the
patch (the decompiler defect) and compile after it.
"""
import importlib.util
import json
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

    def patch(self, text: str, cls: str = "T", ctx=None):
        self.assertNotEqual(javac_compile(text, cls), "", "fixture must fail to compile before the patch")
        res = self.m.patch_source(text, lambda t: javac_compile(t, cls), ctx=ctx)
        return res

    def evidence(self, shipped: str, cls: str = "T") -> dict:
        """ctx built from the javap -v of a self-written 'shipped' class (real bytecode)."""
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / f"{cls}.java"
            src.write_text(shipped, encoding="utf-8")
            r = subprocess.run([f"{JDK}/javac", "--release", "25", "-proc:none", "-d", td + "/out", str(src)],
                               capture_output=True, text=True)
            assert r.returncode == 0, r.stderr
            files = sorted(str(p) for p in Path(td, "out").rglob("*.class"))
            out = subprocess.run([f"{JDK}/javap", "-v", "-p", *files], capture_output=True, text=True).stdout
        return {"methodrefs": self.m.parse_methodrefs(out)}


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


class TestCatchParameterRename(MechanicalCase):
    SRC = """public class T {
   void g() throws Exception {}
   void f() {
      try {
         this.g();
      } catch (Exception e) {
         System.out.println("bad: " + ex);
         throw new RuntimeException(ex);
      }
   }
}
"""

    def test_undeclared_name_in_a_catch_block_becomes_the_catch_parameter(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["catch-parameter-name"])
        self.assertIn('"bad: " + e)', res["text"])
        self.assertIn("new RuntimeException(e)", res["text"])

    def test_name_outside_any_catch_block_is_left_alone(self):
        src = "public class T {\n   int f() {\n      return ex;\n   }\n}\n"
        res = self.patch(src)
        self.assertEqual(res["patches"], [])


class TestInnerConstructorOuterArgument(MechanicalCase):
    SRC = """public class T {
   class Inner { Inner(String s) {} }
   class Inner0 { Inner0() {} }
   class Sub extends Inner {
      Sub(String s) {
         super(T.this, s);
      }
   }

   Inner mk() {
      return new Inner(this, "a");
   }

   Inner0 mk0() {
      return new Inner0(this);
   }
}
"""

    def test_synthetic_outer_instance_argument_is_dropped(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual({p["kind"] for p in res["patches"]}, {"inner-ctor-outer-arg"})
        self.assertEqual(len(res["patches"]), 3)
        self.assertIn("super(s);", res["text"])
        self.assertIn('new Inner("a")', res["text"])
        self.assertIn("new Inner0();", res["text"])

    def test_first_argument_that_is_not_an_outer_this_is_kept(self):
        src = """public class T {
   class Inner { Inner(String s) {} }
   Inner mk(T other) {
      return new Inner(other, "a");
   }
}
"""
        res = self.patch(src)
        self.assertEqual(res["patches"], [])
        self.assertFalse(res["compiles"])


class TestAmbiguousOverloadCast(MechanicalCase):
    SHIPPED = """public class T {
   static class Lg {
      static void log(String s, Object[] a) {}
      static void log(String s, Throwable t) {}
   }
   void f(boolean c, Exception ex) {
      Lg.log("x", (Throwable)(c ? null : null));
      Lg.log("y", (Throwable)null);
   }
}
"""
    DECOMPILED = SHIPPED.replace("(Throwable)(c ? null : null)", "c ? null : null").replace("(Throwable)null", "null")

    def test_parse_methodrefs_reads_owner_name_and_descriptor(self):
        refs = self.m.parse_methodrefs(self._javap_text())
        self.assertIn(("T$Lg", "log", "(Ljava/lang/String;Ljava/lang/Throwable;)V"), refs)

    def _javap_text(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "T.java"
            src.write_text(self.SHIPPED)
            subprocess.run([f"{JDK}/javac", "--release", "25", "-proc:none", "-d", td + "/out", str(src)], check=True)
            files = sorted(str(p) for p in Path(td, "out").rglob("*.class"))
            return subprocess.run([f"{JDK}/javap", "-v", "-p", *files], capture_output=True, text=True).stdout

    def test_ambiguous_arguments_are_cast_to_the_overload_the_bytecode_calls(self):
        res = self.patch(self.DECOMPILED, ctx=self.evidence(self.SHIPPED))
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual({p["kind"] for p in res["patches"]}, {"ambiguous-overload-cast"})
        self.assertIn('Lg.log("y", (java.lang.Throwable)null);', res["text"])
        self.assertIn('Lg.log("x", (java.lang.Throwable)(c ? null : null));', res["text"])

    def test_without_bytecode_evidence_nothing_is_guessed(self):
        res = self.patch(self.DECOMPILED, ctx={"methodrefs": set()})
        self.assertEqual(res["patches"], [])

    def test_both_overloads_in_the_bytecode_is_not_decidable(self):
        ctx = {"methodrefs": {("T$Lg", "log", "(Ljava/lang/String;Ljava/lang/Throwable;)V"),
                              ("T$Lg", "log", "(Ljava/lang/String;[Ljava/lang/Object;)V")}}
        res = self.patch(self.DECOMPILED, ctx=ctx)
        self.assertEqual(res["patches"], [])


class TestSwitchExpressionToStatement(MechanicalCase):
    SRC = """public class T {
   String f(int k, boolean c) {
      String s = "a";

      s = switch (k) {
         case 1 -> "one";
         case 2, 3 -> {
            if (c) {
               yield s + ":x";
            }
         }
         default -> {
            try {
               yield s.trim();
            } catch (RuntimeException e) {
            }
         }
      };
      return s;
   }
}
"""

    def test_switch_expression_whose_arms_may_not_yield_becomes_a_statement(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["switch-yield-statement"])
        self.assertIn("      switch (k) {", res["text"])
        self.assertIn('case 1 -> s = "one";', res["text"])
        self.assertIn('s = s + ":x";', res["text"])
        self.assertNotIn("yield", res["text"])
        self.assertIn("      }\n      return s;", res["text"])

    def test_nested_switch_expression_is_left_alone(self):
        src = self.SRC.replace('"one"', "switch (k) { case 1 -> \"a\"; default -> \"b\"; }")
        res = self.patch(src)
        self.assertEqual(res["patches"], [])


class TestEmptyStatementLoopExit(MechanicalCase):
    SRC = """import java.util.*;
public class T {
   int f(Iterator<String> it) {
      int n = 0;

      while (true) {
         if (!it.hasNext()) {
            ;
         } else {
            n += it.next().length();
         }
      }

      return n;
   }
}
"""

    def test_lone_empty_statement_in_an_endless_loop_becomes_break(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["loop-exit-break"])
        self.assertIn("            break;", res["text"])

    def test_two_empty_statements_are_ambiguous_and_left_alone(self):
        src = self.SRC.replace("n += it.next().length();", ";")
        res = self.patch(src)
        self.assertEqual(res["patches"], [])


class TestTryWithResourcesField(MechanicalCase):
    SRC = """import java.io.*;
public class T implements Closeable {
   private Writer w1 = new StringWriter();
   protected Closeable w2 = new StringWriter();
   private Writer out;

   public void close() throws IOException {
      try (
         this.w1;
         this.w2;
         Writer closing = this.out;
      ) {
         this.w1 = null;
         this.out = null;
      }
   }
}
"""

    def test_field_resources_become_typed_locals(self):
        res = self.patch(self.SRC)
        self.assertTrue(res["compiles"], res["residual_errors"])
        self.assertEqual([p["kind"] for p in res["patches"]], ["twr-field-resource"] * 2)
        self.assertIn("Writer w1_res = this.w1;", res["text"])
        self.assertIn("Closeable w2_res = this.w2;", res["text"])


def _grade_json(path: Path, classes: dict):
    path.write_text(json.dumps({"classes": classes}))


@unittest.skipUnless(HAVE_JDK, "needs JDK 25")
class TestModuleDriver(unittest.TestCase):
    BROKEN = """package p;
public class Foo {
   int f(Object c) {
      if (!(c instanceof String var6)) {
         var6 = "z";
      }

      return var6.length();
   }
}
"""
    OK_P = "package p;\npublic class Bar { int x; }\n"

    def setUp(self):
        self.m = _load()
        self.td = tempfile.TemporaryDirectory()
        self.org = Path(self.td.name)
        mod = self.org / "mod"
        (mod / "vineflower2" / "p").mkdir(parents=True)
        (mod / "vineflower2p" / "p").mkdir(parents=True)
        (mod / "vineflower2" / "p" / "Foo.java").write_text(self.BROKEN)
        (mod / "vineflower2" / "p" / "Bar.java").write_text("package p;\nclass Bar {")
        (mod / "vineflower2p" / "p" / "Bar.java").write_text(self.OK_P)
        _grade_json(mod / "fidelity.vineflower2.json", {
            "p/Foo": {"grade": "bytecode-only", "attempted": [["vineflower2", "no-compile"]]},
            "p/Bar": {"grade": "bytecode-only", "attempted": [["vineflower2", "no-compile"]]},
            "p/Ok": {"grade": "roundtrip-exact", "attempted": [["vineflower2", "roundtrip-exact"]]}})
        _grade_json(mod / "fidelity.vineflower2.patched.json", {
            "p/Bar": {"grade": "bytecode-only", "attempted": [["vineflower2", "no-compile"], ["vineflower2p", "compiles-mismatch"]]}})

    def tearDown(self):
        self.td.cleanup()

    def test_population_takes_the_source_tree_and_its_own_grade(self):
        pop = self.m.module_population(self.org / "mod")
        self.assertEqual(pop["p/Foo"], {"tree": "vineflower2", "source_grade": "no-compile"})
        self.assertEqual(pop["p/Bar"], {"tree": "vineflower2p", "source_grade": "compiles-mismatch"})
        self.assertNotIn("p/Ok", pop)

    def test_patch_module_writes_carried_and_patched_files_and_manifest(self):
        spec = importlib.util.spec_from_file_location("fid_t", os.path.join(TOOLS_DIR, "n5-fidelity.py"))
        fid = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = fid
        spec.loader.exec_module(fid)
        man = self.m.patch_module("mod", self.org, "vineflower2m", fid=fid, classpath="",
                                  javac_bin=f"{JDK}/javac", tool_server=False)
        out = self.org / "mod" / "vineflower2m"
        self.assertEqual(sorted(man["classes"]), ["p/Foo"])
        self.assertTrue(man["classes"]["p/Foo"]["compiles"])
        self.assertIn("String var6;", (out / "p" / "Foo.java").read_text())
        self.assertEqual((out / "p" / "Bar.java").read_text(), self.OK_P)  # carried from vineflower2p
        on_disk = json.loads((out / "PATCHES.json").read_text())
        self.assertEqual(on_disk["carried_files"], 1)
        self.assertEqual(on_disk["classes"]["p/Foo"]["patches"][0]["kind"], "pattern-binding-scope")


if __name__ == "__main__":
    unittest.main()
