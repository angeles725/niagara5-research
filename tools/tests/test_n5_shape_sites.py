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


_FID = None


def _fid():
    global _FID
    if _FID is None:
        spec = importlib.util.spec_from_file_location("n5_fidelity_for_shape_tests", TOOLS_DIR / "n5-fidelity.py")
        _FID = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _FID
        spec.loader.exec_module(_FID)
    return _FID


def graded(java: str, cls: str = "T") -> dict:
    """The grader's parse of a class compiled by javac 25 (`javap -v -p`)."""
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / f"{cls}.java").write_text(java)
        subprocess.run([f"{JDK}/javac", "--release", "25", "-g", "-d", td, str(Path(td) / f"{cls}.java")],
                       check=True, capture_output=True)
        out = subprocess.run([f"{JDK}/javap", "-v", "-p", str(Path(td) / f"{cls}.class")], check=True,
                             capture_output=True, text=True).stdout
    return _fid().parse_javap_verbose(out)


def exact_equal(a: str, b: str) -> bool:
    """True when the grader's exact normalizer finds no difference between the two sources' classes."""
    d = _fid().diff_normalized_classes(graded(a), graded(b))
    return not d["mismatched_methods"] and not d["missing_methods"] and not d["extra_methods"]


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
        """decompiled (vineflower shape) != shipped (javac shape) under the grader\'s exact normalizer, and the site
        hypothesis maps the first onto bytecode equal to the second."""
        self.assertFalse(exact_equal(wrap(decompiled), wrap(shipped)), "fixture must start different")
        out = self.apply_all(name, decompiled)
        self.assertTrue(exact_equal(wrap(out), wrap(shipped)))


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

    def test_a_ternary_the_decompiler_wrapped_over_several_lines(self):
        self.assert_reproduces(
            "split-return-ternary",
            "   Object b(Object x, Object y) {\n      return x != null && !x.toString().isEmpty()\n         ? x.toString()\n"
            "         : y;\n   }\n",
            "   Object b(Object x, Object y) {\n      if (x != null && !x.toString().isEmpty()) {\n"
            "         return x.toString();\n      }\n      return y;\n   }\n")

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


class TestHoistDeclaration(ShapeSiteCase):
    """javac numbers locals in declaration order. The decompiler declares an assigned-later local
    right before its first branch; the shipped source often declared it earlier, which permutes the
    slots of every local declared in between."""

    DECOMPILED = ("   void m(boolean s) {\n      for (int i = 0; i < 3; i++) {\n         this.f += i;\n      }\n\n"
                  "      Object body = new Object();\n      int code;\n      if (s) {\n"
                  "         code = 200;\n      } else {\n         code = 403;\n      }\n\n      this.f = code;\n"
                  "      this.o = body;\n   }\n")
    SHIPPED = ("   void m(boolean s) {\n      for (int i = 0; i < 3; i++) {\n         this.f += i;\n      }\n\n"
               "      int code;\n      Object body = new Object();\n      if (s) {\n"
               "         code = 200;\n      } else {\n         code = 403;\n      }\n\n      this.f = code;\n"
               "      this.o = body;\n   }\n")

    def test_declaration_moves_above_the_previous_declaration(self):
        self.assert_reproduces("hoist-declaration", self.DECOMPILED, self.SHIPPED)

    def test_only_uninitialized_declarations_move_and_never_out_of_their_block(self):
        hyp = self.h.SITE_HYPOTHESES["hoist-declaration"]
        self.assertEqual(hyp.sites(self.SHIPPED), [])          # nothing precedes `int code;`
        nested = ("   void m(boolean s) {\n      Object a = f();\n      if (s) {\n         int b;\n         b = 1;\n"
                  "      }\n   }\n")
        self.assertEqual(hyp.sites(nested), [])                # `Object a` is in the enclosing block
        init = "   void m() {\n      Object a = f();\n      int b = 3;\n   }\n"
        self.assertEqual(hyp.sites(init), [])                  # initialized: moving it would reorder effects


