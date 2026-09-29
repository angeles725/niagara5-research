"""Tests for tools/n5_canon.py: sound CFG canonicalization behind the
`roundtrip-canonical` grades of tools/n5-fidelity.py.

Each rule is tested twice: on a small hand-written javap fixture (the rule
off -> forms differ, the rule on -> forms equal, and a semantic change is
still detected with the rule on) and on a real javac-25-compiled pair of
equivalent Java sources exercising the shape the rule exists for. Tests
needing javac/javap skip when JDK 25 is absent.
"""
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOOLS_DIR)

JDK25_JAVAC = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javac"
JDK25_JAVAP = "/home/linuxbrew/.linuxbrew/opt/openjdk@25/bin/javap"


def _jdk_available():
    return os.path.isfile(JDK25_JAVAC) and os.path.isfile(JDK25_JAVAP)


def _load_fidelity():
    spec = importlib.util.spec_from_file_location("n5_fidelity", os.path.join(TOOLS_DIR, "n5-fidelity.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def m(lines, rows=(), params=0):
    """A method dict as parse_javap_verbose records it."""
    return {"raw_code": list(lines), "raw_exception_rows": list(rows), "param_slots": params}


def javac_methods(body_a, body_b, name="f", header="static int f(int x, int y)", extra=""):
    """Compile two classes that differ only in method `name`'s body and return
    (method_a, method_b) as parse_javap_verbose records them."""
    fid = _load_fidelity()
    out = []
    with tempfile.TemporaryDirectory() as td:
        for i, body in enumerate((body_a, body_b)):
            d = os.path.join(td, str(i))
            os.makedirs(d)
            src = os.path.join(d, "C.java")
            Path(src).write_text(f"public class C {{ {extra} {header} {{ {body} }} }}\n")
            subprocess.run([JDK25_JAVAC, "--release", "25", "-g", "-d", d, src], check=True, capture_output=True)
            parsed = fid.parse_javap_verbose(fid.run_javap_verbose(os.path.join(d, "C.class"), javap_bin=JDK25_JAVAP))
            out.append(next(v for (n, _), v in parsed["methods"].items() if n == name))
    return out


class CanonTestCase(unittest.TestCase):
    def setUp(self):
        import n5_canon
        self.c = n5_canon

    def assertCanonEqual(self, a, b, rules):
        self.assertEqual(self.c.canonical_form(a, rules), self.c.canonical_form(b, rules))

    def assertCanonDiffer(self, a, b, rules):
        self.assertFalse(self.c.canonical_equal(a, b, rules))


class TestBaselineForm(CanonTestCase):
    def test_polarity_and_layout_do_not_matter(self):
        a = m(["0: iload_0", "1: ifeq 6", "4: iconst_1", "5: ireturn", "6: iconst_2", "7: ireturn"], params=1)
        b = m(["0: iload_0", "1: ifne 6", "4: iconst_2", "5: ireturn", "6: iconst_1", "7: ireturn"], params=1)
        self.assertCanonEqual(a, b, ())

    def test_unreachable_code_is_dropped(self):
        a = m(["0: iconst_1", "1: ireturn"])
        b = m(["0: iconst_1", "1: ireturn", "2: nop", "3: iconst_2", "4: ireturn"])
        self.assertCanonEqual(a, b, ())

    def test_negated_condition_is_detected(self):
        a = m(["0: iload_0", "1: ifeq 6", "4: iconst_1", "5: ireturn", "6: iconst_2", "7: ireturn"], params=1)
        b = m(["0: iload_0", "1: ifne 6", "4: iconst_1", "5: ireturn", "6: iconst_2", "7: ireturn"], params=1)
        self.assertCanonDiffer(a, b, self.c.ALL_RULES)

    def test_parameters_are_pinned(self):
        a = m(["0: iload_0", "1: iload_1", "2: isub", "3: ireturn"], params=2)
        b = m(["0: iload_1", "1: iload_0", "2: isub", "3: ireturn"], params=2)
        self.assertCanonDiffer(a, b, self.c.ALL_RULES)

    def test_width_variants_collapse(self):
        a = m(["0: ldc #5 // String x", "2: areturn"])
        b = m(["0: ldc_w #300 // String x", "3: areturn"])
        self.assertCanonEqual(a, b, ())

    def test_switch_key_to_target_mapping_is_semantic(self):
        sw = ["0: iload_0", "1: lookupswitch { // 2", "1: 28", "2: 30", "default: 32", "}",
              "28: iconst_1", "29: ireturn", "30: iconst_2", "31: ireturn", "32: iconst_3", "33: ireturn"]
        swapped = list(sw)
        swapped[2], swapped[3] = "1: 30", "2: 28"
        self.assertCanonDiffer(m(sw, params=1), m(swapped, params=1), self.c.ALL_RULES)

    def test_jsr_is_unsupported_and_never_equal(self):
        a = m(["0: jsr 4", "3: return", "4: astore_1", "5: ret 1"])
        with self.assertRaises(self.c.Unsupported):
            self.c.canonical_form(a, ())
        self.assertFalse(self.c.canonical_equal(a, a, ()))

    def test_unknown_rule_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.c.canonical_form(m(["0: return"]), ("no-such-rule",))


class TestExceptionCoverage(CanonTestCase):
    CODE = ["0: aload_0", "1: invokevirtual #2 // Method f:()V", "4: return",
            "5: astore_1", "6: return", "7: astore_1", "8: aload_1", "9: athrow"]

    def test_row_order_of_overlapping_rows_is_catch_priority(self):
        rows = [(0, 4, 5, "Class java/io/IOException"), (0, 4, 7, "Class java/lang/Exception")]
        self.assertCanonDiffer(m(self.CODE, rows, 1), m(self.CODE, list(reversed(rows)), 1), self.c.ALL_RULES)

    def test_catch_type_is_semantic(self):
        a = [(0, 4, 5, "Class java/io/IOException")]
        b = [(0, 4, 5, "Class java/lang/RuntimeException")]
        self.assertCanonDiffer(m(self.CODE, a, 1), m(self.CODE, b, 1), self.c.ALL_RULES)

    def test_reordering_non_overlapping_rows_is_a_no_op(self):
        code = ["0: invokestatic #2 // Method f:()V", "3: invokestatic #3 // Method g:()V", "6: return",
                "7: astore_0", "8: return", "9: astore_0", "10: return"]
        rows = [(0, 3, 7, "Class java/io/IOException"), (3, 6, 9, "Class java/lang/Exception")]
        self.assertCanonEqual(m(code, rows), m(code, list(reversed(rows))), ())

    def test_row_ending_at_code_length_is_accepted(self):
        code = ["0: invokestatic #2 // Method f:()V", "3: goto 7", "6: pop", "7: return"]
        form = self.c.canonical_form(m(code, [(0, 8, 6, "any")]), ())
        self.assertTrue(form)


@unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
class TestBaselineRealJavac(CanonTestCase):
    def test_if_else_with_swapped_arms_is_equal(self):
        a, b = javac_methods("if (x > y) return 1; else return 2;", "if (x <= y) return 2; else return 1;")
        self.assertNotEqual(a["code"], b["code"])
        self.assertCanonEqual(a, b, ())

    def test_real_operand_swap_is_detected(self):
        a, b = javac_methods("return x - y;", "return y - x;")
        self.assertCanonDiffer(a, b, self.c.ALL_RULES)


class TestJumpRules(CanonTestCase):
    """thread / const / cmp0 / tail / inl / merge / min."""
    TWO_RETURNS = ["0: iload_0", "1: ifeq 6", "4: iconst_1", "5: ireturn", "6: iconst_2", "7: ireturn"]

    def test_tail_inlines_a_shared_return(self):
        a = m(self.TWO_RETURNS, params=1)
        b = m(["0: iload_0", "1: ifeq 8", "4: iconst_1", "5: goto 9", "8: iconst_2", "9: ireturn"], params=1)
        self.assertCanonDiffer(a, b, ())
        self.assertCanonEqual(a, b, ("tail",))
        c = m(["0: iload_0", "1: ifeq 8", "4: iconst_3", "5: goto 9", "8: iconst_2", "9: ireturn"], params=1)
        self.assertCanonDiffer(a, c, self.c.ALL_RULES)

    def test_thread_skips_an_empty_goto_block(self):
        a = m(["0: iload_0", "1: ifeq 7", "4: goto 7", "7: return"], params=1)
        b = m(["0: iload_0", "1: ifeq 4", "4: return"], params=1)
        self.assertCanonDiffer(a, b, ())
        self.assertCanonEqual(a, b, ("thread",))

    def test_const_folds_a_constant_fed_zero_test(self):
        a = m(["0: iload_0", "1: ifeq 8", "4: iconst_1", "5: goto 9", "8: iconst_0", "9: ifeq 14",
               "12: iconst_1", "13: ireturn", "14: iconst_2", "15: ireturn"], params=1)
        b = m(self.TWO_RETURNS, params=1)
        self.assertCanonDiffer(a, b, ("thread",))
        self.assertCanonEqual(a, b, ("const", "thread"))
        # the constants swapped: the arms select the other return
        c = m(["0: iload_0", "1: ifeq 8", "4: iconst_0", "5: goto 9", "8: iconst_1", "9: ifeq 14",
               "12: iconst_1", "13: ireturn", "14: iconst_2", "15: ireturn"], params=1)
        self.assertCanonDiffer(c, b, self.c.ALL_RULES)

    def test_cmp0_compare_with_zero_is_the_one_operand_form(self):
        a = m(["0: iload_0", "1: iconst_0", "2: if_icmpeq 7", "5: iconst_1", "6: ireturn", "7: iconst_2",
               "8: ireturn"], params=1)
        b = m(["0: iload_0", "1: ifeq 6", "4: iconst_1", "5: ireturn", "6: iconst_2", "7: ireturn"], params=1)
        self.assertCanonDiffer(a, b, ())
        self.assertCanonEqual(a, b, ("cmp0",))
        one = m(["0: iload_0", "1: iconst_1", "2: if_icmpeq 7", "5: iconst_1", "6: ireturn", "7: iconst_2",
                 "8: ireturn"], params=1)
        self.assertCanonDiffer(one, b, self.c.TIER1_RULES)
        null = m(["0: aload_0", "1: aconst_null", "2: if_acmpne 7", "5: iconst_1", "6: ireturn", "7: iconst_2",
                  "8: ireturn"], params=1)
        nonnull = m(["0: aload_0", "1: ifnonnull 6", "4: iconst_1", "5: ireturn", "6: iconst_2", "7: ireturn"],
                    params=1)
        self.assertCanonEqual(null, nonnull, ("cmp0",))

    def test_inl_duplicates_a_small_shared_jump_block(self):
        a = m(["0: iload_0", "1: ifeq 10", "4: invokestatic #2 // Method f:()V", "7: goto 13",
               "10: invokestatic #3 // Method g:()V", "13: iconst_5", "14: istore_1", "15: goto 18",
               "18: iload_1", "19: ireturn"], params=1)
        b = m(["0: iload_0", "1: ifeq 13", "4: invokestatic #2 // Method f:()V", "7: iconst_5", "8: istore_1",
               "9: goto 21", "12: nop", "13: invokestatic #3 // Method g:()V", "16: iconst_5", "17: istore_1",
               "18: goto 21", "21: iload_1", "22: ireturn"], params=1)
        self.assertCanonDiffer(a, b, ())
        self.assertCanonEqual(a, b, ("inl",))

    def test_merge_concatenates_a_single_predecessor_chain(self):
        a = m(["0: invokestatic #2 // Method f:()V", "3: goto 6", "6: invokestatic #3 // Method g:()V",
               "9: return"])
        b = m(["0: invokestatic #2 // Method f:()V", "3: invokestatic #3 // Method g:()V", "6: return"])
        self.assertCanonDiffer(a, b, ())
        self.assertCanonEqual(a, b, ("merge",))
        c = m(["0: invokestatic #3 // Method g:()V", "3: invokestatic #2 // Method f:()V", "6: return"])
        self.assertCanonDiffer(a, c, self.c.ALL_RULES)

    def test_min_merges_identical_blocks(self):
        a = m(["0: iload_0", "1: ifeq 8", "4: invokestatic #2 // Method f:()V", "7: return",
               "8: invokestatic #2 // Method f:()V", "11: return"], params=1)
        b = m(["0: iload_0", "1: ifeq 4", "4: invokestatic #2 // Method f:()V", "7: return"], params=1)
        self.assertCanonDiffer(a, b, ())
        self.assertCanonEqual(a, b, ("min",))
        c = m(["0: iload_0", "1: ifeq 8", "4: invokestatic #2 // Method f:()V", "7: return",
               "8: invokestatic #3 // Method g:()V", "11: return"], params=1)
        self.assertCanonDiffer(c, b, self.c.ALL_RULES)


@unittest.skipUnless(_jdk_available(), "JDK 25 not installed")
class TestJumpRulesRealJavac(CanonTestCase):
    def test_early_return_vs_ternary(self):
        # the BLong.encode(long) shape: two direct areturns vs a goto to one areturn
        a, b = javac_methods('if (v == 0) return "a"; return "b";', 'return v == 0 ? "a" : "b";',
                             header="static String f(long v)")
        self.assertCanonDiffer(a, b, ())
        self.assertEqual(self.c.resolve_rules(a, b), ["tail"])

    def test_identical_return_blocks(self):
        a, b = javac_methods("if (x > 0) { g(1); return 0; } if (y > 0) { g(2); return 0; } return 0;",
                             "if (x > 0) g(1); else if (y > 0) g(2); return 0;",
                             extra="static void g(int i) {}")
        self.assertCanonDiffer(a, b, ())
        self.assertIsNotNone(self.c.resolve_rules(a, b))

    def test_loop_continue_polarity(self):
        a, b = javac_methods("for (int i = 0; i < x; i++) { if (i == y) continue; g(i); } return 0;",
                             "for (int i = 0; i < x; i++) { if (i != y) g(i); } return 0;",
                             extra="static void g(int i) {}")
        self.assertCanonDiffer(a, b, ())
        self.assertIsNotNone(self.c.resolve_rules(a, b))


if __name__ == "__main__":
    unittest.main()