class TestUnguardElse(ShapeSiteCase):
    """The inverse of the early return: javac compiles `if (c) { REST } else { throw }` with the
    throw last, the decompiler's `if (!c) { throw } REST` puts it first."""

    def test_guard_becomes_the_if_branch_with_a_leaving_else(self):
        self.assert_reproduces(
            "unguard-else",
            "   void m(Object x) {\n      if (!(x instanceof String)) {\n         throw new IllegalStateException(\"bad\");\n"
            "      }\n\n      this.f = 1;\n      this.f = 2;\n   }\n",
            "   void m(Object x) {\n      if (x instanceof String) {\n         this.f = 1;\n         this.f = 2;\n"
            "      } else {\n         throw new IllegalStateException(\"bad\");\n      }\n   }\n")

    def test_only_a_leaving_guard_followed_by_statements_is_a_site(self):
        hyp = self.h.SITE_HYPOTHESES["unguard-else"]
        self.assertEqual(hyp.sites("   void m() {\n      if (c()) {\n         a();\n      }\n\n      b();\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      if (c()) {\n         return;\n      }\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      if (c()) {\n         return;\n      } else {\n         a();\n"
                                   "      }\n\n      b();\n   }\n"), [])


class TestHoistForVariable(ShapeSiteCase):
    """A `for` variable declared before the loop keeps its slot after it; the decompiler's
    `for (int i = ...)` frees the slot for the next local."""

    def test_for_variable_is_declared_before_the_loop(self):
        self.assert_reproduces(
            "hoist-for-var",
            "   void m() {\n      for (int col = 0; col < 3; col++) {\n         this.f += col;\n      }\n\n"
            "      Object t = new Object();\n      this.o = t;\n   }\n",
            "   void m() {\n      int col;\n      for (col = 0; col < 3; col++) {\n         this.f += col;\n      }\n\n"
            "      Object t = new Object();\n      this.o = t;\n   }\n")

    def test_only_single_variable_for_declarations_are_sites(self):
        hyp = self.h.SITE_HYPOTHESES["hoist-for-var"]
        self.assertEqual(len(hyp.sites("   void m() {\n      for (int a = 0; a < 3; a++) {\n      }\n   }\n")), 1)
        self.assertEqual(hyp.sites("   void m() {\n      for (int a = 0, b = 1; a < 3; a++) {\n      }\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      for (Object o : list) {\n      }\n   }\n"), [])


class TestInvertGuardReturn(ShapeSiteCase):
    """`if (c) { A return y; } return x;` -> `if (!c) { return x; } A return y;`: javac emits the early
    `return x` where the decompiler folds it into the trailing one."""

    def test_trailing_return_becomes_the_guard(self):
        self.assert_reproduces(
            "invert-guard-return",
            "   int m(int a, int b) {\n      if (a > 0 && b > 0) {\n         this.f = 1;\n         this.f = 2;\n"
            "         return 1;\n      }\n\n      return 0;\n   }\n",
            "   int m(int a, int b) {\n      if (!(a > 0 && b > 0)) {\n         return 0;\n      }\n"
            "      this.f = 1;\n      this.f = 2;\n      return 1;\n   }\n")

    def test_needs_a_leaving_block_and_an_immediately_following_return(self):
        hyp = self.h.SITE_HYPOTHESES["invert-guard-return"]
        self.assertEqual(hyp.sites("   int m(int a) {\n      if (a > 0) {\n         f();\n      }\n\n      return 0;\n   }\n"), [])
        self.assertEqual(hyp.sites("   int m(int a) {\n      if (a > 0) {\n         return 1;\n      }\n\n      f();\n"
                                   "      return 0;\n   }\n"), [])


class TestPatternBinding(ShapeSiteCase):
    """The decompiler writes `if (x instanceof T) { ... (T)x ... }`; the shipped code used a pattern
    binding (`x instanceof T t`), whose astore/aload pair javac keeps."""

    def test_cast_of_the_tested_name_becomes_a_binding(self):
        self.assert_reproduces(
            "instanceof-binding",
            "   Object m(Object s) {\n      if (s instanceof String) {\n         return (String)s;\n      }\n\n"
            "      return null;\n   }\n",
            "   Object m(Object s) {\n      if (s instanceof String t) {\n         return t;\n      }\n\n"
            "      return null;\n   }\n")

    def test_negated_test_binds_for_the_rest_of_the_block(self):
        self.assert_reproduces(
            "instanceof-binding",
            "   Object m(Object s) {\n      if (!(s instanceof String)) {\n         return null;\n      }\n\n"
            "      this.f = ((String)s).length();\n      return s;\n   }\n",
            "   Object m(Object s) {\n      if (!(s instanceof String t)) {\n         return null;\n      }\n\n"
            "      this.f = t.length();\n      return s;\n   }\n")

    def test_only_a_plain_name_with_a_cast_in_the_scope_is_a_site(self):
        hyp = self.h.SITE_HYPOTHESES["instanceof-binding"]
        self.assertEqual(hyp.sites("   void m(Object s) {\n      if (s instanceof String) {\n         f();\n      }\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m(Object s) {\n      if (g() instanceof String) {\n         f((String)g());\n"
                                   "      }\n   }\n"), [])


class TestReturnOutOfTry(ShapeSiteCase):
    """The decompiler returns from inside the `try` (`return r;` as its last statement); javac compiled
    the shipped `try { .. } catch (..) { throw .. } return r;` with the return after the handlers."""

    def test_trailing_return_of_the_try_body_moves_after_the_handlers(self):
        self.assert_reproduces(
            "return-out-of-try",
            "   Object m(Object x) {\n      Object r = x;\n      try {\n         this.f = 1;\n         return r;\n"
            "      } catch (RuntimeException e) {\n         throw new IllegalStateException(\"bad\");\n      }\n   }\n",
            "   Object m(Object x) {\n      Object r = x;\n      try {\n         this.f = 1;\n"
            "      } catch (RuntimeException e) {\n         throw new IllegalStateException(\"bad\");\n      }\n\n"
            "      return r;\n   }\n")

    def test_not_a_site_when_a_handler_falls_through_or_a_finally_exists(self):
        hyp = self.h.SITE_HYPOTHESES["return-out-of-try"]
        falls = ("   Object m(Object x) {\n      try {\n         f();\n         return x;\n      } catch (RuntimeException e) {\n"
                 "         g();\n      }\n\n      return null;\n   }\n")
        self.assertEqual(hyp.sites(falls), [])
        fin = ("   Object m(Object x) {\n      try {\n         f();\n         return x;\n      } finally {\n         g();\n"
               "      }\n   }\n")
        self.assertEqual(hyp.sites(fin), [])


class TestSwitchCaseOrder(ShapeSiteCase):
    """javac lays the case blocks out in source order; the decompiler sorts them. The shipped
    tableswitch targets tell the original order."""

    SHIPPED = ("   int m(int x) {\n      switch (x) {\n         case 301:\n            return 0;\n         case 304:\n"
               "            return 2;\n         case 302:\n            return 1;\n         default:\n            return 3;\n"
               "      }\n   }\n")
    DECOMPILED = ("   int m(int x) {\n      switch (x) {\n         case 301:\n            return 0;\n         case 302:\n"
                  "            return 1;\n         case 304:\n            return 2;\n         default:\n            return 3;\n"
                  "      }\n   }\n")

    def ctx_for(self, decompiled: str, shipped: str, name: str = "m", desc: str = "(I)I"):
        key = (name, desc)
        start = decompiled.index("   int m(") if False else decompiled.index(f" {name}(")
        return {"methods": [{"name": name, "desc": desc, "start": start, "end": len(decompiled), "body_start": start}],
                "shipped": {key: graded(wrap(shipped))["methods"][key]["code"]},
                "ours": {key: graded(wrap(decompiled))["methods"][key]["code"]},
                "mismatched": {key}}

    def test_case_groups_follow_the_shipped_layout(self):
        self.assertFalse(exact_equal(wrap(self.DECOMPILED), wrap(self.SHIPPED)))
        out = self.h.reorder_switch_cases(self.DECOMPILED, self.ctx_for(self.DECOMPILED, self.SHIPPED))
        self.assertEqual(out, self.SHIPPED)
        self.assertTrue(exact_equal(wrap(out), wrap(self.SHIPPED)))

    def test_already_ordered_and_unmappable_labels_are_left_alone(self):
        ctx = self.ctx_for(self.SHIPPED, self.SHIPPED)
        self.assertEqual(self.h.reorder_switch_cases(self.SHIPPED, ctx), self.SHIPPED)
        named = self.DECOMPILED.replace("case 304:", "case Foo.BAR:")
        ctx = self.ctx_for(self.DECOMPILED, self.SHIPPED)
        self.assertEqual(self.h.reorder_switch_cases(named, ctx), named)


class TestSplitOrCondition(ShapeSiteCase):
    """javac compiles `if (a) { T } if (b) { T }` with two copies of T; the decompiler merges them into
    `if (a || b) { T }`, whose single copy bisimulation-minimizes the shipped code (rule `min`)."""

    def test_leaving_block_is_duplicated_per_operand(self):
        self.assert_reproduces(
            "split-or-condition",
            "   void m(int a, int b) {\n      if (a > 0 || b > 0) {\n         throw new RuntimeException(\"x\");\n"
            "      }\n\n      this.f = 1;\n   }\n",
            "   void m(int a, int b) {\n      if (a > 0) {\n         throw new RuntimeException(\"x\");\n      }\n\n"
            "      if (b > 0) {\n         throw new RuntimeException(\"x\");\n      }\n\n      this.f = 1;\n   }\n")

    def test_three_operands_split_to_a_fixed_point(self):
        src = ("   void m(int a, int b, int c) {\n      if (a > 0 || b > 0 || c > 0) {\n         return;\n      }\n\n"
               "      this.f = 1;\n   }\n")
        out = self.apply_all("split-or-condition", src)
        self.assertEqual(out.count("return;"), 3)
        self.assertNotIn("||", out)

    def test_only_a_leaving_block_with_a_top_level_or_is_a_site(self):
        hyp = self.h.SITE_HYPOTHESES["split-or-condition"]
        self.assertEqual(hyp.sites("   void m() {\n      if (a() || b()) {\n         f();\n      }\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      if (a() && (b() || c())) {\n         return;\n      }\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      if (a() || b()) {\n         return;\n      } else {\n         f();\n"
                                   "      }\n   }\n"), [])


class TestElseIfChainReturns(ShapeSiteCase):
    """The early return of a void method's last `if` also applies to an `else if` chain: javac puts
    a `return` (not a jump to the end) at the end of every branch that has one."""

    def test_else_if_chain_at_the_end_returns_per_branch(self):
        self.assert_reproduces(
            "early-return-else",
            "   void m(int x) {\n      if (x == 1) {\n         this.f = 1;\n         this.f = 2;\n      } else if (x == 2) {\n"
            "         this.f = 3;\n         this.f = 4;\n      } else {\n         this.f = 5;\n         this.f = 6;\n      }\n   }\n",
            "   void m(int x) {\n      if (x == 1) {\n         this.f = 1;\n         this.f = 2;\n         return;\n      }\n"
            "      if (x == 2) {\n         this.f = 3;\n         this.f = 4;\n         return;\n      }\n"
            "      this.f = 5;\n      this.f = 6;\n   }\n")


class TestBooleanMaterialization(ShapeSiteCase):
    """Tier-2 shapes (n5_canon `boolmat`, `cmp1`): a boolean written as `x ? true : false` or compared
    with `== true` compiles to branches the plain value does not have."""

    def test_boolean_ternary_materialization(self):
        self.assert_reproduces(
            "wrap-boolean-ternary",
            "   boolean m() {\n      return this.z;\n   }\n",
            "   boolean m() {\n      return this.z ? true : false;\n   }\n")

    def test_comparison_with_true(self):
        self.assert_reproduces(
            "eq-true",
            "   int m(boolean q) {\n      if (q) {\n         return 1;\n      }\n\n      return 2;\n   }\n",
            "   int m(boolean q) {\n      if (q == true) {\n         return 1;\n      }\n\n      return 2;\n   }\n")

    def test_literals_and_compound_conditions_are_not_sites(self):
        self.assertEqual(self.h.SITE_HYPOTHESES["wrap-boolean-ternary"].sites("   boolean m() {\n      return true;\n   }\n"), [])
        eq = self.h.SITE_HYPOTHESES["eq-true"]
        self.assertEqual(eq.sites("   void m() {\n      if (a && b) {\n         f();\n      }\n   }\n"), [])
        self.assertEqual(eq.sites("   void m() {\n      if (x == true) {\n         f();\n      }\n   }\n"), [])


class TestHoistArgumentTemp(ShapeSiteCase):
    """A `new T(..)` argument the original source kept in a local (`T t = new T(..); call(t);`): the
    local's store/load pair, and the order of evaluation, are in the shipped code."""

    def test_new_argument_moves_into_a_local_before_the_statement(self):
        self.assert_reproduces(
            "hoist-arg-temp",
            "   void m(java.util.List<Object> l) {\n      l.add(new Object());\n   }\n",
            "   void m(java.util.List<Object> l) {\n      Object argTmp = new Object();\n      l.add(argTmp);\n   }\n")

    def test_only_new_arguments_of_a_plain_call_statement_are_sites(self):
        hyp = self.h.SITE_HYPOTHESES["hoist-arg-temp"]
        self.assertEqual(len(hyp.sites("   void m() {\n      a.b(1, new X(y), z);\n   }\n")), 1)
        self.assertEqual(hyp.sites("   void m() {\n      a.b(1, f(y), z);\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      x = a.b(new X());\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      a.b(new X() {\n      });\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      a.b(new X(new Y()));\n   }\n"), [])


class TestSplitHoistDeclaration(ShapeSiteCase):
    """The declaration of an initialized local moves up (`T x;`) and its initializer stays in place
    (`x = e;`): javac numbers the local by the declaration, the code is executed where the assignment is."""

    DECOMPILED = ("   void m() {\n      for (int i = 0; i < 3; i++) {\n         this.f += i;\n      }\n\n"
                  "      Object a = new Object();\n      int b = this.f + 1;\n      this.o = a;\n      this.f = b;\n   }\n")
    SHIPPED = ("   void m() {\n      for (int i = 0; i < 3; i++) {\n         this.f += i;\n      }\n\n"
               "      int b;\n      Object a = new Object();\n      b = this.f + 1;\n      this.o = a;\n      this.f = b;\n   }\n")

    def test_initialized_declaration_is_split_and_its_declaration_hoisted(self):
        hyp = self.h.SITE_HYPOTHESES["split-hoist-declaration"]
        self.assertFalse(exact_equal(wrap(self.DECOMPILED), wrap(self.SHIPPED)))
        out = hyp.apply(self.DECOMPILED, hyp.sites(self.DECOMPILED)[0])       # one site: the rest is the climb's
        self.assertEqual(out, self.SHIPPED)
        self.assertTrue(exact_equal(wrap(out), wrap(self.SHIPPED)))

    def test_only_a_single_line_initialized_declaration_after_another_declaration(self):
        hyp = self.h.SITE_HYPOTHESES["split-hoist-declaration"]
        self.assertEqual(hyp.sites("   void m() {\n      int b = f();\n   }\n"), [])
        self.assertEqual(hyp.sites("   void m() {\n      Object a = f();\n      var b = g();\n   }\n"), [])
        self.assertEqual(len(hyp.sites("   void m() {\n      Object a = f();\n      int b = g();\n   }\n")), 1)


if __name__ == "__main__":
    unittest.main()
